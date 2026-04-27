#!/usr/bin/env python3
"""
redshift_toolkit.utils.hash_identifier — identify hash type and emit the
right Hashcat / John the Ripper mode/format for cracking.

Better than `hashid` for offensive workflows because:
  - It returns the *most likely* candidate first, not 30 false positives.
  - It outputs both Hashcat (-m N) and John (--format) flags.
  - It has explicit support for prefix-tagged formats (bcrypt $2*, scrypt
    $7$, Argon2 $argon2*, MD5(unix) $1$, SHA-512 crypt $6$, NTLM, NetNTLMv2,
    Kerberos, JWT, Django, Wordpress, vBulletin, etc.).
  - It can identify multiple hashes at once from a file.

Usage
-----
  python3 -m redshift_toolkit.utils.hash_identifier '5f4dcc3b5aa765d61d8327deb882cf99'
  python3 -m redshift_toolkit.utils.hash_identifier --file hashes.txt
  python3 -m redshift_toolkit.utils.hash_identifier --hash '$1$abc$...' --json

Author: Redshift Project — Module 07
License: MIT
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict

GREEN = "\033[92m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass
class Match:
    name: str
    hashcat_mode: int | None
    john_format: str | None
    confidence: str  # "high" | "medium" | "low"
    note: str = ""


# (regex, name, -m mode, --format, confidence, note)
PREFIXED = [
    (r"^\$1\$[^$]{1,8}\$[A-Za-z0-9./]{22}$", "MD5-Crypt (Unix /etc/shadow $1$)",
     500, "md5crypt", "high", ""),
    (r"^\$2[abxy]?\$\d{2}\$[A-Za-z0-9./]{53}$", "bcrypt",
     3200, "bcrypt", "high", ""),
    (r"^\$5\$(rounds=\d+\$)?[^$]{1,16}\$[A-Za-z0-9./]{43}$", "SHA-256 Crypt",
     7400, "sha256crypt", "high", ""),
    (r"^\$6\$(rounds=\d+\$)?[^$]{1,16}\$[A-Za-z0-9./]{86}$", "SHA-512 Crypt",
     1800, "sha512crypt", "high", ""),
    (r"^\$7\$.{11,}$", "scrypt",
     8900, "scrypt", "high", ""),
    (r"^\$argon2(i|d|id)\$.+$", "Argon2",
     None, "argon2", "high", "Hashcat support requires recent build"),
    (r"^\$pbkdf2-sha256\$\d+\$[A-Za-z0-9+/=]+\$[A-Za-z0-9+/=]+$",
     "PBKDF2-SHA256 (passlib)",
     10900, "pbkdf2-hmac-sha256", "high", ""),
    (r"^\$pbkdf2-sha512\$\d+\$[A-Za-z0-9+/=]+\$[A-Za-z0-9+/=]+$",
     "PBKDF2-SHA512 (passlib)",
     12100, None, "high", ""),
    (r"^\$P\$[A-Za-z0-9./]{31}$", "phpass / WordPress",
     400, "phpass", "high", ""),
    (r"^\$H\$[A-Za-z0-9./]{31}$", "phpass (vBulletin/joomla variant)",
     400, "phpass", "high", ""),
    (r"^pbkdf2_sha256\$\d+\$[A-Za-z0-9+/=]+\$[A-Za-z0-9+/=]+$",
     "Django PBKDF2-SHA256",
     10000, "django", "high", ""),
    (r"^\$krb5asrep\$23\$.+", "Kerberos AS-REP (RC4)",
     18200, "krb5asrep", "high", "AS-REP roastable account"),
    (r"^\$krb5tgs\$23\$.+", "Kerberos TGS (RC4)",
     13100, "krb5tgs", "high", "Kerberoastable"),
    (r"^\$krb5tgs\$17\$.+", "Kerberos TGS (AES-128)",
     19600, None, "high", ""),
    (r"^\$krb5tgs\$18\$.+", "Kerberos TGS (AES-256)",
     19700, None, "high", ""),
    (r"^[a-fA-F0-9]{32}:[a-fA-F0-9]{32}$", "LM:NTLM (split LM:NT)",
     1000, "NT", "high", "(NT half is mode 1000)"),
    (r"^[^:]+::[^:]+:[a-fA-F0-9]{16}:[a-fA-F0-9]{32}:[a-fA-F0-9]+$",
     "NetNTLMv1",
     5500, "netntlm", "high", ""),
    (r"^[^:]+::[^:]+:[a-fA-F0-9]{16}:[a-fA-F0-9]{32}:[a-fA-F0-9]+$",
     "NetNTLMv1 (alt)", 5500, "netntlm", "low", ""),
    (r"^[^:]+::[^:]+:[a-fA-F0-9]+:[a-fA-F0-9]{32}:[a-fA-F0-9]+$",
     "NetNTLMv2", 5600, "netntlmv2", "high", ""),
    (r"^eyJ[A-Za-z0-9_=-]+\.eyJ[A-Za-z0-9_=-]+\.[A-Za-z0-9_=-]+$",
     "JSON Web Token",
     16500, None, "high", "Use jwt_tool.brute for HS256/384/512"),
    (r"^SCRYPT:\d+:\d+:\d+:[A-Za-z0-9+/=]+:[A-Za-z0-9+/=]+$",
     "scrypt (cisco/lib variant)", 8900, "scrypt", "medium", ""),
]

# Length-based candidates for raw hex hashes.
RAW_HEX_CANDIDATES = {
    32: [
        Match("MD5", 0, "raw-md5", "high"),
        Match("MD4", 900, "raw-md4", "low"),
        Match("NTLM (NT-only)", 1000, "NT", "high",
              note="If from secretsdump or NTDS dump"),
        Match("LM (single-part LANMAN hash)", 3000, "LM", "low"),
    ],
    40: [
        Match("SHA-1", 100, "raw-sha1", "high"),
        Match("RIPEMD-160", 6000, "ripemd160", "low"),
    ],
    56: [
        Match("SHA-224", 1300, "raw-sha224", "medium"),
    ],
    64: [
        Match("SHA-256", 1400, "raw-sha256", "high"),
        Match("BLAKE2b-256", None, None, "low"),
        Match("Keccak-256", None, "raw-keccak-256", "low"),
    ],
    96: [
        Match("SHA-384", 10800, "raw-sha384", "medium"),
    ],
    128: [
        Match("SHA-512", 1700, "raw-sha512", "high"),
        Match("Whirlpool", 6100, "whirlpool", "low"),
    ],
}


def identify(h: str) -> list[Match]:
    h = h.strip()
    out: list[Match] = []

    # Prefix-tagged formats first
    for pattern, name, mode, fmt, conf, note in PREFIXED:
        if re.match(pattern, h):
            out.append(Match(name=name, hashcat_mode=mode, john_format=fmt,
                             confidence=conf, note=note))

    # Bare hex hash → length-based candidates
    if re.match(r"^[a-fA-F0-9]+$", h):
        candidates = RAW_HEX_CANDIDATES.get(len(h), [])
        out.extend(candidates)

    # Salted MD5 / SHA1 forms (hash:salt or hash$salt)
    if re.match(r"^[a-fA-F0-9]{32}[:$].+$", h):
        out.append(Match("md5(pass.salt) / md5(salt.pass)", 10, "dynamic_*",
                         "medium", note="try multiple modes: 10, 20, 30, 40"))
    if re.match(r"^[a-fA-F0-9]{40}[:$].+$", h):
        out.append(Match("sha1(pass.salt) variants", 110, "dynamic_*",
                         "medium", note="try modes 110, 120, 130, 140"))

    # Apache APR1 (md5-based)
    if h.startswith("$apr1$"):
        out.append(Match("Apache APR1 (md5)", 1600, "md5apr1", "high"))

    # Cisco type 7 (weak XOR)
    if re.match(r"^[0-9]{2}[A-F0-9]+$", h.upper()):
        out.append(Match("Cisco Type 7 (reversible XOR)", None, None,
                         "low", note="not a real hash; reversible without cracking"))

    return out


def render_text(h: str, matches: list[Match], color: bool) -> str:
    on = color
    out = [paint(f"\n=== Hash: {h[:60]}{'…' if len(h) > 60 else ''}", BOLD, on),
           paint(f"  length: {len(h)}", GREY, on)]
    if not matches:
        out.append(paint("  no candidates matched", YELLOW, on))
        return "\n".join(out)
    for i, m in enumerate(matches, 1):
        cmark = (GREEN if m.confidence == "high"
                 else YELLOW if m.confidence == "medium"
                 else GREY)
        mode = f"-m {m.hashcat_mode}" if m.hashcat_mode is not None else "-m ?"
        fmt = f"--format={m.john_format}" if m.john_format else "--format=?"
        out.append(paint(f"  {i}. {m.name}  [{m.confidence}]", cmark, on))
        out.append(f"     hashcat: {mode}    |    john: {fmt}")
        if m.note:
            out.append(paint(f"     note: {m.note}", GREY, on))
    return "\n".join(out)


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


def main() -> int:
    ap = argparse.ArgumentParser(description="Identify hash type and crack mode.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("hash", nargs="?", help="single hash string")
    g.add_argument("--file", help="file with one hash per line")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    hashes: list[str] = []
    if args.hash:
        hashes.append(args.hash)
    else:
        with open(args.file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    hashes.append(line)

    if args.json:
        out = []
        for h in hashes:
            out.append({
                "hash": h,
                "length": len(h),
                "candidates": [asdict(m) for m in identify(h)],
            })
        print(json.dumps(out, indent=2))
    else:
        for h in hashes:
            print(render_text(h, identify(h), color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
