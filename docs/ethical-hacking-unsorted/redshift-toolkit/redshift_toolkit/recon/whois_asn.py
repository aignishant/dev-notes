#!/usr/bin/env python3
"""
redshift_toolkit.recon.whois_asn — WHOIS / RDAP / BGP-ASN lookup.

Given a domain or IP, returns:
  - Registrar / nameservers / dates (domain)
  - WHOIS-style organization / country (IP)
  - ASN, BGP-announced prefixes (via the public bgpview.io API)
  - Origin AS, AS owner

No third-party libraries required (uses stdlib + http.client).

Usage
-----
  python3 -m redshift_toolkit.recon.whois_asn example.com
  python3 -m redshift_toolkit.recon.whois_asn 8.8.8.8 --json
  python3 -m redshift_toolkit.recon.whois_asn --asn 15169

Author: Redshift Project — Module 09
License: MIT
"""

from __future__ import annotations

import argparse
import http.client
import ipaddress
import json
import re
import socket
import ssl
import sys
import urllib.parse
from dataclasses import dataclass, asdict, field

GREEN = "\033[92m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


def is_ip(s: str) -> bool:
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False


@dataclass
class Result:
    target: str
    kind: str = "unknown"  # domain | ip | asn
    rdap: dict = field(default_factory=dict)
    whois_text: str | None = None
    asn: int | None = None
    asn_owner: str | None = None
    prefixes: list[str] = field(default_factory=list)
    error: str | None = None


# ─── Plain WHOIS over TCP/43 ────────────────────────────────────────────────
WHOIS_SERVERS = {
    "default": "whois.iana.org",
    "com":     "whois.verisign-grs.com",
    "net":     "whois.verisign-grs.com",
    "org":     "whois.publicinterestregistry.org",
    "io":      "whois.nic.io",
    "co":      "whois.nic.co",
    "ai":      "whois.nic.ai",
    "us":      "whois.nic.us",
    "uk":      "whois.nic.uk",
    "de":      "whois.denic.de",
    "fr":      "whois.afnic.fr",
    "in":      "whois.registry.in",
    "jp":      "whois.jprs.jp",
    "ru":      "whois.tcinet.ru",
    "cn":      "whois.cnnic.cn",
}


def whois_query(target: str, server: str | None = None,
                timeout: float = 5.0) -> str:
    if server is None:
        if is_ip(target):
            server = "whois.arin.net"
        else:
            tld = target.rsplit(".", 1)[-1].lower()
            server = WHOIS_SERVERS.get(tld, WHOIS_SERVERS["default"])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((server, 43))
        s.sendall((target + "\r\n").encode())
        chunks = []
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks).decode("latin-1", errors="replace")
    finally:
        s.close()


def whois_followup(text: str) -> str | None:
    """Many WHOIS responses say 'see referral' — grab the next server."""
    m = re.search(r"refer:\s*(\S+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r"whois server:\s*(\S+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def whois_full(target: str, timeout: float = 5.0) -> str:
    text = whois_query(target, timeout=timeout)
    refer = whois_followup(text)
    if refer and refer not in WHOIS_SERVERS.values():
        try:
            text2 = whois_query(target, server=refer, timeout=timeout)
            if text2.strip():
                return text2
        except OSError:
            pass
    return text


# ─── RDAP via rdap.org ──────────────────────────────────────────────────────
def http_get_json(url: str, timeout: float = 6.0) -> dict | None:
    parts = urllib.parse.urlparse(url)
    conn_cls = (http.client.HTTPSConnection if parts.scheme == "https"
                else http.client.HTTPConnection)
    conn = conn_cls(parts.netloc, timeout=timeout)
    try:
        path = parts.path + ("?" + parts.query if parts.query else "")
        conn.request("GET", path or "/",
                     headers={"User-Agent": "redshift-toolkit/1.0",
                              "Accept": "application/json"})
        resp = conn.getresponse()
        body = resp.read()
        if resp.status >= 400:
            return None
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None
    finally:
        conn.close()


def rdap_lookup(target: str) -> dict:
    if is_ip(target):
        return http_get_json(f"https://rdap.org/ip/{target}") or {}
    return http_get_json(f"https://rdap.org/domain/{target}") or {}


# ─── BGP / ASN via bgpview.io ───────────────────────────────────────────────
def bgp_lookup_ip(ip: str) -> tuple[int | None, str | None, list[str]]:
    data = http_get_json(f"https://api.bgpview.io/ip/{ip}") or {}
    if data.get("status") != "ok":
        return None, None, []
    payload = data.get("data", {})
    prefixes = payload.get("prefixes") or []
    asns = []
    if prefixes:
        for p in prefixes:
            asn = p.get("asn", {}).get("asn")
            owner = p.get("asn", {}).get("name")
            if asn:
                asns.append((asn, owner))
    if asns:
        first_asn, first_owner = asns[0]
        return first_asn, first_owner, [p.get("prefix") for p in prefixes
                                        if p.get("prefix")]
    return None, None, []


def bgp_asn_prefixes(asn: int) -> tuple[str | None, list[str]]:
    data = http_get_json(f"https://api.bgpview.io/asn/{asn}/prefixes") or {}
    if data.get("status") != "ok":
        return None, []
    pfx = (data.get("data") or {}).get("ipv4_prefixes", []) + \
          (data.get("data") or {}).get("ipv6_prefixes", [])
    return None, sorted({p.get("prefix") for p in pfx if p.get("prefix")})


def bgp_asn_meta(asn: int) -> str | None:
    data = http_get_json(f"https://api.bgpview.io/asn/{asn}") or {}
    if data.get("status") != "ok":
        return None
    return (data.get("data") or {}).get("name")


# ─── Driver ─────────────────────────────────────────────────────────────────
def lookup(target: str, do_whois: bool = True, do_rdap: bool = True,
           do_bgp: bool = True) -> Result:
    r = Result(target=target)
    if target.lower().startswith("as") and target[2:].isdigit():
        target = target[2:]
    if target.isdigit():
        r.kind = "asn"
        asn = int(target)
        r.asn = asn
        r.asn_owner = bgp_asn_meta(asn)
        _, r.prefixes = bgp_asn_prefixes(asn)
        return r
    r.kind = "ip" if is_ip(target) else "domain"
    if do_whois:
        try:
            r.whois_text = whois_full(target)
        except (OSError, socket.timeout) as e:
            r.error = f"whois: {e}"
    if do_rdap:
        try:
            r.rdap = rdap_lookup(target)
        except Exception as e:
            r.error = (r.error or "") + f"; rdap: {e}"
    if do_bgp and r.kind == "ip":
        try:
            asn, owner, prefixes = bgp_lookup_ip(target)
            r.asn, r.asn_owner, r.prefixes = asn, owner, prefixes
        except Exception as e:
            r.error = (r.error or "") + f"; bgp: {e}"
    return r


def render_text(r: Result, color: bool) -> str:
    out = [paint(f"\n=== {r.target} [{r.kind}] ===", BOLD, color)]
    if r.error:
        out.append(paint(f"errors: {r.error}", YELLOW, color))
    if r.kind == "domain" and r.rdap:
        events = r.rdap.get("events", []) or []
        for e in events:
            out.append(f"  {e.get('eventAction', '?'):20} {e.get('eventDate', '?')}")
        ns_list = []
        for ns in r.rdap.get("nameservers", []) or []:
            name = ns.get("ldhName")
            if name:
                ns_list.append(name)
        if ns_list:
            out.append(f"  nameservers: {', '.join(ns_list)}")
        for ent in r.rdap.get("entities", []) or []:
            roles = ",".join(ent.get("roles", []))
            handle = ent.get("handle", "?")
            out.append(f"  entity[{roles}]: {handle}")
    if r.kind == "ip":
        out.append(f"  ASN:    {r.asn}  ({r.asn_owner or '?'})")
        out.append(f"  prefixes ({len(r.prefixes)}):")
        for p in r.prefixes[:10]:
            out.append(f"    - {p}")
        if len(r.prefixes) > 10:
            out.append(f"    ... and {len(r.prefixes) - 10} more")
    if r.kind == "asn":
        out.append(f"  AS{r.asn}: {r.asn_owner or '?'}")
        out.append(f"  prefixes ({len(r.prefixes)}):")
        for p in r.prefixes[:30]:
            out.append(f"    - {p}")
        if len(r.prefixes) > 30:
            out.append(f"    ... and {len(r.prefixes) - 30} more")
    if r.whois_text:
        out.append(paint("\n  --- WHOIS (first 20 lines) ---", GREY, color))
        for line in r.whois_text.splitlines()[:20]:
            out.append(f"  {line}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="WHOIS / RDAP / BGP-ASN lookup.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("target", nargs="?", help="domain, IP, or AS number")
    g.add_argument("--asn", type=int, help="lookup an ASN's prefixes")
    ap.add_argument("--no-whois", action="store_true")
    ap.add_argument("--no-rdap", action="store_true")
    ap.add_argument("--no-bgp", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()

    target = args.target if args.target else f"AS{args.asn}"
    color = sys.stdout.isatty() and not args.no_color and not args.json

    result = lookup(target, do_whois=not args.no_whois,
                    do_rdap=not args.no_rdap,
                    do_bgp=not args.no_bgp)

    if args.json:
        d = asdict(result)
        # rdap can be huge — keep
        print(json.dumps(d, indent=2, default=str))
    else:
        print(render_text(result, color))
    return 0 if not result.error else 1


if __name__ == "__main__":
    sys.exit(main())
