# Netflix — 50 most-asked questions

> The 50 problems Netflix has asked most often, with the patterns behind them and what the interviewer is grading. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">Netflix</span> &nbsp; <span class="phase-status phase-inprogress">Phase 8 — company page</span>

---

## 📖 How this page is organized

1. **What interviewing here is like** — rounds, format, signal, vibe.
2. **What this company tests** — the specific skills they grade for.
3. **Common patterns** — which of the 20 patterns show up most often.
4. **The 50 questions** — grouped by topic.
5. **Deep-dives** — 3 representative problems in mini-v3 format.
6. **Day-of tips**.

---

## 🏢 What interviewing at Netflix is like

### Rounds (typical Senior SWE onsite — 2026)

Netflix hires senior — **L4 (junior) is rare**, most openings are **L5 (senior) and L6 (staff)**. Expect this profile.

| Round | Length | Focus |
|---|---|---|
| **Recruiter screen** | 30 min | Background, "Netflix culture deck" alignment. |
| **Hiring manager** | 60 min | Project deep-dive + "are you senior?" gauge. |
| **Tech screen** | 60 min | One coding problem + system design micro. |
| **Onsite — coding** | 60 min | One hard or two mediums. |
| **Onsite — system design ×2** | 60 min each | Streaming-flavored: video CDN, A/B testing, recommendations. **Heavy weight.** |
| **Onsite — culture / values** | 60 min | The "freedom + responsibility" interview. |
| **Onsite — cross-functional** | 60 min | Pair with PM or director — "would I want to work with this person?" |

### What "the Netflix style" actually means

- **Senior-only bar.** They're not training you. You should be able to architect a streaming subsystem on a whiteboard in 60 min.
- **Fewer rounds, deeper signal.** Each interviewer expects 60 min of substantive talk; surface-level answers fail.
- **Culture deck > LeetCode.** Read the Netflix culture deck. They will ask "describe a time you disagreed and committed." Calibrate your stories.
- **High-context, low-process.** They explicitly hire people who thrive without scaffolding. Show you've worked autonomously and shipped without check-ins.
- **Why are you leaving your current role?** Netflix asks bluntly. Have an honest answer.

!!! tip "The Netflix interviewer mindset"
    Netflix interviewers ask: *"Would I trust this person to own a P0 with a 2am page and no escalation?"* — a senior bar dressed in casual clothing.

---

## 🎯 What Netflix tests

| Signal | Where they grade it | How to show it |
|---|---|---|
| **Coding fluency** | Tech screen + coding round | Senior-level cleanness, no LeetCode-y showmanship. Solve, polish, move on. |
| **System design depth** | 2 design rounds | Talk *capacity* (Tbps of video traffic), *partitioning* (geo-CDN), *failure modes*. |
| **Production seniority** | All rounds | "We had X bug at 3am, here's how I rolled back" — narrate the *messy* parts of past projects. |
| **Judgment under ambiguity** | Cross-functional | Disagree calmly. Commit publicly. Show you can handle *vague* asks. |
| **High-trust culture fit** | Culture round | Bias to action, dropping work that's not high-impact, telling teammates the truth. |

---

## 🧩 Patterns that show up most often

| Pattern | Frequency | Why Netflix likes it |
|---|---|---|
| **System design at scale** | ⭐⭐⭐⭐⭐ | The *primary* signal. You can ace coding and fail design and not get an offer. |
| **Hash + heap composition** | ⭐⭐⭐⭐ | Top-K viewing, recommendations. |
| **Trees / DFS** | ⭐⭐⭐⭐ | Standard fluency check. |
| **DP** | ⭐⭐⭐⭐ | A/B test analysis, prediction problems. |
| **Sliding window** | ⭐⭐⭐ | Logs, time-series. |
| **Graphs (BFS/DFS)** | ⭐⭐⭐ | Recommendation graphs, content dependencies. |
| **Concurrency** | ⭐⭐⭐ | Streaming systems are concurrent by nature. |

---

## 📋 The 50 questions

Status: ✅ = full v3 in this bible &nbsp; 📝 = mini-v3 below &nbsp; 🚧 = lands later in Phase 8.

### Arrays & strings (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash map | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Maximum Subarray | <span class="diff-medium">Medium</span> | Kadane's | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 3 | Merge Intervals | <span class="diff-medium">Medium</span> | Sort + sweep | [✅](../../04-patterns/04-merge-intervals.md) |
| 4 | Insert Interval | <span class="diff-medium">Medium</span> | Linear sweep | 🚧 |
| 5 | Meeting Rooms II | <span class="diff-medium">Medium</span> | Min-heap on intervals | 🚧 |
| 6 | Sliding Window Maximum | <span class="diff-hard">Hard</span> | Monotonic deque | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 7 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 8 | Minimum Window Substring | <span class="diff-hard">Hard</span> | Sliding window | 🚧 |
| 9 | Longest Consecutive Sequence | <span class="diff-medium">Medium</span> | Hash set | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 10 | Subarray Sum Equals K | <span class="diff-medium">Medium</span> | Prefix sum + hash | 🚧 |

### Trees & graphs (8)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 11 | Binary Tree Level Order Traversal | <span class="diff-medium">Medium</span> | BFS | 🚧 |
| 12 | Binary Tree Right Side View | <span class="diff-medium">Medium</span> | BFS | 🚧 |
| 13 | Lowest Common Ancestor (Binary Tree) | <span class="diff-medium">Medium</span> | DFS post-order | 🚧 |
| 14 | Number of Islands | <span class="diff-medium">Medium</span> | Grid BFS/DFS | 🚧 |
| 15 | Course Schedule | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 16 | Word Ladder | <span class="diff-hard">Hard</span> | BFS on word graph | 🚧 |
| 17 | Network Delay Time | <span class="diff-medium">Medium</span> | Dijkstra | 🚧 |
| 18 | Cheapest Flights Within K Stops | <span class="diff-medium">Medium</span> | Bellman-Ford | 🚧 |

### Heap & Top-K (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 19 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap / bucket sort | 🚧 |
| 20 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | [📝](#deep-dive-2-find-median-from-data-stream) |
| 21 | Merge K Sorted Lists | <span class="diff-hard">Hard</span> | Min-heap | 🚧 |
| 22 | K Closest Points to Origin | <span class="diff-medium">Medium</span> | Heap / quickselect | 🚧 |
| 23 | Sliding Window Median | <span class="diff-hard">Hard</span> | Two heaps + lazy delete | 🚧 |

### DP (6)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 24 | House Robber | <span class="diff-medium">Medium</span> | 1D DP | 🚧 |
| 25 | Longest Increasing Subsequence | <span class="diff-medium">Medium</span> | Patience / DP | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 26 | Longest Common Subsequence | <span class="diff-medium">Medium</span> | 2D DP | 🚧 |
| 27 | Edit Distance | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |
| 28 | Best Time to Buy and Sell Stock IV | <span class="diff-hard">Hard</span> | DP w/ K transactions | 🚧 |
| 29 | Word Break | <span class="diff-medium">Medium</span> | DP + dict | 🚧 |

### Streaming + design (10) — **Netflix specialty**

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 30 | Design HTTP Rate Limiter | <span class="diff-medium">Medium</span> | Token bucket / sliding window | 🚧 |
| 31 | Design URL Shortener | <span class="diff-medium">Medium</span> | Hash + DB | [✅](../../08-system-design/tier-1-core/01-url-shortener.md) |
| 32 | Design Netflix Recommendations | <span class="diff-hard">Hard</span> | ML pipeline + cache | 🚧 |
| 33 | Design Video Streaming Service | <span class="diff-hard">Hard</span> | CDN + adaptive bitrate | 🚧 |
| 34 | Design A/B Testing Framework | <span class="diff-hard">Hard</span> | Bucket + stats | 🚧 |
| 35 | Design Top K Trending Movies | <span class="diff-medium">Medium</span> | Heap + log streams | 🚧 |
| 36 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |
| 37 | LFU Cache | <span class="diff-hard">Hard</span> | Hash + DLL of DLLs | 🚧 |
| 38 | Logger Rate Limiter | <span class="diff-easy">Easy</span> | Hash + timestamp | 🚧 |
| 39 | Hit Counter | <span class="diff-medium">Medium</span> | Circular buffer | 🚧 |

### Misc / mediums (8)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 40 | 3Sum | <span class="diff-medium">Medium</span> | Sort + two ptrs | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 41 | Container With Most Water | <span class="diff-medium">Medium</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 42 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 43 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 44 | Copy List with Random Pointer | <span class="diff-medium">Medium</span> | Hash / interleave | 🚧 |
| 45 | Valid Parentheses | <span class="diff-easy">Easy</span> | Stack | 🚧 |
| 46 | Daily Temperatures | <span class="diff-medium">Medium</span> | Monotonic stack | 🚧 |
| 47 | Single Number | <span class="diff-easy">Easy</span> | XOR | [✅](../../04-patterns/20-bitwise-xor.md) |

### System-flavored coding (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 48 | Implement strStr (substring search) | <span class="diff-easy">Easy</span> | KMP / Rabin-Karp | [📝](#deep-dive-3-implement-strstr-with-rabin-karp) |
| 49 | Implement Trie (Prefix Tree) | <span class="diff-medium">Medium</span> | Trie | [✅](../../05-advanced/01-tries.md) |
| 50 | Word Search II | <span class="diff-hard">Hard</span> | Trie + DFS | 🚧 |

---

## 🔬 Deep-dives — 3 Netflix-style walkthroughs

These three are picked because:

- **Meeting Rooms II** is Netflix's "do you understand min-heap on intervals?" filter — and a stepping stone to the recommendation-throttle design follow-up.
- **Find Median from Data Stream** is the canonical streaming-DS problem at Netflix's scale (logs, watch-time percentiles).
- **Rabin-Karp** shows the "rolling hash" / streaming-substring intuition that pops up in CDN content-fingerprinting.

---

### Deep-dive 1: Meeting Rooms II

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Netflix</span>

> Given an array of meeting `intervals = [[start, end], ...]`, return the minimum number of rooms required.

#### 📖 Story mode

You run a Netflix HQ floor. Each meeting needs a room from `start` to `end`. How few rooms can you survive with?

#### 🧠 Thinking process

- **Brute force**: simulate every minute. O(max_end · n).
- **Insight**: sort by `start`. Use a **min-heap** keyed on end-times of in-progress meetings. For each new meeting, if the earliest-ending room has freed up by then, *reuse* it. Otherwise, allocate a new room.
- **Why min-heap?** Constant-time peek of "earliest ending" means we know in O(log n) whether reuse is possible.

#### 🐍 Optimal solution

```python
import heapq

def min_meeting_rooms(intervals: list[list[int]]) -> int:
    """Min rooms needed for non-overlapping scheduling."""
    if not intervals:
        return 0
    intervals.sort(key=lambda iv: iv[0])
    end_heap: list[int] = []                 # end-times of in-progress meetings

    for start, end in intervals:
        if end_heap and end_heap[0] <= start:
            heapq.heappop(end_heap)          # reuse the earliest-ending room
        heapq.heappush(end_heap, end)

    return len(end_heap)
```

**Why peek `end_heap[0] <= start`?** A room that *just* freed (end == start) is reusable depending on convention. LC says yes. State the assumption.

#### 🔍 Dry run on `[[0,30],[5,10],[15,20]]`

Sorted: same.

| meeting | heap before | reuse? | heap after |
|---|---|---|---|
| (0,30) | [] | no | [30] |
| (5,10) | [30] | 30 ≤ 5? no | [10,30] |
| (15,20) | [10,30] | 10 ≤ 15? yes — pop 10 | [20,30] |

Answer: 2. ✅

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **Sort + heap** | O(n log n) | O(n) |

#### 🔄 Netflix's classic follow-up

??? question "Now stream-process meetings as they're added (no batch sort)."
    Maintain two heaps — a "future starts" min-heap and an "in-progress ends" min-heap. Tick forward. Same logic, online.

??? question "Now schedule them into the *fewest* rooms, returning *which* room each meeting goes to."
    Same algorithm, but instead of a counter, the heap holds `(end, room_id)`. On reuse, take that room's id. On allocate, mint a new id.

??? question "Generalize to N teams with weighted priority — high-priority team gets a room first."
    Multi-keyed heap: `(priority, end_time)`. Or split into per-team heaps and use round-robin allocation when priorities tie.

#### 🐛 Common bugs

- Sorting by `end` instead of `start` — gives a different (also valid) algorithm but a wrong invariant if you're not careful.
- Using `<` instead of `<=` — depending on convention, may over-allocate.

---

### Deep-dive 2: Find Median from Data Stream

<span class="diff-hard">Hard</span> &nbsp; <span class="company-tag">Netflix</span> &nbsp; <span class="company-tag">Google</span>

> Design `addNum(x)` and `findMedian()` for a stream of integers. Both should be efficient (no full sort per query).

#### 📖 Story mode

Netflix tracks watch-time per session. The data scientists ask: "what's the median session length, *as new sessions complete*?" Must update on every event.

#### 🧠 Thinking process

- **Naive**: maintain sorted list, O(n) insert.
- **Insight**: split the stream into two halves — a **max-heap** for the lower half, **min-heap** for the upper half. Median is the top of one (odd count) or the average of both tops (even count).
- **Invariant**: `len(low) == len(high) or len(low) == len(high) + 1`.

#### 🐍 Optimal solution

```python
import heapq

class MedianFinder:
    def __init__(self) -> None:
        self.low: list[int] = []        # max-heap (negated)
        self.high: list[int] = []       # min-heap

    def addNum(self, num: int) -> None:
        # Always push to low first (negated), then balance into high.
        heapq.heappush(self.low, -num)
        heapq.heappush(self.high, -heapq.heappop(self.low))
        if len(self.high) > len(self.low):
            heapq.heappush(self.low, -heapq.heappop(self.high))

    def findMedian(self) -> float:
        if len(self.low) > len(self.high):
            return -self.low[0]
        return (-self.low[0] + self.high[0]) / 2
```

**The push-then-balance trick** ensures correctness regardless of where `num` belongs — push, then move one across.

#### 🔍 Dry run

`addNum(1) addNum(2) findMedian() addNum(3) findMedian()`

| op | low (max-heap) | high (min-heap) | median |
|---|---|---|---|
| addNum(1) | [-1] | [] | — |
| addNum(2) | [-1] | [2] | — |
| findMedian | — | — | (1+2)/2 = 1.5 |
| addNum(3) | [-2,-1] | [3] | — |
| findMedian | — | — | 2 |

#### ⏱️ Complexity

| Op | Time | Space |
|---|---|---|
| `addNum` | O(log n) | O(n) |
| `findMedian` | O(1) | — |

#### 🔄 Netflix's classic follow-up

??? question "What if the stream is bounded to integers in [0, 100]?"
    Use a fixed-size 101-bucket count array. `addNum` is O(1); `findMedian` is O(100) — effectively constant.

??? question "What if the stream is huge and we only care about *approximate* median?"
    Two options: (a) **t-digest** for O(log n) inserts and approximate-quantile queries; (b) **Reservoir sampling** to keep a uniform sample and compute median there.

??? question "What if you need 99th percentile, not median?"
    Approximate: t-digest. Exact: maintain heaps with the right ratio (top 1% in one heap, bottom 99% in the other).

#### 🐛 Common bugs

- Forgetting to negate in max-heap simulation.
- Off-by-one balance: writing `len(low) >= len(high) + 2` instead of `> len(high)` (sometimes matters by one swap).

---

### Deep-dive 3: Implement strStr (with Rabin-Karp)

<span class="diff-easy">Easy</span> &nbsp; <span class="company-tag">Netflix</span>

> Given strings `haystack` and `needle`, return the index of the first occurrence of `needle` in `haystack`, or -1.

#### 📖 Story mode

Naive matching is O(n · m). Linear time matchers exist (KMP, Z-algorithm). Rabin-Karp uses a **rolling hash** — fast in practice and the gateway intuition for content fingerprinting in CDNs.

#### 🧠 Thinking process

- **Naive**: for each position in haystack, compare m characters. O(n · m).
- **Idea**: hash the needle. Compute a rolling hash of every length-`m` window in the haystack. When the hash matches, do a full character compare to confirm (avoid false positives).
- **Why "rolling"**: O(1) update from window i to window i+1 — subtract leading char, multiply, add trailing char.

#### 🐍 Optimal solution (Rabin-Karp)

```python
def str_str(haystack: str, needle: str) -> int:
    """Index of first occurrence of needle in haystack, or -1."""
    n, m = len(haystack), len(needle)
    if m == 0:
        return 0
    if m > n:
        return -1

    BASE = 257
    MOD  = (1 << 61) - 1
    high_pow = pow(BASE, m - 1, MOD)        # the place-value of the leading char

    needle_h = 0
    window_h = 0
    for i in range(m):
        needle_h = (needle_h * BASE + ord(needle[i])) % MOD
        window_h = (window_h * BASE + ord(haystack[i])) % MOD

    for i in range(n - m + 1):
        if window_h == needle_h and haystack[i:i + m] == needle:
            return i
        if i < n - m:
            window_h = ((window_h - ord(haystack[i]) * high_pow) * BASE
                        + ord(haystack[i + m])) % MOD

    return -1
```

**Why the integrity check?** Hash collisions exist. Even with a 61-bit prime modulus they can happen — verify with a real comparison.

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **Rabin-Karp avg** | O(n + m) | O(1) |
| **Rabin-Karp worst** | O(n · m) | O(1) |
| **KMP** | O(n + m) | O(m) |

#### 🔄 Netflix's classic follow-up

??? question "Detect *all* occurrences (not just the first)."
    Same loop, just append `i` to a result list and don't return early.

??? question "What if haystack is a 10 GB log file streamed from S3?"
    Rabin-Karp still works — process bytes streaming. KMP also works. Don't load the whole file. Acknowledge bandwidth as the bottleneck, not CPU.

??? question "What if you need to find any of K needles in haystack?"
    **Aho-Corasick** automaton: O(n + sum(|needles|)) — build trie + failure links, sweep haystack once. Used in spam filters and CDN content moderation.

#### 🐛 Common bugs

- Forgetting the `% MOD` on intermediate products — overflow ruins the hash.
- Forgetting the integrity check — false positives go unhandled.
- Off-by-one in `high_pow` exponent.

---

## 🗓️ Day-of tips for a Netflix interview

!!! tip "The morning checklist"
    1. **Re-read the [Netflix culture deck](https://about.netflix.com/en/culture)** the night before. Calibrate stories to "freedom + responsibility."
    2. **Re-read your last 2 projects' tradeoffs.** Senior bar = able to defend choices.
    3. **One system design dry-run** out loud — Netflix's primary signal.
    4. **One coding warm-up** — but don't stress LeetCode here.
    5. **Test Webex / Zoom + your video setup**.

### During the interview

| Stage | What to say / do |
|---|---|
| **First 60s** | Restate. Ask 2 *senior-level* clarifying questions (capacity, SLA, failure modes). |
| **Pre-coding (~5 min)** | State approach + tradeoffs. *Mention failure modes.* |
| **Coding (~25 min)** | Narrate. Type clean. Senior code reads like prod. |
| **System design (60 min)** | Capacity → APIs → data model → partitioning → caching → failure modes → metrics. **In that order.** |
| **Behavioral** | "Disagree and commit" stories ready. Be candid about past mistakes. |

### Red & green flags

- 🚩 LeetCode-y showmanship without context.
- 🚩 Inability to defend a past project's choice.
- 🚩 "We did" instead of "I led."
- 🟢 "We hit X failure mode at scale; here's how I led the rollback."
- 🟢 Pushing back on a vague spec — "before I design this, I need to know X."
- 🟢 Naming your *own* tradeoff cost ("this saves latency but costs $X/month at our QPS").

---

## 🔁 Where to go from here

- **Solve the 50** in roughly the order above.
- **System design** is the primary signal — start with [URL Shortener](../../08-system-design/index.md) then build up to streaming-flavored designs.
- **Cross-check** with the [Top 100 by Pattern](../top-100-by-pattern.md).
- **Behavioral** prep at [Behavioral](../../11-behavioral/index.md), tagged for "freedom + responsibility."

> Same six-part shape as [Google 50](google-50.md) and [Meta 50](meta-50.md).
