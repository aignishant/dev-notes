# Actions — Deep Dive

## Definition

> *"An Action is a Python script representing a single task — enrich an IoC, send a message, isolate a host, update an alert, query a database. Actions are invoked from Playbook Steps. They receive input via entities, parameters, or both, and return a script result, a JSON result, entity enrichment, and optionally a predefined widget."*

## Action Inputs — Three Modes

| Mode | How | Example |
|---|---|---|
| **Entities** | `siemplify.target_entities` filtered by `EntityType` | VirusTotal "Enrich IP" pulls IPs already associated with the alert |
| **Parameters** | Action YAML `parameters:` → `extract_action_param()` | VirusTotal "Enrich IOCs" — analyst enters values manually |
| **Combined** | Both | Teams "Send User Message" — user entity + message text |

## Action Outputs — Four Channels

| Output | Set via | Seen in |
|---|---|---|
| **Script Result** | `siemplify.end(msg, result_value, status)` — `result_value` is the scalar that appears in the step output (e.g., `"true"`/`"false"`) | Playbook step output |
| **JSON Result** | `siemplify.result.add_result_json(...)` OR base-class `self.json_results = {...}` | "JSON Result" tab on the step; feeds predefined widgets |
| **Entity Enrichment** | `entity.additional_properties["Prefix_key"] = value` → `siemplify.update_entities([...])` | Entity details pane in alert view |
| **Predefined Widget** | YAML + HTML bound to JSON Result | Alert view rendered HTML |

## Execution States

From `soar_sdk.ScriptResult`:

| Constant | Meaning |
|---|---|
| `EXECUTION_STATE_COMPLETED` | Success |
| `EXECUTION_STATE_FAILED` | Hard error — stop the action |
| `EXECUTION_STATE_TIMEDOUT` | Ran out of time — return partial results |
| `EXECUTION_STATE_INPROGRESS` | Async — platform will re-call the action (long-polling use case) |

## Two Patterns Coexist in the Repo

### Legacy (Siemplify-era, procedural)

```python
from soar_sdk.ScriptResult import EXECUTION_STATE_COMPLETED, EXECUTION_STATE_FAILED
from soar_sdk.SiemplifyAction import SiemplifyAction
from soar_sdk.SiemplifyUtils import output_handler

from ..core.AbuseIPDB import AbuseIPDBInvalidAPIKeyManagerError, AbuseIPDBManager

IDENTIFIER = "AbuseIPDB"
SCRIPT_NAME = "AbuseIPDB - Ping"


@output_handler
def main():
    siemplify = SiemplifyAction()
    siemplify.script_name = SCRIPT_NAME

    api_key = siemplify.extract_configuration_param(siemplify, param_name="Api Key")
    verify_ssl = siemplify.extract_configuration_param(
        siemplify, param_name="Verify SSL", default_value=False, input_type=bool,
    )

    try:
        ipdb = AbuseIPDBManager(api_key, verify_ssl)
        ipdb.test_connectivity()
        status = EXECUTION_STATE_COMPLETED
        output_message = "Connection Established"
        result_value = "true"
    except AbuseIPDBInvalidAPIKeyManagerError:
        status = EXECUTION_STATE_FAILED
        result_value = "false"
        output_message = "Invalid API key was provided. Access is forbidden."
    except Exception as e:
        status = EXECUTION_STATE_FAILED
        result_value = "false"
        output_message = f"General error performing action {SCRIPT_NAME}. Error: {e}"

    siemplify.end(output_message, result_value, status)


if __name__ == "__main__":
    main()
```

### Modern (TIPCommon 2.x base class)

```python
from __future__ import annotations
import json
from typing import TYPE_CHECKING

from TIPCommon.base.action import Action
from TIPCommon.extraction import extract_action_param
from TIPCommon.validation import ParameterValidator

if TYPE_CHECKING:
    from TIPCommon.base.interfaces import ApiClient
    from TIPCommon.types import JSON, Contains

SCRIPT_NAME: str = "Load JSON String to Object"


def main() -> None:
    LoadJsonStringToObject(name=SCRIPT_NAME).run()


class LoadJsonStringToObject(Action):
    def _extract_action_parameters(self) -> None:
        self.params.json_string = extract_action_param(
            siemplify=self.soar_action,
            param_name="Json String",
            is_mandatory=True,
            print_value=True,
        )

    def _validate_params(self) -> None:
        validator: ParameterValidator = ParameterValidator(self.soar_action)
        validator.validate_json(
            param_name="Json String",
            json_string=self.params.json_string,
        )

    def _init_api_clients(self) -> Contains[ApiClient]:
        """No API requests here, skip."""

    def _perform_action(self, _: None = None) -> None:
        json_results: JSON = json.loads(self.params.json_string)
        self.json_results = json_results


if __name__ == "__main__":
    main()
```

## Template Method Pattern — The `run()` Lifecycle

In TIPCommon 2.x, `Action.run()` calls these phases in order:

```
run()
  ├─ _extract_action_parameters()   # Pull params from SDK
  ├─ _validate_params()             # Validate via ParameterValidator
  ├─ _init_api_clients()            # Instantiate core API client
  ├─ _perform_action()              # YOUR business logic
  └─ <base class handles>:
      - json_results → SDK
      - entity updates
      - execution state
      - output message
      - error wrapping
```

Each subclass overrides **only the abstract methods**. The base class handles logging, timing, error-to-state mapping, output finalization. This is the Template Method pattern in GoF terms.

## Entity-Targeting Action — The Canonical Pattern

```python
from soar_sdk.SiemplifyDataModel import EntityTypes
from soar_sdk.SiemplifyUtils import unix_now, convert_unixtime_to_datetime

address_entities = [
    e for e in siemplify.target_entities
    if e.entity_type == EntityTypes.ADDRESS and not e.is_internal
]

enriched_entities, limit_entities, failed_entities, missing_entities = [], [], [], []
json_results = {}

for entity in address_entities:
    # Honor execution deadline
    if unix_now() >= siemplify.execution_deadline_unix_time_ms:
        siemplify.LOGGER.error(
            f"Timed out at {convert_unixtime_to_datetime(siemplify.execution_deadline_unix_time_ms)}"
        )
        status = EXECUTION_STATE_TIMEDOUT
        break

    try:
        report = abuse_ipdb.check_ip(entity.identifier, max_days)
        if not report:
            missing_entities.append(entity.identifier)
            continue

        json_results[entity.identifier] = report.to_json()
        for attrib in dir(report):
            if not attrib.startswith("__"):
                entity.additional_properties[f"AbuseIPDB_{attrib}"] = str(getattr(report, attrib))
        if int(report.abuseConfidenceScore) >= int(sus_threshold):
            entity.is_suspicious = True
        enriched_entities.append(entity)
    except RateLimitError:
        limit_entities.append(entity.identifier)
    except Exception as e:
        siemplify.LOGGER.error(f"Failed {entity.identifier}: {e}")
        failed_entities.append(entity.identifier)

if enriched_entities:
    siemplify.update_entities(enriched_entities)

siemplify.result.add_result_json(convert_dict_to_json_result_dict(json_results))
```

Five best practices baked in:

1. Filter entities by type + `is_internal`
2. Check execution deadline inside the loop
3. Four-bucket categorization of results
4. Prefix every enrichment key (`AbuseIPDB_*`)
5. Aggregate and update in one `update_entities()` call (fewer SDK round trips)

## Action YAML

```yaml
name: Load JSON String to Object
description: Loads a JSON string into an object
integration_identifier: YourIntegrationIdentifier
parameters:
  - name: Json String
    default_value: '{}'
    type: string
    description: 'A JSON string to load as an object'
    is_mandatory: true
dynamic_results_metadata:
  - result_name: JsonResult
    show_result: true
    result_example_path: './resources/load_json_string_to_object_JsonResult_example.json'
creator: Your Name
script_result_name: is_success
```

Key fields:

| Field | What it does |
|---|---|
| `name` | Human-readable action name |
| `integration_identifier` | Must match `identifier` in `definition.yaml` |
| `parameters[]` | Input parameters rendered in SOAR UI |
| `parameters[].type` | `string` / `integer` / `boolean` / `password` / `ddl` (dropdown) / `multi_choice` / `content_url` |
| `parameters[].is_mandatory` | Required in UI |
| `parameters[].is_advanced` | Hidden behind "Advanced" accordion |
| `parameters[].mode` | `regular` (standard) or `script` (allows placeholder expressions) |
| `dynamic_results_metadata[]` | Declares the `JsonResult` schema (and example path) so widgets can bind |
| `script_result_name` | The name shown for the scalar Script Result — typically `is_success` |
| `creator` | Author |

## Action Timeout Awareness

Every action has a platform-enforced deadline (`siemplify.execution_deadline_unix_time_ms`). If you're iterating entities or pages:

- Check the deadline inside the loop
- On breach: return `EXECUTION_STATE_TIMEDOUT` with **partial results already committed**

This prevents the platform from orchestrating "ghost" timeouts where your action died silently and the playbook hangs.

## Error Types — Custom Exception Hierarchy

Idiom: define errors in `core/<integration>.py`:

```python
class AbuseIPDBManagerError(Exception): ...
class AbuseIPDBInvalidAPIKeyManagerError(AbuseIPDBManagerError): ...
class AbuseIPDBRateLimitError(AbuseIPDBManagerError): ...
class AbuseIPDBServerError(AbuseIPDBManagerError): ...
```

Catch the specific subclass for user-facing error messages; catch the base for generic handling; catch `Exception` last for unknown failures.

## Output Message Formatting — Convention

Pattern most of the repo follows:

```
"Successfully enriched N entities in AbuseIPDB.\n\n"
"Failed entities: a, b, c\n"
"Rate-limited entities: d, e\n"
"Missing entities: f, g\n"
```

Multi-line, entity-group summary. The analyst reads this in the playbook step output.

## Next

→ **[Connectors Deep Dive](connectors.md)**
