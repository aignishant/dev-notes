# Scaling Connectors

## The Problem

> *"Our CrowdStrike connector was ingesting 500 alerts per 5-minute cycle. The customer's volume grew to 5,000 per cycle. The connector falls behind — every cycle it processes a window but the next window is already bigger. The backlog grows unboundedly. Design a solution."*

This is a classic scaling interview. Walk through the full decision tree.

## Step 1 — Measure Before Optimizing

Never optimize before measurement. Confirm:

- What's the actual per-cycle time?
- Where is time spent? API calls (N+1 per-alert detail fetch is usually the culprit), local processing, or state saves?
- Is the third party rate-limiting us or serving as fast as we ask?
- Memory bounded?

Add instrumentation:

```python
start = time.monotonic()
self._logger.info(f"Fetched {len(alerts)} alerts in {time.monotonic() - start:.1f}s")
```

If fetch is 90% of cycle, focus there. If processing is, focus there.

## Step 2 — Optimize Request Patterns

### Batch Endpoints

Most APIs have batch endpoints. `/detections/entities/summaries/GET/v1` takes a list of IDs; don't call per-ID.

Before:
```python
for id in ids:
    details = api.get_detail(id)  # N requests
```

After:
```python
details = api.get_details_batch(ids)  # 1 request, or chunks of 100
```

Often a 10-100× improvement.

### Pre-Filter Before Detail Fetch

If the list endpoint gives enough signal, filter before spending requests on details:

```python
summaries = api.list_summaries(since=last_run)
high_severity = [s for s in summaries if s["severity"] >= "High"]
details = api.batch_get([s["id"] for s in high_severity])
```

## Step 3 — Parallelism

Single-threaded sync fetch is often the floor. Options:

### Sync with threading.ThreadPoolExecutor

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_all(self, ids):
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(self._api.get_detail, id) for id in ids]
        return [f.result() for f in as_completed(futures)]
```

Simpler than async, concurrent I/O, requests-compatible.

### Async

```python
async def fetch_all(self, ids):
    sem = asyncio.Semaphore(10)
    async def one(id):
        async with sem:
            return await self._api.get_detail(id)
    return await asyncio.gather(*(one(i) for i in ids))
```

Higher ceiling than threads. Requires `AsyncConnector`.

**Pick threads for simplicity, async for peak throughput.**

## Step 4 — Connector Splitting

If one connector truly can't keep up:

### Split by Severity

- "Falcon High Severity" connector — more frequent schedule, small volume, low latency
- "Falcon Low Severity" connector — less frequent, higher batch

### Split by Type

- Detections connector
- IOAs connector
- Hosts-state connector

Each connector can tune its schedule, Max Alerts Per Cycle, and filter independently.

### Split by Environment

Multi-tenant: one connector instance per environment. Smaller per-instance scope; parallelism at the platform level.

## Step 5 — Cursor-Based Resumable Pagination

Connectors that must handle bursty volume:

```python
def get_alerts(self):
    cursor = self._read_context("cursor")
    alerts = []
    while not self._deadline_approaching() and len(alerts) < self.max_per_cycle:
        page = self._api.fetch(cursor=cursor)
        alerts.extend(page.items)
        cursor = page.next_cursor
        if cursor is None:
            break
    self._save_context("cursor", cursor)
    return alerts
```

Next cycle resumes. Never drop alerts even during large backfills.

## Step 6 — Change Schedule, Not Code

Sometimes the answer is scheduling, not optimization:

- Current: every 5 minutes, 500 alerts → barely keeping up
- Solution: every 2 minutes, 200 alerts → more cycles, smaller each, same total throughput, lower latency per alert

Or reverse for expensive pull:

- Every 15 minutes instead of 5, batch more per request, fewer total round trips

## Step 7 — Architectural Alternatives

### Feed + Parser (SIEM path)

If third party supports pushing logs via syslog / HTTPS feed, migrate ingestion to the SIEM path. Parsers handle high volume better than connectors.

### Webhook Receiver

If third party can push events:

- Stand up a webhook receiver (often via Power-up integration)
- Third party pushes on-demand; no polling overhead

### Multi-Process Connector (advanced)

Platform-level support varies, but some TIPCommon versions allow connectors to fan out across worker processes.

## Step 8 — Observability for Scale

Instrument to catch regressions:

- Per-cycle alert count
- Per-cycle duration
- Queue depth (alerts waiting to be processed)
- Rate-limit events per cycle
- Context size

Plot these — a scaling problem always shows up as a trend in one of them before it becomes a crisis.

## The Interview Narrative

When asked this question, structure:

1. **"I'd measure first — instrument per-phase time, identify the bottleneck."**
2. **"If API is the bottleneck, check for batch endpoints first; they're usually 10-100× wins."**
3. **"If still bottlenecked, add concurrency — threads for simplicity, async for peak."**
4. **"If single connector can't keep up, split by severity/type/environment."**
5. **"For spiky load, cursor-based pagination with context checkpointing — never drop alerts."**
6. **"For very high volume, consider migrating to Feed + Parser or webhook receiver."**
7. **"Always instrument first. Scale fixes that aren't measurable aren't improvements."**

That's an architecturally-sound 5-minute answer.

## Next

→ **[Designing a New Integration](design-new-integration.md)**
