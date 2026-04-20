# 21 — Quantitative Aptitude & Logical Reasoning
## For Product-Based Companies (Google, Amazon, Goldman Sachs, etc.)

---

## 🎯 Where These Are Asked
```
Google:        Estimation problems ("How many golf balls fit in a school bus?")
Amazon:        LP (Leadership Principles) + math-in-code
Goldman Sachs: Heavy math/probability/puzzles
Quant Firms:   Probability, combinatorics, brain teasers
Startups:      Quick mental math, estimation, logic
```

---

## 21.1 Number Theory & Math for Coding

### Q1: Check if a number is prime — O(√n)

```python
def is_prime(n):
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

# Sieve of Eratosthenes — find all primes up to n — O(n log log n)
def sieve(n):
    is_p = [True] * (n + 1)
    is_p[0] = is_p[1] = False
    for i in range(2, int(n**0.5) + 1):
        if is_p[i]:
            for j in range(i*i, n + 1, i):
                is_p[j] = False
    return [i for i in range(n + 1) if is_p[i]]
```

### Q2: GCD, LCM, Modular Arithmetic

```python
import math

# GCD — Euclidean algorithm O(log(min(a,b)))
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a
# Or: math.gcd(a, b)

# LCM
def lcm(a, b):
    return a * b // gcd(a, b)

# Modular exponentiation — (base^exp) % mod — O(log exp)
def power_mod(base, exp, mod):
    result = 1
    base %= mod
    while exp > 0:
        if exp % 2 == 1:
            result = (result * base) % mod
        exp //= 2
        base = (base * base) % mod
    return result

# Fibonacci with matrix exponentiation — O(log n)
def fib_fast(n):
    if n <= 1:
        return n
    def mat_mult(A, B):
        return [
            [A[0][0]*B[0][0] + A[0][1]*B[1][0], A[0][0]*B[0][1] + A[0][1]*B[1][1]],
            [A[1][0]*B[0][0] + A[1][1]*B[1][0], A[1][0]*B[0][1] + A[1][1]*B[1][1]]
        ]
    def mat_pow(M, p):
        result = [[1,0],[0,1]]    # Identity
        while p:
            if p % 2:
                result = mat_mult(result, M)
            M = mat_mult(M, M)
            p //= 2
        return result
    
    M = [[1,1],[1,0]]
    return mat_pow(M, n)[0][1]
```

### Q3: Bit Manipulation Essentials

```python
# Check if power of 2
def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0

# Count set bits (Hamming weight)
def count_bits(n):
    count = 0
    while n:
        count += 1
        n &= (n - 1)    # Clear lowest set bit
    return count

# Single Number — find element appearing once (others appear twice) — O(n)
def single_number(nums):
    result = 0
    for num in nums:
        result ^= num      # XOR: a ^ a = 0, a ^ 0 = a
    return result

# Missing Number — find missing in [0, n] — O(n)
def missing_number(nums):
    n = len(nums)
    return n * (n + 1) // 2 - sum(nums)

# Reverse Bits
def reverse_bits(n):
    result = 0
    for _ in range(32):
        result = (result << 1) | (n & 1)
        n >>= 1
    return result

# Bit tricks cheat sheet:
# x & 1          → check if odd
# x >> 1         → divide by 2
# x << 1         → multiply by 2
# x & (x - 1)    → clear lowest set bit
# x & (-x)       → isolate lowest set bit
# x ^ y          → find bits that differ
```

---

## 21.2 Probability & Statistics

### Q4: Probability questions asked in interviews

```python
"""
Q: What is the probability of getting at least one 6 in 4 dice rolls?
A: P(at least one 6) = 1 - P(no 6 in 4 rolls)
   = 1 - (5/6)^4
   = 1 - 625/1296
   ≈ 0.5177 or ~52%

Q: You flip a fair coin until you get heads. Expected number of flips?
A: Geometric distribution: E[X] = 1/p = 1/0.5 = 2 flips

Q: Birthday paradox: How many people needed for 50% chance two share birthday?
A: P(all different) = 365/365 × 364/365 × 363/365 × ...
   Only 23 people needed! (counter-intuitive)

Q: Monty Hall problem: 3 doors, 1 car, 2 goats. You pick door 1. Host opens door 3 (goat). Switch?
A: YES, always switch. Switching wins 2/3 of the time.
   - Stay: 1/3 probability
   - Switch: 2/3 probability

Q: Two children problem: "I have two children. At least one is a boy. Probability both are boys?"
A: Sample space with at least one boy: {BB, BG, GB}
   P(BB) = 1/3 (NOT 1/2!)

Q: Expected value of rolling a die until you get a 6?
A: Geometric distribution: E = 1/p = 1/(1/6) = 6 rolls
"""

# Simulate to verify
import random

def simulate_at_least_one_six(trials=1_000_000):
    count = sum(
        1 for _ in range(trials)
        if any(random.randint(1, 6) == 6 for _ in range(4))
    )
    return count / trials

# print(simulate_at_least_one_six())  # ~0.518

# Reservoir Sampling — Select k items randomly from a stream of unknown size — O(n)
def reservoir_sample(stream, k):
    """Uniformly random k items from a stream of unknown size."""
    reservoir = []
    for i, item in enumerate(stream):
        if i < k:
            reservoir.append(item)
        else:
            j = random.randint(0, i)
            if j < k:
                reservoir[j] = item
    return reservoir
```

---

## 21.3 Estimation Questions (Fermi Problems)

### Q5: Google-style estimation questions

```
Framework for Fermi Estimation:
  1. Break the problem into smaller, estimable parts
  2. Make reasonable assumptions (state them!)
  3. Do order-of-magnitude math
  4. Sanity check the result

Q: "How many golf balls fit in a school bus?"
  Step 1: Volume of school bus
    - Internal: ~2.5m × 2m × 7.5m = ~37.5 m³
    - Subtract seats (~25%): ~28 m³ = 28,000,000 cm³
  Step 2: Volume of golf ball
    - Diameter ~4.3 cm → radius ~2.15 cm
    - Volume = 4/3 × π × r³ ≈ 41.6 cm³
  Step 3: Packing efficiency ~64%
    - Effective volume per ball: 41.6 / 0.64 ≈ 65 cm³
  Step 4: 28,000,000 / 65 ≈ ~430,000 golf balls
  Answer: ~400,000–500,000

Q: "How many piano tuners are in Chicago?"
  - Chicago population: ~2.7 million
  - People per household: ~2.5 → ~1.1M households
  - % with piano: ~5% → ~55,000 pianos
  - Tunings per year: ~1.5 → ~82,500 tunings/year
  - Tunings per tuner per day: ~4 → ~1,000/year
  - Tuners needed: 82,500 / 1,000 ≈ ~83 piano tuners
  Answer: ~80-100

Q: "Estimate Google's daily search revenue"
  - Daily searches: ~8.5 billion
  - Searches with ads: ~30% → ~2.5 billion
  - Click-through rate: ~3% → ~75 million clicks
  - Average CPC: ~$2
  - Daily revenue: 75M × $2 = ~$150M/day
  - Annual: ~$55B (actual Google Search revenue: ~$175B, so our
    estimate is reasonable for search-only)
```

---

## 21.4 Puzzles & Brain Teasers

### Q6: Classic puzzles asked in tech interviews

```
PUZZLE 1: Two Eggs Problem
  You have 2 eggs and a 100-floor building. Find the minimum number of
  drops to determine the highest safe floor (egg doesn't break).

  Solution: Optimal = 14 drops
  - Drop first egg from floors: 14, 27, 39, 50, 60, 69, 77, 84, 90, 95, 99, 100
  - If it breaks, use second egg to check floors one by one
  - Worst case: 14 drops (try floor 14, then 1-13 = 14 total)
  - Formula: n(n+1)/2 ≥ 100 → n = 14

PUZZLE 2: Water Jug Problem
  You have a 3-liter and a 5-liter jug. Measure exactly 4 liters.
  
  Solution:
  1. Fill 5L jug
  2. Pour into 3L jug (5L has 2L remaining)
  3. Empty 3L jug
  4. Pour 2L from 5L into 3L jug (3L has 2L)
  5. Fill 5L jug
  6. Pour from 5L into 3L jug (fills remaining 1L) → 5L jug has 4L ✓

PUZZLE 3: Burning Ropes
  Two ropes, each takes exactly 1 hour to burn completely.
  Burns non-uniformly. Measure 45 minutes.
  
  Solution:
  1. Light rope 1 from BOTH ends, rope 2 from ONE end simultaneously
  2. Rope 1 burns out in 30 minutes (half time when lit from both ends)
  3. At that moment, light rope 2's other end
  4. Rope 2 burns out in 15 more minutes (30 min worth of rope, now burning from both ends)
  5. Total: 30 + 15 = 45 minutes ✓

PUZZLE 4: 8 Identical Balls
  8 balls, one heavier. Find it in minimum weighings using a balance scale.
  
  Solution: 2 weighings
  1. Put 3 vs 3 on scale
     - If balanced: heavy ball is in remaining 2 → weigh them (1 more weighing)
     - If unbalanced: take heavier group of 3 → weigh 1 vs 1 from those
       - If balanced: third ball is heavy
       - If unbalanced: heavier side is the answer
```

---

## 21.5 Combinatorics for Coding

```python
# Combinations: C(n,k) = n! / (k! × (n-k)!)
from math import comb, factorial

print(comb(10, 3))     # 120 — ways to choose 3 from 10

# Permutations: P(n,k) = n! / (n-k)!
def permutations_count(n, k):
    return factorial(n) // factorial(n - k)

print(permutations_count(10, 3))  # 720

# Catalan Number — appears in many problems
# C(n) = C(2n, n) / (n+1)
# Counts: valid parentheses, BST structures, triangulations
def catalan(n):
    return comb(2*n, n) // (n + 1)

# First few: 1, 1, 2, 5, 14, 42, 132, 429, 1430

# Stars and Bars — distribute n identical items into k bins
# C(n+k-1, k-1)
# Example: Distribute 10 candies among 3 kids = C(12, 2) = 66 ways

# Pigeonhole Principle
# If n items in m containers and n > m, at least one container has > 1 item
# Example: In 367 people, at least 2 share a birthday (366 possible days)

# Inclusion-Exclusion Principle
# |A ∪ B| = |A| + |B| - |A ∩ B|
# |A ∪ B ∪ C| = |A| + |B| + |C| - |A∩B| - |A∩C| - |B∩C| + |A∩B∩C|
```

---

## 21.6 Common Math Patterns in DSA

```python
# Pattern: Prefix Sum — Range sum in O(1) after O(n) preprocessing
def range_sum_query(nums, queries):
    prefix = [0]
    for num in nums:
        prefix.append(prefix[-1] + num)
    
    results = []
    for left, right in queries:
        results.append(prefix[right + 1] - prefix[left])
    return results

# Pattern: Dutch National Flag — Sort 0s, 1s, 2s in one pass
def sort_colors(nums):
    lo, mid, hi = 0, 0, len(nums) - 1
    while mid <= hi:
        if nums[mid] == 0:
            nums[lo], nums[mid] = nums[mid], nums[lo]
            lo += 1
            mid += 1
        elif nums[mid] == 1:
            mid += 1
        else:
            nums[mid], nums[hi] = nums[hi], nums[mid]
            hi -= 1

# Pattern: Boyer-Moore Majority Vote — Find majority element O(n), O(1) space
def majority_element(nums):
    candidate = count = 0
    for num in nums:
        if count == 0:
            candidate = num
        count += 1 if num == candidate else -1
    return candidate

# Pattern: Pow(x, n) — O(log n) fast exponentiation
def my_pow(x, n):
    if n < 0:
        x = 1 / x
        n = -n
    result = 1
    while n:
        if n & 1:
            result *= x
        x *= x
        n >>= 1
    return result

# Pattern: Count Primes (Sieve) — already shown above

# Pattern: Integer to Roman / Roman to Integer
def int_to_roman(num):
    values = [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),
              (100,'C'),(90,'XC'),(50,'L'),(40,'XL'),
              (10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
    result = []
    for val, sym in values:
        while num >= val:
            result.append(sym)
            num -= val
    return ''.join(result)

# Pattern: Detect Squares / Rectangles in coordinate geometry
# Given n points, count number of axis-aligned rectangles
# Use hash map of x → set of y values, then for each pair of x's,
# count common y values: C(common, 2) rectangles
```

---

## 21.7 Speed Math Tips for Interviews

```
Powers of 2:
  2^10 = 1,024 ≈ 1 thousand (1 KB)
  2^20 ≈ 1 million (1 MB)
  2^30 ≈ 1 billion (1 GB)
  2^32 ≈ 4.3 billion (max unsigned 32-bit int)
  2^40 ≈ 1 trillion (1 TB)

Quick estimates:
  log₂(1,000) ≈ 10
  log₂(1,000,000) ≈ 20
  log₂(1,000,000,000) ≈ 30

  1 million seconds ≈ 11.5 days
  1 billion seconds ≈ 31.7 years

  1 byte = 8 bits
  1 int = 4 bytes (32-bit)
  1 long = 8 bytes (64-bit)

  1 million ints = 4 MB
  1 billion ints = 4 GB

ASCII: 'A'=65, 'Z'=90, 'a'=97, 'z'=122, '0'=48

Fibonacci: 1,1,2,3,5,8,13,21,34,55,89,144...
```

---
