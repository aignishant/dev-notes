# Bit manipulation — common across all companies

> XOR is your friend, two's-complement is the trap, and `n & (n-1)` is half the answers.

<span class="company-tag">Google</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">TCS</span> &nbsp; <span class="company-tag">ISRO</span> &nbsp; <span class="phase-status phase-done">Phase 14 — Common Across</span>

---

Bit problems are pure-tactic: a 3-line solution often hides behind a 30-line brute force, and the interviewer is watching for whether you reach for XOR, `n & (n-1)`, or a bitmask before scanning the array twice. Most of these run in `O(n)` time and `O(1)` extra memory — exactly the constraints that distinguish a B-grade answer from an A. The Single Number family alone tests every core trick: XOR self-cancellation, bit-counting modulo 3, and split-by-set-bit. This page covers the must-know set; if you can derive Single Number III and "sum without `+`" on a whiteboard, you're prepared for any bit question that shows up.

## Patterns at a glance

| Pattern | Frequency | Signal phrase | Core identity |
|---|---|---|---|
| XOR cancellation | Very high | "appears twice except…" | `x ^ x = 0`, `x ^ 0 = x` |
| `n & (n-1)` | High | "count set bits", "power of 2" | Clears the lowest set bit |
| Lowest set bit | High | "isolate rightmost 1" | `n & -n` |
| Bitmask subsets | High | n ≤ 20, "all subsets" | Iterate `mask` from 0 to `(1<<n)-1` |
| Bit-by-bit construction | Medium | "reverse bits", "sum without +" | Build 32-bit answer from LSB |
| 32-bit emulation in Python | Medium | "as if it were 32-bit signed" | `& 0xFFFFFFFF` mask |
| Trie of bits | Medium | "max XOR pair" | Greedy MSB-first walk |
| Range AND | Low | "AND of [l, r]" | Common prefix of `l` and `r` |

## Problem list

| # | Problem | Pattern | Difficulty | Companies |
|---|---|---|---|---|
| 1 | Number of 1 Bits (Hamming Weight) | `n & (n-1)` | Easy | Universal |
| 2 | Counting Bits | DP on bits | Easy | Amazon, Apple |
| 3 | Reverse Bits | Bit-by-bit | Easy | Amazon, Apple |
| 4 | Single Number I | XOR all | Easy | Universal |
| 5 | Single Number II | mod-3 bit count | Med | Google, Bloomberg |
| 6 | Single Number III | XOR + split-by-bit | Med | Google, Meta |
| 7 | Missing Number | XOR or sum | Easy | Microsoft |
| 8 | Find the Duplicate Number | Floyd / bit | Med | Amazon |
| 9 | Power of Two | `n & (n-1) == 0` | Easy | Amazon |
| 10 | Power of Three | log / loop | Easy | TCS |
| 11 | Power of Four | Bitmask `0x55555555` | Easy | Two Sigma |
| 12 | Subsets (bitmask) | Mask iteration | Med | Meta |
| 13 | Sum of Two Integers (no `+`/`-`) | XOR + carry shift | Med | Google, Meta |
| 14 | Hamming Distance | XOR + popcount | Easy | Universal |
| 15 | Total Hamming Distance | Per-bit count | Med | Meta |
| 16 | XOR Operation in Array | Direct loop | Easy | TCS |
| 17 | Decode XORed Array | Prefix XOR | Easy | Amazon |
| 18 | Bitwise AND of Numbers Range | Common prefix | Med | Google |
| 19 | Maximum XOR of Two Numbers | Bit Trie | Med | Google |

??? tip "Identities you should not have to derive"
    | Expression | Meaning |
    |---|---|
    | `x ^ x` | `0` |
    | `x ^ 0` | `x` |
    | `x & -x` | Lowest set bit (as a value) |
    | `x & (x-1)` | `x` with its lowest set bit cleared |
    | `x | (x-1)` | Sets all trailing zeros to 1 |
    | `~x + 1` | Two's-complement negation, `-x` |
    | `(x >> i) & 1` | Bit `i` of `x` |
    | `x | (1 << i)` | Set bit `i` |
    | `x & ~(1 << i)` | Clear bit `i` |
    | `x ^ (1 << i)` | Toggle bit `i` |

---

## Deep-dive 1 — Single Number III (find the two non-repeating)

> Every element appears **twice** in `nums` except for **two** numbers `a` and `b` that each appear once. Return both, in any order, in `O(n)` time and `O(1)` space.

Single Number I (one unique) is `reduce(xor, nums)`. With **two** uniques the XOR of the array gives `xor_ab = a ^ b` — non-zero (since `a ≠ b`) but it doesn't directly separate the two. The key insight: any set bit in `xor_ab` is a position where `a` and `b` **differ**. Pick any such bit, partition the array into two groups by that bit, and XOR each group separately. Each group contains exactly one of `{a, b}` (plus pairs that cancel) — so each XOR collapses to a single value.

### Steps

1. Compute `xor_ab = a ^ b` by XOR-ing every element.
2. Isolate any set bit of `xor_ab`. The conventional choice is `xor_ab & -xor_ab` — the lowest set bit — using two's-complement.
3. Walk the array a second time. Numbers with that bit set XOR into bucket `a`; numbers without it XOR into bucket `b`.
4. Return `[a, b]`.

### Solution

```python linenums="1"
from __future__ import annotations


def single_number_iii(nums: list[int]) -> list[int]:
    """Return the two elements that appear exactly once.

    All other elements appear exactly twice. Runs in O(n) time, O(1) space.

    Args:
        nums: List where two distinct values appear once, all others twice.

    Returns:
        A two-element list ``[a, b]`` (order is not specified).
    """
    xor_ab = 0
    for x in nums:
        xor_ab ^= x                     # (1) xor_ab = a ^ b at end

    # (2) Isolate the lowest set bit. ``-xor_ab`` is the two's-complement
    #     negation, and ``x & -x`` keeps only the rightmost 1.
    diff_bit = xor_ab & -xor_ab

    a = b = 0
    for x in nums:
        if x & diff_bit:                # (3) bucket by the differing bit
            a ^= x
        else:
            b ^= x
    return [a, b]
```

1. Pairs cancel via `x ^ x = 0`, leaving exactly `a ^ b`.
2. `xor_ab` is guaranteed non-zero (otherwise `a == b`), so `xor_ab & -xor_ab` is a valid single-bit mask. Python's arbitrary-precision ints make `-xor_ab` behave as `~xor_ab + 1` over enough bits — the trick still works because we only ever use the **lowest** set bit.
3. Every element with `diff_bit` set goes to bucket A; every element without it goes to bucket B. Duplicates of any value go into the same bucket together (their bit is identical), so they cancel within the bucket. `a` and `b` end up split — exactly one in each bucket.

### Complexity

| Metric | Cost |
|---|---|
| Time | `O(n)` (two passes) |
| Space | `O(1)` |

??? question "Why specifically the lowest set bit, and not the highest?"
    Any set bit of `xor_ab` works. The lowest is just the cheapest to extract — `x & -x` is one instruction. Using the highest would require finding `bit_length() - 1`, which is also fine but slightly more code.

??? warning "Don't store anything per-element"
    A hash map / `Counter` solves this in O(n) but uses O(n) space — that fails the spirit of the problem. The interviewer is specifically asking for the bit trick.

---

## Deep-dive 2 — Sum of Two Integers without `+` or `-`

> Compute `a + b` using only bitwise operators. Account for negative integers under 32-bit signed semantics.

In binary addition, **XOR is sum without carry** and **AND followed by left-shift is the carry**:

- `a ^ b` produces every column where exactly one of `a`, `b` has a `1` — the "no-carry sum."
- `(a & b) << 1` produces every column that needed to carry into the next position.

Add those two and you have the true sum — but "add" recursively means `getSum(a ^ b, (a & b) << 1)`. Loop until the carry is 0; then `a` is the answer.

### The Python gotcha — 32-bit emulation

Python `int` is unbounded. When the interim sum overflows what would be 32 bits in C / Java, Python simply uses more bits — the carry never reaches zero and the loop never terminates. To emulate 32-bit signed arithmetic:

1. Mask both `a` and `b` to 32 bits each iteration: `a & 0xFFFFFFFF`.
2. After the loop, if `a > 0x7FFFFFFF` (the maximum positive 32-bit int), the "real" value is negative — convert via `a - 0x100000000` (i.e. `a - (1 << 32)`).

### Solution

```python linenums="1"
from __future__ import annotations


def get_sum(a: int, b: int) -> int:
    """Compute ``a + b`` using only bitwise operators (32-bit signed).

    Args:
        a: First addend, treated as a 32-bit signed integer.
        b: Second addend, treated as a 32-bit signed integer.

    Returns:
        The 32-bit signed sum.
    """
    MASK = 0xFFFFFFFF              # (1) low 32 bits
    INT_MAX = 0x7FFFFFFF           # (2) max positive 32-bit signed

    while b != 0:
        # (3) sum without carry, kept inside 32 bits
        sum_no_carry = (a ^ b) & MASK
        # (4) carry, shifted left by one and clipped to 32 bits
        carry = ((a & b) << 1) & MASK
        a, b = sum_no_carry, carry

    # (5) If the top bit is set, ``a`` represents a negative number under
    #     two's-complement 32-bit semantics — convert to a Python negative.
    return a if a <= INT_MAX else a - 0x100000000
```

1. `0xFFFFFFFF` is `2**32 - 1` — keeps only the low 32 bits and stops Python from "growing" the int forever.
2. `0x7FFFFFFF` is `2**31 - 1`, the maximum positive 32-bit signed value. Anything above it is a wrapped negative.
3. XOR is addition mod 2 per bit — a binary half-adder ignoring carry.
4. AND identifies positions where both bits are 1 (the carry source); the `<< 1` shifts the carry into the next column. Clip to 32 bits so the loop terminates.
5. Final sign correction. `a - 2**32` flips the most-significant-bit's interpretation from `+2³¹` to `-2³¹`, restoring the signed value.

### Walkthrough — `get_sum(3, 5)`

| Iter | `a` (bin) | `b` (bin) | `a ^ b` | `(a & b) << 1` |
|---|---|---|---|---|
| 0 | `011` | `101` | `110` | `010` |
| 1 | `110` | `010` | `100` | `100` |
| 2 | `100` | `100` | `000` | `1000` |
| 3 | `000` | `1000` | `1000` | `0` |
| 4 | `1000` (= 8) | `0` | — | — |

Loop exits, `a = 8`. Correct.

### Complexity

| Metric | Cost |
|---|---|
| Time | `O(1)` — at most 32 carry-propagations under 32-bit semantics |
| Space | `O(1)` |

??? warning "Forgetting the mask is the #1 bug"
    Without `& MASK`, `get_sum(-1, 1)` runs forever in Python: `-1` is treated as an infinite stream of `1` bits, so `(a & b) << 1` keeps producing more carry. The mask anchors the computation to a finite bit-width.

??? question "Subtraction with the same primitive?"
    `a - b == get_sum(a, get_sum(~b, 1))`. `~b + 1` is the two's-complement negation, and we already have `+` via `get_sum`.

---

## 🃏 Cheatsheet

| Trick | When |
|---|---|
| `x ^ x = 0`, `x ^ 0 = x` | Pair-cancel duplicates in O(n) / O(1) |
| `x & -x` | Isolate the lowest set bit |
| `x & (x - 1)` | Clear the lowest set bit — popcount and power-of-two check |
| `n & (n - 1) == 0` | `n` is a power of two (and `n > 0`) |
| `0x55555555` | Mask of "every odd-indexed bit" — power-of-four test |
| `(a ^ b)` and `(a & b) << 1` | Sum-without-carry and carry, the half-adder pair |
| `& 0xFFFFFFFF` | 32-bit clamp in Python — required for sum-without-`+` |
| `bin(x).count('1')` | Pythonic popcount; `int.bit_count()` in 3.10+ |
| `for sub in range(1 << n)` | Enumerate every subset of an `n`-element set |
| `(mask >> i) & 1` | Test whether element `i` is in the subset `mask` |
| Prefix XOR | "XOR over range [l, r] = pre[r+1] ^ pre[l]" |
| Bit Trie | Greedy max-XOR pair; insert MSB-first, then walk preferring opposite bit |

??? tip "Five-second sanity checks"
    - `1 << 31` is `2_147_483_648` — already outside 32-bit signed positive range; don't store as "INT_MAX" without subtracting 1.
    - `~0` in Python is `-1`, an infinite-width int. Mask if you need a finite width.
    - `-x == ~x + 1` only under two's complement — Python honors it logically, but mind the bit-width when converting back.
    - `int.bit_length()` returns the position of the highest set bit (1-indexed); `0.bit_length() == 0`.
    - Right shift on negative Python ints arithmetically extends the sign — for logical shift, mask first.

??? note "When the bit trick is overkill"
    For `Single Number I/II/III`, the bit tricks meet the O(1)-space bar — interviewers expect them. For "find duplicate," Floyd's cycle detection on the value graph is cleaner than the bit-bucket approach. Read the constraint sheet: if O(n) extra space is allowed, a `Counter` is faster to write and harder to get wrong.
