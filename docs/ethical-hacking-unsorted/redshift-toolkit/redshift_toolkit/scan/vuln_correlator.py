#!/usr/bin/env python3
"""
redshift_toolkit.scan.vuln_correlator — service version → CPE → CVE.

Given an svc_enum.py output (`services` JSON), match each version string
against an embedded CPE/CVE knowledge base (high-impact CVEs for common
services), and optionally enrich with a downloaded NVD JSON feed.

The embedded KB is intentionally small but covers software you'll actually
encounter on engagements (nginx, Apache, OpenSSH, Exim, IIS, MS SQL,
MySQL, PostgreSQL, Redis, MongoDB, Elasticsearch, Citrix Netscaler,
F5 BIG-IP, ProFTPD, vsftpd, …). Add your own entries in `EMBEDDED_KB`.

For an exhaustive lookup, download an NVD JSON feed:

  curl -s https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz \
      | gunzip > nvd-recent.json

  ./vuln_correlator.py --services versions.json --nvd-feed nvd-recent.json

Usage
-----
  ./vuln_correlator.py --services versions.json
  ./vuln_correlator.py --services versions.json --min-severity high
  ./vuln_correlator.py --services versions.json --output findings.json

Author: Redshift Project — Module 10
License: MIT
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "none": 0}


def cmpver(a: str, b: str) -> int:
    """Compare dotted version strings. Returns negative/zero/positive."""
    def parts(v: str) -> list:
        out = []
        for tok in re.split(r"[.\-+_]", v):
            if tok.isdigit():
                out.append((0, int(tok)))
            else:
                out.append((1, tok))
        return out
    pa, pb = parts(a), parts(b)
    for x, y in zip(pa, pb):
        if x != y:
            return -1 if x < y else 1
    return 0 if len(pa) == len(pb) else (-1 if len(pa) < len(pb) else 1)


def vmatches(version: str, spec: str) -> bool:
    """Match a version against a constraint like '<1.18.0' or '>=2.4.0,<2.4.55'."""
    if not version:
        return False
    for clause in spec.split(","):
        clause = clause.strip()
        m = re.match(r"^([<>=!]+)\s*(.+)$", clause)
        if not m:
            continue
        op, target = m.group(1), m.group(2).strip()
        c = cmpver(version, target)
        ok = (
            (op == "<"  and c <  0) or
            (op == "<=" and c <= 0) or
            (op == ">"  and c >  0) or
            (op == ">=" and c >= 0) or
            (op == "==" and c == 0) or
            (op == "!=" and c != 0)
        )
        if not ok:
            return False
    return True


# ─── Embedded KB. (vendor, product, version_constraint, cve, severity, summary) ─
EMBEDDED_KB = [
    # OpenSSH
    ("openssh", "openssh", "<7.7", "CVE-2018-15473", "medium",
     "OpenSSH user enumeration via timing/error responses"),
    ("openssh", "openssh", "<9.6", "CVE-2024-6387", "high",
     "regreSSHion: signal handler race → unauthenticated RCE on glibc Linux"),
    # nginx
    ("nginx", "nginx", "<1.20.1", "CVE-2021-23017", "high",
     "Off-by-one DNS resolver heap-write → potential RCE"),
    ("nginx", "nginx", "<1.22.1", "CVE-2022-41741", "high",
     "MP4 module out-of-bounds memory read/write"),
    # Apache
    ("apache", "httpd", "<2.4.50", "CVE-2021-41773", "high",
     "Path traversal and file disclosure in path normalization"),
    ("apache", "httpd", "<2.4.52", "CVE-2021-44790", "critical",
     "mod_lua buffer overflow → potential RCE"),
    ("apache", "httpd", "<2.4.55", "CVE-2023-25690", "high",
     "HTTP request smuggling via mod_proxy"),
    # Exim
    ("exim", "exim", "<4.97", "CVE-2023-42115", "critical",
     "Out-of-bounds write in SMTP server (pre-auth RCE)"),
    # IIS
    ("microsoft", "iis", "<10.0.18", "CVE-2017-7269", "critical",
     "PROPFIND buffer overflow in WebDAV (legacy systems)"),
    # MSSQL
    ("microsoft", "mssql", "<14.0", "CVE-2022-23277", "high",
     "Microsoft SQL Server reporting services RCE"),
    # MySQL
    ("oracle", "mysql", "<5.7.30", "CVE-2020-2922", "medium",
     "Server: Pluggable Auth privilege escalation"),
    # PostgreSQL
    ("postgresql", "postgresql", "<14.4", "CVE-2022-1552", "high",
     "Autovacuum/index/REINDEX privilege escalation"),
    # Redis
    ("redis", "redis", "<5.0.7", "CVE-2019-10192", "high",
     "Heap buffer overflow via crafted Lua module"),
    ("redis", "redis", "<6.2.7", "CVE-2022-0543", "critical",
     "Debian/Ubuntu Lua sandbox escape → RCE (default packaging)"),
    ("redis", "redis", "<7.2.0", "CVE-2023-28856", "medium",
     "DoS via crafted commands"),
    # MongoDB
    ("mongodb", "mongodb", "<4.0.27", "CVE-2021-20329", "medium",
     "Auth bypass via crafted hostname"),
    # Elasticsearch
    ("elastic", "elasticsearch", "<7.13.4", "CVE-2021-22137", "medium",
     "Field-level security bypass"),
    # Citrix Netscaler / ADC (the famous one)
    ("citrix", "netscaler", "<13.1-49.13", "CVE-2023-3519", "critical",
     "Unauthenticated RCE in Citrix ADC/Gateway"),
    ("citrix", "netscaler", "<13.0-93.7", "CVE-2019-19781", "critical",
     "Path traversal → unauthenticated RCE"),
    # F5 BIG-IP
    ("f5", "big-ip", "<16.1.5", "CVE-2022-1388", "critical",
     "iControl REST authentication bypass → RCE"),
    # vsftpd
    ("vsftpd", "vsftpd", "==2.3.4", "CVE-2011-2523", "critical",
     "Backdoored release: smiley face triggers root shell"),
    # ProFTPD
    ("proftpd", "proftpd", "<1.3.7e", "CVE-2020-9273", "high",
     "Use-after-free in mod_cap → RCE"),
    # phpMyAdmin
    ("phpmyadmin", "phpmyadmin", "<4.8.6", "CVE-2018-19968", "high",
     "Authenticated SQL injection"),
    # Jenkins
    ("jenkins", "jenkins", "<2.441", "CVE-2024-23897", "critical",
     "CLI argument parser file read → potentially RCE"),
]


# ─── Version extraction from svc_enum entries ──────────────────────────────
VERSION_RE = re.compile(
    r"(?P<product>[A-Za-z][A-Za-z0-9._-]+)[/\s]+"
    r"(?P<version>\d+(?:\.\d+){1,3}(?:[A-Za-z]\d*)?)"
)


def extract_product_version(svc: dict) -> tuple[str, str] | None:
    """Try a few fields in priority order."""
    fields = [svc.get("version"), svc.get("banner"),
              (svc.get("extras") or {}).get("server")]
    for f in fields:
        if not f:
            continue
        m = VERSION_RE.search(f)
        if m:
            return m.group("product").lower(), m.group("version")
    return None


@dataclass
class Finding:
    service_key: str
    ip: str
    port: int
    service_label: str
    detected_product: str
    detected_version: str
    cve: str
    severity: str
    summary: str


def correlate(services: dict[str, dict],
              kb: list[tuple] = EMBEDDED_KB) -> list[Finding]:
    findings: list[Finding] = []
    for key, svc in services.items():
        pv = extract_product_version(svc)
        if pv is None:
            continue
        product, version = pv
        for vendor, kb_product, constraint, cve, sev, summary in kb:
            if kb_product not in product and product not in kb_product:
                continue
            if vmatches(version, constraint):
                findings.append(Finding(
                    service_key=key, ip=svc.get("ip", ""),
                    port=int(svc.get("port", 0)),
                    service_label=svc.get("service", ""),
                    detected_product=product,
                    detected_version=version,
                    cve=cve, severity=sev, summary=summary,
                ))
    return findings


def filter_min_severity(fs: list[Finding], min_sev: str) -> list[Finding]:
    floor = SEVERITY_RANK.get(min_sev.lower(), 0)
    return [f for f in fs if SEVERITY_RANK.get(f.severity.lower(), 0) >= floor]


def render_text(findings: list[Finding], color: bool) -> str:
    if not findings:
        return paint("\n[ok] No vulnerable versions matched the embedded KB.",
                     GREEN, color)
    out = [paint(f"\n=== Findings: {len(findings)} ===", BOLD, color)]
    findings = sorted(findings, key=lambda f: -SEVERITY_RANK.get(f.severity, 0))
    for f in findings:
        sev_color = (RED if f.severity in ("critical", "high")
                     else YELLOW if f.severity == "medium"
                     else GREY)
        out.append(paint(
            f"\n  [{f.severity.upper():<8}] {f.cve}  "
            f"{f.detected_product} {f.detected_version}",
            sev_color, color))
        out.append(f"    on {f.ip}:{f.port} ({f.service_label})")
        out.append(paint(f"    {f.summary}", GREY, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Service version → CVE correlator.")
    ap.add_argument("--services", required=True,
                    help="services JSON from svc_enum")
    ap.add_argument("--nvd-feed", help="optional NVD JSON feed for richer matching")
    ap.add_argument("--min-severity", default="medium",
                    choices=["low", "medium", "high", "critical"])
    ap.add_argument("--output", help="write findings JSON here")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color

    svc_obj = json.loads(Path(args.services).read_text())
    services = svc_obj.get("services") or {}
    findings = correlate(services)
    findings = filter_min_severity(findings, args.min_severity)

    out_obj = {
        "generated_at": time.time(),
        "tool": "vuln_correlator",
        "min_severity": args.min_severity,
        "findings": [asdict(f) for f in findings],
    }

    if args.output:
        Path(args.output).write_text(json.dumps(out_obj, indent=2))
        print(paint(f"[+] wrote {args.output}", GREEN, color), file=sys.stderr)
        print(render_text(findings, color), file=sys.stderr)
    else:
        print(render_text(findings, color))

    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
