# Glossary

Alphabetical reference. If you can't recall a term mid-interview, check here.

## A

**Action** — A Python script representing a single on-demand task, invoked from a Playbook step. Lives at `integration/actions/`.

**AlertInfo** — SDK class (`soar_sdk.SiemplifyConnectorsDataModel.AlertInfo`) that connectors build and submit. Contains `alert_id`, `display_id`, `events`, `start_time`, `end_time`, `environment`, etc.

**Apiable** — TIPCommon Protocol combining `ApiClient` + `Authable` — something that makes API calls and can authenticate.

**ApiClient** — TIPCommon Protocol any integration's API client should conform to.

**AsyncConnector** — TIPCommon base class for async-capable connectors. In `TIPCommon.base.connector.async_connector`.

**Authable** — TIPCommon Protocol for auth-capable clients (has `login`, `refresh_token`, `logout`).

## B

**BaseAlert** — TIPCommon data model wrapping a raw alert before it's converted to `AlertInfo`.

**BaseJobRefreshToken** — Specialized `Job` base for OAuth token refresh on a schedule.

**BaseSyncJob** — Specialized `Job` base for bidirectional SOAR ↔ third-party sync with loop-prevention scaffolding.

**Block** — A reusable sub-playbook invoked from a parent via `NestedWorkflowIdentifier`.

## C

**Cache** (TIPCommon) — In-memory per-run KV, via `TIPCommon.cache.Cache`.

**Case** — Platform-created container of related Alerts, grouped by time window + entity overlap.

**CBN** — Configuration-Based Normalization; the parser DSL used in `parser.conf`.

**CLA** — Contributor License Agreement, required before any PR to Content Hub.

**CLI** — The `mp` command-line interface.

**Community integration** — Contributed by an individual, lives under `content/response_integrations/third_party/community/`.

**Connector** — Continuous script that ingests alerts from a third-party product.

**Container** — TIPCommon data model (`TIPCommon.data_models.Container`) — dict-like bag with attribute access. Used for `self.params`.

**Context** (platform) — Persistent encrypted KV store accessible to connectors/jobs via `TIPCommon.context`.

**Custom integration** — Customer-specific integration, not published to public Content Hub, lives at `content/response_integrations/custom/`.

## D

**DataStream** — TIPCommon helper for streaming large datasets.

**definition.yaml** — Integration's identity + top-level config schema.

**dev-env** — `mp dev-env` subcommand for login/push/pull with a dev SOAR instance.

## E

**Entity** — SOAR-level IoC/asset (IP, user, hash, URL, domain) extracted from event data via ontology mapping.

**EntityTypes** — SDK enum (`soar_sdk.SiemplifyDataModel.EntityTypes`). Values: ADDRESS, USER, FILEHASH, URL, HOSTNAME, PROCESS, EMAIL_ADDRESS, MACADDRESS, CVE, etc.

**EnvironmentCommon** — TIPCommon's companion lib for multi-tenant environment resolution.

**EnvironmentHandle** — Object returned by `GetEnvironmentCommonFactory.create_environment_common(...)`.

**Event** — Single normalized log record in UDM format.

**EXECUTION_STATE_COMPLETED / FAILED / TIMEDOUT / INPROGRESS** — SDK constants from `soar_sdk.ScriptResult`.

**extract_action_param / extract_connector_param / extract_job_param / extract_configuration_param** — TIPCommon helpers for pulling parameters from the SDK.

## F

**Feed** — SIEM-side ingestion path (vs Connector on SOAR side); preferred for scale.

## G

**Generic[ApiClient]** — Typing pattern in TIPCommon base classes giving subclasses typed access to their specific API client.

**GetEnvironmentCommonFactory** — EnvironmentCommon factory for per-connector environment resolvers.

**google/** — Top-level directory for Google-developed content.

## H

**HTTP status codes** — standard meanings: 401 auth, 403 permission, 404 not found, 429 rate limit, 500-599 server error.

## I

**identifier** (in `definition.yaml`) — immutable platform-unique key. Cannot be renamed after release.

**integration_identifier** — Field on every action/connector/job YAML that must match the top-level `definition.yaml` identifier.

**integration_testing** — Test harness package providing mock SOAR platform objects.

**IoC** — Indicator of Compromise (IP, hash, domain, URL).

**is_internal** — Entity property marking internal-to-tenant assets; TI enrichment actions should usually skip these.

**is_suspicious** — Entity property set True by actions that detect malicious indicators.

## J

**Job** — Cron-like script for state sync between SOAR and a third party. Does not create alerts.

**JSON Result** — Action output channel; set via `self.json_results = {...}` or `siemplify.result.add_result_json(...)`. Rendered in playbook step output and consumed by widgets.

## L

**last_success_time** — Context value connectors/jobs read at start to bound their query window.

**LogType** — SecOps canonical identifier for a log source (APACHE, AZURE_AD, GCP_CLOUDAUDIT). Must be known to SecOps or pre-approved.

## M

**Manual trigger** — Playbook trigger fired by analyst click.

**`mp`** — The marketplace CLI.

**MSSP** — Managed Security Service Provider — customers running SOAR for their own end-customers.

## N

**NestedWorkflowIdentifier** — Parameter in a Block step pointing at another playbook's identifier. The reuse mechanism.

## O

**Ontology** — Rules that map event fields to entity types. Three levels: Source → Product → Event (top-down inheritance).

**ontology_mapping.yaml** — File in the integration root containing the rules. REQUIRED if the integration has a connector.

**output_handler** — Legacy SDK decorator wrapping procedural `main()` actions. Replaced by TIPCommon 2.x base classes.

**Overflow** — Platform's alert-flood protection. Connectors check `is_overflowed(alert_info)` before emitting.

**overviews.yaml** — Playbook's catalog-facing metadata (short description, detailed, use case, prerequisites).

## P

**ParameterValidator** — TIPCommon class providing typed validation methods (`validate_json`, `validate_range`, `validate_email`, etc.).

**Parser** — CBN file that normalizes raw logs into UDM events.

**parser.conf** — The parser code file.

**Partner integration** — Contributed by an official vendor, lives under `content/response_integrations/third_party/partner/`.

**password** (parameter type) — `definition.yaml` field type that stores value encrypted at rest and masks in logs.

**Ping action** — Mandatory connectivity-test action in every integration.

**Playbook** — Automated YAML-defined workflow: trigger + steps + widgets.

**power_ups/** — Google utility packs (`email_utilities`, `template_engine`, etc.) — reusable building blocks, not vertical integrations.

**print_value** — Parameter on extraction helpers. **Must be False for secrets.**

**Processed IDs cache** — Connector state tracking alerts already ingested; key mechanism for idempotency.

**pyproject.toml** — Per-integration dependencies + tool config.

## R

**Ready for review** — PR state indicating "please review now," as opposed to Draft.

**release_notes.yaml** — Per-version changelog file in each integration/playbook.

**result_value** — Scalar Script Result from an action; typically `"true"` / `"false"` or an integer/ID.

**Retry-After** — HTTP header on 429 responses indicating seconds to wait before retry.

**Ruff** — Rust-based linter + formatter. Replaces Black + flake8 + isort + pyupgrade.

## S

**`safe_rendering`** — Widget YAML field controlling HTML sanitization. `true` = sanitize + block JS.

**script_result_name** — Action YAML field naming the Script Result (usually `is_success`).

**Semver** — Semantic versioning; bump MAJOR for breaking, MINOR for feature, PATCH for bugfix.

**SiemplifyAction / SiemplifyConnectorExecution / SiemplifyJob** — Legacy-named SDK classes used by actions/connectors/jobs.

**SIEM** — Security Information and Event Management — ingest + detection side.

**SOAR** — Security Orchestration, Automation, and Response — incident response side.

**Source / Product / Event** — Three levels of ontology hierarchy.

**STAR** — Situation / Task / Action / Result — behavioral answer structure.

**start_time / end_time** — UDM / AlertInfo fields critical for case grouping.

**Squash merge** — Repo's merge strategy; multiple PR commits become one on `main`.

## T

**Template Method** — GoF design pattern; TIPCommon base classes use it. Base defines execution skeleton, subclass fills phases.

**TIPCommon** — The shared runtime library; wraps SDK with typed, tested, base-class API.

**Trigger** — Playbook's entry point: Alert, Entity, or Manual.

**Ty** — Astral's type checker. Replaces mypy in `mp check --static-type-check`.

**TypedDict** — typing construct for dict-shaped data with known keys.

## U

**UDM** — Unified Data Model; SecOps' canonical event schema.

**uv** — Rust-backed Python package manager from Astral. Project manager + env manager + tool manager.

**uv.lock** — Lockfile committed per integration for reproducible builds.

## V

**Validate Parsers (Stage 1)** — Automatic parser validation in CI.

**Validate Google & Parsers (Stage 2)** — Manually triggered parser validation against live SecOps.

**verify_ssl** — Integration config param; should default to True.

## W

**Widget** — HTML/CSS/JS UI component. Two kinds: **Predefined** (integration-level, action-bound, rendered in alert view) and **Playbook** (rendered in case overview).

**wmp** — Windows variant of `mp` (avoids Windows's built-in alias).

## Next

→ **[Red-Flag Answers to Avoid](red-flags.md)**
