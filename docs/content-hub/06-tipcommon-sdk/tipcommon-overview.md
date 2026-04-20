# TIPCommon Library

## Definition

> *"TIPCommon is the shared runtime library that every Google SecOps integration depends on. It provides base classes (`Action`, `Connector`, `Job`), parameter extraction + validation helpers, SOAR-platform operation abstractions, time utilities, encryption, caching, OAuth flows, and REST helpers. It wraps the lower-level SOAR SDK (`soar_sdk`) with a consistent, typed, testable API."*

## Where It Lives

```
packages/
├── tipcommon/
│   ├── TIPCommon/
│   │   ├── src/
│   │   │   └── TIPCommon/
│   │   │       ├── __init__.py
│   │   │       ├── adapters/
│   │   │       ├── base/                 # Base classes (Action, Connector, Job)
│   │   │       ├── rest/                 # HTTP + SOAR API + GCP + async clients
│   │   │       ├── cache.py
│   │   │       ├── consts.py
│   │   │       ├── context.py            # Context data management
│   │   │       ├── data_models.py        # BaseAlert, Container, etc.
│   │   │       ├── encryption.py
│   │   │       ├── exceptions.py
│   │   │       ├── execution.py
│   │   │       ├── extraction.py         # extract_action_param, etc.
│   │   │       ├── filters.py
│   │   │       ├── oauth.py
│   │   │       ├── smp_io.py
│   │   │       ├── smp_time.py           # Timestamps + deadlines
│   │   │       ├── soar_ops.py
│   │   │       ├── transformation.py
│   │   │       ├── types.py              # Type aliases (JSON, Entity, etc.)
│   │   │       ├── utils.py
│   │   │       └── validation.py         # ParameterValidator
│   │   └── pyproject.toml
│   └── whls/                             # Pre-built wheels per version
│       ├── TIPCommon-1.0.10-py3-none-any.whl
│       ├── TIPCommon-1.0.11-py2.py3-none-any.whl
│       ├── ...
│       └── TIPCommon-2.0.6-py3-none-any.whl
└── envcommon/                            # EnvironmentCommon (a TIPCommon dependency)
```

## Why Multiple Versions Ship Simultaneously

The repo retains **every historical wheel** under `whls/` because:

1. Deployed integrations pin their version and **breaking them en masse** would require re-certifying hundreds of integrations.
2. Each integration's `pyproject.toml` declares its TIPCommon version via a local `[tool.uv.sources]` entry pointing at the wheel.
3. The runtime is single-version per integration — one integration's 2.0.6 doesn't affect another's 1.1.2.

Over time, integrations are migrated to the latest major. New integrations must pin the latest (enforced by `mp validate`).

## What's in Each Module (Developer Cheat Sheet)

| Module | You'll use when |
|---|---|
| `TIPCommon.base.action` | Writing any new Action |
| `TIPCommon.base.connector` | Writing any new Connector |
| `TIPCommon.base.job` | Writing any new Job |
| `TIPCommon.extraction` | Pulling params from SDK (`extract_action_param`, etc.) |
| `TIPCommon.validation` | Validating params (`ParameterValidator.validate_*`) |
| `TIPCommon.smp_time` | Time/deadline helpers (`get_last_success_time`, `is_approaching_action_timeout`) |
| `TIPCommon.data_models` | `BaseAlert`, `Container`, `ConnectorParamTypes` |
| `TIPCommon.consts` | Format constants (`UNIX_FORMAT`, `DATETIME_FORMAT`, `NONE_VALS`) |
| `TIPCommon.exceptions` | Base exception classes |
| `TIPCommon.utils` | Utility helpers (`camel_to_snake_case`, `get_entity_original_identifier`, `is_first_run`, `is_overflowed`, `platform_supports_db`) |
| `TIPCommon.filters` | `filter_list_by_type` and related predicates |
| `TIPCommon.transformation` | Data transformations (`convert_dict_to_json_result_dict`) |
| `TIPCommon.oauth` | OAuth 2.0 flows + token refresh |
| `TIPCommon.cache` | In-memory + persistent caching |
| `TIPCommon.context` | Connector/job context KV store |
| `TIPCommon.encryption` | Encrypt/decrypt platform-stored secrets |
| `TIPCommon.rest.httplib` | HTTP session with retry/timeout |
| `TIPCommon.rest.soar_api` | SOAR platform API client |
| `TIPCommon.rest.gcp` | Google Cloud auth helpers |
| `TIPCommon.rest.async_soar_platform_clients` | Async variants of SOAR clients |

## The TIPCommon → EnvironmentCommon Relationship

- **TIPCommon depends on EnvironmentCommon** (not the other way around).
- If your integration lists TIPCommon as a dep, you **must also** list EnvironmentCommon.
- EnvironmentCommon can be used **alone** if you only need environment handling.

From the docs: *"If you add TIPCommon to your project, you must also add EnvironmentCommon, as TIPCommon depends on it."*

## Adding TIPCommon to a New Integration

```bash
# from your integration's root folder (e.g., my_integration/)
uv add ../../packages/tipcommon/TIPCommon-2.0.6/TIPCommon-2.0.6-py2.py3-none-any.whl
uv add ../../packages/envcommon/EnvironmentCommon-1.0.2/EnvironmentCommon-1.0.2-py2.py3-none-any.whl
```

This adds them to `pyproject.toml`:

```toml
dependencies = [
    "environmentcommon",
    "tipcommon",
]

[tool.uv.sources]
tipcommon = { path = "../../../../packages/tipcommon/whls/TIPCommon-2.0.6-py3-none-any.whl" }
environmentcommon = { path = "../../../../packages/envcommon/EnvironmentCommon-1.0.2/EnvironmentCommon-1.0.2-py2.py3-none-any.whl" }
```

Then `uv sync` to install.

## Python 2 Compatibility — A Quirk

You'll notice some wheel filenames say `py2.py3` (e.g. `TIPCommon-1.0.11-py2.py3-none-any.whl`) and others say `py3` only. Historically, SOAR supported Python 2 integrations. TIPCommon 1.x kept that compatibility; TIPCommon 2.x dropped it. New integrations are **Python 3.11 only** and use 2.x; legacy wheels remain for old integrations that haven't migrated.

## Future Distribution

From the repo docs: *"We plan to publish these dependencies in the future."* Today they're local wheels. Eventually they'll be on a public index — but for now, you must point at the local path.

## Next

→ **[Base Classes](base-classes.md)**
