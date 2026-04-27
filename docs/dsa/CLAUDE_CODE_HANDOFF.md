# 🚀 CLAUDE CODE HANDOFF — DSA & System Design Bible

---

## 📋 INSTRUCTIONS FOR YOU (the user) — read this first

1. **Install Claude Code** (terminal version OR VS Code extension — pick what's comfortable)
2. **Create an empty folder** somewhere on your computer:
   ```bash
   mkdir ~/dsa-bible
   cd ~/dsa-bible
   ```
3. **Copy these two files** into that folder:
   - `IMPLEMENTATION_PLAN_v3.md` (the master spec we built)
   - `CLAUDE_CODE_HANDOFF.md` (this file)
4. **Open Claude Code** in that folder
5. **Paste the message below** (everything between the `---START---` and `---END---` markers) as your very first message to Claude Code
6. **Let it run.** It will set up the project, build Phase 1, and tell you how to run the site.

---

## ⬇️ COPY EVERYTHING BELOW THIS LINE INTO CLAUDE CODE ⬇️

---START---

# Mission

You are building a comprehensive **DSA (Data Structures & Algorithms) and System Design Bible** as an MkDocs site. This is a multi-phase project. Your job is to execute it phase by phase, starting with **Phase 1** today.

# Background about me (the user)

- **Skill level:** Beginner. I know basic Python but I am NOT a strong developer yet.
- **Goal:** Crack interviews at product companies (Google, Meta, Amazon, Microsoft, Adobe, Apple, Netflix, Uber, Flipkart, etc.), Indian service companies (TCS, Infosys, Wipro, HCL, Cognizant, etc.), AND Indian PSU/government (ISRO, DRDO, BARC, etc.).
- **Preferred language:** Python.
- **Communication style:** Use simple language. Explain every small thing. I get lost in jargon.
- **What I want from this project:** When the bible is done, I should NOT need any other book, course, or YouTube video to crack these interviews.

# The full project spec

Read the file **`IMPLEMENTATION_PLAN_v3.md`** in this folder. **Read it completely before doing anything else.** It contains:

- Full 14-phase delivery plan
- Site structure (~355 pages, 5,000+ problems)
- Format for every type of page (data structure topics, problems, system design projects, etc.)
- Quality bar I expect

That file is the contract. Follow it.

# Phase 1 — what to deliver TODAY

Phase 1 is the foundation. It must be high-quality because every later phase will copy this format.

**Phase 1 deliverables:**

1. **Project setup**
   - `mkdocs.yml` with Material theme, all needed plugins (mermaid, search, content-tabs, admonitions, MathJax)
   - `requirements.txt` listing all Python packages
   - `README.md` explaining the project
   - `.gitignore` for Python/MkDocs
   - Initialize git repo
   - Folder structure for all 14 sections (even empty placeholders, so the nav skeleton works)

2. **Welcome page**
   - `docs/index.md` — clear "how to use this bible" page

3. **Complete Section 00 — Roadmap (planner)**
   - `docs/00-roadmap/how-to-use-this-doc.md`
   - `docs/00-roadmap/pick-your-plan.md` (decision tree across the 6 plans)
   - `docs/00-roadmap/3-week-sprint-plan.md`
   - `docs/00-roadmap/5-week-balanced-plan.md`
   - `docs/00-roadmap/6-week-thorough-plan.md`
   - `docs/00-roadmap/1-month-crash-plan.md`
   - `docs/00-roadmap/3-month-fast-track.md`
   - `docs/00-roadmap/6-month-study-plan.md`
   - `docs/00-roadmap/daily-routine.md`
   - `docs/00-roadmap/how-to-approach-any-problem.md` (the 7-step framework)
   - `docs/00-roadmap/company-wise-prep.md` (Google vs Meta vs Amazon vs Adobe vs Microsoft vs TCS vs ISRO etc.)
   - `docs/00-roadmap/product-vs-service-vs-psu-strategy.md`
   - `docs/00-roadmap/interview-stages-explained.md`
   - `docs/00-roadmap/progress-tracker.md`

4. **Complete Section 01 — Foundations**
   - `docs/01-foundations/python-crash-course-for-dsa.md`
   - `docs/01-foundations/python-tricks-for-interviews.md` (Counter, defaultdict, heapq, bisect)
   - `docs/01-foundations/python-stl-deep-dive.md` (collections, itertools, functools, operator)
   - `docs/01-foundations/time-complexity-explained.md`
   - `docs/01-foundations/space-complexity-explained.md`
   - `docs/01-foundations/big-o-cheatsheet.md`
   - `docs/01-foundations/how-to-think-recursively.md`
   - `docs/01-foundations/input-output-handling.md`
   - `docs/01-foundations/code-quality-for-interviews.md`
   - `docs/01-foundations/dry-run-method.md`

5. **The gold-standard sample chapter** (CRITICAL — this is the template for everything that follows)
   - `docs/02-data-structures/arrays/01-array-basics.md`
   - This single file should contain ALL of:
     - The 12-part topic page format from IMPLEMENTATION_PLAN_v3.md
     - 40+ problems (10 easy, 15 medium, 10 hard, 10 product-based-asked, 5 service/PSU-asked)
     - Every problem in the full v3 progressive 5-layer solution format
     - Every problem with line-by-line code explanation
     - Every problem with 🌍 Real-World Usage section
     - Every problem with 3-5 incremental interviewer follow-ups (each fully solved)
     - Every problem tagged with companies that asked it
   - This file will be LONG (likely 20,000-40,000 words). That's expected. Do not shortcut it.

6. **One sample company page**
   - `docs/07-popular-problems/product-based/google-50.md`
   - Show the format for company-specific pages — don't need all 50 problems written out, just a complete representative sample (10-15 problems) with full v3-format solutions, plus the page structure (intro, interview style at this company, common patterns, etc.)

7. **One sample common-across page**
   - `docs/12-common-across-all-companies/02-arrays-common.md`
   - Same idea — show the format with 10-15 representative common-across-companies array problems.

# Quality bar — non-negotiable

For **every single problem** you write, you must include:

```
PROBLEM: <name>
ASKED AT: 🏷️ <list of companies>
PATTERN: 🎯 <pattern>
DIFFICULTY: 🟢/🟡/🔴

📖 Story Mode (explain like I'm 5)
🌍 Real-World Usage (where this matters in production — be specific with industries/products)
🧠 Thinking Process (brute force → why slow → insight → optimal)

🐍 Solution in 5 Layers:
  Layer 1: Brute Force (every line of code explained on a separate line below it)
  Layer 2: Optimized (every line explained)
  Layer 3: Edge Cases Handled
  Layer 4: Production-Ready (input validation, type hints, docstrings)
  Layer 5: Variants Interviewers Ask

🔍 Dry Run (walk through 1 example step by step)
⏱️ Complexity Analysis (time + space + WHY)
🎯 Pattern Used
🔄 Interviewer Follow-ups (3-5 progressive variants, each fully solved)
🐛 Common Bugs
✅ Edge Cases Checklist
🏢 Sample Interviewer Quote
```

For **every topic page** (like array-basics.md), you must include the 12-part structure from the v3 plan:
1. What is this? (plain English + analogy)
2. Why do we need this?
3. How it works internally (with diagrams)
4. Python implementation from scratch
5. Time & space complexity table
6. Built-in Python tools to use
7. When to use vs when NOT to use
8. Common mistakes & gotchas
9. Patterns this connects to
10. Practice problems (40+ in v3 format)
11. How interviewers ask this
12. Self-check quiz

# Tone rules

- **Simple language.** I'm a beginner. No jargon without explanation.
- **Short sentences.** Long ones lose me.
- **Real-world analogies first**, then the technical detail.
- **Show, don't just tell.** Code with comments beats prose.
- **Be patient.** Assume I don't know what a hash table is the first time I read about it.

# Tech stack to use

- **MkDocs** with **mkdocs-material** theme
- Plugins: `pymdown-extensions` (admonitions, tabs, code highlighting), `mkdocs-material` (search, navigation), `mermaid2-plugin` (diagrams), MathJax for any math
- Python 3.10+
- All code samples in Python
- Markdown for all content
- Mermaid for diagrams (text-based, renders in browser)

# Working style — how I want you to operate

1. **Read `IMPLEMENTATION_PLAN_v3.md` fully first.** Confirm you've read it before starting work.
2. **Plan Phase 1 with me before executing.** Show me the file list you intend to create and any decisions you're making (e.g. plugin choice, theme color). Wait for my "go" before writing files.
3. **Work in batches.** Don't try to write all of Phase 1 in one go without checkpoints. After major batches (e.g., setup done, roadmap done, foundations done, sample chapter done), pause and tell me what's next.
4. **Set up a way for me to verify as you go.** After project setup, tell me how to run `mkdocs serve` and what URL to open. After each batch, tell me what new pages I can browse.
5. **If something is unclear, ASK.** Don't guess on important decisions. Examples: theme color, plugin choices, sample problem selection, depth trade-offs.
6. **If a tool is missing on my machine** (Python, pip, mkdocs, git), walk me through installing it patiently — I'm a beginner.
7. **Estimate honestly.** If something will be huge, tell me before starting so I can decide to break it up.
8. **Commit to git** at meaningful checkpoints with clear commit messages.

# What "Phase 1 done" looks like

- I can run `mkdocs serve` in the project folder
- The site loads at `http://127.0.0.1:8000`
- The sidebar shows all 14 sections (some empty for later phases — that's fine)
- The Roadmap section is fully readable with all 6 study plans
- The Foundations section is fully readable
- The sample Arrays chapter is fully readable with all 40+ problems and v3-format solutions
- The sample Google-50 page and arrays-common page are readable
- Everything looks polished — Material theme, working search, clean nav
- Git repo has clean commit history
- I can confidently say "yes, this quality scales — let's continue to Phase 2"

# After Phase 1

Wait for my review and approval. Don't start Phase 2 until I say so. I'll either:
- ✅ "Looks great, continue with Phase 2" → you start Phase 2
- 🔁 "Change X, Y, Z first" → you fix and re-show
- 🛑 "Pause, I want to tweak the plan" → you wait

# Start now

Begin by:
1. Reading `IMPLEMENTATION_PLAN_v3.md`
2. Confirming what you've read
3. Showing me your Phase 1 execution plan (file list + key decisions)
4. Asking me any blockers
5. Waiting for my "go"

Then build.

---END---

## 📌 After you paste the above into Claude Code

Claude Code will:
1. Read the v3 plan file
2. Confirm understanding
3. Show you its Phase 1 execution plan
4. Ask any clarifying questions (theme color, etc.)
5. Wait for your "go"
6. Build Phase 1
7. Tell you how to run the site

**Your job during this:**
- Answer its clarifying questions (it'll ask 2-5 things)
- Run any setup commands it tells you (it'll walk you through)
- Open the local site at `http://127.0.0.1:8000` when it says it's ready
- Review the sample Arrays chapter — that's your quality validation
- Say "looks great, continue" → it goes to Phase 2

## 🆘 Troubleshooting

If Claude Code can't proceed because of missing tools:

| Problem | Fix |
|---|---|
| Python not installed | Install Python 3.10+ from python.org |
| pip not working | `python -m ensurepip --upgrade` |
| `mkdocs: command not found` | `pip install mkdocs mkdocs-material pymdown-extensions mkdocs-mermaid2-plugin` |
| Git not installed | Install from git-scm.com |
| Port 8000 already in use | `mkdocs serve -a 127.0.0.1:8001` |

If Claude Code's output doesn't match the v3 quality bar:
- Tell it: "This doesn't match the v3 spec — see [section]. Redo it with the full progressive 5-layer format."

If you want to pause and adjust scope mid-phase:
- Just say: "Pause. I want to change X."

## 🎯 Coming back here

Once your bible is being built (or even partially built), come back to this chat for:
- **Mock interviews** (I'll act as a Google/Meta/etc. interviewer and grill you)
- **Concept re-explanations** ("explain Dijkstra in even simpler words")
- **Code review** of your own attempts ("here's my solution to <problem>, what's wrong?")
- **Daily study questions** ("give me 3 array problems to do today")
- **Topic deep-dives** ("teach me segment trees from scratch")
- **Progress check-ins** ("I've done X, what should I do next?")

Good luck — go build the bible. 🚀
