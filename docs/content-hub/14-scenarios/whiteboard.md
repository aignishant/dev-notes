# Whiteboard Problems

Open-ended design prompts. No single right answer. What's being graded: your ability to **structure the unknown**, name tradeoffs, propose a concrete path, and stay honest about what you don't know.

## Prompt 1 — "Design a system that ingests 1M alerts/day"

### Structure your answer

1. **Clarify requirements** — 1M/day = ~12/sec average, bursts 10-100x — *is this real-time needed?*
2. **Right ingestion path** — Feed + Parser, not a connector. Parser scales; connectors don't.
3. **Throughput budget** — 100 alerts/sec sustained, 1000/sec peak; size the parser accordingly
4. **Separation** — ingestion layer (parser) decoupled from enrichment (integrations)
5. **Back-pressure** — if enrichment is slower than ingestion, buffer OR throttle; don't drop alerts
6. **Observability** — metric per layer (ingest rate, parse success rate, enrichment backlog)
7. **Isolation** — one noisy customer can't DoS another; per-tenant quotas

Don't pretend to know SOAR internals you don't. Say: *"I'd need to understand the platform's ingestion pipeline limits to design this concretely — what's the per-tenant throughput ceiling the platform supports?"*

## Prompt 2 — "A customer has 50 integrations; how do you manage dependency versions?"

- **Per-integration pinning** — each integration's `pyproject.toml` + `uv.lock` owns its deps
- **Shared libs via local wheels** — TIPCommon/EnvironmentCommon kept in `packages/` with multiple versions
- **Version matrix testing** — CI runs each integration against its pinned TIPCommon
- **Deprecation cadence** — wheel retention policy; no wheel removed while any customer is pinned on it
- **Centralized security patches** — critical CVE in a shared lib requires bumping all dependent integrations; tracked in a matrix
- **Tooling** — `mp validate` checks for deprecated or unsupported pinnings

Add tradeoffs aloud: *"Per-integration pinning isolates blast radius but multiplies the CI matrix. We accept the CI cost for the isolation win."*

## Prompt 3 — "Design an approval workflow for community integrations"

- **Automated gate** — `mp validate`, lint, type check, tests, CLA signed (all required)
- **Human gate** — 2 reviewers: domain reviewer (content team) + security reviewer (especially for auth or network-facing code)
- **Partner integrations** — additional vendor-side review required
- **Labels** — `security-review-needed`, `partner-approval-pending` as PR labels to route
- **Reviewer rotation** — to prevent single-person bottleneck
- **Escalation** — if any reviewer requests changes but author disagrees, third reviewer breaks the tie
- **SLA** — initial review within 1 business day; full cycle within 3 business days
- **Publishing** — automatic after merge via internal pipeline

## Prompt 4 — "Build a playbook framework from scratch"

Less concrete than the others — they want to see your analysis.

- **Mental model:** DAG of steps with branching on step output. Trigger defines entry conditions. Steps are typed: action, function, condition, block.
- **Core concepts:** trigger definition, step types, data flow (placeholder grammar), error paths.
- **Storage:** YAML for definitions, platform-native for runtime state.
- **Execution engine:** reads the DAG, executes steps in order respecting conditional branches, stores step outputs for later reference, handles timeouts per step and per playbook.
- **Extension points:** new step types, new placeholder expressions, new trigger types.

Stop. Don't try to design every detail. Say: *"I'd start with the 4 core step types; every other feature can be composed from those. Extension points I'd add last once the core is proven."*

## Prompt 5 — "Integration X is slow in production. Tell me how to debug."

Covered in detail in [Debug a Failing Connector](debug-connector.md). Key moves:

- Gather facts before hypothesizing
- Name hypotheses upfront
- Evidence-driven narrowing
- Containment before full fix
- Post-mortem action items

## Prompt 6 — "Tenant has 100 integrations using VirusTotal; quota exhausted"

- **Short-term:** identify the heaviest integrations (usage telemetry), throttle their VT calls at the integration layer
- **Medium-term:** introduce a shared cache in a power-up enrichment module
- **Long-term:** central VirusTotal proxy integration — all integrations call the proxy; proxy dedupes, caches, manages quota across tenant

Explain the progression: *"I'd take a staged approach rather than jumping to the architectural answer — immediate relief first, systemic fix after."*

## Prompt 7 — "Design a testing framework for integrations"

Covered in Section 9. Key features:

- Mock SOAR platform (`integration_testing` package)
- Mock third-party product server
- Mock HTTP session
- pytest fixtures for common entities/configs
- Idempotency test harness for connectors
- Behavioral regression harness (replay against fixtures, diff output)

## Prompt 8 — "How would you onboard 10 new community contributors?"

- **Documentation** — clear contribution guide, with tier-by-tier difficulty
- **Starter tickets** — label a pool of small, well-defined issues as "good-first-issue"
- **Onboarding session** — monthly open office-hours for new contributors
- **Mentorship pairing** — match each new contributor with an existing reviewer
- **Feedback loop** — track time-to-first-PR, time-to-merged-PR, contributor retention metrics
- **Community channel** — Discord/Slack where contributors can ask questions publicly

Frame as: *"The goal isn't 10 PRs — it's 10 contributors who stick around. Measure retention, not volume."*

## Prompt 9 — "What would you change about the Content Hub architecture if you could?"

Sincere, thoughtful answer. Avoid "nothing, it's great."

Examples:

- *"I'd push harder on Feed + Parser over connector ingestion — we've accumulated some connector-based flows that should have been parsers."*
- *"The SDK vs TIPCommon boundary has drifted — some logic is in both. I'd want to publish the SDK independently so TIPCommon can declare its SDK version range, like any library relationship."*
- *"The `power_ups/` pattern is great but underutilized — more integrations should be composing existing power-ups rather than writing their own utility code."*

Shows reflection and judgment.

## General Whiteboard Strategy

1. **Clarify** — never start sketching until requirements are bounded
2. **Outline aloud** — name the 3-5 parts before drawing any
3. **Pick one slice to detail** — can't fit everything; show deep on one part
4. **Name tradeoffs explicitly** — "we're choosing X at the cost of Y"
5. **Surface what you don't know** — "I'd need to know Z before I can design this specifically"
6. **Close with follow-up questions** — "What else should I consider?"

Whiteboard interviews grade your judgment more than your knowledge. Show both.

## Next

→ **[Section 15: Quick Reference](../15-quick-reference/cheat-sheet.md)**
