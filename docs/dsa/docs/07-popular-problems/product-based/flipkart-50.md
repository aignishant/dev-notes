# Flipkart — 50 most-asked questions

> The 50 problems Flipkart (Marketplace, Myntra, Cleartrip) has asked most often. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">Flipkart</span> &nbsp; <span class="phase-status phase-inprogress">Phase 8 — company page</span>

---

## 🏢 What interviewing at Flipkart is like

| Round | Length | Focus |
|---|---|---|
| **OA (HackerEarth)** | 90 min | 2-3 medium problems. |
| **Phone screen** | 60 min | Coding + DS. |
| **Onsite — coding ×2** | 60 min each | Algorithms + scale. |
| **Onsite — system design** | 60 min | E-commerce flavored — order, cart, inventory. |
| **Onsite — hiring manager** | 45 min | Behavioral + project deep-dive. |

**Flipkart style**: India's largest e-com. Bias toward sale-day (Big Billion Days) scaling. Distributed systems thinking + scale numbers. SDE-2 / SDE-3 bar is high — equivalent to FAANG mid-senior.

---

## 🎯 What Flipkart tests

| Signal | Where | How to show |
|---|---|---|
| Coding fluency | All | Standard mediums fast. |
| Scale + sale-day instincts | Design | Inventory consistency, payment idempotency. |
| Trade-off articulation | All | CAP, latency vs consistency. |
| Project depth | Manager | Numbers: latency, traffic, downstream impact. |

---

## 🧩 Patterns Flipkart loves

| Pattern | Frequency | Why |
|---|---|---|
| **Heap top-K** | ⭐⭐⭐⭐⭐ | Search ranking, deals. |
| **DP** | ⭐⭐⭐⭐ | Pricing, coupon optimisation. |
| **Hash + sliding window** | ⭐⭐⭐⭐ | Standard medium. |
| **Graph BFS / DFS** | ⭐⭐⭐⭐ | Catalog, category trees. |
| **Design** | ⭐⭐⭐⭐⭐ | E-com design always present. |

---

## 📋 The 50 questions

### Arrays & strings (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 3 | Maximum Subarray | <span class="diff-medium">Medium</span> | Kadane | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 4 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 5 | Rotate Array | <span class="diff-medium">Medium</span> | Reverse trick | 🚧 |
| 6 | Merge Intervals | <span class="diff-medium">Medium</span> | Sort + sweep | [✅](../../04-patterns/04-merge-intervals.md) |
| 7 | Stock Buy / Sell | <span class="diff-easy">Easy</span> | Greedy | 🚧 |
| 8 | Find Duplicate | <span class="diff-medium">Medium</span> | Floyd's | 🚧 |
| 9 | Set Matrix Zeroes | <span class="diff-medium">Medium</span> | In-place markers | 🚧 |
| 10 | Spiral Matrix | <span class="diff-medium">Medium</span> | Layer-by-layer | 🚧 |

### Linked lists (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 11 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 12 | Merge Two Sorted Lists | <span class="diff-easy">Easy</span> | Two pointers | 🚧 |
| 13 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |
| 14 | Detect Cycle | <span class="diff-easy">Easy</span> | Floyd's | 🚧 |

### Trees (6)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 15 | Level Order Traversal | <span class="diff-medium">Medium</span> | BFS | 🚧 |
| 16 | LCA of Binary Tree | <span class="diff-medium">Medium</span> | Post-order | 🚧 |
| 17 | Validate BST | <span class="diff-medium">Medium</span> | DFS bounds | 🚧 |
| 18 | Serialize / Deserialize | <span class="diff-hard">Hard</span> | BFS | 🚧 |
| 19 | Diameter of Binary Tree | <span class="diff-easy">Easy</span> | Post-order | 🚧 |
| 20 | Category Tree Search | <span class="diff-medium">Medium</span> | DFS + breadcrumb | 🚧 |

### Graphs (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 21 | Number of Islands | <span class="diff-medium">Medium</span> | DFS / BFS | 🚧 |
| 22 | Course Schedule | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 23 | Word Ladder | <span class="diff-hard">Hard</span> | BFS | 🚧 |
| 24 | Cheapest Flights K Stops | <span class="diff-medium">Medium</span> | Bellman-Ford | 🚧 |
| 25 | Network Delay Time | <span class="diff-medium">Medium</span> | Dijkstra | 📝 (see [Uber 50](uber-50.md)) |

### Heap / Top-K (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 26 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap | [✅](../../04-patterns/12-top-k-elements.md) |
| 27 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | [✅](../../04-patterns/09-two-heaps.md) |
| 28 | K Closest Points | <span class="diff-medium">Medium</span> | Heap | 🚧 |
| 29 | Top K Trending Products | <span class="diff-hard">Hard</span> | Heap + decay | 🚧 |

### Backtracking (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 30 | Subsets | <span class="diff-medium">Medium</span> | Backtrack | 🚧 |
| 31 | Permutations | <span class="diff-medium">Medium</span> | Backtrack | 🚧 |
| 32 | Word Search | <span class="diff-medium">Medium</span> | DFS + visited | 🚧 |

### DP (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 33 | Climbing Stairs | <span class="diff-easy">Easy</span> | Fib DP | 🚧 |
| 34 | Coin Change | <span class="diff-medium">Medium</span> | Unbounded knapsack | 🚧 |
| 35 | Word Break | <span class="diff-medium">Medium</span> | DP | 🚧 |
| 36 | Edit Distance | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |
| 37 | LIS | <span class="diff-medium">Medium</span> | DP / patience | 🚧 |

### Search & sort (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 38 | Search in Rotated Sorted Array | <span class="diff-medium">Medium</span> | Modified BS | 🚧 |
| 39 | Find First and Last Position | <span class="diff-medium">Medium</span> | BS variant | 🚧 |
| 40 | Sort Colors | <span class="diff-medium">Medium</span> | Dutch flag | 🚧 |

### Design (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 41 | Design Cart | <span class="diff-medium">Medium</span> | OOP | 🚧 |
| 42 | Design Inventory System | <span class="diff-hard">Hard</span> | Distributed counter | 📝 |
| 43 | Design Coupon Engine | <span class="diff-hard">Hard</span> | Rule engine | 📝 |
| 44 | Design Order Service | <span class="diff-hard">Hard</span> | Saga pattern | 🚧 |
| 45 | Design Payment Gateway | <span class="diff-hard">Hard</span> | Idempotency + retry | 🚧 |
| 46 | Design Search Ranking | <span class="diff-hard">Hard</span> | Inverted idx + score | 🚧 |
| 47 | Design Notification | <span class="diff-hard">Hard</span> | Pub/sub | 🚧 |
| 48 | Design Rate Limiter | <span class="diff-medium">Medium</span> | Token bucket | 🚧 |
| 49 | Design Recommendation | <span class="diff-hard">Hard</span> | Collab filter | 🚧 |
| 50 | Design Big Billion Days Surge | <span class="diff-hard">Hard</span> | Auto-scale + queue | 📝 |

---

## 🔬 Three deep-dives

### Deep-dive 1 — Inventory Reservation under Concurrency

??? question "Story: 1M users hit 'buy' on the same iPhone with 1000 units. Don't oversell."

    Atomic decrement on the inventory counter. Use Redis `DECR` (single-threaded, fast) or DB `SELECT FOR UPDATE`. Reservation has a TTL — if checkout fails, release.

```python
import time
from threading import Lock

class Inventory:
    def __init__(self):
        self.stock: dict[str, int] = {}
        self.reservations: dict[str, tuple[str, float]] = {}  # res_id → (sku, expires_at)
        self.lock = Lock()

    def add(self, sku: str, qty: int) -> None:
        with self.lock:
            self.stock[sku] = self.stock.get(sku, 0) + qty

    def reserve(self, sku: str, res_id: str, ttl_sec: float = 600) -> bool:
        with self.lock:
            self._evict_expired()
            if self.stock.get(sku, 0) <= 0:
                return False
            self.stock[sku] -= 1
            self.reservations[res_id] = (sku, time.monotonic() + ttl_sec)
            return True

    def confirm(self, res_id: str) -> bool:
        with self.lock:
            if res_id not in self.reservations:
                return False
            del self.reservations[res_id]
            return True

    def release(self, res_id: str) -> None:
        with self.lock:
            entry = self.reservations.pop(res_id, None)
            if entry:
                sku, _ = entry
                self.stock[sku] += 1

    def _evict_expired(self) -> None:
        now = time.monotonic()
        expired = [r for r, (_, t) in self.reservations.items() if t < now]
        for r in expired:
            sku, _ = self.reservations.pop(r)
            self.stock[sku] += 1
```

??? abstract "Complexity"

    O(1) per `reserve`/`confirm`/`release`. `_evict_expired` is O(R); make it lazy or run as a background sweep.

??? tip "Flipkart follow-up: 'how does this scale across 50 servers?'"

    Move state to Redis with `DECR` returning new value. Lua script makes "decr if positive, else fail" atomic. Distributed locks (Redlock) only if cross-region.

---

### Deep-dive 2 — Coupon Rule Engine

??? question "Story: 'Get 10% off Mobiles up to ₹1500, only for SBI cards, only for Plus members.' Build a rule engine that evaluates this against a cart."

    Compose-able predicates + actions. Each rule is `(predicates, action, priority)`. Evaluate predicates; apply highest-priority matching rule's action.

```python
from dataclasses import dataclass, field
from typing import Callable

@dataclass
class Cart:
    user_id: int
    items: list[dict] = field(default_factory=list)
    payment_method: str = ""
    is_plus: bool = False

@dataclass
class Rule:
    name: str
    predicates: list[Callable[[Cart], bool]]
    discount_fn: Callable[[Cart], float]
    priority: int = 0

class CouponEngine:
    def __init__(self):
        self.rules: list[Rule] = []

    def register(self, rule: Rule) -> None:
        self.rules.append(rule)
        self.rules.sort(key=lambda r: -r.priority)

    def best_discount(self, cart: Cart) -> tuple[str, float]:
        for rule in self.rules:
            if all(p(cart) for p in rule.predicates):
                return rule.name, rule.discount_fn(cart)
        return "no_offer", 0.0

# Usage
def is_mobile_cart(c: Cart) -> bool:
    return any(item["category"] == "Mobile" for item in c.items)

def is_sbi(c: Cart) -> bool:
    return c.payment_method == "SBI"

def is_plus_member(c: Cart) -> bool:
    return c.is_plus

mobile_offer = Rule(
    name="MOBILE_SBI_PLUS_10PCT",
    predicates=[is_mobile_cart, is_sbi, is_plus_member],
    discount_fn=lambda c: min(1500.0, 0.1 * sum(i["price"] for i in c.items if i["category"] == "Mobile")),
    priority=10,
)
```

??? abstract "Complexity"

    O(R · P) per cart, R rules × P predicates. Index by category for early elimination at scale.

??? tip "Flipkart follow-up: 'we have 5000 active coupons during BBD'"

    Pre-bucket rules by qualifying category (`Mobile`, `Apparel`, …) and payment method. Only evaluate rules whose buckets intersect the cart. Reduces from 5000 to ~50.

---

### Deep-dive 3 — Big Billion Days Surge Handling

??? question "Story: regular load is 50k req/s. BBD opens at midnight and hits 2M req/s in 30 seconds. Don't fall over."

    **Pre-warm + queue + degrade**. Auto-scale ahead of time, put all writes through a durable queue, downgrade non-critical features (recommendations, reviews).

```python
# Sketch — three layers of protection
class SurgeShield:
    def __init__(self, edge_rate: int, queue_rate: int):
        self.edge_rate = edge_rate    # token bucket at API gateway
        self.queue_rate = queue_rate  # internal worker rate
        self.dropped = 0
        self.queued = 0

    def handle_request(self, req: dict, queue) -> str:
        # Layer 1 — edge token bucket
        if not self._allow_at_edge():
            self.dropped += 1
            return "RATE_LIMITED"
        # Layer 2 — durable queue
        queue.put(req)
        self.queued += 1
        return "ACCEPTED"

    def _allow_at_edge(self) -> bool:
        # placeholder — same algorithm as Stripe rate limiter
        return True
```

??? tip "Flipkart follow-up: 'what gets degraded first?'"

    Reverse-priority list: turn off recommendations → personalised search → image-rich product cards → reviews. Checkout + payment NEVER degrade.

---

## 🛡️ Day-of tips

- **Big Billion Days = guaranteed talking point**. Have specific numbers: 1.4B requests, 5M concurrent users, 200M page views.
- **Idempotency stories**: payment, order placement — they'll dig into "what if the network blips after 200ms".
- **India-scale realities**: weak network, low-end devices. Mention payload reduction, image compression in design rounds.
- **Behavioral: "biggest production incident"**. Have one with measured impact, not just "we recovered".
