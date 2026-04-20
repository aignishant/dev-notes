# Module 3 — Kernels & SVM

**Questions 36–50.** SVM is less popular in modern production, but it's heavily tested for two reasons: (1) it forces you to demonstrate mathematical maturity (duality, kernels, margin theory), and (2) it's still the right answer for specific problems — small datasets, high-dimensional sparse features, anomaly detection.

---

## Q36. Derive the primal SVM objective. Why is the margin 2/‖w‖? { #q36 }

**Setup.** Linearly separable data, labels `y_i ∈ {-1, +1}`. We want a hyperplane `w·x + b = 0` that separates classes with maximum margin.

**Decision rule:** `sign(w·x + b)`.

**Margin geometry.** The hyperplane's distance from a point `x` is `|w·x + b| / ‖w‖`. We choose `w, b` such that for the closest points (support vectors): `w·x + b = ±1`.

With this normalization, the margin between the two supporting hyperplanes is:

\[
\text{margin} = \frac{2}{\|w\|}
\]

**Maximizing 2/‖w‖ ↔ minimizing ‖w‖² / 2.**

**Primal objective (hard margin):**

\[
\min_{w, b} \frac{1}{2} \|w\|^2 \quad \text{subject to} \quad y_i (w \cdot x_i + b) \geq 1 \quad \forall i
\]

**Soft margin** (allows violations via slack `ξ_i`):

\[
\min_{w, b, \xi} \frac{1}{2} \|w\|^2 + C \sum_i \xi_i \quad \text{subject to} \quad y_i (w \cdot x_i + b) \geq 1 - \xi_i, \; \xi_i \geq 0
\]

`C` is the regularization parameter — high C means less tolerance for violations.

```python
from sklearn.svm import LinearSVC

svm = LinearSVC(C=1.0, loss='hinge', max_iter=10000)
svm.fit(X_train, y_train)
```

<div class="tip-box" markdown>
**Interviewer probe:** "Why is the constraint `y_i (w·x_i + b) ≥ 1` and not `≥ 0`?" — answer: any positive constant works; `1` is just a scaling choice. By setting it to 1, the margin becomes `2/‖w‖`, giving a clean optimization.
</div>

---

## Q37. Why the dual form? Derive it. { #q37 }

**Motivation.** Two reasons to solve the dual:

1. The dual depends only on **inner products** `x_i · x_j`, enabling the kernel trick.
2. The dual is a **quadratic program** in `n` variables (one per sample), solvable with specialized QP solvers.

**Lagrangian:**

\[
L(w, b, \alpha) = \frac{1}{2}\|w\|^2 - \sum_i \alpha_i [y_i(w \cdot x_i + b) - 1], \quad \alpha_i \geq 0
\]

Setting gradients to zero:

\[
\frac{\partial L}{\partial w} = 0 \implies w = \sum_i \alpha_i y_i x_i
\]

\[
\frac{\partial L}{\partial b} = 0 \implies \sum_i \alpha_i y_i = 0
\]

Substitute back:

\[
\max_\alpha \sum_i \alpha_i - \frac{1}{2} \sum_{i,j} \alpha_i \alpha_j y_i y_j (x_i \cdot x_j)
\]

\[
\text{s.t.} \quad \alpha_i \geq 0, \quad \sum_i \alpha_i y_i = 0
\]

**Soft-margin dual:** same objective, but with constraint `0 ≤ α_i ≤ C`.

**KKT conditions identify support vectors:**

- `α_i = 0` → point is correctly classified and beyond the margin (non-support).
- `0 < α_i < C` → point is on the margin (support vector).
- `α_i = C` → point is inside the margin or misclassified.

**Prediction:**

\[
f(x) = \text{sign}\left( \sum_i \alpha_i y_i (x_i \cdot x) + b \right)
\]

Only support vectors contribute — the rest have `α_i = 0`.

---

## Q38. Explain the kernel trick. What makes a valid kernel? { #q38 }

**The idea.** Map data into a high-dimensional feature space via `φ(x)`, but never compute `φ(x)` explicitly. Just need `K(x_i, x_j) = φ(x_i) · φ(x_j)`.

**Example — polynomial kernel of degree 2:**

\[
K(x, z) = (x \cdot z + 1)^2
\]

For 2D input `x = (x_1, x_2)`, this corresponds to mapping:

\[
\phi(x) = (1, \sqrt{2}x_1, \sqrt{2}x_2, x_1^2, x_2^2, \sqrt{2}x_1 x_2)
\]

You get the inner product in this 6D space by computing a 2D inner product and squaring — O(d) instead of O(d²).

**Mercer's theorem.** `K` is a valid kernel iff it's:

1. **Symmetric:** `K(x, z) = K(z, x)`.
2. **Positive semi-definite:** for any set of points, the Gram matrix `[K(x_i, x_j)]` has non-negative eigenvalues.

**Standard kernels in sklearn:**

| Kernel | Formula | Intuition |
|---|---|---|
| **Linear** | `x · z` | No mapping |
| **Polynomial** | `(γ x·z + r)^d` | Feature interactions up to degree d |
| **RBF / Gaussian** | `exp(-γ‖x-z‖²)` | Infinite-dimensional — similarity based on distance |
| **Sigmoid** | `tanh(γ x·z + r)` | Similar to neural net, not always PSD |

```python
from sklearn.svm import SVC

# Try different kernels
for kernel in ['linear', 'poly', 'rbf']:
    svm = SVC(kernel=kernel, C=1.0, gamma='scale')
    svm.fit(X_train, y_train)
    print(f"{kernel}: {svm.score(X_test, y_test):.3f}")
```

<div class="tip-box" markdown>
**Senior signal:** "RBF is a universal approximator on compact sets — it can fit anything given enough training data. That's its blessing and curse — γ tuning is critical to avoid overfitting."
</div>

---

## Q39. What do C and γ control in RBF SVM? How do you tune them? { #q39 }

**C (regularization):**

- **Low C** (e.g., 0.01): large margin, tolerant of misclassifications → underfits.
- **High C** (e.g., 1000): small margin, penalizes any error heavily → overfits.

**γ (RBF bandwidth):**

- **Low γ** (e.g., 0.001): broad Gaussian, smooth decision boundary → underfits.
- **High γ** (e.g., 100): narrow Gaussian, each point only influences nearby region → overfits, essentially memorizes training set.

**Visual intuition:** γ controls the "radius of influence" of each support vector. Low γ → support vectors influence distant regions. High γ → only immediate neighbors.

**Tuning:**

```python
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV

param_grid = {
    'C': [0.1, 1, 10, 100],
    'gamma': ['scale', 0.001, 0.01, 0.1, 1.0],
}
grid = GridSearchCV(SVC(kernel='rbf'), param_grid, cv=5, n_jobs=-1)
grid.fit(X_train, y_train)
print(grid.best_params_)
```

**Default `gamma='scale'`** uses `1 / (n_features × X.var())` — a reasonable starting point that depends on data scale.

<div class="scenario" markdown>
**Watch out:** SVM is sensitive to feature scaling. Always `StandardScaler` before fitting. Without scaling, features with large magnitudes dominate the distance computation and γ tuning becomes almost meaningless.
</div>

---

## Q40. Why does SVM scale poorly to large datasets? What's the fix? { #q40 }

**Training complexity of kernel SVM:** between O(n²) and O(n³) depending on solver.

**Why:** the dual has n variables (one `α_i` per sample), and the constraint matrix is O(n²) in memory.

**Practical cutoff:** ~100,000 samples. Beyond that, SVM becomes infeasible.

**Fixes:**

**1. LinearSVC** — for linear kernel only. Uses liblinear, O(n) per iteration. Handles millions of samples.

```python
from sklearn.svm import LinearSVC

# Equivalent to SVC(kernel='linear') but much faster
lsvc = LinearSVC(C=1.0, loss='hinge', max_iter=10000)
lsvc.fit(X_train, y_train)
```

**2. SGDClassifier** with hinge loss — SGD-based linear SVM. Streams over data.

```python
from sklearn.linear_model import SGDClassifier

svm_sgd = SGDClassifier(loss='hinge', alpha=1e-4, max_iter=50)
svm_sgd.fit(X_train, y_train)
```

**3. Nystroem approximation** — approximates RBF kernel with explicit low-rank features, then uses linear SVM.

```python
from sklearn.kernel_approximation import Nystroem
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ('feature_map', Nystroem(kernel='rbf', n_components=300, gamma=0.1)),
    ('svm', LinearSVC(C=1.0)),
])
pipe.fit(X_train, y_train)
# Scales to millions of rows with near-RBF-SVM accuracy
```

**4. RFF (Random Fourier Features)** — similar idea, theoretically justified by Bochner's theorem.

```python
from sklearn.kernel_approximation import RBFSampler

rff = RBFSampler(gamma=0.1, n_components=300, random_state=42)
X_rff = rff.fit_transform(X_train)
lsvc = LinearSVC().fit(X_rff, y_train)
```

---

## Q41. When is SVM the right choice in 2026? { #q41 }

**Use SVM when:**

1. **Small data, high dimensions** — `n < 10,000`, `p > n`. Text classification (TF-IDF features), some bioinformatics. SVM's margin bias prevents overfitting when gradient boosting would overfit.
2. **Need hard margin or specific kernel prior** — physics-informed ML or one-class SVM for anomaly detection.
3. **Baseline for paper / research** — common comparison baseline in ML publications.
4. **Interpretable similarity-based reasoning** — "this prediction is based on these 10 support vectors that look like the test point."

**Don't use SVM when:**

1. **Data > 100K rows** — training is prohibitive. Use GBM or neural net.
2. **Need probability calibration** — SVM outputs distances, not probabilities. Platt scaling is a hack.
3. **Mixed feature types (numeric + categorical)** — RBF assumes Euclidean geometry; doesn't respect categorical boundaries.
4. **Heavy imbalance** — SVM's margin treats all classes equally; class weights help but can distort.
5. **Production latency is tight** — SVM inference is O(num_SV × d), which can be slow if you have many support vectors.

<div class="tip-box" markdown>
**Honest answer for interviews:** "For most tabular problems in 2026, I'd start with LightGBM. SVM is my go-to for (1) high-dimensional sparse data like text, where linear SVM is hard to beat, and (2) one-class SVM for anomaly detection with limited labels."
</div>

---

## Q42. Hinge loss — derive it and explain vs log loss. { #q42 }

**Hinge loss:**

\[
L_{hinge}(y, f(x)) = \max(0, 1 - y f(x))
\]

where `y ∈ {-1, +1}` and `f(x) = w·x + b`.

**Intuition:** no penalty if the point is correctly classified with margin ≥ 1. Linear penalty for being inside the margin or misclassified.

**Gradient:**

\[
\frac{\partial L}{\partial w} = \begin{cases} -y x & \text{if } y f(x) < 1 \\ 0 & \text{otherwise} \end{cases}
\]

This is non-differentiable at `y f(x) = 1` (the hinge) — use subgradients for SGD.

**Hinge vs log loss:**

| Property | Hinge | Log Loss |
|---|---|---|
| Formula | `max(0, 1 - y f)` | `log(1 + exp(-y f))` |
| Smoothness | Kink at 1 | Smooth everywhere |
| Behavior when correct | Zero penalty beyond margin | Small but nonzero penalty |
| Produces probabilities | No | Yes (via sigmoid) |
| Gradient for correct predictions | Zero | Small but nonzero |
| Robust to outliers | Relatively | Less so |

**Consequence:** hinge is "sparse" — only support vectors contribute to updates. Log loss updates every sample, no matter how confident.

```python
import numpy as np
import matplotlib.pyplot as plt

margin = np.linspace(-2, 3, 100)
hinge = np.maximum(0, 1 - margin)
logistic = np.log(1 + np.exp(-margin)) / np.log(2)  # normalize to same scale

plt.plot(margin, hinge, label='Hinge')
plt.plot(margin, logistic, label='Log loss (scaled)')
plt.axvline(1, linestyle='--', alpha=0.5)
plt.xlabel('y·f(x)')
plt.ylabel('Loss')
```

---

## Q43. What's one-class SVM and when would you use it? { #q43 }

**Setting.** You have only "normal" examples; no anomaly labels. Goal: learn a boundary enclosing the normal data, flag outliers at test time.

**Formulation (Schölkopf et al. 2001):**

Instead of separating two classes, separate data from the origin in feature space:

\[
\min_{w, \xi, \rho} \frac{1}{2} \|w\|^2 + \frac{1}{\nu n} \sum_i \xi_i - \rho
\]

\[
\text{s.t.} \quad w \cdot \phi(x_i) \geq \rho - \xi_i, \quad \xi_i \geq 0
\]

- `ν` is an upper bound on the fraction of outliers (also a lower bound on support vectors).
- `ρ` is the offset of the decision boundary from origin.

**Output:** `f(x) = w·φ(x) - ρ`. Positive = inlier, negative = outlier.

**When to use:**

- Anomaly detection with pure normal data.
- Medium-dimensional (dozens to hundreds of features).
- Small data (< 50K normal samples).

```python
from sklearn.svm import OneClassSVM

# Train on normal data only
ocsvm = OneClassSVM(
    nu=0.05,           # expected outlier fraction
    kernel='rbf',
    gamma='scale',
)
ocsvm.fit(X_normal)

# Predict on mixed data
anomaly_score = ocsvm.decision_function(X_test)
is_outlier = ocsvm.predict(X_test) == -1
```

**Alternatives:**

- **Isolation Forest** — usually faster, scales better.
- **LOF (Local Outlier Factor)** — local density-based, handles varying density better.
- **Autoencoder reconstruction error** — for high-dimensional data.

<div class="scenario" markdown>
**Real use case:** network intrusion detection. Trained on 10 days of normal traffic, One-Class SVM flags anomalies in real-time. Works well because normal traffic has stable patterns; attacks deviate sharply.
</div>

---

## Q44. What's Support Vector Regression (SVR)? How does it differ from classification SVM? { #q44 }

**SVR objective:**

\[
\min_{w, b} \frac{1}{2} \|w\|^2 + C \sum_i (\xi_i + \xi_i^*)
\]

\[
\text{s.t.} \quad y_i - (w \cdot x_i + b) \leq \epsilon + \xi_i
\]

\[
(w \cdot x_i + b) - y_i \leq \epsilon + \xi_i^*
\]

**Key idea: ε-insensitive loss.** Predictions within ε of the true target incur no penalty. Only errors larger than ε contribute.

**Compare to Huber loss:** both are robust, but SVR is sparse (points within the ε-tube have zero loss) while Huber penalizes all errors.

**Implications:**

- **Sparse solution** — only points outside the tube become support vectors.
- **Robust to outliers** — extreme values contribute linearly (not quadratically).
- **Additional hyperparameter** — `ε` controls fit-quality/sparsity tradeoff.

```python
from sklearn.svm import SVR

svr = SVR(
    kernel='rbf',
    C=1.0,
    epsilon=0.1,         # tube width
    gamma='scale',
)
svr.fit(X_train, y_train)
```

<div class="tip-box" markdown>
**Interviewer probe:** "When would you choose SVR over Ridge?" — "When the data has heavy-tailed noise and I want robustness. Ridge will be pulled by outliers; SVR ignores errors inside the ε-tube."
</div>

---

## Q45. Explain the intuition for why high-dimensional data can be linearly separable. { #q45 }

**Claim:** in sufficiently high dimensions, randomly labeled data often becomes linearly separable.

**Cover's theorem (1965):** the number of dichotomies of `n` points in `d` dimensions that are linearly separable is:

\[
C(n, d) = 2 \sum_{k=0}^{d-1} \binom{n-1}{k}
\]

When `d ≥ n - 1`, *all* dichotomies are linearly separable — any labeling works.

**Practical consequence for SVM:**

- In high-dim (text: 100K features), linear SVM almost always finds a separating hyperplane.
- That's both why SVM is great on text (good baseline) and risky (easy to overfit).

**Why kernels work:** implicitly projecting to higher dimensions makes the data linearly separable. RBF projects to infinite dimensions — for any finite data, RBF SVM can perfectly separate it (with γ tuned right).

**The catch:** linear separability on training ≠ generalization. That's why regularization (`C`, margin maximization) matters so much.

<div class="scenario" markdown>
**Real anecdote:** text classification with 200K TF-IDF features, 5K documents. Linear SVM achieves 100% training accuracy easily. Proper CV reveals the generalization gap — tune C via CV, not training accuracy.
</div>

---

## Q46. Why is SVM less probabilistic than logistic regression? How do you fix that? { #q46 }

**Issue.** SVM outputs a signed distance to the hyperplane. That's not a probability.

**Platt scaling (Platt 1999).** Fit a sigmoid on top of SVM scores:

\[
P(y=1 | f) = \frac{1}{1 + \exp(A f + B)}
\]

`A, B` fit by minimizing log-loss on held-out data.

**How sklearn does it:**

```python
from sklearn.svm import SVC

svm = SVC(kernel='rbf', probability=True)  # enables Platt scaling
svm.fit(X_train, y_train)
probs = svm.predict_proba(X_test)
# Warning: probability=True triggers 5-fold CV internally — training is 5x slower
```

**Alternative: isotonic regression** — non-parametric calibration.

```python
from sklearn.calibration import CalibratedClassifierCV

svm_base = SVC(kernel='rbf')  # no probability=True
calibrated = CalibratedClassifierCV(svm_base, method='isotonic', cv=5)
calibrated.fit(X_train, y_train)
probs = calibrated.predict_proba(X_test)
```

<div class="tip-box" markdown>
**Senior signal:** "Platt scaling works when there are few samples near the boundary; isotonic works when you have enough data (≥ 1000) and miscalibration isn't sigmoidal."
</div>

---

## Q47. What's multi-class SVM? One-vs-rest vs one-vs-one. { #q47 }

SVM is fundamentally binary. Multi-class extensions:

**One-vs-Rest (OvR).**

Train `K` classifiers, each separates class `k` from all others. Predict argmax.

- **Pros:** K models, simpler.
- **Cons:** class imbalance per model (1 vs K-1), calibration issues when merging scores.

**One-vs-One (OvO).**

Train `K(K-1)/2` classifiers, each for a pair of classes. Predict via majority vote.

- **Pros:** each model trains on balanced subset, more accurate.
- **Cons:** K² models → expensive for many classes.

**Crammer-Singer (native multi-class).**

Solve one joint optimization:

\[
\min \sum_k \|w_k\|^2 + C \sum_i \max_{k \neq y_i} \max(0, 1 + w_k \cdot x_i - w_{y_i} \cdot x_i)
\]

- **Pros:** theoretically cleaner, no merging heuristic.
- **Cons:** supported by few libraries (not sklearn's `SVC`).

**Practical:** sklearn's `SVC` defaults to **OvO**. `LinearSVC` uses **OvR**. For most problems, they differ by < 1%.

```python
from sklearn.svm import SVC

# OvO (default for SVC)
svm_ovo = SVC(decision_function_shape='ovo')

# OvR
svm_ovr = SVC(decision_function_shape='ovr')

# LinearSVC default is OvR
from sklearn.svm import LinearSVC
linear_ovr = LinearSVC(multi_class='ovr')
```

---

## Q48. SVM for imbalanced classes — what's the right strategy? { #q48 }

**The problem.** Vanilla SVM maximizes margin globally; with 99:1 imbalance, the optimal margin often misclassifies all minority.

**Three fixes:**

**1. Class weights (`class_weight='balanced'`).**

sklearn automatically weights classes inversely to their frequency:

```python
from sklearn.svm import SVC

svm = SVC(kernel='rbf', class_weight='balanced')
# Equivalent to C_0 = C × N / (2 × N_0), C_1 = C × N / (2 × N_1)
```

**2. Explicit weights per class.**

```python
svm = SVC(class_weight={0: 1, 1: 10})  # minority gets 10x weight
```

**3. Tune threshold after fitting.**

```python
# Train with default, adjust threshold on validation
probs = svm.decision_function(X_val)  # distance from hyperplane

# Find threshold that maximizes F1
from sklearn.metrics import f1_score
import numpy as np

thresholds = np.linspace(probs.min(), probs.max(), 100)
scores = [f1_score(y_val, probs > t) for t in thresholds]
best_threshold = thresholds[np.argmax(scores)]
```

<div class="tip-box" markdown>
**Pragmatic note:** for extreme imbalance (fraud at 0.1%), SVM rarely competes with gradient boosting. The margin maximization is fighting too hard against the imbalance.
</div>

---

## Q49. How does SVM relate to logistic regression mathematically? { #q49 }

Both are linear classifiers minimizing a convex loss + regularization. They differ only in the loss function:

| | Logistic Regression | SVM |
|---|---|---|
| Loss | `log(1 + exp(-y f))` | `max(0, 1 - y f)` |
| Regularization | L2 or L1 | L2 (via ‖w‖²) |
| Outputs | Probabilities | Signed distances |
| Support vectors | None (all points contribute) | Few (margin violators) |

**In the limit of large regularization** (`C → 0`), both converge to similar solutions.

**In the limit of small regularization** (`C → ∞`):

- Logistic regression overfits smoothly.
- SVM gets dominated by outliers (slack variables grow).

**Empirical findings:**

- On balanced, clean tabular data: within ~1% of each other.
- With severe outliers: SVM more robust (hinge loss is linear beyond margin, log loss is sub-linear but every point contributes).
- For probabilistic output: logistic regression natively, SVM needs calibration.

<div class="scenario" markdown>
**Question frame:** "You're deciding between SVM and logistic regression for a text classifier" — rephrase: they're nearly equivalent linear models; the real choice is loss function (hinge vs log) and calibration needs. For most text problems, both are fine; logistic is more ergonomic for probabilities.
</div>

---

## Q50. Explain why RBF kernel corresponds to an infinite-dimensional feature space. { #q50 }

**Claim.** `K(x, z) = exp(-γ‖x - z‖²)` corresponds to `K(x, z) = φ(x) · φ(z)` where `φ` maps into an infinite-dimensional Hilbert space.

**Sketch of proof.** Write the Gaussian kernel as a Taylor expansion:

\[
\exp(-\gamma \|x - z\|^2) = \exp(-\gamma \|x\|^2) \exp(-\gamma \|z\|^2) \exp(2\gamma x \cdot z)
\]

The last factor expands:

\[
\exp(2\gamma x \cdot z) = \sum_{k=0}^{\infty} \frac{(2\gamma)^k}{k!} (x \cdot z)^k
\]

Each term `(x·z)^k` corresponds to monomial features of degree `k`. Summing all degrees = infinite-dim feature space.

**Consequence.** Any labeling of training data is linearly separable in RBF's feature space with the right γ — essentially memorization territory without careful regularization.

**Why it still generalizes in practice.** The Gaussian falls off quickly away from training points. The effective complexity is controlled by γ and C, not by feature-space dimension.

**Rule of thumb:** if RBF SVM isn't beating linear SVM on your data, the problem is probably more subtle (class imbalance, noisy labels, wrong features). Adding kernel complexity rarely fixes those.

```python
# Quick diagnostic — compare linear and RBF
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score

linear_score = cross_val_score(SVC(kernel='linear'), X, y, cv=5).mean()
rbf_score = cross_val_score(SVC(kernel='rbf'), X, y, cv=5).mean()

print(f"Linear: {linear_score:.3f}, RBF: {rbf_score:.3f}")
# If < 1% difference → linear is enough; skip the hyperparameter pain of RBF
```
