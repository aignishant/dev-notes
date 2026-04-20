# ML Algorithms — Interview Mastery

<div class="hero" markdown>
## Every classical ML algorithm, dissected.

From linear regression's closed form to LightGBM's histogram tricks, from K-means' Lloyd convergence to UMAP's manifold approximation — **125+ questions** that cover the *why*, not just the *what*, of every algorithm you'll be asked about.

No hand-waving. Math where it matters. Python where it helps. Scenarios where you'll sweat.
</div>

<div class="stats-grid" markdown>
<div class="stat-card" markdown>
**125+**
Deep-dive questions
</div>

<div class="stat-card" markdown>
**8**
Algorithm families
</div>

<div class="stat-card" markdown>
**50+**
Production scenarios
</div>

<div class="stat-card" markdown>
**3**
Mock interview rounds
</div>
</div>

## Module map

| # | Module | Questions | Focus |
|---|---|---|---|
| 1 | [Linear Models](linear-models.md) | Q1–Q15 | OLS, GLMs, regularized variants, assumptions |
| 2 | [Tree-Based Models](tree-models.md) | Q16–Q40 | Trees → RF → GBM → XGBoost/LightGBM/CatBoost |
| 3 | [Distance & Probabilistic](distance-probabilistic.md) | Q41–Q55 | KNN, Naive Bayes, LDA/QDA, GMM |
| 4 | [SVM & Kernels](svm-kernels.md) | Q56–Q70 | Margin, duality, kernel trick, SVR |
| 5 | [Unsupervised Learning](unsupervised.md) | Q71–Q95 | Clustering, dim reduction, anomaly detection |
| 6 | [Time Series](time-series.md) | Q96–Q110 | ARIMA, Prophet, state-space, modern ML approaches |
| 7 | [Recommender Systems](recommenders.md) | Q111–Q125 | CF, MF, implicit feedback, two-tower |
| 8 | [Algorithm Selection](algorithm-selection.md) | Q126–Q135 | When to use what, under which constraints |
| 9 | [Mock Interviews](mock-interview.md) | 3 rounds | Algorithm-choice scenarios with rubrics |
| 10 | [Rapid Revision](rapid-revision.md) | — | Cheat sheet & algorithm decision tree |

## The algorithm-thinking framework

Every algorithm in this site is analyzed along six axes:

1. **Assumptions** — what must be true about the data for it to work
2. **Objective** — what it's actually optimizing
3. **Mechanics** — how the optimization is executed
4. **Complexity** — time and space, train vs inference
5. **Failure modes** — where it breaks, and why
6. **When to pick it** — the concrete production signal

<div class="tip-box" markdown>
**Interview signal:** The strongest candidates don't just name algorithms — they articulate *tradeoffs*. "I'd use LightGBM because…" loses to "I'd use LightGBM over XGBoost because of histogram binning on large datasets, and over Random Forest because boosting reduces bias where our baseline underfits."
</div>

## Study plan

!!! tip "The 3-pass method"
    - **Pass 1 (breadth):** Read every module's first 3 questions. Know the taxonomy.
    - **Pass 2 (depth):** Pick the 3 families you'll be grilled on (usually tree-based + unsupervised + one specialty). Rewrite answers in your own words.
    - **Pass 3 (scenarios):** Run the mock interviews timed. Score against the rubrics.

Let's go.
