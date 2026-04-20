# Module 2 — Tree-Based Models

Twenty-five questions. Decision trees and their ensembles (Random Forest, XGBoost, LightGBM, CatBoost) are the *most asked* algorithms in ML interviews because they're the dominant production choice for tabular data.

---

## Q16. How does a decision tree make a split? Explain Gini vs Entropy. { #q16 }

At each node, the tree considers all features and all possible split points, picking the one that **maximizes purity gain** in the children.

**Gini impurity** for a node with class proportions $p_k$:

$$
\text{Gini} = 1 - \sum_{k=1}^{K} p_k^2
$$

**Entropy:**

$$
H = -\sum_{k=1}^{K} p_k \log_2 p_k
$$

**Information gain** for a split:

$$
\text{Gain} = H_{\text{parent}} - \sum_{c \in \text{children}} \frac{n_c}{n_{\text{parent}}} H_c
$$

| Criterion | Range | Behavior | Speed |
|---|---|---|---|
| Gini | [0, 0.5] for binary | Isolates majority class; slightly favors frequent classes | Faster (no log) |
| Entropy | [0, 1] for binary | More sensitive to class distribution changes | Slightly slower |

In practice, **results are nearly identical**. Gini is the sklearn default because it's computationally cheaper.

```python
from sklearn.tree import DecisionTreeClassifier

tree = DecisionTreeClassifier(criterion='gini', max_depth=5).fit(X, y)
# or criterion='entropy' / 'log_loss'
```

---

## Q17. How does a regression tree split? { #q17 }

Instead of purity, regression trees minimize **variance** (or equivalently MSE) in the children:

$$
\text{MSE}_{\text{node}} = \frac{1}{n} \sum_{i \in \text{node}} (y_i - \bar{y}_{\text{node}})^2
$$

The split that minimizes the weighted sum of children's MSE wins:

$$
\Delta \text{MSE} = \text{MSE}_{\text{parent}} - \sum_c \frac{n_c}{n_p} \text{MSE}_c
$$

Each leaf predicts the **mean** of its training samples. For `criterion='absolute_error'`, it predicts the median instead (robust to outliers).

```python
from sklearn.tree import DecisionTreeRegressor
tree = DecisionTreeRegressor(criterion='squared_error', max_depth=5).fit(X, y)
```

---

## Q18. Why is a single decision tree a bad model? { #q18 }

**Four weaknesses:**

1. **High variance.** Trees are sensitive to small data changes — flip one training example and a split might change, cascading into a completely different tree.
2. **Axis-aligned splits.** Trees can't draw diagonal boundaries. A rotated decision boundary requires a deep, jagged staircase.
3. **Greedy splits.** The algorithm is locally optimal at each node, not globally optimal.
4. **Easy to overfit.** Without depth limits, a tree can grow until every leaf has one sample — perfect train, terrible test.

**Fixes:**

- **Prune** aggressively (`max_depth`, `min_samples_leaf`, `min_samples_split`).
- **Post-pruning via cost-complexity** (`ccp_alpha`).
- **Ensemble** many trees — the whole point of Random Forest and boosting.

<div class="tip-box" markdown>
**Interview angle:** A single tree is *interpretable* but *weak*. An ensemble is *strong* but *less interpretable*. SHAP bridges the gap for boosted trees.
</div>

---

## Q19. What is bagging? How does Random Forest use it? { #q19 }

**Bagging** (Bootstrap Aggregating):

1. Draw $B$ bootstrap samples (sampling with replacement) from training data.
2. Train a model on each sample independently.
3. Average (regression) or majority-vote (classification) predictions.

**Why it works:** By the law of large numbers, averaging $B$ unbiased estimators with variance $\sigma^2$ and correlation $\rho$ gives variance $\rho \sigma^2 + \frac{(1-\rho)\sigma^2}{B}$. As $B \to \infty$, only the correlation-floor term remains.

**Random Forest** = bagging + **feature subsampling at each split**.

At each node, instead of considering all features, RF considers only a random subset (`max_features`). This *decorrelates* the trees — if one feature is dominant, different trees will be forced to use different features, pushing correlation $\rho$ down.

```python
from sklearn.ensemble import RandomForestClassifier

rf = RandomForestClassifier(
    n_estimators=500,
    max_features='sqrt',   # sqrt(p) for classification, p/3 for regression
    max_depth=None,        # grow deep
    n_jobs=-1,
    random_state=42
).fit(X, y)
```

**Typical hyperparameters:**

| Parameter | Default | Tune to |
|---|---|---|
| `n_estimators` | 100 | 500–2000 (diminishing returns) |
| `max_features` | `sqrt` | Smaller → more decorrelation |
| `max_depth` | None | Limit for regularization |
| `min_samples_leaf` | 1 | Larger → smoother predictions |

---

## Q20. Random Forest: what is OOB error and why is it useful? { #q20 }

**Out-of-Bag (OOB) error:**

Each bootstrap sample omits ~37% of training data (since $(1 - 1/n)^n \to 1/e \approx 0.368$). For each training point, about a third of the trees *didn't* see it during training — those trees can score it honestly.

OOB error is the mean error of these "held-out" predictions aggregated across the forest.

**Why it's useful:**

- **Free cross-validation.** No need to hold out data or run separate CV.
- **Computed during training** — no extra cost.
- Useful for tuning `n_estimators` — you can plot OOB error vs number of trees.

```python
rf = RandomForestClassifier(n_estimators=500, oob_score=True).fit(X, y)
print(f"OOB accuracy: {rf.oob_score_:.4f}")
```

!!! note
    OOB is slightly pessimistic (each prediction uses fewer trees than the full forest). For small forests, use real CV.

---

## Q21. Explain AdaBoost. How does it differ from bagging? { #q21 }

**AdaBoost** (Adaptive Boosting):

1. Initialize sample weights $w_i = 1/n$.
2. For $t = 1, \dots, T$:
   - Train a weak learner $h_t$ (usually a stump — depth-1 tree) on weighted data.
   - Compute weighted error: $\epsilon_t = \sum_i w_i \mathbb{1}[h_t(x_i) \neq y_i]$.
   - Compute model weight: $\alpha_t = \frac{1}{2} \ln \frac{1 - \epsilon_t}{\epsilon_t}$.
   - Update sample weights: $w_i \leftarrow w_i \cdot e^{-\alpha_t y_i h_t(x_i)}$, then normalize.
3. Final prediction: $H(x) = \text{sign}\left(\sum_t \alpha_t h_t(x)\right)$.

**Intuition:** Misclassified samples get more weight → next learner focuses on the hard cases. Confident correct learners get larger $\alpha$ in the final vote.

**Bagging vs boosting:**

| Dimension | Bagging (RF) | Boosting (AdaBoost, GBM) |
|---|---|---|
| Training | Parallel | Sequential |
| Focus | All samples equal | Hard samples emphasized |
| Reduces | Variance | Bias |
| Base learner | Deep (low bias, high var) | Shallow (stumps or depth-3) |
| Overfitting | Rare | Happens without regularization |
| Outlier sensitivity | Low | High (weights amplify outliers) |

---

## Q22. Explain Gradient Boosting in detail. { #q22 }

Gradient Boosting is AdaBoost generalized: instead of reweighting, we fit each learner to the **negative gradient** of the loss.

**For MSE loss:**

1. Initialize $F_0(x) = \bar{y}$.
2. For $m = 1, \dots, M$:
   - Compute pseudo-residuals: $r_{im} = y_i - F_{m-1}(x_i)$.
   - Fit a tree $h_m$ to predict these residuals.
   - Update: $F_m(x) = F_{m-1}(x) + \eta \cdot h_m(x)$, where $\eta$ is the learning rate.

For arbitrary differentiable loss $L$, the residual becomes the negative gradient:

$$
r_{im} = -\left[\frac{\partial L(y_i, F(x_i))}{\partial F(x_i)}\right]_{F = F_{m-1}}
$$

**The three knobs of gradient boosting:**

1. **Learning rate** ($\eta$, a.k.a. shrinkage) — smaller = more trees needed, usually better generalization. Typical: 0.01–0.1.
2. **Number of trees** ($M$) — more trees can overfit without shrinkage.
3. **Tree depth** — usually 3–8. Deeper trees capture interactions, but each tree does more of the work.

**Regularization tricks:**

- Shrinkage ($\eta < 1$).
- Subsampling (fit each tree on a random 50–80% of rows — "stochastic gradient boosting").
- Early stopping on validation loss.
- L1/L2 regularization on leaf values (XGBoost, LightGBM).

```python
from sklearn.ensemble import GradientBoostingClassifier

gbm = GradientBoostingClassifier(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=4,
    subsample=0.8,
    validation_fraction=0.1,
    n_iter_no_change=10  # early stopping
).fit(X, y)
```

---

## Q23. XGBoost: what makes it different from vanilla GBM? { #q23 }

XGBoost's key innovations:

1. **Second-order gradient information.** Vanilla GBM uses only the gradient; XGBoost uses **both gradient and Hessian** in its leaf-weight calculation, giving a better Newton-style update.

   Optimal leaf weight:
   $$
   w^* = -\frac{\sum g_i}{\sum h_i + \lambda}
   $$

2. **Regularization in the objective.** XGBoost minimizes:

   $$
   \mathcal{L} = \sum_i L(y_i, \hat{y}_i) + \gamma T + \frac{1}{2} \lambda \sum_j w_j^2
   $$

   where $T$ is the number of leaves, $\gamma$ penalizes tree complexity, and $\lambda$ is L2 on leaf weights.

3. **Sparsity-aware split finding.** Handles missing values natively — at each split, XGBoost learns a default direction (left or right) for missing values based on which gives higher gain.

4. **Pre-sorted and cached-block algorithm.** Sorts features once, reuses.

5. **Parallelization of split-finding** across features (trees are still sequential).

6. **Built-in early stopping, DART (dropout in trees), GPU support.**

```python
import xgboost as xgb

dtrain = xgb.DMatrix(X_train, label=y_train)
dval = xgb.DMatrix(X_val, label=y_val)

params = {
    'objective': 'binary:logistic',
    'learning_rate': 0.05,
    'max_depth': 6,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'reg_alpha': 0.1,    # L1
    'reg_lambda': 1.0,   # L2
    'gamma': 0.1,        # min split loss
    'eval_metric': 'auc'
}

model = xgb.train(
    params, dtrain,
    num_boost_round=1000,
    evals=[(dval, 'val')],
    early_stopping_rounds=50
)
```

---

## Q24. LightGBM: how is it different from XGBoost? { #q24 }

LightGBM's major innovations over XGBoost:

1. **Histogram-based splits.** Instead of examining every possible split point, LightGBM buckets feature values into fixed bins (default 255) and searches only bin boundaries. This is $O(n_{\text{bins}})$ instead of $O(n)$ per feature.

2. **Leaf-wise growth (vs. level-wise).** XGBoost grows the tree level-by-level (breadth-first). LightGBM splits the leaf with the highest gain, regardless of depth — this produces asymmetric trees that fit the data faster but risk overfitting. Use `num_leaves` to control complexity.

   ```
   Level-wise (XGBoost default)       Leaf-wise (LightGBM)
          *                                   *
         / \                                 / \
        /   \                               /   \
       *     *                             *     *
      / \   / \                           / \
     *   * *   *                         *   *
                                        / \
                                       *   *
   ```

3. **GOSS (Gradient-based One-Side Sampling).** Keeps all samples with large gradients (hard cases), downsamples easy ones. Retains ~same accuracy at 1/4 the training time.

4. **EFB (Exclusive Feature Bundling).** Bundles mutually exclusive sparse features into a single feature, drastically reducing effective feature count.

5. **Native categorical handling.** No need to one-hot — LightGBM splits on categorical features using a special algorithm (sort by gradient, find best partition).

**When to pick:**

- **LightGBM** — default for large datasets (> 100K rows). 3–10× faster than XGBoost.
- **XGBoost** — slightly more stable, strong community, great for Kaggle.
- **CatBoost** — if you have many high-cardinality categoricals (ordered target encoding built in).

```python
import lightgbm as lgb

train_data = lgb.Dataset(X_train, label=y_train, categorical_feature=['cat1', 'cat2'])
val_data = lgb.Dataset(X_val, label=y_val)

params = {
    'objective': 'binary',
    'metric': 'auc',
    'num_leaves': 63,
    'learning_rate': 0.05,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'min_data_in_leaf': 20,
    'lambda_l2': 1.0,
}

model = lgb.train(
    params, train_data,
    num_boost_round=2000,
    valid_sets=[val_data],
    callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)]
)
```

---

## Q25. CatBoost: what's its superpower? { #q25 }

CatBoost's three innovations:

1. **Ordered Target Encoding.** Standard target encoding (replace category with its mean target) causes leakage because a row's own target contributes to its encoding. CatBoost uses **ordered encoding** — for each row, it computes the target mean using only rows that appeared *before* it in a random permutation. This is leak-free.

2. **Ordered Boosting.** Similar idea applied to the boosting loop. Multiple models are trained on different permutations; each tree uses a model trained on rows *before* the current row to compute gradients. This reduces target leakage in gradient estimation.

3. **Symmetric (oblivious) trees.** All splits at the same depth use the same feature and threshold. Makes inference extremely fast (each prediction is just a binary-encoded index lookup).

**When CatBoost wins:**

- Datasets with **many high-cardinality categorical features** (user IDs, product IDs, zip codes).
- Use cases where **inference speed matters** (latency-sensitive serving).
- When you want a **strong model with minimal hyperparameter tuning** — CatBoost's defaults are often Kaggle-competitive.

```python
from catboost import CatBoostClassifier

model = CatBoostClassifier(
    iterations=2000,
    learning_rate=0.05,
    depth=6,
    cat_features=['category_col', 'zip_code'],
    eval_metric='AUC',
    early_stopping_rounds=50,
    verbose=100
).fit(X_train, y_train, eval_set=(X_val, y_val))
```

---

## Q26. When would you choose LightGBM over XGBoost — and vice versa? { #q26 }

| Situation | Pick | Why |
|---|---|---|
| Dataset > 1M rows | LightGBM | Histogram binning → 3–10× faster |
| Dataset < 10K rows | XGBoost | Leaf-wise growth risks overfitting on small data |
| Many high-cardinality categoricals | CatBoost > LightGBM | Native ordered target encoding |
| Inference latency critical | CatBoost | Oblivious trees, 2–4× faster inference |
| Kaggle / competition | Ensemble all three | Each brings slight edge |
| Limited RAM | LightGBM | Lower memory footprint via histograms |
| GPU training | LightGBM or XGBoost | Both have GPU support; XGBoost's is more mature |
| Stable, well-understood | XGBoost | Most widely deployed, most forgiving defaults |

<div class="scenario" markdown>
**Scenario:** Your team trains XGBoost nightly on 50M rows and it takes 4 hours. The business wants hourly retraining. What do you do?

**Answer structure:** (1) Switch to LightGBM → histogram-based binning will likely cut time to ~30–60 min. (2) If still too slow, consider GOSS sampling or train on a rolling 7-day window instead of all history. (3) Enable GPU training. (4) Reduce `num_boost_round` with `early_stopping_rounds` on a sliding validation set.
</div>

---

## Q27. How is feature importance calculated in tree ensembles? What are the gotchas? { #q27 }

Three methods:

**1. Gain (default in XGBoost/LightGBM):** Total reduction in loss attributed to splits on this feature.

**2. Split count (frequency):** How often the feature is used for splits. Ignores magnitude.

**3. Cover (XGBoost):** Number of samples affected by splits on this feature.

**Gotchas:**

- **Bias toward high-cardinality features.** A continuous feature with 10,000 unique values has more split opportunities than a binary one, inflating its importance artificially.
- **Correlated features split importance.** If two features are correlated, importance gets arbitrarily divided between them — the "winning" one in an early split looks important; the other looks useless even though they carry the same info.
- **Doesn't capture interactions.** A feature might be individually weak but critical in interactions.

**Better alternative: Permutation importance.**

Shuffle one feature's values in the validation set, measure the drop in performance. Features whose shuffling crashes accuracy are important.

```python
from sklearn.inspection import permutation_importance

result = permutation_importance(
    model, X_val, y_val,
    n_repeats=10, random_state=42, n_jobs=-1
)
importances = pd.DataFrame({
    'feature': X_val.columns,
    'importance': result.importances_mean,
    'std': result.importances_std
}).sort_values('importance', ascending=False)
```

**Even better: SHAP.** Provides per-prediction feature attribution and handles interactions properly.

```python
import shap
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_val)
shap.summary_plot(shap_values, X_val)
```

---

## Q28. What is early stopping and why is it almost mandatory for boosting? { #q28 }

**Early stopping:** Monitor validation loss during training; stop when it hasn't improved for $k$ consecutive rounds.

**Why it's essential for boosting:**

- Boosting greedily reduces bias at every iteration. Given enough iterations, it will memorize training noise.
- The "correct" number of trees depends on the dataset, learning rate, depth — you can't predict it.
- Early stopping effectively turns `n_estimators` into an automatically-tuned hyperparameter.

**Implementation:**

```python
model = lgb.train(
    params, train_data,
    num_boost_round=5000,  # upper bound
    valid_sets=[val_data],
    callbacks=[lgb.early_stopping(stopping_rounds=50)]
)
best_iter = model.best_iteration
print(f"Optimal: {best_iter} trees out of 5000")
```

**Gotcha:** The validation set must be a proper held-out set. If you early-stop on the same data used for hyperparameter tuning, you're leaking. Best practice: three-way split (train / val-for-early-stop / final-test).

---

## Q29. Explain how trees handle categorical features in XGBoost, LightGBM, and CatBoost. { #q29 }

**XGBoost:** Does **not** natively handle categoricals. You must one-hot encode, label-encode, or target-encode beforehand. Recent versions (≥ 1.5) have experimental `enable_categorical=True` that splits categoricals by partitioning.

**LightGBM:** Native support. Algorithm:

1. Sort categories by `sum(gradients) / sum(hessians)`.
2. Find the best split point in this sorted order.

This is optimal in a specific sense (Fisher, 1958) and avoids one-hot explosion. Pass `categorical_feature=['col1', 'col2']` to `Dataset()`.

**CatBoost:** Uses **ordered target encoding** (see Q25). Leakage-free by construction.

**Comparison on a 50-cardinality feature:**

| Approach | New features created | Overfitting risk |
|---|---|---|
| One-hot encoding | 50 sparse cols | Low |
| Label encoding | 1 col with arbitrary ordering | High — tree splits on spurious ordering |
| Target encoding (naive) | 1 col | Very high — target leakage |
| Target encoding (out-of-fold) | 1 col | Medium |
| LightGBM native | 0 (internal) | Low |
| CatBoost native | 0 (internal) | Very low |

<div class="tip-box" markdown>
**Interviewer trap:** "Should you one-hot encode for LightGBM?" Answer: *No.* One-hot hurts LightGBM because each binary column has only one possible split, preventing the optimal Fisher-style partitioning. Use `categorical_feature` argument instead.
</div>

---

## Q30. Random Forest vs Gradient Boosting: when to use each? { #q30 }

| Criterion | Random Forest | Gradient Boosting |
|---|---|---|
| **Out-of-box accuracy** | Good | Usually better on tabular |
| **Overfitting risk** | Low | High without tuning |
| **Training time** | Parallelizable, fast | Sequential, slower |
| **Hyperparameter sensitivity** | Forgiving | Sensitive to LR, depth, num trees |
| **Handles noisy labels** | Well (averaging smooths) | Poorly (keeps chasing noise) |
| **Outliers** | Robust | Sensitive |
| **Interpretability** | Decent (feature importance) | Worse, needs SHAP |
| **Inference speed** | Slow (hundreds of trees) | Slow but similar |

**Rule of thumb:**

- **First baseline** — Random Forest. Fast, no tuning needed.
- **Production model** — LightGBM/XGBoost, tuned.
- **Noisy/messy data** — Random Forest is surprisingly robust.
- **Interpretable production model** — shallow GBM with SHAP.

---

## Q31. How do you prevent overfitting in gradient boosting? { #q31 }

Seven levers:

1. **Lower learning rate** (`learning_rate=0.01` instead of 0.1). Pair with more trees.
2. **Early stopping** on a held-out validation set.
3. **Tree depth cap** (`max_depth=6` or `num_leaves=31`).
4. **Minimum samples per leaf** (`min_samples_leaf=20` or `min_data_in_leaf=100`). Prevents tiny leaves that memorize noise.
5. **Row subsampling** (`subsample=0.8`, `bagging_fraction=0.8`).
6. **Column subsampling** (`colsample_bytree=0.8`, `feature_fraction=0.8`).
7. **L1/L2 regularization on leaf weights** (`reg_alpha`, `reg_lambda`).

**Optuna-driven tuning:**

```python
import optuna
import lightgbm as lgb

def objective(trial):
    params = {
        'objective': 'binary',
        'metric': 'auc',
        'num_leaves': trial.suggest_int('num_leaves', 16, 256),
        'learning_rate': trial.suggest_float('lr', 0.01, 0.3, log=True),
        'feature_fraction': trial.suggest_float('feat', 0.5, 1.0),
        'bagging_fraction': trial.suggest_float('bag', 0.5, 1.0),
        'bagging_freq': trial.suggest_int('bag_freq', 1, 7),
        'min_data_in_leaf': trial.suggest_int('min_leaf', 10, 200),
        'lambda_l2': trial.suggest_float('l2', 1e-3, 10.0, log=True),
        'verbose': -1
    }
    model = lgb.train(params, train_data, 2000,
                      valid_sets=[val_data],
                      callbacks=[lgb.early_stopping(50)])
    return model.best_score['valid_0']['auc']

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100)
```

---

## Q32. What is gradient boosting for ranking (LambdaRank, LambdaMART)? { #q32 }

Classical boosting optimizes pointwise loss. **LambdaMART** optimizes *ranking* loss directly.

Key idea: define a pseudo-gradient (the "lambda") that reflects how much a pair of items' ranking contributes to the ranking metric (NDCG, MAP).

For items $i$ (higher relevance) and $j$ (lower relevance):

$$
\lambda_{ij} = \frac{\partial C_{ij}}{\partial s_i} \cdot |\Delta \text{NDCG}_{ij}|
$$

where $C_{ij}$ is cross-entropy between predicted rank pair probability and ideal pair (1 for correct order), and $\Delta \text{NDCG}_{ij}$ is how much NDCG would change if $i, j$ were swapped.

Each item's gradient is the sum of all its $\lambda$'s: features that push relevant items up and irrelevant down.

**Implementation in LightGBM:**

```python
params = {
    'objective': 'lambdarank',
    'metric': 'ndcg',
    'ndcg_eval_at': [1, 3, 5, 10],
    'label_gain': [0, 1, 3, 7, 15],  # relevance gains
}

train_data = lgb.Dataset(
    X_train, label=y_train,
    group=group_train  # number of items per query
)
```

**Use cases:** search ranking, product listing, feed ordering, ad ranking.

---

## Q33. Explain bias-variance tradeoff in tree ensembles. { #q33 }

**Single deep tree:** Low bias (can memorize training set), high variance.

**Random Forest:**

- Bias unchanged from individual tree (similar depth).
- Variance reduced by averaging $B$ trees: variance is $\rho \sigma^2 + \frac{(1-\rho) \sigma^2}{B}$.
- The feature subsampling at each split *decorrelates* trees, pushing $\rho$ down and amplifying the reduction.

**Gradient Boosting:**

- Each tree is shallow (high bias individually).
- Each tree reduces the *bias* of the overall ensemble by fitting residuals.
- Variance is controlled via low learning rate and row/column subsampling.

**Dial analogy:**

- RF: reduces variance. If underfitting, RF won't help much — you need deeper trees or better features.
- GBM: reduces bias. If overfitting, you need regularization.

---

## Q34. Can tree models extrapolate? { #q34 }

**No.** This is a fundamental limitation.

A tree's prediction for any input is the mean (or class vote) of the leaf it lands in. The leaf's value is determined *entirely* by training examples that fell into it.

If a test input has a feature value outside any training range — say, training had `income ∈ [10K, 100K]` and test has `income = 500K` — the tree predicts the same value as `income = 100K`. It cannot extrapolate the trend.

**Consequence for production:**

- Distribution shift → predictions plateau at training boundary.
- Long-tail features (sales, income, web traffic) need careful bucketing or log transforms.
- For time series forecasting with trends, tree models break down beyond the training period.

**Fixes:**

- Log-transform heavy-tailed features.
- Add linear-ish features (differences, trends).
- Use linear models *alongside* trees for extrapolation-heavy regions.
- For time series specifically, include time as an explicit feature — but don't expect miracles.

<div class="tip-box" markdown>
**Interviewer favorite:** "Why did my forecasting model (LightGBM) predict identical values for the last 3 months of 2026 when trained on 2020–2025 data?" → *Because there's an upward trend, and LightGBM clips extrapolation at the training maximum.* Add trend features explicitly or use a time-series model.
</div>

---

## Q35. Explain "monotonic constraints" in gradient boosting. When do you use them? { #q35 }

Some tree libraries (XGBoost, LightGBM, CatBoost) let you enforce:

> "Prediction must be monotonically non-decreasing (or non-increasing) in feature X."

**Mechanics:** At each split, if the proposed partition would violate monotonicity (e.g., a split where high-X leaf has lower prediction than low-X leaf), the split is rejected or the leaf values are clipped to preserve monotonicity.

**Use cases:**

- **Credit risk:** default risk must not decrease as debt-to-income increases.
- **Insurance:** premium must not decrease as claim history worsens.
- **Medical:** dose-response relationships.
- **Regulatory:** fair lending often requires monotonic risk features.

```python
# LightGBM
params = {
    'monotone_constraints': [1, 0, -1, 0, 0],
    # 1: increasing, -1: decreasing, 0: none
    # ...
}

# XGBoost
params = {'monotone_constraints': '(1,0,-1,0,0)'}
```

**Tradeoff:** Enforcing monotonicity can hurt accuracy, but it's often *required* by stakeholders or regulators. Always A/B test accuracy with and without.

---

## Q36. What is stacking / blending? How does it work? { #q36 }

**Stacking:**

1. Train several base models on training data.
2. Generate out-of-fold predictions (use CV to prevent leakage).
3. Train a **meta-model** (often logistic regression) on these predictions.
4. The meta-model learns how to combine base models optimally.

**Blending** is similar but uses a fixed holdout set instead of CV.

```python
from sklearn.ensemble import StackingClassifier
from sklearn.linear_model import LogisticRegression

base_models = [
    ('lgb', LGBMClassifier()),
    ('xgb', XGBClassifier()),
    ('rf', RandomForestClassifier()),
]

stack = StackingClassifier(
    estimators=base_models,
    final_estimator=LogisticRegression(),
    cv=5,
    stack_method='predict_proba'
).fit(X, y)
```

**When it helps:**

- Your base models make *different* errors (diversity is key).
- You have enough data that the meta-model doesn't overfit.
- Marginal Kaggle gains (last 0.5% AUC).

**When it doesn't:**

- Base models are similar (e.g., three LightGBMs with slightly different hyperparameters).
- Small dataset — meta-model overfits the CV predictions.
- Inference latency budget is tight — stacking adds all base models' cost.

---

## Q37. What is isolation forest? Why is it good for anomaly detection? { #q37 }

**Isolation Forest:**

1. Build many random trees. At each node, pick a random feature and a random split value.
2. To score a point, measure the average path length from root to leaf across trees.
3. **Anomalies have shorter paths** — they get isolated quickly because they're different.

**Why it works:** Normal points live in dense regions; isolating them requires many splits. Anomalies are in sparse regions; one or two random splits can isolate them.

**Advantages:**

- Doesn't assume a distribution (unlike Gaussian Mixture).
- Linear time complexity $O(n \log n)$.
- Works well in high dimensions.
- Handles mixed feature types.

**Disadvantages:**

- Depends on random splits — results vary between runs (stabilize with many trees).
- Struggles with clustered anomalies.
- The score is relative, not absolute — thresholding is ad-hoc.

```python
from sklearn.ensemble import IsolationForest

clf = IsolationForest(
    n_estimators=200,
    contamination=0.01,  # expected fraction of anomalies
    random_state=42
).fit(X)

# -1 = anomaly, 1 = normal
predictions = clf.predict(X)
# Continuous score (lower = more anomalous)
scores = clf.score_samples(X)
```

---

## Q38. How do you handle class imbalance in tree ensembles? { #q38 }

Four approaches, in order of simplicity:

**1. Class weights** (`scale_pos_weight` in XGBoost/LightGBM):

```python
# Imbalance ratio: minority gets more weight
neg, pos = np.bincount(y_train)
params['scale_pos_weight'] = neg / pos
```

**2. `is_unbalance` flag (LightGBM):** Auto-computes weights.

**3. Threshold tuning:** Train normally, then pick the decision threshold that maximizes your target metric (F1, or your business criterion) on validation data.

```python
from sklearn.metrics import precision_recall_curve

probs = model.predict_proba(X_val)[:, 1]
p, r, thresholds = precision_recall_curve(y_val, probs)
f1_scores = 2 * p * r / (p + r + 1e-10)
best_threshold = thresholds[np.argmax(f1_scores)]
```

**4. Focal loss** (custom objective): Down-weights easy examples, focuses on hard minority samples. Useful for extreme imbalance (>100:1). Implement as custom objective.

**What usually does NOT help for tree models:**

- **SMOTE** — creates synthetic samples in feature space. Trees care about rank, not magnitude; SMOTE rarely helps and can introduce noise. Use only after trying the above.
- **Random undersampling** — wastes data. Acceptable only when dataset is enormous and compute-constrained.

<div class="tip-box" markdown>
**Production reality:** On fraud/churn/default problems (0.1–5% positive), the right answer is almost always *class weights + PR-AUC optimization + threshold tuning*. SMOTE is over-recommended in courses and under-used in production.
</div>

---

## Q39. Explain SHAP values for tree models. { #q39 }

**SHAP (SHapley Additive exPlanations):** Each feature's contribution to a prediction, measured as its *Shapley value* from cooperative game theory.

Shapley value for feature $i$:

$$
\phi_i = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|! (|F| - |S| - 1)!}{|F|!} [f(S \cup \{i\}) - f(S)]
$$

This is the average marginal contribution of feature $i$ across all possible feature orderings.

**Guarantees:**

- **Local accuracy:** $\hat{y} = \phi_0 + \sum_i \phi_i$ (prediction decomposes exactly).
- **Missingness:** absent features get zero attribution.
- **Consistency:** if a feature's contribution increases, its SHAP value increases.

**For tree models, SHAP has an efficient exact algorithm** (TreeSHAP, $O(TLD^2)$ where $T$ trees, $L$ leaves, $D$ depth) — no need to approximate.

```python
import shap

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_val)

# Global importance
shap.summary_plot(shap_values, X_val)

# Explain a single prediction
shap.force_plot(explainer.expected_value, shap_values[0], X_val.iloc[0])

# Dependence plot (feature interactions)
shap.dependence_plot('feature_x', shap_values, X_val)
```

**Why SHAP > feature importance:**

- Per-prediction explanation (not just global).
- Handles correlated features fairly.
- Quantifiable interactions.
- Principled theoretical foundation.

---

## Q40. Why are gradient boosted trees so hard to beat on tabular data? { #q40 }

Five reasons, accumulated from a decade of Kaggle and production:

1. **Native handling of mixed types.** Categorical, continuous, binary — all in one model. No embedding required.
2. **Robust to feature scaling.** Monotonic transforms of features don't change splits. No normalization needed.
3. **Handles missing values internally.** No imputation required (XGBoost/LightGBM).
4. **Captures non-linearities and interactions** automatically via splits.
5. **Regularization is strong and easy to tune.** Depth, learning rate, subsampling, L1/L2, minimum leaf samples — many dials.

**Why neural nets usually lose on tabular:**

- **Little sequential/spatial structure** in tabular — nothing for conv/attention to exploit.
- **Smaller datasets.** Most tabular problems have 10K–10M rows. NNs need more.
- **Feature engineering matters more.** Trees handle engineered features; NNs don't help more than trees on the same features.
- **Heterogeneous features** (one-hot, log, raw). NNs handle this poorly without manual preprocessing.

**The exceptions:**

- **Huge datasets with rich categorical features** (recsys, ad click). Two-tower or DeepFM can beat trees.
- **Tabular + sequences** (session data, transactions over time). Transformers like TabTransformer may win.
- **Tabular + structure** (graph of users). GNNs beat trees.
- **When interpretability is irrelevant and latency is fine.** Ensembles of trees + NNs win.

<div class="scenario" markdown>
**Scenario:** Your team wants to replace a LightGBM model with a TabNet/TabTransformer. Champion arguments and counter-arguments?

**Champion for NN:** Attention might capture feature interactions more flexibly; pre-training on unlabeled data; better at cold-start with embeddings.

**Counter:** 10× more engineering work, slower training, harder to debug, usually comparable or worse accuracy on standard tabular benchmarks. Unless you have a specific reason (multi-modal features, massive dataset, transfer from unlabeled), stick with LightGBM.
</div>
