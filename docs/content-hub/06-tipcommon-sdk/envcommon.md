# EnvironmentCommon

## Definition

> *"EnvironmentCommon is TIPCommon's companion library that handles environment-specific configuration — most importantly, resolving which SOAR environment an ingested alert or event belongs to in a multi-tenant deployment. Connectors use it to tag each alert with the right environment so case management is correctly scoped."*

## Where It Lives

```
packages/envcommon/
├── EnvironmentCommon/
├── EnvironmentCommon-1.0.1/
│   └── EnvironmentCommon-1.0.1-py2.py3-none-any.whl
└── EnvironmentCommon-1.0.2/
    └── EnvironmentCommon-1.0.2-py2.py3-none-any.whl
```

Like TIPCommon, multiple versions are shipped as wheels.

## The Core Problem It Solves — Multi-Tenant Environments

A single SOAR tenant can serve multiple **environments** (customer BU, region, subsidiary). When a connector ingests alerts, each alert must be tagged with the right environment:

- Analyst for BU-A sees only BU-A alerts
- SLAs differ per environment
- Playbook permissions scope per environment

How does the connector know which env an alert belongs to?

## The Three Inputs

Connectors typically expose three parameters:

| Parameter | Purpose |
|---|---|
| `Environment Field Name` | Which event field carries the environment value (e.g., `dept`, `customer_id`) |
| `Environment Regex Pattern` | Regex that extracts/normalizes the env value from the field |
| `Default Environment` | Fallback if no match |

EnvironmentCommon bundles these three into one resolver.

## Usage in a Connector

```python
from EnvironmentCommon import EnvironmentHandle, GetEnvironmentCommonFactory

class MyConnector(Connector):
    def init_managers(self) -> None:
        self._env_common: EnvironmentHandle = GetEnvironmentCommonFactory.create_environment_common(
            siemplify=self.siemplify,
            environment_field_name=self.params.environment_field_name,
            environment_regex_pattern=self.params.environment_regex_pattern,
            default_environment=self.params.default_environment,
        )

    def create_alert_info(self, alert: BaseAlert) -> AlertInfo:
        info = AlertInfo()
        # ... populate other fields ...
        info.environment = self._env_common.get_environment(alert.raw_data)
        return info
```

That one call — `self._env_common.get_environment(event_dict)` — resolves the env based on all three inputs. No regex code in your connector.

## Environment Resolution Logic (Conceptual)

```python
def get_environment(event: dict) -> str:
    # 1. Extract the raw value from the configured field
    raw_value = event.get(self.env_field_name)
    if raw_value is None:
        return self.default_environment

    # 2. Apply the regex pattern
    match = re.search(self.env_regex_pattern, str(raw_value))
    if not match:
        return self.default_environment

    # 3. Return the first capture group (or full match)
    return match.group(1) if match.groups() else match.group(0)
```

Customers configure the connector's params to match their taxonomy.

## Jobs Use It Too

Jobs that iterate cases by environment use:

```python
case_ids = self.soar_job.get_cases_ids_by_filter(
    ...
    environments=[self.params.environment_name],
)
```

The job's `environment_name` param is typically set per-scheduler-instance so one job runs per env, keeping scope tight.

## Standalone Usage

You can use EnvironmentCommon **without** TIPCommon (it has no upward dependency). Uncommon, but valid:

```bash
# In your integration:
uv add ../../packages/envcommon/EnvironmentCommon-1.0.2/EnvironmentCommon-1.0.2-py2.py3-none-any.whl
# Without also adding TIPCommon
```

Use case: a script that only needs environment resolution and nothing else.

## Why EnvironmentCommon Is Separate From TIPCommon

- **Cleaner dep graph** — TIPCommon doesn't force you to inherit env handling if you don't need it
- **Independent versioning** — env resolution logic changes rarely, TIPCommon changes often
- **Smaller footprint** — pure env handling is a few hundred LoC; TIPCommon is thousands

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Forgetting to set `environment` on `AlertInfo` | Alert lands in default env → visible to wrong tenants |
| Hardcoding env name in connector | Breaks multi-tenant; use EnvironmentCommon properly |
| Regex not capturing group | `env_common.get_environment` falls back to default silently |
| Field name typo in `environment_field_name` | Always returns default — hard to debug. Log raw field access. |
| Forgetting EnvironmentCommon when using TIPCommon | TIPCommon depends on it — `uv sync` will fail |

## Next

→ **[SOAR SDK](soar-sdk.md)**
