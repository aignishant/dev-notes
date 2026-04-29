# Math — common across all companies

> Number theory, fast exponentiation, and base conversions — small problems with sharp edge cases.

<span class="company-tag">Google</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">TCS</span> &nbsp; <span class="company-tag">ISRO</span> &nbsp; <span class="phase-status phase-done">Phase 14 — Common Across</span>

---

Math problems are deceptively simple — the LeetCode difficulty often says **Easy**, yet they break candidates because of overflow, sign handling, base conversions, and "implement without `*` / `/` / `%`" constraints. ISRO and TCS interviews lean heavily on these (closer to traditional CS coursework), while FAANG uses them as warm-up rounds where the bar is **getting every edge case right** in five minutes. This page collects the canonical set: fast exponentiation, primality, integer parsing, base systems, and a few bit/math hybrids. Master `pow(x, n)` and the Sieve of Eratosthenes and you can derive most others on the spot.

## Patterns at a glance

| Pattern | Frequency | Signal phrase | Core trick |
|---|---|---|---|
| Fast exponentiation | High | "x^n", "modular pow" | Halve `n`, square `x` |
| Sieve of Eratosthenes | High | "count primes ≤ n" | Mark composites from `i*i` |
| Digit DP / digit walk | Medium | "happy number", "digits sum" | Iterate via `divmod(n, 10)` |
| Base conversion | High | "Roman", "Excel column", "atoi" | Map symbols to weights |
| Bit-tricks for arithmetic | Medium | "no `*`, `/`, `%`" | Shifts + adds |
| Overflow guards | Universal | "32-bit signed range" | Compare against `2**31 - 1` |
| Cycle detection (math) | Medium | "happy number" | Floyd / seen-set |
| Trailing-zero counting | Low-med | "factorial zeros" | Count factors of 5 |

## Problem list

| # | Problem | Pattern | Difficulty | Companies |
|---|---|---|---|---|
| 1 | Pow(x, n) | Fast exponentiation | Med | Google, Meta |
| 2 | Sqrt(x) | Binary search | Easy | Amazon, TCS |
| 3 | Reverse Integer | Overflow guard | Med | Bloomberg, Apple |
| 4 | String to Integer (atoi) | Parsing + clamp | Med | Meta, Amazon |
| 5 | Add Binary | Base 2 string | Easy | Meta, Amazon |
| 6 | Plus One | Carry walk | Easy | Google |
| 7 | Excel Sheet Column Number | Base 26 | Easy | TCS, Microsoft |
| 8 | Excel Sheet Column Title | Base 26 (1-indexed!) | Easy | Microsoft, ISRO |
| 9 | Roman to Integer | Symbol weights | Easy | Amazon |
| 10 | Integer to Roman | Greedy substitution | Med | Amazon |
| 11 | Happy Number | Cycle detection | Easy | Google |
| 12 | Count Primes | Sieve of Eratosthenes | Med | Amazon, ISRO |
| 13 | GCD of Two Numbers | Euclidean | Easy | TCS, ISRO |
| 14 | Fibonacci Number | DP / matrix | Easy | Universal |
| 15 | Climbing Stairs | DP / Fibonacci | Easy | Universal |
| 16 | Number of 1 Bits | Bit + math | Easy | Universal |
| 17 | Multiply Strings | Schoolbook multiply | Med | Meta, ISRO |
| 18 | Divide Two Integers | Bit-shift division | Med | Meta, Microsoft |
| 19 | Factorial Trailing Zeros | Count factors of 5 | Med | TCS, Bloomberg |
| 20 | Ugly Number I / II | Multi-pointer | Med | Amazon |
| 21 | Super Pow | Modular fast exp | Med | Google |

??? tip "Five edge cases that always show up"
    1. `n = 0` — exponent zero, divisor zero, factorial of zero.
    2. Negative inputs — `pow(x, -3)`, negative atoi.
    3. INT_MIN / INT_MAX — `-2**31` cannot be negated in 32-bit.
    4. Empty / whitespace strings.
    5. Leading zeros and signs.

---

## Deep-dive 1 — Pow(x, n) with fast exponentiation

> Implement `pow(x, n)` in `O(log |n|)`. Handle negative `n` (return reciprocal) and `n = 0` (return 1).

Naive `result = 1; for _ in range(n): result *= x` is O(n) — too slow for `n = 2³¹ - 1`. Fast exponentiation halves the exponent each step:

- If `n` is even: `x^n = (x²)^(n/2)`.
- If `n` is odd: `x^n = x · (x²)^((n-1)/2)`.

Iterative form keeps a running `result`, multiplying it in **only when the current bit of `n` is 1** — i.e. we walk the binary expansion of `n`.

### State, invariant, base

- **Invariant:** `answer = result · x^n` is preserved across the loop.
- **Loop step:** if `n` is odd, fold one factor of `x` into `result`; then square `x` and halve `n`.
- **Base:** when `n` becomes 0, `x^n = 1`, so `answer = result`.

### Solution

```python linenums="1"
from __future__ import annotations


def my_pow(x: float, n: int) -> float:
    """Compute ``x ** n`` in O(log |n|) via iterative fast exponentiation.

    Args:
        x: The base. May be negative or fractional.
        n: The integer exponent. May be negative; ``n == 0`` returns 1.0.

    Returns:
        ``x`` raised to the power ``n`` as a float.
    """
    if n < 0:                  # (1) collapse the negative case
        x = 1 / x
        n = -n

    result = 1.0
    base = x
    while n > 0:
        if n & 1:              # (2) current binary bit is set
            result *= base
        base *= base           # (3) square for the next bit
        n >>= 1                # (4) advance to the next bit
    return result
```

1. Folding `n < 0` into `x = 1/x; n = -n` halves the code paths. In strict 32-bit languages you'd guard against `n == INT_MIN` (cannot be negated); Python's arbitrary-precision ints make this a non-issue.
2. `n & 1` is the LSB of `n`; equivalent to `n % 2 == 1` but cheaper and the idiom interviewers expect.
3. Squaring `base` corresponds to advancing the exponent's "place value" — `x, x², x⁴, x⁸, …`.
4. `n >>= 1` is integer division by 2; pairs naturally with `n & 1`.

### Complexity

| Metric | Cost |
|---|---|
| Time | `O(log |n|)` |
| Space | `O(1)` |

??? question "Why not the recursive form?"
    Recursive `pow(x, n//2)` is equally O(log n) but uses O(log n) stack and risks Python's default recursion-limit on `n ≈ 2³¹`. Iterative is safer in interviews and benchmarks faster.

??? question "Modular pow for `(x^n) mod m`?"
    Drop `result = (result * base) % m` and `base = (base * base) % m` into the loop body. This is the foundation of Super Pow, RSA, and Miller–Rabin primality.

---

## Deep-dive 2 — Count Primes via Sieve of Eratosthenes

> Return the number of primes strictly less than `n`.

Trial division per number is `O(n √n)` and times out beyond `n ≈ 10⁶`. The sieve flips the question: instead of testing each number for primality, **mark every composite** by walking through multiples of each prime. Each composite is marked O(1) amortized times, giving `O(n log log n)`.

### Algorithm

1. Create `is_prime = [True] * n`; mark `is_prime[0] = is_prime[1] = False`.
2. For each `i` from 2 up to `√n`:
   - If `is_prime[i]`, mark `is_prime[i*i], is_prime[i*i + i], …` as `False`.
3. Return `sum(is_prime)`.

The two non-obvious optimizations:

- **Outer loop only to `√n`.** Any composite `c < n` has a factor `≤ √c < √n`, so it gets marked by then.
- **Start the inner sweep at `i*i`, not `2*i`.** Smaller multiples (`2i, 3i, …, (i-1)i`) were already crossed off by smaller primes.

### Solution

```python linenums="1"
from __future__ import annotations


def count_primes(n: int) -> int:
    """Count primes strictly less than ``n`` via the Sieve of Eratosthenes.

    Args:
        n: Upper bound (exclusive). Must be non-negative.

    Returns:
        The number of primes ``p`` with ``2 <= p < n``.
    """
    if n < 2:
        return 0

    is_prime = [True] * n
    is_prime[0] = is_prime[1] = False

    i = 2
    while i * i < n:                       # (1) only up to sqrt(n)
        if is_prime[i]:
            # (2) Python slice-assign is the idiomatic fast-mark
            step = i
            start = i * i
            is_prime[start:n:step] = [False] * len(range(start, n, step))
        i += 1

    return sum(is_prime)
```

1. `i * i < n` is the integer-safe `i < sqrt(n)`. Avoids importing `math` and dodges floating-point rounding at the boundary.
2. Slice assignment (`a[start:n:step] = [...]`) runs at C speed inside CPython — significantly faster than a Python-level inner `for` loop. The `len(range(...))` matches the slice length exactly.

### Complexity

| Metric | Cost |
|---|---|
| Time | `O(n log log n)` |
| Space | `O(n)` (the boolean array) |

??? warning "Off-by-one — strictly less than `n`"
    LeetCode's spec is "primes less than `n`," so for `n = 10` the answer is **4** (`{2,3,5,7}`), not 5. If the prompt says "≤ n", iterate the array of size `n + 1`.

??? question "Memory tighter than `n` bytes?"
    Use `bytearray(n)` (1 byte per entry, ~8× less than a Python `list[bool]` due to object overhead) or a `bitarray`. For `n = 5 × 10⁶`, this is the difference between 200 MB and 5 MB.

??? tip "Linear / Euler sieve"
    A linear sieve marks each composite **exactly once** by its smallest prime factor, giving `O(n)`. The constant factor isn't always better than Eratosthenes for `n ≤ 10⁷`, but it also produces the smallest-prime-factor table — useful for repeated factorization.

---

## 🃏 Cheatsheet

| Trick | When |
|---|---|
| `n & 1` and `n >>= 1` | Walk the binary expansion of an exponent |
| `i * i < n` instead of `sqrt` | Integer-safe loop bound for sieves and primality |
| Slice-assign `a[s:e:step] = [v]*k` | Fast mark in CPython, beats inner loops |
| `divmod(n, 10)` | Walk decimal digits without string conversion |
| `0x7FFFFFFF` / `-0x80000000` | 32-bit signed clamps for atoi / reverse int |
| Greedy Roman pairs | Map `[(1000,'M'),(900,'CM'),…]` and subtract |
| Trailing zeros of `n!` | `sum(n // 5**k for k in 1..)` — count factors of 5 |
| Euclidean GCD | `gcd(a, b) = gcd(b, a % b)`, base `gcd(a, 0) = a` |
| Happy number cycle | Floyd's slow/fast pointer on digit-square sum |
| Multiply two big integers | Schoolbook into `result[i+j] += a[i]*b[j]`, then carry-propagate |
| Divide without `/` | Double the divisor (`d, d<<1, d<<2…`) until > dividend, subtract |
| Sign in atoi/divide | Strip sign first, work positive, re-apply at end |

??? tip "INT overflow shortlist (32-bit signed)"
    - `INT_MAX = 2**31 - 1 = 2_147_483_647`
    - `INT_MIN = -2**31 = -2_147_483_648`
    - `-INT_MIN` overflows by 1 — guard divide / abs / negate explicitly.
    - For atoi: clamp **before** appending the next digit (`if result > (INT_MAX - d) // 10`).

??? note "When the prompt says 'no built-ins'"
    "No `*`, `/`, `%`": use bit shifts and `+`/`-`. "No `pow`": fast exp manually. "No string→int": walk characters with `ord(c) - ord('0')`. Always confirm which built-ins are off-limits — interviewers vary.
