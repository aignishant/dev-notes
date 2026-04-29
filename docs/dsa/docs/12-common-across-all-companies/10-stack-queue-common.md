# Stack & queue — common across all companies

> Stacks turn nested structure into linear scans. Monotonic stacks turn `O(n²)` "next greater" problems into `O(n)`. This chapter is the highest leverage-per-line you'll find on the bible.

<span class="company-tag">Google</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">TCS</span> &nbsp; <span class="company-tag">ISRO</span> &nbsp; <span class="phase-status phase-done">Phase 14 — Common Across</span>

---

## 📖 Why stacks and queues are "everywhere"

Three reasons they appear in every interview track:

1. **Parsing & validation** — anything with brackets, operators, or nested structure (Valid Parentheses, Decode String, Basic Calculator) is a stack problem in disguise. TCS / ISRO love these for their clean correctness criterion.
2. **Monotonic stack** — solves the "for each element, find the next/previous greater/smaller" family in `O(n)`. Daily Temperatures, Largest Rectangle, Sum of Subarray Minimums — all the same template. Google / Meta gateposts.
3. **Stack-built primitives** — Min Stack, Queue-from-Stacks, Stack-from-Queues. Forces candidates to articulate amortised analysis, which interviewers grade explicitly.

---

## 🧩 Patterns that drive these 14

| Pattern | Frequency | Problems on this page |
|---|---|---|
| **Bracket / pair matching** | ⭐⭐⭐⭐⭐ | Valid Parentheses, Asteroid Collision |
| **Monotonic stack (next greater / smaller)** | ⭐⭐⭐⭐⭐ | Daily Temperatures, Next Greater I/II/III, Largest Rectangle, Sum of Subarray Minimums, Trap Rain Water |
| **Stack of `(state, prefix)`** | ⭐⭐⭐⭐ | Decode String, Basic Calculator |
| **Two-stack design** | ⭐⭐⭐⭐ | Min Stack, Queue from Stacks |
| **Postfix / RPN evaluation** | ⭐⭐⭐ | Evaluate RPN, Basic Calculator II |
| **Monotonic deque** | ⭐⭐⭐⭐ | Sliding Window Maximum |

---

## 📋 The 14 questions

Difficulty pills: <span class="diff-easy">Easy</span> &nbsp; <span class="diff-medium">Medium</span> &nbsp; <span class="diff-hard">Hard</span>

| # | Problem | Difficulty | Pattern | LeetCode |
|---|---|---|---|---|
| 1 | Valid Parentheses | <span class="diff-easy">Easy</span> | Bracket matching | 20 |
| 2 | Min Stack | <span class="diff-medium">Medium</span> | Auxiliary stack | 155 |
| 3 | Implement Queue using Stacks | <span class="diff-easy">Easy</span> | Two-stack amortised | 232 |
| 4 | Implement Stack using Queues | <span class="diff-easy">Easy</span> | Single-queue rotate | 225 |
| 5 | Daily Temperatures | <span class="diff-medium">Medium</span> | Monotonic decreasing | 739 |
| 6 | Next Greater Element (I / II / III) | <span class="diff-medium">Medium</span> | Monotonic stack | 496 / 503 / 556 |
| 7 | Largest Rectangle in Histogram | <span class="diff-hard">Hard</span> | Monotonic increasing | 84 |
| 8 | Trapping Rain Water (stack) | <span class="diff-hard">Hard</span> | Monotonic decreasing | 42 |
| 9 | Evaluate Reverse Polish Notation | <span class="diff-medium">Medium</span> | Operand stack | 150 |
| 10 | Basic Calculator (I / II / III) | <span class="diff-hard">Hard</span> | Stack of partial sums | 224 / 227 / 772 |
| 11 | Decode String | <span class="diff-medium">Medium</span> | Stack of `(count, prefix)` | 394 |
| 12 | Asteroid Collision | <span class="diff-medium">Medium</span> | Stack with sign rule | 735 |
| 13 | Sliding Window Maximum | <span class="diff-hard">Hard</span> | Monotonic deque | 239 |
| 14 | Sum of Subarray Minimums | <span class="diff-medium">Medium</span> | PLE / NLE monotonic | 907 |

---

## 🔬 Deep-dive 1 — Largest Rectangle in Histogram (LC 84)

> *Given bar heights, return the area of the largest axis-aligned rectangle.*

The canonical monotonic stack. Each bar's "rectangle" extends left until a strictly shorter bar, and right until a strictly shorter bar. We maintain an **increasing** stack of indices; when the current bar breaks the invariant, we pop and finalise rectangles for the popped bars.

??? question "Full solution — `largest_rectangle_area`"

    ```python linenums="1"
    from __future__ import annotations

    def largest_rectangle_area(heights: list[int]) -> int:
        """Largest rectangle area in a histogram.

        Time: O(n)   Space: O(n)
        """
        # Sentinel 0 at the end forces all remaining bars to be popped.
        heights = heights + [0]
        stack: list[int] = []   # indices, heights[stack] strictly increasing
        best = 0

        for i, h in enumerate(heights):
            # Maintain strictly-increasing invariant.
            while stack and heights[stack[-1]] > h:
                top = stack.pop()
                # The popped bar's rectangle:
                #   height = heights[top]
                #   right boundary = i (first strictly shorter bar to the right)
                #   left boundary  = stack[-1] (first strictly shorter bar to the left,
                #                              or -1 if stack empty)
                left = stack[-1] if stack else -1
                width = i - left - 1
                best = max(best, heights[top] * width)
            stack.append(i)

        return best
    ```

??? tip "Why this is `O(n)`"
    Each index is pushed exactly once and popped at most once. The inner `while` is amortised — across the whole run, total pop work is bounded by total push work, which is `n`. So the total runtime is linear despite the nested loop.

??? note "Reading off left/right boundaries"
    When we pop index `top`:
    - The bar at `i` is the **first strictly shorter bar to the right** of `top` (that's why we're popping).
    - The new top of the stack (after popping) is the **first strictly shorter bar to the left** — by the increasing invariant, every bar still in the stack has height ≤ `heights[top]`, and the one just below `top` is strictly less (otherwise `top` would have been popped first).
    - Width is `i - left - 1` — the open interval `(left, i)` has exactly that many indices.

!!! warning "Sentinel matters"
    Without the trailing `0`, bars left in the stack at the end never get popped, and you miss the rectangle that extends to the array's right edge. Equivalent alternatives: append `0` (shown), or run a final cleanup loop with `i = len(heights)`.

This same template solves **Maximal Rectangle** (LC 85, run histogram on each row's accumulated heights) and **Sum of Subarray Minimums** (LC 907, where each element's contribution is `value × (i − PLE) × (NLE − i)`).

---

## 🔬 Deep-dive 2 — Decode String (LC 394)

> *`"3[a2[c]]"` → `"accaccacc"`. Decode a string with nested `k[...]` repetitions.*

The stack stores **suspended computations**: when we hit `[`, we push the current `(repeat_count, prefix_string)` onto the stack and reset both. When we hit `]`, we pop and combine.

??? question "Full solution — `decode_string`"

    ```python linenums="1"
    from __future__ import annotations

    def decode_string(s: str) -> str:
        """Decode strings of the form k[encoded].

        Time: O(output length)
        Space: O(nesting depth + output)
        """
        stack: list[tuple[int, str]] = []   # (repeat_count, prefix_built_so_far)
        cur_str = ""
        cur_num = 0

        for ch in s:
            if ch.isdigit():
                # Multi-digit numbers: shift-and-add.
                cur_num = cur_num * 10 + int(ch)
            elif ch == "[":
                # Suspend: push the prefix and the multiplier.
                stack.append((cur_num, cur_str))
                cur_str = ""
                cur_num = 0
            elif ch == "]":
                # Resume: prepend the saved prefix, multiply current segment.
                k, prefix = stack.pop()
                cur_str = prefix + cur_str * k
            else:
                cur_str += ch

        return cur_str
    ```

??? note "What we save and why"
    At `[`, two pieces of state would otherwise be lost:
    1. The **multiplier** `k` for the segment we're about to start.
    2. The **prefix** built before `[` — siblings or characters at the outer level.

    Pushing `(k, prefix)` lets us reset both `cur_num` and `cur_str` to start fresh on the inner segment. At `]`, we close that segment by computing `cur_str * k` and re-attaching it after the saved prefix.

    Trace `"3[a2[c]]"`:

    | char | stack | cur_num | cur_str |
    |---|---|---|---|
    | `3` | `[]` | 3 | `""` |
    | `[` | `[(3, "")]` | 0 | `""` |
    | `a` | `[(3, "")]` | 0 | `"a"` |
    | `2` | `[(3, "")]` | 2 | `"a"` |
    | `[` | `[(3, ""), (2, "a")]` | 0 | `""` |
    | `c` | `[(3, ""), (2, "a")]` | 0 | `"c"` |
    | `]` | `[(3, "")]` | 0 | `"a" + "c"*2 = "acc"` |
    | `]` | `[]` | 0 | `"" + "acc"*3 = "accaccacc"` |

The same `(state, prefix)` stack pattern solves **Basic Calculator I/II/III** (where state is `(sign, accumulated_value)`), **Mini Parser** (LC 385), and **Number of Atoms** (LC 726).

---

## 🃏 Cheatsheet

- **Use a list as a stack** in Python — `append` / `pop` are `O(1)`. `collections.deque` is for queues / monotonic deques.
- **Bracket matching** — push openers, pop on closers, check match. Empty stack at end ⇒ valid.
- **Min Stack** — store `(value, current_min)` tuples on the same stack, or use a parallel min-stack.
- **Queue from two stacks** — push onto `in_stack`; on pop/peek, transfer to `out_stack` only when `out_stack` is empty. Each element moves at most twice ⇒ amortised `O(1)`.
- **Monotonic increasing stack** — pop when current ≤ top. Use for "previous greater", "next greater" (scan reverse).
- **Monotonic decreasing stack** — pop when current ≥ top. Use for "previous smaller", "next smaller".
- **Largest rectangle / subarray minimums** — sentinel `0` (or `-inf` / `+inf`) at the end forces final flushing. Don't forget it.
- **Next greater in circular array (LC 503)** — iterate `2n` times with `i % n` indexing; only push during the first pass, only resolve during both passes.
- **Decode String / Calculator** — `(state, prefix)` stack. Push on `[` / `(`, pop on `]` / `)`, multiply / sign-flip in between.
- **Asteroid Collision** — push positives directly. On a negative, pop while top is positive and smaller; if equal, also pop the top; if a larger positive remains, drop the negative.
- **RPN evaluation** — operand stack only; on operator, pop right then left, push result. Beware Python's `int(-3 / 2)` rounding — use `int(a / b)` (truncation toward zero), not `a // b` (floor).
- **Basic Calculator** — handle `+ −` with running sum + sign; handle `× ÷` with a stack that lazily multiplies the top; handle parentheses by recursing or pushing `(running, sign)`.
- **Sliding Window Maximum** — monotonic decreasing deque of indices. Front = current max; pop front when out of window; pop back while smaller than incoming.
- **Edge cases**: empty input, single element, all increasing, all decreasing, deeply nested brackets, mismatched brackets, multi-digit numbers.
- **When stack/queue isn't enough**: random access mid-computation (use a list), or non-LIFO/non-FIFO ordering (use a heap, sorted set, or balanced BST).
