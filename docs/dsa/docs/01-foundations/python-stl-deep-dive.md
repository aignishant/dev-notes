# Python STL deep-dive

> The complete tour of `collections`, `itertools`, `functools`, `operator`. The four modules that make Python feel like a functional language for DSA.

[Python tricks](python-tricks-for-interviews.md) covered the most common idioms. This page goes deeper — every utility you'll ever want in interviews, organized by module.

---

## `collections` — beyond Counter and defaultdict

### `deque` — double-ended queue

```python
from collections import deque

q = deque([1, 2, 3])
q.append(4)             # right append    — O(1)
q.appendleft(0)         # left append     — O(1)
q.pop()                 # right pop       — O(1)
q.popleft()             # left pop        — O(1)
q.extend([5, 6])        # extend right
q.extendleft([0, -1])   # extend left (reversed: result is [-1, 0, ..., 5, 6])
q.rotate(2)             # rotate right by 2 (last 2 → front)
q.rotate(-1)            # rotate left by 1
```

**Use cases:**
- **BFS queue** — `deque.append` + `deque.popleft`
- **Sliding window with indices** — `deque.append` + `deque.popleft` + access by index
- **Recently-used buffer** with `maxlen`:

```python
recent = deque(maxlen=5)   # auto-evicts oldest when full
```

`deque(maxlen=K)` is a **fixed-size circular buffer** in 1 line. Useful for "last K events."

---

### `OrderedDict` — preserves insertion order

In Python 3.7+, regular `dict` already preserves insertion order. `OrderedDict` is rarely needed now, **except** for two things:

1. **`move_to_end(key)`** — reorder a key to the end
2. **`popitem(last=False)`** — pop oldest

This makes `OrderedDict` perfect for **LRU cache** implementation:

```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.cache = OrderedDict()

    def get(self, key):
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.cap:
            self.cache.popitem(last=False)   # evict oldest
```

LRU cache is a top-20 LeetCode problem. With `OrderedDict`, it's 15 lines.

---

### `namedtuple` — readable tuples

```python
from collections import namedtuple

Point = namedtuple("Point", ["x", "y"])
p = Point(3, 5)

p.x        # 3 — by name
p[0]       # 3 — by index
p.y        # 5
```

Use when you have a small "record" — coordinates, edges, intervals — and you want clarity over speed.

```python
Edge = namedtuple("Edge", ["src", "dst", "weight"])
graph = [Edge(0, 1, 5), Edge(1, 2, 3)]
for e in graph:
    print(e.src, e.dst)         # readable
```

For larger records, prefer `dataclass`. For interviews, namedtuple is faster to write.

---

### `ChainMap` — multiple dicts as one

Rare in interviews. Lets you treat multiple dicts as a single read-only view.

```python
from collections import ChainMap

defaults = {"color": "red", "user": "guest"}
overrides = {"color": "blue"}

merged = ChainMap(overrides, defaults)
merged["color"]    # "blue" (overrides wins)
merged["user"]     # "guest" (falls through to defaults)
```

Useful in real codebases (config layering). Skip in interviews unless asked.

---

## `itertools` — looping building blocks

### `chain` — concatenate iterables

```python
from itertools import chain

a = [1, 2, 3]
b = [4, 5]
c = (6, 7)

list(chain(a, b, c))         # [1, 2, 3, 4, 5, 6, 7]
list(chain.from_iterable([[1,2],[3,4],[5]]))   # [1,2,3,4,5] — flatten one level
```

`chain.from_iterable` is the cleanest matrix-flatten in Python.

---

### `combinations` and `permutations`

```python
from itertools import combinations, permutations

list(combinations([1,2,3,4], 2))
# [(1,2), (1,3), (1,4), (2,3), (2,4), (3,4)]   — order doesn't matter

list(permutations([1,2,3], 2))
# [(1,2), (1,3), (2,1), (2,3), (3,1), (3,2)]   — order matters
```

Use when the problem says "all 2-element subsets" or "all orderings."

There's also `combinations_with_replacement([1,2,3], 2)` → `[(1,1), (1,2), (1,3), (2,2), (2,3), (3,3)]`.

---

### `product` — Cartesian product

```python
from itertools import product

list(product([1,2], [3,4]))
# [(1,3), (1,4), (2,3), (2,4)]

list(product([0,1], repeat=3))
# [(0,0,0), (0,0,1), (0,1,0), (0,1,1), (1,0,0), (1,0,1), (1,1,0), (1,1,1)]
```

`product([0,1], repeat=n)` enumerates all binary strings of length n — useful for "subset by bitmask" patterns.

---

### `accumulate` — running totals

```python
from itertools import accumulate

list(accumulate([1, 2, 3, 4]))             # [1, 3, 6, 10]
list(accumulate([1, 2, 3, 4], initial=0))  # [0, 1, 3, 6, 10] (Python 3.8+)

# With custom op
import operator
list(accumulate([1, 2, 3, 4], operator.mul))    # [1, 2, 6, 24]   — cumulative product

list(accumulate([3, 1, 4, 1, 5], max))          # [3, 3, 4, 4, 5] — running max
```

This is **prefix sums in 1 line**. The whole "build prefix sum array" pattern collapses to:

```python
prefix = [0] + list(accumulate(arr))
# prefix[i] = sum of first i elements
# range_sum(i, j) = prefix[j+1] - prefix[i]
```

---

### `groupby` — group adjacent equal items

**Important:** `groupby` only groups **consecutive** equal items. Sort first if you want full grouping.

```python
from itertools import groupby

data = "aaabbcaaa"
for key, group in groupby(data):
    print(key, list(group))
# a ['a', 'a', 'a']
# b ['b', 'b']
# c ['c']
# a ['a', 'a', 'a']

# With key function
nums = [1, 2, 4, 5, 7]
for is_even, group in groupby(nums, key=lambda x: x % 2 == 0):
    print(is_even, list(group))
# False [1]
# True [2, 4]
# False [5, 7]
```

Use for **run-length encoding** in 2 lines:

```python
def rle(s):
    return [(ch, len(list(g))) for ch, g in groupby(s)]

rle("aaabbc")    # [('a', 3), ('b', 2), ('c', 1)]
```

---

### `takewhile` and `dropwhile`

```python
from itertools import takewhile, dropwhile

list(takewhile(lambda x: x < 5, [1, 2, 3, 6, 1, 2]))   # [1, 2, 3] — stops at 6
list(dropwhile(lambda x: x < 5, [1, 2, 3, 6, 1, 2]))   # [6, 1, 2] — skips while < 5
```

Less common but elegant for "prefix that satisfies P" problems.

---

### `count`, `cycle`, `repeat` — infinite iterators

```python
from itertools import count, cycle, repeat

# count(start, step) — like range but infinite
for i in count(10, 2):
    if i > 20: break
    print(i)         # 10, 12, 14, 16, 18, 20

# cycle — loop forever
for i, color in zip(range(7), cycle(["red", "green", "blue"])):
    print(color)     # red, green, blue, red, green, blue, red

# repeat
list(repeat("hi", 3))    # ['hi', 'hi', 'hi']
```

`cycle` is great for round-robin assignment problems.

---

### `pairwise` — adjacent pairs (Python 3.10+)

```python
from itertools import pairwise

list(pairwise([1, 2, 3, 4, 5]))
# [(1, 2), (2, 3), (3, 4), (4, 5)]
```

Perfect for "consecutive differences" problems:

```python
# Are values strictly increasing?
all(a < b for a, b in pairwise(arr))
```

If you're on Python <3.10:

```python
def pairwise(it):
    return zip(it, it[1:])
```

---

## `functools` — function-level tools

### `lru_cache` and `cache` — memoization in 1 line

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n < 2: return n
    return fib(n-1) + fib(n-2)

fib(100)    # instant — memoized
```

This is **DP-style memoization** without writing a memo dict yourself.

```python
from functools import cache    # Python 3.9+

@cache    # equivalent to lru_cache(maxsize=None)
def f(x): ...
```

**Constraint:** arguments must be **hashable** (no lists, dicts, sets as args). Wrap them in tuples if needed.

```python
@cache
def grid_solve(i, j, grid):       # ❌ grid is unhashable list
    ...

@cache
def grid_solve(i, j, grid_tuple):  # ✅ pass tuple of tuples
    ...
```

---

### `reduce` — left fold

```python
from functools import reduce

reduce(lambda a, b: a + b, [1, 2, 3, 4])         # 10  (1+2 → 3+3 → 6+4 → 10)
reduce(lambda a, b: a * b, [1, 2, 3, 4])         # 24  (factorial-style)
reduce(lambda a, b: max(a, b), [3, 1, 4, 1, 5])  # 5
```

For most cases, prefer `sum`, `max`, `min`, `math.prod`. Use `reduce` for less common operations or when state needs to be threaded through.

---

### `partial` — pre-fill arguments

```python
from functools import partial

def power(base, exp):
    return base ** exp

square = partial(power, exp=2)
cube = partial(power, exp=3)

square(5)    # 25
cube(3)      # 27
```

Use for callbacks with fixed extra args.

---

### `cmp_to_key` — custom comparison sort

Sometimes a sort needs a true 3-way comparison (return negative / 0 / positive), not a key. Use `cmp_to_key`.

```python
from functools import cmp_to_key

def compare(a, b):
    # custom rule — sort by length DESC, then alphabetical ASC
    if len(a) != len(b):
        return len(b) - len(a)
    return -1 if a < b else (1 if a > b else 0)

words = ["cat", "ape", "an", "bat"]
words.sort(key=cmp_to_key(compare))
# ['ape', 'bat', 'cat', 'an']
```

Most of the time `key=` is enough. Keep `cmp_to_key` in mind for the rare problem (e.g., LeetCode "Largest Number").

---

## `operator` — function versions of operators

### Why this exists

Sometimes you want `+` or `<` as a *value* you can pass around. `operator` provides function versions.

```python
import operator

operator.add(2, 3)        # 5
operator.mul(2, 3)        # 6
operator.lt(2, 3)         # True

# Useful with reduce
from functools import reduce
reduce(operator.add, [1, 2, 3, 4])    # 10
reduce(operator.mul, [1, 2, 3, 4])    # 24
```

### `itemgetter` — pluck fields, fast and clean

```python
from operator import itemgetter

people = [("Alice", 30), ("Bob", 25), ("Carol", 35)]

# Sort by age
people.sort(key=itemgetter(1))
# [('Bob', 25), ('Alice', 30), ('Carol', 35)]

# Sort by name then age
people.sort(key=itemgetter(0, 1))

# Equivalent to lambda but slightly faster
# lambda x: x[1]   →   itemgetter(1)
```

`itemgetter` is faster than the lambda equivalent and arguably clearer.

### `attrgetter` and `methodcaller`

```python
from operator import attrgetter

# For objects: sort by .age
people.sort(key=attrgetter("age"))

# For sorting by method: sort strings by length, descending
words.sort(key=methodcaller("lower"))
```

---

## `math` — bonus mention

Not strictly STL, but always available:

```python
import math

math.gcd(12, 18)        # 6
math.lcm(4, 6)          # 12 (Python 3.9+)
math.isqrt(17)          # 4 — integer square root
math.comb(5, 2)         # 10 — binomial coefficient (Python 3.8+)
math.perm(5, 2)         # 20 — permutation
math.factorial(5)       # 120
math.log2(1024)         # 10.0
math.inf, -math.inf     # signed infinity
math.prod([1,2,3,4])    # 24 (Python 3.8+)
```

`math.gcd`, `math.comb`, and `math.inf` show up constantly in interview problems.

---

## The combined cheat sheet

| Module | Tool | Use it for |
|---|---|---|
| `collections` | `Counter` | counting, top-K, anagrams |
| | `defaultdict` | grouping, default-value dicts |
| | `deque` | BFS, fixed-size buffer, both-end ops |
| | `OrderedDict` | LRU cache |
| | `namedtuple` | readable records (Edge, Point) |
| `itertools` | `chain.from_iterable` | flatten one level |
| | `combinations / permutations` | enumerate all subsets / orderings |
| | `product` | Cartesian product, binary strings |
| | `accumulate` | prefix sum (or any running fold) |
| | `groupby` | run-length encoding |
| | `pairwise` | consecutive pairs |
| `functools` | `cache` / `lru_cache` | memoization |
| | `reduce` | left fold |
| | `cmp_to_key` | custom 3-way comparator |
| `operator` | `itemgetter` / `attrgetter` | clean sort keys |
| `math` | `gcd`, `comb`, `inf`, `isqrt` | math utilities |

---

## When NOT to use these

These tools speed you up only **if you remember them under pressure**. If you're hesitating between `Counter` and a manual dict for 90 seconds in an interview, just write the manual dict. Use what you know cold.

The rule: practice these in problems before the interview. Reach for them often enough that they're reflexive.

---

## Self-check

Can you, without peeking:

- [ ] Build a fixed-size LRU using `OrderedDict`?
- [ ] Compute prefix sums in 1 line with `accumulate`?
- [ ] Memoize a recursive function with `@cache`?
- [ ] Sort `[(a, 1), (b, 3), (c, 2)]` by 2nd element using `itemgetter`?
- [ ] Run-length encode `"aaabb"` using `groupby`?
- [ ] Generate all 2-element combinations from `[1,2,3,4]`?

If yes → you're done with Python foundations. Move to complexity.

---

## Up next

→ [Time complexity explained](time-complexity-explained.md) — Big-O without the math degree.
