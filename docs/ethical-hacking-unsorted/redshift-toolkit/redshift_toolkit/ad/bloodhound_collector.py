#!/usr/bin/env python3
"""
redshift_toolkit.ad.bloodhound_collector — SharpHound-style data collection
in pure Python (no SharpHound binary, no .NET).

Outputs JSON files matching the BloodHound v4 ingest format:

  users_<TIMESTAMP>.json
  computers_<TIMESTAMP>.json
  groups_<TIMESTAMP>.json
  domains_<TIMESTAMP>.json
  containers_<TIMESTAMP>.json   (skeleton)
  ous_<TIMESTAMP>.json          (skeleton)
  gpos_<TIMESTAMP>.json         (skeleton)

These can be drag-dropped into the BloodHound GUI for graph analysis.

This is a *minimal* collector — it produces enough data for
"shortest path to Domain Admin" queries to work. It does not:
- Collect session data (would require SMB queries on each computer)
- Collect local admin enumeration (same)
- Collect GPO link data with full ACL (use SharpHound for those)

Why pure Python?
- Runs on Linux pivot hosts where SharpHound won't.
- AV/EDR doesn't yet signature it.
- You can audit every line of code.

Usage
-----
  python3 -m redshift_toolkit.ad.bloodhound_collector \\
      --dc dc01.lab.local --user alice -p Password1 \\
      --domain lab.local --output ./bh-data/

Requires
--------
  pip install ldap3

Author: Redshift Project — Module 18
License: MIT
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any


GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def domain_to_dn(domain: str) -> str:
    return ",".join(f"DC={p}" for p in domain.split("."))


def sid_to_str(sid_bytes: bytes) -> str:
    """Convert binary objectSid (NDR-encoded) to S-1-... string."""
    if not sid_bytes:
        return ""
    revision = sid_bytes[0]
    sub_authority_count = sid_bytes[1]
    identifier_authority = int.from_bytes(sid_bytes[2:8], "big")
    parts = [f"S-{revision}-{identifier_authority}"]
    for i in range(sub_authority_count):
        offset = 8 + i * 4
        sub = int.from_bytes(sid_bytes[offset:offset+4], "little")
        parts.append(str(sub))
    return "-".join(parts)


def guid_to_str(guid_bytes: bytes) -> str:
    """Convert binary objectGUID to GUID string."""
    if not guid_bytes or len(guid_bytes) < 16:
        return ""
    g = guid_bytes
    return f"{int.from_bytes(g[0:4], 'little'):08x}-{int.from_bytes(g[4:6], 'little'):04x}-" \
           f"{int.from_bytes(g[6:8], 'little'):04x}-{g[8:10].hex()}-{g[10:16].hex()}"


def collect(dc: str, user: str, password: str, domain: str, output_dir: str):
    try:
        from ldap3 import ALL, NTLM, Connection, Server, BASE, SUBTREE
    except ImportError:
        sys.stderr.write("error: pip install ldap3\n")
        sys.exit(2)

    base_dn = domain_to_dn(domain)
    s = Server(dc, get_info=ALL)
    c = Connection(s, user=f"{domain}\\{user}", password=password,
                   authentication=NTLM, auto_bind=True)
    domain_upper = domain.upper()

    os.makedirs(output_dir, exist_ok=True)
    ts = int(time.time())

    # Get domain SID
    c.search(base_dn, "(objectClass=domainDNS)", search_scope=BASE,
             attributes=["objectSid", "name"])
    if not c.entries:
        raise RuntimeError("could not read domain object")
    dom_sid_bytes = c.entries[0]["objectSid"].raw_values[0]
    domain_sid = sid_to_str(dom_sid_bytes)

    # USERS
    c.search(base_dn, "(&(objectClass=user)(objectCategory=person))",
             attributes=["sAMAccountName", "objectSid", "objectGUID",
                         "userAccountControl", "memberOf", "primaryGroupID",
                         "servicePrincipalName", "adminCount", "lastLogon",
                         "pwdLastSet", "displayName", "description"], paged_size=500)
    users_data = []
    for e in c.entries:
        sam = str(e.sAMAccountName.value or "")
        sid = sid_to_str(e["objectSid"].raw_values[0]) if e["objectSid"].raw_values else ""
        guid = guid_to_str(e["objectGUID"].raw_values[0]) if e["objectGUID"].raw_values else ""
        uac = int(e.userAccountControl.value or 0)
        member_of = [str(m) for m in e.memberOf.values] if e.memberOf else []
        spn = [str(x) for x in e.servicePrincipalName.values] if e.servicePrincipalName else []
        users_data.append({
            "ObjectIdentifier": sid,
            "Properties": {
                "name": f"{sam.upper()}@{domain_upper}",
                "domain": domain_upper,
                "domainsid": domain_sid,
                "objectid": sid,
                "guid": guid,
                "samaccountname": sam,
                "displayname": str(e.displayName.value or ""),
                "description": str(e.description.value or ""),
                "useraccountcontrol": uac,
                "enabled": not (uac & 0x0002),
                "dontreqpreauth": bool(uac & 0x400000),
                "passwordnotreqd": bool(uac & 0x0020),
                "unconstraineddelegation": bool(uac & 0x80000),
                "trustedtoauth": bool(uac & 0x1000000),
                "hasspn": bool(spn),
                "admincount": int(e.adminCount.value or 0) if e.adminCount.value else 0,
                "serviceprincipalnames": spn,
            },
            "PrimaryGroupSID": f"{domain_sid}-{e.primaryGroupID.value}" if e.primaryGroupID.value else None,
            "Aces": [],   # full ACE collection requires nTSecurityDescriptor parse
        })

    # COMPUTERS
    c.search(base_dn, "(objectCategory=computer)",
             attributes=["sAMAccountName", "objectSid", "objectGUID",
                         "userAccountControl", "dNSHostName", "operatingSystem",
                         "memberOf", "primaryGroupID",
                         "servicePrincipalName", "msDS-AllowedToDelegateTo",
                         "msDS-AllowedToActOnBehalfOfOtherIdentity"], paged_size=500)
    computers_data = []
    for e in c.entries:
        sam = str(e.sAMAccountName.value or "")
        sid = sid_to_str(e["objectSid"].raw_values[0]) if e["objectSid"].raw_values else ""
        guid = guid_to_str(e["objectGUID"].raw_values[0]) if e["objectGUID"].raw_values else ""
        uac = int(e.userAccountControl.value or 0)
        dns_name = str(e.dNSHostName.value or "")
        computers_data.append({
            "ObjectIdentifier": sid,
            "Properties": {
                "name": f"{sam.rstrip('$').upper()}.{domain_upper}",
                "domain": domain_upper,
                "domainsid": domain_sid,
                "objectid": sid,
                "guid": guid,
                "samaccountname": sam,
                "operatingsystem": str(e.operatingSystem.value or ""),
                "haslaps": False,  # TODO: query ms-Mcs-AdmPwd presence
                "useraccountcontrol": uac,
                "enabled": not (uac & 0x0002),
                "unconstraineddelegation": bool(uac & 0x80000),
                "trustedtoauth": bool(uac & 0x1000000),
            },
            "Aces": [],
            "Sessions": {"Results": [], "Collected": False},
            "LocalAdmins": {"Results": [], "Collected": False},
            "RemoteDesktopUsers": {"Results": [], "Collected": False},
            "DcomUsers": {"Results": [], "Collected": False},
            "PSRemoteUsers": {"Results": [], "Collected": False},
        })

    # GROUPS
    c.search(base_dn, "(objectCategory=group)",
             attributes=["sAMAccountName", "objectSid", "objectGUID",
                         "member", "description", "adminCount"], paged_size=500)
    groups_data = []
    for e in c.entries:
        sam = str(e.sAMAccountName.value or "")
        sid = sid_to_str(e["objectSid"].raw_values[0]) if e["objectSid"].raw_values else ""
        guid = guid_to_str(e["objectGUID"].raw_values[0]) if e["objectGUID"].raw_values else ""
        members = []
        for m in (e.member.values if e.member else []):
            members.append({"ObjectIdentifier": str(m), "ObjectType": "Unknown"})
        groups_data.append({
            "ObjectIdentifier": sid,
            "Properties": {
                "name": f"{sam.upper()}@{domain_upper}",
                "domain": domain_upper,
                "domainsid": domain_sid,
                "objectid": sid,
                "guid": guid,
                "samaccountname": sam,
                "description": str(e.description.value or ""),
                "admincount": int(e.adminCount.value or 0) if e.adminCount.value else 0,
            },
            "Members": members,
            "Aces": [],
        })

    domains_data = [{
        "ObjectIdentifier": domain_sid,
        "Properties": {
            "name": domain_upper,
            "domain": domain_upper,
            "domainsid": domain_sid,
            "objectid": domain_sid,
        },
        "Trusts": [],
        "Aces": [],
        "Links": [],
        "ChildObjects": [],
    }]

    # Write
    written = {}
    for kind, data in (("users", users_data), ("computers", computers_data),
                        ("groups", groups_data), ("domains", domains_data),
                        ("containers", []), ("ous", []), ("gpos", [])):
        fname = f"{kind}_{ts}.json"
        path = os.path.join(output_dir, fname)
        with open(path, "w") as f:
            json.dump({
                "data": data,
                "meta": {"type": kind, "count": len(data), "version": 5},
            }, f, indent=2)
        written[kind] = path

    c.unbind()
    return written


def main():
    p = argparse.ArgumentParser(
        prog="bloodhound_collector",
        description="SharpHound-style LDAP data collector — output BloodHound JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--dc", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("-p", "--password", required=True)
    p.add_argument("--domain", required=True)
    p.add_argument("--output", required=True, help="Output directory (will be created)")
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args()

    on = sys.stdout.isatty() and not args.no_color

    try:
        files = collect(args.dc, args.user, args.password, args.domain, args.output)
    except Exception as e:
        sys.stderr.write(f"{RED}[!] {e}{RESET}\n")
        sys.exit(1)

    color = GREEN if on else ""
    reset = RESET if on else ""
    print(f"{color}[+] BloodHound JSON written:{reset}")
    for kind, path in files.items():
        print(f"    {kind:12s} → {path}")
    print(f"{color}[+] Drag-drop these files into BloodHound GUI.{reset}")


if __name__ == "__main__":
    main()
