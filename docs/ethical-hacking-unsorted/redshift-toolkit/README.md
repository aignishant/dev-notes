# redshift-toolkit

Personal offensive security Python toolkit accompanying the **Redshift** ethical hacking curriculum.

Grows module-by-module across Parts 1–16. By the time Part 16 ships, this will be 15+ sub-packages with ~300 scripts.

## Install

```bash
# From the repo root
cd redshift-toolkit
pip install -e .

# With extras
pip install -e ".[net,crypto]"
pip install -e ".[all]"

# Dev tools (formatter, type-checker, tests)
pip install -e ".[dev]"
```

## First three modules (Part 1)

- `redshift_toolkit.utils.encoder_decoder` — base64/32/16, hex, URL, ROT, gzip, XOR codec Swiss army knife.
- `redshift_toolkit.utils.cheatsheet_cli` — searchable command cheat-sheet stored in `~/.redshift/cheats.yaml`.
- `redshift_toolkit.utils.notes_cli` — engagement notebook; per-engagement markdown appended with timestamps.

Three shell entry points are installed with the package:

```bash
rs-encode b64 encode "admin:password"
rs-cheats search "kerberoast"
rs-notes new "Acme-Q2-2026"
```

## Layout

```
redshift_toolkit/
├── recon/         (filled in Part 3)
├── scan/          (filled in Part 3)
├── web/           (filled in Part 4)
├── net/           (filled in Parts 2, 5)
├── payload/       (filled in Part 6)
├── creds/         (filled in Part 7)
├── ad/            (filled in Part 7)
├── postex/        (filled in Part 7)
├── cloud/         (filled in Part 9)
├── mobile/        (filled in Part 10)
├── ics/           (filled in Part 10)
├── c2/            (filled in Part 11)
├── evasion/       (filled in Parts 11–12)
├── forensics/     (filled in Parts 13–14)
├── automation/    (filled in Parts 13–16)
└── utils/         (started in Part 1)
```

## Ethics

Everything here is for **authorized** testing, lab practice, and detection engineering. See `../docs/part-01-foundations/02-legal.md`.
