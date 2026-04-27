#!/usr/bin/env python3
"""
redshift_toolkit.web.websocket_fuzzer — WebSocket auth + CSWSH probe.

Modes
-----
- --upgrade-test:   send the WebSocket upgrade with NO auth header, with a
                    different Origin: header, with no Origin at all. Observe
                    whether the upgrade succeeds. The classic CSWSH symptom
                    is: upgrade succeeds with attacker Origin, then the
                    server pushes authenticated data based on the cookie
                    sent by the browser.
- --send:           after a successful upgrade, send custom messages and
                    print server replies.
- --auth-mismatch:  upgrade with one user's cookie/token, then attempt to
                    send a message that should belong to another (e.g.,
                    referencing another user_id in the payload).

This module implements just enough of the WebSocket framing protocol
(RFC 6455) to do upgrade + send/receive of text frames. Compression and
binary frames are out of scope.

Usage
-----
  python3 -m redshift_toolkit.web.websocket_fuzzer \\
      --url wss://api.example.com/ws --upgrade-test --origin https://evil.com
  python3 -m redshift_toolkit.web.websocket_fuzzer \\
      --url wss://api.example.com/ws --auth-cookie 'session=...' \\
      --send '{"type":"ping"}'

Author: Redshift Project — Module 15
License: MIT — Lab use only.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import socket
import ssl
import struct
import sys
from urllib.parse import urlsplit

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def _ws_key() -> str:
    return base64.b64encode(os.urandom(16)).decode()


def _expected_accept(key: str) -> str:
    import hashlib
    return base64.b64encode(
        hashlib.sha1((key + WS_GUID).encode()).digest()
    ).decode()


def upgrade(url: str, *, origin: str | None = None,
            auth_cookie: str | None = None, bearer: str | None = None,
            extra_headers: list[tuple[str, str]] | None = None,
            tls_verify: bool = True, timeout: float = 10.0
            ) -> tuple[bool, int, str, socket.socket | None, bytes]:
    """Send the WebSocket upgrade. Returns (success, status, raw_response_head,
    open_socket_if_success, leftover_bytes)."""
    sp = urlsplit(url)
    if sp.scheme not in ("ws", "wss"):
        raise ValueError(f"expected ws:// or wss:// URL, got {sp.scheme}")
    tls = (sp.scheme == "wss")
    host = sp.hostname or ""
    port = sp.port or (443 if tls else 80)
    path = sp.path or "/"
    if sp.query:
        path += "?" + sp.query

    key = _ws_key()
    headers = [
        ("Host", host),
        ("Upgrade", "websocket"),
        ("Connection", "Upgrade"),
        ("Sec-WebSocket-Key", key),
        ("Sec-WebSocket-Version", "13"),
        ("User-Agent", "redshift-toolkit-ws/0.4"),
    ]
    if origin:
        headers.append(("Origin", origin))
    if auth_cookie:
        headers.append(("Cookie", auth_cookie))
    if bearer:
        headers.append(("Authorization", f"Bearer {bearer}"))
    for k, v in (extra_headers or []):
        headers.append((k, v))

    req = (f"GET {path} HTTP/1.1\r\n"
           + "".join(f"{k}: {v}\r\n" for k, v in headers)
           + "\r\n").encode()

    s = socket.create_connection((host, port), timeout=timeout)
    if tls:
        ctx = ssl.create_default_context()
        if not tls_verify:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        s = ctx.wrap_socket(s, server_hostname=host)

    s.sendall(req)
    s.settimeout(timeout)
    raw = b""
    while b"\r\n\r\n" not in raw and len(raw) < 8192:
        try:
            chunk = s.recv(4096)
        except socket.timeout:
            break
        if not chunk:
            break
        raw += chunk

    head, _, leftover = raw.partition(b"\r\n\r\n")
    head_text = head.decode("latin-1", errors="replace")
    status = 0
    first = head_text.split("\r\n", 1)[0] if head_text else ""
    parts = first.split(" ", 2)
    if len(parts) >= 2 and parts[1].isdigit():
        status = int(parts[1])

    if status == 101:
        # Verify Sec-WebSocket-Accept
        ok = False
        for line in head_text.split("\r\n"):
            if line.lower().startswith("sec-websocket-accept:"):
                got = line.split(":", 1)[1].strip()
                if got == _expected_accept(key):
                    ok = True
                break
        return ok, status, head_text, (s if ok else None), leftover
    try:
        s.close()
    except Exception:
        pass
    return False, status, head_text, None, leftover


def _send_text_frame(s: socket.socket, payload: str) -> None:
    data = payload.encode()
    fin_op = 0x81  # FIN + text
    mask = os.urandom(4)
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    plen = len(data)
    if plen < 126:
        header = bytes([fin_op, 0x80 | plen]) + mask
    elif plen < 65536:
        header = bytes([fin_op, 0x80 | 126]) + plen.to_bytes(2, "big") + mask
    else:
        header = bytes([fin_op, 0x80 | 127]) + plen.to_bytes(8, "big") + mask
    s.sendall(header + masked)


def _read_frame(s: socket.socket, timeout: float = 5.0) -> tuple[int, bytes]:
    s.settimeout(timeout)
    head = s.recv(2)
    if len(head) < 2:
        return 0, b""
    fin_op = head[0]
    op = fin_op & 0x0F
    masked = (head[1] & 0x80) != 0
    plen = head[1] & 0x7F
    if plen == 126:
        plen = int.from_bytes(s.recv(2), "big")
    elif plen == 127:
        plen = int.from_bytes(s.recv(8), "big")
    mask = s.recv(4) if masked else b""
    payload = b""
    while len(payload) < plen:
        chunk = s.recv(plen - len(payload))
        if not chunk:
            break
        payload += chunk
    if masked and mask:
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return op, payload


def main() -> int:
    ap = argparse.ArgumentParser(description="WebSocket auth + CSWSH probe.")
    ap.add_argument("--url", required=True, help="ws:// or wss:// URL")
    ap.add_argument("--upgrade-test", action="store_true",
                    help="run the matrix of {origin, no origin, evil origin}")
    ap.add_argument("--auth-cookie", help="cookie to send during upgrade")
    ap.add_argument("--bearer", help="bearer token to send during upgrade")
    ap.add_argument("--origin", default=None, help="Origin: header for upgrade")
    ap.add_argument("--send", help="send this message after a successful upgrade")
    ap.add_argument("--recv-count", type=int, default=3,
                    help="how many frames to read after sending")
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--timeout", type=float, default=10.0)
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color

    if args.upgrade_test:
        scenarios = [
            ("no-auth, no Origin", None, None, None),
            ("no-auth, evil Origin", "https://evil.example.com", None, None),
            ("with-auth, no Origin", None, args.auth_cookie, args.bearer),
            ("with-auth, same Origin",
                f"https://{urlsplit(args.url).hostname}", args.auth_cookie, args.bearer),
            ("with-auth, evil Origin (CSWSH)",
                "https://evil.example.com", args.auth_cookie, args.bearer),
        ]
        for label, origin, cookie, bearer in scenarios:
            ok, status, head, sock, _ = upgrade(args.url, origin=origin,
                                                 auth_cookie=cookie,
                                                 bearer=bearer,
                                                 tls_verify=not args.insecure,
                                                 timeout=args.timeout)
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass
            tag = (paint("[OK  ]", GREEN, color) if ok
                   else paint("[FAIL]", RED, color))
            note = ""
            if "evil" in label and ok:
                note = paint("  ← upgrade succeeded with attacker Origin (CSWSH risk)",
                             RED, color)
            print(f"  {tag} {label:<35} status={status}{note}")
        return 0

    # Default: upgrade and optionally send a message
    ok, status, head, sock, leftover = upgrade(args.url, origin=args.origin,
                                                auth_cookie=args.auth_cookie,
                                                bearer=args.bearer,
                                                tls_verify=not args.insecure,
                                                timeout=args.timeout)
    if not ok or not sock:
        print(paint(f"[!] upgrade failed (status {status})", RED, color),
              file=sys.stderr)
        print(head, file=sys.stderr)
        return 1
    print(paint(f"[+] upgrade succeeded (status {status})", GREEN, color))

    if args.send:
        _send_text_frame(sock, args.send)
        for _ in range(args.recv_count):
            try:
                op, payload = _read_frame(sock, timeout=args.timeout)
            except Exception as e:
                print(f"  read error: {e}")
                break
            if op == 0x1:  # text
                print(f"  ← TEXT: {payload.decode('utf-8', errors='replace')[:500]}")
            elif op == 0x2:
                print(f"  ← BINARY: {len(payload)}b")
            elif op == 0x8:
                print(f"  ← CLOSE")
                break
            elif op == 0x9:
                print(f"  ← PING")
            elif op == 0xA:
                print(f"  ← PONG")
            else:
                print(f"  ← op=0x{op:x} len={len(payload)}")

    try:
        sock.close()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
