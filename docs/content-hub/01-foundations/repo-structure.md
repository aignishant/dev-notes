# Repository Structure

Know this layout like your phone number. Interviewers open a 3-minute "walk me through the repo" question in ~70% of sessions for this role.

## Top-Level Layout

```
content-hub/
├── content/                       # All deliverable content
│   ├── response_integrations/
│   │   ├── google/                # Google-developed integrations
│   │   ├── third_party/
│   │   │   ├── community/         # Community-contributed (57+)
│   │   │   └── partner/           # Partner-supported (31+)
│   │   └── power_ups/             # Google utility packs (email, git_sync, template_engine, etc.)
│   ├── playbooks/
│   │   ├── google/
│   │   └── third_party/
│   │       ├── community/
│   │       └── partner/
│   └── parsers/
│       └── third_party/
│           ├── community/
│           ├── partnerA/
│           └── partnerB/
│
├── packages/                      # Shared libraries + tooling
│   ├── tipcommon/                 # Core runtime library (multiple versions)
│   │   ├── TIPCommon/             # Source
│   │   └── whls/                  # Pre-built wheels for each version
│   ├── envcommon/                 # EnvironmentCommon — dep of TIPCommon
│   ├── mp/                        # The CLI
│   ├── integration_testing/       # "Black-box" local test harness
│   └── integration_testing_whls/  # Wheels
│
├── tools/                         # One-off utility scripts
│   ├── migration/                 # Legacy → new format migration
│   └── parsers/                   # Parser validation scripts
│
├── docs/                          # Official documentation
│   ├── content_deep_dive/
│   │   ├── response_integrations/
│   │   ├── playbooks/
│   │   └── parsers/
│   ├── getting_started/
│   ├── tools_and_sdk/
│   └── resources/                 # Images, assets
│
├── .github/                       # Workflows + Action definitions
│   └── actions/
│       └── custom-integration-push/
│
├── LICENSE                        # Apache 2.0
├── README.md
└── ruff.toml                      # Root linting config
```

## The "Content" Taxonomy (Memorize This Split)

| Dimension | Split |
|---|---|
| **Content type** | `response_integrations/` • `playbooks/` • `parsers/` |
| **Authorship** | `google/` • `third_party/community/` • `third_party/partner/` • `power_ups/` |

So an integration lives at a full path like:
```
content/response_integrations/third_party/community/abuse_ipdb/
```

That's the vocabulary — *community response integration called `abuse_ipdb`*.

## Anatomy of a Single Integration

Take `abuse_ipdb/` as the canonical example. From the deep-dive docs, every integration follows:

```
abuse_ipdb/
├── actions/               # Action scripts (the most common content)
│   ├── __init__.py
│   ├── Ping.py            # Mandatory connectivity test
│   ├── Ping.yaml
│   ├── CheckIpReputation.py
│   └── CheckIpReputation.yaml
├── core/                  # Shared code: API client, auth, data models
│   ├── __init__.py
│   ├── AbuseIPDB.py       # The API manager class
│   └── data_models/
├── connectors/            # (Optional) Continuous alert ingestion
├── jobs/                  # (Optional) Sync scripts
├── widgets/               # (Optional) HTML widgets for alert view
├── tests/                 # pytest suite
│   ├── __init__.py
│   ├── common.py
│   ├── conftest.py
│   ├── core/              # Mocked third-party product
│   ├── test_defaults/
│   │   └── test_imports.py
│   └── test_actions/
├── resources/             # logo.svg, image.png, example JSON results
├── __init__.py
├── .python-version        # 3.11
├── definition.yaml        # Integration metadata + config schema
├── ontology_mapping.yaml  # Required if there's a connector
├── pyproject.toml         # uv-managed deps
├── release_notes.yaml     # Per-version changelog
└── uv.lock                # Pinned deps
```

## What Lives Where — The File Purpose Table

| File | Purpose | Required? |
|---|---|---|
| `definition.yaml` | Integration identity + top-level params (API key, URL, etc.) | ✅ Always |
| `pyproject.toml` | Dependencies + tool config (pytest, ruff, ty) | ✅ Always |
| `uv.lock` | Lock file with exact pinned versions | ✅ Always |
| `release_notes.yaml` | Semantic changelog per version | ✅ Always |
| `.python-version` | Python version (3.11) | ✅ Always |
| `ontology_mapping.yaml` | Event → Entity mapping rules | ✅ **If** a connector exists |
| `<action>.yaml` | Action's UI schema: params, result metadata | ✅ Per action |
| `<action>.py` | Action implementation | ✅ Per action |
| `core/*.py` | Shared API client + auth + data models | Recommended |
| `tests/` | pytest tests | Recommended (PR gate) |

## The Packages Directory — The Real Backbone

This is what separates the "wrote an integration" candidate from the "led the project" candidate.

```
packages/
├── tipcommon/                 # Runtime library every integration uses
│   ├── TIPCommon/src/         # Latest source (2.0.6)
│   └── whls/                  # 1.0.10 → 2.0.6 wheels kept for back-compat
├── envcommon/                 # Environment-handling layer
├── mp/                        # The CLI developers live in
├── integration_testing/       # Pytest fixtures + mock SOAR platform
└── integration_testing_whls/
```

### Why Multiple TIPCommon Versions?

Production integrations deployed long ago may still target TIPCommon `1.0.14`. Changing the platform-default TIPCommon would break them. So the repo ships **every historical wheel** under `packages/tipcommon/whls/`, and each integration pins its own version in `pyproject.toml` via a local `path = "../../packages/tipcommon/..."` source.

## Tools Directory

- `tools/migration/` — scripts to migrate legacy integration format to current
- `tools/parsers/` — parser validation (see Section 5)

These are **contributor tools**, not customer-facing. If asked about them, frame as "developer ergonomics".

## Docs Directory

```
docs/
├── getting_started/        # Setup env, core concepts
├── content_deep_dive/      # Per-content-type deep dives (authoritative reference)
├── tools_and_sdk/          # mp, SDK, TIPCommon docs
├── resources/              # Diagrams, screenshots
├── code_of_conduct.md
├── contributing.md
├── github_actions.md
└── navigation.md           # Meta-overview of the repo
```

## The GitHub Actions Directory

```
.github/
└── actions/
    └── custom-integration-push/   # Reusable Action: push a custom integration to a customer's SOAR
```

This Action (`chronicle/content-hub/actions/custom-integration-push@main`) is what customers use in *their own* repos to auto-sync custom integrations. Know this — it's a common "customer-side" question.

## Red-Flag Repo Questions & Fast Answers

| Interviewer asks… | Your sharp answer |
|---|---|
| "Where does a new community integration go?" | `content/response_integrations/third_party/community/<snake_case_name>/` |
| "What's the difference between `google/` and `power_ups/`?" | `google/` = full integrations Google ships; `power_ups/` = internal utility packs (email, template engine, git sync) usable as building blocks |
| "Why does the repo ship multiple TIPCommon wheels?" | Back-compat: deployed integrations pin older versions and breaking them would require mass re-certification |
| "Where do parsers live?" | `content/parsers/third_party/community/<VENDOR>_<PRODUCT>/cbn/` |
| "Where are tests co-located?" | Inside each integration at `<integration>/tests/`, not at the repo root |

## Next

→ **[Beginner Interview Q&A](questions.md)**
