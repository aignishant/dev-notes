# Anthropic — 50 most-asked questions

> The 50 problems Anthropic (Claude, Claude Code, Constitutional AI, Computer Use) has asked most often. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">Anthropic</span> &nbsp; <span class="phase-status phase-done">Phase 8 — Company list</span>

---

## 🏢 What interviewing at Anthropic is like

| Round | Length | Focus |
|---|---|---|
| **Recruiter screen** | 30 min | Background + safety / mission alignment. |
| **Tech phone screen** | 60-90 min | Pragmatic engineering problem with discussion. |
| **Take-home** | ~3-5 hr | Build a real, useful tool — they grade craft + judgment. |
| **Onsite — coding ×2** | 60 min each | Real-world flavored, often LLM-systems. |
| **Onsite — system design** | 60 min | Inference infra, agent orchestration, evals. |
| **Onsite — values / safety** | 45-60 min | Multiple rounds on safety mindset, careful thinking, cooperative work. |
| **Onsite — manager** | 45 min | Project deep-dive. |

**Anthropic style**: deeply mission-driven (AI safety + helpful, honest, harmless), unusually heavy emphasis on **careful thinking** and **values fit**. Take-home is graded on judgment as much as code. Slower / more thoughtful pace than typical SF tech. Multiple values rounds.

---

## 🎯 What Anthropic tests

| Signal | Where | How to show |
|---|---|---|
| Careful thinking | All | Surface assumptions, name trade-offs, push back on flawed problem statements. |
| Engineering judgment | Take-home | Right scope, right tests, right docs. |
| Safety mindset | Values rounds | Concrete view on alignment, deployment caution. |
| LLM systems instinct | Coding + design | Tools, agents, evals, retrieval. |

---

## 🧩 Patterns Anthropic loves

| Pattern | Frequency | Why |
|---|---|---|
| **Hash + sliding window** | ⭐⭐⭐⭐⭐ | Token / log work. |
| **Trie + DFS** | ⭐⭐⭐⭐ | Tool routing, prefix dispatch. |
| **DP** | ⭐⭐⭐⭐ | Beam search, edit-distance evals. |
| **Heap K-way** | ⭐⭐⭐⭐ | Top-k sampling, scoring. |
| **Concurrency** | ⭐⭐⭐⭐ | Inference batchers, agent loops. |
| **Design + judgment** | ⭐⭐⭐⭐⭐ | Both technical and ethical. |

---

## 📋 The 50 questions

### Arrays & strings (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 3 | Edit Distance | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |
| 4 | Group Anagrams | <span class="diff-medium">Medium</span> | Hash | 🚧 |
| 5 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 6 | Minimum Window Substring | <span class="diff-hard">Hard</span> | Sliding window | 🚧 |
| 7 | Longest Common Subsequence | <span class="diff-medium">Medium</span> | 2D DP | 🚧 |
| 8 | Maximum Subarray | <span class="diff-medium">Medium</span> | Kadane | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 9 | Rolling Hash | <span class="diff-medium">Medium</span> | Hash | 📝 (see [Netflix 50](netflix-50.md)) |
| 10 | Subarray Sum Equals K | <span class="diff-medium">Medium</span> | Prefix + hash | 🚧 |

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
| 17 | Path Sum II | <span class="diff-medium">Medium</span> | DFS + backtrack | 🚧 |

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
| 24 | Beam Search | <span class="diff-hard">Hard</span> | Heap + DP | 📝 |
| 25 | Top-K Logits Sampling | <span class="diff-medium">Medium</span> | Heap / partial sort | 🚧 |
| 26 | Constrained Decoding (top-p) | <span class="diff-medium">Medium</span> | Sort + cum-sum | 🚧 |

### Trie / strings (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 27 | Implement Trie | <span class="diff-medium">Medium</span> | Trie | [✅](../../05-advanced/01-tries.md) |
| 28 | Word Search II | <span class="diff-hard">Hard</span> | Trie + DFS | 🚧 |
| 29 | Tool Routing Trie | <span class="diff-medium">Medium</span> | Trie | 📝 |
| 30 | Longest Word in Dict | <span class="diff-medium">Medium</span> | Trie | 🚧 |

### DP (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 31 | Climbing Stairs | <span class="diff-easy">Easy</span> | Fib DP | 🚧 |
| 32 | Coin Change | <span class="diff-medium">Medium</span> | Unbounded knapsack | 🚧 |
| 33 | Word Break | <span class="diff-medium">Medium</span> | DP | 🚧 |
| 34 | Decode Ways | <span class="diff-medium">Medium</span> | DP | 🚧 |
| 35 | Longest Increasing Subsequence | <span class="diff-medium">Medium</span> | DP + BS | 🚧 |

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
| 40 | Inference Request Batcher | <span class="diff-hard">Hard</span> | Latency-bounded batch | 📝 (see [OpenAI 50](openai-50.md)) |
| 41 | Agent Loop with Cancellation | <span class="diff-medium">Medium</span> | Cooperative cancel | 🚧 |

### Design / agents (9)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 42 | Design Claude Serving | <span class="diff-hard">Hard</span> | Batching + KV cache | 📝 |
| 43 | Design Tool-Calling Agent | <span class="diff-hard">Hard</span> | Loop + tool registry | 📝 |
| 44 | Design RAG with Citations | <span class="diff-hard">Hard</span> | Embed + ANN + grounded | 🚧 |
| 45 | Design Eval Harness | <span class="diff-hard">Hard</span> | Sample + judge + ELO | 🚧 |
| 46 | Design Constitutional Filter | <span class="diff-hard">Hard</span> | Pre + post inference filter | 🚧 |
| 47 | Design Cost Tracker per User | <span class="diff-medium">Medium</span> | Token meter + bucket | 🚧 |
| 48 | Design Conversation Compaction | <span class="diff-medium">Medium</span> | Summary + sliding | 🚧 |
| 49 | Design Computer-Use Agent | <span class="diff-hard">Hard</span> | Screenshot + action loop | 🚧 |
| 50 | Design Sandbox for Code Exec | <span class="diff-hard">Hard</span> | Container + resource cap | 🚧 |

---

## 🔬 Three deep-dives

### Deep-dive 1 — Tool-Calling Agent Loop

??? question "Story: model can call tools (search, code, file_read). Build the agent loop: model → tool call → result → model … until model returns a final answer."

    The loop terminates when the model emits no tool call. Bound iterations to avoid runaways. Stream partial outputs back to user.

```python
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class ToolCall:
    name: str
    args: dict[str, Any]

@dataclass
class ModelOutput:
    text: str
    tool_call: ToolCall | None  # None means final answer

ToolFn = Callable[[dict[str, Any]], str]

def run_agent(
    prompt: str,
    model: Callable[[list[dict]], ModelOutput],
    tools: dict[str, ToolFn],
    max_iters: int = 20,
) -> str:
    history: list[dict] = [{"role": "user", "content": prompt}]
    for _ in range(max_iters):
        out = model(history)
        history.append({"role": "assistant", "content": out.text, "tool_call": out.tool_call})
        if out.tool_call is None:
            return out.text
        if out.tool_call.name not in tools:
            history.append({"role": "tool", "name": out.tool_call.name,
                            "content": "ERROR: unknown tool"})
            continue
        try:
            result = tools[out.tool_call.name](out.tool_call.args)
        except Exception as e:
            result = f"ERROR: {e}"
        history.append({"role": "tool", "name": out.tool_call.name, "content": result})
    raise RuntimeError("agent exceeded max_iters")
```

??? abstract "Complexity"

    O(I) model calls + O(I) tool calls where I ≤ `max_iters`.

??? tip "Anthropic follow-up: 'what if a tool call should be cancellable mid-execution?'"

    Pass a `threading.Event` cancellation token into each tool. Tool implementations check it cooperatively. The agent loop respects user-initiated cancel by setting the event before the next iteration.

---

### Deep-dive 2 — Conversation Compaction

??? question "Story: Claude has a 200k context window, but conversations can exceed that. Build a compaction step that preserves meaning."

    Threshold-trigger: when token budget exceeds X, summarise the **oldest** N messages into a single system note, drop them, keep the recent tail. Important: never summarise tool outputs that the recent assistant turn referenced.

```python
from dataclasses import dataclass

@dataclass
class Msg:
    role: str
    content: str
    tokens: int  # precomputed

class Compactor:
    def __init__(self, budget_tokens: int, summarise_fn):
        self.budget = budget_tokens
        self.summarise = summarise_fn  # callable list[Msg] -> str

    def compact(self, history: list[Msg], keep_recent: int = 8) -> list[Msg]:
        total = sum(m.tokens for m in history)
        if total <= self.budget:
            return history

        head = history[:-keep_recent]
        tail = history[-keep_recent:]
        if not head:
            return tail  # nothing safe to drop

        summary_text = self.summarise(head)
        summary = Msg(role="system",
                      content=f"[Earlier conversation summary]\n{summary_text}",
                      tokens=len(summary_text) // 4)
        return [summary] + tail
```

??? abstract "Complexity"

    O(N) to scan; the summariser is the dominant cost (one extra LLM call).

??? tip "Anthropic follow-up: 'how do you avoid losing tool-call context in the summary?'"

    Tag tool outputs with stable IDs. The summariser is instructed to preserve tool IDs verbatim if they're cited in the kept tail. Alternatively, **never** drop messages that any retained turn references.

---

### Deep-dive 3 — Constitutional Filter (pre + post)

??? question "Story: prevent the model from outputting harmful content. Layer filters before AND after the model."

    Pre-filter rejects clearly disallowed prompts cheaply. Post-filter inspects model output and either passes, regenerates, or refuses. Use cheap classifiers for the gate; reserve LLM-judge for ambiguous cases.

```python
from typing import Callable

class Constitution:
    def __init__(self, pre_classifier: Callable[[str], float],
                 post_classifier: Callable[[str], float],
                 threshold: float = 0.8):
        self.pre = pre_classifier
        self.post = post_classifier
        self.threshold = threshold

    def screen_prompt(self, user_text: str) -> tuple[bool, str]:
        if self.pre(user_text) > self.threshold:
            return False, "I can't help with that."
        return True, ""

    def screen_response(self, model_text: str) -> tuple[bool, str]:
        if self.post(model_text) > self.threshold:
            return False, "I'm going to decline this answer."
        return True, model_text
```

??? abstract "Complexity"

    O(1) extra cost per turn for the cheap classifiers. LLM-judge fallback adds one model call.

??? tip "Anthropic follow-up: 'a borderline case slipped through. How do you find similar ones?'"

    Embed the slipped case, retrieve nearest neighbours in your eval set + log corpus, label them, retrain the classifier. Continuous loop, never a one-shot fix.

---

## 🛡️ Day-of tips

- **Surface assumptions out loud**. "I'm assuming the input is well-formed; should I handle malformed?" — this is the single thing they grade hardest.
- **Push back when warranted**. If the problem statement is ambiguous, ask. If the suggested approach has a flaw, name it.
- **Take-home**: one well-tested, well-documented small thing > a sprawling unfinished bigger thing.
- **Values round**: prepare a position on (a) when you'd block a launch, (b) how you'd handle a model misbehaviour incident, (c) what 'helpful, honest, harmless' means concretely.
- **Be calm**. The bar is high but the rooms are unhurried — they'd rather see you think than rush.
