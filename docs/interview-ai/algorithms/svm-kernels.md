# Module 4 — SVM & Kernel Methods

Fifteen questions on Support Vector Machines. SVMs lost popularity to tree ensembles in the 2010s, but interviewers still probe them because they force you to think about **margin maximization**, **duality**, and the **kernel trick** — foundational concepts that reappear in modern ML.

---

## Q56. Explain the intuition behind SVM. What's a "maximum margin" classifier? { #q56 }

**SVM's core idea:** Among all hyperplanes that separate the classes, pick the one that **maximizes the margin** — the distance from the hyperplane to the nearest training points.

**Why max margin?**

- **Better generalization:** A wider margin means the decision boundary is "far" from any training point, so small perturbations in test data won't flip predictions.
- **VC dimension bounds:** PAC learning theory says generalization error is bounded by the margin (Vapnik, 1995).

**Visualization:** Imagine two clusters on a plane. Many lines can separate them. SVM picks the unique line where the gap between the line and the nearest points from each class is maximal.

The nearest points are called **support vectors** — they're the only training points that matter for the decision boundary. Remove all other points and the boundary doesn't change.

---

## Q57. Formalize SVM as an optimization problem. { #q57 }

**Hard-margin SVM** (linearly separable data):

$$
\min_{w, b} \frac{1}{2} \|w\|^2
$$

subject to:

$$
y_i (w^\top x_i + b) \geq 1 \quad \forall i
$$

The constraint says: every training point is on the correct side of the margin.

**The margin** is $\frac{2}{\|w\|}$, so minimizing $\|w\|^2$ maximizes the margin.

**Soft-margin SVM** (for non-separable data, introduces slack variables):

$$
\min_{w, b, \xi} \frac{1}{2} \|w\|^2 + C \sum_i \xi_i
$$

subject to:

$$
y_i (w^\top x_i + b) \geq 1 - \xi_i, \quad \xi_i \geq 0
$$

**$C$** is the regularization parameter:

- **Large C:** Few violations allowed → narrow margin, risk of overfitting.
- **Small C:** Many violations tolerated → wide margin, risk of underfitting.

```python
from sklearn.svm import SVC

# Soft-margin linear SVM
svm = SVC(kernel='linear', C=1.0).fit(X, y)

# Access support vectors
print(svm.support_vectors_.shape)  # only the points on the margin
```

---

## Q58. Explain hinge loss. How does it differ from log loss? { #q58 }

**Hinge loss** (SVM's loss function):

$$
L(y, f(x)) = \max(0, 1 - y \cdot f(x))
$$

where $y \in \{-1, +1\}$ and $f(x) = w^\top x + b$.

- If $y \cdot f(x) \geq 1$ → loss = 0 (point outside margin, no penalty).
- If $y \cdot f(x) < 1$ → loss = $1 - y f(x)$ (linear penalty for being inside margin or wrong side).

**Comparison with log loss:**

| Feature | Hinge | Log Loss |
|---|---|---|
| Gradient for correctly-classified far-from-boundary | Zero | Small but nonzero |
| Gradient for misclassified | Linear | Larger for very wrong |
| Probabilistic output | No | Yes |
| Sparse solution | Yes (many α=0) | No |
| Sensitivity to outliers | High | Higher still |

**Geometric intuition:** Hinge loss gives you the **support vector** property — points far from the boundary contribute zero gradient, so they're "ignored." Only the hard cases shape the decision boundary.

```python
import numpy as np

def hinge_loss(y_true, scores):
    # y_true in {-1, +1}
    return np.maximum(0, 1 - y_true * scores).mean()
```

---

## Q59. What's the dual formulation of SVM? Why does it matter? { #q59 }

Using Lagrangian duality, the SVM problem has a dual form:

$$
\max_\alpha \sum_i \alpha_i - \frac{1}{2} \sum_{i,j} \alpha_i \alpha_j y_i y_j \langle x_i, x_j \rangle
$$

subject to:

$$
0 \leq \alpha_i \leq C, \quad \sum_i \alpha_i y_i = 0
$$

**Key properties of the dual:**

- Only **inner products** $\langle x_i, x_j \rangle$ appear — never the features directly.
- Most $\alpha_i = 0$ at the optimum; only support vectors have $\alpha_i > 0$.
- **The kernel trick** (next question) replaces inner products with kernel evaluations — enabling non-linear classification.

**Why does the dual matter?**

1. **Kernel trick** requires the dual.
2. When $p > n$ (more features than samples), the dual is smaller and faster to solve.
3. The dual makes the **sparsity** structure explicit — only support vectors contribute.

**Prediction via dual:**

$$
f(x) = \text{sign}\left(\sum_{i \in \text{SV}} \alpha_i y_i K(x_i, x) + b\right)
$$

---

## Q60. Explain the kernel trick. { #q60 }

**Problem:** What if data isn't linearly separable?

**Naive solution:** Map data to a higher-dimensional feature space where it *is* separable. E.g., 2D $(x_1, x_2)$ → 3D $(x_1, x_2, x_1^2 + x_2^2)$.

**Issue:** Explicit mapping to high-dim space is expensive.

**Kernel trick:** We never need to *explicitly* compute the mapping $\phi(x)$ — we only need the inner product $\langle \phi(x), \phi(x') \rangle$ in that space. A **kernel function** $K(x, x')$ computes this inner product directly, without ever visiting the mapped space.

$$
K(x, x') = \langle \phi(x), \phi(x') \rangle
$$

**Why this is magical:** The mapped space can be **infinite-dimensional** (e.g., RBF kernel) — impossible to compute explicitly, but the inner product in it is computable in constant time.

**Common kernels:**

| Kernel | Formula | Equivalent feature space |
|---|---|---|
| Linear | $\langle x, x' \rangle$ | Identity (no mapping) |
| Polynomial (degree $d$) | $(\gamma \langle x, x' \rangle + r)^d$ | All monomials up to degree $d$ |
| RBF (Gaussian) | $\exp(-\gamma \|x - x'\|^2)$ | Infinite-dimensional |
| Sigmoid | $\tanh(\gamma \langle x, x' \rangle + r)$ | Neural-net-like |
| String kernel | (sequence similarity) | For text/bio |

```python
# Polynomial SVM
SVC(kernel='poly', degree=3, gamma='scale').fit(X, y)

# RBF SVM (most common)
SVC(kernel='rbf', gamma='scale', C=1.0).fit(X, y)

# Precomputed kernel (custom)
K = my_kernel_function(X, X)
SVC(kernel='precomputed').fit(K, y)
```

---

## Q61. Tune C and gamma in RBF SVM — what do they control? { #q61 }

**C (regularization):**

- **Small C (0.001–0.1):** Tolerates misclassifications → wider margin, simpler boundary, underfit.
- **Large C (10–1000):** Strict classifier → narrow margin, complex boundary, overfit.

**Gamma (γ) in RBF kernel:** Controls the "width" of the Gaussian.

$$
K(x, x') = \exp(-\gamma \|x - x'\|^2)
$$

- **Small gamma:** Wide Gaussian → far-away points influence the classification → smooth boundary.
- **Large gamma:** Narrow Gaussian → only very close points matter → each support vector has only local influence → wiggly, overfit boundary.

**Tuning approach:** Grid search on log scale.

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'C': [0.01, 0.1, 1, 10, 100],
    'gamma': [0.001, 0.01, 0.1, 1, 10],
}
grid = GridSearchCV(SVC(kernel='rbf'), param_grid, cv=5, n_jobs=-1).fit(X, y)
print(grid.best_params_)
```

<div class="tip-box" markdown>
**Intuition for C × gamma interaction:** Both control flexibility. High C + high gamma = extreme overfitting. Low C + low gamma = extreme underfitting. They partially compensate — a moderate-C moderate-gamma is usually safe.
</div>

---

## Q62. Why do SVMs scale poorly with large datasets? { #q62 }

**Training complexity:**

- Between $O(n^2)$ and $O(n^3)$ in the number of training samples.
- For kernel SVM, the kernel matrix is $n \times n$ — memory-prohibitive at $n > 50K$.

**Why:** The dual QP has $n$ variables and requires computing pairwise kernel values.

**Scaling strategies:**

**1. Linear SVM at scale (LinearSVC):** Uses primal formulation, solved via coordinate descent. Scales to millions of rows; $O(np)$ per iteration.

```python
from sklearn.svm import LinearSVC
model = LinearSVC(C=1.0, loss='squared_hinge', max_iter=2000).fit(X, y)
```

**2. Kernel approximation:** Explicitly map features to a random-feature representation that approximates the RBF kernel, then use linear SVM.

```python
from sklearn.kernel_approximation import RBFSampler

rbf_feature = RBFSampler(gamma=0.1, n_components=500, random_state=42)
X_mapped = rbf_feature.fit_transform(X)
model = LinearSVC(C=1.0).fit(X_mapped, y)
```

**3. Stochastic gradient descent with hinge loss:** Equivalent to linear SVM training.

```python
from sklearn.linear_model import SGDClassifier
model = SGDClassifier(loss='hinge', alpha=1e-4, max_iter=100).fit(X, y)
```

**4. GPU-accelerated kernel SVMs (ThunderSVM, cuML).**

**Modern reality:** For $n > 100K$, SVMs are rarely the right choice. LightGBM scales to millions of rows with better accuracy and faster inference.

---

## Q63. What is SVR (Support Vector Regression)? { #q63 }

**SVR** is the regression version of SVM. Instead of finding a boundary that separates classes with a margin, it finds a function that fits within an **ε-tube** around the true values.

**Loss function — ε-insensitive loss:**

$$
L_\epsilon(y, f(x)) = \max(0, |y - f(x)| - \epsilon)
$$

- Predictions within $\epsilon$ of true value incur **zero loss**.
- Outside the tube, loss grows linearly (hinge-like).

**Optimization:**

$$
\min_{w, b, \xi, \xi^*} \frac{1}{2} \|w\|^2 + C \sum_i (\xi_i + \xi_i^*)
$$

subject to the prediction being within $\epsilon$ plus slack.

**Key hyperparameters:**

- $\epsilon$ — tube width. Larger $\epsilon$ → more tolerance, simpler model.
- $C$ — penalty for predictions outside the tube.
- Kernel choice — same as SVC.

```python
from sklearn.svm import SVR

model = SVR(kernel='rbf', C=1.0, epsilon=0.1, gamma='scale').fit(X, y)
```

**Why SVR has fallen out of favor:** Scales poorly. LightGBM and neural nets dominate modern regression tasks. SVR still sees use in small-data scientific computing and time-series forecasting with custom kernels.

---

## Q64. What is One-Class SVM? When is it useful? { #q64 }

**One-Class SVM** learns a boundary that encloses the "normal" training data. Anything outside is flagged as an anomaly.

**Formulation:** Minimize the volume of a region that contains a specified fraction $\nu$ of training data:

$$
\min_{w, \rho, \xi} \frac{1}{2} \|w\|^2 + \frac{1}{\nu n} \sum_i \xi_i - \rho
$$

subject to:

$$
w^\top \phi(x_i) \geq \rho - \xi_i, \quad \xi_i \geq 0
$$

The decision function $f(x) = w^\top \phi(x) - \rho$ is positive for "normal" and negative for "anomalous."

**Use cases:**

- **Novelty detection:** train on known-good data, flag anything different.
- **Fraud detection** with only legitimate transactions labeled.
- **Network intrusion detection.**

```python
from sklearn.svm import OneClassSVM

oc_svm = OneClassSVM(
    kernel='rbf',
    gamma='scale',
    nu=0.01    # ~1% of data treated as anomalies
).fit(X_normal)

predictions = oc_svm.predict(X_test)  # +1 normal, -1 anomaly
scores = oc_svm.score_samples(X_test)  # continuous
```

**Alternatives:** Isolation Forest is typically faster and more robust; deep autoencoders for high-dim data.

---

## Q65. How does SVM handle multi-class classification? { #q65 }

SVMs are natively binary. Two strategies for multi-class:

**1. One-vs-Rest (OvR):**

- Train $K$ classifiers, each separating class $k$ from all others.
- Predict by picking the class with the highest score.
- $K$ models to train; fast.

**2. One-vs-One (OvO):**

- Train $K(K-1)/2$ classifiers, one per class pair.
- Predict by majority vote (each classifier votes for one of its two classes).
- $O(K^2)$ models; slower for large $K$, but each model uses less data.

**sklearn defaults to OvO** (`decision_function_shape='ovr'` exposes OvR-style scores):

```python
from sklearn.svm import SVC

# OvO internally
model = SVC(kernel='rbf', decision_function_shape='ovr').fit(X, y)
# decisions has shape (n_samples, n_classes)
decisions = model.decision_function(X)
```

**For $K > 10$ classes**, OvR or direct multi-class methods (Crammer-Singer) are usually faster.

---

## Q66. How does SVM compare to logistic regression? { #q66 }

| Aspect | SVM (linear) | Logistic Regression |
|---|---|---|
| **Loss function** | Hinge | Log loss |
| **Optimization** | Convex QP | Convex, gradient-based |
| **Probabilistic output** | No (needs Platt scaling) | Yes, natively |
| **Decision surface** | Max-margin hyperplane | Maximum-likelihood hyperplane |
| **Robustness to outliers** | High (hinge = zero for correct far points) | Lower (log loss always nonzero) |
| **Sparsity in solution** | Yes (only SV matter) | No (all points contribute) |
| **Multi-class** | OvO/OvR | Natively with softmax |
| **Kernel extension** | Yes (kernel trick) | Yes (but less common) |
| **Large-scale** | LinearSVC or SGD | Scales well, SGD |

**In practice:**

- Linear SVM and logistic regression often give very similar accuracy.
- Logistic regression wins when you need **calibrated probabilities**.
- SVM wins when **robust to label noise** is critical (hinge loss ignores far-correct points).

```python
# Functionally equivalent for most cases:
LogisticRegression(C=1.0, penalty='l2')
LinearSVC(C=1.0, loss='squared_hinge')
```

---

## Q67. Explain Platt scaling. Why do you need it for SVMs? { #q67 }

**SVMs output scores, not probabilities.** The decision value $f(x) = w^\top x + b$ tells you "confidence" in some sense, but it's not a calibrated probability.

**Platt scaling:** Fit a sigmoid on top of the SVM's outputs:

$$
P(y = 1 \mid x) = \frac{1}{1 + \exp(A \cdot f(x) + B)}
$$

Fit $A, B$ by minimizing log loss on a **held-out calibration set** (to avoid overfitting since SVM already fit on training).

```python
# sklearn wraps SVC with probability=True to do Platt scaling internally
model = SVC(kernel='rbf', probability=True).fit(X, y)
probs = model.predict_proba(X_val)

# Or use CalibratedClassifierCV for more control
from sklearn.calibration import CalibratedClassifierCV

base = SVC(kernel='rbf')
calibrated = CalibratedClassifierCV(base, method='sigmoid', cv=5).fit(X, y)
```

**Caveats:**

- Platt scaling costs an extra pass with CV → 5× slower training.
- It can sometimes hurt probability rankings (rare but documented).
- **Isotonic regression** is a non-parametric alternative that fits better-calibrated probabilities when you have ≥ 1000 calibration samples.

---

## Q68. What's the VC dimension, and why does it matter for SVMs? { #q68 }

**VC (Vapnik-Chervonenkis) dimension:** The largest number of points that a classifier can *shatter* — assign any possible binary labeling without error.

Examples:

- Threshold on a line: VC = 2 (can shatter 2 points but not 3 in all orderings).
- Linear classifier in $\mathbb{R}^d$: VC = $d + 1$.
- Circles in $\mathbb{R}^2$: VC = 3.

**Why it matters:** PAC learning theory gives a generalization bound:

$$
\text{test error} \leq \text{train error} + O\left(\sqrt{\frac{\text{VC dim}}{n}}\right)
$$

**SVM's punchline:** Margin-maximization *effectively reduces VC dimension*. The bound becomes:

$$
\text{test error} \leq O\left(\frac{R^2 / \text{margin}^2}{n}\right)
$$

where $R$ is the radius of the data's enclosing ball. A wider margin → tighter generalization bound → better expected test accuracy.

**This is why SVM was theoretically celebrated in the 1990s**: it provides margin-based generalization guarantees that don't depend on the ambient dimension — making kernel SVM's infinite-dim feature space not terrifying.

---

## Q69. SVM pros and cons — when would you use it today? { #q69 }

**Pros:**

- Strong theoretical foundation (VC theory, convex optimization).
- Works well in **high-dimensional data** (text, genomics).
- Effective when $p \gg n$ (more features than samples).
- Memory-efficient at inference (only needs support vectors).
- Kernel flexibility enables non-linear decision boundaries.

**Cons:**

- Poor scalability — $O(n^2)$ to $O(n^3)$ training.
- Sensitive to feature scaling.
- Probabilistic outputs need extra calibration step (Platt).
- Hard to tune (C, γ, kernel choice).
- Multi-class requires workarounds.

**When SVM is still a good choice in 2026:**

- **Text classification with small/medium data** (< 100K docs) — LinearSVC with TF-IDF is a strong, simple baseline.
- **Bioinformatics** — small-$n$, high-$p$ problems (gene expression, protein classification).
- **Novelty detection** — OneClassSVM.
- **Scientific computing** with custom kernels (graph kernels, string kernels).

**When NOT to use SVM:**

- Tabular data with $n > 50K$ → LightGBM wins on accuracy and speed.
- Image/audio/text with deep features available → neural nets or CNNs.
- Any problem requiring calibrated probabilities → logistic regression or NN with sigmoid.

---

## Q70. Scenario: build a spam classifier using SVM. { #q70 }

**Walk through from scratch:**

**1. Data:**

```python
texts = [...]  # emails
labels = [...]  # 0 = ham, 1 = spam
```

**2. Feature extraction:**

```python
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer(
    max_features=50000,
    ngram_range=(1, 2),  # unigrams + bigrams
    min_df=5,            # ignore rare terms
    max_df=0.9,          # ignore too-common terms
    sublinear_tf=True    # log-scale TF
)
X = vectorizer.fit_transform(texts)
```

**3. Train:**

```python
from sklearn.svm import LinearSVC

model = LinearSVC(C=1.0, max_iter=2000).fit(X_train, y_train)
```

Why LinearSVC over SVC: text features are high-dim and sparse; RBF kernel is wasteful.

**4. Tune:**

```python
from sklearn.model_selection import GridSearchCV

grid = GridSearchCV(
    LinearSVC(max_iter=2000),
    {'C': [0.01, 0.1, 1, 10]},
    scoring='f1',
    cv=5
).fit(X_train, y_train)
```

**5. Calibrate:**

```python
from sklearn.calibration import CalibratedClassifierCV

calibrated = CalibratedClassifierCV(grid.best_estimator_, method='sigmoid', cv=5).fit(X_train, y_train)
```

**6. Evaluate:**

```python
from sklearn.metrics import classification_report, roc_auc_score

preds = calibrated.predict(X_test)
probs = calibrated.predict_proba(X_test)[:, 1]
print(classification_report(y_test, preds))
print(f"ROC-AUC: {roc_auc_score(y_test, probs):.4f}")
```

**7. Interpret:**

```python
# Top spam/ham-indicating features
coef = calibrated.base_estimator.coef_.ravel()
feature_names = vectorizer.get_feature_names_out()
top_spam = np.argsort(coef)[-20:]
top_ham = np.argsort(coef)[:20]

print("Most spam-y tokens:", feature_names[top_spam])
print("Most ham-y tokens:", feature_names[top_ham])
```

<div class="tip-box" markdown>
**Interviewer tip:** The strongest candidates finish with **operational concerns**: How do I handle new vocabulary (retraining cadence)? How do I monitor concept drift (spam tactics evolve)? What's my false-positive cost (flagging a wanted email is worse than missing a spam)? These show production maturity beyond pure modeling.
</div>
