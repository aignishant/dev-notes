#!/usr/bin/env python3
"""
hash_identifier.py
==================

Identify the algorithm(s) that may have produced a given hash string.

Use cases (defensive / authorized only):
  - Triaging password-hash dumps you obtained from your own pentest engagement
  - Identifying hashes encountered during a CTF
  - Recognizing hashes in malware static analysis (config blobs, IOC matches)
  - Developer sanity-check of which algorithm a backend is using

This is a static lexical analyzer — it does NOT crack the hash.

Usage
-----
    python hash_identifier.py 5f4dcc3b5aa765d61d8327deb882cf99
    python hash_identifier.py '$2b$12$abcdefghijklmnopqrstuv...'
    python hash_identifier.py '$argon2id$v=19$m=65536,t=3,p=4$...'
    cat hashes.txt | python hash_identifier.py -

Author: Ethical Hacking Mastery curriculum
License: Educational use
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("[-] rich is required: pip install rich", file=sys.stderr)
    sys.exit(1)

console = Console()


@dataclass(frozen=True)
class HashCandidate:
    name: str
    hashcat_mode: str | None       # for `hashcat -m N`
    john_format: str | None        # for `john --format=...`
    description: str


# --------------------------------------------------------------------------- #
# Identification rules
# --------------------------------------------------------------------------- #
HEX = r"^[a-fA-F0-9]{%d}$"
B64URL = r"^[A-Za-z0-9_\-]+={0,2}$"


def _match_prefix(s: str) -> list[HashCandidate]:
    """Modular crypt format `$id$...` and similar prefixed hashes."""
    out: list[HashCandidate] = []
    if s.startswith("$1$"):
        out.append(HashCandidate("MD5 crypt (md5crypt)", "500", "md5crypt",
                                 "Linux /etc/shadow MD5 ($1$); deprecated"))
    elif s.startswith("$2") and len(s) >= 4 and s[3] == "$":
        v = s[2]
        out.append(HashCandidate(f"bcrypt ($2{v}$)", "3200", "bcrypt",
                                 "bcrypt password hash; cost in 4th field"))
    elif s.startswith("$5$"):
        out.append(HashCandidate("SHA-256 crypt", "7400", "sha256crypt",
                                 "Linux /etc/shadow SHA-256"))
    elif s.startswith("$6$"):
        out.append(HashCandidate("SHA-512 crypt", "1800", "sha512crypt",
                                 "Linux /etc/shadow SHA-512 (modern default)"))
    elif s.startswith("$y$"):
        out.append(HashCandidate("yescrypt", None, "yescrypt",
                                 "Modern Linux /etc/shadow on some distros"))
    elif s.startswith("$argon2"):
        out.append(HashCandidate("Argon2 (id/i/d)", None, "argon2",
                                 "Memory-hard PHC winner (Argon2id is preferred)"))
    elif s.startswith("$pbkdf2"):
        out.append(HashCandidate("PBKDF2 (PHC format)", "10900", "pbkdf2",
                                 "Iterated SHA-2 / SHA-1; widely used"))
    elif s.startswith("$scrypt$") or s.startswith("$7$"):
        out.append(HashCandidate("scrypt", "8900", "scrypt",
                                 "Memory-hard KDF"))
    elif s.startswith("{SSHA}") or s.startswith("{SHA}") or s.startswith("{MD5}"):
        out.append(HashCandidate("LDAP base64-wrapped hash", None, None,
                                 "OpenLDAP-style base64 wrapper"))
    elif s.startswith("$P$") or s.startswith("$H$"):
        out.append(HashCandidate("phpass (Wordpress / phpBB / Joomla)",
                                 "400", "phpass",
                                 "PHP portable password hash"))
    elif s.startswith("$apr1$"):
        out.append(HashCandidate("Apache MD5 (apr1)", "1600", "md5crypt",
                                 "htpasswd default"))
    elif s.startswith("$NT$"):
        out.append(HashCandidate("NT hash (with $NT$ prefix)", "1000", "nt",
                                 "Windows NT hash, MD4(UTF-16-LE(password))"))
    return out


def _match_jwt(s: str) -> list[HashCandidate]:
    if s.count(".") == 2:
        parts = s.split(".")
        if all(re.match(B64URL, p) for p in parts if p):
            return [HashCandidate(
                "JWT (JSON Web Token)", "16500", None,
                "header.payload.signature in base64url; use jwt_analyzer.py for deep analysis",
            )]
    return []


def _match_hex(s: str) -> list[HashCandidate]:
    """Plain hex hashes — disambiguate by length."""
    if not re.match(r"^[a-fA-F0-9]+$", s):
        return []
    n = len(s)
    cands: list[HashCandidate] = []
    if n == 32:
        cands += [
            HashCandidate("MD5",       "0",     "raw-md5",
                          "Cryptographically broken; still seen in legacy systems"),
            HashCandidate("NTLM (NT hash)", "1000", "nt",
                          "Windows NT hash; same length as MD5 — context matters"),
            HashCandidate("MD4",       "900",   "raw-md4",
                          "Older than MD5; underlies NT hash"),
            HashCandidate("LM hash (half)", "3000", "lm",
                          "Two 16-char halves; full LM is 32 hex"),
        ]
    elif n == 40:
        cands += [
            HashCandidate("SHA-1",     "100",   "raw-sha1",
                          "Broken (SHAttered, 2017); avoid for new systems"),
            HashCandidate("RIPEMD-160", "6000", "ripemd160", "Used in some crypto contexts"),
        ]
    elif n == 56:
        cands.append(HashCandidate("SHA-224", "1300", "raw-sha224", ""))
    elif n == 64:
        cands += [
            HashCandidate("SHA-256",   "1400",  "raw-sha256", "Modern, recommended for hashing"),
            HashCandidate("SHA3-256",  "17400", "raw-sha3",   "Keccak / SHA-3"),
            HashCandidate("BLAKE2s-256", None,  "blake2s",    ""),
        ]
    elif n == 96:
        cands.append(HashCandidate("SHA-384", "10800", "raw-sha384", ""))
    elif n == 128:
        cands += [
            HashCandidate("SHA-512",   "1700",  "raw-sha512", "Modern"),
            HashCandidate("Whirlpool", "6100",  "whirlpool",  ""),
            HashCandidate("BLAKE2b-512", "600", "blake2b",    ""),
        ]
    return cands


def identify(s: str) -> list[HashCandidate]:
    s = s.strip()
    if not s:
        return []

    # Try richer formats first
    matches = _match_prefix(s)
    if matches:
        return matches

    matches = _match_jwt(s)
    if matches:
        return matches

    # MySQL hashes (start with *)
    if s.startswith("*") and len(s) == 41 and re.match(r"^\*[a-fA-F0-9]{40}$", s):
        return [HashCandidate("MySQL 4.1+ password hash", "300", "mysql-sha1",
                              "SHA1(SHA1(password)) — used by mysql.user.password")]

    # Cisco $9$ / $8$ / type 7
    if s.startswith("$9$"):
        return [HashCandidate("Cisco IOS Type 9 (scrypt)", "9300", None, "")]
    if s.startswith("$8$"):
        return [HashCandidate("Cisco IOS Type 8 (PBKDF2-SHA-256)", "9200", None, "")]

    # Hex fallback
    matches = _match_hex(s)
    if matches:
        return matches

    return []


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _print_results(hash_str: str, candidates: list[HashCandidate]) -> None:
    console.rule(f"[bold cyan]{hash_str[:120]}{'…' if len(hash_str) > 120 else ''}")

    if not candidates:
        console.print("[red]✗ No confident match.[/red] "
                      "Hint: try removing surrounding quotes / whitespace, "
                      "or check whether it's a custom encoding.")
        return

    table = Table(show_lines=False, header_style="bold cyan")
    table.add_column("Likely algorithm")
    table.add_column("hashcat -m", justify="right")
    table.add_column("john --format")
    table.add_column("Note", overflow="fold")
    for c in candidates:
        table.add_row(
            c.name,
            c.hashcat_mode or "-",
            c.john_format or "-",
            c.description,
        )
    console.print(table)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Identify likely hash algorithm(s) for a given string.",
    )
    parser.add_argument("hash", nargs="?",
                        help="Hash string to identify, or '-' to read from stdin")
    args = parser.parse_args()

    if args.hash is None:
        parser.print_help()
        sys.exit(0)

    if args.hash == "-":
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            _print_results(line, identify(line))
    else:
        _print_results(args.hash, identify(args.hash))


if __name__ == "__main__":
    main()
