# Top 100 by Pattern

> The 100 highest-leverage interview problems, **grouped by the 20 patterns** that solve them. Five problems per pattern. Solve these and you'll recognise the pattern in 95% of interview problems on sight — because every problem here has been asked by every product company at some point in the last five years.

<span class="phase-status phase-inprogress">Phase 8 — curated lists chapter</span>

---

## 📖 How to use this list

This list is **not** a "do these in order and you'll pass." It is a **diagnostic + drill ground**:

1. **Read the [pattern bible](../04-patterns/index.md) first.** Every problem here is annotated with its pattern; the page is useless until you know what those patterns are.
2. **For each pattern, solve 1 problem cold (no hints), then 4 with the page open.** The first one tells you whether you internalised the pattern; the next four cement the variations.
3. **Time-box yourself.** 25 minutes per medium, 40 per hard. If you blow past, look at the editorial — drilling speed matters more than completing in isolation.
4. **Re-solve weakest 20 from scratch a week later.** Spaced repetition is the only thing that survives interview pressure.

!!! tip "How this list was curated"
    The 100 are picked by frequency-of-asking across Google, Meta, Amazon, Microsoft, Apple, Uber, Airbnb, Stripe, Atlassian, and Salesforce 2021–2026 (Glassdoor, LeetCode discuss, Blind, ex-employee blogs). Where two problems test the same micro-pattern, the better-known one is kept. Easy problems are excluded unless they are the canonical illustration of a pattern (e.g. LC 21 for k-way merge).

---

## 🎯 The 20 patterns and 5 problems each

### 1. Sliding Window

| LC # | Problem                                       | Difficulty | Sub-pattern               | Key insight                                                       |
|------|-----------------------------------------------|------------|---------------------------|-------------------------------------------------------------------|
| 3    | Longest Substring Without Repeating Characters | Medium    | Variable window + set     | Shrink from the left when a duplicate enters.                    |
| 76   | Minimum Window Substring                       | Hard       | Variable window + counts  | `need` map + `formed` counter; shrink while valid.               |
| 209  | Minimum Size Subarray Sum                      | Medium     | Variable window + sum     | Grow until sum ≥ target, shrink while still ≥.                   |
| 239  | Sliding Window Maximum                         | Hard       | Monotonic deque           | Deque holds indices of decreasing values; pop stale at front.    |
| 567  | Permutation in String                          | Medium     | Fixed window + counts     | Compare two 26-int arrays; slide one char at a time.             |

### 2. Two Pointers

| LC # | Problem                                   | Difficulty | Sub-pattern         | Key insight                                                            |
|------|-------------------------------------------|------------|---------------------|------------------------------------------------------------------------|
| 11   | Container With Most Water                  | Medium     | Opposite ends       | Move the shorter side; water height is bounded by the shorter wall.   |
| 15   | 3Sum                                       | Medium     | Sort + opposite-end | Fix `i`, two-pointer the rest; skip duplicates on `i`, `l`, `r`.      |
| 42   | Trapping Rain Water                        | Hard       | Two-pointer maxes   | Track `left_max` / `right_max`; water = max(both) − height.            |
| 75   | Sort Colors                                | Medium     | Three-way partition | Dutch national flag; `lo`, `mid`, `hi` pointers.                      |
| 88   | Merge Sorted Array                         | Easy       | Merge from the back | Fill `nums1` from `m + n − 1` to avoid overwriting unread values.     |

### 3. Fast & Slow Pointers

| LC # | Problem                                   | Difficulty | Sub-pattern             | Key insight                                                                |
|------|-------------------------------------------|------------|-------------------------|----------------------------------------------------------------------------|
| 141  | Linked List Cycle                          | Easy       | Floyd cycle detection   | Tortoise + hare; meet inside cycle iff cycle exists.                       |
| 142  | Linked List Cycle II                       | Medium     | Cycle entry algebra     | After meet, restart slow at head; both move 1 step → meet at entry.        |
| 202  | Happy Number                               | Easy       | Cycle on number sequence| Detect cycle in `f(n) = sum_of_squares_of_digits`.                         |
| 287  | Find the Duplicate Number                  | Medium     | Floyd on array indices  | Treat `nums[i]` as next-pointer; cycle exists iff duplicate.                |
| 876  | Middle of the Linked List                  | Easy       | Fast = 2x slow          | When fast hits None, slow is at middle (right-of-two for even length).     |

### 4. Merge Intervals

| LC # | Problem                                 | Difficulty | Sub-pattern              | Key insight                                                          |
|------|-----------------------------------------|------------|--------------------------|----------------------------------------------------------------------|
| 56   | Merge Intervals                          | Medium     | Sort + sweep             | Sort by start; merge if `cur.start ≤ prev.end`.                     |
| 57   | Insert Interval                          | Medium     | Three-phase walk         | Pre / overlap / post — handle each segment separately.               |
| 253  | Meeting Rooms II                         | Medium     | Sweep-line / heap        | Sort starts/ends; or min-heap of end-times for active meetings.      |
| 435  | Non-overlapping Intervals                | Medium     | Greedy by end-time       | Sort by end; greedily keep earliest-ending compatible.               |
| 759  | Employee Free Time                       | Hard       | Multi-list merge intervals| Min-heap over `(start, list_idx, idx)` like k-way merge.            |

### 5. Cyclic Sort

| LC # | Problem                                | Difficulty | Sub-pattern             | Key insight                                                            |
|------|----------------------------------------|------------|-------------------------|------------------------------------------------------------------------|
| 41   | First Missing Positive                  | Hard       | In-place hash via index | Place `k` at `nums[k-1]`; first index `i` with `nums[i] != i+1` wins. |
| 268  | Missing Number                          | Easy       | XOR or sum              | XOR `nums` with `0..n`; survivor is missing.                          |
| 287  | Find the Duplicate Number               | Medium     | Cyclic-sort placement   | Alternative to Floyd: place each at its home; first conflict = dup.   |
| 442  | Find All Duplicates in an Array         | Medium     | Sign-flip marker        | Mark `nums[abs(x)-1]` negative; second visit means duplicate.         |
| 448  | Find All Numbers Disappeared            | Easy       | Sign-flip marker        | After marking, indices still positive are the missing values.         |

### 6. In-Place Linked List Reversal

| LC # | Problem                              | Difficulty | Sub-pattern        | Key insight                                                       |
|------|--------------------------------------|------------|--------------------|-------------------------------------------------------------------|
| 25   | Reverse Nodes in k-Group              | Hard       | k-group reversal   | Count k ahead; if exists, reverse and recurse on tail.            |
| 92   | Reverse Linked List II                | Medium     | Sublist reversal   | Walk to `left − 1`; reverse `right − left + 1` nodes; reattach.   |
| 143  | Reorder List                          | Medium     | Reverse + zip      | Find middle, reverse second half, merge alternately.              |
| 206  | Reverse Linked List                   | Easy       | Three-pointer      | `prev`, `cur`, `nxt` — the canonical template.                    |
| 234  | Palindrome Linked List                | Easy       | Reverse half + compare | Find middle, reverse second half, two-pointer compare.        |

### 7. Tree BFS

| LC # | Problem                                | Difficulty | Sub-pattern          | Key insight                                                       |
|------|----------------------------------------|------------|----------------------|-------------------------------------------------------------------|
| 102  | Binary Tree Level Order Traversal      | Medium     | Standard BFS         | Snapshot `len(queue)` at the top of each iteration for the level. |
| 103  | Binary Tree Zigzag Level Order         | Medium     | BFS + reverse parity | Track depth parity; reverse the level on odd depths.              |
| 199  | Binary Tree Right Side View            | Medium     | BFS take last        | Last node added at each level is rightmost.                       |
| 297  | Serialize and Deserialize Binary Tree  | Hard       | BFS with sentinels   | Encode None as `'#'`; decode with a queue + iterator.              |
| 994  | Rotting Oranges                        | Medium     | Multi-source BFS     | Initial queue = all rotten cells; BFS time = answer.              |

### 8. Tree DFS

| LC # | Problem                                  | Difficulty | Sub-pattern              | Key insight                                                                  |
|------|------------------------------------------|------------|--------------------------|------------------------------------------------------------------------------|
| 98   | Validate Binary Search Tree               | Medium     | DFS with bounds          | Pass `(lo, hi)` down; each node must lie within.                             |
| 124  | Binary Tree Maximum Path Sum              | Hard       | Post-order with global    | Return single-arm; update global with full triangle.                          |
| 236  | Lowest Common Ancestor of a Binary Tree   | Medium     | Post-order               | If both subtrees report a hit, current node is the LCA.                       |
| 543  | Diameter of Binary Tree                   | Easy       | Post-order with global    | Same triangle pattern as 124, but counting edges.                             |
| 1448 | Count Good Nodes in Binary Tree           | Medium     | DFS with running max     | Push the max-on-path down; count when current ≥ max.                          |

### 9. Two Heaps

| LC # | Problem                                | Difficulty | Sub-pattern             | Key insight                                                                  |
|------|----------------------------------------|------------|-------------------------|------------------------------------------------------------------------------|
| 295  | Find Median from Data Stream            | Hard       | Max-heap + min-heap     | Maintain `|lo| − |hi| ∈ {0, 1}`; median at top.                              |
| 480  | Sliding Window Median                   | Hard       | Two-heap + lazy delete  | Add `to_remove` map; prune at heap tops only.                                |
| 502  | IPO                                     | Hard       | Capital-gated heap      | Min-heap by capital + max-heap by profit gated by current cash.              |
| 632  | Smallest Range Covering Elements         | Hard       | Min-heap of k pointers  | Heap holds smallest from each list; track current max; advance min.          |
| 1942 | The Number of the Smallest Unoccupied Chair | Medium  | Two heaps               | Available chairs (min-heap) + busy chairs (min-heap by leave time).          |

### 10. Subsets / Backtracking

| LC # | Problem                                 | Difficulty | Sub-pattern               | Key insight                                                                 |
|------|-----------------------------------------|------------|---------------------------|-----------------------------------------------------------------------------|
| 39   | Combination Sum                          | Medium     | Backtrack with reuse      | Pass `start` index to allow reuse without duplicates.                       |
| 46   | Permutations                             | Medium     | Used-set / swap-in-place  | Two canonical templates: `used[]` array or in-place swap.                   |
| 51   | N-Queens                                 | Hard       | Constraint propagation    | Three sets: `cols`, `diag1 (r+c)`, `diag2 (r−c)`.                            |
| 78   | Subsets                                  | Medium     | Choose / don't choose     | At each index, branch include or skip; produces all 2ⁿ subsets.             |
| 79   | Word Search                              | Medium     | DFS on grid + visited     | Mark visited in-place; restore on backtrack.                                |

### 11. Modified Binary Search

| LC # | Problem                                  | Difficulty | Sub-pattern              | Key insight                                                                  |
|------|------------------------------------------|------------|--------------------------|------------------------------------------------------------------------------|
| 33   | Search in Rotated Sorted Array            | Medium     | Two-half check           | One half is always sorted; check which one contains target.                  |
| 153  | Find Minimum in Rotated Sorted Array      | Medium     | Pivot via comparison      | Compare `nums[mid]` to `nums[hi]`.                                           |
| 410  | Split Array Largest Sum                   | Hard       | Binary search on answer  | Binary-search the max-subarray-sum; check feasibility with `m` greedy splits.|
| 875  | Koko Eating Bananas                       | Medium     | Binary search on answer  | Search `k` ∈ `[1, max]`; feasible if `Σ ⌈p_i/k⌉ ≤ H`.                         |
| 1095 | Find in Mountain Array                    | Hard       | Two-phase binary search  | First find peak; then two binary searches (ascending + descending).          |

### 12. Top K Elements

| LC # | Problem                                | Difficulty | Sub-pattern              | Key insight                                                              |
|------|----------------------------------------|------------|--------------------------|--------------------------------------------------------------------------|
| 215  | Kth Largest Element in an Array         | Medium     | Min-heap of size k OR quickselect | Heap is `O(n log k)`; quickselect is `O(n)` expected.        |
| 347  | Top K Frequent Elements                 | Medium     | Counter + heap           | Count, then min-heap of size k by frequency.                            |
| 658  | Find K Closest Elements                 | Medium     | Two-pointer or BS+window | Binary-search the window's left edge directly.                          |
| 692  | Top K Frequent Words                    | Medium     | Counter + custom heap    | Custom comparator (freq desc, lex asc).                                 |
| 973  | K Closest Points to Origin              | Medium     | Min-heap of size k OR QS | Same skeleton as 215; comparator is `x² + y²`.                          |

### 13. K-Way Merge

| LC # | Problem                                | Difficulty | Sub-pattern             | Key insight                                                               |
|------|----------------------------------------|------------|-------------------------|---------------------------------------------------------------------------|
| 21   | Merge Two Sorted Lists                  | Easy       | Two-pointer merge       | Dummy head + walk; relink the smaller next.                               |
| 23   | Merge k Sorted Lists                    | Hard       | Min-heap of k pointers  | Push heads, pop smallest, push next.                                      |
| 373  | Find K Pairs with Smallest Sums         | Medium     | Heap on grid            | Push `(0, j)`; on pop `(i, j)` push `(i+1, j)` (and `(0, j+1)` once).     |
| 378  | Kth Smallest in a Sorted Matrix         | Medium     | Min-heap of row pointers OR BS on value | Heap = `O(k log n)`; BS-on-value = `O(n log(max−min))`.|
| 632  | Smallest Range Covering Elements         | Hard       | k-way merge + max track  | Heap pops min; track current max across heap.                            |

### 14. Topological Sort

| LC # | Problem                                | Difficulty | Sub-pattern         | Key insight                                                                  |
|------|----------------------------------------|------------|---------------------|------------------------------------------------------------------------------|
| 207  | Course Schedule                         | Medium     | Cycle detection     | Kahn's BFS; if final processed != n, cycle exists.                           |
| 210  | Course Schedule II                      | Medium     | Topo order          | Same algorithm; emit nodes as you process them.                              |
| 269  | Alien Dictionary                        | Hard       | Build graph + topo  | Compare adjacent pairs to derive edges; detect cycles.                       |
| 310  | Minimum Height Trees                    | Medium     | Layer-peel leaves   | BFS from leaves inward; last 1–2 nodes are the centroids.                    |
| 1857 | Largest Color Value in a Directed Graph | Hard       | Topo + DP           | DP `count[u][c]` over the topo order; cycle → return −1.                     |

### 15. 0/1 Knapsack DP

| LC # | Problem                                  | Difficulty | Sub-pattern             | Key insight                                                              |
|------|------------------------------------------|------------|-------------------------|--------------------------------------------------------------------------|
| 416  | Partition Equal Subset Sum                | Medium     | Subset-sum boolean DP   | Target = total / 2; reduce to "can we hit `target`?"                     |
| 474  | Ones and Zeroes                           | Medium     | 2D knapsack             | `dp[zeros][ones]` over strings.                                          |
| 494  | Target Sum                                | Medium     | Reduce to subset sum    | Pick `P ⊆ S` with `Σ P = (target + total)/2`.                            |
| 879  | Profitable Schemes                        | Hard       | 3D knapsack             | `dp[i][members][profit_floor]` capping profit at `minProfit`.            |
| 1049 | Last Stone Weight II                      | Medium     | Min-diff partition       | Same as 416 but minimise abs-diff between two halves.                    |

### 16. Unbounded Knapsack DP

| LC # | Problem                                | Difficulty | Sub-pattern             | Key insight                                                                |
|------|----------------------------------------|------------|-------------------------|----------------------------------------------------------------------------|
| 322  | Coin Change                             | Medium     | Min-count DP            | `dp[a] = 1 + min(dp[a − c] for c)`.                                        |
| 377  | Combination Sum IV                      | Medium     | Order-matters count     | `dp[t] = Σ dp[t − n]`; outer loop on target, inner on nums (order matters).|
| 518  | Coin Change II                          | Medium     | Order-doesn't-matter    | Outer loop on coins, inner on amount.                                       |
| 983  | Minimum Cost For Tickets                | Medium     | Time-windowed unbounded | DP over days; transitions are 1 / 7 / 30-day costs.                        |
| 2585 | Number of Ways to Earn Points           | Hard       | Bounded-count knapsack  | Two-loop DP with per-question counts capped.                                |

### 17. Fibonacci Numbers DP

| LC # | Problem                                | Difficulty | Sub-pattern         | Key insight                                                                  |
|------|----------------------------------------|------------|---------------------|------------------------------------------------------------------------------|
| 70   | Climbing Stairs                          | Easy       | dp[i] = dp[i-1] + dp[i-2] | Literal Fibonacci.                                                       |
| 198  | House Robber                             | Medium     | Two-state DP         | `dp[i] = max(dp[i-1], dp[i-2] + nums[i])`.                                  |
| 213  | House Robber II                          | Medium     | Circular variant     | Run twice: skip first, or skip last; take max.                              |
| 740  | Delete and Earn                          | Medium     | Convert to 198       | Sum points by value; then House-Robber over the value axis.                 |
| 746  | Min Cost Climbing Stairs                 | Easy       | Same as 70 with cost | `dp[i] = cost[i] + min(dp[i-1], dp[i-2])`.                                  |

### 18. Palindromic Subsequence DP

| LC # | Problem                                | Difficulty | Sub-pattern             | Key insight                                                                  |
|------|----------------------------------------|------------|-------------------------|------------------------------------------------------------------------------|
| 5    | Longest Palindromic Substring           | Medium     | Expand around centre OR DP | 2n − 1 centres in O(n²); DP gives same complexity.                       |
| 131  | Palindrome Partitioning                 | Medium     | Backtrack + palindrome DP | Pre-compute `is_pal[l][r]`; backtrack splits.                              |
| 132  | Palindrome Partitioning II              | Hard       | DP min-cuts             | `cuts[i] = min(cuts[j] + 1)` for `j` where `s[j+1..i]` is palindrome.        |
| 516  | Longest Palindromic Subsequence         | Medium     | 2D DP `dp[l][r]`        | `dp[l][r] = dp[l+1][r-1] + 2` if `s[l] == s[r]`, else `max(...)`.            |
| 647  | Palindromic Substrings                  | Medium     | Expand around centre    | Count palindromes by expanding from each centre; same trick as 5.            |

### 19. Longest Common Subsequence DP

| LC # | Problem                                | Difficulty | Sub-pattern              | Key insight                                                                |
|------|----------------------------------------|------------|--------------------------|----------------------------------------------------------------------------|
| 72   | Edit Distance                           | Hard       | LCS-flavoured DP         | `dp[i][j] = min(insert, delete, replace) + 1` (or LCS-extend on match).    |
| 583  | Delete Operation for Two Strings        | Medium     | LCS                      | Answer = `len(a) + len(b) − 2 · LCS(a, b)`.                                |
| 712  | Minimum ASCII Delete Sum                | Medium     | LCS by sum               | Same DP, but cost = ASCII-sum instead of count.                            |
| 1143 | Longest Common Subsequence              | Medium     | The canonical LCS DP     | `dp[i][j]` over prefixes; `+1` on match else max.                          |
| 1312 | Minimum Insertion Steps to Palindrome   | Hard       | LCS with reverse         | Answer = `len(s) − LCS(s, reverse(s))`.                                    |

### 20. Bitwise XOR

| LC # | Problem                                | Difficulty | Sub-pattern             | Key insight                                                                  |
|------|----------------------------------------|------------|-------------------------|------------------------------------------------------------------------------|
| 136  | Single Number                           | Easy       | XOR all                 | All pairs cancel; survivor is the singleton.                                 |
| 137  | Single Number II                        | Medium     | Bit-count mod 3         | For each bit, sum mod 3 isolates the singleton.                              |
| 260  | Single Number III                       | Medium     | Partition by bit        | XOR all → diff; pick a set bit; partition into two groups; XOR each.         |
| 268  | Missing Number                          | Easy       | XOR with index          | XOR `nums` with `0..n`; survivor is missing.                                 |
| 421  | Maximum XOR of Two Numbers in Array     | Medium     | Bitwise trie            | Insert into 32-bit trie; for each `x`, walk greedily for max XOR.            |

---

## 📊 Frequency vs effort grid

If you have only **30 problems' worth of time**, drill these — the highest frequency-asked, ordered by pattern:

1. Sliding Window — LC 3, 76, 209
2. Two Pointers — LC 11, 15, 42
3. Fast/Slow — LC 141, 142
4. Merge Intervals — LC 56, 253
5. Tree BFS — LC 102, 199
6. Tree DFS — LC 124, 236
7. Two Heaps — LC 295
8. Backtracking — LC 39, 78, 79
9. Modified BS — LC 33, 875
10. Top K — LC 215, 347
11. K-way Merge — LC 23
12. Topological Sort — LC 207, 269
13. Knapsack — LC 322, 416
14. Fibonacci DP — LC 198
15. LCS DP — LC 1143, 72
16. XOR — LC 136, 421

That's exactly 30 problems covering 16 of 20 patterns. Solve them well; the remaining 70 are amplifiers.

---

## 🧭 Where to go from here

- Once you've drilled this list, hit a **company page** for your target employer — those filter the 100 down to "what *they* ask most" with a different ordering.
- For **system-design** prep, jump to [System Design](../08-system-design/index.md).
- If you stumble on a particular pattern, the [pattern bible](../04-patterns/index.md) is your remedial reading — every problem above links back to its canonical pattern page.

> **Up next in popular problems:** the company pages — Meta, Amazon, Microsoft, Apple, and the rest of the product/service/PSU spread.
