# Triggers

## Definition

> *"A Trigger is an event listener that defines the conditions under which a playbook executes. Each playbook has exactly one trigger, defined in `trigger.yaml`. Triggers come in three types — Alert, Entity, and Manual — and use AND/OR-combined field conditions to ensure the playbook runs only in the right context."*

## The Three Trigger Types — Detailed

### 1. Alert Trigger

Fires on **alert creation OR update** matching conditions. The most common trigger type.

**Use cases:**
- Auto-enrich phishing alerts
- Auto-contain suspicious endpoint alerts
- Auto-close false-positive alerts from a known source

```yaml
trigger_type: "alert"
conditions:
  - operator: "AND"
    rules:
      - field: "alert.name"
        operator: "contains"
        value: "Phishing"
      - field: "alert.severity"
        operator: "gte"
        value: "High"
```

**Fires when:** an alert matching both conditions is created or updated.

### 2. Entity Trigger

Fires on **entity creation or update** matching conditions.

**Use cases:**
- "Whenever a new User entity appears, check leaked-credential databases"
- "Whenever a new external IP entity appears, compute base-rate reputation"

```yaml
trigger_type: "entity"
conditions:
  - operator: "AND"
    rules:
      - field: "entity.type"
        operator: "equals"
        value: "USER"
      - field: "entity.is_internal"
        operator: "equals"
        value: "false"
```

**Fires when:** any new external USER entity is created.

### 3. Manual Trigger

Fires when an **analyst clicks "Run Playbook"** in the UI — alert, case, or entity view.

**Use cases:**
- Containment playbooks (don't auto-isolate hosts)
- One-off investigation aids ("pull forensics from this machine")
- Destructive remediation requiring analyst judgment

```yaml
trigger_type: "manual"
# conditions optional — even for manual, you may restrict to certain contexts
conditions:
  - operator: "AND"
    rules:
      - field: "alert.source_integration"
        operator: "equals"
        value: "CrowdStrike"
```

## Condition Grammar

### `operator` — at the group level

| | Meaning |
|---|---|
| `AND` | All rules must match |
| `OR` | Any rule matches |

### `operator` — at the rule level

| Operator | Meaning | Example |
|---|---|---|
| `equals` | Exact match | `severity equals "High"` |
| `not_equals` | Not equal | `name not_equals "Test"` |
| `contains` | Substring/array contains | `name contains "Phishing"` |
| `not_contains` | Negation of contains | `name not_contains "Test"` |
| `starts_with` | Prefix match | `name starts_with "EDR_"` |
| `ends_with` | Suffix match | `name ends_with "_approved"` |
| `gte` / `lte` | Numeric/severity compare | `severity gte "Medium"` |
| `gt` / `lt` | Strict inequality | `count gt "10"` |
| `matches_regex` | Regex | `hostname matches_regex "^srv-.*"` |
| `in` | Value in list | `type in ["PHISHING","MALWARE"]` |

### Fields You Can Reference

**Alert fields:**

- `alert.name`
- `alert.severity` (`Info` / `Low` / `Medium` / `High` / `Critical`)
- `alert.priority`
- `alert.source_integration` — which integration's connector produced it
- `alert.device_vendor`, `alert.device_product`
- `alert.environment` — multi-env tenants
- `alert.rule_generator`
- `alert.ticket_id`
- `alert.tags[]`
- Any custom `alert.additional_properties.*`

**Entity fields:**

- `entity.type` — e.g. `ADDRESS`, `USER`, `FILEHASH`
- `entity.identifier` — the value
- `entity.is_internal`
- `entity.is_suspicious`
- `entity.additional_properties.*`

**Case fields** (for alert triggers that join case context):

- `case.id`
- `case.priority`
- `case.tags[]`
- `case.status`

## Nested Condition Groups

Some trigger systems support nested groups for complex logic:

```yaml
conditions:
  - operator: "AND"
    rules:
      - field: "alert.severity"
        operator: "gte"
        value: "High"
      - operator: "OR"              # nested group
        rules:
          - field: "alert.name"
            operator: "contains"
            value: "Phishing"
          - field: "alert.name"
            operator: "contains"
            value: "Malware"
```

"Severity ≥ High AND (name contains Phishing OR name contains Malware)"

## Fire-on-Create vs Fire-on-Update

Alert triggers fire on both by default. To restrict:

- `fire_on_create: true, fire_on_update: false` — only new alerts
- `fire_on_create: false, fire_on_update: true` — only updates (useful for "when the alert gets new events")
- Both true (default) — fires on any change

## Testing Triggers

1. Write the playbook with trigger
2. Push to dev SOAR: `mp dev-env push playbook <n>`
3. Generate a matching alert (e.g. via connector test run or manual alert creation)
4. Confirm the playbook instance appears in Playbook Runs

If it doesn't fire, check:

- Trigger type matches the event (Alert vs Entity)
- Every condition is satisfied (inspect the actual alert object)
- No conflicting trigger in another playbook stealing the event (rare but possible)

## Priority Ordering

If multiple playbooks have triggers that match the same event, they **all fire** — there's no single-winner selection. If you need mutual exclusion, add a guard condition to each playbook's trigger that ensures they don't overlap.

## Common Trigger Mistakes

| Mistake | Impact |
|---|---|
| `value: High` (unquoted) | YAML parses as enum — may not match string `"High"` in alert. Always quote. |
| Regex without anchors | `matches_regex "srv-"` matches `not-srv-1` too. Use `^srv-` or `^srv-\w+$` |
| Condition on a field the connector doesn't populate | Trigger never fires. Verify field presence in a sample alert first. |
| Trigger type mismatch | Using Alert trigger and filtering by `entity.type` — invalid. |
| Missing trigger_type | `mp validate` rejects |

## Next

→ **[Steps & Blocks](steps.md)**
