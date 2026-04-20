# Live Coding — Build a Connector

## The Prompt

> *"Write a connector that polls `https://api.example.com/alerts?since={unix_ms}` and ingests each alert. Each response gives a list of `{id: str, title: str, severity: str, created_at_unix_ms: int, events: [...]}`. Handle idempotency across runs."*

## Step 1 — Clarify (1-2 min)

- "Auth — API key header?"
- "Pagination — single page or cursor? For this, assume single page up to some max, and use time-since filter."
- "Max volume per cycle we should cap at?"
- "Timeout behavior?"

## Step 2 — Structure

```
example_connector/
├── connectors/
│   ├── __init__.py
│   ├── alerts_connector.py
│   └── alerts_connector.yaml
├── core/
│   ├── __init__.py
│   └── api_client.py
├── ontology_mapping.yaml
├── definition.yaml
└── pyproject.toml
```

## Step 3 — API Client

```python
# core/api_client.py
from __future__ import annotations
from pydantic import BaseModel
import requests


class AlertPayload(BaseModel):
    id: str
    title: str
    severity: str
    created_at_unix_ms: int
    events: list[dict] = []


class ExampleClient:
    def __init__(self, base_url: str, api_key: str, verify_ssl: bool = True, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers["X-API-Key"] = api_key
        self.session.verify = verify_ssl
        self.timeout = timeout

    def fetch_alerts_since(self, since_unix_ms: int, limit: int = 200) -> list[AlertPayload]:
        r = self.session.get(
            f"{self.base_url}/alerts",
            params={"since": since_unix_ms, "limit": limit},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return [AlertPayload.model_validate(a) for a in r.json().get("alerts", [])]

    def ping(self) -> bool:
        r = self.session.get(f"{self.base_url}/ping", timeout=self.timeout)
        r.raise_for_status()
        return True
```

## Step 4 — Connector

```python
# connectors/alerts_connector.py
from __future__ import annotations
from typing import TYPE_CHECKING

from soar_sdk.SiemplifyConnectorsDataModel import AlertInfo
from TIPCommon.base.connector import Connector
from TIPCommon.data_models import BaseAlert
from TIPCommon.extraction import extract_connector_param
from TIPCommon.validation import ParameterValidator
from TIPCommon import context
from TIPCommon.smp_time import get_last_success_time
from TIPCommon.consts import UNIX_FORMAT

from ..core.api_client import ExampleClient

if TYPE_CHECKING:
    pass

PROCESSED_IDS_KEY = "processed_alert_ids"
MAX_CACHE_SIZE = 10_000


def main() -> None:
    ExampleConnector(script_name="Example Alerts Connector").start()


class ExampleConnector(Connector):
    def extract_params(self) -> None:
        self.params.api_root = extract_connector_param(
            siemplify=self.siemplify, param_name="API Root",
            is_mandatory=True, print_value=True,
        )
        self.params.api_key = extract_connector_param(
            siemplify=self.siemplify, param_name="API Key",
            is_mandatory=True, print_value=False,
        )
        self.params.verify_ssl = extract_connector_param(
            siemplify=self.siemplify, param_name="Verify SSL",
            input_type=bool, default_value=True,
        )
        self.params.max_hours_back_str = extract_connector_param(
            siemplify=self.siemplify, param_name="Max Hours Back",
            default_value="4", print_value=True,
        )
        self.params.max_alerts_per_cycle_str = extract_connector_param(
            siemplify=self.siemplify, param_name="Max Alerts Per Cycle",
            default_value="200", print_value=True,
        )

    def validate_params(self) -> None:
        validator = ParameterValidator(self.siemplify)
        self.params.max_hours_back = validator.validate_positive(
            param_name="Max Hours Back", value=self.params.max_hours_back_str,
        )
        self.params.max_alerts_per_cycle = validator.validate_positive(
            param_name="Max Alerts Per Cycle", value=self.params.max_alerts_per_cycle_str,
        )

    def read_context_data(self) -> None:
        self._last_run_ms = get_last_success_time(
            siemplify=self.siemplify,
            offset_with_metric={"hours": self.params.max_hours_back},
            time_format=UNIX_FORMAT,
        )
        self._processed_ids: set[str] = set(
            context.get(self.siemplify, PROCESSED_IDS_KEY, default=[])
        )

    def init_managers(self) -> None:
        self._client = ExampleClient(
            base_url=self.params.api_root,
            api_key=self.params.api_key,
            verify_ssl=self.params.verify_ssl,
        )

    def get_alerts(self) -> list[BaseAlert]:
        raw = self._client.fetch_alerts_since(
            since_unix_ms=self._last_run_ms,
            limit=self.params.max_alerts_per_cycle,
        )
        # Filter duplicates using processed IDs cache
        new_alerts = [a for a in raw if a.id not in self._processed_ids]
        self.logger.info(
            f"Fetched {len(raw)} alerts since {self._last_run_ms}, "
            f"{len(new_alerts)} new after dedup"
        )
        return [
            BaseAlert(raw_data=a.model_dump(), alert_id=a.id)
            for a in new_alerts
        ]

    def create_alert_info(self, alert: BaseAlert) -> AlertInfo:
        info = AlertInfo()
        data = alert.raw_data
        info.alert_id = alert.alert_id
        info.ticket_id = alert.alert_id
        info.display_id = data["title"]
        info.name = data["title"]
        info.rule_generator = "ExampleProduct"
        info.start_time = int(data["created_at_unix_ms"])
        info.end_time = int(data["created_at_unix_ms"])
        info.priority = self._map_severity(data["severity"])
        info.device_vendor = "Example Inc"
        info.device_product = "Example Alerts"
        info.environment = self._env_common.get_environment(data) \
            if hasattr(self, "_env_common") and self._env_common else self.params.environment_name
        info.source_grouping_identifier = alert.alert_id
        info.events = data.get("events", [])
        return info

    def store_alert_in_cache(self, alert: BaseAlert) -> None:
        self._processed_ids.add(alert.alert_id)

    def _save_context_data(self) -> None:
        # Cap the set size to prevent unbounded growth
        capped = list(self._processed_ids)[-MAX_CACHE_SIZE:]
        context.set(self.siemplify, PROCESSED_IDS_KEY, capped)
        self._save_timestamp(self.connector_start_time)

    @staticmethod
    def _map_severity(sev: str) -> int:
        # Align with platform's priority scale (example: 0-100)
        return {"Low": 40, "Medium": 60, "High": 80, "Critical": 100}.get(sev, 50)


if __name__ == "__main__":
    main()
```

## Step 5 — Ontology Mapping

```yaml
# ontology_mapping.yaml (conceptual structure)
source:
  product:
    name: ExampleProduct
    events:
      - event_type: default
        mappings:
          start_time: $.created_at_unix_ms
          end_time: $.created_at_unix_ms
          entities:
            - type: ADDRESS
              field: $.events[*].src_ip
            - type: ADDRESS
              field: $.events[*].dst_ip
            - type: USER
              field: $.events[*].user
            - type: FILEHASH
              field: $.events[*].file_hash
```

## Step 6 — Idempotency Test

```python
def test_connector_idempotent(mock_siemplify_connector, mock_client):
    mock_client.fetch_alerts_since.return_value = [
        AlertPayload(id="1", title="t1", severity="High",
                     created_at_unix_ms=1729000000000, events=[]),
    ]

    # First run
    connector = ExampleConnector(script_name="Test")
    connector._siemplify = mock_siemplify_connector
    connector._client = mock_client
    connector.read_context_data()
    alerts_first = connector.get_alerts()
    assert len(alerts_first) == 1
    connector.store_alert_in_cache(alerts_first[0])
    connector._save_context_data()

    # Second run — same API returns same alert
    connector.read_context_data()
    alerts_second = connector.get_alerts()
    assert len(alerts_second) == 0, "Idempotency broken — re-emitted alert"
```

This is the most important connector test. **Always** include it.

## Step 7 — What You Explained Along the Way

- **`extract_params` / `validate_params` split** — different error messages for missing vs malformed
- **`read_context_data`** — loads processed IDs from persistent context
- **`init_managers`** — separate from context read, for testability
- **`get_alerts` dedups using the cache** — prevents re-emission
- **`create_alert_info` populates `start_time`/`end_time`** — required for case grouping
- **Processed IDs capped at 10k** — prevents unbounded growth
- **Saving `connector_start_time`, not "now"** — overlap-safe windowing

Every one of these is an interview topic from earlier sections.

## Next

→ **[Debug a Failing Connector](debug-connector.md)**
