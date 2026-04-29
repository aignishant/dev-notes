# Python STL Cheatsheet

> Every standard-library tool you'll reach for in an interview. Memorise the import line + the one-liner.

<span class="phase-status phase-done">Phase 14 — Resources</span>

---

## `collections`

```python
from collections import deque, Counter, defaultdict, OrderedDict, namedtuple
```

### `deque` — double-ended queue, O(1) both ends

```python
q = deque([1, 2, 3])
q.append(4)            # right
q.appendleft(0)        # left
q.pop(); q.popleft()   # both O(1)
q.rotate(2)            # rotate right by 2
deque(maxlen=5)        # bounded; auto-evicts old
```

### `Counter` — frequency counts

```python
c = Counter("hello")              # Counter({'l': 2, 'h': 1, 'e': 1, 'o': 1})
c.most_common(2)                  # [('l', 2), ('h', 1)]
c["x"]                            # 0 (default 0, not KeyError)
c1 + c2; c1 - c2                  # add/subtract counters
c1 & c2; c1 | c2                  # min/max element-wise
```

### `defaultdict` — default values for missing keys

```python
d = defaultdict(list)
d["a"].append(1)                  # no KeyError; creates []

graph = defaultdict(set)          # adjacency list
counter = defaultdict(int)        # cleaner than Counter for accumulation
```

### `OrderedDict` — insertion-ordered dict

```python
od = OrderedDict()
od.move_to_end("a")               # for LRU implementations
od.popitem(last=False)            # FIFO eviction
```

> Note: regular `dict` is insertion-ordered since Python 3.7. Use `OrderedDict` only when you need `move_to_end` or LRU-style semantics.

### `namedtuple`

```python
Point = namedtuple("Point", ["x", "y"])
p = Point(1, 2)
p.x; p[0]                         # both work
```

---

## `heapq` — min-heap

```python
import heapq

h = [3, 1, 4, 1, 5]
heapq.heapify(h)                  # O(N) in-place
heapq.heappush(h, 2)              # O(log N)
heapq.heappop(h)                  # smallest, O(log N)
heapq.nsmallest(3, h)             # O(N + K log N)
heapq.nlargest(3, h)
heapq.heappushpop(h, x)           # push then pop, O(log N) once
heapq.heapreplace(h, x)           # pop then push, O(log N) once
```

### Max-heap trick

```python
# Negate values
heapq.heappush(h, -value)
top = -heapq.heappop(h)
```

### Heap of tuples (priority + payload)

```python
heapq.heappush(h, (priority, item))
# Tie-break with a counter to avoid comparing items
heapq.heappush(h, (priority, counter, item))
```

---

## `bisect` — binary search

```python
import bisect

a = [1, 3, 5, 7, 9]
bisect.bisect_left(a, 5)          # 2  (leftmost insertion point)
bisect.bisect_right(a, 5)         # 3  (rightmost; alias bisect)
bisect.insort(a, 4)               # insert maintaining order, O(N) (shift)

# Find first index >= x
i = bisect.bisect_left(a, x)
# Find last index <= x
i = bisect.bisect_right(a, x) - 1
```

---

## `itertools`

```python
import itertools as it

list(it.permutations([1, 2, 3]))           # all orderings
list(it.permutations([1, 2, 3], 2))        # length-2
list(it.combinations([1, 2, 3], 2))        # [(1,2), (1,3), (2,3)]
list(it.combinations_with_replacement([1, 2], 2))  # [(1,1), (1,2), (2,2)]
list(it.product([1, 2], [3, 4]))           # cartesian product
list(it.accumulate([1, 2, 3, 4]))          # running sum [1,3,6,10]
list(it.accumulate([1, 2, 3, 4], max))     # running max
list(it.chain([1, 2], [3, 4]))             # concatenate iterables
list(it.groupby("aabbcc"))                 # group consecutive
list(it.zip_longest([1, 2], [3, 4, 5]))    # pad shorter with None
list(it.islice(range(100), 5, 10))         # slice on iterator
```

---

## `functools`

```python
from functools import lru_cache, cache, reduce, cmp_to_key, partial

@cache                            # since 3.9; unbounded
def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)

@lru_cache(maxsize=None)          # pre-3.9 equivalent
def fib(n): ...

reduce(lambda a, b: a + b, [1, 2, 3, 4])  # 10
reduce(lambda a, b: a + b, [1, 2, 3], 100)  # initial value

# Custom sort with comparator
sorted(items, key=cmp_to_key(lambda a, b: -1 if a < b else 1))
```

---

## Sorting

```python
sorted(arr)                                # ascending
sorted(arr, reverse=True)                  # descending
sorted(arr, key=lambda x: (x[1], -x[0]))   # multi-key
arr.sort()                                 # in-place

# Stable sort: chain by least-significant first
arr.sort(key=lambda x: x.b)
arr.sort(key=lambda x: x.a)                # primary

# Sort strings as numbers (natural sort)
sorted(["10", "2", "1"], key=int)
```

---

## String methods worth remembering

```python
s.split()                          # splits on any whitespace
s.split(",")                       # specific separator
s.rsplit(",", 1)                   # split from right, max 1 split
s.strip(); s.lstrip(); s.rstrip()
s.replace("a", "b", 1)             # max 1 replacement
s.count("ab")                      # non-overlapping count
s.find("ab"); s.rfind("ab")        # -1 if not found
s.startswith("ab"); s.endswith("ab")
s.zfill(5)                         # zero-pad to width
s.rjust(5, "0"); s.ljust(5, "_")
s.isdigit(); s.isalpha(); s.isalnum()
s.lower(); s.upper(); s.title(); s.swapcase()
"sep".join(parts)                  # ALWAYS for concatenation in loops
ord("a")                           # 97
chr(97)                            # "a"
"a" < "b"                          # lex compare on strings
```

---

## Sets

```python
a = {1, 2, 3}; b = {2, 3, 4}
a | b                              # union {1,2,3,4}
a & b                              # intersection {2,3}
a - b                              # difference {1}
a ^ b                              # symmetric diff {1,4}
a.issubset(b); a.issuperset(b)
a.add(x); a.discard(x); a.remove(x)  # discard no-error; remove KeyError

frozenset([1, 2, 3])               # hashable; can be dict key
```

---

## Dicts

```python
d = {"a": 1, "b": 2}
d.get("c", 0)                      # default if missing
d.setdefault("c", []).append(1)    # init-and-append idiom
{**d1, **d2}                       # merge (d2 wins on dup)
d1 | d2                            # 3.9+ merge
{k: v for k, v in d.items() if v > 0}  # filter

dict.fromkeys(["a", "b"], 0)       # {"a": 0, "b": 0}
```

---

## `math`

```python
import math

math.gcd(12, 18)                   # 6
math.lcm(4, 6)                     # 12 (3.9+)
math.isqrt(10)                     # 3 (integer sqrt, exact)
math.comb(5, 2)                    # 10 (binomial)
math.perm(5, 2)                    # 20
math.log(8, 2)                     # 3.0
math.inf; -math.inf; math.nan
math.floor(2.7); math.ceil(2.3)
divmod(17, 5)                      # (3, 2) — quot, rem
pow(2, 10)                         # 1024
pow(2, 10, 1000)                   # 24 (modular exponentiation)
```

---

## `string`

```python
import string

string.ascii_lowercase             # 'abcdefghijklmnopqrstuvwxyz'
string.ascii_uppercase
string.ascii_letters
string.digits                      # '0123456789'
string.punctuation                 # '!"#$%&...'
string.whitespace
```

---

## Common idioms

```python
# Reverse list in-place
arr[::-1]                          # new copy
arr.reverse()                      # in-place

# 2D grid initialisation
grid = [[0] * cols for _ in range(rows)]   # CORRECT
grid = [[0] * cols] * rows                 # WRONG: shared rows!

# Enumerate with offset
for i, x in enumerate(arr, start=1): ...

# Zip and unzip
list(zip([1, 2], [3, 4]))                  # [(1, 3), (2, 4)]
a, b = zip(*[(1, 3), (2, 4)])              # ((1, 2), (3, 4))

# Transpose
list(zip(*matrix))                          # rows ↔ columns

# Flatten one level
flat = [x for row in matrix for x in row]

# Conditional max/min in one line
max((x for x in arr if x % 2 == 0), default=-1)

# Walrus for "compute and check"
while (line := input()) != "":
    process(line)

# Type hints
from typing import Optional
def f(x: list[int], k: int | None = None) -> dict[str, int]: ...
```

---

## What NOT to use

| Don't | Use instead |
|---|---|
| `s += "x"` in loop | `parts.append("x"); "".join(parts)` |
| `if x in list:` for membership | `if x in set:` |
| `arr.pop(0)` | `deque.popleft()` |
| `[[0]*n]*m` for 2D | `[[0]*n for _ in range(m)]` |
| `range(len(arr))` | `enumerate(arr)` |
| `lambda x: x[0]` for sort key | `operator.itemgetter(0)` (faster) |
| Dict get-or-create with `if k in d` | `defaultdict` or `setdefault` |
| Manual frequency counter | `Counter` |
| `sorted(arr)[0]` | `min(arr)` |

---

## Memorise these import lines

```python
from collections import deque, Counter, defaultdict
import heapq
import bisect
import itertools as it
from functools import cache, lru_cache, reduce
import math
```

These six lines cover ~95% of interview problems.
