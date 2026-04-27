# Code quality for interviews

> Two solutions can be the same Big-O, but only one looks "senior." Here's how to make yours look senior.

---

## Why code quality matters in interviews

Interviewers don't just grade correctness. They grade **how you'd write code on their team**.

A messy correct solution gets a "weak hire." A clean correct solution gets a "strong hire." Same algorithm, different signal.

The good news: code quality follows a small set of habits. Build them in practice; they show up automatically under pressure.

---

## The five things interviewers notice

1. **Names** — variables, functions, parameters. Are they readable?
2. **Structure** — is the function shaped logically? Edge cases at top, main flow in the middle, return at bottom?
3. **Comments** — sparse, useful, never restating the code.
4. **Type hints + docstrings** — bonus points, especially for senior roles.
5. **Edge case handling** — empty input, single element, max/min values, negatives, duplicates.

Master these five. The rest is style.

---

## 1. Names

### Bad names

```python
def f(a, b):
    r = []
    for i in range(len(a)):
        for j in range(len(a)):
            if a[i] + a[j] == b and i != j:
                r.append([i, j])
    return r
```

What does this do? You have to read the body to find out.

### Good names

```python
def find_pairs_with_sum(nums: list[int], target: int) -> list[list[int]]:
    pairs = []
    for i in range(len(nums)):
        for j in range(len(nums)):
            if nums[i] + nums[j] == target and i != j:
                pairs.append([i, j])
    return pairs
```

Now the function tells you what it does at a glance.

### Naming rules

- **Function names**: verbs. `find_pair`, `compute_distance`, `is_valid`, `count_islands`.
- **Variables**: nouns. `nums`, `total`, `result`, `seen`, `count`.
- **Booleans**: `is_X` / `has_X` / `can_X`. `is_palindrome`, `has_cycle`, `can_jump`.
- **Indices in loops**: `i`, `j`, `k` are fine for short loops. For longer functions, use meaningful names: `row`, `col`, `idx`, `node_idx`.
- **Avoid single-letter names** unless conventional: `n` (size), `i/j` (indices), `x/y` (coords), `s` (string).
- **No abbreviations** unless ubiquitous: `idx` ✓, `cnt` ✗ (just say `count`), `nbr` ✗ (just say `neighbor`).

### Names by problem type

| Domain | Common names |
|---|---|
| Arrays | `nums`, `arr`, `target`, `i`, `j`, `left`, `right` |
| Strings | `s`, `t`, `pattern`, `ch`, `idx` |
| Trees | `root`, `node`, `left`, `right`, `parent`, `depth` |
| Graphs | `graph`, `adj`, `node`, `neighbor`, `visited`, `queue` |
| DP | `dp`, `prev`, `curr`, `cache` |
| Hash maps | `seen`, `count`, `index_of`, `freq` |

These names are familiar to interviewers. Use them.

---

## 2. Structure

### Standard function shape

```python
def solve(input):
    # 1. Edge cases (early return)
    if not input:
        return <default>

    # 2. Initialize state
    state = ...

    # 3. Main logic
    for x in input:
        ...

    # 4. Return
    return result
```

This shape reads top-to-bottom. Edge cases at the top, main work in the middle, return at the bottom.

### Example — Two Sum

```python
def two_sum(nums: list[int], target: int) -> list[int]:
    """Return indices of two numbers that sum to target.

    Returns empty list if no pair exists.
    """
    # Edge case
    if len(nums) < 2:
        return []

    # State: map of value → index seen so far
    seen = {}

    # Main loop
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i

    # Fall-through: no pair found
    return []
```

This reads cleanly.

### Decompose long functions

If your solution is 60+ lines, split it. Most interviewers value a helper function more than a clever one-liner.

```python
def solve(grid):
    if not grid: return 0
    rows, cols = len(grid), len(grid[0])
    visited = [[False] * cols for _ in range(rows)]

    def dfs(r, c):
        if r < 0 or c < 0 or r >= rows or c >= cols: return
        if visited[r][c] or grid[r][c] == 0: return
        visited[r][c] = True
        for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
            dfs(r + dr, c + dc)

    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1 and not visited[r][c]:
                dfs(r, c)
                count += 1
    return count
```

The helper `dfs` is named, scoped, and reusable. The outer logic is clear.

---

## 3. Comments

### When to comment

✅ **Comment when:**
- The "why" isn't obvious from the code.
- You're using a non-trivial trick or invariant.
- You're hand-waving an assumption (e.g., "input is sorted").

❌ **Don't comment when:**
- The code is self-explanatory.
- The comment just restates what the code does.
- The comment is a TODO that doesn't belong.

### Bad comments

```python
i = 0                            # initialize i to 0
i += 1                           # increment i by 1
if x == 0: return                # if x equals zero, return
```

These are noise. Delete.

### Good comments

```python
# Two-pointer scan: left and right converge from opposite ends.
# Invariant: arr[:left] and arr[right+1:] are both already sorted.
left, right = 0, len(arr) - 1
```

Or:

```python
# We use a max-heap by negating values, since heapq is a min-heap.
heapq.heappush(heap, -value)
```

These add context the code can't show.

---

## 4. Type hints + docstrings

In LeetCode you can skip these. In a Google interview or a senior role, **add them**. They take 5 seconds and signal professionalism.

### Type hints (Python 3.9+)

```python
def two_sum(nums: list[int], target: int) -> list[int]:
    ...

def is_valid(s: str) -> bool:
    ...

def find_path(graph: dict[int, list[int]], start: int, end: int) -> list[int] | None:
    ...
```

Use modern syntax: `list[int]` not `List[int]`, `int | None` not `Optional[int]`.

### Docstrings (Google-style)

```python
def two_sum(nums: list[int], target: int) -> list[int]:
    """Return indices of two numbers that sum to target.

    Args:
        nums: List of integers (may contain duplicates).
        target: The desired sum.

    Returns:
        A list of two indices [i, j] with i < j and nums[i] + nums[j] == target.
        Empty list if no such pair exists.

    Time:  O(n) — single pass with hash map.
    Space: O(n) — hash map of values seen.
    """
```

This is what professional Python looks like. Stating time/space in the docstring is a power move.

---

## 5. Edge cases

These are your free interview points. Always check:

| Edge case | Default response |
|---|---|
| Empty input (`[]`, `""`, `None`) | Return default (0, [], None, False) |
| Single element | Often the answer is itself |
| All same elements | Watch for divide-by-zero, count = n |
| Sorted vs reverse-sorted | Check if your alg assumes sorted |
| Negative numbers | Especially in DP / sliding window |
| Duplicates | Especially in two-pointer |
| Max int / overflow | Less common in Python, but mention it |
| Cycles (in linked list / graph) | Track `visited` |

### Pattern: handle at the top

```python
def solve(arr):
    if not arr:                          # empty
        return 0
    if len(arr) == 1:                    # single element
        return arr[0]
    # main logic
```

Always *say* you're checking edge cases. Even if you don't write them all out, mention them: "If `arr` is empty, I'd return 0 — let me handle that."

---

## A bad-code → good-code transformation

### Before

```python
def f(a):
    d = {}
    for i in range(len(a)):
        if a[i] in d:
            d[a[i]] += 1
        else:
            d[a[i]] = 1
    m = 0
    r = None
    for k in d:
        if d[k] > m:
            m = d[k]
            r = k
    return r
```

### After

```python
from collections import Counter

def most_frequent(nums: list[int]) -> int | None:
    """Return the most frequent number in nums (None if empty)."""
    if not nums:
        return None

    counts = Counter(nums)
    return counts.most_common(1)[0][0]
```

Same correctness. Half the lines. Clearer intent. Uses the standard library.

---

## Style guide — the short version

| Rule | Example |
|---|---|
| Functions are verbs | `find_pair`, `is_valid`, `compute_total` |
| Variables are nouns | `nums`, `result`, `seen`, `count` |
| Use `_` for unused vars | `for _ in range(n):` |
| Use `enumerate` not `range(len(...))` | `for i, x in enumerate(arr):` |
| Use `zip` not parallel indices | `for a, b in zip(arr1, arr2):` |
| Prefer comprehensions to manual loops | `[x*2 for x in arr]` |
| Constants in UPPER_SNAKE_CASE | `MAX_DEPTH = 100` |
| Spaces around binary ops | `x + y`, not `x+y` |
| 4-space indent, no tabs | (Python standard) |
| Empty line between logical chunks | Improves readability |

---

## What interviewers say privately

Real interviewer feedback I've seen:

✅ "Wrote clear code, named variables sensibly, handled edges first. Easy hire."
✅ "Refactored mid-interview when she noticed the function was getting long. Senior-level instinct."
❌ "Solved the problem but variables were `a, b, c, x, y, z`. Hard to follow."
❌ "Crammed everything into one giant function. Hard to debug under questioning."
❌ "Didn't handle empty input. Crashed when I tested with `[]`."

---

## A 30-second self-review checklist

Before you say "I'm done":

- [ ] Function name describes what it does
- [ ] Variable names are readable (not `a, b, x, t1`)
- [ ] Edge cases handled at top
- [ ] No dead code / unused variables
- [ ] No print statements (unless asked)
- [ ] Type hints on inputs and outputs (bonus)
- [ ] One docstring (bonus)
- [ ] Time / space complexity stated out loud

If you do all 8 in every interview, you'll be the cleanest 80% of candidates.

---

## Anti-patterns to avoid

### 1. Premature optimization

Don't write `bisect_left` magic when a simple `for` loop would be just as fast for n=100. Optimize after correctness.

### 2. Cleverness for its own sake

```python
return [(x, y) for x in arr1 for y in arr2 if x + y == target if x < y]
```

vs

```python
result = []
for x in arr1:
    for y in arr2:
        if x + y == target and x < y:
            result.append((x, y))
return result
```

The second is plainer and equally fast. Prefer it.

### 3. Mutating inputs without saying so

```python
def solve(nums):
    nums.sort()       # ⚠️ caller's list got mutated
    ...
```

If you'll mutate the input, **say so** to the interviewer or copy first: `nums = sorted(nums)`.

### 4. Magic numbers

```python
if x > 100:                       # what's 100?
    return False
```

vs

```python
MAX_REQUESTS_PER_MINUTE = 100
if x > MAX_REQUESTS_PER_MINUTE:
    return False
```

### 5. Catching `Exception`

```python
try:
    ...
except Exception:                # too broad
    pass
```

Catch specific exceptions: `except KeyError:`, `except ValueError:`, etc.

---

## What "Pythonic" really means

- Use the standard library (`Counter`, `defaultdict`, `heapq`, `bisect`).
- Use built-in iteration patterns (`enumerate`, `zip`, `reversed`).
- Use comprehensions where they fit.
- Avoid C-style `for i in range(len(arr))` when `for x in arr` works.
- Avoid manual `if x not in d: d[x] = []` when `defaultdict(list)` exists.
- Prefer EAFP ("ask for forgiveness") over LBYL ("look before you leap"):

```python
# LBYL
if key in d:
    val = d[key]
else:
    val = default

# EAFP (Pythonic)
val = d.get(key, default)
```

---

## Self-check

Rewrite this for clarity:

```python
def f(g, s):
    v = [False] * len(g)
    q = [s]
    v[s] = True
    c = 0
    while q:
        x = q.pop(0)
        c += 1
        for y in g[x]:
            if not v[y]:
                v[y] = True
                q.append(y)
    return c
```

(Answer: rename `f` to `count_reachable`, `g` to `graph`, `s` to `start`, `v` to `visited`, `q` to `queue`, `c` to `count`. Use `deque`. Add type hints and docstring.)

---

## Up next

→ [The dry-run method](dry-run-method.md) — verify your solution before you write a single line of test code.
