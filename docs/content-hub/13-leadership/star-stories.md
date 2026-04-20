# STAR Stories Bank

Pre-structured stories you can adapt. **Replace specifics with your real examples** — names, metrics, dates. Interviewers can smell made-up stories; make yours true.

The structure: **Situation → Task → Action → Result**. Keep to 2-3 minutes each; the Action section is 70% of the airtime.

---

## Story 1 — Leading the TIPCommon 2.x Migration

**Situation**
*"We had 40+ community integrations built on the legacy `@output_handler` procedural pattern — TIPCommon 1.x. Over 3-4 years of accretion, the code quality was inconsistent, error handling duplicated, tests sparse. Platform SDK changes were breaking integrations one by one because each had its own ad-hoc SDK usage."*

**Task**
*"As team lead, I owned the migration to TIPCommon 2.x class-based base classes — without breaking customer deployments, and with a team of 2-3 engineers alongside normal work."*

**Action**
*"I broke it into phases. First, **stopped the bleeding** — updated `mp validate` to reject new integrations pinning 1.x, preventing new tech debt. Second, **built a compatibility shim** in 2.x that matched 1.x's observable behaviors — I didn't want integrations to surface subtle differences. Third, **wrote a migration tool** that auto-generated the 2.x class skeleton from a 1.x action and left business logic as TODOs for humans.*

*Then I piloted three integrations myself end-to-end and wrote a runbook. The team executed in waves of 5 per week. Each PR deployed to staging, ran 24 hours before production promotion. We had a regression harness that replayed mocked third-party fixtures through both old and new, flagging any behavioral diff.*

*For rollout, we parallel-deployed old + new for one release cycle, customers opted in, and telemetry drove cutover — we kept the old version until active usage dropped to zero."*

**Result**
*"All 40+ integrations migrated in ~14 weeks. Zero customer-reported regressions during migration. Error handling consistency improved across the board — `mp validate` now catches at PR time what used to surface as production bugs. Incident rate on migrated integrations dropped ~40% year-over-year based on our ticket tracking. Migration runbook now onboards new team members who work on legacy code elsewhere in the org."*

---

## Story 2 — Connector Scaling Under Load

**Situation**
*"A major customer's CrowdStrike connector was ingesting ~500 alerts per 5-minute cycle. Their volume grew to ~5,000 during a security event. The connector fell behind — each cycle processed less than arrived. Backlog unbounded, case queue missing alerts, customer escalated."*

**Task**
*"Diagnose and restore timely ingestion without losing alerts."*

**Action**
*"I instrumented the connector first — added per-phase timing. The bottleneck was N+1: we called `/detections/{id}/detail` per detection. 500 alerts × 300ms = 2.5 minutes on API alone. With processing overhead, we hit the 5-minute platform timeout.*

*Short-term I refactored to use CrowdStrike's batch `/detections/entities/summaries/GET/v1` endpoint — 500 detections in one call. That alone restored steady-state ingestion.*

*Then I added cursor-based pagination with connector context checkpointing — if a cycle couldn't finish the full backlog, the next cycle resumed from saved cursor. No dropped alerts during bursts.*

*For the longer term I proposed splitting into two connectors — High-severity at 1-minute cadence, Low-severity at 10-minute cadence — giving ops knobs to balance freshness vs load. That landed the following quarter."*

**Result**
*"Cycle time dropped from failing-to-complete to ~40 seconds. Backlog cleared within 2 hours of deploy. Customer retained. The pagination + batch pattern became standard in our connector template — 5 subsequent connectors adopted it. I wrote up the pattern in our internal playbook for scale incidents."*

---

## Story 3 — A Critical PR That Needed Pushback

**Situation**
*"A senior engineer on an adjacent team opened a PR introducing a new TIPCommon helper for parameter extraction with a signature that clashed with our existing one — similar name, different semantics (returned None on missing instead of raising). They were blocked on it for their own project."*

**Task**
*"Decide whether to accept, ask for rework, or propose an alternative — under pressure of their timeline."*

**Action**
*"I blocked the PR with a specific, technical explanation — not just 'I disagree.' The existing `extract_action_param` raises `ParameterExtractionError`, handled centrally by the base `run()` method. Silently returning None would bypass that error path and cause subtle failures deep in action code rather than clean user-facing messages at the extraction phase.*

*I proposed an alternative: keep their function but name it `extract_action_param_safe` with explicit semantics. That way both patterns coexist, each clearly named for what it does.*

*I booked 30 minutes with the engineer to walk through it. Turned out their real need was a default value without raising — which our existing function supports via `default_value=...` with `is_mandatory=False`. They changed their PR to use the existing helper. Their project unblocked same day."*

**Result**
*"Avoided adding a confusing duplicate API to a library used by 100+ integrations. The engineer later said the conversation clarified the design philosophy of TIPCommon for them — that clean user-facing errors beat defensive None returns. I used this interaction as a training example in our code-review guide."*

---

## Story 4 — Shipping an Integration Under Deadline

**Situation**
*"A partner vendor wanted their integration live by their RSA conference announcement — 6 weeks out. Their OAuth flow was custom (not standard client credentials), they wanted 8 actions + a connector + a widget, and the partner's point-of-contact was unreachable half the time."*

**Task**
*"Deliver a shippable, tested, partner-labeled integration in 6 weeks."*

**Action**
*"I scoped hard. Of the 8 actions they requested, 3 were mission-critical for the RSA demo; the other 5 were nice-to-have. I negotiated a phase-1 release with the critical 3 actions plus the connector, and phase-2 for the rest three weeks later. This got us a realistic first milestone.*

*On the custom OAuth, I paired with our senior engineer to build it as a reusable pattern in the integration's `core/auth.py` — not as a one-off — so if we ever encountered the same non-standard flow elsewhere, we'd have a template. Took two days.*

*To handle the partner's patchy availability, I front-loaded the unknowns: spec'd the 3 actions' semantics in the first week, got sign-off async, then the team could execute without needing them. I scheduled one 30-min sync per week, not ad-hoc.*

*Testing: I wrote a mock version of their API server (`tests/core/product.py`) matching their response shapes. This unblocked parallel test writing without needing their sandbox.*

*I personally wrote the first action end-to-end and had the team mirror the pattern for the other two. Pair-review on each PR."*

**Result**
*"Phase 1 shipped 4 days before the RSA announcement. Partner demoed successfully. Phase 2 landed on its 3-week extension. The reusable OAuth pattern was later applied to two other partner integrations. One lesson — I'd have pushed harder earlier for explicit API documentation from the partner; half our debugging time was reverse-engineering undocumented edge cases."*

---

## Story 5 — Handling a Production Incident

**Situation**
*"At 11 PM on a Friday, alerts started firing — a community connector's recent release (merged that afternoon) was posting duplicate alerts to one customer's queue. Case volume tripled in 40 minutes."*

**Task**
*"Contain the issue, restore normal operation, and prevent recurrence without creating additional customer pain."*

**Action**
*"I acknowledged in the on-call channel immediately and opened an incident doc. First question: scope. Single customer or broader? I pulled logs — only one customer had the new version deployed. Second question: contained or growing? Growing. Case queue doubling every 10 minutes.*

*I made the call: roll back that specific customer's integration to the previous version in the Content Hub catalog. That stopped ingestion of duplicates within 5 minutes. I communicated to the customer's on-call: problem contained, investigation ongoing, no action needed from them.*

*Then I diagnosed. The recent release had changed the connector's `alert_id` generation from the third-party's stable detection ID to a `uuid.uuid4()` — a one-line PR change that slipped through review because the author's test mock didn't exercise idempotency across runs. Every cycle was treating old alerts as new.*

*Fix was narrow: revert the ID change, add an idempotency regression test, mandate the test pattern via `mp validate` checks. Landed the fix in the main branch that weekend.*

*Post-mortem Monday: blameless, focused on 'how did the test gap slip.' Action items: (1) add idempotency-across-runs as a required test pattern; (2) add a `mp validate` check catching `uuid.uuid4()` as an `alert_id`; (3) contribute a 'connector idempotency' section to the contribution guide."*

**Result**
*"Customer impact: ~40 minutes of noisy queue, no lost alerts. Fix deployed by Monday. All three action items completed within two sprints. Since then, similar bugs have been caught at PR stage rather than in production. The incident became a training example in our onboarding — 'here's a subtle bug that slipped; here's what we changed so it won't again.'"*

---

## Story 6 — Mentoring a Struggling Engineer

**Situation**
*"A mid-level engineer on my team, strong individual contributor, was missing our standard 1-day PR review SLA repeatedly. His own PRs were getting stuck in review loops for weeks. Manager flagged it in a check-in."*

**Task**
*"Understand what was going on and help him either get on track or escalate appropriately."*

**Action**
*"First 1:1, I didn't lead with the metric. I asked what was hard about his week. Turned out he was taking on too much — someone he trusted had left and he'd absorbed their ownership informally without naming it.*

*We made two changes. One, I re-distributed his absorbed ownership to three people, not just to him. Two, I set specific weekly reviewing goals — 2 PRs per week, reviewed within 24 hours, nothing else — to create a habit that then extended.*

*For his own PRs stuck in review: I asked why he thought they were stuck. He said reviewers kept asking big-picture design questions. I looked at one — and reviewers were right, his PRs were large and hard to scope. So we paired on decomposing the next feature into 4 small PRs. Each merged in 2 days instead of 2 weeks.*

*Over the following quarter I checked in weekly, not biweekly. His review metric recovered within a month. His own PR velocity recovered within 6 weeks."*

**Result**
*"He's now one of our strongest reviewers and a reliable shipper. He's started mentoring newer hires on the small-PR pattern. I learned that 'missing SLA' is almost never about the SLA — it's about something underneath. Pattern I now apply to everyone on the team when metrics drift."*

---

## Story 7 — Disagreement With a Peer Lead

**Situation**
*"The platform team's lead proposed an SDK change that would have broken two major TIPCommon versions simultaneously. The change was technically cleaner but would have forced content-hub to re-release 30+ integrations on a compressed timeline."*

**Task**
*"Find a path that accommodated their technical goal without the breaking cost to our team."*

**Action**
*"I started by not fighting the change directly. I wrote up the actual cost — estimated engineer-days to migrate 30 integrations, expected regression risk, customer-impact scenarios. Concrete numbers, not just concerns.*

*Then I proposed a phased plan: maintain the old SDK surface as a deprecated-but-functional shim for two releases, giving content-hub a realistic migration window. The platform lead could ship their cleaner interface on the new path immediately.*

*We met over a 30-minute whiteboard session. I listened to their constraints — they had their own downstream consumers depending on the clean interface landing by a specific date. So we found the crossover: 6-month shim period, clearly marked as deprecated, with joint-team communication plan.*

*I documented the agreement in an RFC — the shim would be removed in version X, migration guide Y, owning team Z for each phase."*

**Result**
*"Both teams shipped their pieces on time. No customer-facing breakage. The RFC became a template for future cross-team API transitions. I learned: coming to a disagreement with cost numbers beats coming with opinions. Leadership peer respected the 'here's what this costs us' framing even when we disagreed."*

---

## Adapting These to Your Real History

For each: replace the specifics with your actual ones. Don't invent — interviewers smell fake immediately. The structure is transferable; the data must be yours.

Three questions to ask yourself when preparing:

1. **Can I name specific metrics?** (count of integrations, % improvement, days saved, customer count)
2. **Can I name my specific action clearly separate from the team's?** ("I did X" not "we did X")
3. **Would a teammate recognize this story?** (If yes, it's real; if no, it's embellished)

Polish these 6-8 stories across topics (shipping, scaling, people, incidents, disagreements, mentorship). You'll draw from them for 90% of behavioral questions.

## Next

→ **[Behavioral Questions](behavioral-questions.md)**
