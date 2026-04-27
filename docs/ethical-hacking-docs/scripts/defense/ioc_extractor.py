#!/usr/bin/env python3
"""
ioc_extractor.py
================

Extract Indicators of Compromise (IOCs) from any text source — emails,
threat reports, blog posts, malware reports, log files.

Extracts:
  * IPv4 + IPv6 addresses (with private/loopback filtering)
  * Domains (defanged + normal)
  * URLs
  * Email addresses
  * MD5, SHA-1, SHA-256, SHA-512 hashes
  * CVE identifiers
  * Bitcoin / Monero addresses (basic patterns)
  * MITRE ATT&CK technique IDs (T1234, T1234.001)
  * File paths (Windows + POSIX, best-effort)

Defangs are normalized:
  hxxp://example[.]com  →  http://example.com
  1[.]2[.]3[.]4         →  1.2.3.4

Usage
-----
    python ioc_extractor.py report.txt
    cat threat_report.eml | python ioc_extractor.py -
    python ioc_extractor.py - --json out.json --no-private

Author: Ethical Hacking Mastery curriculum
License: Educational use
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from collections import defaultdict
from typing import Any

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("[-] rich is required: pip install rich", file=sys.stderr)
    sys.exit(1)

console = Console()


# --------------------------------------------------------------------------- #
# De-fanging — normalize obfuscated IOCs commonly found in reports
# --------------------------------------------------------------------------- #
DEFANG_REPLACEMENTS = [
    (r"\[\.\]", "."),
    (r"\[dot\]", "."),
    (r"\(\.\)", "."),
    (r"\{\.\}", "."),
    (r"\[:\]", ":"),
    (r"\[/\]", "/"),
    (r"\[at\]", "@"),
    (r"\[@\]", "@"),
    (r"hxxp", "http"),
    (r"hXXp", "http"),
    (r"meow", "http"),     # rare but seen
]


def refang(text: str) -> str:
    out = text
    for pat, repl in DEFANG_REPLACEMENTS:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out


# --------------------------------------------------------------------------- #
# Patterns
# --------------------------------------------------------------------------- #
RE_IPV4 = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}"
                     r"(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\b")

# A small but effective IPv6 regex (covers the common shapes)
RE_IPV6 = re.compile(
    r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"
    r"|\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b"
    r"|\b::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}\b"
)

RE_DOMAIN = re.compile(
    r"\b(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)\.)+"
    r"[a-zA-Z]{2,24}\b"
)
RE_URL = re.compile(r"\bhttps?://[^\s<>'\"()]+", re.IGNORECASE)
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,24}")
RE_MD5 = re.compile(r"\b[a-fA-F0-9]{32}\b")
RE_SHA1 = re.compile(r"\b[a-fA-F0-9]{40}\b")
RE_SHA256 = re.compile(r"\b[a-fA-F0-9]{64}\b")
RE_SHA512 = re.compile(r"\b[a-fA-F0-9]{128}\b")
RE_CVE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)
RE_ATTCK = re.compile(r"\bT\d{4}(?:\.\d{3})?\b")
RE_BTC = re.compile(r"\b(?:bc1[a-zA-HJ-NP-Z0-9]{25,62}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b")
RE_XMR = re.compile(r"\b4[0-9AB][0-9a-zA-Z]{93}\b")
RE_WIN_PATH = re.compile(r"[a-zA-Z]:\\[\w\\\.\-\$\(\) ]+")
RE_POSIX_PATH = re.compile(r"(?<![\w./])/(?:[\w.\-]+/)+[\w.\-]+")

NON_TLDS_TO_DROP = {"local", "localhost", "lan", "internal"}


# --------------------------------------------------------------------------- #
# Validation helpers
# --------------------------------------------------------------------------- #
def classify_ip(addr: str) -> str:
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return "invalid"
    if ip.is_loopback:
        return "loopback"
    if ip.is_private:
        return "private"
    if ip.is_link_local:
        return "link-local"
    if ip.is_multicast:
        return "multicast"
    if ip.is_reserved:
        return "reserved"
    return "public"


def is_plausible_domain(d: str) -> bool:
    if d.split(".")[-1].lower() in NON_TLDS_TO_DROP:
        return False
    # Avoid matches like 1.2.3.4 being captured as a "domain"
    if RE_IPV4.fullmatch(d):
        return False
    return True


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #
def extract(text: str, include_private: bool) -> dict[str, Any]:
    text = refang(text)

    found: dict[str, set[str]] = defaultdict(set)

    for ip in RE_IPV4.findall(text):
        cls = classify_ip(ip)
        if cls == "invalid":
            continue
        if not include_private and cls in ("loopback", "private", "link-local"):
            continue
        found[f"ipv4_{cls}"].add(ip)

    for ip in RE_IPV6.findall(text):
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            continue
        cls = classify_ip(ip)
        if not include_private and cls in ("loopback", "private", "link-local"):
            continue
        found[f"ipv6_{cls}"].add(ip)

    for url in RE_URL.findall(text):
        url = url.rstrip(".,);]")     # trim trailing punctuation
        found["urls"].add(url)

    for email in RE_EMAIL.findall(text):
        found["emails"].add(email.lower())

    for d in RE_DOMAIN.findall(text):
        d = d.lower().rstrip(".")
        if is_plausible_domain(d):
            found["domains"].add(d)

    # Hashes — order matters (SHA512 first so longer doesn't get truncated)
    for h in RE_SHA512.findall(text):
        found["sha512"].add(h.lower())
    text_for_shorter = re.sub(RE_SHA512, "", text)
    for h in RE_SHA256.findall(text_for_shorter):
        found["sha256"].add(h.lower())
    text_for_shorter = re.sub(RE_SHA256, "", text_for_shorter)
    for h in RE_SHA1.findall(text_for_shorter):
        found["sha1"].add(h.lower())
    text_for_shorter = re.sub(RE_SHA1, "", text_for_shorter)
    for h in RE_MD5.findall(text_for_shorter):
        found["md5"].add(h.lower())

    for cve in RE_CVE.findall(text):
        found["cves"].add(cve.upper())

    for t in RE_ATTCK.findall(text):
        found["attck_techniques"].add(t)

    for addr in RE_BTC.findall(text):
        # Heuristic: legacy BTC starts with 1/3 + 25-34 chars; bech32 starts with bc1
        found["btc_addresses"].add(addr)
    for addr in RE_XMR.findall(text):
        found["xmr_addresses"].add(addr)

    for p in RE_WIN_PATH.findall(text):
        found["windows_paths"].add(p)
    for p in RE_POSIX_PATH.findall(text):
        # Avoid matching URLs again (already captured)
        if "://" not in p:
            found["posix_paths"].add(p)

    # Convert sets → sorted lists for stable output
    return {k: sorted(v) for k, v in found.items() if v}


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def render(iocs: dict[str, list[str]]) -> None:
    if not iocs:
        console.print("[yellow]No IOCs found.[/yellow]")
        return
    table = Table(title="Extracted IOCs", header_style="bold cyan", show_lines=False)
    table.add_column("Type", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Sample (first 3)", overflow="fold", style="dim")
    for k in sorted(iocs):
        v = iocs[k]
        sample = ", ".join(v[:3]) + ("…" if len(v) > 3 else "")
        table.add_row(k, str(len(v)), sample)
    console.print(table)

    console.rule("[bold]All IOCs[/bold]")
    for k in sorted(iocs):
        console.print(f"\n[bold cyan]{k}[/bold cyan] ({len(iocs[k])})")
        for item in iocs[k]:
            console.print(f"  {item}")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description="Extract IOCs from text.")
    parser.add_argument("path", help="File path, or '-' for stdin")
    parser.add_argument("--no-private", action="store_true",
                        help="Exclude private/loopback/link-local IPs")
    parser.add_argument("--json", default=None,
                        help="Also write JSON output to this file")
    args = parser.parse_args()

    if args.path == "-":
        text = sys.stdin.read()
    else:
        try:
            with open(args.path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as e:
            raise SystemExit(f"[-] Cannot open {args.path}: {e}")

    iocs = extract(text, include_private=not args.no_private)
    render(iocs)

    if args.json:
        try:
            with open(args.json, "w") as f:
                json.dump(iocs, f, indent=2)
            console.print(f"[green]Wrote {args.json}[/green]")
        except OSError as e:
            console.print(f"[red]Failed to write JSON: {e}[/red]")


if __name__ == "__main__":
    main()
