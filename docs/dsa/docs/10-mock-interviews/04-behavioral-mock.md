# Mock 4 — Behavioral / Leadership Round (45 min)

> **Setup**: Amazon-style bar-raiser interview. Two STAR-anchored questions, deep follow-ups. The transcript shows what "deep" looks like — interviewers will *not* let you finish a tidy story.

<span class="phase-status phase-done">Phase 14 — Mock Interview</span>

---

## 🎬 Transcript

### Story 1 — Disagree and Commit (~22 min)

> **I**: Tell me about a time you disagreed with a teammate and ended up committing to their direction.
>
> **C** *(Situation, ~30 s)*: At my previous company we ran a billing pipeline that aggregated usage events. The team was deciding whether to migrate from a homegrown event store to Kafka. I'd built the homegrown store and was the de-facto owner of it.
>
> **C** *(Task, ~30 s)*: My tech lead — let's call her S — proposed migrating to Kafka. I disagreed: the homegrown store was working, fully observable, and the migration would be 3 months of pure infrastructure work with no user-visible features.
>
> **C** *(Action, ~3 min)*: I wrote a design doc explaining why I thought the migration wasn't worth it. Three points: existing system met all current SLAs; Kafka would solve a problem we didn't have yet (fan-out to multiple consumers); migration cost was real, sustained-feature cost was opportunity-equivalent. S read it, came back with a counter-doc focused on the *next two years* of demand: three new internal teams wanted the events, and serving each of them through our existing API would require write fan-out we didn't support. After that I changed my mind. I committed by leading the migration myself, including the parts I'd argued against. I onboarded one of those three teams personally.
>
> **C** *(Result)*: Migration completed in 14 weeks, 2 weeks over my own estimate. All three downstream teams onboarded within 6 months. The homegrown store was decommissioned without incident. I learned to weight *future* demand heavier in architectural decisions — my error was asking "does the current system work?" when I should have asked "does the current system work for the workloads we'll have in 18 months?"

> **I**: Why did her doc convince you and not your own?
>
> **C**: Mine answered the wrong question. I argued total cost vs benefit *today*. She argued cost vs benefit over a planning horizon. The data on the three new teams was real — I'd just discounted it because it wasn't urgent.
>
> **I**: How did you feel during the migration, after you'd lost the argument?
>
> **C**: Honestly mixed. The first month I had a chip on my shoulder — I was building the thing I'd argued against. I caught myself looking for evidence that I'd been right. I told my manager that, and she pushed me to write a "what I'd want this to look like" doc — basically reframed me from a passive executor into the architect of the new system. After that the chip went away.
>
> **I**: Have you been on the other side since? Where someone disagreed with you and committed?
>
> **C**: Yes — last year. A junior engineer pushed back on a database choice (I wanted Postgres, he wanted DynamoDB for a write-heavy ingestion path). I made the call for Postgres. Six months in he was right — we're now sharding it manually because the workload outgrew it. I told him directly that he'd been right, and that I'd weighted his argument too lightly because he was new to the team.
>
> **I**: How did you weigh his argument too lightly?
>
> **C**: I treated his lack of context on the existing system as if it negated his domain knowledge. He'd worked at a place that ran exactly this kind of pipeline on Dynamo. I should have separated "doesn't know our codebase" from "doesn't know the technology." Different things.

??? tip "What just happened"

    The follow-ups went **emotional → specific → reciprocal → meta**. Each layer pushes for evidence the candidate has reflected, not just rehearsed. Notice the candidate volunteered the failure case (the Postgres call) rather than waiting to be asked. Bar-raiser gold.

### Story 2 — Highest Standards (~18 min)

> **I**: Tell me about a time you raised the bar on code or process beyond what was asked.
>
> **C** *(Situation)*: Same company, different team. We were shipping a feature flag system. The roadmap said "build the API and a basic admin UI."
>
> **C** *(Task)*: I owned the API.
>
> **C** *(Action)*: As I was implementing the flag-evaluation path, I noticed it was on the hot path of every request — we were going to add ~3 ms per request on day one. The roadmap didn't mention performance. I raised it in standup; the product manager pushed back ("ship it, optimise later"). I didn't drop it. I built two extra things the roadmap didn't ask for: (1) a benchmark suite that ran on every commit and would fail the build if median latency on flag evaluation exceeded 0.5 ms, and (2) a client-side cache that warmed at process start and refreshed in the background, so the hot path was a memory lookup. Day-one performance was 0.1 ms p99 instead of 3 ms. I didn't ship the cache as a bonus — I made it a precondition of GA.
>
> **C** *(Result)*: Feature flags went out and our service-wide p99 didn't move at all. Six months later the team that built the *next* internal platform asked me how I'd done it; the benchmark-as-build-gate became a pattern across our org.

> **I**: How did the PM react when you held GA on the cache?
>
> **C**: Annoyed. He raised it with my manager. I'd written the rationale up beforehand — including a forecast of what would happen to the request-latency dashboards on day one without the cache, and what the rollback would cost. My manager backed the call. The PM and I had a follow-up where I committed to giving him an early heads-up next time I planned to expand scope, even when I thought it was clearly right.
>
> **I**: Was the PM still annoyed after that?
>
> **C**: Yeah — for a sprint or two. Honestly that was on me. I'd been right on the technical merits but I hadn't done the work of giving him a real heads-up. Saying "I'll build a benchmark suite, it'll add a week" the day before code-complete is not the same as raising it at sprint planning.
>
> **I**: When would you NOT raise the bar like that?
>
> **C**: Two cases. (1) When the increment is mine, not the user's. If I want a fancier abstraction or a more elegant API and the user-visible result is identical, that's my own polish — do it on my own time or not at all. (2) When the team has explicitly de-prioritised it. If we've discussed performance, agreed it's fine, and shipped — going back and re-litigating because I personally would have done it differently is corrosive.

??? tip "What just happened"

    The interviewer asked "when would you NOT do this?" — a classic test for whether the candidate has internalised the principle as a *trade-off*, not a personality trait. Two-case answer with concrete examples passed.

### Last 5 min — candidate questions

> **C**: If I joined the team, what would the first month look like? What's a hard thing the team is currently working through? When you've watched candidates not work out at this level, what was the most common reason?

??? tip "What just happened"

    Three questions, none generic. The third is bold but legitimate — interviewers respect the question because it shows the candidate is thinking about *their own* failure modes.

---

## 🟢 What was good

- **Specific** stories with names, time-frames, dollar / week / percent figures.
- **Volunteered failures** without being asked (the Postgres call).
- **Emotional honesty** ("first month I had a chip on my shoulder").
- **Meta-reflection** that named the *general lesson*, not just "I learned to listen better."
- Anticipated the "when would you NOT" follow-up with a structured two-case answer.

## 🟡 What was weak

- Story 1 was 22 min — at the upper edge of what an interviewer wants. Two questions in 45 min is the goal; three is better.
- Quantified results were a little soft ("decommissioned without incident"). Numbers like "saved $X/month in storage" or "P99 dropped from Y to Z" are stronger.
- Both stories were technical. A behavioural round usually wants at least one *people* story (a hire, a coaching, a difficult report).

## 🔁 How to do it better

1. **Pre-load 6-8 stories** across the leadership principles, each with: 30 s situation, 30 s task, 3 min action, 30 s result. Practice the *action* part — that's where 80% of signal lives.
2. **Have a "people" story** that doesn't involve writing code. E.g., a 1:1 that changed someone's trajectory; a conflict between two reports; a hire you championed.
3. **Bring numbers**. "p99 latency dropped from 240 ms to 32 ms," "we cut on-call pages from 30/week to 4/week," "the migration saved $180K/year." Even round-numbered estimates beat adjectives.
4. **Have a 2-3 min version of every story**. Some interviewers will cut you off at the 90-second mark to test your compression. Practice the compressed version separately.

---

## 🃏 Cheatsheet for behavioural rounds

- STAR with the action part heaviest (3 min of a 5 min answer).
- Specific names, dates, dollar/percentage figures.
- Volunteer the failure case before being asked.
- Have a story per leadership principle pre-built.
- Reserve 1-2 stories about *people*, not code.
- Compressed (2 min) and expanded (5 min) versions of each.
- Three pre-loaded candidate questions, one of them bold.
