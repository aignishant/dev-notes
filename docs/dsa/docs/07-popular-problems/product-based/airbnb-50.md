# Airbnb — 50 most-asked questions

> The 50 problems Airbnb has asked most often, with the patterns behind them and what the interviewer is grading. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">Airbnb</span> &nbsp; <span class="phase-status phase-done">Phase 8 — Company list</span>

---

## 📖 How this page is organized

1. **What interviewing here is like**.
2. **What this company tests**.
3. **Common patterns**.
4. **The 50 questions**.
5. **Deep-dives** — 3 representative problems.
6. **Day-of tips**.

---

## 🏢 What interviewing at Airbnb is like

### Rounds (typical SWE onsite — 2026)

Airbnb is famous for its **multi-domain** interview — coding, system design, *and* "cross-functional" rounds blended together.

| Round | Length | Focus |
|---|---|---|
| **Recruiter screen** | 30 min | Background + Airbnb values. |
| **Technical phone screen** | 60 min | One coding problem. Often a *real-world* feel: "implement a price filter." |
| **Onsite — coding ×2** | 60 min each | **Design a working class** (LRU, file system, scheduler) — often 60 min on one problem with progressively harder requirements. |
| **Onsite — system design** | 60 min | "Design Airbnb search" / "design the booking flow". |
| **Onsite — cross-functional** | 60 min | Working with PM/design — empathy, communication. |
| **Onsite — Airbnb values** | 60 min | The "host an Airbnb" round — culture-deep, mission-aligned. |

### What "the Airbnb style" actually means

- **Build something working**. Coding rounds aren't 25-min LeetCode mediums — they're 60-min "design and implement this class with these 4 APIs," with follow-ups bolted on.
- **Cross-functional empathy.** Airbnb hires for "culture-add." They explicitly grade on "could PMs / designers work with this person?"
- **"Tell me about your most meaningful project"** — they want a real story about why you cared.
- **Design + implement combo.** The line between "system design" and "coding" blurs at Airbnb. You'll write actual code in design rounds.
- **Travel + community** themed problems. Listings, calendars, booking conflicts, search filters.

!!! tip "The Airbnb interviewer mindset"
    Airbnb interviewers ask: *"Would I want to host this person at my home?"* — half-joking. The real question: do they communicate, care, and ship?

---

## 🎯 What Airbnb tests

| Signal | Where they grade it | How to show it |
|---|---|---|
| **Build-a-thing fluency** | Coding rounds | Implement classes with multiple APIs in 60 min. |
| **Iteration under follow-ups** | Coding rounds | Each round adds requirements; refactor cleanly without rewrites. |
| **System design** | Design round | "Design Airbnb's search/booking" with availability + pricing + filters. |
| **Empathy + communication** | Cross-functional | Talk to non-engineers like humans. Translate tech to product. |
| **Mission alignment** | Airbnb values round | "Why Airbnb?" — better have a real answer. |

---

## 🧩 Patterns that show up most often

| Pattern | Frequency | Why Airbnb likes it |
|---|---|---|
| **OOP / class design** | ⭐⭐⭐⭐⭐ | Their primary signal. |
| **Hash map composition** | ⭐⭐⭐⭐⭐ | Standard medium fluency. |
| **Trees** | ⭐⭐⭐⭐ | Calendar / availability / nested filters. |
| **Sliding window** | ⭐⭐⭐⭐ | Booking-conflict detection. |
| **Graph BFS / DFS** | ⭐⭐⭐ | Search graphs, recommendations. |
| **Backtracking** | ⭐⭐⭐ | Listing combinations, filter expansion. |
| **Heap / Top-K** | ⭐⭐⭐ | Top listings ranking. |
| **DP** | ⭐⭐ | Less common; pricing optimization sometimes. |
| **Concurrency** | ⭐⭐ | Booking double-bookings, locks. |

---

## 📋 The 50 questions

Status: ✅ = full v3 in this bible &nbsp; 📝 = mini-v3 below &nbsp; 🚧 = lands later in Phase 8.

### Practical / mini-systems (10) — **Airbnb specialty**

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Design a Calendar / Booking System | <span class="diff-medium">Medium</span> | Interval tree | [📝](#deep-dive-1-mybookingcalendar) |
| 2 | Design a Pricing Engine | <span class="diff-medium">Medium</span> | OOP + strategy pattern | 🚧 |
| 3 | Design a Search Filter Pipeline | <span class="diff-medium">Medium</span> | Composite filters | 🚧 |
| 4 | Implement a Mini Regex Engine | <span class="diff-hard">Hard</span> | NFA / DP | 🚧 |
| 5 | Implement Wildcard Matching | <span class="diff-hard">Hard</span> | DP | 🚧 |
| 6 | Boggle / Word Search II | <span class="diff-hard">Hard</span> | Trie + DFS | 🚧 |
| 7 | Implement a Mini File System | <span class="diff-hard">Hard</span> | Trie of nodes | 🚧 |
| 8 | Implement an LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |
| 9 | Implement a Rate Limiter | <span class="diff-medium">Medium</span> | Token bucket / sliding | 🚧 |
| 10 | Implement a Pub-Sub System | <span class="diff-medium">Medium</span> | Hash of subscriber lists | 🚧 |

### Strings (8)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 11 | Two Sum | <span class="diff-easy">Easy</span> | Hash | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 12 | Group Anagrams | <span class="diff-medium">Medium</span> | Hash + sorted-key | 🚧 |
| 13 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 14 | Minimum Window Substring | <span class="diff-hard">Hard</span> | Sliding window | 🚧 |
| 15 | Text Justification | <span class="diff-hard">Hard</span> | Greedy line break | [📝](#deep-dive-2-text-justification) |
| 16 | Valid Palindrome | <span class="diff-easy">Easy</span> | Two pointers | 🚧 |
| 17 | Decode String | <span class="diff-medium">Medium</span> | Stack | 🚧 |
| 18 | Basic Calculator II | <span class="diff-medium">Medium</span> | Stack + precedence | 🚧 |

### Trees (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 19 | Binary Tree Level Order Traversal | <span class="diff-medium">Medium</span> | BFS | 🚧 |
| 20 | Lowest Common Ancestor (Binary Tree) | <span class="diff-medium">Medium</span> | DFS post-order | 🚧 |
| 21 | Validate BST | <span class="diff-medium">Medium</span> | DFS + bounds | 🚧 |
| 22 | Serialize / Deserialize Binary Tree | <span class="diff-hard">Hard</span> | DFS + queue | 🚧 |
| 23 | Construct Tree from Preorder + Inorder | <span class="diff-medium">Medium</span> | Recursive partition | 🚧 |

### Graphs (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 24 | Number of Islands | <span class="diff-medium">Medium</span> | Grid BFS/DFS | 🚧 |
| 25 | Course Schedule | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 26 | Alien Dictionary | <span class="diff-hard">Hard</span> | Topo sort | 🚧 |
| 27 | Reconstruct Itinerary | <span class="diff-hard">Hard</span> | Eulerian path | [📝](#deep-dive-3-reconstruct-itinerary) |
| 28 | Word Ladder | <span class="diff-hard">Hard</span> | BFS on word graph | 🚧 |

### Backtracking (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 29 | Combinations | <span class="diff-medium">Medium</span> | Backtracking | 🚧 |
| 30 | Permutations | <span class="diff-medium">Medium</span> | Backtracking | 🚧 |
| 31 | Word Search | <span class="diff-medium">Medium</span> | Grid DFS + backtrack | 🚧 |
| 32 | Combination Sum | <span class="diff-medium">Medium</span> | Backtracking | 🚧 |

### Sliding window / two pointers (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 33 | 3Sum | <span class="diff-medium">Medium</span> | Sort + two ptrs | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 34 | Container With Most Water | <span class="diff-medium">Medium</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 35 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 36 | Merge Intervals | <span class="diff-medium">Medium</span> | Sort + sweep | [✅](../../04-patterns/04-merge-intervals.md) |
| 37 | Meeting Rooms II | <span class="diff-medium">Medium</span> | Min-heap | 🚧 |

### Heap & Top-K (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 38 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap / bucket | 🚧 |
| 39 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | 🚧 |
| 40 | Merge K Sorted Lists | <span class="diff-hard">Hard</span> | Min-heap | 🚧 |

### DP (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 41 | Climbing Stairs | <span class="diff-easy">Easy</span> | 1D DP | 🚧 |
| 42 | Word Break | <span class="diff-medium">Medium</span> | DP + dictionary | 🚧 |
| 43 | Edit Distance | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |
| 44 | Longest Common Subsequence | <span class="diff-medium">Medium</span> | 2D DP | 🚧 |

### Misc (6)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 45 | Valid Parentheses | <span class="diff-easy">Easy</span> | Stack | 🚧 |
| 46 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 47 | Maximum Subarray | <span class="diff-medium">Medium</span> | Kadane's | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 48 | Single Number | <span class="diff-easy">Easy</span> | XOR | [✅](../../04-patterns/20-bitwise-xor.md) |
| 49 | Pow(x, n) | <span class="diff-medium">Medium</span> | Fast exponentiation | 🚧 |
| 50 | Kth Smallest Element in a BST | <span class="diff-medium">Medium</span> | In-order traversal | 🚧 |

---

## 🔬 Deep-dives — 3 Airbnb-style walkthroughs

These three are picked because:

- **Calendar / Booking** is the *literal* Airbnb domain — and the canonical "build a class with multiple APIs" 60-min round.
- **Text Justification** is asked at Airbnb constantly — UI rendering of listings has every flavor of this.
- **Reconstruct Itinerary** is the cute, on-brand graph problem — Airbnb's product is *travel itineraries*.

---

### Deep-dive 1: MyBookingCalendar

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Airbnb</span>

> Implement `book(start, end) -> bool`. Return True if no overlap with existing bookings; False otherwise. Designed as an Airbnb listing's calendar.

#### 📖 Story mode

Each Airbnb listing has a calendar — non-overlapping intervals. Booking only succeeds if the requested range is free.

#### 🧠 Thinking process

- **Naive list**: scan all intervals. O(n) per book.
- **Sorted list + binary search**: insertion is O(log n) for the search but O(n) for the shift. Still better than scanning.
- **Best**: balanced BST keyed on `start`, value = `end`. Find the predecessor and successor in O(log n); check disjoint.
- In Python interviews, `sortedcontainers.SortedList` is the practical answer (treat it as a balanced BST).

#### 🐍 Optimal solution

```python
from sortedcontainers import SortedList

class MyCalendar:
    def __init__(self) -> None:
        self.bookings: SortedList[tuple[int, int]] = SortedList()  # (start, end)

    def book(self, start: int, end: int) -> bool:
        # Find the booking with the largest start <= start
        # In SortedList, bisect by (start, +inf) and look at the predecessor.
        idx = self.bookings.bisect_left((start, float("inf")))

        if idx > 0 and self.bookings[idx - 1][1] > start:
            return False                       # overlaps with previous
        if idx < len(self.bookings) and self.bookings[idx][0] < end:
            return False                       # overlaps with next

        self.bookings.add((start, end))
        return True
```

**Why bisect on `(start, +inf)`?** It puts us *just past* any booking starting at `start`. The predecessor is the candidate "previous" interval; the element at `idx` is the "next" one.

#### 🔍 Dry run

`book(10,20) book(15,25) book(20,30)`

| call | bookings before | predecessor | next | overlap? | result |
|---|---|---|---|---|---|
| (10,20) | [] | — | — | no | T → [(10,20)] |
| (15,25) | [(10,20)] | (10,20) end=20 > 15 | — | yes | F |
| (20,30) | [(10,20)] | (10,20) end=20 not > 20 | — | no | T → [(10,20),(20,30)] |

#### ⏱️ Complexity

| Op | Time | Space |
|---|---|---|
| `book` | O(log n) | O(n) |

#### 🔄 Airbnb's classic follow-up

??? question "Now do MyCalendarII — allow up to 2 overlaps but not 3 (LC 731)."
    Maintain a second list of *intersection* intervals. On book, check if the new range overlaps any *intersection* — if yes, reject. Else add to bookings + recompute intersections involving the new range.

??? question "Now do MyCalendarIII — return the *current max k-booked* count (LC 732)."
    Sweep-line: maintain a sorted dict of `point -> count`. On book(s, e), increment at s and decrement at e. The max prefix-sum over the dict is the answer. Stride: a Fenwick tree gives O(log n) per book.

??? question "How would you scale this to 1B bookings?"
    Shard by listing_id. Each listing's calendar is small (~1K intervals). Hash-shard at the gateway.

#### 🐛 Common bugs

- Open vs closed intervals: `[start, end)` vs `[start, end]`. State the convention.
- Bisect on `(start, end)` instead of `(start, +inf)` — gets the wrong predecessor when starts coincide.

---

### Deep-dive 2: Text Justification

<span class="diff-hard">Hard</span> &nbsp; <span class="company-tag">Airbnb</span>

> Given an array of words and a max line width, return the *fully-justified* text — pad with spaces so lines are exactly `width` chars, distributing spaces as evenly as possible. The last line is left-justified.

#### 📖 Story mode

Airbnb's listing description renders justified on the page. Same algorithm Word, browsers, and LaTeX use (the simple greedy version, not Knuth-Plass).

#### 🧠 Thinking process

- **Greedy line-fill**: pack as many words as fit. Distribute spaces.
- **Edge cases**: single word per line (left-pad with spaces); the *last line* (always left-justified).
- **Spacing math**: `total_spaces = width - sum(len(w))`. `slots = len(words) - 1`. `base = total_spaces // slots`; `extra = total_spaces % slots` distributed to the leftmost slots.

#### 🐍 Optimal solution

```python
def full_justify(words: list[str], width: int) -> list[str]:
    lines: list[str] = []
    i, n = 0, len(words)

    while i < n:
        # Greedy: fit as many words as possible on this line
        j = i
        line_len = len(words[j])
        j += 1
        while j < n and line_len + 1 + len(words[j]) <= width:
            line_len += 1 + len(words[j])
            j += 1

        # words[i..j-1] fit on this line
        slots = j - i - 1                          # number of inter-word gaps
        is_last = (j == n)

        if slots == 0 or is_last:
            # Left-justify; one space between, pad right with spaces
            line = " ".join(words[i:j])
            line += " " * (width - len(line))
        else:
            total_spaces = width - sum(len(w) for w in words[i:j])
            base, extra = divmod(total_spaces, slots)
            parts: list[str] = []
            for k in range(slots):
                parts.append(words[i + k])
                parts.append(" " * (base + (1 if k < extra else 0)))
            parts.append(words[j - 1])
            line = "".join(parts)

        lines.append(line)
        i = j

    return lines
```

**The `if k < extra` distribution** is the part interviewers grade on — it's the "evenly as possible" rule.

#### 🔍 Dry run on `words=["This","is","an","example","of","text","justification."]`, `width=16`

Line 1: ["This","is","an"] — total_chars 8, slots 2, total_spaces 8. base=4, extra=0. → `"This    is    an"`.
Line 2: ["example","of","text"] — total 13, slots 2, spaces 3. base=1, extra=1. → `"example  of text"`.
Line 3: ["justification."] — last line, left-justified. → `"justification.  "`.

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **Greedy** | O(total chars) | O(total chars) |

#### 🔄 Airbnb's classic follow-up

??? question "Now optimize for *minimum total badness* across all lines (Knuth-Plass)."
    DP: `dp[i] = min total badness for justifying words[0..i]`. Transition over all valid line breaks at `j < i`. O(n²). Used in TeX.

??? question "What if some words must stay together (e.g., 'Hong Kong')?"
    Pre-merge them as a single token before greedy line-fill.

#### 🐛 Common bugs

- Forgetting the last-line special case — gives center-justified last line.
- Off-by-one on slots when only one word fits — divide by 0 if you don't guard.

---

### Deep-dive 3: Reconstruct Itinerary

<span class="diff-hard">Hard</span> &nbsp; <span class="company-tag">Airbnb</span>

> Given a list of flight tickets `[from, to]`, reconstruct a single itinerary starting from JFK that uses every ticket exactly once. If multiple valid itineraries exist, return the lex-smallest.

#### 📖 Story mode

You're handed a stack of paper tickets. Find the order in which they were used, starting at JFK. There's one — sometimes multiple — valid sequence. Return the alphabetically-smallest.

#### 🧠 Thinking process

- This is **Eulerian path** — visit every edge exactly once.
- **Hierholzer's algorithm**: DFS, but post-order — when you can't go anywhere, backtrack and prepend.
- **Lex-smallest**: at each node, sort outgoing edges and take them in order. A min-heap as the adjacency list does this in O(log) per pop.

#### 🐍 Optimal solution

```python
import heapq
from collections import defaultdict

def find_itinerary(tickets: list[list[str]]) -> list[str]:
    """Lex-smallest Eulerian path starting at JFK."""
    g: dict[str, list[str]] = defaultdict(list)
    for u, v in tickets:
        heapq.heappush(g[u], v)             # min-heap so we always pick smallest

    route: list[str] = []

    def dfs(u: str) -> None:
        while g[u]:
            v = heapq.heappop(g[u])
            dfs(v)
        route.append(u)                     # post-order

    dfs("JFK")
    return route[::-1]                       # reverse for forward order
```

**Why post-order + reverse?** When you hit a dead end, that node is the *last* in the itinerary. Building the list post-order then reversing gives the right traversal — and it works even if you'd otherwise get "stuck" partway through.

#### 🔍 Dry run on `[["MUC","LHR"],["JFK","MUC"],["SFO","SJC"],["LHR","SFO"]]`

g = {JFK: [MUC], MUC: [LHR], LHR: [SFO], SFO: [SJC]}.

DFS(JFK) → DFS(MUC) → DFS(LHR) → DFS(SFO) → DFS(SJC). At SJC, no edges → append SJC. Backtrack: SFO, LHR, MUC, JFK each appended in turn.

route = [SJC, SFO, LHR, MUC, JFK]. Reversed: [JFK, MUC, LHR, SFO, SJC]. ✅

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **Hierholzer + heap** | O(E log E) | O(V + E) |

#### 🔄 Airbnb's classic follow-up

??? question "What if there's no valid itinerary (the graph isn't Eulerian)?"
    The standard Eulerian-path conditions: at most one vertex with `out − in == 1` (start) and one with `in − out == 1` (end), all others balanced. Or detect during DFS — if we don't use every edge, fail.

??? question "What if you must minimize *total cost* (weighted edges)?"
    Travelling-salesman-like — NP-hard in general. For Eulerian paths over a DAG of cost-sorted edges, sorting by cost is greedy but not always optimal. Mention NP-hard and pivot.

??? question "What if tickets can be used multiple times (repeats allowed)?"
    Plain BFS / DFS for shortest path now; it's no longer Eulerian. Use Dijkstra.

#### 🐛 Common bugs

- Using a regular sorted list and `pop(0)` — that's O(n). Heap or `deque` keeps it O(log).
- Forgetting to *reverse* — you get a backwards itinerary.

---

## 🗓️ Day-of tips for an Airbnb interview

!!! tip "The morning checklist"
    1. **Sleep 8 hours**.
    2. **Re-read** Airbnb's [tech blog](https://medium.com/airbnb-engineering) — calibrates the system-design vocabulary.
    3. **Prepare 2 stories** about a project you cared about — be ready for "why does this matter to you?"
    4. **Practice 60-min build problems** — pick LRU, mini-FS, calendar.
    5. **Test Zoom + your IDE** the night before.

### During the interview

| Stage | What to say / do |
|---|---|
| **First 60s** | Restate. Sketch the API surface. **Ask about edge cases** (booking conflicts, retroactive changes, etc.). |
| **Pre-coding (~5-10 min)** | Sketch the class, methods, data structures **before** typing. |
| **Coding (~30 min)** | Build the simplest version. **Then iterate** as the interviewer adds requirements. |
| **System design** | API → data model → storage → search index → caching → metrics. |
| **Cross-functional** | Talk about working *with* PMs and designers. Use "we discussed and decided" framing. |

### Red & green flags

- 🚩 Treating each follow-up as a rewrite.
- 🚩 Engineer-only framing in cross-functional rounds.
- 🚩 No real "why I want to work here" answer.
- 🟢 Refactoring cleanly between follow-ups (extract a method, rename for clarity).
- 🟢 Using Airbnb domain words ("listing," "calendar," "host," "guest") naturally.
- 🟢 Asking about how the team works with design.

---

## 🔁 Where to go from here

- **Solve the 50** in roughly the order above.
- **Practice 60-min builds**: LRU, file system, calendar, regex engine.
- **Cross-check** with the [Top 100 by Pattern](../top-100-by-pattern.md).
- **System design** — start with [URL Shortener](../../08-system-design/index.md), then "design Airbnb search" mentally.

> Same six-part shape as [Google 50](google-50.md) and [Meta 50](meta-50.md).
