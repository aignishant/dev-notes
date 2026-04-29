# Palindromic Subsequence DP

> The first **interval DP** in the bible: `dp[i][j]` describes some property of the substring `s[i..j]`, and the recurrence reads strictly *smaller* intervals (`dp[i+1][j-1]`, `dp[i+1][j]`, `dp[i][j-1]`). The trick that ties the family together is the **diagonal-by-diagonal fill order** — outer loop over interval *length*, inner loop over the left endpoint. Once that's internalised, Longest Palindromic Subsequence (LC 516), Longest Palindromic Substring (LC 5), Min Insertions to Make Palindrome (LC 1312), and Palindrome Partitioning II (LC 132) all collapse to one-page solutions.

<span class="phase-status phase-done">Phase 5 — Patterns</span>

---

## 📖 What is palindromic subsequence DP?

A **palindrome** reads the same forwards and backwards. A **subsequence** keeps order but can skip characters; a **substring** is contiguous. The two families are structurally similar but differ in one critical recurrence step.

**State:** `dp[i][j]` = some property of `s[i..j]` (inclusive on both ends). The property changes per problem:

- **Length** of longest palindromic subseq in `s[i..j]` (LC 516)
- **Boolean** is-palindrome on `s[i..j]` (LC 5, LC 647)
- **Count** of palindromic subsequences in `s[i..j]` (LC 730)
- **Min cuts** to partition `s[..j]` into palindromes (LC 132 — 1D, but interval-style underneath)

**Recurrence shape (subsequence form):**

```
dp[i][j] = 2 + dp[i+1][j-1]              if s[i] == s[j]
         = max(dp[i+1][j], dp[i][j-1])   otherwise
```

The boundary case `i == j` (single character) is always a palindrome of length 1. The case `i > j` (empty range) has property 0.

**Why diagonal fill order?** `dp[i][j]` reads `dp[i+1][j-1]` — the cell **diagonally one down and one left**. Filling row-by-row top-down, that cell hasn't been computed yet. Filling **by interval length** (`length = j - i + 1`, from 1 up to n) guarantees every smaller interval is done before any larger one.

The mental model: imagine the DP table as a triangle (only `i ≤ j` matters). Each diagonal corresponds to a fixed length. Sweep diagonals outward from the main diagonal (length 1) to the corner (length n).

!!! tip "The signal — when to reach for palindromic-subsequence DP"
    Reach for it when you see:

    - "**Longest / shortest / count** palindromic subsequence / substring."
    - "**Minimum insertions / deletions / cuts** to make a string a palindrome."
    - The state involves a substring `s[i..j]` and the recurrence reads strictly smaller substrings.
    - Generally any problem where "the answer for s[i..j] depends on the answer for shorter intervals inside."

    Don't reach for it when:

    - The problem is single-axis 1D (Climbing Stairs, House Robber) — different pattern.
    - You need *contiguity* without palindrome structure — sliding window or two-pointer often beats it.
    - The substring property doesn't decompose to smaller intervals — different DP shape.

---

## 🧩 The three flavors

### Flavor 1: Subsequence length DP — `dp[i][j] = length of longest palindromic subseq`

The canonical interval DP. The recurrence is the recurrence the whole pattern is named after.

```python
def longest_palindrome_subseq(s: str) -> int:
    """LC 516."""
    n = len(s)
    dp = [[0] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = 1                                              # (1) single-char palindromes

    for length in range(2, n + 1):                                # (2) diagonal-by-diagonal
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                dp[i][j] = 2 + (dp[i + 1][j - 1] if length > 2 else 0)   # (3) edge case for length 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])

    return dp[0][n - 1]
```

1. Base case: every single character is a palindrome of length 1.
2. **Outer loop on length, inner on left endpoint**. This is the entire pattern's beating heart.
3. For length 2, `dp[i+1][j-1]` would be `dp[i+1][i]` — an *empty* interval. The convention is "empty interval = property 0" — but our 0-initialised table happens to give the right answer here. The explicit `if length > 2` is defensive.

**Examples:** Longest Palindromic Subsequence (LC 516), Min Insertion Steps to Make Palindrome (LC 1312 — `n - LPS(s)`).

### Flavor 2: Substring boolean DP — `dp[i][j] = is s[i..j] a palindrome?`

Boolean version. The recurrence: `s[i..j]` is a palindrome iff `s[i] == s[j]` **and** `s[i+1..j-1]` is a palindrome.

```python
def longest_palindromic_substring(s: str) -> str:
    """LC 5."""
    n = len(s)
    dp = [[False] * n for _ in range(n)]
    start, max_len = 0, 1
    for i in range(n):
        dp[i][i] = True

    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                if length == 2 or dp[i + 1][j - 1]:                # (1) base case + recurse
                    dp[i][j] = True
                    if length > max_len:
                        start, max_len = i, length

    return s[start:start + max_len]
```

1. Length 2: any matching pair is a palindrome (the inner interval is empty, trivially palindrome). Length ≥ 3: also requires the inner `dp[i+1][j-1]` to be true.

**The "expand around center" alternative** is also O(n²) but uses O(1) space — cleaner code, identical complexity. The DP form is interview-standard because it generalises smoothly to counting variants and to weighted versions.

**Examples:** Longest Palindromic Substring (LC 5), Palindromic Substrings count (LC 647), Palindrome Partitioning (LC 131 — uses the `dp[i][j]` table to drive backtracking).

### Flavor 3: 1D-rolled DP for "min cuts" / "min insertions"

Some problems express the interval recurrence as a **min over a split point**. They reduce to a 1D DP whose every cell loops over all earlier indices.

```python
def min_cuts_palindrome(s: str) -> int:
    """LC 132 — minimum cuts so each substring is a palindrome."""
    n = len(s)
    is_pal = [[False] * n for _ in range(n)]                      # (1) precompute palindrome table
    for i in range(n):
        is_pal[i][i] = True
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j] and (length == 2 or is_pal[i + 1][j - 1]):
                is_pal[i][j] = True

    dp = [0] * n                                                  # (2) dp[j] = min cuts for s[..j]
    for j in range(n):
        if is_pal[0][j]:
            dp[j] = 0                                             # whole prefix is one palindrome
        else:
            dp[j] = min(dp[i - 1] + 1 for i in range(1, j + 1) if is_pal[i][j])
    return dp[n - 1]
```

1. **Two-phase DP:** first build the boolean palindrome table (Flavor 2), then run a 1D DP that *reads* it.
2. `dp[j]` = min cuts needed for `s[0..j]`. If `s[0..j]` is itself a palindrome, zero cuts. Otherwise, find a split: `s[i..j]` is a palindrome and `s[..i-1]` was solved with `dp[i-1]` cuts.

**Examples:** Palindrome Partitioning II (LC 132), Min Insertions Steps to Make Palindrome (LC 1312 — solvable as `n - LPS` *or* via interval DP directly).

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Longest palindromic subseq | Length of LPS | LC 516 | `dp[i][j] = 2 + dp[i+1][j-1]` if match |
| 2 | Longest palindromic substring | Substring version | LC 5 | Boolean DP, return `s[start:start+max_len]` |
| 3 | Count palindromic substrings | Total count | LC 647 | Increment counter when `dp[i][j]` becomes True |
| 4 | Min insertions to palindrome | LPS reduction | LC 1312 | Answer is `n - LPS(s)` |
| 5 | Min cuts | Partition into palindromes | LC 132 | 1D DP over precomputed `is_pal` table |
| 6 | Count distinct palindromic subseqs | Distinct multisets | LC 730 | More careful interval DP with letter tracking |
| 7 | Palindrome partitioning enum | Output all partitions | LC 131 | DP table drives backtracking |

---

## 📋 Twenty problems on this pattern

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Longest Palindromic Subsequence | 516 | <span class="diff-medium">Medium</span> | Subseq length | 📝 |
| 2 | Longest Palindromic Substring | 5 | <span class="diff-medium">Medium</span> | Substring boolean | 📝 |
| 3 | Palindromic Substrings | 647 | <span class="diff-medium">Medium</span> | Count substrings | 📝 |
| 4 | Min Insertion Steps to Make a String Palindrome | 1312 | <span class="diff-hard">Hard</span> | LPS reduction | 📝 |
| 5 | Palindrome Partitioning II | 132 | <span class="diff-hard">Hard</span> | Min cuts | 📝 |
| 6 | Palindrome Partitioning | 131 | <span class="diff-medium">Medium</span> | Enumeration via DP table | 📝 |
| 7 | Palindrome Partitioning III | 1278 | <span class="diff-hard">Hard</span> | k-cuts DP | 📝 |
| 8 | Count Different Palindromic Subsequences | 730 | <span class="diff-hard">Hard</span> | Distinct count | 📝 |
| 9 | Valid Palindrome | 125 | <span class="diff-easy">Easy</span> | Two-pointer (cousin) | 📝 |
| 10 | Valid Palindrome II | 680 | <span class="diff-easy">Easy</span> | Two-pointer + skip | 📝 |
| 11 | Valid Palindrome IV | 2330 | <span class="diff-medium">Medium</span> | Two-pointer + tolerance | 📝 |
| 12 | Maximum Product of Lengths of Two Palindromic Subsequences | 2002 | <span class="diff-medium">Medium</span> | Bitmask DP | 📝 |
| 13 | Longest Palindrome (anagram) | 409 | <span class="diff-easy">Easy</span> | Counting (cousin) | 📝 |
| 14 | Shortest Palindrome | 214 | <span class="diff-hard">Hard</span> | KMP (cousin) | 📝 |
| 15 | Palindrome Pairs | 336 | <span class="diff-hard">Hard</span> | Trie + reverse pairs | 📝 |
| 16 | Find the Closest Palindrome | 564 | <span class="diff-hard">Hard</span> | Number manipulation | 📝 |
| 17 | Largest Palindrome Product | 479 | <span class="diff-hard">Hard</span> | Number manipulation | 📝 |
| 18 | Palindrome Linked List | 234 | <span class="diff-easy">Easy</span> | LL reversal (cousin) | ✅ |
| 19 | Maximize Palindrome Length From Subsequences | 1771 | <span class="diff-hard">Hard</span> | LPS variant on concat | 📝 |
| 20 | Palindrome Number | 9 | <span class="diff-easy">Easy</span> | Number manipulation | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Longest Palindromic Subsequence (LC 516)

> Given a string `s`, return the length of the longest palindromic subsequence.

The cleanest exposition of interval DP. Memorise this recurrence; the rest of the pattern is variations.

#### Code (re-stated)

```python
def longest_palindrome_subseq(s: str) -> int:
    n = len(s)
    dp = [[0] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = 1

    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                dp[i][j] = 2 + (dp[i + 1][j - 1] if length > 2 else 0)
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])

    return dp[0][n - 1]
```

#### The recurrence, in words

**Case `s[i] == s[j]`**: take both characters. The remainder is `s[i+1..j-1]`; its LPS plus 2 (for the matched pair) is the answer.

**Case `s[i] != s[j]`**: at most one of them is in the LPS. Try dropping each end and recurse: `max(dp[i+1][j], dp[i][j-1])`.

**Edge case (length = 2)**: `dp[i+1][j-1]` would be `dp[i+1][i]`, an "empty interval." Convention: empty interval has LPS 0; with matching ends the answer is 2 (just the pair).

#### Dry run on `s = "bbbab"`

`n = 5`. Initial dp (all zeros, diagonal = 1):

```
    0 1 2 3 4
  +-----------
0 | 1 . . . .
1 | _ 1 . . .
2 | _ _ 1 . .
3 | _ _ _ 1 .
4 | _ _ _ _ 1
```

(Cells below the diagonal are unused.)

**length = 2:**

| (i, j) | s[i], s[j] | match? | dp[i][j] |
|--------|------------|--------|----------|
| (0, 1) | b, b | yes | 2 |
| (1, 2) | b, b | yes | 2 |
| (2, 3) | b, a | no | max(dp[3][3], dp[2][2]) = 1 |
| (3, 4) | a, b | no | max(dp[4][4], dp[3][3]) = 1 |

**length = 3:**

| (i, j) | s[i], s[j] | match? | dp[i][j] |
|--------|------------|--------|----------|
| (0, 2) | b, b | yes | 2 + dp[1][1] = 3 |
| (1, 3) | b, a | no | max(dp[2][3], dp[1][2]) = max(1, 2) = 2 |
| (2, 4) | b, b | yes | 2 + dp[3][3] = 3 |

**length = 4:**

| (i, j) | s[i], s[j] | match? | dp[i][j] |
|--------|------------|--------|----------|
| (0, 3) | b, a | no | max(dp[1][3], dp[0][2]) = max(2, 3) = 3 |
| (1, 4) | b, b | yes | 2 + dp[2][3] = 3 |

**length = 5:**

| (i, j) | s[i], s[j] | match? | dp[i][j] |
|--------|------------|--------|----------|
| (0, 4) | b, b | yes | 2 + dp[1][3] = 4 |

Output: `dp[0][4] = 4`. The LPS is `"bbbb"` (positions 0, 1, 2, 4). ✓

#### The diagonal sweep — why it works

`dp[i][j]` reads `dp[i+1][j-1]`, `dp[i+1][j]`, `dp[i][j-1]`. All three have **smaller interval length** than `(i, j)`. By processing intervals in order of increasing length, every dependency is computed first.

If you instead loop `for i in range(n)` outer and `for j in range(i, n)` inner, you'd compute `dp[0][1]`, `dp[0][2]`, `dp[0][3]`, … *first*, before `dp[1][2]` — but `dp[0][2]` reads `dp[1][1]` ✓ and `dp[0][3]` reads `dp[1][2]` ✗. **Wrong order.** The diagonal sweep is the only natural fix.

The other natural fix is the **reverse-i, forward-j** order: `for i in range(n-1, -1, -1)` then `for j in range(i+1, n)`. This works because by the time `(i, j)` runs, both `(i+1, j-1)` and `(i+1, j)` and `(i, j-1)` have been computed (the first two have larger `i`, the last has smaller `j`).

#### Complexity

- **Time:** O(n²). Two nested loops, constant work per cell.
- **Space:** O(n²). Reducible to O(n) by keeping only the current and previous "diagonals," but the savings rarely matter and the array form is the interview default.

---

### Deep-dive 2 — Longest Palindromic Substring (LC 5)

> Given a string `s`, return the longest palindromic substring (contiguous).

Two equally good approaches: the **DP** (this section) and **expand around centre** (briefly compared).

#### DP approach

```python
def longest_palindromic_substring(s: str) -> str:
    n = len(s)
    if n < 2:
        return s
    dp = [[False] * n for _ in range(n)]
    start, max_len = 0, 1
    for i in range(n):
        dp[i][i] = True

    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                if length == 2 or dp[i + 1][j - 1]:
                    dp[i][j] = True
                    if length > max_len:
                        start, max_len = i, length

    return s[start:start + max_len]
```

#### Dry run on `s = "babad"`

`n = 5`. Initial dp (diagonal True).

**length = 2:**

| (i, j) | s[i], s[j] | dp |
|--------|------------|-----|
| (0, 1) | b, a | False |
| (1, 2) | a, b | False |
| (2, 3) | b, a | False |
| (3, 4) | a, d | False |

No length-2 palindromes.

**length = 3:**

| (i, j) | s[i], s[j] | inner True? | dp |
|--------|------------|-------------|-----|
| (0, 2) | b, b | dp[1][1]=True | True; max_len = 3, start = 0 |
| (1, 3) | a, a | dp[2][2]=True | True; ties, keep earlier |
| (2, 4) | b, d | — | False |

**length = 4:**

| (i, j) | s[i], s[j] | inner True? | dp |
|--------|------------|-------------|-----|
| (0, 3) | b, a | — | False |
| (1, 4) | a, d | — | False |

**length = 5:**

| (i, j) | s[i], s[j] | dp |
|--------|------------|-----|
| (0, 4) | b, d | False |

Output: `s[0:3] = "bab"` (or equivalently `"aba"` from `(1, 3)`). ✓

#### Expand around centre — the cleaner alternative

```python
def longest_palindromic_substring_centre(s: str) -> str:
    if not s:
        return ""
    start, end = 0, 0

    def expand(l: int, r: int) -> tuple[int, int]:
        while l >= 0 and r < len(s) and s[l] == s[r]:
            l -= 1
            r += 1
        return l + 1, r - 1

    for i in range(len(s)):
        l1, r1 = expand(i, i)                                     # odd-length centres
        l2, r2 = expand(i, i + 1)                                 # even-length centres
        for l, r in ((l1, r1), (l2, r2)):
            if r - l > end - start:
                start, end = l, r

    return s[start:end + 1]
```

Same O(n²) time, **O(1) space.** Considered the cleaner production code. Show both in interviews; the DP form generalises better to counting variants and weighted variants.

#### Substring vs subsequence — the structural difference

| Aspect | Substring (LC 5) | Subsequence (LC 516) |
|--------|------------------|-----------------------|
| What `dp[i][j]` stores | Boolean is-palindrome | Length of LPS |
| Recurrence (match) | `dp[i+1][j-1]` (must propagate) | `2 + dp[i+1][j-1]` |
| Recurrence (no match) | `False` (can't recover) | `max(dp[i+1][j], dp[i][j-1])` |
| Output | Substring text | Length |

The substring version is **stricter** — a single mismatch at the ends kills the palindromic property. The subsequence version can drop characters to recover.

#### Complexity

- **Time:** O(n²) for both DP and expand-around-centre.
- **Space:** O(n²) for DP, O(1) for expand-around-centre.

---

### Deep-dive 3 — Min Insertion Steps to Make a String Palindrome (LC 1312)

> Given `s`, return the minimum insertions to make it a palindrome. Insertions can be at any position.

**The clean reduction:** the answer is `n - LPS(s)`.

#### Why?

Any palindrome we build from `s` keeps some of the original characters and inserts the rest. The kept characters must themselves form a palindrome (because their *order* is preserved). The largest such "kept" set is the LPS. We insert one matching character for each character of `s` that's *not* in the LPS — that's `n - LPS(s)` insertions.

Visual: `s = "leetcode"`, LPS = `"eee"` (length 3), `n - LPS = 5`. Indeed `"leetcode"` requires 5 insertions to become a palindrome (one valid result: `"leetcodocteel"` — kept characters `"eee"` are at original positions, others have mirrored insertions).

#### Code

```python
def min_insertions(s: str) -> int:
    """LC 1312."""
    n = len(s)
    dp = [[0] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = 1

    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                dp[i][j] = 2 + (dp[i + 1][j - 1] if length > 2 else 0)
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])

    return n - dp[0][n - 1]
```

The body is **byte-for-byte the LC 516 solution**. The "min insertions" framing is solved by a one-line transform of the LPS answer.

#### Direct interval DP (without LPS reduction)

You can also write a min-insertions DP directly. Let `mins[i][j]` = min insertions to make `s[i..j]` a palindrome:

```
mins[i][j] = mins[i+1][j-1]              if s[i] == s[j]
           = 1 + min(mins[i+1][j], mins[i][j-1])  otherwise
```

Same complexity, equally correct. The LPS reduction is more elegant and easier to remember.

#### Dry run on `s = "mbadm"`

`n = 5`. LPS computation:

| length | (i, j) | match? | dp[i][j] |
|--------|--------|--------|----------|
| 2 | (0,1) m,b | no | 1 |
| 2 | (1,2) b,a | no | 1 |
| 2 | (2,3) a,d | no | 1 |
| 2 | (3,4) d,m | no | 1 |
| 3 | (0,2) m,a | no | max(1,1)=1 |
| 3 | (1,3) b,d | no | max(1,1)=1 |
| 3 | (2,4) a,m | no | max(1,1)=1 |
| 4 | (0,3) m,d | no | max(1,1)=1 |
| 4 | (1,4) b,m | no | max(1,1)=1 |
| 5 | (0,4) m,m | yes | 2 + dp[1][3]=1 = 3 |

LPS = 3 (e.g., `"mbm"` or `"mam"` or `"mdm"`). Min insertions = `5 - 3 = 2`. ✓

(One valid result: `"mbdadbm"` from inserting `d` and `b`, length 7 — but actually we can make it work with 2 insertions: `s = "mbadm"`, insert to get `"mbadabm"` length 7, palindrome. Alternatively `"mdbabdm"`. Either way 2 insertions.)

#### Complexity

- **Time:** O(n²).
- **Space:** O(n²).

---

## 🐛 Common bugs

1. **Wrong fill order.** Looping `for i in range(n)` outer with `for j in range(i, n)` inner reads cells that haven't been computed yet. Use the diagonal sweep (`for length`) or the reverse-i / forward-j order.
2. **Length-2 edge case.** `dp[i+1][j-1]` for length 2 is `dp[i+1][i]` (empty interval). The 0-initialised table happens to give the right answer for the LPS variant (`2 + 0 = 2`), but the boolean variant requires an explicit `length == 2` check.
3. **Confusing substring with subsequence.** Substring requires *contiguity*; subsequence allows skipping. The two recurrences differ in the no-match branch. Reading the problem twice prevents 30 minutes of debugging.
4. **LC 1312 forgetting the `n - LPS` reduction.** Writing a fresh interval DP is fine but doubles the work. The `n - LPS` reduction is the slick trick.
5. **Boolean DP returning a length instead of a substring (LC 5).** Track `start` and `max_len` as you go; rebuild the substring at the end.
6. **Mutating the same `dp` table to do both is-palindrome and counting.** Two different DPs with two different recurrences. Use two tables.
7. **Off-by-one in the substring slice.** `s[start:start + max_len]` is exclusive on the upper end. Using `s[start:start + max_len - 1]` cuts off the last character.
8. **Trying a 1D rolling form for full LPS.** The recurrence reads three cells (`[i+1][j-1]`, `[i+1][j]`, `[i][j-1]`) — three diagonals, not just one. Possible but bug-prone; default to the 2D form.

---

## 🗣️ Interviewer phrasings to recognize

- "Longest **palindromic subsequence**." → LC 516, `dp[i][j] = 2 + dp[i+1][j-1]` if match.
- "Longest **palindromic substring**." → LC 5, boolean DP or expand-around-centre.
- "Count **palindromic substrings** in s." → LC 647, count `dp[i][j]` cells that are True.
- "**Min insertions / deletions** to make palindrome." → `n - LPS(s)`.
- "**Min cuts** to split into palindromes." → LC 132, two-phase DP (palindrome table + 1D cut DP).
- "How many **distinct** palindromic subsequences." → LC 730, more careful interval DP with letter tracking.

---

## 🧭 Connections to other patterns

- **LCS DP** (page coming next) — same 2D recurrence shape on two strings; LPS(s) = LCS(s, reverse(s)).
- **Two Pointers** ([02-two-pointers.md](02-two-pointers.md)) — Valid Palindrome (LC 125, 680) is the linear-time variant; expand-around-centre is two-pointer in disguise.
- **0/1 Knapsack DP** ([15-01-knapsack-dp.md](15-01-knapsack-dp.md)) — both are 2D DPs but axes differ: knapsack is item × capacity, palindrome is left × right.
- **Subsets & Backtracking** ([10-subsets-backtracking.md](10-subsets-backtracking.md)) — LC 131 Palindrome Partitioning uses the `is_pal` table to drive backtracking.
- **String Pattern Matching** — LC 214 Shortest Palindrome uses KMP / Z-algorithm; same problem, different machinery.

---

## ✅ Self-check — 8 questions

??? question "1. Why do you fill the DP table by interval length, not row by row?"
    `dp[i][j]` reads `dp[i+1][j-1]`, `dp[i+1][j]`, `dp[i][j-1]` — all of which are *strictly smaller intervals*. Filling row by row would read uncomputed cells. Filling by interval length (or reverse-i / forward-j) ensures every dependency is already done.

??? question "2. What's the recurrence for Longest Palindromic Subsequence?"
    `dp[i][j] = 2 + dp[i+1][j-1]` if `s[i] == s[j]`; otherwise `max(dp[i+1][j], dp[i][j-1])`. Base case `dp[i][i] = 1` for single characters.

??? question "3. How does LPS solve Min Insertions to Make Palindrome (LC 1312)?"
    The kept characters in any palindrome you build must form a palindrome themselves (preserved order). The largest such subset is the LPS. You insert one character per non-LPS character, giving `n - LPS(s)` insertions.

??? question "4. What's the difference in recurrence between substring (LC 5) and subsequence (LC 516)?"
    Match case: substring stores `dp[i+1][j-1]` (boolean propagate); subsequence stores `2 + dp[i+1][j-1]` (length increment). No-match case: substring is `False` (can't recover); subsequence is `max(dp[i+1][j], dp[i][j-1])` (try dropping each end).

??? question "5. Why does expand-around-centre work in O(n²) time and O(1) space?"
    There are 2n - 1 possible centres (n single characters + n-1 between-character gaps). Each centre expands until characters mismatch — at most O(n) per expansion. Total work: O(n²). No DP table needed; just two indices.

??? question "6. How does LC 132 (Palindrome Partitioning II) use two DP tables?"
    First, build `is_pal[i][j]` via the standard interval DP. Then run a 1D DP `dp[j] = min cuts to make s[..j] a partition of palindromes`, scanning over all valid splits using `is_pal`. Total O(n²).

??? question "7. What if the problem asks for the actual longest palindromic subsequence, not just its length?"
    Reconstruct it after running the DP. From `dp[0][n-1]`, walk: if `s[i] == s[j]`, record both ends and move to `dp[i+1][j-1]`; else go to whichever of `dp[i+1][j]` or `dp[i][j-1]` is larger. The collected characters in order form the LPS.

??? question "8. Why is `LPS(s) = LCS(s, reverse(s))`?"
    A palindromic subsequence of `s` reads the same forwards and backwards — equivalently, it's a subsequence of `s` AND a subsequence of `reverse(s)`. The longest such common subsequence is exactly the LPS. So the LPS reduces to the LCS pattern (next page) on `s` and its reverse.

---

> **Next pattern up:** Longest Common Subsequence DP — the canonical 2D DP on two sequences, with Edit Distance, LIS, and the dozens of "compare two strings" variants that fall out of the same template (page coming next).
