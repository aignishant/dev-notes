# 🎤 Mock Interviews — Deep Learning

> Three progressively harder interview simulations, modeled on what you'll actually face at FAANG, top AI labs, and unicorn startups. Each includes expected answers, rubrics, and the follow-up questions senior interviewers ask when they sense you've gone deeper than the surface.

---

## 🎯 Round 1 — Phone Screen (45 min)

**Role:** Mid-level Deep Learning Engineer
**Interviewer stance:** Fast, breadth-oriented. Wants to weed out surface-level candidates. Expects crisp answers to 6-8 questions in 45 minutes.

---

### Warm-up (5 min)

**Q: Walk me through a deep learning project you've shipped, focusing on the one architectural decision you'd revisit.**

*What they're testing:* Can you talk about trade-offs? Do you own your mistakes?

**Strong-answer structure:**
1. **Context** (30s): "At [company], I trained a model to classify X from Y. Dataset was ~N samples, class imbalance Z:1. Ship constraint: <K ms latency on CPU."
2. **Decision + rationale** (1 min): "We chose MobileNetV3 + FPN instead of a full ResNet-50 — latency mattered more than 0.5% accuracy. Also used focal loss because of the imbalance."
3. **What you'd revisit** (1 min): "In retrospect, we should have used knowledge distillation from an EfficientNet-B3 teacher. We left ~2% accuracy on the table because we didn't have time to build the distillation pipeline — that would have been the next iteration."

*Red flags:* listing frameworks, no numbers, no reflection.

---

### Technical breadth (25 min)

**Q1: Explain why we need activation functions in neural networks.**

*Expected:* Without non-linearities, a stack of linear layers collapses to a single linear transformation. No matter how many layers, you'd only represent linear functions. Activation functions (ReLU, GELU, etc.) break linearity, allowing arbitrary function approximation (universal approximation theorem).

*Follow-up:* "What happens if you use a linear activation in the hidden layers but softmax at the output?" → Still just logistic regression. Can't learn anything non-linearly separable.

---

**Q2: What's the vanishing gradient problem, and how do modern architectures handle it?**

*Expected:* In deep networks with saturating activations (sigmoid, tanh), gradients shrink exponentially with depth during backprop. Mitigations: ReLU/GELU (non-saturating), proper init (Xavier for sigmoid/tanh, Kaiming for ReLU), BatchNorm/LayerNorm (stabilizes activations), residual connections (identity path lets gradients flow), LSTM/GRU gates (for RNNs).

*Follow-up:* "Why do residual connections specifically help?" → Identity path provides uninterrupted gradient flow. Formally: $\partial L / \partial x = \partial L / \partial y \cdot (1 + \partial F / \partial x)$ — the "+1" ensures gradients don't fully vanish even if $F$ produces small gradients.

---

**Q3: Walk through the math of backprop for a simple network: $y = W_2 \sigma(W_1 x)$, loss $L = \frac{1}{2}(y - t)^2$. Compute $\partial L / \partial W_1$.**

*Expected:* Chain rule, carefully:

$$\frac{\partial L}{\partial W_1} = \underbrace{(y - t)}_{\partial L/\partial y} \cdot \underbrace{W_2^T}_{\partial y/\partial h} \cdot \underbrace{\sigma'(W_1 x)}_{\partial h/\partial z_1} \cdot \underbrace{x^T}_{\partial z_1/\partial W_1}$$

where $h = \sigma(z_1)$ and $z_1 = W_1 x$. Shapes must match — this is where candidates usually stumble.

*Red flag:* can't do shape analysis. Interviewers at Meta, Google DeepMind, OpenAI will 100% ask derivations.

---

**Q4: Batch norm vs layer norm — why transformers use LayerNorm.**

*Expected:* BN normalizes over (N, H, W) per channel → depends on batch statistics, mixes samples. LayerNorm normalizes per-token over feature dimension → independent of batch, same behavior at train/test. For variable-length sequences, BN is problematic (padded positions pollute statistics, different sequence lengths give different channel stats). LN is natural for tokens.

*Follow-up:* "Why not InstanceNorm?" → IN would normalize per-channel per-token, reducing information that differentiates channels. LN preserves feature magnitudes.

---

**Q5: You're training a CNN and your validation accuracy is 99% but test accuracy on new data is 70%. What's wrong?**

*Expected:*
1. **Data leakage** (most common): validation was drawn from the same distribution as train (e.g., same patients split across train/val). Need patient-level split, not image-level.
2. **Distribution shift:** test data is genuinely different (different cameras, lighting, demographics).
3. **Label leakage:** a proxy feature in training perfectly predicts label (e.g., hospital source correlates with disease).

*Follow-up:* "How would you diagnose which?" → Check for near-duplicate samples across splits, analyze per-cluster performance, look at a few misclassified examples for distribution clues.

---

**Q6: Quick succession — what's the difference between: BPE vs WordPiece? LSTM vs GRU? Cross-entropy vs KL divergence? Dropout vs DropConnect?**

*Expected (one-line answers):*
- **BPE vs WordPiece:** BPE merges by frequency; WordPiece merges by likelihood gain (used by BERT).
- **LSTM vs GRU:** LSTM has 3 gates + separate cell state; GRU has 2 gates, simpler, often comparable accuracy.
- **CE vs KL:** CE = $-\sum y \log p$; KL = $\sum y \log(y/p)$. For one-hot labels, KL reduces to CE + constant.
- **Dropout vs DropConnect:** Dropout zeros activations; DropConnect zeros weights.

---

### Coding (10 min)

**Q: Implement scaled dot-product attention in PyTorch from scratch.**

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class ScaledDotProductAttention(nn.Module):
    def forward(self, q, k, v, mask=None):
        # q, k, v shape: (B, H, L, d_k)
        d_k = q.size(-1)
        scores = torch.matmul(q, k.transpose(-2, -1)) / (d_k ** 0.5)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        attn = F.softmax(scores, dim=-1)
        return torch.matmul(attn, v), attn
```

*Follow-ups:*
- "Why divide by $\sqrt{d_k}$?" → Variance of dot product of random vectors grows with dim; scaling keeps softmax from saturating.
- "What's the memory cost?" → $O(L^2)$ — quadratic in sequence length. FlashAttention avoids materializing the full matrix.
- "How would you add a causal mask?" → Upper triangular mask: `torch.triu(torch.ones(L, L), diagonal=1).bool()`, set those positions to -inf.

---

### Rubric

| Score | Meaning |
|---|---|
| **Strong hire** | Derives backprop without hints, articulates trade-offs with numbers, catches own edge cases in code |
| **Hire** | Solid technical answers, maybe fumbles one derivation, writes working code with light guidance |
| **No hire** | Memorized definitions, can't explain *why*, code has shape bugs they can't debug |

---

## 🎯 Round 2 — Deep Dive (60 min)

**Role:** Senior Deep Learning Engineer (L5/E6)
**Interviewer stance:** Skeptical, goes deep on one topic. Will push until you hit your limit. Expects you to own uncertainty gracefully.

**Scenario:** *"We need to train a vision transformer (ViT-L/16) on 50M proprietary images across 100 categories, with severe class imbalance (head classes have 1M examples, tail classes have 200). We have 128 A100s for 2 weeks. Walk me through your approach."*

---

### Phase 1 — Problem decomposition (10 min)

**You should lead with:**
1. "Let me clarify the goal: are we optimizing mean accuracy, balanced accuracy, or per-class recall?"
2. "What's the inference latency budget? That affects architecture."
3. "Are the tail classes important enough to justify sacrificing head-class performance?"

*Why this matters:* interviewers want to see you don't jump to solutions before understanding constraints. A candidate who just says "use focal loss" loses points vs. one who first asks the right questions.

---

### Phase 2 — Training pipeline design (25 min)

**Architecture:**
- ViT-L/16 has 307M params. With AdamW in mixed precision + ZeRO-2, memory per GPU ≈ 12GB for states + activations with batch 128.
- **FSDP or DeepSpeed ZeRO-2** across 128 GPUs. Global batch = 128 × 128 = 16384 images.
- Patch size 16 → 196 tokens for 224×224 inputs. Consider 384×384 inputs if data warrants.

**Handling 50M images:**
- WebDataset / FFCV format (shards of ~1GB each). Standard JPEG decoding is the bottleneck at ~20k images/sec/GPU.
- Preprocessing: resize to 256, random crop 224 at train time. Normalization by ImageNet stats (with caveats — check your data's true stats).

**Class imbalance — 3 complementary approaches:**

1. **Weighted sampler:** each batch contains a bounded # of any class. `WeightedRandomSampler` with weights $\propto 1/\text{count}$ (possibly $\propto 1/\sqrt{\text{count}}$ to avoid over-correcting).
2. **Loss reweighting:** focal loss or class-balanced loss (Cui et al. 2019): $w_c = \frac{1 - \beta}{1 - \beta^{n_c}}$ where $\beta \approx 0.999$.
3. **Two-stage training:** first pretrain on natural distribution, then fine-tune on balanced sampling ("cRT" — classifier retraining). Often best results.

**Optimizer:**
- **AdamW**, LR 1e-3, weight decay 0.1.
- **Linear warmup** for 10k steps, **cosine decay** to 1e-6 over ~300k total steps.
- **Layer-wise LR decay** (0.75) — earlier layers learn slower (they're closer to pretrained init if we're starting from IN-21k).
- Consider **LAMB** if batch >32k.

**Regularization:**
- **Stochastic depth** 0.1 → 0.2 (linear growth with depth).
- **Dropout** 0.1 in the MLP and attention.
- **MixUp (α=0.8) + CutMix (α=1.0)** randomly applied.
- **RandAugment** (num_ops=2, magnitude=9).
- **Label smoothing 0.1.**
- **EMA** of weights (decay 0.9999) — critical for ViT.

**Expected timeline:**
- 300k steps × ~0.5s/step (with FSDP, mixed precision, 128×A100) = ~42 hours = 1.75 days.
- Leaves ~12 days for ablations: augmentation strength, focal loss α/γ, two-stage vs one-stage, etc.

---

### Phase 3 — Debugging deep dive (15 min)

**Interviewer:** "*You ran training for 2 days. Head-class accuracy is 85%, but tail-class accuracy is 12%. What now?*"

**Systematic diagnosis:**

1. **Check the classifier bias:** `b[head] >> b[tail]`? If so, the model has "learned" to predict head classes. → Reset classifier, retrain on balanced sampling (cRT).
2. **Check feature quality on tail classes:** compute t-SNE / UMAP on features. Are tail classes clustered? If yes, problem is in the classifier; if no, the backbone never learned tail-class features.
3. **Check augmentation strength:** maybe too aggressive for small-sample classes. Try per-class augmentation strength.
4. **Check label noise:** with only 200 examples per tail class, even 5 mislabeled examples is 2.5% noise. Use a teacher model / self-supervised pretraining to denoise.

**Advanced moves:**
- **Classifier-free guidance via logit adjustment** (Menon et al.): at inference, subtract $\tau \log p(y)$ from logits.
- **Pretrain with self-supervision** (DINOv2, MAE) on all data including tail, *then* train classifier on balanced subset.
- **Synthetic data generation** via a diffusion model conditioned on tail classes (emerging 2024+ approach).

---

### Phase 4 — Production constraints (10 min)

**Interviewer:** "*We need to deploy this on CPU servers at 50ms latency budget. ViT-L runs at 800ms. What's your plan?*"

**Deployment funnel:**
1. **Distillation** to a much smaller student (e.g., MobileViT or DistilViT): teacher ViT-L → student that's 10-20× smaller. Expected ~2-3% accuracy drop.
2. **INT8 quantization** on the distilled student. Another 2-4× speedup, <1% accuracy drop if using QAT.
3. **Pruning:** structured head pruning — up to 30% of attention heads can go with negligible impact.
4. **ONNX / TensorRT / OpenVINO** export for CPU inference with optimized kernels.

Realistic ending budget: a distilled + quantized + pruned student at ~40ms/image on CPU, within 3% of the teacher's accuracy.

*Follow-up:* "*What if you had GPU inference instead?*" → Keep ViT-L, use FlashAttention, FP16/INT8, TensorRT. Likely fits budget with no compression.

---

### Rubric

| Score | Meaning |
|---|---|
| **Strong hire** | Asks clarifying questions, covers 3-4 regularization axes, proactively discusses failure modes and mitigations, knows scaling (FSDP/ZeRO), mentions pretraining/SSL, gives realistic timeline |
| **Hire** | Hits the obvious bases (ViT, focal loss, AdamW), handles 2/3 follow-ups well, realistic latency plan |
| **No hire** | Name-drops techniques without trade-offs, can't estimate GPU memory, no pretraining strategy, gives vague "more data / better hyperparameters" |

---

## 🎯 Round 3 — System Design (75 min)

**Role:** Staff / Principal Deep Learning Engineer
**Interviewer stance:** Wants to see end-to-end thinking: research, infra, product, business, ethics. Will probe weaknesses.

**Scenario:** *"Design the model training and serving system for a code completion service like GitHub Copilot. It must support 10M developers, with P95 latency <200ms, 40+ programming languages, privacy guarantees for enterprise customers, and continuous improvement from user interactions."*

---

### Phase 1 — Problem framing (10 min)

Before diving in, enumerate:

**Functional requirements:**
- Autocomplete snippets (single line, multi-line).
- Code explanation, refactoring, unit test generation.
- Context: up to 16k tokens of surrounding code.
- Multiple languages, ideally a single model per family (or universal).

**Non-functional requirements:**
- **Latency P95 < 200ms** for first token, stream subsequent tokens.
- **Scale:** 10M devs × avg 100 completions/day = 1B reqs/day ≈ 11.5k QPS average, maybe 50k QPS peak.
- **Privacy:** enterprise code must never leak into the base model.
- **Continuous improvement:** RLHF-style training from accept/reject signals.

**Out-of-scope (clarify):** multi-modal (images in code), autonomous agents, end-to-end IDE integration.

---

### Phase 2 — Model architecture and training (20 min)

**Base model:**
- **Decoder-only transformer** (GPT-style), ~13B-30B parameters for quality, or 3-7B for cost.
- **Long context** via RoPE scaling or sliding-window attention (Mistral-style) — 16k ideal.
- **Fill-in-the-middle (FIM) objective** (Bavarian et al. 2022) during pretraining — crucial for code completion. Standard next-token prediction is insufficient for suggesting mid-line completions.

**Pretraining:**
- Data: public GitHub repos (filtered by license), Stack Exchange, technical docs, language documentation.
- Dedup aggressively (hashing near-duplicate code blocks).
- Hold out: known benchmark problems (HumanEval, MBPP, LeetCode). Data contamination is a major pitfall.
- **Mix ratio:** ~70% code, ~20% natural language, ~10% math. Mixing improves reasoning.
- Train for ~1-2T tokens.

**Fine-tuning:**
- **SFT** on curated pairs (high-quality completions).
- **RLHF or DPO** from in-product accept/reject signals.
- **Per-language fine-tuning** for rare languages (Fortran, Rust) if base model underperforms.

**Evaluation:**
- **HumanEval, MBPP, BigCodeBench** for unit-testable correctness.
- **LiveCodeBench** for contamination-free eval.
- **Human eval** on real-world completions (acceptance rate, edit distance from accepted completion).
- **Per-language breakdown** — aggregate numbers hide failures in rare languages.

---

### Phase 3 — Serving infrastructure (20 min)

**Inference architecture:**
- **TensorRT-LLM or vLLM** for high-throughput inference.
- **Paged attention / KV cache** essential — most requests share common prefixes (file headers, imports).
- **Continuous batching** — process different requests at different decoding steps in same batch.
- **Speculative decoding:** small draft model (e.g., 1B) proposes tokens; large model verifies. 2-3× speedup.
- **Quantization:** INT8 or FP8 weights. Maintains quality, halves memory and often improves throughput.

**Request routing:**
- **Regional pools** of GPUs (us-east, eu-west, ap-south, etc.) — latency requires proximity.
- **Load balancer** routes based on language (language-specific LoRA adapters in some serving cells).
- **Model tiering:** small model (3B) for single-line, large model (30B) for multi-line or complex refactors. Classifier routes the request.

**Capacity planning:**
- 30B model in FP8 = ~30GB. Fits on one H100 (80GB) with KV cache.
- Per H100: ~5000 tok/sec with FlashAttention 3 + continuous batching.
- 50k QPS × 100 tokens per response = 5M tok/sec. → ~1000 H100s globally. Cost: ~$30M/year of GPU rental alone.
- **Cache layer:** vector DB for near-identical completions (popular idioms). Cuts model calls by ~15%.

**Latency budget (P95 < 200ms):**
- Network: 30ms
- Input tokenization + preprocessing: 10ms
- Prefill (context → first token): 100ms (for 2k-token context on A100)
- Buffer: 60ms
→ Streaming the rest tokens at 20-50ms each keeps UX snappy.

---

### Phase 4 — Privacy, security, and ethics (15 min)

**Enterprise privacy:**
- **Inference-only isolation:** enterprise context never goes into training.
- **Per-tenant encryption** at rest and in flight.
- **On-prem / VPC deployment** option for sensitive customers (financial, government, healthcare).
- **Regex / ML-based filter** to prevent leaking training-memorized secrets (API keys, password patterns).

**Memorization risk:**
- Models memorize rare training data (Carlini et al. 2021). Mitigate via:
  - Aggressive dedup at pretraining.
  - Differential privacy during fine-tuning (DP-SGD).
  - Post-hoc scan for known sensitive strings in training data.

**Licensing:**
- Filter training data by license (MIT, Apache, BSD — fine; GPL — controversial, probably exclude).
- Emit license metadata with completions (Copilot's current approach).

**Continuous learning without leakage:**
- RLHF signals aggregated — individual completions never retrain.
- Differential privacy on gradients from user interactions.

**Failure modes:**
- Model suggests insecure code (SQL injection patterns, etc.). → Run static analysis on generated code, flag risky patterns.
- Model suggests broken code → capture accept rate, feed low-acceptance prompts back into training data curation.

---

### Phase 5 — Continuous improvement loop (10 min)

**Data flywheel:**
1. User accepts/rejects suggestions → logged with context (opt-in).
2. High-quality accepted examples → next round of SFT data.
3. Low-quality examples → analyzed for systematic failure modes (e.g., bad at generics in Rust).
4. Per-language metrics drive **targeted data collection** for weak spots.

**Model refresh cadence:**
- Small models: weekly (LoRA adapter training on new examples).
- Base model retraining: quarterly (expensive, but needed to absorb schema shifts).

**A/B testing:**
- Canary new models on 1% of traffic. Monitor acceptance rate, latency, correctness.
- Gradual rollout over 2 weeks. Rollback plan documented.

**Monitoring:**
- Online: acceptance rate, P95/P99 latency, GPU utilization.
- Offline: automated HumanEval runs every deploy, drift detection on input distribution.

---

### Rubric

| Dimension | Strong hire | Hire | No hire |
|---|---|---|---|
| **Scoping** | Asks clarifying qs, articulates NFRs with numbers | Covers functional, less rigor on latency/scale | Dives into model without bounding problem |
| **Model choice** | Justifies decoder-only + FIM + long context with trade-offs | Picks reasonable architecture but weak on FIM | "Just use a transformer" with no specifics |
| **Infra** | Knows vLLM, paged attention, speculative decoding; estimates GPU count | Mentions batching and quantization but rough numbers | Hand-waves serving |
| **Privacy/ethics** | Raises proactively; proposes concrete mitigations | Covers basics when prompted | Only covers if pressed |
| **Data flywheel** | End-to-end accept→retrain loop with DP | Identifies need but not details | Missing |
| **Ownership** | Discusses failure modes and mitigations proactively | Responsive to prompts | Waits to be asked |

---

## 📋 Post-mortem after any mock interview

After every interview (mock or real), write down:

1. **Two questions you answered well** — what made them strong? Replicate.
2. **One question you stumbled on** — was it knowledge, clarity, or nerves?
3. **One phrase that earned visible approval** — reuse it.
4. **The most senior concept you touched** — study it one level deeper for next time.

The people who convert mock interviews into offers do this reflection *every single time*. It's the single highest-ROI habit in interview prep.

→ Next: [📋 Rapid Revision](rapid-revision.md)
