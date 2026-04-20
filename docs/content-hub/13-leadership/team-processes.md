# Team Processes

Processes are what separate a team that scales from one that drowns. Your 5 years of lead experience means you've built these — articulate them.

## The Core Processes You Should Be Able to Describe

### 1. Intake & Prioritization

> *"How do new integration requests get into the backlog?"*

Typical flow:

1. Request comes in (customer, sales, partner, internal)
2. Logged in issue tracker with: vendor, use case, estimated scope, requesting customer, urgency
3. Weekly triage meeting — evaluate against capacity and existing commitments
4. Assign: (a) build internally, (b) route to partner, (c) defer, (d) decline
5. Communicate decision back to requester

Avoid: ad-hoc build-what-we're-excited-about. Without process, the backlog becomes personal preference.

### 2. Sprint / Cadence Model

> *"How does work flow once in the backlog?"*

Common pattern: 2-week sprints with:

- Planning — pull top priorities from backlog, break down into stories
- Daily standups (15 min)
- Mid-sprint check-in
- Demo + retrospective at end
- Next sprint planning begins

For content-hub specifically, many items are sized small (one integration action) and fit in a sprint; larger initiatives (new integration, migration) span multiple sprints with visible milestones.

### 3. On-Call Rotation

> *"When a customer's connector breaks at 2 AM, who responds?"*

Characteristics of a healthy on-call:

- Rotating weekly among senior team members
- Clear escalation path (L1 → L2 → engineering lead)
- Documented runbooks per integration — what "broken" looks like, how to diagnose
- Post-incident review for non-trivial incidents
- On-call work credited in individual review

### 4. PR Review SLA

> *"How do we keep PRs from rotting?"*

Expected:

- Initial review within 1 business day
- Full review cycle within 3 business days
- Draft PRs excluded until marked Ready for Review
- Weekly review metrics: avg time-to-first-review, avg time-to-merge

Reviews are part of the job, not overhead. Leads should model this — review PRs first thing each day.

### 5. Release & Deprecation Cadence

> *"How often do we publish new content, and how do we retire old content?"*

- Continuous delivery — merged content flows through publishing pipeline same-day/week
- Versioning — semver on every integration
- Deprecation policy: flag `deprecated: true` → N months grace → `removed: true`
- Customer comms for breaking changes (`regressive: true` release notes)

### 6. Documentation Requirements

> *"What do we require contributors to document?"*

Per integration:

- `README.md` at the integration root (optional but encouraged)
- Action `description:` fields filled (use `mp describe` for consistency)
- `overviews.yaml` for playbooks (marketing-quality)
- Release notes per change
- Ontology mapping comments for non-obvious mappings

Docs are a PR gate — missing docs = request changes.

### 7. Onboarding

> *"How long before a new hire ships their first PR?"*

Target: **2 weeks** from start to merged PR.

Structure:

- Week 1: environment setup, read docs, pair-programming with senior on a small task
- Week 2: pick a real low-risk ticket, complete it, open PR, ship
- Week 3-4: solo work with code-review safety net
- Month 2: can ship a new small integration end-to-end

Key: the onboarding task is *real work*, not a throwaway tutorial. Makes the new hire's impact tangible from day one.

### 8. Cross-Team Collaboration

> *"How do you interact with the SOAR platform team (which owns the SDK)?"*

- Quarterly sync on roadmap alignment
- Dedicated Slack channel for SDK questions
- Escalation path when SDK changes break integrations
- Platform team's SDK RFCs reviewed by content-hub leads

Avoid: "throw work over the fence." Content and platform teams must see each other's constraints.

## Leadership Metrics You Actually Use

| Metric | What it tells you |
|---|---|
| Time-to-first-review | Team responsiveness; contributor experience |
| PR merge rate | Are contributions actually landing? |
| Deployment frequency | Pipeline health |
| Bugs-per-integration per quarter | Quality trend |
| On-call load per person | Burnout risk |
| Test coverage per integration | Long-term stability |
| Active contributor count | Community health |

Track at least three. If you can't name any metrics, you're not leading — you're just coding with authority.

## Process Anti-Patterns to Avoid

| Anti-pattern | Fix |
|---|---|
| "I review everything" (single-point-of-failure) | Build review rotation; distribute ownership |
| No standup → drift | 15-min sync, ruthlessly time-boxed |
| 3-week PR review cycles | SLA in writing, track + escalate |
| No deprecation policy → legacy forever | Quarterly deprecation review |
| "We don't need docs, we know the code" | New hires disagree loudly |
| Heroics culture | Shared on-call, not individual hero on-call |

## Interview Framing

When asked "how did you manage your team?":

> *"Four things I paid explicit attention to: intake & prioritization (weekly triage with documented decisions), PR review SLA (1 business day first look), on-call rotation (weekly rotating among 4 seniors with documented runbooks), and onboarding (new hire ships real PR in 2 weeks). I also tracked time-to-first-review and PR merge rate — if either trended wrong, I treated it as a team-health signal, not a code quality one."*

That's a leader-sounding answer in 60 seconds.

## Next

→ **[Code Review Standards](code-review.md)**
