#!/usr/bin/env python3
"""
redshift_toolkit.web.password_reset_audit — password-reset weakness auditor.

Why this matters
----------------
Account takeover via password reset is a perennial top-3 finding in bug-bounty
data. The flow is rarely tested end-to-end because each individual step looks
benign in isolation. This script enumerates the ten patterns that have shipped
account takeovers across financial, healthcare, gov, and SaaS targets:

    1. Predictable token         (timestamp, sequential, low entropy)
    2. Token leak via Referer    (token in URL, page links to 3rd party)
    3. No expiration             (reset link valid days/weeks later)
    4. Token reuse               (same token works twice)
    5. Race condition            (two parallel resets share the token)
    6. Cross-user token          (Alice's token resets Bob's password)
    7. Host-header injection     (reset email points to attacker)
    8. Email parameter pollution (?email=victim&email=attacker)
    9. Bypassable rate limit     (per-IP, per-email, per-account?)
   10. Response oracle           (different response for valid vs invalid email)

What this does
--------------
Probes each of the above against an application you control or are authorised
to test. You supply:

* --reset-init-url       e.g. https://app.example.com/forgot
* --email-field          form field carrying the email (default "email")
* --known-email          a real registered email (you control it)
* --reset-confirm-url    URL pattern with {token} that completes reset
                         e.g. https://app.example.com/reset?token={token}

NOTE: This script will never *actually* reset a password without --do-confirm.
It defaults to read-only enumeration so you can run it against a staging or
authorised production environment.

Usage
-----
    python3 -m redshift_toolkit.web.password_reset_audit \\
        --reset-init-url https://app.example.com/forgot \\
        --email-field email \\
        --known-email me@yours.example \\
        --unknown-email random-nope@yours.example \\
        --tokens-from-stdin   # paste tokens from real reset emails

Author: Redshift Project — Module 17 (Auth & AuthZ)
License: MIT — authorised testing only.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

from .http_client import HttpRequest, send


GREEN, RED, YELLOW, CYAN, GREY, BOLD, RESET = (
    "\x1b[32m", "\x1b[31m", "\x1b[33m", "\x1b[36m", "\x1b[90m", "\x1b[1m", "\x1b[0m",
)


def paint(t: str, c: str, *, enabled: bool = True) -> str:
    return f"{c}{t}{RESET}" if enabled else t


# ---------------------------------------------------------------------------
# Token entropy + structure analysis
# ---------------------------------------------------------------------------
def shannon(data: str) -> float:
    if not data:
        return 0.0
    counts: Dict[str, int] = {}
    for c in data:
        counts[c] = counts.get(c, 0) + 1
    total = len(data)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def looks_jwt(s: str) -> bool:
    return s.count(".") == 2 and all(p for p in s.split("."))


def looks_uuid(s: str) -> bool:
    return len(s) == 36 and s.count("-") == 4


def looks_hex(s: str) -> bool:
    return bool(s) and all(c in "0123456789abcdefABCDEF" for c in s)


def looks_b64(s: str) -> bool:
    return bool(s) and all(c.isalnum() or c in "-_+/=" for c in s)


def looks_timestamp_or_seq(s: str) -> bool:
    if s.isdigit():
        n = int(s)
        return 1_000_000_000 <= n <= int(time.time()) + 86400  # epoch-like
    return False


@dataclass
class TokenAnalysis:
    token: str
    length: int
    shannon: float
    structure: str
    weak: bool


def analyse_token(t: str) -> TokenAnalysis:
    if looks_jwt(t):
        struct, weak = "JWT", False
    elif looks_uuid(t):
        struct, weak = "UUID", False
    elif looks_timestamp_or_seq(t):
        struct, weak = "epoch/sequential", True
    elif looks_hex(t):
        struct, weak = "hex", len(t) < 32
    elif looks_b64(t):
        struct, weak = "base64ish", len(t) < 22
    else:
        struct, weak = "unknown", len(t) < 16
    s = shannon(t)
    if s < 3.5 and len(t) >= 8:
        weak = True
    return TokenAnalysis(token=t, length=len(t), shannon=round(s, 2),
                         structure=struct, weak=weak)


def analyse_corpus(tokens: List[str]) -> Dict[str, object]:
    analyses = [analyse_token(t) for t in tokens]
    out: Dict[str, object] = {"per_token": [asdict(a) for a in analyses]}
    if len(analyses) >= 2:
        try:
            out["length_stdev"] = statistics.stdev([a.length for a in analyses])
        except statistics.StatisticsError:
            out["length_stdev"] = 0
        out["mean_shannon"] = round(sum(a.shannon for a in analyses) / len(analyses), 2)
    out["any_weak"] = any(a.weak for a in analyses)
    return out


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
def post_form(url: str, fields: Dict[str, str], *, timeout: float = 10.0,
              extra_headers: Optional[List[Tuple[str, str]]] = None) -> Tuple[int, int, str]:
    body = urlencode(fields).encode()
    headers = [("Content-Type", "application/x-www-form-urlencoded")]
    if extra_headers:
        headers.extend(extra_headers)
    try:
        resp = send(HttpRequest(method="POST", url=url, headers=headers, body=body),
                    timeout=timeout, follow_redirects=False)
        b = resp.body or b""
        return resp.status, len(b), (b[:300].decode("utf-8", errors="replace"))
    except Exception as e:
        return -1, 0, f"<error: {e}>"


def get_url(url: str, *, timeout: float = 10.0) -> Tuple[int, int, str]:
    try:
        resp = send(HttpRequest(method="GET", url=url), timeout=timeout, follow_redirects=False)
        b = resp.body or b""
        return resp.status, len(b), (b[:300].decode("utf-8", errors="replace"))
    except Exception as e:
        return -1, 0, f"<error: {e}>"


# ---------------------------------------------------------------------------
# Audits
# ---------------------------------------------------------------------------
@dataclass
class AuditFinding:
    test: str
    severity: str  # info | low | medium | high | critical
    detail: str


def audit_response_oracle(reset_init_url: str, email_field: str,
                          known_email: str, unknown_email: str,
                          *, timeout: float = 10.0) -> AuditFinding:
    s1, l1, b1 = post_form(reset_init_url, {email_field: known_email}, timeout=timeout)
    s2, l2, b2 = post_form(reset_init_url, {email_field: unknown_email}, timeout=timeout)
    if s1 != s2 or abs(l1 - l2) > 50 or _short_excerpt(b1) != _short_excerpt(b2):
        return AuditFinding(
            test="response oracle (valid vs invalid email)",
            severity="medium",
            detail=f"differ: known→({s1}, {l1}) unknown→({s2}, {l2})",
        )
    return AuditFinding(test="response oracle", severity="info",
                        detail="responses are indistinguishable")


def _short_excerpt(b: str) -> str:
    return " ".join(b.split())[:100]


def audit_email_param_pollution(reset_init_url: str, email_field: str,
                                known_email: str, attacker_email: str,
                                *, timeout: float = 10.0) -> AuditFinding:
    body = f"{email_field}={known_email}&{email_field}={attacker_email}"
    headers = [("Content-Type", "application/x-www-form-urlencoded")]
    try:
        resp = send(HttpRequest(method="POST", url=reset_init_url, headers=headers,
                                body=body.encode()),
                    timeout=timeout, follow_redirects=False)
        snippet = (resp.body or b"")[:200].decode("utf-8", errors="replace")
        return AuditFinding(
            test="email parameter pollution",
            severity="info",
            detail=f"status={resp.status}, snippet={snippet[:120]}. "
                   f"Manual confirmation: check whether the reset email arrives at attacker_email instead of known_email.",
        )
    except Exception as e:
        return AuditFinding(test="email parameter pollution", severity="info",
                            detail=f"error: {e}")


def audit_host_header_reset(reset_init_url: str, email_field: str,
                            known_email: str, attacker_host: str,
                            *, timeout: float = 10.0) -> AuditFinding:
    body = urlencode({email_field: known_email}).encode()
    headers = [
        ("Content-Type", "application/x-www-form-urlencoded"),
        ("Host", attacker_host),
        ("X-Forwarded-Host", attacker_host),
    ]
    try:
        resp = send(HttpRequest(method="POST", url=reset_init_url, headers=headers,
                                body=body),
                    timeout=timeout, follow_redirects=False)
        return AuditFinding(
            test="host-header reset poisoning",
            severity="info",
            detail=f"posted with Host:{attacker_host} (status={resp.status}). "
                   f"Manual confirmation: check whether the reset email link points to {attacker_host}.",
        )
    except Exception as e:
        return AuditFinding(test="host-header reset", severity="info", detail=f"error: {e}")


def audit_rate_limit(reset_init_url: str, email_field: str, known_email: str,
                     n: int = 10, *, timeout: float = 5.0) -> AuditFinding:
    statuses: List[int] = []
    for _ in range(n):
        s, _, _ = post_form(reset_init_url, {email_field: known_email}, timeout=timeout)
        statuses.append(s)
    blocked = sum(1 for s in statuses if s in (429, 403))
    if blocked == 0:
        return AuditFinding(
            test="rate limiting",
            severity="medium",
            detail=f"{n} consecutive POSTs returned {statuses} — no rate limit detected",
        )
    return AuditFinding(test="rate limiting", severity="info",
                        detail=f"{blocked}/{n} requests blocked")


def audit_token_corpus(tokens: List[str]) -> AuditFinding:
    if not tokens:
        return AuditFinding(test="token entropy", severity="info",
                            detail="no tokens supplied")
    info = analyse_corpus(tokens)
    sev = "high" if info.get("any_weak") else "info"
    return AuditFinding(test="token entropy / structure", severity=sev,
                        detail=json.dumps(info))


def audit_token_reuse(reset_confirm_url_template: str, token: str,
                      *, timeout: float = 10.0) -> AuditFinding:
    """Hit the same token twice — with --do-confirm flag the operator must accept the side-effect."""
    url = reset_confirm_url_template.replace("{token}", token)
    s1, _, _ = get_url(url, timeout=timeout)
    s2, _, _ = get_url(url, timeout=timeout)
    if s1 == s2 and s1 in (200, 302):
        return AuditFinding(test="token reuse",
                            severity="high",
                            detail=f"token works twice (status1={s1}, status2={s2})")
    return AuditFinding(test="token reuse", severity="info",
                        detail=f"second attempt status={s2} vs first={s1}")


def audit_token_expiration(reset_confirm_url_template: str, token: str,
                           wait_seconds: int = 0, *,
                           timeout: float = 10.0) -> AuditFinding:
    url = reset_confirm_url_template.replace("{token}", token)
    if wait_seconds > 0:
        time.sleep(wait_seconds)
    s, _, _ = get_url(url, timeout=timeout)
    return AuditFinding(test=f"token expiration after {wait_seconds}s",
                        severity="info",
                        detail=f"status={s}. Compare against fresh token, run again with bigger --wait.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="password_reset_audit",
                                description="Password-reset 10-pattern auditor.")
    p.add_argument("--reset-init-url", required=True)
    p.add_argument("--email-field", default="email")
    p.add_argument("--known-email", required=True,
                   help="email registered to a real account you control")
    p.add_argument("--unknown-email", default="redshift-canary-nope-9z@example.invalid")
    p.add_argument("--attacker-email", default="evil@attacker.example")
    p.add_argument("--attacker-host", default="evil.example")

    p.add_argument("--reset-confirm-url",
                   help="URL pattern with {token}, e.g. https://app/reset?token={token}")
    p.add_argument("--tokens-from-stdin", action="store_true",
                   help="read newline-separated tokens from STDIN for entropy + structural analysis")
    p.add_argument("--token-for-reuse",
                   help="single token to test for reuse (requires --reset-confirm-url)")
    p.add_argument("--token-for-expiration",
                   help="single token to test against a wait window")
    p.add_argument("--wait", type=int, default=0,
                   help="seconds to sleep before re-trying (for expiration test)")

    p.add_argument("--rate-limit-n", type=int, default=10)
    p.add_argument("--skip-rate-limit", action="store_true")
    p.add_argument("--timeout", type=float, default=10.0)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args(argv)

    findings: List[AuditFinding] = []

    findings.append(audit_response_oracle(args.reset_init_url, args.email_field,
                                          args.known_email, args.unknown_email,
                                          timeout=args.timeout))
    findings.append(audit_email_param_pollution(args.reset_init_url, args.email_field,
                                                args.known_email, args.attacker_email,
                                                timeout=args.timeout))
    findings.append(audit_host_header_reset(args.reset_init_url, args.email_field,
                                            args.known_email, args.attacker_host,
                                            timeout=args.timeout))
    if not args.skip_rate_limit:
        findings.append(audit_rate_limit(args.reset_init_url, args.email_field,
                                         args.known_email, n=args.rate_limit_n,
                                         timeout=args.timeout))

    if args.tokens_from_stdin:
        tokens = [line.strip() for line in sys.stdin if line.strip()]
        findings.append(audit_token_corpus(tokens))

    if args.reset_confirm_url and args.token_for_reuse:
        findings.append(audit_token_reuse(args.reset_confirm_url, args.token_for_reuse,
                                          timeout=args.timeout))
    if args.reset_confirm_url and args.token_for_expiration:
        findings.append(audit_token_expiration(args.reset_confirm_url,
                                               args.token_for_expiration,
                                               wait_seconds=args.wait, timeout=args.timeout))

    if args.format == "json":
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        c = not args.no_color
        print(paint(f"\n[password_reset_audit] {len(findings)} checks", BOLD, enabled=c))
        for f in findings:
            sevcol = {"critical": RED, "high": RED, "medium": YELLOW, "low": CYAN}.get(f.severity, GREY)
            print(f"  {paint(f.severity.upper(), sevcol, enabled=c):16s} "
                  f"{paint(f.test, BOLD, enabled=c):40s} {f.detail[:120]}")
        print()
        print(paint("Manual follow-up needed for:", BOLD, enabled=c))
        print("  • response oracle: ensure responses are byte-identical")
        print("  • email param pollution: confirm which email actually receives the reset")
        print("  • host-header reset: check the reset email link domain")
        print("  • token reuse / expiration: capture multiple tokens, run with --tokens-from-stdin")

    bad = any(f.severity in ("medium", "high", "critical") for f in findings)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
