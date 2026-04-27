#!/usr/bin/env python3
"""
subdomain_enum.py — Multi-source passive subdomain enumerator.

Aggregates subdomains from multiple public passive sources:
  - Certificate Transparency logs (crt.sh)
  - HackerTarget DNS API
  - AlienVault OTX
  - URLScan.io
  - (optional) ProjectDiscovery's chaos DB if CHAOS_API_KEY is set

Deduplicates, optionally resolves with the system DNS resolver, and writes
JSON output. Purely passive — no traffic to the target.

⚠️ AUTHORIZATION REQUIRED ⚠️
Only use against domains you own or are explicitly authorized to enumerate
(e.g. bug-bounty programs in scope). Consult ROE before running.

Usage:
    python3 subdomain_enum.py example.com
    python3 subdomain_enum.py example.com --resolve --output subs.json
    python3 subdomain_enum.py example.com --sources crt,otx --quiet
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import socket
import sys
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Iterable

import httpx

USER_AGENT = "subdomain-enum-script/1.0 (educational/defensive use only)"
TIMEOUT = httpx.Timeout(20.0, connect=10.0)
SUBDOMAIN_RE = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$", re.I)


@dataclass
class EnumResult:
    domain: str
    sources: dict[str, list[str]] = field(default_factory=dict)
    all_subs: set[str] = field(default_factory=set)
    resolved: dict[str, list[str]] = field(default_factory=dict)


def _is_valid_subdomain(s: str, root: str) -> bool:
    s = s.strip().lower().lstrip("*.").rstrip(".")
    if not s or s == root:
        return False
    if not s.endswith("." + root):
        return False
    return bool(SUBDOMAIN_RE.match(s))


async def fetch_crtsh(client: httpx.AsyncClient, domain: str) -> list[str]:
    """Certificate Transparency via crt.sh JSON API."""
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    r = await client.get(url, headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    out: set[str] = set()
    for entry in r.json():
        for name in (entry.get("name_value") or "").splitlines():
            if _is_valid_subdomain(name, domain):
                out.add(name.lower().lstrip("*."))
    return sorted(out)


async def fetch_hackertarget(client: httpx.AsyncClient, domain: str) -> list[str]:
    url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
    r = await client.get(url, headers={"User-Agent": USER_AGENT})
    if r.status_code != 200 or "API count exceeded" in r.text:
        return []
    out: set[str] = set()
    for line in r.text.splitlines():
        host = line.split(",", 1)[0].strip().lower()
        if _is_valid_subdomain(host, domain):
            out.add(host)
    return sorted(out)


async def fetch_otx(client: httpx.AsyncClient, domain: str) -> list[str]:
    url = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns"
    r = await client.get(url, headers={"User-Agent": USER_AGENT})
    if r.status_code != 200:
        return []
    out: set[str] = set()
    for record in (r.json() or {}).get("passive_dns", []):
        host = (record.get("hostname") or "").strip().lower()
        if _is_valid_subdomain(host, domain):
            out.add(host)
    return sorted(out)


async def fetch_urlscan(client: httpx.AsyncClient, domain: str) -> list[str]:
    url = "https://urlscan.io/api/v1/search/"
    r = await client.get(url, params={"q": f"domain:{domain}"}, headers={"User-Agent": USER_AGENT})
    if r.status_code != 200:
        return []
    out: set[str] = set()
    for hit in (r.json() or {}).get("results", []):
        page_domain = (hit.get("page", {}).get("domain") or "").strip().lower()
        if _is_valid_subdomain(page_domain, domain):
            out.add(page_domain)
    return sorted(out)


async def fetch_chaos(client: httpx.AsyncClient, domain: str) -> list[str]:
    """ProjectDiscovery chaos — needs CHAOS_API_KEY env var."""
    api_key = os.getenv("CHAOS_API_KEY")
    if not api_key:
        return []
    url = f"https://dns.projectdiscovery.io/dns/{domain}/subdomains"
    r = await client.get(url, headers={"User-Agent": USER_AGENT, "Authorization": api_key})
    if r.status_code != 200:
        return []
    body = r.json() or {}
    out: set[str] = set()
    for sub in body.get("subdomains") or []:
        host = f"{sub}.{domain}".lower()
        if _is_valid_subdomain(host, domain):
            out.add(host)
    return sorted(out)


SOURCES: dict[str, Callable[[httpx.AsyncClient, str], Awaitable[list[str]]]] = {
    "crt": fetch_crtsh,
    "hackertarget": fetch_hackertarget,
    "otx": fetch_otx,
    "urlscan": fetch_urlscan,
    "chaos": fetch_chaos,
}


async def resolve_host(host: str, sem: asyncio.Semaphore) -> tuple[str, list[str]]:
    async with sem:
        loop = asyncio.get_running_loop()
        try:
            infos = await loop.run_in_executor(None, socket.getaddrinfo, host, None)
            ips = sorted({i[4][0] for i in infos})
            return host, ips
        except (socket.gaierror, OSError):
            return host, []


async def enumerate(domain: str, source_names: Iterable[str], resolve: bool, quiet: bool) -> EnumResult:
    result = EnumResult(domain=domain)
    async with httpx.AsyncClient(timeout=TIMEOUT, http2=True, follow_redirects=True) as client:
        tasks = {name: SOURCES[name](client, domain) for name in source_names if name in SOURCES}
        for name, coro in tasks.items():
            try:
                subs = await coro
            except Exception as exc:
                if not quiet:
                    print(f"[!] {name}: error: {exc}", file=sys.stderr)
                subs = []
            result.sources[name] = subs
            result.all_subs.update(subs)
            if not quiet:
                print(f"[+] {name}: {len(subs)} subdomains", file=sys.stderr)

    if resolve and result.all_subs:
        if not quiet:
            print(f"[*] Resolving {len(result.all_subs)} subdomains...", file=sys.stderr)
        sem = asyncio.Semaphore(50)
        coros = [resolve_host(h, sem) for h in sorted(result.all_subs)]
        for fut in asyncio.as_completed(coros):
            host, ips = await fut
            if ips:
                result.resolved[host] = ips
        if not quiet:
            print(f"[+] {len(result.resolved)} alive (resolved)", file=sys.stderr)

    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("domain", help="Root domain to enumerate (e.g. example.com)")
    p.add_argument(
        "--sources",
        default=",".join(SOURCES.keys()),
        help=f"Comma-separated sources (default: all). Available: {','.join(SOURCES)}",
    )
    p.add_argument("--resolve", action="store_true", help="Resolve subdomains via DNS")
    p.add_argument("--output", "-o", help="Write JSON to file (default: stdout)")
    p.add_argument("--quiet", "-q", action="store_true", help="Suppress progress messages")
    args = p.parse_args()

    domain = args.domain.lower().lstrip(".")
    if not SUBDOMAIN_RE.match(domain) and not re.match(r"^[a-z0-9-]+\.[a-z]{2,}$", domain):
        print(f"[-] {args.domain!r} doesn't look like a domain.", file=sys.stderr)
        return 2

    source_names = [s.strip() for s in args.sources.split(",") if s.strip()]
    unknown = [s for s in source_names if s not in SOURCES]
    if unknown:
        print(f"[-] Unknown sources: {unknown}. Available: {list(SOURCES)}", file=sys.stderr)
        return 2

    try:
        result = asyncio.run(enumerate(domain, source_names, args.resolve, args.quiet))
    except KeyboardInterrupt:
        print("\n[!] Interrupted.", file=sys.stderr)
        return 130

    payload = {
        "domain": result.domain,
        "total_unique": len(result.all_subs),
        "sources": result.sources,
        "all_subdomains": sorted(result.all_subs),
        "resolved": dict(sorted(result.resolved.items())) if args.resolve else None,
    }

    out = json.dumps(payload, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        if not args.quiet:
            print(f"[+] Wrote {args.output}", file=sys.stderr)
    else:
        print(out)

    return 0


if __name__ == "__main__":
    sys.exit(main())
