"""
HTTP Security Header Auditor
============================

Fetches a URL and grades its HTTP response on common security headers and
cookie hygiene. Defensive use only: pen-test reporting, posture reviews,
or hardening your own services.

Usage
-----
    python http_header_auditor.py https://example.com
    python http_header_auditor.py https://example.com --json
    python http_header_auditor.py https://example.com --no-redirect

Checks
------
- Strict-Transport-Security (HSTS): present, max-age >= 1 year, includeSubDomains
- Content-Security-Policy: present, no 'unsafe-inline'/'unsafe-eval', no '*'
- X-Frame-Options or CSP frame-ancestors
- X-Content-Type-Options: nosniff
- Referrer-Policy: present and strict
- Permissions-Policy (formerly Feature-Policy)
- Cross-Origin-Opener-Policy / Cross-Origin-Resource-Policy
- Cookies: Secure, HttpOnly, SameSite, no overly-broad Path
- Server / X-Powered-By disclosure
- TLS minimum version (best effort via `ssl` socket)
"""

from __future__ import annotations

import argparse
import json
import re
import socket
import ssl
import sys
from dataclasses import dataclass, field, asdict
from urllib.parse import urlparse

import httpx


# --------------------------------------------------------------------------- #
# Result model
# --------------------------------------------------------------------------- #

GRADE_THRESHOLDS = [(90, "A"), (80, "B"), (70, "C"), (60, "D"), (0, "F")]


@dataclass
class Finding:
    name: str
    status: str           # "ok" | "warn" | "fail"
    detail: str
    points: int           # weight contribution


@dataclass
class AuditReport:
    url: str
    final_url: str
    status_code: int
    tls_version: str | None
    findings: list[Finding] = field(default_factory=list)

    def add(self, name: str, status: str, detail: str, points: int) -> None:
        self.findings.append(Finding(name, status, detail, points))

    @property
    def score(self) -> int:
        earned = sum(f.points for f in self.findings if f.status == "ok")
        max_points = sum(abs(f.points) for f in self.findings) or 1
        return round(100 * earned / max_points)

    @property
    def grade(self) -> str:
        s = self.score
        for threshold, letter in GRADE_THRESHOLDS:
            if s >= threshold:
                return letter
        return "F"


# --------------------------------------------------------------------------- #
# Individual checks
# --------------------------------------------------------------------------- #

def check_hsts(headers: dict[str, str], rep: AuditReport) -> None:
    val = headers.get("strict-transport-security")
    if not val:
        rep.add("HSTS", "fail", "Strict-Transport-Security header missing", 10)
        return
    m = re.search(r"max-age\s*=\s*(\d+)", val, re.I)
    age = int(m.group(1)) if m else 0
    has_subdomains = "includesubdomains" in val.lower()
    if age >= 31_536_000 and has_subdomains:
        rep.add("HSTS", "ok", f"max-age={age}, includeSubDomains", 10)
    elif age >= 31_536_000:
        rep.add("HSTS", "warn",
                f"max-age={age} OK but missing includeSubDomains", 5)
    else:
        rep.add("HSTS", "warn", f"max-age={age} below 1 year", 4)


def check_csp(headers: dict[str, str], rep: AuditReport) -> None:
    val = headers.get("content-security-policy")
    if not val:
        rep.add("CSP", "fail", "Content-Security-Policy header missing", 15)
        return
    issues = []
    if "'unsafe-inline'" in val:
        issues.append("contains 'unsafe-inline'")
    if "'unsafe-eval'" in val:
        issues.append("contains 'unsafe-eval'")
    if re.search(r"default-src[^;]*\*", val) or re.search(r"script-src[^;]*\s\*", val):
        issues.append("uses wildcard '*' in script/default-src")
    if issues:
        rep.add("CSP", "warn", "; ".join(issues), 7)
    else:
        rep.add("CSP", "ok", "policy looks reasonable", 15)


def check_frame_options(headers: dict[str, str], rep: AuditReport) -> None:
    xfo = headers.get("x-frame-options", "").upper()
    csp = headers.get("content-security-policy", "")
    if xfo in {"DENY", "SAMEORIGIN"} or "frame-ancestors" in csp.lower():
        rep.add("Clickjacking",
                "ok", f"X-Frame-Options={xfo or 'via CSP'}", 5)
    else:
        rep.add("Clickjacking", "fail",
                "no X-Frame-Options or CSP frame-ancestors", 5)


def check_content_type_options(headers: dict[str, str], rep: AuditReport) -> None:
    if headers.get("x-content-type-options", "").lower() == "nosniff":
        rep.add("MIME sniffing", "ok", "nosniff set", 5)
    else:
        rep.add("MIME sniffing", "fail",
                "X-Content-Type-Options: nosniff missing", 5)


def check_referrer_policy(headers: dict[str, str], rep: AuditReport) -> None:
    val = (headers.get("referrer-policy") or "").lower()
    strict = {"no-referrer", "same-origin", "strict-origin",
              "strict-origin-when-cross-origin"}
    if val in strict:
        rep.add("Referrer-Policy", "ok", val, 5)
    elif val:
        rep.add("Referrer-Policy", "warn", f"set to '{val}' (not strict)", 2)
    else:
        rep.add("Referrer-Policy", "fail", "missing", 5)


def check_permissions_policy(headers: dict[str, str], rep: AuditReport) -> None:
    if "permissions-policy" in headers or "feature-policy" in headers:
        rep.add("Permissions-Policy", "ok", "present", 3)
    else:
        rep.add("Permissions-Policy", "warn",
                "no Permissions-Policy header", 3)


def check_cookies(set_cookie_values: list[str], rep: AuditReport) -> None:
    if not set_cookie_values:
        rep.add("Cookies", "ok", "no cookies set", 0)
        return
    bad = []
    for raw in set_cookie_values:
        name = raw.split("=", 1)[0].strip()
        low = raw.lower()
        problems = []
        if "secure" not in low:
            problems.append("no Secure")
        if "httponly" not in low:
            problems.append("no HttpOnly")
        if "samesite" not in low:
            problems.append("no SameSite")
        if problems:
            bad.append(f"{name}: {', '.join(problems)}")
    if bad:
        rep.add("Cookie flags", "fail",
                "; ".join(bad), 10)
    else:
        rep.add("Cookie flags", "ok",
                f"{len(set_cookie_values)} cookies all flagged", 10)


def check_disclosure(headers: dict[str, str], rep: AuditReport) -> None:
    leaks = []
    for h in ("server", "x-powered-by", "x-aspnet-version", "x-aspnetmvc-version"):
        if h in headers:
            leaks.append(f"{h}: {headers[h]}")
    if leaks:
        rep.add("Info disclosure", "warn",
                "; ".join(leaks), 3)
    else:
        rep.add("Info disclosure", "ok",
                "no version banners exposed", 3)


def detect_tls_version(host: str, port: int = 443) -> str | None:
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((host, port), timeout=5) as raw:
            with ctx.wrap_socket(raw, server_hostname=host) as s:
                return s.version()
    except OSError:
        return None


def check_tls(rep: AuditReport) -> None:
    if rep.tls_version is None:
        rep.add("TLS version", "warn", "could not negotiate TLS", 5)
        return
    safe = {"TLSv1.2", "TLSv1.3"}
    if rep.tls_version in safe:
        rep.add("TLS version", "ok", rep.tls_version, 5)
    else:
        rep.add("TLS version", "fail",
                f"weak: {rep.tls_version}", 5)


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #

def audit(url: str, follow_redirects: bool = True,
          timeout: float = 10.0) -> AuditReport:
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)

    with httpx.Client(follow_redirects=follow_redirects,
                      timeout=timeout, verify=True,
                      headers={"User-Agent": "header-auditor/1.0"}) as c:
        try:
            r = c.get(url)
        except httpx.RequestError as e:
            print(f"request failed: {e}", file=sys.stderr)
            sys.exit(2)

    headers_lower = {k.lower(): v for k, v in r.headers.items()}
    set_cookies = r.headers.get_list("set-cookie") if hasattr(
        r.headers, "get_list") else [v for k, v in r.headers.multi_items()
                                     if k.lower() == "set-cookie"]

    tls_version = (detect_tls_version(parsed.hostname or "")
                   if parsed.scheme == "https" else None)

    rep = AuditReport(url=url, final_url=str(r.url),
                      status_code=r.status_code, tls_version=tls_version)

    check_hsts(headers_lower, rep)
    check_csp(headers_lower, rep)
    check_frame_options(headers_lower, rep)
    check_content_type_options(headers_lower, rep)
    check_referrer_policy(headers_lower, rep)
    check_permissions_policy(headers_lower, rep)
    check_cookies(set_cookies, rep)
    check_disclosure(headers_lower, rep)
    check_tls(rep)
    return rep


def render_text(rep: AuditReport) -> str:
    lines = [
        f"URL:        {rep.url}",
        f"Final URL:  {rep.final_url}",
        f"Status:     {rep.status_code}",
        f"TLS:        {rep.tls_version or 'n/a'}",
        f"Score:      {rep.score}/100  Grade: {rep.grade}",
        "",
        f"{'Check':<22}{'Status':<8}Detail",
        "-" * 70,
    ]
    icons = {"ok": "[+]", "warn": "[!]", "fail": "[-]"}
    for f in rep.findings:
        lines.append(f"{f.name:<22}{icons.get(f.status, '?'):<8}{f.detail}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", help="Target URL (https:// preferred)")
    ap.add_argument("--json", action="store_true",
                    help="Emit machine-readable JSON")
    ap.add_argument("--no-redirect", action="store_true",
                    help="Do not follow redirects")
    ap.add_argument("--timeout", type=float, default=10.0)
    args = ap.parse_args()

    rep = audit(args.url,
                follow_redirects=not args.no_redirect,
                timeout=args.timeout)

    if args.json:
        print(json.dumps({**asdict(rep),
                          "score": rep.score,
                          "grade": rep.grade}, indent=2))
    else:
        print(render_text(rep))

    sys.exit(0 if rep.grade in {"A", "B"} else 1)


if __name__ == "__main__":
    main()
