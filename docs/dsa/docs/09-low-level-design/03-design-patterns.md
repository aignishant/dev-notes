# Design patterns (GoF reference)

> 23 patterns boiled down. Each one — when, why, Python implementation, and the LLD problem that asks for it.

<span class="phase-status phase-done">Phase 13 — GoF reference</span>

---

## 🏛️ The three families

| Family | Purpose | Patterns |
|---|---|---|
| **Creational** | How objects get made | Singleton, Factory, Abstract Factory, Builder, Prototype |
| **Structural** | How objects compose | Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy |
| **Behavioural** | How objects interact | Chain of Responsibility, Command, Iterator, Mediator, Memento, Observer, State, Strategy, Template Method, Visitor, Interpreter |

You don't need to memorise all 23. **Master 8-10 and recognise the rest.** The 8 you'll actually use in interviews are starred below.

---

## ⭐ Creational

### Singleton ⭐

Exactly one instance, globally accessible.

```python
class Logger:
    _instance: "Logger | None" = None

    def __new__(cls) -> "Logger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def log(self, msg: str): print(msg)

a, b = Logger(), Logger()
assert a is b
```

**When**: shared resource (logger, config, connection pool).
**Watch**: hides global state; thread-safety; harder to test.
**Pythonic alternative**: a module-level instance (`logger = Logger()` in a module). Modules *are* singletons.

### Factory Method ⭐

Subclasses decide which concrete type to make.

```python
class Vehicle(ABC):
    @abstractmethod
    def drive(self): ...

class Car(Vehicle):
    def drive(self): print("driving car")

class Bike(Vehicle):
    def drive(self): print("riding bike")

class VehicleFactory:
    @staticmethod
    def create(kind: str) -> Vehicle:
        match kind:
            case "car":  return Car()
            case "bike": return Bike()
        raise ValueError(kind)
```

**When**: object creation logic is non-trivial or needs to vary by parameter.
**LLD problems**: Vehicle factory in **Parking Lot**, payment-method factory in checkout.

### Builder

Step-by-step construction of complex objects.

```python
class PizzaBuilder:
    def __init__(self):
        self.size = "M"
        self.toppings: list[str] = []
        self.crust = "regular"

    def with_size(self, size): self.size = size; return self
    def add_topping(self, t): self.toppings.append(t); return self
    def with_crust(self, c): self.crust = c; return self
    def build(self) -> "Pizza":
        return Pizza(self.size, self.toppings, self.crust)

p = (PizzaBuilder()
     .with_size("L")
     .add_topping("olives")
     .add_topping("mushrooms")
     .with_crust("thin")
     .build())
```

**When**: many optional fields; readable construction matters.
**Pythonic alternative**: dataclasses with defaults + keyword args.

### Abstract Factory

Family of related factories.

```python
class GUIFactory(ABC):
    @abstractmethod
    def create_button(self) -> "Button": ...
    @abstractmethod
    def create_window(self) -> "Window": ...

class MacFactory(GUIFactory): ...
class WindowsFactory(GUIFactory): ...
```

**When**: cross-platform UI, themed components, test-double swapping.

### Prototype

Clone an existing object.

```python
import copy
template = Order(...)
new_order = copy.deepcopy(template)
```

Use Python's `copy` module. Rarely needs a dedicated class.

---

## ⭐ Structural

### Adapter ⭐

Make two incompatible interfaces work together.

```python
class OldPaymentAPI:
    def make_payment(self, dollars: int): ...

class NewPaymentAPI(ABC):
    @abstractmethod
    def charge(self, cents: int): ...

class OldToNewAdapter(NewPaymentAPI):
    def __init__(self, old: OldPaymentAPI):
        self.old = old
    def charge(self, cents: int):
        self.old.make_payment(cents // 100)
```

**When**: integrating legacy code, third-party APIs that don't match your interface.

### Decorator ⭐

Wrap an object to add behaviour without subclassing.

```python
class Coffee:
    def cost(self) -> float: return 3.0
    def describe(self) -> str: return "coffee"

class Milk:
    def __init__(self, c): self.c = c
    def cost(self): return self.c.cost() + 0.5
    def describe(self): return self.c.describe() + " + milk"

class Sugar:
    def __init__(self, c): self.c = c
    def cost(self): return self.c.cost() + 0.2
    def describe(self): return self.c.describe() + " + sugar"

c = Sugar(Milk(Coffee()))
print(c.describe(), c.cost())   # "coffee + milk + sugar 3.7"
```

**When**: stackable optional behaviour. Python's `@decorator` syntax for functions is the same idea.

### Facade ⭐

A single high-level interface over a complex subsystem.

```python
class Compiler:
    def compile(self, src: str):
        ast = Parser().parse(src)
        ir = TypeChecker().check(ast)
        bin = CodeGen().emit(ir)
        return Linker().link(bin)
```

**When**: hide a complex subsystem behind a simple API. The `compile()` method is a facade over Parser/TypeChecker/CodeGen/Linker.

### Composite

Tree of objects, treated uniformly.

```python
class Node(ABC):
    @abstractmethod
    def render(self) -> str: ...

class Leaf(Node):
    def __init__(self, text): self.text = text
    def render(self): return self.text

class Group(Node):
    def __init__(self, children: list[Node]):
        self.children = children
    def render(self):
        return "[" + ", ".join(c.render() for c in self.children) + "]"
```

**When**: file system, UI tree, AST, organisation chart.

### Proxy

Stand-in for another object — controls access, lazy-loads, caches.

```python
class RemoteService:
    def call(self): ...

class CachingProxy(RemoteService):
    def __init__(self, real: RemoteService):
        self.real = real
        self.cache: dict = {}

    def call(self, key):
        if key not in self.cache:
            self.cache[key] = self.real.call(key)
        return self.cache[key]
```

**When**: caching, access control, lazy loading, remote stubs.

### Flyweight

Share immutable common state across many objects.

```python
class TextStyle:
    _pool: dict = {}
    def __init__(self, font, size, color):
        self.font, self.size, self.color = font, size, color

    @classmethod
    def get(cls, font, size, color):
        key = (font, size, color)
        if key not in cls._pool:
            cls._pool[key] = cls(font, size, color)
        return cls._pool[key]
```

**When**: many objects, mostly identical (e.g. characters in a doc, tiles in a game).

### Bridge

Decouple abstraction from implementation so they can vary independently.

Often confused with Adapter; bridge is **chosen up-front**, adapter is **bolted-on later**.

---

## ⭐ Behavioural

### Strategy ⭐

Pluggable algorithm objects. Same problem, different methods.

```python
class SortStrategy(ABC):
    @abstractmethod
    def sort(self, data: list) -> list: ...

class QuickSort(SortStrategy):
    def sort(self, data): ...

class MergeSort(SortStrategy):
    def sort(self, data): ...

class Sorter:
    def __init__(self, strat: SortStrategy):
        self.strat = strat
    def run(self, data): return self.strat.sort(data)
```

**When**: multiple ways to do the same task (sort, discount, route, encrypt).
**Why**: Open/Closed in action.

### Observer ⭐

Subjects publish events; observers subscribe.

```python
class Subject:
    def __init__(self):
        self._subs: list = []
    def subscribe(self, fn): self._subs.append(fn)
    def notify(self, event):
        for fn in self._subs:
            fn(event)

s = Subject()
s.subscribe(lambda e: print("logger:", e))
s.subscribe(lambda e: print("metrics:", e))
s.notify("clicked")
```

**When**: pub/sub, GUI events, model-view sync, audit trails.

### State ⭐

Object's behaviour changes by state. Replace `if state == X: …` with state objects.

```python
class TrafficLight:
    def __init__(self):
        self.state: "LightState" = Red(self)
    def next(self): self.state.next()

class LightState(ABC):
    def __init__(self, light): self.light = light
    @abstractmethod
    def next(self): ...

class Red(LightState):
    def next(self): self.light.state = Green(self.light)

class Green(LightState):
    def next(self): self.light.state = Yellow(self.light)

class Yellow(LightState):
    def next(self): self.light.state = Red(self.light)
```

**When**: state machine with non-trivial transitions (vending machine, trip lifecycle, order workflow).

### Command

Encapsulate a request as an object — undoable.

```python
class Command(ABC):
    @abstractmethod
    def execute(self): ...
    @abstractmethod
    def undo(self): ...

class AddText(Command):
    def __init__(self, doc, text): self.doc, self.text = doc, text
    def execute(self): self.doc.append(self.text)
    def undo(self): self.doc.remove(self.text)
```

**When**: undo/redo, transactional ops, queued operations, macros.

### Chain of Responsibility

Request flows through a chain of handlers until one handles it.

```python
class Handler(ABC):
    def __init__(self, nxt: "Handler | None" = None):
        self.nxt = nxt

    def handle(self, req):
        if self.can_handle(req):
            return self.process(req)
        if self.nxt:
            return self.nxt.handle(req)
        return None

    @abstractmethod
    def can_handle(self, req) -> bool: ...
    @abstractmethod
    def process(self, req): ...
```

**When**: middleware (auth → log → handler), expense approval (manager → director → CFO), event filters.

### Template Method

Define the skeleton; subclasses fill in steps.

```python
class Report(ABC):
    def generate(self):
        data = self.fetch()
        rows = self.transform(data)
        return self.render(rows)
    @abstractmethod
    def fetch(self): ...
    @abstractmethod
    def transform(self, data): ...
    def render(self, rows): return "\n".join(rows)
```

**When**: algorithm with fixed structure but variable steps.

### Iterator

Traverse a collection without exposing internals. Python's `__iter__` / `__next__` is exactly this. You probably already use it.

### Mediator

Central object coordinates communication between many.

**When**: many components talking to each other (GUIs, chat rooms, air traffic control).

### Memento

Capture and restore an object's internal state. Useful for undo.

### Visitor

Add operations to a class hierarchy without modifying it. Useful for AST processing, but heavy. Use with care.

### Interpreter

Define a grammar; evaluate sentences. Rare in interviews unless designing a query language.

---

## 🎯 LLD interview pattern picks

| Problem | Patterns to reach for |
|---|---|
| Parking Lot | Strategy (pricing), Factory (vehicle), Singleton (lot) |
| Elevator | State, Strategy (scheduling), Observer (floor calls) |
| Vending Machine | State (idle/has-money/dispense), Command (refund) |
| LRU Cache | (no GoF; use OrderedDict / dict + DLL) |
| Library | Strategy (lending policy), Observer (return events) |
| Splitwise | Strategy (split type — equal/exact/percent) |
| Chess | Command (move + undo), State (game state) |
| Tic-Tac-Toe | Strategy (player kind: human / random / minimax) |
| Logger | Singleton, Chain of Responsibility (level filters) |
| Snake & Ladder | Template (turn loop), Strategy (dice variants) |
| Notification | Observer, Strategy (channel: email/sms/push) |
| File system | Composite (file/dir tree) |

---

## 🪤 Misuses

??? warning "Pattern-stuffing"

    Forcing a Visitor where a `for` loop suffices. Patterns are tools, not goals. If the simpler version is clear and correct, ship that.

??? warning "Naming everything a Factory"

    Renaming `make_X()` to `XFactory.create()` doesn't make it a pattern. Factory has meaning when *which concrete class to instantiate* is itself decided dynamically.

??? warning "Singleton-as-globals"

    Hidden global state. Hard to test. Prefer constructor injection.

??? warning "Decorator nest hell"

    Stacking 6 decorators makes order non-obvious. Cap at 2-3 layers; otherwise refactor.

---

## ➡️ Where this connects

- [OOP fundamentals](01-oop-fundamentals.md) — the building blocks.
- [SOLID](02-solid-principles.md) — why patterns work.
- LLD problems showcase patterns in action: [Parking Lot](problems/01-parking-lot.md), [Elevator](problems/02-elevator-system.md), [LRU Cache](problems/03-lru-cache.md), [Vending Machine](problems/04-vending-machine.md).
