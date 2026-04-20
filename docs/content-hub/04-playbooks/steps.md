# Steps & Blocks

## Definition

> *"Steps are the executable building blocks of a playbook. Each step represents one action — an integration Action call, a built-in Function, a Condition branch, or a nested Block (sub-playbook). Steps are chained into a directed graph that the platform executes top-to-bottom with conditional branching."*

## The Four Step Types

### 1. Integration Action Step

The most common type — calls an action from a response integration.

```yaml
id: enrich_ip_step
name: Enrich IP with VirusTotal
type: Action
action_identifier: VirusTotal_Enrich IP
integration_identifier: VirusTotal
parameters:
  - name: Threshold
    value: "60"
  - name: Entity Type
    value: "ADDRESS"
# Inputs — entities or params
target_entities_scope: alert_entities    # or: all_entities, specific_entities
# Result routing
on_success: next_step_id
on_failure: failure_handler_step_id
```

Key fields:

| Field | Meaning |
|---|---|
| `action_identifier` | The Action's full name (prefixed with integration_identifier) |
| `integration_identifier` | Which integration provides the action |
| `parameters` | Mapped to the action YAML's `parameters` — values can be literals or placeholder expressions |
| `target_entities_scope` | Which entities to pass (alert-scoped, all, or filtered) |

### 2. Function Step

Built-in platform functions — no integration required.

**Common functions:**

- **Set Variable** — create a playbook variable
- **Add Comment** — add a comment to the case/alert
- **Change Priority** — modify case severity
- **Add Tag** — tag the case
- **Assign Case** — assign to analyst/queue
- **Close Case** — auto-close

```yaml
id: tag_auto_triaged
name: Tag as Auto-Triaged
type: Function
function_name: Add Tag
parameters:
  - name: Tag
    value: "auto-triaged"
on_success: next_step_id
```

### 3. Condition Step

Branches based on previous step output.

```yaml
id: check_reputation_score
name: Check if VT score >= threshold
type: Condition
condition_group:
  logical_operator: and
  conditions:
    - field: "[enrich_ip_step.ScriptResult]"
      operator: "equals"
      value: "true"
    - field: "[enrich_ip_step.JsonResult.malicious_count]"
      operator: "gte"
      value: "5"
on_true: escalate_step_id
on_false: auto_close_step_id
```

Conditions are where placeholder expressions shine — you reference prior step outputs via `[step_id.JsonResult.path]`.

### 4. Block Step (Nested Playbook)

Call another playbook as a sub-routine.

```yaml
id: run_phishing_block
name: Phishing Enrichment Block
type: Block
parameters:
  - name: NestedWorkflowIdentifier
    value: "bb22cc33-dd44-ee55-ff66-001122334455"   # block playbook identifier
  - name: Alert Source
    value: "[Alert.source_integration]"
on_success: next_step
```

`NestedWorkflowIdentifier` points at the nested playbook's `identifier` from its `definition.yaml`.

## Step References (Placeholder Grammar)

Every step produces output that subsequent steps can reference:

| Expression | What it resolves to |
|---|---|
| `[step_id.ScriptResult]` | Scalar Script Result of the step |
| `[step_id.JsonResult]` | Full JSON Result object |
| `[step_id.JsonResult.key]` | Dotted-path access into JSON |
| `[step_id.JsonResult.items[0].name]` | Array indexing |
| `[Alert.name]` | Parent alert's name |
| `[Alert.severity]` | Severity |
| `[Case.id]` | Case ID |
| `[EntityIdentifier]` | Current entity (inside entity-scoped steps) |
| `[Variable.VARIABLE_NAME]` | Playbook variable set by Set Variable function |

## Step Ordering & Flow Control

Steps have:

- `on_success: <next_step_id>` — normal forward link
- `on_failure: <failure_step_id>` — error-handling branch
- `on_true: <step_id>` / `on_false: <step_id>` — for Condition steps

No explicit "parallel" step — the platform can run independent branches in parallel but you express this by having the same step linked from multiple upstreams.

## Block Reuse — Why It Matters

!!! tip "The interview soundbite"
    *"Blocks let us write a 'Phishing Enrichment Block' once and reuse it from 'Phishing Low Priority', 'Phishing High Priority', 'Phishing Manual Review', etc. We avoid N copies of the same 12 steps. When we fix a bug in the block, every parent playbook inherits the fix automatically."*

### When to Extract a Block

Extract a block when:

1. The same 3+ steps repeat across multiple playbooks
2. A logical unit of work (e.g., "Enrich all IoCs", "Notify SOC") is standalone
3. You want the reused logic versioned independently

### Common Reusable Blocks in the Repo

The `power_ups/` integrations often have companion playbook blocks:

- "Enrich All IOCs" — iterates entities, calls TI actions
- "Send Enrichment Summary Email" — formats results, sends email
- "Escalate to SOC Queue" — assigns, tags, comments, notifies

## Step Timeout

Each action step has its own timeout (inherited from the action's default, overridable per-step). On timeout the step fails — you decide whether the playbook halts (default) or routes `on_failure` to a recovery step.

## Loops & Iteration

Playbooks don't have explicit `for` loops — iteration happens implicitly at the step level:

- An action step with `target_entities_scope: alert_entities` runs **once per entity** (the action is responsible for iterating internally)
- To loop over arbitrary data, you usually extract an "iterate + call sub-block" pattern

!!! warning "Don't over-loop in playbooks"
    Playbooks aren't a general-purpose DSL. If you find yourself needing complex iteration, either (a) move the iteration inside the action code, or (b) refactor the whole problem into a block that's invoked per item.

## Step Naming Conventions

- **Filename**: `<step_id>.yaml` (snake_case)
- **Step `id:`**: matches the filename (e.g., `enrich_ip_step`)
- **Step `name:`**: human-readable (e.g., `Enrich IP with VirusTotal`)
- **Never rename `id:`** after release — breaks references in other steps

## Common Step Mistakes

| Mistake | Impact |
|---|---|
| Referencing a step's JsonResult before it ran | Placeholder resolves to literal text, breaks condition |
| `target_entities_scope` mismatch with action's intent | Action receives wrong entities, silent incorrect behavior |
| Forgetting `on_failure` on critical steps | One API hiccup halts entire playbook |
| Duplicate step IDs across files | Graph becomes ambiguous; `mp validate` fails |
| Using `NestedWorkflowIdentifier` of a deleted block | Step hangs; playbook fails at runtime |

## Next

→ **[Widgets](widgets.md)**
