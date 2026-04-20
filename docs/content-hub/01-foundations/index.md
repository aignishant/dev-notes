# Section 1 — Foundations

Before we touch code, we need a rock-solid mental model of the platform this project plugs into. Interviewers at any level will probe whether you actually understand **what problem the Content Hub exists to solve**, not just the file layout.

## What you'll learn

- What Google SecOps is and how SIEM + SOAR fit together
- What the Content Hub repo is, who uses it, and how content reaches customers
- The top-level repo layout and the "why" behind each directory
- The mental model of Content → Platform flow

## Pages

1. **[Google SecOps Overview](google-secops-overview.md)** — SIEM + SOAR, cases, alerts, events
2. **[What is the Content Hub?](what-is-content-hub.md)** — Its purpose, audience, lifecycle
3. **[Repository Structure](repo-structure.md)** — `content/`, `packages/`, `tools/`, `docs/`
4. **[Beginner Interview Q&A](questions.md)** — 20+ questions with model answers

!!! tip "Interview insight"
    Interviewers love when candidates can explain **why** the repo is structured this way. "Because content is versioned separately from platform code, the SOAR product can update independently and customers can pull fresh integrations without a platform upgrade" is the kind of sentence that makes a senior interviewer lean in.
