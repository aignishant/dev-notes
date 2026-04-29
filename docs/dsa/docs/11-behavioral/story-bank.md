# Story bank — the 8 stories every senior should have

> Eight reusable stories cover ~90% of behavioral questions. Write them once, retag for every company.

<span class="phase-status phase-done">Phase 14 — story bank + worksheet</span>

---

## 🏛️ Why a bank, not a script

Engineers prep one or two stories, then panic when the question doesn't match. The fix: **eight diverse stories**, each retaggable to many prompts. When the interviewer asks "tell me about a conflict", you don't memorise "the conflict story" — you scan your eight, pick the one that fits *this* phrasing, and tell it.

A good bank has stories that:

- Span **different scopes** (small bug fix → org-wide initiative).
- Span **different roles** (you led / you contributed / you disagreed / you mentored).
- Have **specific numbers** (latency, revenue, users, cost, time).
- Have **a mistake or a tradeoff** — not all triumphs.

---

## 📚 The 8 stories

Each story below:

1. **Theme** — the core signal it evidences.
2. **Common prompts** — what questions it answers.
3. **Maps to** — which company values / LPs.
4. **Shape sketch** — STAR-L outline.

---

### 1. The conflict story

**Theme**: disagreement with a peer or senior, resolved with data + judgment.

**Prompts**:

- "Tell me about a conflict with a coworker."
- "Describe a time you disagreed with your manager."
- "When did you have to push back on a decision?"

**Maps to**: Amazon **Have Backbone, Disagree and Commit** • Google **collaboration + intellectual humility** • Meta **Be Open** • Microsoft **growth mindset**.

**Shape sketch**:

> S: Tech lead wanted X library; I believed Y was the right choice for our scale.
> T: 1-week deadline before lock-in.
> A: Wrote a 1-page comparison memo with 3 benchmarks I ran. Walked her through it. She raised constraints I hadn't considered (operational cost, on-call). I revised; she agreed Y was better for the long-term but X for V1. We shipped X for V1, planned Y for V2.
> R: V1 shipped on time, V2 migration started 4 months later, no on-call regressions.
> L: I'd write the memo *first* next time, not after disagreement surfaced.

??? warning "Trap"

    The "I won the argument" framing. Strong candidates show **both sides moving** — that's collaboration evidence, not stubborn-ness evidence.

---

### 2. The leadership story

**Theme**: you took ownership of an ambiguous problem nobody else owned.

**Prompts**:

- "Tell me about a time you led a project."
- "Describe a situation where you had to take initiative."
- "When did you go beyond your role?"

**Maps to**: Amazon **Ownership + Bias for Action** • Google **bias to action** • Meta **Be Bold** • Apple **craft**.

**Shape sketch**:

> S: Build pipeline was flaky — 30% of CI runs failing for unrelated reasons.
> T: Not assigned to me; nobody owned it; we were losing 6 dev-hours / day.
> A: Spent a Friday evening tracing the top 5 flake causes. Wrote a 1-page report Monday. Volunteered to drive fixes; got buy-in from manager for 1 week of focus. Coordinated with infra team on the 2 systemic issues; fixed the other 3 myself.
> R: Flake rate from 30% → 4% in 2 weeks. Saved ~30 dev-hours/week.
> L: I should've raised it as a team-level concern earlier instead of working around it.

??? warning "Trap"

    Claiming credit for work others did. Always name the team members who contributed.

---

### 3. The failure story

**Theme**: a real, owned failure with concrete learning.

**Prompts**:

- "Tell me about your biggest failure."
- "When did something not go as planned?"
- "Describe a mistake you made."

**Maps to**: Every company. **Self-awareness is the primary signal in behavioral rounds.**

**Shape sketch**:

> S: Migrating an auth subsystem to a new library.
> T: Cutover scheduled for Saturday 2am, low-traffic window.
> A: I'd tested staging exhaustively but skipped a load test against the real auth provider's rate limits, assuming "we're under the limit". At cutover, prod immediately hit a hidden burst-rate limit; users got logged out for 22 minutes before I rolled back.
> R: 22-minute partial outage; ~3% of active sessions affected.
> L: I now write a "what could go wrong" doc before any cutover and explicitly include external dependencies. I also added a load-test against rate limits to our migration runbook template.

??? warning "Trap"

    The "weakness was caring too much" / "perfectionism" answer. Universally panned. **Pick a real failure.** The interviewer is grading whether you can own one — they're not punishing you for having one.

---

### 4. The ambiguity story

**Theme**: you made progress without clear requirements / direction.

**Prompts**:

- "Tell me about a time you worked with ambiguous requirements."
- "When did you have to make a decision without all the information?"
- "Describe an open-ended project."

**Maps to**: Google **comfort with ambiguity** • Amazon **Are Right, A Lot + Dive Deep** • Meta **Move Fast + Be Bold**.

**Shape sketch**:

> S: PM said "make checkout faster" — no spec, no target, no instrumentation.
> T: One quarter to ship something that mattered.
> A: Spent week 1 instrumenting checkout to find the real slow steps. Found 70% of latency was in 2 backend calls. Talked to PM, scoped the project to those 2 calls. Set target: cut median checkout latency by 40%. Designed, built, shipped.
> R: Median checkout time 4.2s → 2.1s (50% reduction). Conversion +1.8%.
> L: Defining the problem was 30% of the work — I'd start with that next time too, but write it up as a doc to align stakeholders earlier.

??? warning "Trap"

    "I just figured it out" — too vague. Show **how** you reduced ambiguity (data, conversation, scoping doc).

---

### 5. The technical risk story

**Theme**: a calculated bet — non-obvious technical choice that worked.

**Prompts**:

- "Tell me about a time you took a risk."
- "When did you make a non-obvious technical choice?"
- "Describe a time you advocated for a contrarian approach."

**Maps to**: Amazon **Invent and Simplify + Are Right, A Lot** • Meta **Be Bold** • Apple **craft** • Google **bias to action**.

**Shape sketch**:

> S: Search ranking was a hand-tuned scoring formula; team was iterating linearly.
> T: I believed embedding-based ranking would unlock 20%+ relevance gain.
> A: Spent 2 weeks of my own time prototyping with a small dataset. Showed manager the prototype + a 6-week plan with milestones + a kill-switch criterion ("if relevance gain < 8% at week 4, abort"). Got buy-in.
> R: Shipped at week 7 (1 week late). Relevance gain measured at +22%. Manager invited me to drive the V2.
> L: I underestimated the eval setup time. Next time I'd budget 30% for evaluation infrastructure.

??? warning "Trap"

    Risks where "the risk" was lazy or untested. Show the **calculation** — the kill-switch, the milestone gates, the prototype.

---

### 6. The customer-impact story

**Theme**: you flagged or fixed something that mattered to a real user.

**Prompts**:

- "Tell me about a time you delighted a customer."
- "When did you advocate for users against pressure?"
- "Describe a time you understood a customer problem deeply."

**Maps to**: Amazon **Customer Obsession** (must-have) • Apple **craft + privacy** • Adobe **domain interest** • Microsoft **customer focus**.

**Shape sketch**:

> S: Support ticket volume up 30% on the mobile app — couldn't tell why from internal metrics.
> T: Eng lead said "let support handle it"; I disagreed.
> A: Spent half a day reading 50 tickets. Found a clear pattern: users on a specific Android version saw a layout bug after a recent update. Filed bug, wrote a fix, shipped to that segment in 3 days.
> R: Support ticket volume back to baseline. ~15k users unblocked.
> L: We didn't have telemetry that would catch this; I added an automated funnel-drop alert as a follow-up.

??? warning "Trap"

    Generic "I care about users". Show the **specific user** + **specific action**.

---

### 7. The mentoring story

**Theme**: you raised someone else's effectiveness.

**Prompts**:

- "Tell me about a time you mentored someone."
- "Describe a time you helped a junior engineer."
- "How have you scaled yourself through others?"

**Maps to**: Amazon **Hire and Develop the Best** • Google **collaboration** • Meta **Meta, Metamates, Me** • Microsoft **One Microsoft**.

**Shape sketch**:

> S: New grad on team was struggling with code reviews — getting 30+ comments per PR.
> T: Manager asked me to help informally.
> A: Reviewed his last 3 PRs together, walked through the patterns. Pair-programmed once a week for a month. Pointed him at 2 internal docs and 1 book chapter. Gave him a small project to lead end-to-end.
> R: His PR comment count dropped to ~6 by month 2. He led the project successfully and got a promotion 9 months later. He still pings me with questions but his self-sufficiency is high.
> L: Pair programming was the unlock — I'd start with that next time, not with the docs.

??? warning "Trap"

    Vague "I helped my team grow". Pick **one person**, **specific actions**, **measurable change**.

---

### 8. The ethics / pushback story

**Theme**: you said no to something that was wrong, even at cost.

**Prompts**:

- "Tell me about a time you stood up for what was right."
- "When did you push back on a leadership decision?"
- "Describe an ethical dilemma."

**Maps to**: Amazon **Have Backbone + Earn Trust** • Apple **privacy + discretion** • Anthropic / safety-tilted companies • RBI / SEBI **integrity**.

**Shape sketch**:

> S: Marketing wanted to A/B test a dark-pattern unsubscribe flow that would reduce opt-outs by an estimated 8%.
> T: I was the engineer who'd build it.
> A: Raised the concern in the kickoff: "this violates our privacy principles, and I think it's a regulatory risk." Asked for a 30-min review with legal. Legal sided with me. We redesigned the flow to be clearer instead.
> R: Opt-outs went up 1.2% with the new flow — but no regulator action and no user backlash. We'd later learn the original design was illegal in 2 EU jurisdictions.
> L: I waited until kickoff to raise it; I'd raise it in the planning doc next time so it's resolved before engineering work starts.

??? warning "Trap"

    Self-righteousness. Tell it calmly — you raised it, listened, a decision was made, you committed.

---

## ✍️ The worksheet — write your own

For **each** of the 8 themes above, fill out:

```
THEME: ___________________________________

PROMPT (one common phrasing): ___________________________________

S — Situation (where, when, who):
___________________________________

T — Task (what you specifically had to do):
___________________________________

A — Action (4-5 bullets — what YOU did, not "we"):
1. ___________________________________
2. ___________________________________
3. ___________________________________
4. ___________________________________
5. ___________________________________

R — Result (with NUMBERS):
___________________________________

L — Learning (what you'd do differently):
___________________________________

VALUES / LPs THIS EVIDENCES (3-5):
___________________________________

Length when spoken aloud: ____ seconds (target 90)
```

Print the worksheet 8 times. Fill out one per day for 8 days. By the end you have a full bank.

---

## 🪤 Common bank-building mistakes

??? warning "All wins, no failures"

    A bank without #3 (failure) is unusable. Interviewers ask for a failure in 70%+ of behavioral rounds.

??? warning "Stories from the same project"

    If 6 of your 8 stories come from one project, the interviewer will probe other projects. Diversify.

??? warning "Stories you can't quantify"

    "It made the team happier" — too soft. Find a metric. Even rough ones ("from 3 incidents/week to 0").

??? warning "Stories older than 2 years"

    For mid-career roles, stories from before 2 years ago read as stale. For new grads, college projects are fine.

??? warning "Stories you didn't actually own"

    If you can't answer "what did *you* specifically do" with verbs you can defend, drop the story.

---

## 🔁 Retagging — one story, many prompts

The conflict story (#1) above can answer at least 6 different prompts depending on emphasis:

| If asked… | Emphasise |
|---|---|
| "Tell me about a conflict" | The disagreement + how you resolved it. |
| "Disagree with manager" | The tech-lead role + your written memo. |
| "How do you handle pushback" | Her counter + you revising your view. |
| "Time you changed your mind" | The constraints she raised + you updating. |
| "Cross-team negotiation" | The V1/V2 compromise. |
| "How do you make decisions" | The benchmarks you ran + the data-driven case. |

Same story. Five different framings. **This is the leverage of a story bank.**

---

## ⏱️ Practice — 90-second drills

For each story:

1. Write it out at ~250 words.
2. Read aloud. Time yourself.
3. If over 90s, cut adjectives + context-setting.
4. Re-read at the new length.
5. Do this 3 times per stor
y over 3 days. The compression sticks.

Record audio on your phone. Listen back once. The first listen is uncomfortable; the second is where you find the fixes.

---

## ➡️ Where this connects

- Fold each story into a [STAR-L answer](star-method.md).
- Tag against [Amazon LPs](amazon-leadership-principles.md) / [Googleyness](googleyness.md) / [Meta values](meta-move-fast.md) / [MS-Apple-Adobe](microsoft-apple-adobe.md) for company-specific framing.
- Use [50 questions](common-questions.md) as the prompt list to drill against.
