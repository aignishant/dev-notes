# Jobs — Deep Dive

## Definition

> *"A Job is a Python script that runs continuously on a schedule. Unlike a connector, a job does NOT create alerts — it synchronizes state between SOAR and a third-party product. The canonical example is 'mirror SOAR case comments to the corresponding third-party ticket' or vice versa. Jobs live at `jobs/<n>.py` + `<n>.yaml` and are available under **Response → Job's Scheduler**."*

## Actions vs Connectors vs Jobs — Final Clarification

| | Action | Connector | Job |
|---|---|---|---|
| **Invocation** | Playbook step | Cron | Cron |
| **Purpose** | Single task | Alert ingestion | State sync |
| **Creates alerts?** | ❌ | ✅ | ❌ |
| **Receives entities?** | ✅ | ❌ | ❌ (operates on cases/alerts by filter) |
| **Per-run result** | Step output + JSON result | List of `AlertInfo` | Idempotent mutations |

## Job YAML

```yaml
name: Comment on tagged cases
parameters:
    - name: Tags
      default_value: Job Comment
      type: string
      description: Case tags that the job will comment on
      is_mandatory: true
    - name: Comment
      default_value: Job Comment
      type: string
      description: The comment that will be written to cases with the matching tags
      is_mandatory: true
description: Job Description
integration: Integration
creator: Admin
```

## Canonical Job Shape (TIPCommon 2.x)

```python
from __future__ import annotations
from typing import TYPE_CHECKING

import TIPCommon.consts
from soar_sdk.SiemplifyDataModel import CaseFilterStatusEnum
from TIPCommon.base.job import Job
from TIPCommon.extraction import extract_job_param
from TIPCommon.validation import ParameterValidator

if TYPE_CHECKING:
    from TIPCommon.base.interfaces import ApiClient
    from TIPCommon.types import Contains


def main() -> None:
    CommentOnTaggedCases(name="Comment on tagged cases").start()


class CommentOnTaggedCases(Job):
    def _extract_job_params(self) -> None:
        self.params.tags_string = extract_job_param(
            param_name="Tags", siemplify=self.soar_job, is_mandatory=True, print_value=True,
        )
        self.params.comment = extract_job_param(
            param_name="Comment", siemplify=self.soar_job, is_mandatory=True, print_value=True,
        )
        self.params.max_hours_back_string = extract_job_param(
            param_name="Max Hours Backwards", siemplify=self.soar_job, is_mandatory=True, print_value=True,
        )

    def _validate_params(self) -> None:
        validator = ParameterValidator(self.soar_job)
        self.params.tags = validator.validate_csv(
            param_name="Tags", csv_string=self.params.tags_string,
        )
        self.params.max_hours_back = validator.validate_positive(
            param_name="Max Hours Backwards", value=self.params.max_hours_back_string,
        )

    def _init_api_clients(self) -> Contains[ApiClient]:
        """No API Client needed for this job."""

    def _perform_job(self) -> None:
        last_run_ts = self._get_job_last_success_time(
            offset_with_metric={"hours": self.params.max_hours_back},
            time_format=TIPCommon.consts.UNIX_FORMAT,
        )

        case_ids: list[int] = self.soar_job.get_cases_ids_by_filter(
            status=CaseFilterStatusEnum.OPEN,
            update_time_from_unix_time_in_ms=last_run_ts,
            start_time_from_unix_time_in_ms=last_run_ts,
            tags=self.params.tags,
            environments=[self.params.environment_name],
        )
        for case_id in case_ids:
            self._add_comment_to_case_by_id(case_id)

        self._save_timestamp_by_unique_id(self.job_start_time)

    def _add_comment_to_case_by_id(self, case_id: int) -> None:
        alert_ids: list[str] = self.soar_job.get_alerts_ticket_ids_by_case_id(case_id)
        if not alert_ids:
            return
        alert_id = alert_ids[0]
        self.soar_job.add_comment(self.params.comment, case_id, alert_id)


if __name__ == "__main__":
    main()
```

## Job Lifecycle

```
Job.start()
  ├─ _extract_job_params()
  ├─ _validate_params()
  ├─ _init_api_clients()
  ├─ _perform_job()
  │    ├─ fetch last success time
  │    ├─ query cases/alerts since last run
  │    ├─ for each: mutate state
  │    └─ save timestamp
  └─ base handles error wrapping + logging
```

## The "Sync" Patterns You'll See

### Pattern 1 — SOAR → Third-Party (outbound sync)

> *"When a SOAR case comment is added, mirror it to the corresponding third-party ticket."*

1. Query SOAR for cases updated since last run.
2. For each case, fetch new comments since last run.
3. POST each comment to the third-party ticket (matched by external ticket ID).

### Pattern 2 — Third-Party → SOAR (inbound sync, non-alert)

> *"When a third-party ticket changes status, update the SOAR case."*

1. Query third-party for tickets changed since last run.
2. For each changed ticket, find the SOAR case (by external ticket ID stored in case context).
3. Update SOAR case status/priority/tags.

### Pattern 3 — Bidirectional sync

Two jobs, one each direction. Or a single job that handles both phases with careful ordering (usually outbound first, inbound second, to avoid loops).

## Preventing Sync Loops

If outbound mirrors SOAR comments to third-party, and inbound mirrors third-party comments to SOAR, you'll loop forever. Break the loop with:

1. **Author tag** — prefix mirrored comments with `[SOAR]` or `[ServiceNow]` and skip those on the other side
2. **Idempotency key** — include a stable ID in the mirrored comment metadata
3. **Time threshold** — only mirror comments older than N seconds (avoids tight loops)

Any robust bidirectional sync implements at least one of these.

## `_get_job_last_success_time` — The State Mechanic

```python
last_run_ts = self._get_job_last_success_time(
    offset_with_metric={"hours": self.params.max_hours_back},
    time_format=TIPCommon.consts.UNIX_FORMAT,
)
```

- On **first run**: there's no last success → returns `now - max_hours_back` (the backfill window)
- On **subsequent runs**: returns the last successful `job_start_time` you saved

The job saves its own success timestamp at the end: `self._save_timestamp_by_unique_id(self.job_start_time)`. Note the save happens with `job_start_time`, not "now" — if the run took 4 minutes, saving "now" would skip those 4 minutes of activity next run.

## Job Environment Scoping

Many tenants run multi-environment. Jobs should honor `self.params.environment_name` and pass it into `get_cases_ids_by_filter(environments=[env_name])`. Otherwise you mutate cross-tenant state — a serious bug.

## Job Idempotency

Jobs MUST be idempotent. The same job running twice should not:

- Add the same comment twice
- Create the same ticket twice
- Toggle status back and forth

Check target state before mutating:

```python
existing = self.api.get_ticket_comments(ticket_id)
if new_comment.idempotency_key in [c.idempotency_key for c in existing]:
    self.logger.info(f"Skipping already-mirrored comment {new_comment.idempotency_key}")
    continue
self.api.add_comment(ticket_id, new_comment)
```

## Jobs That Need No API Client

Some jobs operate purely on SOAR state (e.g., auto-close cases older than N days, auto-tag cases matching a pattern). In those, `_init_api_clients` is a no-op:

```python
def _init_api_clients(self) -> Contains[ApiClient]:
    """No API client needed for this job."""
```

## Base Classes for Sync Jobs

TIPCommon ships specialized bases:

- `base/job/base_job.py` — general-purpose Job
- `base/job/base_sync_job.py` — scaffolding for bidirectional sync
- `base/job/base_job_refresh_token.py` — jobs that refresh OAuth tokens on a schedule
- `base/job/job_case.py` — iterating cases with paging

Use them instead of rewriting the wheel.

## Next

→ **[Widgets](widgets.md)**
