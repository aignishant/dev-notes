# Section 5 — Parsers

Parsers are the SIEM-side component of the Content Hub. You're unlikely to be grilled on CBN syntax as an integration lead, but you **will** be asked about the end-to-end parser contribution pipeline, UDM, and how parsers relate to connectors.

## What you'll learn

- What CBN and UDM are, at a practical level
- Parser folder structure and required files
- The two-stage validation pipeline (standalone + live instance)
- Test data conventions and the 1,000-log requirement
- How parsers compare with connector-based ingestion

## Pages

1. **[CBN & UDM](cbn-udm.md)**
2. **[Parser Folder Structure](structure.md)**
3. **[Test Data & Validation](testdata.md)**
4. **[Interview Q&A](questions.md)**

!!! tip "Honest scoping wins"
    If you didn't personally write parsers, say so explicitly. *"My work focused on the SOAR side — I reviewed parser PRs and understand the validation pipeline end-to-end, but CBN authoring was owned by our SIEM parser specialists."* This positions you as a lead who knows their boundaries.
