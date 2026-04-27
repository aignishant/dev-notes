#!/usr/bin/env python3
"""
redshift_toolkit.postex.port_forwarder — Generic asyncio TCP forwarder.

Listens on LISTEN_HOST:LISTEN_PORT, forwards every connection to
TARGET_HOST:TARGET_PORT bidirectionally. Logs the first 64 bytes of each
direction (handy for protocol identification) when --verbose.

Usage
-----
  # Forward localhost:13389 → 10.0.0.50:3389 (RDP via pivot)
  python3 -m redshift_toolkit.postex.port_forwarder \\
      --listen 127.0.0.1:13389 --target 10.0.0.50:3389

  # Public listener (e.g. on a redirector) → internal target
  python3 -m redshift_toolkit.postex.port_forwarder \\
      --listen 0.0.0.0:8443 --target internal-app:443

Author: Redshift Project — Module 19
License: MIT
"""

from __future__ import annotations

import argparse
import asyncio
import sys

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


async def relay(reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
                tag: str, verbose: bool):
    bytes_seen = 0
    first = True
    try:
        while True:
            data = await reader.read(8192)
            if not data:
                break
            if first and verbose:
                preview = data[:64].hex()
                print(f"  [{tag}] {len(data)}B  preview={preview}", file=sys.stderr)
                first = False
            bytes_seen += len(data)
            writer.write(data)
            await writer.drain()
    except Exception:
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        if verbose:
            print(f"  [{tag}] closed; {bytes_seen}B forwarded", file=sys.stderr)


def make_handler(target_host: str, target_port: int, verbose: bool):
    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername")
        if verbose:
            print(f"{GREEN}[+] client {peer} → {target_host}:{target_port}{RESET}",
                  file=sys.stderr)
        try:
            r2, w2 = await asyncio.wait_for(
                asyncio.open_connection(target_host, target_port), timeout=10)
        except Exception as e:
            print(f"{RED}[!] target connect failed: {e}{RESET}", file=sys.stderr)
            writer.close()
            return
        await asyncio.gather(
            relay(reader, w2, f"{peer}→target", verbose),
            relay(r2, writer, f"target→{peer}", verbose),
        )
    return handler


async def run(listen_host: str, listen_port: int, target_host: str,
              target_port: int, verbose: bool):
    server = await asyncio.start_server(
        make_handler(target_host, target_port, verbose),
        listen_host, listen_port)
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets)
    print(f"{GREEN}[+] forwarder listening on {addrs} → "
          f"{target_host}:{target_port}{RESET}", file=sys.stderr)
    async with server:
        await server.serve_forever()


def main():
    p = argparse.ArgumentParser(
        prog="port_forwarder",
        description="Asyncio bidirectional TCP forwarder.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--listen", required=True, help="HOST:PORT to listen on")
    p.add_argument("--target", required=True, help="HOST:PORT to forward to")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    lh, lp = args.listen.rsplit(":", 1)
    th, tp = args.target.rsplit(":", 1)
    try:
        asyncio.run(run(lh, int(lp), th, int(tp), args.verbose))
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
