#!/usr/bin/env python3
"""
redshift_toolkit.recon.wayback_paths — pull every URL ever archived for
a domain from the Internet Archive Wayback Machine, then mine them for
useful intel.

What it produces
----------------
- Unique URL list (every URL the Wayback Machine ever crawled).
- Per-extension counts (.json, .php, .config, .bak, .pdf, .xml, …).
- Unique query parameters across all URLs (often reveal hidden APIs).
- Subdomains discovered along the way.
- Suspicious paths (e.g. `/admin`, `/.git`, `/swagger`, `/api`).

Usage
-----
  python3 -m redshift_toolkit.recon.wayback_paths example.com
  python3 -m redshift_toolkit.recon.wayback_paths example.com --json
  python3 -m redshift_toolkit.recon.wayback_paths example.com \\
        --max-urls 50000 --filter '\\.(json|php|env|bak|config)'

Author: Redshift Project — Module 09
License: MIT
"""

from __future__ import annotations

import argparse
import http.client
import json
import re
import sys
import time
import urllib.parse
from collections import Counter
from dataclasses import dataclass, field, asdict

GREEN = "\033[92m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


SUSPICIOUS_PATH_TOKENS = (
    "admin", "login", ".git", ".svn", ".env", "backup", "debug",
    "swagger", "api-docs", "graphql", "phpinfo", "config",
    "actuator", ".bak", ".old", "wp-admin", "test", "private",
    "internal", ".aws", ".ssh", "metadata",
)

EXT_RE = re.compile(r"\.(\w{1,8})($|\?)")


@dataclass
class Report:
    target: str
    queried_at: float
    total_records: int = 0
    unique_urls: list[str] = field(default_factory=list)
    extensions: dict[str, int] = field(default_factory=dict)
    query_params: list[str] = field(default_factory=list)
    discovered_subdomains: list[str] = field(default_factory=list)
    suspicious_paths: list[str] = field(default_factory=list)


def cdx_query(domain: str, max_urls: int, timeout: float = 60.0) -> list[str]:
    """The CDX API: text format is fastest for our purposes."""
    qs = urllib.parse.urlencode({
        "url": f"*.{domain}/*",
        "output": "txt",
        "fl": "original",
        "collapse": "urlkey",
        "limit": str(max_urls),
    })
    path = f"/cdx/search/cdx?{qs}"
    conn = http.client.HTTPSConnection("web.archive.org", timeout=timeout)
    try:
        conn.request("GET", path,
                     headers={"User-Agent": "redshift-toolkit/1.0"})
        r = conn.getresponse()
        data = r.read()
        if r.status != 200:
            return []
        return [line.strip() for line in data.decode("utf-8", "replace").splitlines() if line.strip()]
    finally:
        conn.close()


def analyze(domain: str, urls: list[str], filter_re: re.Pattern | None) -> Report:
    rep = Report(target=domain, queried_at=time.time(),
                 total_records=len(urls))
    seen_urls: set[str] = set()
    extensions: Counter[str] = Counter()
    params: set[str] = set()
    subdomains: set[str] = set()
    suspicious: list[str] = []

    for u in urls:
        if filter_re and not filter_re.search(u):
            continue
        seen_urls.add(u)

        try:
            parts = urllib.parse.urlparse(u)
        except ValueError:
            continue

        host = parts.netloc.lower().split(":")[0]
        if host.endswith("." + domain.lower()) or host == domain.lower():
            subdomains.add(host)

        m = EXT_RE.search(parts.path)
        if m:
            ext = m.group(1).lower()
            if 1 <= len(ext) <= 8 and not ext.isdigit():
                extensions[ext] += 1

        for q in parts.query.split("&"):
            if "=" in q:
                params.add(q.split("=", 1)[0])

        path_low = parts.path.lower()
        if any(tok in path_low for tok in SUSPICIOUS_PATH_TOKENS):
            suspicious.append(u)

    rep.unique_urls = sorted(seen_urls)
    rep.extensions = dict(extensions.most_common(50))
    rep.query_params = sorted(params)
    rep.discovered_subdomains = sorted(subdomains)
    rep.suspicious_paths = suspicious[:200]
    return rep


def render_text(r: Report, color: bool) -> str:
    out = [paint(f"\n=== Wayback paths: {r.target} ===", BOLD, color),
           f"  records returned: {r.total_records}",
           f"  unique URLs (after filter): {len(r.unique_urls)}",
           f"  unique subdomains: {len(r.discovered_subdomains)}",
           f"  unique query params: {len(r.query_params)}"]

    if r.discovered_subdomains:
        out.append(paint("\n  Subdomains:", BOLD, color))
        for s in r.discovered_subdomains[:30]:
            out.append(f"    - {s}")

    if r.extensions:
        out.append(paint("\n  Top extensions:", BOLD, color))
        for ext, n in list(r.extensions.items())[:20]:
            out.append(f"    .{ext:<8} {n}")

    if r.query_params:
        out.append(paint("\n  Distinct query params (first 40):", BOLD, color))
        out.append("    " + ", ".join(r.query_params[:40]))

    if r.suspicious_paths:
        out.append(paint(f"\n  Suspicious paths: {len(r.suspicious_paths)}",
                         BOLD, color))
        for u in r.suspicious_paths[:25]:
            out.append(f"    - {u}")

    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Wayback Machine URL extractor.")
    ap.add_argument("domain")
    ap.add_argument("--max-urls", type=int, default=20000)
    ap.add_argument("--filter", help="optional regex to filter URLs")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()

    color = sys.stdout.isatty() and not args.no_color and not args.json
    filt = re.compile(args.filter) if args.filter else None

    print(paint(f"[*] querying Wayback CDX for *.{args.domain}/*",
                BOLD, color), file=sys.stderr)
    urls = cdx_query(args.domain, args.max_urls)
    print(paint(f"[*] received {len(urls)} URL records",
                GREY, color), file=sys.stderr)

    rep = analyze(args.domain, urls, filt)

    if args.json:
        print(json.dumps(asdict(rep), indent=2))
    else:
        print(render_text(rep, color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
