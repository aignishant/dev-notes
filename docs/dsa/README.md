# 📘 DSA & System Design Bible

A self-contained, beginner-friendly bible for cracking interviews at:

- **Product companies** — Google, Meta, Amazon, Microsoft, Adobe, Apple, Netflix, Uber, Flipkart…
- **Indian service companies** — TCS, Infosys, Wipro, HCL, Cognizant…
- **Indian PSUs / government** — ISRO, DRDO, BARC…

When this bible is finished, you should not need any other book, course, or YouTube video.

Built with [MkDocs](https://www.mkdocs.org/) + the [Material theme](https://squidfunk.github.io/mkdocs-material/).

---

## What's inside (when complete)

- ~355 pages of content
- 5,000+ problems, each with progressive line-by-line Python solutions
- 25+ system-design deep-dives (cloud + on-prem + architecture)
- 15+ company-specific question banks
- 6 study plans (3w / 5w / 6w / 1mo / 3mo / 6mo)

The full spec is in [`IMPLEMENTATION_PLAN_v3.md`](IMPLEMENTATION_PLAN_v3.md). The bible is being built phase by phase.

---

## How to run the site locally

You only need to do this once.

### 1. Install Python 3.10 or newer

Check your version:

```bash
python3 --version
```

If you don't have it: install from [python.org](https://www.python.org/downloads/) or your system package manager.

### 2. Install the dependencies

The simplest path (matches the way mkdocs is already installed on this machine):

```bash
pip install --user --break-system-packages -r requirements.txt
```

If you prefer a clean virtualenv (recommended for serious development):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Serve the site

From this folder:

```bash
mkdocs serve
```

Then open <http://127.0.0.1:8000> in your browser. The page auto-reloads when you save a markdown file.

If port 8000 is busy:

```bash
mkdocs serve -a 127.0.0.1:8001
```

### 4. Build a static site (optional)

```bash
mkdocs build
```

The static site lands in `site/`. Open `site/index.html` directly, or deploy that folder anywhere (GitHub Pages, Netlify, S3+CloudFront…).

---

## Folder layout

```
.
├── IMPLEMENTATION_PLAN_v3.md     # The spec (the contract for what gets built)
├── CLAUDE_CODE_HANDOFF.md        # Phase 1 brief
├── mkdocs.yml                    # MkDocs configuration + nav
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── .gitignore
└── docs/
    ├── index.md                  # Welcome page
    ├── stylesheets/extra.css     # Custom polish
    ├── javascripts/mathjax.js    # Math support
    ├── 00-roadmap/               # Study plans + how-to-use guides
    ├── 01-foundations/           # Python + complexity basics
    ├── 02-data-structures/       # Arrays, strings, lists, trees, graphs…
    ├── 03-algorithms/            # Sort, search, recursion, DP, graph algos…
    ├── 04-patterns/              # The 20 interview patterns
    ├── 05-advanced/              # Tries, segment trees, union-find…
    ├── 06-ultra-advanced/        # Heavy hitters: persistent DS, online algos…
    ├── 07-popular-problems/      # Curated lists + per-company question banks
    ├── 08-system-design/         # 25+ system design projects
    ├── 09-low-level-design/      # OOP design patterns + LLD problems
    ├── 10-mock-interviews/       # Full mock interview transcripts
    ├── 11-behavioral/            # Behavioral / STAR / leadership rounds
    ├── 12-common-across-all-companies/  # Most-asked across all companies
    └── 13-resources/             # Cheatsheets, references, further reading
```

---

## Build status (phase tracker)

| Phase | What it covers | Status |
|---|---|---|
| 1 | Skeleton + Foundations + sample chapter | 🚧 In progress |
| 2 | Core data structures (arrays, strings, linked lists, stacks, queues, hash tables) | ⏳ Pending |
| 3 | Trees, heaps, graphs, advanced DS | ⏳ Pending |
| 4 | Algorithms (sort, search, recursion, DP, greedy, graph, string) | ⏳ Pending |
| 5 | All 20 patterns | ⏳ Pending |
| 6 | Advanced + ultra-advanced topics | ⏳ Pending |
| 7 | Top-100-by-Pattern + curated lists | ⏳ Pending |
| 8 | Product company pages (22) | ⏳ Pending |
| 9 | Service company pages (17) | ⏳ Pending |
| 10 | Indian PSU pages (21) | ⏳ Pending |
| 11 | System design fundamentals + Tier-1 (5 core projects) | ⏳ Pending |
| 12 | System design Tier-2 (20 important projects) | ⏳ Pending |
| 13 | System design Tier-3 (5 bonus) + LLD | ⏳ Pending |
| 14 | Mock interviews + behavioral + common-across + resources + final polish | ⏳ Pending |

---

## License

Personal study material. No license granted for redistribution.
