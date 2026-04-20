# 🧬 LLM Foundations

> **Q1–Q20 · 20 questions** on the bedrock of large language models — what "LLM" actually means, how tokens become outputs, the three architecture families, scaling laws, emergent abilities, context windows, and the compute/memory bill you'll actually have to pay. Master this module before touching prompting or fine-tuning.

---

## Q1. What is a Large Language Model, and what precisely makes it "large"? { #q1 }

An LLM is a neural network — almost always a **decoder-only transformer** in 2026 — trained to predict the next token in a sequence of text. "Large" is qualitative and has shifted over time, but the useful working definition today is:

- **>10 billion parameters** for a "small LLM" (Llama 3 8B, Mistral 7B, Phi-3 mini).
- **70B–500B** for flagship open-weight models (Llama 3 70B, DeepSeek-V3 671B MoE).
- **>1 trillion** for the frontier (GPT-4 class, Claude 3+, Gemini 1.5 Ultra).

**What's actually being predicted:** $P(x_t \mid x_{<t})$, a probability distribution over the next token given all prior tokens. Training minimizes the negative log-likelihood (cross-entropy) over trillions of tokens.

$$\mathcal{L} = -\sum_t \log P_\theta(x_t \mid x_{<t})$$

**The emergent surprise:** when you train such a model on a sufficiently diverse corpus at sufficient scale, it stops being "just autocomplete" and starts doing translation, coding, reasoning, Q&A, instruction following — **purely from next-token prediction**. This is the central miracle of modern GenAI, and still not fully explained theoretically.

<div class="tip-box" markdown>
**Interview framing:** when asked "what is an LLM," don't give a one-liner. Anchor it as "a decoder-only transformer trained at scale on next-token prediction, which exhibits emergent capabilities beyond what the objective would suggest." That phrase signals familiarity with the whole arc.
</div>

---

## Q2. Encoder-only vs decoder-only vs encoder-decoder — which is an LLM? { #q2 }

| Family | Example | Attention pattern | Primary use |
|---|---|---|---|
| **Encoder-only** | BERT, RoBERTa, DeBERTa | Bidirectional | Classification, embedding, NER |
| **Decoder-only** | GPT, Llama, Claude, Mistral | Causal (unidirectional) | Generation, instruction-following |
| **Encoder-decoder** | T5, BART, FLAN-T5 | Encoder bidir + decoder causal + cross-attn | Seq2seq (MT, summarization) |

**Why decoder-only won:**

1. **Unified interface:** every task becomes "continue this prompt." No per-task architecture changes.
2. **Cleaner scaling:** encoder-decoder models have two separate stacks, complicating pretraining data mixing and scaling.
3. **Context reuse via KV cache:** because attention is causal, we can cache past keys/values and decode new tokens in $O(1)$ attention cost — impossible with bidirectional encoders.
4. **Emergent few-shot learning** was discovered in decoder-only GPT-3 first; encoder-only models never exhibited it as cleanly.

**Where encoders still matter:** embeddings (retrieval, similarity), reranking, classification where you don't need generation. **Where encoder-decoder still matters:** translation, certain summarization tasks where "input is distinct from output" is a natural framing.

```python
# Decoder-only: one model, one attention pattern, one objective
from transformers import AutoTokenizer, AutoModelForCausalLM

tok = AutoTokenizer.from_pretrained("meta-llama/Llama-3-8B")
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3-8B")
```

---

## Q3. Tokenization: BPE vs WordPiece vs SentencePiece vs Unigram { #q3 }

**Why subword tokenization?** Character-level is too long (4× more tokens, slower, more memory). Word-level is too brittle (OOV tokens, 50k+ vocab for English, millions for multilingual). Subword hits the sweet spot: fixed vocab (~32k-256k), no OOV, efficient.

**Byte-Pair Encoding (BPE):** start from characters; greedily merge the most frequent adjacent pair; repeat until vocab size reached.

```
Initial: l o w </w> | l o w e r </w> | n e w e s t </w>
Step 1:  "o w" frequent → lo w_ | lo w e r_ | n e w e s t_
Step 2:  continue merging...
```

Used by GPT-2/3/4, Llama, Mistral (as BBPE — byte-level BPE, operating on bytes not characters for truly universal coverage).

**WordPiece (BERT):** similar to BPE but merges by maximum likelihood gain instead of frequency. Greedy longest-match at inference.

**Unigram LM (SentencePiece default):** starts with a large vocab, removes tokens iteratively based on likelihood loss. Gives *probabilistic* tokenization at inference (can sample different segmentations — useful for robustness).

**SentencePiece:** a library, not an algorithm. Wraps BPE or Unigram with pre-tokenization removed (treats input as a raw sequence of Unicode chars, with whitespace as a regular symbol `▁`). Used by T5, Llama, Mistral.

| Algo | Merge criterion | Used by |
|---|---|---|
| BPE | Frequency | GPT, Llama, Mistral |
| BBPE | Byte-level BPE | GPT-2+, robust to any Unicode |
| WordPiece | Likelihood gain | BERT, DistilBERT |
| Unigram | Likelihood-based pruning | ALBERT, XLNet (via SP) |

```python
# Tokenization in practice
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("meta-llama/Llama-3-8B")
ids = tok.encode("Transformers are magical.")
# [128000, 9424, 388, 527, 24632, 13]
decoded = tok.decode(ids)
# '<|begin_of_text|>Transformers are magical.'
```

<div class="tip-box" markdown>
**Common interview mistake:** saying "BERT uses BPE." BERT uses **WordPiece**, which is similar but different. Llama uses **BPE** (on bytes, BBPE). Know which model uses which.
</div>

---

## Q4. Why do tokenizers matter so much in production? { #q4 }

A tokenizer choice that seems minor at research time has enormous downstream effects:

**1. Cost per token** = cost per API call. OpenAI charges per-token. If your tokenizer fragments a language heavily (e.g., GPT-3's tokenizer was 4-5× worse for Chinese/Arabic/Hindi than English), non-English users pay multiples more for the same content.

**2. Context length efficiency.** "128k context" measured in tokens is very different across tokenizers. Japanese text in a GPT tokenizer might use 3× more tokens than English — so your "128k" becomes "~42k" of actual Japanese characters.

**3. Behavior on numbers, code, and rare strings.**
- Older tokenizers split digits arbitrarily ("1234" → ["12", "34"]), making arithmetic *much* harder. Llama 3 and GPT-4 tokenize digits individually, which materially improves arithmetic.
- Whitespace handling in code (tabs vs spaces) affects performance dramatically on code tasks. Models trained on SentencePiece with `▁` tokens handle spaces explicitly; BPE variants vary.

**4. Tokenizer–model binding is permanent.** Once a model is trained, you *cannot* change its tokenizer without retraining (the embedding matrix is keyed by token IDs). You can extend it (add new tokens and new rows to the embedding matrix), but the old tokens' semantics are baked in.

**5. Security surface.** Tokenizers have been exploited for prompt injection (e.g., "glitch tokens" like `SolidGoldMagikarp` that had broken training signal). Every production system should have a tokenizer audit.

<div class="scenario" markdown>
**Scenario — cost optimization for a multilingual chatbot:** you're serving users in 50 languages on top of GPT-4. Spanish users generate tokens at 1.3× English rate, Japanese at 2.8×, Korean at 3.4×. Finance notices a 3× cost overrun in Asian markets. Fix: switch to a model with a more multilingual-efficient tokenizer (Llama 3, Mistral-Large, Claude 3), OR train a custom tokenizer and fine-tune a base model with extended vocab. The second path takes weeks but can halve inference costs.
</div>

---

## Q5. What is an embedding, and how does it relate to a token? { #q5 }

A **token embedding** is a learned vector $e_t \in \mathbb{R}^d$ associated with each token ID in the vocabulary. Model parameters include a lookup table $E \in \mathbb{R}^{V \times d}$ where $V$ is vocab size (~128k for Llama 3) and $d$ is hidden dim (e.g., 4096 for Llama 3 8B).

**Flow of information:**

```
"Hello" → [token ID 9906] → E[9906] → 4096-dim vector
                          ↓
                   (+ positional info)
                          ↓
                   [transformer layers]
                          ↓
                   final hidden state
                          ↓
                   × E^T (weight tying) OR separate lm_head
                          ↓
                   logits over V tokens
                          ↓
                   softmax → probability distribution
```

**Weight tying** (Press & Wolf 2017): share the input embedding matrix $E$ with the output projection. Cuts parameters by ~10-20% with no quality loss — used by most modern LLMs except the largest (where the two are decoupled for marginal quality gains).

**"Embedding" has two different meanings in the LLM world:**

1. **Internal token embeddings** — what we just described, learned as part of LM training.
2. **Sentence/document embeddings** — dense vectors representing entire strings, used for retrieval. These are typically produced by *encoder* models (SentenceTransformers, E5, BGE, OpenAI `text-embedding-3-*`) that have been specifically fine-tuned for similarity.

**Don't confuse these.** A question like "give me an embedding of this sentence using GPT-4" is almost always answered wrong by someone pulling the last hidden state — you need a model that was trained with a retrieval objective (contrastive loss).

```python
# Proper sentence embeddings
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-large-en-v1.5")
embeddings = model.encode(["a cat sits on a mat", "the dog sleeps"])
# shape: (2, 1024)
```

---

## Q6. Positional encodings in LLMs — absolute, learned, RoPE, ALiBi { #q6 }

Self-attention is **permutation-equivariant**: without position information, `"dog bites man"` and `"man bites dog"` give identical representations. Positional encodings inject sequence-order information.

**Sinusoidal (original Transformer, 2017):**

$$PE(pos, 2i) = \sin(pos / 10000^{2i/d}), \quad PE(pos, 2i+1) = \cos(pos / 10000^{2i/d})$$

Added to input embeddings. Deterministic, extrapolates in theory but not well in practice.

**Learned absolute (BERT, GPT-2):** positions 0..N are rows of a learned matrix. Simple, effective — fails to extrapolate beyond training length.

**Rotary Position Embedding (RoPE, Su et al. 2021)** — dominant in 2024+ LLMs (Llama, Mistral, Qwen). Rotates the query and key vectors in 2D subspaces by an angle proportional to position:

$$q_m^{\text{rot}} = R_{\Theta, m} q_m$$

where $R_{\Theta, m}$ is a block-diagonal rotation matrix. Crucially, the attention score $q_m \cdot k_n$ after rotation depends only on $m-n$ (the *relative* distance), giving translation-equivariance.

**ALiBi (Press et al. 2021):** no positional encoding in the embedding at all. Instead, bias the attention scores by distance:

$$\text{score}(i,j) = q_i \cdot k_j - m \cdot |i - j|$$

where $m$ is a head-specific constant. Extrapolates exceptionally well to longer sequences than trained on.

| Method | Extrapolation | Relative? | Used by |
|---|---|---|---|
| Sinusoidal | Theoretical, weak in practice | No | Original Transformer |
| Learned absolute | None | No | BERT, GPT-2 |
| **RoPE** | Good (with scaling tricks) | Yes | **Llama, Mistral, Qwen, DeepSeek** |
| **ALiBi** | Excellent | Yes | MPT, BLOOM, Falcon |
| **NoPE** (Kazemnejad 2023) | Surprisingly works | N/A | Research |

**RoPE scaling for long context** (key 2024 topic):
- **Linear scaling (PI):** divide position indices by factor $k$. Works up to ~4× training length.
- **NTK-aware / YaRN:** adjust the frequency base $\theta$. Better quality at long context.
- **LongRoPE, RoPE-scaled Llama 3.1:** enables 128k context from an 8k-trained model with modest additional training.

---

## Q7. What are scaling laws, and why do they matter? { #q7 }

**Kaplan et al. 2020** (OpenAI) showed that LLM loss follows predictable power laws in compute ($C$), parameters ($N$), and data ($D$):

$$L(N, D) \approx \left(\frac{N_c}{N}\right)^{\alpha_N} + \left(\frac{D_c}{D}\right)^{\alpha_D}$$

with empirically measured $\alpha_N, \alpha_D \approx 0.3$-$0.4$.

**Chinchilla (Hoffmann et al. 2022)** corrected the original: for a *fixed compute budget*, the optimal balance is roughly **20 training tokens per parameter**. GPT-3 (175B params, 300B tokens) was heavily **under-trained** — a 70B model trained on 1.4T tokens (Chinchilla) matched it.

**Post-Chinchilla, the frontier changed tactics:**
- Train smaller models on *more* tokens than Chinchilla-optimal, because **inference cost** scales with params not tokens. A 7B model trained on 15T tokens (Llama 3 style) is "over-trained" from a pretraining-cost view but far cheaper to serve.
- Llama 3 8B was trained on ~15T tokens, ~7× Chinchilla-optimal. The quality gain is meaningful, and the cheaper inference justifies it.

**Why scaling laws matter in interviews:**
1. They justify why frontier labs raise ever-larger rounds (compute scales predictably).
2. They guide practical decisions: "should I make my model 2× bigger or train on 2× more data?"
3. They explain **why emergence is surprising but not magical** — loss drops smoothly, but downstream task metrics can jump sharply at a threshold.

<div class="tip-box" markdown>
**Senior-level framing:** "Scaling laws are predictive for *pretraining loss* — but downstream capabilities like reasoning, coding, and tool use scale non-smoothly. That's why you can't just extrapolate 'loss at 10x compute' into 'ability to do X at 10x compute.'"
</div>

---

## Q8. What is emergence, and is it real? { #q8 }

**Emergence** (Wei et al. 2022) = capabilities present in large models but absent in smaller ones *in the same family*. Famous examples: 2-digit arithmetic, 3-digit multiplication, logical deduction, some translation pairs — all appear suddenly at a specific parameter threshold.

**Plot: accuracy vs model scale shows a step function, not a curve.**

```
Accuracy
  │                    ┌─────
  │                    │
  │                    │
  │                    │
  │                    │
0 │_____________───────┘
  └────────────────────────────→ Model size (log)
         <threshold       ≥threshold
```

**The "is it real?" debate (Schaeffer et al. 2023):** when you change from **exact-match accuracy** (harsh, binary) to a **smoother metric** (token log-likelihood, partial credit), the step function often becomes a smooth curve. So the emergence is partly an artifact of how we measure. *But:* the threshold where models become *usable* for a task is still real — users care about exact-match accuracy.

**Explanations for emergence:**

1. **Capability threshold:** solving a task requires composing $k$ sub-skills, each needing scale $s$. The full task requires scale $s^k$, giving a sharp threshold.
2. **Grokking:** training-time phenomenon where generalization suddenly clicks long after memorization. Related but distinct from scale-emergence.
3. **Metric artifact:** as above — partly about measurement, not capability.

**Capabilities that famously emerged with scale:**

| Capability | Emergence threshold |
|---|---|
| Few-shot learning | ~1B (GPT-2 → GPT-3) |
| Chain-of-thought | ~60B (Wei et al. 2022) |
| Tool use (via function calling) | ~70B |
| Zero-shot code generation | ~10B |
| Instruction following | SFT, not just scale |
| Multilingual reasoning | ~70B |

---

## Q9. What is next-token prediction, and why does it work for so many tasks? { #q9 }

At training time, for a sequence $x_1, \ldots, x_T$:

$$\mathcal{L} = -\frac{1}{T} \sum_{t=1}^T \log P_\theta(x_t \mid x_1, \ldots, x_{t-1})$$

This is just *cross-entropy* with teacher forcing. Nothing fancy.

**Why does this simple objective produce translation, coding, chat, math, creative writing?**

The **multi-task distillation view**: if your training corpus includes translation pairs ("English: …\nFrench: …"), math solutions, code, instructions followed by responses, etc., then **predicting the next token in that corpus implicitly requires solving the task**. The model isn't learning "language" — it's learning to imitate the distribution of human-produced text, which happens to contain all these tasks.

**Formally (via the implicit reward view, Andreas 2022):** next-token prediction approximates a mixture of reward functions — every document in the corpus is a demonstration of some latent task.

**What this implies for capabilities:**
1. If a task is *not represented* in the corpus, the base model cannot do it zero-shot.
2. Quality of the base model on a task is bounded by the best human demonstrations in the corpus.
3. RLHF/SFT push the model *past* the corpus average toward a specific behavior.

---

## Q10. Decoding strategies — greedy, beam, top-k, top-p, temperature { #q10 }

After the model produces logits $z \in \mathbb{R}^V$ for the next token, a **decoding strategy** selects the actual token.

**Greedy:** always pick $\arg\max$. Deterministic. Boring, repetitive, gets stuck in loops.

**Temperature:** softmax with a temperature $T$:

$$P(x_i) = \frac{\exp(z_i / T)}{\sum_j \exp(z_j / T)}$$

$T = 1$: raw distribution. $T < 1$: sharper (more deterministic). $T > 1$: flatter (more random). $T \to 0$: equivalent to greedy.

**Top-k sampling:** restrict to the top $k$ tokens, then renormalize and sample.

**Top-p (nucleus) sampling (Holtzman et al. 2019):** restrict to the smallest set of tokens whose cumulative probability exceeds $p$, then sample. Adaptive: at confident steps, fewer tokens are considered; at uncertain steps, more.

**Beam search:** track the $k$ most likely sequences. Each step, extend each beam with all possible next tokens, keep the top-$k$ overall. Great for constrained generation (translation, summarization) but produces **bland, repetitive output** for open-ended generation.

**Typical production defaults:**

| Use case | Temperature | Top-p | Top-k |
|---|---|---|---|
| Classification / structured | 0.0 (greedy) | 1.0 | — |
| Chat (helpful assistant) | 0.7 | 0.9 | 40 |
| Creative writing | 0.9–1.2 | 0.95 | — |
| Code generation | 0.2–0.4 | 0.95 | — |
| Translation | 0.0 (beam, k=4) | — | — |

```python
# Hugging Face generation
from transformers import AutoTokenizer, AutoModelForCausalLM

tok = AutoTokenizer.from_pretrained("meta-llama/Llama-3-8B-Instruct")
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3-8B-Instruct", device_map="auto")

inputs = tok("Explain quantum entanglement.", return_tensors="pt").to(model.device)
out = model.generate(**inputs,
                     max_new_tokens=200,
                     temperature=0.7,
                     top_p=0.9,
                     do_sample=True,
                     repetition_penalty=1.1)
print(tok.decode(out[0], skip_special_tokens=True))
```

**Advanced techniques (2024+):**
- **Min-p sampling:** more principled than top-p for low-entropy distributions.
- **Contrastive decoding:** penalize tokens that a weak model would also predict.
- **Speculative decoding** (inference-only): draft with a small model, verify with the large one — 2-3× faster. Not a quality-altering technique.

---

## Q11. What does the inside of a transformer block actually do? { #q11 }

A decoder-only transformer block is strikingly simple — two sub-layers, each preceded by a norm and wrapped in a residual:

```
x
├── LayerNorm / RMSNorm
├── Multi-Head Self-Attention
├── + residual
│
├── LayerNorm / RMSNorm
├── Feed-Forward Network (MLP)
└── + residual
```

**Attention's job:** **move information between tokens.** Each position pulls content from all prior positions weighted by query-key similarity. This is the *only* mechanism for cross-token interaction.

**MLP's job:** **process information within each token independently.** The MLP operates on each position's hidden state in isolation (positional info already baked into the embedding). It's where most of the "knowledge" lives — ablation studies show MLP parameters encode facts.

**Quantitatively:** a typical transformer block has $12 d^2$ parameters, split ~1/3 in attention ($4d^2$: Q, K, V, output) and ~2/3 in MLP ($8d^2$: up + down projection with 4× expansion).

**Modern variants you should know:**
- **SwiGLU MLP** (used in Llama, Mistral): gated activation instead of standard ReLU/GELU. Slightly more params but better quality.
- **Pre-LN vs Post-LN:** pre-LN (norm before sublayer) is easier to train and is the default. Post-LN (original Transformer) is unstable for deep networks.
- **RMSNorm** (no mean subtraction) is faster than LayerNorm and comparable in quality.
- **Grouped-query attention (GQA):** fewer K/V heads than Q heads — reduces KV cache memory at inference.

---

## Q12. How does self-attention actually compute an output? { #q12 }

For each position $i$ in a sequence of length $L$, with hidden dim $d$ and head dim $d_k = d / h$:

1. **Project** the input $X \in \mathbb{R}^{L \times d}$ into queries, keys, values via learned matrices $W_Q, W_K, W_V$:
   
   $$Q = XW_Q, \quad K = XW_K, \quad V = XW_V$$

2. **Compute attention scores** (similarity of each query to each key):

   $$S = \frac{QK^T}{\sqrt{d_k}} \in \mathbb{R}^{L \times L}$$

3. **Apply causal mask** (set future positions to $-\infty$).

4. **Softmax** over keys:

   $$A = \text{softmax}(S)$$

5. **Weighted sum of values:**

   $$Z = A V$$

6. **Project** back: $Y = Z W_O$.

**Multi-head** = do steps 1-5 in parallel across $h$ heads, each with $d_k = d/h$ dimensions, then concatenate and project.

$$\text{MHA}(X) = \text{concat}(Z_1, \ldots, Z_h) W_O$$

**Why divide by $\sqrt{d_k}$?** Without it, dot products grow as $O(\sqrt{d_k})$, pushing softmax into saturated regions where gradients vanish.

**Why multiple heads?** Different heads specialize (syntactic vs semantic, local vs distant, etc.). Empirically, 8-32 heads is the sweet spot.

**Quadratic cost:** step 2 is $O(L^2 d)$, which dominates for long sequences. This is why FlashAttention, sparse attention, Mamba, etc. all exist.

```python
import torch, torch.nn as nn, torch.nn.functional as F

class CausalSelfAttention(nn.Module):
    def __init__(self, d_model, n_heads):
        super().__init__()
        self.n_heads = n_heads
        self.d_k = d_model // n_heads
        self.qkv = nn.Linear(d_model, 3 * d_model, bias=False)
        self.proj = nn.Linear(d_model, d_model, bias=False)

    def forward(self, x):
        B, L, D = x.shape
        qkv = self.qkv(x).reshape(B, L, 3, self.n_heads, self.d_k).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]               # (B, H, L, d_k)
        scores = q @ k.transpose(-2, -1) / (self.d_k ** 0.5)
        mask = torch.tril(torch.ones(L, L, device=x.device)).view(1, 1, L, L)
        scores = scores.masked_fill(mask == 0, float("-inf"))
        attn = F.softmax(scores, dim=-1)
        out = (attn @ v).transpose(1, 2).reshape(B, L, D)
        return self.proj(out)
```

---

## Q13. KV cache — the secret to fast autoregressive inference { #q13 }

**The problem:** at inference, we generate one token at a time. Naively, each new token requires re-running attention over all previous tokens, giving $O(L^2)$ per step and $O(L^3)$ for a full sequence.

**The insight:** for a newly generated token at position $L$, we only need to compute *its* query, and *its* interaction with keys and values for positions $0 \ldots L$. Keys and values for positions $< L$ were *already computed* in the previous step. Cache them.

**Pseudocode:**

```python
# Cache: for each layer, store (K, V) of shape (batch, n_heads, current_len, d_k)
past_kv = [(None, None) for _ in layers]

for t in range(max_new_tokens):
    # Only compute for the NEW token (1 position)
    x_new = embed(token_t)   # (B, 1, D)
    
    for l, (W_q, W_k, W_v, ...) in enumerate(layers):
        q_new = x_new @ W_q     # (B, H, 1, d_k)
        k_new = x_new @ W_k
        v_new = x_new @ W_v
        
        # Concatenate with cached K, V
        if past_kv[l][0] is not None:
            k = torch.cat([past_kv[l][0], k_new], dim=2)
            v = torch.cat([past_kv[l][1], v_new], dim=2)
        else:
            k, v = k_new, v_new
        past_kv[l] = (k, v)
        
        # Attention: query is new (L=1), keys/values span full history
        attn = (q_new @ k.transpose(-2, -1)) / (d_k ** 0.5)
        attn = softmax(attn)
        out = attn @ v   # (B, H, 1, d_k)
        # ... MLP, residuals ...
    
    token_t = sample(out)
```

**Result:** $O(L)$ per token instead of $O(L^2)$ — orders of magnitude faster.

**KV cache memory cost** for a single sequence:

$$\text{Memory} = 2 \times n_{\text{layers}} \times n_{\text{kv heads}} \times d_{\text{head}} \times L \times \text{bytes/elem}$$

For Llama 3 70B at 32k context in BF16: $2 \times 80 \times 8 \times 128 \times 32768 \times 2 = 10.7$ GB *per sequence*. The KV cache dominates memory at long context — larger than the model weights for long contexts.

**Optimizations built on top:**
- **Grouped-query attention (GQA):** share K/V across groups of query heads, cutting KV cache by 4-8×.
- **Multi-query attention (MQA):** extreme case — one K/V head for all queries.
- **Paged attention (vLLM):** manage KV cache in fixed-size "pages" (like OS virtual memory) to avoid fragmentation.
- **KV cache quantization:** store K/V in INT8 or INT4.

---

## Q14. What determines the maximum context length? { #q14 }

Three hard constraints and two soft ones.

**Hard constraint 1 — positional encoding range.** If the model was trained with absolute positions 0..4095, it genuinely doesn't know how to represent position 5000. RoPE and ALiBi (relative positional encodings) mitigate this, but extrapolation beyond the training distribution degrades quality unless you use scaling tricks.

**Hard constraint 2 — attention compute.** $O(L^2 d)$ FLOPs per layer. At $L = 128k$, this is ~$10^{11}$ ops per layer — FlashAttention and sparse attention are essential to make this tractable.

**Hard constraint 3 — KV cache memory.** At 128k context, per-sequence KV cache for Llama 3 70B is ~43 GB. You're not fitting many concurrent requests.

**Soft constraint 1 — "effective" context.** Models are trained with certain context distribution. They often *ignore* information in the middle of long contexts ("lost in the middle," Liu et al. 2023), even when they technically attend over it.

**Soft constraint 2 — retrieval quality in context.** Needle-in-a-haystack tests show that even 1M-context models have degraded recall past a certain point — Claude 3, Gemini 1.5 Pro remain the strongest long-context retrievers in 2026 benchmarks.

**Techniques for extending context:**

| Technique | Approach | Typical gain |
|---|---|---|
| RoPE linear scaling (PI) | Divide position indices by $k$ | 4-8× |
| NTK-aware RoPE scaling | Adjust base frequency $\theta$ | 4-32× |
| YaRN | Per-dim frequency interpolation | 16-32× |
| LongRoPE | Find optimal per-dim scaling | 256× (8k → 2M) |
| Sliding window (Mistral) | Local attention + recurrence | Unbounded, linear mem |
| Infini-attention (Google) | Linear attention + memory | Unbounded |
| Mamba / SSM | Recurrent (non-attention) | Unbounded, linear mem |

---

## Q15. FlashAttention — what problem does it actually solve? { #q15 }

**The observation (Dao et al. 2022):** standard attention is **memory-bound**, not compute-bound, on modern GPUs. Computing $QK^T$, then softmax, then multiplying by $V$ materializes an $L \times L$ intermediate matrix — gigabytes of HBM traffic for long sequences.

**FlashAttention's trick — "tiling + online softmax":**

1. Never materialize the full attention matrix.
2. Process $Q, K, V$ in tiles (e.g., 128×128 blocks) that fit in on-chip SRAM.
3. Use the **online softmax** algorithm (Milakov & Gimelshein 2018) to compute softmax block-by-block, maintaining running max and sum statistics.
4. Accumulate output incrementally.

**Result:** same math, same numerical accuracy, but **2-4× faster** and **10-20× less memory** for long sequences.

**FlashAttention 2 (2023):** optimized backward pass, better parallelization across sequence dimension.

**FlashAttention 3 (2024):** asynchronous software pipelining for Hopper (H100), FP8 support. ~1.5-2× faster than FA2.

**Key point for interviews:** FlashAttention does **not change the math** (it's exact, not approximate). It's a memory-hierarchy-aware implementation of the same attention. Both the forward pass and gradients are identical.

```python
# FlashAttention is exposed via torch.nn.functional.scaled_dot_product_attention
# in PyTorch 2+ — with automatic backend selection (FA, memory-efficient, math)
import torch.nn.functional as F

out = F.scaled_dot_product_attention(q, k, v, is_causal=True)
# PyTorch picks the fastest backend automatically
```

**Approximate alternatives (different trade-off: sacrifice exactness for speed):**
- **Sparse attention** (Longformer, BigBird): only attend to a subset of positions.
- **Linear attention** (Performer, Linformer): $O(L)$ via kernel tricks.
- **Mamba / SSM:** replace attention entirely with recurrent state-space models.

---

## Q16. Context rot, lost-in-the-middle, and long-context weaknesses { #q16 }

Even models that technically support 128k+ contexts often fail to *use* them effectively. Three key phenomena:

**1. Lost in the Middle (Liu et al. 2023):** when relevant information is in the middle of a long context, retrieval accuracy dips significantly. Models show a U-shape: great at the beginning (primacy) and end (recency), worse in the middle.

**2. Attention sinks (Xiao et al. 2023):** the first few tokens of a sequence soak up disproportionate attention mass — often "filler" tokens that end up being used as attention "sinks" where the model dumps attention budget. Removing them corrupts long-context reasoning.

**3. Needle-in-a-haystack tests:** hide a fact at position $p$ in a long document, ask the model to retrieve it. Modern frontier models (Claude 3 Opus, GPT-4 Turbo, Gemini 1.5 Pro) are near-perfect at short haystacks but degrade past 32-64k depending on position.

**Mitigations at inference:**
- **Place the instruction at both start and end** of a long context. Models attend more heavily to ends.
- **RAG instead of stuff-the-context:** retrieve top-k relevant chunks and put just those in context, rather than dumping the entire document.
- **Re-ranking:** after retrieving candidates, a reranker model scores them — higher-quality inputs to the LLM.
- **Hierarchical summarization:** summarize chunks, then summarize summaries.

<div class="scenario" markdown>
**Scenario — legal contract analysis on 200-page documents:** naively putting the full document in a 128k context gives ~70% recall on questions about clauses in the middle. Two-stage approach: chunk into 2-page sections, retrieve top-5 relevant chunks with a BGE/E5 embedding model, rerank with Cohere Rerank or a custom reranker, pass top-3 to Claude/GPT-4. Recall jumps to ~92%. Costs 20× less in tokens.
</div>

---

## Q17. Training a base LLM — the pretraining recipe { #q17 }

**Data (2024-2026 standard):**
- Web scrape (Common Crawl, filtered and deduplicated aggressively) — 60-80% of tokens.
- Books, papers, encyclopedic sources — ~5-15%.
- **Code** — 10-25%, crucial for reasoning quality.
- Mathematical texts, proofs, Q&A (GSM8K-style) — 2-5%.
- Multilingual corpora for non-English capability — varies.
- **Synthetic data** (2024+ trend): teacher models generate textbooks, Q&A, code explanations. Phi family was the big proof point.

**Preprocessing:**
- **Deduplication** (near-exact via MinHash, plus exact via hash). Reduces memorization and improves quality.
- **Quality filtering** with a classifier (good-vs-bad text) or perplexity filtering.
- **Contamination filtering:** remove documents containing common benchmark questions.
- **PII scrubbing:** a weak guarantee, but standard.
- **Tokenize** once, store as binary shards (webdataset, mosaicml-streaming).

**Architecture (Llama 3 style):**
- Decoder-only transformer, pre-norm, RMSNorm.
- RoPE positional encoding, possibly scaled for long context.
- SwiGLU MLP, no MLP bias.
- GQA (grouped-query attention) — e.g., 8 K/V heads per 32 Q heads.
- Vocab size 32k-256k depending on multilingual needs.

**Training:**
- **AdamW**, $\beta_1 = 0.9$, $\beta_2 = 0.95$, weight decay 0.1.
- **LR schedule:** linear warmup (2-4k steps) → cosine decay to ~10% of peak.
- **Peak LR:** 6e-4 for ~7B, scaling inversely with model size (1.5e-4 for 70B).
- **BF16** mixed precision (FP32 master weights).
- **Gradient clipping** at 1.0.
- **Batch size:** 0.5M to 4M tokens (large batches needed for stable training at scale).
- **Duration:** 1-15T tokens. Chinchilla says 20 tokens/param is optimal; 2024+ practice is 100-1000+ tokens/param for better inference economics.

**Infra:**
- **3D parallelism:** data + tensor + pipeline. FSDP for medium scale, Megatron-style for frontier scale.
- **Gradient checkpointing** for activation memory.
- **FP8** on H100+ for the largest runs.

**Cost:** ~1-2M H100-hours for a 70B model on 15T tokens. At $2/H100-hour = $2-4M in raw compute.

---

## Q18. Compute and memory: how do you estimate them? { #q18 }

**FLOPs for training** (decoder-only transformer, standard estimate):

$$C \approx 6 N D$$

where $N$ = parameters, $D$ = training tokens. The "6" comes from 2 FLOPs per forward MAC, plus 2× for backward, plus 1× for activation recomputation (ballpark).

- Llama 3 70B trained on 15T tokens: $6 \times 70 \times 10^9 \times 15 \times 10^{12} = 6.3 \times 10^{24}$ FLOPs.
- At H100 peak BF16 = ~$10^{15}$ FLOPs/sec, with 40-50% utilization: $6.3 \times 10^{24} / (5 \times 10^{14}) = 1.3 \times 10^{10}$ GPU-seconds = 1.45M H100-hours.

**FLOPs for inference** (generating one token):

$$C \approx 2N$$

So a 70B model: 140G FLOPs per token. At H100 peak + bandwidth limits, ~50-100 tok/sec per GPU batch of 1.

**Memory for inference** (rough):

$$M_{\text{total}} = N \cdot \text{bytes}_{\text{weights}} + M_{\text{KV cache}} + M_{\text{activations}}$$

For Llama 3 70B in INT8:
- Weights: $70 \times 10^9 \times 1 = 70$ GB
- KV cache at 32k context: ~10 GB per sequence
- Activations: small (few hundred MB per layer in flight)

**Memory for training** (rough): $16 N$ bytes for Adam states + weights + gradients (as covered in the Deep Learning optimization module), plus activations scaling with batch size and sequence length.

<div class="tip-box" markdown>
**Back-of-envelope rule:** in an interview, you should be able to estimate in your head: "a 70B model takes ~140 GB in FP16, so it fits on 2× 80GB H100s with some room for KV cache. A 7B model takes ~14 GB in FP16, fits comfortably on a 24 GB consumer GPU." If you can't, you're not yet at senior level for GenAI systems.
</div>

---

## Q19. What does GPT-4, Claude, or Llama know — and how do we know that? { #q19 }

**Base knowledge = a snapshot of the training data, plus emergent generalization.**

**What base models "know":**
- Facts present in training corpus (Wikipedia-like knowledge, code patterns, common concepts).
- Semantic and syntactic patterns across languages.
- Procedural knowledge for tasks represented in the data (sorting algorithms, proof patterns, translation mappings).

**What base models *don't* know:**
- Events after training cutoff (post-training knowledge is *not* in the base model — retrieval is how this gap is bridged).
- Private data (your company's internal docs).
- Facts that aren't represented in text (sensory experiences, some tacit skills).
- The "right" answer when facts are rare — they'll confidently interpolate, leading to hallucinations.

**Epistemic properties:**

1. **Calibration:** raw base models tend to be reasonably calibrated. Instruction-tuned models are *worse* calibrated — they've been trained to sound confident.
2. **Consistency across paraphrases:** models often answer differently to paraphrases of the same question. Robustness across wordings is an active research area.
3. **Training cutoff is "fuzzy":** models don't cleanly know "my training data ends on March 31, 2024." They'll often confidently discuss events right up to (or past) the cutoff based on anticipatory mentions.

**How to probe what a model knows:**

```python
# A good probe: ask the model its own knowledge cutoff + confidence
"What is your training cutoff date? Are you uncertain about any recent events?"

# Better: test with known-post-cutoff facts
"Who won the 2024 US presidential election?"
# If answered correctly → post-cutoff info leaked into training
# If hallucinated → no knowledge, but no awareness of ignorance
# If "I don't know post-X date" → well-calibrated
```

---

## Q20. Instruction tuning vs base models — what's the difference? { #q20 }

A **base model** is the output of pretraining. Give it "Q: What is the capital of France?" and it might continue with "A: Paris" — or it might continue with "Q: What is the capital of Spain?" because it's continuing a list-of-questions pattern. **Base models autocomplete; they don't obey.**

**Instruction tuning (SFT)** = supervised fine-tuning on (instruction, response) pairs. Crafted/curated datasets of "task-follow pairs" teach the model to be a helpful assistant.

**Examples of instruction data:**
- FLAN, Super-NaturalInstructions — academic datasets of diverse NLP tasks.
- Dolly, OpenAssistant — human-generated.
- Alpaca, Vicuna, WizardLM — generated from larger models (self-instruct paradigm).
- Ultrachat, OpenHermes — large-scale synthetic multi-turn chat.

**After SFT, what's different?**
- Model follows instructions reliably (answers direct questions).
- Model outputs well-formatted responses (markdown, lists, JSON when asked).
- Model refuses clearly unsafe requests (to varying degrees).
- **But:** SFT alone produces less-nuanced behavior than RLHF/DPO — models can be over-verbose, less helpful on edge cases, and more prone to hallucination under pressure.

**Alignment pipeline in 2026 (the standard):**

```
Pretrained base model
    ↓  SFT on curated instruction data
Instruction-tuned model
    ↓  RLHF or DPO on preference data
Aligned model (the "chat" release)
    ↓  Safety tuning, refusal training, red-teaming
Production model
```

**What you serve to users** is almost always the final aligned model. Base models are released primarily for researchers and fine-tuning workflows.

<div class="scenario" markdown>
**Scenario — SFT over-verbose, loses quality on long contexts:** a common failure after SFT is that the model becomes overly wordy on short queries ("Here's a comprehensive answer…") and sometimes drops structural precision on long-context tasks. Mitigation: add preference data where concise responses are preferred to verbose ones for simple queries, then DPO. This is exactly what the transition from SFT-only models to RLHF/DPO-aligned models fixed in 2023-2024.
</div>

---

## ✅ Module Recap

- An **LLM** = decoder-only transformer trained on next-token prediction at scale. "Large" is $\geq 7$B parameters in 2026 practice.
- **Decoder-only won** because of unified interface, clean scaling, KV cache, and emergent few-shot.
- **Tokenization matters** commercially (cost per token), technically (numbers, code), and strategically (tokenizer–model binding is permanent).
- **RoPE** is the dominant positional encoding in 2024+, with scaling tricks (YaRN, LongRoPE) for long context.
- **Scaling laws (Chinchilla)** say 20 tokens/param is pretraining-optimal; 2024+ practice pushes this to 100-1000+ for cheaper inference.
- **Emergence is real but partially a measurement artifact** — smooth metrics smooth it out.
- **KV cache** makes autoregressive inference $O(L)$ per token instead of $O(L^2)$; it dominates memory at long context.
- **FlashAttention** is exact and just memory-hierarchy-aware; not approximate.
- **Lost-in-the-middle** and attention sinks make long-context real-world retrieval weaker than benchmarks suggest.
- **Instruction tuning** is what makes a model "chat-like"; **RLHF/DPO** on top gives production-grade quality.

→ Next: [✍️ Prompting & In-Context Learning](prompting.md)
