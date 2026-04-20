# ⚡ Inference & Deployment

> **Q61–Q85 · 25 questions** on the hard part of LLMs — making them *actually serve at scale*. KV cache, paged attention, continuous batching, speculative decoding, quantization (GPTQ / AWQ / GGUF / FP8), vLLM vs TGI vs TensorRT-LLM, latency budgets, autoscaling, and the trade-offs that separate a demo from a production system.

---

## Q61. The two phases of LLM inference — prefill vs decode { #q61 }

Every LLM request has **two structurally different phases:**

**1. Prefill (compute-bound):** process the entire input prompt in one forward pass. All tokens are available, so the full sequence flows through the transformer in parallel — a single matrix multiply per layer over the whole prompt.

**2. Decode (memory-bound):** generate output tokens one at a time. Each new token requires a forward pass that reads the entire KV cache. You can only generate one token per forward pass because token $t+1$ depends on token $t$.

| Phase | Bottleneck | Scales with | Optimization lever |
|---|---|---|---|
| Prefill | FLOPs (GPU compute) | prompt length | FlashAttention, tensor parallel |
| Decode | Memory bandwidth | KV cache size | Quantization, paged attention, speculative decoding |

**Why this matters:**
- Prefill for 2k tokens on H100 ≈ 50–100 ms
- Decode at ~50–80 tokens/sec per request
- For a 500-token response, **decode dominates total latency.**

Understanding this split is the #1 thing that separates engineers who can reason about LLM inference from those who can't.

<div class="tip-box" markdown>
**Interviewer probe:** "Why is LLM inference memory-bound and not compute-bound?" Answer: because decode generates one token at a time, you're doing a tiny amount of matmul per token but reading GB of KV cache + weights. GPU FLOPs sit idle — the memory subsystem is the bottleneck. This is why quantization (less memory per param) and batching (amortize memory reads across requests) are the primary decode speedups.
</div>

---

## Q62. KV cache — what it stores and why it's huge { #q62 }

**Problem:** at decode step $t$, attention needs keys and values for all previous tokens $0, 1, \ldots, t-1$. Recomputing them from scratch every step would be $O(t^2)$ waste.

**Solution (KV cache):** store $K$ and $V$ for every past token in GPU memory. At step $t$, compute only $Q_t, K_t, V_t$ for the current token, append $K_t, V_t$ to the cache, run attention with the new $Q_t$ against the full $K, V$.

**Memory per token (per layer):**
$$\text{bytes} = 2 \times n_{\text{heads}} \times d_{\text{head}} \times \text{dtype\_bytes}$$

For Llama-3-70B: 80 layers, 64 heads, 128 head dim, BF16 (2 bytes):

$$80 \times 2 \times 64 \times 128 \times 2 = 2.6 \text{ MB per token}$$

A 32k-context request consumes ~80 GB of KV cache alone. That's larger than the model weights.

```python
# Conceptual pseudocode of cached decoding
k_cache = []  # per layer, shape (seq, heads, d_head)
v_cache = []
for t in range(max_new_tokens):
    q, k, v = compute_qkv(x_t)
    k_cache.append(k); v_cache.append(v)
    attn = softmax(q @ stack(k_cache).T / sqrt(d)) @ stack(v_cache)
    x_t = next_token_logits(attn)
```

**Reducing KV cache:**

| Technique | What it does | Savings |
|---|---|---|
| **MQA** (Multi-Query Attention) | All heads share one K,V | H× reduction |
| **GQA** (Grouped-Query Attention) | K,V heads grouped, fewer than Q heads | ~4-8× |
| **KV cache quantization** | Store K,V in INT8 / INT4 | 2-4× |
| **Sliding window attention** | Only last N tokens' KV | constant memory per token |
| **PagedAttention** | Non-contiguous KV blocks | eliminates fragmentation |

---

## Q63. PagedAttention and vLLM — the virtual memory trick { #q63 }

**Problem with naive KV cache:** you must allocate max-sequence-length buffers per request upfront, leading to massive memory fragmentation. If a request only generates 100 tokens but you reserved space for 2048, ~95% of that memory is wasted.

**PagedAttention** (Kwon et al. 2023, the foundation of vLLM): apply OS-style virtual memory to the KV cache.

- Divide KV cache into **fixed-size blocks** (e.g., 16 tokens).
- Each sequence's tokens are stored in non-contiguous blocks.
- A **block table** maps logical token positions → physical blocks.
- Attention kernel traverses the block table to gather K, V.

**Results:**
- Memory waste drops from ~60-80% to <4%.
- 2-4× throughput vs naive serving.
- Enables **prefix sharing** — multiple requests with the same system prompt can share KV blocks.

```python
# vLLM usage — the production standard in 2026
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Llama-3-70B-Instruct",
          tensor_parallel_size=4,
          gpu_memory_utilization=0.95,
          max_num_batched_tokens=8192)

sampling = SamplingParams(temperature=0.7, max_tokens=512, top_p=0.9)
outputs = llm.generate(prompts, sampling)
```

<div class="scenario" markdown>
**Scenario — you're getting OOMs at high QPS:** Your naive server allocates 4096-token KV buffers per request, serving 32 concurrent requests = 32 × 4096 × 2.6 MB = 340 GB. H100 only has 80 GB. Switch to vLLM → fragmentation drops, effective concurrency rises 3-4× on same hardware. This is the single highest-ROI change you can make for LLM serving.
</div>

---

## Q64. Continuous batching — why static batching wastes 90% of compute { #q64 }

**Static batching** (the naive way): wait for N requests, run them together, wait for *all* to finish before starting next batch. Problem: if one request generates 512 tokens and another generates 10, the batch waits for the long one. 90%+ of GPU cycles wasted.

**Continuous (in-flight) batching** (Orca paper, 2022): requests join and leave the batch **at the iteration level**, not the request level.

**Mechanism:**
1. At each decode iteration, check for finished requests → evict from batch.
2. Check incoming queue → add new requests to the batch if there's room.
3. Prefill and decode can be interleaved (or scheduled separately with chunked prefill).

**Result:** GPU utilization goes from 10-30% → 70-90%. Throughput jumps 4-10×.

**Every serious LLM serving framework** (vLLM, TGI, TensorRT-LLM, SGLang) does continuous batching. If your team still uses static batching, that's a 2-hour PR worth millions in GPU savings.

---

## Q65. Speculative decoding — 2-3× faster with math that feels like magic { #q65 }

**Core idea:** use a small "draft" model to propose $k$ tokens in one forward pass, then use the big "target" model to **verify** all $k$ in a single pass (not $k$ sequential passes).

**Algorithm:**
1. Draft model generates $k$ candidate tokens (takes ~1/10 of target's time).
2. Target model scores all $k$ candidates in *one* parallel forward pass.
3. Accept the longest prefix of draft tokens that matches what target would have generated (via rejection sampling).
4. If all $k$ accepted → you got $k$ tokens for one target pass (massive speedup).
5. If first one rejected → you got just 1 token from target. No loss.

**Key insight:** this preserves the **exact output distribution** of the target model. The math (rejection sampling) ensures sampled tokens are distributed identically to vanilla target decoding.

```
P_target(x) ≥ P_draft(x) · r(x), where r(x) = min(1, P_target(x)/P_draft(x))
```

If $r(x_i) < $ uniform random → reject, resample from $(P_{\text{target}} - P_{\text{draft}})_+$.

**Typical speedup:** 2-3× on real workloads. Higher when draft ≈ target (e.g., sharing architecture).

**Variants:**
- **Medusa heads** — train extra heads on the target model itself to predict tokens 2, 3, 4 ahead. No separate draft model needed.
- **EAGLE** — tree-of-drafts with feature-level prediction. SOTA as of 2026.
- **Lookahead decoding** — Jacobi iteration, no training required.

<div class="tip-box" markdown>
**Gotcha:** speculative decoding speedup depends on *draft acceptance rate*. A tiny, poorly-matched draft might achieve 30% acceptance → barely 1.3× speedup. A well-chosen draft (say, 7B drafting for 70B from same family) hits 70-80% acceptance → 2.5-3× speedup.
</div>

---

## Q66. Quantization for LLMs — GPTQ, AWQ, SmoothQuant, GGUF { #q66 }

**Why quantize:** the #1 lever for making big models fit and run fast. Each halving of precision roughly halves memory and doubles throughput.

| Method | Bits | Training? | Key technique | Best for |
|---|---|---|---|---|
| **GPTQ** | 4 | No (PTQ) | Layerwise optimal rounding via Hessian approximation | GPU serving, general purpose |
| **AWQ** | 4 | No (PTQ) | Per-channel scaling based on activation magnitudes | Edge + GPU, highest accuracy 4-bit |
| **SmoothQuant** | 8 (W8A8) | No | Migrate activation outliers → weights | H100/A100, best latency |
| **GGUF (k-quants)** | 2-8 | No | Mixed bit-width per block | CPU inference, llama.cpp |
| **FP8** | 8 (E4M3/E5M2) | Yes (QAT or scales) | Tensor-Core native | H100/B100 forward pass |
| **NF4** (QLoRA) | 4 | No | Information-theoretic quantile quantization | QLoRA fine-tuning |
| **BitNet / 1-bit LLMs** | 1.58 | Yes (from scratch) | Ternary weights {-1, 0, 1} | Future hardware |

**The outlier problem** (the reason naive INT8 fails on LLMs):

A few activation channels have 10-100× larger magnitudes than the rest. Uniform quantization gives them huge quantization error that ruins downstream layers.

**Solutions by method:**
- **GPTQ:** optimize quantization *per weight* using calibration data + inverse Hessian.
- **AWQ:** shift per-channel scale from activations to weights (weights are less sensitive).
- **SmoothQuant:** mathematically move outliers from A to W via $\text{diag}(s)^{-1}$ on act, $\text{diag}(s)$ on weight, preserves output.

```python
# AWQ quantization in practice
from awq import AutoAWQForCausalLM
model = AutoAWQForCausalLM.from_pretrained("meta-llama/Llama-3-70B-Instruct")
model.quantize(tokenizer, quant_config={"zero_point": True, "q_group_size": 128, "w_bit": 4})
model.save_quantized("llama3-70b-awq")
# Result: 35 GB model (down from 140 GB), ~1% benchmark drop
```

<div class="scenario" markdown>
**Scenario — serving 70B on 1×A100 (80 GB):** Full precision FP16 = 140 GB → won't fit. BF16 weights alone = 140 GB, still doesn't fit. Solution: AWQ 4-bit → 35 GB weights + ~10 GB for KV cache budget + 5 GB for overhead = 50 GB total. Fits with room for concurrency. Benchmark drop typically <2% on MMLU/HumanEval.
</div>

---

## Q67. FP8 and modern low-precision — the H100 sweet spot { #q67 }

**H100 Tensor Cores** native support two FP8 formats:

| Format | Exponent | Mantissa | Range | Use |
|---|---|---|---|---|
| **E4M3** | 4 | 3 | ±448 | Forward pass, weights |
| **E5M2** | 5 | 2 | ±57344 | Backward pass, gradients |

**Per-tensor scaling:** before casting BF16 → FP8, multiply by a scale chosen so the max absolute value fits in FP8's range. Store the scale per-tensor.

**Results:**
- FP8 training: ~2× throughput vs BF16 (paper-reported on GPT-175B).
- FP8 inference: ~2× throughput and ~2× memory savings. Very minor quality loss (<0.5% on most benchmarks).

**Software:**
- **NVIDIA Transformer Engine** handles FP8 casting/scaling automatically.
- **TensorRT-LLM** supports FP8 serving natively.
- **vLLM** added FP8 support in 2024.

**Should you use it?**
- H100/H200/B100: **yes**, if accuracy budget allows. Best throughput available.
- A100 and earlier: no FP8 hardware; stick with INT8 quantization.
- Training: FP8 for pretraining large models; BF16 for everything else.

---

## Q68. TensorRT-LLM vs vLLM vs TGI vs SGLang — picking a serving framework { #q68 }

| Framework | Sweet spot | Pros | Cons |
|---|---|---|---|
| **vLLM** | General-purpose GPU serving | Easiest setup, huge model support, fast OSS velocity | Less bleeding-edge perf than TRT-LLM |
| **TensorRT-LLM** | Max throughput on NVIDIA | Best raw performance, FP8, in-flight batching | Complex build, NVIDIA-only |
| **TGI** (Hugging Face) | HuggingFace ecosystem | Plug-and-play with HF, streaming, good monitoring | Slightly slower than vLLM lately |
| **SGLang** | Complex prompting flows | RadixAttention for prefix caching, structured generation | Newer, smaller community |
| **llama.cpp / Ollama** | CPU / edge / consumer GPU | GGUF format, CPU inference, Mac-friendly | Not server-grade throughput |
| **MLX** | Apple Silicon | Native Metal, good perf on M-series | Mac-only |

**Decision tree:**
- On NVIDIA H100 fleet, latency-sensitive → **TensorRT-LLM**.
- OSS-first team, fast iteration, NVIDIA/AMD → **vLLM**.
- Tight HF integration, adapters, streaming APIs → **TGI**.
- Heavy prefix sharing (chatbots with long system prompts) → **SGLang**.
- Laptop / Mac / edge → **llama.cpp / Ollama / MLX**.

```python
# Starting a vLLM OpenAI-compatible server
# python -m vllm.entrypoints.openai.api_server \
#   --model meta-llama/Llama-3-70B-Instruct \
#   --tensor-parallel-size 4 \
#   --quantization awq \
#   --max-model-len 32768 \
#   --gpu-memory-utilization 0.92 \
#   --enable-prefix-caching
```

---

## Q69. Tensor parallelism vs pipeline parallelism for inference { #q69 }

**Tensor parallelism (TP):** split individual matrices across GPUs. A matmul `(B, L, d) @ (d, d)` is split column-wise across N GPUs — each GPU does `(d, d/N)`, then all-reduce.

- **Latency:** adds NCCL all-reduce per transformer block. On NVLink, negligible; on PCIe, painful.
- **Scaling:** near-linear inside a node (NVLink). Degrades across nodes.
- **Use when:** model doesn't fit on one GPU *and* you have fast intra-node links.

**Pipeline parallelism (PP):** split *layers* across GPUs. GPU 0 holds layers 0-40, GPU 1 holds 41-80, etc.

- **Latency:** each request passes through all GPUs sequentially. Good for throughput (pipelined batches), bad for per-request latency.
- **Scaling:** good across nodes (only activations transit boundaries).
- **Use when:** multi-node deployment, throughput > latency.

**For inference (where latency matters):**
- Prefer **TP within a node** (NVLink).
- Combine with **data parallelism** (replicas) across nodes.
- Use **PP** only if model doesn't fit even with max TP.

```
# Serving Llama-3-405B across 2 nodes of 8×H100:
# TP=8 within each node (NVLink)
# PP=2 across nodes (Infiniband)
# DP=1
# Result: ~70-120 tok/s, fits comfortably
```

---

## Q70. Chunked prefill and disaggregated serving { #q70 }

**Problem:** prefill is compute-bound (saturates GPU), decode is memory-bound. Running them on the same GPU:
- During prefill, decode latency spikes (shared compute).
- Decode wastes FLOPs.

**Chunked prefill (vLLM/TGI):** split long prefills into chunks of N tokens. Interleave prefill chunks with decode iterations, smoothing latency.

**Disaggregated serving** (DistServe, SplitWise 2023-2024): separate GPU pools for prefill and decode.
- Prefill GPUs: optimized for compute (H100 SXM, top FP8 throughput).
- Decode GPUs: optimized for memory bandwidth and KV capacity (L40S, H200).
- KV cache transferred from prefill → decode via NVLink / NVMe over RDMA.

**Result:** 2-3× throughput gains vs monolithic, strict latency SLA adherence.

**When worth it:** 1M+ QPS, multiple model types, dedicated serving team. Overkill for single-team deployments.

---

## Q71. Sampling strategies — temperature, top-k, top-p, min-p, typical { #q71 }

**Temperature** $T$: divides logits before softmax. $T<1$ sharpens; $T>1$ flattens.

$$p_i = \frac{\exp(z_i / T)}{\sum_j \exp(z_j / T)}$$

**Greedy ($T=0$):** always pick argmax. Deterministic, often repetitive/boring.

**Top-k:** keep only the top $k$ tokens, renormalize, sample. Caps wildness.

**Top-p (nucleus, Holtzman 2019):** keep smallest set whose cumulative probability exceeds $p$, sample. Adapts to distribution shape — narrow for confident predictions, wide for uncertain.

**Min-p** (2024): keep tokens whose probability $\geq p \times \max(p_i)$. More robust than top-p for tuning.

**Typical sampling** (Meister 2022): keep tokens whose surprisal is near the expected entropy. Rarely used in production.

**Repetition penalty:** scale down logits of previously seen tokens. Common to combine with top-p.

**Beam search:** maintain $k$ parallel hypotheses, keep top-$k$ at each step. Deterministic, good for translation / summarization, **bad for chat** (repetitive, too safe).

```python
# Typical production settings for chat:
sampling = SamplingParams(
    temperature=0.7,
    top_p=0.9,
    repetition_penalty=1.1,
    max_tokens=1024,
)
# For code: temperature=0.2, top_p=0.95, no repetition penalty
# For creative: temperature=1.0, top_p=0.95
```

---

## Q72. Structured generation — JSON mode, grammars, constrained decoding { #q72 }

**Problem:** you need the LLM to output strict JSON (or SQL, regex, any formal grammar). Asking nicely in the prompt fails ~5-10% of the time; at 1M requests/day that's unacceptable.

**Solution 1 — Outlines / Guidance / LMFE:** compile a grammar (JSON schema, regex, CFG) into a DFA. At each step, mask out tokens that would violate the grammar before sampling.

**Solution 2 — XGrammar (2024):** hardware-accelerated constrained decoding. 10-100× faster grammar enforcement than Outlines. Now integrated into vLLM, SGLang.

**Solution 3 — Model-native** (OpenAI, Anthropic APIs): structured outputs or tool use APIs enforce JSON at the model layer. Reliable but vendor-locked.

```python
# With vLLM + Outlines
from outlines import models, generate
from pydantic import BaseModel

class Response(BaseModel):
    answer: str
    confidence: float
    sources: list[str]

model = models.vllm("meta-llama/Llama-3-8B-Instruct")
generator = generate.json(model, Response)
result = generator("What is photosynthesis?")
# Guaranteed to parse as Response, no retries needed
```

**Trade-off:** constrained decoding may produce *worse* content than free generation (the model can be forced down suboptimal paths). Always eval quality, not just parse rate.

---

## Q73. Caching — prompt caching, semantic caching, KV cache reuse { #q73 }

Three distinct caching layers, three distinct wins:

**1. KV cache prefix sharing (systems layer):**
- Requests with same prefix reuse same KV blocks.
- RadixAttention (SGLang) / prefix caching (vLLM): automatic.
- Gains are huge for chatbots with long system prompts (10-100× prefill speedup).

**2. Prompt caching (API layer — Anthropic, OpenAI):**
- Cache specific prompt segments server-side; subsequent calls reuse them.
- 90% latency reduction, 90% cost reduction on cached tokens.
- Use when: same system prompt across many requests, long context reused (e.g., RAG chunks).

**3. Semantic cache (application layer):**
- Embed incoming query → search cache of past (query, response) pairs.
- If similarity > threshold, return cached response.
- Libraries: **GPTCache**, **Redis with vector search**.
- Gains: 20-50% hit rate in chat apps with recurring FAQ patterns.

```python
# Semantic cache pattern
from gptcache import Cache
from gptcache.embedding import OpenAI as CacheEmbedder

cache = Cache()
cache.init(embedding_func=CacheEmbedder().to_embeddings,
           similarity_threshold=0.9)

def chat(prompt):
    hit = cache.get(prompt)
    if hit: return hit
    response = llm.complete(prompt)
    cache.put(prompt, response)
    return response
```

**Gotchas:**
- Semantic cache must invalidate on context changes (user session, model version).
- KV cache reuse only works if system prompt is *literally identical* (even whitespace matters).
- Never cache PII responses across users without isolation.

---

## Q74. Long context — sliding window, YaRN, LongRoPE, context parallelism { #q74 }

Serving 1M-token context is hard because:
1. **Memory:** KV cache at 1M tokens × 2.6 MB/tok = 2.6 TB. Won't fit anywhere.
2. **Latency:** attention is $O(L^2)$. 1M × 1M = 10¹² ops per layer per pass. Slow.

**Architectural fixes (at training time):**
- **Sliding window attention** (Mistral, Gemma): attend only to last N tokens. Information flows via stacked windows.
- **Dilated / sparse attention** (Longformer, BigBird): fixed sparse pattern.
- **Linear attention / Mamba SSM**: $O(L)$ compute and memory. State-Space Models.

**Position encoding fixes (at fine-tuning time):**
- **RoPE scaling** (PI, position interpolation): rescale RoPE frequencies. Quick and simple.
- **NTK-aware scaling** (YaRN, LongRoPE): smarter rescaling preserving high-frequency info. Current SOTA.
- **ALiBi**: linear bias that extrapolates naturally.

**Serving fixes (at inference time):**
- **KV cache quantization** → INT4 KV cache = 8× smaller.
- **KV cache offload** to CPU / NVMe (InfiniAttention, DeepSpeed-Inference).
- **Context parallelism (Ring Attention)**: shard KV cache across GPUs along sequence dim.
- **Chunked decoding**: process long input in chunks, summarize, attend to summary.

<div class="scenario" markdown>
**Scenario — customer wants 1M-token RAG context:** Don't. Instead: (1) use a 32k-context model with better retrieval, (2) hierarchical summarization, (3) iterative refinement. True 1M context is costly and often the model attends poorly to middle content (the "lost in the middle" problem, Liu et al. 2023). Cheaper to fix retrieval than scale context.
</div>

---

## Q75. The "lost in the middle" problem { #q75 }

**Finding** (Liu et al. 2023): LLMs retrieve information best when it's at the **start or end** of the context. Information in the middle is often ignored or misused — accuracy can drop 20-30% for middle-placed facts.

**Why:** attention is biased by training. Positional encodings and learned attention patterns favor early tokens (they've been seen by more subsequent tokens). Recency bias from next-token prediction favors the tail.

**Mitigations:**

1. **Order-aware retrieval (RAG):** put the most relevant chunks **first and last**; middle chunks are deprioritized anyway.
2. **Summarize middle content:** compress with a smaller model, place summary near the query.
3. **Multi-step reasoning:** first answer "what do we need from this?", then answer using just the relevant extracted info.
4. **Use longer-context-trained models:** models trained on long context (Claude 3.5, Gemini 1.5, Qwen-2 32k+) show less dip.
5. **Eval on needle-in-haystack** benchmarks (Greg Kamradt's test, RULER) — don't trust context length marketing.

---

## Q76. Batching trade-offs — throughput vs P99 latency { #q76 }

Larger batches → higher throughput, but **higher P99 latency for any single request** (variance in batch composition).

**SLA framing:**
- **Throughput-optimized** (bulk offline eval, RAG indexing): max batch, no cap on per-request time.
- **Latency-optimized** (interactive chat, coding assistants): small batch (even 1), prioritize time-to-first-token (TTFT).
- **Mixed SLA**: separate queues/pools. Low-latency queue = small batch; background queue = large batch.

**Levers:**
- `max_num_seqs` (concurrent requests in batch): 32-128 typical.
- `max_num_batched_tokens` (total tokens in a forward pass): controls compute budget per iteration.
- `priority` / queue weighting: route critical requests to low-latency pool.

**TTFT vs TPOT:**
- **TTFT** (time to first token) = prefill latency. Dominated by prompt length.
- **TPOT** (time per output token) = decode step latency. Dominated by batch size and KV cache size.
- Users care about *both* — fast first token (responsiveness) and fast subsequent tokens (reading speed).

---

## Q77. Latency-oriented system design — a chat endpoint { #q77 }

Target: P95 TTFT < 300 ms, P95 total response < 5 s, for a 70B-class model.

**Architecture:**

1. **Edge layer (Cloudflare/CDN):** TLS, WAF, regional routing.
2. **API gateway:** auth, rate limiting, per-tenant quotas.
3. **Request classifier:** a tiny model (1B or rules) routes to the right serving tier:
   - Simple / short requests → 8B model (cheap, fast).
   - Complex / reasoning → 70B model.
   - Code → code-specialist model.
4. **Serving fleet:** multiple replicas, TP within node, DP across nodes. Continuous batching. FP8 quantization.
5. **KV cache tier:** prefix caching for system prompts. Semantic cache for FAQs.
6. **Fallback:** if primary region fails, fall back to secondary. Degraded mode: return cached or smaller-model response.

**Monitoring (non-negotiable):**
- TTFT / TPOT histograms per-model, per-region.
- Queue depth / wait time.
- KV cache utilization.
- Token throughput ($/token tracked to budget).
- Acceptance rate if using speculative decoding.
- Error rates: OOMs, timeouts, quality regressions.

---

## Q78. Cost estimation — what does serving an LLM actually cost? { #q78 }

**GPU cost (cloud, 2026):**
- H100 (80 GB) on-demand: ~$2-4/hr cloud.
- H200 (141 GB): ~$3-5/hr.
- Rough rule: **$0.2-1/M input tokens, $1-3/M output tokens** for 70B-class open models self-hosted.

**Throughput math (70B @ BF16, 8×H100 TP):**
- Prefill: ~30,000 tokens/sec.
- Decode: ~80 tok/sec/request × 64 concurrent = ~5,000 output tok/sec.
- **Output capacity:** 5,000 × 3600 × 8 GPUs = 144M output tokens/hr per node.
- **Node cost**: 8 × $3 = $24/hr.
- **Output $/M tokens**: $24 / 144 = **~$0.17 per M output tokens** (ideal, 100% utilization).
- Real world with 30% avg utilization: $0.5-1 per M.

**API pricing benchmarks (2026):**
- Frontier hosted (GPT-5, Claude 4, Gemini Pro 2): $10-30 per M output tokens.
- Mid-tier hosted (Haiku, GPT-5 Mini): $1-5 per M.
- Self-hosted Llama 3.3 70B AWQ: $0.5-2 per M (fully-loaded).

**Decision:** self-host breakeven is around ~50M tokens/day sustained. Below that, APIs are cheaper once you count ops, on-call, depreciation. Above that, self-hosting wins hard on cost and privacy.

---

## Q79. Autoscaling LLM services — the cold-start trap { #q79 }

**Why autoscaling LLMs is hard:**
- Model load time: 70B model = 140 GB → 60-180 s to load from disk.
- Warming: CUDA graphs, torch.compile, FP8 calibration — another 30-60 s.
- Net cold start: **2-5 minutes** before a new pod can serve.

**Mitigations:**

| Strategy | How | Trade-off |
|---|---|---|
| **Overprovision** | Keep N+20% replicas warm | Cost ↑ 20% |
| **Pre-warm on schedule** | Scale up before peak hours | Needs good forecasting |
| **Shared weight storage** | Load from RDMA / NFS-mounted weights | Infra complexity |
| **Scale on queue depth** | Add pods when queue > X seconds | Reactive, some latency spikes |
| **Two-tier: warm pool + burst** | Always-on pool + cold pool that scales | Hybrid complexity |

**Modern best practice:** stateful autoscaler with predictive (time-series) + reactive (queue depth) signals. Keep a warm pool sized to p50 load, burst pool for spikes.

```python
# Pseudo-config for predictive autoscaling
autoscaler:
  min_replicas: 4
  max_replicas: 32
  target_queue_wait_ms: 500
  scale_up_cooldown: 60s
  scale_down_cooldown: 600s  # much slower to scale down
  predictive:
    forecast_window: 15min
    scale_ahead_of_demand: 120s
```

---

## Q80. Streaming responses — SSE and the UX trade { #q80 }

**Why stream:** a 500-token response takes ~6s on a 70B model. Waiting 6s for blank → bad UX. Streaming first token after ~300 ms → feels instant.

**Protocols:**
- **Server-Sent Events (SSE)** — standard. Unidirectional server→client. Every major chat UI uses this.
- **WebSockets** — bidirectional. Used when you also need client→server pushes mid-stream (voice, interruptions).
- **gRPC streaming** — internal service-to-service.

**OpenAI-compatible SSE format:**
```
data: {"choices": [{"delta": {"content": "Hello"}}]}\n\n
data: {"choices": [{"delta": {"content": " world"}}]}\n\n
data: [DONE]\n\n
```

**Client considerations:**
- **Reconnection logic:** SSE can drop; client must handle reconnect with continuation token.
- **Token-level rendering:** incrementally concatenate, render Markdown progressively.
- **Cancellation:** client closes connection → server must stop generation to free GPU. vLLM does this via abort signal.

**Edge cases:**
- Connection drops mid-stream → partial response logged; user sees "incomplete."
- Proxies (Cloudflare, nginx) may buffer SSE — set `X-Accel-Buffering: no`.
- Corporate firewalls sometimes block SSE — have WebSocket fallback.

---

## Q81. Prompt + response logging for observability { #q81 }

You *must* log prompts and responses in prod (with consent / privacy controls). Otherwise you can't debug.

**What to log:**
- Request ID, user ID (hashed), tenant ID.
- Model version, sampling params.
- Full prompt (or hash if PII), full response.
- TTFT, TPOT, total latency.
- Token counts (input, output, cached).
- Cost.
- User feedback (thumbs up/down, edits, regenerations) if available.

**Storage:**
- Hot (last 7 days): OpenSearch / Elastic for instant debugging.
- Warm (30-90 days): S3 + Athena / BigQuery for analytics.
- Cold (>90 days): aggregated metrics only, delete raw under GDPR.

**Privacy:**
- PII detection (Presidio, spaCy + regex) → mask before storage.
- Per-tenant encryption.
- Data retention limits negotiated per contract.
- EU data stays in EU (residency compliance).

**Tools:**
- **Helicone, Langfuse, Phoenix, Braintrust**: specialized LLM observability.
- **OpenTelemetry GenAI semantic conventions** (standardizing in 2025): model.name, prompt.template, etc.

---

## Q82. A/B testing LLM changes in production { #q82 }

**What changes you A/B test:**
- Model version (fine-tune vs base).
- Prompt template changes.
- Sampling parameters.
- RAG retrieval quality.

**Challenges unique to LLMs:**
- **Outcome is subjective** (no ground-truth click/purchase signal in chat).
- **High variance**: same user, same query, different response.
- **Long-tail distribution** of inputs makes stratified sampling tricky.
- **Ethical issues**: you're experimenting on real users; sensitive domains need guardrails.

**Metrics that work:**
- **Regeneration rate** (did user click "retry"?).
- **Copy rate** (did user copy part of the response?).
- **Edit distance** (did user heavily edit the suggestion?).
- **Session length** (did user keep using the product?).
- **Retention** (did user come back next week?).
- **Explicit feedback**: thumbs up/down, star rating.

**Experiment infra:**
- Deterministic hash-based assignment (user_id → variant) for stability.
- Interleaved eval: each user session sees both variants, picks preferred (Chatbot Arena-style).
- Canary → 1% → 5% → 25% → 100%, with rollback hooks.

---

## Q83. Monitoring model quality drift in production { #q83 }

LLM quality can degrade for reasons that have nothing to do with the model:
- Input distribution shifts (users start asking new things).
- Downstream tools change (API responses that RAG pulls from change format).
- Training data contamination of benchmarks → measured gains were illusions.

**Drift signals to monitor:**

| Signal | What it catches |
|---|---|
| Output length distribution | Model becoming more verbose / truncating |
| Refusal rate | Safety overcorrection (false positives) |
| Acceptance rate (for autocomplete) | Generic user-facing quality regression |
| Toxic content fraction | Safety regression |
| Token entropy | Model became more / less deterministic |
| Latency | Infrastructure issues |

**Shadow deploys:**
- Run new model on X% of traffic in parallel, log responses, **don't show them** to users. Compare offline.
- Great for catching regressions before rollout.

**Periodic auto-eval:**
- Cron job runs 1000+ fixed evaluation prompts against production, scores via LLM-as-judge, flags regressions.
- Schedule before every deploy and daily.

---

## Q84. Serving multiple models — LoRA hot-swapping and routing { #q84 }

**Problem:** you have 20 customer-specific fine-tunes. Serving each as its own endpoint = 20× GPUs = bankruptcy.

**Solution — LoRA multi-tenant serving:**

1. Keep **one base model** loaded (e.g., Llama-3 70B).
2. Store each customer's **LoRA adapter** (~100 MB) separately.
3. At request time, apply the correct adapter to the base model's forward pass.

**Frameworks:**
- **S-LoRA** (2023): serves thousands of LoRAs concurrently on one base, handles batching across adapters.
- **vLLM multi-LoRA** (2024): native support, production-ready.
- **TensorRT-LLM LoRA plugin**.

**Performance:**
- Compared to single-LoRA: ~5-10% overhead per adapter.
- Compared to 20 separate models: ~10-20× cheaper.

**Routing:**
- Request includes `adapter_id` header or API key.
- Server loads adapter from object store (S3) into memory on first request (~100 ms), caches for subsequent.

```python
# vLLM multi-LoRA
llm = LLM(model="meta-llama/Llama-3-70B", enable_lora=True, max_loras=8, max_lora_rank=16)

request_a = llm.generate(prompt_a, sampling_params, lora_request=LoRARequest("cust-a", 1, "/adapters/a"))
request_b = llm.generate(prompt_b, sampling_params, lora_request=LoRARequest("cust-b", 2, "/adapters/b"))
```

---

## Q85. Capstone: the full inference path for a frontier chatbot { #q85 }

Let's trace a single user message end-to-end at a hypothetical frontier chat product:

**t=0ms — User types "Summarize my last meeting" and hits Enter.**
- Client sends HTTPS request with user token to regional edge (Cloudflare).

**t=15ms — Edge layer:**
- TLS terminated. WAF inspects. Rate limiting check. Routes to nearest POP.

**t=25ms — API gateway:**
- JWT validated. User tier determined (Pro → 70B model access).
- Request ID assigned. Billing tracker opens.

**t=30ms — Context retrieval (RAG):**
- Embed query → vector search over user's meeting transcripts.
- Top-5 chunks returned from vector DB.

**t=80ms — Request arrives at serving cluster:**
- Classifier decides: complex summarization → route to 70B pool.
- Queued in continuous batch; wait time ~30ms.

**t=110ms — Prefill starts:**
- System prompt + RAG chunks + user message = 2500 tokens.
- KV cache prefix (system prompt) already cached → only new tokens processed.
- Prefill takes ~120ms on H100 with FP8.

**t=230ms — First token emitted:**
- Streaming to client via SSE.
- Speculative decoding active: 70B + 8B draft → ~2.5× speedup.

**t=230ms → 2500ms — Decode:**
- Each token ~15 ms perceived (with speculation).
- 150-token summary streams in ~2.3s.
- Client renders incrementally.

**t=2500ms — [DONE] sent.**
- Billing finalized: 2500 input + 150 output tokens = $0.004 at $0.50/M input, $1.50/M output.
- Request logged for observability + feedback collection.

**Background:**
- Output + feedback flows into training data curation pipeline.
- Anomaly detection (hallucination? PII leak?) runs async.

<div class="tip-box" markdown>
**If you can tell this end-to-end story in an interview**, you're demonstrating the systems thinking that staff-level interviewers are looking for. Know the latency budget of each step, know which step dominates, know what breaks at 10× scale. That's the bar.
</div>

---

## ✅ Module Recap

- **Prefill is compute-bound; decode is memory-bound** — the foundational mental model.
- **KV cache dominates decode memory** — MQA/GQA, PagedAttention, quantization are your levers.
- **Continuous batching** is the single highest-ROI serving change; **speculative decoding** adds 2-3×.
- **AWQ/GPTQ for 4-bit inference, FP8 for H100 throughput** — pick based on hardware and accuracy budget.
- **vLLM for OSS general-purpose, TensorRT-LLM for NVIDIA max-perf, llama.cpp for edge.**
- **Long context is hard** — sliding window, RoPE scaling, KV quantization, or: fix retrieval instead.
- **Cost/latency/throughput is a 3-way trade-off** — design your SLA first, optimize ruthlessly.

→ Next: [📊 Evaluation & Benchmarks](evaluation.md)
