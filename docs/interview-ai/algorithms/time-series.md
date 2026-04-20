# Module 6 — Time Series

Fifteen questions covering classical and modern approaches to time series — the kind of questions that trip up candidates who've only studied i.i.d. data. Temporal dependencies break most of what you learned in ML-101.

---

## Q96. What makes time series fundamentally different from tabular data? { #q96 }

Five critical differences:

1. **Observations are not independent.** Today's value depends on yesterday's. The i.i.d. assumption behind most ML is violated.

2. **Order matters.** You can't shuffle rows. Random train/test splits cause **leakage** — testing on data from *before* your training data violates causality.

3. **Distributions shift over time.** The process generating data in 2020 isn't the same as 2026 (concept drift, trend, regime change).

4. **Autocorrelation.** A time series' own past values are often the strongest predictors — more than any exogenous feature.

5. **Seasonality.** Daily, weekly, yearly, holiday cycles create patterns that need explicit modeling.

**Consequences for modeling:**

- Always use **time-based splits**: train on past, validate on future.
- Use **walk-forward / expanding-window cross-validation**, not standard K-fold.
- Lag features, rolling statistics, and Fourier features are essential.
- Classical time-series methods (ARIMA, exponential smoothing) often beat ML for short horizons on univariate series.

---

## Q97. Define stationarity. Why does it matter? { #q97 }

**Strict stationarity:** The joint distribution of any set of observations doesn't depend on time.

**Weak (second-order) stationarity:** Mean, variance, and autocovariance are constant over time.

**Why it matters:** Most classical time series models (AR, MA, ARIMA) **require** stationarity. A non-stationary series has changing statistical properties → model parameters won't generalize.

**Testing for stationarity:**

- **Augmented Dickey-Fuller (ADF)** test: null hypothesis = series has a unit root (non-stationary). Low p-value → stationary.
- **KPSS test:** null hypothesis = stationary. Complement to ADF.
- **Visual check:** Plot the series. Trend? Changing variance? Not stationary.

```python
from statsmodels.tsa.stattools import adfuller, kpss

adf_stat, p_value, *_ = adfuller(series)
print(f"ADF p-value: {p_value:.4f}")  # < 0.05 → stationary

kpss_stat, p_value, *_ = kpss(series)
print(f"KPSS p-value: {p_value:.4f}")  # > 0.05 → stationary
```

**Making a series stationary:**

- **Differencing:** $\Delta y_t = y_t - y_{t-1}$. Removes trend.
- **Seasonal differencing:** $y_t - y_{t-s}$. Removes seasonality.
- **Log transform:** Stabilizes variance when variance grows with level.
- **Box-Cox transform:** Generalization of log for positive data.

---

## Q98. Explain ARIMA. What do the three parameters mean? { #q98 }

**ARIMA(p, d, q):**

- **AR(p) — AutoRegressive:** Linear combination of $p$ past values.
  $$
  y_t = c + \phi_1 y_{t-1} + \dots + \phi_p y_{t-p} + \varepsilon_t
  $$
- **I(d) — Integrated:** $d$ orders of differencing applied to make the series stationary.
  $$
  \Delta^d y_t
  $$
- **MA(q) — Moving Average:** Linear combination of $q$ past forecast errors.
  $$
  y_t = c + \varepsilon_t + \theta_1 \varepsilon_{t-1} + \dots + \theta_q \varepsilon_{t-q}
  $$

Combined:

$$
\phi(B)(1-B)^d y_t = c + \theta(B) \varepsilon_t
$$

where $B$ is the backshift operator ($B y_t = y_{t-1}$).

**Choosing p, d, q:**

- **d**: smallest integer that makes the series stationary (usually 0, 1, or 2).
- **p**: examine the PACF plot — cutoff at lag $p$.
- **q**: examine the ACF plot — cutoff at lag $q$.

**SARIMA:** Adds seasonal components $(P, D, Q, s)$ for seasonality of period $s$.

```python
from statsmodels.tsa.statespace.sarimax import SARIMAX

model = SARIMAX(
    y,
    order=(2, 1, 2),
    seasonal_order=(1, 1, 1, 12)  # monthly seasonality
).fit()

forecast = model.forecast(steps=12)
```

**Auto-ARIMA:** grid searches over $(p, d, q)$ minimizing AIC.

```python
from pmdarima import auto_arima
model = auto_arima(y, seasonal=True, m=12, stepwise=True).fit(y)
```

---

## Q99. Explain ACF and PACF. How do they help choose ARIMA parameters? { #q99 }

**ACF (AutoCorrelation Function):** Correlation of $y_t$ with $y_{t-k}$ — includes effects of intermediate lags.

**PACF (Partial AutoCorrelation Function):** Correlation of $y_t$ with $y_{t-k}$ after **removing** the effects of lags $1, 2, \dots, k-1$.

**Identification rules:**

| Process | ACF | PACF |
|---|---|---|
| AR(p) | Decays gradually | Cuts off after lag $p$ |
| MA(q) | Cuts off after lag $q$ | Decays gradually |
| ARMA(p,q) | Decays after $q$ | Decays after $p$ |

**Practical use:**

1. Plot both ACF and PACF of the differenced (stationary) series.
2. If PACF cuts off at lag $k$ and ACF decays → AR(k).
3. If ACF cuts off at lag $k$ and PACF decays → MA(k).
4. If both decay → ARMA, try small p, q and compare by AIC.

```python
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

import matplotlib.pyplot as plt
fig, axes = plt.subplots(2, 1, figsize=(10, 6))
plot_acf(series.diff().dropna(), lags=30, ax=axes[0])
plot_pacf(series.diff().dropna(), lags=30, ax=axes[1])
```

---

## Q100. Explain Exponential Smoothing (ETS models). { #q100 }

**Simple Exponential Smoothing** (for stationary series, no trend or seasonality):

$$
\hat{y}_{t+1} = \alpha y_t + (1-\alpha) \hat{y}_t
$$

The forecast is a weighted average of past observations, with weights decaying exponentially.

**Holt's linear method** (adds trend):

$$
\ell_t = \alpha y_t + (1-\alpha)(\ell_{t-1} + b_{t-1})
$$
$$
b_t = \beta(\ell_t - \ell_{t-1}) + (1-\beta) b_{t-1}
$$
$$
\hat{y}_{t+h} = \ell_t + h \cdot b_t
$$

**Holt-Winters** (adds seasonality): Additional seasonal component $s_t$, either additive or multiplicative.

**ETS framework:** Error × Trend × Seasonal components:

- Error: Additive (A) or Multiplicative (M).
- Trend: None (N), Additive (A), Additive damped (Ad), Multiplicative (M), Multiplicative damped (Md).
- Seasonal: None (N), Additive (A), Multiplicative (M).

E.g., `ETS(A,A,A)` = additive error, additive trend, additive seasonality.

```python
from statsmodels.tsa.holtwinters import ExponentialSmoothing

model = ExponentialSmoothing(
    y,
    trend='add',
    seasonal='mul',
    seasonal_periods=12,
    damped_trend=True
).fit()

forecast = model.forecast(24)
```

**When ETS wins over ARIMA:**

- Short series where ARIMA overfits.
- Strong, clean seasonality.
- When automated forecasting at scale is needed (ETS is very robust).

---

## Q101. Explain Facebook Prophet. What are its strengths and weaknesses? { #q101 }

**Prophet's model:**

$$
y(t) = g(t) + s(t) + h(t) + \varepsilon_t
$$

- $g(t)$: piecewise linear or logistic trend with automatic changepoint detection.
- $s(t)$: seasonal components (Fourier series for yearly, weekly, daily).
- $h(t)$: holiday effects.
- $\varepsilon_t$: noise.

Fit via STAN (Bayesian inference) or L-BFGS (MAP estimation).

**Strengths:**

- **Robust to missing data and outliers.**
- **Handles holidays natively** (plug in country holidays).
- **Good defaults** — often works out of the box.
- **Uncertainty intervals** built in.
- **Interpretable components** (plot trend, seasonality, holidays separately).

**Weaknesses:**

- **Univariate only by default.** Adding regressors is possible but clunky.
- **Overestimates trend changes.** Many false changepoints.
- **Can produce unreasonable forecasts** (e.g., extrapolating linear trends indefinitely) — use `cap` for logistic growth.
- **Slow on many short series** (fit one model per series).

**When to use:**

- Forecasting with strong seasonality + holidays (retail, web traffic).
- Quick baseline before investing in a custom model.
- Business analyst teams needing an accessible tool.

```python
from prophet import Prophet

df = pd.DataFrame({'ds': dates, 'y': values})
model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False,
    changepoint_prior_scale=0.05
)
model.add_country_holidays(country_name='US')
model.fit(df)

future = model.make_future_dataframe(periods=90)
forecast = model.predict(future)
```

---

## Q102. How do you cross-validate time series models? { #q102 }

**Standard K-fold is WRONG for time series** — it leaks future information into training.

**Correct methods:**

**1. Expanding window (most common):**

```
Fold 1: Train [1..100], Test [101..110]
Fold 2: Train [1..110], Test [111..120]
Fold 3: Train [1..120], Test [121..130]
```

Training set grows; model re-fit each fold.

**2. Rolling window:**

```
Fold 1: Train [1..100],  Test [101..110]
Fold 2: Train [11..110], Test [111..120]
Fold 3: Train [21..120], Test [121..130]
```

Training window is fixed size.

**3. Blocked CV (when no auto-correlation):** Split into contiguous blocks, hold one out.

```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5, test_size=30, gap=7)
# gap=7 leaves a 7-point buffer between train and test to avoid leakage

for train_idx, test_idx in tscv.split(X):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    # fit and evaluate
```

**Walk-forward validation** is more realistic:

- Train on all data up to time $t$.
- Predict $t+1$.
- Add actual $t+1$ to training.
- Repeat.

This simulates what will happen in production and is the strongest validation.

<div class="tip-box" markdown>
**Gotcha:** If using lag features, ensure the lag window doesn't cross into the test set. A simple `lag_1` feature for a row in the test set must come from the last training-set row, not itself.
</div>

---

## Q103. What metrics should you use for time series forecasting? { #q103 }

| Metric | Formula | Properties |
|---|---|---|
| **MAE** | $\frac{1}{n}\sum\|y - \hat{y}\|$ | Robust to outliers, same unit as target |
| **MSE / RMSE** | $\frac{1}{n}\sum (y-\hat{y})^2$ | Penalizes large errors more |
| **MAPE** | $\frac{100}{n}\sum \frac{\|y-\hat{y}\|}{\|y\|}$ | Scale-free %, but fails at $y=0$ |
| **sMAPE** | $\frac{200}{n}\sum \frac{\|y-\hat{y}\|}{\|y\|+\|\hat{y}\|}$ | Symmetric version, bounded [0, 200%] |
| **MASE** | MAE / MAE of naive seasonal forecast | Scale-free, > 1 = worse than naive |
| **R²** | $1 - \frac{SS_{res}}{SS_{tot}}$ | Familiar, but misleading for time series |
| **Pinball loss** | For quantile forecasts | Use when uncertainty matters |

**Choice by situation:**

- **Comparing models on same series:** RMSE or MAE.
- **Comparing across series with different scales:** MASE or sMAPE.
- **Demand forecasting:** MAE (penalties for over/under-stock are roughly linear).
- **Financial / risk forecasting:** Pinball loss at risk quantiles.

**Always compare against a naive baseline:**

- Naive: $\hat{y}_{t+1} = y_t$.
- Seasonal naive: $\hat{y}_{t+1} = y_{t+1-s}$.

If your model doesn't beat the seasonal naive, don't ship it.

```python
from sklearn.metrics import mean_absolute_error, mean_squared_error

mae = mean_absolute_error(y_true, y_pred)
rmse = np.sqrt(mean_squared_error(y_true, y_pred))

# MAPE handles zero with small epsilon
mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100

# MASE (scale by naive)
naive_mae = np.mean(np.abs(np.diff(y_train)))
mase = mae / naive_mae
```

---

## Q104. How do you create lag features for time series ML? { #q104 }

**Lag features** turn a time series into a tabular problem that standard ML can handle.

**Types:**

1. **Raw lags:** $y_{t-1}, y_{t-2}, \dots, y_{t-k}$.
2. **Rolling statistics:** mean, std, min, max over the last $k$ periods.
3. **Expanding statistics:** cumulative mean, cumulative std (careful with leakage).
4. **Difference lags:** $y_{t-1} - y_{t-2}$.
5. **Seasonal lags:** $y_{t-s}$ (e.g., $y_{t-7}$ for weekly, $y_{t-365}$ for yearly).
6. **Date features:** hour, day-of-week, month, is_holiday, is_weekend.
7. **Fourier features:** $\sin(2\pi k t / T), \cos(2\pi k t / T)$ for smooth seasonality.

```python
import pandas as pd

def make_lag_features(df, target, lags=[1, 7, 14, 28], windows=[7, 28]):
    # Raw lags
    for lag in lags:
        df[f'{target}_lag_{lag}'] = df[target].shift(lag)
    # Rolling mean/std (shifted to avoid leakage)
    for w in windows:
        df[f'{target}_rmean_{w}'] = df[target].shift(1).rolling(w).mean()
        df[f'{target}_rstd_{w}'] = df[target].shift(1).rolling(w).std()
    return df

df = make_lag_features(df, 'sales')
```

**Critical leakage warning:** Always `shift(1)` before `rolling()`. `df['sales'].rolling(7).mean()` uses the current row in the window — a forward-looking error.

---

## Q105. Can you use gradient boosting for time series forecasting? { #q105 }

**Yes — and it's often state of the art for tabular time series.**

**Approach:**

1. Engineer lag features (Q104).
2. Include calendar features.
3. Include exogenous regressors (weather, promotions, holidays).
4. Train LightGBM/XGBoost on the resulting tabular problem.
5. For multi-step forecasting, choose between:
   - **Direct strategy:** One model per horizon (separate models for $t+1, t+2, \dots$).
   - **Recursive strategy:** One model; use its predictions as lag features for the next step.
   - **Multi-output:** Sklearn `MultiOutputRegressor` — one model per horizon step.

**Direct strategy code:**

```python
import lightgbm as lgb

horizons = [1, 7, 14, 28]
models = {}
for h in horizons:
    df[f'target_h{h}'] = df['sales'].shift(-h)
    # drop rows where target is NaN
    train = df.dropna(subset=[f'target_h{h}'])
    X = train[feature_cols]
    y = train[f'target_h{h}']
    models[h] = lgb.LGBMRegressor(n_estimators=500, learning_rate=0.05).fit(X, y)
```

**Tree-based strengths on time series:**

- Handles non-linear relationships between lag features and target.
- Captures interactions (sales × promotion).
- Natively deals with missing values (holidays, sensor gaps).
- Scales to many series (global model, train once).

**Tree-based weaknesses:**

- **Cannot extrapolate** (see Q34). Upward trends will plateau beyond training range.
- Less principled uncertainty quantification than classical methods.

**Fix for extrapolation:** Combine with classical trend model (trend via linear regression on time + residuals modeled by LightGBM).

---

## Q106. Explain the difference between univariate and multivariate time series. { #q106 }

**Univariate:** One variable observed over time (daily temperature).

**Multivariate:** Multiple variables observed over time, where they may influence each other (temperature + humidity + wind speed).

**Key distinction:** In multivariate modeling, you model the **joint dynamics** — past values of any variable can predict future values of any other.

**Univariate methods:** ARIMA, ETS, Prophet, simple RNN.

**Multivariate methods:**

- **VAR (Vector AutoRegression):** Each variable is a linear function of past values of all variables.
  $$
  y_t = A_1 y_{t-1} + A_2 y_{t-2} + \dots + A_p y_{t-p} + \varepsilon_t
  $$
  where $y_t \in \mathbb{R}^k$ and $A_i$ are $k \times k$ matrices.

- **VARMA, VARIMA:** Generalizations adding MA terms, differencing.

- **State space models:** Kalman filter, DLM.

- **Modern:** DeepAR, Temporal Fusion Transformer (TFT), N-BEATS with covariates.

**Granger causality test:** Does $X$ "Granger-cause" $Y$? Test if including past values of $X$ improves prediction of $Y$ beyond using past values of $Y$ alone. Useful for understanding which multivariate interactions matter.

```python
from statsmodels.tsa.api import VAR

model = VAR(endog=df[['temp', 'humidity', 'wind']]).fit(maxlags=10, ic='aic')
forecast = model.forecast(df.values[-model.k_ar:], steps=24)
```

---

## Q107. What is a state space model / Kalman filter? { #q107 }

**State space model:** A two-equation framework:

**State equation (dynamics):**

$$
x_t = F x_{t-1} + w_t, \quad w_t \sim \mathcal{N}(0, Q)
$$

**Observation equation:**

$$
y_t = H x_t + v_t, \quad v_t \sim \mathcal{N}(0, R)
$$

The *state* $x_t$ is hidden; we only observe $y_t$ (noisy measurements).

**Kalman filter:** Recursive Bayesian update. Given $y_1, \dots, y_t$:

1. **Predict:** Use $F$ to roll state forward: $\hat{x}_{t|t-1} = F \hat{x}_{t-1|t-1}$.
2. **Update:** When $y_t$ arrives, correct prediction: $\hat{x}_{t|t} = \hat{x}_{t|t-1} + K_t (y_t - H \hat{x}_{t|t-1})$.

The Kalman gain $K_t$ optimally balances model prediction vs new observation based on their respective uncertainties.

**Why it's cool:**

- Recursive — no need to store all past data.
- Provides uncertainty estimates naturally.
- Generalizes ARIMA, ETS, and many other models into one framework.
- Extends to non-linear cases (Extended Kalman, Unscented Kalman, Particle Filter).

**Applications:**

- Sensor fusion (GPS + IMU in cars/drones).
- Tracking (radar, vision).
- Econometrics (estimating unobservable latent states like "true inflation").
- Time series forecasting with structural components.

```python
from statsmodels.tsa.statespace.structural import UnobservedComponents

# Local linear trend + seasonal
model = UnobservedComponents(
    y,
    level='local linear trend',
    seasonal=12,
    stochastic_seasonal=True
).fit()

forecast = model.forecast(24)
```

---

## Q108. What are DeepAR, N-BEATS, Temporal Fusion Transformer? { #q108 }

Three modern deep learning time series models:

**DeepAR (Amazon, 2017):**

- RNN (LSTM/GRU) autoregressively predicting parameters of a likelihood (Gaussian, negative binomial).
- **Trained jointly across many related series** (e.g., thousands of product SKUs) → global model.
- Outputs probabilistic forecasts.
- Strong for retail demand forecasting.

**N-BEATS (2020):**

- Fully-connected architecture — no recurrence, no attention.
- Generates forecasts via a stack of "blocks," each producing a backcast and forecast decomposition.
- **Interpretable version** decomposes into trend and seasonality basis functions.
- **Generic version** learns basis functions end-to-end.
- Exceptional performance on benchmarks (M4 competition).

**Temporal Fusion Transformer (TFT, 2019):**

- Transformer-based, multi-horizon forecasting.
- Handles static covariates, time-varying known covariates (future promotions), and time-varying observed covariates.
- Uses attention to learn feature importance per time step.
- Outputs quantile predictions.
- Good for complex mixed-input forecasting.

**When to pick what:**

| Situation | Model |
|---|---|
| Many related short series (retail) | DeepAR |
| Univariate benchmark performance | N-BEATS |
| Mixed static + time-varying features | TFT |
| Quick baseline | LightGBM + lag features |
| Strong seasonality, small data | Prophet |

```python
# Using neuralforecast
from neuralforecast import NeuralForecast
from neuralforecast.models import NBEATS, DeepAR, TFT

models = [
    NBEATS(h=24, input_size=72, max_steps=500),
    DeepAR(h=24, input_size=72, max_steps=500),
    TFT(h=24, input_size=72, max_steps=500),
]
nf = NeuralForecast(models=models, freq='H')
nf.fit(df)
forecasts = nf.predict()
```

---

## Q109. What are the challenges of real-world time series in production? { #q109 }

Seven hard problems:

1. **Missing data and irregular sampling.** Sensors drop out; purchases are irregular. Need imputation (forward fill, interpolation, model-based) or models that handle irregularity (state space, continuous-time RNN).

2. **Cold start.** New product/customer has no history. Solutions: hierarchical models, transfer learning from similar series, use exogenous features.

3. **Concept drift.** The relationship changes — COVID broke every demand model in 2020. Monitoring + retraining cadence matters.

4. **Evaluation at multiple horizons.** Your 1-day forecast vs 30-day forecast need different metrics and models.

5. **Hierarchical reconciliation.** Forecasts at product level, store level, region level must sum consistently. Techniques: MinT reconciliation, hierarchical neural networks.

6. **Outliers and structural breaks.** One anomalous spike (promotion, recall, outage) can poison an ARIMA model. Need robust methods (Huber loss, robust regression).

7. **Forecast delivery latency.** Some applications need sub-second forecasts (ad bidding), others need end-of-day (inventory). Affects model choice.

<div class="scenario" markdown>
**Scenario:** You deploy a demand forecasting model. Two weeks later, MAPE has doubled. What do you check first?

**Answer structure:**
1. **Data pipeline:** Are inputs still arriving correctly? Schema changed?
2. **Concept drift:** Run ADF test on recent residuals. Plot predictions vs actuals.
3. **External event:** Holiday, promotion, supply shock? Retrain with recent data, or add event flag.
4. **Model degradation:** Has the target distribution shifted? Compare feature distributions (KS test).
5. **Rollback and retrain:** If uncertain, rollback to last known-good model while investigating.
</div>

---

## Q110. Classical ARIMA vs LightGBM vs DeepAR — when would you pick each? { #q110 }

| Criterion | ARIMA / Prophet | LightGBM | DeepAR / TFT |
|---|---|---|---|
| **Data size** | Single series, 100–10K points | Many series OR one with rich features | Many related series (100+) |
| **Exogenous features** | Difficult / limited | Easy | Native |
| **Cold start** | Needs long history | Needs features | Transfer from similar |
| **Probabilistic** | Yes, principled | No (or with quantile regression) | Native |
| **Training speed** | Fast per series | Very fast | Slow (GPU) |
| **Inference speed** | Fast | Very fast | Medium |
| **Interpretability** | High (trend/seasonal decomp) | Medium (SHAP) | Low |
| **Multi-horizon** | Recursive | Direct or recursive | Direct |
| **Irregularity** | Poor | OK with imputation | Specialized variants |

**Decision tree:**

- **One short series, strong seasonality:** Prophet or ETS.
- **One long series, trend + seasonality:** SARIMA or ETS.
- **Many series with shared patterns:** DeepAR or global LightGBM.
- **Rich exogenous features (weather, promos):** LightGBM or TFT.
- **Critical uncertainty estimates:** State space, DeepAR, quantile regression in GBM.
- **Quickest path to baseline:** Naive + seasonal naive → Prophet → LightGBM.

<div class="tip-box" markdown>
**Pragmatic truth:** For many business problems, a well-engineered LightGBM beats sophisticated deep learning. Fancy models shine when you have many related series (thousands of SKUs) and rich covariates. For one series with 500 points, ARIMA or ETS is usually better.
</div>
