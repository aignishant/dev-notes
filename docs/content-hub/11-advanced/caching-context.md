# Caching & Context

## Two Distinct Things

| | **Cache** | **Context** |
|---|---|---|
| **Scope** | Per-process / per-run | Across runs (persistent) |
| **Backed by** | In-memory dict | Platform KV store |
| **Lifetime** | Duration of one action/connector run | Until explicitly deleted |
| **Used for** | Avoid repeated API calls within a single run | Last-run timestamp, processed IDs, OAuth tokens |

## `TIPCommon.cache`

In-memory, per-run cache:

```python
from TIPCommon.cache import Cache

cache = Cache()

def enrich_ip(ip: str) -> Report:
    if cached := cache.get(ip):
        return cached
    report = fetch_from_api(ip)
    cache.set(ip, report)
    return report
```

Good for: actions iterating many entities where several map to the same upstream query.

### TTL Variant

```python
cache.set(ip, report, ttl_seconds=60)
```

## `TIPCommon.context` — Persistent State

Connectors and jobs persist across runs via **platform context**. Stored encrypted.

```python
from TIPCommon import context

# Get
value = context.get(self.siemplify, "some_key")
value = context.get(self.siemplify, "some_key", default="fallback")

# Set
context.set(self.siemplify, "some_key", "some_value")

# Delete
context.delete(self.siemplify, "some_key")
```

### Typical Keys a Connector Stores

| Key | Purpose |
|---|---|
| `last_success_time` | Timestamp of last successful run |
| `processed_alert_ids` | Set of externally-sourced IDs already ingested |
| `oauth_access_token` | Cached bearer token |
| `oauth_expires_at` | Token expiry time |
| `pagination_cursor` | In-flight cursor for a paginated scan across runs |

## The Last-Success-Time Pattern

```python
from TIPCommon.smp_time import get_last_success_time
from TIPCommon.consts import UNIX_FORMAT

def read_context_data(self) -> None:
    self._last_run = get_last_success_time(
        siemplify=self.siemplify,
        offset_with_metric={"hours": self.params.max_hours_back},
        time_format=UNIX_FORMAT,
    )

def _save_context_data(self) -> None:
    self._save_timestamp(self.connector_start_time)
```

On first run: returns `now - max_hours_back` (backfill window).
On subsequent runs: returns the last saved timestamp.

!!! tip "Save connector_start_time, not `unix_now()`"
    Save `self.connector_start_time` at the end of the run, not "now". If the run took 4 minutes, saving "now" would miss the 4 minutes of activity during the run. Using `connector_start_time` guarantees overlap-safe windowing.

## Processed-IDs Cache Pattern

```python
def read_context_data(self) -> None:
    self._processed_ids: set[str] = set(
        context.get(self.siemplify, "processed_alert_ids", default=[])
    )

def get_alerts(self) -> list[BaseAlert]:
    raw_alerts = self.api.fetch_since(self._last_run)
    new_alerts = [a for a in raw_alerts if a.id not in self._processed_ids]
    return new_alerts

def store_alert_in_cache(self, alert: BaseAlert) -> None:
    self._processed_ids.add(alert.alert_id)

def _save_context_data(self) -> None:
    # Cap the size to prevent unbounded growth
    MAX_CACHE_SIZE = 10_000
    recent_ids = list(self._processed_ids)[-MAX_CACHE_SIZE:]
    context.set(self.siemplify, "processed_alert_ids", recent_ids)
```

### Why Cap the Set Size?

Without a cap, the set grows forever. After 6 months, context read/write gets slow. Cap at some multiple of typical per-run volume.

## The Platform DB (Advanced)

Some TIPCommon versions support a richer DB abstraction via `platform_supports_db()`:

```python
from TIPCommon.utils import platform_supports_db

if platform_supports_db():
    # Use the platform DB for structured state
    ...
else:
    # Fall back to context KV
    ...
```

This guards against version skew between the platform and your integration.

## Cross-Cycle Pagination

Scenario: Third-party returns 10,000 alerts paginated 500 per page. Your connector only has 2 minutes per cycle — it can process 2 pages before the deadline.

Pattern: **checkpoint the cursor in context**, continue next cycle.

```python
def get_alerts(self) -> list[BaseAlert]:
    cursor = context.get(self.siemplify, "pagination_cursor")
    alerts = []
    while not self._deadline_approaching():
        page, cursor = self.api.fetch_page(cursor)
        alerts.extend(page)
        if cursor is None:
            break  # end of data
    context.set(self.siemplify, "pagination_cursor", cursor)
    return alerts
```

Next cycle resumes from where you left off. Clean shutdown; no lost data.

## DataStream (TIPCommon)

`TIPCommon.DataStream` is a helper for streaming large datasets without loading all into memory. Iteration:

```python
from TIPCommon.DataStream import DataStream

with DataStream(self.siemplify, "large_set") as ds:
    ds.append(item)
    ...
    for item in ds.iter():
        ...
```

Useful when tracking huge processed-ID sets or cursors with more structure than a simple list.

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Saving mutable objects to context, mutating in-place | Always call `context.set` explicitly; no auto-save |
| Context growing unbounded | Cap sizes, TTL old entries |
| Reading context before `read_context_data()` phase | Use the connector lifecycle; don't bypass |
| Using context as a cache for within-run data | Use `TIPCommon.cache` instead |
| Forgetting to persist `connector_start_time` | Next run has wrong window — dupes or gaps |

## Next

→ **[Encryption](encryption.md)**
