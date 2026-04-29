# Hash — common across all companies

> The O(1)-lookup hammer. Half of "medium" interview problems are really hash problems wearing a costume.

<span class="company-tag">Google</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">TCS</span> &nbsp; <span class="company-tag">ISRO</span> &nbsp; <span class="phase-status phase-done">Phase 14 — Common Across</span>

---

A hash table turns "did I see X?" and "how many X have I seen?" into O(1) operations — and that single ability collapses dozens of otherwise-O(n²) problems into O(n). This page collects the 15 problems that show up across **every** company's loop. If two-pointer is the most-asked technique, hashing is a close second.

## Patterns that drive these problems

| Pattern | Frequency | Where it shows up |
|---|---|---|
| Hash map for "have I seen?" | ★★★★★ | Two Sum, Contains Duplicate, Isomorphic |
| Counter / frequency map | ★★★★★ | Top K Frequent, Find All Anagrams, First Unique |
| Prefix sum + hash | ★★★★★ | Subarray Sum = K, Continuous Subarray Sum |
| Hash + linked list | ★★★★☆ | LRU Cache, Insert/Delete/GetRandom |
| Set tricks | ★★★★☆ | Longest Consecutive, Happy Number |
| Hash by canonical key | ★★★★☆ | Group Anagrams, Word Pattern, Isomorphic |

## The list (15 problems)

| # | Problem | Difficulty | Pattern | LC# |
|---|---|---|---|---|
| 1 | Two Sum | Easy | Map of complements | 1 |
| 2 | Group Anagrams | Medium | Hash by signature | 49 |
| 3 | Top K Frequent Elements | Medium | Counter + heap/bucket | 347 |
| 4 | Longest Consecutive Sequence | Medium | Set + only-start trick | 128 |
| 5 | Subarray Sum Equals K | Medium | Prefix sum + map | 560 |
| 6 | Contains Duplicate II | Easy | Map of last-index | 219 |
| 7 | Contains Duplicate III | Hard | Bucket / sorted set | 220 |
| 8 | Valid Sudoku | Medium | Set per row/col/box | 36 |
| 9 | Happy Number | Easy | Set or Floyd's | 202 |
| 10 | Isomorphic Strings | Easy | Two-way mapping | 205 |
| 11 | Word Pattern | Easy | Two-way mapping | 290 |
| 12 | First Unique Character | Easy | Counter | 387 |
| 13 | Insert Delete GetRandom O(1) | Medium | Hash + dynamic array | 380 |
| 14 | LRU Cache | Medium | Hash + doubly-linked list | 146 |
| 15 | 4Sum II | Medium | Pair-sum hashing | 454 |
| 16 | Find All Anagrams in a String | Medium | Sliding window + counter | 438 |

---

## Deep-dive 1 — Subarray Sum Equals K

The single best hash trick in the canon. The naive solution is O(n²) (try every subarray). The hash solution is O(n) and worth memorising at a *muscle* level.

??? question "Why does `prefix - k` give the count?"
    Let `P[i]` be the prefix sum after `i` elements. A subarray `(j, i]` sums to `P[i] - P[j]`. We want this to equal `k`, so `P[j] = P[i] - k`. As we sweep, we ask: "how many earlier prefixes equal `P[i] - k`?" — that's the count of subarrays ending at `i` with sum `k`. Sum the counts for every `i`.

??? question "Why is the seed `{0: 1}` mandatory?"
    To handle subarrays that **start at index 0**. If the prefix at `i` already equals `k`, we need `P[j] = 0` to be "seen once" before the loop began. Skip the seed and you'll silently miss those.

```python linenums="1"
from __future__ import annotations
from collections import defaultdict


def subarray_sum(nums: list[int], k: int) -> int:
    """Count contiguous subarrays whose sum equals k.

    Maintain a running prefix sum; for each index i, the number of
    valid subarrays ending at i is the count of earlier prefixes
    equal to (current_prefix - k).

    Time:  O(n)
    Space: O(n)
    """
    counts: dict[int, int] = defaultdict(int)
    counts[0] = 1                     # empty prefix — handles i==0 case
    prefix = 0
    answer = 0
    for x in nums:
        prefix += x
        answer += counts[prefix - k]
        counts[prefix] += 1
    return answer


# Trace: nums = [1, 1, 1], k = 2
# i=0  prefix=1  counts[-1]=0  answer=0  counts={0:1, 1:1}
# i=1  prefix=2  counts[0]=1   answer=1  counts={0:1, 1:1, 2:1}
# i=2  prefix=3  counts[1]=1   answer=2  counts={0:1, 1:1, 2:1, 3:1}
# answer = 2  (subarrays [1,1] at indices 0..1 and 1..2)
```

!!! tip "When you see 'count subarrays with sum/XOR/property X'..."
    Reach for **prefix-aggregate + hash**. It generalises beyond sums (XOR, divisibility by k, etc.).

---

## Deep-dive 2 — Longest Consecutive Sequence

Sorting gives O(n log n) trivially. The interview wants O(n). The trick: put everything in a set, then **only start counting from numbers that have no predecessor**. Each number is touched at most twice across the whole algorithm.

??? question "Why is the algorithm O(n) and not O(n²)?"
    The inner `while` only runs when `num` is the **start** of a run (no `num - 1` in the set). Across the entire input each number is visited at most once as a "starter" and at most once as part of one run. Total work: O(n).

```python linenums="1"
from __future__ import annotations


def longest_consecutive(nums: list[int]) -> int:
    """Longest run of consecutive integers in O(n).

    Build a set; for each number that is the start of a run
    (i.e. num - 1 is absent), walk the run upward and record its length.

    Time:  O(n)  amortised
    Space: O(n)
    """
    seen = set(nums)
    best = 0
    for num in seen:
        if num - 1 in seen:
            continue                  # not a starter — skip
        length = 1
        curr = num
        while curr + 1 in seen:
            curr += 1
            length += 1
        best = max(best, length)
    return best


# Example: nums = [100, 4, 200, 1, 3, 2]
# seen = {100, 4, 200, 1, 3, 2}
# Starters (no predecessor in seen): 100, 200, 1
#   start 100 -> run length 1
#   start 200 -> run length 1
#   start 1   -> 1 -> 2 -> 3 -> 4, length 4
# answer = 4
```

!!! warning "Don't iterate `for num in nums` if there are duplicates"
    `nums` may have repeats (e.g. `[1, 2, 0, 1]`); iterating the **set** avoids redoing work and avoids miscounting. Use `for num in seen`.

---

## 🃏 Cheatsheet

- **Two Sum**: one pass, store `value -> index`, ask for the complement on each new number.
- **Counter** (`collections.Counter`): one-line frequency map; pairs perfectly with `most_common(k)` for Top-K.
- **Prefix sum + hash** for "count subarrays with sum X" — seed the map with `{0: 1}` always.
- **Set + only-count-starters** for longest-consecutive style runs in O(n).
- **Two-way mapping** (`a -> b` AND `b -> a`) for isomorphic / pattern problems — one-way maps miss the `("aa", "ab")` collision.
- **Hash + DLL = LRU**. Hash + dynamic array = Insert/Delete/GetRandom O(1). Memorise both wirings.
- **Bucket sort** beats heap for Top-K Frequent when you know `k <= n` — O(n) instead of O(n log k).
- **`defaultdict(int)`** is the cleanest way to write a counter from scratch; **`Counter`** is even cleaner if you're counting an iterable.
- **Watch the seed.** Empty-prefix `{0: 1}`, fresh map `defaultdict(list)` — getting the initial state wrong is the #1 source of off-by-one bugs.
- **Hashing custom objects**: implement both `__hash__` and `__eq__`, or use `frozenset` / `tuple` for ad-hoc keys.
- **Sliding window + counter** beats hashing-the-whole-string for "find all anagrams of P in S" — keep a window-counter and a target-counter and compare.
