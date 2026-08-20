
# dev-notes — project instructions

This is a multi-section MkDocs Material knowledge base. The root `mkdocs.yml` builds the umbrella site at `/dev-notes/`. Sub-projects (e.g. `docs/dsa/`) keep their own `mkdocs.yml` so they can be built standalone, but their pages are also wired into the root nav.

## UI conventions (root + all sub-sites)

Apply these to both the root and every sub-site (`docs/dsa/` etc.) — the user has asked for the most advanced/interactive mkdocs UI.

- **Theme**: Material; light scheme `default`/indigo, dark scheme `slate`/indigo. Auto-toggle via `prefers-color-scheme`.
- **Features**: enable `navigation.instant{,.prefetch,.progress}`, `navigation.tracking`, `navigation.tabs{,.sticky}`, `navigation.path`, `navigation.indexes`, `navigation.top`, `navigation.footer`, `toc.follow`, `search.{suggest,highlight,share}`, `content.code.{copy,annotate,select}`, `content.tabs.link`, `content.tooltips`, `header.autohide`, `announce.dismiss`.
- **Markdown extensions**: `pymdownx.superfences` (with `mermaid` custom fence), `pymdownx.tabbed` (`alternate_style: true`), `pymdownx.tasklist` (`custom_checkbox: true`), `pymdownx.details`, `pymdownx.highlight` (`anchor_linenums`, `line_spans`), `pymdownx.inlinehilite`, `pymdownx.snippets`, `pymdownx.arithmatex` (`generic: true`), `pymdownx.keys`, `pymdownx.mark`, `pymdownx.caret`, `pymdownx.tilde`, `pymdownx.betterem`, `pymdownx.smartsymbols`, `pymdownx.emoji` (twemoji + to_svg), plus core `admonition`, `attr_list`, `def_list`, `footnotes`, `md_in_html`, `tables`, `toc` (`permalink: true`).
- **Assets**: every site has `docs/stylesheets/extra.css` (3D cards, glassmorphism, gradients, custom scrollbar, dark-mode overrides) and `docs/javascripts/extra.js` (three.js hero mount, smooth interactions). three.js is loaded from CDN only when needed.
- **Landing pages**: prefer Material grid cards (`<div class="grid cards" markdown>` with `:material-…:` icons) over plain bullet lists.
- **Code**: use code annotations, tabbed language variants, line highlighting where appropriate.
- **Icons**: Material, Octicons, FontAwesome — all available via `pymdownx.emoji` configured for twemoji.

## Build commands

- `mkdocs build --strict` from repo root — builds the umbrella site.
- `cd docs/dsa && mkdocs build --strict` — builds the standalone DSA site (kept working in parallel).
- `mkdocs serve` from repo root — live-reload dev server at `http://127.0.0.1:8000/dev-notes/`.

## Karpathy "simplicity" exception

The user's global CLAUDE.md emphasises "Simplicity First / Surgical Changes". For UI work on these mkdocs sites the user has explicitly requested the opposite — go rich. Don't strip features in the name of simplicity here.
