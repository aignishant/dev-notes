# Module 8 — Algorithm Selection

Ten scenario questions. By this point you know the algorithms. This module tests whether you can **pick the right one** given constraints. Interviewers use these to distinguish candidates who've memorized algorithms from those who can actually use them.

---

## Q126. How do you systematically pick an algorithm for a new problem? { #q126 }

**Decision framework (in order):**

**1. What's the task?**

- Classification / regression → supervised.
- Grouping / anomaly detection → unsupervised.
- Sequential decisions → reinforcement learning.
- Predict next step → sequence models or time series.

**2. What does the data look like?**

- **Size:** < 1K rows, 1K–100K, 100K–10M, > 10M. Each tier unlocks different algorithms.
- **Type:** Tabular, images, text, time series, graphs, multi-modal.
- **Label availability:** Full labels, weak labels, none.
- **Balance:** Balanced, imbalanced, extreme (fraud).
- **Quality:** Clean, noisy, adversarial, missing values.

**3. What are the constraints?**

- **Latency:** Real-time (<50ms) vs batch (hours).
- **Memory:** Edge device vs server.
- **Interpretability:** Legally required or not.
- **Update frequency:** Daily retrain vs monthly.
- **Accuracy requirements:** 99% needed or 80% enough.

**4. What's the maturity of the problem?**

- First attempt → baseline (logistic, random forest).
- Existing model → targeted improvement.
- Research → try SOTA.

**5. What does the team know?**

- Maintainability matters. A LightGBM model your team understands beats a transformer they don't.

<div class="tip-box" markdown>
**Senior signal:** In interviews, candidates who start with "it depends" and then systematically ask about data and constraints win. Candidates who jump straight to "I'd use XGBoost" seem junior.
</div>

---

## Q127. Scenario: predict whether a credit card transaction is fraud. { #q127 }

**Constraints given:**

- Binary classification.
- Extreme imbalance (~0.1% fraud).
- Real-time decision (< 20ms).
- Regulatory: must explain rejections.
- High cost of false negatives (miss fraud = $$$ loss).
- High cost of false positives (reject valid customer = churn).

**Algorithm choice: Gradient Boosting (LightGBM/XGBoost).**

**Reasoning:**

- **Tabular data** with transaction features → GBDT is default.
- **Imbalance handling:** `scale_pos_weight`, focal loss, or PR-AUC optimization.
- **Fast inference:** 100-tree model predicts in ~1ms. CatBoost oblivious trees faster still.
- **Interpretability:** SHAP values explain individual rejections. Critical for regulatory compliance.
- **Features:** Aggregations over time windows (spend in last 1h, last 7 days), velocity features (transactions per minute), device/IP features.

**Not choosing:**

- **Deep learning:** Overkill. Latency risk. Harder to explain.
- **Logistic regression:** Won't capture complex interactions.
- **Random Forest:** Inferior to boosting on imbalanced data.
- **Isolation Forest:** For unsupervised; here we have labels.

**Full system:**

```
[Transaction]
    ↓
[Rules engine] → hard rules (blacklisted card, known fraud pattern)
    ↓ passed
[LightGBM model] → probability of fraud
    ↓
[Threshold tuning] → threshold set by cost curve (FP vs FN cost)
    ↓
[SHAP explanation] → top 3 features contributing to rejection
    ↓
[Decision + log]
```

**Monitoring:**

- Precision at high-recall thresholds.
- Feature drift alerts (e.g., sudden rise in card-not-present transactions).
- Adversarial concept drift (fraudsters adapt).

---

## Q128. Scenario: forecast daily sales for 10,000 SKUs in 1,000 stores. { #q128 }

**Scale:** 10M × 365 = 3.65B time-series points per year.

**Algorithm choice: Global LightGBM with lag features + hierarchical reconciliation.**

**Reasoning:**

- **10M series** is too many for per-series ARIMA (training cost explodes).
- **Global models** (one model across all series) exploit shared patterns.
- **LightGBM** handles mixed feature types, categorical features (store, SKU), and scales.
- **Hierarchical** because forecasts must reconcile at product × store × region levels.

**Feature engineering:**

```python
features = [
    # Lag features
    'sales_lag_1', 'sales_lag_7', 'sales_lag_14', 'sales_lag_28', 'sales_lag_365',
    # Rolling
    'sales_rmean_7', 'sales_rmean_28', 'sales_rstd_28',
    # Calendar
    'day_of_week', 'month', 'is_holiday', 'days_to_holiday',
    # Categorical embeddings or target-encoded
    'store_id', 'sku_id', 'category',
    # Contextual
    'temp_forecast', 'promotion_active', 'price', 'competitor_price',
    # Hierarchical
    'category_mean_7', 'store_mean_7',
]
```

**Training:**

- Train on years 2022–2024, validate on 2025, test on 2026 H1.
- Use **TimeSeriesSplit** CV.
- Direct multi-horizon (separate model per horizon h=1, 7, 14, 28).
- Early stopping on validation MAPE.

**Not choosing:**

- **Per-SKU ARIMA:** 10M models = untractable. Short series = bad fits.
- **Prophet per series:** Same reason.
- **DeepAR / TFT:** Plausible alternative, but GPU cost and complexity outweigh benefit on tabular-heavy features.

**Hierarchical reconciliation:**

After forecasts, use MinT reconciliation to ensure store forecasts sum to region forecasts.

```python
# Using darts or hierarchicalforecast
from hierarchicalforecast.methods import MinTrace
reconciler = MinTrace(method='ols')
reconciled = reconciler.reconcile(forecasts, hierarchy)
```

---

## Q129. Scenario: build a churn prediction model for a SaaS company. { #q129 }

**Context:**

- B2B SaaS with 10K customers.
- Monthly billing cycle.
- Lots of usage data (logins, feature adoption, support tickets).
- Business wants to intervene before churn.

**Algorithm choice: LightGBM for prediction + SHAP for intervention playbooks.**

**Reasoning:**

- **Tabular, medium-sized** → GBDT.
- **Interpretability matters** — customer success team needs to know *why* the model says "at risk."
- **10K customers** is small for deep learning but ample for GBDT.

**Target definition (often the hardest part):**

- Churn = canceled within next 30 / 60 / 90 days?
- For monthly billing, typically predict "churn in next 30 days" refreshed weekly.

**Features:**

- **Usage trend:** Logins last 30d vs previous 30d.
- **Feature adoption:** Number of features used in last 30d.
- **Engagement velocity:** Declining logins? Rising support tickets?
- **Account health:** Payment delays, contract stage.
- **Demographics:** Company size, industry, contract value.
- **Health score inputs:** NPS if available.

**Label leakage trap:**

- "Customer logged into cancellation page" is a feature *after* they've decided — predicts too well, intervenes too late.
- Exclude features that only appear because the churn process has started.

**Imbalance handling:**

- Typical churn rate: 2–10% monthly. Use `scale_pos_weight` or tune threshold for business cost.
- Business asks: "How many customers can CS actually contact?" → pick top-k by predicted risk rather than a threshold.

**Evaluation:**

- **PR-AUC** (imbalance-aware).
- **Lift / gain chart:** If we contact top 20% riskiest, what fraction of churners do we catch?
- **A/B test** the intervention program — model accuracy alone isn't business success.

---

## Q130. Scenario: anomaly detection on sensor data from 10,000 machines. { #q130 }

**Context:**

- IoT sensors streaming at 1Hz.
- 10K devices, 20 metrics each.
- Goal: detect failing machines before they break.
- No labels (most failures unseen, heterogeneous).

**Algorithm choice: LSTM autoencoder per machine-type + statistical thresholds.**

**Reasoning:**

- **Unsupervised** because no labels.
- **Temporal structure** — failures manifest as pattern changes over minutes/hours, not point anomalies.
- **Autoencoder reconstruction error** as anomaly score. When the model fails to reconstruct, something's off.
- **LSTM** (or Transformer) captures temporal patterns.
- **Per machine-type** because machines of different types have very different patterns.

**Alternative pipeline:**

1. **Per-sensor statistical:** Z-score on rolling windows → catches sudden spikes.
2. **Multivariate Gaussian fit:** Detects correlated anomalies.
3. **LSTM autoencoder:** Learns normal temporal patterns, flags reconstruction error.
4. **Aggregate:** If ≥ 2 of the 3 systems flag, alert.

**Why not pure Isolation Forest?**

- Doesn't leverage temporal structure (treats each timestamp independently).
- Useful as one signal in the ensemble, not the whole system.

**Why not supervised?**

- Failures are rare and diverse. Labeled examples of past failures don't generalize to new failure modes.
- Anomaly detection is the right framing when "weird" is more predictable than "failure mode X."

**Production considerations:**

- **Streaming architecture:** Kafka → Flink / Spark Streaming → model inference → alert system.
- **Alert fatigue:** Threshold calibration crucial; too many false alerts → ignored.
- **Feedback loop:** Operators label alerts ("real failure," "false alarm"). Use these to refine thresholds over time.
- **Cold start:** New machine type = no baseline → use related type's model, refine as data accumulates.

---

## Q131. Scenario: classify customer reviews into 20 product categories. { #q131 }

**Context:**

- Input: review text (1–500 words).
- Output: one of 20 categories.
- 50K labeled examples.
- Balanced enough classes.
- Inference latency relaxed (batch).

**Algorithm progression (simple to complex):**

**Baseline: Logistic Regression + TF-IDF.**

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=50000, ngram_range=(1, 2))),
    ('clf', LogisticRegression(C=1.0, multi_class='multinomial', max_iter=500))
]).fit(X_text, y)
```

Expected accuracy: 80–85%. Strong baseline.

**Better: LightGBM on TF-IDF.** Usually 1–2% worse than logistic for text — text is high-dim sparse, linear models love this. Skip.

**Better: Pre-trained transformer (DistilBERT, RoBERTa).**

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import Trainer, TrainingArguments

model = AutoModelForSequenceClassification.from_pretrained(
    'distilbert-base-uncased', num_labels=20
)
# Fine-tune with HuggingFace Trainer
```

Expected accuracy: 88–94%.

**Best (when labels are rich): Fine-tuned larger model (RoBERTa-large, DeBERTa).**

Expected: 90–95%.

**Decision:**

- If baseline accuracy is enough → logistic regression. Done in 10 minutes.
- If max accuracy matters and you have GPU → DistilBERT.
- If state of the art is the bar → DeBERTa or a specialized LLM.

**LLM-based classification:**

For 20 classes with few-shot examples, a zero-shot or few-shot API call to GPT-4 / Claude can hit 85–90% without any training. Cost-performance tradeoff depends on volume.

<div class="tip-box" markdown>
**Interviewer signal:** Senior candidates start with the simplest baseline and only move up the complexity ladder when the business need justifies it. Junior candidates pick the fanciest-sounding model.
</div>

---

## Q132. Scenario: predict house prices from 50 features. { #q132 }

**Context:**

- Regression.
- 10K houses, 50 features (mixed continuous, categorical).
- Need interpretability for realtors.
- Accuracy is important but ~5% MAPE is fine.

**Algorithm choice: LightGBM + SHAP.**

**Reasoning:**

- **Tabular with mixed types** → GBDT.
- **Small dataset (10K):** Use cross-validation and tune carefully.
- **Interpretability:** SHAP values explain each prediction.

**Runner-up: Regularized linear regression (if monotonicity matters).**

- If realtors need "doubling square footage doubles price" intuition, constrained monotonic GBDT or plain linear regression with log-transformed price is cleaner.

**Feature engineering:**

- Log-transform price (residuals are closer to normal).
- Interactions: `bedrooms × bathrooms`, `sqft × neighborhood`.
- Geographic features: distance to downtown, school district.
- Temporal: months since last sale in neighborhood.

**Evaluation:**

- MAE and MAPE (real-estate standard).
- Check residuals: are high-end homes systematically under-predicted? (Common failure.)
- Split by region: does the model work equally in different markets?

**Avoiding pitfalls:**

- **Target leakage:** "tax_assessed_value" is basically the price. Drop it.
- **Temporal leakage:** Train on 2022, test on 2026? Market shifted. Use recent data.
- **Outliers:** Mansions and teardowns both exist. Consider winsorizing or robust loss.

---

## Q133. Scenario: segment users for a marketing campaign. { #q133 }

**Context:**

- 500K users with 20 behavioral features (RFM, engagement, demographics).
- Need 4–6 interpretable segments for marketing.
- No labels.

**Algorithm choice: K-means with K = 5, after standardization.**

**Reasoning:**

- **Small number of desired segments** (business can't operate 20 campaigns).
- **K-means is interpretable:** centroid features describe each segment.
- **Stable:** Same clusters run-to-run with fixed seed.

**Pipeline:**

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('kmeans', KMeans(n_clusters=5, n_init=20, random_state=42))
])
labels = pipe.fit_predict(features)
```

**Then interpret:**

- Compute centroid feature values.
- Give each segment a name: "Champions," "At-Risk," "New Users," "Hibernating," "Low-Value."
- Visualize with 2D UMAP for stakeholder presentations.

**Not choosing:**

- **HDBSCAN:** Produces variable-size clusters and noise. Marketing needs clean, assignable segments.
- **GMM:** Soft assignments are conceptually appealing but marketing needs hard assignment ("which campaign?").
- **Hierarchical:** Works but overkill; K-means gives the same quality here.

**Iterate:**

- Show stakeholders. Often they'll say "we need a premium vs mass-market split." → re-run with that feature weighted.
- Watch for segments that are too small to target (< 1% = not actionable).
- Re-cluster quarterly to capture evolving behavior.

---

## Q134. Scenario: rank search results for an e-commerce site. { #q134 }

**Context:**

- User enters query → 10K candidate products match.
- Need to rank top 20.
- Training data: click logs (query, product, clicked/not).
- Latency: < 100ms.

**Algorithm choice: Two-stage pipeline.**

**Stage 1 — Retrieval:**

- **BM25** (classical lexical matching) for keyword overlap.
- **Embedding-based retrieval** (sentence transformer on product + query, FAISS for ANN) for semantic.
- Union top-1000 from both.

**Stage 2 — Ranking:**

- **LightGBM with LambdaRank loss** (pairwise / listwise).
- Features:
  - Query × product: BM25 score, cosine sim, exact token match count.
  - Product: historical CTR, price, rating, recency.
  - Query: query length, has brand, has category.
  - User: past purchase categories (personalization).

```python
import lightgbm as lgb

params = {
    'objective': 'lambdarank',
    'metric': 'ndcg',
    'ndcg_eval_at': [5, 10, 20],
}

train_set = lgb.Dataset(
    X_train, label=y_train,
    group=group_sizes  # num candidates per query
)

ranker = lgb.train(params, train_set, num_boost_round=500)
```

**Reasoning:**

- **Retrieval stage** needed to cut 10K → 1K at speed.
- **LightGBM with LambdaRank** specifically optimizes NDCG — ranks matter, not predictions.
- **Fast inference:** Tree models predict ranking features in microseconds.

**Not choosing:**

- **Pure deep ranker:** Higher accuracy ceiling, but latency risk and complexity. Consider for Stage 2b (re-rank top 50).
- **Pure BM25:** No personalization. Misses semantic matches (query "jacket" → product "windbreaker").

**Position bias handling:**

- Train with IPS-weighted samples (Q124) to de-bias from historical position effects.
- Or use click models (DBN, UBM) to estimate unbiased relevance.

---

## Q135. Master cheat sheet: algorithm picks at a glance. { #q135 }

**First-choice algorithms by scenario:**

| Scenario | First pick | Why |
|---|---|---|
| Tabular binary classification | LightGBM | Fast, accurate, handles mixed types |
| Tabular regression | LightGBM | Same |
| Imbalanced tabular (fraud, churn) | LightGBM + class_weight/focal | Handles imbalance with tuning |
| Text classification, medium data | Logistic regression + TF-IDF | Strong baseline in minutes |
| Text classification, need SOTA | DistilBERT / RoBERTa fine-tune | Pretrained wins |
| Image classification | Pretrained CNN/ViT fine-tune | Rarely train from scratch |
| Regression with extrapolation | Linear/ridge + engineered features | Trees can't extrapolate |
| Recommender, millions of items | Two-tower + LightGBM ranker | Scalable + precise |
| Recommender, < 1M items, starting out | ALS matrix factorization | Strong baseline |
| Time series, single series, seasonal | ETS / SARIMA / Prophet | Classical shines |
| Time series, many related series | Global LightGBM or DeepAR | Shared learning |
| Clustering, interpretable segments | K-means | Simple, hard assignments |
| Clustering, unknown K, noise | HDBSCAN | Density-based |
| Anomaly detection, tabular | Isolation Forest | Fast, no assumption |
| Anomaly detection, images/time-series | Autoencoder reconstruction | Learns normal patterns |
| Dimensionality reduction for viz | UMAP | Fast, preserves structure |
| Dimensionality reduction for ML | PCA | Linear, preserves variance |
| Very high-dim sparse (text) | LinearSVC / Logistic | Scales well |
| Need interpretability (legal) | Monotonic GBDT or linear | Explainable |
| Tiny data (< 500) | Ridge / Logistic | Regularize aggressively |
| Huge data (> 100M rows) | Linear SGD / distributed GBDT | Scales |

**Second-choice when the first disappoints:**

- LightGBM not working → try XGBoost (different regularization), or CatBoost (categorical handling).
- GBDT overfitting → more regularization, fewer features, more data, or simpler linear baseline.
- Linear underfitting → add polynomial features, interactions, or switch to GBDT.
- Deep model not converging → simpler architecture, more data, check data quality, try pretrained.

**Final wisdom:**

1. **Always start with a baseline** (mean predictor, logistic regression, random forest).
2. **Complexity is a cost**, not a feature. Every level up brings maintenance burden.
3. **Data quality beats algorithm sophistication** 90% of the time.
4. **The "right" algorithm is the one your team can deploy, monitor, and improve.**

<div class="tip-box" markdown>
**The senior mindset:** A good ML engineer's instinct on seeing a new problem is to ask "what's the simplest thing that could work?" not "what's the most advanced model?". Reach for the shelf in this order: baseline → linear/tree → tuned GBDT → neural net → SOTA. Stop the first time accuracy meets the business need.
</div>
