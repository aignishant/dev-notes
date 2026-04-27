#!/usr/bin/env python3
"""
redshift_toolkit.postex.winrm_exec — WinRM (WS-Management) remote
command execution.

WinRM (TCP 5985 HTTP, TCP 5986 HTTPS) is Microsoft's preferred remote
management protocol. It tends to look like legitimate admin traffic
(Enter-PSSession), making it a stealthier choice than SMB-service
techniques on hardened networks.

Auth: NTLM (default) or Kerberos (--use-kerb).

Usage
-----
  # NTLM
  python3 -m redshift_toolkit.postex.winrm_exec \\
      --target 10.0.0.50 --user alice -p 'Password1' \\
      --command 'whoami; hostname'

  # Kerberos
  KRB5CCNAME=/tmp/alice.ccache python3 -m redshift_toolkit.postex.winrm_exec \\
      --target dc01.lab.local --user alice --use-kerb \\
      --command 'Get-Process | Select Name,Id'

  # HTTPS (5986) with self-signed cert acceptance
  python3 -m redshift_toolkit.postex.winrm_exec \\
      --target 10.0.0.50 --user alice -p 'Password1' \\
      --port 5986 --ssl --no-verify --command 'whoami'

Requires
--------
  pip install pypsrp        (preferred)
  OR
  pip install requests-ntlm xmltodict (fallback subset)

Author: Redshift Project — Module 19
License: MIT
"""

from __future__ import annotations

import argparse
import sys


GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def execute_pypsrp(target: str, port: int, ssl: bool, user: str, password: str,
                   domain: str, command: str, use_kerb: bool, no_verify: bool) -> str:
    try:
        from pypsrp.client import Client
    except ImportError:
        raise SystemExit("pypsrp not installed: pip install pypsrp")

    auth = "kerberos" if use_kerb else "ntlm"
    user_str = f"{domain}\\{user}" if domain and not use_kerb else user
    client = Client(
        target, username=user_str, password=password,
        port=port, ssl=ssl, auth=auth, cert_validation=not no_verify,
    )
    out, streams, had_errors = client.execute_cmd(command)
    if had_errors and streams.error:
        out += "\n[stderr]\n" + "\n".join(str(e) for e in streams.error)
    client.close()
    return out


def main():
    p = argparse.ArgumentParser(
        prog="winrm_exec",
        description="WinRM remote command execution (NTLM or Kerberos).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--target", required=True)
    p.add_argument("--port", type=int, default=5985)
    p.add_argument("--ssl", action="store_true", help="Use HTTPS (5986)")
    p.add_argument("--no-verify", action="store_true", help="Disable cert verification")
    p.add_argument("--user", required=True)
    p.add_argument("-p", "--password", default="")
    p.add_argument("--domain", default="")
    p.add_argument("--use-kerb", action="store_true",
                   help="Use Kerberos auth (KRB5CCNAME must be set)")
    p.add_argument("--command", required=True)
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args()

    on = sys.stdout.isatty() and not args.no_color
    print(f"{GREEN if on else ''}[+] WinRM {'kerberos' if args.use_kerb else 'ntlm'} "
          f"→ {args.target}:{args.port}{RESET if on else ''}", file=sys.stderr)

    try:
        out = execute_pypsrp(args.target, args.port, args.ssl,
                             args.user, args.password, args.domain,
                             args.command, args.use_kerb, args.no_verify)
    except SystemExit:
        raise
    except Exception as e:
        print(f"{RED if on else ''}[!] failed: {e}{RESET if on else ''}", file=sys.stderr)
        sys.exit(1)
    print(out, end="")


if __name__ == "__main__":
    main()
