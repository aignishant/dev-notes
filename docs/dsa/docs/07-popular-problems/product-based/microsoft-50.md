# Microsoft — 50 most-asked questions

> The 50 problems Microsoft (Azure, Office, Windows, Bing, GitHub, LinkedIn, Xbox) has asked most often, with the patterns behind them and what the interviewer is grading. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">Microsoft</span> &nbsp; <span class="phase-status phase-inprogress">Phase 8 — company page</span>

---

## 📖 How this page is organized

1. **What interviewing here is like** — rounds, format, signal, vibe.
2. **What this company tests** — the specific skills they grade for.
3. **Common patterns** — which of the 20 patterns show up most often.
4. **The 50 questions** — grouped by topic.
5. **Deep-dives** — 3 representative problems in mini-v3 format.
6. **Day-of tips**.

---

## 🏢 What interviewing at Microsoft is like

### Rounds (typical SDE / SDE II onsite — 2026)

| Round | Length | Focus |
|---|---|---|
| **Online assessment** | 75 min | 2 medium coding problems. CodeSignal / HackerRank. |
| **Phone screen** | 45-60 min | One coding + a short OOP / system question. Teams + shared editor. |
| **Onsite — coding ×2** | 60 min each | Coding-heavy. Often **OOP design** flavor in one of them. |
| **Onsite — system design** | 60 min | SDE II+. Azure-flavored for some teams. |
| **Onsite — "as appropriate"** | 60 min | Wildcard: deeper coding, debugging, or technical project deep-dive. |
| **Onsite — hiring manager** | 45-60 min | Behavioral + project deep-dive. |

### What "the Microsoft style" actually means

- **Less leetcode-y than Google/Meta**. More OOP-style design problems ("design a parking lot", "design a deck of cards"), more debugging existing code.
- **They love "what would you change about this code?"** — Microsoft uses mid-level code review as a signal even in SWE rounds.
- **Project deep-dive matters.** Be ready to whiteboard the architecture of your most recent project. They will go *3 levels deep*.
- **Calm under pressure.** Microsoft interviewers are typically less aggressive than Meta/Amazon. Don't mistake niceness for low rigor — they take notes.
- **Teams-specific**: Azure/cloud teams ask infra-flavored questions; Office team asks doc/format problems; Bing team asks ranking/search.

!!! tip "The Microsoft interviewer mindset"
    Microsoft interviewers ask: *"Could this person ship a feature in our codebase next week?"* — practical, not theoretical. They prefer working medium-complex code over elegant-but-incomplete.

---

## 🎯 What Microsoft tests

| Signal | Where they grade it | How to show it |
|---|---|---|
| **Coding correctness** | All coding rounds | Working code in 30 min, test cases included. |
| **OOP / design fluency** | One coding round | Class hierarchies, interface design, SOLID violations. |
| **Debugging instinct** | "As appropriate" round | Read someone else's code, find the bug, propose a fix. |
| **Project ownership** | Hiring manager round | Be ready for "what was *your* contribution?" 3 layers deep. |
| **Communication** | Every round | Walk through your reasoning. Microsoft *especially* values clarity. |
| **Cross-team thinking** | System design + behavioral | "How would Office's team integrate this?" — show Microsoft-the-org awareness. |

---

## 🧩 Patterns that show up most often

| Pattern | Frequency | Why Microsoft likes it |
|---|---|---|
| **Trees / recursion** | ⭐⭐⭐⭐⭐ | Their bread and butter. Especially BST + tree-with-parent variants. |
| **OOP design** | ⭐⭐⭐⭐⭐ | "Design X" problems are a Microsoft signature. |
| **Hash map composition** | ⭐⭐⭐⭐ | Standard medium filter. |
| **Linked list manipulation** | ⭐⭐⭐⭐ | Classic Microsoft territory — reverse, merge, intersect. |
| **DP** | ⭐⭐⭐⭐ | More than Meta, less than Google. |
| **Graphs** | ⭐⭐⭐ | Topological sort, BFS / DFS. |
| **Sliding window** | ⭐⭐⭐ | String problems mostly. |
| **Backtracking** | ⭐⭐⭐ | Word search, permutations, combinations. |
| **Bit manipulation** | ⭐⭐⭐ | Microsoft loves bit tricks more than most. |

---

## 📋 The 50 questions

Status: ✅ = full v3 in this bible &nbsp; 📝 = mini-v3 below &nbsp; 🚧 = lands later in Phase 8.

### Arrays & strings (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash map | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Reverse Words in a String | <span class="diff-medium">Medium</span> | In-place reversal | 🚧 |
| 3 | String to Integer (atoi) | <span class="diff-medium">Medium</span> | State machine | 🚧 |
| 4 | Spiral Matrix | <span class="diff-medium">Medium</span> | Layer-by-layer | 🚧 |
| 5 | Set Matrix Zeroes | <span class="diff-medium">Medium</span> | In-place markers | 🚧 |
| 6 | Rotate Image | <span class="diff-medium">Medium</span> | Transpose + reverse | 🚧 |
| 7 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 8 | Valid Palindrome | <span class="diff-easy">Easy</span> | Two pointers | 🚧 |
| 9 | Group Anagrams | <span class="diff-medium">Medium</span> | Hash + sorted-key | 🚧 |
| 10 | Excel Sheet Column Title | <span class="diff-easy">Easy</span> | Base-26 conversion | 🚧 |

### Linked lists (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 11 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 12 | Merge Two Sorted Lists | <span class="diff-easy">Easy</span> | Two pointers | 🚧 |
| 13 | Add Two Numbers | <span class="diff-medium">Medium</span> | Carry + dummy head | 🚧 |
| 14 | Linked List Cycle | <span class="diff-easy">Easy</span> | Floyd's tortoise + hare | 🚧 |
| 15 | Copy List with Random Pointer | <span class="diff-medium">Medium</span> | Hash / interleave | 🚧 |

### Trees (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 16 | Binary Tree Inorder Traversal | <span class="diff-easy">Easy</span> | Iterative + stack | 🚧 |
| 17 | Validate BST | <span class="diff-medium">Medium</span> | DFS + bounds | 🚧 |
| 18 | Lowest Common Ancestor (BST) | <span class="diff-medium">Medium</span> | DFS recursion | 🚧 |
| 19 | Lowest Common Ancestor (Binary Tree) | <span class="diff-medium">Medium</span> | DFS post-order | 🚧 |
| 20 | Convert Sorted Array to BST | <span class="diff-easy">Easy</span> | Recursive midpoint | 🚧 |
| 21 | Populating Next Right Pointers | <span class="diff-medium">Medium</span> | BFS / level pointers | 🚧 |
| 22 | Diameter of Binary Tree | <span class="diff-easy">Easy</span> | DFS post-order | 🚧 |
| 23 | Binary Tree Maximum Path Sum | <span class="diff-hard">Hard</span> | DFS post-order | 🚧 |
| 24 | Serialize / Deserialize Binary Tree | <span class="diff-hard">Hard</span> | DFS + queue | 🚧 |
| 25 | Construct Tree from Preorder + Inorder | <span class="diff-medium">Medium</span> | Recursive partition | 🚧 |

### Graphs (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 26 | Number of Islands | <span class="diff-medium">Medium</span> | Grid BFS/DFS | 🚧 |
| 27 | Course Schedule | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 28 | Clone Graph | <span class="diff-medium">Medium</span> | DFS + hash | 🚧 |
| 29 | Word Ladder | <span class="diff-hard">Hard</span> | BFS on word graph | 🚧 |

### DP (6)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 30 | Climbing Stairs | <span class="diff-easy">Easy</span> | 1D DP | 🚧 |
| 31 | Maximum Subarray (Kadane's) | <span class="diff-medium">Medium</span> | DP | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 32 | Longest Increasing Subsequence | <span class="diff-medium">Medium</span> | Patience / DP | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 33 | Word Break | <span class="diff-medium">Medium</span> | DP + dictionary | 🚧 |
| 34 | Edit Distance | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |
| 35 | Best Time to Buy and Sell Stock | <span class="diff-easy">Easy</span> | Running min | [✅](../../02-data-structures/arrays/01-array-basics.md) |

### Bit manipulation (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 36 | Single Number | <span class="diff-easy">Easy</span> | XOR | [✅](../../04-patterns/20-bitwise-xor.md) |
| 37 | Number of 1 Bits | <span class="diff-easy">Easy</span> | n & (n-1) | 🚧 |
| 38 | Reverse Bits | <span class="diff-easy">Easy</span> | Bit-by-bit shift | 🚧 |

### Stacks / queues (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 39 | Valid Parentheses | <span class="diff-easy">Easy</span> | Stack | 🚧 |
| 40 | Min Stack | <span class="diff-medium">Medium</span> | Two stacks | [📝](#deep-dive-2-min-stack) |
| 41 | Implement Queue using Stacks | <span class="diff-easy">Easy</span> | Two stacks | 🚧 |

### Backtracking (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 42 | Combinations | <span class="diff-medium">Medium</span> | Backtracking | 🚧 |
| 43 | Permutations | <span class="diff-medium">Medium</span> | Backtracking + swap | 🚧 |
| 44 | Word Search | <span class="diff-medium">Medium</span> | Grid DFS + backtrack | 🚧 |

### Design / OOP (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 45 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |
| 46 | Design Tic-Tac-Toe | <span class="diff-medium">Medium</span> | Row/col/diag counters | [📝](#deep-dive-3-design-tic-tac-toe) |
| 47 | Design Hit Counter | <span class="diff-medium">Medium</span> | Circular buffer | 🚧 |
| 48 | Implement Trie (Prefix Tree) | <span class="diff-medium">Medium</span> | Trie | [✅](../../05-advanced/01-tries.md) |

### Misc (2)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 49 | Pow(x, n) | <span class="diff-medium">Medium</span> | Fast exponentiation | [📝](#deep-dive-1-powx-n) |
| 50 | Sqrt(x) | <span class="diff-easy">Easy</span> | Binary search | 🚧 |

---

## 🔬 Deep-dives — 3 Microsoft-style walkthroughs

These three are picked because:

- **Pow(x, n)** is asked at Microsoft *constantly* — and the recursive halving trick is exactly the kind of "did you really learn this in school?" filter they love.
- **Min Stack** showcases the OOP-design + clever-data-structure combo Microsoft prizes.
- **Design Tic-Tac-Toe** is the canonical Microsoft "make this O(1) per move" optimization problem.

---

### Deep-dive 1: Pow(x, n)

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Microsoft</span>

> Implement `pow(x, n)` — `x` is a double, `n` is an int (can be negative).

#### 📖 Story mode

You can't just call `**` (the interviewer will say "implement it"). The naive `for _ in range(n): result *= x` is `O(n)` — for `n = 2³¹` that's a billion multiplies. There's a `O(log n)` way.

#### 🧠 Thinking process

- **Insight**: `x²ᵏ = (x²)ᵏ`. So `x¹⁰ = (x²)⁵ = (x²) · (x²)⁴ = (x²) · ((x²)²)²`. Each squaring halves the exponent — `log n` steps.
- **Negative n**: compute `pow(1/x, -n)`. Watch for `n = -2³¹` overflow (Python ints don't overflow but be explicit).

#### 🐍 Optimal solution

```python
def my_pow(x: float, n: int) -> float:
    """Compute x ** n in O(log |n|) by binary exponentiation."""
    if n < 0:
        x, n = 1 / x, -n

    result = 1.0
    while n > 0:
        if n & 1:           # odd: multiply current x into result
            result *= x
        x *= x              # square the base
        n >>= 1             # halve the exponent

    return result
```

**Why iterative, not recursive?** Avoids Python's recursion depth limit at large `n`. Same complexity, no stack risk.

#### 🔍 Dry run on `x=2, n=10`

| n (binary) | x | result |
|---|---|---|
| 1010 | 2 | 1 |
| 101 (n>>1=5) | 4 (=2²) | 1 (bit was 0 — skip) |
| 10 | 16 (=4²) | 4 (bit was 1 — multiply) |
| 1 | 256 (=16²) | 4 (bit was 0 — skip) |
| 0 | — | 1024 (bit was 1 — multiply) |

`2¹⁰ = 1024`. ✅

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **Binary exp** | O(log \|n\|) | O(1) |

#### 🔄 Microsoft's classic follow-up

??? question "What about `pow(x, n) mod m`?"
    Modular binary exp: `result = (result * x) % m; x = (x * x) % m`. Identical structure. This is the engine behind RSA.

??? question "How would you handle `pow(matrix, n)`?"
    Same algorithm, with matrix multiplication instead of scalar. Solves Fibonacci in `O(log n)` and many linear-recurrence DPs.

??? question "What if `x` is very close to 1 and `n` is huge?"
    Use `exp(n * log(x))` for floating-point speed, but be aware of catastrophic cancellation. Binary exp gives more bits of precision when `x ≈ 1`.

#### 🐛 Common bugs

- Treating `n = -2147483648` naively — `-n` overflows in C/Java; in Python it's fine, but mention you'd `n = -n` after promoting to long.
- Forgetting `if n & 1` — that's how the algorithm picks which powers to multiply.

---

### Deep-dive 2: Min Stack

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Microsoft</span> &nbsp; <span class="company-tag">Amazon</span>

> Design a stack supporting `push(x)`, `pop()`, `top()`, and `getMin()` — all in O(1).

#### 📖 Story mode

A normal stack lets you peek at the top in O(1) — but the *minimum*? That'd be O(n) without help. Trick: maintain a parallel stack tracking the running min.

#### 🧠 Thinking process

- **Naive**: scan whole stack on `getMin()` — O(n). Fail.
- **Insight**: at every `push(x)`, the min for the *current* stack is `min(x, previous_min)`. Push that on a "min stack" too. Pop both together.
- **Optimization**: if `x > current min`, you don't *need* to push to min-stack. But push the same min value onto it (slight space cost) for code simplicity.

#### 🐍 Optimal solution

```python
class MinStack:
    def __init__(self) -> None:
        self.stack: list[int] = []
        self.mins: list[int] = []      # mins[i] = min of stack[0..i]

    def push(self, x: int) -> None:
        self.stack.append(x)
        self.mins.append(min(x, self.mins[-1]) if self.mins else x)

    def pop(self) -> None:
        self.stack.pop()
        self.mins.pop()

    def top(self) -> int:
        return self.stack[-1]

    def getMin(self) -> int:
        return self.mins[-1]
```

**Invariant**: `mins[i]` is always the minimum of `stack[0..i]`. Push and pop maintain that in O(1).

#### 🔍 Dry run

`push(3) push(5) push(2) push(1) getMin() pop() getMin()`

| op | stack | mins | result |
|---|---|---|---|
| push(3) | [3] | [3] | — |
| push(5) | [3,5] | [3,3] | — |
| push(2) | [3,5,2] | [3,3,2] | — |
| push(1) | [3,5,2,1] | [3,3,2,1] | — |
| getMin() | — | — | 1 |
| pop() | [3,5,2] | [3,3,2] | — |
| getMin() | — | — | 2 |

#### ⏱️ Complexity

| Op | Time | Space |
|---|---|---|
| All four | O(1) | O(n) |

#### 🔄 Microsoft's classic follow-up

??? question "Reduce space — only push to mins when the new element is ≤ current min."
    Yes — saves space for non-monotonic inputs. On pop, only pop from mins if the popped value equals `mins[-1]`. Slightly trickier; mention as the optimization.

??? question "Now design a Max-Frequency Stack — `pop()` returns the most frequent element."
    Use a freq map `freq[x] = count`, plus a list of stacks `groups[f]` holding elements at frequency `f`, plus `maxFreq`. `push(x)`: increment freq, push to `groups[freq[x]]`, update maxFreq. `pop()`: pop from `groups[maxFreq]`, decrement freq, decrement maxFreq if `groups[maxFreq]` is empty. (LC 895.)

#### 🐛 Common bugs

- Forgetting to pop from `mins` on `pop()` — the invariant breaks immediately.
- Using `min()` over the whole stack — that's the naive O(n).

---

### Deep-dive 3: Design Tic-Tac-Toe

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Microsoft</span>

> Design `move(row, col, player)` for an `n×n` Tic-Tac-Toe. Each `move` returns 0 (continue), 1 (player 1 wins), or 2 (player 2 wins). Goal: O(1) per move.

#### 📖 Story mode

Naive: re-check the whole row, column, both diagonals after every move. O(n) per move. For `n = 1000` and `n²` moves, that's `O(n³)` — too slow. Goal: O(1) per move via running counts.

#### 🧠 Thinking process

- **Per-row count**: track how many marks player 1 has in each row, vs player 2. When either hits `n`, that player wins.
- **Encoding**: use `+1` for player 1, `-1` for player 2. A row's count hits `+n` → P1 wins; `-n` → P2 wins. Same for columns and the two diagonals.
- **Now O(1) per move** — only update 1 row, 1 col, and (if applicable) 1 or 2 diagonals.

#### 🐍 Optimal solution

```python
class TicTacToe:
    def __init__(self, n: int) -> None:
        self.n = n
        self.rows = [0] * n
        self.cols = [0] * n
        self.diag = 0           # main diagonal (row == col)
        self.anti = 0           # anti-diagonal (row + col == n - 1)

    def move(self, row: int, col: int, player: int) -> int:
        delta = 1 if player == 1 else -1
        target = self.n if player == 1 else -self.n

        self.rows[row] += delta
        self.cols[col] += delta
        if row == col:
            self.diag += delta
        if row + col == self.n - 1:
            self.anti += delta

        if (self.rows[row] == target or self.cols[col] == target
                or self.diag == target or self.anti == target):
            return player
        return 0
```

**The +1 / -1 encoding** is what makes this elegant — it conflates "did P1 win this row?" and "did P2 win this row?" into one counter per row.

#### 🔍 Dry run on `n=3`

`move(0,0,1) move(0,1,2) move(1,1,1) move(0,2,2)` — P2 wins top row.

| call | rows | cols | diag | anti | result |
|---|---|---|---|---|---|
| move(0,0,1) | [1,0,0] | [1,0,0] | 1 | 0 | 0 |
| move(0,1,2) | [0,0,0] | [1,-1,0] | 1 | -1 | 0 |
| move(1,1,1) | [0,1,0] | [1,0,0] | 2 | 0 | 0 |
| move(0,2,2) | [-1,0,0] | [1,0,-1] | 2 | -1 | 0 |

Hmm — answer is 0 each step (P2 needs 3-in-row but only has 2). Continuing:

`move(2,1,2)`: rows=[-1,0,-1], cols=[1,-2,-1], diag=2, anti=-1 → still 0.

The trace is illustrative — the *mechanism* is what matters, and it's O(1) per move.

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| `move` | O(1) | O(n) |
| Total | — | O(n) for n×n board |

#### 🔄 Microsoft's classic follow-up

??? question "Now make it support 4-in-a-row Connect-Four-style?"
    Replace the per-row counter with running streaks of consecutive same-player moves per row/col/diag. On each move, recompute *only* the relevant streak — still O(1) since the streak length is bounded by the win condition.

??? question "What about Gomoku (5-in-row on 19×19)?"
    Same idea — track running streaks. Or fall back to checking only the four directions through the just-placed piece — O(streak length) per move.

#### 🐛 Common bugs

- Returning 1 / 2 only on `==` — yes correct, but if you allow a move on an already-occupied cell the counter inflates and corrupts. Add an "is cell free?" guard for production.
- Missing the anti-diagonal check.

---

## 🗓️ Day-of tips for a Microsoft interview

!!! tip "The morning checklist"
    1. **Review your most recent project** at 3 levels of depth — be ready for "why did you pick X over Y?"
    2. **One easy + one OOP design** warm-up. Microsoft loves design.
    3. **Practice debugging** — read 50-line code samples, find the bug. (LC has a small "debug" problem set.)
    4. **Test Teams + your IDE** the night before.

### During the interview

| Stage | What to say / do |
|---|---|
| **First 60 seconds** | Restate. Ask 2 clarifying Qs. State approach. |
| **Pre-coding (~5 min)** | Sketch the class hierarchy or function signature **before** typing. |
| **Coding (~25 min)** | Narrate. Type clean. Add type hints + docstrings — Microsoft *notices*. |
| **Testing (~5 min)** | One example + one edge case. |
| **OOP follow-up** | If they ask "now make this extensible", talk through the **interface** before changing code. |
| **Project deep-dive** | Be ready for *3 levels* of "why did you choose X?" Have your tradeoff reasoning rehearsed. |

### Red & green flags

- 🚩 Skipping clarifying questions — Microsoft notes silence.
- 🚩 Not testing your code — they wait for you to ask "can I run an example?"
- 🚩 Inability to defend your project's design choices.
- 🟢 Cleanly factored helpers + type hints + docstrings.
- 🟢 Volunteering a class diagram before typing code.
- 🟢 Explaining a tradeoff *and* its cost.

---

## 🔁 Where to go from here

- **Solve the 50** in roughly the order above.
- **Cross-check** with the [Top 100 by Pattern](../top-100-by-pattern.md).
- **System design** — start with [URL Shortener](../../08-system-design/index.md). Microsoft's Azure-flavored design problems land in Phase 9.
- **OOP / LLD** prep at [Low-Level Design](../../09-low-level-design/index.md).

> Same six-part shape as [Google 50](google-50.md), [Meta 50](meta-50.md), and [Amazon 50](amazon-50.md).
