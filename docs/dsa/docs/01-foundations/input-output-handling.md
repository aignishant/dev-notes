# Input/output handling

> Read fast, print clean. Mostly for online judges and competitive programming, but useful in interviews too.

---

## Why this matters

Most LeetCode-style interviews give you a function signature — input is already parsed for you. But:

- **Codeforces, HackerRank, GFG, online judges** — you read raw stdin.
- **Indian service company / PSU coding tests** — same. You read input yourself.
- **Some product company OAs** — also stdin-based.
- **Interview "implement a CLI"** — you parse args and stdin.

If you can't read input cleanly under pressure, you'll lose 5 minutes you don't have.

---

## The basics — `input()` and `print()`

### `input()` — reads one line, returns a `str`

```python
name = input()              # "Alice"
print(name)                 # Alice
```

`input()` **always returns a string**. Even if the user types `42`, you get `"42"`.

### Convert types yourself

```python
n = int(input())            # "42" → 42
x = float(input())          # "3.14" → 3.14
```

---

## Reading multiple values on one line

This is the most common pattern. Input like `3 5 7` on a single line.

```python
# Read three ints separated by spaces
a, b, c = map(int, input().split())
```

Breakdown:
- `input()` → `"3 5 7"`
- `.split()` → `["3", "5", "7"]`
- `map(int, ...)` → iterator that yields `3, 5, 7`
- Unpack into `a, b, c`

If you don't know how many values:

```python
nums = list(map(int, input().split()))     # any number of ints
```

---

## Reading n lines

Pattern: first line is `n`, then `n` lines follow.

```python
n = int(input())
arr = []
for _ in range(n):
    arr.append(int(input()))
```

Or with comprehension:

```python
n = int(input())
arr = [int(input()) for _ in range(n)]
```

Or with `sys.stdin` (faster, see below):

```python
import sys
data = sys.stdin.read().split()
n = int(data[0])
arr = list(map(int, data[1:1+n]))
```

---

## Reading a 2D matrix

```python
n, m = map(int, input().split())     # rows, cols
grid = []
for _ in range(n):
    row = list(map(int, input().split()))
    grid.append(row)
```

Or one-liner:

```python
grid = [list(map(int, input().split())) for _ in range(n)]
```

---

## Fast I/O — `sys.stdin` and `sys.stdout`

`input()` is slow when you have 10⁵+ lines. Use `sys.stdin`.

### Pattern: read everything at once

```python
import sys
input = sys.stdin.readline                # rebind input to be faster

n = int(input())
arr = list(map(int, input().split()))
```

That single rebinding `input = sys.stdin.readline` is a 5-10× speedup.

### Pattern: read all input as one big blob

For very large inputs, read everything at once:

```python
import sys
data = sys.stdin.read().split()
idx = 0

n = int(data[idx]); idx += 1
arr = list(map(int, data[idx:idx+n])); idx += n
```

This is the fastest, but you manage your own pointer.

### Fast print

```python
import sys
print = sys.stdout.write     # or use sys.stdout.write directly
```

But careful — `sys.stdout.write` doesn't auto-add `\n` and only takes strings.

For many lines of output, build a list and join:

```python
output = []
for x in arr:
    output.append(str(x))
sys.stdout.write("\n".join(output) + "\n")
```

This is much faster than calling `print()` 10⁵ times.

---

## Common input formats

### Format 1 — single number

```
5
```
```python
n = int(input())
```

### Format 2 — array of numbers, single line

```
3 1 4 1 5 9 2 6
```
```python
arr = list(map(int, input().split()))
```

### Format 3 — n then array

```
8
3 1 4 1 5 9 2 6
```
```python
n = int(input())
arr = list(map(int, input().split()))
```

### Format 4 — multiple test cases

```
3
4
1 2 3 4
2
5 5
3
1 1 1
```
```python
t = int(input())
for _ in range(t):
    n = int(input())
    arr = list(map(int, input().split()))
    # solve
```

### Format 5 — string input

```
hello world
```
```python
s = input()                  # "hello world"
words = input().split()      # ["hello", "world"]
```

### Format 6 — pairs / edges

```
5 6
1 2
2 3
3 4
4 5
1 5
2 4
```

```python
n, m = map(int, input().split())
edges = []
for _ in range(m):
    u, v = map(int, input().split())
    edges.append((u, v))
```

### Format 7 — grid

```
3 3
1 0 0
0 1 0
0 0 1
```

```python
n, m = map(int, input().split())
grid = [list(map(int, input().split())) for _ in range(n)]
```

---

## Output formatting

### Print on one line, space-separated

```python
arr = [1, 2, 3, 4]
print(*arr)                  # "1 2 3 4"
# or
print(" ".join(map(str, arr)))
```

### Print on separate lines

```python
print("\n".join(map(str, arr)))
# or
for x in arr:
    print(x)
```

### Print formatted numbers

```python
x = 3.14159
print(f"{x:.2f}")            # "3.14"
print(f"{x:.4f}")            # "3.1416"

n = 42
print(f"{n:05d}")            # "00042" (zero-padded)
print(f"{n:>5d}")            # "   42" (right-aligned)
```

### Print without trailing newline

```python
print("hello", end="")       # no newline
print("hello", end=" ")      # ends with space instead
```

### Print without space between args

```python
print("hello", "world")              # "hello world"
print("hello", "world", sep="")      # "helloworld"
print("hello", "world", sep="-")     # "hello-world"
```

---

## A complete fast template (for online judges)

```python
import sys
input = sys.stdin.readline

def solve():
    n = int(input())
    arr = list(map(int, input().split()))
    # ... compute answer
    print(sum(arr))

t = int(input())
for _ in range(t):
    solve()
```

Or all-at-once style:

```python
import sys

def main():
    data = sys.stdin.read().split()
    idx = 0
    t = int(data[idx]); idx += 1

    out = []
    for _ in range(t):
        n = int(data[idx]); idx += 1
        arr = list(map(int, data[idx:idx+n])); idx += n
        out.append(str(sum(arr)))

    sys.stdout.write("\n".join(out) + "\n")

main()
```

---

## Common mistakes

### Mistake 1 — forgetting to convert to int

```python
n = input()                  # n is "5", not 5
for i in range(n):           # 💥 TypeError: range() can't take str
```

**Fix:** `n = int(input())`.

### Mistake 2 — `.split()` without unpacking properly

```python
a, b = input().split()       # a="3", b="5" — STILL strings!
print(a + b)                 # "35", not 8
```

**Fix:** `a, b = map(int, input().split())`.

### Mistake 3 — reading too few or too many lines

If the input format is "n then n lines," off-by-one in your loop count means the next test case's first line gets eaten by yours.

### Mistake 4 — `input()` after binding to `sys.stdin.readline`

`sys.stdin.readline` includes the trailing `\n`. `input()` doesn't. So if you `print(name + "!")` and `name` was read with `readline`, you get `"Alice\n!"`.

**Fix:** strip — `name = input().strip()` or `name = sys.stdin.readline().strip()`.

### Mistake 5 — print in a tight loop

```python
for x in big_list:
    print(x)                 # slow for 10⁵+ items
```

**Fix:** `print("\n".join(map(str, big_list)))`.

### Mistake 6 — leftover whitespace

`input()` returns the line minus the trailing newline. But not other whitespace. If the input has weird spacing, use `.strip()`:

```python
s = input().strip()          # remove leading/trailing whitespace
```

---

## Reading input for interactive problems

Some problems give you partial input, you compute, you print, server gives you more input, etc. (Codeforces "interactive" tag.)

```python
import sys
input = sys.stdin.readline

def query(x):
    print(x, flush=True)     # ⚠️ MUST flush
    return int(input())

# usage
result = query(42)
```

The `flush=True` is critical. Without it, your output is buffered and the server hangs.

---

## A note on Python's I/O speed

Python is slow. For 10⁶+ lines of input, even `sys.stdin` can be tight. Tricks:

1. **Read everything at once:** `data = sys.stdin.read().split()` — one syscall, no loop.
2. **Build output as a list, join once:** avoids 10⁶ `print()` calls.
3. **Avoid `int(input())` in tight loops:** `map(int, ...)` is faster.

For competitive programming, this Python template usually beats the time limit:

```python
import sys
data = sys.stdin.buffer.read().split()
idx = 0

def read_int():
    global idx
    val = int(data[idx])
    idx += 1
    return val

# use read_int() everywhere
```

`sys.stdin.buffer.read()` is the fastest possible read in Python.

---

## In an actual interview

For LeetCode-style interviews, you don't read input — the function signature gives it to you. But interviewers may ask:

> "Walk me through what your function expects. What if `nums` is empty? What if `nums[i]` is negative?"

Always handle edge cases at the top:

```python
def two_sum(nums: list[int], target: int) -> list[int]:
    if not nums or len(nums) < 2:
        return []
    ...
```

For "design a CLI" style questions, here's the minimal Python pattern:

```python
import sys

def main():
    args = sys.argv[1:]              # command-line args (excluding script name)
    for line in sys.stdin:
        line = line.strip()
        # process
        print(line.upper())

if __name__ == "__main__":
    main()
```

---

## Self-check

Write the input-reading code for these formats:

1. A single line with space-separated ints. → ?
2. n on the first line, then n lines, each containing one int. → ?
3. n m on the first line, then an n×m grid of ints. → ?
4. t test cases. Each test case has 2 lines: an int n, then an array of n ints. → ?
5. Read until EOF. → ?

(Answers:
1. `arr = list(map(int, input().split()))`
2. `n = int(input()); arr = [int(input()) for _ in range(n)]`
3. `n, m = map(int, input().split()); grid = [list(map(int, input().split())) for _ in range(n)]`
4. `t = int(input()); ...` then loop with the n-then-array pattern.
5. `for line in sys.stdin: ...`)

---

## Up next

→ [Code quality for interviews](code-quality-for-interviews.md) — naming, structure, comments, what reviewers look for.
