# 🎯 Mock Interviews

!!! abstract "How to use this module"
    Three full-length mock rounds covering the algorithm stack. **Set a timer, speak aloud, and only peek at the rubric after you've committed to an answer.** Passing interviews isn't about knowing more algorithms — it's about talking about them precisely under pressure.

---

## Round 1: Phone screen (45 minutes) { #round-1 }

Typical setting: tech screener or Zoom video, one senior ML engineer asking rapid-fire concept questions to filter for depth. Expect them to probe until you hit the edge of your knowledge.

### Section A — Linear & tree models (15 min)

**Q1.** Walk me through Ridge vs Lasso — and when would you use Elastic Net?

??? success "What strong candidates say"
    Ridge adds L2 penalty → closed-form solution $\hat\beta = (X^TX + \lambda I)^{-1}X^Ty$, shrinks coefficients smoothly but never to zero. Lasso adds L1 penalty → no closed form (solve via coordinate descent or LARS), **induces exact sparsity** because the L1 ball has corners on the axes. Ridge is better when all features matter a little; Lasso when you need feature selection. **Elastic Net** (Ridge + Lasso) handles the case Lasso fails in: correlated feature groups. Lasso arbitrarily picks one and zeros the rest; Elastic Net keeps them grouped.

    **Red flag:** saying "L1 selects features because gradients are zero" without the geometric intuition. Say "L1 ball has corners — the optimum lands on a corner, which means some coordinates are zero." That's the real reason.

**Q2.** How does XGBoost differ from vanilla Gradient Boosting?

??? success "What strong candidates say"
    Vanilla GBM: fit each tree to negative gradient of loss, step size $\eta$. XGBoost adds:
    
    1. **Second-order approximation** — uses gradient and Hessian, lets it converge faster and support custom losses.
    2. **Regularization** directly in the tree structure score: $\gamma T + \frac{1}{2}\lambda \sum w_j^2$.
    3. **Split finding** with histogram-based approximate algorithm (like LightGBM).
    4. **Sparsity-aware split** — handles missing values as a first-class citizen.
    5. **Column subsampling**, cache-aware access, parallel tree construction.
    
    The impact: faster, more regularized, usually wins tabular competitions through 2022 before LightGBM eclipsed it on speed for massive categorical data.

**Q3.** You've trained a Random Forest. It gets 95% train accuracy and 70% test accuracy. How do you diagnose?

??? success "What strong candidates say"
    Classic overfitting. Ordered actions:
    
    1. **Reduce tree capacity** — lower `max_depth`, raise `min_samples_leaf`.
    2. **Lower feature sampling** per split — `max_features` to $\sqrt{p}$ if not already.
    3. **More data or data augmentation** if feasible.
    4. **Check for leakage** — 95→70 gap is big enough that leakage is a real suspect, especially time-based or target-encoded features.
    5. Consider **switching to GBM**, which generally regularizes better than RF when tuned.
    
    Then I'd plot a **learning curve** — does train error come down as samples grow? If yes, data-limited. If no, model is memorizing something it shouldn't.

### Section B — SVM & kernels (10 min)

**Q4.** What is the kernel trick?

??? success "What strong candidates say"
    The dual SVM optimization only uses **inner products** $\mathbf{x}_i^T \mathbf{x}_j$. Replace with $K(\mathbf{x}_i, \mathbf{x}_j) = \phi(\mathbf{x}_i)^T \phi(\mathbf{x}_j)$ for some feature map $\phi$, and you implicitly operate in the $\phi$-space without ever computing $\phi$. Common kernels: polynomial, RBF (corresponds to an infinite-dimensional $\phi$), sigmoid. The "trick" is bypassing the explicit map — Mercer's theorem guarantees any positive-semidefinite $K$ corresponds to a valid Hilbert space feature map.

**Q5.** When would you NOT use SVM in 2026?

??? success "What strong candidates say"
    Most of the time, honestly. Tabular data above ~50k rows → XGBoost/LightGBM are strictly better. High-dim sparse (text, recsys) → linear models or transformers. Images/audio/text → deep learning. SVM still has niches: small datasets (<10k) with well-designed kernels, problems where margin maximization has a clean interpretation, one-class novelty detection. The model fell out of industrial favor primarily because it scales $O(n^2)$ to $O(n^3)$, which is untenable on modern data.

### Section C — Clustering & dimensionality (10 min)

**Q6.** K-means vs DBSCAN — when to choose which?

??? success "What strong candidates say"
    K-means: partitional, requires k, assumes roughly spherical equal-size clusters, scales to huge data. DBSCAN: density-based, discovers k, handles arbitrary cluster shapes, flags noise, but struggles with varying-density clusters and picks of `eps` depend on a k-distance plot.
    
    **Pick K-means when**: clusters are convex, you know k, data is huge, speed matters.
    **Pick DBSCAN when**: shapes are arbitrary, density is roughly uniform, noise exists, k is unknown.
    **Pick HDBSCAN when**: you want DBSCAN's benefits but with variable density and no `eps` hyperparameter.

**Q7.** t-SNE vs UMAP vs PCA — practical differences?

??? success "What strong candidates say"
    PCA: linear, preserves global variance directions, fast, reversible, bad at nonlinear structure.
    t-SNE: nonlinear, preserves **local** neighborhoods (Student-t heavy-tail fixes crowding), slow ($O(n^2)$ naive, $O(n \log n)$ with Barnes-Hut), non-parametric (no transform for new points), distances between clusters are **not meaningful**.
    UMAP: nonlinear, based on fuzzy simplicial sets + Riemannian approximation, preserves both local and some global structure, 10–100x faster than t-SNE, supports transform for new points, and tends to give more interpretable cluster-level distances.
    
    **Bottom line**: PCA for linear exploration and preprocessing, UMAP for nonlinear visualization and downstream ML, t-SNE still wins for publication-quality 2D visualizations when you don't care about global structure.

### Section D — Short-answer speed round (10 min)

**Q8.** Why does Naive Bayes work so well despite the naive independence assumption?

??? success "What strong candidates say"
    Two reasons: (1) Class posterior depends on **rank order** of probabilities, not absolute values — features can be correlated but if the violation affects all classes symmetrically, the argmax is unchanged. (2) The bias from the assumption is often dominated by the low variance of its estimator; in small-data, high-dim regimes (like text) this tradeoff favors NB. Zhang 2004 proved this formally.

**Q9.** You see ACF tailing off and PACF cutting off at lag 2. What model?

??? success "What strong candidates say"
    AR(2) — PACF cutoff identifies the AR order, ACF decay is consistent with AR. If the series isn't stationary, difference first and run the test on the differenced series. Fit ARIMA(2, d, 0) and verify residuals are white noise via Ljung-Box.

**Q10.** In a recommender with 50k items, retrieval gives you 200 candidates. Ranker adds 3% NDCG offline but 0% online CTR. Where's the bug?

??? success "What strong candidates say"
    Offline/online disconnect. Likely causes: (1) **position bias** — offline data is from a previous ranker; items at rank 1 got way more exposure. Apply IPS. (2) **Retrieval ceiling** — the ranker is rearranging an already-suboptimal candidate set. Check retrieval recall@200. (3) **Selection bias** — items never shown weren't scored offline. (4) **Diversity collapse** — new ranker is more confident, less diverse, and users bail. Fix: add an exploration bucket and evaluate the candidate generator separately from the ranker.

---

### Round 1 Rubric

| Bar | Description |
|---|---|
| **Strong hire** | Defines concepts precisely, gives geometric/statistical intuition, cites real-world tradeoffs, mentions scaling/cost concerns, catches interviewer gotchas |
| **Hire** | Correct on 7+ of 10, occasional missed nuance, recovers on follow-ups |
| **Lean hire** | Correct on 5–6, mostly textbook knowledge, weak on applied tradeoffs |
| **No hire** | <5 correct, confuses fundamentals (L1 vs L2, bias vs variance), can't defend claims |

---

## Round 2: Technical deep dive (60 minutes) { #round-2 }

Typical setting: on-site (or virtual on-site) with 1–2 ML engineers. One algorithm area chosen, pushed to the boundary. Expect whiteboard / shared doc.

### Scenario

> You've been asked to join a team building a **real-time anomaly detection system** for a cloud infrastructure provider. The system ingests **millions of metric time series** per minute (CPU, memory, disk I/O, network latency) from hundreds of thousands of hosts. SREs receive alerts when behavior looks anomalous. Right now the system uses **static thresholds per metric per host**, with many false positives and missed true alerts. You have 15 minutes to sketch your approach, then 45 minutes of Q&A.

### Part 1: Sketch your approach (15 min)

??? tip "High-level answer framework"
    **Step 1 — Problem decomposition**
    
    - Short-term anomalies (spikes, drops) vs regime changes (sustained shifts)
    - Point vs contextual vs collective anomalies
    - Labels: mostly unlabeled; some SRE-acknowledged true/false alerts exist → use for evaluation
    
    **Step 2 — Modeling stack**
    
    1. **Per-series baseline**: Prophet or STL-based decomposition to learn trend + weekly/daily seasonality per metric-host. Residual > $k\sigma$ = candidate anomaly.
    2. **Multivariate context**: group metrics per host into a feature vector, run **Isolation Forest** across recent window — catches "this host looks weird in the joint space."
    3. **Cross-host**: cluster hosts by behavior (K-means on feature embeddings) — within-cluster outliers are candidate anomalies ("one web server in the web-server cluster is behaving unlike its peers").
    4. **Change-point detection**: Bayesian online CP or CUSUM per metric for regime shifts.
    
    **Step 3 — Ensembling & scoring**
    
    - Rank-normalize each detector's score
    - Weighted sum, weights learned from SRE feedback labels
    - Threshold calibrated to a budget (N alerts per day)
    
    **Step 4 — Serving**
    
    - Streaming: use River (online ML) or Half-Space Trees for incremental IForest
    - Latency target: < 30 s from metric arrival to alert
    - Stateful: maintain rolling windows in Redis / Kafka Streams
    
    **Step 5 — Feedback loop**
    
    - Every alert → SRE marks true / false / unknown
    - Use as training signal for a **supervised model** (LightGBM) that re-ranks candidate anomalies
    - Retrain nightly with online learning for feature drift

### Part 2: Follow-up probes (45 min)

**Interviewer probe 1:** "Your Isolation Forest scores are noisy — one minute the host is anomalous, next minute it's not, even though nothing changed."

??? success "Strong answer"
    Multiple causes and fixes:
    
    1. **Score instability from subsampling.** IForest scores depend on a random sample of 256 points per tree. Use more trees (400+), larger sample, or seed the forest deterministically for stability. 
    2. **Feature-level noise.** Apply **smoothing** — use 1-minute rolling means or exponential smoothing on input features before scoring.
    3. **Post-score smoothing.** Aggregate scores over a 5-minute window — trigger only if median score in window crosses threshold. This trades latency for stability.
    4. **Hysteresis threshold.** Different enter vs exit thresholds (enter at 0.85, exit at 0.70) — prevents flapping around the boundary.

**Interviewer probe 2:** "SREs complain most alerts are for hosts that are being rebooted during planned maintenance. Fix it."

??? success "Strong answer"
    This is a **known-benign pattern** mislabeled as anomaly. Options:
    
    1. **Add a `maintenance` feature** to the model — is this host under maintenance? → feed as feature to the supervised re-ranker. If yes, suppresses anomaly score.
    2. **Exclusion filter** in the serving layer — query the maintenance system, suppress alerts for hosts with active change windows. Simple and effective.
    3. **Label leakage for supervised.** If labeled data includes post-hoc "false positive (was maintenance)" labels, the ranker will learn to suppress this naturally — validates the approach.
    4. **Right answer:** combine — exclusion filter as a hard rule (won't miss because model is confused), supervised re-ranker as a soft backup. Hard rules for known patterns, learned models for unknowns.

**Interviewer probe 3:** "Cluster (K-means) drift — hosts migrate between clusters as their workloads change. Your 'this host is unlike its peers' signal gives false positives during natural migration."

??? success "Strong answer"
    K-means is a static snapshot; the world is dynamic. Fixes:
    
    1. **Re-cluster periodically** (daily) and use a sliding window of features.
    2. **Soft clustering** (GMM) — get cluster assignment probabilities. "Drift" is a gradual shift in posterior, not a hard jump.
    3. **Local density methods** (LOF) instead of K-means-based — detects anomalies relative to *current* k-NN, naturally adapts.
    4. **Change-point detection** on the cluster assignment per host — flag when a host transitions clusters and *skip anomaly scoring during transition*.
    5. The meta-point: **anomaly detection must account for non-stationarity**. A detector that assumes the world was the same last week as this week will have false positives every time behavior evolves.

**Interviewer probe 4:** "Rank the three biggest risks with this design."

??? success "Strong answer"
    1. **Alert fatigue from false positives.** With millions of series and moderate precision, even 0.01% FP rate = thousands of bad alerts per day. Must budget alerts and calibrate thresholds against SRE capacity — **precision@capacity**, not raw recall.
    2. **Feedback loop bias.** Supervised re-ranker learns from labels biased toward what SREs saw. Anomalies we never surface can't be learned. Mitigation: exploration bucket (small random sample of low-score anomalies still surfaced for SRE review) — expensive but essential.
    3. **Concept drift.** Workloads, deploy patterns, and infrastructure evolve monthly. Models stale quickly. Mitigation: monitor per-feature drift (KS test), auto-retrain when drift exceeds threshold, **shadow-deploy** new models and compare against current before cutover.

---

### Round 2 Rubric

| Criterion | Strong signal | Weak signal |
|---|---|---|
| **Problem decomposition** | Calls out anomaly types, labels, latency early | Jumps straight to algorithm without framing |
| **Algorithm selection** | Justifies with data properties (scale, dim, feedback) | Picks favorite without defense |
| **Ensembling mindset** | Proposes 2+ detectors + rank-ensemble | Single-model solution |
| **Production mindset** | Discusses latency, state, retraining, drift, monitoring | Pure model talk, no operational layer |
| **Feedback loop bias** | Raises exploration / debiasing proactively | Misses completely |
| **Communication** | Explains tradeoffs, calibrates confidence | Hedges constantly or over-asserts |

---

## Round 3: Applied algorithm system design (75 minutes) { #round-3 }

Typical setting: final round, panel of 2 senior engineers + 1 tech lead. Full-system ML design with algorithm choices front and center.

### Scenario

> You're building a **job recommendation system** for a job board with **5 million active users**, **200k job postings** refreshed daily. Users apply to ~0.5% of jobs they see. The board makes money when applications convert to hires. Design the end-to-end system, with special attention to algorithm choices at each stage. Budget: one ML engineer, one backend engineer, 3 months to first production launch.

### Expected answer structure (senior ML engineer)

#### 1. Clarifying questions (first 5 min)

!!! info "Questions worth asking"
    - What's the current baseline (popularity, manual curation, nothing)?
    - Do we have labels beyond applications (saves, views, time-on-posting, ultimately hires)?
    - Cold start severity — how many new users per day, how many new jobs per day?
    - Latency budget for feed generation?
    - Do we personalize by query (search) or just homepage feed (recsys)?
    - Fairness / regulatory constraints (job recommendations have legal implications — EEOC, disparate impact)?

#### 2. Problem framing (10 min)

**Objective**: maximize application-to-hire conversion, subject to **diversity constraint** (avoid funneling all women to admin roles — real legal risk).

**Labels in order of fidelity**: hire → interview → application → save → view.

**Multi-objective**: weighted combination `w_a * P(apply) + w_i * P(interview) + w_h * P(hire)` with $w$s learned from historical data.

#### 3. Architecture (20 min)

```
USER  ──► Retrieval ──► Ranking ──► Diversity rerank ──► Feed
          (10k jobs)    (500 jobs)   (100 jobs)
            ~5ms          ~30ms       ~2ms
```

**Retrieval (multi-source union):**

| Source | Method | Weight |
|---|---|---|
| **Content** | Job text + user resume → SBERT embedding, FAISS ANN | High for cold users |
| **Collaborative** | Two-tower (user side: history, skills; job side: features) | High for warm users |
| **Geographic** | Jobs within N miles of user | Hard filter |
| **Recent applicants** | Jobs similar users applied to in last 7 days | Freshness boost |

**Ranking (deep learning ranker):**

- Inputs: user features, job features, **cross features** (user-skill × job-required-skill, user-seniority × job-level), context (time-of-day, device)
- Architecture: DCN v2 (deep & cross network) or DLRM — feature crosses matter enormously here
- Loss: multi-task learning — predict apply / interview / hire jointly with shared bottom
- Training data: impression-level logs with IPS weights for position bias

**Rerank:**

- MMR (Maximal Marginal Relevance) for category diversity
- Fairness constraint: no single job category > 50% of top-10 feed
- Freshness boost: newly posted jobs get small score bonus

#### 4. Algorithm choices — defend each (15 min)

| Decision | Why |
|---|---|
| Two-tower over MF | Needs content features for cold-start new jobs (200k/day) |
| DCN v2 over LightGBM | Cross features between user and job are the strongest signal; DCN learns them efficiently |
| SBERT over TF-IDF | Semantic match (user wrote "python dev" → matches "backend engineer (Py)") |
| Multi-task over single-objective | Hires are sparse; leveraging denser signals (applications, saves) via shared representation |
| MMR over DPP for diversity | DPP is more principled but MMR is 10× cheaper, adequate for 100-item feed |
| FAISS HNSW over LSH | Better recall for dense embeddings at this scale |

#### 5. Cold start & fairness (10 min)

**New user:**
- Resume upload → embed → match content retrieval on day 1
- Small onboarding (3-5 preference questions) seeds the warm tower
- Explicit exploration bucket for new users' first 5 sessions (5% random injection into feed)

**New job:**
- Two-tower uses features, not IDs, so embeddings available immediately
- Freshness boost for first 24 hours
- Editorial / boosted slot for employer-paid postings (business reality)

**Fairness:**
- **Audit** recommendations quarterly: does top-10 for women-indicating profiles overrepresent traditionally-female-coded roles?
- **Post-processing fairness**: ensure demographic parity within role categories
- **Counterfactual evaluation**: generate counterfactual profiles (swap gender-correlated tokens) and check rec stability
- Don't train on gender/race, but know **proxies will leak** — active monitoring required

#### 6. Evaluation & launch plan (10 min)

**Offline:**
- Recall@100 for retrieval
- NDCG@10, MAP for ranker
- Per-category coverage for diversity

**Online:**
- A/B test vs baseline, primary metric = hire rate (but long measurement window — hires take weeks)
- Guardrails: application rate, time-on-site, diversity metrics
- 5% holdout always keeps the baseline for regression testing

**Launch phases:**
1. Week 4: Retrieval only (two-tower) + simple point-wise ranker (LightGBM) — replaces popularity baseline
2. Week 8: Multi-task DCN ranker in A/B test
3. Week 10: Diversity rerank + fairness audits
4. Week 12: Production full rollout

#### 7. What could go wrong (5 min)

- **Employer gaming**: advertisers stuff keywords to match more queries → need spam filters on job side
- **Filter bubble**: user only sees data science roles because they applied once → exploration + diversity guards
- **Selection bias in labels**: applications are only from jobs we showed → IPS critical
- **Long feedback loop**: hires take weeks → apply rate is a lagging-indicator proxy, primary signal
- **Regulatory**: NYC Automated Employment Decision law (2023) requires bias audit — budget for this

---

### Round 3 Rubric

| Criterion | Strong signal |
|---|---|
| **Algorithm grounding** | Defends every algorithm choice with data properties and tradeoffs |
| **Two-stage recsys architecture** | Proposes retrieval + ranking + rerank, with latency per stage |
| **Multi-task / multi-objective** | Identifies label sparsity, leverages denser signals |
| **Cold-start plan** | Separate strategies for new users and new items, with exploration |
| **Fairness / ethics awareness** | Raises bias audits, legal constraints, counterfactual eval without prompting |
| **Business mindset** | Links back to hire rate, employer paid postings, launch milestones |
| **Risk enumeration** | Identifies top 3–5 risks with mitigations |

---

## ✅ Rounds Recap

- **Round 1**: Define, compare, pick. Be precise and cite geometric/statistical intuition.
- **Round 2**: Own a system end-to-end. Ensembling, feedback loops, and drift matter as much as the model.
- **Round 3**: Senior bar. Justify **every** algorithm choice, think in two stages, raise fairness / bias before they ask.

The bar rises each round, but the pattern is constant: **precise concept → algorithm selection → production-grade concerns**. Run each round with a timer; score yourself honestly; repeat until you hit "strong hire" on all three.

→ Next: [📋 Rapid Revision](rapid-revision.md)
