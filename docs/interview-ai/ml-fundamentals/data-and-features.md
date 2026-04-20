# 2. Data & Features

> **Module goal:** 80% of real ML work is data work. This module covers the questions interviewers use to separate textbook-only candidates from engineers who've shipped models. Every question here has cost someone a production outage.

---

## Q21. How do you handle missing values? { #q21 }

There is no universal answer — the right strategy depends on **why** data is missing. Learn this framework:

**The three types of missingness (Rubin 1976):**

| Type | Meaning | Example |
|---|---|---|
| **MCAR** (Missing Completely At Random) | Missingness is independent of everything | Sensor randomly drops readings |
| **MAR** (Missing At Random) | Missingness depends on observed variables | Older users skip income question |
| **MNAR** (Missing Not At Random) | Missingness depends on the missing value itself | High earners refuse to disclose salary |

**Treatment options, ranked by sophistication:**

1. **Drop rows** — safe if missing <5% and MCAR.
2. **Drop columns** — if a feature is mostly missing and not critical.
3. **Mean/median/mode imputation** — quick, but distorts variance.
4. **Forward-fill / back-fill** — time series only.
5. **Model-based imputation** — `sklearn.impute.IterativeImputer`, KNN imputer.
6. **Add missingness indicator** — critical when missingness itself carries signal.
7. **Tree-based models handle NaN natively** (LightGBM, CatBoost) — let them.

```python
from sklearn.impute import SimpleImputer, KNNImputer
import pandas as pd

# Strategy 1: Median for numeric, mode for categorical
num_imputer = SimpleImputer(strategy='median')
df[num_cols] = num_imputer.fit_transform(df[num_cols])

# Strategy 2: KNN — respects feature relationships
knn_imputer = KNNImputer(n_neighbors=5)
df_num = knn_imputer.fit_transform(df[num_cols])

# Strategy 3: Add missing indicator (super useful)
df['income_was_missing'] = df['income'].isna().astype(int)
df['income'] = df['income'].fillna(df['income'].median())
```

<div class="scenario" markdown>
**30% of your `income` column is missing. What do you do?**

**Answer:** (1) Investigate *why* — survey form skip, data pipeline failure, refusal bias? (2) If MNAR (likely — high earners refuse), a missingness indicator is critical because missingness is itself a strong signal. (3) Impute with a model conditioned on correlated features (age, location, employment). (4) For tree models, pass `NaN` directly. (5) Never mean-impute — you'll compress variance and underestimate error bars.
</div>

---

## Q22. Encoding categorical variables — which encoder when? { #q22 }

| Encoder | Creates | Use when |
|---|---|---|
| **One-hot** | N binary columns | Low cardinality (<15), no ordering |
| **Ordinal / label** | Single integer column | Categories have natural order (low/med/high) |
| **Target / mean encoding** | Single column with target mean per category | High cardinality; must guard against leakage |
| **Frequency encoding** | Replace category with its count | Quick, survives high cardinality, tree-friendly |
| **Binary encoding** | log₂(N) binary columns | Medium cardinality, want compactness |
| **Hashing** | Fixed K columns via hash | Extremely high cardinality, memory-bound |
| **Embeddings** | Dense learned vector | Deep learning, very high cardinality (user IDs) |

**The target-encoding trap:**

```python
# WRONG — leaks test labels into features
df['city_enc'] = df.groupby('city')['target'].transform('mean')

# RIGHT — fit on train only, apply to val/test
from category_encoders import TargetEncoder
enc = TargetEncoder(smoothing=10.0)  # smoothing prevents overfit on rare cats
X_train_enc = enc.fit_transform(X_train, y_train)
X_val_enc = enc.transform(X_val)
```

**Smoothing formula:** `encoded = (n_category · mean_category + m · global_mean) / (n_category + m)`. For rare categories, falls back toward global mean, preventing overfit.

---

## Q23. Feature scaling — standardization vs normalization vs robust scaling { #q23 }

| Method | Formula | Range | Use for |
|---|---|---|---|
| **Standardization (z-score)** | `(x − μ) / σ` | Unbounded, μ=0, σ=1 | Most ML; assumes roughly Gaussian |
| **Min-max normalization** | `(x − min) / (max − min)` | [0, 1] | Neural nets, images, bounded outputs |
| **Robust scaling** | `(x − median) / IQR` | Unbounded, robust | Data with outliers |
| **Max-abs** | `x / max(|x|)` | [−1, 1] | Sparse data (preserves sparsity) |
| **Log transform** | `log(x + c)` | Unbounded | Right-skewed (income, counts) |

**Which algorithms care about scaling?**

- **Care (scale-dependent):** distance-based (k-NN, k-means, SVM with RBF), gradient-based (neural nets, logistic regression), PCA.
- **Don't care:** tree-based (decision trees, random forests, gradient boosting) — they split on thresholds, invariant to monotonic transforms.

<div class="tip-box" markdown>
**Fit scaler on train only, transform train/val/test.** Fitting on full data is subtle leakage — test-set means sneak into your training features.
</div>

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled   = scaler.transform(X_val)   # NOT fit_transform
X_test_scaled  = scaler.transform(X_test)  # NOT fit_transform
```

---

## Q24. Outlier detection and handling { #q24 }

**Detection methods:**

1. **Z-score** — flag `|z| > 3`. Assumes normal distribution.
2. **IQR rule** — flag outside `[Q1 − 1.5·IQR, Q3 + 1.5·IQR]`. Robust.
3. **Isolation Forest** — trees; outliers isolated quickly.
4. **LOF (Local Outlier Factor)** — density-based; finds local outliers.
5. **Domain rules** — negative age, age > 120, etc.

**Handling:**

- **Remove** — only if clearly erroneous.
- **Cap / winsorize** — clip at 1st/99th percentile.
- **Log transform** — long-tailed distributions.
- **Model-based** — robust losses (Huber), quantile regression.
- **Keep them** — for fraud detection, outliers ARE the signal.

```python
# Winsorize
from scipy.stats.mstats import winsorize
df['income_cap'] = winsorize(df['income'], limits=[0.01, 0.01])

# Isolation Forest for anomaly detection
from sklearn.ensemble import IsolationForest
iso = IsolationForest(contamination=0.01, random_state=42)
df['is_outlier'] = iso.fit_predict(X) == -1
```

!!! warning "Don't blindly remove"
    Outliers in fraud, medical, and safety-critical domains are often the very thing you're modeling. **Understand before you delete.**

---

## Q25. Class imbalance — the complete playbook { #q25 }

When positive class is 1–5% (fraud, disease, churn), accuracy becomes meaningless and models default to "predict majority."

**The 5 weapons:**

1. **Resampling**
    - **SMOTE** — synthesize new minority samples by interpolation between neighbors.
    - **ADASYN** — SMOTE but focuses on borderline cases.
    - **Random undersampling** — drop majority (wastes data).
    - **Tomek links** — remove majority samples near decision boundary.

2. **Class weights** — `class_weight='balanced'` in sklearn. Gradient is up-weighted for minority class.

3. **Threshold tuning** — default 0.5 is rarely optimal. Tune on validation to maximize F1 or business metric.

4. **Focal loss** — automatically down-weights easy examples. Great for extreme imbalance.

5. **Metric change** — use precision/recall/F1/AUC-PR, not accuracy.

```python
from imblearn.over_sampling import SMOTE
from sklearn.linear_model import LogisticRegression

smote = SMOTE(random_state=42, k_neighbors=5)
X_resampled, y_resampled = smote.fit_resample(X_train, y_train)  # TRAIN ONLY

# Alternative: class weights
model = LogisticRegression(class_weight='balanced')

# Alternative: tune threshold
from sklearn.metrics import f1_score
probs = model.predict_proba(X_val)[:, 1]
best_t = max(np.linspace(0.01, 0.99, 99),
             key=lambda t: f1_score(y_val, probs > t))
```

<div class="scenario" markdown>
**You have 99.7% non-fraud, 0.3% fraud. Your model gets 99.7% accuracy. Is it good?**

**Answer:** No — it's predicting the majority class for everything. Accuracy is useless here. Use AUC-PR (precision-recall AUC), which directly measures minority-class performance. Also report recall at the precision you can operationally tolerate (e.g. "recall at 90% precision"). Business question: what's the cost of false negative (missed fraud) vs false positive (bothered customer)? That ratio determines your threshold.
</div>

---

## Q26. Data leakage — the #1 bug in ML { #q26 }

Data leakage = information from outside the training set sneaks into your features. Your model scores great in dev, tanks in production.

**The common culprits:**

1. **Target leakage** — a feature contains or is derived from the target. Example: `loan_status='approved'` and feature `payment_history` computed after approval.
2. **Train-test contamination** — fitting any transformer (scaler, encoder, imputer, PCA) on the full dataset.
3. **Temporal leakage** — using future information in time-series. Feature `30_day_moving_avg` computed with today's data.
4. **Duplicate rows across splits** — same user in train and test.
5. **Group leakage** — same group (customer, patient) in train and test with correlated outcomes.
6. **Preprocessing before split** — feature selection or oversampling before the split.

**The golden rule — always split first, transform second.**

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Pipeline ensures every transform is fit on train only
pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('model', LogisticRegression())
])

# Cross-validation respects the pipeline automatically
from sklearn.model_selection import cross_val_score
scores = cross_val_score(pipe, X, y, cv=5)
```

---

## Q27. Feature selection — filter, wrapper, embedded { #q27 }

**Filter methods** — use statistics, independent of model.

- Variance threshold (drop near-constant features)
- Correlation with target (Pearson, Spearman)
- Chi-squared (categorical features)
- Mutual information (non-linear)

**Wrapper methods** — try different subsets, train model, compare.

- Forward selection / backward elimination
- Recursive Feature Elimination (RFE)
- Expensive but model-aware.

**Embedded methods** — feature selection built into training.

- L1 (Lasso) — zeros out weights.
- Tree-based feature importance (permutation importance is more reliable).

```python
# Permutation importance — gold standard, works for any model
from sklearn.inspection import permutation_importance

result = permutation_importance(model, X_val, y_val, n_repeats=10, random_state=42)
for i in result.importances_mean.argsort()[::-1]:
    print(f"{X.columns[i]:30s} {result.importances_mean[i]:.4f}")
```

!!! tip "Permutation importance > default tree importance"
    Default feature_importances_ in random forests is biased toward high-cardinality features. Permutation importance directly measures "how much does performance drop if I shuffle this column?" — a much cleaner signal.

---

## Q28. Feature extraction vs feature selection { #q28 }

- **Feature selection** — pick a subset of existing features. Keeps interpretability.
- **Feature extraction** — create new features (often compressed) from originals. PCA, autoencoders, UMAP, t-SNE. May lose interpretability but reduce dimensionality.

**When each wins:**
- **Select** — if you need to explain the model (medical, legal, finance).
- **Extract** — if you have many correlated features (sensors, images) and only care about predictive power.

---

## Q29. PCA — what it is, when to use it, when NOT { #q29 }

PCA finds orthogonal directions of maximum variance and projects data onto the top-k.

**Mathematical view:** SVD of the centered data matrix. The first k principal components are the top-k right singular vectors. Each captures progressively less variance.

**When to use:**
- Dimensionality reduction for visualization (k=2 or 3).
- Reducing correlated numeric features before a linear model.
- Compressing images/embeddings for faster serving.
- Denoising (drop low-variance components).

**When NOT to use:**
- When you need interpretability — PCs are linear combos of features, hard to explain.
- When the variance is not aligned with the target (PCA is unsupervised; it doesn't know what you want to predict).
- For categorical or sparse data (use MCA, truncated SVD, or autoencoders).
- When non-linear structure matters (use UMAP, t-SNE, autoencoders).

```python
from sklearn.decomposition import PCA

# Scale first — PCA is sensitive to scale
X_scaled = StandardScaler().fit_transform(X)

# Choose k by explained variance
pca = PCA(n_components=0.95)  # keep 95% of variance
X_reduced = pca.fit_transform(X_scaled)

print(f"Reduced from {X.shape[1]} to {X_reduced.shape[1]} dims")
print(f"Explained variance: {pca.explained_variance_ratio_.cumsum()}")
```

**PCA vs LDA:** PCA is unsupervised (max variance), LDA is supervised (max class separability). If you have labels and classification is the goal, LDA often beats PCA for dimensionality reduction.

---

## Q30. Train-test split strategies { #q30 }

| Strategy | When to use |
|---|---|
| **Random split** | IID data, classification, no groups |
| **Stratified split** | Imbalanced classification — preserves class ratios |
| **Time-series split** | Temporal data — never randomize |
| **Group split (`GroupKFold`)** | Same entity across rows (patients, users, sessions) |
| **Stratified Group k-Fold** | Both imbalance and groups (medical cohorts) |

**The time-series split in detail:**

```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5, test_size=1000, gap=100)
for train_idx, test_idx in tscv.split(X):
    # train_idx always before test_idx in time
    X_tr, X_te = X.iloc[train_idx], X.iloc[test_idx]
    ...
```

The `gap` parameter prevents leakage when your features use rolling windows — without it, a 30-day moving average could span the split boundary.

---

## Q31. Cross-validation — k-fold, stratified, LOOCV, time-series { #q31 }

**k-Fold CV** — split into k folds, train on k-1, test on 1, rotate. Average scores.

| Variant | Key property |
|---|---|
| **k-Fold** | Standard, IID data. k=5 or 10 typical. |
| **Stratified k-Fold** | Preserves class ratios in each fold. Default for classification. |
| **Leave-One-Out (LOOCV)** | k = N. High variance estimate, expensive. Tiny datasets only. |
| **Repeated k-Fold** | Run k-fold multiple times with different seeds, average. Reduces variance. |
| **Nested k-Fold** | Outer = model evaluation, inner = hyperparameter tuning. Correct but expensive. |
| **TimeSeriesSplit** | Forward-chaining, never uses future for past. |
| **GroupKFold** | Same group stays in one fold (prevents leakage). |

**Why nested CV matters:** if you do hyperparameter tuning and performance estimation on the *same* CV folds, you're overfit to the folds. Nested CV separates them.

```python
from sklearn.model_selection import GridSearchCV, cross_val_score

inner_cv = StratifiedKFold(n_splits=3)
outer_cv = StratifiedKFold(n_splits=5)

grid = GridSearchCV(estimator=model, param_grid=params, cv=inner_cv)
nested_scores = cross_val_score(grid, X, y, cv=outer_cv)
print(f"Unbiased estimate: {nested_scores.mean():.3f} ± {nested_scores.std():.3f}")
```

---

## Q32. Data augmentation — philosophy and techniques { #q32 }

Data augmentation creates new training examples by applying label-preserving transformations. It's *regularization that grows your dataset*.

**By modality:**

| Modality | Augmentations |
|---|---|
| **Images** | Flip, rotate, crop, color jitter, Cutout, Mixup, AutoAugment, RandAugment |
| **Text** | Back-translation, synonym replacement, random insertion/deletion (EDA), paraphrasing via LLM |
| **Tabular** | SMOTE, Gaussian noise on continuous features, feature dropout |
| **Audio** | Time stretch, pitch shift, SpecAugment (mask spectrogram patches) |
| **Time series** | Jittering, scaling, time warping, window slicing |

**The key rule:** augmentation must preserve the label. Rotating a "6" 180° turns it into a "9" — that breaks the label.

**Mixup** is a particularly elegant augmentation:

```python
# Mix two samples AND their labels with mixing weight λ
idx = np.random.permutation(len(X_batch))
lam = np.random.beta(0.2, 0.2)  # beta distribution peaks at 0 and 1
X_mixed = lam * X_batch + (1 - lam) * X_batch[idx]
y_mixed = lam * y_batch + (1 - lam) * y_batch[idx]
```

---

## Q33. Skewed distributions — when and how to transform { #q33 }

**Detect skew:** `df['income'].skew()`. |skew| > 1 is notable; > 2 is significant.

**Transformations:**

| Transform | Best for | Formula |
|---|---|---|
| **Log** | Right-skewed, positive values | `log(x + 1)` |
| **Square root** | Mild right skew, counts | `√x` |
| **Box-Cox** | Positive values, automatic λ search | via `scipy.stats.boxcox` |
| **Yeo-Johnson** | Handles negative values too | `sklearn.preprocessing.PowerTransformer` |
| **Quantile transform** | Force any shape to uniform or normal | `QuantileTransformer` |

```python
from sklearn.preprocessing import PowerTransformer

pt = PowerTransformer(method='yeo-johnson')
X_train_pt = pt.fit_transform(X_train[numeric_cols])
```

**When NOT to transform:** tree models are scale-invariant and skew-invariant. Don't bother for XGBoost, LightGBM, random forest.

---

## Q34. High-cardinality categorical features — the hidden danger { #q34 }

"City," "product_id," "user_id" can have thousands of unique values. One-hot explodes dimensionality.

**Strategies:**

1. **Target encoding with smoothing** — compact, model-agnostic, guard against leakage.
2. **Frequency / count encoding** — replace category with its frequency.
3. **Feature hashing** — hash to fixed K dimensions. Collisions are OK at scale.
4. **Embedding layers** (deep learning) — learn a dense vector per category. Gold standard for user/item IDs.
5. **Grouping** — top-k most frequent + "other" bucket.
6. **CatBoost native handling** — uses ordered target encoding to avoid leakage automatically.

```python
# Group rare categories
top_cities = df['city'].value_counts().head(50).index
df['city_grouped'] = df['city'].where(df['city'].isin(top_cities), 'other')
```

---

## Q35. Binning and discretization { #q35 }

**Binning** — convert continuous to discrete buckets.

**When useful:**
- Linear models that need to capture non-linear relationships.
- Reducing noise in features with measurement error.
- Creating interpretable rules.
- Handling outliers (top bin captures extremes).

**Binning strategies:**

| Strategy | How | Use for |
|---|---|---|
| **Equal-width** | Fixed-size intervals | Uniform distributions |
| **Equal-frequency (quantile)** | Each bin = equal count | Skewed distributions |
| **k-means-based** | Cluster-driven cuts | Multi-modal data |
| **Decision-tree-based** | Optimal splits for a target | Supervised binning |
| **Domain-driven** | Business-meaningful thresholds | Credit scores, age groups |

```python
from sklearn.preprocessing import KBinsDiscretizer

kbd = KBinsDiscretizer(n_bins=5, encode='ordinal', strategy='quantile')
df['age_bin'] = kbd.fit_transform(df[['age']])
```

!!! warning "Binning throws away information"
    Before binning, ask: "Is this gain in simplicity worth the loss in signal?" For modern tree models, binning rarely helps.

---

## Q36. Handling text features in classical ML { #q36 }

**Bag-of-words** — count vectorizer. Simple, sparse, loses order.

**TF-IDF** — term frequency × inverse document frequency. Weights rare discriminative words higher.

**n-grams** — capture local order (bigrams = two-word phrases).

**Character n-grams** — robust to misspellings and OOV.

**Word embeddings (Word2Vec, GloVe, FastText)** — dense vectors; capture semantic similarity.

**Sentence embeddings (sentence-transformers, OpenAI embeddings)** — modern default; one vector per document.

```python
from sklearn.feature_extraction.text import TfidfVectorizer

vec = TfidfVectorizer(
    ngram_range=(1, 2),
    max_features=10000,
    min_df=3,           # ignore terms in < 3 docs
    max_df=0.95,        # ignore terms in > 95% of docs
    sublinear_tf=True   # 1 + log(tf) instead of raw tf
)
X_tfidf = vec.fit_transform(texts)
```

---

## Q37. Handling time/date features { #q37 }

A raw timestamp is almost never a useful feature. Decompose it:

```python
df['day_of_week']   = df['ts'].dt.dayofweek    # 0-6
df['hour']          = df['ts'].dt.hour          # 0-23
df['month']         = df['ts'].dt.month         # 1-12
df['is_weekend']    = (df['ts'].dt.dayofweek >= 5).astype(int)
df['day_of_year']   = df['ts'].dt.dayofyear     # 1-366

# Cyclical encoding — because hour 23 is close to hour 0
import numpy as np
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

# Time since event
df['days_since_signup'] = (df['ts'] - df['signup_ts']).dt.days
```

**Cyclical encoding** is the underrated trick: `sin` and `cos` preserve the "hour 23 is near hour 0" property, which integer encoding destroys.

---

## Q38. Multicollinearity — when features are too correlated { #q38 }

Two features are **multicollinear** if they carry nearly the same information.

**Problems it causes:**
- Linear model coefficients become unstable — tiny data changes flip signs.
- Standard errors inflate — coefficients are individually insignificant even when jointly significant.
- Interpretation is meaningless — "holding X2 constant" isn't possible if X2 always moves with X1.

**Detection — Variance Inflation Factor (VIF):**

```python
from statsmodels.stats.outliers_influence import variance_inflation_factor

vif = pd.DataFrame({
    'feature': X.columns,
    'VIF': [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
})
# VIF > 5: notable. VIF > 10: severe multicollinearity.
```

**Mitigation:**
- Drop one of the correlated pair.
- Combine (e.g., `total = a + b`).
- Regularize (L2/ridge stabilizes coefficients).
- Use a tree model — unaffected by multicollinearity for prediction (though feature importance becomes split among correlated features).

---

## Q39. Feature interactions { #q39 }

**Interaction** = the effect of feature A on the target depends on feature B.

Example: `discount × is_loyal_customer` may matter more than either alone.

**Detecting interactions:**
- Domain knowledge (marketing × segment).
- Tree models capture them automatically via splits.
- SHAP interaction values — `shap.TreeExplainer().shap_interaction_values()`.
- Partial dependence plots for pairs.

**Generating them:**

```python
from sklearn.preprocessing import PolynomialFeatures

# degree=2, interaction_only=True → only cross-terms, no x^2
poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
X_int = poly.fit_transform(X)
```

!!! tip "Interactions for linear models, not for trees"
    Polynomial features help linear/logistic regression. Trees already learn interactions via nested splits — adding polynomial features barely helps and explodes dimensionality.

---

## Q40. Data quality checks — your pre-model sanity list { #q40 }

Before training **any** model, run through:

1. **Schema** — column types match expectations? Dates parsed as datetime?
2. **Duplicates** — `df.duplicated().sum()` — and by key columns too.
3. **Missing** — `df.isna().sum()` per column, visualize with `missingno`.
4. **Cardinality** — `df.nunique()` — flag constant columns (drop) and high-cardinality ones.
5. **Distributions** — histograms + skew + kurtosis per numeric feature.
6. **Target leakage check** — train a simple model; if any feature alone achieves >95% AUC, investigate.
7. **Train-test distribution match** — KS test or population stability index (PSI) between splits.
8. **Label noise** — for classification, manually inspect 50 random labels.
9. **Class balance** — `y.value_counts(normalize=True)`.
10. **Temporal sanity** — min/max of timestamps match expected range.

```python
# Quick one-liner health check
def health_check(df):
    return pd.DataFrame({
        'dtype': df.dtypes,
        'missing_%': df.isna().mean() * 100,
        'unique': df.nunique(),
        'sample': df.iloc[0]
    })
health_check(df)
```

<div class="tip-box" markdown>
The candidates who ace data-focused questions have a **reflexive habit** of running these checks. In interviews, say "first I'd profile the data — check for missing, duplicates, distribution, and leakage" before naming any model. That one sentence separates seniors from juniors.
</div>

---

**Module complete.** Next → [3. Training & Optimization →](training-optimization.md)
