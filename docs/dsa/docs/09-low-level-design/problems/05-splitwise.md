# Design Splitwise

> Track shared expenses across friends and minimise the number of settlements. The LLD problem that's secretly a graph problem.

<span class="phase-status phase-done">Phase 13 — classic LLD</span>

---

## 🎤 Problem

> *"Design a Splitwise-like expense sharing app. Users add expenses across groups, splitting them equally / unequally / by percentage / by share. Show each person's net balance. Suggest the **minimum number of transactions** to settle up."*

A 30-45 minute LLD round. Interviewer expects:

1. **Clarifying questions** (split types? groups? currency?).
2. **Class diagram** for User / Expense / Group / Splits.
3. **Balance graph**: who owes whom.
4. **Settlement minimisation** — the algorithm twist.

---

## ❓ Clarifying questions

1. **Split types?** Equal, exact amounts, percentage, by shares (units)?
2. **Groups?** Friends-only, or grouped (Trip, Apartment)?
3. **Currency?** Single currency or multi?
4. **Settlements?** Manual ("I paid Alice $20") or auto-suggested?
5. **History?** Need an activity feed?
6. **Recurring expenses?** (rent, utilities)
7. **Notifications?** Out of scope unless asked.

**Default assumptions**:

- 4 split types (EQUAL, EXACT, PERCENT, SHARES).
- Single currency (cents).
- Both individual and group expenses.
- Auto-suggest minimum settlements.

---

## 🏛️ Class design

### Enums + value objects

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import heapq
import uuid


class SplitType(Enum):
    EQUAL   = "EQUAL"
    EXACT   = "EXACT"
    PERCENT = "PERCENT"
    SHARES  = "SHARES"


@dataclass
class User:
    id: str
    name: str
    email: str
```

### Splits (Strategy pattern)

```python
@dataclass
class Split:
    """How much one user owes for an expense."""
    user_id: str
    amount_cents: int        # positive = owes


class SplitStrategy(ABC):
    @abstractmethod
    def compute(self, total_cents: int, parties: list[dict]) -> list[Split]:
        """parties = list of {'user_id': ..., 'value': X}; meaning depends on strategy."""


class EqualSplit(SplitStrategy):
    def compute(self, total_cents, parties):
        n = len(parties)
        share = total_cents // n
        rem = total_cents - share * n              # distribute remainder cents
        out = [Split(p["user_id"], share) for p in parties]
        for i in range(rem):
            out[i].amount_cents += 1
        return out


class ExactSplit(SplitStrategy):
    def compute(self, total_cents, parties):
        s = sum(p["value"] for p in parties)
        if s != total_cents:
            raise ValueError(f"exact splits sum {s} != total {total_cents}")
        return [Split(p["user_id"], p["value"]) for p in parties]


class PercentSplit(SplitStrategy):
    def compute(self, total_cents, parties):
        if sum(p["value"] for p in parties) != 100:
            raise ValueError("percentages must sum to 100")
        return [Split(p["user_id"], total_cents * p["value"] // 100) for p in parties]


class SharesSplit(SplitStrategy):
    """e.g. roommate split 2:1:1 — heavier eater pays more."""
    def compute(self, total_cents, parties):
        total_shares = sum(p["value"] for p in parties)
        return [
            Split(p["user_id"], total_cents * p["value"] // total_shares)
            for p in parties
        ]
```

### Expense

```python
@dataclass
class Expense:
    id: str
    description: str
    total_cents: int
    paid_by: str                 # user_id
    splits: list[Split]
    group_id: str | None = None
```

### BalanceSheet — the heart of the system

```python
class BalanceSheet:
    """Tracks net balances. balances[A][B] = amount A owes B (positive)."""

    def __init__(self):
        self.balances: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def add_expense(self, e: Expense):
        for s in e.splits:
            if s.user_id == e.paid_by:
                continue                              # payer's own share — no debt
            # s.user_id owes e.paid_by s.amount_cents
            self.balances[s.user_id][e.paid_by] += s.amount_cents
            # Cancel out reverse direction immediately
            self._normalize(s.user_id, e.paid_by)

    def _normalize(self, a: str, b: str):
        """If A owes B and B owes A, net them out."""
        ab = self.balances[a][b]
        ba = self.balances[b][a]
        if ab > ba:
            self.balances[a][b] = ab - ba
            self.balances[b][a] = 0
        else:
            self.balances[b][a] = ba - ab
            self.balances[a][b] = 0

    def net_balance(self, user_id: str) -> int:
        """Positive = others owe them; negative = they owe."""
        owed_to_them = sum(self.balances[u][user_id] for u in self.balances)
        they_owe = sum(self.balances[user_id].values())
        return owed_to_them - they_owe

    def show(self, user_id: str) -> dict[str, int]:
        """Per-counterparty balances. + = they owe me; - = I owe them."""
        result: dict[str, int] = {}
        for other in {*self.balances, *self.balances[user_id]}:
            net = self.balances[other].get(user_id, 0) - self.balances[user_id].get(other, 0)
            if net != 0:
                result[other] = net
        return result
```

### Group

```python
@dataclass
class Group:
    id: str
    name: str
    members: set[str] = field(default_factory=set)
    expenses: list[Expense] = field(default_factory=list)
```

### The service (Facade)

```python
class SplitwiseService:
    def __init__(self):
        self.users: dict[str, User] = {}
        self.groups: dict[str, Group] = {}
        self.sheet = BalanceSheet()

    def add_expense(
        self,
        description: str,
        total_cents: int,
        paid_by: str,
        strategy: SplitStrategy,
        parties: list[dict],
        group_id: str | None = None,
    ) -> Expense:
        splits = strategy.compute(total_cents, parties)
        e = Expense(str(uuid.uuid4()), description, total_cents, paid_by, splits, group_id)
        if group_id is not None:
            self.groups[group_id].expenses.append(e)
        self.sheet.add_expense(e)
        return e

    def settle_up(self, payer: str, payee: str, amount_cents: int):
        """Manual settlement: payer hands payee cash → reduce debt."""
        self.sheet.balances[payer][payee] -= amount_cents
        self.sheet._normalize(payer, payee)
```

---

## 💸 Minimum settlements (the graph problem)

> *"Given a list of net balances, find the **fewest transactions** that zero out every account."*

This is **NP-hard** in general (subset-sum reduction), but a **greedy max-heap** works well in practice and matches what real Splitwise does.

```python
def min_settlements(net: dict[str, int]) -> list[tuple[str, str, int]]:
    """
    net[user] = positive (owed) / negative (owes).
    Returns list of (debtor, creditor, amount) transactions.
    """
    creditors = [(-v, u) for u, v in net.items() if v > 0]   # max-heap (negate)
    debtors   = [( v, u) for u, v in net.items() if v < 0]   # min-heap (already neg)
    heapq.heapify(creditors)
    heapq.heapify(debtors)

    result: list[tuple[str, str, int]] = []
    while creditors and debtors:
        cred_neg, cred_user = heapq.heappop(creditors)
        debt_val, debt_user = heapq.heappop(debtors)
        cred_amt, debt_amt = -cred_neg, -debt_val           # both positive

        pay = min(cred_amt, debt_amt)
        result.append((debt_user, cred_user, pay))

        if cred_amt > pay:
            heapq.heappush(creditors, (-(cred_amt - pay), cred_user))
        if debt_amt > pay:
            heapq.heappush(debtors,  (-(debt_amt - pay), debt_user))

    return result
```

??? note "Why greedy isn't optimal"

    Optimal settlement minimisation is NP-hard (reduces to subset-sum). The greedy heap approach is O(n log n) and produces ≤ n-1 transactions, which is the upper bound. For real apps, it's good enough — Splitwise itself uses a similar approach.

---

## 🧪 Walkthrough

```python
svc = SplitwiseService()
svc.users = {
    "A": User("A", "Alice",  "a@x"),
    "B": User("B", "Bob",    "b@x"),
    "C": User("C", "Carol",  "c@x"),
}

# Alice pays $30 dinner; split equally 3 ways
svc.add_expense("Dinner", 3000, "A", EqualSplit(),
                [{"user_id": "A"}, {"user_id": "B"}, {"user_id": "C"}])
# → B owes A 1000, C owes A 1000

# Bob pays $15 cab; split equally
svc.add_expense("Cab", 1500, "B", EqualSplit(),
                [{"user_id": "A"}, {"user_id": "B"}, {"user_id": "C"}])
# → A owes B 500, C owes B 500.
#   But B already owed A 1000 → netted to: B owes A 500, C owes B 500.

# Net balances
nets = {u: svc.sheet.net_balance(u) for u in svc.users}
# A: +500   B: 0   C: -500

print(min_settlements(nets))
# [('C', 'A', 500)]   ← single transaction settles everything
```

---

## 🎯 Patterns + SOLID applied

| Decision | Pattern / principle |
|---|---|
| `SplitStrategy` ABC + 4 impls | **Strategy** + OCP — add `ItemizedSplit` later |
| `BalanceSheet` separate from `Expense` | **Single Responsibility** |
| `SplitwiseService` is the public surface | **Facade** |
| `_normalize` keeps balances canonical | Invariant — at most one direction per pair |
| `min_settlements` is pure | Easy to test in isolation |

---

## 🚀 Extensions

??? question "Multi-currency?"

    Each expense carries a `Currency`. Convert to a **base currency** at expense-time using a frozen FX rate (don't re-convert later — rates fluctuate). Store both: `original_amount + currency` for audit, `base_cents` for balance math.

??? question "Recurring expenses (rent)?"

    `RecurringExpense(frequency, day_of_month, ...)`. Cron job materialises a real `Expense` on the schedule. Reuse `add_expense` flow.

??? question "Activity feed?"

    Observer: `BalanceSheet` is subject; a `FeedService` listens for `add_expense` / `settle_up` and appends to user feeds.

??? question "Friend-of-friend visibility?"

    Add `Friendship` table. Restrict `add_expense` to expenses where all parties are mutual friends or share a group.

??? question "Concurrent expense additions?"

    Per-user lock on the `BalanceSheet` rows touched. For a fully distributed system: serialise via single-writer per (group_id) using a queue.

??? question "Audit log / dispute resolution?"

    Append-only `ExpenseEvent` log with `(timestamp, expense_id, action, before_state, after_state)`. Enables reverting a wrongly-added expense without recomputing the world.

??? question "Settlement that requires fewer human transfers?"

    The greedy approach favours fewest transactions but ignores who *can* pay whom (e.g., banking limits). Add a graph constraint: edges = allowed channels (UPI / Venmo / cash). Then min-cost flow on the constrained graph.

---

## ⏱️ Pacing

| Minute | What |
|---|---|
| 0–3   | Clarifying questions. |
| 3–8   | Class diagram: User, Expense, Split, BalanceSheet. |
| 8–25  | Code: SplitStrategy hierarchy + BalanceSheet. |
| 25–35 | Min-settlements algorithm; mention NP-hardness. |
| 35–45 | Q&A; pick one extension (multi-currency / FX). |

---

## 🪤 Common mistakes

??? warning "Storing balances in both directions independently"

    `A→B = 100` and `B→A = 30` un-normalised wastes memory + confuses queries. Always net to canonical direction.

??? warning "Floating point for money"

    `0.1 + 0.2 != 0.3`. **Integer cents only**.

??? warning "Mutating splits inside Expense after add"

    `add_expense` should treat the expense as immutable post-insert. Adjustments happen via reversing + re-adding (and logging).

??? warning "Forgetting payer's own share"

    If Alice pays $30 for 3 people, she owes herself $10 — but that's a no-op, not a debt. Skip splits where `user_id == paid_by`.

??? warning "Trying to compute optimal min-transactions"

    It's NP-hard. State the trade-off, ship the greedy. Interviewer values the awareness.

---

## ➡️ Where this connects

- [Hash table basics](../../02-data-structures/hash-tables/01-hash-table-basics.md) — nested dict balances.
- [Heaps](../../02-data-structures/index.md) — settlement min-heaps.
- [SOLID](../02-solid-principles.md) — Strategy = OCP for splits.
- Other LLD: [Parking Lot](01-parking-lot.md), [Vending Machine](04-vending-machine.md).
