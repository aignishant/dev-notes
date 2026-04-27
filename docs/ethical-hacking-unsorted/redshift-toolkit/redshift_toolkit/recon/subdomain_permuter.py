#!/usr/bin/env python3
"""
redshift_toolkit.recon.subdomain_permuter — subdomain permutation engine.

Takes a list of seed subdomains and produces variations using a small
DSL of prefixes, suffixes, and transformations. The output is a flat
candidate list suitable for piping into `subdomain_enum.py`.

Patterns generated
------------------
- Prefix/suffix joins:  api → dev-api, api-dev, api-uat, prod-api
- Number suffixes:       api → api1, api2, … apiN
- Environment markers:   api → api.dev, api.uat, dev.api
- Region markers:        api → us-east-api, eu-west-api
- Word splits / merges:  api-prod ↔ api.prod ↔ apiprod
- Acronym substitution:  app-api → app-svc, app-bff (configurable)

Usage
-----
  python3 -m redshift_toolkit.recon.subdomain_permuter \\
        --seeds api,app,web --max 1000
  python3 -m redshift_toolkit.recon.subdomain_permuter \\
        --seeds-file seeds.txt --num-suffix 5 \\
        | python3 -m redshift_toolkit.recon.subdomain_enum \\
            --target example.com --wordlist -

Author: Redshift Project — Module 11
License: MIT
"""

from __future__ import annotations

import argparse
import json
import sys
from itertools import product

DEFAULT_PREFIXES = [
    "dev", "uat", "stg", "stage", "staging", "prod", "qa", "test",
    "internal", "external", "old", "new", "v1", "v2", "v3", "beta",
    "alpha", "preprod", "lab", "demo", "sandbox", "shared",
]

DEFAULT_SUFFIXES = [
    "old", "new", "bak", "backup", "tmp", "test", "dev", "internal",
    "private", "public", "v1", "v2", "v3", "1", "2", "3",
]

DEFAULT_REGIONS = [
    "us", "us-east", "us-west", "us-central",
    "eu", "eu-west", "eu-central",
    "ap", "ap-south", "ap-southeast", "ap-northeast",
]

JOINERS = ["-", ".", ""]


def permute(seed: str, prefixes: list[str], suffixes: list[str],
            regions: list[str], num_suffix: int,
            include_regions: bool) -> set[str]:
    out: set[str] = {seed}

    # prefix-seed and seed-prefix
    for p, j in product(prefixes, JOINERS):
        out.add(f"{p}{j}{seed}")
        out.add(f"{seed}{j}{p}")

    # seed-suffix
    for s, j in product(suffixes, JOINERS):
        out.add(f"{seed}{j}{s}")

    # number suffixes
    for n in range(1, num_suffix + 1):
        out.add(f"{seed}{n}")
        out.add(f"{seed}-{n}")
        out.add(f"{seed}.{n}")

    # regions
    if include_regions:
        for r, j in product(regions, JOINERS):
            out.add(f"{r}{j}{seed}")
            out.add(f"{seed}{j}{r}")

    # if seed already contains a separator, also produce merged/split variants
    if "-" in seed:
        out.add(seed.replace("-", "."))
        out.add(seed.replace("-", ""))
    if "." in seed:
        out.add(seed.replace(".", "-"))
        out.add(seed.replace(".", ""))

    return {x for x in out if x and len(x) <= 63
            and all(c.isalnum() or c in "-." for c in x)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Subdomain permutation engine.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--seeds", help="comma-separated seed list")
    g.add_argument("--seeds-file", help="file with one seed per line")
    ap.add_argument("--prefixes", default=",".join(DEFAULT_PREFIXES))
    ap.add_argument("--suffixes", default=",".join(DEFAULT_SUFFIXES))
    ap.add_argument("--regions", default=",".join(DEFAULT_REGIONS))
    ap.add_argument("--no-regions", action="store_true")
    ap.add_argument("--num-suffix", type=int, default=5)
    ap.add_argument("--max", type=int, default=10000,
                    help="cap output count (sorted before slicing)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.seeds:
        seeds = [s.strip() for s in args.seeds.split(",") if s.strip()]
    else:
        with open(args.seeds_file) as f:
            seeds = [s.strip() for s in f
                     if s.strip() and not s.startswith("#")]

    prefixes = [p.strip() for p in args.prefixes.split(",") if p.strip()]
    suffixes = [s.strip() for s in args.suffixes.split(",") if s.strip()]
    regions = [r.strip() for r in args.regions.split(",") if r.strip()]

    candidates: set[str] = set()
    for seed in seeds:
        candidates.update(permute(
            seed, prefixes, suffixes, regions,
            args.num_suffix, not args.no_regions,
        ))

    final = sorted(candidates)[:args.max]
    if args.json:
        print(json.dumps({"seeds": seeds, "candidates": final,
                          "count": len(final)}, indent=2))
    else:
        for c in final:
            print(c)
    return 0


if __name__ == "__main__":
    sys.exit(main())
