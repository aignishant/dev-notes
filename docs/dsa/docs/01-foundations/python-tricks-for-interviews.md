# Python tricks for interviews

> Four objects that turn 15-line solutions into 5-line solutions. Counter, defaultdict, heapq, bisect.

These four come from Python's standard library. Knowing them is the difference between "I solved it" and "I solved it elegantly." Interviewers notice.

---

## 1. `Counter` — count anything in one line

### What it does

`Counter` is a `dict` subclass for counting occurrences. You give it any iterable; it gives you a dict of `value → count`.

```python
from collections import Counter

c = Counter("banana")
# Counter({'a': 3, 'n': 2, 'b': 1})

c = Counter([1, 2, 2, 3, 3, 3])
# Counter({3: 3, 2: 2, 1: 1})

c = Counter("anagram") - Counter("nag")
# Counter({'a': 2, 'r': 1, 'm': 1})  — set-like subtraction
```

### Why it's so useful

The "count occurrences" pattern shows up in **anagram, frequency, top-K, and matching** problems. With `Counter`, you skip the boilerplate.

### Useful methods

```python
c = Counter("mississippi")

c.most_common(2)         # [('i', 4), ('s', 4)]   — top-2 most common
c['z']                   # 0  (NOT KeyError — Counter returns 0 for missing keys!)
sum(c.values())          # 11 — total count
list(c.elements())       # iterator over expanded items: 'i','i','i','i','s','s',...
c.update("xyz")          # add another iterable's counts
```

### Two interview-winning idioms

**Idiom 1 — anagram check in 1 line:**

```python
def is_anagram(s, t):
    return Counter(s) == Counter(t)
```

**Idiom 2 — top-K frequent:**

```python
def top_k_frequent(nums, k):
    return [val for val, _ in Counter(nums).most_common(k)]
```

That's it. Compare to writing both with raw `dict` — it's 4× more code.

### Common bug

```python
c = Counter("abc")
c['z']           # 0 — does NOT add 'z' to the counter
c['z'] += 1      # NOW 'z' is in the counter with value 1
```

Reading a missing key returns 0 but **doesn't insert** it. Writing inserts. Subtle but matters when iterating.

---

## 2. `defaultdict` — no more KeyError boilerplate

### What it does

`defaultdict(factory)` is a `dict` that auto-creates a default value when you access a missing key.

```python
from collections import defaultdict

d = defaultdict(int)        # default value: 0
d['apple'] += 1             # works — d['apple'] starts at 0, becomes 1
d['banana'] += 5

d = defaultdict(list)       # default value: []
d['fruits'].append('apple') # works — d['fruits'] starts as [], appends
d['fruits'].append('banana')

d = defaultdict(set)        # default value: set()
d['letters'].add('a')
```

### When to use which factory

| Factory | Default | Use for |
|---|---|---|
| `int` | `0` | counting (alternative to `Counter`) |
| `list` | `[]` | grouping items by key |
| `set` | `set()` | grouping unique items by key |
| `dict` | `{}` | nested dict |
| `lambda: <value>` | custom | any other default |

### The grouping pattern (huge in interviews)

```python
# Group anagrams: {sorted-letters: [original words]}
def group_anagrams(words):
    groups = defaultdict(list)
    for word in words:
        key = "".join(sorted(word))
        groups[key].append(word)
    return list(groups.values())
```

Without `defaultdict`, you'd write:

```python
groups = {}
for word in words:
    key = "".join(sorted(word))
    if key not in groups:
        groups[key] = []
    groups[key].append(word)
```

`defaultdict` saves the `if key not in groups: groups[key] = []` boilerplate. That's ~30% of typical solutions.

### Counter vs defaultdict(int) — which?

Both can count. Differences:

| | `Counter` | `defaultdict(int)` |
|---|---|---|
| Built for counting | Yes | Hacked into it |
| `.most_common(k)` | ✅ | ❌ |
| Set-like operations (`+`, `-`, `&`, `|`) | ✅ | ❌ |
| Slightly faster constructor with iterable | ✅ | ❌ |

**Rule:** if you're counting an iterable directly, use `Counter`. If you're counting in a custom way (e.g., counting weighted contributions), `defaultdict(int)` is fine.

---

## 3. `heapq` — priority queue in 5 lines

### What it does

`heapq` gives you a **min-heap** (smallest element always at index 0). Everything operates on a regular list.

```python
import heapq

heap = []
heapq.heappush(heap, 5)
heapq.heappush(heap, 2)
heapq.heappush(heap, 8)
heapq.heappush(heap, 1)
# heap is now [1, 2, 8, 5] — note: not fully sorted, just heap-ordered

heapq.heappop(heap)      # 1 — smallest
heapq.heappop(heap)      # 2
# heap is now [5, 8]

heapq.heapify(arr)       # convert any list to a heap in-place — O(n)
```

### Why min-heap is the right model

- **Top-K smallest** → keep a max-heap of size K, pop the largest when over capacity. Wait, but Python only gives min-heap…
- **Top-K largest** → keep a min-heap of size K, pop the smallest when over capacity.

```python
# Top-K largest in O(n log k)
def top_k_largest(nums, k):
    heap = []
    for x in nums:
        heapq.heappush(heap, x)
        if len(heap) > k:
            heapq.heappop(heap)
    return heap   # the K largest, in any order
```

### Max-heap with the negation trick

Python's `heapq` is a min-heap. For max-heap behavior, **push negative values**.

```python
heap = []
heapq.heappush(heap, -5)
heapq.heappush(heap, -2)
heapq.heappush(heap, -8)

largest = -heapq.heappop(heap)   # 8
```

Or for objects, push tuples `(-priority, item)`.

### Three interview gold idioms

**Idiom 1 — K closest points to origin (LeetCode 973):**

```python
def k_closest(points, k):
    heap = []
    for x, y in points:
        dist = x*x + y*y
        heapq.heappush(heap, (-dist, x, y))    # max-heap by dist
        if len(heap) > k:
            heapq.heappop(heap)
    return [(x, y) for _, x, y in heap]
```

**Idiom 2 — merge K sorted lists:**

```python
def merge_k_sorted(lists):
    heap = [(lst[0], i, 0) for i, lst in enumerate(lists) if lst]
    heapq.heapify(heap)
    result = []
    while heap:
        val, i, j = heapq.heappop(heap)
        result.append(val)
        if j + 1 < len(lists[i]):
            heapq.heappush(heap, (lists[i][j+1], i, j+1))
    return result
```

**Idiom 3 — running median (two heaps):**

Track lower half (max-heap) and upper half (min-heap). Median is in the larger heap's top.

### Useful one-liners

```python
heapq.nlargest(3, nums)      # top-3 largest, sorted descending
heapq.nsmallest(3, nums)     # bottom-3 smallest, sorted ascending
heapq.merge(list1, list2)    # iterator over merged sorted sequences
```

`nlargest` and `nsmallest` are O(n log k), perfect for "top-K" problems when K is small.

---

## 4. `bisect` — binary search built-in

### What it does

`bisect` does binary search on a **sorted** list. It tells you where a value would go to keep the list sorted.

```python
import bisect

arr = [1, 3, 5, 7, 9, 11]

bisect.bisect_left(arr, 5)    # 2  — leftmost position where 5 fits
bisect.bisect_right(arr, 5)   # 3  — rightmost position where 5 fits
bisect.bisect(arr, 5)         # 3  — alias for bisect_right

# Insertion (preserves sorted order)
bisect.insort(arr, 4)         # arr is now [1, 3, 4, 5, 7, 9, 11]
```

### When to use which

- **`bisect_left(arr, x)`**: leftmost spot where `x` could go = **first index of `x`** if it exists, or where it'd be inserted.
- **`bisect_right(arr, x)`**: rightmost spot = **first index *after* `x`**.

```python
arr = [1, 2, 2, 2, 3, 5]

bisect_left(arr, 2)    # 1  — first 2
bisect_right(arr, 2)   # 4  — just after the last 2

# Number of 2s = bisect_right - bisect_left
count_of_2 = bisect.bisect_right(arr, 2) - bisect.bisect_left(arr, 2)
# 3
```

### Interview idioms

**Idiom 1 — does `x` exist in sorted array (clean binary search)?**

```python
def contains(arr, x):
    i = bisect.bisect_left(arr, x)
    return i < len(arr) and arr[i] == x
```

**Idiom 2 — first element ≥ `x`:**

```python
i = bisect.bisect_left(arr, x)
# arr[i] is the first element ≥ x (if i < len(arr))
```

**Idiom 3 — last element ≤ `x`:**

```python
i = bisect.bisect_right(arr, x) - 1
# arr[i] is the last element ≤ x (if i >= 0)
```

**Idiom 4 — Longest Increasing Subsequence (LIS) in O(n log n):**

```python
def length_of_lis(nums):
    tails = []
    for x in nums:
        i = bisect.bisect_left(tails, x)
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)
```

This problem is classic and the `bisect` solution is a one-pager. Without bisect, the same solution is 20+ lines.

### Common bug

`bisect` requires the list to be **sorted**. If it's not, you get garbage. Always sort first or maintain sorted order with `insort`.

---

## 5. Honorable mentions — three more 1-liners

These aren't the "big four" but they save lines often.

### `sorted(iterable, key=...)`

```python
words = ["apple", "fig", "cherry"]

sorted(words)                            # alphabetical
sorted(words, key=len)                   # by length
sorted(words, key=lambda w: -len(w))     # by length, descending
sorted(words, reverse=True)              # reverse alphabetical

# Multiple keys
people = [("Alice", 30), ("Bob", 25), ("Alice", 22)]
sorted(people, key=lambda p: (p[0], p[1]))
# [('Alice', 22), ('Alice', 30), ('Bob', 25)]
```

### `collections.deque` — O(1) push/pop both ends

```python
from collections import deque

q = deque()
q.append(1)            # push to right — O(1)
q.appendleft(0)        # push to left  — O(1)
q.pop()                # pop right     — O(1)
q.popleft()            # pop left      — O(1)
```

Use deque for **BFS** (queue) and **sliding window with index** problems. Never use `list.pop(0)` — it's O(n).

### `itertools.combinations` / `permutations`

```python
from itertools import combinations, permutations, product

list(combinations([1, 2, 3], 2))    # [(1,2), (1,3), (2,3)]
list(permutations([1, 2, 3], 2))    # [(1,2), (1,3), (2,1), (2,3), (3,1), (3,2)]
list(product([1, 2], [3, 4]))       # [(1,3), (1,4), (2,3), (2,4)]
```

Skip the recursion boilerplate when the problem says "all subsets" or "all pairs."

### `zip(*matrix)` — transpose a matrix in 1 line

```python
matrix = [[1, 2, 3],
          [4, 5, 6],
          [7, 8, 9]]

transposed = list(zip(*matrix))
# [(1, 4, 7), (2, 5, 8), (3, 6, 9)]

# To get list of lists instead of tuples:
transposed = [list(row) for row in zip(*matrix)]
```

---

## 6. The cheat sheet (memorize)

| Need | Use | Import from |
|---|---|---|
| Count occurrences | `Counter(iterable)` | `collections` |
| Top-K most common | `Counter(iter).most_common(k)` | `collections` |
| Group items by key | `defaultdict(list)` | `collections` |
| Min priority queue | `heapq.heappush / heappop` | `heapq` |
| Max priority queue | `heapq` with negated values | `heapq` |
| K-largest | `heapq.nlargest(k, iter)` | `heapq` |
| Binary search exists? | `bisect_left` + check | `bisect` |
| Insert and keep sorted | `bisect.insort(list, x)` | `bisect` |
| O(1) both-end queue | `deque()` | `collections` |
| All k-subsets | `combinations(iter, k)` | `itertools` |

Every interview problem with "count," "top-K," "group by," "sorted insert," or "BFS" can use one of these.

---

## 7. Self-check

Can you, without peeking:

- [ ] Count letter frequency of `"hello"` in 1 line?
- [ ] Group `["bat", "tab", "cat"]` into anagram families?
- [ ] Find the 3 largest numbers in a list using `heapq`?
- [ ] Use `bisect` to check if a value is in a sorted list?
- [ ] Use `deque` to implement a BFS queue?
- [ ] Generate all 2-element combinations of `[1,2,3,4]`?

If yes → you're ready for the [STL deep-dive](python-stl-deep-dive.md).

---

## Up next

→ [Python STL deep-dive](python-stl-deep-dive.md) — `collections`, `itertools`, `functools`, `operator` — the complete tour.
