# Longest Common Subsequence DP

> The canonical **two-sequence** DP. `dp[i][j]` describes some property of `a[..i]` versus `b[..j]`, and the recurrence reads three neighbours: `dp[i-1][j-1]`, `dp[i-1][j]`, `dp[i][j-1]`. Once you internalise that grid shape, **Edit Distance**, **Shortest Common Supersequence**, **Distinct Subsequences**, **Min ASCII Delete Sum**, **Interleaving String**, and **Longest Increasing Subsequence** all collapse to one template with a swapped recurrence. The whole "compare two strings" interview category lives here.

<span class="phase-status phase-done">Phase 5 — Patterns</span>

---

## 📖 What is LCS-style DP?

A 2D DP whose two axes are **two sequences** (or one sequence and itself reversed, or one sequence and a sorted copy). `dp[i][j]` captures some property of the prefixes `a[..i]` and `b[..j]`:

- **Length** of the longest common subseq of `a[..i]` and `b[..j]` (LC 1143)
- **Edit distance** between `a[..i]` and `b[..j]` (LC 72)
- **Count** of times `b[..j]` appears as a subseq of `a[..i]` (LC 115)
- **Boolean** "is `c[..i+j]` an interleaving of `a[..i]` and `b[..j]`" (LC 97)
- **Min cost** of deletions/insertions to align (LC 583, LC 712)

**Recurrence shape (LCS form):**

```
dp[i][j] = dp[i-1][j-1] + 1                if a[i-1] == b[j-1]
         = max(dp[i-1][j], dp[i][j-1])     otherwise
```

The boundary row and column (`dp[0][*]` and `dp[*][0]`) represent comparing against the empty prefix — usually 0 for length, `j` or `i` for edit distance, 1 for distinct-subseq count of empty target.

**Why the (i-1, j-1) diagonal?** When the last characters match, both must be in the alignment — pair them and recurse on the strictly smaller prefix. When they don't match, at least one of them isn't in the alignment — try dropping each.

The mental model: imagine the DP table as an `(n+1) × (m+1)` grid where rows are positions in `a` and columns are positions in `b`. Each cell looks **up**, **left**, and **diagonally up-left**. Fill row-by-row, left-to-right — every dependency is already done.

!!! tip "The signal — when to reach for LCS-style DP"
    Reach for it when you see:

    - **Two sequences** and you're asked about commonality, alignment, or transformation between them.
    - "Edit distance" / "min operations to convert" / "delete to make equal."
    - "Subsequence of one is a subsequence of the other."
    - "Shortest string containing both as subseqs" / "longest string contained in both."
    - **One sequence vs sorted copy** of itself → LIS reduces to LCS.
    - **One sequence vs reverse** of itself → LPS reduces to LCS.

    Don't reach for it when:

    - The problem is single-sequence with bounded lookback — Fibonacci-style DP.
    - The recurrence is on a **single sequence's intervals** — palindromic / interval DP.
    - The two sequences are very long and you only need to know **if** they have any common element — hashing / set intersection beats O(n·m) DP.

---

## 🧩 The four flavors

### Flavor 1: Length DP — `dp[i][j] = length of LCS(a[..i], b[..j])`

The mother of the family.

```python
def longest_common_subsequence(a: str, b: str) -> int:
    """LC 1143."""
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]                    # (1) (n+1)x(m+1) — row/col 0 is empty prefix

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1                   # (2) match — pair and recurse on smaller prefix
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])        # (3) drop one end, take the better

    return dp[n][m]
```

1. The **+1 dimension** is the indexing trick. Cell `(i, j)` represents the prefix `a[:i]` (length `i`), so `a[i-1]` is the last character. The 0th row/column is the empty prefix — LCS with empty string is 0.
2. Match: extend the diagonal by one.
3. No match: take the better of "drop `a`'s last" or "drop `b`'s last."

**Examples:** LCS (LC 1143), Delete Operation for Two Strings (LC 583, answer is `n + m - 2·LCS`), Shortest Common Supersequence (LC 1092, answer length is `n + m - LCS`).

### Flavor 2: Edit-distance DP — `dp[i][j] = min ops to transform a[..i] → b[..j]`

Same grid, three-way min instead of "match-or-drop."

```python
def edit_distance(a: str, b: str) -> int:
    """LC 72."""
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i                                              # (1) delete i characters from a
    for j in range(m + 1):
        dp[0][j] = j                                              # insert j characters into a

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]                       # (2) free match — no op
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j - 1],                             # (3) replace
                    dp[i - 1][j],                                 #     delete a[i-1]
                    dp[i][j - 1],                                 #     insert b[j-1]
                )

    return dp[n][m]
```

1. **Boundary is non-zero** for edit distance. Converting an `i`-char prefix to an empty string requires `i` deletions.
2. Free match — same character at both ends, no operation needed. Inherit the answer from the smaller prefix.
3. Three operations, each costs 1: replace (read from diagonal), delete from `a` (read from above), insert into `a` (read from left).

**Examples:** Edit Distance (LC 72), One Edit Distance (LC 161 — special-cased to O(n)).

### Flavor 3: Counting DP — `dp[i][j] = number of ways …`

Count the alignments instead of measuring them.

```python
def num_distinct(s: str, t: str) -> int:
    """LC 115 — number of distinct subsequences of s equal to t."""
    n, m = len(s), len(t)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = 1                                              # (1) empty target — exactly one way

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i][j] = dp[i - 1][j]                               # (2) skip s[i-1]
            if s[i - 1] == t[j - 1]:
                dp[i][j] += dp[i - 1][j - 1]                      # (3) match — also add ways using s[i-1]

    return dp[n][m]
```

1. The empty target string is a subsequence of any prefix exactly once (the empty alignment).
2. Always have the option to skip `s[i-1]`. That accounts for all alignments that don't use this character.
3. If they match, additionally add all alignments that *do* use `s[i-1]` to match `t[j-1]`.

**Examples:** Distinct Subsequences (LC 115), Number of Common Subsequences variants.

### Flavor 4: LIS reduction — LCS on `a` and sorted-unique `a`

The longest increasing subsequence reduces to LCS:

```python
def length_of_lis_via_lcs(nums: list[int]) -> int:
    """LC 300 — O(n²) via LCS."""
    sorted_unique = sorted(set(nums))
    n, m = len(nums), len(sorted_unique)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if nums[i - 1] == sorted_unique[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m]
```

This is **O(n²)**, same as the standard DP for LIS. The truly fast O(n log n) LIS is patience-sorting / binary-search-on-tails — a different pattern. The LCS reduction is mostly a *connection* worth knowing, not the production solution.

**Examples:** LIS (LC 300, O(n log n) preferred), Russian Doll Envelopes (LC 354 — 2D LIS), Longest Increasing Path (LC 329 — graph DP, related but distinct).

---

## 🎒 The eight sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | LCS length | Length of common subseq | LC 1143 | `dp[i-1][j-1] + 1` if match |
| 2 | Edit distance | Min insert/delete/replace | LC 72 | 3-way min, boundary `i`/`j` |
| 3 | Distinct subseqs | Count alignments | LC 115 | Add diagonal on match, always inherit `dp[i-1][j]` |
| 4 | Shortest common supersequence | Min superseq length | LC 1092 | `n + m - LCS` length, then reconstruct |
| 5 | Delete to equal | Min deletes both sides | LC 583 | `n + m - 2·LCS` |
| 6 | Min ASCII delete sum | Weighted delete | LC 712 | `dp[i-1][j] + ord(a[i-1])` etc. |
| 7 | Interleaving boolean | `c` is interleaving of `a`, `b` | LC 97 | `dp[i][j] = (dp[i-1][j] and a[i-1] == c[i+j-1]) or (dp[i][j-1] and …)` |
| 8 | LIS as LCS | Sequence vs sorted copy | LC 300 (O(n²) form) | `LCS(arr, sorted(set(arr)))` |

---

## 📋 Twenty problems on this pattern

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Longest Common Subsequence | 1143 | <span class="diff-medium">Medium</span> | LCS length | 📝 |
| 2 | Edit Distance | 72 | <span class="diff-hard">Hard</span> | Edit distance | 📝 |
| 3 | Distinct Subsequences | 115 | <span class="diff-hard">Hard</span> | Counting | 📝 |
| 4 | Delete Operation for Two Strings | 583 | <span class="diff-medium">Medium</span> | Delete to equal | 📝 |
| 5 | Minimum ASCII Delete Sum for Two Strings | 712 | <span class="diff-medium">Medium</span> | Weighted delete | 📝 |
| 6 | Shortest Common Supersequence | 1092 | <span class="diff-hard">Hard</span> | SCS | 📝 |
| 7 | Interleaving String | 97 | <span class="diff-medium">Medium</span> | Interleaving boolean | 📝 |
| 8 | Longest Common Substring (contiguous) | — | <span class="diff-medium">Medium</span> | Substring variant | 📝 |
| 9 | Longest Increasing Subsequence | 300 | <span class="diff-medium">Medium</span> | LIS as LCS / patience | 📝 |
| 10 | Russian Doll Envelopes | 354 | <span class="diff-hard">Hard</span> | 2D LIS | 📝 |
| 11 | Number of Longest Increasing Subseqs | 673 | <span class="diff-medium">Medium</span> | LIS variant + count | 📝 |
| 12 | One Edit Distance | 161 | <span class="diff-medium">Medium</span> | Edit distance, special-cased | 📝 |
| 13 | Wildcard Matching | 44 | <span class="diff-hard">Hard</span> | Pattern-matching DP | 📝 |
| 14 | Regular Expression Matching | 10 | <span class="diff-hard">Hard</span> | Pattern-matching DP | 📝 |
| 15 | Longest Palindromic Subsequence | 516 | <span class="diff-medium">Medium</span> | LPS via LCS(s, rev(s)) | ✅ |
| 16 | Maximum Length of Repeated Subarray | 718 | <span class="diff-medium">Medium</span> | Longest common substring | 📝 |
| 17 | Uncrossed Lines | 1035 | <span class="diff-medium">Medium</span> | LCS, renamed | 📝 |
| 18 | Maximum Length of Pair Chain | 646 | <span class="diff-medium">Medium</span> | LIS variant | 📝 |
| 19 | Distinct Echo Substrings | 1316 | <span class="diff-hard">Hard</span> | LCS variant + hashing | 📝 |
| 20 | Largest Plus Sign / Maximal Square | 221 | <span class="diff-medium">Medium</span> | 2D DP cousin | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Longest Common Subsequence (LC 1143)

> Given two strings `a` and `b`, return the length of their longest common subsequence.

#### Code (re-stated)

```python
def longest_common_subsequence(a: str, b: str) -> int:
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m]
```

#### The recurrence, in words

**Match (`a[i-1] == b[j-1]`)**: pair the two last characters into the LCS. The remaining problem is `LCS(a[..i-1], b[..j-1])` — strictly smaller in both axes. Add 1.

**No match**: at most one of the two characters is in the LCS. Try dropping each end and take the better:

- Drop `a`'s last → `LCS(a[..i-1], b[..j])` = `dp[i-1][j]`.
- Drop `b`'s last → `LCS(a[..i], b[..j-1])` = `dp[i][j-1]`.

**Boundaries**: LCS with the empty string is always 0. The 0th row/column is naturally 0 from the array initialiser.

#### Dry run on `a = "abcde"`, `b = "ace"`

`n = 5`, `m = 3`. Initial dp is `(6 × 4)` zeros.

|       | ε | a | c | e |
|-------|---|---|---|---|
| **ε** | 0 | 0 | 0 | 0 |
| **a** | 0 | 1 | 1 | 1 |
| **b** | 0 | 1 | 1 | 1 |
| **c** | 0 | 1 | 2 | 2 |
| **d** | 0 | 1 | 2 | 2 |
| **e** | 0 | 1 | 2 | 3 |

Walk through a few:

- `(1,1)`: `a == a` → `dp[0][0] + 1 = 1`.
- `(2,1)`: `b ≠ a` → `max(dp[1][1], dp[2][0]) = max(1, 0) = 1`.
- `(3,2)`: `c == c` → `dp[2][1] + 1 = 2`.
- `(5,3)`: `e == e` → `dp[4][2] + 1 = 3`.

Output: `dp[5][3] = 3`. The LCS is `"ace"`. ✓

#### Reconstructing the LCS

The DP gives length only. To recover the string, walk backward:

```python
def lcs_string(a: str, b: str) -> str:
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    result: list[str] = []
    i, j = n, m
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            result.append(a[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return "".join(reversed(result))
```

Walk back from `(n, m)`. On match, record and step diagonally. On mismatch, follow whichever neighbour has the larger `dp` value. Reverse at the end.

#### Space optimisation: O(min(n, m))

`dp[i][j]` only reads `dp[i-1][*]` and `dp[i][*]` — only the previous and current row. Roll to two 1D arrays:

```python
def lcs_rolled(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a                                               # ensure b is the shorter
    n, m = len(a), len(b)
    prev = [0] * (m + 1)
    curr = [0] * (m + 1)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev, curr = curr, prev
        for k in range(m + 1):
            curr[k] = 0                                           # reset reused buffer
    return prev[m]
```

Rolling kills reconstruction (no full table to walk back). Use the full 2D form if you need the actual subsequence.

#### Complexity

- **Time:** O(n·m). Two nested loops, constant work per cell.
- **Space:** O(n·m) for the table; O(min(n, m)) rolled. Reconstruction needs the full table.

---

### Deep-dive 2 — Edit Distance (LC 72)

> Given two strings `a` and `b`, return the minimum number of operations (insert, delete, replace, each costing 1) to convert `a` into `b`.

#### Code (re-stated)

```python
def edit_distance(a: str, b: str) -> int:
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j - 1],                             # replace
                    dp[i - 1][j],                                 # delete from a
                    dp[i][j - 1],                                 # insert into a
                )

    return dp[n][m]
```

#### Reading each operation off the recurrence

The grid axes: rows = positions in `a`, columns = positions in `b`. Each cell `(i, j)` says "min ops to turn the first `i` chars of `a` into the first `j` chars of `b`."

- **Match** (`a[i-1] == b[j-1]`): the last character is already correct. No op. Inherit from `dp[i-1][j-1]`.
- **Replace**: change `a[i-1]` to `b[j-1]`. The first `i-1` chars of `a` must already equal the first `j-1` chars of `b`. Cost: `1 + dp[i-1][j-1]`.
- **Delete from `a`**: drop `a[i-1]`. The first `i-1` chars of `a` must equal the first `j` chars of `b`. Cost: `1 + dp[i-1][j]`.
- **Insert into `a`**: place `b[j-1]` at the end of the partial result. The first `i` chars of `a` must equal the first `j-1` chars of `b`. Cost: `1 + dp[i][j-1]`.

#### Dry run on `a = "horse"`, `b = "ros"`

`n = 5`, `m = 3`.

|       | ε | r | o | s |
|-------|---|---|---|---|
| **ε** | 0 | 1 | 2 | 3 |
| **h** | 1 | 1 | 2 | 3 |
| **o** | 2 | 2 | 1 | 2 |
| **r** | 3 | 2 | 2 | 2 |
| **s** | 4 | 3 | 3 | 2 |
| **e** | 5 | 4 | 4 | 3 |

A few cells in detail:

- `(1,1)`: `h ≠ r` → `1 + min(dp[0][0], dp[0][1], dp[1][0]) = 1 + min(0,1,1) = 1`.
- `(2,2)`: `o == o` → `dp[1][1] = 1`.
- `(5,3)`: `e ≠ s` → `1 + min(dp[4][2], dp[4][3], dp[5][2]) = 1 + min(3,2,3) = 3`.

Output: `dp[5][3] = 3`. ✓ (`horse → rorse → rose → ros`.)

#### Why we read **three** neighbours, not two

For LCS, mismatch reads only above and left. For edit distance, mismatch also reads the **diagonal** (replace operation). The replace operation is unique to edit-distance-style problems where you can "transform" a character in place.

#### Variations: weighted edits

If insert / delete / replace have different costs (LC 712 uses ASCII as cost), swap each `1` for the operation's cost. The shape of the recurrence is identical.

#### Complexity

- **Time:** O(n·m).
- **Space:** O(n·m); rollable to O(min(n, m)) when reconstruction isn't needed.

---

### Deep-dive 3 — Distinct Subsequences (LC 115)

> Given strings `s` and `t`, return the number of distinct subsequences of `s` that equal `t`.

This is the **counting** flavour of LCS. Same grid, different recurrence.

#### Code (re-stated)

```python
def num_distinct(s: str, t: str) -> int:
    n, m = len(s), len(t)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = 1                                              # empty target — one way (the empty alignment)

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i][j] = dp[i - 1][j]                               # skip s[i-1]
            if s[i - 1] == t[j - 1]:
                dp[i][j] += dp[i - 1][j - 1]                      # match — also use s[i-1]

    return dp[n][m]
```

#### Why this recurrence is *not* a max

For length, you take the **best** alignment. For counting, you take the **sum** over disjoint cases. Every alignment either uses `s[i-1]` to match `t[j-1]` (only possible if they match) or it doesn't. These cases don't overlap, so add.

- **Skip `s[i-1]`**: alignments using only `s[..i-1]`. That's `dp[i-1][j]`.
- **Use `s[i-1]` to match `t[j-1]`** (only when `s[i-1] == t[j-1]`): alignments using only `s[..i-1]` to match `t[..j-1]`, with this one extra pair appended. That's `dp[i-1][j-1]`.

Total: `dp[i-1][j] + (dp[i-1][j-1] if match else 0)`.

#### Boundary subtlety

`dp[0][0] = 1` (empty matches empty in one way). `dp[0][j > 0] = 0` (can't form a non-empty target from an empty source). `dp[i][0] = 1` for all `i ≥ 0` (empty target always matches in one way — by skipping all of `s`).

The natural array init handles `dp[0][j > 0] = 0`. The explicit loop sets `dp[i][0] = 1`.

#### Dry run on `s = "rabbbit"`, `t = "rabbit"`

`n = 7`, `m = 6`.

|       | ε | r | a | b | b | i | t |
|-------|---|---|---|---|---|---|---|
| **ε** | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| **r** | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| **a** | 1 | 1 | 1 | 0 | 0 | 0 | 0 |
| **b** | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| **b** | 1 | 1 | 1 | 2 | 1 | 0 | 0 |
| **b** | 1 | 1 | 1 | 3 | 3 | 0 | 0 |
| **i** | 1 | 1 | 1 | 3 | 3 | 3 | 0 |
| **t** | 1 | 1 | 1 | 3 | 3 | 3 | 3 |

Selected cells:

- `(5, 4)`: `s[4] = 'b'`, `t[3] = 'b'` → match. `dp[4][4] + dp[4][3] = 1 + 2 = 3`.
- `(6, 4)`: `s[5] = 'b'`, `t[3] = 'b'` → match. `dp[5][4] + dp[5][3] = 1 + 2... wait, recompute.`

Recompute `(6,4)`: `s[5] = 'b'`, `t[3] = 'b'` → match. `dp[6][4] = dp[5][4] + dp[5][3] = 1 + 2 = 3`. ✓

- `(7, 6)`: `s[6] = 'i'`, `t[5] = 't'` → no match. `dp[7][6] = dp[6][6] = 0`. Wait, that gives 0 but the answer should be 3.

Re-check: `t = "rabbit"`, length 6. `s = "rabbbit"`, length 7. We need `dp[7][6]`. `s[6] = 't'` (last char), `t[5] = 't'` → match. `dp[7][6] = dp[6][6] + dp[6][5] = 0 + 3 = 3`. ✓

Output: 3. The three alignments use the three positions of `'b'` in `s` for the second `'b'` in `t`.

#### Why this *isn't* the same as `comb(n, m)`

The matching positions matter, not just the lengths. Different problems give wildly different counts.

#### Complexity

- **Time:** O(n·m).
- **Space:** O(n·m); rollable to O(m) since each row only reads the previous row.

---

## 🐛 Common bugs

1. **Off-by-one on the index.** `a[i-1]` is the *last* character of the prefix `a[:i]`. Using `a[i]` will index out of bounds and silently miscompute. The +1 dimensioning is the convention; stick with it.
2. **Wrong boundary.** LCS has 0-row/0-column = 0. Edit distance has `dp[i][0] = i`, `dp[0][j] = j`. Distinct subseqs has `dp[i][0] = 1`. Mixing them produces silently wrong answers.
3. **Reading three neighbours when two suffice (or vice versa).** LCS reads only above + left + diagonal-on-match. Edit distance reads all three on mismatch. Distinct subseqs reads only above (always) + diagonal-on-match.
4. **Returning `dp[n-1][m-1]` instead of `dp[n][m]`.** With +1 dimensioning, the answer cell is `(n, m)`, not `(n-1, m-1)`.
5. **Rolling array reset bug.** When rolling to 1D, you must clear the buffer between rows for max/min DPs. For purely additive DPs (counting), the assignment overwrites — but the boundary `dp[i][0]` must be set fresh each row.
6. **Replace cost vs match cost in edit distance.** On `a[i-1] == b[j-1]`, the cost is `dp[i-1][j-1]` (free), not `1 + dp[i-1][j-1]` (replace). Forgetting the free-match branch makes every diagonal cost 1.
7. **LCS confused with LCSubstring.** Subsequence allows skipping; substring is contiguous. The substring DP zeros out on mismatch (no carryover); the subsequence DP propagates the max. Using the wrong recurrence is one of the most common interview blunders.
8. **Allocating `(n) × (m)` instead of `(n+1) × (m+1)`.** The +1 row/column for the empty prefix is what makes the boundary clean. Skipping it forces special-casing `i = 0` and `j = 0` inside the inner loop.
9. **Distinct subseq overflow.** LC 115 answers fit in 32 bits but counts can still grow large. In Python it's fine; in C++/Java use `int`/`long` carefully. Modular variants exist (LC 940 — distinct subseqs of `s`).

---

## 🗣️ Interviewer phrasings to recognize

- "Length of **longest common subsequence**." → LC 1143, classic LCS.
- "**Edit distance** / Levenshtein distance / min ops to convert." → LC 72, three-way min.
- "**Number of ways** to form one string from another." → LC 115, counting flavour.
- "**Min deletions** to make two strings equal." → LC 583, `n + m - 2·LCS`.
- "**Shortest superseq** containing both as subseqs." → LC 1092, length is `n + m - LCS`.
- "Is `c` an **interleaving** of `a` and `b`?" → LC 97, boolean LCS variant.
- "**Longest increasing subsequence**." → LC 300; LCS reduction is one solution, patience-sorting is faster.
- "**Wildcard / regex matching**." → LC 44, LC 10. Pattern-DP cousins.

---

## 🧭 Connections to other patterns

- **Palindromic Subsequence DP** ([18-palindromic-subsequence-dp.md](18-palindromic-subsequence-dp.md)) — `LPS(s) = LCS(s, reverse(s))`. Both are 2D DPs; LPS is single-axis interval, LCS is two-axis.
- **0/1 Knapsack DP** ([15-01-knapsack-dp.md](15-01-knapsack-dp.md)) — both are 2D DPs but axes differ: knapsack is item × capacity, LCS is index × index.
- **Fibonacci Numbers DP** ([17-fibonacci-numbers-dp.md](17-fibonacci-numbers-dp.md)) — single-axis with constant lookback. LCS extends it to two-axis with constant lookback in two directions.
- **Modified Binary Search** ([11-modified-binary-search.md](11-modified-binary-search.md)) — patience-sorting LIS is binary-search-on-tails, the O(n log n) alternative to the O(n²) LCS form for LIS.
- **String Pattern Matching** — Wildcard (LC 44) and Regex (LC 10) are pattern-DP cousins; same grid shape, more recurrence cases.

---

## ✅ Self-check — 8 questions

??? question "1. Why is the DP table dimensioned (n+1) × (m+1), not n × m?"
    The 0th row and 0th column represent the **empty prefix**. The boundary case (LCS with empty string = 0; edit distance to/from empty = i or j; distinct subseqs of empty target = 1) sits naturally there. Without the extra row/column you have to special-case `i = 0` and `j = 0` inside the inner loop.

??? question "2. What's the recurrence for LCS, and why three reads?"
    Match: `dp[i][j] = dp[i-1][j-1] + 1` (pair both ends). No match: `dp[i][j] = max(dp[i-1][j], dp[i][j-1])` (drop one end). Three reads because the recurrence considers three subproblems — pair both, drop a's last, drop b's last — but only one is taken on match.

??? question "3. How does LCS reduce to LPS? And LIS to LCS?"
    `LPS(s) = LCS(s, reverse(s))` — a palindromic subseq of `s` is a subseq of both `s` and its reverse. `LIS(arr) = LCS(arr, sorted(set(arr)))` — an increasing subseq of `arr` is a subseq of both `arr` and the sorted unique version. Both reductions land on the same grid shape.

??? question "4. Why does Edit Distance have boundary `dp[i][0] = i` while LCS has `dp[i][0] = 0`?"
    Edit distance from a length-`i` prefix to the empty string requires `i` deletions. LCS with the empty string is 0 because there are no common characters. The boundary encodes the *meaning* of the table.

??? question "5. Can LCS run in O(min(n, m)) space?"
    Yes — each row only reads the previous row. Roll to two 1D arrays of length `min(n, m) + 1`. You lose the ability to reconstruct the LCS string (the full table is gone), so use the rolled form when only the length matters.

??? question "6. Why does Distinct Subsequences (LC 115) sum instead of max?"
    For length, you pick the *best* alignment. For count, you sum over *disjoint* cases. Every distinct alignment either uses `s[i-1]` or doesn't — those are non-overlapping, so add the counts.

??? question "7. What changes in the recurrence for LCSubstring (contiguous) vs LCSubsequence?"
    LCSubstring: on match, `dp[i][j] = dp[i-1][j-1] + 1`. On mismatch, `dp[i][j] = 0` (a non-matching pair *breaks* the run). The answer is the **max** over the entire table, not `dp[n][m]`. LCSubseq: on mismatch, propagate the better of `dp[i-1][j]` / `dp[i][j-1]` — the run can recover by skipping characters.

??? question "8. Why is the LCS reduction for LIS only O(n²) when patience-sorting gives O(n log n)?"
    The LCS DP itself is O(n·m). For LIS reduction, `m = n` (sorted unique copy), giving O(n²). Patience-sorting maintains an array of "tails of increasing subseqs of each length" and binary-searches each new element into that array — O(log n) per element, O(n log n) total. The LCS form is mostly pedagogical; the patience-sorting form is what production code uses.

---

> **Next pattern up:** Bitwise XOR — the last canonical pattern. Single Number variants, missing-number tricks, and the "two numbers appearing once among duplicates" classics. The series will then close with summary index updates and a `What's next?` page (page coming next).
