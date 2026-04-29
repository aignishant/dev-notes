# Cyclic Sort

> When the input is "an array of n numbers in the range `[1..n]` (or `[0..n-1]`) — find the missing one / the duplicate / the smallest positive integer absent." The trick is to place each value at the index that *equals* it, then a single linear scan reveals exactly what's wrong. **O(n) time, O(1) extra space**, and you'll see it asked verbatim at Microsoft, Amazon, and Google.

<span class="phase-status phase-done">Phase 5 — Patterns</span>

---

## 📖 What is cyclic sort?

Imagine n numbered lockers and n students numbered 1..n. Every student is *somewhere* in the hallway but probably standing in front of the wrong locker. Walk down the hall: at each locker, look at whoever's standing there; if that student belongs at *another* locker, send them there (swap). Keep doing that *at the same locker* until the student in front of it owns it. Move to the next locker. Repeat.

After one pass, every student is at their own locker — *or* you discover that two students claim the same locker (duplicate) and that some lockers have nobody (missing).

That's cyclic sort. Each value `v` "wants" to live at index `v - 1` (or `v` if zero-indexed). You walk left to right and **swap each misplaced value home in O(1) per swap**. A value moves at most once into its home, so the total swap work is O(n). Then a second linear scan answers the actual question.

!!! tip "The signal — when to reach for cyclic sort"
    Reach for it when the problem says:

    - "Array of n integers, each in range `[1..n]`" (or `[0..n-1]`).
    - "Find the missing number / the duplicate / all duplicates / first missing positive."
    - "**Without using extra space**" or "in-place / O(1) memory."
    - The brute force is sort + compare, or hash-set, both of which the interviewer wants you to beat.

    If values are *not* bounded by `n`, cyclic sort doesn't apply directly — fall back to **XOR**, **bit-set**, or **negative marking** (still in-place but uses sign instead of position).

---

## 🧩 The three flavors

### Flavor 1: 1-indexed cyclic sort — values in `[1..n]`

```python
def cyclic_sort(nums: list[int]) -> None:
    """Place each value v at index v - 1, in-place."""
    i = 0
    while i < len(nums):
        home = nums[i] - 1               # (1) where nums[i] belongs
        if nums[i] != nums[home]:        # (2) NOT `home != i` — see deep-dive 1
            nums[i], nums[home] = nums[home], nums[i]
        else:
            i += 1                       # (3) only advance when settled
```

1. Value `v` is at home when its index is `v - 1`.
2. Compare **values**, not indices. If two slots already hold the right value, advancing prevents an infinite swap loop on duplicates.
3. **Don't `i += 1` inside the swap branch.** The newly arrived value at `i` may itself be misplaced — re-check it.

**Examples:** Cyclic Sort itself, Missing Number variants in `[1..n]`.

### Flavor 2: 0-indexed cyclic sort — values in `[0..n-1]`

```python
def cyclic_sort_zero(nums: list[int]) -> None:
    i = 0
    while i < len(nums):
        if nums[i] != nums[nums[i]]:     # value v wants index v (not v-1)
            nums[i], nums[nums[i]] = nums[nums[i]], nums[i]
        else:
            i += 1
```

The shift is a single character. Pick whichever matches the problem's index convention and don't mix them.

**Examples:** Missing Number (LC 268), Find the Duplicate Number variants.

### Flavor 3: Cyclic sort with out-of-range values — First Missing Positive

The trickiest case. Values can be negative, zero, or larger than `n`. Only values in `[1..n]` can possibly be the answer's neighbours, so during the placement sweep you **ignore everything else**.

```python
def first_missing_positive(nums: list[int]) -> int:
    n = len(nums)
    i = 0
    while i < n:
        v = nums[i]
        if 1 <= v <= n and nums[i] != nums[v - 1]:
            nums[i], nums[v - 1] = nums[v - 1], nums[i]
        else:
            i += 1                        # out-of-range or already settled

    for i in range(n):
        if nums[i] != i + 1:
            return i + 1
    return n + 1
```

The "ignore" branch is what makes this work for noisy input — see Deep-dive 3.

**Examples:** First Missing Positive (LC 41), Smallest Missing Positive after k removals.

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Place into bucket | One-pass sort by `v → v-1` | Cyclic Sort | Swap-then-recheck |
| 2 | Find missing single | One slot doesn't match | Missing Number (LC 268) | Scan for `i + 1 ≠ nums[i]` |
| 3 | Find duplicate | One slot's `nums[home]` already correct | Find the Duplicate Number (LC 287) | Detect at swap time |
| 4 | Find all missing | Multiple slots wrong | Find All Numbers Disappeared (LC 448) | Scan and collect |
| 5 | Find all duplicates | Each duplicate appears exactly twice | Find All Duplicates (LC 442) | After cyclic sort, mismatched slot ⇒ duplicate |
| 6 | First missing positive | Ignore out-of-range | First Missing Positive (LC 41) | Range-guarded swap |
| 7 | Set mismatch | Both missing & duplicate | Set Mismatch (LC 645) | One pass yields both |

---

## 📋 Twenty problems on this pattern

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Cyclic Sort (place 1..n) | — | <span class="diff-easy">Easy</span> | Place into bucket | 📝 |
| 2 | Missing Number | 268 | <span class="diff-easy">Easy</span> | Find missing single | 📝 |
| 3 | Find All Numbers Disappeared | 448 | <span class="diff-easy">Easy</span> | Find all missing | 📝 |
| 4 | Find the Duplicate Number | 287 | <span class="diff-medium">Medium</span> | Find duplicate | 📝 |
| 5 | Find All Duplicates in an Array | 442 | <span class="diff-medium">Medium</span> | Find all duplicates | 📝 |
| 6 | Set Mismatch | 645 | <span class="diff-easy">Easy</span> | Set mismatch | 📝 |
| 7 | First Missing Positive | 41 | <span class="diff-hard">Hard</span> | First missing positive | 📝 |
| 8 | Find the Corrupt Pair | — | <span class="diff-easy">Easy</span> | Set mismatch | 📝 |
| 9 | Smallest Missing Positive after k removals | — | <span class="diff-medium">Medium</span> | First missing positive | 📝 |
| 10 | K Missing Positive Numbers | 1539 | <span class="diff-easy">Easy</span> | Find all missing | 📝 |
| 11 | Find the Smallest Missing Integer | — | <span class="diff-medium">Medium</span> | First missing positive | 📝 |
| 12 | Find All Lonely Numbers in the Array | 2150 | <span class="diff-medium">Medium</span> | Place + scan | 📝 |
| 13 | Couples Holding Hands | 765 | <span class="diff-hard">Hard</span> | Place into bucket (greedy union-find variant) | 📝 |
| 14 | Sort Colors (Dutch flag) | 75 | <span class="diff-medium">Medium</span> | Bucket-by-value | 📝 |
| 15 | Array Nesting | 565 | <span class="diff-medium">Medium</span> | Cycle-following on indices | 📝 |
| 16 | Maximum Swap | 670 | <span class="diff-medium">Medium</span> | Bucket-by-digit | 📝 |
| 17 | Pancake Sorting | 969 | <span class="diff-medium">Medium</span> | Place via prefix flips | 📝 |
| 18 | Wiggle Sort II | 324 | <span class="diff-medium">Medium</span> | Place into bucket (3-way) | 📝 |
| 19 | Beautiful Arrangement | 526 | <span class="diff-medium">Medium</span> | Permutation-by-position search | 📝 |
| 20 | Smallest Range Covering Elements | 632 | <span class="diff-hard">Hard</span> | k-buckets sweep | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Cyclic Sort (the primitive)

> Given `nums` of length `n` containing every integer in `[1..n]` exactly once but in some random order, sort it in-place in O(n) and O(1) extra space.

You can't beat O(n log n) for general sorting — but the **value range** is gold here. Comparison-sort lower bounds are about distinguishing arbitrary permutations; we already know the multiset.

#### Code

```python
def cyclic_sort(nums: list[int]) -> None:
    i = 0
    while i < len(nums):
        home = nums[i] - 1
        if nums[i] != nums[home]:
            nums[i], nums[home] = nums[home], nums[i]
        else:
            i += 1
```

#### Dry run on `[3, 1, 5, 4, 2]`

| Step | `i` | `nums` before | `nums[i]` | `home` | Action | `nums` after |
|------|-----|---------------|-----------|--------|--------|--------------|
| 1 | 0 | `[3,1,5,4,2]` | 3 | 2 | swap idx 0,2 | `[5,1,3,4,2]` |
| 2 | 0 | `[5,1,3,4,2]` | 5 | 4 | swap idx 0,4 | `[2,1,3,4,5]` |
| 3 | 0 | `[2,1,3,4,5]` | 2 | 1 | swap idx 0,1 | `[1,2,3,4,5]` |
| 4 | 0 | `[1,2,3,4,5]` | 1 | 0 | settled, i++ | `[1,2,3,4,5]` |
| 5 | 1 | `[1,2,3,4,5]` | 2 | 1 | settled, i++ | — |
| 6 | 2..4 | … | … | … | all settled | — |

**Why O(n) total?** Every swap moves one value to its final home. Total useful swaps ≤ n. Plus n iterations that just advance `i`. = O(n) work.

#### Why we test values, not indices

Try `[1, 1]` (n=2, but with a duplicate — illegal for "exactly once" but illustrative). With `home != i`:
- i=0: nums[0]=1, home=0, `0 != 0` false → i++.
- i=1: nums[1]=1, home=0, `0 != 1` true → swap → still `[1,1]` → infinite loop.

With `nums[i] != nums[home]`:
- i=0: nums[0]=1, nums[0]=1, equal → i++.
- i=1: nums[1]=1, nums[0]=1, equal → i++. Done.

The value-comparison guard handles duplicates gracefully — which is *also* what the duplicate-finding flavors rely on.

#### Complexity

- **Time:** O(n).
- **Space:** O(1) extra (in-place).

---

### Deep-dive 2 — Find All Duplicates (LC 442)

> Given `nums` of length `n` where each integer is in `[1..n]` and every integer appears once or twice, return all that appear twice. Must be O(n) time and O(1) extra space (output list excluded).

Two clean approaches share the same skeleton:

1. **Cyclic sort + scan** — what we'll demo here.
2. **Negative marking** — flip the sign at index `|v| - 1`; if already negative, `|v|` is a duplicate. Equally O(1) space, slightly trickier with sign restoration.

#### Code

```python
def find_duplicates(nums: list[int]) -> list[int]:
    n = len(nums)
    i = 0
    while i < n:
        home = nums[i] - 1
        if nums[i] != nums[home]:
            nums[i], nums[home] = nums[home], nums[i]
        else:
            i += 1

    return [nums[i] for i in range(n) if nums[i] != i + 1]
```

After cyclic sort, every position either holds its "home" value or holds a duplicate that *couldn't go home* because home was already correct.

#### Dry run on `[4, 3, 2, 7, 8, 2, 3, 1]`

After cyclic sort:

| i | swap-trace ending state |
|---|---|
| start | `[4,3,2,7,8,2,3,1]` |
| settle pass | `[1,2,3,4,3,2,7,8]` |

Now scan for `nums[i] != i + 1`:

| i | `nums[i]` | `i + 1` | mismatch? |
|---|-----------|---------|-----------|
| 0 | 1 | 1 | — |
| 1 | 2 | 2 | — |
| 2 | 3 | 3 | — |
| 3 | 4 | 4 | — |
| 4 | 3 | 5 | ✓ collect 3 |
| 5 | 2 | 6 | ✓ collect 2 |
| 6 | 7 | 7 | — |
| 7 | 8 | 8 | — |

Output `[3, 2]` ✓.

#### Why duplicates land "out of place"

The first occurrence of every value gets sent to its home (because `nums[i] != nums[home]` is true the first time). The second occurrence finds its home already occupied (`nums[i] == nums[home]`), so the swap branch is skipped and `i` advances. The duplicate is left wherever the swaps last deposited it.

#### Complexity

- **Time:** O(n).
- **Space:** O(1) extra.

---

### Deep-dive 3 — First Missing Positive (LC 41)

> Given an unsorted array of arbitrary integers (negatives, zeros, large positives — no constraints), find the smallest missing positive integer in O(n) time and O(1) extra space.

This is the *crown jewel* of the cyclic-sort pattern and one of the most asked hard interview problems at FAANG. The trick is recognising that **the answer must be in `[1..n+1]`** — there are at most `n` distinct positives present, so at least one of `{1, 2, …, n+1}` is missing.

#### Code

```python
def first_missing_positive(nums: list[int]) -> int:
    n = len(nums)
    i = 0
    while i < n:
        v = nums[i]
        if 1 <= v <= n and nums[i] != nums[v - 1]:
            nums[i], nums[v - 1] = nums[v - 1], nums[i]
        else:
            i += 1

    for i in range(n):
        if nums[i] != i + 1:
            return i + 1
    return n + 1
```

The two-fold guard `1 <= v <= n and nums[i] != nums[v - 1]` is the key.
- `1 <= v <= n` — ignore noise (negatives, zeros, values bigger than n).
- `nums[i] != nums[v - 1]` — duplicate guard, same as basic cyclic sort.

#### Dry run on `[3, 4, -1, 1]` (n=4)

| Step | `i` | `nums` before | `v` | Range OK? | Home occupied? | Action | `nums` after |
|------|-----|---------------|-----|-----------|-----------------|--------|--------------|
| 1 | 0 | `[3,4,-1,1]` | 3 | ✓ (1≤3≤4) | `nums[2]=-1 ≠ 3` | swap idx 0,2 | `[-1,4,3,1]` |
| 2 | 0 | `[-1,4,3,1]` | -1 | ✗ | — | i++ | `[-1,4,3,1]` |
| 3 | 1 | `[-1,4,3,1]` | 4 | ✓ | `nums[3]=1 ≠ 4` | swap idx 1,3 | `[-1,1,3,4]` |
| 4 | 1 | `[-1,1,3,4]` | 1 | ✓ | `nums[0]=-1 ≠ 1` | swap idx 1,0 | `[1,-1,3,4]` |
| 5 | 1 | `[1,-1,3,4]` | -1 | ✗ | — | i++ | — |
| 6 | 2 | `[1,-1,3,4]` | 3 | ✓ | `nums[2]=3` settled | i++ | — |
| 7 | 3 | `[1,-1,3,4]` | 4 | ✓ | `nums[3]=4` settled | i++ | — |

Final array: `[1, -1, 3, 4]`. Scan: `nums[0]=1` ✓, `nums[1]=-1 ≠ 2` → return **2**. ✓

#### The proof — why O(n)?

Each successful swap places a positive value into its home slot, and a value never leaves its home. So at most `n` swaps. Each iteration either swaps (charges to one of those n) or advances `i` (charges to one of n iterations). Total work: O(n).

#### Why "1 to n+1" is the right answer range

- If `[1..n]` are all present, the answer is `n + 1`.
- Otherwise the smallest missing is some `k ∈ [1..n]`.
- No `k > n + 1` can ever be the smallest missing (you'd need *all* of 1..n+1 to be present, which would require n+1 distinct positives in n slots).

This is why the second loop returns `n + 1` if no mismatch is found.

#### Complexity

- **Time:** O(n).
- **Space:** O(1) extra (mutates input — caller should be told).

---

## 🐛 Common bugs

1. **`if home != i` instead of `if nums[i] != nums[home]`.** Loops forever on duplicates. The values-comparison form handles all cases.
2. **Advancing `i` after a swap.** The new value at index `i` might itself be misplaced. Only `i++` when the swap branch is *not* taken.
3. **Forgetting the `1 <= v <= n` guard in First Missing Positive.** A negative value tries to swap to index `-2`; you'll get either an `IndexError` or silent wraparound (Python). Crash-and-bug, both bad.
4. **Mixing 0-indexed and 1-indexed conventions.** Pick one based on the value range and stick to it.
5. **Returning `nums[i] - 1` as the missing index in LC 268.** The missing number is `i` (the index that *should* hold a value), not the displaced value at that slot.
6. **Mutating in a "read-only" interview.** Cyclic sort destroys the input. If the interviewer says "don't mutate," fall back to negative-marking-with-sign-restore or use XOR (works only for the LC 268 single-missing case).
7. **Pancake / array-nesting confusion.** These are *cycle-following*, not cyclic-sort. Different mechanics — don't conflate.

---

## 🗣️ Interviewer phrasings to recognize

- "Each integer appears exactly once except one — find it." → Missing Number / cyclic sort flavor 2.
- "Each appears exactly twice except one." → XOR (different pattern), or set-mismatch with cyclic sort.
- "Find duplicate without modifying the array, O(1) space." → **Floyd's cycle detection on the value-as-pointer trick** (different page — see [Fast & Slow Pointers](03-fast-slow-pointers.md)). Cyclic sort needs to mutate.
- "Smallest missing positive integer."  → LC 41, deep-dive 3.
- "All numbers in `[1..n]` that don't appear." → LC 448, scan after cyclic sort.

---

## 🧭 Connections to other patterns

- **Fast & Slow Pointers** — Find the Duplicate Number (LC 287) has a famous O(1)-space *no-mutation* solution by treating `nums` as a linked list and applying Floyd's cycle detection. See [03-fast-slow-pointers.md](03-fast-slow-pointers.md).
- **Negative marking** — same in-place spirit as cyclic sort but uses *sign* instead of *position* to encode "I've seen this index." Trade: simpler logic, but breaks if values could be negative to start with.
- **Counting / bucket sort** — cyclic sort is the in-place analog of counting sort. Use counting sort if you can afford O(n) extra space; cyclic sort if you can't.
- **XOR** — for the strict "every element appears twice except one" variant, `reduce(xor, nums)` is O(n) time, O(1) space, and doesn't need mutation. Different pattern, same problem family.

---

## ✅ Self-check — 8 questions

??? question "1. Why must the value range be `[1..n]` (or `[0..n-1]`) for cyclic sort to work?"
    The mapping `value → index` must land inside the array. If `v > n`, `nums[v-1]` is out of bounds. If `v < 1`, you'd need negative indexing semantics that aren't part of the algorithm. The bounded range *is* the algorithm.

??? question "2. Why test `nums[i] != nums[home]` instead of `home != i`?"
    On duplicates, `home != i` is `true` even when the duplicate is already in someone else's correct slot — so the swap is a no-op that gets repeated forever. Comparing values catches that case (`nums[i] == nums[home]`) and lets you advance.

??? question "3. Could you sort by `i = home - 1` indices instead of by `home`?"
    The convention is that value `v` goes to index `v - 1`. You can flip that (e.g., `v → n - v`) if you want descending order, but it's pure cosmetic — the algorithm is the same.

??? question "4. Why is First Missing Positive O(n) and not O(n²) given the nested swaps?"
    Amortized analysis: each successful swap *commits* one value to its final home. There are at most `n` such commits. Other iterations just advance `i` (also `n` of those). Total: O(n).

??? question "5. What changes if duplicates are allowed in the input range `[1..n]`?"
    Most flavors still work — duplicates are exactly what we want to detect (Find All Duplicates). The duplicate-guard in the swap condition (`nums[i] != nums[home]`) is what handles them; we wouldn't need it if we *knew* there were no duplicates.

??? question "6. Why does First Missing Positive ignore values out of range instead of placing them somewhere?"
    Out-of-range values can't be the answer (the answer is in `[1..n+1]`) and can't be placed anywhere meaningful (no home in `[0..n-1]`). Leaving them as flotsam is fine — the second-pass scan only looks for "is `nums[i] == i + 1`?" and out-of-range values fail that check at exactly the right spot.

??? question "7. When do you prefer negative marking over cyclic sort?"
    When the input range is `[1..n]` *and* you want to avoid the swap mechanics — sign flipping is fewer lines and doesn't move values around. Caveats: original values must all be positive (otherwise sign carries information), and you must restore signs if the caller will inspect the array afterward.

??? question "8. How would you handle the read-only constraint of LC 287 (Find the Duplicate)?"
    Cyclic sort can't help (it mutates). Use **Floyd's cycle detection** on `nums` as a functional graph: `f(i) = nums[i]`. The duplicate creates a cycle; the entry to that cycle is the duplicate. O(n) time, O(1) extra space, no mutation. See the [Fast & Slow Pointers](03-fast-slow-pointers.md) page.

---

> **Next pattern up:** In-Place Linked List Reversal — how to reverse a sublist with three-pointer relinking and why it underlies "reverse k-group," palindrome check, and rotate list (page coming next).
