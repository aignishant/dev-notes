# 50 common behavioral questions

> The 50 questions that show up in 90% of behavioral rounds. Each with a template, two real example shapes, and the trap.

<span class="phase-status phase-done">Phase 14 — common-question bank</span>

---

## 📋 How to use this page

1. Pick the questions tagged for your target company (Amazon LP / Google / Meta / Microsoft / Apple / Adobe / Service / PSU).
2. Map each question to **one story from your [story bank](story-bank.md)**. Reuse aggressively — one story can answer 3-5 questions with different framings.
3. Practice **out loud**. Reading is not practice.

Tag legend: **[A]** = Amazon &nbsp; **[G]** = Google &nbsp; **[M]** = Meta &nbsp; **[MS]** = Microsoft &nbsp; **[Ap]** = Apple &nbsp; **[Ad]** = Adobe &nbsp; **[S]** = Service co &nbsp; **[P]** = PSU

---

## A. Self-introduction & motivation (5)

??? question "1. Tell me about yourself. **[All]**"

    **Template**: Background → 1-2 highlights → current focus → why this role.

    **Example shape**: "I'm a backend engineer with 4 years at [Company], where I currently lead the search team's infrastructure. Two highlights — I rebuilt our query routing layer (cut p99 from 800ms to 120ms), and I mentor 2 junior engineers. I'm interested in [Target] specifically because [team's problem matches my background]."

    **Trap**: reading your résumé. Pick 2-3 highlights, leave hooks.

??? question "2. Why do you want to work here? **[All]**"

    **Template**: 3 specific reasons, none of which are "stock + brand".

    **Example shape**: "Three reasons. First, [team's specific work] — I read [their blog post / paper] and the approach resonates. Second, the scale — [number]. Third, [growth angle for me — e.g., I want to learn distributed systems and your team builds them daily]."

    **Trap**: generic flattery. Make it specific to the team.

??? question "3. Why are you leaving your current role? **[All]**"

    **Template**: Forward-looking, not backward. Never bad-mouth.

    **Example shape**: "I've grown a lot at [Company] — shipped X, learned Y. I'm looking for the next stretch, which is [scale / domain / depth] that I can find at [Target]."

    **Trap**: "My manager / company is bad." Disqualifying everywhere.

??? question "4. Where do you see yourself in 5 years? **[All]**"

    **Template**: A role at the company that builds on the role you're applying for.

    **Example shape**: "I'd like to be a senior / staff engineer at [Target], having grown deep in [domain] and started mentoring others on it."

    **Trap**: "Starting my own company / doing an MBA" — disqualifying for full-time roles.

??? question "5. What are you currently learning? **[G][M][Ap][MS]**"

    **Template**: One specific topic, what triggered it, what you've actually built.

    **Example shape**: "I've been learning Rust over the past 3 months. Triggered by reading about Discord's migration. I rewrote a small utility I had in Python — turned a 50ms hot loop into 3ms. I'm not production-ready yet but I get the appeal."

    **Trap**: "I just read books." Show **applied** learning.

---

## B. Strengths, weaknesses, self-awareness (6)

??? question "6. What's your biggest strength? **[All]**"

    **Template**: Strength + 1 specific example evidencing it.

    **Example shape**: "Calm under pressure. Last quarter we had an outage at 11pm — my call, my fix, post-mortem the next day, no team panic."

    **Trap**: claiming a strength with no example. Generic strengths are forgotten.

??? question "7. What's your biggest weakness? **[All]**"

    **Template**: Real weakness + active mitigation.

    **Example shape**: "I tend to over-commit early in a project — say yes to too many parallel things. I started using a personal kanban with a strict 'in-progress = 2' limit; that's helped me push back earlier."

    **Trap**: "perfectionism / caring too much / working too hard". Universally panned.

??? question "8. Tell me about a time you failed. **[A][G][M][MS]**"

    **Template**: STAR-L. Real failure, your role in it, what you'd do differently.

    **Example shape**: "Owned a migration; underestimated cross-team coordination. Cut over before all consumers were ready, broke 3 dashboards. Spent 2 days firefighting. Lesson — I now build a stakeholder map and confirm sign-off in writing before any cutover."

    **Trap**: false-failure. Fake humility ("My biggest failure was caring too much") signals lack of self-awareness.

??? question "9. Tell me about feedback you didn't agree with. **[MS][G][A]**"

    **Template**: Specific feedback, your initial reaction, how you weighed it, what you eventually did.

    **Example shape**: "Manager told me I was 'too direct in code reviews'. I disagreed initially — felt it was clear feedback. Then I asked 2 colleagues; both said the tone landed as harsh. I started prefixing comments with 'optional:' / 'one option:' for non-blocking suggestions. Net better."

    **Trap**: "I disagreed and stuck to my guns." Misses the self-awareness signal.

??? question "10. What would your last manager say is your area to grow? **[MS][G][Ad]**"

    **Template**: Specific growth area, what you've done about it.

    **Example shape**: "She'd say I should write more — design docs, RFCs. I'm naturally a 'just build it' person. I committed to writing 1 doc per quarter and have stuck to it for the past 4."

    **Trap**: "She'd say I'm too good at everything." Tone-deaf.

??? question "11. Tell me about a time you took on too much. **[MS][G]**"

    **Template**: Specific overload moment, how you triaged, what you cut.

    **Example shape**: "Q4 last year — I was on-call, leading 2 features, and mentoring a junior, all at once. I dropped the ball on the junior's 1-on-1 prep two weeks running. Brought it up with my manager, transferred his mentorship to a peer for the quarter, told him directly what was happening."

    **Trap**: making it sound effortless. They want self-correction.

---

## C. Conflict + collaboration (8)

??? question "12. Tell me about a conflict with a coworker. **[All]**"

    **Template**: Real disagreement, how you approached resolution, outcome.

    **Example shape**: "Disagreed with a senior IC on whether to rewrite or refactor a service. Wrote a 1-pager comparing risks; she pushed back with specific examples I'd missed; we landed on hybrid (refactor now, rewrite later). Stayed friends."

    **Trap**: "We didn't really disagree — we talked it out". Missing the conflict.

??? question "13. Tell me about a disagreement with your manager. **[A][G][M]**"

    **Template**: Disagreement, how you raised it, the resolution, what you committed to afterwards.

    **Example shape**: "Manager wanted to deprioritise a tech-debt cleanup I thought was urgent. I escalated by writing a 1-pager with specific incidents the debt had caused. She pushed back; I prioritised her items, but she allocated 1 sprint per quarter to the debt. Six months in, debt was 70% reduced."

    **Trap**: "I went over her head." Failure mode unless severe ethics issue.

??? question "14. Tell me about a time you helped a struggling teammate. **[All]**"

    **Template**: Specific person, specific intervention, specific outcome.

    **Example shape**: "Junior on the team was missing deadlines. I asked her in 1-on-1; turned out she was reluctant to ask for code review. I started a 30-min Tuesday review session; she ramped up; six months later she was shipping faster than I was."

    **Trap**: making it about you ("I rescued the project").

??? question "15. Tell me about a time you persuaded someone. **[All]**"

    **Template**: Person, what they thought, your approach, the change.

    **Example shape**: "Senior eng was sceptical of moving to a new framework. I built a 2-day POC, ran it side-by-side with the old system, showed him the numbers. Switched in week 3."

    **Trap**: "I just kept pushing until they gave in." Persuasion, not attrition.

??? question "16. Tell me about a time you disagreed and committed. **[A]**"

    **Template**: STAR-L with a clear "I committed despite disagreeing".

    See [Amazon LP — Have Backbone](amazon-leadership-principles.md#13-have-backbone-disagree-and-commit).

??? question "17. Tell me about a time you worked with a difficult person. **[All]**"

    **Template**: What made them difficult, how you adapted.

    **Example shape**: "Worked with a PM who critiqued in writing harshly. I started copying both of us on every action item with explicit ownership; reduced ambiguity, the friction dropped."

    **Trap**: making it about them being bad. Make it about your adjustment.

??? question "18. Tell me about a cross-team project. **[All]**"

    **Template**: What spanned teams, your role, how alignment was reached.

    **Example shape**: "Our search team needed cooperation from indexing + ranking + serving. I drafted the cross-team plan, ran weekly 30-min syncs, managed the dependency graph. Shipped on date."

    **Trap**: vague "we collaborated". Show **how**.

??? question "19. Tell me about giving difficult feedback. **[G][MS][Ap]**"

    **Template**: Person, situation, how you delivered, outcome.

    **Example shape**: "Peer was checking in unfinished code. I told him directly in 1-on-1, framed as 'I want to be honest'. He pushed back; I gave specific examples. He adjusted; we kept the working relationship."

    **Trap**: avoiding the actual feedback. They want to hear what you said.

---

## D. Initiative, ownership, leadership (7)

??? question "20. Tell me about a time you took initiative. **[A][M][G]**"

    **Template**: Spotted-something-nobody-asked-you-to-do + outcome.

    **Example shape**: "Noticed our staging environment was 6 weeks behind production. Nobody owned it. I built a daily sync script + monitoring; staging stayed within 2 days for the rest of my tenure."

    **Trap**: claiming you "led" something everyone was on.

??? question "21. Tell me about a project you owned end-to-end. **[A][G][Ap]**"

    **Template**: Project, your scope, what end-to-end meant, outcome.

    **Example shape**: "Owned a 10-week feature — design, code, tests, rollout, post-launch monitoring. I set the scope, wrote the design doc, coded the bulk, coordinated 2 collaborators on edges, ran the rollout. Post-launch hit my user-engagement target within 2 weeks."

    **Trap**: "End-to-end" = "I did everything alone". Almost never true; admit collaborators.

??? question "22. Tell me about leading without authority. **[All]**"

    **Template**: Initiative outside your formal role, how you got buy-in.

    **Example shape**: "Was an IC on the team; spotted that we were duplicating work with another team. Set up a monthly cross-team review (no meeting requested by management). It became permanent within a quarter."

    **Trap**: claiming "leadership" of a meeting you just attended.

??? question "23. Tell me about a time you made a tough decision. **[All]**"

    **Template**: Decision, options, why you chose, what happened.

    **Example shape**: "Had to cut a feature 1 week before launch — third-party dependency was unstable. Decision: ship without it. Painful for the PM, right for users. Re-added the feature in next release with a stable replacement."

    **Trap**: "Easy decision in hindsight." Show why it was hard.

??? question "24. Tell me about mentoring someone. **[A][MS][G]**"

    **Template**: Mentee, what they needed, your specific intervention, growth.

    See Question 14.

??? question "25. Tell me about delegating. **[G][M]**"

    **Template**: When, why, to whom, outcome.

    **Example shape**: "Junior was ready for harder work. Handed off the search-config feature with a 30-min kickoff. He shipped in 3 weeks; I checked in twice, didn't micromanage."

    **Trap**: "I delegated and forgot about it." Some oversight is expected.

??? question "26. Tell me about a time you set a high standard. **[A][Ap]**"

    **Template**: Standard, why, how you held the line, outcome.

    See [Amazon LP — Insist on the Highest Standards](amazon-leadership-principles.md#7-insist-on-the-highest-standards).

---

## E. Customer / impact (5)

??? question "27. Tell me about a time you went above and beyond for a customer. **[A][Ad]**"

    **Template**: Customer, normal expectation, what you did beyond, outcome.

    **Example shape**: "Customer reported a bug we'd marked as 'won't fix — edge case'. Investigated; turned out it affected 3% of paying users. Pushed for a fix that quarter; shipped it. Their renewal came in unexpected."

    **Trap**: not having a real customer story. Fake ones are obvious.

??? question "28. Tell me about a measurable impact you've had. **[All]**"

    **Template**: Specific work + before-and-after metric.

    **Example shape**: "Rebuilt the index pipeline. Build time went from 6 hours to 35 minutes. Team can now reindex daily where they used to do it weekly; freshness improved measurably."

    **Trap**: vague "made things better". Numbers or it didn't happen.

??? question "29. Tell me about a project that changed direction mid-way. **[M][G]**"

    **Template**: Original direction, what triggered the pivot, what you did.

    **Example shape**: "Started building a feature for power users. Halfway through, A/B test data showed casual users were the actual growth lever. Pivoted in week 4 — kept 60% of code, redesigned the UX. Shipped 2 weeks later than plan; right product."

    **Trap**: "We didn't really change much." Show the pivot.

??? question "30. Tell me about a time you said no. **[A][G][M][MS]**"

    **Template**: Ask, your reasoning, how you said no, outcome.

    **Example shape**: "PM asked for a feature 1 week before our quarterly launch. I said no, gave specific risk reasoning, proposed it in next quarter. He pushed back; I held; we shipped clean and added the feature 6 weeks later."

    **Trap**: "I never say no." Then you have a different problem.

??? question "31. Tell me about doing something for the long term. **[M][G]**"

    **Template**: Investment > immediate return, why, outcome.

    See [Meta — Focus on Long-Term Impact](meta-move-fast.md).

---

## F. Technical judgment + risk (5)

??? question "32. Tell me about a tough technical problem. **[All]**"

    **Template**: Problem, why hard, your approach, outcome.

    **Example shape**: "Race condition in a high-QPS service appeared once a week. Reproduced locally with chaos-testing tools, found a non-atomic read-then-write pattern across two replicas. Fix was a CAS loop; problem disappeared."

    **Trap**: making it sound easy. Show the difficulty.

??? question "33. Tell me about a time you took a calculated risk. **[A][M]**"

    **Template**: Risk, your calculation, outcome.

    **Example shape**: "Proposed an unproven approach for a critical service. Risk: 30% chance it failed; reward: 50% latency improvement. We A/B'd at 1% traffic for 2 weeks before scaling. It worked."

    **Trap**: "I just did it." That's recklessness, not calculated.

??? question "34. Tell me about a time you simplified something complex. **[A][G]**"

    **Template**: What was complex, what you simplified, outcome.

    See [Amazon LP — Invent and Simplify](amazon-leadership-principles.md#3-invent-and-simplify).

??? question "35. Tell me about a debugging story. **[Ap][G][N (NVIDIA)]**"

    **Template**: Symptom, your hypotheses, what you tried, root cause, fix.

    **Example shape**: "Service was returning 500s ~once an hour. Two hypotheses: GC pause or upstream timeout. I added tracing; turned out neither — a memory-mapped file was being remapped under load. Fix: pre-allocate. p999 dropped 100×."

    **Trap**: skipping the wrong hypotheses. Showing the dead-ends adds credibility.

??? question "36. Tell me about an architecture decision you made. **[All — senior]**"

    **Template**: Decision, alternatives considered, criteria, outcome.

    **Example shape**: "Chose Postgres over a NoSQL store for a 10× growth use case. Criteria: existing team expertise, transaction needs, expected size at year 2. NoSQL would have given us scale-out 'free' but cost us in operational complexity. Two years on, Postgres is still working; right call."

    **Trap**: not naming the alternative. Decisions need at least one rejected alternative.

---

## G. Pressure, ambiguity, growth (5)

??? question "37. Tell me about a high-pressure moment. **[All]**"

    **Template**: Setup, your role, what you did, outcome.

    **Example shape**: "Outage 4 hours before a major launch. I was on-call. Triage to 3 hypotheses in 20 mins, picked one, rolled forward, recovered the service in 90 mins. Launch went on time."

    **Trap**: bragging. Stay calm in the retell.

??? question "38. Tell me about a project with shifting requirements. **[All]**"

    **Template**: Original scope, what shifted, how you adapted.

    **Example shape**: "Started a feature with one customer in mind. Halfway through, sales pulled in a different customer with different needs. We split the feature into two configurable paths. Both shipped; some over-engineering, but managed it."

    **Trap**: complaining about scope creep. Show adaptation.

??? question "39. Tell me about a time you had to learn something new fast. **[MS][G]**"

    **Template**: What, why fast, how you learned, outcome.

    See Question 5.

??? question "40. Tell me about a time you didn't have enough information. **[G][M][A]**"

    **Template**: The gap, your decision under uncertainty, outcome.

    See [Google — Comfort with ambiguity](googleyness.md).

??? question "41. Tell me about your most ambiguous project. **[G][M]**"

    **Template**: What was ambiguous, how you brought structure.

    **Example shape**: "Took on an exploratory ML project with no clear success metric. First two weeks I built a draft metric, validated it with 3 stakeholders, shipped a v0 to iterate against. Without that, the project would have wandered for months."

    **Trap**: thriving in chaos without delivering structure.

---

## H. Closing + culture-specific (9)

??? question "42. Why should we hire you? **[All]**"

    **Template**: Concise, specific match between your strengths and the role.

    **Example shape**: "Three reasons. First, my last 4 years align directly with [the team's problem space]. Second, I bring [specific strength — e.g., systems-design across layers]. Third, I'm at a stage where I want to invest in mentoring + scope, which the role description includes."

    **Trap**: generic "I'm a hard worker" lists.

??? question "43. What questions do you have for us? **[All]**"

    Always have 2-3.

    **Safe genres**:

    1. **About the team's recent work**: "I read about [X] — what's the next 6-month direction?"
    2. **About the role's evolution**: "What does success look like 3 / 12 months in?"
    3. **About the interviewer**: "What's the most surprising thing about working here?"

    **Trap**: "How much does it pay?" / "When do I hear back?" Never ask comp here; that's for the recruiter.

??? question "44. Tell me about Amazon's [specific LP]. **[A]**"

    Direct LP question — you should know all 16. See [Amazon LP page](amazon-leadership-principles.md).

??? question "45. What's your view on user data? **[Ap]**"

    **Template**: Pro-privacy, pragmatic, with a real example.

    See [Apple — Privacy mindset](microsoft-apple-adobe.md).

??? question "46. Tell me about a time you collaborated with a designer / PM. **[Ad][Ap]**"

    See [Adobe — Friendly Domain](microsoft-apple-adobe.md).

??? question "47. Are you willing to relocate? **[S][P]**"

    **[Service / PSU]**: yes, anywhere. See [Service HR rounds](service-company-hr.md).

??? question "48. Are you OK with the bond? **[S]**"

    **[Service co]**: yes, with terms understood. See [Service HR rounds](service-company-hr.md).

??? question "49. What's happening in your sector recently? **[P]**"

    **[PSU]**: 2-3 current items + your view. See [PSU style](psu-interview-style.md).

??? question "50. What's a recent technical thing you're excited about? **[All]**"

    **Template**: One thing + why + what you've done with it.

    **Example shape**: "Rust async runtimes — Tokio specifically. I'm excited because of the borrow-checker meeting concurrency safely. I've been porting a small library as a learning project; it's slow going but each bug I trip is a real lesson."

    **Trap**: hype-chasing. Show actual engagement, not headlines.

---

## ➡️ Next

Once you've mapped these to your 8 stories ([story bank](story-bank.md)), do a 1-hour mock with a friend. Random 5 questions, 90 seconds each, friend grades each on a 1-5.

Then re-rehearse the bottom-2.
