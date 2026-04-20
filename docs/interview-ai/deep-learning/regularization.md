# 🛡️ Regularization & Normalization

> **Q96–Q115 · 20 questions** on the techniques that decide whether your model *generalizes* or memorizes — dropout variants, normalization deep-dives, augmentation, MixUp/CutMix, label smoothing, stochastic depth, knowledge distillation, pruning, and quantization. These are the tools that take a model from "works on the training set" to "ships to production."

---

## Q96. Dropout — mechanics, inverted dropout, and why `.eval()` matters { #q96 }

**Dropout** (Srivastava et al. 2014): during training, randomly zero out each activation with probability $p$ (typically 0.1–0.5). This forces the network to not rely on any single neuron, reducing co-adaptation.

**Inverted dropout** (modern default): scale surviving activations by $1/(1-p)$ during training, so *no* scaling is needed at inference.

$$\tilde{h} = h \cdot \frac{m}{1-p}, \quad m \sim \text{Bernoulli}(1-p)$$

At inference, `.eval()` disables dropout — forgetting to call it is a top-10 deep learning bug.

**Interpretation 1 — ensemble:** each forward pass samples a different "thinned" subnetwork. At test time you're (approximately) averaging $2^n$ subnetworks.

**Interpretation 2 — noise injection:** multiplicative Bernoulli noise in the hidden layer. Noise acts as a regularizer.

```python
class Model(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 256)
        self.drop = nn.Dropout(p=0.3)
        self.fc2 = nn.Linear(256, 10)
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.drop(x)                # active only when model.train()
        return self.fc2(x)
```

| Variant | Drops | Use case |
|---|---|---|
| Standard `nn.Dropout` | Individual activations | MLPs, transformer FFN |
| `nn.Dropout2d` (spatial) | Entire feature maps | Conv layers (channel-wise corr.) |
| `nn.Dropout3d` | Entire 3D feature volumes | Video models |
| Variational dropout | Same mask across timesteps | RNNs (Gal & Ghahramani) |
| DropConnect | Individual weights | Rarely used; more expensive |

<div class="tip-box" markdown>
**Transformer-specific rules of thumb:** residual dropout ~0.1, attention dropout ~0.1, FFN dropout ~0.1. For fine-tuning, keep pretraining dropout or slightly increase it — don't remove it entirely, or the model overfits instantly on small datasets.
</div>

---

## Q97. Weight decay vs L2 regularization — the AdamW distinction (revisited) { #q97 }

**L2 penalty in the loss:** $\mathcal{L}_{\text{reg}} = \mathcal{L} + \frac{\lambda}{2} \|\theta\|^2$. The gradient gets an extra $\lambda \theta$ term.

**Weight decay in the update rule:** multiply $\theta$ by $(1-\eta\lambda)$ at each step — directly shrink weights.

For **SGD**, the two are equivalent:

$$\theta - \eta(g + \lambda\theta) = (1-\eta\lambda)\theta - \eta g$$

For **Adam**, they're *not* equivalent, because L2 gets scaled by the adaptive $1/\sqrt{\hat{v}_t}$ — rarely-updated parameters get under-regularized, often-updated parameters get over-regularized. **AdamW decouples** decay from the gradient update, applying it uniformly.

| Optimizer | L2 in loss | Decoupled decay | Equivalent? |
|---|---|---|---|
| SGD | ✅ | ✅ | Yes |
| Adam | ⚠️ wrong | — | — |
| AdamW | — | ✅ | No, AdamW is correct |

**What should you regularize?** Usually weight matrices, not biases or norm parameters. `no_decay` the biases and BN/LN params:

```python
decay, no_decay = [], []
for n, p in model.named_parameters():
    if p.ndim < 2 or "bias" in n or "norm" in n.lower():
        no_decay.append(p)
    else:
        decay.append(p)
optimizer = torch.optim.AdamW([
    {"params": decay, "weight_decay": 0.1},
    {"params": no_decay, "weight_decay": 0.0},
], lr=3e-4)
```

---

## Q98. Label smoothing — why softmax targets should never be 1.0 { #q98 }

**Vanilla cross-entropy target:** a one-hot vector $[0, 0, 1, 0, 0]$. The model is rewarded for pushing the correct logit to $+\infty$ — causing **overconfidence** and fragile decision boundaries.

**Label smoothing** (Szegedy et al. 2016): replace the target with a mixture of one-hot and uniform:

$$y_i^{\text{LS}} = (1-\epsilon) y_i + \frac{\epsilon}{K}$$

where $K$ = number of classes, $\epsilon \in [0.05, 0.2]$ typically. The model no longer gets asymptotic reward for extreme confidence — logits stay bounded.

**Effects:**
- Better calibration (model confidence matches accuracy).
- Slight accuracy bump (~0.2–0.5%).
- Improved robustness to noisy labels.
- Hurts when you need to distill the model later (softer targets are *less informative* for distillation). Use temperature scaling instead if distillation matters.

```python
# PyTorch supports it natively since 1.10
criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
```

| When to use | When to skip |
|---|---|
| Image classification (ImageNet) | Models you plan to distill from |
| Machine translation (MT) | Tiny datasets (may hurt) |
| Any task with calibration needs | Binary tasks (use BCE tricks instead) |

---

## Q99. Data augmentation — the free regularizer { #q99 }

**Principle:** transform inputs in ways that preserve the label, effectively multiplying dataset size. **Augmentation is usually the cheapest, highest-ROI regularizer you can add.**

**Vision augmentations:**
- *Geometric:* random crop, horizontal flip, rotation, scale, perspective
- *Color:* brightness, contrast, saturation, hue jitter, grayscale
- *Noise/erasing:* Gaussian noise, Cutout, Random Erasing
- *Advanced:* AutoAugment (RL-searched policies), RandAugment (simpler, 2 params), TrivialAugment

**NLP augmentations:**
- Synonym replacement, back-translation, word dropout, EDA
- Most effective at small data scale; at LLM scale, more data > augmentation

**Audio:** SpecAugment — masking time and frequency bands on spectrograms.

```python
from torchvision import transforms as T

train_tf = T.Compose([
    T.RandomResizedCrop(224),
    T.RandomHorizontalFlip(),
    T.RandAugment(num_ops=2, magnitude=9),
    T.ToTensor(),
    T.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
    T.RandomErasing(p=0.25),
])
```

<div class="scenario" markdown>
**Scenario — model overfits on 5k medical images:** Don't just add dropout. First, aggressive augmentation (rotation ±30°, color jitter, elastic deformation, CutMix) can multiply effective dataset size by 10-50× and is nearly always a win for small-data vision. Consult radiologists on which augmentations preserve pathology — e.g., horizontal flip is fine for chest X-rays but wrong for asymmetric organs.
</div>

---

## Q100. MixUp and CutMix — training on mixed inputs { #q100 }

**MixUp** (Zhang et al. 2018): linearly interpolate *two images* and their *labels*:

$$\tilde{x} = \lambda x_i + (1-\lambda) x_j, \quad \tilde{y} = \lambda y_i + (1-\lambda) y_j, \quad \lambda \sim \text{Beta}(\alpha, \alpha)$$

typically $\alpha = 0.2$. Forces linear behavior between training examples — reduces sharp decision boundaries, improves calibration and adversarial robustness.

**CutMix** (Yun et al. 2019): instead of blending pixels, *cut* a rectangle from image A and *paste* it onto image B. Labels are mixed proportionally to area. Preserves local features better than MixUp.

**Mosaic** (YOLOv4): four images tiled into a grid. Used heavily in detection.

```python
import numpy as np, torch

def mixup(x, y, alpha=0.2):
    lam = np.random.beta(alpha, alpha)
    idx = torch.randperm(x.size(0))
    mixed_x = lam * x + (1 - lam) * x[idx]
    y_a, y_b = y, y[idx]
    return mixed_x, y_a, y_b, lam

# In training loop:
mixed_x, y_a, y_b, lam = mixup(x, y)
logits = model(mixed_x)
loss = lam * criterion(logits, y_a) + (1 - lam) * criterion(logits, y_b)
```

| Method | Pros | Cons |
|---|---|---|
| MixUp | Smooth decision boundaries, better calibration | Images look unnatural |
| CutMix | Preserves local structure | Can hurt when class is position-sensitive |
| Mosaic | 4-in-1, great for detection | Complex, detection-specific |

---

## Q101. Stochastic depth and DropPath — dropping whole layers { #q101 }

**Stochastic depth** (Huang et al. 2016): during training, randomly **drop entire residual blocks** with some probability $p_l$ that grows linearly with depth. Effectively, you're training an ensemble of networks with varying depth.

$$H_l = H_{l-1} + \mathbb{1}[b_l = 1] \cdot f_l(H_{l-1}), \quad b_l \sim \text{Bernoulli}(1-p_l)$$

**DropPath** is the same idea repackaged for transformers and ConvNeXt — drops the residual branch output (keeps identity path).

```python
class DropPath(nn.Module):
    def __init__(self, drop_prob=0.0):
        super().__init__()
        self.drop_prob = drop_prob
    def forward(self, x):
        if self.drop_prob == 0.0 or not self.training:
            return x
        keep = 1 - self.drop_prob
        mask = x.new_empty(x.size(0), *([1]*(x.ndim-1))).bernoulli_(keep)
        return x * mask / keep

# Usage in a transformer block
class Block(nn.Module):
    def __init__(self, dim, drop_path=0.1):
        ...
        self.drop_path = DropPath(drop_path)
    def forward(self, x):
        x = x + self.drop_path(self.attn(self.norm1(x)))
        x = x + self.drop_path(self.mlp(self.norm2(x)))
        return x
```

**Why it works:**
- Trains shallower networks implicitly (better gradient flow).
- Acts as ensemble.
- Makes very deep models (100+ layers) trainable.

Used in ResNet, ViT, ConvNeXt, Swin Transformer. Typical schedule: drop_path rate 0 at layer 0, growing linearly to 0.1–0.3 at the last layer.

---

## Q102. Batch Normalization — the deep dive on quirks and gotchas { #q102 }

**BN forward:**

$$\hat{x} = \frac{x - \mu_B}{\sqrt{\sigma_B^2 + \epsilon}}, \quad y = \gamma \hat{x} + \beta$$

where $\mu_B, \sigma_B$ are per-batch, per-channel statistics. Two learnable params per channel: $\gamma$ (scale), $\beta$ (shift).

**Training vs inference:**
- **Train:** normalize using current batch statistics, update running mean/var with EMA.
- **Eval:** normalize using running statistics. This mismatch is why `.eval()` is critical.

**Why it works (modern view):** not "internal covariate shift" as originally claimed — rather, it **smooths the loss landscape** (Santurkar et al. 2018) and decouples optimization from initialization.

**Known gotchas:**

1. **Small batch size breaks it.** BN variance is noisy with batch < 16. Use GroupNorm.
2. **BN + Dropout interaction.** Applying dropout before BN breaks BN's statistics. If you must combine, put dropout after BN.
3. **DDP and BN:** by default, each GPU computes its own BN stats (local batch of 32, not global 256). Use `nn.SyncBatchNorm.convert_sync_batchnorm(model)` to share stats across GPUs.
4. **Fine-tuning:** freezing BN (`bn.eval()` + stopping running stat updates) is often crucial when fine-tuning with a small dataset — otherwise BN stats drift on limited samples.
5. **BN destroys independence between samples** — bad for tasks where per-example statistics shouldn't leak across a batch.

```python
# Freeze BN during fine-tuning:
for m in model.modules():
    if isinstance(m, nn.BatchNorm2d):
        m.eval()
        for p in m.parameters():
            p.requires_grad = False
```

---

## Q103. Layer, Group, Instance norm — when to use which { #q103 }

All normalize $x \to (x - \mu)/\sigma$ over different axes:

| Norm | Axes normalized (for NCHW input) | Independent per | Best for |
|---|---|---|---|
| **BatchNorm** | (N, H, W), per channel C | Channel | Big batch CNNs |
| **LayerNorm** | (C, H, W), per sample N | Sample | Transformers, RNNs |
| **InstanceNorm** | (H, W), per (N, C) | Sample × Channel | Style transfer |
| **GroupNorm** | (C/G, H, W), per sample N and group | Group | Small-batch training, detection |

**LayerNorm** is the norm of choice for sequence models — it doesn't depend on batch size, doesn't mix samples, and it works the same at train and inference.

**GroupNorm** (Wu & He 2018): splits channels into G groups, normalizes within each. Independent of batch size. Good default when you can't use BN (e.g., detection with batch 2-4 per GPU). Typical G = 32.

**RMSNorm** (Zhang & Sennrich 2019): LayerNorm without mean centering — just scale by RMS. Faster, and surprisingly as good or better than LayerNorm for LLMs (Llama, PaLM, modern LLMs all use it).

$$\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{d}\sum_i x_i^2 + \epsilon}} \cdot \gamma$$

```python
class RMSNorm(nn.Module):
    def __init__(self, dim, eps=1e-6):
        super().__init__()
        self.scale = nn.Parameter(torch.ones(dim))
        self.eps = eps
    def forward(self, x):
        norm = x.pow(2).mean(-1, keepdim=True).add(self.eps).sqrt()
        return x / norm * self.scale
```

<div class="tip-box" markdown>
**Interviewer gotcha:** "Why doesn't BERT use BatchNorm?" Because sequences have variable length, and BN would mix statistics across different sentence lengths in weird ways. LayerNorm normalizes per-token, which is natural for sequences.
</div>

---

## Q104. Weight standardization and other parameter regularizations { #q104 }

**Weight standardization** (Qiao et al. 2019): normalize the *weights* themselves instead of activations:

$$\hat{W}_{i,:} = \frac{W_{i,:} - \mu_i}{\sigma_i + \epsilon}$$

Combined with GroupNorm, it matches BN performance on ImageNet even with tiny batches (1-2 per GPU). Useful for memory-constrained detection/segmentation.

**Spectral normalization** (Miyato et al. 2018): divide $W$ by its largest singular value, enforcing Lipschitz constraint $\|Wx - Wy\| \leq \|x - y\|$. Critical for GAN discriminators to prevent training instability.

**Orthogonal regularization:** add $\|W^T W - I\|^2$ to loss — encourages weight matrix columns to be orthogonal. Used in GANs (BigGAN) and some RNN variants.

**Max-norm constraint:** after each update, rescale any weight vector whose norm exceeds $c$. Simple, effective for MLPs but less commonly used now.

---

## Q105. Ensembling — the last mile of accuracy { #q105 }

**Principle:** combining multiple models reduces variance. For $M$ independent models with uncorrelated errors, ensemble variance is reduced by $1/M$.

**Strategies:**

1. **Simple averaging:** average predictions across models. Works surprisingly well.
2. **Snapshot ensembles** (Huang et al. 2017): save checkpoints at cosine LR minima, average predictions. One training run, $M$ models.
3. **Stochastic Weight Averaging (SWA)** (Izmailov et al. 2018): average *weights* (not predictions) from the tail of training. Finds flatter minima; generalizes better.
4. **Stacking:** train a meta-model on the base models' predictions.
5. **Test-Time Augmentation (TTA):** at inference, apply multiple augmentations and average predictions. Cheap, often +0.5-2%.

```python
# Stochastic Weight Averaging in PyTorch
from torch.optim.swa_utils import AveragedModel, SWALR, update_bn

swa_model = AveragedModel(model)
swa_scheduler = SWALR(optimizer, swa_lr=0.05)

for epoch in range(epochs):
    for x, y in loader:
        optimizer.zero_grad()
        loss = criterion(model(x), y)
        loss.backward(); optimizer.step()
    if epoch >= swa_start:
        swa_model.update_parameters(model)
        swa_scheduler.step()

update_bn(loader, swa_model)   # recompute BN statistics with swa weights
```

| Method | Cost | Typical gain |
|---|---|---|
| TTA (10 crops) | 10× inference | +0.5-2% |
| Snapshot ensemble (5 snaps) | 1× train, 5× inference | +1-3% |
| SWA | ~1× train, 1× inference | +0.5-1.5% |
| Full ensemble (5 models) | 5× train, 5× inference | +2-5% |

---

## Q106. Knowledge distillation — teacher–student training { #q106 }

**Goal:** compress a large "teacher" model into a smaller "student" model while preserving accuracy. Student learns from the teacher's soft predictions (which carry *more information* than hard labels — e.g., "75% cat, 15% dog, 10% fox" tells the student about class similarities).

**Hinton's KD loss:**

$$\mathcal{L}_{\text{KD}} = \alpha \, T^2 \, \text{KL}(p_T \| p_S) + (1-\alpha) \, \text{CE}(y, p_S)$$

where $p_T, p_S$ are *softened* teacher/student probabilities with temperature $T > 1$:

$$p_i = \frac{\exp(z_i / T)}{\sum_j \exp(z_j / T)}$$

Higher $T$ produces softer distributions (more information about dark classes). Typical $T \in [2, 5]$.

```python
def distill_loss(student_logits, teacher_logits, labels, T=4.0, alpha=0.7):
    soft_t = F.log_softmax(teacher_logits / T, dim=-1)
    soft_s = F.log_softmax(student_logits / T, dim=-1)
    kd = F.kl_div(soft_s, soft_t, reduction="batchmean", log_target=True) * (T * T)
    ce = F.cross_entropy(student_logits, labels)
    return alpha * kd + (1 - alpha) * ce
```

**Beyond logit matching:**
- **Feature distillation:** match intermediate layer activations (FitNets).
- **Attention distillation:** match attention maps (for transformers — TinyBERT, DistilBERT).
- **Relation distillation:** match similarity matrices between examples.

**LLM-era distillation:**
- **Task distillation:** teacher generates synthetic Q&A pairs, student fine-tuned on them.
- **Chain-of-thought distillation:** teacher generates reasoning traces, student learns to produce them.
- Alpaca, Orca, Phi series — all trained via distillation from GPT-4/GPT-3.5.

<div class="scenario" markdown>
**Scenario — need to deploy BERT-base to mobile:** Distill BERT-base into a 4-layer TinyBERT using teacher soft labels + intermediate layer matching + attention distillation. Typical result: 7.5× smaller, 9× faster, 96-99% of BERT-base performance on GLUE.
</div>

---

## Q107. Pruning — removing weights without losing accuracy { #q107 }

**Premise:** neural networks are massively over-parameterized. Many weights contribute little; remove them.

**Unstructured (magnitude) pruning:** zero out the smallest-magnitude weights. Produces a *sparse* tensor, which is fast on specialized hardware (Ampere 2:4 sparsity, or Cerebras) but not on standard GPUs.

**Structured pruning:** remove entire rows/columns/channels/heads. Produces a *smaller dense tensor* — actually faster on standard hardware.

**Iterative pruning:** prune → fine-tune → prune → fine-tune. Can remove 80–90% of weights with <1% accuracy loss.

**Lottery Ticket Hypothesis** (Frankle & Carbin 2018): inside a large random network, a sparse subnetwork ("winning ticket") exists that can match the full network's performance *when trained from the same initialization*. Has deep implications for how overparameterization works.

```python
import torch.nn.utils.prune as prune

# Magnitude prune 30% of weights in every linear layer
for name, module in model.named_modules():
    if isinstance(module, nn.Linear):
        prune.l1_unstructured(module, name="weight", amount=0.3)

# Make the pruning permanent (remove the mask machinery)
for name, module in model.named_modules():
    if isinstance(module, nn.Linear):
        prune.remove(module, "weight")
```

**LLM pruning (2023+):**
- **Wanda:** magnitude × input activation norm as pruning criterion.
- **SparseGPT:** one-shot pruning using calibration data + second-order info.
- **Structured pruning of attention heads:** many heads contribute negligibly (Michel et al.).

| Method | Sparsity achievable | Hardware speedup |
|---|---|---|
| Magnitude unstructured | 90%+ | Only on sparse HW |
| 2:4 structured (Ampere) | 50% | ~1.5-2× on A100 |
| Structured channel pruning | 30-50% | Full speedup |
| LLM distillation + prune | 50-70% | Full speedup |

---

## Q108. Quantization — INT8, INT4, and post-training vs QAT { #q108 }

**Goal:** reduce model memory and compute by using lower-precision weights/activations (INT8, INT4, even INT2).

**Key formulas (symmetric INT8 quantization):**

$$s = \frac{\max(|x|)}{127}, \quad x_q = \text{round}(x / s), \quad x_{\text{dequant}} = x_q \cdot s$$

**Post-Training Quantization (PTQ):** calibrate scales on a small dataset, no retraining. Fast (seconds to minutes). Loses 1-3% accuracy typically.

**Quantization-Aware Training (QAT):** insert "fake quantization" nodes during training — forward uses quantized values, gradients flow through Straight-Through Estimator. Recovers nearly all accuracy. Slower (requires training).

**Dynamic quantization:** quantize weights statically, activations quantized per-batch at inference. Simple; good for RNNs and transformers on CPU.

```python
# Post-training dynamic quantization in PyTorch
import torch.ao.quantization as quant
quantized = quant.quantize_dynamic(
    model, {nn.Linear, nn.LSTM}, dtype=torch.qint8,
)
# ~4× smaller, 2-4× faster on CPU inference.
```

**LLM quantization (the hot area):**

| Method | Bits | Key trick | Accuracy drop |
|---|---|---|---|
| GPTQ | 4 | Layerwise optimal rounding | <1% |
| AWQ | 4 | Activation-aware per-channel scaling | <1% |
| SmoothQuant | 8 | Balance act/weight outliers | ~0.5% |
| QLoRA | 4 (NF4) | 4-bit frozen + 16-bit LoRA | ~nothing, fine-tuneable |
| BitNet | 1.58 | Ternary weights {-1, 0, 1} | Competitive from scratch |

**Key insight:** activations in LLMs have **outliers** (a few large values per channel) that make naive quantization fail. SmoothQuant, AWQ, and GPTQ all address this.

---

## Q109. QLoRA — 4-bit fine-tuning that actually works { #q109 }

**Problem:** fine-tuning a 65B model requires ~1TB of GPU memory for full precision. Way beyond consumer setups.

**QLoRA** (Dettmers et al. 2023) = **Quantized** LoRA:

1. **NF4 quantization**: 4-bit NormalFloat, information-theoretically optimal for normally-distributed weights.
2. **Double quantization**: quantize the quantization constants themselves.
3. **Frozen 4-bit base model** + **trainable 16-bit LoRA adapters**.
4. **Paged optimizers**: page Adam states to CPU when GPU OOM imminent.

Result: 65B model fine-tunable on a **single 48 GB GPU**. Accuracy matches full-precision fine-tuning on downstream benchmarks.

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model

bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3-70b", quantization_config=bnb)

lora = LoraConfig(r=64, lora_alpha=16, target_modules=["q_proj","k_proj","v_proj","o_proj"],
                  lora_dropout=0.05, bias="none", task_type="CAUSAL_LM")
model = get_peft_model(model, lora)
model.print_trainable_parameters()   # ~0.1% of params trainable
```

<div class="scenario" markdown>
**Scenario — fine-tune a 70B model on a single 80GB H100:** QLoRA with NF4 + double quant brings the frozen base to ~18GB, LoRA adapters add ~0.5GB, optimizer states maybe 1GB. Use gradient checkpointing to handle activations. Train 1-3 epochs on your task data, merge adapters back at the end. This is how most "custom 70B models" in production are actually made.
</div>

---

## Q110. Early stopping — why it's equivalent to L2 (in linear models) { #q110 }

**Early stopping:** monitor validation loss; stop training when it stops improving for $k$ epochs (patience).

**Surprising result (linear models):** gradient descent with early stopping is approximately equivalent to L2-regularized regression. Intuitively:
- Early iterations move in directions with large gradient (high-eigenvalue directions of the Hessian — the "important" features).
- Later iterations fine-tune small directions (low-eigenvalue directions — noise-prone).
- Stopping early is like shrinking the small-eigenvalue directions, exactly what L2 does.

**Practical tips:**
- Use **validation loss**, not validation accuracy, to decide (loss is smoother).
- Patience 5-10 epochs for CNNs; 1-3 for LLMs.
- Save the best checkpoint; don't use the final one.
- Combine with LR decay on plateau.

```python
best_loss, best_state, patience_counter = float('inf'), None, 0
PATIENCE = 5
for epoch in range(EPOCHS):
    train_one_epoch()
    val_loss = evaluate()
    if val_loss < best_loss:
        best_loss = val_loss
        best_state = copy.deepcopy(model.state_dict())
        patience_counter = 0
    else:
        patience_counter += 1
        if patience_counter >= PATIENCE:
            print(f"Early stopping at epoch {epoch}"); break
model.load_state_dict(best_state)
```

---

## Q111. Noise injection — input, weight, and gradient noise { #q111 }

**Input noise:** add Gaussian noise to inputs. Classic trick, makes the model robust. In vision, typically $\sigma = 0.01$ to $0.1$ (post-normalization).

**Weight noise:** add noise to weights during forward pass. Bayesian neural network flavor — implicit ensemble. Dropout is a special case (multiplicative Bernoulli noise).

**Gradient noise (Neelakantan et al. 2015):** add decaying Gaussian noise to gradients:

$$g_t \leftarrow g_t + \mathcal{N}(0, \sigma_t^2), \quad \sigma_t = \frac{\eta}{(1+t)^{0.55}}$$

Helps training of very deep / noisy models.

**Input smoothing** (for adversarial robustness): train with inputs noised, wrap inference with an averaging step.

---

## Q112. Regularization through architecture — residuals, skip connections, normalization { #q112 }

Modern architectures build regularization into the *architecture*, not just the loss.

**Residual connections** (ResNet): $y = x + F(x)$. Acts as a regularizer because:
- Identity path provides "default behavior" — the network can ignore $F$ if it's not useful.
- Enables very deep networks without gradient vanishing.
- Effectively creates an ensemble of shorter paths (Veit et al. 2016).

**Dense connections** (DenseNet): each layer sees *all* prior layers. Even more implicit ensembling.

**Attention** acts as a content-based regularizer — dynamic weighting based on query-key similarity.

**Layer/Batch norm** implicitly constrain activation statistics, reducing covariate-shift-like effects.

**Why stacking these works:** each technique contributes a different inductive bias. The architecture itself is a "prior" that steers learning toward generalizable solutions.

---

## Q113. The double descent phenomenon { #q113 }

**Classical bias-variance curve:** error has a U-shape — too simple = underfit, too complex = overfit. Sweet spot in the middle.

**Double descent** (Belkin et al. 2019, Nakkiran et al. 2020): as you increase model capacity *past* the interpolation threshold (training error = 0), test error goes *down again*, often below the classical minimum.

```
Test error
  │
  │     ╱╲
  │    ╱  ╲____________
  │   ╱               ╲___
  │__╱                    ╲___
  │                            ╲___
  └─────────────────────────────────→ model size
        classical       modern (overparameterized)
        regime          regime
```

**Implications:**
- More parameters can be *strictly better*, contradicting classical wisdom.
- Explains why 100B+ LLMs work at all.
- Implicit regularization (SGD bias toward flat minima, L2 decay) matters more in the overparameterized regime.

**Practical takeaway:** when in doubt, scale up model and data together — it usually wins.

---

## Q114. Generalization bounds and why deep learning defies them (mostly) { #q114 }

**Classical VC-dimension bounds:** test error $\leq$ train error $+ \tilde{O}(\sqrt{\text{VC-dim}/n})$. Predicts massive overparameterization = terrible generalization.

**Why deep nets work anyway:** VC-dimension alone doesn't capture the *implicit bias* of SGD. Modern theory considers:

- **Flat minima hypothesis:** SGD prefers wide/flat minima, which generalize better than sharp ones (Hochreiter & Schmidhuber 1997; Keskar et al. 2016).
- **Neural Tangent Kernel (NTK) theory:** in the infinite-width limit, neural network training is equivalent to kernel regression. Explains why huge nets still generalize.
- **Implicit regularization of SGD:** mini-batch noise biases optimization toward low-norm solutions.
- **PAC-Bayes bounds** and compression-based bounds give tighter guarantees for neural nets than VC.

**Practical implications:** no one uses these bounds to set hyperparameters. But the *insights* (flat minima, noise helps, small-batch SGD > large-batch for generalization) are useful.

---

## Q115. Putting it all together — a senior-level regularization strategy { #q115 }

When building a production model, layer regularization thoughtfully:

**1. Architecture-level (always on):**
- Residual connections, normalization (LN for transformers, BN for CNNs with large batch).
- Appropriate depth/width for dataset size (don't use 100M params on 1000 samples).

**2. Optimization-level:**
- Weight decay (AdamW, 0.01–0.1 for transformers, 1e-4 for ResNets).
- Cosine LR schedule with warmup.
- Gradient clipping (1.0 for LLMs, 5.0 for RNNs).

**3. Input-level:**
- Heavy augmentation early in training.
- MixUp / CutMix for classification.
- Label smoothing (0.1).

**4. Training-level:**
- Dropout (0.1–0.3 for MLPs, 0.1 for transformers, 0.0 for well-regularized large datasets).
- Stochastic depth / DropPath (grows with layer index).
- Early stopping + best-checkpoint saving.

**5. Post-training:**
- Stochastic Weight Averaging.
- TTA at inference for a cheap accuracy bump.

**6. If deploying under constraints:**
- Distillation → pruning → quantization (in that order).
- Expect: 10× smaller, 5-10× faster, ≤1% accuracy drop.

<div class="tip-box" markdown>
**Golden rule for interviews:** when asked "how would you prevent overfitting on dataset X?", walk through this stack from cheapest to most expensive. Start with "more data / better augmentation," progress to "dropout + weight decay," and only mention advanced techniques if the simple ones aren't enough. Interviewers want to see you diagnose before medicating.
</div>

---

## ✅ Module Recap

- **Dropout, weight decay (AdamW), label smoothing** — the always-on trio for modern DL.
- **Normalization** (BN, LN, GN, RMSNorm) — picks depend on architecture and batch size.
- **Data augmentation + MixUp/CutMix** — the cheapest regularizers, enormous ROI.
- **Stochastic depth / DropPath** — lets you train 100+ layer networks.
- **Distillation → pruning → quantization** — the deployment pipeline for production models.
- **QLoRA** revolutionized large-model fine-tuning on commodity hardware.
- **Double descent and implicit regularization of SGD** explain why massive overparameterization works.
- **Stack regularization from cheap to expensive** — diagnose first, medicate second.

→ Next: [🎤 Mock Interviews](mock-interview.md)
