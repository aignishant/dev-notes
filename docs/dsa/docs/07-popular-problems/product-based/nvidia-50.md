# NVIDIA — 50 most-asked questions

> The 50 problems NVIDIA (CUDA, GPUs, deep-learning, autonomous, Omniverse) has asked most often. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">NVIDIA</span> &nbsp; <span class="phase-status phase-done">Phase 8 — Company list</span>

---

## 🏢 What interviewing at NVIDIA is like

| Round | Length | Focus |
|---|---|---|
| **Recruiter screen** | 30 min | Background. |
| **Tech phone screen** | 60 min | Coding (C++ heavy for kernel teams). |
| **Onsite — coding ×2** | 60 min each | Algorithms + low-level / GPU thinking. |
| **Onsite — domain** | 60 min | CUDA / parallel algorithms / numerical stability — depends on team. |
| **Onsite — system design** | 60 min | Could be deep learning serving, simulator, or HW/SW interface. |
| **Onsite — manager** | 45 min | Project deep-dive. |

**NVIDIA style**: hardware-aware, performance-obsessed. C++ over Python for many teams. Bias toward **how does this map to the GPU**: warps, shared memory, memory coalescing. Deep learning teams ask about kernels, mixed precision, layer fusion. Slower interview pipeline (6-8 weeks).

---

## 🎯 What NVIDIA tests

| Signal | Where | How to show |
|---|---|---|
| Performance instinct | All | Cache locality, branch divergence, memory bandwidth. |
| Numerical sense | Domain | FP16 / BF16 / TF32 trade-offs, overflow, NaN. |
| Parallel algorithms | Domain | Reduction, scan, sort, histogram on GPU. |
| C++ fluency | Most teams | RAII, move semantics, templates. |

---

## 🧩 Patterns NVIDIA loves

| Pattern | Frequency | Why |
|---|---|---|
| **Bit / SIMD thinking** | ⭐⭐⭐⭐⭐ | Warp-level tricks, masks. |
| **Hash + sliding window** | ⭐⭐⭐⭐ | Standard mediums. |
| **Heap / partial sort** | ⭐⭐⭐⭐ | Top-K (often as a parallel reduction). |
| **DP** | ⭐⭐⭐⭐ | Layer fusion cost models. |
| **Graph BFS** | ⭐⭐⭐⭐ | Connectivity, dependency analysis. |
| **DSA + numerical** | ⭐⭐⭐⭐ | Stable mean, Kahan summation. |

---

## 📋 The 50 questions

### Arrays & strings (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Maximum Subarray | <span class="diff-medium">Medium</span> | Kadane | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 3 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 4 | Sliding Window Maximum | <span class="diff-hard">Hard</span> | Monotonic deque | 🚧 |
| 5 | Median of Two Sorted Arrays | <span class="diff-hard">Hard</span> | BS partition | 🚧 |
| 6 | Subarray Sum Equals K | <span class="diff-medium">Medium</span> | Prefix + hash | 🚧 |
| 7 | Set Matrix Zeroes | <span class="diff-medium">Medium</span> | In-place markers | 🚧 |
| 8 | Spiral Matrix | <span class="diff-medium">Medium</span> | Layer-by-layer | 🚧 |
| 9 | Rotate Image | <span class="diff-medium">Medium</span> | Transpose + reverse | 🚧 |
| 10 | Find Duplicate | <span class="diff-medium">Medium</span> | Floyd's | 🚧 |

### Linked lists (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 11 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 12 | Merge K Sorted Lists | <span class="diff-hard">Hard</span> | Heap | 🚧 |
| 13 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |

### Trees (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 14 | Validate BST | <span class="diff-medium">Medium</span> | DFS bounds | 🚧 |
| 15 | LCA of Binary Tree | <span class="diff-medium">Medium</span> | Post-order | 🚧 |
| 16 | Serialize / Deserialize | <span class="diff-hard">Hard</span> | BFS | 🚧 |
| 17 | Binary Tree Right Side View | <span class="diff-medium">Medium</span> | BFS | 🚧 |

### Graphs (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 18 | Number of Islands | <span class="diff-medium">Medium</span> | DFS | 🚧 |
| 19 | Course Schedule II | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 20 | Network Delay Time | <span class="diff-medium">Medium</span> | Dijkstra | 📝 (see [Uber 50](uber-50.md)) |
| 21 | Connected Components in Grid | <span class="diff-medium">Medium</span> | DSU / BFS | 🚧 |
| 22 | Compute Graph DAG Schedule | <span class="diff-hard">Hard</span> | Topo + critical path | 📝 (see [Databricks 50](databricks-50.md)) |

### Heap / Top-K (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 23 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap | [✅](../../04-patterns/12-top-k-elements.md) |
| 24 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | [✅](../../04-patterns/09-two-heaps.md) |
| 25 | K Closest Points | <span class="diff-medium">Medium</span> | Heap | 🚧 |
| 26 | Parallel Top-K | <span class="diff-hard">Hard</span> | Reduce + merge | 📝 |

### DP (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 27 | Climbing Stairs | <span class="diff-easy">Easy</span> | Fib DP | 🚧 |
| 28 | Coin Change | <span class="diff-medium">Medium</span> | Unbounded knapsack | 🚧 |
| 29 | Edit Distance | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |
| 30 | LIS | <span class="diff-medium">Medium</span> | DP + BS | 🚧 |
| 31 | Burst Balloons | <span class="diff-hard">Hard</span> | Interval DP | 🚧 |

### Bit / numerics (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 32 | Single Number | <span class="diff-easy">Easy</span> | XOR | 🚧 |
| 33 | Number of 1 Bits | <span class="diff-easy">Easy</span> | Brian Kernighan | 🚧 |
| 34 | Reverse Bits | <span class="diff-easy">Easy</span> | Bit manipulation | 🚧 |
| 35 | Pow(x, n) | <span class="diff-medium">Medium</span> | Binary exp | 📝 (see [Microsoft 50](microsoft-50.md)) |
| 36 | Kahan Summation | <span class="diff-medium">Medium</span> | Compensated sum | 📝 |

### Search & sort (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 37 | Search in Rotated Sorted Array | <span class="diff-medium">Medium</span> | Modified BS | 🚧 |
| 38 | Sort Colors | <span class="diff-medium">Medium</span> | Dutch flag | 🚧 |
| 39 | Find Peak Element | <span class="diff-medium">Medium</span> | BS variant | 🚧 |

### Concurrency / parallel (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 40 | Parallel Reduction (sum) | <span class="diff-medium">Medium</span> | Tree reduce | 📝 |
| 41 | Parallel Prefix Sum (scan) | <span class="diff-hard">Hard</span> | Hillis-Steele | 🚧 |
| 42 | Parallel Histogram | <span class="diff-medium">Medium</span> | Atomic / privatised | 🚧 |
| 43 | Bounded Blocking Queue | <span class="diff-medium">Medium</span> | Lock + cond var | 🚧 |

### Design (7)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 44 | Design DL Inference Server | <span class="diff-hard">Hard</span> | Batching + GPU pool | 🚧 |
| 45 | Design Layer Fusion Optimiser | <span class="diff-hard">Hard</span> | DAG + cost model | 🚧 |
| 46 | Design Mixed-Precision Trainer | <span class="diff-hard">Hard</span> | Loss scaling + master copy | 🚧 |
| 47 | Design GPU Memory Allocator | <span class="diff-hard">Hard</span> | Slab + free-list | 🚧 |
| 48 | Design Profiler | <span class="diff-hard">Hard</span> | Trace + flamegraph | 🚧 |
| 49 | Design Driver Update System | <span class="diff-medium">Medium</span> | Versioned + rollback | 🚧 |
| 50 | Design Sim → Real Pipeline | <span class="diff-hard">Hard</span> | Domain randomisation | 🚧 |

---

## 🔬 Three deep-dives

### Deep-dive 1 — Parallel Reduction (sum)

??? question "Story: sum 1B floats on a GPU. Naive: each thread atomic-adds to a global = serialised contention. Better: tree reduction in shared memory."

    Each thread block reduces its chunk in shared memory using a tree pattern. One value per block goes back to global; a final block reduces those.

```python
# Pythonic sketch — pretend `block` is a CUDA block of T threads,
# `shared[T]` is shared memory.

def block_reduce(block_data: list[float]) -> float:
    """Reduce inside a block of T (power-of-two) threads."""
    shared = list(block_data)
    T = len(shared)
    stride = T // 2
    while stride > 0:
        # Each thread tid in [0, stride) does shared[tid] += shared[tid + stride]
        for tid in range(stride):
            shared[tid] += shared[tid + stride]
        stride //= 2
    return shared[0]

def grid_reduce(data: list[float], block_size: int = 256) -> float:
    block_sums: list[float] = []
    for start in range(0, len(data), block_size):
        block_sums.append(block_reduce(data[start : start + block_size]))
    return sum(block_sums)  # final reduction
```

??? abstract "Complexity"

    O(N) work, O(log T) depth per block. Memory traffic dominates — bandwidth-bound, not compute-bound.

??? tip "NVIDIA follow-up: 'how do you make the inner loop faster than the textbook version?'"

    Each thread does 2-4 loads up front + register-level adds (loop unrolling). Use **warp shuffles** (`__shfl_down_sync`) for the last 32 elements — no shared memory needed. This roughly doubles throughput.

---

### Deep-dive 2 — Kahan Summation

??? question "Story: summing 1B FP32 values gives wrong results due to round-off. Fix it without going to FP64."

    Maintain a running compensation term `c` for the lost low-order bits. Add `(value - c)` to `sum`; recover the round-off error and feed it forward.

```python
def kahan_sum(values: list[float]) -> float:
    s = 0.0
    c = 0.0  # compensation
    for v in values:
        y = v - c
        t = s + y       # losing low-order bits of y
        c = (t - s) - y # what we lost (sign-flipped)
        s = t
    return s
```

??? example "Why it works"

    `(t - s)` is the part of `y` that *did* fit. Subtracting `y` gives the negative of what was lost. Adding that to the next `y` recovers it.

??? abstract "Complexity"

    O(N) time, O(1) state. ~4× the FLOPs of a naive sum, but provably stable.

??? tip "NVIDIA follow-up: 'parallelise it across a GPU'"

    Each thread runs a Kahan-summed local accumulator over its slice. Final reduction also uses Kahan. The improved version is **Neumaier's** which handles the case where `|s| < |y|`.

---

### Deep-dive 3 — Parallel Top-K

??? question "Story: pick top-K from 1B floats on the GPU."

    Per-block: each thread maintains a small min-heap of K. Block merges its threads' heaps. Grid merges block heaps in a final reduction.

```python
import heapq

def topk_thread(chunk: list[float], k: int) -> list[float]:
    heap: list[float] = []
    for v in chunk:
        if len(heap) < k:
            heapq.heappush(heap, v)
        elif v > heap[0]:
            heapq.heappushpop(heap, v)
    return heap

def topk_block(thread_results: list[list[float]], k: int) -> list[float]:
    merged: list[float] = []
    for tr in thread_results:
        for v in tr:
            if len(merged) < k:
                heapq.heappush(merged, v)
            elif v > merged[0]:
                heapq.heappushpop(merged, v)
    return merged

def topk_grid(blocks: list[list[float]], k: int) -> list[float]:
    return topk_block(blocks, k)
```

??? abstract "Complexity"

    O(N log K) total work, O(log B + log T) depth where B = blocks, T = threads.

??? tip "NVIDIA follow-up: 'K is small (~32) — there's a better way'"

    For small K, **bitonic top-K** sort is faster on GPU because it's branch-free and warp-friendly. For large K, **radix select** beats both.

---

## 🛡️ Day-of tips

- **Performance vocabulary fluency**: warp, occupancy, coalesced, shared mem, register pressure, bank conflicts.
- **C++ readiness**: even Python-track candidates should know the rule of three, virtual destructors, move semantics.
- **Numerical safety**: name FP16 / BF16 / FP32 / TF32 differences; know when one overflows / loses precision.
- **Cycle is slow**: 6-8 weeks is common. Don't take silence as rejection.
