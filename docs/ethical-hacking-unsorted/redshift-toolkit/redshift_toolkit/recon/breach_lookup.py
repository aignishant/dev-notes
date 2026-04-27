#!/usr/bin/env python3
"""
redshift_toolkit.recon.breach_lookup — local breach-corpus query using
SHA-1 prefix indexing (HaveIBeenPwned-style, offline).

Why local
---------
Querying public breach APIs leaks the targets of your engagement to the
API operator. For ethically constrained engagements you need a workflow
that stays on your machine.

Storage layout (the corpus is just a directory of files):

  corpus/
    AAAAA.txt        # SHA-1 hashes starting with this 5-char prefix
    AAAAB.txt
    ...

Each line of a prefix file is the *remaining 35 hex chars* of the hash
plus an optional `:count` suffix. This matches HIBP's published format
exactly, so a downloaded HIBP NTLM/SHA1 password database fits the
schema as-is.

What this script does
---------------------
- `--check-email alice@target.com`   → SHA-1 of email → look up in corpus.
- `--check-password 'Hunter2'`        → SHA-1 of password → look up.
- `--check-file emails.txt`           → bulk check.

The shipped tiny demo corpus (`demo_corpus/`) contains the SHA-1 of
the literal string "password" and a few common test passwords, so the
workflow is verifiable without downloading 12 GB of HIBP data.

Usage
-----
  python3 -m redshift_toolkit.recon.breach_lookup \\
      --corpus demo_corpus --check-password 'password'
  python3 -m redshift_toolkit.recon.breach_lookup \\
      --corpus /opt/hibp --check-file emails.txt --json

Author: Redshift Project — Module 09
License: MIT — Authorized testing only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


@dataclass
class CheckResult:
    input: str
    kind: str           # email | password | hash
    sha1: str
    found: bool
    occurrences: int | None = None


@dataclass
class Report:
    corpus: str
    total_checked: int = 0
    found_count: int = 0
    results: list[CheckResult] = field(default_factory=list)


def sha1_hex(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest().upper()


def lookup(sha1: str, corpus_dir: Path) -> tuple[bool, int | None]:
    sha1 = sha1.upper()
    prefix = sha1[:5]
    suffix = sha1[5:]
    pfile = corpus_dir / f"{prefix}.txt"
    if not pfile.exists():
        return False, None
    try:
        with pfile.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if ":" in line:
                    h, count = line.split(":", 1)
                    count = count.strip()
                else:
                    h, count = line, None
                if h.upper() == suffix:
                    try:
                        return True, int(count) if count else None
                    except ValueError:
                        return True, None
    except OSError:
        pass
    return False, None


def check_email(corpus: Path, addr: str) -> CheckResult:
    h = sha1_hex(addr.strip().lower())
    found, count = lookup(h, corpus)
    return CheckResult(addr, "email", h, found, count)


def check_password(corpus: Path, pw: str) -> CheckResult:
    h = sha1_hex(pw)
    found, count = lookup(h, corpus)
    return CheckResult(pw, "password", h, found, count)


def check_hash(corpus: Path, h: str) -> CheckResult:
    h = h.strip().upper()
    found, count = lookup(h, corpus)
    return CheckResult(h, "hash", h, found, count)


def render_text(r: Report, color: bool, show_passwords: bool) -> str:
    out = [paint(f"\n=== Breach corpus check: {r.corpus} ===", BOLD, color),
           f"  total checked: {r.total_checked}",
           f"  matches:       {r.found_count}"]
    for c in r.results:
        if not c.found:
            out.append(paint(f"  [ ok ]  {c.kind:<8}  {c.input[:50]}",
                             GREY, color))
        else:
            shown = (c.input
                     if c.kind == "email" or show_passwords or c.kind == "hash"
                     else "*" * len(c.input))
            count = (f"  occurrences={c.occurrences}"
                     if c.occurrences is not None else "")
            out.append(paint(
                f"  [PWND]  {c.kind:<8}  {shown[:50]}{count}",
                RED, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Local breach corpus lookup.")
    ap.add_argument("--corpus", required=True,
                    help="path to corpus directory (HIBP-style prefix files)")
    ap.add_argument("--check-email", action="append", default=[])
    ap.add_argument("--check-password", action="append", default=[])
    ap.add_argument("--check-hash", action="append", default=[])
    ap.add_argument("--check-file",
                    help="file with one input per line; type inferred per line")
    ap.add_argument("--show-passwords", action="store_true",
                    help="display matched passwords in plain text (off by default)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json
    corpus = Path(args.corpus)

    if not corpus.is_dir():
        print(f"corpus dir not found: {corpus}", file=sys.stderr)
        return 2

    rep = Report(corpus=str(corpus))

    def consume(token: str) -> CheckResult | None:
        token = token.strip()
        if not token:
            return None
        if "@" in token:
            return check_email(corpus, token)
        if all(ch in "0123456789abcdefABCDEF" for ch in token) and len(token) == 40:
            return check_hash(corpus, token)
        return check_password(corpus, token)

    for e in args.check_email:
        rep.results.append(check_email(corpus, e))
    for p in args.check_password:
        rep.results.append(check_password(corpus, p))
    for h in args.check_hash:
        rep.results.append(check_hash(corpus, h))
    if args.check_file:
        with open(args.check_file) as f:
            for ln in f:
                cr = consume(ln)
                if cr:
                    rep.results.append(cr)

    rep.total_checked = len(rep.results)
    rep.found_count = sum(1 for c in rep.results if c.found)

    if args.json:
        print(json.dumps(asdict(rep), indent=2))
    else:
        print(render_text(rep, color, args.show_passwords))
    return 0


if __name__ == "__main__":
    sys.exit(main())
