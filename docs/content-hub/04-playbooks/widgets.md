# Playbook Widgets

Recap from Section 3: there are **two kinds of widgets** in Google SecOps:

| Flavor | Lives in | Rendered in | Data source |
|---|---|---|---|
| **Predefined widget** | Integration's `widgets/` dir | Alert view | An Action's JSON Result |
| **Playbook widget** | Playbook's `widgets/` dir | Case overview | Playbook step outputs |

This page focuses on the **second** — playbook widgets.

## File Layout

```
my_playbook/
└── widgets/
    ├── incident_summary.html
    ├── incident_summary.yaml
    ├── risk_dashboard.html
    └── risk_dashboard.yaml
```

Each widget = one HTML + one YAML.

## Widget YAML

```yaml
name: Incident Summary
description: Top-line metrics for the case
scope: case                           # case | alert
type: html                            # html | table | json | markdown
data_definition:
  html_height: 300
  safe_rendering: true
default_size: full_width              # half_width | full_width
condition_group:
  logical_operator: and
  conditions:
    - field_name: "[enrich_all_iocs_step.JsonResult]"
      match_type: not_contains
      value: "enrich_all_iocs_step"
data_sources:
  - step_id: enrich_all_iocs_step
  - step_id: virus_total_step
```

`data_sources[]` explicitly declares which step outputs the widget needs — the platform pre-resolves these before rendering.

## HTML with Placeholders

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    .card { background: var(--card-bg); padding: 16px; border-radius: 8px; }
    .metric { font-size: 24px; font-weight: bold; }
    .metric.bad { color: #c00; }
    .metric.good { color: #080; }
  </style>
</head>
<body>
  <div class="card">
    <h2>Incident Summary for Case [Case.id]</h2>
    <p>Alert Name: <strong>[Alert.name]</strong></p>
    <p>Severity: <strong>[Alert.severity]</strong></p>
    <p>IoCs Enriched:
       <span class="metric">[enrich_all_iocs_step.JsonResult.total_enriched]</span></p>
    <p>Malicious IoCs:
       <span class="metric bad">[enrich_all_iocs_step.JsonResult.total_malicious]</span></p>
    <p>VirusTotal Score:
       <span class="metric">[virus_total_step.JsonResult.score]</span></p>
  </div>
</body>
</html>
```

Placeholder grammar: same as predefined widgets — `[step_id.JsonResult.path]`, `[Alert.*]`, `[Case.*]`.

## Four Built-In Widget Types

When HTML is overkill:

### Table Widget

```yaml
name: Enriched Entities Table
type: table
data_sources:
  - step_id: enrich_all_iocs_step
    json_path: "JsonResult.entities"
columns:
  - header: Entity
    json_field: identifier
  - header: Type
    json_field: type
  - header: VT Score
    json_field: vt_score
  - header: AbuseIPDB Score
    json_field: abuse_score
```

### JSON Widget

Collapsible tree view of the raw JSON.

```yaml
name: Raw VirusTotal Response
type: json
data_sources:
  - step_id: virus_total_step
    json_path: "JsonResult"
```

### Markdown Widget

Renders Markdown content.

```yaml
name: Analyst Notes
type: markdown
content: |
  ## Analyst Runbook
  - Review VT score above; score ≥ 60 is suspicious
  - Confirm entity `[EntityIdentifier]` is not in the allowlist
  - Contact the responsible team if severity is Critical
```

### HTML Widget

What we've been showing — full custom HTML.

## When to Use Which

| Need | Use |
|---|---|
| Display a list of records with columns | `table` |
| Let analyst see the raw API response | `json` |
| Write a runbook blurb | `markdown` |
| Custom visualization (chart, timeline) | `html` with `safe_rendering: false` |

Start with built-ins; drop to HTML only when you need customization.

## Case vs Alert Scope

```yaml
scope: case     # Widget appears on case overview
scope: alert    # Widget appears on alert details view
```

Alert-scoped widgets see only the triggering alert's steps; case-scoped widgets can pull from steps across all alerts in the case.

## Multi-Alert Aggregation (Case Scope)

A case-scoped widget might aggregate across multiple alerts:

```html
<p>Total Alerts in Case: [Case.alert_count]</p>
<p>Total Malicious IoCs:
   [Sum(enrich_all_iocs_step.JsonResult.total_malicious)]</p>
```

Aggregation functions like `Sum()`, `Avg()`, `Max()`, `Count()` aren't universally supported — check your platform version before relying on them; otherwise do the aggregation inside a step and render the scalar.

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Placeholder resolves to literal `[step_id.JsonResult]` | Step didn't run — add a condition guard |
| Widget renders before slow step completes | Use `condition_group` guarding on step completion |
| Hardcoded colors ignore dark mode | Use CSS variables (`var(--text-color)`) |
| No fallback for missing data | Render `—` or hide section when field absent |

## Widget Iteration During Dev

1. Edit HTML + YAML
2. `mp validate playbook <n>` — catch YAML issues
3. Push playbook: `mp dev-env push playbook <n>`
4. Open a case matching the trigger, let the playbook run
5. Inspect the case overview to see widget rendering
6. Iterate

## Next

→ **[Overviews](overviews.md)**
