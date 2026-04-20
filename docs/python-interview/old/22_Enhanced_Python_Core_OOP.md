# 22 — Enhanced Python Questions: Core + OOP + Advanced
## Most Important Missing Questions for Files 01, 02, 03

---

## 22.1 ADDITIONS TO FILE 01 (Python Core)

### Q1: Difference between `deepcopy`, `copy`, and assignment — MOST ASKED

```python
import copy

# Assignment: SAME object (reference)
a = [[1, 2], [3, 4]]
b = a
b[0][0] = 99
print(a)   # [[99, 2], [3, 4]] ← a changed! Same object

# Shallow copy: NEW outer object, SAME inner objects
a = [[1, 2], [3, 4]]
b = copy.copy(a)      # or a.copy() or a[:] or list(a)
b.append([5, 6])
print(a)   # [[1, 2], [3, 4]] ← outer not affected
b[0][0] = 99
print(a)   # [[99, 2], [3, 4]] ← inner IS affected (shared reference)

# Deep copy: COMPLETELY independent
a = [[1, 2], [3, 4]]
b = copy.deepcopy(a)
b[0][0] = 99
print(a)   # [[1, 2], [3, 4]] ← NOT affected
```

### Q2: What is `*args` and `**kwargs`? Real-world usage?

```python
# *args collects extra positional arguments as TUPLE
# **kwargs collects extra keyword arguments as DICT

def log_call(func_name, *args, **kwargs):
    print(f"Calling {func_name}")
    print(f"  Positional args: {args}")     # tuple
    print(f"  Keyword args: {kwargs}")       # dict

log_call("save", 1, 2, 3, format="json", compress=True)
# Calling save
# Positional args: (1, 2, 3)
# Keyword args: {'format': 'json', 'compress': True}

# Unpacking — the REVERSE operation
def add(a, b, c):
    return a + b + c

nums = [1, 2, 3]
print(add(*nums))      # Unpack list → positional args → 6

config = {"a": 10, "b": 20, "c": 30}
print(add(**config))    # Unpack dict → keyword args → 60

# Real-world: Decorator that preserves all arguments
from functools import wraps
def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)    # Forward all args
        print(f"{func.__name__}: {time.time()-start:.4f}s")
        return result
    return wrapper
```

### Q3: What is the difference between `list`, `tuple`, `set`, and `dict`?

```python
"""
┌──────────┬──────────┬───────────┬───────────┬───────────────┐
│          │ list     │ tuple     │ set       │ dict          │
├──────────┼──────────┼───────────┼───────────┼───────────────┤
│ Ordered  │ Yes      │ Yes       │ No        │ Yes (3.7+)    │
│ Mutable  │ Yes      │ No        │ Yes       │ Yes           │
│ Duplicates│ Yes     │ Yes       │ No        │ Keys: No      │
│ Indexed  │ Yes      │ Yes       │ No        │ By key        │
│ Hashable │ No       │ Yes*      │ No        │ No            │
│ Syntax   │ [1,2,3]  │ (1,2,3)   │ {1,2,3}   │ {'a':1}       │
│ Use when │ Ordered  │ Immutable │ Unique    │ Key-value     │
│          │ collection│ record   │ membership│ lookup        │
│ Lookup   │ O(n)     │ O(n)      │ O(1)      │ O(1)          │
└──────────┴──────────┴───────────┴───────────┴───────────────┘
*tuple is hashable only if all elements are hashable
"""
```

### Q4: Explain Python's `with` statement and why it's important.

```python
# with statement calls __enter__ and __exit__ automatically
# Guarantees cleanup even if exception occurs

# ❌ Without with — cleanup might not happen
f = open("file.txt")
try:
    data = f.read()
finally:
    f.close()

# ✅ With statement — always cleans up
with open("file.txt") as f:
    data = f.read()
# f.close() called automatically, even on exception!

# Multiple context managers
with open("input.txt") as inp, open("output.txt", "w") as out:
    out.write(inp.read())

# Custom context manager
class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self.start
        print(f"Elapsed: {self.elapsed:.4f}s")
        return False   # Don't suppress exceptions

with Timer() as t:
    time.sleep(1)
# Prints: Elapsed: 1.0001s
```

### Q5: Explain `map()`, `filter()`, `reduce()`, and when to use list comprehension instead.

```python
from functools import reduce

numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# map: apply function to each element
squares = list(map(lambda x: x**2, numbers))
# [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]

# filter: keep elements where function returns True
evens = list(filter(lambda x: x % 2 == 0, numbers))
# [2, 4, 6, 8, 10]

# reduce: accumulate values
total = reduce(lambda a, b: a + b, numbers)    # 55
product = reduce(lambda a, b: a * b, numbers)  # 3628800

# ✅ Pythonic: use list comprehension instead of map/filter
squares = [x**2 for x in numbers]                    # Cleaner than map
evens = [x for x in numbers if x % 2 == 0]           # Cleaner than filter

# When to use map/filter vs comprehension:
# Comprehension: Most cases — more readable, Pythonic
# map: When applying an existing named function → map(str, numbers)
# filter: Rarely — comprehension is almost always better
# reduce: For accumulation that can't be done with sum/min/max
```

### Q6: What are `lambda` functions? When to use and NOT use?

```python
# Lambda: anonymous single-expression function
square = lambda x: x ** 2
add = lambda x, y: x + y

# ✅ Good use: short functions in sort/map/filter
students = [("Alice", 90), ("Bob", 75), ("Charlie", 85)]
sorted(students, key=lambda s: s[1])

# ✅ Good use: simple callbacks
button.on_click(lambda: print("Clicked!"))

# ❌ Bad use: Complex logic — use def instead
# ❌ Bad: assigning lambda to variable (defeats the purpose)
f = lambda x, y: x if x > y else y     # ❌ Just use def max_val(x, y)

# Lambda limitations:
# - Single expression only (no statements, no assignments)
# - No docstrings
# - Hard to debug (shows as <lambda> in tracebacks)
```

### Q7: What happens when you do `a = 256` vs `a = 257`? Explain Python object caching.

```python
# Python pre-caches integers from -5 to 256
a = 256
b = 256
print(a is b)     # True — same object (cached)

a = 257
b = 257
print(a is b)     # False — different objects (not cached)
# Note: In REPL, compiler may optimize this. In scripts, it's False.

# String interning: identifier-like strings are cached
a = "hello"
b = "hello"
print(a is b)     # True

a = "hello world"
b = "hello world"
print(a is b)     # May be False (space = not identifier-like)

# IMPORTANT: Always use == for value comparison, not 'is'
# Only use 'is' for: None, True, False, sentinel objects
```

### Q8: Explain Python's `collections` module — most important classes.

```python
from collections import (
    Counter, defaultdict, OrderedDict, deque, namedtuple, ChainMap
)

# Counter — count occurrences
words = ["apple", "banana", "apple", "cherry", "banana", "apple"]
count = Counter(words)
print(count)                    # Counter({'apple': 3, 'banana': 2, 'cherry': 1})
print(count.most_common(2))     # [('apple', 3), ('banana', 2)]
count.update(["apple"])         # Add more counts
print(count["apple"])           # 4

# defaultdict — auto-creates missing keys
graph = defaultdict(list)
graph["A"].append("B")          # No KeyError — creates empty list automatically
graph["A"].append("C")

word_groups = defaultdict(set)
for word in words:
    word_groups[len(word)].add(word)

# deque — O(1) append/pop from both ends
dq = deque([1, 2, 3])
dq.appendleft(0)     # O(1)
dq.append(4)          # O(1)
dq.popleft()           # O(1)
dq.rotate(1)           # Rotate right by 1

# namedtuple — lightweight immutable class
Point = namedtuple('Point', ['x', 'y'])
p = Point(3, 4)
print(p.x, p.y)       # 3 4 — access by name
print(p[0], p[1])      # 3 4 — access by index

# OrderedDict — remembers insertion order (less needed in 3.7+ dicts)
# ChainMap — combine multiple dicts into one view
defaults = {"color": "red", "size": "medium"}
user_prefs = {"color": "blue"}
config = ChainMap(user_prefs, defaults)
print(config["color"])    # "blue" — user_prefs checked first
print(config["size"])     # "medium" — falls back to defaults
```

---

## 22.2 ADDITIONS TO FILE 02 (OOP)

### Q9: What is the difference between `@staticmethod` and `@classmethod`?

```python
class DateUtil:
    date_format = "%Y-%m-%d"
    
    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day
    
    @classmethod
    def from_string(cls, date_string):
        """Alternative constructor — gets cls (the class itself)."""
        year, month, day = map(int, date_string.split("-"))
        return cls(year, month, day)     # cls = DateUtil (or subclass!)
    
    @staticmethod
    def is_valid_date(date_string):
        """Utility — doesn't need class or instance."""
        try:
            year, month, day = map(int, date_string.split("-"))
            return 1 <= month <= 12 and 1 <= day <= 31
        except ValueError:
            return False

# classmethod creates instances correctly for subclasses
class ISODate(DateUtil):
    pass

d = ISODate.from_string("2024-03-15")
print(type(d))    # <class 'ISODate'> — not DateUtil! cls works correctly

# staticmethod is just a regular function namespaced to the class
DateUtil.is_valid_date("2024-13-01")    # False
```

### Q10: What is multiple inheritance? What are Mixins?

```python
# Multiple inheritance: class inherits from multiple parents
class Printable:
    def print_info(self):
        print(f"{self.__class__.__name__}: {vars(self)}")

class Serializable:
    def to_json(self):
        import json
        return json.dumps(vars(self))

class Validatable:
    def validate(self):
        for key, value in vars(self).items():
            if value is None:
                raise ValueError(f"{key} cannot be None")
        return True

# Mixin pattern: combine capabilities
class User(Printable, Serializable, Validatable):
    def __init__(self, name, email):
        self.name = name
        self.email = email

user = User("Alice", "alice@example.com")
user.print_info()    # User: {'name': 'Alice', 'email': 'alice@example.com'}
print(user.to_json()) # {"name": "Alice", "email": "alice@example.com"}
user.validate()       # True

# Mixin rules:
# 1. Mixins should be small, focused on ONE capability
# 2. Mixins should NOT have __init__ (or call super().__init__)
# 3. Name them with "Mixin" suffix for clarity
# 4. Use for horizontal code reuse (not "is-a" relationship)
```

### Q11: Explain `__repr__` vs `__str__`.

```python
class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price
    
    def __repr__(self):
        """For DEVELOPERS — unambiguous, ideally valid Python to recreate object."""
        return f"Product(name={self.name!r}, price={self.price})"
    
    def __str__(self):
        """For USERS — readable, pretty."""
        return f"{self.name}: ${self.price:.2f}"

p = Product("Widget", 29.99)

print(repr(p))     # Product(name='Widget', price=29.99)  ← developer
print(str(p))      # Widget: $29.99                        ← user
print(p)           # Widget: $29.99 (print calls __str__)

# In containers, __repr__ is used:
print([p])         # [Product(name='Widget', price=29.99)]

# f-string:
print(f"{p}")      # Widget: $29.99 (uses __str__)
print(f"{p!r}")    # Product(name='Widget', price=29.99) (uses __repr__)

# Rule: Always implement __repr__. Implement __str__ only if you need different output.
# If only __repr__ is defined, __str__ falls back to __repr__.
```

### Q12: What are `@property`, getter, setter in Python?

```python
class Temperature:
    def __init__(self, celsius):
        self._celsius = celsius    # Convention: _ means "private"
    
    @property
    def celsius(self):
        """Getter — accessed like an attribute."""
        return self._celsius
    
    @celsius.setter
    def celsius(self, value):
        """Setter — validates on assignment."""
        if value < -273.15:
            raise ValueError("Below absolute zero!")
        self._celsius = value
    
    @property
    def fahrenheit(self):
        """Computed property — read-only."""
        return self._celsius * 9/5 + 32

t = Temperature(25)
print(t.celsius)      # 25 — calls getter (looks like attribute access!)
print(t.fahrenheit)   # 77.0 — computed on access
t.celsius = 30        # Calls setter (validates!)
# t.celsius = -300    # ValueError!
# t.fahrenheit = 100  # AttributeError — no setter defined (read-only)

# Why use @property instead of getters/setters?
# Java style: t.get_celsius(), t.set_celsius(30) — verbose!
# Python style: t.celsius, t.celsius = 30 — clean attribute-like access with validation
```

---

## 22.3 ADDITIONS TO FILE 03 (Advanced)

### Q13: Explain Python's `__dict__` and attribute lookup chain.

```python
class MyClass:
    class_var = "I'm a class variable"
    
    def __init__(self):
        self.instance_var = "I'm an instance variable"

obj = MyClass()

# Instance __dict__ — only instance attributes
print(obj.__dict__)
# {'instance_var': "I'm an instance variable"}

# Class __dict__ — class attributes and methods
print(MyClass.__dict__.keys())
# dict_keys(['__module__', 'class_var', '__init__', '__dict__', ...])

# Attribute lookup order:
# 1. Instance __dict__
# 2. Class __dict__
# 3. Parent class __dict__ (following MRO)
# 4. __getattr__ (if defined)

print(obj.class_var)       # Found in class __dict__
print(obj.instance_var)    # Found in instance __dict__

obj.class_var = "Override"  # Creates in INSTANCE __dict__ (doesn't modify class)
print(obj.__dict__)         # {'instance_var': ..., 'class_var': 'Override'}
print(MyClass.class_var)    # Still "I'm a class variable"
```

### Q14: What is `__all__` in a module?

```python
# __all__ controls what gets exported with `from module import *`

# mymodule.py
__all__ = ['public_function', 'PublicClass']

def public_function():
    pass

def _private_function():    # Convention: underscore = private
    pass

class PublicClass:
    pass

class _InternalClass:
    pass

# In another file:
# from mymodule import *
# This imports ONLY: public_function, PublicClass
# _private_function and _InternalClass are NOT imported

# Without __all__, `import *` imports everything without leading underscore
# Best practice: Always define __all__ in your modules
```

### Q15: What is monkey patching? When is it used?

```python
# Monkey patching: modifying classes/modules at runtime

import json

# Example: Adding a method to an existing class
class User:
    def __init__(self, name):
        self.name = name

# Monkey patch: add to_json method
def to_json(self):
    return json.dumps({"name": self.name})

User.to_json = to_json    # Add method to class at runtime!

user = User("Alice")
print(user.to_json())     # {"name": "Alice"} — works!

# Real-world use: Testing (mock/patch)
# from unittest.mock import patch
# with patch('module.function', return_value=mock_data):
#     test_something()

# ⚠️ When to use:
# ✅ Testing: Mocking external dependencies
# ✅ Hotfixes: Quick production patches
# ❌ Regular code: Makes code unpredictable, hard to debug
# ❌ Libraries: Breaking change for users
```

### Q16: Explain `global` vs `nonlocal` keywords.

```python
x = 10              # Global variable

def outer():
    y = 20          # Enclosing variable
    
    def inner():
        nonlocal y  # Modify enclosing variable
        global x    # Modify global variable
        x = 100
        y = 200
    
    inner()
    print(y)        # 200 (modified by nonlocal)

outer()
print(x)            # 100 (modified by global)

# Without these keywords:
def broken():
    # x = x + 1    # UnboundLocalError! Assignment makes it local
    pass

# Rules:
# global:   Modify module-level variable from inside a function
# nonlocal: Modify enclosing function's variable from inner function
# Best practice: AVOID both. Use return values or class attributes instead.
```

### Q17: What are generators and why are they memory-efficient?

```python
import sys

# List: ALL values in memory
big_list = [x**2 for x in range(1_000_000)]
print(sys.getsizeof(big_list))   # ~8 MB

# Generator: ONE value at a time
big_gen = (x**2 for x in range(1_000_000))
print(sys.getsizeof(big_gen))    # ~200 bytes!

# Generator function with yield
def read_huge_file(filepath):
    """Process 100GB file with constant memory."""
    with open(filepath) as f:
        for line in f:
            yield line.strip()

# Pipeline of generators — each stage processes one item at a time
def pipeline(filepath):
    lines = read_huge_file(filepath)
    errors = (line for line in lines if "ERROR" in line)
    parsed = (parse_log(line) for line in errors)
    return parsed     # Nothing computed yet! Lazy evaluation.

# Computation only happens when you iterate:
for record in pipeline("server.log"):
    save(record)    # Processes one line at a time, constant memory
```

---

## 22.4 MUST-KNOW Python One-Liners (Interview Favorites)

```python
# Swap two variables
a, b = b, a

# Reverse a list/string
lst[::-1]
"hello"[::-1]      # "olleh"

# Flatten 2D list
flat = [x for row in matrix for x in row]

# Remove duplicates preserving order
list(dict.fromkeys(items))

# Transpose matrix
list(zip(*matrix))

# Check palindrome
s == s[::-1]

# Count occurrences
from collections import Counter
Counter("mississippi")    # Counter({'i': 4, 's': 4, 'p': 2, 'm': 1})

# Find most common
Counter(items).most_common(1)[0][0]

# Merge dicts (Python 3.9+)
merged = dict1 | dict2

# Conditional expression (ternary)
result = "even" if x % 2 == 0 else "odd"

# Multiple assignment
x, y, z = 1, 2, 3

# Unpack with *
first, *rest = [1, 2, 3, 4, 5]
# first = 1, rest = [2, 3, 4, 5]

*init, last = [1, 2, 3, 4, 5]
# init = [1, 2, 3, 4], last = 5

# Chain comparisons
1 < x < 10    # Same as: 1 < x and x < 10

# Default dict value
value = my_dict.get("key", "default")

# Create dict from two lists
keys = ["a", "b", "c"]
values = [1, 2, 3]
d = dict(zip(keys, values))    # {'a': 1, 'b': 2, 'c': 3}
```

---
