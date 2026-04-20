# Red-Flag Answers to Avoid

Interviewers don't grade just correctness — they grade how you think. These answers look plausible but signal problems.

## Factual Red Flags

### "Connectors create cases."

**No.** Connectors create **alerts**. The platform groups alerts into cases. Saying this wrong signals you never shipped a real connector.

### "I'd just use `uuid.uuid4()` for the alert_id."

Idempotency broken. Every run emits fresh alerts. Duplicate flood in production.

Correct: use the third-party's **stable external ID**.

### "`@output_handler` is the recommended pattern."

It's legacy. TIPCommon 2.x `Action` base class is what new integrations use. The repo still has `@output_handler` code, but it's for back-compat only.

### "Put the API key in `type: string`."

Plaintext at rest, visible in logs. **Always `type: password`** for secrets.

### "`print_value=True` on the password param."

Logs the secret. CVSS-worthy. Red flag that you don't know the extraction API.

### "The integration's `identifier` can be renamed."

Wrong. It's immutable after release. Renaming breaks every customer's playbook that references it.

### "Every integration needs all three — actions, connectors, jobs."

Wrong. An integration needs **at minimum** a Ping action and a `definition.yaml`. Many VirusTotal-style enrichment integrations have zero connectors and zero jobs.

### "Parsers and connectors do the same thing."

No. Parsers feed SIEM (UDM); connectors feed SOAR (alerts). Parsers scale linearly; connectors don't. Feed + Parser is the preferred path when available.

### "Ontology is optional."

Partly true, partly wrong. Ontology is **optional for pure-action integrations**, but **REQUIRED for any integration with a connector**. Missing ontology for a connector silently breaks case grouping.

### "CLA signed at cla.google.com."

Close but wrong URL. It's **cla.developers.google.com**.

## Structural Red Flags

### "I'd write the code first, then figure out tests."

Signals you think tests are a chore, not a design tool. In this codebase, tests gate PRs — write them alongside the code.

### "LGTM" with no line comments on a 500-line PR.

Rubber stamp. No careful review. Red flag for reviewer quality.

### "I don't use type hints — they slow me down."

Violates the repo's explicit style. `mp check --static-type-check` fails your PR anyway.

### "We just push to main."

Content Hub uses PR-gated main with required status checks — no direct pushes. If you said this, you haven't actually worked on this project.

### "We have one big test file per integration."

Red flag. The standard is a `tests/` directory with per-module splits: `test_defaults/test_imports.py`, `test_actions/test_<n>.py`, etc.

### "Everything's in the same `.venv`."

Wrong — each integration has its own `.venv` because TIPCommon versions differ per integration.

## Process Red Flags

### "I'd ship it, then fix forward if there's a problem."

In a regulated customer-facing product, this is cowboy talk. The fix-forward attitude is OK for backend experiments; it's reckless for production SOAR content touching customer case queues.

### "I don't believe in post-mortems — they waste time."

Red flag. Post-mortems with tracked action items are how teams stop repeating mistakes.

### "If a teammate disagrees with my review, I just approve."

You're not reviewing — you're rubber-stamping. Disagreement should be engaged, not dodged.

### "I don't need to talk to the SDK team — I just work around the SDK."

Architecture-as-isolation. Reasonable cross-team communication prevents the kind of miscommunication that breaks 30 integrations at once.

## Behavioral Red Flags

### "I don't have any weaknesses." / "My biggest weakness is that I care too much."

Sniffed out immediately. Have a real weakness with a concrete improvement you've made.

### "Tell me about a conflict — I don't really have conflicts."

Nobody who's led a team for 5 years has avoided conflict. Either you're lying or you've been passive. Both are red flags.

### "That wasn't my fault — it was [teammate]."

Even if true, blaming in an interview is career-limiting. Reframe as a system problem: "Our process for X didn't catch Y; here's what we changed."

### "I solved it by working 80-hour weeks."

Hero culture. Red flag. Interviewers want to hear how you prevent crises, not how you heroically survive them.

### "I don't need to understand the business side."

Self-limiting. Leads connect technical work to business outcomes; ignoring that ceiling is a career-limiting stance.

## Architectural Red Flags

### "We should rewrite it all."

The second-worst answer in software. Incremental is almost always correct. "Rewrite" is a signal you haven't thought through migration cost.

### "Just use async everywhere — it's faster."

Async has real costs: debugging, maintainability, correct concurrency. It's a tool, not a default.

### "I'd cache everything."

Cache invalidation is one of the two hardest problems in CS. "Just cache it" is naïve. Name the invalidation strategy.

### "We don't need tests for TIPCommon changes because integrations test integration behavior."

Dangerous. TIPCommon changes affect hundreds of integrations. TIPCommon itself needs rigorous tests.

### "Perfect is the enemy of good — ship it now."

Context-dependent; in security tooling, "perfect" often maps to "correct." Shipping a broken connector is worse than shipping nothing.

## Interview-Specific Red Flags

### Not asking any questions at the end.

Signals disinterest. Always have 3-5 prepared — see **[Behavioral Questions](../13-leadership/behavioral-questions.md)** section.

### Rambling answers > 3 minutes.

Signals lack of structure. STAR format keeps you under 3 minutes while hitting all the right beats.

### Disagreeing with the interviewer's premise without acknowledging it.

"You're asking the wrong question" might be true but you need to hear the question out first, then reframe politely.

### Using filler words heavily under stress.

"Uh, so, like, basically, um, kind of..." — signals nervousness. Slow down. Silence is fine.

### Saying "I don't know" without a follow-up.

Honest is good. Better is: *"I don't know that specific detail — here's how I'd figure it out / what I'd expect based on related knowledge."*

## The Golden Rules

1. **Own the mistake; never blame the team mid-answer.**
2. **Quantify when you can** — numbers beat adjectives.
3. **Structure every answer** — STAR for behavioral, 3-step outlines for technical.
4. **Show your thinking** — name hypotheses, explain tradeoffs.
5. **Admit uncertainty deliberately** — makes everything else you say more credible.

## Next

→ **[Day-Before Checklist](day-before.md)**
