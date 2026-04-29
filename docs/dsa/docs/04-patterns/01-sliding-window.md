# Sliding Window

> A two-pointer family of techniques where you keep a "window" over a contiguous slice of the input and slide it forward, expanding or shrinking, instead of restarting from scratch. The #1 most-asked pattern at every product company. This page is the **template** for the other 19 pattern pages.

<span class="phase-status phase-done">Phase 5 — Patterns</span>

---

## 📖 What is sliding window?

Imagine reading a billboard while driving past it. At any moment you see only a fixed-width slice of letters. As you drive forward, one new letter enters on the right, one old letter leaves on the left. You're never re-reading the whole billboard — just shifting your view.

That's sliding window. You maintain a **contiguous range** `[left..right]` over an array or string and, as you advance `right`, you possibly advance `left` to keep some property true. **Each element enters the window once and leaves at most once → O(n) total work.**

The pattern reduces what looks like an O(n²) "for every starting point, scan forward" problem to O(n).

!!! tip "The signal — when to reach for sliding window"
    Reach for it when:

    - The problem mentions **"contiguous"** subarray or **"substring"** (not subsequence).
    - The answer is a **sum, max, min, count, or length** over a window.
    - You're tracking something **monotonic** as you extend a range — for example, "how many distinct chars" or "current sum."
    - Brute force is "try every (i, j) pair" → O(n²) and too slow.

    If the problem says "subsequence" (non-contiguous), it's **not** sliding window — that's DP.

---

## 🧩 The two flavors

Every sliding-window problem is either **fixed-size** or **variable-size**. The mechanics differ.

### Flavor 1: Fixed-size window

You're given `k` and asked something about every window of length `k`.

```python
# Fixed-size template
def fixed_window(arr: list[int], k: int) -> int:
    window_sum = sum(arr[:k])      # initialize first window
    best = window_sum

    for right in range(k, len(arr)):
        # Slide: add the entering element, remove the leaving one.
        window_sum += arr[right] - arr[right - k]
        best = max(best, window_sum)

    return best
```

**Key idea:** the window is always size `k`. When `right` advances by 1, `left` advances by 1. No conditional shrinking.

**Examples:** Maximum sum subarray of size k. Sliding Window Maximum. Find all anagrams of pattern in text.

### Flavor 2: Variable-size window

The window grows and shrinks based on a condition. `right` advances every iteration; `left` advances only when the window violates the constraint.

```python
# Variable-size template
def variable_window(arr: list[int], target: int) -> int:
    left = 0
    window_state = 0           # sum, count, hash map — depends on problem
    best = 0

    for right in range(len(arr)):
        # Expand: include arr[right] in window_state
        window_state += arr[right]

        # Shrink while the window violates the property
        while window_state > target:
            window_state -= arr[left]
            left += 1

        # Record best for the current valid window [left..right]
        best = max(best, right - left + 1)

    return best
```

**Key idea:** `right` is the driver. The `while` shrinks `left` only when needed. Both pointers monotonically move forward.

**Examples:** Longest substring with at most K distinct chars. Smallest subarray with sum ≥ S. Minimum window substring.

---

## ⚡ Why is this O(n)?

The amortized argument: in the variable-window template, every iteration of the outer `for` advances `right` by 1. The inner `while` advances `left` — but `left` can never go beyond `right`, and `left` only ever increases. So across the entire execution:

- `right` advances at most `n` times.
- `left` advances at most `n` times.
- **Total work: at most 2n = O(n).**

The window does *not* re-process elements. That's the magic.

!!! warning "Common confusion"
    People see a `for` with a `while` inside and assume O(n²). Wrong — count *total advances*, not nested loops. Each element enters/leaves at most once.

---

## 🔬 The 7 sub-patterns

Every sliding-window problem reduces to one of these:

| # | Sub-pattern | Window state | Example problem |
|---|---|---|---|
| 1 | **Fixed-size aggregate** | running sum / max / count | Max sum subarray of size k |
| 2 | **Fixed-size + monotonic deque** | deque of indices | Sliding Window Maximum |
| 3 | **Longest valid window** | hash map / counter | Longest substring with K distinct |
| 4 | **Shortest valid window** | shrink past the satisfaction point | Minimum window substring |
| 5 | **Anagram / permutation match** | char-count vector + match counter | Find all anagrams in s |
| 6 | **At-most-K → exactly-K trick** | run "at most K" twice, subtract | Subarrays with K different ints |
| 7 | **Replace / flip** | track count of "wrong" elements | Longest subarray of 1s after K flips |

Master these 7 mechanisms and you've solved every interview sliding-window problem.

---

## 📋 The 20 problems

Difficulty pill conventions:

- <span class="diff-easy">Easy</span> &nbsp; <span class="diff-medium">Medium</span> &nbsp; <span class="diff-hard">Hard</span>

Status:

- ✅ = full v3 solution exists in this bible (link given)
- 📝 = covered in mini-v3 below
- 🚧 = lands in Phase 5 (full v3 solutions for every pattern problem)

### Fundamentals — fixed window (4)

| # | Problem | Difficulty | Sub-pattern | Status |
|---|---|---|---|---|
| 1 | Maximum Sum Subarray of Size K | <span class="diff-easy">Easy</span> | Fixed aggregate | [📝](#deep-dive-1-maximum-sum-subarray-of-size-k) |
| 2 | Average of Subarrays of Size K | <span class="diff-easy">Easy</span> | Fixed aggregate | 🚧 |
| 3 | Maximum Points You Can Obtain from Cards | <span class="diff-medium">Medium</span> | Fixed (both ends) | 🚧 |
| 4 | Sliding Window Maximum | <span class="diff-hard">Hard</span> | Fixed + monotonic deque | [✅](../02-data-structures/arrays/01-array-basics.md) |

### Variable window — longest valid (6)

| # | Problem | Difficulty | Sub-pattern | Status |
|---|---|---|---|---|
| 5 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Longest, hash check | [📝 Google 50](../07-popular-problems/product-based/google-50.md#deep-dive-1-longest-substring-without-repeating-characters) |
| 6 | Longest Substring with At Most K Distinct Characters | <span class="diff-medium">Medium</span> | Longest, K-constraint | [📝](#deep-dive-3-longest-substring-with-at-most-k-distinct-characters) |
| 7 | Longest Substring with At Most 2 Distinct Characters | <span class="diff-medium">Medium</span> | Longest, K=2 special case | 🚧 |
| 8 | Fruit Into Baskets | <span class="diff-medium">Medium</span> | Same as #7, reframed | 🚧 |
| 9 | Longest Repeating Character Replacement | <span class="diff-medium">Medium</span> | Longest + replace tracker | 🚧 |
| 10 | Max Consecutive Ones III (flip K zeros) | <span class="diff-medium">Medium</span> | Longest + flip K | 🚧 |

### Variable window — shortest valid (3)

| # | Problem | Difficulty | Sub-pattern | Status |
|---|---|---|---|---|
| 11 | Smallest Subarray with Sum ≥ S | <span class="diff-medium">Medium</span> | Shortest, sum threshold | [📝](#deep-dive-2-smallest-subarray-with-sum-s) |
| 12 | Minimum Window Substring | <span class="diff-hard">Hard</span> | Shortest, contains all | 🚧 |
| 13 | Minimum Size Subarray Sum (LC 209) | <span class="diff-medium">Medium</span> | Shortest, sum threshold | 🚧 |

### Anagram / permutation matching (3)

| # | Problem | Difficulty | Sub-pattern | Status |
|---|---|---|---|---|
| 14 | Permutation in String | <span class="diff-medium">Medium</span> | Fixed + char-count match | 🚧 |
| 15 | Find All Anagrams in a String | <span class="diff-medium">Medium</span> | Fixed + char-count match | 🚧 |
| 16 | Substring with Concatenation of All Words | <span class="diff-hard">Hard</span> | Multi-word fixed | 🚧 |

### At-most-K → exactly-K trick (2)

| # | Problem | Difficulty | Sub-pattern | Status |
|---|---|---|---|---|
| 17 | Subarrays with K Different Integers | <span class="diff-hard">Hard</span> | exactly-K = atMost(K) − atMost(K−1) | 🚧 |
| 18 | Count Number of Nice Subarrays | <span class="diff-medium">Medium</span> | Same trick on parity | 🚧 |
| 19 | Binary Subarrays With Sum | <span class="diff-medium">Medium</span> | Same trick on sum | 🚧 |

### Hybrid — heap or two heaps (1)

| # | Problem | Difficulty | Sub-pattern | Status |
|---|---|---|---|---|
| 20 | Sliding Window Median | <span class="diff-hard">Hard</span> | Fixed + two heaps | 🚧 |

---

## 🔬 Deep-dives — 3 templates that cover everything

Picked because:

- **#1 Maximum Sum Subarray of Size K** demonstrates the **fixed-size** flavor (the simplest skeleton).
- **#2 Smallest Subarray with Sum ≥ S** demonstrates the **variable-size, shrink-while-violating** flavor — the canonical template.
- **#3 Longest Substring with At Most K Distinct** demonstrates the **variable-size with hash-map state** — the third major shape.

Master these three skeletons and you can solve every problem in the table above by adapting state and exit conditions.

Format: thinking process → optimal solution → dry run → complexity → variants.

---

### Deep-dive 1: Maximum sum subarray of size K

<span class="diff-easy">Easy</span> &nbsp; <span class="company-tag">Everyone</span>

> Given an integer array `arr` and an integer `k`, find the **maximum sum** of any contiguous subarray of size exactly `k`.

Example: `arr = [2, 1, 5, 1, 3, 2]`, `k = 3` → answer is `9` (subarray `[5, 1, 3]`).

#### 📖 Story mode

You can place a 3-day calendar window anywhere on a row of daily revenue numbers. Which placement gives the highest 3-day total?

#### 🧠 Thinking process

- **Brute force**: for every start `i`, sum `arr[i..i+k-1]`. O(n·k).
- **Insight**: when the window slides right by one, the new sum = old sum + new entering element − old leaving element. So we update in O(1), not O(k).

This is the cleanest possible introduction to the pattern.

#### 🐍 Optimal solution

```python
def max_sum_size_k(arr: list[int], k: int) -> int:
    """Maximum sum among all contiguous subarrays of size k."""
    if len(arr) < k:
        raise ValueError("array shorter than window")

    window_sum = sum(arr[:k])         # first window
    best = window_sum

    for right in range(k, len(arr)):
        window_sum += arr[right] - arr[right - k]   # slide
        best = max(best, window_sum)

    return best
```

The `arr[right] - arr[right - k]` is the entire trick: add the entering element, remove the leaving element.

#### 🔍 Dry run on `arr = [2, 1, 5, 1, 3, 2]`, `k = 3`

Initial window `[2, 1, 5]` → `window_sum = 8`, `best = 8`.

| right | arr[right] | arr[right-k] | window_sum | best |
|---|---|---|---|---|
| 3 | 1 | 2 | 8 + 1 − 2 = 7 | 8 |
| 4 | 3 | 1 | 7 + 3 − 1 = 9 | **9** |
| 5 | 2 | 5 | 9 + 2 − 5 = 6 | 9 |

Answer: 9.

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| Brute force | O(n · k) | O(1) |
| **Sliding window** | **O(n)** | **O(1)** |

#### 🔄 Variants you might be asked

??? question "Average instead of sum (LC 643)."
    Same algorithm, just divide `best / k` at the end. The summation logic is identical.

??? question "Maximum sum of size **between** k and m (variable size)."
    No longer fixed-size — switch to a variable-window template, or precompute prefix sums and answer length-bounded range queries.

??? question "Minimum sum subarray of size k."
    Replace `max(best, …)` with `min(best, …)` and initialize `best = window_sum`. Trivial.

??? question "Maximum sum of size k in a **circular** array."
    Concatenate `arr + arr` (logically), apply the same algorithm, but cap `right ≤ n + k − 1` to avoid double-counting.

#### 🐛 Common bugs

- Forgetting to initialize `window_sum = sum(arr[:k])` before the loop — starts with a half-full window.
- Off-by-one on `range(k, len(arr))` vs `range(k - 1, len(arr))` — easiest to verify with the small example.
- Forgetting the `len(arr) < k` guard — silently returns the max of an empty pool (or 0, depending on language).

---

### Deep-dive 2: Smallest subarray with sum ≥ S

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Everyone</span>

> Given a positive-integer array `arr` and a target `s`, find the **length of the smallest contiguous subarray** whose sum is ≥ `s`. If none exists, return 0.

Example: `arr = [2, 1, 5, 2, 3, 2]`, `s = 7` → answer `2` (subarray `[5, 2]`).

#### 📖 Story mode

Streaming bandwidth log: each integer is "MB transferred this second." How few consecutive seconds did it take to transfer at least 7 MB? You need the **shortest** window that meets the threshold.

#### 🧠 Thinking process

- **Brute force**: for every start `i`, walk forward summing until ≥ s. Track shortest. O(n²).
- **Insight**: once you've found a valid window ending at `right`, you can keep **shrinking from the left** as long as the sum stays ≥ s. This finds the *tightest* window ending at `right`. Then you advance `right`. Each pointer moves O(n) total → O(n).

This is the canonical variable-window-shrink template. **Memorize the shape** — it shows up in dozens of problems.

#### 🐍 Optimal solution

```python
def smallest_subarray_with_sum(arr: list[int], s: int) -> int:
    """Length of smallest contiguous subarray with sum >= s. 0 if none."""
    left = 0
    window_sum = 0
    best = float("inf")

    for right in range(len(arr)):
        window_sum += arr[right]                      # expand

        while window_sum >= s:                        # shrink while still valid
            best = min(best, right - left + 1)
            window_sum -= arr[left]
            left += 1

    return 0 if best == float("inf") else best
```

Note: the `while` runs *while still valid*. We record `best` *inside* the while — that captures the smallest window ending at the current `right`.

!!! warning "Why this only works for **positive** numbers"
    The shrink-when-valid logic relies on the fact that removing an element from the left can only **decrease** the sum. With negative numbers, removal could increase it, so the monotonic argument breaks. For arrays with negatives, use prefix sum + deque or different technique.

#### 🔍 Dry run on `arr = [2, 1, 5, 2, 3, 2]`, `s = 7`

| right | arr[right] | window_sum after expand | inner while → shrinks | best |
|---|---|---|---|---|
| 0 (=2) | 2 | 2 | sum<7, no shrink | ∞ |
| 1 (=1) | 1 | 3 | sum<7, no shrink | ∞ |
| 2 (=5) | 5 | 8 | sum≥7: record len=3, shrink → sum=6 | 3 |
| 3 (=2) | 2 | 8 | sum≥7: record len=3 (vs 3, no change), shrink → sum=3 | 3 |
| 4 (=3) | 3 | 6 | sum<7, no shrink | 3 |
| 5 (=2) | 2 | 8 | sum≥7: record len=2, shrink → sum=5 | **2** |

Answer: 2.

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| Brute force | O(n²) | O(1) |
| **Sliding window** | **O(n)** | **O(1)** |

The amortized argument: `left` and `right` each move forward at most `n` times. Total ops: ≤ 2n.

#### 🔄 Variants you might be asked

??? question "What if the array can contain **negative** numbers?"
    Sliding window breaks (the monotonic shrink argument fails). Use **prefix sum + monotonic deque** (LC 862 — Hard). Mention this *immediately* if the interviewer changes the constraint — it shows you understand *why* the technique works.

??? question "Find **how many** subarrays have sum ≥ s, instead of the shortest."
    Same window shape. After the shrink, every left ≤ left' ≤ right with `prefix[right+1] − prefix[left'] ≥ s` qualifies. Count = (left after shrink) once shrink stops.

??? question "Find the smallest subarray with sum **exactly equal** to s."
    Sliding window doesn't apply directly (equality, not ≥). Use a hash map of prefix sums.

??? question "What if `s` is huge and no valid window exists?"
    Your `best == inf` check returns 0 cleanly. Make sure you actually have that guard.

#### 🐛 Common bugs

- Updating `best` *outside* the while loop — gives the wrong answer because you don't capture the tightest window.
- Forgetting to subtract `arr[left]` *before* `left += 1` — the order matters.
- Initializing `best = 0` instead of `inf` — you'd return 0 even when valid windows exist.
- Applying this template to arrays with negatives — see the variant above.

---

### Deep-dive 3: Longest substring with at most K distinct characters

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Google</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">Meta</span>

> Given a string `s` and integer `k`, find the **length of the longest substring** that contains **at most k distinct characters**.

Example: `s = "araaci"`, `k = 2` → answer `4` (substring `"araa"`).

#### 📖 Story mode

You're shopping at a fruit stand that lets you fill any number of baskets — but you only own `k` baskets, and each basket can hold one *type* of fruit. Walking left-to-right, what's the longest run of consecutive fruits you can pick up before you'd need a `(k+1)`-th basket type?

(That's literally LeetCode "Fruit Into Baskets" — same problem, k=2.)

#### 🧠 Thinking process

- **Brute force**: for every start `i`, expand `j` until distinct count exceeds `k`. O(n²).
- **Insight**: when the window has too many distinct chars, we *don't* restart — we just shrink from the left until distinct ≤ k again. Maintain a hash map of `char → count` to know when a char fully leaves the window.

This is the canonical **variable-window with hash-map state** template. The hash map is what makes it work for character constraints.

#### 🐍 Optimal solution

```python
from collections import defaultdict

def longest_substring_k_distinct(s: str, k: int) -> int:
    """Longest substring containing at most k distinct characters."""
    if k == 0 or not s:
        return 0

    char_count: dict[str, int] = defaultdict(int)
    left = 0
    best = 0

    for right, ch in enumerate(s):
        char_count[ch] += 1                          # expand

        while len(char_count) > k:                   # shrink while too many distinct
            left_char = s[left]
            char_count[left_char] -= 1
            if char_count[left_char] == 0:
                del char_count[left_char]            # actually remove key
            left += 1

        best = max(best, right - left + 1)           # record after window is valid

    return best
```

**The crucial detail**: when a character's count hits 0, we `del` the key. Otherwise `len(char_count)` is wrong (it'd count "ghost" zero-count entries).

Note placement of `best = max(...)` — it's *outside* the while, *after* shrinking is done. That's the inverse of deep-dive 2 (shortest = inside while; longest = outside while).

#### 🔍 Dry run on `s = "araaci"`, `k = 2`

| right | ch | char_count after expand | inner while shrink? | window | best |
|---|---|---|---|---|---|
| 0 | a | {a:1} | no (1 ≤ 2) | "a" | 1 |
| 1 | r | {a:1, r:1} | no (2 ≤ 2) | "ar" | 2 |
| 2 | a | {a:2, r:1} | no | "ara" | 3 |
| 3 | a | {a:3, r:1} | no | "araa" | **4** |
| 4 | c | {a:3, r:1, c:1} | yes: shrink → drop 'a','r','a','a' until a only or done… actually: left=0 'a' →{a:2,r:1,c:1} still 3, left=1 'r'→{a:2,c:1} now 2 distinct | "aac" (left=2, right=4) | 4 |
| 5 | i | {a:2, c:1, i:1} | yes: shrink → left=2 'a'→{a:1,c:1,i:1} still 3; left=3 'a'→{c:1,i:1} now 2 | "ci" (left=4, right=5) | 4 |

Answer: 4.

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| Brute force | O(n² · k) | O(k) |
| **Sliding window** | **O(n)** | O(k) |

The hash map holds at most `k+1` chars at any point.

#### 🔄 Variants you might be asked

??? question "**Exactly** k distinct (not at most)."
    Use the **at-most-K trick**: `exactly(K) = atMost(K) − atMost(K-1)`. Run the algorithm twice with different K. This is a recurring trick in counting problems.

??? question "Longest substring with **all unique** chars (LC 3)."
    Special case where `k = ∞` and the constraint is just "no duplicates." Same template; `while len(char_count) > k` becomes `while char_count[ch] > 1`. See [Google 50 deep-dive](../07-popular-problems/product-based/google-50.md#deep-dive-1-longest-substring-without-repeating-characters).

??? question "Longest substring with at most K **0s** (i.e. flip K zeros)."
    Same template but state is "count of zeros in window" instead of "distinct chars." LC 1004 — Max Consecutive Ones III.

??? question "What if `k` is huge (≥ alphabet size)?"
    Then the constraint is never violated and the answer is `len(s)`. A sane implementation handles this without special-casing — the while never fires.

??? question "What if the alphabet is huge (Unicode)?"
    Hash map still works (O(min(n, alphabet)) space). For ASCII you could use a fixed-size array of 128 ints + a distinct-count integer to avoid the dict.

#### 🐛 Common bugs

- Forgetting to `del char_count[left_char]` when count hits 0 — `len(char_count)` overcounts and the while never exits properly.
- Updating `best` *inside* the while (you'd be measuring shrunk windows, not extended ones).
- Off-by-one in `right - left + 1` — sliding window length is *inclusive* of both endpoints.

---

## 🐛 Common bugs across all sliding-window problems

| Bug | Symptom | Fix |
|---|---|---|
| Updating `best` in the wrong place | Returns wrong answer on small inputs | Longest → after while; Shortest → inside while |
| Not removing zero-count keys from hash map | Off-by-one on distinct counts | `if count == 0: del map[key]` |
| Forgetting the `len(arr) < k` guard | IndexError or wrong answer | Add the guard for fixed-size problems |
| Applying shrink-while-valid to negative numbers | Wrong answer | Switch to prefix sum + deque |
| Initializing `best = 0` for "shortest" | Returns 0 instead of "no valid window" | Initialize `best = inf`, check at end |
| Confusing subarray with subsequence | Solving the wrong problem | Read carefully — sliding window is *contiguous* only |

---

## 🎯 How interviewers ask sliding-window problems

### Common phrasings

| What they say | What it means |
|---|---|
| *"Longest contiguous subarray such that…"* | Variable window, longest |
| *"Smallest subarray with sum ≥ X"* | Variable window, shortest |
| *"Find all anagrams of P in S"* | Fixed window of len(P), char-count match |
| *"Maximum / minimum in every window of size K"* | Fixed window + monotonic deque |
| *"Number of substrings with property X"* | Often at-most-K trick |
| *"At most K of something"* | Variable window, hash-map state |

### What they're testing

1. **Pattern recognition** — do you reach for sliding window without prompting?
2. **Template fluency** — can you write the skeleton in 30 seconds?
3. **State design** — what do you track inside the window? (Sum? Count? Hash map? Deque?)
4. **Boundary reasoning** — when do you record the answer? Inside the while or after?
5. **Why O(n)** — can you explain the amortized argument?

### The 4-step interview flow

1. **Recognize** ("contiguous" + "subarray/substring" → sliding window).
2. **Pick the flavor** (fixed if k is given; variable otherwise).
3. **Decide window state** (sum, count, hash map, deque?).
4. **Decide where to record** (longest = after shrink; shortest = inside shrink).

### Red flags

- Solving with O(n²) brute force and saying "this is the best I can do" — sliding window is *expected* knowledge.
- Writing the template but not being able to explain the amortized O(n).
- Confusing sliding window with two-pointer (related but distinct — see below).

---

## 🔗 How sliding window connects to other patterns

| Pattern | Connection |
|---|---|
| **Two pointers** | Sliding window is a *special case* of two pointers — both pointers move forward only. General two pointers may move toward each other or independently. |
| **Monotonic deque** | Used inside the window to track max/min in O(1) amortized — see Sliding Window Maximum. |
| **Hash map** | Used inside the window to track char counts, distinct counts, last-seen indices. |
| **Prefix sum** | When the array can have negatives, sliding window breaks. Switch to prefix sum + hash map. |
| **Binary search on answer** | Sometimes you binary-search the window length and verify with a sliding-window-style scan. |

---

## ✅ Self-check — 8 questions

??? question "1. What's the difference between fixed and variable window?"
    Fixed: window size is given (`k`), both pointers advance together. Variable: window grows with `right`, shrinks `left` only when a constraint is violated.

??? question "2. Why is the variable-window template O(n), not O(n²)?"
    Both pointers monotonically increase. Each ≤ n moves total → 2n = O(n). Not O(n²) despite the nested loops — count *total* advances, not nesting.

??? question "3. When do you update `best`? Inside or outside the while?"
    Longest-valid problems → outside the while (record once the window is valid).
    Shortest-valid problems → inside the while (record while still valid, before shrinking past it).

??? question "4. Why does the variable-window technique fail with negative numbers?"
    The shrink-when-valid logic assumes removing an element can only *decrease* the window's "violatedness." Negatives break that monotonicity — removing a negative *increases* the sum.

??? question "5. What's the at-most-K trick?"
    `exactlyK(arr) = atMostK(arr) − atMost(K−1)(arr)`. Each `atMostK` is a sliding window. Run twice, subtract. Used for "exactly K distinct" / "exactly K odd numbers" / similar counting problems.

??? question "6. Why do you delete the key when count hits 0 in the hash-map version?"
    Otherwise `len(hash_map)` counts ghost entries (keys with value 0), and the constraint `len > k` becomes wrong.

??? question "7. How is sliding window different from two pointers?"
    Sliding window is a *type* of two-pointer technique where both pointers move forward only. General two-pointer (e.g. 3Sum) may have one pointer move backward, or both pointers move toward each other.

??? question "8. What's the give-away that a problem is sliding window?"
    The word **contiguous** + **subarray/substring** + a constraint about a sum, count, max, or distinct elements. If the problem says **subsequence**, it's not sliding window — it's DP.

---

## 🔁 Where to go from here

- **Next pattern**: Two Pointers (when it lands in Phase 5) — the more general parent of sliding window.
- **Apply it**: solve every problem in [Common across — Arrays](../12-common-across-all-companies/02-arrays-common.md) tagged with two-pointer or sliding window.
- **Cross-reference**: every Google-50 problem in the "sliding window" pattern column on the [Google 50 page](../07-popular-problems/product-based/google-50.md).

> When this page is filled out for the other 19 patterns, the structure stays exactly the same — only the templates, sub-patterns, and deep-dive picks change. The shape is the contract.
