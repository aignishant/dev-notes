#!/usr/bin/env python3
"""
handshake_analyzer.py — Analyze WPA / WPA2 handshake & PMKID captures.

Inspects a packet capture (pcap or pcapng) and extracts:
  - All BSSIDs and their advertised SSIDs (from beacons / probe-resp)
  - Channels and signal info if present
  - Encryption type (WPA / WPA2 / WPA3 / OPN)
  - 4-way handshake completeness per (BSSID, client) pair
  - PMKID-bearing EAPOL-M1 frames (PMKID attack candidates)
  - Hashcat-ready hash lines (mode 22000 format) where possible

Optional: runs `hcxpcapngtool` if available for the canonical conversion;
otherwise produces a structured report only (you can convert with:
    hcxpcapngtool -o out.22000 capture.pcap
).

⚠️ AUTHORIZATION REQUIRED ⚠️
The capture file must come from a network you own or are explicitly
authorized to analyze. Reading WPA handshakes from networks you don't
own may violate computer-misuse laws.

Dependencies:
    pip install scapy

Usage:
    python3 handshake_analyzer.py capture.pcap
    python3 handshake_analyzer.py capture.pcap --json -o report.json
    python3 handshake_analyzer.py capture.pcap --convert handshake.22000
"""
from __future__ import annotations

import argparse
import binascii
import json
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict

try:
    from scapy.all import rdpcap, Dot11, Dot11Beacon, Dot11ProbeResp, Dot11Elt, EAPOL
except ImportError:
    print("ERROR: scapy is required. pip install scapy", file=sys.stderr)
    sys.exit(2)


@dataclass
class APInfo:
    bssid: str
    ssid: str = ""
    channel: int | None = None
    encryption: str = "Unknown"     # WPA / WPA2 / WPA3 / OPN
    cipher: str = ""
    auth: str = ""                  # PSK / MGT (Enterprise)


@dataclass
class HandshakeProgress:
    bssid: str
    client: str
    seen_messages: set[int] = field(default_factory=set)        # 1-4
    pmkid: str | None = None        # AP-side PMKID (M1)
    a_nonce: str | None = None
    s_nonce: str | None = None
    mic: str | None = None

    def is_complete(self) -> bool:
        # Hashcat needs at least M1+M2 (PMKID) OR M2+M3 (or full 4-way).
        return self.pmkid is not None or {2, 3}.issubset(self.seen_messages)


@dataclass
class Report:
    capture_file: str
    aps: list[APInfo] = field(default_factory=list)
    handshakes: list[dict] = field(default_factory=list)
    pmkids: list[dict] = field(default_factory=list)
    hashcat_lines: list[str] = field(default_factory=list)


def parse_eapol_key(payload: bytes) -> dict:
    """Parse EAPOL-Key (802.11 4-way handshake) frame."""
    # Per IEEE 802.11i; layout (after EAPOL header which is 4 bytes):
    #   1 byte  type (always 0x02 for IEEE 802.11)
    #   2 bytes Key Information
    #   2 bytes Key Length
    #   8 bytes Replay Counter
    #  32 bytes Key Nonce
    #  16 bytes EAPOL Key IV
    #   8 bytes Key RSC
    #   8 bytes Key ID
    #  16 bytes Key MIC
    #   2 bytes Key Data Length
    #     n bytes Key Data
    if len(payload) < 95:
        return {}
    info = {}
    info["type"] = payload[0]
    info["key_info"] = int.from_bytes(payload[1:3], "big")
    info["key_length"] = int.from_bytes(payload[3:5], "big")
    info["nonce"] = payload[13:45].hex()
    info["mic"] = payload[77:93].hex()
    info["key_data_length"] = int.from_bytes(payload[93:95], "big")
    info["key_data"] = payload[95: 95 + info["key_data_length"]].hex()
    # Determine which message
    ki = info["key_info"]
    install = bool(ki & 0x40)
    ack = bool(ki & 0x80)
    mic_bit = bool(ki & 0x100)
    secure = bool(ki & 0x200)
    if ack and not mic_bit and not install:
        info["m"] = 1
    elif not ack and mic_bit and not secure and not install:
        info["m"] = 2
    elif ack and mic_bit and install:
        info["m"] = 3
    elif not ack and mic_bit and secure:
        info["m"] = 4
    else:
        info["m"] = None
    # PMKID (in Key Data of M1) — 22 bytes: type=0xdd len=0x14 oui=0x000fac type=4 + 16 bytes
    kd = bytes.fromhex(info["key_data"])
    if info["m"] == 1 and len(kd) >= 22 and kd[:2] == b"\xdd\x14" and kd[2:6] == b"\x00\x0f\xac\x04":
        info["pmkid"] = kd[6:22].hex()
    return info


def analyze(capfile: str) -> Report:
    pkts = rdpcap(capfile)
    aps: dict[str, APInfo] = {}
    handshakes: dict[tuple[str, str], HandshakeProgress] = {}

    for pkt in pkts:
        if not pkt.haslayer(Dot11):
            continue
        d11 = pkt[Dot11]

        # Beacons / Probe Responses → AP metadata
        if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp):
            bssid = (d11.addr3 or "").lower()
            if not bssid:
                continue
            ap = aps.get(bssid) or APInfo(bssid=bssid)

            # Walk Dot11Elt chain for SSID / Channel / RSN
            elt = pkt.getlayer(Dot11Elt)
            while elt is not None:
                try:
                    if elt.ID == 0:  # SSID
                        try:
                            ap.ssid = elt.info.decode("utf-8", errors="replace")
                        except Exception:
                            ap.ssid = elt.info.hex()
                    elif elt.ID == 3:  # DS Parameter Set (channel)
                        ap.channel = int.from_bytes(elt.info, "little") if elt.info else None
                    elif elt.ID == 48:  # RSN (WPA2/WPA3)
                        if not ap.encryption.startswith("WPA"):
                            ap.encryption = "WPA2"
                        # WPA3 detection — look for SAE AKM (00-0f-ac-08)
                        if b"\x00\x0f\xac\x08" in elt.info:
                            ap.encryption = "WPA3"
                        if b"\x00\x0f\xac\x02" in elt.info:
                            ap.auth = "PSK"
                        if b"\x00\x0f\xac\x01" in elt.info:
                            ap.auth = "MGT"  # 802.1X / Enterprise
                    elif elt.ID == 221 and elt.info[:4] == b"\x00\x50\xf2\x01":  # WPA1 vendor
                        ap.encryption = "WPA"
                except Exception:
                    pass
                elt = elt.payload.getlayer(Dot11Elt) if elt.payload else None
            aps[bssid] = ap
            continue

        # EAPOL frames — handshake or PMKID
        if pkt.haslayer(EAPOL):
            try:
                # Determine direction (which is BSSID, which is client)
                # If FromDS=1 → from AP, ToDS=0 → addr1 is dest (client), addr2 is BSSID
                # If FromDS=0 ToDS=1 → from client, addr1 is BSSID, addr2 is client
                fc = d11.FCfield
                from_ds = bool(int(fc) & 0x2)
                to_ds = bool(int(fc) & 0x1)
                if from_ds and not to_ds:
                    bssid = (d11.addr2 or "").lower()
                    client = (d11.addr1 or "").lower()
                elif to_ds and not from_ds:
                    bssid = (d11.addr1 or "").lower()
                    client = (d11.addr2 or "").lower()
                else:
                    continue

                eapol = bytes(pkt[EAPOL].payload)
                info = parse_eapol_key(eapol)
                if not info or info.get("m") is None:
                    continue

                key = (bssid, client)
                hs = handshakes.get(key) or HandshakeProgress(bssid=bssid, client=client)
                hs.seen_messages.add(info["m"])
                if info["m"] == 1:
                    hs.a_nonce = info["nonce"]
                    if "pmkid" in info and info["pmkid"] != "00" * 16:
                        hs.pmkid = info["pmkid"]
                elif info["m"] == 2:
                    hs.s_nonce = info["nonce"]
                    hs.mic = info["mic"]
                handshakes[key] = hs
            except Exception:
                continue

    # Build report
    report = Report(capture_file=capfile)
    report.aps = sorted(aps.values(), key=lambda a: a.bssid)

    for hs in handshakes.values():
        ap = aps.get(hs.bssid)
        ssid = ap.ssid if ap else ""
        rec = {
            "bssid": hs.bssid,
            "client": hs.client,
            "ssid": ssid,
            "messages_seen": sorted(hs.seen_messages),
            "complete": hs.is_complete(),
            "has_pmkid": hs.pmkid is not None,
        }
        report.handshakes.append(rec)
        if hs.pmkid:
            report.pmkids.append({
                "bssid": hs.bssid,
                "client": hs.client,
                "ssid": ssid,
                "pmkid": hs.pmkid,
            })
            # Hashcat 22000 PMKID line: WPA*01*PMKID*BSSID*CLIENT*ESSID***
            essid_hex = ssid.encode().hex() if ssid else ""
            report.hashcat_lines.append(
                f"WPA*01*{hs.pmkid}*{hs.bssid.replace(':','')}*{hs.client.replace(':','')}*{essid_hex}***"
            )

    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("capture", help="pcap / pcapng file")
    p.add_argument("--json", action="store_true", help="Output JSON")
    p.add_argument("-o", "--output", help="Write JSON to file")
    p.add_argument("--convert", metavar="OUTFILE", help="Run hcxpcapngtool to produce a 22000 file")
    args = p.parse_args()

    print(f"[*] Reading {args.capture}...", file=sys.stderr)
    try:
        report = analyze(args.capture)
    except FileNotFoundError:
        print(f"[-] File not found: {args.capture}", file=sys.stderr)
        return 1

    if args.convert:
        hcx = shutil.which("hcxpcapngtool")
        if hcx:
            print(f"[*] Running hcxpcapngtool -o {args.convert}", file=sys.stderr)
            try:
                subprocess.run([hcx, "-o", args.convert, args.capture], check=False)
            except subprocess.SubprocessError as e:
                print(f"[!] hcxpcapngtool failed: {e}", file=sys.stderr)
        else:
            print("[!] hcxpcapngtool not in PATH; skipping --convert", file=sys.stderr)

    if args.json or args.output:
        out = json.dumps(asdict(report), indent=2, default=str)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(out)
            print(f"[+] Wrote {args.output}", file=sys.stderr)
        else:
            print(out)
    else:
        print(f"\n=== Capture: {args.capture} ===")
        print(f"\nAccess Points: {len(report.aps)}")
        for ap in report.aps:
            print(f"  {ap.bssid}  ch={ap.channel or '?':>3}  {ap.encryption:6} {ap.auth:4}  {ap.ssid!r}")
        print(f"\nHandshakes: {len(report.handshakes)}")
        for hs in report.handshakes:
            mark = "✓" if hs["complete"] else "·"
            pmk = " [PMKID]" if hs["has_pmkid"] else ""
            print(f"  {mark} {hs['bssid']} ↔ {hs['client']}  ssid={hs['ssid']!r}  M={hs['messages_seen']}{pmk}")
        if report.hashcat_lines:
            print(f"\nHashcat 22000 lines ({len(report.hashcat_lines)} PMKID):")
            for h in report.hashcat_lines:
                print(f"  {h}")
            print("\n  Crack with: hashcat -m 22000 hashes.22000 wordlist.txt")

    return 0


if __name__ == "__main__":
    sys.exit(main())
