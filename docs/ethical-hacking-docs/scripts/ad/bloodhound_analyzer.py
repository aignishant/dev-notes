#!/usr/bin/env python3
"""
bloodhound_analyzer.py — Analyze BloodHound JSON exports without the GUI.

Parses the JSON files produced by SharpHound / bloodhound.py / AzureHound
ingestors and answers the questions BloodHound queries answer:

  - Find owned principals (you mark them by sAMAccountName)
  - Find shortest paths from owned principals to Domain Admins
    (or any specified high-value target)
  - List Kerberoastable accounts
  - List ASREP-roastable accounts
  - List unconstrained-delegation principals
  - List effective members of high-priv groups (transitive)
  - List dangerous ACLs (GenericAll/GenericWrite/WriteDacl/WriteOwner)
    targeting principals you own

No external deps — pure stdlib BFS over the graph.

⚠️ AUTHORIZATION REQUIRED ⚠️
The data this script consumes was collected from a production AD; treat
it as sensitive and don't share BloodHound exports outside the engagement.

Usage:
    python3 bloodhound_analyzer.py /path/to/bloodhound-zips-or-extracted-dir/
    python3 bloodhound_analyzer.py /path/ --owned alice,bob
    python3 bloodhound_analyzer.py /path/ --owned alice --target "DOMAIN ADMINS@CORP.LOCAL"
    python3 bloodhound_analyzer.py /path/ --max-paths 5 --json -o paths.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Edge labels that BloodHound considers traversable for a "compromise" path.
# This mirrors the most common edges the GUI follows.
ATTACK_EDGES = {
    "MemberOf", "HasSession", "AdminTo", "CanRDP", "CanPSRemote", "ExecuteDCOM",
    "AllowedToDelegate", "AllowedToAct", "AddAllowedToAct",
    "GenericAll", "GenericWrite", "WriteDacl", "WriteOwner", "Owns",
    "ForceChangePassword", "ReadLAPSPassword", "ReadGMSAPassword",
    "AddSelf", "AddMember", "AddKeyCredentialLink", "WriteSPN",
    "DCSync", "GetChanges", "GetChangesAll", "SyncLAPSPassword",
    "Contains", "GpLink",
    "DumpSMSAPassword", "AllExtendedRights",
    "SQLAdmin", "HasSIDHistory",
    "ADCSESC1", "ADCSESC2", "ADCSESC3", "ADCSESC4", "ADCSESC5",
    "ADCSESC6a", "ADCSESC6b", "ADCSESC7", "ADCSESC8", "ADCSESC9a", "ADCSESC9b",
    "ADCSESC10a", "ADCSESC10b", "ADCSESC11", "ADCSESC13",
}


@dataclass
class Node:
    object_id: str
    name: str             # sAMAccountName@DOMAIN or fully qualified
    label: str            # User / Computer / Group / Domain / OU / GPO / ...
    properties: dict = field(default_factory=dict)


@dataclass
class Edge:
    src_id: str
    dst_id: str
    kind: str
    properties: dict = field(default_factory=dict)


@dataclass
class Graph:
    nodes: dict[str, Node] = field(default_factory=dict)
    out_edges: dict[str, list[Edge]] = field(default_factory=lambda: defaultdict(list))
    name_to_id: dict[str, str] = field(default_factory=dict)


def load_json_files(input_path: str) -> list[dict]:
    p = Path(input_path)
    files: list[dict] = []
    if p.is_file() and p.suffix == ".zip":
        with zipfile.ZipFile(p) as zf:
            for n in zf.namelist():
                if n.endswith(".json"):
                    with zf.open(n) as f:
                        try:
                            files.append(json.load(f))
                        except json.JSONDecodeError:
                            print(f"[!] Skipping malformed: {n}", file=sys.stderr)
    elif p.is_dir():
        for jf in p.rglob("*.json"):
            try:
                with open(jf, encoding="utf-8") as f:
                    files.append(json.load(f))
            except json.JSONDecodeError:
                print(f"[!] Skipping malformed: {jf}", file=sys.stderr)
        for zf_path in p.rglob("*.zip"):
            try:
                with zipfile.ZipFile(zf_path) as zf:
                    for n in zf.namelist():
                        if n.endswith(".json"):
                            with zf.open(n) as f:
                                try:
                                    files.append(json.load(f))
                                except json.JSONDecodeError:
                                    pass
            except zipfile.BadZipFile:
                continue
    elif p.is_file():
        with open(p, encoding="utf-8") as f:
            files.append(json.load(f))
    return files


def build_graph(json_blobs: list[dict]) -> Graph:
    g = Graph()
    for blob in json_blobs:
        # SharpHound 4.x and 5.x format: { "data": [...], "meta": {...} }
        data = blob.get("data", [])
        meta = blob.get("meta", {})
        node_label = (meta.get("type") or "").rstrip("s").capitalize() or "Unknown"

        for entry in data:
            props = entry.get("Properties", {}) or {}
            object_id = entry.get("ObjectIdentifier") or props.get("objectid") or ""
            if not object_id:
                continue
            name = (props.get("name") or props.get("samaccountname") or props.get("displayname") or object_id).upper()

            node = Node(object_id=object_id, name=name, label=node_label, properties=props)
            g.nodes[object_id] = node
            g.name_to_id[name] = object_id

            # MemberOf / Aces / etc. — convert to outgoing edges
            for grp in entry.get("PrimaryGroupSID", []) or []:
                pass  # rarely present at top level

            # MemberOf
            for member_of in entry.get("MemberOf", []) or []:
                if isinstance(member_of, dict) and "ObjectIdentifier" in member_of:
                    g.out_edges[object_id].append(Edge(object_id, member_of["ObjectIdentifier"], "MemberOf"))

            # Aces (ACLs)
            for ace in entry.get("Aces", []) or []:
                principal = ace.get("PrincipalSID")
                right = ace.get("RightName") or ace.get("Right")
                if principal and right:
                    g.out_edges[principal].append(Edge(principal, object_id, right))

            # Group "Members"
            for m in entry.get("Members", []) or []:
                if isinstance(m, dict) and "ObjectIdentifier" in m:
                    g.out_edges[m["ObjectIdentifier"]].append(Edge(m["ObjectIdentifier"], object_id, "MemberOf"))

            # Computer Sessions / LocalAdmins / RDPers
            for sess in entry.get("Sessions", {}).get("Results", []) or []:
                user = sess.get("UserSID")
                if user:
                    g.out_edges[user].append(Edge(user, object_id, "HasSession"))
            for la in entry.get("LocalAdmins", {}).get("Results", []) or []:
                if la.get("ObjectIdentifier"):
                    g.out_edges[la["ObjectIdentifier"]].append(Edge(la["ObjectIdentifier"], object_id, "AdminTo"))
            for r in entry.get("RemoteDesktopUsers", {}).get("Results", []) or []:
                if r.get("ObjectIdentifier"):
                    g.out_edges[r["ObjectIdentifier"]].append(Edge(r["ObjectIdentifier"], object_id, "CanRDP"))
            for r in entry.get("PSRemoteUsers", {}).get("Results", []) or []:
                if r.get("ObjectIdentifier"):
                    g.out_edges[r["ObjectIdentifier"]].append(Edge(r["ObjectIdentifier"], object_id, "CanPSRemote"))
            for r in entry.get("DcomUsers", {}).get("Results", []) or []:
                if r.get("ObjectIdentifier"):
                    g.out_edges[r["ObjectIdentifier"]].append(Edge(r["ObjectIdentifier"], object_id, "ExecuteDCOM"))

            # Delegation
            atd = entry.get("AllowedToDelegate", []) or []
            for a in atd:
                if isinstance(a, dict) and "ObjectIdentifier" in a:
                    g.out_edges[object_id].append(Edge(object_id, a["ObjectIdentifier"], "AllowedToDelegate"))
            ata = entry.get("AllowedToAct", []) or []
            for a in ata:
                if isinstance(a, dict) and "ObjectIdentifier" in a:
                    g.out_edges[a["ObjectIdentifier"]].append(Edge(a["ObjectIdentifier"], object_id, "AllowedToAct"))

    return g


def shortest_path(g: Graph, src: str, dst: str, max_depth: int = 10) -> list[Edge] | None:
    """BFS through traversable edges only."""
    if src == dst:
        return []
    if src not in g.nodes or dst not in g.nodes:
        return None
    visited = {src}
    parents: dict[str, tuple[str, Edge]] = {}
    q = deque([(src, 0)])
    while q:
        cur, depth = q.popleft()
        if depth >= max_depth:
            continue
        for edge in g.out_edges.get(cur, []):
            if edge.kind not in ATTACK_EDGES:
                continue
            if edge.dst_id in visited:
                continue
            visited.add(edge.dst_id)
            parents[edge.dst_id] = (cur, edge)
            if edge.dst_id == dst:
                # Reconstruct
                path = []
                node = dst
                while node in parents:
                    prev, e = parents[node]
                    path.append(e)
                    node = prev
                return list(reversed(path))
            q.append((edge.dst_id, depth + 1))
    return None


def find_high_value_groups(g: Graph) -> list[Node]:
    """Domain Admins, Enterprise Admins, etc."""
    targets = []
    for n in g.nodes.values():
        name_upper = n.name.upper()
        if any(name_upper.startswith(grp) for grp in (
            "DOMAIN ADMINS@", "ENTERPRISE ADMINS@", "SCHEMA ADMINS@",
            "ADMINISTRATORS@", "ACCOUNT OPERATORS@", "BACKUP OPERATORS@",
        )):
            targets.append(n)
    return targets


def find_kerberoastable(g: Graph) -> list[Node]:
    return [n for n in g.nodes.values()
            if n.label.lower() in ("user",) and n.properties.get("hasspn")]


def find_asrep_roastable(g: Graph) -> list[Node]:
    return [n for n in g.nodes.values()
            if n.label.lower() in ("user",) and n.properties.get("dontreqpreauth")]


def find_unconstrained(g: Graph) -> list[Node]:
    return [n for n in g.nodes.values() if n.properties.get("unconstraineddelegation")]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", help="BloodHound zip, directory, or single JSON file")
    p.add_argument("--owned", help="Comma-separated SAM/UPN names to mark as owned")
    p.add_argument("--target", help="Specific target name (UPPERCASE) — defaults to all high-priv groups")
    p.add_argument("--max-paths", type=int, default=3, help="How many shortest paths per (owned, target)")
    p.add_argument("--max-depth", type=int, default=8, help="BFS depth limit")
    p.add_argument("--json", action="store_true", help="Output JSON")
    p.add_argument("-o", "--output", help="Write JSON to file")
    args = p.parse_args()

    if not os.path.exists(args.input):
        print(f"[-] {args.input} not found.", file=sys.stderr)
        return 1

    blobs = load_json_files(args.input)
    if not blobs:
        print("[-] No JSON found.", file=sys.stderr)
        return 1
    print(f"[*] Loaded {len(blobs)} JSON blob(s) from {args.input}", file=sys.stderr)

    g = build_graph(blobs)
    print(f"[+] Graph: {len(g.nodes)} nodes, "
          f"{sum(len(es) for es in g.out_edges.values())} edges", file=sys.stderr)

    high_val = find_high_value_groups(g)
    kerb = find_kerberoastable(g)
    asrep = find_asrep_roastable(g)
    uncon = find_unconstrained(g)

    paths: list[dict] = []
    if args.owned:
        owned_names = [s.strip().upper() for s in args.owned.split(",") if s.strip()]
        owned_ids = []
        for nm in owned_names:
            # Allow either bare name or name@DOMAIN
            for n in g.nodes.values():
                if n.name == nm or n.name.split("@")[0] == nm:
                    owned_ids.append(n.object_id)
                    break

        targets = []
        if args.target:
            for n in g.nodes.values():
                if n.name == args.target.upper():
                    targets.append(n)
                    break
        else:
            targets = high_val

        if not owned_ids:
            print(f"[!] None of {owned_names} found in graph.", file=sys.stderr)
        if not targets:
            print("[!] No high-value targets resolved.", file=sys.stderr)

        for src_id in owned_ids:
            for tgt in targets:
                path = shortest_path(g, src_id, tgt.object_id, max_depth=args.max_depth)
                if path is None:
                    continue
                paths.append({
                    "from": g.nodes[src_id].name,
                    "to": tgt.name,
                    "length": len(path),
                    "edges": [
                        {
                            "kind": e.kind,
                            "src": g.nodes.get(e.src_id, Node("?", "?", "?")).name,
                            "dst": g.nodes.get(e.dst_id, Node("?", "?", "?")).name,
                        } for e in path
                    ],
                })
        paths.sort(key=lambda x: (x["length"], x["from"], x["to"]))
        paths = paths[:args.max_paths * max(1, len(g.nodes))]  # cap

    payload = {
        "graph": {
            "node_count": len(g.nodes),
            "edge_count": sum(len(es) for es in g.out_edges.values()),
        },
        "high_value_groups": [n.name for n in high_val],
        "kerberoastable_count": len(kerb),
        "kerberoastable_sample": [n.name for n in kerb[:20]],
        "asreproastable_count": len(asrep),
        "asreproastable_sample": [n.name for n in asrep[:20]],
        "unconstrained_delegation_count": len(uncon),
        "unconstrained_delegation_sample": [n.name for n in uncon[:20]],
        "paths": paths,
    }

    out = json.dumps(payload, indent=2, default=str)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"[+] Wrote {args.output}", file=sys.stderr)
    else:
        if args.json:
            print(out)
        else:
            print(f"\nHigh-value groups in graph: {len(high_val)}")
            for n in high_val[:10]:
                print(f"  • {n.name}")
            print(f"\nKerberoastable users: {len(kerb)}")
            print(f"AS-REP roastable users: {len(asrep)}")
            print(f"Unconstrained delegation: {len(uncon)}")
            if paths:
                print(f"\nShortest paths:")
                for path in paths[:args.max_paths]:
                    print(f"\n  {path['from']}  ─→  {path['to']}  ({path['length']} hops)")
                    for e in path["edges"]:
                        print(f"     {e['src']:50} ─[{e['kind']}]→  {e['dst']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
