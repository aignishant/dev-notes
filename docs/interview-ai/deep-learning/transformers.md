# 🎯 Transformers & Attention

!!! abstract "Module Scope"
    The architecture that ate deep learning. Questions **Q56–Q80**. Self-attention from first principles, positional encodings, encoder/decoder variants, BERT/GPT/T5, scaling laws, FlashAttention, KV cache, MoE, LoRA, RLHF/DPO, efficient attention alternatives, ViT. This is the most interview-critical module in 2026.

---

## Q56. Self-attention from scratch — derive Q, K, V and scaled dot-product { #q56 }

<span class="q-badge">Foundational • Must Know</span>

**Starting point**: for a sequence $\mathbf{X} \in \mathbb{R}^{L \times d}$ (L tokens, d-dim each), we want each token's output to be a content-weighted combination of *all* tokens in the sequence.

**The Q, K, V abstraction** (database analogy):

- **Query** ($\mathbf{Q} = \mathbf{X} W_Q$): what this token is looking for.
- **Key** ($\mathbf{K} = \mathbf{X} W_K$): what this token offers as an index.
- **Value** ($\mathbf{V} = \mathbf{X} W_V$): what this token provides as content.

For each query, compute similarity to every key → weights over positions → weighted sum of values.

**Scaled dot-product attention**:

$$\text{Attention}(\mathbf{Q}, \mathbf{K}, \mathbf{V}) = \text{softmax}\left(\frac{\mathbf{Q} \mathbf{K}^T}{\sqrt{d_k}}\right) \mathbf{V}$$

Shapes: $\mathbf{Q}, \mathbf{K}, \mathbf{V}$ each $(L, d_k)$; $\mathbf{Q}\mathbf{K}^T$ is $(L, L)$; output is $(L, d_k)$.

**Why divide by $\sqrt{d_k}$?** If $\mathbf{q}, \mathbf{k}$ are i.i.d. zero-mean unit-variance, $\mathbf{q} \cdot \mathbf{k}$ has variance $d_k$. For $d_k = 64$, dot products have stddev $8$ — softmax saturates (one position gets probability ~1, gradients vanish). Dividing by $\sqrt{d_k}$ rescales to unit variance → well-behaved softmax.

**Why softmax?** Produces a probability distribution over positions. Alternatives (sigmoid, linear) don't enforce weights sum to 1, which turns out to be a crucial inductive bias.

```python
import torch
import torch.nn.functional as F
import math

def scaled_dot_product_attention(Q, K, V, mask=None):
    # Q, K, V: (batch, heads, L, d_k)
    d_k = Q.size(-1)
    scores = Q @ K.transpose(-2, -1) / math.sqrt(d_k)   # (B, H, L, L)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, float('-inf'))
    weights = F.softmax(scores, dim=-1)
    return weights @ V                                   # (B, H, L, d_k)
```

<div class="tip-box" markdown>
**Interviewer question:** "Why Q and K as separate projections — why not just use X directly?" The projection lets the model learn *different similarity spaces* for matching. Also, it decouples the "search" and "content" roles — a token might want to look for nouns but provide verb info downstream.
</div>

---

## Q57. Multi-head attention — why split and why concatenate { #q57 }

<span class="q-badge">Foundational</span>

Single attention = one similarity function. **Multi-head attention** runs $h$ parallel attention ops in different subspaces and concatenates.

**Construction**:

1. Project $\mathbf{X}$ into $h$ lower-dimensional $\mathbf{Q}_i, \mathbf{K}_i, \mathbf{V}_i$, each of dim $d_k = d / h$.
2. Compute $h$ separate attention outputs: $\text{head}_i = \text{Attention}(\mathbf{Q}_i, \mathbf{K}_i, \mathbf{V}_i)$.
3. Concatenate: $(\text{head}_1, \dots, \text{head}_h) \in \mathbb{R}^{L \times d}$.
4. Linear output projection $W_O$.

$$\text{MultiHead}(\mathbf{X}) = \text{Concat}(\text{head}_1, \dots, \text{head}_h) W_O$$

**Why multiple heads**:

- **Different heads specialize** — one attends to syntactic dependencies, another to coreference, another to long-range topic. Visualizations (e.g., BertViz) confirm this.
- **Averages noise** — ensemble effect within the model.
- **More expressive** without more FLOPs (total FLOPs same as single head with dim $d$).

**Parameter count**: Same as single-head attention with full dim — $4 d^2$ parameters for $W_Q, W_K, W_V, W_O$. Heads are a *reshape*, not extra params.

```python
class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, n_heads):
        super().__init__()
        assert d_model % n_heads == 0
        self.n_heads = n_heads
        self.d_k = d_model // n_heads
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)

    def forward(self, x, mask=None):
        B, L, d = x.shape
        Q = self.W_q(x).view(B, L, self.n_heads, self.d_k).transpose(1, 2)
        K = self.W_k(x).view(B, L, self.n_heads, self.d_k).transpose(1, 2)
        V = self.W_v(x).view(B, L, self.n_heads, self.d_k).transpose(1, 2)
        out = scaled_dot_product_attention(Q, K, V, mask)   # (B, H, L, d_k)
        out = out.transpose(1, 2).contiguous().view(B, L, d)
        return self.W_o(out)
```

**Typical configs**:

| Model | $d_{\text{model}}$ | heads | $d_k$ |
|---|---|---|---|
| BERT-base | 768 | 12 | 64 |
| BERT-large | 1024 | 16 | 64 |
| GPT-3 (175B) | 12288 | 96 | 128 |
| LLaMA-70B | 8192 | 64 | 128 |

**Note on Grouped-Query Attention (GQA)** — LLaMA 2+, Gemma: fewer KV heads than Q heads (say 8 KV heads for 64 Q heads). Huge memory savings at inference with minimal quality loss. **Multi-Query Attention (MQA)** is the extreme: 1 KV head. GQA is the modern middle ground.

<div class="tip-box" markdown>
**Interviewer insight:** "Why is the output projection $W_O$ separate — isn't concatenation enough?" Without $W_O$, the heads' outputs are forced to be in separate subspaces of the d-dim output — $W_O$ lets them mix and recombine before the next layer. It's essential, not redundant.
</div>

---

## Q58. Positional encoding — sinusoidal, learned, RoPE, ALiBi { #q58 }

<span class="q-badge">Foundational • Must Know</span>

Attention is **permutation-equivariant**: shuffling tokens shuffles outputs identically. For language, this is catastrophic — word order matters. **Positional encodings** inject position information.

**1. Sinusoidal (Transformer original, 2017)**:

$$\text{PE}(pos, 2i) = \sin(pos / 10000^{2i/d})$$
$$\text{PE}(pos, 2i+1) = \cos(pos / 10000^{2i/d})$$

Added to token embeddings before the first layer.

- Different frequencies per dimension → position 5 vs position 10 have distinguishable representations.
- Any two positions' relative position can be recovered via linear combinations (via angle subtraction formulas) — enables extrapolation, in theory.

**2. Learned absolute (BERT, GPT-2)**:

Just an embedding lookup: `pos_embed = nn.Embedding(max_len, d)`.

- Simpler, often works slightly better in-distribution.
- **Can't extrapolate** beyond max_len seen in training.

**3. Relative Positional Encoding (T5, Shaw 2018)**:

Add learned bias based on relative offset $i - j$ to attention scores.

- Handles arbitrary sequence lengths better.
- Slightly more expensive attention computation.

**4. RoPE (Rotary Position Embedding, Su et al., 2021)** — now standard in LLMs (LLaMA, Gemma, GPT-NeoX):

Rotate query and key vectors by position-dependent angles:

$$\mathbf{q}_m \to R_m \mathbf{q}_m, \quad \mathbf{k}_n \to R_n \mathbf{k}_n$$

where $R_m$ is a block-diagonal rotation matrix. Then:

$$\mathbf{q}_m^T \mathbf{k}_n = \mathbf{q}^T R_{n-m} \mathbf{k}$$

**The attention score depends only on relative position** $n - m$, not absolute position. This gives:

- Relative position handling baked into attention itself.
- Good length generalization (especially with scaling tricks).
- No additional parameters.

**5. ALiBi (Attention with Linear Biases, Press et al., 2022)**:

Add $-m \cdot |i - j|$ to attention scores (where $m$ is a per-head slope). Linearly penalizes distant tokens.

- No position embedding at all.
- Excellent extrapolation — models trained on 1k tokens work on 16k tokens.

| Method | Extrapolates? | Complexity | Used in |
|---|---|---|---|
| Sinusoidal | In theory | None | Original Transformer |
| Learned absolute | No | Embedding table | BERT, GPT-2 |
| Relative | Yes (better) | Per-layer bias | T5 |
| RoPE | Yes (with tricks) | Rotation | LLaMA, Gemma, most LLMs 2023+ |
| ALiBi | Yes (best) | Additive bias | MPT, BLOOM |

```python
# RoPE implementation (simplified)
def rotate_half(x):
    x1, x2 = x[..., :x.size(-1)//2], x[..., x.size(-1)//2:]
    return torch.cat([-x2, x1], dim=-1)

def apply_rope(q, k, cos, sin):
    q = (q * cos) + (rotate_half(q) * sin)
    k = (k * cos) + (rotate_half(k) * sin)
    return q, k
```

<div class="tip-box" markdown>
**Interviewer insight:** "My model trained on 2048 tokens doesn't work on 8192 at inference." Cause: positional encoding doesn't extrapolate. Fix: (1) use **RoPE with YaRN / NTK-aware scaling**, (2) use **ALiBi** from scratch, (3) **fine-tune on longer sequences** (the "long-context extension" step in many open-source LLMs).
</div>

---

## Q59. The Transformer block — anatomy and why it's designed this way { #q59 }

<span class="q-badge">Foundational</span>

A Transformer block is:

```
x → LayerNorm → MultiHeadAttention → + residual → LayerNorm → FFN → + residual → out
```

or with **pre-norm** (most modern LLMs — more stable training):

```
x → [LN → MHA → +x] → [LN → FFN → +x]
```

**Each piece, justified**:

**1. Multi-head attention**: mixes information across token positions.

**2. Residual connection**: same reason as ResNet — smooth gradient flow, enables deep training. The residual highway is critical — a 24-layer Transformer without residuals doesn't train.

**3. Layer normalization**: stabilizes activations, handles the different scales of attention and FFN outputs. Applied per-token (not per-batch like BN), works with any batch size.

**4. Feedforward network (FFN)**: position-wise, two linear layers with activation:

$$\text{FFN}(x) = W_2 \cdot \text{GELU}(W_1 x + b_1) + b_2$$

Typical: $W_1 \in \mathbb{R}^{4d \times d}$ (expand 4x), $W_2 \in \mathbb{R}^{d \times 4d}$ (project back). **Most parameters in a transformer live here**, not in attention.

**Why 4x expansion**: empirically optimal tradeoff — smaller hurts capacity, larger has diminishing returns.

**Why GELU and not ReLU**: GELU ($x \cdot \Phi(x)$) is smoother, slight accuracy improvement, became the standard. More recently, **SwiGLU** (used in LLaMA, PaLM) outperforms GELU:

$$\text{SwiGLU}(x) = \text{Swish}(W_1 x) \odot (W_3 x) \cdot W_2$$

Extra projection + gating → more parameters, but better quality per parameter.

**Pre-norm vs post-norm**:

- **Post-norm** (original, 2017): `LN(x + SubLayer(x))` — requires careful warmup to train deep models.
- **Pre-norm** (GPT-2+): `x + SubLayer(LN(x))` — more stable, can train to hundreds of layers without warmup tricks.

```python
class TransformerBlock(nn.Module):
    def __init__(self, d_model, n_heads, d_ff, dropout=0.1):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_heads)
        self.ln2 = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Linear(d_ff, d_model),
        )
        self.drop = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        # Pre-norm
        x = x + self.drop(self.attn(self.ln1(x), mask))
        x = x + self.drop(self.ffn(self.ln2(x)))
        return x
```

<div class="tip-box" markdown>
**Senior-level takeaway:** The Transformer block is 3 insights stacked: (1) attention does cross-position mixing, (2) FFN does per-position processing, (3) residual + norm make deep stacks trainable. Each piece fails without the others. This is what makes it modular — you can swap attention for Mamba, or FFN for MoE, and get sensible behavior.
</div>

---

## Q60. Encoder, decoder, encoder-decoder — and BERT vs GPT vs T5 { #q60 }

<span class="q-badge">Foundational • Must Know</span>

Three architectural patterns for Transformers:

**1. Encoder-only** (BERT, RoBERTa, DeBERTa):

- **Bidirectional attention** — each token attends to all others.
- Trained with **Masked Language Modeling (MLM)**: mask 15% of tokens, predict them.
- Best for **understanding** tasks: classification, NER, QA.
- Not good for generation (can't easily autoregress).

**2. Decoder-only** (GPT, LLaMA, Claude, Gemini):

- **Causal (masked) attention** — each token attends only to past tokens (no lookahead).
- Trained with **next-token prediction** (causal LM).
- Natively **generative**.
- In 2022+, scales best and is dominant paradigm.

**3. Encoder-decoder** (T5, BART, original Transformer):

- Encoder processes input with bidirectional attention.
- Decoder generates output autoregressively, **cross-attending** to encoder outputs.
- Best for **sequence transduction**: translation, summarization.
- Classic, still used for structured translation tasks.

**Cross-attention** in encoder-decoder: decoder's queries, encoder's keys and values. Decoder looks at encoder's output at each generation step.

```python
# Causal mask for decoder-only (triangular)
mask = torch.tril(torch.ones(L, L))  # (L, L), 1 for allowed, 0 for masked
```

| Aspect | BERT (enc) | GPT (dec) | T5 (enc-dec) |
|---|---|---|---|
| Attention | Bidirectional | Causal | Enc: Bi, Dec: Causal + cross-attn |
| Pretraining | MLM | Causal LM | Span corruption |
| Fine-tune for classification | Easy | Easy | Easy |
| Generation | Hard (hacks) | Native | Native |
| Scale to 100B+ | Impractical | Natural | Possible |
| 2026 relevance | Still popular for embeddings | Dominant for LLMs | Niche (translation) |

**Why decoder-only won (2022+)**:

- **Unified interface**: everything is "predict next token" — translation, QA, classification, code — one model, many tasks.
- **In-context learning**: few-shot prompting works naturally.
- **Scaling is cleaner** — MLM has awkward masking overhead.
- The "bitter lesson" strikes again — simpler objective, better scaling.

**BERT still matters** for: sentence embeddings (SBERT), efficient classification, reranking for search. Modern variants like DeBERTa, ModernBERT (2024) keep it competitive.

<div class="tip-box" markdown>
**Interviewer insight:** Be ready to explain why you'd use encoder-only over decoder-only for a specific task: dense retrieval embeddings, real-time classification, structured token labeling (NER). For generation or anything open-ended, decoder-only is the default.
</div>

---

## Q61. BERT pretraining — MLM, NSP, and why NSP was dropped { #q61 }

<span class="q-badge">Historical</span>

BERT (Devlin et al., 2018) had two pretraining tasks:

**1. Masked Language Modeling (MLM)**:

- Randomly mask 15% of tokens.
- Of those 15%:
  - 80%: replace with `[MASK]`.
  - 10%: replace with random token.
  - 10%: keep unchanged.
- Predict the original.

The 80/10/10 split reduces **train-test mismatch** — at fine-tuning, `[MASK]` doesn't appear, but the model has learned to handle original and corrupted inputs.

**2. Next Sentence Prediction (NSP)**:

- Two sentences A and B. Predict: does B follow A, or is B random?
- Intended to teach sentence-level relationships (for NLI, QA).

**Why NSP was dropped** (RoBERTa, 2019):

- **Too easy** — model uses topic continuity rather than true coherence.
- **Didn't help downstream tasks** — ablations showed removing NSP improved results.
- **Wastes compute** — replace with more MLM on longer sequences.

**RoBERTa's improvements over BERT**:

1. Remove NSP.
2. Train longer on more data.
3. Larger batch size.
4. Dynamic masking (new mask each epoch) instead of static.

**DeBERTa** (2020) added: disentangled attention (separate content and position attention), enhanced mask decoder — SOTA on GLUE for years.

**Modern encoder (2024): ModernBERT** — RoPE, FlashAttention, unpadding, 8k context, strong on retrieval. Shows encoder research is still progressing, just quieter than LLMs.

**What pretraining actually teaches BERT**:

- Token-level: syntax, morphology, lexical disambiguation.
- Sentence-level: via MLM's context usage, not NSP.
- Latent semantic roles emerge in attention heads.

```python
# MLM training step (simplified)
def mlm_step(model, input_ids, mask_prob=0.15):
    labels = input_ids.clone()
    # Mask selection
    prob_matrix = torch.full(labels.shape, mask_prob)
    mask_indices = torch.bernoulli(prob_matrix).bool()
    labels[~mask_indices] = -100  # ignore in loss
    
    # 80% mask, 10% random, 10% keep
    indices_mask = torch.bernoulli(torch.full(labels.shape, 0.8)).bool() & mask_indices
    input_ids[indices_mask] = MASK_TOKEN_ID
    indices_rand = torch.bernoulli(torch.full(labels.shape, 0.5)).bool() & mask_indices & ~indices_mask
    input_ids[indices_rand] = torch.randint(V, labels.shape)[indices_rand]
    
    logits = model(input_ids)
    return F.cross_entropy(logits.view(-1, V), labels.view(-1), ignore_index=-100)
```

<div class="tip-box" markdown>
**Interviewer trivia:** Why 15% masking specifically? Too low → weak signal. Too high → destroys context for prediction. Empirical sweet spot. Chinchilla-style BERT work has suggested higher masking (30-40%) works well with more training.
</div>

---

## Q62. GPT pretraining and fine-tuning pipeline { #q62 }

<span class="q-badge">Modern • Must Know</span>

**Pretraining (causal LM)**: predict next token given all previous tokens. Loss:

$$L = -\sum_t \log P(x_t | x_{<t})$$

Trained on trillions of tokens from the web (filtered, deduplicated, quality-scored). GPT-3: 300B tokens. LLaMA 3: 15T tokens. Training compute: thousands of GPU-years.

**The post-pretraining pipeline** (modern LLM stack, 2024-2026):

**Stage 1: Pretraining** — raw capability.

**Stage 2: Supervised Fine-Tuning (SFT)**:

- High-quality (instruction, response) pairs, human-written or curated.
- Standard next-token loss but only on the response part.
- Teaches format: "user asks X, assistant responds Y".

**Stage 3: Preference Learning** — align outputs with human preferences:

**3a. RLHF (Reinforcement Learning from Human Feedback)** (InstructGPT, 2022):

1. Collect pairs (A, B) of model outputs + human preference.
2. Train **reward model** $r_\theta$: $\log \sigma(r_\theta(A) - r_\theta(B))$ for preferred A.
3. Fine-tune LLM with **PPO** to maximize expected reward, with KL penalty to prior (SFT) model:
   $$J = \mathbb{E}[r(x, y)] - \beta \cdot \text{KL}(\pi_\theta \| \pi_{\text{ref}})$$

**3b. DPO (Direct Preference Optimization)** (Rafailov et al., 2023) — the modern default:

Skip the reward model entirely. Direct loss on pairwise preferences:

$$L_{\text{DPO}} = -\log \sigma\left(\beta \log \frac{\pi_\theta(y_w | x)}{\pi_{\text{ref}}(y_w | x)} - \beta \log \frac{\pi_\theta(y_l | x)}{\pi_{\text{ref}}(y_l | x)}\right)$$

Simpler to implement, more stable than PPO, comparable quality. Standard in open-source.

**3c. Constitutional AI, RLAIF** (Anthropic, 2023+): use an LLM instead of humans to provide preferences / critiques. Scales feedback generation.

**Stage 4: Specialized training** (optional):

- **Code fine-tuning**: more code data.
- **Math fine-tuning**: chain-of-thought, verifier models (GRPO).
- **Tool use / function calling**: structured outputs on demonstration data.

```python
# DPO loss (simplified)
def dpo_loss(logp_chosen, logp_rejected, ref_logp_chosen, ref_logp_rejected, beta=0.1):
    logits = beta * ((logp_chosen - ref_logp_chosen) - (logp_rejected - ref_logp_rejected))
    return -F.logsigmoid(logits).mean()
```

<div class="scenario" markdown>
**Scenario:** You have 10k (prompt, good-response) pairs and want a chat model.<br>
**Answer:** SFT is likely sufficient for 10k examples. Use **LoRA** for memory efficiency. RLHF/DPO needs preference data (typically 10k+ (prompt, chosen, rejected) triples); if you don't have preferences, don't try to do RLHF. If you want to scale, consider **generating preferences with a stronger model** (RLAIF) rather than expensive human labeling.
</div>

---

## Q63. Scaling laws — what they are and what they predict { #q63 }

<span class="q-badge">Modern • Must Know</span>

**Scaling laws** (Kaplan et al., 2020; Hoffmann et al., 2022 — "Chinchilla") describe how LLM loss $L$ scales with:

- $N$: model parameters
- $D$: dataset tokens
- $C$: training compute (roughly $C \approx 6ND$)

**Power-law form**:

$$L(N, D) = L_\infty + \frac{A}{N^\alpha} + \frac{B}{D^\beta}$$

with $\alpha, \beta \approx 0.3-0.35$ empirically.

**Kaplan (2020)** claimed parameters mattered more than data → GPT-3 was under-trained (175B params on 300B tokens).

**Chinchilla (Hoffmann et al., 2022)** found the scaling was off — **for a fixed compute budget, optimal is $N \propto \sqrt{C}, D \propto \sqrt{C}$**, with $D \approx 20 \cdot N$ tokens per parameter.

| Model | Params | Training tokens | Ratio D/N |
|---|---|---|---|
| GPT-3 | 175B | 300B | 1.7x (under-trained!) |
| Chinchilla | 70B | 1.4T | 20x (optimal) |
| LLaMA 1 (65B) | 65B | 1.4T | 22x (near-optimal) |
| LLaMA 3 (70B) | 70B | 15T | 214x (well over) |

**Why modern LLMs train beyond Chinchilla-optimal**: if your goal is *inference-efficient* models, train smaller for longer. LLaMA 3's 8B trained on 15T tokens punches far above its weight class at inference.

**Scaling law implications for your work**:

1. **Budget planning**: can estimate final loss for any (N, D) combination before spending compute.
2. **Architecture comparisons**: fair comparison requires matched compute, not matched parameters.
3. **Data quality matters** — laws assume fixed-quality data; better data = shift intercept.
4. **Emergent abilities** (Wei et al., 2022): some capabilities appear abruptly above a scale threshold (e.g., multi-step reasoning). Debated whether these are truly emergent or artifacts of metrics.

**Compute-optimal training**:

$$\text{Compute} C = 6 N D$$

Given budget $C$:
- Optimal $N \approx 0.09 C^{0.5}$
- Optimal $D \approx 2 \cdot C^{0.5}$  (roughly)

**2026 update**: scaling still works but "compute multipliers" from better data, architecture, and alignment are substantial. A well-trained 8B can beat a poorly-trained 70B. The pure parameter count is a fading proxy for capability.

<div class="tip-box" markdown>
**Interviewer insight:** "Are scaling laws still relevant?" Yes, but with caveats. The shape holds; the constants depend heavily on data quality and training technique. "Chinchilla-optimal" is a starting point, not a commandment — most production models now train well beyond Chinchilla to get cheaper inference.
</div>

---

## Q64. FlashAttention — the key efficiency breakthrough { #q64 }

<span class="q-badge">Systems • Must Know</span>

**The problem with naive attention**: materializing the $L \times L$ attention matrix in memory.

- For $L = 2048, B = 32, H = 12$: that's $32 \cdot 12 \cdot 2048^2 = 1.6$ billion floats = 6.4GB per layer.
- Most of this memory is bandwidth-bound reads/writes to GPU HBM.

**FlashAttention** (Dao et al., 2022) — compute attention without ever materializing the full $L \times L$ matrix:

**Core idea**: tile the computation. Load blocks of Q, K, V into fast SRAM (SM-local memory), compute partial attention, update output incrementally. Uses **online softmax** (Milakov & Gimelshein, 2018) to combine block-level softmax results correctly.

**Online softmax** trick: incrementally update normalizer and max as you process blocks — mathematically equivalent to standard softmax but streaming.

**What you get**:

- **2-4x speedup** on common sequence lengths.
- **10x+ memory reduction** — now $O(L)$ memory instead of $O(L^2)$.
- Enables **much longer sequences** on same hardware.
- Exact attention (no approximation — same outputs as standard).

**FlashAttention-2** (2023): further optimizations, better parallelism across heads and sequence blocks. 2x faster than FlashAttention-1.

**FlashAttention-3** (2024): H100-specific optimizations, TMA, warp-specialization. ~1.5-2x over FA-2.

**In PyTorch 2.0+**:

```python
# Use torch.nn.functional's built-in scaled_dot_product_attention
# It automatically uses FlashAttention when available
import torch.nn.functional as F

attn_output = F.scaled_dot_product_attention(
    Q, K, V,
    attn_mask=mask,
    is_causal=True,
    dropout_p=0.0
)
# Under the hood: FlashAttention on CUDA, efficient implementations on CPU
```

**When FlashAttention doesn't kick in**:

- Unusual mask patterns (forces fallback to default impl).
- Non-contiguous tensors.
- Dtype mismatches (FA requires fp16/bf16/fp8).

**Related efficient attention**:

- **xFormers**: similar optimizations, broader backend support.
- **Paged Attention** (vLLM): efficient KV cache management for inference.

<div class="tip-box" markdown>
**Interviewer insight:** FlashAttention is a rare case of "same math, huge speedup through systems engineering". The math is identical; the implementation reduces HBM traffic. Know that it's a memory-I/O optimization, not an approximation — confusing these signals shallower understanding.
</div>

---

## Q65. KV cache — the key to fast autoregressive inference { #q65 }

<span class="q-badge">Systems • Must Know</span>

**Problem**: generating $N$ tokens autoregressively. Naive: for each new token, rerun attention on the entire sequence so far → $O(N^2)$ total attention cost → $O(N^3)$ if sequence length also grows during generation.

**KV cache**: store computed $\mathbf{K}$ and $\mathbf{V}$ for all previous tokens, reuse them.

```
Step t:
  - New token's Q: compute fresh.
  - Keys K_{1..t-1}, Values V_{1..t-1}: retrieve from cache.
  - Attention: Q_t @ K_{1..t}^T → softmax → multiply V_{1..t}.
  - Append new K_t, V_t to cache.
```

**Cost per token**: $O(L \cdot d)$ per layer, where $L$ is current length. Linear per-token → total $O(N^2 d)$ for $N$ tokens. Huge speedup vs recomputing.

**Memory cost**: $2 \cdot L \cdot H \cdot d_{\text{head}} \cdot B \cdot \text{layers}$ floats. For LLaMA-70B at 2k context, batch 1: ~20GB just for KV cache. This is why KV cache size is a major constraint for LLM serving.

**Tricks to shrink KV cache**:

**1. Multi-Query Attention (MQA)** (Shazeer, 2019):

- Use a single K, V head shared across all Q heads.
- $H \times$ smaller KV cache.
- Some quality loss, but near-free at inference.

**2. Grouped-Query Attention (GQA)** (Ainslie et al., 2023):

- Group Q heads; one K, V per group.
- E.g., 64 Q heads → 8 KV heads → 8× smaller cache vs MHA.
- Used in LLaMA 2 (70B), Mistral, Gemma.

**3. KV cache quantization** (INT8, INT4):

- Quantize cached K and V to 8 or 4 bits.
- 2-4× memory reduction, minor quality loss.

**4. Paged Attention (vLLM)**:

- Store cache in non-contiguous "pages" like OS virtual memory.
- Enables dynamic batching, prefix sharing across requests.

**5. Sliding window attention** (Mistral):

- Only keep the last $W$ tokens' KV.
- Constant memory, but loses long-range context.

```python
# KV cache in HuggingFace Transformers
outputs = model.generate(
    input_ids,
    max_new_tokens=256,
    use_cache=True,   # KV cache ON (default)
)

# With past_key_values for custom loop
past_key_values = None
for _ in range(max_new_tokens):
    outputs = model(
        input_ids=next_token,
        past_key_values=past_key_values,
        use_cache=True,
    )
    past_key_values = outputs.past_key_values
    next_token = outputs.logits[:, -1].argmax(-1, keepdim=True)
```

<div class="scenario" markdown>
**Scenario:** Serving a 70B LLaMA at 4k context, batch 8 — OOM on A100 80GB.<br>
**Answer:** KV cache is eating memory. Options: (1) quantize model to **INT4** (GPTQ, AWQ) — halves weights. (2) Use **GQA** variant (LLaMA 3 70B has GQA built-in). (3) **Quantize KV cache** (INT8). (4) Reduce batch size or context. (5) Deploy on **H100** with more HBM. (6) **vLLM with Paged Attention** for better memory packing.
</div>

---

## Q66. Mixture of Experts (MoE) — sparse scaling { #q66 }

<span class="q-badge">Modern</span>

**Motivation**: we want more parameters (better capability) without proportionally more FLOPs (inference cost).

**MoE** replaces the FFN with a set of $E$ expert FFNs + a learned **router**:

For each token, route to top-$k$ experts (typically $k = 1$ or $k = 2$), combine outputs weighted by router scores.

```
x → Router (linear layer → softmax) → select top-k experts
x → Expert_i(x) for selected i → weighted sum
```

**Activated parameters per token** = (non-expert params) + $k$ expert params. With $E = 8, k = 2$: only 25% of expert params used per token.

**Key MoE models**:

| Model | Total params | Activated per token | Experts |
|---|---|---|---|
| Switch Transformer (2021) | 1.6T | ~20B | Top-1 |
| Mixtral 8x7B (2023) | 47B | 13B | Top-2 |
| DeepSeek-V3 (2024) | 671B | 37B | 256 experts, top-8 |
| Claude Opus (internal specs unclear) | — | — | Reportedly MoE |

**Benefits**:

- Scale parameters without scaling compute.
- Specialization — different experts for different domains (code, math, multilingual).

**Challenges**:

- **Load balancing**: router might learn to always route to the same experts → dead experts. Fix: **auxiliary load-balancing loss** (Switch, Shazeer 2017) penalizes uneven routing.
- **Inference complexity**: need to dispatch tokens to multiple experts, efficient implementation requires batching across tokens.
- **Memory**: all experts must be in GPU memory even though only some are active per token.
- **Training instability**: gradient through the router's discrete selection is tricky.

**Load-balancing loss** (classic form):

$$L_{\text{aux}} = N \sum_{i=1}^{E} f_i \cdot p_i$$

where $f_i$ is the fraction of tokens routed to expert $i$ and $p_i$ is the average router score for expert $i$. Minimized when routes are balanced.

```python
# Simplified MoE forward (top-2)
class MoE(nn.Module):
    def __init__(self, d_model, d_ff, n_experts, k=2):
        super().__init__()
        self.experts = nn.ModuleList([FFN(d_model, d_ff) for _ in range(n_experts)])
        self.router = nn.Linear(d_model, n_experts)
        self.k = k

    def forward(self, x):  # x: (B, L, d)
        logits = self.router(x)                  # (B, L, E)
        probs = F.softmax(logits, dim=-1)
        topk_probs, topk_idx = probs.topk(self.k, dim=-1)
        topk_probs = topk_probs / topk_probs.sum(-1, keepdim=True)
        
        out = torch.zeros_like(x)
        for i, expert in enumerate(self.experts):
            mask = (topk_idx == i).any(-1)       # which tokens pick this expert
            if mask.any():
                expert_out = expert(x[mask])
                # ... combine with top-k weights (detail elided)
        return out
```

<div class="tip-box" markdown>
**Interviewer insight:** MoE is the single most important direction for LLM scale in 2024-2026. Dense models hit economics ceilings; MoEs get more capability per inference dollar. Understanding the tradeoffs (total params vs active params, memory vs compute) is senior-level knowledge.
</div>

---

## Q67. LoRA and parameter-efficient fine-tuning { #q67 }

<span class="q-badge">Modern • Must Know</span>

**The problem**: full fine-tuning of a 70B model requires ~280GB for weights alone, plus optimizer states (2-8x that for Adam). Out of reach on single-GPU.

**LoRA (Low-Rank Adaptation)** (Hu et al., 2021): freeze pretrained weights, inject trainable **low-rank decompositions** into key matrices.

For a pretrained weight $W_0 \in \mathbb{R}^{d \times d}$, LoRA parameterizes the update as:

$$\Delta W = B A, \quad A \in \mathbb{R}^{r \times d}, B \in \mathbb{R}^{d \times r}$$

With $r \ll d$ (typically 4-64). At inference: $W = W_0 + B A$ (or computed as $W_0 x + B A x$).

**Parameter count**: $2 r d$ vs $d^2$ → 100-1000x fewer trainable params for typical $r=8, d=4096$.

**Why it works**:

- Empirically, fine-tuning updates lie in a low-rank subspace (Aghajanyan et al., 2020).
- Pretrained representations are already strong; only small adjustments needed.

**Typical config** for LLM fine-tuning:

- Apply LoRA to attention's Q, V projections (the most impactful).
- $r = 8, \alpha = 16$ (scaling factor $\alpha / r = 2$).
- Frozen base model in 4-bit or 8-bit (QLoRA).

**QLoRA** (Dettmers et al., 2023):

1. Quantize base model to **NF4 (normalized float 4)** — 4-bit weights.
2. LoRA adapters in fp16/bf16.
3. Gradients flow through dequantized weights.
4. Result: fine-tune 70B on a single 48GB GPU.

**LoRA variants**:

- **DoRA**: decompose $W$ into magnitude + direction, train both.
- **LoRA+**: different LRs for A and B matrices.
- **Adalora**: learn which layers need which rank.

```python
# Using PEFT library (HuggingFace)
from peft import LoraConfig, get_peft_model, TaskType

config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=8,
    lora_alpha=16,
    lora_dropout=0.05,
    target_modules=["q_proj", "v_proj"],  # LLaMA-style
    bias="none",
)
model = get_peft_model(base_model, config)
model.print_trainable_parameters()
# trainable params: 4M || all params: 7B || trainable%: 0.06
```

**Other PEFT methods**:

- **Prefix tuning / Prompt tuning**: learn soft prompt embeddings, freeze the rest.
- **Adapters** (Houlsby et al., 2019): insert small trainable modules between layers.
- **BitFit**: only train biases. Surprisingly effective for simple tasks.

**When LoRA falls short**:

- Tasks requiring big behavioral changes (e.g., teaching a new language to an English-only model).
- When $r$ is too small — try higher $r$ before giving up.

<div class="tip-box" markdown>
**Interviewer scenario:** "You have a 4090 (24GB) and want to fine-tune LLaMA-3 70B on domain data." Answer: **QLoRA with 4-bit base + LoRA r=16 adapters**. Gradient accumulation to fit batch size. Flash attention for memory. This is the standard 2026 recipe for consumer-GPU LLM fine-tuning.
</div>

---

## Q68. Efficient attention alternatives — Longformer, Performer, Mamba { #q68 }

<span class="q-badge">Advanced</span>

Attention's $O(L^2)$ complexity is prohibitive for long sequences. Efficient alternatives:

**1. Sparse attention (Longformer, BigBird, Sparse Transformer)**:

- Most tokens attend only to local neighbors + a few global tokens.
- Complexity: $O(L \sqrt{L})$ or $O(L \log L)$.
- Works well for document-level tasks.

Sparsity patterns:
- **Window**: attend to $\pm w$ neighbors.
- **Dilated**: skip pattern for wider receptive field.
- **Global tokens**: some tokens (e.g., [CLS]) attend to everything.

**2. Linear attention (Performer, Linear Transformer)**:

Replace softmax with a **kernel feature map** $\phi$:

$$\text{softmax}(QK^T)V \approx \phi(Q) (\phi(K)^T V)$$

If $\phi$ has low-dimensional output $d' \ll L$, complexity drops to $O(L d')$.

- Performer uses random feature approximation of softmax (FAVOR+).
- Works but quality gap vs full attention for language.

**3. Locality-Sensitive Hashing (Reformer)**:

- Hash similar queries and keys to same bucket, compute attention only within buckets.
- $O(L \log L)$.
- Complex to implement, mixed results.

**4. State-Space Models (SSMs) / Mamba**:

Modern successor family — hidden state $\mathbf{h}_t$ updates linearly:

$$\mathbf{h}_t = A \mathbf{h}_{t-1} + B \mathbf{x}_t, \quad \mathbf{y}_t = C \mathbf{h}_t$$

- **Linear complexity** in sequence length.
- Mamba (Gu & Dao, 2023): makes $A, B, C$ input-dependent (selective state) — captures content-dependent long-range deps.
- Competitive with Transformers at scale for some tasks.
- No KV cache — constant memory at inference.

**5. Mixture-of-Depths, MoR** (2024): dynamically skip layers for some tokens.

**6. Transformer-XL / Compressive Transformer**: segment-level recurrence with cached past activations — extend effective context beyond training length.

| Method | Complexity | Best for |
|---|---|---|
| Full attention | $O(L^2)$ | Quality, short seq |
| Sparse (Longformer) | $O(L \sqrt{L})$ | Document-level |
| Linear (Performer) | $O(L d')$ | Mixed |
| Mamba | $O(L)$ | Very long seq, streaming |
| FlashAttention (not approximate) | $O(L^2)$ wall-time, $O(L)$ memory | General |

**Modern practice (2026)**: full attention with FlashAttention handles up to ~32k tokens comfortably. Beyond that, **sliding window + global attention** (Mistral's approach) or **Mamba-Transformer hybrids** (Jamba, Zamba) are emerging.

<div class="tip-box" markdown>
**Interviewer insight:** Know the complexity hierarchy but emphasize that "efficient attention" has had mixed success replacing full attention in language. The real wins came from **systems-level optimizations** (FlashAttention) rather than mathematical approximations. Mamba is the most promising architectural alternative — watch this space.
</div>

---

## Q69. Vision Transformer (ViT) — attention for images { #q69 }

<span class="q-badge">Cross-Reference</span>

See [Q36 in CNNs module](cnns.md#q36) for architecture details. Key interview points for the transformers module:

**Applying transformer machinery to vision**:

1. Images split into $16 \times 16$ patches.
2. Each patch flattened and linearly projected → "token" of dim $d$.
3. Add positional embedding (typically 2D learned, or 2D-aware RoPE).
4. Prepend a learnable `[CLS]` token.
5. Standard Transformer encoder.
6. `[CLS]` output → classification head.

**Why attention works for images**:

- Patches are tokens with local visual content.
- Self-attention lets distant patches interact (global receptive field from layer 1).
- Permutation equivariance broken by positional embeddings.

**Key design choices**:

- **Patch size**: $16 \times 16$ standard for 224×224 inputs (196 tokens). Smaller patches → more tokens → more compute but finer detail.
- **Positional encoding**: learned 2D (ViT), sinusoidal 2D, or RoPE for 2D.
- **Hybrid variants**: CNN features as input instead of raw patches (Hybrid ViT, early layers are convs).

**Data hunger (from ViT paper, section 4.2)**:

- On ImageNet-1k: ViT underperforms ResNet.
- On ImageNet-21k: ViT matches.
- On JFT-300M: ViT wins.
- With large-scale pretraining (CLIP, DINOv2), ViT dominates.

**Modern vision backbones (2026)**:

- **DINOv2**: self-supervised ViT, universal feature extractor.
- **CLIP**: ViT trained on image-text pairs, strong zero-shot classification.
- **SAM (Segment Anything Model)**: ViT encoder, promptable segmentation.
- **Multimodal**: GPT-4V, Claude, Gemini all use ViT-style vision encoders feeding into LLMs.

**Cross-modal attention**: in VLM (vision-language models), image tokens and text tokens share the same transformer — attention can cross modalities directly. This is how an LLM can "see" an image: the vision encoder produces tokens, they enter the LLM's attention stream alongside text tokens.

<div class="tip-box" markdown>
**Interviewer bridge question:** "Why do LLMs now handle images without special image-processing stages?" Because ViT-style tokenization turns images into a token stream, and the LLM's attention can treat them like any other tokens. The unified representation is the whole point — a single model, one attention mechanism, all modalities.
</div>

---

## Q70. Cross-attention — how decoder talks to encoder { #q70 }

<span class="q-badge">Foundational</span>

In encoder-decoder Transformers (T5, BART, original paper), the decoder uses two attention operations per layer:

**1. Self-attention** (over decoder's own previous tokens, causally masked).

**2. Cross-attention** — queries from decoder, keys and values from encoder:

$$\text{CrossAttn} = \text{softmax}\left(\frac{\mathbf{Q}_{\text{dec}} \mathbf{K}_{\text{enc}}^T}{\sqrt{d_k}}\right) \mathbf{V}_{\text{enc}}$$

**Effect**: at each decoder step, query the encoder's representation of the source sequence for relevant info.

**Classic use**: machine translation. Decoder generates target tokens, attending to encoder's encoding of source text.

**Same math as self-attention** — only difference is K, V come from encoder instead of same sequence.

**Modern revival — Cross-attention in multimodal models**:

- Flamingo (DeepMind, 2022), LLaVA, GPT-4V style models use cross-attention to inject vision/audio info into a frozen LLM.
- Architecture: frozen LLM with added cross-attention layers that attend to vision encoder features.

```python
class CrossAttnBlock(nn.Module):
    def __init__(self, d_model, n_heads):
        super().__init__()
        self.self_attn = MultiHeadAttention(d_model, n_heads)
        self.cross_attn = MultiHeadAttention(d_model, n_heads)
        self.ffn = FFN(d_model, d_model * 4)
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)
        self.ln3 = nn.LayerNorm(d_model)

    def forward(self, x, encoder_out, causal_mask, pad_mask):
        # x queries itself (with causal mask)
        x = x + self.self_attn(self.ln1(x), mask=causal_mask)
        # x queries encoder output
        x = x + self.cross_attn(
            q=self.ln2(x),
            k=encoder_out, v=encoder_out,
            mask=pad_mask
        )
        x = x + self.ffn(self.ln3(x))
        return x
```

**Flamingo / Perceiver IO pattern**: a few learned "latent" queries cross-attend to massive inputs (many image tokens), distilling info to a fixed small number of tokens. Enables efficient multi-image / multi-frame video handling.

<div class="tip-box" markdown>
**Interviewer trivia:** The T5 paper showed encoder-decoder with cross-attention outperforms decoder-only on translation at small scale. But decoder-only models scaled better, and at large scale they match on translation via prompting. This is a recurring pattern — specialized architectures win at small scale, general-purpose ones win at large scale.
</div>

---

## Q71. RLHF vs DPO vs others — the alignment toolbox { #q71 }

<span class="q-badge">Modern • Must Know</span>

**Problem**: pretrained LLMs predict likely text, not **helpful** or **safe** text. Alignment fixes this.

**Three generations of alignment algorithms**:

**Gen 1: RLHF** (Christiano 2017, InstructGPT 2022):

1. Collect preference pairs $(y_w, y_l)$ — chosen and rejected responses.
2. Train reward model $r_\theta(x, y)$ via Bradley-Terry: $P(y_w > y_l) = \sigma(r(y_w) - r(y_l))$.
3. RL (PPO) fine-tune LLM $\pi$ to maximize $\mathbb{E}[r(x, y)] - \beta \cdot \text{KL}(\pi \| \pi_{\text{ref}})$.

- KL term prevents "reward hacking" where $\pi$ drifts from sensible language.
- Complex: 4 models in memory (policy, ref, value, reward). PPO hyperparameter-sensitive.

**Gen 2: DPO** (Rafailov et al., 2023):

Analytical reparametrization of RLHF — solve for $r$ given the optimal policy, substitute back → pure supervised loss on preferences:

$$L_{\text{DPO}} = -\log \sigma\left(\beta \log \frac{\pi_\theta(y_w)}{\pi_{\text{ref}}(y_w)} - \beta \log \frac{\pi_\theta(y_l)}{\pi_{\text{ref}}(y_l)}\right)$$

- No reward model, no RL, no value function.
- Much simpler, cheaper, typically on par with PPO.
- Dominant method in open-source LLMs.

**Gen 3: modern variants**:

- **IPO** (Identity Preference Optimization, Azar 2023): avoids DPO's tendency to overfit to specific preferences.
- **KTO** (Kahneman-Tversky Optimization, Ethayarajh 2024): works on unpaired thumbs-up/thumbs-down data (no pairs needed).
- **ORPO** (Hong 2024): combines SFT and preference loss in one stage — no separate reference model needed.
- **GRPO** (Shao 2024, DeepSeek-R1): group-relative policy optimization for reasoning; replaces value network with within-group baselines.
- **Constitutional AI / RLAIF**: use AI feedback instead of human. Scales preference generation.

**Reasoning-specific RL (2024-2025)**:

- **Process-based rewards** (PRM): score each step of a chain-of-thought, not just final answer.
- **Rejection sampling + fine-tune (STaR, RFT)**: generate many samples, keep successful ones, supervised fine-tune.
- **DeepSeek-R1**: pure RL from base model with GRPO + rule-based rewards → strong reasoning without large SFT dataset.

| Method | Data needed | Stability | Complexity |
|---|---|---|---|
| RLHF (PPO) | Preference pairs | Unstable | High |
| DPO | Preference pairs | Stable | Low |
| KTO | Unpaired ratings | Stable | Low |
| ORPO | Preference pairs | Stable | Very low (no ref model) |
| GRPO (reasoning) | Verifiable rewards | Moderate | Medium |

<div class="scenario" markdown>
**Scenario:** You have 5k (prompt, chosen, rejected) pairs and a SFT model. What to run?<br>
**Answer:** **DPO** is the first choice. Cheap, stable, well-tooled (TRL library). Run SFT first on good responses, then DPO on preference pairs. If data is noisy, try **IPO**. If you have only thumbs-up/thumbs-down (no pairs), try **KTO**. RLHF/PPO only if you have compute, expertise, and strong reason to prefer it.
</div>

---

## Q72. Quantization — INT8, INT4, and what breaks { #q72 }

<span class="q-badge">Systems</span>

**Quantization**: represent weights (and sometimes activations) in lower precision (INT8, INT4, even lower) to save memory and speed up inference.

**Post-Training Quantization (PTQ)** — no retraining:

- Scan weight distribution per tensor / per channel → find scale and zero-point.
- Quantize: $q = \text{round}(x / s + z)$.
- Dequantize at compute time (or use integer kernels).

**PTQ methods**:

- **GPTQ** (Frantar et al., 2022): quantize layer by layer, use Hessian info to minimize activation error. Standard for LLM INT4.
- **AWQ** (Activation-Aware Weight Quantization): scale weights based on activation magnitudes to preserve salient ones. Strong for INT4.
- **SmoothQuant**: shift activation outliers into weights, easier to quantize.

**Quantization-Aware Training (QAT)**:

- Simulate quantization during training (fake quant ops).
- Model learns robust weights under quantization.
- Better than PTQ at low bitwidths (e.g., INT2, INT3).

**Typical accuracy**:

| Bits | Method | Accuracy loss |
|---|---|---|
| FP16 / BF16 | — | Baseline |
| INT8 (weights + activations) | PTQ | Negligible |
| INT4 (weights) | GPTQ / AWQ | 1-2 points on benchmarks |
| INT4 (weights + activations) | QAT | 2-5 points |
| INT2 / 1-bit | QAT + tricks | Significant but improving (BitNet) |

**Speed benefits**:

- INT8: ~2x faster than FP16 on Tensor Cores.
- INT4: ~4x memory reduction, compute speedup depends on kernel support.
- FP8: native on H100/H200 — minimal accuracy loss vs BF16.

**What breaks under quantization**:

1. **Outlier activations** in LLMs — some channels have 100x larger magnitude. Simple quantization crushes them. SmoothQuant, AWQ specifically target this.
2. **Attention softmax** in low precision — softmax is sensitive; usually kept in FP16.
3. **Normalization layers** — running stats at low bit → drift.

**Production stack (2026)**:

- **Weights**: INT4 (GPTQ or AWQ) for large models, INT8 for smaller.
- **Activations**: FP16 / BF16 for most; FP8 on H100.
- **KV cache**: INT8 with per-token scaling.
- **Inference engines**: TensorRT-LLM, vLLM, llama.cpp (GGUF) all handle these.

```python
# Using bitsandbytes for 4-bit inference
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",  # normalized float 4
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3-70b",
    quantization_config=config,
    device_map="auto",
)
```

<div class="tip-box" markdown>
**Interviewer insight:** Quantization is the single biggest lever for LLM cost reduction. A 70B model at INT4 fits on one A100; at FP16 it needs 2-3 GPUs. Understanding the **accuracy/latency/memory** tradeoff at each bitwidth is production-critical knowledge.
</div>

---

## Q73. Speculative decoding — trading compute for latency { #q73 }

<span class="q-badge">Systems</span>

**Problem**: autoregressive generation is inherently sequential. Latency is dominated by the per-token forward pass × number of tokens.

**Speculative decoding** (Leviathan et al., 2022; Chen et al., 2023):

1. **Draft**: a small, fast model generates $K$ candidate tokens.
2. **Verify**: the target (large) model computes logits for all $K$ tokens in **one parallel forward pass**.
3. **Accept**: compare draft and target distributions; accept the longest prefix that passes a rejection-sampling test.
4. On rejection, resample the first disagreeing token from the target distribution.

**Mathematical property**: the accepted tokens are distributed *exactly* as if the target model had generated them sequentially. **Same output quality** as vanilla decoding.

**Speedup**:

- Typical acceptance rate: 60-80% → 2-4x speedup.
- Best when draft and target are well-aligned (same family, different sizes).

**Draft model choices**:

- Smaller model of same family (LLaMA-70B target, LLaMA-1B draft).
- **Medusa** (Cai et al., 2024): add extra heads to target model that predict tokens $t+1, t+2, t+3, \dots$ in parallel. No separate draft model.
- **EAGLE** (Li et al., 2024): draft with a single transformer layer on target's hidden states.

**Lookahead decoding**: different approach, generates n-gram candidates from a Jacobi-like iteration — no draft model, different speedup profile.

**When speculative decoding struggles**:

- Highly entropic distributions (creative writing) → low draft acceptance.
- Very long generations where the draft drifts.
- Specialized domain tasks where draft model lacks knowledge.

**Production use**: vLLM, TGI, TensorRT-LLM all support speculative decoding. Typical 1.5-3x speedup in chat applications.

<div class="tip-box" markdown>
**Interviewer insight:** Speculative decoding is a rare "free lunch" — quality preserved, latency reduced. The trade is **extra compute** (running draft model), not quality. In throughput-limited serving (many concurrent users), speculative decoding might be slower per token (more compute). In latency-limited serving (single user, low concurrency), it's a clear win.
</div>

---

## Q74. Long-context: how do modern LLMs handle 100k+ tokens? { #q74 }

<span class="q-badge">Systems / Modern</span>

**Claude 2.1**: 200k tokens. **Gemini 1.5**: 1M (some 10M). **GPT-4 Turbo**: 128k. How?

**Three pillars**:

**1. Positional encoding that extrapolates**:

- **RoPE with NTK-aware interpolation / YaRN / PI** — tweak RoPE frequencies to generalize beyond training length.
- **ALiBi** — linear bias, naturally extrapolates.
- **Position Interpolation (PI)** (Chen et al., 2023): interpolate positions into pretrained range, then fine-tune on long sequences.

**2. Efficient attention**:

- **FlashAttention** (essential) — memory $O(L)$, wall-time still $O(L^2)$ but hides constants.
- **Sliding window attention** + **global tokens** (Mistral, Longformer): local patterns with select global.
- **Ring attention** — split sequence across devices, rotate KV across ring.

**3. Long-context fine-tuning**:

- Models pretrained on 8k tokens don't work well at 100k out of the box.
- Fine-tune on progressively longer sequences (4k → 16k → 64k → 128k) with curriculum.
- Use synthetic long-context data (long documents, multi-doc QA, retrieval needles) for robustness.

**Evaluating long-context**:

- **Needle in a Haystack** (Kamradt 2023): plant a single fact in long context, ask the model to retrieve it. Tests basic recall.
- **RULER** (Hsieh 2024): 13 tasks probing different long-context skills.
- **LongBench, L-Eval**: broader benchmarks.

**Common failures**:

- **Lost in the middle** (Liu et al., 2023): models attend well to beginning and end of context, poorly to middle.
- **Length generalization collapse**: models trained on 2k fail at 4k unless the architecture supports extrapolation.
- **Cost explosion**: attention is $O(L^2)$; at 1M tokens, a single forward pass is very expensive.

**Production patterns for long context**:

1. **RAG instead of long context**: often cheaper to retrieve relevant chunks than to put everything in context. See [Q75, RAG module](../rag/).
2. **Long-context only when needed**: code understanding, book summarization, multi-document analysis.
3. **Prefix caching**: if many queries share a long prefix (e.g., system prompt), cache its KV once. vLLM, SGLang, Claude's caching support this.

<div class="scenario" markdown>
**Scenario:** Client wants to analyze 500-page financial documents with an LLM.<br>
**Answer:** Two paths: (1) **long-context model** (Claude 200k, Gemini 1M) — simplest, but expensive per query and may lose middle detail. (2) **RAG**: chunk the doc, embed, retrieve relevant chunks per query. Cheaper, better for many queries over the same doc. Hybrid works too: RAG to pull the top sections, then process those with long-context model.
</div>

---

## Q75. Embeddings with transformers — sentence/passage vectors { #q75 }

<span class="q-badge">Applied</span>

Transformer-based embeddings dominate dense retrieval, semantic search, clustering, and RAG.

**Simple approach**: mean-pool hidden states of a BERT / RoBERTa → sentence vector. Works but not competitive with specialized models.

**SBERT (Sentence-BERT)** (Reimers & Gurevych, 2019) — the seminal approach:

- Fine-tune BERT with **Siamese/Triplet networks** on sentence pairs:
  - $L = \max(0, m + d(a, p) - d(a, n))$ (triplet)
  - Or contrastive: $L = -\log \sigma(s(a, p) - s(a, n))$
- Mean-pool outputs for fixed-size vector.

**Modern embedding models (2026)**:

| Model | Dim | Notable |
|---|---|---|
| **OpenAI text-embedding-3-large** | 3072 | Scalable dim (can truncate) |
| **Cohere Embed v3** | 1024 | Multilingual |
| **E5 / BGE / GTE / Voyage** | 768-1024 | Open, top of MTEB |
| **nomic-embed-text-v2** | 768 | Long context (8k) |
| **Mistral-embed** | 1024 | Strong multilingual |

**Training recipe for modern embeddings**:

1. **Weakly supervised pretraining** on web pairs (title-body, query-document).
2. **Supervised fine-tuning** on labeled pairs + mined hard negatives.
3. **Multi-task** on retrieval, classification, clustering, STS.
4. **Instruction-tuning** — add task instructions ("Represent this for retrieval: ...").

**Hard negative mining** — critical for quality:

- Easy negatives (random pairs): model learns trivial distinctions.
- Hard negatives (topically similar but wrong): model learns fine distinctions.
- Mine via BM25 retrieval on train set, or use a previous model's top-K non-positives.

**Matryoshka embeddings** (Kusupati et al., 2022):

- Train so that prefix of the vector (first 64, 128, 256 dims) is also a useful embedding.
- Enables dynamic dimensionality — use 1024-dim for precision, 128-dim for speed.
- Adopted in OpenAI's v3 embeddings.

**Bi-encoder vs cross-encoder**:

| | Bi-encoder | Cross-encoder |
|---|---|---|
| Architecture | Encode query and doc separately | Encode (query, doc) pair |
| Speed | Fast (pre-embed docs) | Slow (one pass per pair) |
| Quality | Good | Best |
| Use | First-stage retrieval | Reranking top-K |

**Retrieval pipeline**: bi-encoder retrieves top 100 → cross-encoder reranks to top 10.

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-large-en-v1.5')
embeddings = model.encode(sentences, normalize_embeddings=True)
# Use cosine similarity for retrieval
```

<div class="tip-box" markdown>
**Interviewer insight:** Embeddings are the backbone of RAG, semantic search, and agent memory. Know:
- **Why fine-tune for a domain** — pretrained embeddings miss specialized vocab.
- **Hybrid retrieval** — combine dense (embedding) + sparse (BM25) for robustness.
- **MTEB benchmark** — the Massive Text Embedding Benchmark. Check it when picking a model.
</div>

---

## Q76. Chain-of-thought, tree-of-thought, reasoning paradigms { #q76 }

<span class="q-badge">Modern</span>

**Chain-of-thought (CoT)** (Wei et al., 2022): prompt LLM to generate intermediate reasoning steps before final answer. Massive accuracy gains on reasoning tasks.

**Zero-shot CoT**: append "Let's think step by step." (Kojima et al., 2022). Works surprisingly well without examples.

**Few-shot CoT**: include examples with full reasoning traces in prompt.

**Self-consistency** (Wang et al., 2022): sample $k$ CoTs, majority-vote final answers. More compute for more accuracy.

**Tree of Thoughts (ToT)** (Yao et al., 2023): explore multiple reasoning branches, backtrack, evaluate. More planning-like than linear CoT.

**Graph of Thoughts**: arbitrary DAG structure of reasoning nodes.

**Program-of-Thoughts / Program-aided Language Models**: generate code that solves the problem, execute code, read result. Much stronger on math.

**2024-2026 revolution — RL for reasoning**:

- **OpenAI o1 / o3**: CoT integrated into training via RL on verifiable reward signals (math, code). Model generates long internal reasoning ("test-time compute"), sometimes thousands of tokens of thinking before answering.
- **DeepSeek-R1**: open-source equivalent. Pure RL (GRPO) from base model + rule-based rewards → emergent CoT.
- **Claude's extended thinking**: similar paradigm — allocate test-time compute to reasoning-heavy problems.

**Key ideas**:

1. **Test-time compute scaling**: spend more tokens thinking → better answers. Sometimes beats scaling training compute.
2. **Process reward models (PRMs)**: score each step; enables search and verification.
3. **Self-improvement**: model generates CoTs, verifier picks correct ones, fine-tune on successful traces → recursive improvement.

**Practical tips for CoT in production**:

- **Structured CoT**: use XML tags to separate reasoning from final answer — easier to extract.
- **Hide CoT from user**: reasoning is internal; only show the answer.
- **Cost tradeoff**: CoT increases token costs substantially. Use for hard problems, not simple queries.
- **Evaluation**: beware of "reasoning" that doesn't actually cause the answer — LLMs sometimes produce plausible reasoning post-hoc. Measure end-to-end accuracy, not reasoning quality alone.

```python
# Basic CoT prompting
prompt = f"""Solve this problem step by step.

Problem: {question}

Let me think through this carefully:
1."""

# Self-consistency: sample multiple, majority vote
answers = [extract_answer(llm.generate(prompt, temperature=0.7)) for _ in range(10)]
final = Counter(answers).most_common(1)[0][0]
```

<div class="tip-box" markdown>
**Interviewer insight:** In 2026, the frontier is **test-time compute** — letting models think for longer before answering. This shifts the paradigm from "bigger model for harder problems" to "same model + more thinking for harder problems". Reasoning models (o1, R1, Claude's extended thinking) embody this.
</div>

---

## Q77. Tokenizer tricks — special tokens, chat templates, function calling { #q77 }

<span class="q-badge">Practical</span>

Modern LLMs use specialized tokens for structure. Missing these breaks everything.

**Special tokens**:

- `<s>` / `<bos>`: beginning of sequence.
- `</s>` / `<eos>`: end of sequence. Generation typically stops at EOS.
- `<pad>`: padding token for batching.
- `<unk>`: unknown (rare in modern byte-level BPE).
- `<|im_start|>`, `<|im_end|>` (ChatML): mark message boundaries.

**Chat templates** — how multi-turn conversations are serialized:

LLaMA 2/3 chat template:
```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>

What's 2+2?<|eot_id|><|start_header_id|>assistant<|end_header_id|>

4<|eot_id|>
```

**Critical**: use the **exact** chat template the model was trained on. Wrong template = garbage outputs (most common LLM bug).

```python
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")
messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "What's 2+2?"},
]
# tokenizer handles chat template
input_ids = tok.apply_chat_template(
    messages, return_tensors="pt", add_generation_prompt=True
)
```

**Function calling / structured output**:

Models trained on function-calling data learn to emit JSON when given tool schemas. Two approaches:

- **Native function calling** (OpenAI, Claude, Gemini, LLaMA-3.1+): model emits structured calls; platform parses.
- **Constrained generation** (guidance, outlines, vLLM JSON mode): at inference, mask logits to force grammar conformance. Guaranteed valid JSON even if model wasn't trained for it.

**Grammar-constrained decoding**:

- Define JSON schema → regex → state machine.
- At each decoding step, mask logits for tokens that violate the grammar.
- Outputs always valid. Quality can sometimes degrade (model forced into unnatural completions).

**Token budget management**:

- Count tokens of prompt + expected output to ensure fit in context.
- `tiktoken` for OpenAI models, `tokenizer.encode()` for HF models.
- Be aware of template overhead (chat formatting can add 20-50 tokens per turn).

<div class="scenario" markdown>
**Scenario:** You're getting terrible responses from a fine-tuned LLaMA-3.<br>
**Answer:** 90% chance it's a **chat template mismatch**. Check: (1) are you using `apply_chat_template` or manually constructing? (2) did you fine-tune with the same template? (3) does your prompt include `<|eot_id|>` correctly? This is the single most common LLM bug in production.
</div>

---

## Q78. LLM evaluation — beyond perplexity { #q78 }

<span class="q-badge">Applied</span>

Perplexity measures language modeling quality but not capability. Modern LLM evaluation:

**1. Academic benchmarks**:

| Benchmark | Measures |
|---|---|
| **MMLU** | General knowledge across 57 subjects |
| **GSM8K, MATH** | Math word problems |
| **HumanEval, MBPP** | Code generation |
| **ARC, HellaSwag** | Commonsense reasoning |
| **TruthfulQA** | Factual accuracy on misleading questions |
| **BIG-Bench Hard** | Hard reasoning tasks |
| **IFEval** | Instruction following |
| **MT-Bench** | Multi-turn dialog quality (GPT-4 judge) |
| **Chatbot Arena** | Human pairwise preferences, Elo rating |

**2. Issues with benchmarks**:

- **Contamination**: benchmarks leak into training data; scores inflate.
- **Saturation**: frontier models score 90+ on MMLU → no signal for improvement.
- **Narrow vs useful**: benchmark performance ≠ real-world utility.

**3. Modern best practices**:

- **Chatbot Arena** (LMSYS): humans chat with anonymous LLMs and vote. Most trusted comparative signal.
- **Domain-specific eval sets**: build your own held-out evaluation of real user queries for your app.
- **LLM-as-judge**: use a strong model (GPT-4, Claude) to score outputs. Cheap, reasonably reliable, but can have biases (length, tone).
- **Pairwise vs absolute scoring**: pairwise more reliable.

**4. Capability-specific eval**:

- **Reasoning**: MATH, AIME, GSM8K, ARC-AGI.
- **Code**: LiveCodeBench (contamination-resistant), SWE-bench (real software issues), HumanEval+.
- **Safety**: HarmBench, AdvBench, jailbreak resistance tests.
- **Truthfulness**: TruthfulQA, SimpleQA.
- **Long context**: RULER, needle-in-haystack variants.

**5. Production-grade evaluation**:

- **Golden eval set** — 50-500 real examples from your users, manually labeled with expected outputs.
- **Regression testing** — run eval before every prompt / model change.
- **A/B testing** — real users, production traffic, user-level metrics (task success, thumbs up/down, retention).
- **Human review** for high-stakes outputs.

**Red-teaming**:

- Adversarial probing — get humans or LLMs to try to break the model.
- Jailbreak attempts, toxic queries, edge cases.

<div class="tip-box" markdown>
**Interviewer insight:** In industry, **your custom eval set + real user feedback > any public benchmark**. Public benchmarks are useful for coarse model selection, but shipping changes to an LLM product requires a project-specific eval harness. Saying "we used MMLU to decide if the new model is better" in a staff interview is a red flag.
</div>

---

## Q79. Hallucination — causes, mitigations, and fundamental limits { #q79 }

<span class="q-badge">Applied</span>

**Hallucination** = LLM generates content that's plausible but false. Comes in flavors:

1. **Factual hallucination**: wrong facts (dates, names, attributions).
2. **Context-unfaithful**: contradicts info provided in the prompt/RAG.
3. **Fabrication**: invents sources, URLs, citations.
4. **Compounding errors**: one mistake cascades through CoT.

**Why LLMs hallucinate**:

1. **Training objective is next-token prediction**, not truth. Plausibility > accuracy.
2. **Knowledge has gaps**: training cutoffs, long-tail facts poorly represented.
3. **Overconfidence**: no calibrated "I don't know" signal.
4. **Statistical pattern completion**: if a question looks like a knowable one, model guesses based on patterns.

**Mitigations**:

**A. Retrieval-Augmented Generation (RAG)**:

- Ground responses in retrieved documents.
- Reduces factual hallucination dramatically.
- Doesn't eliminate context-unfaithful hallucination (model may still make things up even with sources).

**B. Prompt engineering**:

- "If you don't know, say so."
- "Base your answer only on the provided context."
- "Cite your sources from the provided documents."

**C. Constrained decoding / function calling**:

- Force JSON / SQL / grammar → can't make up fields.

**D. Self-verification**:

- Generate answer → separately check against facts → revise.
- **Chain-of-Verification (CoVe)** (Dhuliawala 2023): LLM asks itself verifying sub-questions, answers them, refines final answer.

**E. Fine-tuning**:

- Include "I don't know" examples.
- DPO against hallucinated responses (negatives) and grounded ones (positives).

**F. Retrieval with citations**:

- Force model to cite source span for each claim. Humans can verify.

**G. Uncertainty estimation**:

- Confidence from logit entropy, self-consistency across samples, verbalized confidence.
- Threshold low-confidence outputs → defer to human / fallback.

**Fundamental limits**:

- No scalable oracle for factual accuracy.
- Model may know facts but lack the meta-knowledge to tell when it doesn't.
- Even with RAG, hallucination persists if retrieved passages are misused or missing.

**Measurement**:

- **TruthfulQA**: designed to elicit common misconceptions.
- **FActScore** (Min et al., 2023): decompose output into atomic facts, check each.
- **SimpleQA** (OpenAI, 2024): 4000 short-form factoid questions; even frontier models score < 50%.

<div class="scenario" markdown>
**Scenario:** Medical Q&A product — hallucinations are unacceptable.<br>
**Answer:** Defense in depth: (1) **RAG against vetted sources** (UpToDate, PubMed); no answer without a citation. (2) **Constrained format** requiring structured citation. (3) **Uncertainty thresholding** — low-confidence → "consult a physician". (4) **Retrieval quality over retrieval recall** — better to return "I don't have enough info" than a hallucinated answer. (5) **Human review** for generated content before user-facing. (6) **Monitor** with ground-truth spot checks.
</div>

---

## Q80. Modern transformer recipe — what a 2026 production LLM looks like { #q80 }

<span class="q-badge">Modern • Capstone</span>

A 2026 production-grade LLM (e.g., LLaMA-3, Gemma 2, Mistral, Qwen-2, Claude-like) combines:

**Architecture**:

- **Decoder-only Transformer** — 20-80 layers.
- **Pre-norm** (LayerNorm before each sublayer).
- **RMSNorm** instead of LayerNorm (faster, slightly better).
- **RoPE** positional encoding (with YaRN / NTK scaling for long context).
- **SwiGLU** FFN activation instead of GELU.
- **GQA (Grouped-Query Attention)** — fewer KV heads than Q heads.
- **Weight tying** — input embedding = output projection (saves params).
- **No dropout** in many modern LLMs (training scale makes it unnecessary; adds noise to gradient).

**Pretraining**:

- **15T+ tokens** of high-quality, filtered, deduplicated data.
- **Mixed data sources**: web (majority), books, papers, code, math, multilingual.
- **Data curriculum**: progressively higher-quality data toward end of training.
- **Synthetic data**: model-generated reasoning traces for math/code. Increasingly important.
- **Training compute**: 10^24 to 10^26 FLOPs for frontier models.

**Training stack**:

- **BF16 / FP8** mixed precision.
- **ZeRO-3 or FSDP** for model-parallel training.
- **AdamW** optimizer, $\beta_1 = 0.9, \beta_2 = 0.95$.
- **Cosine LR schedule** with warmup.
- **Gradient clipping** at 1.0.
- **FlashAttention-2 / 3**.
- **Batch size**: millions of tokens; gradient accumulation to hit target.

**Post-training**:

1. **SFT** on curated, diverse, multi-turn data.
2. **Preference optimization** (DPO / RLHF / GRPO) on preference pairs.
3. **Capability-specific fine-tuning** (code, math, tool use, safety).
4. **Red-team + patch loops**.

**Serving**:

- **Quantization**: INT4 weights, FP8 or INT8 KV cache.
- **Speculative decoding** with Medusa/EAGLE heads.
- **Continuous batching** (vLLM, TGI).
- **Prefix caching** for shared prompts.
- **Paged attention** for variable-length sequences.

**Safety / alignment**:

- **Constitutional AI**-style feedback loops.
- **Content classifiers** pre- and post-model.
- **Refusal training** for harmful queries.
- **Watermarking** of outputs (emerging area).

| Layer | 2018 (BERT) | 2022 (GPT-3) | 2026 (SOTA) |
|---|---|---|---|
| Norm | LayerNorm | LayerNorm | RMSNorm |
| Pos encoding | Learned abs | Learned abs | RoPE + scaling |
| Activation | GELU | GELU | SwiGLU |
| Attention | Standard MHA | Standard MHA | GQA + FlashAttention |
| Parallelism | Data | Data + Tensor | Data + Tensor + Pipeline + Sequence |
| Context | 512 | 2048 | 128k-10M |
| Alignment | — | RLHF | DPO + Constitutional AI + reasoning RL |

<div class="tip-box" markdown>
**Interviewer capstone question:** "Describe the complete lifecycle of a production LLM." A senior answer walks through: data curation → pretraining architecture choices → optimizer and scaling → post-training stack → quantization for serving → evaluation → monitoring and patch cycles. If you can tell this story end-to-end, you're demonstrating the kind of systems thinking that separates staff+ candidates from mid-level.
</div>

---

## ✅ Module Recap

- **Self-attention** computes content-weighted combinations across all positions via Q/K/V projections and scaled dot-product.
- **Multi-head attention** splits into parallel subspaces, heads specialize. Modern variants (GQA, MQA) reduce KV cache for inference.
- **Positional encoding** is critical (attention is permutation-equivariant); **RoPE** and **ALiBi** are modern defaults with good extrapolation.
- **Decoder-only transformers won** because of cleaner scaling and unified interface; encoder-only (BERT) still useful for embeddings.
- **FlashAttention** and **KV caching** are the key systems-level efficiency tricks.
- **LoRA/QLoRA** democratized fine-tuning; **DPO** simplified alignment.
- **Scaling laws, MoE, long-context, reasoning RL, speculative decoding** are the frontier research directions shaping 2026 LLMs.

→ Next: [⚙️ Optimization & Training](optimization.md)
