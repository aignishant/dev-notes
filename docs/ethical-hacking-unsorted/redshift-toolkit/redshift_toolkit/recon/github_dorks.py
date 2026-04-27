#!/usr/bin/env python3
"""
redshift_toolkit.recon.github_dorks — GitHub code search runner with a
curated list of high-signal dorks.

Looks for leaked credentials, internal hostnames, configs, and other
artifacts that developers accidentally committed and that touch the
target organization or domain.

Token
-----
Set GITHUB_TOKEN in the environment to enable authenticated search.
Without a token, you'll be heavily rate-limited and search coverage is
poorer. Generate a fine-grained PAT with public_repo read scope.

Usage
-----
  export GITHUB_TOKEN=ghp_...
  python3 -m redshift_toolkit.recon.github_dorks --org acme
  python3 -m redshift_toolkit.recon.github_dorks --org acme --domain acme.com
  python3 -m redshift_toolkit.recon.github_dorks --domain acme.com --json
  python3 -m redshift_toolkit.recon.github_dorks --org acme --dorks-file mydorks.txt

Author: Redshift Project — Module 09
License: MIT
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import sys
import time
from dataclasses import dataclass, asdict, field

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


# Curated dork list. {ORG} and {DOMAIN} are placeholders.
# Entries with no placeholder run unconditionally.
DEFAULT_DORKS = [
    # Cloud credentials
    ("aws-access-key", '"{DOMAIN}" AKIA'),
    ("aws-key-pattern", '"AKIA[0-9A-Z]{{16}}" "{DOMAIN}"'),
    ("aws-secret", '"{DOMAIN}" "aws_secret_access_key"'),
    ("gcp-key", '"{DOMAIN}" "GOOGLE_APPLICATION_CREDENTIALS"'),
    ("azure-conn", '"{DOMAIN}" "DefaultEndpointsProtocol=https"'),
    # Generic credentials & private keys
    ("private-key-rsa", '"{DOMAIN}" "BEGIN RSA PRIVATE KEY"'),
    ("private-key-ed25519", '"{DOMAIN}" "BEGIN OPENSSH PRIVATE KEY"'),
    ("password-yaml", '"{DOMAIN}" filename:.yml password'),
    ("password-env", '"{DOMAIN}" filename:.env'),
    ("dotenv", 'filename:.env "{DOMAIN}"'),
    # CI/CD secrets
    ("jenkins-internal", '"jenkins.{DOMAIN}"'),
    ("ci-token", '"{DOMAIN}" "CI_TOKEN"'),
    # DB connection strings
    ("mongo-uri", '"{DOMAIN}" "mongodb+srv://"'),
    ("postgres-uri", '"{DOMAIN}" "postgres://" password'),
    ("redis-uri", '"{DOMAIN}" "redis://"'),
    # Internal hostnames / DNS leaks
    ("internal-host", '"corp.{DOMAIN}"'),
    ("vpn-host", '"vpn.{DOMAIN}"'),
    # API keys generic
    ("api-key", '"{DOMAIN}" "api_key"'),
    ("auth-bearer", '"{DOMAIN}" "Authorization: Bearer"'),
    ("slack-webhook", '"{DOMAIN}" "hooks.slack.com"'),
    # Org-scoped (need ORG)
    ("org-aws-key", 'org:{ORG} AKIA'),
    ("org-jenkins", 'org:{ORG} "jenkins"'),
    ("org-rsa", 'org:{ORG} "BEGIN RSA PRIVATE KEY"'),
    ("org-dotenv", 'org:{ORG} filename:.env'),
    ("org-tfvars", 'org:{ORG} extension:tfvars'),
]


@dataclass
class Hit:
    dork_name: str
    query: str
    repo_full_name: str
    file_path: str
    html_url: str
    fragment: str | None = None


@dataclass
class Report:
    org: str | None
    domain: str | None
    queries_run: int = 0
    hits: list[Hit] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def github_search(query: str, token: str | None,
                  per_page: int = 30) -> tuple[list[dict], int | None]:
    """Search GitHub code endpoint. Returns (items, status_code).
    Honors basic rate limiting (sleeps on 403 when reset header present).
    """
    import urllib.parse
    qs = urllib.parse.urlencode({"q": query, "per_page": per_page})
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "redshift-toolkit",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    conn = http.client.HTTPSConnection("api.github.com", timeout=15)
    try:
        conn.request("GET", f"/search/code?{qs}", headers=headers)
        r = conn.getresponse()
        body = r.read()
        if r.status == 403:
            # Possibly rate-limited
            reset = r.getheader("X-RateLimit-Reset")
            remaining = r.getheader("X-RateLimit-Remaining")
            if remaining == "0" and reset:
                wait = max(0, int(reset) - int(time.time()) + 2)
                if wait < 90:
                    time.sleep(wait)
            return [], 403
        if r.status >= 400:
            return [], r.status
        data = json.loads(body)
        return data.get("items", []), 200
    finally:
        conn.close()


def run(org: str | None, domain: str | None,
        dorks: list[tuple[str, str]] | None = None,
        per_dork: int = 10, delay: float = 6.0,
        token: str | None = None) -> Report:
    rep = Report(org=org, domain=domain)
    dorks = dorks or DEFAULT_DORKS
    if not token:
        rep.notes.append("no GITHUB_TOKEN set — heavily rate-limited results")

    for name, template in dorks:
        if "{ORG}" in template and not org:
            continue
        if "{DOMAIN}" in template and not domain:
            continue
        query = template.replace("{ORG}", org or "").replace("{DOMAIN}", domain or "")
        rep.queries_run += 1

        items, status = github_search(query, token, per_page=per_dork)
        if status == 403:
            rep.notes.append(f"rate-limited on '{name}'; partial results")
        for it in items[:per_dork]:
            repo = (it.get("repository") or {}).get("full_name", "?")
            path = it.get("path", "?")
            url = it.get("html_url", "")
            frag = None
            text_matches = it.get("text_matches") or []
            if text_matches:
                frag = (text_matches[0].get("fragment") or "")[:200]
            rep.hits.append(Hit(name, query, repo, path, url, frag))
        time.sleep(delay)
    return rep


def render_text(r: Report, color: bool) -> str:
    out = [paint(f"\n=== GitHub dorks: org={r.org} domain={r.domain} ===",
                 BOLD, color),
           f"  queries run: {r.queries_run}",
           f"  hits: {len(r.hits)}"]
    if r.notes:
        for n in r.notes:
            out.append(paint(f"  note: {n}", YELLOW, color))
    by_dork: dict[str, list[Hit]] = {}
    for h in r.hits:
        by_dork.setdefault(h.dork_name, []).append(h)
    for dork in sorted(by_dork):
        hits = by_dork[dork]
        out.append(paint(f"\n  [{dork}]  {len(hits)} hit(s)", GREEN, color))
        for h in hits[:8]:
            out.append(f"    {h.repo_full_name:<40} {h.file_path}")
            out.append(paint(f"      {h.html_url}", GREY, color))
            if h.fragment:
                snippet = h.fragment.replace("\n", " ⏎ ")[:120]
                out.append(paint(f"      “{snippet}”", GREY, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="GitHub code search dork runner.")
    ap.add_argument("--org", help="GitHub org name")
    ap.add_argument("--domain", help="target domain")
    ap.add_argument("--dorks-file",
                    help="custom dorks file (one query template per line)")
    ap.add_argument("--per-dork", type=int, default=10)
    ap.add_argument("--delay", type=float, default=6.0,
                    help="seconds between queries to dodge rate limits")
    ap.add_argument("--token-env", default="GITHUB_TOKEN")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    if not args.org and not args.domain:
        print("must specify at least --org or --domain", file=sys.stderr)
        return 2

    dorks = DEFAULT_DORKS
    if args.dorks_file:
        custom = []
        with open(args.dorks_file) as f:
            for ln in f:
                ln = ln.strip()
                if not ln or ln.startswith("#"):
                    continue
                custom.append((f"custom-{len(custom)}", ln))
        dorks = custom

    token = os.environ.get(args.token_env)
    rep = run(args.org, args.domain, dorks, args.per_dork, args.delay, token)

    if args.json:
        print(json.dumps({
            "org": rep.org, "domain": rep.domain,
            "queries_run": rep.queries_run,
            "hits": [asdict(h) for h in rep.hits],
            "notes": rep.notes,
        }, indent=2))
    else:
        print(render_text(rep, color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
