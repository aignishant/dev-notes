# GitHub Actions Workflows

## Where Workflows Live

```
.github/
├── workflows/           # The workflows that run on PR/push
│   ├── validate-integrations.yml
│   ├── validate-playbooks.yml
│   ├── validate-parsers.yml
│   ├── lint-and-format.yml
│   └── ...
└── actions/             # Reusable Actions exposed to consumers
    └── custom-integration-push/
        └── guide.md
```

## The Reusable Action: `custom-integration-push`

From `docs/github_actions.md`:

```yaml
- uses: chronicle/content-hub/actions/custom-integration-push@main
  with:
    api-root: ${{ secrets.SOAR_API_ROOT }}
    api-key: ${{ secrets.SOAR_API_KEY }}
```

**Purpose:** Auto-push custom integrations from a customer's fork to their SOAR instance on every relevant commit.

**Features:**

- **Automated sync** — watches `content/response_integrations/custom/` directory
- **Flexible auth** — API Key (recommended) or Username/Password
- **Smart triggers** — only runs when relevant files change

## CI Workflows That Run on PR

### 1. Lint + Format

Runs `mp check` and `mp format --check` on changed Python files.

```yaml
- name: Lint
  run: uv run mp check --changed-files --static-type-check --raise-error-on-violations
```

Fails if:

- Lint violations
- Type check errors
- Formatting not applied

### 2. Integration Validation

For each changed integration:

```yaml
- name: Validate
  run: uv run mp validate integration ${{ matrix.integration }}
```

Checks structural integrity + full test build.

### 3. Unit Tests

```yaml
- name: Test
  run: uv run mp test ${{ matrix.integration }}
```

Runs pytest in each integration's `.venv`.

### 4. Parser Validation (Two-Stage)

**Stage 1** — automatic:

```yaml
- name: Validate Parsers
  run: python tools/parsers/validations/run_validations.py
```

**Stage 2** — manually triggered by contributor via `secops` CLI; reports status back.

### 5. Matrix Strategy for Parallel Runs

```yaml
strategy:
  matrix:
    integration: ${{ fromJson(needs.detect-changes.outputs.changed) }}
  fail-fast: false
```

Detects changed integrations in a pre-flight job, then runs validation in parallel.

## Build Caching

Leverages `uv` caching:

```yaml
- name: Setup uv
  uses: astral-sh/setup-uv@v3
  with:
    enable-cache: true
    cache-dependency-glob: "**/pyproject.toml"
```

Cuts CI time dramatically for integrations whose deps haven't changed.

## Python Version Matrix

Currently 3.11-only (`.python-version` pins it). Workflows:

```yaml
- name: Setup Python
  run: uv python install 3.11
```

No multi-version matrix — the platform runtime is fixed.

## Secrets

- `SOAR_API_ROOT` — dev environment URL
- `SOAR_API_KEY` — admin-scoped API key
- (For parser Stage 2) `GCP_CREDENTIALS_JSON`

Never logged. Secrets are provided via `${{ secrets.NAME }}` at step level.

## Required Status Checks

`main` branch has a GitHub Repository Ruleset — **PRs cannot merge until all required checks pass**. The required set:

| Check | What |
|---|---|
| Validate Integrations | `mp validate` on changed integrations |
| Validate Playbooks | `mp validate` on changed playbooks |
| Validate Parsers | Standalone parser validations |
| Validate Google & Parsers | Live-instance parser validation (manual trigger) |
| Lint & Format | `mp check` + `mp format --check` |
| Unit Tests | `mp test` on changed integrations |
| CLA Check | Contributor License Agreement signed |

## The "Ready for Review" Convention

From `contributing.md`:

> *"If you opened your PR as a 'Draft', please mark it as 'Ready for Review' once all validations pass."*

Drafts signal "in progress, don't review yet." Moving to Ready-for-Review signals "please look at this now."

## Post-Merge Pipeline

Once merged to `main`:

1. An internal publishing pipeline (not visible in this repo) picks up the new content
2. Builds the deployable zips
3. Publishes to the Content Hub registry
4. Customers see the new/updated content in their in-product Content Hub catalog

This side is deliberately opaque to contributors — it's managed by the Content Hub release team.

## Next

→ **[PR Workflow](pr-workflow.md)**
