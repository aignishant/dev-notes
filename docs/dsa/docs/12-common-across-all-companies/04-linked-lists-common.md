# Linked lists — common across all companies

> Pointer arithmetic, dummy heads, and Floyd's cycle trick — the linked-list canon every interviewer keeps in their pocket.

<span class="company-tag">Google</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">TCS</span> &nbsp; <span class="company-tag">ISRO</span> &nbsp; <span class="phase-status phase-done">Phase 14 — Common Across</span>

---

Linked-list problems are the cleanest test of **pointer manipulation** an interviewer can ask. There's no library to hide behind — you either understand the wiring or you don't. The 15 problems below are the ones every shop reuses; once you can do them blindfolded, list problems stop being scary.

## Patterns that drive these problems

| Pattern | Frequency | Where it shows up |
|---|---|---|
| Iterative reversal (`prev/curr/next`) | ★★★★★ | Reverse list, Reverse II, Reorder, Palindrome |
| Two pointers (slow/fast) | ★★★★★ | Cycle detection, middle, Nth-from-end, Palindrome |
| Dummy head node | ★★★★★ | Merge, Add, Remove Nth, Sort |
| Hash map for nodes | ★★★★☆ | Copy w/ Random Pointer, Intersection (one variant) |
| Merge-sort on lists | ★★★☆☆ | Sort List |
| In-place rewiring | ★★★☆☆ | Odd-Even, Rotate, Reorder |

## The list (15 problems)

| # | Problem | Difficulty | Pattern | LC# |
|---|---|---|---|---|
| 1 | Reverse Linked List | Easy | Iterative reversal | 206 |
| 2 | Reverse Linked List II | Medium | Reversal in place | 92 |
| 3 | Merge Two Sorted Lists | Easy | Dummy head | 21 |
| 4 | Linked List Cycle | Easy | Floyd's tortoise/hare | 141 |
| 5 | Linked List Cycle II | Medium | Floyd's + math | 142 |
| 6 | Remove Nth From End | Medium | Two pointers (gap of n) | 19 |
| 7 | Add Two Numbers | Medium | Dummy head + carry | 2 |
| 8 | Intersection of Two Lists | Easy | Two-pointer switch | 160 |
| 9 | Palindrome Linked List | Easy | Mid + reverse half | 234 |
| 10 | Odd Even Linked List | Medium | Two chains | 328 |
| 11 | Copy List with Random Pointer | Medium | Hash map / interleave | 138 |
| 12 | Reorder List | Medium | Mid + reverse + merge | 143 |
| 13 | Sort List | Medium | Merge sort | 148 |
| 14 | Rotate List | Medium | Find tail + relink | 61 |
| 15 | Remove Duplicates from Sorted List | Easy | One pointer | 83 |

---

## Deep-dive 1 — Reverse Linked List (iterative + recursive)

The "hello world" of linked lists. If you can write **both** versions in 60 seconds without bugs, you've earned the right to attempt every other list problem.

??? question "Why does the iterative version need three pointers, not two?"
    You're rotating a triple `(prev, curr, next)`. If you only kept `(prev, curr)`, the moment you write `curr.next = prev` you've lost the original `curr.next` and can't advance. The `nxt` temp is the bookmark.

=== "Iterative"

    ```python linenums="1"
    from __future__ import annotations
    from dataclasses import dataclass


    @dataclass
    class ListNode:
        val: int
        next: "ListNode | None" = None


    def reverse_list(head: ListNode | None) -> ListNode | None:
        """Reverse a singly-linked list in place.

        Time:  O(n)
        Space: O(1)
        """
        prev: ListNode | None = None
        curr = head
        while curr is not None:
            nxt = curr.next        # bookmark
            curr.next = prev       # flip
            prev = curr            # advance prev
            curr = nxt             # advance curr
        return prev                # new head
    ```

=== "Recursive"

    ```python linenums="1"
    def reverse_list_rec(head: ListNode | None) -> ListNode | None:
        """Recursive reversal.

        Time:  O(n)
        Space: O(n) — call stack.
        """
        if head is None or head.next is None:
            return head
        new_head = reverse_list_rec(head.next)
        head.next.next = head      # the head of the rest now points back
        head.next = None           # detach to avoid a cycle
        return new_head
    ```

!!! tip "Pick the iterative version on a whiteboard"
    O(1) space and no stack-overflow risk. Mention recursion as the elegant alternative — interviewers like seeing both.

---

## Deep-dive 2 — Linked List Cycle II (Floyd's tortoise & hare)

Detecting a cycle is easy. Finding **where** the cycle begins is the elegant part — and the math is the kind of thing senior interviewers love to hear explained.

??? question "Why do the pointers meet exactly at the cycle entrance after the reset?"
    Let `a` = distance from head to cycle start, `b` = distance from cycle start to meeting point, `c` = remaining cycle length so that `b + c` = cycle length `L`.

    - Slow has walked `a + b`.
    - Fast has walked `a + b + k(b + c)` for some integer `k ≥ 1`.
    - Fast moves twice as fast: `2(a + b) = a + b + k(b + c)` → `a + b = k(b + c)` → `a = k(b + c) - b = (k-1)L + c`.

    So `a ≡ c (mod L)`. Restart one pointer at `head` and keep the other at the meeting point; advance both **one step at a time**. After `a` steps the head-pointer reaches the cycle entrance, and the other has walked `a` further inside the cycle = `c + (a - c)` = an integer number of full loops past the entrance. They meet exactly at the entrance. ∎

```python linenums="1"
from __future__ import annotations


def detect_cycle(head: ListNode | None) -> ListNode | None:
    """Return the node where the cycle begins, or None.

    Floyd's algorithm — two phases:
      1. slow/fast meet inside the cycle (or fast hits None).
      2. reset one pointer to head; advance both by 1; meeting point
         is the cycle entrance.

    Time:  O(n)
    Space: O(1)
    """
    slow = fast = head
    # Phase 1 — find a meeting point inside the cycle.
    while fast is not None and fast.next is not None:
        slow = slow.next               # type: ignore[union-attr]
        fast = fast.next.next
        if slow is fast:
            break
    else:
        return None                     # ran off the end, no cycle
    if fast is None or fast.next is None:
        return None

    # Phase 2 — walk from head and meeting point at same speed.
    p = head
    q = slow
    while p is not q:
        p = p.next                      # type: ignore[union-attr]
        q = q.next                      # type: ignore[union-attr]
    return p
```

!!! warning "Don't use a hash set in the interview"
    A `seen: set[ListNode]` solves it in O(n) time **and** O(n) space — but Floyd's is the expected answer because it's O(1) space and shows you actually understand pointers.

---

## 🃏 Cheatsheet

- **Always use a `dummy` head** when the answer might modify `head` (merge, remove, add). Saves an entire branch of edge-case code.
- **Slow/fast** finds the middle in one pass: `slow` ends at the middle (left-middle for even-length).
- **Slow/fast** detects cycles in O(1) space; cycle II needs the extra reset-and-walk trick.
- **Reverse-then-merge** is the secret sauce for Reorder List and Palindrome List.
- **Two pointers with a fixed gap of `n`** removes the Nth-from-end in one pass — no length count needed.
- **Pointer switch trick** for Intersection of Two Lists: `pA = pA.next or headB; pB = pB.next or headA`. They meet after `len(A)+len(B)` steps.
- **Copy List w/ Random Pointer**: either hash `old -> new` (O(n) space), or interleave new nodes between old ones for O(1) extra space.
- **Sort List in O(n log n)** = merge sort on lists. Quick sort on lists is painful — don't suggest it.
- **Detach before you re-attach.** Forgetting `head.next = None` in recursive reverse creates a cycle.
- **`while curr and curr.next`** is the safest loop guard for any "look one ahead" pattern.
