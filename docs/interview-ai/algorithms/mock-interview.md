# Mock Interviews

Three timed mock rounds, each focused on algorithm-choice scenarios. Time yourself. After each, score against the rubric. Do this three times over two weeks and you will destroy real interviews.

---

## Round 1 — 30-minute Phone Screen

**Scenario:** You're interviewing for a Senior ML Engineer role at a mid-size e-commerce company. The interviewer is a Staff engineer.

---

### Q1 (3 min): "Walk me through what happens mathematically when you call `RandomForestClassifier().fit(X, y)`."

**Strong answer structure:**

1. **Bagging:** Draw B bootstrap samples (sampling with replacement) from the training set. Each sample is roughly 63% unique rows.
2. **Per tree:** Grow a decision tree on that sample. At each split, pick the best split among a random subset of features (`max_features=sqrt(p)` by default for classification).
3. **Split criterion:** Gini impurity (by default). The split that maximizes weighted Gini reduction wins.
4. **Stopping:** Trees grow until pure leaves or until a depth/size limit (default: no limit in sklearn).
5. **Prediction:** Majority vote across trees (or averaged probabilities for `predict_proba`).

**Bonus points for mentioning:**

- OOB (out-of-bag) error computed from the ~37% of samples each tree didn't see.
- Why feature subsampling decorrelates trees → lower ensemble variance.
- Training is parallelizable (unlike boosting).

**Scoring:**

- 3/3: Covered bagging, feature subsampling, split criterion, prediction.
- 2/3: Covered most but missed one critical piece (e.g., feature subsampling).
- 1/3: Described the algorithm superficially but missed the key math.

---

### Q2 (5 min): "I have a classification dataset with 100K rows, 20 features, 5% positive class. Which algorithm would you try first, and why? How would you handle the imbalance?"

**Strong answer:**

"I'd start with LightGBM because of tabular data and 100K rows puts it in its sweet spot — fast training, robust accuracy.

For imbalance at 5%, that's moderate, not extreme. My approach:

1. First, try without rebalancing but use `scale_pos_weight=19` (neg/pos ratio).
2. Monitor PR-AUC, not accuracy — accuracy is misleading.
3. Tune the decision threshold based on the business cost of FP vs FN, not the default 0.5.
4. I'd avoid SMOTE — it rarely helps with tree models and can add noise.

If PR-AUC is still poor, I'd look at:
- Feature engineering (is there a signal I'm missing?).
- Focal loss as a custom objective to focus on hard examples.
- Collecting more positive examples if possible.

Before all this, I'd do a null-model check: predict class-ratio frequency; confirm any trained model beats that baseline."

**Interviewer probes:**

- "What about SMOTE?" → "For tree models, usually not worth it. The model cares about feature rank order and splits; SMOTE adds synthetic points that don't reliably improve splits. I'd only try it after exhausting weight-based and loss-based approaches."
- "What metric would you optimize?" → "Depends on business cost. If FP and FN have equal cost, F1. If FN is worse (missed fraud), recall at fixed precision. I'd build a cost curve with the stakeholder."

---

### Q3 (6 min): "When would you use a Random Forest vs Gradient Boosting?"

**Strong answer:**

"They're both tree ensembles but solve different problems:

- **Random Forest** reduces **variance** through bagging and feature randomization. It's less prone to overfitting, trains in parallel, and needs minimal tuning. Good first choice for robustness.

- **Gradient Boosting** reduces **bias** by sequentially fitting residuals. Each tree corrects the previous ones' errors. Much more accurate on well-curated tabular data but more sensitive to hyperparameters and prone to overfitting without regularization.

In practice:
- **First baseline or messy/noisy data** → Random Forest. No tuning required.
- **Production / competition accuracy** → LightGBM or XGBoost. Needs tuning but extra 2–5% accuracy.
- **Outliers in target** → Random Forest is more robust. Boosting keeps fitting to them.

A subtle point: they scale differently. More trees in RF → diminishing returns but never hurts. More trees in GBM → can overfit without early stopping."

---

### Q4 (8 min): "Design a model to predict if a user will churn in the next 30 days. Walk me through the whole process."

**Strong answer structure (talk through out loud):**

"First, I'd clarify the problem:

- What's the churn definition exactly? Uninstall? No activity for 30 days? Contract cancel?
- What's the business use? If the team can only contact 1000 users per week, I care about precision at top-k, not overall accuracy.
- What's the cost of false positives vs negatives?

Assuming a SaaS churn-in-30-days problem:

**1. Label definition:** For each user at time t, label = 1 if they churned between t and t+30. I'd exclude features that only appear because churn is already in progress (e.g., visited the cancel page) to avoid leakage.

**2. Feature engineering:**
- Usage trends: logins in last 7/30 days, delta vs previous period.
- Engagement velocity: new features used, depth of usage.
- Customer health: support tickets, NPS if available.
- Account data: tenure, plan, company size.

**3. Split:** Time-based — train on users as of 2025 Q1, validate on Q2, test on Q3. NOT random splits (leaks future).

**4. Model:** LightGBM. Tabular, mixed types, needs SHAP for CSM interpretability.

**5. Evaluation:**
- PR-AUC.
- Lift@10%: if we contact top 10% riskiest, what fraction of churners do we catch?
- Calibration: does 30% risk mean 30% actually churn?

**6. Deployment:**
- Weekly scoring.
- Hand top-k to CS team.
- A/B test the intervention itself — does contacting high-risk users reduce churn?

**7. Monitoring:**
- Feature drift (did a product change alter usage patterns?).
- Performance decay.
- Retrain monthly."

**Scoring:**

- 4/4: Clarified the problem, thought about leakage, picked LightGBM with reasoning, mentioned business metrics and deployment.
- 3/4: Solid modeling answer but missed leakage or deployment.
- 2/4: Named an algorithm, discussed some features, but didn't show production thinking.

---

### Q5 (8 min): "You deploy your churn model. It was 92% accurate in test. After two months, performance has dropped to 74%. Walk me through how you'd debug."

**Strong answer:**

"Accuracy alone is suspicious here (imbalanced problem), but assume the drop is real on PR-AUC or recall. I'd work through a checklist:

**Step 1 — Data pipeline integrity:**
- Are features being computed the same way in production vs training?
- Any schema changes? New missing values?
- Run a KS test comparing live feature distributions to training distributions.

**Step 2 — Concept drift:**
- Has the *relationship* between features and churn changed?
- Compare model residuals over time. Are predictions systematically off for certain cohorts?
- If there was a product change in the last 2 months (e.g., new pricing tier, new feature), retrain with recent data.

**Step 3 — Label drift:**
- Did the definition of churn change (support tickets reclassified)?
- Are we measuring the same label we trained on?

**Step 4 — Model staleness:**
- If I never retrained, drift explains everything.
- Set up a retraining cadence and benchmark weekly.

**Step 5 — External factor:**
- Did a competitor launch something? Economic shift? These often explain drift.

**Step 6 — Action:**
- If the cause is fixable (pipeline bug) → fix and redeploy.
- If drift → retrain on recent data, consider online learning if drift is continuous.
- If product change → add new features capturing the change, retrain."

---

**Phone screen rubric (out of 15):**

- 13–15: Strong hire. Show production maturity, not just algorithm knowledge.
- 10–12: Hire. Solid ML fundamentals, some gaps in system thinking.
- 7–9: Borderline. Knows the algorithms but struggles with tradeoffs.
- < 7: No hire. Significant gaps in core knowledge.

---

## Round 2 — 60-minute Technical Deep Dive

**Scenario:** You're deep into the loop for a Staff ML role at a subscription music streaming company. The interviewer is a Principal ML engineer.

---

### Part A (15 min): "Tell me everything you know about gradient boosting."

Expected depth:

1. **Core math:** Fit trees sequentially to pseudo-residuals (negative gradients of loss).
2. **Hyperparameters:**
   - Learning rate (shrinkage) — smaller = more trees, better generalization.
   - Depth / num_leaves — controls interaction order.
   - Min samples per leaf — regularization.
   - Subsampling — stochastic gradient boosting.
   - L1/L2 on leaf weights.
3. **Variants:**
   - XGBoost: second-order gradients + regularization in objective.
   - LightGBM: histogram-based splits, leaf-wise growth, GOSS, EFB, native categorical.
   - CatBoost: ordered target encoding, oblivious trees, ordered boosting.
4. **When it fails:**
   - Extrapolation (prediction plateaus at training max).
   - Very noisy labels (keeps fitting noise).
   - Extreme imbalance (needs threshold tuning).
   - Sparse high-dim data (linear beats it).
5. **Tuning strategy:** Optuna over learning_rate (log), num_leaves, feature/bagging fraction, min_data_in_leaf, L2 reg.
6. **When NOT to use:** Extrapolation needed, need calibrated probabilities (use Platt/isotonic on top), need online learning.

**Follow-up probes:**

- "Why are XGBoost and LightGBM faster than sklearn's GBM?" → Pre-sorted blocks, parallelized split-finding, histogram optimization.
- "How would you explain SHAP values to a non-technical manager?" → "SHAP assigns each feature a credit score for the prediction. Like explaining a soccer player's contribution to a goal — some set up, some scored. The numbers add up to the prediction."

---

### Part B (15 min): Scenario — "We're losing ~3% of users per month. Design an end-to-end ML system to reduce that."

**Expected components:**

1. **Frame the problem:**
   - Is this individual-level prediction (churn) or aggregate (monthly rate)?
   - What's the desired outcome — predict churn, reduce it, both?
   - What's the latency/cadence? Batch weekly vs real-time?

2. **ML model for prediction:**
   - LightGBM churn predictor (as in Phone Round Q4).
   - SHAP for per-user explanations.

3. **Intervention design:**
   - Different interventions by risk level: email, push, in-app, human outreach.
   - Match intervention to SHAP's top reason (usage drop → content rec; billing issue → concierge).

4. **A/B testing the intervention:**
   - Holdout group: high-risk users with no intervention.
   - Measure: churn reduction, CLV lift, revenue impact.

5. **Feedback loop:**
   - Re-train weekly with new churn labels.
   - Update intervention strategies based on A/B results.
   - Watch for over-intervention (too many emails → unsubscribes).

6. **Metrics (not just accuracy):**
   - Predicted-to-actual churn alignment.
   - Intervention lift (churn_control - churn_treatment).
   - Unit economics (cost of intervention vs retained LTV).

**Strong candidates go beyond the ML model.** Mediocre candidates only talk about the model.

---

### Part C (15 min): "Here's a dataset preview. What's wrong with it?"

*(Interviewer shares a dataset screenshot with the following issues)*

- `user_id` duplicated across rows (multiple transactions per user).
- `is_churned` column has 48% positives — suspiciously balanced.
- `revenue` column has negative values.
- `signup_date` is "2025-13-45" for some rows.
- Strong correlation between `last_active_date` and target — looks like leakage.
- `country` has 1,247 unique values but should be 195.

**Strong answer:**

"Several red flags:

1. **User ID duplicates:** Need to understand the grain. Is this user-month or user-transaction? Aggregate or deduplicate before modeling.

2. **48% positives:** That's way too balanced for real churn (usually 2–10%). Possible causes: sampling bias (only sampled high-risk users), label leakage, or definition mismatch.

3. **Negative revenue:** Refunds? Corrupted data? Need to ask domain owner.

4. **Invalid dates:** '2025-13-45' is a parsing issue. Run data quality checks: `pd.to_datetime(errors='coerce')` and inspect NaT counts.

5. **Correlation with target:** `last_active_date` being highly correlated screams label leakage — the date of last activity is essentially defined *by* the churn event. Drop it or use a version with a consistent time cutoff.

6. **Too many countries:** Typos, mixed encodings. Clean with a country mapping; group rare ones as 'Other.'

Before modeling: data quality audit. If I skip this, my model will be wrong in confusing ways."

---

### Part D (15 min): Coding — "Implement a train/test split that respects temporal order for a churn dataset."

```python
import pandas as pd
import numpy as np
from sklearn.metrics import average_precision_score
import lightgbm as lgb

def time_split_churn(df, snapshot_col, target_col, 
                     train_end='2025-06-30', 
                     val_end='2025-09-30',
                     features=None):
    """
    Train: snapshots up to train_end.
    Val: train_end < snapshot <= val_end.
    Test: snapshot > val_end.
    """
    df = df.sort_values(snapshot_col).copy()
    df[snapshot_col] = pd.to_datetime(df[snapshot_col])
    
    train_mask = df[snapshot_col] <= train_end
    val_mask = (df[snapshot_col] > train_end) & (df[snapshot_col] <= val_end)
    test_mask = df[snapshot_col] > val_end
    
    if features is None:
        features = [c for c in df.columns 
                    if c not in [snapshot_col, target_col, 'user_id']]
    
    X_train, y_train = df.loc[train_mask, features], df.loc[train_mask, target_col]
    X_val, y_val = df.loc[val_mask, features], df.loc[val_mask, target_col]
    X_test, y_test = df.loc[test_mask, features], df.loc[test_mask, target_col]
    
    # Safety check: no user should appear in multiple splits unless we expect it
    train_users = set(df.loc[train_mask, 'user_id'])
    test_users = set(df.loc[test_mask, 'user_id'])
    overlap = train_users & test_users
    print(f"User overlap train/test: {len(overlap)} "
          f"(OK if users recur across snapshots)")
    
    return (X_train, y_train), (X_val, y_val), (X_test, y_test)


def train_eval(train, val, test):
    X_train, y_train = train
    X_val, y_val = val
    X_test, y_test = test

    train_set = lgb.Dataset(X_train, y_train)
    val_set = lgb.Dataset(X_val, y_val, reference=train_set)
    
    params = dict(objective='binary', metric='average_precision',
                  num_leaves=63, learning_rate=0.05, 
                  feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=5,
                  scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),
                  verbose=-1)
    
    model = lgb.train(params, train_set, num_boost_round=2000,
                      valid_sets=[val_set],
                      callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)])
    
    for name, X, y in [('Val', *val), ('Test', *test)]:
        pr_auc = average_precision_score(y, model.predict(X))
        print(f"{name} PR-AUC: {pr_auc:.4f}")
    
    return model
```

**Probes during coding:**

- "What if a user appears in both train and test?" → "For churn prediction, that's often expected — same user at different time snapshots. What we must prevent is information from future snapshots leaking into training features."
- "Why `scale_pos_weight`?" → "For imbalance. Roughly inversely proportional to class frequency."
- "Why early stopping on a separate val set, not test?" → "Test must remain truly held out. Val is for model-selection decisions, test for final reporting."

---

**Technical deep dive rubric (out of 20):**

- 18–20: Staff-level. Strong on algorithms, systems, code, and tradeoffs.
- 14–17: Senior-level. Solid in 3 of 4 areas.
- 10–13: Mid-level. Gaps in systems or tradeoffs.
- < 10: Not ready for Staff role.

---

## Round 3 — 75-minute Algorithm Design

**Scenario:** Final round for a Principal ML role. Design a full ML system; the interviewer probes every choice.

---

### The Prompt

"A large online learning platform wants to personalize its course recommendations. They have 10M users and 50K courses. Users show interest by browsing, enrolling, completing, and rating. Design their recommender."

---

### Expected answer structure (75 minutes)

**1. Clarify (5 min):**

- Business goal: more completions? engagement? revenue?
- Latency: batch nightly? real-time during browsing?
- Feedback loop: cold-start for new courses common?
- Existing infra: Python/Spark? GPU? Vector DB?

Assume: goal = maximize course completions; real-time; launches 500 new courses per month.

**2. High-level architecture (10 min):**

```
[User] → [Request]
          ↓
    [Retrieval stage — millisecond]
       ↓ (1000 candidates)
    [Ranking stage — fast GBDT]
       ↓ (scored list)
    [Re-ranking — diversity, freshness]
       ↓ (top 20)
    [Serve]
          ↓
    [Impression + click + complete logs]
          ↓
    [Offline training — daily]
```

**3. Retrieval stage (15 min):**

Multiple retrievers in parallel:

- **Popular + trending:** top courses by enrollments last 7 days, bucketed by interest.
- **Item-item CF:** co-enrollment nearest neighbors. Precomputed.
- **Two-tower semantic retrieval:**
  - User tower: user profile (past enrollments, completion rate, category interests, demographics).
  - Course tower: text embeddings + category + instructor + difficulty.
  - Trained with contrastive loss on (user, enrolled_course) pairs.
  - Serve via FAISS/HNSW.
- **Content-based:** if user searches "machine learning," TF-IDF/semantic match on courses.
- **Session-based:** SASRec over recent user activity for "next-best course."

Union top-200 from each → 1000-candidate pool (after dedup).

**4. Ranking stage (15 min):**

LightGBM with `lambdarank` objective.

Features:

- User × course: cosine sim from two-tower, # enrollments in category, past completion rate in category.
- User: tenure, active cohort, plan tier.
- Course: historical completion rate, avg rating, enrollment trend, recency.
- Cross: time-of-day × course duration (short videos for mobile evenings).

Training:

- Implicit signal: 1 if enrolled, 0 otherwise.
- Group by (user, session) for listwise training.
- Retrain daily on sliding window.

**5. Re-ranking (5 min):**

- **Maximum Marginal Relevance (MMR)** for diversity.
- **Freshness boost** for new courses (combats cold-start).
- **Category budgets** to prevent filter bubble.
- **Business rules:** hide already-enrolled, hide sold-out-like-equivalents.

**6. Cold start (5 min):**

- **New course:** Content embedding enters the two-tower item space immediately. Boost factor for ~first 30 days to gather interactions.
- **New user:** Demographic features drive initial embedding. Onboarding questionnaire. Default to popular + diverse categories.

**7. Evaluation (10 min):**

**Offline:**
- NDCG@10 on held-out enrollments.
- Hit rate@20.
- Coverage: what fraction of catalog gets shown?

**Online A/B:**
- Completions per user (primary).
- CTR, enrollment rate (leading indicators).
- Long-term retention, NPS (lagging).
- Course diversity per user (health metric).

**Counter-metrics to watch:**
- Popular-course cannibalization.
- New-user overwhelm.
- Engagement ≠ learning: users might engage with trivia, but completions require quality.

**8. Exploration and ongoing improvement (5 min):**

- Thompson sampling for a small (~2%) exploration slice.
- Multi-armed bandit for tuning ranking features.
- Watch for feedback loops (rich-get-richer on popular courses).

**9. Risks & mitigations (5 min):**

- **Popularity bias:** MMR + coverage metrics + exploration.
- **Concept drift:** User interests shift quarterly; retrain.
- **Regulatory / bias:** audit for demographic fairness (e.g., recommending vocational-only to low-income).
- **Gaming:** course authors might inflate ratings. Detect anomalies.

---

### Grader's questions throughout

- "Why two-tower instead of just CF?" → Scales to 10M × 50K; handles cold-start for new courses via content features.
- "Why GBDT ranker and not deep?" → Latency. GBDT inference is microseconds; deep ranker needs GPU serving. Also, GBDT is easier to tune and maintain. Revisit if offline gap is large.
- "Will your system ever recommend a course below its retrieval threshold?" → No, which is a limitation. If retrieval misses it, ranker can't recover. Hence multiple retrievers.
- "How would you handle abuse — a user trying to manipulate the recommender?" → Per-user velocity limits, feedback fraud detection (clicks without dwell), reweighted loss.

---

**Algorithm design rubric (out of 25):**

- 22–25: Principal-level. Strong system thinking, depth in every component, nuanced tradeoffs.
- 17–21: Senior/Staff. Good system design, some depth gaps.
- 12–16: Mid. Outlines a recommender but misses production concerns.
- < 12: Significant gaps — more theory than implementation.

---

**Meta-note across all rounds:**

The signal that separates great candidates from good ones:

- Great candidates **clarify before solving.**
- Great candidates **propose baselines** before complex models.
- Great candidates talk about **monitoring, drift, retraining** without being asked.
- Great candidates **admit uncertainty** and describe experiments to resolve it.
- Great candidates' answers **tie ML choices to business metrics.**

If you do these five things consistently, you will outperform 80% of candidates regardless of algorithm trivia knowledge.
