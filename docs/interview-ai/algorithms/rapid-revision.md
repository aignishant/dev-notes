# Rapid Revision

Read this the morning of the interview. It's a concentrated residue of the whole site — formulas, decision heuristics, and phrases that score points.

---

## The Algorithm Decision Tree

```
Is the task supervised?
├── YES
│   ├── Regression
│   │   ├── Need extrapolation / monotonicity
│   │   │   → Linear / Ridge / Lasso / GAM
│   │   ├── Complex relationships, tabular
│   │   │   → LightGBM / XGBoost
│   │   └── Time series component
│   │       → LightGBM + lag features, or Prophet/ARIMA
│   └── Classification
│       ├── Tabular, general
│       │   → LightGBM
│       ├── Text, small data
│       │   → Logistic + TF-IDF
│       ├── Text, max accuracy
│       │   → DistilBERT / RoBERTa fine-tune
│       ├── Images
│       │   → Pretrained CNN fine-tune
│       └── Very imbalanced
│           → LightGBM + class_weight + PR-AUC + threshold tuning
└── NO (unsupervised)
    ├── Clustering
    │   ├── Known K, interpretable
    │   │   → K-means
    │   ├── Unknown K, noise present
    │   │   → HDBSCAN
    │   ├── Non-convex shapes
    │   │   → Spectral clustering
    │   └── Soft assignments / density
    │       → GMM
    ├── Dimensionality reduction
    │   ├── Linear, variance-based
    │   │   → PCA
    │   ├── Non-linear, visualization
    │   │   → UMAP (or t-SNE)
    │   └── Non-negative data
    │       → NMF
    └── Anomaly detection
        ├── Tabular, general
        │   → Isolation Forest
        ├── Local anomalies
        │   → LOF
        ├── Gaussian-like
        │   → Elliptic Envelope
        └── High-dim / sequence
            → Autoencoder reconstruction error
```

---

## The Formulas That Always Get Asked

**OLS closed form:**
$$
\hat{\beta} = (X^\top X)^{-1} X^\top y
$$

**Ridge closed form:**
$$
\hat{\beta}_\text{ridge} = (X^\top X + \lambda I)^{-1} X^\top y
$$

**Logistic regression:**
$$
P(y=1|x) = \sigma(w^\top x) = \frac{1}{1 + e^{-w^\top x}}
$$

**Binary cross-entropy:**
$$
L = -\frac{1}{n}\sum_i [y_i \log p_i + (1-y_i)\log(1-p_i)]
$$

**Gini impurity:**
$$
\text{Gini} = 1 - \sum_k p_k^2
$$

**Entropy:**
$$
H = -\sum_k p_k \log_2 p_k
$$

**Hinge loss (SVM):**
$$
L = \max(0, 1 - y \cdot f(x))
$$

**Softmax:**
$$
P(y=k|x) = \frac{e^{w_k^\top x}}{\sum_j e^{w_j^\top x}}
$$

**KNN distance (Euclidean):**
$$
d(x, y) = \sqrt{\sum_i (x_i - y_i)^2}
$$

**Cosine similarity:**
$$
\cos(x, y) = \frac{x \cdot y}{\|x\| \|y\|}
$$

**NDCG:**
$$
\text{NDCG}_k = \frac{\text{DCG}_k}{\text{IDCG}_k}, \quad \text{DCG}_k = \sum_{i=1}^{k} \frac{2^{\text{rel}_i} - 1}{\log_2(i+1)}
$$

---

## Tree Ensembles At a Glance

| Algo | Key idea | Best for | Gotcha |
|---|---|---|---|
| Decision tree | Greedy splits | Baseline, explainable | High variance alone |
| Random Forest | Bagging + feature subsample | Messy data, no tuning | Doesn't extrapolate |
| AdaBoost | Reweight wrong points | Simple, classical | Sensitive to outliers |
| GBM | Fit negative gradients | Strong baseline | Overfits without LR shrink |
| XGBoost | 2nd-order + regularized | Kaggle, production | Tuning-heavy |
| LightGBM | Histogram + leaf-wise | Large data, fastest | Leaf-wise can overfit small data |
| CatBoost | Ordered encoding + oblivious | High-cardinality cats | Slightly slower training |

---

## Linear Models Cheat Sheet

| Need | Model |
|---|---|
| Continuous target | Linear regression |
| Binary target | Logistic regression |
| Count target | Poisson regression |
| Positive-skewed target | Gamma regression |
| Feature selection | Lasso (L1) |
| Correlated features | Ridge (L2) |
| Both | ElasticNet |
| Multiclass | Softmax (multinomial logistic) |

**L1 vs L2:**

- L1: diamond constraint, corners on axes → sparse (feature selection).
- L2: circular constraint, smooth → shrinks but doesn't zero.

---

## Clustering at a Glance

| Algo | Shape handled | K needed? | Noise |
|---|---|---|---|
| K-means | Spherical, equal size | Yes | No |
| GMM | Elliptical, soft | Yes | No |
| DBSCAN | Arbitrary | No | Yes |
| HDBSCAN | Variable density | No | Yes |
| Hierarchical | Flexible | No | No |
| Spectral | Non-convex | Yes | No |

**Picking K:** Elbow + silhouette + domain. No statistical test.

---

## Dimensionality Reduction at a Glance

| Method | Linear? | Use for | Keep in mind |
|---|---|---|---|
| PCA | Yes | Variance-preserving dim reduction | Scale features first |
| Kernel PCA | No | Non-linear, small data | O(n²) memory |
| LDA | Yes | Supervised, classification | Max K-1 dims |
| ICA | Yes | Source separation | Needs non-Gaussian |
| NMF | Yes | Parts-based, non-neg data | Topic modeling |
| t-SNE | No | Visualization | Don't use for ML pipeline |
| UMAP | No | Visualization + clustering | Much faster than t-SNE |
| Autoencoder | No | Deep, high-dim | Needs enough data |

---

## Time Series Quick Reference

**Stationarity tests:**
- ADF: $H_0$ = non-stationary. Low p → stationary.
- KPSS: $H_0$ = stationary. High p → stationary.

**Making stationary:**
- Differencing for trend.
- Log/Box-Cox for variance.
- Seasonal differencing for seasonality.

**Model picks:**

| Situation | Model |
|---|---|
| Single series, trend + seasonality | SARIMA or ETS |
| Robust with holidays | Prophet |
| Many related series | Global LightGBM or DeepAR |
| Rich covariates | LightGBM or TFT |
| Probabilistic forecasts | State space, DeepAR |

**Validation:** Time-based split, walk-forward. NEVER random.

---

## Recommender Quick Reference

**Approaches:**

- Content-based: item features → solves cold start for items.
- Collaborative filtering: user-item interactions → captures latent patterns.
- Hybrid: best of both.
- Two-tower: dominant modern approach.

**Stages:**

1. Retrieval (fast, recall-focused) → multiple retrievers union.
2. Ranking (precise, scoring) → LightGBM / deep ranker.
3. Re-ranking (diversity, freshness) → MMR, bandits.

**Evaluation:**

- Offline: NDCG@k, MAP, hit rate, coverage.
- Online: CTR, CVR, session length, retention.

**Cold start fix:** Content features via two-tower.

---

## Scenarios → Algorithm

| Scenario | Pick |
|---|---|
| Fraud detection (0.1% positive, real-time) | LightGBM + SHAP + threshold tuning |
| Customer churn (interpretable) | LightGBM + SHAP |
| Demand forecasting, many SKUs | Global LightGBM with lag features |
| New product recommender | Two-tower with content features |
| Anomaly on time series | LSTM autoencoder |
| Text classification, 20 classes, 50K docs | Logistic + TF-IDF baseline → DistilBERT |
| Image classification | Pretrained CNN/ViT fine-tune |
| Customer segmentation | K-means, K=5 |
| House price prediction | LightGBM + SHAP (or Ridge for monotonic) |
| Search ranking | LightGBM + LambdaRank |

---

## Red-Flag Phrases to Avoid

- ❌ "I'd use a neural network because it's more powerful."
- ❌ "SMOTE always helps imbalance."
- ❌ "R² is 0.95 so the model is great."
- ❌ "K-means clusters will naturally emerge."
- ❌ "Accuracy is the main metric."
- ❌ "I'd split 80/20 randomly." *(for time series)*

## Green-Flag Phrases That Score Points

- ✅ "Let me start with the simplest baseline."
- ✅ "What's the business cost of FP vs FN?"
- ✅ "I'd use time-based splits to avoid leakage."
- ✅ "PR-AUC is more meaningful than ROC-AUC here given the imbalance."
- ✅ "I'd A/B test before trusting offline metrics."
- ✅ "What does the team need to maintain this?"
- ✅ "Before I pick a model, I'd want to understand the data."

---

## Final Check (30 seconds before each interview)

- Breathe.
- Clarify before you solve.
- Name a baseline first.
- Justify every choice in terms of the **data, constraints, and business goal.**
- If you don't know, say so and describe how you'd find out.

You've got this.
