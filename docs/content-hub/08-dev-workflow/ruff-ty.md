# Ruff & Ty — Lint & Type Check

## Ruff

> *"Ruff is the linter + formatter, also from Astral, written in Rust. Replaces black + isort + flake8 + pyupgrade + autoflake with a single tool that's 10-100× faster."*

The Content Hub's ruff config lives at the repo root (`ruff.toml`) and is extended per-integration or per-package via their own `ruff.toml`.

### What Ruff Catches

- Style (spacing, line length, quotes)
- Unused imports, unused variables
- Import ordering
- Dead code
- Simple bugs (unreachable branches, always-true conditions)
- Modernization (old `.format()` → f-strings, etc.)
- Security basics (hardcoded passwords, `eval`, `shell=True`)

### How We Use It

```bash
mp check .                        # lint
mp check . --fix                  # auto-fix safe issues
mp check . --fix --unsafe-fixes   # also apply review-required fixes
mp format .                       # format (like black)
```

Or direct:

```bash
uv run ruff check .
uv run ruff format .
```

### Line Length

Repo uses **88** (Black-compatible default), with **100** permitted if you follow the full-type-hint style.

### Import Sorting

Ruff's import sorting (replacing `isort`) enforces three groups, each alphabetized:

1. Standard library
2. Third-party
3. Local relative imports

### Running on Save (PyCharm)

The dev setup guide enables Ruff's "Run on save" so every file save auto-formats. No manual invocation needed inside the IDE.

## Ty

> *"Ty is Astral's new type checker (sibling to Ruff). Replaces mypy/pyright with something Rust-fast. The Content Hub uses it for static type checking in `mp check --static-type-check`."*

Ty is newer than mypy/pyright and still maturing, but fast. Configuration lives in `ty.toml` or `pyproject.toml`:

```toml
[tool.ty]
python_version = "3.11"
strict = true
```

### What Ty Catches

- Missing type hints on public APIs (if `strict=true`)
- Type mismatches (passing `str` where `int` expected)
- Misuse of generics
- `None` flowing into non-optional positions
- Incorrect Protocol implementations

### Running

```bash
mp check . --static-type-check
# or
uv run ty check
```

CI runs this on every PR.

### Strict Mode

Strict mode catches the most. Typical trade-off:

- **Integration code** — strict typically on
- **Test code** — looser; pytest fixtures don't play nicely with strict
- **Legacy code** — often `# type: ignore` until migration

## The Core Hints You Use

```python
from __future__ import annotations     # enables modern syntax on 3.11
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from TIPCommon.base.interfaces import ApiClient
    from TIPCommon.types import JSON, Contains, Entity

def process(entities: list[Entity], limit: int = 10) -> dict[str, JSON]:
    ...
```

### `from __future__ import annotations`

Postpones evaluation of type hints. Benefits:

1. Can use modern syntax (`list[int]`, `dict[str, X]`, `X | None`) in contexts that need older syntax support
2. Avoids circular import issues — annotations become strings
3. Required pattern in the repo

### `TYPE_CHECKING` Guard

Imports used only for types go inside `if TYPE_CHECKING:`. At runtime these aren't imported — faster startup, avoids circular imports.

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from soar_sdk.SiemplifyAction import SiemplifyAction  # only for hints
```

## Ruff + Ty in the mp check Pipeline

```bash
mp check [paths] [options]
```

- Without `--static-type-check`: only Ruff runs (lint)
- With `--static-type-check`: Ruff + Ty

CI always runs both.

## Per-File Ignores

When a rule genuinely can't apply:

```python
# noqa: E501                          # skip line-length on this line
# noqa: E501, B008                    # multiple
# ruff: noqa                          # skip all on file
```

Use sparingly. Every `noqa` is a comment maintenance burden.

## Typical Lint Rules Enabled

Repo-wide (simplified):

- `E`, `W` — pycodestyle errors + warnings
- `F` — pyflakes
- `I` — import sorting
- `B` — flake8-bugbear (common Python bugs)
- `C4` — flake8-comprehensions
- `UP` — pyupgrade (modernize syntax)
- `N` — pep8-naming
- `ANN` — annotations (if strict)
- `RUF` — Ruff-specific rules

## Format-on-Save

With the Ruff plugin in PyCharm, enable "All actions on save → Reformat with Ruff". On every Ctrl+S:

1. Imports sorted
2. Format applied
3. Safe fixes applied

Same behavior via Ruff's LSP in VS Code.

## Common Rule Violations You'll See

| Rule | What | Fix |
|---|---|---|
| E501 | Line too long | Wrap |
| F401 | Unused import | Remove |
| F841 | Unused variable | Remove or prefix `_` |
| B008 | Function call in default arg | Use `None` + factory pattern |
| UP006 | Use `list` not `List` | Modernize |
| UP007 | Use `X | None` not `Optional[X]` | Modernize |
| N806 | Variable name not snake_case | Rename |
| ANN201 | Missing return type annotation | Add `-> None` or appropriate |

## Next

→ **[Pydantic](pydantic.md)**
