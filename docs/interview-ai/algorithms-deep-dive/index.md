# ML Algorithms — Deep Dive Mastery

<div class="hero" markdown>

## The algorithm encyclopedia for interviews that actually ship

**115+ questions** across **7 modules** covering every classical ML algorithm you'll be asked about — from logistic regression to gradient boosting internals to DBSCAN's unreasonable effectiveness. Every answer comes with the math, the intuition, the Python, and the production scar tissue.

</div>

<div class="stats-grid" markdown>

<div class="stat-card" markdown>
**115+**
conceptual & scenario questions
</div>

<div class="stat-card" markdown>
**7**
algorithm families covered
</div>

<div class="stat-card" markdown>
**50+**
Python code snippets
</div>

<div class="stat-card" markdown>
**3**
mock interview rounds
</div>

</div>

---

## Why this guide exists

Most algorithm resources pick a side: **math-heavy** (great for exams, useless when an interviewer asks "why does LightGBM win 9/10 Kaggle competitions?") or **code-heavy** (great for blog posts, useless when an interviewer asks "derive the dual form of SVM").

This guide covers **both** for every algorithm:

- The **math** (derivations, objective functions, complexity) — so you can defend any choice.
- The **intuition** (when it works, when it breaks, analogies that stick) — so you can *explain* to a non-ML stakeholder.
- The **Python** (scikit-learn, LightGBM, statsmodels) — so you can reach for it under time pressure.
- The **production lens** (scale, latency, memory, retraining) — so you sound like someone who has shipped, not just studied.

## Module map

| Module | Range | Focus | Must-know for roles |
|---|---|---|---|
| 📘 **Linear & GLMs** | Q1–Q15 | Linear/logistic regression, Ridge, Lasso, Poisson, SVR | All roles — table-stakes |
| 🌲 **Tree Ensembles** | Q16–Q35 | CART, RF, GBM, XGBoost, LightGBM, CatBoost internals | Tabular-heavy roles (finance, ads, fraud) |
| ⚙️ **Kernels & SVM** | Q36–Q50 | SVM primal/dual, kernel trick, RBF, one-class | ML research, NLP/CV baselines |
| 🎲 **Probabilistic & Instance** | Q51–Q65 | Naive Bayes, kNN, Bayesian networks, HMM | NLP, search, health |
| 🧭 **Clustering & Unsupervised** | Q66–Q85 | K-means, DBSCAN, HDBSCAN, GMM, PCA, t-SNE, UMAP | Segmentation, exploratory |
| 📈 **Time Series** | Q86–Q100 | ARIMA, Prophet, state-space, Kalman, ARCH/GARCH | Forecasting, demand, finance |
| 🛒 **Recommenders & Specialty** | Q101–Q115 | Matrix factorization, ALS, Isolation Forest, LOF | Recsys, anomaly detection |

## How to use this guide

<div class="scenario" markdown>

### 3-pass study method

**Pass 1 — Breadth (3 days).** Read every question title and the first paragraph of each answer. Build a mental map of *what exists*.

**Pass 2 — Depth (1 week).** Pick the 2 modules most relevant to the role. Rewrite each answer in your own words. Run every code snippet.

**Pass 3 — Mocks (2 days).** Do all 3 mock rounds, timed. Review with the rubrics.

**Day before.** Only the rapid-revision cheat sheet.
</div>

## What makes an algorithm answer "senior"

An entry-level candidate explains *what* the algorithm does. A senior candidate explains:

1. **What objective** is being optimized (and what alternatives exist).
2. **Computational complexity** in training and inference.
3. **When it breaks** — assumptions that fail in practice.
4. **What you'd use instead** and why.
5. **Production concerns** — memory, drift sensitivity, interpretability.

Every answer in this guide is written to hit those five beats. Ready? Open any module →
