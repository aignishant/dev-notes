# 📋 Rapid Revision

> The night before your interview, read only this. Every formula, every rule of thumb, every phrase that senior engineers use when they talk about deep learning. Nothing here is filler.

---

## 🧠 The 20 facts you cannot fumble

1. **Backprop is chain rule.** Gradient at layer $l$ = gradient from layer $l+1$ × local Jacobian.
2. **Vanishing gradient = product of many small values → 0.** Fix: ReLU, Kaiming init, BatchNorm, residuals.
3. **ReLU > sigmoid** because its gradient is 1 (not ≤ 0.25) in the active region.
4. **Softmax + cross-entropy are numerically combined** for stability: don't compute softmax then log separately.
5. **Adam ≠ AdamW.** For anything with weight decay, use AdamW.
6. **BN normalizes across batch; LN normalizes across features.** Transformers use LN because sequences have variable length.
7. **Dropout is disabled by `.eval()`.** If you forget, your model's predictions will be garbage at inference.
8. **Attention cost is $O(L^2 d)$** in sequence length $L$ and dim $d$. FlashAttention reduces memory, not FLOPs.
9. **KV cache grows linearly with context length** — the real bottleneck for long-context LLM inference.
10. **RoPE and ALiBi** are the two dominant positional encodings in 2026 LLMs.
11. **Temperature $T > 1$** flattens distributions (more random); $T < 1$ sharpens (more deterministic).
12. **Top-k, top-p (nucleus), beam search** are the three sampling strategies you must know.
13. **Teacher forcing** during training causes **exposure bias** at inference — the model sees its own errors for the first time.
14. **LoRA** = freeze base weights, train $W + \Delta W$ where $\Delta W = AB$, $A, B$ low rank. Typical $r=8$ or $r=16$.
15. **QLoRA** = 4-bit base + LoRA adapters, enables fine-tuning 65B on one GPU.
16. **Distillation** = student trained on soft targets from teacher. Use temperature $T = 3-5$.
17. **Pruning (structured) + quantization (INT8 or INT4)** can shrink a model 10-20× with <2% accuracy drop.
18. **FSDP/ZeRO-3** shards parameters, gradients, and optimizer states across GPUs. Lets you train 100B+ models.
19. **Gradient checkpointing** saves activations only at marked points; recomputes in backward. Trade ~33% compute for ~80% activation memory.
20. **Universal approximation theorem:** a 2-layer network with enough units can approximate any continuous function. Depth helps with *efficiency*, not expressiveness.

---

## 🔢 Formulas to know cold

### Losses

$$\text{BCE}(y, \hat{y}) = -[y \log \hat{y} + (1-y) \log(1-\hat{y})]$$

$$\text{CE}(y, \hat{y}) = -\sum_c y_c \log \hat{y}_c$$

$$\text{Focal}(y, \hat{y}) = -\alpha (1-\hat{y}_y)^\gamma \log \hat{y}_y$$

$$\text{KL}(P \| Q) = \sum_x P(x) \log \frac{P(x)}{Q(x)}$$

### Activations and gradients

$$\text{ReLU}(x) = \max(0, x) \quad \text{ReLU}'(x) = \mathbb{1}[x > 0]$$

$$\sigma(x) = \frac{1}{1 + e^{-x}} \quad \sigma'(x) = \sigma(x)(1 - \sigma(x))$$

$$\text{GELU}(x) = x \Phi(x) \approx 0.5 x \left(1 + \tanh\left(\sqrt{2/\pi}(x + 0.044715 x^3)\right)\right)$$

$$\text{SiLU}(x) = x \cdot \sigma(x)$$

$$\text{softmax}(z)_i = \frac{e^{z_i}}{\sum_j e^{z_j}}$$

### Attention

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right) V$$

### Optimizers

$$\text{SGD + momentum:} \quad v \leftarrow \mu v + g, \quad \theta \leftarrow \theta - \eta v$$

$$\text{Adam:} \quad m \leftarrow \beta_1 m + (1-\beta_1) g, \quad v \leftarrow \beta_2 v + (1-\beta_2) g^2$$

$$\hat{m} = m / (1 - \beta_1^t), \quad \hat{v} = v / (1 - \beta_2^t), \quad \theta \leftarrow \theta - \eta \hat{m} / (\sqrt{\hat{v}} + \epsilon)$$

### Normalization

$$\text{BN/LN: } \hat{x} = \gamma \cdot \frac{x - \mu}{\sqrt{\sigma^2 + \epsilon}} + \beta$$

### Information

$$H(X) = -\sum_x p(x) \log p(x) \quad \text{(entropy)}$$

$$\text{Perplexity} = \exp(\text{average CE})$$

---

## 🎯 Architecture cheat codes

### CNN output shape

$$H_{out} = \left\lfloor \frac{H_{in} + 2P - D(K-1) - 1}{S} + 1 \right\rfloor$$

Parameters in a Conv2d: $C_{in} \times C_{out} \times K \times K + C_{out}$ (bias).

### Transformer parameter count (roughly)

For a decoder-only transformer with $L$ layers, hidden dim $d$, MLP factor 4:
- Per block: $4d^2$ (QKV + output projection) + $8d^2$ (MLP) = $12d^2$
- Total (ignoring embeddings): $12 L d^2$

GPT-3 175B check: $L=96$, $d=12288$ → $12 \times 96 \times 12288^2 \approx 174B$. ✅

### Memory budget (training)

| Component | Bytes/param (BF16 mixed) |
|---|---|
| BF16 weights | 2 |
| FP32 master copy | 4 |
| BF16 gradients | 2 |
| FP32 Adam `m`+`v` | 8 |
| **Static total** | **16** |

For a 7B model: 112GB just for static state. Add activations.

---

## 🗺 Decision tree for interview questions

```
What problem?
├─ Image classification
│    ├─ Small data (<10k)    → Pretrained ResNet/ViT + heavy augmentation + early stopping
│    ├─ Medium (10k-1M)      → ViT-B or EfficientNet, RandAugment, MixUp, label smoothing
│    └─ Large (>1M)          → ViT-L/H, MAE or DINOv2 pretraining, scaling LR with batch
│
├─ Detection / Segmentation
│    ├─ Real-time            → YOLOv8, RT-DETR
│    ├─ Accuracy-first       → DETR, DINO, Mask2Former
│
├─ Sequence
│    ├─ Short (≤512)         → Transformer encoder/decoder
│    ├─ Streaming            → RNN/LSTM or Mamba (SSM)
│    ├─ Very long (>32k)     → Longformer, BigBird, or sliding-window Mistral-style
│
├─ Text generation
│    ├─ Fine-tuning 7B-70B   → LoRA or QLoRA + AdamW + cosine + warmup
│    ├─ Serving              → vLLM + paged attention + speculative decoding + FP8
│    ├─ Alignment            → SFT → DPO or RLHF (PPO)
│
├─ Embeddings / Retrieval
│    ├─ Text                 → Sentence-T5, E5, BGE
│    ├─ Multi-modal          → CLIP, SigLIP
│
└─ Reinforcement learning
     ├─ Discrete actions     → DQN family (Rainbow)
     ├─ Continuous actions   → PPO, SAC
     ├─ From demonstrations  → Behavior cloning + DPO/RLHF
```

---

## 💬 Phrases that earn points

- "*Let me first scope the problem before choosing an architecture.*"
- "*What are we optimizing for — accuracy, latency, memory, fairness?*"
- "*I'd start with the simplest baseline that could plausibly work, then iterate.*"
- "*Before adding regularization, let me check the data: shuffling, leakage, labels.*"
- "*The first debugging step is to overfit a batch of 4 — if I can't, I have a bug, not a hyperparameter problem.*"
- "*AdamW, not Adam — weight decay should be decoupled from the gradient update.*"
- "*I'd use LayerNorm here, not BatchNorm, because of variable-length sequences.*"
- "*For 200ms latency, I'd distill to a smaller model, quantize to INT8, and use TensorRT.*"
- "*Pretraining on in-domain data with a self-supervised objective before fine-tuning usually pays off.*"
- "*I'd want to see per-class and per-slice metrics before trusting mean accuracy.*"

## 🚫 Phrases that lose points

- "Adam is always better than SGD." (False for vision.)
- "More layers is always better." (No — depth has diminishing returns; scaling laws are joint in data, params, compute.)
- "I'd just throw more data at it." (Without characterizing the problem, this is a junior answer.)
- "Dropout = 0.5 is standard." (0.5 is aggressive; modern default is 0.1–0.3 depending on model.)
- "We'd use BERT." (BERT is 2018 architecture — for classification, a modern encoder is better; for generation, a decoder. Show you know the landscape.)
- "The learning rate doesn't matter much." (It matters more than any other hyperparameter.)
- "I'll figure it out once I see the data." (Fine in practice — a trap in interviews. Come with a structured plan.)

---

## ⚙️ Hyperparameter starting points (2026 defaults)

| Task | Optimizer | LR | Batch | Warmup | Decay | Weight decay |
|---|---|---|---|---|---|---|
| CNN classification (small) | SGD+mom | 0.1 → 0.001 | 256 | 5 epochs | cosine | 5e-4 |
| ViT-B | AdamW | 1e-3 | 1024–4096 | 10k steps | cosine | 0.05 |
| BERT pretraining | AdamW | 1e-4 | 256 | 10k steps | linear | 0.01 |
| GPT pretraining | AdamW | 6e-4 → 6e-5 | 0.5–4M tokens | 2k–10k steps | cosine | 0.1 |
| LLM fine-tuning (full) | AdamW | 2e-5 | 32 | 3% | cosine | 0.0 |
| LoRA fine-tuning | AdamW | 1e-4 | 16–64 | 3% | cosine | 0.0 |
| QLoRA (70B) | Paged AdamW | 2e-4 | 16 | 3% | cosine | 0.0 |
| RL fine-tune (PPO) | AdamW | 1e-6 to 5e-7 | small | — | linear | 0.0 |

---

## 🧩 Shapes I always verify when writing model code

- Input tensor shape: `(B, C, H, W)` for images, `(B, L)` for tokens, `(B, L, d)` for embeddings.
- Attention scores: `(B, H, L_q, L_k)` — not `(B, L, L, H)`.
- Multi-head split: `d = num_heads × head_dim`, not `d × num_heads`.
- Broadcasting traps: `(B, 1, L)` mask vs `(B, L)` labels — always check before `masked_fill`.
- Loss expects `logits`, not probs — `CrossEntropyLoss` does log-softmax internally.

---

## 🧪 Debugging checklist (print this out)

1. Loss is NaN → clip gradients, lower LR, check for log(0).
2. Loss doesn't decrease → wrong loss? wrong label shape? LR too small?
3. Val >> train loss → overfit; regularize.
4. Val ≈ train loss but both high → underfit; bigger model, more epochs, higher LR.
5. Training is slow → check GPU util; if low, data pipeline is the bottleneck.
6. Model works in training but bad in prod → `.eval()` mode? preprocessing mismatch?
7. Distributed training is unstable → LR scaled with batch? Warmup long enough? Sync BN?
8. OOM → gradient checkpointing, smaller batch + gradient accumulation, FSDP, mixed precision.

---

## 🔗 Top resources (for the week before)

- **"The Little Book of Deep Learning"** — François Fleuret (free PDF). Read it end to end.
- **"Neural Networks: Zero to Hero"** — Karpathy's YouTube series. Build a transformer from scratch.
- **"Deep Learning Tuning Playbook"** — Google Research. Hyperparameter bible.
- **Papers to have skimmed**: Attention Is All You Need, BERT, GPT-3, LLaMA 2/3, FlashAttention, LoRA, DPO, RoPE, ALiBi, RWKV, Mamba.
- **Blog posts**: Lilian Weng's blog, Chip Huyen's *Designing ML Systems*, Jay Alammar's illustrated transformer.

---

## 🏆 Night-before ritual

1. **Review the 20 facts above.** Close the doc, recite them.
2. **Redraw one transformer block** from memory — attention path + MLP path + norms + residuals.
3. **Write out Adam update rule** from memory.
4. **Explain backprop for a 2-layer MLP** out loud to your rubber duck.
5. **Review your own past project.** Three numbers (dataset size, accuracy, latency). Three trade-offs. Three things you'd do differently.
6. **Sleep.** Eight hours beats four hours of last-minute cramming. This isn't false — the literature on consolidation is unambiguous.

---

**You've got this.** Deep learning interviews reward clarity of thinking far more than memorized detail. Explain, don't recite. Admit uncertainty, then reason your way to an answer. That's what senior engineers sound like.

🎯 *Now go crush it.*
