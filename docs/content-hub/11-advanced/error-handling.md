# Error Handling Patterns

## The Core Principle

> *"Every integration fails in predictable ways. Code for the failure modes as first-class outcomes, not exceptions to handle at the end."*

## The Exception Hierarchy Pattern

Define a small hierarchy in `core/exceptions.py` (or inside the API client module):

```python
class MyProductError(Exception):
    """Base for all MyProduct client errors."""

class MyProductAuthError(MyProductError): ...
class MyProductInvalidAPIKeyError(MyProductAuthError): ...

class MyProductClientError(MyProductError):
    """4xx errors except auth."""

class MyProductRateLimitError(MyProductError): ...
class MyProductNotFoundError(MyProductError): ...

class MyProductServerError(MyProductError):
    """5xx — retry-worthy."""

class MyProductTimeoutError(MyProductError): ...
```

This lets your actions catch the **most specific** exception for each case and produce a targeted user message.

## Mapping HTTP Errors to Exceptions

```python
def _request(self, method, path, **kw):
    try:
        r = self.session.request(method, self.base_url + path, **kw)
    except requests.Timeout as e:
        raise MyProductTimeoutError(f"Request timed out: {path}") from e
    except requests.ConnectionError as e:
        raise MyProductError(f"Connection error: {e}") from e

    if r.status_code == 401:
        raise MyProductInvalidAPIKeyError("Invalid or expired API key")
    if r.status_code == 403:
        raise MyProductAuthError("Insufficient permissions")
    if r.status_code == 404:
        raise MyProductNotFoundError(f"Not found: {path}")
    if r.status_code == 429:
        retry_after = int(r.headers.get("Retry-After", "60"))
        raise MyProductRateLimitError(f"Rate limited, retry after {retry_after}s")
    if 400 <= r.status_code < 500:
        raise MyProductClientError(f"{r.status_code}: {r.text[:200]}")
    if 500 <= r.status_code < 600:
        raise MyProductServerError(f"{r.status_code}: {r.text[:200]}")

    return r.json()
```

Log the full status + truncated body, but never the full request body (may contain secrets).

## Action-Level Error Handling

In an action's `_perform_action`, catch specific first:

```python
def _perform_action_on_entity(self, entity):
    try:
        report = self._api_client.check_ip(entity.identifier)
    except MyProductNotFoundError:
        self._missing_entities.append(entity.identifier)
        return
    except MyProductRateLimitError as e:
        self._limit_entities.append(entity.identifier)
        self._logger.warning(f"Rate-limited on {entity.identifier}: {e}")
        return
    except MyProductAuthError as e:
        # Fatal — no point continuing; re-raise to kill the action
        raise
    except MyProductError as e:
        self._failed_entities.append(entity.identifier)
        self._logger.error(f"Failed on {entity.identifier}: {e}")
        return

    # Happy path
    self._enriched_entities.append(entity)
```

**Four buckets** — as discussed in Section 3: enriched, limit, failed, missing. Per-entity iteration never aborts the whole action for one bad entity.

## Retry with Backoff

For transient errors (rate limit, 5xx, timeouts):

```python
import time
import random

def _with_retry(self, func, *args, attempts=3, **kwargs):
    for attempt in range(attempts):
        try:
            return func(*args, **kwargs)
        except (MyProductRateLimitError, MyProductServerError, MyProductTimeoutError) as e:
            if attempt == attempts - 1:
                raise
            delay = 2 ** attempt + random.uniform(0, 1)   # 1-2, 2-3, 4-5 seconds
            self._logger.info(f"Retry {attempt + 1}/{attempts} after {delay:.1f}s due to {type(e).__name__}")
            time.sleep(delay)
```

Exponential backoff with jitter — prevents thundering-herd when multiple connectors / actions hit the same rate limit simultaneously.

## What Retry Is NOT For

- **Auth errors** — retry won't help; re-raise immediately
- **`Not Found`** — the entity isn't there, retrying won't find it
- **Validation errors** (400) — input is wrong; retry won't fix
- **Permission errors** (403) — won't change on retry

Retry only for **genuinely transient** failures: rate limit, 5xx, timeout, connection error.

## Timeout Awareness

Check the platform deadline inside retry loops:

```python
from TIPCommon.smp_time import is_approaching_action_timeout

def _with_retry(self, func, *args, **kwargs):
    for attempt in range(3):
        if is_approaching_action_timeout(self.soar_action):
            raise TimeoutError("Platform deadline approaching, aborting retry")
        try:
            return func(*args, **kwargs)
        except (RetryableError,):
            time.sleep(2 ** attempt)
```

Don't retry past the platform's cutoff — partial success beats action-killed-by-timeout.

## Output Messages

Good output message example:

```
Successfully enriched 8 out of 10 entities in MyProduct.

Enriched:
  8.8.8.8, 1.1.1.1, ...
Missing (not found):
  9.9.9.9, 2.2.2.2
Failed:
  3.3.3.3 — Connection timeout
Rate-limited (retry next cycle):
  4.4.4.4
```

Bad output message example:

```
Error: NoneType object has no attribute 'json'
```

Users see output messages in the playbook step output. Write them for an analyst at 2 AM reading the playbook history.

## Logging Best Practices

| Level | When |
|---|---|
| `DEBUG` | Detailed flow, request bodies (sanitized) |
| `INFO` | Phase markers, happy path events |
| `WARNING` | Recoverable issues (rate limit, missing optional field) |
| `ERROR` | Per-entity failures that don't kill the action |
| `EXCEPTION` | Unrecoverable — include stack trace |

Never log:

- API keys, tokens, passwords
- Full request bodies that may contain secrets
- PII (user emails, real names) beyond what's necessary

Always log:

- Action/connector start + end
- External entity identifiers (IPs, hashes)
- HTTP status codes
- Retry attempts
- Context size before/after save

## The Try-Except-Finally Sandwich

For connectors, use a finally clause to save state even on failure:

```python
try:
    self.get_alerts()
    self.process_alerts()
except Exception as e:
    self._logger.exception(f"Connector run failed: {e}")
    # Don't re-raise — we want state saved
finally:
    if not self.is_test_run:
        self._save_context_data()   # save progress even on failure
```

A crashed connector should not lose its last-success-timestamp — otherwise the next run reprocesses an entire backfill window.

## Error-as-Value Philosophy (When Reasonable)

Some functions prefer returning `Result[T, Error]` over throwing:

```python
from dataclasses import dataclass

@dataclass
class ApiResult:
    success: bool
    data: dict | None = None
    error: str | None = None
    retryable: bool = False

def check_ip(ip) -> ApiResult:
    try:
        return ApiResult(success=True, data=self._api.get(ip))
    except RateLimitError as e:
        return ApiResult(success=False, error=str(e), retryable=True)
```

Callers handle via data not exception-handling. Makes flow more explicit. TIPCommon doesn't mandate this style, but some integrations use it for core paths.

## Next

→ **[Rate Limiting & Pagination](rate-limiting.md)**
