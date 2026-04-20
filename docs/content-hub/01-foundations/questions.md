# Beginner Interview Questions — Foundations

20 questions you **must** be able to answer instantly. These are the "warm-up" questions that — if you fumble — signal to the interviewer they should go easier on you the rest of the hour. Don't fumble.

---

## Q1. What is the Google SecOps Content Hub?

**Model answer:**
> *"It's the open-source central repository under Apache 2.0 where community and partner-contributed content for Google SecOps lives — Response Integrations, Playbooks, and Parsers — along with shared libraries (TIPCommon, EnvironmentCommon) and the `mp` CLI used to build, validate, and deploy that content. Contributions go through PR, are validated by GitHub Actions, and after merge are published to the in-product Content Hub catalog that customers install from."*

---

## Q2. What's the difference between SIEM and SOAR in Google SecOps?

**Model answer:**
> *"SIEM handles ingestion and detection — raw logs are normalized via parsers into UDM, then detection rules fire events that become alerts. SOAR handles response — it manages Cases, runs Playbooks that orchestrate Actions from Response Integrations, and presents Entities (IoCs, assets) extracted via Ontology Mapping. Content Hub ships content for both sides: parsers for SIEM, integrations and playbooks for SOAR."*

---

## Q3. What are the three main content types in the repo?

1. **Response Integrations** — Python scripts: Actions, Connectors, Jobs, Widgets
2. **Playbooks** — YAML-defined automated workflows with Triggers, Steps, Widgets
3. **Parsers** — CBN configuration files that normalize raw logs to UDM

---

## Q4. What's the difference between an Action, a Connector, and a Job?

| | Action | Connector | Job |
|---|---|---|---|
| **Runs** | On demand (from playbook) | Continuously (cron-like) | Continuously |
| **Purpose** | Perform one task: enrich, remediate, triage | Ingest alerts from third parties | Sync state between SOAR and third party |
| **Creates** | JSON result, entity enrichment, widget | Alerts | Comments, updates, nothing new |
| **Example** | "Enrich IP with VirusTotal" | "Pull CrowdStrike detections every 5 min" | "Mirror SOAR comments to ServiceNow tickets" |

---

## Q5. Where does a community-contributed integration live in the repo?

```
content/response_integrations/third_party/community/<snake_case_integration_name>/
```

All filenames must be **snake_case**.

---

## Q6. Why is the TIPCommon library shipped as multiple wheel files in the repo?

> *"Back-compat. Older deployed integrations pin older TIPCommon versions (1.0.10, 1.1.2.2, etc.). Forcing them to the latest would require re-testing and re-certifying every one. So we ship every historical wheel under `packages/tipcommon/whls/` and integrations pin their version in `pyproject.toml` via a local path source."*

---

## Q7. What is `mp`?

> *"The marketplace CLI — `mp` — is the developer-facing command-line tool that builds integrations into the deployable zip format, validates their structure and metadata, runs tests, lints code, and lets you push/pull content to your dev SOAR instance. It's the daily driver of any contributor. Lives at `packages/mp/`."*

---

## Q8. Name the main `mp` commands.

| Command | Does |
|---|---|
| `mp build` | Build an integration/playbook into deployable zip |
| `mp validate` | Structural + metadata validation |
| `mp test` | Run pre-build integration tests |
| `mp check` | Lint + optional static type check (via ruff + ty) |
| `mp format` | Auto-format Python |
| `mp dev-env login/push/pull` | Push/pull content to a dev SOAR environment |
| `mp describe` | AI-generated descriptions for actions |
| `mp config` | Configure `mp` settings |

---

## Q9. What Python version does the project use and why?

**Python 3.11**, pinned in each integration's `.python-version` file and enforced in `pyproject.toml` (`>=3.11,<3.12`). 3.11 was chosen because: (a) it's the platform runtime, (b) it gives modern typing features (`match`/`case`, `Self`, improved generics), (c) it has significant perf wins over 3.10 while being stable.

---

## Q10. What package manager does Content Hub use?

**`uv`** (from Astral). It's used for:
- `uv sync` — install project deps
- `uv add` — add a dep (updates `pyproject.toml` + `uv.lock`)
- `uv run` — run inside the virtual env
- `uv tool install mp` — install `mp` as a persistent global tool

Chosen over pip/poetry for **speed** and **deterministic lockfiles**.

---

## Q11. Why is every integration's `uv.lock` committed?

For reproducible builds. The CI and the dev must install the exact same transitive dependency graph. Without `uv.lock`, a third-party dep publishing a breaking patch could silently fail only in CI.

---

## Q12. What's in `definition.yaml`?

```yaml
identifier: AbuseIPDB            # Unique platform identifier
name: AbuseIPDB                  # Display name
parameters:
  - name: Api Key                # Integration config params shown in SOAR UI
    type: password
    is_mandatory: true
  - name: Verify SSL
    type: boolean
    default_value: true
categories:                      # Tags in the catalog
  - Security
  - Threat Intelligence
svg_logo_path: resources/logo.svg
image_path: resources/image.png
```

It's the **identity card + config schema** of the integration. Used by the SOAR UI to render the configuration form.

---

## Q13. What's `ontology_mapping.yaml` for, and when is it required?

It defines how **event fields map to SOAR Entity types** (IP, user, hash, URL, domain). **Required** if the integration has a connector — because the connector creates events from third-party data and those events need to be mapped into Entities for case management to work. The ontology has a **3-level hierarchy** — Source → Product → Event — with inheritance top-down.

---

## Q14. What's the difference between `community/` and `partner/`?

| | community | partner |
|---|---|---|
| **Who maintains** | Individual community members | Official product vendor (e.g. Infoblox, AnyRun) |
| **Support level** | Best-effort | Vendor-supported |
| **Branding** | Labeled "Community" in catalog | Labeled with partner name |
| **Review bar** | Same technical bar, more independence | Same, coordinated with vendor |

Both live under `third_party/` and follow the **same internal structure**.

---

## Q15. What's the first action every integration must ship?

**Ping** — a basic connectivity test. `Ping.py` + `Ping.yaml`. It validates the API Key / URL / auth works and is the first thing the SOAR UI calls when a user clicks "Test" on the integration config screen.

---

## Q16. What's UDM?

**Unified Data Model** — Google SecOps' canonical event schema. Parsers translate raw logs (syslog, JSON, CSV) into UDM events. It's a standardized shape so detection rules and searches work the same across any vendor's logs.

---

## Q17. What's CBN?

**Configuration-Based Normalization** — the DSL used in `parser.conf` files. It consists of **filters** (select fields from raw log) and **mutations** (transform + write to UDM). Lives at `content/parsers/.../cbn/parser.conf`.

---

## Q18. What's the difference between an Event, an Alert, and a Case?

- **Event** — one normalized record (UDM)
- **Alert** — a grouped set of events flagged as possibly malicious (by a rule or a connector)
- **Case** — a container of related alerts, auto-created by the platform when alerts share time + entity overlap

**Only the platform creates Cases.** Connectors create Alerts. Alerts contain Events.

---

## Q19. What's a Widget in this context?

Two flavors:

1. **Predefined Widget** (integration level) — HTML widget bound to an **Action's JSON Result**, rendered in the Alert view. Defined in `widgets/<name>.html` + `<name>.yaml`.
2. **Playbook Widget** — HTML widget rendered in the case overview, fed from playbook step data. Defined in the playbook's `widgets/` dir.

Both use placeholders like `[{stepInstanceName}.JsonResult]` that get replaced at render time.

---

## Q20. Walk me through making your first change to an existing integration.

**Script answer:**
1. `mp dev-env login --api-root <url> --api-key <key>` — auth to my dev SOAR
2. `mp dev-env pull integration <name> --dest ./tmp` — pull latest deployed version (optional, if not already in repo)
3. Edit `<action>.py` + `<action>.yaml`
4. Add/update tests under `tests/test_actions/`
5. `mp format` — auto-format
6. `mp check --fix --static-type-check` — lint + type check
7. `mp test <name>` — run tests
8. `mp validate integration <name>` — structural validation
9. Bump version and add entry in `release_notes.yaml`
10. Open PR, ensure CLA is signed, wait for GitHub Actions to pass
11. Address review feedback → squash merge

That 11-step answer shows you've lived this loop a hundred times, not read about it once.

---

## Next

Section 1 done. → **[Section 2: Core Concepts](../02-core-concepts/index.md)**
