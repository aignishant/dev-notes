# Rapid Revision — 1-Hour Cheat Sheet

The night before the interview. Skim this, not the whole site.

---

## The 15 ideas every ML interview tests { #big-ideas }

1. **Bias-variance tradeoff** — simple models underfit (high bias), complex overfit (high variance). Find sweet spot via regularization + CV.
2. **Train / val / test** — val for hyperparameters, test touched *once*. Temporal split for time-series.
3. **Data leakage** — any info in features that wouldn't be available at prediction time. The #1 cause of "99% accuracy that crashes in prod."
4. **Class imbalance** — accuracy lies. Use PR-AUC, threshold tuning, class weights. SMOTE is usually overrated.
5. **Cross-validation** — k-fold for IID, time-series split for temporal, stratified for imbalance, grouped for leaky groupings.
6. **Regularization** — L1 (sparse, feature selection), L2 (smooth, collinearity), ElasticNet (both), dropout (NN), early stopping.
7. **Gradient descent family** — SGD, Momentum, Adam, AdamW. Adam is the default for NN; LightGBM has its own optimizer.
8. **Bagging vs boosting** — bagging (parallel, reduces variance, RF), boosting (sequential, reduces bias, XGBoost).
9. **Metrics map to business** — F1 when both errors matter, precision when FP costly, recall when FN costly, MAE for symmetric regression, quantile loss for asymmetric.
10. **Feature engineering beats model choice** on tabular data 80% of the time.
11. **Start boring** — logistic regression or LightGBM before any neural net on tabular data.
12. **Calibration** ≠ discrimination. A model can rank perfectly but still output miscalibrated probabilities.
13. **Drift** — data drift (input shift), concept drift (relationship shift), label drift (prior shift). Monitor all three.
14. **Reproducibility** — seed, data snapshot, code version, environment. Without it, you can't debug production.
15. **The 10× rule** — if someone asks "make it 10% more accurate," 9 times out of 10 the right answer is "why?" not "yes."

---

## Must-know formulas { #formulas }

| Concept | Formula |
|---|---|
| **MSE** | `(1/n) Σ (yᵢ - ŷᵢ)²` |
| **MAE** | `(1/n) Σ |yᵢ - ŷᵢ|` |
| **Log loss** | `-(1/n) Σ [yᵢ log(ŷᵢ) + (1-yᵢ) log(1-ŷᵢ)]` |
| **Precision** | `TP / (TP + FP)` |
| **Recall** | `TP / (TP + FN)` |
| **F1** | `2·P·R / (P + R)` |
| **R²** | `1 - SS_res / SS_tot` |
| **Sigmoid** | `1 / (1 + e⁻ˣ)` |
| **Softmax** | `eˣᵢ / Σ eˣⱼ` |
| **Bias-variance** | `E[(y - ŷ)²] = Bias² + Variance + σ²` |
| **Gradient update** | `w ← w - η ∇L(w)` |

---

## Decision cheat sheet { #decisions }

**Classification threshold?** → Maximize F1 on validation, or pick threshold that hits business precision/recall target.

**Imbalanced data?** → Class weights > SMOTE. Optimize PR-AUC. Threshold tune.

**Too many features?** → LightGBM feature importance + permutation importance. Drop correlated pairs. Don't RFE with 500+ features.

**Missing values?** → Tree models (XGBoost/LightGBM): pass through. Linear/NN: impute + add missingness indicator.

**Categorical features?** → Low cardinality: one-hot. High cardinality: target encoding with out-of-fold. Tree models: ordinal is often fine.

**Time-series data?** → Never shuffle. Features from past only. TimeSeriesSplit for CV. Watch for weekly/yearly seasonality.

**Model won't converge?** → Check LR (too high → NaN, too low → flat loss). Check feature scaling. Check for nan/inf in data.

**Great train, poor test?** → Overfitting → more regularization, more data, simpler model, early stopping.

**Poor train, poor test?** → Underfitting → more features, more model capacity, less regularization.

**Production accuracy dropped?** → Feature drift > model drift > label shift. Check PSI per feature first.

---

## The phrases that earn points { #phrases }

- *"Before choosing a model, I'd establish a baseline with logistic regression."*
- *"I'd want to clarify the business metric before picking an ML metric."*
- *"PR-AUC is more informative than ROC-AUC for imbalanced problems."*
- *"I'd run it in shadow mode for a week before any user-facing rollout."*
- *"I'd monitor PSI per feature and alert at 0.2."*
- *"Feature engineering usually moves the needle more than model choice on tabular data."*
- *"I'd prefer a simple, interpretable model unless the accuracy gain is material and measurable."*
- *"I'd retrain on a rolling window rather than all historical data."*
- *"The label definition is where most projects fail — I'd nail that down first."*

## The phrases that lose points { #red-flags }

- *"I'd throw a neural network at it."* (Without justification, signals inexperience.)
- *"The model got 99% accuracy."* (Without checking for leakage or imbalance.)
- *"I'd use SMOTE."* (Default-picking an overrated technique.)
- *"I'd use all the data."* (Without temporal considerations.)
- *"Just tune the hyperparameters."* (Skipping feature engineering and diagnosis.)
- *"We can always retrain later."* (Missing the monitoring/rollback story.)

---

## 60-second elevator pitch for yourself

Practice this until it flows:

> "I'm an ML engineer with [X] years of experience. My focus is [tabular/NLP/vision/recsys]. I've shipped models in [fraud/ranking/forecasting/etc.] at [scale — e.g., 10M predictions/day]. My strongest skill is [X] — for example, [one concrete story — "I reduced our model's p99 latency from 200ms to 40ms by moving from XGBoost to a distilled LightGBM served via ONNX"]. What I'm looking for: [growth area — "I want to go deeper on LLMs in production"]."

Three rules:

1. One number (scale, latency, business impact).
2. One concrete story (not generic).
3. One honest growth edge (not weakness-theater).

---

## Final checklist — the morning of { #morning-of }

- [ ] Re-read the big 15 ideas above.
- [ ] Re-practice your 60-second pitch out loud.
- [ ] Review 2–3 projects you'd reference — metric, scale, your role, outcome.
- [ ] Have a question ready for them: *"What does a successful first 90 days look like in this role?"*
- [ ] Water, not coffee (jitters hurt clarity).
- [ ] Walk 10 minutes before the call — it resets cortisol.

**You've prepared. Trust the prep. Go.**
