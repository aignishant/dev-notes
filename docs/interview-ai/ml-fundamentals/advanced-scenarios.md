# 6. Advanced & Scenarios

> **Module goal:** This is where interviews separate candidates. Every question is a mini-scenario drawn from real production issues. Learn the patterns, not the punchlines.

---

## Q91. Concept drift vs Data drift vs Label drift { #q91 }

| Type | What changes | Example | Detection |
|---|---|---|---|
| **Covariate shift / data drift** | P(X) changes | Age distribution of users shifts older | Compare train vs prod distributions (KS test, PSI) |
| **Concept drift** | P(y \| X) changes | What makes a good loan applicant changes post-recession | Monitor model performance over time |
| **Label drift / prior shift** | P(y) changes | Fraud rate rises during holidays | Compare class frequencies over time |

**Mitigation:**
- **Monitor** feature distributions (PSI, KL divergence).
- **Retrain** periodically — daily, weekly, on-trigger.
- **Domain adaptation** — reweight or adapt the model.
- **Online learning** — update incrementally.
- **Champion-challenger** — shadow-deploy candidate models.

```python
# Population Stability Index (PSI) — drift detection
def psi(expected, actual, buckets=10):
    breaks = np.percentile(expected, np.linspace(0, 100, buckets+1))
    exp_freq, _ = np.histogram(expected, breaks)
    act_freq, _ = np.histogram(actual, breaks)
    exp_freq = exp_freq / exp_freq.sum() + 1e-6
    act_freq = act_freq / act_freq.sum() + 1e-6
    return ((act_freq - exp_freq) * np.log(act_freq / exp_freq)).sum()

# PSI < 0.1: no drift. 0.1–0.25: moderate. > 0.25: significant drift.
```

---

## Q92. Model interpretability — SHAP, LIME, permutation importance { #q92 }

| Method | How | Scope |
|---|---|---|
| **SHAP** | Shapley values from game theory | Global + per-prediction, model-agnostic |
| **LIME** | Fit local linear model around a prediction | Per-prediction, model-agnostic |
| **Permutation importance** | Shuffle each feature, measure perf drop | Global, model-agnostic |
| **Partial dependence plots** | Vary one feature, average over others | Global marginal effect |
| **Tree feature importance** | Built-in sklearn attribute | Global, fast but biased |
| **Integrated gradients** | Path integral of gradients | Per-prediction, neural nets |
| **Attention weights** | Softmax weights from transformer | Per-prediction, transformers — interpret with care |

**SHAP is the modern default:**

```python
import shap

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_val)

shap.summary_plot(shap_values, X_val)    # global importance
shap.force_plot(explainer.expected_value, shap_values[0], X_val.iloc[0])  # local explain
```

**SHAP's theoretical appeal:** uniquely satisfies four fairness axioms (efficiency, symmetry, dummy, additivity). Attributions sum to the model output — no leftover.

<div class="tip-box" markdown>
In regulated domains (credit, healthcare), interpretability isn't optional — it's mandatory. Know SHAP well. Know the fact that attention weights are not reliable explanations (Jain & Wallace 2019).
</div>

---

## Q93. SHAP in depth — what it gives you { #q93 }

**SHAP (SHapley Additive exPlanations)** attributes each prediction to input features using Shapley values from cooperative game theory.

$$
\phi_i = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|!(|F|-|S|-1)!}{|F|!} [f(S \cup \{i\}) - f(S)]
$$

Average marginal contribution of feature i across all orderings.

**Output properties:**

- **Local accuracy:** `∑ φ_i + E[f(X)] = f(x)`
- **Missingness:** missing feature → zero SHAP.
- **Consistency:** if a model gives feature more impact, its SHAP increases.

**Variants:**
- **TreeSHAP** — exact, fast for trees.
- **KernelSHAP** — model-agnostic, slow.
- **DeepSHAP** — approximation for neural nets.
- **LinearSHAP** — closed-form for linear models.

---

## Q94. Handling extreme class imbalance — fraud 0.1% scenario { #q94 }

<div class="scenario" markdown>
**You're building fraud detection. Positive rate = 0.1%. Accuracy isn't useful. What's your approach end-to-end?**

**Answer:**

1. **Metric** — PR-AUC + recall at fixed precision (business tells you "we can tolerate 5% false-positive rate on alerts").
2. **Sampling** — SMOTE or class weights; avoid random undersampling on a 0.1% class (wastes info). Alternatively, train on all positives + 10× random negatives for speed.
3. **Model** — start with gradient boosting (LightGBM with `is_unbalance=True` or `scale_pos_weight`). Calibrate.
4. **Threshold** — tune on validation to hit target precision-recall operating point.
5. **Feature engineering** — transaction frequency, deviations from user's baseline, velocity features (tx/hour), graph features (shared merchants/devices).
6. **Live** — shadow-deploy first, compare to rules. Human-in-the-loop for borderline.
7. **Feedback loop** — confirmed labels from manual review feed back into training.
8. **Drift** — fraud patterns evolve weekly; retrain often.
</div>

---

## Q95. Your model drops from 90% to 70% accuracy in production — debug { #q95 }

**Systematic debugging order:**

1. **Verify the metric drop is real.** Is your monitoring computing the same way as training? Label latency might skew metrics.
2. **Data pipeline check.** Are features being computed the same way in prod as in training? Schema drift? Encoding mismatches?
3. **Population drift (PSI/KS).** Compare feature distributions train vs prod. Identify which features shifted.
4. **Covariate vs concept drift.** Does retraining on recent data recover performance? If yes → data drift. If no → concept drift.
5. **Segment analysis.** Is the drop uniform, or concentrated in a subgroup? (e.g., new geography, new product line).
6. **Label quality.** Are production labels arriving correctly? Delayed labels can cause phantom drops.
7. **Deployment-time issues.** Check the actual model artifact matches the trained one; version mismatches are common.
8. **Feedback loop / selection bias.** The deployed model changes user behavior, which changes future data.

!!! tip "Ask for the freshness gap"
    If the last training data is from 6 months ago and production is today, that's your lead suspect. Data drift is the single most common cause.

---

## Q96. Multi-class vs multi-label classification { #q96 }

- **Multi-class** — each sample gets exactly one label out of N. (Spam vs promo vs social vs primary.)
- **Multi-label** — each sample can have multiple labels. (Tags on a blog post.)

**Implementation:**

- Multi-class → softmax, cross-entropy.
- Multi-label → sigmoid per class, binary cross-entropy per class (independent).

**One-vs-Rest (OvR)** and **One-vs-One (OvO)** are strategies to extend binary classifiers:
- OvR → N classifiers (each class vs rest). Imbalanced per-classifier but simple.
- OvO → N(N-1)/2 classifiers. Balanced per-classifier but expensive.

Sklearn's `MultiOutputClassifier` and `OneVsRestClassifier` handle these.

---

## Q97. Handling multi-class with extreme class count { #q97 }

When you have 10,000+ classes (product catalog, NER types, billion-scale softmax):

- **Hierarchical softmax** — tree over classes, O(log N).
- **Sampled softmax / negative sampling** — train against random subset of negatives per step. Word2Vec, embeddings at scale.
- **Extreme classification (XMC)** methods — Parabel, SLICE, AttentionXML.
- **Retrieval-then-rerank** — use an embedding model for candidate retrieval, classifier for final ranking.

---

## Q98. Handling non-stationary time series { #q98 }

<div class="scenario" markdown>
**Your time-series forecast worked well for 6 months then stopped. Why?**

**Answer:**
- **Trend change** — underlying growth pattern shifted (post-COVID demand change, for instance).
- **Seasonality shift** — holidays, business cycles changed.
- **Regime change** — structural break (new product launch, competitor entry).
- **Outliers driving new normal** — a sustained spike becomes the new baseline.

**Mitigation:**
- Use models that incorporate seasonality + trend (Prophet, ETS, SARIMA, Temporal Fusion Transformer).
- Detect change points (Bayesian online changepoint, PELT).
- Retrain frequently with a rolling window.
- Include exogenous variables (price, promotions, COVID dummy).
</div>

---

## Q99. Model monitoring in production — what to log { #q99 }

**Infrastructure metrics:** latency, throughput, error rate, memory.

**Input monitoring:**
- Feature distribution drift (PSI per feature, weekly).
- Missing-value rates.
- Out-of-range values (indicator of upstream bug).

**Output monitoring:**
- Prediction distribution drift.
- Score histograms — bimodal, smooth, concentrated?
- Prediction latency.

**Performance monitoring (when labels available):**
- Primary metric (AUC, F1, RMSE) vs training baseline.
- Segment-level performance.
- Calibration over time.

**Alerting:**
- PSI > 0.25 on any feature → alert.
- Primary metric drop > X% → alert.
- Null rate or OOR rate spike → alert.
- Any input schema change → block deployment.

---

## Q100. Reproducibility — making sure your run is the same tomorrow { #q100 }

**Common reproducibility killers:**
1. No random seed set.
2. Library version drift.
3. Hardware differences (different GPU → floating-point non-determinism).
4. Non-deterministic operations (CUDA's atomic adds).
5. Data pipeline randomness (multi-worker data loader order).

**Practices:**

```python
import random, numpy as np, torch

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
```

- Pin library versions (`requirements.txt` with ==).
- Use a containerized environment (Docker).
- Version data, not just code (DVC, LakeFS, Delta).
- Log hyperparameters, model, git SHA, data version into MLflow/W&B.

---

## Q101. Handling new/unseen categories in production { #q101 }

Your model was trained on cities {NYC, SF, LA, ...}. A user in Boise shows up. What happens?

**Depends on encoding:**

- **One-hot** — Boise = all zeros. Might behave OK but isn't great.
- **Label encoding** — error, KeyError.
- **Target encoding** — needs default (global mean).
- **Embeddings** — need an `<UNK>` token reserved during training.
- **Hashing** — Boise hashes deterministically to some bucket.
- **Tree with native categorical** (LightGBM/CatBoost) — treats unseen as NaN or assigns to default branch.

**Best practice:** reserve an `<UNK>` / `other` bucket during training. Randomly label 0.5% of training-set cities as `<UNK>` so the model learns to handle it gracefully.

---

## Q102. Shadow deployment, canary, champion-challenger, A/B — know the difference { #q102 }

| Strategy | What it does | When |
|---|---|---|
| **Shadow** | New model runs in parallel; predictions logged, not served | Before any user impact; pre-launch validation |
| **Canary** | Route small % of traffic to new model | Confidence-building before full rollout |
| **Champion-Challenger** | Multiple models; track metrics; auto-promote best | Continuous improvement |
| **A/B test** | Random split, statistical comparison | Measure causal effect on business metric |
| **Blue-Green** | Two full environments; atomic switchover | Instant rollback capability |
| **Multi-armed bandit** | Dynamically route more traffic to winning variant | Lower regret than A/B at cost of cleaner stats |

---

## Q103. Handling label noise { #q103 }

Labels are rarely perfect — medical labels have inter-annotator disagreement, web-crawled text has wrong tags, user "likes" are noisy.

**Techniques:**

1. **Confident learning** (`cleanlab`) — identify mislabeled samples via confidence estimation.
2. **Symmetric / asymmetric noise-robust losses** — generalized cross-entropy, normalized cross-entropy, forward correction.
3. **Label smoothing** — mild robustness.
4. **Co-teaching** — two networks teach each other, each avoids samples the other is confident are wrong.
5. **Bootstrapping / soft labels** — the model's own high-confidence predictions become training targets.
6. **Active label correction** — flag low-confidence / high-disagreement samples for re-annotation.

```python
import cleanlab

issues = cleanlab.filter.find_label_issues(
    labels=y_train,
    pred_probs=model.predict_proba(X_train)
)
X_clean, y_clean = X_train[~issues], y_train[~issues]
```

---

## Q104. When training data is expensive — active learning { #q104 }

**Active learning** = the model picks which samples to label next to maximize learning efficiency.

**Strategies:**

1. **Uncertainty sampling** — label the samples where the model is least confident (highest entropy, smallest margin between top two classes).
2. **Query-by-committee** — label samples where an ensemble disagrees most.
3. **Expected model change** — label samples whose labels would most change the model.
4. **Diversity sampling** — label in regions of feature space you haven't labeled yet.
5. **Core-set selection** — label a diverse subset that best covers the data distribution.

Typical workflow: label 1% → train → query 1% most uncertain → label → retrain. Can reach full-supervision performance at 20% label cost.

---

## Q105. Transfer learning & fine-tuning — the modern default { #q105 }

**Transfer learning** — take a model trained on a large source task and adapt to a smaller target task.

**Why it works:** low-level features (edges in images, syntax in text) generalize; high-level features become task-specific.

**Fine-tuning strategies:**

1. **Feature extraction** — freeze backbone, train only the final head. Fastest, least data needed.
2. **Full fine-tuning** — unfreeze everything, small LR. Best performance, needs more data.
3. **Layer-wise discriminative LR** — earlier layers → tiny LR, later → higher LR.
4. **LoRA / adapters** — train small additional modules, keep base frozen. Standard for LLMs.

**When to not transfer:** if source and target domains are very different (medical X-rays vs ImageNet), transfer may hurt.

---

**Module complete.** Next → [7. Production & Debugging →](production-debugging.md)
