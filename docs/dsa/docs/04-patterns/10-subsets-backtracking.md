# Subsets & Backtracking

> The recursive "try-all-then-undo" engine that powers every "generate all valid X" question — subsets, permutations, combinations, palindrome partitioning, N-Queens, Sudoku, word break, generate parentheses. One template ("choose, recurse, un-choose") underlies a dozen distinct problems. The thing to internalise is **how to skip duplicates without missing valid answers** and **when to prune dead branches early**.

<span class="phase-status phase-done">Phase 5 — Patterns</span>

---

## 📖 What is backtracking?

Imagine you're walking a maze with branching corridors and a notebook. At each fork you scribble "I went left" and walk on. If you hit a dead end, you erase the last entry and try the other way. If you find the exit, you copy the notebook into your final answer book — *then keep exploring*, because the problem asks for **all** valid paths, not the first one.

That's backtracking. The mechanics are always:

1. **Choose** — make a decision at the current step.
2. **Recurse** — explore the consequences.
3. **Un-choose** — undo the decision so the parent can try a different one.

The state you mutate is shared across calls (a list, a set, a board) — that's the whole performance trick. **Backtracking ≠ "try every combination naively."** Naive enumeration creates a fresh copy at every step (O(n) per step). Backtracking reuses one buffer and pops at the end.

Subsets is the canonical primitive: at each index, *either include the element or skip it*. That's a binary tree of depth `n` with `2ⁿ` leaves — exactly the count of subsets.

!!! tip "The signal — when to reach for backtracking"
    Reach for it when you see:

    - "Generate **all**" — all subsets, all permutations, all valid combinations, all paths.
    - "Find **a** valid X" with a complex constraint — N-Queens, Sudoku, word break.
    - The brute force is "enumerate all 2ⁿ / n! candidates and filter" — backtracking *is* that, but with **pruning**.
    - State space is exponential and DP/greedy don't apply (no overlapping subproblems).

    Cousins:

    - **DFS on a tree** ([08-tree-dfs.md](08-tree-dfs.md)) — when the branching is *over a given tree*, not over the choice space.
    - **Bitmask DP** — when 2ⁿ subsets is small enough to enumerate as bitmasks (typically n ≤ 20).

---

## 🧩 The three flavors

### Flavor 1: Include / exclude (subset primitive)

For each element in order, branch on "include" vs "skip." Use a single shared `path` list with `append`/`pop` for the choose/un-choose dance.

```python
def subsets(nums: list[int]) -> list[list[int]]:
    out: list[list[int]] = []
    path: list[int] = []

    def backtrack(i: int) -> None:
        if i == len(nums):
            out.append(path.copy())            # (1) snapshot at every leaf
            return
        # Skip nums[i]
        backtrack(i + 1)
        # Include nums[i]
        path.append(nums[i])
        backtrack(i + 1)
        path.pop()                             # (2) un-choose

    backtrack(0)
    return out
```

1. **Always copy.** `out.append(path)` stores a reference; subsequent pops mutate it.
2. **Pop matches every push.** This is the "un-choose" step; without it the path leaks into the parent's frame.

The same problem is often presented with a "start index" idiom — same answer, slightly different shape:

```python
def subsets_start_index(nums: list[int]) -> list[list[int]]:
    out: list[list[int]] = []
    path: list[int] = []

    def backtrack(start: int) -> None:
        out.append(path.copy())                # (3) every node is a subset
        for i in range(start, len(nums)):
            path.append(nums[i])
            backtrack(i + 1)
            path.pop()

    backtrack(0)
    return out
```

3. Because every prefix is a valid subset, you snapshot at every recursion *entry*, not just at leaves.

**Examples:** Subsets (LC 78), Subsets II (LC 90 with duplicates), Combinations (LC 77).

### Flavor 2: Permutation (used-set tracking)

Permutations differ from subsets in that **order matters** and **every position must be filled**. The shared state is a `used` set (or boolean array) indicating which elements have been picked.

```python
def permute(nums: list[int]) -> list[list[int]]:
    out: list[list[int]] = []
    path: list[int] = []
    used: list[bool] = [False] * len(nums)

    def backtrack() -> None:
        if len(path) == len(nums):
            out.append(path.copy())
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            used[i] = True
            path.append(nums[i])
            backtrack()
            path.pop()
            used[i] = False

    backtrack()
    return out
```

The duplicate-handling extension (LC 47):

```python
def permute_unique(nums: list[int]) -> list[list[int]]:
    nums.sort()                                # (1) cluster duplicates
    out: list[list[int]] = []
    path: list[int] = []
    used: list[bool] = [False] * len(nums)

    def backtrack() -> None:
        if len(path) == len(nums):
            out.append(path.copy())
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            # (2) Skip duplicate-of-prev unless the prev one was used (i.e., we're
            # already on a "this duplicate group" path).
            if i > 0 and nums[i] == nums[i - 1] and not used[i - 1]:
                continue
            used[i] = True
            path.append(nums[i])
            backtrack()
            path.pop()
            used[i] = False

    backtrack()
    return out
```

1. Sorting clusters duplicates so the skip rule (line 2) can detect them.
2. The `not used[i-1]` predicate is the cleanest correct way to say *"only the leftmost unused duplicate may start a new path at this depth."* See Deep-dive 2 for the proof.

**Examples:** Permutations (LC 46), Permutations II (LC 47), Letter Tile Possibilities (LC 1079).

### Flavor 3: Partition / constraint backtracking

Sometimes the recursion isn't "choose one of n elements" but "choose where to **cut** an input." Palindrome Partitioning, Word Break II, Restore IP Addresses, Generate Parentheses — all share this shape.

```python
def palindrome_partition(s: str) -> list[list[str]]:
    out: list[list[str]] = []
    path: list[str] = []

    def is_palindrome(left: int, right: int) -> bool:
        while left < right:
            if s[left] != s[right]:
                return False
            left += 1
            right -= 1
        return True

    def backtrack(start: int) -> None:
        if start == len(s):
            out.append(path.copy())
            return
        for end in range(start, len(s)):       # (1) cut s[start..end]
            if is_palindrome(start, end):      # (2) prune: only recurse on valid prefix
                path.append(s[start : end + 1])
                backtrack(end + 1)
                path.pop()

    backtrack(0)
    return out
```

1. The choice is "where does this segment end?"
2. **Pruning at the gate.** If the current cut isn't a palindrome, don't even recurse — the entire subtree is wasted work.

**Examples:** Palindrome Partitioning (LC 131), Word Break II (LC 140), Restore IP Addresses (LC 93), Generate Parentheses (LC 22), N-Queens (LC 51), Sudoku Solver (LC 37).

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Include/exclude | Each element in or out | Subsets (LC 78) | Two recursive calls per element |
| 2 | Subsets with duplicates | Same, but skip duplicate paths | Subsets II (LC 90) | Sort, then `i > start and nums[i] == nums[i-1]: skip` |
| 3 | Permutation (used-set) | Pick any unused element next | Permutations (LC 46) | `used: list[bool]` |
| 4 | Permutation with duplicates | Skip duplicates at same depth | Permutations II (LC 47) | Sort + `not used[i-1]` skip rule |
| 5 | Combination Sum | Reuse / no-reuse from candidates | Combination Sum (LC 39, 40) | Pass `start` (no reuse) or `i` (reuse OK) |
| 6 | Partition-style | Choose a cut, recurse on suffix | Palindrome Partitioning (LC 131) | Validate prefix, recurse on `end+1` |
| 7 | Constraint-based | Validate a board state | N-Queens (LC 51) | Maintain `cols / diag1 / diag2` sets |

---

## 📋 Twenty problems on this pattern

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Subsets | 78 | <span class="diff-medium">Medium</span> | Include/exclude | 📝 |
| 2 | Subsets II | 90 | <span class="diff-medium">Medium</span> | Subsets with duplicates | 📝 |
| 3 | Permutations | 46 | <span class="diff-medium">Medium</span> | Permutation | 📝 |
| 4 | Permutations II | 47 | <span class="diff-medium">Medium</span> | Permutation with duplicates | 📝 |
| 5 | Combinations | 77 | <span class="diff-medium">Medium</span> | Include/exclude | 📝 |
| 6 | Combination Sum | 39 | <span class="diff-medium">Medium</span> | Combination Sum (reuse) | 📝 |
| 7 | Combination Sum II | 40 | <span class="diff-medium">Medium</span> | Combination Sum (no reuse) | 📝 |
| 8 | Combination Sum III | 216 | <span class="diff-medium">Medium</span> | Combination + size constraint | 📝 |
| 9 | Letter Combinations of Phone Number | 17 | <span class="diff-medium">Medium</span> | Cartesian product | 📝 |
| 10 | Generate Parentheses | 22 | <span class="diff-medium">Medium</span> | Partition-style | 📝 |
| 11 | Palindrome Partitioning | 131 | <span class="diff-medium">Medium</span> | Partition-style | 📝 |
| 12 | Word Break II | 140 | <span class="diff-hard">Hard</span> | Partition-style + memo | 📝 |
| 13 | Restore IP Addresses | 93 | <span class="diff-medium">Medium</span> | Partition-style + 4-segment | 📝 |
| 14 | N-Queens | 51 | <span class="diff-hard">Hard</span> | Constraint-based | 📝 |
| 15 | N-Queens II | 52 | <span class="diff-hard">Hard</span> | Constraint-based (count) | 📝 |
| 16 | Sudoku Solver | 37 | <span class="diff-hard">Hard</span> | Constraint-based | 📝 |
| 17 | Word Search | 79 | <span class="diff-medium">Medium</span> | Grid DFS + visited | 📝 |
| 18 | Word Search II | 212 | <span class="diff-hard">Hard</span> | Grid DFS + Trie | 📝 |
| 19 | Beautiful Arrangement | 526 | <span class="diff-medium">Medium</span> | Permutation with constraint | 📝 |
| 20 | Expression Add Operators | 282 | <span class="diff-hard">Hard</span> | Partition + arithmetic | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Subsets (LC 78)

> Given a list of distinct integers `nums`, return all possible subsets (the power set). Order doesn't matter; no duplicate subsets in the output.

#### Code (start-index version)

```python
def subsets(nums: list[int]) -> list[list[int]]:
    out: list[list[int]] = []
    path: list[int] = []

    def backtrack(start: int) -> None:
        out.append(path.copy())
        for i in range(start, len(nums)):
            path.append(nums[i])
            backtrack(i + 1)
            path.pop()

    backtrack(0)
    return out
```

#### Dry run on `nums = [1, 2, 3]`

The recursion tree (each node = one `backtrack(start)` call; emitted subset shown next to it):

```
backtrack(0)            → emits []
├─ pick 1, backtrack(1) → emits [1]
│  ├─ pick 2, bt(2)     → emits [1, 2]
│  │  └─ pick 3, bt(3)  → emits [1, 2, 3]
│  └─ pick 3, bt(3)     → emits [1, 3]
├─ pick 2, backtrack(2) → emits [2]
│  └─ pick 3, bt(3)     → emits [2, 3]
└─ pick 3, backtrack(3) → emits [3]
```

`out = [[], [1], [1,2], [1,2,3], [1,3], [2], [2,3], [3]]` — all 2³ = 8 subsets.

#### Why "every node is a subset," not "every leaf"

In the partition-style template (Flavor 3) we only emit at leaves because internal nodes don't represent complete answers. For subsets, **every prefix of choices is itself a valid subset** — `[1]` is a subset, `[1, 2]` is a subset, etc. So we emit at the top of every call.

#### Subsets II (LC 90) — duplicate-handling

```python
def subsets_with_dup(nums: list[int]) -> list[list[int]]:
    nums.sort()
    out: list[list[int]] = []
    path: list[int] = []

    def backtrack(start: int) -> None:
        out.append(path.copy())
        for i in range(start, len(nums)):
            if i > start and nums[i] == nums[i - 1]:
                continue                       # skip duplicate at this depth
            path.append(nums[i])
            backtrack(i + 1)
            path.pop()

    backtrack(0)
    return out
```

The skip rule says: at any given depth, each *value* may start at most one new branch. Sorting clusters equal values; `i > start` ensures we still allow the *first* occurrence at that depth.

#### Complexity

- **Time:** O(n · 2ⁿ) — there are 2ⁿ subsets and copying each costs O(n).
- **Space:** O(n) recursion stack + output.

---

### Deep-dive 2 — Permutations II (LC 47)

> Given a collection of numbers `nums` that might contain duplicates, return all possible *unique* permutations.

The trap: duplicates make naive `permute(nums)` produce repeats. Sorting + a clever skip rule cuts the duplicates without missing any unique permutation.

#### Code (re-stated)

```python
def permute_unique(nums: list[int]) -> list[list[int]]:
    nums.sort()
    out: list[list[int]] = []
    path: list[int] = []
    used: list[bool] = [False] * len(nums)

    def backtrack() -> None:
        if len(path) == len(nums):
            out.append(path.copy())
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            if i > 0 and nums[i] == nums[i - 1] and not used[i - 1]:
                continue
            used[i] = True
            path.append(nums[i])
            backtrack()
            path.pop()
            used[i] = False

    backtrack()
    return out
```

#### Why `not used[i - 1]` and not `used[i - 1]`?

Both look plausible — most candidates pick wrong on the first try. Let's prove `not used[i - 1]` by example.

Take `nums = [1, 1, 2]` (already sorted). Index 0 = first `1`, index 1 = second `1`, index 2 = `2`.

At depth 0 (path=[]) we iterate i = 0, 1, 2:

- i=0: pick first 1. Recurse.
- i=1: `nums[1] == nums[0]`. Is `used[0]`? `False` (we already popped it after recursion returned). **Skip.**
- i=2: pick 2. Recurse.

This is correct: at depth 0, we want exactly *one* of the two 1's to start a new branch. The leftmost unused duplicate gets to.

Inside the i=0 recursion, depth 1, path=[1], `used = [T, F, F]`:
- i=0: used → skip.
- i=1: `nums[1] == nums[0]`. Is `used[0]`? **True** — we *are* on the "first 1" branch and the second 1 is filling in *behind* us. **Don't skip.** Pick second 1. Recurse.
- i=2: pick 2.

So permutations starting with 1 include `[1, 1, 2]` and `[1, 2, 1]`. ✓

If we had instead written `if … used[i - 1]: continue`, at depth 0 we'd let *both* 1's start branches (both have `used[i-1] = False`), producing duplicate top-level permutations.

#### Dry run sketch on `nums = [1, 1, 2]`

The recursion produces exactly 3 unique permutations: `[1,1,2]`, `[1,2,1]`, `[2,1,1]`. Without the skip rule we'd get 6 (each with the two 1's interchangeable but indistinguishable).

#### Complexity

- **Time:** O(n · n!) worst case (no duplicates).
- **Space:** O(n) for `path`, `used`, recursion.

---

### Deep-dive 3 — Palindrome Partitioning (LC 131)

> Given a string `s`, partition it such that every substring of the partition is a palindrome. Return all possible palindrome partitionings.

The canonical partition-style backtracking. The "choice" at each step is *where to put the next cut*.

#### Code (re-stated)

```python
def palindrome_partition(s: str) -> list[list[str]]:
    out: list[list[str]] = []
    path: list[str] = []

    def is_palindrome(left: int, right: int) -> bool:
        while left < right:
            if s[left] != s[right]:
                return False
            left += 1
            right -= 1
        return True

    def backtrack(start: int) -> None:
        if start == len(s):
            out.append(path.copy())
            return
        for end in range(start, len(s)):
            if is_palindrome(start, end):
                path.append(s[start : end + 1])
                backtrack(end + 1)
                path.pop()

    backtrack(0)
    return out
```

#### Dry run on `s = "aab"`

The decision tree (each node = one `backtrack(start)` call):

```
bt(0): try cuts s[0..0]="a"✓, s[0..1]="aa"✓, s[0..2]="aab"✗
├─ "a" → bt(1): try s[1..1]="a"✓, s[1..2]="ab"✗
│        └─ "a" → bt(2): try s[2..2]="b"✓
│                  └─ "b" → bt(3): emit ["a","a","b"]
└─ "aa" → bt(2): try s[2..2]="b"✓
          └─ "b" → bt(3): emit ["aa","b"]
```

Output: `[["a","a","b"], ["aa","b"]]` ✓.

#### The pruning win

If `is_palindrome(start, end)` fails, we **don't recurse**. That cuts off the entire subtree of "what if I extend with a non-palindrome prefix?" — these would all be invalid eventually, but pruning at the gate avoids exploring them at all.

For pathological inputs like `"aaaaaa…"` the recursion still has 2ⁿ valid partitionings, but for inputs with few palindromes the pruning is dramatic.

#### Optimization — DP-precompute palindromes

`is_palindrome` is O(n) per call, called O(n²) times → O(n³). Precomputing a `dp[i][j]` table in O(n²) makes lookup O(1):

```python
n = len(s)
dp: list[list[bool]] = [[False] * n for _ in range(n)]
for i in range(n - 1, -1, -1):
    for j in range(i, n):
        if s[i] == s[j] and (j - i < 2 or dp[i + 1][j - 1]):
            dp[i][j] = True
```

Trade: O(n²) extra space for an O(n) speedup per call. Worth it for n ≥ ~50.

#### Complexity

- **Time:** O(n · 2ⁿ) — up to 2ⁿ partitions, each up to n characters to copy.
- **Space:** O(n) for `path` + O(n²) if using the DP table.

---

## 🐛 Common bugs

1. **`out.append(path)` instead of `out.append(path.copy())`** — the #1 backtracking bug. Every entry in `out` aliases the same list.
2. **Forgetting to pop after recursing.** The path leaks into the parent's frame; sibling iterations explore corrupted state.
3. **Permutations II: using `used[i - 1]` instead of `not used[i - 1]`.** Subtle; produces duplicates. See Deep-dive 2.
4. **Subsets II: comparing `i > 0` instead of `i > start`.** The check is "duplicate at this depth," not "duplicate anywhere." `i > start` ensures the first occurrence at the current recursion depth is allowed through.
5. **Combination Sum: passing `i + 1` when reuse is allowed** (LC 39) or `i` when reuse is forbidden (LC 40). Read the problem.
6. **Partition-style: emitting at internal nodes.** Only the leaf (where `start == len(s)`) represents a complete partitioning.
7. **N-Queens: validating with O(n) row scan instead of `cols / diag1 / diag2` sets.** O(n) per cell × n² cells = O(n³). Sets give O(1) checks.
8. **Recursion limit on long strings.** Word Break II on 200-char inputs can hit Python's 1000-frame default. Use memoization (`@functools.cache`) on `(start)` if results are reusable, or convert to iterative DP.

---

## 🗣️ Interviewer phrasings to recognize

- "Find all subsets / power set." → Flavor 1.
- "All unique permutations." → Flavor 2 with sort + skip rule.
- "All ways to choose k items." → Combinations, start-index variant.
- "All palindrome partitions." → Flavor 3.
- "Place N queens / solve Sudoku." → Constraint-based; maintain conflict sets.
- "Generate all valid parentheses strings of length 2n." → Partition-style with two counters (`open_count`, `close_count`).
- "Word break — return all sentences." → Partition-style + memoization.

---

## 🧭 Connections to other patterns

- **Tree DFS** ([08-tree-dfs.md](08-tree-dfs.md)) — backtracking *is* DFS over the implicit decision tree.
- **Dynamic Programming** — when the decision tree has overlapping subproblems, memoize and you've crossed into DP. Word Break II is the textbook crossover.
- **Bitmask DP** — for n ≤ 20, you can replace the `used` boolean array with a single int and memoize the partial state.
- **BFS** — backtracking generates *all* answers; if you only want the *shortest* sequence of choices, switch to BFS over states.

---

## ✅ Self-check — 8 questions

??? question "1. Why must we copy `path` when emitting?"
    `path` is a single shared list mutated throughout the recursion. Storing references to it would give you `n` aliases to whatever state `path` ends in — usually empty. `path.copy()` snapshots the current state.

??? question "2. What's the difference between subsets, combinations, and permutations?"
    Subsets: pick any subset of the elements; order within the subset doesn't matter. Combinations: pick exactly k of the elements; order doesn't matter. Permutations: pick all elements in some order; order matters. Backtracking handles all three with small variations on the same template.

??? question "3. Why does sorting help in Subsets II / Permutations II?"
    Sorting clusters equal values together. The skip rule then needs only a single comparison `nums[i] == nums[i-1]` (constant time, local) instead of a global "have I already used this value at this depth?" set lookup.

??? question "4. In Permutations II, why isn't the rule `not used[i - 1]` symmetric to `i > start` in Subsets II?"
    Subsets II uses a `start` index because subsets are order-independent — you only ever go forward. Permutations have no `start`; every element is fair game at every position. The `used[]` array tracks *which* elements are picked; `not used[i - 1]` plays the role of "we're at the first unused duplicate at this depth."

??? question "5. When should you memoize a backtracking solution?"
    When the same `(state)` would be re-explored from multiple paths. Subsets, permutations, and combinations have *no* overlapping subproblems — all paths are distinct. Word Break II *does* — `backtrack(start)` is shared across many parent paths.

??? question "6. Generate Parentheses (LC 22) — what's the recursion?"
    Two counters: `open_count` and `close_count` (each at most n). At each step, append `'('` if `open_count < n`, append `')'` if `close_count < open_count`. Emit when both equal n. Pure constraint-based partition.

??? question "7. N-Queens — why O(1) conflict checks via sets?"
    For each placed queen at `(r, c)`, three diagonals/columns are now off-limits: column `c`, diagonal `r - c`, anti-diagonal `r + c`. Maintain three sets of these keys; check membership in O(1). Don't rescan the board.

??? question "8. How does pruning differ from memoization?"
    Pruning skips exploring a subtree because it's *guaranteed invalid* (e.g., a non-palindrome prefix in LC 131). Memoization caches the *result* of an explored subtree to avoid re-exploring. Different mechanisms; both shrink the work but for different reasons.

---

> **Next pattern up:** Modified Binary Search — find a value in a *rotated*, *infinite*, or *bitonic* sorted array; find the first/last index of a target; binary-search the answer space (page coming next).
