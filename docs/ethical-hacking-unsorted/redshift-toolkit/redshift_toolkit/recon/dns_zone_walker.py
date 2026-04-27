#!/usr/bin/env python3
"""
redshift_toolkit.recon.dns_zone_walker — DNSSEC zone walking + AXFR.

What it does
------------
1. AXFR (DNS zone transfer) attempt against each authoritative NS for
   the target. Most modern providers refuse, but you'll still find
   AXFR-permissive infrastructure in lab, government, and ICS networks.
2. NSEC walking: when a DNSSEC-signed zone uses NSEC (not NSEC3),
   each name's record points at the *next* existing name. Walking the
   chain enumerates every name in the zone.
3. NSEC3 hash collection: for NSEC3 zones, harvest the hashes (offline
   cracking with hashcat 8300 is the recommended next step).

No external libraries — uses the same DNS encoder/parser as
`dns_client.py` from Module 8.

Usage
-----
  python3 -m redshift_toolkit.recon.dns_zone_walker example.com
  python3 -m redshift_toolkit.recon.dns_zone_walker example.com \\
      --ns ns1.example.com --json
  python3 -m redshift_toolkit.recon.dns_zone_walker example.com --no-axfr

Author: Redshift Project — Module 11
License: MIT
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import struct
import sys
import time
from dataclasses import dataclass, asdict, field

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


# ─── DNS encode/decode (copied/condensed from dns_client.py) ────────────────
def encode_name(name: str) -> bytes:
    out = bytearray()
    for label in name.rstrip(".").split("."):
        if not label:
            continue
        b = label.encode("ascii")
        out.append(len(b))
        out.extend(b)
    out.append(0)
    return bytes(out)


def build_query(name: str, qtype: int) -> bytes:
    txid = int.from_bytes(os.urandom(2), "big")
    flags = 0x0100  # RD
    return struct.pack(">HHHHHH", txid, flags, 1, 0, 0, 0) + \
           encode_name(name) + struct.pack(">HH", qtype, 1)


def read_name(data: bytes, off: int) -> tuple[str, int]:
    labels: list[str] = []
    saw_ptr = False
    next_off = off
    safety = 0
    while True:
        if safety > 64 or off >= len(data):
            return ".".join(labels), next_off
        safety += 1
        ln = data[off]
        if ln == 0:
            off += 1
            if not saw_ptr:
                next_off = off
            return ".".join(labels), next_off
        if (ln & 0xC0) == 0xC0:
            ptr = ((ln & 0x3F) << 8) | data[off + 1]
            if not saw_ptr:
                next_off = off + 2
                saw_ptr = True
            off = ptr
            continue
        off += 1
        labels.append(data[off:off + ln].decode("ascii", errors="replace"))
        off += ln


def parse(data: bytes) -> dict:
    """Return rcode + per-section RR list with rtype + rdata bytes + name."""
    out = {"rcode": -1, "answers": [], "authority": [], "additional": []}
    if len(data) < 12:
        return out
    txid, flags, qd, an, ns, ar = struct.unpack(">HHHHHH", data[:12])
    out["rcode"] = flags & 0x0F
    off = 12
    for _ in range(qd):
        _, off = read_name(data, off)
        off += 4

    def parse_section(off: int, count: int, key: str):
        nonlocal_off = off
        for _ in range(count):
            name, nonlocal_off = read_name(data, nonlocal_off)
            if nonlocal_off + 10 > len(data):
                return nonlocal_off
            rtype, rclass, ttl, rdlen = struct.unpack(
                ">HHIH", data[nonlocal_off:nonlocal_off + 10])
            nonlocal_off += 10
            rdata = data[nonlocal_off:nonlocal_off + rdlen]
            nonlocal_off += rdlen
            out[key].append({
                "name": name, "type": rtype, "class": rclass,
                "ttl": ttl, "rdata": rdata,
            })
        return nonlocal_off

    off = parse_section(off, an, "answers")
    off = parse_section(off, ns, "authority")
    off = parse_section(off, ar, "additional")
    return out


# ─── Network helpers ────────────────────────────────────────────────────────
def udp_query(server: str, payload: bytes, timeout: float = 3.0) -> bytes | None:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        s.sendto(payload, (server, 53))
        data, _ = s.recvfrom(4096)
        s.close()
        return data
    except OSError:
        return None


def tcp_query(server: str, payload: bytes, timeout: float = 5.0) -> bytes | None:
    """Return raw response (length-prefix stripped)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((server, 53))
        s.sendall(struct.pack(">H", len(payload)) + payload)
        chunks = []
        while True:
            ln_b = b""
            while len(ln_b) < 2:
                c = s.recv(2 - len(ln_b))
                if not c:
                    return None
                ln_b += c
            (ln,) = struct.unpack(">H", ln_b)
            buf = b""
            while len(buf) < ln:
                c = s.recv(ln - len(buf))
                if not c:
                    return None
                buf += c
            chunks.append(buf)
            try:
                s.settimeout(1.0)
                peek = s.recv(0)
            except (socket.timeout, OSError):
                break
            if not peek:
                break
        s.close()
        return b"".join(chunks) if chunks else None
    except OSError:
        return None


def axfr_attempt(domain: str, ns: str, timeout: float = 8.0) -> tuple[bool, list[str], str | None]:
    """AXFR is qtype 252. Streamed over TCP. Multi-message reply."""
    payload = build_query(domain, 252)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ns, 53))
        s.sendall(struct.pack(">H", len(payload)) + payload)
        names: set[str] = set()
        deadline = time.time() + timeout
        while time.time() < deadline:
            ln_b = b""
            while len(ln_b) < 2:
                try:
                    c = s.recv(2 - len(ln_b))
                except (socket.timeout, OSError):
                    c = b""
                if not c:
                    s.close()
                    return (len(names) > 0, sorted(names), None)
                ln_b += c
            (ln,) = struct.unpack(">H", ln_b)
            buf = b""
            while len(buf) < ln:
                try:
                    c = s.recv(ln - len(buf))
                except (socket.timeout, OSError):
                    c = b""
                if not c:
                    break
                buf += c
            resp = parse(buf)
            for sect in ("answers", "authority", "additional"):
                for rr in resp.get(sect, []):
                    n = rr.get("name", "").lower()
                    if n and (n.endswith(domain) or n == domain.rstrip(".")):
                        names.add(n)
            if resp.get("rcode") not in (0,):
                break
        s.close()
        return (len(names) > 0, sorted(names), None)
    except OSError as e:
        return False, [], str(e)


# ─── NSEC walking ───────────────────────────────────────────────────────────
def parse_nsec_rdata(rdata: bytes, full: bytes) -> str | None:
    """First field of NSEC rdata is the next domain name."""
    try:
        off = full.find(rdata)
        if off < 0:
            return None
        name, _ = read_name(full, off)
        return name.rstrip(".").lower()
    except Exception:
        return None


def query_nsec(server: str, name: str, timeout: float) -> tuple[str | None, bytes]:
    """Returns the next-name in the NSEC chain, or None if unsupported."""
    payload = build_query(name, 47)  # NSEC = 47
    data = udp_query(server, payload, timeout) or tcp_query(server, payload, timeout) or b""
    if not data:
        return None, b""
    resp = parse(data)
    for rr in resp.get("answers", []) + resp.get("authority", []):
        if rr["type"] == 47:
            nxt = parse_nsec_rdata(rr["rdata"], data)
            if nxt:
                return nxt, data
    return None, data


def walk_nsec(domain: str, server: str, max_steps: int = 5000,
              timeout: float = 3.0) -> list[str]:
    seen: set[str] = set()
    current = domain.lower().rstrip(".")
    for _ in range(max_steps):
        nxt, _ = query_nsec(server, current, timeout)
        if not nxt or nxt in seen:
            break
        if not nxt.endswith(domain):
            break
        seen.add(nxt)
        current = nxt
    return sorted(seen)


# ─── Driver ─────────────────────────────────────────────────────────────────
def find_nameservers(domain: str, resolver: str = "1.1.1.1",
                     timeout: float = 3.0) -> list[str]:
    payload = build_query(domain, 2)  # NS
    data = udp_query(resolver, payload, timeout)
    if not data:
        return []
    resp = parse(data)
    out: list[str] = []
    for rr in resp.get("answers", []) + resp.get("authority", []):
        if rr["type"] == 2:
            try:
                off = data.index(rr["rdata"])
                ns_name, _ = read_name(data, off)
                out.append(ns_name.rstrip(".").lower())
            except ValueError:
                continue
    return list(dict.fromkeys(out))


def resolve_a(host: str, resolver: str, timeout: float) -> str | None:
    payload = build_query(host, 1)
    data = udp_query(resolver, payload, timeout)
    if not data:
        return None
    resp = parse(data)
    for rr in resp.get("answers", []):
        if rr["type"] == 1 and len(rr["rdata"]) == 4:
            return ".".join(str(b) for b in rr["rdata"])
    return None


@dataclass
class Report:
    target: str
    nameservers: list[str] = field(default_factory=list)
    axfr_attempts: list[dict] = field(default_factory=list)
    axfr_zone: list[str] = field(default_factory=list)
    nsec_walk: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def run(domain: str, resolver: str, ns_override: list[str] | None,
        do_axfr: bool, do_nsec: bool, timeout: float) -> Report:
    rep = Report(target=domain)
    nsl = ns_override or find_nameservers(domain, resolver, timeout)
    if not nsl:
        rep.notes.append("could not locate nameservers")
        return rep
    rep.nameservers = nsl

    ns_ips: list[tuple[str, str]] = []
    for n in nsl:
        ip = resolve_a(n, resolver, timeout)
        if ip:
            ns_ips.append((n, ip))

    if do_axfr:
        for ns, ip in ns_ips:
            ok, names, err = axfr_attempt(domain, ip, timeout=8.0)
            rep.axfr_attempts.append({
                "ns": ns, "ip": ip, "permitted": ok,
                "names": len(names), "error": err,
            })
            if ok:
                rep.axfr_zone.extend(names)
        rep.axfr_zone = sorted(set(rep.axfr_zone))

    if do_nsec and ns_ips:
        # Try each NS until one yields an NSEC chain
        for ns, ip in ns_ips:
            walked = walk_nsec(domain, ip, max_steps=3000, timeout=timeout)
            if walked:
                rep.nsec_walk = walked
                rep.notes.append(f"NSEC walk via {ns} ({ip}) → {len(walked)}")
                break
        else:
            rep.notes.append("no NSEC chain found (zone may use NSEC3 or be unsigned)")
    return rep


def render_text(rep: Report, color: bool) -> str:
    out = [paint(f"\n=== DNS zone walk: {rep.target} ===", BOLD, color)]
    out.append(f"  nameservers: {', '.join(rep.nameservers) or '?'}")
    if rep.axfr_attempts:
        out.append(paint("\n  AXFR attempts:", BOLD, color))
        for a in rep.axfr_attempts:
            mark = paint("ALLOWED", RED, color) if a["permitted"] else paint("refused", GREEN, color)
            out.append(f"    {a['ns']} ({a['ip']}): {mark}  names={a['names']}"
                       + (f"  err={a['error']}" if a['error'] else ""))
    if rep.axfr_zone:
        out.append(paint(f"\n  AXFR zone names: {len(rep.axfr_zone)}", BOLD, color))
        for n in rep.axfr_zone[:30]:
            out.append(f"    - {n}")
        if len(rep.axfr_zone) > 30:
            out.append(f"    ... and {len(rep.axfr_zone) - 30} more")
    if rep.nsec_walk:
        out.append(paint(f"\n  NSEC walk: {len(rep.nsec_walk)}", BOLD, color))
        for n in rep.nsec_walk[:30]:
            out.append(f"    - {n}")
        if len(rep.nsec_walk) > 30:
            out.append(f"    ... and {len(rep.nsec_walk) - 30} more")
    for note in rep.notes:
        out.append(paint(f"  note: {note}", YELLOW, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="DNS zone walker (NSEC + AXFR).")
    ap.add_argument("domain")
    ap.add_argument("--ns", default=None,
                    help="comma-separated authoritative server override")
    ap.add_argument("--resolver", default="1.1.1.1",
                    help="recursive resolver for the initial NS lookup")
    ap.add_argument("--no-axfr", action="store_true")
    ap.add_argument("--no-nsec", action="store_true")
    ap.add_argument("--timeout", type=float, default=3.0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    ns_list = [s.strip() for s in args.ns.split(",")] if args.ns else None

    rep = run(args.domain, args.resolver, ns_list,
              do_axfr=not args.no_axfr, do_nsec=not args.no_nsec,
              timeout=args.timeout)

    if args.json:
        print(json.dumps(asdict(rep), indent=2))
    else:
        print(render_text(rep, color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
