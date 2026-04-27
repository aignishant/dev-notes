#!/usr/bin/env python3
"""
ad_ldap_recon.py — Read-only Active Directory enumeration via LDAP.

Connects to a Domain Controller via LDAP and enumerates:
  - Domain info (name, functional level, password policy)
  - Users (with UAC flags decoded)
  - Groups
  - Computers
  - GPOs
  - Trusts
  - Kerberoastable accounts (users with SPNs)
  - ASREPRoastable accounts (DONT_REQ_PREAUTH set)
  - Disabled / locked / never-expiring / pwd-not-required accounts
  - High-priv group memberships (Domain Admins, Enterprise Admins, etc.)

Read-only. No writes, no Kerberos, no exploitation. Outputs a structured
JSON report you can hand to BloodHound or feed into a SIEM.

⚠️ AUTHORIZATION REQUIRED ⚠️
Only run against domains you own or are explicitly authorized to enumerate.
Even read-only LDAP queries may trigger SIEM alerts.

Dependencies:
    pip install ldap3

Usage:
    python3 ad_ldap_recon.py -d corp.local -u alice -p Summer2026 -s 10.0.0.5
    python3 ad_ldap_recon.py -d corp.local -u alice -p Summer2026 -s dc.corp.local --ldaps -o report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

try:
    from ldap3 import Server, Connection, ALL, SUBTREE, NTLM
    from ldap3.utils.conv import escape_filter_chars
except ImportError:
    print("ERROR: ldap3 is required. Install with: pip install ldap3", file=sys.stderr)
    sys.exit(2)


# UserAccountControl flag bits we care about
UAC_FLAGS = {
    0x0002: "ACCOUNTDISABLE",
    0x0010: "LOCKOUT",
    0x0020: "PASSWD_NOTREQD",
    0x0040: "PASSWD_CANT_CHANGE",
    0x0080: "ENCRYPTED_TEXT_PWD_ALLOWED",
    0x0100: "TEMP_DUPLICATE_ACCOUNT",
    0x0200: "NORMAL_ACCOUNT",
    0x0800: "INTERDOMAIN_TRUST_ACCOUNT",
    0x1000: "WORKSTATION_TRUST_ACCOUNT",
    0x2000: "SERVER_TRUST_ACCOUNT",
    0x10000: "DONT_EXPIRE_PASSWORD",
    0x20000: "MNS_LOGON_ACCOUNT",
    0x40000: "SMARTCARD_REQUIRED",
    0x80000: "TRUSTED_FOR_DELEGATION",
    0x100000: "NOT_DELEGATED",
    0x200000: "USE_DES_KEY_ONLY",
    0x400000: "DONT_REQ_PREAUTH",
    0x800000: "PASSWORD_EXPIRED",
    0x1000000: "TRUSTED_TO_AUTH_FOR_DELEGATION",
    0x4000000: "PARTIAL_SECRETS_ACCOUNT",
}

HIGH_PRIV_GROUPS = [
    "Domain Admins", "Enterprise Admins", "Schema Admins",
    "Account Operators", "Server Operators", "Print Operators",
    "Backup Operators", "DnsAdmins",
    "Cert Publishers", "Group Policy Creator Owners",
    "Domain Controllers", "Read-only Domain Controllers",
    "Protected Users",
]


@dataclass
class Report:
    domain: str
    server: str
    timestamp: str
    domain_info: dict = field(default_factory=dict)
    password_policy: dict = field(default_factory=dict)
    users: list[dict] = field(default_factory=list)
    groups: list[dict] = field(default_factory=list)
    computers: list[dict] = field(default_factory=list)
    gpos: list[dict] = field(default_factory=list)
    trusts: list[dict] = field(default_factory=list)
    kerberoastable: list[dict] = field(default_factory=list)
    asreproastable: list[dict] = field(default_factory=list)
    flagged_accounts: list[dict] = field(default_factory=list)
    high_priv_membership: dict[str, list[str]] = field(default_factory=dict)


def decode_uac(uac: int) -> list[str]:
    return [name for bit, name in UAC_FLAGS.items() if uac & bit]


def domain_to_basedn(domain: str) -> str:
    return ",".join(f"DC={p}" for p in domain.split("."))


def filetime_to_iso(ft) -> str | None:
    """Convert AD FILETIME (100ns intervals since 1601) to ISO datetime, if valid."""
    if ft is None or ft in (0, "0"):
        return None
    try:
        if isinstance(ft, datetime):
            return ft.replace(tzinfo=timezone.utc).isoformat()
        ft = int(ft)
        if ft <= 0 or ft >= 9223372036854775000:
            return None
        unix_ts = (ft - 116444736000000000) // 10000000
        return datetime.fromtimestamp(unix_ts, timezone.utc).isoformat()
    except (ValueError, OverflowError, OSError):
        return None


def get_value(entry, attr: str, default=None):
    if attr not in entry:
        return default
    val = entry[attr].value
    return val if val is not None else default


def query(conn: Connection, base: str, ldap_filter: str, attrs: list[str]) -> list:
    conn.search(base, ldap_filter, search_scope=SUBTREE, attributes=attrs, paged_size=500)
    return list(conn.entries)


def enumerate_domain(conn: Connection, base_dn: str, report: Report) -> None:
    # Domain root info
    entries = query(conn, base_dn, "(objectClass=domain)", [
        "name", "objectSid", "msDS-Behavior-Version",
        "minPwdLength", "pwdProperties", "lockoutThreshold",
        "lockoutDuration", "maxPwdAge", "minPwdAge", "pwdHistoryLength",
    ])
    if entries:
        e = entries[0]
        report.domain_info = {
            "dn": str(e.entry_dn),
            "name": str(get_value(e, "name") or ""),
            "objectSid": str(get_value(e, "objectSid") or ""),
            "functional_level": str(get_value(e, "msDS-Behavior-Version") or ""),
        }
        report.password_policy = {
            "min_length": get_value(e, "minPwdLength"),
            "complexity_flags": get_value(e, "pwdProperties"),
            "lockout_threshold": get_value(e, "lockoutThreshold"),
            "history_length": get_value(e, "pwdHistoryLength"),
        }


def enumerate_users(conn: Connection, base_dn: str, report: Report) -> None:
    attrs = [
        "sAMAccountName", "userPrincipalName", "displayName",
        "description", "userAccountControl", "memberOf",
        "servicePrincipalName", "pwdLastSet", "lastLogon",
        "adminCount", "objectSid",
    ]
    entries = query(conn, base_dn, "(&(objectCategory=person)(objectClass=user))", attrs)
    for e in entries:
        uac = get_value(e, "userAccountControl") or 0
        flags = decode_uac(uac)
        sam = str(get_value(e, "sAMAccountName") or "")
        spns = get_value(e, "servicePrincipalName") or []
        if isinstance(spns, str):
            spns = [spns]
        description = get_value(e, "description")
        if isinstance(description, list):
            description = description[0] if description else None

        user = {
            "samAccountName": sam,
            "upn": str(get_value(e, "userPrincipalName") or ""),
            "displayName": str(get_value(e, "displayName") or ""),
            "description": str(description) if description else None,
            "uac": uac,
            "flags": flags,
            "spns": [str(s) for s in spns],
            "adminCount": get_value(e, "adminCount"),
            "pwdLastSet": filetime_to_iso(get_value(e, "pwdLastSet")),
            "lastLogon": filetime_to_iso(get_value(e, "lastLogon")),
        }
        report.users.append(user)

        # Kerberoastable: regular user with SPN
        if spns and 0x0002 not in (uac & 0x0002,) and "NORMAL_ACCOUNT" in flags:
            report.kerberoastable.append({"sam": sam, "spns": user["spns"]})

        # ASREPRoastable
        if "DONT_REQ_PREAUTH" in flags:
            report.asreproastable.append({"sam": sam, "uac": uac})

        # Flagged
        flag_reasons = []
        if "ACCOUNTDISABLE" in flags:
            flag_reasons.append("disabled")
        if "PASSWD_NOTREQD" in flags:
            flag_reasons.append("passwd_not_required")
        if "DONT_EXPIRE_PASSWORD" in flags:
            flag_reasons.append("password_never_expires")
        if "TRUSTED_FOR_DELEGATION" in flags:
            flag_reasons.append("unconstrained_delegation")
        if "TRUSTED_TO_AUTH_FOR_DELEGATION" in flags:
            flag_reasons.append("constrained_delegation_protocol_transition")
        if description and any(k in description.lower() for k in ("pwd", "pass", "secret")):
            flag_reasons.append("description_mentions_password")
        if flag_reasons:
            report.flagged_accounts.append({"sam": sam, "reasons": flag_reasons})


def enumerate_groups(conn: Connection, base_dn: str, report: Report) -> None:
    attrs = ["sAMAccountName", "description", "member", "groupType"]
    entries = query(conn, base_dn, "(objectCategory=group)", attrs)
    for e in entries:
        members = get_value(e, "member") or []
        if isinstance(members, str):
            members = [members]
        sam = str(get_value(e, "sAMAccountName") or "")
        report.groups.append(
            {
                "sam": sam,
                "description": str(get_value(e, "description") or "") or None,
                "member_count": len(members),
                "members": [str(m) for m in members],
            }
        )
        if sam in HIGH_PRIV_GROUPS:
            report.high_priv_membership[sam] = [str(m) for m in members]


def enumerate_computers(conn: Connection, base_dn: str, report: Report) -> None:
    attrs = ["sAMAccountName", "dNSHostName", "operatingSystem", "operatingSystemVersion", "userAccountControl"]
    entries = query(conn, base_dn, "(objectCategory=computer)", attrs)
    for e in entries:
        uac = get_value(e, "userAccountControl") or 0
        report.computers.append(
            {
                "sam": str(get_value(e, "sAMAccountName") or ""),
                "dns": str(get_value(e, "dNSHostName") or ""),
                "os": str(get_value(e, "operatingSystem") or ""),
                "os_version": str(get_value(e, "operatingSystemVersion") or ""),
                "uac": uac,
                "flags": decode_uac(uac),
            }
        )


def enumerate_gpos(conn: Connection, base_dn: str, report: Report) -> None:
    attrs = ["displayName", "gPCFileSysPath", "whenCreated", "whenChanged"]
    entries = query(conn, base_dn, "(objectClass=groupPolicyContainer)", attrs)
    for e in entries:
        report.gpos.append(
            {
                "name": str(get_value(e, "displayName") or ""),
                "path": str(get_value(e, "gPCFileSysPath") or ""),
                "created": str(get_value(e, "whenCreated") or ""),
                "changed": str(get_value(e, "whenChanged") or ""),
            }
        )


def enumerate_trusts(conn: Connection, base_dn: str, report: Report) -> None:
    attrs = ["trustPartner", "trustType", "trustDirection", "trustAttributes"]
    entries = query(conn, base_dn, "(objectClass=trustedDomain)", attrs)
    for e in entries:
        report.trusts.append(
            {
                "partner": str(get_value(e, "trustPartner") or ""),
                "type": get_value(e, "trustType"),
                "direction": get_value(e, "trustDirection"),
                "attributes": get_value(e, "trustAttributes"),
            }
        )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-d", "--domain", required=True, help="Domain (e.g. corp.local)")
    p.add_argument("-u", "--username", required=True, help="Username (sAMAccountName or UPN)")
    p.add_argument("-p", "--password", required=True, help="Password")
    p.add_argument("-s", "--server", required=True, help="DC hostname or IP")
    p.add_argument("--ldaps", action="store_true", help="Use LDAPS (port 636)")
    p.add_argument("--ntlm", action="store_true", help="Use NTLM auth instead of simple bind")
    p.add_argument("-o", "--output", help="Write JSON report to file")
    p.add_argument("-q", "--quiet", action="store_true", help="Less progress output")
    args = p.parse_args()

    base_dn = domain_to_basedn(args.domain)
    server_uri = f"ldap{'s' if args.ldaps else ''}://{args.server}"

    if not args.quiet:
        print(f"[*] Connecting to {server_uri} (base DN: {base_dn})", file=sys.stderr)

    server = Server(server_uri, get_info=ALL)
    user = f"{args.domain}\\{args.username}" if args.ntlm else f"{args.username}@{args.domain}"
    auth = NTLM if args.ntlm else None

    try:
        conn = Connection(server, user=user, password=args.password, authentication=auth, auto_bind=True)
    except Exception as e:
        print(f"[-] Bind failed: {e}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"[+] Bound as {user}", file=sys.stderr)

    report = Report(domain=args.domain, server=args.server, timestamp=datetime.now(timezone.utc).isoformat())

    steps = [
        ("domain", enumerate_domain),
        ("users", enumerate_users),
        ("groups", enumerate_groups),
        ("computers", enumerate_computers),
        ("gpos", enumerate_gpos),
        ("trusts", enumerate_trusts),
    ]
    for name, fn in steps:
        if not args.quiet:
            print(f"[*] Enumerating {name}...", file=sys.stderr)
        try:
            fn(conn, base_dn, report)
        except Exception as e:
            print(f"[!] {name} failed: {e}", file=sys.stderr)

    conn.unbind()

    if not args.quiet:
        print(
            f"[+] Done. Users={len(report.users)} "
            f"Groups={len(report.groups)} "
            f"Computers={len(report.computers)} "
            f"GPOs={len(report.gpos)} "
            f"Kerberoastable={len(report.kerberoastable)} "
            f"ASREPRoastable={len(report.asreproastable)} "
            f"Flagged={len(report.flagged_accounts)}",
            file=sys.stderr,
        )

    payload = json.dumps(asdict(report), indent=2, default=str)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(payload)
        if not args.quiet:
            print(f"[+] Wrote report to {args.output}", file=sys.stderr)
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    sys.exit(main())
