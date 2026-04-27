#!/usr/bin/env python3
"""
redshift_toolkit.ad.acl_analyzer — DACL collection and attack-path analysis.

Two modes:

  --collect        Walk every AD object, parse nTSecurityDescriptor,
                   record interesting ACEs (GenericAll, GenericWrite,
                   WriteDACL, WriteOwner, ForceChangePassword,
                   AllExtendedRights, Replication-Get-Changes-*).
                   Output a JSON edge list.

  --shortest-path  Given a JSON edge list (from --collect or BloodHound),
                   find the shortest attack chain from --from to --to.

The shortest-path mode uses BFS on a directed graph built from edges
(principal --right--> object). It mirrors BloodHound's
"Shortest Path to Domain Admin" but in tens of milliseconds without Neo4j.

Dangerous rights tracked
------------------------
  GenericAll, GenericWrite, WriteDACL, WriteOwner,
  AllExtendedRights, ForceChangePassword, AddMember,
  Replication-Get-Changes, Replication-Get-Changes-All

Usage
-----
  # Step 1: collect
  python3 -m redshift_toolkit.ad.acl_analyzer \\
      --dc dc01.lab.local --user alice -p Password1 \\
      --domain lab.local --collect --output dacls.json

  # Step 2: find path
  python3 -m redshift_toolkit.ad.acl_analyzer \\
      --input dacls.json --from alice --to "Domain Admins" --shortest-path

Requires
--------
  pip install ldap3 impacket

Author: Redshift Project — Module 18
License: MIT
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


# Right names → bit masks (from MS-ADTS / SDDL)
GENERIC_ALL    = 0x10000000
GENERIC_WRITE  = 0x40000000
GENERIC_READ   = 0x80000000
WRITE_DACL     = 0x00040000
WRITE_OWNER    = 0x00080000
ALL_EXT_RIGHTS = 0x00000100
WRITE_PROP     = 0x00000020

# Object-type GUIDs of interest
RIGHT_GUIDS = {
    "00299570-246d-11d0-a768-00aa006e0529": "ForceChangePassword",
    "1131f6aa-9c07-11d1-f79f-00c04fc2dcd2": "DS-Replication-Get-Changes",
    "1131f6ad-9c07-11d1-f79f-00c04fc2dcd2": "DS-Replication-Get-Changes-All",
    "bf9679c0-0de6-11d0-a285-00aa003049e2": "Self-Member-of-Group",
    "00000000-0000-0000-0000-000000000000": "All",
}


def domain_to_dn(domain: str) -> str:
    return ",".join(f"DC={p}" for p in domain.split("."))


def collect_dacls(dc: str, user: str, password: str, domain: str) -> dict:
    """Walk all objects, parse security descriptors, build edge list."""
    try:
        from ldap3 import ALL, NTLM, Connection, Server, BASE, SUBTREE
        from ldap3.protocol.microsoft import security_descriptor_control
        from impacket.ldap.ldaptypes import SR_SECURITY_DESCRIPTOR
    except ImportError:
        sys.stderr.write("error: pip install ldap3 impacket\n")
        sys.exit(2)

    base_dn = domain_to_dn(domain)
    s = Server(dc, get_info=ALL)
    c = Connection(s, user=f"{domain}\\{user}", password=password,
                   authentication=NTLM, auto_bind=True)
    controls = security_descriptor_control(sdflags=0x04)  # DACL only

    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    DANGEROUS_BITS = (GENERIC_ALL | GENERIC_WRITE | WRITE_DACL | WRITE_OWNER)

    # We focus on user/computer/group objects
    c.search(base_dn,
             "(|(objectClass=user)(objectClass=computer)(objectClass=group))",
             attributes=["sAMAccountName", "objectSid", "nTSecurityDescriptor"],
             controls=controls, paged_size=500)

    for entry in c.entries:
        sam = str(entry.sAMAccountName.value or "")
        if not sam:
            continue
        try:
            obj_sid_raw = entry["objectSid"].raw_values[0]
        except Exception:
            continue
        target_sid = _sid_to_str(obj_sid_raw)
        nodes[target_sid] = {"name": sam, "sid": target_sid}

        if "nTSecurityDescriptor" not in entry or not entry["nTSecurityDescriptor"].raw_values:
            continue
        sd_raw = entry["nTSecurityDescriptor"].raw_values[0]
        try:
            sd = SR_SECURITY_DESCRIPTOR()
            sd.fromString(sd_raw)
        except Exception:
            continue

        for ace in sd["Dacl"].aces:
            if ace["AceType"] not in (0x00, 0x05):
                continue
            try:
                trustee = ace["Ace"]["Sid"].formatCanonical()
            except Exception:
                continue
            mask = ace["Ace"]["Mask"]["Mask"] if hasattr(ace["Ace"]["Mask"], "__getitem__") else int(ace["Ace"]["Mask"])
            rights: list[str] = []

            if mask & GENERIC_ALL:
                rights.append("GenericAll")
            if mask & GENERIC_WRITE:
                rights.append("GenericWrite")
            if mask & WRITE_DACL:
                rights.append("WriteDACL")
            if mask & WRITE_OWNER:
                rights.append("WriteOwner")

            # ACCESS_ALLOWED_OBJECT_ACE: extended rights via ObjectType GUID
            if ace["AceType"] == 0x05 and "ObjectType" in ace["Ace"].fields:
                try:
                    ot = ace["Ace"]["ObjectType"]
                    ot_hex = bytes(ot).hex()
                    guid = (f"{int.from_bytes(bytes.fromhex(ot_hex[0:8]), 'little'):08x}-"
                            f"{int.from_bytes(bytes.fromhex(ot_hex[8:12]), 'little'):04x}-"
                            f"{int.from_bytes(bytes.fromhex(ot_hex[12:16]), 'little'):04x}-"
                            f"{ot_hex[16:20]}-{ot_hex[20:32]}")
                    if guid in RIGHT_GUIDS:
                        rights.append(RIGHT_GUIDS[guid])
                except Exception:
                    pass

            if rights:
                edges.append({"src": trustee, "dst": target_sid, "rights": rights})

    c.unbind()
    return {"nodes": nodes, "edges": edges}


def _sid_to_str(sid_bytes: bytes) -> str:
    if not sid_bytes:
        return ""
    revision = sid_bytes[0]
    sub_authority_count = sid_bytes[1]
    identifier_authority = int.from_bytes(sid_bytes[2:8], "big")
    parts = [f"S-{revision}-{identifier_authority}"]
    for i in range(sub_authority_count):
        offset = 8 + i * 4
        parts.append(str(int.from_bytes(sid_bytes[offset:offset+4], "little")))
    return "-".join(parts)


def shortest_path(edges_list: list[dict], from_id: str, to_id: str,
                  nodes: dict) -> list[dict]:
    """BFS from from_id (sid OR sam) to to_id."""
    # Build adjacency
    adj: dict[str, list[tuple[str, list[str]]]] = {}
    for e in edges_list:
        adj.setdefault(e["src"], []).append((e["dst"], e["rights"]))

    # Allow lookup by name → sid
    name_to_sid = {nodes[s]["name"].lower(): s for s in nodes}
    from_sid = from_id if from_id in nodes else name_to_sid.get(from_id.lower())
    to_sid = to_id if to_id in nodes else name_to_sid.get(to_id.lower())

    if not from_sid:
        raise SystemExit(f"From '{from_id}' not found")
    if not to_sid:
        raise SystemExit(f"To '{to_id}' not found")

    # BFS
    queue = deque([(from_sid, [])])
    visited = {from_sid}
    while queue:
        cur, path = queue.popleft()
        if cur == to_sid:
            return path
        for nxt, rights in adj.get(cur, []):
            if nxt in visited:
                continue
            visited.add(nxt)
            queue.append((nxt, path + [{"from": cur, "to": nxt, "rights": rights,
                                         "from_name": nodes.get(cur, {}).get("name", cur),
                                         "to_name": nodes.get(nxt, {}).get("name", nxt)}]))
    return []


def main():
    p = argparse.ArgumentParser(
        prog="acl_analyzer",
        description="Collect AD DACLs and find attack paths.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--dc", help="Domain controller (for --collect)")
    p.add_argument("--user", help="Authenticated user (for --collect)")
    p.add_argument("-p", "--password", help="Password (for --collect)")
    p.add_argument("--domain", help="Domain (for --collect)")
    p.add_argument("--collect", action="store_true", help="Collect DACLs")
    p.add_argument("--output", help="Output JSON file (for --collect)")
    p.add_argument("--input", help="Input JSON file (for --shortest-path)")
    p.add_argument("--shortest-path", action="store_true", help="Find shortest path")
    p.add_argument("--from", dest="from_id", help="Source principal (name or SID)")
    p.add_argument("--to", dest="to_id", help="Target principal (name or SID)")
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args()

    on = sys.stdout.isatty() and not args.no_color

    if args.collect:
        if not all([args.dc, args.user, args.password, args.domain, args.output]):
            sys.stderr.write("--collect requires --dc --user -p --domain --output\n")
            sys.exit(2)
        data = collect_dacls(args.dc, args.user, args.password, args.domain)
        with open(args.output, "w") as f:
            json.dump(data, f, indent=2)
        print(paint(f"[+] {len(data['nodes'])} nodes, {len(data['edges'])} edges → {args.output}",
                    GREEN, on))
        return

    if args.shortest_path:
        if not (args.input and args.from_id and args.to_id):
            sys.stderr.write("--shortest-path requires --input --from --to\n")
            sys.exit(2)
        with open(args.input) as f:
            data = json.load(f)
        path = shortest_path(data["edges"], args.from_id, args.to_id, data["nodes"])
        if not path:
            print(paint(f"[!] No path from {args.from_id} to {args.to_id}", RED, on))
            sys.exit(1)
        print(paint(f"[+] Path of length {len(path)}:", GREEN, on))
        for hop in path:
            rights = ", ".join(hop["rights"])
            print(f"    {hop['from_name']:30s} --[{rights}]--> {hop['to_name']}")
        return

    p.print_help()


if __name__ == "__main__":
    main()
