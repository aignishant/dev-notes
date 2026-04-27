#!/usr/bin/env python3
"""
redshift_toolkit.automation.report_generator — Markdown report from an
asset graph + findings list.

Produces the "report a stakeholder will actually read" layout:
  1. Executive summary
  2. Scope
  3. Top-N findings (sorted by severity × exploitability)
  4. Asset summary (counts)
  5. Notable services (old versions, exposed admin ports)
  6. JSON appendix index

Usage
-----
  python3 -m redshift_toolkit.automation.report_generator \\
      --graph graph.json --output report.md
  python3 -m redshift_toolkit.automation.report_generator \\
      --graph graph.json   # prints to stdout

Author: Redshift Project — Module 12
License: MIT
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def _summarize_findings(graph: dict) -> dict:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in graph.get("findings", []) or []:
        sev = (f.get("severity") or "info").lower()
        if sev in counts:
            counts[sev] += 1
    return counts


def _sort_findings(findings: list[dict]) -> list[dict]:
    return sorted(findings,
                  key=lambda f: -SEVERITY_RANK.get((f.get("severity") or "info").lower(), 0))


def _executive_summary(graph: dict, target: str) -> str:
    sub_count = len(graph.get("subdomains") or {})
    ip_count = len(graph.get("ips") or {})
    svc_count = len(graph.get("services") or {})
    f_counts = _summarize_findings(graph)
    high_plus = f_counts["critical"] + f_counts["high"]

    lines = [f"This report covers external attack-surface reconnaissance for "
             f"**{target}**. The pipeline discovered "
             f"**{sub_count} subdomains**, **{ip_count} unique IPs**, and "
             f"**{svc_count} reachable services**."]
    if high_plus:
        lines.append(
            f"**{high_plus}** finding(s) at high or critical severity warrant "
            f"immediate review. ")
    else:
        lines.append("No high-severity findings were correlated against the "
                     "embedded knowledge base; this does not preclude latent "
                     "vulnerabilities and should be supplemented with manual "
                     "testing.")
    if (graph.get("metadata") or {}).get("sources"):
        lines.append(
            "Data sources used: "
            + ", ".join(graph["metadata"]["sources"])
            + ".")
    return "\n\n".join(lines)


def _scope_section(graph: dict, target: str, log: list[dict] | None) -> str:
    lines = [f"- **Target apex domain:** `{target}`",
             f"- **Generated at:** "
             f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"]
    if log:
        lines.append("- **Pipeline steps executed:**")
        for entry in log:
            ok = entry.get("ok")
            mark = "✅" if ok else "⚠️ "
            extra = ""
            for k, v in entry.items():
                if k in ("step", "ok"):
                    continue
                extra += f" `{k}={v}`"
            lines.append(f"    - {mark} `{entry.get('step')}`{extra}")
    return "\n".join(lines)


def _top_findings_section(graph: dict, top_n: int = 10) -> str:
    findings = _sort_findings(graph.get("findings") or [])
    if not findings:
        return "_No findings produced by the embedded correlator._"
    lines = []
    for i, f in enumerate(findings[:top_n], 1):
        sev = (f.get("severity") or "info").upper()
        cve = f.get("cve") or "—"
        product = f.get("detected_product") or "?"
        version = f.get("detected_version") or "?"
        ip = f.get("ip") or "?"
        port = f.get("port") or "?"
        summary = f.get("summary") or ""
        lines.append(f"### {i}. [{sev}] {cve} — {product} {version}")
        lines.append(f"")
        lines.append(f"- **Service:** `{ip}:{port}`")
        lines.append(f"- **Severity:** {sev}")
        if summary:
            lines.append(f"- **Summary:** {summary}")
        lines.append(f"- **Recommendation:** Patch / upgrade "
                     f"`{product}` to a fixed release, then re-scan to "
                     f"confirm.")
        lines.append("")
    return "\n".join(lines)


def _asset_summary(graph: dict) -> str:
    s_subs = len(graph.get("subdomains") or {})
    s_ips = len(graph.get("ips") or {})
    s_svcs = len(graph.get("services") or {})
    f = _summarize_findings(graph)
    return (
        "| Metric | Count |\n"
        "|---|---|\n"
        f"| Subdomains | {s_subs} |\n"
        f"| Unique IPs | {s_ips} |\n"
        f"| Services | {s_svcs} |\n"
        f"| Critical findings | {f['critical']} |\n"
        f"| High findings | {f['high']} |\n"
        f"| Medium findings | {f['medium']} |\n"
        f"| Low findings | {f['low']} |"
    )


def _notable_services(graph: dict, max_rows: int = 25) -> str:
    rows: list[tuple[str, str, str, str]] = []
    for key, svc in (graph.get("services") or {}).items():
        proto = svc.get("service") or ""
        version = svc.get("version") or ""
        banner = (svc.get("banner") or "")[:80]
        if proto in ("rdp", "vnc", "smb", "telnet") or "admin" in banner.lower():
            rows.append((key, proto, version, banner))
        elif version:
            rows.append((key, proto, version, banner))
    rows = rows[:max_rows]
    if not rows:
        return "_No services found (active scan may have been skipped)._"
    out = ["| Endpoint | Service | Version | Banner |",
           "|---|---|---|---|"]
    for key, proto, version, banner in rows:
        b = banner.replace("|", "\\|").replace("\n", " ")
        out.append(f"| `{key}` | {proto} | {version or '—'} | {b or '—'} |")
    return "\n".join(out)


def _subdomain_section(graph: dict, max_rows: int = 60) -> str:
    subs = graph.get("subdomains") or {}
    if not subs:
        return "_No subdomains in graph._"
    items = sorted(subs.items())[:max_rows]
    lines = ["| Subdomain | Sources | IPs | Note |",
             "|---|---|---|---|"]
    for name, node in items:
        srcs = ", ".join(node.get("sources", []))
        ips = ", ".join((node.get("ips") or [])[:3])
        note = ""
        if node.get("takeover"):
            t = node["takeover"]
            if t.get("candidate"):
                note = "**TAKEOVER CANDIDATE**"
            else:
                note = f"fingerprint: {t.get('service', '')}"
        lines.append(f"| `{name}` | {srcs} | {ips or '—'} | {note} |")
    if len(subs) > max_rows:
        lines.append(f"\n_…and {len(subs) - max_rows} more not shown._")
    return "\n".join(lines)


def render(graph: dict, target: str | None = None,
           pipeline_log: list[dict] | None = None) -> str:
    if target is None:
        target = (graph.get("metadata") or {}).get("target") or "(unknown)"
    sections = [
        f"# Reconnaissance Report — {target}",
        "",
        "## 1. Executive Summary",
        "",
        _executive_summary(graph, target),
        "",
        "## 2. Scope and Methodology",
        "",
        _scope_section(graph, target, pipeline_log),
        "",
        "## 3. Top Findings",
        "",
        _top_findings_section(graph),
        "",
        "## 4. Asset Summary",
        "",
        _asset_summary(graph),
        "",
        "## 5. Notable Services",
        "",
        _notable_services(graph),
        "",
        "## 6. Subdomains",
        "",
        _subdomain_section(graph),
        "",
        "## Appendix: Source files",
        "",
        "Each pipeline step also wrote a JSON artifact in the output "
        "directory. The graph itself is `graph.json`. The full "
        "machine-readable findings list is `findings.json`. Service "
        "details are in `services.json`. Passive sources are "
        "`passive_subdomains.json`, `cert_transparency.json`, "
        "`whois_asn.json`. Takeover scan results are in `takeover.json`.",
        "",
        "---",
        f"_Generated by `redshift-toolkit/automation/report_generator.py` "
        f"at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}._",
    ]
    return "\n".join(sections) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Markdown report from asset graph.")
    ap.add_argument("--graph", required=True, help="graph.json from asset_graph")
    ap.add_argument("--target", help="override target shown in title")
    ap.add_argument("--output", help="write report.md here (default: stdout)")
    args = ap.parse_args()

    graph = json.loads(Path(args.graph).read_text())
    md = render(graph, args.target)
    if args.output:
        Path(args.output).write_text(md)
        print(f"[+] wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
