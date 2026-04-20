# 📈 Time Series Forecasting

!!! abstract "Module Scope"
    Classical (ARIMA family, exponential smoothing, state space) + modern ML approaches (boosting on features, Prophet, N-BEATS). Questions **Q86–Q100**. Time series interviews punish people who apply iid ML blindly — interviewers test whether you understand **stationarity, autocorrelation, leakage, and proper validation**.

---

## Q86. Derive ARIMA(p, d, q) from first principles { #q86 }

<span class="q-badge">Conceptual • Classical</span>

**ARIMA = AutoRegressive Integrated Moving Average.** Three pieces:

1. **AR(p)**: current value depends on last $p$ values.
   $$y_t = \phi_1 y_{t-1} + \phi_2 y_{t-2} + \cdots + \phi_p y_{t-p} + \epsilon_t$$

2. **I(d)**: series is differenced $d$ times to become stationary.
   $$\nabla y_t = y_t - y_{t-1}, \quad \nabla^2 y_t = \nabla(\nabla y_t)$$

3. **MA(q)**: current value depends on last $q$ shocks (forecast errors).
   $$y_t = \epsilon_t + \theta_1 \epsilon_{t-1} + \cdots + \theta_q \epsilon_{t-q}$$

Combined ARIMA(p, d, q): difference $d$ times, then apply AR(p) + MA(q) to the differenced series:

$$\phi(B)(1 - B)^d y_t = \theta(B)\epsilon_t$$

where $B$ is the backshift operator $B y_t = y_{t-1}$.

**Assumptions**: errors are white noise (iid, zero mean, constant variance), underlying process is linear after differencing.

| Piece | Fixes | Diagnostic |
|---|---|---|
| AR(p) | Momentum / mean-reversion | PACF cuts off at lag p |
| I(d) | Non-stationary trend | ADF / KPSS test |
| MA(q) | Short-lived shocks | ACF cuts off at lag q |

```python
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

# Check stationarity
adf_stat, p_value, *_ = adfuller(y)
print(f"ADF p-value: {p_value:.4f}")  # > 0.05 → non-stationary, difference

# Fit ARIMA(2, 1, 2)
model = ARIMA(y, order=(2, 1, 2))
fit = model.fit()
print(fit.summary())
forecast = fit.forecast(steps=30)
```

<div class="tip-box" markdown>
**Interviewer tip:** "How do you pick p, d, q?" — ADF/KPSS for $d$, then look at ACF (for q) and PACF (for p) of the differenced series. Or use `auto_arima` (pmdarima) with AIC minimization — but explain you'd sanity-check residuals (Ljung-Box) before trusting it.
</div>

---

## Q87. SARIMA, SARIMAX — when and how { #q87 }

<span class="q-badge">Applied</span>

**SARIMA(p,d,q)(P,D,Q)$_m$** adds seasonal AR, seasonal differencing, seasonal MA at period $m$.

$$\phi(B)\Phi(B^m)(1-B)^d(1-B^m)^D y_t = \theta(B)\Theta(B^m)\epsilon_t$$

- $m$ = seasonal period (12 for monthly-with-yearly, 7 for daily-with-weekly, 24 for hourly-with-daily)
- $(P, D, Q)$ = seasonal orders

**SARIMAX** adds exogenous regressors $X_t$ (promotions, holidays, price, weather).

```python
from statsmodels.tsa.statespace.sarimax import SARIMAX

# Monthly sales with yearly seasonality, promo flag as exogenous
model = SARIMAX(y, exog=promo_flag,
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 12))
fit = model.fit(disp=False)
forecast = fit.forecast(steps=12, exog=future_promo)
```

| Scenario | Model |
|---|---|
| Monthly retail sales w/ Christmas peak | SARIMA(1,1,1)(1,1,1)₁₂ |
| Daily web traffic w/ weekly pattern | SARIMA(p,d,q)(P,D,Q)₇ |
| Sales + promo + price | SARIMAX w/ exog |
| Multiple seasonalities (weekly + yearly) | Fourier terms in SARIMAX, or Prophet |

<div class="scenario" markdown>
**Scenario:** Retail client wants 13-week forecast per SKU-store. ARIMA fits each series, but 50,000 series makes it slow.<br>
**Answer:** Three options — (1) hierarchical reconciliation with ARIMA at top level, (2) single global LightGBM with SKU/store as features, (3) cluster similar SKUs, fit one ARIMA per cluster. In practice, global ML models win on accuracy + throughput once you have ≥1k series; ARIMA wins for <100 high-value series with explanation needs.
</div>

---

## Q88. Stationarity — what, why, how to test { #q88 }

<span class="q-badge">Conceptual</span>

**Weak stationarity**: mean, variance, and autocovariance do not depend on time.

**Why ARIMA cares**: the ARMA representation assumes a time-invariant process. Fit ARMA on a trending series and the model thinks "next value = last value + drift" forever — forecasts explode or drift badly.

**Tests** (run both, they ask opposite questions):

| Test | Null hypothesis | Reject → |
|---|---|---|
| **ADF (Augmented Dickey-Fuller)** | Series has unit root (non-stationary) | Stationary |
| **KPSS** | Series is stationary | Non-stationary |

**Both agree stationary**: $d = 0$. **Both non-stationary**: difference and retest. **Disagree**: possible structural break or deterministic trend — investigate.

```python
from statsmodels.tsa.stattools import adfuller, kpss

# ADF: small p-value (<0.05) → stationary
print("ADF p-value:", adfuller(y)[1])
# KPSS: small p-value → NON-stationary (opposite!)
print("KPSS p-value:", kpss(y, regression='c')[1])

# If non-stationary, difference once and retry
y_diff = y.diff().dropna()
```

**Variance non-stationarity** (increasing variance over time) → log or Box-Cox transform before differencing.

<div class="tip-box" markdown>
**Gotcha:** ADF has low power on short series (<100 obs) and series close to unit root. Don't rely on p-values alone — also plot the series, ACF, and rolling statistics.
</div>

---

## Q89. Interpret ACF and PACF — the Box-Jenkins method { #q89 }

<span class="q-badge">Conceptual</span>

- **ACF(k)** = correlation between $y_t$ and $y_{t-k}$ (direct + indirect effects).
- **PACF(k)** = correlation between $y_t$ and $y_{t-k}$ **after removing** effects of intermediate lags.

**Identifying orders** (after differencing to stationarity):

| Pattern | Interpretation |
|---|---|
| ACF decays gradually, PACF cuts off at lag p | **AR(p)** |
| ACF cuts off at lag q, PACF decays gradually | **MA(q)** |
| Both decay gradually | **ARMA(p, q)** — use info criteria |
| ACF has spikes at seasonal lags | Seasonal component needed |

```python
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(14, 4))
plot_acf(y_diff, lags=40, ax=axes[0])
plot_pacf(y_diff, lags=40, ax=axes[1])
```

**Bounds**: values inside the blue band (~$\pm 2/\sqrt{n}$) are not statistically different from zero.

<div class="tip-box" markdown>
**Interviewer tip:** If asked "how do you pick p and q from these plots?", show the PACF-cutoff / ACF-cutoff heuristic but acknowledge it's fuzzy in practice — modern workflow is grid-search AIC/BIC over $(p,d,q)$ and verify residuals are white noise (Ljung-Box p > 0.05).
</div>

---

## Q90. Exponential smoothing — simple, Holt, Holt-Winters { #q90 }

<span class="q-badge">Classical</span>

Weighted average where recent obs matter more. Three versions:

**Simple (SES)** — level only, no trend/seasonality:

$$\hat{y}_{t+1} = \alpha y_t + (1 - \alpha) \hat{y}_t, \quad \alpha \in [0, 1]$$

**Holt's linear** — level + trend:

$$\ell_t = \alpha y_t + (1-\alpha)(\ell_{t-1} + b_{t-1})$$
$$b_t = \beta(\ell_t - \ell_{t-1}) + (1-\beta) b_{t-1}$$

**Holt-Winters** — level + trend + seasonality (additive or multiplicative):

$$\ell_t = \alpha (y_t - s_{t-m}) + (1-\alpha)(\ell_{t-1} + b_{t-1})$$
$$b_t = \beta(\ell_t - \ell_{t-1}) + (1-\beta) b_{t-1}$$
$$s_t = \gamma (y_t - \ell_t) + (1-\gamma) s_{t-m}$$

```python
from statsmodels.tsa.holtwinters import ExponentialSmoothing

model = ExponentialSmoothing(
    y, trend='add', seasonal='add', seasonal_periods=12
).fit()
forecast = model.forecast(12)
```

| When to use | Choose |
|---|---|
| No trend, no seasonality | SES |
| Trend, no seasonality | Holt |
| Trend + seasonality | Holt-Winters |
| Multiplicative seasonality (seasonality grows with level) | HW multiplicative |

<div class="scenario" markdown>
**Scenario:** Monthly iPhone unit sales have a clear yearly cycle (Q4 peak) and the peak grows every year.<br>
**Answer:** Holt-Winters with **multiplicative seasonality** — additive would under-forecast the peaks as the level grows. Alternative: log-transform then use additive HW.
</div>

---

## Q91. State-space models and the Kalman filter { #q91 }

<span class="q-badge">Conceptual • Advanced</span>

A **state-space model** represents a time series through an unobserved latent state:

$$\text{State:} \quad x_t = F x_{t-1} + w_t, \quad w_t \sim \mathcal{N}(0, Q)$$
$$\text{Observation:} \quad y_t = H x_t + v_t, \quad v_t \sim \mathcal{N}(0, R)$$

The **Kalman filter** does exact Bayesian inference for this linear-Gaussian case in closed form, producing:

- **Filtered state** $p(x_t \mid y_{1:t})$: best guess given past + current
- **Smoothed state** $p(x_t \mid y_{1:T})$: best guess given full series
- **One-step-ahead prediction** $p(y_{t+1} \mid y_{1:t})$

**Why it's powerful**:

1. ARIMA, exponential smoothing, local linear trend all have state-space forms → unified framework.
2. Handles **missing observations** naturally (just skip the update step).
3. Handles **time-varying parameters** via augmented state.
4. Gives **forecast uncertainty** (covariance of predictive distribution).

```python
from statsmodels.tsa.statespace.structural import UnobservedComponents

# Local linear trend + seasonal(12) + AR(1) cycle
model = UnobservedComponents(
    y, level='local linear trend',
    seasonal=12, autoregressive=1
)
fit = model.fit(disp=False)
# Decompose into level, trend, seasonal, AR components
fit.plot_components()
```

**Extensions**: Extended KF (nonlinear Gaussian), Unscented KF (highly nonlinear), Particle Filter (non-Gaussian).

<div class="tip-box" markdown>
**Interviewer tip:** Mention that the Kalman filter is optimal (MMSE) when assumptions hold (linear dynamics, Gaussian noise). Real systems violate this → particle filters. Also connects to LQG control and SLAM in robotics — name-drop if the role touches those.
</div>

---

## Q92. Facebook Prophet — how it works, when to use { #q92 }

<span class="q-badge">Applied</span>

Prophet is a **decomposable additive model**:

$$y(t) = g(t) + s(t) + h(t) + \epsilon_t$$

- $g(t)$: **trend** — piecewise linear or logistic growth with automatic changepoints.
- $s(t)$: **seasonality** — Fourier series (weekly + yearly, or custom).
- $h(t)$: **holidays** — user-provided indicator list.
- $\epsilon_t$: Gaussian noise.

Fit via Bayesian MAP in Stan; gives uncertainty intervals via MCMC or analytic approximation.

```python
from prophet import Prophet
import pandas as pd

# Prophet expects columns 'ds' (datestamp) and 'y'
df = pd.DataFrame({'ds': dates, 'y': values})

m = Prophet(yearly_seasonality=True, weekly_seasonality=True,
            changepoint_prior_scale=0.05)
m.add_country_holidays(country_name='US')
m.fit(df)

future = m.make_future_dataframe(periods=90)
forecast = m.predict(future)
m.plot(forecast)
m.plot_components(forecast)  # trend, weekly, yearly, holidays
```

| Strengths | Weaknesses |
|---|---|
| Handles missing data, outliers, holidays natively | Slow on 10k+ series |
| Interpretable decomposition | Doesn't model AR residuals → can miss short-term dynamics |
| Intuitive hyperparameters (`changepoint_prior_scale`, `seasonality_prior_scale`) | Tends to over-smooth |
| Uncertainty intervals out of the box | Not for high-frequency (sub-daily) |

<div class="scenario" markdown>
**Scenario:** "Prophet has fallen out of favor in 2026 — why?"<br>
**Answer:** Accuracy competitions (M4, M5) showed global ML models (LightGBM, N-BEATS, TFT) beat Prophet on most real datasets. Prophet is still good when you need **automatic holiday/changepoint handling + interpretability** for a few series, or as a quick baseline. For scale or accuracy, move to global ML.
</div>

---

## Q93. ARCH and GARCH — volatility modeling { #q93 }

<span class="q-badge">Finance</span>

ARIMA models the **mean** of a series, assuming constant variance. Financial returns have **volatility clustering** — variance itself is autocorrelated (quiet periods, then big moves cluster). ARCH/GARCH model the variance.

**ARCH(q)** — variance depends on past squared shocks:

$$\sigma_t^2 = \alpha_0 + \sum_{i=1}^{q} \alpha_i \epsilon_{t-i}^2$$

**GARCH(p, q)** — adds persistence via past variances:

$$\sigma_t^2 = \alpha_0 + \sum_{i=1}^{q} \alpha_i \epsilon_{t-i}^2 + \sum_{j=1}^{p} \beta_j \sigma_{t-j}^2$$

Returns modeled as $r_t = \mu + \epsilon_t$ where $\epsilon_t = \sigma_t z_t$, $z_t \sim \mathcal{N}(0, 1)$.

```python
from arch import arch_model

# Fit GARCH(1, 1) to daily log returns
model = arch_model(returns, vol='Garch', p=1, q=1, dist='normal')
fit = model.fit(disp='off')
print(fit.summary())

# Forecast next 10 days of volatility
forecasts = fit.forecast(horizon=10)
```

**Variants**: EGARCH (asymmetric — negative shocks raise volatility more), GJR-GARCH (threshold), TGARCH.

| Use for | Avoid for |
|---|---|
| Value-at-Risk (VaR) | Price forecasting (you're forecasting variance, not direction) |
| Option pricing with stochastic vol | Low-frequency data with constant variance |
| Risk parity portfolios | Series where variance really is constant |

<div class="tip-box" markdown>
**Interviewer tip:** If you interview for quant roles, know that $\alpha + \beta < 1$ is required for stationarity of variance; $\alpha + \beta$ close to 1 means volatility is highly persistent (IGARCH limit).
</div>

---

## Q94. Time series cross-validation — why k-fold fails { #q94 }

<span class="q-badge">Practical</span>

**Standard k-fold CV leaks the future into the past** — if fold 1's training set includes 2024 data and its test set is 2023, the model is impossibly "prescient". This inflates metrics dramatically.

**Three correct approaches:**

**1. Expanding window (walk-forward):**
```
Train: [1, ..., T₁]         Test: [T₁+1, ..., T₁+h]
Train: [1, ..., T₂]         Test: [T₂+1, ..., T₂+h]
Train: [1, ..., T₃]         Test: [T₃+1, ..., T₃+h]
```

**2. Sliding window (rolling origin):**
```
Train: [1, ..., T₁]                 Test: [T₁+1, ..., T₁+h]
Train: [d+1, ..., T₂]               Test: [T₂+1, ..., T₂+h]
```

**3. Blocked CV with gap**: leave a gap between train and test equal to the forecast horizon or autocorrelation length to avoid leakage from lagged features.

```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5, test_size=30, gap=7)
for train_idx, test_idx in tscv.split(X):
    model.fit(X[train_idx], y[train_idx])
    score = model.score(X[test_idx], y[test_idx])
```

**Metric choice**: report **horizon-wise** metrics (day-1 RMSE, day-7 RMSE, day-30 RMSE), not just aggregate — error typically grows with horizon.

<div class="scenario" markdown>
**Scenario:** Team's model has 0.03 MAPE on backtest but 0.18 in production.<br>
**Answer:** Four common leaks: (1) random k-fold CV, (2) rolling statistics (mean, std) computed on the full series before split, (3) target-encoded categorical using full-series target, (4) lag features leaking future rows during train/test construction. Audit the entire pipeline for any operation that touches the future.
</div>

---

## Q95. VAR — vector autoregression for multivariate series { #q95 }

<span class="q-badge">Multivariate</span>

When multiple series affect each other (unemployment + inflation + GDP), use **VAR(p)**:

$$\mathbf{y}_t = c + A_1 \mathbf{y}_{t-1} + \cdots + A_p \mathbf{y}_{t-p} + \boldsymbol\epsilon_t$$

Each variable is regressed on past values of itself **and every other variable**. Parameters: $k^2 p$ for $k$ series, lag $p$ — grows fast.

```python
from statsmodels.tsa.api import VAR

# df has columns: gdp, cpi, unemployment
model = VAR(df)
# Info criteria select lag length
lag_order = model.select_order(maxlags=12).aic
fit = model.fit(lag_order)

# Forecast next 4 quarters
forecast = fit.forecast(df.values[-lag_order:], steps=4)
```

**Analysis beyond forecasting:**

- **Granger causality**: does $y_j$ help predict $y_i$ beyond $y_i$'s own past?
- **Impulse response functions (IRFs)**: how does a shock to variable $j$ propagate to variable $i$ over time?
- **Variance decomposition**: what fraction of $y_i$'s forecast variance comes from shocks to $y_j$?

**Extensions**:

- **VECM** (Vector Error Correction): for cointegrated non-stationary series (keep long-run relationship while differencing).
- **Structural VAR (SVAR)**: adds economic identifying restrictions to interpret shocks.

<div class="tip-box" markdown>
**Interviewer gotcha:** Granger causality ≠ real causality. It only means lagged $y_j$ has predictive value for $y_i$ beyond $y_i$'s own lags — a common confounder could drive both.
</div>

---

## Q96. Global ML models for forecasting (LightGBM for time series) { #q96 }

<span class="q-badge">Modern</span>

**M5 competition (2020)**: top solutions were **LightGBM globally trained over all 30k series**, not per-series ARIMA. This is now the default industrial approach.

**Key feature-engineering patterns:**

| Feature | Example |
|---|---|
| Lags | `y_lag_1`, `y_lag_7`, `y_lag_28` |
| Rolling stats | `y_roll_mean_7`, `y_roll_std_28`, `y_roll_max_7` |
| Date parts | dayofweek, month, weekofyear, is_holiday |
| Fourier terms | `sin(2π·t/365)`, `cos(2π·t/365)` |
| Series ID | SKU, store (as categorical) |
| Price, promo, weather | Exogenous |
| Target encoding | Mean sales by (store, dayofweek) |
| Event indicators | Black Friday, end-of-month |

```python
import lightgbm as lgb
import pandas as pd

df['y_lag7'] = df.groupby('sku')['y'].shift(7)
df['y_roll_mean_28'] = df.groupby('sku')['y'].shift(1).rolling(28).mean()
df['dayofweek'] = df['date'].dt.dayofweek

features = ['y_lag7', 'y_roll_mean_28', 'dayofweek', 'price', 'promo', 'sku']
model = lgb.LGBMRegressor(
    objective='tweedie',     # for count/intermittent demand
    n_estimators=2000,
    learning_rate=0.03,
    num_leaves=127,
    categorical_feature=['sku']
).fit(df_train[features], df_train['y'],
      eval_set=[(df_val[features], df_val['y'])],
      callbacks=[lgb.early_stopping(50)])
```

**Critical: use recursive or direct multi-step strategy** for horizons > 1:

- **Recursive**: predict t+1, feed as lag, predict t+2... (compounds error, but works with one model).
- **Direct**: train separate model per horizon (no error compounding, but more models).
- **DirRec / hybrid**: often best in practice.

<div class="scenario" markdown>
**Scenario:** 50k SKUs, 3 years daily, forecast 28 days. How would you build it?<br>
**Answer:** Global LightGBM with Tweedie objective (handles zeros in intermittent demand), lag + rolling features, SKU/category/store as categoricals, direct multi-step (28 models) or single recursive. Validate with 5-fold expanding-window CV on most recent 6 months, report per-horizon WMAPE. Compare against a naive seasonal benchmark (last-year-same-week) — if you don't beat it, something's wrong.
</div>

---

## Q97. N-BEATS, N-HiTS, TFT — modern deep forecasting { #q97 }

<span class="q-badge">Deep Learning</span>

**N-BEATS** (2019, Oreshkin et al.):

- Stack of fully-connected blocks, each outputting a **backcast** (reconstruct history) and **forecast** (future).
- Doubly-residual: next block works on backcast residuals.
- Two variants: **generic** (interpretable-agnostic) and **interpretable** (trend + seasonality basis).
- No recurrence, no attention — just MLPs. Beat every statistical method in M4.

**N-HiTS** (2022): N-BEATS with hierarchical multi-rate sampling. Faster and more accurate for long horizons.

**Temporal Fusion Transformer (TFT)** (Google, 2020):

- Handles static covariates + known-future covariates (calendar, planned promos) + observed covariates (past weather).
- LSTM encoder + multi-head attention + gating.
- **Quantile outputs** (P10/P50/P90) natively → probabilistic forecasts.
- Interpretable variable importance and attention weights.

```python
# PyTorch-Forecasting is the standard TFT implementation
from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet

training = TimeSeriesDataSet(
    df_train, time_idx="time_idx", target="sales",
    group_ids=["sku"], max_encoder_length=90, max_prediction_length=28,
    static_categoricals=["sku", "category"],
    time_varying_known_reals=["price", "promo"],
    time_varying_unknown_reals=["sales"],
)

tft = TemporalFusionTransformer.from_dataset(training, hidden_size=64,
                                             attention_head_size=4,
                                             dropout=0.1, loss=QuantileLoss())
```

| Model | Best for |
|---|---|
| **N-BEATS** | Pure univariate, high-accuracy benchmark |
| **N-HiTS** | Long horizons (hundreds of steps) |
| **TFT** | Multivariate with rich static + future covariates, need interpretability |
| **DeepAR** | Probabilistic, many related series, cold-start new series |
| **PatchTST / Autoformer** | 2023+ transformers; long horizons, efficient |

<div class="tip-box" markdown>
**Interviewer tip:** In 2026 the "do I need deep learning?" answer is still **it depends**. LightGBM with well-engineered features beats deep models on many tabular forecasting problems when series are < 1000. Deep models pull ahead at scale (10k+ series) and with heterogeneous covariates.
</div>

---

## Q98. Probabilistic forecasting — why point forecasts aren't enough { #q98 }

<span class="q-badge">Advanced</span>

A point forecast tells you one number. **Real business decisions need distributions** — "what's the 95th percentile demand so I don't stock out?" "what's the probability we exceed capacity?"

**Ways to produce probabilistic forecasts:**

| Method | Approach |
|---|---|
| **Quantile regression** | Predict P10, P50, P90 directly via pinball loss |
| **Conformal prediction** | Distribution-free intervals using calibration residuals |
| **MC Dropout / deep ensembles** | Aggregate multiple stochastic forward passes |
| **Bayesian models** | Posterior predictive distribution (Prophet, BSTS) |
| **DeepAR** | Parametric output (Gaussian, NegBin) with autoregressive sampling |
| **Bootstrap residuals** | Add resampled past errors to point forecast |

**Evaluation metrics** (point metrics like RMSE don't work for distributions):

- **Pinball loss** (for quantile forecasts): $L_\tau(y, q) = \max(\tau(y-q), (\tau-1)(y-q))$
- **CRPS (Continuous Ranked Probability Score)**: generalizes pinball across all quantiles.
- **Coverage**: fraction of actuals inside the 90% interval — should be ~90%.
- **Interval width**: narrower is better (conditional on correct coverage).

```python
# Quantile LightGBM - train one model per quantile
from lightgbm import LGBMRegressor

models = {}
for q in [0.1, 0.5, 0.9]:
    models[q] = LGBMRegressor(objective='quantile', alpha=q,
                              n_estimators=500).fit(X_train, y_train)

p10 = models[0.1].predict(X_test)
p50 = models[0.5].predict(X_test)
p90 = models[0.9].predict(X_test)
```

<div class="scenario" markdown>
**Scenario:** Inventory planner wants to decide safety stock. Point forecast is 100 units, with P90 = 140.<br>
**Answer:** Safety stock should be based on the **forecast distribution + service-level target**. If target is 95% service level, stock up to the P95 of demand. This is impossible with only a point forecast — hence probabilistic forecasting is essential for inventory/capacity/pricing decisions.
</div>

---

## Q99. Anomaly detection in time series { #q99 }

<span class="q-badge">Applied</span>

**Categories:**

1. **Point anomalies** — single observation far from expected.
2. **Contextual anomalies** — normal in general, abnormal for the context (high sales are normal; high sales on Tuesday aren't).
3. **Collective anomalies** — subsequence is abnormal though each point looks fine (heart arrhythmia).

**Common methods:**

| Method | Detects | Notes |
|---|---|---|
| **Z-score / rolling Z** | Points | Assumes Gaussian, fails with trend/seasonality |
| **Seasonal decomposition (STL) + residual Z** | Points after removing trend/seasonal | Classic, still strong |
| **ARIMA forecast residuals** | Points | Flag residuals > 3σ |
| **Prophet intervals** | Points | Flag obs outside prediction interval |
| **Isolation Forest on windowed features** | Points + collective | Flexible, works on features |
| **LSTM autoencoder reconstruction error** | Subsequences | Deep, needs lots of normal data |
| **Matrix Profile (STUMPY)** | Collective (motifs/discords) | Non-parametric, no training, excellent |

```python
import stumpy
import numpy as np

# Window size m, chosen based on expected anomaly length
mp = stumpy.stump(y, m=100)
# Highest values in mp[:, 0] are the "discords" (most anomalous subsequences)
anomaly_idx = np.argsort(mp[:, 0])[-5:]
```

**Evaluation** is hard — anomalies are rare and often unlabeled.

- Precision/recall if labels exist.
- **Range-based F1** (Tatbul et al.) accounts for partial detection of extended events.
- Manual review + domain expert to establish ground truth.

<div class="tip-box" markdown>
**Interviewer tip:** Ask about the **cost of false positives vs false negatives** before picking a threshold. Credit card fraud: false positives annoy customers but missed fraud costs real money. Manufacturing: missed defects can mean recalls.
</div>

---

## Q100. Decomposition — STL, MSTL, and how to read a decomposition { #q100 }

<span class="q-badge">Diagnostic</span>

**STL (Seasonal-Trend decomposition using LOESS)** splits a series into:

$$y_t = T_t + S_t + R_t$$

- $T_t$ = trend (low-frequency, LOESS smooth)
- $S_t$ = seasonal (repeating at period $m$)
- $R_t$ = remainder (what's left after removing trend + seasonal)

**MSTL** extends STL to multiple seasonal periods (e.g., weekly + yearly together).

```python
from statsmodels.tsa.seasonal import STL, MSTL

# Single seasonality
res = STL(y, period=12, robust=True).fit()
res.plot()

# Multiple seasonalities (weekly + yearly for daily data)
res = MSTL(y, periods=(7, 365)).fit()
res.plot()
```

**How to read a decomposition** (interview gold):

| Check | Means |
|---|---|
| Trend is flat | No long-run drift; differencing may not be needed |
| Trend has sharp changes | Structural breaks — consider changepoint models |
| Seasonal amplitude grows with level | Multiplicative seasonality — log-transform first |
| Remainder has autocorrelation | More signal to extract — try ARMA on remainder |
| Remainder has increasing variance | Heteroscedasticity — Box-Cox transform |
| Remainder has outliers | Flag for anomaly detection |

<div class="scenario" markdown>
**Scenario:** Product analytics lead asks: "Did last quarter's dip come from the promo-end or was it a trend shift?"<br>
**Answer:** Run STL decomposition. If the dip shows up entirely in the **seasonal component's expected trough** → no anomaly. If it shows in the **trend**, there's a real slowdown. If in the **remainder**, it's a one-off event (and worth investigating). This separates "explained by pattern" from "new information" — a conversation that's otherwise hand-wavy.
</div>

---

## ✅ Module Recap

- Classical stack: **ARIMA → SARIMA → SARIMAX** for interpretable low-volume forecasting.
- Always check **stationarity** (ADF + KPSS) and **residuals** (Ljung-Box) before trusting a model.
- **Time series CV** must never mix future into past. Use expanding or sliding window.
- **Global ML models (LightGBM)** dominate at scale; **N-BEATS/TFT** for long horizons and rich covariates.
- **Probabilistic forecasts** beat point forecasts for decision-making — pinball loss, conformal, quantile regression.
- **Decomposition (STL/MSTL)** is a free diagnostic — run it before modeling anything.

→ Next: [🛒 Recommenders & Specialty](recommenders.md)
