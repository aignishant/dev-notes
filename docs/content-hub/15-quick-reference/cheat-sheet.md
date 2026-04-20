# Cheat Sheet — Content Hub Lead Interview

Print this. Keep it on your desk during prep. Memorize the left column; the right column is explanation.

## Core Definitions (10-second answers)

| | |
|---|---|
| **Content Hub** | Open-source repo (Apache 2.0) of community/partner Response Integrations, Playbooks, and Parsers for Google SecOps |
| **Response Integration** | Python + YAML package: actions, connectors, jobs, widgets, core client |
| **Action** | On-demand task run from a playbook step |
| **Connector** | Cron-like script that ingests alerts from third-party products |
| **Job** | Cron-like script that syncs state between SOAR and third-party products |
| **Playbook** | YAML-defined workflow: trigger → steps → (actions/conditions/blocks) |
| **Parser** | CBN file that transforms raw logs into UDM events |
| **CBN** | Configuration-Based Normalization — parser DSL |
| **UDM** | Unified Data Model — canonical event schema |
| **Entity** | IoC/asset (IP, user, hash, URL) extracted from events |
| **Ontology** | Event-field → Entity-type mapping rules |
| **TIPCommon** | Shared library with `Action`/`Connector`/`Job` base classes |
| **`mp` CLI** | Build/validate/test/deploy CLI |

## The Data Flow (Memorize This Chain)

```
Raw Log → Parser → UDM → Detection Rule → Alert
Third-Party API → Connector → Alert
Alert → Ontology Mapping → Entities
Alerts + Time/Entity overlap → Case
Alert/Case + Trigger match → Playbook fires
Playbook steps → Integration Actions → Entity enrichment / Remediation
```

## File Structure Mnemonic

```
integration/
├── actions/         — on-demand tasks
├── connectors/      — alert ingestion
├── jobs/            — state sync
├── core/            — API client + shared code
├── widgets/         — HTML+YAML UI (alert view)
├── tests/           — pytest suite
├── resources/       — logo + example JSON
├── definition.yaml  — identity + config params
├── ontology_mapping.yaml   — REQUIRED if connector exists
├── release_notes.yaml      — per-version changelog
├── pyproject.toml   — uv deps
└── uv.lock
```

## The 4-Phase Action Lifecycle

```
_extract_action_parameters()  → pull from SDK
_validate_params()            → via ParameterValidator
_init_api_clients()           → build client from core/
_perform_action(entity=None)  → business logic
```

Base class handles: logging, timing, error wrapping, timeout checks, finalization.

## The 6-Phase Connector Lifecycle

```
extract_params()           → params
validate_params()          → validation
read_context_data()        → last-run ts + processed IDs
init_managers()            → API client
get_alerts()               → fetch from third party
for each alert:
   create_alert_info()     → build AlertInfo
   overflow check
   store_alert_in_cache()  → processed IDs
_save_context_data()       → persist state (cap at 10k)
```

## TIPCommon Key Modules

| Module | For |
|---|---|
| `TIPCommon.base.action` | `Action` base class |
| `TIPCommon.base.connector` | `Connector` / `AsyncConnector` |
| `TIPCommon.base.job` | `Job` / `BaseSyncJob` / `BaseJobRefreshToken` |
| `TIPCommon.extraction` | `extract_action_param`, `extract_connector_param`, `extract_job_param` |
| `TIPCommon.validation` | `ParameterValidator.validate_json / csv / range / email / url / ...` |
| `TIPCommon.smp_time` | `get_last_success_time`, `is_approaching_action_timeout` |
| `TIPCommon.context` | Persistent KV store |
| `TIPCommon.cache` | In-memory per-run cache |
| `TIPCommon.oauth` | OAuth 2.0 helpers |
| `TIPCommon.data_models` | `BaseAlert`, `Container` |
| `TIPCommon.types` | `JSON`, `Entity`, `Contains` type aliases |

## `mp` Commands

| | |
|---|---|
| `mp build` | Build to zip / `--deconstruct` reverses |
| `mp validate` | Structural + metadata / `--only-pre-build` for fast |
| `mp test` | Run pytest |
| `mp check` | Lint via Ruff / `--static-type-check` adds Ty |
| `mp format` | Auto-format |
| `mp dev-env login/push/pull` | Deploy to dev SOAR |
| `mp describe` | AI action descriptions |

## The Four Entity Buckets (Action-Level)

```python
enriched_entities   # successful
limit_entities      # rate-limited (retry next cycle)
failed_entities     # other errors
missing_entities    # not found in third party
```

Iterate entities; try/except routes into buckets; single bad entity doesn't fail action.

## The Three Loop-Prevention Strategies (Sync Jobs)

1. **Author tag** — `[SOAR-Mirror]` prefix on mirrored comments
2. **Idempotency key** — unique ID embedded in the record
3. **Time threshold** — only mirror older-than-N-seconds changes

## OAuth Client Credentials Pattern

```
(1) POST /oauth/token with client_id + client_secret
(2) Receive access_token + expires_in
(3) Cache token in connector context (encrypted)
(4) Use Bearer token on every API call
(5) On 401: invalidate cache + refresh + retry once
```

## Ontology Required Fields

Two absolutely mandatory:

- `start_time`
- `end_time`

Without these → case grouping breaks silently → SOAR floods with one-case-per-alert.

## Type Hint Header (Every File)

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from TIPCommon.base.interfaces import ApiClient
    from TIPCommon.types import JSON, Contains
```

## Common Pitfalls (Never Do)

- `type: string` for API keys → use `password`
- `print_value=True` on password → logs secret
- `uuid.uuid4()` as `alert_id` in connector → duplicates every run
- Missing `start_time` / `end_time` in ontology → case grouping broken
- Unbounded `processed_ids` cache → context grows forever
- Bare `except Exception:` without specific branches → confusing errors
- `verify_ssl = False` default → insecure
- Committing secrets / `.env` files → Git forever
- Renaming `definition.yaml.identifier` → breaks customer playbooks

## The Lead-Signal Sentences

Have these in your back pocket:

> *"Connectors create alerts, not cases. The platform groups alerts into cases based on time window and entity overlap."*

> *"TIPCommon's base classes use the Template Method pattern — the base's `run()` orchestrates lifecycle phases; subclasses fill in the specific methods."*

> *"We prefer Feed + Parser for ingestion because it scales. Connectors exist when the third-party doesn't expose a feed-friendly format."*

> *"Every integration's `uv.lock` is committed — reproducible builds across dev, CI, and customer."*

> *"I treat the `Ontology mapping` file as sacred — missing `start_time` or `end_time` silently breaks case grouping."*

> *"We parallel-deploy old and new versions during migrations; customers opt in; telemetry drives cutover."*

## Study Path (If You Forget Everything Else)

- Week before → Sections 3, 6, 11, 12 (deep technical)
- Night before → this cheat sheet + Section 13 (behavioral)
- Morning of → Section 15's [Day-Before Checklist](day-before.md)

## Next

→ **[Glossary](glossary.md)**
