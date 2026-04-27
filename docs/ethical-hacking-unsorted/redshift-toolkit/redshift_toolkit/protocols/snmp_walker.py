#!/usr/bin/env python3
"""
redshift_toolkit.protocols.snmp_walker — SNMP community brute + high-value MIB walk.

What it does
------------
1. Sends `SNMPv2c GetRequest` for sysDescr.0 with each community string
   in a list. A response means "valid community string."
2. For every host that returned a valid community, walks high-value OIDs
   that historically yield: running processes, installed software, IP
   addresses, ARP tables, routing tables, Windows users (legacy MIBs),
   and listening TCP/UDP services.
3. Reports findings, JSON or text.

Why we wrote our own
--------------------
- `snmpwalk` shells well but doesn't pivot easily to JSON.
- `pysnmp` is heavy and inconsistent across Python versions.
- The wire format is simple. We build the GetRequest by hand.

Wire format
-----------
SNMPv2c uses ASN.1 BER. Top-level SEQUENCE:
  INTEGER  version (1 = v2c, 0 = v1)
  OCTETSTRING  community
  PDU (Get/GetNext/Set/Response)
    INTEGER request-id
    INTEGER error-status
    INTEGER error-index
    SEQUENCE varbinds
      SEQUENCE varbind
        OBJECT IDENTIFIER name
        Value (NULL for Get)

Usage
-----
  python3 -m redshift_toolkit.protocols.snmp_walker -t 10.0.0.10
  python3 -m redshift_toolkit.protocols.snmp_walker -t 10.0.0.0/24 \\
      --communities common.txt --json
  python3 -m redshift_toolkit.protocols.snmp_walker -t 10.0.0.10 \\
      --community public --walk 1.3.6.1.2.1.25.4.2.1.2

Author: Redshift Project — Module 08
License: MIT
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import socket
import struct
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


COMMON_COMMUNITIES = [
    "public", "private", "community", "manager", "admin", "test",
    "router", "switch", "snmp", "snmpd", "default", "cisco", "secret",
    "read", "write", "guest", "monitor", "all", "0", "system",
]

HIGH_VALUE_OIDS = {
    "sysDescr":        "1.3.6.1.2.1.1.1.0",
    "sysName":         "1.3.6.1.2.1.1.5.0",
    "sysContact":      "1.3.6.1.2.1.1.4.0",
    "sysLocation":     "1.3.6.1.2.1.1.6.0",
    "sysUpTime":       "1.3.6.1.2.1.1.3.0",
    "sysObjectID":     "1.3.6.1.2.1.1.2.0",
    # walks (we GETNEXT through these)
    "hrSWRunName":     "1.3.6.1.2.1.25.4.2.1.2",   # running processes
    "hrSWInstalledName": "1.3.6.1.2.1.25.6.3.1.2", # installed software
    "ipAdEntAddr":     "1.3.6.1.2.1.4.20.1.1",     # interface IPs
    "tcpListenLocalPort": "1.3.6.1.2.1.6.13.1.3",  # listening TCP ports
    "ifDescr":         "1.3.6.1.2.1.2.2.1.2",      # interface descriptions
    "atPhysAddress":   "1.3.6.1.2.1.3.1.1.2",      # ARP table (legacy)
}


# ─── Minimal ASN.1 BER encoder/decoder ──────────────────────────────────────
def _enc_len(n: int) -> bytes:
    if n < 0x80:
        return bytes([n])
    blen = (n.bit_length() + 7) // 8
    return bytes([0x80 | blen]) + n.to_bytes(blen, "big")


def _enc_int(value: int) -> bytes:
    if value == 0:
        body = b"\x00"
    else:
        blen = (value.bit_length() + 8) // 8
        body = value.to_bytes(blen, "big", signed=True)
    return b"\x02" + _enc_len(len(body)) + body


def _enc_string(s: bytes) -> bytes:
    return b"\x04" + _enc_len(len(s)) + s


def _enc_null() -> bytes:
    return b"\x05\x00"


def _enc_oid(oid: str) -> bytes:
    parts = [int(p) for p in oid.split(".")]
    body = bytes([parts[0] * 40 + parts[1]])
    for n in parts[2:]:
        if n == 0:
            body += b"\x00"
            continue
        chunk = []
        while n:
            chunk.append(n & 0x7F)
            n >>= 7
        chunk = list(reversed(chunk))
        for i in range(len(chunk) - 1):
            chunk[i] |= 0x80
        body += bytes(chunk)
    return b"\x06" + _enc_len(len(body)) + body


def _enc_seq(body: bytes, tag: int = 0x30) -> bytes:
    return bytes([tag]) + _enc_len(len(body)) + body


def build_get_request(community: str, oid: str, request_id: int,
                      pdu_tag: int = 0xA0) -> bytes:
    """pdu_tag: 0xA0 = GetRequest, 0xA1 = GetNextRequest, 0xA2 = GetResponse."""
    varbind = _enc_seq(_enc_oid(oid) + _enc_null())
    varbinds = _enc_seq(varbind)
    pdu = _enc_seq(
        _enc_int(request_id) + _enc_int(0) + _enc_int(0) + varbinds,
        tag=pdu_tag,
    )
    return _enc_seq(_enc_int(1) + _enc_string(community.encode()) + pdu)


def _read_len(data: bytes, off: int) -> tuple[int, int]:
    first = data[off]; off += 1
    if first < 0x80:
        return first, off
    n = first & 0x7F
    return int.from_bytes(data[off:off + n], "big"), off + n


def _decode_oid(data: bytes) -> str:
    if not data:
        return ""
    first = data[0]
    out = [str(first // 40), str(first % 40)]
    n = 0
    for b in data[1:]:
        n = (n << 7) | (b & 0x7F)
        if not (b & 0x80):
            out.append(str(n)); n = 0
    return ".".join(out)


def parse_response(data: bytes) -> list[tuple[str, object]]:
    """Walk a GetResponse and return list of (oid, value)."""
    # SEQUENCE
    assert data[0] == 0x30
    _, off = _read_len(data, 1)
    # version INTEGER
    assert data[off] == 0x02
    vlen, off2 = _read_len(data, off + 1)
    off = off2 + vlen
    # community OCTETSTRING
    assert data[off] == 0x04
    clen, off2 = _read_len(data, off + 1)
    off = off2 + clen
    # PDU
    pdu_tag = data[off]
    plen, off2 = _read_len(data, off + 1)
    off = off2
    pdu_end = off + plen
    # request-id, error-status, error-index
    for _ in range(3):
        assert data[off] == 0x02
        ln, off2 = _read_len(data, off + 1)
        off = off2 + ln
    # varbinds SEQUENCE
    assert data[off] == 0x30
    vlen, off2 = _read_len(data, off + 1)
    off = off2
    end = off + vlen
    out = []
    while off < end:
        # SEQUENCE varbind
        assert data[off] == 0x30
        vlen, off2 = _read_len(data, off + 1)
        off = off2
        # OID
        assert data[off] == 0x06
        olen, off2 = _read_len(data, off + 1)
        oid = _decode_oid(data[off2:off2 + olen])
        off = off2 + olen
        # value
        vtag = data[off]
        vlen2, off2 = _read_len(data, off + 1)
        vbody = data[off2:off2 + vlen2]
        off = off2 + vlen2

        if vtag == 0x04:  # OCTET STRING
            try:
                value = vbody.decode("utf-8")
            except UnicodeDecodeError:
                value = vbody.hex()
        elif vtag == 0x02:  # INTEGER
            value = int.from_bytes(vbody, "big", signed=True) if vbody else 0
        elif vtag == 0x06:
            value = _decode_oid(vbody)
        elif vtag == 0x40 and len(vbody) == 4:  # IPAddress
            value = ".".join(str(b) for b in vbody)
        elif vtag in (0x41, 0x42, 0x43, 0x46, 0x47):  # Counter, Gauge, etc.
            value = int.from_bytes(vbody, "big") if vbody else 0
        elif vtag == 0x05:
            value = None
        elif vtag in (0x80, 0x81, 0x82):  # noSuchObject / noSuchInstance / endOfMib
            value = None  # caller can detect by absence of further data
        else:
            value = vbody.hex()
        out.append((oid, value))
    return out


def udp_query(host: str, payload: bytes, timeout: float) -> bytes | None:
    fam = socket.AF_INET6 if ":" in host else socket.AF_INET
    s = socket.socket(fam, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        s.sendto(payload, (host, 161))
        data, _ = s.recvfrom(8192)
        return data
    except (socket.timeout, OSError):
        return None
    finally:
        s.close()


@dataclass
class SnmpHost:
    host: str
    valid_communities: list[str] = field(default_factory=list)
    findings: dict[str, object] = field(default_factory=dict)


def probe_host(host: str, communities: list[str], timeout: float,
               do_walk: bool, walk_limit: int) -> SnmpHost:
    out = SnmpHost(host=host)
    for c in communities:
        payload = build_get_request(c, HIGH_VALUE_OIDS["sysDescr"],
                                    request_id=int.from_bytes(os.urandom(2), "big"))
        resp = udp_query(host, payload, timeout)
        if not resp:
            continue
        try:
            varbinds = parse_response(resp)
        except Exception:
            continue
        if varbinds and varbinds[0][1] is not None:
            out.valid_communities.append(c)
            if not do_walk:
                continue
            # Static GETs
            for name, oid in HIGH_VALUE_OIDS.items():
                if not oid.endswith(".0"):
                    continue
                payload = build_get_request(
                    c, oid, request_id=int.from_bytes(os.urandom(2), "big"))
                r = udp_query(host, payload, timeout)
                if r:
                    try:
                        vb = parse_response(r)
                        if vb:
                            out.findings[name] = vb[0][1]
                    except Exception:
                        pass
            # GETNEXT walk for the multi-instance OIDs (cap to walk_limit)
            for name, oid in HIGH_VALUE_OIDS.items():
                if oid.endswith(".0"):
                    continue
                values = []
                cur = oid
                for _ in range(walk_limit):
                    payload = build_get_request(
                        c, cur,
                        request_id=int.from_bytes(os.urandom(2), "big"),
                        pdu_tag=0xA1,  # GetNextRequest
                    )
                    r = udp_query(host, payload, timeout)
                    if not r:
                        break
                    try:
                        vb = parse_response(r)
                    except Exception:
                        break
                    if not vb:
                        break
                    next_oid, val = vb[0]
                    if not next_oid.startswith(oid + "."):
                        break
                    values.append(val)
                    cur = next_oid
                if values:
                    out.findings[name] = values
            break  # one valid community is enough for our purposes
    return out


def expand(spec: str) -> list[str]:
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


def render_text(reports: list[SnmpHost], color: bool) -> str:
    out = []
    for r in reports:
        if not r.valid_communities:
            out.append(paint(f"\n[-] {r.host}: no valid community", GREY, color))
            continue
        out.append(paint(f"\n── {r.host} ──", BOLD, color))
        out.append(paint(f"  community: {', '.join(r.valid_communities)}", GREEN, color))
        for name, val in r.findings.items():
            if isinstance(val, list):
                out.append(f"  {name} ({len(val)} entries):")
                for v in val[:10]:
                    out.append(f"    - {v}")
                if len(val) > 10:
                    out.append(f"    ... and {len(val) - 10} more")
            else:
                vs = str(val)
                if len(vs) > 100:
                    vs = vs[:100] + "…"
                out.append(f"  {name}: {vs}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="SNMP community brute + MIB walk.")
    ap.add_argument("-t", "--target", required=True)
    ap.add_argument("--communities",
                    help="file with one community string per line")
    ap.add_argument("--community",
                    help="single community to use (skips brute phase)")
    ap.add_argument("--walk", default=None,
                    help="OID to walk (replaces default high-value list)")
    ap.add_argument("--walk-limit", type=int, default=200,
                    help="max GETNEXT iterations per OID tree")
    ap.add_argument("--timeout", type=float, default=2.0)
    ap.add_argument("--concurrency", type=int, default=20)
    ap.add_argument("--no-walk", action="store_true",
                    help="only validate the community, don't walk")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()

    color = sys.stdout.isatty() and not args.no_color and args.format == "text"

    if args.community:
        communities = [args.community]
    elif args.communities:
        with open(args.communities) as f:
            communities = [ln.strip() for ln in f
                           if ln.strip() and not ln.startswith("#")]
    else:
        communities = COMMON_COMMUNITIES

    # If --walk override is given, swap it in.
    if args.walk:
        HIGH_VALUE_OIDS.clear()
        HIGH_VALUE_OIDS["custom"] = args.walk

    targets = sorted(set(expand(args.target)))

    print(paint(
        f"[*] {len(targets)} target(s), {len(communities)} community guess(es)",
        BOLD, color
    ), file=sys.stderr)

    reports: list[SnmpHost] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(probe_host, h, communities, args.timeout,
                          not args.no_walk, args.walk_limit): h for h in targets}
        for fut in as_completed(futs):
            reports.append(fut.result())

    reports.sort(key=lambda r: r.host)

    if args.format == "json":
        print(json.dumps([asdict(r) for r in reports], indent=2, default=str))
    else:
        print(render_text(reports, color))
        valid_count = sum(1 for r in reports if r.valid_communities)
        print(paint(
            f"\n[*] {valid_count}/{len(reports)} hosts had valid SNMP community.",
            BOLD, color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
