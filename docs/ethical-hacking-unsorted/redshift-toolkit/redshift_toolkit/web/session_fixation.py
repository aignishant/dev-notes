#!/usr/bin/env python3
"""
redshift_toolkit.web.session_fixation — session-fixation & rotation auditor.

Why this matters
----------------
A correctly-implemented login flow must *rotate* the session identifier when a
user authenticates. If the application keeps the same session ID across the
anonymous→authenticated boundary, an attacker who plants a known session ID in
the victim's browser (via meta-refresh, link injection, or a sub-domain XSS)
ends up sharing the victim's session post-login. This was OWASP A2 in 2007 and
2010 and still appears in the wild whenever a developer reaches for a custom
auth instead of a battle-tested framework.

What this script does
---------------------
1.  Visit a "pre-login" URL and capture session cookies (e.g. PHPSESSID,
    JSESSIONID, sessionid, ASP.NET_SessionId, connect.sid, _csrf_token).
2.  Drive a login by POSTing supplied credentials, **reusing the captured
    cookies**.
3.  Compare cookies before and after authentication. Each session cookie that
    keeps the SAME value is a finding.
4.  Optionally make an authenticated request (e.g. /me, /dashboard) using the
    PRE-login cookie set to confirm exploitability.

Usage
-----
    python3 -m redshift_toolkit.web.session_fixation \\
        --pre-url   https://app.example.com/login \\
        --login-url https://app.example.com/login \\
        --login-data "username=test&password=Test1234" \\
        --csrf-field csrf_token \\
        --csrf-cookie XSRF-TOKEN \\
        --auth-check-url https://app.example.com/api/me

Author: Redshift Project — Module 17 (Auth & AuthZ)
License: MIT — authorised testing only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

from .http_client import HttpRequest, send


GREEN, RED, YELLOW, CYAN, GREY, BOLD, RESET = (
    "\x1b[32m", "\x1b[31m", "\x1b[33m", "\x1b[36m", "\x1b[90m", "\x1b[1m", "\x1b[0m",
)


def paint(t: str, c: str, *, enabled: bool = True) -> str:
    return f"{c}{t}{RESET}" if enabled else t


# Common session-cookie name fragments
SESSION_NAME_HINTS = (
    "session", "sess", "sid", "jsessionid", "phpsessid", "asp.net_sessionid",
    "connect.sid", "express:sess", "auth", "user", "login", "token",
)


def is_session_cookie(name: str) -> bool:
    n = name.lower()
    return any(h in n for h in SESSION_NAME_HINTS)


# ---------------------------------------------------------------------------
# Cookie jar (minimal)
# ---------------------------------------------------------------------------
def parse_set_cookie_headers(headers: List[Tuple[str, str]]) -> Dict[str, str]:
    """Return {name: value} from all Set-Cookie headers."""
    jar: Dict[str, str] = {}
    for k, v in headers:
        if k.lower() != "set-cookie":
            continue
        # Just take the first 'name=value' segment
        first = v.split(";", 1)[0].strip()
        if "=" in first:
            n, val = first.split("=", 1)
            jar[n.strip()] = val.strip()
    return jar


def cookies_to_header(jar: Dict[str, str]) -> str:
    return "; ".join(f"{k}={v}" for k, v in jar.items())


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------
@dataclass
class FixationReport:
    pre_cookies: Dict[str, str] = field(default_factory=dict)
    post_cookies: Dict[str, str] = field(default_factory=dict)
    fixed_cookies: List[str] = field(default_factory=list)
    new_cookies: List[str] = field(default_factory=list)
    auth_check_status: Optional[int] = None
    auth_check_authenticated: Optional[bool] = None
    notes: List[str] = field(default_factory=list)


def extract_csrf_field(body: bytes, field_name: str) -> Optional[str]:
    """Find <input name=field_name value=...> in HTML body."""
    pat = rb'<input[^>]*name=["\']?' + re.escape(field_name.encode()) + rb'["\']?[^>]*value=["\']?([^"\'>\s]+)["\']?'
    m = re.search(pat, body, re.I)
    if m:
        return m.group(1).decode("utf-8", errors="replace")
    pat2 = rb'<input[^>]*value=["\']?([^"\'>\s]+)["\']?[^>]*name=["\']?' + re.escape(field_name.encode()) + rb'["\']?'
    m = re.search(pat2, body, re.I)
    return m.group(1).decode("utf-8", errors="replace") if m else None


def run(pre_url: str, login_url: str, login_data: str, *,
        csrf_field: Optional[str] = None,
        csrf_cookie: Optional[str] = None,
        auth_check_url: Optional[str] = None,
        auth_check_indicator: Optional[str] = None,
        timeout: float = 15.0) -> FixationReport:
    rep = FixationReport()

    # Step 1: pre-login GET
    try:
        resp = send(HttpRequest(method="GET", url=pre_url), timeout=timeout, follow_redirects=False)
        rep.pre_cookies = parse_set_cookie_headers(resp.headers)
    except Exception as e:
        rep.notes.append(f"pre-login fetch failed: {e}")
        return rep

    if not rep.pre_cookies:
        rep.notes.append("server did not set any cookies on the pre-login page")
        return rep

    # Step 2: extract CSRF from pre-login body if requested
    body_text = resp.body or b""
    csrf_value: Optional[str] = None
    if csrf_field:
        csrf_value = extract_csrf_field(body_text, csrf_field)
        if not csrf_value and csrf_cookie and csrf_cookie in rep.pre_cookies:
            csrf_value = rep.pre_cookies[csrf_cookie]
        if csrf_value:
            login_data = login_data + f"&{csrf_field}={csrf_value}"
            rep.notes.append(f"injected CSRF token into login body ({csrf_field})")
        else:
            rep.notes.append(f"could not locate CSRF field {csrf_field!r}")

    # Step 3: login POST, replaying pre-cookies
    headers = [
        ("Content-Type", "application/x-www-form-urlencoded"),
        ("Cookie", cookies_to_header(rep.pre_cookies)),
    ]
    try:
        resp2 = send(HttpRequest(method="POST", url=login_url,
                                 headers=headers, body=login_data.encode()),
                     timeout=timeout, follow_redirects=False)
    except Exception as e:
        rep.notes.append(f"login POST failed: {e}")
        return rep

    rep.post_cookies = parse_set_cookie_headers(resp2.headers)

    # Step 4: compare
    for name, val in rep.pre_cookies.items():
        if not is_session_cookie(name):
            continue
        post_val = rep.post_cookies.get(name)
        if post_val is None:
            # Cookie not re-issued; pre value will be sent on subsequent requests by the browser
            rep.fixed_cookies.append(name)
        elif post_val == val:
            rep.fixed_cookies.append(name)

    rep.new_cookies = [n for n in rep.post_cookies if n not in rep.pre_cookies]

    # Step 5: auth-check using PRE cookies
    if auth_check_url and rep.fixed_cookies:
        try:
            resp3 = send(HttpRequest(method="GET", url=auth_check_url,
                                     headers=[("Cookie", cookies_to_header(rep.pre_cookies))]),
                         timeout=timeout, follow_redirects=False)
            rep.auth_check_status = resp3.status
            body3 = (resp3.body or b"").decode("utf-8", errors="replace")
            if auth_check_indicator:
                rep.auth_check_authenticated = auth_check_indicator in body3
            else:
                # Heuristic: 200 + body looks user-specific
                rep.auth_check_authenticated = (
                    resp3.status == 200 and any(k in body3.lower()
                                                for k in ("logout", "dashboard", "welcome", "profile"))
                )
        except Exception as e:
            rep.notes.append(f"auth check failed: {e}")

    return rep


def report_text(rep: FixationReport, *, colour: bool = True) -> str:
    L: List[str] = []
    L.append(paint(f"\n[session_fixation] pre={len(rep.pre_cookies)} post={len(rep.post_cookies)}",
                   BOLD, enabled=colour))
    for n in rep.notes:
        L.append(paint(f"  * {n}", GREY, enabled=colour))
    if not rep.fixed_cookies:
        L.append(paint("  ✓ all session cookies rotate after login", GREEN, enabled=colour))
    else:
        for name in rep.fixed_cookies:
            L.append(paint(f"  ! session cookie '{name}' DID NOT rotate after login (FIXATION)",
                           RED, enabled=colour))
    if rep.new_cookies:
        L.append(paint(f"  + new cookies issued post-login: {', '.join(rep.new_cookies)}",
                       CYAN, enabled=colour))
    if rep.auth_check_authenticated is True:
        L.append(paint("  ✗ EXPLOITABLE: pre-login session ID is authenticated after login",
                       RED, enabled=colour))
    elif rep.auth_check_authenticated is False:
        L.append(paint("  ✓ pre-login session ID is NOT authenticated post-login (cookie rotation effective)",
                       GREEN, enabled=colour))
    return "\n".join(L)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="session_fixation",
                                description="Session fixation / rotation auditor.")
    p.add_argument("--pre-url", required=True)
    p.add_argument("--login-url", required=True)
    p.add_argument("--login-data", required=True,
                   help="form body (url-encoded), e.g. username=u&password=p")
    p.add_argument("--csrf-field", help="HTML input name to scrape from pre-login page")
    p.add_argument("--csrf-cookie", help="cookie name carrying CSRF token")
    p.add_argument("--auth-check-url", help="URL to test with pre-cookies after login")
    p.add_argument("--auth-check-indicator",
                   help="string in body that confirms authenticated state")
    p.add_argument("--timeout", type=float, default=15.0)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args(argv)

    rep = run(args.pre_url, args.login_url, args.login_data,
              csrf_field=args.csrf_field, csrf_cookie=args.csrf_cookie,
              auth_check_url=args.auth_check_url,
              auth_check_indicator=args.auth_check_indicator,
              timeout=args.timeout)

    if args.format == "json":
        print(json.dumps(asdict(rep), indent=2, default=str))
    else:
        print(report_text(rep, colour=not args.no_color))

    return 1 if rep.fixed_cookies else 0


if __name__ == "__main__":
    sys.exit(main())
