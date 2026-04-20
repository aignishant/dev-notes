# Response Integrations — Interview Q&A

25 questions across Beginner → Lead. If you can handle these, you own the integration surface of the interview.

---

## Beginner

### Q1. What files are mandatory for every integration?

`__init__.py`, `.python-version` (3.11), `definition.yaml`, `pyproject.toml`, `uv.lock`, `release_notes.yaml`, a Ping action (`.py` + `.yaml`), a core API client, `resources/logo.svg`, `resources/image.png`. Plus `ontology_mapping.yaml` if the integration has a connector.

### Q2. Why must `identifier` in `definition.yaml` never change?

It's the stable key customer playbooks reference. Renaming breaks every downstream playbook instance. Forbidden.

### Q3. What's the difference between `name` and `identifier` in `definition.yaml`?

`identifier` is the **immutable key** used internally (PascalCase, e.g. `AbuseIPDB`). `name` is the **mutable display label** shown in UI — can be changed for cosmetics without breaking anything.

### Q4. Why use `type: password` for API keys?

It's encrypted at rest, masked in logs, and never exposed via API. `type: string` stores plaintext — a serious security flaw.

---

## Intermediate

### Q5. Walk me through the lifecycle of a TIPCommon 2.x Action.

`Action.run()` calls in order:

1. `_extract_action_parameters()` — pull params from SDK
2. `_validate_params()` — via `ParameterValidator`
3. `_init_api_clients()` — build the API client from `core/`
4. `_perform_action()` — business logic, sets `self.json_results`, updates entities
5. Base class finalizes: JSON result → SDK, entity updates, execution state, output message, error wrapping

Template Method pattern — base class owns the skeleton, subclass fills the specific methods.

### Q6. What does `@output_handler` do in legacy actions?

It's the `SiemplifyUtils` decorator that wraps the action's `main()` with:

- Standard logging (start/finish banners)
- Exception catching → FAILED status
- Output streaming to the platform

In TIPCommon 2.x base classes, the base `run()` method replaces this entirely — you don't need `@output_handler`.

### Q7. How does an action know what entities to operate on?

Via `siemplify.target_entities` — a list populated by the platform based on the playbook step's entity scope configuration. You filter by `entity_type` and `is_internal` inside the action.

### Q8. What does `result_value` represent and what are typical values?

It's the **scalar Script Result** exposed to subsequent playbook steps. Convention: `"true"` / `"false"` strings for success-style actions. Some actions return a count (`"5"`), an ID, or an entity type. Declared as `script_result_name: is_success` in the action YAML.

### Q9. What's the difference between `siemplify.end()` and `self.json_results = {...}`?

- `siemplify.end(msg, result_value, status)` — **terminal call** in legacy actions; sets output message, script result, and execution state.
- `self.json_results = {...}` (in TIPCommon 2.x) — sets the JSON result; the base class's `run()` handles the terminal call.

### Q10. Why does the repo ship both legacy (procedural) and modern (class-based) action styles?

Back-compat. Rewriting 100+ integrations en masse is risky. Every new integration must use 2.x, and we migrate legacy integrations opportunistically — typically when touching them for feature work. It's a planned tech-debt reduction stream.

### Q11. How do you handle the execution deadline in an action?

Check `unix_now() >= siemplify.execution_deadline_unix_time_ms` inside entity/page iteration loops. On breach, log, set `status = EXECUTION_STATE_TIMEDOUT`, break out, and return with partial results. Never let the platform kill the action mid-write.

### Q12. What are the four entity result buckets and why?

`enriched_entities`, `limit_entities` (rate-limited), `failed_entities` (other errors), `missing_entities` (not found upstream). Rationale: per-entity partial failure must NOT kill the whole action. Aggregating into buckets lets the output message give analysts an exact per-entity breakdown.

---

## Connectors

### Q13. What's the contract of a connector — what does it MUST produce and MUST NOT produce?

**MUST** produce: a list of `AlertInfo` objects with populated `alert_id`, `display_id`, `events`, `start_time`, `end_time`, and correctly set `environment`.

**MUST NOT** produce: duplicate alerts across runs, cases (only platform creates cases), state without `save_timestamp` for test runs.

### Q14. How do you make a connector idempotent?

Three layers: (1) use the third party's stable external ID as `alert_id`, not `uuid.uuid4()`; (2) maintain a processed-IDs cache in connector context and skip duplicates; (3) query the third-party with a `since=last_success_time` filter so you only see new stuff.

### Q15. What happens if your connector forgets to map `start_time` / `end_time` in ontology?

The platform's alert-grouping engine has no time signal. Every alert becomes its own case. SOAR is flooded. **Silent break** — your tests pass, your action runs, your production is broken. This is one of the most common incidents — a `mp validate` check now enforces both fields for connector-bearing integrations.

### Q16. How do you handle rate-limit errors mid-cycle in a connector?

1. Catch the specific `RateLimitError`
2. Log and break out of the fetch loop
3. **Save state for alerts already processed** (`save_timestamp`)
4. Don't fail the whole run — the next cycle picks up where this one left off

Never retry inline — that blocks the whole scheduler thread.

### Q17. Async connector — when do you choose it over sync?

When (a) the third-party API supports concurrent requests (doesn't 429 you), (b) alert volume per cycle is high, (c) per-alert detail fetches can parallelize cleanly. Use `AsyncConnector` from `TIPCommon.base.connector.async_connector`. Don't use async as a default — it adds complexity; prefer sync until you have a perf reason.

---

## Jobs

### Q18. What's the difference between a Job and a Connector?

Both run on a schedule. **Connectors create alerts.** **Jobs sync existing state** (comments, status, tags) between SOAR and a third party. Jobs don't produce `AlertInfo` — they call `soar_job.add_comment()`, `update_case_priority()`, etc.

### Q19. How do you prevent sync loops in a bidirectional Job pair?

Three techniques: (1) author tag — prefix mirrored comments with `[SOAR]` or `[ServiceNow]` and skip those on the other side; (2) idempotency keys embedded in the mirrored object; (3) time threshold — only mirror objects older than N seconds, preventing tight back-to-back mirroring.

### Q20. Why does a Job save `self.job_start_time` instead of "now" at the end?

If the job run took 4 minutes, saving "now" would skip those 4 minutes worth of activity on the next run — comments added while the job was executing would be missed. Saving `job_start_time` ensures the next run's query window starts from just before this run began.

---

## Widgets

### Q21. What's the difference between `safe_rendering: true` and `false`?

`true` sanitizes HTML and blocks inline JS — default for community widgets to prevent XSS. `false` executes JS — needed for interactive widgets (charts, rich inputs) but requires stricter security review. We default to `true` for community, allow `false` for partner after review.

### Q22. What does the standard widget condition guard do?

```yaml
condition_group:
  logical_operator: and
  conditions:
    - field_name: '[{stepInstanceName}.JsonResult]'
      match_type: not_contains
      value: '{stepInstanceName}'
```

It checks that the JsonResult placeholder has been **resolved to real data** (i.e., the step ran). Without this, widgets render with literal `{stepInstanceName}` text when the referenced step didn't execute — looks broken.

---

## Lead-Level

### Q23. A connector is in production and customers report their case queue is filled with one-alert-per-case instead of grouped. Walk me through your debugging.

1. **Check ontology status in the platform UI** — is the mapping present? If not, it wasn't deployed correctly.
2. **Verify `start_time` and `end_time` are mapped** — most common cause of broken grouping.
3. **Inspect a sample alert's raw `events`** — do the fields the ontology references actually exist? Field rename upstream is a common cause.
4. **Check that the Product-level mapping is applied**, not just Event level — inheritance gaps happen when customer overrides partial rules.
5. **Look at case grouping rules themselves** — tenant config may have narrowed the time window so much that even correct ontology can't group.
6. **Test with a hand-crafted alert via the connector** — does it group with an existing case? If yes, the connector's ontology is fine; if no, the problem is in the connector.

### Q24. We have 40+ community connectors on TIPCommon 1.x. You're asked to migrate them all. Plan it.

**Discovery** — inventory every connector + its TIPCommon version + last-change date. Rank by (a) recent activity, (b) customer usage telemetry.

**Compatibility shim first** — ensure TIPCommon 2.x's base classes expose the same external behavior as 1.x's helpers. Any gap fix in TIPCommon first.

**Migration kit** — script that transforms common 1.x patterns to 2.x class skeleton (extract → validate → init → perform). Doesn't do business logic migration; devs finish that.

**Pilot wave** — migrate 3 connectors yourself end-to-end. Document pitfalls. Build tests to lock behavior.

**Waves of 5** — each wave: pull, migrate with kit, add tests, deploy to staging tenant, burn 24 hours in staging, PR to main. Assign one maintainer per integration.

**Regression harness** — run all migrated connectors against the same mock third-party fixtures that 1.x versions ran against. Any behavioral diff is a bug.

**Feature flag** — ship each migrated version alongside the old one in the Content Hub for one release cycle. Customers opt in; telemetry measures. Then deprecate 1.x.

**Exit criteria** — all 40+ on 2.x, `mp validate` enforces 2.x for new PRs, `packages/tipcommon/whls/` retains 1.x wheels for deployed-legacy back-compat but no new integrations may pin them.

### Q25. Architect a new integration for a vendor I name on the whiteboard (say, CrowdStrike Falcon).

I'd structure this as a 7-minute walkthrough:

1. **Authentication model** — CrowdStrike uses OAuth 2.0 client credentials (client_id/client_secret → bearer token). Define `API Root`, `Client ID`, `Client Secret` as `definition.yaml` parameters (`type: password` for secret). Implement token refresh with expiry handling in `core/falcon_auth.py`.

2. **API client** — `core/falcon_client.py` wraps the `requests.Session` with auth injection, retry, timeout, and a `test_connectivity()` method. Custom exceptions: `FalconAuthError`, `FalconRateLimitError`, `FalconNotFoundError`.

3. **Ping** — trivial action: instantiate client, call `test_connectivity()`, return `true`/`false` with clear error message on auth failure.

4. **Actions by analyst journey:**
   - `Enrich Host` — entity-based (HOSTNAME), pulls host details, sensor version, risk score, sets `FalconFalcon_*` enrichment keys and `is_suspicious` if risk score ≥ threshold.
   - `Isolate Host` / `Unisolate Host` — remediation actions on HOSTNAME entities.
   - `List Detections` — parameter-based time-range query.
   - `Get Detection Details` — fetches a detection by ID (parameter).
   - `Update Detection Status` — triaging action.

5. **Connector** — `connectors/falcon_detections.py` polls `/detections/queries/detects/v1` + `/detections/entities/summaries/GET/v1`. Config: API Root, creds, Max Hours Back, Severity Filter, Max Alerts Per Cycle, Environment Field Name. Builds `AlertInfo` with external ID = detection_id (idempotent). Processed-IDs cache keyed by detection_id.

6. **Ontology mapping** — `ontology_mapping.yaml` at Product level:
   - `start_time` → `$.created_timestamp`
   - `end_time` → `$.max_confidence_timestamp`
   - Entities: HOSTNAME from `$.device.hostname`, USER from `$.behaviors[*].user_name`, FILEHASH from `$.behaviors[*].sha256`

7. **Widgets** — a `detection_summary.html` predefined widget bound to `Get Detection Details` action's JSON result, showing severity, tactic/technique, affected host, kill-chain visualization.

8. **Jobs (maybe)** — a `sync_detection_status.py` that mirrors SOAR case status back to Falcon's detection status (triaged/closed).

9. **Tests** — mock Falcon API in `tests/core/product.py`, fixtures for typical detections, per-action tests covering happy path + auth failure + rate limit + empty response.

10. **Release plan** — start at version `1.0.0` with `new: true` in `release_notes.yaml`, submit as Partner integration if CrowdStrike officially supports, Community otherwise.

That answer shows architectural thinking, security awareness, operational thinking, and team coordination in a single coherent response.

---

## Next

→ **[Section 4: Playbooks](../04-playbooks/index.md)**
