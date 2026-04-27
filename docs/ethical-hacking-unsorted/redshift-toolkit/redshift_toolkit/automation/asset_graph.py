#!/usr/bin/env python3
"""
redshift_toolkit.automation.asset_graph — canonical asset graph schema
and merge logic.

Schema (mirrors docs/part-03-recon/12-osint-automation.md)
----------------------------------------------------------
  {
    "domains":    { "<apex>":           { "registrar": ..., "asn": ... } },
    "subdomains": { "<host>":           { "parent": ..., "sources": [...],
                                           "ips": [...], "cname": [...] } },
    "ips":        { "<ip>":             { "subdomains": [...], "asn": ...,
                                           "asn_owner": ... } },
    "services":   { "<ip>:<port>":      { "ip", "port", "proto", "service",
                                           "version", "banner", "extras" } },
    "findings":   [ { "service_key", "ip", "port", "cve", "severity",
                       "summary", "detected_product", "detected_version" } ],
    "metadata":   { "generated_at": <ts>, "sources": [...] }
  }

API
---
  - new_graph(target) → empty graph
  - merge_passive(graph, passive_runner_output)
  - merge_subdomains(graph, list_of_names, source_label)
  - merge_services(graph, svc_enum_output)
  - merge_findings(graph, vuln_correlator_output)
  - load(path)        → graph dict
  - save(graph, path)

CLI
---
  python3 -m redshift_toolkit.automation.asset_graph \\
      --target example.com \\
      --passive passive.json \\
      --services svc.json \\
      --findings findings.json \\
      --output graph.json

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

GREEN = "\033[92m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


def new_graph(target: str | None = None) -> dict:
    return {
        "domains": {},
        "subdomains": {},
        "ips": {},
        "services": {},
        "findings": [],
        "metadata": {
            "generated_at": time.time(),
            "target": target,
            "sources": [],
        },
    }


def _norm_host(s: str) -> str:
    return s.strip().lower().rstrip(".")


def _add_source(graph: dict, src: str) -> None:
    if src and src not in graph["metadata"]["sources"]:
        graph["metadata"]["sources"].append(src)


def merge_subdomains(graph: dict, names: list[str], source: str = "unknown",
                      parent: str | None = None) -> None:
    """Add subdomains. Keep an authoritative parent and dedup sources."""
    _add_source(graph, source)
    for raw in names:
        n = _norm_host(raw)
        if not n or "*" in n:
            continue
        node = graph["subdomains"].setdefault(n, {
            "parent": parent or _infer_parent(n),
            "sources": [],
            "ips": [],
            "cname": [],
        })
        if source not in node["sources"]:
            node["sources"].append(source)
        if parent and not node["parent"]:
            node["parent"] = parent


def _infer_parent(host: str) -> str:
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def merge_dns_resolutions(graph: dict, hits: list[dict],
                          source: str = "subdomain_enum") -> None:
    """Each hit: {name, a: [...], cname: [...]}."""
    _add_source(graph, source)
    for h in hits:
        name = _norm_host(h.get("name", ""))
        if not name:
            continue
        node = graph["subdomains"].setdefault(name, {
            "parent": _infer_parent(name),
            "sources": [],
            "ips": [],
            "cname": [],
        })
        if source not in node["sources"]:
            node["sources"].append(source)
        for ip in h.get("a") or []:
            if ip not in node["ips"]:
                node["ips"].append(ip)
            ip_node = graph["ips"].setdefault(ip, {
                "subdomains": [], "asn": None, "asn_owner": None,
            })
            if name not in ip_node["subdomains"]:
                ip_node["subdomains"].append(name)
        for cn in h.get("cname") or []:
            cn_n = _norm_host(cn)
            if cn_n and cn_n not in node["cname"]:
                node["cname"].append(cn_n)


def merge_passive(graph: dict, passive_obj: dict) -> None:
    """Accept the output of passive_subdomains or osint_runner."""
    target = passive_obj.get("target") or graph["metadata"].get("target")
    if target and target not in graph["domains"]:
        graph["domains"][target] = {}

    # Direct list at top level
    if "subdomains" in passive_obj and isinstance(passive_obj["subdomains"], list):
        merge_subdomains(graph, passive_obj["subdomains"],
                         source="passive", parent=target)
    if "by_source" in passive_obj:
        for src, names in (passive_obj.get("by_source") or {}).items():
            merge_subdomains(graph, names, source=f"passive/{src}",
                             parent=target)

    # osint_runner format with steps.cert_transparency / steps.wayback
    steps = passive_obj.get("steps") or {}
    ct = (steps.get("cert_transparency") or {}).get("summary") or {}
    if ct:
        merge_subdomains(graph, ct.get("unique_subdomains", []),
                         source="passive/crt.sh", parent=target)
    way = (steps.get("wayback") or {}).get("summary") or {}
    if way:
        merge_subdomains(graph, way.get("discovered_subdomains", []),
                         source="passive/wayback", parent=target)

    if "merged_subdomains" in passive_obj:
        merge_subdomains(graph, passive_obj["merged_subdomains"],
                         source="passive/merged", parent=target)

    # whois_asn
    wa = (steps.get("whois_asn") or {}).get("data") or {}
    if wa and wa.get("kind") == "domain" and target:
        graph["domains"].setdefault(target, {})


def merge_services(graph: dict, svc_obj: dict) -> None:
    """Accept svc_enum.py output."""
    _add_source(graph, "svc_enum")
    services = svc_obj.get("services") or {}
    for key, svc in services.items():
        graph["services"][key] = {
            "ip": svc.get("ip"),
            "port": int(svc.get("port", 0)),
            "proto": svc.get("proto", "tcp"),
            "service": svc.get("service", ""),
            "version": svc.get("version", ""),
            "banner": svc.get("banner", "") or "",
            "extras": svc.get("extras") or {},
        }
        ip = svc.get("ip")
        if ip:
            graph["ips"].setdefault(ip, {
                "subdomains": [], "asn": None, "asn_owner": None,
            })


def merge_findings(graph: dict, findings_obj: dict) -> None:
    _add_source(graph, "vuln_correlator")
    for f in findings_obj.get("findings") or []:
        graph["findings"].append(f)


def merge_takeover(graph: dict, takeover_obj: dict) -> None:
    _add_source(graph, "subdomain_takeover_check")
    for r in takeover_obj.get("results") or []:
        if not r.get("matched_service"):
            continue
        host = _norm_host(r.get("name", ""))
        node = graph["subdomains"].setdefault(host, {
            "parent": _infer_parent(host),
            "sources": [], "ips": [], "cname": [],
        })
        node.setdefault("takeover", {})
        node["takeover"] = {
            "service": r.get("matched_service"),
            "candidate": bool(r.get("body_signature_hit")),
            "cname": r.get("cname"),
            "note": r.get("note"),
        }
        if r.get("body_signature_hit"):
            graph["findings"].append({
                "service_key": host,
                "ip": (r.get("a") or [None])[0] if r.get("a") else None,
                "port": 443,
                "cve": "subdomain-takeover",
                "severity": "high",
                "summary": (f"Orphaned CNAME → {r.get('matched_service')} "
                            f"(takeover candidate)"),
                "detected_product": r.get("matched_service"),
                "detected_version": "",
            })


# ─── Persistence ────────────────────────────────────────────────────────────
def save(graph: dict, path: str | Path) -> None:
    Path(path).write_text(json.dumps(graph, indent=2, default=str))


def load(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


# ─── Stats ──────────────────────────────────────────────────────────────────
def summary(graph: dict) -> dict:
    return {
        "domains": len(graph["domains"]),
        "subdomains": len(graph["subdomains"]),
        "ips": len(graph["ips"]),
        "services": len(graph["services"]),
        "findings": len(graph["findings"]),
        "sources": graph["metadata"].get("sources", []),
    }


def render_text(graph: dict, color: bool) -> str:
    s = summary(graph)
    out = [paint(
        f"\n=== Asset graph: {graph['metadata'].get('target') or '(unknown)'} ===",
        BOLD, color)]
    out.append(f"  domains:    {s['domains']}")
    out.append(f"  subdomains: {s['subdomains']}")
    out.append(f"  ips:        {s['ips']}")
    out.append(f"  services:   {s['services']}")
    out.append(f"  findings:   {s['findings']}")
    out.append(f"  sources:    {', '.join(s['sources']) or '(none)'}")
    return "\n".join(out)


# ─── CLI ────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="Asset graph builder / merger.")
    ap.add_argument("--target", help="apex domain")
    ap.add_argument("--passive", help="passive_subdomains/osint_runner JSON")
    ap.add_argument("--dns-hits", help="subdomain_enum JSON")
    ap.add_argument("--services", help="svc_enum JSON")
    ap.add_argument("--findings", help="vuln_correlator JSON")
    ap.add_argument("--takeover", help="subdomain_takeover_check JSON")
    ap.add_argument("--input-graph", help="existing graph to merge into")
    ap.add_argument("--output", help="write merged graph here")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color

    graph = (load(args.input_graph) if args.input_graph
             else new_graph(args.target))
    if args.target and args.target not in graph["domains"]:
        graph["domains"][args.target] = {}
    if args.target:
        graph["metadata"]["target"] = args.target

    if args.passive:
        merge_passive(graph, json.loads(Path(args.passive).read_text()))
    if args.dns_hits:
        obj = json.loads(Path(args.dns_hits).read_text())
        hits = obj.get("hits") or []
        merge_dns_resolutions(graph, hits, source="subdomain_enum")
    if args.services:
        merge_services(graph, json.loads(Path(args.services).read_text()))
    if args.findings:
        merge_findings(graph, json.loads(Path(args.findings).read_text()))
    if args.takeover:
        merge_takeover(graph, json.loads(Path(args.takeover).read_text()))

    if args.output:
        save(graph, args.output)
        print(paint(f"[+] wrote {args.output}", GREEN, color),
              file=sys.stderr)
        print(render_text(graph, color), file=sys.stderr)
    else:
        print(json.dumps(graph, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
