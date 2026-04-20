# Playbook Structure

## Folder Layout

```
my_playbook/
├── steps/
│   ├── step_1.yaml
│   ├── step_2.yaml
│   └── ...
├── widgets/
│   ├── incident_summary.html
│   └── incident_summary.yaml
├── definition.yaml           # Playbook identity + configuration
├── display_info.yaml         # UI metadata (display name, author)
├── overviews.yaml            # Catalog-facing summary
├── release_notes.yaml        # Version history
└── trigger.yaml              # When the playbook fires
```

Playbooks live at:

- `content/playbooks/third_party/community/<n>/` — community
- `content/playbooks/third_party/partner/<n>/` — partner
- `content/playbooks/google/<n>/` — Google-maintained

All folder and file names **snake_case**.

## File Purpose Matrix

| File | Required | Purpose |
|---|---|---|
| `definition.yaml` | ✅ | Playbook metadata — name, identifier, version, parameters |
| `display_info.yaml` | ✅ | Display name, description, author — shown in Content Hub UI |
| `overviews.yaml` | ✅ | Catalog summary, use case, prerequisites |
| `release_notes.yaml` | ✅ | Per-version changelog |
| `trigger.yaml` | ✅ | Entry-point event definition |
| `steps/*.yaml` | ✅ (≥1) | The playbook's execution graph |
| `widgets/*.html`+`.yaml` | Optional | Case-overview visualizations |

## `definition.yaml` — Playbook Identity

Plays the same role as the integration's `definition.yaml`:

- **`identifier`** — immutable platform key
- **`name`** — display name
- **`version`** — semver
- **`parameters`** — playbook-level inputs (rarely used; usually configured per-step)

## `display_info.yaml`

```yaml
display_name: Phishing Triage Playbook
description: Automated enrichment and triage for phishing alerts
author: Security Team
categories:
  - Phishing
  - Email
  - Triage
```

Fed directly to the catalog card users see in the Content Hub UI.

## `overviews.yaml` — The "Product Page"

```yaml
short_description: |
  Automatically enrich and triage suspected phishing alerts.

detailed_description: |
  This playbook triggers on alerts matching "Phishing" in the alert name.
  It extracts URLs, IPs, and email entities, runs them through VirusTotal,
  AbuseIPDB, and WhoisXMLAPI, evaluates a composite risk score,
  and either auto-closes (low risk) or escalates to the SOC queue (high risk).

use_case: |
  Phishing is the #1 SOC alert volume driver. This playbook reduces
  analyst triage time from 15 minutes to 30 seconds per alert.

prerequisites:
  - VirusTotal integration configured with a valid API key
  - AbuseIPDB integration configured with a valid API key
  - WhoisXMLAPI integration configured
  - SOC queue escalation channel set up
```

Users pick playbooks by reading this. Treat it as marketing copy, not developer notes.

## `trigger.yaml` — The Entry Point

```yaml
id: "b1a2b3c4-d5e6-f7g8-h9i0-j1k2l3m4n5o6"
name: "High Priority Phishing Alert Trigger"
version: 1.0
trigger_type: "alert"
conditions:
  - operator: "AND"
    rules:
      - field: "alert.name"
        operator: "contains"
        value: "Phishing"
      - field: "alert.severity"
        operator: "equals"
        value: "High"
```

Full grammar covered on **[Triggers](triggers.md)**.

## `steps/<n>.yaml`

Each step is its own file. The name of the file matters because it becomes the step's identifier within the playbook. Full format on **[Steps & Blocks](steps.md)**.

## `release_notes.yaml`

Identical schema to integration release notes:

```yaml
- description: Initial release of Phishing Triage Playbook.
  integration_version: 1.0
  item_name: Phishing Triage Playbook
  item_type: Playbook
  new: true
  publish_time: '2025-10-15'
```

## The Two Contribution Paths

### Path 1 — `mp` tool (recommended)

```bash
# Authenticate
mp dev-env login --api-root <url> --api-key <key>

# Pull from your dev SOAR (export playbook into repo-ready shape)
mp dev-env pull playbook <n> --dest ./pulled

# Edit display_info.yaml and release_notes.yaml
# Move to correct directory
mv ./pulled/<n> content/playbooks/third_party/community/

# Validate
mp validate playbook <n>

# Open PR
```

### Path 2 — Manual

```bash
# Export playbook from SOAR UI (downloads a zip)

# Deconstruct into repo-ready structure
mp build -p <n> --deconstruct --src <path-to-exported-zip>

# Fill display_info.yaml + release_notes.yaml
# Move into the right directory
# Open PR
```

## Block Reuse — The Biggest Gotcha

!!! warning "Critical contribution rule"
    If your playbook uses a Block (sub-playbook) that already exists in the repo, **do NOT duplicate it**. Instead, update your step's `NestedWorkflowIdentifier` to point at the existing block's identifier.

Procedure:

1. Find the existing block under `content/playbooks/`
2. Open `<block>/definition.yaml` → copy the `identifier` value
3. In your playbook's `steps/<step>.yaml`, find the parameter `NestedWorkflowIdentifier`
4. Replace its `value:` with the copied identifier
5. Repeat for every block your playbook reuses

This makes playbooks **composable** — a core value of the catalog.

## Next

→ **[Triggers](triggers.md)**
