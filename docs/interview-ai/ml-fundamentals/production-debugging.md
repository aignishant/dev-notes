# 7. Production & Debugging

> **Module goal:** These are the questions interviewers save for the end to see if you've actually shipped ML. The candidates who handle them well get senior offers.

---

## Q106. Your model has 95% offline accuracy but users complain it's "dumb" — diagnose { #q106 }

<div class="scenario" markdown>
**Offline accuracy 95%. Users file bugs saying "recommendations are wrong." What's happening?**

**Answer — walk through these hypotheses:**

1. **Offline ≠ online distribution.** The offline test set was historical; users today behave differently.

2. **Offline metric doesn't reflect user satisfaction.** You optimized accuracy; users care about relevance, diversity, freshness.

3. **Feedback loop.** Your model recommends a narrow set → users engage → training data becomes even narrower → model narrows further. "Filter bubble" failure mode.

4. **Edge cases matter more than average.** 95% average accuracy means 5% of users have a bad experience — and those 5% are the vocal ones.

5. **Popularity bias.** Model recommends popular items to everyone. Metric high, user satisfaction low for niche users.

6. **Cold-start.** New users/items get worse predictions; aggregate metric masks it.

7. **Calibration.** If 90% confident predictions are right only 60% of the time, downstream ranking/display decisions suffer.

**Fixes:**
- A/B test user-centered metrics (engagement, time-on-site, diversity).
- Segment performance by user cohort (new, niche, power users).
- Explicit diversity/serendipity objectives in ranker.
- Human eval sampling — have real people rate 100 recommendations weekly.
</div>

---

## Q107. Root-cause checklist: model "mysteriously" got worse overnight { #q107 }

1. **Did anything deploy?** New model? New feature pipeline? Dependency update?
2. **Did the data source change?** Upstream vendor schema changed, columns reordered, units changed (cents vs dollars).
3. **Did a data pipeline fail silently?** Null rate spike, column-all-same-value, partial backfill.
4. **Time-based:** Daylight saving, year rollover, leap day, fiscal-year reset, holiday.
5. **External event:** News event, viral trend, platform outage upstream.
6. **Label quality:** Are you computing the target label the same way?
7. **Measurement error:** The metric itself is buggy — maybe it was always worse, you just started measuring.
8. **Small sample noise:** A single day's metric can fluctuate 5% just by chance with small volume.

```python
# Quick sanity diagnostics
df_today = load_prod_features(date='today')
df_yesterday = load_prod_features(date='yesterday')

for col in df_today.columns:
    psi_val = psi(df_yesterday[col], df_today[col])
    if psi_val > 0.1:
        print(f"DRIFT: {col} PSI={psi_val:.3f}")
```

---

## Q108. Latency vs accuracy — the deployment tradeoff { #q108 }

**Scenarios:**

- **Real-time ad ranking:** < 50ms p99. Accuracy matters but can't block render.
- **Fraud scoring at checkout:** < 200ms. Critical path; trade model size for speed.
- **Batch recommendation:** 6-hour batch OK. Use biggest model you can.
- **Search typeahead:** < 100ms. Often pre-compute + cache.

**Speed levers (roughly in order of free → costly):**

1. **Caching** — memoize common inputs.
2. **Quantization** — FP32 → FP16/INT8, often 2–4× speedup, <1% accuracy drop.
3. **Distillation** — train a smaller "student" to mimic a bigger "teacher."
4. **Pruning** — zero-out weights below a threshold.
5. **Hardware** — GPU / TPU / accelerators.
6. **Architecture swap** — transformer → smaller transformer / MLP-mixer / linear model.
7. **Two-stage: retrieve-then-rerank** — fast lightweight filter, expensive ranker on top-k.
8. **Feature reduction** — expensive features only for top candidates.

---

## Q109. Serving architectures — offline batch vs online real-time vs near-real-time { #q109 }

| Mode | Characteristics | Tools |
|---|---|---|
| **Batch** | Run daily/hourly, write to warehouse or k-v store | Airflow + Spark + Snowflake/BigQuery |
| **Near-real-time** | Minute-level updates via stream | Kafka + Flink + Redis |
| **Online** | Request-response, p99 latency SLA | BentoML, TorchServe, TF-Serving, Triton, SageMaker endpoints |
| **Edge** | On-device (mobile, browser) | ONNX Runtime, Core ML, TFLite |

**Feature stores** bridge online and offline: ensure train-serve consistency.

**Key serving concerns:**
- Train-serve skew (preprocessing differences).
- Feature freshness (real-time vs batch).
- Model versioning (A/B ready).
- Rollback capability (fast revert on regression).

---

## Q110. Training-serving skew — what causes it, how to prevent { #q110 }

**Training-serving skew** = the model sees different features at train time than at inference.

**Common causes:**

1. **Different code paths** — training preprocesses in pandas, production uses Java/Go. Differences in how `NaN`, timezone, string case handled.
2. **Time-of-feature mismatch** — training uses a feature computed "as of the event time"; production uses "current value," which is different because time has passed.
3. **Late-arriving data** — some features in training had fully-settled downstream values; production has only partial.
4. **Feature versioning** — a business rule changed; training data reflects old rule, production uses new.

**Prevention:**

- **Feature store** (Feast, Tecton, Vertex Feature Store) — single source of truth for both training and serving.
- **Shared preprocessing code** — one Python package, imported by both train and serve.
- **Point-in-time correctness** — when assembling training data, use only features available at the prediction time.
- **Shadow mode** — before cutover, compare train and serve outputs on same inputs; they must match.

---

## Q111. When *not* to use ML { #q111 }

**Don't use ML when:**

- **Rules work better.** 10-rule expert system often beats a fancy model on simple domains.
- **Ground truth doesn't exist.** If you can't define "right," you can't supervise.
- **Cost of error is catastrophic and unbounded.** Safety-critical without fallback.
- **You don't have enough data.** < 1K samples for complex problems — use heuristics or collect more data first.
- **The problem is deterministic.** Route optimization → OR, not ML.
- **Regulation prohibits black-box.** Sometimes a linear scorecard is all you can ship.
- **You need perfect reproducibility for legal.** Rules beat models.

**Interview signal:** "I'd start with a heuristic baseline and only move to ML if it measurably beats it." This shows maturity.

---

## Q112. Cost of model ownership — what interviewers want to hear { #q112 }

Beyond accuracy, a production model has:

1. **Training cost** — GPU hours, data pipeline runs, labeling cost.
2. **Inference cost** — per-request compute; at 100M requests/day, 1ms more means $$.
3. **Monitoring cost** — infrastructure + engineer time watching dashboards.
4. **Retraining cost** — each cycle needs pipelines to rerun.
5. **Debugging cost** — complex models are slower to diagnose.
6. **Opportunity cost** — engineer time spent iterating.
7. **Ethical/legal cost** — bias audits, documentation, compliance.

**The business frame:** "Does this model's value exceed its total cost of ownership?" If incremental accuracy gains a model 0.5% but doubles latency, the answer may be no.

---

## Q113. Your manager says "can we make it 10% more accurate?" — how to respond { #q113 }

**Don't say yes or no immediately.** Run the decomposition:

1. **Current state.** What's the baseline error? On what metric? On which segments?
2. **Ceiling analysis.** If your model were perfect on *one* stage of the pipeline, how much would overall metric improve? Points you to the right lever.
3. **Data ceiling.** Is label noise limiting you? If labels disagree 5% of the time, you can't get above 95%.
4. **Feature ceiling.** Are there features you don't yet have that would help? (user history, device info, signal x)
5. **Model ceiling.** Learning curve suggests more capacity would help or not.
6. **Budget.** What's the cost of +10%? A week of tuning is cheap. Six months of data collection is not.
7. **Business.** Does 10% more accuracy translate to anything the business can measure?

**The senior-engineer response:** "Let me do a ceiling analysis this week and come back with three tractable paths and their expected ROI." You've turned a demand into a plan.

---

## Q114. The single most common production ML bug { #q114 }

**Train-serve skew via string handling.** Example:

- Training: `city.lower().strip()`.
- Serving: `city` (no normalization).
- Result: "NYC" in training is a common category; " NYC" or "nyc" in production is unseen.

**Generalization:** every preprocessing step applied in notebook but not in the serving code causes a silent accuracy drop. This is why feature stores and shared preprocessing packages matter.

---

## Q115. The "90-10 rule" every senior ML engineer knows { #q115 }

> **90% of the value comes from 10% of the work — and that 10% is almost always data work, not modeling.**

Cleaner labels, better features, fixed leakage, correct splits — these beat "XGBoost vs CatBoost" agonizing. Engineers who obsess over hyperparameters while their labels are 15% wrong are running on a treadmill.

**Interview-ready phrasing:** "I'd spend the first two days on data understanding and leakage audits — then use the simplest model that works, tuned lightly. That's where the 90% of my returns come from."

---

**Module complete.** Next → [🎯 Mock Interviews →](mock-interview.md)
