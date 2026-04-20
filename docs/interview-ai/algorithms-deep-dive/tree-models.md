# Module 2 — Tree Ensembles

**Questions 16–35.** Decision trees, Random Forest, Gradient Boosting, and the XGBoost / LightGBM / CatBoost trinity. If your role touches tabular data, **this is the module you master**. Every Kaggle competition winner since 2017 has used some variant of gradient boosting.

---

## Q16. How does a decision tree choose its splits? Derive Gini and entropy. { #q16 }

**Core idea.** At each node, pick the feature and threshold that produces the "purest" child nodes.

**Impurity measures** for classification — assume `p_k` is proportion of class `k` in a node:

**Gini impurity:**

\[
G = 1 - \sum_k p_k^2
\]

**Entropy (log base 2):**

\[
H = -\sum_k p_k \log_2 p_k
\]

**Information gain** for a split:

\[
IG = H(parent) - \sum_{child} \frac{n_{child}}{n_{parent}} H(child)
\]

Pick the split with maximum IG (or equivalently, minimum weighted child impurity).

**For regression:** use *variance reduction*:

\[
\text{Var-reduction} = Var(parent) - \sum_{child} \frac{n_{child}}{n_{parent}} Var(child)
\]

**Gini vs Entropy — practical notes:**

- Gini is faster (no log).
- They agree ~99% of the time.
- Entropy slightly favors more balanced splits. Gini slightly favors splits that isolate one class.
- Use default (Gini in sklearn, Histogram in LightGBM) unless you have a specific reason.

```python
from sklearn.tree import DecisionTreeClassifier, export_text

tree = DecisionTreeClassifier(
    criterion='gini',     # or 'entropy'
    max_depth=5,
    min_samples_split=20,
    random_state=42,
)
tree.fit(X_train, y_train)
print(export_text(tree, feature_names=feature_names))
```

<div class="tip-box" markdown>
**Interviewer follow-up:** "Why doesn't the tree consider all possible splits?" — For continuous features, it *does* sort values and consider thresholds between consecutive distinct values. For high-cardinality categoricals, modern implementations (LightGBM) sort by target mean and split on quantiles.
</div>

---

## Q17. What's the difference between ID3, C4.5, and CART? { #q17 }

| | ID3 (1986) | C4.5 (1993) | CART (1984) |
|---|---|---|---|
| **Splits** | Multi-way | Multi-way | Binary only |
| **Criterion** | Information gain | Gain ratio | Gini / variance |
| **Handles continuous?** | No | Yes | Yes |
| **Handles missing?** | No | Yes (weights) | Yes (surrogates) |
| **Pruning** | None | Pessimistic error | Cost-complexity |
| **Output** | Classification | Classification | Both |

**scikit-learn and modern libraries use CART** — binary, handles both tasks, supports pruning.

**Why gain ratio?** Information gain biases toward features with many categories (e.g., unique ID). Gain ratio normalizes by the entropy of the split itself:

\[
GainRatio = \frac{IG}{-\sum_i \frac{n_i}{n} \log_2 \frac{n_i}{n}}
\]

This penalizes splits that produce many small children.

---

## Q18. How do you control overfitting in a decision tree? { #q18 }

Trees overfit almost by design — without constraints, they grow until every leaf has one sample.

**Pre-pruning (stop growing early):**

- `max_depth` — caps tree depth. Most common knob.
- `min_samples_split` — don't split nodes with fewer samples.
- `min_samples_leaf` — each leaf must have ≥ k samples.
- `max_features` — consider only a random subset of features per split (used in Random Forest).
- `min_impurity_decrease` — skip splits that improve impurity by less than threshold.

**Post-pruning:**

- **Cost-complexity pruning** (CART): minimize `total_impurity + α × num_leaves`. Increase α to prune more aggressively.

```python
from sklearn.tree import DecisionTreeClassifier

# Get the cost-complexity path
tree = DecisionTreeClassifier(random_state=42)
path = tree.cost_complexity_pruning_path(X_train, y_train)
alphas = path.ccp_alphas

# CV over alphas to find best
from sklearn.model_selection import cross_val_score

best_score = -1
for alpha in alphas:
    t = DecisionTreeClassifier(ccp_alpha=alpha, random_state=42)
    score = cross_val_score(t, X_train, y_train, cv=5).mean()
    if score > best_score:
        best_score, best_alpha = score, alpha

final = DecisionTreeClassifier(ccp_alpha=best_alpha).fit(X_train, y_train)
```

<div class="scenario" markdown>
**Reality check:** for a *single tree*, heavy regularization helps. In an *ensemble* (RF, GBM), individual trees are often intentionally shallow (depth 3-8 for GBM, unconstrained for RF) and the ensemble handles variance.
</div>

---

## Q19. Explain Random Forest from first principles. Why does averaging trees work? { #q19 }

**Recipe (Breiman 2001):**

1. Bootstrap sample (with replacement) the training data.
2. Train a tree on that sample, but at each split consider only `√p` (classification) or `p/3` (regression) randomly chosen features.
3. Repeat for `n_estimators` trees.
4. Predict by majority vote (classification) or mean (regression).

**Two sources of diversity:** bootstrap samples + random feature selection at splits.

**Why it works:**

Averaging `T` identically distributed but correlated variables with variance `σ²` and pairwise correlation `ρ` gives:

\[
Var(\bar{X}) = \rho \sigma^2 + \frac{1-\rho}{T} \sigma^2
\]

As `T → ∞`, variance approaches `ρσ²`. **The random feature selection reduces `ρ`**, which is why RF beats bagged trees (which keep all features).

**Practical gotchas:**

- `n_estimators` — more is better, but returns diminish after ~500.
- `max_features` — the key knob. Reduce to inject more diversity.
- **Out-of-bag (OOB) score** — each sample is OOB for ~37% of trees; use this for free CV.
- `n_jobs=-1` — trivially parallel.

```python
from sklearn.ensemble import RandomForestClassifier

rf = RandomForestClassifier(
    n_estimators=500,
    max_features='sqrt',
    max_depth=None,          # grow fully; variance is handled by averaging
    min_samples_leaf=5,
    n_jobs=-1,
    oob_score=True,
    random_state=42,
)
rf.fit(X_train, y_train)
print(f"OOB score: {rf.oob_score_:.4f}")
```

---

## Q20. Gradient Boosting — walk through one boosting iteration. { #q20 }

**Gradient Boosting (Friedman 1999) — the algorithm:**

1. Initialize model `F_0(x)` (e.g., mean of `y` for regression, log-odds for classification).
2. For `m = 1 ... M`:
   a. Compute **residuals** = negative gradient of loss w.r.t. current predictions:

\[
r_{im} = -\left[ \frac{\partial L(y_i, F(x_i))}{\partial F(x_i)} \right]_{F=F_{m-1}}
\]

   b. Fit a regression tree `h_m(x)` to these residuals.

   c. Find optimal step size `γ_m` (line search).

   d. Update: `F_m(x) = F_{m-1}(x) + η · γ_m · h_m(x)` where `η` is the learning rate.

**For squared error loss**, the negative gradient *is* the residual `y - F(x)` — hence the name "gradient boosting" generalizes this beyond squared error.

**For logistic loss** (binary classification), the negative gradient is `y - σ(F(x))` — the probability error.

**Key insight:** each tree fits the *errors the previous ensemble is still making*. You're doing functional gradient descent in model space.

```python
from sklearn.ensemble import GradientBoostingClassifier

gbm = GradientBoostingClassifier(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=4,              # weak learners
    subsample=0.8,            # stochastic gradient boosting
    random_state=42,
)
gbm.fit(X_train, y_train)
```

<div class="tip-box" markdown>
**Interviewer probe:** "Why small learning rate + many trees?" — Shrinkage. Smaller steps allow the ensemble to correct itself. Friedman's paper showed `η = 0.1` with 500 trees consistently beats `η = 1` with 50 trees.
</div>

---

## Q21. XGBoost — what are the key innovations over vanilla GBM? { #q21 }

XGBoost (Chen & Guestrin, 2016) adds several breakthroughs:

**1. Second-order Taylor expansion of loss.**

Vanilla GBM uses first-order gradient. XGBoost uses both gradient `g_i` and hessian `h_i`:

\[
L^{(t)} \approx \sum_i \left[ g_i f_t(x_i) + \frac{1}{2} h_i f_t(x_i)^2 \right] + \Omega(f_t)
\]

This gives a better step direction, especially for non-squared losses.

**2. Regularized tree objective.**

\[
\Omega(f) = \gamma T + \frac{1}{2} \lambda \|w\|^2
\]

where `T` is number of leaves, `w` are leaf weights. Penalizes complex trees directly.

**3. Optimal leaf weights in closed form:**

\[
w^*_j = -\frac{\sum_{i \in j} g_i}{\sum_{i \in j} h_i + \lambda}
\]

**4. Split finding with gain formula:**

\[
Gain = \frac{1}{2} \left[ \frac{G_L^2}{H_L + \lambda} + \frac{G_R^2}{H_R + \lambda} - \frac{(G_L + G_R)^2}{H_L + H_R + \lambda} \right] - \gamma
\]

Prune split if Gain < 0.

**5. System optimizations.**

- **Sparsity-aware split finding** — handles missing values natively by learning a default direction.
- **Weighted quantile sketch** — approximate split finding for large data.
- **Parallel column blocks** — enables parallel tree construction.
- **Cache-aware access** — a huge real-world speedup.
- **External memory (out-of-core)** — train on datasets larger than RAM.

```python
import xgboost as xgb

model = xgb.XGBClassifier(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=6,
    reg_alpha=0.1,           # L1 regularization
    reg_lambda=1.0,          # L2 regularization
    gamma=0.1,               # min gain to split
    subsample=0.8,
    colsample_bytree=0.8,
    tree_method='hist',      # histogram-based (fast)
    device='cuda',           # or 'cpu'
    early_stopping_rounds=50,
    eval_metric='logloss',
)
model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
```

---

## Q22. LightGBM — what's different from XGBoost and why is it faster? { #q22 }

LightGBM (Ke et al., 2017) shares the XGBoost foundation but adds three key tricks:

**1. Histogram-based splits (faster than XGBoost's level-wise hist).**

Bins continuous features into 255 discrete bins. Split finding operates on bins, not raw values. Memory: O(bins × features) instead of O(samples × features).

**2. Leaf-wise tree growth (vs level-wise).**

| Strategy | Behavior | Pro | Con |
|---|---|---|---|
| **Level-wise** (XGBoost default) | Expand all leaves at current depth before going deeper | Balanced tree | Sometimes expands low-gain leaves |
| **Leaf-wise** (LightGBM default) | Always expand the leaf with highest gain | Converges faster with fewer leaves | Can overfit on small datasets → need `num_leaves` control |

**3. GOSS (Gradient-based One-Side Sampling).**

Instead of using all samples for split finding:

- Keep all samples with large gradients (the "difficult" ones).
- Randomly sample the small-gradient ones.
- Weighted so the split-finding estimate stays unbiased.

Typically 5-10x speedup with < 1% accuracy loss.

**4. EFB (Exclusive Feature Bundling).**

In sparse feature spaces (e.g., one-hot encoded data), many features are mutually exclusive (never non-zero for the same sample). LightGBM bundles them into a single feature → dramatically reduces effective dimensionality.

**When LightGBM wins:**

- Large datasets (millions of rows).
- Sparse features (lots of categoricals).
- Fast experimentation — LightGBM often trains 5-10x faster than XGBoost.

**When XGBoost still wins:**

- Small-to-medium datasets where leaf-wise overfits.
- When reproducibility across platforms is critical.

```python
import lightgbm as lgb

model = lgb.LGBMClassifier(
    n_estimators=500,
    learning_rate=0.05,
    num_leaves=63,          # key knob for leaf-wise; 2^max_depth - 1
    max_depth=-1,           # unlimited (controlled by num_leaves)
    min_child_samples=20,
    reg_alpha=0.1,
    reg_lambda=1.0,
    colsample_bytree=0.8,
    subsample=0.8,
    subsample_freq=5,
    random_state=42,
)
model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)],
)
```

<div class="tip-box" markdown>
**Interview shortcut answer:** "LightGBM = XGBoost + histogram + leaf-wise + GOSS. Usually 5–10x faster, small accuracy tradeoff on tiny datasets, often better on large ones."
</div>

---

## Q23. CatBoost — why and when? { #q23 }

CatBoost (Yandex, 2017) targets the **categorical feature problem** that plagues XGBoost/LightGBM with large-cardinality categoricals.

**Innovations:**

**1. Ordered Target Statistics (to prevent target leakage).**

Standard target encoding leaks: encoding uses the row's own target. CatBoost uses a **random permutation** of the data and computes target statistics using *only previous* rows in that ordering.

**2. Ordered boosting.**

Standard boosting leaks similarly: gradients are computed on the same data used to train trees. CatBoost maintains multiple supporting models, each trained on a different permutation, to compute unbiased gradients.

**3. Symmetric (oblivious) trees.**

All nodes at the same depth use the **same split**. Makes inference ~100x faster (one comparison per level, no branching). Also a form of regularization.

**4. GPU support for both training and inference.**

**When CatBoost shines:**

- Tabular data with many high-cardinality categoricals (user IDs, zip codes, product IDs).
- You need out-of-the-box performance without heavy feature engineering.
- Inference latency matters.

**When it doesn't win:**

- Pure numeric tabular data — XGBoost/LightGBM often match or beat it.
- Enormous datasets where training time dominates (LightGBM usually wins).

```python
from catboost import CatBoostClassifier

cat_features = ['city', 'product_id', 'device_type']

model = CatBoostClassifier(
    iterations=500,
    learning_rate=0.05,
    depth=6,
    cat_features=cat_features,  # automatic encoding
    l2_leaf_reg=3,
    early_stopping_rounds=50,
    verbose=0,
)
model.fit(X_train, y_train, eval_set=(X_val, y_val))
```

---

## Q24. How does LightGBM handle categorical features natively? { #q24 }

LightGBM can handle categoricals without one-hot:

**Algorithm (Fisher 1958, applied to GBM):**

1. For each node, for each categorical feature:
2. Compute sum of gradients for each category.
3. Sort categories by `(sum_grad) / (sum_hess + λ)`.
4. Find the best binary split point along this sorted order.

This is **O(k log k)** where k is number of categories — dramatically better than O(2^k) for exact categorical splits.

```python
import lightgbm as lgb

# Tell LightGBM which features are categorical
model = lgb.LGBMClassifier()
model.fit(
    X_train, y_train,
    categorical_feature=['city', 'device'],  # pass feature names or indices
)

# Internally, LightGBM encodes categoricals as integers
# Make sure you pass them as 'category' dtype for pandas integration:
X_train['city'] = X_train['city'].astype('category')
```

**Caveats:**

- Requires `min_data_per_group` to avoid overfitting on rare categories (default: 100).
- For high-cardinality (> 1000 categories), target encoding with smoothing often beats native handling.
- Not well-supported in XGBoost (you still need encoding).

---

## Q25. Why do gradient boosting and Random Forest have such different recommended depths? { #q25 }

| | Random Forest | Gradient Boosting |
|---|---|---|
| **Typical depth** | None (grow fully) | 3-8 |
| **Trees are…** | Fully-grown overfit trees | Weak learners |
| **Variance control** | Averaging + feature sampling | Small learning rate + many trees |
| **Bias control** | Already low from unconstrained trees | Many rounds of residual fitting |

**RF logic:** Each tree is a low-bias high-variance estimator. Averaging many such trees reduces variance without increasing bias → grow trees as deep as possible.

**GBM logic:** Each tree is a *correction* on the residuals. A deep tree could memorize residuals and leave nothing for subsequent trees to learn. Shallow trees plus many rounds create a strong *ensemble* even though each component is weak.

**Deep-tree GBM pitfall:** if you set `max_depth=20` in XGBoost, the first few trees fit the training data perfectly → subsequent trees have nothing to boost → early stopping kicks in at iteration 5 → underfit ensemble.

<div class="tip-box" markdown>
**Quick rule:** RF → `max_depth=None, min_samples_leaf=5`. GBM → `max_depth=6, learning_rate=0.05, n_estimators=500, early_stopping=50`.
</div>

---

## Q26. How do gradient boosting libraries handle missing values natively? { #q26 }

**XGBoost & LightGBM: "default direction" trick.**

At each split, the algorithm tries sending missing values to both the left and right child and picks whichever direction gives higher gain. This is stored with the split. At inference, missing values automatically take the learned default direction.

**Why it works:** missingness is often informative. If users who don't fill the "income" field are more likely to default, the tree learns to route them toward the "default" leaf without needing explicit imputation.

**CatBoost:** Three modes:

- `Min` — treat missing as less than any observed value.
- `Max` — treat as greater than any observed value.
- `Forbidden` — raise an error.

**When you should still impute:**

- If missingness is truly random and adds noise.
- If you're combining tree-based with linear model in stacking.
- If you have domain knowledge about better imputation (e.g., median by group).

```python
# XGBoost just works
model = xgb.XGBClassifier()
model.fit(X_with_nans, y)  # handles NaN directly

# But linear models cannot — impute first
from sklearn.impute import SimpleImputer
X_imputed = SimpleImputer(strategy='median').fit_transform(X_with_nans)
```

<div class="scenario" markdown>
**Production gotcha:** during training, a feature has 5% NaN. In production, a pipeline bug starts sending 50% NaN. The model silently routes them all one way — sometimes catastrophically. Add a check: alert if a feature's NaN rate shifts by more than 20%.
</div>

---

## Q27. What's early stopping in gradient boosting and how do you do it correctly? { #q27 }

**Idea:** stop adding trees when validation performance stops improving.

**Correct implementation:**

1. Split training data into train + validation.
2. Pass validation set to `fit` along with `early_stopping_rounds=50`.
3. Library monitors validation score; stops when no improvement for 50 rounds.
4. Returns the model at the **best iteration**, not the latest.

```python
import lightgbm as lgb

model = lgb.LGBMClassifier(
    n_estimators=2000,        # upper bound, not actual number used
    learning_rate=0.05,
)
model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    eval_metric='auc',
    callbacks=[
        lgb.early_stopping(stopping_rounds=50),
        lgb.log_evaluation(period=100),
    ],
)
print(f"Best iteration: {model.best_iteration_}")
```

**Common mistakes:**

1. **Using test set as validation.** Creates leakage. Test set must be untouched.
2. **`early_stopping_rounds` too small.** 10 rounds is too tight; use 50-100.
3. **Not returning best iteration.** Modern libraries do this automatically, but double-check.
4. **Mismatch between training metric and eval_metric.** The library optimizes training loss but monitors eval metric — ensure they're consistent (e.g., don't train on log-loss but early-stop on AUC unless intentional).
5. **Different preprocessing on train vs val.** Train/val must come from the same preprocessing pipeline.

---

## Q28. Explain SHAP values for tree models. Why are they unique? { #q28 }

**Problem:** feature importance in trees is not well-defined. Gain, split-count, and permutation importance give different answers.

**SHAP (SHapley Additive exPlanations)** uses cooperative game theory:

\[
\phi_i = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|! (|F| - |S| - 1)!}{|F|!} \left[ f(S \cup \{i\}) - f(S) \right]
\]

Each feature's SHAP value is its **average marginal contribution** across all possible feature orderings.

**Properties that make SHAP unique** (Shapley's original axioms):

1. **Efficiency:** `Σ φ_i = f(x) - E[f(X)]` → SHAP values sum to the prediction minus baseline.
2. **Symmetry:** two features contributing equally get equal SHAP values.
3. **Dummy:** a feature that doesn't affect the model gets SHAP = 0.
4. **Additivity:** for an ensemble, SHAP of the sum = sum of SHAPs.

**Why trees are easy for SHAP:** Lundberg's TreeSHAP algorithm computes exact Shapley values in O(TLD²) per prediction (T = trees, L = leaves, D = depth) — **polynomial** in tree size, vs exponential in general.

```python
import shap

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# Global importance: mean |SHAP| per feature
shap.summary_plot(shap_values, X_test, plot_type='bar')

# Local explanation for one prediction
shap.force_plot(
    explainer.expected_value,
    shap_values[0],
    X_test.iloc[0]
)

# Feature interactions
interaction = explainer.shap_interaction_values(X_test[:100])
```

<div class="tip-box" markdown>
**Senior signal:** "I prefer SHAP over permutation importance because it respects feature interactions and gives local explanations. But I cross-check — if SHAP global and permutation disagree strongly, that's a signal of data issue (leakage or unstable features)."
</div>

---

## Q29. Why do gradient boosting models often need probability calibration? { #q29 }

**The issue:** GBM optimizes log-loss, which *should* give calibrated probabilities — but several things distort it in practice:

1. **Early stopping** halts optimization before full calibration.
2. **Class weights or `scale_pos_weight`** for imbalanced data create systematic bias.
3. **Subsampling** (`subsample < 1`) introduces noise that tilts probabilities.
4. **Multiple trees averaging** creates S-shaped distortion near 0 and 1.

**Diagnostic:** plot a **reliability diagram**. Bucket predictions by score, plot mean predicted vs mean actual.

```python
from sklearn.calibration import calibration_curve
import matplotlib.pyplot as plt

prob_pos = model.predict_proba(X_val)[:, 1]
fraction_pos, mean_pred = calibration_curve(y_val, prob_pos, n_bins=10)

plt.plot(mean_pred, fraction_pos, marker='o', label='Model')
plt.plot([0, 1], [0, 1], '--', label='Perfect')
plt.xlabel('Predicted probability')
plt.ylabel('Actual frequency')
```

**If miscalibrated → fix with:**

1. **Platt scaling** (logistic regression on top of model scores). Good for small validation sets.
2. **Isotonic regression** — non-parametric monotonic mapping. Needs more data (~1000+), but handles arbitrary miscalibration.

```python
from sklearn.calibration import CalibratedClassifierCV

# Wrap the trained model with calibration
calibrated = CalibratedClassifierCV(model, method='isotonic', cv='prefit')
calibrated.fit(X_val, y_val)

# Use calibrated probabilities
probs = calibrated.predict_proba(X_test)[:, 1]
```

<div class="scenario" markdown>
**Why it matters in production:** for fraud, pricing, medical diagnosis — you need *probabilities*, not just rankings. If you say "8% default probability" and actual default for that score bucket is 25%, you're catastrophically underpricing risk.
</div>

---

## Q30. Feature importance — gain, split, permutation, SHAP. When to use which? { #q30 }

| Method | Measures | Pros | Cons |
|---|---|---|---|
| **Gain (default in XGBoost/LGBM)** | Total reduction in loss from splits on this feature | Fast, built-in | Biased toward high-cardinality continuous features |
| **Split count / Frequency** | How often the feature is used for splitting | Fast | Same bias; doesn't account for split depth |
| **Permutation importance** | Drop in performance when feature is shuffled | Model-agnostic, less biased | Slow, unstable with correlated features (both get deflated) |
| **SHAP** | Average marginal contribution | Theoretically principled, decomposable | Slowest; requires shap library |

**Practical workflow:**

1. **Fast first pass:** gain importance to rank features.
2. **Cross-check:** permutation importance on a subset of top features. Big disagreements = red flag.
3. **Interpretation / auditing:** SHAP for local and global explanation.
4. **Feature selection:** combine — drop features where all methods agree it's near-zero.

```python
# Gain (built-in)
import pandas as pd
gain_imp = pd.Series(model.feature_importances_, index=feature_names).sort_values()

# Permutation
from sklearn.inspection import permutation_importance
perm = permutation_importance(model, X_val, y_val, n_repeats=10, n_jobs=-1)
perm_imp = pd.Series(perm.importances_mean, index=feature_names).sort_values()

# SHAP
import shap
explainer = shap.TreeExplainer(model)
shap_vals = explainer.shap_values(X_val[:5000])
shap_imp = pd.Series(np.abs(shap_vals).mean(0), index=feature_names).sort_values()

# Compare
comparison = pd.concat([gain_imp, perm_imp, shap_imp], axis=1,
                       keys=['gain', 'permutation', 'shap'])
```

<div class="tip-box" markdown>
**Common interview trap:** "Feature X has highest gain importance, so it's the most important, right?" — Wrong. Gain is biased toward features with many possible splits (high-cardinality, continuous). A permutation or SHAP cross-check might reveal the "important" feature is actually noise.
</div>

---

## Q31. XGBoost: what does the `dart` booster do? When is it useful? { #q31 }

**DART (Dropouts meet Multiple Additive Regression Trees)** — Vinayak & Gilad-Bachrach, 2015.

**Idea:** apply dropout (as in neural networks) to boosting trees. At each iteration:

1. Randomly drop a fraction of existing trees.
2. Fit a new tree to residuals *from the reduced ensemble*.
3. Rescale new tree and kept-dropped trees so the total prediction stays consistent.

**Why it helps:** classical GBM suffers from **over-specialization** — later trees fit tiny refinements, making the ensemble sensitive to early trees. DART forces all trees to contribute meaningfully.

**When to use DART:**

- Noisy data where standard GBM overfits residuals.
- Medium-sized datasets (10K-500K rows).
- When ensemble is stuck plateauing despite more rounds.

**Costs:**

- Trains slower (same number of trees = more work per tree).
- Harder to use with early stopping (validation score is noisier).
- Inference is slightly slower (more trees needed to match GBM accuracy).

```python
import xgboost as xgb

model = xgb.XGBClassifier(
    booster='dart',
    rate_drop=0.1,           # probability of dropping each tree
    skip_drop=0.5,           # probability of skipping dropout this iteration
    normalize_type='tree',   # 'tree' or 'forest'
    n_estimators=500,
    learning_rate=0.05,
)
```

---

## Q32. What's the relationship between XGBoost / LightGBM regularization parameters (α, λ, γ)? { #q32 }

Three knobs with distinct roles:

**`reg_alpha` (L1 regularization on leaf weights):**

- Adds `α × Σ|w_j|` penalty.
- Pushes leaf weights toward zero — essentially drops leaves.
- Creates sparse trees.

**`reg_lambda` (L2 regularization on leaf weights):**

- Adds `(λ/2) × Σw_j²`.
- Shrinks leaf weights smoothly.
- Default in XGBoost is `λ=1` — a small amount is almost always on.

**`gamma` (minimum loss reduction to split, XGBoost only):**

- Controls the **tree structure**, not the weights.
- A split is only made if it improves loss by at least `γ`.
- Higher γ → shallower trees with fewer splits.

**LightGBM equivalents:**

- `lambda_l1` = `reg_alpha`
- `lambda_l2` = `reg_lambda`  
- `min_gain_to_split` = `gamma`

**Tuning hierarchy for tree models:**

1. First: `n_estimators`, `learning_rate` (with early stopping — free).
2. Second: `max_depth` / `num_leaves` — biggest effect on complexity.
3. Third: `min_child_weight` / `min_data_in_leaf`.
4. Fourth: `subsample`, `colsample_bytree` for variance.
5. Last (fine-tuning): `reg_alpha`, `reg_lambda`, `gamma`.

```python
# A sensible starting-point grid
grid = {
    'n_estimators': [500, 1000, 2000],   # with early stopping, just set high
    'learning_rate': [0.01, 0.05, 0.1],
    'max_depth': [4, 6, 8],
    'min_child_weight': [1, 5, 10],
    'subsample': [0.7, 0.8, 0.9],
    'colsample_bytree': [0.7, 0.8, 0.9],
    'reg_alpha': [0, 0.1, 1.0],
    'reg_lambda': [1.0, 5.0, 10.0],
}
```

<div class="tip-box" markdown>
**Pragmatic advice:** use Optuna or Bayesian optimization, not grid search — the space is too large. 100 Optuna trials typically beats 1000 grid points.
</div>

---

## Q33. How do you handle class imbalance in gradient boosting? { #q33 }

Four options with different tradeoffs:

**1. `scale_pos_weight` (XGBoost) or `is_unbalance=True` (LightGBM).**

Sets the loss weight of the positive class. Recommended: `count(neg) / count(pos)`.

- ✅ No data duplication.
- ❌ Miscalibrates probabilities — you'll need to calibrate post-hoc.

**2. Class weights sample-by-sample.**

Pass a `sample_weight` vector in `fit`. Most flexible, but same calibration caveat.

**3. Focal Loss (custom objective).**

\[
FL(p_t) = -(1 - p_t)^\gamma \log(p_t)
\]

Down-weights easy examples, focuses on hard ones. Available via custom objective.

**4. Sampling-based — oversample minority or undersample majority.**

- Undersampling majority: fast training, loses information.
- SMOTE: risky — GBM already handles imbalance well; SMOTE adds noise.

**Prefer `scale_pos_weight`** as the default — it's the cleanest.

```python
from sklearn.utils.class_weight import compute_sample_weight

# Option 1: XGBoost
import xgboost as xgb
spw = (y_train == 0).sum() / (y_train == 1).sum()
model = xgb.XGBClassifier(scale_pos_weight=spw, ...)

# Option 2: LightGBM
import lightgbm as lgb
model = lgb.LGBMClassifier(is_unbalance=True, ...)
# Or more explicitly:
# model = lgb.LGBMClassifier(class_weight='balanced', ...)

# Option 3: Custom sample weights
sample_weights = compute_sample_weight('balanced', y_train)
model.fit(X_train, y_train, sample_weight=sample_weights)
```

<div class="scenario" markdown>
**Real scenario:** fraud detection with 0.1% positive rate. `scale_pos_weight=999` tempts the model to flag everything as positive. Always tune `scale_pos_weight` in CV — smaller values (like `sqrt(999) ≈ 31`) often work better than the raw ratio.
</div>

---

## Q34. Stacking vs blending vs voting — how do they differ? { #q34 }

Three ways to combine models:

**1. Voting (simplest):**

- Hard voting: majority of class predictions.
- Soft voting: average of predicted probabilities.

```python
from sklearn.ensemble import VotingClassifier

voting = VotingClassifier(
    estimators=[('lgb', lgb_model), ('xgb', xgb_model), ('lr', lr_model)],
    voting='soft',
    weights=[2, 2, 1],
)
```

**2. Blending:**

- Split train into train + holdout.
- Train base models on train.
- Base models predict on holdout.
- Train a *meta-learner* on (base-model predictions, labels) from holdout.

Fast, simple, but only uses one holdout for the meta-learner.

**3. Stacking (proper):**

- Use k-fold out-of-fold predictions from base models on the full training set.
- Meta-learner trained on these out-of-fold predictions.
- Uses all data for both base and meta, but requires more code.

```python
from sklearn.ensemble import StackingClassifier

stack = StackingClassifier(
    estimators=[('lgb', lgb_model), ('xgb', xgb_model), ('rf', rf_model)],
    final_estimator=LogisticRegression(),
    cv=5,                    # out-of-fold CV for base predictions
    stack_method='predict_proba',
    n_jobs=-1,
)
```

**When stacking wins:**

- Base models are **diverse** (different algorithm families). Stacking 3 LightGBMs with different seeds rarely helps.
- You have enough data — stacking overfits on small data.
- The meta-learner is simple (logistic regression) — complex meta-learners overfit the base model errors.

**Real-world tradeoff:**

- Production cost: stacking requires N + 1 models served, N + 1 inferences, N + 1 monitoring pipelines.
- Usually, a well-tuned single LightGBM is within 0.5% of a stacked ensemble, at 1/N the cost.

<div class="tip-box" markdown>
**Senior signal:** "Stacking is a Kaggle tool, not usually a production tool. I use it when the accuracy gain justifies 3x infrastructure cost — rare in practice."
</div>

---

## Q35. GBM inference is slow in production — how do you speed it up? { #q35 }

Five techniques, ranked by effort:

**1. Fewer trees via early stopping (free).**

If your model uses 1000 trees but the best iteration is 450, truncate to 450.

**2. Lower `max_depth` (small accuracy tradeoff).**

Going from depth 8 to 5 ~halves tree traversal time. Retraining shows accuracy drop — accept if small.

**3. Model distillation.**

Train a smaller GBM (or even a linear model) on the predictions of the big one.

```python
# Large "teacher" model
teacher = lgb.LGBMClassifier(n_estimators=1000, max_depth=8).fit(X_train, y_train)
teacher_probs = teacher.predict_proba(X_train)[:, 1]

# Small "student" fit on teacher probabilities
student = lgb.LGBMRegressor(n_estimators=100, max_depth=4).fit(X_train, teacher_probs)
# Distillation often gives 90%+ of teacher performance at 5-10x speed
```

**4. Compile to ONNX or Treelite.**

Treelite converts trees to optimized C code — 2-5x inference speedup.

```python
import treelite
import treelite.sklearn  # or treelite.xgboost, treelite.lightgbm

tree_model = treelite.Model.from_lightgbm(model.booster_)
tree_model.export_lib(toolchain='gcc', libpath='./model.so')
# Load and predict with treelite_runtime (Cython-optimized)
```

**5. GPU inference.**

For batch scoring of millions of rows, GPU inference via NVIDIA FIL or RAPIDS cuML is 10-100x faster.

**Benchmarks at typical scale (500-tree model, 100 features):**

| Approach | Latency / prediction |
|---|---|
| Raw LightGBM predict | 30 µs |
| LightGBM + treelite | 8 µs |
| Distilled + treelite | 2 µs |
| GPU batch of 1M | 0.05 µs |

<div class="scenario" markdown>
**Real production story:** ad ranking system needed sub-5ms model inference. Trained a 500-tree LightGBM (great accuracy, 25ms latency). Distilled to a 50-tree student (0.3% AUC drop, 3ms latency). Shipped the student. Model lifespan: 3 years.
</div>
