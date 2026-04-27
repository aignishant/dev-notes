# The dry-run method

> Trace your code by hand, on paper, with one example. The single highest-leverage habit in problem-solving.

---

## What a dry run is

A **dry run** is when you simulate your code on paper (or in your head, or on a whiteboard) using a small example, line by line, tracking every variable's value at every step.

It's not running the code. It's pretending to be the computer and watching your own logic execute.

Real-world analogy: before you bake a cake for 100 people, you bake one. You see what happens. You catch the surprises.

---

## Why dry runs matter

In an interview:

- You **can't run code** half the time (whiteboard, doc editor, screen share with no IDE).
- Even when you can run it, the test runner is slow and noisy.
- A dry run takes 60 seconds and catches 80% of bugs.
- Interviewers respect candidates who dry-run *before* claiming "I'm done."

In practice (LeetCode, real work):

- Dry runs build intuition. After 50 dry runs, you'll see bugs in code you wrote 5 seconds ago, before running it.
- Dry runs surface edge cases you didn't think to test.
- Dry runs let you debug **without a debugger**.

This is the single most under-practiced skill among average candidates.

---

## How to do a dry run — the technique

1. **Pick a small example.** Not the example from the problem (already obvious). Pick one that's small but non-trivial — maybe 4-6 elements, with at least one tricky case (duplicate, edge value, empty, etc.).
2. **Set up a table** with one column per variable.
3. **Walk through your code line by line.** For each line that changes a variable, update the table.
4. **Check loop conditions and branches.** Mark which `if` branches fire.
5. **Watch the return value.**
6. **Compare to the expected answer.** If they match, you've validated the logic for that example. Try another example with a different shape.

Use whatever notation you like — paper, whiteboard, comment block in your editor. The key is **make it visible**.

---

## Worked example 1 — Two Sum

```python
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
```

**Dry run with `nums = [3, 5, 1, 7], target = 8`:**

| Iter | i | num | complement | `complement in seen`? | seen after |
|------|---|-----|------------|-----------------------|------------|
| start | — | — | — | — | `{}` |
| 1 | 0 | 3 | 5 | no | `{3: 0}` |
| 2 | 1 | 5 | 3 | **yes** → return `[0, 1]` | — |

Return `[0, 1]`. Expected: indices of 3 and 5. ✅

Now try `nums = [3, 5, 1, 7], target = 4`:

| Iter | i | num | complement | `complement in seen`? | seen after |
|------|---|-----|------------|-----------------------|------------|
| 1 | 0 | 3 | 1 | no | `{3: 0}` |
| 2 | 1 | 5 | -1 | no | `{3: 0, 5: 1}` |
| 3 | 2 | 1 | 3 | **yes** → return `[0, 2]` | — |

Return `[0, 2]`. ✅

Try `nums = [3, 5], target = 100` (no pair):

| Iter | i | num | complement | `complement in seen`? | seen after |
|------|---|-----|------------|-----------------------|------------|
| 1 | 0 | 3 | 97 | no | `{3: 0}` |
| 2 | 1 | 5 | 95 | no | `{3: 0, 5: 1}` |
| end | — | — | — | — | — |

Falls through, returns `[]`. ✅

Edge case: `nums = [3, 3], target = 6`:

| Iter | i | num | complement | `complement in seen`? | seen after |
|------|---|-----|------------|-----------------------|------------|
| 1 | 0 | 3 | 3 | no | `{3: 0}` |
| 2 | 1 | 3 | 3 | **yes** → return `[0, 1]` | — |

Return `[0, 1]`. ✅ Note this catches a subtle bug: if you'd written `seen[num] = i` *before* the lookup, you'd return `[1, 1]` (wrong). Dry run caught the order.

---

## Worked example 2 — sliding window (longest substring without repeating)

```python
def length_of_longest_substring(s):
    seen = set()
    left = 0
    longest = 0
    for right in range(len(s)):
        while s[right] in seen:
            seen.remove(s[left])
            left += 1
        seen.add(s[right])
        longest = max(longest, right - left + 1)
    return longest
```

**Dry run with `s = "abcabcbb"`:**

| right | s[right] | While loop | seen after | left | window length | longest |
|-------|----------|------------|------------|------|---------------|---------|
| 0 | a | (skip) | {a} | 0 | 1 | 1 |
| 1 | b | (skip) | {a, b} | 0 | 2 | 2 |
| 2 | c | (skip) | {a, b, c} | 0 | 3 | 3 |
| 3 | a | a in seen → remove s[0]=a, left=1 | {b, c, a} | 1 | 3 | 3 |
| 4 | b | b in seen → remove s[1]=b, left=2 | {c, a, b} | 2 | 3 | 3 |
| 5 | c | c in seen → remove s[2]=c, left=3 | {a, b, c} | 3 | 3 | 3 |
| 6 | b | b in seen → remove s[3]=a, left=4; remove s[4]=b, left=5 | {c, b} | 5 | 2 | 3 |
| 7 | b | b in seen → remove s[5]=c, left=6; remove s[6]=b, left=7 | {b} | 7 | 1 | 3 |

Return 3. ✅ Expected: "abc" → length 3.

Notice how the dry run caught the inner `while` loop running multiple times in one iteration (rows 6 and 7). If you'd misread it as a single `if`, you'd get the wrong answer.

---

## Worked example 3 — recursive tree depth

```python
def max_depth(root):
    if root is None:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))
```

**Dry run with this tree:**

```
       1
      / \
     2   3
    /
   4
```

Use a call stack table:

| Call | Returns | Why |
|------|---------|-----|
| `max_depth(1)` | ? | needs L, R |
| ↳ `max_depth(2)` | ? | needs L, R |
| ↳↳ `max_depth(4)` | ? | needs L, R |
| ↳↳↳ `max_depth(None)` | 0 | base case |
| ↳↳↳ `max_depth(None)` | 0 | base case |
| ↳↳ `max_depth(4)` | 1 + max(0, 0) = 1 | |
| ↳↳ `max_depth(None)` | 0 | base case (right of 2) |
| ↳ `max_depth(2)` | 1 + max(1, 0) = 2 | |
| ↳ `max_depth(3)` | ? | needs L, R |
| ↳↳ `max_depth(None)` | 0 | |
| ↳↳ `max_depth(None)` | 0 | |
| ↳ `max_depth(3)` | 1 + max(0, 0) = 1 | |
| `max_depth(1)` | 1 + max(2, 1) = 3 | |

Return 3. ✅ The deepest path is 1→2→4 (3 nodes).

---

## When you should dry-run

✅ **Always dry-run when:**
- You just wrote the function and haven't run it yet.
- You're in an interview without a runner.
- Your code "looks right" but you have a hunch.
- You can't reach a bug with breakpoints.
- You're about to claim "I'm done."

❌ **You can skip dry-running when:**
- The function is 3 lines and uses only built-ins you've used 1000 times.
- You've already run it on the obvious examples and got correct output.

When in doubt, dry-run.

---

## Picking the right dry-run input

A good dry-run input has:

1. **Small size.** 3-6 elements. Not the trivial 1-element case.
2. **A non-obvious structure.** Mix of values, at least one duplicate or edge.
3. **A clear expected answer.** You should know what the right output is before tracing.

| Problem type | Good dry-run input |
|---|---|
| Array manipulation | `[3, 1, 4, 1, 5]` (has duplicate) |
| Two-pointer | `[1, 2, 3, 4, 5]` and `target = 7` |
| Sliding window | `"abcabcbb"` (mixed repeats) |
| Tree | small tree with both balanced and skewed sections |
| Graph | 4-5 nodes, at least one cycle |
| DP | input that reveals overlapping subproblems |

---

## Dry-running in an interview — script

```
You: "Let me trace through with an example to make sure this works.
      Take nums = [3, 5, 1, 7], target = 8."

[Walk through table out loud, narrating]

You: "i=0, num=3, complement=5, 5 isn't in seen, so we add 3:0.
      i=1, num=5, complement=3, 3 is in seen at index 0, return [0, 1]. ✓"

You: "Let's try the no-pair case. nums=[3, 5], target=100.
      We add both, fall through, return []. ✓"

You: "Edge case — duplicates. nums=[3, 3], target=6.
      i=0 we add 3:0. i=1 we look up 3, find it, return [0, 1]. ✓
      Important: we check `seen` before adding, so the first 3 doesn't conflict with itself."
```

This narration *signals* you understand your code. Interviewers love it.

---

## Common dry-run discoveries

After enough dry runs, you'll start catching these classic bugs:

### 1. Off-by-one in loop bounds
```python
for i in range(len(arr)):     # 0..n-1
for i in range(len(arr)+1):   # 0..n  ← reads arr[n], crash
for i in range(1, len(arr)):  # 1..n-1, skips arr[0]
```

A dry run catches whether you meant to skip the first.

### 2. Updating state in wrong order
```python
seen[num] = i            # ❌ added before checking
if complement in seen:
    return ...
```

Dry run shows that this returns `[i, i]` for `nums=[3], target=6` — caught instantly.

### 3. Missing edge case
```python
def length(s):
    return s.index(' ')   # ❌ what if no space?
```

Dry run with `"hello"` → ValueError. Caught before submit.

### 4. Wrong comparison
```python
while left < right:      # vs `left <= right` — different inclusion
```

Dry run with a 1-element array reveals which is right.

### 5. Wrong loop variable
```python
for i in range(n):
    arr[j] = ...         # ❌ used `j` instead of `i`
```

Dry run column for `j` shows it never changes — bug.

---

## Dry-running for big-O

You can also dry-run to *count* operations.

```python
for i in range(n):
    for j in range(i, n):    # not n!
        ...
```

How many times does the body run? Trace for n=4:

- i=0: j=0,1,2,3 → 4 iterations
- i=1: j=1,2,3 → 3
- i=2: j=2,3 → 2
- i=3: j=3 → 1

Total: 4+3+2+1 = 10. For general n, that's `n*(n+1)/2` ≈ O(n²).

Now you know the answer **and** the constant factor.

---

## Dry-running for correctness proofs

The tightest interview answer is one where you can argue *why* the algorithm is correct.

**Sliding window invariant:**
> "After each iteration, `seen` holds exactly the characters in `s[left:right+1]`, and they are all distinct."

Dry-run this invariant on your example. Does it hold at every iteration? If yes, you've proved correctness for that input. (Real proofs go deeper, but this is interview-grade.)

---

## Common mistakes when dry-running

### 1. Skipping steps mentally
You'll be tempted to say "obviously this works." Don't. **Write every line.** That's the whole point.

### 2. Using too small an input
`arr = [1, 2]` doesn't expose duplicates, edge values, or branching. Use 4-6 elements.

### 3. Not tracking all variables
You think it's fine because the variable you care about is correct, but a side-effect variable went stale. Track all state.

### 4. Believing the variable name
`done = True` may not mean "done." Check the actual logic that reads `done`.

### 5. Dry-running the wrong function
If your bug is in a helper, dry-run the helper. The outer function might be a red herring.

---

## A two-minute interview drill

Pick a problem you've solved before. Open the solution. Don't read it.

1. Write a fresh test case (4-6 elements).
2. Read your code line by line, building the variable table.
3. Compute the return value.
4. Check against expected output.
5. If wrong: which line is the first to deviate?

Do this 5 times a week for a month. Your bug-catching speed will double.

---

## Self-check

Dry-run this code with `nums = [4, 1, 2, 1, 2]`:

```python
def single_number(nums):
    result = 0
    for x in nums:
        result ^= x
    return result
```

Track `result` after each iteration. (Hint: `^` is XOR.)

| iter | x | result before | result after |
|------|---|---------------|--------------|
| 1 | 4 | 0 | 4 |
| 2 | 1 | 4 | 5 |
| 3 | 2 | 5 | 7 |
| 4 | 1 | 7 | 6 |
| 5 | 2 | 6 | 4 |

Return 4. ✅ The "single number" (no duplicate) is 4.

Notice: XOR cancels duplicates, leaving the lonely one. Without the dry run, you might believe this works; with the dry run, you *understand* why.

---

## The mental upgrade

Once dry-running becomes a habit, you stop guessing whether your code works. You **know**. That confidence is what interviewers see and what mediocre candidates lack.

Practice this on every single LeetCode problem until it's automatic. Then apply it on real-world bugs.

---

## Section 01 — Foundations is complete

You now have:

1. **[Python crash course](python-crash-course-for-dsa.md)** — language basics, idioms, gotchas.
2. **[Python tricks for interviews](python-tricks-for-interviews.md)** — Counter, heapq, bisect, defaultdict.
3. **[Python STL deep dive](python-stl-deep-dive.md)** — collections, itertools, functools.
4. **[Time complexity explained](time-complexity-explained.md)** — Big-O without the math degree.
5. **[Space complexity explained](space-complexity-explained.md)** — what "in-place" means.
6. **[Big-O cheatsheet](big-o-cheatsheet.md)** — one-page reference.
7. **[How to think recursively](how-to-think-recursively.md)** — mindset and templates.
8. **[Input/output handling](input-output-handling.md)** — read fast, print clean.
9. **[Code quality for interviews](code-quality-for-interviews.md)** — naming, structure, edge cases.
10. **[The dry-run method](dry-run-method.md)** — this page.

→ **Next section: [Data structures](../02-data-structures/index.md)** — arrays first, then strings, then everything else.
