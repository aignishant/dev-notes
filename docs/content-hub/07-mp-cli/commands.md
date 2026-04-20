# `mp` Commands — Deep Dive

## Installation

### Persistent Install (Recommended)

```bash
uv tool install mp --from git+https://github.com/chronicle/content-hub.git#subdirectory=packages/mp
mp --help
```

### One-Shot

```bash
uvx --from git+https://github.com/chronicle/content-hub.git#subdirectory=packages/mp mp --help
```

!!! warning "Windows users"
    Use `wmp` instead of `mp` to avoid conflicts with Windows' built-in `mp` alias.

## Command Matrix

| Command | What it does |
|---|---|
| `mp build` | Build integrations or playbooks into deployable format |
| `mp validate` | Structural + metadata validation |
| `mp test` | Run pre-build integration tests |
| `mp check` | Lint + type check |
| `mp format` | Auto-format Python |
| `mp dev-env` | login / push / pull with dev SOAR |
| `mp describe` | AI-generated action descriptions |
| `mp config` | Configure `mp` settings |

## `mp build`

Transforms source code into deployable zip artifacts.

### Subcommands

```bash
mp build integration [INTEGRATION_NAMES]... [OPTIONS]
mp build playbook    [PLAYBOOK_NAMES]... [OPTIONS]
mp build repository  [REPOSITORIES]... [OPTIONS]
```

### Options

| Option | Meaning |
|---|---|
| `--src PATH` | Custom source folder |
| `--dst PATH` | Custom destination folder |
| `--deconstruct` / `-d` | **Reverse**: decompose a built zip into repo format |
| `--custom-integration` | Build from custom repository |
| `--quiet` / `-q` | Less logging |
| `--verbose` / `-v` | More logging |

### Repository Targets

- `google` — commercial integrations
- `third_party` — community + partner
- `custom` — customer-owned custom repo
- `playbooks` — playbook content

### Examples

```bash
# Build a single integration
mp build integration my_integration

# Build multiple
mp build integration my_integration another_integration

# Deconstruct an exported zip back into repo format
mp build integration my_integration --deconstruct --src ./exported.zip

# Build the entire third_party repo (community + partner)
mp build repository third_party
```

## `mp validate`

Enforces structural + metadata correctness. **This is what CI runs on every PR.**

```bash
mp validate integration [INTEGRATION]... [OPTIONS]
mp validate playbook    [PLAYBOOK]... [OPTIONS]
mp validate repository  [REPOSITORY]... [OPTIONS]
```

### Options

| Option | Meaning |
|---|---|
| `--only-pre-build` | Skip full build, run cheap structural checks only |
| `--quiet` / `-q` | |
| `--verbose` / `-v` | |

### What It Catches

- Missing required files (`definition.yaml`, `pyproject.toml`, `uv.lock`)
- Mismatched `integration_identifier` between `definition.yaml` and action YAMLs
- Missing `ontology_mapping.yaml` when a connector exists
- Action YAMLs referencing non-existent integration identifiers
- Missing `start_time`/`end_time` in ontology for connector-bearing integrations
- `release_notes.yaml` version not bumped
- Invalid `publish_time` format
- Non-snake_case filenames
- `default_value` on `password`-type parameters (security)
- Missing logo files at declared paths
- Broken widget YAML references

### Example

```bash
# Run all validation including full build
mp validate integration my_integration

# Fast iteration — just structural checks
mp validate integration my_integration --only-pre-build
```

## `mp test`

Runs the integration's pytest suite.

```bash
mp test [TARGETS] [OPTIONS]
```

Works with the integration's own `tests/` directory + uses `integration_testing` package for mocked SOAR platform.

## `mp check`

Lint + optional static type check.

```bash
mp check [FILE_PATHS]... [OPTIONS]
```

### Options

| Option | Meaning |
|---|---|
| `--output-format` | `concise`, `full`, `json`, `junit`, `github`, `gitlab`, `sarif`, etc. |
| `--fix` | Auto-fix issues that don't need human review |
| `--unsafe-fixes` | Also apply fixes that need review (requires `--fix`) |
| `--changed-files` | Only check files changed since HEAD |
| `--static-type-check` | Run `ty` type check |
| `--raise-error-on-violations` | Exit code 1 on violations |

### Examples

```bash
# Check files
mp check path/to/file1.py path/to/dir

# Fix safe issues automatically
mp check path/to/files --fix

# Pre-push hook: check only what you changed, with type checking
mp check --changed-files --static-type-check --raise-error-on-violations
```

`mp check` wraps `ruff` (linter/formatter) and `ty` (type checker). Full Ruff output format list:

`concise`, `full`, `json`, `json-lines`, `junit`, `grouped`, `github`, `gitlab`, `pylint`, `rdjson`, `azure`, `sarif`

## `mp format`

Auto-format Python. Wraps `ruff format`.

```bash
mp format [OPTIONS] [FILE_PATHS]...
```

Typical use: run before every commit.

## `mp describe`

**AI-generated descriptions** for integration actions. Reads action code + YAML + produces proposed `description` field values.

```bash
mp describe [INTEGRATION]
```

Useful for large integrations with dozens of actions where hand-writing descriptions is tedious.

## `mp config`

Configure the CLI's own settings — API endpoint defaults, log level, etc.

```bash
mp config <key>=<value>
```

Rare in day-to-day use.

## `mp dev-env`

Full section next page — this is the most-used subset.

```bash
mp dev-env login
mp dev-env push integration <n>
mp dev-env push playbook <n>
mp dev-env push custom-integration-repository
mp dev-env pull integration <n>
mp dev-env pull playbook <n>
```

## Typical Developer Loop

```bash
# 1. Morning — pull latest integration from dev SOAR
mp dev-env pull integration my_integration --dst ./tmp

# 2. Edit in IDE

# 3. Format + lint + type check
mp format
mp check --changed-files --static-type-check --fix

# 4. Run tests
mp test my_integration

# 5. Validate structure
mp validate integration my_integration --only-pre-build

# 6. Push to dev SOAR for smoke test
mp dev-env push integration my_integration

# 7. Test in SOAR UI: run the action manually

# 8. Full validate before PR
mp validate integration my_integration

# 9. Git commit + push + open PR
```

That 9-step loop runs dozens of times a day for an active integration.

## Next

→ **[dev-env Workflow](dev-env.md)**
