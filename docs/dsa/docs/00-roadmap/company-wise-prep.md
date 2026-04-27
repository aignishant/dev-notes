# Company-wise prep

> 15+ companies, side by side. What each one tests, weights, and forgives.

This page tells you *what's different* per company. The bible's content is the same — what changes is which sections you weight, which problems you grind, which behavioral angle you emphasize.

---

## Quick reference table

| Company | Coding bar | System design | Behavioral | LP / culture | Time pressure | Communication weight |
|---|---|---|---|---|---|---|
| **Google** | Hard | Senior+ only | Medium | "Googleyness" | Medium | High |
| **Meta** | Hard | E5+ only | Medium-High | "Move Fast" | High | High |
| **Amazon** | Medium-Hard | Senior+ only | Very High | 16 LPs | Medium | High |
| **Microsoft** | Medium | Senior+ only | Medium | Growth mindset | Medium | High |
| **Apple** | Medium-Hard | Domain-specific | Medium | Team-fit | Medium | High |
| **Adobe** | Medium | Sometimes | Medium | "Genuine" | Medium | Medium |
| **Netflix** | Hard (senior bar) | Always | High | "Keeper Test" | Low | Very High |
| **Uber** | Hard | Senior+ always | Medium | "Tech Talent" | Medium-High | High |
| **Flipkart** | Medium-Hard | Senior+ | Medium | Indian product culture | Medium | Medium |
| **Stripe** | Hard (correctness) | Senior+ | High | "Writing culture" | Low (but deep) | Very High |
| **Airbnb** | Medium-Hard | Senior+ | High | "Belong anywhere" | Medium | High |
| **TCS** | Easy-Medium | Rare | High (HR) | Service mindset | Low | Medium |
| **Infosys** | Easy-Medium | Rare | High (HR) | Service mindset | Low | Medium |
| **Wipro** | Easy | Rare | High (HR) | Service mindset | Low | Medium |
| **HCL** | Easy-Medium | Rare | Medium | Service | Low | Medium |
| **ISRO** | Medium (theory) | No | Medium (panel) | Mission-fit | Low | High |
| **DRDO** | Medium (theory) | No | Medium (panel) | Patriotism | Low | High |
| **BARC** | Medium (theory) | No | Medium (panel) | Mission-fit | Low | High |

---

## Product companies (deep-dive)

### Google

**The bar:** "Universally hard problems," graded on signal not just correctness. They want to see *how you think*, not "did you get the answer."

**What they test most:**
- Graphs (BFS/DFS variants), DP, modified binary search
- Tree problems with weird constraints (serialize/deserialize, LCA in N-ary)
- Implementation problems (don't underestimate "messy easy" problems — Google loves them)
- System design at L4+ (every senior loop has 1–2 design rounds)

**Time pressure:** medium. They give you space to think.

**Communication weight:** very high. A correct silent answer scores worse than a partially-correct narrated one.

**What to grind in this bible:**
- All 20 patterns deeply
- DP family (their favorite)
- Graph algorithms — including Dijkstra, topological sort, components
- 2 Tier-1 system design projects
- The "Googleyness" behavioral round (intellectual humility, collaboration)

**What to skip:**
- Heavy memorization of exotic algorithms (they re-derive them with you)
- Pre-canned answers (they smell rehearsal)

**Sample interviewer style:** "Walk me through your thinking before you code. I care about how you arrive there as much as where you arrive."

---

### Meta (Facebook)

**The bar:** "Pattern speed." Six 45-min coding rounds in a day. You need to recognize the pattern in <60 seconds and code in <30 minutes.

**What they test most:**
- BFS / DFS heavily
- Sliding window, two pointers, prefix sums
- LeetCode-style mediums, sometimes hards. Rarely "trick" problems.
- "Find all paths," "minimum X," "longest Y" types

**Time pressure:** high. They expect 2 problems per round (yes, two). Speed is a real signal.

**Communication weight:** high but you need both speed AND clarity.

**What to grind:**
- Top-150 Meta-tagged questions (will be in the Meta page in Phase 8)
- Speed drills — solve a fresh medium in <25 min repeatedly
- The patterns: Tree BFS/DFS, Graph BFS, Sliding Window — Meta loves these

**Behavioral:** "Move Fast" is the cultural anchor. Tell stories about taking calculated risks, shipping fast, recovering from mistakes.

**Sample interviewer style:** "Let's get to the optimal directly if we can. Skip the obvious brute force unless you need it."

---

### Amazon

**The bar:** "Bar-raisers" — one interviewer in your loop is independent and votes solely on whether you'd raise the bar. They lean heavily on Leadership Principles.

**What they test:**
- Coding: medium-hard, 2 rounds
- 1 system design (senior+)
- **3 behavioral / Leadership Principles rounds.** Yes, three. Each round = 2–3 LP-style stories.

**LP weight:** **very high.** You can solve every problem and still fail if your stories don't show LPs.

**The 16 Amazon Leadership Principles you must know:**
1. Customer Obsession
2. Ownership
3. Invent and Simplify
4. Are Right, A Lot
5. Learn and Be Curious
6. Hire and Develop the Best
7. Insist on the Highest Standards
8. Think Big
9. Bias for Action
10. Frugality
11. Earn Trust
12. Dive Deep
13. Have Backbone; Disagree and Commit
14. Deliver Results
15. Strive to be Earth's Best Employer
16. Success and Scale Bring Broad Responsibility

You need **8–10 STAR-format stories** that map to multiple LPs. Each story should hit 2–3 LPs (e.g., "Ownership + Bias for Action + Deliver Results"). The Behavioral section in this bible (Phase 14) will go deep.

**Sample interviewer style:** "Tell me about a time you disagreed with your manager. What did you do? What was the result?"

---

### Microsoft

**The bar:** classic, fair, balanced. They're famous for being well-organized and reasonable.

**What they test:**
- Coding: medium difficulty, classics (linked lists, trees, basic DP, basic graphs)
- 1 system design (senior+)
- 1–2 behavioral rounds (growth mindset + collaboration)
- "AS Appropriate" round — manager fit

**Time pressure:** medium. Problems are not exotic; they let you think.

**What to grind:**
- All 20 patterns at medium depth
- The "Top 50 Microsoft" list (will be in Phase 8)
- 1 Tier-1 system design project
- Growth-mindset behavioral stories (story of a failure + what you learned)

**Sample interviewer style:** "Let's do a couple of problems. Tell me about your approach as you go. No rush."

---

### Apple

**The bar:** **highly team-dependent.** A loop at the iOS Maps team is wildly different from a loop at the Compiler team.

**What they test:**
- Coding: medium-hard, often domain-flavored (graphics? OS? data structures?)
- 1–2 system design rounds (senior+)
- Manager fit + behavioral (less LP-driven, more "how do you collaborate" style)

**Trick:** **research the team you're interviewing with.** Apple recruiters will tell you. The team's domain heavily shapes the questions.

**What to grind:**
- Universal patterns (Apple is fair on classics)
- If you know the team's domain, study its specific patterns (e.g., compiler team → trees, ASTs, DP on intervals)

**Sample interviewer style:** Highly varied. Could be friendly + slow or sharp + Socratic. Expect both.

---

### Adobe

**The bar:** strong on DSA fundamentals + LLD (low-level design / OOP).

**What they test:**
- Coding: medium DSA, 2 rounds
- 1 LLD round (design Parking Lot, Splitwise, etc.)
- 1 manager round
- Sometimes 1 system design (senior+)

**What to grind:**
- All 20 patterns
- LLD section of this bible (Phase 13) — Adobe leans on this
- Object-oriented Python (encapsulation, inheritance, design patterns)

**Sample interviewer style:** "Let's design a parking lot. Start with the entities and their relationships."

---

### Netflix

**The bar:** **senior-only** (Netflix doesn't really hire junior engineers). Bar is high; behavioral is brutal ("Keeper Test").

**What they test:**
- 1–2 coding rounds, but with focus on *correctness, readability, and judgment* — not "did you optimize the last 5%"
- 1–2 system design rounds (always heavy)
- 3+ behavioral rounds — culture deck mastery is mandatory

**Read:** Netflix Culture Deck. Know it. Reference it in answers.

**What to grind:**
- Less raw problems, more depth on a few
- 2–3 Tier-1 system design projects (especially video streaming)
- Behavioral: 8–10 stories that show *judgment* (when you'd disagree, when you wouldn't)

**Sample interviewer style:** "Tell me about a time you made a decision your team disagreed with."

---

### Uber

**The bar:** very high, especially on system design and concurrency.

**What they test:**
- 2 coding rounds, often with multi-threading or concurrency twists
- 1–2 system design rounds — they LOVE Uber-style problems (matchmaking, location, fleet management)
- 1 behavioral round

**What to grind:**
- All 20 patterns
- Concurrency (Python `threading`, `asyncio`, locks, deadlocks)
- 2 Tier-1 system design projects (Uber is one of them — read it deeply)

---

### Flipkart, Swiggy, Zomato (Indian product unicorns)

**The bar:** medium-hard DSA + system design. Less time pressure than US product companies.

**What they test:**
- Coding: 2 rounds, medium-hard
- 1–2 system design rounds (senior+)
- 1 behavioral / managerial round

**What to grind:**
- All 20 patterns
- 2 Tier-1 system design projects (URL shortener + a domain-relevant one — food delivery for Swiggy, e-commerce for Flipkart)
- Indian-product-context stories (scale, payments, regional languages)

---

### Stripe, Airbnb, others (smaller US product)

**The bar:** correctness over speed. Code review style.

**What they test:**
- 1–2 coding rounds with **emphasis on production-quality code**
- 1–2 system design rounds (senior+ always)
- 1–2 behavioral rounds — communication is heavily weighted

**What to grind:**
- Edge cases, input validation, type hints, docstrings
- Stripe specifically: writing samples / async problem-solving questions
- 2 Tier-1 system design projects

---

## Service companies (TCS, Infosys, Wipro, HCL, Cognizant, Capgemini, Accenture, Tech Mahindra…)

**The bar:** **basic competence + good communication.** They hire in volume and train on the job.

**What they test:**
- Aptitude (logic, math) — separate online round
- Coding: 1–2 questions, easy-medium (string manipulation, basic DSA)
- Technical Q&A — basics of OOP, DBMS, OS, networks (theory-heavy)
- HR round — "Why us?", "5-year plan", communication, attitude

**What to grind:**
- The 20 patterns at medium level (no need to grind hards)
- CS fundamentals (OOP, DBMS, OS, CN — Phase 14 of this bible)
- HR round prep (the "Why us?" and "Why service company over product?" questions)

**What NOT to do:**
- Don't quote your LeetCode count. They don't care.
- Don't show off advanced topics. Focus on clarity.

**Sample question style:**
- "Reverse a linked list" (literally)
- "What's normalization in DBMS?"
- "Tell me about yourself in 2 minutes."

---

## PSU companies (ISRO, DRDO, BARC, ECIL, BEL, HAL, BHEL…)

**The bar:** **theory mastery + panel poise.**

**What they test:**
- Written exam (GATE-style or company-specific) on CS fundamentals + DSA
- **Panel interview** with 4–6 senior scientists
- Theory-heavy: OS, DBMS, Computer Networks, Compilers, Computer Architecture
- Some basic DSA, often pseudocode rather than running code
- Project / final-year work deep-dive
- "Why this organization?" — patriotism / mission angle matters here

**What to grind:**
- GATE syllabus level CS theory
- Phase 14 CS fundamentals section (this bible)
- Final-year project — be ready for a 30-min deep-dive on it
- The 20 patterns at basic level

**Behavioral angle:** very different from product/service. Emphasize:
- Long-term commitment (PSU = career, not stepping stone)
- Mission alignment ("I want to contribute to ISRO's missions")
- Ability to work in panel-style hierarchy

**Sample interviewer style:** "Explain virtual memory. Go." Then: "Now explain page fault handling on Linux." Then: "Why do you want to join ISRO?"

---

## How to read this page

When you've picked your target, read **only that company's section** carefully. Then customize your study plan:

- Heavy LP-weight company (Amazon)? Add behavioral story-building from week 1, not week 10.
- Speed-heavy (Meta)? Add timed drills daily.
- Theory-heavy (PSU)? Add a daily 30-min CS-fundamentals review.
- LLD-heavy (Adobe)? Read the LLD section (Phase 13) along with DSA.

If you're interviewing at multiple companies in different categories, **prep for the strictest** — it covers the others.

→ [Product vs Service vs PSU strategy](product-vs-service-vs-psu-strategy.md) — the three cultures, deeper.
