# Mocking Third-Party APIs

## Rule: Mock at the HTTP Session Layer

> *"Mock as low as possible. If you mock the API client's high-level method, you're testing your mock, not the code. Mock the HTTP session object — that way your `core/api_client.py` runs real parsing, error handling, and retries."*

## Three Common Mocking Libraries

| Library | Best for | Feel |
|---|---|---|
| `unittest.mock` | Per-call MagicMock | Stdlib, verbose |
| `responses` | Mocking `requests` calls | URL-based matcher, intuitive |
| `pytest-httpx` | Mocking `httpx` | Async-friendly |
| `pytest-mock` | `mocker` fixture | Cleaner syntax over unittest.mock |

Most Content Hub integrations use `responses` or `requests_mock` depending on style preference.

## `responses` Example

```python
import responses
from ..core.abuseipdb import AbuseIPDBManager

@responses.activate
def test_check_ip_success():
    responses.add(
        responses.GET,
        "https://api.abuseipdb.com/api/v2/check",
        json={"data": {"abuseConfidenceScore": 85, "countryCode": "RU", "isp": "Bad ISP",
                       "ipAddress": "1.2.3.4", "isPublic": True, "ipVersion": 4}},
        status=200,
    )

    manager = AbuseIPDBManager(api_key="test")
    result = manager.check_ip("1.2.3.4", max_days=30)

    assert result.abuseConfidenceScore == 85
    assert result.countryCode == "RU"
    assert responses.calls[0].request.headers.get("Key") == "test"
```

## Mocking Error Responses

```python
@responses.activate
def test_check_ip_rate_limited():
    responses.add(
        responses.GET,
        "https://api.abuseipdb.com/api/v2/check",
        json={"errors": [{"detail": "Daily rate limit exceeded"}]},
        status=429,
    )

    manager = AbuseIPDBManager(api_key="test")
    with pytest.raises(AbuseIPDBRateLimitError):
        manager.check_ip("1.2.3.4", max_days=30)
```

## Mocking Auth Failure

```python
@responses.activate
def test_check_ip_invalid_api_key():
    responses.add(
        responses.GET,
        "https://api.abuseipdb.com/api/v2/check",
        json={"errors": [{"detail": "Authentication failed"}]},
        status=401,
    )

    manager = AbuseIPDBManager(api_key="invalid")
    with pytest.raises(AbuseIPDBInvalidAPIKeyManagerError):
        manager.check_ip("1.2.3.4", max_days=30)
```

## Mocking Multiple Sequential Calls

For actions that iterate entities:

```python
@responses.activate
def test_iterates_three_entities():
    for i, ip in enumerate(["1.1.1.1", "2.2.2.2", "3.3.3.3"]):
        responses.add(
            responses.GET,
            "https://api.abuseipdb.com/api/v2/check",
            json={"data": {"abuseConfidenceScore": i * 30, "ipAddress": ip, "isPublic": True, "ipVersion": 4}},
            status=200,
            match=[responses.matchers.query_param_matcher({"ipAddress": ip, "maxAgeInDays": "30"})],
        )

    # ... run action that iterates these IPs ...
    assert len(responses.calls) == 3
```

Use `match` to route different responses per unique query.

## Mocking OAuth Token Refresh

```python
@responses.activate
def test_auto_refreshes_expired_token():
    # First call: token
    responses.add(
        responses.POST,
        "https://auth.example.com/oauth/token",
        json={"access_token": "new_token", "expires_in": 3600},
        status=200,
    )
    # Next call: the actual endpoint
    responses.add(
        responses.GET,
        "https://api.example.com/detections",
        json={"detections": []},
        status=200,
    )

    client = MyOauthClient(client_id="x", client_secret="y")
    client.token = None  # force refresh
    result = client.list_detections()

    assert len(responses.calls) == 2    # token + detections
    assert "Bearer new_token" in responses.calls[1].request.headers["Authorization"]
```

## Freezing Time

When code uses `datetime.now()` or `unix_now()`:

```python
from freezegun import freeze_time

@freeze_time("2025-10-15 12:00:00")
def test_timestamp_handling():
    ts = unix_now()
    assert ts == 1760529600000    # fixed Unix ms at frozen time
```

## Forbidding Real Network in CI

Add to `conftest.py`:

```python
import pytest
import socket

@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def no_socket(*a, **kw):
        raise RuntimeError("Real network call in test! Mock the HTTP layer.")
    monkeypatch.setattr(socket, "socket", no_socket)
```

Or use `pytest-socket`:

```toml
[tool.pytest.ini_options]
addopts = ["--disable-socket", "--allow-unix-socket"]
```

Any accidental real-network call fails the test immediately.

## Capturing Request Payloads

Verify your code sent the right request:

```python
@responses.activate
def test_sends_correct_auth_header():
    responses.add(responses.GET, "https://api.example.com/x", json={}, status=200)
    client = MyClient(api_key="secret")
    client.get_x()

    request = responses.calls[0].request
    assert request.headers["Authorization"] == "Bearer secret"
    assert request.headers["User-Agent"] == "MyIntegration/1.0"
```

## Common Mocking Anti-Patterns

| Anti-pattern | Why bad | Better |
|---|---|---|
| Mocking `check_ip()` method directly | Skips parsing, error handling — tests the mock | Mock HTTP session; `check_ip` runs real code |
| Single test with 10 responses | If one fails, hard to debug | Split into focused tests |
| Matching only URL, not method/headers/body | False positives, flaky | Use full matchers |
| Hardcoded timestamps in test data | Breaks at DST / timezone boundaries | Use `freezegun` |
| Forgetting `@responses.activate` | Mocks silently don't apply | Use pytest fixture that auto-activates |

## Next

→ **[Fixtures & conftest](fixtures.md)**
