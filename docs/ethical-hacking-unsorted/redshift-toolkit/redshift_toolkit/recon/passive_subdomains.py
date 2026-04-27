#!/usr/bin/env python3
"""
redshift_toolkit.recon.passive_subdomains — multi-source passive subdomain
aggregator. Combines:

- crt.sh (Certificate Transparency)
- HackerTarget hostsearch
- AlienVault OTX passive DNS
- Optional: VirusTotal v3 (requires VT_API_KEY env var)

Produces a deduped, sorted list of subdomains.

No third-party Python deps — uses stdlib http.client.

Usage
-----
  python3 -m redshift_toolkit.recon.passive_subdomains example.com
  python3 -m redshift_toolkit.recon.passive_subdomains example.com --json
  python3 -m redshift_toolkit.recon.passive_subdomains example.com \\
      --no-otx --no-hackertarget

Author: Redshift Project — Module 11
License: MIT
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import sys
import time
import urllib.parse
from dataclasses import dataclass, field, asdict

GREEN = "\033[92m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


@dataclass
class Source:
    name: str
    count: int = 0
    error: str | None = None


@dataclass
class Report:
    target: str
    sources: list[Source] = field(default_factory=list)
    subdomains: list[str] = field(default_factory=list)
    by_source: dict[str, list[str]] = field(default_factory=dict)


def _https(host: str, path: str, timeout: float = 15.0,
           headers: dict | None = None) -> bytes | None:
    h = {"User-Agent": "redshift-toolkit/1.0", "Accept": "*/*"}
    if headers:
        h.update(headers)
    try:
        c = http.client.HTTPSConnection(host, timeout=timeout)
        c.request("GET", path, headers=h)
        r = c.getresponse()
        body = r.read()
        c.close()
        if r.status >= 400:
            return None
        return body
    except Exception:
        return None


def from_crtsh(domain: str) -> tuple[set[str], str | None]:
    body = _https("crt.sh",
                  f"/?q=%25.{urllib.parse.quote(domain)}&output=json")
    if not body:
        return set(), "no response"
    try:
        rows = json.loads(body)
    except json.JSONDecodeError:
        rows = []
        for line in body.decode("utf-8", "replace").splitlines():
            line = line.strip().rstrip(",")
            if line.startswith("{") and line.endswith("}"):
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    out: set[str] = set()
    for r in rows:
        for n in (r.get("name_value") or "").splitlines():
            n = n.strip().lower().strip(".")
            if not n or "@" in n or "*" in n:
                continue
            if n.endswith("." + domain) or n == domain:
                out.add(n)
    return out, None


def from_hackertarget(domain: str) -> tuple[set[str], str | None]:
    body = _https("api.hackertarget.com", f"/hostsearch/?q={domain}")
    if not body:
        return set(), "no response"
    out: set[str] = set()
    for line in body.decode("utf-8", "replace").splitlines():
        if "," in line:
            host = line.split(",", 1)[0].strip().lower()
            if host and (host.endswith("." + domain) or host == domain):
                out.add(host)
    return out, None


def from_otx(domain: str) -> tuple[set[str], str | None]:
    body = _https("otx.alienvault.com",
                  f"/api/v1/indicators/domain/{urllib.parse.quote(domain)}/passive_dns")
    if not body:
        return set(), "no response"
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return set(), "non-json"
    out: set[str] = set()
    for rec in data.get("passive_dns") or []:
        host = (rec.get("hostname") or "").strip().lower().rstrip(".")
        if host and (host.endswith("." + domain) or host == domain):
            out.add(host)
    return out, None


def from_virustotal(domain: str, api_key: str) -> tuple[set[str], str | None]:
    out: set[str] = set()
    cursor = ""
    for _ in range(5):
        path = f"/api/v3/domains/{urllib.parse.quote(domain)}/subdomains?limit=40"
        if cursor:
            path += f"&cursor={cursor}"
        body = _https("www.virustotal.com", path,
                      headers={"x-apikey": api_key})
        if not body:
            return out, "no response"
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return out, "non-json"
        for rec in data.get("data") or []:
            host = (rec.get("id") or "").strip().lower()
            if host and host.endswith(domain):
                out.add(host)
        cursor = ((data.get("meta") or {}).get("cursor") or "").strip()
        if not cursor:
            break
        time.sleep(0.4)
    return out, None


def aggregate(domain: str, use_crtsh: bool = True,
              use_hackertarget: bool = True,
              use_otx: bool = True,
              use_vt: bool = True) -> Report:
    rep = Report(target=domain)
    if use_crtsh:
        s, err = from_crtsh(domain)
        rep.sources.append(Source("crt.sh", len(s), err))
        rep.by_source["crt.sh"] = sorted(s)
    if use_hackertarget:
        s, err = from_hackertarget(domain)
        rep.sources.append(Source("hackertarget", len(s), err))
        rep.by_source["hackertarget"] = sorted(s)
    if use_otx:
        s, err = from_otx(domain)
        rep.sources.append(Source("otx", len(s), err))
        rep.by_source["otx"] = sorted(s)
    if use_vt:
        api_key = os.environ.get("VT_API_KEY")
        if api_key:
            s, err = from_virustotal(domain, api_key)
            rep.sources.append(Source("virustotal", len(s), err))
            rep.by_source["virustotal"] = sorted(s)

    merged: set[str] = set()
    for s in rep.by_source.values():
        merged.update(s)
    rep.subdomains = sorted(merged)
    return rep


def render_text(rep: Report, color: bool) -> str:
    out = [paint(f"\n=== Passive subdomains: {rep.target} ===", BOLD, color)]
    for s in rep.sources:
        sc = (GREEN if s.count else GREY) if not s.error else YELLOW
        out.append(paint(
            f"  {s.name:<14} {s.count:>5}" + (f"  ({s.error})" if s.error else ""),
            sc, color))
    out.append(paint(f"\n  unique merged: {len(rep.subdomains)}", BOLD, color))
    for n in rep.subdomains[:80]:
        out.append(f"    - {n}")
    if len(rep.subdomains) > 80:
        out.append(paint(f"    ... and {len(rep.subdomains) - 80} more",
                         GREY, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Passive subdomain aggregator across public sources.")
    ap.add_argument("domain")
    ap.add_argument("--no-crtsh", action="store_true")
    ap.add_argument("--no-hackertarget", action="store_true")
    ap.add_argument("--no-otx", action="store_true")
    ap.add_argument("--no-vt", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    rep = aggregate(args.domain,
                    use_crtsh=not args.no_crtsh,
                    use_hackertarget=not args.no_hackertarget,
                    use_otx=not args.no_otx,
                    use_vt=not args.no_vt)
    if args.json:
        print(json.dumps(asdict(rep), indent=2))
    else:
        print(render_text(rep, color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
