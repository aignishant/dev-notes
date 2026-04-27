#!/usr/bin/env python3
"""
failed_ssh_analyzer.py
======================

Parse Linux auth logs and produce an actionable report on SSH brute-force
attempts against your server.

DEFENSIVE USE
-------------
This script READS your own server's logs. It identifies:
  * Source IPs hammering your SSH service
  * Which usernames they tried (often gives away whose creds they're after)
  * Time windows of activity
  * Top usernames seen in failures
  * Whether any of those failures was followed by a SUCCESS (the scary case)

This is exactly what a SOC analyst, sysadmin, or incident responder does daily.

Sources supported
-----------------
  * /var/log/auth.log (Debian/Ubuntu, syslog format)
  * /var/log/secure   (RHEL/CentOS/Fedora, syslog format)
  * journalctl -u ssh -o short-iso (piped via stdin)
  * Any text file that contains the standard sshd messages

Usage
-----
    python failed_ssh_analyzer.py /var/log/auth.log
    sudo python failed_ssh_analyzer.py            # auto-detect log file
    journalctl -u ssh -o short | python failed_ssh_analyzer.py -
    python failed_ssh_analyzer.py auth.log --top 20 --json out.json

Author: Ethical Hacking Mastery curriculum
License: Educational use
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("[-] rich is required: pip install rich", file=sys.stderr)
    sys.exit(1)

console = Console()


# --------------------------------------------------------------------------- #
# Regexes covering common sshd log shapes
# --------------------------------------------------------------------------- #
RE_FAILED = re.compile(
    r"Failed password for (?:invalid user )?(?P<user>\S+) from "
    r"(?P<ip>\d{1,3}(?:\.\d{1,3}){3}|[0-9a-fA-F:]+) port (?P<port>\d+)"
)
RE_INVALID = re.compile(
    r"Invalid user (?P<user>\S+) from "
    r"(?P<ip>\d{1,3}(?:\.\d{1,3}){3}|[0-9a-fA-F:]+)"
)
RE_ACCEPTED = re.compile(
    r"Accepted (?:password|publickey) for (?P<user>\S+) from "
    r"(?P<ip>\d{1,3}(?:\.\d{1,3}){3}|[0-9a-fA-F:]+) port (?P<port>\d+)"
)

# Capture leading timestamp (best-effort). Matches both syslog and ISO.
RE_TS = re.compile(
    r"^(?P<ts>"
    r"\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}"           # syslog: 'Apr 27 09:00:00'
    r"|"
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[.\d]*[+\-Z][0-9:]*"  # ISO
    r")"
)


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
@dataclass
class IpStats:
    ip: str
    failed: int = 0
    invalid_user: int = 0
    successes: int = 0
    users_tried: Counter = field(default_factory=Counter)
    first_seen: str | None = None
    last_seen: str | None = None
    successful_logins: list[tuple[str, str]] = field(default_factory=list)  # (user, ts)


# --------------------------------------------------------------------------- #
# Parser
# --------------------------------------------------------------------------- #
def parse_lines(lines):
    by_ip: dict[str, IpStats] = {}
    overall_users = Counter()

    for line in lines:
        ts_match = RE_TS.search(line)
        ts = ts_match.group("ts") if ts_match else None

        m_fail = RE_FAILED.search(line)
        m_inv = RE_INVALID.search(line)
        m_ok = RE_ACCEPTED.search(line)

        if not (m_fail or m_inv or m_ok):
            continue

        m = m_fail or m_inv or m_ok
        ip = m.group("ip")
        user = m.group("user")
        s = by_ip.setdefault(ip, IpStats(ip=ip))

        if s.first_seen is None:
            s.first_seen = ts
        s.last_seen = ts

        if m_fail:
            s.failed += 1
            s.users_tried[user] += 1
            overall_users[user] += 1
        if m_inv:
            s.invalid_user += 1
            s.users_tried[user] += 1
            overall_users[user] += 1
        if m_ok:
            s.successes += 1
            s.successful_logins.append((user, ts or ""))

    return by_ip, overall_users


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def render(by_ip: dict[str, IpStats], top_users: Counter, top: int) -> None:
    if not by_ip:
        console.print("[yellow]No SSH events found in the input.[/yellow]")
        return

    # Top attacker IPs by failed-attempt volume
    table = Table(title=f"Top {top} attacker IPs", header_style="bold cyan",
                  show_lines=False)
    table.add_column("IP")
    table.add_column("Failed", justify="right")
    table.add_column("Invalid user", justify="right")
    table.add_column("Successes", justify="right", style="bold")
    table.add_column("Distinct users", justify="right")
    table.add_column("Top user")
    table.add_column("First seen")
    table.add_column("Last seen")

    sorted_ips = sorted(
        by_ip.values(),
        key=lambda s: (s.failed + s.invalid_user, s.successes),
        reverse=True,
    )
    for s in sorted_ips[:top]:
        succ_style = "[red bold]" if s.successes else ""
        end = "[/red bold]" if s.successes else ""
        top_user, _ = s.users_tried.most_common(1)[0] if s.users_tried else ("-", 0)
        table.add_row(
            s.ip,
            str(s.failed),
            str(s.invalid_user),
            f"{succ_style}{s.successes}{end}",
            str(len(s.users_tried)),
            top_user,
            s.first_seen or "-",
            s.last_seen or "-",
        )
    console.print(table)

    # Top usernames probed
    table2 = Table(title=f"Top {top} usernames probed",
                   header_style="bold cyan", show_lines=False)
    table2.add_column("Username")
    table2.add_column("Attempts", justify="right")
    for u, c in top_users.most_common(top):
        table2.add_row(u, str(c))
    console.print(table2)

    # Special call-outs
    danger = [s for s in by_ip.values() if s.successes and (s.failed + s.invalid_user) >= 5]
    if danger:
        console.rule("[bold red]⚠  Successful logins from heavy-failure sources[/bold red]")
        for s in danger:
            console.print(
                f"[red bold]{s.ip}[/red bold] · "
                f"{s.failed + s.invalid_user} failures, "
                f"{s.successes} success(es)"
            )
            for user, ts in s.successful_logins:
                console.print(f"   ↳ user=[bold]{user}[/bold]  at  {ts}")
        console.print(
            "[yellow]Investigate immediately. A successful login after a brute-force "
            "campaign may indicate compromise.[/yellow]"
        )


# --------------------------------------------------------------------------- #
# Sources
# --------------------------------------------------------------------------- #
def find_default_log() -> str | None:
    for p in ("/var/log/auth.log", "/var/log/secure"):
        if os.path.isfile(p):
            return p
    return None


def read_source(path: str | None):
    if path == "-" or path is None and not sys.stdin.isatty():
        return sys.stdin
    if path is None:
        path = find_default_log()
        if path is None:
            raise SystemExit("[-] No log path given and /var/log/auth.log "
                             "/ /var/log/secure not found.")
    try:
        return open(path, "r", encoding="utf-8", errors="replace")
    except OSError as e:
        raise SystemExit(f"[-] Cannot open {path}: {e}")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Defensive SSH log analyzer.",
    )
    parser.add_argument("path", nargs="?", default=None,
                        help="Path to auth.log/secure, '-' for stdin, or omit to auto-detect")
    parser.add_argument("--top", type=int, default=10,
                        help="How many rows in the top-N tables (default 10)")
    parser.add_argument("--json", default=None,
                        help="Also write a JSON report to this path")
    args = parser.parse_args()

    src = read_source(args.path)
    by_ip, overall_users = parse_lines(src)

    if hasattr(src, "close"):
        try:
            src.close()
        except Exception:
            pass

    render(by_ip, overall_users, args.top)

    if args.json:
        out = {
            "ips": [
                {**asdict(s), "users_tried": dict(s.users_tried)}
                for s in by_ip.values()
            ],
            "top_users": overall_users.most_common(),
        }
        try:
            with open(args.json, "w") as f:
                json.dump(out, f, indent=2, default=str)
            console.print(f"[green]Wrote JSON report to {args.json}[/green]")
        except OSError as e:
            console.print(f"[red]Failed to write JSON: {e}[/red]")


if __name__ == "__main__":
    main()
