#!/usr/bin/env python3
"""
redshift_toolkit.web.cookie_analyzer — audit Set-Cookie security flags.

Each cookie set by a target is scored against:
  - Secure
  - HttpOnly
  - SameSite (Lax | Strict | None)
  - Domain scope
  - Path scope
  - __Host- / __Secure- prefix
  - Max-Age / Expires presence
  - Cookie name patterns suggesting framework (PHPSESSID, JSESSIONID, etc.)

Scoring
-------
- Critical: missing Secure on HTTPS site
- Critical: missing HttpOnly on session cookie
- High:    SameSite=None without Secure
- High:    no SameSite, no equivalent CSRF protection visible
- Medium:  Domain=. (broad scope) without explicit need
- Medium:  extremely long Max-Age (> 1 year for session)
- Info:    framework leak via cookie name

Usage
-----
  python3 -m redshift_toolkit.web.cookie_analyzer --url https://example.com/
  python3 -m redshift_toolkit.web.cookie_analyzer --url https://example.com/ --json

Author: Redshift Project — Module 13
License: MIT
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict, field
from urllib.parse import urlsplit

from redshift_toolkit.web.http_client import HttpRequest, send

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


# Heuristics for "looks like a session cookie"
SESSION_NAME_PATTERNS = [
    re.compile(r"sess", re.I),
    re.compile(r"sid", re.I),
    re.compile(r"^auth", re.I),
    re.compile(r"token", re.I),
    re.compile(r"^jwt", re.I),
    re.compile(r"^connect\.sid$", re.I),    # Express
    re.compile(r"^laravel_session$", re.I),
    re.compile(r"^_session_id$", re.I),     # Rails
    re.compile(r"^csrftoken$", re.I),
]

# Framework leak patterns
FRAMEWORK_HINTS = {
    "PHPSESSID": "PHP",
    "JSESSIONID": "Java (Tomcat/Jetty/etc.)",
    "ASP.NET_SessionId": ".NET",
    "ASPSESSIONID": "Classic ASP",
    "ASPXAUTH": ".NET Forms Auth",
    "CFID": "ColdFusion",
    "CFTOKEN": "ColdFusion",
    "connect.sid": "Express.js",
    "laravel_session": "Laravel",
    "_session_id": "Rails",
    "csrftoken": "Django (csrftoken)",
    "sessionid": "Django (sessionid)",
    "wordpress_": "WordPress (logged-in)",
    "wp-settings-": "WordPress",
    "ci_session": "CodeIgniter",
    "yii_": "Yii",
    "frontend_lang": "Magento",
}


@dataclass
class CookieParsed:
    name: str
    value: str
    domain: str | None = None
    path: str | None = None
    expires: str | None = None
    max_age: int | None = None
    secure: bool = False
    http_only: bool = False
    same_site: str | None = None
    raw: str = ""


@dataclass
class CookieFinding:
    cookie: str
    severity: str
    issue: str


def parse_set_cookie(line: str) -> CookieParsed:
    parts = [p.strip() for p in line.split(";")]
    nv = parts[0]
    if "=" in nv:
        name, value = nv.split("=", 1)
    else:
        name, value = nv, ""
    c = CookieParsed(name=name.strip(), value=value.strip(), raw=line)
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            kl = k.strip().lower()
            vl = v.strip()
            if kl == "domain":
                c.domain = vl
            elif kl == "path":
                c.path = vl
            elif kl == "expires":
                c.expires = vl
            elif kl == "max-age":
                try:
                    c.max_age = int(vl)
                except ValueError:
                    pass
            elif kl == "samesite":
                c.same_site = vl
        else:
            kl = p.strip().lower()
            if kl == "secure":
                c.secure = True
            elif kl == "httponly":
                c.http_only = True
            elif kl == "samesite":
                c.same_site = ""
    return c


def looks_like_session(name: str) -> bool:
    return any(p.search(name) for p in SESSION_NAME_PATTERNS)


def framework_hint(name: str) -> str | None:
    for prefix, fw in FRAMEWORK_HINTS.items():
        if name == prefix or name.startswith(prefix.rstrip("_") + "_") \
           or name.lower() == prefix.lower():
            return fw
    return None


def audit(cookies: list[CookieParsed], over_https: bool) -> list[CookieFinding]:
    findings: list[CookieFinding] = []
    for c in cookies:
        is_session = looks_like_session(c.name)

        if over_https and not c.secure:
            findings.append(CookieFinding(
                cookie=c.name,
                severity="critical" if is_session else "high",
                issue="missing Secure flag on HTTPS — cookie can leak over plaintext"))

        if is_session and not c.http_only:
            findings.append(CookieFinding(
                cookie=c.name, severity="critical",
                issue="session cookie missing HttpOnly — XSS = full session theft"))

        if not c.same_site:
            findings.append(CookieFinding(
                cookie=c.name,
                severity="high" if is_session else "medium",
                issue="missing SameSite — CSRF risk; default browser handling varies"))
        elif c.same_site.lower() == "none" and not c.secure:
            findings.append(CookieFinding(
                cookie=c.name, severity="high",
                issue="SameSite=None without Secure — modern browsers reject; "
                      "indicates broken intent"))

        if c.domain and c.domain.startswith("."):
            findings.append(CookieFinding(
                cookie=c.name, severity="medium",
                issue=f"Domain={c.domain} — shared with subdomains, expanding "
                      f"XSS blast radius"))

        if c.max_age and c.max_age > 365 * 24 * 3600 and is_session:
            findings.append(CookieFinding(
                cookie=c.name, severity="medium",
                issue=f"Max-Age={c.max_age}s (>1 year) on session cookie"))

        if c.name.startswith("__Host-"):
            ok = c.secure and (c.path == "/") and not c.domain
            if not ok:
                findings.append(CookieFinding(
                    cookie=c.name, severity="info",
                    issue="__Host- prefix requires Secure + Path=/ + no Domain"))
        elif c.name.startswith("__Secure-") and not c.secure:
            findings.append(CookieFinding(
                cookie=c.name, severity="info",
                issue="__Secure- prefix requires Secure"))

        fh = framework_hint(c.name)
        if fh:
            findings.append(CookieFinding(
                cookie=c.name, severity="info",
                issue=f"cookie name discloses framework: {fh}"))

    return findings


def fetch_cookies(url: str, tls_verify: bool = True,
                  timeout: float = 10.0) -> tuple[list[CookieParsed], bool]:
    """Fetch URL and return all cookies set by the response."""
    r = send(HttpRequest(method="GET", url=url),
             timeout=timeout, tls_verify=tls_verify, follow_redirects=False)
    cookies: list[CookieParsed] = []
    for k, v in r.headers:
        if k.lower() == "set-cookie":
            cookies.append(parse_set_cookie(v))
    over_https = urlsplit(url).scheme.lower() == "https"
    return cookies, over_https


def render_text(cookies: list[CookieParsed], findings: list[CookieFinding],
                color: bool) -> str:
    out = [paint("\n=== Cookie audit ===", BOLD, color)]
    if not cookies:
        out.append(paint("  no cookies set in the response", GREY, color))
        return "\n".join(out)
    for c in cookies:
        flags = []
        flags.append(paint("Secure", GREEN, color) if c.secure
                     else paint("!Secure", RED, color))
        flags.append(paint("HttpOnly", GREEN, color) if c.http_only
                     else paint("!HttpOnly", RED, color))
        ss = c.same_site or "none"
        ss_color = GREEN if ss.lower() in ("strict", "lax") else YELLOW
        flags.append(paint(f"SameSite={ss}", ss_color, color))
        out.append(f"  ── {paint(c.name, BOLD, color)}")
        out.append(f"      flags: {' '.join(flags)}")
        if c.domain:
            out.append(f"      domain: {c.domain}")
        if c.path:
            out.append(f"      path:   {c.path}")
        if c.max_age is not None:
            out.append(f"      max-age: {c.max_age}s")

    sev_color = {"critical": RED, "high": RED, "medium": YELLOW, "info": GREY}
    if findings:
        out.append(paint(f"\n  Findings ({len(findings)}):", BOLD, color))
        for f in findings:
            out.append(f"    [{paint(f.severity, sev_color.get(f.severity, GREY), color)}] "
                       f"{f.cookie}: {f.issue}")
    else:
        out.append(paint("\n  No issues found.", GREEN, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit Set-Cookie security flags.")
    ap.add_argument("--url", required=True)
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--timeout", type=float, default=10.0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    cookies, over_https = fetch_cookies(args.url,
                                         tls_verify=not args.insecure,
                                         timeout=args.timeout)
    findings = audit(cookies, over_https)

    if args.json:
        print(json.dumps({
            "over_https": over_https,
            "cookies": [asdict(c) for c in cookies],
            "findings": [asdict(f) for f in findings],
        }, indent=2))
    else:
        print(render_text(cookies, findings, color))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
