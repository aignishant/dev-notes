# Playbooks — Interview Q&A

---

## Q1. What are the three trigger types and when do you use each?

- **Alert** — most common; fires on alert create/update matching conditions. Use for rule-based automation (phishing, malware alerts).
- **Entity** — fires on entity create/update. Use for entity-focused flows (any new external user → check threat intel).
- **Manual** — analyst-initiated. Use for destructive actions you don't want auto-running (isolate host, kill process).

---

## Q2. What are the four step types?

Integration Action (calls an action from a response integration), Function (built-in platform functions like Add Comment, Set Variable), Condition (branch on field value), Block (nested sub-playbook).

---

## Q3. How do you reuse logic across multiple playbooks?

**Blocks.** Extract the shared steps into a standalone playbook (a Block), then call it from each parent via a Block step whose `NestedWorkflowIdentifier` points at the block's `identifier`. When you fix a bug in the block, every parent inherits the fix.

---

## Q4. Explain the placeholder grammar.

`[step_id.JsonResult.key]` — access prior step's JSON output. `[Alert.severity]` — triggering alert's fields. `[Case.id]` — parent case. `[EntityIdentifier]` — current entity in entity-scoped steps. `[Variable.FOO]` — playbook variable set by a Set Variable function step.

---

## Q5. Why does a playbook widget need a `condition_group` guard?

Without it, placeholders like `[step_id.JsonResult.total]` render as literal text when the referenced step didn't run (because upstream failed, skipped, or hasn't reached it). The standard guard checks the placeholder doesn't contain the literal step name:

```yaml
condition_group:
  conditions:
    - field_name: "[my_step.JsonResult]"
      match_type: not_contains
      value: "my_step"
```

---

## Q6. What's the standard contribution path for a playbook?

1. `mp dev-env login` + `mp dev-env pull playbook <n>`
2. Fill `display_info.yaml` and `release_notes.yaml`
3. If reusing existing blocks, update step's `NestedWorkflowIdentifier` to point at them (don't duplicate)
4. Move to `content/playbooks/third_party/<community|partner>/`
5. `mp validate playbook <n>`
6. Open PR

---

## Q7. Can a playbook have more than one trigger?

No — exactly one `trigger.yaml` per playbook. For multiple trigger scenarios, create multiple playbooks that share the same Block for their common logic.

---

## Q8. What's the difference between `display_info.yaml` and `overviews.yaml`?

`display_info.yaml` feeds the catalog tile (name, author, short description, categories). `overviews.yaml` feeds the detail panel when users click the tile — long-form description, use case, prerequisites. Both ship with every playbook.

---

## Q9. A step references `[step_a.JsonResult.foo]` but the UI shows the literal text. Diagnose.

Either (a) `step_a` didn't run (upstream failure / wrong branch), (b) the JSON key `.foo` doesn't exist in the actual output, (c) step IDs were renamed after the reference was written. Check the playbook run history to see `step_a`'s status and the raw JSON output shape.

---

## Q10. How do you handle partial failures in a playbook?

Use `on_failure:` to route failing steps to a recovery step. For per-entity failures (action iterating entities where some succeed, some fail), the action itself aggregates into success/limit/failed/missing buckets — the playbook step still succeeds overall. Only bail out if the step's `on_failure` is defined or if the failure is catastrophic.

---

## Q11. Why don't playbooks have explicit `for` loops?

Because iteration happens at the **action level**: an action with `target_entities_scope: alert_entities` is called once per entity. If you truly need iteration over arbitrary lists outside of entity scope, the pattern is to extract the per-item logic into a Block and chain it via a Block-step loop, or (usually better) move the iteration inside action code.

---

## Q12. How do you prevent two playbooks from stepping on each other when they both trigger on the same alert?

Three options: (a) make trigger conditions mutually exclusive (e.g., one fires on `severity: High`, the other on `severity: Medium`); (b) rely on the platform's concurrent-execution support — they both run, and their actions operate on separate entity enrichment keys; (c) use a guard variable at the top of each playbook that checks a case tag and bails if the other has already run.

---

## Q13. What's `NestedWorkflowIdentifier` and why is it the main gotcha for contributors?

It's the parameter in a Block step that identifies *which* block playbook to invoke. When contributing a playbook that reuses an existing block, the contributor must update their step's `NestedWorkflowIdentifier.value` to the existing block's `identifier` from the repo, not the copy they exported from their dev SOAR. Forgetting to do this creates a duplicate block in the merge — a reviewer-caught mistake.

---

## Q14. Walk me through what happens from "alert created" to "playbook widget rendered in case overview".

1. Connector ingests alert → platform creates Alert.
2. Ontology mapping extracts entities.
3. Platform groups alert into Case.
4. Platform matches Case/Alert against all playbook triggers.
5. Every matching playbook fires — a Playbook Run is created per match.
6. The platform executes steps in order, respecting `on_success` / `on_failure`.
7. Action steps call integration action scripts; JSON results are stored with the step.
8. Case overview renders widgets. Each widget's YAML declares its `data_sources:` (step IDs). Widgets are rendered with placeholders resolved against step data.
9. Analyst sees the rendered case overview.

---

## Q15. Scenario: a playbook runs for 10 minutes every time — the SOC complains. How do you optimize?

1. **Profile** — which step(s) dominate runtime? Usually a slow integration action.
2. **Parallelize** — if steps are independent, route them as siblings from the same upstream.
3. **Cache** — if the slow step re-queries the same external API per entity, push caching into `core/` so repeated calls within a window reuse results.
4. **Pre-filter** — if `Enrich All IOCs` runs on every alert but many entities are internal and excluded anyway, short-circuit earlier with a condition step.
5. **Async** — rewrite the hot action using async HTTP if the underlying API supports parallelism.
6. **Simplify** — reduce the scope: not every alert needs a 12-step enrichment flow. Add a severity gate that skips expensive steps for Low severity.

Measure-then-optimize, not speculate-then-refactor.

---

## Next

→ **[Section 5: Parsers](../05-parsers/index.md)**
