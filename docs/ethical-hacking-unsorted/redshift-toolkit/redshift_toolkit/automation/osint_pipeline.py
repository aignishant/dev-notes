#!/usr/bin/env python3
"""
redshift_toolkit.automation.osint_pipeline — passive → active → correlate
→ report driver.

Chains every Module 9 / 10 / 11 toolkit module into a single command and
emits an asset graph + Markdown report.

Steps
-----
  1. PASSIVE
     - passive_subdomains.aggregate
     - cert_harvester.aggregate
     - whois_asn.lookup (best-effort)
  2. ACTIVE   (skipped if --no-active)
     - subdomain_enum.enum (using a small built-in wordlist or supplied)
     - masscan_wrapper backend (python-asyncio fallback) on top ports
     - svc_enum on resulting service stub
  3. CORRELATE
     - vuln_correlator on services
  4. ASSEMBLE
     - asset_graph.merge_*
     - report_generator → report.md
     - save graph.json

The pipeline is forgiving: each step that fails records the error but
doesn't prevent the next step from running.

Usage
-----
  python3 -m redshift_toolkit.automation.osint_pipeline \\
      --target example.com --outdir engagements/example/2026-04-25/
  python3 -m redshift_toolkit.automation.osint_pipeline \\
      --target example.com --no-active
  python3 -m redshift_toolkit.automation.osint_pipeline \\
      --target example.com --max-resolve 200 --top-ports 80,443

Author: Redshift Project — Module 12
License: MIT — Authorized testing only.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOLKIT = ROOT / "redshift-toolkit"
if TOOLKIT.exists():
    sys.path.insert(0, str(TOOLKIT))

from redshift_toolkit.recon import (
    passive_subdomains, cert_harvester, whois_asn,
    subdomain_enum, subdomain_takeover_check,
)
from redshift_toolkit.scan import (
    masscan_wrapper, svc_enum, vuln_correlator,
)
from redshift_toolkit.automation import asset_graph, report_generator

GREEN = "\033[92m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


def step(label: str, color: bool) -> float:
    print(paint(f"\n[+] {label} …", BOLD, color), file=sys.stderr)
    return time.time()


def done(t0: float, color: bool) -> None:
    print(paint(f"    done in {time.time() - t0:.1f}s", GREY, color),
          file=sys.stderr)


def fail(label: str, e: Exception, color: bool) -> None:
    print(paint(f"    {label} failed: {e}", YELLOW, color), file=sys.stderr)


def run(target: str, outdir: Path, do_active: bool,
        max_resolve: int, top_ports: list[int],
        wordlist_path: str | None,
        do_takeover: bool, color: bool) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    graph = asset_graph.new_graph(target)
    graph["domains"][target] = {}
    pipeline_log: list[dict] = []

    # ── 1. Passive ──────────────────────────────────────────────────────────
    t0 = step("passive subdomain aggregation", color)
    try:
        ps = passive_subdomains.aggregate(target)
        (outdir / "passive_subdomains.json").write_text(
            json.dumps({"target": ps.target,
                        "sources": [s.__dict__ for s in ps.sources],
                        "by_source": ps.by_source,
                        "subdomains": ps.subdomains}, indent=2))
        asset_graph.merge_passive(graph, {
            "target": ps.target,
            "subdomains": ps.subdomains,
            "by_source": ps.by_source,
        })
        pipeline_log.append({"step": "passive_subdomains", "ok": True,
                              "count": len(ps.subdomains)})
    except Exception as e:
        fail("passive_subdomains", e, color)
        pipeline_log.append({"step": "passive_subdomains", "ok": False,
                              "error": str(e)})
    done(t0, color)

    t0 = step("certificate transparency", color)
    try:
        ct = cert_harvester.aggregate(target)
        (outdir / "cert_transparency.json").write_text(
            json.dumps({"target": ct.target,
                        "cert_count": ct.cert_count,
                        "issuers": ct.issuers,
                        "unique_subdomains": ct.unique_subdomains}, indent=2))
        asset_graph.merge_subdomains(graph, ct.unique_subdomains,
                                      source="passive/crt.sh", parent=target)
        pipeline_log.append({"step": "cert_transparency", "ok": True,
                              "count": len(ct.unique_subdomains)})
    except Exception as e:
        fail("cert_harvester", e, color)
        pipeline_log.append({"step": "cert_transparency", "ok": False,
                              "error": str(e)})
    done(t0, color)

    t0 = step("WHOIS / RDAP", color)
    try:
        wa = whois_asn.lookup(target, do_whois=True, do_rdap=True, do_bgp=False)
        (outdir / "whois_asn.json").write_text(
            json.dumps(wa.__dict__, indent=2, default=str))
        graph["domains"][target] = {"rdap": bool(wa.rdap),
                                     "whois_excerpt": (wa.whois_text or "")[:300]}
        pipeline_log.append({"step": "whois_asn", "ok": True})
    except Exception as e:
        fail("whois_asn", e, color)
        pipeline_log.append({"step": "whois_asn", "ok": False, "error": str(e)})
    done(t0, color)

    # ── 2. Active ───────────────────────────────────────────────────────────
    if do_active:
        t0 = step("active DNS brute", color)
        try:
            if wordlist_path:
                with open(wordlist_path) as f:
                    words = [w.strip() for w in f
                             if w.strip() and not w.startswith("#")]
            else:
                words = list(subdomain_enum.BUILTIN_WORDLIST)
            rep_brute = asyncio.run(subdomain_enum.enum(
                target, words, 100, 2.0, 2,
                ["1.1.1.1", "8.8.8.8", "9.9.9.9"]))
            asset_graph.merge_dns_resolutions(graph, [
                {"name": h.name, "a": h.a, "cname": h.cname}
                for h in rep_brute.hits
            ], source="subdomain_enum")
            (outdir / "active_dns_brute.json").write_text(json.dumps({
                "target": rep_brute.target,
                "candidates_tested": rep_brute.candidates_tested,
                "wildcard_ips": rep_brute.wildcard_ips,
                "hits": [{"name": h.name, "a": h.a, "cname": h.cname}
                         for h in rep_brute.hits],
            }, indent=2))
            pipeline_log.append({"step": "active_dns_brute", "ok": True,
                                  "hits": len(rep_brute.hits)})
        except Exception as e:
            fail("subdomain_enum", e, color)
            pipeline_log.append({"step": "active_dns_brute", "ok": False,
                                  "error": str(e)})
        done(t0, color)

        # Pick a small set of resolved hosts to active-scan.
        hosts_to_scan: list[str] = []
        for sub, node in graph["subdomains"].items():
            if node.get("ips"):
                hosts_to_scan.append(sub)
            if len(hosts_to_scan) >= max_resolve:
                break

        if hosts_to_scan:
            t0 = step(f"port scan of {len(hosts_to_scan)} live host(s)", color)
            try:
                ips: list[str] = []
                for h in hosts_to_scan:
                    ips.extend(graph["subdomains"][h].get("ips", []))
                ips = sorted(set(ips))
                stub_path = outdir / "services_stub.json"
                # python-asyncio fallback (no masscan binary required)
                hits = asyncio.run(masscan_wrapper._python_backend(
                    ips, top_ports, 200, 2.0))
                stub = {"services": masscan_wrapper.emit_services_stub(hits),
                        "metadata": {"source": "pipeline", "ts": time.time()}}
                stub_path.write_text(json.dumps(stub, indent=2))
                pipeline_log.append({"step": "port_scan", "ok": True,
                                      "open_ports": len(hits)})
            except Exception as e:
                fail("port_scan", e, color)
                pipeline_log.append({"step": "port_scan", "ok": False,
                                      "error": str(e)})
            done(t0, color)

            t0 = step("service version enumeration", color)
            try:
                jobs: list[tuple[str, int]] = []
                stub = json.loads((outdir / "services_stub.json").read_text())
                for key, svc in (stub.get("services") or {}).items():
                    jobs.append((svc["ip"], int(svc["port"])))
                hits_svc = asyncio.run(svc_enum.run_scan(jobs, 200, 2.5))
                services_obj = {
                    "services": {f"{h.ip}:{h.port}": h.__dict__ for h in hits_svc},
                    "metadata": {"generated_at": time.time(), "tool": "svc_enum"},
                }
                (outdir / "services.json").write_text(
                    json.dumps(services_obj, indent=2))
                asset_graph.merge_services(graph, services_obj)
                pipeline_log.append({"step": "svc_enum", "ok": True,
                                      "services": len(services_obj["services"])})
            except Exception as e:
                fail("svc_enum", e, color)
                pipeline_log.append({"step": "svc_enum", "ok": False,
                                      "error": str(e)})
            done(t0, color)

            # Vuln correlation
            t0 = step("vulnerability correlation", color)
            try:
                services_obj = json.loads((outdir / "services.json").read_text())
                findings = vuln_correlator.correlate(
                    services_obj.get("services") or {})
                findings_obj = {
                    "generated_at": time.time(),
                    "min_severity": "low",
                    "findings": [f.__dict__ for f in findings],
                }
                (outdir / "findings.json").write_text(
                    json.dumps(findings_obj, indent=2))
                asset_graph.merge_findings(graph, findings_obj)
                pipeline_log.append({"step": "vuln_correlator", "ok": True,
                                      "findings": len(findings)})
            except Exception as e:
                fail("vuln_correlator", e, color)
                pipeline_log.append({"step": "vuln_correlator", "ok": False,
                                      "error": str(e)})
            done(t0, color)

    # ── 3. Takeover scan (cheap, skip HTTP fetch by default) ────────────────
    if do_takeover and graph["subdomains"]:
        t0 = step("subdomain takeover scan (CNAME fingerprint)", color)
        try:
            results = []
            for sub in graph["subdomains"]:
                r = subdomain_takeover_check.check_one(
                    sub, "1.1.1.1", 4.0, do_http=False)
                results.append(r)
            takeover_obj = {
                "queried": len(results),
                "results": [r.__dict__ for r in results],
                "candidates": [r.__dict__ for r in results
                                if r.body_signature_hit],
            }
            (outdir / "takeover.json").write_text(
                json.dumps(takeover_obj, indent=2, default=str))
            asset_graph.merge_takeover(graph, takeover_obj)
            pipeline_log.append({"step": "takeover", "ok": True,
                                  "fingerprinted": sum(1 for r in results
                                                       if r.matched_service)})
        except Exception as e:
            fail("takeover", e, color)
            pipeline_log.append({"step": "takeover", "ok": False,
                                  "error": str(e)})
        done(t0, color)

    # ── 4. Save graph + report ──────────────────────────────────────────────
    asset_graph.save(graph, outdir / "graph.json")

    md = report_generator.render(graph, target, pipeline_log)
    (outdir / "report.md").write_text(md)

    print(paint(f"\n[+] wrote {outdir}/graph.json", GREEN, color),
          file=sys.stderr)
    print(paint(f"[+] wrote {outdir}/report.md", GREEN, color),
          file=sys.stderr)
    print(asset_graph.render_text(graph, color), file=sys.stderr)

    return graph


def main() -> int:
    ap = argparse.ArgumentParser(description="OSINT pipeline driver.")
    ap.add_argument("--target", required=True)
    ap.add_argument("--outdir", default="recon-output")
    ap.add_argument("--no-active", action="store_true")
    ap.add_argument("--no-takeover", action="store_true")
    ap.add_argument("--max-resolve", type=int, default=50,
                    help="cap how many resolved hosts to scan")
    ap.add_argument("--top-ports", default="80,443,22,8080,8443,3306,3389,445,21,25",
                    help="comma-separated port list for active scan")
    ap.add_argument("--wordlist", default=None)
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color

    ports = [int(p) for p in args.top_ports.split(",") if p.strip()]
    run(args.target, Path(args.outdir),
        do_active=not args.no_active,
        max_resolve=args.max_resolve,
        top_ports=ports,
        wordlist_path=args.wordlist,
        do_takeover=not args.no_takeover,
        color=color)
    return 0


if __name__ == "__main__":
    sys.exit(main())
