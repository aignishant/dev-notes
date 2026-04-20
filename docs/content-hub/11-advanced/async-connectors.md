# Async Connectors

## When to Choose Async

| | Sync | Async |
|---|---|---|
| **Default** | ✅ | |
| **Complexity** | Low | Higher |
| **Debugging** | Easy | Stack traces are meaner |
| **Use when** | Volume low, API serial | Third-party tolerates concurrent calls AND volume is high AND per-alert enrichment parallelizes |

**Rule:** Don't use async by default. Reach for it only when you have a measurable reason.

## `TIPCommon.base.connector.async_connector`

```python
import asyncio

from TIPCommon.base.connector.async_connector import AsyncConnector
from TIPCommon.data_models import BaseAlert


class FastConnector(AsyncConnector):
    async def get_alerts(self) -> list[BaseAlert]:
        ids = await self.api.list_alert_ids(since=self._last_run)
        tasks = [self.api.fetch_alert_detail(id) for id in ids]
        details = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            BaseAlert(raw_data=d, alert_id=d["id"])
            for d in details
            if not isinstance(d, Exception)
        ]

    async def create_alert_info(self, alert: BaseAlert) -> AlertInfo:
        # Build AlertInfo — can still be sync-style logic inside
        info = AlertInfo()
        info.alert_id = alert.alert_id
        # ...
        return info


def main() -> None:
    FastConnector(script_name="Fast Connector").start()   # base handles asyncio.run()
```

## Concurrency Limiting

`asyncio.gather` will fire all tasks at once — dangerous against most APIs. Use a semaphore:

```python
async def get_alerts(self) -> list[BaseAlert]:
    ids = await self.api.list_alert_ids(since=self._last_run)
    sem = asyncio.Semaphore(10)   # at most 10 concurrent

    async def fetch_one(id):
        async with sem:
            return await self.api.fetch_alert_detail(id)

    results = await asyncio.gather(*(fetch_one(id) for id in ids), return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

Tune the semaphore value based on the third party's rate limit.

## Async HTTP Clients

Stick with `httpx` for async — same API surface as `requests`:

```python
import httpx

class AsyncMyClient:
    def __init__(self, base_url: str, api_key: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    async def list_alert_ids(self, since: int) -> list[str]:
        r = await self.client.get("/alerts", params={"since": since})
        r.raise_for_status()
        return [a["id"] for a in r.json()["alerts"]]

    async def fetch_alert_detail(self, id: str) -> dict:
        r = await self.client.get(f"/alerts/{id}")
        r.raise_for_status()
        return r.json()

    async def close(self):
        await self.client.aclose()
```

Ensure `await client.aclose()` in connector cleanup — or use `async with`.

## Async-Safe Error Handling

`asyncio.gather(return_exceptions=True)` prevents one failure from killing the whole batch. Collect exceptions and report:

```python
results = await asyncio.gather(*tasks, return_exceptions=True)

successes = []
failures = []
for id, result in zip(ids, results):
    if isinstance(result, Exception):
        failures.append((id, type(result).__name__, str(result)))
    else:
        successes.append(result)

self.logger.warning(f"{len(failures)} alerts failed: {failures[:5]}")  # log sample
```

## Async Rate Limit Handling

Rate limits hit at any point in parallel calls. Back off with jitter:

```python
import random

async def fetch_with_backoff(self, id: str, attempts: int = 3) -> dict:
    for attempt in range(attempts):
        try:
            return await self.client.get(f"/alerts/{id}").raise_for_status().json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < attempts - 1:
                delay = 2 ** attempt + random.uniform(0, 1)
                await asyncio.sleep(delay)
                continue
            raise
    raise RuntimeError("exhausted retries")
```

## Timeout Coordination

The platform's deadline (`execution_deadline_unix_time_ms`) still applies. In async:

```python
async def get_alerts(self) -> list[BaseAlert]:
    remaining_ms = self._deadline_remaining_ms()
    timeout = remaining_ms / 1000 - 5   # leave 5s for finalization

    try:
        result = await asyncio.wait_for(self._fetch_all(), timeout=timeout)
    except asyncio.TimeoutError:
        self.logger.warning("Async fetch timed out, returning partial")
        return self._partial_results   # whatever was collected
    return result
```

Respect the platform deadline — partial success is better than killed-mid-process.

## Common Async Pitfalls

| Pitfall | Fix |
|---|---|
| `asyncio.gather` without semaphore → API 429s | Semaphore with value ≤ provider's concurrent limit |
| Forgetting `await client.aclose()` | Connection leak; use `async with` or explicit cleanup |
| Mixing sync `requests` with async code | Blocks event loop; all HTTP must go through `httpx` async |
| `async` functions that don't `await` anything | Return coroutine, never scheduled → silent no-op |
| Assuming exceptions propagate | `gather(return_exceptions=True)` swallows them into return list — handle them |

## When NOT to Use Async

- The third-party API serializes requests anyway (some old APIs do)
- Rate limit is so tight that concurrency buys nothing
- Per-alert processing is trivial (< 10ms) — overhead of asyncio > gain
- Team is uncomfortable with async debugging — maintainability matters more than 2x speedup

The best answer to "should I use async?" is often "no, keep it simple."

## Next

→ **[Sync Jobs Pattern](sync-jobs.md)**
