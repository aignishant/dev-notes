# Backtracking — common across all companies

> Try a choice, recurse, undo. The most underrated interview superpower.

<span class="company-tag">Google</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">TCS</span> &nbsp; <span class="company-tag">ISRO</span> &nbsp; <span class="phase-status phase-done">Phase 14 — Common Across</span>

---

Backtracking is depth-first search through a decision tree where you **mutate** state on the way down and **undo** on the way up. Almost every problem is the same skeleton — pick what to add to `path`, recurse, pop. The interesting parts are pruning (skip branches that can't yield answers) and de-duplication (sort + skip-equal-prev). If you understand `path.append → recurse → path.pop`, you're 80% there.

## Pattern frequency

| Pattern | Frequency | Typical signal |
|---|---|---|
| Subsets / power set | ⭐⭐⭐⭐⭐ | "all subsets", "all combinations" |
| Permutations | ⭐⭐⭐⭐ | "all orderings", "anagram-like" |
| Combination sum | ⭐⭐⭐⭐ | "all combinations summing to target" |
| Grid backtracking | ⭐⭐⭐⭐ | word search, N-queens, sudoku |
| Partitioning | ⭐⭐⭐ | palindrome partition, IP addresses |
| With Trie | ⭐⭐⭐ | word search II — many words at once |

## Problem set

| # | Problem | Difficulty | Pattern | LeetCode |
|---|---|---|---|---|
| 1 | Subsets | Medium | Pick / skip | 78 |
| 2 | Subsets II (with dups) | Medium | Sort + skip-equal | 90 |
| 3 | Permutations | Medium | Used array | 46 |
| 4 | Permutations II (with dups) | Medium | Sort + skip-if-prev-not-used | 47 |
| 5 | Combinations | Medium | Pick from `start..n` | 77 |
| 6 | Combination Sum | Medium | Reuse-allowed | 39 |
| 7 | Combination Sum II | Medium | No-reuse + dedupe | 40 |
| 8 | Combination Sum III | Medium | Fixed length k | 216 |
| 9 | Combination Sum IV | Medium | DP, not backtracking | 377 |
| 10 | Letter Combinations of Phone Number | Medium | Cartesian product | 17 |
| 11 | Generate Parentheses | Medium | Open/close counts | 22 |
| 12 | Word Search | Medium | Grid DFS + mark | 79 |
| 13 | Word Search II | Hard | Trie + grid DFS | 212 |
| 14 | N-Queens | Hard | Column / diag sets | 51 |
| 15 | Sudoku Solver | Hard | Constraint propagation | 37 |
| 16 | Palindrome Partitioning | Medium | Slice + recurse | 131 |
| 17 | Restore IP Addresses | Medium | 4-segment partition | 93 |
| 18 | Word Break II | Hard | Memoized backtracking | 140 |
| 19 | Beautiful Arrangement | Medium | Used set + index | 526 |

---

## Deep-dive 1 — Permutations II (LC 47) — handling duplicates

??? question "Why is dedup tricky here?"
    For `[1, 1, 2]`, the two `1`s are *indistinguishable* — `[1ₐ, 1ᵦ, 2]` and `[1ᵦ, 1ₐ, 2]` are the *same* permutation. Without care you'll output each one twice. The trick is to enforce a canonical *order of consumption* among duplicates: a duplicate may be used only if its identical predecessor (in the sorted array) has already been used in this branch.

The canonical "skip equal prev not used" idiom:

1. **Sort** `nums` so equal values are adjacent.
2. Maintain a `used: list[bool]`.
3. At each level, iterate through indices. To pick `nums[i]`:
    - It must not already be used.
    - **And** if `nums[i] == nums[i-1]` and `nums[i-1]` is *not* used, skip — because that means the predecessor is available but we're trying to use the later duplicate first, which would create a redundant branch.

```python linenums="1"
from __future__ import annotations


class Solution:
    def permuteUnique(self, nums: list[int]) -> list[list[int]]:
        nums.sort()                                 # (1) duplicates now adjacent
        result: list[list[int]] = []
        path: list[int] = []
        used = [False] * len(nums)

        def backtrack() -> None:
            if len(path) == len(nums):
                result.append(path.copy())          # (2) snapshot — path is mutated
                return

            for i in range(len(nums)):
                if used[i]:
                    continue
                # The dedup rule: skip a duplicate when its identical
                # predecessor at i-1 has NOT been used in this branch.
                if i > 0 and nums[i] == nums[i - 1] and not used[i - 1]:   # (3)
                    continue

                used[i] = True
                path.append(nums[i])
                backtrack()
                path.pop()                          # (4) undo
                used[i] = False

        backtrack()
        return result
```

1. Sorting is non-negotiable — the dedup check assumes equal values are adjacent.
2. `path.copy()` because `path` keeps mutating — failing to copy is the most common bug.
3. The full statement: "I'm `nums[i]`, my predecessor is the same value, and they haven't been used. Skip me — let the predecessor go first." This forces a left-to-right consumption order among duplicates.
4. The "undo" half of every backtracking template — the symmetric of `append`.

??? note "Complexity"
    - Time **O(n · n!)** worst case — `n!` permutations, each O(n) to copy.
    - In practice the dedup pruning brings this down sharply.
    - Space **O(n)** recursion + `used`, plus O(answer-size) for output.

??? tip "Why `not used[i-1]` and not `used[i-1]`?"
    Both conditions can dedupe — but `not used[i-1]` is the more common pattern and tends to prune *earlier* in the tree. `used[i-1]` works but explores more branches before pruning. Stick with `not used[i-1]`.

---

## Deep-dive 2 — Word Search (LC 79) — backtracking on a grid

??? question "Why this is the canonical grid-backtracking template"
    It teaches three things every grid-backtracking problem needs: (1) recurse into 4 neighbors, (2) **mark visited in place** to avoid an extra `visited` set, (3) **unmark on the way up** so other paths can reuse the cell. Once you nail this, N-Queens, Sudoku, and Word Search II are variations on the theme.

The plan:

- For each starting cell `(r, c)`, run a DFS attempting to spell `word`.
- At depth `i`, we need `grid[r][c] == word[i]`.
- To prevent revisiting the same cell within this path, **temporarily overwrite** `grid[r][c]` with a sentinel (`'#'`) — and restore on the way out.
- Recurse into 4 neighbors. If any returns `True`, propagate up.

```python linenums="1"
from __future__ import annotations


class Solution:
    def exist(self, board: list[list[str]], word: str) -> bool:
        rows, cols = len(board), len(board[0])

        def dfs(r: int, c: int, i: int) -> bool:
            # Found the whole word — done.
            if i == len(word):
                return True
            # Out of bounds or mismatch — this branch fails.
            if (
                r < 0 or r >= rows
                or c < 0 or c >= cols
                or board[r][c] != word[i]
            ):
                return False

            # Mark visited in-place. (1)
            saved = board[r][c]
            board[r][c] = "#"

            # Try all 4 directions; short-circuit on first success.
            found = (
                dfs(r + 1, c, i + 1)
                or dfs(r - 1, c, i + 1)
                or dfs(r, c + 1, i + 1)
                or dfs(r, c - 1, i + 1)
            )

            # Unmark — IMPORTANT: other starting cells might need this cell. (2)
            board[r][c] = saved

            return found

        for r in range(rows):
            for c in range(cols):
                if board[r][c] == word[0] and dfs(r, c, 0):     # (3)
                    return True
        return False
```

1. The in-place mark/unmark trick avoids an O(R·C) `visited` set. Mention this in the interview — interviewers love space-saving moves.
2. Forgetting the unmark is the most common bug. Without it, the algorithm becomes *non-backtracking* and silently wrong on later starts.
3. Tiny pruning win: only start DFS where `board[r][c] == word[0]`.

??? note "Complexity"
    Let `N = R · C`, `L = len(word)`.

    - Time **O(N · 4^L)** worst case — every cell can start a DFS that branches 4 ways for L levels (in practice 3 — we never go back).
    - Space **O(L)** recursion depth.

??? tip "Word Search II (LC 212) optimisation"
    For *many* words, don't rerun Word Search per word — that's O(W · N · 4^L). Build a **Trie** of all words, then DFS the grid once: at each step, advance through the Trie. Prune dead Trie branches as you find words. Drops it to roughly **O(N · 4^L)** with `L` = max word length.

    ```python linenums="1"
    # Sketch: build a Trie of words, then DFS the grid passing the current Trie node.
    if char not in trie_node.children: return  # prune
    ...
    if trie_node.word: result.add(trie_node.word); trie_node.word = None  # avoid dups
    ```

---

## Common gotchas

!!! warning "Things that bite people"
    - **Forgetting the snapshot** — `result.append(path)` instead of `result.append(path.copy())`. Then every entry in `result` ends up empty (or all the same).
    - **Forgetting the undo** — for in-place grid marking, missing `board[r][c] = saved` makes one path corrupt all later paths.
    - **Subsets II / Combination Sum II dedup** — same `not used[i-1]` idiom *or* the `if i > start and nums[i] == nums[i-1]: continue` variant. Both work; pick one and stick with it.
    - **N-Queens** — track `cols`, `diag1` (r+c), `diag2` (r-c) as sets — O(1) attack check vs O(n) per row.
    - **Generate Parentheses** — invariants are `open < n` (can open) and `close < open` (can close). Don't track via string scanning.
    - **Word Break II** — pure backtracking is exponential. Memoize on remaining suffix.

## 🃏 Cheatsheet

| Move | When | Skeleton |
|---|---|---|
| Subsets | "all subsets" | `path.append; backtrack(i+1); path.pop` for each `i` from `start` |
| Permutations | "all orderings" | `used` array; iterate all indices; mark/unmark |
| Permutations II / Subsets II | with duplicates | sort + `if nums[i]==nums[i-1] and not used[i-1]: continue` |
| Combination sum (reuse) | unlimited use | recurse with `start=i` (not `i+1`) |
| Grid DFS | word search, N-queens | mark in place, recurse 4 dirs, **unmark** |
| Open/close count | parentheses | `if open<n: rec(...,'(',open+1); if close<open: rec(...,')',close+1)` |
| Partition | palindrome / IP | for `end in range(start+1, len(s)+1)`: validate slice, recurse |

??? tip "Universal backtracking template"
    ```python linenums="1"
    def backtrack(state):
        if is_goal(state):
            result.append(snapshot(state))
            return
        for choice in choices(state):
            if not valid(choice, state):     # pruning lives here
                continue
            apply(choice, state)             # mutate
            backtrack(state)
            undo(choice, state)              # symmetric undo
    ```
    Every problem in this section is a recoloring of those seven lines. Burn them in.
