# 03 — Advanced Python Concepts
## Complete Interview Questions with Examples

---

## 3.1 Decorators

### Q1: Explain decorators from basic to advanced with real-world examples.

**Answer:**

```python
import functools
import time

# ═══════════════════════════════════════
# BASIC DECORATOR — function that wraps another function
# ═══════════════════════════════════════
def timer(func):
    """Measures execution time of a function."""
    @functools.wraps(func)    # Preserves original function's metadata
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(1)
    return "done"

# @timer is syntactic sugar for: slow_function = timer(slow_function)
slow_function()  # "slow_function took 1.0012s"

# ═══════════════════════════════════════
# DECORATOR WITH ARGUMENTS
# ═══════════════════════════════════════
def retry(max_attempts=3, exceptions=(Exception,)):
    """Retry decorator with configurable attempts and exception types."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    print(f"Attempt {attempt}/{max_attempts} failed: {e}")
            raise last_exception
        return wrapper
    return decorator

@retry(max_attempts=3, exceptions=(ConnectionError, TimeoutError))
def fetch_url(url):
    import random
    if random.random() < 0.7:
        raise ConnectionError("Network error")
    return f"Content from {url}"

# ═══════════════════════════════════════
# STACKING DECORATORS
# ═══════════════════════════════════════
def log_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

def validate_positive(func):
    @functools.wraps(func)
    def wrapper(x):
        if x < 0:
            raise ValueError("Must be positive")
        return func(x)
    return wrapper

@log_call           # Applied second (outer)
@validate_positive  # Applied first (inner)
@timer              # Applied first (innermost)
def compute(x):
    return x ** 2

# Equivalent to: compute = log_call(validate_positive(timer(compute)))

# ═══════════════════════════════════════
# CLASS-BASED DECORATOR
# ═══════════════════════════════════════
class memoize:
    """Cache function results (class-based decorator)."""
    def __init__(self, func):
        self.func = func
        self.cache = {}
        functools.update_wrapper(self, func)

    def __call__(self, *args):
        if args not in self.cache:
            self.cache[args] = self.func(*args)
        return self.cache[args]

    def cache_clear(self):
        self.cache.clear()

@memoize
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(100))   # Instant! Without memoization → exponential time

# ═══════════════════════════════════════
# DECORATOR FOR METHODS (handling self)
# ═══════════════════════════════════════
def require_auth(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.is_authenticated:
            raise PermissionError("Authentication required")
        return func(self, *args, **kwargs)
    return wrapper

class API:
    def __init__(self, authenticated=False):
        self.is_authenticated = authenticated

    @require_auth
    def get_data(self):
        return {"secret": "data"}

# ═══════════════════════════════════════
# REAL-WORLD: Rate limiting decorator
# ═══════════════════════════════════════
def rate_limit(calls_per_second=1):
    min_interval = 1.0 / calls_per_second
    def decorator(func):
        last_called = [0.0]
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            last_called[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(calls_per_second=2)
def call_api(endpoint):
    return f"Response from {endpoint}"
```

---

## 3.2 Context Managers

### Q2: Explain context managers — `__enter__`/`__exit__` and `contextlib`.

**Answer:**

```python
# ═══════════════════════════════════════
# Class-based context manager
# ═══════════════════════════════════════
class DatabaseConnection:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.connection = None

    def __enter__(self):
        """Called when entering 'with' block. Returns the resource."""
        print(f"Connecting to {self.connection_string}")
        self.connection = self._connect()
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Called when exiting 'with' block (always, even on exception).
        Args:
            exc_type: Exception class (or None)
            exc_val:  Exception instance (or None)
            exc_tb:   Traceback (or None)
        Returns:
            True  → suppress the exception
            False → re-raise the exception (default)
        """
        print("Closing connection")
        if self.connection:
            self.connection.close()
        if exc_type is not None:
            print(f"Exception occurred: {exc_val}")
        return False    # Don't suppress exceptions

    def _connect(self):
        return type('Connection', (), {'close': lambda s: None, 'query': lambda s, q: f"Result: {q}"})()

with DatabaseConnection("postgresql://localhost/mydb") as conn:
    result = conn.query("SELECT * FROM users")
    print(result)
# Connection automatically closed, even if exception occurs

# ═══════════════════════════════════════
# contextlib — simpler context managers
# ═══════════════════════════════════════
from contextlib import contextmanager

@contextmanager
def timer_context(label="Operation"):
    """Context manager using generator."""
    start = time.perf_counter()
    try:
        yield start          # Code in 'with' block runs here
    finally:
        elapsed = time.perf_counter() - start
        print(f"{label} took {elapsed:.4f}s")

with timer_context("Data processing"):
    time.sleep(0.5)
# "Data processing took 0.5001s"

# ═══════════════════════════════════════
# Temporary state changes
# ═══════════════════════════════════════
@contextmanager
def temporary_directory():
    import tempfile, shutil
    tmpdir = tempfile.mkdtemp()
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir)

with temporary_directory() as tmpdir:
    # Work with temporary files
    with open(f"{tmpdir}/data.txt", "w") as f:
        f.write("temporary data")
# Directory automatically cleaned up

# ═══════════════════════════════════════
# Suppress specific exceptions
# ═══════════════════════════════════════
from contextlib import suppress

with suppress(FileNotFoundError):
    os.remove("nonexistent_file.txt")
# No exception raised!

# ═══════════════════════════════════════
# Reentrant/reusable context managers
# ═══════════════════════════════════════
from contextlib import ExitStack

def process_files(filenames):
    """Open multiple files safely."""
    with ExitStack() as stack:
        files = [stack.enter_context(open(fn)) for fn in filenames]
        # All files are open; all will be closed on exit
        for f in files:
            print(f.read())

# Async context manager (Python 3.7+)
class AsyncDB:
    async def __aenter__(self):
        self.conn = await connect_async()
        return self.conn

    async def __aexit__(self, *exc):
        await self.conn.close()

# async with AsyncDB() as conn:
#     await conn.query("SELECT 1")
```

---

## 3.3 Iterators & Itertools

### Q3: Explain the iterator protocol and `itertools` module.

**Answer:**

```python
# ═══════════════════════════════════════
# Iterator Protocol: __iter__ and __next__
# ═══════════════════════════════════════
class Countdown:
    def __init__(self, start):
        self.start = start

    def __iter__(self):
        """Return iterator object (self)."""
        self.current = self.start
        return self

    def __next__(self):
        """Return next value or raise StopIteration."""
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value

for num in Countdown(5):
    print(num, end=" ")  # 5 4 3 2 1

# Iterable vs Iterator:
# Iterable: has __iter__() → can be looped over (list, str, dict)
# Iterator: has __iter__() AND __next__() → produces values one at a time

lst = [1, 2, 3]           # Iterable
it = iter(lst)              # Iterator (created from iterable)
print(next(it))             # 1
print(next(it))             # 2

# ═══════════════════════════════════════
# itertools — Essential tools for iteration
# ═══════════════════════════════════════
import itertools

# --- Infinite iterators ---
counter = itertools.count(10, 2)        # 10, 12, 14, 16, ...
cycler = itertools.cycle(['R','G','B']) # R, G, B, R, G, B, ...
repeater = itertools.repeat('X', 3)     # X, X, X

# --- Combinatoric ---
# Permutations (order matters)
list(itertools.permutations([1,2,3], 2))
# [(1,2), (1,3), (2,1), (2,3), (3,1), (3,2)]

# Combinations (order doesn't matter)
list(itertools.combinations([1,2,3], 2))
# [(1,2), (1,3), (2,3)]

# Combinations with replacement
list(itertools.combinations_with_replacement([1,2,3], 2))
# [(1,1), (1,2), (1,3), (2,2), (2,3), (3,3)]

# Product (Cartesian product)
list(itertools.product('AB', [1,2]))
# [('A',1), ('A',2), ('B',1), ('B',2)]

# --- Filtering & Slicing ---
# takewhile / dropwhile
data = [1, 3, 5, 8, 2, 1]
list(itertools.takewhile(lambda x: x < 6, data))   # [1, 3, 5]
list(itertools.dropwhile(lambda x: x < 6, data))   # [8, 2, 1]

# islice — slice iterators (can't use regular slicing)
list(itertools.islice(range(100), 5, 15, 2))  # [5, 7, 9, 11, 13]

# compress — filter with selector
data = ['a','b','c','d']
selectors = [True, False, True, False]
list(itertools.compress(data, selectors))  # ['a', 'c']

# --- Grouping ---
# groupby (data must be sorted by key!)
data = [("A", 1), ("A", 2), ("B", 3), ("B", 4), ("A", 5)]
data.sort(key=lambda x: x[0])  # Must sort first!
for key, group in itertools.groupby(data, key=lambda x: x[0]):
    print(f"{key}: {list(group)}")
# A: [('A', 1), ('A', 2), ('A', 5)]
# B: [('B', 3), ('B', 4)]

# --- Chaining ---
a = [1, 2, 3]
b = [4, 5, 6]
list(itertools.chain(a, b))            # [1, 2, 3, 4, 5, 6]
list(itertools.chain.from_iterable([a, b]))  # Same, but from nested iterable

# --- Accumulate ---
list(itertools.accumulate([1,2,3,4]))            # [1, 3, 6, 10] (running sum)
list(itertools.accumulate([1,2,3,4], lambda a,b: a*b))  # [1, 2, 6, 24] (running product)

# Real-world: Batch processing
def batched(iterable, n):
    """Yield successive n-sized chunks."""
    it = iter(iterable)
    while batch := list(itertools.islice(it, n)):
        yield batch

data = range(25)
for batch in batched(data, 10):
    print(f"Processing batch of {len(batch)} items")
```

---

## 3.4 Functools Module

### Q4: Master `functools` — the functional programming toolkit.

**Answer:**

```python
import functools

# lru_cache — automatic memoization with LRU eviction
@functools.lru_cache(maxsize=128)
def expensive_computation(n):
    """Results cached; old entries evicted when cache is full."""
    print(f"Computing {n}...")
    return sum(i**2 for i in range(n))

expensive_computation(1000)    # Computing 1000... (computed)
expensive_computation(1000)    # (instant — cached!)
print(expensive_computation.cache_info())
# CacheInfo(hits=1, misses=1, maxsize=128, currsize=1)

# cache (Python 3.9+) — unbounded cache (simpler than lru_cache(maxsize=None))
@functools.cache
def factorial(n):
    return 1 if n <= 1 else n * factorial(n-1)

# partial — fix some arguments of a function
def power(base, exponent):
    return base ** exponent

square = functools.partial(power, exponent=2)
cube = functools.partial(power, exponent=3)
print(square(5))    # 25
print(cube(3))      # 27

# Real-world: configuring API calls
import json
compact_json = functools.partial(json.dumps, separators=(',', ':'), sort_keys=True)
pretty_json = functools.partial(json.dumps, indent=2, sort_keys=True)

data = {"b": 2, "a": 1}
print(compact_json(data))  # {"a":1,"b":2}
print(pretty_json(data))   # Pretty-printed

# reduce — fold/accumulate
from functools import reduce

# Sum of squares
result = reduce(lambda acc, x: acc + x**2, [1, 2, 3, 4], 0)
print(result)  # 30 (0 + 1 + 4 + 9 + 16)

# Flatten nested list
nested = [[1, 2], [3, 4], [5, 6]]
flat = reduce(lambda a, b: a + b, nested)
print(flat)  # [1, 2, 3, 4, 5, 6]

# singledispatch — function overloading by type
@functools.singledispatch
def format_value(value):
    return str(value)

@format_value.register(int)
def _(value):
    return f"{value:,}"

@format_value.register(float)
def _(value):
    return f"{value:.2f}"

@format_value.register(list)
def _(value):
    return f"[{', '.join(str(v) for v in value)}]"

print(format_value(1000000))     # "1,000,000"
print(format_value(3.14159))     # "3.14"
print(format_value([1, 2, 3]))   # "[1, 2, 3]"
print(format_value("hello"))     # "hello" (default)

# total_ordering — auto-generate comparison methods
@functools.total_ordering
class Student:
    def __init__(self, name, gpa):
        self.name = name
        self.gpa = gpa

    def __eq__(self, other):
        return self.gpa == other.gpa

    def __lt__(self, other):
        return self.gpa < other.gpa
    # total_ordering auto-generates: __le__, __gt__, __ge__

s1 = Student("Alice", 3.9)
s2 = Student("Bob", 3.7)
print(s1 > s2)   # True
print(s1 >= s2)   # True (auto-generated)

# wraps — preserve function metadata in decorators (ALWAYS USE THIS)
def my_decorator(func):
    @functools.wraps(func)    # Without this, func.__name__ becomes 'wrapper'
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
```

---

## 3.5 Python's Global Interpreter Lock (GIL)

### Q5: Explain the GIL. Why does it exist? How to work around it?

**Answer:**

```python
"""
What is the GIL?
- A mutex (lock) that protects access to Python objects
- Only ONE thread can execute Python bytecode at a time
- Exists in CPython (reference implementation)
- Does NOT exist in: Jython, IronPython, PyPy (partially)

Why does it exist?
- Simplifies memory management (reference counting is not thread-safe)
- Makes C extensions simpler and safer
- Historically, single-core CPUs made this acceptable

Impact:
- CPU-bound tasks: NO parallelism with threads (use multiprocessing)
- I/O-bound tasks: GIL is released during I/O → threads work fine
"""

import threading
import multiprocessing
import time

# ═══════════════════════════════════════
# Problem demonstration: CPU-bound with threads
# ═══════════════════════════════════════
def cpu_bound(n):
    return sum(i * i for i in range(n))

# Sequential
start = time.perf_counter()
cpu_bound(10_000_000)
cpu_bound(10_000_000)
print(f"Sequential: {time.perf_counter() - start:.2f}s")

# Threaded — NOT faster due to GIL!
start = time.perf_counter()
t1 = threading.Thread(target=cpu_bound, args=(10_000_000,))
t2 = threading.Thread(target=cpu_bound, args=(10_000_000,))
t1.start(); t2.start()
t1.join(); t2.join()
print(f"Threaded: {time.perf_counter() - start:.2f}s")  # Same or slower!

# Multiprocessing — TRUE parallelism!
start = time.perf_counter()
p1 = multiprocessing.Process(target=cpu_bound, args=(10_000_000,))
p2 = multiprocessing.Process(target=cpu_bound, args=(10_000_000,))
p1.start(); p2.start()
p1.join(); p2.join()
print(f"Multiprocessing: {time.perf_counter() - start:.2f}s")  # ~2x faster!

# ═══════════════════════════════════════
# I/O-bound: Threads work great (GIL released during I/O)
# ═══════════════════════════════════════
import urllib.request

def fetch_url(url):
    with urllib.request.urlopen(url) as response:
        return len(response.read())

urls = ["https://example.com"] * 10

# Threaded I/O — much faster than sequential
start = time.perf_counter()
threads = [threading.Thread(target=fetch_url, args=(url,)) for url in urls]
for t in threads: t.start()
for t in threads: t.join()
print(f"Threaded I/O: {time.perf_counter() - start:.2f}s")

# ═══════════════════════════════════════
# Workarounds for CPU-bound parallelism
# ═══════════════════════════════════════
# 1. multiprocessing (separate processes, separate GILs)
# 2. C extensions (NumPy releases GIL during array operations)
# 3. ctypes/Cython (release GIL explicitly)
# 4. concurrent.futures (high-level API)
# 5. subinterpreters (Python 3.12+)
# 6. free-threaded Python (Python 3.13+ experimental, PEP 703)

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

# CPU-bound → ProcessPoolExecutor
with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(cpu_bound, 10_000_000) for _ in range(4)]
    results = [f.result() for f in futures]

# I/O-bound → ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(fetch_url, url) for url in urls]
    results = [f.result() for f in futures]
```

**Key interview talking points:**
- GIL makes Python threads unsuitable for CPU parallelism
- Use `multiprocessing` or `ProcessPoolExecutor` for CPU-bound work
- Threads are perfectly fine for I/O-bound work (networking, file I/O)
- Python 3.13 introduced experimental free-threaded mode (no GIL)

---

## 3.6 Python Memory Model

### Q6: How does Python manage memory internally?

**Answer:**

```python
import sys

# ═══════════════════════════════════════
# Everything is an object on the heap
# ═══════════════════════════════════════
x = 42
print(sys.getsizeof(x))       # 28 bytes (int object overhead)
print(sys.getsizeof("hello")) # 54 bytes
print(sys.getsizeof([]))      # 56 bytes (empty list)
print(sys.getsizeof({}))      # 64 bytes (empty dict)

# ═══════════════════════════════════════
# Memory optimization techniques
# ═══════════════════════════════════════

# 1. __slots__ (covered in OOP section)
# 2. Generators instead of lists
# 3. array module for homogeneous numeric data
import array
py_list = [1.0] * 1_000_000
arr = array.array('d', [1.0] * 1_000_000)
print(sys.getsizeof(py_list))   # ~8 MB (each float is a Python object)
print(sys.getsizeof(arr))       # ~8 MB (raw doubles, but no object overhead per element)

# 4. numpy for numerical computing (much more efficient)
import numpy as np
np_arr = np.ones(1_000_000)     # ~8 MB contiguous memory

# 5. Memory profiling
# pip install memory-profiler
# @profile
# def my_function():
#     big_list = [0] * 1_000_000
#     return sum(big_list)
# Run: python -m memory_profiler script.py

# 6. tracemalloc — built-in memory tracking
import tracemalloc

tracemalloc.start()
big_data = [x**2 for x in range(100_000)]
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:3]:
    print(stat)
tracemalloc.stop()

# 7. String interning for memory savings
import sys
# Intern frequently used strings
keys = [sys.intern(f"field_{i}") for i in range(1000)]

# 8. weakref for caches (covered in garbage collection section)
```

---

## 3.7 Type Hints & Typing Module

### Q7: Master Python's type hint system.

**Answer:**

```python
from typing import (
    List, Dict, Tuple, Set, Optional, Union,
    Any, Callable, Iterator, Generator,
    TypeVar, Generic, Protocol,
    Literal, TypedDict, Final, Annotated
)

# ═══════════════════════════════════════
# Basic type hints
# ═══════════════════════════════════════
def greet(name: str) -> str:
    return f"Hello, {name}!"

def process_items(items: list[int]) -> dict[str, int]:  # Python 3.9+ lowercase
    return {"sum": sum(items), "count": len(items)}

# Optional — value can be None
def find_user(user_id: int) -> Optional[dict]:  # Same as dict | None (3.10+)
    return None

# Union — multiple types (Python 3.10+: use |)
def normalize(value: Union[str, int, float]) -> str:  # str | int | float
    return str(value)

# ═══════════════════════════════════════
# Callable — function signatures
# ═══════════════════════════════════════
def apply_func(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

# Takes two ints, returns int
apply_func(lambda x, y: x + y, 3, 4)  # 7

# ═══════════════════════════════════════
# TypeVar & Generic — create generic classes/functions
# ═══════════════════════════════════════
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

def first(items: list[T]) -> T:
    """Generic function — works with any type."""
    return items[0]

first([1, 2, 3])          # Returns int
first(["a", "b", "c"])    # Returns str

class Stack(Generic[T]):
    """Generic stack — type-safe."""
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

int_stack: Stack[int] = Stack()
int_stack.push(42)

# ═══════════════════════════════════════
# TypedDict — typed dictionaries
# ═══════════════════════════════════════
class UserDict(TypedDict):
    name: str
    age: int
    email: str
    active: bool

def create_user(data: UserDict) -> None:
    print(data["name"])

# Literal — restrict to specific values
def set_mode(mode: Literal["train", "eval", "predict"]) -> None:
    pass

# Final — constant
MAX_RETRIES: Final = 3

# Annotated — add metadata
from typing import Annotated
PositiveInt = Annotated[int, "Must be positive"]
def process(count: PositiveInt) -> None:
    pass

# ═══════════════════════════════════════
# Generator & Iterator types
# ═══════════════════════════════════════
def count_up(limit: int) -> Generator[int, None, None]:
    """Generator[YieldType, SendType, ReturnType]"""
    for i in range(limit):
        yield i

def read_lines(path: str) -> Iterator[str]:
    with open(path) as f:
        yield from f

# ═══════════════════════════════════════
# Runtime type checking with Protocol
# ═══════════════════════════════════════
from typing import Protocol, runtime_checkable

@runtime_checkable
class Saveable(Protocol):
    def save(self) -> bool: ...
    def load(self) -> dict: ...

class FileStore:
    def save(self) -> bool:
        return True
    def load(self) -> dict:
        return {}

print(isinstance(FileStore(), Saveable))  # True — structural typing!

# ═══════════════════════════════════════
# Python 3.12: New type syntax
# ═══════════════════════════════════════
# type Point = tuple[int, int]                    # Type alias (3.12+)
# def first[T](items: list[T]) -> T: ...          # Inline TypeVar (3.12+)
# class Stack[T]: ...                             # Generic class (3.12+)
```

---

## 3.8 Python Packaging & Modules

### Q8: Explain Python's import system and packaging.

**Answer:**

```python
# ═══════════════════════════════════════
# Import system
# ═══════════════════════════════════════

# 1. Module search order
import sys
print(sys.path)
# [
#   ''                       (current directory),
#   '/usr/lib/python3.x',   (standard library),
#   '/usr/lib/python3.x/site-packages'  (third-party)
# ]

# 2. Import styles
import os                              # Import entire module
from os import path                     # Import specific name
from os.path import join, exists       # Import multiple names
import numpy as np                      # Alias
from typing import *                    # Import all (avoid in production!)

# 3. Relative imports (within packages)
# mypackage/
#   __init__.py
#   module_a.py
#   subpackage/
#     __init__.py
#     module_b.py
#
# In module_b.py:
# from . import module_a           # From current package
# from .. import module_a          # From parent package
# from .module_a import func       # Specific import

# 4. __init__.py purposes
# - Makes a directory a package
# - Runs when package is imported
# - Controls what's exported with __all__

# mypackage/__init__.py
# __all__ = ['ClassA', 'function_b']   # Controls: from mypackage import *
# from .module_a import ClassA
# from .module_b import function_b

# 5. Lazy imports (for faster startup)
def get_numpy():
    import numpy as np    # Only imported when function is called
    return np

# 6. importlib — dynamic imports
import importlib
module = importlib.import_module('json')
data = module.loads('{"key": "value"}')

# ═══════════════════════════════════════
# Package structure (modern)
# ═══════════════════════════════════════
"""
myproject/
├── pyproject.toml          # Modern config (replaces setup.py)
├── src/
│   └── mypackage/
│       ├── __init__.py
│       ├── core.py
│       ├── utils.py
│       └── models/
│           ├── __init__.py
│           └── user.py
├── tests/
│   ├── __init__.py
│   ├── test_core.py
│   └── test_utils.py
├── README.md
└── LICENSE

# pyproject.toml (PEP 621)
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "mypackage"
version = "1.0.0"
requires-python = ">=3.9"
dependencies = [
    "requests>=2.28",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = ["pytest", "mypy", "ruff"]
"""
```

---

## 3.9 Concurrency Patterns

### Q9: Explain `concurrent.futures` and practical concurrency patterns.

**Answer:**

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import time

# ═══════════════════════════════════════
# ThreadPoolExecutor — for I/O-bound tasks
# ═══════════════════════════════════════
def download_page(url):
    time.sleep(0.5)  # Simulate network I/O
    return f"Content from {url}"

urls = [f"https://example.com/page/{i}" for i in range(10)]

# Method 1: map (ordered results)
with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(download_page, urls))
    # Results in same order as input

# Method 2: submit + as_completed (results as they finish)
with ThreadPoolExecutor(max_workers=5) as executor:
    future_to_url = {executor.submit(download_page, url): url for url in urls}

    for future in as_completed(future_to_url):
        url = future_to_url[future]
        try:
            data = future.result(timeout=10)
            print(f"{url}: {data}")
        except Exception as e:
            print(f"{url}: error — {e}")

# ═══════════════════════════════════════
# ProcessPoolExecutor — for CPU-bound tasks
# ═══════════════════════════════════════
def compute_heavy(n):
    return sum(i * i for i in range(n))

with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(compute_heavy, 10_000_000) for _ in range(8)]
    results = [f.result() for f in futures]

# ═══════════════════════════════════════
# Pattern: Fan-out/Fan-in with timeout
# ═══════════════════════════════════════
def fetch_with_fallback(primary_url, fallback_url, timeout=5):
    with ThreadPoolExecutor(max_workers=2) as executor:
        primary = executor.submit(download_page, primary_url)
        try:
            return primary.result(timeout=timeout)
        except TimeoutError:
            fallback = executor.submit(download_page, fallback_url)
            return fallback.result(timeout=timeout)
```

---
