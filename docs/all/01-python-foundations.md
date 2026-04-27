# Module 1 — Python Foundations

> **Bible Module 1 of 14.** Self-contained. Written for Python **3.12+** (works on 3.11 with two flagged exceptions). Code is runnable as-is.

---

## 0. Goal, reader, and how to use this module

**Goal.** After this module you can: write idiomatic, typed, tested Python; reason about *why* code behaves the way it does (not just *what* it does); and use the language well enough that the rest of the bible (FastAPI, ML, LLMs, agents) is about the domain — never about Python itself.

**Target reader.** Beginner who knows another language, OR an intermediate Python user with gaps. If you've never programmed at all, do a 2-hour "syntax tour" video first, then come here.

**How to use it.**
1. Read top to bottom once. Don't skip.
2. Type every code block yourself. Don't copy-paste.
3. Do all 25 problems at the end. Solve before reading the solution.
4. Keep the cheatsheet (§24) open in a tab forever.

**Prerequisites.** Comfort with a terminal. Python 3.12 installed (we'll show how).
**Next steps after this module.** Module 2 (Data Stack: numpy/pandas) and Module 4 (FastAPI).

---

## 1. Setup & tooling

You will use *one* tool for environments and dependencies: **`uv`**. It is 10–100× faster than pip, replaces `pip`, `pip-tools`, `virtualenv`, `pyenv`, and `poetry`, and is what production teams in 2026 use.

### 1.1 Install uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 1.2 Install Python and start a project

```bash
uv python install 3.12          # install Python 3.12 (no system pollution)
uv init my-project               # creates pyproject.toml + .venv
cd my-project
uv add requests pydantic         # adds to pyproject + installs
uv run python script.py          # runs inside the venv automatically
uv sync                          # reproduce env from pyproject.toml + uv.lock
```

**Why this matters.** Every Python project you ever ship needs three things pinned: Python version, dependency versions, and a lockfile. `uv` does all three by default. No `requirements.txt` drift, no "works on my machine."

### 1.3 The four commands you'll actually use

| Command | What it does |
|---|---|
| `uv add PKG` | Add a dependency |
| `uv add --dev pytest ruff mypy` | Add dev-only deps |
| `uv run CMD` | Run anything inside the project venv |
| `uv sync` | Recreate venv from lockfile |

### 1.4 The standard project layout

```
my-project/
├── pyproject.toml      # one config file for everything
├── uv.lock             # exact versions (commit this)
├── .python-version     # "3.12"
├── README.md
├── src/
│   └── my_project/
│       ├── __init__.py
│       └── main.py
└── tests/
    └── test_main.py
```

**Why `src/`?** It prevents accidentally importing your project from the working directory instead of the installed package — a real bug source. Always use `src/` layout for anything you'll ship.

---

## 2. The mental model: names, objects, references

This is the single most important section. If you skip it, you will write subtle bugs forever.

**The rule.** In Python, *variables are names that point to objects*. Assignment never copies. `a = b` makes `a` point to the same object `b` points to.

```python
a = [1, 2, 3]      # creates a list object; name "a" points to it
b = a              # name "b" now points to the SAME list object
b.append(4)        # mutates the object both names see
print(a)           # [1, 2, 3, 4]   <-- surprise if you don't know this
print(a is b)      # True            <-- same object
```
**Output:**
```
[1, 2, 3, 4]
True
```

### 2.1 Mutable vs immutable — the cause of 50% of bugs

| Immutable (safe to share) | Mutable (sharing causes bugs) |
|---|---|
| `int`, `float`, `bool`, `str`, `tuple`, `frozenset`, `bytes` | `list`, `dict`, `set`, `bytearray`, custom classes by default |

**The classic mutable-default trap:**

```python
def add_item(item, basket=[]):       # ⚠️ BUG: default evaluated ONCE at def-time
    basket.append(item)
    return basket

print(add_item("apple"))   # ['apple']
print(add_item("bread"))   # ['apple', 'bread']  <-- not what you want
```

**Fix:** use `None` as the sentinel.

```python
def add_item(item, basket=None):
    if basket is None:
        basket = []
    basket.append(item)
    return basket
```

**Why it matters in real systems.** This bug shipped in production at every company I've seen. It's the #1 reason "the API returns wrong data on the second request."

### 2.2 `is` vs `==`

- `is` → same object in memory (identity).
- `==` → same value (equality).

Use `is` only for `None`, `True`, `False`, and sentinels. Everything else uses `==`.

```python
a = [1, 2]
b = [1, 2]
print(a == b)   # True  (same value)
print(a is b)   # False (different objects)
```

---

## 3. Built-in types — deep enough to be dangerous

### 3.1 Numbers

```python
x: int = 10              # arbitrary precision — no overflow
y: float = 3.14          # IEEE 754 double — has rounding error
z: complex = 2 + 3j

print(0.1 + 0.2 == 0.3)  # False  <-- floating point
print(round(0.1 + 0.2, 10) == 0.3)  # True
```

For money, use `decimal.Decimal`. For exact fractions, `fractions.Fraction`. **Never use `float` for currency.**

### 3.2 Strings

Strings are immutable sequences of Unicode code points.

```python
name = "Ada"
greeting = f"Hello, {name}!"        # f-string — always use these
multiline = """line 1
line 2"""

# common methods you'll use 90% of the time
"  hi  ".strip()        # 'hi'
"a,b,c".split(",")      # ['a', 'b', 'c']
",".join(["a","b","c"]) # 'a,b,c'
"abc".startswith("ab")  # True
"abc".replace("a","z")  # 'zbc'
```

**F-string formatting tricks (3.12+):**

```python
n = 1234567.891
print(f"{n:,.2f}")        # 1,234,567.89   thousands sep, 2 decimals
print(f"{n:>15.2f}")      #     1234567.89  right-aligned, width 15
print(f"{0.875:.1%}")     # 87.5%
print(f"{42:08b}")        # 00101010       binary, width 8
print(f"{name=}")         # name='Ada'     debug form (3.8+)
```

### 3.3 Lists, tuples, dicts, sets — when to use which

| You want… | Use |
|---|---|
| Ordered, mutable, allows duplicates | `list` |
| Ordered, immutable, hashable (e.g., dict key) | `tuple` |
| Key→value lookup in O(1) | `dict` |
| Membership test in O(1), no duplicates | `set` |
| Immutable set (hashable) | `frozenset` |

```python
# list — ordered, mutable
xs = [1, 2, 3]
xs.append(4); xs.pop(0); xs[1:3]; xs.sort()

# tuple — ordered, immutable, often used for fixed-shape records
point = (3, 4)
x, y = point                # unpacking

# dict — insertion-ordered since 3.7, O(1) lookup
user = {"name": "Ada", "age": 30}
user["age"]                 # 30
user.get("missing", 0)      # 0  (no KeyError)
for k, v in user.items(): ...

# set — O(1) membership, deduplication
seen = {1, 2, 3}
seen.add(4); 3 in seen      # True
{1,2,3} & {2,3,4}           # {2, 3}  intersection
```

**The dict performance fact.** Python dicts are extremely fast hash tables. If your code does `if x in some_list` for a list of >50 items, replace it with a set.

### 3.4 Comprehensions — the Pythonic loop

```python
# list comprehension
squares = [n*n for n in range(10) if n % 2 == 0]
# [0, 4, 16, 36, 64]

# dict comprehension
square_map = {n: n*n for n in range(5)}
# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

# set comprehension
unique_lengths = {len(w) for w in ["hi","bye","hello"]}
# {2, 3, 5}

# nested
matrix = [[i*j for j in range(3)] for i in range(3)]
```

**Rule of thumb.** If a comprehension wraps to 3+ lines or has 2+ filters, write a `for` loop instead. Readability beats cleverness.

---

## 4. Control flow

```python
# if/elif/else
if x > 0:    sign = "+"
elif x < 0:  sign = "-"
else:        sign = "0"

# match (3.10+) — structural pattern matching
match command.split():
    case ["go", direction]:           print(f"going {direction}")
    case ["take", *items]:            print(f"taking {items}")
    case ["quit"]:                    print("bye")
    case _:                           print("unknown")

# for/else — else runs if loop completes without break
for n in [2, 3, 5, 7]:
    if n == 4: break
else:
    print("no 4 found")   # this runs

# while
while not done: process()

# walrus := assigns inside an expression (3.8+)
while (chunk := file.read(1024)):
    process(chunk)
```

**Truthiness.** `0`, `0.0`, `""`, `[]`, `{}`, `set()`, `None`, `False` are all falsy. Everything else is truthy. So `if my_list:` checks "non-empty" — preferred over `if len(my_list) > 0:`.

---

## 5. Functions

### 5.1 Parameters and arguments

```python
def fn(pos1, pos2, /, normal, *, kw_only, **rest):
    #     ^^^^^^^^   ^^^^^^   ^^^^^^^^^^^^^^^^^^
    #   positional   either   keyword-only
    ...

# positional-only (before /): caller must pass by position
# keyword-only   (after  *): caller must pass by name
```

This matters for API design: `divmod(10, 3)` is clearer than `divmod(a=10, b=3)`, so `/` is used. `sorted(xs, reverse=True)` is clearer than `sorted(xs, True)`, so `*` is used.

### 5.2 Type hints (modern syntax, 3.12+)

```python
def greet(name: str, times: int = 1) -> str:
    return f"hi {name}!" * times

# Modern generic syntax (3.12+, PEP 695)
def first[T](xs: list[T]) -> T | None:
    return xs[0] if xs else None

# pre-3.12 equivalent:
# from typing import TypeVar; T = TypeVar("T")
# def first(xs: list[T]) -> T | None: ...
```

### 5.3 Closures

A closure is a function that "remembers" variables from the enclosing scope.

```python
def make_counter(start=0):
    count = start
    def increment():
        nonlocal count       # without this, you'd shadow, not mutate
        count += 1
        return count
    return increment

c = make_counter()
c(); c(); c()   # 1, 2, 3
```

### 5.4 `*args`, `**kwargs`, unpacking

```python
def log(*args, **kwargs):
    print("positional:", args)
    print("keyword:",   kwargs)

log(1, 2, 3, level="INFO", tag="api")
# positional: (1, 2, 3)
# keyword:    {'level': 'INFO', 'tag': 'api'}

# unpacking on the call side
nums = [1, 2, 3]
print(*nums)            # equivalent to print(1, 2, 3)

config = {"host": "x", "port": 80}
connect(**config)       # connect(host="x", port=80)
```

---

## 6. OOP — the modern, dataclasses-first way

In 2026, you almost never write a class with a hand-written `__init__`. You use `dataclass` or `pydantic.BaseModel`.

### 6.1 Dataclasses (stdlib, no deps)

```python
from dataclasses import dataclass, field

@dataclass(slots=True, frozen=True)   # slots = less memory; frozen = immutable
class Point:
    x: float
    y: float
    label: str = "origin"
    tags: list[str] = field(default_factory=list)   # never use mutable defaults directly

    def distance_to(self, other: "Point") -> float:
        return ((self.x - other.x)**2 + (self.y - other.y)**2) ** 0.5

p = Point(1.0, 2.0)
print(p)                       # Point(x=1.0, y=2.0, label='origin', tags=[])
print(p.distance_to(Point(4,6))) # 5.0
```

**`slots=True`.** Skips creating `__dict__` on each instance — uses ~40% less memory and faster attribute access. Use it for any class you'll create thousands of.
**`frozen=True`.** Makes the class immutable + hashable (usable as dict key / in sets).

### 6.2 The dunders you actually need

```python
class Money:
    def __init__(self, amount, currency):
        self.amount = amount; self.currency = currency

    def __repr__(self):                 # for developers (debug)
        return f"Money({self.amount}, {self.currency!r})"

    def __str__(self):                  # for users (print)
        return f"{self.amount} {self.currency}"

    def __eq__(self, other):
        return (self.amount, self.currency) == (other.amount, other.currency)

    def __hash__(self):                 # required if you defined __eq__
        return hash((self.amount, self.currency))

    def __lt__(self, other):
        return self.amount < other.amount   # @total_ordering fills in the rest

    def __add__(self, other):
        if self.currency != other.currency:
            raise ValueError("currency mismatch")
        return Money(self.amount + other.amount, self.currency)
```

### 6.3 `classmethod` vs `staticmethod` vs `property`

```python
class User:
    def __init__(self, first, last):
        self.first, self.last = first, last

    @property                           # access as user.full_name (no parens)
    def full_name(self) -> str:
        return f"{self.first} {self.last}"

    @classmethod                        # alternate constructor
    def from_string(cls, s: str) -> "User":
        first, last = s.split()
        return cls(first, last)         # cls = subclass-aware

    @staticmethod                       # logically related, but no self/cls
    def is_valid_name(name: str) -> bool:
        return name.isalpha()

u = User.from_string("Ada Lovelace")
print(u.full_name)                      # Ada Lovelace
```

### 6.4 Inheritance and protocols

Classical inheritance is fine, but **prefer composition + Protocols** for flexible APIs.

```python
from typing import Protocol

class SupportsLog(Protocol):            # structural typing — no inheritance needed
    def log(self, msg: str) -> None: ...

class FileLogger:                       # doesn't inherit anything…
    def log(self, msg: str) -> None: print(f"[file] {msg}")

class CloudLogger:                      # …but both satisfy the Protocol
    def log(self, msg: str) -> None: print(f"[cloud] {msg}")

def run_job(logger: SupportsLog) -> None:
    logger.log("starting")              # works for either, no base class

run_job(FileLogger())
run_job(CloudLogger())
```

**Why this matters.** Protocols give you Go-style "duck typing with type safety." This is how modern Python libraries (FastAPI, pydantic) are designed.

---

## 7. Modules, packages, imports

### 7.1 The mental model

- **Module** = one `.py` file.
- **Package** = a directory with an `__init__.py` (or namespace package without).
- `import x` runs `x.py` once, caches it in `sys.modules`.

```python
# absolute import (preferred)
from my_project.utils import format_date

# relative import (only inside a package)
from .utils import format_date          # same package
from ..core import settings              # parent package
```

### 7.2 The `if __name__ == "__main__"` guard

```python
def main():
    print("running")

if __name__ == "__main__":
    main()
```

Why? When this file is *imported*, `__name__ == "my_module"` and `main()` doesn't run. When you run it directly (`python file.py`), `__name__ == "__main__"` and it does. Without this guard, importing the file accidentally runs your script — a real bug, especially with `multiprocessing` on Windows.

### 7.3 Circular imports — and how to fix them

If `a.py` imports `b.py` and `b.py` imports `a.py`, you'll get an `ImportError` or a partially-initialized module. Fixes, in order of preference:

1. **Refactor.** Move the shared thing to a third module `c.py`.
2. **Import inside the function.** Defers the import until call time.
3. **Use `TYPE_CHECKING`** for type-hint-only imports:

```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .b import Thing            # only imported by type checkers, not at runtime

def f(x: "Thing") -> None: ...      # forward reference as string
```

---

## 8. Errors and exceptions

### 8.1 The hierarchy

`BaseException` → `Exception` → everything you should catch. **Never `except:` or `except BaseException:`** — those swallow `KeyboardInterrupt` (Ctrl-C) and `SystemExit`.

### 8.2 Try / except / else / finally

```python
try:
    data = json.loads(raw)
except json.JSONDecodeError as e:       # specific first
    log.error("bad json: %s", e)
    data = {}
except (ValueError, TypeError) as e:    # group related
    log.error("bad data: %s", e)
    data = {}
else:
    log.info("parsed ok")               # runs only if no exception
finally:
    raw.close()                          # always runs, even on exception
```

### 8.3 Custom exceptions

```python
class AppError(Exception):
    """Base for all app errors."""

class ValidationError(AppError): ...
class NotFoundError(AppError): ...

# raise with chaining — preserves the original cause
try:
    user = db.fetch(id)
except KeyError as e:
    raise NotFoundError(f"user {id}") from e   # use `from e`, not just `raise`
```

### 8.4 Exception groups (3.11+) — for concurrent code

```python
try:
    ...
except* ValueError as eg:    # handle all ValueErrors in a group
    for e in eg.exceptions: ...
except* TypeError as eg:
    ...
```

You'll meet `ExceptionGroup` in `asyncio.TaskGroup` (§15).

### 8.5 EAFP vs LBYL

Pythonic style is **Easier to Ask Forgiveness than Permission**:

```python
# LBYL (Look Before You Leap) — race-condition prone
if "key" in d and d["key"] is not None:
    use(d["key"])

# EAFP (preferred)
try:
    use(d["key"])
except KeyError:
    ...
```

For dicts specifically, `d.get("key", default)` is cleanest.

---

## 9. Iterators, generators, and the comprehension family

### 9.1 The iterator protocol

An iterator is anything implementing `__iter__` and `__next__`. `for` loops use this protocol:

```python
xs = [10, 20, 30]
it = iter(xs)
print(next(it))   # 10
print(next(it))   # 20
print(next(it))   # 30
print(next(it))   # raises StopIteration
```

### 9.2 Generators — iterators made simple

```python
def count_up_to(n):
    i = 0
    while i < n:
        yield i           # pauses here, resumes on next()
        i += 1

for x in count_up_to(3): print(x)   # 0, 1, 2
```

Generators are **lazy** — they produce values on demand and use O(1) memory.

```python
# read a 100GB file line-by-line — never loads it all
def lines(path):
    with open(path) as f:
        for line in f:
            yield line.rstrip()

# generator expression — like a list comprehension but lazy
sum_squares = sum(n*n for n in range(10**6))   # no list materialized
```

### 9.3 `itertools` — the toolkit you'll use forever

```python
from itertools import chain, islice, groupby, product, combinations, accumulate

list(chain([1,2], [3,4]))                   # [1,2,3,4]
list(islice(gen, 5))                         # first 5 from any iterator
list(product([1,2], ["a","b"]))              # [(1,'a'),(1,'b'),(2,'a'),(2,'b')]
list(combinations([1,2,3], 2))               # [(1,2),(1,3),(2,3)]
list(accumulate([1,2,3,4]))                  # [1,3,6,10]  (running sum)

# group consecutive items by key (input must be sorted by the key)
data = [("a",1),("a",2),("b",3),("b",4)]
for key, group in groupby(data, key=lambda x: x[0]):
    print(key, list(group))
# a [('a',1),('a',2)]
# b [('b',3),('b',4)]
```

---

## 10. Context managers — `with` statements

A context manager guarantees setup + cleanup, even on exceptions.

```python
with open("file.txt") as f:        # f.close() guaranteed, even if read raises
    data = f.read()

# multiple
with open("in") as fin, open("out","w") as fout:
    fout.write(fin.read())
```

### 10.1 Writing your own — the `contextlib` way

```python
from contextlib import contextmanager
import time

@contextmanager
def timer(label):
    start = time.perf_counter()
    try:
        yield                       # block runs here
    finally:
        elapsed = time.perf_counter() - start
        print(f"{label}: {elapsed:.3f}s")

with timer("query"):
    result = expensive_db_call()
```

### 10.2 Class-based version

```python
class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self                  # bound to `as` variable
    def __exit__(self, exc_type, exc, tb):
        self.elapsed = time.perf_counter() - self.start
        return False                 # False = don't suppress exceptions
```

**Use cases.** DB transactions, file handles, locks, temp directories, suppressing warnings, timing, mocking in tests.

---

## 11. Decorators — deep

A decorator is a function that takes a function and returns a function.

### 11.1 The basic form

```python
import functools, time

def timed(fn):
    @functools.wraps(fn)             # preserves fn.__name__, fn.__doc__
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = fn(*args, **kwargs)
        print(f"{fn.__name__}: {time.perf_counter()-t0:.3f}s")
        return result
    return wrapper

@timed
def slow_add(a, b):
    time.sleep(0.1)
    return a + b

slow_add(1, 2)    # slow_add: 0.100s
```

`@timed` is sugar for `slow_add = timed(slow_add)`.

### 11.2 Decorator with arguments

Three layers: outermost takes args, middle takes the function, inner is the wrapper.

```python
def retry(times=3, delay=1.0):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for _ in range(times):
                try: return fn(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator

@retry(times=5, delay=0.5)
def flaky_api_call(): ...
```

### 11.3 Stacking, and order

```python
@a
@b
@c
def f(): ...
# equivalent to: f = a(b(c(f)))
# decorators apply bottom-up
```

### 11.4 The `functools` decorators you'll use

```python
from functools import lru_cache, cache, cached_property, singledispatch

@cache                           # memoize forever (3.9+)
def fib(n): return n if n < 2 else fib(n-1)+fib(n-2)

@lru_cache(maxsize=1024)         # memoize with size limit
def slow_query(uid): ...

class Page:
    @cached_property             # compute once, then cache as attribute
    def parsed(self):
        return expensive_parse(self.html)

@singledispatch                  # dispatch on type of first arg
def render(x): raise TypeError

@render.register
def _(x: int): print(f"int: {x}")

@render.register
def _(x: str): print(f"str: {x!r}")
```

---

## 12. Typing — modern style (3.12+)

Type hints are not enforced at runtime. They are checked by `mypy` or `pyright` in CI/your editor. They're documentation that doesn't lie.

### 12.1 The basics

```python
x: int = 1
y: float = 2.0
name: str = "ada"
flags: bool = True
maybe: int | None = None             # 3.10+ union syntax (replaces Optional[int])

xs: list[int] = [1, 2, 3]            # 3.9+ generic builtins (no need for List)
mapping: dict[str, int] = {"a": 1}
pair: tuple[int, str] = (1, "a")
fixed: tuple[int, ...] = (1, 2, 3)   # variable length, all ints
```

### 12.2 Callables, generics, literals, annotated

```python
from collections.abc import Callable, Iterable
from typing import Literal, Annotated, Final

# function type
on_click: Callable[[int, str], None]   # takes (int, str), returns None

# only specific values allowed
mode: Literal["read", "write", "append"] = "read"

# constants
MAX_RETRIES: Final = 5

# attached metadata (used by FastAPI, pydantic, etc.)
UserId = Annotated[int, "primary key"]

# generic functions (3.12+)
def first[T](xs: Iterable[T]) -> T | None:
    for x in xs: return x
    return None
```

### 12.3 TypedDict and NamedTuple

```python
from typing import TypedDict, NamedTuple

class UserDict(TypedDict):
    id: int
    name: str
    email: str | None

u: UserDict = {"id": 1, "name": "ada", "email": None}   # mypy will check shape

class Point(NamedTuple):
    x: float
    y: float

p = Point(1.0, 2.0)
p.x; p[0]   # both work
```

### 12.4 Running a type checker

```bash
uv add --dev mypy
uv run mypy src/
```

**Production tip.** Add `mypy --strict` to CI on day 1. Adding it to a 50k-line codebase later is misery.


---

## 13. File I/O & `pathlib`

Use `pathlib` for paths. Never use `os.path` in new code.

```python
from pathlib import Path

p = Path("data") / "users.csv"        # OS-correct separator
p.exists()                            # True/False
p.is_file()
p.suffix                              # '.csv'
p.stem                                # 'users'
p.parent                              # Path('data')
p.with_suffix(".json")                # Path('data/users.json')

# read/write text — handles encoding properly
text = p.read_text(encoding="utf-8")
p.write_text("hello", encoding="utf-8")

# read/write bytes
data = p.read_bytes()
p.write_bytes(b"\x00\x01\x02")

# iterate files
for f in Path(".").rglob("*.py"):     # recursive glob
    print(f, f.stat().st_size)
```

### 13.1 Always specify encoding

```python
# BAD — uses locale, breaks on Windows vs Linux
with open("f.txt") as f: ...

# GOOD
with open("f.txt", encoding="utf-8") as f: ...
```

### 13.2 JSON, CSV, pickle, tomllib

```python
import json
data = json.loads('{"a": 1}')                       # str → dict
text = json.dumps(data, indent=2, ensure_ascii=False)

# from a file
with open("config.json", encoding="utf-8") as f:
    config = json.load(f)

import csv
with open("users.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):                   # row is a dict
        print(row["name"], row["email"])

import tomllib                                       # 3.11+, read-only
with open("pyproject.toml", "rb") as f:             # note: binary mode
    config = tomllib.load(f)
```

**Never use `pickle` on untrusted data.** It can execute arbitrary code. Use JSON or msgpack instead.

---

## 14. Stdlib power tools

These three modules pay for themselves a thousand times over.

### 14.1 `collections`

```python
from collections import Counter, defaultdict, deque, OrderedDict, ChainMap

# Counter — count anything
words = "the cat sat on the mat".split()
c = Counter(words)
print(c.most_common(2))           # [('the', 2), ('cat', 1)]

# defaultdict — auto-create missing keys
groups = defaultdict(list)
for name, dept in [("a","eng"),("b","eng"),("c","sales")]:
    groups[dept].append(name)
# {'eng': ['a','b'], 'sales': ['c']}

# deque — O(1) append/pop from BOTH ends (lists are O(n) on the left)
from collections import deque
q = deque([1,2,3])
q.appendleft(0); q.popleft()      # both O(1)
q = deque(maxlen=3)               # bounded — old items drop off
```

### 14.2 `functools`

```python
from functools import reduce, partial

reduce(lambda a,b: a+b, [1,2,3,4])    # 10  (use sum() instead, this is for non-trivial)

# partial — pre-fill arguments
import json
to_pretty_json = partial(json.dumps, indent=2, sort_keys=True)
print(to_pretty_json({"b":2, "a":1}))
```

### 14.3 `datetime` — and the gotcha

```python
from datetime import datetime, date, timedelta, timezone, UTC

now_naive = datetime.now()              # ⚠️ no timezone — DON'T USE
now_utc   = datetime.now(UTC)           # 3.11+ shorthand for timezone.utc

# always store UTC, format for display only
later = now_utc + timedelta(days=7, hours=3)
print(later.isoformat())                # '2026-05-04T13:25:00+00:00'

# parse ISO 8601
dt = datetime.fromisoformat("2026-04-27T10:00:00+00:00")
```

**Rule:** every datetime in your system has a timezone. Naive datetimes are a bug.

### 14.4 `re` — quick reference

```python
import re
re.search(r"\d+", "id=42")              # <re.Match ... '42'>
re.findall(r"\w+", "the cat sat")       # ['the','cat','sat']
re.sub(r"\s+", " ", "a   b\tc")         # 'a b c'

# pre-compile if used in a loop
PATTERN = re.compile(r"^user-(\d+)$")
for line in lines:
    if m := PATTERN.match(line):
        print(int(m.group(1)))
```

---

## 15. Concurrency — when to use what

This is where most Python developers get confused. The decision tree:

| Workload | Use |
|---|---|
| **CPU-bound** (math, parsing, image processing) | `multiprocessing` or `concurrent.futures.ProcessPoolExecutor` |
| **I/O-bound, many short tasks** (HTTP, DB, files) | `asyncio` |
| **I/O-bound, simpler / mixing with sync libs** | `concurrent.futures.ThreadPoolExecutor` |

**Why?** The Global Interpreter Lock (GIL) means only one thread executes Python bytecode at a time. Threads still help for I/O (the lock is released during I/O waits) but not for CPU work. Processes have no shared GIL — true parallelism. Asyncio is single-threaded but can manage thousands of concurrent I/O operations cheaply.

> Note: Python 3.13 introduced experimental free-threaded builds (no GIL). In production you can mostly ignore this until 3.14/3.15.

### 15.1 Threads — for I/O, when async is overkill

```python
from concurrent.futures import ThreadPoolExecutor
import requests

urls = ["https://example.com"] * 50

def fetch(u): return requests.get(u).status_code

with ThreadPoolExecutor(max_workers=10) as pool:
    results = list(pool.map(fetch, urls))
```

### 15.2 Processes — for CPU work

```python
from concurrent.futures import ProcessPoolExecutor

def heavy(n): return sum(i*i for i in range(n))

if __name__ == "__main__":              # ⚠️ required on Windows/macOS spawn
    with ProcessPoolExecutor() as pool:
        results = list(pool.map(heavy, [10**6, 10**7, 10**6]))
```

### 15.3 Asyncio — the modern way for I/O

```python
import asyncio
import httpx

async def fetch(client, url):
    r = await client.get(url)
    return r.status_code

async def main():
    urls = ["https://example.com"] * 50
    async with httpx.AsyncClient() as client:
        async with asyncio.TaskGroup() as tg:        # 3.11+
            tasks = [tg.create_task(fetch(client, u)) for u in urls]
        results = [t.result() for t in tasks]
    print(results)

asyncio.run(main())
```

**Mental model.** `await` says "pause this coroutine until X is ready; meanwhile, the event loop runs other coroutines." There is one thread. There is no preemption. Switches happen only at `await` points.

### 15.4 The async cardinal rule

**Never call a blocking function in async code.** A `time.sleep(1)` or a sync `requests.get()` freezes the entire event loop. Use `asyncio.sleep`, `httpx.AsyncClient`, `aiomysql`, etc. If you must call sync code, wrap it:

```python
result = await asyncio.to_thread(blocking_function, arg1, arg2)
```

---

## 16. Logging — properly

`print()` is for scripts. `logging` is for everything else.

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)       # use module name — never the root logger

log.info("user %s logged in", user_id)  # use %s, not f-string — lazy formatting
log.warning("disk %d%% full", pct)
log.error("payment failed", exc_info=True)   # includes traceback
```

**Why `%s` instead of f-string?** If the log level filters out the message, the f-string is still rendered. With `%s`, formatting is deferred.

### 16.1 Structured logging for production

```python
# install: uv add structlog
import structlog
log = structlog.get_logger()
log.info("user_login", user_id=42, ip="1.2.3.4", success=True)
# → JSON line that aggregates cleanly in Datadog/Splunk/CloudWatch
```

---

## 17. Testing with pytest

```bash
uv add --dev pytest pytest-cov
```

```python
# src/myapp/math.py
def add(a, b): return a + b

# tests/test_math.py
import pytest
from myapp.math import add

def test_add_positive():
    assert add(2, 3) == 5

def test_add_raises_on_strings():
    with pytest.raises(TypeError):
        add("a", 1)

@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (-1, 1, 0),
    (0, 0, 0),
])
def test_add_table(a, b, expected):
    assert add(a, b) == expected

@pytest.fixture
def sample_users():
    return [{"id": 1}, {"id": 2}]

def test_users(sample_users):
    assert len(sample_users) == 2
```

```bash
uv run pytest                            # run all
uv run pytest tests/test_math.py::test_add_positive   # one test
uv run pytest -k "positive"              # by keyword
uv run pytest --cov=src/myapp            # coverage
```

**The 2026 minimum testing stack.** `pytest`, `pytest-cov`, `pytest-asyncio` (for async), `hypothesis` (property-based), `freezegun` (time mocking).

---

## 18. Memory, the GIL, and performance

### 18.1 Reference counting + cycle collector

CPython manages memory with reference counts: when a refcount hits zero, the object is freed. A separate cycle collector handles reference cycles (e.g., `a.b = b; b.a = a`).

```python
import sys
x = [1, 2, 3]
print(sys.getrefcount(x))    # 2 (one from x, one from getrefcount's arg)
```

### 18.2 The GIL in one paragraph

CPython holds a global lock so only one thread executes Python bytecode at a time. C extensions (`numpy`, `torch`) release the GIL during their compute, which is why `numpy` can use all cores. For pure Python CPU work, use processes.

### 18.3 Profiling

```bash
# the right way to profile in 2026: py-spy, no code changes
uv tool install py-spy
py-spy record -o profile.svg -- python script.py
py-spy top --pid 12345           # live, attach to running process
```

For per-function timing inside code:

```python
import cProfile, pstats
with cProfile.Profile() as pr:
    run_workload()
pstats.Stats(pr).sort_stats("cumulative").print_stats(20)
```

### 18.4 The performance hierarchy (use in this order)

1. **Better algorithm.** O(n) instead of O(n²). 99% of speedups live here.
2. **Better data structure.** Set instead of list for `in`. Dict instead of list-of-tuples for lookup.
3. **Vectorize with numpy/pandas.** A loop over a 1M-row list is 100× slower than the numpy equivalent.
4. **Cache.** `@functools.cache` for pure functions.
5. **Concurrency.** Threads for I/O, processes for CPU.
6. **Native code.** Cython, Rust + PyO3, or just call into a C library.

---

## 19. Pythonic idioms and anti-patterns

| Anti-pattern | Pythonic |
|---|---|
| `for i in range(len(xs)): x = xs[i]` | `for x in xs:` |
| `for i in range(len(xs)): use(i, xs[i])` | `for i, x in enumerate(xs):` |
| `r = []` + `r.append(...)` in a loop | list comprehension |
| `if x == True:` | `if x:` |
| `if len(xs) > 0:` | `if xs:` |
| `if x != None:` | `if x is not None:` |
| `try: ... except: pass` | catch specific exceptions |
| Mutable default argument | `def f(x=None): if x is None: x = []` |
| `dict.has_key(k)` (doesn't exist in 3) | `k in dict` |
| Manually iterating two lists with index | `for a, b in zip(xs, ys):` |
| String concat in loop with `+=` | `"".join(parts)` |
| Re-reading dict in loop: `if k in d: v = d[k]` | `if (v := d.get(k)) is not None:` |

**Two more rules.**
- **Flat is better than nested.** If you have 4 levels of indentation, refactor.
- **Errors should never pass silently.** No bare `except:`. Ever.

---

## 20. Twenty-five problems (with full structure)

Each problem follows: **Statement → Intuition → Brute force → Optimized → Complexity → Edge cases → Real-world → Follow-ups.** Try every problem before reading the solution.

---

### Problem 1 — Two sum

**Statement.** Given `nums: list[int]` and `target: int`, return indices `(i, j)` such that `nums[i] + nums[j] == target`. Each input has exactly one solution.

**Intuition.** For each `x`, we need `target - x`. Looking up "have I seen this?" should be O(1) → a dict.

**Brute force.**
```python
def two_sum_brute(nums, target):
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return (i, j)
```
O(n²) time, O(1) space.

**Optimized.**
```python
def two_sum(nums: list[int], target: int) -> tuple[int, int]:
    seen: dict[int, int] = {}                   # value -> index
    for i, x in enumerate(nums):
        if (j := seen.get(target - x)) is not None:
            return (j, i)
        seen[x] = i
    raise ValueError("no solution")
```
**I/O example.**
```python
two_sum([2, 7, 11, 15], 9)   # (0, 1)
```

**Complexity.** O(n) time, O(n) space.

**Edge cases.** Empty list (raise); duplicates (`[3,3]`, target 6 → (0,1) — works); negatives (works).

**Real-world.** Pair-finding in transactions ("did two transactions sum to a flagged amount?"), feature-pair joins.

**Follow-ups.** Three sum (sort + two pointers, O(n²)). Two sum II (sorted input → two pointers, O(1) extra space). Streaming version (reservoir).

---

### Problem 2 — Group anagrams

**Statement.** Given `words: list[str]`, group anagrams together. `["eat","tea","tan","ate","nat","bat"]` → `[["eat","tea","ate"],["tan","nat"],["bat"]]`.

**Intuition.** Anagrams share a canonical form. Sort the letters, or use a letter-count tuple — same key.

**Brute force.** Compare every pair of words by sorted form: O(n² · k log k).

**Optimized.**
```python
from collections import defaultdict

def group_anagrams(words: list[str]) -> list[list[str]]:
    groups: dict[tuple[int, ...], list[str]] = defaultdict(list)
    for w in words:
        key = tuple(sorted(w))                  # canonical form
        groups[key].append(w)
    return list(groups.values())
```
**I/O example.**
```python
group_anagrams(["eat","tea","tan","ate","nat","bat"])
# [['eat','tea','ate'], ['tan','nat'], ['bat']]
```

**Complexity.** O(n · k log k), where k = max word length.

**Edge cases.** Empty list → `[]`. Empty strings → all in one group.

**Real-world.** Deduplication of permutations in feature engineering; hash-based grouping in MapReduce.

**Follow-ups.** Use a 26-int letter-count tuple — O(n·k) instead of O(n·k log k). Unicode? Use a frozen Counter as the key.

---

### Problem 3 — LRU cache

**Statement.** Implement a fixed-capacity Least-Recently-Used cache with O(1) `get` and `put`.

**Intuition.** Need O(1) lookup → dict. Need O(1) reorder on access → doubly linked list. Combine them, or cheat: Python's `OrderedDict.move_to_end` does both.

**Solution.**
```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache: OrderedDict[int, int] = OrderedDict()

    def get(self, key: int) -> int | None:
        if key not in self.cache: return None
        self.cache.move_to_end(key)             # mark as most-recently used
        return self.cache[key]

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)      # evict oldest
```

**I/O example.**
```python
c = LRUCache(2); c.put(1,"a"); c.put(2,"b"); c.get(1); c.put(3,"c")
c.get(2)   # None — 2 was evicted
```

**Complexity.** O(1) per op; O(capacity) memory.

**Real-world.** This is `functools.lru_cache`. Used in: web request memoization, ML feature caches, DB query caches, model output caches in LLM apps.

**Follow-ups.** Thread-safe version (add a lock). TTL variant (entries expire). Sharded cache for high concurrency.

---

### Problem 4 — Validate balanced brackets

**Statement.** Given a string of `(){}[]`, return True iff every opener has a matching, correctly-nested closer.

**Intuition.** Every closer must match the most recent opener — that's a stack.

**Solution.**
```python
def is_balanced(s: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in ")]}":
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack
```

**I/O example.**
```python
is_balanced("([]{})")   # True
is_balanced("([)]")     # False
is_balanced("(")        # False
```

**Complexity.** O(n) time, O(n) space.

**Real-world.** Parsing JSON, code editors, validating SQL/jinja templates, LLM tool-call argument validation.

**Follow-ups.** Return the index of the first invalid bracket. Support custom bracket pairs. Handle strings with quoted characters (e.g., `"({)"` inside a string literal).

---

### Problem 5 — Merge intervals

**Statement.** Given a list of `(start, end)` intervals, merge overlapping ones.

**Intuition.** Sort by start. Walk through; if the current interval overlaps the last merged one, extend it; else append.

**Solution.**
```python
def merge_intervals(intervals: list[tuple[int,int]]) -> list[tuple[int,int]]:
    if not intervals: return []
    intervals = sorted(intervals)
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:                   # overlap
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged
```

**I/O example.**
```python
merge_intervals([(1,3),(2,6),(8,10),(15,18)])
# [(1,6),(8,10),(15,18)]
```

**Complexity.** O(n log n) for sort; O(n) extra.

**Real-world.** Calendar scheduling, video editing timelines, log compaction, traffic data aggregation.

**Follow-ups.** Insert one new interval into an already-sorted, merged list (O(n)). Streaming version. Inverted: find gaps between intervals.

---

### Problem 6 — Top-K frequent elements

**Statement.** Given `nums: list[int]` and `k: int`, return the `k` most frequent values.

**Intuition.** Count frequencies. Then either sort (O(n log n)) or use a heap (O(n log k)).

**Solution.**
```python
from collections import Counter
import heapq

def top_k(nums: list[int], k: int) -> list[int]:
    counts = Counter(nums)
    return [v for v, _ in heapq.nlargest(k, counts.items(), key=lambda kv: kv[1])]
```

**I/O example.**
```python
top_k([1,1,1,2,2,3], 2)   # [1, 2]
```

**Complexity.** O(n log k).

**Real-world.** Trending topics, top-N product views, hot keys in caches, frequency caps in rate limiting.

**Follow-ups.** Streaming top-K with bounded memory → Count-Min Sketch + heap. Top-K per partition (each user's top 5 pages).

---

### Problem 7 — Iterator that flattens nested lists

**Statement.** Build an iterator that yields integers from `[[1,2],[3],[],[4,[5,6]]]` as `1,2,3,4,5,6`.

**Intuition.** Recursion is natural; explicit stack avoids deep recursion.

**Solution (recursive generator).**
```python
def flatten(it):
    for x in it:
        if isinstance(x, list):
            yield from flatten(x)               # recurse
        else:
            yield x
```

**I/O example.**
```python
list(flatten([1,[2,[3,[4]]],5]))   # [1,2,3,4,5]
```

**Iterative (avoids stack overflow):**
```python
def flatten_iter(it):
    stack = [iter(it)]
    while stack:
        try:
            x = next(stack[-1])
        except StopIteration:
            stack.pop(); continue
        if isinstance(x, list):
            stack.append(iter(x))
        else:
            yield x
```

**Real-world.** Walking nested JSON (LLM tool outputs, API responses), tree traversal in HTML/XML, AST visitors.

**Follow-ups.** Make it generic over any Iterable. Limit max depth. Stream from a file of JSON lines.

---

### Problem 8 — Longest substring without repeating characters

**Statement.** Given a string, return the length of the longest substring with all unique characters.

**Intuition.** Sliding window. Track the last index of each character; when you hit a duplicate inside the window, jump the left pointer past it.

**Solution.**
```python
def longest_unique(s: str) -> int:
    last: dict[str, int] = {}
    left = 0
    best = 0
    for right, ch in enumerate(s):
        if ch in last and last[ch] >= left:
            left = last[ch] + 1
        last[ch] = right
        best = max(best, right - left + 1)
    return best
```

**I/O example.**
```python
longest_unique("abcabcbb")   # 3 ("abc")
longest_unique("")           # 0
```

**Complexity.** O(n) time, O(min(n, alphabet)) space.

**Real-world.** Detecting longest unique-event run in user sessions; deduplication windows in stream processing.

**Follow-ups.** Allow at most K repeats. Return the actual substring. Unicode (works as-is).

---

### Problem 9 — Word frequency from a huge file

**Statement.** Count word frequencies in a 100GB log file, on a machine with 8GB RAM.

**Intuition.** Stream. Don't load the file. `Counter` updates in place.

**Solution.**
```python
from collections import Counter
from pathlib import Path
import re

WORD = re.compile(r"\w+")

def word_counts(path: Path) -> Counter:
    counts: Counter[str] = Counter()
    with path.open(encoding="utf-8") as f:
        for line in f:                          # iterates one line at a time
            counts.update(w.lower() for w in WORD.findall(line))
    return counts
```

**Complexity.** O(total tokens) time, O(unique words) memory.

**Real-world.** This is the canonical MapReduce job. The streaming pattern (`for line in f`) is essential to most data ETL.

**Follow-ups.** Multi-process speedup with `concurrent.futures` (chunk the file by byte ranges). External sort for true big data. Spark/Beam version (Module 12+).

---

### Problem 10 — Reservoir sampling

**Statement.** Sample `k` items uniformly from a stream of unknown length, using O(k) memory.

**Intuition.** For the i-th item (0-indexed), accept it with probability `k/(i+1)`. If accepted, replace a random element of the reservoir.

**Solution.**
```python
import random

def reservoir_sample(stream, k: int) -> list:
    reservoir = []
    for i, item in enumerate(stream):
        if i < k:
            reservoir.append(item)
        else:
            j = random.randint(0, i)
            if j < k:
                reservoir[j] = item
    return reservoir
```

**Complexity.** O(n) time, O(k) memory. Each item ends in the sample with probability k/n exactly.

**Real-world.** Sampling logs for analytics; sampling training examples from a live stream; A/B test traffic capture.

**Follow-ups.** Weighted reservoir (A-Res algorithm). Distributed (sample on each shard, then sample-of-samples).

---

### Problem 11 — Producer-consumer with a bounded queue (asyncio)

**Statement.** One producer puts items on a queue at variable speed; N consumers pull and process. Backpressure when consumers fall behind.

**Solution.**
```python
import asyncio, random

async def producer(q: asyncio.Queue, n: int):
    for i in range(n):
        await q.put(i)
        await asyncio.sleep(random.random()*0.1)
    for _ in range(N_CONSUMERS):
        await q.put(None)                       # poison pill per consumer

async def consumer(name: str, q: asyncio.Queue):
    while (item := await q.get()) is not None:
        await asyncio.sleep(random.random()*0.2)
        print(f"{name} processed {item}")
        q.task_done()

N_CONSUMERS = 3
async def main():
    q: asyncio.Queue = asyncio.Queue(maxsize=10)   # backpressure: producer blocks at 10
    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer(q, 30))
        for i in range(N_CONSUMERS):
            tg.create_task(consumer(f"c{i}", q))

asyncio.run(main())
```

**Real-world.** Web scraping pipelines, kafka consumer fan-out, model inference batching. The `maxsize` is critical — it's how you avoid OOM when downstream is slow.

**Follow-ups.** Replace the poison pill with a `done` event. Add per-item timeouts. Make it cancellation-safe.

---

### Problem 12 — Rate limiter

**Statement.** Allow at most `n` requests per `t` seconds per key.

**Intuition.** Token bucket: refill `n/t` tokens per second; each request consumes one.

**Solution.**
```python
import time
from dataclasses import dataclass, field

@dataclass
class TokenBucket:
    rate: float                                  # tokens per second
    capacity: float
    tokens: float = field(init=False)
    last: float = field(init=False)

    def __post_init__(self):
        self.tokens = self.capacity
        self.last = time.monotonic()

    def allow(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.last
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

# 5 requests per second, burst up to 10
bucket = TokenBucket(rate=5, capacity=10)
for _ in range(20):
    print(bucket.allow())
    time.sleep(0.1)
```

**Real-world.** API gateways, scraping politeness, LLM API quotas. Combine with Redis for distributed rate limiting.

**Follow-ups.** Sliding-window log limiter (more accurate, more memory). Distributed version using Redis `INCR`+`EXPIRE`.

---

### Problem 13 — Type-safe config loader

**Statement.** Load a config file, validate types, fail fast with clear errors.

**Solution.**
```python
from pydantic import BaseModel, Field, ValidationError
import tomllib

class DBConfig(BaseModel):
    host: str
    port: int = Field(ge=1, le=65535)
    user: str
    password: str

class AppConfig(BaseModel):
    debug: bool = False
    db: DBConfig
    allowed_origins: list[str] = []

def load_config(path: str) -> AppConfig:
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    try:
        return AppConfig(**raw)
    except ValidationError as e:
        print(e)                                # pydantic gives precise errors
        raise
```

**Real-world.** Every production service. Pydantic is the standard config validator in Python now.

**Follow-ups.** Read from env vars (`pydantic-settings`). Hot-reload on file change. Hierarchical configs (base + per-environment overrides).

---

### Problem 14 — Streaming JSON-lines parser

**Statement.** Parse a 50GB `.jsonl` file (one JSON object per line). Yield validated records. Skip and log malformed lines.

**Solution.**
```python
import json, logging
from pathlib import Path
from typing import Iterator

log = logging.getLogger(__name__)

def stream_jsonl(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line: continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                log.warning("line %d: %s", lineno, e)
```

**Real-world.** Log analytics, training data ingestion (most LLM datasets are jsonl), event sourcing.

**Follow-ups.** Batched yield (yield N at a time for downstream batch processing). Parallel parsing across CPU cores. Zstandard-compressed jsonl (`.jsonl.zst`).

---

### Problem 15 — Retry with exponential backoff and jitter

**Solution.**
```python
import functools, random, time

def retry(times=5, base=0.5, cap=30.0, exceptions=(Exception,)):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(times):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    if attempt == times - 1: raise
                    delay = min(cap, base * 2**attempt)
                    delay = random.uniform(0, delay)        # full jitter
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(times=4, exceptions=(ConnectionError, TimeoutError))
def fetch_external(url): ...
```

**Real-world.** Every external API call in production should have this. AWS docs even specify "full jitter" as the recommended strategy.

**Follow-ups.** Async version. Per-attempt logging. `tenacity` library is the production-grade choice — but you should be able to write the basic version yourself.

---

### Problem 16 — Memoize with a TTL

**Solution.**
```python
import functools, time

def ttl_cache(ttl: float):
    def decorator(fn):
        cache: dict = {}
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            if key in cache:
                value, expires = cache[key]
                if now < expires: return value
            value = fn(*args, **kwargs)
            cache[key] = (value, now + ttl)
            return value
        return wrapper
    return decorator

@ttl_cache(ttl=60)
def get_user_profile(user_id: int) -> dict: ...
```

**Real-world.** Caching slow lookups (DB, external API) where staleness for a minute is acceptable. Used heavily in web request handlers.

**Follow-ups.** Make it thread-safe (lock around the dict). Add LRU eviction. Async version (cache per-key locks to avoid the thundering herd).

---

### Problem 17 — Topological sort

**Statement.** Given dependencies between tasks, return an order in which tasks can run, or detect a cycle.

**Solution (Kahn's algorithm).**
```python
from collections import defaultdict, deque

def topo_sort(tasks: list[str], deps: list[tuple[str,str]]) -> list[str]:
    """deps: (a, b) means a must run before b."""
    indeg = {t: 0 for t in tasks}
    graph: dict[str, list[str]] = defaultdict(list)
    for a, b in deps:
        graph[a].append(b)
        indeg[b] += 1

    q = deque(t for t, d in indeg.items() if d == 0)
    order = []
    while q:
        t = q.popleft()
        order.append(t)
        for nxt in graph[t]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)
    if len(order) != len(tasks):
        raise ValueError("cycle detected")
    return order
```

**I/O example.**
```python
topo_sort(["a","b","c","d"], [("a","b"),("b","c"),("a","d")])
# ['a', 'b', 'd', 'c']  (one valid order)
```

**Real-world.** Build systems (make, bazel), Airflow DAG execution, ML pipeline scheduling, package dependency resolution.

**Follow-ups.** Lexicographically smallest order (use a heap instead of a deque). Parallel scheduling (ready set, not order). Cycle reporting (DFS approach).

---

### Problem 18 — Singleton via decorator

**Solution.**
```python
def singleton(cls):
    instances = {}
    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

@singleton
class ConfigManager:
    def __init__(self): self.settings = {}

a = ConfigManager(); b = ConfigManager()
print(a is b)   # True
```

**Real-world warning.** Singletons are often a smell. Prefer dependency injection (pass the config object explicitly). Use singletons sparingly — DB connection pools, logger registries.

**Follow-ups.** Thread-safe singleton (double-checked locking). Why module-level globals are usually a better pattern in Python.

---

### Problem 19 — Sliding window maximum

**Statement.** Given an array and window size `k`, return the max of each window.

**Intuition.** Naive is O(n·k). Use a monotonic deque: keep indices whose values are decreasing; the front is always the max.

**Solution.**
```python
from collections import deque

def sliding_max(nums: list[int], k: int) -> list[int]:
    dq: deque[int] = deque()                    # stores indices
    out = []
    for i, x in enumerate(nums):
        while dq and dq[0] <= i - k:            # drop indices out of window
            dq.popleft()
        while dq and nums[dq[-1]] < x:          # drop smaller from the right
            dq.pop()
        dq.append(i)
        if i >= k - 1:
            out.append(nums[dq[0]])
    return out
```

**I/O example.**
```python
sliding_max([1,3,-1,-3,5,3,6,7], 3)
# [3, 3, 5, 5, 6, 7]
```

**Complexity.** O(n) — each index enters and leaves the deque at most once.

**Real-world.** Real-time max-over-window stats, anomaly detection on metric streams, technical indicators in finance.

**Follow-ups.** Sliding window minimum (mirror). Sliding median (two heaps).

---

### Problem 20 — Pure-functional pipeline with generators

**Statement.** Process an iterable through a series of transformations: filter, map, batch, deduplicate. Lazy and composable.

**Solution.**
```python
from typing import Iterator, Callable, TypeVar, Iterable

T = TypeVar("T")
U = TypeVar("U")

def pipe(it: Iterable[T], *steps: Callable[[Iterable], Iterable]) -> Iterator:
    for step in steps:
        it = step(it)
    return iter(it)

def keep(pred):    return lambda it: (x for x in it if pred(x))
def transform(fn): return lambda it: (fn(x) for x in it)
def dedup():
    def _go(it):
        seen = set()
        for x in it:
            if x not in seen:
                seen.add(x); yield x
    return _go
def batch(n):
    def _go(it):
        buf = []
        for x in it:
            buf.append(x)
            if len(buf) == n: yield buf; buf = []
        if buf: yield buf
    return _go

result = pipe(
    range(20),
    keep(lambda x: x % 2 == 0),
    transform(lambda x: x*x),
    dedup(),
    batch(3),
)
print(list(result))
# [[0, 4, 16], [36, 64, 100], [144, 196, 256], [324]]
```

**Real-world.** Data ETL, log processing, training-data preprocessing. This is the conceptual basis for `tf.data`, `torch.utils.data`, and Hugging Face `datasets`.

**Follow-ups.** Async pipeline. Parallel `map` step. Add error-tolerance (skip-with-log on exceptions).

---

### Problem 21 — Custom context manager for DB transactions

**Solution.**
```python
from contextlib import contextmanager
import sqlite3

@contextmanager
def transaction(conn: sqlite3.Connection):
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

with sqlite3.connect(":memory:") as conn:
    conn.execute("CREATE TABLE t(x INT)")
    with transaction(conn) as cur:
        cur.execute("INSERT INTO t VALUES (1)")
        cur.execute("INSERT INTO t VALUES (2)")
    # auto-committed
```

**Real-world.** Every database write path. The same pattern applies to file writes (write to `.tmp`, rename on success), Redis pipelines, etc.

**Follow-ups.** Async version with `aiosqlite`. Nested transactions (savepoints). Distributed transactions (don't — use sagas instead).

---

### Problem 22 — Async fan-out with bounded concurrency

**Statement.** Fetch 10,000 URLs but never have more than 50 in flight.

**Solution.**
```python
import asyncio, httpx

async def fetch(client, url, sem):
    async with sem:                             # semaphore caps in-flight tasks
        r = await client.get(url, timeout=10)
        return url, r.status_code

async def fetch_all(urls: list[str], concurrency: int = 50):
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient() as client:
        tasks = [fetch(client, u, sem) for u in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

**Real-world.** Web crawlers, batch enrichment from external APIs, sending fan-out notifications. Without the semaphore you'll get rate-limited or OOM.

**Follow-ups.** Stream results as they arrive (`as_completed`). Per-host concurrency caps. Retries with backoff per task.

---

### Problem 23 — Detect cycle in a linked structure

**Statement.** Given a graph as `dict[str, list[str]]`, detect if there's a cycle.

**Solution (DFS with three-color marking).**
```python
WHITE, GRAY, BLACK = 0, 1, 2

def has_cycle(graph: dict[str, list[str]]) -> bool:
    color = {n: WHITE for n in graph}
    def dfs(node):
        color[node] = GRAY
        for nxt in graph.get(node, []):
            if color.get(nxt, WHITE) == GRAY:   # back edge → cycle
                return True
            if color.get(nxt, WHITE) == WHITE and dfs(nxt):
                return True
        color[node] = BLACK
        return False
    return any(color[n] == WHITE and dfs(n) for n in graph)
```

**Real-world.** Detecting circular imports, dependency-graph validation in Airflow/dbt, deadlock detection.

**Follow-ups.** Return one cycle (not just yes/no). Iterative DFS for huge graphs (avoid stack overflow). Strongly-connected components (Tarjan/Kosaraju).

---

### Problem 24 — Implement a simple ORM-like data layer

**Statement.** A class that maps to a SQLite table; supports `save`, `get`, `find`.

**Solution.**
```python
import sqlite3
from dataclasses import dataclass, asdict, fields
from typing import ClassVar, Self

@dataclass
class User:
    id: int | None
    name: str
    email: str
    _table: ClassVar[str] = "users"

    @classmethod
    def init_schema(cls, conn):
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {cls._table}(
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )""")

    def save(self, conn) -> Self:
        cols = [f.name for f in fields(self) if f.name != "id"]
        placeholders = ",".join("?" for _ in cols)
        cur = conn.execute(
            f"INSERT INTO {self._table}({','.join(cols)}) VALUES ({placeholders})",
            [getattr(self, c) for c in cols],
        )
        self.id = cur.lastrowid
        return self

    @classmethod
    def get(cls, conn, id: int) -> Self | None:
        row = conn.execute(f"SELECT * FROM {cls._table} WHERE id=?", (id,)).fetchone()
        return cls(**dict(zip([d[0] for d in conn.execute(f"SELECT * FROM {cls._table} LIMIT 0").description], row))) if row else None
```

**Real-world.** This is a toy version of what SQLAlchemy / SQLModel does. Useful to write once to understand what real ORMs are doing under the hood.

**Follow-ups.** Add `update`, `delete`, `find(**filters)`. Connection pooling. Migrations (Alembic-style).

---

### Problem 25 — Find duplicate files by content

**Statement.** Given a directory, find files with identical content efficiently. (Don't hash everything.)

**Intuition.** Files with different sizes can't be equal. Group by size first, then hash within each group.

**Solution.**
```python
from pathlib import Path
from collections import defaultdict
import hashlib

def find_duplicates(root: Path) -> list[list[Path]]:
    by_size: dict[int, list[Path]] = defaultdict(list)
    for p in root.rglob("*"):
        if p.is_file():
            by_size[p.stat().st_size].append(p)

    duplicates = []
    for size, paths in by_size.items():
        if len(paths) < 2: continue             # unique size → not a dup
        by_hash: dict[str, list[Path]] = defaultdict(list)
        for p in paths:
            h = hashlib.sha256()
            with p.open("rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            by_hash[h.hexdigest()].append(p)
        for group in by_hash.values():
            if len(group) > 1: duplicates.append(group)
    return duplicates
```

**Real-world.** Storage dedup tools, media library managers, build artifact caches, S3 dedup before upload.

**Follow-ups.** Cheap pre-filter: hash only the first 4KB before full hash. Parallel hashing with a process pool. xxh3 instead of sha256 if you trust collisions to be vanishingly rare.

---

## 21. Three mini-projects

These are smaller than the 25 flagship projects you'll see in `/projects/`. They're meant to be doable in 1–3 hours each and exercise everything in this module.

### Mini-project A — A typed CLI for analyzing log files

Build a command `loginspect FILE [--level=ERROR] [--since=2026-01-01]` that:
- Streams a possibly-huge log file (one JSON object per line).
- Filters by level and time.
- Prints a summary: top-N error messages, requests per minute, p50/p95/p99 latency.

**Skills exercised:** generators, `argparse`, `pathlib`, `datetime`, `Counter`, `statistics`, type hints, `pytest`. Use `uv` to package it as an installable CLI (`pyproject.toml` with `[project.scripts]`).

### Mini-project B — Async URL health-checker

A tool that takes a list of URLs and returns each URL's status code, response time, and (if HTTPS) cert expiry days. Concurrency limited to 20.

**Skills exercised:** `asyncio`, `httpx`, semaphores, `dataclass`, `csv` output, retries with backoff. Goal: 1,000 URLs in under 30 seconds.

### Mini-project C — A small in-memory key-value store with TTL

Class with `set(key, value, ttl)`, `get(key)`, `delete(key)`. Lazy expiration on read; periodic cleanup task. Thread-safe and async-safe variants.

**Skills exercised:** `threading.Lock`, `asyncio.Lock`, `time.monotonic`, generics with `[T]`, `__contains__`, `__len__`. Bonus: implement persistence to disk on shutdown.

---

## 22. Real-world usage map (where every concept actually shows up)

| Concept | Where you'll see it in the rest of the bible |
|---|---|
| Dataclasses + Pydantic | FastAPI request/response models; LLM tool schemas; config |
| Type hints | All FastAPI routes, all DSPy programs, `pydantic-ai` agents |
| Generators | Streaming model outputs; `datasets` library; SSE responses |
| Decorators | FastAPI route registration; `@tool` for LLM agents; pytest fixtures |
| Context managers | DB transactions; `torch.no_grad()`; `with mlflow.start_run()` |
| asyncio + TaskGroup | FastAPI handlers; agent fan-out; concurrent LLM calls |
| `multiprocessing` | DataLoader workers in PyTorch; sklearn `n_jobs=-1` |
| `Counter` / `defaultdict` | Feature engineering; bag-of-words; agent state tracking |
| `pathlib` | Dataset loaders; checkpoint paths; artifact stores |
| Logging | Every production service. Structured logs feed observability |
| Protocols | Plugin-style architectures; LangGraph node interfaces |

If a concept feels abstract now, you'll see it return concretely within two modules.

---

## 23. Interview pitfalls — what NOT to say

- **"`is` and `==` are the same."** They aren't. `is` is identity, `==` is equality. Mixing them up on small ints will *seem* to work because of CPython's small-int caching — and break in production on bigger numbers.
- **"Python doesn't have private variables."** It does, by convention: `_name` (internal), `__name` (name-mangled). Pythonic style is "we're all consenting adults" — but you should know the convention.
- **"Threading speeds up CPU work."** It does not, due to the GIL. Use processes or native code.
- **"I'd use a list because lookups are fast."** Lists are O(n) for `in`. Use a set or dict for membership.
- **"I'd write a metaclass for that."** Almost never the right answer. Decorators or `__init_subclass__` are simpler 99% of the time.
- **"Mutable default arguments are fine."** They aren't (§2.1). This is the most common Python interview gotcha.
- **"I prefer `os.path` because pathlib is slow."** Pathlib is fast enough and dramatically clearer. Use it.
- **"I'd use threads for the API calls because async is complicated."** It's worth learning. For 1000+ concurrent I/O ops, asyncio is decisively better.

**How to communicate while solving.** Narrate three things out loud:
1. **Restate the problem in your own words.** "So I have N items and I need…"
2. **State your initial approach + complexity** before coding. "I'll do brute force first — O(n²) — then optimize."
3. **Call out edge cases proactively.** "What if the list is empty? What if there are duplicates?"

This is what separates a strong candidate from a smart one.

---

## 24. Cheatsheet (1-page reference)

```text
ENVIRONMENT (uv)
  uv python install 3.12         install Python
  uv init proj                   create project
  uv add PKG                     add dep
  uv add --dev pytest ruff mypy  dev deps
  uv run CMD                     run in venv
  uv sync                        rebuild env

VARIABLE / TYPE BASICS
  x: int = 1; y: float = 1.0; b: bool = True
  s: str = "hi"; xs: list[int] = []; d: dict[str,int] = {}
  maybe: int | None = None       (3.10+)
  Final: x: Final = 5            (constant)
  Literal: m: Literal["r","w"]   (enum-ish)
  Annotated: Annotated[int,"id"]

STRINGS
  f"{x}"; f"{x:>10.2f}"; f"{x:,}"; f"{x:.1%}"; f"{x=}"
  s.strip(); s.split(); ",".join(xs); s.startswith(); s.replace()

LIST/DICT/SET METHODS
  list:  .append .extend .insert .pop .remove .sort(reverse=,key=) .index .count
  dict:  .get(k,default) .setdefault(k,d) .pop(k,d) .update() .keys() .values() .items()
  set:   .add .remove .discard | & - ^

CONTROL FLOW
  if/elif/else; for/else; while/else; match/case; walrus :=
  ternary: x if cond else y

COMPREHENSIONS
  [f(x) for x in xs if g(x)]
  {k:v for k,v in pairs}
  {f(x) for x in xs}
  (f(x) for x in xs)              generator (lazy)

FUNCTIONS
  def f(pos, /, normal, *, kw, **rest) -> R: ...
  *args, **kwargs unpacking on call: f(*xs), f(**d)
  default-mutable: use None sentinel
  type-generic 3.12+: def f[T](xs: list[T]) -> T: ...

OOP — DATACLASSES FIRST
  @dataclass(slots=True, frozen=True)
  class C:
      x: int
      tags: list[str] = field(default_factory=list)
  @property / @classmethod / @staticmethod
  Protocol for structural typing

ITERATION
  for x in iter; enumerate(xs); zip(xs, ys); reversed(xs); sorted(xs, key=, reverse=)
  itertools: chain islice groupby product combinations accumulate
  yield / yield from; gen exprs; functools.cache

FILES
  Path("a") / "b"; .read_text(encoding="utf-8"); .write_text(...)
  open(p, encoding="utf-8") as f; for line in f: ...
  json.load/dump; csv.DictReader; tomllib.load (rb)

ERRORS
  try/except/else/finally; raise X(...) from cause
  custom: class AppError(Exception): pass
  EAFP > LBYL; never bare except; never except BaseException

CONCURRENCY DECISION
  CPU-bound  → ProcessPoolExecutor / multiprocessing
  IO short   → asyncio + httpx/aiomysql/aiokafka
  IO simple  → ThreadPoolExecutor
  3.11+ async TaskGroup; never block in async (use to_thread)

LOGGING
  log = logging.getLogger(__name__)
  log.info("event %s", val)         lazy formatting
  log.error("...", exc_info=True)
  structured: structlog

PERFORMANCE ORDER
  algo > data structure > vectorize (numpy) > cache > concurrency > native
  py-spy record/top for profiling

PYTHONIC IDIOMS
  for x in xs                       not for i in range(len(xs))
  for i,x in enumerate(xs)
  if xs / if not xs                 not if len(xs) > 0
  x is None / is not None
  with open(...) as f:              context manager
  d.get(k, default)                 not if k in d: d[k] else default
  "".join(parts)                    not s += in loop
  enumerate / zip                   not manual indexing
  set for membership                not list

DUNDER QUICK TABLE
  __init__   __repr__   __str__
  __eq__     __hash__   __lt__
  __len__    __iter__   __next__   __contains__
  __getitem__ __setitem__ __delitem__
  __enter__  __exit__
  __call__   __add__    __sub__

TESTING (pytest)
  assert; pytest.raises(E); @pytest.mark.parametrize("a,b", [...])
  @pytest.fixture; conftest.py for shared fixtures
  pytest -k pattern; pytest --cov=src

TOOLS
  ruff   (lint+format, replaces flake8/black/isort)
  mypy   (type check)  / pyright (faster, MS)
  pytest (test)        / hypothesis (property tests)
  uv     (env+deps)    / py-spy (profile)
```

---

## 25. Prerequisites & next steps

**Prerequisites covered? You can:**
- Set up a uv project from scratch.
- Read someone's typed Python and explain what each `|`, `[`, `Protocol`, `@dataclass` does.
- Reason about whether a piece of code mutates shared state.
- Pick `list` vs `tuple` vs `dict` vs `set` correctly without thinking.
- Write a generator and a context manager from scratch.
- Decide between threads, processes, and asyncio.
- Run tests with pytest and types with mypy.

**Next steps in the bible:**
- **Module 2 — Data Stack (numpy, pandas, polars, viz).** Now that you know Python, we go fast.
- **Module 4 — FastAPI.** Most of what you'll build externally.
- The 25 flagship **projects** start using all of this from project 1 onward.

**External study (if you want depth on this module specifically):**
- *Fluent Python, 2nd ed.* (Ramalho) — the deepest single book on the language.
- The official Python tutorial — surprisingly excellent.
- PEP 8 (style), PEP 20 (Zen), PEP 484 (typing), PEP 695 (modern generics).

---

*End of Module 1. Module 2 covers numpy, pandas, polars, and the visualization stack — same structure, same standards.*
