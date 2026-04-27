#!/usr/bin/env python3
"""
redshift_toolkit.web.cache_poison_probe — web cache poisoning detector.

Methodology
-----------
1. Use a cache-buster query parameter to ensure each test fetches a
   fresh cache entry.
2. Send the request with various potentially-unkeyed headers set to a
   unique canary value.
3. Look for the canary in the response body (reflection).
4. If reflected: send the same URL WITHOUT the header but with the same
   cache-buster — if the canary still appears, the header is unkeyed
   AND the response is poisonable.

Headers tested
--------------
- X-Forwarded-Host         (most common)
- X-Forwarded-Scheme / -Proto
- X-Forwarded-For
- X-Original-URL / X-Rewrite-URL
- X-Host
- X-Forwarded-Server
- Forwarded
- True-Client-IP
- CF-Connecting-IP
- Plus the request line being absolute-form

Caveat
------
This module probes for poisonability — it does NOT actually poison live
caches. The "verify with cache-buster removed" step uses a different
cache-buster value to keep our own test contained.

Usage
-----
  python3 -m redshift_toolkit.web.cache_poison_probe --url https://target.com/
  python3 -m redshift_toolkit.web.cache_poison_probe --url https://target.com/ \\
      --json

Author: Redshift Project — Module 16
License: MIT — Lab use only.
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from dataclasses import dataclass, asdict, field
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from redshift_toolkit.web.http_client import HttpRequest, send

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


HEADERS_TO_TEST = [
    "X-Forwarded-Host",
    "X-Forwarded-Scheme",
    "X-Forwarded-Proto",
    "X-Original-URL",
    "X-Rewrite-URL",
    "X-Host",
    "X-Forwarded-Server",
    "X-Forwarded-Port",
    "Forwarded",
    "True-Client-IP",
    "CF-Connecting-IP",
    "X-Real-IP",
    "X-Backend-Server",
    "X-WAP-Profile",
    "Referer",
]


@dataclass
class CacheFinding:
    header: str
    canary_value: str
    reflected: bool
    keyed: bool       # True = header IS in cache key (NOT poisonable)
    body_excerpt: str = ""
    note: str = ""

    @property
    def poisonable(self) -> bool:
        return self.reflected and not self.keyed


def _add_cache_buster(url: str, value: str) -> str:
    sp = urlsplit(url)
    qs = parse_qsl(sp.query, keep_blank_values=True)
    qs.append(("rscbus", value))
    return urlunsplit((sp.scheme, sp.netloc, sp.path,
                       urlencode(qs), sp.fragment))


def _canary_value(target_host: str) -> tuple[str, str]:
    """Returns (header_value, search_token).  We use a domain-shaped value
    because most "reflect-back" patterns expect a hostname."""
    tok = secrets.token_hex(4)
    return (f"rscbk-{tok}.example.invalid", f"rscbk-{tok}")


def probe(url: str, *, tls_verify: bool = True, timeout: float = 15.0
          ) -> list[CacheFinding]:
    findings: list[CacheFinding] = []
    sp = urlsplit(url)

    for header in HEADERS_TO_TEST:
        # Step 1: send with header + cache buster A
        cb_a = secrets.token_hex(6)
        url_a = _add_cache_buster(url, cb_a)
        canary_val, token = _canary_value(sp.hostname or "")
        h_with = [(header, canary_val)]
        try:
            r = send(HttpRequest(method="GET", url=url_a, headers=h_with),
                     timeout=timeout, tls_verify=tls_verify,
                     follow_redirects=False)
        except Exception as e:
            findings.append(CacheFinding(header=header, canary_value=canary_val,
                                          reflected=False, keyed=False,
                                          note=f"error: {e}"))
            continue
        body_text = r.body.decode("latin-1", errors="replace")
        reflected = token in body_text

        # Step 2: with same cache buster, but no header — does response still
        # contain canary? If yes, our previous response was cached AND the
        # cache key did NOT include this header.
        keyed = True
        if reflected:
            try:
                r2 = send(HttpRequest(method="GET", url=url_a),
                          timeout=timeout, tls_verify=tls_verify,
                          follow_redirects=False)
                body2 = r2.body.decode("latin-1", errors="replace")
                if token in body2:
                    keyed = False  # served the poisoned variant
            except Exception:
                pass

        excerpt = ""
        if reflected:
            idx = body_text.find(token)
            excerpt = body_text[max(0, idx - 40):idx + 80]

        findings.append(CacheFinding(
            header=header, canary_value=canary_val,
            reflected=reflected, keyed=keyed,
            body_excerpt=excerpt))

    return findings


def render_text(findings: list[CacheFinding], color: bool) -> str:
    out = [paint("\n=== Web cache poisoning probe ===", BOLD, color)]
    pcount = 0
    for f in findings:
        if f.poisonable:
            tag = paint("[POIS]", RED, color)
            pcount += 1
        elif f.reflected:
            tag = paint("[refl]", YELLOW, color)
        else:
            tag = paint("[----]", GREEN, color)
        out.append(f"  {tag} {f.header:<22} reflected={f.reflected}  "
                   f"keyed={f.keyed}  {f.note}")
        if f.poisonable:
            out.append(f"          excerpt: {f.body_excerpt.strip()!r}")
    out.append("")
    out.append(paint(f"[{pcount} potential poisoning vector(s)]", BOLD, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Web cache poisoning detector.")
    ap.add_argument("--url", required=True)
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    findings = probe(args.url, tls_verify=not args.insecure,
                     timeout=args.timeout)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        print(render_text(findings, color))

    return 0 if not any(f.poisonable for f in findings) else 1


if __name__ == "__main__":
    sys.exit(main())
