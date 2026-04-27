# Module 12 — MLOps

> **Bible Module 12 of 14.** Self-contained. Written for **MLflow 2.16+, DVC 3.x, BentoML 1.3+, Ray 2.x, Apache Airflow 2.10+, Prefect 3.x, dbt-core 1.8+, Evidently 0.4+, Great Expectations 1.x, Feast 0.40+, Python 3.12+**. Patterns runnable as-is on CPU/local for verification. Assumes Modules 1, 2, 3, 4, 6, 7, 8.

---

## 0. Goal, reader, and how to use this module

**Goal.** After this module you can: build reproducible ML pipelines from raw data to served model; track experiments and model versions; deploy with reliable rollback; monitor production models for drift and performance regression; and design schedules for retraining without manual intervention.

**Target reader.** Modules 1–4, 6, 7, 8 done. The classical-ML and DL training material is the substrate; MLOps is the engineering around it.

**How to use it.** Run every code block; do all 36 problems before reading the solutions. MLOps is heavily about diagrams and decisions — keep §19 cheatsheet open.

**Prerequisites.** Module 7 (training pipelines), Module 6 (cloud + Docker), Module 4 (FastAPI for serving), Module 3 (databases for feature stores).
**Next steps.** Module 13 (LLMOps — the LLM-specific extensions), Module 14 (security automation — same patterns applied to SOC/SIEM).

---

## 1. The MLOps landscape and decision framework

### 1.1 What is MLOps actually solving

A model that works in a notebook is ~5% of the production journey. MLOps fills the other 95%:

| Problem | What MLOps gives you |
|---|---|
| "I can't reproduce last month's model." | Code + data + config versioning |
| "I don't know if the new model is better." | Experiment tracking + offline eval |
| "Production looks different from training." | Feature stores + train-serve consistency |
| "The model degraded but nobody noticed." | Monitoring + drift detection |
| "Retraining is a 3-day manual ordeal." | Pipelines + schedulers |
| "Rolling back the deploy is scary." | Model registry + blue/green |
| "The data team and ML team don't agree." | Contracts + dbt + tests |

### 1.2 The MLOps maturity ladder

| Level | What you have | What's missing |
|---|---|---|
| **0 — Notebook** | Code in Jupyter | Reproducibility, deployment |
| **1 — Manual deploy** | Git + Docker + manual CI | Auto retraining, monitoring |
| **2 — Pipelined training** | Airflow/Prefect + tracked experiments | Drift detection, registry-driven deploy |
| **3 — Continuous training** | Triggered retrains, registry, monitoring | Online learning, multi-model orchestration |
| **4 — Full MLOps** | A/B, shadow, canary, automated rollback | (You're here. Few teams reach this.) |

Most teams target Level 2-3. Level 4 has high engineering cost; only matters for ML-critical products at scale.

### 1.3 The core stack in 2026

| Layer | Standard tools |
|---|---|
| **Code & data versioning** | Git, DVC, lakeFS |
| **Experiment tracking** | MLflow, Weights & Biases, Neptune, Comet |
| **Pipelines / orchestration** | Airflow, Prefect, Dagster, Kubeflow Pipelines |
| **Feature store** | Feast, Tecton, Vertex AI FS, custom |
| **Model registry** | MLflow Model Registry, Vertex AI Model Registry, Weights & Biases |
| **Serving** | FastAPI, BentoML, KServe, Triton, SageMaker, Ray Serve |
| **Distributed compute** | Ray, Dask, Spark |
| **Monitoring & drift** | Evidently, Arize, Fiddler, WhyLabs, custom Prometheus |
| **Data quality / contracts** | Great Expectations, Soda, dbt tests, Pandera |

You'll use 4-7 of these in any real production setup. Don't try all of them; pick one per layer and master it.

### 1.4 Where ML-specific differs from "regular" MLOps

| ML concern | Software analog | Why MLOps is different |
|---|---|---|
| Train-serve skew | Code drift | Data is part of the artifact |
| Offline + online eval | Unit + integration tests | Reality changes; tests are non-deterministic |
| Rollback by version | Same | Models can degrade silently — rollback often needed without an obvious "bug" |
| Drift detection | (No analog) | Distribution shifts are the dominant production failure mode |
| Reproducibility | Same | Data + RNG + code + framework version all matter |
| Cost monitoring | Cloud cost | GPU bill can spike unexpectedly with retraining |

---

## 2. Reproducibility — the foundation

If you can't recreate a model 6 months from now, nothing else in MLOps matters. Reproducibility means: same code + same data + same config = same (or close-enough) model.

### 2.1 What needs versioning

| Artifact | How |
|---|---|
| **Code** | Git, with commit SHA pinned in artifacts |
| **Data** | DVC / lakeFS / Delta Lake / S3 versioning + manifest hash |
| **Config / hyperparams** | YAML/TOML in repo; logged in experiment tracker |
| **Random seeds** | Fixed and logged (`torch.manual_seed`, `np.random.seed`) |
| **Library versions** | `requirements.txt` / `uv.lock` / Docker image with pinned tags |
| **Trained model** | Model registry with version + metadata |
| **Eval set** | Versioned alongside data; immutable for fair comparison |
| **Compute env** | CUDA / driver / OS captured (Docker FROM image) |

A "model bundle" should let any teammate produce a forecast-equivalent artifact. The bundle pattern from Module 7 §13.2 generalizes to any model.

### 2.2 DVC for data versioning

Git tracks code; DVC tracks data referenced by Git. The pattern: a small `.dvc` file in Git points to a content-addressed blob in remote storage.

```bash
# install
pip install dvc dvc-s3                  # or dvc-gs / dvc-azure for other clouds

# initialize alongside Git
dvc init
dvc remote add -d storage s3://my-bucket/dvc

# track a dataset
dvc add data/raw/transactions.parquet   # creates data/raw/transactions.parquet.dvc, .gitignore entries
git add data/raw/transactions.parquet.dvc data/raw/.gitignore
git commit -m "Track raw transactions dataset"
dvc push                                # uploads the actual file to remote

# later, reproduce
git checkout <commit>
dvc pull                                # downloads exact file matching that commit
```

**DVC pipelines** chain stages with explicit deps:

```yaml
# dvc.yaml
stages:
  prepare:
    cmd: python src/prepare.py
    deps: [data/raw/transactions.parquet, src/prepare.py]
    outs: [data/processed/features.parquet]

  train:
    cmd: python src/train.py
    deps: [data/processed/features.parquet, src/train.py, params.yaml]
    params: [train.lr, train.n_estimators]
    outs: [models/model.joblib]
    metrics: [metrics.json]
```

`dvc repro` reruns only the stages whose deps changed. The full DAG is reproducible from `dvc.yaml` + `dvc.lock` + Git.

### 2.3 The reproducibility manifest

Every model artifact should ship with a **manifest.yaml**:

```yaml
model_name: churn-classifier
version: v3.1.0
framework: scikit-learn
framework_version: "1.8.0"
python_version: "3.12.1"
code_sha: abc123def456
data_sha: 8d4c2e9...                # DVC hash or s3 object version
data_window: ["2026-01-01", "2026-04-30"]
seeds:
  numpy: 42
  python: 42
  torch: 42
trained_at: "2026-04-30T14:23:00Z"
trained_by: ci-bot@example.com
metrics_test:
  auc: 0.873
  brier: 0.124
  positives_rate: 0.052
hyperparams:
  learning_rate: 0.05
  num_leaves: 63
docker_image: registry.example.com/ml/churn:v3.1.0
```

Without this, "reproduce that model" becomes archaeology.

### 2.4 The notebook problem

Notebooks are great for exploration; terrible as the source of truth. Production ML code goes in `.py` modules, with notebooks reduced to thin wrappers (`%run analysis.py` style).

**Rules for notebook → production:**
1. Refactor cells into functions with explicit inputs/outputs.
2. Move long-running cells (training) into scripts callable from a pipeline.
3. Lift away environment-specific paths into config.
4. Add tests for any business logic (`pytest`).

`papermill` parametrizes notebooks for batch reruns; `nbdev` / `jupytext` converts to `.py` and back. Pick one or just refactor to plain Python.

---

## 3. Experiment tracking — MLflow as the default

### 3.1 The problem

Without experiment tracking, "which model performed best" becomes a Slack thread. With it, you query a database.

### 3.2 MLflow tracking — minimal example

```python
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

mlflow.set_tracking_uri("http://mlflow.example.com:5000")    # or "file:./mlruns" for local
mlflow.set_experiment("churn-prediction")

with mlflow.start_run(run_name="rf_v1") as run:
    params = {"n_estimators": 300, "max_depth": 12, "min_samples_leaf": 2, "random_state": 42}
    mlflow.log_params(params)

    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_val)[:, 1]
    auc = roc_auc_score(y_val, proba)

    mlflow.log_metric("val_auc", auc)
    mlflow.log_metric("val_pos_rate", float(y_val.mean()))

    # log the model itself
    mlflow.sklearn.log_model(model, name="model", registered_model_name="churn-rf")

    # log artifacts (plots, schemas, etc.)
    mlflow.log_artifact("feature_importances.png")

    # tags for filtering
    mlflow.set_tags({"data_window": "2026Q1", "team": "growth-ml", "code_sha": "abc123"})

    print(f"Run {run.info.run_id} | AUC={auc:.4f}")
```

The `mlflow.sklearn.log_model` call serializes the pipeline + signature + an `mlmodel` descriptor that lets MLflow load it later regardless of the script that created it.

### 3.3 What to log every run

| Category | Fields |
|---|---|
| **Params** | All hyperparams + data window + feature list version |
| **Metrics** | Train/val/test scores; multiple metrics — not just one |
| **Artifacts** | The model; preprocessing artifacts; plots; schemas |
| **Tags** | Code SHA, data SHA, team, env (dev/staging/prod), purpose |
| **Notes** | Brief human-readable description (`mlflow.set_tag("mlflow.note.content", ...)`) |

### 3.4 Comparing runs and filtering

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()
runs = client.search_runs(
    experiment_ids=[exp_id],
    filter_string="metrics.val_auc > 0.85 and tags.env = 'staging'",
    order_by=["metrics.val_auc DESC"],
    max_results=20,
)
for r in runs:
    print(r.info.run_id, r.data.params, r.data.metrics["val_auc"])
```

The MLflow UI does this visually, but the API matters for CI: "promote the best run from yesterday's batch to staging" is a 5-line script.

### 3.5 Alternatives — when to skip MLflow

- **Weights & Biases / Comet / Neptune** — managed, prettier UI, more expensive.
- **TensorBoard** — for deep-learning-specific scalar/histogram tracking (combine with MLflow for run-level tracking).
- **Plain CSV + git tags** — fine for solo work; doesn't scale to a team.

For most teams in 2026: MLflow if self-hosted is OK, W&B if managed is OK.

---

## 4. The model registry pattern

A registry separates "this run produced a model" from "this model is the staging/production version." Decoupling lets you evaluate, rollback, A/B test without touching training code.

### 4.1 Stages

```
None → Staging → Production → Archived
```

Train runs land in **None**. After eval, promote to **Staging**. After validation in shadow / canary, promote to **Production**. When replaced, **Archive**.

### 4.2 MLflow registry — the API

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# register a model from a run
result = mlflow.register_model(
    model_uri=f"runs:/{run.info.run_id}/model",
    name="churn-rf",
)
version = result.version

# (modern MLflow uses aliases instead of legacy stages)
client.set_registered_model_alias("churn-rf", "staging", version)
# ... later, after passing tests ...
client.set_registered_model_alias("churn-rf", "production", version)

# load by alias from any consumer
import mlflow.pyfunc
model = mlflow.pyfunc.load_model("models:/churn-rf@production")
```

The `models:/<name>@<alias>` URI lets serving code load "whatever's currently production" without redeploying.

### 4.3 Registry-driven deploy

The serving Dockerfile pulls by alias:
```python
# at startup
import mlflow, mlflow.pyfunc, os
model = mlflow.pyfunc.load_model(os.environ["MODEL_URI"])      # e.g. "models:/churn-rf@production"
```

When you set the alias to a new version, restarting pods picks up the new model. Combined with rolling deploy (Module 6), zero-downtime model swaps.

### 4.4 Approval gates

Tag the registry with policy: which model versions can move to production?
- All offline metrics above thresholds (AUC ≥ 0.85, calibration ECE ≤ 0.05).
- Approved by data science lead (signature in tag).
- Schema compatibility verified (input columns identical).
- Smoke test passes against canary traffic.

These can be enforced via CI: a GitHub Action that calls the registry API and blocks merges if checks fail.

---

## 5. Pipelines — orchestrating ML work

A pipeline turns "I run these scripts in order" into a DAG that runs reliably, retries on failure, scales horizontally, and logs everything.

### 5.1 The pipeline architecture

```
[ raw data ] → ingest → validate → feature engineer → split → train → eval → register → notify
                          ↓               ↓             ↓        ↓       ↓        ↓
                       data tests    feature tests    leakage  metrics  gates  alerts
```

Each step is an independently retryable unit. Inputs and outputs are explicit (S3 paths, DB tables, registry URIs). The orchestrator (Airflow/Prefect/Dagster) tracks state and reruns only failures.

### 5.2 Airflow — the legacy standard

```python
# dags/churn_train.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {"owner": "ml-team", "retries": 2, "retry_delay": timedelta(minutes=5)}

with DAG(
    "churn_train",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule="0 2 * * *",                # 2 AM daily
    catchup=False,
    tags=["ml", "churn"],
) as dag:
    ingest   = PythonOperator(task_id="ingest",   python_callable=ingest_fn)
    validate = PythonOperator(task_id="validate", python_callable=validate_fn)
    featurize= PythonOperator(task_id="featurize",python_callable=featurize_fn)
    train    = PythonOperator(task_id="train",    python_callable=train_fn)
    evaluate = PythonOperator(task_id="evaluate", python_callable=evaluate_fn)
    register = PythonOperator(task_id="register", python_callable=register_fn)

    ingest >> validate >> featurize >> train >> evaluate >> register
```

### 5.3 Prefect — the modern alternative

```python
from prefect import flow, task

@task(retries=2, retry_delay_seconds=60)
def ingest():
    ...

@task
def validate(df): ...

@flow(name="churn-train")
def churn_train():
    df = ingest()
    validate(df)
    feats = featurize(df)
    model = train(feats)
    metrics = evaluate(model, feats)
    register(model, metrics)

if __name__ == "__main__":
    churn_train()                   # also runs as `prefect deploy`
```

Prefect 3 has nicer Python ergonomics, dynamic DAGs, and good observability. **For new projects in 2026, prefer Prefect or Dagster over Airflow.** For legacy teams already on Airflow, no need to migrate.

### 5.4 Dagster — asset-oriented thinking

Dagster models pipelines as **assets** (the data they produce) rather than tasks. Often a better fit for analytics-heavy ML pipelines.

```python
from dagster import asset

@asset
def raw_transactions():
    return pd.read_parquet("s3://raw/transactions.parquet")

@asset
def features(raw_transactions):
    return engineer_features(raw_transactions)

@asset
def trained_model(features):
    return train(features)
```

The framework discovers the dependency graph from function arguments. Asset-level lineage and freshness checks come built-in.

### 5.5 Triggering retrains

Three trigger types:

| Trigger | When |
|---|---|
| **Schedule** | Daily/weekly retrain regardless of data |
| **Data-driven** | New labeled data above threshold lands |
| **Drift-driven** | Monitoring detects performance drop or feature drift |
| **Manual** | Engineer pushes button (always available as fallback) |

In production: schedule + drift-driven, with manual override.

---

## 6. Feature stores

A feature store is a database optimized for ML features: precomputed values keyed by entity (user_id, product_id, etc.), with **point-in-time correctness** guarantees so training and serving see the same values.

### 6.1 Why feature stores exist

- Training computes `avg_purchase_30d` from historical aggregations.
- Serving needs the *same* feature, computed in real time, with the same definition.
- Without a feature store: two implementations, eventual divergence, train-serve skew.

### 6.2 The two-tier pattern

| Tier | Optimized for | Examples |
|---|---|---|
| **Offline** | Batch training (read all history) | Snowflake, BigQuery, Iceberg, Parquet on S3 |
| **Online** | Low-latency serving (read 1 row at a time) | Redis, DynamoDB, Cassandra, RocksDB |

Both tiers should have **identical feature definitions**. The store is the source of truth.

### 6.3 Feast — the open-source standard

```python
# features.py
from datetime import timedelta
from feast import Entity, Feature, FeatureView, Field
from feast.types import Int64, Float32
from feast.infra.offline_stores.file_source import FileSource

user = Entity(name="user_id", join_keys=["user_id"])

txn_source = FileSource(
    path="data/transactions.parquet",
    timestamp_field="event_ts",
)

user_30d_features = FeatureView(
    name="user_30d",
    entities=[user],
    ttl=timedelta(days=2),
    schema=[
        Field(name="purchase_count_30d", dtype=Int64),
        Field(name="purchase_total_30d", dtype=Float32),
    ],
    source=txn_source,
)
```

```python
# query at training time — historical, point-in-time correct
from feast import FeatureStore

store = FeatureStore(repo_path=".")
training_df = store.get_historical_features(
    entity_df=labels_df,                                # has user_id + event_ts (label time)
    features=["user_30d:purchase_count_30d", "user_30d:purchase_total_30d"],
).to_df()

# at serving time — online, latest values
features = store.get_online_features(
    features=["user_30d:purchase_count_30d", "user_30d:purchase_total_30d"],
    entity_rows=[{"user_id": 12345}],
).to_dict()
```

### 6.4 Point-in-time joins — the killer feature

For training, you need historical features as they were at the label time. For a churn label at `2026-01-15`, the feature `purchase_count_30d` must be computed using only data from `2025-12-16` to `2026-01-15` — *not* including future purchases.

Feast (and similar) handle this with **AS OF** joins: for each label row, find the most recent feature value before that row's timestamp. Doing this manually with SQL is error-prone; the feature store does it correctly by construction.

### 6.5 When NOT to bother

For a single model with simple features, a feature store is overkill. Reach for it when:
- Multiple models share features.
- You're hitting train-serve skew bugs.
- You need real-time serving with consistent definitions.

Otherwise, plain SQL + a reproducible feature pipeline (DVC §2) is fine.

---

## 7. Data quality and contracts

### 7.1 The three flavors of data validation

| Type | What it checks | Tool |
|---|---|---|
| **Schema** | Columns + types present | Pandera, dbt schema tests, Pydantic |
| **Distributional** | Stats within expected range | Great Expectations, Evidently |
| **Business** | Domain rules (no neg ages, dates < today) | Custom or GE custom expectations |

All three should run as a pipeline step, **not** at the end.

### 7.2 Pandera — Pythonic schema checks

```python
import pandera as pa
import pandera.typing as pat
from pandera import Column, Check, DataFrameSchema

schema = DataFrameSchema({
    "user_id":     Column(int,   Check.gt(0), unique=True),
    "age":         Column(int,   Check.in_range(0, 120)),
    "tenure_days": Column(int,   Check.ge(0)),
    "income":      Column(float, Check.ge(0), nullable=True),
    "country":     Column(str,   Check.isin(["US", "UK", "FR", "DE"])),
})

# validate
df_clean = schema.validate(df, lazy=True)        # collects all errors before raising
```

Plug into a pipeline step; failures halt training (good — surface bad data early).

### 7.3 Great Expectations — full data validation

GE is heavier but more powerful. Use when you need:
- A central catalog of expectations across many datasets.
- Data Docs (auto-generated HTML reports).
- Profiling new datasets to suggest expectations.
- Integrations with Airflow / Spark / dbt.

```python
import great_expectations as gx
context = gx.get_context()
ds = context.data_sources.add_pandas("local")
asset = ds.add_dataframe_asset(name="transactions")
batch = asset.add_batch_definition_whole_dataframe("batch").get_batch(batch_parameters={"dataframe": df})
suite = context.suites.add(gx.ExpectationSuite(name="transactions_suite"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="user_id"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="amount", min_value=0))
result = batch.validate(suite)
```

### 7.4 dbt tests — for warehouse-side data

If your features come from a data warehouse, dbt tests are the right layer:

```yaml
# models/schema.yml
models:
  - name: user_features
    columns:
      - name: user_id
        tests:
          - not_null
          - unique
      - name: country
        tests:
          - accepted_values:
              values: ["US", "UK", "FR", "DE"]
      - name: signup_date
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: "<= current_date"
```

Run as part of dbt build; failures block downstream feature publishing. **Catch data bugs upstream of ML, not in production inferences.**

### 7.5 Data contracts — the social layer

A "data contract" is a shared agreement between producers (data engineering) and consumers (ML team) about what data should look like. Concretely:
- Schema in code (often Avro/Protobuf).
- Owner, SLA, expectations.
- Versioned changes with deprecation periods.
- Breaking changes blocked by CI.

Tools: **Buf** (Protobuf), **DataContract.com** specification, **Datafold**. For most teams, a strict dbt schema with PR review is enough.


---

## 8. Serving — beyond the FastAPI wrapper

Module 4 covered the FastAPI basics; production ML serving has additional concerns.

### 8.1 The serving decision matrix

| Pattern | Latency | Throughput | When |
|---|---|---|---|
| **Batch** (scheduled job) | Hours | Massive | Forecasts, tagging large corpora |
| **Streaming** (Kafka consumer) | Seconds | High | Fraud, anomaly detection |
| **Online sync** (REST) | <100 ms | Medium | User-facing predictions |
| **Online async** (queue + result endpoint) | Seconds-minutes | High | Long-running predictions, document processing |
| **Embedded** (in-app model) | <10 ms | Per-device | Mobile, edge |

Most teams need 2-3 of these in production. Don't build all five at once.

### 8.2 BentoML — Python-first model serving

BentoML wraps any Python model with a serving framework: HTTP / gRPC, batching, ONNX-aware, Dockerizable.

```python
# service.py
import bentoml
from bentoml.io import JSON
import joblib

# load once at boot
model_ref = bentoml.sklearn.get("churn-classifier:latest")
runner = model_ref.to_runner()
svc = bentoml.Service("churn-svc", runners=[runner])

@svc.api(input=JSON(), output=JSON())
async def predict(payload: dict) -> dict:
    df = pd.DataFrame([payload])
    proba = (await runner.predict_proba.async_run(df))[0, 1]
    return {"churn_prob": float(proba)}
```

```bash
bentoml serve service:svc       # local
bentoml build                   # bake into a container
bentoml containerize churn-svc:latest
```

BentoML generates Dockerfiles with the right runtime (CPU/GPU), model bundle, and dependencies. Often a faster route than custom FastAPI when the model is the focus.

### 8.3 Triton Inference Server — for high-throughput

Triton is NVIDIA's open-source inference server. Strengths:
- Multi-framework (TensorRT, ONNX, PyTorch, TF).
- Dynamic batching (combines requests automatically).
- Concurrent model execution on a single GPU.
- HTTP / gRPC / streaming.

**Use Triton when** you have a heavy model on GPU and request rate > 100 RPS. **Skip it when** you serve sklearn/XGBoost on CPU — overkill.

### 8.4 Ray Serve — for compositions

Ray Serve excels at multi-model pipelines (model A → enrichment → model B), distributed serving, and dynamic scaling.

```python
from ray import serve

@serve.deployment(num_replicas=4, ray_actor_options={"num_cpus": 2})
class Classifier:
    def __init__(self): self.model = joblib.load("model.joblib")
    async def __call__(self, req): return self.model.predict_proba(req["x"]).tolist()

serve.run(Classifier.bind())
```

Ray scales replicas across a cluster and supports request routing logic.

### 8.5 The "boring" pattern — FastAPI + uvicorn + Docker

For 80% of production tabular ML in 2026, this is still the right answer (Module 4 + 6). It's familiar, debuggable, and there are 100k engineers who can maintain it.

Reach for BentoML / Ray / Triton when the boring pattern hits a real limit (latency, throughput, multi-model orchestration).

### 8.6 Batch prediction — the underrated pattern

For many problems (daily churn scores, weekly recommendations), batch prediction is simpler and cheaper than online serving:

```python
# batch_predict.py — runs on a schedule
import mlflow.pyfunc, pandas as pd, sqlalchemy as sa

model = mlflow.pyfunc.load_model("models:/churn-rf@production")
features = pd.read_sql("SELECT * FROM feature_views.user_30d", engine)
features["score"] = model.predict_proba(features.drop(columns=["user_id"]))[:, 1]
features[["user_id", "score"]].to_sql("scores.user_churn", engine, if_exists="replace", index=False)
```

Wrap in Airflow/Prefect; trigger downstream consumers (notifications, segmentation).

---

## 9. Monitoring and drift detection

### 9.1 The four signals to monitor for ML

| Signal | What it tells you |
|---|---|
| **Operational** (latency, error rate, throughput) | Service health |
| **Input drift** (feature distributions) | "Production data looks different from training" |
| **Output drift** (prediction distributions) | "The model is predicting differently than yesterday" |
| **Performance** (against ground truth, with delay) | "Is the model still accurate?" |

The first three you can compute in real time. The fourth needs labels — usually delayed by hours/days/weeks.

### 9.2 Operational monitoring — same as Module 4

Prometheus + Grafana from Module 4 §15.3. Add ML-specific metrics:

```python
from prometheus_client import Histogram, Counter

predict_latency = Histogram("ml_predict_seconds", "Prediction latency", ["model", "version"])
predict_count   = Counter  ("ml_predict_total",   "Predictions made",  ["model", "version", "outcome"])
predict_error   = Counter  ("ml_predict_error_total", "Prediction errors", ["model", "version", "kind"])
```

Alert on:
- p99 latency > target.
- Error rate > 1%.
- Sudden RPS drop (model not serving).
- Sudden RPS spike (downstream calling wildly).

### 9.3 Input drift detection

For each feature, compare the **production distribution** to the **training distribution**. Detection methods:

| Method | When |
|---|---|
| **PSI** (Population Stability Index) | Single-feature, binned, easy to interpret |
| **KL divergence** / **Jensen-Shannon** | Same; symmetric variant |
| **Kolmogorov-Smirnov test** | Continuous features |
| **Chi-squared test** | Categorical features |
| **Wasserstein distance** | Continuous; robust to outliers |

```python
import numpy as np

def psi(reference, current, bins=10):
    """Population Stability Index. >0.2 signals significant drift; >0.1 mild."""
    edges = np.histogram_bin_edges(reference, bins=bins)
    ref_hist, _ = np.histogram(reference, bins=edges)
    cur_hist, _ = np.histogram(current,   bins=edges)
    ref_p = ref_hist / max(ref_hist.sum(), 1)
    cur_p = cur_hist / max(cur_hist.sum(), 1)
    eps = 1e-6
    return float(np.sum((cur_p - ref_p) * np.log((cur_p + eps) / (ref_p + eps))))
```

Compute PSI per feature, daily, on a sample of production traffic (e.g., 10k rows). Alert when any PSI > 0.2.

### 9.4 Output drift

Same idea, but on the model's predictions. If prediction distribution shifts (mean prediction rate goes from 5% to 15% positive), something changed — input drift, label drift, or model bug.

```python
# percentage of predictions above threshold, over time
positive_rate = (predictions > 0.5).mean()
```

Track positive rate (or mean prediction) hourly; alert on >2σ deviation from baseline.

### 9.5 Performance monitoring (the tricky one)

To compute AUC/F1 you need true labels. For most ML applications, labels arrive with delay:
- Churn prediction: 30-day window before label is known.
- Click prediction: minutes.
- Fraud: hours-days when chargebacks come back.
- Loan default: months.

Patterns:
1. **Delayed evaluation** — store predictions; join to labels when they arrive; compute on a schedule.
2. **Proxy metrics** — track easier-to-compute signals (output rate, calibration of probability bins).
3. **Held-out canary** — deploy candidate models on 5% traffic; measure when labels arrive.

### 9.6 Evidently — the open-source choice

Evidently produces drift reports + a dashboard. Integrates with Prometheus.

```python
from evidently import Report
from evidently.presets import DataDriftPreset, RegressionPreset

report = Report(metrics=[DataDriftPreset()])
result = report.run(reference_data=train_df, current_data=prod_df)
result.save_html("drift_report.html")
```

Run as a daily/weekly job; surface to Slack on findings.

### 9.7 Adversarial / safety monitoring (preview of Module 14)

For LLM apps, monitor for:
- Prompt injection patterns in inputs.
- Refusal rates (sudden spike = jailbreak attempt).
- PII in outputs.

Module 13 (LLMOps) covers these.

---

## 10. Continuous training

### 10.1 What "continuous" means

Not online learning (updating weights on every example). It means **automated retraining triggered by criteria**, with the same rigor as a human-driven retrain — eval, gates, deploy.

### 10.2 Triggers worth automating

```
schedule:    weekly (default for stable problems)
data:        new labeled rows > 10k since last train
drift:       PSI > 0.2 on top-3 features for 3 consecutive days
performance: live AUC drops below threshold (with confidence interval)
manual:      always available — emergency rollback or hotfix
```

Build an orchestrator (Airflow/Prefect) with these triggers. Each one creates a training run with a tag (`trigger: drift_alert_2026-04-30`) so you can audit the cause.

### 10.3 The gate-driven deploy

Every retrained model passes through gates before reaching production:

```
trained → offline_eval → staging → shadow → canary → production
```

Each step has a **measurable gate**:
- Offline: AUC ≥ X, calibration ECE ≤ Y, no feature schema change.
- Staging: smoke tests pass, response time within budget.
- Shadow: predictions on production traffic match within 1% of current production model (for small-change retrains) OR pass differential analysis.
- Canary: 5% of traffic for 24h; key metrics within tolerance.

Failures route back to the data team or trigger rollback.

### 10.4 A/B testing models

For revenue-driving models, randomized control matters more than statistical confidence in offline metrics.

```python
def assign_variant(user_id: int, experiment: str) -> str:
    """Stable hash bucket. Returns 'control' or 'treatment'."""
    import hashlib
    h = hashlib.sha256(f"{experiment}:{user_id}".encode()).hexdigest()
    return "treatment" if int(h, 16) % 100 < 50 else "control"
```

Track:
- Predictions made by each model.
- Downstream business outcomes per variant (purchases, retention, error rates).
- p-values + practical effect sizes after sufficient sample.

Most ML A/B tests need weeks to reach significance; design for that timeline.

### 10.5 Shadow deploy — the underrated pattern

Run new model alongside current model; serve old model's predictions to users; **log both** for offline comparison. No user impact, perfect data.

```python
@app.post("/predict")
async def predict(req: Request) -> Response:
    prod_pred = await prod_model.predict(req)
    candidate_pred = await candidate_model.predict(req)        # don't await? actually do - log both
    log_shadow(req, prod_pred, candidate_pred)
    return prod_pred
```

Shadow for 1-7 days before shadow → canary → production.

---

## 11. Distributed training and large-scale workflows

### 11.1 When you need distributed compute

| Workload | Solution |
|---|---|
| Hyperparameter sweep | Optuna distributed; Ray Tune |
| Big tabular dataset (>20 GB) | Dask, Spark, or Polars on a beefy node |
| Big neural net | DDP / FSDP (Module 8 §10) |
| Large feature engineering | Spark, Dask, BigQuery (Module 5) |
| Many models in parallel | Airflow dynamic tasks; Ray actors |

### 11.2 Ray — for distributed Python

Ray excels at scaling Python code (functions, classes) across a cluster. Three layers:

```python
# Ray Core — primitives
import ray; ray.init()
@ray.remote
def heavy_compute(x): return x ** 2

futures = [heavy_compute.remote(i) for i in range(100)]
results = ray.get(futures)
```

```python
# Ray Tune — hyperparameter tuning across workers
from ray import tune
def trainable(config): tune.report(score=run_one(config))
tuner = tune.Tuner(trainable, param_space={"lr": tune.loguniform(1e-5, 1e-1)})
tuner.fit()
```

```python
# Ray Train — distributed PyTorch / Tensorflow / XGBoost
from ray.train import ScalingConfig
from ray.train.torch import TorchTrainer

trainer = TorchTrainer(
    train_loop_per_worker=train_fn,
    scaling_config=ScalingConfig(num_workers=4, use_gpu=True),
)
trainer.fit()
```

### 11.3 Dask — for big DataFrames

If you outgrow pandas but can't justify Spark, Dask is a parallel pandas substitute:

```python
import dask.dataframe as dd
df = dd.read_parquet("s3://big-bucket/transactions/*.parquet")
agg = (df.groupby("user_id")["amount"].sum().compute())  # triggers distributed computation
```

### 11.4 The Polars-as-Spark-replacement angle

For single-machine workloads up to ~100GB, **Polars with streaming + lazy** (Module 2) often beats Spark/Dask in throughput and ergonomics. Reserve Spark for true multi-node TB-scale work.

---

## 12. Cost monitoring and FinOps for ML

### 12.1 Where the bill goes

| Cost driver | Typical share |
|---|---|
| GPU training | Largest if you train often |
| Inference (CPU/GPU) | Largest if RPS is high |
| Storage (data + artifacts) | Modest, but grows quietly |
| Data transfer | Sneaky — egress between regions/services |
| Notebooks / dev clusters | Often 20–40% of compute waste |

### 12.2 Tagging — the foundation

Every ML resource (notebook instance, training job, serving cluster, S3 prefix) gets tagged:
```
env=prod | dev | exp
team=growth-ml | platform-ml | research
project=churn | recommendations | ...
owner=alice@example.com
```

Without tags, you can't attribute spend; with them, monthly cost per project becomes a SQL query.

### 12.3 Practical FinOps wins

- Use spot/preemptible for training (Module 6 §3).
- Auto-stop dev notebooks after 1h idle.
- Right-size GPUs (don't run inference on A100 if T4 fits).
- Cache pretrained models locally to avoid re-downloading.
- Pre-aggregate features rather than recomputing per request.
- Quantize models served at scale (Module 10 §5.5).

### 12.4 Showback / chargeback

Send each team a weekly cost report with deltas. Cultural change: ML engineers internalize cost.

---

## 13. Anti-patterns

| Anti-pattern | Right way |
|---|---|
| Notebook is the source of truth | Refactor to .py modules + a notebook entrypoint |
| `joblib.load` from a path with no version | Use a registry; load by alias |
| Train and serve compute features differently | Feature store or shared library |
| `pickle` model files | `safetensors` for tensors; `joblib` with manifest for sklearn |
| Random seeds set somewhere but not all | Set at all sources (Python, NumPy, torch, CUDA) and log them |
| Logging only one metric | Log multiple; monitoring needs them later |
| Test set used during tuning | Reserve test for a single final eval |
| One environment file for everyone | Pin deps with `uv.lock` or Docker image SHA |
| Drift detection on raw inputs only | Also monitor predictions and (delayed) performance |
| "It worked yesterday" without versioning | Tag every artifact with code SHA + data hash |
| Production model with no rollback plan | Registry alias swap; previous version always promotable |
| Manual deploy on green metrics | Gate-driven CI; same green criteria each time |
| One huge Airflow DAG | Decompose into stages with explicit interfaces |
| Drift alerts going to nobody | Owner per model + Slack channel + on-call rotation |
| Training pipeline runs only when broken | Schedule + drift-driven + manual = three triggers |
| GPU dev box always on | Auto-stop after idle; spin up on demand |
| Models without performance budgets | Define p99 latency + RPS upfront |
| "MLOps tools" as a goal | Pick the minimum that solves your problem |
| Custom-everything stack | Use battle-tested tools where possible (MLflow, Airflow, vLLM) |

---

## 14. Thirty-six problems (with full structure)

Each problem follows: **Statement → Intuition → Brute force → Optimized → Complexity → Edge cases → Real-world → Follow-ups.**
**Section breakdown:** 5 reproducibility (P1–P5), 5 experiments + registry (P6–P10), 5 pipelines (P11–P15), 4 feature stores (P16–P19), 5 data quality (P20–P24), 5 serving (P25–P29), 5 monitoring + drift (P30–P34), 2 continuous training (P35–P36).

---

### Problem 1 — Build a reproducibility manifest

**Statement.** Write a function that produces a manifest dict for the trained model: code SHA, data hash, library versions, seeds, metrics, timestamp.

**Solution.**
```python
import hashlib, json, subprocess, sys, datetime

def make_manifest(model_name, version, data_path, metrics, hyperparams, seeds):
    code_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    with open(data_path, "rb") as f:
        data_sha = hashlib.sha256(f.read()).hexdigest()
    return {
        "model_name": model_name,
        "version": version,
        "code_sha": code_sha,
        "data_sha": data_sha,
        "data_path": str(data_path),
        "python_version": sys.version.split()[0],
        "trained_at": datetime.datetime.utcnow().isoformat() + "Z",
        "seeds": seeds,
        "hyperparams": hyperparams,
        "metrics": metrics,
    }
```

**Real-world.** Save next to the model artifact (S3 / registry). Surface in monitoring dashboards. Critical for compliance reviews.

**Follow-ups.** Add `library_versions` (pip freeze, pinned). Add Docker image digest.

---

### Problem 2 — DVC pipeline for a churn model

**Statement.** Define `dvc.yaml` with prepare → train → evaluate stages. Show the changes flow on data updates.

**Solution.**
```yaml
stages:
  prepare:
    cmd: python src/prepare.py --in data/raw/transactions.parquet --out data/processed/features.parquet
    deps:
      - data/raw/transactions.parquet
      - src/prepare.py
    outs:
      - data/processed/features.parquet

  train:
    cmd: python src/train.py --features data/processed/features.parquet --out models/model.joblib
    deps:
      - data/processed/features.parquet
      - src/train.py
      - params.yaml
    params:
      - train.lr
      - train.n_estimators
    outs:
      - models/model.joblib

  evaluate:
    cmd: python src/evaluate.py --model models/model.joblib --features data/processed/features.parquet --out metrics.json
    deps:
      - models/model.joblib
      - src/evaluate.py
    metrics:
      - metrics.json
```

`dvc repro` reruns only the changed stages. `dvc params diff` and `dvc metrics diff` show experimentation deltas.

**Real-world.** Pairs perfectly with CI: PRs run `dvc repro && dvc metrics show` and post results as comments.

**Follow-ups.** Multiple parallel experiments via `dvc exp run`. Remote storage for big artifacts.

---

### Problem 3 — Pin a Python environment for serving

**Statement.** Make a serving image whose dependencies don't drift between builds.

**Solution.** Pin transitively, not just direct deps:

```bash
# in your repo
uv pip compile requirements.in -o requirements.txt --generate-hashes
```

`requirements.txt` has every transitive dep with a hash. `pip install -r requirements.txt` is byte-stable.

```dockerfile
# Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Real-world.** Without hash-pinning, a new build of "the same code" can pick up a new transitive version that breaks production.

**Follow-ups.** Multi-stage Dockerfile to slim images. SBOM (Software Bill of Materials) generation for compliance.

---

### Problem 4 — Seed everything

**Statement.** A function that seeds Python, NumPy, PyTorch, CUDA — and logs the seeds used.

**Solution.**
```python
import os, random, numpy as np, torch

def seed_everything(seed: int = 42, deterministic: bool = False) -> dict:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
        torch.use_deterministic_algorithms(True, warn_only=True)
    return {"python": seed, "numpy": seed, "torch": seed,
            "cuda": seed if torch.cuda.is_available() else None,
            "deterministic": deterministic}
```

**Real-world.** Logs to MLflow as `tags.seeds`. Some operations (multi-GPU bf16) remain slightly non-deterministic; document expected variance.

**Follow-ups.** Per-DataLoader-worker seeding via `worker_init_fn`. Distributed seeding (`rank * 1000 + base_seed`).

---

### Problem 5 — Detect environment drift between training and serving

**Statement.** Two services claim to run the same code. Detect that they don't.

**Solution.**
```python
def env_fingerprint() -> dict:
    import sys, platform, importlib
    pkgs = ["torch", "transformers", "scikit-learn", "numpy", "pandas"]
    fp = {
        "python_version": sys.version,
        "platform": platform.platform(),
    }
    for p in pkgs:
        try:
            mod = importlib.import_module(p.replace("-", "_"))
            fp[p] = getattr(mod, "__version__", "unknown")
        except ImportError:
            fp[p] = None
    return fp
```

Have both services expose `/health` returning their fingerprint. Diff in monitoring.

**Real-world.** Train-serve skew often reduces to "training had numpy 1.26, production has 2.1, and one of these silently rounds floats differently."

**Follow-ups.** Pin Docker image digest in registry alias. Hash-pin requirements (P3).

---

### Problem 6 — MLflow run with full logging

**Solution.**
```python
import mlflow, mlflow.sklearn, sys
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, brier_score_loss
import numpy as np

mlflow.set_experiment("churn")
with mlflow.start_run(run_name="rf_v1") as run:
    params = {"n_estimators": 300, "max_depth": 12, "min_samples_leaf": 5,
               "class_weight": "balanced", "random_state": 42, "n_jobs": -1}
    mlflow.log_params(params)
    mlflow.set_tags({"data_window": "2026Q1", "code_sha": "abc123",
                      "trigger": "scheduled", "env": "dev"})

    m = RandomForestClassifier(**params).fit(X_train, y_train)
    proba_v = m.predict_proba(X_val)[:, 1]

    mlflow.log_metrics({
        "val_auc": roc_auc_score(y_val, proba_v),
        "val_brier": brier_score_loss(y_val, proba_v),
        "val_pos_rate": float(y_val.mean()),
        "n_train": len(X_train), "n_val": len(X_val),
    })
    mlflow.sklearn.log_model(m, name="model", registered_model_name="churn-rf",
                              input_example=X_val.iloc[:5])
```

**Real-world.** Add a hash of the data source (e.g., DVC `.dvc` file) so you can trace lineage.

**Follow-ups.** Nested runs for hyperparameter sweeps. `mlflow.evaluate` for richer model evaluation.

---

### Problem 7 — Promote best run to staging

**Statement.** Find the highest-AUC run from the last 24h with `env=dev`, register it, and assign the `staging` alias.

**Solution.**
```python
from mlflow.tracking import MlflowClient
import datetime as dt

client = MlflowClient()
exp = client.get_experiment_by_name("churn")
since_ms = int((dt.datetime.utcnow() - dt.timedelta(days=1)).timestamp() * 1000)
runs = client.search_runs(
    [exp.experiment_id],
    filter_string=f"tags.env = 'dev' and metrics.val_auc > 0.85 and "
                   f"attributes.start_time > {since_ms}",
    order_by=["metrics.val_auc DESC"], max_results=1,
)
if not runs: raise SystemExit("No qualifying runs")
run = runs[0]
result = mlflow.register_model(model_uri=f"runs:/{run.info.run_id}/model", name="churn-rf")
client.set_registered_model_alias("churn-rf", "staging", result.version)
print(f"Promoted run {run.info.run_id} as version {result.version} → staging")
```

**Real-world.** Run as a scheduled CI job. Slack notification on promotion.

**Follow-ups.** Combine with smoke tests; only promote if smoke passes.

---

### Problem 8 — Reload the production model in serving

**Statement.** Serving code should pick up new prod model versions without redeploying.

**Solution.**
```python
import mlflow.pyfunc, threading, time, os

class ModelHolder:
    def __init__(self, uri: str, refresh_seconds: int = 300):
        self.uri = uri
        self.model = mlflow.pyfunc.load_model(uri)
        self._lock = threading.Lock()
        threading.Thread(target=self._refresh, args=(refresh_seconds,), daemon=True).start()

    def _refresh(self, secs: int):
        while True:
            time.sleep(secs)
            try:
                new = mlflow.pyfunc.load_model(self.uri)
                with self._lock: self.model = new
            except Exception as e:
                print("model refresh failed:", e)

    def predict(self, X):
        with self._lock: return self.model.predict(X)

holder = ModelHolder(os.environ["MODEL_URI"])  # e.g. "models:/churn-rf@production"
```

**Real-world.** The pattern lets you deploy a new model by changing the registry alias and waiting up to 5 minutes for serving pods to pick it up. Beats redeploying containers.

**Follow-ups.** Compare model version metadata before swap (graceful rollback if new model fails health check).

---

### Problem 9 — A/B test two models offline

**Solution.**
```python
import numpy as np
from sklearn.metrics import roc_auc_score
from scipy.stats import bootstrap

def compare_with_ci(y_true, p_a, p_b, n_resamples=1000, alpha=0.05):
    """Bootstrap CI for AUC difference."""
    auc_a = roc_auc_score(y_true, p_a)
    auc_b = roc_auc_score(y_true, p_b)
    rng = np.random.default_rng(42)
    diffs = []
    n = len(y_true)
    for _ in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        diffs.append(roc_auc_score(y_true[idx], p_b[idx]) - roc_auc_score(y_true[idx], p_a[idx]))
    diffs = np.sort(diffs)
    lo, hi = diffs[int(alpha/2 * n_resamples)], diffs[int((1-alpha/2) * n_resamples)]
    return {"auc_a": auc_a, "auc_b": auc_b,
             "diff": auc_b - auc_a, "ci": (lo, hi),
             "significant": lo > 0 or hi < 0}
```

**Real-world.** Don't promote based on single-decimal AUC differences; use bootstrap CIs. A 0.001 AUC bump might not survive resampling.

**Follow-ups.** McNemar's test for paired classification.

---

### Problem 10 — Structured comparison report (champion vs challenger)

**Solution.**
```python
import pandas as pd

def comparison_report(y_true, p_champion, p_challenger):
    return pd.DataFrame({
        "metric": ["AUC", "Brier", "Recall@P=0.9", "FN_at_t0.5"],
        "champion":   [auc_at(y_true, p_champion), brier(y_true, p_champion), recall_at_p(y_true, p_champion, 0.9), fn_at(y_true, p_champion, 0.5)],
        "challenger": [auc_at(y_true, p_challenger), brier(y_true, p_challenger), recall_at_p(y_true, p_challenger, 0.9), fn_at(y_true, p_challenger, 0.5)],
    }).assign(delta=lambda d: d["challenger"] - d["champion"])
```

**Real-world.** A single number ("AUC went up") is easy to sneak past review. A multi-metric report exposes trade-offs ("AUC up 0.005, but Recall@P=0.9 down 0.04").

**Follow-ups.** Per-segment reports (by country, customer tier).

---

### Problem 11 — Airflow DAG for a daily train

**Statement.** Author a daily training DAG with retries, alerting, and downstream registry alias update.

**Solution.**
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.email import send_email
from datetime import datetime, timedelta

def alert_on_failure(context):
    send_email(to="ml-oncall@example.com",
               subject=f"DAG failed: {context['dag'].dag_id}",
               html_content=f"Task: {context['task_instance'].task_id}")

default_args = {"owner": "ml", "retries": 2, "retry_delay": timedelta(minutes=10),
                 "on_failure_callback": alert_on_failure}

with DAG("churn_daily_train", schedule="0 2 * * *",
          start_date=datetime(2026,1,1), catchup=False,
          default_args=default_args, tags=["ml","churn"]) as dag:
    ingest    = PythonOperator(task_id="ingest",    python_callable=ingest_fn)
    validate  = PythonOperator(task_id="validate",  python_callable=validate_fn)
    train     = PythonOperator(task_id="train",     python_callable=train_fn)
    evaluate  = PythonOperator(task_id="evaluate",  python_callable=evaluate_fn)
    promote   = PythonOperator(task_id="promote",   python_callable=promote_to_staging_fn)
    smoke     = BashOperator  (task_id="smoke",     bash_command="python tests/smoke_test.py")
    publish   = PythonOperator(task_id="publish",   python_callable=alias_to_prod_fn)

    ingest >> validate >> train >> evaluate >> promote >> smoke >> publish
```

**Real-world.** Email alerts on failure are a starting point; for serious teams, route to PagerDuty + Slack. Define clear ownership (`owner=growth-ml`) so on-call routing works.

**Follow-ups.** Dynamic task mapping (parallel by country). Backfill strategy for historical data.

---

### Problem 12 — Prefect flow with the same DAG

**Solution.**
```python
from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import timedelta

@task(retries=2, retry_delay_seconds=600,
      cache_key_fn=task_input_hash, cache_expiration=timedelta(hours=24))
def ingest(date: str):
    return read_data(date)

@task
def validate(df): ...

@flow(name="churn-daily-train")
def churn_train(date: str):
    df = ingest(date)
    validate(df)
    feats = featurize(df)
    model = train(feats)
    if evaluate(model, feats)["val_auc"] >= 0.85:
        promote(model)
```

**Real-world.** Prefect's caching is a win for incremental retrains. Native `--watch` for local dev iteration.

**Follow-ups.** Deploy with `prefect deploy` to a worker pool. Sub-flows for parallel multi-region training.

---

### Problem 13 — Idempotent pipeline step

**Statement.** A "load to BQ" step crashes mid-write. Make rerunning it safe.

**Solution.**
- Write to a **versioned partition** (`partition = today + run_id`).
- After successful write, atomically swap the active alias / view.
- On retry, the partition is recreated; rerun produces the same partition; final swap is idempotent.

```python
def load_to_bq_idempotent(df, dataset, table, run_id):
    target = f"{dataset}.{table}_v_{run_id}"
    df.to_gbq(target, if_exists="replace")
    # update view to point at this version
    bq.query(f"CREATE OR REPLACE VIEW {dataset}.{table} AS SELECT * FROM {target}").result()
```

**Real-world.** Idempotency is the foundation of reliable pipelines. Without it, retries duplicate, corrupt, or skip data.

**Follow-ups.** Two-phase commit. Write to staging table, validate, then swap.

---

### Problem 14 — Backfill historical data

**Statement.** A new feature needs to be computed for the last 90 days of data.

**Solution.**
```python
# Airflow with date-parameterized DAG runs
from airflow.operators.python import PythonOperator

with DAG("backfill_feature_x", ...) as dag:
    compute = PythonOperator(
        task_id="compute_for_date",
        python_callable=compute_feature_x_for_date,
        op_kwargs={"date": "{{ ds }}"},      # Airflow templating
    )

# trigger backfill: airflow dags backfill -s 2026-01-30 -e 2026-04-30 backfill_feature_x
```

For Prefect: parametrize the flow, then submit one run per date.

**Real-world.** Backfills are when concurrency / resource limits bite. Cap parallelism (`max_active_runs=4`); rate-limit downstream APIs.

**Follow-ups.** Resumable backfills (skip already-completed dates). Monitor and alert if backfill diverges from real-time pipeline.

---

### Problem 15 — Decompose a monolithic 50-task DAG

**Statement.** Inherited a single Airflow DAG with 50 mixed tasks. How would you refactor?

**Approach.**
1. **Group by domain** — ingest, features, model A, model B, alerting.
2. **Extract reusable subDAGs** (or task groups in Airflow 2).
3. **Decouple via assets / data, not control flow** — model B should react to model A's *output asset*, not be wired in series.
4. **Add sensors** for cross-DAG dependencies (`ExternalTaskSensor`).
5. **Document** ownership per group.

**Real-world.** The "one big DAG" pattern fails when (a) one team's bug blocks another team's training, (b) resource contention forces global serialization, (c) on-call has to remember 50 tasks' purpose.

**Follow-ups.** Migrate to Dagster's asset model where the DAG emerges from data dependencies.

---

### Problem 16 — Build a minimal Feast feature view

**Solution.**
```python
from feast import FeatureStore, Entity, FeatureView, Field
from feast.types import Int64, Float32
from feast.infra.offline_stores.file_source import FileSource
from datetime import timedelta

user = Entity(name="user_id", join_keys=["user_id"])

txn_source = FileSource(
    path="data/user_aggregations.parquet",
    timestamp_field="event_ts",
)

user_features = FeatureView(
    name="user_30d",
    entities=[user],
    ttl=timedelta(days=2),
    schema=[
        Field(name="purchase_count_30d", dtype=Int64),
        Field(name="purchase_total_30d", dtype=Float32),
    ],
    source=txn_source,
)
```

After `feast apply`, fetch features for training (with point-in-time correctness) and serving (latest values).

**Real-world.** Define features once, use everywhere. The point-in-time guarantee is the killer feature.

**Follow-ups.** Push streaming feature updates via the online store. Materialize jobs (`feast materialize`) on a schedule.

---

### Problem 17 — Avoid look-ahead in feature engineering

**Statement.** A feature `avg_purchase_30d` is computed for a user, used in training to predict `next_30d_churn`. Why is the naive rolling computation a leak?

**Diagnosis.** A naive `.rolling(30).mean()` on the full history at training time may include rows *after* the label timestamp — meaning the model trains on knowing the future.

**Fix.** Compute features as-of the label timestamp:

```sql
-- BigQuery / Snowflake; "AS OF" join
SELECT
  l.user_id, l.label_ts, l.label,
  AVG(t.amount) OVER (
    PARTITION BY l.user_id ORDER BY t.event_ts
    RANGE BETWEEN INTERVAL '30 days' PRECEDING AND CURRENT ROW
  ) AS avg_purchase_30d
FROM labels l
JOIN transactions t
  ON t.user_id = l.user_id AND t.event_ts <= l.label_ts
```

Or use Feast's `get_historical_features` with the label DataFrame's `event_timestamp` — handled correctly by construction.

**Real-world.** Look-ahead leakage is the #2 cause of "model degraded in production" bugs (after train-serve skew).

**Follow-ups.** Detect leakage with backtesting on multiple cutoff dates.

---

### Problem 18 — Online + offline parity test

**Statement.** Train a model offline, serve it online. Periodically prove the features are the same.

**Solution.**
```python
def parity_check(user_ids, feast_store, online_endpoint):
    """For a sample of users, compute features both ways; assert equal."""
    diffs = []
    for uid in user_ids:
        offline = feast_store.get_online_features(
            features=["user_30d:purchase_count_30d", "user_30d:purchase_total_30d"],
            entity_rows=[{"user_id": uid}],
        ).to_dict()
        online = call_serving(online_endpoint, uid)["features"]
        for k in offline:
            if abs(offline[k][0] - online[k]) > 1e-6:
                diffs.append((uid, k, offline[k][0], online[k]))
    return diffs
```

Run hourly; any diffs > 0 is an alert.

**Real-world.** Catches train-serve skew before it shows up as accuracy degradation.

**Follow-ups.** Sample-based parity for high-RPS systems. Track drift in feature *definitions* (e.g., timezone bugs).

---

### Problem 19 — Compute a feature at request time vs from store

**Trade-off.**
| Compute at request | Read from store |
|---|---|
| Always fresh | Latency-bounded (microseconds) |
| Source-of-truth integration | Cached, periodic refresh |
| Bottleneck on RPS | Scales horizontally |
| Brittle if upstream slow/down | Independent of upstream |

**Rule of thumb:** Read from store for anything that needs <50ms latency or can tolerate 1-15 minute staleness. Compute at request for very volatile signals (in-session features, current cart).

**Real-world.** Hybrid: feature store for static features, request-time for in-session.

**Follow-ups.** Real-time feature engineering pipelines (Flink, Materialize).

---

### Problem 20 — Pandera schema for a feature DataFrame

**Solution.**
```python
import pandera as pa
from pandera import Column, Check, DataFrameSchema

schema = DataFrameSchema({
    "user_id":            Column(int,   Check.gt(0), unique=True),
    "age":                Column(int,   Check.in_range(13, 120)),
    "tenure_days":        Column(int,   Check.ge(0)),
    "income":             Column(float, Check.ge(0), nullable=True),
    "country":            Column(str,   Check.isin(["US","UK","FR","DE"])),
    "purchase_count_30d": Column(int,   Check.ge(0)),
}, strict=True)        # extra columns rejected

df_clean = schema.validate(df, lazy=True)
```

**Real-world.** Plug into a pipeline step. Failures halt training. Use `lazy=True` to surface ALL violations rather than the first one.

**Follow-ups.** Inheritance-based schemas for shared base + variants. Custom checks (`Check(lambda s: ...)`).

---

### Problem 21 — Detect feature distribution shift

**Solution.** (See §9.3 for `psi` function.)

```python
import numpy as np

def feature_drift_report(reference_df, current_df, threshold=0.2):
    """Return per-feature PSI and flag drifted features."""
    out = {}
    for col in reference_df.select_dtypes("number"):
        ref, cur = reference_df[col].dropna(), current_df[col].dropna()
        if len(ref) and len(cur):
            score = psi(ref.values, cur.values)
            out[col] = {"psi": round(score, 3), "drifted": score > threshold}
    return out
```

**Real-world.** Compute daily on a 10k-row sample of production traffic. Surface as a Slack message; auto-create a Jira ticket for any drifted feature.

**Follow-ups.** Per-segment drift (e.g., drift in `country=US` only). Causal analysis (which upstream change caused drift).

---

### Problem 22 — Great Expectations suite for raw data

**Solution.**
```python
import great_expectations as gx

context = gx.get_context()
ds = context.data_sources.add_pandas("my_pandas")
asset = ds.add_dataframe_asset(name="raw_transactions")
batch = asset.add_batch_definition_whole_dataframe("batch") \
              .get_batch(batch_parameters={"dataframe": df})

suite = context.suites.add(gx.ExpectationSuite(name="raw_transactions"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="user_id"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="amount", min_value=0))
suite.add_expectation(gx.expectations.ExpectColumnValuesToMatchRegex(
    column="country", regex=r"^[A-Z]{2}$"
))

result = batch.validate(suite)
print(result["success"])
```

**Real-world.** GE generates Data Docs (HTML reports) for stakeholders. Run as a pipeline gate; halt downstream on failure.

**Follow-ups.** Auto-generate expectations from a profiling pass. Time-series expectations (no anomaly in row count).

---

### Problem 23 — Catch label leakage at training time

**Statement.** A new feature `last_login_within_24h` correlates 0.9 with churn label. Is this a leak?

**Diagnosis questions:**
1. Is the feature computed using data **after** the label timestamp? If yes, leak.
2. Is the feature definitionally the label or a near-duplicate? If yes, leak.
3. Does the feature exist at serving time? If no, this won't generalize.

**Auto-detection.** Single-feature decision tree of depth 1 should not score AUC > 0.95 unless that feature is the label.

```python
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import roc_auc_score
for col in features:
    clf = DecisionTreeClassifier(max_depth=2, random_state=42)
    clf.fit(X[[col]].fillna(-999), y)
    auc = roc_auc_score(y, clf.predict_proba(X[[col]].fillna(-999))[:, 1])
    if auc > 0.95: print(f"⚠ {col}: AUC={auc:.3f} — likely leak")
```

**Real-world.** Module 7 P4 covered this; here it's a **gate** in the pipeline (block training if any single-feature AUC > 0.95).

**Follow-ups.** Time-shifted feature checks: train on day N features, score against day N+30 labels.

---

### Problem 24 — dbt schema test for a feature view

**Solution.**
```yaml
# models/schema.yml
models:
  - name: user_features
    description: Aggregated user features for churn modeling.
    columns:
      - name: user_id
        tests:
          - not_null
          - unique
      - name: country
        tests:
          - accepted_values:
              values: ["US","UK","FR","DE"]
      - name: purchase_count_30d
        tests:
          - dbt_utils.expression_is_true:
              expression: ">= 0"
      - name: signup_date
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: "<= current_date"
```

`dbt build` runs models then tests; failures halt downstream.

**Real-world.** Putting tests in dbt closes the loop with the data team — they see and fix issues at their layer.

**Follow-ups.** Custom tests (SQL) for business rules. Freshness checks (`dbt source freshness`).

---

### Problem 25 — Wrap a model with BentoML

**Solution.**
```python
import bentoml
import joblib

# save the trained model into BentoML's model store
model = joblib.load("model.joblib")
bentoml.sklearn.save_model("churn-rf", model)
```

```python
# service.py
import bentoml
from bentoml.io import JSON

runner = bentoml.sklearn.get("churn-rf:latest").to_runner()
svc = bentoml.Service("churn-svc", runners=[runner])

@svc.api(input=JSON(), output=JSON())
async def predict(payload: dict) -> dict:
    proba = (await runner.predict_proba.async_run([list(payload.values())]))[0, 1]
    return {"churn_prob": float(proba)}
```

```bash
bentoml build
bentoml containerize churn-svc:latest
docker run -p 3000:3000 churn-svc:latest
```

**Real-world.** Use BentoML when "I have a model, I want a container" is the whole story. Use FastAPI + custom Dockerfile when you need more control.

**Follow-ups.** BentoML batch inference. Triton runner for GPU.

---

### Problem 26 — Add micro-batching to a sync model service

**Solution.** (See Module 9 P36 for the full pattern.) Idea: collect requests for ≤10ms or ≤8 items, run one inference batch, fan out results. Improves GPU throughput 5-20×.

For sklearn on CPU, batching helps marginally; the win is on GPU models (LLMs, vision).

**Real-world.** vLLM, Triton, TEI all do this professionally — prefer those over a hand-rolled batcher in production.

---

### Problem 27 — Blue/green model deploy

**Solution.**
```yaml
# Two production deployments behind one Service
apiVersion: apps/v1
kind: Deployment
metadata: { name: churn-svc-blue }
spec:
  selector: { matchLabels: { app: churn, color: blue } }
  template: { metadata: { labels: { app: churn, color: blue } }, spec: { containers: [...] } }
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: churn-svc-green }
spec:
  selector: { matchLabels: { app: churn, color: green } }
  ...
---
apiVersion: v1
kind: Service
metadata: { name: churn-svc }
spec:
  selector: { app: churn, color: blue }    # ← swap to green to release
  ports: [{ port: 80, targetPort: 8080 }]
```

Roll forward by pointing `selector` to green; rollback by pointing back to blue.

**Real-world.** Combined with registry alias swap (P8), enables zero-downtime model updates.

**Follow-ups.** Canary at 5% via two services + Istio / Argo Rollouts.

---

### Problem 28 — Shadow deploy with logging

**Solution.**
```python
async def predict_with_shadow(req):
    prod = await prod_model.predict(req)
    candidate = await candidate_model.predict(req)
    log_shadow(req, prod=prod, candidate=candidate)
    return prod    # always return prod's answer to user
```

`log_shadow` writes to a queue / table for offline comparison.

**Real-world.** 1-7 days of shadow logs is enough to compare two model versions in distribution. **Never skip shadow** for any model touching revenue.

**Follow-ups.** Confidence intervals on shadow diff metrics. Auto-flag candidate as "ready for canary" when shadow agreement passes thresholds.

---

### Problem 29 — Define a serving SLO

**Solution.**
```
Availability: 99.9% over rolling 30 days
Latency:      p50 < 30 ms; p99 < 200 ms
Throughput:   500 RPS sustained
Error rate:   < 0.5% per minute
```

Express as Prometheus alerts; tie to PagerDuty when violated.

**Real-world.** SLOs come from product, not from "what looks easy." A user-facing recommendation has tighter SLO than a daily report.

**Follow-ups.** Error budgets — burn rate alarms. Multi-window multi-burn-rate alerts (Google SRE-style).

---

### Problem 30 — Compute PSI and alert on drift

**Solution.** (See §9.3 + P21.)

Pipeline:
```python
import json

def daily_drift_check(reference_df, current_df, output_path):
    report = feature_drift_report(reference_df, current_df)
    drifted = {k: v for k, v in report.items() if v["drifted"]}
    with open(output_path, "w") as f:
        json.dump(report, f)
    if drifted:
        send_slack(f"Drift detected on {len(drifted)} features: {list(drifted)[:5]}...")
    return drifted
```

Run as a daily cron; reference is the training distribution; current is yesterday's serving traffic.

**Real-world.** Don't just alert — link the alert to a runbook ("if drift detected: 1) investigate upstream change; 2) check if it's seasonal; 3) decide on retrain trigger").

**Follow-ups.** Sliding window comparisons (today vs last week). Per-segment drift detection.

---

### Problem 31 — Track delayed performance metrics

**Statement.** Predict churn today; the label arrives in 30 days.

**Solution.**
```python
# pipeline: every day, compute metrics on predictions made N days ago
def compute_delayed_metrics(prediction_date: str, label_window: int = 30):
    preds = read_predictions(date=prediction_date)        # from log table
    labels = read_labels(start=prediction_date,
                          end=add_days(prediction_date, label_window))
    df = preds.merge(labels, on="user_id", how="inner")
    return {
        "n": len(df),
        "auc": roc_auc_score(df["label"], df["prob"]),
        "brier": brier_score_loss(df["label"], df["prob"]),
    }

# run daily for 30-day-ago predictions; track over time
```

Surface as a dashboard with a confidence interval. Compare against training-time metrics.

**Real-world.** This is the closest thing to ground truth in production. Most other metrics are proxies.

**Follow-ups.** Multiple delay windows (7-day, 30-day churn signals). Trended metrics with regression lines.

---

### Problem 32 — Calibration drift

**Statement.** The model was calibrated at training; over time, calibration may drift even if AUC is stable.

**Solution.**
```python
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss

prob_true, prob_pred = calibration_curve(y_true, p_pred, n_bins=10)
ece = float(np.abs(prob_true - prob_pred).mean())   # Expected Calibration Error
print(f"Brier: {brier_score_loss(y_true, p_pred):.4f}, ECE: {ece:.4f}")
```

Track Brier and ECE weekly. Alert on a 20%+ degradation. Recalibrate (Module 7 §10.4) without retraining as a quick fix.

**Real-world.** Calibration drift breaks downstream business logic (e.g., "predict expected loss"). AUC alone can hide this.

**Follow-ups.** Per-segment calibration. Online recalibration with a rolling label window.

---

### Problem 33 — Evidently drift report

**Solution.**
```python
from evidently import Report
from evidently.presets import DataDriftPreset

report = Report(metrics=[DataDriftPreset()])
result = report.run(reference_data=train_df, current_data=prod_df)
result.save_html("drift_report.html")
result.save_json("drift_report.json")     # machine-readable for alerts
```

Schedule daily; archive HTML reports; pipe summary stats to Prometheus.

**Real-world.** Evidently's HTML is helpful for incident postmortems ("look how feature X drifted three days before the regression").

**Follow-ups.** Per-segment reports. Custom metrics (e.g., target-prediction divergence).

---

### Problem 34 — Define training-data freshness SLO

**Statement.** Your daily retrain pipeline failed for 3 days; nobody noticed.

**Fix.** Define **freshness SLO** explicitly:
- Training data: max 24h old at training time.
- Serving features: max 6h old.
- Model: retrained at least weekly (else alert).

Surface freshness as a Prometheus gauge:
```python
training_data_age_hours = (datetime.utcnow() - latest_data_ts).total_seconds() / 3600
# expose as gauge; alert when > 24
```

**Real-world.** Pipeline failures often hide because there's no signal of "missing data." Make freshness a first-class signal.

**Follow-ups.** dbt source freshness checks. Heartbeat tasks that emit "still alive" metrics.

---

### Problem 35 — Drift-triggered retrain

**Statement.** A retrain DAG runs only when feature drift exceeds a threshold.

**Solution.**
```python
# Airflow with a sensor / branching operator
from airflow.operators.python import BranchPythonOperator

def check_drift_then_branch():
    drift = compute_top_drift_score()        # e.g., max PSI across features
    return "train" if drift > 0.2 else "skip"

with DAG("drift_triggered_retrain", schedule="0 4 * * *", ...) as dag:
    drift_check = BranchPythonOperator(task_id="drift_check", python_callable=check_drift_then_branch)
    train       = PythonOperator(task_id="train",  python_callable=train_fn)
    skip        = PythonOperator(task_id="skip",   python_callable=lambda: print("no retrain needed"))

    drift_check >> [train, skip]
```

**Real-world.** Combine with scheduled retrain (weekly) so you're not solely reactive. Document why a retrain ran (drift_alert vs scheduled) — appears in the experiment tracker tags.

**Follow-ups.** Multi-level triggers (drift + performance + manual). Cooldown to prevent flapping.

---

### Problem 36 — End-to-end CI for a model promotion

**Statement.** Author a CI workflow that, on a `git tag`, trains, evaluates, registers, smoke-tests, and promotes a model — only if all gates pass.

**Solution.**
```yaml
# .github/workflows/ml-release.yml
name: ML Release
on:
  push:
    tags: ['model/*']

jobs:
  train_and_promote:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - name: Pull data
        run: dvc pull
      - name: Train
        run: python -m src.train --output run_id.txt
        env: { MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_URI }} }
      - name: Evaluate gates
        run: python -m src.gate_check --run-id $(cat run_id.txt)
      - name: Register + promote staging
        run: python -m src.promote --run-id $(cat run_id.txt) --alias staging
      - name: Smoke test against staging
        run: python -m tests.smoke_staging
      - name: Promote production
        if: success()
        run: python -m src.promote --run-id $(cat run_id.txt) --alias production
      - name: Notify Slack
        if: always()
        run: python -m src.notify --status ${{ job.status }}
```

**Real-world.** This pattern enforces gates uniformly. Nobody can "just promote" a model that didn't pass the smoke tests — even the lead engineer.

**Follow-ups.** Add canary as an intermediate alias; auto-rollback on canary metrics regression.

---

## 15. Three mini-projects

### Mini-project A — End-to-end churn pipeline with DVC + MLflow + Airflow
Take the churn dataset from Module 7. Track raw + processed data with DVC. Train via a pipeline (Airflow or Prefect). Log to MLflow with full metadata. Promote best run to staging via CI; smoke test; promote to production. Deploy with FastAPI + Docker (Modules 4+6). Add Prometheus metrics; build a Grafana dashboard.

**Skills exercised:** §2-§5, §7-§9. The full Level 2 → Level 3 stack.

### Mini-project B — Drift detection and auto-retrain
Build a daily drift-check job for the production model. Compute PSI per feature, ECE for calibration, delayed AUC against the labels arriving from 30 days ago. Alert via Slack. Add a drift-triggered retrain DAG (P35). Compare scheduled-only vs drift-triggered retrain frequency over 8 weeks.

**Skills exercised:** §9-§10. The "production keeps working" layer.

### Mini-project C — Feature store with parity checks
Define your churn features in Feast. Backfill historical features for training; serve online for realtime requests. Build a parity check (P18) that compares offline vs online for 100 random users every 15 minutes. Surface diffs to a dashboard. Document one bug you found via the parity check.

**Skills exercised:** §6, §7, §9. The most subtle production failure mode.

---

## 16. Real-world usage map

| Concept | Where it returns later |
|---|---|
| Reproducibility manifest | Module 13 (LLMOps): same idea but with prompt + retrieval index versions |
| MLflow experiment tracking | Module 13 (LLMOps): often replaced by LangSmith/Langfuse for LLM apps |
| Model registry alias swap | Module 13 (LLMOps): for fine-tuned models and prompt versions |
| Pipelines (Airflow/Prefect) | Module 13 (LLMOps): RAG pipeline orchestration; eval pipeline |
| Feature stores | Module 13 (LLMOps): retrieval / vector index versioning |
| PSI / drift detection | Module 13 (LLMOps): embedding drift, output drift |
| Calibration drift | Module 13 (LLMOps): LLM judge calibration |
| Shadow/canary deploys | Module 13 (LLMOps): same; especially important for LLM upgrades |
| Pandera / GE schema tests | Module 14 (security): data quality on threat-intel feeds |
| Continuous training triggers | Module 14 (security): detection model auto-retrain on new threat data |

---

## 17. Interview pitfalls — what NOT to say

- **"MLOps means Kubernetes."** No. Most teams need 1-3 tools, not a Kubernetes-everywhere stack.
- **"We use MLflow for everything."** Tracking ≠ pipelines ≠ registry ≠ serving. Be specific.
- **"We retrain weekly to be safe."** Without a retrain trigger justification, you're burning compute. Define when retraining helps.
- **"The model is deployed; we're done."** Without monitoring, the model dies silently.
- **"PSI > 0.2 means retrain."** PSI > 0.2 means *investigate*. Drift doesn't always mean degradation.
- **"We A/B test all models."** A/B requires sample size; for low-RPS models, shadow + offline eval is sufficient.
- **"Reproducibility means same code."** It also means same data, same config, same seed, same compute env.
- **"We use Feast."** Then describe point-in-time joins. If you can't, you're using a glorified key-value store.
- **"Airflow."** Airflow specifically how? Schedule-based, sensor-based, dynamic? "Airflow" is the answer most teams give that signals shallow knowledge.
- **"We pickle our models."** safetensors / joblib / TorchScript / ONNX — say which and why.
- **"Drift detection is hard."** It's straightforward — PSI / KS test / Wasserstein. The hard part is deciding what to do about it.
- **"Latency is fine, we tested locally."** P99 under realistic load on production hardware ≠ p99 on your laptop.

**How to communicate.** Narrate (1) reproducibility — what's versioned, how, where; (2) experiment tracking — what gets logged; (3) registry — promotion criteria + gates; (4) pipelines — orchestrator + triggers; (5) features — store or shared library; (6) serving — pattern + SLO; (7) monitoring — operational + drift + delayed performance; (8) cost — tagging + showback.

---

## 18. Cheatsheet

```text
REPRODUCIBILITY
  version: code (git), data (DVC), config (YAML), env (Docker SHA),
           seed, library deps (uv.lock), eval set (immutable)
  manifest.yaml ships with every model artifact
  uv pip compile --generate-hashes; --require-hashes on install
  seed_everything(42, deterministic=True)

EXPERIMENT TRACKING (MLflow)
  mlflow.set_experiment("name"); with mlflow.start_run() as run:
    log_params, log_metrics, log_artifact, log_model
    set_tags({code_sha, data_window, env, trigger})
  search_runs(filter_string=..., order_by=...)

MODEL REGISTRY (MLflow)
  register_model(model_uri, name) -> version
  client.set_registered_model_alias(name, "staging", version)
  load: mlflow.pyfunc.load_model("models:/name@production")
  modern: aliases, not legacy stages

PIPELINES
  Airflow:  DAG(schedule, default_args, catchup=False); op1 >> op2
  Prefect:  @flow / @task with retries, caching
  Dagster:  asset-oriented; deps emerge from function args
  always: idempotent steps; explicit inputs/outputs; retries; alerts

FEATURE STORE
  Feast: Entity, FeatureView, Source
  offline (training): get_historical_features (point-in-time correct)
  online (serving):   get_online_features (low-latency latest)
  parity check between offline and online — alert on diffs

DATA QUALITY
  Pandera schema: types + Check.in_range / Check.isin / Check.gt
  Great Expectations: suite + Data Docs HTML reports
  dbt schema tests: not_null / unique / accepted_values / freshness
  catch upstream — don't wait for production inferences to fail

SERVING DECISION
  batch:    daily, big throughput, no latency SLO
  streaming: Kafka consumer, sub-second
  online sync: REST, p99<100ms
  online async: queue + result endpoint, seconds-minutes
  embedded: edge / mobile

  tools:
    FastAPI + uvicorn:  default, well-understood
    BentoML:            Python-first, Dockerizable
    Triton:             multi-model GPU, dynamic batching
    Ray Serve:          composition, multi-node
    KServe / SageMaker: managed K8s/cloud

MONITORING (4 signals)
  operational: latency, error rate, RPS  (Prometheus + Grafana)
  input drift: PSI per feature, daily, alert at PSI > 0.2
  output drift: prediction distribution shift
  performance: AUC/Brier on delayed labels (window 7-30 days)

DRIFT METRICS
  PSI > 0.2 = significant; > 0.1 = mild
  KS / chi-squared / Wasserstein for continuous / categorical
  ECE for calibration; track weekly

DEPLOY PATTERNS
  blue/green:  swap selector for instant cutover
  canary:      5% traffic, watch metrics
  shadow:      log both; serve old; compare offline
  rolling:     gradual replacement, K8s default

CONTINUOUS TRAINING TRIGGERS
  schedule (default), data volume, drift, performance, manual
  each retrain → eval → staging → shadow → canary → production
  registry alias swap for atomic deploy

DISTRIBUTED COMPUTE
  Ray (Python actors / tune / train), Dask (DataFrames),
  Spark (only if multi-node TB-scale), Polars (single-node big data)

COST
  tag everything (env, team, project, owner)
  spot/preemptible for training; auto-stop dev notebooks
  right-size GPUs; quantize at scale
  weekly cost report per team

ANTI-PATTERNS (avoid)
  notebook-as-source-of-truth; pickle models without versions
  mismatched train-vs-serve features; one big monolith DAG
  drift alert with no owner; PSI > threshold = "ignore"
  tracking one metric only; test set used during tuning
  no rollback plan; SLO not defined; pipeline freshness invisible
```

---

## 19. Prerequisites & next steps

**Prerequisites covered? You can:**
- Build a reproducibility manifest and version code + data + config + seeds.
- Track experiments in MLflow with full metadata; query and promote runs.
- Use a model registry with aliases for staging/production; reload models without redeploys.
- Author pipelines in Airflow / Prefect / Dagster with retries, idempotency, and triggers.
- Define feature stores and ensure point-in-time correctness.
- Validate data with Pandera / Great Expectations / dbt; catch leakage at training.
- Pick a serving pattern (batch, sync, async, streaming, embedded) and the right tool (FastAPI, BentoML, Triton, Ray Serve).
- Monitor operational, drift, and delayed performance signals; respond to drift.
- Set up continuous training with multiple triggers and gate-driven deploys.
- A/B, shadow, canary deploy ML models without breaking production.
- Track ML cost and apply FinOps practices.

**Next steps in the bible:**
- **Module 13 — LLMOps.** The same patterns specialized for LLM apps: prompt management, eval pipelines, RAG monitoring, cost tracking per token.
- **Module 14 — Security automation.** Many of these patterns reapplied to security data flows (SIEM/EDR/MISP).

**External study (only if you want depth):**
- *Designing Machine Learning Systems* (Chip Huyen, 2022) — the practitioner reference; still current.
- *Machine Learning Design Patterns* (Lakshmanan, Robinson, Munn) — solid catalog of patterns.
- *Reliable Machine Learning* (Cathy Chen et al., O'Reilly) — production-focused.
- The MLflow, DVC, Feast, Evidently docs — read primary sources for tool details.

---

*End of Module 12. Module 13 covers LLMOps — prompt management, observability, eval pipelines, cost/latency tracking, RAG monitoring — same structure, 36 problems.*
