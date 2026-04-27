#!/usr/bin/env python3
"""
redshift_toolkit.recon.subdomain_enum — async DNS subdomain brute-force.

Features
--------
- Async resolution with bounded concurrency.
- Multi-resolver rotation (1.1.1.1, 8.8.8.8, 9.9.9.9, 8.8.4.4, 1.0.0.1).
- Wildcard DNS detection: queries `*.<target>` first; if it resolves,
  every subdomain match against the wildcard IP set is filtered out.
- Per-query retries.
- Wordlist input or stdin.
- Outputs (subdomain, A-records, CNAME) tuples.

This is the standalone DNS-resolver. For passive-source aggregation see
`passive_subdomains.py`. For permutations see `subdomain_permuter.py`.

Wire-level note
---------------
We send DNS queries over UDP using a stdlib-only DNS encoder (the same
one that Module 8's `dns_client.py` uses internally). No `dnspython`
dependency.

Usage
-----
  python3 -m redshift_toolkit.recon.subdomain_enum \\
      --target example.com --wordlist sub-100.txt
  python3 -m redshift_toolkit.recon.subdomain_enum \\
      --target example.com --wordlist - < my_words.txt --json
  python3 -m redshift_toolkit.recon.subdomain_enum \\
      --target example.com --concurrency 200 --resolvers 1.1.1.1,8.8.8.8

Author: Redshift Project — Module 11
License: MIT
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
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


# A short built-in wordlist for self-contained smoke tests.
BUILTIN_WORDLIST = [
    "www", "mail", "ftp", "smtp", "pop", "imap", "ns1", "ns2", "ns3",
    "vpn", "api", "dev", "stage", "staging", "uat", "prod", "test",
    "admin", "portal", "intranet", "extranet", "corp", "internal",
    "git", "gitlab", "github", "jira", "confluence", "jenkins",
    "monitor", "grafana", "prometheus", "metrics", "logs", "kibana",
    "auth", "login", "sso", "okta", "ldap", "ad",
    "files", "fileserver", "cdn", "assets", "static", "media",
    "blog", "shop", "store", "support", "help", "docs",
    "old", "new", "v2", "beta", "preprod", "qa",
    "app", "app1", "app2", "web", "web1", "web2",
    "mobile", "m", "img", "images", "static-cdn",
    "owa", "exchange", "remote", "ssh", "vnc", "rdp",
    "db", "database", "sql", "mysql", "postgres", "mongo", "redis",
    "k8s", "kube", "rancher",
    "dashboard", "console", "manage", "control", "panel",
    "secure", "private", "hidden", "internal-api",
]


# ─── DNS wire — minimal encoder/parser ──────────────────────────────────────
def encode_name(name: str) -> bytes:
    out = bytearray()
    for label in name.rstrip(".").split("."):
        b = label.encode("ascii")
        if not b:
            continue
        out.append(len(b))
        out.extend(b)
    out.append(0)
    return bytes(out)


def build_query(name: str, qtype: int = 1, txid: int | None = None) -> tuple[bytes, int]:
    txid = txid if txid is not None else int.from_bytes(os.urandom(2), "big")
    flags = 0x0100  # RD
    header = struct.pack(">HHHHHH", txid, flags, 1, 0, 0, 0)
    body = encode_name(name) + struct.pack(">HH", qtype, 1)
    return header + body, txid


def _read_name(data: bytes, off: int) -> tuple[str, int]:
    labels: list[str] = []
    saw_pointer = False
    next_off = off
    safety = 0
    while True:
        if safety > 64 or off >= len(data):
            return ".".join(labels) if labels else ".", next_off
        safety += 1
        ln = data[off]
        if ln == 0:
            off += 1
            if not saw_pointer:
                next_off = off
            return ".".join(labels) if labels else ".", next_off
        if (ln & 0xC0) == 0xC0:
            ptr = ((ln & 0x3F) << 8) | data[off + 1]
            if not saw_pointer:
                next_off = off + 2
                saw_pointer = True
            off = ptr
            continue
        off += 1
        labels.append(data[off:off + ln].decode("ascii", errors="replace"))
        off += ln


def parse_response(data: bytes) -> dict:
    out = {"a": [], "cname": [], "rcode": -1}
    if len(data) < 12:
        return out
    txid, flags, qd, an, ns, ar = struct.unpack(">HHHHHH", data[:12])
    out["rcode"] = flags & 0x0F
    off = 12
    for _ in range(qd):
        _, off = _read_name(data, off)
        off += 4
    for _ in range(an):
        _, off = _read_name(data, off)
        if off + 10 > len(data):
            return out
        rtype, _, _, rdlen = struct.unpack(">HHIH", data[off:off + 10])
        off += 10
        rdata = data[off:off + rdlen]
        off += rdlen
        if rtype == 1 and len(rdata) == 4:
            out["a"].append(".".join(str(b) for b in rdata))
        elif rtype == 5:
            cn, _ = _read_name(data, data.find(rdata) if rdata in data else off - rdlen)
            # Re-parse using the offset we know is correct: position of rdata within data.
            # Use a tighter approach:
            try:
                cn_off = data.index(rdata, 12)
                cn, _ = _read_name(data, cn_off)
            except ValueError:
                pass
            out["cname"].append(cn.rstrip("."))
    return out


# ─── Async resolver ─────────────────────────────────────────────────────────
class UdpDnsClient:
    """Async UDP DNS client. Rotates through resolvers."""
    def __init__(self, resolvers: list[str], timeout: float = 2.0,
                 retries: int = 2):
        self.resolvers = resolvers
        self.timeout = timeout
        self.retries = retries
        self._lock = asyncio.Lock()

    async def query(self, name: str, qtype: int = 1) -> dict:
        loop = asyncio.get_event_loop()
        last_exc = None
        for attempt in range(self.retries + 1):
            resolver = random.choice(self.resolvers)
            payload, txid = build_query(name, qtype)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setblocking(False)
            try:
                try:
                    await loop.sock_sendto(sock, payload, (resolver, 53))
                except (NotImplementedError, AttributeError):
                    sock.sendto(payload, (resolver, 53))
                try:
                    data = await asyncio.wait_for(
                        loop.sock_recv(sock, 4096), timeout=self.timeout)
                except (NotImplementedError, AttributeError):
                    sock.settimeout(self.timeout)
                    data, _ = sock.recvfrom(4096)
                resp = parse_response(data)
                resp["resolver"] = resolver
                return resp
            except (asyncio.TimeoutError, OSError) as e:
                last_exc = e
                continue
            finally:
                sock.close()
        return {"a": [], "cname": [], "rcode": -1, "error": str(last_exc)}


@dataclass
class Hit:
    name: str
    a: list[str] = field(default_factory=list)
    cname: list[str] = field(default_factory=list)


@dataclass
class Report:
    target: str
    started_at: float
    finished_at: float = 0.0
    wildcard_ips: list[str] = field(default_factory=list)
    candidates_tested: int = 0
    hits: list[Hit] = field(default_factory=list)


async def detect_wildcard(client: UdpDnsClient, target: str,
                          probes: int = 4) -> set[str]:
    """Query several improbable subdomains; if they all resolve to the
    same set of IPs, that set is the wildcard."""
    samples: list[set[str]] = []
    for _ in range(probes):
        rand = "rs" + os.urandom(8).hex()
        resp = await client.query(f"{rand}.{target}")
        if resp["a"]:
            samples.append(set(resp["a"]))
    if not samples:
        return set()
    if len({frozenset(s) for s in samples}) == 1:
        return samples[0]
    return set().union(*samples)


async def enum(target: str, words: list[str], concurrency: int,
               timeout: float, retries: int, resolvers: list[str],
               progress_every: int = 0) -> Report:
    rep = Report(target=target, started_at=time.time())
    client = UdpDnsClient(resolvers, timeout, retries)

    wildcard = await detect_wildcard(client, target)
    rep.wildcard_ips = sorted(wildcard)

    sem = asyncio.Semaphore(concurrency)
    counter = {"n": 0}

    async def probe(word: str) -> Hit | None:
        async with sem:
            name = f"{word}.{target}"
            resp = await client.query(name)
            counter["n"] += 1
            if (progress_every and counter["n"] % progress_every == 0
                    and sys.stderr.isatty()):
                print(f"\r[*] tested {counter['n']}/{len(words)} ...",
                      end="", file=sys.stderr, flush=True)
            if resp["rcode"] != 0:
                return None
            ips = set(resp["a"])
            # Filter wildcard collisions
            if wildcard and ips and ips.issubset(wildcard):
                return None
            if not ips and not resp["cname"]:
                return None
            return Hit(name=name, a=sorted(ips), cname=resp["cname"])

    tasks = [asyncio.create_task(probe(w)) for w in words]
    for fut in asyncio.as_completed(tasks):
        h = await fut
        if h:
            rep.hits.append(h)
    rep.candidates_tested = len(words)
    rep.finished_at = time.time()
    if progress_every and sys.stderr.isatty():
        print("", file=sys.stderr)
    rep.hits.sort(key=lambda h: h.name)
    return rep


def render_text(rep: Report, color: bool) -> str:
    out = [paint(f"\n=== Subdomain enum: {rep.target} ===", BOLD, color),
           f"  candidates tested: {rep.candidates_tested}",
           f"  resolved hits: {len(rep.hits)}"]
    if rep.wildcard_ips:
        out.append(paint(
            f"  wildcard detected → IPs filtered: {', '.join(rep.wildcard_ips[:5])}",
            YELLOW, color))
    if rep.hits:
        out.append("")
        for h in rep.hits:
            ips = ",".join(h.a) if h.a else "-"
            cn = (" CNAME→ " + " → ".join(h.cname)) if h.cname else ""
            out.append(paint(f"  {h.name}", GREEN, color)
                       + paint(f"  {ips}{cn}", GREY, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Async DNS subdomain brute-force.")
    ap.add_argument("--target", required=True)
    ap.add_argument("--wordlist", default=None,
                    help="path to wordlist file, '-' for stdin, or omit for built-in")
    ap.add_argument("--concurrency", type=int, default=100)
    ap.add_argument("--timeout", type=float, default=2.0)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--resolvers", default="1.1.1.1,8.8.8.8,9.9.9.9,8.8.4.4,1.0.0.1")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    if args.wordlist == "-":
        words = [w.strip() for w in sys.stdin if w.strip()]
    elif args.wordlist:
        with open(args.wordlist) as f:
            words = [w.strip() for w in f if w.strip() and not w.startswith("#")]
    else:
        words = list(BUILTIN_WORDLIST)

    resolvers = [r.strip() for r in args.resolvers.split(",") if r.strip()]

    print(paint(f"[*] {len(words)} candidates × {args.concurrency} concurrency",
                BOLD, color), file=sys.stderr)

    rep = asyncio.run(enum(args.target, words, args.concurrency,
                           args.timeout, args.retries, resolvers,
                           progress_every=max(1, len(words) // 50)))

    if args.json:
        out = asdict(rep)
        print(json.dumps(out, indent=2))
    else:
        print(render_text(rep, color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
