# Content Hub — Interview Prep (Lead Developer, 5 Years)

> **Goal:** Walk into any interview on the Google SecOps Content Hub project and answer **every single question** — from "what is a connector?" to "design a multi-tenant ingestion pipeline" — with confidence and authority.

---

## How This Site is Organised

This is **not** a generic Python interview kit. Every section is **scoped to the Content Hub codebase** you led for 5 years. Each section goes:

1. **Concept explanation** — what it is, why it exists, how it fits
2. **Code walkthrough** — real snippets from the repo (TIPCommon `Action`, `Connector`, `Job` base classes, ontology YAML, `mp` commands)
3. **Interview Questions (tiered)** — Beginner → Intermediate → Senior → Lead/Architect
4. **Model Answers** — STAR-format or technical deep-dive

---

## Suggested Study Paths

=== "You have 1 week"
    - **Day 1-2** — Sections 1, 2, 3 (foundations + integrations)
    - **Day 3** — Section 4 (Playbooks) + Section 5 (Parsers)
    - **Day 4** — Section 6 (TIPCommon / SDK) + Section 7 (mp CLI)
    - **Day 5** — Sections 8, 9 (dev workflow + testing)
    - **Day 6** — Sections 10, 11 (CI/CD + advanced)
    - **Day 7** — Sections 12, 13, 14 (system design + leadership + scenarios)

=== "You have 3 days"
    - **Day 1** — Sections 1–3 deeply, skim 4–5
    - **Day 2** — Sections 6–9
    - **Day 3** — Sections 11–14 + Section 15 cheat sheet

=== "You have 24 hours"
    - Go straight to **[Cheat Sheet](15-quick-reference/cheat-sheet.md)**
    - Then **[Section 3 Q&A](03-response-integrations/questions.md)**, **[Section 12 Q&A](12-system-design/questions.md)**, **[Section 13 behavioral](13-leadership/behavioral-questions.md)**
    - Skim **[Red Flag Answers](15-quick-reference/red-flags.md)**

---

## The 15 Sections at a Glance

| # | Section | Covers | Level |
|---|---------|--------|-------|
| 1 | [Foundations](01-foundations/index.md) | What is SecOps, what is Content Hub, repo structure | Beginner |
| 2 | [Core Concepts](02-core-concepts/index.md) | Integrations, playbooks, parsers, entities, ontology | Beginner → Mid |
| 3 | [Response Integrations](03-response-integrations/index.md) | Actions, connectors, jobs, widgets, definition.yaml | Mid |
| 4 | [Playbooks](04-playbooks/index.md) | Triggers, steps, blocks, widgets | Mid |
| 5 | [Parsers](05-parsers/index.md) | CBN syntax, UDM, testdata | Mid |
| 6 | [TIPCommon & SDK](06-tipcommon-sdk/index.md) | Base classes, extraction, validation | Senior |
| 7 | [mp CLI](07-mp-cli/index.md) | build, validate, test, dev-env | Mid → Senior |
| 8 | [Dev Workflow](08-dev-workflow/index.md) | uv, ruff, ty, pydantic, type hints | Mid |
| 9 | [Testing](09-testing/index.md) | integration_testing, fixtures, mocks | Senior |
| 10 | [CI/CD](10-cicd/index.md) | GitHub Actions, PR flow, status checks | Senior |
| 11 | [Advanced](11-advanced/index.md) | OAuth, caching, async, encryption, rate limiting | Senior → Lead |
| 12 | [System Design](12-system-design/index.md) | Scaling, multi-tenant, migration | Lead |
| 13 | [Leadership](13-leadership/index.md) | Behavioral, mentoring, incidents, STAR | Lead |
| 14 | [Scenarios](14-scenarios/index.md) | Live coding, debugging, whiteboards | All |
| 15 | [Quick Reference](15-quick-reference/cheat-sheet.md) | Cheat sheet, glossary, red flags | All |

---

## How to Answer Any Question (The 4-Layer Framework)

!!! tip "Structure every answer like this"
    1. **Define** — one sentence: *"A connector is a Python script that runs like a cron job to ingest alerts from third-party products into Google SecOps."*
    2. **Locate** — where does it live? *"They live under `content/response_integrations/<repo>/<integration>/connectors/`"*
    3. **Differentiate** — contrast with its siblings: *"Unlike an action, a connector runs continuously; unlike a job, it creates new alerts rather than syncing state."*
    4. **Experience** — prove you've done it: *"I led the team that migrated our 40+ community connectors from the legacy v1.x TIPCommon to the 2.x base-class pattern..."*

Do those four layers in every answer and you will sound senior no matter the difficulty of the question.

---

## Prerequisites

You already know:

- Python 3.11, type hints, `dataclass`/`pydantic`
- Git + GitHub PR workflow
- YAML syntax
- HTTP, REST APIs, OAuth 2.0 basics

If any of those are rusty, review them before opening Section 6.

---

## Let's Go

Start here → **[Section 1: Foundations](01-foundations/index.md)**

Or if you're short on time → **[Cheat Sheet](15-quick-reference/cheat-sheet.md)**
