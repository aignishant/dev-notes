# The STAR method

> Situation, Task, Action, Result. The four-bullet scaffold that turns a 5-minute ramble into a tight 90-second answer.

<span class="phase-status phase-done">Phase 14 — STAR essentials</span>

---

## 📋 The structure

| Letter | What goes here | Length |
|---|---|---|
| **S — Situation** | Where + when + business context. **One** sentence. | ~10s |
| **T — Task** | Your specific responsibility. What you owned. | ~10s |
| **A — Action** | The concrete steps **you** took. The bulk of the answer. | ~50s |
| **R — Result** | Quantitative outcome + lesson learned. | ~20s |

Total: ~90 seconds. If you can't compress to ~90s, you don't know the story well enough.

---

## ⚠️ The single biggest mistake

**Spending 60 seconds on Situation + Task, then rushing Action.**

Interviewers grade Action. Situation + Task are scaffolding. If you've burned 60s of context, you've used most of your budget on the part nobody scores.

Time it. Practice trimming. The leanest version of "where I was" beats the richest one.

---

## ✅ A worked example

> "Tell me about a time you had to convince a senior engineer to change their approach."

??? example "Long, unstructured version (the failure mode)"

    "OK so this was at my previous company, we were building a fraud detection system, and there was this really senior engineer Ravi who'd been there like 10 years and he had a lot of opinions, and we were trying to figure out the right way to do feature engineering, and Ravi had this approach where he wanted to do everything in batch jobs but I was looking at the latency requirements and I thought we should do streaming and so we had like a few meetings about it and at first he was kind of dismissive but then I put together this analysis and we went through it together and eventually he came around, and yeah we shipped it, the system worked well…"

    **Why it fails**: rambling, no structure, no numbers, "kind of" / "like" hedges, no clear Action steps, fuzzy result.

??? example "STAR version"

    **Situation**: "At my last company we were rebuilding a fraud-detection system. SLA was 200ms p99 end-to-end."

    **Task**: "I owned the feature pipeline. The senior architect, who'd shipped the previous version, wanted batch features only. I believed we needed streaming features to hit the SLA."

    **Action**: "I did three things. First, I instrumented the existing system and showed the breakdown — features were 80% of total latency, dominated by point-lookups in batch tables. Second, I built a 24-hour POC against three real fraud patterns and measured: streaming gave us 40ms p99, batch gave us 180ms. Third, I framed the conversation as a hybrid — keep batch for the heavy aggregations, add streaming for hot features — so we kept his existing investment."

    **Result**: "He agreed, we shipped the hybrid 6 weeks later, end-to-end p99 came in at 110ms. The bigger lesson was that I'd initially framed it as 'batch vs streaming' which is adversarial; reframing as 'hybrid' won the room in 5 minutes."

    **Why it works**: 4 sentences of context, 5 sentences of Action, 2 sentences of Result, ~85 seconds spoken.

---

## 🧰 Common variants of STAR

Most interviewers know STAR. Some companies use slight twists.

### CAR (Context, Action, Result)

Drops Task. Used when Task is implicit. **Same thing, lower overhead.**

### SOAR (Situation, Obstacle, Action, Result)

Adds Obstacle — an explicit "what made this hard". Useful for technical-difficulty stories.

### STAR-L (… + Learning)

Adds an explicit Learning step at the end. Amazon's Bar Raiser interviewers love this. "What did you learn? What would you do differently?" closes the loop on self-awareness.

**Default to STAR-L.** Always close with a one-sentence lesson, even if not asked.

---

## 🎯 What each section is graded on

| Section | Grader is checking |
|---|---|
| **Situation** | Is this real? Is the context sized appropriately? Don't pick a story too small (Hello World level) or too big (Saved the Company in 24 Hours). |
| **Task** | Was YOUR scope clear? Were you accountable, or just adjacent? Senior interviewers detect fake ownership instantly. |
| **Action** | Did you DO the work, or did "we" do it? **Use "I" 3-5× more than "we"**. The "we" trap is the #1 reason senior candidates fail behavioral. |
| **Result** | Real number > qualitative claim. "p99 dropped from X to Y" beats "we made it faster". If you don't know the number, don't make one up — say "I don't remember the exact number; ballpark X". |

---

## 🪤 Specific anti-patterns to avoid

??? warning "The hero story"

    "I single-handedly saved the launch by working 90 hours straight." → red flag. Senior interviewers read this as "this person doesn't delegate / doesn't manage their time / will burn out their team". Frame heroics as "we shipped against a tight constraint" not as "I rescued everyone".

??? warning "The vague-failure story"

    "My biggest failure was caring too much / being too thorough / working too hard." → universally panned. Pick a real failure with measurable impact. Show specific corrective action.

??? warning "The 'we' inflation"

    "We built a service handling 10M req/sec." → great, but **what did YOU do?** If your answer to "what did YOU do" is "I was on the team", you don't have a story.

??? warning "The over-rehearsed answer"

    Polished to the point that pauses and adjustments to the actual question vanish. Sounds memorised. Interviewers feel it. Practice the **shape**, not the words.

??? warning "The omitted Result"

    Engineers love Action; they often forget to land the Result. Without Result, the story is half a story. Even a partial result is fine: "we shipped it; not enough time post-ship to know full impact, but the leading indicator was X."

---

## ✏️ Practice prompt

Pick **one** story you'd tell about yourself. Write it as STAR, capped at 90 seconds spoken. Then trim to 75. Then re-add ONE sentence. Iterate.

If you can't make it interesting at 90 seconds, the story isn't the right one. Switch.

The 8 stories you should have on tap are in the [story bank](story-bank.md).

---

## ➡️ Next

Pick your target company's section:

- [Amazon — 16 LPs](amazon-leadership-principles.md)
- [Google — Googleyness](googleyness.md)
- [Meta — Move Fast](meta-move-fast.md)
- [Microsoft / Apple / Adobe](microsoft-apple-adobe.md)
- [Service company HR](service-company-hr.md)
- [PSU interviews](psu-interview-style.md)

Or jump straight to [50 common questions](common-questions.md).
