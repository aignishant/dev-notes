# 🧱 Foundations

!!! abstract "Module Scope"
    The bedrock — perceptron, backprop from first principles, activation functions, loss functions, initialization. Questions **Q1–Q20**. These are interview universals: every deep learning interview touches at least three of them, and weak answers here sink you regardless of how well you know transformers.

---

## Q1. Derive a perceptron and explain what it can't do { #q1 }

<span class="q-badge">Foundational</span>

A perceptron computes:

$$\hat y = \text{sign}(\mathbf{w}^T \mathbf{x} + b)$$

Training rule (Rosenblatt, 1958): for each misclassified example $(\mathbf{x}_i, y_i)$ with $y_i \in \{-1, +1\}$:

$$\mathbf{w} \leftarrow \mathbf{w} + \eta y_i \mathbf{x}_i, \quad b \leftarrow b + \eta y_i$$

**Convergence theorem**: if the data is linearly separable with margin $\gamma$, the perceptron converges in at most $(R/\gamma)^2$ updates, where $R = \max \|\mathbf{x}_i\|$.

**What it can't do (Minsky & Papert, 1969)**: anything not linearly separable. The canonical counterexample is **XOR** — no hyperplane separates $\{(0,0), (1,1)\}$ from $\{(0,1), (1,0)\}$. This killed neural net research for 15 years.

**The fix**: stack perceptrons into a multi-layer network. A single hidden layer with nonlinearity solves XOR trivially. The **universal approximation theorem** (Cybenko 1989, Hornik 1991) shows one hidden layer with enough units can approximate any continuous function on a compact domain.

```python
import numpy as np

class Perceptron:
    def __init__(self, n_features, lr=0.1):
        self.w = np.zeros(n_features)
        self.b = 0.0
        self.lr = lr

    def fit(self, X, y, epochs=20):  # y in {-1, +1}
        for _ in range(epochs):
            for xi, yi in zip(X, y):
                if yi * (self.w @ xi + self.b) <= 0:
                    self.w += self.lr * yi * xi
                    self.b += self.lr * yi
```

<div class="tip-box" markdown>
**Interviewer tip:** If asked "why do we need depth if one hidden layer is universal?" the answer is **expressivity vs efficiency**. A single hidden layer needs exponentially many units to approximate certain functions that a deep network represents compactly. This is why deep learning works.
</div>

---

## Q2. Derive backpropagation on a 2-layer MLP { #q2 }

<span class="q-badge">Foundational • Must Know</span>

Given a network:
$$\mathbf{z}^{(1)} = W^{(1)} \mathbf{x} + \mathbf{b}^{(1)}, \quad \mathbf{a}^{(1)} = \sigma(\mathbf{z}^{(1)})$$
$$\mathbf{z}^{(2)} = W^{(2)} \mathbf{a}^{(1)} + \mathbf{b}^{(2)}, \quad \hat{\mathbf{y}} = \text{softmax}(\mathbf{z}^{(2)})$$
$$L = -\sum_k y_k \log \hat y_k$$

**Backprop is just the chain rule applied layer by layer.**

**Output layer gradient** (cross-entropy + softmax simplifies beautifully):
$$\delta^{(2)} = \frac{\partial L}{\partial \mathbf{z}^{(2)}} = \hat{\mathbf{y}} - \mathbf{y}$$

**Gradients w.r.t. output weights and biases**:
$$\frac{\partial L}{\partial W^{(2)}} = \delta^{(2)} (\mathbf{a}^{(1)})^T, \quad \frac{\partial L}{\partial \mathbf{b}^{(2)}} = \delta^{(2)}$$

**Propagate into hidden layer**:
$$\delta^{(1)} = (W^{(2)})^T \delta^{(2)} \odot \sigma'(\mathbf{z}^{(1)})$$

**Gradients w.r.t. input weights and biases**:
$$\frac{\partial L}{\partial W^{(1)}} = \delta^{(1)} \mathbf{x}^T, \quad \frac{\partial L}{\partial \mathbf{b}^{(1)}} = \delta^{(1)}$$

**General pattern** at layer $\ell$ during the backward pass:
$$\delta^{(\ell)} = (W^{(\ell+1)})^T \delta^{(\ell+1)} \odot \sigma'(\mathbf{z}^{(\ell)})$$

```python
# Manual 2-layer MLP forward and backward
def forward(x, W1, b1, W2, b2):
    z1 = W1 @ x + b1
    a1 = np.maximum(0, z1)           # ReLU
    z2 = W2 @ a1 + b2
    p  = np.exp(z2) / np.exp(z2).sum()  # softmax
    return z1, a1, z2, p

def backward(x, y, z1, a1, z2, p, W2):
    dz2 = p - y                       # softmax+CE simplification
    dW2 = np.outer(dz2, a1)
    db2 = dz2
    da1 = W2.T @ dz2
    dz1 = da1 * (z1 > 0)              # ReLU grad
    dW1 = np.outer(dz1, x)
    db1 = dz1
    return dW1, db1, dW2, db2
```

<div class="tip-box" markdown>
**Interviewer tip:** If asked "what's the computational cost of backprop?" — same order as forward pass. One backward pass = one forward pass. This is why BP is tractable. Numerical differentiation is $O(n)$ times more expensive, which is why nobody uses it.
</div>

---

## Q3. Why sigmoid and tanh fell out of favor for hidden layers { #q3 }

<span class="q-badge">Conceptual</span>

**The vanishing gradient problem.**

- Sigmoid: $\sigma(z) = 1/(1+e^{-z})$, $\sigma'(z) = \sigma(z)(1-\sigma(z))$. Maximum derivative is **0.25** at $z=0$. For $|z| > 4$, derivative is < 0.02.
- tanh: $\tanh'(z) = 1 - \tanh^2(z)$. Maximum derivative is **1** (better), but saturates to 0 for $|z|$ large.

**Gradient through $L$ layers**: gradient magnitude multiplies $L$ of these derivatives. If each is < 1, total gradient shrinks exponentially with depth. For a 20-layer network with sigmoid, gradient at layer 1 is vanishingly small → layer 1 barely learns.

**ReLU fix**: $f(z) = \max(0, z)$, $f'(z) = \mathbb{1}[z > 0]$. Derivative is either 0 or 1 — no shrinkage in the active region.

**Saturation and non-zero centered output** compound the problem:
- Sigmoid output is in $(0, 1)$ — always positive → weights in next layer receive same-sign gradients → zig-zag updates.
- tanh is zero-centered but still saturates.

| Activation | Max derivative | Zero-centered | Still used? |
|---|---|---|---|
| Sigmoid | 0.25 | No | Output layer for binary class, gates in LSTM/GRU |
| tanh | 1.0 | Yes | GRU/LSTM states (zero-centered matters there) |
| ReLU | 1.0 | No | Default choice for hidden layers |
| GELU | ~1.13 | No | Transformers, modern DL default |
| SiLU/Swish | ~1.1 | No | EfficientNet, modern CNNs |

<div class="tip-box" markdown>
**Interviewer follow-up:** "So sigmoid is never used?" Wrong — it's everywhere: LSTM forget/input/output gates need $(0,1)$ outputs, binary classification heads need a probability, attention gating mechanisms use it. It just doesn't belong in deep feed-forward stacks.
</div>

---

## Q4. ReLU — benefits, problems, and the zoo of variants { #q4 }

<span class="q-badge">Foundational</span>

**ReLU** = $\max(0, z)$. Why it won:

1. **No saturation for positive inputs** → gradients flow cleanly.
2. **Computationally trivial** — max and a branch.
3. **Induces sparsity** — about 50% of units are zero at init, encourages disentangled representations.
4. Enables training of very deep networks (first paper: Krizhevsky 2012, AlexNet).

**Problem 1: Dying ReLU.** If a unit's pre-activation is always negative, it outputs zero, its gradient is zero, and it **never recovers**. Happens from bad init or aggressive learning rates. In practice, 10–40% of ReLU units can end up dead.

**Problem 2: Non-differentiable at 0** — a technical curiosity, rarely matters (subgradient convention: grad = 0).

**Variants**:

| Variant | Formula | Fixes |
|---|---|---|
| **Leaky ReLU** | $\max(\alpha z, z)$, $\alpha \approx 0.01$ | Dying ReLU |
| **Parametric ReLU (PReLU)** | Leaky but $\alpha$ learned per-channel | Adaptive slope |
| **ELU** | $z$ if $z>0$ else $\alpha(e^z - 1)$ | Smooth, zero-mean output |
| **SELU** | Scaled ELU with magic constants | Self-normalizing (no BN needed, in theory) |
| **GELU** | $z \cdot \Phi(z)$ (Gaussian CDF) | Smooth, probabilistic interpretation — standard in transformers |
| **Swish / SiLU** | $z \cdot \sigma(z)$ | Smooth, non-monotonic, empirically strong |
| **Mish** | $z \cdot \tanh(\text{softplus}(z))$ | Similar to Swish, slightly different profile |

```python
import torch.nn as nn
# Modern choice: nn.GELU() for transformers, nn.SiLU() for CNNs/vision
```

<div class="scenario" markdown>
**Scenario:** Training a 10-layer network with ReLU, loss stopped decreasing at epoch 5. 30% of ReLU units output zero for all validation inputs.<br>
**Answer:** Dead ReLU epidemic. Fixes: (1) switch to **Leaky ReLU** or **GELU**, (2) reduce learning rate — often the trigger, (3) check initialization — Kaiming init is tuned for ReLU, using Xavier makes the problem worse, (4) add batch norm before ReLU to keep pre-activations centered. Diagnostics: log the fraction of dead units per layer per epoch.
</div>

---

## Q5. Softmax — derivation, numerical stability, why temperature { #q5 }

<span class="q-badge">Foundational</span>

**Softmax** converts logits $\mathbf{z} \in \mathbb{R}^K$ to a probability distribution:

$$p_k = \frac{e^{z_k}}{\sum_{j} e^{z_j}}$$

**Why softmax specifically?** It's the exponential family canonical link for a multinomial distribution — gives a max-entropy distribution for a given mean. Monotone: higher logit → higher probability.

**Numerical stability**: $e^{z_k}$ overflows for $z_k > \sim 88$ (float32). Subtract max before exponentiating (doesn't change the output):

$$p_k = \frac{e^{z_k - \max_j z_j}}{\sum_j e^{z_j - \max_j z_j}}$$

Now the max exponent is $e^0 = 1$ — no overflow.

**Log-softmax** (for cross-entropy loss) is even more stable:

$$\log p_k = z_k - \log\sum_j e^{z_j} = z_k - \max_j z_j - \log\sum_j e^{z_j - \max_j z_j}$$

**Temperature** $T$: $p_k = \frac{e^{z_k/T}}{\sum_j e^{z_j/T}}$

- $T = 1$: standard softmax
- $T \to 0$: argmax (one-hot), used for "sharp" decisions in inference
- $T \to \infty$: uniform distribution, used for **exploration** in RL or **diversity** in LLM sampling
- $T \in (0, 1)$: more confident / sharper — used in **knowledge distillation** (student mimics softened teacher distribution)

```python
import torch
import torch.nn.functional as F

logits = torch.randn(8, 10)
# Numerically stable softmax
probs = F.softmax(logits, dim=-1)
log_probs = F.log_softmax(logits, dim=-1)  # preferred for CE loss

# Temperature sampling (LLM decoding)
T = 0.7
probs = F.softmax(logits / T, dim=-1)
```

<div class="tip-box" markdown>
**Interviewer gotcha:** "What's the gradient of softmax w.r.t. logit $z_k$?" The Jacobian $\partial p_i / \partial z_k = p_i(\delta_{ik} - p_k)$. This combines with CE-loss $\partial L / \partial p_i = -y_i/p_i$ to give the famous simple form $\partial L / \partial z_k = p_k - y_k$.
</div>

---

## Q6. Cross-entropy vs MSE — why CE for classification { #q6 }

<span class="q-badge">Conceptual</span>

**Cross-entropy**: $L = -\sum_k y_k \log \hat y_k$
**MSE**: $L = \frac{1}{2}\sum_k (y_k - \hat y_k)^2$

Three reasons CE dominates classification:

**1. Gradient doesn't vanish when the prediction is wrong.** 

For sigmoid + MSE: $\partial L / \partial z = (y - \hat y) \cdot \sigma'(z) = (y - \hat y) \cdot \hat y (1 - \hat y)$. If the network confidently predicts wrong class ($\hat y \approx 1$ when $y = 0$), $\sigma'(z) \approx 0$ → gradient vanishes → **no learning signal despite being very wrong**.

For sigmoid + CE: $\partial L / \partial z = \hat y - y$. Confidently wrong → gradient is $1 - 0 = 1$, maximal correction.

**2. Information-theoretic grounding.**

CE is the expected number of bits to encode samples from distribution $y$ using code optimal for $\hat y$. Minimizing CE = minimizing KL divergence $y \| \hat y$ (up to entropy of $y$, which is constant in labels).

**3. MLE under multinomial distribution.**

If you model labels as multinomial with parameters $\hat{\mathbf{y}}$, the log-likelihood of $y$ is exactly the negative CE.

| Property | CE | MSE |
|---|---|---|
| Loss when prediction is wrong | High (log scale) | Low-to-moderate (squared) |
| Gradient when confidently wrong | Strong | Can vanish with sigmoid |
| Probabilistic interpretation | MLE under multinomial | MLE under Gaussian (wrong model for labels) |
| Works with softmax | ✅ Gradient simplifies | ❌ Multiple local optima |

**When MSE for classification is still used**: label smoothing blends; some distillation setups; regression heads that output probabilities implicitly. Generally, CE is the default.

<div class="tip-box" markdown>
**Interviewer follow-up:** "When would you use MSE for a regression task vs MAE?" MSE for Gaussian noise (strongly penalizes outliers), MAE for Laplace noise (robust). Huber loss splits the difference — quadratic near zero, linear far from zero — giving outlier robustness without MAE's non-smoothness at zero.
</div>

---

## Q7. Xavier, Kaiming, and why initialization matters { #q7 }

<span class="q-badge">Foundational • Must Know</span>

**The problem**: bad init → activations either vanish (all zeros) or explode (Inf) as they flow forward. Same problem for gradients during backward. Training fails.

**Goal of good init**: keep variance of activations (forward) and gradients (backward) roughly constant across layers.

**Xavier / Glorot init** (2010, for tanh/sigmoid):

$$W \sim \mathcal{N}\left(0, \frac{2}{n_{\text{in}} + n_{\text{out}}}\right) \quad \text{or} \quad W \sim \mathcal{U}\left[-\sqrt{\frac{6}{n_{\text{in}} + n_{\text{out}}}}, \sqrt{\frac{6}{n_{\text{in}} + n_{\text{out}}}}\right]$$

Derivation: for $\mathbf{y} = W\mathbf{x}$ with $\mathbf{x}$ unit-variance and $W$ iid zero-mean, $\text{Var}(y_i) = n_{\text{in}} \text{Var}(W)$. To keep $\text{Var}(y) = 1$, need $\text{Var}(W) = 1/n_{\text{in}}$ (for forward). The average of $1/n_{\text{in}}$ and $1/n_{\text{out}}$ gives Xavier's $2/(n_{\text{in}} + n_{\text{out}})$ — compromise between forward and backward variance.

**Kaiming / He init** (2015, for ReLU):

$$W \sim \mathcal{N}\left(0, \frac{2}{n_{\text{in}}}\right)$$

The factor of 2 compensates for ReLU killing half the activations on average. Using Xavier with ReLU → activations shrink by $\sqrt{1/2}$ per layer → very deep nets stop learning.

| Activation | Use |
|---|---|
| tanh, sigmoid | **Xavier** (gain = 1) |
| ReLU, Leaky ReLU | **Kaiming** (gain = $\sqrt{2}$) |
| SELU | **LeCun normal** ($\text{Var} = 1/n_{\text{in}}$) |
| Linear / output head | **Xavier** or small random |

```python
import torch.nn as nn

for m in model.modules():
    if isinstance(m, nn.Linear):
        nn.init.kaiming_normal_(m.weight, nonlinearity='relu')
        nn.init.zeros_(m.bias)
    elif isinstance(m, nn.Conv2d):
        nn.init.kaiming_normal_(m.weight, nonlinearity='relu')
```

**Bias init**: typically zero. Some architectures use small positives for ReLU biases to reduce dying ReLU.

<div class="scenario" markdown>
**Scenario:** A 50-layer MLP trains fine for 20 epochs, then loss suddenly explodes.<br>
**Answer:** Classic activation-magnitude drift. Even with good init, variance grows layer by layer under nonlinear dynamics. Fix with **batch norm** or **layer norm** between layers — they rescale activations back to zero-mean unit-variance, making deep training stable. This is why BN was a revolution: it decouples init quality from training stability.
</div>

---

## Q8. Batch normalization — derivation and why it works { #q8 }

<span class="q-badge">Foundational • Must Know</span>

**BN** normalizes a minibatch $B = \{x_1, \dots, x_m\}$ per feature:

$$\mu_B = \frac{1}{m}\sum_i x_i, \quad \sigma_B^2 = \frac{1}{m}\sum_i (x_i - \mu_B)^2$$
$$\hat x_i = \frac{x_i - \mu_B}{\sqrt{\sigma_B^2 + \epsilon}}, \quad y_i = \gamma \hat x_i + \beta$$

$\gamma, \beta$ are learned per-feature — let the network undo normalization if needed.

**Inference**: use **running** mean and variance (exponential moving averages from training).

**Why does it work?** Two competing narratives:

1. **Original paper (Ioffe & Szegedy, 2015)**: reduces "internal covariate shift" — layers don't need to re-adapt as earlier layer stats drift during training.
2. **Later analysis (Santurkar et al., 2018)**: the covariate shift explanation is wrong — BN still helps even with random noise added to batch stats. Real reason: **BN smooths the loss landscape** (reduces Lipschitz constant of loss and of its gradient), allowing higher learning rates and more stable training.

**What you get**:

- Higher learning rates without divergence (often 5–10x).
- Faster convergence (often 2–4x fewer epochs).
- Mild regularization effect (batch stats are noisy).
- Less sensitivity to init quality.

**Problems**:

- Depends on batch size → fails for batch size 1 (e.g., fine-tuning with limited memory).
- Inconsistency between train (batch stats) and eval (running stats) — especially problematic for small batches.
- Interferes with RNNs (different length → different batch stats).

```python
import torch.nn as nn

layer = nn.Sequential(
    nn.Linear(256, 256),
    nn.BatchNorm1d(256),   # note: before activation, after linear
    nn.ReLU()
)
```

<div class="tip-box" markdown>
**Interviewer gotcha:** "Should BN come before or after activation?" The original paper puts it **before activation** (the most common convention in 2026). Some papers have tried after-activation — both work, but consistency and the original convention is safer.
</div>

---

## Q9. Layer norm, instance norm, group norm — when each { #q9 }

<span class="q-badge">Comparison</span>

**BN normalizes across the batch dimension**. Alternatives normalize differently:

| Method | Normalizes across | Batch-dependent? |
|---|---|---|
| **Batch Norm (BN)** | Batch + spatial (per channel) | Yes |
| **Layer Norm (LN)** | Channels + spatial (per sample) | No |
| **Instance Norm (IN)** | Spatial only (per sample, per channel) | No |
| **Group Norm (GN)** | Groups of channels + spatial (per sample) | No |

**Intuition via tensor dimensions** for image tensor $(N, C, H, W)$:

```
BN: normalize over (N, H, W), independently per channel C
LN: normalize over (C, H, W), independently per sample N
IN: normalize over (H, W),    independently per (N, C)
GN: normalize over (G, H, W) where channels grouped into G groups
```

**When each wins**:

- **BN**: big-batch CNN training (ImageNet). Not for RNNs or tiny batches.
- **LN**: transformers, RNNs, batch-size-1 training. Does not depend on batch, works identically at train and eval.
- **IN**: style transfer, GANs — when you want to remove style info (channel stats = style).
- **GN**: object detection / segmentation with batch size 2–4 per GPU, where BN is unreliable.

```python
# Transformer block uses LayerNorm
nn.LayerNorm(d_model)

# CNN with small batches — use GroupNorm
nn.GroupNorm(num_groups=32, num_channels=256)

# Style transfer — InstanceNorm
nn.InstanceNorm2d(num_channels)
```

<div class="scenario" markdown>
**Scenario:** Fine-tuning a pretrained CNN with batch size 2 (memory limits). Training loss is fine but validation accuracy is erratic.<br>
**Answer:** Small-batch BN is notoriously unstable — running stats drift because each update only uses 2 samples. Fix: (1) **freeze BN layers** (use pretrained stats, track_running_stats=False), (2) replace BN with **GroupNorm** if weights allow, (3) use **gradient accumulation** to simulate larger effective batch size.
</div>

---

## Q10. Forward pass tensor shapes — explain dimensional flow for a Linear, Conv2d, and Attention { #q10 }

<span class="q-badge">Practical</span>

Knowing shapes fluently is the mark of someone who's actually built models. Cold shapes here:

**nn.Linear(in, out)** for batch of $N$ vectors:
- Input: $(N, \text{in})$
- Weight: $(\text{out}, \text{in})$
- Output: $(N, \text{out})$

**nn.Conv2d(C_in, C_out, K, stride=S, padding=P)**:
- Input: $(N, C_{\text{in}}, H, W)$
- Weight: $(C_{\text{out}}, C_{\text{in}}, K, K)$
- Output: $(N, C_{\text{out}}, H', W')$, where $H' = \lfloor (H + 2P - K)/S \rfloor + 1$.

**Multi-head attention** with $d$ = model dim, $h$ = heads, $d_k = d/h$:
- Input: $(N, L, d)$ where $L$ = sequence length
- $Q, K, V$: each $(N, L, d)$
- Reshape to $(N, L, h, d_k)$, transpose to $(N, h, L, d_k)$
- Scores $QK^T$: $(N, h, L, L)$
- Output: reshape back to $(N, L, d)$

```python
import torch
import torch.nn as nn

# Linear
x = torch.randn(8, 128)        # (batch, features)
fc = nn.Linear(128, 64)
out = fc(x)                     # (8, 64)

# Conv2d
x = torch.randn(8, 3, 32, 32)  # (batch, channels, H, W)
conv = nn.Conv2d(3, 16, kernel_size=3, padding=1)
out = conv(x)                   # (8, 16, 32, 32)

# Multi-head attention
mha = nn.MultiheadAttention(embed_dim=512, num_heads=8, batch_first=True)
x = torch.randn(8, 100, 512)  # (batch, seq_len, d_model)
out, weights = mha(x, x, x)    # out: (8, 100, 512), weights: (8, 100, 100)
```

<div class="tip-box" markdown>
**Interviewer tip:** Always verify shapes with `print(tensor.shape)` when debugging. Most "silent bugs" in deep learning are shape mismatches that happen to broadcast. A well-placed `assert x.shape == (B, C, H, W)` saves hours.
</div>

---

## Q11. Universal approximation theorem — what it really says { #q11 }

<span class="q-badge">Conceptual</span>

**Cybenko (1989) / Hornik (1991):** A feedforward network with a single hidden layer of finite units using a non-constant, bounded, monotonically-increasing activation (sigmoid suffices) can approximate any continuous function on a compact subset of $\mathbb{R}^n$ to arbitrary accuracy.

**What it does NOT say**:

1. **How many units you need.** Often exponentially many for functions that a deep network represents with far fewer.
2. **That training will find such a network.** It says *exists* — the optimization problem to find it is non-convex.
3. **That training data is sufficient.** Approximation is one thing, generalization to unseen data is another (that's statistical learning theory).

**Why this is interesting, not practical**:

- A deep network can represent some functions with $O(n)$ units that require $\Omega(2^n)$ units in a one-hidden-layer network (Telgarsky 2016).
- Representational capacity is about *what's possible*, not *what SGD can realistically find*.

**Depth vs width**:

- Width scales expressivity additively; depth scales multiplicatively.
- Deep narrow > wide shallow for most practical problems (below some overcapacity threshold).

<div class="tip-box" markdown>
**Interviewer tip:** If you say "universal approximation" as a justification for architecture choice, you've missed the point. It proves existence, not tractability or parameter efficiency. Use it as context, not as an answer.
</div>

---

## Q12. What is "inductive bias"? Contrast CNN, RNN, Transformer { #q12 }

<span class="q-badge">Conceptual</span>

**Inductive bias** = the assumptions an architecture or algorithm makes about the world, built into its structure.

More inductive bias → less data needed, but fails if the world doesn't match. Less bias (e.g., MLP) → more flexible, but data-hungry.

| Architecture | Inductive bias |
|---|---|
| **MLP** | Almost none — generic function approximator |
| **CNN** | Translation equivariance (a cat is a cat wherever it is), local receptive fields, weight sharing |
| **RNN / LSTM** | Temporal locality, sequential computation, exponentially decaying memory |
| **Transformer** | Permutation equivariance (minus positional encoding), global receptive field, pairwise interactions |
| **GNN** | Relational bias — messages flow along edges, permutation invariance over neighbors |

**Why this matters for interviews**:

- **Small data** → stronger inductive bias wins. A CNN trained from scratch on 1000 images beats a ViT from scratch on the same data. ViTs need more data (or pretraining) to work.
- **Large data** → weaker inductive bias wins. The architecture's flexibility lets it extract patterns we didn't bake in. This is why ViTs overtook CNNs at scale.

**The "bitter lesson" (Rich Sutton, 2019)**: methods with less inductive bias tend to win over decades, as compute and data scale. Hand-engineered features → learned features. CNN priors → attention priors. Eventually even attention priors will be traded for compute at bigger scale.

<div class="scenario" markdown>
**Scenario:** Team wants to use a ViT for 500-image fine-grained species classification.<br>
**Answer:** Bad fit unless pretrained. ViT has weak inductive bias — needs ~10M images or strong pretraining to compete with a ResNet-50. For 500 images, use a **pretrained CNN** (ResNet, EfficientNet) or a **pretrained ViT** and fine-tune. Training from scratch will lose to nearly any baseline.
</div>

---

## Q13. Train / val / test split — and k-fold for deep learning { #q13 }

<span class="q-badge">Practical</span>

**Three splits, three purposes**:

| Split | Used for | Touched how often |
|---|---|---|
| **Train** | Fit model parameters | Every iteration |
| **Val** | Hyperparameter tuning, early stopping, model selection | Every epoch or periodically |
| **Test** | Final held-out estimate of generalization | **Once** at end |

**Why three and not two**: if you tune hyperparameters on "test", your test set leaks into model selection, and you overestimate performance. This is the single most common leak in research.

**Sizes**: classic 80/10/10 or 70/15/15 for balanced medium data. For massive data, even 98/1/1 works (val and test are still big in absolute terms). For tiny data, **k-fold CV** across train+val, reserve test for final.

**k-fold for deep learning**: less common because (1) training cost is high, (2) val curves guide early stopping, (3) you usually have enough data. When used:

- 5-fold CV for hyperparameter tuning.
- Leave test set fully untouched.
- Average val metrics across folds for robust hyperparameter selection.

**Common mistakes**:

1. **Looking at test during development** → pseudo-leakage ("I'll just peek at test"). Don't.
2. **Data leakage through augmentations or preprocessing** — scaling fit on train+val+test.
3. **Split not accounting for structure** — random split of time-series, speakers, patients leaks across split.

```python
from sklearn.model_selection import train_test_split

# Stratified split for classification
X_trainval, X_test, y_trainval, y_test = train_test_split(
    X, y, test_size=0.15, stratify=y, random_state=42)
X_train, X_val, y_train, y_val = train_test_split(
    X_trainval, y_trainval, test_size=0.15/0.85, stratify=y_trainval, random_state=42)
```

<div class="tip-box" markdown>
**Interviewer tip:** Mention **group-based splits** (e.g., `GroupKFold`) for medical data (by patient) or speech data (by speaker). Random split there is catastrophic leakage.
</div>

---

## Q14. Autograd — how automatic differentiation actually works { #q14 }

<span class="q-badge">Conceptual</span>

PyTorch / TensorFlow autograd uses **reverse-mode automatic differentiation** — mechanized backprop on an arbitrary computation graph.

**Key concepts**:

1. **Dynamic computation graph** (PyTorch): graph is built as operations execute. Each tensor with `requires_grad=True` and its parents form a DAG.
2. **Each op stores its backward function** — given upstream gradient, computes local gradient and propagates.
3. **Reverse-mode**: traverse the graph in reverse topological order, accumulating gradients via chain rule. One backward pass computes gradients w.r.t. **all** parameters in one shot.

**Why reverse-mode for DL**: we have one scalar output (loss) and millions of parameters. Reverse-mode is $O(\text{forward})$; forward-mode would be $O(\text{params} \times \text{forward})$.

**In PyTorch**:
```python
import torch
x = torch.tensor(3.0, requires_grad=True)
y = x**2 + 2*x + 1         # y = 16.0
y.backward()                # compute dy/dx
print(x.grad)               # 2*3 + 2 = 8.0
```

**Common gotchas**:

1. **`.detach()`** — cuts off gradient flow. Used for frozen features, for visualization.
2. **Accumulation** — PyTorch *accumulates* gradients. Must call `optimizer.zero_grad()` each step.
3. **In-place ops (`x += ...`)** — can silently break autograd if intermediate values are needed for backward.
4. **`with torch.no_grad():`** — disables graph tracking. Use for inference and validation to save memory.

```python
# Typical train step
optimizer.zero_grad()        # clear old grads
logits = model(x)
loss = F.cross_entropy(logits, y)
loss.backward()              # populate .grad on all params
optimizer.step()             # apply update
```

<div class="tip-box" markdown>
**Interviewer gotcha:** "What's `retain_graph=True` for?" If you need to backprop through the same graph more than once (e.g., RNN with truncated BPTT, or multiple loss heads), you must retain the graph. Otherwise autograd frees the intermediate activations immediately after the first backward.
</div>

---

## Q15. Loss function zoo — know the top ten { #q15 }

<span class="q-badge">Reference</span>

| Loss | Formula | When |
|---|---|---|
| **MSE** | $\frac{1}{N}\sum (y - \hat y)^2$ | Gaussian-noise regression |
| **MAE** | $\frac{1}{N}\sum \|y - \hat y\|$ | Robust regression, outliers |
| **Huber** | Quadratic near 0, linear far | Compromise MSE/MAE |
| **Binary CE** | $-[y\log \hat y + (1-y)\log(1-\hat y)]$ | Binary classification |
| **Categorical CE** | $-\sum_k y_k \log \hat y_k$ | Multiclass |
| **Focal loss** | $-(1-\hat y)^\gamma \log \hat y$ | Class imbalance (detection) |
| **Contrastive / Triplet** | $\max(0, d(a,p) - d(a,n) + m)$ | Embedding learning |
| **CTC** | Marginalizes over alignments | Unaligned sequences (speech) |
| **KL divergence** | $\sum y \log(y/\hat y)$ | Distillation, variational learning |
| **Wasserstein** | $\inf_{\gamma} \mathbb{E}[\|x - y\|]$ | GAN training, distribution matching |

**Focal loss** (Lin et al., 2017) deserves special attention — the default fix for class imbalance in detection:

$$L_{\text{focal}} = -\alpha_t (1 - p_t)^\gamma \log p_t$$

where $p_t$ is the probability assigned to the true class. The $(1-p_t)^\gamma$ factor downweights easy examples (high $p_t$) so the model focuses on hard ones. $\gamma = 2$ is common. Widely used in object detection (RetinaNet) and imbalanced classification.

**Contrastive learning losses** (for self-supervised pretraining):

- **InfoNCE / NT-Xent**: pull positive pairs closer, push away in-batch negatives. Used in SimCLR, CLIP, MoCo.

$$L = -\log \frac{\exp(\text{sim}(z_i, z_{i+})/\tau)}{\sum_j \exp(\text{sim}(z_i, z_j)/\tau)}$$

**CTC loss** (Connectionist Temporal Classification): lets you train speech or handwriting models when input and output aren't aligned frame-by-frame — model emits per-frame distributions, CTC marginalizes over all valid alignments.

<div class="tip-box" markdown>
**Interviewer tip:** Pick the loss that matches the **generative process of your labels**, not just "the standard loss". MSE for regression assumes Gaussian noise; MAE assumes Laplace. CE assumes multinomial labels. When the assumption is wrong, the loss is wrong.
</div>

---

## Q16. Learning rate — the single most important hyperparameter { #q16 }

<span class="q-badge">Practical • Must Know</span>

**Why LR dominates**: it controls how far each gradient step moves. Too small → training crawls. Too large → training diverges. The right range depends on the optimizer, loss scale, architecture, batch size, and data.

**Typical ranges** (good starting points):

| Optimizer | Vision | NLP / Transformers |
|---|---|---|
| SGD + momentum | 1e-1 to 1e-2 | Not usually used |
| Adam | 1e-3 | 1e-4 to 5e-5 |
| AdamW | 1e-3 to 3e-4 | 1e-4 to 5e-5 |

**LR range test** (Smith 2018) — the single best way to find LR quickly:

1. Start at $10^{-8}$, exponentially increase each batch up to ~$10$.
2. Plot loss vs log(LR).
3. Optimal LR is about an order of magnitude below the LR where loss starts diverging.

```python
# One-cycle LR finder in PyTorch
from torch.optim.lr_scheduler import OneCycleLR

optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
scheduler = OneCycleLR(optimizer, max_lr=1e-3,
                       steps_per_epoch=len(train_loader), epochs=20)
```

**Common LR schedules**:

- **Step decay**: cut by $\gamma$ every $N$ epochs.
- **Cosine annealing**: smooth decay following $\cos$ curve. Often superior to step.
- **Cosine with warm restarts**: periodic cosine, periodic resets. Great for escaping local optima.
- **One-cycle** (Leslie Smith): warmup up to peak, then cosine decay. Standard for fast training.
- **Linear warmup then decay**: transformers default. Critical — transformers don't train without warmup.

**LR warmup** (for transformers): start at ~0, linear ramp over 1–10% of training. Without warmup, early gradients are noisy (BN/LN stats not stable, Adam moment estimates uninitialized) and can push weights into bad regions.

<div class="scenario" markdown>
**Scenario:** Transformer training diverges at step 200.<br>
**Answer:** Three likely causes. (1) **Missing LR warmup** — without it, Adam's second-moment estimate is tiny initially → effective LR is huge → divergence. Add warmup. (2) **Learning rate too high** — halve it. (3) **Gradient clipping missing** — clip to 1.0. These three are the essentials for stable transformer training; run through them in order.
</div>

---

## Q17. Overfitting — how to diagnose and what to do { #q17 }

<span class="q-badge">Practical</span>

**Diagnosis: train/val curves**.

| Train loss | Val loss | Interpretation | Action |
|---|---|---|---|
| Decreasing | Decreasing | Fine, train more | Continue |
| Decreasing | Plateaued | Slight overfit | More regularization |
| Decreasing | Increasing | Overfitting | Strong regularization or early stop |
| High | High | Underfitting | Bigger model, longer training, better features |
| Train << Val | — | Classic overfit | Regularize |
| Train ~ Val, both poor | — | Underfit or bad architecture | More capacity, longer training |

**Regularization toolkit** (in order of what to try first):

1. **More data** — best cure. Augmentation counts.
2. **Dropout** — 0.1 to 0.5, higher for bigger networks.
3. **Weight decay** (L2 regularization) — typically 1e-4 to 1e-2 for AdamW.
4. **Early stopping** — monitor val, stop when patience exceeded.
5. **Smaller model** — reduce layers or hidden dim.
6. **Data augmentation** — crop, flip, color jitter, CutMix, MixUp.
7. **Label smoothing** — target 0.9 instead of 1.0 for correct class.
8. **Stochastic depth / DropPath** — randomly skip residual blocks (for deep nets).

**Diagnosing subtler issues**:

- **Overfit to specific batches**: training loss is bumpy with huge valleys — check for corrupted batches or look at learning rate.
- **Overfit to class imbalance**: val loss looks fine but per-class metrics are skewed — use balanced metrics (F1, macro avg).
- **Overfit to preprocessing**: e.g., model memorized the fact that class A images have a watermark. Blinded augmentation exposes this.

<div class="tip-box" markdown>
**Interviewer tip:** When a model "overfits", the first question isn't "what regularization?" but "**is the validation set representative?**" If val is easier than test (different distribution), you won't see overfit in val — you'll see it at deployment.
</div>

---

## Q18. Parameter count, FLOPs, and what really matters for inference cost { #q18 }

<span class="q-badge">Practical</span>

**Parameter count** = memory + weight storage cost. Does NOT equal inference speed.

**FLOPs** (floating-point operations) = arithmetic cost. Closer to speed but still imperfect.

**Real-world latency** is driven by:

1. **Memory bandwidth** — moving weights + activations from DRAM to compute. Often the bottleneck, not FLOPs.
2. **Sequential dependencies** — an RNN's 1000 sequential steps force 1000 kernel launches.
3. **Kernel launch overhead** — many tiny ops is worse than one big op.
4. **Batch size** — tiny batches underutilize GPU; latency per sample drops with batch.
5. **Hardware features** — Tensor Cores accelerate mat-mul but not pointwise ops.

**Rules of thumb**:

- **Conv2d** dominated by multiplies: $\text{FLOPs} \approx 2 \times C_{\text{in}} \times C_{\text{out}} \times K^2 \times H \times W$.
- **Linear**: $\text{FLOPs} \approx 2 \times N \times \text{in} \times \text{out}$.
- **Attention** is $O(L^2 d)$ for sequence length $L$ — quadratic in sequence length is the transformer pain point.

**Measuring**:
```python
# FLOPs counting
from thop import profile
flops, params = profile(model, inputs=(torch.randn(1, 3, 224, 224),))
print(f"{params/1e6:.2f}M params, {flops/1e9:.2f}G FLOPs")

# Real latency
import torch.utils.benchmark as bench
t = bench.Timer(stmt="model(x)", globals={'model': model, 'x': x})
print(t.timeit(100))
```

**How to speed up inference**:

- **Quantization** (INT8, INT4): 2-4x speedup, minor accuracy loss.
- **Knowledge distillation**: smaller model trained to match big model.
- **Pruning**: zero out small weights, accelerate with sparse kernels.
- **Graph compilation**: TorchScript, ONNX, TensorRT — fuse ops, pick best kernels.
- **FlashAttention / efficient attention** — for transformers.

<div class="scenario" markdown>
**Scenario:** Two CNNs — model A has 10M params, 2 GFLOPs; model B has 100M params, 500 MFLOPs. Which is faster at inference?<br>
**Answer:** **It depends.** Model B has 10x more params (more memory bandwidth) but 4x fewer FLOPs (less compute). On a bandwidth-bound hardware (mobile, CPU), model A wins. On a compute-bound regime (large batch on GPU), model B wins. The right answer involves **measurement on the target hardware** — theoretical FLOPs and params don't decide it.
</div>

---

## Q19. Epoch vs iteration vs step — and how batch size affects everything { #q19 }

<span class="q-badge">Practical</span>

**Definitions**:

- **Iteration / step**: one forward + backward + optimizer update (one mini-batch).
- **Epoch**: one full pass through the training set.
- **Steps per epoch** = $\lceil N / B \rceil$, where $N$ = dataset size, $B$ = batch size.

**Batch size effects**:

| Larger batch | Smaller batch |
|---|---|
| More stable gradients (lower variance estimate) | Noisier gradients |
| Faster throughput per epoch (better GPU utilization) | More steps per epoch, finer update granularity |
| Requires higher LR to maintain train dynamics (linear scaling rule) | Lower LR sufficient |
| Can hurt generalization ("generalization gap" — large-batch SGD converges to sharp minima) | Noise acts as regularizer, better generalization |
| Need warmup to stabilize | Often no warmup needed |

**Linear scaling rule** (Goyal et al., 2017): when batch size scales by $k$, scale LR by $k$. Works up to some batch size ceiling, beyond which it breaks.

**Gradient accumulation** — simulate larger batch when memory-limited:

```python
accum_steps = 4   # effective batch size = actual_batch_size * 4
for i, (x, y) in enumerate(loader):
    loss = F.cross_entropy(model(x), y) / accum_steps
    loss.backward()
    if (i + 1) % accum_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

**Mixed precision** (FP16 + FP32): 2x memory, 2–3x speedup on modern GPUs. Use `torch.cuda.amp`:

```python
scaler = torch.cuda.amp.GradScaler()
for x, y in loader:
    with torch.cuda.amp.autocast():
        loss = F.cross_entropy(model(x), y)
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

<div class="tip-box" markdown>
**Interviewer tip:** "How should I choose batch size?" — Fill the GPU memory as much as possible, then set LR according to scaling rule. Large-batch generalization gap is real but usually fixable with more epochs, warmup, and LR scaling. Don't go smaller than 32 unless forced by memory.
</div>

---

## Q20. Checkpointing, saving, reproducibility — the engineering essentials { #q20 }

<span class="q-badge">Practical</span>

**What to save in a checkpoint**:

```python
checkpoint = {
    'epoch': epoch,
    'step': global_step,
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),   # Adam has moments!
    'scheduler_state_dict': scheduler.state_dict(),   # LR state
    'scaler_state_dict': scaler.state_dict(),         # for AMP
    'random_states': {                                # for reproducibility
        'cpu': torch.get_rng_state(),
        'cuda': torch.cuda.get_rng_state_all(),
        'numpy': np.random.get_state(),
        'python': random.getstate(),
    },
    'val_loss': best_val_loss,
    'config': config,                                 # hyperparameters
}
torch.save(checkpoint, 'checkpoint.pt')
```

**Reproducibility requirements**:

```python
import torch, random, numpy as np

# Seed everything
seed = 42
torch.manual_seed(seed)
torch.cuda.manual_seed_all(seed)
np.random.seed(seed)
random.seed(seed)
torch.backends.cudnn.deterministic = True  # slower but reproducible
torch.backends.cudnn.benchmark = False
# Python hash seed (set as env var before Python starts)
```

**Full reproducibility is harder than it looks**:

- Different CUDA versions → different results.
- Different GPU models → different results (different kernel selections).
- Non-deterministic CUDA kernels (e.g., atomic adds in scatter) → different results even with fixed seed.
- Multi-GPU training order dependencies.

**Pragmatic standard**: reproducible **up to** a small epsilon, not bit-identical.

**Best-practice checkpointing strategy**:

1. Save every $N$ steps + every epoch.
2. Keep last 3 + best (by val metric).
3. Upload to cloud storage for crash resilience.
4. Save `config.yaml` alongside for provenance.
5. Save environment (`pip freeze > requirements.txt`).

<div class="tip-box" markdown>
**Interviewer signal:** "How do you resume training after a crash?" Strong answer: "Load checkpoint including optimizer state (Adam's moments are critical — losing them = ~epochs of wasted compute), scheduler state, RNG state, and AMP scaler. Resume at the exact step." Weak answer: "I load the model weights." Optimizer state is the tell.
</div>

---

## ✅ Module Recap

- **Backprop** is just the chain rule applied to a computation graph. The output-layer simplification $\delta = \hat y - y$ for softmax+CE is the single cleanest derivation in ML.
- **Activations**: default to **ReLU** for CNNs, **GELU** for transformers. Know why sigmoid/tanh fell out of favor (vanishing gradients).
- **Init** matters enormously: Xavier for tanh, Kaiming for ReLU. BN reduces sensitivity but isn't a substitute for good init.
- **BN / LN / GN** serve different regimes. BN for large-batch CNNs, LN for transformers, GN for small-batch vision.
- **LR** is the most important hyperparameter. Use a LR range test, warmup for transformers, cosine/one-cycle schedules.
- **Engineering essentials**: checkpointing, seeding, mixed precision, gradient accumulation. These are what separate "I can make it train" from "I can make it train reliably in production."

→ Next: [👁️ CNNs & Vision](cnns.md)
