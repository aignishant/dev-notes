# SOLID principles

> Five rules for class design. Every LLD interviewer expects you to know them by name and apply them silently.

<span class="phase-status phase-done">Phase 13 — SOLID</span>

---

## 🏛️ The five principles

| Letter | Principle | One-line |
|---|---|---|
| **S** | Single Responsibility | A class has one reason to change. |
| **O** | Open/Closed | Open for extension, closed for modification. |
| **L** | Liskov Substitution | Subtypes must be usable in place of their base. |
| **I** | Interface Segregation | Many specific interfaces beat one fat one. |
| **D** | Dependency Inversion | Depend on abstractions, not concretions. |

---

## S — Single Responsibility (SRP)

> A class should have one, and only one, reason to change.

### Counter-example

```python
class Order:
    def total(self) -> float: ...
    def save_to_db(self): ...
    def send_email_confirmation(self): ...
    def render_invoice_pdf(self): ...
```

Three reasons to change: DB schema, email template, PDF layout. Three responsibilities crammed into one class.

### Fixed

```python
class Order:
    def total(self) -> float: ...

class OrderRepository:
    def save(self, order: Order): ...

class OrderEmailer:
    def send_confirmation(self, order: Order): ...

class InvoiceRenderer:
    def render(self, order: Order) -> bytes: ...
```

Each class changes only when *its* responsibility changes.

??? tip "Test"

    Ask: "If [X] changes, would I edit this class?" If [X] is more than one thing, split.

---

## O — Open/Closed (OCP)

> Software entities should be open for extension, closed for modification.

You should be able to add new behaviour by adding new classes — not by editing existing ones.

### Counter-example

```python
class DiscountCalculator:
    def apply(self, order: Order, kind: str) -> float:
        if kind == "festive":
            return order.total * 0.9
        if kind == "loyalty":
            return order.total * 0.95
        if kind == "first_purchase":
            return order.total - 100
        return order.total
```

Every new discount = edit this class.

### Fixed (strategy pattern)

```python
from abc import ABC, abstractmethod

class Discount(ABC):
    @abstractmethod
    def apply(self, total: float) -> float: ...

class Festive(Discount):
    def apply(self, total: float) -> float: return total * 0.9

class Loyalty(Discount):
    def apply(self, total: float) -> float: return total * 0.95

class FirstPurchase(Discount):
    def apply(self, total: float) -> float: return total - 100

class Calculator:
    def __init__(self, discount: Discount):
        self.discount = discount

    def total(self, order: Order) -> float:
        return self.discount.apply(order.total)
```

New discount? New class. `Calculator` doesn't change.

---

## L — Liskov Substitution (LSP)

> A subtype must be substitutable for its base type without breaking callers.

### Counter-example — the classic Square / Rectangle

```python
class Rectangle:
    def __init__(self, w: float, h: float):
        self.w, self.h = w, h
    def set_w(self, w): self.w = w
    def set_h(self, h): self.h = h
    def area(self): return self.w * self.h


class Square(Rectangle):
    def set_w(self, w):
        self.w = self.h = w               # forces square
    def set_h(self, h):
        self.w = self.h = h


def stretch(r: Rectangle):
    r.set_w(5); r.set_h(10)
    assert r.area() == 50                  # fails for Square (returns 100)
```

`Square` violates `Rectangle`'s contract: callers expect setting `w` and `h` independently. LSP broken.

### Fix

Don't model squares as rectangles. They are different shapes with different invariants.

```python
class Shape(ABC):
    def area(self) -> float: ...

class Rectangle(Shape):
    def __init__(self, w, h): self.w, self.h = w, h
    def area(self): return self.w * self.h

class Square(Shape):
    def __init__(self, s): self.s = s
    def area(self): return self.s * self.s
```

??? tip "Test"

    Replace every use of a base type with each subtype. Anything break? LSP broken.

---

## I — Interface Segregation (ISP)

> Don't force clients to depend on methods they don't use.

### Counter-example

```python
class MultiFunctionDevice(ABC):
    @abstractmethod
    def print_doc(self): ...
    @abstractmethod
    def scan(self): ...
    @abstractmethod
    def fax(self): ...

class OldPrinter(MultiFunctionDevice):
    def print_doc(self): ...
    def scan(self): raise NotImplementedError
    def fax(self): raise NotImplementedError
```

`OldPrinter` is forced to declare methods it can't fulfil.

### Fixed

```python
class Printer(ABC):
    @abstractmethod
    def print_doc(self): ...

class Scanner(ABC):
    @abstractmethod
    def scan(self): ...

class Fax(ABC):
    @abstractmethod
    def fax(self): ...

class OldPrinter(Printer): ...

class CombinedDevice(Printer, Scanner, Fax): ...
```

Small interfaces. Compose what you need.

---

## D — Dependency Inversion (DIP)

> Depend on abstractions, not concretions. High-level modules shouldn't depend on low-level modules.

### Counter-example

```python
class MySQLOrderRepository:
    def save(self, order): ...

class CheckoutService:
    def __init__(self):
        self.repo = MySQLOrderRepository()       # hardcoded

    def checkout(self, order):
        self.repo.save(order)
```

`CheckoutService` is married to MySQL. Can't test without MySQL. Can't swap to Postgres without editing.

### Fixed

```python
class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order): ...

class MySQLOrderRepository(OrderRepository):
    def save(self, order): ...

class CheckoutService:
    def __init__(self, repo: OrderRepository):       # depends on abstraction
        self.repo = repo

    def checkout(self, order):
        self.repo.save(order)
```

In tests: pass a `FakeOrderRepository`. In prod: pass `MySQLOrderRepository`. The high-level module (`CheckoutService`) doesn't know.

??? tip "Constructor injection"

    Pass dependencies into `__init__`. Don't `import` them globally and instantiate inside the class. This is dependency injection — the cleanest way to apply DIP.

---

## 🪤 Common SOLID misuses

??? warning "Splitting too aggressively"

    SRP is not "every method gets its own class". Split when responsibilities have **independent reasons to change**. Premature splitting causes anaemic classes and high indirection.

??? warning "Abstracting before you need to"

    OCP often gets misapplied — people add abstract base classes before they have a second concrete implementation. Wait until you have **two real cases**, then abstract.

??? warning "Interface bloat from compulsive ISP"

    Splitting `IRepository` into `IReadable / IWriteable / IDeletable / ICountable` is overkill if no client uses just one. Keep interfaces aligned with **client needs**, not theory.

??? warning "DIP-by-DI-framework theatre"

    DIP doesn't require an IoC container. A constructor parameter is enough. Frameworks (FastAPI's Depends, Spring) help at scale; for an LLD interview, plain constructor injection is best.

---

## 🎯 LLD interview signal

In an LLD interview, you don't typically *announce* "I'm applying SRP now." You demonstrate it:

- Splitting `Order` from `OrderRepository` (SRP)
- Adding new payment types via subclasses, not switch statements (OCP)
- Constructor-injecting a `NotificationSender` so it can be mocked (DIP)
- Picking small interfaces so a `BasicCar` doesn't have to implement `OffRoadable` (ISP)
- Not having `Square extends Rectangle` (LSP)

Interviewers grade SOLID **silently**: did your design decompose cleanly? If yes, you applied them.

---

## ➡️ Where this connects

- [OOP fundamentals](01-oop-fundamentals.md) — the building blocks SOLID applies to.
- [Design patterns](03-design-patterns.md) — many GoF patterns are SOLID applied (Strategy = OCP, Adapter = DIP, etc.).
- [Parking Lot](problems/01-parking-lot.md) and [Elevator](problems/02-elevator-system.md) showcase SOLID applied end-to-end.
