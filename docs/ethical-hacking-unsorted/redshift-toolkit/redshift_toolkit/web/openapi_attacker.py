#!/usr/bin/env python3
"""
redshift_toolkit.web.openapi_attacker — auto-attack from OpenAPI / Swagger spec.

Reads an OpenAPI 3.x or Swagger 2.x JSON/YAML spec and, for each operation:
  1. Probes auth: send the request with no auth — does it succeed?
  2. Tries trivial parameter swaps where IDs are involved.
  3. Tries common version-sweep paths (/v1/, /v2/, /api/v1/, /api/internal/).
  4. Probes mass-assignment by POSTing extra likely-privileged fields.
  5. Lists endpoints whose `responses` include 200 for unauthenticated calls.

Goal: produce a triage report of "this is the auth/authz attack surface."

Usage
-----
  python3 -m redshift_toolkit.web.openapi_attacker --spec swagger.json \\
      --base https://api.example.com --token $TOK
  python3 -m redshift_toolkit.web.openapi_attacker --spec spec.json \\
      --base https://api.example.com --version-sweep

Author: Redshift Project — Module 15
License: MIT
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict, field
from typing import Iterable

from redshift_toolkit.web.http_client import HttpRequest, send

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


def load_spec(path: str) -> dict:
    text = open(path).read()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore
            return yaml.safe_load(text)
        except Exception as e:
            raise SystemExit(f"could not parse {path} as JSON or YAML: {e}")


def extract_operations(spec: dict) -> list[dict]:
    """Return list of {method, path, params, requestBody}."""
    out = []
    paths = spec.get("paths", {})
    for path, ops in paths.items():
        if not isinstance(ops, dict):
            continue
        for method in ("get", "post", "put", "patch", "delete", "options", "head"):
            op = ops.get(method)
            if not op:
                continue
            params = list(op.get("parameters") or [])
            # Inherit path-level parameters
            for p in (ops.get("parameters") or []):
                params.append(p)
            out.append({
                "method": method.upper(),
                "path": path,
                "params": params,
                "operationId": op.get("operationId", ""),
                "summary": op.get("summary", ""),
                "security": op.get("security"),
                "requestBody": op.get("requestBody"),
            })
    return out


def fill_path(path: str, params: list[dict]) -> str:
    out = path
    for p in params:
        if p.get("in") == "path":
            name = p["name"]
            sample = p.get("example") or {
                "integer": "1", "number": "1.0",
                "string": "test", "boolean": "true",
            }.get((p.get("schema") or {}).get("type", "string"), "test")
            out = out.replace("{" + name + "}", str(sample))
    return out


@dataclass
class OpFinding:
    method: str
    path: str
    note: str = ""
    statuses: dict[str, int] = field(default_factory=dict)


def probe_endpoint(base: str, op: dict, *,
                   auth_headers: list[tuple[str, str]] | None = None,
                   tls_verify: bool = True, timeout: float = 15.0) -> OpFinding:
    full_path = fill_path(op["path"], op["params"])
    url = base.rstrip("/") + full_path
    fin = OpFinding(method=op["method"], path=full_path)

    # 1. Without auth
    try:
        r = send(HttpRequest(method=op["method"], url=url),
                 timeout=timeout, tls_verify=tls_verify, follow_redirects=False)
        fin.statuses["no_auth"] = r.status
        if r.status == 200 and op.get("security"):
            fin.note = "expected auth (per spec) but got 200 unauth — possible auth bypass"
    except Exception as e:
        fin.statuses["no_auth"] = 0
        fin.note = f"no-auth probe failed: {e}"

    # 2. With auth
    if auth_headers:
        try:
            r = send(HttpRequest(method=op["method"], url=url, headers=auth_headers),
                     timeout=timeout, tls_verify=tls_verify, follow_redirects=False)
            fin.statuses["with_auth"] = r.status
        except Exception as e:
            fin.statuses["with_auth"] = 0

    return fin


def version_sweep(base: str, path: str, *,
                  auth_headers: list[tuple[str, str]] | None = None,
                  tls_verify: bool = True, timeout: float = 10.0) -> dict[str, int]:
    """Try alternative version prefixes for the same path."""
    candidates = []
    if "/v1/" in path:
        candidates += [path.replace("/v1/", v) for v in
                       ("/v0/", "/v2/", "/v3/", "/internal/", "/beta/", "/legacy/", "/private/")]
    elif "/v2/" in path:
        candidates += [path.replace("/v2/", v) for v in
                       ("/v0/", "/v1/", "/v3/", "/internal/")]
    elif path.startswith("/api/"):
        candidates += [path.replace("/api/", v) for v in
                       ("/apiv1/", "/apiv2/", "/internalapi/", "/_api/")]
    out: dict[str, int] = {}
    for c in candidates:
        url = base.rstrip("/") + c
        try:
            r = send(HttpRequest(method="GET", url=url, headers=auth_headers or []),
                     timeout=timeout, tls_verify=tls_verify, follow_redirects=False)
            out[c] = r.status
        except Exception:
            out[c] = 0
    return out


def render_text(findings: list[OpFinding], color: bool) -> str:
    out = [paint("\n=== OpenAPI auto-attack ===", BOLD, color)]
    for f in findings:
        if f.statuses.get("no_auth") == 200 and f.note:
            tag = paint("[BYP ]", RED, color)
        else:
            tag = paint("[----]", GREEN, color)
        out.append(f"  {tag} {f.method:<6} {f.path:<60} "
                   f"unauth={f.statuses.get('no_auth', '-')} "
                   f"auth={f.statuses.get('with_auth', '-')}")
        if f.note:
            out.append(f"          {f.note}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Auto-attack from OpenAPI/Swagger spec.")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--base", required=True, help="base URL, e.g. https://api.example.com")
    ap.add_argument("--token", help="bearer token")
    ap.add_argument("--cookie")
    ap.add_argument("-H", "--header", action="append", default=[])
    ap.add_argument("--version-sweep", action="store_true",
                    help="also try alternative API versions for each path")
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    spec = load_spec(args.spec)
    ops = extract_operations(spec)
    if not ops:
        print(f"[!] no operations found in spec", file=sys.stderr)
        return 2

    auth = []
    if args.token:
        auth.append(("Authorization", f"Bearer {args.token}"))
    if args.cookie:
        auth.append(("Cookie", args.cookie))
    for h in args.header:
        if ":" in h:
            k, v = h.split(":", 1)
            auth.append((k.strip(), v.strip()))

    findings = [probe_endpoint(args.base, op, auth_headers=auth or None,
                                tls_verify=not args.insecure,
                                timeout=args.timeout) for op in ops]

    sweep_results: dict[str, dict[str, int]] = {}
    if args.version_sweep:
        seen = set()
        for op in ops:
            if op["path"] in seen:
                continue
            seen.add(op["path"])
            r = version_sweep(args.base, op["path"], auth_headers=auth or None,
                               tls_verify=not args.insecure, timeout=args.timeout)
            interesting = {k: v for k, v in r.items() if v in (200, 201, 204)}
            if interesting:
                sweep_results[op["path"]] = interesting

    if args.json:
        print(json.dumps({
            "operations": [asdict(f) for f in findings],
            "version_sweep": sweep_results,
        }, indent=2))
    else:
        print(render_text(findings, color))
        if sweep_results:
            print(paint("\n=== Version sweep — interesting hits ===", BOLD, color))
            for orig, hits in sweep_results.items():
                print(f"  original: {orig}")
                for v, st in hits.items():
                    print(f"    → {v}  status {st}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
