#!/usr/bin/env python3
"""
redshift_toolkit.protocols.smb_recon — SMB enumeration the way internal
pentesters actually use it.

What it reports for each target
-------------------------------
- SMB dialects supported (SMB1, SMB2.0.2, 2.1, 3.0, 3.0.2, 3.1.1)
- Signing required / signing enabled (the relay-attack predicate)
- OS / domain / hostname (from session setup response)
- Anonymous IPC$ access (null-session)
- Share enumeration (with creds if provided)
- Per-share read/write probe (optional)

Why this matters
----------------
Within the first 30 minutes of an internal pentest, you want a CSV-like
view of every reachable Windows host and *which ones do not require SMB
signing*. Those are your relay candidates for Module 21.

Usage
-----
  python3 -m redshift_toolkit.protocols.smb_recon -t 10.0.0.10
  python3 -m redshift_toolkit.protocols.smb_recon -t 10.0.0.0/24 --concurrency 50
  python3 -m redshift_toolkit.protocols.smb_recon -t 10.0.0.10 \\
      -u alice -p Password1 --shares
  python3 -m redshift_toolkit.protocols.smb_recon -t 10.0.0.10 \\
      -u alice -H 'aad3b...:5d4...' --shares --json

Requires
--------
  pip install impacket

Author: Redshift Project — Module 08
License: MIT
"""

from __future__ import annotations

import argparse
import asyncio
import ipaddress
import json
import socket
import struct
import sys
from concurrent.futures import ThreadPoolExecutor
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
class SmbHost:
    host: str
    reachable: bool = False
    smb1: bool = False
    smb2_dialects: list[str] = field(default_factory=list)
    signing_required: bool | None = None
    os: str | None = None
    domain: str | None = None
    hostname: str | None = None
    null_session: bool = False
    shares: list[dict] = field(default_factory=list)
    error: str | None = None


# ─── Pure-stdlib raw SMB negotiate (works without impacket) ────────────────
SMB1_NEGOTIATE = bytes.fromhex(
    "00000054ff534d4272000000001853c800000000000000000000000000ff"
    "fe00000000003100024c414e4d414e312e3000024c4d312e30580032"
    "0002444f532044303032000200002c00006e6500024c414e4d414e322e3100"
)
SMB2_NEGOTIATE = bytes.fromhex(
    "000000a4fe534d4240000100000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "000000002400050000000000000000000000000000000000700000000200000202"
    "10020000030203110300000000000000010000002000000000000000000000007800"
    "0000080001000000000020000200010002000000000004000200"
)


def _send_recv(host: str, payload: bytes, timeout: float = 3.0) -> bytes | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, 445))
            s.sendall(payload)
            data = b""
            while len(data) < 64:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
            return data
    except OSError:
        return None


def _raw_dialect_check(host: str) -> SmbHost:
    info = SmbHost(host=host)

    # SMB2 negotiate first
    resp2 = _send_recv(host, SMB2_NEGOTIATE)
    if resp2 and len(resp2) >= 70 and resp2[4:8] == b"\xfeSMB":
        info.reachable = True
        # Parse dialect (offset 72) and security mode (offset 70)
        try:
            sec_mode = resp2[70]
            dialect = struct.unpack("<H", resp2[72:74])[0]
            dialect_map = {
                0x0202: "SMB 2.0.2", 0x0210: "SMB 2.1",
                0x0300: "SMB 3.0", 0x0302: "SMB 3.0.2",
                0x0311: "SMB 3.1.1",
            }
            info.smb2_dialects = [dialect_map.get(dialect, f"0x{dialect:04x}")]
            # bit 0 = signing enabled, bit 1 = signing required
            info.signing_required = bool(sec_mode & 0x02)
        except Exception:
            pass
        return info

    # Fall back to SMB1
    resp1 = _send_recv(host, SMB1_NEGOTIATE)
    if resp1 and len(resp1) >= 36 and resp1[4:8] == b"\xffSMB":
        info.reachable = True
        info.smb1 = True
        # SMB1 signing flag is at SecurityMode byte (offset 39 in negotiate response)
        try:
            sec_mode = resp1[39]
            info.signing_required = bool(sec_mode & 0x08)  # signing required bit
        except Exception:
            pass
        return info

    return info


# ─── Optional impacket-driven enrichment ────────────────────────────────────
def _impacket_enrich(info: SmbHost, user: str, password: str, ntlm: str,
                     domain: str, want_shares: bool) -> SmbHost:
    try:
        from impacket.smbconnection import SMBConnection  # type: ignore
        from impacket.nmb import NetBIOSError                 # type: ignore
    except ImportError:
        info.error = "impacket not installed; raw negotiate only"
        return info
    try:
        conn = SMBConnection(info.host, info.host, sess_port=445, timeout=4)
        info.hostname = conn.getServerName()
        info.os = conn.getServerOS()
        info.domain = conn.getServerDomain() or conn.getServerDNSDomainName()

        # Null session
        try:
            conn.login("", "")
            info.null_session = True
            if want_shares:
                for s in conn.listShares():
                    info.shares.append({
                        "name": s["shi1_netname"][:-1],
                        "remark": s["shi1_remark"][:-1],
                    })
        except Exception:
            pass

        # Authenticated
        if user and (password or ntlm):
            try:
                conn = SMBConnection(info.host, info.host, sess_port=445, timeout=4)
                if ntlm:
                    lm, nt = (ntlm.split(":", 1) + [""])[:2] if ":" in ntlm else ("", ntlm)
                    conn.login(user, "", domain or "", lmhash=lm, nthash=nt)
                else:
                    conn.login(user, password, domain or "")
                if want_shares:
                    info.shares = []
                    for s in conn.listShares():
                        info.shares.append({
                            "name": s["shi1_netname"][:-1],
                            "remark": s["shi1_remark"][:-1],
                        })
            except Exception as e:
                info.error = f"auth failed: {e}"
        try:
            conn.logoff()
        except Exception:
            pass
    except Exception as e:
        info.error = (info.error or "") + f"; impacket: {e}"
    return info


def scan_one(host: str, user: str, password: str, ntlm: str,
             domain: str, want_shares: bool) -> SmbHost:
    info = _raw_dialect_check(host)
    if info.reachable and (user or want_shares):
        info = _impacket_enrich(info, user, password, ntlm, domain, want_shares)
    return info


def expand(spec: str) -> list[str]:
    spec = spec.strip()
    if "/" in spec:
        return [str(ip) for ip in ipaddress.ip_network(spec, strict=False).hosts()]
    if "-" in spec and spec.count(".") == 3:
        base, last = spec.rsplit(".", 1)
        if "-" in last:
            lo, hi = last.split("-")
            return [f"{base}.{i}" for i in range(int(lo), int(hi) + 1)]
    try:
        return [socket.gethostbyname(spec)]
    except socket.gaierror:
        return [spec]


def render_text(results: list[SmbHost], color: bool) -> str:
    out = []
    for r in results:
        if not r.reachable:
            out.append(paint(f"\n[-] {r.host}: 445/tcp not reachable", GREY, color))
            continue
        signing = ("REQUIRED"
                   if r.signing_required is True
                   else "NOT required (relay candidate!)"
                   if r.signing_required is False
                   else "unknown")
        signing_color = GREEN if r.signing_required else RED
        out.append(paint(f"\n── {r.host} ──", BOLD, color))
        if r.smb1:
            out.append(paint(f"  SMB1: SUPPORTED  (DEPRECATE — EternalBlue family)",
                             RED, color))
        if r.smb2_dialects:
            out.append(f"  SMB2 dialect: {', '.join(r.smb2_dialects)}")
        out.append(f"  signing: {paint(signing, signing_color, color)}")
        if r.os: out.append(f"  os:       {r.os}")
        if r.domain: out.append(f"  domain:   {r.domain}")
        if r.hostname: out.append(f"  hostname: {r.hostname}")
        if r.null_session:
            out.append(paint("  null session: ALLOWED", RED, color))
        if r.shares:
            out.append(f"  shares ({len(r.shares)}):")
            for s in r.shares:
                out.append(f"    - {s['name']:<20}  {s['remark']}")
        if r.error:
            out.append(paint(f"  note: {r.error}", YELLOW, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="SMB enumeration (version, signing, shares).")
    ap.add_argument("-t", "--target", required=True,
                    help="IP, CIDR, range a.b.c.x-y, or hostname")
    ap.add_argument("-u", "--user", default="")
    ap.add_argument("-p", "--password", default="")
    ap.add_argument("-H", "--ntlm", default="",
                    help="NTLM hash for pass-the-hash (LM:NT or just NT)")
    ap.add_argument("-d", "--domain", default="")
    ap.add_argument("--shares", action="store_true",
                    help="enumerate shares (requires impacket; uses null session if no creds)")
    ap.add_argument("--concurrency", type=int, default=20)
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()

    color = sys.stdout.isatty() and not args.no_color and args.format == "text"
    targets = sorted(set(expand(args.target)))

    print(paint(f"[*] scanning {len(targets)} target(s)", BOLD, color), file=sys.stderr)

    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        results = list(ex.map(
            lambda h: scan_one(h, args.user, args.password, args.ntlm,
                                args.domain, args.shares),
            targets
        ))

    if args.format == "json":
        print(json.dumps([asdict(r) for r in results], indent=2))
    else:
        print(render_text(results, color))
        relay = sum(1 for r in results if r.signing_required is False)
        print(paint(
            f"\n[*] {relay} host(s) without required signing — relay candidates.",
            BOLD, color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
