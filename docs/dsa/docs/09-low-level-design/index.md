# 🧱 Low-Level Design

> Object-oriented design + classic LLD problems. The middle round at most product companies after the algorithmic round.

<span class="phase-status phase-done">Phase 13 — foundations + 4 classic problems</span>

---

## ✅ Available now

<div class="grid cards" markdown>

-   :material-language-python: **[OOP fundamentals (in Python)](01-oop-fundamentals.md)**

    ---

    The four pillars — encapsulation, inheritance, polymorphism, abstraction — done in Python idioms. Dataclasses, ABCs, Protocols, dunder methods, when to compose vs inherit.

-   :material-pillar: **[SOLID principles](02-solid-principles.md)**

    ---

    Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion. Each with a counter-example, a fix, and how interviewers grade it silently.

-   :material-shape: **[Design patterns (GoF reference)](03-design-patterns.md)**

    ---

    23 patterns boiled down. The 8-10 you actually use in interviews — Strategy, Observer, State, Factory, Adapter, Decorator, Facade, Singleton — with Python implementations and the LLD problem each is asked through.

-   :material-parking: **[Design a Parking Lot](problems/01-parking-lot.md)**

    ---

    The "hello world" of LLD. Vehicles, spots, multi-floor, pricing strategies. Asked at Amazon, Uber, Microsoft, Atlassian — almost every product company.

-   :material-elevator: **[Design an Elevator System](problems/02-elevator-system.md)**

    ---

    State machine + scheduling. Multiple elevators, hall calls vs cabin calls, NearestCar / LOOK / SCAN scheduling, fault handling.

-   :material-database: **[Design an LRU Cache](problems/03-lru-cache.md)**

    ---

    The most-asked LLD problem because it crosses both DS (DLL + hash map) and OOP cleanly. O(1) `get` / `put`, sentinels, thread-safety, TTL extensions.

-   :material-soda: **[Design a Vending Machine](problems/04-vending-machine.md)**

    ---

    The State pattern done right. Idle → AcceptingMoney → Dispensing transitions, change-making algorithm, fault handling, card-payment extensions.

</div>

---

## 🎯 What every LLD round grades

| Signal | What it means | How to show |
|---|---|---|
| **Decomposition** | Did you split responsibilities cleanly? | Multiple small classes, not one God class. |
| **Names** | Are your classes / methods named for intent? | `dispatch()`, not `do_thing()`. |
| **Extensibility** | Can a new requirement land without rewriting core? | Strategy + ABC where variation lives. |
| **Type safety** | Do you use `Enum` for finite sets and avoid stringly-typed code? | Enums everywhere, `dataclass` for value objects. |
| **State management** | Do you model state machines explicitly? | `Enum` for states, transitions enforced. |
| **Concurrency awareness** | Do you mention locking / atomicity even if you don't fully implement? | A note + a strategy. |

---

## 📚 Studying suggestions

If you have **3 days**:

1. Day 1: Read [OOP](01-oop-fundamentals.md) + [SOLID](02-solid-principles.md). Code one small example (a `Shape` hierarchy + a printer that prints any shape).
2. Day 2: Skim [design patterns](03-design-patterns.md). Re-implement Strategy + Observer + State from scratch.
3. Day 3: Pick 2 of 4 LLD problems. Write each one **on a whiteboard** without IDE help. Time-box 30 mins.

If you have **2 weeks**: do all 4 problems, plus 4 more from the backlog (Splitwise, Chess, Tic-Tac-Toe, Logger).

---

## 🪤 Top failure modes across all LLD rounds

??? warning "The God class"

    Putting everything into one class. The interviewer is grading your decomposition; this fails it directly.

??? warning "Stringly-typed everything"

    `vehicle_type = "car"`, `state = "idle"`. Use `Enum`. Always.

??? warning "If-elif state chains"

    The interviewer is **explicitly** looking for the State pattern when the problem is a state machine. Don't bury state in flags.

??? warning "Premature optimisation"

    "I'll add a Bloom filter to speed this up" — out of scope unless they probe perf. Get the design correct first.

??? warning "Skipping the clarifying questions"

    Diving into code immediately = fails the senior signal. Spend 2-5 minutes on questions. Always.

??? warning "Forgetting concurrency"

    Even if not implementing, mention the threading boundary. "We'd lock per-spot to avoid double-booking" earns the signal.

---

## 🔭 Coming next

A backlog of 10+ more LLD problems is planned: Splitwise · BookMyShow · Snake & Ladder · Chess · Tic-Tac-Toe · ATM · Library · File System · Logger · Online Stock Brokerage · Rate Limiter · Distributed task queue.

Patterns drilled deeper: **Visitor, Mediator, Command, Memento** with worked examples beyond the GoF reference.
