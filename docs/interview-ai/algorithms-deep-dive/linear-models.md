# Module 1 — Linear & Generalized Linear Models

**Questions 1–15.** Linear regression, logistic regression, regularized variants, and the GLM family. Sounds boring. Is actually tested more than any other family — because every real ML system has a linear model somewhere in the stack (baseline, calibration, post-processing, simple features).

---

## Q1. Derive linear regression from scratch — why does OLS have a closed-form solution? { #q1 }

**Core idea.** Linear regression assumes the relationship `y = Xβ + ε` where `ε ~ N(0, σ²I)`. We find `β` that minimizes squared error.

**Derivation.**

We minimize:

\[
L(\beta) = \|y - X\beta\|^2 = (y - X\beta)^T(y - X\beta)
\]

Expand:

\[
L(\beta) = y^Ty - 2\beta^T X^T y + \beta^T X^T X \beta
\]

Differentiate and set to zero:

\[
\frac{\partial L}{\partial \beta} = -2X^T y + 2X^T X \beta = 0
\]

Solving:

\[
\boxed{\beta = (X^T X)^{-1} X^T y}
\]

**Why closed-form works:** the loss is *quadratic* and *convex* in β. Gradient = zero gives the unique global minimum.

**Why you'd ever use gradient descent instead:** `X^T X` is `p × p`. Inverting it is O(p³). For p > 10,000 features, gradient descent (or SGD) is cheaper per iteration.

```python
import numpy as np
from sklearn.linear_model import LinearRegression

# Closed-form
beta_closed = np.linalg.inv(X.T @ X) @ X.T @ y

# sklearn (uses LAPACK's SVD under the hood — more numerically stable)
lr = LinearRegression(fit_intercept=True)
lr.fit(X, y)

# They should match
np.allclose(beta_closed, lr.coef_)  # True
```

<div class="tip-box" markdown>
**Interviewer tip:** If asked why sklearn uses SVD instead of the normal equation, say: "SVD is more numerically stable when `X^T X` is near-singular (collinear features) — it regularizes implicitly."
</div>

---

## Q2. What are the 5 assumptions of OLS linear regression, and what breaks if each is violated? { #q2 }

| # | Assumption | What breaks if violated | Fix |
|---|---|---|---|
| 1 | **Linearity** — relationship is linear in parameters | Biased estimates, poor fit | Polynomial features, transformations, or non-linear model |
| 2 | **Independence of errors** | Standard errors wrong → invalid p-values | Use GLS, cluster-robust SE, or time-series methods |
| 3 | **Homoscedasticity** — constant error variance | SE wrong → invalid inference | Robust SE (White's), WLS, or log-transform |
| 4 | **Normality of errors** | Matters only for small samples / CI's | Bootstrap CI, or don't worry for n > 500 |
| 5 | **No perfect multicollinearity** | `X^T X` is singular → can't invert | Drop redundant features, Ridge, PCA |

<div class="scenario" markdown>
**Common interview trap:** "Does OLS require features to be normally distributed?" — **No.** It requires *residuals* to be normal, and only for small-sample inference. Feature distributions can be anything.
</div>

```python
# Diagnostic: check assumptions visually
import statsmodels.api as sm
import matplotlib.pyplot as plt

model = sm.OLS(y, sm.add_constant(X)).fit()
residuals = model.resid
fitted = model.fittedvalues

# 1. Linearity: residuals vs fitted should be random cloud
plt.scatter(fitted, residuals)

# 2. Homoscedasticity: Breusch-Pagan test
from statsmodels.stats.diagnostic import het_breuschpagan
_, p_value, _, _ = het_breuschpagan(residuals, sm.add_constant(X))
# p < 0.05 → heteroscedastic

# 3. Normality: Q-Q plot
sm.qqplot(residuals, line='s')
```

---

## Q3. Derive logistic regression — why cross-entropy loss instead of MSE? { #q3 }

**Setup.** We model `P(y=1 | x) = σ(wᵀx) = 1 / (1 + exp(-wᵀx))`.

**Why not MSE on the sigmoid output?** Two reasons:

1. **Non-convex surface.** MSE composed with sigmoid creates a non-convex loss → local minima → gradient descent fails.
2. **Vanishing gradients.** When sigmoid saturates (output near 0 or 1), the gradient of MSE is near zero even when predictions are very wrong. Training stalls.

**Cross-entropy derivation (from maximum likelihood):**

Likelihood of observing labels given model:

\[
L(w) = \prod_{i=1}^n \sigma(w^T x_i)^{y_i} (1 - \sigma(w^T x_i))^{1-y_i}
\]

Negative log-likelihood:

\[
-\log L = -\sum_i \left[ y_i \log \sigma(w^T x_i) + (1-y_i) \log(1 - \sigma(w^T x_i)) \right]
\]

This is convex in `w` and has well-behaved gradients:

\[
\nabla_w L = X^T (\sigma(Xw) - y)
\]

The gradient is proportional to the *error* — even when saturated, the signal is informative.

```python
from sklearn.linear_model import LogisticRegression

# scikit-learn uses L2 regularization by default with C=1
lr = LogisticRegression(penalty='l2', C=1.0, solver='lbfgs', max_iter=1000)
lr.fit(X_train, y_train)

# Interpret coefficients as log-odds
# A coefficient of 0.5 means: one-unit increase in feature multiplies odds by exp(0.5) = 1.65
import numpy as np
odds_ratio = np.exp(lr.coef_)
```

<div class="tip-box" markdown>
**Interviewer follow-up:** "What if you have 3 classes?" — Softmax regression (multinomial logistic). The sigmoid generalizes to `softmax(z)_k = exp(z_k) / Σ exp(z_j)`.
</div>

---

## Q4. Ridge vs Lasso vs ElasticNet — what's the geometric intuition? { #q4 }

All three add a penalty to OLS loss:

- **Ridge:** `L = ‖y - Xβ‖² + λ‖β‖²` (L2 norm)
- **Lasso:** `L = ‖y - Xβ‖² + λ‖β‖₁` (L1 norm)
- **ElasticNet:** `L = ‖y - Xβ‖² + λ₁‖β‖₁ + λ₂‖β‖²`

**Geometric picture.** Imagine minimizing squared error *subject to* a constraint region:

- **Ridge** constraint: sphere (smooth). The optimum touches the sphere tangentially → no coordinate is exactly zero.
- **Lasso** constraint: diamond (corners on axes). The optimum often lands *on a corner* → exact zeros → sparse solution.
- **ElasticNet:** rounded diamond — some sparsity, but groups of correlated features get shrunk together.

| Property | Ridge | Lasso | ElasticNet |
|---|---|---|---|
| Feature selection | No | Yes (hard) | Yes (grouped) |
| Handles collinearity | Well | Poorly — picks one arbitrarily | Well |
| Closed-form | Yes | No (iterative) | No |
| Bayesian prior | Gaussian | Laplace | Mix |

```python
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.preprocessing import StandardScaler

# Always scale features before regularization — otherwise penalty is unfair
# to features with larger magnitudes
X_scaled = StandardScaler().fit_transform(X)

ridge = Ridge(alpha=1.0).fit(X_scaled, y)      # alpha = λ
lasso = Lasso(alpha=0.1).fit(X_scaled, y)
elastic = ElasticNet(alpha=0.1, l1_ratio=0.5).fit(X_scaled, y)
# l1_ratio=0 → Ridge, l1_ratio=1 → Lasso
```

<div class="scenario" markdown>
**When to use which:**

- **You have 5 correlated features, want to keep all** → Ridge.
- **You have 500 features, suspect only 20 matter, want interpretability** → Lasso.
- **You have groups of correlated features, want sparse group selection** → ElasticNet.
- **You don't know which to pick** → ElasticNet with CV over `alpha` and `l1_ratio`.
</div>

---

## Q5. What's the MAP interpretation of Ridge and Lasso? { #q5 }

Regularization = Bayesian prior on parameters.

**Ridge = Gaussian prior.** Assume `β_j ~ N(0, σ²_β)`. The MAP estimate is:

\[
\hat{\beta}_{MAP} = \arg\max_\beta \left[ \log p(y|X, \beta) + \log p(\beta) \right]
\]

The Gaussian prior contributes `-β²/(2σ²_β)` → equivalent to L2 penalty.

**Lasso = Laplace prior.** Assume `β_j ~ Laplace(0, b)`. The prior has a sharp peak at zero → pushes coefficients to be exactly zero. Contributes `-|β|/b` → equivalent to L1 penalty.

**Why this matters:** it tells you *what belief* you're encoding. Ridge says "coefficients are small and smooth." Lasso says "most coefficients are exactly zero, a few are non-zero."

<div class="tip-box" markdown>
**Interviewer asks:** "Why do Lasso coefficients have zeros?" — say: "Because Laplace is a sparsity-inducing prior — its density is non-differentiable at zero, so the MAP estimator favors corner solutions."
</div>

---

## Q6. How do you interpret logistic regression coefficients? { #q6 }

**If coefficient is β_j:**

- A one-unit increase in feature `j` multiplies the **odds** of `y=1` by `exp(β_j)`.
- It does *not* linearly change the probability.

**Example:** model on loan default with feature `income_k` (thousands):

- `β_income = -0.05` → one $1K increase in income reduces default odds by `1 - exp(-0.05) = 4.9%`.
- For $20K income increase: odds multiplier is `exp(-0.05 × 20) = exp(-1) = 0.37`, so default odds drop by 63%.

**Pitfalls:**

1. **Scaling matters.** If you standardize features, coefficients become "per-standard-deviation" effects.
2. **Categorical baselines.** For dummy-encoded features, coefficients are relative to the reference category.
3. **Probability ≠ odds.** Don't say "income reduces probability of default by 4.9%" — that's wrong unless starting probability is near 0 or 1.

```python
import numpy as np
import pandas as pd

# Coefficient interpretation table
coef_df = pd.DataFrame({
    'feature': features,
    'coef': lr.coef_[0],
    'odds_ratio': np.exp(lr.coef_[0]),
    'pct_change_odds': (np.exp(lr.coef_[0]) - 1) * 100
})
print(coef_df.sort_values('pct_change_odds', ascending=False))
```

---

## Q7. What is a Generalized Linear Model (GLM)? Give 3 examples. { #q7 }

**Definition.** A GLM generalizes linear regression by allowing:

1. **Response distribution** from the exponential family (Gaussian, Binomial, Poisson, Gamma, ...).
2. **Link function** `g()` relating `E[y]` to the linear predictor: `g(E[y]) = Xβ`.

**Three canonical examples:**

| Name | Distribution | Link function | Use case |
|---|---|---|---|
| **Linear regression** | Gaussian | Identity: `μ = Xβ` | Continuous outcomes (prices, heights) |
| **Logistic regression** | Binomial | Logit: `log(μ/(1-μ)) = Xβ` | Binary classification |
| **Poisson regression** | Poisson | Log: `log(μ) = Xβ` | Count data (hospital visits, clicks) |

**Less common but asked:**

- **Gamma regression** — continuous positive data with constant coefficient of variation (claim sizes, lifetimes).
- **Negative binomial** — overdispersed count data where Poisson variance = mean doesn't hold.

```python
import statsmodels.api as sm

# Poisson regression for count data
X_const = sm.add_constant(X)
poisson = sm.GLM(y_counts, X_const, family=sm.families.Poisson()).fit()
print(poisson.summary())

# Gamma regression for positive continuous
gamma = sm.GLM(y_positive, X_const, family=sm.families.Gamma(link=sm.families.links.log())).fit()
```

<div class="tip-box" markdown>
**Senior signal:** mention that GLMs are the theoretical backbone for a lot of "classic" statistics in insurance (gamma, Tweedie for claim losses), epidemiology (logistic), and telecom (Poisson for call counts).
</div>

---

## Q8. What's the difference between Poisson and Negative Binomial regression? When to use which? { #q8 }

**Poisson assumes:** `Var(y) = E[y]`. Variance equals mean.

**Real-world problem:** count data is often *overdispersed* — variance >> mean. Examples: customer purchase counts (many zeros, occasional large buyers), insurance claims.

**Negative Binomial** allows variance to exceed mean:

\[
Var(y) = \mu + \alpha \mu^2
\]

where `α` is a dispersion parameter. If `α = 0`, it reduces to Poisson.

**How to choose:**

1. Fit Poisson first.
2. Check **dispersion ratio** = `Pearson χ² / df`. If > 1.2, suspect overdispersion.
3. Fit NegBin and compare AIC.

```python
from scipy.stats import chi2

poisson = sm.GLM(y, X_const, family=sm.families.Poisson()).fit()
dispersion_ratio = poisson.pearson_chi2 / poisson.df_resid
print(f"Dispersion ratio: {dispersion_ratio:.2f}")

if dispersion_ratio > 1.2:
    negbin = sm.GLM(y, X_const, family=sm.families.NegativeBinomial(alpha=1.0)).fit()
    print(f"Poisson AIC: {poisson.aic:.0f}, NegBin AIC: {negbin.aic:.0f}")
```

<div class="scenario" markdown>
**Real interview scenario:** "We're modeling website clicks per user per day. 90% of users have 0 clicks. What model?" — **Zero-inflated NegBin** (or Hurdle model): one component models the zero-inflation (is-it-zero?), another models the positive count.
</div>

---

## Q9. What's Tweedie regression and why is it used in insurance? { #q9 }

**Problem:** claim amounts have two parts:

1. *Whether* a claim occurs (binary, rare).
2. *How much* the claim costs given it occurs (positive continuous).

Modeling these separately = two models. **Tweedie** handles both jointly via a mixture: Poisson-Gamma compound.

**Variance function:**

\[
Var(y) = \phi \mu^p
\]

- `p = 0` → Gaussian.
- `p = 1` → Poisson.
- `p = 2` → Gamma.
- `1 < p < 2` → Compound Poisson-Gamma — exactly the insurance case.

```python
# Available in scikit-learn and xgboost
from sklearn.linear_model import TweedieRegressor

tw = TweedieRegressor(power=1.5, alpha=0.5, link='log').fit(X, y_claims)

# XGBoost also supports Tweedie loss
import xgboost as xgb
model = xgb.XGBRegressor(
    objective='reg:tweedie',
    tweedie_variance_power=1.5
)
```

<div class="tip-box" markdown>
**Insurance interviewer cue:** mention Tweedie naturally → instant signal of domain awareness.
</div>

---

## Q10. When would you choose logistic regression over XGBoost? { #q10 }

Contrarian but important — XGBoost isn't always the answer.

**Choose logistic regression when:**

1. **Interpretability is regulatory.** Banks, insurance, healthcare need model cards. Every coefficient is auditable. XGBoost requires SHAP explanations that auditors often don't accept.
2. **Tiny data** (n < 1000). XGBoost overfits. Logistic regularized is more stable.
3. **Linear decision boundary suffices.** If domain experts can write the rule in one line ("high income + good credit = approve"), logistic captures it.
4. **Calibration matters out-of-the-box.** Logistic outputs well-calibrated probabilities. XGBoost needs Platt scaling or isotonic regression.
5. **Latency is microseconds.** Logistic = one dot product. XGBoost = 100s of tree traversals.
6. **Feature engineering is the bottleneck, not model.** If you have great hand-crafted features, linear model is often within 1% of XGBoost.
7. **Real-time feature updates.** Logistic coefficients can be updated via online SGD; tree ensembles typically can't without retraining.

| Criterion | Logistic | XGBoost |
|---|---|---|
| Accuracy (typical tabular) | Good | Usually +2-10% |
| Interpretability | Direct | Needs SHAP |
| Inference speed | ~0.1 µs | ~10–100 µs |
| Training speed | Fast | Fast with GPU |
| Calibration | Good | Needs post-hoc |
| Handles non-linear | Only with feature eng | Natively |

---

## Q11. Explain the SGD solver for logistic regression. What are its gotchas? { #q11 }

**The update rule for logistic regression via SGD:**

For each training example `(x_i, y_i)`:

\[
w \leftarrow w - \eta \nabla_w L_i = w - \eta (\sigma(w^T x_i) - y_i) x_i
\]

Plus L2 regularization term `−η λ w`.

**Gotchas:**

1. **Learning rate schedule.** Fixed LR oscillates. Use `lr / (1 + α·t)` or `lr / √t`. sklearn's `SGDClassifier` defaults to `1 / (alpha × (t + t0))`.
2. **Feature scaling is mandatory.** Without it, gradients are dominated by large-magnitude features.
3. **Shuffle every epoch.** Otherwise you hit correlated updates and oscillate.
4. **Early stopping on validation loss** — SGD will overfit given enough epochs.
5. **Random seed sensitivity** — two runs give different models. For reproducibility, fix seed *and* control data order.
6. **Don't forget to warm up learning rate** for small batches.

```python
from sklearn.linear_model import SGDClassifier

sgd = SGDClassifier(
    loss='log_loss',         # logistic regression
    penalty='l2',
    alpha=1e-4,              # regularization strength
    learning_rate='optimal', # uses Leon Bottou's heuristic
    max_iter=1000,
    tol=1e-3,                # convergence tolerance
    early_stopping=True,
    validation_fraction=0.1,
    random_state=42,
)
sgd.fit(X_train_scaled, y_train)

# Online learning — feed mini-batches as they arrive
sgd.partial_fit(X_new_batch, y_new_batch, classes=[0, 1])
```

---

## Q12. Explain the bias-variance tradeoff in the context of linear regression and Ridge. { #q12 }

**OLS.** Under the Gauss-Markov assumptions, OLS is the *Best Linear Unbiased Estimator* — minimum variance among all unbiased linear estimators. But "unbiased minimum variance" is not the same as "minimum MSE":

\[
MSE = Bias^2 + Variance
\]

If variance is huge (near-singular `X^T X`), accepting some bias reduces MSE.

**Ridge trade.** Ridge is *biased* (shrinks coefficients toward zero) but has *lower variance* than OLS. For sufficiently large `λ`, Ridge's MSE < OLS's MSE — even though Ridge is biased!

This is why Ridge wins on ill-conditioned problems (near-collinear features, small n).

**Intuition.** Ridge "stabilizes" the solution: small changes in `X` cause small changes in `β`. OLS in the same situation produces wildly different coefficients for small data perturbations.

```python
# Demo: run OLS and Ridge on bootstraps to see variance
from sklearn.utils import resample

coef_ols = []
coef_ridge = []
for _ in range(500):
    X_b, y_b = resample(X, y)
    coef_ols.append(np.linalg.inv(X_b.T @ X_b) @ X_b.T @ y_b)
    coef_ridge.append(Ridge(alpha=10).fit(X_b, y_b).coef_)

import numpy as np
print(f"OLS coef std: {np.std(coef_ols, axis=0).mean():.4f}")
print(f"Ridge coef std: {np.std(coef_ridge, axis=0).mean():.4f}")
# Ridge std is much smaller → lower variance
```

---

## Q13. How do you interpret Lasso's path — what does `alpha` do? { #q13 }

The **Lasso path** shows how coefficients change as `λ` (alpha) varies.

- **Large `λ`** → heavy penalty → all coefficients shrink to zero.
- **Small `λ`** → light penalty → solution approaches OLS.
- As `λ` decreases, features enter the model *one at a time* (roughly, in order of importance).

```python
from sklearn.linear_model import lasso_path
import matplotlib.pyplot as plt

alphas, coefs, _ = lasso_path(X_scaled, y, eps=5e-3, n_alphas=100)

# Plot each feature's trajectory
plt.figure(figsize=(10, 6))
for i in range(X.shape[1]):
    plt.plot(np.log10(alphas), coefs[i])
plt.xlabel('log10(alpha)')
plt.ylabel('Coefficient')
plt.title('Lasso Path — which features enter first')
plt.gca().invert_xaxis()  # decreasing alpha left to right
```

**What to look for in the plot:**

- Features that enter early (left side) are the most predictive.
- Features that stay at zero throughout are useless or redundant.
- Features that flip sign at some `λ` are likely collinear — unstable.

<div class="tip-box" markdown>
**Senior signal:** "I use `LassoCV` to choose `alpha` via cross-validation, then inspect the path to verify the selected features are stable across a range of nearby `alpha` values."
</div>

---

## Q14. What's the perceptron algorithm, and why is it interesting historically? { #q14 }

**Update rule.** Given misclassified example `(x_i, y_i)` with `y_i ∈ {-1, +1}`:

\[
w \leftarrow w + y_i x_i
\]

Only updates on mistakes. Convergence guaranteed if data is linearly separable (Perceptron Convergence Theorem, Rosenblatt 1958, proven by Novikoff 1962).

**Why historically important:**

- The **first** algorithm with a mathematical convergence guarantee for learning.
- Minsky & Papert's 1969 book showed perceptron *can't* solve XOR — paused neural net research for ~15 years ("AI winter").
- SVM's hard-margin case and voted/averaged perceptron (Freund & Schapire, 1999) descend from it.

**Why still used in practice:**

- Online learning with minimal memory.
- Great for text classification baselines with millions of features (each update is O(non-zero features)).
- Voted perceptron gives near-SVM performance at a fraction of training cost.

```python
from sklearn.linear_model import Perceptron

perc = Perceptron(
    penalty='l2',
    alpha=0.0001,
    max_iter=1000,
    tol=1e-3,
    random_state=42,
)
perc.fit(X_train, y_train)

# Equivalent of voted/averaged perceptron — use with early stopping
```

---

## Q15. How do you handle categorical features with logistic regression? { #q15 }

Four options, each with tradeoffs:

**1. One-hot encoding** — `k` categories → `k-1` dummies (drop one as reference).

```python
import pandas as pd
X_oh = pd.get_dummies(df, columns=['city'], drop_first=True)
```

- ✅ Interpretable coefficients.
- ❌ Explodes dimensionality if `k` is large (100+ cities).

**2. Target encoding** — replace each category with mean of `y` for that category (with smoothing).

```python
from category_encoders import TargetEncoder
te = TargetEncoder(smoothing=10)
X_encoded = te.fit_transform(X_train, y_train)
```

- ✅ Preserves dimensionality.
- ❌ Major leakage risk — *must* use out-of-fold encoding.

**3. Frequency encoding** — replace category with its count/frequency.

- ✅ No leakage.
- ❌ Two categories with same frequency collapse — loses info.

**4. Hashing (feature hashing trick)** — hash category to a fixed-size bucket.

```python
from sklearn.feature_extraction import FeatureHasher
fh = FeatureHasher(n_features=128, input_type='string')
X_hashed = fh.transform(X_cat)
```

- ✅ Bounded memory, no vocabulary needed.
- ❌ Collisions reduce interpretability.

**Decision tree for logistic regression:**

- `k < 10` → one-hot.
- `10 ≤ k < 100` → one-hot or target encoding with regularization.
- `k > 100` → target encoding out-of-fold, or hashing for streaming.
- Target is extreme class-imbalanced → **smoothed** target encoding to avoid leakage on rare categories.

<div class="scenario" markdown>
**Production trap:** target encoding computed on full train, then applied to test → looks great in CV, collapses in production because rare test categories have no encoding. Fix: fit target encoder on CV folds only, and specify a fallback strategy for unseen categories (e.g., global mean).
</div>
