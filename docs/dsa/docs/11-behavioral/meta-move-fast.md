# Meta — Move Fast culture

> Meta's behavioral round (the "Jedi" or "leadership" round) grades 5 specific cultural values.

<span class="phase-status phase-done">Phase 14 — Meta values + Jedi round</span>

---

## 🏛️ The 5 Meta values

| Value | What it really means |
|---|---|
| **Move Fast** | Speed > perfection. Bias to ship, then iterate. |
| **Be Bold** | Take calculated risks; don't water down ideas. |
| **Focus on Long-Term Impact** | (Recently updated from "Focus on Impact") — work on what moves the needle, durably. |
| **Be Open** | Constructive disagreement; share information; debate ideas not people. |
| **Build Awesome Things** | Quality bar matters. Don't ship sloppy. |
| **Live in the Future** | (Newer addition) — work on tomorrow's problems, not yesterday's. |
| **Meta, Metamates, Me** | Team and mission first; self last. |

The "leadership" round (45-60 minutes, often with a hiring manager or senior engineer) explicitly probes 2-3 of these.

---

## 🚀 Move Fast

**What gets graded**: did you ship despite incomplete information? When you broke something, did you fix and learn fast?

**Pre-2022 mantra**: "Move fast and break things." Now refined to "Move fast with stable infra" — but the speed bias remains.

**Trap**: stories about months of careful design. Meta wants speed.

**Example shape**: "Spotted a 5% drop in feed engagement. Same day, deployed an experiment to test my hypothesis. By the next morning we had data, by Friday we'd shipped the fix to 100%."

---

## 🎯 Be Bold

**What gets graded**: a decision where you advocated for something **non-consensus** that turned out right.

**Trap**: bold = stupid risk. Show the **calculation** behind the boldness.

**Example shape**: "Team was going to optimize the existing recommendation algorithm by 10%. I proposed rebuilding it from scratch with embeddings. Calculated risk: 6 weeks of work, but if it worked, 30%+ gain. Got buy-in, shipped, ended up at 22% gain."

---

## 🌍 Focus on Long-Term Impact

**What gets graded**: did you work on something that mattered durably? Did you push back when asked to work on low-impact things?

**Trap**: confusing "I worked on something high-profile" with "I worked on something high-impact". Profile ≠ impact.

**Example shape**: "I was asked to add 3 features to a product getting deprecated in 6 months. Instead, I proposed migrating its top 2 features into the successor product. Less visible work, but durable; the deprecated product retired clean."

---

## 💬 Be Open

**What gets graded**: did you disagree publicly and respectfully? Did you change your mind in response to new information?

**Trap**: "We had a healthy debate." Generic. Show **what changed**.

**Example shape**: "Tech lead and I disagreed on whether to use a new framework. Wrote a 1-page memo with my position; she wrote one back. Mid-debate she pointed out a constraint I'd missed; I changed my mind in the meeting. We went with her approach."

---

## ⭐ Build Awesome Things

**What gets graded**: a moment you raised the quality bar — refused to ship subpar — without grinding the team to a halt.

**Trap**: perfectionism. Meta wants quality with shipping speed.

**Example shape**: "Feature was passing functional tests but the animations stuttered on mid-tier Android phones. Held the launch 4 days, isolated the issue (a layout pass on every frame), shipped clean. The 4-day delay was worth the device-market segment we'd have alienated."

---

## 🚀 Live in the Future

**What gets graded**: did you work on emerging tech / build for what's coming? Or solve the problem your grandkids would have had with current tools?

**Trap**: chasing hype. They want **bets** with reasoning.

**Example shape**: "We were building chat features the same way we had for 5 years. I prototyped an AI-summarisation feature and showed it to my manager; pitched a 6-week investigation; led to a small team being formed."

---

## 🤝 Meta, Metamates, Me

**What gets graded**: when team success and individual visibility conflicted, did you choose team?

**Trap**: false humility. They've heard it.

**Example shape**: "Senior on my team was up for promo and one of our shared initiatives was central to her case. I deliberately let her represent it in leadership reviews even though I'd done half the work; mentioned my contribution only when asked directly. She got promoted; we both moved on better off."

---

## 🎯 What Meta interviewers grade vs Amazon's LP rubric

| Difference | Meta | Amazon |
|---|---|---|
| Pace of stories | Faster, looser, less rigid | More rigid STAR + LP-tagging |
| What gets you dinged | Slow / process-heavy / "design committee" stories | Stories without quantitative results |
| Tone | Casual / direct / "what did you do this week" | Formal / structured / "give me an example of when…" |
| Length | 90-120s OK | 60-90s preferred |
| What they probe | Bias to ship, willingness to disagree | Customer obsession, ownership, deliver results |

---

## 🪤 Specific Meta-failure modes

??? warning "The over-process story"

    "We had 4 design reviews and 3 spec docs and got buy-in from 8 stakeholders." → red flag. Meta interviews are wary of process-heavy candidates. Show **decision velocity**.

??? warning "The watered-down disagreement"

    "I had concerns about the approach but went along with it." → not Be Open. They want active disagreement, even if you eventually committed.

??? warning "The 'visible' over 'impactful'"

    "I shipped the public launch announcement / OP-ED" → that's PR. Show actual product / engineering impact.

??? warning "The acquired-company smell"

    Meta has a long history of acquisitions. If your story has the shape of "we did something the FB way of doing things doesn't allow", own it; don't pretend it was a smooth integration.

---

## ⏱️ Structure of a Meta behavioral story

- **Open fast.** Skip the "well let me think" preamble. Just start.
- **Lead with the decision or moment**, not the context. Meta interviewers want the punchline first.
- **Specific numbers, fast.** "10% engagement drop", "5 days", "$50k saved" — drop them in the first 30 seconds.
- **Close with what you'd do differently / what you learned.** Same as STAR-L.

---

## ➡️ Specific Meta-flavored prompts

1. "Tell me about a time you took a risk that didn't pan out."
2. "Tell me about a time you disagreed with your manager publicly."
3. "Tell me about something you shipped fast that wasn't perfect."
4. "Tell me about a time you said no to your tech lead."
5. "Tell me about a project where you pushed for a bigger vision."

Run each through [STAR-L](star-method.md). 90-120s.

---

## 📌 Bonus: the "ship" question

Meta interviewers often ask: "What did you ship in the last 6 months that you're proud of?"

Have an answer ready. **One specific feature**, with metrics, with the trade-off you made.

If you can't name something you shipped, prepare for that to land hard. (Unique to Meta; not as much of a focus elsewhere.)
