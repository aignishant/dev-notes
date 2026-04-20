# CBN & UDM

## UDM (Unified Data Model)

> *"UDM is Google SecOps' canonical event schema. Every parser's job is to transform raw vendor logs into UDM events so that downstream detection rules, search, and correlation work uniformly across every log source in the tenant."*

### Why UDM Matters

- **One schema to rule them all** — a detection rule for "admin login from anomalous country" works regardless of whether the login came from Okta, Azure AD, or Google Workspace, because all three are normalized into UDM.
- **Search consistency** — `principal.user.userid` means the same thing everywhere.
- **Compliance mapping** — standardized fields map cleanly to MITRE ATT&CK, NIST controls.

### UDM Top-Level Field Groups

| Group | Contains |
|---|---|
| `metadata` | Timestamps, event_type, product_name, vendor_name, product_event_type |
| `principal` | The actor — user, host, process that performed the action |
| `target` | The resource acted upon |
| `src` / `dst` | Network source/destination (IP, port, hostname, MAC) |
| `network` | Protocol, direction, session info |
| `security_result` | Detection info — severity, category, rule_name, threat_name |
| `about` | Auxiliary entities referenced by the event |
| `additional` | Structured extra vendor-specific fields |

### A Minimal UDM Event

```json
{
  "metadata": {
    "event_timestamp": "2025-10-15T10:30:00Z",
    "event_type": "USER_LOGIN",
    "vendor_name": "Okta",
    "product_name": "Okta"
  },
  "principal": {
    "user": { "userid": "jdoe@example.com" },
    "ip": ["203.0.113.10"],
    "location": { "country_or_region": "DE" }
  },
  "target": {
    "application": "Okta SSO"
  },
  "security_result": [
    { "action": "ALLOW", "category": "NORMAL" }
  ]
}
```

## CBN (Configuration-Based Normalization)

> *"CBN is the parser DSL used in `parser.conf` files. It's a filter-and-mutation language similar in spirit to Logstash — you declare rules that match fields in raw input and write them into UDM slots."*

### CBN Primitives

| Primitive | Purpose |
|---|---|
| **Filter** | Select fields from raw input. Supports grok patterns, JSON paths, regex, key-value extraction |
| **Mutation** | Transform + write. Supports field renames, type conversion, string manipulation, conditional logic |

### Conceptual CBN Snippet

```
filter {
  # Match the raw log format
  grok {
    match => { "message" => "%{TIMESTAMP_ISO8601:event_time} %{IP:src_ip} %{USER:user} %{WORD:action}" }
  }

  # Parse JSON payload
  json {
    source => "json_payload"
    target => "parsed"
  }

  # Conditional branching
  if [action] == "login_success" {
    mutate {
      replace => { "event.idm.read_only_udm.metadata.event_type" => "USER_LOGIN" }
    }
  }

  # Map fields to UDM
  mutate {
    replace => {
      "event.idm.read_only_udm.metadata.event_timestamp" => "%{event_time}"
      "event.idm.read_only_udm.principal.user.userid" => "%{user}"
      "event.idm.read_only_udm.principal.ip" => "%{src_ip}"
    }
  }
}
```

(Actual CBN syntax varies — this is illustrative. Your parser specialists own the exact grammar.)

### Common CBN Challenges

1. **Timestamp normalization** — vendors ship timestamps in a dozen formats. Must all land as ISO 8601 in UDM.
2. **Multi-line logs** — Some log formats span multiple lines; parsers handle joining.
3. **Nested JSON** — deeply nested payloads need recursive field extraction.
4. **Optional fields** — parser must gracefully handle missing fields without throwing.
5. **Field arrays** — UDM fields like `principal.ip[]` expect arrays; parsers must wrap scalars correctly.
6. **Enum mapping** — mapping vendor-specific action values to UDM's standardized enums (`ALLOW`, `BLOCK`, `QUARANTINE`).

## Why Connectors and Parsers Coexist

| | Parser (SIEM path) | Connector (SOAR path) |
|---|---|---|
| **Best for** | Bulk log ingestion at scale | Structured alert ingestion |
| **Output** | UDM Events | `AlertInfo` (with embedded events) |
| **Downstream consumer** | Detection rules, search | Case management, playbooks |
| **Rate** | High-volume, low per-event latency | Poll-rate bounded, per-alert processing |
| **Requires** | CBN expertise | Python API client expertise |

!!! tip "Architectural answer"
    *"We always prefer Feed + Parser for scale. Connectors exist when the third-party product doesn't expose a feed-friendly format — e.g., the only way to get CrowdStrike detections is their REST API which needs OAuth + pagination + per-detection detail fetches. That's connector territory. For raw syslog or webhook push, parser every time."*

## Next

→ **[Parser Folder Structure](structure.md)**
