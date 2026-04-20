# IDE Setup (PyCharm / JetBrains)

The repo's recommended IDE is **PyCharm / IntelliJ with Python plugin**. Setup guide is in `docs/getting_started/setup_your_environment.md`.

## Two Project Strategies

### Strategy 1 — Monorepo Root

Open the entire `content-hub` folder as the project. Single IDE window, all integrations visible. Works for reviewing PRs across integrations.

### Strategy 2 — Individual Integration

Open a single integration folder (`content/response_integrations/.../my_integration/`) as its own project. Pinned interpreter = that integration's `.venv/bin/python`. Cleaner for focused work.

Most leads use **Strategy 1** with per-module interpreter overrides.

## Python Interpreter Setup

Every integration has its own `.venv`. Point the IDE at it:

1. `File > Settings > Python > Interpreter`
2. Gear icon → Add
3. Select existing env → point at `<integration>/.venv/bin/python`
4. OK

If `.venv` doesn't exist yet:

```bash
cd <integration-folder>
uv sync --dev
```

This creates `.venv` with the correct Python 3.11 + all deps.

## Essential Plugins

### Ruff

Lint + format integration.

Settings:
- Settings → Python → Tools → Ruff
- Enable all options
- Set execution mode to the specific integration's interpreter
- Enable "Run on save" → `All actions on save...`

### Ty

Type checking.

Settings:
- Settings → Python → Tools → ty
- Enable all options
- Set execution mode to the specific integration's interpreter

### Pydantic

Enhanced autocomplete inside Pydantic models.

### PyVenv Manage 2

Switch between integration-specific virtual environments quickly.

Setting the project interpreter:

1. Right-click `<integration>/.venv/bin` folder
2. "Set as project interpreter" (or module interpreter for module scope)

Repeat for each integration you work on.

### Rainbow Brackets

Visual bracket matching.

### Key Promoter X

Notifies you of keyboard shortcuts when you mouse-click — helps you learn.

## Code Style

`File > Settings > Editor > Code Style > Python`:

- **Tabs and Indents:**
  - Use 4 spaces
  - Tab size 4
  - Indent size 4
- **Imports:**
  - Sort imports enabled
  - Join imports with same source
  - Import order: stdlib → third-party → local

## Line Length

`File > Settings > Editor > Code Style`:

- Right margin: **88** (Black/Ruff default) OR **100** (if using the full-type-hint style recommended by the repo — gives more horizontal room for long type signatures).

## Python Integrated Tools

`File > Settings > Tools > Python Integrated Tools`:

- **Testing** — Default test runner: `pytest`
- **Docstring** — Format: `Google`

## Run Configurations

### Running `mp` Commands

1. `Run > Edit Configurations`
2. `+` → `uv run`
3. Configure:
   - Name: e.g. "Validate Integration"
   - Run: Module
   - Module: `mp`
   - Arguments: `validate integration my_integration`
   - Python interpreter: the uv-configured interpreter

### Running a Specific Test

Right-click a test function → Run `pytest '<test>'`. The pytest runner honors `conftest.py`.

### Debug an Action Locally

1. Mock `SiemplifyAction` (the `integration_testing` package helps)
2. Add a run config pointing at your action's `main()`
3. Set breakpoints
4. Run debug

## Docstring Convention

Google-style:

```python
def check_ip_reputation(
    ip: str,
    max_days: int = 30,
    threshold: int = 50,
) -> IPReport:
    """Query AbuseIPDB for an IP's reputation.

    Args:
        ip: IPv4 or IPv6 address to check.
        max_days: Look-back window in days.
        threshold: Minimum confidence score to mark as suspicious.

    Returns:
        IPReport containing score, country, ISP, and history.

    Raises:
        AbuseIPDBInvalidAPIKeyError: If the API key is rejected.
        AbuseIPDBRateLimitError: If rate limit exceeded.
    """
    ...
```

## Git Integration

PyCharm's built-in Git UI is strong — use it for:

- Visual diff before commit
- Stash management
- Branch switching
- PR creation via the GitHub plugin

But the terminal is fine too — use what's fast for you.

## Debugging Tips

- **Step-into TIPCommon code** — because it's a local wheel, PyCharm can step into the source
- **Evaluate expression in debugger** — inspect live Pydantic model values, dict contents
- **Breakpoint conditions** — e.g. `entity.is_suspicious` breaks only on suspicious entities

## Multi-Venv Workflow Tip

When switching integrations:

1. Use `PyVenv Manage 2` → select the new `.venv/bin`
2. Wait for indexing (skeletons refresh)
3. Your imports now resolve for the new integration's deps

Don't share one venv across integrations — they have different TIPCommon versions.

## Shortcut Cheat Sheet (Mac defaults)

| Shortcut | Action |
|---|---|
| ⌥ Enter | Quick fix / intention action |
| ⇧⌘F | Find in files |
| ⇧⇧ | Go to anything |
| ⌘B | Go to definition |
| ⌥⌘B | Go to implementation |
| ⌥F7 | Find usages |
| ⌃G | Next occurrence |
| ⌃T | Refactor menu |
| F6 | Move/rename |
| ⌥⌘L | Reformat code |

## Next

→ **[Interview Q&A](questions.md)**
