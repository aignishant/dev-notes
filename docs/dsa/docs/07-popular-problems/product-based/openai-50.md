# OpenAI — 50 most-asked questions

> The 50 problems OpenAI (ChatGPT, API, fine-tuning, Sora) has asked most often. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">OpenAI</span> &nbsp; <span class="phase-status phase-done">Phase 8 — Company list</span>

---

## 🏢 What interviewing at OpenAI is like

| Round | Length | Focus |
|---|---|---|
| **Recruiter screen** | 30 min | Background + safety / mission alignment. |
| **Tech phone screen** | 90 min | One real engineering problem (not a trick LC). |
| **OA / take-home** | ~3 hr | Build a small, self-contained system. |
| **Onsite — coding ×2** | 60 min each | Pragmatic problems, often ML-systems flavored. |
| **Onsite — system design** | 60 min | "Design ChatGPT serving" or "Design RLHF feedback loop." |
| **Onsite — research / domain** | 45-60 min | If applicable: tokenization, attention math, RL basics. |
| **Onsite — manager / mission** | 45 min | Behavioral + AGI safety alignment. |

**OpenAI style**: research-product hybrid. Bias toward **practical engineering on big, messy, fast-moving systems**. Tokenization, LLM serving, retrieval-augmented generation come up. Mission round is real — they care that you'd push back on unsafe deployment.

---

## 🎯 What OpenAI tests

| Signal | Where | How to show |
|---|---|---|
| Pragmatic engineering | Coding + take-home | Working > clever; tests + README. |
| ML systems instinct | Design | Batching, KV cache, paged attention, autoscaling. |
| Numerical sense | Coding | When asked, reason about FP precision, overflow. |
| Mission alignment | Manager | Concrete view on safe deployment. |

---

## 🧩 Patterns OpenAI loves

| Pattern | Frequency | Why |
|---|---|---|
| **Hash + sliding window** | ⭐⭐⭐⭐⭐ | Tokenization, dedup. |
| **Trie + DFS** | ⭐⭐⭐⭐ | BPE, prefix tokenizers. |
| **DP** | ⭐⭐⭐⭐ | Beam search, edit-distance for evals. |
| **Heap + K-way** | ⭐⭐⭐⭐ | Top-k token sampling, log-prob merging. |
| **Concurrency** | ⭐⭐⭐ | Inference batchers, request queues. |
| **Design for scale** | ⭐⭐⭐⭐⭐ | Inference serving is the dominant theme. |

---

## 📋 The 50 questions

### Arrays & strings (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 3 | Group Anagrams | <span class="diff-medium">Medium</span> | Hash | 🚧 |
| 4 | Edit Distance | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |
| 5 | Longest Palindromic Substring | <span class="diff-medium">Medium</span> | Expand center | 🚧 |
| 6 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 7 | Minimum Window Substring | <span class="diff-hard">Hard</span> | Sliding window | 🚧 |
| 8 | Rolling Hash (Rabin-Karp) | <span class="diff-medium">Medium</span> | Hash | 📝 (see [Netflix 50](netflix-50.md)) |
| 9 | Longest Common Subsequence | <span class="diff-medium">Medium</span> | 2D DP | 🚧 |
| 10 | Maximum Subarray | <span class="diff-medium">Medium</span> | Kadane | [✅](../../02-data-structures/arrays/01-array-basics.md) |

### Linked lists (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 11 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 12 | Merge K Sorted Lists | <span class="diff-hard">Hard</span> | Heap | 🚧 |
| 13 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |

### Trees (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 14 | LCA of Binary Tree | <span class="diff-medium">Medium</span> | Post-order | 🚧 |
| 15 | Validate BST | <span class="diff-medium">Medium</span> | DFS bounds | 🚧 |
| 16 | Serialize / Deserialize | <span class="diff-hard">Hard</span> | BFS | 🚧 |
| 17 | Range Sum BST | <span class="diff-easy">Easy</span> | DFS + prune | 🚧 |

### Graphs (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 18 | Number of Islands | <span class="diff-medium">Medium</span> | DFS | 🚧 |
| 19 | Course Schedule | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 20 | Word Ladder | <span class="diff-hard">Hard</span> | BFS | 🚧 |
| 21 | Network Delay Time | <span class="diff-medium">Medium</span> | Dijkstra | 📝 (see [Uber 50](uber-50.md)) |

### Heap / Top-K (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 22 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap | [✅](../../04-patterns/12-top-k-elements.md) |
| 23 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | [✅](../../04-patterns/09-two-heaps.md) |
| 24 | Top-K Logits Sampling | <span class="diff-medium">Medium</span> | Heap | 📝 |
| 25 | Beam Search Top-K Hypotheses | <span class="diff-hard">Hard</span> | Heap + DP | 📝 |
| 26 | Merge K Token Streams | <span class="diff-hard">Hard</span> | Heap | 🚧 |

### Trie / strings (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 27 | Implement Trie | <span class="diff-medium">Medium</span> | Trie | [✅](../../05-advanced/01-tries.md) |
| 28 | Word Search II | <span class="diff-hard">Hard</span> | Trie + DFS | 🚧 |
| 29 | BPE Tokenizer (mini) | <span class="diff-hard">Hard</span> | Greedy merges | 📝 |
| 30 | Longest Word in Dict | <span class="diff-medium">Medium</span> | Trie | 🚧 |

### DP (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 31 | Climbing Stairs | <span class="diff-easy">Easy</span> | Fib DP | 🚧 |
| 32 | Coin Change | <span class="diff-medium">Medium</span> | Unbounded knapsack | 🚧 |
| 33 | Word Break | <span class="diff-medium">Medium</span> | DP | 🚧 |
| 34 | Longest Increasing Subsequence | <span class="diff-medium">Medium</span> | DP + BS | 🚧 |
| 35 | Decode Ways | <span class="diff-medium">Medium</span> | DP | 🚧 |

### Search & sort (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 36 | Search in Rotated Sorted Array | <span class="diff-medium">Medium</span> | Modified BS | 🚧 |
| 37 | Median of Two Sorted Arrays | <span class="diff-hard">Hard</span> | BS partition | 🚧 |
| 38 | Find Peak Element | <span class="diff-medium">Medium</span> | BS variant | 🚧 |

### Concurrency (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 39 | Bounded Blocking Queue | <span class="diff-medium">Medium</span> | Lock + cond var | 🚧 |
| 40 | Inference Request Batcher | <span class="diff-hard">Hard</span> | Latency-bounded batch | 📝 |
| 41 | Token Streamer | <span class="diff-medium">Medium</span> | Generator + queue | 🚧 |

### Design (9)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 42 | Design ChatGPT Serving | <span class="diff-hard">Hard</span> | Batching + KV cache | 📝 |
| 43 | Design RAG Pipeline | <span class="diff-hard">Hard</span> | Embed + ANN + LLM | 🚧 |
| 44 | Design Rate Limiter (per-user) | <span class="diff-medium">Medium</span> | Token bucket | 🚧 |
| 45 | Design Conversation Memory | <span class="diff-medium">Medium</span> | Sliding context + summary | 🚧 |
| 46 | Design Plugin Framework | <span class="diff-hard">Hard</span> | Tool-calling protocol | 🚧 |
| 47 | Design Eval Harness | <span class="diff-hard">Hard</span> | Sample + judge + ELO | 🚧 |
| 48 | Design Fine-Tune Job Manager | <span class="diff-hard">Hard</span> | Queue + GPU pool | 🚧 |
| 49 | Design Embedding Cache | <span class="diff-medium">Medium</span> | LRU + hash key | 🚧 |
| 50 | Design Safety Classifier Pipeline | <span class="diff-hard">Hard</span> | Pre + post inference filter | 🚧 |

---

## 🔬 Three deep-dives

### Deep-dive 1 — Inference Request Batcher

??? question "Story: GPU does best with batch size 32. Single users send one request at a time. Bridge them: collect requests for up to 10ms, then batch."

    Latency-bounded micro-batching. Two triggers fire the batch: (1) batch full, (2) timeout reached. Result is sent back per-request.

```python
import threading
import queue
import time
from dataclasses import dataclass

@dataclass
class Req:
    payload: dict
    out: queue.Queue  # length-1 queue for the response

class Batcher:
    def __init__(self, max_batch: int = 32, max_wait_ms: float = 10.0):
        self.max_batch = max_batch
        self.max_wait = max_wait_ms / 1000.0
        self.q: queue.Queue[Req] = queue.Queue()
        self.stop = False
        threading.Thread(target=self._loop, daemon=True).start()

    def submit(self, payload: dict) -> dict:
        out: queue.Queue = queue.Queue(1)
        self.q.put(Req(payload, out))
        return out.get()

    def _loop(self) -> None:
        while not self.stop:
            batch: list[Req] = []
            deadline = time.monotonic() + self.max_wait
            while len(batch) < self.max_batch:
                timeout = deadline - time.monotonic()
                if timeout <= 0:
                    break
                try:
                    batch.append(self.q.get(timeout=timeout))
                except queue.Empty:
                    break
            if batch:
                self._run(batch)

    def _run(self, batch: list[Req]) -> None:
        # placeholder model.forward(batch)
        for r in batch:
            r.out.put({"echo": r.payload})
```

??? abstract "Complexity"

    Bounded latency = `max_wait_ms`. Throughput scales with batch size up to GPU saturation.

??? tip "OpenAI follow-up: 'requests have different sequence lengths — what about KV cache?'"

    Continuous batching (vLLM-style): allow new requests to **join an in-flight batch** between decoder steps, sharing the KV cache via paged attention. Throughput up 10× over naive batching at the cost of much more bookkeeping.

---

### Deep-dive 2 — Mini BPE Tokenizer

??? question "Story: implement byte-pair encoding. Repeatedly merge the most frequent adjacent pair until vocab size = N."

    Start from byte-level tokens. Count adjacent pairs across the corpus, pick the most frequent, **replace** it with a new merged token. Repeat.

```python
from collections import Counter

def train_bpe(corpus: list[str], vocab_size: int) -> tuple[list[str], list[tuple[str, str]]]:
    # tokenise to characters; vocab starts with raw chars
    splits = [list(word) for word in corpus]
    vocab: list[str] = sorted({c for word in splits for c in word})
    merges: list[tuple[str, str]] = []

    while len(vocab) < vocab_size:
        pair_counts: Counter[tuple[str, str]] = Counter()
        for split in splits:
            for i in range(len(split) - 1):
                pair_counts[(split[i], split[i + 1])] += 1
        if not pair_counts:
            break
        best, _ = pair_counts.most_common(1)[0]
        merges.append(best)
        vocab.append(best[0] + best[1])

        # apply merge
        new_splits: list[list[str]] = []
        for split in splits:
            new_split: list[str] = []
            i = 0
            while i < len(split):
                if i < len(split) - 1 and (split[i], split[i + 1]) == best:
                    new_split.append(split[i] + split[i + 1])
                    i += 2
                else:
                    new_split.append(split[i])
                    i += 1
            new_splits.append(new_split)
        splits = new_splits
    return vocab, merges
```

??? abstract "Complexity"

    Naive: O(V · N) where V = target vocab, N = corpus size. Real impl uses a heap of pair counts and a per-position update on merge to drop a factor of N.

??? tip "OpenAI follow-up: 'how do you tokenize new text once trained?'"

    Greedy left-to-right matching against the merge list (in training order): start from chars, repeatedly apply the **earliest** applicable merge until no more apply. Or use a regex to pre-segment + a Trie of merges for speed.

---

### Deep-dive 3 — Design ChatGPT Serving

??? question "Story: serve a 70B param model to 100M users. Cold path = first token. Hot path = subsequent tokens via KV cache."

    Three-tier architecture: **gateway** (auth, rate limit, routing) → **scheduler** (batching, KV cache, GPU placement) → **model workers** (sharded by tensor parallelism). Streaming via server-sent events.

```python
# Sketch — orchestration only, not a full impl
from dataclasses import dataclass, field
from queue import Queue

@dataclass
class GenRequest:
    user_id: str
    prompt_tokens: list[int]
    max_tokens: int = 256
    out_stream: Queue = field(default_factory=Queue)
    kv_cache_id: str | None = None

class Scheduler:
    def __init__(self, n_gpu_workers: int):
        self.workers = [Queue() for _ in range(n_gpu_workers)]
        self.next_worker = 0

    def submit(self, req: GenRequest) -> Queue:
        # least-loaded routing in real impl
        worker_q = self.workers[self.next_worker]
        self.next_worker = (self.next_worker + 1) % len(self.workers)
        worker_q.put(req)
        return req.out_stream
```

??? abstract "Complexity"

    Throughput: tokens/sec/GPU = batch · (model FLOPs / GPU FLOPs)⁻¹. Latency: time-to-first-token + (tokens · per-token-latency).

??? tip "OpenAI follow-up: 'what about a 32k context user filling up GPU memory?'"

    Paged attention: split KV cache into fixed-size pages, allocate per-token. Long contexts spill to neighbouring GPUs or get **prefix-cached** if the conversation reuses a system prompt across many users.

---

## 🛡️ Day-of tips

- **Read about LLM serving**: vLLM continuous batching, paged attention, speculative decoding, KV cache, prefix caching. Vocabulary alone helps.
- **Mission round**: have a concrete take on a deployment safety question (e.g., should ChatGPT refuse certain medical advice?). Stake a position.
- **Take-home**: tests, README, and trade-off doc. Better-engineered submission > more features.
- **Numbers**: 70B params × 2 bytes = 140 GB; one A100 has 80 GB. Tensor parallelism is forced.
