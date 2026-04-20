# Section 4 — Playbooks Deep Dive

Playbooks are the orchestration layer — where Actions from integrations become automated incident response. You'll be tested on trigger grammar, step composition, block reuse, and the contribution workflow.

## What you'll learn

- Full playbook folder structure and every YAML file's role
- Trigger types, conditions, and grammar
- Step types: Actions, Functions, Conditions, Blocks
- Playbook-level widgets
- Overview metadata and catalog surfacing
- Contribution paths (`mp` tool vs manual)

## Pages

1. **[Playbook Structure](structure.md)** — file layout
2. **[Triggers](triggers.md)** — Alert, Entity, Manual
3. **[Steps & Blocks](steps.md)** — the four step types + block reuse
4. **[Widgets](widgets.md)** — case overview widgets
5. **[Overviews](overviews.md)** — catalog-facing metadata
6. **[Interview Q&A](questions.md)**

!!! tip "Where playbook questions get tricky"
    Interviewers love asking **"how would you refactor three near-duplicate playbooks"** — the answer is always *Blocks*, but you need to articulate the `NestedWorkflowIdentifier` pattern to sound like you've done it.
