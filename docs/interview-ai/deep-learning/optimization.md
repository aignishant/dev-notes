# ⚙️ Optimization & Training

!!! abstract "Module Scope"
    How deep networks actually train. Questions **Q81–Q95**. SGD/momentum/Nesterov, Adam/AdamW derivations, LR schedules, mixed precision, gradient accumulation, distributed training (DDP/FSDP/ZeRO), gradient checkpointing, LR finders, second-order methods. These questions separate "I can call `optimizer.step()`" from "I can debug a failing training run at 3 AM."

---

## Q81. SGD with momentum and Nesterov — derivation and intuition { #q81 }

<span class="q-badge">Foundational</span>

**Vanilla SGD**:

$$\theta_{t+1} = \theta_t - \eta \nabla L(\theta_t)$$

Problems: noisy, oscillates in ravines (high-curvature + low-curvature directions), slow in flat regions.

**SGD with momentum** (Polyak, 1964):

$$\mathbf{v}_{t+1} = \mu \mathbf{v}_t + \nabla L(\theta_t)$$
$$\theta_{t+1} = \theta_t - \eta \mathbf{v}_{t+1}$$

$\mathbf{v}$ is an exponentially-decaying average of past gradients. $\mu \in [0, 1)$ typical = 0.9 or 0.99.

**Intuition**: ball rolling downhill with inertia. Accumulates velocity in consistent directions, smooths out noise.

**Effective learning rate**: in a direction with persistent gradient, the velocity grows to $\frac{1}{1 - \mu}$ times the single-gradient step → 10x effective LR for $\mu = 0.9$. This is why momentum tolerates lower "nominal" LRs.

**Nesterov Accelerated Gradient (NAG)**:

$$\mathbf{v}_{t+1} = \mu \mathbf{v}_t + \nabla L(\theta_t - \eta \mu \mathbf{v}_t)$$
$$\theta_{t+1} = \theta_t - \eta \mathbf{v}_{t+1}$$

**Key insight**: evaluate gradient at the *look-ahead* point $\theta_t - \eta \mu \mathbf{v}_t$ (where momentum is about to carry you), not the current point.

- Corrects momentum errors earlier.
- Provably better convergence rate on convex problems ($O(1/t^2)$ vs $O(1/t)$ for plain momentum).
- In practice: small improvement (~10%) over plain momentum on deep nets.

```python
# PyTorch
optimizer = torch.optim.SGD(
    model.parameters(),
    lr=0.1,
    momentum=0.9,
    nesterov=True,      # NAG
    weight_decay=5e-4,
)
```

**When to use SGD over Adam**:

- **Vision classification** (ImageNet): SGD+momentum often beats Adam on test accuracy.
- **Fine-tuning large models**: SGD is gentler, less likely to drift far from init.
- **Well-conditioned losses** where adaptive methods don't help.

**When Adam wins**:

- **Transformers / NLP**: huge gradient scale variation across layers; Adam's adaptive per-parameter LR handles it.
- **Sparse gradients** (recommenders): parameters update rarely; Adam accumulates signal better.
- **Hyperparameter sensitivity**: Adam's defaults usually work; SGD's defaults need tuning.

<div class="tip-box" markdown>
**Interviewer insight:** The SGD vs Adam debate has a domain split. Vision ResNet trained with SGD+momentum still beats the same trained with Adam. NLP transformers trained with Adam/AdamW dominate. Know which side your problem is on before defaulting.
</div>

---

## Q82. Adam — full derivation and what each term does { #q82 }

<span class="q-badge">Foundational • Must Know</span>

**Adam** (Kingma & Ba, 2014): adaptive per-parameter learning rates using first and second moment estimates of gradients.

**Updates**:

$$\mathbf{m}_t = \beta_1 \mathbf{m}_{t-1} + (1 - \beta_1) \mathbf{g}_t  \quad \text{first moment (mean)}$$
$$\mathbf{v}_t = \beta_2 \mathbf{v}_{t-1} + (1 - \beta_2) \mathbf{g}_t^2  \quad \text{second moment (uncentered variance)}$$

**Bias correction** (crucial in early steps):

$$\hat{\mathbf{m}}_t = \mathbf{m}_t / (1 - \beta_1^t)$$
$$\hat{\mathbf{v}}_t = \mathbf{v}_t / (1 - \beta_2^t)$$

Because $\mathbf{m}_0 = \mathbf{v}_0 = 0$, the early estimates are biased toward zero. $1 - \beta_1^t$ approaches 1 over time, removing the bias.

**Parameter update**:

$$\theta_t = \theta_{t-1} - \eta \cdot \frac{\hat{\mathbf{m}}_t}{\sqrt{\hat{\mathbf{v}}_t} + \epsilon}$$

**What each piece does**:

- $\mathbf{m}$: momentum (like SGD momentum).
- $\sqrt{\mathbf{v}}$: per-parameter scaling. Parameters with large gradient magnitudes get damped; small-gradient params get boosted. Equivalent to adaptive LR per coordinate.
- $\epsilon$ (e.g., $10^{-8}$): numerical stability (avoid div by zero).
- $\sqrt{\mathbf{v}}$ approximates the curvature: second moment of gradient ~ Fisher information ~ curvature for specific loss families.

**Default hyperparameters**: $\beta_1 = 0.9, \beta_2 = 0.999, \epsilon = 10^{-8}$, $\eta = 10^{-3}$.

**Effective step size**: near isotropic — each coordinate updates by roughly $\eta \cdot \text{sign}(\mathbf{g})$ when $\mathbf{m}$ and $\sqrt{\mathbf{v}}$ align. This is why Adam's LR range is narrow (1e-3 is a magic default across tasks).

**Memory cost**: 2x model params (for $\mathbf{m}$ and $\mathbf{v}$) + 1x (params themselves) = 3x. For a 7B model in FP32, that's 84GB optimizer state — hence quantized optimizers (8-bit Adam).

```python
# Under the hood (simplified)
for p in params:
    if p.grad is None: continue
    g = p.grad
    m[p] = beta1 * m[p] + (1 - beta1) * g
    v[p] = beta2 * v[p] + (1 - beta2) * g * g
    m_hat = m[p] / (1 - beta1 ** t)
    v_hat = v[p] / (1 - beta2 ** t)
    p.data -= lr * m_hat / (v_hat.sqrt() + eps)
```

<div class="tip-box" markdown>
**Interviewer gotcha:** "Why is Adam's default LR 1e-3 when SGD's is 0.1?" Because of $1/\sqrt{\mathbf{v}}$ rescaling — step size is roughly LR × sign(gradient), independent of gradient magnitude. An LR of 0.1 would make steps wildly too large. It's not that Adam has a "smaller LR"; the LR interacts with the normalization.
</div>

---

## Q83. AdamW — why decoupled weight decay matters { #q83 }

<span class="q-badge">Modern • Must Know</span>

**The problem with L2 regularization + Adam**:

L2 reg adds $\lambda \|\theta\|^2 / 2$ to the loss → gradient becomes $\mathbf{g} + \lambda \theta$. In Adam, this augmented gradient flows through both $\mathbf{m}$ and $\mathbf{v}$:

$$\theta_t = \theta_{t-1} - \eta \cdot \frac{\hat{\mathbf{m}}_t (\text{including } \lambda \theta \text{ term})}{\sqrt{\hat{\mathbf{v}}_t} + \epsilon}$$

**Effect**: weight decay is **rescaled by $1/\sqrt{\mathbf{v}}$** — parameters with large gradient history get *less* decay. That's the opposite of what we want (large-magnitude params should decay more, not less).

**AdamW** (Loshchilov & Hutter, 2017) — decouple weight decay from gradient-based update:

$$\mathbf{m}_t, \mathbf{v}_t \text{ computed from } \mathbf{g}_t \text{ only (no } \lambda \theta \text{)}$$
$$\theta_t = \theta_{t-1} - \eta \left(\frac{\hat{\mathbf{m}}_t}{\sqrt{\hat{\mathbf{v}}_t} + \epsilon} + \lambda \theta_{t-1}\right)$$

Weight decay applied directly as $\theta \leftarrow \theta (1 - \eta \lambda)$ — independent of gradient statistics.

**Result**:

- Proper regularization — weight decay does what you expect.
- Better generalization, especially for transformers.
- **Standard optimizer for LLM training since 2019**.

```python
# AdamW with typical LLM settings
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=1e-4,
    betas=(0.9, 0.95),
    eps=1e-8,
    weight_decay=0.1,     # much larger than Adam+L2 default
)
```

**Why weight decay values differ**:

- Adam with L2: $\lambda \approx 10^{-4}$ typical.
- AdamW: $\lambda \approx 0.1$ typical (1000x larger!).

Same *effective* regularization, just parameterized differently. Be careful when porting between frameworks.

**LLM-specific note**: apply weight decay only to **2D+ parameters** (weight matrices), not **biases, norms, embeddings**:

```python
decay_params = [p for n, p in model.named_parameters() 
                if p.dim() >= 2 and 'norm' not in n and 'embed' not in n]
no_decay_params = [p for n, p in model.named_parameters() 
                   if p not in decay_params]

optimizer = torch.optim.AdamW([
    {'params': decay_params, 'weight_decay': 0.1},
    {'params': no_decay_params, 'weight_decay': 0.0},
], lr=1e-4, betas=(0.9, 0.95))
```

<div class="tip-box" markdown>
**Interviewer insight:** "Adam has L2 regularization built in, right?" Wrong — that's the canonical mistake. Adam applied to a loss with L2 term is *not* equivalent to Adam + decoupled weight decay. AdamW exists specifically because the former is broken for deep net regularization. Know this distinction.
</div>

---

## Q84. Adaptive optimizers — RMSProp, AdaGrad, and modern variants { #q84 }

<span class="q-badge">Reference</span>

Timeline and contrast:

**AdaGrad** (Duchi et al., 2011) — accumulate squared gradients forever:

$$\mathbf{v}_t = \mathbf{v}_{t-1} + \mathbf{g}_t^2$$
$$\theta_t = \theta_{t-1} - \eta \mathbf{g}_t / (\sqrt{\mathbf{v}_t} + \epsilon)$$

- Effective LR **monotonically decreases**.
- Good for sparse problems (online learning, embeddings).
- Bad for deep nets: LR decays too aggressively, training stalls.

**RMSProp** (Hinton, 2012 lectures — never formally published!):

$$\mathbf{v}_t = \beta \mathbf{v}_{t-1} + (1 - \beta) \mathbf{g}_t^2$$

Exponential moving average instead of sum → doesn't decay forever.

$$\theta_t = \theta_{t-1} - \eta \mathbf{g}_t / (\sqrt{\mathbf{v}_t} + \epsilon)$$

- Solved AdaGrad's LR-decay-forever problem.
- Adam adds momentum on top of RMSProp's denominator.

**Adam** = RMSProp + momentum + bias correction (see Q82).

**AdamW** = Adam + decoupled weight decay (see Q83).

**Modern variants**:

**LAMB** (You et al., 2019): layer-wise adaptive LR. Normalizes per-layer to enable very large batch training (BERT training in 76 min, 1024 TPUs).

**Lion** (Chen et al., 2023, discovered by AutoML): simpler than Adam.

$$\mathbf{c}_t = \beta_1 \mathbf{m}_{t-1} + (1 - \beta_1) \mathbf{g}_t$$
$$\theta_t = \theta_{t-1} - \eta \cdot \text{sign}(\mathbf{c}_t)$$
$$\mathbf{m}_t = \beta_2 \mathbf{m}_{t-1} + (1 - \beta_2) \mathbf{g}_t$$

- Only tracks momentum (no $\mathbf{v}$) → **half the memory**.
- Uses `sign()` instead of division — simpler compute.
- Competitive with AdamW, sometimes better.
- Adopted by some large-scale training runs.

**Sophia** (Liu et al., 2023): uses approximate Hessian diagonal. Claims 2x speedup over AdamW for LLM pretraining. Not yet widely adopted.

**Shampoo** / **Distributed Shampoo**: second-order, uses Kronecker-factored preconditioner. Expensive per step but fewer steps. Used by some DeepMind / Anthropic training runs.

| Optimizer | Memory | Steps to converge | Use |
|---|---|---|---|
| SGD | 1x params | Many | Vision, fine-tuning |
| SGD+momentum | 2x | Fewer | Vision, final polish |
| Adam | 3x | Fewer | NLP, general |
| AdamW | 3x | Fewer | LLMs (default) |
| Lion | 2x | Comparable to AdamW | Memory-limited LLM |
| Sophia | 3x+ | Fewer (claimed) | Research |
| Shampoo | 4x+ | Much fewer | Exotic, large-scale |

<div class="tip-box" markdown>
**Interviewer tip:** "Which optimizer should I use?" Default AdamW for transformers, SGD+momentum for vision, Lion if memory-constrained. Exotic optimizers (Sophia, Shampoo) — only if you're pushing the frontier and have engineering resources to tune them.
</div>

---

## Q85. Learning rate schedules — from step decay to cosine { #q85 }

<span class="q-badge">Practical • Must Know</span>

**Why schedule at all**:

- Early training: large LR for fast exploration.
- Late training: small LR for fine convergence.
- Constant LR underperforms nearly every scheduled option.

**Schedules in order of appearance**:

**1. Step decay**:

$$\eta_t = \eta_0 \cdot \gamma^{\lfloor t / T \rfloor}$$

Multiply LR by $\gamma$ (e.g., 0.1) every $T$ epochs. Simple, works.

**2. Exponential decay**: $\eta_t = \eta_0 \cdot e^{-\lambda t}$. Smooth alternative.

**3. Cosine annealing** (Loshchilov & Hutter, 2016) — standard for modern training:

$$\eta_t = \eta_{\min} + \frac{1}{2}(\eta_{\max} - \eta_{\min})\left(1 + \cos\left(\frac{t}{T}\pi\right)\right)$$

Smooth decay from $\eta_{\max}$ to $\eta_{\min}$ over $T$ steps. Empirically better than step decay across many tasks.

**4. Cosine with warm restarts (SGDR)**:

Periodically reset LR to $\eta_{\max}$ and run cosine again. Periods often double each cycle ($T_0, 2T_0, 4T_0, \dots$). Helps escape local optima.

**5. Linear warmup + cosine decay** — the standard LLM/Transformer schedule:

- Ramp linearly from 0 to $\eta_{\max}$ over first $W$ steps (e.g., 2000 warmup steps).
- Then cosine decay to some minimum (often 10% of max).

**Why warmup for transformers**:

- Adam's $\mathbf{v}$ (second moment) is small at step 1 → effective LR is large → divergence.
- Warmup lets moment estimates stabilize.
- Without warmup, most transformers diverge in the first few hundred steps.

**6. One-Cycle** (Smith, 2018):

Two phases — warmup to peak, then annealing. Enables "super-convergence" (training an order of magnitude faster). Used for training small/medium vision models quickly.

**7. Noam** (original Transformer paper):

$$\eta_t = d^{-0.5} \cdot \min(t^{-0.5}, t \cdot W^{-1.5})$$

Warmup then polynomial decay. Mostly obsolete — cosine is cleaner.

```python
from torch.optim.lr_scheduler import CosineAnnealingLR, LambdaLR

# Linear warmup + cosine decay (manual)
def lr_lambda(step, warmup=2000, total=100000):
    if step < warmup:
        return step / warmup                         # linear warmup
    progress = (step - warmup) / (total - warmup)
    return 0.5 * (1 + math.cos(math.pi * progress))  # cosine decay

scheduler = LambdaLR(optimizer, lr_lambda)

for step in range(total):
    # ... training step
    optimizer.step()
    scheduler.step()
```

**Practical rules**:

- **Vision**: SGD+momentum + cosine decay (+warmup for large batches).
- **NLP / LLM**: AdamW + warmup + cosine (or constant after warmup for very long training).
- **Chinchilla-style training**: linear decay to 10% of peak over full training.

<div class="tip-box" markdown>
**Interviewer tip:** Mention that **long LR schedules matter more than optimizer choice**. A Transformer trained with plain SGD + a well-tuned schedule can match AdamW with a bad schedule. Hyperparameter ranking (roughly): LR schedule > LR magnitude > optimizer > batch size > weight decay > everything else.
</div>

---

## Q86. Mixed precision training — FP16, BF16, FP8 { #q86 }

<span class="q-badge">Systems • Must Know</span>

**Motivation**: FP32 is wasteful. Lower precision → 2x memory, 2-3x speedup on modern GPUs.

**FP16 (half precision, IEEE)**:

- Range: $\pm 65{,}504$, resolution ~$10^{-3}$.
- **Narrow exponent range** — activations and gradients can underflow to 0 or overflow to Inf.
- Requires **loss scaling** to avoid underflow during backward pass.

**BF16 (brain float 16)**:

- Same exponent bits as FP32 (wide dynamic range), fewer mantissa bits.
- Range: ~$\pm 3 \times 10^{38}$ (same as FP32), lower precision.
- **No loss scaling needed** — huge engineering simplification.
- Standard for LLM training in 2024-2026.

**FP8** (H100+):

- Two formats: E5M2 (wider range, for gradients/activations) and E4M3 (more precision, for weights/activations).
- Requires per-tensor scaling — more engineering effort than BF16.
- 2x memory/speedup over BF16.

```python
# Automatic Mixed Precision (AMP) with BF16
from torch.amp import autocast, GradScaler

# BF16 (no scaler needed — wide dynamic range)
for x, y in loader:
    optimizer.zero_grad()
    with autocast(device_type='cuda', dtype=torch.bfloat16):
        logits = model(x)
        loss = F.cross_entropy(logits, y)
    loss.backward()
    optimizer.step()

# FP16 (scaler required for underflow prevention)
scaler = GradScaler()
for x, y in loader:
    optimizer.zero_grad()
    with autocast(device_type='cuda', dtype=torch.float16):
        logits = model(x)
        loss = F.cross_entropy(logits, y)
    scaler.scale(loss).backward()
    scaler.unscale_(optimizer)
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    scaler.step(optimizer)
    scaler.update()
```

**Loss scaling (FP16)** — multiply loss by $S$ before backward so small gradients stay in representable range. Divide by $S$ before optimizer update.

**Master weights (FP32)**:

- Model weights stored in FP32 ("master copy").
- Forward/backward in FP16/BF16.
- Updates computed in FP32 (Adam moments are sensitive).
- Updated weights cast back to FP16/BF16 for next forward.

**Common failure modes**:

- **NaN loss** early in training: gradient overflow. Check loss scaling, LR warmup, gradient clipping.
- **Training "freezes"** (loss constant): gradient underflow in FP16. Increase loss scale.
- **BN + FP16**: batch statistics can overflow. Keep BN in FP32.

**Precision per component** in practice:

| Component | Precision |
|---|---|
| Weights (stored) | BF16 or FP8 |
| Activations | BF16 |
| Attention softmax | FP32 (sensitive) |
| LayerNorm | FP32 |
| Master weights for optimizer | FP32 (Adam moments) |
| Gradients | BF16 |
| KV cache (inference) | BF16 → INT8 → INT4 |

<div class="tip-box" markdown>
**Interviewer insight:** "Why BF16 for LLM training and not FP16?" Wide dynamic range — no loss scaling, fewer NaN issues, simpler engineering. LLM gradients have big magnitude variation across layers; FP16's narrow range is a liability. This is why the LLM community converged on BF16.
</div>

---

## Q87. Gradient accumulation — effective large batch on small GPU { #q87 }

<span class="q-badge">Practical</span>

**Problem**: you want batch size 256 but only fit 32 on your GPU.

**Gradient accumulation**: run several forward/backward passes without calling `optimizer.step()`, accumulate gradients in `.grad`, step after $N$ micro-batches.

```python
accum_steps = 8    # effective batch = micro_batch * 8

optimizer.zero_grad()
for i, (x, y) in enumerate(loader):
    loss = F.cross_entropy(model(x), y)
    loss = loss / accum_steps    # scale to preserve average
    loss.backward()              # accumulates in .grad
    
    if (i + 1) % accum_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

**What's preserved**: average gradient direction → equivalent to one large batch (modulo BN behavior).

**What's NOT preserved**:

- **BN statistics**: still computed per micro-batch. For BN-heavy models, this is a real difference. Fix: use `SyncBatchNorm` or replace with LayerNorm / GroupNorm.
- **Wall-clock speed**: accumulation adds overhead per step; real large-batch training (more GPUs) is faster.

**Learning rate scaling**: with larger effective batch, follow **linear scaling rule** (Q86 from foundations): scale LR by $k$ if accumulating $k$ micro-batches. With warmup to stabilize.

**Common mistake**: forgetting to scale loss by `1 / accum_steps`:

- Without scaling: gradients sum → effective LR is $k \times$ nominal LR → possibly divergent.
- With scaling: gradients average → same update as single large batch.

**Combining with DDP**:

- With `torch.nn.parallel.DistributedDataParallel`, gradient sync happens at every `backward()` by default — waste.
- Use `model.no_sync()` during non-update steps to avoid inter-GPU communication:

```python
for i, (x, y) in enumerate(loader):
    if (i + 1) % accum_steps != 0:
        with model.no_sync():
            loss.backward()
    else:
        loss.backward()           # sync + optimizer step
        optimizer.step()
        optimizer.zero_grad()
```

<div class="scenario" markdown>
**Scenario:** LLM fine-tuning: target batch size 128 sequences of 2048 tokens, single A100 40GB.<br>
**Answer:** Micro-batch 4 on GPU, gradient accumulation 32 → effective batch 128. Use BF16 + gradient checkpointing to fit larger micro-batch if possible. LR should match what you'd use for batch 128 in one shot (with warmup). Check `model.no_sync()` if multi-GPU.
</div>

---

## Q88. Distributed training — DDP, FSDP, ZeRO stages { #q88 }

<span class="q-badge">Systems • Must Know</span>

**Data parallelism** (simplest):

Each GPU has a full copy of the model; different data shards; gradients averaged (all-reduce) after each step.

- PyTorch `DistributedDataParallel (DDP)`.
- Scales well for models that fit on one GPU.
- Memory per GPU: full model + full optimizer state.

**When DDP isn't enough**: model doesn't fit on one GPU.

**ZeRO (Zero Redundancy Optimizer)** (Rajbhandari et al., 2019, DeepSpeed):

Split optimizer state, gradients, and parameters across GPUs. Three stages of increasing memory savings:

- **ZeRO-1**: shard **optimizer state** (Adam's $m, v$) across GPUs. 4x memory savings (for AdamW). Communication: still all-reduce per step.
- **ZeRO-2**: shard **optimizer state + gradients**. 8x savings.
- **ZeRO-3**: shard **optimizer state + gradients + parameters**. Each GPU holds only its shard; gather on-the-fly when needed for forward/backward. Up to N× savings for N GPUs.

**Tradeoff**: ZeRO-3 has more communication (gather params for each layer). Compute/communication balance depends on hardware interconnect (NVLink >> PCIe).

**FSDP (Fully Sharded Data Parallel)** — PyTorch's native implementation of ZeRO-3:

```python
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP, MixedPrecision
from torch.distributed.fsdp.wrap import transformer_auto_wrap_policy

model = FSDP(
    model,
    auto_wrap_policy=functools.partial(
        transformer_auto_wrap_policy,
        transformer_layer_cls={LlamaDecoderLayer},
    ),
    mixed_precision=MixedPrecision(
        param_dtype=torch.bfloat16,
        reduce_dtype=torch.bfloat16,
    ),
    device_id=torch.cuda.current_device(),
)
```

**Tensor parallelism** (Megatron-LM) — split individual weight matrices across GPUs:

- For attention: split heads across GPUs (column-parallel for QKV, row-parallel for output projection).
- For FFN: column-parallel for up projection, row-parallel for down projection.
- Two all-reduces per transformer block → high communication.
- Only efficient within a node (NVLink-connected GPUs).

**Pipeline parallelism** — different GPUs handle different layers:

- Forward/backward pipelined across stages.
- Requires batching carefully to avoid pipeline bubbles.
- GPipe, 1F1B (one-forward-one-backward) scheduling.

**3D parallelism** (Megatron + DeepSpeed combination) — combine data + tensor + pipeline:

- Tensor parallel within node (NVLink).
- Pipeline parallel across nodes (Infiniband).
- Data parallel on top.
- Used for 100B+ parameter training.

**Sequence parallelism** — split sequence dimension for long-context training.

| Scale | Strategy |
|---|---|
| Fits on 1 GPU | DDP (data parallel only) |
| Fits on 1 node (8 GPUs) | FSDP / ZeRO-3 |
| 100B params, multi-node | Tensor parallel + pipeline parallel + FSDP |
| 1T+ params | Full 3D + MoE expert parallel |

```python
# Quick reference: choosing strategy
if model_params < gpu_memory * 0.5:   # leaves room for optimizer, activations
    # DDP
elif model_params < node_memory * 0.5:
    # FSDP
else:
    # 3D parallelism — reach for Megatron-LM or DeepSpeed
```

<div class="tip-box" markdown>
**Interviewer signal:** Staff+ candidates can discuss **compute/communication tradeoffs** of each strategy. "ZeRO-3 saves memory but sends parameters over NVLink every step" is a senior-level insight. If asked about training 70B+ models, mention **FSDP** (or DeepSpeed ZeRO-3) as the default stack in 2026.
</div>

---

## Q89. Gradient checkpointing — trading compute for memory { #q89 }

<span class="q-badge">Practical</span>

**Problem**: activations dominate GPU memory during training. For a $L$-layer Transformer with $d_{\text{model}}$, the forward pass stores $O(L \cdot B \cdot T \cdot d)$ activations for backward — can be gigabytes.

**Gradient checkpointing** (Chen et al., 2016):

1. During forward pass, **only save checkpoints** every few layers (drop activations in between).
2. During backward, **recompute** the dropped activations on-the-fly as needed.

**Result**: ~$\sqrt{L}$ memory reduction at cost of ~33% more compute (one extra forward through checkpoint segments).

**PyTorch usage**:

```python
from torch.utils.checkpoint import checkpoint

class Block(nn.Module):
    def forward(self, x):
        return self.attn(x) + self.ffn(x)

# Wrap forward with checkpointing
class CheckpointedBlock(Block):
    def forward(self, x):
        return checkpoint(super().forward, x, use_reentrant=False)
```

Or automatically for HuggingFace models:

```python
model.gradient_checkpointing_enable()
```

**When to use**:

- Fine-tuning large models on limited GPU memory (standard for QLoRA, etc.).
- Training with long sequences.
- Any time batch size is limited by activation memory.

**When NOT to use**:

- Small models where activations aren't the bottleneck.
- Inference (no backward, no memory saving).

**Selective checkpointing** — modern practice:

- Checkpoint only **expensive-to-recompute** layers (like attention). Keep activations for cheap layers (like linear + ReLU).
- **Activation checkpointing in FSDP**: checkpoint at the FSDP wrap unit (per transformer block) — standard.

**Related: offloading**:

- **CPU offload** (ZeRO-Offload, DeepSpeed): move optimizer state to CPU RAM. Enables even larger models on fewer GPUs.
- **NVMe offload**: extreme case, for 100B+ on few GPUs.
- Slow due to PCIe; tradeoff is memory for throughput.

<div class="scenario" markdown>
**Scenario:** Training 7B LLM on A100 80GB, OOM with batch size 1.<br>
**Answer:** Stack of tricks: (1) **BF16** (already standard). (2) **Gradient checkpointing** — big win. (3) **QLoRA** — quantize base model to 4-bit, train adapters. (4) **Gradient accumulation** to maintain effective batch. (5) If still OOM: **FSDP** across multiple GPUs. Most solo 7B fine-tuning uses QLoRA + grad checkpointing + grad accumulation.
</div>

---

## Q90. Learning rate finder — the practical "optimal LR" tool { #q90 }

<span class="q-badge">Practical</span>

**LR range test** (Smith, 2015, popularized by fast.ai): empirically find optimal LR in minutes, not hours of hyperparameter search.

**Procedure**:

1. Start LR at very small value (e.g., $10^{-8}$).
2. After each batch, exponentially increase LR until very large (e.g., $10$).
3. Track loss at each LR.
4. Plot loss vs log(LR).
5. Find:
   - **Loss diverges** at some LR → upper bound.
   - **Steepest downward slope** just before divergence → optimal LR.
   - Safe pick: **one order of magnitude below divergence point**.

**Typical plot**:

```
loss │       ╲
     │        ╲___
     │            ╲___      <- steepest slope here
     │                ╲_
     │                  ╲__
     │                    ╲
     │                     ╲_____  ╱     <- loss diverges
     │                            ╱
     │                           ╱
     └────────────────────────── LR (log scale)
       1e-7   1e-5   1e-3  1e-1
```

Pick LR around $10^{-3}$ in this example (steepest slope just before divergence).

**Using fast.ai or PyTorch Lightning**:

```python
# Lightning LR finder
from pytorch_lightning.tuner import Tuner
tuner = Tuner(trainer)
lr_finder = tuner.lr_find(model)
print(lr_finder.suggestion())
```

**Caveats**:

- Optimizer-dependent: run LR finder with the same optimizer you'll train with.
- Schedule matters: this finds a good **peak** LR; combine with cosine schedule for best results.
- Task matters: re-run LR finder when dataset or model changes substantially.

**One-cycle policy** (Smith, 2018) builds on LR finder:

- Warmup from $\eta_{\max}/25$ to $\eta_{\max}$ over 45% of training.
- Cool down from $\eta_{\max}$ back to $\eta_{\max}/25$ over 45%.
- Final 10%: further decay to $\eta_{\max}/10000$.
- Momentum cycles inversely.
- Enables "super-convergence" — same accuracy in ~5x fewer epochs for some tasks.

```python
from torch.optim.lr_scheduler import OneCycleLR

scheduler = OneCycleLR(
    optimizer,
    max_lr=1e-3,
    total_steps=total_steps,
    pct_start=0.1,          # warmup 10%
    anneal_strategy='cos',
)
```

<div class="tip-box" markdown>
**Interviewer tip:** Being able to reliably find a good LR is one of the practical skills that separates engineers who train a model in a week from those who train it in months. The LR finder is a one-evening investment that pays dividends for your entire DL career.
</div>

---

## Q91. Second-order methods — why they're rare despite theoretical appeal { #q91 }

<span class="q-badge">Advanced</span>

**Theory**: Newton's method converges quadratically (much faster than first-order's linear convergence near optimum):

$$\theta_{t+1} = \theta_t - H^{-1} \mathbf{g}$$

$H$ is the Hessian ($d^2$ entries). For a 1B-param model: $10^{18}$ entries — impossible.

**Why SGD beats Newton for deep learning**:

1. **Memory prohibitive**: full Hessian is $O(d^2)$ — infeasible.
2. **Computing Hessian**: $O(d)$ backward passes with Pearlmutter's trick. Slow per step.
3. **Non-convex losses**: Newton can move toward saddles / maxima.
4. **Noisy gradients**: stochastic Hessian estimate is even worse.

**Practical approximations**:

**1. Quasi-Newton (L-BFGS)**:

- Approximate Hessian inverse from past gradients.
- Memory-limited version keeps last $k$ gradient pairs.
- Works for convex / small-scale problems; rarely used for deep nets.

**2. K-FAC (Kronecker-Factored Approximate Curvature)** (Martens & Grosse, 2015):

- Approximate the Fisher Information Matrix per layer as a Kronecker product.
- Tractable: invert two smaller matrices per layer.
- Some use in RL (TRPO uses natural policy gradient).

**3. Shampoo** (Gupta et al., 2018):

- Similar to K-FAC, uses Kronecker-factored preconditioner.
- **Distributed Shampoo** (2023): practical at scale, used in some Google/Anthropic training runs.

**4. Sophia** (Liu et al., 2023):

- Approximate **diagonal Hessian** via Hutchinson's trace estimator.
- Cheap per step (only diagonal), claims 2x speedup over AdamW for LLMs.
- Early adoption, not yet mainstream.

**Why people are revisiting second-order methods for LLMs**:

- LLM pretraining is expensive — even 20% speedup = millions saved.
- At 100B+ scale, more sample-efficient optimizers become economically valuable.
- Compute-bound (not data-bound) regime favors fewer-but-more-informative updates.

**Current state (2026)**:

- **AdamW** remains the default.
- **Lion** is widely adopted for memory savings.
- **Sophia / Shampoo** are under active research; niche adoption.
- Likely future: adaptive selection of second-order info for specific layers.

<div class="tip-box" markdown>
**Interviewer insight:** "Why don't we use Newton's method?" Not because it's bad — because it's **infeasibly expensive** in parameters and matmul size for deep nets. First-order methods with clever tricks (momentum, adaptive scaling, mixed precision) have been "good enough" that beating them is hard. But with LLM training costs exploding, second-order methods are reemerging — worth knowing about.
</div>

---

## Q92. Loss landscape — sharp vs flat minima, large batch generalization { #q92 }

<span class="q-badge">Conceptual</span>

**Setup**: deep net loss surface is non-convex. Training finds *a* minimum, but which one?

**Sharp minima** (Hochreiter & Schmidhuber 1997; Keskar et al., 2016):

- Loss is low but rises quickly around the point.
- Small perturbation to weights → large loss increase.
- Generalize *worse* — they've fit training noise.

**Flat minima**:

- Loss is low *and* stable to perturbations.
- Correspond to simpler models (Bayesian argument: flat regions have more probability mass in weight space).
- Generalize *better*.

**Visual intuition** (loss along a random direction):

```
Sharp:    ▁▁▁▁╲▁▁╱▁▁▁▁           loss low only at exact point
Flat:     ▁▁▁▁▁▁▁▁▁▁▁▁           broad region of low loss
```

**Large-batch generalization gap** (Keskar et al., 2016):

- SGD with small batches: noise → bounces around → lands in flat minima.
- SGD with large batches: less noise → converges to sharp minima → worse generalization.

**Mitigations**:

1. **Warmup + LR scaling** (linear scaling rule): compensates for larger batches.
2. **Ghost BN**: normalize per-sub-batch within a large batch to restore effective noise.
3. **SAM (Sharpness-Aware Minimization)** (Foret et al., 2020): explicit flat-minima-seeking optimizer:
   $$\min_\theta \max_{\|\epsilon\| \leq \rho} L(\theta + \epsilon)$$
   Approximate the inner max by a single gradient step.
4. **Extra epochs / more careful schedules** for large batches.

**SAM example**:

```python
# SAM has two forward-backward passes per step
optimizer.zero_grad()
loss = criterion(model(x), y)
loss.backward()
# First step: perturb toward sharp direction
with torch.no_grad():
    grad_norm = sum(p.grad.norm()**2 for p in model.parameters())**0.5
    for p in model.parameters():
        p.data += rho * p.grad / grad_norm
# Second forward/backward with perturbed weights
optimizer.zero_grad()
loss = criterion(model(x), y)
loss.backward()
# Restore original weights
with torch.no_grad():
    for p in model.parameters():
        p.data -= rho * (prev_grads[p] / grad_norm)
optimizer.step()
```

**Recent debate**: is "flatness → generalization" causal, or correlated? Reparametrizations of the network can change sharpness without changing the function (Dinh et al., 2017). So "flatness" must be measured carefully.

**Practical upshot for interviews**:

- Large batch → you may need more compute to maintain generalization.
- Noise in training (small batch, dropout, weight decay) has a regularizing effect beyond its explicit role.
- "Super-converged" models trained with aggressive 1-cycle schedules are often surprisingly well-generalizing — likely due to high-LR phases acting as implicit flat-finding.

<div class="tip-box" markdown>
**Interviewer insight:** Sharpness-generalization connection is still an active research area. For production, the practical rule is: **use a batch size that fits your compute**, with LR scaling and warmup to maintain quality. SAM and explicit flat-seeking optimizers are nice but add complexity and compute — usually not worth it vs. more-compute-for-longer training.
</div>

---

## Q93. Hyperparameter tuning — practical stack for deep learning { #q93 }

<span class="q-badge">Practical</span>

**Hyperparameters that actually matter**, in rough impact order:

1. **Learning rate** (single biggest lever).
2. **LR schedule** (cosine vs constant vs step).
3. **Batch size** (interacts with LR via linear scaling).
4. **Optimizer** (AdamW vs SGD vs ...).
5. **Weight decay**.
6. **Dropout / regularization strength**.
7. **Warmup length**.
8. **Model architecture** (layers, width, heads).

**Tuning strategies** (in order of sophistication):

**1. Manual tuning**: often fine for LR and a few others. Intuition > random search when you understand the problem.

**2. Grid search**: exhaustive over a small set. Works for 1-2 hyperparameters.

**3. Random search** (Bergstra & Bengio, 2012):

- Random samples in hyperparameter space.
- **Beats grid search** when some hyperparameters don't matter (grid wastes time on them).
- Standard baseline.

**4. Bayesian optimization**:

- Fit a Gaussian process (or tree ensemble) over (hyperparams, validation metric).
- Choose next trial to maximize expected improvement.
- Tools: Optuna, Ray Tune, scikit-optimize.
- Better than random for expensive experiments (~10+ trials).

**5. HyperBand / ASHA**:

- Start many short trials, prune losers early.
- Great when many trials fail fast (e.g., bad LR diverges in 100 steps).
- Common in AutoML pipelines.

**6. Population-based training (PBT)** (Jaderberg et al., 2017):

- Train population of models in parallel.
- Periodically copy weights and perturb hyperparameters from top performers to bottom.
- Used by DeepMind for RL. Niche but powerful.

**Practical recipe** for a deep learning project:

1. **Phase 1 — rough calibration** (1 day):
   - Run LR finder once → set peak LR.
   - Fix a reasonable schedule (cosine).
   - Run a few short trials (~10% of full compute) to set batch size, weight decay.

2. **Phase 2 — targeted search** (1-3 days):
   - Optuna over critical params (LR, WD, dropout).
   - 20-50 trials with ASHA for early stopping.

3. **Phase 3 — full training** (rest of compute):
   - Best config from phase 2 → full training run.
   - Keep a held-out test set for final reporting.

```python
# Optuna + PyTorch example
import optuna

def objective(trial):
    lr = trial.suggest_float('lr', 1e-5, 1e-2, log=True)
    wd = trial.suggest_float('wd', 1e-4, 1e-1, log=True)
    dropout = trial.suggest_float('dropout', 0.0, 0.5)
    
    model = build_model(dropout=dropout)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)
    # ... train, return val_loss
    return val_loss

study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=30)
```

**Common mistakes**:

- **Tuning on test set**: leak, leak, leak.
- **Too many hyperparameters at once**: adding 10 dimensions to your search space won't help if 8 don't matter.
- **Not logging properly**: need WandB / MLflow / TensorBoard to compare trials.
- **Chasing last-decimal wins**: 0.1% validation improvement often isn't reproducible.

<div class="tip-box" markdown>
**Interviewer tip:** "How do you choose hyperparameters?" Strong answer: "Start with established defaults for my architecture, run an LR finder, then Optuna over 3-5 critical hyperparameters with ASHA early stopping, final config with a single long run." Weak answer: "grid search everything." The strong answer shows practical experience.
</div>

---

## Q94. Debugging a failing training run { #q94 }

<span class="q-badge">Practical • Must Know</span>

A training run is failing — what do you check? The question is about diagnostic process, not any one answer.

**Failure mode 1: Loss is NaN.**

Checklist:

1. **Overflow in FP16?** Check loss scaling; try BF16.
2. **Exploding gradients?** Print gradient norm. Add gradient clipping.
3. **Bad init?** Kaiming for ReLU, Xavier for tanh. Don't init everything to zero.
4. **Division by zero?** Check custom loss functions, epsilons.
5. **Bad data?** Any `inf` or `NaN` in inputs? Check preprocessing.
6. **LR too high?** Reduce by 10x. If LR-sensitive, add warmup.

**Failure mode 2: Loss is constant (not decreasing).**

1. **LR too small?** Increase by 10x. Run LR finder.
2. **Gradient underflow in FP16?** Switch to BF16.
3. **Dead ReLU?** Check fraction of zero activations per layer.
4. **Wrong loss function?** Check if loss can decrease on this data.
5. **Optimizer not stepping?** Did you call `optimizer.step()`? Did you zero gradients?
6. **Data loader broken?** Are batches actually different? Print a few batches.
7. **Labels wrong format?** CE expects class indices, not one-hot. BCE expects probabilities.

**Failure mode 3: Train loss decreases, val loss doesn't (overfitting).**

1. **Add regularization**: dropout, weight decay.
2. **More data / augmentation**.
3. **Smaller model**.
4. **Early stopping**.
5. **Check train/val split** — is there leakage?

**Failure mode 4: Train loss doesn't match reported number (reproducibility).**

1. **Seed not set**? `torch.manual_seed`, `np.random.seed`, `random.seed`.
2. **CUDA non-determinism**: `torch.backends.cudnn.deterministic = True`.
3. **Data loader order**: `generator` in `DataLoader`.
4. **Model initialization**: different runs will differ without seed.
5. **Hardware diff**: different GPUs can give different results (kernel selection, floating point).

**Failure mode 5: Loss decreases slowly, metrics plateau.**

1. **LR schedule?** Constant LR → often slow. Try cosine.
2. **Gradient accumulation** to enable bigger effective batch.
3. **Batch norm with small batch?** Switch to LayerNorm or GroupNorm.
4. **Model too small** for the data? Scale up.

**Systematic debugging process**:

1. **Overfit a single batch**. If your model can't drive loss to ~0 on one batch, there's a bug in the model/loss/optimizer, not data/regularization.
2. **Visualize activations / gradients**. Track `grad.norm()` per layer. Dead layers show up immediately.
3. **Binary search the data**. Train on first 1k samples → 10k → 100k. If fails only at scale, it's data/batching.
4. **Compare to reference implementation**. For published architectures, matching hyperparameters and data preprocessing matters.

```python
# Sanity check: can we overfit one batch?
x, y = next(iter(loader))
for step in range(1000):
    optimizer.zero_grad()
    loss = criterion(model(x), y)
    loss.backward()
    optimizer.step()
    if step % 100 == 0:
        print(f"Step {step}: {loss.item()}")
# Loss should approach ~0. If not, something is fundamentally broken.
```

<div class="tip-box" markdown>
**Interviewer insight:** "What would you check first if a training run diverged?" Strong answer: "First, verify we can overfit a single batch — rules out model / loss / optimizer bugs. Then add logging for gradient norm, LR, loss — usually one of these will expose the issue. Most failures are LR too high, bad init, or broken data pipeline." That systematic answer is senior-level.
</div>

---

## Q95. Optimizer state memory and the 8-bit Adam trick { #q95 }

<span class="q-badge">Systems</span>

**Memory breakdown for AdamW training** of a $P$-parameter model in FP32:

| Component | Memory |
|---|---|
| Model params | $4P$ bytes |
| Gradients | $4P$ |
| Adam $m$ (momentum) | $4P$ |
| Adam $v$ (variance) | $4P$ |
| **Total** | **$16P$ bytes** |

For a 7B model: 112GB. That's why single-GPU training of 7B+ models requires tricks.

**With BF16 weights + FP32 master (mixed precision)**:

| Component | Memory |
|---|---|
| BF16 weights (for compute) | $2P$ |
| FP32 master weights | $4P$ |
| BF16 gradients | $2P$ |
| FP32 $m$ | $4P$ |
| FP32 $v$ | $4P$ |
| **Total** | **$16P$** |

Same memory — BF16 doesn't help the optimizer state.

**8-bit optimizers** (Dettmers et al., 2022, `bitsandbytes`):

Quantize $m$ and $v$ to INT8 with block-wise scaling:

$$m \in \mathbb{R}^P \to m' \in \mathbb{Z}_8^P \text{ (with per-block scale)}$$

- **4x smaller optimizer state** → 4GB instead of 16GB for a 1B model.
- Near-identical convergence to full-precision Adam.
- Enabled QLoRA and other consumer-GPU LLM fine-tuning.

```python
import bitsandbytes as bnb

# 8-bit AdamW — drop-in replacement
optimizer = bnb.optim.AdamW8bit(
    model.parameters(),
    lr=1e-4,
    betas=(0.9, 0.95),
    weight_decay=0.1,
)
```

**PagedAdamW** (`bnb.optim.PagedAdamW8bit`):

- Offload optimizer state to CPU when not in use.
- "Pages" state to GPU on demand.
- Enables training that otherwise OOMs on momentary memory spikes.

**Lion optimizer** (Q84):

- Only $m$, no $v$ → 2x memory savings over AdamW.
- Comparable or better results in many settings.
- Adopted for memory-constrained LLM training.

**Gradient-less / sharded optimization**:

- **FSDP** (Q88): shard optimizer state across GPUs. Each GPU holds $1/N$ of the optimizer state.
- Combined with 8-bit: 32x effective memory reduction vs FP32 Adam on single GPU.

**CPU offload** (ZeRO-Offload):

- Store optimizer state in CPU RAM, transfer on demand.
- Slow due to PCIe bandwidth; use only when GPU memory is the hard constraint.

**Practical stack for limited memory**:

- **7B model on 24GB GPU**: QLoRA + AdamW8bit + gradient checkpointing + BF16 compute.
- **70B model on 4×A100**: FSDP (ZeRO-3) + BF16 + AdamW8bit.
- **Extreme constraints**: ZeRO-Offload + CPU Adam.

<div class="tip-box" markdown>
**Interviewer insight:** Optimizer memory is often the forgotten component. A junior engineer runs `model.to(cuda)`, sees OOM, gives up. A senior engineer lists every component contributing to memory (weights, gradients, optimizer states, activations) and systematically optimizes each one — quantizing weights (INT4), gradients (low-bit), optimizer states (8-bit), activations (checkpointing). This layered approach is the staff-engineer mindset.
</div>

---

## ✅ Module Recap

- **SGD+momentum** is king for vision; **AdamW** dominates for LLMs and NLP.
- **AdamW ≠ Adam + L2** — decoupled weight decay matters fundamentally.
- **LR schedule** (cosine with warmup) matters more than optimizer choice. Warmup is mandatory for transformers.
- **Mixed precision** (BF16 standard, FP8 emerging) is essential for modern training.
- **Distributed training** scales via data (DDP) → optimizer shard (ZeRO-1) → gradient+optimizer shard (ZeRO-2) → param+grad+opt shard (ZeRO-3/FSDP).
- **Gradient checkpointing**, **QLoRA**, **8-bit optimizers** together make large-model fine-tuning possible on consumer GPUs.
- **Debugging process**: overfit one batch first, then scale up. Track gradient norms, activations, LR. Most failures are simple once instrumented.

→ Next: [🛡️ Regularization & Normalization](regularization.md)
