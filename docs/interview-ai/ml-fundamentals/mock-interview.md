# Mock Interview Rounds

Three full simulated interview rounds — **Screening**, **Technical Deep Dive**, and **System Design + Case Study** — each with timing, rubrics, and model answers. Run them timed, record yourself, and compare against the rubric.

!!! tip "How to use this section"
    1. Set a timer. Don't look at answers until you've attempted each question.
    2. Speak out loud — interviews are verbal. Writing gives you time to think that you won't have.
    3. After each round, score yourself against the rubric. Anything below 3/5 → revisit the relevant module.

---

## Round 1 — Phone Screen (30 min) { #round-1 }

**Format:** 5 rapid-fire conceptual questions + 1 mini scenario. Tests breadth and communication clarity.

### Q1. Explain bias-variance tradeoff to a non-technical stakeholder. (4 min) { #r1-q1 }

**What the interviewer is checking:**

- Can you translate jargon into intuition?
- Do you know *why* it matters, not just the formula?

**Model answer structure:**

> "Imagine we're training a dartboard-throwing robot. **High bias** means the robot is systematically off — always throws to the left. No matter how many darts it throws, it won't hit the bullseye because its aim is wrong. That's *underfitting*: the model is too simple to capture reality.
>
> **High variance** means the robot is inconsistent — the darts scatter all over. On average it hits the center, but any individual throw is unpredictable. That's *overfitting*: the model memorized training examples but can't generalize to new ones.
>
> The tradeoff: making the robot more flexible (complex model) reduces bias but increases variance. Making it more rigid does the opposite. Our job is to find the sweet spot — usually via regularization and cross-validation."

<div class="tip-box" markdown>
**Interviewer tip:** If they ask "how do you find that sweet spot?" — mention *learning curves* and *validation loss*. Bonus points for noting that *more data* shifts the tradeoff favorably.
</div>

---

### Q2. Difference between bagging and boosting — when would you use each? (4 min) { #r1-q2 }

**Model answer:**

> "**Bagging** trains many models independently on bootstrap samples and averages them. It reduces *variance* — great when your base learner overfits. Random Forest is the canonical example.
>
> **Boosting** trains models sequentially, each correcting the previous model's errors. It reduces *bias* — great when your base learner underfits. XGBoost and LightGBM are the canonical examples.
>
> **When to use:**
>
> - **Tabular data, strong signal, you want top leaderboard accuracy** → boosting (LightGBM).
> - **Noisy labels, you want robustness** → bagging (Random Forest).
> - **Parallel training infrastructure matters** → bagging (embarrassingly parallel).
> - **Latency-sensitive with shallow trees** → boosting with early stopping.
>
> In practice, I start with LightGBM on tabular problems — it's won most Kaggle competitions since 2017, handles missing values natively, and trains fast."

---

### Q3. You have 10M rows and 500 features. How do you approach feature selection? (5 min) { #r1-q3 }

**Model answer:**

> "Three-stage funnel:
>
> **Stage 1 — Cheap filters (get to ~200 features):**
>
> - Drop features with >95% missing or zero variance.
> - Drop duplicates and near-duplicates (correlation > 0.95, keep one).
> - Drop features with <1% non-null in the target class (for imbalanced problems).
>
> **Stage 2 — Model-based importance (get to ~50):**
>
> - Fit a LightGBM on a sample (500K rows).
> - Keep features with gain > threshold.
> - Validate with permutation importance on held-out — built-in importance can mislead with correlated features.
>
> **Stage 3 — Business sanity check:**
>
> - Talk to domain experts. If a top feature doesn't make business sense, it's likely a leak.
> - Check feature stability over time — a feature that's predictive in Jan but not June will break in production.
>
> I avoid exhaustive methods like RFE with 500 features — cost is O(n²) retrainings."

---

### Q4. Your model has 99% accuracy. Are you happy? (3 min) { #r1-q4 }

**Model answer:**

> "No, 99% accuracy is a red flag. Three checks:
>
> 1. **Class balance.** If positive class is 1%, predicting 'always negative' gives 99%. I'd look at precision, recall, PR-AUC — not accuracy.
> 2. **Data leakage.** 99% is suspiciously high for most real problems. I'd check: is the target feature accidentally in the features? Am I using future info? Did I leak across train/test (e.g., same user in both)?
> 3. **Train-test similarity.** Maybe test is just too easy — same distribution, no temporal split. I'd evaluate on a genuinely held-out slice (next month's data, new geography)."

<div class="tip-box" markdown>
**Interviewer tip:** The strongest candidates say "I'd be suspicious" *before* proving it — it shows you've been burned before.
</div>

---

### Q5. What's the difference between L1 and L2 regularization? (4 min) { #r1-q5 }

**Model answer:**

> "Both penalize large weights, but with different geometry.
>
> - **L1 (Lasso)** adds `|w|` to the loss. The penalty has sharp corners at zero, so optimal solutions often land exactly on the corners → some weights become *exactly zero*. It performs implicit feature selection.
> - **L2 (Ridge)** adds `w²`. The penalty is smooth, so weights shrink toward zero but rarely *become* zero. It handles multicollinearity well by spreading weight across correlated features.
>
> **Use L1 when:** you want a sparse, interpretable model with built-in feature selection.
> **Use L2 when:** all features are potentially useful and you want stability under collinearity.
> **Use ElasticNet (both):** when you have grouped correlated features and want some sparsity without dropping whole groups."

---

### Mini Scenario (10 min)

> "You deployed a loan-default model 3 months ago. This week, the approval team says false rejections are up 20%. Walk me through your investigation."

**Model answer framework:**

> "I'd approach this in three layers — data, model, downstream.
>
> **1. Data layer (15 min):**
>
> - Pull input feature distributions for the last week vs training. Compute PSI or KS per feature. Anything drifted?
> - Check for pipeline bugs — did a feature transform change? Did a source system update a schema?
> - Check the label pipeline — is 'default' being labeled the same way? Sometimes ops changes the definition upstream.
>
> **2. Model layer (30 min):**
>
> - Score slice: is the issue concentrated in a segment (e.g., new geography, new product)?
> - Calibration drift: are predicted probabilities still aligned with actual default rates in the recent window?
> - Threshold drift: did someone change the decision threshold downstream?
>
> **3. Downstream layer:**
>
> - Is 'rejection' defined the same way? Maybe the business added a new rule on top of the model.
> - Talk to the approval team — sometimes 'rejections up' is a *feeling* from anecdotes, not data.
>
> My first action: compare the distribution of approved/rejected this week vs baseline. If model scores are unchanged but rejection rate shifted → it's downstream, not the model. If scores shifted → drill into which features drove it."

### Round 1 Rubric

| Criterion | 1 (Weak) | 3 (Solid) | 5 (Exceptional) |
|---|---|---|---|
| **Clarity** | Jargon-heavy, rambling | Clear structure | Analogies + crisp framing |
| **Depth** | Textbook-level | Shows real experience | Mentions edge cases unprompted |
| **Communication** | Monotone, one-way | Checks understanding | Anticipates follow-ups |
| **Trade-off reasoning** | Picks one answer | Mentions alternatives | Explains *when* each applies |
| **Production awareness** | Pure theory | Aware of prod concerns | Cites specific incidents/patterns |

**Pass bar:** ≥ 3 on every criterion.

---

## Round 2 — Technical Deep Dive (60 min) { #round-2 }

**Format:** One core topic probed in depth, with the interviewer following your answer wherever it goes. Tests breadth *and* depth.

### Scenario:

> "Walk me through how you'd train a model to predict whether a credit-card transaction is fraudulent. Assume 500M transactions/year, fraud rate 0.2%."

**Phase 1 — Problem framing (10 min):**

Expected to discuss:

- **Business metric:** What's the cost of FP (friction, lost revenue) vs FN (chargeback)? A typical ratio is 1:50 — one missed fraud costs as much as 50 false alarms.
- **Time horizon:** Real-time (<100ms) or batch? Affects model choice.
- **Labels:** Ground truth fraud comes from chargebacks — arrives 60–120 days late. How do we handle label delay?
- **Decision vs score:** Model outputs a risk score; a separate rules engine makes the block/allow call.

**Phase 2 — Data (10 min):**

- **Features:** transaction amount, merchant category, device fingerprint, velocity features (count per hour/day), geo-distance from last transaction, cardholder history aggregates.
- **Leakage traps:** Don't use future transactions or chargeback-derived features.
- **Imbalance:** 0.2% positive — I would *not* SMOTE by default. Instead, use class weights in LightGBM (`scale_pos_weight`) and evaluate on PR-AUC.
- **Temporal split:** Train on months 1–9, validate month 10, test month 11. Never shuffle — fraud patterns evolve.

**Phase 3 — Model (15 min):**

- **Baseline:** Logistic regression on hand-crafted velocity features. Establishes floor.
- **Production candidate:** LightGBM — handles mixed-type features, missing values, fast inference (~1ms on CPU for 500-tree model).
- **Why not deep learning:** Tabular, moderate feature count → tree boosting wins. DL adds complexity without accuracy gain unless you have sequence/graph structure.
- **Threshold tuning:** Set threshold to meet business precision target (e.g., 95% precision → whatever recall that yields).

**Phase 4 — Deployment (15 min):**

- **Serving:** Feature store (Redis/Feast) for low-latency lookups. Model served via ONNX on CPU — sub-10ms p99.
- **Shadow mode:** Run new model alongside production for 2 weeks, compare decisions but don't act on new model.
- **Rollout:** Canary at 1% → 5% → 25% → 100% over a month, with automatic rollback if precision drops.
- **Monitoring:** PSI per feature, precision-at-threshold, decision distribution, latency p50/p99.

**Phase 5 — Edge cases (10 min):**

- **Cold start:** New cardholder has no history. Fallback: merchant-level and population-level priors.
- **Concept drift:** Fraud tactics evolve quickly. Retrain weekly on rolling 90-day window. Monitor for sudden drops.
- **Adversarial:** Fraudsters probe the system. Don't expose too much feedback (e.g., don't tell them *why* a transaction was declined).

<div class="tip-box" markdown>
**What the interviewer is probing at each phase:**

- Phase 1 → business sense
- Phase 2 → data rigor
- Phase 3 → model judgment (the right tool, not the shiny tool)
- Phase 4 → production maturity
- Phase 5 → experience scars
</div>

### Round 2 Rubric

| Phase | Weak (1) | Solid (3) | Exceptional (5) |
|---|---|---|---|
| **Framing** | Jumps to model | Clarifies metric | Proposes ratio from industry benchmarks |
| **Data** | Lists features | Discusses leakage | Describes label delay handling |
| **Model** | "I'd use a neural net" | Justifies tree boosting | Explains why DL *isn't* needed here |
| **Deployment** | Vague | Mentions monitoring | Specifies shadow → canary → rollout |
| **Edge cases** | None proactive | Mentions drift | Discusses adversarial + cold-start |

---

## Round 3 — Case Study + System Design (75 min) { #round-3 }

**Scenario:**

> "A ride-hailing company wants to predict ETA (estimated time of arrival) for each ride. Currently they use a simple Google Maps API estimate. Design an ML system that beats it. Assume 50M rides/day globally."

### Expected structure:

**1. Clarifying questions (5 min)**

- Is the ETA shown to riders, drivers, or both? (Affects error asymmetry — riders hate underestimates more than overestimates.)
- Is it a single-point estimate or a distribution? (A range gives better UX.)
- What's the current error of the Maps baseline? (Benchmark to beat.)
- What latency budget? (Shown at booking time → <200ms.)

**2. Metric design (10 min)**

- **Offline:** MAE in minutes (interpretable), split by ride length bucket (0–10 min, 10–30 min, 30+ min).
- **Asymmetric loss:** Quantile loss at τ=0.6 — penalizes underestimates more than overestimates.
- **Online:** rider satisfaction (survey), cancellation rate post-booking, driver arrival-time drift.

**3. Features (15 min)**

| Category | Features | Source |
|---|---|---|
| **Route** | Distance, # of turns, road types, traffic signals | Maps API |
| **Traffic** | Current speed per road segment, historical speed at this time-of-day | Real-time feed |
| **Temporal** | Hour, day-of-week, is-holiday, weather | External + calendar |
| **Driver** | Avg historical speed deviation, rating, vehicle type | Internal |
| **Pickup/drop** | Venue type (airport, stadium → slow pickup), entrance complexity | Derived |
| **Context** | Concurrent demand, event nearby | Derived |

**4. Model choice (15 min)**

Three candidates:

| Model | Pros | Cons | Verdict |
|---|---|---|---|
| LightGBM | Fast, strong tabular | Misses sequence structure | ✅ Production v1 |
| GNN over road graph | Captures spatial | Complex infra, hard to debug | v3 candidate |
| Transformer on GPS traces | Captures sequence | Expensive, latency risk | Research track |

> "I'd ship LightGBM first. It'll beat the Maps baseline by 10–15% within a quarter. GNN and transformer are v2/v3 only if LightGBM plateaus."

**5. System architecture (15 min)**

```
[Booking] → [Feature Service] → [Model Serving] → [Post-process]
               ↓                      ↓
           (Redis cache          (LightGBM via ONNX
            + real-time           on GPU for batch,
            traffic feed)         CPU for online)
```

Details:

- **Feature store:** Two-tier — Redis for hot lookups (driver, recent traffic), S3/Parquet for historical aggregates.
- **Online model:** LightGBM via ONNX Runtime, CPU inference, p99 < 50ms.
- **Batch model (optional):** Every 15 min, pre-score common O→D pairs, cache.
- **Fallback:** If model service fails, fall back to Maps ETA + historical error correction.

**6. Rollout + monitoring (10 min)**

- **Shadow mode** for 2 weeks in 1 city. Compare predicted vs actual.
- **A/B test** in 5 cities. Primary metric: MAE. Guardrail: cancellation rate.
- **Monitoring:** MAE sliding window, feature drift (PSI), latency, fallback rate.
- **Retraining:** Weekly, because traffic patterns shift (road work, seasonal).

**7. Edge cases (5 min)**

- New city → cold start. Bootstrap with population-wide model until enough data.
- Outliers → very long rides get high error. Clip training labels at p99 to prevent tail from dominating.
- Black swan → pandemic, weather event. Freeze model, switch to rules, retrain once stable.

### Round 3 Rubric

| Dimension | Weak (1) | Strong (5) |
|---|---|---|
| **Problem framing** | Dives into model | Clarifies metric, stakeholder, baseline |
| **Metric rigor** | "MAE" | Asymmetric loss + online metric + bucketing |
| **Feature engineering** | Lists obvious features | Categorizes + sourcing + leakage checks |
| **Model reasoning** | Picks trendy model | Ships boring, explains why fancy isn't needed yet |
| **System design** | Box diagram only | Feature store, fallback, latency budget |
| **Rollout strategy** | "Deploy it" | Shadow → canary → A/B with guardrails |
| **Edge-case awareness** | None | Cold start, outliers, black swan |

**Pass bar for senior roles:** ≥ 4 average.

---

## Post-interview self-review

After each mock, ask yourself:

1. **Did I ask clarifying questions?** Strong candidates spend 10–15% of time on framing.
2. **Did I propose a baseline first?** "Boring and shipped" beats "fancy and stuck."
3. **Did I quantify tradeoffs?** "10% better MAE at 2× latency" is stronger than "slower but more accurate."
4. **Did I cite production concerns unprompted?** Monitoring, rollback, cost of ownership.
5. **Did I admit uncertainty?** "I'd validate this with an experiment" is a strength, not weakness.

<div class="tip-box" markdown>
**The meta-signal interviewers look for:** *Would I trust this person with a system at 3 AM when it's on fire?* Every answer should nudge toward yes.
</div>
