#!/usr/bin/env python3
"""
redshift_toolkit.automation.recon_diff — diff two asset graphs and emit
a JSON + Markdown changelog.

Detects, across the two snapshots:
  - subdomains added / removed
  - IPs added / removed
  - services added / removed / changed (port newly exposed, banner shift)
  - findings added / fixed (CVE on host present in old but not new)

Output JSON shape:

  {
    "old_path", "new_path", "generated_at",
    "subdomains":  { "added": [...], "removed": [...] },
    "ips":         { "added": [...], "removed": [...] },
    "services":    { "added": [...], "removed": [...], "changed": [...] },
    "findings":    { "added": [...], "fixed": [...] }
  }

Usage
-----
  python3 -m redshift_toolkit.automation.recon_diff \\
      --old graph-2026-04-18.json --new graph-2026-04-25.json
  python3 -m redshift_toolkit.automation.recon_diff \\
      --old old.json --new new.json --output diff.json --markdown diff.md

Author: Redshift Project — Module 12
License: MIT
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Iterable


def _set(d: dict | None) -> set[str]:
    return set((d or {}).keys())


def diff_dict_keys(old: dict | None, new: dict | None) -> tuple[list[str], list[str]]:
    o, n = _set(old), _set(new)
    return sorted(n - o), sorted(o - n)


def diff_services(old: dict, new: dict) -> dict:
    old_svcs = old.get("services") or {}
    new_svcs = new.get("services") or {}
    added, removed = diff_dict_keys(old_svcs, new_svcs)
    changed = []
    for k in set(old_svcs) & set(new_svcs):
        ov = old_svcs[k].get("version") or ""
        nv = new_svcs[k].get("version") or ""
        ob = (old_svcs[k].get("banner") or "")[:80]
        nb = (new_svcs[k].get("banner") or "")[:80]
        if ov != nv or ob != nb:
            changed.append({
                "service": k,
                "old_version": ov, "new_version": nv,
                "old_banner": ob, "new_banner": nb,
            })
    return {
        "added": added,
        "removed": removed,
        "changed": changed,
    }


def diff_findings(old: dict, new: dict) -> dict:
    def key(f: dict) -> tuple:
        return (f.get("service_key", ""), f.get("cve", ""))
    old_set = {key(f): f for f in (old.get("findings") or [])}
    new_set = {key(f): f for f in (new.get("findings") or [])}
    added = [new_set[k] for k in (set(new_set) - set(old_set))]
    fixed = [old_set[k] for k in (set(old_set) - set(new_set))]
    return {
        "added": added,
        "fixed": fixed,
    }


def diff(old: dict, new: dict) -> dict:
    sub_a, sub_r = diff_dict_keys(old.get("subdomains"), new.get("subdomains"))
    ip_a, ip_r = diff_dict_keys(old.get("ips"), new.get("ips"))
    svc = diff_services(old, new)
    findings = diff_findings(old, new)
    return {
        "generated_at": time.time(),
        "subdomains": {"added": sub_a, "removed": sub_r},
        "ips": {"added": ip_a, "removed": ip_r},
        "services": svc,
        "findings": findings,
        "summary": {
            "subs_added": len(sub_a), "subs_removed": len(sub_r),
            "ips_added": len(ip_a), "ips_removed": len(ip_r),
            "svcs_added": len(svc["added"]),
            "svcs_removed": len(svc["removed"]),
            "svcs_changed": len(svc["changed"]),
            "findings_added": len(findings["added"]),
            "findings_fixed": len(findings["fixed"]),
        },
    }


def render_markdown(d: dict, old_label: str, new_label: str) -> str:
    s = d["summary"]
    lines = [
        f"# Recon Diff",
        "",
        f"`{old_label}`  →  `{new_label}`",
        "",
        "## Summary",
        "",
        "| Metric | Δ |",
        "|---|---|",
        f"| Subdomains added | {s['subs_added']} |",
        f"| Subdomains removed | {s['subs_removed']} |",
        f"| IPs added | {s['ips_added']} |",
        f"| IPs removed | {s['ips_removed']} |",
        f"| Services added | {s['svcs_added']} |",
        f"| Services removed | {s['svcs_removed']} |",
        f"| Services changed | {s['svcs_changed']} |",
        f"| Findings added | {s['findings_added']} |",
        f"| Findings fixed | {s['findings_fixed']} |",
        "",
    ]

    if d["subdomains"]["added"]:
        lines.append("## New subdomains")
        lines.append("")
        for n in d["subdomains"]["added"][:50]:
            lines.append(f"- `{n}`")
        if len(d["subdomains"]["added"]) > 50:
            lines.append(f"\n_…and {len(d['subdomains']['added']) - 50} more._")
        lines.append("")

    if d["subdomains"]["removed"]:
        lines.append("## Removed subdomains")
        lines.append("")
        for n in d["subdomains"]["removed"][:50]:
            lines.append(f"- `{n}`")
        lines.append("")

    if d["services"]["added"]:
        lines.append("## New services")
        lines.append("")
        for s in d["services"]["added"][:50]:
            lines.append(f"- `{s}`")
        lines.append("")

    if d["services"]["changed"]:
        lines.append("## Changed services")
        lines.append("")
        lines.append("| Endpoint | Old version | New version |")
        lines.append("|---|---|---|")
        for ch in d["services"]["changed"][:50]:
            lines.append(f"| `{ch['service']}` | {ch['old_version'] or '—'} | "
                         f"{ch['new_version'] or '—'} |")
        lines.append("")

    if d["findings"]["added"]:
        lines.append("## New findings")
        lines.append("")
        for f in d["findings"]["added"][:50]:
            lines.append(
                f"- **[{(f.get('severity') or 'info').upper()}]** "
                f"`{f.get('cve')}` on `{f.get('service_key') or f.get('ip')}` — "
                f"{f.get('summary') or ''}")
        lines.append("")

    if d["findings"]["fixed"]:
        lines.append("## Fixed findings")
        lines.append("")
        for f in d["findings"]["fixed"][:50]:
            lines.append(
                f"- `{f.get('cve')}` on `{f.get('service_key') or f.get('ip')}` "
                f"no longer present")
        lines.append("")

    lines.append("---")
    lines.append(
        f"_Generated by `recon_diff.py` at "
        f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}._"
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Diff two recon snapshots (asset graphs).")
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--output", help="write JSON diff to this path")
    ap.add_argument("--markdown", help="write Markdown diff to this path")
    args = ap.parse_args()

    old = json.loads(Path(args.old).read_text())
    new = json.loads(Path(args.new).read_text())
    d = diff(old, new)
    d["old_path"] = args.old
    d["new_path"] = args.new

    payload = json.dumps(d, indent=2, default=str)
    if args.output:
        Path(args.output).write_text(payload)
        print(f"[+] wrote {args.output}", file=sys.stderr)
    else:
        print(payload)

    if args.markdown:
        md = render_markdown(d, args.old, args.new)
        Path(args.markdown).write_text(md)
        print(f"[+] wrote {args.markdown}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
