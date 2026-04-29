# Stripe — 50 most-asked questions

> The 50 problems Stripe has asked most often, with the patterns behind them and what the interviewer is grading. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">Stripe</span> &nbsp; <span class="phase-status phase-done">Phase 8 — Company list</span>

---

## 📖 How this page is organized

1. **What interviewing here is like**.
2. **What this company tests**.
3. **Common patterns**.
4. **The 50 questions**.
5. **Deep-dives** — 3 representative problems.
6. **Day-of tips**.

---

## 🏢 What interviewing at Stripe is like

### Rounds (typical SWE onsite — 2026)

Stripe's interview style is famously *unique* — they're API-first, payments-first, and run **practical / project-style coding** instead of pure algorithms.

| Round | Length | Focus |
|---|---|---|
| **Recruiter screen** | 30 min | Background + Stripe values. |
| **Technical phone screen** | 60 min | Build something small in your editor. **Not LeetCode.** Open API parsing, simple service implementation. |
| **Onsite — pair programming ×2** | 60 min each | Work *with* the interviewer on a real-feeling problem. Often extending a small codebase, not solving a fresh problem. |
| **Onsite — system design** | 60 min | API design + data modeling. Stripe-flavored: idempotency, retries, audit trails. |
| **Onsite — bug squash** | 60 min | Given buggy code, find and fix bugs while writing tests. |
| **Onsite — culture / values** | 45 min | Stripe's "rigorous + trusting" culture. |

### What "the Stripe style" actually means

- **API design over algorithms.** "Design the `Charge` resource." "How does this API handle partial failures?"
- **Idempotency, idempotency, idempotency.** Every Stripe problem secretly tests "what if this request is replayed?"
- **Money math is exact.** Use integers (cents/satoshis), not floats. They'll fail you for `0.1 + 0.2 != 0.3`.
- **Reading existing code is a real skill.** Bug-squash and pair rounds give you ~200 lines of code; you must read fluently.
- **Test-driven mindset.** Write tests *first* in pair rounds. Stripe's prod codebase is heavily tested.

!!! tip "The Stripe interviewer mindset"
    Stripe interviewers ask: *"Could this person ship a payment endpoint that *never* takes money twice?"* The answer is correctness obsession, idempotency by design, and tests as a love language.

---

## 🎯 What Stripe tests

| Signal | Where they grade it | How to show it |
|---|---|---|
| **Coding fluency in a real editor** | Pair + bug squash | No whiteboard pseudocode. Real, runnable code. |
| **API design judgment** | System design | RESTful, idempotent, well-versioned. |
| **Correctness obsession** | All rounds | Edge cases for *every* function. Currency math in cents. |
| **Test discipline** | Pair + bug squash | Write tests before production code (or alongside). |
| **Reading code fluently** | Bug squash | Skim 200 lines, find the bug in 10 min. |
| **Distributed thinking** | System design | Retries, idempotency keys, eventually-consistent caches. |

---

## 🧩 Patterns that show up most often

| Pattern | Frequency | Why Stripe likes it |
|---|---|---|
| **API design / OOP** | ⭐⭐⭐⭐⭐ | Their primary signal. |
| **Hash map composition** | ⭐⭐⭐⭐ | Idempotency-key tracking. |
| **Trees** | ⭐⭐⭐ | Light but present (parsing, ledgers). |
| **String parsing / state machines** | ⭐⭐⭐⭐ | API request parsers, currency parsers. |
| **Sliding window** | ⭐⭐⭐ | Rate-limiting. |
| **Graph traversal** | ⭐⭐⭐ | Money-flow graphs (account-to-account). |
| **Concurrency (locks, atomics)** | ⭐⭐⭐⭐ | Charges *must* be atomic. |
| **DP** | ⭐⭐ | Rare; sometimes a fraud-detection variant. |
| **Math / number theory** | ⭐⭐⭐ | Currency conversion, decimal precision. |

---

## 📋 The 50 questions

Status: ✅ = full v3 in this bible &nbsp; 📝 = mini-v3 below &nbsp; 🚧 = lands later in Phase 8.

Stripe's questions are unusual — many are *miniature systems* you build in 60 min, not single-function LeetCode. The list below mixes both.

### Practical / mini-systems (10) — **Stripe specialty**

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Build an HTTP request parser | <span class="diff-medium">Medium</span> | State machine | 🚧 |
| 2 | Implement a simple API server | <span class="diff-medium">Medium</span> | OOP + dispatch | 🚧 |
| 3 | Implement an event emitter | <span class="diff-medium">Medium</span> | Hash + callbacks | 🚧 |
| 4 | Build a JSON parser | <span class="diff-medium">Medium</span> | Recursive descent | 🚧 |
| 5 | Implement an idempotency key store | <span class="diff-medium">Medium</span> | Hash + TTL | [📝](#deep-dive-1-idempotency-key-store) |
| 6 | Currency conversion service | <span class="diff-medium">Medium</span> | Graph (BFS / DFS) | [📝](#deep-dive-2-currency-conversion-graph) |
| 7 | Implement retry with exponential backoff | <span class="diff-medium">Medium</span> | Loop + jitter | 🚧 |
| 8 | Implement a rate limiter (token bucket) | <span class="diff-medium">Medium</span> | Bucket + refill | 🚧 |
| 9 | Implement a circuit breaker | <span class="diff-medium">Medium</span> | State machine | 🚧 |
| 10 | Implement a timer / scheduler | <span class="diff-medium">Medium</span> | Min-heap by deadline | 🚧 |

### Strings & parsing (8)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 11 | String to Integer (atoi) | <span class="diff-medium">Medium</span> | State machine | 🚧 |
| 12 | Valid Number | <span class="diff-hard">Hard</span> | State machine / regex | 🚧 |
| 13 | Parse Lisp Expression | <span class="diff-hard">Hard</span> | Recursive descent | 🚧 |
| 14 | Decode String | <span class="diff-medium">Medium</span> | Stack | 🚧 |
| 15 | Basic Calculator II | <span class="diff-medium">Medium</span> | Stack + precedence | 🚧 |
| 16 | Basic Calculator | <span class="diff-hard">Hard</span> | Stack + parens | 🚧 |
| 17 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 18 | Group Anagrams | <span class="diff-medium">Medium</span> | Hash + sorted-key | 🚧 |

### Hash + design (7)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 19 | Two Sum | <span class="diff-easy">Easy</span> | Hash | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 20 | Insert Delete GetRandom O(1) | <span class="diff-medium">Medium</span> | Hash + array | 🚧 |
| 21 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |
| 22 | LFU Cache | <span class="diff-hard">Hard</span> | Hash + DLL of DLLs | 🚧 |
| 23 | Logger Rate Limiter | <span class="diff-easy">Easy</span> | Hash + timestamp | 🚧 |
| 24 | Design Hit Counter | <span class="diff-medium">Medium</span> | Circular buffer | 🚧 |
| 25 | Design In-Memory File System | <span class="diff-hard">Hard</span> | Trie of nodes | 🚧 |

### Money / number math (5) — **Stripe specialty**

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 26 | Add Two Numbers (linked list) | <span class="diff-medium">Medium</span> | Carry + dummy | 🚧 |
| 27 | Multiply Strings | <span class="diff-medium">Medium</span> | Schoolbook + carry | 🚧 |
| 28 | Plus One (large integer) | <span class="diff-easy">Easy</span> | Carry | 🚧 |
| 29 | Fraction to Recurring Decimal | <span class="diff-medium">Medium</span> | Long division + hash | [📝](#deep-dive-3-fraction-to-recurring-decimal) |
| 30 | Pow(x, n) | <span class="diff-medium">Medium</span> | Fast exponentiation | 🚧 |

### Trees (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 31 | Binary Tree Level Order Traversal | <span class="diff-medium">Medium</span> | BFS | 🚧 |
| 32 | Lowest Common Ancestor | <span class="diff-medium">Medium</span> | DFS post-order | 🚧 |
| 33 | Validate BST | <span class="diff-medium">Medium</span> | DFS + bounds | 🚧 |
| 34 | Serialize / Deserialize Binary Tree | <span class="diff-hard">Hard</span> | DFS + queue | 🚧 |

### Graphs (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 35 | Number of Islands | <span class="diff-medium">Medium</span> | Grid BFS/DFS | 🚧 |
| 36 | Course Schedule | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 37 | Account Merge | <span class="diff-medium">Medium</span> | Union-find | 🚧 |

### Concurrency (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 38 | Print in Order | <span class="diff-easy">Easy</span> | Semaphores | 🚧 |
| 39 | Bounded Blocking Queue | <span class="diff-medium">Medium</span> | Mutex + condvars | 🚧 |
| 40 | Building H2O | <span class="diff-medium">Medium</span> | Barriers + semaphores | 🚧 |

### Misc / fundamentals (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 41 | Maximum Subarray | <span class="diff-medium">Medium</span> | Kadane's | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 42 | Best Time to Buy and Sell Stock | <span class="diff-easy">Easy</span> | Running min | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 43 | Merge Intervals | <span class="diff-medium">Medium</span> | Sort + sweep | [✅](../../04-patterns/04-merge-intervals.md) |
| 44 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 45 | Valid Parentheses | <span class="diff-easy">Easy</span> | Stack | 🚧 |
| 46 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap | 🚧 |
| 47 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | 🚧 |
| 48 | Word Break | <span class="diff-medium">Medium</span> | DP + dictionary | 🚧 |
| 49 | Longest Palindromic Substring | <span class="diff-medium">Medium</span> | Expand-around-center | 🚧 |
| 50 | Single Number | <span class="diff-easy">Easy</span> | XOR | [✅](../../04-patterns/20-bitwise-xor.md) |

---

## 🔬 Deep-dives — 3 Stripe-style walkthroughs

These three are picked because:

- **Idempotency Key Store** is *the* Stripe canonical question — they invented the modern usage of idempotency keys in payments APIs.
- **Currency Conversion** is the Stripe-flavored graph problem — directed weighted graph + safety guarantees.
- **Fraction to Recurring Decimal** is the deceptively-deep money-math problem — string formatting + cycle detection.

---

### Deep-dive 1: Idempotency Key Store

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Stripe</span>

> Implement `process(key, request) -> response`. If the same `key` arrives twice within a TTL, return the cached response instead of re-executing.

#### 📖 Story mode

A merchant calls Stripe's `POST /charges`. The network drops the response. They retry with the *same* idempotency key. Stripe must not charge twice — and must return the *same* response.

#### 🧠 Thinking process

- **Naive**: hash map `key -> response`. Works for a single host; explodes across a fleet.
- **Distributed correct**: use a key-value store (Redis / Postgres) with `INSERT ... ON CONFLICT DO NOTHING` semantics. The first writer wins.
- **Race**: between "lookup" and "insert", two requests can both proceed. Solution: atomic insert-or-fetch using DB unique constraint or Redis `SETNX`.
- **TTL**: idempotency keys are short-lived (24h is typical at Stripe). Avoid unbounded growth.

#### 🐍 Optimal solution (single-host sketch)

```python
import threading, time

class IdempotencyStore:
    def __init__(self, ttl_sec: int = 24 * 3600) -> None:
        self.ttl = ttl_sec
        # key -> (response, expires_at)
        self.store: dict[str, tuple[object, float]] = {}
        self.locks: dict[str, threading.Lock] = {}
        self.global_lock = threading.Lock()

    def _lock_for(self, key: str) -> threading.Lock:
        with self.global_lock:
            if key not in self.locks:
                self.locks[key] = threading.Lock()
            return self.locks[key]

    def process(self, key: str, request, handler) -> object:
        # First, fast cache hit (no lock)
        if key in self.store:
            resp, exp = self.store[key]
            if exp > time.time():
                return resp

        # Cache miss — serialize identical keys behind a per-key lock
        with self._lock_for(key):
            # Double-check under lock
            if key in self.store and self.store[key][1] > time.time():
                return self.store[key][0]

            resp = handler(request)            # the *real* work, called once
            self.store[key] = (resp, time.time() + self.ttl)
            return resp
```

**Why per-key locking?** Locking globally would serialize *all* requests. Per-key locks let unrelated keys proceed concurrently while still preventing duplicate execution for the same key.

#### 🔄 Stripe's classic follow-up

??? question "Now make this distributed across 100 hosts."
    Use a shared key-value store. Atomic insert with `INSERT ... ON CONFLICT DO NOTHING` (Postgres) or `SETNX key request_signature` (Redis). The "winner" executes; others poll for the response.

??? question "What if the request body differs but the key is the same?"
    Stripe's actual behavior: store a hash of the request body alongside the response. On replay with same key but different body, return **HTTP 409 Conflict** — *not* a 200 with stale data. Critical for safety.

??? question "What about request/response races where the response doesn't make it back?"
    Idempotency keys solve *exactly* this. The retry returns the cached response, even if the original response failed in transit.

??? question "How do you handle TTL expiry of an in-flight request?"
    Lock-and-write the response *before* clearing TTL on completion. Don't return TTL-expired entries — treat them as cache misses (which then re-execute, possibly double-charging — bad). Better: never TTL-expire in-flight ops, only completed ones.

#### 🐛 Common bugs

- Storing only the response, not the request hash — silently masks bugs.
- Not double-checking under the lock — race between cache miss and acquire.
- TTL = 0 (no expiry) — unbounded memory growth.

---

### Deep-dive 2: Currency Conversion graph

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Stripe</span>

> Given exchange rates `[(from, to, rate), ...]` (directed, weighted), answer queries `convert(amount, from, to) -> amount_in_to`.

#### 📖 Story mode

Stripe needs to convert USD → INR but only has direct USD → EUR and EUR → INR rates. Multiply along the path: `usd_amt * rate(USD→EUR) * rate(EUR→INR)`. That's a graph traversal.

#### 🧠 Thinking process

- **Build a graph**: each currency is a node; each rate is a directed weighted edge (and add reverse `1/rate`).
- **Convert**: BFS/DFS from `from` to `to`, multiplying weights along the path.
- **Subtle**: prefer the *first* path found (BFS) for predictability; multiple paths may give slightly different rates due to float drift.

#### 🐍 Optimal solution

```python
from collections import defaultdict, deque

class CurrencyGraph:
    def __init__(self, rates: list[tuple[str, str, float]]) -> None:
        self.g: dict[str, list[tuple[str, float]]] = defaultdict(list)
        for u, v, r in rates:
            self.g[u].append((v, r))
            self.g[v].append((u, 1.0 / r))      # add reverse for 2-way conversion

    def convert(self, amount: float, src: str, dst: str) -> float:
        if src == dst:
            return amount
        if src not in self.g or dst not in self.g:
            raise KeyError("unknown currency")

        # BFS keeping accumulated multiplier along the path
        visited: set[str] = {src}
        queue: deque[tuple[str, float]] = deque([(src, 1.0)])
        while queue:
            node, mult = queue.popleft()
            for nbr, w in self.g[node]:
                if nbr in visited:
                    continue
                if nbr == dst:
                    return amount * mult * w
                visited.add(nbr)
                queue.append((nbr, mult * w))

        raise ValueError(f"no path from {src} to {dst}")
```

**Why floats and not Decimal?** Production Stripe uses `Decimal` for *settlement*; for FX *quotes* (this problem) floats are acceptable, with explicit precision rounding at the boundary.

#### 🔄 Stripe's classic follow-up

??? question "What if there are arbitrage cycles (USD → EUR → JPY → USD with profit)?"
    **Bellman-Ford on log-rates**: take `log(rate)` for each edge; an arbitrage exists iff there's a *positive*-weight cycle, i.e., a negative-weight cycle in `-log(rate)`. Bellman-Ford detects negative cycles.

??? question "How do you handle stale rates?"
    Stamp each edge with a timestamp. Reject conversions if any edge on the chosen path is older than `T`. Or weight paths by recency.

??? question "How would you scale this to 200 currencies × 200 currencies × 1M conversions/sec?"
    Precompute the *triangulated* table — for every (from, to) pair, store the canonical-path multiplier. Update on every rate change. O(n²) memory; O(1) lookup.

#### 🐛 Common bugs

- Forgetting the reverse edges — `INR → USD` queries fail.
- Using DFS without visited-tracking — infinite loop.

---

### Deep-dive 3: Fraction to Recurring Decimal

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Stripe</span>

> Given numerator and denominator, return the fraction as a string. If repeating, enclose the repeating part in parentheses. Example: `1/6 = "0.1(6)"`.

#### 📖 Story mode

Stripe shows merchants their FX rates. `1/3 = 0.3333...` should render as `0.(3)`. Long division done correctly until you see a remainder repeat.

#### 🧠 Thinking process

- **Integer part**: `n // d`. Handle sign separately.
- **Fractional part**: long division, but track every remainder we've seen. When a remainder repeats, we've found the cycle start — wrap the digits from there in parens.
- **Hash map**: `remainder -> position in output where this remainder first appeared`.

#### 🐍 Optimal solution

```python
def fraction_to_decimal(n: int, d: int) -> str:
    if n == 0:
        return "0"
    if d == 0:
        raise ZeroDivisionError

    sign = "-" if (n < 0) ^ (d < 0) else ""
    n, d = abs(n), abs(d)

    integer, rem = divmod(n, d)
    if rem == 0:
        return sign + str(integer)

    out: list[str] = [sign + str(integer), "."]
    seen: dict[int, int] = {}                  # remainder -> index into out

    while rem != 0:
        if rem in seen:
            idx = seen[rem]
            out.insert(idx, "(")
            out.append(")")
            return "".join(out)
        seen[rem] = len(out)
        rem *= 10
        digit, rem = divmod(rem, d)
        out.append(str(digit))

    return "".join(out)
```

**Why hash map of remainders?** Once a remainder repeats, the entire division pattern from that point on repeats — that's the *definition* of a recurring decimal.

#### 🔍 Dry run on `n=1, d=6`

- integer = 0, rem = 1.
- "0.", seen = {}.
- iter 1: seen[1] = 2 (out = ["0", "."]). rem = 10. digit = 1, rem = 4. out = ["0", ".", "1"].
- iter 2: seen[4] = 3. rem = 40. digit = 6, rem = 4. out = ["0", ".", "1", "6"].
- iter 3: rem = 4, *seen* — insert "(" at index 3, append ")". out = ["0", ".", "1", "(", "6", ")"].

Result: `"0.1(6)"`. ✅

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **Long div + hash** | O(d) | O(d) |

(O(d) because the cycle length is bounded by `d-1` distinct remainders.)

#### 🔄 Stripe's classic follow-up

??? question "What if numbers can be very large (Python OK, but C/Java overflow)?"
    Use big-integer libraries. Mention this explicitly.

??? question "How would you do this for binary or hex output?"
    Replace `* 10` with `* 2` or `* 16`. The cycle-detection mechanic is identical.

??? question "How would you *only detect* whether a fraction is recurring, without producing the digits?"
    `n / gcd(n,d) is recurring iff d / gcd(n,d) has prime factors other than 2 and 5`. Pure number theory — a much faster test.

#### 🐛 Common bugs

- Not handling the negative sign before the abs() call.
- Forgetting to insert "(" *before* appending the digit at that step.
- Using regular division `/` instead of `divmod` — float imprecision corrupts the hash key.

---

## 🗓️ Day-of tips for a Stripe interview

!!! tip "The morning checklist"
    1. **Sleep 8 hours**.
    2. **Re-read** Stripe's [API design guide](https://stripe.com/docs/api) — even just skim. Their interview *is* their API.
    3. **Set up your editor** — Stripe expects you to code in your normal env, not a whiteboard. Configure tests to run in <5s.
    4. **Practice writing tests first** — TDD muscle memory pays off in pair rounds.
    5. **Re-read your favorite past project's API** — they'll ask "why did you make that endpoint POST not PUT?"

### During the interview

| Stage | What to say / do |
|---|---|
| **First 60s** | Restate. **Ask about idempotency, retries, partial failures.** That's the Stripe bingo. |
| **Pre-coding (~5 min)** | Sketch the API signature *before* the body. |
| **Coding (~25 min)** | **Write tests as you go.** Stripe loves it. |
| **Bug squash** | Read the whole codebase silently for 3 min before doing anything. |
| **System design** | API design → data model → idempotency → retry semantics → audit log. |

### Red & green flags

- 🚩 Using floats for currency math.
- 🚩 Not asking about idempotency.
- 🚩 Skipping test writing in pair rounds.
- 🟢 Asking "what should happen on retry?" before writing a line.
- 🟢 Writing tests *first* in pair rounds.
- 🟢 Naming a real API design tradeoff ("PUT is idempotent so this should be PUT").

---

## 🔁 Where to go from here

- **Solve the 50** in roughly the order above. Practice in your *real* editor, not LeetCode's.
- **Read** Stripe's [engineering blog](https://stripe.com/blog/engineering) — it's calibration for their interview style.
- **Cross-check** with the [Top 100 by Pattern](../top-100-by-pattern.md).
- **System design** — the [URL Shortener](../../08-system-design/index.md) page; expand to "design a payments API" mentally.

> Same six-part shape as [Google 50](google-50.md) and [Meta 50](meta-50.md). Stripe's questions are unusually practical-systems-flavored — the shape is identical, but the *content* is API-and-correctness-first.
