#!/usr/bin/env python3
"""Recursive secrets scanner — regex + entropy hybrid.

Walks a source tree looking for high-confidence credentials (provider
patterns) and high-entropy strings that look like secrets. Designed for
defensive AppSec / pre-commit scans.

Authorized use only: scan code you own or are reviewing with permission.

Modes
-----
- regex   : known-pattern matches (AWS keys, GH tokens, JWT, private keys)
- entropy : high-entropy substrings flagged as candidate secrets
- both    : default; combines results

Dependencies
------------
- Python 3.9+ stdlib only.

Usage
-----
    python3 sast_secrets_scan.py /path/to/repo
    python3 sast_secrets_scan.py /path/to/repo --json findings.json
    python3 sast_secrets_scan.py /path/to/repo --mode regex --min-entropy 4.5
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# --- regex catalog: provider -> pattern ----------------------------------------------------
PROVIDER_PATTERNS: dict[str, re.Pattern] = {
    "AWS Access Key ID": re.compile(r"\b(?:AKIA|ASIA|AIDA|AROA|AGPA|AIPA|ANPA|ANVA)[0-9A-Z]{16}\b"),
    "AWS Secret Access Key (heuristic)": re.compile(
        r"(?i)aws(?:.{0,20})?(?:secret|access)[\w_-]{0,5}\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?"
    ),
    "GCP Service Account JSON": re.compile(r'"type"\s*:\s*"service_account"'),
    "Azure Storage Connection String": re.compile(r"DefaultEndpointsProtocol=https?;AccountName=[^;]+;AccountKey=[^;]+"),
    "GitHub PAT (classic)": re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
    "GitHub PAT (fine-grained)": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{82}\b"),
    "GitHub OAuth": re.compile(r"\bgho_[A-Za-z0-9]{36}\b"),
    "GitHub App Token": re.compile(r"\bghs_[A-Za-z0-9]{36}\b"),
    "Slack Token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "Slack Webhook": re.compile(r"https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]{20,}"),
    "Google API Key": re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),
    "Stripe Secret Key": re.compile(r"\bsk_(?:live|test)_[0-9a-zA-Z]{24,}\b"),
    "Stripe Restricted Key": re.compile(r"\brk_(?:live|test)_[0-9a-zA-Z]{24,}\b"),
    "Twilio AccountSID": re.compile(r"\bAC[a-z0-9]{32}\b"),
    "SendGrid API Key": re.compile(r"\bSG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43}\b"),
    "Mailgun API Key": re.compile(r"\bkey-[0-9a-zA-Z]{32}\b"),
    "Heroku API Key": re.compile(r"(?i)heroku.{0,20}[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    "Private Key Header": re.compile(
        r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY-----"
    ),
    "Generic Bearer Token": re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{30,}"),
    "Postgres URL with password": re.compile(r"postgres(?:ql)?://[^:\s]+:[^@\s]+@[^/\s]+"),
    "MongoDB URL with password": re.compile(r"mongodb(?:\+srv)?://[^:\s]+:[^@\s]+@[^/\s]+"),
    "Generic Password Assignment (heuristic)": re.compile(
        r"(?i)\b(?:password|passwd|pwd|secret|token|api_key|apikey)\b\s*[:=]\s*['\"]([^'\"\s]{8,})['\"]"
    ),
}

# Skip patterns
SKIP_DIRS = {".git", ".svn", ".hg", "node_modules", ".venv", "venv", "__pycache__", ".tox", ".idea", ".vscode", "dist", "build", "target", ".next", ".cache"}
SKIP_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".pdf", ".zip", ".tar", ".gz", ".tgz", ".7z", ".rar", ".exe", ".dll", ".so", ".o", ".a", ".bin", ".dat", ".pyc", ".class", ".jar", ".woff", ".woff2", ".ttf", ".otf", ".eot", ".ico", ".mp3", ".mp4", ".webm", ".mov"}
MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB


@dataclass
class Finding:
    file: str
    line: int
    type: str  # "regex" or "entropy"
    rule: str
    snippet: str
    entropy: float = 0.0


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(s)
    h = 0.0
    for c in counts.values():
        p = c / n
        h -= p * math.log2(p)
    return h


def iter_candidate_strings(line: str, min_len: int) -> list[str]:
    """Pull out base64ish/hexish substrings."""
    rx = re.compile(r"[A-Za-z0-9+/=_\-]{%d,}" % min_len)
    return rx.findall(line)


def scan_file(path: Path, mode: str, min_entropy: float, min_len: int) -> list[Finding]:
    findings: list[Finding] = []
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return findings
        text = path.read_text(errors="replace")
    except (OSError, UnicodeError):
        return findings

    for ln, line in enumerate(text.splitlines(), start=1):
        if mode in {"regex", "both"}:
            for rule, pat in PROVIDER_PATTERNS.items():
                if pat.search(line):
                    snippet = line.strip()
                    if len(snippet) > 200:
                        snippet = snippet[:200] + "..."
                    findings.append(Finding(file=str(path), line=ln, type="regex", rule=rule, snippet=snippet))

        if mode in {"entropy", "both"}:
            for tok in iter_candidate_strings(line, min_len):
                h = shannon_entropy(tok)
                if h >= min_entropy:
                    findings.append(
                        Finding(
                            file=str(path),
                            line=ln,
                            type="entropy",
                            rule=f"high_entropy>={min_entropy}",
                            snippet=tok[:80] + ("..." if len(tok) > 80 else ""),
                            entropy=round(h, 3),
                        )
                    )
    return findings


def walk_repo(root: Path, mode: str, min_entropy: float, min_len: int) -> list[Finding]:
    out: list[Finding] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if Path(fn).suffix.lower() in SKIP_EXTS:
                continue
            full = Path(dirpath) / fn
            out.extend(scan_file(full, mode, min_entropy, min_len))
    return out


def deduplicate(findings: list[Finding]) -> list[Finding]:
    seen = set()
    out = []
    for f in findings:
        key = (f.file, f.line, f.type, f.rule, f.snippet)
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path", type=Path, help="repo root or file to scan")
    ap.add_argument("--mode", choices=["regex", "entropy", "both"], default="both")
    ap.add_argument("--min-entropy", type=float, default=4.3, help="entropy threshold (bits)")
    ap.add_argument("--min-len", type=int, default=20, help="minimum candidate-string length for entropy mode")
    ap.add_argument("--json", type=Path, default=None, help="write findings to JSON")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not args.path.exists():
        print(f"[-] path not found: {args.path}", file=sys.stderr)
        return 2

    if args.path.is_file():
        findings = scan_file(args.path, args.mode, args.min_entropy, args.min_len)
    else:
        findings = walk_repo(args.path, args.mode, args.min_entropy, args.min_len)
    findings = deduplicate(findings)

    if not args.quiet:
        for f in findings:
            extra = f"  ent={f.entropy}" if f.type == "entropy" else ""
            print(f"[{f.type}] {f.rule}: {f.file}:{f.line}{extra}\n        {f.snippet}")

    summary = {
        "total": len(findings),
        "regex_hits": sum(1 for f in findings if f.type == "regex"),
        "entropy_hits": sum(1 for f in findings if f.type == "entropy"),
        "by_rule": {},
    }
    for f in findings:
        summary["by_rule"][f.rule] = summary["by_rule"].get(f.rule, 0) + 1

    print(f"\n[+] {summary['total']} findings: {summary['regex_hits']} regex, {summary['entropy_hits']} entropy")

    if args.json:
        args.json.write_text(json.dumps({"summary": summary, "findings": [asdict(f) for f in findings]}, indent=2))
        print(f"[+] details -> {args.json}")

    return 1 if findings else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[!] interrupted", file=sys.stderr)
        sys.exit(130)
