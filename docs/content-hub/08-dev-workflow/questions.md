# Dev Workflow — Interview Q&A

---

## Q1. Why `uv` instead of pip or poetry?

Speed (10-100× faster), deterministic lockfiles, unified interface for envs + deps + tool install + Python version management. Rust-backed. Single source of truth for project config in `pyproject.toml`.

---

## Q2. What's in `uv.lock` and why is it committed?

Every transitive dependency with exact version + hash + platform markers. Committed for reproducible builds — without it, a dep's patch release could silently break CI.

---

## Q3. How does an integration pin a specific TIPCommon version?

```toml
[tool.uv.sources]
tipcommon = { path = "../../../../packages/tipcommon/whls/TIPCommon-2.0.6-py3-none-any.whl" }
```

Points `uv` at the local wheel rather than a public index.

---

## Q4. Why is `soar-sdk` a dev-only dependency?

At runtime the platform provides its own SDK build. Listing it in production deps causes conflict — the zipped copy collides with the platform version, breaking the integration.

---

## Q5. What's Ruff and what does it replace?

A Rust-backed linter + formatter from Astral. Replaces Black + isort + flake8 + pyupgrade + autoflake. 10-100× faster. Ships with the Content Hub via `mp check` / `mp format`.

---

## Q6. What's `ty` and how is it different from mypy?

Astral's new type checker, Rust-backed, much faster than mypy. Integrated via `mp check --static-type-check`. Still maturing but performant enough for CI.

---

## Q7. What does `from __future__ import annotations` do?

Postpones annotation evaluation — all type hints become strings at module parse time. Benefits: use modern generic syntax (`list[int]`), avoid circular imports in hints, faster module load. Required pattern in every integration file.

---

## Q8. Why is `TYPE_CHECKING` used?

```python
if TYPE_CHECKING:
    from heavy_module import SomeType
```

The import only happens when type checkers process the file — not at runtime. Avoids circular imports and speeds up actual runtime.

---

## Q9. What's the repo's line-length convention?

88 (Black/Ruff default) or 100 (for the full-type-hint style that needs horizontal room for type signatures). Configured per-integration in `ruff.toml`.

---

## Q10. What's Pydantic and where do you use it?

Data validation + serialization library. Used for: third-party API response shapes (runtime-validated parsing), internal data models, configuration classes. From the deep-dive docs: *"Use Pydantic for data validation and serialization/deserialization."* v2 is standard.

---

## Q11. Why Pydantic over `@dataclass`?

Runtime validation, type coercion, JSON (de)serialization built-in, field validators, nested models, faster (Rust-backed in v2). Dataclass has none of those — it's a data container, not a validator.

---

## Q12. How do you handle camelCase JSON in a Pydantic model?

```python
class Report(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    abuse_confidence_score: int = Field(alias="abuseConfidenceScore")
```

`alias` bridges wire-format → Python-native. `populate_by_name=True` lets you construct with either.

---

## Q13. You see `.dict()` and `.json()` on a Pydantic model — what's up?

Pydantic v1 API. The repo uses v2 — methods renamed to `.model_dump()` and `.model_dump_json()`. Legacy code using `.dict()` is a migration candidate.

---

## Q14. How do you keep third-party API response models resilient to schema drift?

Set `model_config = ConfigDict(extra="ignore")` on the Pydantic model. New fields from the vendor are silently dropped rather than raising. Keeps the integration functional through minor vendor updates. Recommend `"forbid"` for internal models where typos should break fast.

---

## Q15. What's the difference between `mp format` and `mp check --fix`?

`mp format` — only applies formatting (line-wrap, quoting, spacing). Deterministic transformation.

`mp check --fix` — applies lint auto-fixes (remove unused imports, modernize syntax, etc.). Broader transformation. Use `--unsafe-fixes` for ones that need review.

Typically run both: format first, then check-fix.

---

## Q16. What's the PyCharm "Run on save" workflow?

With the Ruff plugin configured:

- Settings → Python → Tools → Ruff → enable "Run on save"
- On every Ctrl+S: imports sorted, format applied, safe fixes applied

Same effect as `mp format && mp check --fix` but automatic in the editor.

---

## Q17. How do you set up PyCharm to work with multiple integrations in the monorepo?

Open the entire `content-hub` as the project. Install **PyVenv Manage 2** plugin. For each integration you work on:

1. `uv sync --dev` inside that integration's folder
2. Right-click `<integration>/.venv/bin` → Set as project or module interpreter

Switch between integrations via PyVenv Manage 2 → imports resolve per-integration deps.

---

## Q18. Why do we use Google-style docstrings?

Convention + tooling support. PyCharm renders them well, Sphinx generates docs from them, the repo's style guide specifies them. From the setup guide: *"Under Docstring set the Docstring format to Google"*.

---

## Next

→ **[Section 9: Testing](../09-testing/index.md)**
