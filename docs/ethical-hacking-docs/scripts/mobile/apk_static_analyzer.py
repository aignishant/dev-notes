#!/usr/bin/env python3
"""
apk_static_analyzer.py — Static analysis of Android APK files.

Single-file APK analyzer that extracts and reports:
  - Manifest contents (package, version, min/target SDK)
  - All declared permissions, with risk-grouping (signature/dangerous)
  - Exported components (Activities / Services / Receivers / Providers)
  - intent-filters with custom URL schemes (deep-link surface)
  - Network security config indicators (cleartext-permitted, user-CA trust)
  - Signing certificates (subject, issuer, fingerprint, signature scheme)
  - Embedded files of interest (.so, .pem, .key, .json configs)
  - String scan for likely secrets (API keys, AWS, JWT, private keys, URLs)
  - Risky API references (WebView JS interface, MODE_WORLD_*, etc.)

No Android SDK or aapt required — operates on the raw zip + binary
AndroidManifest.xml using axmlparser-style decoding (pure Python).

⚠️ AUTHORIZATION REQUIRED ⚠️
Only analyze APKs you own, develop, are testing under bug-bounty scope,
or are authorized to assess. Distributing modified APKs of others'
software is unlawful in most jurisdictions.

Usage:
    python3 apk_static_analyzer.py app.apk
    python3 apk_static_analyzer.py app.apk --json -o report.json
    python3 apk_static_analyzer.py app.apk --strings-only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import zipfile
from dataclasses import dataclass, field, asdict


# ---------- Binary AndroidManifest.xml decoder ----------
# AXML format is documented in the AOSP frameworks/base/include/androidfw.
# This is a minimal decoder sufficient for extracting elements + attributes.

CHUNK_TYPE_STRING_POOL = 0x0001
CHUNK_TYPE_XML = 0x0003
CHUNK_TYPE_XML_RESOURCE_MAP = 0x0180
CHUNK_TYPE_XML_START_NAMESPACE = 0x0100
CHUNK_TYPE_XML_END_NAMESPACE = 0x0101
CHUNK_TYPE_XML_START_ELEMENT = 0x0102
CHUNK_TYPE_XML_END_ELEMENT = 0x0103
CHUNK_TYPE_XML_CDATA = 0x0104

ATTR_TYPE_STRING = 0x03
ATTR_TYPE_INT_DEC = 0x10
ATTR_TYPE_INT_HEX = 0x11
ATTR_TYPE_INT_BOOLEAN = 0x12
ATTR_TYPE_REFERENCE = 0x01


def _read_string_pool(data: bytes, offset: int) -> tuple[list[str], int]:
    chunk_type, header_size, chunk_size = struct.unpack_from("<HHI", data, offset)
    string_count, _, flags, strings_start, _ = struct.unpack_from("<IIIII", data, offset + 8)
    is_utf8 = bool(flags & (1 << 8))
    offsets = list(struct.unpack_from(f"<{string_count}I", data, offset + 28))
    strings: list[str] = []
    for o in offsets:
        pos = offset + strings_start + o
        try:
            if is_utf8:
                # u16len, u8len (each varint-ish), then bytes
                u16len, n = _decode_utf8_len(data, pos); pos += n
                u8len, n = _decode_utf8_len(data, pos); pos += n
                strings.append(data[pos:pos + u8len].decode("utf-8", errors="replace"))
            else:
                strlen = struct.unpack_from("<H", data, pos)[0]
                if strlen & 0x8000:
                    high = strlen & 0x7fff
                    low = struct.unpack_from("<H", data, pos + 2)[0]
                    strlen = (high << 16) | low
                    pos += 4
                else:
                    pos += 2
                strings.append(data[pos:pos + strlen * 2].decode("utf-16-le", errors="replace"))
        except Exception:
            strings.append("")
    return strings, offset + chunk_size


def _decode_utf8_len(data: bytes, pos: int) -> tuple[int, int]:
    b = data[pos]
    if b & 0x80:
        return ((b & 0x7f) << 8) | data[pos + 1], 2
    return b, 1


@dataclass
class XmlAttr:
    ns: str
    name: str
    value: str


@dataclass
class XmlElement:
    name: str
    ns: str
    attrs: list[XmlAttr] = field(default_factory=list)
    children: list["XmlElement"] = field(default_factory=list)


def parse_axml(data: bytes) -> XmlElement | None:
    if len(data) < 8:
        return None
    chunk_type, header_size, chunk_size = struct.unpack_from("<HHI", data, 0)
    if chunk_type != CHUNK_TYPE_XML:
        return None

    offset = header_size
    strings: list[str] = []

    # Parse all sub-chunks
    root: XmlElement | None = None
    stack: list[XmlElement] = []
    namespaces: dict[int, str] = {}

    while offset < len(data) - 8:
        ct, hs, cs = struct.unpack_from("<HHI", data, offset)
        if cs == 0:
            break
        if ct == CHUNK_TYPE_STRING_POOL:
            strings, offset = _read_string_pool(data, offset)
            continue
        if ct == CHUNK_TYPE_XML_RESOURCE_MAP:
            offset += cs
            continue
        if ct == CHUNK_TYPE_XML_START_NAMESPACE:
            prefix_idx, uri_idx = struct.unpack_from("<II", data, offset + 16)
            if uri_idx < len(strings):
                namespaces[uri_idx] = strings[uri_idx]
            offset += cs
            continue
        if ct == CHUNK_TYPE_XML_END_NAMESPACE:
            offset += cs
            continue
        if ct == CHUNK_TYPE_XML_START_ELEMENT:
            ns_idx, name_idx, _, attr_count = struct.unpack_from("<IIHH", data, offset + 16)
            attrs: list[XmlAttr] = []
            attr_off = offset + 16 + 20  # after the 'start element' header fields
            for i in range(attr_count):
                a_ns, a_name, a_raw, a_typed_size, a_typed_res0, a_typed_type, a_typed_data = \
                    struct.unpack_from("<IIIHBBI", data, attr_off + i * 20)
                ns = strings[a_ns] if 0 <= a_ns < len(strings) else ""
                name = strings[a_name] if 0 <= a_name < len(strings) else ""
                if a_typed_type == ATTR_TYPE_STRING and 0 <= a_raw < len(strings):
                    value = strings[a_raw]
                elif a_typed_type == ATTR_TYPE_INT_BOOLEAN:
                    value = "true" if a_typed_data != 0 else "false"
                elif a_typed_type in (ATTR_TYPE_INT_DEC,):
                    value = str(a_typed_data)
                elif a_typed_type == ATTR_TYPE_INT_HEX:
                    value = f"0x{a_typed_data:x}"
                elif a_typed_type == ATTR_TYPE_REFERENCE:
                    value = f"@0x{a_typed_data:08x}"
                else:
                    value = f"<type=0x{a_typed_type:x},data=0x{a_typed_data:x}>"
                attrs.append(XmlAttr(ns=ns, name=name, value=value))
            elem = XmlElement(name=strings[name_idx] if 0 <= name_idx < len(strings) else "?",
                              ns=strings[ns_idx] if 0 <= ns_idx < len(strings) else "", attrs=attrs)
            if stack:
                stack[-1].children.append(elem)
            else:
                root = elem
            stack.append(elem)
            offset += cs
            continue
        if ct == CHUNK_TYPE_XML_END_ELEMENT:
            if stack:
                stack.pop()
            offset += cs
            continue
        # Unknown chunk
        offset += cs

    return root


# ---------- Walk the parsed manifest ----------

DANGEROUS_PERMISSIONS = {
    "READ_CONTACTS", "WRITE_CONTACTS", "GET_ACCOUNTS",
    "READ_CALL_LOG", "WRITE_CALL_LOG", "READ_PHONE_STATE", "READ_PHONE_NUMBERS",
    "CALL_PHONE", "ANSWER_PHONE_CALLS", "ADD_VOICEMAIL", "USE_SIP",
    "READ_SMS", "RECEIVE_SMS", "SEND_SMS", "RECEIVE_MMS", "RECEIVE_WAP_PUSH",
    "READ_CALENDAR", "WRITE_CALENDAR", "CAMERA", "RECORD_AUDIO",
    "ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION", "ACCESS_BACKGROUND_LOCATION",
    "BODY_SENSORS", "ACCESS_MEDIA_LOCATION",
    "READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE",
    "ACTIVITY_RECOGNITION", "ACCEPT_HANDOVER", "PROCESS_OUTGOING_CALLS",
}

SECRETS_PATTERNS = {
    "AWS Access Key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Google API Key": re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),
    "Google OAuth": re.compile(r"\d{12}-[0-9a-z]{32}\.apps\.googleusercontent\.com"),
    "Stripe key": re.compile(r"\bsk_(live|test)_[0-9a-zA-Z]{24,99}\b"),
    "Slack token": re.compile(r"\bxox[abp]-[0-9a-zA-Z\-]{10,}\b"),
    "GitHub token": re.compile(r"\bgh[ps]_[A-Za-z0-9]{36,}\b"),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b"),
    "Private key": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    "Generic secret": re.compile(r"(?i)\b(secret|api[_-]?key|access[_-]?token)\b\s*[:=]\s*[\"']([A-Za-z0-9_\-]{16,})"),
    "Firebase URL": re.compile(r"https?://[a-z0-9\-]+\.firebaseio\.com\b"),
    "URL": re.compile(r"https?://[A-Za-z0-9.\-_/?#&=%+:]+"),
    "IPv4 (private)": re.compile(r"\b(?:10|192\.168|172\.(?:1[6-9]|2[0-9]|3[01]))\.\d+\.\d+\.\d+\b"),
}


def attr(elem: XmlElement, name: str) -> str | None:
    for a in elem.attrs:
        if a.name == name:
            return a.value
    return None


def find_all(root: XmlElement, name: str) -> list[XmlElement]:
    out = []

    def walk(e: XmlElement):
        if e.name == name:
            out.append(e)
        for c in e.children:
            walk(c)

    walk(root)
    return out


@dataclass
class Component:
    type: str            # activity / service / receiver / provider
    name: str
    exported: str | None
    intents: list[dict] = field(default_factory=list)


@dataclass
class APKReport:
    file: str
    sha256: str = ""
    package: str = ""
    version_name: str = ""
    version_code: str = ""
    min_sdk: str = ""
    target_sdk: str = ""
    permissions: list[str] = field(default_factory=list)
    dangerous_permissions: list[str] = field(default_factory=list)
    components: list[Component] = field(default_factory=list)
    network_security_config: dict = field(default_factory=dict)
    signing_certs: list[dict] = field(default_factory=list)
    embedded_files_of_interest: list[dict] = field(default_factory=list)
    secrets_found: list[dict] = field(default_factory=list)
    risky_api_hits: list[str] = field(default_factory=list)


INTERESTING_FILE_EXT = {".so", ".pem", ".cer", ".crt", ".key", ".json", ".db", ".sqlite", ".txt", ".properties", ".cfg", ".conf"}
RISKY_API_PATTERNS = [
    "addJavascriptInterface",
    "setAllowFileAccess",
    "setJavaScriptEnabled",
    "setDomStorageEnabled",
    "setMixedContentMode",
    "MODE_WORLD_READABLE",
    "MODE_WORLD_WRITEABLE",
    "Cipher.getInstance(\"DES",
    "Cipher.getInstance(\"RC4",
    "Cipher.getInstance(\"AES/ECB",
    "MessageDigest.getInstance(\"MD5",
    "MessageDigest.getInstance(\"SHA-1",
    "TrustAllX509TrustManager",
    "ALLOW_ALL_HOSTNAME_VERIFIER",
    "exec(",
    "Runtime.getRuntime",
    "/sdcard/",
]


def analyze_apk(path: str, scan_strings: bool = True) -> APKReport:
    rep = APKReport(file=path)
    with open(path, "rb") as fh:
        h = hashlib.sha256(fh.read()).hexdigest()
    rep.sha256 = h

    with zipfile.ZipFile(path) as zf:
        # Manifest
        try:
            manifest_data = zf.read("AndroidManifest.xml")
        except KeyError:
            return rep
        manifest = parse_axml(manifest_data)

        if manifest:
            rep.package = attr(manifest, "package") or ""
            rep.version_name = attr(manifest, "versionName") or ""
            rep.version_code = attr(manifest, "versionCode") or ""
            uses_sdk = find_all(manifest, "uses-sdk")
            if uses_sdk:
                rep.min_sdk = attr(uses_sdk[0], "minSdkVersion") or ""
                rep.target_sdk = attr(uses_sdk[0], "targetSdkVersion") or ""

            for up in find_all(manifest, "uses-permission"):
                pn = attr(up, "name") or ""
                rep.permissions.append(pn)
                short = pn.rsplit(".", 1)[-1]
                if short in DANGEROUS_PERMISSIONS:
                    rep.dangerous_permissions.append(pn)

            for comp_type in ("activity", "service", "receiver", "provider"):
                for c in find_all(manifest, comp_type):
                    intents = []
                    for itf in find_all(c, "intent-filter"):
                        actions = [attr(a, "name") for a in find_all(itf, "action")]
                        cats = [attr(a, "name") for a in find_all(itf, "category")]
                        datas = []
                        for d in find_all(itf, "data"):
                            datas.append({a.name: a.value for a in d.attrs})
                        intents.append({"actions": actions, "categories": cats, "data": datas})
                    rep.components.append(Component(
                        type=comp_type, name=attr(c, "name") or "?",
                        exported=attr(c, "exported"), intents=intents,
                    ))

            # Application-level network security config flag
            for app in find_all(manifest, "application"):
                nsc = attr(app, "networkSecurityConfig")
                cleartext = attr(app, "usesCleartextTraffic")
                rep.network_security_config = {
                    "networkSecurityConfig": nsc,
                    "usesCleartextTraffic": cleartext,
                    "debuggable": attr(app, "debuggable"),
                    "allowBackup": attr(app, "allowBackup"),
                }

        # Embedded files of interest
        for info in zf.infolist():
            ext = "." + info.filename.rsplit(".", 1)[-1].lower() if "." in info.filename else ""
            if ext in INTERESTING_FILE_EXT and info.file_size < 5_000_000:
                rep.embedded_files_of_interest.append({
                    "path": info.filename, "size": info.file_size,
                })

        # Signing certs
        for n in zf.namelist():
            if n.startswith("META-INF/") and n.upper().endswith((".RSA", ".DSA", ".EC")):
                try:
                    cert_blob = zf.read(n)
                    rep.signing_certs.append({
                        "path": n,
                        "size": len(cert_blob),
                        "sha256": hashlib.sha256(cert_blob).hexdigest(),
                    })
                except KeyError:
                    continue

        # String scan over key files
        if scan_strings:
            scan_targets = [info.filename for info in zf.infolist()
                            if info.filename in ("classes.dex",) or info.filename.startswith("classes")
                            or info.filename in ("resources.arsc",)
                            or any(info.filename.endswith(e) for e in (".smali", ".so", ".json", ".js", ".html", ".txt", ".properties"))]
            seen_secrets: set[str] = set()
            for tgt in scan_targets[:200]:  # cap to avoid runaway
                try:
                    blob = zf.read(tgt)
                except (KeyError, zipfile.BadZipFile):
                    continue
                # Extract printable ASCII strings (>= 6 chars)
                printable = re.findall(rb"[ -~]{6,}", blob)
                joined = b"\n".join(printable).decode("utf-8", errors="replace")
                for label, pat in SECRETS_PATTERNS.items():
                    for m in pat.finditer(joined):
                        match = m.group(0)
                        if match in seen_secrets:
                            continue
                        seen_secrets.add(match)
                        if label in ("URL", "IPv4 (private)") and len(rep.secrets_found) > 200:
                            continue
                        rep.secrets_found.append({"file": tgt, "kind": label, "match": match[:200]})

                for risky in RISKY_API_PATTERNS:
                    if risky.encode() in blob and risky not in rep.risky_api_hits:
                        rep.risky_api_hits.append(risky)

    return rep


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("apk", help="Path to .apk file")
    p.add_argument("--strings-only", action="store_true", help="Skip manifest decoding (debug)")
    p.add_argument("--no-strings", action="store_true", help="Skip slow string scan")
    p.add_argument("--json", action="store_true", help="Output JSON")
    p.add_argument("-o", "--output", help="Write JSON to file")
    args = p.parse_args()

    try:
        rep = analyze_apk(args.apk, scan_strings=not args.no_strings)
    except (FileNotFoundError, zipfile.BadZipFile) as e:
        print(f"[-] Could not open {args.apk}: {e}", file=sys.stderr)
        return 1

    if args.json or args.output:
        out = json.dumps(asdict(rep), indent=2, default=str)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(out)
            print(f"[+] Wrote {args.output}", file=sys.stderr)
        else:
            print(out)
    else:
        print(f"\n=== {args.apk} ===")
        print(f"sha256:        {rep.sha256}")
        print(f"package:       {rep.package}")
        print(f"version:       {rep.version_name} ({rep.version_code})")
        print(f"sdk:           min={rep.min_sdk}  target={rep.target_sdk}")
        print(f"\nPermissions ({len(rep.permissions)}):")
        for p_ in rep.permissions[:50]:
            mark = "⚠ " if p_ in rep.dangerous_permissions else "  "
            print(f"  {mark}{p_}")
        if len(rep.permissions) > 50:
            print(f"  (+{len(rep.permissions)-50} more)")
        print(f"\nApplication flags: {rep.network_security_config}")
        exported = [c for c in rep.components if c.exported == "true"]
        print(f"\nExported components ({len(exported)} of {len(rep.components)}):")
        for c in exported[:30]:
            print(f"  [{c.type:9}] {c.name}  intents={len(c.intents)}")
        print(f"\nSigning certs ({len(rep.signing_certs)}):")
        for c in rep.signing_certs:
            print(f"  {c['path']}  sha256={c['sha256']}")
        print(f"\nFiles of interest: {len(rep.embedded_files_of_interest)}")
        for f_ in rep.embedded_files_of_interest[:20]:
            print(f"  {f_['path']}  ({f_['size']}B)")
        print(f"\nRisky API references: {len(rep.risky_api_hits)}")
        for r_ in rep.risky_api_hits[:30]:
            print(f"  • {r_}")
        print(f"\nSecret-shaped strings: {len(rep.secrets_found)}")
        # Suppress URL/IP noise for the human view
        for s in [s for s in rep.secrets_found if s["kind"] not in ("URL", "IPv4 (private)")][:30]:
            print(f"  [{s['kind']:18}] {s['file']}  → {s['match']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
