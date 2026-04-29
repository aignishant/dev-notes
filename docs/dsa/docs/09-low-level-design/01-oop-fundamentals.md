# OOP fundamentals (in Python)

> The four pillars + Python idioms. The bedrock of every LLD interview.

<span class="phase-status phase-done">Phase 13 — LLD foundations</span>

---

## 🏛️ The four pillars

| Pillar | One-line | Interview signal |
|---|---|---|
| **Encapsulation** | Bundle data + methods; hide state. | Do you use private attrs + property accessors? |
| **Inheritance** | Derive a class from a base. | Do you use it sparingly, or abuse it? |
| **Polymorphism** | One interface, many implementations. | Do you reach for ABCs / Protocols correctly? |
| **Abstraction** | Hide details behind a clean API. | Do your interfaces have the right level of detail? |

Interviewers grade not whether you *can* use OOP, but whether your model is **clean, minimal, and extensible.**

---

## 1. Encapsulation

Hide internal state. Expose only what the consumer needs.

```python
class BankAccount:
    def __init__(self, owner: str, balance: float = 0.0):
        self._owner = owner
        self._balance = balance               # convention: _ = "internal"

    @property
    def balance(self) -> float:
        return self._balance

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("amount must be positive")
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        if amount > self._balance:
            raise InsufficientFunds()
        self._balance -= amount
```

**Python conventions**:

- `_name` → "internal, treat as private". Not enforced; convention only.
- `__name` (double underscore prefix) → name-mangled to `_ClassName__name`. Use rarely; mostly for avoiding subclass attr collisions.
- `name_` (trailing underscore) → avoid keyword clash (e.g. `class_`).

??? tip "Don't reach for getters/setters by reflex"

    Java idiom: `getBalance()` / `setBalance()`. Python idiom: **public attribute** by default; switch to `@property` only when you need validation, computation, or to control mutation later. The `@property` decorator lets you upgrade without breaking callers.

---

## 2. Inheritance

Reuse implementation. Be careful — composition is usually better.

```python
class Vehicle:
    def __init__(self, plate: str):
        self.plate = plate

    def describe(self) -> str:
        return f"Vehicle {self.plate}"


class Car(Vehicle):
    def __init__(self, plate: str, doors: int):
        super().__init__(plate)
        self.doors = doors

    def describe(self) -> str:
        return f"Car {self.plate} with {self.doors} doors"
```

**Diamond / multiple inheritance**: avoid in interviews unless explicitly asked. Python uses C3 linearisation (`Class.__mro__`).

??? warning "Inheritance is overused"

    "If `B` IS-A `A`" only — and even then, prefer composition unless you have a behavioural relationship. `Stack` does NOT inherit from `list`; it *uses* a list (composition), so consumers can't accidentally `insert(0, ...)` and break the LIFO contract.

---

## 3. Polymorphism

Same call, different behaviour based on type.

### Via abstract base classes (ABC)

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

    @abstractmethod
    def perimeter(self) -> float: ...


class Circle(Shape):
    def __init__(self, r: float):
        self.r = r

    def area(self) -> float:
        return 3.14159 * self.r * self.r

    def perimeter(self) -> float:
        return 2 * 3.14159 * self.r


class Rectangle(Shape):
    def __init__(self, w: float, h: float):
        self.w, self.h = w, h

    def area(self) -> float:
        return self.w * self.h

    def perimeter(self) -> float:
        return 2 * (self.w + self.h)


def total_area(shapes: list[Shape]) -> float:
    return sum(s.area() for s in shapes)
```

### Via Protocol (structural / duck typing)

```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None: ...

def render(things: list[Drawable]) -> None:
    for t in things:
        t.draw()
```

**Use ABC when** you want enforced interface + shared base logic.
**Use Protocol when** you want structural typing (any class with the method works, no inheritance needed).

---

## 4. Abstraction

Expose the *what*, hide the *how*.

```python
class PaymentProcessor:
    """High-level API."""

    def charge(self, card: "Card", amount: int) -> "Receipt":
        # internally: tokenize → call gateway → handle 3DS → record
        token = self._tokenize(card)
        result = self._call_gateway(token, amount)
        if result.requires_3ds:
            result = self._handle_3ds(result)
        return self._record(result)
```

The consumer sees `charge(card, amount)`. They don't know — and don't care — about tokenisation, 3DS, or gateway selection. Each `_helper` is one concern.

---

## 🐍 Python-specific idioms interviewers like to see

### Dunder methods

| Method | Purpose |
|---|---|
| `__init__` | Constructor. |
| `__repr__` | Unambiguous string (debug). Always provide. |
| `__str__` | Friendly string (`print`). |
| `__eq__` | Equality (`==`). Pair with `__hash__`. |
| `__hash__` | Hashable (sets/dict keys). |
| `__lt__`, `__le__`, … | Ordering (use `functools.total_ordering`). |
| `__len__`, `__iter__`, `__contains__` | Containers. |
| `__enter__`, `__exit__` | Context manager (`with`). |
| `__call__` | Make instance callable. |

### Dataclass for value objects

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: float
    y: float

p = Point(1.0, 2.0)
# p.x = 5  # raises FrozenInstanceError
```

`frozen=True` → immutable + hashable. Useful for keys, value objects.

### Enum for finite sets

```python
from enum import Enum

class TripState(Enum):
    REQUESTED = "REQUESTED"
    MATCHED = "MATCHED"
    IN_TRIP = "IN_TRIP"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
```

In LLD interviews: state machines, vehicle types, payment statuses → `Enum`, never raw strings.

### Composition over inheritance

```python
class Engine:
    def start(self): ...

class Car:
    def __init__(self):
        self._engine = Engine()      # HAS-A, not IS-A

    def start(self):
        self._engine.start()
```

---

## 📏 Class design checklist

- [ ] Single Responsibility (one reason to change).
- [ ] Constructor takes only what's required; optional params have sensible defaults.
- [ ] Public surface is minimal; everything else is `_internal`.
- [ ] Methods named for intent (`charge`, `dispatch`), not mechanism (`do_card_thing`).
- [ ] No global mutable state. Pass dependencies in.
- [ ] No `is None` checks for things that are never None — use the type system.
- [ ] `__repr__` provided.
- [ ] No raw strings for finite sets — use `Enum`.

---

## 🔁 Where this connects

- [SOLID principles](02-solid-principles.md) — turn these pillars into design rules.
- [Design patterns](03-design-patterns.md) — reusable shapes built on top.
- LLD problems: [Parking Lot](problems/01-parking-lot.md), [Elevator](problems/02-elevator-system.md), [LRU Cache](problems/03-lru-cache.md), [Vending Machine](problems/04-vending-machine.md).
