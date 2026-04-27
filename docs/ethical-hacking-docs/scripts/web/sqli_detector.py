#!/usr/bin/env python3
"""
sqli_detector.py — Careful, probe-only SQL Injection *detector*.

This is **not** an exploiter. It sends a small, fixed set of well-known
detection probes per parameter and reports parameters that show classic
SQLi signals:
  - Database error strings in the response (error-based)
  - Significant response-length difference between true/false probes
    (boolean-blind)
  - Significant response-time difference for sleep probes (time-blind)

Used to find candidates for manual analysis with sqlmap / Burp / hand work.
Designed to be safe to run during authorized engagements:
  - One concurrent request at a time per host
  - Configurable per-request delay
  - Sleep probes default to 5 seconds (caller can adjust)
  - All probes are read-only — no UPDATE/INSERT/DROP

⚠️ AUTHORIZATION REQUIRED ⚠️
SQL injection probes are an *active* test. Run only against systems you
own or are explicitly authorized to test. ROE applies.

Usage:
    python3 sqli_detector.py "https://target.com/page?id=1&q=test"
    python3 sqli_detector.py "https://target.com/page" --post "id=1&q=test"
    python3 sqli_detector.py "https://target.com/page?id=1" \\
        --header "Cookie: session=abc" --header "Authorization: Bearer ..."
    python3 sqli_detector.py "https://target.com/page?id=1" --json -o sqli.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
import urllib.parse
from dataclasses import dataclass, field, asdict

import httpx

USER_AGENT = "sqli-detector/1.0 (defensive testing only)"
TIMEOUT = httpx.Timeout(60.0, connect=15.0)

# Database error fingerprints — adapted from sqlmap's payload set
ERROR_SIGNATURES = [
    (re.compile(r"SQL syntax.*MySQL", re.I), "MySQL"),
    (re.compile(r"Warning.*mysql_", re.I), "MySQL"),
    (re.compile(r"valid MySQL result", re.I), "MySQL"),
    (re.compile(r"MySqlClient\.", re.I), "MySQL .NET"),
    (re.compile(r"check the manual that corresponds to your MySQL", re.I), "MySQL"),
    (re.compile(r"PostgreSQL.*ERROR", re.I), "PostgreSQL"),
    (re.compile(r"Warning.*pg_", re.I), "PostgreSQL"),
    (re.compile(r"valid PostgreSQL result", re.I), "PostgreSQL"),
    (re.compile(r"Npgsql\.", re.I), "PostgreSQL .NET"),
    (re.compile(r"Driver.*SQL[\-\_\ ]*Server", re.I), "MSSQL"),
    (re.compile(r"OLE DB.*SQL Server", re.I), "MSSQL"),
    (re.compile(r"\[SQL Server\]", re.I), "MSSQL"),
    (re.compile(r"ODBC SQL Server Driver", re.I), "MSSQL"),
    (re.compile(r"Unclosed quotation mark after the character string", re.I), "MSSQL"),
    (re.compile(r"Microsoft OLE DB Provider for ODBC Drivers", re.I), "MSSQL"),
    (re.compile(r"\bORA-\d{5}", re.I), "Oracle"),
    (re.compile(r"Oracle error", re.I), "Oracle"),
    (re.compile(r"quoted string not properly terminated", re.I), "Oracle"),
    (re.compile(r"SQLite/JDBCDriver", re.I), "SQLite"),
    (re.compile(r"SQLite\.Exception", re.I), "SQLite"),
    (re.compile(r"System\.Data\.SQLite\.SQLiteException", re.I), "SQLite"),
    (re.compile(r"Warning.*sqlite_", re.I), "SQLite"),
    (re.compile(r"\[SQLITE_ERROR\]", re.I), "SQLite"),
    (re.compile(r"DB2 SQL error", re.I), "IBM DB2"),
    (re.compile(r"Sybase message", re.I), "Sybase"),
    (re.compile(r"Sybase.*Server message", re.I), "Sybase"),
]


@dataclass
class Probe:
    name: str
    payload: str
    kind: str  # 'error', 'true', 'false', 'sleep'
    sleep_seconds: int = 0


# Carefully-chosen detection probes
PROBES: list[Probe] = [
    Probe("quote", "'", "error"),
    Probe("dquote", '"', "error"),
    Probe("backslash", "\\", "error"),
    Probe("paren", "')", "error"),
    Probe("comment", "'--", "error"),
    Probe("bool_true", "' OR '1'='1' -- ", "true"),
    Probe("bool_false", "' AND '1'='2' -- ", "false"),
    Probe("numeric_true", " OR 1=1-- ", "true"),
    Probe("numeric_false", " AND 1=2-- ", "false"),
    # Sleep probes — last, only fired if other probes look promising
    Probe("sleep_mysql", "' AND SLEEP({s}) -- ", "sleep", sleep_seconds=5),
    Probe("sleep_pgsql", "'; SELECT pg_sleep({s}) -- ", "sleep", sleep_seconds=5),
    Probe("sleep_mssql", "'; WAITFOR DELAY '0:0:{s}' -- ", "sleep", sleep_seconds=5),
]


@dataclass
class Finding:
    parameter: str
    method: str
    probe: str
    payload: str
    evidence: str
    severity: str  # 'high' / 'medium' / 'low'


@dataclass
class ParamReport:
    parameter: str
    method: str
    baseline_length: int
    baseline_status: int
    baseline_time_ms: float
    findings: list[Finding] = field(default_factory=list)


def detect_db_error(body: str) -> str | None:
    for pattern, label in ERROR_SIGNATURES:
        if pattern.search(body):
            return label
    return None


def parse_params(url: str, post_body: str | None) -> tuple[str, dict[str, str], dict[str, str]]:
    parsed = urllib.parse.urlsplit(url)
    base_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    get_params = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
    post_params = dict(urllib.parse.parse_qsl(post_body or "", keep_blank_values=True))
    return base_url, get_params, post_params


async def send(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    get_params: dict[str, str],
    post_params: dict[str, str],
    headers: dict[str, str],
    target_param: str,
    new_value: str,
    is_get: bool,
) -> tuple[httpx.Response | None, float]:
    g = dict(get_params)
    p = dict(post_params)
    if is_get:
        g[target_param] = new_value
    else:
        p[target_param] = new_value
    full_url = url + ("?" + urllib.parse.urlencode(g) if g else "")
    start = time.monotonic()
    try:
        if method == "POST":
            r = await client.post(full_url, data=p, headers=headers)
        else:
            r = await client.get(full_url, headers=headers)
    except httpx.HTTPError:
        return None, 0.0
    return r, (time.monotonic() - start) * 1000.0


async def test_param(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    get_params: dict[str, str],
    post_params: dict[str, str],
    headers: dict[str, str],
    param: str,
    is_get: bool,
    delay: float,
    sleep_seconds: int,
) -> ParamReport:
    original = (get_params if is_get else post_params)[param]
    # Baseline
    baseline, base_time = await send(client, method, url, get_params, post_params, headers, param, original, is_get)
    if baseline is None:
        return ParamReport(parameter=param, method=method, baseline_length=0, baseline_status=0, baseline_time_ms=0.0)

    base_len = len(baseline.text)
    report = ParamReport(
        parameter=param,
        method=method,
        baseline_length=base_len,
        baseline_status=baseline.status_code,
        baseline_time_ms=base_time,
    )

    saw_error = False
    bool_true_len: int | None = None
    bool_false_len: int | None = None

    for probe in PROBES:
        if probe.kind == "sleep":
            # Only fire sleep probes if we already see signals — saves time + load
            if not saw_error and (bool_true_len is None or bool_false_len is None):
                continue
            payload = original + probe.payload.format(s=sleep_seconds)
        else:
            payload = original + probe.payload

        await asyncio.sleep(delay)
        resp, elapsed = await send(client, method, url, get_params, post_params, headers, param, payload, is_get)
        if resp is None:
            continue

        body = resp.text or ""

        if probe.kind == "error":
            db = detect_db_error(body)
            if db:
                saw_error = True
                report.findings.append(
                    Finding(
                        parameter=param,
                        method=method,
                        probe=probe.name,
                        payload=payload,
                        evidence=f"DB error string detected ({db})",
                        severity="high",
                    )
                )
        elif probe.kind == "true":
            bool_true_len = len(body)
        elif probe.kind == "false":
            bool_false_len = len(body)
        elif probe.kind == "sleep":
            # Time-based: response should take ~sleep_seconds longer than baseline
            if elapsed > (base_time + sleep_seconds * 1000 * 0.7):
                report.findings.append(
                    Finding(
                        parameter=param,
                        method=method,
                        probe=probe.name,
                        payload=payload,
                        evidence=f"Sleep probe delayed response by {elapsed - base_time:.0f}ms (baseline {base_time:.0f}ms)",
                        severity="high",
                    )
                )

    # Boolean-blind heuristic
    if bool_true_len is not None and bool_false_len is not None:
        diff = abs(bool_true_len - bool_false_len)
        if diff > 50 and abs(bool_true_len - base_len) < diff:
            report.findings.append(
                Finding(
                    parameter=param,
                    method=method,
                    probe="boolean_blind",
                    payload="(true vs false probe)",
                    evidence=(
                        f"True payload returned {bool_true_len} bytes, "
                        f"false returned {bool_false_len}, baseline {base_len}"
                    ),
                    severity="medium",
                )
            )

    return report


async def run(args: argparse.Namespace) -> list[ParamReport]:
    headers = {"User-Agent": USER_AGENT}
    for h in args.header or []:
        if ":" not in h:
            continue
        k, v = h.split(":", 1)
        headers[k.strip()] = v.strip()

    method = "POST" if args.post else "GET"
    base_url, get_params, post_params = parse_params(args.url, args.post)

    targets: list[tuple[str, bool]] = []
    if args.parameters:
        wanted = {p.strip() for p in args.parameters.split(",") if p.strip()}
        for k in get_params:
            if k in wanted:
                targets.append((k, True))
        for k in post_params:
            if k in wanted:
                targets.append((k, False))
    else:
        targets = [(k, True) for k in get_params] + [(k, False) for k in post_params]

    if not targets:
        raise RuntimeError("No parameters found to test.")

    reports: list[ParamReport] = []
    async with httpx.AsyncClient(timeout=TIMEOUT, verify=not args.insecure, http2=False) as client:
        for param, is_get in targets:
            if not args.quiet:
                ctx = "GET" if is_get else "POST"
                print(f"[*] Testing parameter {param!r} ({ctx})", file=sys.stderr)
            report = await test_param(
                client,
                method,
                base_url,
                get_params,
                post_params,
                headers,
                param,
                is_get,
                args.delay,
                args.sleep_seconds,
            )
            if report.findings and not args.quiet:
                for f in report.findings:
                    print(f"  [!] {f.severity.upper()}: {f.evidence}  (probe: {f.probe})", file=sys.stderr)
            reports.append(report)
    return reports


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("url", help="Target URL (with query string for GET)")
    p.add_argument("--post", help="POST body string (e.g. 'id=1&name=foo')")
    p.add_argument("-H", "--header", action="append", help="Header to add (repeatable)")
    p.add_argument("-p", "--parameters", help="Comma-separated parameter names to test (default: all)")
    p.add_argument("--delay", type=float, default=0.3, help="Delay between probes in seconds (default: 0.3)")
    p.add_argument("--sleep-seconds", type=int, default=5, help="Sleep seconds for time-based probes (default: 5)")
    p.add_argument("-k", "--insecure", action="store_true", help="Skip TLS verification")
    p.add_argument("--json", action="store_true", help="Output JSON")
    p.add_argument("-o", "--output", help="Write JSON report to file")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress progress messages")
    args = p.parse_args()

    if not args.quiet:
        print(
            "[!] SQLi detection probes are ACTIVE. Only run against authorized targets.",
            file=sys.stderr,
        )

    try:
        reports = asyncio.run(run(args))
    except KeyboardInterrupt:
        print("\n[!] Interrupted.", file=sys.stderr)
        return 130
    except RuntimeError as e:
        print(f"[-] {e}", file=sys.stderr)
        return 1

    findings_total = sum(len(r.findings) for r in reports)

    if args.json or args.output:
        payload = json.dumps(
            {
                "url": args.url,
                "method": "POST" if args.post else "GET",
                "total_findings": findings_total,
                "reports": [asdict(r) for r in reports],
            },
            indent=2,
        )
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(payload)
            if not args.quiet:
                print(f"[+] Wrote {args.output}", file=sys.stderr)
        else:
            print(payload)

    if not args.quiet:
        print(f"\n[+] Done. {findings_total} potential SQLi indicators across {len(reports)} parameters.", file=sys.stderr)
        if findings_total:
            print("[i] Validate manually with sqlmap or Burp before reporting.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
