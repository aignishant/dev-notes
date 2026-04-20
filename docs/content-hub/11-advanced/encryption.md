# Encryption

## The Three Layers Where Encryption Shows Up

### 1. `definition.yaml` `type: password`

Parameters declared as `password` are **encrypted at rest** by the platform:

```yaml
parameters:
  - name: Api Key
    type: password
    is_mandatory: true
```

- Stored encrypted in the platform's secrets store
- Masked (`*****`) in UI + logs
- Never returned via API (even by admins — re-entry required)
- Passed in plaintext only to the running integration's memory

**Never** use `type: string` for anything sensitive.

### 2. Platform Context Store

`context.set(siemplify, "token", value)` — the platform persists context encrypted. You don't manage keys; the platform does.

### 3. `TIPCommon.encryption` for Custom Cases

For data you need to encrypt yourself (e.g., a blob passed between components):

```python
from TIPCommon.encryption import encrypt, decrypt

cipher_text = encrypt(plaintext, key=self.params.encryption_key)
plain = decrypt(cipher_text, key=self.params.encryption_key)
```

Rare — most of the time the platform's built-in encryption is enough.

## What You Never Do

| Don't | Because |
|---|---|
| Hardcode secrets in `core/*.py` | Committed to Git; forever readable |
| Log secrets at DEBUG | Logs are persistent; may be ingested to SIEM |
| Use `type: string` for API keys | Plaintext at rest; major CVE-worthy |
| `print_value=True` on password param | Logs the value on extract |
| Commit `.env` files | Must be `.gitignore`d everywhere |
| Store secrets in JSON result | Propagates to playbook steps + widgets |

## Secrets in Context — Platform Handles It

When you do:

```python
context.set(siemplify, "oauth_access_token", "eyJhbGc...")
```

You're **not** exposing the token. The platform encrypts context at rest. But be mindful: context is accessible to the integration itself, and anyone who can read the integration's execution logs can see values logged during `context.set` if you logged the value.

## Secrets in Transit

The integration talks to third-party APIs over HTTPS — enforce TLS:

```python
self.session = requests.Session()
self.session.verify = self.params.verify_ssl   # True by default
```

**`Verify SSL` should default to `True`** in every integration. Only offer `False` as an option for lab/testing setups; real customers should never disable verification.

## Key Rotation

For integrations with persistent tokens:

- Customer rotates API key in third-party UI
- Customer updates the `Api Key` parameter in SOAR
- Your code sees the new value on next extraction — automatically

For OAuth refresh tokens: if the refresh token is revoked (user password change, etc.), your code gets a `401` on refresh → clear the cached token + log clearly that re-auth is needed.

## Handling Revoked Credentials Gracefully

```python
def _request_with_retry(self, ...):
    try:
        return self._do_request(...)
    except HTTPError as e:
        if e.response.status_code == 401:
            # Try once more with fresh token
            self._auth.invalidate()
            try:
                return self._do_request(...)
            except HTTPError as e2:
                if e2.response.status_code == 401:
                    raise InvalidCredentialsError(
                        "API credentials invalid. Update the integration config."
                    ) from e2
        raise
```

## Encryption Q&A Quick Hits

- **Customer asks: "where is my API key stored?"** → *"Encrypted at rest in SOAR's secrets store; masked in UI; never returned via API — re-entry required on changes."*
- **Can I read a password param's current value via the SDK?** → No. Only writes allowed via admin UI; no read endpoint.
- **Can I put a certificate bundle in a param?** → Yes, `type: string` or `content_url` depending on size; but if sensitive, encrypt it yourself with `TIPCommon.encryption` and store only the ciphertext in the param.
- **Should I implement my own encryption for tokens in context?** → No. Platform encryption is enough. Double-encryption complicates rotation and adds no real safety.

## Next

→ **[Async Connectors](async-connectors.md)**
