# The `integration_testing` Package

## What It Is

> *"`integration_testing` is the black-box test harness ship with the Content Hub. It provides a mock SOAR platform — mocked SDK objects, mocked HTTP sessions, mocked third-party product server — so you can run actions and connectors end-to-end locally without a real SOAR instance and without real API calls."*

Lives at `packages/integration_testing/`. Wheels at `packages/integration_testing_whls/`.

## Installation

```toml
[dependency-groups]
dev = ["integration_testing"]

[tool.uv.sources]
integration_testing = { path = "../../../../packages/integration_testing_whls/integration_testing-X.Y.Z-py3-none-any.whl" }
```

## The Mock SOAR Platform

Without `integration_testing`, testing an action means mocking `SiemplifyAction` yourself — tedious and error-prone. With it, you get a pre-built mock that handles:

- Configuration parameters
- Target entities
- Logger
- Context data
- Result recording
- `end()` capture

## Session Mock Pattern — `tests/core/session.py`

Every integration's tests typically contain a `session.py` that mocks the HTTP session used by the API client:

```python
# tests/core/session.py
from unittest.mock import MagicMock

class MockSession:
    def __init__(self):
        self.get = MagicMock()
        self.post = MagicMock()
        self.put = MagicMock()
        self.delete = MagicMock()
        self.headers = {}
        self._expected_calls = []

    def expect(self, method, path, response_json, status=200):
        self._expected_calls.append((method, path, response_json, status))
        # Configure MagicMock to return appropriate response
        ...
```

Inject this into the API client during test:

```python
def test_check_ip(mock_session):
    mock_session.expect("GET", "/api/v2/check", {"data": {"abuseConfidenceScore": 75}})
    client = AbuseIPDBManager(api_key="fake", session=mock_session)
    result = client.check_ip("8.8.8.8", 30)
    assert result.abuseConfidenceScore == 75
```

## Product Mock Pattern — `tests/core/product.py`

More sophisticated — a fake third-party server with realistic state:

```python
# tests/core/product.py
class MockAbuseIPDBProduct:
    def __init__(self):
        self.reports = {}  # ip → report data

    def add_report(self, ip, score, country="US", isp="Test ISP"):
        self.reports[ip] = {
            "ipAddress": ip,
            "abuseConfidenceScore": score,
            "countryCode": country,
            "isp": isp,
            "isPublic": True,
            "ipVersion": 4,
        }

    def check_ip(self, ip):
        if ip not in self.reports:
            return None
        return {"data": self.reports[ip]}

    def set_rate_limited(self):
        self._rate_limited = True
```

```python
@pytest.fixture
def product():
    p = MockAbuseIPDBProduct()
    p.add_report("8.8.8.8", score=0)
    p.add_report("1.2.3.4", score=80)
    return p
```

Use it in tests by routing the API client through the mock:

```python
def test_enrich_malicious_ip(mock_siemplify, product):
    mock_siemplify.target_entities = [make_entity("1.2.3.4", EntityTypes.ADDRESS)]
    # Patch the API call to hit the mock product
    with patch.object(AbuseIPDBManager, "check_ip", side_effect=lambda ip, _: product.check_ip(ip)):
        CheckIpReputation(name="Check IP Reputation").run()
    # Verify entity marked suspicious
    updated = mock_siemplify.update_entities.call_args.args[0]
    assert updated[0].is_suspicious is True
```

## End-to-End Action Test

With the mock product + mock siemplify, you can run the entire action class:

```python
def test_enrich_multiple_entities_mixed_results(mock_siemplify, product, mock_session):
    # Set up entities: one clean, one suspicious, one not-in-db
    mock_siemplify.target_entities = [
        make_entity("8.8.8.8", EntityTypes.ADDRESS),       # clean
        make_entity("1.2.3.4", EntityTypes.ADDRESS),       # suspicious
        make_entity("9.9.9.9", EntityTypes.ADDRESS),       # missing
    ]

    # Set up product state
    product.add_report("8.8.8.8", score=0)
    product.add_report("1.2.3.4", score=85)

    # Run action
    action = CheckIpReputation(name="Check IP Reputation")
    action.soar_action = mock_siemplify
    action.run()

    # Verify outcomes
    enriched_entities = mock_siemplify.update_entities.call_args.args[0]
    assert len(enriched_entities) == 2   # only the two found

    suspicious = [e for e in enriched_entities if e.is_suspicious]
    assert len(suspicious) == 1
    assert suspicious[0].identifier == "1.2.3.4"

    # Verify output_message mentions missing entities
    output_message = mock_siemplify.end.call_args.args[0]
    assert "9.9.9.9" in output_message
    assert "missing" in output_message.lower() or "not found" in output_message.lower()
```

## Connector Testing

Same pattern extended to connectors. Mock `SiemplifyConnectorExecution`:

```python
def test_connector_fetches_alerts(mock_siemplify_connector, mock_product):
    mock_product.add_alert(id=1, severity="High", title="Phishing")
    mock_product.add_alert(id=2, severity="Low", title="Spam")

    connector = MyConnector(script_name="MyConnector")
    connector._siemplify = mock_siemplify_connector
    # patch API client to read from mock_product
    ...
    connector.start()

    # Verify two AlertInfos were returned
    returned = mock_siemplify_connector.return_package.call_args.args[0]
    assert len(returned) == 2
```

## Connector Idempotency Test

The critical test — run the connector twice, second run should produce zero alerts:

```python
def test_connector_idempotent_across_runs(mock_siemplify_connector, mock_product):
    mock_product.add_alert(id=1)

    # First run
    connector = MyConnector(script_name="MyConnector")
    connector._siemplify = mock_siemplify_connector
    connector.start()
    first_run_count = len(mock_siemplify_connector.return_package.call_args.args[0])
    assert first_run_count == 1

    # Second run — no new alerts added
    mock_siemplify_connector.return_package.reset_mock()
    connector.start()
    second_run_count = len(mock_siemplify_connector.return_package.call_args.args[0])
    assert second_run_count == 0, "Connector should be idempotent — no new alerts"
```

Fails loudly if the connector re-emits alerts on repeated runs.

## Common Integration-Test Pitfalls

| Pitfall | Fix |
|---|---|
| Real HTTP calls in tests | Always use mock session / mock product. `pytest-socket` can forbid network at CI level. |
| Timestamp tests fail on fast/slow machines | Use `freezegun` or inject time via a Clock dependency |
| Flaky tests from shared state | Use `function`-scoped fixtures, not `session` |
| Mocking the wrong layer | Mock the HTTP session, not the API client — otherwise you test the mock, not the code |
| Forgetting the second-run idempotency test for connectors | **Always** test it — otherwise you ship duplicates to production |

## Next

→ **[Mocking Third-Party APIs](mocking.md)**
