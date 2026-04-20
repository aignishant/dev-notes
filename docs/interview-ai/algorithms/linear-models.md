# Module 1 — Linear Models

Fifteen questions on linear and generalized linear models. Interviewers love these because they're the *baseline* against which everything else is judged — if you don't understand linear models deeply, you don't understand what neural networks are improving on.

---

## Q1. Derive the closed-form solution for OLS linear regression. { #q1 }

Given a design matrix $X \in \mathbb{R}^{n \times p}$ and targets $y \in \mathbb{R}^n$, we want to find $\beta$ minimizing:

$$
\mathcal{L}(\beta) = \|y - X\beta\|^2 = (y - X\beta)^\top (y - X\beta)
$$

Expand:

$$
\mathcal{L}(\beta) = y^\top y - 2 \beta^\top X^\top y + \beta^\top X^\top X \beta
$$

Take the gradient and set to zero:

$$
\nabla_\beta \mathcal{L} = -2 X^\top y + 2 X^\top X \beta = 0
$$

$$
\boxed{\hat{\beta} = (X^\top X)^{-1} X^\top y}
$$

This is the **normal equation**.

**Why you rarely use it in practice:**

- $(X^\top X)^{-1}$ is $O(p^3)$ to compute — infeasible for wide data.
- $X^\top X$ can be ill-conditioned (near-singular) when features are collinear.
- Gradient descent + QR decomposition + SVD-based pseudoinverse are all more numerically stable.

```python
import numpy as np

# Closed form (don't do this for p > ~1000)
beta = np.linalg.inv(X.T @ X) @ X.T @ y

# Numerically stable version
beta, *_ = np.linalg.lstsq(X, y, rcond=None)

# sklearn does SVD under the hood
from sklearn.linear_model import LinearRegression
model = LinearRegression().fit(X, y)
```

<div class="tip-box" markdown>
**Interviewer tip:** If they ask "why does `sklearn.LinearRegression` not use the closed form?" — answer: *numerical stability*. SVD handles rank-deficient matrices gracefully; matrix inversion does not.
</div>

---

## Q2. What are the five assumptions of OLS? { #q2 }

The Gauss-Markov assumptions, memorized with the acronym **LINE + H**:

| Assumption | What it means | Violation consequence |
|---|---|---|
| **L**inearity | $y = X\beta + \varepsilon$, linear in parameters | Biased estimates, wrong functional form |
| **I**ndependence | Observations independent | Underestimated standard errors |
| **N**ormality of errors | $\varepsilon \sim \mathcal{N}(0, \sigma^2)$ | Invalidates t/F tests (for small n) |
| **E**qual variance (homoscedasticity) | $\text{Var}(\varepsilon_i) = \sigma^2$ constant | Inefficient estimates, bad CIs |
| No perfect multicollinearity | $X^\top X$ invertible | Coefficients undefined or unstable |

**Under L+I+homoscedasticity+no-multicollinearity**, OLS is BLUE (Best Linear Unbiased Estimator) by Gauss-Markov. Normality is only needed for inference (p-values, CIs), not for estimation.

**Diagnostic plots:**

- **Residuals vs fitted** → should look random. Fan shape = heteroscedasticity.
- **Q-Q plot** → residuals should line up on the diagonal. Deviations at tails = non-normal.
- **Residuals vs time** → patterns = autocorrelation.
- **VIF** → variance inflation factor > 10 signals multicollinearity.

```python
import statsmodels.api as sm
model = sm.OLS(y, sm.add_constant(X)).fit()
print(model.summary())           # full diagnostic table
print(model.rsquared_adj)        # adjusted R²
sm.stats.diagnostic.het_breuschpagan(model.resid, model.model.exog)  # heteroscedasticity test
```

---

## Q3. What's the difference between simple, multiple, and polynomial regression? { #q3 }

| Type | Form | Use when |
|---|---|---|
| **Simple linear** | $y = \beta_0 + \beta_1 x + \varepsilon$ | One predictor |
| **Multiple linear** | $y = \beta_0 + \beta_1 x_1 + \dots + \beta_p x_p + \varepsilon$ | Multiple predictors, linear relationship |
| **Polynomial** | $y = \beta_0 + \beta_1 x + \beta_2 x^2 + \dots + \beta_d x^d + \varepsilon$ | Curved, non-linear relationship with one variable |

**Key insight:** Polynomial regression is *still linear* — linear in the *parameters* $\beta$, not the inputs. You're just using a transformed feature matrix $[x, x^2, x^3, \dots]$.

```python
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline

# Degree-3 polynomial
model = make_pipeline(PolynomialFeatures(degree=3), LinearRegression()).fit(X, y)
```

<div class="scenario" markdown>
**Scenario:** A candidate fits a 15-degree polynomial to 20 data points. What goes wrong?

**Answer:** Massive overfitting. Polynomial degree equals flexibility — degree 15 on 20 points produces a curve that oscillates wildly through every training point. Train error → 0, test error → disastrous. The fix: regularize (Ridge) or use splines that penalize curvature, or just use a simpler model.
</div>

---

## Q4. Explain Ridge regression and why L2 penalty shrinks but doesn't zero out coefficients. { #q4 }

Ridge adds an L2 penalty to OLS:

$$
\hat{\beta}_{\text{ridge}} = \arg\min_\beta \|y - X\beta\|^2 + \lambda \|\beta\|_2^2
$$

Closed form:

$$
\hat{\beta}_{\text{ridge}} = (X^\top X + \lambda I)^{-1} X^\top y
$$

**Why it shrinks but doesn't zero:**

The geometry is key. L2 penalty is $\sum \beta_j^2$ — a smooth, circular constraint region. The optimal $\beta$ is where OLS's elliptical contours touch the constraint ball. Because the ball is smooth (no corners), this tangent point is almost always at a location where *all coordinates are nonzero*.

Contrast with L1 (Lasso), whose constraint region is a diamond (polytope) with corners on the axes — tangent points often fall on a corner, zeroing out that coordinate.

**Why Ridge works with multicollinearity:**

When $X^\top X$ is near-singular, its eigenvalues approach zero and $(X^\top X)^{-1}$ blows up. Adding $\lambda I$ shifts all eigenvalues by $\lambda$, keeping the matrix invertible and well-conditioned.

```python
from sklearn.linear_model import Ridge, RidgeCV

# Fixed alpha
model = Ridge(alpha=1.0).fit(X, y)

# CV-selected alpha
model = RidgeCV(alphas=[0.01, 0.1, 1, 10, 100]).fit(X, y)
```

---

## Q5. Explain Lasso regression and why it performs feature selection. { #q5 }

Lasso adds an L1 penalty:

$$
\hat{\beta}_{\text{lasso}} = \arg\min_\beta \|y - X\beta\|^2 + \lambda \|\beta\|_1
$$

**Why it zeros out features:**

The L1 constraint region is a hyper-diamond (an L1 ball) with vertices on the axes. The elliptical contours of OLS touch this diamond more often at a vertex than on an edge — and at a vertex, one or more $\beta_j = 0$.

Mathematically, the soft-thresholding update for Lasso (via coordinate descent) is:

$$
\beta_j \leftarrow \text{sign}(z_j) \cdot \max(|z_j| - \lambda, 0)
$$

When $|z_j| < \lambda$, $\beta_j$ becomes *exactly* zero. This is the mechanism.

**Limitations of Lasso:**

- With highly correlated features, Lasso arbitrarily picks *one* and zeros the rest. Ridge spreads weight across the group.
- When $p > n$, Lasso selects at most $n$ features.
- Non-convex variants (MCP, SCAD) reduce bias of selected coefficients.

**ElasticNet combines both:**

$$
\mathcal{L}(\beta) = \|y - X\beta\|^2 + \lambda_1 \|\beta\|_1 + \lambda_2 \|\beta\|_2^2
$$

Useful when you want Lasso's sparsity plus Ridge's handling of correlated feature groups.

```python
from sklearn.linear_model import Lasso, ElasticNet

lasso = Lasso(alpha=0.1).fit(X, y)
print(f"Non-zero features: {np.sum(lasso.coef_ != 0)}")

enet = ElasticNet(alpha=0.1, l1_ratio=0.5).fit(X, y)
```

---

## Q6. Derive logistic regression's loss function. Why cross-entropy and not MSE? { #q6 }

Logistic regression models:

$$
P(y=1 \mid x) = \sigma(w^\top x) = \frac{1}{1 + e^{-w^\top x}}
$$

**Likelihood** for binary labels:

$$
\mathcal{L}(w) = \prod_{i=1}^{n} p_i^{y_i} (1 - p_i)^{1 - y_i}
$$

Take the negative log:

$$
-\log \mathcal{L}(w) = -\sum_{i=1}^{n} \left[ y_i \log p_i + (1 - y_i) \log(1 - p_i) \right]
$$

This is **binary cross-entropy** (a.k.a. log loss).

**Why not MSE?**

Two reasons:

1. **Non-convexity.** With sigmoid + MSE, the loss surface is non-convex — gradient descent can get stuck in local minima. Cross-entropy + sigmoid gives a convex loss.

2. **Vanishing gradients.** For MSE + sigmoid, the gradient is:

   $$
   \frac{\partial \mathcal{L}}{\partial w} = (p - y) \cdot \sigma'(z) \cdot x
   $$

   When the model is very wrong ($p \approx 1, y = 0$), $\sigma'(z) \approx 0$ — the gradient dies, and learning stalls. Cross-entropy's gradient is $(p - y) \cdot x$ — it's *larger* when the model is more wrong. This is why cross-entropy trains faster.

<div class="tip-box" markdown>
**Interviewer probe:** "Why is MSE OK for linear regression but not logistic?" → Because linear regression outputs unbounded $\hat{y}$, and MSE + identity link gives a convex loss. Logistic's sigmoid breaks the convexity.
</div>

---

## Q7. Explain the decision boundary of logistic regression. Is it linear? { #q7 }

**Yes — the decision boundary is linear in feature space.**

Decision rule: classify as 1 if $P(y=1 \mid x) > 0.5$.

$$
\sigma(w^\top x) > 0.5 \iff w^\top x > 0
$$

The boundary $w^\top x = 0$ is a hyperplane.

**But it's *still* a linear model even if the boundary looks curved** — if you include polynomial or interaction features, the model is linear in the *parameters* but can draw curved boundaries in the original input space.

```python
# Linear boundary in x
LogisticRegression().fit(X, y)

# Curved boundary in x via feature engineering
from sklearn.preprocessing import PolynomialFeatures
model = make_pipeline(PolynomialFeatures(2), LogisticRegression()).fit(X, y)
```

**Comparison:**

| Model | Boundary shape | Why |
|---|---|---|
| Logistic regression | Linear (hyperplane) | Linear in weights |
| Logistic + polynomial features | Curved | Linear in weights, but in a higher-dim space |
| Decision tree | Axis-aligned rectangles | Splits on single features |
| SVM with RBF kernel | Arbitrary curves | Kernel trick maps to infinite-dim space |
| Neural net (deep) | Arbitrary | Universal approximation |

---

## Q8. Multiclass logistic regression: OvR vs softmax. When to use which? { #q8 }

**One-vs-Rest (OvR):**

Fit $K$ binary classifiers, each separating class $k$ from all others. At prediction time, pick the class with the highest probability.

Pros: works with any binary classifier; parallelizable.
Cons: probabilities don't sum to 1 (need rescaling); imbalance in each subproblem.

**Softmax (multinomial logistic):**

Single model with $K$ weight vectors:

$$
P(y = k \mid x) = \frac{e^{w_k^\top x}}{\sum_{j=1}^{K} e^{w_j^\top x}}
$$

Trained with categorical cross-entropy:

$$
\mathcal{L} = -\sum_{i=1}^{n} \sum_{k=1}^{K} \mathbb{1}[y_i = k] \log P(y_i = k \mid x_i)
$$

Pros: proper joint distribution; probabilities sum to 1.
Cons: not compatible with non-probabilistic binary classifiers; requires one coherent optimization.

**Rule of thumb:**

- `LogisticRegression(multi_class='multinomial')` (softmax) — default, best-calibrated.
- `multi_class='ovr'` — use when you need one-vs-rest semantics (e.g., multi-label).
- For SVMs, OvR or OvO is the only option.

---

## Q9. What's a Generalized Linear Model (GLM)? Give three examples. { #q9 }

A GLM has three components:

1. **Random component** — the response $y$ follows an exponential-family distribution.
2. **Systematic component** — a linear predictor $\eta = X\beta$.
3. **Link function** — $g(\mathbb{E}[y]) = \eta$.

The link $g$ connects the linear predictor to the mean of the distribution.

| Response | Distribution | Link | Model |
|---|---|---|---|
| Continuous, unbounded | Gaussian | Identity | Linear regression |
| Binary | Bernoulli | Logit | Logistic regression |
| Count | Poisson | Log | Poisson regression |
| Count with overdispersion | Neg. binomial | Log | NB regression |
| Positive continuous | Gamma | Log (or inverse) | Gamma regression |

```python
import statsmodels.api as sm

# Poisson regression (e.g., count of events per customer)
model = sm.GLM(y, X, family=sm.families.Poisson()).fit()

# Gamma regression (e.g., claim amounts)
model = sm.GLM(y, X, family=sm.families.Gamma(link=sm.families.links.log())).fit()
```

<div class="scenario" markdown>
**Scenario:** Predicting the number of insurance claims per policy per year. Most policies have 0 claims, some have 1, few have 5+. Which model?

**Answer:** Poisson regression — it's designed for non-negative counts. But first check: is $\text{Var}(y) \approx \mathbb{E}[y]$? If variance >> mean (overdispersion), use negative binomial. If many zeros (zero-inflation), use a zero-inflated Poisson or hurdle model.
</div>

---

## Q10. Multicollinearity: what is it, how to detect, how to fix? { #q10 }

**Definition:** Two or more predictors are highly correlated with each other.

**Why it's a problem:**

- Coefficients become unstable — small data changes flip their signs.
- Standard errors inflate → p-values become meaningless.
- Interpretation breaks: "the effect of $X_1$ holding $X_2$ constant" is nonsensical when $X_1$ and $X_2$ move together.
- Prediction performance is unaffected, only inference.

**Detection:**

1. **Correlation matrix** — pairwise, catches simple cases.
2. **Variance Inflation Factor (VIF):** for feature $j$, regress $X_j$ on all other features and compute $\text{VIF}_j = 1 / (1 - R_j^2)$. Rule of thumb:
   - VIF < 5 → fine
   - 5–10 → suspicious
   - > 10 → problematic
3. **Condition number** of $X^\top X$ — large values signal ill-conditioning.

**Fixes:**

- Drop one of the correlated features.
- Combine them (e.g., `height`, `weight` → `BMI`).
- Use Ridge regression (handles it gracefully).
- Use PCA features (orthogonal by construction).

```python
from statsmodels.stats.outliers_influence import variance_inflation_factor

vifs = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
high_vif = [(col, v) for col, v in zip(X.columns, vifs) if v > 10]
```

---

## Q11. What's the interpretation of logistic regression coefficients? { #q11 }

A coefficient $\beta_j$ in logistic regression is interpreted as the **log-odds change** per unit increase in $x_j$.

$$
\log \frac{P(y=1)}{P(y=0)} = w^\top x
$$

So:

- $e^{\beta_j}$ = **odds ratio** for a one-unit increase in $x_j$.
- $e^{\beta_j} > 1$ → increases odds of class 1.
- $e^{\beta_j} < 1$ → decreases odds.

**Example:** In a model predicting loan default, if $\beta_{\text{credit score}} = -0.01$, then:

- A 1-point increase in credit score multiplies default odds by $e^{-0.01} \approx 0.99$ (1% decrease).
- A 100-point increase multiplies odds by $e^{-1} \approx 0.37$ (63% decrease).

!!! warning "Common interview mistake"
    Coefficients are **not** probabilities. They're log-odds. The relationship between coefficient and probability is non-linear (sigmoid).

---

## Q12. How does gradient descent apply to linear regression, and what's the update rule? { #q12 }

For OLS loss $\mathcal{L}(\beta) = \frac{1}{2n} \|y - X\beta\|^2$:

$$
\nabla_\beta \mathcal{L} = -\frac{1}{n} X^\top (y - X\beta)
$$

Update rule:

$$
\beta \leftarrow \beta + \eta \cdot \frac{1}{n} X^\top (y - X\beta)
$$

**Why bother with GD when you have a closed form?**

- **Memory:** Closed form needs $X^\top X$ which is $p \times p$. GD only needs one row/batch at a time.
- **Scale:** For $p \gg 10^4$, matrix inversion is infeasible.
- **Streaming:** SGD can update online as new data arrives.
- **Regularization:** Easy to add L1 penalty with proximal gradient methods.

```python
# Manual GD for linear regression
def linreg_gd(X, y, lr=0.01, n_iter=1000):
    beta = np.zeros(X.shape[1])
    for _ in range(n_iter):
        grad = -X.T @ (y - X @ beta) / len(y)
        beta -= lr * grad
    return beta

# Scikit-learn's SGDRegressor — scales to millions of rows
from sklearn.linear_model import SGDRegressor
model = SGDRegressor(loss='squared_error', penalty='l2', max_iter=1000).fit(X, y)
```

---

## Q13. What is R² and what does it NOT tell you? { #q13 }

$$
R^2 = 1 - \frac{\text{SS}_{\text{res}}}{\text{SS}_{\text{tot}}}
$$

where $\text{SS}_{\text{res}} = \sum (y_i - \hat{y}_i)^2$ and $\text{SS}_{\text{tot}} = \sum (y_i - \bar{y})^2$.

**What R² tells you:** Fraction of variance in $y$ explained by the model (on *this* dataset).

**What R² does NOT tell you:**

- Whether your model is correctly specified.
- Whether predictions are unbiased (a biased model can have high R²).
- Whether your model will generalize.
- Whether your coefficients are statistically significant.
- **Adding features always increases R²**, even if they're random noise. Use **adjusted R²** for model comparison with different feature counts:

$$
R^2_{\text{adj}} = 1 - (1 - R^2) \cdot \frac{n - 1}{n - p - 1}
$$

<div class="tip-box" markdown>
**Interviewer probe:** "I got R² = 0.95 on my model. Is it good?" → Good answer: *"Depends on the problem. For physics, 0.95 might be low; for social science, high. But more important: is it 0.95 on training or held-out data? And does the residual plot look random?"*
</div>

---

## Q14. When would you use a linear model over a neural net or gradient boosting? { #q14 }

Linear models win when:

| Scenario | Why linear wins |
|---|---|
| **Interpretability is legally required** (credit, healthcare) | Coefficients are directly interpretable; GBMs need SHAP |
| **Small data** (< 1000 rows) | Linear models have far less overfitting risk |
| **High-dim sparse data** (text, one-hot) | Scales well with huge $p$; fast to train |
| **Strictly monotonic relationships** with explicit effects | Linear captures them cleanly |
| **Low latency, low memory deployment** | A linear model is just a dot product |
| **Clear hypothesis testing** (does feature X matter?) | Linear model gives p-values; tree-based don't |
| **Baseline before trying anything fancy** | Always start here |

**Concrete examples:**

- Credit scoring (FICO is essentially logistic regression + fair lending compliance).
- Online advertising (logistic regression on hashed features, billions of rows/day).
- Epidemiology (needs interpretable effect sizes).
- Survival analysis (Cox proportional hazards is GLM-adjacent).

---

## Q15. Explain the bias-variance tradeoff for regularized linear regression. { #q15 }

**Unregularized OLS:** Low bias (unbiased estimator), variable variance (high when $p$ is large or features are collinear).

**As $\lambda$ increases (more regularization):**

- **Bias** increases — coefficients shrink toward zero, model becomes more wrong on the "true" relationship.
- **Variance** decreases — model is less sensitive to specific data points.

```
Error = Bias² + Variance + Noise

λ = 0  (OLS)      → Bias² small, Variance large
λ → ∞             → Bias² large,  Variance small
λ* (cross-validated) → sweet spot
```

Mathematically for Ridge, the coefficient estimate is:

$$
\hat{\beta}_{\text{ridge}} = (X^\top X + \lambda I)^{-1} X^\top y
$$

$\mathbb{E}[\hat{\beta}_{\text{ridge}}] = (X^\top X + \lambda I)^{-1} X^\top X \beta \neq \beta$ → biased.

But $\text{Var}(\hat{\beta}_{\text{ridge}}) < \text{Var}(\hat{\beta}_{\text{OLS}})$ → lower variance.

**In practice:** Use `RidgeCV` / `LassoCV` / `ElasticNetCV` — they sweep $\lambda$ over a grid and pick via cross-validation, handling the tradeoff for you.

```python
from sklearn.linear_model import RidgeCV
alphas = np.logspace(-3, 3, 50)
model = RidgeCV(alphas=alphas, cv=5).fit(X, y)
print(f"Optimal alpha: {model.alpha_}")
```
