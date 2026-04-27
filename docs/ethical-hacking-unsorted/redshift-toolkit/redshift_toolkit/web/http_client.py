#!/usr/bin/env python3
"""
redshift_toolkit.web.http_client — raw HTTP/1.1 client.

Why not just use `requests`?
----------------------------
For 95% of work, `requests` is fine. But for offensive testing you need:
  - exact control over byte-level request format (smuggling, header tricks)
  - the ability to send malformed requests that `requests`/`urllib3` reject
  - to avoid the `urllib3` TLS fingerprint that every WAF flags
  - to read raw response bytes including unparseable garbage
  - to skip CRLF normalization and Host-header insertion

This module gives you a raw-byte client when you want one and a friendly
high-level API when you don't.

Capabilities
------------
- HTTP/1.0 and HTTP/1.1 over plain TCP or TLS
- Send arbitrary header sets including duplicates and weird casing
- Decode chunked Transfer-Encoding
- Follow or refuse to follow redirects
- "Fingerprint" mode: request a target, dump every response header
  including those that disclose framework, version, CDN, cache state.
- Importable API and CLI

Usage
-----
  python3 -m redshift_toolkit.web.http_client --url https://example.com --fingerprint
  python3 -m redshift_toolkit.web.http_client --url https://example.com \\
      -H 'X-Custom: foo' -X POST --body '{"x":1}'
  python3 -m redshift_toolkit.web.http_client --url https://example.com --raw

  >>> from redshift_toolkit.web.http_client import HttpRequest, send
  >>> r = send(HttpRequest(method="GET", url="https://example.com"))
  >>> r.status, r.headers["Server"]

Author: Redshift Project — Module 13
License: MIT
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
import time
from dataclasses import dataclass, field
from typing import Iterable
from urllib.parse import urlsplit

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


@dataclass
class HttpRequest:
    method: str = "GET"
    url: str = ""
    # When `headers` is a list of (k,v) tuples we preserve order and duplicates.
    # When it's a dict we insert in dict order with a single value each.
    headers: list[tuple[str, str]] | dict[str, str] = field(default_factory=list)
    body: bytes | str | None = None
    http_version: str = "HTTP/1.1"
    # Override: if set, ignore url parsing and use these directly.
    raw_path: str | None = None
    raw_host: str | None = None
    raw_port: int | None = None
    raw_scheme: str | None = None    # "http" or "https"


@dataclass
class HttpResponse:
    status: int
    reason: str
    http_version: str
    headers: list[tuple[str, str]]
    body: bytes
    raw: bytes
    elapsed_ms: float

    def header(self, name: str) -> str | None:
        ln = name.lower()
        for k, v in self.headers:
            if k.lower() == ln:
                return v
        return None

    @property
    def headers_dict(self) -> dict[str, str]:
        # Lower-cased, last-wins.
        return {k.lower(): v for k, v in self.headers}


# Headers we try not to add automatically when the caller is doing raw work.
_DEFAULT_UA = "redshift-toolkit/0.4 (https://github.com/redshift-project)"

# Headers we audit/highlight in --fingerprint mode.
INTERESTING_HEADERS = [
    "Server", "X-Powered-By", "X-AspNet-Version", "X-AspNetMvc-Version",
    "X-Drupal-Cache", "X-Drupal-Dynamic-Cache", "X-Generator",
    "Via", "X-Backend-Server", "X-Served-By", "X-Cache", "X-Cache-Hits",
    "CF-RAY", "CF-Cache-Status", "X-Amz-Cf-Id", "X-Akamai-Edgescape",
    "Strict-Transport-Security", "Content-Security-Policy",
    "X-Frame-Options", "X-Content-Type-Options", "Referrer-Policy",
    "Permissions-Policy", "Cross-Origin-Embedder-Policy",
    "Cross-Origin-Opener-Policy", "Cross-Origin-Resource-Policy",
    "Set-Cookie", "Cache-Control", "Pragma", "Expires",
    "Access-Control-Allow-Origin", "Access-Control-Allow-Credentials",
    "Access-Control-Allow-Methods", "Access-Control-Allow-Headers",
]


def _parse_url(url: str) -> tuple[str, str, int, str]:
    sp = urlsplit(url)
    scheme = (sp.scheme or "http").lower()
    host = sp.hostname or ""
    if not host:
        raise ValueError(f"could not parse host from {url!r}")
    port = sp.port or (443 if scheme == "https" else 80)
    path = sp.path or "/"
    if sp.query:
        path += "?" + sp.query
    return scheme, host, port, path


def _build_request_bytes(req: HttpRequest) -> tuple[bytes, str, str, int]:
    """Build the wire bytes and return (bytes, scheme, host, port)."""
    if req.raw_host:
        scheme = req.raw_scheme or "http"
        host = req.raw_host
        port = req.raw_port or (443 if scheme == "https" else 80)
        path = req.raw_path or "/"
    else:
        scheme, host, port, path = _parse_url(req.url)

    headers = list(req.headers.items()) if isinstance(req.headers, dict) \
        else list(req.headers)

    # Fill in defaults only if not already present (case-insensitive).
    have = {k.lower() for k, _ in headers}
    if "host" not in have:
        headers.append(("Host", f"{host}:{port}" if port not in (80, 443) else host))
    if "user-agent" not in have:
        headers.append(("User-Agent", _DEFAULT_UA))
    if "accept" not in have:
        headers.append(("Accept", "*/*"))
    if "connection" not in have:
        headers.append(("Connection", "close"))

    body_bytes = b""
    if req.body is not None:
        body_bytes = req.body if isinstance(req.body, bytes) else req.body.encode("utf-8")
        if "content-length" not in have and "transfer-encoding" not in have:
            headers.append(("Content-Length", str(len(body_bytes))))

    request_line = f"{req.method} {path} {req.http_version}\r\n".encode()
    header_block = b"".join(f"{k}: {v}\r\n".encode() for k, v in headers)
    payload = request_line + header_block + b"\r\n" + body_bytes
    return payload, scheme, host, port


def _read_response(sock: socket.socket, timeout: float = 10.0,
                   max_bytes: int = 10 * 1024 * 1024) -> bytes:
    sock.settimeout(timeout)
    chunks = []
    total = 0
    while total < max_bytes:
        try:
            chunk = sock.recv(8192)
        except (socket.timeout, ConnectionResetError):
            break
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
    return b"".join(chunks)


def _decode_chunked(body: bytes) -> bytes:
    out = bytearray()
    pos = 0
    while pos < len(body):
        crlf = body.find(b"\r\n", pos)
        if crlf < 0:
            break
        size_line = body[pos:crlf].split(b";")[0].strip()
        try:
            size = int(size_line, 16)
        except ValueError:
            break
        pos = crlf + 2
        if size == 0:
            break
        out += body[pos:pos + size]
        pos += size + 2
    return bytes(out)


def _parse_response(raw: bytes) -> HttpResponse:
    head, _, body_part = raw.partition(b"\r\n\r\n")
    lines = head.split(b"\r\n")
    if not lines:
        raise ValueError("empty response")
    status_line = lines[0].decode("latin-1", errors="replace")
    parts = status_line.split(" ", 2)
    version = parts[0] if len(parts) > 0 else "HTTP/?"
    status = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    reason = parts[2] if len(parts) > 2 else ""
    headers: list[tuple[str, str]] = []
    for ln in lines[1:]:
        s = ln.decode("latin-1", errors="replace")
        if ":" in s:
            k, v = s.split(":", 1)
            headers.append((k.strip(), v.strip()))

    body = body_part
    te = ""
    cl = ""
    for k, v in headers:
        if k.lower() == "transfer-encoding":
            te = v.lower()
        elif k.lower() == "content-length":
            cl = v
    if "chunked" in te:
        body = _decode_chunked(body)
    elif cl.isdigit():
        body = body[:int(cl)]

    return HttpResponse(status=status, reason=reason, http_version=version,
                        headers=headers, body=body, raw=raw, elapsed_ms=0.0)


def send(req: HttpRequest, *, timeout: float = 10.0,
         tls_verify: bool = True, follow_redirects: bool = False,
         max_redirects: int = 5,
         tls_sni: str | None = None) -> HttpResponse:
    """Send an HttpRequest and return an HttpResponse."""
    visited = 0
    current = req
    while True:
        payload, scheme, host, port = _build_request_bytes(current)
        s = socket.create_connection((host, port), timeout=timeout)
        try:
            if scheme == "https":
                ctx = ssl.create_default_context()
                if not tls_verify:
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                s = ctx.wrap_socket(s, server_hostname=tls_sni or host)
            t0 = time.time()
            s.sendall(payload)
            raw = _read_response(s, timeout=timeout)
            elapsed_ms = (time.time() - t0) * 1000
        finally:
            try:
                s.close()
            except Exception:
                pass
        resp = _parse_response(raw)
        resp.elapsed_ms = elapsed_ms

        if not follow_redirects or resp.status not in (301, 302, 303, 307, 308):
            return resp
        loc = resp.header("Location")
        if not loc or visited >= max_redirects:
            return resp
        if loc.startswith("/"):
            sp = urlsplit(current.url) if current.url else urlsplit(f"{scheme}://{host}:{port}")
            loc = f"{sp.scheme}://{sp.netloc}{loc}"
        # Build a new GET to the new location (most browsers do this for 303)
        current = HttpRequest(method="GET", url=loc, headers=current.headers)
        visited += 1


def fingerprint(url: str, *, timeout: float = 10.0,
                tls_verify: bool = True, color: bool = True) -> str:
    out = []
    methods = ["GET", "OPTIONS"]
    for m in methods:
        try:
            r = send(HttpRequest(method=m, url=url), timeout=timeout,
                     tls_verify=tls_verify, follow_redirects=False)
        except Exception as e:
            out.append(paint(f"  {m}: failed ({e})", RED, color))
            continue
        out.append(paint(f"\n── {m} {url} → {r.status} {r.reason} ({r.elapsed_ms:.0f} ms)",
                         BOLD, color))
        # Group "interesting" headers first, then the rest.
        interesting_lower = {h.lower() for h in INTERESTING_HEADERS}
        interesting = [(k, v) for k, v in r.headers if k.lower() in interesting_lower]
        other = [(k, v) for k, v in r.headers if k.lower() not in interesting_lower]
        for k, v in interesting:
            label = paint(f"{k}:", CYAN, color)
            val = v if len(v) < 200 else v[:200] + "…"
            out.append(f"    {label} {val}")
        if other:
            out.append(paint("  (other headers)", GREY, color))
            for k, v in other:
                val = v if len(v) < 200 else v[:200] + "…"
                out.append(f"    {paint(k + ':', GREY, color)} {val}")
    return "\n".join(out)


# ─── CLI ────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="Raw HTTP/1.1 client with fingerprint mode.")
    ap.add_argument("--url", required=True)
    ap.add_argument("-X", "--method", default="GET")
    ap.add_argument("-H", "--header", action="append", default=[],
                    help="header (repeatable): 'Name: value'")
    ap.add_argument("--body", help="request body (string)")
    ap.add_argument("--body-file", help="request body from file")
    ap.add_argument("--http", default="1.1", choices=["1.0", "1.1"])
    ap.add_argument("--insecure", action="store_true",
                    help="skip TLS cert verification")
    ap.add_argument("--follow", action="store_true",
                    help="follow redirects (max 5)")
    ap.add_argument("--timeout", type=float, default=10.0)
    ap.add_argument("--fingerprint", action="store_true",
                    help="GET + OPTIONS, dump all response headers categorized")
    ap.add_argument("--raw", action="store_true",
                    help="dump raw response bytes (latin-1) and exit")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    if args.fingerprint:
        print(fingerprint(args.url, timeout=args.timeout,
                          tls_verify=not args.insecure, color=color))
        return 0

    headers: list[tuple[str, str]] = []
    for h in args.header:
        if ":" in h:
            k, v = h.split(":", 1)
            headers.append((k.strip(), v.strip()))

    body = args.body
    if args.body_file:
        with open(args.body_file, "rb") as f:
            body = f.read()

    req = HttpRequest(method=args.method, url=args.url, headers=headers,
                      body=body, http_version=f"HTTP/{args.http}")
    try:
        r = send(req, timeout=args.timeout, tls_verify=not args.insecure,
                 follow_redirects=args.follow)
    except Exception as e:
        print(paint(f"[!] request failed: {e}", RED, color), file=sys.stderr)
        return 1

    if args.raw:
        sys.stdout.write(r.raw.decode("latin-1", errors="replace"))
        return 0

    if args.json:
        print(json.dumps({
            "status": r.status, "reason": r.reason, "version": r.http_version,
            "elapsed_ms": r.elapsed_ms,
            "headers": [{"name": k, "value": v} for k, v in r.headers],
            "body": r.body.decode("latin-1", errors="replace"),
        }, indent=2))
    else:
        print(paint(f"{r.http_version} {r.status} {r.reason}  ({r.elapsed_ms:.0f} ms)",
                    BOLD, color))
        for k, v in r.headers:
            print(f"{paint(k + ':', CYAN, color)} {v}")
        print()
        try:
            print(r.body.decode("utf-8"))
        except UnicodeDecodeError:
            print(r.body.decode("latin-1", errors="replace"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
