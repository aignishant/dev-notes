# Self-Grading Rubric

> Score yourself after every mock — your own or one with a partner. The rubric is the same one bar-raisers use, restated for first-person.

<span class="phase-status phase-done">Phase 14 — Mock Interview</span>

---

## How to use

1. Run the mock, ideally with a real partner. Record audio if possible.
2. Take a 10 min break.
3. Score each row honestly. **Be ruthless** — a 3/5 from a friend = a 2/5 in a real loop.
4. Pick the **single weakest row** and design a drill for it before the next mock. Don't try to fix everything.
5. Compare scores across mocks over weeks. Trend matters more than absolute level.

---

## DSA / Coding rubric (45 min round)

| Dimension | 1 — junior | 3 — competent | 5 — staff signal |
|---|---|---|---|
| **Problem comprehension** | Restates problem in own words after starting | Restates before starting; flags ambiguities | Surfaces 3+ traps the interviewer didn't mention |
| **Clarifying questions** | Asks 0-1, generic | 3-5 specific, useful | All assumptions made explicit; asks about scale, edge cases, API contract |
| **Algorithm choice** | Tries first idea that comes to mind | Names 2 approaches, picks one with reason | Names 3+, rules each out by named property (e.g., "BFS fails because edges aren't unit") |
| **Coding speed** | Codes slower than thinks; types out fully | Smooth typing; minor pauses | Code matches mental model in real time; few corrections |
| **Code quality** | Works but messy; dead branches | Clean; one good abstraction | Sentinel patterns, helpful names, `__slots__` / equivalent micro-touches |
| **Edge cases** | Patches when prompted | Lists before tracing | Lists, traces, asserts code already handles each |
| **Testing discipline** | Manual trace only | Trace + named test ideas | Pseudo-pytest with arrange/act/assert per case |
| **Complexity analysis** | Time only, vague ("fast") | Time + space, exact | Average vs worst case; amortised reasoning where applicable |
| **Follow-up depth** | Answers literal question | Answers + one related point | Names trade-offs (lock-free, approx, hierarchical) and conditions for each |
| **Communication** | Long pauses without narration | Mostly narrates thinking | Always narrates; pauses are explicit ("let me think for 30 s") |
| **Time management** | Runs out before finishing | Finishes with 2-3 min spare | Finishes coding by minute 25, edge cases by 35, follow-ups by 40 |
| **Candidate questions** | None or generic | Two specific | Three, one bold (e.g., "what's the team's biggest regret?") |

**Total**: /60

- **45+ /60** → strong staff/senior signal. Apply now.
- **30-44** → solid mid → senior. One or two rows are dragging you down.
- **20-29** → competent but needs work on multiple rows. Pick one.
- **<20** → drill more before booking real loops.

---

## System Design rubric (60 min round)

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Scope framing** | Dives into design without scoping | 5-7 min on functional + non-functional | Asks for budget on clarifying questions; names what's *out* of scope |
| **Capacity estimation** | Round numbers from memory | Calculated from question | Specific math chain (users → QPS → bytes → storage → cost) |
| **Architecture diagram** | Box-and-arrow with no labels | Components + protocols labelled | Read path + write path drawn separately; latency budget annotated |
| **Tech choice reasoning** | Names tools without why | "I'd use X because Y" | "I'd use X because Y; alternatives Z and W traded for these reasons" |
| **Data model** | Hand-waves "store it in a DB" | Specific schema + index strategy | Schema + sharding key + replication + access pattern justification |
| **Caching strategy** | Mentions Redis | Multi-tier (client / edge / service) | Names eviction, invalidation, hot-key mitigation, cold-start |
| **Failure modes** | "It might fail" | One per major component | One *specific* failure mode per component with response (CDN cache miss → tiered cache; DB hot key → adaptive partitioning) |
| **Trade-off articulation** | Picks an answer | "X over Y because trade-off Z" | Multi-axis trade-offs (cost / latency / consistency / dev time) |
| **Non-glamour coverage** | Skips schema, monitoring, deploy | Mentions on prompt | Naturally covers monitoring, security, on-call, regions |
| **Latency budgeting** | None | "Should be fast" | End-to-end budget with each component's contribution |
| **Self-criticism** | Defends design | "I'd validate X with a load test" | Pre-empts the interviewer with "the wave-handed part of my design is…" |

**Total**: /55

- **40+** → strong senior+ signal.
- **25-39** → mid; usually one or two systemic gaps (capacity math or non-glamour coverage).
- **<25** → spend a week on one design from `08-system-design/` before next mock.

---

## Behavioural rubric (45-60 min round)

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Story specificity** | Generic; could be anyone | Names + dates + numbers | All of (3) + the project's *constraint* (deadline, headcount, budget) |
| **STAR balance** | Action is 30 s, result is 3 min | Roughly even | Action ~3 min, result ~30 s with quantified outcome |
| **Multiple stories ready** | One story; recycles it | 4-6 ready | 8+ pre-built; one per leadership principle |
| **Failure ownership** | Externalises ("the team didn't…") | Owns part | Owns specifically; names what *they* would do differently |
| **Emotional honesty** | "It was great, learned a lot" | Names one negative feeling | Names emotion, what triggered it, how they processed it |
| **Reciprocal example** | Doesn't volunteer the inverse | If asked, can give one | Volunteers it ("I've also been on the other side, and…") |
| **Meta-reflection** | "I learned to communicate better" | Lesson with a behaviour change | Lesson generalises beyond the story to a principle |
| **People stories present** | All technical | One people story | At least 2 stories about coaching, hiring, conflict between others |
| **Compression on demand** | Loses the thread when interrupted | Recovers, finishes | Has a 2-min and a 5-min version, picks based on cue |
| **"When would you NOT" handling** | "I always do X" | One reason | Two cases with concrete examples |
| **Candidate questions** | Generic | Two specific | Three, one bold |

**Total**: /55

- **40+** → strong; you'll get the offer if technicals hold up.
- **25-39** → competent but story bank is thin or quantification is weak.
- **<25** → before the next loop, build the story bank (see [Story bank](../11-behavioral/story-bank.md)).

---

## Drill design — pick one weak row and fix it

After scoring, pick the lowest row from the lowest section. Design a 1-week drill:

| Weak row | Drill |
|---|---|
| Capacity estimation | Each morning, estimate the QPS / storage / cost for one product you use (Slack, Spotify, GitHub). Write the math chain. 10 min. |
| Coding speed | Solve 1 medium LeetCode/day with a 25-min timer. **No editing**: type once, fix only what's broken. |
| Edge cases | Before any mock problem, list edge cases on paper *first*. Don't write code until the list is complete. |
| Story specificity | Take your top 3 STAR stories. Add three numbers to each: dates, dollars, percentages. Memorise. |
| Failure ownership | Write the *manager's* version of each of your stories — what would they have said you did wrong? Internalise that. |
| "When would you NOT" | For each behavioural principle, pre-write the inversion. "I have high standards; I would NOT raise the bar when…" |
| Latency budgeting | Pick a system from `08-system-design/`. Draw it. Annotate every arrow with a latency in ms. Sum the longest path. |

---

## Tracking template

Keep a markdown file (or spreadsheet) per mock:

```markdown
## Mock 2026-04-29 — DSA, LRU Cache (with K)
- Total: 38/60
- Weakest row: time management (2/5)
- Drill: 25-min hard timer on next 5 problems
- Notes: spent 22 min on coding, 8 on edge cases, ran out before follow-ups
- Next mock target: finish coding by 18 min mark
```

After 6-8 mocks the trends are obvious. The dimensions that don't move are where you need a different drill, not more reps.
