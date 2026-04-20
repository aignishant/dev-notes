# Pydantic

## Role in the Repo

> *"Pydantic is the data validation and settings-management library used for API response parsing, third-party data shapes, and configuration models. It gives you runtime validation, IDE autocompletion, and typed serialization/deserialization in a single declarative class."*

From the deep-dive docs: *"Use Pydantic for data validation and serialization/deserialization."*

## Why Pydantic vs `@dataclass`

| | `@dataclass` | **Pydantic** |
|---|---|---|
| **Runtime validation** | ❌ | ✅ |
| **Type coercion** | ❌ | ✅ (string → int, etc.) |
| **JSON (de)serialization** | Manual | Built-in (`model_dump_json`) |
| **Field validators** | ❌ | ✅ |
| **Nested model support** | Limited | Full |
| **Performance** | Pure Python | Pydantic v2 is Rust-backed — very fast |

## Where You'll Use Pydantic

### 1. Third-Party API Response Models

```python
from pydantic import BaseModel, Field
from datetime import datetime

class AbuseIpReport(BaseModel):
    ipAddress: str
    isPublic: bool
    ipVersion: int
    isWhitelisted: bool | None = None
    abuseConfidenceScore: int = Field(ge=0, le=100)
    countryCode: str | None = None
    usageType: str | None = None
    isp: str | None = None
    domain: str | None = None
    hostnames: list[str] = []
    totalReports: int = 0
    numDistinctUsers: int = 0
    lastReportedAt: datetime | None = None

class AbuseIpResponse(BaseModel):
    data: AbuseIpReport
```

```python
response = requests.get(...)
parsed = AbuseIpResponse.model_validate(response.json())
score = parsed.data.abuseConfidenceScore  # typed + validated
```

**Wins:** unexpected fields raise; type mismatches raise; you get autocomplete on `parsed.data.isp`.

### 2. Internal Data Models

For passing typed data through your integration:

```python
class EnrichmentResult(BaseModel):
    entity_id: str
    score: int
    is_malicious: bool
    tags: list[str] = []
    verdict_source: str
```

Use across your `core/` module methods. Eliminates bare-dict passing.

### 3. Configuration

```python
class ClientConfig(BaseModel):
    api_root: str
    api_key: str
    verify_ssl: bool = True
    timeout: int = Field(30, gt=0, le=300)
```

```python
config = ClientConfig(
    api_root=self.params.api_root,
    api_key=self.params.api_key,
    verify_ssl=self.params.verify_ssl,
)
client = AbuseIPDBClient(config)
```

## Field Validators

```python
from pydantic import BaseModel, field_validator

class IPReport(BaseModel):
    ip: str

    @field_validator("ip")
    @classmethod
    def must_be_public(cls, v: str) -> str:
        import ipaddress
        addr = ipaddress.ip_address(v)
        if addr.is_private:
            raise ValueError(f"IP {v} is private — cannot be enriched")
        return v
```

Validators run automatically on construction.

## Serialization

```python
report = AbuseIpReport(...)
report.model_dump()          # → dict
report.model_dump_json()     # → JSON string
```

Reverse:

```python
AbuseIpReport.model_validate(some_dict)
AbuseIpReport.model_validate_json(json_str)
```

Used when setting `self.json_results` and loading from the SOAR context store.

## Pydantic v2 vs v1

Repo uses Pydantic v2 — significantly faster (Rust-backed), cleaner API:

| v1 | v2 |
|---|---|
| `parse_obj` | `model_validate` |
| `parse_raw` | `model_validate_json` |
| `dict()` | `model_dump()` |
| `json()` | `model_dump_json()` |
| `@validator` | `@field_validator` |
| `Config` inner class | `model_config = ConfigDict(...)` |

If you see v1 syntax in legacy code, it's a migration candidate.

## The JetBrains Pydantic Plugin

Repo setup guide recommends installing the **Pydantic** JetBrains plugin:

> *"Purpose: Enhanced support for Pydantic models"*

Adds better autocomplete inside Pydantic models, field resolution, model_validate type inference.

## Pydantic Patterns for Third-Party APIs

### Allow Extra Fields

Third parties add new fields without notice. Default is strict; allow extras to survive vendor updates:

```python
from pydantic import ConfigDict

class AbuseIpReport(BaseModel):
    model_config = ConfigDict(extra="allow")   # extras silently kept
    # or "ignore" to drop them, "forbid" to error
    ...
```

Recommended: `"ignore"` for API responses you want to survive schema drift; `"forbid"` for internal models where typos should fail.

### Alias for Wire Names

Third-party JSON often uses camelCase while Python uses snake_case:

```python
from pydantic import Field

class Report(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    abuse_confidence_score: int = Field(alias="abuseConfidenceScore")
    country_code: str | None = Field(None, alias="countryCode")
```

```python
r = Report.model_validate({"abuseConfidenceScore": 50, "countryCode": "US"})
r.abuse_confidence_score  # Python-native access
```

### Optional Chaining for Sparse Responses

```python
hostnames: list[str] = Field(default_factory=list)
lastReportedAt: datetime | None = None
```

Always default optional fields — third parties omit them unpredictably.

## Common Pydantic Pitfalls

| Pitfall | Fix |
|---|---|
| Missing `Field(default_factory=list)` on list fields | Use factory; bare `= []` is a trap (shared mutable default in old patterns) |
| v1 `@validator` on Pydantic v2 | Use `@field_validator` |
| Not using aliases for camelCase APIs | Wrap wire names with `Field(alias="...")` |
| Strict mode on sparse vendor responses | Switch `model_config` to `extra="ignore"` |
| Trying to `.dict()` in v2 | Use `.model_dump()` |

## Next

→ **[Type Hints](type-hints.md)**
