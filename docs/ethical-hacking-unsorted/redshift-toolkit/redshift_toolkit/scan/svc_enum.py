#!/usr/bin/env python3
"""
redshift_toolkit.scan.svc_enum — concurrent service version detection.

Given a list of (host, port) pairs (either via --services-stub from
masscan_wrapper, or a CIDR + port list), probe each with a
protocol-specific request and parse the response for version info.

What it identifies
------------------
- HTTP / HTTPS  → Server header, HTML title, framework hints
- SSH           → SSH-2.0-* banner + software version
- FTP           → 220 banner
- SMTP          → 220 banner
- MySQL         → handshake packet protocol+version
- Redis         → INFO output
- MongoDB       → wire-protocol greet
- SMB           → dialect parsing (delegates to protocols.smb_recon)
- generic       → raw banner up to N bytes

Usage
-----
  ./svc_enum.py --target 10.0.0.10 --ports 22,80,443,3306,6379
  ./svc_enum.py --services-stub services-stub.json --output versions.json
  ./svc_enum.py --target 10.0.0.0/24 --ports top100 --concurrency 300

Output schema (matches asset_graph schema):
  {
    "services": {
      "<ip>:<port>": {
        "ip": "...", "port": ..., "proto": "tcp",
        "service": "http", "version": "...",
        "banner": "...", "extras": {...}
      }
    },
    "metadata": {...}
  }

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


# ─── Probe specifications per port ──────────────────────────────────────────
@dataclass
class Probe:
    port: int
    service: str
    send: bytes = b""
    parser: str = "raw"
    read_bytes: int = 1024
    use_tls: bool = False


PROBES: dict[int, Probe] = {
    21:    Probe(21, "ftp"),
    22:    Probe(22, "ssh"),
    23:    Probe(23, "telnet"),
    25:    Probe(25, "smtp"),
    53:    Probe(53, "dns"),
    80:    Probe(80, "http",
                 b"HEAD / HTTP/1.1\r\nHost: probe\r\nUser-Agent: rs-svc/1\r\nConnection: close\r\n\r\n",
                 parser="http"),
    110:   Probe(110, "pop3"),
    143:   Probe(143, "imap"),
    443:   Probe(443, "https", parser="tls", use_tls=True),
    445:   Probe(445, "smb", parser="smb"),
    3306:  Probe(3306, "mysql", parser="mysql"),
    3389:  Probe(3389, "rdp"),
    5432:  Probe(5432, "postgres",
                 b"\x00\x00\x00\x08\x04\xd2\x16/", parser="raw"),
    5900:  Probe(5900, "vnc"),
    6379:  Probe(6379, "redis", b"INFO\r\nQUIT\r\n", parser="redis"),
    8080:  Probe(8080, "http-alt",
                 b"HEAD / HTTP/1.1\r\nHost: probe\r\nConnection: close\r\n\r\n",
                 parser="http"),
    8443:  Probe(8443, "https-alt", parser="tls", use_tls=True),
    9200:  Probe(9200, "elasticsearch",
                 b"GET / HTTP/1.1\r\nHost: probe\r\n\r\n", parser="http"),
    27017: Probe(27017, "mongodb", parser="mongo"),
}

GENERIC_PROBE = Probe(0, "generic", b"\r\n\r\n")


# ─── Parsers ────────────────────────────────────────────────────────────────
HTTP_SERVER_RE = re.compile(rb"^Server:\s*([^\r\n]+)", re.I | re.M)
HTTP_POWERED_RE = re.compile(rb"^X-Powered-By:\s*([^\r\n]+)", re.I | re.M)
HTTP_TITLE_RE = re.compile(rb"<title[^>]*>([^<]+)</title>", re.I)


def parse_http(data: bytes) -> dict:
    out = {}
    if data.startswith(b"HTTP/"):
        try:
            out["status"] = data.split(b" ", 2)[1].decode()
        except (IndexError, UnicodeDecodeError):
            pass
    m = HTTP_SERVER_RE.search(data)
    if m:
        out["server"] = m.group(1).decode(errors="replace").strip()
    m = HTTP_POWERED_RE.search(data)
    if m:
        out["x_powered_by"] = m.group(1).decode(errors="replace").strip()
    m = HTTP_TITLE_RE.search(data)
    if m:
        out["title"] = m.group(1).decode(errors="replace").strip()[:80]
    return out


def parse_ssh(data: bytes) -> dict:
    out = {}
    line = data.split(b"\n", 1)[0].strip().decode(errors="replace")
    out["banner"] = line
    if line.startswith("SSH-"):
        parts = line.split("-", 2)
        if len(parts) >= 3:
            out["protocol"] = parts[1]
            out["software"] = parts[2]
    return out


def parse_smtp(data: bytes) -> dict:
    text = data.decode(errors="replace").strip()
    return {"banner": text.split("\n", 1)[0][:200]}


def parse_redis(data: bytes) -> dict:
    text = data.decode(errors="replace")
    out = {}
    for line in text.splitlines():
        if line.startswith("redis_version"):
            out["version"] = line.split(":", 1)[1].strip()
        elif line.startswith("os:"):
            out["os"] = line.split(":", 1)[1].strip()
        elif line.startswith("redis_mode"):
            out["mode"] = line.split(":", 1)[1].strip()
    if not out:
        if text.startswith("-NOAUTH"):
            out["state"] = "requires_auth"
        elif text:
            out["state"] = "responded"
    return out


def parse_mysql(data: bytes) -> dict:
    out = {}
    if len(data) < 5:
        return out
    out["protocol"] = data[4]
    end = data.find(b"\x00", 5)
    if end > 5:
        out["version"] = data[5:end].decode(errors="replace")
    return out


def parse_mongo(data: bytes) -> dict:
    return {"replied": bool(data),
            "first_bytes_hex": data[:24].hex() if data else ""}


def parse_smb(data: bytes) -> dict:
    if len(data) < 8:
        return {"state": "no_response"}
    if data[4:8] == b"\xffSMB":
        return {"protocol": "SMB1"}
    if data[4:8] == b"\xfeSMB":
        return {"protocol": "SMB2/3"}
    if data[4:8] == b"\xfdSMB":
        return {"protocol": "SMB3-encrypted"}
    return {"state": "non-SMB"}


def parse_tls(data: bytes) -> dict:
    return {"state": "tls_port_open",
            "first_bytes_hex": data[:16].hex() if data else ""}


PARSERS = {
    "http": parse_http, "ssh": parse_ssh, "smtp": parse_smtp,
    "redis": parse_redis, "mysql": parse_mysql, "mongo": parse_mongo,
    "smb": parse_smb, "tls": parse_tls, "raw": lambda d: {},
}


# ─── Probe runner ───────────────────────────────────────────────────────────
@dataclass
class ServiceHit:
    ip: str
    port: int
    proto: str = "tcp"
    service: str = ""
    version: str = ""
    banner: str = ""
    extras: dict = field(default_factory=dict)
    rtt_ms: float = 0.0


async def probe_one(ip: str, port: int, timeout: float) -> ServiceHit | None:
    spec = PROBES.get(port) or Probe(port=port, service=f"tcp/{port}")
    t0 = time.perf_counter()
    try:
        if spec.use_tls:
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port, ssl=ctx,
                                        server_hostname=ip),
                timeout=timeout,
            )
        else:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port), timeout=timeout)
    except (asyncio.TimeoutError, OSError, Exception):
        return None

    hit = ServiceHit(ip=ip, port=port, service=spec.service)
    try:
        if spec.send:
            try:
                writer.write(spec.send)
                await writer.drain()
            except Exception:
                pass
        try:
            data = await asyncio.wait_for(reader.read(spec.read_bytes),
                                          timeout=timeout)
        except asyncio.TimeoutError:
            data = b""
    except OSError:
        data = b""
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    hit.rtt_ms = (time.perf_counter() - t0) * 1000.0
    if data:
        hit.banner = data[:200].decode("latin-1", errors="replace").strip()
    parsed = PARSERS.get(spec.parser, lambda d: {})(data) or {}
    if "version" in parsed:
        hit.version = parsed.pop("version")
    elif "software" in parsed:
        hit.version = parsed.pop("software")
    elif "server" in parsed:
        hit.version = parsed.pop("server")
    hit.extras = parsed
    return hit


async def run_scan(jobs: list[tuple[str, int]], concurrency: int,
                   timeout: float) -> list[ServiceHit]:
    sem = asyncio.Semaphore(concurrency)

    async def guarded(ip: str, port: int):
        async with sem:
            return await probe_one(ip, port, timeout)

    tasks = [asyncio.create_task(guarded(ip, p)) for ip, p in jobs]
    out: list[ServiceHit] = []
    for fut in asyncio.as_completed(tasks):
        h = await fut
        if h:
            out.append(h)
    return out


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


def main() -> int:
    ap = argparse.ArgumentParser(description="Concurrent service version probe.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--target", help="IP / CIDR / range / hostname")
    g.add_argument("--services-stub",
                   help="JSON file from masscan_wrapper --emit-services-stub")
    ap.add_argument("--ports", default=",".join(str(p) for p in PROBES))
    ap.add_argument("--concurrency", type=int, default=200)
    ap.add_argument("--timeout", type=float, default=2.5)
    ap.add_argument("--output", help="write services JSON here")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color

    jobs: list[tuple[str, int]] = []
    if args.services_stub:
        stub = json.loads(Path(args.services_stub).read_text())
        for key, svc in (stub.get("services") or {}).items():
            jobs.append((svc["ip"], int(svc["port"])))
    else:
        targets = sorted(set(expand(args.target)))
        ports = sorted({int(p) for p in args.ports.split(",") if p})
        for h in targets:
            for p in ports:
                jobs.append((h, p))

    print(paint(f"[*] svc_enum: {len(jobs)} probe(s) (concurrency={args.concurrency})",
                BOLD, color), file=sys.stderr)
    t0 = time.time()
    hits = asyncio.run(run_scan(jobs, args.concurrency, args.timeout))
    dt = time.time() - t0
    print(paint(
        f"[*] identified {len(hits)} service(s) in {dt:.1f}s", GREEN, color
    ), file=sys.stderr)

    services_out: dict[str, dict] = {}
    for h in hits:
        services_out[f"{h.ip}:{h.port}"] = asdict(h)

    out_obj = {
        "services": services_out,
        "metadata": {"generated_at": time.time(),
                     "tool": "svc_enum",
                     "elapsed_s": dt},
    }

    if args.output:
        Path(args.output).write_text(json.dumps(out_obj, indent=2))
        print(paint(f"[+] wrote {args.output}", GREEN, color), file=sys.stderr)
    else:
        print(json.dumps(out_obj, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
