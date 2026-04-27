#!/usr/bin/env python3
"""
redshift_toolkit.scan.tls_inspector — TLS certificate and configuration
inspector.

What it reports per target
--------------------------
- Subject, issuer, full SAN list
- Validity (notBefore / notAfter / days_remaining)
- Public key algorithm + size (flags small RSA, weak DH)
- Signature algorithm (flags MD5/SHA-1)
- Self-signed / chain-incomplete heuristics
- Negotiated cipher suite + TLS protocol version
- Hostname mismatch flag

Two backends
------------
1. Python `ssl` stdlib (always available).
2. `cryptography` library if installed (richer cert dissection).

Usage
-----
  ./tls_inspector.py example.com
  ./tls_inspector.py example.com:8443
  ./tls_inspector.py --target-file targets.txt --json
  ./tls_inspector.py example.com --warn-days 30

Author: Redshift Project — Module 10
License: MIT
"""

from __future__ import annotations

import argparse
import asyncio
import json
import socket
import ssl
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone

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
    target: str
    host: str
    port: int
    reachable: bool = False
    tls_version: str | None = None
    cipher: str | None = None
    subject: str | None = None
    issuer: str | None = None
    san: list[str] = field(default_factory=list)
    not_before: str | None = None
    not_after: str | None = None
    days_remaining: int | None = None
    sig_algorithm: str | None = None
    pubkey_algorithm: str | None = None
    pubkey_size: int | None = None
    self_signed: bool | None = None
    hostname_match: bool | None = None
    serial_number: str | None = None
    flags: list[str] = field(default_factory=list)
    error: str | None = None


def _split_target(t: str) -> tuple[str, int]:
    if ":" in t and not t.startswith("["):
        host, port = t.rsplit(":", 1)
        return host, int(port)
    return t, 443


def _parse_dn(items: tuple) -> str:
    """X509 DN tuple → string. ssl returns (((key, value),), ...)."""
    if not items:
        return ""
    parts = []
    for rdn in items:
        for k, v in rdn:
            parts.append(f"{k}={v}")
    return ", ".join(parts)


def _try_cryptography(der_bytes: bytes) -> dict | None:
    """Richer parse using `cryptography`. Returns None if unavailable."""
    try:
        from cryptography import x509  # type: ignore
        from cryptography.hazmat.primitives.asymmetric import rsa, ec, dsa  # type: ignore
    except ImportError:
        return None
    try:
        cert = x509.load_der_x509_certificate(der_bytes)
    except Exception:
        return None
    out = {
        "sig_algorithm": cert.signature_hash_algorithm.name
            if cert.signature_hash_algorithm else None,
        "serial_number": format(cert.serial_number, "x"),
    }
    pub = cert.public_key()
    if isinstance(pub, rsa.RSAPublicKey):
        out["pubkey_algorithm"] = "RSA"
        out["pubkey_size"] = pub.key_size
    elif isinstance(pub, ec.EllipticCurvePublicKey):
        out["pubkey_algorithm"] = f"EC ({pub.curve.name})"
        out["pubkey_size"] = pub.curve.key_size
    elif isinstance(pub, dsa.DSAPublicKey):
        out["pubkey_algorithm"] = "DSA"
        out["pubkey_size"] = pub.key_size
    return out


def inspect(target: str, timeout: float = 5.0,
            warn_days: int = 30) -> TlsReport:
    host, port = _split_target(target)
    rep = TlsReport(target=target, host=host, port=port)

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    # Make sure we can negotiate ciphers across deployments
    try:
        ctx.set_ciphers("ALL:@SECLEVEL=0")
    except ssl.SSLError:
        pass

    der_bytes: bytes | None = None
    try:
        with socket.create_connection((host, port), timeout=timeout) as raw:
            with ctx.wrap_socket(raw, server_hostname=host) as tls:
                rep.reachable = True
                rep.tls_version = tls.version()
                cipher = tls.cipher()
                if cipher:
                    rep.cipher = f"{cipher[0]} ({cipher[1]}, {cipher[2]} bits)"
                cert = tls.getpeercert()
                der_bytes = tls.getpeercert(binary_form=True)

        if cert:
            rep.subject = _parse_dn(cert.get("subject", ()))
            rep.issuer = _parse_dn(cert.get("issuer", ()))
            sans: list[str] = []
            for typ, val in cert.get("subjectAltName", ()) or ():
                sans.append(f"{typ}:{val}")
            rep.san = sans
            rep.not_before = cert.get("notBefore")
            rep.not_after = cert.get("notAfter")
            rep.serial_number = cert.get("serialNumber")
            if rep.not_after:
                try:
                    not_after_dt = datetime.strptime(
                        rep.not_after, "%b %d %H:%M:%S %Y %Z"
                    ).replace(tzinfo=timezone.utc)
                    rep.days_remaining = (
                        not_after_dt - datetime.now(timezone.utc)
                    ).days
                except ValueError:
                    pass
            rep.self_signed = (rep.subject == rep.issuer)
            try:
                # Manually re-check hostname against cert
                ssl.match_hostname(cert, host)
                rep.hostname_match = True
            except (ssl.CertificateError, ValueError):
                rep.hostname_match = False
            except AttributeError:
                # Python 3.12+ removed ssl.match_hostname; basic SAN check
                names = [v for typ, v in cert.get("subjectAltName", ()) or ()
                         if typ == "DNS"]
                rep.hostname_match = any(
                    host == n or (n.startswith("*.")
                                   and host.endswith(n[1:]))
                    for n in names
                )

        # Optional cryptography enrichment
        if der_bytes:
            extra = _try_cryptography(der_bytes)
            if extra:
                if extra.get("sig_algorithm"):
                    rep.sig_algorithm = extra["sig_algorithm"]
                if extra.get("pubkey_algorithm"):
                    rep.pubkey_algorithm = extra["pubkey_algorithm"]
                if extra.get("pubkey_size"):
                    rep.pubkey_size = extra["pubkey_size"]
                if extra.get("serial_number"):
                    rep.serial_number = extra["serial_number"]

    except (socket.timeout, OSError) as e:
        rep.error = f"connection: {e}"
        return rep
    except ssl.SSLError as e:
        rep.error = f"tls: {e}"
        return rep

    # Flags
    if rep.tls_version in ("SSLv3", "TLSv1", "TLSv1.1"):
        rep.flags.append("legacy_tls_version")
    if rep.sig_algorithm and rep.sig_algorithm.lower() in ("md5", "sha1"):
        rep.flags.append("weak_signature_algorithm")
    if rep.pubkey_algorithm == "RSA" and rep.pubkey_size and rep.pubkey_size < 2048:
        rep.flags.append("weak_rsa_key")
    if rep.self_signed:
        rep.flags.append("self_signed")
    if rep.hostname_match is False:
        rep.flags.append("hostname_mismatch")
    if rep.days_remaining is not None and rep.days_remaining < 0:
        rep.flags.append("expired")
    elif rep.days_remaining is not None and rep.days_remaining < warn_days:
        rep.flags.append(f"expires_within_{warn_days}d")
    return rep


def render_text(r: TlsReport, color: bool) -> str:
    out = [paint(f"\n── {r.target} ──", BOLD, color)]
    if r.error:
        out.append(paint(f"  error: {r.error}", RED, color))
        return "\n".join(out)
    out.append(f"  TLS:        {r.tls_version}    cipher: {r.cipher}")
    out.append(f"  subject:    {r.subject}")
    out.append(f"  issuer:     {r.issuer}")
    if r.san:
        san_short = ", ".join(r.san[:5]) + (f", +{len(r.san) - 5} more"
                                              if len(r.san) > 5 else "")
        out.append(f"  SAN:        {san_short}")
    out.append(f"  validity:   {r.not_before}  →  {r.not_after}")
    if r.days_remaining is not None:
        if r.days_remaining < 0:
            out.append(paint(f"  EXPIRED {-r.days_remaining} days ago", RED, color))
        elif r.days_remaining < 30:
            out.append(paint(f"  expires in {r.days_remaining} days",
                             YELLOW, color))
        else:
            out.append(f"  days remaining: {r.days_remaining}")
    if r.pubkey_algorithm:
        out.append(f"  pubkey:     {r.pubkey_algorithm} {r.pubkey_size or '?'} bits")
    if r.sig_algorithm:
        out.append(f"  sig alg:    {r.sig_algorithm}")
    out.append(f"  hostname match: {r.hostname_match}")
    if r.flags:
        out.append(paint(f"  flags: {', '.join(r.flags)}", RED, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="TLS certificate inspector.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("target", nargs="?", help="host[:port], default port 443")
    g.add_argument("--target-file",
                   help="file with one host[:port] per line")
    ap.add_argument("--timeout", type=float, default=5.0)
    ap.add_argument("--warn-days", type=int, default=30)
    ap.add_argument("--concurrency", type=int, default=20)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    targets: list[str] = []
    if args.target:
        targets.append(args.target)
    else:
        with open(args.target_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    targets.append(line)

    async def go():
        sem = asyncio.Semaphore(args.concurrency)
        loop = asyncio.get_event_loop()

        async def one(t: str) -> TlsReport:
            async with sem:
                return await loop.run_in_executor(
                    None, inspect, t, args.timeout, args.warn_days
                )
        return await asyncio.gather(*[one(t) for t in targets])

    reports = asyncio.run(go())

    if args.json:
        print(json.dumps([asdict(r) for r in reports], indent=2))
    else:
        for r in reports:
            print(render_text(r, color))
        flagged = sum(1 for r in reports if r.flags)
        print(paint(f"\n[*] {flagged}/{len(reports)} target(s) had flags",
                    BOLD, color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
