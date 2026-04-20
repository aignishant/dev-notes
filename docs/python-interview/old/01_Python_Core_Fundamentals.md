# 01 — Python Core Fundamentals
## Complete Interview Questions with Examples

---

## 1.1 Data Types & Variables

### Q1: What are Python's built-in data types? Explain with categories.

**Answer:**
Python has several built-in data types grouped into categories:

```
Numeric:      int, float, complex, bool
Sequence:     list, tuple, range, str
Set:          set, frozenset
Mapping:      dict
Binary:       bytes, bytearray, memoryview
None:         NoneType
```

**Example:**
```python
# Numeric
x = 42                  # int — arbitrary precision in Python
y = 3.14                # float — 64-bit double precision
z = 3 + 4j              # complex — real + imaginary
flag = True              # bool — subclass of int (True == 1)

# Sequence
names = ["Alice", "Bob"]            # list — mutable, ordered
point = (10, 20)                    # tuple — immutable, ordered
r = range(0, 10, 2)                 # range — lazy sequence
greeting = "Hello"                  # str — immutable Unicode

# Set
unique = {1, 2, 3}                  # set — mutable, unordered, unique
frozen = frozenset([1, 2, 3])       # frozenset — immutable set

# Mapping
person = {"name": "Alice", "age": 30}  # dict — key-value pairs

# Binary
raw = b"hello"                      # bytes — immutable
buf = bytearray(b"hello")           # bytearray — mutable
mv = memoryview(buf)                # memoryview — memory access without copy

# None
result = None                       # NoneType — singleton null
```

**Usage:** Understanding data types is foundational. Interviewers test whether you know mutability, memory behavior, and when to choose which type.

---

### Q2: Explain mutable vs immutable types. Why does it matter?

**Answer:**
- **Immutable:** Cannot be changed after creation → `int`, `float`, `str`, `tuple`, `frozenset`, `bytes`
- **Mutable:** Can be modified in place → `list`, `dict`, `set`, `bytearray`

**Example:**
```python
# Immutable — new object created on modification
a = "hello"
print(id(a))        # e.g., 140234567890
a = a + " world"
print(id(a))        # Different id! New object created

# Mutable — same object modified
lst = [1, 2, 3]
print(id(lst))      # e.g., 140234567999
lst.append(4)
print(id(lst))      # Same id! Object modified in place

# TRAP: Default mutable arguments
def bad_func(items=[]):       # ⚠️ Same list shared across calls!
    items.append(1)
    return items

print(bad_func())   # [1]
print(bad_func())   # [1, 1]  ← Bug!

def good_func(items=None):   # ✅ Correct pattern
    if items is None:
        items = []
    items.append(1)
    return items
```

**Why it matters:**
1. **Function arguments:** Mutable defaults are a common bug source
2. **Dictionary keys:** Only immutable (hashable) types can be dict keys
3. **Thread safety:** Immutable objects are inherently thread-safe
4. **Performance:** Immutable objects can be cached and reused (string interning, integer caching)

---

### Q3: What is string interning? What integers does Python cache?

**Answer:**
Python caches small integers and some strings to save memory and speed up comparisons.

```python
# Integer caching: Python pre-caches integers -5 to 256
a = 256
b = 256
print(a is b)       # True — same object from cache

a = 257
b = 257
print(a is b)       # False — different objects (outside cache range)
                     # Note: may be True in some REPL environments due to compiler optimizations

# String interning: Python automatically interns strings that look like identifiers
s1 = "hello"
s2 = "hello"
print(s1 is s2)     # True — interned

s3 = "hello world"
s4 = "hello world"
print(s3 is s4)     # May be False — contains space, not identifier-like

# Manual interning
import sys
s5 = sys.intern("hello world")
s6 = sys.intern("hello world")
print(s5 is s6)     # True — forced interning
```

**Usage:** Explains why `is` vs `==` matters. Use `==` for value comparison, `is` for identity (only use `is` with `None`, `True`, `False`).

---

### Q4: Explain `is` vs `==`. When to use each?

**Answer:**
- `==` checks **value equality** (calls `__eq__`)
- `is` checks **identity** (same object in memory)

```python
a = [1, 2, 3]
b = [1, 2, 3]
c = a

print(a == b)    # True  — same values
print(a is b)    # False — different objects
print(a is c)    # True  — c points to same object as a

# ALWAYS use `is` for None checks
x = None
if x is None:        # ✅ Correct — None is a singleton
    print("None!")

if x == None:        # ⚠️ Works but bad practice — custom __eq__ could break this
    print("None!")

# Real-world example: a class could override __eq__ to break == None
class Tricky:
    def __eq__(self, other):
        return True     # Claims to be equal to everything!

t = Tricky()
print(t == None)     # True  ← Wrong!
print(t is None)     # False ← Correct!
```

---

### Q5: How does Python handle variable assignment and references?

**Answer:**
Python variables are **references (labels/names)** pointing to objects, not containers holding values.

```python
# Assignment creates a reference to an object
x = [1, 2, 3]    # x → list object [1, 2, 3]
y = x             # y → same list object (NOT a copy)

y.append(4)
print(x)          # [1, 2, 3, 4] — both x and y reference the same object

# Creating actual copies
import copy

original = [[1, 2], [3, 4]]

# Shallow copy — new outer list, but inner lists are still shared
shallow = copy.copy(original)         # or original.copy() or list(original) or original[:]
shallow[0].append(99)
print(original)   # [[1, 2, 99], [3, 4]] — inner list was shared!

# Deep copy — fully independent copy at all levels
original2 = [[1, 2], [3, 4]]
deep = copy.deepcopy(original2)
deep[0].append(99)
print(original2)  # [[1, 2], [3, 4]] — completely independent
```

**Usage:** Understanding references is critical for debugging shared-state bugs, especially in function arguments and class attributes.

---

## 1.2 Operators & Expressions

### Q6: Explain Python's operator overloading via dunder methods.

**Answer:**
Python allows custom behavior for operators by defining special methods (dunder/magic methods).

```python
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):           # v1 + v2
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):           # v1 - v2
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):          # v1 * 3
        return Vector(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar):         # 3 * v1 (reversed)
        return self.__mul__(scalar)

    def __eq__(self, other):            # v1 == v2
        return self.x == other.x and self.y == other.y

    def __lt__(self, other):            # v1 < v2
        return self.magnitude() < other.magnitude()

    def __abs__(self):                  # abs(v1)
        return self.magnitude()

    def __repr__(self):                 # repr(v1) — for developers
        return f"Vector({self.x}, {self.y})"

    def __str__(self):                  # str(v1) — for users
        return f"({self.x}, {self.y})"

    def magnitude(self):
        return (self.x**2 + self.y**2) ** 0.5

# Usage
v1 = Vector(3, 4)
v2 = Vector(1, 2)
print(v1 + v2)          # (4, 6)
print(v1 * 3)           # (9, 12)
print(3 * v1)           # (9, 12) — works because of __rmul__
print(abs(v1))           # 5.0
print(v1 == Vector(3,4)) # True
```

**Key dunder methods:**
```
Arithmetic:    __add__, __sub__, __mul__, __truediv__, __floordiv__, __mod__, __pow__
Comparison:    __eq__, __ne__, __lt__, __le__, __gt__, __ge__
Unary:         __neg__, __pos__, __abs__, __invert__
Container:     __len__, __getitem__, __setitem__, __delitem__, __contains__
String:        __str__, __repr__, __format__
Callable:      __call__
Context:       __enter__, __exit__
Iteration:     __iter__, __next__
Hashing:       __hash__
```

---

### Q7: What is the walrus operator (`:=`)? When to use it?

**Answer:**
Introduced in Python 3.8 (PEP 572), the walrus operator assigns a value to a variable **as part of an expression**.

```python
# WITHOUT walrus — redundant computation
data = input("Enter data: ")
while data != "quit":
    process(data)
    data = input("Enter data: ")

# WITH walrus — cleaner
while (data := input("Enter data: ")) != "quit":
    process(data)

# Filtering with computation
numbers = [1, 4, 9, 16, 25, 36]
# Without walrus
results = []
for n in numbers:
    sqrt = n ** 0.5
    if sqrt > 3:
        results.append(sqrt)

# With walrus — concise
results = [sqrt for n in numbers if (sqrt := n ** 0.5) > 3]
print(results)  # [4.0, 5.0, 6.0]

# Regex matching
import re
text = "Phone: 123-456-7890"
if (match := re.search(r'(\d{3}-\d{3}-\d{4})', text)):
    print(f"Found phone: {match.group(1)}")

# Reading file chunks
with open("large_file.txt") as f:
    while (chunk := f.read(8192)):
        process(chunk)
```

**Usage:** Reduces code duplication when you need to both compute a value and test it. Don't overuse — readability comes first.

---

## 1.3 Control Flow

### Q8: How does Python's `for-else` and `while-else` work?

**Answer:**
The `else` clause in a loop executes **only if the loop completes without hitting `break`**.

```python
# Use case: Searching for an item
def find_prime_factor(n):
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            print(f"Found factor: {i}")
            break
    else:
        # Only runs if no break was hit → no factor found
        print(f"{n} is prime!")

find_prime_factor(17)    # 17 is prime!
find_prime_factor(15)    # Found factor: 3

# Real-world usage: Validating data
def validate_records(records):
    for record in records:
        if not record.get("email"):
            print(f"Invalid record: {record}")
            break
    else:
        print("All records valid!")
        return True
    return False

# Equivalent WITHOUT for-else (more verbose)
def validate_records_v2(records):
    found_invalid = False
    for record in records:
        if not record.get("email"):
            print(f"Invalid record: {record}")
            found_invalid = True
            break
    if not found_invalid:
        print("All records valid!")
        return True
    return False
```

---

### Q9: Explain exception handling best practices for senior developers.

**Answer:**

```python
# 1. Catch specific exceptions, never bare except
try:
    value = int(user_input)
except ValueError:
    print("Not a valid integer")
# ❌ NEVER: except:  or  except Exception:  (too broad)

# 2. Use exception chaining
class DatabaseError(Exception):
    pass

def get_user(user_id):
    try:
        return db.query(f"SELECT * FROM users WHERE id={user_id}")
    except ConnectionError as e:
        raise DatabaseError(f"Failed to fetch user {user_id}") from e
        # The original exception is preserved in __cause__

# 3. EAFP vs LBYL
# LBYL (Look Before You Leap) — non-Pythonic
if key in dictionary:
    value = dictionary[key]

# EAFP (Easier to Ask Forgiveness) — Pythonic ✅
try:
    value = dictionary[key]
except KeyError:
    value = default_value

# Even better for this case:
value = dictionary.get(key, default_value)

# 4. Custom exception hierarchies
class AppError(Exception):
    """Base exception for our application."""
    pass

class ValidationError(AppError):
    """Raised when input validation fails."""
    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(f"Validation error on '{field}': {message}")

class NotFoundError(AppError):
    """Raised when a resource is not found."""
    def __init__(self, resource, identifier):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} '{identifier}' not found")

# Usage
try:
    if not email:
        raise ValidationError("email", "Email is required")
    user = find_user(email)
    if not user:
        raise NotFoundError("User", email)
except ValidationError as e:
    return {"error": e.message, "field": e.field}, 400
except NotFoundError as e:
    return {"error": str(e)}, 404

# 5. Context managers for cleanup (preferred over try/finally)
# ❌ Manual cleanup
f = open("file.txt")
try:
    data = f.read()
finally:
    f.close()

# ✅ Context manager
with open("file.txt") as f:
    data = f.read()

# 6. ExceptionGroup (Python 3.11+)
# Handle multiple exceptions simultaneously
try:
    results = await asyncio.gather(task1(), task2(), task3())
except* ValueError as eg:
    for e in eg.exceptions:
        print(f"Value error: {e}")
except* TypeError as eg:
    for e in eg.exceptions:
        print(f"Type error: {e}")
```

---

## 1.4 Functions — Deep Dive

### Q10: Explain all types of function arguments in Python.

**Answer:**

```python
# 1. Positional arguments
def greet(name, greeting):
    return f"{greeting}, {name}!"

greet("Alice", "Hello")           # Positional
greet(greeting="Hi", name="Bob")  # Keyword (any order)

# 2. Default arguments
def connect(host, port=5432, timeout=30):
    print(f"Connecting to {host}:{port} (timeout={timeout}s)")

connect("localhost")                    # Uses defaults
connect("localhost", port=3306)         # Override specific default

# 3. *args — Variable positional arguments (tuple)
def sum_all(*args):
    print(type(args))    # <class 'tuple'>
    return sum(args)

sum_all(1, 2, 3, 4)     # 10

# 4. **kwargs — Variable keyword arguments (dict)
def create_user(**kwargs):
    print(type(kwargs))  # <class 'dict'>
    for key, value in kwargs.items():
        print(f"  {key} = {value}")

create_user(name="Alice", age=30, role="admin")

# 5. Combined — the full signature order matters!
def full_example(pos1, pos2, /, normal, *args, kw_only, **kwargs):
    """
    pos1, pos2    → Positional-only (before /)
    normal        → Normal (positional or keyword)
    *args         → Extra positional
    kw_only       → Keyword-only (after *)
    **kwargs      → Extra keyword
    """
    pass

# 6. Positional-only parameters (Python 3.8+, PEP 570)
def divmod_custom(x, y, /):
    return x // y, x % y

divmod_custom(10, 3)        # ✅ Works
# divmod_custom(x=10, y=3) # ❌ TypeError — positional-only!

# 7. Keyword-only parameters (after * or *args)
def configure(*, debug=False, verbose=False, log_level="INFO"):
    pass

# configure(True)               # ❌ TypeError
configure(debug=True)            # ✅ Must use keyword

# 8. Practical example combining everything
def api_request(
    method,              # Normal positional
    url,                 # Normal positional
    /,                   # Everything above is positional-only
    headers=None,        # Normal with default
    *args,               # Extra positional (rarely used here)
    timeout=30,          # Keyword-only with default
    retry=3,             # Keyword-only with default
    **kwargs             # Extra keywords
):
    """Well-designed API function signature."""
    pass
```

---

### Q11: Explain closures and when to use them.

**Answer:**
A closure is a function that remembers the variables from its enclosing scope even after the outer function has finished executing.

```python
# Basic closure
def make_multiplier(factor):
    def multiply(x):
        return x * factor    # 'factor' is captured from enclosing scope
    return multiply

double = make_multiplier(2)
triple = make_multiplier(3)

print(double(5))    # 10
print(triple(5))    # 15

# Inspect closure variables
print(double.__closure__[0].cell_contents)  # 2

# Closure for stateful functions (counter)
def make_counter(start=0):
    count = [start]          # Use list because we need mutability
    def counter():
        count[0] += 1
        return count[0]
    return counter

c = make_counter()
print(c())  # 1
print(c())  # 2
print(c())  # 3

# Using nonlocal (Python 3+) — cleaner approach
def make_counter_v2(start=0):
    count = start
    def counter():
        nonlocal count       # Allows modification of enclosing variable
        count += 1
        return count
    return counter

# Real-world usage: Logging decorator with closure
def logger(func_name):
    log = []
    def log_call(*args, **kwargs):
        entry = f"{func_name} called with args={args}, kwargs={kwargs}"
        log.append(entry)
        print(entry)
    def get_log():
        return log.copy()
    log_call.get_log = get_log
    return log_call

track = logger("process_data")
track(1, 2, mode="fast")
track(3, 4)
print(track.get_log())

# TRAP: Late binding in closures
functions = []
for i in range(5):
    functions.append(lambda: i)     # ⚠️ All capture the SAME 'i'

print([f() for f in functions])     # [4, 4, 4, 4, 4] — All 4!

# Fix: Use default argument to capture current value
functions = []
for i in range(5):
    functions.append(lambda i=i: i)  # ✅ Each captures its own 'i'

print([f() for f in functions])      # [0, 1, 2, 3, 4]
```

---

### Q12: What are first-class functions? Explain higher-order functions.

**Answer:**
In Python, functions are **first-class objects** — they can be assigned to variables, passed as arguments, returned from functions, and stored in data structures.

```python
# Functions as objects
def shout(text):
    return text.upper()

def whisper(text):
    return text.lower()

# Assign to variable
yell = shout
print(yell("hello"))  # HELLO

# Store in data structures
formatters = {
    "upper": shout,
    "lower": whisper,
    "title": str.title,
}
print(formatters["title"]("hello world"))  # Hello World

# Higher-order function: takes function as argument
def apply_to_list(func, items):
    return [func(item) for item in items]

names = ["alice", "bob", "charlie"]
print(apply_to_list(str.upper, names))   # ['ALICE', 'BOB', 'CHARLIE']

# Higher-order function: returns a function
def make_validator(min_val, max_val):
    def validate(x):
        return min_val <= x <= max_val
    return validate

is_valid_age = make_validator(0, 150)
is_valid_score = make_validator(0, 100)

print(is_valid_age(25))     # True
print(is_valid_score(150))  # False

# Built-in higher-order functions
numbers = [1, -2, 3, -4, 5]

# map — apply function to each item
squared = list(map(lambda x: x**2, numbers))        # [1, 4, 9, 16, 25]

# filter — keep items where function returns True
positives = list(filter(lambda x: x > 0, numbers))  # [1, 3, 5]

# sorted with key function
students = [("Alice", 88), ("Bob", 75), ("Charlie", 93)]
by_grade = sorted(students, key=lambda s: s[1], reverse=True)
# [('Charlie', 93), ('Alice', 88), ('Bob', 75)]

# reduce — accumulate values
from functools import reduce
product = reduce(lambda a, b: a * b, [1, 2, 3, 4])  # 24
```

---

## 1.5 Comprehensions & Generators

### Q13: Compare list comprehension, generator expression, dict/set comprehension.

**Answer:**

```python
# List comprehension — creates full list in memory
squares = [x**2 for x in range(10)]
# [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# Generator expression — lazy evaluation, produces items one at a time
squares_gen = (x**2 for x in range(10))
# <generator object> — no memory allocated for all items
print(next(squares_gen))  # 0
print(next(squares_gen))  # 1

# Dict comprehension
word_lengths = {word: len(word) for word in ["hello", "world", "python"]}
# {'hello': 5, 'world': 5, 'python': 6}

# Set comprehension
unique_lengths = {len(word) for word in ["hello", "world", "python"]}
# {5, 6}

# Nested comprehension
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [x for row in matrix for x in row]         # [1, 2, 3, 4, 5, 6, 7, 8, 9]
transposed = [[row[i] for row in matrix] for i in range(3)]

# Conditional comprehension
evens = [x for x in range(20) if x % 2 == 0]
labels = ["even" if x % 2 == 0 else "odd" for x in range(5)]
# ['even', 'odd', 'even', 'odd', 'even']

# MEMORY COMPARISON — why generators matter
import sys

list_comp = [x**2 for x in range(1_000_000)]
gen_expr = (x**2 for x in range(1_000_000))

print(sys.getsizeof(list_comp))  # ~8,448,728 bytes (~8 MB)
print(sys.getsizeof(gen_expr))   # 200 bytes (constant!)

# Real-world: Processing large CSV line by line
def read_large_csv(filename):
    with open(filename) as f:
        header = next(f).strip().split(",")
        return (
            dict(zip(header, line.strip().split(",")))
            for line in f
        )

# Processes millions of rows with constant memory
for row in read_large_csv("huge_data.csv"):
    if row["status"] == "active":
        process(row)
```

---

### Q14: What is the difference between `yield` and `return`?

**Answer:**

```python
# return — ends function, returns value, function state is lost
def get_squares_list(n):
    result = []
    for i in range(n):
        result.append(i**2)
    return result                    # All computed at once

# yield — pauses function, returns value, state is preserved
def get_squares_gen(n):
    for i in range(n):
        yield i**2                   # Produces one value at a time

# Usage
for sq in get_squares_list(5):       # List: all 5 squares in memory
    print(sq)

for sq in get_squares_gen(5):        # Generator: one at a time
    print(sq)

# yield from — delegate to sub-generator (Python 3.3+)
def flatten(nested):
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)  # Delegate to recursive call
        else:
            yield item

nested = [1, [2, [3, 4], 5], [6, 7]]
print(list(flatten(nested)))  # [1, 2, 3, 4, 5, 6, 7]

# Generator as coroutine (send values INTO generator)
def running_average():
    total = 0
    count = 0
    average = None
    while True:
        value = yield average        # Receive value via .send()
        total += value
        count += 1
        average = total / count

avg = running_average()
next(avg)              # Prime the generator (advance to first yield)
print(avg.send(10))    # 10.0
print(avg.send(20))    # 15.0
print(avg.send(30))    # 20.0

# Generator with cleanup
def managed_resource():
    print("Acquiring resource")
    try:
        yield "resource_handle"
    finally:
        print("Releasing resource")  # Always runs on .close() or GC

gen = managed_resource()
handle = next(gen)     # "Acquiring resource"
gen.close()            # "Releasing resource"
```

---

## 1.6 Scope & Namespaces

### Q15: Explain Python's LEGB rule with examples.

**Answer:**
Python resolves names using the **LEGB** rule — searching in order:

```
L — Local:      Inside the current function
E — Enclosing:  Inside enclosing functions (closures)
G — Global:     Module-level
B — Built-in:   Python's built-in namespace (len, print, etc.)
```

```python
x = "global"                    # G — Global scope

def outer():
    x = "enclosing"             # E — Enclosing scope

    def inner():
        x = "local"             # L — Local scope
        print(x)                # → "local" (found in L)

    inner()
    print(x)                    # → "enclosing" (found in E)

outer()
print(x)                        # → "global" (found in G)

# Modifying outer scopes
count = 0

def increment():
    global count                 # Required to modify global variable
    count += 1

def outer_v2():
    total = 0
    def inner_v2():
        nonlocal total           # Required to modify enclosing variable
        total += 1
        return total
    return inner_v2

# Built-in scope example
print(len([1,2,3]))             # len is found in B (built-in)

# TRAP: Shadowing built-ins
list = [1, 2, 3]                # ⚠️ Shadows built-in 'list'
# list("abc")                   # ❌ TypeError — 'list' is now a list object, not the class!
del list                        # Restore access to built-in

# Namespace inspection
def show_namespaces():
    local_var = 42
    print("Locals:", locals())
    print("Globals keys:", list(globals().keys())[:5])

import builtins
print(dir(builtins)[:10])       # See built-in names
```

---

## 1.7 String Operations

### Q16: Advanced string formatting and manipulation techniques.

**Answer:**

```python
# 1. f-strings (Python 3.6+) — most Pythonic
name = "Alice"
age = 30
print(f"{name} is {age} years old")

# f-string with expressions
print(f"{2 ** 10 = }")                    # "2 ** 10 = 1024"  (debug format, 3.8+)
print(f"{name!r}")                         # "'Alice'" (repr)
print(f"{3.14159:.2f}")                    # "3.14"
print(f"{'hello':>20}")                    # "               hello" (right-align)
print(f"{'hello':*^20}")                   # "*******hello********" (center with fill)
print(f"{1000000:,}")                      # "1,000,000"
print(f"{0.756:.1%}")                      # "75.6%"

# 2. Template strings — safe for user-provided templates
from string import Template
t = Template("Hello $name, your balance is $balance")
print(t.safe_substitute(name="Alice"))     # Missing keys don't raise errors

# 3. Important string methods
text = "  Hello, World!  "
text.strip()                # "Hello, World!"
text.lstrip()               # "Hello, World!  "
text.split(", ")            # ['  Hello', 'World!  ']
"_".join(["a","b","c"])     # "a_b_c"
text.replace("World", "Python")
text.startswith("  He")     # True
text.find("World")          # 9 (index) or -1
text.index("World")         # 9 (raises ValueError if not found)
"hello123".isalnum()        # True
"hello".isalpha()           # True
"123".isdigit()             # True

# 4. Efficient string concatenation
# ❌ Slow — creates new string each iteration
result = ""
for word in words:
    result += word + " "

# ✅ Fast — join is O(n)
result = " ".join(words)

# ✅ For complex building — use list then join
parts = []
for item in data:
    parts.append(process(item))
result = "\n".join(parts)

# 5. Regular expressions
import re

text = "Contact us at support@example.com or sales@example.com"
emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', text)
# ['support@example.com', 'sales@example.com']

# Named groups
pattern = r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})'
match = re.search(pattern, "Date: 2024-03-15")
if match:
    print(match.group("year"))    # "2024"
    print(match.groupdict())      # {'year': '2024', 'month': '03', 'day': '15'}
```

---

## 1.8 Built-in Functions Mastery

### Q17: Explain these commonly asked built-in functions with examples.

**Answer:**

```python
# enumerate — get index + value
fruits = ["apple", "banana", "cherry"]
for i, fruit in enumerate(fruits, start=1):
    print(f"{i}. {fruit}")
# 1. apple   2. banana   3. cherry

# zip — combine iterables
names = ["Alice", "Bob"]
scores = [95, 87]
grades = ["A", "B"]
for name, score, grade in zip(names, scores, grades):
    print(f"{name}: {score} ({grade})")

# zip_longest — don't truncate
from itertools import zip_longest
list(zip_longest([1,2,3], [10,20], fillvalue=0))
# [(1,10), (2,20), (3,0)]

# any / all
nums = [2, 4, 6, 8]
print(all(x % 2 == 0 for x in nums))    # True — all even
print(any(x > 5 for x in nums))          # True — at least one > 5

# map / filter
temps_c = [0, 20, 37, 100]
temps_f = list(map(lambda c: c * 9/5 + 32, temps_c))
# [32.0, 68.0, 98.6, 212.0]

adults = list(filter(lambda p: p["age"] >= 18, people))

# sorted with complex keys
from operator import itemgetter, attrgetter

students = [{"name": "Alice", "gpa": 3.9}, {"name": "Bob", "gpa": 3.7}]
sorted(students, key=itemgetter("gpa"), reverse=True)

# isinstance / issubclass
print(isinstance(42, int))            # True
print(isinstance(True, int))          # True — bool is subclass of int!
print(isinstance(42, (int, float)))   # True — check multiple types

# vars / dir / type / id
class MyObj:
    x = 10
obj = MyObj()
print(vars(obj))     # {} (instance dict — x is class-level)
print(dir(obj))      # All attributes including inherited
print(type(obj))     # <class '__main__.MyObj'>
print(id(obj))       # Memory address (integer)

# getattr / setattr / hasattr / delattr
class Config:
    debug = False
    timeout = 30

cfg = Config()
print(getattr(cfg, "debug"))              # False
print(getattr(cfg, "missing", "default")) # "default" (with fallback)
setattr(cfg, "debug", True)
print(hasattr(cfg, "timeout"))            # True
```

---

### Q18: What are `__name__` and `if __name__ == "__main__":`?

**Answer:**

```python
# Every Python module has a __name__ attribute
# When run directly: __name__ == "__main__"
# When imported:     __name__ == module's name

# mymodule.py
def greet(name):
    return f"Hello, {name}!"

def main():
    print(greet("World"))

if __name__ == "__main__":
    main()

# When you run: python mymodule.py → __name__ is "__main__" → main() runs
# When you do:  import mymodule     → __name__ is "mymodule" → main() does NOT run

# Why this matters:
# 1. Allows a file to be both a module (importable) and a script (runnable)
# 2. Prevents code from executing on import
# 3. Enables testing the module standalone

# Best practice for larger scripts
import sys

def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="World")
    return parser.parse_args()

def main():
    args = parse_args()
    print(greet(args.name))
    return 0

if __name__ == "__main__":
    sys.exit(main())     # Return exit code for CLI usage
```

---

### Q19: How does Python's garbage collection work?

**Answer:**

```python
# Python uses TWO mechanisms for memory management:

# 1. Reference Counting (primary) — immediate, deterministic
import sys

a = [1, 2, 3]           # refcount = 1
b = a                    # refcount = 2
print(sys.getrefcount(a))  # 3 (includes the getrefcount argument itself)

del b                    # refcount decreases
# When refcount hits 0, memory is freed immediately

# 2. Cyclic Garbage Collector (secondary) — for reference cycles
import gc

class Node:
    def __init__(self):
        self.ref = None

# Create a cycle
a = Node()
b = Node()
a.ref = b     # a → b
b.ref = a     # b → a  (CYCLE!)

del a
del b
# refcount never hits 0 because of the cycle!
# The cyclic GC detects and collects these

# GC control
gc.collect()                 # Force garbage collection
gc.get_count()               # Objects in each generation (gen0, gen1, gen2)
gc.get_threshold()           # (700, 10, 10) — thresholds for each generation
gc.disable()                 # Disable automatic GC (rare, for performance tuning)
gc.enable()                  # Re-enable

# Generational GC:
# Gen 0: New objects → collected most frequently
# Gen 1: Survived one collection
# Gen 2: Long-lived objects → collected least frequently

# Weak references — don't increase refcount
import weakref

class ExpensiveObject:
    def __init__(self, name):
        self.name = name

obj = ExpensiveObject("test")
weak = weakref.ref(obj)

print(weak())        # <ExpensiveObject object>
del obj
print(weak())        # None — object was garbage collected

# Usage: Caches that don't prevent garbage collection
cache = weakref.WeakValueDictionary()
```

**Usage:** Understanding GC helps with memory leak debugging, large-scale application optimization, and explaining performance characteristics in system design.

---
