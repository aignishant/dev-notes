# 3. Training & Optimization

> **Module goal:** Anything you train — tree ensemble, deep net, LLM fine-tune — uses the same underlying math. Master it once, apply it everywhere.

---

## Q41. Gradient descent — derive it from scratch { #q41 }

**Goal:** minimize a loss `L(θ)` where θ are model parameters.

**Idea:** the gradient `∇L(θ)` points in the direction of steepest *increase*. So step in the *opposite* direction.

```
θ_{t+1} = θ_t − η · ∇L(θ_t)
```

where η is the learning rate.

**Why it works (intuitively):**

- Taylor expansion: `L(θ + Δ) ≈ L(θ) + ∇L(θ)ᵀ Δ + O(|Δ|²)`
- To decrease L, pick Δ in the direction of `−∇L(θ)`.
- Small η keeps the linear approximation valid.

**Convex vs non-convex:**

- Convex loss (linear/logistic regression, SVM) — GD reaches the global minimum.
- Non-convex (neural nets) — GD reaches *some* local minimum. In practice, for overparameterized nets, local minima are empirically good.

```python
# Vanilla gradient descent by hand (linear regression)
import numpy as np

def gd_linear_regression(X, y, lr=0.01, n_iter=1000):
    n, d = X.shape
    theta = np.zeros(d)
    for t in range(n_iter):
        grad = (2/n) * X.T @ (X @ theta - y)
        theta -= lr * grad
    return theta
```

---

## Q42. Batch GD vs SGD vs Mini-batch GD { #q42 }

| Variant | Batch size | Pros | Cons |
|---|---|---|---|
| **Batch GD** | Full dataset | True gradient; smooth convergence | Slow; can't fit in memory |
| **SGD (stochastic)** | 1 sample | Fast updates; escapes saddle points due to noise | Very noisy; small LR needed |
| **Mini-batch GD** | 32–1024 | Stable, GPU-efficient, noise helps generalization | Hyperparameter: batch size |

**Why mini-batch noise is a *feature*, not a bug:**

The noise acts as implicit regularization. It lets the optimizer escape sharp minima (which generalize poorly) and settle into flat minima (which generalize well). This is one explanation for why SGD-trained networks often beat second-order methods.

**The batch size tradeoff:**

- Small batch (32) — more noise, better generalization, slower per epoch.
- Large batch (4096+) — faster per epoch, but needs warmup + scaled LR; can hurt generalization without tricks.

!!! tip "The linear scaling rule"
    If you scale batch size by k, scale LR by k too (Goyal et al. 2017). Works up to a point; beyond that, you need LARS/LAMB optimizers.

---

## Q43. Momentum, Nesterov, Adam, RMSProp, AdaGrad — compare them { #q43 }

Plain SGD: `θ ← θ − η · g`.

| Optimizer | Update rule (simplified) | Key idea |
|---|---|---|
| **Momentum** | `v ← βv + g;  θ ← θ − η·v` | Remember past gradients; velocity through valleys |
| **Nesterov** | Momentum but look *ahead* first | Corrects oscillations better |
| **AdaGrad** | Per-parameter LR, decreasing with `Σg²` | Adapts to frequency of features |
| **RMSProp** | Like AdaGrad but **exponential average** of `g²` | Fixes AdaGrad's vanishing LR |
| **Adam** | Momentum + RMSProp + bias correction | Default for most deep learning |
| **AdamW** | Adam with **decoupled weight decay** | Default for transformers (Loshchilov & Hutter 2019) |

**When to pick which:**

- **Adam/AdamW** — safe default for nearly everything.
- **SGD + momentum** — still preferred for vision (ResNets, large ConvNets) where it often generalizes better.
- **LAMB / LARS** — massive batch sizes (BERT-scale pretraining).

**The Adam catch:**

Adam's adaptive learning rate can overfit in the final phase of training. Many papers use **Adam for the first half, then switch to SGD with a small LR**.

```python
import torch.optim as optim

# Standard transformer fine-tuning
optimizer = optim.AdamW(model.parameters(), lr=2e-5, weight_decay=0.01)

# CNN on vision data
optimizer = optim.SGD(model.parameters(), lr=0.1, momentum=0.9, weight_decay=5e-4)
```

---

## Q44. Learning-rate schedules — the most underrated hyperparameter { #q44 }

A single LR rarely works for the whole training. Schedules adjust it.

| Schedule | Behavior | Best for |
|---|---|---|
| **Step decay** | Drop by factor every N epochs | Simple, classic |
| **Exponential** | `η · γ^t` | Smooth decay |
| **Cosine annealing** | `η_min + ½(η_max − η_min)(1 + cos(π·t/T))` | Deep learning default |
| **Cosine with warm restarts** | Cosine, restart LR periodically | Escape local minima, strong results |
| **Warmup + cosine** | Linear ramp-up, then cosine | Transformers, large-batch |
| **One-cycle (Leslie Smith)** | Ramp up then down to near-zero | Fast convergence |
| **Reduce-on-plateau** | Drop when val metric stalls | Adaptive, good default |

**Warmup is critical for transformers** — without it, Adam's second moment (v) hasn't adapted, causing unstable gradient estimates early.

```python
from torch.optim.lr_scheduler import CosineAnnealingLR, OneCycleLR

# Cosine annealing
scheduler = CosineAnnealingLR(optimizer, T_max=num_epochs)

# One-cycle — often surprising gains
scheduler = OneCycleLR(optimizer, max_lr=1e-3,
                       steps_per_epoch=len(train_loader), epochs=num_epochs)

for epoch in range(num_epochs):
    for batch in train_loader:
        ...
        optimizer.step()
        scheduler.step()  # every step, not every epoch, for OneCycle
```

---

## Q45. Vanishing and exploding gradients { #q45 }

In deep networks, gradients backpropagate through many layers. Small gradients **multiply down to zero** (vanishing) — early layers don't learn. Large gradients **multiply up to infinity** (exploding) — weights blow up to NaN.

**Causes:**
- Sigmoid/tanh activations saturate → near-zero derivatives → vanishing.
- Deep architectures without skip connections.
- Poor weight initialization (too large → exploding; too small → vanishing).

**Solutions (all used together in modern nets):**
1. **ReLU family** — non-saturating derivative on positive side.
2. **Residual connections** — gradients flow through skips, bypassing chain multiplication.
3. **Batch/Layer normalization** — stabilizes activations throughout the network.
4. **Careful initialization** — Xavier/Glorot for sigmoid/tanh, He for ReLU.
5. **Gradient clipping** — `clip_grad_norm_(params, max_norm=1.0)` — caps exploding gradients in RNNs/transformers.

```python
# Gradient clipping — essential for RNNs and transformers
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
optimizer.step()
```

<div class="scenario" markdown>
**Your loss becomes NaN after a few batches. Walk through your debugging.**

**Answer:** (1) Check for NaN/inf in inputs (`torch.isnan(X).any()`). (2) Reduce learning rate by 10×. (3) Add gradient clipping. (4) Check for `log(0)` in the loss (add epsilon). (5) Check mixed-precision overflow — use `GradScaler`. (6) Inspect the last few gradients before NaN via hooks. (7) Verify targets are in the right range for your loss function.
</div>

---

## Q46. Weight initialization — why random isn't enough { #q46 }

**If you initialize all weights to zero:** every neuron computes the same thing, gradients are identical, no learning breaks symmetry.

**If you initialize too large:** activations explode, gradients explode.

**If you initialize too small:** activations vanish, gradients vanish.

**The Xavier/Glorot initialization (for sigmoid/tanh):**

```
W ~ N(0, 2 / (fan_in + fan_out))
```

Keeps variance constant across layers.

**He initialization (for ReLU):**

```
W ~ N(0, 2 / fan_in)
```

Accounts for ReLU zeroing out half the activations on average.

```python
import torch.nn as nn

# He initialization for ReLU-based nets
for m in model.modules():
    if isinstance(m, nn.Linear):
        nn.init.kaiming_normal_(m.weight, mode='fan_in', nonlinearity='relu')
        nn.init.zeros_(m.bias)
```

---

## Q47. Batch Normalization — what, why, and its quirks { #q47 }

**BatchNorm** normalizes activations across a batch for each feature/channel:

```
x̂ = (x − μ_batch) / √(σ²_batch + ε)
y  = γ · x̂ + β         # γ, β are learned
```

**Why it works (popular explanations):**

1. **Reduces internal covariate shift** (original Ioffe & Szegedy 2015 claim).
2. **Smooths the loss landscape** (Santurkar et al. 2018 — more accepted now).
3. **Enables higher learning rates** empirically.
4. **Acts as regularization** via batch-statistic noise.

**Its quirks:**

- **Train vs eval mode** — uses batch stats in train, running averages in eval. Forgetting `.eval()` is a classic bug.
- **Small batch sizes fail** — batch stats become unreliable. Use GroupNorm or LayerNorm instead.
- **Sequence data** — doesn't fit; use LayerNorm (used in transformers).

**LayerNorm vs BatchNorm:**

- BatchNorm normalizes across the batch dimension per feature.
- LayerNorm normalizes across the feature dimension per sample.
- LayerNorm is batch-size-independent → used in transformers.

```python
# PyTorch
nn.BatchNorm2d(num_features)   # CNN
nn.LayerNorm(hidden_dim)        # transformer
nn.GroupNorm(num_groups, num_channels)  # small-batch CNN
```

---

## Q48. Regularization — L1, L2, and the philosophy { #q48 }

Adding a penalty to the loss to discourage complex models:

```
L_total = L_data + λ · Ω(θ)
```

**L2 (Ridge):** `Ω = ||θ||²`

- Shrinks all weights toward zero, smoothly.
- Keeps all features — just with smaller coefficients.
- Corresponds to Gaussian prior on weights (Bayesian view).

**L1 (Lasso):** `Ω = ||θ||₁`

- Produces *sparse* solutions — many weights become exactly zero.
- Implicit feature selection.
- Corresponds to Laplace prior on weights.

**ElasticNet:** `α · ||θ||₁ + (1−α) · ||θ||²` — best of both.

**Why L1 sparsifies and L2 doesn't — the geometric intuition:**

L1's unit ball is a diamond (vertices at axes), so the loss contour touches it at corners → some weights = 0. L2's ball is smooth → touches at non-zero points.

```python
from sklearn.linear_model import Ridge, Lasso, ElasticNet

ridge = Ridge(alpha=1.0)        # L2
lasso = Lasso(alpha=0.01)       # L1 → sparse
enet  = ElasticNet(alpha=0.01, l1_ratio=0.5)
```

---

## Q49. Dropout — why randomly killing neurons helps { #q49 }

**What:** during training, zero out each neuron with probability `p`. At test time, use all neurons but scale by `(1 − p)`.

**Why it regularizes:**

1. **Prevents co-adaptation** — neurons can't rely on specific others being present.
2. **Ensemble interpretation** — training with dropout = training 2ⁿ thinned networks; test = averaging them (approximately).
3. **Stochastic regularization** — adds noise to activations.

**Where to apply:**
- Dense layers — yes, default p=0.5.
- Conv layers — usually no, or small p (~0.1). Spatial dropout works better.
- Recurrent layers — variational dropout (same mask across time).
- Transformers — yes, applied to attention and FFN (p=0.1 typical).

**Modern twist:** with batch norm + data augmentation, dropout is less critical in CNNs. Still core to transformers.

```python
nn.Sequential(
    nn.Linear(256, 128),
    nn.ReLU(),
    nn.Dropout(p=0.5),     # train: 50% zeroed; eval: all kept, no scaling needed (PyTorch handles)
    nn.Linear(128, 10)
)
```

---

## Q50. Early stopping — the simplest regularizer { #q50 }

**Rule:** monitor validation loss/metric each epoch. If it hasn't improved for `patience` epochs, stop training and restore the best weights.

**Why it works:** equivalent to L2 regularization for linear models (Yao et al. 2007). Early stopping keeps weights close to initialization.

```python
# PyTorch Lightning / custom
best_val = float('inf')
patience = 10
no_improve = 0
for epoch in range(max_epochs):
    val_loss = validate()
    if val_loss < best_val:
        best_val = val_loss
        torch.save(model.state_dict(), 'best.pt')
        no_improve = 0
    else:
        no_improve += 1
        if no_improve >= patience:
            break
model.load_state_dict(torch.load('best.pt'))
```

---

## Q51. Hyperparameter tuning — grid, random, Bayesian, population-based { #q51 }

| Method | How it works | When best |
|---|---|---|
| **Grid search** | Try every combination | ≤3 hyperparameters, cheap training |
| **Random search** | Sample uniformly from distributions | High-dim; beats grid empirically |
| **Bayesian (TPE, GP)** | Model the hyperparameter landscape | Expensive training (deep learning) |
| **Hyperband / BOHB** | Bandits + early stopping | Mixed: explore many, train few fully |
| **Population-Based Training** | Evolve a population of models | Online adaptation during long training |

**Why random beats grid (Bergstra & Bengio 2012):** only a few hyperparameters actually matter. Grid wastes budget on irrelevant axes; random spends evenly.

```python
import optuna

def objective(trial):
    params = {
        'learning_rate': trial.suggest_float('lr', 1e-5, 1e-1, log=True),
        'num_leaves':    trial.suggest_int('num_leaves', 10, 200),
        'feature_fraction': trial.suggest_float('feature_fraction', 0.5, 1.0),
        'min_data_in_leaf': trial.suggest_int('min_data_in_leaf', 5, 100),
    }
    model = lgb.LGBMClassifier(**params).fit(X_train, y_train)
    return roc_auc_score(y_val, model.predict_proba(X_val)[:, 1])

study = optuna.create_study(direction='maximize', pruner=optuna.pruners.MedianPruner())
study.optimize(objective, n_trials=100)
```

---

## Q52. Bagging vs Boosting vs Stacking { #q52 }

| Ensemble | How | Reduces | Example |
|---|---|---|---|
| **Bagging** | Train many models on bootstrap samples, average | Variance | Random Forest |
| **Boosting** | Train models sequentially, each fixing prior errors | Bias (and variance, with regularization) | XGBoost, LightGBM, CatBoost |
| **Stacking** | Train a meta-model on base-model predictions | Both (via diverse bases) | Competition winners |

**When to use which:**

- **Bagging/Random Forest** — baseline strong model, robust, handles noisy labels.
- **Boosting (GBM)** — highest accuracy on tabular data, the tabular king.
- **Stacking** — final % gains, Kaggle-style.

**The reason boosting dominates tabular:** iteratively fitting residuals is extremely sample-efficient when features are structured (the usual tabular case). Deep learning still hasn't reliably beaten GBM on typical tabular problems (Shwartz-Ziv & Armon 2022).

```python
# Stacking example
from sklearn.ensemble import StackingClassifier
from sklearn.linear_model import LogisticRegression

base_models = [
    ('rf',  RandomForestClassifier(n_estimators=200)),
    ('gbm', LGBMClassifier(n_estimators=500)),
    ('svm', SVC(probability=True))
]
meta = LogisticRegression()
stack = StackingClassifier(estimators=base_models, final_estimator=meta, cv=5)
stack.fit(X_train, y_train)
```

---

## Q53. Gradient boosting — how does it actually work? { #q53 }

**The idea:** build an ensemble where each new tree fits the **residuals** (errors) of the current ensemble.

**Step by step:**

1. Start with a simple prediction (e.g., mean of y).
2. Compute residuals: `r_i = y_i − ŷ_i`.
3. Fit a small decision tree to the residuals.
4. Add this tree (scaled by learning rate) to the ensemble.
5. Repeat for many iterations.

**XGBoost's twist:** uses second-order Taylor expansion of the loss → fits trees on both gradient AND Hessian. Plus level-wise tree growth, regularization, handling missing values natively.

**LightGBM's twist:** leaf-wise growth (grows the leaf with biggest loss reduction) → faster, but can overfit on small data.

**CatBoost's twist:** ordered boosting prevents target leakage when target-encoding categoricals on the fly.

**Key hyperparameters to tune:**

```python
lgb.LGBMClassifier(
    learning_rate=0.05,       # smaller = more trees needed but more accurate
    n_estimators=1000,         # use early stopping to pick real count
    max_depth=-1,              # -1 = unlimited; use num_leaves instead
    num_leaves=31,             # core complexity knob
    min_child_samples=20,      # min samples per leaf; regularization
    reg_alpha=0.1,             # L1
    reg_lambda=0.1,            # L2
    feature_fraction=0.8,      # column subsampling per tree (like RF)
    bagging_fraction=0.8,      # row subsampling per tree
    bagging_freq=5
)
```

---

## Q54. Loss functions — how to pick the right one { #q54 }

**Classification:**
- **Binary cross-entropy** — default for binary.
- **Categorical cross-entropy** — multi-class with one-hot.
- **Sparse categorical cross-entropy** — multi-class with integer labels.
- **Focal loss** — extreme imbalance; down-weights easy examples.
- **Hinge loss** — SVMs; max-margin.
- **Label smoothing cross-entropy** — prevents overconfidence.

**Regression:**
- **MSE** — standard; penalizes large errors heavily.
- **MAE** — robust to outliers.
- **Huber** — quadratic near zero, linear far; balance.
- **Quantile loss** — predict a quantile (used for prediction intervals).
- **Log-cosh** — smooth, behaves like MAE for large errors.

**Ranking:**
- **Pairwise hinge / logistic** — learning-to-rank.
- **ListMLE, ListNet** — listwise.
- **NDCG-optimization** — direct ranking metric.

**Custom losses:** you can (and should) match loss to your business objective. If false positives cost 10× false negatives, use a weighted loss.

---

## Q55. Debugging a training run — your systematic checklist { #q55 }

If training isn't working, go through these in order:

1. **Overfit a tiny batch.** Can you get near-zero loss on 10 samples? If no, you have a code bug.
2. **Check data pipeline.** Visualize 20 samples from your training loader. Do they look right? Labels correct?
3. **Check initialization.** Activations should be well-distributed, not all zero or saturated.
4. **Check loss.** Initial loss should be `log(num_classes)` for cross-entropy. Way off? Check loss function.
5. **Scale inputs.** Unscaled inputs cause slow/unstable training.
6. **Reduce LR by 10×.** Most training instability is LR.
7. **Add gradient clipping.** `max_norm=1.0`.
8. **Disable dropout/BN temporarily.** Separate concerns.
9. **Remove augmentation.** See if model can learn raw data.
10. **Simplify architecture.** If deep net fails, try shallow; if fancy, try vanilla.
11. **Check gradient flow.** `param.grad.abs().mean()` per layer.
12. **Monitor loss vs steps, not epochs.** Early signals are at the step level.

!!! tip "Karpathy's recipe"
    Andrej Karpathy's "A Recipe for Training Neural Networks" (blog, 2019) is required reading. TL;DR: start small, verify each step, only then scale up.

---

**Module complete.** Next → [4. Bias, Variance & Regularization →](bias-variance.md)
