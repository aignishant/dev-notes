#!/usr/bin/env python3
"""
redshift_toolkit.postex.ssh_tunnel — SSH port-forwarding wrapper with
keepalive and auto-reconnect.

Why not just `ssh -L`?
- Idle connections drop on stateful firewalls; we set ServerAliveInterval=30.
- Reconnect with exponential backoff after disconnect.
- Centralized logging of when tunnels open/close (forensics-friendly).
- Single command for local / remote / dynamic forwarding.

Wraps OpenSSH client (must be installed). For Python-native SSH, see
paramiko or asyncssh — both work but require additional setup.

Usage
-----
  # Dynamic SOCKS5 proxy through pivot
  python3 -m redshift_toolkit.postex.ssh_tunnel \\
      --target alice@pivot.example.com --dynamic 1080

  # Local forward (target's perspective): forward localhost:8445 → DC:445
  python3 -m redshift_toolkit.postex.ssh_tunnel \\
      --target alice@pivot.example.com \\
      --local 8445:dc01.lab.local:445

  # Remote forward: expose attacker's port 8000 on pivot:8000
  python3 -m redshift_toolkit.postex.ssh_tunnel \\
      --target alice@pivot.example.com \\
      --remote 8000:127.0.0.1:8000

  # Identity file + keepalive
  python3 -m redshift_toolkit.postex.ssh_tunnel \\
      --target alice@pivot.example.com -i ~/.ssh/eng \\
      --dynamic 1080 --keep-alive

Author: Redshift Project — Module 19
License: MIT
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def build_ssh_args(args) -> list[str]:
    cmd = ["ssh", "-N",  # no command
           "-o", "ServerAliveInterval=30",
           "-o", "ServerAliveCountMax=3",
           "-o", "ExitOnForwardFailure=yes",
           "-o", "StrictHostKeyChecking=accept-new"]

    if args.identity:
        cmd += ["-i", args.identity]
    if args.port:
        cmd += ["-p", str(args.port)]
    if args.verbose:
        cmd += ["-v"]
    if args.dynamic:
        cmd += ["-D", str(args.dynamic)]
    if args.local:
        cmd += ["-L", args.local]
    if args.remote:
        cmd += ["-R", args.remote]
    if args.jump:
        cmd += ["-J", args.jump]

    cmd.append(args.target)
    return cmd


def main():
    p = argparse.ArgumentParser(
        prog="ssh_tunnel",
        description="SSH port-forwarding wrapper.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--target", required=True, help="user@host")
    p.add_argument("-p", "--port", type=int, help="SSH port (default 22)")
    p.add_argument("-i", "--identity", help="SSH private key file")
    p.add_argument("-D", "--dynamic", type=int, help="Dynamic SOCKS5 port (e.g. 1080)")
    p.add_argument("-L", "--local", help="Local forward, e.g. 8445:dc:445")
    p.add_argument("-R", "--remote", help="Remote forward, e.g. 8000:localhost:8000")
    p.add_argument("-J", "--jump", help="ProxyJump (e.g. user@bastion:22)")
    p.add_argument("-k", "--keep-alive", action="store_true",
                   help="Auto-reconnect on disconnect (exponential backoff)")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    if not (args.dynamic or args.local or args.remote):
        sys.stderr.write("Specify at least one of --dynamic, --local, --remote\n")
        sys.exit(2)

    if not shutil.which("ssh"):
        sys.stderr.write("error: `ssh` not found in PATH\n")
        sys.exit(2)

    cmd = build_ssh_args(args)
    print(f"{GREEN}[+] SSH command: {' '.join(shlex.quote(x) for x in cmd)}{RESET}",
          file=sys.stderr)

    backoff = 2
    max_backoff = 120
    proc: subprocess.Popen | None = None

    def shutdown(*_):
        if proc:
            proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while True:
        start = time.time()
        try:
            proc = subprocess.Popen(cmd)
            ret = proc.wait()
            elapsed = time.time() - start
            print(f"{YELLOW}[!] SSH exited rc={ret} after {elapsed:.0f}s{RESET}",
                  file=sys.stderr)
        except Exception as e:
            print(f"{RED}[!] launch failed: {e}{RESET}", file=sys.stderr)

        if not args.keep_alive:
            break

        # Reset backoff if connection lasted >60s
        if time.time() - start > 60:
            backoff = 2
        else:
            backoff = min(backoff * 2, max_backoff)
        print(f"{YELLOW}[~] reconnecting in {backoff}s...{RESET}", file=sys.stderr)
        time.sleep(backoff)


if __name__ == "__main__":
    main()
