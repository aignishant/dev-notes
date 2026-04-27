"""
Mini Multi-Port Honeypot
========================

A passive, asyncio-driven honeypot. Listens on a configurable list of TCP
ports, accepts connections, records *what* the attacker sends (first N bytes),
then drops the connection. **It never responds with anything** — that keeps
it simple, low-risk, and makes it useless as a pivot.

Defensive use only. Run on your own infrastructure to detect lateral
movement, opportunistic scanning, or to feed an internal threat-intel feed.

Usage
-----
    sudo python mini_honeypot.py --ports 21,22,23,80,443,3389,5900
    python mini_honeypot.py --ports 2222,8080 --log honeypot.jsonl

The script writes JSONL events to stdout (or --log file). Each event has:
    {ts, src_ip, src_port, dst_port, bytes_recv, sample_b64, sample_ascii}
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import datetime as dt
import json
import logging
import signal
import sys
from pathlib import Path

DEFAULT_PORTS = [21, 22, 23, 25, 80, 110, 143, 443, 445, 1433, 3306,
                 3389, 5432, 5900, 6379, 8080, 8443]

MAX_RECV = 4096       # cap how much we read per connection
READ_TIMEOUT = 3.0    # seconds before we give up waiting for client data

log = logging.getLogger("honeypot")


def _ascii_preview(data: bytes, limit: int = 200) -> str:
    """Return a printable-ASCII rendering of bytes, escapes for control chars."""
    out: list[str] = []
    for b in data[:limit]:
        if 32 <= b < 127:
            out.append(chr(b))
        elif b in (9, 10, 13):
            out.append({9: r"\t", 10: r"\n", 13: r"\r"}[b])
        else:
            out.append(f"\\x{b:02x}")
    suffix = "..." if len(data) > limit else ""
    return "".join(out) + suffix


class HoneypotServer:
    def __init__(self, ports: list[int], host: str, sink) -> None:
        self.ports = ports
        self.host = host
        self.sink = sink     # file-like with .write() + .flush()
        self._servers: list[asyncio.AbstractServer] = []
        self._stop = asyncio.Event()

    async def _handle(self, reader: asyncio.StreamReader,
                      writer: asyncio.StreamWriter, port: int) -> None:
        peer = writer.get_extra_info("peername") or ("?", 0)
        src_ip, src_port = peer[0], peer[1]
        data = b""
        try:
            try:
                data = await asyncio.wait_for(
                    reader.read(MAX_RECV), timeout=READ_TIMEOUT)
            except asyncio.TimeoutError:
                pass
            event = {
                "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
                "src_ip": src_ip,
                "src_port": src_port,
                "dst_port": port,
                "bytes_recv": len(data),
                "sample_b64": base64.b64encode(data).decode() if data else "",
                "sample_ascii": _ascii_preview(data) if data else "",
            }
            self.sink.write(json.dumps(event) + "\n")
            self.sink.flush()
            log.info("hit  %s:%d -> :%d  bytes=%d",
                     src_ip, src_port, port, len(data))
        except Exception as e:                     # noqa: BLE001
            log.warning("error handling %s:%d -> :%d : %r",
                        src_ip, src_port, port, e)
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except OSError:
                pass

    async def start(self) -> None:
        for port in self.ports:
            try:
                server = await asyncio.start_server(
                    lambda r, w, p=port: self._handle(r, w, p),
                    host=self.host, port=port,
                    reuse_address=True)
                self._servers.append(server)
                log.info("listening on %s:%d", self.host, port)
            except PermissionError:
                log.error("permission denied for port %d "
                          "(low ports require root)", port)
            except OSError as e:
                log.error("could not bind %d: %s", port, e)

        if not self._servers:
            log.critical("no ports bound; exiting")
            return

        await self._stop.wait()

        for s in self._servers:
            s.close()
        await asyncio.gather(*(s.wait_closed() for s in self._servers),
                             return_exceptions=True)
        log.info("shut down cleanly")

    def stop(self) -> None:
        self._stop.set()


def parse_ports(spec: str) -> list[int]:
    out: set[int] = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            a, b = chunk.split("-", 1)
            for p in range(int(a), int(b) + 1):
                out.add(p)
        else:
            out.add(int(chunk))
    bad = [p for p in out if not 1 <= p <= 65535]
    if bad:
        raise ValueError(f"invalid ports: {bad}")
    return sorted(out)


async def amain(args: argparse.Namespace) -> None:
    ports = parse_ports(args.ports) if args.ports else DEFAULT_PORTS
    sink = open(args.log, "a", buffering=1) if args.log else sys.stdout
    server = HoneypotServer(ports=ports, host=args.host, sink=sink)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, server.stop)
        except NotImplementedError:
            # Windows
            pass

    try:
        await server.start()
    finally:
        if sink is not sys.stdout:
            sink.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ports", help="Comma-separated ports/ranges, "
                                    "e.g. '22,80,443,8000-8010'")
    ap.add_argument("--host", default="0.0.0.0", help="Bind address")
    ap.add_argument("--log", type=Path,
                    help="Append JSONL events to this file (default stdout)")
    ap.add_argument("--quiet", action="store_true", help="Less verbose stderr")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    try:
        asyncio.run(amain(args))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
