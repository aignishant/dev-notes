#!/usr/bin/env python3
"""
redshift_toolkit.web.dependency_confusion — find unsquatted internal
package names in npm/PyPI/RubyGems.

Methodology
-----------
1. Read package names from --packages-file (one per line) or --extract
   from a package.json / requirements.txt / Gemfile / pyproject.toml.
2. For each name, query the corresponding public registry:
   - npm:    https://registry.npmjs.org/<name>
   - PyPI:   https://pypi.org/pypi/<name>/json
   - RubyGems: https://rubygems.org/api/v1/gems/<name>.json
3. If the registry returns 404 (or 200 with no maintainer = squat), the
   name is registrable on the public registry.
4. Report all squat-able candidates.

Usage
-----
  python3 -m redshift_toolkit.web.dependency_confusion \\
      --packages-file pkgs.txt --registry npm
  python3 -m redshift_toolkit.web.dependency_confusion \\
      --extract /path/to/package.json --registry npm

Author: Redshift Project — Module 16
License: MIT — Reconnaissance only. NEVER publish a package by the same
name without written authorization from the package's owning organization.
"""

from __future__ import annotations

import argparse
import json
import os
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


REGISTRIES = {
    "npm": ("https://registry.npmjs.org/{name}",
            lambda r: r.status == 404 or r.status == 200),
    "pypi": ("https://pypi.org/pypi/{name}/json",
             lambda r: r.status == 404),
    "rubygems": ("https://rubygems.org/api/v1/gems/{name}.json",
                  lambda r: r.status == 404),
}


@dataclass
class DepFinding:
    package: str
    registry: str
    status: int
    available: bool
    note: str = ""


def extract_from_file(path: str) -> list[str]:
    """Best-effort extract package names from a manifest."""
    text = open(path).read()
    base = os.path.basename(path).lower()
    names: list[str] = []
    if base == "package.json":
        try:
            data = json.loads(text)
            for sec in ("dependencies", "devDependencies",
                        "peerDependencies", "optionalDependencies"):
                names.extend((data.get(sec) or {}).keys())
        except json.JSONDecodeError:
            pass
    elif base == "requirements.txt" or base.endswith(".txt"):
        for ln in text.splitlines():
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            # remove version specifier
            m = re.match(r"^([A-Za-z0-9_.\-]+)", ln)
            if m:
                names.append(m.group(1))
    elif base == "pyproject.toml":
        # crude line-based
        for ln in text.splitlines():
            m = re.match(r'\s*"([A-Za-z0-9_.\-]+)"', ln)
            if m:
                names.append(m.group(1))
    elif base == "gemfile" or base == "gemfile.lock":
        for ln in text.splitlines():
            m = re.search(r"^\s*gem\s+['\"]([^'\"]+)", ln)
            if m:
                names.append(m.group(1))
    else:
        # fallback: any package-name-shaped tokens
        names = re.findall(r"[\"']([@a-zA-Z0-9_./\-]{3,40})[\"']", text)
    # de-dupe, preserve order
    seen = set()
    out = []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def check(name: str, registry: str, *, timeout: float = 10.0) -> DepFinding:
    if registry not in REGISTRIES:
        return DepFinding(package=name, registry=registry, status=0,
                           available=False, note=f"unknown registry: {registry}")
    url_tmpl, available_pred = REGISTRIES[registry]
    url = url_tmpl.format(name=name)
    try:
        r = send(HttpRequest(method="GET", url=url),
                 timeout=timeout, tls_verify=True, follow_redirects=True)
    except Exception as e:
        return DepFinding(package=name, registry=registry, status=0,
                           available=False, note=f"request failed: {e}")

    note = ""
    available = False
    if r.status == 404:
        available = True
        note = "package name is unregistered → squat-able"
    elif r.status == 200 and registry == "npm":
        # If npm replies with 200, the package exists. We do NOT mark it
        # available. (npm returns 404 for non-existent.)
        note = "package exists on npm"
    elif r.status == 200:
        note = "package exists"
    else:
        note = f"unusual status {r.status}"
    return DepFinding(package=name, registry=registry, status=r.status,
                       available=available, note=note)


def main() -> int:
    ap = argparse.ArgumentParser(description="Dependency confusion checker.")
    ap.add_argument("--packages-file", help="one package name per line")
    ap.add_argument("--extract", help="extract from package.json/requirements.txt/Gemfile")
    ap.add_argument("--registry", default="npm",
                    choices=list(REGISTRIES.keys()))
    ap.add_argument("--timeout", type=float, default=10.0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    if args.extract:
        names = extract_from_file(args.extract)
    elif args.packages_file:
        names = [ln.strip() for ln in open(args.packages_file)
                 if ln.strip() and not ln.startswith("#")]
    else:
        print("[!] need --extract or --packages-file", file=sys.stderr)
        return 2
    if not names:
        print("[!] no package names found", file=sys.stderr)
        return 2

    findings = [check(n, args.registry, timeout=args.timeout) for n in names]

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        print(paint(f"\n=== Dependency confusion check ({args.registry}) ===",
                    BOLD, color))
        for f in findings:
            tag = (paint("[OPEN]", RED, color) if f.available
                   else paint("[----]", GREEN, color))
            print(f"  {tag} {f.package:<40} status={f.status}  {f.note}")
        squat = [f for f in findings if f.available]
        print(paint(f"\n[{len(squat)} squat-able package(s) of {len(findings)}]",
                    BOLD, color))

    return 0 if not any(f.available for f in findings) else 1


if __name__ == "__main__":
    sys.exit(main())
