#!/usr/bin/env python3
"""STIX 2.1 bundle querier — extract IoCs and TTPs.

Reads STIX 2.1 JSON bundles (e.g., from MISP exports, OpenCTI, MITRE ATT&CK,
CISA AAs) and pulls out:

  - Indicators (with normalised pattern types: file hashes, IPs, domains, URLs)
  - Threat actors / intrusion sets / malware families / tools
  - Attack patterns (ATT&CK techniques) referenced

Defensive threat-intel use only.

Dependencies
------------
- stdlib (no `stix2` library required — pure JSON parsing for portability)

Usage
-----
    python3 stix_query.py bundle.json
    python3 stix_query.py bundle.json --filter indicator --json iocs.json
    python3 stix_query.py bundle.json --object-type attack-pattern,malware
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Common STIX pattern extractors (covers most real-world IoCs)
PATTERN_RX = {
    "md5":     re.compile(r"file:hashes\.(?:'?MD5'?|MD5)\s*=\s*'([0-9a-fA-F]{32})'"),
    "sha1":    re.compile(r"file:hashes\.(?:'?SHA-1'?|SHA1|'SHA-1')\s*=\s*'([0-9a-fA-F]{40})'"),
    "sha256":  re.compile(r"file:hashes\.(?:'?SHA-256'?|SHA256|'SHA-256')\s*=\s*'([0-9a-fA-F]{64})'"),
    "ipv4":    re.compile(r"ipv4-addr:value\s*=\s*'([^']+)'"),
    "ipv6":    re.compile(r"ipv6-addr:value\s*=\s*'([^']+)'"),
    "domain":  re.compile(r"domain-name:value\s*=\s*'([^']+)'"),
    "url":     re.compile(r"url:value\s*=\s*'([^']+)'"),
    "email":   re.compile(r"email-addr:value\s*=\s*'([^']+)'"),
    "filename": re.compile(r"file:name\s*=\s*'([^']+)'"),
    "filepath": re.compile(r"file:parent_directory_ref\.path\s*=\s*'([^']+)'"),
    "registry": re.compile(r"windows-registry-key:key\s*=\s*'([^']+)'"),
    "mutex":    re.compile(r"mutex:name\s*=\s*'([^']+)'"),
}


def extract_iocs(pattern: str) -> list[dict]:
    found = []
    for ioc_type, rx in PATTERN_RX.items():
        for m in rx.finditer(pattern):
            found.append({"type": ioc_type, "value": m.group(1)})
    return found


def load_bundle(path: Path) -> dict:
    raw = json.loads(path.read_text())
    if isinstance(raw, dict) and raw.get("type") == "bundle":
        return raw
    # Some sources just dump a list of objects
    if isinstance(raw, list):
        return {"type": "bundle", "objects": raw}
    if isinstance(raw, dict) and "objects" in raw:
        return raw
    raise SystemExit("[-] not a recognised STIX bundle (no 'type=bundle' or 'objects' list)")


def by_type(objs: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for o in objs:
        out[o.get("type", "unknown")].append(o)
    return out


def relationship_map(objs: list[dict]) -> dict[str, list[tuple[str, str]]]:
    """Return source_ref -> [(relationship_type, target_ref)] map."""
    rels: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for o in objs:
        if o.get("type") == "relationship":
            rels[o.get("source_ref", "")].append((o.get("relationship_type", ""), o.get("target_ref", "")))
    return rels


def attack_external_id(o: dict) -> str | None:
    for ref in o.get("external_references", []) or []:
        if ref.get("source_name", "").lower() in {"mitre-attack", "mitre attack"}:
            return ref.get("external_id", "")
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("bundle", type=Path, help="STIX 2.1 bundle (JSON)")
    ap.add_argument("--object-type", default="", help="comma-separated types to include in summary")
    ap.add_argument("--filter", default="", help="alias for --object-type for one type")
    ap.add_argument("--json", type=Path, default=None, help="write extracted IoCs/TTPs to JSON")
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    if not args.bundle.is_file():
        print(f"[-] not a file: {args.bundle}", file=sys.stderr)
        return 2

    bundle = load_bundle(args.bundle)
    objs = bundle.get("objects", [])
    print(f"[+] bundle '{bundle.get('id', '<no-id>')}': {len(objs)} objects")

    grouped = by_type(objs)
    print(f"[+] object types: {dict(Counter({k: len(v) for k, v in grouped.items()}).most_common())}")

    type_filter = set()
    if args.object_type:
        type_filter |= {x.strip() for x in args.object_type.split(",") if x.strip()}
    if args.filter:
        type_filter.add(args.filter.strip())

    # IoCs
    iocs: list[dict] = []
    indicator_count = 0
    for ind in grouped.get("indicator", []):
        indicator_count += 1
        for entry in extract_iocs(ind.get("pattern", "")):
            iocs.append({
                "ioc_type": entry["type"],
                "value": entry["value"],
                "indicator_id": ind.get("id", ""),
                "indicator_name": ind.get("name", ""),
                "labels": ind.get("labels", []) or ind.get("indicator_types", []),
                "valid_from": ind.get("valid_from", ""),
                "kill_chain_phases": [p.get("phase_name", "") for p in ind.get("kill_chain_phases", []) or []],
            })

    if not type_filter or "indicator" in type_filter:
        print(f"\n[+] {indicator_count} indicator objects -> {len(iocs)} IoCs extracted")
        ioc_counts = Counter(i["ioc_type"] for i in iocs)
        for t, c in ioc_counts.most_common():
            print(f"    {t:<10} {c}")
        for i in iocs[: args.top]:
            print(f"      {i['ioc_type']:<8}  {i['value']:<60}  {i['indicator_name']}")
        if len(iocs) > args.top:
            print(f"      ... ({len(iocs) - args.top} more — use --json)")

    # Threat actors / intrusion sets / malware / tools
    actors = []
    for tname in ("threat-actor", "intrusion-set", "malware", "tool", "campaign"):
        if not type_filter or tname in type_filter:
            for o in grouped.get(tname, []):
                actors.append({
                    "type": tname,
                    "id": o.get("id", ""),
                    "name": o.get("name", ""),
                    "aliases": o.get("aliases", []),
                    "description": (o.get("description", "") or "")[:200],
                })
    if actors:
        print(f"\n[+] threat objects ({len(actors)}):")
        for a in actors[: args.top]:
            aliases = f" (aka {', '.join(a['aliases'])})" if a["aliases"] else ""
            print(f"    [{a['type']:<14}] {a['name']}{aliases}")
        if len(actors) > args.top:
            print(f"    ... ({len(actors) - args.top} more)")

    # ATT&CK techniques
    techniques = []
    if not type_filter or "attack-pattern" in type_filter:
        for ap_obj in grouped.get("attack-pattern", []):
            ext = attack_external_id(ap_obj)
            techniques.append({
                "id": ap_obj.get("id", ""),
                "external_id": ext,
                "name": ap_obj.get("name", ""),
                "kill_chain": [p.get("phase_name", "") for p in ap_obj.get("kill_chain_phases", []) or []],
                "description": (ap_obj.get("description", "") or "")[:240],
            })
        if techniques:
            print(f"\n[+] attack-patterns ({len(techniques)}):")
            for t in techniques[: args.top]:
                ext = f" ({t['external_id']})" if t["external_id"] else ""
                print(f"    {t['name']}{ext}  -- {','.join(t['kill_chain'])}")
            if len(techniques) > args.top:
                print(f"    ... ({len(techniques) - args.top} more)")

    if args.json:
        report = {
            "bundle": str(args.bundle),
            "object_type_counts": {k: len(v) for k, v in grouped.items()},
            "iocs": iocs,
            "actors": actors,
            "techniques": techniques,
        }
        args.json.write_text(json.dumps(report, indent=2))
        print(f"\n[+] full report -> {args.json}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[!] interrupted", file=sys.stderr)
        sys.exit(130)
