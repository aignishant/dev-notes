# Unit Testing with pytest

## Configuration

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
]
```

## Running Tests

```bash
uv run pytest                               # all tests
uv run pytest tests/test_actions/           # one dir
uv run pytest tests/test_actions/test_ping.py::test_success  # single test
uv run pytest -k "ping"                     # name filter
uv run pytest --lf                          # only last failed
uv run pytest --cov=.                       # coverage
```

Or via `mp test`:

```bash
mp test my_integration
```

## Canonical Action Test

```python
import pytest
from unittest.mock import MagicMock, patch

from ..actions.ping import Ping


class TestPing:
    def test_ping_success(self, mock_siemplify, mock_abuseipdb_client):
        mock_abuseipdb_client.test_connectivity.return_value = True

        with patch("..actions.ping.AbuseIPDBManager", return_value=mock_abuseipdb_client):
            Ping(name="Ping").run()

        mock_siemplify.end.assert_called_once()
        args = mock_siemplify.end.call_args.args
        assert args[1] == "true"                        # result_value
        assert "Connection Established" in args[0]       # output_message

    def test_ping_invalid_api_key(self, mock_siemplify, mock_abuseipdb_client):
        from ..core.errors import AbuseIPDBInvalidAPIKeyManagerError
        mock_abuseipdb_client.test_connectivity.side_effect = AbuseIPDBInvalidAPIKeyManagerError()

        with patch("..actions.ping.AbuseIPDBManager", return_value=mock_abuseipdb_client):
            Ping(name="Ping").run()

        mock_siemplify.end.assert_called_once()
        output_message, result_value, status = mock_siemplify.end.call_args.args
        assert result_value == "false"
        assert "Invalid API key" in output_message

    def test_ping_generic_error(self, mock_siemplify, mock_abuseipdb_client):
        mock_abuseipdb_client.test_connectivity.side_effect = Exception("Unexpected")

        with patch("..actions.ping.AbuseIPDBManager", return_value=mock_abuseipdb_client):
            Ping(name="Ping").run()

        output_message, result_value, status = mock_siemplify.end.call_args.args
        assert result_value == "false"
        assert "General error" in output_message
```

Three tests per action minimum: **happy path, specific error (auth), generic error**.

## Parametrized Tests for Enrichment Actions

```python
@pytest.mark.parametrize(
    "score,threshold,expected_suspicious",
    [
        (30, 50, False),
        (50, 50, True),
        (75, 50, True),
        (100, 50, True),
        (0, 50, False),
    ],
)
def test_threshold_logic(score, threshold, expected_suspicious):
    entity = MagicMock()
    entity.is_suspicious = False
    _apply_threshold(entity, score, threshold)
    assert entity.is_suspicious is expected_suspicious
```

Cover the boundary conditions explicitly.

## Testing Pydantic Models

```python
def test_report_parses_valid_response():
    r = AbuseIpReport.model_validate({
        "ipAddress": "8.8.8.8",
        "isPublic": True,
        "ipVersion": 4,
        "abuseConfidenceScore": 0,
    })
    assert r.abuseConfidenceScore == 0
    assert r.countryCode is None  # optional, not provided

def test_report_rejects_invalid_score():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        AbuseIpReport.model_validate({
            "ipAddress": "8.8.8.8",
            "isPublic": True,
            "ipVersion": 4,
            "abuseConfidenceScore": 150,  # > 100 → rejected
        })
```

## test_imports.py — The Default

```python
# tests/test_defaults/test_imports.py
def test_all_action_imports():
    """Verify every action module imports without error."""
    from ..actions import ping, check_ip_reputation  # noqa: F401

def test_all_connector_imports():
    from ..connectors import my_connector  # noqa: F401

def test_core_imports():
    from ..core import abuseipdb  # noqa: F401
```

Why this matters: a missing dep or syntax error in an action file breaks the platform's load. This test catches it before push.

## Coverage Expectations

Typical bar for PR approval:

- **80%+ line coverage** for new integrations
- **90%+ for business logic in `core/`**
- Tests for **every action's happy path + at least one failure mode**
- `test_imports.py` always green

## Common Assertions

```python
# Did siemplify.end get the expected state?
mock_siemplify.end.assert_called_once_with(expected_msg, "true", EXECUTION_STATE_COMPLETED)

# Did update_entities include our enriched ones?
mock_siemplify.update_entities.assert_called_once()
called_entities = mock_siemplify.update_entities.call_args.args[0]
assert len(called_entities) == 2
assert all(e.is_suspicious for e in called_entities)

# Did the API client get called correctly?
mock_client.check_ip.assert_called_with("8.8.8.8", 30)

# Did json_results contain expected data?
add_json_call = mock_siemplify.result.add_result_json.call_args
assert "8.8.8.8" in add_json_call.args[0]
```

## Fixtures Best Practice

Define once in `conftest.py`, reuse across tests:

```python
# conftest.py
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_siemplify():
    s = MagicMock()
    s.script_name = "Test"
    s.target_entities = []
    s.execution_deadline_unix_time_ms = 999999999999999
    s.extract_configuration_param.side_effect = lambda *, param_name, **k: {
        "Api Key": "test-api-key",
        "Verify SSL": "false",
    }.get(param_name)
    return s
```

Fixtures auto-discovered by pytest. Use by parameter name in test functions.

## Next

→ **[integration_testing Package](integration-testing.md)**
