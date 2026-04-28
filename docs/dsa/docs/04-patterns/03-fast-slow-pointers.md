# Fast & Slow Pointers

> Two pointers walking the same sequence at **different speeds**. The slow pointer moves one step at a time; the fast pointer moves two. This simple speed differential is enough to detect cycles, find midpoints, find loop starts, and check periodicity — all in O(n) time and **O(1) space**. Also called **Floyd's Tortoise and Hare** (cycle detection version).

---

## 📖 What is the fast & slow pointers pattern?

You've got a structure you can walk forward (linked list, sequence under a function `f`, integer with digit transformations). You start two pointers at the head; one moves one step per tick, the other two. **If a cycle exists, the fast pointer will eventually lap the slow one and meet it. If no cycle exists, the fast pointer reaches the end first.**

The pattern is a member of the [Two Pointers family](02-two-pointers.md), but it's important enough — and asked in enough distinct ways — to deserve its own page.

!!! tip "The signal — when to reach for fast & slow"
    Reach for it when:

    - The problem mentions **"cycle"**, **"loop"**, **"infinite"**, or **"fixed point"**.
    - You need to find the **middle** of a linked list in one pass.
    - You're walking a sequence under a deterministic function `f(x)` and asking *whether it terminates*.
    - You need O(1) extra space — a hash set of visited nodes / values is the obvious O(n)-space alternative.
    - The structure is **non-indexable** (linked list, function-iteration) — you can't binary-search or jump.

    If the structure supports random access and you don't care about space, a hash set is simpler. Reach for fast/slow when memory matters.

---

## 🧩 The three flavors

### Flavor 1: Cycle detection (Floyd's Tortoise and Hare)

Walk both pointers from the head. If they ever meet, there's a cycle. If `fast` hits `None` (or the end), there isn't.

```python
def has_cycle(head) -> bool:
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False
```

**Why it works:** if a cycle of length `C` exists, `fast` gains 1 step per tick on `slow`. After at most `C` ticks inside the cycle, `fast` catches up.

**Examples:** Linked List Cycle, Happy Number, Find Duplicate Number.

### Flavor 2: Find the cycle entry (after detection)

Once `slow` and `fast` meet, reset one to the head and walk both at speed 1. They meet at the cycle's entry. (Floyd's classic insight.)

```python
def cycle_start(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            break
    else:
        return None                        # no cycle

    # Phase 2: reset slow, walk both at speed 1
    slow = head
    while slow is not fast:
        slow = slow.next
        fast = fast.next
    return slow
```

**Why it works:** if the head-to-cycle distance is `a` and the meeting-point-to-entry distance (going forward inside the cycle) is also `a`, then a fresh pointer from head and the meeting-point pointer will collide at the entry. The math is in the deep-dive below.

**Examples:** Linked List Cycle II (find start node), Find Duplicate Number (treats array as functional graph).

### Flavor 3: Find the middle / k-from-end

Same speed differential, but the goal is *position*, not collision.

```python
def find_middle(head):
    """For odd length: the middle. For even: the second of the two middles."""
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow
```

When `fast` finishes, `slow` has covered half the distance — exactly the middle.

**Examples:** Middle of the Linked List, Palindrome Linked List, Reorder List.

---

## ⚡ Why is this O(n)?

For non-cycle traversals: `fast` covers at most n steps; the loop runs at most n/2 iterations.

For cycle detection: let the cycle have length `C` and tail length `T` (head to cycle entry). After `T` ticks, both pointers are inside the cycle. From there, `fast` gains 1 per tick on `slow`. They meet within `C` more ticks. Total: `T + C ≤ n` iterations → **O(n) time, O(1) space**.

The hash-set alternative (mark every node visited; if you see one twice, cycle) is also O(n) time but **O(n) space**. Fast/slow trades cleverness for memory.

!!! warning "Common confusion"
    Fast/slow pointers vs general two-pointers:
    
    - **Two pointers**: pointers move at the same speed but in different directions, or in different arrays.
    - **Fast/slow**: pointers move in the *same* direction at *different* speeds. The speed differential is the key.
    
    Both are O(n) two-index techniques, but they exploit different structural properties.

---

## 🔬 The 7 sub-patterns

Every fast/slow problem reduces to one of these:

| # | Sub-pattern | Goal | Example problem |
|---|---|---|---|
| 1 | **Cycle detection (boolean)** | Yes/no there's a cycle | Linked List Cycle |
| 2 | **Cycle entry (locate)** | Where does the cycle start? | Linked List Cycle II |
| 3 | **Cycle length** | How many nodes are in the cycle? | Custom variant |
| 4 | **Find middle** | n/2-th node | Middle of the Linked List |
| 5 | **Functional iteration** | Cycle in `x → f(x)` | Happy Number, Find Duplicate |
| 6 | **k-from-end** | Two pointers k apart, walk together | Remove Nth from End |
| 7 | **Palindrome via half-reverse** | Find middle, reverse half, compare | Palindrome Linked List |

Master these 7 mechanisms and you've solved every interview fast/slow problem.

---

## 📋 The 20 problems

Difficulty pill conventions:

- <span class="diff-easy">Easy</span> &nbsp; <span class="diff-medium">Medium</span> &nbsp; <span class="diff-hard">Hard</span>

Status:

- ✅ = full v3 solution exists in this bible (link given)
- 📝 = covered in mini-v3 below
- 🚧 = lands in Phase 5 (full v3 solutions for every pattern problem)

### Cycle detection — boolean (3)

| # | Problem | Difficulty | Sub-pattern | Status |
|---|---|---|---|---|
| 1 | Linked List Cycle | <span class="diff-easy">Easy</span> | Cycle detection | [✅](../02-data-structures/linked-lists/01-linked-list-basics.md#problem-3-linked-list-cycle) |
| 2 | Happy Number | <span class="diff-easy">Easy</span> | Functional iteration | [✅](../02-data-structures/hash-tables/01-hash-table-basics.md#problem-5-happy-number) |
| 3 | Circular Array Loop | <span class="diff-medium">Medium</span> | Functional iteration | 🚧 |

### Cycle localization (4)

| # | Problem | Difficulty | Sub-pattern | Status |
|---|---|---|---|---|
| 4 | Linked List Cycle II (entry) | <span class="diff-medium">Medium</span> | Cycle entry | [✅](../02-data-structures/linked-lists/01-linked-list-basics.md#problem-16-linked-list-cycle-ii-start-of-the-cycle) |
| 5 | Find the Duplicate Number | <span class="diff-medium">Medium</span> | Functional iteration | [✅](../02-data-structures/arrays/01-array-basics.md#problem-26-find-the-duplicate-number) |
| 6 | Cycle length (variant) | <span class="diff-medium">Medium</span> | Cycle length | [📝](#deep-dive-1-detect-cycle-and-find-its-length) |
| 7 | Find Common Suffix of Two Lists | <span class="diff-easy">Easy</span> | Two-pointer length-align | 🚧 |

### Find middle / k-from-end (5)

| # | Problem | Difficulty | Sub-pattern | Status |
|---|---|---|---|---|
| 8 | Middle of the Linked List | <span class="diff-easy">Easy</span> | Find middle | [✅](../02-data-structures/linked-lists/01-linked-list-basics.md#problem-4-middle-of-the-linked-list) |
| 9 | Palindrome Linked List | <span class="diff-easy">Easy</span> | Half-reverse | [✅](../02-data-structures/linked-lists/01-linked-list-basics.md#problem-6-palindrome-linked-list) |
| 10 | Reorder List | <span class="diff-medium">Medium</span> | Half-reverse + interleave | [✅](../02-data-structures/linked-lists/01-linked-list-basics.md#problem-12-reorder-list) |
| 11 | Remove Nth Node From End | <span class="diff-medium">Medium</span> | k-from-end | [✅](../02-data-structures/linked-lists/01-linked-list-basics.md#problem-5-remove-nth-node-from-end-of-list) |
| 12 | Rotate List | <span class="diff-medium">Medium</span> | k-from-end + rewire | [✅](../02-data-structures/linked-lists/01-linked-list-basics.md#problem-14-rotate-list) |

### Functional iteration / number theory (3)

| # | Problem | Difficulty | Sub-pattern | Status |
|---|---|---|---|---|
| 13 | Linked List Random Node (reservoir) | <span class="diff-medium">Medium</span> | Length pass | [✅](../02-data-structures/linked-lists/01-linked-list-basics.md#problem-10-linked-list-random-node-reservoir-sampling) |
| 14 | Squares Eventually Reach 1? (Happy variant) | <span class="diff-easy">Easy</span> | Functional iteration | [📝](#deep-dive-2-happy-number-with-floyd) |
| 15 | Detect Stuck Loop in Sequence | <span class="diff-medium">Medium</span> | Periodicity | 🚧 |

### Linked-list utilities (5)

| # | Problem | Difficulty | Sub-pattern | Status |
|---|---|---|---|---|
| 16 | Sort List (merge sort using middle-find) | <span class="diff-medium">Medium</span> | Find middle | [✅](../02-data-structures/linked-lists/01-linked-list-basics.md#problem-17-sort-list-merge-sort) |
| 17 | Convert Sorted List to BST | <span class="diff-medium">Medium</span> | Find middle | [✅](../02-data-structures/linked-lists/01-linked-list-basics.md#problem-25-convert-sorted-list-to-bst) |
| 18 | Intersection of Two Linked Lists | <span class="diff-easy">Easy</span> | Length-align | [✅](../02-data-structures/linked-lists/01-linked-list-basics.md#problem-7-intersection-of-two-linked-lists) |
| 19 | Split Linked List in Parts | <span class="diff-medium">Medium</span> | Length pass | 🚧 |
| 20 | Find Length & Last Node | <span class="diff-easy">Easy</span> | One-pass length | 🚧 |

---

## 🔬 Deep-dives — 3 templates that cover everything

Picked because:

- **#1 Detect cycle and find its length** demonstrates the **basic Floyd's** flavor — the textbook starting point.
- **#2 Happy Number with Floyd** demonstrates the **functional-iteration** application — same pattern on integers instead of nodes.
- **#3 Find Cycle Start (LC 142)** demonstrates the **two-phase Floyd's** with the clever math that lands you at the entry.

Master these three and you've handled every fast/slow application.

Format: thinking process → optimal solution → dry run → complexity → variants.

---

### Deep-dive 1: Detect cycle and find its length

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Everyone</span>

> Given a linked list, return `True` if it contains a cycle, and if so, the length of the cycle. (Composite of LC 141 + cycle-length follow-up.)

#### 📖 Story mode

A train running on a track with a possible loop section. Two passengers walk forward — one slow, one fast. If the track loops, they'll meet somewhere on the loop section. Once met, the slow walker can lap the loop alone and count steps to measure its circumference.

#### 🧠 Thinking process

- **Brute force**: maintain a hash set of visited nodes. O(n) time, O(n) space. Cycle length = `index_of_repeat − index_first_seen`.
- **Insight (Floyd's)**: walk `slow` 1 step, `fast` 2 steps per tick. Inside a cycle, `fast` gains 1 step on `slow` per tick. They will meet within `C` ticks (cycle length). After meeting, freeze `slow`; walk `fast` alone until it returns — that's `C`.

The two-phase approach is the canonical way to extract structural info (length, entry) without allocating memory.

#### 🐍 Optimal solution

```python
def cycle_with_length(head) -> tuple[bool, int]:
    """Return (has_cycle, cycle_length). cycle_length=0 if no cycle."""
    slow = fast = head
    # Phase 1: detect
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            break
    else:
        return (False, 0)

    # Phase 2: measure
    length = 1
    fast = fast.next
    while fast is not slow:
        fast = fast.next
        length += 1
    return (True, length)
```

#### 🔍 Dry run on a cycle of length 4 with a 2-node tail (`a → b → c → d → e → c`)

Phase 1:

| tick | slow | fast | meet? |
|---|---|---|---|
| 0 | a | a | (start) |
| 1 | b | c | no |
| 2 | c | e | no |
| 3 | d | d | **yes**, break |

Phase 2 (slow stays at `d`, fast advances):

| step | fast | length |
|---|---|---|
| 0 | e | 1 |
| 1 | c | 2 |
| 2 | d | 3 (matches slow) → done |

Wait — that gave length 3, but the cycle is `c → d → e → c` which is 3 nodes. Let me recount: `c → d → e → c` has 3 edges, 3 distinct nodes — cycle length 3. ✓

Re-examining the original example: I claimed "cycle of length 4" but `c → d → e → c` is 3 nodes. Cycle *length* is conventionally the number of nodes (or edges) in the loop — pick one and stick with it. The algorithm counts edges traversed by `fast` until it returns; that's the same as node count for a simple cycle.

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| Hash set | O(n) | O(n) |
| **Floyd's** | **O(n)** | **O(1)** |

Phase 1: at most `T + C ≤ n` ticks. Phase 2: exactly `C` ticks. Total: ≤ `T + 2C ≤ 2n` → O(n).

#### 🔄 Variants you might be asked

??? question "Brent's algorithm — same problem, faster constant factor?"
    Brent's variant uses a "powers of 2" jump for `fast` and resets `slow` at each power. Slightly faster in practice (~36% fewer ops on average) but the same big-O. Mention if asked about competitive-coding optimizations; otherwise Floyd's is the canonical answer.

??? question "Detect a cycle in a directed graph (not just a list)?"
    Floyd's doesn't generalize — at each node you'd need to know which outgoing edge counts as `next`. Use **DFS with three-color marking** (white / gray / black). A back-edge to a gray node = cycle.

??? question "What if the cycle is *guaranteed* to exist?"
    Skip the `while fast and fast.next` guard — but defensive coders keep it. The compiler can hoist the guard for you.

??? question "Cycle length without finding the cycle first?"
    You'd still need to run phase 1 to know where you are inside the cycle. There's no shortcut without entering the cycle.

#### 🐛 Common bugs

- Walking `fast` two steps without checking `fast.next` is `None` — null-deref on linear lists.
- Starting `slow = head.next, fast = head` (off-by-one start) — they'll never meet on the first iteration even when they should.
- Counting Phase 2 from the meeting point but resetting one of the pointers — you only need to walk *one* of them.
- Reporting cycle "length 0" with a self-loop — a self-loop is length 1; Phase 2 still gives the right answer.

---

### Deep-dive 2: Happy Number with Floyd

<span class="diff-easy">Easy</span> &nbsp; <span class="company-tag">Google</span> &nbsp; <span class="company-tag">Amazon</span>

> A "happy number" is a positive integer where repeatedly replacing the number with the sum of squares of its digits eventually reaches 1. Numbers that don't are stuck in a cycle that never includes 1. Decide whether `n` is happy. (LeetCode 202.)

Example: `19 → 1² + 9² = 82 → 8² + 2² = 68 → 6² + 8² = 100 → 1² + 0² + 0² = 1`. Happy.

`2 → 4 → 16 → 37 → 58 → 89 → 145 → 42 → 20 → 4 → ...`. Cycle, not happy.

#### 📖 Story mode

You're walking through an arithmetic landscape under the rule "next = sum of squares of digits." Either you arrive at 1 (the absorbing state) or you fall into an unbreakable loop. You need to decide which, in O(1) extra space.

#### 🧠 Thinking process

- **Brute force**: track visited numbers in a hash set. O(k) time and space, where `k` is the trajectory length until repeat or 1.
- **Insight (Floyd's)**: the function `f(x) = sum_of_digit_squares(x)` is deterministic — every starting point eventually reaches a cycle (or 1). Apply Floyd's to detect: walk `slow = f(slow)`, `fast = f(f(fast))`. They'll meet at some value. If that value is 1, happy. Otherwise, stuck.

This generalizes: **any deterministic function on a finite domain has a cycle**. Floyd's detects it in O(1) space.

#### 🐍 Optimal solution

```python
def is_happy(n: int) -> bool:
    """True iff n eventually reaches 1 under digit-square iteration."""
    def f(x: int) -> int:
        s = 0
        while x:
            d = x % 10
            s += d * d
            x //= 10
        return s

    slow = n
    fast = f(n)
    while fast != 1 and slow != fast:
        slow = f(slow)
        fast = f(f(fast))
    return fast == 1
```

#### 🔍 Dry run on `n = 19`

| tick | slow | fast | f(slow) | f(f(fast)) |
|---|---|---|---|---|
| 0 | 19 | 82 | — | — |
| 1 | 82 | 68 | f(19)=82 | f(82)=68 → f(68)=100 → 1 |
| 2 | 68 | 1 | f(82)=68 | f(100)=1, f(1)=1 |

`fast == 1` → return True.

Dry run on `n = 4`:

| tick | slow | fast |
|---|---|---|
| 0 | 4 | 16 |
| 1 | 16 | 37 |
| 2 | 37 | 58 |
| 3 | 58 | 89 |
| 4 | 89 | 145 |
| 5 | 145 | 42 |
| 6 | 42 | 4 (back to start!) — slow=42, fast=4, not equal yet |
| 7 | 20 | 145 |
| ... | ... | ... |
| eventually | 4 | 4 | **meet → not happy** |

`fast` hits a meeting point that isn't 1 → return False.

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| Hash set | O(log n × k) | O(k) |
| **Floyd's** | **O(log n × k)** | **O(1)** |

Per `f` call is O(log n) (number of digits). The trajectory length `k` is empirically small for any 64-bit input (max around 30 for n < 10⁹).

#### 🔄 Variants you might be asked

??? question "Why must Floyd's terminate on this function?"
    Domain is finite (digit-square sums of `n` digits are bounded). Pigeonhole: any walk longer than the domain size must revisit. So Floyd's *always* terminates.

??? question "Could you reach 1 *and* be in a cycle?"
    No — `f(1) = 1` (1 is a fixed point). Once you're at 1, you stay. So reaching 1 ⇔ happy.

??? question "Replace digit-squares with digit-cubes — does the analysis change?"
    Same shape — finite domain, deterministic function, must cycle or reach a fixed point. Different fixed-point set (e.g., 153 = 1³ + 5³ + 3³ is a "narcissistic number"). Algorithm unchanged.

??? question "Happy primes?"
    Subset of happy numbers that are also prime. Same detection, then a primality check on the result. Unrelated to the pattern.

#### 🐛 Common bugs

- Initializing `slow = fast = n` and looping `while slow != fast` — you'd exit immediately. Either start `fast = f(n)` or use a do-while.
- Forgetting to check `fast == 1` separately — without it, you'd report unhappy for happy numbers.
- Mutating digits via floats (`x / 10`) instead of integer division (`x // 10`) — floating-point error.
- Negative inputs — spec says positive; if you must support them, handle `n = 0` (fixed point at 0, not 1).

---

### Deep-dive 3: Find the Cycle Start (Floyd's two-phase)

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Google</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">Meta</span>

> Given a linked list, return the node where the cycle begins. If no cycle, return `None`. (LeetCode 142.)

#### 📖 Story mode

You've detected the cycle (Phase 1 — they meet). Now you need to find the on-ramp where the tail joins the loop. Floyd's beautiful insight: from the meeting point, the distance to the entry is the *same* as the distance from the head to the entry. So a fresh pointer from head and the meeting-point pointer, both walking at speed 1, collide exactly at the entry.

#### 🧠 Thinking process

Math first. Let:

- `T` = head-to-cycle-entry distance (length of the tail).
- `C` = cycle length.
- `M` = entry-to-meeting-point distance, measured forward inside the cycle.

When `slow` and `fast` meet:

- `slow` has moved `T + M` steps.
- `fast` has moved `2(T + M)` steps and made some `k` extra full laps: `2(T + M) = T + M + k·C`.
- Therefore `T + M = k·C`, i.e. `T = k·C − M = (k−1)·C + (C − M)`.

That last form is the magic: from the meeting point, `(C − M)` more forward steps lands at the entry. Adding any multiple of `C` (full laps) doesn't change the position. So **walking exactly `T` steps from the meeting point** lands at the entry. Walking `T` steps from the head also lands at the entry. They collide there.

So the algorithm: reset one pointer to head, walk both at speed 1 — they meet at the entry.

#### 🐍 Optimal solution

```python
def detect_cycle_start(head):
    """Return the node where the cycle begins, or None."""
    slow = fast = head
    # Phase 1
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            break
    else:
        return None

    # Phase 2: same speed from head
    slow = head
    while slow is not fast:
        slow = slow.next
        fast = fast.next
    return slow
```

#### 🔍 Dry run on a tail of length 2 (`a → b`) into a cycle of length 3 (`c → d → e → c`)

`T = 2`, `C = 3`.

Phase 1:

| tick | slow | fast |
|---|---|---|
| 0 | a | a |
| 1 | b | c |
| 2 | c | e |
| 3 | d | d (meet) |

Meeting point `d`. So `M = 1` (one step from entry `c` to `d`).

Phase 2 — reset slow to `a`, walk both:

| tick | slow | fast |
|---|---|---|
| 0 | a | d |
| 1 | b | e |
| 2 | c | c (meet at entry) |

Return `c`. ✓

Verify the math: `T = 2 = (k − 1)·3 + (3 − 1) = (k − 1)·3 + 2`. With `k = 1`, `T = 2`. ✓

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| Hash set | O(n) | O(n) |
| **Floyd's two-phase** | **O(n)** | **O(1)** |

Phase 1: ≤ `T + C` iterations. Phase 2: exactly `T` iterations. Total: ≤ `2T + C ≤ 2n`.

#### 🔄 Variants you might be asked

??? question "Find the cycle entry **and** the cycle length in one algorithm."
    Phase 1 → meeting point. Phase 2a → entry (this deep-dive). Phase 2b → cycle length (deep-dive 1, walk from meeting point alone). Three phases, still O(n) total. See [LL P16](../02-data-structures/linked-lists/01-linked-list-basics.md#problem-16-linked-list-cycle-ii-start-of-the-cycle) for the full implementation.

??? question "Find Duplicate Number (LC 287) — how does it use this?"
    Treat `nums[i]` as a pointer "from index i to index nums[i]." With one duplicate, two indices point to the same value, creating a cycle in this functional graph. Floyd's two-phase finds the cycle entry, which equals the duplicate value. O(n) time, O(1) space — beats sort and beats hash set.

??? question "What if the cycle entry is the head itself?"
    Then `T = 0` and `slow = head` collides with `fast` immediately at the start of Phase 2. The loop body runs 0 times; we return `head`. ✓

??? question "Prove that the meeting point is *uniquely* determined by `T` and `C`."
    Inside the cycle, `slow` enters at position 0 (relative to entry) at tick `T`. `fast` enters at position `(2T) mod C` at tick `T`. From there, `fast` gains 1 per tick on `slow` (modulo `C`). They meet when the gap closes — uniquely determined.

#### 🐛 Common bugs

- Returning the meeting point as the entry — that's only the entry if `M = 0`, i.e., the meeting happens to be at the entry. The algorithm needs Phase 2.
- Skipping the no-cycle check — if Phase 1 exits because `fast` hit `None`, you must return `None`, not run Phase 2 on garbage.
- Using `==` instead of `is` for node comparison — works on small inputs but burns you on duplicate values in `Node.val`.
- Resetting `fast` instead of `slow` to head in Phase 2 — symmetric, both work, but pick one and document it.

---

## 🐛 Common bugs across all fast/slow problems

| Bug | Symptom | Fix |
|---|---|---|
| Walking `fast.next.next` without null guards | NullPointerException on linear lists | Always check `fast and fast.next` |
| Starting both at head with `while slow != fast` | Exits immediately | Use do-while pattern, or start `fast = head.next` |
| Confusing edge count with node count | Off-by-one cycle length | Pick a convention (count *advances* of one pointer) |
| Hash-set fallback "for safety" | Defeats O(1) space win | Trust the math |
| Reporting the meeting point as cycle entry | Wrong on most inputs | Run Phase 2 from head |
| Functional iteration on negative / zero input | Infinite loop or crash | Validate the function's domain |
| Mutating list during traversal | Cycle detection corrupted | Don't modify pointers mid-walk |

---

## 🎯 How interviewers ask fast/slow problems

### Common phrasings

| What they say | What it means |
|---|---|
| *"Does this list have a cycle?"* | Floyd's, return bool |
| *"Where does the cycle start?"* | Floyd's two-phase |
| *"Find the middle of the list"* | Slow/fast, return slow at end |
| *"Remove the n-th from the end"* | k-from-end, fast leads by n |
| *"Is this number happy?"* | Functional iteration with Floyd's |
| *"Find the duplicate without modifying the array"* | LC 287 — array as functional graph |
| *"Without extra memory"* | The signal that hash set is forbidden — Floyd's wins |

### What they're testing

1. **Pattern recognition** — do you spot "cycle / midpoint" and reach for fast/slow?
2. **Null-safety** — do you guard `fast.next.next` correctly?
3. **Math literacy** — can you explain why Phase 2 finds the cycle entry?
4. **Space awareness** — do you mention the O(1) space win over hash set?
5. **Edge cases** — empty list, single node, self-loop, head-as-entry.

### The 4-step interview flow

1. **Recognize**: cycle? midpoint? functional iteration? k-from-end?
2. **Pick the phase count**: 1 (detect) or 2 (locate / measure)?
3. **Set up the pointers**: same start? offset by k? offset by 1?
4. **State the loop guard**: `while fast and fast.next` for cycle / midpoint.

### Red flags

- Walking pointers without null guards — instant signal.
- Reaching for a hash set when interviewer said "O(1) space."
- Confusing fast/slow with general two-pointer.
- Not knowing why Phase 2 lands on the entry — math literacy is part of the test.

---

## 🔗 How fast & slow connects to other patterns

| Pattern | Connection |
|---|---|
| **Two pointers** | Fast/slow is the speed-differential specialization. [Parent page](02-two-pointers.md). |
| **Linked list** | Most fast/slow problems are on linked lists; the technique is the canonical alternative to "convert to array first." |
| **Hash table** | Hash-set cycle detection is the O(n)-space alternative — strictly worse on memory but trivially correct. |
| **Sorting** | Sorting destroys the structural invariants fast/slow exploits — never sort first. |
| **Number theory / sequences** | Pollard's rho factorization uses Floyd's on integer iterations — the same idea applied to RSA-breaking. |
| **Graph theory** | Cycle detection in arbitrary graphs uses DFS three-coloring instead — fast/slow only works on functional graphs (one outgoing edge per node). |

---

## ✅ Self-check — 8 questions

??? question "1. Why must `fast` and `slow` meet inside a cycle?"
    Inside the cycle, `fast` gains 1 step per tick on `slow`. The gap shrinks monotonically modulo `C` (cycle length) and must reach 0 within `C` ticks.

??? question "2. Why does Phase 2 (reset slow to head) land at the cycle entry?"
    Algebra: at the meeting point, `T + M = k·C`, so `T = (k−1)·C + (C − M)`. Walking `T` steps from the meeting point lands at the entry; `T` steps from head also lands at the entry. They meet there.

??? question "3. Can fast/slow find a cycle in a general graph?"
    No — fast/slow needs a *deterministic next* (one outgoing edge per node). General graphs need DFS-three-coloring or BFS-with-parent.

??? question "4. What's the maximum number of iterations in Phase 1?"
    `T + C ≤ n`. The slow pointer must enter the cycle (T ticks), then traverse at most `C` more before fast catches up.

??? question "5. Why is the hash-set alternative O(n) space?"
    You store every visited node. Worst case (no cycle), n entries.

??? question "6. What happens if the list is empty?"
    `slow = fast = head = None`. The first iteration's `while fast and fast.next` is False — exit immediately, return `None` / False. Always test this case.

??? question "7. Find the middle of an even-length list — which middle do you get?"
    With `slow = fast = head` and `while fast and fast.next`, you get the *second* of the two middles (index `n/2`). For the *first* middle (index `n/2 - 1`), use `while fast.next and fast.next.next`.

??? question "8. Give-away that a problem is fast/slow (not general two-pointer)?"
    "Cycle," "loop," "fixed point," "middle," "n-th from end," or "without extra memory on a linked structure." Speed differential plus same-direction walking is the tell.
