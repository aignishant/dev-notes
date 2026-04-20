# Advanced Topics — Interview Q&A

---

## Q1. How do you handle OAuth token refresh for a connector running every 5 minutes?

Cache the token in connector context (encrypted at rest by the platform). Track `expires_at`. On each run: if token exists and not expired, use it; otherwise exchange client_id + client_secret for a new one and cache. On any 401 response, invalidate the cache and re-fetch. TIPCommon's OAuth helpers automate this pattern.

---

## Q2. What's the difference between `TIPCommon.cache` and `TIPCommon.context`?

`cache` is per-process / per-run in-memory — cleared when the action/connector run ends. `context` is persistent platform KV storage — survives across runs, encrypted at rest. Use `cache` within a single run (e.g., dedupe repeated API calls across entities); use `context` for state that must persist (last-run timestamp, processed IDs, OAuth tokens).

---

## Q3. Your connector's processed-IDs cache is growing unbounded. What do you do?

Cap the size. Before saving to context, truncate to the most recent N IDs:

```python
MAX_CACHE = 10_000
recent = list(self._processed_ids)[-MAX_CACHE:]
context.set(self.siemplify, "processed_ids", recent)
```

Choose N as a multiple of peak per-run volume — at least 2-5×. For a connector producing ~1000 alerts/cycle, 10,000 is comfortable.

---

## Q4. Why save `connector_start_time` instead of `unix_now()` at the end of a connector?

If the run took 4 minutes and you saved "now", the next run's window starts 4 minutes after this one started — you'd miss any activity that happened during the run. Saving `connector_start_time` ensures overlap-safe windowing — the next run picks up right where this one began, re-processing the same few minutes safely (idempotency via processed-IDs handles dedup).

---

## Q5. When do you choose async over sync for a connector?

When all three hold: (a) the third-party API tolerates concurrent requests without 429-storming, (b) alert volume per cycle is high enough that serial processing falls behind, (c) per-alert detail fetches parallelize cleanly. Don't reach for async by default — debugging and maintainability costs are real. Usually sync is fine.

---

## Q6. How do you prevent a sync loop between SOAR and a third-party ticketing system?

Three techniques, usually combined:

1. **Author tag** — prefix mirrored comments with `[SOAR-Mirror]` or similar; skip those on the return path
2. **Idempotency key** — embed a unique ID in the mirrored record; other side queries for the key before mirroring back
3. **Time threshold** — only mirror changes older than N seconds, smoothing any residual oscillation

Plus: outbound → inbound ordering, strict serial.

---

## Q7. How do you handle a 429 rate limit response?

1. Parse `Retry-After` header (fallback: 60 seconds)
2. Sleep with jitter: `retry_after + random.uniform(0, retry_after * 0.3)`
3. Retry up to N times (typically 3) with exponential backoff
4. If still failing, classify the entity/alert into a `rate_limited` bucket and continue with others
5. Next cycle picks up — don't kill the whole run for rate limits

Check platform deadline inside retry loops; don't retry past the action timeout.

---

## Q8. Walk me through pagination for a connector that must fetch 10,000 alerts but only has 2 minutes per run.

Cursor-based pagination with context checkpointing:

1. On run start, read saved `pagination_cursor` from context
2. Loop fetching pages with that cursor, saving new cursor after each page
3. Break when: cursor is None (end), deadline approaching, OR max alerts per cycle reached
4. Save final cursor to context
5. Next run resumes from saved cursor

No data loss, graceful continuation.

---

## Q9. Why is exponential backoff always paired with jitter?

Without jitter: all clients that hit rate limit simultaneously retry at exactly the same computed time, creating a new thundering herd. Jitter smears retries across a small random window, letting the API recover.

```python
delay = (2 ** attempt) + random.uniform(0, 1)
```

---

## Q10. How do you handle a partial failure across entity iteration in an action?

Four-bucket categorization:

```python
enriched_entities = []    # succeeded
limit_entities = []       # rate-limited
failed_entities = []      # other errors
missing_entities = []     # not found upstream
```

Per-entity try/except routes into the right bucket. Action never fails wholesale for one bad entity. Output message summarizes per-bucket. Update enriched_entities via `siemplify.update_entities()` at the end in a single call.

---

## Q11. An auth error (401) — should you retry?

**No.** 401 on the first call after token refresh means credentials are genuinely bad. Retrying won't fix it. Immediately raise `InvalidCredentialsError` with a clear "update integration config" message.

Exception: if you haven't refreshed the token yet in this call, refresh + retry **once**. That handles the "platform-cached token became stale" case.

---

## Q12. A third-party rate-limits per-second; your connector launches 100 concurrent tasks. Design.

Semaphore-bounded concurrency:

```python
sem = asyncio.Semaphore(n)   # match the per-second quota
async def fetch(id):
    async with sem:
        return await client.get(id)

results = await asyncio.gather(*(fetch(i) for i in ids), return_exceptions=True)
```

Plus a `TokenBucket` for finer-grained per-second rate control. Plus `return_exceptions=True` so one failure doesn't sink the batch.

---

## Q13. How would you debug "our connector is silently duplicating alerts across runs"?

1. Confirm `alert_id` is the third-party's stable ID, not `uuid.uuid4()`
2. Check processed-IDs cache is being read + written to context
3. Inspect context contents: is `processed_ids` growing run-over-run?
4. Check the filter logic: `if alert.id not in self._processed_ids` — is comparison correct?
5. Run the idempotency test: fire the connector twice with no new data; second run must emit zero alerts
6. If issue persists, add diagnostic logging around the dedup filter and observe one run

---

## Q14. Why must you never log API keys even at DEBUG level?

Logs are persistent. They're often ingested into SIEMs, shipped to log aggregators, retained for compliance. An API key in logs can leak to dozens of systems. `print_value=True` on a password param is a CVSS-worthy security incident. `extract_action_param(print_value=False)` for every sensitive parameter, always.

---

## Q15. Explain your approach to observability in a long-running connector.

- Structured log at each lifecycle phase: extract, validate, init, fetch, process, save
- Log key metrics: alerts fetched, filtered, deduped, emitted
- Log rate-limit events + retry counts
- Log context size before/after save (catch unbounded growth)
- Emit a summary at end: "Processed N alerts in M seconds, K duplicates filtered, L rate-limited, cursor saved"
- Never log secrets or full HTTP bodies
- `self._logger.exception(e)` on unexpected errors — stack trace included

The SOC reads these logs at 2 AM when their pipeline breaks.

---

## Next

→ **[Section 12: System Design](../12-system-design/index.md)**
