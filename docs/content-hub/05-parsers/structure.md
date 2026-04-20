# Parser Folder Structure

## Where Parsers Live

```
content/parsers/
└── third_party/
    ├── community/
    │   └── VENDOR1_PRODUCT1/
    │       └── cbn/
    │           ├── parser.conf
    │           ├── metadata.json
    │           ├── README.md        # optional
    │           └── testdata/
    │               ├── testcase1_logs.json
    │               └── testcase1_events.json
    ├── partnerA/
    │   └── VENDOR_PRODUCT/
    │       └── cbn/
    └── partnerB/
        └── VENDOR_PRODUCT/
            └── cbn/
```

!!! note "Directory convention"
    The parser folder is named `VENDOR_PRODUCT` (uppercase, underscored). The `cbn/` subfolder holds the actual parser — the container `VENDOR_PRODUCT` can hold multiple parser variants per product down the road.

## Required Files

### 1. `parser.conf`

The parser itself, in CBN syntax. Authoritative source of the parsing logic.

### 2. `metadata.json`

```json
{
  "log_type": "AZURE_AD",
  "product": "Azure Active Directory",
  "vendor": "Microsoft",
  "supported_format": "SYSLOG,CSV",
  "category": "Identity and Access Management",
  "description": "Parses audit logs from Azure AD.",
  "references": "https://learn.microsoft.com/en-us/azure/active-directory/reports-monitoring/"
}
```

Field glossary:

| Field | Required | Meaning |
|---|---|---|
| `log_type` | recommended | SecOps LogType identifier (`APACHE`, `GCP_CLOUDAUDIT`, `AZURE_AD`). Must be known or pre-approved. |
| `product` | ✅ | Human-readable product name |
| `vendor` | ✅ | Vendor name |
| `supported_format` | recommended | Input formats (`SYSLOG`, `JSON`, `CSV`, `KV`, `XML`) |
| `category` | recommended | Group in the hub |
| `description` | recommended | One-paragraph description |
| `references` | recommended | Public docs link for log format |

### 3. `testdata/` directory

Test logs + expected UDM output pairs:

```
testdata/
├── testcase1_logs.json           # Raw input
├── testcase1_events.json         # Expected UDM output
├── testcase2_logs.json
├── testcase2_events.json
└── ...
```

The validator pairs files by **`testcaseN_` prefix**. Multi-case support lets you cover multiple log variants (login event, failed login, admin action, etc.) in one parser.

### 4. `README.md` (optional)

- Log format quirks
- Known limitations
- Vendor-version compatibility notes

## The `log_type` Gate

- Must be either (a) **an existing, known SecOps LogType**, or (b) a **pre-approved new LogType**
- New LogTypes require coordination with the internal SecOps team — you can't just invent one
- Validation explicitly checks: *"no new logtype is added without support from internal team"*

## Multiple Parsers per Vendor

A single vendor can ship multiple parsers, one per product:

```
content/parsers/third_party/community/
├── MICROSOFT_AZURE_AD/
│   └── cbn/
├── MICROSOFT_DEFENDER/
│   └── cbn/
└── MICROSOFT_OFFICE_365/
    └── cbn/
```

Each is independently versioned and reviewed.

## Partner Parsers vs Community Parsers

Same structure — different location:

- Community: `content/parsers/third_party/community/VENDOR_PRODUCT/cbn/`
- Partner: `content/parsers/third_party/partnerA/VENDOR_PRODUCT/cbn/`

(Unlike integrations, where partner is `third_party/partner/` singular, parsers use `partnerA`/`partnerB` keyed by partner name.)

## Prerequisites for Contribution

The repo docs are strict:

1. **CLA signed**
2. **`chronicle.admin` role** in the tenant where the log-type data is ingested
3. **≥1,000 log entries ingested** of the target log type (ensures realistic testing)
4. **`chronicle.parsers.run`** permission for local testing
5. **PII scrubbed** from testdata — contributor's responsibility, enforced via review

## Next

→ **[Test Data & Validation](testdata.md)**
