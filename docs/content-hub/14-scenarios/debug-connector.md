# Debug a Failing Connector

## The Prompt

> *"A customer reports that after updating our Falcon connector from v2.1.3 to v2.2.0, they're seeing duplicate alerts in their case queue. Walk me through your debugging."*

This is an **interactive** interview — you're expected to ask questions, propose hypotheses, narrow down. The interviewer grades your process, not just the final answer.

## Step 1 — Establish Facts (1-2 min)

Start by asking:

- "When did the upgrade happen? Before/after the issue started?"
- "How many duplicates per hour? Is it growing or stable?"
- "Are duplicates exactly identical, or do they have different platform alert IDs but same external data?"
- "Does it affect all alerts from the connector or specific ones?"
- "Any changes on the customer side around the same time?"
- "Did we deploy to other customers at the same time? Are they affected?"

## Step 2 — Frame Hypotheses (1-2 min)

Before jumping into code, **name the likely causes**:

1. **alert_id not stable** — regenerated each run (e.g., `uuid.uuid4()` crept in)
2. **Processed-IDs cache not reading** — context read/write broken
3. **Processed-IDs cache reset** — maybe context was cleared by an upgrade
4. **Time-window misalignment** — connector pulling same window repeatedly
5. **Upstream duplicates** — third party is sending duplicates; connector faithfully ingests
6. **Ontology change** — not duplication in ingest, but case grouping broke, so separate cases per same alert

Say this out loud — interviewer sees structured thinking.

## Step 3 — Gather Evidence

For each hypothesis, what would confirm/refute?

### Hypothesis 1: alert_id not stable

```bash
# Compare alert_ids across runs for the same source alert
# Pull SOAR case queue; inspect .external_id vs .platform_id
```

If the external_id varies between duplicates → yes, stable ID is broken.
If the external_id is identical → no, duplicates have same external ID, must be elsewhere.

### Hypothesis 2: Cache read broken

Look at the connector logs for the upgrade window. Specifically `read_context_data` phase:

```
INFO: read_context_data — processed_ids count: 0
```

If the count jumped from 5000 (pre-upgrade) to 0 (post-upgrade), cache isn't reading. Diff the connector code between v2.1.3 and v2.2.0 — maybe the cache key changed.

### Hypothesis 3: Time window

Look at the timestamp passed to the third-party API:

```
INFO: fetching alerts since 1729000000000
```

If the same timestamp appears across runs, `save_timestamp` isn't committing. Code diff will show.

### Hypothesis 4: Upstream duplicates

Compare counts: if third party shows N alerts for a time window but customer sees 2N, and the external IDs map 1-to-1, it's not upstream — it's us.

### Hypothesis 5: Ontology change

If duplicates have different `case_id`s in SOAR (not different alerts in one case), it's not connector duplication — it's case grouping broken. Check ontology mapping diff — particularly `start_time`/`end_time`.

## Step 4 — Narrow Down

Typically one or two hypotheses become clear fast. Walk through:

> *"Given the count is stable and duplicates have the same external data but different platform alert IDs, and context is showing 0 processed IDs after the upgrade — Hypothesis 2. The cache key or read logic changed in the upgrade. Let me diff v2.1.3 and v2.2.0's connector code."*

```diff
- self._processed_ids = set(context.get(self.siemplify, "processed_alert_ids", default=[]))
+ self._processed_ids = set(context.get(self.siemplify, "processed_ids", default=[]))
```

**Found it.** The cache key was renamed in v2.2.0. After upgrade, the new code looks up a key that doesn't exist → returns empty default → treats everything as new.

## Step 5 — Fix

Smallest change that solves it:

```python
def read_context_data(self) -> None:
    # Read both old and new keys for backward compat during transition
    self._processed_ids = set(
        context.get(self.siemplify, "processed_ids", default=[])
        or context.get(self.siemplify, "processed_alert_ids", default=[])
    )
```

And next PR migrates the old key data to the new one, then removes the fallback.

Or, if migration matters for multiple customers: ship a **migration helper** that's run once on upgrade to copy the data over.

## Step 6 — Containment (before the fix lands)

If this is active production pain, contain first:

- Roll back the customer to v2.1.3 via Content Hub
- Stops new duplicates
- Buys time to prepare the fix and migration

## Step 7 — Post-mortem Action Items

1. Never rename a context key without a migration path
2. Add a `mp validate` check that flags changes to `context.get/set` keys
3. Regression test: run connector against a canned fixture with pre-existing processed_ids in both old and new format, verify no re-emission
4. Contribution guide: document "context schema migration" as a required consideration for any connector PR

## What the Interviewer Is Grading

- **Didn't just start coding** — asked scoping questions first
- **Named hypotheses upfront** — shows systematic thinking
- **Used evidence to narrow** — not guessing
- **Proposed containment before fix** — operational maturity
- **Closed with post-mortem actions** — preventing recurrence

Finishing with "and here's how we make sure this class of bug can't happen again" is the signature of a lead.

## Next

→ **[Migrate Legacy Integration](migrate-legacy.md)**
