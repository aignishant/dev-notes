# Behavioral Questions — 30+ Common Asks

For each, a brief guide on what the interviewer is really probing and which STAR story applies.

## Leadership & Ownership

### 1. "Tell me about a time you led a technical initiative end-to-end."

**Probing:** scope, coordination, outcome ownership. Use **TIPCommon migration story** (Story 1).

### 2. "Describe a project where you owned the outcome, not just your tasks."

**Probing:** ownership beyond code. Use **connector scaling story** (Story 2) — you instrumented, diagnosed, shipped, and landed a template pattern.

### 3. "Walk me through a complex system you designed or refactored."

**Probing:** architectural thinking. Migration story or new integration design framework from Section 12.

### 4. "What's the hardest technical decision you've made as a lead?"

Answer pattern: frame as a tradeoff, not as a binary right/wrong. Example: *"Decided to accept TIPCommon 1.x compat shim rather than force migration — because breaking 30+ deployed integrations would cost more trust than the cleaner code would recover. The cost of that choice: we maintained the shim for 6 months. Would I do it again? Yes."*

---

## Conflict & Disagreement

### 5. "Tell me about a time you disagreed with a teammate."

Use **PR-pushback story** (Story 3). Key: specific technical disagreement, resolved with alternatives proposed.

### 6. "How do you handle disagreement with someone more senior?"

Use **peer-lead disagreement story** (Story 7). Key: came with data, not just opinions; proposed alternative; found crossover.

### 7. "Describe a situation where you had to say no to a stakeholder."

Example pattern: *"A partner wanted us to ship a rushed integration before testing was complete. I said no — but I said yes to an interim solution: we'd ship behind a feature flag, gated to that one partner's tenant, with clear 'beta' labeling. Got their urgency met without compromising quality for other customers."*

### 8. "Tell me about a time you were wrong."

Don't dodge. Real example: *"I pushed for async on a connector that didn't need it. Volume was low; I expected scale to come. Three months later we realized async was complicating debugging for junior team members, and the performance gain never materialized because volume stayed flat. I reverted to sync. Lesson: don't architect for scale you don't have."*

---

## Mentoring & People

### 9. "Tell me about someone you helped grow."

Use **mentoring struggling engineer story** (Story 6). Specific actions, specific outcomes.

### 10. "Describe how you give feedback."

Pattern: *"Direct on the substance, kind on the delivery, specific always. PR comments get prefixes — `blocking:`, `nit:`, `suggestion:` — so the author knows what's mandatory vs optional. In 1:1s, I use SBI: Situation, Behavior, Impact. Example: 'In yesterday's standup (S), when you cut off Sara mid-sentence (B), it made the discussion feel closed down (I). Can we find a different way?' It works because it names behavior, not identity."*

### 11. "Tell me about a hire that didn't work out."

Hard question — be honest without being cruel. Example: *"Hired a strong technical candidate who didn't fit our collaborative review culture. We gave feedback, set expectations, paired extensively; at 4 months it wasn't working. My manager and I had the conversation to part ways. Lesson: I under-weighted culture fit in the interview loop. Adjusted our interview rubric to explicitly include collaboration scoring."*

### 12. "How do you onboard new team members?"

Pattern from [Mentoring](mentoring.md): 30/60/90 model, first real PR by day 14, stretch work by month 2.

### 13. "Describe how you handle someone underperforming."

Pattern: *"First, understand why — performance issues usually have a cause: overload, personal issues, skill gap, wrong role. I have a direct conversation early, not after months of passive frustration. Then we agree on specific expectations with specific dates. If it works, great. If it doesn't after genuine effort, I partner with my manager on the next step."*

---

## Incidents & Pressure

### 14. "Tell me about a production incident you led."

Use **Friday-night incident story** (Story 5). Key: acknowledge, contain, diagnose, fix, post-mortem — in that order.

### 15. "How do you handle working under pressure?"

Pattern: *"My go-to pattern is 'calm is a leverage point.' Team reads my stress — if I'm visibly stressed, they are too. So I slow down my speech, use structured triage (scope → trend → decision), and communicate at predictable intervals. After the incident, I rest, and then I run the post-mortem. Can't do post-mortems well when exhausted."*

### 16. "Tell me about a time you had to make a decision with incomplete information."

Pattern: *"Balance reversibility against cost of waiting. Reversible decisions — make them fast. Irreversible — wait for more info even if costly. During the Friday incident, rolling back was reversible; I did it in 5 minutes. If the decision had been 'let's rewrite the connector from scratch,' I'd have waited."*

---

## Collaboration

### 17. "Describe a cross-team project."

Use **peer-lead disagreement story** (Story 7) — platform team + content-hub, found a phased path.

### 18. "How do you work with product managers / stakeholders?"

Pattern: *"I treat engineering asks as business problems. Instead of 'can we build X?' I ask 'what customer problem are we solving?' That gives us room to propose alternatives that fit our constraints. I also push for written specs before coding — if it can't be written down, it's not ready to build."*

### 19. "Tell me about a time you influenced someone without authority."

Pattern: *"Brought data, named shared goals, offered to take on part of the work myself. The TIPCommon 2.x migration started as my initiative — I didn't have org authority to force it. I wrote up the cost of staying on 1.x, showed the incident trend data, proposed a pilot I'd drive myself. Leadership funded the broader migration after the pilot showed results."*

---

## Prioritization & Scope

### 20. "How do you prioritize when everything is urgent?"

Pattern: *"Three questions: what happens if this doesn't get done? (impact), is anyone else unblocked by this? (dependencies), what's the reversibility cost? Urgent-important gets done now. Urgent-unimportant gets delegated or deferred. Important-not-urgent goes into sprint planning. Urgent-everything usually means we're overcommitted — I have a conversation with the team about what we'll not do."*

### 21. "Tell me about a project you had to cut scope on."

Use **RSA deadline integration story** (Story 4) — negotiated phase 1 (3 actions) + phase 2 (5 actions).

### 22. "Describe a time you pushed back on a timeline."

Pattern: *"Customer wanted a parser + integration in 2 weeks; realistic was 6. I wrote up what was achievable in 2 (ping + 2 actions), 4 (+ connector), and 6 (+ ontology + widget + jobs). Gave the stakeholder a choice, not a rejection. They picked 4 weeks with phase 2 later."*

---

## Technical Judgment

### 23. "Describe a technical tradeoff you made."

Async connector story, or choosing TIPCommon shim over hard cutover.

### 24. "When have you chosen not to do the 'right' technical solution?"

Pattern: *"The 'right' solution often has a cost the team can't afford. Example: I wanted to refactor all our connectors to use a shared pagination helper. Would have taken 6 weeks. Instead I built the helper and required new code to use it; legacy migrated opportunistically during feature work. 'Right' solution would have delayed everything else; pragmatic path got 80% of the benefit over 6 months."*

### 25. "Tell me about a piece of code you're proud of."

Pattern: specific, technical, modest. Example: *"The connector idempotency pattern we codified — `alert_id` = stable external, processed-IDs cache capped at 10k, tested with dual-run assertion. Simple, verifiable, and it prevents a whole class of production bugs."*

---

## Self-Awareness

### 26. "What's your biggest weakness?"

Not *"I care too much"* — give something real. Example: *"Early on I tended to rewrite others' code during review rather than suggest changes — felt faster but robbed the author of the learning. I've worked on this by explicitly asking 'what change would you make?' in my comments instead of writing the replacement code. Still catch myself sometimes."*

### 27. "What have you learned in your current role?"

Pattern: one concrete learning per significant period. Example: *"Year 1, I learned the codebase. Year 2, I learned when to say no. Year 3, I learned that code review is my highest-leverage activity. Year 4-5, I learned how to delegate ownership, not just tasks — my team ships more when I'm less involved."*

### 28. "What would your team say about you?"

Mix of strengths and specific improvements. Pattern: *"They'd say I'm consistent in reviews — 1-day SLA, always. They'd say I push for quality, sometimes to the point of friction — I've been told I can over-index on edge cases. They'd say I'm there when things break. They'd also probably say I'm slow to promote ideas publicly — I focus on the team's wins more than my own."*

---

## Role Fit

### 29. "Why are you looking to change roles / why this role?"

Honest pattern: what you've learned, what's next, what this role specifically offers. Don't bash current employer. Example: *"I've spent 5 years going deep on one integration ecosystem. I want to bring that depth to a broader problem space — this role would let me apply the patterns I've built while learning a new domain. Specifically your team's [X] is something I don't have in my current scope."*

### 30. "Where do you see yourself in 3-5 years?"

Concrete + honest. Example: *"Senior staff engineer or engineering manager — I'm exploring which. The common thread: impact via a team, not as an IC. In this role, I'd expect to be leading multiple projects, mentoring other leads, and making technical calls that shape the next 2-3 years of the platform."*

---

## Rapid-Fire Questions

### 31. "What's your management philosophy?"

Pattern: *"Autonomy within constraints. Give people clear outcomes, then get out of the way. Check in weekly on blockers, not on progress."*

### 32. "Remote vs office?"

Pattern: *"I work well remote, but specific interactions — hard conversations, live coding, incident response — are better in person or on video with whiteboards. Mix of both."*

### 33. "How do you stay current?"

Pattern: *"Reading team PRs — the best and latest patterns in our codebase. Two industry newsletters I actually read (name them). Annual deep dive into one adjacent area I don't know. Not 'read everything' — chosen depth."*

### 34. "Tell me about a time you had to learn something fast."

Pattern: OAuth client credentials example from Story 4, or a parser-side question you ramped on for a review.

---

## Questions You Should Ask Them

Always have 3-5 ready:

1. *"What does success look like for this role in the first 6 months?"*
2. *"How is technical decision-making done — individual authority, group consensus, or something else?"*
3. *"What's the biggest technical challenge the team is working on right now?"*
4. *"How does this team relate to [adjacent team] — what's the boundary?"*
5. *"What do you think hasn't been solved yet that a good hire would solve?"*

Questions that show you think like a lead, not a candidate looking for a job.

---

## Interview Day Preparation

The night before:

- Review 6-8 STAR stories; not memorize, know the beats
- Check the company's recent product announcements
- Prepare 3-5 questions to ask
- Confirm logistics (time zones, video platform, documents you can access)

Morning of:

- Light breakfast
- No caffeine overdose — makes you talk fast and sound nervous
- 10 minutes of walk / no-phone before the interview
- Print or have a sheet with names and dates of your major projects — if your mind blanks, you have the facts handy

## Next

→ **[Section 14: Scenario Playbook](../14-scenarios/index.md)**
