#!/usr/bin/env python3
"""
redshift_toolkit.recon.cert_harvester — pull every certificate ever
issued for a domain from public Certificate Transparency aggregators.

Uses crt.sh as the primary source. CT logs reveal subdomains that are or
were ever served by a CA-signed cert — i.e. most production-facing
services. Often surfaces internal-looking hostnames developers didn't
realize would become public.

Usage
-----
  python3 -m redshift_toolkit.recon.cert_harvester example.com
  python3 -m redshift_toolkit.recon.cert_harvester example.com --json
  python3 -m redshift_toolkit.recon.cert_harvester example.com --include-expired

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
from dataclasses import dataclass, asdict, field

GREEN = "\033[92m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


@dataclass
class Cert:
    name_value: str
    issuer_name: str | None = None
    not_before: str | None = None
    not_after: str | None = None


@dataclass
class Report:
    target: str
    queried_at: float
    cert_count: int = 0
    unique_subdomains: list[str] = field(default_factory=list)
    issuers: dict[str, int] = field(default_factory=dict)
    sample_certs: list[Cert] = field(default_factory=list)


def http_get(host: str, path: str, timeout: float = 15.0,
             retries: int = 3) -> bytes | None:
    """Fetch with HTTPS, retrying on transient failures."""
    last_err = None
    for attempt in range(retries):
        try:
            conn = http.client.HTTPSConnection(host, timeout=timeout)
            conn.request("GET", path,
                         headers={"User-Agent": "redshift-toolkit/1.0",
                                  "Accept": "application/json"})
            r = conn.getresponse()
            data = r.read()
            conn.close()
            if r.status == 200:
                return data
            if r.status in (429, 502, 503, 504):
                time.sleep(2 ** attempt)
                continue
            return None
        except Exception as e:
            last_err = e
            time.sleep(1.5 ** attempt)
    if last_err:
        sys.stderr.write(f"[!] http_get {host}{path} failed: {last_err}\n")
    return None


def crtsh_query(domain: str, include_expired: bool = True) -> list[dict]:
    """crt.sh JSON: ?q=%25.<domain>&output=json (% is wildcard)."""
    expired = "" if include_expired else "&exclude=expired"
    path = f"/?q=%25.{urllib.parse.quote(domain)}&output=json{expired}"
    data = http_get("crt.sh", path)
    if not data:
        return []
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        # crt.sh sometimes returns NDJSON-ish output
        out = []
        for line in data.decode("utf-8", "replace").splitlines():
            line = line.strip().rstrip(",")
            if line.startswith("{") and line.endswith("}"):
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
        return out


# ─── Aggregation ────────────────────────────────────────────────────────────
def aggregate(domain: str, include_expired: bool = True) -> Report:
    rows = crtsh_query(domain, include_expired)
    rep = Report(target=domain, queried_at=time.time(), cert_count=len(rows))

    names: set[str] = set()
    issuers: dict[str, int] = {}
    samples: list[Cert] = []

    for r in rows:
        name_value = r.get("name_value") or ""
        # name_value may contain multiple newline-separated names
        for raw in name_value.splitlines():
            n = raw.strip().strip(".").lower()
            if not n or "@" in n:
                continue
            # Filter out names that aren't subdomains of target
            if n.endswith("." + domain.lower()) or n == domain.lower():
                names.add(n)

        iss = r.get("issuer_name") or ""
        issuers[iss] = issuers.get(iss, 0) + 1

        if len(samples) < 50:
            samples.append(Cert(
                name_value=name_value.replace("\n", "; "),
                issuer_name=iss,
                not_before=r.get("not_before"),
                not_after=r.get("not_after"),
            ))

    rep.unique_subdomains = sorted(names)
    rep.issuers = dict(sorted(issuers.items(), key=lambda kv: -kv[1])[:20])
    rep.sample_certs = samples
    return rep


def render_text(r: Report, color: bool) -> str:
    out = [paint(f"\n=== Cert Transparency: {r.target} ===", BOLD, color)]
    out.append(f"  certs returned: {r.cert_count}")
    out.append(f"  unique subdomains: {len(r.unique_subdomains)}")
    out.append(paint("\n  Top issuers:", BOLD, color))
    for iss, n in list(r.issuers.items())[:10]:
        out.append(f"    {n:5}  {iss}")
    out.append(paint(f"\n  Subdomains ({len(r.unique_subdomains)}):", BOLD, color))
    for s in r.unique_subdomains[:80]:
        out.append(f"    - {s}")
    if len(r.unique_subdomains) > 80:
        out.append(paint(f"    ... and {len(r.unique_subdomains) - 80} more",
                         GREY, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="CT log harvester via crt.sh")
    ap.add_argument("domain", help="target domain (e.g. example.com)")
    ap.add_argument("--include-expired", action="store_true", default=True)
    ap.add_argument("--no-include-expired", dest="include_expired",
                    action="store_false")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()

    color = sys.stdout.isatty() and not args.no_color and not args.json

    print(paint(f"[*] querying crt.sh for *.{args.domain} ...", BOLD, color),
          file=sys.stderr)
    report = aggregate(args.domain, args.include_expired)

    if args.json:
        print(json.dumps({
            "target": report.target,
            "queried_at": report.queried_at,
            "cert_count": report.cert_count,
            "issuers": report.issuers,
            "unique_subdomains": report.unique_subdomains,
            "sample_certs": [asdict(c) for c in report.sample_certs[:30]],
        }, indent=2))
    else:
        print(render_text(report, color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
