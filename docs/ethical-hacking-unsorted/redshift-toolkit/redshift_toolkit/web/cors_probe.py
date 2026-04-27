#!/usr/bin/env python3
"""
redshift_toolkit.web.cors_probe — CORS misconfiguration scanner.

What it tests
-------------
1. Reflected-origin: server echoes whatever Origin: was sent.
   With Allow-Credentials: true → critical (any attacker page reads responses).
2. Null-origin acceptance: Origin: null is accepted.
   Reachable from sandboxed iframes, data: URLs, and certain redirects.
3. Subdomain wildcard: server allows *.target.com — find unclaimed subdomains.
4. Suffix-match weakness: server allows target.com.evil.com.
5. Pre-domain match: server allows eviltarget.com.
6. Trusted-internal: server allows http://internal.target.local.
7. Common vendor wildcards (S3, GitHub Pages) accidentally trusted.

Usage
-----
  python3 -m redshift_toolkit.web.cors_probe --url https://api.example.com/me
  python3 -m redshift_toolkit.web.cors_probe --url https://api.example.com/me \\
      --auth-cookie 'session=...' --json

Author: Redshift Project — Module 13
License: MIT
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict, field
from urllib.parse import urlsplit

from redshift_toolkit.web.http_client import HttpRequest, send

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


@dataclass
class CorsTest:
    name: str
    origin_sent: str
    severity: str  # "critical" | "high" | "medium" | "info"
    description: str


CORS_TESTS = [
    CorsTest("Reflected origin", "https://evil.attacker.com",
             "critical",
             "Server echoes whatever Origin we send. With Credentials, "
             "any attacker page can read responses including cookies."),
    CorsTest("Null origin", "null",
             "high",
             "Origin: null is reachable from sandboxed iframes, data: URLs, "
             "and certain redirect chains."),
    CorsTest("Suffix match", "{target}.evil.com",
             "high",
             "Allow-Origin matches target.com.evil.com — attacker registers "
             "evil.com as a domain and any subdomain is trusted."),
    CorsTest("Prefix match", "evil{target}",
             "high",
             "Allow-Origin matches eviltarget.com — attacker registers a "
             "domain that contains the target as a substring."),
    CorsTest("Underscore replacement", "{scheme}://{target}_evil.com",
             "medium",
             "Some validators use regex with weak boundaries — underscore "
             "is sometimes treated as part of the domain."),
    CorsTest("Backtick injection", "{scheme}://{target}`evil.com",
             "medium",
             "Backtick is allowed in some browser URL parsers but not in regex "
             "boundary checks — exploitable in Safari/Chrome."),
    CorsTest("Empty origin", "",
             "info",
             "Some servers reflect the empty string as Allow-Origin."),
    CorsTest("Internal trusted", "http://internal.{target}",
             "medium",
             "Server trusts http:// internal subdomain — attacker takes over "
             "via subdomain takeover."),
    CorsTest("S3 wildcard", "https://s3.amazonaws.com",
             "medium",
             "Some apps trust S3 origin; attacker hosts page on S3 bucket."),
    CorsTest("Subdomain trust", "https://attacker.{target}",
             "high",
             "Server trusts any subdomain — combine with subdomain takeover."),
]


@dataclass
class Finding:
    test: str
    origin: str
    allow_origin: str | None
    allow_credentials: bool
    severity: str
    note: str = ""

    def is_vulnerable(self) -> bool:
        if not self.allow_origin:
            return False
        return self.allow_origin == self.origin or self.allow_origin == "*"


def probe(url: str, auth_cookie: str | None = None,
          tls_verify: bool = True, timeout: float = 10.0) -> list[Finding]:
    """Run CORS test suite against `url`."""
    sp = urlsplit(url)
    target_host = sp.hostname or ""
    target_no_scheme = target_host
    findings: list[Finding] = []

    headers_base = []
    if auth_cookie:
        headers_base.append(("Cookie", auth_cookie))

    for t in CORS_TESTS:
        origin = (t.origin_sent
                  .replace("{target}", target_no_scheme)
                  .replace("{scheme}", sp.scheme or "https"))
        req_headers = list(headers_base) + [("Origin", origin)]
        try:
            r = send(HttpRequest(method="GET", url=url, headers=req_headers),
                     timeout=timeout, tls_verify=tls_verify,
                     follow_redirects=False)
        except Exception as e:
            findings.append(Finding(test=t.name, origin=origin,
                                    allow_origin=None,
                                    allow_credentials=False,
                                    severity="info",
                                    note=f"request failed: {e}"))
            continue
        ao = r.header("Access-Control-Allow-Origin")
        ac = (r.header("Access-Control-Allow-Credentials") or "").lower() == "true"
        f = Finding(test=t.name, origin=origin,
                    allow_origin=ao, allow_credentials=ac,
                    severity=t.severity, note=t.description)
        findings.append(f)

    return findings


def render_text(findings: list[Finding], color: bool) -> str:
    out = [paint("\n=== CORS probe results ===", BOLD, color)]
    vuln_count = 0
    for f in findings:
        is_vuln = f.is_vulnerable()
        if is_vuln:
            vuln_count += 1
        marker = (paint("[VULN]", RED, color) if is_vuln
                  else paint("[ok  ]", GREEN, color)
                  if f.allow_origin
                  else paint("[----]", YELLOW, color))
        sev = ""
        if is_vuln:
            sev = " " + paint(f"({f.severity})", RED if f.severity == "critical" else YELLOW, color)
        creds = (paint(" + creds", RED, color)
                 if f.allow_credentials and is_vuln else "")
        out.append(f"  {marker} {f.test:<24} → "
                   f"Origin: {f.origin or '(empty)'}")
        out.append(f"           Allow-Origin: {f.allow_origin or '(none)'}{creds}{sev}")
    out.append("")
    out.append(paint(f"[{vuln_count} vulnerable test(s) of {len(findings)}]",
                     BOLD, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="CORS misconfiguration probe.")
    ap.add_argument("--url", required=True)
    ap.add_argument("--auth-cookie", help="Cookie header value to send")
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--timeout", type=float, default=10.0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    findings = probe(args.url, auth_cookie=args.auth_cookie,
                     tls_verify=not args.insecure, timeout=args.timeout)

    if args.json:
        out = []
        for f in findings:
            d = asdict(f)
            d["vulnerable"] = f.is_vulnerable()
            out.append(d)
        print(json.dumps(out, indent=2))
    else:
        print(render_text(findings, color))

    return 0 if not any(f.is_vulnerable() for f in findings) else 1


if __name__ == "__main__":
    sys.exit(main())
