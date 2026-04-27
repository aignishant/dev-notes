#!/usr/bin/env python3
"""
wayback_url_extractor.py — Harvest historic URLs for a domain from the
Wayback Machine's CDX API.

Pulls every URL the Wayback Machine has indexed for a domain (and optionally
its subdomains) since a given year. Useful for finding:
  - Deprecated /admin endpoints
  - Old API routes that may still work
  - Backup files exposed historically
  - Parameter names in URLs (great seed for fuzzing)

Purely passive — queries archive.org, not the target.

⚠️ AUTHORIZATION REQUIRED for any active follow-up ⚠️
Querying the Wayback Machine doesn't touch the target. But probing the
URLs you discover is *active* and requires authorization.

Usage:
    python3 wayback_url_extractor.py example.com
    python3 wayback_url_extractor.py example.com --subs --from 2020 -o urls.txt
    python3 wayback_url_extractor.py example.com --filter-extensions js,json,xml
    python3 wayback_url_extractor.py example.com --interesting-only
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from typing import Iterable

import httpx

USER_AGENT = "wayback-url-extractor/1.0 (educational/defensive use only)"
TIMEOUT = httpx.Timeout(120.0, connect=20.0)
CDX_URL = "https://web.archive.org/cdx/search/cdx"

# Substrings that mark a URL as worth a closer look
INTERESTING_PATTERNS = [
    "admin", "login", "signin", "register", "signup", "api", "graphql",
    "swagger", "openapi", "console", "debug", "test", "dev", "staging",
    "internal", "backup", "old", "tmp", "_export", "export", "download",
    "upload", "redirect", "callback", "oauth", "saml", "key", "token",
    "secret", "session", "passwd", "password", "config", "env",
    ".git", ".svn", ".env", ".bak", ".old", "phpinfo", "actuator",
    "wp-admin", "wp-content", "wp-json", "?", "id=", "user=", "uid=",
    "file=", "path=", "url=", "redirect=", "next=", "return=", "callback=",
]

INTERESTING_EXTENSIONS = {
    "json", "xml", "yaml", "yml", "env", "bak", "old", "swp",
    "sql", "log", "txt", "conf", "cfg", "ini", "key", "pem",
    "git", "svn",
}


def fetch_cdx(
    domain: str,
    include_subs: bool,
    from_year: int | None,
    extensions: list[str] | None,
    limit: int | None,
) -> Iterable[str]:
    """Stream URLs from the CDX API. Generator to avoid building a huge list."""
    target = f"*.{domain}/*" if include_subs else f"{domain}/*"
    params: dict[str, str] = {
        "url": target,
        "output": "txt",
        "fl": "original",
        "collapse": "urlkey",
    }
    if from_year:
        params["from"] = f"{from_year}0101"
    if limit:
        params["limit"] = str(limit)
    if extensions:
        # CDX supports filter=urlkey:.*\.ext$ — combine into one regex
        ext_re = "|".join(re.escape(e.lstrip(".").lower()) for e in extensions)
        params["filter"] = f"urlkey:.*\\.({ext_re})($|\\?)"

    qs = urllib.parse.urlencode(params)
    full_url = f"{CDX_URL}?{qs}"

    with httpx.stream("GET", full_url, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}) as r:
        r.raise_for_status()
        for raw_line in r.iter_lines():
            line = raw_line.strip() if isinstance(raw_line, str) else raw_line.decode("utf-8", errors="ignore").strip()
            if line:
                yield line


def is_interesting(url: str) -> bool:
    u = url.lower()
    if any(p in u for p in INTERESTING_PATTERNS):
        return True
    # extension check
    path = urllib.parse.urlsplit(url).path
    if "." in path.rsplit("/", 1)[-1]:
        ext = path.rsplit(".", 1)[-1].lower().split("?", 1)[0]
        if ext in INTERESTING_EXTENSIONS:
            return True
    return False


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("domain", help="Target domain (e.g. example.com)")
    p.add_argument("--subs", action="store_true", help="Include subdomains (*.domain)")
    p.add_argument("--from", dest="from_year", type=int, help="Earliest year to include (e.g. 2020)")
    p.add_argument(
        "--filter-extensions",
        help="Comma-separated list of file extensions to keep (e.g. js,json,bak,env)",
    )
    p.add_argument("--limit", type=int, help="Max records (CDX-side limit)")
    p.add_argument("--interesting-only", action="store_true", help="Only emit URLs that match interesting heuristics")
    p.add_argument("-o", "--output", help="Write URLs to file (one per line)")
    p.add_argument("--json", action="store_true", help="Emit JSON object instead of plain URLs")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress progress messages")
    args = p.parse_args()

    extensions = None
    if args.filter_extensions:
        extensions = [e.strip().lstrip(".") for e in args.filter_extensions.split(",") if e.strip()]

    if not args.quiet:
        print(f"[*] Querying Wayback CDX for {args.domain} (subs={args.subs})...", file=sys.stderr)

    urls: list[str] = []
    seen: set[str] = set()
    interesting: list[str] = []
    try:
        for url in fetch_cdx(args.domain, args.subs, args.from_year, extensions, args.limit):
            if url in seen:
                continue
            seen.add(url)
            keep = url
            if args.interesting_only and not is_interesting(url):
                continue
            urls.append(keep)
            if is_interesting(url):
                interesting.append(url)
    except KeyboardInterrupt:
        print("\n[!] Interrupted, writing partial results.", file=sys.stderr)
    except httpx.HTTPError as e:
        print(f"[-] Wayback CDX error: {e}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(
            f"[+] {len(urls)} unique URLs ({len(interesting)} flagged interesting)",
            file=sys.stderr,
        )

    if args.json:
        payload = json.dumps(
            {"domain": args.domain, "count": len(urls), "interesting": interesting, "urls": urls},
            indent=2,
        )
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(payload)
            if not args.quiet:
                print(f"[+] Wrote {args.output}", file=sys.stderr)
        else:
            print(payload)
    else:
        body = "\n".join(urls)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(body + "\n")
            if not args.quiet:
                print(f"[+] Wrote {args.output}", file=sys.stderr)
        else:
            print(body)

    return 0


if __name__ == "__main__":
    sys.exit(main())
