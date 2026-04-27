# Module 17 · Authentication & Authorization

Authentication answers "who are you?". Authorization answers "what are you allowed to do?". Bugs in both are the highest-impact findings on most engagements: bypass them and you skip every other defense.

This module is the longest in Part 4 because the surface is largest. We'll cover OAuth 2.0/OIDC, SAML, session management, password reset, MFA, and the federation patterns that connect them.

## 1. The taxonomy of authentication mechanisms

| Mechanism | Where credentials live | What you attack |
|---|---|---|
| Form-based login | POST `/login`, sets session cookie | Brute force, default creds, response oracles |
| HTTP Basic / Digest | `Authorization:` header | Brute force, MITM (Basic = base64) |
| API key | Header or query param | Logging, leakage, lack of rotation |
| Bearer token (opaque) | `Authorization: Bearer xxx` | Theft via XSS / log leak |
| JWT | Same, but self-contained | Module 07: alg confusion, weak secret, kid injection |
| OAuth 2.0 | Authorization code → access token | State confusion, redirect manipulation, scope abuse |
| OIDC | OAuth + ID token | Same + ID token validation flaws |
| SAML | Browser-mediated assertion exchange | XML signature wrapping (XSW), assertion replay |
| WebAuthn / FIDO2 | Hardware-backed key | Strong; attack the fallback (often password) |
| MFA — TOTP | App-generated 6-digit code | Brute force the code, time-skew attacks |
| MFA — SMS | Code via text | SIM swap, SS7 interception, social engineering |
| MFA — Push | Notification | "MFA fatigue" bombing |

## 2. OAuth 2.0 / OIDC — the long list of pitfalls

### A 60-second OAuth refresher

The Authorization Code flow:

```
1. App says "log in with provider" → redirects user to:
   https://provider.com/authorize?
     response_type=code
     &client_id=APP_ID
     &redirect_uri=https://app.com/callback
     &scope=openid profile email
     &state=RANDOMNONCE_FROM_APP

2. Provider authenticates user, redirects to:
   https://app.com/callback?code=ABC123&state=RANDOMNONCE_FROM_APP

3. App's backend POSTs to provider with the code:
   POST https://provider.com/token
     grant_type=authorization_code
     code=ABC123
     redirect_uri=https://app.com/callback
     client_id=APP_ID
     client_secret=APP_SECRET (or PKCE verifier for public clients)

4. Provider returns access_token (and id_token for OIDC).
```

Every step has known failure modes.

### OAuth attack: redirect_uri exact match bypass

The provider should validate `redirect_uri` exactly equals the registered one. Common mistakes:

```
Registered:   https://app.com/callback
Attack 1:     https://app.com/callback/../redirect?to=evil.com  (path traversal)
Attack 2:     https://app.com.evil.com/callback                 (suffix-match)
Attack 3:     https://app.com/callback?next=https://evil.com    (open redirect chain)
Attack 4:     https://app.com/callback#evil.com                 (fragment trick)
Attack 5:     https://evil.com/callback                         (substring/regex match)
Attack 6:     https://app.com:1337/callback                     (port not validated)
Attack 7:     https://app.com/callback%2f@evil.com              (URL parsing differential)
```

Win condition: the auth code lands at attacker-controlled URL. With it, attacker exchanges code for token (assuming PKCE not used or no client_secret on public client).

### OAuth attack: state parameter omitted or unverified

`state` is a CSRF token. If the app doesn't generate one, or doesn't verify it on callback, the attacker can:

1. Initiate auth flow themselves, get a code for *their* account
2. Trick victim into visiting `https://app.com/callback?code=ATTACKERS_CODE`
3. Victim's browser exchanges the code; app logs the victim in as the *attacker*
4. Now attacker can read the victim's queries, files uploaded "by them", etc.

### OAuth attack: PKCE missing on public clients

PKCE (Proof Key for Code Exchange) binds the code to a cryptographic verifier. Without it, public clients (mobile apps, SPAs) leak codes that can be redeemed by anyone who intercepts them. Modern guidance is PKCE for all clients.

### OIDC attack: ID token validation

ID tokens are JWTs. Common validation failures:
- Algorithm confusion (Module 07 again — RS256 → HS256)
- Issuer not validated (`iss` claim)
- Audience not validated (`aud` claim)
- `nonce` not bound to flow (replay)
- `sub` accepted from any issuer (federation confusion)
- `email_verified` ignored — attacker registers `victim@target.com` at attacker-controlled IdP

### OIDC attack: Discovery document

OIDC has a `.well-known/openid-configuration` endpoint that describes the IdP. Attacks:
- The endpoint includes URLs to JWKS, authorization, token, userinfo. If the app trusts these without verifying TLS or pinning, MITM rewrites them.
- The `issuer` URL itself is sometimes user-controlled (multi-tenant SaaS) → IdP confusion attack.

Our **`oauth_flow_analyzer.py`** runs the canonical audit:
1. Fetch `.well-known/openid-configuration`
2. Validate every endpoint URL, TLS chain
3. Test redirect_uri with the attack matrix above
4. Test `state` requirement (omit, reuse, mismatch)
5. Test PKCE requirement
6. Decode any ID tokens it can obtain and report `iss`/`aud`/`sub`/`email_verified` configs

## 3. SAML — XML signature wrapping (XSW) and friends

SAML is XML-based, so the attacks are XML-based.

### A SAML response, simplified:

```xml
<samlp:Response>
  <Assertion ID="A1">
    <Subject>victim@target.com</Subject>
    <AttributeStatement>
      <Attribute Name="role">user</Attribute>
    </AttributeStatement>
    <ds:Signature>
      <SignedInfo>
        <Reference URI="#A1">...</Reference>
      </SignedInfo>
      <SignatureValue>...</SignatureValue>
    </ds:Signature>
  </Assertion>
</samlp:Response>
```

The signature covers `<Assertion ID="A1">`. The application must:
1. Verify the signature is valid
2. Verify the **signed element is the one used for authentication**

It's the second step that almost always breaks.

### XSW1: insert a fake assertion alongside the signed one

```xml
<samlp:Response>
  <Assertion>
    <Subject>admin@target.com</Subject>     ← attacker's claim
    <AttributeStatement><Attribute Name="role">admin</Attribute></AttributeStatement>
    <ds:Signature>
      <SignedInfo><Reference URI="#A1"/></SignedInfo>   ← signature still references A1
      <SignatureValue>VALID_SIG_FROM_ORIGINAL</SignatureValue>
    </ds:Signature>
  </Assertion>
  <Assertion ID="A1">                                    ← original signed assertion
    <Subject>victim@target.com</Subject>
    <AttributeStatement><Attribute Name="role">user</Attribute></AttributeStatement>
  </Assertion>
</samlp:Response>
```

If the application reads the FIRST assertion but verifies the signature against the one referenced (A1, the original), the signature is valid and the attacker's claim is used.

### XSW2-XSW8

Eight canonical wrapping variants — different placements of the fake assertion (in the header, as a sibling, nested in `<Object>`, etc.). The right answer for the application is to check XML canonicalization carefully or use SAML libraries that do it correctly.

### Other SAML attacks

- **XML comments in NameID**: Some parsers truncate at comment. `<NameID>admin<!---->@target.com</NameID>` parses as `admin` to one stack and `admin@target.com` to another.
- **XXE in SAML response**: Module 14, parsed XML.
- **Replay**: Capture a valid assertion, replay until `NotOnOrAfter` expires. If the app doesn't check assertion ID uniqueness (one-time-use), this works.
- **Audience confusion**: SAML assertion intended for service A used at service B.

Our **`saml_attacker.py`** generates XSW1-XSW8 variants from a captured SAML response and replays each against a target's ACS endpoint, observing the response.

## 4. Session management failures

### Session fixation

```
1. Attacker visits target.com, gets session cookie SESS=abc.
2. Attacker tricks victim into a URL that sets SESS=abc:
   https://target.com/?sess=abc
   (if the app accepts session cookie via GET param)
   or via XSS / subdomain injection.
3. Victim authenticates with SESS=abc still set.
4. App associates abc with victim's identity.
5. Attacker, also holding SESS=abc, is now authenticated as victim.
```

Defense: rotate session IDs on every privilege change (login, logout, password change). Detection: capture cookie before login, login, see if it changed.

Our **`session_fixation.py`** runs this exact test.

### Insufficient session expiration

Test:
- Get a valid session cookie. 
- Wait 24h, send a request with the cookie. Still authenticated?
- Logout. Send a request with the cookie. Still authenticated?
- Change password. Send a request with the old cookie. Still authenticated?

All three should return 401/403. Often only the first does.

### Concurrent session control

Most apps allow N concurrent sessions per user — sometimes unlimited. Test by:
- Logging in twice from different devices.
- Logging in N+1 times. Observe whether old sessions are killed.
- Logout from one — does it kill all sessions, or just one?

## 5. Password reset flaws

The single highest-impact bug class outside of full RCE. Patterns:

| Flaw | Test |
|---|---|
| Predictable token | Generate 5 reset tokens for accounts you control. Are they sequential? Time-based? Insufficient entropy? |
| Token leak via Referer | Reset link contains token. User clicks an external link from the reset page → Referer leaks token to third party. |
| Token in URL logged | Server access logs / proxy logs / CDN logs all retain the URL → token is in many places. |
| Email change no re-auth | App lets user change email without entering password. Combined with weak session = full takeover. |
| Reset email host header injection | Module 16 — Host header controls reset URL host. |
| Username enumeration on reset | Reset endpoint replies differently for valid vs invalid emails. |
| No token expiration | Reset tokens valid forever. |
| Token reuse | Token usable multiple times. |
| Race: token still valid post-use | Use token once successfully, immediately use again before invalidation propagates. |
| Token validates but doesn't bind | Token valid for any password change request (cross-user). |

Our **`password_reset_audit.py`** runs this matrix.

## 6. MFA bypasses

| Bypass | Mechanism |
|---|---|
| MFA flow can be skipped | Login endpoint returns auth cookie before MFA step; attacker uses it directly. |
| Backup codes never expire | Old leaked backup codes still work years later. |
| Bypass via password-reset | Reset password flow doesn't require MFA → reset to bypass. |
| Bypass via legacy API | Old API version (`/api/v1/login`) doesn't enforce MFA; new one does. |
| Bypass via SSO failure | App accepts a non-MFA-protected SSO when MFA-protected one fails. |
| Brute force code | TOTP is 6 digits. Without rate limiting, 10^6 attempts. With sliding window of 30s, ~10^7. |
| MFA bombing | Push MFA → spam victim with notifications until they accept. |
| Session reuse pre-MFA | Cookie issued before MFA step is the same as post-MFA → submit cookie alone. |

Our **`auth_bypass_probe.py`** covers many of these patterns.

## 7. Authorization patterns

Beyond IDOR (Module 14), authorization architecture matters:

### RBAC (Role-Based Access Control)

User has roles, roles have permissions. Common bugs:
- Role assignment endpoint accepts arbitrary role name (mass assignment)
- Role hierarchy not enforced (admin > moderator > user — but check implementation)
- Role check at controller level, not service level → direct service calls bypass

### ABAC (Attribute-Based Access Control)

User has attributes (department, clearance, time-of-day). Permissions are policies. Common bugs:
- Time-of-day check uses client clock
- Department attribute mass-assignable
- Policy engine rejects on missing attribute → set attribute to null to bypass

### ReBAC (Relationship-Based Access Control)

User can access resource if there's a graph edge to it. (Modern: Google Zanzibar, Auth0 FGA.) Common bugs:
- Edge insertion via mass assignment
- Stale edges not removed (former employee retains access)

## 8. The 90-minute auth audit

```bash
# 1. Discover auth surface
python3 -m redshift_toolkit.web.openapi_attacker --spec spec.json \
    --enumerate-auth

# 2. OAuth/OIDC config audit
python3 -m redshift_toolkit.web.oauth_flow_analyzer \
    --discovery https://target.com/.well-known/openid-configuration

# 3. SAML attacks (if SAML present)
python3 -m redshift_toolkit.web.saml_attacker \
    --captured-response captured.xml \
    --acs-url https://target.com/saml/acs

# 4. Session fixation
python3 -m redshift_toolkit.web.session_fixation \
    --login-url https://target.com/login \
    --user testuser --pass testpass

# 5. Password reset audit
python3 -m redshift_toolkit.web.password_reset_audit \
    --reset-url https://target.com/forgot-password \
    --emails test1@target.com,test2@target.com

# 6. Generic auth bypass patterns
python3 -m redshift_toolkit.web.auth_bypass_probe \
    --base https://target.com \
    --protected /admin/users \
    --token "$TOKEN"
```

## 9. Industry-specific framings

### Financial services

**Wire fraud via OAuth state confusion** is a documented attack pattern. Linking attacker-controlled accounts to victim banking flows. SAML signature wrapping in agent SSO portals is a known finding category.

### Healthcare

**SAML XSW** in clinician portals (Epic, Cerner integrations) — frequent finding category, frequently downplayed by vendors. Password reset flaws are HIPAA-critical because they expose PHI.

### Government

**SSO federation between agencies** (login.gov, ID.me, GSA HSPD-12). Misconfigurations here can cross agency boundaries — high-impact, well-rewarded on Hack the Pentagon.

### SaaS / Enterprise

**Multi-tenant identity boundaries.** SCIM provisioning misconfigurations, JIT user creation leaving stale accounts, OIDC `iss` validation across tenants. Lots of bug bounty value.

## 10. Recap

You should now be able to:

- Audit OAuth 2.0 / OIDC flows for redirect, state, PKCE, ID-token issues
- Generate XSW1-XSW8 SAML signature-wrapping variants
- Detect session fixation, insufficient expiration, predictable IDs
- Walk a password reset flow looking for the 10 known patterns
- Identify common MFA bypasses
- Run a 90-minute auth audit end-to-end with the toolkit

Tools shipped with this module:

| Script | Purpose |
|---|---|
| `redshift_toolkit.web.oauth_flow_analyzer` | OAuth 2.0 / OIDC audit |
| `redshift_toolkit.web.saml_attacker` | SAML XSW1-XSW8 variant generator + ACS replayer |
| `redshift_toolkit.web.session_fixation` | Session fixation tester |
| `redshift_toolkit.web.auth_bypass_probe` | Generic auth bypass patterns (header tricks, path tricks, MFA skip) |
| `redshift_toolkit.web.password_reset_audit` | Password reset flow audit |
| `scripts/part-04/17-auth-authz/auth_runner.py` | Module 17 orchestrator |

→ Next: **Part 5 · Network & Infrastructure Pentesting** *(coming in the next ship — Modules 18-21: AD attacks, Kerberos exploitation, network pivoting, lateral movement)*.
