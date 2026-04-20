# Section 3 — Response Integrations Deep Dive

Now we're in the technical core. This section owns the codebase you worked in daily. Expect the **majority of your interview time** on these topics.

## What you'll learn

- Full folder anatomy of a production-grade integration
- Action, Connector, and Job patterns — including TIPCommon 2.x base classes
- `definition.yaml` schema and what every field controls
- Widget definition (HTML + YAML + `{stepInstanceName}.JsonResult` binding)
- Idioms for API clients, error handling, auth

## Pages

1. **[Integration Structure](structure.md)** — folder-by-folder anatomy
2. **[Actions Deep Dive](actions.md)** — legacy vs modern, lifecycle, inputs/outputs
3. **[Connectors Deep Dive](connectors.md)** — alert building, overflow handling, last-run timestamps
4. **[Jobs Deep Dive](jobs.md)** — sync patterns, `_get_job_last_success_time`, idempotency
5. **[Widgets](widgets.md)** — predefined widget YAML + HTML binding
6. **[definition.yaml Explained](definition-yaml.md)** — field by field
7. **[Interview Q&A](questions.md)** — 25+ questions

!!! tip "Guaranteed interview prompt"
    *"Walk me through writing a new integration from scratch for a third-party threat intelligence product."* Your answer should touch every page in this section.
