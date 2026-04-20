# 02 — Object-Oriented Programming in Python
## Complete Interview Questions with Examples

---

## 2.1 Classes & Objects

### Q1: Explain the difference between class variables and instance variables.

**Answer:**

```python
class Employee:
    # Class variable — shared by ALL instances
    company = "TechCorp"
    employee_count = 0

    def __init__(self, name, salary):
        # Instance variables — unique to each instance
        self.name = name
        self.salary = salary
        Employee.employee_count += 1    # Modify via class name

# Demonstration
e1 = Employee("Alice", 90000)
e2 = Employee("Bob", 85000)

print(e1.company)            # "TechCorp" — accessed via instance (reads class var)
print(e2.company)            # "TechCorp"
print(Employee.company)      # "TechCorp" — accessed via class

# TRAP: Assigning via instance creates a NEW instance variable (shadows class var)
e1.company = "NewCorp"       # Creates instance variable on e1 ONLY
print(e1.company)            # "NewCorp" — instance variable
print(e2.company)            # "TechCorp" — still class variable
print(Employee.company)      # "TechCorp" — class variable unchanged

print(e1.__dict__)           # {'name': 'Alice', 'salary': 90000, 'company': 'NewCorp'}
print(e2.__dict__)           # {'name': 'Bob', 'salary': 85000}  — no 'company'!

# TRAP with mutable class variables
class BadTeam:
    members = []                     # ⚠️ Shared mutable class variable
    def add_member(self, name):
        self.members.append(name)    # Modifies the SHARED list

t1 = BadTeam()
t2 = BadTeam()
t1.add_member("Alice")
print(t2.members)                    # ["Alice"] — Bug! Shared across instances

class GoodTeam:
    def __init__(self):
        self.members = []            # ✅ Instance variable — unique to each
```

---

### Q2: Explain `__init__`, `__new__`, `__del__` and object lifecycle.

**Answer:**

```python
class MyClass:
    def __new__(cls, *args, **kwargs):
        """
        Called FIRST. Creates and returns the instance.
        Rarely overridden — use for:
          - Singletons
          - Immutable types (str, int, tuple)
          - Custom metaclass behavior
        """
        print("1. __new__ called — creating instance")
        instance = super().__new__(cls)
        return instance

    def __init__(self, name):
        """
        Called SECOND. Initializes the instance.
        This is what you override 99% of the time.
        """
        print("2. __init__ called — initializing instance")
        self.name = name

    def __del__(self):
        """
        Called when object is garbage collected.
        NOT guaranteed to run (avoid for critical cleanup).
        Use context managers instead.
        """
        print(f"3. __del__ called — {self.name} being destroyed")

obj = MyClass("test")
# Output:
# 1. __new__ called — creating instance
# 2. __init__ called — initializing instance

del obj
# 3. __del__ called — test being destroyed

# Singleton pattern using __new__
class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, value=None):
        if value is not None:
            self.value = value

s1 = Singleton(42)
s2 = Singleton(99)
print(s1 is s2)       # True — same instance
print(s1.value)        # 99 — __init__ was called again!

# Immutable subclass using __new__
class PositiveInt(int):
    def __new__(cls, value):
        if value < 0:
            raise ValueError("Must be positive")
        return super().__new__(cls, value)

n = PositiveInt(42)
print(n + 8)           # 50 — works like a normal int
# PositiveInt(-5)      # ValueError: Must be positive
```

---

### Q3: Explain all four pillars of OOP with Python examples.

**Answer:**

```python
# ═══════════════════════════════════════════
# 1. ENCAPSULATION — bundling data + methods, controlling access
# ═══════════════════════════════════════════
class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner            # Public
        self._account_type = "savings" # Protected (convention — "don't touch")
        self.__balance = balance       # Private (name mangling)

    def deposit(self, amount):
        if amount > 0:
            self.__balance += amount
            return True
        return False

    def get_balance(self):             # Controlled access
        return self.__balance

    @property
    def balance(self):                 # Pythonic way — property
        return self.__balance

    @balance.setter
    def balance(self, value):
        if value < 0:
            raise ValueError("Balance cannot be negative")
        self.__balance = value

acc = BankAccount("Alice", 1000)
print(acc.balance)              # 1000 (via property)
acc.balance = 500               # Uses setter (validates)
# acc.__balance                 # ❌ AttributeError (name-mangled)
print(acc._BankAccount__balance) # 500 — name mangling (accessible but DON'T)


# ═══════════════════════════════════════════
# 2. INHERITANCE — reuse and extend existing classes
# ═══════════════════════════════════════════
class Animal:
    def __init__(self, name, species):
        self.name = name
        self.species = species

    def speak(self):
        raise NotImplementedError("Subclasses must implement speak()")

    def __str__(self):
        return f"{self.name} ({self.species})"

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name, species="Canine")   # Call parent __init__
        self.breed = breed

    def speak(self):
        return "Woof!"

    def fetch(self, item):
        return f"{self.name} fetches the {item}"

class Cat(Animal):
    def speak(self):
        return "Meow!"

dog = Dog("Rex", "German Shepherd")
cat = Cat("Whiskers", "Feline")
print(dog.speak())     # "Woof!"
print(dog.fetch("ball"))  # "Rex fetches the ball"


# ═══════════════════════════════════════════
# 3. POLYMORPHISM — same interface, different behavior
# ═══════════════════════════════════════════
def animal_sound(animal: Animal):
    """Works with ANY Animal subclass — polymorphism!"""
    print(f"{animal.name} says: {animal.speak()}")

animal_sound(dog)      # Rex says: Woof!
animal_sound(cat)      # Whiskers says: Meow!

# Duck typing — Python's approach to polymorphism
class Robot:
    def __init__(self):
        self.name = "RoboBot"
    def speak(self):
        return "Beep boop!"

animal_sound(Robot())  # Works! Python doesn't care about the class — only the method


# ═══════════════════════════════════════════
# 4. ABSTRACTION — hide complexity, show essentials
# ═══════════════════════════════════════════
from abc import ABC, abstractmethod

class PaymentProcessor(ABC):
    """Abstract base class — cannot be instantiated directly."""

    @abstractmethod
    def process_payment(self, amount: float) -> bool:
        """Must be implemented by subclasses."""
        pass

    @abstractmethod
    def refund(self, transaction_id: str) -> bool:
        pass

    def validate_amount(self, amount: float) -> bool:
        """Concrete method — shared logic."""
        return amount > 0

class StripeProcessor(PaymentProcessor):
    def process_payment(self, amount):
        if self.validate_amount(amount):
            print(f"Processing ${amount} via Stripe")
            return True
        return False

    def refund(self, transaction_id):
        print(f"Refunding {transaction_id} via Stripe")
        return True

# PaymentProcessor()          # ❌ TypeError — can't instantiate abstract class
processor = StripeProcessor()  # ✅ All abstract methods implemented
processor.process_payment(99.99)
```

---

## 2.2 Inheritance Deep Dive

### Q4: Explain Method Resolution Order (MRO) and the diamond problem.

**Answer:**

```python
# Diamond problem: D inherits from B and C, which both inherit from A
class A:
    def method(self):
        print("A.method")

class B(A):
    def method(self):
        print("B.method")
        super().method()

class C(A):
    def method(self):
        print("C.method")
        super().method()

class D(B, C):
    def method(self):
        print("D.method")
        super().method()

# MRO is computed using C3 Linearization algorithm
print(D.__mro__)
# (<class 'D'>, <class 'B'>, <class 'C'>, <class 'A'>, <class 'object'>)

d = D()
d.method()
# Output:
# D.method
# B.method
# C.method
# A.method
# → Each class is called ONCE, in MRO order. No duplicate calls!

# MRO Rules (C3 Linearization):
# 1. Children come before parents
# 2. Left parents come before right parents (in class definition order)
# 3. Relative order is preserved

# Practical example: Mixins
class LoggingMixin:
    def log(self, message):
        print(f"[LOG] {self.__class__.__name__}: {message}")

class SerializerMixin:
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items()
                if not k.startswith('_')}

class User(LoggingMixin, SerializerMixin):
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def save(self):
        self.log(f"Saving user {self.name}")
        data = self.to_dict()
        # ... save to database
        return data

user = User("Alice", "alice@example.com")
user.save()
print(user.to_dict())  # {'name': 'Alice', 'email': 'alice@example.com'}
```

---

### Q5: What are `@classmethod`, `@staticmethod`, and `@property`?

**Answer:**

```python
class Temperature:
    # Class variable
    _conversion_factor = 1.8

    def __init__(self, celsius):
        self._celsius = celsius

    # INSTANCE METHOD — operates on instance (self)
    def to_fahrenheit(self):
        return self._celsius * self._conversion_factor + 32

    # CLASS METHOD — operates on class (cls), not instance
    @classmethod
    def from_fahrenheit(cls, fahrenheit):
        """Alternative constructor — creates Temperature from Fahrenheit."""
        celsius = (fahrenheit - 32) / cls._conversion_factor
        return cls(celsius)          # cls() allows subclass to work correctly

    @classmethod
    def from_kelvin(cls, kelvin):
        """Another alternative constructor."""
        return cls(kelvin - 273.15)

    # STATIC METHOD — no access to instance or class
    @staticmethod
    def is_valid_temperature(celsius):
        """Utility function — doesn't need instance or class."""
        return celsius >= -273.15     # Above absolute zero

    # PROPERTY — attribute-like access with getter/setter/deleter
    @property
    def celsius(self):
        """Getter — accessed like an attribute."""
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        """Setter — validates on assignment."""
        if value < -273.15:
            raise ValueError("Temperature below absolute zero!")
        self._celsius = value

    @celsius.deleter
    def celsius(self):
        """Deleter — called on del obj.celsius."""
        print("Resetting temperature")
        self._celsius = 0

    def __repr__(self):
        return f"Temperature({self._celsius}°C)"

# Usage
t1 = Temperature(100)
t2 = Temperature.from_fahrenheit(212)      # classmethod as factory
t3 = Temperature.from_kelvin(373.15)       # classmethod as factory

print(t1.celsius)            # 100 — property getter
t1.celsius = 50              # Property setter (validated)
# t1.celsius = -300          # ValueError!

Temperature.is_valid_temperature(-300)  # False — staticmethod

# Why classmethod over staticmethod for factories?
class SpecialTemp(Temperature):
    pass

st = SpecialTemp.from_fahrenheit(212)
print(type(st))  # <class 'SpecialTemp'> — cls ensures correct type!
# If it were a staticmethod using Temperature(), it would always return Temperature
```

---

### Q6: Explain descriptors — the mechanism behind properties.

**Answer:**

```python
# A descriptor is any object that implements __get__, __set__, or __delete__
# Properties, classmethod, staticmethod are ALL implemented as descriptors

class Validated:
    """A reusable descriptor for validated attributes."""
    def __init__(self, min_value=None, max_value=None):
        self.min_value = min_value
        self.max_value = max_value

    def __set_name__(self, owner, name):
        """Called when descriptor is assigned to a class attribute."""
        self.name = name                    # Store the attribute name
        self.storage_name = f"_{name}"      # Private storage name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self                      # Accessed via class
        return getattr(obj, self.storage_name, None)

    def __set__(self, obj, value):
        if self.min_value is not None and value < self.min_value:
            raise ValueError(f"{self.name} must be >= {self.min_value}")
        if self.max_value is not None and value > self.max_value:
            raise ValueError(f"{self.name} must be <= {self.max_value}")
        setattr(obj, self.storage_name, value)

    def __delete__(self, obj):
        delattr(obj, self.storage_name)

# Usage — reusable validation across multiple classes
class Product:
    price = Validated(min_value=0)
    quantity = Validated(min_value=0, max_value=10000)
    rating = Validated(min_value=0, max_value=5)

    def __init__(self, name, price, quantity, rating):
        self.name = name
        self.price = price           # Triggers Validated.__set__
        self.quantity = quantity
        self.rating = rating

p = Product("Widget", 9.99, 100, 4.5)
print(p.price)                       # 9.99 — triggers Validated.__get__
# p.price = -5                       # ValueError: price must be >= 0
# p.rating = 6                       # ValueError: rating must be <= 5

# Descriptor protocol:
# Data descriptor:     has __set__ and/or __delete__ → takes priority over instance dict
# Non-data descriptor: only __get__ → instance dict takes priority
# Lookup order: data descriptor → instance __dict__ → non-data descriptor → __getattr__
```

---

## 2.3 Advanced OOP

### Q7: What are metaclasses? When would you use them?

**Answer:**

```python
# In Python, EVERYTHING is an object, including classes.
# A metaclass is the "class of a class" — it defines how classes behave.

# type is the default metaclass
class MyClass:
    pass

print(type(MyClass))       # <class 'type'>
print(type(type))          # <class 'type'> — type is its own metaclass!

# Creating a class dynamically with type()
# type(name, bases, namespace)
DynamicClass = type('DynamicClass', (object,), {
    'x': 10,
    'greet': lambda self: f"Hello from {self.__class__.__name__}"
})

obj = DynamicClass()
print(obj.greet())         # "Hello from DynamicClass"

# Custom metaclass — controls class creation
class ValidatedMeta(type):
    """Metaclass that enforces rules on class definitions."""

    def __new__(mcs, name, bases, namespace):
        # Enforce: all classes must have a docstring
        if not namespace.get('__doc__'):
            raise TypeError(f"Class '{name}' must have a docstring")

        # Enforce: methods starting with 'test_' must exist if class has 'run_tests'
        if 'run_tests' in namespace:
            test_methods = [k for k in namespace if k.startswith('test_')]
            if not test_methods:
                raise TypeError(f"Class '{name}' has run_tests but no test methods")

        cls = super().__new__(mcs, name, bases, namespace)
        return cls

# class BadClass(metaclass=ValidatedMeta):  # ❌ TypeError: must have docstring
#     pass

class GoodClass(metaclass=ValidatedMeta):
    """This class is valid."""
    pass

# Real-world use case: Auto-registering plugins
class PluginRegistry(type):
    plugins = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if bases:  # Don't register the base class itself
            mcs.plugins[name] = cls
        return cls

class Plugin(metaclass=PluginRegistry):
    """Base class for all plugins."""
    pass

class PDFExporter(Plugin):
    def export(self, data):
        return f"Exporting to PDF: {data}"

class CSVExporter(Plugin):
    def export(self, data):
        return f"Exporting to CSV: {data}"

# All plugins auto-registered!
print(PluginRegistry.plugins)
# {'PDFExporter': <class 'PDFExporter'>, 'CSVExporter': <class 'CSVExporter'>}

# Factory from registry
def get_exporter(format_name):
    cls = PluginRegistry.plugins.get(f"{format_name}Exporter")
    if cls:
        return cls()
    raise ValueError(f"Unknown format: {format_name}")

exporter = get_exporter("PDF")
print(exporter.export("report"))  # "Exporting to PDF: report"
```

**When to use metaclasses:** ORMs (Django models), plugin systems, API frameworks, validation. Most developers should prefer decorators or `__init_subclass__` (simpler alternatives).

---

### Q8: Explain `__init_subclass__` — the simpler metaclass alternative.

**Answer:**

```python
# Python 3.6+ — much simpler than metaclasses for most use cases

class Plugin:
    _registry = {}

    def __init_subclass__(cls, plugin_name=None, **kwargs):
        """Called automatically when a class inherits from Plugin."""
        super().__init_subclass__(**kwargs)
        name = plugin_name or cls.__name__
        Plugin._registry[name] = cls
        print(f"Registered plugin: {name}")

    @classmethod
    def get_plugin(cls, name):
        return cls._registry.get(name)

class ImageProcessor(Plugin, plugin_name="image"):
    def process(self):
        return "Processing image"

class VideoProcessor(Plugin, plugin_name="video"):
    def process(self):
        return "Processing video"

# Automatically registered!
print(Plugin._registry)
# {'image': <class 'ImageProcessor'>, 'video': <class 'VideoProcessor'>}

processor = Plugin.get_plugin("image")()
print(processor.process())  # "Processing image"

# Another use: enforcing interface
class Serializable:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'serialize'):
            raise TypeError(f"{cls.__name__} must implement serialize()")
        if not hasattr(cls, 'deserialize'):
            raise TypeError(f"{cls.__name__} must implement deserialize()")

class User(Serializable):
    def serialize(self):
        return {"name": self.name}

    @classmethod
    def deserialize(cls, data):
        return cls(data["name"])
```

---

### Q9: Explain `__slots__` and when to use them.

**Answer:**

```python
import sys

# Normal class — uses __dict__ for attribute storage (flexible but memory-heavy)
class PointDict:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# Slots class — fixed attributes, no __dict__ (memory-efficient)
class PointSlots:
    __slots__ = ('x', 'y')
    def __init__(self, x, y):
        self.x = x
        self.y = y

# Memory comparison
pd = PointDict(1, 2)
ps = PointSlots(1, 2)

print(sys.getsizeof(pd) + sys.getsizeof(pd.__dict__))  # ~152 bytes
print(sys.getsizeof(ps))                                 # ~56 bytes
# ~63% memory saving!

# For millions of objects, this adds up dramatically
# 1 million PointDict objects ≈ 152 MB
# 1 million PointSlots objects ≈ 56 MB

# Restrictions with __slots__
ps.z = 10  # ❌ AttributeError — can't add new attributes
# No __dict__ available (unless explicitly included in __slots__)

# Slots with inheritance
class Point3D(PointSlots):
    __slots__ = ('z',)     # Only add NEW slots
    def __init__(self, x, y, z):
        super().__init__(x, y)
        self.z = z

# Best practices:
# ✅ Use slots for data classes with many instances (ORM models, data points)
# ✅ Use slots when memory is a concern
# ❌ Don't use if you need dynamic attributes
# ❌ Don't use with multiple inheritance (complex interactions)
```

---

### Q10: Explain Python's data classes (`@dataclass`).

**Answer:**

```python
from dataclasses import dataclass, field, asdict, astuple
from typing import List, Optional

# Basic dataclass — auto-generates __init__, __repr__, __eq__
@dataclass
class User:
    name: str
    email: str
    age: int
    active: bool = True    # Default value

user = User("Alice", "alice@ex.com", 30)
print(user)             # User(name='Alice', email='alice@ex.com', age=30, active=True)
print(user == User("Alice", "alice@ex.com", 30))  # True — __eq__ auto-generated

# Advanced dataclass
@dataclass(order=True, frozen=True)    # order: comparison methods, frozen: immutable
class Version:
    major: int
    minor: int
    patch: int

    @property
    def string(self):
        return f"{self.major}.{self.minor}.{self.patch}"

v1 = Version(2, 0, 1)
v2 = Version(2, 1, 0)
print(v1 < v2)         # True — compares field by field
# v1.major = 3          # ❌ FrozenInstanceError — immutable!
print(sorted([v2, v1])) # [Version(2, 0, 1), Version(2, 1, 0)]

# Mutable default fields — use field(default_factory=...)
@dataclass
class Team:
    name: str
    members: List[str] = field(default_factory=list)     # ✅ Correct
    metadata: dict = field(default_factory=dict)
    _id: int = field(init=False, repr=False)              # Excluded from __init__ and __repr__

    def __post_init__(self):
        """Called after __init__ — for derived fields or validation."""
        self._id = hash(self.name)
        if not self.name:
            raise ValueError("Team name cannot be empty")

team = Team("Engineering")
team.members.append("Alice")
print(team)            # Team(name='Engineering', members=['Alice'], metadata={})

# Conversion utilities
print(asdict(team))     # {'name': 'Engineering', 'members': ['Alice'], 'metadata': {}}
print(astuple(team))    # ('Engineering', ['Alice'], {})

# Dataclass vs namedtuple vs regular class:
# dataclass:    Mutable by default, type hints, methods, full OOP
# namedtuple:   Immutable, lightweight, tuple subclass, limited
# regular class: Full control, more boilerplate
```

---

### Q11: What is the `__call__` method? How to make objects callable?

**Answer:**

```python
class Multiplier:
    def __init__(self, factor):
        self.factor = factor

    def __call__(self, x):
        """Makes instance callable like a function."""
        return x * self.factor

double = Multiplier(2)
triple = Multiplier(3)

print(double(5))       # 10 — calling instance like a function
print(triple(5))       # 15
print(callable(double)) # True

# Real-world: Configurable decorator class
class retry:
    def __init__(self, max_attempts=3, delay=1):
        self.max_attempts = max_attempts
        self.delay = delay

    def __call__(self, func):
        import time
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, self.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == self.max_attempts:
                        raise
                    print(f"Attempt {attempt} failed: {e}. Retrying...")
                    time.sleep(self.delay)
        return wrapper

@retry(max_attempts=3, delay=2)
def fetch_data(url):
    # ... network request
    pass

# Real-world: Callable for ML inference pipeline
class SentimentAnalyzer:
    def __init__(self, model_path):
        self.model = self._load_model(model_path)

    def _load_model(self, path):
        # Load ML model
        return "model"

    def __call__(self, text):
        """Predict sentiment — usage: analyzer("Great product!")"""
        # preprocessed = self.preprocess(text)
        # return self.model.predict(preprocessed)
        return {"text": text, "sentiment": "positive", "confidence": 0.95}

analyze = SentimentAnalyzer("model.pkl")
result = analyze("This is amazing!")  # Calling like a function
print(result)
```

---

### Q12: Explain Abstract Base Classes (ABCs) and structural subtyping.

**Answer:**

```python
from abc import ABC, abstractmethod

# ABC — forces subclasses to implement required methods
class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        """Must be implemented by all shapes."""
        pass

    @abstractmethod
    def perimeter(self) -> float:
        pass

    def describe(self) -> str:
        """Concrete method — shared by all shapes."""
        return f"{self.__class__.__name__}: area={self.area():.2f}, perimeter={self.perimeter():.2f}"

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        import math
        return math.pi * self.radius ** 2

    def perimeter(self):
        import math
        return 2 * math.pi * self.radius

# Shape()                # ❌ TypeError — can't instantiate
c = Circle(5)
print(c.describe())      # "Circle: area=78.54, perimeter=31.42"

# Structural subtyping with register() — "virtual subclass"
class OldRectangle:
    """Legacy class that we can't modify."""
    def __init__(self, w, h):
        self.w, self.h = w, h
    def area(self):
        return self.w * self.h
    def perimeter(self):
        return 2 * (self.w + self.h)

Shape.register(OldRectangle)
print(isinstance(OldRectangle(3, 4), Shape))  # True — virtual subclass!

# Protocol classes (Python 3.8+) — structural typing
from typing import Protocol, runtime_checkable

@runtime_checkable
class Drawable(Protocol):
    def draw(self) -> None:
        ...

class Widget:
    def draw(self):
        print("Drawing widget")

# Widget doesn't inherit from Drawable, but structurally matches
w = Widget()
print(isinstance(w, Drawable))  # True — duck typing, formalized!
```

---

### Q13: Explain `__getattr__`, `__getattribute__`, and `__setattr__`.

**Answer:**

```python
class SmartObject:
    def __init__(self):
        # Must use object.__setattr__ to avoid recursion
        object.__setattr__(self, '_data', {})
        object.__setattr__(self, 'name', 'SmartObject')

    def __getattr__(self, name):
        """
        Called ONLY when normal attribute lookup fails.
        Use for: dynamic attributes, proxies, default values.
        """
        print(f"__getattr__ called for '{name}'")
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

    def __getattribute__(self, name):
        """
        Called for EVERY attribute access (before __getattr__).
        Rarely overridden — use cautiously to avoid infinite recursion.
        """
        print(f"__getattribute__ called for '{name}'")
        return object.__getattribute__(self, name)  # Use super to avoid recursion

    def __setattr__(self, name, value):
        """Called for EVERY attribute assignment."""
        print(f"__setattr__: {name} = {value}")
        if name.startswith('_'):
            object.__setattr__(self, name, value)   # Allow private attrs
        else:
            self._data[name] = value                # Store in dict

# Practical: Proxy pattern
class LazyProxy:
    """Delays initialization until first attribute access."""
    def __init__(self, factory):
        object.__setattr__(self, '_factory', factory)
        object.__setattr__(self, '_obj', None)

    def _ensure_loaded(self):
        if object.__getattribute__(self, '_obj') is None:
            factory = object.__getattribute__(self, '_factory')
            object.__setattr__(self, '_obj', factory())

    def __getattr__(self, name):
        self._ensure_loaded()
        return getattr(self._obj, name)

# Usage
def expensive_init():
    print("Loading expensive resource...")
    return {"data": [1, 2, 3]}

proxy = LazyProxy(expensive_init)
# Nothing loaded yet...
print(proxy["data"])  # NOW it loads → "Loading expensive resource..." → [1, 2, 3]
```

---
