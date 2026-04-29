# Bit Manipulation

> Think in bits, code in tricks — the cheat-codes layer of algorithms.

<span class="phase-status phase-done">Phase 4 — Algorithms</span>

---

## Why Bit Manipulation

Bit tricks compress logic that would otherwise need branches, sets, or hashmaps:
counting bits, encoding subsets, detecting parity, simulating flags. Interviewers
love them because the right one-liner replaces ten lines of conditional code —
and they reveal whether you understand binary at the metal.

!!! tip "Reading the room"
    See "subset" + "n ≤ 20"? Think **bitmask DP**. See "appears once among pairs"?
    Think **XOR**. See "power of two"? Think `n & (n - 1) == 0`.

---

## Basic Operations

| Op | Symbol | Meaning |
|---|---|---|
| AND | `&` | both bits set |
| OR | `\|` | either bit set |
| XOR | `^` | bits differ |
| NOT | `~` | flip all bits (Python: arbitrary precision, returns `-x - 1`) |
| Left shift | `<<` | multiply by $2^k$ |
| Right shift | `>>` | floor-divide by $2^k$ (arithmetic on signed) |

```python
a, b = 0b1100, 0b1010
a & b   # 0b1000
a | b   # 0b1110
a ^ b   # 0b0110
~a      # -13   (two's complement, infinite-width in Python)
a << 2  # 0b110000  (= 48)
a >> 1  # 0b110     (= 6)
```

---

## The Bit Tricks Table

| Goal | Formula |
|---|---|
| Set $i$-th bit | `x \| (1 << i)` |
| Clear $i$-th bit | `x & ~(1 << i)` |
| Toggle $i$-th bit | `x ^ (1 << i)` |
| Test $i$-th bit | `(x >> i) & 1` |
| Lowest set bit (mask) | `x & -x` |
| Strip lowest set bit | `x & (x - 1)` |
| Check power of 2 | `x > 0 and x & (x - 1) == 0` |
| Hamming weight (Kernighan) | repeatedly `x &= x - 1` |
| Swap without temp | `a ^= b; b ^= a; a ^= b` |
| Floor log2 | `x.bit_length() - 1` |

??? note "Why `x & -x` works"
    In two's complement, `-x` flips every bit and adds 1. The lowest set bit is the
    only place both `x` and `-x` share a 1. Everything to its left differs;
    everything to its right is 0 in both. The AND isolates that single bit.

### Brian Kernighan's bit count

```python
def popcount(x: int) -> int:
    count = 0
    while x:
        x &= x - 1   # strips the lowest set bit
        count += 1
    return count
```

Runs in $O(\text{number of set bits})$, not $O(\text{width})$.

??? question "Python 3.10+ shortcut?"
    Yes — `int.bit_count()` is implemented in C and beats any hand-rolled loop:
    ```python
    (0b10110101).bit_count()  # 5
    ```

---

## XOR Properties

XOR is the Swiss Army knife of bit problems:

- $a \oplus a = 0$
- $a \oplus 0 = a$
- Commutative + associative — order doesn't matter
- $a \oplus b \oplus a = b$ — pairs cancel

These four facts unlock a family of problems.

### Single number among pairs (LC 136)

Every element appears twice except one. XOR everything; pairs cancel, the loner survives.

```python
def singleNumber(nums: list[int]) -> int:
    result = 0
    for n in nums:
        result ^= n
    return result
```

$O(n)$ time, $O(1)$ extra space.

### Two non-repeating numbers (LC 260)

XOR everything → get $a \oplus b$. Pick any set bit (use `x & -x`) — that bit
differs between `a` and `b`. Partition by that bit and XOR each group.

```python
def singleNumberIII(nums: list[int]) -> list[int]:
    xor_all = 0
    for n in nums:
        xor_all ^= n
    diff_bit = xor_all & -xor_all
    a = b = 0
    for n in nums:
        if n & diff_bit:
            a ^= n
        else:
            b ^= n
    return [a, b]
```

### Missing number (LC 268)

Numbers $0..n$ with one missing. XOR all values **and** all indices `0..n`; the survivor is the missing one.

```python
def missingNumber(nums: list[int]) -> int:
    result = len(nums)
    for i, n in enumerate(nums):
        result ^= i ^ n
    return result
```

### Find the duplicate (XOR variant)

When the array contains $1..n$ with one duplicate, XOR all values + `1..n`
isolates the duplicate (only works if duplicate appears exactly twice extra; otherwise use Floyd's cycle).

---

## Bitmasks for Subsets

### Iterate all subsets of `{0..n-1}`

Each subset is a number in `[0, 2^n)`; bit `i` set ⇔ element `i` is in the subset.

```python
def all_subsets(elements: list[int]) -> list[list[int]]:
    n = len(elements)
    subsets: list[list[int]] = []
    for mask in range(1 << n):
        subset = [elements[i] for i in range(n) if mask & (1 << i)]
        subsets.append(subset)
    return subsets
```

### Iterate subsets **of** a given mask

Classic trick used in subset-sum-style DP: enumerate every submask of `mask`.

```python
def submasks(mask: int) -> list[int]:
    result = []
    sub = mask
    while sub > 0:
        result.append(sub)
        sub = (sub - 1) & mask
    result.append(0)  # empty subset
    return result
```

Total work over **all** masks of an $n$-bit universe is $O(3^n)$, not $4^n$.

---

## Bitmask DP

When state space is "subset of up to ~20 items", encode the subset in an int.

### Travelling Salesman (held–karp sketch)

`dp[mask][i]` = shortest path that visits exactly the cities in `mask` and ends at `i`.

```python
def tsp(dist: list[list[int]]) -> int:
    n = len(dist)
    INF = float('inf')
    dp = [[INF] * n for _ in range(1 << n)]
    dp[1][0] = 0  # start at city 0
    for mask in range(1, 1 << n):
        if not mask & 1:
            continue
        for i in range(n):
            if not mask & (1 << i):
                continue
            for j in range(n):
                if mask & (1 << j) or i == j:
                    continue
                new_mask = mask | (1 << j)
                dp[new_mask][j] = min(dp[new_mask][j], dp[mask][i] + dp[i][j])
    full = (1 << n) - 1
    return min(dp[full][i] + dist[i][0] for i in range(1, n))
```

$O(n^2 \cdot 2^n)$ — feasible up to $n \approx 20$.

### Subset with target sum

```python
def subset_sum_bitmask(nums: list[int], target: int) -> bool:
    n = len(nums)
    for mask in range(1 << n):
        if sum(nums[i] for i in range(n) if mask & (1 << i)) == target:
            return True
    return False
```

Pure brute-force at $O(n \cdot 2^n)$ — replace with meet-in-the-middle for $n > 30$.

---

## Python-Specific Notes

??? note "Arbitrary-precision ints"
    Python ints have no fixed width. Left-shifting just grows them. There is no
    `unsigned` and no overflow — convenient, but watch out:
    - `~x` returns `-x - 1`, not a 32-bit complement.
    - To simulate fixed-width unsigned 32-bit: mask with `& 0xFFFFFFFF`.

```python
def add_32bit(a: int, b: int) -> int:
    MASK = 0xFFFFFFFF
    while b:
        carry = (a & b) << 1 & MASK
        a = (a ^ b) & MASK
        b = carry
    # convert back to signed 32-bit
    return a if a < 0x80000000 else a - 0x100000000
```

??? note "Useful built-ins"
    | Function | Purpose |
    |---|---|
    | `bin(x)` | binary string with `0b` prefix |
    | `int(s, 2)` | parse binary string |
    | `x.bit_length()` | bits needed (= floor log2 + 1) |
    | `x.bit_count()` | popcount, Python 3.10+ |
    | `x.to_bytes(n, 'big')` | bytes for big-int hashing |

---

## Interview Problems

### Problem 1 — Number of 1 Bits (LC 191)

```python
def hammingWeight(n: int) -> int:
    count = 0
    while n:
        n &= n - 1
        count += 1
    return count
```

Or the one-liner: `return n.bit_count()`.

### Problem 2 — Counting Bits (LC 338)

For `i = 0..n`, return the popcount of each. DP: `bits[i] = bits[i >> 1] + (i & 1)`.

```python
def countBits(n: int) -> list[int]:
    bits = [0] * (n + 1)
    for i in range(1, n + 1):
        bits[i] = bits[i >> 1] + (i & 1)
    return bits
```

$O(n)$ — strictly better than calling popcount per number.

### Problem 3 — Single Number II (LC 137)

Every number appears three times except one — return that one. Track bits using
two accumulators: `ones` holds bits seen once, `twos` holds bits seen twice.

```python
def singleNumberII(nums: list[int]) -> int:
    ones = twos = 0
    for n in nums:
        ones = (ones ^ n) & ~twos
        twos = (twos ^ n) & ~ones
    return ones
```

??? question "How does this work?"
    Think bit-by-bit. For each bit, we want a state machine over counts mod 3.
    The pair `(twos, ones)` encodes 0/1/2 occurrences:
    - `00 → 01` on a 1
    - `01 → 10` on a 1
    - `10 → 00` on a 1
    The two assignments above implement exactly that transition in parallel
    across all 32 bits. After processing, `ones` carries the bits that appeared
    once mod 3 — the unique element.

---

## 🃏 Cheatsheet

| Pattern | Trick |
|---|---|
| Lowest set bit | `x & -x` |
| Strip lowest | `x & (x - 1)` |
| Power of 2 | `x > 0 and x & (x - 1) == 0` |
| Popcount fast | `x.bit_count()` (3.10+) or Kernighan |
| Find loner among pairs | XOR all |
| All subsets | `for mask in range(1 << n)` |
| Submasks of mask | `sub = (sub - 1) & mask` |
| 32-bit unsigned sim | `& 0xFFFFFFFF` |
| Linear recurrence in subsets | bitmask DP, $n \le 20$ |
| Floor log2 | `x.bit_length() - 1` |

!!! warning "Don't outsmart the compiler"
    `a ^= b; b ^= a; a ^= b` is a classic interview answer, but in Python tuple
    swap `a, b = b, a` is faster *and* clearer. Use the XOR swap only when asked
    to avoid extra storage.
