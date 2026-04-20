# Testing — Interview Q&A

---

## Q1. What framework does the project use for testing?

pytest. Configured in each integration's `pyproject.toml` under `[tool.pytest.ini_options]`. The `mp test` command wraps `pytest` invocation.

---

## Q2. What's the standard test folder layout?

```
tests/
├── __init__.py
├── common.py                 # shared test data constants
├── conftest.py               # pytest fixtures
├── core/
│   ├── session.py            # mock HTTP session
│   └── product.py            # mock third-party product
├── test_defaults/
│   └── test_imports.py       # can everything import?
└── test_actions/
    └── test_*.py
```

---

## Q3. What's `test_imports.py` for and why is it mandatory?

It imports every action/connector/job module to catch missing deps or syntax errors. A missing import breaks the integration in the platform at load time. This test catches it before push. The default test scaffold always includes it.

---

## Q4. What's the `integration_testing` package?

A Google-maintained dev dependency that provides black-box mocks — mock `SiemplifyAction`/`SiemplifyConnectorExecution`/`SiemplifyJob`, mock entity sets, configuration mocks, HTTP session mocks. Lets actions run end-to-end locally without a real SOAR instance or real API calls.

---

## Q5. Where should you mock — the API client's high-level methods, or the HTTP session?

**HTTP session.** Mocking the client's `check_ip()` skips parsing, error handling, and retry — you test the mock. Mocking at the session level means your API client runs its real code against canned responses. Much higher-signal tests.

---

## Q6. What's the minimum set of tests per action?

At least three: **happy path, specific error (e.g., invalid API key), generic error**. Plus `test_imports.py` for the whole integration. Coverage bar: ~80% lines for the action file.

---

## Q7. What's a critical test for connectors?

**Idempotency** — run the connector twice; second run emits zero new alerts. Catches bugs where `alert_id` isn't stable or processed-IDs cache isn't consulted.

---

## Q8. How do you test timestamp-sensitive code?

Use `freezegun`:

```python
from freezegun import freeze_time

@freeze_time("2025-10-15 12:00:00")
def test_uses_current_time():
    ...
```

Fixed clock makes tests reproducible across machines and time zones.

---

## Q9. How do you prevent real network calls in tests?

`pytest-socket` at the CI level (`--disable-socket`). Or an autouse fixture that patches `socket.socket`. Any accidental HTTP call fails the test immediately.

---

## Q10. What's the advantage of `responses` over `unittest.mock.patch`?

`responses` matches by URL + HTTP method + query params + body, so you verify the API client actually produced the right request. `unittest.mock.patch` only verifies the method was called — doesn't validate what was actually sent over the wire.

---

## Q11. What fixture scopes does pytest have and when do you pick each?

`function` (default) — new fixture per test. Safe default.
`class` — one per test class.
`module` — one per `.py` file.
`session` — one per entire pytest run.

Use `function` unless setup is genuinely expensive (DB connection, remote wheel install). Larger scopes create test-order dependencies.

---

## Q12. How do you test a Pydantic model?

Two axes: **accepts valid data** and **rejects invalid data**.

```python
def test_report_accepts_valid():
    r = Report.model_validate({"score": 50})
    assert r.score == 50

def test_report_rejects_out_of_range():
    with pytest.raises(ValidationError):
        Report.model_validate({"score": 150})
```

Plus edge cases: optional fields absent, type coercion ("50" → 50), alias handling (`abuseConfidenceScore` → `abuse_confidence_score`).

---

## Q13. How do you parametrize a test across many inputs?

```python
@pytest.mark.parametrize("score,threshold,expected", [
    (30, 50, False),
    (50, 50, True),
    (85, 50, True),
])
def test_threshold_logic(score, threshold, expected):
    assert _is_suspicious(score, threshold) == expected
```

One `@parametrize` replaces N near-duplicate tests — also gives each case a unique name in pytest output.

---

## Q14. A test is flaky — sometimes passes, sometimes fails. How do you approach?

1. **Isolate** — run that test 100× locally. Does it fail some of the time? Yes = flaky, not random env.
2. **Check shared state** — module-scoped fixtures, class attributes, caches that persist across tests
3. **Check time** — use `freezegun` if time-dependent
4. **Check order** — run with `pytest-randomly` to randomize order; if deterministic order is required, there's a test-ordering bug
5. **Check concurrency** — if tests use threads/async, mocks may race
6. **Check external calls** — a real network call sneaked in

Flakiness is always a bug, never "just flaky". Fix or mark `@pytest.mark.xfail` pending fix.

---

## Q15. What's the approach to test coverage?

Target 80%+ line coverage for new integrations, 90%+ on `core/` business logic. Measured via `pytest --cov=.` or `uv run pytest --cov`. CI surfaces coverage and can gate on it. We don't chase 100% — some SDK glue is practically impossible to test without elaborate mocks.

---

## Next

→ **[Section 10: CI/CD](../10-cicd/index.md)**
