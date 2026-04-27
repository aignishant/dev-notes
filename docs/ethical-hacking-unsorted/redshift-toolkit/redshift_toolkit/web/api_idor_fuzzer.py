#!/usr/bin/env python3
"""
redshift_toolkit.web.api_idor_fuzzer — IDOR / BOLA / mass-assignment fuzzer.

Takes two authenticated sessions (A, B), each owning some object IDs, and
checks whether either user can access or modify the other's resources.

Methodology
-----------
1. Read the endpoint map from a file or auto-discover from JSON responses.
2. For each ID in the URL/body of an endpoint, swap A's ID for B's ID
   while using A's session.
3. Compare:
   - 200 with B's data → IDOR confirmed.
   - 403 / 404 → correct.
   - 200 with A's data → endpoint ignored the changed ID (probably ok).
4. Mass assignment: PATCH /api/me with extra fields like `role: admin`,
   `is_admin: true`, `tenant_id: <other>`, observe response.
5. Rate limit: in --rate-test, send 30 requests in 5s to a sensitive endpoint
   and observe whether any limit is enforced.

Usage
-----
  # Build endpoints.json with two test users' IDs:
  # [
  #   {"name":"get_user", "method":"GET", "url":"https://api.com/users/{id}",
  #    "id_a":"100", "id_b":"200"},
  #   {"name":"get_order","method":"GET","url":"https://api.com/orders/{id}",
  #    "id_a":"500", "id_b":"600"}
  # ]
  python3 -m redshift_toolkit.web.api_idor_fuzzer \\
      --endpoints endpoints.json \\
      --token-a $TOK_A --token-b $TOK_B

  python3 -m redshift_toolkit.web.api_idor_fuzzer \\
      --endpoints endpoints.json --token-a $TOK_A \\
      --rate-test --rate-target /api/me --rate-burst 30

Author: Redshift Project — Module 15
License: MIT
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from dataclasses import dataclass, asdict, field
from typing import Any

from redshift_toolkit.web.http_client import HttpRequest, send

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


@dataclass
class IdorFinding:
    name: str
    url_a: str
    url_b: str
    status_a_self: int = 0
    status_a_b: int = 0
    body_a_self_len: int = 0
    body_a_b_len: int = 0
    verdict: str = ""    # "vulnerable" | "ok" | "ambiguous" | "error"
    note: str = ""


def auth_headers(token: str | None, cookie: str | None) -> list[tuple[str, str]]:
    h = []
    if token:
        h.append(("Authorization", f"Bearer {token}"))
    if cookie:
        h.append(("Cookie", cookie))
    return h


def test_idor(ep: dict, *,
              auth_a: list[tuple[str, str]],
              tls_verify: bool = True, timeout: float = 15.0) -> IdorFinding:
    name = ep.get("name") or ep["url"]
    url_template = ep["url"]
    method = ep.get("method", "GET").upper()
    body = ep.get("body")
    id_a = str(ep["id_a"])
    id_b = str(ep["id_b"])

    url_self = url_template.format(id=id_a)
    url_other = url_template.format(id=id_b)

    headers_self = list(auth_a) + [(k, v) for k, v in (ep.get("headers") or {}).items()]
    try:
        r_self = send(HttpRequest(method=method, url=url_self,
                                  headers=headers_self, body=body),
                      timeout=timeout, tls_verify=tls_verify,
                      follow_redirects=False)
        r_other = send(HttpRequest(method=method, url=url_other,
                                   headers=headers_self, body=body),
                       timeout=timeout, tls_verify=tls_verify,
                       follow_redirects=False)
    except Exception as e:
        return IdorFinding(name=name, url_a=url_self, url_b=url_other,
                           verdict="error", note=str(e))

    f = IdorFinding(name=name, url_a=url_self, url_b=url_other,
                    status_a_self=r_self.status,
                    status_a_b=r_other.status,
                    body_a_self_len=len(r_self.body),
                    body_a_b_len=len(r_other.body))

    if r_other.status in (401, 403, 404):
        f.verdict = "ok"
        f.note = f"correctly denied with {r_other.status}"
    elif r_other.status == 200 and r_self.status == 200:
        # If body identical, the endpoint may not actually use the ID
        if r_other.body == r_self.body:
            f.verdict = "ambiguous"
            f.note = "responses identical — endpoint may not honor the ID"
        elif id_b.encode() in r_other.body:
            f.verdict = "vulnerable"
            f.note = "received B's resource while authenticated as A"
        else:
            f.verdict = "ambiguous"
            f.note = "200 with different body — manual review"
    else:
        f.verdict = "ambiguous"
        f.note = f"unusual statuses self={r_self.status} other={r_other.status}"
    return f


def test_mass_assignment(url: str, *, method: str = "PATCH",
                         auth: list[tuple[str, str]],
                         payloads: list[dict] | None = None,
                         tls_verify: bool = True, timeout: float = 15.0
                         ) -> list[dict]:
    payloads = payloads or [
        {"role": "admin"},
        {"is_admin": True},
        {"isAdmin": True},
        {"isSuperuser": True},
        {"tenant_id": "00000000-0000-0000-0000-000000000000"},
        {"verified": True},
        {"email_verified": True},
        {"plan": "enterprise"},
        {"balance": 1000000},
        {"approved": True},
    ]
    out = []
    for p in payloads:
        body = json.dumps(p)
        h = list(auth) + [("Content-Type", "application/json")]
        try:
            r = send(HttpRequest(method=method, url=url, headers=h, body=body),
                     timeout=timeout, tls_verify=tls_verify,
                     follow_redirects=False)
        except Exception as e:
            out.append({"payload": p, "error": str(e)})
            continue
        out.append({"payload": p, "status": r.status,
                    "body_len": len(r.body),
                    "echoed": all(str(v) in r.body.decode("latin-1", errors="replace")
                                  for v in p.values())})
    return out


def rate_test(target_url: str, *, method: str = "GET",
              auth: list[tuple[str, str]], burst: int = 30,
              tls_verify: bool = True, timeout: float = 10.0) -> dict:
    """Send `burst` requests as concurrently as Python allows."""
    results = {"sent": 0, "ok": 0, "limited": 0, "errors": 0}
    lock = threading.Lock()

    def worker():
        try:
            r = send(HttpRequest(method=method, url=target_url, headers=auth),
                     timeout=timeout, tls_verify=tls_verify,
                     follow_redirects=False)
            with lock:
                results["sent"] += 1
                if r.status == 429 or 'rate' in (r.header('Retry-After') or '').lower():
                    results["limited"] += 1
                elif 200 <= r.status < 400:
                    results["ok"] += 1
        except Exception:
            with lock:
                results["errors"] += 1

    threads = [threading.Thread(target=worker) for _ in range(burst)]
    t0 = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    results["elapsed_s"] = round(time.time() - t0, 3)
    return results


def render_idor(findings: list[IdorFinding], color: bool) -> str:
    out = [paint("\n=== IDOR / BOLA results ===", BOLD, color)]
    sev_color = {"vulnerable": RED, "ok": GREEN, "ambiguous": YELLOW, "error": GREY}
    for f in findings:
        c = sev_color.get(f.verdict, GREY)
        out.append(f"  [{paint(f.verdict, c, color)}] {f.name}")
        out.append(f"      A→A: {f.status_a_self} ({f.body_a_self_len}b)  "
                   f"A→B: {f.status_a_b} ({f.body_a_b_len}b)")
        if f.note:
            out.append(f"      {f.note}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="API IDOR / BOLA / mass-assignment fuzzer.")
    ap.add_argument("--endpoints", help="JSON file with endpoint list")
    ap.add_argument("--token-a", help="bearer token A")
    ap.add_argument("--cookie-a", help="cookie A")
    ap.add_argument("--token-b", help="bearer token B (informational)")
    ap.add_argument("--cookie-b", help="cookie B (informational)")
    ap.add_argument("--mass-assign-url",
                    help="URL to test for mass assignment (e.g. /api/users/me)")
    ap.add_argument("--mass-assign-method", default="PATCH")
    ap.add_argument("--rate-test", action="store_true")
    ap.add_argument("--rate-target", help="URL for rate-limit test")
    ap.add_argument("--rate-burst", type=int, default=30)
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    auth_a = auth_headers(args.token_a, args.cookie_a)
    out: dict[str, Any] = {}

    if args.endpoints:
        with open(args.endpoints) as f:
            endpoints = json.load(f)
        idor_results = [test_idor(ep, auth_a=auth_a,
                                   tls_verify=not args.insecure,
                                   timeout=args.timeout)
                        for ep in endpoints]
        out["idor"] = [asdict(r) for r in idor_results]
        if not args.json:
            print(render_idor(idor_results, color))

    if args.mass_assign_url:
        ma = test_mass_assignment(args.mass_assign_url, method=args.mass_assign_method,
                                   auth=auth_a,
                                   tls_verify=not args.insecure,
                                   timeout=args.timeout)
        out["mass_assignment"] = ma
        if not args.json:
            print(paint("\n=== Mass-assignment results ===", BOLD, color))
            for r in ma:
                if r.get("echoed"):
                    print(f"  [{paint('ECHO', RED, color)}] {r['payload']} "
                          f"→ status {r.get('status')}")
                else:
                    print(f"  [{paint('---', GREEN, color)}] {r['payload']} "
                          f"→ status {r.get('status')}")

    if args.rate_test and args.rate_target:
        rt = rate_test(args.rate_target, auth=auth_a, burst=args.rate_burst,
                        tls_verify=not args.insecure, timeout=args.timeout)
        out["rate_test"] = rt
        if not args.json:
            print(paint("\n=== Rate-limit test ===", BOLD, color))
            print(f"  burst={args.rate_burst} sent={rt['sent']} "
                  f"ok={rt['ok']} limited={rt['limited']} "
                  f"errors={rt['errors']} time={rt['elapsed_s']}s")
            if rt["limited"] == 0:
                print(paint(f"  [VULN] no rate limiting observed", RED, color))

    if args.json:
        print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
