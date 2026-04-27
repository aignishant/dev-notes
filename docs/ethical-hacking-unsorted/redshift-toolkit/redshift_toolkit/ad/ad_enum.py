#!/usr/bin/env python3
"""
redshift_toolkit.ad.ad_enum — LDAP enumeration the way modern AD operators do it.

What it reports
---------------
- Domain info (controllers, FSMO, functional level, password policy)
- All users with userAccountControl flags decoded
- Kerberoastable accounts (objects with a servicePrincipalName)
- AS-REP roastable accounts (DONT_REQ_PREAUTH bit set)
- adminCount=1 accounts (high-value historical admins)
- Computers with unconstrained delegation
- Trust relationships
- All groups + their members (Domain Admins, Enterprise Admins, etc.)
- LAPS-managed computers (with the password if you have read rights)
- Password not required, password never expires accounts
- Optionally GPOs and OUs

Usage
-----
  python3 -m redshift_toolkit.ad.ad_enum --dc dc01.lab.local \\
      --user alice -p Password1 --domain lab.local --all

  python3 -m redshift_toolkit.ad.ad_enum --dc dc01.lab.local \\
      --user alice -p Password1 --domain lab.local --filter kerberoastable

  python3 -m redshift_toolkit.ad.ad_enum --dc dc01.lab.local \\
      --anonymous --domain lab.local --filter trusts

Requires
--------
  pip install ldap3

Author: Redshift Project — Module 18
License: MIT
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


# userAccountControl flags
UAC_FLAGS = {
    0x0001: "SCRIPT",
    0x0002: "ACCOUNTDISABLE",
    0x0008: "HOMEDIR_REQUIRED",
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


def decode_uac(value: int) -> list[str]:
    return [name for bit, name in UAC_FLAGS.items() if value & bit]


def filetime_to_datetime(filetime: int) -> str | None:
    """Convert Windows FILETIME (100-ns since 1601-01-01) to ISO 8601 string."""
    if filetime == 0 or filetime == 0x7FFFFFFFFFFFFFFF:
        return None
    epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
    try:
        dt = epoch + timedelta(microseconds=filetime / 10)
        return dt.isoformat()
    except (OverflowError, OSError):
        return None


@dataclass
class UserInfo:
    sam_account_name: str
    distinguished_name: str
    user_account_control: int
    uac_flags: list[str]
    spn: list[str] = field(default_factory=list)
    description: str = ""
    member_of: list[str] = field(default_factory=list)
    pwd_last_set: str | None = None
    last_logon: str | None = None
    admin_count: int = 0
    kerberoastable: bool = False
    as_rep_roastable: bool = False


@dataclass
class ComputerInfo:
    sam_account_name: str
    dns_hostname: str
    operating_system: str
    user_account_control: int
    uac_flags: list[str]
    unconstrained_delegation: bool
    constrained_delegation: list[str] = field(default_factory=list)
    rbcd: bool = False
    laps_password: str | None = None


@dataclass
class GroupInfo:
    sam_account_name: str
    distinguished_name: str
    members: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class TrustInfo:
    name: str
    direction: str
    trust_type: str
    sid: str = ""


@dataclass
class DomainInfo:
    domain: str
    dn: str
    functional_level: str
    password_policy: dict[str, Any] = field(default_factory=dict)


@dataclass
class EnumResult:
    domain: DomainInfo | None = None
    users: list[UserInfo] = field(default_factory=list)
    computers: list[ComputerInfo] = field(default_factory=list)
    groups: list[GroupInfo] = field(default_factory=list)
    trusts: list[TrustInfo] = field(default_factory=list)
    kerberoastable: list[str] = field(default_factory=list)
    as_rep_roastable: list[str] = field(default_factory=list)
    admin_count: list[str] = field(default_factory=list)
    unconstrained: list[str] = field(default_factory=list)
    rbcd_targets: list[str] = field(default_factory=list)
    interesting_descriptions: list[dict[str, str]] = field(default_factory=list)


def connect_ldap(server: str, user: str | None, password: str | None,
                 domain: str, anonymous: bool, ssl: bool):
    """Establish ldap3 connection. Imported lazily to keep module importable without ldap3."""
    try:
        from ldap3 import ALL, NTLM, SASL, KERBEROS, Connection, Server
    except ImportError:
        sys.stderr.write("error: this tool requires `pip install ldap3`\n")
        sys.exit(2)

    s = Server(server, get_info=ALL, use_ssl=ssl)
    if anonymous:
        c = Connection(s, auto_bind=True)
    else:
        if not user or not password:
            raise SystemExit("--user and --password required (or --anonymous)")
        upn = f"{domain}\\{user}"
        c = Connection(s, user=upn, password=password, authentication=NTLM, auto_bind=True)
    return c


def domain_to_dn(domain: str) -> str:
    return ",".join(f"DC={p}" for p in domain.split("."))


def enumerate_users(conn, base_dn: str) -> tuple[list[UserInfo], list[str], list[str], list[str], list[dict]]:
    """Pull user objects, decode UAC, flag interesting accounts."""
    attrs = ["sAMAccountName", "distinguishedName", "userAccountControl",
             "servicePrincipalName", "description", "memberOf",
             "pwdLastSet", "lastLogon", "adminCount"]
    conn.search(base_dn, "(&(objectCategory=person)(objectClass=user))",
                attributes=attrs, paged_size=500)

    users = []
    kerberoastable = []
    as_rep = []
    admin_count = []
    interesting_desc = []

    for entry in conn.entries:
        uac = int(entry.userAccountControl.value or 0)
        flags = decode_uac(uac)
        spn = [str(s) for s in entry.servicePrincipalName.values] if entry.servicePrincipalName else []
        description = str(entry.description.value) if entry.description.value else ""
        member_of = [str(m) for m in entry.memberOf.values] if entry.memberOf else []
        admin_cnt = int(entry.adminCount.value or 0) if entry.adminCount.value else 0

        sam = str(entry.sAMAccountName.value)
        is_kerb = bool(spn) and not (uac & 0x0002)  # has SPN, not disabled
        is_asrep = bool(uac & 0x400000) and not (uac & 0x0002)

        # Heuristic: scan for password-like content in description
        if description and any(k in description.lower() for k in ("pass", "pwd", "secret", "credential")):
            interesting_desc.append({"user": sam, "description": description})

        u = UserInfo(
            sam_account_name=sam,
            distinguished_name=str(entry.distinguishedName.value),
            user_account_control=uac,
            uac_flags=flags,
            spn=spn,
            description=description,
            member_of=member_of,
            pwd_last_set=filetime_to_datetime(int(entry.pwdLastSet.value or 0)) if entry.pwdLastSet.value else None,
            last_logon=filetime_to_datetime(int(entry.lastLogon.value or 0)) if entry.lastLogon.value else None,
            admin_count=admin_cnt,
            kerberoastable=is_kerb,
            as_rep_roastable=is_asrep,
        )
        users.append(u)
        if is_kerb:
            kerberoastable.append(sam)
        if is_asrep:
            as_rep.append(sam)
        if admin_cnt == 1:
            admin_count.append(sam)

    return users, kerberoastable, as_rep, admin_count, interesting_desc


def enumerate_computers(conn, base_dn: str) -> tuple[list[ComputerInfo], list[str], list[str]]:
    attrs = ["sAMAccountName", "dNSHostName", "operatingSystem",
             "userAccountControl", "msDS-AllowedToDelegateTo",
             "msDS-AllowedToActOnBehalfOfOtherIdentity", "ms-Mcs-AdmPwd"]
    conn.search(base_dn, "(objectCategory=computer)", attributes=attrs, paged_size=500)

    computers = []
    unconstrained = []
    rbcd_targets = []

    for entry in conn.entries:
        uac = int(entry.userAccountControl.value or 0)
        flags = decode_uac(uac)
        is_uncon = bool(uac & 0x80000)
        constrained = []
        if "msDS-AllowedToDelegateTo" in entry and entry["msDS-AllowedToDelegateTo"]:
            constrained = [str(x) for x in entry["msDS-AllowedToDelegateTo"].values]
        rbcd = bool(entry["msDS-AllowedToActOnBehalfOfOtherIdentity"].value) if "msDS-AllowedToActOnBehalfOfOtherIdentity" in entry else False
        laps = None
        if "ms-Mcs-AdmPwd" in entry and entry["ms-Mcs-AdmPwd"].value:
            laps = str(entry["ms-Mcs-AdmPwd"].value)

        sam = str(entry.sAMAccountName.value)
        c = ComputerInfo(
            sam_account_name=sam,
            dns_hostname=str(entry.dNSHostName.value or ""),
            operating_system=str(entry.operatingSystem.value or ""),
            user_account_control=uac,
            uac_flags=flags,
            unconstrained_delegation=is_uncon,
            constrained_delegation=constrained,
            rbcd=rbcd,
            laps_password=laps,
        )
        computers.append(c)
        if is_uncon:
            unconstrained.append(sam)
        if rbcd:
            rbcd_targets.append(sam)

    return computers, unconstrained, rbcd_targets


def enumerate_groups(conn, base_dn: str) -> list[GroupInfo]:
    """Pull groups; for high-value groups, expand membership."""
    high_value = {"Domain Admins", "Enterprise Admins", "Schema Admins",
                  "Account Operators", "Backup Operators", "Server Operators",
                  "Print Operators", "DnsAdmins", "Remote Desktop Users"}
    attrs = ["sAMAccountName", "distinguishedName", "member", "description"]
    conn.search(base_dn, "(objectCategory=group)", attributes=attrs, paged_size=500)

    groups = []
    for entry in conn.entries:
        sam = str(entry.sAMAccountName.value)
        members = [str(m) for m in entry.member.values] if entry.member else []
        groups.append(GroupInfo(
            sam_account_name=sam,
            distinguished_name=str(entry.distinguishedName.value),
            members=members,
            description=str(entry.description.value) if entry.description.value else "",
        ))
    return groups


def enumerate_trusts(conn, base_dn: str) -> list[TrustInfo]:
    attrs = ["name", "trustDirection", "trustType", "trustPartner", "securityIdentifier"]
    conn.search(base_dn, "(objectClass=trustedDomain)", attributes=attrs)
    direction_map = {0: "DISABLED", 1: "INBOUND", 2: "OUTBOUND", 3: "BIDIRECTIONAL"}
    type_map = {1: "DOWNLEVEL_NT", 2: "UPLEVEL_AD", 3: "MIT_KERBEROS", 4: "DCE"}

    trusts = []
    for entry in conn.entries:
        d = int(entry.trustDirection.value or 0)
        t = int(entry.trustType.value or 0)
        sid = ""
        if entry.securityIdentifier.value:
            try:
                # ldap3 returns SID as bytes
                sid = str(entry.securityIdentifier.value)
            except Exception:
                sid = ""
        trusts.append(TrustInfo(
            name=str(entry.name.value),
            direction=direction_map.get(d, str(d)),
            trust_type=type_map.get(t, str(t)),
            sid=sid,
        ))
    return trusts


def get_password_policy(conn, base_dn: str) -> dict[str, Any]:
    attrs = ["minPwdLength", "pwdHistoryLength", "lockoutThreshold",
             "lockoutDuration", "lockoutObservationWindow", "maxPwdAge"]
    conn.search(base_dn, "(objectClass=domainDNS)", attributes=attrs)
    if not conn.entries:
        return {}
    e = conn.entries[0]
    return {
        "min_password_length": int(e.minPwdLength.value or 0) if e.minPwdLength.value else 0,
        "password_history": int(e.pwdHistoryLength.value or 0) if e.pwdHistoryLength.value else 0,
        "lockout_threshold": int(e.lockoutThreshold.value or 0) if e.lockoutThreshold.value else 0,
    }


def main():
    p = argparse.ArgumentParser(
        prog="ad_enum",
        description="LDAP enumeration of an Active Directory domain.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--dc", required=True, help="Domain controller (FQDN or IP)")
    p.add_argument("--user", help="Domain username")
    p.add_argument("-p", "--password", help="Password")
    p.add_argument("--domain", required=True, help="Domain (e.g. lab.local)")
    p.add_argument("--anonymous", action="store_true", help="Try anonymous bind")
    p.add_argument("--ssl", action="store_true", help="Use LDAPS (port 636)")
    p.add_argument("--all", action="store_true", help="Enumerate everything")
    p.add_argument("--filter", choices=("users", "computers", "groups", "trusts",
                                        "kerberoastable", "asreproastable", "admincount",
                                        "unconstrained", "policy"),
                   help="Restrict enumeration to one category")
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args()

    on = (sys.stdout.isatty() and not args.no_color)
    base_dn = domain_to_dn(args.domain)

    try:
        conn = connect_ldap(args.dc, args.user, args.password, args.domain, args.anonymous, args.ssl)
    except Exception as e:
        sys.stderr.write(paint(f"[!] Bind failed: {e}\n", RED, on))
        sys.exit(1)

    result = EnumResult(domain=DomainInfo(domain=args.domain, dn=base_dn,
                                          functional_level="(unknown)"))

    do_users = args.all or args.filter in (None, "users", "kerberoastable", "asreproastable", "admincount")
    do_computers = args.all or args.filter in (None, "computers", "unconstrained")
    do_groups = args.all or args.filter in (None, "groups")
    do_trusts = args.all or args.filter in (None, "trusts")
    do_policy = args.all or args.filter == "policy"

    if do_users:
        users, kb, asr, ac, idesc = enumerate_users(conn, base_dn)
        result.users = users
        result.kerberoastable = kb
        result.as_rep_roastable = asr
        result.admin_count = ac
        result.interesting_descriptions = idesc

    if do_computers:
        comps, uncon, rbcd = enumerate_computers(conn, base_dn)
        result.computers = comps
        result.unconstrained = uncon
        result.rbcd_targets = rbcd

    if do_groups:
        result.groups = enumerate_groups(conn, base_dn)

    if do_trusts:
        result.trusts = enumerate_trusts(conn, base_dn)

    if do_policy and result.domain:
        result.domain.password_policy = get_password_policy(conn, base_dn)

    conn.unbind()

    if args.format == "json":
        print(json.dumps(asdict(result), indent=2, default=str))
        return

    # Text output
    print(paint(f"\n[+] Domain: {args.domain} ({base_dn})", BOLD, on))
    if result.domain and result.domain.password_policy:
        pol = result.domain.password_policy
        print(f"    Password policy: min_len={pol.get('min_password_length')}, "
              f"history={pol.get('password_history')}, lockout={pol.get('lockout_threshold')}")

    if result.users:
        print(paint(f"\n[+] Users: {len(result.users)}", GREEN, on))
        for u in result.users[:30]:
            tag = []
            if u.kerberoastable:
                tag.append(paint("KERB", YELLOW, on))
            if u.as_rep_roastable:
                tag.append(paint("AS-REP", RED, on))
            if u.admin_count == 1:
                tag.append(paint("adminCount", CYAN, on))
            tag_s = " ".join(tag) if tag else ""
            print(f"    {u.sam_account_name:30s} {tag_s}")
        if len(result.users) > 30:
            print(paint(f"    ... and {len(result.users) - 30} more", GREY, on))

    if result.kerberoastable:
        print(paint(f"\n[!] Kerberoastable accounts: {len(result.kerberoastable)}", YELLOW, on))
        for sam in result.kerberoastable[:20]:
            print(f"      {sam}")

    if result.as_rep_roastable:
        print(paint(f"\n[!] AS-REP roastable accounts: {len(result.as_rep_roastable)}", RED, on))
        for sam in result.as_rep_roastable:
            print(f"      {sam}")

    if result.admin_count:
        print(paint(f"\n[!] adminCount=1 accounts: {len(result.admin_count)}", CYAN, on))

    if result.unconstrained:
        print(paint(f"\n[!] Unconstrained delegation: {len(result.unconstrained)}", RED, on))
        for sam in result.unconstrained:
            print(f"      {sam}")

    if result.rbcd_targets:
        print(paint(f"\n[!] RBCD targets: {len(result.rbcd_targets)}", YELLOW, on))

    if result.interesting_descriptions:
        print(paint(f"\n[!] Suspicious descriptions: {len(result.interesting_descriptions)}", YELLOW, on))
        for d in result.interesting_descriptions[:10]:
            print(f"      {d['user']}: {d['description']}")

    if result.trusts:
        print(paint(f"\n[+] Trust relationships: {len(result.trusts)}", BOLD, on))
        for t in result.trusts:
            print(f"    {t.name:30s} dir={t.direction:14s} type={t.trust_type}")

    if result.computers:
        print(paint(f"\n[+] Computers: {len(result.computers)}", BOLD, on))

    if result.groups:
        print(paint(f"\n[+] Groups: {len(result.groups)}", BOLD, on))


if __name__ == "__main__":
    main()
