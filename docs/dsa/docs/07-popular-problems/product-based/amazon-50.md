# Amazon — 50 most-asked questions

> The 50 problems Amazon (AWS, Retail, Alexa, Ads, Prime Video) has asked most often over the last 5 years, with the patterns behind them and what the interviewer is actually grading. Same six-part shape as the [Google 50](google-50.md) and [Meta 50](meta-50.md) pages.

<span class="company-tag">Amazon</span> &nbsp; <span class="phase-status phase-inprogress">Phase 8 — company page</span>

---

## 📖 How this page is organized

Six-part shape — identical to every other company page in this bible.

1. **What interviewing here is like** — rounds, format, signal, vibe.
2. **What this company tests** — the specific skills they grade for.
3. **Common patterns** — which of the 20 patterns show up most often.
4. **The 50 questions** — grouped by topic, with difficulty + pattern + a one-liner.
5. **Deep-dives** — 3 representative problems in mini-v3 format with Amazon-specific framing.
6. **Day-of tips** — last-minute reminders.

---

## 🏢 What interviewing at Amazon is like

### Rounds (typical SDE I/II onsite — 2026)

| Round | Length | Focus |
|---|---|---|
| **Online assessment (OA)** | 90-120 min | 2 coding problems + work-style + work simulation. CodeSignal. |
| **Phone screen** | 60 min | One coding problem + behavioral on 2 Leadership Principles. |
| **Onsite — coding ×2** | 60 min each | Coding problem + LP behavioral *interleaved*. ≈ 30 min each. |
| **Onsite — system design** | 60 min | SDE II+ only. AWS-flavored. |
| **Onsite — Bar Raiser** | 60 min | A senior employee from a *different* org. They can veto the hire. Coding + heavy LP. |
| **Onsite — hiring manager** | 60 min | Mostly LP, some coding. |

SDE I = new grad. SDE II = ~3-5 yr exp. SDE III+ adds more design + cross-team rounds.

### What "the Amazon style" actually means

- **LP, LP, LP.** Every interviewer evaluates you on the [16 Leadership Principles](https://www.amazon.jobs/en/principles). Coding is necessary but not sufficient.
- **STAR stories matter as much as algorithms.** Have ~12 stories prepared, each tagged to 2-3 LPs.
- **Bar Raiser is the wild card.** They're *trained* to detect "would this person lower the bar?" — they can solo-veto. Their LP questions go deepest.
- **Customer obsession** is the LP. If you can frame your solution in terms of "what does the customer experience?", you score.
- **Bias for action vs deliver results.** The interviewer wants to see you ship something working in 30 min, then improve — not pursue the optimal in silence.
- **Ownership.** "What did *you* do?" not "what did the team do?" Use **I**, not we.

!!! tip "The Amazon interviewer mindset"
    Amazon interviewers fill in a structured rubric mapped to LPs after every round. They mentally ask: *"Which LPs did this candidate demonstrate, and which did they fail to demonstrate?"* — not "did they solve the problem." A solved problem with no LP signal is a no-hire.

---

## 🎯 What Amazon tests

Mapping rounds → signals:

| Signal | Where they grade it | How to show it |
|---|---|---|
| **Coding correctness** | OA, phone, onsite ×2, Bar Raiser | Solve in 25 min; spend 5 min testing. **Working > optimal**. |
| **Customer obsession** | Every round | Frame the problem from the user's perspective. "If this is slow, the customer abandons their cart." |
| **Ownership** | Every behavioral | "I owned the migration end-to-end. When the rollback failed at 2am, I…" |
| **Bias for action** | Coding rounds + behavioral | Write something *now*, optimize later. State your tradeoff. |
| **Deliver results** | Every round | Have **outcome metrics** for every story. "Reduced p99 latency from 800ms to 120ms." |
| **Are right, a lot** | Bar Raiser | Acknowledge when you don't know; pivot to what you *would* try; reason aloud about probabilities. |
| **Dive deep** | System design, behavioral | Be ready for "explain how a database index works internally" mid-design round. |
| **Frugality** | System design | Choose the cheapest AWS service that meets the SLA. They love S3 + Lambda combos. |

---

## 🧩 Patterns that show up most often

Based on 5 years of public reports (Glassdoor, LeetCode discuss, Blind, ex-Amazon blogs):

| Pattern | Frequency | Why Amazon likes it |
|---|---|---|
| **BFS / DFS on grid or graph** | ⭐⭐⭐⭐⭐ | Warehouses-as-grids, dependency chains, package routing. |
| **Trie + autocomplete** | ⭐⭐⭐⭐⭐ | Search bar on amazon.com is *literally* the canonical product. |
| **Heap / Top-K** | ⭐⭐⭐⭐⭐ | Recommendation rankings, K-closest fulfillment centers. |
| **Hash map composition** | ⭐⭐⭐⭐ | Frequency counting at retail scale. |
| **Sliding window** | ⭐⭐⭐⭐ | Fraud detection, log analysis, time-series. |
| **Topological sort** | ⭐⭐⭐⭐ | Dependency graphs, package install order, course-schedule clones. |
| **Two pointers** | ⭐⭐⭐ | Beyond-brute-force filter. |
| **Backtracking** | ⭐⭐⭐ | Combinations, partition-labels variants. |
| **Union-find** | ⭐⭐⭐ | Connected components, account merge. |
| **DP** | ⭐⭐⭐ | Less than Google but classic stock + knapsack still appear. |
| **Binary search on answer** | ⭐⭐⭐ | "Minimum capacity to ship in D days" family. |

---

## 📋 The 50 questions

Difficulty pill conventions:

- <span class="diff-easy">Easy</span> &nbsp; <span class="diff-medium">Medium</span> &nbsp; <span class="diff-hard">Hard</span>

Status:

- ✅ = full v3 solution exists in this bible (link given)
- 📝 = covered in mini-v3 below
- 🚧 = lands in Phase 8 (full v3 solutions for every Amazon problem)

### Arrays & strings (12)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash map | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Best Time to Buy and Sell Stock | <span class="diff-easy">Easy</span> | Running min | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 3 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 4 | Most Common Word | <span class="diff-easy">Easy</span> | Hash map + tokenize | 🚧 |
| 5 | Group Anagrams | <span class="diff-medium">Medium</span> | Hash + sorted-key | 🚧 |
| 6 | Longest Palindromic Substring | <span class="diff-medium">Medium</span> | Expand-around-center | 🚧 |
| 7 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 8 | Partition Labels | <span class="diff-medium">Medium</span> | Greedy + last-index map | 🚧 |
| 9 | Integer to Roman | <span class="diff-medium">Medium</span> | Greedy lookup | 🚧 |
| 10 | Roman to Integer | <span class="diff-easy">Easy</span> | Lookup + subtraction rule | 🚧 |
| 11 | Reorder Log Files | <span class="diff-easy">Easy</span> | Custom sort | 🚧 |
| 12 | String to Integer (atoi) | <span class="diff-medium">Medium</span> | State machine | 🚧 |

### Linked lists (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 13 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 14 | Merge Two Sorted Lists | <span class="diff-easy">Easy</span> | Two pointers | 🚧 |
| 15 | Copy List with Random Pointer | <span class="diff-medium">Medium</span> | Hash map / interleave | 🚧 |

### Trees (7)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 16 | Binary Tree Level Order Traversal | <span class="diff-medium">Medium</span> | BFS | 🚧 |
| 17 | Validate BST | <span class="diff-medium">Medium</span> | DFS + bounds | 🚧 |
| 18 | Lowest Common Ancestor (Binary Tree) | <span class="diff-medium">Medium</span> | DFS post-order | 🚧 |
| 19 | Binary Tree Maximum Path Sum | <span class="diff-hard">Hard</span> | DFS post-order | 🚧 |
| 20 | Diameter of Binary Tree | <span class="diff-easy">Easy</span> | DFS post-order | 🚧 |
| 21 | Symmetric Tree | <span class="diff-easy">Easy</span> | Recursive mirror | 🚧 |
| 22 | Word Search II | <span class="diff-hard">Hard</span> | Trie + DFS | 🚧 |

### Graphs (6)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 23 | Number of Islands | <span class="diff-medium">Medium</span> | Grid BFS/DFS | 🚧 |
| 24 | Rotting Oranges | <span class="diff-medium">Medium</span> | Multi-source BFS | [📝](#deep-dive-3-rotting-oranges) |
| 25 | Course Schedule | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 26 | Course Schedule II | <span class="diff-medium">Medium</span> | Topo sort + order | 🚧 |
| 27 | Word Ladder | <span class="diff-hard">Hard</span> | BFS on word graph | 🚧 |
| 28 | Critical Connections in a Network | <span class="diff-hard">Hard</span> | Tarjan bridges | 🚧 |

### Heap & Top-K (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 29 | K Closest Points to Origin | <span class="diff-medium">Medium</span> | Heap / quickselect | [📝](#deep-dive-2-k-closest-points-to-origin) |
| 30 | Top K Frequent Words | <span class="diff-medium">Medium</span> | Heap + custom compare | 🚧 |
| 31 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap / bucket sort | 🚧 |
| 32 | Merge K Sorted Lists | <span class="diff-hard">Hard</span> | Min-heap | 🚧 |
| 33 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | 🚧 |

### Trie & autocomplete (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 34 | Implement Trie (Prefix Tree) | <span class="diff-medium">Medium</span> | Trie | [✅](../../05-advanced/01-tries.md) |
| 35 | Search Suggestions System | <span class="diff-medium">Medium</span> | Trie / sort + bisect | [📝](#deep-dive-1-search-suggestions-system) |
| 36 | Concatenated Words | <span class="diff-hard">Hard</span> | Trie + DP | 🚧 |

### Backtracking (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 37 | Letter Combinations of a Phone Number | <span class="diff-medium">Medium</span> | Backtracking | 🚧 |
| 38 | Generate Parentheses | <span class="diff-medium">Medium</span> | Backtracking + counters | 🚧 |
| 39 | Word Break | <span class="diff-medium">Medium</span> | DP + dictionary | 🚧 |

### Dynamic programming (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 40 | Climbing Stairs | <span class="diff-easy">Easy</span> | 1D DP | 🚧 |
| 41 | Maximum Subarray (Kadane's) | <span class="diff-medium">Medium</span> | DP | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 42 | Coin Change | <span class="diff-medium">Medium</span> | Unbounded knapsack | 🚧 |
| 43 | Longest Common Subsequence | <span class="diff-medium">Medium</span> | 2D DP | 🚧 |

### Search / two pointers (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 44 | 3Sum | <span class="diff-medium">Medium</span> | Sort + two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 45 | Capacity to Ship Packages Within D Days | <span class="diff-medium">Medium</span> | Binary search on answer | 🚧 |
| 46 | First Bad Version | <span class="diff-easy">Easy</span> | Binary search | 🚧 |

### Design (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 47 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |
| 48 | Insert Delete GetRandom O(1) | <span class="diff-medium">Medium</span> | Hash + array swap | 🚧 |
| 49 | Design In-Memory File System | <span class="diff-hard">Hard</span> | Trie of nodes | 🚧 |
| 50 | Logger Rate Limiter | <span class="diff-easy">Easy</span> | Hash + timestamp | 🚧 |

---

## 🔬 Deep-dives — 3 Amazon-style walkthroughs

These three are picked because:

- **Search Suggestions** is the canonical Amazon problem — it *is* the search bar.
- **K Closest Points** showcases the heap-vs-quickselect tradeoff Amazon loves to ask follow-ups about.
- **Rotting Oranges** is the cleanest multi-source BFS warm-up — Amazon uses it as the "can you do BFS without restarting from scratch?" filter.

---

### Deep-dive 1: Search Suggestions System

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Amazon</span>

> Given a sorted list of `products` and a `searchWord`, return up to 3 lexicographically smallest products that share each prefix `searchWord[:k]` for `k = 1..len(searchWord)`.

#### 📖 Story mode

You're typing "mou" into amazon.com's search bar. After "m" you see the 3 alphabetically-smallest products starting with "m". After "mo" you see the 3 starting with "mo". And so on. The page must update on every keystroke.

#### 🧠 Thinking process

- **Approach A (sort + binary search)**: sort `products`. For each prefix, binary-search the first product that starts with the prefix. The next 3 (if they share the prefix) are the answer.
- **Approach B (Trie)**: build a Trie. At each node, store the 3 lex-smallest words passing through it. For each prefix, walk the trie, return the stored list.
- **Why both matter**: A is shorter and faster to ship in 30 min; B is what they want for the **follow-up** "what if products are added/removed at runtime?"

#### 🐍 Optimal solution (sort + bisect)

```python
import bisect

def suggested_products(products: list[str], search_word: str) -> list[list[str]]:
    """Return up to 3 lex-smallest products per growing prefix of search_word."""
    products.sort()                                     # O(P log P)
    out: list[list[str]] = []
    prefix = ""

    for ch in search_word:
        prefix += ch
        # First product that is >= prefix (lex order)
        i = bisect.bisect_left(products, prefix)
        # Take up to 3, but only those that still start with prefix
        out.append([
            p for p in products[i:i + 3] if p.startswith(prefix)
        ])

    return out
```

**Why `bisect_left`**: it gives the *first* position whose product is `>= prefix`. The next two (at most) sit immediately after — but we still must check `startswith` because we may have run past the prefix block.

#### 🔍 Dry run on `products = ["mobile","mouse","moneypot","monitor","mousepad"]`, `search_word = "mouse"`

After sort: `["mobile","moneypot","monitor","mouse","mousepad"]`.

| step | prefix | bisect_left | products[i:i+3] | filtered |
|---|---|---|---|---|
| 1 | "m" | 0 | ["mobile","moneypot","monitor"] | all start with "m" ✅ |
| 2 | "mo" | 0 | ["mobile","moneypot","monitor"] | all ✅ |
| 3 | "mou" | 3 | ["mouse","mousepad"] | both ✅ |
| 4 | "mous" | 3 | ["mouse","mousepad"] | both ✅ |
| 5 | "mouse" | 3 | ["mouse","mousepad"] | both ✅ |

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **Sort + bisect** | O(P log P + W · log P) | O(P) |
| **Trie + per-node top-3** | O(P · L + W · L) | O(P · L) |

(P = #products, L = avg length, W = `len(search_word)`)

#### 🔄 Amazon's classic follow-up

??? question "What if products are added/removed at runtime?"
    Use the **Trie** version. Each Trie node stores a sorted list of up to 3 lex-smallest words passing through. On insert, walk the trie and update each node's top-3 if the new word qualifies. On lookup, walk to the prefix node and return its list — O(L) per query.

??? question "What if the dataset is 100M products and won't fit in memory?"
    Build a **distributed trie** sharded by first character (or first 2 chars). Each query routes to one shard. Each shard's top-3 is then merged at the gateway — though if you shard correctly (one shard per prefix), no merge is needed.

??? question "What if 'lex-smallest' becomes 'most popular'?"
    Each trie node stores a top-3 by popularity score. On purchase events, propagate score updates up the path — O(L) per update.

#### 🐛 Common bugs

- Forgetting the `startswith(prefix)` filter — `bisect_left` doesn't guarantee a match.
- Slicing `products[i:i+3]` and *then* sorting — wastes work; the array is already sorted.
- Building a Trie character-by-character but forgetting to maintain the per-node top-3 invariant on insert.

---

### Deep-dive 2: K Closest Points to Origin

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">Meta</span>

> Given an array of points `points[i] = (x, y)` and an integer `K`, return the `K` points closest to the origin.

#### 📖 Story mode

Customer searches "pizza" on the Amazon app. You have 100K restaurants with `(lat, lng)`. Return the 5 closest. The naive sort-all is wasted work — we only need the top 5.

#### 🧠 Thinking process

- **Sort all**: O(n log n). Wasted work for K ≪ n.
- **Max-heap of size K**: keep the K-smallest distances. Push every point; pop when heap > K. **O(n log K)**, the standard answer.
- **Quickselect (partial sort)**: O(n) expected. The interviewer's favorite *follow-up* — they want both.

#### 🐍 Optimal solution (max-heap of size K)

```python
import heapq

def k_closest(points: list[list[int]], k: int) -> list[list[int]]:
    """Return the K points (x,y) closest to origin (Euclidean, squared OK)."""
    # Python's heapq is a min-heap. Negate the key to fake a max-heap.
    heap: list[tuple[int, list[int]]] = []

    for x, y in points:
        d = x * x + y * y                  # squared distance — no need for sqrt
        if len(heap) < k:
            heapq.heappush(heap, (-d, [x, y]))
        elif -heap[0][0] > d:              # current farthest in top-K is farther than this point
            heapq.heapreplace(heap, (-d, [x, y]))

    return [p for _, p in heap]
```

**Why squared distance?** Comparing `x²+y²` is monotonic with `√(x²+y²)`. Skip the sqrt — fewer FLOPs, no float precision issues.

**Why max-heap of size K, not min-heap of size n?** The max-heap stays bounded at K, so `push/pop` is `O(log K)`, not `O(log n)`. Memory is `O(K)`, not `O(n)`.

#### 🔍 Dry run on `points = [[1,3],[-2,2],[5,8],[0,1]]`, `k = 2`

Distances²: 10, 8, 89, 1.

| step | point | d | heap before | action | heap after |
|---|---|---|---|---|---|
| 1 | (1,3) | 10 | [] | push (size<k) | [(-10,(1,3))] |
| 2 | (-2,2) | 8 | [(-10,...)] | push (size<k) | [(-10,...), (-8,...)] |
| 3 | (5,8) | 89 | top dist=10 | 10>89? no. skip | unchanged |
| 4 | (0,1) | 1 | top dist=10 | 10>1? yes. heapreplace | [(-8,(-2,2)), (-1,(0,1))] |

Result: `[(-2,2), (0,1)]`. ✅

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **Sort all** | O(n log n) | O(n) |
| **Max-heap of K** | O(n log K) | O(K) |
| **Quickselect** | O(n) expected, O(n²) worst | O(1) extra |

#### 🔄 Amazon's classic follow-up

??? question "Can you do better than O(n log K)?"
    Yes — **quickselect** gives O(n) expected. Pick a random pivot, partition by distance, recurse on the side containing the K-th element. After the recursion, the first K positions are the answer (unsorted). The interviewer is testing "do you know about partial sort?"

??? question "What if points stream in (can't fit in memory)?"
    The max-heap-of-K approach **already handles streams** — you only need O(K) memory. This is why Amazon prefers the heap solution over `sorted(...)[:k]` for the canonical answer.

??? question "What if points are 3D / N-dimensional?"
    Same algorithm with `sum(c*c for c in coords)`. For *very* high D + many queries, switch to a **KD-tree** (`O(log n)` per query average) or LSH for approximate nearest neighbors.

#### 🐛 Common bugs

- Using `math.sqrt(x*x + y*y)` — slower, and tiny float errors cause flaky equal-distance tie-breaks.
- Pushing all `n` points into a min-heap then popping K — that's O(n + K log n), not O(n log K). Memory blows up.
- Forgetting to negate the key for max-heap simulation — returns the K *farthest* points.

---

### Deep-dive 3: Rotting Oranges

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Amazon</span>

> Given an `m × n` grid where `0` = empty, `1` = fresh orange, `2` = rotten orange, each minute every fresh orange adjacent (4-directionally) to a rotten one rots. Return the minute count when no fresh orange remains, or -1 if impossible.

#### 📖 Story mode

A warehouse pallet has rotten apples mixed in with fresh ones. Each minute, every apple touching a rotten one rots too. Multi-source disease spread. The answer is the *latest* time any apple rots — not the first.

#### 🧠 Thinking process

- **Why BFS, not DFS?** BFS naturally tracks "minutes" as level numbers. DFS gives you a time per cell, but level-tracking is messy.
- **Multi-source**: seed the queue with **all rotten oranges at once**, not one at a time. Their levels start at 0 simultaneously.
- **Why this is wrong from a single source**: you'd compute distance from one rotten orange, but the answer is `min` over all sources — which is exactly what multi-source BFS computes.

#### 🐍 Optimal solution

```python
from collections import deque

def oranges_rotting(grid: list[list[int]]) -> int:
    """Minutes until all oranges rot, or -1 if any fresh orange is unreachable."""
    rows, cols = len(grid), len(grid[0])
    queue: deque[tuple[int, int, int]] = deque()  # (r, c, minute)
    fresh = 0

    # Seed all rotten cells (minute 0)
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2:
                queue.append((r, c, 0))
            elif grid[r][c] == 1:
                fresh += 1

    minutes = 0
    while queue:
        r, c, t = queue.popleft()
        minutes = max(minutes, t)
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                grid[nr][nc] = 2
                fresh -= 1
                queue.append((nr, nc, t + 1))

    return minutes if fresh == 0 else -1
```

**The fresh counter is the cleanup**: if any fresh oranges remain after BFS, they were unreachable — return -1.

#### 🔍 Dry run on `[[2,1,1],[1,1,0],[0,1,1]]`

Initial queue: `[(0,0,0)]`. fresh = 6.

| pop | t | newly rotted | fresh | queue tail |
|---|---|---|---|---|
| (0,0,0) | 0 | (0,1,1), (1,0,1) | 4 | … |
| (0,1,1) | 1 | (0,2,2), (1,1,2) | 2 | … |
| (1,0,1) | 1 | — (already rotted) | 2 | … |
| (0,2,2) | 2 | — | 2 | … |
| (1,1,2) | 2 | (2,1,3) | 1 | … |
| (2,1,3) | 3 | (2,2,4) | 0 | … |
| (2,2,4) | 4 | — | 0 | done |

Minutes max = 4. fresh == 0. Answer: **4**. ✅

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **Multi-source BFS** | O(m · n) | O(m · n) |

#### 🔄 Amazon's classic follow-up

??? question "What if rot can spread diagonally too?"
    Add the 4 diagonal directions to the directions tuple. Algorithm unchanged.

??? question "What if some rotten oranges are 'super-rotten' and rot 2 cells per minute?"
    Each cell now has a per-source spreading rate. Multi-source BFS still works — change the `t + 1` to the source's rate. Or model as Dijkstra with non-uniform edge weights.

??? question "What if the grid is huge and only updates per second?"
    Streaming: keep a `last_rot_time[(r,c)]` map. On each tick, scan the *frontier* (cells rotted last tick) and spread. O(perimeter) per tick instead of O(grid).

#### 🐛 Common bugs

- Seeding the queue with one rotten orange, not all of them — gives time-from-one-source, not the answer.
- Forgetting the `fresh` counter — returns 0 instead of -1 on disconnected fresh oranges.
- DFS: works but level-tracking gets ugly (you'd recurse with `(t+1)` and take a max over recursive calls — fine, just less natural).

---

## 🗓️ Day-of tips for an Amazon interview

!!! tip "The morning checklist"
    1. **Sleep 8 hours**. Onsite is 5+ hours of LP-heavy interviews — you need the stamina.
    2. **Re-read your STAR stories**. Have ~12 ready, each tagged to 2-3 LPs. *Don't* try to memorize — internalize.
    3. **Re-read** the [16 LPs](https://www.amazon.jobs/en/principles), especially Customer Obsession, Ownership, Bias for Action.
    4. **One easy + one medium warm-up**. Pick from this 50.
    5. **Have water + tissues + paper**. Long days; physical comfort matters.

### During each round

| Stage | What to say / do |
|---|---|
| **First 60 seconds (coding)** | Restate. **Ask 2 clarifying questions tied to the customer.** "Are duplicate inputs possible? — they would be in the real catalog." |
| **Pre-coding (~5 min)** | State approach + complexity. **Mention frugality**: "I'll use O(K) memory, not O(n) — relevant for our cluster." |
| **Coding (~25 min)** | Narrate. Type clean. **Talk LPs while coding** when natural. |
| **Testing (~5 min)** | Walk through 1 example + 1 edge case. |
| **Behavioral (~15-25 min)** | Wait for the LP question. Use **STAR** format: *Situation, Task, Action (your action), Result (with metrics)*. |

### Red flags Amazon interviewers note

- Saying "we did" instead of "I did" in STAR stories.
- No outcome metrics in your stories. ("It was successful" → "What does successful mean?")
- Solving the problem but never connecting it back to the customer.
- Defending a wrong answer for more than 30s — Amazon prefers humble pivots.
- LP stories that contradict each other across rounds (interviewers compare notes).

### Green flags Amazon interviewers note

- Taking ownership in stories: "I owned the migration end-to-end. I made the call to roll back at 2am."
- Customer-framed solutions: "If lookups are slow, the customer abandons their cart."
- Outcome metrics: "Reduced p99 from 800ms to 120ms" instead of "made it fast."
- Acknowledging tradeoffs: "Quickselect is O(n) expected but harder to implement under time pressure — the heap is the safer ship."
- Asking how the team uses what they built.

---

## 🔁 Where to go from here

- **Solve the 50** in roughly the order above. Each topic compounds.
- **Practice STAR stories** out loud. The 16 LPs come up in *every* round — coding included.
- **Cross-check** with the [Top 100 by Pattern](../top-100-by-pattern.md). Anything on both lists is **must-do**.
- **System design (SDE II+)** has its own page. Start with [URL Shortener](../../08-system-design/index.md), then S3 / DynamoDB / Lambda combos (lands in Phase 9).
- **Behavioral** prep lives in [Behavioral](../../11-behavioral/index.md) — Amazon's section will be the largest because of LPs.

> Same six-part shape as [Google 50](google-50.md) and [Meta 50](meta-50.md). Microsoft, Apple, Netflix, Uber roll out next, all reusing this structure.
