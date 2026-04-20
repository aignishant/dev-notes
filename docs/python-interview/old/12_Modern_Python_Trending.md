# 12 — Modern Python & Trending Topics
## Questions to Show You're Current

---

## 12.1 Python 3.10–3.13 Features

### Q1: What's new in recent Python versions?

**Answer:**

```python
# ═══════════════════════════════════════
# Python 3.10: Structural Pattern Matching
# ═══════════════════════════════════════
def handle_response(response):
    match response:
        case {"status": 200, "data": data}:
            return process(data)
        case {"status": 404}:
            return "Not found"
        case {"status": status} if status >= 500:
            return f"Server error: {status}"
        case _:
            return "Unknown response"

# Union types with | syntax
def process(value: int | str | None) -> str:
    match value:
        case int():
            return f"Integer: {value}"
        case str():
            return f"String: {value}"
        case None:
            return "Nothing"

# ═══════════════════════════════════════
# Python 3.11: ExceptionGroup, faster Python
# ═══════════════════════════════════════
# ExceptionGroup — handle multiple exceptions simultaneously
try:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(risky_task_1())
        tg.create_task(risky_task_2())
except* ValueError as eg:
    for e in eg.exceptions:
        print(f"ValueError: {e}")
except* TypeError as eg:
    for e in eg.exceptions:
        print(f"TypeError: {e}")

# Better error messages with notes
try:
    raise ValueError("bad value")
except ValueError as e:
    e.add_note("This happened during data processing")
    e.add_note(f"Input was: {input_data}")
    raise

# tomllib — built-in TOML parser
import tomllib
with open("pyproject.toml", "rb") as f:
    config = tomllib.load(f)

# ═══════════════════════════════════════
# Python 3.12: Type parameter syntax, f-string improvements
# ═══════════════════════════════════════
# New type alias syntax
type Point = tuple[int, int]
type Matrix[T] = list[list[T]]

# Generic functions — inline TypeVar
def first[T](items: list[T]) -> T:
    return items[0]

# Generic classes
class Stack[T]:
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

# F-string improvements — any expression allowed
songs = ["Yesterday", "Hey Jude"]
print(f"Songs: {", ".join(songs)}")  # Quotes inside f-strings!

# Per-interpreter GIL (PEP 684)
# Each sub-interpreter gets its own GIL → true parallelism

# ═══════════════════════════════════════
# Python 3.13: Free-threaded Python (experimental)
# ═══════════════════════════════════════
"""
PEP 703: Making the GIL optional
  - Build Python with --disable-gil
  - True multi-threaded parallelism
  - Experimental in 3.13, expected stable in future versions
  - Impact: Threading becomes viable for CPU-bound tasks

JIT Compiler (PEP 744):
  - Experimental copy-and-patch JIT
  - Potential 5-10% speedup for hot loops
  - Foundation for future optimizations
"""
```

---

## 12.2 Rust + Python (PyO3)

### Q2: Why is Rust becoming important for Python developers?

**Answer:**

```python
"""
Why Rust + Python?
  - Performance-critical code in Rust, everything else in Python
  - Memory safety without garbage collection
  - Zero-cost abstractions
  - Growing ecosystem: polars, pydantic-core, ruff, uv

Popular Rust-powered Python tools:
  - Polars:       DataFrame library (10-100x faster than pandas)
  - Pydantic v2:  Core validation in Rust (5-50x faster)
  - Ruff:         Linter (10-100x faster than flake8)
  - uv:           Package installer (10-100x faster than pip)
  - tokenizers:   Hugging Face tokenizer library
  - orjson:       Fast JSON parsing
"""

# Polars — the modern alternative to pandas
import polars as pl

# Read data
df = pl.read_csv("data.csv")

# Lazy evaluation — build query plan, execute optimally
result = (
    df.lazy()
    .filter(pl.col("age") > 30)
    .group_by("department")
    .agg([
        pl.col("salary").mean().alias("avg_salary"),
        pl.col("name").count().alias("count"),
    ])
    .sort("avg_salary", descending=True)
    .collect()      # Execute the optimized query plan
)

# Why Polars over Pandas?
# - 10-100x faster for large datasets
# - Lazy evaluation with query optimization
# - True parallel execution
# - Consistent API (no SettingWithCopyWarning)
# - Better memory management
# - Expression-based API is more composable
```

---

## 12.3 AI Engineering Trends

### Q3: What AI engineering trends should a Python developer know?

**Answer:**

```python
"""
1. AI Agents & Agentic Workflows
   - Autonomous AI that uses tools, plans, and executes
   - Frameworks: LangGraph, CrewAI, AutoGen
   - Pattern: Plan → Act → Observe → Reflect → Repeat

2. RAG Evolution
   - Hybrid search (vector + keyword)
   - Agentic RAG (AI decides when/what to retrieve)
   - Graph RAG (knowledge graphs + vector search)
   - Multi-modal RAG (images, tables, code)

3. LLM Ops / ML Ops
   - Model serving: vLLM, TGI, Ollama
   - Evaluation: custom benchmarks, LLM-as-judge
   - Prompt management: version control for prompts
   - Guardrails: input/output filtering
   - Cost optimization: caching, smaller models

4. Fine-tuning Techniques
   - LoRA/QLoRA: Parameter-efficient fine-tuning
   - RLHF/DPO: Alignment training
   - Distillation: Smaller models from larger ones

5. Multi-modal AI
   - Vision-Language models (GPT-4V, Claude 3)
   - Audio processing (Whisper)
   - Code generation (specialized models)

6. Edge AI & On-Device
   - Quantization: INT8, INT4 models
   - ONNX Runtime: Cross-platform inference
   - Apple MLX, Google MediaPipe

7. Structured Output
   - Function calling / Tool use
   - JSON mode
   - Constrained generation
"""

# Prompt engineering best practices
"""
Techniques:
  1. Zero-shot:     Direct instruction
  2. Few-shot:      Provide examples
  3. Chain-of-thought: "Think step by step"
  4. Self-consistency: Multiple reasoning paths, majority vote
  5. ReAct:          Reason + Act (for agents)

System Prompt Template:
  You are a {role} that helps with {domain}.
  Your task is to {objective}.
  Follow these rules:
    1. {rule_1}
    2. {rule_2}
  Output format: {json/markdown/structured}

  Example:
  Input: {example_input}
  Output: {example_output}
"""
```

---

## 12.4 Security Best Practices

### Q4: Python security for senior developers.

```python
# ═══════════════════════════════════════
# Common vulnerabilities and fixes
# ═══════════════════════════════════════

# 1. SQL Injection
# ❌ NEVER use string formatting for SQL
query = f"SELECT * FROM users WHERE name = '{user_input}'"

# ✅ Use parameterized queries
cursor.execute("SELECT * FROM users WHERE name = %s", (user_input,))
# Or with SQLAlchemy:
session.query(User).filter(User.name == user_input)

# 2. Command Injection
# ❌ Never use shell=True with user input
import subprocess
subprocess.run(f"echo {user_input}", shell=True)  # DANGEROUS!

# ✅ Use list arguments
subprocess.run(["echo", user_input])

# 3. Secret management
# ❌ Never hardcode secrets
API_KEY = "sk-1234567890"

# ✅ Use environment variables
import os
API_KEY = os.environ["API_KEY"]

# Or use python-dotenv / pydantic-settings
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    api_key: str
    model_config = {"env_file": ".env"}

# 4. Input validation
# ✅ Always validate and sanitize input
from pydantic import BaseModel, Field
class UserInput(BaseModel):
    name: str = Field(max_length=100)
    email: EmailStr

# 5. Dependency security
# pip install pip-audit
# pip-audit                    # Check for known vulnerabilities
# pip install safety
# safety check                 # Another vulnerability scanner

# 6. HTTPS everywhere
# ❌ requests.get("http://api.example.com")
# ✅ requests.get("https://api.example.com", verify=True)

# 7. Hashing passwords
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash("my_password")
is_valid = pwd_context.verify("my_password", hashed)
# NEVER use md5 or sha256 for passwords!
```

---

## 12.5 Performance Optimization

### Q5: How to optimize Python application performance?

```python
# ═══════════════════════════════════════
# Profiling — measure before optimizing!
# ═══════════════════════════════════════

# 1. cProfile — function-level profiling
import cProfile
cProfile.run('my_function()', sort='cumulative')

# 2. line_profiler — line-by-line
# pip install line-profiler
# @profile
# def my_function():
#     ...
# kernprof -l -v script.py

# 3. memory_profiler
# pip install memory-profiler
# @profile
# def my_function():
#     ...
# python -m memory_profiler script.py

# 4. py-spy — sampling profiler (no code changes needed!)
# pip install py-spy
# py-spy top --pid 12345
# py-spy record -o profile.svg -- python script.py

# ═══════════════════════════════════════
# Common optimizations
# ═══════════════════════════════════════

# 1. Use built-in functions (implemented in C)
# ❌ sum = 0; for x in items: sum += x
# ✅ total = sum(items)

# 2. Use dict/set for lookups instead of list
# ❌ O(n): if item in large_list
# ✅ O(1): if item in large_set

# 3. Use generators for large data
# ❌ [x**2 for x in range(10_000_000)]  # 80MB in memory
# ✅ (x**2 for x in range(10_000_000))  # ~120 bytes

# 4. String concatenation
# ❌ result = ""; for s in strings: result += s
# ✅ result = "".join(strings)

# 5. Local variable access is faster than global
def fast_function():
    local_len = len  # Cache built-in as local
    for item in data:
        local_len(item)

# 6. Use __slots__ for many small objects
# 7. Use numpy for numerical computations
# 8. Use multiprocessing for CPU-bound tasks
# 9. Use connection pooling for databases
# 10. Cache expensive computations (functools.lru_cache)
```

---

## 12.6 Behavioral & Soft Skills

### Q6: Common behavioral questions for senior Python developers.

```
Q: Tell me about a time you improved system performance.
Framework: STAR (Situation, Task, Action, Result)
  - Describe the slow system (metrics)
  - What you investigated (profiling)
  - What you changed (specific optimizations)
  - Quantified improvement (X% faster, Y% less memory)

Q: How do you handle disagreements about technical decisions?
  - Listen first, understand their perspective
  - Present data/benchmarks, not opinions
  - Prototype if needed to compare approaches
  - Disagree and commit — once decided, support the decision

Q: How do you mentor junior developers?
  - Code reviews with explanations, not just corrections
  - Pair programming sessions
  - Share learning resources and context
  - Give gradually increasing responsibility

Q: Describe your approach to debugging a production issue.
  - Stay calm, gather information (logs, metrics, alerts)
  - Reproduce the issue (if possible)
  - Narrow down: recent changes? specific endpoint? load-related?
  - Fix → test → deploy → postmortem

Q: How do you stay current with Python and tech?
  - Python weekly newsletters, PEP tracking
  - Open source contributions
  - Personal AI projects (show your passion!)
  - Conference talks (PyCon, EuroPython)
  - Community engagement (Python Discord, Reddit)

Key Points for 9+ Years Experience:
  - Talk about ARCHITECTURE decisions, not just coding
  - Discuss TRADEOFFS you've evaluated
  - Show LEADERSHIP in technical decisions
  - Demonstrate MENTORING and knowledge sharing
  - Highlight BUSINESS IMPACT of your work
```

---

## 12.7 Quick Reference — Cheat Sheet

```python
# ═══════════════════════════════════════
# Most-asked one-liners
# ═══════════════════════════════════════

# Reverse a string
s[::-1]

# Flatten nested list
[x for sub in nested for x in sub]

# Remove duplicates preserving order
list(dict.fromkeys(items))

# Transpose a matrix
list(zip(*matrix))

# Check palindrome
s == s[::-1]

# Fibonacci generator
def fib():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Merge two dicts
merged = {**dict1, **dict2}       # Python 3.5+
merged = dict1 | dict2             # Python 3.9+

# Find most common element
from collections import Counter
Counter(items).most_common(1)[0][0]

# Convert list of tuples to dict
dict([(1,'a'), (2,'b')])

# Chunk a list
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

# Time a function
import time
start = time.perf_counter()
result = my_function()
print(f"{time.perf_counter() - start:.4f}s")

# Read file as string
content = Path("file.txt").read_text()

# Pretty print
from pprint import pprint
pprint(complex_dict, width=80, depth=3)
```

---

**You're ready. Go ace that interview! 🐍🚀**
