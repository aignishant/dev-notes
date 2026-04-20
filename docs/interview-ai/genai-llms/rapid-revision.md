# 📋 Rapid Revision

> Night-before, morning-of, commute-in review. Only what matters. Cover this and your GenAI/LLM interview will feel manageable.

---

## 🧠 The 25 facts you cannot fumble

1. **Decoder-only transformers** dominate in 2026. Trained with next-token prediction, scale cleanly, unified interface.
2. **Tokenizers**: BPE (GPT, Llama), WordPiece (BERT), SentencePiece (mT5, Llama 3 base). Matters more than people think.
3. **KV cache** stores K, V for past tokens. Dominates decode memory. MQA/GQA reduce it 4-8×.
4. **LLM inference has two phases**: prefill (compute-bound), decode (memory-bound).
5. **RoPE** (rotary positional embedding) is standard. ALiBi is the main alternative.
6. **RLHF pipeline**: SFT → reward model → PPO (with KL penalty to SFT policy).
7. **DPO** replaces PPO with a simpler preference-likelihood objective. Used by Llama 3 Instruct, many others.
8. **Constitutional AI / RLAIF**: AI feedback replaces humans, guided by natural-language principles.
9. **LoRA**: low-rank adapters $W + BA$. Trains ~0.1-1% of params. Adapter files tiny.
10. **QLoRA**: 4-bit NF4 frozen base + 16-bit LoRA. Fine-tune 70B on 48GB.
11. **PEFT is the default** for applied fine-tuning. Full fine-tuning is rare outside frontier labs.
12. **GPTQ / AWQ** are the go-to 4-bit PTQ methods for LLM inference.
13. **FP8** (H100+) is the new default for frontier training and fast inference.
14. **vLLM, TensorRT-LLM, TGI, SGLang** — know trade-offs and when to reach for each.
15. **PagedAttention** (vLLM) is virtual-memory for KV cache. 2-4× throughput win.
16. **Continuous batching** is non-negotiable for serving. 4-10× over static.
17. **Speculative decoding**: small drafts, big verifies. 2-3× decode speedup. Exact same output distribution.
18. **Chain-of-thought** improves reasoning. Self-consistency (majority vote) further boosts.
19. **RAG architecture**: chunk → embed → vector DB → retrieve top-k → rerank → generate.
20. **Prompt injection is unsolved**. Layered defenses: instruction hierarchy, tags, output filters, dual-LLM.
21. **Hallucination** = plausible but wrong or unsupported. Mitigate with RAG + abstention training + verification.
22. **Calibration**: LLMs are overconfident by default. Temp scaling helps; verbalized confidence needs explicit training.
23. **Benchmarks leak**. Use LiveBench, SWE-bench Verified, GPQA, private evals.
24. **LLM-as-judge** has position/length/style/self-enhancement biases. Pair test, cross-judge to mitigate.
25. **Context length marketing lies**. Measure needle-in-haystack. Models often fail mid-context ("lost in the middle").

---

## 🔢 Formulas to know cold

### Attention

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right) V$$

Memory: $O(L^2 \cdot d)$. Compute: $O(L^2 \cdot d)$.

### Softmax with temperature

$$p_i = \frac{\exp(z_i / T)}{\sum_j \exp(z_j / T)}$$

### KL divergence (RLHF penalty)

$$\text{KL}(\pi_\theta \| \pi_{\text{ref}}) = \sum_t \pi_\theta(a_t|s_t) \log \frac{\pi_\theta(a_t|s_t)}{\pi_{\text{ref}}(a_t|s_t)}$$

### PPO clipped surrogate

$$L = \mathbb{E}\!\left[\min(\rho_t A_t, \text{clip}(\rho_t, 1-\epsilon, 1+\epsilon) A_t)\right]$$

where $\rho_t = \pi_\theta(a_t|s_t) / \pi_{\text{old}}(a_t|s_t)$.

### DPO loss

$$L_{\text{DPO}} = -\log \sigma\!\left(\beta \log \frac{\pi_\theta(y_w|x)}{\pi_{\text{ref}}(y_w|x)} - \beta \log \frac{\pi_\theta(y_l|x)}{\pi_{\text{ref}}(y_l|x)}\right)$$

$y_w$ = preferred, $y_l$ = dispreferred. $\beta$ controls KL regularization.

### LoRA

$$h = (W_0 + \Delta W) x = W_0 x + BAx, \quad A \in \mathbb{R}^{r \times d}, \; B \in \mathbb{R}^{d \times r}$$

Typical $r \in \{8, 16, 32, 64\}$.

### KV cache size (per request, all layers)

$$\text{bytes} = 2 \times n_{\text{layers}} \times n_{\text{kv\_heads}} \times d_{\text{head}} \times L \times \text{dtype\_bytes}$$

---

## 🎯 Architecture decision tree

```
Task?
├─ Classification / NER            → Encoder (BERT / ModernBERT / DeBERTa)
├─ Embedding / Retrieval           → bi-encoder (E5, nomic, BGE) or OpenAI text-embedding-3
├─ Reranking                       → cross-encoder (bge-reranker, cohere-rerank)
├─ Chat / Generation / Reasoning
│   ├─ Quality first              → Frontier API (Claude, GPT, Gemini)
│   ├─ Privacy / cost             → Open weights (Llama, Mistral, Qwen, DeepSeek)
│   ├─ Edge / on-device           → 1-7B quantized via llama.cpp / MLX
│   ├─ Code-specific              → DeepSeek-Coder, StarCoder2, CodeLlama
│
└─ Multimodal
    ├─ Vision-language            → GPT-4o, Claude 3.5 Sonnet, Qwen-VL, Llama 3.2 V
    ├─ Image generation           → Stable Diffusion 3, Flux, DALL-E 3
    ├─ Audio (ASR)                → Whisper, Seamless, Gemini
    └─ Audio (TTS)                → OpenAI TTS, ElevenLabs, Kokoro (open)
```

---

## ⚙️ Hyperparameter starting points (2026)

| Training | Optimizer | LR | Batch | Warmup |
|---|---|---|---|---|
| LLM pretraining (70B) | AdamW | 3e-4 → 3e-5 | 4M tokens | 2k steps |
| SFT (full FT) | AdamW | 2e-5 | 32 | 3% |
| SFT (LoRA r=16) | AdamW | 1e-4 | 16-32 | 3% |
| QLoRA (70B, r=64) | Paged AdamW | 2e-4 | 16 | 3% |
| DPO | AdamW | 5e-7 | 32 | 10% |
| PPO (RLHF) | AdamW | 1e-6 | variable | 10% |

| Sampling | Temp | Top-p | Rep penalty |
|---|---|---|---|
| Chat (general) | 0.7 | 0.9 | 1.1 |
| Code | 0.2 | 0.95 | 1.0 |
| Creative | 1.0-1.2 | 0.95 | 1.0 |
| Deterministic extraction | 0.0 (greedy) | — | — |
| Self-consistency math | 0.8 | 0.95 | — (sample 10+) |

---

## 💬 Phrases that earn points

- "*Prefill is compute-bound, decode is memory-bound.*"
- "*I'd evaluate with a tiered setup: smoke on every PR, broad weekly, full pre-release.*"
- "*AdamW, not Adam — decoupled weight decay.*"
- "*PagedAttention eliminates fragmentation; continuous batching amortizes compute across requests.*"
- "*I'd measure retrieval quality before touching the model.*"
- "*For enterprise deployment, no per-tenant data goes into the base model — LoRA adapters per tenant.*"
- "*Prompt injection is not solved. Layered defenses: tags + instruction hierarchy + dual-LLM for untrusted content.*"
- "*Speculative decoding preserves the exact target distribution — it's not an approximation.*"
- "*LLM-as-judge is biased; I'd pair test and cross-judge with a different model family.*"
- "*'Lost in the middle' — I'd place the most relevant chunks first and last.*"

## 🚫 Phrases that lose points

- "GPT-4 gets 90% on MMLU so it's the best." (Contamination; MMLU alone is misleading.)
- "More context is always better." (False — quality degrades mid-context.)
- "RLHF is just fine-tuning with a reward model." (Imprecise; PPO loop with KL is the key.)
- "We'd use BERT for the chatbot." (Encoder-only, doesn't generate well.)
- "Just fine-tune it on our data." (Without eval, data curation, and a flywheel plan, this is junior.)
- "Quantization destroys accuracy." (Modern 4-bit methods lose <2% on quality benchmarks.)
- "The model hallucinated, so we add more RAG." (Retrieval quality matters, not just its presence.)

---

## 🧩 LLM project cheat sheet

**If you need to build a RAG pipeline tomorrow:**

1. **Chunking**: semantic chunks by structure (not fixed tokens). 200-500 token chunks.
2. **Embedding**: nomic-embed-text-v2 or BGE-M3 open; text-embedding-3-large hosted.
3. **Vector DB**: Qdrant / Pinecone / pgvector depending on scale.
4. **Hybrid retrieval**: dense + BM25 with reciprocal rank fusion.
5. **Reranker**: bge-reranker-v2 (open) or Cohere Rerank 3.
6. **Prompt template**: system + retrieved chunks (tagged) + user query.
7. **Evaluation**: RAGAs — faithfulness, answer_relevancy, context_precision, context_recall.
8. **Monitoring**: log every retrieval, flag when top-k hits are low similarity.

**If you need to fine-tune an LLM tomorrow:**

1. **Curate data**: quality > quantity. 1k great examples beats 100k noisy.
2. **Format consistently**: chat template or completion format, pick one, enforce.
3. **Pick PEFT**: LoRA r=16-32 covers 90% of tasks. QLoRA if 70B+ on single GPU.
4. **Hyperparameters**: LR 1e-4, 2-3 epochs, cosine with 3% warmup, batch 16-32.
5. **Eval**: held-out test set from same distribution + at least one general benchmark for regression check.
6. **Deploy**: merge LoRA or hot-swap; monitor quality vs baseline.

---

## 🔍 Debugging checklist

**Model outputs gibberish:**
- Wrong prompt template? (Chat models use specific system/user tags.)
- Wrong tokenizer-model pairing?
- Mixed precision gone wrong? (Check for NaN in logits.)

**Model refuses benign request:**
- Over-refusal from safety training. Adjust prompt; escalate to policy team.
- Add "[This is a benign educational request]" framing. (Works as a patch; long-term need better safety tuning.)

**Hallucinated citations in RAG:**
- Retrieval quality poor → fix retrieval first.
- Prompt doesn't strongly tie citation to sources → add "only cite from the provided context."
- Run post-hoc verifier.

**Latency > target:**
- KV cache too big? → GQA, INT8 KV cache.
- No continuous batching? → Switch to vLLM.
- No spec decoding? → Add draft model.
- Prefill dominates? → Chunk prefill, prefix caching.
- Decode dominates? → Smaller model tier for simple requests.

**Quality regression after fine-tune:**
- Catastrophic forgetting → reduce LR, add general data mix.
- Train data too narrow / biased → diversify.
- Over-epoch'd → early stop.

---

## 🏆 Night-before ritual

1. Review the **25 facts** above. Close the doc. Recite them.
2. Write out **RLHF pipeline** from memory. Three phases, what each does, what gets trained.
3. Write the **DPO loss** formula.
4. Explain **KV cache** and why decode is memory-bound.
5. Explain **LoRA + QLoRA** math and tradeoffs.
6. Map **vLLM, TensorRT-LLM, llama.cpp** to their sweet spots.
7. Recall your own project: three numbers, three trade-offs, one regret.
8. **Sleep**. You need it more than the last cram.

---

**You've got this.** GenAI/LLM interviews are not about reciting papers — they're about **crisp trade-off reasoning**, ownership of end-to-end systems, and the scars of having shipped something. You have all of those. Now go show them.

🎯 *Go land the offer.*
