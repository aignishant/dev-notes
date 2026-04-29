# Arrays — common across all companies

> The 25 array problems that show up *everywhere* — product, service, PSU. If your time is limited, solve these first. This page is the **template** for the 15 other "common across companies" topic pages in this section.

<span class="company-tag">Google</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">Microsoft</span> &nbsp; <span class="company-tag">TCS</span> &nbsp; <span class="company-tag">Infosys</span> &nbsp; <span class="company-tag">ISRO</span> &nbsp; <span class="company-tag">DRDO</span> &nbsp; <span class="phase-status phase-done">Phase 14 — Common Across</span>

---

## 📖 How this page is organized

Every "common across companies" topic page in this bible follows the **same five-part shape**:

1. **What "asked everywhere" actually means** — how this list was built.
2. **The patterns that drive these 25** — frequency table.
3. **The 25 questions** — table with difficulty + pattern + status link.
4. **Deep-dives** — 3 representative problems in mini-v3 format.
5. **How to use this page** — solving order, time budget, links to related sections.

Once you've read one, you've read them all.

---

## 🎯 What "asked everywhere" actually means

This list is the **intersection** of three different worlds:

| World | Companies in scope | What they care about |
|---|---|---|
| **Product / FAANG-style** | Google, Meta, Amazon, Microsoft, Adobe, Apple, Netflix, Uber, Stripe, Anthropic, OpenAI… | Algorithmic depth, code quality, system design |
| **Service / consulting** | TCS, Infosys, Wipro, HCL, Cognizant, Capgemini, Accenture, IBM India… | Coverage of fundamentals, ability to write correct code under time pressure |
| **PSU / R&D** | ISRO, DRDO, BARC, BEL, HAL, ECIL, RBI Grade B, SEBI… | Strong CS basics, written tests on data structures + algorithms |

The 25 questions on this page have shown up in **at least all three** consistently over the last 5 years. If a problem is on this list, you can be ~95% sure you'll see it (or a near-variant) in one of your interviews.

!!! tip "The safety-net rule"
    Solve **every problem on this page** before any other prep. Even if you only had 2 weeks total, these 25 + the corresponding patterns are the highest ROI you'll get.

---

## 🧩 Patterns that drive these 25

| Pattern | Frequency | Problems on this page |
|---|---|---|
| **Two pointers** | ⭐⭐⭐⭐⭐ | Reverse, Move Zeros, Remove Dup, 3Sum, Container, Trap Rain Water |
| **Hash map / hash set** | ⭐⭐⭐⭐⭐ | Two Sum, Longest Consecutive, Subarray Sum K |
| **Prefix / suffix arrays** | ⭐⭐⭐⭐ | Product Except Self, Max Product Subarray, Subarray Sum K |
| **Kadane / 1D DP** | ⭐⭐⭐⭐ | Max Subarray, Max Product Subarray, Best Time to Buy/Sell |
| **Modified binary search** | ⭐⭐⭐⭐ | Search Rotated, First/Last Position, Find Peak, Median of Two |
| **In-place / cyclic sort** | ⭐⭐⭐ | Find Missing, Find Duplicate, First Missing Positive, Sort Colors |
| **Three-reverse / rotate** | ⭐⭐⭐ | Rotate Array by K |
| **Merge two sorted** | ⭐⭐⭐ | Merge Sorted Arrays, Median of Two |

If you master these 8 patterns alone, you've solved 80% of all array-flavored interview questions, regardless of company.

---

## 📋 The 25 questions

Difficulty pill conventions:

- <span class="diff-easy">Easy</span> &nbsp; <span class="diff-medium">Medium</span> &nbsp; <span class="diff-hard">Hard</span>

Status:

- ✅ = full v3 solution exists in this bible (link given)
- 📝 = covered in mini-v3 below
- 🚧 = lands in Phase 14 (full v3 solutions for every common-across page)

### Fundamentals — start here (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Reverse an Array in-place | <span class="diff-easy">Easy</span> | Two pointers (opposite ends) | [📝](#deep-dive-1-reverse-an-array-in-place) |
| 2 | Find Maximum / Minimum | <span class="diff-easy">Easy</span> | Linear scan | 🚧 |
| 3 | Find Min and Max simultaneously | <span class="diff-easy">Easy</span> | Pair-wise tournament | 🚧 |
| 4 | Move Zeros to End | <span class="diff-easy">Easy</span> | Two pointers (read/write) | 🚧 |
| 5 | Remove Duplicates from Sorted Array | <span class="diff-easy">Easy</span> | Two pointers (read/write) | 🚧 |

### Searching & rotation (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 6 | Rotate Array by K | <span class="diff-medium">Medium</span> | Three-reverse trick | [📝](#deep-dive-2-rotate-array-by-k) |
| 7 | Search in Rotated Sorted Array | <span class="diff-medium">Medium</span> | Modified binary search | [✅](../02-data-structures/arrays/01-array-basics.md) |
| 8 | First and Last Position of element | <span class="diff-medium">Medium</span> | Modified binary search | 🚧 |
| 9 | Find Peak Element | <span class="diff-medium">Medium</span> | Modified binary search | [✅](../02-data-structures/arrays/01-array-basics.md) |

### Sums & subarrays (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 10 | Two Sum | <span class="diff-easy">Easy</span> | Hash map | [✅](../02-data-structures/arrays/01-array-basics.md) |
| 11 | 3Sum | <span class="diff-medium">Medium</span> | Sort + two pointers | [✅](../02-data-structures/arrays/01-array-basics.md) |
| 12 | Maximum Subarray (Kadane's) | <span class="diff-medium">Medium</span> | 1D DP | [✅](../02-data-structures/arrays/01-array-basics.md) |
| 13 | Maximum Product Subarray | <span class="diff-medium">Medium</span> | Two-state DP | [✅](../02-data-structures/arrays/01-array-basics.md) |
| 14 | Subarray Sum Equals K | <span class="diff-medium">Medium</span> | Prefix sum + hash | [✅](../02-data-structures/arrays/01-array-basics.md) |

### Stocks & water (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 15 | Best Time to Buy and Sell Stock | <span class="diff-easy">Easy</span> | Running min | [✅](../02-data-structures/arrays/01-array-basics.md) |
| 16 | Container With Most Water | <span class="diff-medium">Medium</span> | Two pointers | [✅](../02-data-structures/arrays/01-array-basics.md) |
| 17 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Two pointers + max tracking | [✅](../02-data-structures/arrays/01-array-basics.md) |

### Missing, duplicate, in-place tricks (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 18 | Find Missing Number (1..n) | <span class="diff-easy">Easy</span> | XOR / sum invariant | [📝](#deep-dive-3-find-missing-number-in-1n) |
| 19 | Find the Duplicate Number | <span class="diff-medium">Medium</span> | Floyd cycle / negate marker | [✅](../02-data-structures/arrays/01-array-basics.md) |
| 20 | First Missing Positive | <span class="diff-hard">Hard</span> | Cyclic sort | [✅](../02-data-structures/arrays/01-array-basics.md) |
| 21 | Sort Colors (Dutch Flag) | <span class="diff-medium">Medium</span> | 3-pointer sweep | [✅](../02-data-structures/arrays/01-array-basics.md) |

### Merge & multi-array (2)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 22 | Merge Two Sorted Arrays in-place | <span class="diff-easy">Easy</span> | Two pointers from end | [✅](../02-data-structures/arrays/01-array-basics.md) |
| 23 | Median of Two Sorted Arrays | <span class="diff-hard">Hard</span> | Binary search on partition | [✅](../02-data-structures/arrays/01-array-basics.md) |

### Hash-set tricks & products (2)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 24 | Longest Consecutive Sequence | <span class="diff-medium">Medium</span> | Hash set + start detection | [✅](../02-data-structures/arrays/01-array-basics.md) |
| 25 | Product of Array Except Self | <span class="diff-medium">Medium</span> | Prefix + suffix | [✅](../02-data-structures/arrays/01-array-basics.md) |

---

## 🔬 Deep-dives — 3 universally-asked walkthroughs

Picked because:

- Each is **asked at every kind of company** — FAANG to TCS to ISRO.
- Each shows a **distinct fundamental** (in-place two pointers, the three-reverse rotate trick, the XOR invariant).
- Each is the **simplest version** of a pattern you'll see harder variants of in the chapter.

Format: thinking process → optimal solution → dry run → complexity → variant follow-ups.

---

### Deep-dive 1: Reverse an array in-place

<span class="diff-easy">Easy</span> &nbsp; <span class="company-tag">Everyone</span>

> Given an array, reverse it **without using extra space**.

#### 📖 Story mode

You have a row of cards face-up. Mirror them — the first becomes the last, the last becomes the first. You can only swap two cards at a time, no holding spare cards aside.

#### 🧠 Thinking process

- **Brute force**: copy to a new array in reverse order. O(n) time, **O(n) space** — disqualified by "in-place."
- **Insight**: swap pairs `(0, n-1), (1, n-2), …` until the two pointers cross. Each swap fixes two elements.

#### 🐍 Optimal solution

```python
def reverse_in_place(arr: list[int]) -> None:
    """Reverse arr in-place. Mutates the input."""
    left, right = 0, len(arr) - 1
    while left < right:
        arr[left], arr[right] = arr[right], arr[left]
        left += 1
        right -= 1
```

That's it. No extra array, no recursion overhead, every line traceable.

!!! tip "Pythonic alternatives"
    `arr.reverse()` (in-place, built-in) and `arr[::-1]` (creates a new list, *not* in-place) both exist. **Always implement the manual version first** in a service-company interview — the interviewer wants to see you know the underlying algorithm, not just the standard library.

#### 🔍 Dry run on `[1, 2, 3, 4, 5]`

| left | right | swap? | array |
|---|---|---|---|
| 0 | 4 | yes (1↔5) | [5, 2, 3, 4, 1] |
| 1 | 3 | yes (2↔4) | [5, 4, 3, 2, 1] |
| 2 | 2 | stop (left ≥ right) | [5, 4, 3, 2, 1] |

For an even-length array `[1, 2, 3, 4]`, the loop runs twice (0↔3, 1↔2) and exits when `left = 2, right = 1`.

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **In-place two pointers** | O(n) | O(1) |

#### 🔄 Common follow-ups

??? question "Reverse only a sub-array `arr[i..j]`."
    Same idea — start with `left = i, right = j`. This is a building block for several other problems (rotate, reverse words in a string, etc.).

??? question "Reverse a string in-place in Python."
    Strings are immutable in Python — you cannot reverse in place. Convert to a list first, reverse, then join. The interviewer is testing whether you know this language quirk.

??? question "Reverse a linked list in-place."
    Different DS, same idea: walk once, swap `prev`/`next` pointers. See the linked list chapter when it lands.

??? question "Reverse only when a condition is met (e.g. reverse every K elements)."
    See LeetCode 25 (Reverse Nodes in K-Group) and the "rotate" problem below — both build on this primitive.

#### 🐛 Common bugs

- Using `<= ` instead of `<` in the loop — causes the middle element to swap with itself in odd-length arrays (harmless but wasted work) or, with off-by-ones, swaps elements twice and undoes the reverse.
- Forgetting that `arr[left], arr[right] = arr[right], arr[left]` is a *single* atomic swap in Python — beginners sometimes write it as two lines and lose the value.

---

### Deep-dive 2: Rotate array by K

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Everyone</span>

> Rotate `nums` to the right by `k` steps. Do it **in-place** with O(1) extra space.

Example: `[1, 2, 3, 4, 5, 6, 7]` with `k = 3` → `[5, 6, 7, 1, 2, 3, 4]`.

#### 📖 Story mode

A queue of people: every minute, the last 3 cycle to the front. You can't use a second queue. How do you do it with just shuffling in place?

#### 🧠 Thinking process

- **Brute force 1**: shift every element right by 1, repeat `k` times. O(n·k).
- **Brute force 2**: use a copy of size n. Place each element at its target index. O(n) time, **O(n) space** — disqualified.
- **Insight (the magic)**: three reverses!
    1. Reverse the whole array: `[7, 6, 5, 4, 3, 2, 1]`
    2. Reverse the first `k` elements: `[5, 6, 7, 4, 3, 2, 1]`
    3. Reverse the last `n - k` elements: `[5, 6, 7, 1, 2, 3, 4]` ✓

This is one of the most beautiful tricks in array problems. Once you've seen it, you can never un-see it.

#### 🐍 Optimal solution

```python
def rotate(nums: list[int], k: int) -> None:
    """Rotate nums right by k in-place. Mutates."""
    n = len(nums)
    k %= n                                # normalize: k can be > n
    if k == 0:
        return

    def reverse(left: int, right: int) -> None:
        while left < right:
            nums[left], nums[right] = nums[right], nums[left]
            left += 1
            right -= 1

    reverse(0, n - 1)        # whole
    reverse(0, k - 1)        # first k
    reverse(k, n - 1)        # rest
```

The helper `reverse` is the primitive from deep-dive 1. Composing primitives is what senior engineers do.

#### 🔍 Dry run on `[1,2,3,4,5,6,7]`, `k=3`

| Step | Array |
|---|---|
| Start | `[1, 2, 3, 4, 5, 6, 7]` |
| Reverse all (0..6) | `[7, 6, 5, 4, 3, 2, 1]` |
| Reverse first k (0..2) | `[5, 6, 7, 4, 3, 2, 1]` |
| Reverse rest (3..6) | `[5, 6, 7, 1, 2, 3, 4]` ✓ |

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **Three-reverse** | O(n) | O(1) |

Each element gets touched at most twice (once in the full reverse, once in either the prefix or suffix reverse). Two passes total → O(n).

#### 🔄 Common follow-ups

??? question "Rotate **left** by K instead of right."
    Equivalent to rotating right by `n - k`. Or do the same three reverses with the splits at `k` (not `n - k`). Easy reframe.

??? question "What if K is **negative**?"
    `k = ((k % n) + n) % n` normalizes both signs. Walk through both cases at the whiteboard — interviewers love when you spot the sign issue.

??? question "Use cyclic-replacement rotation instead of three-reverse."
    Walk i = 0; jump to `(i + k) % n`; place the element; continue until you've placed `n` elements (using a counter — *not* a `seen` set). Watch for cycles when `gcd(n, k) > 1`. This is harder to get right under pressure — interviewers respect that you know it exists, but you'd typically code three-reverse.

??? question "Rotate a 2D matrix by 90° clockwise."
    Same idea, different axis: transpose, then reverse each row. Composes the same primitive (reverse) on a different shape.

??? question "What if extra space were allowed?"
    `nums[:] = nums[-k:] + nums[:-k]` — one-liner using slicing. Mention it, then say "but the in-place version is what you asked for."

#### 🐛 Common bugs

- Forgetting `k %= n` — when `k > n`, you end up rotating multiple full cycles unnecessarily, or worse, slicing out of bounds.
- Returning a new array instead of mutating — read the problem statement carefully; "in-place" is a constraint.
- Reversing prefix and suffix with the wrong indices (off-by-one on `k - 1` vs `k`).

---

### Deep-dive 3: Find missing number in 1..n

<span class="diff-easy">Easy</span> &nbsp; <span class="company-tag">Everyone</span>

> An array contains `n - 1` distinct numbers from `1` to `n`. Find the missing one.

Example: `n = 5`, `arr = [3, 1, 4, 5]` → missing is `2`.

#### 📖 Story mode

A teacher has a register with rolls 1 to 30. One student is absent. Without going through the names one by one, can you tell who?

The teacher's trick: count everyone present, subtract their roll-number sum from `1+2+…+30`. Whatever's left is the missing roll.

#### 🧠 Thinking process

- **Brute force**: sort `arr`, walk through, find the gap. O(n log n).
- **Hash set**: insert all of `arr`, check 1..n for the missing one. O(n) time, **O(n) space**.
- **Math invariant**: `1 + 2 + … + n = n(n+1)/2`. Subtract the actual sum of `arr` from this expected sum → the missing number. O(n) time, **O(1) space**.
- **XOR invariant**: same idea but XOR-based. `(1 ^ 2 ^ … ^ n) ^ (arr[0] ^ arr[1] ^ …)` cancels every present number, leaving only the missing one. Avoids potential overflow in non-Python languages.

The XOR version is the **interviewer favorite** — it shows you know that XOR is its own inverse and that `a ^ a = 0`.

#### 🐍 Optimal solution

=== "Sum-based"

    ```python
    def missing_number(arr: list[int]) -> int:
        """Return the missing number from 1..n given n-1 of them."""
        n = len(arr) + 1                 # there are n-1 elements, missing one
        expected = n * (n + 1) // 2
        return expected - sum(arr)
    ```

=== "XOR-based"

    ```python
    def missing_number_xor(arr: list[int]) -> int:
        """XOR-based: avoids any overflow, no math needed."""
        n = len(arr) + 1
        x = 0
        for i in range(1, n + 1):
            x ^= i
        for v in arr:
            x ^= v
        return x
    ```

Both are O(n) time, O(1) space. The sum version is shorter; the XOR version is overflow-safe.

#### 🔍 Dry run on `arr = [3, 1, 4, 5]`

**Sum version**: `n = 5`, expected = `15`, sum(arr) = `13`. Missing = `2`. ✓

**XOR version**:

| step | x |
|---|---|
| init | 0 |
| ^=1 | 1 |
| ^=2 | 3 |
| ^=3 | 0 |
| ^=4 | 4 |
| ^=5 | 1 |
| ^=3 | 2 |
| ^=1 | 3 |
| ^=4 | 7 |
| ^=5 | 2 |

Final: `2`. ✓

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| Sort + scan | O(n log n) | O(1) or O(n) |
| Hash set | O(n) | O(n) |
| **Sum / XOR** | **O(n)** | **O(1)** |

#### 🔄 Common follow-ups

??? question "What if **two** numbers are missing instead of one?"
    Sum gives `a + b`, sum-of-squares gives `a² + b²` — solve the 2-equation system. Or XOR: get `a ^ b`, find any set bit, partition the array around that bit, XOR each partition separately. (LeetCode 260 — the second version is what they want.)

??? question "What if numbers are 0..n instead of 1..n?"
    Same algorithm, just adjust `expected = n * (n + 1) / 2` (sum of 0..n) and the XOR loop range to `range(0, n + 1)`.

??? question "What if **one number is missing AND one is duplicated**?"
    Use sum (gives `missing - duplicate`) and sum-of-squares (gives `missing² - duplicate²`). Solve. (LeetCode 645.)

??? question "What if `n` is huge and `arr` is a stream?"
    Sum still works as a running invariant — accumulate as elements arrive. XOR works identically. Both are streaming-friendly. Hash set isn't.

??? question "What if numbers are unbounded (not in 1..n)?"
    Now sum/XOR don't give you a unique answer. You need a hash set, or sort + scan. The "1..n" constraint is what makes the math invariants work.

#### 🐛 Common bugs

- `n = len(arr)` instead of `n = len(arr) + 1` — off-by-one is the #1 bug here.
- Using `n * (n + 1) / 2` instead of `// 2` in Python — gives a float, returning `2.0` instead of `2` (cosmetic, but interviewers notice).
- Trying XOR on the array values without first XORing 1..n — you only get one half of the cancellation.

---

## 🗓️ How to use this page

### Solving order — the 3-week plan

If you have **3 weeks** total and want maximum coverage:

| Week | Focus | Problems |
|---|---|---|
| 1 | Fundamentals + searching | 1-9 (in order) |
| 2 | Sums, subarrays, stocks, water | 10-17 |
| 3 | Tricks + multi-array + hash | 18-25 |

If you have **1 week**, solve only the ✅ ones (already in the chapter). They're the highest-yield 12 of the 25.

### Time budget per problem

- <span class="diff-easy">Easy</span>: 15-20 min including dry-run + complexity discussion.
- <span class="diff-medium">Medium</span>: 25-35 min.
- <span class="diff-hard">Hard</span>: 40-60 min on first attempt; 25-30 min on second.

If you're spending 60+ min on a medium, **stop and read the solution** — you're past the point of productive struggle.

### Cross-reference

- **Pattern depth**: when a problem on this page introduces a pattern you don't know, jump to [Patterns](../04-patterns/index.md) and read that chapter before moving on.
- **Company-specific framing**: see [Google 50](../07-popular-problems/product-based/google-50.md) for the Google version of these. Many overlap.
- **Full v3 walkthroughs**: 17 of the 25 problems are fully solved in [Arrays — chapter](../02-data-structures/arrays/01-array-basics.md). The remaining 8 land in Phase 14.

---

## 🔁 Where to go from here

- **Strings — common across companies**: the next topic page in this section, when it lands in Phase 14.
- **[Top 100 by pattern](../07-popular-problems/index.md)**: the highest-leverage 100 problems, organized by which of the 20 patterns they use.
- **[Behavioral](../11-behavioral/index.md)**: once you have the algorithmic muscle, layer on STAR-method storytelling.

> When this page is filled out for the other 15 topics, the structure stays exactly the same — only the table contents and the deep-dive picks change. The five-part shape is the contract.
