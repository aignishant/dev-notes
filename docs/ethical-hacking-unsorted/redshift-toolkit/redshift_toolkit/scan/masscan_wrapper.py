#!/usr/bin/env python3
"""
redshift_toolkit.scan.masscan_wrapper — drive masscan with sensible
defaults and parse its JSON output into the toolkit's canonical schema.

What it does
------------
- Builds a `masscan` command with safe defaults (rate limit, retries,
  excluded ranges, output format).
- Runs masscan, captures stdout JSON.
- Parses into a list of {host, port, proto, ts} dicts.
- Optionally writes a `services-stub.json` that `svc_enum.py` can pick
  up directly.

If masscan isn't installed, falls back to internally-asyncio TCP-connect
sweep over the requested ports (slower but works without root).

Usage
-----
  sudo ./masscan_wrapper.py -t 10.0.0.0/24 -p 1-65535 --rate 50000
  ./masscan_wrapper.py -t 10.0.0.0/24 -p 80,443,8080 --no-masscan
  sudo ./masscan_wrapper.py -t 10.0.0.0/24 -p top1000 \\
        --output scan.json --emit-services-stub services-stub.json

Author: Redshift Project — Module 10
License: MIT — Authorized testing only.
"""

from __future__ import annotations

import argparse
import asyncio
import ipaddress
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


TOP_1000_HINT = list(range(1, 1024)) + [
    1080, 1234, 1352, 1433, 1521, 1604, 1723, 1812, 2049, 2222, 2375,
    2376, 3000, 3128, 3268, 3306, 3389, 3690, 4040, 4444, 4848, 5000,
    5432, 5601, 5672, 5900, 5984, 6379, 6443, 6660, 6667, 6697, 7001,
    7777, 8000, 8005, 8006, 8008, 8009, 8080, 8081, 8443, 8888, 9000,
    9090, 9100, 9200, 9300, 9418, 9999, 10000, 11211, 27017, 28017,
    32768, 50000, 50030, 50070,
]


@dataclass
class OpenPort:
    host: str
    port: int
    proto: str = "tcp"
    timestamp: float = 0.0


@dataclass
class Report:
    target: str
    started_at: float
    finished_at: float = 0.0
    backend: str = ""
    open_ports: list[OpenPort] = field(default_factory=list)


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


def parse_ports(spec: str) -> list[int]:
    spec = spec.strip().lower()
    if spec == "top1000":
        return sorted(set(TOP_1000_HINT))
    out: set[int] = set()
    for token in spec.split(","):
        token = token.strip()
        if "-" in token:
            a, b = token.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(token))
    return sorted(p for p in out if 1 <= p <= 65535)


# ─── Backend: masscan ───────────────────────────────────────────────────────
def run_masscan(target_spec: str, port_spec: str, rate: int,
                exclude_path: str | None) -> list[OpenPort]:
    if not shutil.which("masscan"):
        raise RuntimeError("masscan binary not on PATH")
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tf:
        out_path = tf.name
    cmd = ["masscan", target_spec, "-p", port_spec, "--rate", str(rate),
           "-oJ", out_path, "--wait", "1"]
    if exclude_path:
        cmd += ["--excludefile", exclude_path]
    subprocess.run(cmd, check=True)
    open_ports: list[OpenPort] = []
    with open(out_path) as f:
        text = f.read().strip()
    os.unlink(out_path)
    # masscan -oJ output: array of records, but newline-delimited
    text = text.lstrip("[\n").rstrip("\n]\n").rstrip(",")
    for line in text.splitlines():
        line = line.strip().rstrip(",")
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        host = rec.get("ip")
        for portinfo in rec.get("ports", []) or []:
            open_ports.append(OpenPort(
                host=host, port=int(portinfo.get("port", 0)),
                proto=portinfo.get("proto", "tcp"),
                timestamp=float(rec.get("timestamp", 0) or 0),
            ))
    return open_ports


# ─── Backend: pure Python (asyncio connect) ────────────────────────────────
async def _scan_one(host: str, port: int, timeout: float) -> OpenPort | None:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout)
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        return OpenPort(host=host, port=port, proto="tcp",
                        timestamp=time.time())
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return None


async def _python_backend(targets: list[str], ports: list[int],
                          concurrency: int, timeout: float) -> list[OpenPort]:
    sem = asyncio.Semaphore(concurrency)

    async def guarded(h: str, p: int):
        async with sem:
            return await _scan_one(h, p, timeout)

    tasks = [asyncio.create_task(guarded(h, p)) for h in targets for p in ports]
    out: list[OpenPort] = []
    for fut in asyncio.as_completed(tasks):
        result = await fut
        if result:
            out.append(result)
    return out


# ─── Driver ─────────────────────────────────────────────────────────────────
def emit_services_stub(open_ports: list[OpenPort]) -> dict:
    """Format that svc_enum.py and asset_graph.py will accept directly."""
    services: dict[str, dict] = {}
    for op in open_ports:
        key = f"{op.host}:{op.port}"
        services[key] = {
            "ip": op.host,
            "port": op.port,
            "proto": op.proto,
            "discovered_at": op.timestamp,
        }
    return services


def main() -> int:
    ap = argparse.ArgumentParser(description="masscan wrapper / fallback scanner.")
    ap.add_argument("-t", "--target", required=True,
                    help="IP, CIDR, range, or hostname")
    ap.add_argument("-p", "--ports", default="80,443,22,3389,445,8080",
                    help="port spec (top1000 or 22,80,8000-8100)")
    ap.add_argument("--rate", type=int, default=10000,
                    help="masscan packets/sec (used only when masscan is in use)")
    ap.add_argument("--exclude", default=None,
                    help="masscan --excludefile path")
    ap.add_argument("--no-masscan", action="store_true",
                    help="skip masscan and use built-in async TCP scanner")
    ap.add_argument("--concurrency", type=int, default=200,
                    help="(python backend) max in-flight connects")
    ap.add_argument("--timeout", type=float, default=2.0,
                    help="(python backend) per-connect timeout")
    ap.add_argument("--output", help="write report JSON to this file")
    ap.add_argument("--emit-services-stub", default=None,
                    help="also write a services-stub.json for svc_enum")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color

    rep = Report(target=args.target, started_at=time.time())

    if args.no_masscan or not shutil.which("masscan"):
        rep.backend = "python-asyncio"
        targets = sorted(set(expand(args.target)))
        ports = parse_ports(args.ports)
        print(paint(
            f"[*] {rep.backend}: {len(targets)} hosts × {len(ports)} ports "
            f"= {len(targets) * len(ports)} probes",
            BOLD, color), file=sys.stderr)
        rep.open_ports = asyncio.run(_python_backend(
            targets, ports, args.concurrency, args.timeout))
    else:
        rep.backend = "masscan"
        print(paint(
            f"[*] running masscan -p {args.ports} on {args.target} at rate {args.rate}",
            BOLD, color), file=sys.stderr)
        try:
            rep.open_ports = run_masscan(args.target, args.ports,
                                          args.rate, args.exclude)
        except subprocess.CalledProcessError as e:
            print(paint(f"[!] masscan failed: {e}", RED, color), file=sys.stderr)
            return 1

    rep.finished_at = time.time()
    print(paint(
        f"[*] {len(rep.open_ports)} open ports in {rep.finished_at - rep.started_at:.1f}s",
        GREEN, color), file=sys.stderr)

    out_obj = {
        "target": rep.target,
        "backend": rep.backend,
        "started_at": rep.started_at,
        "finished_at": rep.finished_at,
        "open_ports": [asdict(op) for op in rep.open_ports],
    }
    if args.output:
        Path(args.output).write_text(json.dumps(out_obj, indent=2))
        print(paint(f"[+] wrote {args.output}", GREEN, color), file=sys.stderr)
    else:
        print(json.dumps(out_obj, indent=2))

    if args.emit_services_stub:
        stub = {
            "services": emit_services_stub(rep.open_ports),
            "metadata": {"source": "masscan_wrapper", "ts": rep.finished_at},
        }
        Path(args.emit_services_stub).write_text(json.dumps(stub, indent=2))
        print(paint(f"[+] wrote services stub {args.emit_services_stub}",
                    GREEN, color), file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
