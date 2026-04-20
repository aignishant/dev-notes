# Migration Strategy

## The Scenario

> *"We have 40+ community integrations on TIPCommon 1.x (procedural `@output_handler` style). Migrate to TIPCommon 2.x (class-based base)."*

This is a canonical lead-level prompt. Here's how to structure the answer.

## Phase 0 — Stop the Bleeding

**Before** you migrate anything, prevent new technical debt:

- `mp validate` rejects new integrations pinning TIPCommon 1.x
- `mp validate` warns on modifications to legacy-style actions without migration
- Update contribution docs — new work must use 2.x base classes

Without this, you're migrating faster than new legacy code is being written. Unwinnable.

## Phase 1 — Inventory & Prioritization

Build a spreadsheet:

| Integration | TIPCommon version | Last changed | # Actions | # Connectors | Customer usage (high/med/low) | Team owner | Priority |
|---|---|---|---|---|---|---|---|
| abuse_ipdb | 1.1.2 | 2024-03 | 2 | 0 | High | Community | P1 |
| ... | ... | ... | ... | ... | ... | ... | ... |

Priority matrix:

- **P1** — high customer usage + recent changes (touched often → migrate first)
- **P2** — high customer usage + stable (less churn risk, still important)
- **P3** — low customer usage + stable (might deprecate instead)
- **P4** — abandoned / broken (consider removal)

## Phase 2 — Compatibility Shim

Before touching integrations, ensure **TIPCommon 2.x's base classes expose all the behaviors** 1.x integrations relied on. Gaps:

- If 1.x's `extract_configuration_param` returns `False` on missing boolean but 2.x raises → fix 2.x
- If 1.x gives direct access to `siemplify.target_entities` and 2.x's base abstracts it → add a compat property

This is a **TIPCommon PR first**, integrations after. Don't start migrating integrations until the shim is production-stable.

## Phase 3 — Migration Kit

Write automation that transforms common 1.x patterns to 2.x skeleton:

```python
# Pseudocode for the migrator

def migrate_action(legacy_py: Path) -> str:
    """Transform a legacy `@output_handler main()` into a class-based stub."""
    tree = parse(legacy_py.read_text())
    main_func = find_function(tree, "main")

    # Extract patterns:
    param_extractions = find_calls(main_func, "extract_configuration_param")
    param_extractions += find_calls(main_func, "extract_action_param")

    # Generate new file shape
    return render_template(
        class_name=...,
        script_name=...,
        extract_params_body=convert_to_params_container(param_extractions),
        validate_params_body="pass",   # human to fill
        init_client_body=...,
        perform_action_body="# TODO: port business logic",
    )
```

The migrator:
- Generates the 2.x class skeleton
- Moves parameter extractions into `_extract_action_parameters`
- Preserves the API client instantiation in `_init_api_clients`
- Leaves the core business logic as a TODO for a human to move into `_perform_action`

Doesn't try to auto-migrate business logic — that's where bugs hide.

## Phase 4 — Pilot Wave

Migrate **3 integrations yourself** end-to-end:

1. Pick one low-risk (few actions, no connector)
2. One medium (several actions)
3. One complex (connector + jobs)

For each:

- Use the migrator to generate scaffold
- Move business logic manually
- Write tests (if missing)
- Deploy to staging tenant, burn 24 hours
- Document every pitfall you hit

The pilot produces a **migration runbook** that the rest of the team will follow.

## Phase 5 — Waves of 5

Team executes the runbook in batches:

- Week 1: 5 integrations migrated → PRs → review → merge
- Week 2: next 5
- ...

Each PR:
- Scoped to one integration
- Tests added/updated
- Deployed to staging, burned 24 hours before production promotion

Keep waves small — lets you catch issues early rather than discovering a systemic bug after 20 integrations.

## Phase 6 — Regression Harness

Before cutting over, run **behavioral regression** tests:

- For each migrated integration, replay the same mock third-party fixtures against the old and new versions
- Diff the `AlertInfo` output / entity enrichment output
- Any non-trivial diff is a migration bug

```python
def test_migration_preserves_behavior(mock_product):
    old_result = OldConnector_v1_1_2().run_against(mock_product)
    new_result = NewConnector_v2_0_6().run_against(mock_product)
    assert deep_equal(old_result, new_result, ignore_fields=["timestamp"])
```

## Phase 7 — Feature-Flagged Rollout

Ship each migrated version alongside the old one for one release cycle:

- Old: `abuse_ipdb` v2.1.3 (legacy) — still available
- New: `abuse_ipdb` v3.0.0 (modernized) — marked as preferred

Customers opt in. Telemetry shows adoption and any issues. After a cycle with no issues, deprecate v2.x.

```yaml
# release_notes.yaml
- description: Modernized to TIPCommon 2.x base classes. No behavior change.
  integration_version: 3.0.0
  item_name: AbuseIPDB
  item_type: Integration
  regressive: false    # we preserved behavior
  publish_time: '2026-03-15'
```

## Phase 8 — Cleanup

- Deprecate 1.x in the hub catalog
- Remove 1.x wheels from `packages/tipcommon/whls/` **only after all deployed customers have migrated** — check telemetry
- Update `mp validate` to reject 1.x pinning in any new integration
- Close the migration epic

## Timeline — A Realistic Estimate

- Phase 0-1: 1 week
- Phase 2-3: 2 weeks
- Phase 4: 1 week
- Phase 5: 40 integrations / 5 per week = **8 weeks**
- Phase 6-7: 2 weeks overlapping
- Phase 8: 1 week

**Total: ~14 weeks** (3.5 months) with a team of 2-3 engineers.

Be honest about this in interview — pretending you'd do it in 2 weeks is a red flag.

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| Customer's live integration breaks | Parallel-deploy old+new; customers opt in |
| Migration kit produces broken code | Pilot with 3 integrations first; refine kit |
| Behavioral regression slips past review | Mandatory regression harness in CI |
| Team burnout from mechanical work | Keep waves small, rotate owners |
| Discovery of undocumented 1.x behaviors | Document as you find them; add to compat shim |

## Interview Tip

This question is really asking **"can you lead complex technical migrations?"**. The answer isn't the specific phases — it's the structured thinking:

- **Stop the bleeding first**
- **Inventory → prioritize**
- **De-risk with a pilot**
- **Parallel deploy; don't cut over**
- **Regression harness, not faith**
- **Realistic timeline**
- **Document relentlessly**

Anyone can name TIPCommon base classes; few articulate this sequence.

## Next

→ **[Interview Q&A](questions.md)**
