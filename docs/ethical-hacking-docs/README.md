# 🛡️ Ethical Hacking Mastery

A comprehensive ethical hacking & cybersecurity reference — from foundations to advanced offensive/defensive operations, oriented toward US & India government cybersecurity careers (NSA, CISA, FBI, USCYBERCOM, CERT-In, NCIIPC, NTRO, DRDO, etc.).

> ⚠️ **For legal, authorized testing and educational use only.** Read [Legal & Ethics](docs/00-getting-started/legal-ethics.md) before doing anything in this repository.

## What's Inside

Six phases, each building on the last:

1. **Foundations** — networking, OS internals, crypto, Python for security
2. **Recon** — OSINT, scanning, vulnerability assessment
3. **Offensive** — web app, system, AD, wireless, mobile pentesting
4. **Specializations** — cloud, malware analysis, RE, exploit dev, IoT, AI security
5. **Defense** — red, blue, purple team; DFIR; threat intel
6. **Career** — reporting, certifications, US + India agency pathways, CTFs

Plus ~40 production-quality Python tools you can read, run, and adapt.

## Quick Start

```bash
# Clone
git clone <repo-url> ethical-hacking-mastery
cd ethical-hacking-mastery

# Install docs deps and serve locally
python -m venv .venv
source .venv/bin/activate          # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
mkdocs serve

# Open http://127.0.0.1:8000
```

To install tool dependencies for the Python scripts:

```bash
pip install -r requirements-tools.txt
```

## Delivery Status

This curriculum is being built in stages. Each stage adds complete chapters and Python tools.

| Stage | Phase coverage | Scripts | Status |
|---|---|---|---|
| **Stage 1** | Getting Started · Phase 1 (Foundations) | 9 scripts | ✅ Delivered |
| **Stage 2** | Phase 2 (Recon) · Phase 3 — web AppSec foundations | 11 scripts | ✅ Delivered |
| Stage 3 | Phase 3 rest (Auth, Linux/Windows, AD, wireless, mobile, pivoting) · Phase 4 part 1 | +10 scripts | Planned |
| Stage 4 | Phase 4 rest (RE, exploit dev, IoT, AI sec) · Phase 5 (Red/Blue/DFIR/TI/Purple) | +10 scripts | Planned |
| Stage 5 | Phase 6 (Reporting, Certifications, Government Career US+India, CTFs) · Final polish | — | Planned |

See [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) for the full roadmap.

## Repository Layout

```
ethical-hacking-docs/
├── docs/                  # MkDocs source
│   ├── 00-getting-started/
│   ├── 01-foundations/
│   ├── 02-recon/
│   ├── 03-offensive/
│   ├── 04-specializations/
│   ├── 05-defense/
│   ├── 06-career/
│   ├── 99-appendix/
│   └── assets/
├── scripts/               # Python tools, organized by category
│   ├── recon/
│   ├── scanning/
│   ├── web/
│   ├── crypto/
│   ├── forensics/
│   ├── malware-analysis/
│   ├── automation/
│   └── defense/
├── mkdocs.yml
├── requirements.txt       # docs build
├── requirements-tools.txt # security tool deps
└── IMPLEMENTATION_PLAN.md
```

## Build & Deploy

```bash
mkdocs build         # static site → ./site/
mkdocs gh-deploy     # publish to GitHub Pages
```

A GitHub Actions workflow at `.github/workflows/docs.yml` will auto-deploy on every push to `main`.

## License & Disclaimer

Educational content licensed for personal study. The Python tools are released under MIT for legitimate research and authorized testing **only**. Use against systems you don't own or have written permission to test is illegal in most jurisdictions, including the United States (CFAA) and India (IT Act 2000 §66).

The author and contributors are not responsible for misuse.
