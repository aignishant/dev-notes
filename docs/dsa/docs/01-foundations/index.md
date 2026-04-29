# 🐍 Foundations

> Python + complexity. Skip this and everything else takes 3× longer.

<span class="phase-status phase-done">Phase 1 — Foundations</span>

These are the building blocks. Whether you're a complete beginner or have been coding for years, **at least skim each page** — interviewers test the small details (slicing, mutation, complexity vocabulary) more often than they test "the algorithm." A senior with sloppy Python loses to a junior with crisp Python.

---

## 🐍 Python for interviews

<div class="grid cards" markdown>

-   :material-language-python: **[Python crash course for DSA](python-crash-course-for-dsa.md)**

    ---

    The Python you actually need to know — variables, lists, dicts, sets, tuples, functions, classes, slicing, comprehensions, mutation traps. Skip if you've shipped a Python service; otherwise this is non-negotiable.

-   :material-flash: **[Python tricks for interviews](python-tricks-for-interviews.md)** <span class="difficulty medium">High-leverage</span>

    ---

    `Counter`, `defaultdict`, `heapq`, `bisect` — the four objects that win interviews. Plus `sorted(key=…)`, tuple sorting, `enumerate`, `zip`, walrus, f-strings, and the *one* `lru_cache` line that saves a DP problem.

-   :material-toolbox: **[Python STL deep-dive](python-stl-deep-dive.md)**

    ---

    `collections`, `itertools`, `functools`, `operator`. The complete guided tour. Every primitive an interviewer expects you to recall in under five seconds.

-   :material-keyboard-outline: **[Input/output handling](input-output-handling.md)** <span class="difficulty hard">OA-critical</span>

    ---

    `input()`, `sys.stdin.readline`, fast IO templates, parsing space-separated ints, multi-line graphs. **Crucial for online assessments** — you will time-out without this even if your algorithm is right.

</div>

---

## ⏱️ Complexity — speak the interviewer's language

<div class="grid cards" markdown>

-   :material-clock-fast: **[Time complexity explained](time-complexity-explained.md)**

    ---

    Big-O without the math degree. How to count loops, recursion trees, amortisation, and why O(n log n) beats O(n²) the moment n hits a few thousand.

-   :material-database-outline: **[Space complexity explained](space-complexity-explained.md)**

    ---

    What "in-place" *actually* means and why interviewers care. Stack space vs heap space, recursion depth, the auxiliary-space trap, and the in-place techniques that flip O(n) → O(1).

-   :material-clipboard-list-outline: **[Big-O cheatsheet](big-o-cheatsheet.md)**

    ---

    One-page complexity reference. Every common operation across `list`, `dict`, `set`, `deque`, `heapq`, `bisect`, plus the "common mistakes" column you'll be quizzed on.

</div>

---

## 🧠 Mindset & craft

<div class="grid cards" markdown>

-   :material-brain: **[How to think recursively](how-to-think-recursively.md)**

    ---

    The mindset, the template, the common bugs. Why "trust the recursion" is the most underrated three-word lesson in DSA. Comes with a five-step recipe and the off-by-one traps that bite everyone.

-   :material-pencil-box-outline: **[The dry-run method](dry-run-method.md)** <span class="difficulty medium">Trust-builder</span>

    ---

    How to debug code on paper before you submit. The two-column dry-run table, the "small + adversarial" example pair, and how dry-running turns a panicked guess into a confident submission.

-   :material-star-shooting: **[Code quality for interviews](code-quality-for-interviews.md)**

    ---

    What an interviewer is grading besides correctness. Naming, micro-structure, edge-case handling, and the difference between "it works" and "I'd hire this person."

</div>

---

## ✅ Recommended reading order

If you have **2–3 hours**:

1. [Python crash course for DSA](python-crash-course-for-dsa.md)
2. [Python tricks for interviews](python-tricks-for-interviews.md)
3. [Big-O cheatsheet](big-o-cheatsheet.md)
4. [How to approach any problem](../00-roadmap/how-to-approach-any-problem.md) (back in Roadmap)

You're ready to start **[Data Structures](../02-data-structures/index.md)**.

If you have **a full day**, read every page in this section. You will not regret it. The "boring" pages — `input-output-handling.md`, `code-quality-for-interviews.md`, `dry-run-method.md` — are the ones that tip a borderline candidate into a hire.
