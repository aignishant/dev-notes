#!/usr/bin/env python3
"""
redshift_toolkit.recon.subdomain_takeover_check — orphaned-CNAME
subdomain takeover candidate detector.

Workflow per subdomain
----------------------
1. Resolve CNAME (and A as fallback).
2. Match CNAME target against a fingerprint database of takeover-prone
   services (S3, Azure Blob, GitHub Pages, Heroku, Fastly, Tumblr, etc.).
3. If the CNAME points at a fingerprinted service:
   a. Fetch the resource over HTTP/HTTPS.
   b. Match response body against the service's "no such resource"
      signature.
   c. If both match → flag as a takeover candidate.

False-positive guard: services with valid resources don't match, so a
plain S3-hosted site that exists won't be flagged.

Usage
-----
  python3 -m redshift_toolkit.recon.subdomain_takeover_check \\
      --names a.example.com,b.example.com
  python3 -m redshift_toolkit.recon.subdomain_takeover_check \\
      --names-file subs.txt --json
  python3 -m redshift_toolkit.recon.subdomain_takeover_check \\
      --names-file subs.txt --concurrency 30 --timeout 6

Author: Redshift Project — Module 11
License: MIT — Authorized testing only.
"""

from __future__ import annotations

import argparse
import asyncio
import http.client
import json
import os
import socket
import ssl
import struct
import sys
from dataclasses import dataclass, asdict, field

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


# ─── Fingerprint DB ─────────────────────────────────────────────────────────
@dataclass
class Fingerprint:
    name: str
    cname_patterns: list[str]
    body_signatures: list[str]
    status_hint: int | None = None
    severity: str = "high"


FINGERPRINTS: list[Fingerprint] = [
    Fingerprint("AWS S3",
                [".s3.amazonaws.com", ".s3-website", ".s3-website-",
                 ".s3.dualstack.", ".s3-accelerate."],
                ["NoSuchBucket", "The specified bucket does not exist"],
                status_hint=404),
    Fingerprint("Azure Blob",
                [".blob.core.windows.net"],
                ["The specified blob does not exist",
                 "BlobNotFound"]),
    Fingerprint("Azure Cloudapp",
                [".cloudapp.net", ".azurewebsites.net",
                 ".trafficmanager.net"],
                ["404 Web Site not found"]),
    Fingerprint("GitHub Pages",
                [".github.io"],
                ["There isn't a GitHub Pages site here.",
                 "For root URLs (like http://example.com/) you must provide an index.html file"]),
    Fingerprint("Heroku",
                [".herokuapp.com", ".herokudns.com"],
                ["No such app", "no-such-app", "There's nothing here, yet."]),
    Fingerprint("Fastly",
                [".fastly.net"],
                ["Fastly error: unknown domain"]),
    Fingerprint("Shopify",
                [".myshopify.com"],
                ["Sorry, this shop is currently unavailable.",
                 "Only one step left!"]),
    Fingerprint("Tumblr",
                [".tumblr.com"],
                ["Whatever you were looking for doesn't currently exist at this address.",
                 "There's nothing here."]),
    Fingerprint("Surge.sh",
                [".surge.sh"],
                ["project not found"]),
    Fingerprint("Tilda",
                [".tilda.ws"],
                ["Please renew your subscription"]),
    Fingerprint("Webflow",
                [".webflow.io", ".proxy.webflow.com"],
                ["The page you are looking for doesn't exist or has been moved."]),
    Fingerprint("Bitbucket",
                [".bitbucket.io"],
                ["Repository not found"]),
    Fingerprint("Cargo",
                [".cargocollective.com"],
                ["404 Not Found", "If you're moving your domain away from Cargo"]),
    Fingerprint("Pantheon",
                [".pantheonsite.io"],
                ["The gods are wise", "404 error unknown site"]),
    Fingerprint("Helpjuice",
                [".helpjuice.com"],
                ["We could not find what you're looking for."]),
    Fingerprint("HelpScout",
                [".helpscoutdocs.com"],
                ["No settings were found for this company"]),
    Fingerprint("Ghost",
                [".ghost.io"],
                ["The thing you were looking for is no longer here, or never was"]),
    Fingerprint("Zendesk",
                [".zendesk.com"],
                ["Help Center Closed"]),
    Fingerprint("Strikingly",
                [".strikingly.com", ".s.strikinglydns.com"],
                ["page not found"]),
]


# ─── DNS lookup (uses resolver-provided functions if available) ─────────────
def encode_name(name: str) -> bytes:
    out = bytearray()
    for label in name.rstrip(".").split("."):
        if label:
            b = label.encode("ascii")
            out.append(len(b))
            out.extend(b)
    out.append(0)
    return bytes(out)


def build_query(name: str, qtype: int) -> bytes:
    txid = int.from_bytes(os.urandom(2), "big")
    flags = 0x0100
    return (struct.pack(">HHHHHH", txid, flags, 1, 0, 0, 0)
            + encode_name(name) + struct.pack(">HH", qtype, 1))


def read_name(data: bytes, off: int) -> tuple[str, int]:
    labels: list[str] = []
    saw_ptr = False
    next_off = off
    safety = 0
    while True:
        if safety > 64 or off >= len(data):
            return ".".join(labels), next_off
        safety += 1
        ln = data[off]
        if ln == 0:
            off += 1
            if not saw_ptr:
                next_off = off
            return ".".join(labels), next_off
        if (ln & 0xC0) == 0xC0:
            ptr = ((ln & 0x3F) << 8) | data[off + 1]
            if not saw_ptr:
                next_off = off + 2
                saw_ptr = True
            off = ptr
            continue
        off += 1
        labels.append(data[off:off + ln].decode("ascii", errors="replace"))
        off += ln


def parse_resp(data: bytes) -> dict:
    out = {"answers": [], "rcode": -1}
    if len(data) < 12:
        return out
    txid, flags, qd, an, ns, ar = struct.unpack(">HHHHHH", data[:12])
    out["rcode"] = flags & 0x0F
    off = 12
    for _ in range(qd):
        _, off = read_name(data, off)
        off += 4
    for _ in range(an):
        _, off = read_name(data, off)
        if off + 10 > len(data):
            return out
        rtype, _, _, rdlen = struct.unpack(">HHIH", data[off:off + 10])
        off += 10
        rdata = data[off:off + rdlen]
        off += rdlen
        if rtype == 5:
            try:
                cn_off = data.index(rdata, 12)
                cn, _ = read_name(data, cn_off)
                out["answers"].append({"type": "cname",
                                        "value": cn.rstrip(".")})
            except ValueError:
                pass
        elif rtype == 1 and len(rdata) == 4:
            out["answers"].append({"type": "a",
                                    "value": ".".join(str(b) for b in rdata)})
    return out


def query_dns(name: str, resolver: str, timeout: float) -> dict:
    payload = build_query(name, 5)  # CNAME first
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(timeout)
        s.sendto(payload, (resolver, 53))
        data, _ = s.recvfrom(4096)
    except OSError:
        return {"answers": [], "rcode": -1}
    finally:
        s.close()
    resp = parse_resp(data)
    # If no CNAME, also try A
    if not resp["answers"]:
        payload = build_query(name, 1)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.settimeout(timeout)
            s.sendto(payload, (resolver, 53))
            data, _ = s.recvfrom(4096)
            resp = parse_resp(data)
        except OSError:
            return {"answers": [], "rcode": -1}
        finally:
            s.close()
    return resp


# ─── HTTP fetch ─────────────────────────────────────────────────────────────
def http_fetch(host: str, timeout: float = 6.0) -> tuple[int, str]:
    """Try HTTPS first, then HTTP. Return (status, body[:64K])."""
    for scheme in ("https", "http"):
        try:
            if scheme == "https":
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                conn = http.client.HTTPSConnection(host, timeout=timeout,
                                                   context=ctx)
            else:
                conn = http.client.HTTPConnection(host, timeout=timeout)
            conn.request("GET", "/",
                         headers={"User-Agent": "redshift-takeover-check/1.0",
                                  "Host": host})
            r = conn.getresponse()
            body = r.read(64 * 1024)
            conn.close()
            return r.status, body.decode("utf-8", "replace")
        except Exception:
            continue
    return 0, ""


# ─── Driver ─────────────────────────────────────────────────────────────────
@dataclass
class Result:
    name: str
    cname: str | None = None
    a: list[str] = field(default_factory=list)
    matched_service: str | None = None
    body_signature_hit: bool = False
    severity: str = "info"
    status_code: int | None = None
    note: str = ""


@dataclass
class Report:
    queried: int = 0
    results: list[Result] = field(default_factory=list)
    candidates: list[Result] = field(default_factory=list)


def check_one(name: str, resolver: str, timeout: float,
              do_http: bool = True) -> Result:
    res = Result(name=name)
    resp = query_dns(name, resolver, timeout)
    cname = next((a["value"] for a in resp["answers"]
                  if a["type"] == "cname"), None)
    a_records = [a["value"] for a in resp["answers"] if a["type"] == "a"]
    res.cname = cname
    res.a = a_records

    if not cname:
        res.note = "no CNAME (only A records or NXDOMAIN)"
        return res

    cname_low = cname.lower()
    matched = None
    for fp in FINGERPRINTS:
        for pat in fp.cname_patterns:
            if pat in cname_low:
                matched = fp
                break
        if matched:
            break
    if not matched:
        res.note = f"CNAME → {cname} (not on fingerprint list)"
        return res

    res.matched_service = matched.name
    res.severity = matched.severity
    if not do_http:
        res.note = "fingerprint match (HTTP check skipped)"
        return res

    status, body = http_fetch(name, timeout=timeout)
    res.status_code = status
    body_low = body.lower()
    body_hit = any(sig.lower() in body_low for sig in matched.body_signatures)
    res.body_signature_hit = body_hit

    if body_hit:
        res.note = f"TAKEOVER CANDIDATE: matched {matched.name} signature"
    else:
        res.note = (f"CNAME points at {matched.name} but no orphan signature "
                    f"in body (status {status})")
    return res


def render_text(rep: Report, color: bool) -> str:
    out = [paint(f"\n=== Subdomain takeover scan ===", BOLD, color),
           f"  queried: {rep.queried}"]
    cands = [r for r in rep.results if r.body_signature_hit]
    fingerprinted = [r for r in rep.results
                     if r.matched_service and not r.body_signature_hit]
    out.append(paint(f"  takeover candidates: {len(cands)}",
                     RED if cands else GREEN, color))
    out.append(f"  fingerprinted (no body match): {len(fingerprinted)}")

    for r in cands:
        out.append(paint(
            f"\n  [TAKEOVER]  {r.name}  →  CNAME {r.cname}", RED, color))
        out.append(f"    service: {r.matched_service}  http_status={r.status_code}")
        out.append(f"    note: {r.note}")
    for r in fingerprinted[:10]:
        out.append(paint(
            f"\n  [fingerprint]  {r.name}  →  CNAME {r.cname}", YELLOW, color))
        out.append(f"    service: {r.matched_service}  http_status={r.status_code}")
        out.append(paint(f"    {r.note}", GREY, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Subdomain takeover candidate detector.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--names", help="comma-separated subdomains")
    g.add_argument("--names-file", help="file with one subdomain per line")
    ap.add_argument("--resolver", default="1.1.1.1")
    ap.add_argument("--timeout", type=float, default=4.0)
    ap.add_argument("--concurrency", type=int, default=20)
    ap.add_argument("--no-http", action="store_true",
                    help="skip HTTP fetch (only do CNAME fingerprint)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    if args.names:
        names = [n.strip() for n in args.names.split(",") if n.strip()]
    else:
        with open(args.names_file) as f:
            names = [n.strip() for n in f
                     if n.strip() and not n.startswith("#")]

    rep = Report(queried=len(names))

    async def worker(n: str) -> Result:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, check_one, n, args.resolver, args.timeout,
            not args.no_http,
        )

    async def runner():
        sem = asyncio.Semaphore(args.concurrency)

        async def guarded(n: str) -> Result:
            async with sem:
                return await worker(n)
        return await asyncio.gather(*[guarded(n) for n in names])

    rep.results = asyncio.run(runner())
    rep.candidates = [r for r in rep.results if r.body_signature_hit]

    if args.json:
        print(json.dumps({
            "queried": rep.queried,
            "results": [asdict(r) for r in rep.results],
            "candidates": [asdict(r) for r in rep.candidates],
        }, indent=2))
    else:
        print(render_text(rep, color))
    return 0 if not rep.candidates else 1


if __name__ == "__main__":
    sys.exit(main())
