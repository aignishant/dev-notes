#!/usr/bin/env python3
"""
cve_correlator.py — Map service banners to known CVEs via the NVD API,
enriched with CISA KEV (Known Exploited) and EPSS (exploit-prediction)
data.

Workflow:
  1. Read service banners as input — either from nmap XML, the
     nmap_xml_parser.py JSON output, or a manual list (`product:version`).
  2. For each (product, version), construct a CPE-style query and hit
     the NVD CVE API 2.0.
  3. Cross-reference matches against the CISA KEV catalog and the EPSS
     daily score feed.
  4. Output a prioritized JSON / table report.

Pure stdlib + httpx. No NVD API key required (unauth tier is rate-limited
to ~5 req/30s). With NVD_API_KEY set, the limit is much higher.

⚠️ AUTHORIZATION REQUIRED for the underlying scan ⚠️
This tool only queries NVD/CISA/FIRST APIs — it doesn't touch the target.
But the banners you feed it must come from authorized scans.

Usage:
    python3 cve_correlator.py --nmap-xml scan.xml
    python3 cve_correlator.py --nmap-json parsed.json
    python3 cve_correlator.py --banner "Apache httpd:2.4.49" --banner "OpenSSH:8.2p1"
    python3 cve_correlator.py --nmap-xml scan.xml --kev-only -o report.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict

import httpx

USER_AGENT = "cve-correlator/1.0 (defensive vulnerability triage)"
NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
EPSS_URL = "https://api.first.org/data/v1/epss"
TIMEOUT = httpx.Timeout(40.0, connect=15.0)


@dataclass
class Match:
    cve_id: str
    cvss_v3_score: float | None
    cvss_v3_severity: str
    cvss_vector: str
    description: str
    in_kev: bool
    epss: float | None
    references: list[str] = field(default_factory=list)


@dataclass
class BannerLookup:
    product: str
    version: str
    matches: list[Match] = field(default_factory=list)
    error: str | None = None


def fetch_kev(client: httpx.Client) -> set[str]:
    try:
        r = client.get(KEV_URL, headers={"User-Agent": USER_AGENT})
        r.raise_for_status()
        data = r.json()
        return {v.get("cveID") for v in data.get("vulnerabilities", []) if v.get("cveID")}
    except httpx.HTTPError as e:
        print(f"[!] KEV fetch failed: {e}", file=sys.stderr)
        return set()


def fetch_epss(client: httpx.Client, cve_ids: list[str]) -> dict[str, float]:
    """EPSS scores for a list of CVE IDs (max 100 per call)."""
    out: dict[str, float] = {}
    for i in range(0, len(cve_ids), 100):
        batch = cve_ids[i : i + 100]
        params = {"cve": ",".join(batch)}
        try:
            r = client.get(EPSS_URL, params=params, headers={"User-Agent": USER_AGENT})
            r.raise_for_status()
            for entry in r.json().get("data", []):
                cid = entry.get("cve")
                try:
                    out[cid] = float(entry.get("epss", 0.0))
                except (TypeError, ValueError):
                    continue
        except httpx.HTTPError as e:
            print(f"[!] EPSS batch failed: {e}", file=sys.stderr)
    return out


def query_nvd(client: httpx.Client, product: str, version: str) -> list[Match]:
    """Query NVD using a keyword search — broader than CPE matching but more forgiving."""
    headers = {"User-Agent": USER_AGENT}
    if api_key := os.getenv("NVD_API_KEY"):
        headers["apiKey"] = api_key

    keyword = f"{product} {version}".strip()
    params = {"keywordSearch": keyword, "resultsPerPage": 50}

    try:
        r = client.get(NVD_API, params=params, headers=headers)
    except httpx.HTTPError as e:
        return []

    if r.status_code == 403:
        time.sleep(6)
        r = client.get(NVD_API, params=params, headers=headers)
    if r.status_code != 200:
        return []

    matches: list[Match] = []
    data = r.json()
    for vuln in data.get("vulnerabilities", []):
        cve = vuln.get("cve", {})
        cve_id = cve.get("id", "")
        descs = cve.get("descriptions", [])
        description = next((d.get("value", "") for d in descs if d.get("lang") == "en"), "")

        metrics = cve.get("metrics", {})
        cvss_score: float | None = None
        cvss_severity = ""
        cvss_vector = ""
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            entries = metrics.get(key) or []
            if entries:
                d = entries[0].get("cvssData", {})
                cvss_score = d.get("baseScore")
                cvss_severity = d.get("baseSeverity") or entries[0].get("baseSeverity") or ""
                cvss_vector = d.get("vectorString", "")
                break

        refs = [ref.get("url") for ref in cve.get("references", []) if ref.get("url")][:5]

        matches.append(
            Match(
                cve_id=cve_id,
                cvss_v3_score=cvss_score,
                cvss_v3_severity=cvss_severity,
                cvss_vector=cvss_vector,
                description=(description[:300] + "...") if len(description) > 300 else description,
                in_kev=False,
                epss=None,
                references=refs,
            )
        )
    # Crude post-filter: ensure version string appears in description for relevance
    if version:
        matches = [m for m in matches if version in m.description or re.search(re.escape(version), m.description)] or matches
    return matches


def banners_from_nmap_xml(path: str) -> list[tuple[str, str]]:
    tree = ET.parse(path)
    root = tree.getroot()
    out: list[tuple[str, str]] = []
    for svc in root.findall(".//service"):
        product = svc.get("product", "").strip()
        version = svc.get("version", "").strip()
        if product:
            out.append((product, version))
    return out


def banners_from_nmap_json(path: str) -> list[tuple[str, str]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    out: list[tuple[str, str]] = []
    for host in data.get("hosts", []):
        for port in host.get("ports", []):
            svc = port.get("service", {}) or {}
            product = (svc.get("product") or "").strip()
            version = (svc.get("version") or "").strip()
            if product:
                out.append((product, version))
    return out


def parse_manual_banners(items: list[str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for raw in items:
        if ":" in raw:
            product, version = raw.split(":", 1)
            out.append((product.strip(), version.strip()))
        else:
            out.append((raw.strip(), ""))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--nmap-xml", help="nmap XML output to read banners from")
    src.add_argument("--nmap-json", help="nmap_xml_parser.py JSON output")
    src.add_argument("--banner", action="append", help="Manual banner: product:version (repeatable)")
    p.add_argument("--kev-only", action="store_true", help="Filter to CVEs on the CISA KEV list")
    p.add_argument("--min-cvss", type=float, default=0.0, help="Minimum CVSS score (default: 0.0)")
    p.add_argument("-o", "--output", help="Write JSON report to file")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress progress messages")
    args = p.parse_args()

    if args.nmap_xml:
        banners = banners_from_nmap_xml(args.nmap_xml)
    elif args.nmap_json:
        banners = banners_from_nmap_json(args.nmap_json)
    else:
        banners = parse_manual_banners(args.banner or [])

    if not banners:
        print("[-] No banners found.", file=sys.stderr)
        return 2

    # Dedupe
    banners = sorted(set(banners))
    if not args.quiet:
        print(f"[*] {len(banners)} unique banners to look up.", file=sys.stderr)

    with httpx.Client(timeout=TIMEOUT, http2=False) as client:
        if not args.quiet:
            print("[*] Fetching CISA KEV...", file=sys.stderr)
        kev_set = fetch_kev(client)

        results: list[BannerLookup] = []
        for product, version in banners:
            if not args.quiet:
                print(f"[*] NVD: {product} {version}", file=sys.stderr)
            try:
                matches = query_nvd(client, product, version)
            except Exception as e:
                results.append(BannerLookup(product=product, version=version, error=str(e)))
                continue
            results.append(BannerLookup(product=product, version=version, matches=matches))
            time.sleep(6.5 if not os.getenv("NVD_API_KEY") else 0.7)  # rate-limit politeness

        # Mark KEV
        all_cve_ids: list[str] = []
        for r in results:
            for m in r.matches:
                m.in_kev = m.cve_id in kev_set
                all_cve_ids.append(m.cve_id)

        # EPSS
        if all_cve_ids:
            if not args.quiet:
                print(f"[*] Fetching EPSS scores for {len(set(all_cve_ids))} CVEs...", file=sys.stderr)
            epss_map = fetch_epss(client, sorted(set(all_cve_ids)))
            for r in results:
                for m in r.matches:
                    m.epss = epss_map.get(m.cve_id)

    # Filtering
    for r in results:
        if args.kev_only:
            r.matches = [m for m in r.matches if m.in_kev]
        if args.min_cvss:
            r.matches = [m for m in r.matches if (m.cvss_v3_score or 0) >= args.min_cvss]
        # Sort by KEV first, then CVSS desc
        r.matches.sort(key=lambda m: (not m.in_kev, -(m.cvss_v3_score or 0)))

    payload = {
        "summary": {
            "banners": len(results),
            "total_matches": sum(len(r.matches) for r in results),
            "kev_matches": sum(1 for r in results for m in r.matches if m.in_kev),
        },
        "results": [asdict(r) for r in results],
    }

    out = json.dumps(payload, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        if not args.quiet:
            print(f"[+] Wrote {args.output}", file=sys.stderr)
    else:
        print(out)

    if not args.quiet:
        kev_count = payload["summary"]["kev_matches"]
        print(
            f"\n[+] Done. {payload['summary']['total_matches']} CVE matches "
            f"across {len(results)} banners, {kev_count} on CISA KEV.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
