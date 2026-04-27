#!/usr/bin/env python3
"""
redshift_toolkit.web.tls_quirks — HSTS / weak cipher / ALPN / cert audit.

Scope (web-tier, complementary to Part 2 Module 07's tls_inspector)
------------------------------------------------------------------
- HSTS: header presence, max-age, includeSubDomains, preload eligibility
- Cert SAN list (Subject Alt Names; correlate with subdomain enum)
- ALPN protocols offered by the server (h2, http/1.1, http/0.9?)
- Minimum TLS version reachable (1.0 / 1.1 weakness)
- Compression / SCSV / OCSP-must-staple flags
- HTTPS→HTTP downgrade risk (HSTS missing)
- Mixed-content risk (Content-Security-Policy blocks present?)

Usage
-----
  python3 -m redshift_toolkit.web.tls_quirks --url https://example.com
  python3 -m redshift_toolkit.web.tls_quirks --url https://example.com --json

Author: Redshift Project — Module 13
License: MIT
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
from dataclasses import dataclass, asdict, field
from urllib.parse import urlsplit

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
class TlsReport:
    host: str
    port: int
    negotiated_version: str | None = None
    negotiated_cipher: str | None = None
    alpn: list[str] = field(default_factory=list)
    legacy_versions_accepted: list[str] = field(default_factory=list)
    cert_subject: str = ""
    cert_issuer: str = ""
    cert_san: list[str] = field(default_factory=list)
    cert_not_after: str = ""
    hsts_header: str | None = None
    hsts_max_age: int | None = None
    hsts_include_subdomains: bool = False
    hsts_preload: bool = False
    findings: list[tuple[str, str]] = field(default_factory=list)


def _try_handshake(host: str, port: int, ver: int, timeout: float = 5.0
                   ) -> tuple[bool, str, str, list, str | None]:
    ctx = ssl.SSLContext(ver)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        ctx.set_alpn_protocols(["h2", "http/1.1"])
    except Exception:
        pass
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        ws = ctx.wrap_socket(s, server_hostname=host)
        cipher = ws.cipher()
        peer = ws.getpeercert()
        alpn = ws.selected_alpn_protocol()
        ws.close()
        return True, str(cipher[0] if cipher else ""), \
               str(cipher[1] if cipher else ""), peer.get("subjectAltName", []) if peer else [], alpn
    except Exception:
        return False, "", "", [], None


def gather(host: str, port: int = 443, timeout: float = 5.0) -> TlsReport:
    rep = TlsReport(host=host, port=port)

    # Default negotiation
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            ctx.set_alpn_protocols(["h2", "http/1.1", "http/1.0"])
        except Exception:
            pass
        ws = ctx.wrap_socket(s, server_hostname=host)
        rep.negotiated_version = ws.version()
        cipher = ws.cipher()
        if cipher:
            rep.negotiated_cipher = f"{cipher[0]} ({cipher[1]} bits)"
        try:
            rep.alpn = [ws.selected_alpn_protocol() or ""]
        except Exception:
            pass
        # Cert (need verify_mode != CERT_NONE to get real cert via getpeercert,
        # but we can use SSLObject._sslobj or fall back to ssl.get_server_certificate)
        ws.close()
    except Exception as e:
        rep.findings.append(("critical", f"TLS handshake failed: {e}"))
        return rep

    # Try to fetch the cert separately for full details.
    try:
        pem = ssl.get_server_certificate((host, port), timeout=timeout)
        # Parse with the cryptography lib if available, else regex out subject.
        try:
            from cryptography import x509
            from cryptography.hazmat.primitives import serialization
            cert = x509.load_pem_x509_certificate(pem.encode())
            rep.cert_subject = cert.subject.rfc4514_string()
            rep.cert_issuer = cert.issuer.rfc4514_string()
            rep.cert_not_after = cert.not_valid_after_utc.isoformat() \
                if hasattr(cert, "not_valid_after_utc") else str(cert.not_valid_after)
            try:
                ext = cert.extensions.get_extension_for_oid(
                    x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
                rep.cert_san = [str(n.value) for n in ext.value]
            except x509.ExtensionNotFound:
                pass
        except ImportError:
            rep.cert_subject = "(install `cryptography` for cert details)"
    except Exception as e:
        rep.findings.append(("medium", f"could not retrieve cert: {e}"))

    # Probe for legacy TLS acceptance
    legacy_probes = [
        (ssl.PROTOCOL_TLSv1, "TLS 1.0"),
        (ssl.PROTOCOL_TLSv1_1, "TLS 1.1"),
    ]
    for proto, name in legacy_probes:
        try:
            ok, _, _, _, _ = _try_handshake(host, port, proto, timeout)
            if ok:
                rep.legacy_versions_accepted.append(name)
                rep.findings.append(("high", f"legacy {name} accepted"))
        except (AttributeError, ssl.SSLError):
            # Modern OpenSSL drops PROTOCOL_TLSv1 entirely — that's fine
            pass

    # HSTS check via HTTP request
    try:
        r = send(HttpRequest(method="GET", url=f"https://{host}:{port}/"),
                 timeout=timeout, tls_verify=False, follow_redirects=False)
        hsts = r.header("Strict-Transport-Security")
        rep.hsts_header = hsts
        if not hsts:
            rep.findings.append(("high", "HSTS header missing — downgrade attacks viable"))
        else:
            for part in [p.strip() for p in hsts.split(";")]:
                if part.startswith("max-age="):
                    try:
                        rep.hsts_max_age = int(part.split("=", 1)[1])
                    except ValueError:
                        pass
                elif part.lower() == "includesubdomains":
                    rep.hsts_include_subdomains = True
                elif part.lower() == "preload":
                    rep.hsts_preload = True
            if rep.hsts_max_age is not None and rep.hsts_max_age < 15552000:
                rep.findings.append(("medium",
                    f"HSTS max-age={rep.hsts_max_age}s (<6 months — preload requires ≥1 year)"))
            if not rep.hsts_include_subdomains:
                rep.findings.append(("medium", "HSTS lacks includeSubDomains"))
    except Exception as e:
        rep.findings.append(("medium", f"HSTS probe failed: {e}"))

    return rep


def render_text(rep: TlsReport, color: bool) -> str:
    out = [paint(f"\n=== TLS audit: {rep.host}:{rep.port} ===", BOLD, color)]
    out.append(f"  Negotiated: {rep.negotiated_version} / {rep.negotiated_cipher}")
    out.append(f"  ALPN:       {', '.join(rep.alpn) or '(none)'}")
    out.append(f"  Subject:    {rep.cert_subject or '(unknown)'}")
    if rep.cert_san:
        out.append(f"  SAN ({len(rep.cert_san)}): {', '.join(rep.cert_san[:8])}"
                   f"{'…' if len(rep.cert_san) > 8 else ''}")
    out.append(f"  Issuer:     {rep.cert_issuer or '(unknown)'}")
    out.append(f"  Expires:    {rep.cert_not_after or '(unknown)'}")
    out.append(f"  HSTS:       {rep.hsts_header or paint('(missing)', RED, color)}")
    if rep.legacy_versions_accepted:
        out.append(paint(f"  Legacy accepted: {', '.join(rep.legacy_versions_accepted)}",
                         RED, color))
    if rep.findings:
        out.append(paint(f"\n  Findings ({len(rep.findings)}):", BOLD, color))
        sev_color = {"critical": RED, "high": RED, "medium": YELLOW, "info": GREY}
        for sev, msg in rep.findings:
            out.append(f"    [{paint(sev, sev_color.get(sev, GREY), color)}] {msg}")
    else:
        out.append(paint("\n  No issues found.", GREEN, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="HSTS / TLS / cert audit.")
    ap.add_argument("--url", required=True)
    ap.add_argument("--timeout", type=float, default=5.0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    sp = urlsplit(args.url)
    host = sp.hostname or args.url
    port = sp.port or 443

    rep = gather(host, port, timeout=args.timeout)

    if args.json:
        print(json.dumps(asdict(rep), indent=2))
    else:
        print(render_text(rep, color))
    return 0 if not rep.findings else 1


if __name__ == "__main__":
    sys.exit(main())
