#!/usr/bin/env python3
"""
redshift_toolkit.net.network_mapper — passive host discovery and OS
fingerprinting from sniffed traffic or a pcap.

Why passive
-----------
Active scanning (`nmap`) is loud and triggers IDS rules. Passive mapping
just listens to traffic that is already on the wire — switching, ARP,
DHCP, broadcasts, mDNS, NetBIOS, traffic between observed hosts — and
infers a network map. Perfect during low-and-slow recon.

What it produces
----------------
For each observed host:
  - IP and MAC address (when seen on L2)
  - OUI vendor (from MAC)
  - Hostnames seen in mDNS, NetBIOS, DHCP requests
  - OS guess from initial-TTL + TCP options ordering (basic p0f-style)
  - Services it talked to and that talked to it (ports observed)
  - First/last seen timestamps

API
---
  from redshift_toolkit.net.network_mapper import map_pcap, map_live
  hosts = map_pcap("capture.pcap")
  hosts = map_live("eth0", duration=60)

CLI
---
  python3 -m redshift_toolkit.net.network_mapper --pcap capture.pcap
  sudo python3 -m redshift_toolkit.net.network_mapper --iface eth0 --duration 60

Author: Redshift Project — Module 06
License: MIT
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict

try:
    from scapy.all import (rdpcap, sniff, conf, Ether, ARP, IP, IPv6,
                           TCP, UDP, DNS, DNSQR, BOOTP, DHCP, Raw)  # type: ignore
except ImportError:
    print("Requires scapy: pip install scapy", file=sys.stderr)
    sys.exit(2)

GREEN = "\033[92m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


@dataclass
class Host:
    ip: str
    mac: str | None = None
    vendor: str | None = None
    hostnames: set[str] = field(default_factory=set)
    os_guess: str | None = None
    ports_seen_in: set[int] = field(default_factory=set)
    ports_seen_out: set[int] = field(default_factory=set)
    first_seen: float = 0.0
    last_seen: float = 0.0
    flow_count: int = 0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["hostnames"] = sorted(self.hostnames)
        d["ports_seen_in"] = sorted(self.ports_seen_in)
        d["ports_seen_out"] = sorted(self.ports_seen_out)
        return d


# Tiny OUI map (extend with a real database for production).
OUI = {
    "00:50:56": "VMware",
    "00:0c:29": "VMware",
    "52:54:00": "QEMU/KVM",
    "08:00:27": "VirtualBox",
    "00:1c:42": "Parallels",
    "00:15:5d": "Microsoft Hyper-V",
    "ac:de:48": "Apple",
    "b8:27:eb": "Raspberry Pi Foundation",
    "dc:a6:32": "Raspberry Pi (Trading)",
    "00:0f:00": "Cisco",
    "00:1b:21": "Intel",
    "00:e0:4c": "Realtek",
    "f0:18:98": "Apple",
    "ec:fa:bc": "Apple",
    "f8:e4:3b": "ARRIS",
}


def vendor_lookup(mac: str) -> str | None:
    if not mac or mac == "ff:ff:ff:ff:ff:ff":
        return None
    return OUI.get(mac.lower()[:8])


def guess_os_from_ttl(ttl: int) -> str | None:
    """Common defaults: Linux 64, macOS 64, Windows 128, network gear 255."""
    if ttl <= 0:
        return None
    if ttl <= 64:
        return "Linux/macOS/BSD" if ttl > 32 else "low-TTL device"
    if ttl <= 128:
        return "Windows"
    return "network device (TTL ~255)"


def map_packets(packets) -> dict[str, Host]:
    hosts: dict[str, Host] = {}

    def touch(ip: str, ts: float) -> Host:
        h = hosts.get(ip)
        if h is None:
            h = Host(ip=ip, first_seen=ts, last_seen=ts)
            hosts[ip] = h
        else:
            h.last_seen = ts
        return h

    for p in packets:
        ts = float(p.time) if hasattr(p, "time") else time.time()

        # ARP — bind IP <-> MAC
        if p.haslayer(ARP):
            arp = p[ARP]
            if arp.psrc and arp.psrc != "0.0.0.0":
                h = touch(arp.psrc, ts)
                h.mac = arp.hwsrc
                h.vendor = vendor_lookup(arp.hwsrc)
            if arp.pdst and arp.pdst not in ("0.0.0.0", "255.255.255.255"):
                touch(arp.pdst, ts)

        # IP/IPv6 + TCP/UDP — record observed flows and ports
        if p.haslayer(IP):
            src, dst = p[IP].src, p[IP].dst
            ttl = p[IP].ttl
            sh = touch(src, ts)
            dh = touch(dst, ts)
            if sh.os_guess is None:
                sh.os_guess = guess_os_from_ttl(ttl)
            sh.flow_count += 1
            if p.haslayer(Ether):
                if not sh.mac:
                    sh.mac = p[Ether].src
                    sh.vendor = vendor_lookup(p[Ether].src)
            if p.haslayer(TCP):
                sh.ports_seen_out.add(int(p[TCP].dport))
                dh.ports_seen_in.add(int(p[TCP].dport))
            if p.haslayer(UDP):
                sh.ports_seen_out.add(int(p[UDP].dport))
                dh.ports_seen_in.add(int(p[UDP].dport))
        elif p.haslayer(IPv6):
            src, dst = p[IPv6].src, p[IPv6].dst
            sh = touch(src, ts); touch(dst, ts)
            sh.flow_count += 1

        # DNS / mDNS — collect hostnames the host queries (often own name leaks)
        if p.haslayer(DNS) and p.haslayer(DNSQR) and p.haslayer(IP):
            qname = p[DNSQR].qname
            if isinstance(qname, bytes):
                qname = qname.decode("ascii", errors="replace").rstrip(".")
            if qname and qname.endswith(".local"):
                touch(p[IP].src, ts).hostnames.add(qname)

        # DHCP — hostname is in option 12
        if p.haslayer(DHCP) and p.haslayer(BOOTP):
            for opt in p[DHCP].options:
                if isinstance(opt, tuple) and opt[0] == "hostname":
                    name = opt[1]
                    if isinstance(name, bytes):
                        name = name.decode("utf-8", errors="replace")
                    if p.haslayer(IP):
                        touch(p[IP].src, ts).hostnames.add(name)
                    elif p[BOOTP].ciaddr:
                        touch(p[BOOTP].ciaddr, ts).hostnames.add(name)

        # NetBIOS Name Service (UDP/137) — quick parse for sender's name
        if p.haslayer(UDP) and p[UDP].sport == 137 and p.haslayer(Raw):
            data = bytes(p[Raw].load)
            # NBNS encodes names with first-half-byte, second-half-byte ASCII
            if len(data) > 12 and data[12] == 0x20:
                enc = data[13:13 + 32]
                try:
                    decoded = "".join(
                        chr(((enc[i] - 0x41) << 4) | (enc[i + 1] - 0x41))
                        for i in range(0, 32, 2)
                    ).rstrip()
                    if decoded.isprintable() and p.haslayer(IP):
                        touch(p[IP].src, ts).hostnames.add(decoded)
                except Exception:
                    pass

    return hosts


def map_pcap(path: str) -> dict[str, Host]:
    return map_packets(rdpcap(path))


def map_live(iface: str, duration: int = 60) -> dict[str, Host]:
    conf.verb = 0
    pkts = sniff(iface=iface, timeout=duration, store=True)
    return map_packets(pkts)


def render_text(hosts: dict[str, Host], color: bool) -> str:
    out = []
    if not hosts:
        return paint("[!] no hosts observed", YELLOW, color)
    out.append(paint(f"\n=== Observed {len(hosts)} host(s) ===", BOLD, color))
    for ip in sorted(hosts):
        h = hosts[ip]
        line = f"\n  {paint(ip, GREEN, color):<25}"
        if h.mac:
            line += f"  mac={h.mac}"
        if h.vendor:
            line += f"  vendor={h.vendor}"
        if h.os_guess:
            line += f"  os?={h.os_guess}"
        out.append(line)
        if h.hostnames:
            out.append(f"      hostnames: {', '.join(sorted(h.hostnames))}")
        if h.ports_seen_out:
            out.append(f"      → talked to ports: "
                       f"{', '.join(str(p) for p in sorted(h.ports_seen_out)[:15])}"
                       f"{' …' if len(h.ports_seen_out) > 15 else ''}")
        if h.ports_seen_in:
            out.append(f"      ← was contacted on: "
                       f"{', '.join(str(p) for p in sorted(h.ports_seen_in)[:15])}"
                       f"{' …' if len(h.ports_seen_in) > 15 else ''}")
        out.append(paint(f"      flows={h.flow_count}", GREY, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Passive network mapper.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pcap", help="path to .pcap / .pcapng")
    g.add_argument("--iface", help="interface to sniff")
    ap.add_argument("--duration", type=int, default=60,
                    help="seconds to sniff in live mode")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()

    color = sys.stdout.isatty() and not args.no_color and args.format == "text"

    if args.pcap:
        hosts = map_pcap(args.pcap)
    else:
        try:
            hosts = map_live(args.iface, args.duration)
        except PermissionError:
            print("Need root / CAP_NET_RAW to sniff.", file=sys.stderr)
            return 2

    if args.format == "json":
        print(json.dumps({ip: h.to_dict() for ip, h in sorted(hosts.items())},
                         indent=2, default=str))
    else:
        print(render_text(hosts, color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
