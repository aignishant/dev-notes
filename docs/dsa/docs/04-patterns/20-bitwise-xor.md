# Bitwise XOR

> The smallest, sharpest pattern in the bible. **XOR has three magic properties** — `x ^ 0 = x`, `x ^ x = 0`, and `x ^ y ^ x = y` — and an entire family of "find the odd one out" problems collapses to a single linear pass with no extra space. Single Number, Missing Number, Two Singles in a duplicated array, Maximum XOR of Two Numbers (with a trie), Sum of Two Integers without `+`, and the bit-tricks playbook (`n & (n-1)`, `n & -n`) all live here.

<span class="phase-status phase-done">Phase 5 — Patterns</span>

---

## 📖 What is the Bitwise XOR pattern?

XOR (`^`, exclusive-or) returns 1 iff exactly one input bit is 1. Three properties make it the workhorse of the pattern:

1. **Identity:** `x ^ 0 = x`. XOR with zero leaves a value unchanged.
2. **Self-cancellation:** `x ^ x = 0`. Any value XORed with itself becomes zero.
3. **Commutative + associative:** `(a ^ b) ^ c = a ^ (b ^ c) = a ^ c ^ b`. Order of XOR operations doesn't matter.

Combined: **XOR-ing a stream of numbers cancels every value that appears an even number of times and leaves the XOR of the values that appear an odd number of times.** That single observation drives the whole pattern.

The mental model: XOR is a **counter that's collapsed mod 2 per bit**. Each bit position counts independently and only remembers parity. That's why duplicates vanish — pairs of 1s cancel.

!!! tip "The signal — when to reach for Bitwise XOR"
    Reach for it when:

    - "Every element appears **k times** except one (or two)." Try XOR (k=2) or per-bit-mod-k (k=3 etc.).
    - "Find the **missing** number" / "find the duplicate" in a known range.
    - "Maximum / minimum XOR of two numbers in an array." → bitwise trie.
    - "Add two numbers **without using `+` or `-`**." → XOR + AND-shift.
    - "Count set bits" / "is power of two" / "lowest set bit." → `n & (n-1)` / `n & -n`.

    Don't reach for it when:

    - Values appear arbitrarily many times — XOR can't disentangle parity beyond 2.
    - You need the **count** of duplicates, not just the existence — use a hash map.
    - The data is non-integer or the bit interpretation is meaningless — XOR is a number-theoretic trick, not a generic dedup.

---

## 🧩 The five flavors

### Flavor 1: XOR-everything to find the odd one

The single linear pass that solves Single Number (LC 136), Missing Number (LC 268), and Find the Duplicate via XOR (educational form).

```python
def single_number(nums: list[int]) -> int:
    """LC 136 — every element appears twice except one."""
    result = 0
    for x in nums:
        result ^= x                                               # (1) duplicates cancel; the single survives
    return result
```

1. The XOR identity does all the work. After the loop, every number that appeared twice has self-cancelled to 0; the lone number XORed with 0 is itself.

```python
def missing_number(nums: list[int]) -> int:
    """LC 268 — array contains n distinct numbers from [0..n], find the missing one."""
    result = len(nums)                                            # (1) seed with n
    for i, x in enumerate(nums):
        result ^= i ^ x                                           # (2) XOR all indices and values
    return result
```

1. Indices range over `[0..n-1]`; values range over `[0..n]` minus one. Seeding with `n` covers the index `n` that the loop doesn't see.
2. Every value that's both an index and a value cancels. The missing number is the lone survivor.

**Examples:** Single Number (LC 136), Missing Number (LC 268), Find the Difference (LC 389).

### Flavor 2: Two singles via XOR + bit split

When two numbers each appear once and the rest appear twice (LC 260).

```python
def single_number_iii(nums: list[int]) -> list[int]:
    """LC 260 — exactly two numbers appear once; rest appear twice."""
    xor_all = 0
    for x in nums:
        xor_all ^= x                                              # (1) xor_all = a ^ b (the two singles)

    diff_bit = xor_all & -xor_all                                 # (2) lowest set bit — a bit where a and b differ

    a = b = 0
    for x in nums:
        if x & diff_bit:                                          # (3) split into two groups by that bit
            a ^= x
        else:
            b ^= x

    return [a, b]
```

1. Pairs cancel; the result is `a ^ b` where `a` and `b` are the two unique numbers. This is non-zero (because `a ≠ b`), so at least one bit differs.
2. `n & -n` isolates the **lowest set bit** of `n` (a fundamental two's-complement trick — see Flavor 5). Any bit set in `xor_all` is a position where `a` and `b` disagree; we pick the lowest.
3. Partition the array by this bit. `a` is in one group, `b` in the other; duplicates stay together. XOR each group separately to recover its single.

**Examples:** Single Number III (LC 260).

### Flavor 3: Per-bit modular counting (every k-th)

When elements repeat **three** times (or any k > 2) except one. XOR can't natively handle k=3 — it's a mod-2 trick — so count each bit independently mod k.

```python
def single_number_ii(nums: list[int]) -> int:
    """LC 137 — every element appears three times except one."""
    ones = twos = 0
    for x in nums:
        ones = (ones ^ x) & ~twos                                 # (1) bit appears once if it was 0 and is now 1, but not in 'twos'
        twos = (twos ^ x) & ~ones                                 #     bit appears twice if … you know what, just trust the table
    return ones
```

1. The two-state machine tracks each bit as `(ones, twos)` — count of times that bit has been seen mod 3 (00 → 01 → 10 → 00). The compound assignment is the standard trick to keep it branchless.

A more readable version uses generic per-bit counting:

```python
def single_number_ii_readable(nums: list[int]) -> int:
    result = 0
    for bit in range(32):
        count = sum((x >> bit) & 1 for x in nums)
        if count % 3:
            result |= 1 << bit
    if result >= (1 << 31):                                       # (1) sign-extend for negative numbers
        result -= 1 << 32
    return result
```

1. Python ints are arbitrary precision, so we manually wrap into 32-bit signed-int territory if the input is negative.

**Examples:** Single Number II (LC 137), Single Number variants for any odd-out-among-k-times scenario.

### Flavor 4: Bitwise trie for max XOR of pairs

When you need the **maximum** XOR over all pairs (LC 421), build a trie indexed by bits.

```python
def find_maximum_xor(nums: list[int]) -> int:
    """LC 421 — max XOR of any two elements."""
    BITS = max(nums).bit_length() if nums else 0
    root: dict = {}

    for x in nums:                                                # (1) insert each number bit-by-bit (MSB first)
        node = root
        for i in range(BITS - 1, -1, -1):
            b = (x >> i) & 1
            node = node.setdefault(b, {})

    best = 0
    for x in nums:                                                # (2) for each x, greedily walk the trie taking the opposite bit when possible
        node = root
        cur = 0
        for i in range(BITS - 1, -1, -1):
            b = (x >> i) & 1
            opp = 1 - b
            if opp in node:
                cur |= 1 << i
                node = node[opp]
            else:
                node = node[b]
        best = max(best, cur)

    return best
```

1. Build a binary trie from MSB downward. Each path from root to leaf is one number's bits.
2. To maximise `x ^ y`, at each bit prefer the **opposite** bit of `x` (so that XOR contributes 1 there). Greedy at each level — MSB choices dominate.

**Examples:** Maximum XOR of Two Numbers in Array (LC 421), Maximum XOR With Element From Array (LC 1707).

### Flavor 5: Single-number bit tricks

The toolkit that powers the rest of the pattern. Memorise these idioms.

```python
def hamming_weight(n: int) -> int:
    """LC 191 — number of 1 bits."""
    count = 0
    while n:
        n &= n - 1                                                # (1) clears the lowest set bit
        count += 1
    return count


def is_power_of_two(n: int) -> bool:
    """LC 231."""
    return n > 0 and (n & (n - 1)) == 0                           # (2) exactly one set bit


def lowest_set_bit(n: int) -> int:
    """Isolate the lowest set bit (a power of 2)."""
    return n & -n                                                 # (3) two's-complement magic


def get_sum(a: int, b: int) -> int:
    """LC 371 — add two integers without using + or -."""
    MASK = 0xFFFFFFFF
    while b:
        a, b = (a ^ b) & MASK, ((a & b) << 1) & MASK              # (4) XOR is sum w/o carry; AND<<1 is the carry
    return a if a < 0x80000000 else ~(a ^ MASK)                   # (5) sign-extend
```

1. `n & (n-1)` clears the **lowest set bit**. Iterating until zero counts set bits in O(popcount) instead of O(bits).
2. A power of two has exactly one set bit; `n - 1` is all ones below it; AND is 0.
3. `n & -n` isolates the lowest set bit. In two's complement, `-n = ~n + 1`, which flips every bit *and then* propagates a carry up to the lowest 1, making it the only bit they share.
4. Adder loop: XOR is the no-carry sum; `(a & b) << 1` is the carry-out. Repeat until no carry.
5. Python ints are unbounded; mask to 32 bits and sign-extend manually.

**Examples:** Number of 1 Bits (LC 191), Power of Two (LC 231), Power of Four (LC 342), Counting Bits (LC 338), Sum of Two Integers (LC 371), Reverse Bits (LC 190), Bitwise AND of Numbers Range (LC 201).

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | XOR everything | Find the odd one out (k=2) | LC 136 / 268 | `result ^= x` over the stream |
| 2 | Split by lowest set bit | Two odd-ones-out | LC 260 | `xor_all & -xor_all` to find a discriminating bit |
| 3 | Per-bit mod-k count | Odd one among k-times duplicates | LC 137 | Sum each bit mod k; reassemble |
| 4 | Bitwise trie (max XOR) | Best pair under XOR | LC 421 | MSB-first trie, greedy opposite-bit walk |
| 5 | `n & (n-1)` | Clear lowest set bit | LC 191, LC 231 | Counts bits / detects powers of two |
| 6 | `n & -n` | Isolate lowest set bit | LC 260 | Two's-complement self-and-negative trick |
| 7 | XOR-as-sum-without-carry | `+` from `^` and `&` | LC 371 | XOR + (AND << 1) carry loop |

---

## 📋 Twenty problems on this pattern

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Single Number | 136 | <span class="diff-easy">Easy</span> | XOR everything | 📝 |
| 2 | Single Number II | 137 | <span class="diff-medium">Medium</span> | Per-bit mod-3 | 📝 |
| 3 | Single Number III | 260 | <span class="diff-medium">Medium</span> | Split by lowest set bit | 📝 |
| 4 | Missing Number | 268 | <span class="diff-easy">Easy</span> | XOR with index | 📝 |
| 5 | Find the Difference | 389 | <span class="diff-easy">Easy</span> | XOR everything | 📝 |
| 6 | Number of 1 Bits | 191 | <span class="diff-easy">Easy</span> | `n & (n-1)` loop | 📝 |
| 7 | Counting Bits | 338 | <span class="diff-easy">Easy</span> | DP via `n >> 1` + low bit | 📝 |
| 8 | Power of Two | 231 | <span class="diff-easy">Easy</span> | `n & (n-1) == 0` | 📝 |
| 9 | Power of Four | 342 | <span class="diff-easy">Easy</span> | Power-of-two + bit-position mask | 📝 |
| 10 | Reverse Bits | 190 | <span class="diff-easy">Easy</span> | Bit-by-bit / divide-and-conquer | 📝 |
| 11 | Sum of Two Integers | 371 | <span class="diff-medium">Medium</span> | XOR + carry loop | 📝 |
| 12 | Maximum XOR of Two Numbers in Array | 421 | <span class="diff-medium">Medium</span> | Bitwise trie | 📝 |
| 13 | Maximum XOR With Element From Array | 1707 | <span class="diff-hard">Hard</span> | Offline trie + sort by limit | 📝 |
| 14 | XOR Queries of a Subarray | 1310 | <span class="diff-medium">Medium</span> | Prefix XOR | 📝 |
| 15 | Decode XOR-ed Array | 1720 | <span class="diff-easy">Easy</span> | Reverse XOR pairing | 📝 |
| 16 | Decode XOR-ed Permutation | 1734 | <span class="diff-medium">Medium</span> | XOR algebra on permutations | 📝 |
| 17 | Bitwise AND of Numbers Range | 201 | <span class="diff-medium">Medium</span> | Common prefix via shift | 📝 |
| 18 | Total Hamming Distance | 477 | <span class="diff-medium">Medium</span> | Per-bit count contributions | 📝 |
| 19 | Concatenation of Consecutive Binary Numbers | 1680 | <span class="diff-medium">Medium</span> | Bit-length tricks | 📝 |
| 20 | UTF-8 Validation | 393 | <span class="diff-medium">Medium</span> | Mask + shift parsing | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Single Number (LC 136)

> Given a non-empty array of integers where every element appears twice except one, find the single one. O(n) time, O(1) space.

The poster child for the pattern. **One line.**

```python
def single_number(nums: list[int]) -> int:
    result = 0
    for x in nums:
        result ^= x
    return result
```

#### Why it works

XOR is **commutative and associative**, so the order doesn't matter — the result equals `nums[0] ^ nums[1] ^ … ^ nums[n-1]` no matter how we group the operations.

Group all the duplicates together: each pair becomes `x ^ x = 0`. All the zeros XOR together to 0. Finally, `0 ^ single = single`. Done.

#### Dry run on `[4, 1, 2, 1, 2]`

| step | x | result before | result after |
|------|---|---------------|--------------|
| 0 | 4 | `0` | `0 ^ 4 = 4` |
| 1 | 1 | `4` | `4 ^ 1 = 5` |
| 2 | 2 | `5` | `5 ^ 2 = 7` |
| 3 | 1 | `7` | `7 ^ 1 = 6` |
| 4 | 2 | `6` | `6 ^ 2 = 4` |

Output: 4. ✓

#### Why a hash-map solution is worse

A hash map gives O(n) time but **O(n) space** and has cache misses. The XOR solution is single-register, branchless, optimal. In an interview, naming the hash-map approach as "the obvious one" and then producing the XOR solution shows you understand the constraint.

#### Variations

- **Find the Difference (LC 389):** XOR all characters of both strings. The duplicates cancel; the extra survives. `chr(reduce(xor, map(ord, s + t)))`.
- **Missing Number (LC 268):** XOR all numbers and all indices. The matched index/value pairs cancel; the missing number remains.

#### Complexity

- **Time:** O(n).
- **Space:** O(1).

---

### Deep-dive 2 — Single Number III (LC 260)

> Given an array where exactly two elements appear once and all others appear twice, return the two singles. O(n) time, O(1) space.

The clever extension. Pure XOR can't separate two singles — `a ^ b` is one number. The trick is to **partition the array** by a bit where `a` and `b` differ.

#### Code (re-stated)

```python
def single_number_iii(nums: list[int]) -> list[int]:
    xor_all = 0
    for x in nums:
        xor_all ^= x

    diff_bit = xor_all & -xor_all

    a = b = 0
    for x in nums:
        if x & diff_bit:
            a ^= x
        else:
            b ^= x

    return [a, b]
```

#### Step 1: collapse to `a ^ b`

XOR everything. Pairs cancel. Result is `a ^ b`.

#### Step 2: find a bit where `a` and `b` differ

`a ≠ b`, so `a ^ b ≠ 0` — there's at least one bit set in `xor_all`. Any such bit works. We pick the **lowest set bit** with `n & -n`. This is the cleanest expression.

##### Why `n & -n` isolates the lowest set bit

In two's-complement, `-n = ~n + 1`. Walk through `n = 0b01101100`:

```
n         = 0b01101100
~n        = 0b10010011
~n + 1    = 0b10010100   = -n
n & -n    = 0b00000100   ← only the lowest set bit survives
```

The carry from the +1 in `~n + 1` propagates exactly up to (and flips) the lowest set bit of the original `n`. That's the one bit that's set in **both** `n` and `-n`.

#### Step 3: partition by that bit

Every duplicate has the same value for *every* bit, so it lands in the same bucket as its twin. Pairs cancel within their bucket. `a` and `b` differ at `diff_bit` so they land in different buckets. Each bucket XORs to a single value: one bucket gives `a`, the other gives `b`.

#### Dry run on `[1, 2, 1, 3, 2, 5]`

`xor_all`:

`0 ^ 1 = 1`, `1 ^ 2 = 3`, `3 ^ 1 = 2`, `2 ^ 3 = 1`, `1 ^ 2 = 3`, `3 ^ 5 = 6 = 0b110`.

`diff_bit = 6 & -6 = 0b110 & 0b...11111010 = 0b010 = 2`.

Partition:

| x | x & 2 | bucket |
|---|-------|--------|
| 1 | 0 | b |
| 2 | 2 | a |
| 1 | 0 | b |
| 3 | 2 | a |
| 2 | 2 | a |
| 5 | 0 | b |

`a = 2 ^ 3 ^ 2 = 3`. `b = 1 ^ 1 ^ 5 = 5`. Output: `[3, 5]`. ✓

#### Why no other bit position works equally well

Any set bit of `xor_all` partitions correctly. We pick the lowest because `n & -n` is a one-instruction expression. Picking the highest set bit needs a `bit_length() - 1` computation. Same correctness, slightly more code.

#### Complexity

- **Time:** O(n) — two linear passes.
- **Space:** O(1).

---

### Deep-dive 3 — Maximum XOR of Two Numbers in Array (LC 421)

> Given an integer array, find the maximum XOR of `nums[i] ^ nums[j]` over all pairs. O(n · BITS) time.

The brute force is O(n²). The smarter approach is a **bitwise trie**: a tree where each level represents a bit position.

#### The intuition: greedy MSB-first

To maximise XOR, we want the **highest bits** to differ. If two numbers' MSBs differ, that bit contributes `2^(BITS-1)` to their XOR — more than every lower bit combined. So:

1. Insert all numbers into a binary trie indexed MSB-first.
2. For each number `x`, walk the trie greedily: at each bit, prefer the **opposite** bit (because that's what makes the XOR bit = 1). If the opposite branch exists in the trie, take it. Otherwise, take the same-bit branch.
3. The path you walk is the partner that maximises XOR with `x`. Track the running XOR; the max over all `x` is the answer.

#### Code (re-stated)

```python
def find_maximum_xor(nums: list[int]) -> int:
    BITS = max(nums).bit_length() if nums else 0
    root: dict = {}

    for x in nums:
        node = root
        for i in range(BITS - 1, -1, -1):
            b = (x >> i) & 1
            node = node.setdefault(b, {})

    best = 0
    for x in nums:
        node = root
        cur = 0
        for i in range(BITS - 1, -1, -1):
            b = (x >> i) & 1
            opp = 1 - b
            if opp in node:
                cur |= 1 << i
                node = node[opp]
            else:
                node = node[b]
        best = max(best, cur)

    return best
```

#### Dry run on `nums = [3, 10, 5, 25, 2, 8]`

Max value is 25; `BITS = 5` (since `25 = 0b11001`). Numbers in 5-bit binary:

| x | bits |
|----|------|
| 3 | 00011 |
| 10 | 01010 |
| 5 | 00101 |
| 25 | 11001 |
| 2 | 00010 |
| 8 | 01000 |

After inserting all into the MSB-first trie, query `x = 5 (00101)`:

| bit pos | bit of x | want opposite | available? | path | cur |
|---------|----------|---------------|------------|------|-----|
| 4 | 0 | 1 | yes (25 has bit-4 = 1) | take 1 | 16 |
| 3 | 0 | 1 | no — only 25 down this path; bit-3 of 25 is 1 | take 1 | 16+8=24 |
| 2 | 1 | 0 | yes (25 has bit-2 = 0) | take 0 | 24+4=28 |
| 1 | 0 | 1 | no (25 has bit-1 = 0) | take 0 | 28 |
| 0 | 1 | 0 | no (25 has bit-0 = 1) | take 1 | 28 |

`5 ^ 25 = 0b00101 ^ 0b11001 = 0b11100 = 28`. ✓

Iterating over all `x`, the maximum found is 28 — the answer.

#### Alternative: hash-set rebuild per bit (Krishan's trick)

A space-trade: you can solve LC 421 without an explicit trie by building the answer bit-by-bit from the top, maintaining a set of prefixes. The trie form is more general (extends to "max XOR with elements satisfying constraint Z" — LC 1707) and easier to remember.

#### Complexity

- **Time:** O(n · BITS). Trie build and query each pass over n numbers and BITS bits.
- **Space:** O(n · BITS) for the trie (each insertion walks BITS levels).

---

## 🐛 Common bugs

1. **Forgetting that XOR doesn't help if values appear ≥ 3 times.** XOR is mod-2 per bit. For Single Number II (LC 137), naive XOR gives a useless answer. You need per-bit mod-3 counting.
2. **Mistaking `n & -n` for the highest set bit.** It isolates the **lowest** set bit. For the highest, use `1 << (n.bit_length() - 1)` or `n & ~(n - 1)` is also lowest. There's no equally clean one-liner for the highest bit in pure bit-twiddling.
3. **Sign-extension in Python (LC 137, LC 371).** Python ints are arbitrary precision. When the problem expects a 32-bit signed result, mask with `0xFFFFFFFF` and manually wrap negatives with `if result >= 0x80000000: result -= 1 << 32`.
4. **`n & (n-1)` on negative `n`.** Use unsigned-mask first or be careful — Python handles this fine, but C/Java need explicit `unsigned` casts.
5. **Confusing XOR with addition.** XOR is "addition without carry." For *true* addition (LC 371), you need `(a ^ b) + ((a & b) << 1)`, repeated.
6. **Including the missing index in Missing Number sum-formula.** Two formulations: XOR-and-index (here) and `n*(n+1)/2 - sum(nums)` (Gauss). The Gauss form **overflows** in fixed-width languages for large `n`. The XOR form doesn't.
7. **Trie max-XOR forgetting to take the same-bit branch when the opposite is unavailable.** A naive greedy that only takes opposite-bit branches walks off the trie. You must fall back to the same-bit branch — the XOR for that bit is then 0 and `cur` doesn't get a `1 << i`.
8. **Treating `n & (n-1) == 0` as power-of-two without the `n > 0` check.** `0 & -1 = 0` in two's complement, so 0 would falsely report as a power of two. Always require `n > 0`.

---

## 🗣️ Interviewer phrasings to recognize

- "Every element appears **twice** except one." → LC 136, XOR everything.
- "Two elements appear once, rest twice." → LC 260, XOR + split by lowest set bit.
- "Every element appears **three times** except one." → LC 137, per-bit mod-3.
- "Find the **missing** / extra / duplicate (range known)." → LC 268, XOR with indices.
- "**Maximum XOR** of any two." → LC 421, bitwise trie.
- "Add two numbers **without `+`**." → LC 371, XOR + carry-shift.
- "Count set bits / population count." → LC 191, `n & (n-1)` loop.
- "Is `n` a **power of two**?" → LC 231, `n > 0 and (n & (n-1)) == 0`.
- "**Bitwise AND of [m..n]**." → LC 201, find common prefix by right-shifting until equal.

---

## 🧭 Connections to other patterns

- **Cyclic Sort** ([05-cyclic-sort.md](05-cyclic-sort.md)) — both attack "find missing/duplicate in [0..n]" problems with O(1) space; cyclic sort places values, XOR collapses them.
- **Modified Binary Search** ([11-modified-binary-search.md](11-modified-binary-search.md)) — Bitwise AND of Numbers Range (LC 201) can be solved by finding the **common bit prefix** via parallel right-shifts, a binary-search cousin.
- **Tries** — bitwise tries (LC 421) are the same data structure as word tries, indexed on bits instead of characters.
- **Prefix Sums / Prefix XOR** — XOR-of-subarray queries (LC 1310, LC 1442, LC 1738) reduce to prefix-XOR with `xor[r] ^ xor[l-1]`, structurally identical to prefix-sum tricks.
- **Hash maps** — the "naive" alternative for almost every XOR problem. Always name it as the simpler-but-O(n)-space alternative; XOR is the upgrade.

---

## ✅ Self-check — 8 questions

??? question "1. Why does XOR-everything find the lone unduplicated value?"
    XOR is commutative and associative, and `x ^ x = 0`. Reorder the stream so duplicates are adjacent — each pair cancels to 0. The lone value is XORed with all those zeros, surviving unchanged.

??? question "2. Why does `n & -n` isolate the lowest set bit?"
    In two's-complement, `-n = ~n + 1`. The +1 propagates a carry up through the trailing zeros of `n` and flips the lowest 1 bit. Above that point, every bit of `-n` is the bitwise complement of `n`. So `n & -n` keeps exactly the lowest set bit.

??? question "3. How do you find two unique numbers in a stream of duplicates (LC 260)?"
    XOR everything to get `a ^ b`. Use `xor_all & -xor_all` to find a bit where they differ. Partition the array by that bit and XOR each half — each half collapses to one of the two unique values.

??? question "4. Why doesn't XOR alone work for Single Number II (every element three times except one)?"
    XOR collapses bits mod 2. Three appearances of a value give `x ^ x ^ x = x` (not 0). So duplicates don't cancel. You need per-bit counting modulo 3 — sum each bit position, take mod 3, reassemble.

??? question "5. How does the bitwise trie find the maximum XOR pair in O(n · BITS)?"
    Insert all numbers into a binary trie MSB-first. For each `x`, walk the trie greedily preferring the opposite bit at each level — that's the bit that contributes 1 to the XOR. The MSB-first walk ensures higher bits dominate, so the greedy is optimal.

??? question "6. How do you add two integers without `+` or `-`?"
    XOR is "sum without carry." AND-then-shift-left is the carry. Loop: `a, b = a ^ b, (a & b) << 1` until carry is 0. Final `a` is the sum. Mask to 32 bits and sign-extend if working in fixed width.

??? question "7. What's the difference between `n & (n-1)` and `n & -n`?"
    `n & (n-1)` **clears** the lowest set bit (zeroes it). `n & -n` **isolates** the lowest set bit (zeroes everything else). They're complementary tools — use the first for set-bit counting / power-of-two checks, the second when you need the bit *value* itself.

??? question "8. Why is the XOR form of Missing Number safer than the Gauss-formula form?"
    Gauss's form (`n*(n+1)/2 - sum(nums)`) **overflows** for large `n` in fixed-width languages — `n*(n+1)` can exceed 32-bit int. The XOR form involves no arithmetic on large products and works for any size that fits the int type.

---

> **🎉 Pattern complete.** That closes out the 20-pattern canonical bible. Every common interview question you'll see in DS&A maps to one of these patterns — often more than one, and the "which pattern fits this?" instinct is the reflex that the bible is designed to build. From here the journey is **Advanced** (segment trees, monotonic stacks, math DPs), **Ultra-Advanced** (Mo's algorithm, suffix arrays, network flow), and **System Design**. See the [section index](index.md) for the full map.
