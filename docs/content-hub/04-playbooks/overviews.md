# Overviews

`overviews.yaml` is the playbook's "store page" — what users see before they install.

## The File

```yaml
short_description: |
  Automated enrichment and triage of phishing alerts.

detailed_description: |
  Triggers on any High-severity alert whose name contains "Phishing".
  Enriches all embedded URLs, IPs, and email entities against VirusTotal,
  AbuseIPDB, and WhoisXMLAPI. Computes a composite risk score and branches:
  - Risk >= 70: escalate to SOC, tag as "phishing-confirmed"
  - Risk 30-69: tag as "phishing-review", assign to Level-1 queue
  - Risk < 30: auto-close with comment

use_case: |
  Reduces analyst triage time for phishing from 15 min to 30 sec per alert.
  Target environments: email gateway integrations (Proofpoint, Mimecast),
  email-sourced alerts in SIEM detection rules.

prerequisites:
  - VirusTotal integration configured with a Premium API key
  - AbuseIPDB integration configured
  - WhoisXMLAPI integration configured
  - SOC queue "phishing-review" set up in SOAR
  - Tags "phishing-confirmed", "phishing-review", "phishing-auto-closed" created
```

## Field Schema

| Field | Purpose |
|---|---|
| `short_description` | One-line catalog subtitle |
| `detailed_description` | Multi-paragraph behavior description |
| `use_case` | When to install — who benefits |
| `prerequisites` | What must be configured first |
| `intended_audience` | (optional) "SOC L1", "Incident Response", "Threat Hunting" |
| `estimated_runtime` | (optional) Typical completion time |

## Write This Like Marketing Copy

This is what users read. Poor overviews = low adoption. Three rules:

1. **Concrete outcomes** — *"reduces triage time from 15 min to 30 sec"* beats *"automates enrichment"*
2. **Honest scope** — if you only handle URL-based phishing, say so
3. **Name prerequisites** — analysts hate installing a playbook and discovering mid-incident it needs 3 other integrations

## Overview vs display_info — Don't Confuse

| File | Target consumer | Content |
|---|---|---|
| `display_info.yaml` | UI renderer | Name, author, description, category tags |
| `overviews.yaml` | End user reading the catalog | Full product-page content |

Both are shown in the UI, but `display_info` fills the tile and `overviews` fills the detail panel.

## Next

Section 4 conceptual pages done. → **[Interview Q&A](questions.md)**
