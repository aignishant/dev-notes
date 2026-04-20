# 4. Bias, Variance & Regularization

> **Module goal:** If you understand bias-variance intuitively, you can diagnose any struggling model in seconds. This module is short but dense — every question here is asked in 90% of ML interviews.

---

## Q56. The bias-variance decomposition — derive it { #q56 }

For a regression problem with true function `f(x)`, noisy label `y = f(x) + ε` (where `ε` is zero-mean noise with variance `σ²`), and model prediction `ĥ(x)` learned from training data:

$$
\mathbb{E}[(y - \hat{h}(x))^2] = \underbrace{(\mathbb{E}[\hat{h}(x)] - f(x))^2}_{\text{Bias}^2} + \underbrace{\mathbb{E}[(\hat{h}(x) - \mathbb{E}[\hat{h}(x)])^2]}_{\text{Variance}} + \underbrace{\sigma^2}_{\text{Irreducible}}
$$

**In words:**

- **Bias²** — how wrong is the model's *average* prediction vs the truth? (Systematic error.)
- **Variance** — how much do predictions change if we re-train on different data from the same distribution? (Sensitivity.)
- **Irreducible noise** — label noise you can never fix with any model.

**The dart-board mental picture:**

| Bias | Variance | Picture |
|---|---|---|
| Low | Low | Tight cluster at bullseye — ideal |
| High | Low | Tight cluster, but in the wrong spot — underfit |
| Low | High | Scattered around bullseye — overfit |
| High | High | Scattered AND off-center — bad model, bad data |

---

## Q57. Underfitting vs Overfitting — symptoms and cures { #q57 }

| Symptom | Underfit | Overfit |
|---|---|---|
| Train error | High | Very low |
| Val error | High | Much higher than train |
| Train-val gap | Small | Large |
| Fix direction | Increase capacity, richer features | Decrease capacity, add regularization, more data |

**Underfit cures:**
- Use a more expressive model.
- Add features / interaction terms.
- Reduce regularization.
- Train longer.
- Reduce LR (if it's oscillating and not improving).

**Overfit cures:**
- More training data (always helps, rarely possible).
- Regularization (L1/L2, dropout).
- Data augmentation.
- Early stopping.
- Simpler model.
- Feature selection.
- Ensemble via bagging.

<div class="scenario" markdown>
**Train accuracy 99%, val accuracy 72%. Diagnose and fix.**

**Answer:** Textbook overfitting — 27% gap. (1) Add regularization (L2=0.01, try L1 if many irrelevant features). (2) Reduce model capacity or add dropout. (3) Augment data. (4) Check for data leakage in training (too-good-to-be-true on train is a leakage tell). (5) Collect more data if possible. (6) Use cross-validation to verify — if CV folds show similar gap, it's overfit; if gaps vary wildly, it could be a small val set or unlucky split.
</div>

---

## Q58. Regularization — all techniques in one place { #q58 }

**Explicit regularization** (add penalty to loss):

- **L1 / Lasso** — sparsity, implicit feature selection.
- **L2 / Ridge** — shrinkage, handles multicollinearity.
- **Elastic Net** — combination.
- **Label smoothing** — prevents confident wrong predictions.

**Implicit regularization** (properties of training):

- **Early stopping.**
- **SGD noise** — implicit bias toward flat minima.
- **Dropout.**
- **Batch normalization** — small regularization from batch-stat noise.
- **Data augmentation.**

**Architectural regularization:**

- **Weight sharing** (CNNs, transformers) — drastically fewer params.
- **Pooling** — enforces local invariance.
- **Parameter tying.**

!!! tip "Which one to reach for first"
    In deep learning, try **data augmentation + early stopping + weight decay** before anything exotic. That trio solves 90% of overfitting.

---

## Q59. Learning curves — how to read them { #q59 }

Plot training and validation error (or loss) vs training set size or training time.

**Pattern → diagnosis:**

| Pattern | Diagnosis | Action |
|---|---|---|
| Both curves high, close together, plateau | High bias | More capacity / features |
| Train curve low, val curve high, large gap | High variance | More data / regularization |
| Both high, large gap | Both high bias & variance | Rethink model |
| Both low, close together | Good fit | Ship it |

```python
from sklearn.model_selection import learning_curve
import matplotlib.pyplot as plt

sizes, train_scores, val_scores = learning_curve(
    model, X, y, cv=5, train_sizes=np.linspace(0.1, 1.0, 10),
    scoring='neg_mean_squared_error'
)

plt.plot(sizes, -train_scores.mean(axis=1), label='train')
plt.plot(sizes, -val_scores.mean(axis=1), label='val')
plt.xlabel('Training set size'); plt.ylabel('MSE'); plt.legend()
```

**The key question a learning curve answers:** will more data help? If the val curve is still decreasing, yes. If it has plateaued, no — you're capacity-limited.

---

## Q60. Why does cross-validation work? { #q60 }

A single train/val split gives you *one* estimate of generalization error — and it's noisy (depends on which samples landed in val).

**k-fold CV** reduces that variance by averaging k estimates. Each fold serves as val once. You get:

- **Better estimate** of expected error.
- **Standard deviation** across folds → error bars.
- **More training data usage** (each sample appears in k-1 training folds).

**Tradeoff:** k-fold CV trains `k` models. Time-expensive for large models. That's why deep learning often skips CV and relies on a single held-out val set.

---

## Q61. When is k-fold CV a bad idea? { #q61 }

1. **Time series** — random k-fold uses future data to predict past. Use `TimeSeriesSplit`.
2. **Grouped data** — same patient/user in train and val = leakage. Use `GroupKFold`.
3. **Extreme class imbalance with small k** — some folds may have no positives. Use `StratifiedKFold` with larger k, or repeated stratified CV.
4. **Huge datasets + deep learning** — CV cost is prohibitive; single held-out val is fine.
5. **Dependent samples** (e.g., geography where nearby points correlate) — spatial or block CV.

---

## Q62. L1 vs L2 — the coefficient story { #q62 }

**Visualize the constrained optimization:**

L1 constraint = diamond; L2 constraint = circle. Loss level sets are ellipses. Where the ellipse first touches the constraint:

- **L1** — most often touches at a corner (where some coordinates are zero) → sparse.
- **L2** — touches at a generic point → no coordinates exactly zero, but all shrunk.

**Practical implications:**

| Property | L1 | L2 |
|---|---|---|
| Sparsity | Yes — zeros out features | No — just shrinks |
| Feature selection | Yes | No |
| Grouped features (correlated) | Picks one arbitrarily | Spreads weight across them |
| Convex but non-smooth | Yes — needs subgradient methods | Yes and smooth — closed-form solution |
| Use when | Many irrelevant features | Many relevant, correlated features |

**Elastic Net** combines both: L1 for selection + L2 for stability on correlated groups.

---

## Q63. How to diagnose high bias specifically { #q63 }

**Signals:**
- Train error is high (not just val error).
- Adding data doesn't help — validation curve has plateaued parallel to train.
- Simple model on your problem beats your complex model (unusual).

**Actions:**
1. Increase model capacity (deeper net, more trees, larger embedding dim).
2. Train longer.
3. Reduce regularization.
4. Add richer features or interaction terms.
5. Use a better architecture matched to the data (CNN for images, not MLP).

---

## Q64. How to diagnose high variance specifically { #q64 }

**Signals:**
- Train accuracy is excellent, val accuracy is much worse.
- Performance varies a lot across CV folds.
- Removing a few training samples changes predictions significantly.

**Actions:**
1. Collect more training data (most powerful fix).
2. Add regularization.
3. Use a simpler model.
4. Data augmentation.
5. Bagging / ensembling.
6. Feature selection — drop irrelevant features that the model is fitting noise in.

---

## Q65. When will more data help? When won't it? { #q65 }

**More data helps when variance dominates:** the model is overfitting. More samples stabilize the estimate of the true function.

**More data doesn't help when bias dominates:** the model is too simple. It'll underfit on 1K samples and still underfit on 1M samples.

**Rule of thumb:** if the train-val gap is small AND error is high, bias is your problem → upgrade the model. If the gap is large, data will help.

**Data quality > quantity:** cleaner labels on 10K samples often beat noisy labels on 1M. Especially for label-noise-sensitive losses like cross-entropy.

---

## Q66. Why does dropout work — three competing explanations { #q66 }

1. **Ensemble view (Hinton et al.):** training with dropout p trains 2ⁿ different subnetworks. Test-time = averaging them via weight scaling.

2. **Co-adaptation prevention:** neurons cannot rely on specific neighbors being present → develop robust features.

3. **Stochastic regularization noise:** dropout is equivalent to adding multiplicative noise to activations, which is a form of regularization (similar in spirit to Bayesian weight uncertainty).

All three are partially true; no single theory fully explains it.

---

## Q67. Label smoothing — the "don't be too confident" regularizer { #q67 }

Standard cross-entropy pushes softmax outputs toward pure 0/1. Label smoothing replaces the target:

- Instead of `[0, 1, 0, 0]` → use `[ε/K, 1−ε+ε/K, ε/K, ε/K]` with small ε (e.g., 0.1).

**Effects:**

- Prevents the model from becoming overconfident (logits stay bounded).
- Improves calibration.
- Acts as mild regularization.
- Often gives a small bump in test accuracy.

Used in Inception-v3, transformers, GPT training.

```python
# PyTorch supports label smoothing natively
criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
```

---

## Q68. Regularization effect of data augmentation { #q68 }

Data augmentation is a form of regularization — it forces the model to be invariant to the applied transformations.

- Flipping images → model learns that horizontal orientation doesn't matter.
- Cropping → model learns shift invariance.
- Color jitter → color invariance.

**This is regularization by prior knowledge** — you're telling the model what transformations shouldn't change the label.

**Modern techniques to know:**

- **Mixup** — linear interpolation of two samples AND their labels.
- **CutMix** — paste a patch from one image into another; mix labels proportionally.
- **RandAugment / AutoAugment** — automated search for augmentation policies.
- **TrivialAugment** — surprisingly simple, often beats the complex ones.

---

## Q69. The double descent phenomenon — why classic bias-variance is incomplete { #q69 }

Classic theory: as capacity grows, test error follows a U-curve — decreases (bias drops) then increases (variance explodes).

**Modern empirical fact (Belkin et al. 2019, Nakkiran et al. 2020):** with very high capacity (modern deep nets), test error goes **down → up → down again**. The second descent happens after the "interpolation threshold" where the model perfectly fits the training set.

**Implications:**

- Bigger models can be better, not worse, even past the interpolation threshold.
- Explains why 175B-parameter LLMs generalize better than 1B models, not worse.
- Implicit regularization from SGD + architecture is doing more than classical theory captures.

**Interview use:** when asked "don't bigger models overfit?", cite double descent as the reason modern best practice doesn't match the U-curve story.

---

## Q70. Calibration — when probabilities aren't really probabilities { #q70 }

A calibrated model's predicted probability matches empirical frequency: if it says "70% chance of rain," it actually rains ~70% of the time.

**Why it matters:** decisions often depend on probabilities (cost-benefit thresholds, risk-weighted actions). A miscalibrated model gives unreliable confidence.

**Measure:** reliability diagram, Expected Calibration Error (ECE), Brier score.

```python
from sklearn.calibration import calibration_curve, CalibratedClassifierCV

# Plot reliability diagram
probs = model.predict_proba(X_val)[:, 1]
frac_pos, mean_pred = calibration_curve(y_val, probs, n_bins=10)

# Fix calibration — Platt scaling (sigmoid) or isotonic
calibrated = CalibratedClassifierCV(model, method='isotonic', cv=5)
calibrated.fit(X_train, y_train)
```

**Model calibration profile:**

- **Logistic regression** — well calibrated out of the box.
- **Random forests, boosted trees** — often overconfident near 0 and 1.
- **Deep neural nets with modern architectures** — typically overconfident (label smoothing helps).
- **SVM** — outputs not probabilities at all; use Platt scaling.

---

**Module complete.** Next → [5. Evaluation Metrics →](metrics.md)
