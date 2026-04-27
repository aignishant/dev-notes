#!/usr/bin/env python3
"""
redshift_toolkit.web.cache_deception — cache deception detector.

Methodology (Omer Gil's pattern)
--------------------------------
1. Authenticate to the target with the supplied cookie/token.
2. Fetch /api/profile/cat.jpg (or other dynamic-endpoint + static-extension
   combos). Many routers map this to /api/profile (dynamic), but the cache
   sees `.jpg` and decides to cache the response.
3. Forget your auth (or use a different session). Fetch the same URL.
4. If the response still contains data that looks user-specific (matches
   from the authenticated response), the cache served a static copy of
   the authenticated user's response — that's cache deception.

Static extensions tested (most common to most exotic):
  .jpg .png .gif .ico .svg .css .js .woff .woff2 .pdf
  .html .txt .xml .json .map

Plus path-based variations:
  /static/<dynamic-path>
  /<dynamic-path>;.jpg     ← path parameter trick

Usage
-----
  python3 -m redshift_toolkit.web.cache_deception \\
      --url https://app.example.com/api/profile \\
      --auth-cookie 'session=abc' \\
      --identity-marker '"email":"alice@example.com"'

Author: Redshift Project — Module 16
License: MIT — Lab use only.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, asdict, field

from redshift_toolkit.web.http_client import HttpRequest, send

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


STATIC_EXTENSIONS = [".jpg", ".png", ".gif", ".ico", ".svg", ".css", ".js",
                     ".woff", ".woff2", ".pdf", ".html", ".txt", ".xml",
                     ".json", ".map"]

PATH_TEMPLATES = [
    "{base}/cat{ext}",
    "{base}{ext}",
    "{base};name=cat{ext}",
    "{base}/cat{ext};name=cat",
    "{base}%2Fcat{ext}",
    "{base}/..%2fcat{ext}",
    "{base}/cat{ext}?cb=1",
]


@dataclass
class DeceptionFinding:
    url: str
    auth_status: int
    auth_body_len: int
    auth_marker_present: bool
    unauth_status: int
    unauth_body_len: int
    unauth_marker_present: bool
    cache_status_header: str | None = None
    is_deception: bool = False


def probe(base_url: str, auth_headers: list[tuple[str, str]],
          identity_marker: str, *,
          tls_verify: bool = True, timeout: float = 15.0,
          unauth_delay_s: float = 1.0) -> list[DeceptionFinding]:
    findings: list[DeceptionFinding] = []

    candidates = []
    for tmpl in PATH_TEMPLATES:
        for ext in STATIC_EXTENSIONS:
            candidates.append(tmpl.format(base=base_url, ext=ext))
    candidates = list(dict.fromkeys(candidates))  # de-dupe preserve order

    for url in candidates:
        try:
            r_a = send(HttpRequest(method="GET", url=url, headers=auth_headers),
                       timeout=timeout, tls_verify=tls_verify,
                       follow_redirects=False)
        except Exception:
            continue
        body_a = r_a.body.decode("latin-1", errors="replace")
        marker_a = identity_marker in body_a

        # Sleep briefly to allow CDN to register and cache.
        time.sleep(unauth_delay_s)

        try:
            r_u = send(HttpRequest(method="GET", url=url),
                       timeout=timeout, tls_verify=tls_verify,
                       follow_redirects=False)
        except Exception:
            continue
        body_u = r_u.body.decode("latin-1", errors="replace")
        marker_u = identity_marker in body_u

        cache_hdr = (r_u.header("X-Cache") or r_u.header("CF-Cache-Status")
                     or r_u.header("X-Cache-Hits") or r_u.header("Age"))

        deception = marker_a and marker_u and r_u.status == 200

        findings.append(DeceptionFinding(
            url=url, auth_status=r_a.status, auth_body_len=len(r_a.body),
            auth_marker_present=marker_a,
            unauth_status=r_u.status, unauth_body_len=len(r_u.body),
            unauth_marker_present=marker_u,
            cache_status_header=cache_hdr,
            is_deception=deception))
    return findings


def render_text(findings: list[DeceptionFinding], color: bool) -> str:
    out = [paint("\n=== Cache deception probe ===", BOLD, color)]
    if not findings:
        out.append("  no candidates tested.")
        return "\n".join(out)
    hit_count = 0
    for f in findings:
        if f.is_deception:
            tag = paint("[VULN]", RED, color)
            hit_count += 1
        elif f.auth_marker_present and f.unauth_status == 200:
            tag = paint("[susp]", YELLOW, color)
        else:
            tag = paint("[----]", GREEN, color)
        cache = f"  cache={f.cache_status_header}" if f.cache_status_header else ""
        out.append(f"  {tag} {f.url}")
        out.append(f"        auth: {f.auth_status} ({f.auth_body_len}b, "
                    f"marker={'Y' if f.auth_marker_present else 'N'})  "
                    f"unauth: {f.unauth_status} ({f.unauth_body_len}b, "
                    f"marker={'Y' if f.unauth_marker_present else 'N'}){cache}")
    out.append("")
    out.append(paint(f"[{hit_count} deception hit(s)]", BOLD, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Web cache deception detector.")
    ap.add_argument("--url", required=True,
                    help="dynamic endpoint URL, e.g. https://app/api/profile")
    ap.add_argument("--auth-cookie", help="Cookie header value (authenticated)")
    ap.add_argument("--bearer", help="bearer token")
    ap.add_argument("-H", "--header", action="append", default=[])
    ap.add_argument("--identity-marker", required=True,
                    help="distinct string from authenticated response (e.g. user email)")
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--unauth-delay", type=float, default=1.0,
                    help="seconds between auth+unauth requests (cache settle)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    auth = []
    if args.auth_cookie:
        auth.append(("Cookie", args.auth_cookie))
    if args.bearer:
        auth.append(("Authorization", f"Bearer {args.bearer}"))
    for h in args.header:
        if ":" in h:
            k, v = h.split(":", 1)
            auth.append((k.strip(), v.strip()))

    findings = probe(args.url, auth, args.identity_marker,
                     tls_verify=not args.insecure, timeout=args.timeout,
                     unauth_delay_s=args.unauth_delay)
    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        print(render_text(findings, color))
    return 0 if not any(f.is_deception for f in findings) else 1


if __name__ == "__main__":
    sys.exit(main())
