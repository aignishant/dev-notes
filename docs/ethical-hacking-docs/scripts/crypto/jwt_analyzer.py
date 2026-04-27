#!/usr/bin/env python3
"""
jwt_analyzer.py
===============

Decode and audit a JSON Web Token (JWT) for common security weaknesses.

DEFENSIVE / DEVELOPER USE ONLY
------------------------------
Use against tokens issued by your own applications, in your own pentest
engagements with written authorization, or during CTFs. Do not use against
tokens you do not have permission to test.

What this tool does
-------------------
  * Decodes the header + payload (no signature verification by default).
  * Pretty-prints the structure.
  * Flags common issues:
      - alg=none (server may accept unsigned tokens)
      - HS* with plausibly weak / public keys
      - Missing exp / nbf / iat
      - Already-expired tokens
      - alg=RS*/ES* but a 'kid'/'jku'/'x5u' that points to attacker-influenced URLs
      - Sensitive claim names (password, secret, etc.)
      - Algorithm-confusion potential
  * Optionally verifies the signature when given a key/JWKS URL.

Usage
-----
    python jwt_analyzer.py <jwt-string>
    python jwt_analyzer.py -                                # read from stdin
    python jwt_analyzer.py <jwt> --secret 'mysharedsecret'
    python jwt_analyzer.py <jwt> --jwks https://example.com/.well-known/jwks.json

Author: Ethical Hacking Mastery curriculum
License: Educational use
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import sys
from typing import Any

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
except ImportError:
    print("[-] rich is required: pip install rich", file=sys.stderr)
    sys.exit(1)

console = Console()


# --------------------------------------------------------------------------- #
# Decoding
# --------------------------------------------------------------------------- #
def b64url_decode(s: str) -> bytes:
    pad = (-len(s)) % 4
    return base64.urlsafe_b64decode(s + "=" * pad)


def decode_jwt(token: str) -> tuple[dict[str, Any], dict[str, Any], bytes, str, str]:
    """Returns (header, payload, signature_bytes, signing_input, raw_signature_b64)."""
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"JWT must have 3 dot-separated parts, got {len(parts)}")
    h_b64, p_b64, s_b64 = parts
    try:
        header = json.loads(b64url_decode(h_b64))
        payload = json.loads(b64url_decode(p_b64))
    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError(f"failed to decode JWT segments: {e}") from e
    signature = b64url_decode(s_b64) if s_b64 else b""
    signing_input = f"{h_b64}.{p_b64}"
    return header, payload, signature, signing_input, s_b64


# --------------------------------------------------------------------------- #
# Auditing
# --------------------------------------------------------------------------- #
SENSITIVE_CLAIMS = {"password", "passwd", "pwd", "secret", "client_secret",
                    "api_key", "apikey", "private_key", "credit_card", "ssn"}


def audit(header: dict[str, Any], payload: dict[str, Any],
          signature: bytes) -> list[tuple[str, str]]:
    """Return list of (severity, message) tuples."""
    findings: list[tuple[str, str]] = []
    alg = (header.get("alg") or "").lower()

    # 1. alg=none
    if alg in ("none", ""):
        findings.append(("HIGH",
            "Algorithm is 'none' — token is unsigned. If the server accepts this, "
            "anyone can mint admin tokens. Always pin a non-'none' alg server-side."))

    # 2. Weak / suspicious algs
    if alg.startswith("hs"):
        findings.append(("INFO",
            f"HMAC algorithm ({alg}). Secret should be ≥ 32 random bytes. "
            "Weak secrets can be cracked offline (hashcat -m 16500)."))

    # 3. Algorithm-confusion potential
    if alg.startswith("hs") and ("jwk" in header or "jku" in header
                                  or "x5u" in header or "x5c" in header):
        findings.append(("HIGH",
            "HS* alg combined with key-distribution headers (jwk/jku/x5u/x5c) "
            "smells like algorithm confusion. Ensure the server pins the alg."))

    # 4. kid / jku / x5u with attacker-influenceable URLs
    for hdr in ("jku", "x5u"):
        if hdr in header:
            findings.append(("HIGH",
                f"Header contains '{hdr}={header[hdr]}'. If the server fetches this URL "
                "to validate, attackers can host malicious keys. Server must allow-list trusted hosts."))
    if "kid" in header and any(c in str(header["kid"]) for c in "/.\\"):
        findings.append(("MEDIUM",
            f"'kid' looks path-like ({header['kid']}); if used in a file lookup or SQL query, "
            "watch for path traversal / SQL injection."))

    # 5. Time claims
    now = dt.datetime.now(dt.timezone.utc).timestamp()
    if "exp" not in payload:
        findings.append(("MEDIUM",
            "No 'exp' (expiration) claim — tokens never expire. Server should reject."))
    else:
        try:
            exp = float(payload["exp"])
            remaining = exp - now
            if remaining < 0:
                findings.append(("INFO",
                    f"Token EXPIRED {abs(int(remaining))}s ago "
                    f"(exp={dt.datetime.fromtimestamp(exp, dt.timezone.utc).isoformat()})."))
            elif remaining > 86400 * 30:
                findings.append(("MEDIUM",
                    f"Token has very long lifetime "
                    f"({int(remaining/86400)} days). Prefer short-lived access tokens."))
        except Exception:
            findings.append(("MEDIUM", "'exp' is not a valid numeric timestamp."))

    if "nbf" not in payload:
        findings.append(("LOW", "No 'nbf' (not-before) claim."))
    if "iat" not in payload:
        findings.append(("LOW", "No 'iat' (issued-at) claim."))
    if "iss" not in payload:
        findings.append(("LOW", "No 'iss' (issuer) claim — server should pin the expected issuer."))
    if "aud" not in payload:
        findings.append(("LOW", "No 'aud' (audience) claim — guards against token re-use across services."))

    # 6. Sensitive claims
    for claim in payload:
        if claim.lower() in SENSITIVE_CLAIMS:
            findings.append(("HIGH",
                f"Claim '{claim}' looks sensitive — JWT payload is BASE64, not encrypted. "
                "Don't put secrets in the payload. Use JWE if you need confidentiality."))

    # 7. Mutable role/admin claims
    for claim in ("role", "roles", "admin", "is_admin", "scope", "scopes", "permissions"):
        if claim in payload:
            findings.append(("INFO",
                f"Claim '{claim}'={payload[claim]!r} carries authorization. "
                "Server must verify the signature & issuer; never trust client-supplied JWTs."))

    # 8. Empty signature
    if not signature and alg not in ("none", ""):
        findings.append(("HIGH",
            f"Empty signature with alg={alg}. Server must reject."))

    return findings


# --------------------------------------------------------------------------- #
# Optional signature verification
# --------------------------------------------------------------------------- #
def verify_with_secret(token: str, secret: str) -> tuple[bool, str]:
    try:
        import jwt as pyjwt   # type: ignore
    except ImportError:
        return False, "PyJWT not installed (pip install pyjwt) — skipping verify"
    try:
        # Decode without verifying first to learn alg
        header = json.loads(b64url_decode(token.split(".")[0]))
        alg = header.get("alg", "HS256")
        pyjwt.decode(token, secret, algorithms=[alg],
                     options={"verify_aud": False, "verify_iss": False,
                              "verify_exp": False})
        return True, f"Signature VALID for alg={alg} with provided secret."
    except Exception as e:
        return False, f"Signature INVALID / not verifiable: {e}"


def verify_with_jwks(token: str, jwks_url: str) -> tuple[bool, str]:
    try:
        import jwt as pyjwt           # type: ignore
        from jwt import PyJWKClient   # type: ignore
    except ImportError:
        return False, "PyJWT[crypto] not installed (pip install 'pyjwt[crypto]')"
    try:
        jwks = PyJWKClient(jwks_url)
        signing_key = jwks.get_signing_key_from_jwt(token).key
        header = json.loads(b64url_decode(token.split(".")[0]))
        alg = header.get("alg", "RS256")
        pyjwt.decode(token, signing_key, algorithms=[alg],
                     options={"verify_aud": False, "verify_iss": False,
                              "verify_exp": False})
        return True, f"Signature VALID against JWKS ({jwks_url}) using alg={alg}."
    except Exception as e:
        return False, f"Signature INVALID / not verifiable: {e}"


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
SEVERITY_COLOR = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "cyan", "INFO": "white"}


def print_section(title: str, body: dict[str, Any]) -> None:
    js = json.dumps(body, indent=2, ensure_ascii=False, default=str)
    console.print(Panel(Syntax(js, "json", line_numbers=False),
                        title=f"[bold]{title}[/bold]", border_style="blue"))


def print_findings(findings: list[tuple[str, str]]) -> None:
    if not findings:
        console.print("[green]✓ No notable issues found.[/green]")
        return
    table = Table(title="Findings", header_style="bold cyan", show_lines=True)
    table.add_column("Severity")
    table.add_column("Note", overflow="fold")
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
    for sev, note in sorted(findings, key=lambda x: order.get(x[0], 99)):
        table.add_row(f"[{SEVERITY_COLOR[sev]}]{sev}[/{SEVERITY_COLOR[sev]}]", note)
    console.print(table)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Decode and audit a JWT for common weaknesses.",
    )
    parser.add_argument("token", help="JWT string, or '-' to read from stdin")
    parser.add_argument("--secret", default=None,
                        help="HMAC secret to verify HS* signature")
    parser.add_argument("--jwks", default=None,
                        help="JWKS URL to verify RS*/ES*/PS* signature")
    args = parser.parse_args()

    token = sys.stdin.read().strip() if args.token == "-" else args.token.strip()
    if not token:
        raise SystemExit("[-] No token provided.")

    try:
        header, payload, signature, signing_input, sig_b64 = decode_jwt(token)
    except ValueError as e:
        raise SystemExit(f"[-] {e}")

    print_section("Header", header)
    print_section("Payload", payload)

    sig_meta = {
        "length_bytes": len(signature),
        "first_8_bytes_hex": signature[:8].hex() if signature else "",
        "encoded": sig_b64 or "(empty)",
    }
    print_section("Signature", sig_meta)

    findings = audit(header, payload, signature)
    print_findings(findings)

    if args.secret:
        ok, msg = verify_with_secret(token, args.secret)
        console.print(f"[bold]Verify (secret):[/bold] "
                      f"{'[green]'+msg+'[/green]' if ok else '[red]'+msg+'[/red]'}")
    if args.jwks:
        ok, msg = verify_with_jwks(token, args.jwks)
        console.print(f"[bold]Verify (JWKS):[/bold] "
                      f"{'[green]'+msg+'[/green]' if ok else '[red]'+msg+'[/red]'}")


if __name__ == "__main__":
    main()
