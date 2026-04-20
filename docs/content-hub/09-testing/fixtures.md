# Fixtures & `conftest.py`

## What Fixtures Are

pytest fixtures are dependency-injected test setup. Define once, consume by name, isolated per test.

## `conftest.py` Scope

```
tests/
├── conftest.py                      # applies to all tests below
├── test_defaults/
│   └── test_imports.py
├── test_actions/
│   ├── conftest.py                  # applies to test_actions only
│   └── test_ping.py
└── test_connectors/
    └── test_my_connector.py
```

- Nearest `conftest.py` wins for a test file
- Root `conftest.py` is globally available
- No imports needed — pytest auto-discovers

## Canonical Fixture Set

```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_siemplify():
    """Mocked SiemplifyAction."""
    s = MagicMock()
    s.script_name = "Test Script"
    s.target_entities = []
    s.execution_deadline_unix_time_ms = 9999999999999

    # Config param lookup
    config_map = {
        "Api Key": "test-api-key",
        "Verify SSL": "false",
    }
    s.extract_configuration_param.side_effect = lambda *, param_name, **kw: config_map.get(param_name)

    # Action param lookup
    action_params = {}
    def _action_param_lookup(*, param_name, default_value=None, **kw):
        return action_params.get(param_name, default_value)
    s.extract_action_param.side_effect = _action_param_lookup
    s._action_params = action_params   # expose for test mutation

    return s


@pytest.fixture
def mock_entity_ip():
    """Build a mock IP address entity."""
    def _make(ip, is_internal=False, is_suspicious=False):
        e = MagicMock()
        e.identifier = ip
        e.entity_type = "ADDRESS"
        e.is_internal = is_internal
        e.is_suspicious = is_suspicious
        e.additional_properties = {}
        return e
    return _make


@pytest.fixture
def api_key():
    return "test-api-key-11111111-2222-3333-4444-555555555555"
```

## Fixture Scopes

```python
@pytest.fixture                         # default: function-scoped
@pytest.fixture(scope="class")          # one per test class
@pytest.fixture(scope="module")         # one per .py file
@pytest.fixture(scope="session")        # one per pytest run
```

Use `function` for mutable state (default). Use `session` only for expensive, immutable setup.

## Fixture Composition

Fixtures can depend on fixtures:

```python
@pytest.fixture
def mock_abuseipdb_client(api_key):
    client = MagicMock()
    client.api_key = api_key
    client.check_ip.return_value = None
    return client


@pytest.fixture
def ping_action(mock_siemplify, mock_abuseipdb_client):
    from ..actions.ping import Ping
    action = Ping(name="Test Ping")
    action._soar_action = mock_siemplify
    action._api_client = mock_abuseipdb_client
    return action
```

## Parametrized Fixtures

```python
@pytest.fixture(params=["8.8.8.8", "1.1.1.1", "9.9.9.9"])
def ip_entity(request, mock_entity_ip):
    return mock_entity_ip(request.param)


def test_enrich_each_ip(ip_entity):
    # This test runs 3 times, once per parameterized IP
    assert ip_entity.identifier.count(".") == 3
```

Multi-axis parametrization:

```python
@pytest.fixture(params=[(30, 50), (60, 80), (90, 30)])
def threshold_case(request):
    max_days, threshold = request.param
    return {"max_days": max_days, "threshold": threshold}
```

## Autouse Fixtures

Apply to every test without being named:

```python
@pytest.fixture(autouse=True)
def setup_logging(caplog):
    caplog.set_level("INFO")
```

Use sparingly — hidden behavior makes tests hard to read.

## Temp Directory Fixture

```python
def test_writes_to_disk(tmp_path):
    (tmp_path / "output.json").write_text("{}")
    assert (tmp_path / "output.json").exists()
```

`tmp_path` is a built-in — unique per test, auto-cleaned.

## Marker Pattern

```python
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow",
    "integration: end-to-end tests",
    "unit: fast unit tests",
]
```

```python
@pytest.mark.slow
def test_large_dataset():
    ...

@pytest.mark.integration
def test_end_to_end_action():
    ...
```

Run subsets:

```bash
pytest -m "not slow"               # skip slow tests
pytest -m "unit"                   # only unit
pytest -m "integration or slow"
```

## Sharing `common.py`

In addition to fixtures, put mock data constants in `tests/common.py`:

```python
# tests/common.py
SAMPLE_ABUSEIPDB_RESPONSE = {
    "data": {
        "ipAddress": "1.2.3.4",
        "isPublic": True,
        "ipVersion": 4,
        "abuseConfidenceScore": 85,
        "countryCode": "RU",
    }
}

INVALID_API_KEY_RESPONSE = {
    "errors": [{"detail": "Authentication failed"}]
}

DEFAULT_MAX_DAYS = 30
DEFAULT_THRESHOLD = 50
```

Import and use:

```python
from ..tests.common import SAMPLE_ABUSEIPDB_RESPONSE

@responses.activate
def test_basic_flow():
    responses.add(responses.GET, "https://...", json=SAMPLE_ABUSEIPDB_RESPONSE, status=200)
    ...
```

Keeps tests readable; changes to the sample propagate everywhere.

## Next

→ **[Interview Q&A](questions.md)**
