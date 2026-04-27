# Time complexity explained

> Big-O without the math degree. What it is, why interviewers care, and how to figure out yours in 30 seconds.

---

## What time complexity is — the everyday version

You're cooking dinner for 1 person. Takes 30 minutes.
You're cooking for 2 people. Maybe 35 minutes.
For 4 people? Maybe 50 minutes.
For 100 people? You're ordering catering.

Time complexity is the same idea: **how does the time grow as the input grows?**

In computer science, we use **Big-O notation** to describe this growth. `O(n)` means "time grows linearly with input size." `O(n²)` means "time grows with the square of input size." That's it. Big-O is a label for a *growth pattern*.

---

## Why interviewers care

Two solutions can both produce the right answer. One runs in 10 ms, the other in 10 minutes. For interview-sized inputs, that gap means *failed* vs *passed*. **Picking a solution with the right complexity is half the interview**.

Interviewers will ask: "What's the time complexity?" If you say "I don't know," it's a red flag. If you say "O(n²) because of the nested loop, but I think we can do better," you've already won.

---

## The growth zoo (memorize this list)

These are the time complexities you'll see in interviews, from fastest to slowest:

| Big-O | Name | Example | What it means for n=10⁶ |
|---|---|---|---|
| **O(1)** | Constant | Look up a dict key | Instant |
| **O(log n)** | Logarithmic | Binary search | ~20 operations |
| **O(n)** | Linear | One loop through array | ~1M operations (fast) |
| **O(n log n)** | Linearithmic | Efficient sort (merge, heap, Timsort) | ~20M operations (still fast) |
| **O(n²)** | Quadratic | Two nested loops | ~10¹² ops (10K seconds — too slow!) |
| **O(n³)** | Cubic | Three nested loops | Forget it |
| **O(2ⁿ)** | Exponential | Naive recursion (Fibonacci, subset enum) | Forget it past n=30 |
| **O(n!)** | Factorial | Generate all permutations | Forget it past n=10 |

### The practical interpretation

- **O(1) and O(log n)** — these are great. You're done.
- **O(n)** — usually the goal. "Single pass."
- **O(n log n)** — the natural complexity for "needs sort first" problems.
- **O(n²)** — usually the brute force. Sometimes acceptable, often not.
- **O(2ⁿ)** — only acceptable for tiny n (≤20). Common with backtracking on small inputs.

---

## How to figure out a function's complexity

Three rules cover ~95% of cases.

### Rule 1 — Count nested loops

A loop over `n` items is O(n). Two nested loops over `n` items is O(n²). Three is O(n³).

```python
# O(n)
for x in arr:
    print(x)

# O(n²)
for i in range(n):
    for j in range(n):
        print(i, j)

# O(n × m) — when sizes are different, name them differently
for x in arr:        # n items
    for y in other:  # m items
        print(x, y)
```

### Rule 2 — Sequential blocks add (and we keep the dominant one)

```python
def f(arr):
    for x in arr:           # O(n)
        print(x)
    for x in arr:           # O(n)
        print(x * 2)
```

Total: O(n) + O(n) = O(2n). Big-O drops constants → **O(n)**.

```python
def g(arr):
    arr.sort()              # O(n log n)
    for x in arr:           # O(n)
        print(x)
```

Total: O(n log n) + O(n). Big-O keeps only the dominant term → **O(n log n)**.

### Rule 3 — Halving means logarithmic

If each step **halves** the work, the total work is `log₂(n)`.

```python
def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:                     # how many iterations?
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1                # halve right
        else:
            hi = mid - 1                # halve left
    return -1
```

Each iteration cuts the range in half. Starts at `n`, goes to `n/2`, then `n/4`, …, down to 1. That's `log₂(n)` steps. → **O(log n)**.

---

## Common operation complexities (cheat list)

These come up so often, you must know them cold.

### List operations

| Operation | Complexity | Why |
|---|---|---|
| `arr[i]` (index) | O(1) | direct memory access |
| `arr[i] = x` | O(1) | same |
| `arr.append(x)` | O(1) amortized | doubles capacity when full |
| `arr.pop()` (last) | O(1) | |
| `arr.pop(0)` (first) | **O(n)** | shifts everything |
| `arr.insert(0, x)` | **O(n)** | shifts everything |
| `x in arr` | **O(n)** | scans linearly |
| `arr.remove(x)` | **O(n)** | scan + shift |
| `len(arr)` | O(1) | length is cached |
| `arr.sort()` | O(n log n) | Timsort |
| `arr[i:j]` (slice) | O(j-i) | copies the slice |

### Dict / set operations

| Operation | Complexity |
|---|---|
| `d[k]` | O(1) average |
| `d[k] = v` | O(1) average |
| `k in d` | O(1) average |
| `del d[k]` | O(1) average |
| `len(d)` | O(1) |

(Worst case is O(n) on hash collisions, but interviewers always accept O(1).)

### String operations

| Operation | Complexity |
|---|---|
| `s[i]` | O(1) |
| `s + t` | O(\|s\| + \|t\|) |
| `s.find(sub)` | O(\|s\| × \|sub\|) worst case |
| `sub in s` | O(\|s\| × \|sub\|) worst case |
| `s.split(sep)` | O(\|s\|) |
| `"".join(list_of_strs)` | O(total length) |

### `deque` — fast both ends

| Operation | Complexity |
|---|---|
| `d.append(x)` | O(1) |
| `d.appendleft(x)` | O(1) |
| `d.pop()` | O(1) |
| `d.popleft()` | O(1) |

This is why **BFS uses `deque`**, not `list`.

### `heapq` — priority queue

| Operation | Complexity |
|---|---|
| `heappush(h, x)` | O(log n) |
| `heappop(h)` | O(log n) |
| `heap[0]` (peek) | O(1) |
| `heapify(arr)` | O(n) — surprisingly! |

---

## Best, average, worst — usually we report worst

For interviews, the convention is **worst case**. When someone asks "what's the time complexity?", they mean worst case unless specified.

For some algorithms, average case is more useful (quicksort, hash maps). But name the case explicitly:

> "Quicksort is O(n log n) average, O(n²) worst case (with bad pivots). Heap sort is O(n log n) worst case but with bigger constants. We usually pick quicksort because the average dominates real-world data."

That kind of answer scores points.

---

## Amortized complexity — for `arr.append`

`arr.append(x)` is O(1) "amortized." What does that mean?

A Python list reserves extra capacity. When it fills up, it doubles. The doubling is O(n), but it happens 1 time out of every n appends. So the **average over many appends** is O(1).

You'll hear this called "amortized O(1)." For interviews, just say "O(1)" — interviewers know.

---

## Common gotchas

### Gotcha 1 — `in` on a list vs a set

```python
arr = list(range(10**6))   # 1 million items

# ❌ O(n) per lookup
for i in range(100):
    if 999999 in arr: pass    # scans 1M items, 100 times

# ✅ O(1) per lookup
arr_set = set(arr)
for i in range(100):
    if 999999 in arr_set: pass
```

This single change can be the difference between TLE (Time Limit Exceeded) and Accepted.

### Gotcha 2 — string concatenation in a loop

```python
# ❌ O(n²) — each += creates a new string
result = ""
for ch in s:
    result += ch

# ✅ O(n)
result = "".join(ch for ch in s)
```

### Gotcha 3 — `arr.pop(0)`

```python
# ❌ O(n) per pop — shifts everything left
queue = [1, 2, 3]
while queue:
    front = queue.pop(0)

# ✅ O(1) per pop
from collections import deque
queue = deque([1, 2, 3])
while queue:
    front = queue.popleft()
```

### Gotcha 4 — Recursive Fibonacci

```python
# ❌ O(2ⁿ) — recomputes the same values
def fib(n):
    if n < 2: return n
    return fib(n-1) + fib(n-2)

# ✅ O(n) — memoize
from functools import cache
@cache
def fib(n):
    if n < 2: return n
    return fib(n-1) + fib(n-2)
```

`fib(40)` takes minutes the first way, milliseconds the second.

---

## Practical complexity targets by input size

When the problem says "n can be up to 10⁵", it's hinting at the expected complexity. Use this table:

| Input size | Acceptable complexity | Don't even try |
|---|---|---|
| n ≤ 10 | O(n!) | — |
| n ≤ 20 | O(2ⁿ) | O(n!) |
| n ≤ 500 | O(n³) | O(2ⁿ) |
| n ≤ 5,000 | O(n²) | O(n³) |
| n ≤ 10⁶ | O(n log n) or O(n) | O(n²) |
| n ≤ 10⁸ | O(log n) or O(n) | O(n log n) usually too slow |
| n ≤ 10¹⁸ | O(log n) | O(n) |

If `n=10⁵` is given and you're proposing O(n²), you're probably missing a faster solution. Look for sliding window, two pointers, or hash map.

---

## How to communicate complexity in an interview

Don't just say "O(n)" and move on. Show your work:

> "The outer loop runs n times. Inside, the dict lookup is O(1) average. So the total is O(n) time. For space, the dict can hold up to n keys, so O(n) space. The constants are small — one hash op per element, no extra passes — so this should be efficient even for n=10⁶."

That's a complete, score-worthy complexity analysis.

---

## Self-check

Without peeking, what's the complexity of:

1. Searching a sorted array of n items with binary search?
2. Iterating a list and calling `if x in other_list:` for each x?
3. Sorting an array of n items?
4. Looking up a key in a hash map?
5. Heap-pushing n items, then popping all?
6. `for i in range(n): for j in range(n): for k in range(n): ...`?
7. The Fibonacci function `fib(n) = fib(n-1) + fib(n-2)` without memoization?

(Answers: 1. O(log n) 2. O(n × m) 3. O(n log n) 4. O(1) avg 5. O(n log n) 6. O(n³) 7. O(2ⁿ).)

---

## Up next

→ [Space complexity explained](space-complexity-explained.md) — what "in-place" actually means.
