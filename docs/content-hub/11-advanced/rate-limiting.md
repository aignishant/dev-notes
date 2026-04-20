# Rate Limiting & Pagination

## Rate Limiting — Three Layers

### Layer 1 — Respect the `Retry-After` Header

Standards-compliant APIs send `Retry-After: <seconds>` on 429:

```python
if r.status_code == 429:
    retry_after = int(r.headers.get("Retry-After", "60"))
    raise RateLimitError(retry_after=retry_after)
```

The caller sleeps for that duration before retrying.

### Layer 2 — Proactive Rate Limiting (Token Bucket)

For APIs with published limits (e.g., "1000 req/min"):

```python
import time
from collections import deque

class TokenBucket:
    def __init__(self, capacity: int, refill_per_sec: float):
        self.capacity = capacity
        self.refill = refill_per_sec
        self.tokens = capacity
        self.last_refill = time.time()

    def acquire(self, count: int = 1) -> None:
        while self.tokens < count:
            now = time.time()
            self.tokens = min(self.capacity, self.tokens + (now - self.last_refill) * self.refill)
            self.last_refill = now
            if self.tokens < count:
                time.sleep((count - self.tokens) / self.refill)
        self.tokens -= count
```

Use:

```python
bucket = TokenBucket(capacity=1000, refill_per_sec=1000/60)

def check_ip(ip):
    bucket.acquire()
    return self._api.get(f"/check?ip={ip}")
```

This prevents hitting 429 in the first place.

### Layer 3 — Global Concurrency Cap

For async, use a semaphore (see Section 11's [Async Connectors](async-connectors.md)):

```python
sem = asyncio.Semaphore(10)  # never more than 10 concurrent

async def fetch_one(id):
    async with sem:
        return await self.client.get_alert(id)
```

## Exponential Backoff with Jitter

When a retry is warranted, randomize the delay:

```python
import random

def backoff(attempt: int, base: float = 1.0, max_delay: float = 60) -> float:
    delay = min(max_delay, base * (2 ** attempt))
    jitter = random.uniform(0, delay * 0.3)
    return delay + jitter
```

**Without jitter:** every client with the same backoff retries at the exact same time — thundering herd.

**With jitter:** retries smear across a window, preserving the API's ability to recover.

## Pagination Patterns

### Offset-Based

```
GET /alerts?offset=0&limit=100
GET /alerts?offset=100&limit=100
```

```python
def fetch_all(self):
    offset = 0
    while True:
        page = self._api.get(f"/alerts?offset={offset}&limit=100")
        if not page:
            break
        yield from page
        offset += len(page)
```

**Pro:** Simple, stateless.
**Con:** Inconsistent if the dataset changes during iteration — rows may be skipped or duplicated.

### Cursor-Based

```
GET /alerts?cursor=abc&limit=100
Response: { "items": [...], "next_cursor": "xyz" }
```

```python
def fetch_all(self):
    cursor = None
    while True:
        page = self._api.get(f"/alerts?cursor={cursor}&limit=100" if cursor else "/alerts?limit=100")
        yield from page["items"]
        cursor = page.get("next_cursor")
        if not cursor:
            break
```

**Pro:** Consistent across changes; opaque cursor.
**Con:** Can't jump to a specific page; resumption requires preserving the cursor.

### Time-Window

```
GET /alerts?since=1729382400000
```

```python
def fetch_since(self, timestamp_ms: int):
    return self._api.get(f"/alerts?since={timestamp_ms}")
```

**Pro:** Natural fit for connectors with last-success-time.
**Con:** Edge cases at boundaries — duplicate or missing if boundary is ambiguous.

## Cursor-Based Pagination Across Connector Runs

Third party has 10,000 alerts; connector has 2 minutes. Pattern:

```python
def get_alerts(self):
    cursor = self._read_context("pagination_cursor")
    alerts = []
    while not self._deadline_approaching():
        page_result = self._api.fetch_page(cursor=cursor, limit=500)
        alerts.extend(page_result.items)
        cursor = page_result.next_cursor
        if cursor is None:
            break
        if len(alerts) >= self.params.max_alerts_per_cycle:
            break
    self._save_context("pagination_cursor", cursor)
    return alerts
```

Next cycle resumes from the saved cursor. No data loss.

## Limit Size Tradeoffs

| Page size | Tradeoff |
|---|---|
| Small (10-50) | Many round trips; more overhead per alert; more resilient to API limits |
| Medium (100-500) | **Usually best** — good balance |
| Large (1000+) | Fewer round trips; risk of timeout per request; memory pressure |

Start with 100; tune based on observed performance.

## Handling "Total Count" Efficiently

Some APIs return `total: 5000` in the first response. Use it to avoid pagination when there's less data than your page size:

```python
first = self._api.get("/alerts?limit=500")
if first["total"] <= 500:
    return first["items"]
# else paginate
```

Avoids unnecessary calls for small datasets.

## Rate Limit Recovery — Cross-Connector

Two connectors in the same tenant hammering the same API can compound rate limit problems. Solutions:

- **Per-tenant shared token bucket** — store rate-limit state in context so all connectors see it
- **Stagger schedules** — one connector at :00, other at :02, etc.
- **Consolidate** — if they query the same endpoint, consider merging into one connector

## Dealing with 503 Backoff Patterns

Some APIs use 503 instead of 429 for "try again later". Treat identically:

```python
if r.status_code in (429, 503):
    retry_after = int(r.headers.get("Retry-After", "60"))
    raise RateLimitError(retry_after=retry_after)
```

## Logging Rate-Limit Events

Always log when you hit a limit — SOC teams use these logs to correlate connector issues:

```python
self._logger.warning(
    f"Rate-limited by {self.product_name}. "
    f"Retry after {retry_after}s. "
    f"Processed {processed_count}/{total_count} in this cycle."
)
```

## Next

→ **[Interview Q&A](questions.md)**
