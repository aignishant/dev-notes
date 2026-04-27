# Module 13 · Web Fundamentals for Attackers

Most web app pentest reports today still find vulnerabilities that are essentially "the developer didn't understand HTTP." So before we look at injection, smuggling, or auth confusion, we need to establish a wire-level mental model: what *exactly* the browser sends, what the server sees, what the proxy in between does to it, and where each component disagrees.

If you can read a `tcpdump` of an HTTP/1.1 conversation byte-by-byte, you'll find smuggling bugs that no scanner catches. If you can sketch the HTTP/2 frame structure on a whiteboard, you'll spot CONTINUATION-frame attacks before they make CVE lists. That's the goal of this module.

## 1. The HTTP request — wire format, bottom up

A complete HTTP/1.1 GET, on the wire (the `\r\n` is the literal CRLF separator):

```
GET /products?id=42 HTTP/1.1\r\n
Host: shop.example.com\r\n
User-Agent: Mozilla/5.0\r\n
Accept: text/html\r\n
Cookie: session=eyJ1c2VyX2lkIjoxN30; theme=dark\r\n
\r\n
```

Five things to internalize:

1. **The request line** has three space-separated tokens: METHOD, request-target, version. Whitespace between them is *significant* — Apache famously parsed `GET\t/admin\tHTTP/1.1` differently from `GET /admin HTTP/1.1`, and that exact bug shipped in three different web stacks (CVE-2007-0450, CVE-2015-3185, CVE-2020-1934).

2. **Headers are case-insensitive** by spec, but case-preserving by every CDN and most proxies. `Host:` and `host:` mean the same thing to the spec; some servers normalize, some don't, and the disagreement is exploitable (HTTP/1 to HTTP/2 desync attacks).

3. **The blank line `\r\n\r\n`** terminates the header block. Header order matters. Duplicate headers are sometimes concatenated with commas, sometimes overwrite each other, sometimes both depending on the field — this is the foundation of HTTP request smuggling (Module 16).

4. **The request body** follows the headers. Its length is determined by either:
   - `Content-Length: N` — read exactly N bytes after the blank line
   - `Transfer-Encoding: chunked` — read until a zero-length chunk
   
   When *both* are present, frontend and backend can disagree. That's literally request smuggling.

5. **The request-target** can be:
   - `origin-form`: `/path?query` (the normal one)
   - `absolute-form`: `http://shop.example.com/path` (used in proxy requests)
   - `authority-form`: `host:port` (used for CONNECT)
   - `asterisk-form`: `*` (used for OPTIONS)
   
   Most servers accept all four — but normalization differs. CVE-2022-44877 (CWP) and many others lived in this gap.

### Building HTTP requests by hand

Because every web tool eventually lies to you about exactly what it sent, you should be able to construct an HTTP request from first principles. From a Python REPL:

```python
import socket

req = (
    b"GET /products?id=42 HTTP/1.1\r\n"
    b"Host: shop.example.com\r\n"
    b"User-Agent: rs-probe/1.0\r\n"
    b"Connection: close\r\n"
    b"\r\n"
)

s = socket.create_connection(("shop.example.com", 80), timeout=5)
s.sendall(req)
data = b""
while True:
    chunk = s.recv(4096)
    if not chunk:
        break
    data += chunk
print(data.decode("latin-1"))
```

Our **`http_client.py`** in the toolkit wraps this pattern with timeouts, TLS, redirect following, and chunked-decode handling — but always falls back to raw bytes when you ask it to. That escape hatch matters.

## 2. The HTTP response

```
HTTP/1.1 200 OK\r\n
Server: nginx/1.20.1\r\n
Date: Sat, 25 Apr 2026 12:34:56 GMT\r\n
Content-Type: text/html; charset=utf-8\r\n
Content-Length: 1431\r\n
Set-Cookie: session=abc123; Secure; HttpOnly; SameSite=Lax\r\n
\r\n
<!doctype html>...
```

**Status codes you must recognize as an attacker** (not a complete list — the specifically interesting ones):

| Code | Meaning | Attacker reaction |
|---|---|---|
| `200` | OK | Normal response — content matters |
| `204` | No Content | Often returned by silent failures; check Set-Cookie |
| `301/302/303/307/308` | Redirect | Open redirect candidate; check Location header |
| `400` | Bad Request | Often leaks parser internals — read the body |
| `401` | Unauthorized | Auth header rejected; try variations |
| `403` | Forbidden | Authz failure; try header/path tricks (X-Original-URL, /admin/./, /admin%2e/, etc.) |
| `404` | Not Found | Sometimes leaks server type; sometimes lies (404 vs 401 disclosure) |
| `405` | Method Not Allowed | Try other verbs — `Allow:` header tells you which |
| `500` | Server Error | Stack trace? Request body too large? Probe further |
| `502/504` | Bad Gateway / Gateway Timeout | Backend dead — your last request might have caused it |
| `503` | Service Unavailable | WAF rate limit? Backoff and rotate IPs |
| `999` | (LinkedIn) "I think you're a bot" — non-standard rate-limit signal |

### Header-driven information disclosure

These response headers are the lowest-hanging fruit on every web pentest:

| Header | What it leaks |
|---|---|
| `Server:` | Web server + version (often disabled, but not always) |
| `X-Powered-By:` | Framework + version (PHP, ASP.NET, Express, etc.) |
| `X-AspNet-Version:` | Specific .NET runtime |
| `X-Drupal-Cache:`, `X-Drupal-Dynamic-Cache:` | Confirms Drupal |
| `X-Generator:` | Same — often Drupal, MediaWiki, Joomla |
| `Via:` | Reverse proxy chain (Squid, Cloudflare, etc.) |
| `X-Backend-Server:` | Specific backend hostname (huge leak — often shows AWS internal hostnames) |
| `Set-Cookie:` (cookie name) | Often reveals framework: `PHPSESSID`, `JSESSIONID`, `ASP.NET_SessionId`, `connect.sid` (Express), `_csrf` patterns |
| `Strict-Transport-Security:` | Absent → MITM downgrade attacks viable |
| `Content-Security-Policy:` | Read it; the gaps are XSS opportunities |
| `X-Frame-Options:` | Absent → clickjacking |

Our **`http_client.py`** dumps all of these in a "fingerprint" mode, and **`cookie_analyzer.py`** specifically audits Set-Cookie security.

## 3. HTTP/2 — frame-level mental model

HTTP/2 is binary. A connection is divided into **streams**, each carrying **frames**. The frame types you'll see most:

| Frame | Hex | Carries |
|---|---|---|
| `DATA` | `0x00` | Request/response body |
| `HEADERS` | `0x01` | Compressed header block |
| `PRIORITY` | `0x02` | Stream priority |
| `RST_STREAM` | `0x03` | Stream cancel |
| `SETTINGS` | `0x04` | Connection settings |
| `PING` | `0x06` | Keepalive |
| `GOAWAY` | `0x07` | Connection close |
| `CONTINUATION` | `0x09` | Continued HEADERS |

A request:
1. Open new stream (odd ID for client-initiated)
2. Send HEADERS frame (HPACK-compressed pseudo-headers `:method`, `:path`, `:authority`, `:scheme`)
3. Send DATA frames if body
4. Server replies on same stream

Why this matters for us:

- **Request smuggling in HTTP/2 → HTTP/1.1 downgrade.** Frontend speaks H2, backend speaks H1. The CL/TE-chunked tricks come back differently because H2 doesn't have those headers. James Kettle's "HTTP/2: The Sequel is Always Worse" (2021) is mandatory reading.
- **CONTINUATION flood (CVE-2024-27316).** Sending unbounded CONTINUATION frames before the END_HEADERS bit DoSes most HTTP/2 stacks. Trivial to write, hard for vendors to fix.
- **Rapid reset attack (CVE-2023-44487).** Open and immediately reset streams faster than the server cleans them up. 200M+ RPS recorded against Cloudflare.
- **HPACK confusion.** Two streams can encode the same `:authority` differently — some validators ignore HPACK-decoded values.

Our **`http2_client.py`** speaks H2 at the frame level — useful for testing all of the above without `nghttp2` or `curl --http2`.

## 4. The browser security model

This is the trust model every web app inherits, whether it knows it or not.

### Same-Origin Policy (SOP)

Two URLs are "same origin" iff their **scheme + hostname + port** are exactly equal. Different origins:

| URL A | URL B | Same origin? |
|---|---|---|
| `https://app.example.com/x` | `https://app.example.com/y` | ✅ |
| `https://app.example.com` | `http://app.example.com` | ❌ scheme differs |
| `https://app.example.com` | `https://app.example.com:8443` | ❌ port differs |
| `https://app.example.com` | `https://api.example.com` | ❌ host differs |
| `https://app.example.com` | `https://app.example.com.evil.com` | ❌ host differs (don't be fooled by subdomain prefix) |

SOP forbids JavaScript on origin A from *reading* the response body of origin B. It does NOT forbid:
- Sending requests cross-origin (CSRF lives here)
- Loading scripts cross-origin (XSSI, supply-chain attacks live here)
- Loading images cross-origin (timing oracles, CSP-bypass leaks)

### CORS — relaxing SOP, breaking it badly

CORS lets a server *opt in* to cross-origin reads. The server returns:

```
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Credentials: true
```

Two famous misconfigurations:

1. **Origin reflection with credentials.** Server reflects whatever the request's `Origin:` header is, and also sets `Allow-Credentials: true`. Means *any* attacker page can read responses including the user's cookies. Fatal.
2. **Wildcard with null origin.** `Allow-Origin: null` is reachable from sandboxed iframes, data: URLs, and certain redirect chains.

Our **`cors_probe.py`** tests for both — and several variants — by sending different `Origin:` values and observing the reflected response.

### Cookies

Cookie semantics, in attacker order of importance:

| Attribute | What it does | When it bites |
|---|---|---|
| `Secure` | Only sent over HTTPS | Without it: cookie leaks on HTTP (active MITM, or a single HTTP fetch) |
| `HttpOnly` | Not readable from JS | Without it: any XSS = full session theft |
| `SameSite=Strict` | Never sent on cross-site requests | Without it: CSRF, GET-based state changes |
| `SameSite=Lax` | Sent on top-level GET navigations | Cross-site POSTs blocked but GET-based actions still vulnerable |
| `SameSite=None; Secure` | Sent everywhere if HTTPS | Maximum cross-site risk; only valid choice for SSO/embedded contexts |
| `Domain=.example.com` | Shared with subdomains | Subdomain XSS = full domain compromise |
| `Path=/admin` | Restricted by path | Bypassed via XSS on `/` or path-traversal in the URL |
| `Max-Age` / `Expires` | Lifetime | Sometimes excessive; tokens that never expire |
| `__Host-` prefix | Forces Secure + Path=/ + no Domain | Strong; absent is a yellow flag |
| `__Secure-` prefix | Forces Secure | Weaker than `__Host-` but still useful |

Our **`cookie_analyzer.py`** scores every cookie in a response against this matrix and outputs JSON findings.

### TLS — what changes for attackers

By 2026 we assume TLS 1.2+ with strong ciphers. The remaining quirks worth knowing:

- **HSTS** (`Strict-Transport-Security`) tells the browser to never speak HTTP again to this host. Without it, every fresh tab is a downgrade opportunity. With `includeSubDomains` and `preload`, it's strong.
- **Certificate Transparency** logs every cert issued for a domain — and you've already used `cert_harvester.py` (Part 3) to mine those for hidden subdomains.
- **Renegotiation attacks** are dead in TLS 1.3, but plenty of 2026 production traffic is still 1.2.
- **TLS fingerprinting (JA3, JA4)** — your client's cipher list and extension order is a fingerprint. WAFs use it to detect non-browser traffic. If your scanner uses Python `requests` with default `urllib3`, every WAF on Earth has signatures for it.

Our **`tls_quirks.py`** probes for HSTS misconfiguration, weak ciphers, and unusual ALPN behavior.

## 5. The session lifecycle

Modern web apps maintain user state through one or more of:

| Mechanism | Where it lives | Attacker concern |
|---|---|---|
| Session cookie | Set-Cookie + browser cookie jar | Theft via XSS / network / CSRF replay |
| JWT in cookie | Same as above, but self-contained | Algorithm confusion (Module 07) |
| JWT in localStorage | Browser storage, accessed by JS | XSS = trivial theft, no HttpOnly protection |
| Bearer token in header | Authorization: Bearer xxx | Often logged in proxy access logs (huge leak) |
| OAuth access token | localStorage or in-memory | Bound to scope and audience — often misvalidated |
| SAML assertion | POST body to ACS endpoint | Signature wrapping, XSW attacks |

**The full lifecycle of a session** — useful as a checklist when auditing:

1. **Establishment** — login form, OAuth flow, SAML SSO, session cookie issued
2. **Renewal** — refresh token, sliding expiration, re-auth
3. **Privilege change** — role assumption, "view as user X" features (huge IDOR territory)
4. **Termination** — logout endpoint, session revocation, token blacklist
5. **Device binding** — was this session anchored to a device fingerprint?

Each step has well-known failure modes. Module 17 walks through them all with tooling.

## 6. The HTTP attack surface map

When you're handed a new web app and asked to "find bugs," this is the surface:

```
                         ┌────────────────────────┐
                         │   Static content        │
                         │   (JS, CSS, images)     │
                         │   ▶ JS source mining    │
                         │   ▶ map files leak src  │
                         └────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────────┐
        │   Authenticated API surface                        │
        │   ┌───────────┐  ┌───────────┐  ┌───────────┐      │
        │   │ REST/JSON │  │ GraphQL   │  │ WebSocket │      │
        │   └───────────┘  └───────────┘  └───────────┘      │
        │     ▶ IDOR        ▶ Introspect   ▶ Auth bypass     │
        │     ▶ MassAssign  ▶ Batch attack ▶ DoS             │
        │     ▶ Rate limits                                  │
        └───────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────────┐
        │   Server-side                                      │
        │   ▶ SQLi / NoSQLi      ▶ SSRF                      │
        │   ▶ XXE                ▶ XSLT                      │
        │   ▶ Command injection  ▶ Path traversal            │
        │   ▶ Deserialization    ▶ Template injection (SSTI) │
        │   ▶ File upload → RCE                              │
        └───────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────────┐
        │   Infrastructure                                   │
        │   ▶ Misconfigured CDN     ▶ Cache poisoning        │
        │   ▶ HTTP smuggling        ▶ Cache deception        │
        │   ▶ Host header attacks   ▶ Subdomain takeover     │
        └───────────────────────────────────────────────────┘
```

Every section maps onto a module:
- 14 (Top 10) — server-side injection + IDOR
- 15 (APIs) — middle layer
- 16 (Advanced) — infrastructure
- 17 (AuthN/Z) — wraps around all of the above

## 7. Industry-specific framing

### Financial services

A typical retail-banking web app has a **public marketing tier**, an **authenticated customer portal**, an **agent/teller app**, and **admin/back-office**. The agent app and back-office almost always live on a separate domain (e.g. `agent.bank.com`), and the auth model is often SAML SSO via Okta or Ping. Authorization checks at the API layer are frequently weaker on the agent side, on the assumption that "only employees can hit it." That assumption breaks the moment a customer-portal SSRF can reach `agent.internal.bank.com`.

Specific things to look for:
- Account number IDOR on transfer/transaction endpoints
- Statement PDF download endpoints (often unauthorized)
- Beneficiary edit flows (race conditions during change windows)
- Wire-transfer 2FA bypass (was the OTP validation stateful? Check for replays)

### Healthcare

US hospital systems operate **patient portals** (MyChart, Epic, etc.), **provider portals** (clinician-facing), **payer portals** (insurance billing), and **HL7/FHIR APIs** that often interconnect. The patient portal is the customer-facing tier; vulnerabilities there directly impact PHI under HIPAA.

Specific things to look for:
- IDOR on `/api/patient/{id}/records` (the canonical mistake)
- Mass assignment on `/api/patient/{id}` letting you set provider, insurance, etc.
- File upload on the `/messages` feature → server-side path traversal
- Print-friendly view URLs leaking data without auth
- Test environments mirroring production data

### Government / Defense

Federal agencies typically run **public-facing portals** (login.gov, DoD's milConnect), **agency-specific apps** (USAJOBS, IRS Free File), and **authenticated cleared environments**. The first two are FedRAMP Moderate or High; the last is not directly reachable from the internet but increasingly has limited public-facing components.

Look for:
- Authentication bypass via crafted SAML assertions (Module 17)
- IDOR on FOIA request status pages
- Subdomain takeover on legacy `.gov` subdomains (long history of these)
- Cache deception on identity proofing flows

## 8. Lab — set up a punching bag

Before the next module, set up at least one of:

| App | Why | URL |
|---|---|---|
| **DVWA** | Classic SQLi/XSS/CSRF playground | github.com/digininja/DVWA |
| **OWASP Juice Shop** | Modern SPA + REST + GraphQL | github.com/juice-shop/juice-shop |
| **bWAPP** | 100+ web vulnerabilities | itsecgames.com |
| **WebGoat** | OWASP-curated, structured lessons | github.com/WebGoat/WebGoat |
| **PortSwigger Web Security Academy** | Free labs from the Burp authors — best in class | portswigger.net/web-security |
| **HackTheBox / TryHackMe** | Real targets (paid tiers) | hackthebox.com / tryhackme.com |

Run the toolkit's tools against these. The PortSwigger Academy is the gold standard for skill development.

## 9. Recap

You should now be able to:

- Construct an HTTP/1.1 request from raw bytes and explain every line
- Sketch the HTTP/2 frame layer well enough to discuss CONTINUATION-flood and Rapid Reset
- Distinguish same-origin from same-site, and explain the difference between SameSite=Lax and Strict
- Read a Set-Cookie header and identify all five security flags
- Map an unknown web target's attack surface

Tooling shipped with this module:

| Script | Purpose |
|---|---|
| `redshift_toolkit.web.http_client` | Raw HTTP/1.1 client with optional TLS, redirect, chunked decoding |
| `redshift_toolkit.web.http2_client` | HTTP/2 frame-level client (HEADERS, DATA, CONTINUATION, RST_STREAM) |
| `redshift_toolkit.web.cors_probe` | CORS misconfiguration matrix |
| `redshift_toolkit.web.cookie_analyzer` | Cookie security flag audit |
| `redshift_toolkit.web.tls_quirks` | HSTS, weak cipher, ALPN audit |
| `scripts/part-04/13-web-fundamentals/web_recon_runner.py` | Module 13 orchestrator: fingerprint + CORS + cookies + TLS in one call |

→ Next: [Module 14 · OWASP Top 10 Deep Dives](14-owasp-deep-dives.md).
