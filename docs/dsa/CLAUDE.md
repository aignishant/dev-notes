# DSA Bible — project instructions

Standalone MkDocs Material site for DSA + system design interview prep. Built independently here AND wired into the root `dev-notes` nav at `/dev-notes/dsa/...`. Both builds must keep working — every change should be valid for both.

## UI conventions

Apply the umbrella project's UI conventions in full (see `../../CLAUDE.md`). In short: glassmorphism cards, 3D hover transforms, three.js hero on the welcome page, latest Material/Octicon/FontAwesome icons, advanced code visuals (annotations, tabbed languages, line highlights), interactive grid cards on every section landing page.

The user has explicitly asked for "most advanced and interactive mkdocs UI" — go rich. Their global "Simplicity First" rule does not apply to UI here.

## Assets

- `docs/stylesheets/extra.css` — base CSS variables, difficulty pills, company tags, grid-card 3D effects, glassmorphism, dark-mode overrides.
- `docs/javascripts/extra.js` — three.js hero mount, interactive helpers.
- `docs/javascripts/mathjax.js` — MathJax bootstrap (already wired).

## Required mkdocs.yml features / extensions

See `../../CLAUDE.md` for the canonical list. Keep parity between this site's `mkdocs.yml` and the root one's settings for the DSA pages so both renders look identical.

## Build

- `mkdocs build --strict` here builds the standalone site to `site/`.
- From the repo root, `mkdocs build --strict` builds the umbrella site (which includes DSA pages under `dsa/docs/...`).
