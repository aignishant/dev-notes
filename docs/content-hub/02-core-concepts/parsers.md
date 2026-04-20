# Parsers

## Definition

> *"A Parser is a CBN (Configuration-Based Normalization) file that transforms raw log data — syslog, JSON, CSV, etc. — into Google SecOps' canonical UDM (Unified Data Model) event schema, so detection rules and search work uniformly across every vendor's logs. Parsers live at `content/parsers/` and feed the SIEM side of the platform, not the SOAR side."*

## Why This Matters for an Integration Lead

Most interviewers will test whether you know that **Content Hub has BOTH sides**. Missing parsers in your answer signals you only worked on SOAR content, not the full surface.

## Parser Folder Structure

```
content/parsers/
└── third_party/
    ├── community/
    │   └── VENDOR_PRODUCT/
    │       └── cbn/
    │           ├── parser.conf              # The parser code (CBN DSL)
    │           ├── metadata.json            # log_type, product, vendor, etc.
    │           ├── README.md                # Optional
    │           └── testdata/
    │               ├── testcase1_logs.json
    │               ├── testcase1_events.json       # Expected UDM output
    │               ├── testcase2_logs.json
    │               └── testcase2_events.json
    └── partnerA/
        └── VENDOR_PRODUCT/
            └── cbn/
```

## metadata.json

```json
{
  "log_type": "AZURE_AD",
  "product": "Azure Active Directory",
  "vendor": "Microsoft",
  "supported_format": "SYSLOG,CSV",
  "category": "Identity and Access Management",
  "description": "Parses audit logs from Azure AD.",
  "references": "https://learn.microsoft.com/..."
}
```

`log_type` is the authoritative SecOps LogType identifier — APACHE, GCP_CLOUDAUDIT, etc. Must be either a known LogType or an approved new one.

## CBN — The Parser DSL

CBN has two primitives:

1. **Filters** — select fields from the raw log (regex, grok-like, JSON paths)
2. **Mutations** — transform and write into UDM fields

It looks like a Logstash/Grok hybrid configured via `parser.conf`.

!!! warning "Don't claim deep CBN expertise if you don't have it"
    Unless you wrote parsers yourself, frame your knowledge as: *"I've reviewed parser PRs and understand the validation pipeline, but CBN authoring is typically done by our SIEM parser specialists — my focus was on the SOAR integration side."* Interviewers respect scoped honesty over fake confidence.

## UDM (Unified Data Model)

UDM is Google SecOps' canonical event schema. Every parser's job is to produce UDM. Key UDM field groups you might be asked about:

- `metadata` — timestamps, product, vendor, event_type
- `principal` — the actor (user, host, process)
- `target` — the affected asset
- `src` / `dst` — network source/destination (IP, port, hostname)
- `network` — protocol, direction, flow data
- `security_result` — detection info (severity, category, rule_name)

## The Parser PR Validation Pipeline

When you open a parser PR, TWO check runs MUST pass:

### 1. Validate Parsers (standalone)

- Folder structure OK
- Required files present (`metadata.json`, `*.conf`, events, test logs)
- Unit tests: parser run against `testdata/*_logs.json` matches `*_events.json`
- `log_type` uniqueness + existence in SecOps
- No unauthorized new log types

### 2. Validate Google & Parsers (live SecOps instance)

This one requires **manual triggering** by the contributor with the `secops` CLI:

```bash
secops \
  --project-id <project-id> \
  --customer-id <customer-id> \
  log-type trigger-checks \
  --associated-pr <PR number> \
  --log-type <log-type>
```

Then fetch the result:

```bash
secops \
  --project-id <project-id> \
  --customer-id <customer-id> \
  log-type get-analysis-report \
  --name <report-name>
```

The analysis measures **parse efficiency** and **UDM field coverage** against real customer logs — it flags regressions.

## Contributor Requirements

- **CLA signed**
- `chronicle.admin` role in the tenant with the log-type data ingested
- **At least 1,000 log entries** ingested for that log type in the tenant
- `chronicle.parsers.run` permission for local testing
- **PII scrubbed** from any committed testdata — the contributor's responsibility

## Multiple Test Cases per Parser

Parsers support **multiple test cases**, not just one:

```
testdata/
├── testcase1_logs.json
├── testcase1_events.json
├── testcase2_logs.json
└── testcase2_events.json
```

The validator pairs them by the `testcaseN_` prefix. This is a detail worth mentioning — it shows you understand the testing granularity.

## How Parsers Relate to Connectors

| Path | When you'd use it |
|---|---|
| **Feed + Parser (SIEM)** | Primary — bulk ingestion via SIEM feed, normalized into UDM. High volume, low latency. |
| **Connector (SOAR)** | When the third party doesn't have a feed-compatible format, or when alerts need SOAR-specific metadata. |

From `core_concepts.md`: *"in Google SecOps you can also ingest data via SIEM Feed + Parser and in general, that's the preferred method."*

!!! tip "Architectural answer"
    *"Feed + Parser is the preferred ingestion path because it scales better, normalizes to UDM for search, and is decoupled from per-alert processing. Connectors exist for cases where feed ingestion isn't feasible or alert-specific processing must happen at ingestion time — but they don't scale as linearly."*

## Next

→ **[Entities](entities.md)**
