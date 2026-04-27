#!/usr/bin/env python3
"""
arp_spoof_detector.py
=====================

A DEFENSIVE network-monitoring tool that watches your local network for
ARP-spoofing / ARP-poisoning attacks against your machine or your LAN.

How ARP spoofing works (so you know what we're detecting)
---------------------------------------------------------
ARP maps IP addresses to MAC addresses on a local network. An attacker
on the same LAN can send forged ARP replies claiming "I am the gateway",
poisoning every host's ARP cache so victim traffic is sent through the
attacker (a man-in-the-middle position).

What this tool does
-------------------
  * Sniffs ARP packets on the chosen interface.
  * Builds a baseline IP→MAC mapping.
  * Alerts when:
      - An IP suddenly maps to a *different* MAC ("MAC flap")
      - Multiple IPs claim the same MAC (typical of MITM)
      - ARP replies arrive that were not solicited (high volume)
      - The default-gateway MAC changes
  * Logs alerts to console and (optionally) to a JSON-lines file for SIEM.

This script does NOT send forged ARP packets. It is read-only — it sniffs
broadcast / multicast traffic that is already on the wire.

Requirements
------------
    pip install scapy rich
    sudo (because raw sniffing requires CAP_NET_RAW on Linux,
          or admin/Npcap on Windows)

Usage
-----
    sudo python arp_spoof_detector.py
    sudo python arp_spoof_detector.py --iface eth0
    sudo python arp_spoof_detector.py --iface wlan0 --json-log /var/log/arp_alerts.log

Author: Ethical Hacking Mastery curriculum
License: Educational use
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

try:
    from scapy.all import ARP, sniff, get_if_hwaddr, conf  # type: ignore
except ImportError:
    print("[-] scapy is required: pip install scapy", file=sys.stderr)
    sys.exit(1)

try:
    from rich.console import Console
except ImportError:
    print("[-] rich is required: pip install rich", file=sys.stderr)
    sys.exit(1)

console = Console()


# --------------------------------------------------------------------------- #
# State
# --------------------------------------------------------------------------- #
@dataclass
class ArpState:
    """Tracks the rolling state of the LAN's ARP layer."""
    ip_to_mac: dict[str, str] = field(default_factory=dict)         # baseline
    mac_to_ips: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    reply_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    gateway_ip: str | None = None
    json_log_path: str | None = None
    interface: str = ""

    def alert(self, kind: str, **details) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        msg = f"[bold red][!] ALERT[/bold red] [yellow]{kind}[/yellow] " + " ".join(
            f"{k}={v}" for k, v in details.items()
        )
        console.print(f"[dim]{ts}[/dim] {msg}")
        if self.json_log_path:
            try:
                with open(self.json_log_path, "a") as f:
                    f.write(json.dumps({"ts": ts, "alert": kind,
                                        "iface": self.interface, **details}) + "\n")
            except OSError as e:
                console.print(f"[red]Failed to write log: {e}[/red]")

    def info(self, msg: str) -> None:
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        console.print(f"[dim]{ts}[/dim] [cyan][i][/cyan] {msg}")


# --------------------------------------------------------------------------- #
# Detection logic
# --------------------------------------------------------------------------- #
def detect_default_gateway() -> str | None:
    """Best-effort default gateway (Linux only — used for prioritized monitoring)."""
    try:
        with open("/proc/net/route") as f:
            for line in f.readlines()[1:]:
                fields = line.strip().split()
                if fields[1] == "00000000":      # default route
                    raw = fields[2]
                    octets = [str(int(raw[i:i+2], 16)) for i in range(6, -2, -2)]
                    return ".".join(octets)
    except Exception:
        return None
    return None


def handle_packet(pkt, state: ArpState) -> None:
    """Process a single sniffed packet; only ARP replies are interesting."""
    if not pkt.haslayer(ARP):
        return
    arp = pkt[ARP]

    # ARP op: 1 = who-has (request), 2 = is-at (reply)
    if arp.op != 2:
        return

    sender_ip = arp.psrc
    sender_mac = arp.hwsrc.lower()

    # Skip our own replies
    if sender_mac == state.ip_to_mac.get(sender_ip, "").lower():
        # already known — count and move on
        state.reply_counts[sender_ip] += 1
        return

    # --- Detection 1: MAC flap (IP suddenly has a new MAC) -------------------
    if sender_ip in state.ip_to_mac:
        old_mac = state.ip_to_mac[sender_ip]
        if old_mac != sender_mac:
            tag = "GATEWAY_MAC_CHANGED" if sender_ip == state.gateway_ip else "MAC_FLAP"
            state.alert(tag, ip=sender_ip, old_mac=old_mac, new_mac=sender_mac)
            # don't immediately overwrite — the old MAC may be the legitimate one;
            # we update only after we see persistent corroboration.
            state.mac_to_ips[sender_mac].add(sender_ip)
            return
    else:
        state.info(f"learned {sender_ip} → {sender_mac}")
        state.ip_to_mac[sender_ip] = sender_mac

    state.mac_to_ips[sender_mac].add(sender_ip)
    state.reply_counts[sender_ip] += 1

    # --- Detection 2: one MAC claims many IPs (classic spoofer) -------------
    ips_for_mac = state.mac_to_ips[sender_mac]
    if len(ips_for_mac) >= 3:
        state.alert(
            "ONE_MAC_MANY_IPS",
            mac=sender_mac,
            ips=sorted(ips_for_mac),
            count=len(ips_for_mac),
        )

    # --- Detection 3: floods of unsolicited replies -------------------------
    if state.reply_counts[sender_ip] > 0 and state.reply_counts[sender_ip] % 50 == 0:
        state.alert(
            "REPLY_FLOOD",
            ip=sender_ip,
            mac=sender_mac,
            count=state.reply_counts[sender_ip],
        )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Defensive ARP-spoof / ARP-poisoning detector.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Run as root / Administrator. Sniffs ARP traffic only — does not send.\n"
            "Stop with Ctrl-C. Detected alerts go to stdout and (optionally) JSON-lines log.\n"
        ),
    )
    parser.add_argument("--iface", default=None,
                        help="Interface to sniff (default: scapy's default)")
    parser.add_argument("--json-log", default=None,
                        help="Append-only JSON-lines alert log path")
    args = parser.parse_args()

    iface = args.iface or conf.iface
    try:
        own_mac = get_if_hwaddr(iface).lower()
    except Exception as e:
        raise SystemExit(f"[-] Could not read MAC of {iface}: {e}")

    if os.name == "posix" and os.geteuid() != 0:
        console.print("[yellow]⚠  Not running as root — sniff may fail.[/yellow]")

    state = ArpState(
        json_log_path=args.json_log,
        interface=str(iface),
    )
    state.gateway_ip = detect_default_gateway()
    state.info(f"Interface: {iface}  ·  Local MAC: {own_mac}")
    if state.gateway_ip:
        state.info(f"Detected default gateway: {state.gateway_ip} (will watch closely)")
    if state.json_log_path:
        state.info(f"Logging alerts to {state.json_log_path}")

    console.print("[bold green]Sniffing ARP… press Ctrl-C to stop.[/bold green]\n")

    def shutdown(signum, frame):
        console.print("\n[yellow]Stopped.[/yellow]")
        # Print summary
        seen = len(state.ip_to_mac)
        console.print(f"[dim]Saw {seen} distinct IP→MAC bindings during run.[/dim]")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        sniff(
            filter="arp",
            iface=iface,
            store=False,
            prn=lambda p: handle_packet(p, state),
        )
    except PermissionError:
        raise SystemExit("[-] Permission denied — run with sudo / as Administrator.")
    except OSError as e:
        raise SystemExit(f"[-] Sniff failed: {e}")


if __name__ == "__main__":
    main()
