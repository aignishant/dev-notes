# `definition.yaml` — Explained

`definition.yaml` is the integration's identity card. Interviewers ask about it because it's the contract between your integration and the platform UI.

## Real Example (AbuseIPDB)

```yaml
identifier: AbuseIPDB
name: AbuseIPDB
parameters:
  - name: Api Key
    type: password
    description: ''
    is_mandatory: true
    integration_identifier: AbuseIPDB
  - name: Verify SSL
    default_value: true
    description: ''
    type: boolean
    is_mandatory: false
    integration_identifier: AbuseIPDB
categories:
  - Security
  - Threat Intelligence
svg_logo_path: resources/logo.svg
image_path: resources/image.png
```

## Field-by-Field

| Field | Type | Required | Purpose |
|---|---|---|---|
| `identifier` | string | ✅ | Platform-unique identifier. Referenced by every action/connector/job YAML via `integration_identifier:`. **Never changes** after release. |
| `name` | string | ✅ | Display name in the Content Hub UI. Can differ from identifier. |
| `description` | string | recommended | Short description shown in catalog |
| `parameters[]` | list | ✅ | Integration-level config rendered in SOAR UI when admin configures the integration |
| `categories[]` | list[string] | ✅ | Tags for filtering in the catalog (e.g. `Security`, `Threat Intelligence`, `Endpoint`) |
| `svg_logo_path` | string | ✅ | Relative path to vector logo |
| `image_path` | string | ✅ | Relative path to raster logo (catalog tile) |
| `api_version` | string | sometimes | Platform API compatibility version |
| `author` | string | optional | Author name |

## Parameter Field Schema

Each `parameters[]` entry:

```yaml
- name: Api Root                        # Display label in UI
  type: string                          # string | password | boolean | integer | ddl | multi_choice | content_url
  description: 'Base URL of the API'    # Help text in UI
  is_mandatory: true                    # Red asterisk in UI if true
  default_value: https://api.example.com
  integration_identifier: AbuseIPDB     # Must match top-level identifier
  # For ddl / multi_choice:
  optional_values:
    - Option1
    - Option2
```

## Parameter Types

| Type | UI control | Python coercion |
|---|---|---|
| `string` | Text input | `str` |
| `password` | Masked input, stored encrypted | `str` |
| `boolean` | Toggle | `bool` |
| `integer` | Number input | `int` |
| `ddl` | Dropdown (single select) | `str` |
| `multi_choice` | Multi-select | CSV `str` → parse to `list[str]` |
| `content_url` | URL field | `str` |
| `script` | Multi-line (for scripts/expressions) | `str` |

## The `password` Type — Security Note

`type: password` tells the platform to:

1. Store the value **encrypted** at rest
2. Mask the value in logs (`*****`)
3. Never expose it via the API — only pass it to the running integration
4. Require re-entry on changes (can't be read back)

**Always** use `password` for API keys, OAuth client secrets, passwords. Never `string`.

## Categories — The Standard Set

Common categories used across the repo:

- `Security`
- `Threat Intelligence`
- `Endpoint`
- `Email`
- `Communication`
- `Ticketing`
- `Cloud`
- `Network`
- `SIEM`
- `Identity & Access Management`
- `Data Enrichment`

Using non-standard categories is allowed but reviewed — stick to existing ones unless there's genuine need.

## Integration Identifier Rules

- **Unique across the entire platform** (not just your tenant)
- **Must never change** after release (breaks customer playbook references)
- **Case-sensitive** — `AbuseIPDB` ≠ `abuseipdb`
- **PascalCase** by convention (though spaces are allowed: `Microsoft Graph Security Tools`)

This value is the **primary key** the platform uses to link actions, connectors, jobs, widgets, ontology, and customer configs. Treat it as immutable.

## The `integration_identifier:` Field Inside Parameters

Every parameter repeats the top-level identifier:

```yaml
parameters:
  - name: Api Key
    integration_identifier: AbuseIPDB   # <-- here
```

Yes, it's redundant. It's a legacy artifact from before `definition.yaml` was unified. `mp validate` checks it matches the top-level `identifier:` — if it doesn't, validation fails.

## `svg_logo_path` vs `image_path`

- `svg_logo_path` — **SVG**, used in the product UI and any resizable surface. Preferred because it scales.
- `image_path` — **PNG**, used in the catalog tile and places that can't render SVG. Typically `256x256` or `512x512`.

Both must exist under `resources/` and be referenced by relative path.

## A Fuller Example (Hypothetical Connector Integration)

```yaml
identifier: MyProduct
name: My Product
description: Detection and response integration for My Product
api_version: 2
parameters:
  - name: API Root
    type: string
    description: 'Base URL, e.g. https://api.myproduct.com'
    is_mandatory: true
    default_value: https://api.myproduct.com
    integration_identifier: MyProduct
  - name: API Key
    type: password
    description: 'API key with read + write scope'
    is_mandatory: true
    integration_identifier: MyProduct
  - name: Verify SSL
    type: boolean
    default_value: true
    description: 'Enable SSL certificate verification'
    is_mandatory: false
    integration_identifier: MyProduct
  - name: Request Timeout (sec)
    type: integer
    default_value: 30
    description: 'Per-request timeout in seconds'
    is_mandatory: false
    integration_identifier: MyProduct
categories:
  - Security
  - Endpoint
svg_logo_path: resources/logo.svg
image_path: resources/image.png
author: Acme Inc.
```

## Validation Rules `mp validate` Enforces

- `identifier` is set, unique, and used consistently
- Every `parameters[].integration_identifier` matches
- Logo files exist at declared paths
- `categories` non-empty
- `type` is a known value
- `password`-type params don't have `default_value` (security — prevents accidental commits)
- `is_mandatory` is a bool, not a string
- Action YAMLs reference only existing integration identifier

## Common Mistakes

| Mistake | Impact |
|---|---|
| Renaming `identifier` after release | **Breaks every customer's playbook** — forbidden |
| `default_value` on a `password` param | **Credential leak** — `mp validate` rejects it |
| Missing `svg_logo_path` or file | Catalog shows broken image icon |
| Wrong case in `integration_identifier` inside param | Action fails to load |
| `type: string` for an API key | Stored plaintext — serious security bug |

## Next

→ **[Interview Q&A](questions.md)**
