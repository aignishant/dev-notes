#!/usr/bin/env python3
"""
tech_fingerprint.py — Web technology fingerprinter.

Identifies the technology stack of a web application by combining:
  - HTTP response headers (Server, X-Powered-By, X-AspNet-Version, etc.)
  - Cookie patterns (PHPSESSID, JSESSIONID, ASP.NET_SessionId, ...)
  - HTML body markers (generator meta tags, framework comments)
  - Favicon hash (Shodan-compatible mmh3 of base64-encoded icon)

Pure Python, single file. Read-only — sends 1–3 GET requests per target.

⚠️ AUTHORIZATION REQUIRED ⚠️
While the requests are minimal, run only against systems you own or are
explicitly authorized to enumerate.

Usage:
    python3 tech_fingerprint.py https://example.com
    python3 tech_fingerprint.py -l urls.txt --json -o results.json
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import re
import sys
from dataclasses import dataclass, field, asdict

import httpx

try:
    import mmh3  # for Shodan-compatible favicon hashing
    HAVE_MMH3 = True
except ImportError:
    HAVE_MMH3 = False

USER_AGENT = "Mozilla/5.0 tech-fingerprint/1.0 (defensive testing only)"
TIMEOUT = httpx.Timeout(15.0, connect=10.0)

# Header-based fingerprints. Order matters: first match wins per category.
HEADER_RULES: list[tuple[str, str, str]] = [
    # (header, regex, label)
    ("server", r"^cloudflare", "CDN: Cloudflare"),
    ("server", r"^Apache(/[\d.]+)?", "Server: Apache"),
    ("server", r"^nginx(/[\d.]+)?", "Server: nginx"),
    ("server", r"^Microsoft-IIS", "Server: IIS"),
    ("server", r"openresty", "Server: OpenResty"),
    ("server", r"litespeed", "Server: LiteSpeed"),
    ("x-powered-by", r"^PHP", "Language: PHP"),
    ("x-powered-by", r"^ASP\.NET", "Framework: ASP.NET"),
    ("x-powered-by", r"^Express", "Framework: Express (Node.js)"),
    ("x-powered-by", r"^Next\.js", "Framework: Next.js"),
    ("x-aspnet-version", r".+", "Framework: ASP.NET"),
    ("x-generator", r".+", "Generator (header)"),
    ("x-drupal-cache", r".+", "CMS: Drupal"),
    ("x-amz-cf-id", r".+", "CDN: AWS CloudFront"),
    ("x-served-by", r"cache-", "CDN: Fastly"),
    ("x-akamai-transformed", r".+", "CDN: Akamai"),
    ("via", r"varnish", "Cache: Varnish"),
    ("set-cookie", r"PHPSESSID=", "Language: PHP (cookie)"),
    ("set-cookie", r"JSESSIONID=", "Framework: Java servlet"),
    ("set-cookie", r"ASP\.NET_SessionId=", "Framework: ASP.NET (cookie)"),
    ("set-cookie", r"laravel_session=", "Framework: Laravel (cookie)"),
    ("set-cookie", r"connect\.sid=", "Framework: Express (cookie)"),
    ("set-cookie", r"_wp_session=", "CMS: WordPress (cookie)"),
    ("set-cookie", r"django", "Framework: Django (cookie)"),
]

# Body-based fingerprints
BODY_RULES: list[tuple[str, str]] = [
    (r'<meta name="generator" content="([^"]+)"', "Generator: {match}"),
    (r"wp-content/", "CMS: WordPress"),
    (r"/wp-includes/", "CMS: WordPress"),
    (r"<!-- This is Joomla", "CMS: Joomla"),
    (r"Joomla!", "CMS: Joomla"),
    (r"Drupal\.settings", "CMS: Drupal"),
    (r'name="csrf-token"', "Framework: Rails (csrf-token meta)"),
    (r"_next/static/", "Framework: Next.js"),
    (r"window\.__NUXT__", "Framework: Nuxt.js"),
    (r"ng-version=", "Framework: Angular"),
    (r"data-reactroot", "Framework: React"),
    (r"id=\"__NEXT_DATA__\"", "Framework: Next.js"),
    (r"laravel-socialite", "Framework: Laravel"),
    (r"csrfmiddlewaretoken", "Framework: Django"),
    (r"<input type=\"hidden\" name=\"__VIEWSTATE\"", "Framework: ASP.NET WebForms"),
    (r"Powered by .*phpBB", "App: phpBB"),
    (r"Magento", "CMS: Magento"),
    (r"shopify", "CMS: Shopify"),
    (r"hubspot", "Marketing: HubSpot"),
    (r"google-site-verification", "Verification: Google"),
    (r'<script[^>]*src="[^"]*jquery-([\d.]+)', "Library: jQuery {match}"),
    (r'<script[^>]*src="[^"]*bootstrap-([\d.]+)', "Library: Bootstrap {match}"),
]


@dataclass
class FingerprintResult:
    url: str
    status: int | None = None
    final_url: str | None = None
    server: str | None = None
    findings: set[str] = field(default_factory=set)
    favicon_hash: int | None = None
    error: str | None = None

    def to_jsonable(self) -> dict:
        d = asdict(self)
        d["findings"] = sorted(self.findings)
        return d


def match_headers(headers: httpx.Headers, findings: set[str]) -> None:
    for header, pattern, label in HEADER_RULES:
        for value in headers.get_list(header):
            if re.search(pattern, value, re.I):
                findings.add(label)
                break


def match_body(body: str, findings: set[str]) -> None:
    for pattern, label in BODY_RULES:
        m = re.search(pattern, body, re.I)
        if m:
            value = m.group(1) if m.groups() else ""
            findings.add(label.replace("{match}", value))


async def fetch_favicon_hash(client: httpx.AsyncClient, base_url: str) -> int | None:
    if not HAVE_MMH3:
        return None
    fav_url = base_url.rstrip("/") + "/favicon.ico"
    try:
        r = await client.get(fav_url)
        if r.status_code != 200 or not r.content:
            return None
        encoded = base64.encodebytes(r.content)
        return mmh3.hash(encoded)
    except (httpx.HTTPError, OSError):
        return None


async def fingerprint_one(client: httpx.AsyncClient, url: str, sem: asyncio.Semaphore) -> FingerprintResult:
    res = FingerprintResult(url=url)
    async with sem:
        try:
            r = await client.get(url, headers={"User-Agent": USER_AGENT})
        except httpx.HTTPError as e:
            res.error = f"{type(e).__name__}: {e}"
            return res
        res.status = r.status_code
        res.final_url = str(r.url)
        res.server = r.headers.get("server")
        match_headers(r.headers, res.findings)
        match_body(r.text or "", res.findings)
        # Favicon
        base = f"{r.url.scheme}://{r.url.host}"
        if r.url.port:
            base += f":{r.url.port}"
        res.favicon_hash = await fetch_favicon_hash(client, base)
        return res


async def run(urls: list[str], concurrency: int, verify_tls: bool) -> list[FingerprintResult]:
    async with httpx.AsyncClient(
        timeout=TIMEOUT, follow_redirects=True, verify=verify_tls, http2=True
    ) as client:
        sem = asyncio.Semaphore(concurrency)
        return await asyncio.gather(*(fingerprint_one(client, u, sem) for u in urls))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("url", nargs="?", help="Single URL to fingerprint")
    g.add_argument("-l", "--list", help="File with one URL per line")
    p.add_argument("-c", "--concurrency", type=int, default=10, help="Concurrent requests (default: 10)")
    p.add_argument("-k", "--insecure", action="store_true", help="Skip TLS verification")
    p.add_argument("--json", action="store_true", help="Output JSON")
    p.add_argument("-o", "--output", help="Write JSON to file")
    args = p.parse_args()

    if args.list:
        with open(args.list, encoding="utf-8") as f:
            urls = [u.strip() for u in f if u.strip() and not u.startswith("#")]
    else:
        urls = [args.url]

    urls = [u if "://" in u else f"http://{u}" for u in urls]

    if not HAVE_MMH3:
        print("[!] mmh3 not installed — favicon hashing disabled. (pip install mmh3)", file=sys.stderr)

    try:
        results = asyncio.run(run(urls, args.concurrency, not args.insecure))
    except KeyboardInterrupt:
        print("\n[!] Interrupted.", file=sys.stderr)
        return 130

    if args.json or args.output:
        payload = json.dumps([r.to_jsonable() for r in results], indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(payload)
            print(f"[+] Wrote {args.output}", file=sys.stderr)
        else:
            print(payload)
    else:
        for r in results:
            print(f"\n=== {r.url} ===")
            if r.error:
                print(f"  ERROR: {r.error}")
                continue
            print(f"  Status: {r.status}  →  {r.final_url}")
            if r.server:
                print(f"  Server: {r.server}")
            if r.favicon_hash is not None:
                print(f"  Favicon hash: {r.favicon_hash}")
            for f in sorted(r.findings):
                print(f"  • {f}")
            if not r.findings:
                print("  (no fingerprints matched)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
