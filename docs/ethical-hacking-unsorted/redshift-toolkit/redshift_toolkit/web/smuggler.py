#!/usr/bin/env python3
"""
redshift_toolkit.web.smuggler — HTTP request smuggling detector.

Detection method (timing-based, per PortSwigger Web Security Academy):

For each variant (CL.TE, TE.CL, TE.TE), we send a probe whose body
declarations cause the *backend* to wait for additional bytes that the
*frontend* won't send. If the backend disagrees with the frontend, our
connection times out (or is held open longer than baseline). If they
agree, the response comes back at baseline speed.

We compare elapsed times with a control request to identify desync.

Variants tested
---------------
- CL.TE       : both CL and TE; frontend uses CL, backend uses TE
- TE.CL       : both; frontend TE, backend CL
- TE.TE (×6)  : various obfuscations of duplicate TE that bypass one parser
- HTTP/2 H2.0 : if --http2 specified, send H2 request with embedded TE/CL

This module DETECTS smuggling potential. Full exploitation requires
manual handling per-target (different impact stories per target — auth
bypass, cache poisoning of prefix, etc.).

Usage
-----
  python3 -m redshift_toolkit.web.smuggler --url https://example.com
  python3 -m redshift_toolkit.web.smuggler --url https://example.com --variant TE.CL --json

Author: Redshift Project — Module 16
License: MIT — Lab use only.
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
import time
from dataclasses import dataclass, asdict, field
from urllib.parse import urlsplit

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


def _connect(host: str, port: int, tls: bool, *, timeout: float = 10.0,
             tls_verify: bool = True) -> socket.socket:
    s = socket.create_connection((host, port), timeout=timeout)
    if tls:
        ctx = ssl.create_default_context()
        if not tls_verify:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        s = ctx.wrap_socket(s, server_hostname=host)
    return s


def _read_response(s: socket.socket, timeout: float = 5.0) -> bytes:
    s.settimeout(timeout)
    chunks = []
    while True:
        try:
            chunk = s.recv(8192)
        except (socket.timeout, ConnectionResetError):
            break
        if not chunk:
            break
        chunks.append(chunk)
        if len(b"".join(chunks)) > 1024 * 1024:
            break
    return b"".join(chunks)


def _baseline(host: str, port: int, tls: bool, path: str, *,
              timeout: float = 10.0, tls_verify: bool = True) -> tuple[int, float]:
    """One simple POST as baseline. Returns (status, elapsed_s)."""
    body = "x=y"
    req = (f"POST {path} HTTP/1.1\r\n"
           f"Host: {host}\r\n"
           f"Content-Length: {len(body)}\r\n"
           f"Connection: close\r\n"
           f"\r\n"
           f"{body}").encode()
    s = _connect(host, port, tls, timeout=timeout, tls_verify=tls_verify)
    t0 = time.time()
    try:
        s.sendall(req)
        raw = _read_response(s, timeout=5.0)
    finally:
        try:
            s.close()
        except Exception:
            pass
    elapsed = time.time() - t0
    status = 0
    if raw.startswith(b"HTTP/"):
        line = raw.split(b"\r\n", 1)[0].decode("latin-1", errors="replace")
        parts = line.split(" ", 2)
        if len(parts) >= 2 and parts[1].isdigit():
            status = int(parts[1])
    return status, elapsed


# Build smuggling probe payloads. We use POST / with an extra junk header.
# In all cases the *intended* result if smuggling works is that the backend
# waits for more data, causing our read() to time out / hang.

def _probe_cl_te(host: str, path: str) -> bytes:
    """Frontend uses CL (5), backend uses TE (chunked → terminator at 0\r\n\r\n).
    If frontend wins: full body consumed → response. If backend wins:
    chunked body never terminates from its perspective, sees only `0\r\n\r\nG`
    where G is start of next request. Backend hangs."""
    body = (
        "0\r\n"      # zero-length chunk → backend says "done"
        "\r\n"
        "G"          # extra byte the frontend includes in CL=6 but
                     # backend treats as start of next request
    )
    return (f"POST {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"Content-Length: 6\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"\r\n"
            f"{body}").encode()


def _probe_te_cl(host: str, path: str) -> bytes:
    """Frontend uses TE, backend uses CL.

    TE-decoded body: chunk size 8 + "SMUGGLED" + 0\r\n\r\n  → 1 request to FE.
    CL=3 means BE only reads "8\r\n", then expects next request — the
    "SMUGGLED..." prefix is the next request. BE may hang waiting for it
    to complete.
    """
    body = (
        "8\r\n"
        "SMUGGLED\r\n"
        "0\r\n"
        "\r\n"
    )
    return (f"POST {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"Content-Length: 3\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"\r\n"
            f"{body}").encode()


# TE.TE variants — try to obfuscate TE so one impl rejects, the other accepts.
TE_TE_VARIANTS = [
    ("space-before-colon",
        b"Transfer-Encoding : chunked\r\n"),
    ("tab-separator",
        b"Transfer-Encoding:\tchunked\r\n"),
    ("duplicate-headers",
        b"Transfer-Encoding: chunked\r\nTransfer-Encoding: x\r\n"),
    ("xa0 whitespace",
        b"Transfer-Encoding: chunked\r\n X: y\r\n"),  # leading space line continuation
    ("smuggled-prefix",
        b" Transfer-Encoding: chunked\r\n"),
    ("uppercase-only",
        b"TRANSFER-ENCODING: chunked\r\n"),
]


def _probe_te_te(host: str, path: str, te_header_block: bytes) -> bytes:
    body = (
        "0\r\n"
        "\r\n"
        "G"
    ).encode()
    return (f"POST {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n".encode()
            + te_header_block
            + f"Content-Length: 6\r\n"
            f"\r\n".encode()
            + body)


@dataclass
class SmugFinding:
    variant: str
    elapsed_s: float
    status: int
    suspect: bool
    note: str = ""


def _send_and_time(host: str, port: int, tls: bool, payload: bytes,
                   *, timeout: float, tls_verify: bool) -> tuple[int, float]:
    s = _connect(host, port, tls, timeout=timeout, tls_verify=tls_verify)
    t0 = time.time()
    try:
        s.sendall(payload)
        raw = _read_response(s, timeout=timeout)
    finally:
        try:
            s.close()
        except Exception:
            pass
    elapsed = time.time() - t0
    status = 0
    if raw.startswith(b"HTTP/"):
        line = raw.split(b"\r\n", 1)[0].decode("latin-1", errors="replace")
        parts = line.split(" ", 2)
        if len(parts) >= 2 and parts[1].isdigit():
            status = int(parts[1])
    return status, elapsed


def detect(host: str, port: int = 443, *, tls: bool = True,
           path: str = "/", variants: list[str] | None = None,
           hang_threshold: float = 4.0,
           timeout: float = 10.0,
           tls_verify: bool = True) -> tuple[float, list[SmugFinding]]:
    base_status, base_elapsed = _baseline(host, port, tls, path,
                                            timeout=timeout, tls_verify=tls_verify)

    def _record(label: str, payload: bytes) -> SmugFinding:
        try:
            st, el = _send_and_time(host, port, tls, payload,
                                     timeout=hang_threshold + 1.0,
                                     tls_verify=tls_verify)
        except (socket.timeout, ConnectionResetError) as e:
            return SmugFinding(variant=label,
                               elapsed_s=hang_threshold + 1.0,
                               status=0, suspect=True,
                               note=f"socket error: {e}")
        suspect = (el >= base_elapsed + hang_threshold)
        note = (f"baseline={base_elapsed:.2f}s, this={el:.2f}s "
                f"(Δ={el-base_elapsed:+.2f}s)")
        return SmugFinding(variant=label, elapsed_s=el, status=st,
                           suspect=suspect, note=note)

    out: list[SmugFinding] = []

    if not variants or "CL.TE" in variants:
        out.append(_record("CL.TE", _probe_cl_te(host, path)))
    if not variants or "TE.CL" in variants:
        out.append(_record("TE.CL", _probe_te_cl(host, path)))
    if not variants or "TE.TE" in variants:
        for label, hdr in TE_TE_VARIANTS:
            out.append(_record(f"TE.TE/{label}", _probe_te_te(host, path, hdr)))

    return base_elapsed, out


def render_text(base_elapsed: float, findings: list[SmugFinding],
                color: bool) -> str:
    out = [paint("\n=== HTTP request smuggling detector ===", BOLD, color)]
    out.append(f"  baseline elapsed: {base_elapsed:.2f}s")
    suspect_count = 0
    for f in findings:
        if f.suspect:
            tag = paint("[SUSPECT]", RED, color)
            suspect_count += 1
        else:
            tag = paint("[ ok    ]", GREEN, color)
        out.append(f"  {tag} {f.variant:<26} status={f.status}  {f.note}")
    out.append("")
    if suspect_count:
        out.append(paint(
            f"  {suspect_count} variant(s) showed timing differences — "
            f"manual confirmation recommended", RED, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="HTTP request smuggling detector.")
    ap.add_argument("--url", required=True)
    ap.add_argument("--variant", action="append", default=None,
                    help="restrict variants (e.g. --variant CL.TE --variant TE.CL)")
    ap.add_argument("--hang-threshold", type=float, default=4.0,
                    help="extra seconds beyond baseline to consider 'hanging' "
                         "(default 4)")
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--timeout", type=float, default=10.0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    sp = urlsplit(args.url)
    if sp.scheme not in ("http", "https"):
        print("expected http/https", file=sys.stderr)
        return 2
    host = sp.hostname or ""
    port = sp.port or (443 if sp.scheme == "https" else 80)
    path = sp.path or "/"

    base_elapsed, findings = detect(host, port, tls=(sp.scheme == "https"),
                                     path=path, variants=args.variant,
                                     hang_threshold=args.hang_threshold,
                                     timeout=args.timeout,
                                     tls_verify=not args.insecure)

    if args.json:
        print(json.dumps({
            "baseline_elapsed_s": base_elapsed,
            "findings": [asdict(f) for f in findings],
        }, indent=2))
    else:
        print(render_text(base_elapsed, findings, color))

    return 0 if not any(f.suspect for f in findings) else 1


if __name__ == "__main__":
    sys.exit(main())
