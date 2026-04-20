# Section 9 — Testing

## Overview

Every integration ships `tests/`. PR review checks test coverage. The `integration_testing` package is the secret sauce — it provides a mock SOAR platform so actions can run locally end-to-end without a real SOAR instance.

## Test Folder Layout

```
my_integration/tests/
├── __init__.py
├── common.py                    # shared test constants, mock data
├── conftest.py                  # pytest fixtures
├── core/
│   ├── __init__.py
│   ├── session.py               # mock HTTP session
│   └── product.py               # mock third-party product API
├── test_defaults/
│   ├── __init__.py
│   └── test_imports.py          # "can we import everything?"
└── test_actions/
    ├── __init__.py
    ├── test_action1.py
    └── test_action2.py
```

## The `integration_testing` Package

Lives at `packages/integration_testing/`. Wheels at `packages/integration_testing_whls/`. Added as dev dependency:

```toml
[dependency-groups]
dev = ["integration_testing"]

[tool.uv.sources]
integration_testing = { path = "../../../../packages/integration_testing_whls/..." }
```

What it gives you:

- Mock `SiemplifyAction`, `SiemplifyConnectorExecution`, `SiemplifyJob`
- Mock entity set
- Mock configuration parameters
- HTTP session mocker (via `session.py` pattern)
- Mock third-party product server

## Pages

1. **[Unit Testing with pytest](unit-testing.md)**
2. **[integration_testing Package](integration-testing.md)**
3. **[Mocking Third-Party APIs](mocking.md)**
4. **[Fixtures & conftest](fixtures.md)**
5. **[Interview Q&A](questions.md)**
