# Live Coding — Build an Action

## The Prompt

> *"Write a Content Hub action that enriches IP entities using a mock threat-intel API. The API returns `{score: int, country: str, tags: list[str]}` for a given IP. Mark an entity suspicious if score ≥ 70."*

You have ~30 minutes. Here's the full approach.

## Step 1 — Ask Clarifying Questions (2 min)

Don't just start coding. Show lead-level thinking:

- "Is this a new integration or adding to an existing one?"
- "What auth does the API use — API key, OAuth?"
- "Should I use the TIPCommon 2.x base class pattern?"
- "Do you want me to write the YAML too, or just the Python?"
- "Should I include tests or just the implementation?"

Assume for this walkthrough: new integration, API key auth, TIPCommon 2.x, YAML included, at least one happy-path test.

## Step 2 — Sketch the Structure (1 min)

```
ti_enricher/
├── actions/
│   ├── __init__.py
│   ├── enrich_ip.py
│   └── enrich_ip.yaml
├── core/
│   ├── __init__.py
│   └── ti_client.py
├── tests/
│   ├── conftest.py
│   └── test_actions/
│       └── test_enrich_ip.py
├── definition.yaml
└── pyproject.toml
```

State out loud what each file does.

## Step 3 — Core API Client

```python
# core/ti_client.py
from __future__ import annotations
from typing import TYPE_CHECKING

import requests
from pydantic import BaseModel

if TYPE_CHECKING:
    pass


class TIReport(BaseModel):
    score: int
    country: str
    tags: list[str] = []


class TIClientError(Exception):
    """Base for TI client errors."""


class TIAuthError(TIClientError): ...
class TIRateLimitError(TIClientError): ...
class TINotFoundError(TIClientError): ...


class TIClient:
    def __init__(self, base_url: str, api_key: str, verify_ssl: bool = True):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers["X-API-Key"] = api_key
        self.session.verify = verify_ssl

    def test_connectivity(self) -> bool:
        r = self.session.get(f"{self.base_url}/ping", timeout=10)
        if r.status_code == 401:
            raise TIAuthError("Invalid API key")
        r.raise_for_status()
        return True

    def lookup_ip(self, ip: str) -> TIReport | None:
        r = self.session.get(f"{self.base_url}/ip/{ip}", timeout=10)
        if r.status_code == 401:
            raise TIAuthError("Invalid API key")
        if r.status_code == 404:
            return None
        if r.status_code == 429:
            raise TIRateLimitError("Rate limit exceeded")
        r.raise_for_status()
        return TIReport.model_validate(r.json())
```

## Step 4 — Action (TIPCommon 2.x)

```python
# actions/enrich_ip.py
from __future__ import annotations
from typing import TYPE_CHECKING

from soar_sdk.ScriptResult import (
    EXECUTION_STATE_COMPLETED,
    EXECUTION_STATE_TIMEDOUT,
)
from soar_sdk.SiemplifyDataModel import EntityTypes
from soar_sdk.SiemplifyUtils import (
    convert_dict_to_json_result_dict,
    convert_unixtime_to_datetime,
    unix_now,
)
from TIPCommon.base.action import Action
from TIPCommon.extraction import (
    extract_action_param,
    extract_configuration_param,
)
from TIPCommon.validation import ParameterValidator

from ..core.ti_client import (
    TIAuthError,
    TIClient,
    TIRateLimitError,
)

if TYPE_CHECKING:
    from TIPCommon.base.interfaces import ApiClient
    from TIPCommon.types import Contains

SCRIPT_NAME = "Enrich IP"
PREFIX = "TI_"


def main() -> None:
    EnrichIP(name=SCRIPT_NAME).run()


class EnrichIP(Action[TIClient]):
    def _extract_action_parameters(self) -> None:
        self.params.api_root = extract_configuration_param(
            siemplify=self.soar_action,
            provider_name="TIEnricher",
            param_name="API Root",
            is_mandatory=True,
            print_value=True,
        )
        self.params.api_key = extract_configuration_param(
            siemplify=self.soar_action,
            provider_name="TIEnricher",
            param_name="API Key",
            is_mandatory=True,
            print_value=False,
        )
        self.params.verify_ssl = extract_configuration_param(
            siemplify=self.soar_action,
            provider_name="TIEnricher",
            param_name="Verify SSL",
            input_type=bool,
            default_value=True,
            print_value=True,
        )
        self.params.threshold_str = extract_action_param(
            siemplify=self.soar_action,
            param_name="Suspicious Threshold",
            default_value="70",
            print_value=True,
        )

    def _validate_params(self) -> None:
        validator = ParameterValidator(self.soar_action)
        self.params.threshold = validator.validate_range(
            param_name="Suspicious Threshold",
            value=self.params.threshold_str,
            min_value=0,
            max_value=100,
        )

    def _init_api_clients(self) -> Contains[ApiClient]:
        return TIClient(
            base_url=self.params.api_root,
            api_key=self.params.api_key,
            verify_ssl=self.params.verify_ssl,
        )

    def _perform_action(self, _: None = None) -> None:
        address_entities = [
            e for e in self.soar_action.target_entities
            if e.entity_type == EntityTypes.ADDRESS and not e.is_internal
        ]

        enriched = []
        limited = []
        failed = []
        missing = []
        json_results: dict = {}

        for entity in address_entities:
            if unix_now() >= self.soar_action.execution_deadline_unix_time_ms:
                self.logger.error(
                    f"Timeout approaching: "
                    f"{convert_unixtime_to_datetime(self.soar_action.execution_deadline_unix_time_ms)}"
                )
                self._execution_state = EXECUTION_STATE_TIMEDOUT
                break

            try:
                report = self._api_client.lookup_ip(entity.identifier)
            except TIAuthError:
                raise  # auth error is fatal, re-raise
            except TIRateLimitError:
                limited.append(entity.identifier)
                continue
            except Exception as e:
                self.logger.error(f"Failed on {entity.identifier}: {e}")
                failed.append(entity.identifier)
                continue

            if report is None:
                missing.append(entity.identifier)
                continue

            json_results[entity.identifier] = report.model_dump()
            entity.additional_properties[f"{PREFIX}score"] = str(report.score)
            entity.additional_properties[f"{PREFIX}country"] = report.country
            entity.additional_properties[f"{PREFIX}tags"] = ",".join(report.tags)

            if report.score >= self.params.threshold:
                entity.is_suspicious = True

            enriched.append(entity)

        if enriched:
            self.soar_action.update_entities(enriched)

        self.soar_action.result.add_result_json(convert_dict_to_json_result_dict(json_results))

        # Build output message
        parts = [f"Processed {len(address_entities)} IP entities."]
        if enriched:
            parts.append(f"Enriched: {len(enriched)}")
        if limited:
            parts.append(f"Rate-limited: {', '.join(limited)}")
        if failed:
            parts.append(f"Failed: {', '.join(failed)}")
        if missing:
            parts.append(f"Missing (not found): {', '.join(missing)}")

        self._output_message = "\n".join(parts)
        self._result_value = bool(enriched)
        if not self._execution_state:
            self._execution_state = EXECUTION_STATE_COMPLETED


if __name__ == "__main__":
    main()
```

**Talking points while writing:**

- "I'm filtering entities to ADDRESS + non-internal — TI on internal IPs is wasted quota"
- "Four-bucket error categorization — one bad entity doesn't kill the action"
- "I check `is_internal` and `execution_deadline_unix_time_ms` — production patterns"
- "I prefix enrichment keys with `TI_` to prevent collision with other integrations"
- "Auth error I re-raise — fatal; no point processing more"

## Step 5 — Action YAML

```yaml
name: Enrich IP
description: Enriches IP entities with TI data from the configured provider.
integration_identifier: TIEnricher
parameters:
  - name: Suspicious Threshold
    default_value: "70"
    type: integer
    description: Score at or above which the entity is marked suspicious (0-100).
    is_mandatory: false
dynamic_results_metadata:
  - result_name: JsonResult
    show_result: true
    result_example_path: './resources/enrich_ip_JsonResult_example.json'
creator: Your Name
script_result_name: is_success
```

## Step 6 — Tests

```python
# tests/test_actions/test_enrich_ip.py
from unittest.mock import MagicMock, patch

import pytest


def _make_entity(ip, is_internal=False):
    e = MagicMock()
    e.identifier = ip
    e.entity_type = "ADDRESS"
    e.is_internal = is_internal
    e.is_suspicious = False
    e.additional_properties = {}
    return e


class TestEnrichIP:
    def test_enriches_suspicious_ip(self, mock_siemplify):
        from ..core.ti_client import TIReport
        from ..actions.enrich_ip import EnrichIP

        mock_siemplify.target_entities = [_make_entity("1.2.3.4")]
        mock_client = MagicMock()
        mock_client.lookup_ip.return_value = TIReport(
            score=85, country="RU", tags=["scanner"]
        )

        action = EnrichIP(name="Enrich IP")
        action._soar_action = mock_siemplify
        action._api_client = mock_client
        action._perform_action()

        entity = mock_siemplify.target_entities[0]
        assert entity.is_suspicious is True
        assert entity.additional_properties["TI_score"] == "85"
        assert entity.additional_properties["TI_country"] == "RU"
        mock_siemplify.update_entities.assert_called_once()

    def test_skips_internal_ip(self, mock_siemplify):
        from ..actions.enrich_ip import EnrichIP

        mock_siemplify.target_entities = [_make_entity("10.0.0.1", is_internal=True)]
        mock_client = MagicMock()

        action = EnrichIP(name="Enrich IP")
        action._soar_action = mock_siemplify
        action._api_client = mock_client
        action._perform_action()

        mock_client.lookup_ip.assert_not_called()

    def test_missing_ip_bucket(self, mock_siemplify):
        from ..actions.enrich_ip import EnrichIP

        mock_siemplify.target_entities = [_make_entity("1.2.3.4")]
        mock_client = MagicMock()
        mock_client.lookup_ip.return_value = None  # not found

        action = EnrichIP(name="Enrich IP")
        action._soar_action = mock_siemplify
        action._api_client = mock_client
        action._perform_action()

        entity = mock_siemplify.target_entities[0]
        assert entity.is_suspicious is False
        assert "missing" in action._output_message.lower() or "not found" in action._output_message.lower()
```

## What You Talked About During the Exercise

- Why TIPCommon 2.x base class pattern (Template Method, centralized error handling)
- Why Pydantic model for `TIReport` (validated, typed)
- Why custom exception hierarchy (specific error handling at the action layer)
- Why `is_internal` check (operational quality)
- Why deadline check (timeout awareness)
- Why `print_value=False` on API Key (security)
- Why prefix enrichment keys (collision-prevention)

Covered every topic from Sections 3, 6, 8, 11. This is what "senior fluency" looks like.

## Next

→ **[Live Coding - Connector](coding-connector.md)**
