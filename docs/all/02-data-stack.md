# Module 2 — The Data Stack (NumPy, Pandas, Polars, Visualization)

> **Bible Module 2 of 14.** Self-contained. Written for **NumPy 2.x, Pandas 2.2+/3.0, Polars 1.x, Matplotlib 3.10+**. All code is runnable as-is. Assumes you've completed Module 1.

---

## 0. Goal, reader, and how to use this module

**Goal.** After this module you can: load any tabular dataset; clean it; reshape it; aggregate it; visualize it; and reason about *why* one approach is 100× faster than another. You'll know when to reach for NumPy vs Pandas vs Polars vs DuckDB. This is the foundation for every ML/DL/LLM module that follows.

**Target reader.** Completed Module 1, or already comfortable with Python. No prior NumPy/Pandas experience required.

**How to use it.** Same as Module 1 — read top to bottom, type every code sample, do all 36 problems before reading solutions, keep §19 cheatsheet open forever.

**Prerequisites.** Module 1.
**Next steps after this module.** Module 3 (Databases & SQLAlchemy) and Module 7 (Classical ML) — both lean on this heavily.

---

## 1. The data stack landscape

Before any code, the decision tree. Wrong tool choice will cost you 10–100× performance or weeks of refactoring.

| Use case | Right tool |
|---|---|
| Numerical arrays, math, linear algebra, ML feature matrices | **NumPy** |
| Tabular data, < 10M rows, mixed types, exploratory analysis | **Pandas** |
| Tabular data, > 10M rows, performance-critical, production ETL | **Polars** |
| Querying parquet files / large local data with SQL | **DuckDB** |
| Distributed (multi-machine) tabular data | **PySpark** or **Ray Datasets** |
| Streaming columnar data between systems | **Arrow** |

**The one-line summary.**
- NumPy: arrays of numbers.
- Pandas: spreadsheets with code.
- Polars: pandas redesigned for speed.
- Arrow / Parquet: the storage formats they all share.

You will use NumPy in **every** ML module. You'll use Pandas constantly in analysis and feature engineering. Polars is the production choice when datasets get bigger or the bill matters.

---

## 2. NumPy — arrays, dtypes, broadcasting

### 2.1 Why NumPy exists

A Python list of 1,000,000 floats: ~57 MB, scattered across the heap, each operation interpreted in CPython.
A NumPy array of 1,000,000 float64s: 8 MB contiguous, math runs in compiled C with SIMD instructions, ~100× faster.

NumPy is the substrate the entire scientific Python stack sits on (pandas, scikit-learn, PyTorch tensors all interoperate with NumPy arrays).

### 2.2 Creating arrays

```python
import numpy as np

# from a list
a = np.array([1, 2, 3])               # dtype inferred: int64
b = np.array([1.0, 2.0, 3.0])          # dtype: float64
c = np.array([1, 2, 3], dtype=np.float32)  # explicit dtype

# common factories
np.zeros((3, 4))                       # 3x4 of 0.0
np.ones((2, 3))
np.full((2, 2), 7)                     # filled with 7
np.arange(0, 10, 2)                    # [0,2,4,6,8] — like range
np.linspace(0, 1, 5)                   # [0., 0.25, 0.5, 0.75, 1.] — N evenly spaced
np.eye(3)                              # 3x3 identity
np.random.default_rng(42).normal(0, 1, size=(2, 3))  # gaussian — modern RNG API
```

**Use the modern RNG.** `np.random.default_rng(seed)` gives you a `Generator`. The legacy `np.random.rand()` etc. is global state — avoid in new code.

### 2.3 dtype matters more than you think

```python
a = np.array([1, 2, 3], dtype=np.int8)
print(a + 200)      # [-55, -54, -53] — wraps! int8 maxes at 127

# cast explicitly
b = a.astype(np.int32)
```

**Memory math.** A 1B-row float64 array = 8 GB. Same array as float32 = 4 GB. For ML, float32 is usually sufficient and halves memory + speeds up GPU ops.

| dtype | Bytes | Use when |
|---|---|---|
| `bool` | 1 | masks, flags |
| `int8` / `uint8` | 1 | image pixels, small categoricals |
| `int32` / `int64` | 4 / 8 | counts, IDs |
| `float32` | 4 | ML training (default) |
| `float64` | 8 | scientific computing, finance |
| `complex128` | 16 | signal processing |

### 2.4 Shape, axes, and the mental model

An array has a `shape` tuple. Axis numbers go from outermost to innermost.

```python
a = np.zeros((2, 3, 4))        # 3-D: 2 "sheets" of 3 rows × 4 cols
print(a.shape)                  # (2, 3, 4)
print(a.ndim)                   # 3
print(a.size)                   # 24
print(a.dtype)                  # float64
```

For a 2-D array:
- **axis 0** = rows (going down)
- **axis 1** = columns (going across)

```python
m = np.array([[1, 2, 3],
              [4, 5, 6]])
m.sum()              # 21 — over everything
m.sum(axis=0)        # [5, 7, 9] — collapse rows, one value per column
m.sum(axis=1)        # [6, 15] — collapse cols, one value per row
m.sum(axis=0, keepdims=True)  # [[5,7,9]] — preserve the dimension (useful for broadcasting back)
```

**Memorize this:** `axis=k` means "collapse along axis k, leaving the other axes." This is the source of 50% of NumPy/Pandas confusion.

### 2.5 Indexing and slicing

```python
a = np.arange(20).reshape(4, 5)
# [[ 0  1  2  3  4]
#  [ 5  6  7  8  9]
#  [10 11 12 13 14]
#  [15 16 17 18 19]]

a[1, 2]              # 7 — single element
a[1]                 # [5,6,7,8,9] — entire row 1
a[:, 2]              # [2,7,12,17] — entire column 2
a[1:3, 1:4]          # rows 1-2, cols 1-3
a[::2]               # every other row
a[:, ::-1]           # all cols reversed (useful for image flips)
```

**Critical:** slicing returns a *view* (shares memory). Mutating the slice mutates the original.

```python
v = a[1:3, 1:4]
v[0, 0] = -1
print(a[1, 1])       # -1  ← modified!

# to copy explicitly:
v = a[1:3, 1:4].copy()
```

### 2.6 Boolean and fancy indexing

```python
a = np.array([1, 2, 3, 4, 5])
mask = a > 2                # [False, False, True, True, True]
a[mask]                     # [3, 4, 5]
a[a > 2] = 0                # in-place: [1, 2, 0, 0, 0]

# fancy (integer) indexing — copies, not view
idx = np.array([0, 2, 4])
a[idx]                      # picks those positions

# 2-D fancy
m = np.arange(20).reshape(4, 5)
m[[0, 2], [1, 3]]           # [1, 13] — pairs (0,1) and (2,3)
m[[0, 2]]                   # rows 0 and 2
```

### 2.7 Broadcasting — the most powerful feature

Broadcasting lets arrays of different shapes interact, virtually replicating the smaller along missing axes — without actually copying memory.

**The rules.** When operating on two arrays, NumPy compares shapes element-wise from the *trailing* dimension. They are compatible when:
1. Dimensions are equal, or
2. One of them is 1.

```python
a = np.arange(6).reshape(2, 3)        # shape (2, 3)
b = np.array([10, 20, 30])             # shape (3,)
a + b
# [[10, 21, 32],
#  [13, 24, 35]]   — b is broadcast across rows

# add a column vector
col = np.array([[100], [200]])         # shape (2, 1)
a + col
# [[100, 101, 102],
#  [203, 204, 205]]

# centering data — classic ML pattern
X = np.random.default_rng(0).normal(0, 1, size=(100, 5))
X_centered = X - X.mean(axis=0)        # subtract per-column mean (shape (5,) broadcasts over rows)
```

**Why it matters.** Broadcasting eliminates loops. A `for` loop over rows in Python is ~100× slower than the equivalent broadcast operation.

### 2.8 Vectorization — the rule

**Replace explicit loops with array operations whenever possible.**

```python
# slow (Python-loop)
result = np.zeros(1_000_000)
for i in range(1_000_000):
    result[i] = a[i] ** 2 + 3*a[i] + 1

# fast (vectorized) — same result, ~100× faster
result = a**2 + 3*a + 1
```

When you can't vectorize directly (e.g. branching logic), use `np.where`, `np.select`, or `np.vectorize` (the last is convenient but not actually fast — it's still a Python loop under the hood).

```python
# branching: where(condition, value_if_true, value_if_false)
np.where(a > 0, np.sqrt(a), 0)

# multi-branch
conditions = [a < 0, a == 0, a > 0]
choices = [-1, 0, 1]
np.select(conditions, choices)
```

---

## 3. NumPy — advanced indexing, axis ops, linear algebra

### 3.1 Reshape, transpose, concat, split

```python
a = np.arange(12)
a.reshape(3, 4)               # 3x4
a.reshape(3, -1)              # -1 means "infer this dimension"
a.reshape(-1, 1)              # column vector

m = np.arange(6).reshape(2, 3)
m.T                            # transpose, shape (3, 2)
m.transpose()                  # same as .T for 2-D
m.transpose(1, 0)              # explicit axis order — needed for 3-D+

np.concatenate([m, m], axis=0)         # stack vertically
np.concatenate([m, m], axis=1)         # stack horizontally
np.vstack([m, m])              # shorthand for axis=0
np.hstack([m, m])              # shorthand for axis=1
np.stack([m, m], axis=0)       # creates a NEW axis (shape becomes (2,2,3))

np.split(a, 3)                 # split into 3 equal pieces
```

### 3.2 Aggregations and reductions

```python
a = np.arange(12).reshape(3, 4)
a.sum() / a.mean() / a.std() / a.var() / a.min() / a.max() / a.prod()
a.argmin() / a.argmax()                # index of min/max (flattened)
a.argmin(axis=0)                        # per-column

# numerically stable / NaN-aware
np.nansum(a)        # ignores NaN
np.nanmean(a)
np.percentile(a, [50, 95, 99])         # p50, p95, p99
```

### 3.3 Sorting and searching

```python
a = np.array([3, 1, 4, 1, 5, 9, 2, 6])
np.sort(a)                  # [1,1,2,3,4,5,6,9]  copy
a.sort()                    # in-place
np.argsort(a)               # indices that would sort

# find insertion points (for sorted array)
np.searchsorted(np.array([1,3,5,7]), 4)   # 2 — would go at index 2

# unique values + counts
vals, counts = np.unique([1,2,2,3,3,3], return_counts=True)
# vals=[1,2,3]  counts=[1,2,3]
```

### 3.4 Linear algebra (the bits ML actually uses)

```python
A = np.array([[1, 2], [3, 4]])
b = np.array([5, 6])

A @ b               # matrix-vector product — preferred over np.dot
A @ A               # matrix-matrix product
A.T                 # transpose
np.linalg.inv(A)    # inverse — rarely needed; usually solve a system instead
np.linalg.solve(A, b)   # solves Ax = b — much more numerically stable than A^-1 @ b

# eigendecomposition (used in PCA)
vals, vecs = np.linalg.eig(A)

# SVD — the bedrock of PCA, recommender systems, latent factors
U, S, Vt = np.linalg.svd(A)

# norms
np.linalg.norm(b)               # L2 norm by default
np.linalg.norm(b, ord=1)        # L1
np.linalg.norm(A, ord='fro')    # Frobenius (matrix L2)
```

**Production rule:** Never compute `inv(A) @ b`. Always use `solve(A, b)`. Inverses are numerically unstable and ~3× slower.

### 3.5 Random — the modern API

```python
rng = np.random.default_rng(seed=42)   # reproducible
rng.normal(0, 1, size=1000)            # gaussian
rng.uniform(-1, 1, size=(10, 10))
rng.integers(0, 100, size=5)           # ints in [0, 100)
rng.choice([1, 2, 3], size=10, p=[0.5, 0.3, 0.2])  # weighted
rng.permutation(10)                     # shuffled 0..9
rng.shuffle(arr)                        # in-place
```

**Always seed in tests, ML training, and anything reproducible.** Never seed in production cryptography (use `secrets`).

---

## 4. Pandas — Series and DataFrame fundamentals

### 4.1 The two structures

- **`Series`** — a 1-D labeled array (basically a NumPy array + an index).
- **`DataFrame`** — a 2-D table where each column is a Series and rows have an index.

```python
import pandas as pd

s = pd.Series([10, 20, 30], index=["a", "b", "c"], name="score")
# a    10
# b    20
# c    30
# Name: score, dtype: int64

df = pd.DataFrame({
    "name":  ["Ada", "Bob", "Cal"],
    "age":   [30, 25, 40],
    "score": [88.5, 72.0, 95.5],
})
#   name  age  score
# 0  Ada   30   88.5
# 1  Bob   25   72.0
# 2  Cal   40   95.5
```

### 4.2 Reading and writing data

```python
# CSV
df = pd.read_csv("users.csv")
df = pd.read_csv("users.csv", parse_dates=["created_at"], dtype={"id": "int32"})
df.to_csv("out.csv", index=False)

# Parquet — preferred for any data > a few MB
df = pd.read_parquet("users.parquet")
df.to_parquet("out.parquet", compression="zstd")

# JSON / JSON Lines
df = pd.read_json("data.jsonl", lines=True)

# Excel
df = pd.read_excel("file.xlsx", sheet_name="Sheet1")

# SQL
import sqlalchemy
engine = sqlalchemy.create_engine("postgresql://...")
df = pd.read_sql("SELECT * FROM users WHERE active = true", engine)
```

**Production rule.** Use parquet, never CSV, for anything that lives more than 10 minutes. CSV has no schema, no compression, ambiguous types, and is 5–10× slower to read.

### 4.3 First-look operations

When you receive a new DataFrame, run these five lines:

```python
df.shape                # (n_rows, n_cols)
df.dtypes               # types per column
df.head(3)              # first rows
df.describe(include="all")   # numeric stats + value_counts for objects
df.isna().sum()         # missing values per column
```

### 4.4 Indexing — `.loc`, `.iloc`, and the rules

There are exactly three ways to select. Memorize them.

| Syntax | Meaning |
|---|---|
| `df["col"]` | Select column by label (returns Series) |
| `df.loc[row_label, col_label]` | Label-based |
| `df.iloc[row_int, col_int]` | Position-based |

```python
df.loc[0]                          # row with index label 0
df.loc[0, "name"]                  # one cell
df.loc[:, "name"]                  # entire column
df.loc[df["age"] > 25, ["name", "score"]]    # boolean + columns

df.iloc[0]                         # first row regardless of index label
df.iloc[0:2, 0:2]                  # first 2 rows × first 2 cols
df.iloc[-1]                        # last row
```

**The single biggest pandas trap:** `df["col"][0]` for assignment is **chained indexing**. It may modify a copy or a view depending on phase of the moon.

```python
# DON'T
df[df["age"] > 25]["score"] = 0    # SettingWithCopyWarning, may not work

# DO
df.loc[df["age"] > 25, "score"] = 0
```

Always use `.loc` for assignment.

### 4.5 Adding, dropping, renaming columns

```python
df["double_age"] = df["age"] * 2                    # new column
df = df.assign(triple_age=lambda d: d["age"] * 3)   # chainable

df = df.drop(columns=["double_age"])
df = df.drop(index=[0, 1])                          # drop rows by label

df = df.rename(columns={"name": "full_name"})
```

### 4.6 Categorical dtype — the memory win

```python
# 1M-row column with 5 unique values — stored as 1M strings = MB of waste
df["status"] = df["status"].astype("category")
# now stored as 1M int8s + a tiny lookup table — ~95% memory reduction
```

Always convert low-cardinality string columns to category before doing groupby on them — it's not just memory, groupby is also faster.

---

## 5. Pandas — selection, filtering, missing data

### 5.1 Boolean filtering

```python
df[df["age"] > 25]
df[(df["age"] > 25) & (df["score"] > 80)]   # & not `and`, parens required
df[df["name"].isin(["Ada", "Bob"])]
df[df["name"].str.startswith("A")]
df[~df["score"].isna()]                      # negate with ~
df.query("age > 25 and score > 80")          # SQL-ish, sometimes cleaner
```

**The `&` / `|` / `~` rule.** Pandas overloads bitwise operators because Python's `and`/`or` aren't overridable. Always use `&`, `|`, `~`, and parenthesize.

### 5.2 Missing data — NaN, NA, NaT

Pandas has three nulls: `np.nan` (float), `pd.NaT` (datetime), and `pd.NA` (the new nullable null). Check with:

```python
df.isna()                       # boolean DataFrame
df["x"].isna().sum()            # count missing in one column
df.dropna()                     # drop rows with any NaN
df.dropna(subset=["email"])     # only check this column
df.fillna(0)                    # fill with constant
df["x"].fillna(df["x"].median())     # fill with median
df.fillna(method="ffill")       # forward-fill (last good value)
df.interpolate()                # linear interpolation between valid points
```

**Distinction.** `dropna` and `fillna` are nearly always the right tool. **Never** silently `df.fillna(0)` numeric columns in production without thinking — zero is a *value*, and it can poison downstream stats. Document why you chose your fill strategy.

### 5.3 Replacing, mapping, applying

```python
df["status"] = df["status"].replace({"old": "new", "x": "y"})
df["grade"] = df["score"].map(lambda s: "A" if s >= 90 else "B")  # element-wise
df["full"] = df.apply(lambda r: f"{r['name']} ({r['age']})", axis=1)  # row-wise
```

**Performance hierarchy** (fastest → slowest):
1. Vectorized: `df["x"] * 2`, `df["x"].str.lower()`
2. `.map()` with a dict (very fast for replacement)
3. `.apply()` axis=0 on Series
4. `.apply()` axis=1 on DataFrame (Python loop in disguise — slow)
5. `for row in df.iterrows():` (almost always wrong)

If you find yourself reaching for `.apply(axis=1)`, ask whether it can be vectorized first.

---

## 6. Pandas — groupby, agg, transform, apply

This is the heart of pandas. If you understand groupby deeply, you understand pandas.

### 6.1 The split-apply-combine model

```
groupby = SPLIT data into groups based on key(s)
        + APPLY a function to each group
        + COMBINE results back into a structure
```

### 6.2 Aggregations

```python
df.groupby("dept")["salary"].mean()           # one stat per group
df.groupby("dept")["salary"].agg(["mean", "median", "std"])
df.groupby(["dept", "level"])["salary"].sum()    # multi-key

# named aggregations — clean output column names
df.groupby("dept").agg(
    avg_salary=("salary", "mean"),
    n_people  =("salary", "count"),
    top_score =("score",  "max"),
)
```

### 6.3 Transform vs aggregate vs apply

These three look similar and are wildly different. Memorize the distinction.

| Method | Returns | Use for |
|---|---|---|
| `.agg()` | One row per group | Summaries |
| `.transform()` | Same shape as input | Per-group features |
| `.apply()` | Anything | Custom logic |

```python
# transform — adds a per-group column without collapsing rows
df["dept_avg"] = df.groupby("dept")["salary"].transform("mean")
df["pct_of_dept"] = df["salary"] / df["dept_avg"]

# z-score within each group
df["salary_z"] = df.groupby("dept")["salary"].transform(
    lambda s: (s - s.mean()) / s.std()
)

# apply — fully custom; slower
def top2(group):
    return group.nlargest(2, "salary")
df.groupby("dept").apply(top2, include_groups=False)
```

### 6.4 Windowing functions (rolling, expanding, ewm)

```python
df["rolling_mean"] = df["price"].rolling(window=7).mean()    # 7-period MA
df["rolling_max"]  = df["price"].rolling(7).max()
df["expanding"]    = df["price"].expanding().mean()           # cumulative
df["ewm"]          = df["price"].ewm(span=5).mean()           # exp-weighted

# rolling per group
df["rolling_in_dept"] = df.groupby("dept")["salary"].transform(
    lambda s: s.rolling(3, min_periods=1).mean()
)
```

---

## 7. Pandas — merging, joining, reshaping

### 7.1 Merging (joins)

```python
users  = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
orders = pd.DataFrame({"user_id": [1, 1, 2, 4], "amount": [10, 20, 30, 40]})

# inner — only matching keys (default)
pd.merge(users, orders, left_on="id", right_on="user_id")

# left — all of users, matching orders
pd.merge(users, orders, left_on="id", right_on="user_id", how="left")

# outer — all keys from both
pd.merge(users, orders, left_on="id", right_on="user_id", how="outer", indicator=True)

# many-to-many: use validate to catch bugs early
pd.merge(a, b, on="key", validate="one_to_one")     # raises if violated
```

**The `validate` parameter is gold.** It catches join-cardinality bugs (the silent doubler) before they pollute your analysis.

### 7.2 Concat — stacking

```python
pd.concat([df1, df2], axis=0)              # stack rows (UNION ALL-ish)
pd.concat([df1, df2], axis=1)              # stack columns (must align indexes)
pd.concat([df1, df2], ignore_index=True)   # reset index 0..n
```

### 7.3 Pivot — long ↔ wide

```python
# long-format input
long = pd.DataFrame({
    "date":   ["2026-01", "2026-01", "2026-02", "2026-02"],
    "metric": ["sales", "users", "sales", "users"],
    "value":  [100, 50, 120, 55],
})

wide = long.pivot(index="date", columns="metric", values="value")
#          sales  users
# date
# 2026-01    100     50
# 2026-02    120     55

# back to long
back = wide.reset_index().melt(id_vars="date", var_name="metric", value_name="value")
```

### 7.4 `pivot_table` — the aggregating cousin

`pivot` errors on duplicates; `pivot_table` aggregates them.

```python
pd.pivot_table(
    df,
    index="dept",
    columns="level",
    values="salary",
    aggfunc=["mean", "count"],
    margins=True,         # adds row/col totals
)
```

### 7.5 Stack / unstack — for hierarchical indexes

```python
wide.stack()     # column level → row level (wide → long)
wide.unstack()   # row level → column level (long → wide)
```

`stack`/`unstack` are pivot for MultiIndex DataFrames. You'll meet them whenever you `groupby` on multiple keys.


---

## 8. Pandas — time series

Time series is where pandas truly shines. Every concept here will return in MLOps and finance work.

### 8.1 Datetime essentials

```python
import pandas as pd

# always parse on read
df = pd.read_csv("events.csv", parse_dates=["timestamp"])

# convert if you missed it
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

# always store UTC. Convert for display only.
df["local"] = df["timestamp"].dt.tz_convert("America/New_York")

# the .dt accessor — your gateway to date components
df["year"]      = df["timestamp"].dt.year
df["month"]     = df["timestamp"].dt.month
df["weekday"]   = df["timestamp"].dt.day_name()
df["hour"]      = df["timestamp"].dt.hour
df["is_weekend"] = df["timestamp"].dt.dayofweek >= 5
```

### 8.2 DatetimeIndex — set it as the index for time ops

```python
df = df.set_index("timestamp").sort_index()

# slice by time strings
df.loc["2026-01"]                          # all of January 2026
df.loc["2026-01-15":"2026-01-20"]
df.loc["2026-01-15 09:00":"2026-01-15 17:00"]

# pick first/last in window
df.first("7D")         # first 7 days from earliest
df.last("30D")         # last 30 days
```

### 8.3 Resample — the time-aware groupby

```python
# downsample: 1-minute data → 1-hour bars
hourly = df["price"].resample("1h").agg(["first", "max", "min", "last"])

# upsample with fill
df.resample("1min").ffill()                 # forward-fill missing minutes

# rolling time window (different from .rolling(N))
df["price"].rolling("7D").mean()            # 7-day rolling mean
```

**Frequency strings you'll use:** `"D"` day, `"h"` hour, `"min"` minute, `"s"` second, `"W"` week, `"ME"` month-end, `"QE"` quarter-end, `"YE"` year-end. (Pandas 2.2+ uses lowercase + suffixes; the old `"M"` is deprecated.)

### 8.4 Shift, diff, pct_change

```python
df["yesterday"]   = df["price"].shift(1)        # value from 1 step ago
df["delta"]       = df["price"].diff()          # difference vs previous
df["pct"]         = df["price"].pct_change()    # ratio change
df["lag_7d"]      = df["price"].shift(7, freq="D")  # time-aware shift
```

These four operations are the basis of nearly every time-series feature in ML.

---

## 9. Pandas — performance and memory

### 9.1 The performance reality

Pandas is a Python library wrapping NumPy. Most of its speed comes from staying in vectorized NumPy ops. The moment you drop to Python-loop level, you lose 100×.

| Operation on 1M rows | Approx time |
|---|---|
| Vectorized: `df["x"] * 2` | ~5 ms |
| `.map(dict)` | ~30 ms |
| `.apply(axis=0)` on a Series | ~100 ms |
| `.apply(axis=1)` on DataFrame | ~3,000 ms |
| `for _, row in df.iterrows():` | ~30,000 ms |
| `for row in df.itertuples():` | ~1,500 ms (10× faster than iterrows, still slow) |

**Rule:** if your function uses pandas/numpy primitives, vectorize. If it truly needs row-by-row Python logic, consider whether you actually need pandas at all (often raw NumPy or Polars is better).

### 9.2 Memory profiling

```python
df.memory_usage(deep=True).sum() / 1e6      # MB used (deep=True for object cols)
df.info(memory_usage="deep")                 # per-column breakdown
```

### 9.3 Memory wins, in order of impact

1. **Read with `dtype=`** to avoid wide defaults.
2. **Use categories** for repeated strings.
3. **Use `Int32` / `Int8` / `Float32`** when range allows (the capital-`I` versions are nullable).
4. **Read columns you actually need:** `pd.read_parquet(path, columns=["a","b"])`.
5. **Read in chunks:** `pd.read_csv(path, chunksize=100_000)` for files larger than RAM.
6. **Switch to Polars or DuckDB** for >10M rows or constant memory pressure.

### 9.4 The `query` and `eval` tricks

For very large frames, `df.query()` and `df.eval()` use a numexpr backend that can be 2–4× faster than the equivalent boolean expression *and* avoids creating intermediate arrays:

```python
df.query("age > 25 and score > 80")          # fast for big frames
df.eval("bonus = score * 0.1")                # in-place column add, fast
```

For small frames, the overhead isn't worth it.

---

## 10. Polars — when and why

Polars is a younger DataFrame library written in Rust. It is **dramatically faster** than pandas (often 5–30×) and has a saner API. In 2026, it's the production choice for any new ETL pipeline.

### 10.1 The mental model differences

| | Pandas | Polars |
|---|---|---|
| Underlying engine | NumPy (Python) | Apache Arrow + Rust |
| Index | Yes (often confusing) | No — rows are just rows |
| Mutation | In-place common | Always returns a new frame |
| Lazy execution | No | Yes (`scan_*` + `collect`) |
| Multi-core | Limited | Default |
| Null handling | NaN/NaT/NA mess | One unified `null` |
| Strings | Slow object dtype | Fast UTF-8, native |

### 10.2 The basics — eager API

```python
import polars as pl

df = pl.DataFrame({
    "name":  ["Ada", "Bob", "Cal", "Dan"],
    "dept":  ["eng", "eng", "sales", "sales"],
    "salary": [100, 120, 90, 95],
})

# columns are referenced via pl.col(...)
df.filter(pl.col("salary") > 95)
df.select("name", "dept")
df.with_columns(
    salary_k = pl.col("salary") * 1000,
    high     = pl.col("salary") > 100,
)
df.group_by("dept").agg(
    pl.col("salary").mean().alias("avg"),
    pl.col("salary").max().alias("max"),
    pl.len().alias("n"),
)
```

**The Polars idiom.** Build expressions with `pl.col("x")`, chain them with `.with_columns(...)`, `.filter(...)`, `.group_by(...).agg(...)`. The query is optimized end-to-end before execution.

### 10.3 Lazy execution — the killer feature

```python
# scan_* gives a LazyFrame — nothing is read yet
q = (
    pl.scan_parquet("events_*.parquet")          # globs supported
      .filter(pl.col("event_type") == "purchase")
      .group_by("user_id")
      .agg(pl.col("amount").sum().alias("total"))
      .filter(pl.col("total") > 1000)
      .sort("total", descending=True)
      .limit(100)
)

print(q.explain())          # see the optimized plan
result = q.collect()        # NOW it runs — fully optimized, parallel
```

The lazy planner does projection pushdown (read only needed columns), predicate pushdown (filter while reading), and parallel execution. On a 50GB parquet dataset, this is often 50–100× faster than the eager pandas equivalent.

### 10.4 When to use which

| Situation | Choice |
|---|---|
| Quick analysis, < 1M rows, lots of plotting | Pandas — ecosystem still wins |
| Production ETL, > 5M rows, performance matters | **Polars** |
| ML feature engineering for training | Either; Polars if dataset is large |
| Working with someone else's pandas codebase | Pandas |
| New project today, given a free choice | **Polars** |

---

## 11. Visualization — matplotlib mental model

Matplotlib is the substrate. Seaborn and Plotly sit on top of it (or alongside it). Learn matplotlib's mental model once, you can navigate any plot in any library.

### 11.1 Figure and Axes — the only concept you need

A **Figure** is the outer canvas. **Axes** are the plotting areas inside it. Everything you draw goes onto an Axes.

```python
import matplotlib.pyplot as plt
import numpy as np

# the explicit, "object-oriented" API — what you should always use
fig, ax = plt.subplots(figsize=(8, 5))
x = np.linspace(0, 10, 100)
ax.plot(x, np.sin(x), label="sin")
ax.plot(x, np.cos(x), label="cos", linestyle="--")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_title("Trig functions")
ax.legend()
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig("trig.png", dpi=150)
plt.show()
```

**Avoid the `pyplot` "implicit" API** (`plt.plot(...)` etc.) for anything beyond a one-liner. The explicit `fig, ax = ...` style is what production code uses — it scales to subplots without rewriting.

### 11.2 Subplots

```python
fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(10, 6), sharex=True)
axes[0, 0].plot(x, np.sin(x));  axes[0, 0].set_title("sin")
axes[0, 1].plot(x, np.cos(x));  axes[0, 1].set_title("cos")
axes[1, 0].hist(np.random.randn(1000), bins=30)
axes[1, 1].scatter(np.random.randn(100), np.random.randn(100))
fig.tight_layout()
```

### 11.3 The plot types you'll use 95% of the time

```python
ax.plot(x, y)                        # line
ax.scatter(x, y, c=labels, s=sizes, alpha=0.5)
ax.bar(categories, values)
ax.barh(categories, values)          # horizontal — better for long labels
ax.hist(data, bins=30)
ax.boxplot(arrays_list, labels=names)
ax.imshow(matrix, cmap="viridis")    # heatmap / image
ax.errorbar(x, y, yerr=err)
ax.fill_between(x, y_low, y_high, alpha=0.3)
```

### 11.4 Style essentials

```python
plt.rcParams["figure.dpi"] = 120          # crisper inline plots
plt.rcParams["axes.spines.top"] = False    # remove top border
plt.rcParams["axes.spines.right"] = False
plt.style.use("seaborn-v0_8-whitegrid")    # a nice default
```

**Color principles:** sequential data → `viridis`; diverging (e.g. correlations) → `RdBu`; categorical → `tab10` (default). Never use jet/rainbow — they distort perceived data.

---

## 12. Visualization — seaborn for stats, plotly for interactive

### 12.1 Seaborn — statistical visualization in one line

```python
import seaborn as sns

# distributions
sns.histplot(df, x="score", hue="dept", kde=True)
sns.boxplot(df, x="dept", y="salary")
sns.violinplot(df, x="dept", y="salary")

# relationships
sns.scatterplot(df, x="age", y="salary", hue="dept", size="score")
sns.regplot(df, x="age", y="salary")           # scatter + regression line
sns.lmplot(df, x="age", y="salary", col="dept")  # facet by column

# correlations
sns.heatmap(df.corr(numeric_only=True), annot=True, cmap="RdBu", center=0)

# pair plot — every numeric column vs every other (great EDA)
sns.pairplot(df, hue="dept")
```

Seaborn is built on matplotlib. Customize the underlying axes:

```python
ax = sns.boxplot(df, x="dept", y="salary")
ax.set_title("Salary by department")
ax.figure.savefig("box.png")
```

### 12.2 Plotly — interactive (and what to use in dashboards)

```python
import plotly.express as px

fig = px.scatter(df, x="age", y="salary", color="dept",
                 hover_data=["name"], size="score")
fig.update_layout(title="Salaries")
fig.write_html("scatter.html")
```

Plotly figures are interactive (zoom, hover, toggle series). In Streamlit, Dash, or notebooks, they're a step up. For a static report or paper, stick with matplotlib/seaborn.

### 12.3 The visualization decision tree

| Goal | Tool |
|---|---|
| Static report / paper | matplotlib (or seaborn) |
| Quick EDA on a DataFrame | seaborn |
| Interactive in a notebook | plotly |
| Embedded in a web app / dashboard | plotly + Dash, or Streamlit |
| Geospatial maps | plotly, folium |
| Real-time updating plot | streamlit + plotly |

---

## 13. I/O at scale — Parquet, Arrow, DuckDB

### 13.1 Parquet — the format you should default to

Parquet is a columnar, compressed, self-describing format. Pros vs CSV:

- **5–10× smaller** on disk (column compression).
- **5–50× faster to read.** You only read columns you need.
- **Schema-aware** — types are preserved exactly.
- **Predicate pushdown** — readers can skip whole row groups.

```python
df.to_parquet("data.parquet", compression="zstd", index=False)
df = pd.read_parquet("data.parquet", columns=["a", "b"])    # only reads those cols
```

### 13.2 Apache Arrow — the in-memory format

Arrow is the language-agnostic columnar memory format. Pandas, Polars, DuckDB, Spark, BigQuery clients can all share Arrow tables without copying. This is why polars + duckdb interop is free.

### 13.3 DuckDB — SQL on local files

DuckDB is "SQLite for analytics." It runs queries directly on parquet/csv/JSON without loading them into pandas first.

```python
import duckdb

# query a parquet file directly
result = duckdb.sql("""
    SELECT user_id, SUM(amount) AS total
    FROM 'events_*.parquet'
    WHERE event_type = 'purchase'
    GROUP BY user_id
    HAVING total > 1000
    ORDER BY total DESC
    LIMIT 100
""").df()                                # convert to pandas

# or back to polars
result_pl = duckdb.sql("...").pl()
```

For exploratory analytics on files larger than RAM, this is often the fastest, simplest tool. Add it to your toolbelt.

---

## 14. DataFrame anti-patterns — what NOT to do

| Anti-pattern | Right way |
|---|---|
| `df["col"][df["x"]>0] = 1` (chained) | `df.loc[df["x"]>0, "col"] = 1` |
| `for _, row in df.iterrows():` | Vectorize, or use `df.to_dict("records")` if truly needed |
| Loading 50GB CSV into pandas | Polars `scan_csv` lazy, or DuckDB |
| `df.append(other)` in a loop | Build a list of frames, `pd.concat` once at the end |
| `df.apply(lambda r: r["a"] + r["b"], axis=1)` | `df["a"] + df["b"]` |
| `df.sort_values("x").iloc[0]` to get min row | `df.loc[df["x"].idxmin()]` |
| `pd.read_csv(...)` then immediately filtering 99% out | Filter at read time with `chunksize` or use Polars/DuckDB |
| Converting datetime with `apply(lambda x: ...)` | `pd.to_datetime(series, format="...")` |
| Storing low-cardinality strings as object | `.astype("category")` |
| Using `==` on float columns | Use `np.isclose(a, b)` |
| `df["x"].apply(lambda s: s.upper())` on strings | `df["x"].str.upper()` (vectorized) |

---

## 15. Thirty-six problems (with full structure)

Each problem follows: **Statement → Intuition → Brute force → Optimized → Complexity → Edge cases → Real-world → Follow-ups.**
**Section breakdown:** 12 NumPy (P1–P12), 15 Pandas (P13–P27), 4 Polars (P28–P31), 5 Visualization (P32–P36).

---

### Problem 1 — Standardize a feature matrix (z-score)

**Statement.** Given `X: np.ndarray` of shape `(n_samples, n_features)`, return X with each column having mean 0 and std 1.

**Intuition.** Subtract per-column mean, divide by per-column std. Broadcasting handles the per-column part.

**Brute force.**
```python
def standardize_loop(X):
    out = np.empty_like(X, dtype=float)
    for j in range(X.shape[1]):
        col = X[:, j]
        out[:, j] = (col - col.mean()) / col.std()
    return out
```

**Optimized.**
```python
def standardize(X: np.ndarray) -> np.ndarray:
    mean = X.mean(axis=0, keepdims=True)        # shape (1, n_features)
    std  = X.std(axis=0, keepdims=True)
    std[std == 0] = 1.0                          # avoid div-by-zero on constant cols
    return (X - mean) / std
```

**I/O.**
```python
X = np.array([[1, 100], [2, 200], [3, 300]], dtype=float)
standardize(X)
# [[-1.224..., -1.224...],
#  [ 0.    ,    0.    ],
#  [ 1.224...,  1.224...]]
```

**Complexity.** O(n·d) time, O(d) extra memory (for mean/std vectors).

**Edge cases.** Constant column → std=0 (we patch to 1.0). All-NaN column → use `np.nanmean` / `np.nanstd`. Single row → std=0 across the board.

**Real-world.** Every linear/logistic regression, neural net pre-processing, clustering input. This is `sklearn.preprocessing.StandardScaler` under the hood.

**Follow-ups.** Robust scaling using median/IQR (resistant to outliers). Streaming version (Welford's online algorithm). Per-feature scaling fit on train, applied to test (fit-transform pattern).

---

### Problem 2 — Pairwise Euclidean distances without loops

**Statement.** Given `A: (n, d)` and `B: (m, d)`, return `D: (n, m)` where `D[i,j] = ||A[i] - B[j]||_2`.

**Intuition.** `||a-b||² = ||a||² + ||b||² - 2·a·b`. All three terms can be computed with matrix operations.

**Brute force.** Triple-nested loop: O(n·m·d) but Python-level — ~1000× slower.

**Optimized.**
```python
def pairwise_dist(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    a2 = (A**2).sum(axis=1, keepdims=True)        # (n, 1)
    b2 = (B**2).sum(axis=1, keepdims=True).T      # (1, m)
    ab = A @ B.T                                   # (n, m)
    sq = a2 + b2 - 2 * ab
    sq = np.maximum(sq, 0)                         # numerical floor
    return np.sqrt(sq)
```

**I/O.**
```python
A = np.array([[0,0],[1,0]])
B = np.array([[0,0],[0,1],[3,4]])
pairwise_dist(A, B)
# [[0., 1., 5.],
#  [1., 1.41421356, 4.47213595]]
```

**Complexity.** O(n·d + m·d + n·m) — the matrix product dominates. ~100–1000× faster than loops because BLAS uses SIMD + multi-core.

**Edge cases.** Floating-point can produce tiny negatives — clamp with `np.maximum(sq, 0)` before sqrt. For very high-dim data, prefer `scipy.spatial.distance.cdist` or `sklearn.metrics.pairwise.euclidean_distances`.

**Real-world.** k-NN classifiers, clustering, nearest-vector search in embedding spaces (early RAG implementations did this naively).

**Follow-ups.** Cosine distance. Top-k nearest (use `np.argpartition`, not full sort). Batched version for memory-bounded GPUs. FAISS for production-scale ANN.

---

### Problem 3 — Rolling mean using a 1D convolution / cumsum

**Statement.** Compute the simple moving average over window `k` for a 1-D array of length n.

**Intuition.** Naive loop is O(n·k). With a cumulative-sum trick, it's O(n).

**Solution.**
```python
def rolling_mean(x: np.ndarray, k: int) -> np.ndarray:
    """Returns array of length n - k + 1."""
    csum = np.concatenate(([0.0], np.cumsum(x, dtype=float)))
    return (csum[k:] - csum[:-k]) / k
```

**I/O.**
```python
rolling_mean(np.array([1,2,3,4,5,6]), 3)
# array([2., 3., 4., 5.])
```

**Complexity.** O(n) time, O(n) extra space.

**Edge cases.** k > n (empty result). Floating-point cumsum drift on huge arrays — use `np.cumsum(x, dtype=np.float64)` to avoid float32 drift.

**Real-world.** Smoothing in time-series, feature engineering, technical indicators in finance, signal processing.

**Follow-ups.** Centered window (return values aligned at the middle of each window). Rolling median (no cumsum trick — use `bottleneck.move_median`). Rolling on uneven time index — that's pandas `rolling("7D")`.

---

### Problem 4 — One-hot encode an integer label vector

**Statement.** Given labels `y` of shape `(n,)` with values in `[0, K)`, return `Y: (n, K)` one-hot matrix.

**Solution.**
```python
def one_hot(y: np.ndarray, num_classes: int | None = None) -> np.ndarray:
    if num_classes is None:
        num_classes = int(y.max()) + 1
    Y = np.zeros((y.size, num_classes), dtype=np.float32)
    Y[np.arange(y.size), y] = 1.0       # fancy indexing
    return Y
```

**I/O.**
```python
one_hot(np.array([0, 2, 1, 2]))
# [[1., 0., 0.],
#  [0., 0., 1.],
#  [0., 1., 0.],
#  [0., 0., 1.]]
```

**Complexity.** O(n·K) memory; O(n) writes.

**Edge cases.** Negative labels (raise). `num_classes` smaller than max label (silent IndexError — validate first). Sparse high-cardinality (use `scipy.sparse` or embeddings).

**Real-world.** Multi-class classification targets, categorical features for trees/linear models, attention masks.

**Follow-ups.** Smooth one-hot for label smoothing (used in transformer training). Multi-label (a row can have multiple 1s — use `Y[rows, cols] = 1`). Index-sparse representation (just store the indices).

---

### Problem 5 — Top-k argmax along an axis

**Statement.** For an array of scores shape `(n, K)`, return the indices of the top-k columns per row.

**Intuition.** A full sort is O(K log K). `argpartition` is O(K) and gives you the top-k unsorted; sort only the k indices afterwards.

**Solution.**
```python
def topk(scores: np.ndarray, k: int) -> np.ndarray:
    # partition: top-k in last k positions (unsorted)
    part = np.argpartition(scores, -k, axis=1)[:, -k:]
    # then sort just those k by descending score
    rows = np.arange(scores.shape[0])[:, None]
    sorted_within = np.argsort(-scores[rows, part], axis=1)
    return part[rows, sorted_within]
```

**I/O.**
```python
S = np.array([[0.1, 0.5, 0.2, 0.9, 0.3],
              [0.7, 0.1, 0.4, 0.2, 0.6]])
topk(S, 2)
# [[3, 1],
#  [0, 4]]
```

**Complexity.** O(n·K) for partition + O(n·k log k) for the small sort — vs O(n·K log K) for full sort.

**Real-world.** Classifier top-k accuracy, retrieval candidate generation, recommender scoring, LLM next-token sampling (top-k).

**Follow-ups.** Top-k along axis 0. Top-k with returning the values too. Top-p (nucleus) sampling: cumulative-prob threshold. Heavy-hitters in streaming (count-min sketch).

---

### Problem 6 — Image: convert RGB to grayscale, vectorized

**Statement.** Image array shape `(H, W, 3)` of uint8. Return `(H, W)` grayscale using ITU-R BT.601 weights `[0.299, 0.587, 0.114]`.

**Solution.**
```python
def rgb_to_gray(img: np.ndarray) -> np.ndarray:
    weights = np.array([0.299, 0.587, 0.114], dtype=np.float32)
    return (img.astype(np.float32) @ weights).astype(np.uint8)
```

**I/O.**
```python
img = np.array([[[255,0,0]], [[0,255,0]], [[0,0,255]]], dtype=np.uint8)  # (3,1,3)
rgb_to_gray(img)
# [[ 76],
#  [149],
#  [ 29]]
```

**Complexity.** O(H·W) — single matrix multiply through BLAS.

**Edge cases.** RGBA images have shape `(H, W, 4)` — index `[..., :3]` first. Float images in `[0,1]` — skip the `astype(uint8)` cast at the end.

**Real-world.** Image preprocessing for OCR, classical CV, thumbnail generation. Vectorization here matters: a Python loop over 4K pixels is unusable.

**Follow-ups.** Batch of images shape `(N, H, W, 3)` — same code works (numpy broadcasts the matmul). HSV/LAB conversion. Per-channel histogram equalization.

---

### Problem 7 — Train/test split (no sklearn)

**Statement.** Given features `X (n, d)` and labels `y (n,)`, split into train/test of given fraction with reproducible randomness.

**Solution.**
```python
def train_test_split(X: np.ndarray, y: np.ndarray,
                     test_frac: float = 0.2, seed: int = 0):
    rng = np.random.default_rng(seed)
    n = len(X)
    perm = rng.permutation(n)
    n_test = int(n * test_frac)
    test_idx, train_idx = perm[:n_test], perm[n_test:]
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]
```

**Complexity.** O(n) time, O(n) extra (for the permutation).

**Edge cases.** Class imbalance — use stratified split for classification. Time series — never random-split; always split chronologically (look-ahead leakage). Tiny datasets — cross-validation, not single split.

**Real-world.** Foundation of every ML pipeline. Subtle: leak-free splitting requires care for grouped data (same user shouldn't be in both splits).

**Follow-ups.** Stratified by class. Group-aware split. K-fold cross-validation. Time-series cross-validation (expanding window).

---

### Problem 8 — Mini-batch iterator with shuffling

**Statement.** Yield mini-batches `(X_batch, y_batch)` of size `B` from `(X, y)`, shuffled each epoch.

**Solution.**
```python
def batch_iter(X: np.ndarray, y: np.ndarray, batch_size: int,
               shuffle: bool = True, seed: int = 0):
    rng = np.random.default_rng(seed)
    n = len(X)
    while True:                                  # epoch loop — caller breaks
        idx = rng.permutation(n) if shuffle else np.arange(n)
        for start in range(0, n, batch_size):
            sl = idx[start:start + batch_size]
            yield X[sl], y[sl]
```

**Complexity.** O(n) per epoch.

**Edge cases.** Last batch smaller than B (most code accepts this). With drop_last=True, skip it. Multi-process loading: each worker needs a different seed.

**Real-world.** Every neural net training loop. PyTorch's `DataLoader` does exactly this with multi-worker support and prefetching.

**Follow-ups.** Weighted sampling (oversample minority class). Bucket-by-length (NLP batching). Sharded across machines.

---

### Problem 9 — Stable softmax

**Statement.** Implement softmax that doesn't overflow on large logits.

**Intuition.** `softmax(x) = softmax(x - c)` for any constant c. Subtract `max(x)` to keep all exponents ≤ 0.

**Naive (broken).**
```python
def softmax_naive(x):
    e = np.exp(x)
    return e / e.sum()
# softmax_naive(np.array([1000., 1001., 1002.])) → all NaN (inf/inf)
```

**Solution.**
```python
def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = x - x.max(axis=axis, keepdims=True)      # shift for numerical stability
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)
```

**I/O.**
```python
softmax(np.array([1000., 1001., 1002.]))
# [0.09003057, 0.24472847, 0.66524096]
```

**Complexity.** O(n).

**Real-world.** Output of classification heads, attention weights in transformers. The "subtract max" trick is in every framework's source.

**Follow-ups.** Log-softmax (more stable for cross-entropy). Temperature scaling. Sparse-softmax / top-k softmax for vocab size 100K+.

---

### Problem 10 — Fast count of items per row using bincount

**Statement.** Given an integer array `(n, m)` where each cell is a class label in `[0, K)`, return shape `(n, K)` counts per row.

**Intuition.** `np.bincount` is the fastest way to count integers. Apply per row.

**Solution.**
```python
def per_row_counts(arr: np.ndarray, K: int) -> np.ndarray:
    n = arr.shape[0]
    out = np.zeros((n, K), dtype=np.int32)
    # use np.add.at for unbuffered scatter
    rows = np.repeat(np.arange(n), arr.shape[1])
    np.add.at(out, (rows, arr.ravel()), 1)
    return out
```

**I/O.**
```python
arr = np.array([[0, 1, 1, 2],
                [2, 2, 0, 0]])
per_row_counts(arr, K=3)
# [[1, 2, 1],
#  [2, 0, 2]]
```

**Complexity.** O(n·m) — one pass.

**Real-world.** Bag-of-words feature matrices, n-gram counts, multi-hot encoding for sparse categoricals.

**Follow-ups.** Sparse output for huge K (`scipy.sparse.csr_matrix`). Weighted counts (`np.add.at(out, idx, weights)`).

---

### Problem 11 — Find indices of local maxima in a 1D array

**Statement.** Return indices `i` where `x[i] > x[i-1]` and `x[i] > x[i+1]` (strict peaks), excluding endpoints.

**Solution.**
```python
def find_peaks(x: np.ndarray) -> np.ndarray:
    return np.where((x[1:-1] > x[:-2]) & (x[1:-1] > x[2:]))[0] + 1
```

**I/O.**
```python
find_peaks(np.array([1, 3, 2, 5, 4, 6, 6, 1]))
# [1, 3]   (index 5 isn't a strict peak — its right neighbor equals it)
```

**Complexity.** O(n).

**Edge cases.** Plateaus (use `>=` for one side and `>` for the other if plateaus count). NaN — preprocess. Endpoints — extend the array if you want them.

**Real-world.** Audio onset detection, sensor data anomaly spikes, financial chart pivots. `scipy.signal.find_peaks` has a richer API (height, prominence, distance) for production use.

**Follow-ups.** Minimum prominence (height above surrounding valleys). Min distance between peaks. 2-D image local maxima.

---

### Problem 12 — Boolean mask intersection of N arrays, memory-efficient

**Statement.** Given a list of `N` boolean arrays, all shape `(M,)`, find indices where all are True.

**Solution.**
```python
def common_true(masks: list[np.ndarray]) -> np.ndarray:
    if not masks: return np.array([], dtype=np.int64)
    combined = masks[0]
    for m in masks[1:]:
        combined = combined & m         # short-circuit possible? not in numpy
    return np.where(combined)[0]
```

For very many masks, `np.logical_and.reduce(masks)` is equivalent and slightly faster.

**Complexity.** O(N·M).

**Real-world.** Compound filter conditions in feature pipelines, multi-criteria screening, intersection of cohort definitions.

**Follow-ups.** Bitset-style packed booleans (8× memory reduction). Sparse boolean (only store True indices) when most are False.

---

### Problem 13 — DataFrame: clean a messy CSV

**Statement.** A CSV has columns `name`, `age`, `email`, `joined`. Issues: trailing/leading whitespace; mixed-case email; `age` sometimes blank or "n/a"; `joined` in inconsistent date formats.

**Solution.**
```python
import pandas as pd
import numpy as np

def clean_users(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["name"]  = df["name"].str.strip()
    df["email"] = df["email"].str.strip().str.lower()
    # age: replace "n/a" / "" with NaN, then numeric
    df["age"] = pd.to_numeric(
        df["age"].astype(str).str.strip().replace({"n/a": None, "": None}),
        errors="coerce",
    ).astype("Int32")                            # nullable int
    df["joined"] = pd.to_datetime(df["joined"], errors="coerce", utc=True)
    # drop rows with no usable email
    df = df.dropna(subset=["email"])
    df = df[df["email"].str.contains("@", na=False)]
    return df.reset_index(drop=True)
```

**Real-world.** Day 1 of every analytics project. Build a re-usable `clean_*` function per data source — never inline cleaning in analysis code.

**Follow-ups.** Validate with pandera or pydantic. Schema versioning. Track row-counts before/after each step (data-quality monitoring).

---

### Problem 14 — DataFrame: top-3 highest-paid per department

**Statement.** Given employees DataFrame with `dept, name, salary`, return a DataFrame of the top 3 in each department.

**Solution.**
```python
def top_n_per_group(df: pd.DataFrame, group: str, sort_by: str, n: int) -> pd.DataFrame:
    return (
        df.sort_values(sort_by, ascending=False)
          .groupby(group, as_index=False)
          .head(n)
          .sort_values([group, sort_by], ascending=[True, False])
          .reset_index(drop=True)
    )
```

**I/O.**
```python
df = pd.DataFrame({
    "dept":   ["eng","eng","eng","sales","sales","sales"],
    "name":   ["a","b","c","d","e","f"],
    "salary": [100, 90, 95, 70, 60, 80],
})
top_n_per_group(df, "dept", "salary", 2)
#     dept name  salary
# 0    eng    a     100
# 1    eng    c      95
# 2  sales    f      80
# 3  sales    d      70
```

**Complexity.** O(n log n) for the sort; the groupby + head is O(n).

**Real-world.** Top-K queries, leaderboards, A/B test cohort dashboards. The `sort + groupby.head(n)` pattern is the cleanest pandas idiom; SQL equivalent is `ROW_NUMBER() OVER (PARTITION BY ...)`.

**Follow-ups.** Bottom-N. Top-N with ties broken by another column. Large data → use `pl.DataFrame.top_k(n).over("dept")` in Polars.

---

### Problem 15 — Find duplicates by composite key

**Statement.** Find rows where `(user_id, event_type, day)` is duplicated.

**Solution.**
```python
def find_duplicates(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    mask = df.duplicated(subset=keys, keep=False)   # mark every duplicate, not just repeats
    return df[mask].sort_values(keys)
```

**Complexity.** O(n) for hash-based duplicate detection.

**Real-world.** Data-quality checks, deduplication before joins, idempotency violations in event pipelines.

**Follow-ups.** Drop duplicates keeping latest (`drop_duplicates(subset=..., keep="last")` after sorting). Approximate dedup on text (LSH, MinHash). Soft-duplicates by similarity.

---

### Problem 16 — Pivot a long event log into a session matrix

**Statement.** Events DataFrame `user_id, event_type, ts`. Build a wide DataFrame: one row per user, one column per event_type, value = count.

**Solution.**
```python
def session_matrix(events: pd.DataFrame) -> pd.DataFrame:
    return (
        events.pivot_table(
            index="user_id",
            columns="event_type",
            values="ts",
            aggfunc="count",
            fill_value=0,
        )
        .astype("int32")
    )
```

**Real-world.** Funnel analysis, churn-prediction features, behavior segmentation, embedding inputs.

**Follow-ups.** Time-windowed (events in last 7 days only). Multi-session per user (`groupby([user_id, session_id])`). Memory-savvy version with `pl.pivot` for billions of rows.

---

### Problem 17 — Time-series: 7-day rolling DAU

**Statement.** Events table `user_id, ts`. Compute 7-day rolling unique-user count (DAU/MAU style).

**Solution (a 30-day approximation that's actually correct).**
```python
def rolling_unique_users(events: pd.DataFrame, window_days: int = 7) -> pd.Series:
    # Bucket to day, then for each day count distinct users in past window
    daily = (
        events.assign(day=events["ts"].dt.tz_convert("UTC").dt.normalize())
              .groupby("day")["user_id"].agg(set)
    )
    # rolling apply on sets
    out = {}
    days = daily.index.sort_values()
    from collections import deque
    win = deque()                                # of (day, set)
    running = set()
    user_count = {}                              # user -> count of windows it's in (so we can drop)
    # simpler: just rebuild union per day — fine up to ~hundreds of days
    for i, d in enumerate(days):
        start = d - pd.Timedelta(days=window_days - 1)
        sets_in_win = daily.loc[(daily.index >= start) & (daily.index <= d)]
        out[d] = len(set().union(*sets_in_win))
    return pd.Series(out, name=f"unique_users_{window_days}d").sort_index()
```

**Complexity.** O(W·U) per day where W=window, U=avg users/day. For very large data, build an inverted "user → days seen" map and use a sliding window.

**Real-world.** Product analytics dashboards, retention metrics. The naive `rolling().nunique()` can be slow; understanding when to rebuild your aggregation matters.

**Follow-ups.** Streaming DAU using HyperLogLog (`datasketches` library) — constant memory regardless of users. Polars equivalent (much faster). MAU rolling 30-day.

---

### Problem 18 — Window function: cumulative sum per group, reset on date

**Statement.** Sales `customer_id, date, amount`. Add a column `cum_amount_ytd` — cumulative sum within the same year, per customer.

**Solution.**
```python
def cum_ytd(sales: pd.DataFrame) -> pd.DataFrame:
    sales = sales.sort_values(["customer_id", "date"]).copy()
    sales["year"] = sales["date"].dt.year
    sales["cum_amount_ytd"] = (
        sales.groupby(["customer_id", "year"])["amount"].cumsum()
    )
    return sales.drop(columns="year")
```

**Real-world.** Revenue dashboards, year-to-date metrics, billing systems. SQL: `SUM(amount) OVER (PARTITION BY customer_id, YEAR(date) ORDER BY date)`.

**Follow-ups.** Quarter-to-date. Trailing 12 months. Per-customer running median (no built-in cumulative median — use `expanding().median()`).

---

### Problem 19 — Join: enrich orders with customer info, validate cardinality

**Statement.** `orders (order_id, customer_id, amount)` and `customers (customer_id, name, country)`. Produce `orders` enriched with `name` and `country`. The join must NOT cause row count to change.

**Solution.**
```python
def enrich_orders(orders: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    # Validate: every customer_id is unique in customers
    if customers["customer_id"].duplicated().any():
        raise ValueError("customers has duplicate customer_id")
    # left join with explicit validate
    return orders.merge(
        customers[["customer_id", "name", "country"]],
        on="customer_id",
        how="left",
        validate="m:1",          # many orders, one customer
    )
```

**Real-world.** Every analytics pipeline. The `validate=` parameter has saved careers — silent many-to-many joins double row counts and corrupt downstream metrics for weeks before someone notices.

**Follow-ups.** Inner vs left choice (do you want orders with no matching customer dropped or kept with nulls?). Enrichment with a slowly-changing dimension (use the customer record as of the order date).

---

### Problem 20 — Memory: reduce a CSV from 4 GB to fit in 1 GB

**Statement.** A CSV has 50M rows, columns `user_id (int)`, `country (str, 50 unique)`, `is_active (bool-ish "true"/"false")`, `score (float)`, `ts (datetime)`. Loading naively uses ~4 GB. Get it under 1 GB.

**Solution.**
```python
def read_compact(path: str) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        dtype={
            "user_id":   "int32",         # 8B → 4B
            "country":   "category",      # str object → category dict
            "is_active": "bool",          # explicit bool
            "score":     "float32",
        },
        parse_dates=["ts"],
        engine="pyarrow",                  # faster reader
    )
    return df
```

**Result.** Typically 4× smaller. For best results, save once as parquet:

```python
df.to_parquet("data.parquet", compression="zstd")
# subsequent reads are 10× faster and even smaller on disk
```

**Real-world.** Day-1 production move. Most people leave performance on the table by accepting pandas defaults.

**Follow-ups.** Read in chunks (`chunksize`) for >RAM data. Switch to Polars `scan_csv` for end-to-end laziness. Convert pipeline to parquet/Iceberg.

---

### Problem 21 — String: extract domain from email column

**Solution.**
```python
def add_email_domain(df: pd.DataFrame, col: str = "email") -> pd.DataFrame:
    df = df.copy()
    df["email_domain"] = df[col].str.lower().str.extract(r"@([\w\.-]+)$", expand=False)
    return df
```

**I/O.**
```python
add_email_domain(pd.DataFrame({"email": ["a@x.com", "B@Y.IO", "bad-email"]}))
#         email email_domain
# 0     a@x.com        x.com
# 1     B@Y.IO         y.io
# 2   bad-email          NaN
```

**Real-world.** Cohorting, deliverability checks, anti-fraud, B2B/consumer split.

**Follow-ups.** Public suffix list (PSL) handling — `co.uk` is one TLD. Disposable-email detection. Vectorized validation with regex compiled once.

---

### Problem 22 — Detecting outliers per group

**Statement.** For each `dept`, mark rows where `salary` is more than 3 IQRs above Q3 or below Q1.

**Solution.**
```python
def mark_outliers(df: pd.DataFrame, group: str, value: str, k: float = 3.0) -> pd.DataFrame:
    df = df.copy()
    q1 = df.groupby(group)[value].transform(lambda s: s.quantile(0.25))
    q3 = df.groupby(group)[value].transform(lambda s: s.quantile(0.75))
    iqr = q3 - q1
    df["is_outlier"] = (df[value] < q1 - k * iqr) | (df[value] > q3 + k * iqr)
    return df
```

**Real-world.** Data quality, fraud signals, bonus/comp review flags. Robust to skewed distributions in a way that mean ± 3·std is not.

**Follow-ups.** MAD-based outlier (median absolute deviation — even more robust). Multivariate outliers (Mahalanobis distance, Isolation Forest).

---

### Problem 23 — Cohort retention table

**Statement.** Events `(user_id, ts)`. Compute retention: percent of users from cohort month M who are still active in month M+k for k=0..N.

**Solution.**
```python
def cohort_retention(events: pd.DataFrame, max_k: int = 6) -> pd.DataFrame:
    e = events.copy()
    e["month"]  = e["ts"].dt.tz_convert("UTC").dt.to_period("M")
    cohort_month = e.groupby("user_id")["month"].min().rename("cohort")
    e = e.merge(cohort_month, on="user_id")
    e["k"] = (e["month"] - e["cohort"]).apply(lambda x: x.n)
    pivot = (
        e.drop_duplicates(["user_id", "k"])
         .groupby(["cohort", "k"])["user_id"].nunique()
         .unstack("k").fillna(0).astype(int)
    )
    cohort_size = pivot[0]
    return pivot.div(cohort_size, axis=0).round(3).iloc[:, :max_k+1]
```

**Real-world.** The most-asked product analytics question. Every PM wants a cohort retention triangle.

**Follow-ups.** Weekly cohorts. Revenue retention (sum amount instead of nunique users). Confidence intervals for small cohorts.

---

### Problem 24 — A/B test t-test with effect size

**Statement.** Two arrays `a, b` of metric values. Return mean diff, 95% CI of the diff, t-stat, p-value, Cohen's d.

**Solution.**
```python
import numpy as np
from scipy import stats

def ab_test(a: np.ndarray, b: np.ndarray) -> dict:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    na, nb = len(a), len(b)
    ma, mb = a.mean(), b.mean()
    va, vb = a.var(ddof=1), b.var(ddof=1)
    diff = mb - ma
    se   = np.sqrt(va/na + vb/nb)               # Welch's standard error
    t_stat, p = stats.ttest_ind(b, a, equal_var=False)
    df_ = (va/na + vb/nb)**2 / ((va/na)**2/(na-1) + (vb/nb)**2/(nb-1))
    ci_half = stats.t.ppf(0.975, df_) * se
    pooled_sd = np.sqrt(((na-1)*va + (nb-1)*vb) / (na + nb - 2))
    cohen_d = diff / pooled_sd if pooled_sd > 0 else 0.0
    return {
        "mean_a": ma, "mean_b": mb, "diff": diff,
        "ci95": (diff - ci_half, diff + ci_half),
        "t": float(t_stat), "p": float(p), "cohen_d": cohen_d,
    }
```

**Real-world.** A/B testing infrastructure. Beware: t-test assumes IID samples. Repeat-user metrics (sessions per user) violate this — use bootstrap or hierarchical models.

**Follow-ups.** Bootstrap confidence intervals. Mann–Whitney for non-normal. Sequential testing (Optimizely / always-valid p-values).

---

### Problem 25 — Build features for a churn model

**Statement.** Events `(user_id, ts, event_type, value)` and a `churn_label_date`. For each `user_id`, build a feature row using only data **before** `churn_label_date`: total events 30d/90d, distinct event types, days since last event, sum/avg `value`.

**Solution.**
```python
def build_churn_features(events: pd.DataFrame, label_date: pd.Timestamp) -> pd.DataFrame:
    e = events[events["ts"] < label_date].copy()
    e["days_back"] = (label_date - e["ts"]).dt.days
    g = e.groupby("user_id")
    f = pd.DataFrame({
        "events_30d":  g.apply(lambda x: (x["days_back"] <= 30).sum(), include_groups=False),
        "events_90d":  g.apply(lambda x: (x["days_back"] <= 90).sum(), include_groups=False),
        "n_event_types": g["event_type"].nunique(),
        "days_since_last": g["days_back"].min(),
        "value_sum":   g["value"].sum(),
        "value_mean":  g["value"].mean(),
    })
    return f.reset_index()
```

**Real-world.** This is feature engineering for any tabular ML model. Critical: time-cutoff (only past data) prevents leakage. In production this lives in a feature store (Tecton, Feast).

**Follow-ups.** Time-decay weighted aggregates (recent events weighted higher). Per-event-type counts. Vectorize with rolling windows for thousands of label dates.

---

### Problem 26 — Streaming aggregate from chunked CSV

**Statement.** A 50 GB CSV of `(user_id, amount)`. Compute per-user total without loading the file.

**Solution.**
```python
from collections import defaultdict
import pandas as pd

def streaming_user_totals(path: str, chunksize: int = 500_000) -> pd.Series:
    totals: dict[int, float] = defaultdict(float)
    for chunk in pd.read_csv(path, chunksize=chunksize, dtype={"user_id":"int32","amount":"float64"}):
        partial = chunk.groupby("user_id")["amount"].sum()
        for uid, val in partial.items():
            totals[uid] += val
    return pd.Series(totals, name="total").sort_index()
```

**Real-world.** Pre-spark batch jobs, log aggregation, feature offline batches. The pattern (`groupby` per chunk + accumulate) generalizes to any associative aggregation.

**Follow-ups.** Polars `scan_csv` does this end-to-end with optimization. DuckDB query directly on CSV. Multi-process chunk consumption.

---

### Problem 27 — Apply a model row-wise without `apply(axis=1)`

**Statement.** Score every row through a function `f(a, b, c) → float`. The naive `df.apply(lambda r: f(r.a, r.b, r.c), axis=1)` is too slow.

**Solution (vectorize the function input).**
```python
def vectorized_score(df: pd.DataFrame) -> pd.Series:
    a, b, c = df["a"].to_numpy(), df["b"].to_numpy(), df["c"].to_numpy()
    # f as numpy ops:
    return pd.Series(np.exp(-a) + b * c**0.5, index=df.index)
```

If `f` is a black box (e.g. a sklearn model):

```python
preds = model.predict(df[["a","b","c"]].to_numpy())   # batch call
df["score"] = preds
```

**Real-world.** Bulk ML scoring, rule engines, business logic application. Replacing `apply(axis=1)` with vectorized numpy is often a 100× win.

**Follow-ups.** When `f` truly can't be vectorized: numba `@njit`, Cython, or polars expressions (which compile to Rust).

---

### Problem 28 — Polars: lazy parquet aggregation

**Statement.** Files `events_2026_*.parquet` (20 GB total). Find the top 10 user_ids by total purchase amount in Q1 2026.

**Solution.**
```python
import polars as pl

q = (
    pl.scan_parquet("events_2026_*.parquet")
      .filter(pl.col("event_type") == "purchase")
      .filter(pl.col("ts").is_between(
          pl.datetime(2026, 1, 1), pl.datetime(2026, 4, 1), closed="left"))
      .group_by("user_id")
      .agg(pl.col("amount").sum().alias("total"))
      .sort("total", descending=True)
      .limit(10)
)
top10 = q.collect(streaming=True)     # streaming for >RAM data
```

**Why this is fast.** Predicate pushdown means only matching rows are decoded; column projection means only `user_id, ts, event_type, amount` are read; multiple cores chew through different files in parallel.

**Real-world.** Daily ETL. The pandas equivalent reads the entire 20 GB into RAM first.

**Follow-ups.** Window function for "top K per cohort." Streaming sink to parquet. Materialized views with Delta Lake.

---

### Problem 29 — Polars: window function — per-customer running balance

**Solution.**
```python
import polars as pl

balances = (
    transactions
      .sort(["customer_id", "ts"])
      .with_columns(
          balance = pl.col("amount").cum_sum().over("customer_id")
      )
)
```

**Real-world.** Banking ledgers, stock-portfolio cost basis, inventory FIFO/LIFO.

**Follow-ups.** Reset balance at year boundaries (`over(["customer_id", pl.col("ts").dt.year()])`). Multi-currency totals.

---

### Problem 30 — Polars: join performance comparison

**Statement.** Demonstrate Polars's automatic join algorithm choice on a 50M × 1M join.

**Solution.**
```python
import polars as pl

# polars picks hash-join for unsorted, sort-merge for sorted inputs
big   = pl.scan_parquet("events.parquet")          # 50M
small = pl.scan_parquet("users.parquet")           # 1M

joined = (
    big.join(small, on="user_id", how="left")
       .group_by("country")
       .agg(pl.col("amount").sum())
       .collect(streaming=True)
)
```

Polars uses hash-join with the smaller side as the build side automatically. On the same hardware where pandas takes 3 minutes, Polars runs this in ~5 seconds.

**Real-world.** Daily jobs that previously required Spark are now single-machine with Polars + a beefy box.

**Follow-ups.** `coalesce` for streaming. Asof join (last value at-or-before). Cross join with pre-filter.

---

### Problem 31 — Polars: convert a pandas pipeline (1:1)

**Statement.** Convert this pandas snippet to polars:

```python
result = (df
    .query("country == 'US'")
    .assign(net = lambda d: d.gross - d.tax)
    .groupby("month").agg(total_net=("net","sum"), n=("net","count"))
    .reset_index()
    .sort_values("total_net", ascending=False))
```

**Solution.**
```python
import polars as pl

result = (
    df  # pl.DataFrame
      .filter(pl.col("country") == "US")
      .with_columns(net = pl.col("gross") - pl.col("tax"))
      .group_by("month")
      .agg(
          total_net = pl.col("net").sum(),
          n         = pl.col("net").count(),
      )
      .sort("total_net", descending=True)
)
```

**Real-world.** Most pandas → polars migrations are mechanical. The hardest mental shift is "no index" — rows are just rows; if you want an index, it's a column.

**Follow-ups.** Round-trip via Arrow (`df.to_arrow()` ↔ `pl.from_arrow(...)` — zero copy). Drop-in replacement for sklearn input (works directly).

---

### Problem 32 — Visualization: plot training and validation loss with annotations

**Statement.** Given `train_losses, val_losses` lists per epoch, plot both, annotate the best validation epoch, mark a vertical line, and save.

**Solution.**
```python
import matplotlib.pyplot as plt
import numpy as np

def plot_losses(train, val, save_path="loss.png"):
    epochs = np.arange(1, len(train) + 1)
    best_epoch = int(np.argmin(val)) + 1
    best_val = min(val)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(epochs, train, label="train", color="C0")
    ax.plot(epochs, val,   label="val",   color="C1")
    ax.axvline(best_epoch, color="grey", linestyle="--", alpha=0.5)
    ax.scatter([best_epoch], [best_val], color="C1", zorder=5)
    ax.annotate(f"best: epoch {best_epoch}\nval={best_val:.3f}",
                xy=(best_epoch, best_val),
                xytext=(best_epoch + 1, best_val + 0.05),
                arrowprops=dict(arrowstyle="->"))
    ax.set_xlabel("epoch"); ax.set_ylabel("loss"); ax.set_title("Training curves")
    ax.legend(); ax.grid(alpha=0.3); fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
```

**Real-world.** Every notebook in your future. Hand-rolling small plotting helpers is faster than importing seaborn for one-offs.

**Follow-ups.** Log-scale y-axis. Multiple runs overlaid (different colors). Highlight overfitting region. Same plot in plotly for interactive notebooks.

---

### Problem 33 — Visualization: faceted boxplot from long-form data

**Solution (seaborn).**
```python
import seaborn as sns

g = sns.catplot(
    data=df,
    x="dept", y="salary",
    col="level",            # one subplot per level
    kind="box",
    height=4, aspect=1.2,
    sharey=True,
)
g.set_xticklabels(rotation=30)
g.fig.suptitle("Salary by department × level", y=1.02)
g.savefig("facets.png", dpi=150)
```

**Real-world.** EDA, model error analysis (residuals by group), monitoring dashboards.

**Follow-ups.** Ordering categories by median (`order=df.groupby("dept")["salary"].median().sort_values().index`). Overlay individual points (`sns.swarmplot`). Use violin for distribution shape.

---

### Problem 34 — Visualization: correlation heatmap, cleaner version

**Solution.**
```python
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

def correlation_heatmap(df, figsize=(8, 6)):
    corr = df.select_dtypes("number").corr()
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)   # hide upper triangle (redundant)
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(
        corr, mask=mask, cmap="RdBu_r", center=0, vmin=-1, vmax=1,
        annot=True, fmt=".2f", square=True, linewidths=0.5,
        cbar_kws={"shrink": 0.8}, ax=ax,
    )
    ax.set_title("Feature correlations")
    fig.tight_layout()
    return fig
```

**Why hide the upper triangle.** Correlation is symmetric — showing both halves is noise. The diagonal is always 1. Cleaner is more readable.

**Real-world.** First step in feature selection, multicollinearity screening, EDA on tabular data.

**Follow-ups.** Cluster the rows/cols (sns.clustermap) so correlated features visually group. Conditional correlation (partial correlation given other features).

---

### Problem 35 — Visualization: time-series with shaded confidence band

**Solution.**
```python
import matplotlib.pyplot as plt

def plot_with_band(t, y_mean, y_low, y_high, label="prediction"):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(t, y_mean, label=label, color="C0")
    ax.fill_between(t, y_low, y_high, alpha=0.25, color="C0", label="95% CI")
    ax.set_xlabel("time"); ax.set_ylabel("value")
    ax.legend(); ax.grid(alpha=0.3); fig.tight_layout()
    return fig
```

**Real-world.** Forecast plots, A/B test daily lift, model uncertainty visualization.

**Follow-ups.** Multiple series with their own bands. Highlight test/holdout region with vertical span (`ax.axvspan`). Date formatting on x-axis (`mdates.DateFormatter`).

---

### Problem 36 — Visualization: histogram + KDE with smart binning

**Solution.**
```python
import seaborn as sns
import numpy as np

def smart_hist(data, ax=None):
    """Freedman–Diaconis bin width — robust to outliers."""
    data = np.asarray(data)
    iqr = np.subtract(*np.percentile(data, [75, 25]))
    bin_width = 2 * iqr / np.cbrt(len(data)) if iqr > 0 else None
    nbins = max(10, int((data.max() - data.min()) / bin_width)) if bin_width else 30
    return sns.histplot(data, bins=nbins, kde=True, ax=ax)
```

**Why Freedman–Diaconis.** Default `bins=10` is wrong for most distributions. F-D adapts to data spread and is robust to outliers — what every textbook recommends.

**Real-world.** Data exploration; understanding feature distributions before modeling; spotting bimodality / heavy tails.

**Follow-ups.** Log-x for heavy-tailed data. Compare two groups (`hue=`). ECDF plot for distributions you really need to compare (`sns.ecdfplot`).

---

## 16. Three mini-projects

### Mini-project A — End-to-end EDA report on a public dataset

Pick a dataset (NYC taxi, Kaggle Titanic, or a public CSV >100MB). Build a notebook that produces, in order:
1. Schema + missing-value report
2. Univariate distributions (histograms / value_counts) for every column
3. Bivariate plots vs target (if classification: boxplots; if regression: scatter)
4. Correlation heatmap of numerics
5. Three "interesting" findings, each with a single-sentence headline + one chart

**Skills exercised:** every section of this module. **Constraint:** under 300 lines of code, runs end-to-end, no `apply(axis=1)`.

### Mini-project B — A pandas → polars migration

Take any pandas notebook you've written (or a public one — Kaggle has thousands). Convert it to polars line-for-line. Time both. Document any operation that became *harder* (there are a few — left-anti-joins, certain time-series ops). This builds the muscle memory for production migrations.

### Mini-project C — A small reusable feature library

Build a module `features.py` exposing functions like `add_lag`, `add_rolling_mean`, `add_time_features`, `add_target_encoding`, `add_count_encoding` — each takes a DataFrame and returns a DataFrame with new columns. Add tests with pytest. This is the seed of a real feature store.

---

## 17. Real-world usage map

| Concept | Where it returns later |
|---|---|
| NumPy broadcasting | PyTorch tensors (same rules); attention computation |
| `np.linalg.solve` / SVD | PCA, recommender SVD, linear regression closed-form |
| Stable softmax | Every transformer; LLM sampling code |
| Vectorized rolling/diff | Feature engineering for tabular ML; financial signals |
| `pd.merge` + `validate=` | Production ETL safety |
| `groupby().transform()` | Per-group features without leakage |
| Cohort retention | Product analytics; churn prediction labels |
| Categorical dtype | XGBoost/LightGBM categorical features |
| Polars lazy + parquet | Modern data lake querying; Iceberg/Delta |
| DuckDB on parquet | Lightweight analytics layer; agentic data tools |
| matplotlib OO API | Custom dashboards; scientific figures |
| seaborn for EDA | First 30 minutes of every new dataset |

---

## 18. Interview pitfalls — what NOT to say

- **"NumPy is fast because it's compiled."** Closer: it stores data contiguously in homogeneous types and dispatches to BLAS/LAPACK/SIMD-aware C code. The "compiled" framing misses *why*.
- **"I'd use a for-loop over the DataFrame to..."** Stop. Describe the vectorized version first. Always.
- **"I'll just `df.apply` it."** Specify `axis=`, and acknowledge that `axis=1` is a Python loop in disguise.
- **"NaN equals NaN."** It doesn't. `np.nan == np.nan` is False. Use `.isna()`.
- **"The pandas index doesn't matter."** It does — operations align on the index. Resetting it can silently change a join.
- **"Just use float64 everywhere."** Defensible for analysis; wasteful for ML training (use float32) and embedded contexts.
- **"I'll just merge and see what comes out."** Always state the expected cardinality before the merge. Use `validate=`.
- **"Polars is just a faster pandas."** It's a different model — no index, eager-vs-lazy, expression API. The Rust-vs-Python part is only one reason it's faster.
- **"I'll plot with `plt.plot(...)`."** Use the OO API: `fig, ax = plt.subplots()`. The implicit pyplot state is fine for one-offs, terrible for anything reusable.
- **"I'll use `iterrows`."** Don't. State the vectorized alternative; use `itertuples` if you genuinely need rows; only as a last resort.

**How to communicate.** Before any pandas operation: state (1) the input shape, (2) the expected output shape, (3) the cardinality of any join. Doing this out loud catches half of bugs before they happen.

---

## 19. Cheatsheet

```text
NUMPY ARRAY CREATION
  np.array(list)         np.zeros / ones / full / eye(n)
  np.arange(s,e,step)    np.linspace(s,e,n)
  rng = np.random.default_rng(seed)
  rng.normal/uniform/integers/choice/permutation

DTYPES (memory)
  bool 1 | int8/uint8 1 | int32 4 | int64 8
  float32 4 | float64 8 | complex128 16
  cast: a.astype(np.float32)

SHAPE & INDEX
  a.shape  a.ndim  a.size  a.dtype
  a.reshape(r,c)  a.reshape(-1,1)  a.T  a.transpose(...)
  a[1,2]  a[1]  a[:,2]  a[1:3, 1:4]  a[::-1]
  view (slice) shares memory; use .copy() for a copy
  a[mask]  a[a>0]=0  a[idx_array]  a[[r],[c]]
  np.where(cond, t, f)  np.select([c1,c2], [v1,v2], default=)

BROADCASTING
  shapes align trailing; dim must equal or be 1
  X - X.mean(axis=0)              standardize
  X - X.mean(axis=1, keepdims=True)
  np.maximum(a, b)  np.minimum(a, b)

REDUCTIONS (axis= !)
  sum mean std var min max prod
  argmin argmax  argsort
  np.percentile / np.quantile
  np.nansum / np.nanmean (NaN-aware)

LINEAR ALGEBRA
  A @ B            matmul
  A.T              transpose
  np.linalg.solve(A, b)            never inv(A)@b
  np.linalg.svd(A)  eig(A)  norm(x, ord=)
  np.einsum("ij,jk->ik", A, B)     general tensor ops

PANDAS — IO
  read_csv/parquet/json/sql; to_parquet(... compression="zstd")
  always: parse_dates=, dtype={...}, columns=[...]

PANDAS — INSPECT
  .shape .dtypes .info(memory_usage="deep")
  .head() .tail() .sample(5)
  .describe(include="all")
  .isna().sum()  .nunique()  .value_counts()
  .memory_usage(deep=True).sum()/1e6

PANDAS — SELECT
  df["col"] / df[["a","b"]]
  df.loc[label, label]   df.iloc[int, int]
  df.loc[mask, cols]     ALWAYS .loc for assignment
  df.query("a > 0 and b == 'x'")

PANDAS — FILTER & MISSING
  df[(df.a>0) & (df.b<5)]    & | ~ , parens
  df[df.x.isin([...])]       df[~df.x.isna()]
  df.dropna(subset=...)      df.fillna(value)
  df.fillna(method="ffill")  df.interpolate()

PANDAS — TRANSFORM
  df["new"] = df.x * 2        vectorize
  df.assign(y=lambda d: d.x*2)
  df["x"].map({"a":1})        replace via dict
  df["x"].str.upper() / .startswith / .extract(r"...")
  df["x"].dt.year / month / hour / dayofweek

PANDAS — GROUPBY
  agg:        df.groupby(k)[v].mean()
  multi-agg:  .agg(name=("v","mean"), n=("v","count"))
  transform:  df["z"] = df.groupby(k)[v].transform("mean")
  apply:      df.groupby(k).apply(custom, include_groups=False)
  rolling:    df["v"].rolling(7).mean()  (or .rolling("7D"))
  ewm:        df["v"].ewm(span=5).mean()

PANDAS — JOIN/RESHAPE
  df.merge(other, on=, how=, validate="m:1")
  pd.concat([a,b], axis=0|1, ignore_index=True)
  df.pivot(index=, columns=, values=)
  df.melt(id_vars=, var_name=, value_name=)
  df.pivot_table(index, columns, values, aggfunc=, margins=True)
  df.stack() / df.unstack()

PANDAS — TIME
  pd.to_datetime(x, utc=True, errors="coerce")
  df = df.set_index("ts").sort_index()
  df.loc["2026-01"]   df.last("30D")
  df.resample("1h").sum() / .ohlc() / .ffill()
  df["x"].shift(1)  .diff()  .pct_change()

PANDAS — PERFORMANCE
  vectorize > map > apply(axis=0) >> apply(axis=1) > iterrows
  itertuples > iterrows (if you must loop)
  category dtype for low-cardinality strings
  Int32/Float32/category to shrink RAM
  read_parquet > read_csv (always)
  query/eval for big-frame boolean filters

POLARS
  df.filter(pl.col("x")>0)
  df.select("a","b")
  df.with_columns(y = pl.col("x")*2)
  df.group_by("k").agg(pl.col("v").mean(), pl.len())
  pl.scan_parquet(...).filter(...).collect(streaming=True)
  pl.col("x").over("group")           window
  df.join(other, on="k", how="left")

DUCKDB
  duckdb.sql("SELECT ... FROM 'file.parquet'").df()
  duckdb.sql("...").pl()
  works on globs, http(s), s3 directly

MATPLOTLIB
  fig, ax = plt.subplots(figsize=(w,h))
  ax.plot/scatter/bar/hist/imshow/errorbar/fill_between
  ax.set_xlabel/ylabel/title; ax.legend(); ax.grid(alpha=0.3)
  fig.tight_layout(); fig.savefig("x.png", dpi=150)
  subplots: fig, axes = plt.subplots(2, 2, sharex=True)

SEABORN
  sns.histplot(df, x=, hue=, kde=True)
  sns.boxplot(df, x=, y=, hue=)
  sns.scatterplot / regplot / lmplot(col=)
  sns.heatmap(corr, annot=True, cmap="RdBu", center=0)
  sns.pairplot(df, hue=)

ANTI-PATTERNS (avoid)
  chained assignment df[mask][col]=v
  for/iterrows over big frames
  apply(axis=1) when vectorizable
  read_csv on >5GB files
  silently fillna(0) on numeric
  inv(A)@b
  jet/rainbow colormaps
  pyplot implicit API for production
```

---

## 20. Prerequisites & next steps

**Prerequisites covered? You can:**
- Vectorize a Python loop into NumPy.
- Choose dtype that costs minimum memory while preserving correctness.
- Read parquet with column projection and predicate pushdown.
- Clean a messy CSV and write a reusable cleaner.
- Group, transform, and pivot data without leaving vectorized code.
- Decide between pandas, Polars, and DuckDB for a given task.
- Build publication-quality plots with the matplotlib OO API.

**Next steps in the bible:**
- **Module 3 — Databases.** Persisting and querying the data you've now learned to manipulate.
- **Module 4 — FastAPI.** Serving it as APIs.
- **Module 7 — Classical ML.** Where every tool here becomes a feature pipeline.

**External study (only if you want depth on this module):**
- *Python for Data Analysis, 3rd ed.* (Wes McKinney, the creator of pandas).
- The Polars User Guide (free, online — better than most books).
- *Fundamentals of Data Visualization* (Wilke) — free online, the best modern viz reference.
- NumPy and matplotlib official docs are excellent — read them before tutorials.

---

*End of Module 2. Module 3 covers SQLite, MySQL, SQLAlchemy 2.x, and Redis — same structure, 35+ problems.*
