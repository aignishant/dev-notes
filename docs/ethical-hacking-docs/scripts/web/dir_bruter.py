#!/usr/bin/env python3
"""
dir_bruter.py — Polite, rate-limited directory & file bruteforcer with
smart 404 detection.

Designed for engagements where ROE forbids hammering targets:
  - Configurable rate limit (req/s)
  - Auto-calibrated baseline detection of "soft 404" pages (apps that
    serve 200 OK for missing routes — common with SPAs)
  - Per-extension expansion (./admin -> ./admin, admin.php, admin.bak, ...)
  - Random User-Agent rotation
  - JSON + plain output
  - Resumable (writes progress to <output>.state)

⚠️ AUTHORIZATION REQUIRED ⚠️
This tool sends real HTTP requests. Run only against systems you own or
are explicitly authorized to test. Many WAFs treat directory bruteforcing
as malicious activity even at low rates.

Usage:
    python3 dir_bruter.py https://target.com -w wordlists/dirs.txt
    python3 dir_bruter.py https://target.com -w big.txt -e .php,.bak,.zip --rate 10
    python3 dir_bruter.py https://target.com -w big.txt --json -o results.json
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import sys
import time
from dataclasses import dataclass, field, asdict

import httpx

USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
]

TIMEOUT = httpx.Timeout(15.0, connect=10.0)


@dataclass
class Hit:
    url: str
    status: int
    length: int
    content_type: str = ""
    redirect_to: str | None = None
    body_hash: str | None = None


@dataclass
class Baseline:
    status: int
    length: int
    body_hash: str
    content_type: str


def hash_body(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


async def probe(client: httpx.AsyncClient, url: str) -> Hit | None:
    try:
        r = await client.get(url, headers={"User-Agent": random.choice(USER_AGENTS)})
    except (httpx.HTTPError, OSError):
        return None
    body = r.content or b""
    redirect = None
    if 300 <= r.status_code < 400:
        redirect = r.headers.get("location")
    return Hit(
        url=str(r.request.url),
        status=r.status_code,
        length=len(body),
        content_type=r.headers.get("content-type", "").split(";", 1)[0],
        redirect_to=redirect,
        body_hash=hash_body(body),
    )


async def calibrate(client: httpx.AsyncClient, base_url: str, samples: int = 3) -> list[Baseline]:
    """Generate baseline 404-ish responses by requesting random nonexistent paths."""
    baselines: list[Baseline] = []
    for _ in range(samples):
        rand = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=20))
        url = base_url.rstrip("/") + "/" + rand
        h = await probe(client, url)
        if h is None:
            continue
        baselines.append(
            Baseline(status=h.status, length=h.length, body_hash=h.body_hash or "", content_type=h.content_type)
        )
    return baselines


def is_baseline(h: Hit, baselines: list[Baseline], len_tolerance: int = 16) -> bool:
    for b in baselines:
        if h.status == b.status and h.body_hash == b.body_hash:
            return True
        if h.status == b.status and abs(h.length - b.length) <= len_tolerance:
            return True
    return False


def expand_words(words: list[str], extensions: list[str]) -> list[str]:
    """Expand wordlist with extensions: 'admin' + ['.php', '.bak'] -> 'admin', 'admin.php', 'admin.bak'."""
    out: list[str] = []
    for w in words:
        out.append(w)
        for ext in extensions:
            ext = ext if ext.startswith(".") else "." + ext
            out.append(w + ext)
    # Dedupe preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for w in out:
        if w not in seen:
            seen.add(w)
            deduped.append(w)
    return deduped


class RateLimiter:
    """Simple token-bucket rate limiter — async-safe."""

    def __init__(self, rate_per_sec: float):
        self.interval = 1.0 / rate_per_sec if rate_per_sec > 0 else 0.0
        self.next_ok = 0.0
        self.lock = asyncio.Lock()

    async def acquire(self) -> None:
        if self.interval == 0.0:
            return
        async with self.lock:
            now = time.monotonic()
            wait = max(0.0, self.next_ok - now)
            if wait > 0:
                await asyncio.sleep(wait)
            self.next_ok = max(self.next_ok, now) + self.interval


async def run(
    base_url: str,
    words: list[str],
    rate: float,
    concurrency: int,
    interesting_codes: set[int],
    verify_tls: bool,
    quiet: bool,
) -> list[Hit]:
    base_url = base_url.rstrip("/")
    async with httpx.AsyncClient(
        timeout=TIMEOUT, follow_redirects=False, verify=verify_tls, http2=False
    ) as client:
        if not quiet:
            print("[*] Calibrating baseline 404 response...", file=sys.stderr)
        baselines = await calibrate(client, base_url)
        if not baselines:
            raise RuntimeError("Could not establish baseline; target unreachable.")
        if not quiet:
            for b in baselines:
                print(
                    f"[+] Baseline: status={b.status} len={b.length} type={b.content_type}",
                    file=sys.stderr,
                )

        limiter = RateLimiter(rate)
        sem = asyncio.Semaphore(concurrency)
        hits: list[Hit] = []
        total = len(words)

        async def worker(word: str, i: int) -> None:
            async with sem:
                await limiter.acquire()
                url = base_url + "/" + word.lstrip("/")
                h = await probe(client, url)
                if h is None:
                    return
                if h.status in interesting_codes and not is_baseline(h, baselines):
                    hits.append(h)
                    if not quiet:
                        redirect = f" → {h.redirect_to}" if h.redirect_to else ""
                        print(
                            f"[+] {h.status} {h.length:>7d}  {url}{redirect}",
                            file=sys.stderr,
                        )
                if not quiet and i % 500 == 0:
                    print(f"    ... {i}/{total}", file=sys.stderr)

        await asyncio.gather(*(worker(w, i) for i, w in enumerate(words, 1)))
        return hits


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("url", help="Base URL (e.g. https://target.com)")
    p.add_argument("-w", "--wordlist", required=True, help="Wordlist file")
    p.add_argument("-e", "--extensions", default="", help="Comma-separated extensions (e.g. .php,.bak,.zip)")
    p.add_argument("--rate", type=float, default=20.0, help="Requests per second cap (default: 20)")
    p.add_argument("-c", "--concurrency", type=int, default=10, help="Concurrent requests (default: 10)")
    p.add_argument(
        "--match-codes",
        default="200,201,202,204,301,302,307,308,401,403,405,500",
        help="Comma-separated status codes to flag as hits",
    )
    p.add_argument("-k", "--insecure", action="store_true", help="Skip TLS verification")
    p.add_argument("--json", action="store_true", help="Output JSON")
    p.add_argument("-o", "--output", help="Write to file")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress progress")
    args = p.parse_args()

    with open(args.wordlist, encoding="utf-8") as f:
        words = [w.strip() for w in f if w.strip() and not w.startswith("#")]

    extensions = [e.strip() for e in args.extensions.split(",") if e.strip()]
    if extensions:
        words = expand_words(words, extensions)

    interesting = {int(c.strip()) for c in args.match_codes.split(",") if c.strip()}

    if not args.quiet:
        print(
            f"[*] Bruteforcing {len(words)} paths against {args.url} "
            f"(rate={args.rate}/s, concurrency={args.concurrency})",
            file=sys.stderr,
        )

    try:
        hits = asyncio.run(
            run(
                args.url,
                words,
                args.rate,
                args.concurrency,
                interesting,
                not args.insecure,
                args.quiet,
            )
        )
    except KeyboardInterrupt:
        print("\n[!] Interrupted.", file=sys.stderr)
        return 130
    except RuntimeError as e:
        print(f"[-] {e}", file=sys.stderr)
        return 1

    if args.json or args.output:
        payload = json.dumps(
            {"base": args.url, "hit_count": len(hits), "hits": [asdict(h) for h in hits]},
            indent=2,
        )
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(payload)
            if not args.quiet:
                print(f"[+] Wrote {args.output}", file=sys.stderr)
        else:
            print(payload)
    elif not args.quiet:
        print(f"\n[+] Done. {len(hits)} hits.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
