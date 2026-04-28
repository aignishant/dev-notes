# In-Place Linked List Reversal

> The three-pointer dance that flips a linked list — or any sublist of one — in O(n) time and **O(1) extra space**. Reverse a list, reverse a sublist, reverse every k nodes, swap pairs, check palindrome, rotate by k. Once you internalise the `prev / curr / next_node` triplet, half the linked-list questions in the FAANG bank fall in five lines.

<span class="phase-status phase-inprogress">Phase 5 — pattern page (Batch 17)</span>

---

## 📖 What is in-place reversal?

You're walking down a chain of arrows: `1 → 2 → 3 → 4 → 5 → None`. The goal is to flip every arrow without allocating new nodes — so the chain becomes `1 ← 2 ← 3 ← 4 ← 5` (and you return the new head, `5`).

If you just write `curr.next = prev` blindly, you destroy the link to whatever comes after `curr` and you can never recover it. The fix is to **save `curr.next` into a temporary** *before* you overwrite, do the flip, then advance.

That gives the canonical three-pointer template:

```
     prev    curr    next_node
       ↓       ↓        ↓
      ...  →  X    →   ...
```

At each step:

1. **Save** `next_node = curr.next`.
2. **Flip** `curr.next = prev`.
3. **Advance** `prev = curr`, `curr = next_node`.

Each node gets touched exactly once → **O(n) time, O(1) space**.

!!! tip "The signal — when to reach for in-place reversal"
    Reach for it when you see:

    - Linked-list problem mentioning **"reverse"**, **"reorder"**, **"k group"**, **"swap pairs"**, **"palindrome"**, or **"rotate."**
    - Constraint: **"do not allocate new nodes"** / **"O(1) extra space."**
    - The natural recursion would blow the stack on long lists (the iterative three-pointer dance avoids this).

    Cousin patterns:

    - **Stack-based reversal** — push everything onto a stack, pop in reverse. O(n) extra space; OK for short lists, bad for "constant memory."
    - **Array conversion** — copy values to a list, two-pointer reverse, copy back. Cheating; only acceptable if the interviewer explicitly allows it.

---

## 🧩 The three flavors

### Flavor 1: Full-list reversal (the primitive)

```python
class ListNode:
    def __init__(self, val: int = 0, next: "ListNode | None" = None) -> None:
        self.val = val
        self.next = next


def reverse_list(head: ListNode | None) -> ListNode | None:
    prev: ListNode | None = None
    curr = head
    while curr:
        next_node = curr.next       # (1) save
        curr.next = prev            # (2) flip
        prev = curr                 # (3) advance prev
        curr = next_node            # (4) advance curr
    return prev                     # (5) prev is the new head
```

1. **Save** the forward pointer before you overwrite it.
2. **Flip** the current node's arrow back.
3–4. **Slide** the window forward by one.
5. When `curr` is `None`, `prev` holds the last visited node — which is the new head.

**Examples:** Reverse Linked List (LC 206), Palindrome Linked List (LC 234 — reverse second half), Reorder List (LC 143 — reverse second half then weave).

### Flavor 2: Sublist reversal (`reverseBetween`, LC 92)

You're given `head, left, right` (1-indexed). Reverse only the nodes in positions `[left..right]`, leave the rest intact. The trick: a **dummy head** so you don't have to special-case `left == 1`, plus an **anchor pointer** before the sublist that you'll relink at the end.

```python
def reverse_between(
    head: ListNode | None, left: int, right: int
) -> ListNode | None:
    if not head or left == right:
        return head

    dummy = ListNode(0, head)               # (1) sentinel
    before = dummy
    for _ in range(left - 1):               # (2) walk to node before sublist
        assert before.next is not None
        before = before.next

    # `start` is the first node of the sublist; it will become the LAST.
    start = before.next
    assert start is not None
    curr = start.next
    # Splice each `curr` to the front of the sublist, one at a time.
    for _ in range(right - left):
        assert curr is not None
        start.next = curr.next              # (3) detach curr
        curr.next = before.next             # (4) prepend to sublist
        before.next = curr                  # (5) re-anchor
        curr = start.next                   # (6) advance

    return dummy.next
```

The "splice forward" idiom (lines 3–6) is **subtly different** from the basic three-pointer dance — instead of flipping arrows in place, you keep yanking each `curr` to the *front* of the sublist. The effect is the same reversal, but with the relinking already done at every step, so no fix-up is needed at the end.

**Examples:** Reverse Linked List II (LC 92), Reverse Nodes in Even Length Groups (LC 2074).

### Flavor 3: K-group reversal (LC 25)

Reverse every k consecutive nodes. If the final group has fewer than k nodes, **leave it alone**.

```python
def reverse_k_group(head: ListNode | None, k: int) -> ListNode | None:
    dummy = ListNode(0, head)
    group_prev = dummy

    while True:
        kth = group_prev
        for _ in range(k):                  # (1) find the kth node from group_prev
            if kth.next is None:
                return dummy.next           # not enough nodes → leave intact
            kth = kth.next

        group_next = kth.next
        # (2) Standard three-pointer reverse from group_prev.next up to and including kth
        prev, curr = group_next, group_prev.next
        while curr is not group_next:
            assert curr is not None
            nxt = curr.next
            curr.next = prev
            prev = curr
            curr = nxt

        # (3) Re-anchor: old group_prev.next is now the tail of the reversed group
        new_tail = group_prev.next
        assert new_tail is not None
        group_prev.next = kth               # new head of group
        group_prev = new_tail               # tail becomes the next group_prev
```

The two new ideas vs Flavor 1:

- **Bounded reversal** — reverse from `group_prev.next` up to and including `kth`. We *seed* `prev = group_next` so the inner loop's flip arrow points at the next group automatically.
- **Re-anchoring** — the node that *was* the head of the group is now its tail; that node becomes the next iteration's `group_prev`.

**Examples:** Reverse Nodes in k-Group (LC 25), Swap Nodes in Pairs (LC 24 — k=2 special case), Reverse Alternate k Nodes.

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Full reversal | Flip every arrow | Reverse Linked List (LC 206) | `prev/curr/next` triplet |
| 2 | Sublist reversal | Flip a contiguous middle range | Reverse Linked List II (LC 92) | Dummy + before-anchor + splice-forward |
| 3 | K-group reversal | Flip every k nodes | Reverse Nodes in k-Group (LC 25) | Bounded reversal + re-anchor |
| 4 | Pair swap | k=2 specialisation | Swap Nodes in Pairs (LC 24) | Three-step pointer hop |
| 5 | Reverse-half-and-compare | Reverse second half for palindrome | Palindrome Linked List (LC 234) | Find middle (fast/slow) → reverse → walk both |
| 6 | Reverse-and-weave | Reverse second half then interleave | Reorder List (LC 143) | Compose middle + reverse + merge |
| 7 | Rotate-by-k | Conceptual reversal of pieces | Rotate List (LC 61) | Find length → close cycle → cut |

---

## 📋 Twenty problems on this pattern

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Reverse Linked List | 206 | <span class="diff-easy">Easy</span> | Full reversal | 📝 |
| 2 | Reverse Linked List II | 92 | <span class="diff-medium">Medium</span> | Sublist reversal | 📝 |
| 3 | Swap Nodes in Pairs | 24 | <span class="diff-medium">Medium</span> | Pair swap | 📝 |
| 4 | Reverse Nodes in k-Group | 25 | <span class="diff-hard">Hard</span> | K-group reversal | 📝 |
| 5 | Palindrome Linked List | 234 | <span class="diff-easy">Easy</span> | Reverse-half-and-compare | 📝 |
| 6 | Reorder List | 143 | <span class="diff-medium">Medium</span> | Reverse-and-weave | 📝 |
| 7 | Rotate List | 61 | <span class="diff-medium">Medium</span> | Rotate-by-k | 📝 |
| 8 | Odd Even Linked List | 328 | <span class="diff-medium">Medium</span> | Two-list weaving | 📝 |
| 9 | Add Two Numbers II | 445 | <span class="diff-medium">Medium</span> | Reverse + add + reverse | 📝 |
| 10 | Plus One Linked List | 369 | <span class="diff-medium">Medium</span> | Reverse + carry + reverse | 📝 |
| 11 | Reverse Nodes in Even Length Groups | 2074 | <span class="diff-medium">Medium</span> | K-group variant | 📝 |
| 12 | Reverse Linked List in Place (recursive) | 206 var | <span class="diff-easy">Easy</span> | Full reversal | 📝 |
| 13 | Swap Nodes Given k from start/end | 1721 | <span class="diff-medium">Medium</span> | Find-then-swap | 📝 |
| 14 | Split LL into Parts | 725 | <span class="diff-medium">Medium</span> | Bounded chunking | 📝 |
| 15 | Remove Nth From End | 19 | <span class="diff-medium">Medium</span> | Two-pointer + relink | 📝 |
| 16 | Partition List | 86 | <span class="diff-medium">Medium</span> | Two-list partition | 📝 |
| 17 | Reverse Substring Between Each Pair of Parens | 1190 | <span class="diff-medium">Medium</span> | Stack-of-strings (cousin) | 📝 |
| 18 | Flatten Multilevel Doubly Linked List | 430 | <span class="diff-medium">Medium</span> | DFS + relink | 📝 |
| 19 | Insertion Sort List | 147 | <span class="diff-medium">Medium</span> | Insert-into-sorted prefix | 📝 |
| 20 | Sort List | 148 | <span class="diff-medium">Medium</span> | Merge sort on LL | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Reverse Linked List (LC 206)

> Given the head of a singly linked list, reverse it and return the new head.

The primitive every other variant builds on. If you can't do this in your sleep, the rest of the chapter is uphill.

#### Code

```python
def reverse_list(head: ListNode | None) -> ListNode | None:
    prev: ListNode | None = None
    curr = head
    while curr:
        next_node = curr.next
        curr.next = prev
        prev = curr
        curr = next_node
    return prev
```

#### Dry run on `1 → 2 → 3 → None`

| Step | `prev` | `curr` | `next_node` | After flip + advance |
|------|--------|--------|-------------|----------------------|
| 0 (init) | `None` | `1` | — | — |
| 1 | `None` | `1` | `2` | `prev=1`, `curr=2`, list now `None ← 1`, `2 → 3` |
| 2 | `1` | `2` | `3` | `prev=2`, `curr=3`, list now `None ← 1 ← 2`, `3 → None` |
| 3 | `2` | `3` | `None` | `prev=3`, `curr=None`, list now `None ← 1 ← 2 ← 3` |

Loop exits, return `prev` = `3`. New chain: `3 → 2 → 1 → None`. ✓

#### Recursive variant (for completeness)

```python
def reverse_list_rec(head: ListNode | None) -> ListNode | None:
    if head is None or head.next is None:
        return head
    new_head = reverse_list_rec(head.next)
    head.next.next = head           # the node after head points back to head
    head.next = None                # cut the old forward arrow
    return new_head
```

The recursion is elegant but uses **O(n) stack** — worst case 50k deep on LC's max input → stack overflow. Iterative is the production answer.

#### Complexity

- **Time:** O(n).
- **Space:** O(1) iterative; O(n) recursive (stack frames).

---

### Deep-dive 2 — Reverse Linked List II (LC 92)

> Reverse the nodes of the list from position `left` to position `right` (1-indexed) in one pass and in-place.

The classic interview discriminator. Most candidates manage Flavor 1 in their sleep but fumble the splice-forward idiom on Flavor 2.

#### Code (re-stated)

```python
def reverse_between(
    head: ListNode | None, left: int, right: int
) -> ListNode | None:
    if not head or left == right:
        return head

    dummy = ListNode(0, head)
    before = dummy
    for _ in range(left - 1):
        assert before.next is not None
        before = before.next

    start = before.next
    assert start is not None
    curr = start.next
    for _ in range(right - left):
        assert curr is not None
        start.next = curr.next
        curr.next = before.next
        before.next = curr
        curr = start.next

    return dummy.next
```

#### Dry run on `1 → 2 → 3 → 4 → 5`, `left=2`, `right=4`

After the index walk, `before` points at node `1`, `start` points at node `2`, `curr` points at node `3`. Expected output: `1 → 4 → 3 → 2 → 5`.

**Iteration 1** — splice `curr=3` to the front of the sublist:

```
Before: 1 → 2 → 3 → 4 → 5
              ↑   ↑
            start curr
After detach (start.next = curr.next):    1 → 2 → 4 → 5,  curr=3 floating
After prepend (curr.next = before.next):  3 → 2 → 4 → 5
After re-anchor (before.next = curr):     1 → 3 → 2 → 4 → 5
After advance (curr = start.next):        curr = 4
```

State: `1 → 3 → 2 → 4 → 5`, `start=2`, `curr=4`.

**Iteration 2** — splice `curr=4`:

```
Detach (start.next = curr.next):   1 → 3 → 2 → 5,  curr=4 floating
Prepend (curr.next = before.next): 4 → 3 → 2 → 5
Re-anchor (before.next = curr):    1 → 4 → 3 → 2 → 5
Advance (curr = start.next):       curr = 5
```

We've done `right - left = 2` iterations. Loop exits. Return `dummy.next = 1 → 4 → 3 → 2 → 5`. ✓

#### Why splice-forward instead of "reverse + reattach"

You *can* solve this by detaching the sublist, calling `reverse_list` on it, and reattaching. But that's two passes (find sublist, then reverse) plus four pointer fix-ups at the boundaries — easy to off-by-one at the boundaries. Splice-forward does the entire thing in one inner loop with three pointer writes per node and the boundary conditions handled by `dummy`.

#### Complexity

- **Time:** O(n).
- **Space:** O(1).

---

### Deep-dive 3 — Reverse Nodes in k-Group (LC 25)

> Reverse the nodes of a linked list k at a time. If the final group has fewer than k nodes, leave it intact.

This problem is famously hard for live coding because there are **three** moving anchors (`group_prev`, `kth`, `group_next`) and one inner reversal. We'll walk through both the algorithm and the dry run.

#### Code (re-stated, with comments)

```python
def reverse_k_group(head: ListNode | None, k: int) -> ListNode | None:
    dummy = ListNode(0, head)
    group_prev = dummy                       # node before current group

    while True:
        # 1) Find the kth node from group_prev. If it doesn't exist, stop.
        kth = group_prev
        for _ in range(k):
            if kth.next is None:
                return dummy.next
            kth = kth.next

        group_next = kth.next                # first node of the next group

        # 2) Reverse the group [group_prev.next .. kth] inclusive.
        # Seed prev = group_next so the inner reversal's first flip
        # already points at the next group — no fix-up needed at the end.
        prev, curr = group_next, group_prev.next
        while curr is not group_next:
            assert curr is not None
            nxt = curr.next
            curr.next = prev
            prev = curr
            curr = nxt

        # 3) Re-anchor: the node that *was* the group's head is now its tail;
        # the kth node we just stepped to is the new head of the group.
        new_tail = group_prev.next
        assert new_tail is not None
        group_prev.next = kth
        group_prev = new_tail
```

#### Dry run on `1 → 2 → 3 → 4 → 5`, `k = 2`

**Iteration 1** — group is `(1, 2)`:

- `group_prev` = dummy, find `kth` = `2`, `group_next` = `3`.
- Reverse from `1` to `2`, with `prev` seeded to `3`. After inner loop: `1 ← 2`, with `1.next = 3` (the seed wired through).
- Re-anchor: `new_tail = 1`, `dummy.next = 2`, `group_prev = 1`.
- List state: `2 → 1 → 3 → 4 → 5` (with dummy at the start).

**Iteration 2** — group is `(3, 4)`:

- `group_prev` = node 1, find `kth` = `4`, `group_next` = `5`.
- Reverse from `3` to `4`, `prev` seeded to `5`. After inner loop: `3 ← 4`, with `3.next = 5`.
- Re-anchor: `new_tail = 3`, `1.next = 4`, `group_prev = 3`.
- List state: `2 → 1 → 4 → 3 → 5`.

**Iteration 3** — only one node left (`5`), can't form a group of 2:

- The `for _ in range(k)` finds `kth.next is None` after one step and returns `dummy.next`.

Final list: `2 → 1 → 4 → 3 → 5`. ✓

For `k=3` on the same input, iteration 1 reverses `(1,2,3)` to `3 → 2 → 1 → 4 → 5`; iteration 2 finds only 2 nodes left and bails out.

#### Why seeding `prev = group_next` is the elegant move

Without it, after reversing the group you'd have to walk back to the new tail and reattach: `new_tail.next = group_next`. Seeding `prev` ahead of time **bakes that final fix-up into the inner loop's very first flip** (`curr.next = prev` on the first iteration writes `1.next = 3`). One fewer pointer assignment, and one fewer line where you can off-by-one.

#### Complexity

- **Time:** O(n) — every node is touched a constant number of times.
- **Space:** O(1).

---

## 🐛 Common bugs

1. **Forgetting to save `next` before flipping.** `curr.next = prev` *destroys* the forward link. If you didn't save it first, you've lost the rest of the list.
2. **Returning `head` instead of `prev`.** After the loop, `head` is the last (now-tail) node, not the new head. Return `prev`.
3. **Off-by-one on `left - 1` in sublist reversal.** Walking `left - 1` steps from `dummy` lands you on the node *before* the sublist. Walking `left` steps lands you on the first node of the sublist — wrong anchor.
4. **K-group: forgetting the "less than k remaining" exit.** If the tail has fewer than k nodes, you must *not* reverse them. The check `if kth.next is None` inside the for loop handles this only because we start `kth = group_prev` (one before the group) — moving k steps lands us *on* the kth node. Off-by-one here means you reverse k+1 nodes or skip one.
5. **K-group: reversing without seeding `prev`.** You'll end up with the reversed group whose new tail's `next` is `None`, severing the rest of the list.
6. **Pair swap done with values, not pointers.** "Swap pairs" sometimes the candidate writes `a.val, b.val = b.val, a.val`. Many follow-ups (e.g., where the node carries more than `val`) want true pointer manipulation; ask first.
7. **Recursive reversal stack overflow.** Recursion is `O(n)` stack — fine on whiteboard, fails LC's 5×10⁴-node tests if it's already deep.
8. **Modifying the input when the caller didn't expect it.** Reversal is destructive. If a follow-up asks "now print the original list," you've already mutated it.

---

## 🗣️ Interviewer phrasings to recognize

- "Reverse the linked list." → Flavor 1.
- "Reverse from position m to n." → Flavor 2.
- "Reverse every k nodes." / "Reverse in groups of k." → Flavor 3.
- "Swap every two adjacent nodes." → Flavor 3 with k=2 (or pair-swap inline).
- "Is this list a palindrome — in O(1) space?" → Find middle (fast/slow) + reverse second half + walk.
- "Rearrange so first/last/second/second-last alternate." → Reorder List (LC 143).
- "Rotate the list to the right by k places." → Compute length, close into a cycle, cut at `length - k % length`.

---

## 🧭 Connections to other patterns

- **Fast & Slow Pointers** ([03-fast-slow-pointers.md](03-fast-slow-pointers.md)) — palindrome and reorder-list both rely on `find middle` first.
- **Two Pointers** ([02-two-pointers.md](02-two-pointers.md)) — the `prev / curr` triplet is a degenerate same-direction two-pointer with a third state variable.
- **Stacks** — alternative for reversal when O(n) extra space is allowed and recursion is forbidden (e.g., embedded systems).
- **Recursion / divide-and-conquer** — Sort List (LC 148) uses merge-sort with reversal-style relinking inside merge. Same pointer-fluency required.

---

## ✅ Self-check — 8 questions

??? question "1. Why must we save `curr.next` before writing `curr.next = prev`?"
    The assignment overwrites the only forward link. Without saving it first, the rest of the list is unreachable — you've leaked everything past `curr`.

??? question "2. Why does the iterative reversal return `prev` and not `head`?"
    The loop terminates when `curr is None`. At that moment, `prev` points at the last visited node — i.e., the original tail, which is now the new head.

??? question "3. Trick question — name a case where Flavor 1 fails."
    None. Flavor 1 handles `head=None` (loop body never runs, returns `None`) and single-node lists (one iteration, returns the same node). It's the most universally correct primitive in the chapter.

??? question "4. Why use a dummy node in Flavor 2 and Flavor 3 but not Flavor 1?"
    Flavor 1 returns whatever `prev` ends up as — no fixed reference to "the head" matters. Flavors 2 and 3 must keep a stable pointer to **the node before the section being modified**, even when that section starts at the original head. The dummy's `next` is always the answer's head.

??? question "5. Why does seeding `prev = group_next` matter in k-group reversal?"
    It fuses the post-reversal "reattach the new tail to the next group" into the very first flip of the inner loop, cutting one pointer write and one off-by-one risk.

??? question "6. How would you reverse a doubly linked list?"
    Same triplet, but each step also flips the `prev` pointer: `curr.prev, curr.next = curr.next, curr.prev`. Then advance `curr = curr.prev` (which used to be `curr.next`). New head is the old tail.

??? question "7. Can you reverse a linked list using only one pointer?"
    Not without recursion or other auxiliary state. The three-pointer dance is the minimum for an iterative O(1)-space solution. (Variants compress two pointers into a swap-and-walk, but the *three pieces of state* — what came before, what's current, what comes next — are always implicit.)

??? question "8. Palindrome Linked List in O(1) space — outline?"
    1) Fast/slow to find the middle. 2) Reverse the second half. 3) Walk first-half pointer and reversed-second-half pointer in lockstep, comparing values. 4) (Optional, polite) un-reverse the second half so the caller's list is intact. Total: O(n) time, O(1) extra.

---

> **Next pattern up:** Tree BFS — level-order traversal with a queue, the foundation for "right side view," "zigzag," "minimum depth," and most layered-tree questions (page coming next).
