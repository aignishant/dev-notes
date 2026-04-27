#!/usr/bin/env python3
"""
redshift_toolkit.web.graphql_introspect — GraphQL schema dumper.

Sends the canonical introspection query and writes:
- the full schema JSON (for use by graphql_attacks.py)
- a human-readable summary
- a flagged list of "interesting" types whose fields contain
  password/secret/token/apiKey/credential/private/admin/etc.

Usage
-----
  python3 -m redshift_toolkit.web.graphql_introspect \\
      --url https://app.example.com/graphql --output schema.json
  python3 -m redshift_toolkit.web.graphql_introspect \\
      --url https://app.example.com/graphql --auth-cookie 'session=...'

Author: Redshift Project — Module 15
License: MIT
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
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


INTROSPECTION_QUERY = """
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
    types {
      kind
      name
      description
      fields(includeDeprecated: true) {
        name
        description
        args {
          name
          type { ...TypeRef }
          defaultValue
        }
        type { ...TypeRef }
        isDeprecated
        deprecationReason
      }
      inputFields {
        name
        type { ...TypeRef }
        defaultValue
      }
      enumValues(includeDeprecated: true) {
        name
        description
      }
    }
  }
}
fragment TypeRef on __Type {
  kind
  name
  ofType {
    kind
    name
    ofType {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
        }
      }
    }
  }
}
"""

# Patterns we flag as "interesting" in field/argument/type names.
SENSITIVE_PATTERNS = [
    re.compile(r"password", re.I),
    re.compile(r"secret", re.I),
    re.compile(r"token", re.I),
    re.compile(r"apikey", re.I),
    re.compile(r"api_key", re.I),
    re.compile(r"credential", re.I),
    re.compile(r"private", re.I),
    re.compile(r"admin", re.I),
    re.compile(r"ssn", re.I),
    re.compile(r"creditcard|credit_card", re.I),
    re.compile(r"^iban$", re.I),
    re.compile(r"internal", re.I),
    re.compile(r"impersonate", re.I),
    re.compile(r"bypass", re.I),
    re.compile(r"debug", re.I),
]


def is_sensitive(name: str) -> bool:
    return any(p.search(name) for p in SENSITIVE_PATTERNS)


@dataclass
class GraphqlSummary:
    query_type: str | None = None
    mutation_type: str | None = None
    subscription_type: str | None = None
    type_count: int = 0
    query_fields: list[str] = field(default_factory=list)
    mutation_fields: list[str] = field(default_factory=list)
    interesting: list[str] = field(default_factory=list)


def fetch_schema(url: str, *, headers: list[tuple[str, str]] | None = None,
                 tls_verify: bool = True, timeout: float = 30.0
                 ) -> tuple[dict | None, int, str]:
    h = list(headers or [])
    if not any(k.lower() == "content-type" for k, _ in h):
        h.append(("Content-Type", "application/json"))
    body = json.dumps({"query": INTROSPECTION_QUERY})
    r = send(HttpRequest(method="POST", url=url, headers=h, body=body),
             timeout=timeout, tls_verify=tls_verify, follow_redirects=False)
    text = r.body.decode("utf-8", errors="replace")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None, r.status, text[:500]
    return data, r.status, text[:500]


def summarize(schema: dict) -> GraphqlSummary:
    s = GraphqlSummary()
    sch = schema.get("data", {}).get("__schema") if isinstance(schema, dict) else None
    if not sch:
        return s
    s.query_type = (sch.get("queryType") or {}).get("name")
    s.mutation_type = (sch.get("mutationType") or {}).get("name")
    s.subscription_type = (sch.get("subscriptionType") or {}).get("name")
    s.type_count = len(sch.get("types") or [])

    for t in sch.get("types") or []:
        tname = t.get("name") or ""
        if tname.startswith("__"):
            continue
        if tname == s.query_type:
            for f in t.get("fields") or []:
                s.query_fields.append(f["name"])
        if tname == s.mutation_type:
            for f in t.get("fields") or []:
                s.mutation_fields.append(f["name"])
        if is_sensitive(tname):
            s.interesting.append(f"type {tname}")
        for f in (t.get("fields") or []):
            if is_sensitive(f["name"]):
                s.interesting.append(f"{tname}.{f['name']}")
            for arg in (f.get("args") or []):
                if is_sensitive(arg["name"]):
                    s.interesting.append(
                        f"arg {arg['name']} on {tname}.{f['name']}")
        for f in (t.get("inputFields") or []):
            if is_sensitive(f["name"]):
                s.interesting.append(f"{tname}.{f['name']} (input)")
    return s


def render_text(summary: GraphqlSummary, color: bool) -> str:
    out = [paint("\n=== GraphQL schema summary ===", BOLD, color)]
    out.append(f"  Query type:        {summary.query_type or '(none)'}")
    out.append(f"  Mutation type:     {summary.mutation_type or '(none)'}")
    out.append(f"  Subscription type: {summary.subscription_type or '(none)'}")
    out.append(f"  Total types:       {summary.type_count}")

    out.append(paint(f"\n  Query fields ({len(summary.query_fields)}):", BOLD, color))
    for q in summary.query_fields[:50]:
        out.append(f"    - {q}")
    if len(summary.query_fields) > 50:
        out.append(f"    … +{len(summary.query_fields) - 50} more")

    out.append(paint(f"\n  Mutation fields ({len(summary.mutation_fields)}):",
                     BOLD, color))
    for m in summary.mutation_fields[:50]:
        out.append(f"    - {m}")
    if len(summary.mutation_fields) > 50:
        out.append(f"    … +{len(summary.mutation_fields) - 50} more")

    if summary.interesting:
        out.append(paint(f"\n  Sensitive-looking ({len(summary.interesting)}):",
                         BOLD, color))
        for x in summary.interesting[:50]:
            out.append(f"    - {paint(x, YELLOW, color)}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="GraphQL introspection dumper.")
    ap.add_argument("--url", required=True)
    ap.add_argument("--auth-cookie", help="Cookie header value")
    ap.add_argument("--bearer", help="Bearer token (Authorization header)")
    ap.add_argument("-H", "--header", action="append", default=[])
    ap.add_argument("--output", help="write full schema JSON here")
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("--json", action="store_true",
                    help="print the full schema (or summary if introspection failed) "
                         "as JSON to stdout")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    headers = []
    if args.auth_cookie:
        headers.append(("Cookie", args.auth_cookie))
    if args.bearer:
        headers.append(("Authorization", f"Bearer {args.bearer}"))
    for h in args.header:
        if ":" in h:
            k, v = h.split(":", 1)
            headers.append((k.strip(), v.strip()))

    schema, status, excerpt = fetch_schema(args.url, headers=headers,
                                            tls_verify=not args.insecure,
                                            timeout=args.timeout)
    if not schema or "data" not in schema or not schema.get("data"):
        msg = (f"introspection request returned status={status}, "
               f"body excerpt: {excerpt!r}")
        if args.json:
            print(json.dumps({"error": "introspection failed",
                              "status": status, "excerpt": excerpt}))
        else:
            print(paint(f"[!] {msg}", RED, color), file=sys.stderr)
        return 1

    summary = summarize(schema)
    if args.output:
        with open(args.output, "w") as f:
            json.dump(schema, f, indent=2)
        if not args.json:
            print(paint(f"[+] full schema written to {args.output}", GREEN, color))

    if args.json:
        print(json.dumps({"summary": asdict(summary), "schema": schema}, indent=2))
    else:
        print(render_text(summary, color))

    return 0


if __name__ == "__main__":
    sys.exit(main())
