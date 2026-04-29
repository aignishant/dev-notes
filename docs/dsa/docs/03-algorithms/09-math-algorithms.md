# Math Algorithms

> Number theory, combinatorics, and modular arithmetic — the algebraic toolbox interviewers love.

<span class="phase-status phase-done">Phase 4 — Algorithms</span>

---

## Why Math Algorithms

Many interview problems reduce to a number-theoretic identity once you spot it:
counting paths becomes `C(n, k)`, a recurrence becomes matrix exponentiation,
and "compute under modulo $10^9 + 7$" demands modular inverse. Knowing the
recipes saves you from re-deriving them under pressure.

!!! tip "The mod-1e9+7 reflex"
    Whenever the problem says "answer can be large, return modulo $10^9 + 7$",
    expect: factorials + modular inverse, fast power, or matrix exponentiation.

---

## GCD and LCM

### Euclidean algorithm

`gcd(a, b) = gcd(b, a % b)`, terminating when `b == 0`. Runs in $O(\log \min(a, b))$.

```python
def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a

def lcm(a: int, b: int) -> int:
    return a // gcd(a, b) * b  # divide first to avoid overflow
```

Python's `math.gcd` / `math.lcm` are C-fast — use them when allowed.

### Extended Euclidean (for modular inverse)

Finds `(g, x, y)` such that `a*x + b*y = g = gcd(a, b)`.
When `gcd(a, m) == 1`, `x mod m` is the modular inverse of `a`.

```python
def ext_gcd(a: int, b: int) -> tuple[int, int, int]:
    if b == 0:
        return a, 1, 0
    g, x1, y1 = ext_gcd(b, a % b)
    return g, y1, x1 - (a // b) * y1

def mod_inverse(a: int, m: int) -> int:
    g, x, _ = ext_gcd(a % m, m)
    if g != 1:
        raise ValueError("inverse does not exist")
    return x % m
```

---

## Modular Arithmetic

??? note "Core identities"
    - $(a + b) \bmod m = ((a \bmod m) + (b \bmod m)) \bmod m$
    - $(a \cdot b) \bmod m = ((a \bmod m) \cdot (b \bmod m)) \bmod m$
    - $(a - b) \bmod m = ((a \bmod m) - (b \bmod m) + m) \bmod m$
    - **Division has no direct rule** — multiply by the modular inverse.

### Modular inverse — two recipes

| Modulus type | Method | Cost |
|---|---|---|
| `m` is prime | Fermat: $a^{-1} \equiv a^{m-2} \pmod m$ | $O(\log m)$ via fast power |
| `gcd(a, m) == 1` | Extended Euclid | $O(\log m)$ |

```python
MOD = 10**9 + 7

def inv_fermat(a: int, p: int = MOD) -> int:
    return pow(a, p - 2, p)  # Python's pow handles three args natively
```

---

## Fast Exponentiation

Compute $a^b \bmod m$ in $O(\log b)$ by squaring.

=== "Iterative"

    ```python
    def fast_pow(base: int, exp: int, mod: int) -> int:
        result = 1
        base %= mod
        while exp:
            if exp & 1:
                result = result * base % mod
            base = base * base % mod
            exp >>= 1
        return result
    ```

=== "Recursive"

    ```python
    def fast_pow_rec(base: int, exp: int, mod: int) -> int:
        if exp == 0:
            return 1
        half = fast_pow_rec(base, exp // 2, mod)
        sq = half * half % mod
        return sq * base % mod if exp & 1 else sq
    ```

=== "Pythonic"

    ```python
    pow(base, exp, mod)  # built-in, fastest
    ```

---

## Sieve of Eratosthenes

Generate all primes up to `n` in $O(n \log \log n)$.

```python
def sieve(n: int) -> list[int]:
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            for j in range(i * i, n + 1, i):  # start at i*i, smaller multiples already marked
                is_prime[j] = False
    return [i for i, p in enumerate(is_prime) if p]
```

??? note "Linear sieve (briefly)"
    The classical sieve marks composites multiple times. A *linear sieve* assigns
    each composite to its smallest prime factor and runs in strict $O(n)$ —
    overkill for typical interviews but worth name-dropping. It also gives you
    the smallest-prime-factor table for free, useful for fast factorisation.

---

## Primality Testing

### Trial division

```python
def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True
```

$O(\sqrt n)$ — fine for `n` up to $\sim 10^{12}$.

### Miller–Rabin sketch

For huge `n` use Miller–Rabin (probabilistic, but with a deterministic witness
set it is exact for `n < 3.3 \times 10^{24}`).

```python
def miller_rabin(n: int) -> bool:
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True
```

---

## Factorisation

Trial division up to $\sqrt n$ is the workhorse:

```python
def factor(n: int) -> dict[int, int]:
    factors: dict[int, int] = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors
```

??? note "Pollard's rho (briefly)"
    For factorising numbers up to $\sim 10^{18}$, Pollard's rho runs in
    expected $O(n^{1/4})$ using a cycle-finding trick on $f(x) = x^2 + c \bmod n$.
    Pair it with Miller–Rabin to recurse on factors. Rarely required in interviews
    — but good to mention if asked "what beats trial division?".

---

## Combinatorics — nCr with Mod

Precompute factorials and modular inverse factorials in $O(n)$:

```python
MOD = 10**9 + 7

def build_factorials(n: int) -> tuple[list[int], list[int]]:
    fact = [1] * (n + 1)
    for i in range(1, n + 1):
        fact[i] = fact[i - 1] * i % MOD
    inv_fact = [1] * (n + 1)
    inv_fact[n] = pow(fact[n], MOD - 2, MOD)
    for i in range(n - 1, -1, -1):
        inv_fact[i] = inv_fact[i + 1] * (i + 1) % MOD
    return fact, inv_fact

def nCr(n: int, r: int, fact: list[int], inv_fact: list[int]) -> int:
    if r < 0 or r > n:
        return 0
    return fact[n] * inv_fact[r] % MOD * inv_fact[n - r] % MOD
```

Each query is $O(1)$ after preprocessing.

---

## Catalan Numbers

$C_n = \frac{1}{n+1}\binom{2n}{n}$ — counts balanced parentheses, BSTs with `n` nodes,
monotonic lattice paths, triangulations of an $(n+2)$-gon.

```python
def catalan_dp(n: int) -> list[int]:
    cat = [0] * (n + 1)
    cat[0] = 1
    for i in range(1, n + 1):
        for j in range(i):
            cat[i] += cat[j] * cat[i - 1 - j]
    return cat

def catalan_formula(n: int, fact: list[int], inv_fact: list[int]) -> int:
    return fact[2 * n] * inv_fact[n] % MOD * inv_fact[n + 1] % MOD
```

---

## Matrix Exponentiation

Any linear recurrence becomes matrix power. For Fibonacci:

$$\begin{pmatrix} F_{n+1} \\ F_n \end{pmatrix} = \begin{pmatrix} 1 & 1 \\ 1 & 0 \end{pmatrix}^n \begin{pmatrix} F_1 \\ F_0 \end{pmatrix}$$

```python
Matrix = list[list[int]]

def mat_mul(A: Matrix, B: Matrix, mod: int) -> Matrix:
    n, m, p = len(A), len(B), len(B[0])
    C = [[0] * p for _ in range(n)]
    for i in range(n):
        for k in range(m):
            if A[i][k]:
                for j in range(p):
                    C[i][j] = (C[i][j] + A[i][k] * B[k][j]) % mod
    return C

def mat_pow(M: Matrix, e: int, mod: int) -> Matrix:
    n = len(M)
    result = [[int(i == j) for j in range(n)] for i in range(n)]  # identity
    while e:
        if e & 1:
            result = mat_mul(result, M, mod)
        M = mat_mul(M, M, mod)
        e >>= 1
    return result

def fib(n: int, mod: int = MOD) -> int:
    if n == 0:
        return 0
    M = mat_pow([[1, 1], [1, 0]], n, mod)
    return M[0][1]
```

$O(\log n)$ for the $n$-th Fibonacci.

---

## Interview Problems

### Problem 1 — Pow(x, n) (LC 50)

```python
def myPow(x: float, n: int) -> float:
    if n < 0:
        x, n = 1 / x, -n
    result = 1.0
    while n:
        if n & 1:
            result *= x
        x *= x
        n >>= 1
    return result
```

??? question "Watch out"
    Negative `n` flips base. `n` can be `-2**31`, but Python ints handle it.

### Problem 2 — Count Primes (LC 204)

```python
def countPrimes(n: int) -> int:
    if n < 2:
        return 0
    is_prime = [True] * n
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            for j in range(i * i, n, i):
                is_prime[j] = False
    return sum(is_prime)
```

### Problem 3 — Unique Paths (LC 62)

Combinatorial form: choose which of the $m+n-2$ steps go right.

```python
from math import comb

def uniquePaths(m: int, n: int) -> int:
    return comb(m + n - 2, m - 1)
```

DP version is $O(mn)$; this is $O(\min(m, n))$.

---

## 🃏 Cheatsheet

| Tool | Use when | Complexity |
|---|---|---|
| `gcd(a, b)` | reduce fractions, LCM | $O(\log \min)$ |
| Extended Euclid | modular inverse, any modulus | $O(\log m)$ |
| Fermat's little | modular inverse, prime mod | $O(\log m)$ |
| `pow(a, b, m)` | fast exp | $O(\log b)$ |
| Sieve | all primes up to $n$ | $O(n \log \log n)$ |
| Trial division | factor $n \le 10^{12}$ | $O(\sqrt n)$ |
| Miller–Rabin | primality, big $n$ | $O(k \log^3 n)$ |
| Pollard's rho | factor big $n$ | $O(n^{1/4})$ |
| Factorial + inv-fact | $\binom{n}{r} \bmod p$ | $O(n)$ pre, $O(1)$ query |
| Matrix power | linear recurrence | $O(k^3 \log n)$ |

!!! tip "Interview reflex"
    Mod $10^9 + 7$ is prime — always reach for Fermat first.
