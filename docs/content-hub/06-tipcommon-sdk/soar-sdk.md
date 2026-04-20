# SOAR SDK

## Definition

> *"The Google SecOps SOAR SDK is the low-level library that exposes the SOAR platform's runtime surface to integration scripts — `SiemplifyAction`, `SiemplifyConnectorExecution`, `SiemplifyJob`, entity data models, script-result constants. TIPCommon's base classes wrap the SDK to give a cleaner, typed, tested API. Integration code rarely calls the SDK directly; it goes through TIPCommon."*

## The `Siemplify*` Naming

You'll see these everywhere:

- `SiemplifyAction` — the object actions receive
- `SiemplifyConnectorExecution` — the object connectors receive
- `SiemplifyJob` — the object jobs receive
- `SiemplifyDataModel.EntityTypes` — entity type enums
- `SiemplifyUtils` — utility helpers (`output_handler`, `unix_now`, `convert_unixtime_to_datetime`)
- `SiemplifyConnectorsDataModel.AlertInfo` — the alert contract

The name is legacy — Google acquired Siemplify in 2022 and rebranded to Chronicle SOAR, then merged with SIEM into Google SecOps in 2024. Class names stayed for back-compat.

## The SDK is NOT in the Content Hub Repo

The SDK source lives in Google's backend — not this repo. The repo docs explicitly warn:

> *"The SOAR SDK is currently a **work in progress** and is intended for **reference only**. The code provided in the SDK does not reflect the code that is being used in the Google SecOps SOAR product."*

A reference version is on GitHub: `https://github.com/chronicle/soar-sdk.git`. It's for IDE autocompletion, type checking, and documentation — **not** runtime. At runtime, the platform provides its own SDK build.

## How to Add the SDK to Your Integration

```bash
# from your integration's root folder
uv add --dev git+https://github.com/chronicle/soar-sdk.git
```

**Critical:** it must go in the **dev dependencies** group, not production. If you add it to production, the integration zip ships with its own (reference-only) SDK copy, which conflicts with the platform's actual SDK at runtime and breaks the integration.

Your `pyproject.toml` should end up with:

```toml
[dependency-groups]
dev = [
    # ... other dev dependencies ...
    "soar-sdk",
]

[tool.uv.sources]
soar-sdk = { git = "https://github.com/chronicle/soar-sdk.git" }
```

Then `uv sync --dev` to install.

## Alternative: IDE Source Root Setup

If you prefer source-level visibility over installed wheel:

```bash
git clone https://github.com/chronicle/soar-sdk.git
```

Then in PyCharm:

1. Settings → Project → Project Structure
2. Add Content Root → select cloned soar-sdk folder
3. Mark the `src` folder as Sources (blue folder icon)

IDE now resolves imports + autocompletion without installing the package.

## Key SDK Classes You'll Touch

### `SiemplifyAction`

```python
siemplify = SiemplifyAction()
siemplify.script_name = "My Action"

# Extract parameters
api_key = siemplify.extract_configuration_param(siemplify, param_name="Api Key")
some_param = siemplify.extract_action_param("Some Param", is_mandatory=True, input_type=int)

# Logging
siemplify.LOGGER.info("message")
siemplify.LOGGER.error("failure")
siemplify.LOGGER.exception(exc)

# Entity access
for entity in siemplify.target_entities:
    ...

# Enrichment commit
siemplify.update_entities(enriched_entities)

# JSON result
siemplify.result.add_result_json(json_results_dict)

# Deadline
if unix_now() >= siemplify.execution_deadline_unix_time_ms:
    # timed out

# Finalize
siemplify.end(output_message, result_value, execution_state)
```

### `SiemplifyConnectorExecution`

```python
siemplify = SiemplifyConnectorExecution()

# Parameters from connector YAML
max_alerts = siemplify.extract_connector_param("Max Alerts Per Cycle", input_type=int)

# Context (persistent state)
last_ts = siemplify.fetch_timestamp(datetime_format=True)
siemplify.save_timestamp(new_unix_timestamp=now)

# Submit alerts
siemplify.return_package(alerts_list=processed_alerts)
```

### `SiemplifyJob`

```python
soar_job = SiemplifyJob()

# Query cases
case_ids = soar_job.get_cases_ids_by_filter(
    status=CaseFilterStatusEnum.OPEN,
    update_time_from_unix_time_in_ms=last_ts,
    tags=["triage-pending"],
    environments=["production"],
)

# Mutate a case
soar_job.add_comment("Job auto-comment", case_id, alert_id)
soar_job.update_case_priority(case_id, new_priority)

# Save timestamp
soar_job.save_timestamp(...)
```

### `EntityTypes` (Constants)

```python
from soar_sdk.SiemplifyDataModel import EntityTypes

EntityTypes.ADDRESS
EntityTypes.USER
EntityTypes.FILEHASH
EntityTypes.URL
EntityTypes.HOSTNAME
EntityTypes.PROCESS
EntityTypes.EMAIL_ADDRESS
EntityTypes.MACADDRESS
EntityTypes.THREATCAMPAIGN
EntityTypes.CVE
```

### `ScriptResult` Execution States

```python
from soar_sdk.ScriptResult import (
    EXECUTION_STATE_COMPLETED,
    EXECUTION_STATE_FAILED,
    EXECUTION_STATE_TIMEDOUT,
    EXECUTION_STATE_INPROGRESS,
)
```

### `AlertInfo`

```python
from soar_sdk.SiemplifyConnectorsDataModel import AlertInfo

info = AlertInfo()
info.alert_id = "..."
info.display_id = "..."
info.ticket_id = "..."
info.name = "..."
info.rule_generator = "..."
info.start_time = ...
info.end_time = ...
info.priority = ...
info.device_vendor = "..."
info.device_product = "..."
info.environment = "..."
info.source_grouping_identifier = "..."
info.events = [...]
```

## When to Use the SDK Directly vs TIPCommon

| Do | Use |
|---|---|
| Extract parameters | `TIPCommon.extraction.*` (wraps `extract_action_param`) |
| Validate params | `TIPCommon.validation.ParameterValidator.*` |
| Logging | `TIPCommon`'s `ScriptLogger` protocol (wraps `siemplify.LOGGER`) |
| Time helpers | `TIPCommon.smp_time` (wraps SDK time utils) |
| Build AlertInfo | SDK directly (TIPCommon has `BaseAlert` but the final `AlertInfo` is SDK-native) |
| Entity iteration | SDK directly (`siemplify.target_entities`) |
| Final `siemplify.end()` | TIPCommon base class handles this for you |

**Rule of thumb:** If TIPCommon wraps it, prefer TIPCommon. If not, use the SDK directly.

## SDK Version Skew

TIPCommon is pinned per-integration; the SDK is **not** — the platform provides whatever SDK version is active at runtime. This means:

- If the SDK makes a backwards-incompatible change, every TIPCommon version that relied on the old contract breaks.
- TIPCommon's job is to **shield integrations from SDK churn** — abstract the SDK enough that integrations don't care.
- When the SDK changes, TIPCommon maintainers update the wrapper first; integrations move to the new TIPCommon version at their own pace.

This is **why you never skip TIPCommon for direct SDK access** — the indirection is the whole point.

## Next

→ **[Interview Q&A](questions.md)**
