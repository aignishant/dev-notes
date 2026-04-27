#!/usr/bin/env python3
"""
ct_subdomain_enum.py
====================

Passively enumerate subdomains of a given apex domain by querying public
Certificate Transparency (CT) logs. CT is a public, append-only log of every
TLS certificate ever issued by participating CAs — it's open data anyone can
query.

This is 100% passive: no traffic is sent to the target; we only query the
public crt.sh database. Useful for:
  * Asset discovery on domains you own
  * Authorized recon during pentests
  * Bug bounty (within program scope)
  * Defensive: knowing what subdomains exist helps you protect them

Usage
-----
    python ct_subdomain_enum.py example.com
    python ct_subdomain_enum.py example.com --resolve
    python ct_subdomain_enum.py example.com --resolve --json out.json

Output
------
A unique sorted list of subdomains that have ever been issued a certificate.
With --resolve, each subdomain is also DNS-resolved (still passive — DNS
queries go to your resolver, not the target).

Author: Ethical Hacking Mastery curriculum
License: Educational use
"""
from __future__ import annotations

import argparse
import asyncio
import json
import socket
import sys
from typing import Any

try:
    import httpx
except ImportError:
    print("[-] httpx is required: pip install httpx", file=sys.stderr)
    sys.exit(1)

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich.table import Table
except ImportError:
    print("[-] rich is required: pip install rich", file=sys.stderr)
    sys.exit(1)

console = Console()

CRT_SH_URL = "https://crt.sh/?q=%25.{domain}&output=json"


# --------------------------------------------------------------------------- #
# CT lookup
# --------------------------------------------------------------------------- #
async def fetch_crt_sh(domain: str, timeout: float = 60.0) -> list[dict[str, Any]]:
    url = CRT_SH_URL.format(domain=domain)
    async with httpx.AsyncClient(http2=True, timeout=timeout,
                                 headers={"User-Agent": "ct-subdomain-enum/1.0"}) as c:
        r = await c.get(url)
        r.raise_for_status()
        try:
            return r.json()
        except Exception as e:
            raise SystemExit(f"[-] crt.sh did not return JSON: {e}")


def extract_names(records: list[dict[str, Any]], apex: str) -> set[str]:
    names: set[str] = set()
    apex = apex.lower().strip(".")
    for rec in records:
        for field in ("name_value", "common_name"):
            value = rec.get(field) or ""
            for line in value.split("\n"):
                line = line.strip().lower().strip(".")
                if not line:
                    continue
                # Skip wildcards but keep the apex form for the user to see
                line = line.lstrip("*.")
                if line == apex or line.endswith("." + apex):
                    names.add(line)
    return names


# --------------------------------------------------------------------------- #
# DNS resolution
# --------------------------------------------------------------------------- #
async def resolve_one(name: str, sem: asyncio.Semaphore) -> tuple[str, list[str]]:
    async with sem:
        loop = asyncio.get_running_loop()
        try:
            infos = await loop.getaddrinfo(name, None, type=socket.SOCK_STREAM)
            ips = sorted({i[4][0] for i in infos})
            return name, ips
        except (socket.gaierror, OSError):
            return name, []


async def resolve_all(names: list[str], concurrency: int = 50
                      ) -> dict[str, list[str]]:
    sem = asyncio.Semaphore(concurrency)
    out: dict[str, list[str]] = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Resolving DNS", total=len(names))

        async def runner(n: str):
            n2, ips = await resolve_one(n, sem)
            out[n2] = ips
            progress.advance(task)

        await asyncio.gather(*(runner(n) for n in names))
    return out


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def render(domain: str, names: list[str], resolution: dict[str, list[str]] | None) -> None:
    console.print(f"\n[bold green]Found {len(names)} unique names for {domain}[/bold green]\n")

    if resolution is None:
        for n in names:
            console.print(n)
        return

    table = Table(header_style="bold cyan", show_lines=False)
    table.add_column("Subdomain", style="cyan")
    table.add_column("Resolved IPs", overflow="fold")
    live = 0
    for n in names:
        ips = resolution.get(n, [])
        if ips:
            live += 1
        table.add_row(n, ", ".join(ips) if ips else "[red]NXDOMAIN[/red]")
    console.print(table)
    console.print(f"\n[dim]Resolvable: {live}/{len(names)}[/dim]")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
async def amain(args: argparse.Namespace) -> None:
    domain = args.domain.lower().strip(".")
    console.print(f"[cyan]Querying crt.sh for *.{domain}…[/cyan]")
    try:
        records = await fetch_crt_sh(domain, timeout=args.timeout)
    except httpx.HTTPError as e:
        raise SystemExit(f"[-] HTTP error: {e}")

    names = sorted(extract_names(records, domain))
    if not names:
        console.print("[yellow]No certificate records found in CT for this domain.[/yellow]")
        return

    resolution: dict[str, list[str]] | None = None
    if args.resolve:
        resolution = await resolve_all(names, concurrency=args.concurrency)

    render(domain, names, resolution)

    if args.json:
        out = {"domain": domain, "subdomains": names}
        if resolution is not None:
            out["resolution"] = resolution
        try:
            with open(args.json, "w") as f:
                json.dump(out, f, indent=2)
            console.print(f"[green]Wrote {args.json}[/green]")
        except OSError as e:
            console.print(f"[red]Failed to write JSON: {e}[/red]")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Passive subdomain enumeration via Certificate Transparency logs.",
    )
    parser.add_argument("domain", help="Apex domain (e.g., example.com)")
    parser.add_argument("--resolve", action="store_true",
                        help="Also resolve each subdomain to IPs")
    parser.add_argument("--concurrency", type=int, default=50,
                        help="DNS resolver concurrency (default 50)")
    parser.add_argument("--timeout", type=float, default=60.0,
                        help="HTTP timeout in seconds (default 60)")
    parser.add_argument("--json", default=None,
                        help="Write JSON output to this path")
    args = parser.parse_args()

    try:
        asyncio.run(amain(args))
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted.[/red]")
        sys.exit(130)


if __name__ == "__main__":
    main()
