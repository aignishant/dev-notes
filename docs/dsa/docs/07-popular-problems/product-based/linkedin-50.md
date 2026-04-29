# LinkedIn — 50 most-asked questions

> The 50 problems LinkedIn (Microsoft-owned, but its own interview style) has asked most often, with the patterns behind them and what the interviewer is grading. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">LinkedIn</span> &nbsp; <span class="phase-status phase-done">Phase 8 — Company list</span>

---

## 📖 How this page is organized

1. **What interviewing here is like**.
2. **What this company tests**.
3. **Common patterns**.
4. **The 50 questions**.
5. **Deep-dives** — 3 representative problems.
6. **Day-of tips**.

---

## 🏢 What interviewing at LinkedIn is like

### Rounds (typical SWE / Senior SWE onsite — 2026)

| Round | Length | Focus |
|---|---|---|
| **Recruiter screen** | 30 min | Background. |
| **Phone screen — coding** | 60 min | One coding problem. CoderPad. |
| **Onsite — coding ×2** | 60 min each | Algorithms. **One round usually emphasizes problem-solving conversations** more than blank-page implementation. |
| **Onsite — host manager** | 60 min | Behavioral + project deep-dive. |
| **Onsite — system design** | 60 min | Senior IC+. Often LinkedIn-flavored: feed ranking, search, messaging. |
| **Onsite — values / culture** | 45 min | "Members First, Relationships Matter" — LinkedIn's stated values. |

### What "the LinkedIn style" actually means

- **Conversational coding.** LinkedIn interviewers explicitly value *thinking-out-loud* over heads-down typing. Long silences cost points.
- **Problem-solving > LeetCode.** Their questions are often *not* in LeetCode's top-200 — they invent variants. Don't memorize, internalize patterns.
- **Production engineering bias.** Java is the dominant LinkedIn language; many interviewers expect *idiomatic* code (favoring `Map<>`, generics, etc.). Python is fine but be clean.
- **Project deep-dive matters.** Be ready to whiteboard your last project at multiple zoom levels.
- **Members First.** A LinkedIn shibboleth — "what does the *member* (user) experience?"

!!! tip "The LinkedIn interviewer mindset"
    LinkedIn interviewers ask: *"Could this person collaborate with my team for the next 5 years?"* — they prize long-tenure hires and culture-add. Curiosity scores; ego costs.

---

## 🎯 What LinkedIn tests

| Signal | Where they grade it | How to show it |
|---|---|---|
| **Problem-solving narrative** | Coding rounds | Talk through your approach, alternatives, tradeoffs *before* coding. |
| **Idiomatic code** | Coding rounds | Whatever language you pick — write it like a senior would. |
| **System design at scale** | Senior+ design round | Feed ranking, search, messaging, edge graph. |
| **Mentor-able** | Host manager | Stories that show learning *and* teaching. |
| **Member-first thinking** | Several rounds | Frame solutions in terms of impact on the LinkedIn member (user). |

---

## 🧩 Patterns that show up most often

| Pattern | Frequency | Why LinkedIn likes it |
|---|---|---|
| **Trees + recursion** | ⭐⭐⭐⭐⭐ | Their bread and butter. |
| **Graphs (BFS / DFS)** | ⭐⭐⭐⭐⭐ | LinkedIn *is* a graph. Connection traversal. |
| **Hash + heap** | ⭐⭐⭐⭐ | Top-K People You May Know. |
| **String parsing** | ⭐⭐⭐⭐ | Profile parsing, query parsing. |
| **DP** | ⭐⭐⭐⭐ | Search ranking, A/B tests. |
| **Sliding window** | ⭐⭐⭐ | Activity feed, throttling. |
| **Backtracking** | ⭐⭐⭐ | Permutations, valid configurations. |
| **OOP / design** | ⭐⭐⭐⭐ | "Design an LRU" — classic LinkedIn phone screen. |
| **Concurrency** | ⭐⭐⭐ | Activity-feed processing, real-time messaging. |

---

## 📋 The 50 questions

Status: ✅ = full v3 in this bible &nbsp; 📝 = mini-v3 below &nbsp; 🚧 = lands later in Phase 8.

### Arrays & strings (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Maximum Subarray | <span class="diff-medium">Medium</span> | Kadane's | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 3 | Maximum Product Subarray | <span class="diff-medium">Medium</span> | DP w/ min+max | 🚧 |
| 4 | Find Largest Number ≤ K (Binary Search) | <span class="diff-medium">Medium</span> | Binary search | 🚧 |
| 5 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 6 | Group Anagrams | <span class="diff-medium">Medium</span> | Hash + sorted-key | 🚧 |
| 7 | Text Justification | <span class="diff-hard">Hard</span> | Greedy line break | 🚧 |
| 8 | Valid Number | <span class="diff-hard">Hard</span> | State machine | 🚧 |
| 9 | Roman to Integer | <span class="diff-easy">Easy</span> | Lookup + subtraction rule | 🚧 |
| 10 | Integer to Roman | <span class="diff-medium">Medium</span> | Greedy lookup | 🚧 |

### Trees (10) — **LinkedIn specialty**

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 11 | Binary Tree Level Order Traversal | <span class="diff-medium">Medium</span> | BFS | 🚧 |
| 12 | Binary Tree Zigzag Level Order Traversal | <span class="diff-medium">Medium</span> | BFS + reverse | 🚧 |
| 13 | Symmetric Tree | <span class="diff-easy">Easy</span> | Recursive mirror | 🚧 |
| 14 | Lowest Common Ancestor (Binary Tree) | <span class="diff-medium">Medium</span> | DFS post-order | 🚧 |
| 15 | Closest Binary Search Tree Value | <span class="diff-easy">Easy</span> | BST traversal | 🚧 |
| 16 | Binary Tree Upside Down | <span class="diff-medium">Medium</span> | Recursive rotation | 🚧 |
| 17 | All Nodes Distance K in Binary Tree | <span class="diff-medium">Medium</span> | DFS + BFS hybrid | 🚧 |
| 18 | Maximum Depth of Binary Tree | <span class="diff-easy">Easy</span> | DFS | 🚧 |
| 19 | Validate BST | <span class="diff-medium">Medium</span> | DFS + bounds | 🚧 |
| 20 | Serialize / Deserialize N-ary Tree | <span class="diff-hard">Hard</span> | DFS + delim | 🚧 |

### Graphs (6)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 21 | Number of Islands | <span class="diff-medium">Medium</span> | Grid BFS/DFS | 🚧 |
| 22 | Course Schedule | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 23 | Word Ladder | <span class="diff-hard">Hard</span> | BFS on word graph | 🚧 |
| 24 | Find Eventual Safe States | <span class="diff-medium">Medium</span> | Reverse topo / DFS | 🚧 |
| 25 | Shortest Path in a Grid with Obstacles Elimination | <span class="diff-hard">Hard</span> | BFS w/ state | 🚧 |
| 26 | Connecting Cities With Minimum Cost | <span class="diff-medium">Medium</span> | MST (Kruskal/Prim) | 🚧 |

### Heap & Top-K (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 27 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | 🚧 |
| 28 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap | 🚧 |
| 29 | Merge K Sorted Lists | <span class="diff-hard">Hard</span> | Min-heap | 🚧 |
| 30 | Find K Pairs with Smallest Sums | <span class="diff-medium">Medium</span> | Heap on (a, b) | 🚧 |

### DP (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 31 | Climbing Stairs | <span class="diff-easy">Easy</span> | 1D DP | 🚧 |
| 32 | Word Break II | <span class="diff-hard">Hard</span> | DP + DFS | 🚧 |
| 33 | Edit Distance | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |
| 34 | Longest Increasing Subsequence | <span class="diff-medium">Medium</span> | Patience / DP | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 35 | Paint House | <span class="diff-medium">Medium</span> | DP w/ constraint | 🚧 |

### Linked lists (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 36 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 37 | Merge Two Sorted Lists | <span class="diff-easy">Easy</span> | Two pointers | 🚧 |
| 38 | Linked List Cycle | <span class="diff-easy">Easy</span> | Floyd's | 🚧 |

### Backtracking (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 39 | Permutations II (with duplicates) | <span class="diff-medium">Medium</span> | Backtracking + skip | 🚧 |
| 40 | Combinations | <span class="diff-medium">Medium</span> | Backtracking | 🚧 |
| 41 | Word Pattern | <span class="diff-easy">Easy</span> | Bijection check | 🚧 |

### Design / OOP (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 42 | Design HashMap | <span class="diff-easy">Easy</span> | Chaining | 🚧 |
| 43 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |
| 44 | Implement Trie (Prefix Tree) | <span class="diff-medium">Medium</span> | Trie | [✅](../../05-advanced/01-tries.md) |
| 45 | Insert Delete GetRandom O(1) | <span class="diff-medium">Medium</span> | Hash + array swap | [📝](#deep-dive-1-randomizedset) |
| 46 | Design Hit Counter | <span class="diff-medium">Medium</span> | Circular buffer | 🚧 |

### Misc / LinkedIn favorites (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 47 | Pow(x, n) | <span class="diff-medium">Medium</span> | Fast exponentiation | 🚧 |
| 48 | Sqrt(x) | <span class="diff-easy">Easy</span> | Binary search | 🚧 |
| 49 | Sparse Vector dot product | <span class="diff-medium">Medium</span> | Two pointers | [📝](#deep-dive-2-sparse-vector-dot-product) |
| 50 | Nested List Weight Sum II | <span class="diff-medium">Medium</span> | BFS + level weight | [📝](#deep-dive-3-nested-list-weight-sum-ii) |

---

## 🔬 Deep-dives — 3 LinkedIn-style walkthroughs

These three are picked because:

- **RandomizedSet** is the canonical LinkedIn data-structure-design problem.
- **Sparse Vector** is asked at *every* LinkedIn onsite (recommendation features are sparse vectors).
- **Nested List Weight Sum II** is a LinkedIn-original — uniquely loved here.

---

### Deep-dive 1: RandomizedSet

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">LinkedIn</span> &nbsp; <span class="company-tag">Stripe</span>

> Design `insert(x)`, `remove(x)`, `getRandom()` — all in O(1).

#### 📖 Story mode

A set with *uniform-random* element access. Hash set has O(1) insert/remove but no random access. Array has O(1) random but O(n) remove. Combine them.

#### 🧠 Thinking process

- **Storage**: an array `arr` of values + a hash map `pos: value -> index in arr`.
- **insert**: append to arr, record pos.
- **remove**: swap the to-remove with the last element, pop last. O(1).
- **getRandom**: pick a uniform random index into arr.

#### 🐍 Optimal solution

```python
import random

class RandomizedSet:
    def __init__(self) -> None:
        self.arr: list[int] = []
        self.pos: dict[int, int] = {}            # value -> index in arr

    def insert(self, val: int) -> bool:
        if val in self.pos:
            return False
        self.pos[val] = len(self.arr)
        self.arr.append(val)
        return True

    def remove(self, val: int) -> bool:
        if val not in self.pos:
            return False
        idx, last = self.pos[val], self.arr[-1]
        self.arr[idx] = last
        self.pos[last] = idx
        self.arr.pop()
        del self.pos[val]
        return True

    def getRandom(self) -> int:
        return random.choice(self.arr)
```

**The swap-with-last trick** keeps the array contiguous — no shifting on remove.

#### ⏱️ Complexity

| Op | Time | Space |
|---|---|---|
| All three | O(1) | O(n) |

#### 🔄 LinkedIn's classic follow-up

??? question "Now allow duplicates — `RandomizedCollection`."
    Replace `pos: value -> index` with `pos: value -> set of indices`. On remove, pop any one index from the set. Same swap-with-last trick.

??? question "How would you implement weighted random selection?"
    Maintain a prefix-sum array; sample by `bisect_left(prefix, random.randint(1, total))`. O(log n) random; O(n) update unless you switch to a Fenwick tree.

??? question "How do you make this thread-safe?"
    Wrap with a single mutex (cheap correctness). For high concurrency, use a read-write lock or a lock-free skip list — explain the tradeoff.

#### 🐛 Common bugs

- Forgetting to update `pos[last]` on remove — `getRandom` returns a stale index.
- Not removing `pos[val]` *after* the swap — confuses the index map.
- Using `random.randrange(len(arr))` then `arr[i]` — fine, just verbose; `random.choice` is clearer.

---

### Deep-dive 2: Sparse Vector dot product

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">LinkedIn</span> &nbsp; <span class="company-tag">Meta</span>

> Design a sparse vector class storing only nonzero indices. Implement `dotProduct(other)` efficiently.

(Same problem as on the [Meta 50 page](meta-50.md#deep-dive-3-sparse-vector-dot-product) — included here because LinkedIn asks it just as often.)

#### 🐍 Optimal solution

```python
class SparseVector:
    def __init__(self, nums: list[int]):
        self.pairs: list[tuple[int, int]] = [
            (i, x) for i, x in enumerate(nums) if x != 0
        ]

    def dotProduct(self, other: "SparseVector") -> int:
        i, j, total = 0, 0, 0
        a, b = self.pairs, other.pairs
        while i < len(a) and j < len(b):
            if a[i][0] == b[j][0]:
                total += a[i][1] * b[j][1]; i += 1; j += 1
            elif a[i][0] < b[j][0]:
                i += 1
            else:
                j += 1
        return total
```

#### 🔄 LinkedIn's classic follow-up

??? question "What if one is super-sparse and the other is dense?"
    Iterate the sparse one; binary-search in the dense one's index list. O(k_sparse · log k_dense).

??? question "How does this scale to LinkedIn's recommendation features (10M-dimensional)?"
    Same algorithm — features *are* sparse vectors. In production, batched on Spark / Flink, with Locality-Sensitive Hashing for approximate nearest-neighbor lookups.

??? question "How to compute cosine similarity?"
    `cos(u, v) = u·v / (||u|| · ||v||)`. Compute the dot product as above, plus precompute `||u||²` once on construction. O(k) per similarity query.

---

### Deep-dive 3: Nested List Weight Sum II

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">LinkedIn</span>

> Given a nested list of integers, return the *weighted* sum where the **deepest** integers have weight 1, and shallower integers have proportionally larger weights. (LC 364 — opposite of the original Weight Sum I.)

#### 📖 Story mode

`[[1,1],2,[1,1]]` — depth-1 has `2`, depth-2 has `1,1,1,1`. Max depth = 2. Weights: depth-1 → 2, depth-2 → 1. Sum = 2·2 + (1+1+1+1)·1 = 8.

#### 🧠 Thinking process

- **Naive**: two passes — first to compute max depth, then weighted sum.
- **One-pass trick**: BFS level-by-level. At each level, maintain a `level_sum` (just the integers at this level) and a running `total_unweighted`. For each new level, `total = total + level_sum_so_far`. After processing all levels, the *deepest* level's contribution is added once; the second-deepest twice; etc. — that's exactly the right weighting.

#### 🐍 Optimal solution (one-pass BFS trick)

```python
from collections import deque

def depth_sum_inverse(nested_list) -> int:
    """Weighted sum with depth weights inverted (deepest = 1)."""
    queue = deque(nested_list)
    unweighted = 0       # sum of integers seen so far at current level
    weighted = 0         # accumulator

    while queue:
        level_size = len(queue)
        for _ in range(level_size):
            item = queue.popleft()
            if item.isInteger():
                unweighted += item.getInteger()
            else:
                queue.extend(item.getList())
        weighted += unweighted              # deeper levels contribute fewer times

    return weighted
```

**Why this works**: a leaf at the deepest level is added to `unweighted` once and then to `weighted` once (the iteration of its level). A leaf one level shallower is added to `weighted` *twice* (its level + the next level). And so on. That's the inverse-depth weighting, in one pass.

#### 🔍 Dry run on `[[1,1],2,[1,1]]`

- Level 1: queue starts as `[[1,1], 2, [1,1]]`. Process: 2 is integer (unweighted += 2). Lists are flattened into queue.
- After level 1: `unweighted = 2, weighted = 2`.
- Level 2: queue is `[1,1,1,1]`. unweighted += 1+1+1+1 = 6.
- After level 2: `unweighted = 6, weighted = 2 + 6 = 8`.

Answer: 8. ✅

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **One-pass BFS** | O(N) | O(N) |

(N = total integers + lists.)

#### 🔄 LinkedIn's classic follow-up

??? question "Now do Nested List Weight Sum I (depth-1 weight 1, deepening grows)."
    DFS with current depth. Sum `value * depth`.

??? question "How would you flatten and yield integers lazily (NestedIterator, LC 341)?"
    Stack of iterators. On `next()`, drill into nested lists until you find an integer.

??? question "What if the structure is so deep that recursion blows the stack?"
    Convert to iterative — explicit stack of `(iterator, depth)`.

#### 🐛 Common bugs

- Two-pass (first pass for max depth, second for sum) is *correct* but the one-pass trick is what LinkedIn grades on. Mention you know both.
- Forgetting to add `unweighted` once *more* at each level — that's where the inversion comes from.

---

## 🗓️ Day-of tips for a LinkedIn interview

!!! tip "The morning checklist"
    1. **Sleep 8 hours**.
    2. **Re-read your project tradeoffs** — LinkedIn loves the host-manager deep-dive.
    3. **One easy + one tree warm-up** — LinkedIn loves trees.
    4. **Re-read** "Members First, Relationships Matter, etc." — LinkedIn's [official values](https://about.linkedin.com/).
    5. **Test your CoderPad / IDE** the night before.

### During the interview

| Stage | What to say / do |
|---|---|
| **First 60s** | Restate. Ask 2 clarifying questions. **Talk through your initial approach.** |
| **Pre-coding (~5 min)** | State approach + alternatives + pick + complexity. *Talking* is itself the signal. |
| **Coding (~25 min)** | Narrate. Type clean. **Explain why** each line exists. |
| **Testing (~5 min)** | Walk through 1 example + 1 edge. |
| **Behavioral** | "Tell me about a time you mentored someone" — LinkedIn loves growth stories. |

### Red & green flags

- 🚩 Heads-down typing without narration. ("I just want to think first" is OK if you say it explicitly — silent typing isn't.)
- 🚩 Ego in past projects. "We struggled, here's what I learned" beats "I was right."
- 🟢 Naming alternatives ("we could also use a heap, but the array gives us O(1) random access — better for this case").
- 🟢 Asking the interviewer's perspective at the end.

---

## 🔁 Where to go from here

- **Solve the 50** in roughly the order above.
- **Tree fluency** is the LinkedIn cornerstone — drill the [Tree DFS](../../04-patterns/08-tree-dfs.md) and [Tree BFS](../../04-patterns/07-tree-bfs.md) patterns.
- **Cross-check** with the [Top 100 by Pattern](../top-100-by-pattern.md).
- **System design** — start with [URL Shortener](../../08-system-design/index.md), then "design LinkedIn feed."

> Same six-part shape as [Google 50](google-50.md) and [Meta 50](meta-50.md).
