# Handling Incidents

## The Calm Script

Production breaks. Your job as lead: **bring calm, fast triage, and structured recovery.** Here's the sequence.

## Phase 1 — Acknowledge (0-5 min)

- Acknowledge in the relevant channel so everyone knows it's being handled
- Create an incident tracking doc (link in channel)
- Page on-call if it's not already them
- State scope: *"Seeing X, customer Y impacted, investigating"*

Calm language, no blame, no speculation. Customers and teammates watch leaders for signal.

## Phase 2 — Triage (5-30 min)

Answer three questions fast:

1. **What's broken?** (symptom, not cause)
2. **Who's affected?** (one customer, all customers, one integration, all connectors)
3. **Is it getting worse?** (linear, exponential, stable)

Gather evidence:

- Recent deploys? (70% of incidents are someone's recent change)
- Recent third-party status page? (50% of the rest)
- Matching logs across affected connectors
- Customer-side vs platform-side

Don't diagnose yet. Gather enough to decide: **contain vs investigate**.

## Phase 3 — Contain (decision point)

If impact is growing, **contain first, diagnose after**.

- Roll back the last deploy (if recent)
- Disable the failing connector / integration version in the customer's tenant
- Throttle requests if rate-limit storm
- Switch off automation that's amplifying the blast radius

**Containment is success.** It buys you time to diagnose without escalating customer pain.

## Phase 4 — Diagnose (30 min - hours)

Methodical, not heroic:

- Read logs with timestamps aligned
- Diff: what was the last-working state vs now?
- Reproduce locally if possible
- Narrow suspect list to one or two theories
- Confirm (or refute) each theory with evidence

Pair with someone — incident fatigue is real, a second pair of eyes catches mistakes.

## Phase 5 — Fix (minutes, once diagnosed)

Ship the narrowest possible fix:

- Not a refactor
- Not "while we're in here"
- Not a "better solution" — just the fix
- Add a test that would have caught this
- Ship behind a flag if uncertain about blast radius

After the fix lands, monitor closely — confirm it actually resolved symptoms.

## Phase 6 — Communicate

Throughout the incident, update the channel / status page at predictable intervals:

- On identification: *"Symptom X identified, investigating."*
- Every 30 min even if nothing new: *"Still investigating; no new info."*
- On containment: *"Blast radius contained; root cause ongoing."*
- On fix: *"Fix deployed; monitoring."*
- On resolution: *"Resolved. Post-mortem to follow."*

Silence during an incident erodes trust faster than bad news.

## Phase 7 — Post-Mortem

Within 1 week:

- **Blameless** — systems, not people
- **Timeline** — what happened, when, who saw what
- **Impact** — number of customers, duration, scope
- **Root cause** — the actual technical cause (5 Whys)
- **Contributing factors** — what made it worse (missing alerts, slow rollback, etc.)
- **Action items** — concrete follow-ups with owners and dates

Action items are the highest-leverage output. Track them in a ticketing system; close them.

## Common Incident Patterns in This Domain

### Pattern 1: Connector Storm After Config Change

Customer updates Max Hours Back from 4 to 48 during a maintenance window. Next cycle pulls 48 hours of alerts. Connector runs long, falls behind, compounds. Customer calls in panic.

**Mitigation:** validate config changes gently — warning in UI on large `Max Hours Back`.

### Pattern 2: Third-Party API Schema Change

Vendor ships a new schema without notice. Pydantic model raises `ValidationError`. Connector fails silently (exception in main loop → caught by base class → logged → next cycle).

**Mitigation:** Pydantic `extra="ignore"` on external models; observability on parse failures.

### Pattern 3: Shared Rate Limit Exhaustion

Customer adds a 50th integration pulling from VirusTotal. Other 49 start 429'ing. All enrichment actions fail.

**Mitigation:** shared rate-limit coordinator in power-up enrichment; alerting on 429 rate.

### Pattern 4: Cascading Playbook Failures

An action's JSON result shape changes. Dozens of playbooks using that action's output with `.JsonResult.foo` start breaking. Placeholder resolves to literal string.

**Mitigation:** JSON schema versioning on JSON results; backwards-compatible changes only in minor versions.

### Pattern 5: Missing Ontology After Upgrade

Connector release accidentally drops `end_time` mapping. Alerts still ingest but stop grouping into cases. Case queue floods. Customer doesn't notice for days.

**Mitigation:** `mp validate` enforcing ontology requirements; alerting on unexpected case-count spikes.

## The Lead's Role in Incidents

**Not to be the smartest engineer.** Be:

- **Calmest person in the room** — panic propagates; calm does too
- **Traffic director** — who's investigating what; prevent duplication
- **Communicator** — customers, stakeholders, rest of engineering
- **Decision maker** — "we roll back" / "we push forward" — own the call
- **Protect the team** — no "why didn't you catch this" mid-incident

After: own the post-mortem, own the action items, own what changes next.

## What to Tell an Interviewer

*"I've led a handful of incidents in my time on content hub. The pattern I've settled into is: acknowledge fast in the channel, triage for 15-30 minutes to identify scope and trend, contain before fully diagnosing if impact is growing, fix with the narrowest possible change, then blameless post-mortem with tracked action items. The hardest part is emotional — keeping the team calm and resisting the urge to 'just fix it right' mid-incident. Ship the fix, revisit the architecture next sprint."*

That's a 60-second answer that shows experience.

## Next

→ **[STAR Stories Bank](star-stories.md)**
