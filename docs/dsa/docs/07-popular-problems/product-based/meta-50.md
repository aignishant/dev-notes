# Meta — 50 most-asked questions

> The 50 problems Meta (Facebook / Instagram / WhatsApp) has asked most often over the last 5 years, with the patterns behind them and what the interviewer is actually grading. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">Meta</span> &nbsp; <span class="phase-status phase-done">Phase 8 — Company list</span>

---

## 📖 How this page is organized

Six-part shape — identical to every other company page in this bible.

1. **What interviewing here is like** — rounds, format, signal, vibe.
2. **What this company tests** — the specific skills they grade for.
3. **Common patterns** — which of the 20 patterns show up most often.
4. **The 50 questions** — grouped by topic, with difficulty + pattern + a one-liner.
5. **Deep-dives** — 3 representative problems in mini-v3 format with Meta-specific framing.
6. **Day-of tips** — last-minute reminders.

---

## 🏢 What interviewing at Meta is like

### Rounds (typical SWE E3/E4 onsite — 2026)

| Round | Length | Focus |
|---|---|---|
| **Phone screen — coding** | 45 min | Two coding problems back-to-back. Both usually mediums. CoderPad. |
| **Onsite — Ninja ×2** | 45 min each | Pure coding. **Two problems per round.** ≈ 22 min/problem. |
| **Onsite — Pirate** | 45 min | Behavioral + career story. The "do we want this person" round. |
| **Onsite — Architect** | 45 min | System design. E4+. |

E3 = new grad. E4 = ~2-5 yr exp. E5+ adds an extra design + cross-functional round.

### What "the Meta style" actually means

- **Speed matters.** Two-problems-in-45-min means you cannot be precious. Identify the pattern fast, code clean, move on.
- **One-shot correctness is prized**. Compile-and-run isn't a substitute for thinking; bugs caught by the interviewer cost more than at Google.
- **They will ask "can you do better?"** — and they expect a *better* answer, not a defense of the current one. Always know the next-tier optimization.
- **The 5-step framework**: clarify → plan → code → test → optimize. Saying these out loud shows process.
- **No system design at E3.** All four onsite rounds are coding. That's why pattern recognition is everything.

!!! tip "The Meta interviewer mindset"
    Meta interviewers are often graded on calibration, not just outcome. They mentally ask: *"Did this candidate solve the second problem in time, with clean code, while explaining clearly?"* Optimizing for the third is what separates a hire from a no-hire.

---

## 🎯 What Meta tests

Mapping rounds → signals:

| Signal | Where they grade it | How to show it |
|---|---|---|
| **Speed + pattern recognition** | Ninja rounds | Identify the pattern in <60s. Don't restart. Reuse subroutines between problems in the same round. |
| **Code quality under time pressure** | Ninja rounds | Helpers, sentinels, type hints — even in 22 min. Tested code beats untested perfect code. |
| **Communication** | Every round | Narrate continuously. Acknowledge tradeoffs. State complexity *before* coding. |
| **Product sense** | Pirate, sometimes Ninja | "Why would Meta build this?" — show curiosity about *why* the problem matters. |
| **Scale thinking** | Architect (E4+) | News Feed, chat, photos — all at billion-user scale. Estimate fan-out, push vs pull, cache invalidation. |
| **Drive / impact / ownership** | Pirate | STAR stories where you owned a thing end-to-end and shipped it. |

---

## 🧩 Patterns that show up most often

Based on 5 years of public reports (Glassdoor, LeetCode discuss, Blind, ex-Meta blogs):

| Pattern | Frequency | Why Meta likes it |
|---|---|---|
| **Tree BFS / DFS** | ⭐⭐⭐⭐⭐ | News Feed, comment threads, social graph — all trees and graphs. |
| **Hash map composition** | ⭐⭐⭐⭐⭐ | Their "is this candidate fluent?" test. Two-pointer + hash, sliding window + hash. |
| **Graph BFS / DFS / topo** | ⭐⭐⭐⭐ | Social graph, friendship recommendations, dependency resolution. |
| **Sliding window** | ⭐⭐⭐⭐ | Strings, character-frequency variants — extremely common at Meta. |
| **Heap / priority queue** | ⭐⭐⭐⭐ | Top-K friends, ranking, news-feed scoring. |
| **Design (LRU, RandomPick, sparse vector)** | ⭐⭐⭐⭐ | Meta loves "design this in 22 min" mid-Ninja. |
| **Two pointers** | ⭐⭐⭐ | Their "beyond brute force" filter. |
| **Backtracking** | ⭐⭐⭐ | Combinations, valid parentheses, regex. |
| **Binary search** | ⭐⭐⭐ | Often "binary search the answer" variants. |
| **DP** | ⭐⭐ | Less than Google. When asked, usually 1D + a follow-up. |
| **Trie** | ⭐⭐ | Autocomplete, friend-search-by-prefix. |

---

## 📋 The 50 questions

Difficulty pill conventions:

- <span class="diff-easy">Easy</span> &nbsp; <span class="diff-medium">Medium</span> &nbsp; <span class="diff-hard">Hard</span>

Status:

- ✅ = full v3 solution exists in this bible (link given)
- 📝 = covered in mini-v3 below
- 🚧 = lands in Phase 8 (full v3 solutions for every Meta problem)

### Arrays & strings (14)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash map | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Best Time to Buy and Sell Stock | <span class="diff-easy">Easy</span> | Running min | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 3 | Move Zeroes | <span class="diff-easy">Easy</span> | Two pointers | 🚧 |
| 4 | Merge Intervals | <span class="diff-medium">Medium</span> | Sort + sweep | [✅](../../04-patterns/04-merge-intervals.md) |
| 5 | Next Permutation | <span class="diff-medium">Medium</span> | In-place reversal | 🚧 |
| 6 | Subarray Sum Equals K | <span class="diff-medium">Medium</span> | Prefix sum + hash | 🚧 |
| 7 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 8 | Minimum Window Substring | <span class="diff-hard">Hard</span> | Sliding window | 🚧 |
| 9 | Valid Palindrome II | <span class="diff-easy">Easy</span> | Two pointers + skip-one | 🚧 |
| 10 | Add Strings | <span class="diff-easy">Easy</span> | Carry simulation | 🚧 |
| 11 | Multiply Strings | <span class="diff-medium">Medium</span> | Schoolbook + carry | 🚧 |
| 12 | Valid Word Abbreviation | <span class="diff-easy">Easy</span> | Two pointers | 🚧 |
| 13 | Simplify Path | <span class="diff-medium">Medium</span> | Stack | 🚧 |
| 14 | Integer to English Words | <span class="diff-hard">Hard</span> | Recursion + lookup | 🚧 |

### Linked lists (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 15 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 16 | Add Two Numbers | <span class="diff-medium">Medium</span> | Carry + dummy head | 🚧 |
| 17 | Copy List with Random Pointer | <span class="diff-medium">Medium</span> | Hash map / interleave | 🚧 |

### Trees (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 18 | Binary Tree Right Side View | <span class="diff-medium">Medium</span> | BFS / DFS-by-depth | 🚧 |
| 19 | Binary Tree Vertical Order Traversal | <span class="diff-medium">Medium</span> | BFS + column map | [📝](#deep-dive-1-vertical-order-traversal) |
| 20 | Diameter of Binary Tree | <span class="diff-easy">Easy</span> | DFS post-order | 🚧 |
| 21 | Lowest Common Ancestor (Binary Tree) | <span class="diff-medium">Medium</span> | DFS post-order | 🚧 |
| 22 | LCA III (with parent pointers) | <span class="diff-medium">Medium</span> | Two-pointer on ancestors | 🚧 |
| 23 | Binary Tree Maximum Path Sum | <span class="diff-hard">Hard</span> | DFS post-order | 🚧 |
| 24 | Convert BST to Sorted Doubly Linked List | <span class="diff-medium">Medium</span> | In-order + prev pointer | 🚧 |
| 25 | Range Sum of BST | <span class="diff-easy">Easy</span> | DFS with bounds | 🚧 |
| 26 | Binary Tree Level Order Traversal | <span class="diff-medium">Medium</span> | BFS | 🚧 |
| 27 | Serialize / Deserialize Binary Tree | <span class="diff-hard">Hard</span> | DFS + queue | 🚧 |

### Graphs (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 28 | Number of Islands | <span class="diff-medium">Medium</span> | Grid BFS/DFS | 🚧 |
| 29 | Clone Graph | <span class="diff-medium">Medium</span> | DFS + hash | 🚧 |
| 30 | Word Ladder | <span class="diff-hard">Hard</span> | BFS on word graph | 🚧 |
| 31 | Alien Dictionary | <span class="diff-hard">Hard</span> | Topo sort | 🚧 |
| 32 | Shortest Path in Binary Matrix | <span class="diff-medium">Medium</span> | BFS 8-directional | 🚧 |

### Heap & Top-K (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 33 | Kth Largest Element in an Array | <span class="diff-medium">Medium</span> | Quickselect / heap | 🚧 |
| 34 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap / bucket sort | 🚧 |
| 35 | Merge K Sorted Lists | <span class="diff-hard">Hard</span> | Min-heap | 🚧 |
| 36 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | 🚧 |

### Backtracking (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 37 | Subsets | <span class="diff-medium">Medium</span> | Backtracking | 🚧 |
| 38 | Letter Combinations of a Phone Number | <span class="diff-medium">Medium</span> | Backtracking | 🚧 |
| 39 | Remove Invalid Parentheses | <span class="diff-hard">Hard</span> | BFS on string | 🚧 |

### Dynamic programming (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 40 | Climbing Stairs | <span class="diff-easy">Easy</span> | 1D DP | 🚧 |
| 41 | Decode Ways | <span class="diff-medium">Medium</span> | 1D DP | 🚧 |
| 42 | Longest Increasing Subsequence | <span class="diff-medium">Medium</span> | Patience / DP | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 43 | Continuous Subarray Sum | <span class="diff-medium">Medium</span> | Prefix mod + hash | 🚧 |

### Sorting / search (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 44 | Custom Sort String | <span class="diff-medium">Medium</span> | Counting + order map | 🚧 |
| 45 | Find First and Last Position in Sorted Array | <span class="diff-medium">Medium</span> | Binary search | 🚧 |
| 46 | Pow(x, n) | <span class="diff-medium">Medium</span> | Fast exponentiation | 🚧 |

### Design (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 47 | Random Pick with Weight | <span class="diff-medium">Medium</span> | Prefix sum + binary search | [📝](#deep-dive-2-random-pick-with-weight) |
| 48 | Dot Product of Two Sparse Vectors | <span class="diff-medium">Medium</span> | Two pointers on (idx, val) | [📝](#deep-dive-3-sparse-vector-dot-product) |
| 49 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |
| 50 | Min Stack | <span class="diff-medium">Medium</span> | Two stacks | 🚧 |

---

## 🔬 Deep-dives — 3 Meta-style walkthroughs

These three are picked because:

- They appear in **almost every Meta onsite** per recent reports (Vertical Order, Random Pick, Sparse Vector).
- They each demonstrate a **different signal** Meta grades on (data-structure composition, algorithm-as-API, two-pointer fluency).
- They each have a **classic Meta follow-up** that is itself the "second problem" of a Ninja round.

---

### Deep-dive 1: Vertical Order Traversal

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span>

> Given the root of a binary tree, return the vertical order traversal — for each column (left-most first), list nodes top-to-bottom, then left-to-right at the same `(row, col)`.

#### 📖 Story mode

Imagine pinning every node to a `(row, col)` grid. Root is `(0, 0)`. Left child is `(row+1, col-1)`, right child is `(row+1, col+1)`. Print all columns left-to-right, top-to-bottom inside each column.

#### 🧠 Thinking process

- **Idea**: BFS, tagging each node with its column. Group by column.
- **Trick**: at the same `(row, col)`, ties break by **value** (LC 987) or by **insertion order** (LC 314). The interviewer may ask you to handle either.
- **Why BFS not DFS?** BFS visits row-by-row, which is exactly how we want to break ties within a column.

#### 🐍 Optimal solution (LC 314 — insertion-order tie-break)

```python
from collections import defaultdict, deque

def vertical_order(root):
    """Return columns, leftmost first; each column is a list top-to-bottom."""
    if not root:
        return []
    cols: dict[int, list[int]] = defaultdict(list)
    queue = deque([(root, 0)])
    min_col, max_col = 0, 0

    while queue:
        node, col = queue.popleft()
        cols[col].append(node.val)
        min_col, max_col = min(min_col, col), max(max_col, col)
        if node.left:
            queue.append((node.left, col - 1))
        if node.right:
            queue.append((node.right, col + 1))

    return [cols[c] for c in range(min_col, max_col + 1)]
```

**Tracking `min_col, max_col`** lets us output columns in order without sorting the dict's keys (a small but classic Meta polish).

#### 🔍 Dry run on tree `[3,9,20,null,null,15,7]`

```
       3 (col 0)
      / \
     9   20 (col 1)
        /  \
      15    7 (col 2)
     (col 1)
```

BFS: (3,0), (9,-1), (20,1), (15,0), (7,2). Cols: `{-1:[9], 0:[3,15], 1:[20], 2:[7]}` → `[[9],[3,15],[20],[7]]`.

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **BFS** | O(n) | O(n) |

#### 🔄 Meta's classic follow-up

??? question "What if tie-break is by node value (LC 987), not insertion order?"
    Store `(row, val)` tuples in `cols[col]`, then sort each column. O(n log n).

??? question "Can you do it in O(n) with bucket-sort tricks?"
    For LC 314 yes (above). For LC 987, no — the value-tie-break forces a comparison sort within columns in the worst case.

??? question "Stream 1B nodes — can't fit in memory."
    External merge: bucket nodes by `col` to disk during traversal, then merge per-column files. The interviewer is checking if you know "groupby + external sort" beats "load everything."

#### 🐛 Common bugs

- Using DFS — you lose the row ordering and have to sort by `(row, ...)` afterward.
- Forgetting to track `min_col` / `max_col` — sorting dict keys is fine but slightly slower and feels unidiomatic.

---

### Deep-dive 2: Random Pick with Weight

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Google</span>

> Given an array `w` of positive weights, implement `pickIndex()` that returns index `i` with probability `w[i] / sum(w)`.

#### 📖 Story mode

You have a roulette wheel. Each slice has width proportional to its weight. Spin a ball — which slice does it land in? That's a binary search on the cumulative-weight prefix.

#### 🧠 Thinking process

- **Insight**: convert weights to a prefix sum. Generate a random `r ∈ [1, total]`. Find the smallest index `i` where `prefix[i] >= r`. That's `bisect_left` on the prefix array.
- **Why prefix sum**: it turns "land in slice `i`" into "first index where running total ≥ r" — a textbook binary search.

#### 🐍 Optimal solution

```python
import bisect, random

class Solution:
    def __init__(self, w: list[int]):
        # prefix[i] = sum of w[0..i] inclusive.
        self.prefix: list[int] = []
        running = 0
        for x in w:
            running += x
            self.prefix.append(running)
        self.total = running

    def pickIndex(self) -> int:
        r = random.randint(1, self.total)
        return bisect.bisect_left(self.prefix, r)
```

**Why `bisect_left`, not `bisect_right`?** Because we want the *smallest* index whose prefix ≥ `r` — `bisect_left` returns insertion point keeping `r` left of equals.

#### 🔍 Dry run on `w = [1, 3, 2]`

`prefix = [1, 4, 6]`, `total = 6`. `r ∈ {1,2,3,4,5,6}` uniform.

| r | bisect_left(prefix, r) | Index returned |
|---|---|---|
| 1 | 0 | 0 (prob 1/6 ✅) |
| 2 | 1 | 1 (prob 3/6 across r∈{2,3,4} ✅) |
| 3 | 1 | 1 |
| 4 | 1 | 1 |
| 5 | 2 | 2 (prob 2/6 across r∈{5,6} ✅) |
| 6 | 2 | 2 |

Distribution matches `[1/6, 3/6, 2/6]` — correct.

#### ⏱️ Complexity

| Op | Time | Space |
|---|---|---|
| `__init__` | O(n) | O(n) |
| `pickIndex` | O(log n) | — |

#### 🔄 Meta's classic follow-up

??? question "What if the weights are updated dynamically?"
    Replace the prefix array with a **Fenwick (BIT)** keyed by index. `update(i, Δ)` is O(log n); `pickIndex` becomes a "find smallest index whose prefix ≥ r" — a BIT walk in O(log n).

??? question "What if weights can be negative?"
    Probabilities can't be negative — so the question only makes sense if you're modeling something else (e.g., "pick a non-zero-weighted item" with rejection sampling). Push back on the spec.

??? question "What if you must avoid `random.randint` (e.g., embedded device)?"
    Use **alias method** by Walker — O(n) preprocessing, O(1) per pick, only needs uniform `[0,1)`. Standard answer for distribution sampling at scale.

#### 🐛 Common bugs

- `random.randint(0, total)` instead of `(1, total)` — gives index 0 too often (`r=0` always matches `bisect_left` = 0).
- Off-by-one on `prefix` — using exclusive prefix shifts every probability.

---

### Deep-dive 3: Sparse Vector dot product

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Meta</span>

> Design a class `SparseVector` storing a vector with mostly zeros. Implement `dotProduct(other: SparseVector)` efficiently.

#### 📖 Story mode

A vector with 1M dimensions but only 100 non-zero entries should not be stored as a list of 1M zeros. Store only the non-zero `(index, value)` pairs. Now dot-product is "merge two sorted lists by index."

#### 🧠 Thinking process

- **Storage**: list of `(idx, val)` tuples sorted by `idx`. (Or hash map — interviewer will challenge this; see follow-up.)
- **Dot product**: two pointers walking both lists; advance the smaller index. Sum products only when indices match.
- **Why two pointers, not hash join?** Hash works (O(min(n, m))) but the two-pointer merge is O(n + m) deterministic, lower constants, and shows pattern fluency.

#### 🐍 Optimal solution

```python
class SparseVector:
    def __init__(self, nums: list[int]):
        # Store only non-zero entries, sorted by index by construction.
        self.pairs: list[tuple[int, int]] = [
            (i, x) for i, x in enumerate(nums) if x != 0
        ]

    def dotProduct(self, other: "SparseVector") -> int:
        i, j, total = 0, 0, 0
        a, b = self.pairs, other.pairs
        while i < len(a) and j < len(b):
            if a[i][0] == b[j][0]:
                total += a[i][1] * b[j][1]
                i += 1
                j += 1
            elif a[i][0] < b[j][0]:
                i += 1
            else:
                j += 1
        return total
```

#### 🔍 Dry run on `v1 = [1,0,0,2,3]` and `v2 = [0,3,0,4,0]`

`v1.pairs = [(0,1),(3,2),(4,3)]`, `v2.pairs = [(1,3),(3,4)]`.

| i | j | a[i] | b[j] | action | total |
|---|---|---|---|---|---|
| 0 | 0 | (0,1) | (1,3) | a smaller, i++ | 0 |
| 1 | 0 | (3,2) | (1,3) | b smaller, j++ | 0 |
| 1 | 1 | (3,2) | (3,4) | match, +2·4=8 | 8 |
| 2 | 2 |  |  | done |  |

Answer: 8. ✅ (Sanity: `1·0+0·3+0·0+2·4+3·0 = 8`.)

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| `__init__` | O(n) | O(k) where k = non-zeros |
| `dotProduct` | O(k₁ + k₂) | O(1) extra |

#### 🔄 Meta's classic follow-up

??? question "What if one vector is super-sparse (10 non-zeros) and the other is dense (1M non-zeros)?"
    Iterate over the **sparse** one, **binary search** in the dense one. O(k_sparse · log k_dense) beats O(k_sparse + k_dense) when k_sparse ≪ k_dense.

??? question "Why not a hash map?"
    Valid alternative — `O(min(k₁, k₂))` lookup. Two-pointer is preferred when pairs are already sorted (cheaper, cache-friendly). Mention both, pick two-pointer, justify.

??? question "What about 100B-dimensional vectors distributed across machines?"
    Shard by index range. Each shard does a local dot-product; sum across shards. The interviewer is checking if you can hop from "in-memory algorithm" to "distributed system" without flailing.

#### 🐛 Common bugs

- Storing zeros — defeats the entire point.
- Using lists of `idx` and lists of `val` separately — fine, but error-prone when advancing pointers in lockstep.
- Forgetting `i += 1; j += 1` on match — infinite loop.

---

## 🗓️ Day-of tips for a Meta interview

!!! tip "The morning checklist"
    1. **Sleep 8 hours**. Tired-Meta-candidate is a losing combo because speed matters here more than at most companies.
    2. **Re-read** *only* the [pattern cheat-sheet](../../04-patterns/index.md) and your "common bugs" notes.
    3. **One easy warm-up + one medium** the morning of — get into 22-min/problem rhythm.
    4. **Test CoderPad** the night before. Auto-format off, no autocomplete crutches.
    5. **Browser tabs**: only the meeting link. Notifications muted.

### During each Ninja round

| Stage | What to say / do |
|---|---|
| **First 60 seconds (per problem)** | Restate. Two clarifying questions. State pattern guess. |
| **Pre-coding (~3 min)** | State your approach **and complexity**. "I'll do hashmap-prefix-sum, O(n) time, O(n) space." |
| **Coding (~12 min)** | Narrate. Type clean. Edge cases at top. |
| **Testing (~3 min)** | Walk through one example + one edge case **out loud**. |
| **Move on** | If problem 1 took 25 min, *cut* — apologize, jump to problem 2. **Do not over-spend.** |

### Red flags Meta interviewers note

- Spending 35 min on problem 1 of a 2-problem round.
- Coding silently for 5+ minutes.
- Defending a wrong answer when given a hint.
- "I'd add error handling in real code" instead of writing it.
- Forgetting to give complexity until prompted.

### Green flags Meta interviewers note

- Naming the pattern in the first 60 seconds.
- Volunteering a follow-up *before* the interviewer asks ("with a Fenwick tree we could…").
- Catching your own bug during dry run and fixing it without prompting.
- Cutting your losses on problem 1 to save problem 2.
- Asking how the algorithm would scale at Meta-size data.

---

## 🔁 Where to go from here

- **Solve the 50** in roughly the order above (arrays → trees → graphs → heap → design). Each topic compounds.
- **For each problem you don't recognize**, hit the [pattern that drives it](../../04-patterns/index.md) before grinding more instances.
- **Cross-check** with the [Top 100 by Pattern](../top-100-by-pattern.md) — anything on both lists is **must-do**.
- **System design (E4+)** has its own page. Start with [URL Shortener](../../08-system-design/index.md), then News Feed (lands in Phase 9).
- **Behavioral (Pirate)** prep lives in [Behavioral](../../11-behavioral/index.md).

> Same six-part shape as [Google 50](google-50.md). When Amazon, Microsoft, and the rest land, the structure stays identical — the rounds, patterns, and 50 questions change.
