# Content Hub Interview Prep — MkDocs Site

A comprehensive interview-preparation site for the Google SecOps Content Hub project, tailored for a lead developer with 5 years of experience.

## What's Inside

**96 markdown pages across 15 sections**, roughly 200,000 words of interview-ready content covering:

1. **Foundations** — Google SecOps, Content Hub overview, repo structure
2. **Core Concepts** — Integrations, Playbooks, Parsers, Entities, Ontology, Cases/Alerts/Events
3. **Response Integrations** — Actions, Connectors, Jobs, Widgets, `definition.yaml` deep dive
4. **Playbooks** — Triggers, Steps, Blocks, Widgets, Overviews
5. **Parsers** — CBN, UDM, test data, validation pipeline
6. **TIPCommon & SOAR SDK** — Base classes (Template Method), extraction/validation, EnvironmentCommon
7. **`mp` CLI** — build, validate, test, check, format, dev-env, describe
8. **Dev Workflow** — uv, ruff, ty, Pydantic, type hints, IDE setup
9. **Testing** — pytest, `integration_testing` package, mocking, fixtures
10. **CI/CD** — GitHub Actions, PR workflow, validation checks
11. **Advanced** — OAuth, caching, encryption, async connectors, sync jobs, error handling, rate limiting
12. **System Design** — scaling connectors, new integrations, multi-tenant, migration
13. **Leadership & Behavioral** — team processes, code review, mentoring, incidents, STAR stories, 30+ behavioral Qs
14. **Scenarios** — live-coding actions/connectors, debug, migrate legacy, whiteboard
15. **Quick Reference** — cheat sheet, glossary, red-flag answers, day-before checklist

Every section ends with **interview Q&A** graded Beginner → Lead.

## How to Use

### Option 1 — Run the MkDocs site locally (recommended)

Requirements: Python 3.11+, pip.

```bash
# Install dependencies
pip install mkdocs mkdocs-material pymdown-extensions

# Serve locally with live-reload
cd interview-prep
mkdocs serve

# Open http://127.0.0.1:8000 in your browser
```

You'll get a full searchable documentation site with dark mode, navigation tabs, mermaid diagrams, and code highlighting.

### Option 2 — Browse the pre-built static site

The `site/` directory contains the pre-built HTML. Open `site/index.html` in a browser directly, OR serve with any static file server:

```bash
cd interview-prep/site
python -m http.server 8000
# Open http://127.0.0.1:8000
```

### Option 3 — Read markdown files directly

All content is under `docs/`. Open any `.md` file in your editor or a markdown viewer. Start with `docs/index.md`.

## Recommended Study Paths

**1 week before interview:**
- Day 1-2: Sections 1-3 (foundations + integrations)
- Day 3: Sections 4-5 (playbooks + parsers)
- Day 4: Sections 6-7 (TIPCommon + mp CLI)
- Day 5: Sections 8-9 (workflow + testing)
- Day 6: Sections 10-11 (CI/CD + advanced)
- Day 7: Sections 12-14 (system design + leadership + scenarios)

**3 days before:**
- Day 1: Sections 1-5 (skim)
- Day 2: Sections 6-11 (focus on 6, 11)
- Day 3: Sections 12-15

**24 hours before:**
- `docs/15-quick-reference/cheat-sheet.md`
- `docs/15-quick-reference/day-before.md`
- `docs/13-leadership/behavioral-questions.md`

## Customization

- Replace STAR story specifics in `docs/13-leadership/star-stories.md` with your real history.
- Fork and edit freely — everything is plain markdown.

## Credits

Content based entirely on the real `content-hub` repo structure, TIPCommon library source, the `mp` CLI, and the official documentation shipped with the project.

Good luck with the interview. You've got this. 🍀
