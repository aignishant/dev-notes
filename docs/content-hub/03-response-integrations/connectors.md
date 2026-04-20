# Connectors — Deep Dive

## Definition

> *"A Connector is a Python script that runs continuously like a cron job. Its job is to poll a third-party product, pull new alerts (or alert-worthy events), and post them as `AlertInfo` objects for platform ingestion. Connectors live at `connectors/<n>.py` + `<n>.yaml`. Connectors create **Alerts**, not Cases — the platform groups alerts into cases."*

## Connector YAML

```yaml
name: Example Connector
parameters:
    - name: Alert JSON to ingest
      default_value: |
          {
            "display_name": "display_name",
            "events": [
              {"key1": "value1"}
            ]
          }
      type: string
      description: The event that would be ingested by the connector
      is_mandatory: true
      is_advanced: false
      mode: regular
description: Example connector description
integration: IntegrationIdentifier
rules: []
is_connector_rules_supported: true
creator: Admin
```

Key fields:

| Field | Meaning |
|---|---|
| `name` | Human-readable connector name |
| `integration` | Must match `identifier` in `definition.yaml` |
| `parameters[]` | Runtime params (API Root, API Key, Max Hours Back, Alert Type Filter, etc.) |
| `rules[]` | Pre-filter rules (allowlist/blocklist/whitelist) evaluated before alert creation |
| `is_connector_rules_supported` | Enables the rules feature in the UI |
| `creator` | Author |

## Typical Connector Parameters

Most real connectors expose at least:

- **API Root** — third-party endpoint URL
- **API Key / Credentials** — auth
- **Verify SSL** — boolean
- **Environment Field Name** — which event field maps to SOAR environment
- **Environment Regex Pattern** — regex over that field
- **Max Hours Backwards** — how far back to pull on first run
- **Max Alerts Per Cycle** — ingestion rate cap
- **Alert Type Filter / Severity Filter** — vendor-specific selection
- **Offset Timezone** — normalize third-party timestamps
- **Proxy Server Address / Username / Password** — HTTP proxy support
- **Disable Overflow** — turn off the platform's alert-flood protection
- **Whitelist as a Blacklist** — inverts the connector rules

## Connector Lifecycle (TIPCommon 2.x)

```
Connector.start()
  ├─ extract_params()          # Pull params from SDK
  ├─ validate_params()         # Validate via ParameterValidator
  ├─ init_managers()           # Build API clients
  ├─ read_context_data()       # Load last-run state (timestamp, processed IDs)
  ├─ loop:
  │    ├─ get_alerts()         # Fetch from third-party
  │    ├─ for alert:
  │    │    ├─ pre-process (rules, filters, whitelist)
  │    │    ├─ create_alert_info(alert)
  │    │    ├─ overflow check
  │    │    └─ yield AlertInfo
  │    └─ break if deadline / max reached
  └─ save_context_data()       # Persist last-run timestamp + processed IDs
```

## Canonical Modern Connector Shape

```python
from __future__ import annotations
import uuid

from soar_sdk.SiemplifyConnectorsDataModel import AlertInfo
from TIPCommon.base.connector import Connector
from TIPCommon.data_models import BaseAlert
from TIPCommon.extraction import extract_connector_param
from TIPCommon.validation import ParameterValidator


def main() -> None:
    ExampleConnector(script_name="Example Connector").start()


class ExampleConnector(Connector):
    def extract_params(self) -> None:
        self.params.alert_json = None
        self.params.alert_json_str = extract_connector_param(
            siemplify=self.siemplify,
            param_name="Alert JSON to ingest",
            is_mandatory=True,
            print_value=True,
        )

    def validate_params(self) -> None:
        validator = ParameterValidator(self.siemplify)
        self.params.alert_json = validator.validate_json(
            param_name="Alert JSON to ingest",
            json_string=self.params.alert_json_str,
        )
        self._validate_alert_json()

    def _validate_alert_json(self) -> None:
        match self.params.alert_json:
            case {"display_name": _, "events": [*_, _]} as alert_json if alert_json:
                return
            case _:
                raise ValueError(
                    "Alert JSON to ingest is not a valid Alert object. "
                    "Provide {'display_name': ..., 'events': [...]}"
                )

    def init_managers(self) -> None:
        """No API requests needed for this example."""

    def get_alerts(self) -> list[BaseAlert]:
        alert = BaseAlert(raw_data=self.params.alert_json, alert_id=uuid.uuid4())
        return [alert]

    def create_alert_info(self, alert: BaseAlert) -> AlertInfo:
        info = AlertInfo()
        info.alert_id = alert.alert_id
        info.display_id = alert.raw_data["display_name"]
        info.events = alert.raw_data["events"]
        return info


if __name__ == "__main__":
    main()
```

Notice the **pattern match** (`match/case`) in `_validate_alert_json` — Python 3.10+ idiom used heavily in modern integrations.

## Building a Real `AlertInfo`

```python
def create_alert_info(self, alert: BaseAlert) -> AlertInfo:
    info = AlertInfo()
    info.alert_id = str(alert.raw_data["incident_id"])            # stable external ID
    info.display_id = alert.raw_data["title"]                      # what shows in UI
    info.ticket_id = str(alert.raw_data["incident_id"])            # for update/dedup
    info.name = alert.raw_data["title"]
    info.rule_generator = alert.raw_data.get("rule_name", "Default Rule")
    info.start_time = int(alert.raw_data["created_at_unix_ms"])
    info.end_time = int(alert.raw_data["last_updated_unix_ms"])
    info.priority = map_severity_to_priority(alert.raw_data["severity"])
    info.device_vendor = "VendorName"
    info.device_product = "ProductName"
    info.environment = self.params.environment
    info.source_grouping_identifier = alert.raw_data["incident_id"]
    info.events = [build_event(e) for e in alert.raw_data["events"]]
    return info
```

Every field here feeds into ontology mapping and case grouping — treat `AlertInfo` population as a first-class concern.

## Idempotency — The Cardinal Rule

Connectors MUST be idempotent across runs. Enforce via:

1. **Stable `alert_id`** — use the third-party's stable identifier, not `uuid.uuid4()` unless you're really generating new alerts
2. **Processed-IDs cache** — store recently-seen IDs in connector context and skip duplicates
3. **Last-run timestamp** — query third-party with `since=last_run_timestamp`

```python
last_run = self._get_connector_last_success_time()  # stored in context
new_alerts = self.api.fetch_since(last_run)
processed_ids = self._read_processed_ids_cache()
new_alerts = [a for a in new_alerts if a.id not in processed_ids]
```

## Overflow Protection

The platform has **alert overflow protection** — if too many alerts with similar attributes arrive, the platform suppresses excess ones. The connector framework exposes `is_overflowed(alert_info)` to check before yielding.

If overflow is triggered, the connector should:
- **Log the suppression**
- **Continue processing subsequent alerts** (don't bail)
- **NOT mark the alert as processed** in context (let it retry next cycle if conditions change)

The "Disable Overflow" parameter lets customers opt out of this.

## Connector Context & State

Connectors persist state across runs via:

- **Context data** — platform-backed KV store, read via `self.siemplify.fetch_timestamp()` and `self.siemplify.save_timestamp(...)`
- **Last success time** — special context key managed by TIPCommon helpers
- **Custom keys** — for processed-ID tracking, auth tokens, etc.

```python
from TIPCommon.consts import UNIX_FORMAT

last_success = self._get_connector_last_success_time(
    offset_with_metric={"hours": self.params.max_hours_back},
    time_format=UNIX_FORMAT,
)
# ... fetch alerts ...
self._save_timestamp(self.connector_start_time)
```

## Test Run Mode

`is_test_run=True` distinguishes the SOAR UI's **"Test"** button from an actual scheduled run. In test mode:

- Don't save state (no `save_timestamp`)
- Don't push alerts to the pipeline
- Return a sample so UI can display

The base class exposes `self.is_test_run` — respect it.

## Environment Extraction

Multi-environment customers need connectors that tag alerts with the right environment name. The platform uses:

- `Environment Field Name` parameter — which event field carries the env
- `Environment Regex Pattern` parameter — regex to extract/normalize
- Fallback to default environment if no match

EnvironmentCommon provides `GetEnvironmentCommonFactory` which hides this logic — just call `env_common.get_environment(event_dict)`.

## Async Connector Variant

TIPCommon also ships an **async** connector base class: `TIPCommon.base.connector.async_connector.AsyncConnector`. Use when:

- Third-party API supports concurrent requests
- Alert volume per cycle is high
- Per-alert enrichment (e.g., GET alert details per ID) parallelizes well

```python
import asyncio
from TIPCommon.base.connector.async_connector import AsyncConnector

class FastConnector(AsyncConnector):
    async def get_alerts(self):
        ids = await self.api.list_alert_ids()
        tasks = [self.api.fetch_alert_detail(id) for id in ids]
        return await asyncio.gather(*tasks)
```

## Connector Rules

`is_connector_rules_supported: true` enables in-UI allowlist/blocklist rules (by alert name, severity, tag, etc.). The base class evaluates rules before `create_alert_info`, so your code doesn't implement the filter — declare support and provide fields.

## Common Connector Gotchas

| Gotcha | Prevention |
|---|---|
| Duplicate alerts across runs | Stable external alert_id + processed-ID cache |
| Missing `start_time`/`end_time` → no case grouping | Map in ontology AND populate in `AlertInfo` |
| Connector falls behind on large tenants | Use async base, tune `Max Alerts Per Cycle`, add pagination |
| Timestamp drift (third party in UTC, local clock in PST) | Always convert to Unix MS; explicit timezone handling |
| Auth token expiry mid-cycle | Refresh in `get_alerts` on 401; don't fail the whole run |
| Rate limit half-way through | Catch, log, save progress, return partial success |

## Next

→ **[Jobs Deep Dive](jobs.md)**
