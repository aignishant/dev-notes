#!/usr/bin/env python3
"""
redshift_toolkit.protocols.smtp_recon — SMTP user enumeration and open
relay testing.

Capabilities
------------
- Banner grab (often reveals MTA: Postfix, Exim, Exchange, sendmail).
- VRFY username probe (often disabled, but worth checking).
- EXPN mailing-list probe.
- RCPT TO probe (most reliable user enumerator on permissive MTAs).
- Open relay test (cleanly).
- STARTTLS detection.
- Honors per-server rate limits with configurable delay.

Usage
-----
  python3 -m redshift_toolkit.protocols.smtp_recon -t mail.lab.local
  python3 -m redshift_toolkit.protocols.smtp_recon -t mail.lab.local \\
      --users users.txt --domain lab.local --method rcpt
  python3 -m redshift_toolkit.protocols.smtp_recon -t mail.lab.local \\
      --relay-test --json

Author: Redshift Project — Module 08
License: MIT — Authorized testing only.
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from dataclasses import dataclass, asdict, field

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


@dataclass
class SmtpReport:
    host: str
    port: int
    banner: str | None = None
    starttls: bool = False
    auth_methods: list[str] = field(default_factory=list)
    valid_users: list[str] = field(default_factory=list)
    invalid_users: list[str] = field(default_factory=list)
    open_relay: bool | None = None
    notes: list[str] = field(default_factory=list)


class SmtpClient:
    def __init__(self, host: str, port: int, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: socket.socket | None = None
        self.buf = b""

    def __enter__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))
        return self

    def __exit__(self, *a):
        try:
            self.sendcmd("QUIT")
        except Exception:
            pass
        if self.sock:
            self.sock.close()

    def _readline(self) -> bytes:
        while b"\n" not in self.buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                break
            self.buf += chunk
        line, _, self.buf = self.buf.partition(b"\n")
        return line + b"\n"

    def read_response(self) -> tuple[int, str]:
        lines = []
        while True:
            line = self._readline().decode("latin-1", errors="replace").rstrip("\r\n")
            lines.append(line)
            if len(line) < 4 or line[3] == " ":
                break
        return int(lines[0][:3]) if lines and lines[0][:3].isdigit() else 0, "\n".join(lines)

    def sendcmd(self, cmd: str) -> tuple[int, str]:
        self.sock.sendall((cmd + "\r\n").encode())
        return self.read_response()


def grab(host: str, port: int, helo_as: str, timeout: float) -> SmtpReport:
    rpt = SmtpReport(host=host, port=port)
    try:
        with SmtpClient(host, port, timeout) as c:
            code, banner = c.read_response()
            if code:
                rpt.banner = banner.split("\n", 1)[0]
            code, ehlo_resp = c.sendcmd(f"EHLO {helo_as}")
            if code == 250:
                for ln in ehlo_resp.splitlines():
                    text = ln[4:].strip()
                    if text.upper() == "STARTTLS":
                        rpt.starttls = True
                    if text.upper().startswith("AUTH"):
                        rpt.auth_methods = text.split()[1:]
            else:
                # Some MTAs reject EHLO; fall back to HELO
                c.sendcmd(f"HELO {helo_as}")
    except (socket.timeout, OSError) as e:
        rpt.notes.append(f"connect/banner error: {e}")
    return rpt


def enum_users(host: str, port: int, users: list[str], domain: str,
               method: str, helo_as: str, sender: str, delay: float,
               timeout: float, rpt: SmtpReport) -> SmtpReport:
    try:
        with SmtpClient(host, port, timeout) as c:
            c.read_response()
            code, _ = c.sendcmd(f"EHLO {helo_as}")
            if code != 250:
                c.sendcmd(f"HELO {helo_as}")

            for u in users:
                addr = f"{u}@{domain}" if "@" not in u else u
                if method == "vrfy":
                    code, msg = c.sendcmd(f"VRFY {addr}")
                    is_valid = code in (250, 251, 252)
                elif method == "expn":
                    code, msg = c.sendcmd(f"EXPN {u}")
                    is_valid = code == 250
                else:  # rcpt
                    c.sendcmd(f"RSET")
                    c.sendcmd(f"MAIL FROM: <{sender}>")
                    code, msg = c.sendcmd(f"RCPT TO: <{addr}>")
                    is_valid = code in (250, 251)
                (rpt.valid_users if is_valid else rpt.invalid_users).append(addr)
                if delay:
                    time.sleep(delay)
    except (socket.timeout, OSError) as e:
        rpt.notes.append(f"enum error: {e}")
    return rpt


def relay_test(host: str, port: int, helo_as: str, ext_from: str,
               ext_to: str, timeout: float, rpt: SmtpReport) -> SmtpReport:
    """Try to relay a message from `ext_from` to `ext_to`, where neither
    domain is local to the server. If RCPT succeeds and DATA is accepted
    without auth, the server is an open relay.
    """
    try:
        with SmtpClient(host, port, timeout) as c:
            c.read_response()
            c.sendcmd(f"EHLO {helo_as}")
            c.sendcmd(f"MAIL FROM: <{ext_from}>")
            code, msg = c.sendcmd(f"RCPT TO: <{ext_to}>")
            if code in (250, 251):
                rpt.open_relay = True
                rpt.notes.append(f"open relay: RCPT accepted ({msg.splitlines()[0]})")
            else:
                rpt.open_relay = False
                rpt.notes.append(f"relay refused: {msg.splitlines()[0]}")
            c.sendcmd("RSET")
    except (socket.timeout, OSError) as e:
        rpt.notes.append(f"relay-test error: {e}")
    return rpt


def render_text(r: SmtpReport, color: bool) -> str:
    out = [paint(f"\n── {r.host}:{r.port} ──", BOLD, color)]
    if r.banner:
        out.append(f"  banner: {r.banner}")
    out.append(f"  starttls: {paint('yes', GREEN, color) if r.starttls else paint('NO', RED, color)}")
    if r.auth_methods:
        out.append(f"  AUTH methods: {' '.join(r.auth_methods)}")
    if r.valid_users:
        out.append(paint(f"  valid users ({len(r.valid_users)}):", GREEN, color))
        for u in r.valid_users[:30]:
            out.append(f"    + {u}")
        if len(r.valid_users) > 30:
            out.append(f"    ... and {len(r.valid_users) - 30} more")
    if r.invalid_users and len(r.valid_users) == 0:
        out.append(paint(
            f"  no valid users found among {len(r.invalid_users)} attempts",
            GREY, color
        ))
    if r.open_relay is True:
        out.append(paint("  OPEN RELAY: YES", RED, color))
    elif r.open_relay is False:
        out.append(paint("  open relay: no", GREEN, color))
    for n in r.notes:
        out.append(paint(f"  note: {n}", YELLOW, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="SMTP recon: banner, user enum, open-relay test.")
    ap.add_argument("-t", "--target", required=True)
    ap.add_argument("--port", type=int, default=25)
    ap.add_argument("--users", help="file with usernames (one per line)")
    ap.add_argument("--domain", default="example.com",
                    help="domain to append when usernames are bare")
    ap.add_argument("--method", choices=["rcpt", "vrfy", "expn"], default="rcpt")
    ap.add_argument("--helo-as", default="redshift.local")
    ap.add_argument("--sender", default="probe@example.com")
    ap.add_argument("--delay", type=float, default=0.05,
                    help="sleep between probes to dodge rate limits")
    ap.add_argument("--timeout", type=float, default=5.0)
    ap.add_argument("--relay-test", action="store_true")
    ap.add_argument("--ext-from", default="probe@externaldomain1.invalid")
    ap.add_argument("--ext-to", default="dropbox@externaldomain2.invalid")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()

    color = sys.stdout.isatty() and not args.no_color and args.format == "text"

    rpt = grab(args.target, args.port, args.helo_as, args.timeout)
    if args.users:
        with open(args.users) as f:
            ulist = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
        enum_users(args.target, args.port, ulist, args.domain, args.method,
                   args.helo_as, args.sender, args.delay, args.timeout, rpt)
    if args.relay_test:
        relay_test(args.target, args.port, args.helo_as, args.ext_from,
                   args.ext_to, args.timeout, rpt)

    if args.format == "json":
        print(json.dumps(asdict(rpt), indent=2))
    else:
        print(render_text(rpt, color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
