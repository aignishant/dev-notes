# Sync Jobs Pattern

## Problem

Many tenants want bidirectional synchronization between SOAR and a third-party system. A case in SOAR ↔ a ticket in ServiceNow / Jira / Zendesk. Comments, status, priority, tags must reflect on both sides.

Naïve implementation creates **sync loops** — A mirrors to B, B mirrors back to A, infinite oscillation.

## `BaseSyncJob`

TIPCommon's `base_sync_job.py` codifies the solution. It splits a sync job into three phases:

1. **Outbound phase** — push SOAR-side changes to third party
2. **Inbound phase** — pull third-party changes into SOAR
3. **Loop prevention** — distinguish mirrored changes from native ones

```python
from TIPCommon.base.job.base_sync_job import BaseSyncJob

class ServiceNowSyncJob(BaseSyncJob):
    def _perform_outbound_sync(self) -> None:
        """SOAR → ServiceNow."""
        cases = self._get_recently_updated_cases()
        for case in cases:
            self._sync_case_outbound(case)

    def _perform_inbound_sync(self) -> None:
        """ServiceNow → SOAR."""
        tickets = self.client.list_tickets_updated_since(self._last_inbound)
        for ticket in tickets:
            self._sync_ticket_inbound(ticket)
```

## Three Loop-Prevention Strategies

### Strategy 1 — Author Tag

Every mirrored event is tagged with a marker indicating its origin:

```python
MIRRORED_COMMENT_PREFIX = "[SOAR-Mirror]"

# Outbound
def _sync_case_outbound(self, case):
    for comment in self._new_soar_comments(case):
        if comment.text.startswith(MIRRORED_COMMENT_PREFIX):
            continue   # already a mirrored one — don't re-mirror
        self.client.add_comment(
            case.external_ticket_id,
            f"{MIRRORED_COMMENT_PREFIX} {comment.author}: {comment.text}"
        )

# Inbound
def _sync_ticket_inbound(self, ticket):
    for comment in self._new_snow_comments(ticket):
        if MIRRORED_COMMENT_PREFIX in comment.text:
            continue   # was mirrored from SOAR — skip
        self.soar_job.add_comment(ticket.case_id, ...)
```

**Pros:** Simple. Transparent to anyone reading logs.
**Cons:** Prefix is user-visible; some teams find it ugly.

### Strategy 2 — Idempotency Key

Embed a unique ID in the mirrored object so the other side recognizes it:

```python
import uuid

def _sync_case_outbound(self, case):
    for comment in self._new_soar_comments(case):
        idempotency_key = f"soar-{case.id}-{comment.id}"
        if self.client.ticket_has_comment_with_key(case.external_id, idempotency_key):
            continue
        self.client.add_comment(
            ticket_id=case.external_id,
            text=comment.text,
            custom_field_idempotency=idempotency_key,
        )
```

**Pros:** Invisible to users.
**Cons:** Requires the third-party to support custom fields; adds query overhead.

### Strategy 3 — Time Threshold

Only mirror changes older than N seconds:

```python
THRESHOLD_SECONDS = 10

def _sync_case_outbound(self, case):
    for comment in case.comments:
        age = now() - comment.created_at
        if age < THRESHOLD_SECONDS:
            continue   # too new; wait for next cycle
        self.client.add_comment(...)
```

**Pros:** Trivial. No state.
**Cons:** Adds latency. Doesn't fully prevent loops, just makes them slower.

**Best practice:** combine Strategy 1 + Strategy 2. Primary prevention via idempotency key; fallback via author tag.

## Field-by-Field Sync vs Whole-Record

| | Field-by-field | Whole-record |
|---|---|---|
| **What** | Detect per-field changes, mirror only changed fields | Detect any change, mirror the whole record |
| **Pro** | Minimal API calls; granular | Simple implementation |
| **Con** | Requires diffing prior state | Costly if records are large |

For SOAR ↔ ticketing, field-by-field wins because the third party rate-limits updates.

## Two-Way Status Mapping

SOAR has its status enum; third party has its. Maintain explicit mapping:

```python
STATUS_MAP_OUT = {
    "New": "open",
    "Investigating": "in_progress",
    "Pending Vendor": "waiting_on_vendor",
    "Closed": "resolved",
}

STATUS_MAP_IN = {v: k for k, v in STATUS_MAP_OUT.items()}
```

Handle unknown statuses gracefully — don't lose information:

```python
def translate_status_inbound(snow_status):
    if snow_status not in STATUS_MAP_IN:
        self.logger.warning(f"Unknown ServiceNow status: {snow_status}, leaving SOAR unchanged")
        return None
    return STATUS_MAP_IN[snow_status]
```

## Ordering Matters

If you run outbound then inbound:

1. Outbound pushes SOAR comment to ServiceNow (added to SNow with SOAR tag)
2. Inbound fetches SNow changes — sees the just-added comment
3. Loop-prevention (author tag) skips it

If you ran inbound then outbound, or both in parallel, you could mirror a comment back to itself within one cycle.

**Always:** outbound → inbound, strict serial. Document this in the code.

## External ID Reference

Each SOAR case has an "external ticket ID" field pointing at the third-party record:

```python
case.add_custom_property("external_ticket_id", "INC0012345")
```

And conversely each ticket has a SOAR case reference:

```python
self.client.update_ticket(
    ticket_id,
    custom_fields={"soar_case_id": str(case.id)},
)
```

Bidirectional references make sync lookups O(1) — no scanning.

## Next

→ **[Error Handling Patterns](error-handling.md)**
