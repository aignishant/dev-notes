#!/usr/bin/env python3
"""
vhost_finder.py — Virtual host discovery via Host-header brute-force.

Finds web applications served via different `Host:` headers on the same IP.
Uses response-size + content-hash diffing against a baseline to filter
generic 404 / catch-all responses, surfacing only Hosts that produce
meaningfully different responses.

⚠️ AUTHORIZATION REQUIRED ⚠️
Vhost discovery sends real HTTP requests to the target. Run only against
systems you own or are explicitly authorized to test. ROE applies.

Usage:
    python3 vhost_finder.py http://10.0.0.5 -d target.com -w subs.txt
    python3 vhost_finder.py https://target.com -d target.com -w subs.txt --json
    python3 vhost_finder.py http://10.0.0.5 --hostnames host1,host2,host3
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from dataclasses import dataclass, asdict
from typing import Iterable

import httpx

USER_AGENT = "vhost-finder/1.0 (defensive testing only)"
TIMEOUT = httpx.Timeout(15.0, connect=10.0)


@dataclass
class HostResult:
    host: str
    status: int
    length: int
    body_hash: str
    title: str | None
    interesting: bool


def _extract_title(text: str, limit: int = 200) -> str | None:
    if "<title" not in text.lower():
        return None
    try:
        start = text.lower().index("<title")
        start = text.index(">", start) + 1
        end = text.lower().index("</title>", start)
        return text[start:end].strip()[:limit] or None
    except ValueError:
        return None


def _hash_body(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


async def probe_host(client: httpx.AsyncClient, base: str, host: str, sem: asyncio.Semaphore) -> HostResult | None:
    async with sem:
        try:
            r = await client.get(base, headers={"Host": host, "User-Agent": USER_AGENT})
        except (httpx.HTTPError, OSError):
            return None
        body = r.text
        return HostResult(
            host=host,
            status=r.status_code,
            length=len(body),
            body_hash=_hash_body(body),
            title=_extract_title(body),
            interesting=False,
        )


async def baseline_probe(client: httpx.AsyncClient, base: str) -> tuple[HostResult, HostResult]:
    """Get two baselines: one with no special Host header (just default), one with random nonexistent."""
    sem = asyncio.Semaphore(1)
    default = await probe_host(client, base, "this-vhost-does-not-exist-12345.invalid", sem)
    nonexistent = await probe_host(client, base, "another-fake-vhost-67890.invalid", sem)
    if not default or not nonexistent:
        raise RuntimeError("Could not establish baseline — target unreachable.")
    return default, nonexistent


def is_interesting(r: HostResult, baselines: list[HostResult], len_tolerance: int = 32) -> bool:
    """A host is interesting if it differs meaningfully from every baseline."""
    for b in baselines:
        if r.status == b.status and abs(r.length - b.length) < len_tolerance and r.body_hash == b.body_hash:
            return False
    return True


async def run(base: str, hosts: Iterable[str], concurrency: int, verify_tls: bool, quiet: bool) -> list[HostResult]:
    async with httpx.AsyncClient(
        timeout=TIMEOUT, http2=False, follow_redirects=False, verify=verify_tls
    ) as client:
        if not quiet:
            print(f"[*] Establishing baseline against {base}...", file=sys.stderr)
        b1, b2 = await baseline_probe(client, base)
        if not quiet:
            print(
                f"[+] Baseline: status={b1.status} length={b1.length} hash={b1.body_hash}",
                file=sys.stderr,
            )

        sem = asyncio.Semaphore(concurrency)
        coros = [probe_host(client, base, h, sem) for h in hosts]
        results: list[HostResult] = []
        baselines = [b1, b2]
        for fut in asyncio.as_completed(coros):
            r = await fut
            if r is None:
                continue
            if is_interesting(r, baselines):
                r.interesting = True
                results.append(r)
                if not quiet:
                    title = f' "{r.title}"' if r.title else ""
                    print(
                        f"[+] {r.host:50s} status={r.status} len={r.length:>7d}{title}",
                        file=sys.stderr,
                    )
        return results


def load_hosts(args: argparse.Namespace) -> list[str]:
    hosts: list[str] = []
    if args.wordlist:
        with open(args.wordlist, encoding="utf-8") as f:
            words = [w.strip() for w in f if w.strip() and not w.startswith("#")]
        if args.domain:
            hosts.extend(f"{w}.{args.domain}" for w in words)
        else:
            hosts.extend(words)
    if args.hostnames:
        hosts.extend(h.strip() for h in args.hostnames.split(",") if h.strip())
    return sorted(set(hosts))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("url", help="Base URL to test (e.g. http://10.0.0.5 or https://target.com)")
    p.add_argument("-d", "--domain", help="Append this domain to wordlist entries (e.g. target.com)")
    p.add_argument("-w", "--wordlist", help="Wordlist of subdomain prefixes (or full hosts if no -d)")
    p.add_argument("--hostnames", help="Comma-separated full hostnames to test (in addition to wordlist)")
    p.add_argument("-c", "--concurrency", type=int, default=20, help="Concurrent requests (default: 20)")
    p.add_argument("-k", "--insecure", action="store_true", help="Skip TLS verification")
    p.add_argument("--json", action="store_true", help="Emit JSON results to stdout")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress progress messages")
    args = p.parse_args()

    if not args.wordlist and not args.hostnames:
        p.error("Either --wordlist or --hostnames is required.")

    hosts = load_hosts(args)
    if not hosts:
        print("[-] No hostnames to test.", file=sys.stderr)
        return 2

    if not args.quiet:
        print(f"[*] Testing {len(hosts)} candidate vhosts against {args.url}", file=sys.stderr)

    try:
        results = asyncio.run(run(args.url, hosts, args.concurrency, not args.insecure, args.quiet))
    except KeyboardInterrupt:
        print("\n[!] Interrupted.", file=sys.stderr)
        return 130
    except RuntimeError as e:
        print(f"[-] {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"base": args.url, "interesting": [asdict(r) for r in results]}, indent=2))
    elif not args.quiet:
        print(f"\n[+] Found {len(results)} interesting vhosts.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
