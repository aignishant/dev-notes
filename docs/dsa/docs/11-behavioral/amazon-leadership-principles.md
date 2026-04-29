# Amazon Leadership Principles

> Required reading even if you're not interviewing at Amazon. Microsoft, Google, and many others copy this rubric.

<span class="phase-status phase-done">Phase 14 — 16 LPs decoded</span>

---

## 🏛️ Why LPs matter

Every Amazon interview round (5 onsites + Bar Raiser) is **explicitly** mapped to 2-3 LPs. The interviewer fills out a rubric afterwards: "Did this candidate evidence Customer Obsession? Bias for Action? Earn Trust?" If a story you tell **doesn't map to an LP**, it isn't graded.

So: every story you tell should be tagged with the LPs it evidences. Aim for **2 stories per LP** in your story bank — 32 stories total. Reuse aggressively (one story can map to 2-3 LPs).

The 16 LPs are below, with what each really tests, the trap, and an example shape.

---

## 1. Customer Obsession

> Leaders start with the customer and work backwards.

**What it really tests**: did you push back against an internally-easy decision because it was bad for the customer?

**Trap**: stories where you did "what was right for the user" without anyone disagreeing with you. No tension = no story.

**Example shape**: "PM wanted X because it boosted a revenue metric. I had data showing X hurt customer retention by Y%. I pushed for measurement, we A/B'd, the data won, we shipped Z instead."

---

## 2. Ownership

> Leaders don't say "that's not my job."

**What it really tests**: did you fix something that wasn't strictly yours, with downstream consequences you owned?

**Trap**: hero stories. "I worked 90 hours" reads as poor planning, not ownership.

**Example shape**: "Bug was technically owned by another team but blocking my service. Instead of just filing a ticket, I debugged it, sent them a fix with tests, and proposed a process change for the future."

---

## 3. Invent and Simplify

> Leaders expect and require innovation … find ways to simplify.

**What it really tests**: did you reduce complexity, not just add features?

**Trap**: "I built a really cool thing." That's invention, not simplification. The bar wants both.

**Example shape**: "We had 4 separate dashboards for 1 metric. I unified them into one with saved-views, deprecated 3, reduced eng-on-call load by 40%."

---

## 4. Are Right, A Lot

> Leaders have strong judgment and good instincts.

**What it really tests**: a non-obvious call you made that turned out right, and you can articulate why.

**Trap**: "I just had a hunch." They want the reasoning, not the gut.

**Example shape**: "Team wanted to use NoSQL. I argued for Postgres because our data was relational and our team didn't have ops experience for the alternative. Six months in, we'd have been firefighting if we'd gone the other way."

---

## 5. Learn and Be Curious

> Leaders are never done learning.

**What it really tests**: a domain you actively learned that wasn't in your job description.

**Trap**: "I read a book on it." Show **applied** learning.

**Example shape**: "I had no ML background but our service needed an ranking layer. I took a Coursera course, prototyped 3 approaches in evenings, and the simplest one shipped."

---

## 6. Hire and Develop the Best

> Leaders raise the performance bar with every hire.

**What it really tests**: did you contribute to others' growth, even if you weren't a manager?

**Trap**: "I gave good feedback." Show specific growth.

**Example shape**: "Junior on my team was struggling with code review. I started a 30-min weekly mentor session, walked through patterns. 6 months later he was reviewing my PRs."

---

## 7. Insist on the Highest Standards

> Leaders have relentlessly high standards.

**What it really tests**: a moment you refused to ship something subpar.

**Trap**: framing this as perfectionism. They want **shipped**, not **polished forever**.

**Example shape**: "Code was passing tests but I noticed flakiness in production logs. Held the launch 4 days, found a race condition. The fix saved us a P0 we'd otherwise have had on day 1."

---

## 8. Think Big

> Thinking small is a self-fulfilling prophecy.

**What it really tests**: did you propose something beyond the immediate ask?

**Trap**: "I had a vision." Show that you **executed against the bigger vision**, even partially.

**Example shape**: "Was asked to fix a logging bug. Realised our logging stack was the underlying issue; pitched a 6-month plan to consolidate three systems; got buy-in; shipped phase 1, which paid for itself in alert fatigue reduction."

---

## 9. Bias for Action

> Speed matters in business.

**What it really tests**: a moment you moved without complete information, and the call worked.

**Trap**: recklessness. They want **calculated risk + speed**, not "I just shipped it".

**Example shape**: "Outage hit. Two competing diagnoses, ~70% confidence in one. I rolled with it instead of waiting for full root cause. Recovered the service, did the post-mortem after."

---

## 10. Frugality

> Accomplish more with less.

**What it really tests**: did you constrain a solution intentionally?

**Trap**: "We didn't have budget." That's a constraint imposed on you, not frugality.

**Example shape**: "Team proposed a $50k/mo Elasticsearch cluster for a use case I knew Postgres full-text could handle. I built a 200-line POC over a weekend, we deferred ES indefinitely."

---

## 11. Earn Trust

> Listen attentively, speak candidly, treat others respectfully.

**What it really tests**: a moment you delivered uncomfortable feedback (up or down) and were heard.

**Trap**: "We had open communication." Generic.

**Example shape**: "VP wanted to ship before legal review. I disagreed in writing, copied his manager, included the specific risk. He pushed back, then took a meeting, then we delayed 3 days for review. Email tone mattered — direct but not adversarial."

---

## 12. Dive Deep

> Leaders operate at all levels, stay connected to the details.

**What it really tests**: a problem you solved by getting closer to the data than expected for your level.

**Trap**: "I read the logs." That's table stakes. Show **deeper** than expected.

**Example shape**: "As tech lead I was supposed to delegate, but the latency regression bug had baffled the team for 3 days. I sat with the on-call engineer, we read the kernel-level perf trace, found a misaligned struct in our protobuf. Junior engineer wouldn't have spotted it."

---

## 13. Have Backbone; Disagree and Commit

> Leaders are obligated to respectfully challenge … but commit wholly once a decision is made.

**What it really tests**: TWO things — you disagreed strongly, AND you committed wholeheartedly after the call went the other way.

**Trap**: only telling half. "I disagreed" without commit, or "I committed" without disagreement, fails.

**Example shape**: "Argued strongly against a particular database choice. Lost the argument. Spent the next 6 weeks helping make it work — wrote the migration tooling, hosted weekly office hours for the team. Two years later it was still working fine; my prediction was wrong, the commitment was right."

---

## 14. Deliver Results

> Focus on the key inputs and deliver them with the right quality and in a timely fashion.

**What it really tests**: you shipped, on time, with quality.

**Trap**: "It was delayed but…" — Amazon's bar wants delivered, not almost-delivered.

**Example shape**: "Owned a 6-week feature. Mid-sprint hit a database limit nobody had foreseen. Triaged into MUST-have / NICE-to-have, cut scope by 30% with stakeholder buy-in, delivered MUST on date with full quality. NICE shipped two weeks later."

---

## 15. Strive to be Earth's Best Employer

> Leaders work every day to create a safer, more productive, more diverse, more just work environment.

**What it really tests**: you contributed to your team's culture, not just your own work.

**Trap**: "I was a great team player." Show specific change.

**Example shape**: "Noticed our standups were 45 mins of senior engineers monologuing. Restructured to round-robin 60-second updates with async deeper threads. Stand-up time dropped to 15 mins, junior engineers actually got to speak."

---

## 16. Success and Scale Bring Broad Responsibility

> We must be humble and thoughtful about even the secondary effects of our actions.

**What it really tests**: you considered impact beyond direct users — privacy, fairness, environmental, externalities.

**Trap**: this LP is newer; people often shoehorn old stories. Be specific about secondary effects.

**Example shape**: "Personalisation feature was working great by raw metrics. I realised our model was correlating with proxy variables for demographic groups. Pulled in a fairness review before launch. Shipped 2 weeks later with calibrated outputs."

---

## 🎯 How to use this in interviews

1. Build **2 stories per LP** in your [story bank](story-bank.md). 32 stories sounds intimidating but most overlap (one Outage story can map to Bias for Action + Ownership + Earn Trust).
2. The interviewer will tell you which LP they're testing — sometimes obliquely. Listen for "tell me about a time you…" with the LP-shape.
3. **Open with a one-line LP framing**: "This is a story about Bias for Action — when I had to ship without full information." Saves them rubric-mapping work; they love it.
4. Always close with a **Lesson Learned** sentence (per [STAR-L](star-method.md)). Bar Raisers grade self-awareness explicitly.

---

## 🪤 Bar Raiser specifics

The Bar Raiser is a senior IC from another org, has veto on the hire, and is trained to grade hard. They're disproportionately likely to ask:

- "Tell me about a time you failed."
- "Tell me about a time you disagreed with your manager."
- "What would you do differently?"

**Have these THREE stories ready, polished, with a strong Lesson.** They show up in 80% of Bar Raiser rounds.
