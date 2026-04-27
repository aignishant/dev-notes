#!/usr/bin/env python3
"""
redshift_toolkit.scan.os_fingerprint — passive + lightweight active OS
fingerprinting using TTL distance, TCP options ordering, and HTTP banners.

Two modes:
  1. PASSIVE — read a pcap, observe SYN-ACKs and HTTP responses, score.
  2. ACTIVE  — open a TCP connection on a chosen port (default 80),
               capture the first SYN-ACK and any HTTP banner, score.

Why this matters
----------------
Knowing if a host is Windows vs Linux vs network gear changes which
exploit and recon paths to follow. Doing it without `nmap -O` (which
needs root + raw sockets and is loud) keeps you nimble.

Usage
-----
  ./os_fingerprint.py --pcap capture.pcap
  ./os_fingerprint.py --target 10.0.0.10 --port 443
  ./os_fingerprint.py --target 10.0.0.0/24 --port 80 --json

Author: Redshift Project — Module 10
License: MIT
"""

from __future__ import annotations

import argparse
import asyncio
import ipaddress
import json
import re
import socket
import sys
import time
from dataclasses import dataclass, field, asdict
from collections import Counter

GREEN = "\033[92m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


@dataclass
class Guess:
    host: str
    candidates: list[tuple[str, int]] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


# Common HTTP server hints
HTTP_HINTS = [
    (re.compile(rb"Server:\s*Microsoft-IIS", re.I), "Windows"),
    (re.compile(rb"Server:\s*Microsoft-HTTPAPI", re.I), "Windows"),
    (re.compile(rb"X-Powered-By:\s*ASP\.NET", re.I), "Windows"),
    (re.compile(rb"Server:\s*nginx", re.I), "Linux/Unix"),
    (re.compile(rb"Server:\s*Apache.*Ubuntu", re.I), "Linux (Ubuntu)"),
    (re.compile(rb"Server:\s*Apache.*Debian", re.I), "Linux (Debian)"),
    (re.compile(rb"Server:\s*Apache.*CentOS", re.I), "Linux (CentOS)"),
    (re.compile(rb"Server:\s*Apache.*Win", re.I), "Windows"),
    (re.compile(rb"Server:\s*lighttpd", re.I), "Linux/embedded"),
    (re.compile(rb"Server:\s*Werkzeug", re.I), "Linux (Python dev)"),
    (re.compile(rb"Server:\s*BaseHTTP", re.I), "Linux (Python dev)"),
]


def score_from_ttl(ttl: int) -> list[tuple[str, int]]:
    if ttl <= 0:
        return []
    if 50 <= ttl <= 64:
        return [("Linux/macOS/BSD", 70)]
    if 65 <= ttl <= 128:
        if ttl >= 110:
            return [("Windows", 75), ("Linux/macOS/BSD", 10)]
        return [("Linux/macOS/BSD", 35), ("Windows", 30)]
    if ttl >= 200:
        return [("network device (Cisco/Juniper)", 80)]
    return []


def score_from_window(win: int) -> list[tuple[str, int]]:
    """Common defaults: Linux 29200/64240, macOS 65535, Windows 8192/65535."""
    out = []
    if win in (29200, 14600, 64240, 28960):
        out.append(("Linux/macOS/BSD", 50))
    if win == 65535:
        out.append(("Windows or macOS", 30))
    if win == 8192:
        out.append(("Windows", 40))
    if win == 5840:
        out.append(("Linux (older kernel)", 50))
    return out


def score_from_options(opt_order: list[str]) -> list[tuple[str, int]]:
    """Heuristic: option ordering tells you the OS lineage.
    Modern Linux:    MSS,SACK,TS,NOP,WS  or MSS,NOP,WS,NOP,NOP,TS
    Modern Windows:  MSS,NOP,WS,NOP,NOP,SACK
    """
    s = ",".join(opt_order)
    if "SACK,TS" in s or "TS,NOP,WS" in s:
        return [("Linux/macOS/BSD", 30)]
    if "WS,NOP,NOP,SACK" in s:
        return [("Windows", 30)]
    return []


def merge(scores: list[list[tuple[str, int]]]) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for chunk in scores:
        for name, weight in chunk:
            counter[name] += weight
    return counter.most_common()


# ─── Active probing (asyncio TCP) ───────────────────────────────────────────
async def active_probe(host: str, port: int, timeout: float) -> Guess:
    g = Guess(host=host)
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout)
    except (asyncio.TimeoutError, OSError):
        g.evidence.append("connection failed")
        return g

    # Get the underlying socket TTL of the *peer's* SYN-ACK.
    # asyncio doesn't expose received TTL, so we approximate by
    # checking the local socket's IP_TTL from the kernel after connect.
    sock = writer.get_extra_info("socket")
    ttl_seen = None
    if sock is not None:
        try:
            ttl_seen = sock.getsockopt(socket.IPPROTO_IP, socket.IP_TTL)
        except OSError:
            pass

    # Send a probe to elicit an HTTP banner if applicable.
    banner = b""
    try:
        writer.write(b"GET / HTTP/1.0\r\nHost: probe\r\n\r\n")
        await writer.drain()
        try:
            banner = await asyncio.wait_for(reader.read(2048), timeout=timeout)
        except asyncio.TimeoutError:
            pass
    except Exception:
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    scores: list[list[tuple[str, int]]] = []
    if ttl_seen is not None:
        # Note: IP_TTL is the OUTBOUND TTL of our socket, not the peer's.
        # For a meaningful peer-TTL we'd need raw sockets; what we can do
        # is record the banner-derived hints.
        g.evidence.append(f"local IP_TTL on socket: {ttl_seen}")
    if banner:
        for rx, label in HTTP_HINTS:
            if rx.search(banner):
                g.evidence.append(f"HTTP hint: {label}")
                scores.append([(label, 60)])
                break
        if banner[:5] == b"HTTP/":
            g.evidence.append(f"got HTTP banner ({len(banner)} bytes)")

    if scores:
        g.candidates = merge(scores)
    else:
        g.evidence.append("insufficient evidence (no banner, no peer TTL)")
    return g


def passive_pcap(path: str) -> dict[str, Guess]:
    try:
        from scapy.all import rdpcap, IP, TCP, Raw  # type: ignore
    except ImportError:
        print("Passive mode needs scapy: pip install scapy", file=sys.stderr)
        sys.exit(2)

    guesses: dict[str, Guess] = {}
    for p in rdpcap(path):
        if not (p.haslayer(IP) and p.haslayer(TCP)):
            continue
        ttl = int(p[IP].ttl)
        win = int(p[TCP].window)
        flags = int(p[TCP].flags)
        # Look at SYN-ACKs to fingerprint the responder
        if flags & 0x12 == 0x12:  # SYN+ACK
            host = p[IP].src
            g = guesses.setdefault(host, Guess(host=host))
            opts = [name for name, _ in (p[TCP].options or [])]
            scores = [
                score_from_ttl(ttl),
                score_from_window(win),
                score_from_options(opts),
            ]
            g.evidence.append(f"SYN-ACK ttl={ttl} win={win} opts={','.join(opts)}")
            existing = dict(g.candidates)
            for chunk in scores:
                for name, w in chunk:
                    existing[name] = existing.get(name, 0) + w
            g.candidates = sorted(existing.items(), key=lambda kv: -kv[1])
        elif p.haslayer(Raw) and p[TCP].sport in (80, 8080, 8000):
            data = bytes(p[Raw].load)
            host = p[IP].src
            g = guesses.setdefault(host, Guess(host=host))
            for rx, label in HTTP_HINTS:
                if rx.search(data):
                    g.evidence.append(f"HTTP hint: {label}")
                    existing = dict(g.candidates)
                    existing[label] = existing.get(label, 0) + 60
                    g.candidates = sorted(existing.items(), key=lambda kv: -kv[1])
                    break
    return guesses


def expand(spec: str) -> list[str]:
    if "/" in spec:
        return [str(ip) for ip in ipaddress.ip_network(spec, strict=False).hosts()]
    if "-" in spec and spec.count(".") == 3:
        base, last = spec.rsplit(".", 1)
        if "-" in last:
            lo, hi = last.split("-")
            return [f"{base}.{i}" for i in range(int(lo), int(hi) + 1)]
    try:
        return [socket.gethostbyname(spec)]
    except socket.gaierror:
        return [spec]


def render_text(guesses: list[Guess], color: bool) -> str:
    out = []
    for g in guesses:
        out.append(paint(f"\n── {g.host} ──", BOLD, color))
        if g.candidates:
            top = g.candidates[0]
            out.append(paint(f"  best guess: {top[0]} (score={top[1]})",
                             GREEN, color))
            for name, score in g.candidates[1:5]:
                out.append(paint(f"    alternative: {name} ({score})", GREY, color))
        else:
            out.append(paint("  no candidate scored", YELLOW, color))
        for ev in g.evidence[:6]:
            out.append(paint(f"  evidence: {ev}", GREY, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="OS fingerprint via TTL/options/banner.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--target", help="IP/CIDR/range/hostname for active probing")
    g.add_argument("--pcap", help="pcap to analyze passively")
    ap.add_argument("--port", type=int, default=80,
                    help="port for active probing (HTTP banner most useful)")
    ap.add_argument("--timeout", type=float, default=3.0)
    ap.add_argument("--concurrency", type=int, default=50)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    if args.pcap:
        guesses = list(passive_pcap(args.pcap).values())
    else:
        targets = sorted(set(expand(args.target)))
        sem = asyncio.Semaphore(args.concurrency)

        async def go(h):
            async with sem:
                return await active_probe(h, args.port, args.timeout)

        async def runner():
            return await asyncio.gather(*[go(h) for h in targets])

        guesses = asyncio.run(runner())

    if args.json:
        print(json.dumps([asdict(g) for g in guesses], indent=2))
    else:
        print(render_text(guesses, color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
