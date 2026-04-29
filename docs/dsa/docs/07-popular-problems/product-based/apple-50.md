# Apple — 50 most-asked questions

> The 50 problems Apple has asked most often, with the patterns behind them and what the interviewer is grading. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">Apple</span> &nbsp; <span class="phase-status phase-inprogress">Phase 8 — company page</span>

---

## 📖 How this page is organized

1. **What interviewing here is like** — rounds, format, signal, vibe.
2. **What this company tests** — the specific skills they grade for.
3. **Common patterns** — which of the 20 patterns show up most often.
4. **The 50 questions** — grouped by topic.
5. **Deep-dives** — 3 representative problems in mini-v3 format.
6. **Day-of tips**.

---

## 🏢 What interviewing at Apple is like

### Rounds (typical SWE ICT3-ICT4 onsite — 2026)

| Round | Length | Focus |
|---|---|---|
| **Recruiter screen** | 30 min | Background + team match. **Apple is highly team-specific.** |
| **Hiring manager** | 45 min | Project deep-dive + culture fit. |
| **Tech screen** | 60 min | One coding problem + a domain-specific question (Swift / iOS / kernel / metal — depends on team). |
| **Onsite — coding ×2** | 60 min each | Algorithms + data structures. |
| **Onsite — domain ×2** | 60 min each | Team-specific: iOS APIs, Swift internals, GPU shaders, audio DSP, Bluetooth, etc. |
| **Onsite — system design** | 60 min | ICT4+. Often "design a feature in iOS" rather than abstract scale. |

### What "the Apple style" actually means

- **Team-first hiring.** You don't interview "for Apple" — you interview for **a specific team**. Each team has its own rubric.
- **Quiet but rigorous.** Interviewers are typically calm, sometimes terse. Don't read silence as boredom.
- **Domain knowledge weighs heavily.** If you're applying to the camera team, expect to discuss image-pipeline tradeoffs. If applying to the kernel team, expect threading + memory-model questions.
- **Privacy-aware framing.** Apple loves problems framed in terms of "compute this *without* sending data to the server." Differential privacy, on-device ML, local-only solutions score.
- **"How would this feel for the user?"** — UX is part of the answer even on backend rounds.

!!! tip "The Apple interviewer mindset"
    Apple interviewers ask: *"Does this person care about **the craft**?"* They want to see attention to detail — clean variable names, thoughtful edge cases, considered tradeoffs. Sloppy code reads as "doesn't care," which is fatal at Apple.

---

## 🎯 What Apple tests

| Signal | Where they grade it | How to show it |
|---|---|---|
| **Coding quality** | All coding rounds | Clean, well-named, thoughtfully tested code. Not just correct — *crafted*. |
| **Domain depth** | Domain rounds | Know your team's stack. iOS team? Know the run-loop. Kernel team? Know mach-threads. |
| **Tradeoff thinking** | Every round | "Latency vs battery" / "memory vs compute" — Apple cares about *physical* constraints. |
| **User empathy** | System design + behavioral | "Why is this better for the user?" must be answerable for every choice. |
| **Privacy mindset** | Many rounds | Prefer on-device + privacy-preserving computation when applicable. |
| **Curiosity** | Hiring manager + culture | Ask thoughtful questions about the team, the product, the constraints. |

---

## 🧩 Patterns that show up most often

| Pattern | Frequency | Why Apple likes it |
|---|---|---|
| **Trees & recursion** | ⭐⭐⭐⭐⭐ | Classic Apple algorithmic territory. |
| **Two pointers** | ⭐⭐⭐⭐ | Strings, arrays, in-place transformations. |
| **Hash map + sliding window** | ⭐⭐⭐⭐ | Standard medium filter. |
| **Linked list manipulation** | ⭐⭐⭐⭐ | Reversals, merges, intersection. |
| **DP** | ⭐⭐⭐⭐ | 1D + 2D classics. |
| **Bit manipulation** | ⭐⭐⭐ | Embedded/kernel teams especially. |
| **Stacks / monotonic stack** | ⭐⭐⭐ | Histogram, parsing. |
| **Graphs (BFS/DFS)** | ⭐⭐⭐ | Less than Google, but still common. |
| **OOP design** | ⭐⭐⭐ | One round will likely be "design X for iOS". |
| **Concurrency primitives** | ⭐⭐⭐ | If the team is system-flavored. GCD, async/await, locks. |

---

## 📋 The 50 questions

Status: ✅ = full v3 in this bible &nbsp; 📝 = mini-v3 below &nbsp; 🚧 = lands later in Phase 8.

### Arrays & strings (12)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash map | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Best Time to Buy and Sell Stock | <span class="diff-easy">Easy</span> | Running min | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 3 | Maximum Subarray (Kadane's) | <span class="diff-medium">Medium</span> | DP | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 4 | Container With Most Water | <span class="diff-medium">Medium</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 5 | 3Sum | <span class="diff-medium">Medium</span> | Sort + two ptrs | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 6 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 7 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 8 | Longest Palindromic Substring | <span class="diff-medium">Medium</span> | Expand-around-center | 🚧 |
| 9 | Group Anagrams | <span class="diff-medium">Medium</span> | Hash + sorted-key | 🚧 |
| 10 | First Unique Character in a String | <span class="diff-easy">Easy</span> | Hash count + scan | 🚧 |
| 11 | Compare Version Numbers | <span class="diff-medium">Medium</span> | Tokenize + compare | 🚧 |
| 12 | Text Justification | <span class="diff-hard">Hard</span> | Greedy line break | 🚧 |

### Linked lists (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 13 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 14 | Merge Two Sorted Lists | <span class="diff-easy">Easy</span> | Two pointers | 🚧 |
| 15 | Reorder List | <span class="diff-medium">Medium</span> | Mid + reverse + merge | 🚧 |
| 16 | Linked List Cycle | <span class="diff-easy">Easy</span> | Floyd's | 🚧 |
| 17 | Reverse Nodes in k-Group | <span class="diff-hard">Hard</span> | In-place segments | 🚧 |

### Trees (8)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 18 | Validate BST | <span class="diff-medium">Medium</span> | DFS + bounds | 🚧 |
| 19 | Binary Tree Level Order Traversal | <span class="diff-medium">Medium</span> | BFS | 🚧 |
| 20 | Binary Tree Zigzag Level Order Traversal | <span class="diff-medium">Medium</span> | BFS + reverse | 🚧 |
| 21 | Binary Tree Maximum Path Sum | <span class="diff-hard">Hard</span> | DFS post-order | 🚧 |
| 22 | Symmetric Tree | <span class="diff-easy">Easy</span> | Recursive mirror | 🚧 |
| 23 | Invert Binary Tree | <span class="diff-easy">Easy</span> | DFS | 🚧 |
| 24 | Lowest Common Ancestor (Binary Tree) | <span class="diff-medium">Medium</span> | DFS post-order | 🚧 |
| 25 | Construct Tree from Preorder + Inorder | <span class="diff-medium">Medium</span> | Recursive partition | 🚧 |

### Graphs (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 26 | Number of Islands | <span class="diff-medium">Medium</span> | Grid BFS/DFS | 🚧 |
| 27 | Course Schedule | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 28 | Word Ladder | <span class="diff-hard">Hard</span> | BFS on word graph | 🚧 |

### DP (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 29 | Climbing Stairs | <span class="diff-easy">Easy</span> | 1D DP | 🚧 |
| 30 | Coin Change | <span class="diff-medium">Medium</span> | Unbounded knapsack | 🚧 |
| 31 | Word Break | <span class="diff-medium">Medium</span> | DP + dictionary | 🚧 |
| 32 | Edit Distance | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |
| 33 | Decode Ways | <span class="diff-medium">Medium</span> | 1D DP | 🚧 |

### Stacks (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 34 | Valid Parentheses | <span class="diff-easy">Easy</span> | Stack | 🚧 |
| 35 | Daily Temperatures | <span class="diff-medium">Medium</span> | Monotonic stack | 🚧 |
| 36 | Largest Rectangle in Histogram | <span class="diff-hard">Hard</span> | Monotonic stack | [📝](#deep-dive-2-largest-rectangle-in-histogram) |

### Bit & math (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 37 | Single Number | <span class="diff-easy">Easy</span> | XOR | [✅](../../04-patterns/20-bitwise-xor.md) |
| 38 | Number of 1 Bits | <span class="diff-easy">Easy</span> | n & (n-1) | 🚧 |
| 39 | Reverse Integer | <span class="diff-medium">Medium</span> | Math + overflow | 🚧 |
| 40 | Pow(x, n) | <span class="diff-medium">Medium</span> | Fast exponentiation | 🚧 |
| 41 | Sqrt(x) | <span class="diff-easy">Easy</span> | Binary search | 🚧 |

### Backtracking (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 42 | Permutations | <span class="diff-medium">Medium</span> | Backtracking + swap | 🚧 |
| 43 | Subsets | <span class="diff-medium">Medium</span> | Backtracking | 🚧 |
| 44 | Letter Combinations of a Phone Number | <span class="diff-medium">Medium</span> | Backtracking | 🚧 |

### Heap & search (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 45 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap / bucket sort | 🚧 |
| 46 | Find K Closest Elements | <span class="diff-medium">Medium</span> | Two pointers / binary search | 🚧 |
| 47 | Median of Two Sorted Arrays | <span class="diff-hard">Hard</span> | Binary search on partition | [✅](../../02-data-structures/arrays/01-array-basics.md) |

### Concurrency / design (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 48 | Print in Order (LC 1114) | <span class="diff-easy">Easy</span> | Semaphore / event | [📝](#deep-dive-3-print-in-order) |
| 49 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |
| 50 | Implement Trie (Prefix Tree) | <span class="diff-medium">Medium</span> | Trie | [✅](../../05-advanced/01-tries.md) |

---

## 🔬 Deep-dives — 3 Apple-style walkthroughs

These three are picked because:

- **Two Sum** is the deceptively-simple Apple staple — they grade you on the *quality* of code, not the answer.
- **Largest Rectangle** is the canonical Apple "do you really understand monotonic stack?" check.
- **Print in Order** is the canonical Apple concurrency primer (especially for kernel / iOS systems teams).

---

### Deep-dive 1: Two Sum (the *crafted* version)

<span class="diff-easy">Easy</span> &nbsp; <span class="company-tag">Apple</span>

> Given an array `nums` and a target `t`, return indices of two numbers that add up to `t`.

#### 📖 Story mode

The classic. Apple uses it as a warm-up — but they *grade* the polish: your variable names, your edge cases, your tests, your "what if no answer exists" handling.

#### 🧠 Thinking process

- **O(n²) brute force**: nested loop. Mention it, then do better.
- **Hash map**: as you iterate, check if `target - x` is in a previously-seen map.
- **Apple polish**: clean naming (`complement`, not `t-x`), early return, type hints, docstring.

#### 🐍 Optimal solution

```python
def two_sum(nums: list[int], target: int) -> list[int]:
    """
    Indices of two numbers in nums that sum to target.

    Returns [i, j] with i < j. If no such pair exists, returns [].
    Assumes at most one valid pair exists (per LeetCode spec).
    """
    seen: dict[int, int] = {}                  # value -> index
    for i, x in enumerate(nums):
        complement = target - x
        if complement in seen:
            return [seen[complement], i]
        seen[x] = i
    return []
```

**Why "complement" not "t-x"?** Apple interviewers score readability. Naming a thing makes the code *describe its intent*.

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **Hash map** | O(n) | O(n) |

#### 🔄 Apple's classic follow-up

??? question "What if the array is sorted?"
    Two pointers — `O(n)` time, **`O(1)` space**. State this as the better answer when sorting is given.

??? question "What if multiple valid pairs exist — return all of them?"
    Same hash-map walk, but instead of returning early, append every `(seen[c], i)` pair to a result list. Watch for duplicates if the array has repeats.

??? question "What if the array is so large it doesn't fit in memory?"
    Two-pass external sort + two-pointer scan. Or distribute the hash by `x % numShards` to N machines.

#### 🐛 Common bugs

- Using `seen[x] = i` *before* the lookup — `[3, 3]` with target 6 returns `[0, 0]` instead of `[0, 1]`.
- Returning the *values* instead of the indices.
- Forgetting the "no solution" case.

---

### Deep-dive 2: Largest Rectangle in Histogram

<span class="diff-hard">Hard</span> &nbsp; <span class="company-tag">Apple</span> &nbsp; <span class="company-tag">Google</span>

> Given an array of bar heights `h`, find the largest rectangle that fits inside the histogram.

#### 📖 Story mode

Each bar is 1 wide. A rectangle has *some* height `h[k]` and width = (rightmost bar ≥ h[k]) − (leftmost bar ≥ h[k]) + 1, contiguous. For each bar `k` as the *shortest* bar, find that span. Take the max.

#### 🧠 Thinking process

- **O(n²) brute force**: for each bar, expand left + right while bars ≥ current height. Submit if `n ≤ 10⁴`.
- **Insight**: a monotonically *increasing* stack of bar indices lets you find both the previous-shorter and next-shorter bar in O(n) total. When you pop a bar, you've found its full span.
- **Why monotonic?** Because we only care about indices whose height could still extend rightward. A taller bar earlier in the stack would have been popped when a shorter bar arrived.

#### 🐍 Optimal solution

```python
def largest_rectangle(h: list[int]) -> int:
    """Largest rectangle area in a histogram of bar heights h."""
    stack: list[int] = []        # indices, heights monotonically non-decreasing
    h.append(0)                  # sentinel forces all bars to pop at the end
    best = 0

    for i, height in enumerate(h):
        while stack and h[stack[-1]] > height:
            top = stack.pop()
            # Width: from after the new top of stack to i-1
            left = stack[-1] if stack else -1
            best = max(best, h[top] * (i - left - 1))
        stack.append(i)

    h.pop()                      # restore caller's array
    return best
```

**The sentinel `0`** at the end forces all remaining bars to be popped — without it, we'd need a second loop to drain the stack.

#### 🔍 Dry run on `h = [2, 1, 5, 6, 2, 3]` (then sentinel 0)

| i | h[i] | stack ops | best |
|---|---|---|---|
| 0 | 2 | push | 0 |
| 1 | 1 | pop 2 (width 1, area 2), push 1 | 2 |
| 2 | 5 | push | 2 |
| 3 | 6 | push | 2 |
| 4 | 2 | pop 6 (w=1, a=6), pop 5 (w=2, a=10), push 4 | 10 |
| 5 | 3 | push | 10 |
| 6 | 0 | pop 3 (w=1, a=3), pop 2 (w=4, a=8), pop 1 (w=6, a=6) | **10** |

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **Monotonic stack** | O(n) | O(n) |

#### 🔄 Apple's classic follow-up

??? question "Now do Maximal Rectangle in a 0/1 matrix."
    For each row, treat it as a histogram of "1-height accumulated to here." Run the same algorithm per row. O(rows · cols).

??? question "What if h has 10⁹ entries (streaming)?"
    Process bars one at a time; the stack holds only indices smaller than the current. Memory is bounded by the longest monotonic prefix — typically O(n) worst case. For pathological adversarial input, no streaming algorithm avoids O(n) state.

#### 🐛 Common bugs

- Forgetting the sentinel — leaves the stack non-empty, area unaccounted for.
- Off-by-one on `i - left - 1`: walk through the dry run for `[2,1]` to convince yourself.
- Using `>=` instead of `>` in the while condition — runs O(n²) on `[1,1,1,...,1]` because no element ever pops.

---

### Deep-dive 3: Print in Order

<span class="diff-easy">Easy</span> &nbsp; <span class="company-tag">Apple</span>

> Three threads call `first()`, `second()`, `third()` independently. Ensure output is always `firstsecondthird` regardless of arrival order.

#### 📖 Story mode

A textbook synchronisation problem. The thread orchestrator is non-deterministic — your job is to *force* a happens-before chain between three async functions.

#### 🧠 Thinking process

- **Tools available**: locks, semaphores, events, condition variables. All work; semaphores are the cleanest.
- **Idea**: two semaphores, both initially blocked. `first()` releases sem1 after running. `second()` waits on sem1, runs, releases sem2. `third()` waits on sem2, runs.
- **Why semaphores not booleans**: a flag + busy-wait wastes CPU; semaphores park the thread.

#### 🐍 Optimal solution

```python
import threading

class Foo:
    def __init__(self) -> None:
        # Both semaphores start "drained" — second() and third() block.
        self.sem_2 = threading.Semaphore(0)
        self.sem_3 = threading.Semaphore(0)

    def first(self, printFirst) -> None:
        printFirst()
        self.sem_2.release()              # unblock second()

    def second(self, printSecond) -> None:
        self.sem_2.acquire()              # wait until first() finished
        printSecond()
        self.sem_3.release()              # unblock third()

    def third(self, printThird) -> None:
        self.sem_3.acquire()              # wait until second() finished
        printThird()
```

**Key invariant**: `release()` happens-before the matching `acquire()` returns. The chain `release(sem_2) → acquire(sem_2) → release(sem_3) → acquire(sem_3)` enforces total order.

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| Each call | O(1) | O(1) |

#### 🔄 Apple's classic follow-up

??? question "Generalize to N steps in order."
    Array of N-1 semaphores. Step `k` acquires `sems[k-1]` (skip for k=0), runs, releases `sems[k]` (skip for k=N-1).

??? question "Now make `first()` `second()` `third()` repeatable — they're each called many times in a loop."
    Replace semaphores with **condition variables** + a shared step counter. Or use a single mutex + `step % 3`.

??? question "What's the difference between this and using Python's `asyncio.Event`?"
    `Event.wait()` parks the *coroutine* (cooperative). Semaphores park the *thread* (preemptive). Apple's iOS / kernel teams will probe whether you can articulate this distinction.

#### 🐛 Common bugs

- Using `Semaphore(1)` — both calls would slip through immediately.
- Spinning on a flag — wastes CPU and on weak memory models can race.
- Releasing before printing — undefined output order.

---

## 🗓️ Day-of tips for an Apple interview

!!! tip "The morning checklist"
    1. **Sleep 8 hours**. Apple's onsite is long but calm — stamina + composure win.
    2. **Re-read your project tradeoffs.** "Why did you pick X?" with a real answer.
    3. **One easy + one domain warm-up** (iOS APIs, kernel concepts, GPU shaders — whatever your team).
    4. **Test your video setup** the night before. (Apple uses Webex frequently.)
    5. **Have water + paper** for sketching.

### During the interview

| Stage | What to say / do |
|---|---|
| **First 60s** | Restate. Ask 2 clarifying Qs. **Mention an edge case you'll handle**. |
| **Pre-coding (~5 min)** | State approach + complexity. Mention a tradeoff. |
| **Coding (~25 min)** | Narrate. **Type clean** — Apple grades polish. Add docstrings. |
| **Testing (~5 min)** | Walk through 1 example + 1 edge case. *Test your code* — don't ask the interviewer to. |
| **Domain follow-up** | Ground every choice in physical constraints (battery, memory, latency). |

### Red & green flags

- 🚩 Sloppy variable names (`x`, `tmp`, `i2`).
- 🚩 No edge-case handling.
- 🚩 Talking *over* the interviewer when they hint.
- 🟢 Writing a docstring before the function body.
- 🟢 "If we had a memory budget of X, I'd switch approaches because…"
- 🟢 Asking a curious question about the team's tech stack at the end.

---

## 🔁 Where to go from here

- **Solve the 50** in roughly the order above.
- **Cross-check** with the [Top 100 by Pattern](../top-100-by-pattern.md).
- **Domain prep** is team-specific — research your team's tech stack the week before.
- **Concurrency** (for systems teams): grok GCD / async-await / locks / atomics. LC's "Concurrency" tag has the canonical 12.

> Same six-part shape as [Google 50](google-50.md), [Meta 50](meta-50.md), [Amazon 50](amazon-50.md), and [Microsoft 50](microsoft-50.md).
