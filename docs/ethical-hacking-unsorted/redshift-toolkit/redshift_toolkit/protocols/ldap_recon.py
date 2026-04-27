#!/usr/bin/env python3
"""
redshift_toolkit.protocols.ldap_recon — LDAP / Active Directory enumeration.

What it does
------------
1. Anonymous probe — read RootDSE, identify naming contexts, domain controllers.
2. Authenticated dump (if creds given):
     - All users with key attributes
     - All groups + members
     - Computer accounts
     - Service accounts (servicePrincipalName) — Kerberoastable
     - Pre-auth disabled accounts — AS-REP roastable
     - "adminCount=1" accounts — protected (was admin)
     - Password-policy summary

Output is structured (JSON) and text.

Usage
-----
  python3 -m redshift_toolkit.protocols.ldap_recon -t 10.0.0.10
  python3 -m redshift_toolkit.protocols.ldap_recon -t dc01.corp.local \\
      -u alice -p Password1 -d corp.local
  python3 -m redshift_toolkit.protocols.ldap_recon -t dc01.corp.local \\
      -u alice -p Password1 -d corp.local --json > corp_dump.json

Requires
--------
  pip install ldap3

Author: Redshift Project — Module 08
License: MIT
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


# UAC flag interpretation
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
    0x400000: "DONT_REQUIRE_PREAUTH",   # ← AS-REP roastable
    0x800000: "PASSWORD_EXPIRED",
    0x1000000: "TRUSTED_TO_AUTH_FOR_DELEGATION",
    0x4000000: "PARTIAL_SECRETS_ACCOUNT",
}


def decode_uac(value: int) -> list[str]:
    return [name for bit, name in UAC_FLAGS.items() if value & bit]


@dataclass
class Result:
    host: str
    rootdse: dict | None = None
    naming_contexts: list[str] = field(default_factory=list)
    users: list[dict] = field(default_factory=list)
    groups: list[dict] = field(default_factory=list)
    computers: list[dict] = field(default_factory=list)
    spns: list[dict] = field(default_factory=list)        # Kerberoastable
    asrep_users: list[dict] = field(default_factory=list)  # AS-REP roastable
    admincount: list[dict] = field(default_factory=list)
    error: str | None = None


def anonymous_probe(host: str, port: int, use_ssl: bool) -> Result:
    try:
        from ldap3 import Server, Connection, ALL, SUBTREE, BASE  # type: ignore
    except ImportError:
        r = Result(host=host)
        r.error = "ldap3 not installed; pip install ldap3"
        return r

    r = Result(host=host)
    server = Server(host, port=port, use_ssl=use_ssl, get_info=ALL,
                    connect_timeout=4)
    try:
        conn = Connection(server, auto_bind=True)
        info = server.info
        if info is not None:
            r.rootdse = {
                "defaultNamingContext": info.other.get("defaultNamingContext"),
                "rootDomainNamingContext": info.other.get("rootDomainNamingContext"),
                "domainFunctionality": info.other.get("domainFunctionality"),
                "forestFunctionality": info.other.get("forestFunctionality"),
                "supportedLDAPVersion": info.supported_ldap_versions,
                "supportedSASLMechanisms": list(info.supported_sasl_mechanisms or []),
            }
            r.naming_contexts = list(info.naming_contexts or [])
        conn.unbind()
    except Exception as e:
        r.error = str(e)
    return r


def authenticated_dump(host: str, port: int, use_ssl: bool, user: str,
                       password: str, domain: str, base_dn: str | None) -> Result:
    try:
        from ldap3 import Server, Connection, ALL, SUBTREE, NTLM  # type: ignore
    except ImportError:
        r = Result(host=host)
        r.error = "ldap3 not installed; pip install ldap3"
        return r

    r = anonymous_probe(host, port, use_ssl)
    if r.error and not r.naming_contexts:
        return r

    base = base_dn or (r.rootdse or {}).get("defaultNamingContext")
    if not base:
        r.error = (r.error or "") + "; could not determine base DN"
        return r

    bind_user = f"{domain}\\{user}" if domain else user
    server = Server(host, port=port, use_ssl=use_ssl, get_info=ALL,
                    connect_timeout=4)
    try:
        conn = Connection(server, user=bind_user, password=password,
                          authentication=NTLM, auto_bind=True)
    except Exception as e:
        r.error = f"bind failed: {e}"
        return r

    # Users
    try:
        conn.search(
            base, "(&(objectCategory=person)(objectClass=user))",
            search_scope=SUBTREE, attributes=[
                "sAMAccountName", "userPrincipalName", "userAccountControl",
                "memberOf", "description", "pwdLastSet", "lastLogonTimestamp",
                "adminCount", "servicePrincipalName"
            ], paged_size=500
        )
        for entry in conn.entries:
            uac_val = int(entry.userAccountControl.value or 0)
            uac_flags = decode_uac(uac_val)
            user_dict = {
                "samAccountName": str(entry.sAMAccountName.value or ""),
                "userPrincipalName": str(entry.userPrincipalName.value or ""),
                "uac": uac_val,
                "uac_flags": uac_flags,
                "description": str(entry.description.value or ""),
                "memberOf_count": len(entry.memberOf.values or []),
                "spns": list(entry.servicePrincipalName.values or []),
                "adminCount": int(entry.adminCount.value or 0),
            }
            r.users.append(user_dict)
            if "DONT_REQUIRE_PREAUTH" in uac_flags and "ACCOUNTDISABLE" not in uac_flags:
                r.asrep_users.append(user_dict)
            if user_dict["spns"]:
                r.spns.append(user_dict)
            if user_dict["adminCount"] == 1:
                r.admincount.append(user_dict)
    except Exception as e:
        r.error = (r.error or "") + f"; user search failed: {e}"

    # Groups
    try:
        conn.search(
            base, "(objectClass=group)", search_scope=SUBTREE,
            attributes=["cn", "member"], paged_size=500
        )
        for entry in conn.entries:
            r.groups.append({
                "cn": str(entry.cn.value or ""),
                "member_count": len(entry.member.values or []),
            })
    except Exception as e:
        r.error = (r.error or "") + f"; group search failed: {e}"

    # Computers
    try:
        conn.search(
            base, "(objectClass=computer)", search_scope=SUBTREE,
            attributes=["dNSHostName", "operatingSystem", "operatingSystemVersion"],
            paged_size=500
        )
        for entry in conn.entries:
            r.computers.append({
                "host": str(entry.dNSHostName.value or ""),
                "os": str(entry.operatingSystem.value or ""),
                "version": str(entry.operatingSystemVersion.value or ""),
            })
    except Exception as e:
        r.error = (r.error or "") + f"; computer search failed: {e}"

    try:
        conn.unbind()
    except Exception:
        pass
    return r


def render_text(r: Result, color: bool) -> str:
    out = [paint(f"\n=== LDAP recon for {r.host} ===", BOLD, color)]
    if r.error:
        out.append(paint(f"errors: {r.error}", YELLOW, color))
    if r.rootdse:
        out.append(paint("RootDSE:", CYAN := BOLD, color))
        for k, v in r.rootdse.items():
            out.append(f"  {k}: {v}")
    if r.naming_contexts:
        out.append(f"naming contexts: {', '.join(r.naming_contexts)}")
    if r.users:
        out.append(paint(f"\nUsers: {len(r.users)}", BOLD, color))
        out.append(paint(f"  AS-REP roastable: {len(r.asrep_users)}",
                         RED if r.asrep_users else GREY, color))
        for u in r.asrep_users[:20]:
            out.append(f"    - {u['samAccountName']}")
        out.append(paint(f"  Kerberoastable (SPN set): {len(r.spns)}",
                         RED if r.spns else GREY, color))
        for u in r.spns[:20]:
            out.append(f"    - {u['samAccountName']}  ({len(u['spns'])} SPN)")
        out.append(paint(f"  adminCount=1: {len(r.admincount)}",
                         YELLOW if r.admincount else GREY, color))
    if r.computers:
        out.append(paint(f"\nComputers: {len(r.computers)}", BOLD, color))
        for c in r.computers[:10]:
            out.append(f"    - {c['host']:<35} {c['os']} {c['version']}")
        if len(r.computers) > 10:
            out.append(f"    ... and {len(r.computers) - 10} more")
    if r.groups:
        out.append(paint(f"\nGroups: {len(r.groups)}", BOLD, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="LDAP / Active Directory enumeration.")
    ap.add_argument("-t", "--target", required=True, help="DC IP or hostname")
    ap.add_argument("--port", type=int, default=389)
    ap.add_argument("--ssl", action="store_true",
                    help="use LDAPS (sets default port to 636)")
    ap.add_argument("-u", "--user", default="")
    ap.add_argument("-p", "--password", default="")
    ap.add_argument("-d", "--domain", default="", help="NETBIOS domain")
    ap.add_argument("--base-dn", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()

    color = sys.stdout.isatty() and not args.no_color and not args.json
    if args.ssl and args.port == 389:
        args.port = 636

    if args.user:
        result = authenticated_dump(args.target, args.port, args.ssl,
                                     args.user, args.password, args.domain,
                                     args.base_dn)
    else:
        result = anonymous_probe(args.target, args.port, args.ssl)

    if args.json:
        print(json.dumps(asdict(result), indent=2, default=str))
    else:
        print(render_text(result, color))
    return 0 if not result.error else 1


if __name__ == "__main__":
    sys.exit(main())
