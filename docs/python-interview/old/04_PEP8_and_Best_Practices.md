# 04 — PEP8, Coding Standards & Best Practices
## Complete Interview Questions with Examples

---

## 4.1 PEP 8 — Style Guide

### Q1: What is PEP 8 and why does it matter?

**Answer:**
PEP 8 is Python's official style guide. It ensures consistent, readable code across the Python ecosystem. Most companies enforce PEP 8 compliance in code reviews.

```python
# ═══════════════════════════════════════
# NAMING CONVENTIONS
# ═══════════════════════════════════════

# Variables and functions: snake_case
user_name = "Alice"
def calculate_total_price(items):
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
DATABASE_URL = "postgresql://localhost/db"
PI = 3.14159

# Classes: PascalCase (CapWords)
class UserAccount:
    pass
class HTTPClient:
    pass

# Private: prefix with underscore
_internal_cache = {}
def _helper_function():
    pass

# Name mangling: double underscore prefix
class MyClass:
    __private_attr = 42     # Becomes _MyClass__private_attr

# Dunder methods: reserved for Python
def __init__(self):
    pass

# Module names: short, lowercase, no hyphens
# good: utils.py, models.py, db_helpers.py
# bad:  Utils.py, my-module.py, DBHelpers.py

# Package names: short, lowercase, no underscores
# good: mypackage, requests, flask
# bad:  my_package, MyPackage


# ═══════════════════════════════════════
# INDENTATION & SPACING
# ═══════════════════════════════════════

# 4 spaces per indentation level (NEVER tabs)
def function():
    if True:
        for i in range(10):
            print(i)

# Line continuation — aligned with opening delimiter
result = some_function(
    argument_one, argument_two,
    argument_three, argument_four
)

# OR hanging indent
result = some_function(
    argument_one,
    argument_two,
    argument_three,
)

# Binary operators — break BEFORE operator
total = (first_variable
         + second_variable
         - third_variable)

# Spaces around operators
x = 5
y = x + 3
z = x**2            # Exception: highest priority operator, no spaces
result = (a + b) * (c - d)

# No spaces in keyword arguments or defaults
def func(key=value):
    pass
func(arg=value)

# Spaces after commas, colons in dicts
my_list = [1, 2, 3]
my_dict = {"key": "value", "name": "Alice"}

# No space before colon in slices
my_list[1:3]
my_list[::2]

# Maximum line length: 79 characters (72 for docstrings)
# Use parentheses for implicit continuation
long_string = (
    "This is a very long string that "
    "spans multiple lines for readability"
)


# ═══════════════════════════════════════
# BLANK LINES
# ═══════════════════════════════════════

# Two blank lines: before/after top-level definitions
import os


class MyClass:
    """First class."""
    pass


class AnotherClass:
    """Second class."""
    pass


def top_level_function():
    pass

# One blank line: between methods in a class
class Example:
    def method_one(self):
        pass

    def method_two(self):
        pass

# Use blank lines sparingly inside functions to indicate logical sections


# ═══════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════

# Order: stdlib → third-party → local (separated by blank lines)
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, request

from mypackage.models import User
from mypackage.utils import validate

# One import per line (for modules)
import os
import sys
# NOT: import os, sys

# Specific imports are OK on one line
from os.path import join, exists

# Avoid wildcard imports
# ❌ from module import *
# ✅ from module import specific_function

# Absolute imports preferred over relative
# ✅ from mypackage.utils import helper
# ⚠️ from .utils import helper  (OK within packages)
```

---

### Q2: What are PEP 257 (Docstrings) and PEP 484 (Type Hints)?

**Answer:**

```python
# ═══════════════════════════════════════
# PEP 257 — Docstring Conventions
# ═══════════════════════════════════════

# One-line docstring (simple functions)
def square(n):
    """Return the square of n."""
    return n ** 2

# Multi-line docstring (complex functions)
def fetch_user_data(user_id, include_history=False):
    """Fetch user data from the database.

    Retrieves user profile information and optionally includes
    their activity history.

    Args:
        user_id: The unique identifier for the user.
        include_history: If True, include activity history.
            Defaults to False.

    Returns:
        A dict mapping user fields to their values. Example:
            {'name': 'Alice', 'email': 'alice@example.com'}

    Raises:
        ValueError: If user_id is negative.
        NotFoundError: If no user matches the given ID.

    Example:
        >>> data = fetch_user_data(42)
        >>> print(data['name'])
        'Alice'
    """
    pass

# Class docstring
class DataProcessor:
    """Process and transform raw data into structured formats.

    This class handles data validation, cleaning, and transformation
    for the analytics pipeline.

    Attributes:
        source: The data source connection string.
        batch_size: Number of records to process at a time.

    Example:
        >>> processor = DataProcessor("s3://bucket/data")
        >>> processor.run()
    """

    def __init__(self, source, batch_size=1000):
        """Initialize DataProcessor.

        Args:
            source: Data source connection string.
            batch_size: Records per batch. Defaults to 1000.
        """
        self.source = source
        self.batch_size = batch_size


# ═══════════════════════════════════════
# PEP 484 — Type Hints (see also File 03 Q7)
# ═══════════════════════════════════════

from typing import Optional

def process_data(
    data: list[dict[str, str]],
    limit: Optional[int] = None,
    *,
    strict: bool = False
) -> dict[str, int]:
    """Process data with type hints for clarity and tooling."""
    results: dict[str, int] = {}
    for item in data[:limit]:
        key = item.get("name", "unknown")
        results[key] = results.get(key, 0) + 1
    return results
```

---

### Q3: Explain Python code quality tools and linters.

**Answer:**

```python
# ═══════════════════════════════════════
# LINTERS & FORMATTERS
# ═══════════════════════════════════════

# 1. Ruff — Modern, extremely fast linter + formatter (replaces flake8, isort, black)
#    pip install ruff
#    ruff check .           # Lint
#    ruff format .          # Format
#    ruff check --fix .     # Auto-fix

# pyproject.toml configuration:
"""
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "SIM"]
# E: pycodestyle errors, F: pyflakes, W: warnings
# I: isort, N: naming, UP: pyupgrade, B: bugbear, SIM: simplify
"""

# 2. mypy — Static type checker
#    pip install mypy
#    mypy mypackage/
"""
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
"""

# 3. pylint — Comprehensive linter (more opinionated)
#    pip install pylint
#    pylint mypackage/

# 4. pre-commit — Run checks before every commit
"""
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
"""


# ═══════════════════════════════════════
# COMMON PEP8 VIOLATIONS & FIXES
# ═══════════════════════════════════════

# E711: Comparison to None
# ❌ if x == None:
# ✅ if x is None:

# E712: Comparison to True/False
# ❌ if x == True:
# ✅ if x:
# ❌ if x == False:
# ✅ if not x:

# E721: Don't compare types, use isinstance
# ❌ if type(x) == int:
# ✅ if isinstance(x, int):

# W291: Trailing whitespace
# W292: No newline at end of file
# W293: Whitespace before comment

# E501: Line too long (>79 chars)
# Solution: Use parentheses or refactor

# F401: Imported but unused
# Solution: Remove unused imports

# F811: Redefined unused name
# Solution: Remove duplicate definitions
```

---

### Q4: What are Python's anti-patterns? What should senior developers avoid?

**Answer:**

```python
# ═══════════════════════════════════════
# ANTI-PATTERNS TO AVOID
# ═══════════════════════════════════════

# 1. Using mutable default arguments
# ❌ Bad
def append_to(element, target=[]):
    target.append(element)
    return target
# ✅ Good
def append_to(element, target=None):
    if target is None:
        target = []
    target.append(element)
    return target

# 2. Catching broad exceptions
# ❌ Bad
try:
    do_something()
except Exception:
    pass    # Silently swallowing ALL errors
# ✅ Good
try:
    do_something()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    handle_error()

# 3. Using string concatenation in loops
# ❌ Bad — O(n²) due to string immutability
result = ""
for item in large_list:
    result += str(item) + ","
# ✅ Good — O(n)
result = ",".join(str(item) for item in large_list)

# 4. Not using context managers
# ❌ Bad
f = open("file.txt")
data = f.read()
f.close()    # Might not execute if exception occurs
# ✅ Good
with open("file.txt") as f:
    data = f.read()

# 5. Unnecessary use of range(len())
# ❌ Bad
for i in range(len(items)):
    print(items[i])
# ✅ Good
for item in items:
    print(item)
# If you need index:
for i, item in enumerate(items):
    print(i, item)

# 6. Using type() for type checking
# ❌ Bad
if type(x) == list:
    pass
# ✅ Good
if isinstance(x, list):
    pass

# 7. Not using dict.get() for defaults
# ❌ Bad
if key in my_dict:
    value = my_dict[key]
else:
    value = default
# ✅ Good
value = my_dict.get(key, default)

# 8. Repeated dictionary lookups
# ❌ Bad
if user_id in users:
    user = users[user_id]
    process(user)
# ✅ Good
user = users.get(user_id)
if user is not None:
    process(user)

# 9. God classes (classes doing too much)
# ❌ Bad: UserManagerEmailSenderReportGenerator class
# ✅ Good: Separate UserManager, EmailSender, ReportGenerator

# 10. Magic numbers
# ❌ Bad
if status == 3:
    retry()
# ✅ Good
STATUS_RETRYABLE = 3
if status == STATUS_RETRYABLE:
    retry()
# Or better: use Enum
from enum import Enum
class Status(Enum):
    RETRYABLE = 3
```

---

### Q5: Explain important PEPs every Python developer should know.

**Answer:**

| PEP | Title | Key Point |
|-----|-------|-----------|
| PEP 8 | Style Guide | Coding conventions for Python |
| PEP 20 | Zen of Python | `import this` — guiding principles |
| PEP 257 | Docstring Conventions | How to write docstrings |
| PEP 484 | Type Hints | Function annotations for types |
| PEP 526 | Variable Annotations | `x: int = 5` |
| PEP 572 | Walrus Operator | `if (n := len(a)) > 10:` |
| PEP 570 | Positional-Only Params | `def f(x, y, /):` |
| PEP 612 | ParamSpec | Preserve callable signatures in decorators |
| PEP 621 | Project Metadata | `pyproject.toml` standard |
| PEP 636 | Structural Pattern Matching | `match/case` (Python 3.10) |
| PEP 703 | Making the GIL Optional | Free-threaded Python |
| PEP 695 | Type Parameter Syntax | `type Point = tuple[int, int]` (3.12) |

```python
# The Zen of Python
import this
"""
Key principles:
- Beautiful is better than ugly.
- Explicit is better than implicit.
- Simple is better than complex.
- Readability counts.
- There should be one — and preferably only one — obvious way to do it.
- If the implementation is hard to explain, it's a bad idea.
- Namespaces are one honking great idea — let's do more of those!
"""

# Pattern matching (PEP 636, Python 3.10+)
def process_command(command):
    match command.split():
        case ["quit"]:
            return "Exiting..."
        case ["go", direction]:
            return f"Going {direction}"
        case ["pick", "up", item]:
            return f"Picked up {item}"
        case ["drop", *items]:
            return f"Dropped {', '.join(items)}"
        case _:
            return "Unknown command"

print(process_command("go north"))        # "Going north"
print(process_command("pick up sword"))   # "Picked up sword"
print(process_command("drop a b c"))      # "Dropped a, b, c"

# Advanced pattern matching with guards and types
def handle_event(event):
    match event:
        case {"type": "click", "x": x, "y": y} if x > 0 and y > 0:
            return f"Click at ({x}, {y})"
        case {"type": "keypress", "key": str(key)}:
            return f"Key pressed: {key}"
        case {"type": "resize", "width": int(w), "height": int(h)}:
            return f"Resized to {w}x{h}"
        case _:
            return "Unknown event"
```

---

### Q6: Explain SOLID principles applied to Python.

**Answer:**

```python
from abc import ABC, abstractmethod

# ═══════════════════════════════════════
# S — Single Responsibility Principle
# ═══════════════════════════════════════
# Each class should have ONE reason to change

# ❌ Bad — does too much
class UserManagerBad:
    def create_user(self, data): pass
    def send_email(self, user, msg): pass
    def generate_report(self, users): pass

# ✅ Good — separated concerns
class UserRepository:
    def create(self, data): pass
    def find(self, user_id): pass

class EmailService:
    def send(self, to, subject, body): pass

class UserReportGenerator:
    def generate(self, users): pass


# ═══════════════════════════════════════
# O — Open/Closed Principle
# ═══════════════════════════════════════
# Open for extension, closed for modification

# ❌ Bad — must modify to add new discount type
class DiscountCalculatorBad:
    def calculate(self, price, discount_type):
        if discount_type == "percentage":
            return price * 0.9
        elif discount_type == "flat":
            return price - 10
        # Must add more elif for each new type!

# ✅ Good — extend by adding new classes
class Discount(ABC):
    @abstractmethod
    def apply(self, price: float) -> float:
        pass

class PercentageDiscount(Discount):
    def __init__(self, percent: float):
        self.percent = percent
    def apply(self, price):
        return price * (1 - self.percent / 100)

class FlatDiscount(Discount):
    def __init__(self, amount: float):
        self.amount = amount
    def apply(self, price):
        return price - self.amount

# New discount? Just create a new class!
class BuyOneGetOneFree(Discount):
    def apply(self, price):
        return price / 2


# ═══════════════════════════════════════
# L — Liskov Substitution Principle
# ═══════════════════════════════════════
# Subtypes must be substitutable for their base types

# ❌ Bad — Square violates Rectangle's behavior
class Rectangle:
    def __init__(self, w, h):
        self.width = w
        self.height = h
    def area(self):
        return self.width * self.height

class SquareBad(Rectangle):
    def __init__(self, side):
        super().__init__(side, side)
    # Setting width alone would break the square invariant!

# ✅ Good — separate abstractions
class Shape(ABC):
    @abstractmethod
    def area(self) -> float: pass

class RectangleGood(Shape):
    def __init__(self, w, h):
        self.width = w
        self.height = h
    def area(self):
        return self.width * self.height

class SquareGood(Shape):
    def __init__(self, side):
        self.side = side
    def area(self):
        return self.side ** 2


# ═══════════════════════════════════════
# I — Interface Segregation Principle
# ═══════════════════════════════════════
# Don't force classes to implement methods they don't use

# ❌ Bad — forces all workers to implement all methods
class WorkerBad(ABC):
    @abstractmethod
    def work(self): pass
    @abstractmethod
    def eat(self): pass     # Robots don't eat!

# ✅ Good — separate interfaces
class Workable(ABC):
    @abstractmethod
    def work(self): pass

class Feedable(ABC):
    @abstractmethod
    def eat(self): pass

class HumanWorker(Workable, Feedable):
    def work(self): print("Working")
    def eat(self): print("Eating")

class RobotWorker(Workable):
    def work(self): print("Computing")
    # No eat() needed!


# ═══════════════════════════════════════
# D — Dependency Inversion Principle
# ═══════════════════════════════════════
# Depend on abstractions, not concrete implementations

# ❌ Bad — directly depends on concrete class
class NotificationServiceBad:
    def __init__(self):
        self.sender = SMTPEmailSender()     # Hard-coded dependency!
    def notify(self, msg):
        self.sender.send(msg)

# ✅ Good — depends on abstraction (interface)
class MessageSender(ABC):
    @abstractmethod
    def send(self, message: str) -> bool: pass

class EmailSender(MessageSender):
    def send(self, message):
        print(f"Email: {message}")
        return True

class SlackSender(MessageSender):
    def send(self, message):
        print(f"Slack: {message}")
        return True

class NotificationService:
    def __init__(self, sender: MessageSender):     # Inject dependency
        self.sender = sender
    def notify(self, msg):
        self.sender.send(msg)

# Easy to swap implementations!
service = NotificationService(EmailSender())
service = NotificationService(SlackSender())
```

---

### Q7: Explain common Python design patterns.

**Answer:**

```python
# ═══════════════════════════════════════
# 1. SINGLETON — ensure only one instance
# ═══════════════════════════════════════
class Singleton:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# Better: use module-level instance (Pythonic singleton)
# config.py
# _config = None
# def get_config():
#     global _config
#     if _config is None:
#         _config = load_config()
#     return _config

# ═══════════════════════════════════════
# 2. FACTORY — create objects without specifying class
# ═══════════════════════════════════════
class Serializer:
    @staticmethod
    def create(format_type):
        serializers = {
            "json": JsonSerializer,
            "xml": XmlSerializer,
            "yaml": YamlSerializer,
        }
        cls = serializers.get(format_type)
        if not cls:
            raise ValueError(f"Unknown format: {format_type}")
        return cls()

# ═══════════════════════════════════════
# 3. OBSERVER — event-driven notifications
# ═══════════════════════════════════════
class EventEmitter:
    def __init__(self):
        self._listeners = {}

    def on(self, event, callback):
        self._listeners.setdefault(event, []).append(callback)

    def emit(self, event, *args, **kwargs):
        for callback in self._listeners.get(event, []):
            callback(*args, **kwargs)

emitter = EventEmitter()
emitter.on("user_created", lambda user: print(f"Welcome {user}!"))
emitter.on("user_created", lambda user: print(f"Sending email to {user}"))
emitter.emit("user_created", "Alice")

# ═══════════════════════════════════════
# 4. STRATEGY — interchangeable algorithms
# ═══════════════════════════════════════
class Compressor:
    def __init__(self, strategy):
        self._strategy = strategy

    def compress(self, data):
        return self._strategy(data)

# Strategies as functions (Pythonic — no need for classes)
def gzip_compress(data): return f"gzip({data})"
def lz4_compress(data): return f"lz4({data})"

c = Compressor(gzip_compress)
print(c.compress("hello"))      # "gzip(hello)"

c = Compressor(lz4_compress)
print(c.compress("hello"))      # "lz4(hello)"

# ═══════════════════════════════════════
# 5. DECORATOR PATTERN — add behavior dynamically
# ═══════════════════════════════════════
# (Python's decorator syntax IS the decorator pattern — see File 03 Q1)
```

---
