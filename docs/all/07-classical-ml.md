# Module 7 — Classical Machine Learning

> **Bible Module 7 of 14.** Self-contained. Written for **scikit-learn 1.8+, XGBoost 3.x, LightGBM 4.6+, CatBoost 1.2+, Optuna 4.x, SHAP 0.51+, imbalanced-learn 0.14+, Python 3.12+**. All code runnable as-is. Assumes Modules 1–6.

---

## 0. Goal, reader, and how to use this module

**Goal.** After this module you can: take a tabular dataset; build a leak-free training pipeline; pick the right model class; tune hyperparameters efficiently; evaluate honestly with the right metrics; explain a model's predictions to stakeholders; and ship the trained model behind a FastAPI service deployed via the cloud patterns in Module 6.

**Target reader.** Modules 1–4 done. Familiarity with pandas/numpy from Module 2 is assumed. No prior ML required.

**How to use it.** Same as before. Do all 36 problems before reading the solutions.

**Prerequisites.** Modules 1, 2, 3 (DBs/SQL where features come from). Module 4 (FastAPI for serving). Module 6 (cloud) for production deploys.
**Next steps.** Module 8 (Deep Learning), Module 12 (MLOps), Module 13 (LLMOps). Many "ML" problems are still best solved with classical ML — don't skip this for trendier tools.

---

## 1. The classical ML landscape

| Problem shape | Right tool |
|---|---|
| Tabular, < ~1M rows, want simple + interpretable | **Linear / logistic regression** |
| Tabular, want high accuracy without much tuning | **XGBoost / LightGBM / CatBoost** (gradient-boosted trees) |
| Tabular, training set is huge or features are sparse | **LightGBM** with `device='gpu'` if needed |
| Tabular with many categorical columns | **CatBoost** (native cat handling) or **LightGBM** (`categorical_feature=`) |
| Ranking / recommendation | **LightGBM with `lambdarank`** or two-tower deep models (Module 8) |
| Clustering / unsupervised | **k-means**, **DBSCAN**, **HDBSCAN** |
| Dimensionality reduction | **PCA** for linear; **UMAP** for non-linear viz |
| Time series forecasting | Boosting on lag features, **Prophet**, **statsmodels** |
| Anomaly detection | **Isolation Forest**, **One-Class SVM**, autoencoders |

**The 2026 reality of tabular ML.** Gradient-boosted trees (XGBoost/LightGBM/CatBoost) win Kaggle and most internal benchmarks against tabular data. Deep tabular models (TabNet, FT-Transformer) help in narrow cases. **Default to a GBM** and only escalate when you have a clear reason.

### 1.1 Where this module fits in your career

If you do "data science" or "ML engineering" on tabular data, this module is 70% of your day-to-day. Module 8+ covers deep learning, but most production ML still runs on the techniques here. Master this before reaching for transformers.

---

## 2. The standard ML workflow

Every supervised learning project follows this loop:

```
1. Frame the problem.            What are we predicting? Why? How do we measure success?
2. Collect data + labels.        From DB / BQ / S3.
3. Split data.                   Train / val / test (and crucially, leak-free).
4. Build a baseline.             Trivial model (mean predictor / logistic regression). Set a floor.
5. Engineer features.            The single highest-leverage step.
6. Train candidate models.       GBM is usually first.
7. Tune hyperparameters.         Optuna; bounded budget.
8. Evaluate on held-out test.    ONCE. Honestly.
9. Calibrate / threshold.        For classification with downstream decisions.
10. Interpret & sanity-check.    SHAP, permutation importance, examples.
11. Save artifacts.              Model + feature schema + metrics + data version.
12. Deploy as a service.         FastAPI in a container; Module 6.
13. Monitor in production.       Drift, performance, latency.
14. Retrain on schedule.         Loop back to 2.
```

This module covers steps 3-12 in depth. Steps 1, 13, and 14 are Module 12 (MLOps).

---

## 3. Splits, leakage, and the cardinal sin

### 3.1 Train / val / test

- **Train.** Used to fit the model.
- **Validation (dev).** Used to choose hyperparameters and compare models.
- **Test (holdout).** Used **once at the end** to estimate performance on truly unseen data.

Common ratios: 70/15/15 for medium datasets; 80/10/10 if data is plentiful; cross-validation (no fixed val) for small data.

```python
from sklearn.model_selection import train_test_split

X_trainval, X_test,  y_trainval, y_test  = train_test_split(X, y, test_size=0.15, random_state=42, stratify=y)
X_train,    X_val,   y_train,    y_val   = train_test_split(X_trainval, y_trainval, test_size=0.176, random_state=42, stratify=y_trainval)
# 0.176 of the 85% remaining ≈ 15% of the original
```

### 3.2 Stratify for classification

If the positive class is 5%, a random 15% test split might end up with 0% positives. **Always `stratify=y`** for classification. For multi-output, stratify on a representative target.

### 3.3 Group-aware splits

If your data has groups that *must not* leak across splits (same user appearing in train and test, same patient, same household), use `GroupKFold` / `GroupShuffleSplit`:

```python
from sklearn.model_selection import GroupShuffleSplit
gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(gss.split(X, y, groups=user_ids))
```

### 3.4 Time-series splits

**Never random-split time-series.** The future cannot inform the past.

```python
from sklearn.model_selection import TimeSeriesSplit
tscv = TimeSeriesSplit(n_splits=5, test_size=30_000)   # rolling-origin CV
for train_idx, val_idx in tscv.split(X):
    ...    # train_idx is everything before val_idx in time
```

### 3.5 Data leakage — the cardinal sin

Leakage = information from the future / from the test set bleeding into training. Symptoms: implausibly good results in dev, terrible in production. Sources:

1. **Target leakage.** A feature contains the answer in disguise. Classic: predicting "will user churn?" using `last_login_date`, but `last_login_date` is computed *after* the cutoff. Includes anything computed using the label.
2. **Train-test contamination.** Imputing missing values, scaling, or encoding using the *full* dataset before splitting → test stats leak into train.
3. **Look-ahead leakage.** Time-series feature uses future information (`rolling(30).mean()` centered on the timestamp).
4. **Group leakage.** Same user/group in train and test; the model memorizes.
5. **Duplicate rows split across train/test.** Memorization rather than generalization.

**The rule:** every transformation that learns from data (mean, std, OHE categories, target encoding) **must be fit on training data only** and applied to val/test. This is what scikit-learn `Pipeline` enforces automatically — §5.

---

## 4. Baselines — the most-skipped step

Before training anything fancy, train a **baseline**. If your fancy model doesn't beat it meaningfully, something's wrong (or the baseline was already great).

```python
from sklearn.dummy import DummyClassifier, DummyRegressor

# classification baselines
DummyClassifier(strategy="stratified")  # random by class proportion
DummyClassifier(strategy="most_frequent")  # always predict majority

# regression baselines
DummyRegressor(strategy="mean")
DummyRegressor(strategy="median")
```

Add a logistic regression / linear regression baseline next. If a 5-line linear model gets within 2% of XGBoost on your problem, you've learned something important: most signal is linear; spend time on features, not algorithms.

---

## 5. The scikit-learn pipeline — your unit of work

Pipelines are scikit-learn's way of bundling preprocessing + model into one object. They prevent leakage, simplify deployment, and make hyperparameter tuning clean.

### 5.1 The basic Pipeline

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("clf",    LogisticRegression(max_iter=1000)),
])
pipe.fit(X_train, y_train)                     # fits scaler on train, then clf
pipe.predict(X_test)                            # uses train-fitted scaler — NO leakage
pipe.score(X_test, y_test)
```

Every step has `fit` (learn from train) and `transform` (apply); the last step has `fit_predict`.

### 5.2 ColumnTransformer — different transforms per column

Real datasets have mixed types. Apply different preprocessing to different columns.

```python
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

numeric_cols = ["age", "income", "tenure_days"]
categorical_cols = ["country", "plan"]

preprocess = ColumnTransformer([
    ("num", Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale",  StandardScaler()),
    ]), numeric_cols),
    ("cat", Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("ohe",    OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ]), categorical_cols),
], remainder="drop")

model = Pipeline([
    ("prep", preprocess),
    ("clf",  LogisticRegression(max_iter=1000)),
])
model.fit(X_train, y_train)
```

`handle_unknown="ignore"` is critical — at serving time you'll see categories not in train; without this, predictions crash. With it, unknown categories become all-zero vectors.

### 5.3 Why pipelines, in one sentence

**A pipeline is the artifact you deploy.** One object that takes raw input and returns a prediction. Without it, you have to remember to apply the same imputation, scaling, encoding manually at serving time — and any deviation is a "train-serve skew" production bug.

### 5.4 The transformations you'll use 90% of the time

| Step | Class | When |
|---|---|---|
| Impute missing | `SimpleImputer(strategy="median")` | Numeric NaN |
| Impute missing categorical | `SimpleImputer(strategy="most_frequent")` | Categorical NaN |
| Scale numeric | `StandardScaler()` | Linear models, distance-based, NN |
| Robust scale | `RobustScaler()` | Numeric with outliers |
| One-hot encode | `OneHotEncoder(handle_unknown="ignore")` | Low-cardinality categoricals for linear models |
| Ordinal encode | `OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)` | Tree models with categoricals |
| Target encode | `TargetEncoder()` (sklearn ≥1.3) | High-cardinality categoricals |
| Polynomial | `PolynomialFeatures(degree=2)` | Linear models, when you suspect interactions |
| Discretize | `KBinsDiscretizer` | Bin a continuous feature |

### 5.5 Pipelines + cross-validation = leak-free CV

```python
from sklearn.model_selection import cross_val_score

scores = cross_val_score(model, X_trainval, y_trainval, cv=5, scoring="roc_auc")
print(f"AUC: {scores.mean():.3f} ± {scores.std():.3f}")
```

For each fold, the pipeline's preprocessing is fit on that fold's training portion and applied to its validation portion. **No leakage.** This is the only correct way to do CV with preprocessing.

---

## 6. Linear and logistic regression — the bedrock

Often dismissed as "too simple," they remain: the best baseline; the most interpretable; competitive on some problems; and the right answer for many high-traffic, low-latency production endpoints.

### 6.1 Linear regression

```python
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet

# Ordinary least squares — minimal, can overfit on many features
LinearRegression()

# Ridge (L2) — shrinks coefficients toward zero; default for "I don't know"
Ridge(alpha=1.0)

# Lasso (L1) — drives some coefficients to zero (feature selection)
Lasso(alpha=0.01)

# Elastic Net — mix of L1 and L2
ElasticNet(alpha=0.1, l1_ratio=0.5)
```

`alpha` controls regularization strength. Tune via `RidgeCV`/`LassoCV` on a log scale (`np.logspace(-4, 4, 50)`). Linear models **need** scaling — always pair with `StandardScaler`.

### 6.2 Logistic regression — classification

```python
from sklearn.linear_model import LogisticRegression

# Default: L2 regularization, 'lbfgs' solver, C=1.0 (smaller C = more regularization)
LogisticRegression(C=1.0, max_iter=1000, class_weight="balanced")

# L1 for feature selection (gives sparse coefficients)
LogisticRegression(penalty="l1", solver="liblinear", C=0.1)

# Multinomial vs one-vs-rest
LogisticRegression(multi_class="multinomial", solver="lbfgs")  # default in 1.5+; OvR is legacy
```

Always increase `max_iter` (default 100 is too low). `class_weight="balanced"` handles imbalance simply (more sophisticated approaches in §11).

### 6.3 Interpreting coefficients

After fitting, `model.coef_` and `model.intercept_` are the parameters.

```python
# logistic regression with scaled features:
import numpy as np
import pandas as pd

# get the LogisticRegression step out of the pipeline
clf = pipe.named_steps["clf"]
prep = pipe.named_steps["prep"]

# get feature names after preprocessing
feature_names = prep.get_feature_names_out()
coef_table = pd.DataFrame({
    "feature": feature_names,
    "coef": clf.coef_[0],
    "abs_coef": np.abs(clf.coef_[0]),
}).sort_values("abs_coef", ascending=False)
print(coef_table.head(20))
```

For linear regression with **scaled** features, coefficient magnitude is meaningful. For logistic, coefficient is the log-odds change per 1-unit feature change. **Unscaled coefficients are not comparable across features.**

---

## 7. Trees, forests, and gradient boosting — the workhorses

Tree-based models dominate tabular ML. Memorize the family.

### 7.1 Decision tree — the building block

A decision tree splits on features to maximize purity. Single trees overfit easily; their value is as a building block for ensembles, and as an interpretable visualization tool.

```python
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree import plot_tree

tree = DecisionTreeClassifier(max_depth=4, min_samples_leaf=20, random_state=42)
tree.fit(X_train, y_train)
plot_tree(tree, feature_names=X.columns, max_depth=3)
```

### 7.2 Random Forest — bagging trees

Many independent deep trees, each trained on a bootstrap sample with a random feature subset, averaged.

```python
from sklearn.ensemble import RandomForestClassifier

rf = RandomForestClassifier(
    n_estimators=300,         # more trees almost always helps
    max_depth=None,           # let trees grow; depth is implicitly limited by min_samples_leaf
    min_samples_leaf=2,
    n_jobs=-1,                # use all cores
    random_state=42,
    class_weight="balanced",
)
rf.fit(X_train, y_train)
```

RF is robust, easy to use, gives you free feature importances. Its main drawback: usually 1-3% behind boosted trees on accuracy.

### 7.3 Gradient-boosted trees — the modern default

GBMs train trees sequentially, each correcting the previous one's errors. The big three are XGBoost, LightGBM, and CatBoost.

| | XGBoost | LightGBM | CatBoost |
|---|---|---|---|
| Speed (CPU) | Fast | **Fastest** | Medium |
| GPU | Yes | Yes | Yes |
| Categorical handling | Manual encoding | `categorical_feature=` | **Native, best** |
| Default quality | Excellent | Excellent | Excellent |
| Memory | Higher | **Lowest** | Higher |
| Overfit guard | Manual | Manual | Built-in priors |
| Interface | Python + native | Python + native | Python + native |

**Pick:** LightGBM by default. CatBoost when you have many high-cardinality categoricals. XGBoost when you've used it for years or your team's tooling expects it.

### 7.4 LightGBM — a complete example

```python
import lightgbm as lgb
from sklearn.metrics import roc_auc_score

train_data = lgb.Dataset(X_train, label=y_train)
val_data   = lgb.Dataset(X_val,   label=y_val, reference=train_data)

params = {
    "objective":      "binary",
    "metric":         "auc",
    "boosting_type":  "gbdt",
    "learning_rate":  0.05,
    "num_leaves":     63,         # 2^max_depth - 1 ish; 31 is default
    "max_depth":      -1,         # -1 = unlimited; control via num_leaves
    "feature_fraction": 0.9,      # column sampling (per tree)
    "bagging_fraction": 0.9,      # row sampling
    "bagging_freq":   5,
    "min_data_in_leaf": 50,       # bigger = less overfit
    "lambda_l1":      0.1,
    "lambda_l2":      0.1,
    "verbose":        -1,
    "seed":           42,
}

model = lgb.train(
    params,
    train_data,
    num_boost_round=2000,                # max trees
    valid_sets=[val_data],
    callbacks=[
        lgb.early_stopping(stopping_rounds=50),    # stop when val no longer improving
        lgb.log_evaluation(period=100),
    ],
)

pred = model.predict(X_test, num_iteration=model.best_iteration)
print("AUC:", roc_auc_score(y_test, pred))
```

**The five hyperparameters that matter most** (in rough order of impact):
1. `learning_rate` (lower = more trees needed but better generalization). 0.05–0.1 default.
2. `num_leaves` (model complexity). 31–127 typical.
3. `min_data_in_leaf` (overfit guard). 50–500 typical.
4. `feature_fraction` and `bagging_fraction` (regularization via sampling). 0.7–1.0.
5. `lambda_l1` and `lambda_l2` (regularization). 0–10.

Plus `num_boost_round` with **early stopping** — never set this high without early stopping.

### 7.5 XGBoost — same problem in XGBoost dialect

```python
import xgboost as xgb
from sklearn.metrics import roc_auc_score

dtrain = xgb.DMatrix(X_train, label=y_train)
dval   = xgb.DMatrix(X_val,   label=y_val)
dtest  = xgb.DMatrix(X_test,  label=y_test)

params = {
    "objective":        "binary:logistic",
    "eval_metric":      "auc",
    "learning_rate":    0.05,
    "max_depth":        6,
    "min_child_weight": 1,
    "subsample":        0.9,
    "colsample_bytree": 0.9,
    "lambda":           1,         # L2
    "alpha":            0,         # L1
    "tree_method":      "hist",    # fast histogram-based; use 'gpu_hist' for GPU
    "seed":             42,
}

model = xgb.train(
    params, dtrain,
    num_boost_round=2000,
    evals=[(dtrain, "train"), (dval, "val")],
    early_stopping_rounds=50,
    verbose_eval=100,
)

pred = model.predict(dtest, iteration_range=(0, model.best_iteration + 1))
print("AUC:", roc_auc_score(y_test, pred))
```

### 7.6 CatBoost — for categorical-heavy data

```python
from catboost import CatBoostClassifier, Pool

cat_features = ["country", "plan", "device", "city"]
train_pool = Pool(X_train, y_train, cat_features=cat_features)
val_pool   = Pool(X_val,   y_val,   cat_features=cat_features)

model = CatBoostClassifier(
    iterations=2000, learning_rate=0.05, depth=6,
    l2_leaf_reg=3, random_seed=42,
    early_stopping_rounds=50, verbose=100,
    eval_metric="AUC",
)
model.fit(train_pool, eval_set=val_pool)
print("Best iter:", model.get_best_iteration())
```

CatBoost handles categoricals natively (ordered target encoding) — no preprocessing needed for categorical columns.

### 7.7 Sklearn-API wrappers

All three GBMs have sklearn-compatible wrappers (`XGBClassifier`, `LGBMClassifier`, `CatBoostClassifier`). Use them when you want pipelines + GridSearchCV. Use the native APIs (above) for early stopping and full control.

```python
from lightgbm import LGBMClassifier
clf = LGBMClassifier(n_estimators=500, learning_rate=0.05, num_leaves=63, random_state=42)
clf.fit(X_train, y_train, eval_set=[(X_val, y_val)], callbacks=[lgb.early_stopping(50)])
```


---

## 8. Feature engineering — where you actually win

A simple model with good features beats a complex model with raw features almost every time. This section is the highest-leverage in the module.

### 8.1 The taxonomy

| Type | Examples |
|---|---|
| **Aggregation** | `mean(amount) over last 30 days`, `count distinct sessions per user` |
| **Ratio / interaction** | `purchase_total / view_count`, `age / tenure_days` |
| **Time-based** | `days_since_signup`, `is_weekend`, `hour_of_day`, `time_until_event` |
| **Lag** | `revenue.shift(7)`, `clicks.diff(1)` |
| **Rolling window** | `rolling(7).mean()`, `expanding().std()` |
| **Categorical encoding** | OHE, ordinal, target encoding, count encoding |
| **Text** | `len`, `word_count`, TF-IDF, embeddings |
| **External joins** | weather, holidays, geocoding, public-data joins |

### 8.2 Categorical encoding — picking right

| Cardinality | Linear models | Tree models |
|---|---|---|
| Low (< ~15) | One-hot | Either |
| Medium (~15–100) | Target encoding (CV-fold) | Native cat (LGBM/CatBoost) |
| High (>100) | Target encoding or count encoding | Native cat |
| Hash-trick OK? | Yes for very high cardinality | Yes |

**Target encoding** replaces a category with the mean target for that category. Powerful but **leak-prone**: must be computed via cross-fold or with smoothing.

```python
from sklearn.preprocessing import TargetEncoder    # sklearn 1.3+
te = TargetEncoder(target_type="binary", random_state=42, cv=5)
X_train_te = te.fit_transform(X_train[["category"]], y_train)
X_test_te  = te.transform(X_test[["category"]])
```

### 8.3 Time-based features — the lifeblood of time-series

```python
import pandas as pd

df = df.sort_values(["user_id", "ts"])
df["hour"]      = df["ts"].dt.hour
df["dow"]       = df["ts"].dt.dayofweek
df["is_weekend"] = (df["dow"] >= 5).astype(int)
df["days_since_signup"] = (df["ts"] - df["signup_ts"]).dt.days

# lag and rolling per user — careful with the index
df["amount_lag1"] = df.groupby("user_id")["amount"].shift(1)
df["amount_lag7"] = df.groupby("user_id")["amount"].shift(7)
df["amount_roll7_mean"] = (
    df.groupby("user_id")["amount"]
      .rolling(7, min_periods=1).mean()
      .reset_index(level=0, drop=True)
)
df["amount_roll7_std"]  = (
    df.groupby("user_id")["amount"]
      .rolling(7, min_periods=2).std()
      .reset_index(level=0, drop=True)
)
```

**Cyclical encoding** for hour/day-of-week — captures that hour 23 is close to hour 0:

```python
import numpy as np
df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
```

### 8.4 Aggregation features (the highest-leverage on tabular)

For user/customer-level prediction, aggregate transactional history:

```python
agg = (
    transactions
      .groupby("user_id")
      .agg(
          n_orders          =("order_id",  "count"),
          total_revenue     =("amount",    "sum"),
          avg_order         =("amount",    "mean"),
          last_order_days   =("ts",        lambda s: (NOW - s.max()).days),
          n_distinct_categories=("category", "nunique"),
      )
      .reset_index()
)
features = users.merge(agg, on="user_id", how="left").fillna({"n_orders": 0, "total_revenue": 0})
```

The trick: keep the time cutoff explicit. For a model predicting "will the user churn next month?", aggregations must use only data up to *now* — never future data. (Module 5 §SCD2 patterns are useful here.)

### 8.5 Interaction features

For linear models, hand-craft interactions; for tree models, the algorithm finds them. But meaningful ratios still help trees:

```python
df["amount_per_view"]     = df["total_revenue"] / df["n_views"].clip(lower=1)
df["completion_rate"]     = df["completed"] / df["started"].clip(lower=1)
df["recency_to_frequency"] = df["last_order_days"] / df["n_orders"].clip(lower=1)
```

`.clip(lower=1)` to avoid div-by-zero. Or use `np.where`.

### 8.6 The feature engineering checklist

When you finish a feature, ask:
1. **Could this leak target info?** Anything computed using y, or with a future timestamp?
2. **Will this be available at inference time?** If "amount in last 30 days" requires a query, can your serving layer make it fast enough?
3. **Is there a natural prior?** Median/mean as a fallback for new users.
4. **Could a small change in the input flip the prediction?** Test with edge cases.

---

## 9. Hyperparameter tuning — Optuna

Grid search is dead. Bayesian optimization (Optuna's TPE) is the standard for ≥3 hyperparameters; random search for fewer. Both beat grid search badly.

### 9.1 Optuna basics

```python
import optuna
from sklearn.model_selection import cross_val_score
import lightgbm as lgb

def objective(trial):
    params = {
        "objective":         "binary",
        "metric":            "auc",
        "verbosity":         -1,
        "boosting_type":     "gbdt",
        "learning_rate":     trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "num_leaves":        trial.suggest_int  ("num_leaves", 15, 255),
        "min_data_in_leaf":  trial.suggest_int  ("min_data_in_leaf", 20, 500, log=True),
        "feature_fraction":  trial.suggest_float("feature_fraction", 0.5, 1.0),
        "bagging_fraction":  trial.suggest_float("bagging_fraction", 0.5, 1.0),
        "bagging_freq":      trial.suggest_int  ("bagging_freq", 1, 10),
        "lambda_l1":         trial.suggest_float("lambda_l1", 1e-3, 10, log=True),
        "lambda_l2":         trial.suggest_float("lambda_l2", 1e-3, 10, log=True),
    }
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data   = lgb.Dataset(X_val,   label=y_val, reference=train_data)
    model = lgb.train(
        params, train_data,
        num_boost_round=2000,
        valid_sets=[val_data],
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)],
    )
    return model.best_score["valid_0"]["auc"]

study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(objective, n_trials=50, timeout=3600)        # 50 trials OR 1 hour
print("Best AUC:", study.best_value)
print("Best params:", study.best_params)
```

### 9.2 Pruning — terminate bad trials early

```python
def objective(trial):
    params = {...}
    pruning_callback = optuna.integration.LightGBMPruningCallback(trial, "auc")
    model = lgb.train(params, train_data, num_boost_round=2000,
                      valid_sets=[val_data],
                      callbacks=[lgb.early_stopping(50), pruning_callback, lgb.log_evaluation(0)])
    return model.best_score["valid_0"]["auc"]
```

Pruning skips promising-only-early trials. Cuts search time roughly in half.

### 9.3 Defaults that are often "good enough"

For LightGBM on a typical tabular problem, this set is competitive without tuning:

```python
LGBMClassifier(
    n_estimators=2000, learning_rate=0.03,
    num_leaves=63, min_child_samples=50,
    subsample=0.9, colsample_bytree=0.9,
    reg_alpha=0.1, reg_lambda=0.1,
    random_state=42,
)
# train with early stopping at 50 rounds
```

Reach for Optuna when you've already done feature engineering. **Tuning a model with bad features is wasted time.**

### 9.4 Search budgets and stopping

50–200 trials usually finds 95% of the gain. Mark a budget upfront (`timeout=1h` or `n_trials=100`) and stop. The remaining 5% rarely moves business outcomes.

---

## 10. Evaluation metrics — pick the right one

The metric you optimize is the metric you care about. Wrong metric = wrong model.

### 10.1 Classification

| Metric | Use when |
|---|---|
| **Accuracy** | Balanced classes, all errors equal |
| **Precision** | False positives are expensive (e.g., spam) |
| **Recall (sensitivity)** | False negatives are expensive (e.g., disease screening) |
| **F1** | Want a balance, no clear cost asymmetry |
| **AUC-ROC** | Want a threshold-free ranking score; balanced classes |
| **AUC-PR** | Imbalanced classes, focus on positives |
| **Log loss** | Probabilities matter for downstream decisions |
| **Brier score** | Calibration |

```python
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                              roc_auc_score, average_precision_score, log_loss,
                              brier_score_loss, classification_report,
                              confusion_matrix, roc_curve, precision_recall_curve)

y_pred  = model.predict(X_test)              # 0/1
y_proba = model.predict_proba(X_test)[:, 1]  # probabilities

print(classification_report(y_test, y_pred, digits=3))
print("AUC-ROC :", roc_auc_score(y_test, y_proba))
print("AUC-PR  :", average_precision_score(y_test, y_proba))
print("Log loss:", log_loss(y_test, y_proba))
```

### 10.2 Regression

| Metric | Use when |
|---|---|
| **MAE** | Outliers are bad signal — robust |
| **RMSE** | Large errors should be penalized more |
| **MAPE** | Percentage error matters; targets all positive, no zeros |
| **R²** | Explained-variance interpretation |
| **MSLE** | Targets span orders of magnitude, percent error |

```python
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

mae  = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2   = r2_score(y_test, y_pred)
```

### 10.3 The threshold matters — for classification

Models output probabilities. The threshold (default 0.5) turns probabilities into decisions. Picking the threshold is a **business decision**, not a model decision.

```python
import numpy as np
from sklearn.metrics import precision_recall_curve

precisions, recalls, thresholds = precision_recall_curve(y_test, y_proba)
f1s = 2 * precisions * recalls / np.maximum(precisions + recalls, 1e-9)
best = int(np.argmax(f1s))
print(f"Best F1 threshold: {thresholds[best]:.3f}, F1={f1s[best]:.3f}, "
      f"P={precisions[best]:.3f}, R={recalls[best]:.3f}")
```

In production, you might pick a threshold for fixed precision (e.g., "we need >95% precision; what recall can we get?"), or fixed cost (each false positive costs $X, each false negative $Y).

### 10.4 Calibration — when probabilities matter

If a downstream system uses your probabilities (expected value, threshold optimization, ensembling), they must be **calibrated** — predicted 0.7 should mean ~70% true positive rate.

Tree boosters tend to be well-calibrated; logistic regression usually is; neural nets often aren't; SVMs aren't.

```python
from sklearn.calibration import CalibratedClassifierCV, calibration_curve

# wrap any classifier; uses Platt scaling or isotonic regression to recalibrate
calibrated = CalibratedClassifierCV(base_model, method="isotonic", cv=5)
calibrated.fit(X_train, y_train)

# diagnostic: reliability curve
from sklearn.calibration import calibration_curve
prob_true, prob_pred = calibration_curve(y_test, y_proba, n_bins=10)
```

A perfectly calibrated model: `prob_true ≈ prob_pred`.

### 10.5 Cross-validation results — sanity checks

Look at the **distribution** of CV scores, not just the mean. A 5-fold CV with scores `[0.92, 0.65, 0.88, 0.91, 0.93]` (mean=0.86) signals a problem with that one fold — likely a temporal split issue or data quality outlier.

---

## 11. Imbalanced classes

Most real classification problems are imbalanced (5% fraud, 1% click, 0.01% rare disease). The default balance assumption fails.

### 11.1 The cheap fix — `class_weight="balanced"`

Most sklearn classifiers and GBMs support it:
```python
LogisticRegression(class_weight="balanced")
RandomForestClassifier(class_weight="balanced")
LGBMClassifier(class_weight="balanced")  # or `is_unbalance=True`
```

This weights the minority class proportionally during training. **First thing to try.** Often enough.

### 11.2 Resampling — when class_weight isn't enough

```python
from imblearn.over_sampling import SMOTE, RandomOverSampler
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline as ImbPipeline    # NOT sklearn's Pipeline

pipe = ImbPipeline([
    ("scale",   StandardScaler()),
    ("smote",   SMOTE(random_state=42)),                   # only on training data
    ("clf",     LogisticRegression(max_iter=1000)),
])
pipe.fit(X_train, y_train)
```

**Critical:** use `imblearn.pipeline.Pipeline` (not sklearn's), so resampling **only happens on training folds during CV** — never on validation.

### 11.3 Use the right metric

For imbalance, **AUC-PR** and **F1** are far more informative than accuracy. A 99%-accuracy model on a 1%-positive problem might just predict "no" always.

### 11.4 Threshold tuning

For decisions, lower the threshold below 0.5. With 1% positives, predicted probability of 0.1 might still be a strong "yes" signal.

```python
# pick threshold for a target precision
target_precision = 0.95
mask = precisions >= target_precision
threshold_at_target = thresholds[mask][np.argmax(recalls[mask])]
```

---

## 12. Interpretability — SHAP, permutation, partial dependence

Explaining a model is often more important than the model itself for stakeholders.

### 12.1 Built-in feature importance — caveats

```python
# tree models — built-in
fi = pd.DataFrame({"feature": X.columns, "importance": rf.feature_importances_}).sort_values("importance", ascending=False)
```

**Caveat:** built-in importance is biased toward high-cardinality and continuous features. Use **permutation importance** for trustworthy comparison:

```python
from sklearn.inspection import permutation_importance
result = permutation_importance(model, X_val, y_val, n_repeats=10, random_state=42, n_jobs=-1)
fi = pd.DataFrame({"feature": X.columns,
                    "imp_mean": result.importances_mean,
                    "imp_std":  result.importances_std}).sort_values("imp_mean", ascending=False)
```

Permutation importance: shuffle one feature, measure the score drop. Model-agnostic, unbiased.

### 12.2 SHAP — per-prediction explanations

SHAP values are the gold standard for "why did the model predict X for this row?"

```python
import shap

# for tree models (LightGBM/XGBoost/CatBoost/RandomForest)
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# global summary
shap.summary_plot(shap_values, X_test)         # bar = importance; dot = effect direction

# single prediction
shap.force_plot(explainer.expected_value, shap_values[0], X_test.iloc[0])

# dependence plot — feature value vs SHAP value
shap.dependence_plot("age", shap_values, X_test, interaction_index="income")
```

For non-tree models, `shap.KernelExplainer` works — slower, sample your data.

### 12.3 Partial dependence and ICE

```python
from sklearn.inspection import partial_dependence, PartialDependenceDisplay
PartialDependenceDisplay.from_estimator(model, X_train, ["age", "income"], kind="both")
# kind="average" -> PDP, kind="individual" -> ICE, "both" -> overlay
```

PDP shows average effect of a feature; ICE shows individual rows. Useful sanity check ("does my model think doubling income halves churn?").

### 12.4 Sanity-check examples

For every model, before deploying:
- Pick 5 random correct predictions; explain the top SHAP features. Do they make sense?
- Pick 5 worst errors; explain. Are they justifiable mistakes or red flags?
- Examine the highest-importance feature: is it a leak in disguise?

---

## 13. Saving, loading, and serving

### 13.1 Saving the entire pipeline

```python
import joblib

joblib.dump(pipe, "model.joblib", compress=3)         # not pickle; joblib is pickle + numpy-aware
loaded = joblib.load("model.joblib")
loaded.predict(X_test)
```

**Always save the pipeline**, not just the final estimator. If you save `model` separately from `scaler`, you'll forget to apply the scaler at serve time. The pipeline is the deploy artifact.

### 13.2 Versioning

A model isn't a single file; it's a **bundle**:
- `model.joblib` (the pipeline)
- `feature_schema.json` (column names, dtypes — verified at load and at serve)
- `metrics.json` (test metrics; for monitoring drift)
- `data_version.txt` (commit SHA / DVC hash of the training data)
- `code_version.txt` (git SHA of the training code)
- `requirements.txt` (libraries pinned)

Store as one tarball in S3 / GCS:
```
s3://myorg-models/churn/v3/
├── model.joblib
├── feature_schema.json
├── metrics.json
└── manifest.yaml
```

### 13.3 Sklearn version compatibility

Pickled models are **not** version-compatible across sklearn versions. Always pin and document `sklearn==1.8.0` in your serving image.

For long-term portability, use **ONNX**:
```python
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
onnx_model = convert_sklearn(pipe, initial_types=[("X", FloatTensorType([None, X.shape[1]]))])
with open("model.onnx", "wb") as f:
    f.write(onnx_model.SerializeToString())
```

ONNX runtime works in any language; survives sklearn upgrades; enables hardware-accelerated inference.

### 13.4 Serving with FastAPI (the integration with Modules 4 + 6)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib, numpy as np

app = FastAPI()
pipe = joblib.load("/app/model.joblib")

class Features(BaseModel):
    age: int
    income: float
    country: str
    plan: str
    tenure_days: int

@app.post("/predict")
def predict(features: Features):
    df = pd.DataFrame([features.model_dump()])
    proba = float(pipe.predict_proba(df)[0, 1])
    return {"churn_prob": proba, "decision": int(proba > 0.5)}

@app.get("/health")
def health():
    return {"status": "ok"}
```

Wrap in the Module 6 Dockerfile, deploy to Cloud Run / Fargate / K8s. That's a production model service.

### 13.5 Train-serve skew — the production killer

Your model trained on transformed features. At serve time, the pipeline must apply the **identical** transformation. Bugs:

- Pipeline drift: training pipeline and serving pipeline diverge.
- Feature drift: a feature's source upstream changed.
- Schema mismatch: serve sends `tenure_days` as float; pipeline expects int.

Fix: serialize the pipeline (not just the model); validate schema on every request; log feature distributions at serve time and compare to training distributions weekly (Module 12).

---

## 14. Anti-patterns

| Anti-pattern | Right way |
|---|---|
| Random-splitting time series | `TimeSeriesSplit` or chronological split |
| Fitting scaler on full dataset before split | Inside a `Pipeline`; fit on train only |
| Default LogisticRegression with `max_iter=100` | Bump to 1000+; check convergence |
| Ignoring `stratify` for classification | Always stratify on `y` |
| Reporting a single CV mean, not std | Report mean ± std and look at fold variance |
| Tuning on the test set | Reserve test for ONE final evaluation |
| Optimizing accuracy on imbalanced data | Use AUC-PR, F1, or business cost |
| Threshold = 0.5 by default | Tune threshold for your business metric |
| Keeping `n_estimators=10000` with no early stopping | Always early-stop |
| Using built-in feature importance to compare features | Permutation importance |
| Saving `model` only | Save the whole `Pipeline` |
| Hardcoded feature list at inference | Schema validation; pydantic; same column order |
| `apply` in feature engineering on big data | Vectorize with numpy/polars (Modules 2, 5) |
| SMOTE on test set | Resample only training fold |
| Same hyperparams for train and val sets | (impossible; but tune on val, evaluate on test once) |
| Re-fitting on full train+test "for the final model" | Acceptable in practice but document and re-evaluate honestly |
| Mixing pandas + sklearn ColumnTransformer column names sloppily | Use `set_output(transform="pandas")` so pipeline returns DataFrames |
| Comparing test scores across teams w/ different splits | Use a shared, frozen test set + version |

---

## 15. Thirty-six problems (with full structure)

Each problem follows: **Statement → Intuition → Brute force → Optimized → Complexity → Edge cases → Real-world → Follow-ups.**
**Section breakdown:** 5 splits/leakage (P1–P5), 5 pipelines (P6–P10), 4 linear+interpretation (P11–P14), 6 trees/GBM (P15–P20), 4 hyperparameter tuning (P21–P24), 5 metrics (P25–P29), 3 imbalance/calibration (P30–P32), 3 interpretability (P33–P35), 3 deployment (P36 + extras embedded).

---

### Problem 1 — A leak-free train/val/test split

**Statement.** Build a 70/15/15 split for a classification problem with class imbalance (5% positive). Stratify on the label. Reproducible.

**Solution.**
```python
from sklearn.model_selection import train_test_split

X_trv, X_test, y_trv, y_test = train_test_split(
    X, y, test_size=0.15, random_state=42, stratify=y
)
X_train, X_val, y_train, y_val = train_test_split(
    X_trv, y_trv, test_size=0.176, random_state=42, stratify=y_trv
)
# 0.176 of remaining 85% ≈ 15% original

print(y_train.mean(), y_val.mean(), y_test.mean())
# all approx 0.05 — stratification preserves class balance
```

**Real-world.** Stratification is a one-line bug fix that prevents "test set has 0% positives" pathologies on small or imbalanced data.

**Follow-ups.** Multi-label stratification (`MultilabelStratifiedShuffleSplit` from `iterstrat`). Date-stratified splits.

---

### Problem 2 — Group-aware split for sessions

**Statement.** Each row is a session; the same `user_id` appears in many sessions. Train and test must not share any user.

**Solution.**
```python
from sklearn.model_selection import GroupShuffleSplit

gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(gss.split(X, y, groups=df["user_id"]))
X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
assert set(df.iloc[train_idx]["user_id"]) & set(df.iloc[test_idx]["user_id"]) == set()
```

**Real-world.** Healthcare (per-patient), recommenders (per-user), ranking (per-query). Without group awareness, models memorize group identity and report inflated metrics that collapse in production.

**Follow-ups.** `GroupKFold` for cross-validation. `StratifiedGroupKFold` for both grouped and stratified.

---

### Problem 3 — Time-series split with embargo

**Statement.** Time-stamped data; train must be strictly before val, val before test, with a 1-day embargo to avoid same-day correlation.

**Solution.**
```python
import pandas as pd

df = df.sort_values("ts")
cutoff_test = df["ts"].quantile(0.85)
cutoff_val  = df["ts"].quantile(0.70)
embargo = pd.Timedelta(days=1)

train = df[df["ts"] <  cutoff_val - embargo]
val   = df[(df["ts"] >= cutoff_val) & (df["ts"] < cutoff_test - embargo)]
test  = df[df["ts"] >= cutoff_test]
```

**Real-world.** Finance, ad serving, anomaly detection. The embargo gap prevents leakage from "an event near the boundary affects both sides."

**Follow-ups.** Walk-forward CV (`TimeSeriesSplit`). Purged k-fold (de Prado).

---

### Problem 4 — Detecting target leakage

**Statement.** Your CV AUC is 0.99, but you suspect leakage. How do you find which feature?

**Solution.**

1. **Sanity check:** train a single decision tree of depth 1. Is one feature alone giving near-perfect score? Inspect it.
2. **Permutation importance** at depth 1: which single feature loses 0.4+ AUC when shuffled?
3. **Time-of-day check:** is the feature only available *after* the event you're predicting?
4. **Schema review:** `last_login_date`, `total_lifetime_value`, `cancellation_reason` — anything sounding *posterior* to your prediction time.

```python
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import roc_auc_score

for col in X.columns:
    clf = DecisionTreeClassifier(max_depth=2, random_state=42)
    clf.fit(X[[col]].fillna(-999), y)
    auc = roc_auc_score(y, clf.predict_proba(X[[col]].fillna(-999))[:, 1])
    if auc > 0.95:
        print(f"⚠ {col}: AUC={auc:.3f}  ← suspicious")
```

**Real-world.** Most "too good to be true" results in ML are leakage. Build this check into every project.

**Follow-ups.** Leakage in feature joins (joining a "future" table). Signal leakage via row order.

---

### Problem 5 — Reproducible split utility

**Statement.** Build a function `make_splits(df, target, group=None, time=None, ...)` that handles any of the above cases with one signature.

**Solution.**
```python
def make_splits(
    df, target,
    *,
    test_size=0.15, val_size=0.15, seed=42,
    group=None, time=None, embargo_days=0, stratify=False,
):
    """Return train, val, test DataFrames."""
    df = df.copy()
    if time is not None:
        df = df.sort_values(time).reset_index(drop=True)
        cutoff_test = df[time].quantile(1 - test_size)
        cutoff_val  = df[time].quantile(1 - test_size - val_size)
        emb = pd.Timedelta(days=embargo_days)
        train = df[df[time] <  cutoff_val - emb]
        val   = df[(df[time] >= cutoff_val) & (df[time] < cutoff_test - emb)]
        test  = df[df[time] >= cutoff_test]
        return train, val, test
    if group is not None:
        from sklearn.model_selection import GroupShuffleSplit
        gss1 = GroupShuffleSplit(1, test_size=test_size, random_state=seed)
        trv_i, te_i = next(gss1.split(df, df[target], groups=df[group]))
        trv = df.iloc[trv_i].reset_index(drop=True)
        te  = df.iloc[te_i ].reset_index(drop=True)
        gss2 = GroupShuffleSplit(1, test_size=val_size/(1-test_size), random_state=seed)
        tr_i, va_i = next(gss2.split(trv, trv[target], groups=trv[group]))
        return trv.iloc[tr_i], trv.iloc[va_i], te
    # plain stratified split
    from sklearn.model_selection import train_test_split
    strat = df[target] if stratify else None
    trv, te = train_test_split(df, test_size=test_size, random_state=seed, stratify=strat)
    strat = trv[target] if stratify else None
    tr,  va = train_test_split(trv, test_size=val_size/(1-test_size), random_state=seed, stratify=strat)
    return tr, va, te
```

**Real-world.** Every team eventually writes one. Codify your team's splitting policy in this single function so it's hard to misuse.

**Follow-ups.** Add `purge_days` for purged k-fold. Walk-forward CV variant.

---

### Problem 6 — Pipeline with mixed numeric + categorical features

**Solution.**
```python
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression

numeric = ["age", "income", "tenure_days"]
categorical = ["country", "plan"]

prep = ColumnTransformer([
    ("num", Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("sc",  StandardScaler()),
    ]), numeric),
    ("cat", Pipeline([
        ("imp", SimpleImputer(strategy="most_frequent")),
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ]), categorical),
], remainder="drop")

model = Pipeline([("prep", prep), ("clf", LogisticRegression(max_iter=1000))])
model.fit(X_train, y_train)
print(model.score(X_val, y_val))
```

**Why.** All preprocessing is fit only on training data per CV fold. Saved pipeline is the single artifact you deploy.

**Follow-ups.** `set_output(transform="pandas")` to keep DataFrames through transforms (sklearn 1.2+). Custom transformers via `FunctionTransformer`.

---

### Problem 7 — Custom transformer (FunctionTransformer)

**Statement.** Add a feature `log1p(amount)` and a feature `is_weekend` derived from `dow` — both inside the pipeline so they apply at serve time.

**Solution.**
```python
import numpy as np
from sklearn.preprocessing import FunctionTransformer
from sklearn.pipeline import FeatureUnion

def add_features(X):
    X = X.copy()
    X["amount_log"] = np.log1p(X["amount"].clip(lower=0))
    X["is_weekend"] = (X["dow"] >= 5).astype(int)
    return X

feature_adder = FunctionTransformer(add_features, validate=False)

pipe = Pipeline([
    ("features", feature_adder),
    ("prep",     prep),                 # ColumnTransformer from P6
    ("clf",      LogisticRegression()),
])
```

**Real-world.** Most useful feature engineering can be expressed as DataFrame -> DataFrame transforms inside the pipeline. Keeps the deploy artifact self-contained.

**Follow-ups.** Build a custom class inheriting `BaseEstimator, TransformerMixin` for stateful transformers (e.g., target encoders).

---

### Problem 8 — Target encoder via cross-fitting

**Statement.** Encode high-cardinality `city` (50k unique values) for a tree model. Avoid leakage.

**Solution.**
```python
from sklearn.preprocessing import TargetEncoder

te = TargetEncoder(target_type="binary", smooth="auto", cv=5, random_state=42)
X_train_te = te.fit_transform(X_train[["city"]], y_train)
X_test_te  = te.transform(X_test[["city"]])
```

`TargetEncoder` (sklearn 1.3+) does cross-fold encoding internally — within each CV fold, `city -> mean target` is computed on the *other* folds. No leakage. `smooth="auto"` shrinks small-count categories toward the global mean.

**Real-world.** Standard treatment of high-cardinality features. Cleaner than category-encoders' library historically.

**Follow-ups.** Multi-class target type. Combine with hashing for ultra-high cardinality. Use frequency encoding as a complement.

---

### Problem 9 — Pipeline + cross-validation for honest scoring

**Solution.**
```python
from sklearn.model_selection import cross_val_score, StratifiedKFold
import numpy as np

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(model, X_trainval, y_trainval, cv=skf, scoring="roc_auc", n_jobs=-1)
print(f"AUC: {scores.mean():.3f} ± {scores.std():.3f}  folds: {np.round(scores, 3)}")
```

**Why per-fold.** A 5-fold result of `[0.72, 0.71, 0.74, 0.73, 0.91]` (mean=0.76) is a red flag — investigate fold 5. Maybe a temporal split issue, or one fold has all the easy positives.

**Real-world.** Always look at fold variance. Means lie.

**Follow-ups.** `cross_validate` to get train/test/fit-time per fold. `RepeatedStratifiedKFold` for variance estimates.

---

### Problem 10 — Pipelines with imbalance handling

**Statement.** Combine SMOTE oversampling with a logistic regression in a leak-safe way.

**Solution.**
```python
from imblearn.pipeline import Pipeline as ImbPipeline    # NOT sklearn's Pipeline
from imblearn.over_sampling import SMOTE
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

pipe = ImbPipeline([
    ("scale", StandardScaler()),
    ("smote", SMOTE(random_state=42)),
    ("clf",   LogisticRegression(max_iter=1000)),
])
# in CV / GridSearch, SMOTE only resamples each training fold — not val
```

**Real-world.** A frequent bug is using sklearn's Pipeline with SMOTE — SMOTE then "resamples" the val/test fold too. `imblearn.pipeline.Pipeline` knows to skip resampling at predict time.

**Follow-ups.** Combined under+over with `SMOTEENN`. Class-weight as the simpler alternative.

---

### Problem 11 — Logistic regression baseline with proper scaling

**Solution.**
```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegressionCV

pipe = Pipeline([
    ("sc",  StandardScaler()),
    ("clf", LogisticRegressionCV(
                Cs=10, cv=5, scoring="roc_auc",
                penalty="l2", max_iter=2000,
                class_weight="balanced", n_jobs=-1, random_state=42)),
])
pipe.fit(X_train, y_train)
print("Best C:", pipe.named_steps["clf"].C_[0])
print("AUC:", pipe.score(X_val, y_val))
```

`LogisticRegressionCV` does internal CV to choose `C`. One-line baseline that often gets within a few % of XGBoost. **Always run this before reaching for boosting.**

**Real-world.** "We need a deep model" — does a tuned LR get 0.82 vs your model's 0.84? Stop and explain why the extra 2% matters for the business.

**Follow-ups.** L1 (sparse). Polynomial features. Calibration check (logistic is usually well-calibrated).

---

### Problem 12 — Lasso for feature selection

**Solution.**
```python
import numpy as np
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler

# scale first; otherwise penalty is unfair across features
sc = StandardScaler()
X_train_sc = sc.fit_transform(X_train)
lasso = LassoCV(cv=5, alphas=np.logspace(-4, 1, 50), n_jobs=-1, random_state=42)
lasso.fit(X_train_sc, y_train)
selected = np.where(np.abs(lasso.coef_) > 1e-5)[0]
print(f"Selected {len(selected)}/{X.shape[1]} features at alpha={lasso.alpha_:.4f}")
print(X.columns[selected].tolist())
```

**Real-world.** Useful as a sparse baseline and as a **feature selector** for downstream models. Lasso on 1000 features → top 50 → train tree model on those.

**Follow-ups.** `SelectFromModel(Lasso(...), threshold=...)` for plug-in selection inside a pipeline.

---

### Problem 13 — Read coefficients meaningfully

**Statement.** A logistic regression on scaled features says `coef[income]=0.7, coef[country_US]=-0.3`. What does this mean?

**Interpretation.**
- **Sign:** positive coef ⇒ feature increases probability of positive class.
- **Magnitude on scaled features:** comparable across features. `income` (0.7) influences predictions ~2.3× more than `country_US` (-0.3).
- **Per-unit interpretation:** for a unit-standardized feature, "1 SD increase in income raises log-odds by 0.7" → `exp(0.7) ≈ 2.0` → odds roughly double.

```python
import pandas as pd

clf = pipe.named_steps["clf"]
prep = pipe.named_steps["prep"]
feature_names = prep.get_feature_names_out()
coefs = pd.DataFrame({"feature": feature_names, "coef": clf.coef_[0],
                      "odds_ratio": np.exp(clf.coef_[0])}).sort_values("coef", key=abs, ascending=False)
```

**Real-world.** If you're deploying a logistic model, a stakeholder will ask "why was this user flagged?" — coefficients are your answer. Tree models get harder; that's where SHAP comes in (P33).

**Follow-ups.** Confidence intervals for coefficients (statsmodels). Feature interactions via PolynomialFeatures.

---

### Problem 14 — Polynomial features for non-linear linear regression

**Statement.** Predict `y = x^2 + 0.3*x*z + noise` with a linear model.

**Solution.**
```python
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import Ridge

pipe = Pipeline([
    ("poly", PolynomialFeatures(degree=2, interaction_only=False, include_bias=False)),
    ("sc",   StandardScaler()),
    ("clf",  Ridge(alpha=1.0)),
])
pipe.fit(X_train, y_train)
```

**Caveat.** Polynomial features explode quickly: 100 features at degree 2 → 5,150 features. Combine with Lasso for selection or use `interaction_only=True`.

**Real-world.** When the data is small and you suspect a known interaction, this beats a small tree. For large data, GBMs find interactions automatically.

**Follow-ups.** Splines (`SplineTransformer`) for smooth non-linear. Generalized additive models (`pygam`).

---

### Problem 15 — A complete LightGBM training run

**Solution.**
```python
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report

# example data
X, y = make_classification(n_samples=20000, n_features=30, n_informative=10,
                            weights=[0.9, 0.1], random_state=42)
X = pd.DataFrame(X, columns=[f"f{i}" for i in range(30)])
X_trv, X_te, y_trv, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
X_tr,  X_va, y_tr,  y_va = train_test_split(X_trv, y_trv, test_size=0.2, random_state=42, stratify=y_trv)

train_data = lgb.Dataset(X_tr, label=y_tr)
val_data   = lgb.Dataset(X_va, label=y_va, reference=train_data)

params = {
    "objective":"binary","metric":"auc","verbosity":-1,
    "learning_rate":0.05, "num_leaves":63, "min_data_in_leaf":50,
    "feature_fraction":0.9, "bagging_fraction":0.9, "bagging_freq":5,
    "lambda_l1":0.1, "lambda_l2":0.1, "is_unbalance":True, "seed":42,
}
model = lgb.train(params, train_data, num_boost_round=2000,
                   valid_sets=[val_data],
                   callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)])

pred = model.predict(X_te, num_iteration=model.best_iteration)
print("AUC:", round(roc_auc_score(y_te, pred), 3),
      "best_iter:", model.best_iteration)
```

**Real-world.** This is the template for 80% of tabular ML projects. Memorize the pattern.

**Follow-ups.** `lgb.cv()` for cross-validated training. Save with `model.save_model("model.txt")` (text format, version-portable).

---

### Problem 16 — XGBoost with histogram method on big data

**Solution.**
```python
import xgboost as xgb

dtr = xgb.DMatrix(X_tr, label=y_tr)
dva = xgb.DMatrix(X_va, label=y_va)
dte = xgb.DMatrix(X_te, label=y_te)

params = {
    "objective":"binary:logistic","eval_metric":"auc",
    "tree_method":"hist","learning_rate":0.05,"max_depth":6,
    "min_child_weight":1,"subsample":0.9,"colsample_bytree":0.9,
    "reg_lambda":1,"reg_alpha":0,
    "scale_pos_weight": (y_tr == 0).sum() / (y_tr == 1).sum(),
    "seed":42,
}

model = xgb.train(params, dtr, num_boost_round=2000,
                   evals=[(dtr,"train"),(dva,"val")],
                   early_stopping_rounds=50, verbose_eval=0)

pred = model.predict(dte, iteration_range=(0, model.best_iteration + 1))
```

`tree_method="hist"` is histogram-based — much faster than `exact` on large data. For GPU: `device="cuda"` (XGBoost 2.0+).

**Real-world.** XGBoost remains the most-deployed boosting framework — pick it if your org already has tooling and CI for it.

**Follow-ups.** `xgb.train` vs `XGBClassifier` (sklearn API). DART boosting (`booster="dart"`). Distributed XGBoost on Spark/Dask.

---

### Problem 17 — CatBoost for categorical-heavy data

**Solution.**
```python
from catboost import CatBoostClassifier, Pool

cat_features = ["country", "plan", "device", "city"]
train_pool = Pool(X_tr, y_tr, cat_features=cat_features)
val_pool   = Pool(X_va, y_va, cat_features=cat_features)

model = CatBoostClassifier(
    iterations=2000, learning_rate=0.05, depth=6,
    l2_leaf_reg=3, random_seed=42, eval_metric="AUC",
    early_stopping_rounds=50, verbose=0,
    auto_class_weights="Balanced",
)
model.fit(train_pool, eval_set=val_pool)
print("Best iter:", model.get_best_iteration())
```

CatBoost handles categoricals via **ordered target statistics** — robust to leakage and works well even on small data.

**Real-world.** Especially strong on datasets with many categorical features (city, brand, SKU). Often beats LGBM on these without hyperparameter tuning.

**Follow-ups.** Combine numerical + text + categorical. Use `cat_features` indices instead of names if columns aren't named.

---

### Problem 18 — Compare three models honestly

**Solution.**
```python
import time
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from lightgbm import LGBMClassifier
from xgboost  import XGBClassifier
from catboost import CatBoostClassifier

models = {
    "LGBM":    LGBMClassifier(n_estimators=500, learning_rate=0.05, num_leaves=63,
                                random_state=42, verbose=-1),
    "XGB":     XGBClassifier(n_estimators=500,  learning_rate=0.05, max_depth=6,
                                random_state=42, eval_metric="auc", verbosity=0),
    "CatBoost":CatBoostClassifier(iterations=500, learning_rate=0.05, depth=6,
                                    random_seed=42, verbose=0),
}

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
results = []
for name, model in models.items():
    scores, train_times = [], []
    for fold, (tr, va) in enumerate(skf.split(X, y)):
        t0 = time.perf_counter()
        m = model.__class__(**model.get_params())
        m.fit(X.iloc[tr], y.iloc[tr])
        train_times.append(time.perf_counter() - t0)
        proba = m.predict_proba(X.iloc[va])[:, 1]
        scores.append(roc_auc_score(y.iloc[va], proba))
    results.append({
        "model": name, "auc_mean": np.mean(scores), "auc_std": np.std(scores),
        "train_s": np.mean(train_times),
    })
import pandas as pd
print(pd.DataFrame(results))
```

**Real-world.** The right framing is "AUC ± std and training time." Sometimes XGBoost is 2 hours and CatBoost is 20 minutes for the same AUC — pick the latter.

**Follow-ups.** Add inference-time speed. Track GPU usage. Use `cross_validate` for cleaner output.

---

### Problem 19 — Categorical feature handling per algorithm

| Algorithm | Best treatment |
|---|---|
| LogisticRegression | OneHot + StandardScaler |
| RandomForest | OrdinalEncoder OK; OHE OK; OHE often slightly better |
| LightGBM | Native: `categorical_feature=[...]`; or OrdinalEncoder |
| XGBoost | OrdinalEncoder + `enable_categorical=True` (XGB 1.6+) |
| CatBoost | Native: `cat_features=[...]` — best in class |

**Don't** OneHot a 10k-cardinality column for a tree model; use ordinal or native handling. **Don't** use raw integer labels for a linear model unless they're truly ordinal — implies a meaningless ordering.

**Follow-ups.** Frequency encoding as additional feature. Embedding-based encoding via deep models (Module 8).

---

### Problem 20 — Feature importance from boosted trees

**Solution.**
```python
import pandas as pd
import lightgbm as lgb

# importance from LightGBM
imp = pd.DataFrame({
    "feature":  model.feature_name(),
    "split":    model.feature_importance(importance_type="split"),
    "gain":     model.feature_importance(importance_type="gain"),
}).sort_values("gain", ascending=False)
print(imp.head(20))
```

**Caveat.** "split" counts how often the feature is used; "gain" weights by improvement. **Gain is more meaningful.** Both are biased toward high-cardinality features — use permutation importance (P33) for unbiased ranking.

**Real-world.** Built-in importance is fine for "which features did the tree use a lot" — useful as a fast sanity check after training.

**Follow-ups.** SHAP for per-prediction explanations (P34). Compare gain to permutation to spot proxy features.

---

### Problem 21 — Optuna for LightGBM tuning

**Solution.** (See §9.1 for full code.)

Set a **budget** before starting (`n_trials=100` or `timeout=3600`). Persist the study so you can resume:
```python
study = optuna.create_study(
    study_name="lgbm-churn",
    storage="sqlite:///optuna.db",
    direction="maximize", load_if_exists=True,
    sampler=optuna.samplers.TPESampler(seed=42),
)
study.optimize(objective, n_trials=100, timeout=3600)
```

**Real-world.** TPE finds 95% of the gain in the first 30-50 trials. Tail trials only help marginally — don't run 1000-trial studies.

**Follow-ups.** Multi-objective (Optuna's `NSGAIISampler`) for AUC vs latency. Distributed trials with shared SQLite/MySQL storage.

---

### Problem 22 — Pruning under-performing trials

**Solution.**
```python
def objective(trial):
    params = {...}
    pruner_cb = optuna.integration.LightGBMPruningCallback(trial, "auc")
    train_data = lgb.Dataset(X_tr, label=y_tr)
    val_data   = lgb.Dataset(X_va, label=y_va, reference=train_data)
    model = lgb.train(params, train_data, num_boost_round=2000,
                       valid_sets=[val_data],
                       callbacks=[lgb.early_stopping(50), pruner_cb, lgb.log_evaluation(0)])
    return model.best_score["valid_0"]["auc"]

study = optuna.create_study(direction="maximize",
                             pruner=optuna.pruners.MedianPruner(n_startup_trials=10, n_warmup_steps=20))
study.optimize(objective, n_trials=100)
```

Pruning kills trials that look bad early. Under typical settings, 30-50% of trials get pruned, halving wall time.

**Real-world.** Pruning is a free speedup; always combine with TPE.

**Follow-ups.** HyperbandPruner. SuccessiveHalvingPruner. Custom pruners for non-LGBM frameworks.

---

### Problem 23 — Tune via cross-validation, not single split

**Solution.**
```python
def objective(trial):
    params = {...}
    skf = StratifiedKFold(5, shuffle=True, random_state=42)
    scores = []
    for tr_i, va_i in skf.split(X_trv, y_trv):
        d_tr = lgb.Dataset(X_trv.iloc[tr_i], label=y_trv.iloc[tr_i])
        d_va = lgb.Dataset(X_trv.iloc[va_i], label=y_trv.iloc[va_i], reference=d_tr)
        m = lgb.train(params, d_tr, num_boost_round=2000, valid_sets=[d_va],
                       callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)])
        scores.append(m.best_score["valid_0"]["auc"])
    return float(np.mean(scores))
```

**Why.** A single train/val split has variance. CV averages it out — better hyperparameters, less overfit-to-val-set.

**Real-world.** Cost: 5× the compute. Worth it for final tuning runs; prototype with single-split.

**Follow-ups.** Repeated CV. `lightgbm.cv()` directly with TPE.

---

### Problem 24 — Pick the search space

**Statement.** What ranges do you put in `trial.suggest_*` for LightGBM?

**Practical defaults:**
```python
{
  "learning_rate":    trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
  "num_leaves":       trial.suggest_int  ("num_leaves",     15, 255),
  "max_depth":        trial.suggest_int  ("max_depth",      -1,  16),
  "min_data_in_leaf": trial.suggest_int  ("min_data_in_leaf", 5, 500, log=True),
  "feature_fraction": trial.suggest_float("feature_fraction", 0.5, 1.0),
  "bagging_fraction": trial.suggest_float("bagging_fraction", 0.5, 1.0),
  "bagging_freq":     trial.suggest_int  ("bagging_freq",    1, 10),
  "lambda_l1":        trial.suggest_float("lambda_l1", 1e-3, 10, log=True),
  "lambda_l2":        trial.suggest_float("lambda_l2", 1e-3, 10, log=True),
  "min_gain_to_split": trial.suggest_float("min_gain_to_split", 0.0, 0.5),
}
```

**Tips.**
- `log=True` for learning rate, regularization, min-data — orders-of-magnitude effects.
- Keep `num_leaves` x `max_depth` reasonable: `num_leaves <= 2^max_depth`.
- Lock `objective`, `metric`, `seed` outside the search.

**Real-world.** Reuse the same search space across projects — too narrow misses the optimum, too wide wastes trials. The above is conservative but solid.

---

### Problem 25 — Pick the right classification metric

**Statement.** Six scenarios; for each, what metric do you optimize?

| Scenario | Right metric |
|---|---|
| Email spam filter (rare miss is annoying; false flag is bad) | **Precision** at high recall |
| Cancer screening (false negative is catastrophic) | **Recall** at high precision |
| Click-through prediction for ranking ads | **AUC-ROC** |
| Fraud detection (1% positives) | **AUC-PR** |
| Calibrated probabilities for downstream pricing | **Log loss** + **Brier** |
| Multi-class with imbalance | **macro-F1** or **balanced accuracy** |

**Real-world.** Stakeholders often say "accuracy" when they mean something else. Translate "accuracy" to the right metric for the cost asymmetry.

**Follow-ups.** Custom business-cost metrics: `cost = FP*$5 + FN*$50` — minimize on val, threshold accordingly.

---

### Problem 26 — Compute precision-recall curve and pick threshold

**Solution.**
```python
import numpy as np
from sklearn.metrics import precision_recall_curve

precisions, recalls, thresholds = precision_recall_curve(y_val, y_proba_val)

# best F1
f1s = 2 * precisions * recalls / np.maximum(precisions + recalls, 1e-9)
best = int(np.argmax(f1s[:-1]))                       # last point has no threshold
print(f"Best F1: {f1s[best]:.3f} @ threshold={thresholds[best]:.3f} "
      f"(precision={precisions[best]:.3f}, recall={recalls[best]:.3f})")

# threshold for fixed precision >= 0.9
mask = precisions[:-1] >= 0.9
if mask.any():
    idx = np.where(mask)[0]
    pick = idx[np.argmax(recalls[:-1][idx])]
    print(f"Threshold for precision>=0.9: {thresholds[pick]:.3f}, recall={recalls[pick]:.3f}")
```

**Real-world.** Picking thresholds is where ML meets business. Fix one (precision OR cost) and maximize the other.

**Follow-ups.** Per-cohort thresholds (different defaults for different user segments). Smoothed thresholds via Platt or isotonic.

---

### Problem 27 — Calibration check + recalibration

**Solution.**
```python
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve, CalibratedClassifierCV
from sklearn.metrics import brier_score_loss

# diagnostic: reliability curve
prob_true, prob_pred = calibration_curve(y_val, y_proba_val, n_bins=10)
print("Brier:", brier_score_loss(y_val, y_proba_val))

# fix it
cal = CalibratedClassifierCV(base_estimator=model, method="isotonic", cv=5)
cal.fit(X_trv, y_trv)
y_proba_cal = cal.predict_proba(X_te)[:, 1]
print("Brier after isotonic:", brier_score_loss(y_te, y_proba_cal))
```

**Real-world.** SVMs and MLPs are usually miscalibrated. Trees are usually decent. Recalibration is a free improvement when probabilities feed into downstream decisions.

**Follow-ups.** Platt vs isotonic — Platt for small data, isotonic for >1k validation samples.

---

### Problem 28 — Multiclass classification metrics

**Solution.**
```python
from sklearn.metrics import classification_report, confusion_matrix, f1_score

print(classification_report(y_te, y_pred, digits=3))
# precision, recall, f1 per class + macro avg, weighted avg

print("macro F1:",    f1_score(y_te, y_pred, average="macro"))
print("weighted F1:", f1_score(y_te, y_pred, average="weighted"))

import seaborn as sns
sns.heatmap(confusion_matrix(y_te, y_pred), annot=True, fmt="d")
```

**Macro vs weighted:** macro treats every class equally; weighted weights by support. Use macro for balanced classes; weighted for imbalanced.

**Real-world.** A 99% accuracy on 100-class problem might be "90% accuracy on 1 class with 99% of data, 0% on the other 99 classes." Macro F1 catches this.

---

### Problem 29 — Regression metrics done right

**Solution.**
```python
import numpy as np
from sklearn.metrics import (mean_absolute_error, mean_squared_error, mean_absolute_percentage_error,
                              r2_score, mean_squared_log_error)

y_pred = model.predict(X_te)
print("MAE :", mean_absolute_error(y_te, y_pred))
print("RMSE:", np.sqrt(mean_squared_error(y_te, y_pred)))
print("MAPE:", mean_absolute_percentage_error(y_te, y_pred))
print("R2  :", r2_score(y_te, y_pred))

# for targets that span orders of magnitude:
print("MSLE:", mean_squared_log_error(np.maximum(y_te,0), np.maximum(y_pred,0)))
```

**Use:**
- **MAE**: easy to communicate ("avg error 5 dollars"). Robust to outliers.
- **RMSE**: penalizes big mistakes. Standard for "smooth" errors.
- **MAPE**: percentage error. Breaks at zero. Good for varying-scale.
- **MSLE**: log-scale errors. Useful for skewed targets (revenue, count).
- **R²**: "fraction of variance explained" — interpretable but sensitive to test set.

**Real-world.** Pick the metric that aligns with the business cost. Forecasting: usually MAPE or RMSE. Property prices: often MAE (median dollars off).

---

### Problem 30 — Imbalanced data, three approaches compared

**Solution.**
```python
import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LogisticRegression
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from sklearn.preprocessing import StandardScaler

base = LogisticRegression(max_iter=1000, random_state=42)

approaches = {
    "default":    [("sc", StandardScaler()), ("clf", base)],
    "balanced":   [("sc", StandardScaler()), ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42))],
    "smote":      [("sc", StandardScaler()), ("smote", SMOTE(random_state=42)),
                    ("clf", LogisticRegression(max_iter=1000, random_state=42))],
    "undersample":[("sc", StandardScaler()), ("us", RandomUnderSampler(random_state=42)),
                    ("clf", LogisticRegression(max_iter=1000, random_state=42))],
}

for name, steps in approaches.items():
    pipe = ImbPipeline(steps)
    auc = cross_val_score(pipe, X, y, cv=5, scoring="average_precision", n_jobs=-1).mean()
    print(f"{name:12s}: AUC-PR = {auc:.3f}")
```

**Typical result.** `class_weight="balanced"` and SMOTE are nearly tied; both beat default. Undersample loses information unless data is huge. `class_weight` is the simplest and usually sufficient.

**Real-world.** Try `class_weight="balanced"` first. Resort to SMOTE only if it noticeably helps.

**Follow-ups.** Focal loss for very imbalanced (deep models). Cost-sensitive learning.

---

### Problem 31 — Cost-sensitive thresholding

**Statement.** Each false positive costs $5; each false negative costs $50. Pick the threshold that minimizes total cost.

**Solution.**
```python
import numpy as np

def expected_cost(y_true, y_proba, threshold, cost_fp=5, cost_fn=50):
    pred = (y_proba >= threshold).astype(int)
    fp = ((pred == 1) & (y_true == 0)).sum()
    fn = ((pred == 0) & (y_true == 1)).sum()
    return fp * cost_fp + fn * cost_fn

thresholds = np.linspace(0.01, 0.99, 99)
costs = [expected_cost(y_val, y_proba_val, t) for t in thresholds]
best_t = thresholds[int(np.argmin(costs))]
print(f"Optimal threshold: {best_t:.2f}, cost: ${min(costs)}")
```

**Real-world.** This is the right way to convert a model's probability into a decision. Many deployed models still use 0.5 by accident.

**Follow-ups.** Per-segment costs (different user types have different FN/FP costs). Update costs over time as the business evolves.

---

### Problem 32 — Calibrate XGBoost output

**Statement.** XGBoost is well-calibrated by default? Verify, and recalibrate if needed.

**Solution.**
```python
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import brier_score_loss
import xgboost as xgb

clf = xgb.XGBClassifier(n_estimators=300, learning_rate=0.05, max_depth=6,
                         eval_metric="auc", random_state=42)
clf.fit(X_tr, y_tr)
proba = clf.predict_proba(X_va)[:, 1]
print("Brier raw:", brier_score_loss(y_va, proba))

# inspect calibration curve
prob_true, prob_pred = calibration_curve(y_va, proba, n_bins=10)
# if prob_true diverges meaningfully from prob_pred, recalibrate

cal = CalibratedClassifierCV(clf, method="isotonic", cv=5)
cal.fit(X_tr, y_tr)
proba_cal = cal.predict_proba(X_va)[:, 1]
print("Brier calibrated:", brier_score_loss(y_va, proba_cal))
```

**Real-world.** XGBoost defaults are usually near-calibrated, but a CalibratedClassifierCV wrap rarely hurts and often shaves a few % off Brier.

---

### Problem 33 — Permutation importance (model-agnostic)

**Solution.**
```python
from sklearn.inspection import permutation_importance
import pandas as pd

result = permutation_importance(model, X_val, y_val,
                                 scoring="roc_auc", n_repeats=10,
                                 random_state=42, n_jobs=-1)
imp = pd.DataFrame({
    "feature": X_val.columns,
    "imp_mean": result.importances_mean,
    "imp_std":  result.importances_std,
}).sort_values("imp_mean", ascending=False)
print(imp.head(20))
```

**Why.** Model-agnostic, unbiased toward cardinality, intuitive ("how much does the score drop if I randomize feature X?").

**Caveat.** Slow on big test sets — sample. Correlated features can both look low (because the model can use the other one).

**Real-world.** A staple for trustworthy global feature importance reports.

**Follow-ups.** Conditional permutation for correlated features. Per-class importance for multiclass.

---

### Problem 34 — SHAP explanations for a tree model

**Solution.**
```python
import shap

# fast for tree models
explainer = shap.TreeExplainer(lgb_model)
shap_values = explainer.shap_values(X_val)
# for binary classification, shap_values is a 2D array [n_samples, n_features]
#    (or a list of 2 arrays in older shap versions; compatible)

# global summary plot
shap.summary_plot(shap_values, X_val)              # plt.show() afterwards in scripts

# top features by mean(|shap|)
import numpy as np, pandas as pd
imp = pd.DataFrame({
    "feature": X_val.columns,
    "mean_abs_shap": np.abs(shap_values).mean(axis=0),
}).sort_values("mean_abs_shap", ascending=False)

# explain a single prediction
i = 0
print("Prediction:", lgb_model.predict(X_val.iloc[i:i+1])[0])
contributions = pd.DataFrame({
    "feature": X_val.columns,
    "value":   X_val.iloc[i].values,
    "shap":    shap_values[i],
}).sort_values("shap", key=abs, ascending=False)
print(contributions.head(10))
```

**Real-world.** SHAP is the standard for "explain this prediction" in tabular ML. Used in production at fintech / healthcare / hiring for decision auditability.

**Follow-ups.** SHAP interaction values (`shap_interaction_values`). Force / waterfall plots for individual rows. Sample for speed on big test sets.

---

### Problem 35 — Detect a leaky feature with SHAP

**Statement.** Your top SHAP feature has 30× the importance of the next feature. Is that a leak?

**Investigation.**
1. **Plot SHAP dependence:** `shap.dependence_plot("suspect_feature", shap_values, X_val)`. If small changes in the feature flip the prediction, that's suspicious.
2. **Check the lineage:** how is this feature computed? Does it use the target column or any post-event data?
3. **Train without it:** drop the feature, retrain. If AUC drops from 0.99 to 0.75, your model basically *was* this feature — strong sign of leakage.
4. **Ask domain experts:** "is `last_login_date` known *before* a churn decision?" Often the answer is "no, we compute that nightly after we know they churned."

**Real-world.** "We have an awesome feature" is often "we have a leak we haven't noticed." Always do this check before declaring success.

**Follow-ups.** Drop-column importance (slower but conclusive). Feature lineage tracing in dbt / feature store.

---

### Problem 36 — Serve a model behind FastAPI

**Solution.** (Combines Modules 4, 6, and 7.)

```python
# train.py
import joblib
from sklearn.pipeline import Pipeline
# ... build and train pipe ...
joblib.dump(pipe, "/artifacts/model.joblib", compress=3)

# also save metadata
import json
with open("/artifacts/feature_schema.json", "w") as f:
    json.dump({
        "features": ["age", "income", "country", "plan", "tenure_days"],
        "version":  "v3.1.0",
        "trained_at": "2026-04-27",
        "metrics": {"auc": 0.86, "brier": 0.12},
    }, f, indent=2)
```

```python
# serve.py — FastAPI service
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pandas as pd
import joblib, json, structlog
from typing import Annotated

log = structlog.get_logger()

app = FastAPI(title="churn-predictor", version="3.1.0")

@app.on_event("startup")
def load_model():
    app.state.pipe = joblib.load("/artifacts/model.joblib")
    with open("/artifacts/feature_schema.json") as f:
        app.state.schema = json.load(f)

class Features(BaseModel):
    age: Annotated[int,    Field(ge=0, le=120)]
    income: Annotated[float, Field(ge=0)]
    country: str
    plan: str
    tenure_days: Annotated[int, Field(ge=0)]

@app.post("/predict")
def predict(payload: Features):
    df = pd.DataFrame([payload.model_dump()])
    try:
        proba = float(app.state.pipe.predict_proba(df)[0, 1])
    except Exception as e:
        log.exception("prediction_failed", error=str(e))
        raise HTTPException(500, "prediction error")
    log.info("prediction", proba=proba, version=app.state.schema["version"])
    return {"churn_prob": proba, "model_version": app.state.schema["version"]}

@app.get("/health")
def health(): return {"status": "ok"}
```

Build the Docker image (Module 6 §6.1), deploy to Cloud Run (Module 6 §5.2). Wire up Prometheus metrics (Module 4 §15.3) for `/metrics`. Set up alerts on prediction-rate drops or latency spikes.

**Real-world.** This is the deployable artifact — a self-contained service. The fact that it's just a FastAPI on a container is the *point*: model serving is not magic.

**Follow-ups.** Batch predict endpoint (`/predict-batch`). A/B testing two model versions (Module 6 P30). Feature lookup from a feature store (Module 12).

---

## 16. Three mini-projects

### Mini-project A — Tabular churn predictor end-to-end
A real-ish e-commerce dataset (synthesize with `sklearn.datasets.make_classification` plus categorical noise, or use the public Telco churn data). Build:
1. EDA notebook with leakage checks.
2. Feature pipeline (numeric + categorical + time-based).
3. Three models (LR baseline, LightGBM, CatBoost) compared with CV.
4. Optuna tuning on the winner (50 trials).
5. SHAP report.
6. Calibration + threshold pick.
7. Serialized pipeline + metadata bundle.
8. FastAPI service (Module 4) in Docker (Module 6).
9. README with all metrics and one-page model card.

**Skills exercised:** every section. This is your portfolio piece.

### Mini-project B — Time-series forecasting with feature engineering
Daily revenue per store. Build lag/rolling features; LightGBM with `TimeSeriesSplit`; per-store error analysis; backtested forecasts vs naive baseline (last-week-same-day).

**Skills exercised:** time-series splits, lag/rolling features, group-aware modeling.

### Mini-project C — Imbalanced fraud-style classifier
Fraud-style data (1% positive). Compare class_weight, SMOTE, undersample, focal-loss XGBoost. Pick the threshold for fixed precision (95%) and report recall. Build a per-segment threshold (different thresholds for new vs returning users).

**Skills exercised:** imbalance handling, AUC-PR, threshold tuning, segment-aware thresholds.

---

## 17. Real-world usage map

| Concept | Where it returns later |
|---|---|
| Pipeline + ColumnTransformer | Module 8 (DL) for tabular preprocessing; Module 12 for production pipelines |
| Train-serve skew prevention | Module 12 (MLOps), Module 13 (LLMOps) |
| Group-aware splits | Module 8 NLP/CV (per-document or per-image splits); Module 10 RAG eval |
| Feature engineering patterns | Module 12 feature stores; Module 13 LLM eval features |
| LightGBM / XGBoost | Still the production workhorse on tabular data; ensemble with deep models |
| Optuna | Module 8 (DL hyperparameter tuning), Module 11 (agent prompt search) |
| SHAP explanations | Stakeholder reports for any tabular model; debugging before production |
| Calibration | Module 13 — calibrated LLM-as-judge scores |
| FastAPI + serialization | Module 8 (DL serving), Module 10 (LLM serving); same pattern |

---

## 18. Interview pitfalls — what NOT to say

- **"Accuracy is the right metric."** Almost never. Be specific about the cost asymmetry.
- **"Random Forest is enough."** Defensible, but on tabular data GBMs typically win. Justify.
- **"I tuned hyperparameters by hand."** Use Optuna; explain the search space; show the budget.
- **"I scaled features before splitting."** Leakage. Pipeline scales inside CV folds.
- **"99.5% AUC, ship it!"** That's a red flag for leakage. Run P4's diagnostic.
- **"The default threshold is fine."** Tune for the cost matrix. State assumptions.
- **"I'll just use SMOTE."** It rarely beats `class_weight="balanced"`. Compare both.
- **"Feature importance shows X is most important."** Built-in importance is biased; use permutation or SHAP for honest comparison.
- **"I dropped feature X because it was correlated with Y."** Trees handle correlation fine; dropping doesn't necessarily help. Show before/after.
- **"My CV gave 0.85; let me also report test 0.84."** State which decisions were made on val vs test. The test set should be touched ONCE.
- **"`fit(X, y)` on the full data and submit."** Acceptable for the *final* model after honest evaluation; document it explicitly.
- **"PCA always helps."** It rarely helps tree models. For linear/distance-based methods, sometimes.
- **"I'll use OneHot for `city` (50k unique)."** That's 50k columns. Use ordinal/native or target encoding.
- **"My model is black box, can't explain."** SHAP exists. Use it.

**How to communicate.** When presenting an ML project, narrate (1) problem framing + metric choice, (2) data and split strategy with leakage check, (3) baseline model, (4) feature engineering decisions with reasons, (5) model class + tuning, (6) honest test evaluation + calibration, (7) interpretation (SHAP), (8) deploy + monitoring plan.

---

## 19. Cheatsheet

```text
WORKFLOW
  Frame -> Collect -> Split (LEAK-FREE) -> Baseline ->
  Features -> Train -> Tune -> Test ONCE -> Calibrate ->
  Threshold -> Interpret -> Save bundle -> Deploy -> Monitor

SPLITS
  random:    train_test_split(X, y, test_size=0.15, random_state=42, stratify=y)
  group:     GroupShuffleSplit(test_size=0.2).split(X, y, groups=g)
  time:      TimeSeriesSplit(n_splits=5)  OR  chronological + embargo
  stratified+grouped: StratifiedGroupKFold

PIPELINE (the deploy artifact)
  ColumnTransformer([
      ("num", Pipeline([SimpleImputer("median"), StandardScaler()]), numeric_cols),
      ("cat", Pipeline([SimpleImputer("most_frequent"),
                         OneHotEncoder(handle_unknown="ignore", sparse_output=False)]),
                cat_cols),
  ], remainder="drop")
  Pipeline([("prep", prep), ("clf", LogisticRegression(max_iter=1000))])

ENCODERS
  low cardinality:  OneHotEncoder(handle_unknown="ignore")
  ordinal/trees:    OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
  high cardinality: TargetEncoder(target_type="binary", cv=5)
  CatBoost native:  Pool(X, y, cat_features=[...])

LIGHTGBM (defaults that work)
  params = {
      "objective":"binary","metric":"auc","verbosity":-1,
      "learning_rate":0.05, "num_leaves":63, "min_data_in_leaf":50,
      "feature_fraction":0.9, "bagging_fraction":0.9, "bagging_freq":5,
      "lambda_l1":0.1, "lambda_l2":0.1, "is_unbalance":True, "seed":42,
  }
  lgb.train(params, train_data, num_boost_round=2000,
             valid_sets=[val], callbacks=[lgb.early_stopping(50)])

XGBOOST
  xgb.train({"objective":"binary:logistic","eval_metric":"auc","tree_method":"hist",...},
             dtrain, num_boost_round=2000, evals=[...], early_stopping_rounds=50)

CATBOOST
  CatBoostClassifier(iterations=2000, learning_rate=0.05, depth=6,
                       l2_leaf_reg=3, random_seed=42,
                       early_stopping_rounds=50, verbose=0,
                       cat_features=[...], auto_class_weights="Balanced")

OPTUNA (TPE + pruning)
  sampler = optuna.samplers.TPESampler(seed=42)
  pruner  = optuna.pruners.MedianPruner(n_startup_trials=10, n_warmup_steps=20)
  study   = optuna.create_study(direction="maximize", sampler=sampler, pruner=pruner)
  study.optimize(objective, n_trials=100, timeout=3600)

METRICS — CLASSIFICATION
  AUC-ROC:  imbalanced OK, threshold-free, ranking quality
  AUC-PR:   imbalanced, focus on positive class
  F1:       balance precision/recall
  log loss: probability quality
  Brier:    calibration
  always: classification_report(y_te, y_pred), confusion_matrix

METRICS — REGRESSION
  MAE  — robust, easy to communicate
  RMSE — penalizes large errors
  MAPE — % error; breaks at zero
  MSLE — orders-of-magnitude targets
  R²   — variance explained

THRESHOLDING
  precision_recall_curve(y, proba) -> precisions, recalls, thresholds
  pick by: best F1, fixed precision, or business cost (FP*$, FN*$)

CALIBRATION
  CalibratedClassifierCV(model, method="isotonic", cv=5)
  brier_score_loss; calibration_curve

IMBALANCE
  1) class_weight="balanced"  (try first)
  2) imblearn.pipeline + SMOTE / RandomUnderSampler  (NOT sklearn's Pipeline!)
  3) custom loss (focal) for deep models
  metric: AUC-PR  not AUC-ROC; threshold not 0.5

INTERPRETABILITY
  SHAP (TreeExplainer for trees; KernelExplainer for anything)
    shap_values = explainer.shap_values(X_val)
    summary_plot, dependence_plot, force_plot
  permutation_importance (model-agnostic, unbiased)
  PDP / ICE for "average effect of feature X"
  built-in feature_importances_ — biased toward high-cardinality

DEPLOY
  joblib.dump(pipe, "model.joblib", compress=3)  — pipeline, not just model
  bundle: model.joblib + feature_schema.json + metrics.json + manifest
  pin sklearn version in serving image
  ONNX for cross-version stability
  FastAPI route: pydantic in -> pipe.predict_proba -> JSON out
  schema validation; structured logs with version stamp

ANTI-PATTERNS (avoid)
  fit on full data before split; default max_iter=100
  AUC-ROC on imbalanced (use AUC-PR); test set used for tuning
  random split on time-series; OHE 50k-cardinality column
  built-in importance for compare; saving model not pipeline
  threshold = 0.5 by default; SMOTE in sklearn pipeline (use imblearn)
```

---

## 20. Prerequisites & next steps

**Prerequisites covered? You can:**
- Frame an ML problem and pick the right metric for the cost asymmetry.
- Build leak-free train/val/test splits (random, group-aware, time-aware).
- Wrap preprocessing + model in a sklearn `Pipeline` that's safe for CV and serving.
- Run a logistic-regression baseline before reaching for boosting.
- Train and tune LightGBM/XGBoost/CatBoost with early stopping.
- Drive an Optuna study with TPE + pruning + bounded budget.
- Pick classification metrics, threshold, and calibrate probabilities.
- Handle imbalance with `class_weight`, SMOTE, and threshold tuning.
- Interpret a model globally (permutation importance, SHAP summary) and per-prediction (SHAP).
- Save a model-as-pipeline bundle and serve it behind a FastAPI service in a container.

**Next steps in the bible:**
- **Module 8 — Deep Learning.** PyTorch, training loops, transfer learning. Many tabular problems still benefit from gradient-boosting; deep models shine on unstructured (text/image) data.
- **Module 12 — MLOps.** Feature stores, model registries, monitoring, retraining. The infrastructure around what you built here.
- **Module 13 — LLMOps.** Many "modern" LLM apps still benefit from a classical ML layer (retrieval ranker, intent classifier, relevance re-ranker).

**External study (only if you want depth):**
- *Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow* (Géron) — the standard textbook; sklearn chapters are excellent.
- *The Elements of Statistical Learning* (Hastie, Tibshirani, Friedman) — the theory backbone; free online.
- *Feature Engineering for Machine Learning* (Zheng & Casari) — brief, focused on the highest-leverage skill.
- The XGBoost, LightGBM, CatBoost, and SHAP project docs — increasingly the right reference for production tuning.

---

*End of Module 7. Module 8 covers Deep Learning — PyTorch, training loops, transfer learning, distributed training, debugging, mixed precision — same structure, 35+ problems.*
