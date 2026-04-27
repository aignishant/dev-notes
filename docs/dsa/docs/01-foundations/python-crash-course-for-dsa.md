# Python crash course for DSA

> Just the Python you need to solve interview problems. No fluff.

If you've never coded before, this page won't be enough — you'll want a beginner Python tutorial too. But if you've written *any* Python (a `for` loop, a function), this page covers the rest.

---

## What this page assumes you know

- You can run a Python file (`python3 myfile.py`) or a REPL.
- You've seen `print("hello")`, `if x > 5:`, and `for i in range(10):`.

That's it. Everything else, we cover here.

---

## 1. Variables and types

```python
x = 5            # int
y = 3.14         # float
name = "Alice"   # str
done = True      # bool
nothing = None   # None — Python's "no value"
```

You don't declare types. Python figures them out from the value on the right.

**Important:** `int` and `float` are *different types*. `5` and `5.0` print the same but compare equal because Python coerces. Just know they exist.

```python
print(5 == 5.0)   # True
print(5 / 2)      # 2.5  — division ALWAYS returns float
print(5 // 2)     # 2    — integer division
print(5 % 2)      # 1    — remainder
print(2 ** 10)    # 1024 — power
```

!!! warning "The `/` vs `//` trap"
    In Python 3, `5 / 2 = 2.5` (float). For integer division, use `//`. This trips up everyone exactly once. The fix: always use `//` when you want integer math.

---

## 2. Lists — your daily driver

Lists are Python's array. Most DSA problems start with one.

### Create

```python
arr = [1, 2, 3, 4, 5]
empty = []
zeros = [0] * 10        # ten zeros: [0,0,0,0,0,0,0,0,0,0]
matrix = [[0] * 3 for _ in range(3)]   # 3×3 grid of zeros
```

!!! warning "The matrix gotcha"
    `[[0] * 3] * 3` creates 3 references to the **same** inner list. Modifying one row modifies all 3. Always use the comprehension form `[[0]*3 for _ in range(3)]`. This bug burns interview candidates daily.

### Index and slice

```python
arr = [10, 20, 30, 40, 50]
arr[0]       # 10  — first
arr[-1]      # 50  — last (negative = from the right)
arr[1:4]     # [20, 30, 40]  — half-open: includes start, excludes end
arr[:3]      # [10, 20, 30]
arr[2:]      # [30, 40, 50]
arr[::-1]    # [50, 40, 30, 20, 10]  — reverse
arr[::2]     # [10, 30, 50]  — every 2nd
```

Slicing **never errors** on out-of-range indices — it just returns what fits. Direct indexing (`arr[100]`) throws `IndexError`.

### Mutate

```python
arr.append(60)            # add to end → O(1)
arr.pop()                 # remove last → O(1), returns it
arr.pop(0)                # remove first → O(n) — SLOW, avoid
arr.insert(2, 99)         # insert at index 2 → O(n)
arr.remove(30)            # remove first occurrence of value 30 → O(n)
arr.extend([7, 8, 9])     # arr += [7, 8, 9]
arr.reverse()             # in-place reverse
arr.sort()                # in-place sort
sorted(arr)               # NEW sorted list (doesn't change arr)
len(arr)                  # length
30 in arr                 # boolean membership test, O(n)
```

### Most-used patterns in interviews

```python
# Sum
total = sum(arr)

# Min / max
mn, mx = min(arr), max(arr)

# Index of value
idx = arr.index(30)       # first index where value is 30; raises ValueError if not found

# Count
c = arr.count(30)

# Map / filter / accumulate
squared = [x*x for x in arr]
evens   = [x for x in arr if x % 2 == 0]
```

---

## 3. Strings — like lists, but immutable

```python
s = "hello"
s[0]         # 'h'
s[-1]        # 'o'
s[1:4]       # 'ell'
s[::-1]      # 'olleh'  — reverse a string
len(s)       # 5
"e" in s     # True
```

**Strings are immutable.** You can't do `s[0] = 'H'`. To "modify" a string, build a new one.

### Common operations

```python
s = "  Hello World  "
s.strip()                  # 'Hello World'   — remove whitespace ends
s.lower()                  # '  hello world  '
s.upper()                  # '  HELLO WORLD  '
s.split()                  # ['Hello', 'World']  — splits on whitespace
"a,b,c".split(",")         # ['a', 'b', 'c']
"-".join(["a", "b", "c"])  # 'a-b-c'
s.replace("Hello", "Hi")   # '  Hi World  '
s.startswith("  H")        # True
s.find("World")            # 8 (index, or -1 if not found)
"abc".isalpha()            # True
"123".isdigit()            # True
```

### Building strings — the "+= in loop" trap

```python
# ❌ SLOW: O(n²) total because each += creates a new string
result = ""
for ch in s:
    result += ch

# ✅ FAST: O(n) — collect to list, join at end
parts = []
for ch in s:
    parts.append(ch)
result = "".join(parts)
```

This trips people up. Strings are immutable, so `+=` reallocates every time. **In interviews, always join lists.**

### Char ↔ int

```python
ord('a')     # 97   — char to int
chr(97)      # 'a'  — int to char
ord('z') - ord('a')   # 25  — useful for "letter index"
```

---

## 4. Tuples — immutable lists

```python
point = (3, 5)
x, y = point          # unpacking
point[0]              # 3
# point[0] = 99       # ERROR — tuples are immutable
```

**When to use:**
- As **dict keys** (lists can't be keys, tuples can)
- For **multiple return values** from a function
- When you want to *prevent* accidental mutation

```python
def divmod_pair(a, b):
    return a // b, a % b   # returns a tuple

q, r = divmod_pair(17, 5)  # q=3, r=2
```

---

## 5. Dictionaries (hash maps) — your second daily driver

```python
d = {}                          # empty
d = {"a": 1, "b": 2}            # with values
d["c"] = 3                      # add
d["a"]                          # 1 — access (KeyError if missing)
d.get("z")                      # None — safe access
d.get("z", 0)                   # 0 — default if missing
"a" in d                        # True — O(1) membership
del d["a"]                      # remove
len(d)                          # 2
```

### Iterate

```python
for key in d:                   # iterates keys
    print(key, d[key])

for key, val in d.items():      # iterates pairs
    print(key, val)

for val in d.values():
    print(val)
```

### Why dicts are magical for DSA

```python
# Counting
counts = {}
for ch in "banana":
    counts[ch] = counts.get(ch, 0) + 1
# counts = {'b': 1, 'a': 3, 'n': 2}
```

This pattern shows up in 30% of array/string problems. Memorize it. (Or use `Counter` from [Python tricks](python-tricks-for-interviews.md) — easier.)

!!! tip "Dict access is O(1)"
    For interview purposes, treat `d[k]`, `k in d`, and `d[k] = v` as constant time. They aren't *theoretically* — they're amortized — but interviewers always accept O(1).

---

## 6. Sets — like dicts but values-only

```python
s = set()                       # empty (NOT {} — that's an empty dict)
s = {1, 2, 3}                   # with values
s.add(4)
s.remove(2)                     # KeyError if missing
s.discard(2)                    # safe — does nothing if missing
3 in s                          # True — O(1)
len(s)                          # number of elements

a = {1, 2, 3}
b = {2, 3, 4}
a | b                           # union: {1, 2, 3, 4}
a & b                           # intersection: {2, 3}
a - b                           # difference: {1}
a ^ b                           # symmetric difference: {1, 4}
```

**When to use a set:** when you only care about "have I seen this?" — not "how many times?"

```python
# Find first repeated element
def first_repeat(arr):
    seen = set()
    for x in arr:
        if x in seen:
            return x
        seen.add(x)
    return None
```

---

## 7. Functions

```python
def add(a, b):
    return a + b

def greet(name="World"):        # default argument
    return f"Hello, {name}"

def sum_all(*nums):             # *args = variadic
    return sum(nums)

def make_user(**kwargs):        # **kwargs = keyword variadic
    return kwargs

# Calling
add(2, 3)                       # 5
greet()                         # "Hello, World"
greet("Alice")                  # "Hello, Alice"
greet(name="Bob")               # "Hello, Bob"  — keyword arg
sum_all(1, 2, 3, 4)             # 10
make_user(name="Eve", age=30)   # {'name': 'Eve', 'age': 30}
```

### The mutable default argument trap

```python
# ❌ BUG: default list is shared across calls
def add_item(item, lst=[]):
    lst.append(item)
    return lst

print(add_item(1))   # [1]
print(add_item(2))   # [1, 2]   — surprised? you should be

# ✅ FIX
def add_item(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst
```

This bug shows up in real codebases. Don't use mutable defaults.

---

## 8. Conditionals

```python
x = 10
if x > 0:
    print("positive")
elif x < 0:
    print("negative")
else:
    print("zero")

# Ternary — fits on one line
sign = "pos" if x > 0 else "neg"

# Chained comparisons
if 0 < x < 100:                 # nice
    print("in range")
```

### Truthy and falsy values

```python
if some_list:                   # True if non-empty
if not some_list:               # True if empty
```

These are **falsy**: `None`, `False`, `0`, `0.0`, `""`, `[]`, `{}`, `set()`, `tuple()`.

Everything else is **truthy**.

In interviews, prefer `if arr:` over `if len(arr) > 0:` and `if arr is not None:`.

---

## 9. Loops

```python
# range(start, stop, step)  — stop is EXCLUSIVE
for i in range(5):              # 0, 1, 2, 3, 4
for i in range(2, 7):           # 2, 3, 4, 5, 6
for i in range(10, 0, -2):      # 10, 8, 6, 4, 2

# Iterating a list — by value
for x in arr:
    print(x)

# Iterating with index
for i, x in enumerate(arr):
    print(i, x)

# Iterating two lists in lock-step
for x, y in zip(arr1, arr2):
    print(x, y)

# Nested
for i in range(rows):
    for j in range(cols):
        ...

# while
while condition:
    ...

# break / continue
for x in arr:
    if x < 0:
        continue                # skip this iteration
    if x > 100:
        break                   # exit the loop
    print(x)
```

### enumerate vs range — interviewers care

```python
# ❌ Less idiomatic
for i in range(len(arr)):
    print(i, arr[i])

# ✅ Idiomatic
for i, x in enumerate(arr):
    print(i, x)
```

Both work. The second is what senior Python looks like.

---

## 10. Comprehensions — Python's superpower

```python
# List
squared = [x*x for x in arr]
evens = [x for x in arr if x % 2 == 0]
matrix_flat = [v for row in matrix for v in row]   # flatten

# Dict
sq_dict = {x: x*x for x in range(5)}        # {0:0, 1:1, 2:4, 3:9, 4:16}
inverted = {v: k for k, v in d.items()}     # swap keys and values

# Set
unique_chars = {c for c in s if c.isalpha()}
```

**When to use:** when the loop body is one expression. **When NOT to use:** when the body has 3+ steps or a conditional with side effects. Loops are still fine and clearer for those.

---

## 11. Lambdas

```python
square = lambda x: x * x
square(5)                        # 25

# Most common use: as a sort key
words = ["apple", "fig", "cherry"]
words.sort(key=lambda w: len(w))           # sort by length
# words = ['fig', 'apple', 'cherry']

pairs = [(1, "b"), (2, "a"), (3, "c")]
pairs.sort(key=lambda p: p[1])             # sort by 2nd element
```

Lambdas are anonymous one-line functions. Use for short, throwaway logic. For anything multi-line, use `def`.

---

## 12. Classes — just enough for trees and graphs

```python
class Node:
    def __init__(self, val):
        self.val = val
        self.next = None

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

# Use
root = TreeNode(1, TreeNode(2), TreeNode(3))
print(root.val)            # 1
print(root.left.val)       # 2
```

For 95% of interview problems, this is all the OOP you need. Encapsulation, inheritance, design patterns — those are LLD round territory ([Phase 13](../09-low-level-design/index.md)).

---

## 13. Common pitfalls — read this twice

> ⚠️ **`5 / 2 = 2.5`** in Python 3. Use `//` for integer division.
>
> ⚠️ **Strings are immutable.** Use `"".join(list_of_chars)`, not `+=`.
>
> ⚠️ **Mutable default args** — `def f(x=[])` is a bug factory. Use `None` and check.
>
> ⚠️ **`[[0]*n]*m`** creates aliased rows. Use `[[0]*n for _ in range(m)]`.
>
> ⚠️ **`set()` is empty set.** `{}` is empty dict.
>
> ⚠️ **`is` vs `==`.** `is` checks identity (same object). `==` checks value. Use `==` for almost everything; reserve `is` for `is None`.
>
> ⚠️ **`copy()` is shallow.** For nested structures, use `import copy; copy.deepcopy(x)`.

---

## 14. Self-check

Without peeking, can you:

- [ ] Reverse a list in 1 line of Python?
- [ ] Get the last element of a list?
- [ ] Iterate a list with both index and value?
- [ ] Initialize a 3×4 grid of zeros (correctly)?
- [ ] Count occurrences of each character in a string using a `dict`?
- [ ] Sort a list of `(name, age)` tuples by age?
- [ ] Create a set of unique elements from a list?
- [ ] Define a class for a binary tree node?

If yes to all → you're ready for the [Python tricks](python-tricks-for-interviews.md) page.

If no to any → re-read that section and re-type the example. Don't move on.

---

## Up next

→ [Python tricks for interviews](python-tricks-for-interviews.md) — Counter, defaultdict, heapq, bisect.
