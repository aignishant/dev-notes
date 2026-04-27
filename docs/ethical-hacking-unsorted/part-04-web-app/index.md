# Part 4 · Web Application Security

Welcome to the most lucrative and most actively contested attack surface on Earth: web applications. Every Fortune 500 firm, every government agency, every bank, every hospital lives behind a web tier. When that tier breaks — and it does, daily — the consequences are measured in billions of dollars, millions of patient records, or compromised national infrastructure.

This part takes you from the wire-level mechanics of HTTP all the way to the attacks defining 2024-2026 bug bounty payouts: HTTP/2 request smuggling, GraphQL batching abuse, prototype pollution gadget chains, OAuth state confusion, and SAML signature wrapping.

## Why web app security is non-negotiable

| Industry | Where the money is | Real-world precedent |
|---|---|---|
| **Financial services** | Authentication bypasses, IDOR on transfer endpoints, SSRF to internal banking APIs | Capital One 2019 (SSRF → 100M records) |
| **Healthcare** | Patient portal IDOR, HL7/FHIR API authorization, mass assignment on prescription endpoints | Multiple HIPAA breaches; HHS OCR settlements regularly $1M+ |
| **Government** | Authentication weaknesses, file upload to RCE, XXE in document upload | login.gov, DoD HackerOne reports, repeated GAO findings |
| **Critical infrastructure** | Operator portal auth bypass, SCADA HMI XSS-to-CSRF, vendor portal SSRF | Oldsmar water plant 2021 (remote access ~ web tier) |
| **Cloud / SaaS** | Tenant isolation breaks, JWT confusion, OAuth scope confusion | Microsoft 2023 token-signing-key compromise (CVE chain) |
| **E-commerce / Retail** | Cart manipulation, race conditions on coupons, payment SSRF | Magecart-class supply-chain attacks |

For a US Government cleared role you'll be asked, point-blank, "Walk me through finding and exploiting a SSRF in a cloud application." Part 4 prepares you to answer that.

## Modules

| # | Module | Focus |
|---|---|---|
| **13** | [Web Fundamentals for Attackers](13-web-fundamentals.md) | HTTP/1.1 / HTTP/2 / HTTP/3 wire format, browser security model, cookies, CORS, TLS quirks, the modern session lifecycle |
| **14** | [OWASP Top 10 Deep Dives](14-owasp-deep-dives.md) | A01-A10 with attacker-first walkthroughs and tool implementations: BAC/IDOR, injection (SQLi, XSS, XXE, command), SSRF, deserialization, misconfig |
| **15** | [Modern API Attacks](15-api-attacks.md) | REST, GraphQL, WebSocket, gRPC; mass assignment, BOLA, schema introspection abuse, batch attacks, OpenAPI-driven auto-attack |
| **16** | [Advanced Web Attacks](16-advanced-web.md) | HTTP/1 + HTTP/2 request smuggling, web cache poisoning + deception, prototype pollution, dependency confusion, host header attacks |
| **17** | [Authentication & Authorization](17-auth-authz.md) | OAuth 2.0/OIDC pitfalls, SAML XML-Signature attacks, session fixation, JWT pitfalls, password reset flaws, MFA bypass |

## Learning outcomes

By the end of Part 4 you can:

- Read and write **raw HTTP wire bytes** without `curl` or `requests` — you understand exactly what the browser sends, what the server parses, and where they disagree.
- Detect every **OWASP Top 10 (2021)** category with both manual probes and automated scripts. You know the difference between *finding* an XSS and *exploiting* it (CSP-bypass, framework gadget chains, DOM clobbering).
- Audit **modern APIs** (REST + GraphQL + WebSocket) for authorization flaws using OpenAPI specs and introspection.
- Detect **HTTP request smuggling** in CL.TE, TE.CL, TE.TE, and H2.0 variants and explain why each works.
- Audit **OAuth/OIDC and SAML** flows for the canonical mistakes (open redirect chain, PKCE bypass, ID token confusion, signature wrapping).
- Drive a full **web pentest engagement** with the toolkit: recon → auth audit → injection scan → API fuzz → smuggling probe → report.

## Prerequisites

You should be comfortable with everything from Parts 1-3:
- Python sockets, threading, async (Part 1)
- TCP/TLS handshake mechanics (Part 2)
- HTTP basics from the wire-level fingerprinter (Part 2 Module 08)
- DNS/recon outputs feeding into the asset graph (Part 3)

If any of these feel shaky, revisit them before continuing — the web tier sits on top of everything we've built so far.

## Toolkit additions in this part

`redshift_toolkit/web/` grows from an empty package to **25+ modules**:

```
redshift_toolkit/web/
├── http_client.py            # raw HTTP/1.1 client (no requests dep)
├── http2_client.py           # HTTP/2 frame-level client
├── cors_probe.py             # CORS misconfiguration detector
├── cookie_analyzer.py        # cookie security audit
├── tls_quirks.py             # TLS edge cases
├── sqli_oracle.py            # blind SQLi detector
├── xss_scanner.py            # reflected/stored/DOM XSS
├── xxe_oracle.py             # XML external entity
├── ssrf_prober.py            # SSRF + cloud metadata
├── path_traversal.py         # LFI/RFI scanner
├── cmd_injection.py          # command injection oracle
├── graphql_introspect.py     # GraphQL schema dumper
├── graphql_attacks.py        # batch / alias overloading
├── api_idor_fuzzer.py        # IDOR / BOLA / mass assignment
├── openapi_attacker.py       # auto-attack from Swagger spec
├── websocket_fuzzer.py       # WebSocket fuzzer
├── smuggler.py               # HTTP request smuggling
├── cache_poison_probe.py     # web cache poisoning
├── cache_deception.py        # cache deception
├── proto_pollution_probe.py  # prototype pollution
├── dependency_confusion.py   # dependency confusion checker
├── host_header_attacks.py    # host header injection
├── oauth_flow_analyzer.py    # OAuth/OIDC auditor
├── saml_attacker.py          # SAML XML-Signature attacks
├── session_fixation.py       # session fixation
├── auth_bypass_probe.py      # generic auth bypass
└── password_reset_audit.py   # password reset flow audit
```

## Engagement workflow with the toolkit

A typical web pentest, end-to-end with the toolkit:

```bash
# 1. Recon (Part 3) feeds the web target list
python3 -m redshift_toolkit.automation.osint_pipeline --target acme.com \
    --outdir engagements/acme/$(date +%F)/

# 2. Crawl + cookie/CORS/TLS audit (Module 13)
python3 -m redshift_toolkit.web.cors_probe --url https://app.acme.com
python3 -m redshift_toolkit.web.cookie_analyzer --url https://app.acme.com

# 3. OWASP top 10 probe (Module 14)
python3 -m redshift_toolkit.web.sqli_oracle --url 'https://app.acme.com/?id=1'
python3 -m redshift_toolkit.web.ssrf_prober --url https://app.acme.com/api/fetch \
    --param url

# 4. API attack surface (Module 15)
python3 -m redshift_toolkit.web.graphql_introspect --url https://app.acme.com/graphql
python3 -m redshift_toolkit.web.openapi_attacker --spec swagger.json

# 5. Advanced attack surface (Module 16)
python3 -m redshift_toolkit.web.smuggler --url https://app.acme.com
python3 -m redshift_toolkit.web.cache_poison_probe --url https://app.acme.com

# 6. Auth audit (Module 17)
python3 -m redshift_toolkit.web.oauth_flow_analyzer \
    --discovery https://app.acme.com/.well-known/openid-configuration
python3 -m redshift_toolkit.web.session_fixation \
    --login-url https://app.acme.com/login

# 7. Roll into report (Part 3 automation extends to web findings)
python3 -m redshift_toolkit.automation.report_generator \
    --graph engagements/acme/$(date +%F)/graph.json \
    --findings engagements/acme/$(date +%F)/findings.json
```

## Ethics — re-read before you proceed

These tools work. Many of them are written assuming the operator already has authorization. Specifically:

- **Stored XSS payloads** that fetch from your domain are designed for a target you control or have written authorization to test.
- **SQLi/SSRF/XXE oracles** make many requests to identify behavior. On a production system without authorization, this constitutes a CFAA violation in the US, with parallels in most countries.
- **Smuggling, cache poisoning, and host-header attacks** can affect *other* users of the same target. They must only be exercised in a lab or with explicit, written, scope-limited authorization.

Responsible use looks like a written contract with a defined scope, defined timeframe, defined targets, defined out-of-scope assets, an emergency contact, and a remediation expectation. Anything else is unauthorized access.

→ Begin with [Module 13 · Web Fundamentals](13-web-fundamentals.md).
