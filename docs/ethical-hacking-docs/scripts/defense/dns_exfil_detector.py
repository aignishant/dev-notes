#!/usr/bin/env python3
"""DNS tunneling / exfiltration detector.

Flags suspicious DNS query patterns indicative of tunneling or
exfiltration:
  - Long subdomain labels (e.g. > 50 chars)
  - High Shannon entropy in subdomain (> 4.0)
  - High query rate per parent domain
  - Unusual record types (TXT, NULL) at high volume

Reads either:
  - Zeek `dns.log` (TSV, both classic and JSON streamed)
  - PCAP file (requires `scapy`)

Defensive blue-team / DFIR use only. Designed for review of telemetry you
are authorised to inspect.

Dependencies
------------
- stdlib for Zeek log parsing
- scapy (`pip install scapy`) for PCAP mode

Usage
-----
    # Zeek dns.log (TSV)
    python3 dns_exfil_detector.py --zeek /var/log/zeek/current/dns.log

    # PCAP capture
    python3 dns_exfil_detector.py --pcap traffic.pcap

    # JSON Zeek log
    python3 dns_exfil_detector.py --zeek-json zeek-dns.json --top 50
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_LABEL_LEN = 50
DEFAULT_ENTROPY = 4.0
DEFAULT_QPM_PER_DOM = 50  # queries per parent domain (per log slice) to flag


@dataclass
class Suspicion:
    parent_domain: str
    subdomain_sample: str
    qtype: str
    src: str
    label_len: int
    entropy: float
    reasons: list[str]


def shannon(s: str) -> float:
    if not s:
        return 0.0
    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(s)
    h = 0.0
    for c in counts.values():
        p = c / n
        h -= p * math.log2(p)
    return h


def split_domain(qname: str) -> tuple[str, str]:
    """Return (subdomain_label_concat, parent_domain) — naive: parent = last 2 labels."""
    qname = qname.rstrip(".")
    if not qname:
        return "", ""
    parts = qname.split(".")
    if len(parts) <= 2:
        return "", qname
    parent = ".".join(parts[-2:])
    sub = ".".join(parts[:-2])
    return sub, parent


def evaluate(qname: str, qtype: str, src: str, label_len_t: int, ent_t: float) -> Suspicion | None:
    sub, parent = split_domain(qname)
    longest = max((len(p) for p in sub.split(".") if p), default=0)
    h = shannon(sub) if sub else 0.0
    reasons = []
    if longest >= label_len_t:
        reasons.append(f"long_label>={label_len_t}")
    if h >= ent_t:
        reasons.append(f"entropy>={ent_t}")
    if qtype.upper() in {"TXT", "NULL"} and (h >= ent_t - 0.5 or longest >= 20):
        reasons.append(f"unusual_qtype:{qtype}")
    if not reasons:
        return None
    return Suspicion(
        parent_domain=parent,
        subdomain_sample=sub[:120],
        qtype=qtype,
        src=src,
        label_len=longest,
        entropy=round(h, 3),
        reasons=reasons,
    )


# -- Zeek TSV parsing ---------------------------------------------------------
def parse_zeek_tsv(path: Path) -> list[tuple[str, str, str]]:
    """Yield (qname, qtype, src) from Zeek dns.log TSV."""
    rows: list[tuple[str, str, str]] = []
    fields: list[str] = []
    with path.open() as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            if line.startswith("#fields"):
                fields = line.split("\t")[1:]
                continue
            if line.startswith("#"):
                continue
            parts = line.split("\t")
            if not fields or len(parts) < len(fields):
                continue
            row = dict(zip(fields, parts))
            qname = row.get("query", "")
            qtype = row.get("qtype_name", "") or row.get("qtype", "")
            src = row.get("id.orig_h", "")
            if qname:
                rows.append((qname, qtype, src))
    return rows


def parse_zeek_json(path: Path) -> list[tuple[str, str, str]]:
    """Yield (qname, qtype, src) from Zeek streaming JSON dns.log."""
    rows: list[tuple[str, str, str]] = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            qname = obj.get("query", "")
            qtype = obj.get("qtype_name", "") or str(obj.get("qtype", ""))
            src = obj.get("id.orig_h", "") or obj.get("orig_h", "")
            if qname:
                rows.append((qname, qtype, src))
    return rows


def parse_pcap(path: Path) -> list[tuple[str, str, str]]:
    try:
        from scapy.all import rdpcap, DNS, IP, IPv6  # type: ignore
    except ImportError:
        print("[-] scapy required for pcap mode: pip install scapy", file=sys.stderr)
        sys.exit(2)
    qtype_map = {1: "A", 2: "NS", 5: "CNAME", 6: "SOA", 12: "PTR", 15: "MX", 16: "TXT", 28: "AAAA", 33: "SRV", 257: "CAA"}
    rows: list[tuple[str, str, str]] = []
    pkts = rdpcap(str(path))
    for p in pkts:
        if not p.haslayer(DNS):
            continue
        d = p[DNS]
        if d.qd is None or d.qr != 0:  # only queries
            continue
        try:
            qname = d.qd.qname.decode(errors="replace").rstrip(".")
            qtype = qtype_map.get(int(d.qd.qtype), str(d.qd.qtype))
        except Exception:
            continue
        src = ""
        if p.haslayer(IP):
            src = p[IP].src
        elif p.haslayer(IPv6):
            src = p[IPv6].src
        rows.append((qname, qtype, src))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--zeek", type=Path, help="Zeek dns.log (TSV)")
    grp.add_argument("--zeek-json", type=Path, help="Zeek dns.log (streaming JSON)")
    grp.add_argument("--pcap", type=Path, help="PCAP file")
    ap.add_argument("--label-len", type=int, default=DEFAULT_LABEL_LEN)
    ap.add_argument("--entropy", type=float, default=DEFAULT_ENTROPY)
    ap.add_argument("--qpm-threshold", type=int, default=DEFAULT_QPM_PER_DOM, help="queries-per-parent threshold")
    ap.add_argument("--top", type=int, default=20, help="top N parent domains to summarise")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    if args.zeek:
        rows = parse_zeek_tsv(args.zeek)
        src_label = str(args.zeek)
    elif args.zeek_json:
        rows = parse_zeek_json(args.zeek_json)
        src_label = str(args.zeek_json)
    else:
        rows = parse_pcap(args.pcap)
        src_label = str(args.pcap)

    print(f"[+] parsed {len(rows)} DNS queries from {src_label}")

    suspicions: list[Suspicion] = []
    parent_counts: Counter = Counter()
    parent_to_subs: dict[str, set[str]] = defaultdict(set)

    for qname, qtype, src in rows:
        _, parent = split_domain(qname)
        if parent:
            parent_counts[parent] += 1
            parent_to_subs[parent].add(qname)
        s = evaluate(qname, qtype, src, args.label_len, args.entropy)
        if s:
            suspicions.append(s)

    high_volume = [(d, c) for d, c in parent_counts.items() if c >= args.qpm_threshold]
    high_volume.sort(key=lambda x: x[1], reverse=True)

    print(f"\n[+] {len(suspicions)} per-query suspicions")
    for s in suspicions[:50]:
        print(
            f"    {s.parent_domain:<35} qt={s.qtype:<5} ll={s.label_len:>3} ent={s.entropy:>5.2f} "
            f"src={s.src:<15} reasons={','.join(s.reasons)}"
        )
    if len(suspicions) > 50:
        print(f"    ... ({len(suspicions) - 50} more — use --json)")

    print(f"\n[+] high-volume parent domains (>= {args.qpm_threshold} queries):")
    for d, c in high_volume[: args.top]:
        unique_subs = len(parent_to_subs[d])
        print(f"    {d:<40} queries={c:>6} unique_subdomains={unique_subs:>5}")

    if args.json:
        report = {
            "source": src_label,
            "total_queries": len(rows),
            "suspicions": [asdict(s) for s in suspicions],
            "high_volume_parents": [{"domain": d, "queries": c, "unique_subdomains": len(parent_to_subs[d])} for d, c in high_volume],
            "thresholds": {"label_len": args.label_len, "entropy": args.entropy, "qpm": args.qpm_threshold},
        }
        args.json.write_text(json.dumps(report, indent=2))
        print(f"\n[+] full report -> {args.json}")
    return 1 if suspicions or high_volume else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[!] interrupted", file=sys.stderr)
        sys.exit(130)
