# How to use this bible

> The owner's manual. 10 minutes here saves 10 weeks later.

---

## TL;DR

1. **Pick a plan** in [Pick your study plan](pick-your-plan.md). Commit to it.
2. **Read [How to approach any problem](how-to-approach-any-problem.md)** — the 7-step framework you'll use forever.
3. **Build foundations** in the [Foundations](../01-foundations/index.md) section. Don't skip.
4. **Topic → problems → repeat.** For each topic, read the chapter, then solve its problems in order.
5. **Mock yourself** at the end of every week. Be honest.

That's the whole strategy. The rest of this page explains the *how*.

---

## The 5 ways to use this bible

Different people learn differently. Pick the way that fits.

### Way 1 — Plan-driven (recommended for most)

You pick a study plan (3 weeks → 6 months) and follow it day by day. The plan tells you which page to read and which problems to solve each day. **No decisions to make.** Just show up.

> Best for: beginners, busy people, anyone who freezes when given choices.

### Way 2 — Topic-driven

You pick a topic (say, "linked lists") and grind it from chapter intro through every problem before moving on.

> Best for: people who like to *finish* something before starting the next.

### Way 3 — Pattern-driven

You skip topics and instead cycle through the 20 [Patterns](../04-patterns/index.md) — each pattern's page collects problems from many topics that share the same trick.

> Best for: people preparing for a specific company that asks pattern-heavy interviews (Meta, Amazon).

### Way 4 — Company-driven

You go straight to your target company's page in [Popular Problems](../07-popular-problems/index.md) and grind those.

> Best for: a deadline. Risky if your foundations are weak — the company set assumes you already know the basics.

### Way 5 — Mock-driven

You read just enough theory to be dangerous, then book mock interviews and let the gaps tell you what to study next.

> Best for: experienced engineers who already know the theory and need *interview practice*, not learning.

---

## How to read a topic chapter

Every topic chapter has the same 12-part shape. Read the parts you need; skim the ones you already know.

| Section | What it gives you | Skip if… |
|---|---|---|
| 1. What is this? | Plain-English explanation + analogy | Never. Always read this. |
| 2. Why do we need this? | The real-world reasons | You're already convinced |
| 3. How it works internally | Diagrams + memory layout | You truly understand it |
| 4. Python implementation | Built from scratch | You can implement it sleeping |
| 5. Complexity table | Big-O for every operation | Never. Always glance. |
| 6. Built-in tools | Which Python builtins to use | You memorized them |
| 7. When to use vs when NOT | Decision rules | You always pick correctly |
| 8. Common mistakes | Bugs people make | Never. Always read. |
| 9. Patterns this connects to | The bigger picture | Cross-references for later |
| 10. Practice problems | The 40+ problems | **Never skip — this is the work** |
| 11. How interviewers ask | Phrasing patterns | You've done 50+ mocks |
| 12. Self-check quiz | 10–20 yes/no questions | Never. Use it to confirm you got it. |

**The order matters.** Read 1 → 5, then jump straight to problems (10). Come back to 6, 7, 8, 11 after you've struggled with a few problems — they'll make 10× more sense.

---

## How to read a problem page

Every problem has the same shape too. Resist the urge to scroll straight to the code.

!!! tip "The right reading order"
    1. **Read the problem statement.** Don't read the solution yet.
    2. **Try it yourself for 20 minutes.** Even if you don't finish, you've earned the right to read the solution.
    3. **Read 📖 Story Mode** to confirm you understood the problem.
    4. **Read 🌍 Real-World Usage** so you know why this matters.
    5. **Read 🧠 Thinking Process** — this is the most important section. It teaches you how to *arrive at* the solution, not just memorize it.
    6. **Read 🐍 Layer 1 (brute force).** Try to predict the time complexity *before* it tells you.
    7. **Read 🐍 Layer 2 (optimized).** Pause at every line. Why this line?
    8. **Run 🔍 Dry Run in your head** with the example.
    9. **Cover the screen and re-implement Layer 2 from scratch.** Don't peek.
    10. **Check 🐛 Common Bugs.** Did you hit any?
    11. **Check ✅ Edge Cases Checklist.** Mentally answer "yes I handle this" for each.
    12. **Try 🔄 Interviewer Follow-ups.** Each one is a free practice problem.

That's the full loop. About 30–60 minutes per problem the first time. Speeds up to 10–15 minutes once you're in flow.

---

## What to do when you're stuck

The "rescue ladder" — climb only as far as you need.

> 🪜 **Rung 1 (5 min):** Re-read the problem. Underline numbers and constraints. **80% of "stuck" is misreading.**
>
> 🪜 **Rung 2 (10 min):** Walk through a tiny example by hand on paper. Use n=3 or n=4. Don't try to think in general; just *do* it for one case.
>
> 🪜 **Rung 3 (5 min):** Read just the 📖 Story Mode and 🌍 Real-World Usage of the problem. Sometimes a real-world frame unlocks the abstract puzzle.
>
> 🪜 **Rung 4 (5 min):** Read 🧠 Thinking Process **only up to the brute-force idea**. Stop. Try to code the brute force yourself.
>
> 🪜 **Rung 5 (5 min):** Read up through "Why is brute force slow?" Stop. Think about where it wastes work.
>
> 🪜 **Rung 6:** Read the optimized solution, then close the page and re-derive it from memory.

If you climbed all six rungs and still don't get it, **mark the problem ⏸️ "park"** and move on. Come back tomorrow. Sleep is an algorithm.

---

## Active recall — the only study hack that matters

Reading is not studying. **Reading is studying when you can close the book and reproduce what you read.** That's active recall.

After every problem, try to answer (without peeking):

- What was the brute force? Why was it slow?
- What was the insight that made it fast?
- What pattern was it?
- What's a problem that uses the same pattern?
- What edge cases would I check?

If you can't, you didn't learn it. Read it again.

---

## How to track progress

Use [Progress tracker](progress-tracker.md). Three numbers matter:

1. **Topics covered** (out of ~50)
2. **Problems solved** (count solved without peeking)
3. **Mock interviews done** (with self-grading)

Review weekly. Adjust your plan if you're consistently behind or ahead.

---

## How to come back after a break

A week off? A month? No problem. Don't try to "catch up" by skipping ahead.

**The 3-day comeback ritual:**

- **Day 1:** Re-read the [Big-O cheatsheet](../01-foundations/big-o-cheatsheet.md). Re-solve any 5 problems you marked ⏸️ park.
- **Day 2:** Re-read the last topic chapter you finished. Re-solve any 5 of its problems from memory.
- **Day 3:** One mock interview from the [Mock Interviews](../10-mock-interviews/index.md) section. Honestly grade yourself. Resume your plan from where you left off.

The bible is patient. It'll be here whenever you come back.

---

## How NOT to use this bible

> ❌ **Don't** read solutions before attempting. You waste the value of the problem.
>
> ❌ **Don't** memorize code. Memorize *patterns*. Code follows.
>
> ❌ **Don't** grind 200 problems on one topic. Spread the load — 5 problems × 10 topics > 50 problems × 1 topic.
>
> ❌ **Don't** skip Foundations. You'll move 3× slower in every later section.
>
> ❌ **Don't** chase "hard" problems too early. Easy → Medium → Hard, in that order.
>
> ❌ **Don't** binge-read without coding. Reading 3 chapters and solving 0 problems is procrastination dressed as productivity.

---

## Frequently asked

??? question "I've been at it for 3 days and feel I'm forgetting yesterday's stuff. Normal?"
    Yes. Use the **next-day repeat rule**: at the start of every study day, re-solve 1–2 problems from the previous day **from memory**, before starting new content. Forgetting is part of the loop. The repeat rule is what converts "forgot" into "owned."

??? question "Do I need to do all 5,000 problems?"
    No. Most people who land top offers solve 300–500 problems carefully, not 5,000 sloppily. The bible has 5,000+ so you have *choice* and *coverage*, not because you must do them all.

??? question "Should I use this with LeetCode?"
    Yes. The bible explains. LeetCode is where you *type and submit*. Code in the bible isn't a substitute for muscle memory at the keyboard.

??? question "Do I need to know advanced stuff for service-company interviews?"
    No. Service-company interviews focus on basics + clarity. See [Product vs Service vs PSU strategy](product-vs-service-vs-psu-strategy.md).

??? question "I solved a problem differently from the bible. Is that wrong?"
    Almost certainly not — it's great. Multiple correct solutions is a sign of understanding. Just check that your complexity matches or beats the bible's.

??? question "Should I write code by hand on paper?"
    Once a week, yes. It exposes whether you actually know the syntax or are leaning on autocomplete.

---

## Up next

→ [Pick your study plan](pick-your-plan.md) — choose your timeline before doing anything else.
