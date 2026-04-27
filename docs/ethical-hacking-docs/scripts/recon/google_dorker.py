#!/usr/bin/env python3
"""
google_dorker.py — Generate Google dork queries for a target.

Produces categorized, copy-paste-ready dork queries given a target domain.
Does NOT automatically execute searches — search engines rate-limit, require
ToS-respecting use, and CAPTCHA aggressive automation. Manual execution of
the produced queries (or via a paid search API) is the user's responsibility.

⚠️ AUTHORIZATION REQUIRED ⚠️
Dorks are passive in spirit (you query the search engine, not the target),
but acting on findings (downloading files, accessing exposed admin panels,
using leaked credentials) without authorization is unauthorized access.

Usage:
    python3 google_dorker.py example.com
    python3 google_dorker.py example.com --categories secrets,exposed_files
    python3 google_dorker.py example.com --json -o dorks.json
    python3 google_dorker.py example.com --engine bing
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from dataclasses import dataclass

# Each entry: (category, description, query_template)
# {d} expands to the target domain.
DORK_TEMPLATES: list[tuple[str, str, str]] = [
    # ---- Site presence & subdomains
    ("subdomains", "All indexed pages on the domain", "site:{d}"),
    ("subdomains", "Subdomains (excludes www)", "site:*.{d} -site:www.{d}"),
    ("subdomains", "Internal-flavored subdomains", "site:{d} (intranet OR internal OR dev OR staging OR test OR uat OR qa)"),

    # ---- Exposed files
    ("exposed_files", "Backup files", "site:{d} (ext:bak OR ext:backup OR ext:old OR ext:save OR ext:swp)"),
    ("exposed_files", "Config files", "site:{d} (ext:conf OR ext:cnf OR ext:ini OR ext:cfg OR ext:env OR ext:yaml OR ext:yml)"),
    ("exposed_files", "SQL dumps", "site:{d} (ext:sql OR ext:dump OR ext:db OR ext:bak)"),
    ("exposed_files", "Logs", "site:{d} (ext:log OR \"error.log\" OR \"access.log\")"),
    ("exposed_files", "Source archives", "site:{d} (ext:zip OR ext:rar OR ext:tar OR ext:gz OR ext:7z)"),
    ("exposed_files", "Documents (often metadata-rich)", "site:{d} (ext:pdf OR ext:doc OR ext:docx OR ext:xls OR ext:xlsx)"),

    # ---- Directory listings
    ("directory_listing", "Apache dir listing", 'site:{d} intitle:"index of"'),
    ("directory_listing", "Nginx dir listing", 'site:{d} "Index of /"'),
    ("directory_listing", "Tomcat manager", 'site:{d} intitle:"Apache Tomcat"'),

    # ---- Login pages
    ("login_pages", "Generic admin/login", 'site:{d} (inurl:admin OR inurl:login OR inurl:signin OR inurl:portal OR inurl:account)'),
    ("login_pages", "WP admin", 'site:{d} inurl:wp-admin'),
    ("login_pages", "phpMyAdmin", 'site:{d} (inurl:phpmyadmin OR intitle:"phpMyAdmin")'),
    ("login_pages", "cPanel", 'site:{d} inurl:cpanel'),
    ("login_pages", "Drupal admin", 'site:{d} inurl:user/login'),
    ("login_pages", "RDP web client", 'site:{d} inurl:RDWeb'),
    ("login_pages", "VPN portals", 'site:{d} (inurl:vpn OR inurl:remote OR "FortiGate" OR "Pulse Secure")'),

    # ---- Secrets & credentials in indexed pages
    ("secrets", "API keys / tokens", 'site:{d} ("api_key" OR "apikey" OR "api-key" OR "access_token" OR "client_secret")'),
    ("secrets", "Passwords / credentials", 'site:{d} (intext:password OR intext:passwd OR intext:credentials)'),
    ("secrets", "DB connection strings", 'site:{d} ("jdbc:" OR "mongodb://" OR "postgres://" OR "mysql://" OR "redis://")'),
    ("secrets", "AWS access keys", 'site:{d} "AKIA"'),
    ("secrets", "Private keys", 'site:{d} "BEGIN RSA PRIVATE KEY" OR "BEGIN OPENSSH PRIVATE KEY"'),

    # ---- Specific exposed services
    ("specific", "Git web interfaces", 'site:{d} (inurl:.git OR intitle:"Index of /.git")'),
    ("specific", "Jenkins", 'site:{d} (intitle:"Dashboard [Jenkins]" OR inurl:jenkins)'),
    ("specific", "GitLab", 'site:{d} (intitle:"GitLab" inurl:users/sign_in)'),
    ("specific", "Confluence", 'site:{d} (inurl:/spaces/ OR "Powered by Atlassian Confluence")'),
    ("specific", "Jira", 'site:{d} (inurl:browse/ OR inurl:secure/Dashboard.jspa)'),
    ("specific", "SonarQube", 'site:{d} intitle:"SonarQube"'),
    ("specific", "Grafana", 'site:{d} inurl:/d/'),
    ("specific", "Kibana", 'site:{d} (intitle:"Kibana" OR inurl:/app/kibana)'),
    ("specific", "Spring Actuator endpoints", 'site:{d} (inurl:/actuator/env OR inurl:/actuator/heapdump OR inurl:/actuator/mappings)'),

    # ---- Errors and stack traces
    ("errors", "Stack traces / debug pages", 'site:{d} ("Whitelabel Error Page" OR "Werkzeug Debugger" OR "Django Traceback" OR "PHP Fatal error")'),
    ("errors", "SQL errors leaked", 'site:{d} ("ORA-00921" OR "mysql_fetch_array()" OR "PostgreSQL.*ERROR" OR "SQL syntax")'),

    # ---- Pivot OFF the domain (data leaked elsewhere)
    ("offsite_leaks", "Pastebin", 'site:pastebin.com {d}'),
    ("offsite_leaks", "GitHub mentions", 'site:github.com "{d}"'),
    ("offsite_leaks", "GitLab mentions", 'site:gitlab.com "{d}"'),
    ("offsite_leaks", "Stack Overflow / dev forum mentions", 'site:stackoverflow.com {d}'),
    ("offsite_leaks", "Dev.to / Medium / blog posts", '("{d}" OR "{d_root}") (site:dev.to OR site:medium.com)'),
    ("offsite_leaks", "Trello boards", 'site:trello.com {d}'),
    ("offsite_leaks", "Postman collections", 'site:postman.com {d}'),
    ("offsite_leaks", "Public S3 buckets", '"{d_root}" site:s3.amazonaws.com'),

    # ---- People (use carefully and ethically)
    ("people", "LinkedIn employees", 'site:linkedin.com/in "{d_root}"'),
    ("people", "Email format hints", '"{d}" "@{d}"'),
]


SEARCH_ENGINE_URLS = {
    "google": "https://www.google.com/search?q={q}",
    "bing": "https://www.bing.com/search?q={q}",
    "duckduckgo": "https://duckduckgo.com/?q={q}",
    "brave": "https://search.brave.com/search?q={q}",
}


@dataclass
class Dork:
    category: str
    description: str
    query: str
    url: str


def make_dorks(domain: str, engine: str) -> list[Dork]:
    domain = domain.strip().lower().lstrip(".")
    root = ".".join(domain.split(".")[-2:]) if domain.count(".") >= 1 else domain
    base = SEARCH_ENGINE_URLS[engine]
    out = []
    for cat, desc, tmpl in DORK_TEMPLATES:
        q = tmpl.format(d=domain, d_root=root)
        url = base.format(q=urllib.parse.quote_plus(q))
        out.append(Dork(category=cat, description=desc, query=q, url=url))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("domain", help="Target domain (e.g. example.com)")
    p.add_argument(
        "--categories",
        help="Comma-separated category filter (e.g. secrets,exposed_files,login_pages). Default: all.",
    )
    p.add_argument(
        "--engine",
        choices=list(SEARCH_ENGINE_URLS),
        default="google",
        help="Search engine for the URL (default: google)",
    )
    p.add_argument("--json", action="store_true", help="Emit JSON")
    p.add_argument("-o", "--output", help="Write to file")
    args = p.parse_args()

    dorks = make_dorks(args.domain, args.engine)

    if args.categories:
        wanted = {c.strip() for c in args.categories.split(",")}
        dorks = [d for d in dorks if d.category in wanted]
        if not dorks:
            print(f"[-] No dorks match categories {wanted}.", file=sys.stderr)
            return 2

    if args.json or args.output:
        payload = json.dumps(
            [{"category": d.category, "description": d.description, "query": d.query, "url": d.url} for d in dorks],
            indent=2,
        )
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(payload)
            print(f"[+] Wrote {len(dorks)} dorks to {args.output}", file=sys.stderr)
        else:
            print(payload)
    else:
        current = ""
        for d in dorks:
            if d.category != current:
                current = d.category
                print(f"\n=== {current.upper().replace('_', ' ')} ===")
            print(f"\n  # {d.description}")
            print(f"  {d.query}")
            print(f"  → {d.url}")

    print(
        "\n[i] Reminder: review each query before executing. "
        "Search-engine ToS apply. Acting on findings without "
        "authorization may be illegal.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
