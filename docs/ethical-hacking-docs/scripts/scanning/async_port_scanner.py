#!/usr/bin/env python3
"""
async_port_scanner.py
=====================

A production-quality asynchronous TCP port scanner for AUTHORIZED security
assessments and self-audit of your own systems.

Use cases (all defensive / authorized):
  - Verify your own server's exposed services match what you intended
  - Sanity-check firewall rules after changes
  - Inventory listening ports across hosts you own / are paid to test
  - Lab learning during cybersecurity training

LEGAL NOTE
----------
Port scanning systems you do NOT own or have written permission to test
may be unlawful in your jurisdiction (e.g., CFAA in the US, IT Act in India).
Only run against:
  - Your own machines / lab VMs
  - Systems you have written authorization to test
  - Public test targets that explicitly invite scanning (e.g. scanme.nmap.org)

Usage
-----
    python async_port_scanner.py 127.0.0.1
    python async_port_scanner.py 192.168.1.10 --ports 1-1024
    python async_port_scanner.py example.com --ports 22,80,443,8000-8100
    python async_port_scanner.py 10.0.0.5 --top 1000 --concurrency 1000 --timeout 1.5

Author: Ethical Hacking Mastery curriculum
License: Educational use
"""
from __future__ import annotations

import argparse
import asyncio
import socket
import sys
import time
from dataclasses import dataclass
from typing import Iterable

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    from rich.table import Table
except ImportError:
    print("[-] rich is required: pip install rich", file=sys.stderr)
    sys.exit(1)

console = Console()

# ---- The 100 statistically most-common open TCP ports (nmap --top-ports 100) ----
TOP_100_PORTS = [
    7, 9, 13, 21, 22, 23, 25, 26, 37, 53, 79, 80, 81, 88, 106, 110, 111, 113,
    119, 135, 139, 143, 144, 179, 199, 389, 427, 443, 444, 445, 465, 513, 514,
    515, 543, 544, 548, 554, 587, 631, 646, 873, 990, 993, 995, 1025, 1026,
    1027, 1028, 1029, 1110, 1433, 1720, 1723, 1755, 1900, 2000, 2001, 2049,
    2121, 2717, 3000, 3128, 3306, 3389, 3986, 4899, 5000, 5009, 5051, 5060,
    5101, 5190, 5357, 5432, 5631, 5666, 5800, 5900, 6000, 6001, 6646, 7070,
    8000, 8008, 8009, 8080, 8081, 8443, 8888, 9100, 9999, 10000, 32768, 49152,
    49153, 49154, 49155, 49156, 49157,
]

# Common service names (best-effort; banner grab fills in real version)
COMMON_SERVICES = {
    21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns",
    80: "http", 110: "pop3", 111: "rpcbind", 135: "msrpc",
    139: "netbios-ssn", 143: "imap", 389: "ldap", 443: "https",
    445: "microsoft-ds", 465: "smtps", 587: "submission", 631: "ipp",
    636: "ldaps", 873: "rsync", 993: "imaps", 995: "pop3s",
    1433: "ms-sql-s", 1521: "oracle", 2049: "nfs", 3306: "mysql",
    3389: "ms-wbt-server", 5432: "postgresql", 5900: "vnc",
    5985: "winrm-http", 5986: "winrm-https", 6379: "redis",
    8000: "http-alt", 8080: "http-proxy", 8443: "https-alt",
    9200: "elasticsearch", 11211: "memcached", 27017: "mongodb",
}


@dataclass
class ScanResult:
    """A single port-scan result."""
    port: int
    open: bool
    banner: str | None = None
    service: str | None = None


# --------------------------------------------------------------------------- #
# Core scanner
# --------------------------------------------------------------------------- #
async def probe_port(host: str, port: int, timeout: float) -> ScanResult:
    """Probe a single TCP port with optional banner grab."""
    try:
        connect_coro = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(connect_coro, timeout=timeout)

        banner: str | None = None
        try:
            data = await asyncio.wait_for(reader.read(128), timeout=0.6)
            banner = data.decode(errors="ignore").strip().splitlines()[0] if data else None
        except (asyncio.TimeoutError, UnicodeDecodeError):
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

        return ScanResult(port=port, open=True, banner=banner,
                          service=COMMON_SERVICES.get(port))
    except (asyncio.TimeoutError, OSError, ConnectionRefusedError):
        return ScanResult(port=port, open=False)


async def scan_host(host: str, ports: list[int], concurrency: int,
                    timeout: float) -> list[ScanResult]:
    """Scan all ports on a host with a bounded concurrency semaphore."""
    sem = asyncio.Semaphore(concurrency)

    async def bound_probe(p: int) -> ScanResult:
        async with sem:
            return await probe_port(host, p, timeout)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(f"Scanning {host}", total=len(ports))
        results: list[ScanResult] = []

        async def runner(p: int):
            r = await bound_probe(p)
            progress.advance(task)
            return r

        for coro in asyncio.as_completed([runner(p) for p in ports]):
            results.append(await coro)

    return sorted(results, key=lambda r: r.port)


# --------------------------------------------------------------------------- #
# CLI helpers
# --------------------------------------------------------------------------- #
def parse_port_spec(spec: str) -> list[int]:
    """Parse a port spec like '22,80,443,8000-8100' into a sorted unique list."""
    out: set[int] = set()
    for piece in spec.split(","):
        piece = piece.strip()
        if not piece:
            continue
        if "-" in piece:
            a, b = piece.split("-", 1)
            lo, hi = int(a), int(b)
            if lo < 1 or hi > 65535 or lo > hi:
                raise ValueError(f"invalid port range: {piece}")
            out.update(range(lo, hi + 1))
        else:
            p = int(piece)
            if not 1 <= p <= 65535:
                raise ValueError(f"invalid port: {p}")
            out.add(p)
    return sorted(out)


def resolve(host: str) -> str:
    """Resolve a hostname to IP for display; fail clearly if it doesn't resolve."""
    try:
        return socket.gethostbyname(host)
    except socket.gaierror as e:
        raise SystemExit(f"[-] Could not resolve '{host}': {e}")


def render_results(host: str, ip: str, results: list[ScanResult],
                   elapsed: float, total_scanned: int) -> None:
    open_results = [r for r in results if r.open]

    table = Table(
        title=f"Open ports on {host} ({ip})",
        show_lines=False,
        header_style="bold cyan",
    )
    table.add_column("Port", justify="right", style="bold")
    table.add_column("Service", style="green")
    table.add_column("Banner", style="dim", overflow="fold")

    for r in open_results:
        table.add_row(
            f"{r.port}/tcp",
            r.service or "-",
            (r.banner or "")[:120],
        )

    if open_results:
        console.print(table)
    else:
        console.print(f"[yellow]No open ports found on {host} in scanned range.[/yellow]")

    console.print(
        f"[dim]Scanned {total_scanned} ports in {elapsed:.2f}s · "
        f"{len(open_results)} open · "
        f"{total_scanned - len(open_results)} closed/filtered[/dim]"
    )


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Async TCP port scanner for AUTHORIZED security testing. "
            "Use only on systems you own or have permission to assess."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s 127.0.0.1\n"
            "  %(prog)s 192.168.1.10 --ports 1-1024\n"
            "  %(prog)s example.com --ports 22,80,443\n"
            "  %(prog)s 10.0.0.5 --top 100 --concurrency 1000\n"
        ),
    )
    parser.add_argument("host", help="Target host (IP or hostname)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--ports", default=None,
                       help="Port spec: '22,80,443' or '1-1024' or '22,80,8000-8100'")
    group.add_argument("--top", type=int, default=None,
                       help="Scan the top N most common ports (max 100 here)")
    parser.add_argument("--timeout", type=float, default=1.0,
                        help="Per-port connect timeout in seconds (default: 1.0)")
    parser.add_argument("--concurrency", type=int, default=500,
                        help="Maximum concurrent probes (default: 500)")
    args = parser.parse_args()

    # Authorization reminder
    console.print(
        "[bold yellow]⚠  Run only against systems you own or are authorized to test.[/bold yellow]\n"
    )

    # Resolve target
    ip = resolve(args.host)

    # Determine ports
    if args.top is not None:
        if args.top < 1:
            raise SystemExit("--top must be >= 1")
        ports = TOP_100_PORTS[: min(args.top, len(TOP_100_PORTS))]
    elif args.ports is not None:
        try:
            ports = parse_port_spec(args.ports)
        except ValueError as e:
            raise SystemExit(f"[-] {e}")
    else:
        ports = list(range(1, 1025))   # default: well-known ports

    if args.concurrency < 1:
        raise SystemExit("--concurrency must be >= 1")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be > 0")

    console.print(
        f"[cyan]Scanning {args.host} ({ip}) · "
        f"{len(ports)} ports · concurrency={args.concurrency} · "
        f"timeout={args.timeout}s[/cyan]"
    )

    t0 = time.perf_counter()
    try:
        results = asyncio.run(
            scan_host(ip, ports, args.concurrency, args.timeout)
        )
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted.[/red]")
        sys.exit(130)
    elapsed = time.perf_counter() - t0

    render_results(args.host, ip, results, elapsed, len(ports))


if __name__ == "__main__":
    main()
