# Suffix Arrays & Suffix Automata

> The data structure for "**many substrings of one long string.**" A **suffix array** is a sorted list of all `n` suffixes of a string — by index, not by storing each suffix. Combined with the **LCP (Longest Common Prefix) array**, you can answer: "longest repeated substring," "number of distinct substrings," "longest common substring of two texts," "k-th smallest substring," and "substring search" in linear-or-near-linear time. **Suffix automata** (SAM) are the deterministic-finite-automaton cousin — same problems, different machinery, often fewer lines.

<span class="phase-status phase-done">Phase 6 — Advanced</span>

---

## 📖 What is a suffix array?

For a string `s` of length `n`, the **suffix array** `sa[0..n-1]` is the permutation of `0..n-1` such that:

```
s[sa[0]:] < s[sa[1]:] < … < s[sa[n-1]:]    (lexicographic order)
```

You don't store the suffixes themselves — just the starting indices. Each suffix is `s[sa[i]:]` (Python slice).

For `s = "banana"`, the six suffixes are `"banana", "anana", "nana", "ana", "na", "a"`. Sorted:

| rank | sa[i] | suffix       |
|------|-------|--------------|
| 0    | 5     | `a`          |
| 1    | 3     | `ana`        |
| 2    | 1     | `anana`      |
| 3    | 0     | `banana`     |
| 4    | 4     | `na`         |
| 5    | 2     | `nana`       |

The **LCP array** `lcp[1..n-1]` records the **length of the longest common prefix** between `sa[i-1]` and `sa[i]` (consecutive suffixes in sorted order):

| i | sa[i] | suffix | lcp[i] | lcp explanation |
|---|-------|--------|--------|-----------------|
| 0 | 5 | `a` | — | — |
| 1 | 3 | `ana` | 1 | `a` |
| 2 | 1 | `anana` | 3 | `ana` |
| 3 | 0 | `banana` | 0 | nothing |
| 4 | 4 | `na` | 0 | nothing |
| 5 | 2 | `nana` | 2 | `na` |

The mental model: **the suffix array is a binary-search-friendly view of every substring**. Every substring of `s` is a prefix of some suffix; sorting suffixes lets you binary-search any substring in O(|p| log n), and the LCP array lets you compute substring statistics (counts, longest repeats, distinct counts) in linear time.

!!! tip "The signal — when to reach for suffix arrays / SAM"
    Reach for it when:

    - **One long string**, asking about *substrings* — distinct count, longest repeat, longest common with another text.
    - **Substring search** with many queries against a fixed text → build SA once, binary-search each query.
    - "Number of times substring `p` occurs in `s`" → SA + LCP gives O(|p| log n + occurrences).
    - "Lexicographically smallest / k-th rotation" — SA over `s + s`.

    Don't reach for it when:

    - **Many short strings, exact match only** — a hash set or Aho–Corasick (multi-pattern) is simpler.
    - **One short pattern in one short text** — KMP or Z-algorithm has lower constants.
    - You need **multi-pattern matching against one text** — Aho–Corasick.
    - The string is short enough that O(n²) brute-force fits — don't pull a SA out for `n ≤ 1000`.

---

## 🧩 The four flavors

### Flavor 1: Naive O(n² log n) — sort all suffixes

The reference implementation. Use only for tiny `n` or to verify a more complex implementation.

```python
def suffix_array_naive(s: str) -> list[int]:
    return sorted(range(len(s)), key=lambda i: s[i:])             # (1) Python sort calls strcmp; up to O(n) per compare
```

1. The sort is O(n log n) comparisons; each string compare on suffixes is O(n) worst case → O(n² log n) total. Acceptable for `n ≤ 5_000`.

### Flavor 2: Doubling / prefix-doubling O(n log² n)

Sort suffixes by their first 1 character, then 2, then 4, then 8 … doubling each round. Use ranks from the previous round to compare 2k-prefixes in O(1).

```python
def suffix_array_doubling(s: str) -> list[int]:
    n = len(s)
    sa = list(range(n))
    rank = [ord(c) for c in s]
    tmp = [0] * n
    k = 1

    while True:
        def key(i: int) -> tuple[int, int]:
            return (rank[i], rank[i + k] if i + k < n else -1)    # (1) compare 2k-prefix as a pair

        sa.sort(key=key)

        tmp[sa[0]] = 0
        for i in range(1, n):
            tmp[sa[i]] = tmp[sa[i - 1]] + (1 if key(sa[i]) != key(sa[i - 1]) else 0)
        rank = tmp[:]
        if rank[sa[-1]] == n - 1:                                 # (2) all ranks distinct → fully sorted
            break
        k *= 2

    return sa
```

1. The 2k-prefix at index `i` is `(rank[i], rank[i + k])` — first half's rank concatenated with second half's. Comparing tuples is O(1).
2. When all suffixes have distinct ranks, sorting is complete.

**Complexity:** O(n log² n) — `log n` doubling rounds × `n log n` per sort. For `n = 10^5`, fast enough.

### Flavor 3: SA-IS O(n) — induced sorting

The state-of-the-art linear-time suffix-array construction (Nong, Zhang, Chan 2009). 200+ lines of pointer-juggling. **Don't write it from scratch in an interview** — know it exists, use a library if you need linear time.

In practice for competitive programming you use **Flavor 2 (doubling)**; for production text indexing you use library SA-IS.

### Flavor 4: Suffix Automaton (SAM) O(n) construction, O(n) states

The minimal DFA accepting every substring of `s`. Each state corresponds to an *equivalence class* of substrings (same set of right-extensions). Powerful and shorter than SA-IS to write.

```python
class SuffixAutomaton:
    def __init__(self) -> None:
        self.next: list[dict] = [{}]                              # (1) state 0 = initial
        self.link: list[int] = [-1]                               # suffix links
        self.length: list[int] = [0]
        self.last = 0

    def extend(self, c: str) -> None:
        cur = len(self.next)
        self.next.append({})
        self.link.append(-1)
        self.length.append(self.length[self.last] + 1)

        p = self.last
        while p != -1 and c not in self.next[p]:                  # (2) walk suffix links, add `c` transition
            self.next[p][c] = cur
            p = self.link[p]

        if p == -1:
            self.link[cur] = 0
        else:
            q = self.next[p][c]
            if self.length[p] + 1 == self.length[q]:
                self.link[cur] = q
            else:                                                  # (3) clone q
                clone = len(self.next)
                self.next.append(self.next[q].copy())
                self.link.append(self.link[q])
                self.length.append(self.length[p] + 1)
                while p != -1 and self.next[p].get(c) == q:
                    self.next[p][c] = clone
                    p = self.link[p]
                self.link[q] = clone
                self.link[cur] = clone

        self.last = cur
```

1. Standard SAM has at most `2n - 1` states. Each state's `next` is a dict of outgoing transitions per character.
2. Walking suffix links (`link[p]`) and adding transitions captures the new character's behaviour across all suffix-equivalence classes.
3. The "clone q" branch handles the case where extending creates an inconsistency in the existing state's right-extension set.

**SAM applications** (each in O(n)): count distinct substrings, longest common substring with another text, k-th smallest substring, occurrence count of a pattern.

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical use | Trick |
|---|-------------|---------------|----------------|-------|
| 1 | Build SA | Sorted list of suffix indices | foundation | Doubling for interview-acceptable, SA-IS for production |
| 2 | Build LCP (Kasai) | Adjacent-suffix prefix lengths | substring statistics | Walk `s` left-to-right with previous LCP guess |
| 3 | Pattern search | Find pattern `p` in text | many queries against fixed `s` | Binary-search SA in O(\|p\| log n) |
| 4 | Longest repeated substring | Max in LCP | clone detection | `max(lcp)` and the corresponding suffix |
| 5 | Number of distinct substrings | Total minus shared | analytics | `n*(n+1)/2 - sum(lcp)` |
| 6 | Longest common substring of 2 texts | Concat with separator | dedup / diff | Build SA on `a + '#' + b`, scan LCP for max where adjacent suffixes come from different sides |
| 7 | k-th lexicographic substring | Walk the SA | enumeration | Use LCP to skip duplicate prefixes |

---

## 📋 Twenty problems on suffix arrays / SAM

| # | Problem | LC #/source | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Longest Duplicate Substring | LC 1044 | <span class="diff-hard">Hard</span> | Longest repeat | 📝 |
| 2 | Longest Common Substring | LC 718 (variant) | <span class="diff-medium">Medium</span> | Two-text LCS substring | 📝 |
| 3 | Distinct Substrings Count | SPOJ DISUBSTR | <span class="diff-medium">Medium</span> | n(n+1)/2 − Σlcp | 📝 |
| 4 | Substring Search (multi-query) | UVa / CF | <span class="diff-medium">Medium</span> | Binary-search SA | 📝 |
| 5 | Longest Palindromic Substring (alt) | LC 5 (alt) | <span class="diff-medium">Medium</span> | SA on s + '#' + reverse(s) | ✅ |
| 6 | Repeated DNA Sequences | LC 187 | <span class="diff-medium">Medium</span> | SA overkill — hash is simpler | 📝 |
| 7 | Number of Different Subsequences GCDs | LC 1819 | <span class="diff-hard">Hard</span> | Number-theoretic, SA cousin | 📝 |
| 8 | Lexicographically Smallest String After Operations | LC 1625 | <span class="diff-medium">Medium</span> | SA-friendly framing | 📝 |
| 9 | k-th smallest substring | CF | <span class="diff-hard">Hard</span> | SA + LCP walk | 📝 |
| 10 | Longest Common Substring of two texts | UVa | <span class="diff-hard">Hard</span> | SA on concat with sentinel | 📝 |
| 11 | Number of distinct substrings | CSES | <span class="diff-hard">Hard</span> | Same n(n+1)/2 − Σlcp | 📝 |
| 12 | Repetitions of strings | CF | <span class="diff-hard">Hard</span> | SA + Z-array hybrid | 📝 |
| 13 | Pattern Position | CSES | <span class="diff-medium">Medium</span> | SA binary-search | 📝 |
| 14 | Word Combinations | CSES | <span class="diff-hard">Hard</span> | Aho–Corasick or SAM | 📝 |
| 15 | Longest Common Substring of k strings | CF | <span class="diff-hard">Hard</span> | Generalised suffix array + sliding window | 📝 |
| 16 | Counting occurrences of substring | CSES | <span class="diff-hard">Hard</span> | SA + LCP range | 📝 |
| 17 | Substring Sums | rare | <span class="diff-hard">Hard</span> | SAM + DP | 📝 |
| 18 | Distinct Substrings II (with deletion) | CF | <span class="diff-hard">Hard</span> | SAM rebuild trick | 📝 |
| 19 | Longest Common Substring (Hashing alt) | LC 1923 | <span class="diff-hard">Hard</span> | Binary search + hashing | 📝 |
| 20 | Z-algorithm pattern matching | UVa | <span class="diff-medium">Medium</span> | Cousin: not SA but related | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Building the SA via doubling (the interview default)

> Sort the suffixes of `s` in O(n log² n) using prefix-doubling.

#### The plan

Round 0: rank each suffix by its first character. Multiple suffixes can share a rank.

Round k (k = 1, 2, 4, 8, …): rank each suffix by the **pair** `(rank[i], rank[i + k])` — the first `k` characters' rank concatenated with the next `k` characters' rank. Sort by this pair, assign new ranks. Each round doubles the prefix length being compared.

When all ranks are distinct, sorting is complete.

#### Code (re-stated)

```python
def suffix_array_doubling(s: str) -> list[int]:
    n = len(s)
    sa = list(range(n))
    rank = [ord(c) for c in s]
    tmp = [0] * n
    k = 1

    while True:
        def key(i: int) -> tuple[int, int]:
            return (rank[i], rank[i + k] if i + k < n else -1)

        sa.sort(key=key)

        tmp[sa[0]] = 0
        for i in range(1, n):
            tmp[sa[i]] = tmp[sa[i - 1]] + (1 if key(sa[i]) != key(sa[i - 1]) else 0)
        rank = tmp[:]
        if rank[sa[-1]] == n - 1:
            break
        k *= 2

    return sa
```

#### Walking `s = "banana"`

`n = 6`. Initial `rank = [98, 97, 110, 97, 110, 97]` (ord values of 'banana').

Sort by `(rank[i], rank[i+1])`:

| i | s[i:i+2] | key |
|---|----------|-----|
| 0 | ba | (98, 97) |
| 1 | an | (97, 110) |
| 2 | na | (110, 97) |
| 3 | an | (97, 110) |
| 4 | na | (110, 97) |
| 5 | a- | (97, -1) |

Sorted order: `5 (a-), 1 (an), 3 (an), 0 (ba), 2 (na), 4 (na)`. So `sa = [5, 1, 3, 0, 2, 4]`.

New ranks: distinguish keys. (97,-1)→0, (97,110)→1, (97,110)→1, (98,97)→2, (110,97)→3, (110,97)→3. New `rank = [2, 1, 3, 1, 3, 0]` (assigned by original index).

Not all ranks distinct (1 and 3 each appear twice). Set k = 2.

Sort by `(rank[i], rank[i+2])`:

| i | key |
|---|-----|
| 0 | (2, 3) |
| 1 | (1, 1) |
| 2 | (3, 3) |
| 3 | (1, 0) |
| 4 | (3, -1) |
| 5 | (0, -1) |

Sorted: `5, 3, 1, 0, 4, 2`. So `sa = [5, 3, 1, 0, 4, 2]`. ✓ Matches the table at the top of this page.

New ranks: all distinct (0,-1)→0, (1,0)→1, (1,1)→2, (2,3)→3, (3,-1)→4, (3,3)→5. Loop exits.

#### Why doubling

Each round doubles the comparable prefix length. After `log n` rounds, prefixes are length `n` — every suffix is fully ordered. Per-round sort is O(n log n) on tuple keys; total O(n log² n).

#### Complexity

- **Time:** O(n log² n) with Python sort (extra log from sort). Pure radix-sort variant achieves O(n log n).
- **Space:** O(n).

---

### Deep-dive 2 — Kasai's LCP construction

> Compute `lcp[i]` = LCP length of `s[sa[i-1]:]` and `s[sa[i]:]` in O(n).

The naive O(n²) is "for each pair of adjacent suffixes, compare characters until mismatch." Kasai's insight: process suffixes in **original-string order** (not sorted order), and the LCP between `s[i:]` and its sort-neighbour can only **shrink by 1** when you move from `i` to `i+1`.

#### Code

```python
def build_lcp_kasai(s: str, sa: list[int]) -> list[int]:
    n = len(s)
    rank = [0] * n
    for i, p in enumerate(sa):
        rank[p] = i                                               # (1) inverse: rank[i] = position of s[i:] in SA

    lcp = [0] * n
    h = 0                                                         # (2) running LCP, never resets to 0 fully
    for i in range(n):
        if rank[i] > 0:
            j = sa[rank[i] - 1]                                   # (3) the suffix immediately before s[i:] in SA
            while i + h < n and j + h < n and s[i + h] == s[j + h]:
                h += 1
            lcp[rank[i]] = h
            if h > 0:
                h -= 1                                            # (4) the key invariant — drop only by 1
        else:
            h = 0

    return lcp
```

1. Build the inverse permutation: `rank[i]` is the position of `s[i:]` in the sorted SA.
2. The running LCP variable. Drops by *at most 1* per outer iteration; never re-explores characters.
3. The neighbour to compare against — the suffix one position earlier in the SA.
4. After processing suffix `s[i:]`, the next outer iteration is `s[i+1:]`. The LCP of `s[i+1:]` with *its* SA-neighbour is at least `h - 1` — drop the leading character we just consumed.

#### Walking `s = "banana"`, `sa = [5, 3, 1, 0, 4, 2]`

`rank = [3, 2, 5, 1, 4, 0]` (inverse of sa).

| i | rank[i] | j = sa[rank[i]-1] | walk | lcp[rank[i]] | h after |
|---|---------|-------------------|------|--------------|---------|
| 0 | 3 | sa[2] = 1 | s[0]='b' vs s[1]='a' → 0 | lcp[3] = 0 | h = 0 |
| 1 | 2 | sa[1] = 3 | s[1]='a' vs s[3]='a' → match; s[2]='n' vs s[4]='n' → match; s[3]='a' vs s[5]='a' → match; s[4]='n' vs s[6]=oob → stop; h = 3 | lcp[2] = 3 | h = 2 |
| 2 | 5 | sa[4] = 4 | s[2+2]='n' vs s[4+2]=oob → stop; h = 2 | lcp[5] = 2 | h = 1 |
| 3 | 1 | sa[0] = 5 | s[3+1]='n' vs s[5+1]=oob → stop; h = 1 | lcp[1] = 1 | h = 0 |
| 4 | 4 | sa[3] = 0 | s[4]='n' vs s[0]='b' → 0 | lcp[4] = 0 | h = 0 |
| 5 | 0 | (rank=0, skip) | — | — | h = 0 |

`lcp = [0, 1, 3, 0, 0, 2]`. ✓ Matches the table.

#### Why it's linear

The variable `h` is decremented by at most 1 per outer iteration and incremented inside the inner loop. Each inner-loop increment is "real work" — it moves a global pointer forward, which can happen at most `2n` times across all iterations. Total work O(n).

#### Complexity

- **Time:** O(n).
- **Space:** O(n) for `rank` and `lcp`.

---

### Deep-dive 3 — Longest Repeated Substring (LC 1044)

> Given a string `s`, return the longest substring that appears at least twice. If none, return "".

#### The plan with SA + LCP

A "repeated substring" of length `k` in `s` corresponds to **two suffixes whose LCP is ≥ k**. The longest repeated substring is `max(lcp)` characters long, and one of the two repetitions starts at `sa[argmax(lcp)]`.

#### Code

```python
def longest_dup_substring_sa(s: str) -> str:
    """LC 1044 with SA + Kasai. Reference implementation; LC's official solution uses
    binary search + Rabin-Karp for tighter constants."""
    if len(s) < 2:
        return ""
    sa = suffix_array_doubling(s)
    lcp = build_lcp_kasai(s, sa)
    if max(lcp) == 0:
        return ""
    i = lcp.index(max(lcp))                                       # (1) position in SA where max LCP is
    return s[sa[i] : sa[i] + lcp[i]]                              # (2) the repeated substring
```

1. `lcp[i]` is the LCP between `sa[i-1]` and `sa[i]`. The maximum over all `i` is the longest substring that appears at least twice (once at position `sa[i-1]`, once at `sa[i]`).
2. Slice from one of the two starts.

#### Dry run on `s = "banana"`

From the LCP table: `lcp = [0, 1, 3, 0, 0, 2]`. Max is 3 at `i = 2`. `sa[2] = 1`. Repeated substring: `s[1:1+3] = "ana"`. ✓ ("ana" appears at positions 1 and 3 of "banana".)

#### Why this beats the brute O(n³)

Brute force checks all O(n²) substrings against all O(n) start positions. SA + LCP is O(n log² n) for SA + O(n) for LCP + O(n) to scan. For `n = 10^5`, brute is ~10^15 ops, SA approach is ~10^7. Several orders of magnitude.

For LC 1044 specifically, the **official solution** uses **binary search on the answer length + Rabin-Karp polynomial hashing**: also O(n log n) with smaller constants. SA is the more *general* tool (also gives distinct substring count, k-th smallest, etc.) at slightly higher constants.

#### Complexity

- **Time:** O(n log² n) for SA + O(n) for LCP + O(n) for scan.
- **Space:** O(n).

---

## 🐛 Common bugs

1. **Sort returning suffixes by string, not by index.** `sorted(suffixes_list)` works for tiny inputs but allocates `n` strings of average length `n/2` — O(n²) memory. Always sort indices with a key function instead.
2. **Off-by-one in Kasai when `i + h >= n`.** The bounds check `i + h < n and j + h < n` must be inside the inner-while condition, not after.
3. **Forgetting the `h -= 1` decrement.** Without it the algorithm degrades to O(n²) — Kasai's whole insight is that LCP can drop by *at most* 1 per outer iteration.
4. **Building the SA for substring search but binary-searching on raw strings.** The clean form is `lo = bisect_left(sa, p, key=lambda i: s[i:i+len(p)])` — but Python's `bisect` doesn't take `key` (until 3.10). Either upgrade or write a manual binary search on the SA.
5. **Concatenating two strings without a separator** for "longest common substring of two texts." Without a sentinel `#` (lower than all real characters), substrings can span the boundary and give bogus matches. Always insert a separator that doesn't appear in either input.
6. **Using SA when a hash set works.** "Find all distinct substrings of length k" → roll a hash. Don't reach for SA when k is fixed and small.
7. **SAM clone direction confusion.** The clone state inherits `q`'s transitions but takes `p + 1` length and `q`'s suffix link; the original `q` then points its suffix link at the clone. Easy to flip.
8. **Allocating `O(n × Σ)` for SAM transitions** when the alphabet is large. Use a dict per state (sparse) instead of a fixed-size array. For lowercase ASCII you can use a 26-array; for arbitrary Unicode use dicts.

---

## 🗣️ Interviewer phrasings to recognize

- "**Longest repeated substring** in s." → SA + LCP + max(lcp).
- "**Number of distinct substrings**." → `n(n+1)/2 - sum(lcp)`.
- "Search for many patterns in a fixed text." → SA + binary search per pattern.
- "**Longest common substring** of `a` and `b`." → SA on `a + '#' + b`, scan LCP for adjacent-from-different-sides max.
- "k-th lexicographic substring of s." → SA + LCP walk, skipping duplicates.
- "All occurrences of pattern `p` in `s`." → SA + binary search → contiguous SA range; size = number of occurrences.
- "Longest substring appearing at least k times." → SA + LCP + sliding window of length k on LCP.
- "Multi-pattern matching." → Aho–Corasick (different DS, related family).

---

## 🧭 Connections to other patterns

- **[Tries](01-tries.md)** — a *suffix trie* is the natural DS but uses O(n²) space. SA + LCP gives the same query power in O(n) space. SAM is the minimised DFA equivalent of a suffix trie, in O(n) states.
- **KMP / Z-algorithm** — single-pattern linear-time match. SA is overkill when you have one pattern and one text; KMP/Z are the right tools.
- **Aho–Corasick** — multi-pattern matching trie with failure links. Use when you have *many short patterns* matched against one text. SA is the dual: *one text*, *many query patterns*.
- **Polynomial hashing (Rabin-Karp)** — competing technique. Often easier to write, comparable performance, but probabilistic. SA is deterministic.
- **[Bitwise XOR](../04-patterns/20-bitwise-xor.md)** — unrelated but worth contrasting: both are "advanced primitives" that show up where the naive O(n²) is too slow.

---

## ✅ Self-check — 8 questions

??? question "1. What does `sa[i]` actually store?"
    The starting *index* in `s` of the suffix that's i-th in lexicographic order. Suffixes themselves are not stored — `s[sa[i]:]` recovers the i-th suffix on demand.

??? question "2. What does `lcp[i]` mean?"
    The length of the longest common prefix between the two adjacent suffixes `s[sa[i-1]:]` and `s[sa[i]:]` in the sorted SA. `lcp[0]` is undefined (no predecessor).

??? question "3. Why does prefix-doubling reach a sorted SA in log n rounds?"
    Each round doubles the prefix length being compared. After `log n` rounds, prefixes are of length `n` — every suffix is fully compared and ordered. Within each round, sorting tuples (prev-rank, half-shifted prev-rank) is O(n log n).

??? question "4. Why is Kasai's LCP construction O(n) and not O(n log n)?"
    The running LCP variable `h` decrements by at most 1 per outer iteration and is incremented only by real character matches. Across all iterations the total increments are at most `2n`, so the inner loop's total work is O(n).

??? question "5. How do you count distinct substrings using SA + LCP?"
    Total substrings (with multiplicity) = `n(n+1)/2`. Substrings that are *duplicated between adjacent SA suffixes* contribute `lcp[i]` overlaps each. Distinct = total minus the LCP overlaps: `n(n+1)/2 - sum(lcp)`.

??? question "6. How do you find the longest common substring of two texts `a` and `b`?"
    Concatenate `a + '#' + b` (sentinel '#' must be lex-smaller than any real char). Build SA + LCP. Scan adjacent SA pairs; for pairs where one suffix starts inside `a` and the other inside `b`, the LCP is a candidate. Return the max.

??? question "7. When would you prefer a suffix automaton over a suffix array?"
    SAM gives O(n) states/transitions and supports incremental "extend by one character" — natural for streaming. SA is a static structure; rebuilding after appends is O(n log n). Many counting queries (occurrence count, distinct substrings) are equally easy on either; SAM tends to be shorter for "longest common substring with another text" via DFA traversal.

??? question "8. What's the relationship between a suffix array and a suffix tree?"
    A suffix tree is a compacted trie of all suffixes (Ukkonen's algo, O(n)). The SA + LCP is essentially the *euler-tour traversal* of the suffix tree's leaves with edge depths — same information, different layout, much less memory. Most suffix-tree algorithms have an SA + LCP analogue.

---

> **Up next in Advanced:** Heavy-Light Decomposition — turning tree path queries into log² n range queries via O(log n) chain-jumps.
