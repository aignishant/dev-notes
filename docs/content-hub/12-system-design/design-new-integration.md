# Designing a New Integration

Classic interview prompt: *"Design an integration for vendor X."* Structure your answer using this 10-step framework.

## The 10-Step Framework

### 1. Discovery — What Does the Vendor Do?

Before touching code, answer:

- **Primary purpose:** EDR? Threat Intel? Ticketing? Cloud security posture?
- **Customer journeys:** What analyst actions does the SOAR user need?
- **Auth model:** API key? OAuth 2.0 client credentials? Multi-step login?
- **Rate limits:** Requests per minute, per day, per quota type?
- **Data volume:** How many alerts/events per day per typical customer?
- **Webhook support?** Alternative to polling.

### 2. Folder Structure

```
crowdstrike_falcon/
├── actions/
├── connectors/
├── jobs/
├── widgets/
├── core/
│   ├── falcon_client.py
│   ├── auth.py
│   └── data_models/
├── resources/
├── tests/
├── definition.yaml
├── ontology_mapping.yaml
├── pyproject.toml
└── release_notes.yaml
```

### 3. `definition.yaml` — Integration-Level Config

```yaml
identifier: CrowdStrikeFalcon
name: CrowdStrike Falcon
description: Endpoint Detection and Response integration for CrowdStrike Falcon
parameters:
  - name: API Root
    type: string
    is_mandatory: true
    default_value: https://api.crowdstrike.com
  - name: Client ID
    type: string
    is_mandatory: true
  - name: Client Secret
    type: password
    is_mandatory: true
  - name: Verify SSL
    type: boolean
    default_value: true
categories:
  - Security
  - Endpoint
svg_logo_path: resources/logo.svg
image_path: resources/image.png
```

### 4. Core API Client (`core/falcon_client.py`)

```python
class FalconClient:
    def __init__(self, api_root, client_id, client_secret, verify_ssl=True):
        self._auth = FalconOAuth(api_root, client_id, client_secret)
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.base_url = api_root

    def test_connectivity(self) -> bool:
        self._request("GET", "/user-management/queries/user-uuids-by-email/v1")
        return True

    def get_device(self, host_id: str) -> DeviceDetails: ...
    def isolate_host(self, host_id: str) -> None: ...
    def unisolate_host(self, host_id: str) -> None: ...
    def list_detections(self, since: int, limit: int = 100) -> DetectionPage: ...
    def get_detection_detail(self, id: str) -> DetectionDetail: ...
    def update_detection_status(self, id: str, status: str) -> None: ...
    def batch_get_detections(self, ids: list[str]) -> list[DetectionDetail]: ...
```

Custom exceptions: `FalconAuthError`, `FalconRateLimitError`, `FalconNotFoundError`, `FalconServerError`.

### 5. Ping Action

Trivial: instantiate client, call `test_connectivity()`, return true/false with clear error.

### 6. Service-Specific Actions by Analyst Journey

Group by what the SOC does:

**Enrichment:**
- `Enrich Host` — HOSTNAME entity → get_device → enrichment
- `Enrich User` — USER entity → get user incidents/detections
- `Get Detection Details` — parameter-based detection lookup

**Remediation:**
- `Isolate Host` — HOSTNAME entity → isolate_host
- `Unisolate Host` — HOSTNAME entity → unisolate_host
- `Run On-Demand Scan` — HOSTNAME entity → trigger_scan

**Triage:**
- `Update Detection Status` — set detection to triaged/closed
- `Add Comment to Detection`

Each action has:
- Entity-based or parameter-based inputs per analyst expectation
- Predefined widget when JSON result benefits from visualization (Detection Details → kill-chain viz)
- Four-bucket error categorization for entity iteration

### 7. Connector

`connectors/falcon_detections.py`:

- Poll `/detections/queries/detects/v1` for IDs since last_run
- Batch fetch details via `/detections/entities/summaries/GET/v1`
- Use cursor-based pagination (CrowdStrike supports `offset`)
- Processed-IDs cache in context
- `Max Alerts Per Cycle`, `Severity Filter`, `Max Hours Backwards` params
- Environment extraction via EnvironmentCommon

### 8. Ontology Mapping

`ontology_mapping.yaml` at Product level:

```yaml
# Conceptual
source:
  product:
    name: CrowdStrikeFalcon
    events:
      - event_type: default
        mappings:
          start_time: $.created_timestamp
          end_time: $.max_confidence_timestamp
          entities:
            - type: HOSTNAME
              field: $.device.hostname
            - type: USER
              field: $.behaviors[*].user_name
            - type: FILEHASH
              field: $.behaviors[*].sha256
            - type: ADDRESS
              field: $.device.external_ip
```

`start_time` and `end_time` are CRITICAL for case grouping.

### 9. Jobs (If Needed)

`jobs/sync_detection_status.py`:
- Mirror SOAR case status changes to Falcon detection status
- Loop-prevention via author tag
- Scheduled every 5-10 minutes

### 10. Tests

- `tests/core/product.py` — mock Falcon server with preloaded detections, hosts
- `tests/core/session.py` — mock HTTP session
- `tests/test_defaults/test_imports.py` — can import everything
- `tests/test_actions/test_ping.py` — happy path + auth fail + generic fail
- `tests/test_actions/test_isolate_host.py` — per-entity behavior
- `tests/test_connectors/test_falcon_detections.py` — idempotency, pagination, rate-limit handling

Target 80%+ coverage.

## Release Plan

- `release_notes.yaml`:

```yaml
- description: Initial release of CrowdStrike Falcon integration.
  integration_version: 1.0.0
  item_name: CrowdStrike Falcon
  item_type: Integration
  new: true
  publish_time: '2026-01-15'
```

- File under `content/response_integrations/third_party/partner/crowdstrike_falcon/` (if CrowdStrike supports officially) or `community/` otherwise

## Common Pitfalls in Interview Answers

| Pitfall | Correction |
|---|---|
| Skipping ping action | "Every integration ships a Ping action first — connectivity sanity" |
| Forgetting ontology mapping | "Connector requires `ontology_mapping.yaml` with `start_time`/`end_time`" |
| Not mentioning batch endpoints | "I'd use Falcon's batch summaries endpoint, not per-ID fetches" |
| Hardcoding secret in code | "`Client Secret` is `type: password` — encrypted at rest" |
| Missing tests | "Tests are a PR gate; I'd write them alongside each action" |

## Next

→ **[Multi-Tenant Considerations](multi-tenant.md)**
