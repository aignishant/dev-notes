#!/usr/bin/env python3
"""
redshift_toolkit.recon.vhost_fuzzer — Host-header fuzzing for hidden
virtual hosts on a target IP.

How it works
------------
1. Establish a baseline by querying the IP with a nonsense Host: header.
   Record (status, content-length, body-hash).
2. For every candidate name from a wordlist, send the same request with
   `Host: <candidate>` and compare. Anything different is a candidate
   for a hidden vhost.
3. Group results by their (status, length, body-hash) fingerprint. The
   baseline group is filtered out; everything else is reported.

Works equally well for HTTP (port 80) and HTTPS (443).

Usage
-----
  ./vhost_fuzzer.py --target 10.0.0.10 --port 80 \\
      --wordlist subs.txt --apex example.com
  ./vhost_fuzzer.py --target 10.0.0.10 --port 443 --tls \\
      --apex example.com --wordlist - < candidates.txt
  ./vhost_fuzzer.py --target https://10.0.0.10 --apex example.com \\
      --candidates intranet,admin,internal --json

Author: Redshift Project — Module 11
License: MIT
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import ssl
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, asdict, field
from urllib.parse import urlparse

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


@dataclass
class Probe:
    candidate: str
    status: int = 0
    length: int = 0
    body_sha1: str = ""
    server: str | None = None
    title: str | None = None
    error: str | None = None


@dataclass
class Report:
    target_ip: str
    port: int
    tls: bool
    candidates_tested: int
    baseline: Probe | None = None
    distinct_groups: list[dict] = field(default_factory=list)
    interesting: list[Probe] = field(default_factory=list)


async def fetch(ip: str, port: int, tls: bool, host_header: str,
                path: str, timeout: float) -> Probe:
    p = Probe(candidate=host_header)
    try:
        if tls:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            try:
                ctx.set_ciphers("ALL:@SECLEVEL=0")
            except ssl.SSLError:
                pass
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port, ssl=ctx,
                                        server_hostname=host_header),
                timeout=timeout)
        else:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port), timeout=timeout)
    except Exception as e:
        p.error = str(e)
        return p

    try:
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host_header}\r\n"
            f"User-Agent: redshift-vhost-fuzzer/1.0\r\n"
            f"Accept: */*\r\n"
            f"Connection: close\r\n\r\n"
        ).encode()
        writer.write(req)
        await writer.drain()
        try:
            data = await asyncio.wait_for(reader.read(64 * 1024),
                                          timeout=timeout)
        except asyncio.TimeoutError:
            data = b""
    except OSError as e:
        p.error = str(e)
        return p
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    if not data:
        p.error = "empty response"
        return p
    head, _, body = data.partition(b"\r\n\r\n")
    try:
        first_line = head.split(b"\r\n", 1)[0].decode("latin-1", "replace")
        parts = first_line.split(" ", 2)
        if len(parts) >= 2 and parts[1].isdigit():
            p.status = int(parts[1])
    except Exception:
        pass
    p.length = len(body)
    p.body_sha1 = hashlib.sha1(body).hexdigest()
    for line in head.split(b"\r\n"):
        low = line.lower()
        if low.startswith(b"server:"):
            p.server = line.decode("latin-1", "replace")[7:].strip()
            break
    # crude title match
    lower_body = body[:8000].lower()
    if b"<title" in lower_body:
        try:
            i = lower_body.index(b"<title")
            j = lower_body.index(b"</title>", i)
            inner = body[i:j]
            inner = inner.split(b">", 1)[1] if b">" in inner else inner
            p.title = inner.decode("utf-8", "replace").strip()[:80]
        except ValueError:
            pass
    return p


async def run(target: str, port: int, tls: bool, candidates: list[str],
              concurrency: int, timeout: float, path: str) -> Report:
    rep = Report(target_ip=target, port=port, tls=tls,
                 candidates_tested=len(candidates))

    # Baseline using a deliberately invalid Host header
    bogus = "bogus" + os.urandom(4).hex() + ".invalid"
    rep.baseline = await fetch(target, port, tls, bogus, path, timeout)

    sem = asyncio.Semaphore(concurrency)

    async def one(cand: str) -> Probe:
        async with sem:
            return await fetch(target, port, tls, cand, path, timeout)

    probes = await asyncio.gather(*[one(c) for c in candidates])

    groups: dict[tuple, list[Probe]] = defaultdict(list)
    for pr in probes:
        if pr.error:
            continue
        key = (pr.status, pr.length, pr.body_sha1)
        groups[key].append(pr)

    base_key = ((rep.baseline.status, rep.baseline.length, rep.baseline.body_sha1)
                if rep.baseline and not rep.baseline.error else None)

    for key, members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        if key == base_key:
            continue
        rep.distinct_groups.append({
            "fingerprint": {"status": key[0], "length": key[1],
                            "body_sha1": key[2][:16]},
            "candidate_count": len(members),
            "samples": [asdict(p) for p in members[:5]],
        })
        rep.interesting.extend(members)

    return rep


def render_text(rep: Report, color: bool) -> str:
    out = [paint(f"\n=== vhost fuzz: {rep.target_ip}:{rep.port}"
                 f" ({'TLS' if rep.tls else 'plain'}) ===", BOLD, color),
           f"  candidates tested: {rep.candidates_tested}"]
    if rep.baseline:
        bl = rep.baseline
        out.append(paint(
            f"  baseline: status={bl.status} length={bl.length} "
            f"sha1={bl.body_sha1[:16] if bl.body_sha1 else '?'}", GREY, color))
    out.append(paint(f"  distinct non-baseline groups: {len(rep.distinct_groups)}",
                     BOLD, color))
    for grp in rep.distinct_groups[:20]:
        fp = grp["fingerprint"]
        out.append(paint(
            f"\n  ── group  status={fp['status']}  length={fp['length']}  "
            f"sha1={fp['body_sha1']}  ({grp['candidate_count']} candidate(s))",
            GREEN, color))
        for s in grp["samples"]:
            extra = ""
            if s.get("server"):
                extra += f"  server={s['server']}"
            if s.get("title"):
                extra += f"  title={s['title']!r}"
            out.append(f"    + {s['candidate']}{extra}")
    return "\n".join(out)


def parse_target(s: str) -> tuple[str, int, bool]:
    if s.startswith("http://") or s.startswith("https://"):
        u = urlparse(s)
        tls = (u.scheme == "https")
        port = u.port or (443 if tls else 80)
        return u.hostname, port, tls
    return s, 0, False  # caller fills port/tls


def main() -> int:
    ap = argparse.ArgumentParser(description="Host-header virtual host fuzzer.")
    ap.add_argument("--target", required=True,
                    help="IP or http(s)://IP[:port]")
    ap.add_argument("--port", type=int, default=80)
    ap.add_argument("--tls", action="store_true")
    ap.add_argument("--apex", default="example.com",
                    help="domain suffix to append to candidates")
    ap.add_argument("--candidates",
                    help="comma-separated host names (full or prefixes)")
    ap.add_argument("--wordlist",
                    help="file with one candidate per line ('-' for stdin)")
    ap.add_argument("--path", default="/")
    ap.add_argument("--concurrency", type=int, default=30)
    ap.add_argument("--timeout", type=float, default=4.0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    host, parsed_port, parsed_tls = parse_target(args.target)
    port = parsed_port or args.port
    tls = parsed_tls or args.tls

    raw: list[str] = []
    if args.candidates:
        raw.extend(c.strip() for c in args.candidates.split(",") if c.strip())
    if args.wordlist == "-":
        raw.extend(w.strip() for w in sys.stdin if w.strip())
    elif args.wordlist:
        with open(args.wordlist) as f:
            raw.extend(w.strip() for w in f
                       if w.strip() and not w.startswith("#"))
    if not raw:
        print("must provide --candidates or --wordlist", file=sys.stderr)
        return 2

    apex = args.apex.strip(".")

    def expand(c: str) -> str:
        if "." in c:
            return c
        return f"{c}.{apex}"

    candidates = [expand(c) for c in raw]

    print(paint(
        f"[*] vhost-fuzz {host}:{port} ({'TLS' if tls else 'plain'})  "
        f"candidates={len(candidates)}", BOLD, color), file=sys.stderr)
    rep = asyncio.run(run(host, port, tls, candidates,
                          args.concurrency, args.timeout, args.path))
    if args.json:
        print(json.dumps(asdict(rep), indent=2))
    else:
        print(render_text(rep, color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
