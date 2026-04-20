# Integration Structure

## Full Anatomy

```
integration_name/
├── actions/
│   ├── __init__.py
│   ├── action1.py
│   ├── action1.yaml
│   ├── action2.py
│   └── action2.yaml
│
├── core/
│   ├── __init__.py
│   ├── integration_client.py        # THE API client
│   └── data_models/
│       ├── data_model_1.py
│       └── data_model_2.py
│
├── connectors/
│   ├── __init__.py
│   ├── connector1.py
│   └── connector1.yaml
│
├── widgets/
│   ├── widget1.html
│   └── widget1.yaml
│
├── jobs/
│   ├── __init__.py
│   ├── job1.py
│   └── job1.yaml
│
├── resources/
│   ├── action1_JsonResult_example.json
│   ├── image.png                    # PNG logo for catalog
│   └── logo.svg                     # SVG logo for product UI
│
├── tests/
│   ├── __init__.py
│   ├── common.py                    # shared test constants + mock data
│   ├── conftest.py                  # pytest fixtures
│   ├── core/
│   │   ├── __init__.py
│   │   ├── session.py               # mock HTTP session
│   │   └── product.py               # mock third-party product
│   ├── test_defaults/
│   │   ├── __init__.py
│   │   └── test_imports.py          # "can we import everything?"
│   └── test_actions/
│       ├── __init__.py
│       ├── test_action1.py
│       └── test_action2.py
│
├── __init__.py
├── .python-version                  # "3.11\n"
├── ontology_mapping.yaml            # REQUIRED if connector exists
├── definition.yaml                  # Integration identity + config schema
├── pyproject.toml                   # uv deps + tool config
├── release_notes.yaml               # Per-version changelog
└── uv.lock                          # Reproducible deps
```

## File Purpose Table (Deep Version)

| File | Must-contain | Used by |
|---|---|---|
| `__init__.py` (root) | Empty | Python import system |
| `.python-version` | `3.11` | uv, IDE |
| `definition.yaml` | `identifier`, `name`, `parameters`, `categories`, `svg_logo_path`, `image_path` | SOAR UI, `mp` validator |
| `ontology_mapping.yaml` | Source/Product/Event mapping rules | Platform entity extractor |
| `pyproject.toml` | name, description, version, `[project.dependencies]`, `[tool.uv.sources]`, `[tool.ruff]`, `[tool.ty]`, `[tool.pytest.ini_options]` | uv, ruff, ty, pytest |
| `release_notes.yaml` | List of change entries with `integration_version`, `item_name`, `item_type`, `description`, flags | `mp build`, publishing pipeline |
| `uv.lock` | Generated — never hand-edit | uv |
| `actions/*.py` | Action class | Platform runtime |
| `actions/*.yaml` | Action input params + output schema + metadata | SOAR UI |
| `connectors/*.py` | Connector class | Platform runtime (cron) |
| `connectors/*.yaml` | Connector params + metadata | SOAR UI |
| `jobs/*.py` | Job class | Platform runtime (cron) |
| `jobs/*.yaml` | Job params + metadata | SOAR UI |
| `core/*.py` | API client, auth, data models, constants | All scripts |
| `widgets/*.html` + `*.yaml` | HTML + widget binding | Alert view |
| `resources/logo.svg` + `image.png` | Branding | Catalog UI |
| `resources/<action>_JsonResult_example.json` | Sample JSON output for widget schema | Widget renderer |
| `tests/` | pytest suite | CI |

## release_notes.yaml Fields

```yaml
- description: Added a new action 'Check IP Reputation'.
  integration_version: 2.0
  item_name: Check IP Reputation
  item_type: Action
  new: true
  publish_time: '2025-10-15'
```

**Flag glossary:**

| Flag | Meaning |
|---|---|
| `new: true` | New component (or 1.0 initial release) — shown as "New!" in the hub |
| `deprecated: true` | Phased out but still functional |
| `removed: true` | Completely removed |
| `regressive: true` | **Breaks existing functionality** — customers must update playbooks |

Flags default to `false` if omitted. Missing `publish_time` or using a non-YYYY-MM-DD format fails `mp validate`.

## pyproject.toml — Real Example Shape

```toml
[project]
name = "abuse_ipdb"
version = "4.0.0"
description = "AbuseIPDB integration"
readme = "README.md"
requires-python = ">=3.11,<3.12"
dependencies = [
    "requests>=2.31.0",
    "tipcommon",
    "environmentcommon",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "integration_testing",
    "soar-sdk",
]

[tool.uv.sources]
tipcommon = { path = "../../../../packages/tipcommon/whls/TIPCommon-2.0.6-py3-none-any.whl" }
environmentcommon = { path = "../../../../packages/envcommon/EnvironmentCommon-1.0.2/EnvironmentCommon-1.0.2-py2.py3-none-any.whl" }
integration_testing = { path = "../../../../packages/integration_testing_whls/..." }
soar-sdk = { git = "https://github.com/chronicle/soar-sdk.git" }

[tool.ruff]
line-length = 88
# extends the root ruff.toml

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Why `soar-sdk` is dev-only:** it's packaged with the SOAR runtime. If you list it in production deps, your integration zip will include it and conflict with the platform's version at runtime.

## Required Implementation Checklist

Every shippable integration has:

1. A core **API client class** with authentication
2. A **Ping action** for connectivity
3. At least **one service-specific action** that demonstrates value
4. **Tests** for all components
5. **Error handling** for API failures (including auth, rate limit, timeouts)
6. **Type hints** throughout

Skip any one of these and the PR gets bounced.

## Naming Rules

- All filenames **snake_case** — no exceptions
- Python class names **PascalCase**
- YAML files match the Python filename: `check_ip_reputation.py` + `check_ip_reputation.yaml`
- The action's `name:` in YAML is **human-readable with spaces**: `Check IP Reputation`
- The action's `script_result_name:` is typically `is_success` (boolean true/false as string)

## Module Nesting in `core/`

`core/` may contain subfolders, but **all Python filenames must be unique across the entire integration** — even across nested folders. This is a platform constraint: the runtime flattens imports.

## Next

→ **[Actions Deep Dive](actions.md)**
