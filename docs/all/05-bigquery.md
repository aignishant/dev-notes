# Module 5 — BigQuery & Data Warehousing

> **Bible Module 5 of 14.** Self-contained. Written for **Google BigQuery (current as of 2026), `google-cloud-bigquery 3.x`, `pandas-gbq 0.22+`, `bigframes 1.x`, dbt-bigquery 1.7+**. Assumes Modules 1–4. SQL examples use BigQuery's GoogleSQL dialect; analytic patterns transfer 1:1 to Snowflake, Redshift, and DuckDB with minor syntax differences.

---

## 0. Goal, reader, and how to use this module

**Goal.** After this module you can: design a BigQuery dataset for analytics; write SQL that costs \$1 instead of \$100; partition and cluster tables correctly; query BQ from Python with the right tool for the job (client lib, pandas-gbq, or BigFrames); load batch and streaming data; reason about slots, BI Engine, and materialized views; and connect BigQuery into ML pipelines for both training data extraction and inference output.

**Target reader.** Modules 1–3 done. SQL knowledge from Module 3 transfers — most of what's new here is the warehouse mental model (columnar, distributed, pay-per-byte) and BigQuery-specific features (ARRAY/STRUCT, partitioning, slot-based pricing).

**How to use it.** Same as before. Do all 36 problems before reading the solutions.

**Prerequisites.** Modules 1 (Python), 3 (SQL).
**Next steps.** Module 6 (Cloud foundations — IAM, networking, deploys), Module 7 (Classical ML — features often live in BQ), Module 12 (MLOps).

---

## 1. The warehouse landscape

Transactional databases (Module 3) and warehouses are different beasts. Knowing why prevents wrong-tool choices that haunt teams for years.

| | OLTP (MySQL, Postgres) | OLAP / Warehouse (BigQuery, Snowflake) |
|---|---|---|
| Storage | Row-oriented | **Column-oriented** |
| Workload | Lots of small reads/writes (single rows, by key) | Few huge reads (scan billions of rows, aggregate) |
| Latency target | < 10ms | seconds to minutes |
| Concurrency | thousands of users | tens to hundreds of analyst queries |
| Pricing model | Hourly server cost | Per-query bytes scanned OR slot reservations |
| Schema flexibility | Strict | Flexible (nested types, late-binding JSON) |
| Indexes | B-tree indexes | **No traditional indexes** — partition + cluster instead |
| Tx semantics | Full ACID | Limited (multi-statement scripts, no general row locks) |

**Use BigQuery for:** analytics, reporting, ML feature pipelines, data lake querying, ad-hoc exploration on billions of rows.
**Don't use it for:** the primary store of an OLTP app, single-row lookups by key (use BigQuery Lookup Tables / Bigtable for that), or anything needing millisecond latency.

### 1.1 BigQuery vs the alternatives

| | BigQuery | Snowflake | Redshift | ClickHouse | DuckDB |
|---|---|---|---|---|---|
| Hosting | GCP only | Multi-cloud | AWS only | Self-host or Cloud | **Embedded** (in your process) |
| Pricing | Per-query OR slots | Per-second compute | Per-hour cluster | Per-instance | Free |
| Storage | Decoupled (cheap) | Decoupled | Coupled (older) / RA3 decoupled | Tighter coupling | Single file |
| Best for | "Just query, never manage infra" | Multi-cloud, strong perf | AWS-centric | Real-time, sub-second | Local analytics on parquet |

In 2026 the practical choice is usually Snowflake or BigQuery. **BigQuery** edges ahead when: you're already on GCP; you want truly serverless (no warehouses to suspend/resume); you need streaming inserts at high volume; you use Looker Studio or Vertex AI heavily.

---

## 2. BigQuery mental model

### 2.1 The hierarchy

```
GCP project
└── dataset (like a schema)
    ├── table
    ├── view
    ├── materialized view
    └── routine (SQL/JS UDF)
```

A fully qualified name: `` `my-project.analytics.events` ``. Backticks are required when the project ID contains hyphens (which it usually does).

### 2.2 Slots — the unit of compute

A **slot** is a virtual CPU. BigQuery breaks every query into a DAG of stages and runs each stage across many slots in parallel. You either pay per byte scanned (on-demand) or pay for a reserved slot pool (capacity / editions).

- **On-demand:** \$5 per TB scanned (varies by region; check current pricing). No commitment. Best for unpredictable loads.
- **Editions / reservations:** flat slot capacity (Standard, Enterprise, Enterprise Plus). Predictable cost; queries can use up to your reservation.

This pricing model dictates **everything** about how you write queries. We'll come back to it constantly.

### 2.3 Storage

Storage is **always** decoupled from compute. You pay separately for:
- **Active storage** (~\$0.02/GB/month) — tables modified in last 90 days.
- **Long-term storage** (~\$0.01/GB/month) — automatically applied after 90 days untouched. Free.

Storage is cheap. Compute is expensive. Optimize for compute first.

### 2.4 The two SQL dialects

BigQuery has **GoogleSQL** (formerly "Standard SQL," default since 2017) and **Legacy SQL** (deprecated). Always use GoogleSQL. If you see queries with `[my-project:dataset.table]` or no backticks, those are legacy — modernize them.

---

## 3. Storage internals — partitioning and clustering

This section is the most important in the module. Get partitioning + clustering right and your queries cost 1% of what they would otherwise.

### 3.1 Why columnar storage matters

A row store keeps rows together: `(id1, name1, age1, dept1) (id2, name2, age2, dept2) ...`. A column store keeps columns together: `(id1, id2, ...) (name1, name2, ...) (age1, age2, ...)`.

Consequence: `SELECT AVG(salary) FROM employees` on a column store reads only the `salary` column from disk. On a row store, it reads every byte. For wide tables with selective queries, column stores are often 10–100× faster and cheaper.

**Rule:** never `SELECT *` in BigQuery on tables that matter. Always specify columns.

### 3.2 Partitioning

A partitioned table is internally split into segments by a column's value (typically a date). A query that filters on the partition column reads only matching partitions.

```sql
CREATE TABLE `my-project.analytics.events`
(
    user_id INT64,
    event_type STRING,
    payload JSON,
    event_ts TIMESTAMP
)
PARTITION BY DATE(event_ts)
OPTIONS (
    partition_expiration_days = 365,
    require_partition_filter = TRUE       -- BLOCKS queries without a partition filter
);
```

```sql
-- this scans ONE partition
SELECT COUNT(*) FROM `my-project.analytics.events`
WHERE DATE(event_ts) = '2026-04-27';

-- this scans ALL partitions — and is REJECTED at parse time if require_partition_filter is set
SELECT COUNT(*) FROM `my-project.analytics.events`;
```

**Partition column choices:**
- `DATE(timestamp)` — by far the most common.
- Integer range — for numeric keys (rarely useful).
- Ingestion time — partitions by when the row was loaded (`_PARTITIONTIME` pseudo-column). Use when you don't have a natural date column.

**Non-negotiable rule:** every analytical fact table should be partitioned. Set `require_partition_filter = TRUE` on production tables — it forces every query to declare its partition range, preventing the multi-thousand-dollar accidental scan.

### 3.3 Clustering

Clustering sorts data within each partition by one or more columns. Filters on cluster columns let BigQuery skip blocks within the partition — essentially a coarse index.

```sql
CREATE TABLE `my-project.analytics.events`
(...)
PARTITION BY DATE(event_ts)
CLUSTER BY user_id, event_type;
```

Now this is fast and cheap:
```sql
SELECT * FROM `my-project.analytics.events`
WHERE DATE(event_ts) = '2026-04-27'
  AND user_id = 42;
-- partition narrows to one day; clustering narrows within the day
```

**Clustering rules:**
- Up to 4 columns per cluster spec.
- Order matters — filter on the leftmost column for full benefit (similar to composite indexes in §3 of Module 3).
- High-cardinality columns (`user_id`, `session_id`) cluster best.
- Low-cardinality columns (`country`, `device_type`) help less but are still useful when they're often filtered.
- Clustering rebuilds itself in the background — no DBA work.

### 3.4 The cost-vs-cardinality table

| | Don't partition | Partition by date | Partition + cluster |
|---|---|---|---|
| Daily query (1% data) | Scans 100% | Scans 1% | Scans 1% |
| Single-user query | Scans 100% | Scans 100% (no date filter helps) | **Scans <0.01%** |
| Cost ratio (typical) | 1× | ~0.01× | ~0.0001× |

Partitioning + clustering compose. Both are free to set; you pay only at write time (a small metadata cost).

### 3.5 What replaces an index

Coming from Postgres? In BigQuery you usually do **not** need indexes. Partitioning + clustering covers 90% of the cases. The remaining 10%: BQ has **search indexes** for `SEARCH(...)` text matching and **vector indexes** (introduced 2024) for similarity search. Use them only when the query plan tells you to.

---

## 4. SQL in BigQuery — what's different

### 4.1 The dialect basics

GoogleSQL is ANSI-compatible plus enhancements. From Module 3 SQL, `SELECT/JOIN/GROUP BY/window functions/CTEs/recursive CTEs` all work the same.

**Useful extensions you'll use constantly:**

```sql
-- QUALIFY — filters on window-function output (cleaner than wrapping in a subquery)
SELECT user_id, event_type, ts,
       ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY ts DESC) AS rn
FROM events
QUALIFY rn = 1;                     -- last event per user

-- EXCEPT / REPLACE — projection helpers
SELECT * EXCEPT (password_hash, internal_token)
FROM users;

SELECT * REPLACE (LOWER(email) AS email)
FROM users;

-- safe casting and division
SAFE_CAST(s AS INT64)               -- returns NULL on failure (instead of error)
SAFE_DIVIDE(a, b)                   -- returns NULL on division by zero

-- date math
DATE_TRUNC(date, MONTH), DATE_DIFF(d1, d2, DAY), DATE_ADD(d, INTERVAL 7 DAY)
TIMESTAMP_TRUNC, TIMESTAMP_DIFF, TIMESTAMP_ADD
```

### 4.2 ARRAY and STRUCT — the killer feature

BigQuery natively stores nested data. This is rare in OLTP but normal in event streams (a single event has multiple items).

```sql
-- a row with nested data
SELECT
    'order_1' AS order_id,
    [STRUCT('Pen' AS name, 2 AS qty), STRUCT('Pad' AS name, 1 AS qty)] AS items;
```

Output:
```
order_id  items
order_1   [{name=Pen, qty=2}, {name=Pad, qty=1}]
```

To query nested data, **UNNEST**:

```sql
-- one row per (order, item)
SELECT order_id, item.name, item.qty
FROM orders, UNNEST(items) AS item;
```

**Rule of thumb:** model "list of related things per parent" as `ARRAY<STRUCT<...>>` instead of a separate child table when the children are queried with the parent. This avoids JOINs entirely and is enormously cheaper at scale.

```sql
-- aggregate inside the array, no GROUP BY needed
SELECT order_id,
       (SELECT SUM(qty) FROM UNNEST(items)) AS total_items,
       ARRAY_LENGTH(items) AS line_count
FROM orders;
```

### 4.3 JSON type

For genuinely schema-flexible payloads:

```sql
SELECT
    payload.user_id AS user_id,
    JSON_VALUE(payload, '$.event.type') AS event_type,
    JSON_QUERY_ARRAY(payload, '$.tags') AS tags
FROM events;
```

`JSON_VALUE` extracts a scalar; `JSON_QUERY` extracts a JSON sub-tree; `JSON_QUERY_ARRAY` extracts and unnests an array. Use the typed `JSON` column type (not `STRING`) — it's compressed and queries faster.

**Trade-off.** Native columns are cheaper to scan than JSON paths. If a JSON field is queried often, promote it to a real column.

### 4.4 Approximate aggregations

Exact aggregations on billions of rows are expensive. For analytics, approximate is usually fine and 10× cheaper.

```sql
-- approximate count distinct (HyperLogLog++)
SELECT APPROX_COUNT_DISTINCT(user_id) FROM events;     -- vs COUNT(DISTINCT)

-- approximate quantiles
SELECT APPROX_QUANTILES(latency_ms, 100)[OFFSET(95)] AS p95
FROM api_logs;

-- approx top counts (sketches)
SELECT APPROX_TOP_COUNT(country, 10) FROM users;

-- save sketches for later combining (very useful for daily roll-ups)
SELECT day, HLL_COUNT.INIT(user_id) AS sketch FROM events GROUP BY day;
```

`HLL_COUNT.INIT` produces a sketch you can `MERGE` later — perfect for "approximate distinct users over arbitrary time windows" without re-scanning raw events.

### 4.5 Window functions go further

All Module 3 window functions work; BigQuery adds more:

```sql
-- LAG / LEAD / FIRST_VALUE / LAST_VALUE / NTH_VALUE
SELECT user_id, ts,
       ts - LAG(ts) OVER (PARTITION BY user_id ORDER BY ts) AS gap,
       FIRST_VALUE(ts) OVER (PARTITION BY user_id ORDER BY ts
                             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS first_seen
FROM events;
```

### 4.6 Pivot / unpivot built-in

BigQuery has native PIVOT (much cleaner than the conditional aggregation pattern from Module 3):

```sql
SELECT * FROM (
    SELECT month, category, amount FROM orders
)
PIVOT (SUM(amount) FOR category IN ('A','B','C'));
```

UNPIVOT goes the other way — wide to long.

---

## 5. Loading data into BigQuery

Five common patterns:

### 5.1 Batch from GCS — the standard

The fastest way to load large data. BQ reads from Cloud Storage in parallel.

```python
from google.cloud import bigquery
client = bigquery.Client()

job = client.load_table_from_uri(
    source_uris="gs://my-bucket/events/2026-04-27/*.parquet",
    destination="my-project.analytics.events",
    job_config=bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        time_partitioning=bigquery.TimePartitioning(field="event_ts", type_="DAY"),
        clustering_fields=["user_id", "event_type"],
        # autodetect schema if needed:
        # autodetect=True,
    ),
)
job.result()                    # blocks until done
print(f"Loaded {job.output_rows} rows")
```

**Format choice:**
- **Parquet** — preferred for new pipelines. Columnar, fastest, supports nested types.
- **Avro** — second choice for streaming. Strong schema, splittable.
- **JSON / CSV** — works but slower. Use only when source is already in this format.

### 5.2 Streaming inserts (Storage Write API)

For low-latency event ingest. Modern API is the **Storage Write API** (formerly the legacy `tabledata.insertAll`).

```python
from google.cloud import bigquery_storage_v1
from google.cloud.bigquery_storage_v1 import types, writer
from google.protobuf import descriptor_pb2

# pre-defined proto schema
client = bigquery_storage_v1.BigQueryWriteClient()
parent = client.table_path(PROJECT, DATASET, TABLE)
write_stream = types.WriteStream(type_=types.WriteStream.Type.COMMITTED)
stream = client.create_write_stream(parent=parent, write_stream=write_stream)

# (build proto rows; append; commit)
# In practice — use bigframes.streaming, dataflow, or pubsub-to-bq subscriptions for production.
```

For most teams: don't roll this yourself. Use a Pub/Sub subscription with a BigQuery destination, Dataflow, or Datastream — they handle batching, retries, and exactly-once semantics.

### 5.3 Federated queries (no load at all)

BigQuery can query GCS files, Cloud SQL, Spanner, and others directly. Often the right move for one-time analyses.

```sql
-- query parquet directly from GCS
CREATE EXTERNAL TABLE my_project.analytics.staging_events
OPTIONS (
    format = 'PARQUET',
    uris = ['gs://my-bucket/events/*.parquet']
);

SELECT COUNT(*) FROM my_project.analytics.staging_events;
```

External tables don't get the full performance of native tables (no clustering, partial partitioning). For ongoing workloads, load into native; use external for ad-hoc exploration.

### 5.4 BigLake tables — the modern hybrid

BigLake combines external storage with BQ's governance and (with caching) much of the performance. Strong choice for a lakehouse architecture: data lives in GCS as parquet/iceberg; BigLake makes it queryable from BigQuery without a copy.

### 5.5 INSERT INTO from a query

```sql
INSERT INTO `my-project.analytics.daily_summary`
SELECT day, country, COUNT(*) AS n_events
FROM `my-project.analytics.events`
WHERE DATE(event_ts) = CURRENT_DATE()
GROUP BY day, country;
```

For ETL inside BigQuery — common pattern in dbt models (§10).

---

## 6. The cost model — and how to tame it

### 6.1 The cardinal rule

> **You pay for bytes scanned, not bytes returned.**

A query that reads 1 TB and returns 10 rows costs the same as one that reads 1 TB and returns a million rows. The lever you control is **what gets read** — that's why §3 (partition + cluster) is the main cost story.

### 6.2 Five practical cost killers

#### 1. Partition filter — every time
```sql
-- Without (scans everything from beginning of time):
SELECT COUNT(*) FROM events WHERE user_id = 42;

-- With (scans one day):
SELECT COUNT(*) FROM events
WHERE DATE(event_ts) = '2026-04-27' AND user_id = 42;
```

#### 2. Specify columns
```sql
-- Reads ALL columns (potentially 50 GB of unused JSON):
SELECT * FROM events WHERE ...;

-- Reads only needed columns:
SELECT user_id, event_type FROM events WHERE ...;
```

#### 3. Use materialized views for hot summaries

A materialized view is precomputed and incrementally refreshed:
```sql
CREATE MATERIALIZED VIEW analytics.daily_active_users
AS
SELECT DATE(event_ts) AS day, APPROX_COUNT_DISTINCT(user_id) AS dau
FROM analytics.events
GROUP BY day;
```

Subsequent queries on the MV are nearly free. BQ also auto-rewrites compatible queries against the underlying table to use the MV ("smart tuning").

#### 4. Approximate functions
`APPROX_COUNT_DISTINCT` is ~10× cheaper than `COUNT(DISTINCT)` and within 1–2% on typical distributions. For dashboards, use approximate.

#### 5. The dry-run discipline
Before running anything expensive:

```python
job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
job = client.query(query, job_config=job_config)
print(f"Estimated bytes processed: {job.total_bytes_processed / 1e9:.2f} GB")
```

In the BigQuery UI, the byte estimate appears in the top-right before you click Run. Make this a habit.

### 6.3 Cost controls (governance)

- **Custom query quotas** per user/project (daily byte cap).
- **Maximum bytes billed** on a query — fails if it would exceed, instead of running and billing.
- **Reservation slot caps** for Editions — even if a single query is huge, your bill is bounded by your reservation.
- **`require_partition_filter`** on hot tables — prevents accidental full scans.

```python
job_config = bigquery.QueryJobConfig(
    maximum_bytes_billed=10 * 1024 * 1024 * 1024     # 10 GB cap; query fails if exceeded
)
client.query(sql, job_config=job_config)
```

### 6.4 On-demand vs Editions — which to pick

- **On-demand:** good when usage is bursty or unpredictable. \$5/TB scanned. No reservation overhead.
- **Editions (Standard/Enterprise/Enterprise Plus):** flat slot pool. Predictable cost. Better for steady, high-volume workloads (typically once you cross ~\$2k/month on-demand).

Check current pricing in the GCP console — these numbers move. The decision logic doesn't.

---

## 7. Performance — partitioning, clustering, slots, query plans

### 7.1 The query plan

In the BQ UI, every query has an "Execution details" tab with a stage-by-stage DAG. Each stage shows:
- Slot-ms consumed (the unit of compute work).
- Records read / written.
- Wait/read/compute/write timing.

When tuning, look at:
- **Wait** time — slot starvation (you need more reservation or off-peak scheduling).
- **Records read** — should match your partition + cluster pruning. If too high, your filters aren't being applied at the storage level.
- **Slot-ms skew across workers** — one slow stage = a hot key, common with `JOIN` or `GROUP BY` on a skewed column.

### 7.2 Materialized views — when they help

MVs work for **deterministic aggregations** that you query repeatedly with consistent grouping. They don't work for:
- Window functions (mostly).
- Non-deterministic functions (`CURRENT_TIMESTAMP()`, `RAND()`).
- Outer joins (limited).

Always check: `bq show --view my_project:dataset.mv` shows last refresh time and size.

### 7.3 BI Engine

BI Engine is an in-memory cache for BigQuery. With BI Engine reservation, queries from Looker / Looker Studio (and in many cases programmatic queries) hit RAM and return in <1 second. Pricing: per GB-hour of memory reserved. Worth it for high-traffic dashboards.

### 7.4 Stored procedures and scripting

```sql
-- multi-statement procedural SQL — useful for ETL scripts
DECLARE start_date DATE DEFAULT DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY);

BEGIN
    DELETE FROM analytics.summary
    WHERE day >= start_date;

    INSERT INTO analytics.summary
    SELECT DATE(event_ts) AS day, COUNT(*) AS n
    FROM analytics.events
    WHERE DATE(event_ts) >= start_date
    GROUP BY day;
END;
```

For nontrivial pipelines, prefer **dbt** (§10) over scripting in raw BQ — version-controlled, testable, lineage-aware.

### 7.5 UDFs (user-defined functions)

```sql
-- SQL UDF
CREATE TEMP FUNCTION grade(score FLOAT64) RETURNS STRING AS (
    CASE WHEN score >= 90 THEN 'A'
         WHEN score >= 75 THEN 'B'
         ELSE 'C' END
);

-- JavaScript UDF (slower; use SQL if possible)
CREATE TEMP FUNCTION title_case(s STRING) RETURNS STRING
LANGUAGE js AS r"""
    return s.replace(/\w\S*/g, t => t.charAt(0).toUpperCase() + t.substr(1).toLowerCase());
""";
```

SQL UDFs are essentially free (inlined). JavaScript UDFs cross a process boundary per row — slow on big tables. Persistent UDFs (`CREATE FUNCTION`) live in a dataset and can be reused.


---

## 8. Python client — `google-cloud-bigquery`

### 8.1 Setup and auth

```bash
uv add google-cloud-bigquery google-cloud-bigquery-storage db-dtypes
```

Authentication: prefer Application Default Credentials (ADC). Set up once with `gcloud auth application-default login` (dev) or use a service account on cloud (mounted via env or workload identity).

```python
from google.cloud import bigquery

client = bigquery.Client(project="my-project")    # uses ADC
```

### 8.2 The five operations you'll use 95% of the time

```python
# 1. Run a query and get a DataFrame
df = client.query("SELECT user_id, COUNT(*) AS n FROM `p.d.events` GROUP BY user_id LIMIT 100").to_dataframe()

# 2. Run a query with parameters (always use parameters; never f-string user input)
job = client.query(
    """SELECT * FROM `p.d.events`
       WHERE DATE(event_ts) = @day AND user_id = @uid""",
    job_config=bigquery.QueryJobConfig(query_parameters=[
        bigquery.ScalarQueryParameter("day", "DATE",  "2026-04-27"),
        bigquery.ScalarQueryParameter("uid", "INT64", 42),
    ]),
)
df = job.to_dataframe()

# 3. Load a DataFrame into a table
job = client.load_table_from_dataframe(
    df, "p.d.staging",
    job_config=bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",       # or APPEND / EMPTY
        schema=[bigquery.SchemaField("name", "STRING"), bigquery.SchemaField("score", "FLOAT64")],
    ),
)
job.result()

# 4. Load from GCS (much faster for big files; see §5.1)
client.load_table_from_uri(...).result()

# 5. Stream rows in (small batches, low latency; uses the legacy insertAll API for simplicity)
errors = client.insert_rows_json("p.d.events", [
    {"user_id": 1, "event_type": "click", "event_ts": "2026-04-27T10:00:00Z"}
])
```

### 8.3 Reading large results — use Storage Read API

For results bigger than ~100 MB, the default REST result download is slow. Use the BigQuery Storage Read API (much faster; columnar Arrow over gRPC):

```python
from google.cloud import bigquery
from google.cloud import bigquery_storage

bq = bigquery.Client()
bqstorage = bigquery_storage.BigQueryReadClient()

df = bq.query("SELECT ... FROM big_table").to_dataframe(bqstorage_client=bqstorage)
# 5–20× faster on multi-GB results
```

### 8.4 Schemas, jobs, and metadata

```python
table = client.get_table("p.d.events")
print(table.num_rows, table.num_bytes / 1e9, "GB")
for f in table.schema:
    print(f.name, f.field_type, "REPEATED" if f.mode == "REPEATED" else "")

# list jobs (debugging)
for job in client.list_jobs(max_results=10):
    print(job.job_id, job.state, getattr(job, "total_bytes_billed", None))
```

### 8.5 Async / parallel queries

The client is sync. For concurrent queries, run them in threads (queries are I/O-bound, so threads are fine):

```python
from concurrent.futures import ThreadPoolExecutor

queries = ["SELECT COUNT(*) FROM t1", "SELECT COUNT(*) FROM t2", "SELECT COUNT(*) FROM t3"]
with ThreadPoolExecutor(max_workers=10) as pool:
    results = list(pool.map(lambda q: client.query(q).to_dataframe(), queries))
```

For truly async-native code (FastAPI), use `asyncio.to_thread(client.query, sql)` — there's no first-class async client.

---

## 9. Pandas-GBQ and BigFrames — when to use which

You have three Python paths into BigQuery. Pick by use case.

| Tool | What it is | Best for |
|---|---|---|
| `google-cloud-bigquery` | Official client; results -> DataFrame | Production code, control, large jobs |
| `pandas-gbq` | Thin pandas wrapper (`read_gbq`/`to_gbq`) | Notebooks, ad-hoc pulls |
| `bigframes` | "pandas API, executes on BQ slots" | Working with TB-scale data without leaving Python |

### 9.1 pandas-gbq

```python
import pandas as pd
df = pd.read_gbq("SELECT ... FROM `p.d.t` LIMIT 1000", project_id="my-project")
df.to_gbq("p.d.scratch", project_id="my-project", if_exists="replace")
```

Pleasant for notebook work. Don't ship it in production loops — the cli library is more featureful and explicit.

### 9.2 BigFrames — pandas semantics, BigQuery scale

`bigframes` lets you write pandas code that compiles to BQ SQL. Good for: feature engineering on TB-scale data without ever materializing it locally.

```python
import bigframes.pandas as bpd

bpd.options.bigquery.project = "my-project"
bpd.options.bigquery.location = "US"

df = bpd.read_gbq("p.d.events")                    # lazy — no data pulled yet
agg = (df[df["event_ts"] >= "2026-01-01"]
         .groupby("user_id")
         .agg(n=("event_id", "count"), total=("amount", "sum")))

# only when you call .to_pandas() or .to_gbq() does compute happen
top = agg.nlargest(100, "total").to_pandas()
```

Very nice for large-scale ML feature pipelines. Note: you're paying BQ slots, not compute on your laptop.

### 9.3 Choosing

- **One-off notebook:** `pandas-gbq` is fine.
- **Production ETL:** `google-cloud-bigquery` directly + raw SQL (clearer plans, easier review).
- **Pandas-style feature engineering on big data:** `bigframes`.
- **Already on dbt:** dbt models in SQL; Python only orchestrates.

---

## 10. dbt + BigQuery — the production ETL pattern

For anything beyond a couple of scheduled queries, **use dbt**. dbt-bigquery turns SQL into version-controlled, testable, documented data products.

```sql
-- models/marts/orders_daily.sql
{{ config(
    materialized='incremental',
    partition_by={'field': 'day', 'data_type': 'date'},
    cluster_by=['country'],
    incremental_strategy='insert_overwrite'
) }}

SELECT DATE(event_ts) AS day,
       country,
       COUNT(*) AS n_orders,
       SUM(amount) AS revenue
FROM {{ ref('events_clean') }}

{% if is_incremental() %}
  WHERE DATE(event_ts) >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)   -- backfill window
{% endif %}

GROUP BY day, country
```

Why dbt is the standard:
- **Lineage** — every table knows what feeds it.
- **Tests** — `unique`, `not_null`, custom SQL tests run on each build.
- **Docs** — auto-generated catalog + lineage graph.
- **Incremental builds** — no need to rebuild yesterday's data daily.
- **Macros** — reusable SQL logic without copy-paste.

You don't need to deeply learn dbt to use BigQuery, but every team eventually adopts it (or a competitor like SQLMesh).

---

## 11. Security — IAM, RLS, CLS, and column masking

### 11.1 IAM — the baseline

BigQuery uses GCP IAM. The roles you need to know:

- `roles/bigquery.dataViewer` — read tables in a dataset.
- `roles/bigquery.dataEditor` — read + write data, can't change schema.
- `roles/bigquery.dataOwner` — full control of dataset.
- `roles/bigquery.jobUser` — run queries (separate from data access).
- `roles/bigquery.user` — run jobs *and* read metadata.
- `roles/bigquery.admin` — everything.

**Principle of least privilege.** Apps that just query: `dataViewer` + `jobUser`. ETL writers: `dataEditor` + `jobUser`. Never `admin` for service accounts.

### 11.2 Row-level security

```sql
-- only let user X see their own rows
CREATE ROW ACCESS POLICY user_owned_data
ON `p.d.orders`
GRANT TO ('user:ada@example.com')
FILTER USING (customer_email = SESSION_USER());
```

Without this, every analyst querying a multi-tenant table risks seeing all tenants. RLS pushes the filter into the table so you can't forget it.

### 11.3 Column-level security and masking

```sql
-- tag a column with a policy tag (PII)
ALTER TABLE `p.d.users`
ALTER COLUMN ssn SET OPTIONS (policy_tags=["projects/p/locations/us/taxonomies/.../policyTags/..."]);
```

Users without the right access see `NULL` (or a masked value) when they query the column. Combined with Data Catalog taxonomies, this gives you data-classification-aware queries — non-PII users can run the same queries; sensitive fields just don't return.

### 11.4 Authorized views and routines

Authorized views let you expose a *derived* dataset to users who can't see the source — a common pattern when granting external partners limited access.

---

## 12. BigQuery ML — training models in SQL

For analysts and dashboards, BQML lets you train and predict without leaving SQL. Worth knowing for two scenarios: (1) quick baseline models, (2) inference at scale on warehouse data.

```sql
-- train a logistic regression on warehouse data
CREATE OR REPLACE MODEL `p.d.churn_model`
OPTIONS (
    model_type = 'LOGISTIC_REG',
    input_label_cols = ['churned'],
    auto_class_weights = TRUE
)
AS
SELECT churned, n_logins_30d, total_spend, days_since_last_login, country
FROM `p.d.training_data`;

-- evaluate
SELECT * FROM ML.EVALUATE(MODEL `p.d.churn_model`, TABLE `p.d.test_data`);

-- predict
SELECT user_id, predicted_churned_probs
FROM ML.PREDICT(MODEL `p.d.churn_model`, TABLE `p.d.live_features`);
```

Supported model types include linear/logistic regression, k-means, time-series ARIMA, matrix factorization, boosted trees (via Vertex AI integration), DNN, and `IMPORT TF_LITE` for arbitrary ONNX/TF models. For deep models, BQML calls Vertex AI under the hood.

**Where BQML shines:** baseline models on tabular data; running inference on terabytes (no data movement). **Where it doesn't:** custom architectures, fine-tuning, anything you'd write in PyTorch.

### 12.1 Embeddings + vector search

```sql
-- generate text embeddings via a Vertex AI model
SELECT
    article_id,
    ml_generate_embedding_result AS embedding
FROM ML.GENERATE_EMBEDDING(
    MODEL `p.d.embedding_model`,
    (SELECT article_id, content AS content FROM articles)
);

-- find similar rows
SELECT *
FROM VECTOR_SEARCH(
    TABLE `p.d.article_embeddings`,
    'embedding',
    (SELECT embedding FROM `p.d.article_embeddings` WHERE article_id = 42),
    top_k => 10
);
```

For RAG and recommender pipelines (Module 10/11), this is BigQuery's native vector path. Alternatives: pgvector (Postgres), Vertex Vector Search, dedicated vector DBs.

---

## 13. Streaming patterns — Pub/Sub → BigQuery

The standard event-driven ingest:

```
producer → Pub/Sub topic → BigQuery subscription → table
```

A "BigQuery subscription" on Pub/Sub writes messages directly to a table — no Dataflow needed for simple cases. For richer transformations: Dataflow (Apache Beam) is the production standard; Dataproc Serverless is the Spark-native alternative.

For ML inference on streams: events arrive in BQ in seconds; BQML or Vertex AI scores them; predictions land in another table or Pub/Sub topic for downstream actions.

---

## 14. Anti-patterns

| Anti-pattern | Right way |
|---|---|
| `SELECT *` on big tables | Specify columns |
| Tables not partitioned | `PARTITION BY DATE(...)` from day one |
| Tables without `require_partition_filter` | Add it on production tables |
| `COUNT(DISTINCT)` for dashboards | `APPROX_COUNT_DISTINCT` |
| Joining a 1B row table to itself for window logic | Use window functions + QUALIFY |
| Modeling parent/child as two tables | `ARRAY<STRUCT<...>>` if always queried together |
| String JSON column queried often | Real columns or typed `JSON` |
| f-string user input into SQL | `bigquery.ScalarQueryParameter` |
| Loading via streaming for batch data | `load_table_from_uri` (parquet from GCS) — 100× cheaper |
| Loading CSV when source is JSON/parquet | Use the source's native format |
| Re-aggregating raw events for every dashboard | Materialized views or daily summary tables |
| `OFFSET` for huge result pagination | Use the Storage Read API and stream rows |
| Running expensive query without dry-run | Always dry-run unfamiliar queries |
| Granting `bigquery.admin` to apps | `dataViewer` + `jobUser` is usually enough |
| Manually scripted procedural SQL | dbt models with tests and lineage |
| Cross-region datasets | Co-locate data and queries; cross-region transfers add cost |
| One huge table, no clustering | Partition + cluster on actual filter columns |

---

## 15. Thirty-six problems (with full structure)

Each problem follows: **Statement → Intuition → Brute force → Optimized → Complexity → Edge cases → Real-world → Follow-ups.**
**Section breakdown:** 8 BigQuery SQL fundamentals (P1–P8), 6 ARRAY/STRUCT/JSON (P9–P14), 5 Partitioning/Clustering (P15–P19), 4 Cost control (P20–P23), 5 Python client / loading (P24–P28), 4 Performance tuning (P29–P32), 4 BQML / advanced (P33–P36).

---

### Problem 1 — Top-N per group with QUALIFY

**Statement.** From `events(user_id, event_ts, event_type)`, return the most recent event per user.

**Solution.**
```sql
SELECT user_id, event_ts, event_type
FROM `p.d.events`
WHERE DATE(event_ts) BETWEEN '2026-04-01' AND '2026-04-30'
QUALIFY ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY event_ts DESC) = 1;
```

**Why QUALIFY.** Module 3 required wrapping in a CTE to filter on a window-function output. BigQuery's `QUALIFY` does it inline — cleaner and the planner sees through it.

**Real-world.** Dashboard "last login per user," last purchase per customer, latest snapshot per entity.

**Follow-ups.** Top-3 per user (`<= 3`). Last event of each type per user (`PARTITION BY user_id, event_type`). Time-decay weighted "most relevant" event.

---

### Problem 2 — DAU / MAU with HyperLogLog sketches

**Statement.** Compute daily active users and 30-day rolling DAU without re-scanning raw events each day.

**Solution.**
```sql
-- Stage 1: nightly sketch per day (write to a small sketch table)
CREATE OR REPLACE TABLE `p.d.dau_sketches`
PARTITION BY day AS
SELECT DATE(event_ts) AS day, HLL_COUNT.INIT(user_id) AS sketch
FROM `p.d.events`
WHERE DATE(event_ts) BETWEEN '2026-01-01' AND CURRENT_DATE()
GROUP BY day;

-- Stage 2: query rolling 30-day distinct users from sketches (cheap)
SELECT day,
       HLL_COUNT.MERGE(sketch) OVER (
           ORDER BY day
           ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
       ) AS users_30d
FROM `p.d.dau_sketches`
ORDER BY day;
```

**Why it matters.** Raw `COUNT(DISTINCT)` on a sliding window scans every event in the window every day. Sketches reduce that to per-day write + tiny merge — typically 100× cheaper.

**Real-world.** Standard pattern for product analytics at scale.

**Follow-ups.** WAU/MAU from the same sketches. Stick a materialized view on the sketches for instant queries. Per-cohort sketches.

---

### Problem 3 — Event-funnel analysis

**Statement.** Of users who did `view_product` on day D, what fraction did `add_to_cart` and then `checkout` within 7 days?

**Solution.**
```sql
WITH steps AS (
  SELECT user_id, DATE(event_ts) AS day, event_type, MIN(event_ts) AS first_ts
  FROM `p.d.events`
  WHERE DATE(event_ts) BETWEEN '2026-04-01' AND '2026-04-15'
    AND event_type IN ('view_product','add_to_cart','checkout')
  GROUP BY user_id, day, event_type
),
viewers AS (
  SELECT user_id, day AS view_day, first_ts AS view_ts
  FROM steps WHERE event_type = 'view_product'
),
funnel AS (
  SELECT v.user_id, v.view_day,
         MAX(CASE WHEN s.event_type='add_to_cart' AND s.first_ts BETWEEN v.view_ts AND TIMESTAMP_ADD(v.view_ts, INTERVAL 7 DAY) THEN 1 ELSE 0 END) AS cart,
         MAX(CASE WHEN s.event_type='checkout'    AND s.first_ts BETWEEN v.view_ts AND TIMESTAMP_ADD(v.view_ts, INTERVAL 7 DAY) THEN 1 ELSE 0 END) AS checkout
  FROM viewers v
  LEFT JOIN steps s ON s.user_id = v.user_id
  GROUP BY v.user_id, v.view_day
)
SELECT view_day,
       COUNT(*) AS viewers,
       SAFE_DIVIDE(SUM(cart), COUNT(*))     AS cart_rate,
       SAFE_DIVIDE(SUM(checkout), COUNT(*)) AS checkout_rate
FROM funnel
GROUP BY view_day
ORDER BY view_day;
```

**Real-world.** Every product analytics dashboard. The 7-day window must be expressed in SQL — counting events per user without time guards is a classic source of inflated funnel numbers.

**Follow-ups.** Multi-touch attribution. Cohorted funnel (signup-week cohorts). First-time-buyer funnels.

---

### Problem 4 — Sessionization with LAG and SUM-over

**Statement.** Group user events into sessions where ≥30 minutes between events starts a new session.

**Solution.**
```sql
WITH gaps AS (
  SELECT user_id, event_ts,
         TIMESTAMP_DIFF(event_ts, LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts), MINUTE) AS gap_min
  FROM `p.d.events`
  WHERE DATE(event_ts) = '2026-04-27'
),
session_starts AS (
  SELECT user_id, event_ts,
         CASE WHEN gap_min IS NULL OR gap_min >= 30 THEN 1 ELSE 0 END AS is_new
  FROM gaps
),
sessions AS (
  SELECT user_id, event_ts,
         SUM(is_new) OVER (PARTITION BY user_id ORDER BY event_ts) AS session_id
  FROM session_starts
)
SELECT user_id, session_id,
       MIN(event_ts) AS started_at,
       MAX(event_ts) AS ended_at,
       COUNT(*) AS n_events
FROM sessions
GROUP BY user_id, session_id;
```

**Why "running sum of gap markers" gives a session ID.** Every gap >= 30 min adds 1; everything else adds 0. The running sum stays constant within a session and bumps at boundaries.

**Real-world.** Web analytics, app analytics, IoT devices. A standard interview question.

**Follow-ups.** Per-session metrics (events, duration, conversion). Multiple gap thresholds. Idle vs active session distinction.

---

### Problem 5 — Slowly Changing Dimension (Type 2) — point-in-time join

**Statement.** `users_history(user_id, valid_from, valid_to, plan)` and `events(user_id, event_ts, ...)`. Enrich each event with the plan that was active at that time.

**Solution.**
```sql
SELECT e.user_id, e.event_ts, e.event_type, h.plan
FROM `p.d.events` AS e
JOIN `p.d.users_history` AS h
  ON h.user_id = e.user_id
 AND e.event_ts >= h.valid_from
 AND e.event_ts <  COALESCE(h.valid_to, TIMESTAMP('9999-12-31'))
WHERE DATE(e.event_ts) = '2026-04-27';
```

**Real-world.** Critical for revenue analytics and any audit-grade reporting — "Which plan was the user on when they made this purchase?"

**Follow-ups.** Range-join optimization (cluster on `(user_id, valid_from)`). Multi-version dimensions. Effective-date snapshots ("plan as of last day of month").

---

### Problem 6 — Pivot + UNPIVOT

**Statement.** Wide → long: `metrics(date, sales_us, sales_eu, sales_apac)` -> `(date, region, sales)`.

**Solution.**
```sql
SELECT * FROM `p.d.metrics`
UNPIVOT (sales FOR region IN (sales_us AS 'us', sales_eu AS 'eu', sales_apac AS 'apac'));
```

For long → wide:
```sql
SELECT * FROM (
  SELECT date, region, sales FROM `p.d.metrics_long`
)
PIVOT (SUM(sales) FOR region IN ('us','eu','apac'));
```

**Real-world.** ETL between data warehousing styles. Wide is friendlier for BI tools; long is friendlier for ML.

**Follow-ups.** Multiple value columns in PIVOT. Dynamic PIVOT (when columns are unknown — usually requires building SQL programmatically).

---

### Problem 7 — Recursive CTE for hierarchy

**Statement.** `categories(id, parent_id)`. Return every ancestor of a given leaf category.

**Solution.**
```sql
WITH RECURSIVE chain AS (
  SELECT id, parent_id, 1 AS depth
  FROM `p.d.categories`
  WHERE id = 42
  UNION ALL
  SELECT c.id, c.parent_id, ch.depth + 1
  FROM `p.d.categories` c
  JOIN chain ch ON c.id = ch.parent_id
)
SELECT * FROM chain ORDER BY depth;
```

BigQuery supports recursive CTEs since 2022. Same syntax as Postgres.

**Real-world.** Category trees, org charts, comment threads, Bills of Materials.

**Follow-ups.** All descendants of a node. Path strings for breadcrumbs. Cycle detection (limit depth).

---

### Problem 8 — DENSE_RANK with ties for fair ranking

**Statement.** Rank products by total revenue this month; ties share a rank; the next product gets the immediately next number (not skipping).

**Solution.**
```sql
SELECT product_id, total,
       DENSE_RANK() OVER (ORDER BY total DESC) AS rank
FROM (
  SELECT product_id, SUM(amount) AS total
  FROM `p.d.orders`
  WHERE DATE(created_at) BETWEEN '2026-04-01' AND '2026-04-30'
  GROUP BY product_id
);
```

**RANK vs DENSE_RANK vs ROW_NUMBER:**
- `ROW_NUMBER` = unique 1..N regardless of ties.
- `RANK` = ties share rank; next jumps (`1, 2, 2, 4`).
- `DENSE_RANK` = ties share rank; next is sequential (`1, 2, 2, 3`).

**Real-world.** Leaderboards, top-K reports. Pick the right one based on user expectation.

**Follow-ups.** Per-month ranking + change vs last month (window over month).

---

### Problem 9 — Aggregating inside an ARRAY without UNNEST

**Statement.** Order rows have `items ARRAY<STRUCT<product_id INT64, qty INT64, price NUMERIC>>`. Compute order total and item count per row.

**Solution.**
```sql
SELECT order_id,
       (SELECT SUM(qty * price) FROM UNNEST(items)) AS total,
       ARRAY_LENGTH(items) AS line_count,
       (SELECT MAX(qty) FROM UNNEST(items)) AS max_qty_per_line
FROM `p.d.orders`;
```

**Why.** Subqueries inside UNNEST stay in the row's nested context — no GROUP BY, no shuffle. ~10× faster than UNNESTing then re-grouping by `order_id`.

**Real-world.** Order rollups, log-payload metrics, anything modeled as parent + children in one row.

**Follow-ups.** Find products that appear in more than 3 orders. Aggregate per product across all orders.

---

### Problem 10 — UNNEST with OFFSET for positional access

**Statement.** Find orders where the first item is "PEN-001".

**Solution.**
```sql
SELECT order_id
FROM `p.d.orders`, UNNEST(items) AS item WITH OFFSET pos
WHERE pos = 0 AND item.product_id = 'PEN-001';
```

`WITH OFFSET` exposes the array index. Indispensable when order matters (e.g., cart sequence, page navigation paths).

**Real-world.** Path analysis, "first/last touch" attribution, ordered enrollment steps.

**Follow-ups.** Find arrays where item N matches. Trim arrays to first K items (`SELECT ARRAY_AGG(item ORDER BY pos LIMIT 5) FROM UNNEST(items) AS item WITH OFFSET pos`).

---

### Problem 11 — Pivot dynamic event types into columns

**Statement.** Events have varied `event_type`. For each user, columns: count of view, click, purchase.

**Solution (PIVOT).**
```sql
SELECT * FROM (
  SELECT user_id, event_type
  FROM `p.d.events`
  WHERE DATE(event_ts) = '2026-04-27'
)
PIVOT (COUNT(*) AS n FOR event_type IN ('view','click','purchase'));
```

If event types are unknown ahead of time, you must build the SQL programmatically — BigQuery doesn't have native dynamic pivot.

**Real-world.** Feature engineering for ML — one feature per event type per user.

**Follow-ups.** Per-day per-user matrix (add `day` to outer SELECT). Time-decayed counts.

---

### Problem 12 — Build an ARRAY<STRUCT> from joined tables

**Statement.** Join `orders` and `order_lines`; produce one row per order with `items ARRAY<STRUCT<product_id, qty>>`.

**Solution.**
```sql
SELECT o.order_id, o.created_at,
       ARRAY_AGG(STRUCT(l.product_id, l.qty) ORDER BY l.line_no) AS items
FROM `p.d.orders` o
JOIN `p.d.order_lines` l USING (order_id)
GROUP BY o.order_id, o.created_at;
```

**Real-world.** Denormalizing for analytics — collapse parent + children into one row that's cheap to scan. The reverse of "starting from normalized OLTP."

**Follow-ups.** Same with `STRUCT` of computed fields (line totals). Filter children before aggregating (`ARRAY_AGG(... IGNORE NULLS)`).

---

### Problem 13 — JSON_VALUE vs JSON_QUERY

**Statement.** A `payload JSON` column holds shapes like `{"event":"click","target":{"id":42,"label":"Buy"},"tags":["a","b"]}`. Extract `event` (scalar), `target` (object), `tags` (array of strings).

**Solution.**
```sql
SELECT
    JSON_VALUE(payload, '$.event')                 AS event_name,        -- STRING scalar
    JSON_QUERY(payload, '$.target')                AS target_json,       -- JSON object
    JSON_VALUE(payload, '$.target.id')             AS target_id,         -- nested scalar
    JSON_QUERY_ARRAY(payload, '$.tags')            AS tag_array,         -- ARRAY<JSON>
    (SELECT ARRAY_AGG(JSON_VALUE(t)) FROM UNNEST(JSON_QUERY_ARRAY(payload, '$.tags')) AS t) AS tags
FROM `p.d.events`;
```

**Three rules:**
- `JSON_VALUE` for scalars (returns STRING — cast as needed: `SAFE_CAST(JSON_VALUE(payload,'$.target.id') AS INT64)`).
- `JSON_QUERY` for objects/arrays.
- `JSON_QUERY_ARRAY` to get an array you can UNNEST.

**Real-world.** Late-binding schema in event streams; webhook payloads; product event tracking.

**Follow-ups.** Promote frequently-queried JSON paths to real columns. Generate columns at load time. Schema-on-read tradeoffs.

---

### Problem 14 — STRUCT comparison and grouping

**Statement.** Group orders by their entire shipping address (a STRUCT). Count duplicates.

**Solution.**
```sql
SELECT shipping_address, COUNT(*) AS n_orders
FROM `p.d.orders`
GROUP BY shipping_address;        -- whole struct as a key
```

Yes, BigQuery groups by STRUCT directly. Equality is field-by-field including nulls.

**Real-world.** Deduplication of multi-field keys; clustering by composite values; address normalization.

**Follow-ups.** Group by hashed STRUCT (`FARM_FINGERPRINT(TO_JSON_STRING(shipping_address))`) when STRUCT contains nested arrays (which can't be grouped directly).

---

### Problem 15 — Partition-pruned query (and the dry-run test)

**Statement.** A 10TB events table is partitioned by `DATE(event_ts)`. Confirm a query reads only one day.

**Solution.**
```python
from google.cloud import bigquery
client = bigquery.Client()

sql = """SELECT COUNT(*) FROM `p.d.events` WHERE DATE(event_ts) = '2026-04-27'"""

# Dry run — no compute, just an estimate
job = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
print(f"Will scan: {job.total_bytes_processed / 1e9:.2f} GB")

# A non-pruned variant (proves the point)
sql_bad = """SELECT COUNT(*) FROM `p.d.events`"""
job2 = client.query(sql_bad, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
print(f"Without filter: {job2.total_bytes_processed / 1e9:.2f} GB")    # ~1000× larger
```

**Real-world.** Always dry-run unfamiliar queries before running them. Make the byte estimate a habit you scan in the BQ UI before clicking Run.

**Follow-ups.** Add `maximum_bytes_billed` as a hard cap. Use `_PARTITIONTIME` for ingestion-time partitions.

---

### Problem 16 — Force partition filter to prevent accidents

**Statement.** Set up a fact table that *cannot* be queried without a partition filter.

**Solution.**
```sql
CREATE OR REPLACE TABLE `p.d.events`
(
    user_id INT64, event_type STRING, event_ts TIMESTAMP, payload JSON
)
PARTITION BY DATE(event_ts)
CLUSTER BY user_id, event_type
OPTIONS (
    partition_expiration_days = 730,
    require_partition_filter = TRUE
);
```

Now `SELECT COUNT(*) FROM ... events` errors at parse time:
> Cannot query over table 'p.d.events' without a filter over column(s) 'event_ts' that can be used for partition elimination.

**Real-world.** Mandatory on production fact tables. Saves real money — every team has a "I forgot the filter" \$1k story.

**Follow-ups.** Combine with custom quotas. View on top to enforce per-user partition limits.

---

### Problem 17 — Add clustering to an existing huge table

**Statement.** Existing 10TB partitioned table is slow when filtering by `user_id`. Add clustering without re-loading.

**Solution.**
```sql
ALTER TABLE `p.d.events`
SET OPTIONS (clustering_fields = ['user_id', 'event_type']);

-- new data is clustered immediately; old data is re-clustered in the background over hours
```

If you need it sooner, rewrite the table:
```sql
CREATE OR REPLACE TABLE `p.d.events_v2`
PARTITION BY DATE(event_ts)
CLUSTER BY user_id, event_type AS
SELECT * FROM `p.d.events`;
-- then ALTER ... RENAME or swap pointers via views
```

**Real-world.** A common day-2 cost optimization. Verify benefit with `EXPLAIN`-style query stats before and after.

**Follow-ups.** Test cluster column ordering — leftmost matters most. Adding too many cluster columns dilutes effectiveness.

---

### Problem 18 — Choose partition column wisely

**Statement.** Events arrive with two timestamps: `received_ts` (when ingested) and `event_ts` (when client says it happened). Partition by which?

**Solution.**
```sql
-- Partition by what your QUERIES filter on. Almost always event_ts.
PARTITION BY DATE(event_ts)
```

The reasoning: dashboards and ML features want "what happened on day X?" — that's `event_ts`. Late-arriving data goes into the right partition because BQ uses the column value, not ingestion order.

If you also need to handle late-arriving data correctly (e.g. backfills 30 days late), use `event_ts` for partitioning AND set partition_expiration generously. Re-aggregating downstream tables when late data arrives is the dbt incremental pattern (§10).

**Real-world.** This decision is commonly wrong on the first cut and painful to fix later. Think hard about it.

**Follow-ups.** Ingestion-time partitioning when no client timestamp is trustworthy. Multi-column partitioning (BQ supports only one — composite via expression).

---

### Problem 19 — Backfill a single partition cheaply

**Statement.** Reprocess just yesterday's data without rebuilding the entire table.

**Solution.**
```sql
-- atomic single-partition replace via DELETE + INSERT in a transaction
BEGIN
  DELETE FROM `p.d.daily_summary` WHERE day = '2026-04-26';
  INSERT INTO `p.d.daily_summary`
  SELECT DATE(event_ts) AS day, country, COUNT(*) AS n
  FROM `p.d.events`
  WHERE DATE(event_ts) = '2026-04-26'
  GROUP BY day, country;
END;
```

In dbt, this is the `incremental_strategy='insert_overwrite'` model — handles partition replacement atomically.

**Real-world.** Backfills, late-arriving data, fixing a bug in transformation logic. Always partition-scoped — never rebuild the whole table.

**Follow-ups.** Use `MERGE` for upserts. `TRUNCATE TABLE ... PARTITION` (a 2024 feature) for ultra-cheap partition swaps.

---

### Problem 20 — Cap a query's cost at \$1

**Statement.** A junior analyst is about to run a query against a TB-scale table. Limit the bill in case it goes wrong.

**Solution.**
```python
# 1 GB at $5/TB ≈ $0.005, so $1 ≈ ~200 GB
MAX_BYTES = 200 * 1024**3

job_config = bigquery.QueryJobConfig(maximum_bytes_billed=MAX_BYTES)
job = client.query(sql, job_config=job_config)
# fails at submit time if the planner thinks it will exceed the cap
```

In the UI: **Query settings -> Advanced -> Maximum bytes billed**. Set as a per-query default in your team's onboarding.

**Real-world.** This single setting has saved more money in BigQuery than any other configuration. Run it on every notebook by default.

**Follow-ups.** Org-level custom quotas. Per-user daily caps. Slack notifications on >X bytes scanned.

---

### Problem 21 — Use APPROX vs exact aggregation

**Statement.** Show cost difference between `COUNT(DISTINCT)` and `APPROX_COUNT_DISTINCT` on a 1B-row table.

**Solution.**
```sql
-- exact: scans full column
SELECT COUNT(DISTINCT user_id) FROM `p.d.events` WHERE DATE(event_ts) BETWEEN '2026-01-01' AND '2026-04-30';
-- ~120 GB scanned, ~60s

-- approximate: same scan, but the planner uses HLL — typically the same scan but less compute
SELECT APPROX_COUNT_DISTINCT(user_id) FROM `p.d.events` WHERE DATE(event_ts) BETWEEN '2026-01-01' AND '2026-04-30';
-- typical accuracy: ~1-2% relative error; cost: similar bytes, much less compute time
```

For sketches that get *cheaper over time*, see Problem 2 (precomputed daily HLL sketches that you `MERGE`).

**Real-world.** Default approximate for dashboards. Use exact only for accounting / billing where the spec says exact.

**Follow-ups.** Precision tuning (`HLL_COUNT.INIT(x, 18)` for ~0.1% error). Sketch storage as bytes for cross-query reuse.

---

### Problem 22 — Materialized view to make a hot query free

**Statement.** A dashboard runs `SELECT day, country, n FROM daily_dau` every 5 minutes. Make it nearly free.

**Solution.**
```sql
CREATE MATERIALIZED VIEW `p.d.dau_country_mv`
PARTITION BY day AS
SELECT DATE(event_ts) AS day, country, APPROX_COUNT_DISTINCT(user_id) AS n
FROM `p.d.events`
GROUP BY day, country;
```

The MV refreshes incrementally as base data changes. Queries against the MV (or queries against the base table that BQ can rewrite to use the MV) hit precomputed results.

**Real-world.** The "ELT precompute" pattern — pay for compute once at write time; reads are nearly free.

**Follow-ups.** Don't create MVs for low-volume queries (refresh cost > query cost). Refresh-on-demand mode for predictable batch refresh. BI Engine reservation for sub-second BI dashboards.

---

### Problem 23 — Spotting an expensive accidental scan

**Statement.** A pipeline started costing 10× more last week. Find the culprit.

**Solution.**
```sql
-- find the most expensive jobs in the last 7 days
SELECT
    user_email,
    SUM(total_bytes_billed) / POW(1024, 4) AS tb_billed,
    COUNT(*) AS n_jobs,
    APPROX_TOP_COUNT(query, 1)[OFFSET(0)].value AS top_query_sample
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND job_type = 'QUERY'
  AND state = 'DONE'
GROUP BY user_email
ORDER BY tb_billed DESC
LIMIT 20;
```

`INFORMATION_SCHEMA.JOBS_*` views expose job history with byte and slot stats — the audit trail every BQ team uses.

**Real-world.** Weekly ritual: "who scanned the most this week?" Surfaces missing partition filters, runaway dbt models, and over-eager BI tools.

**Follow-ups.** Slot-time per job (for reservation users). Cost attribution by service account / job label.

---

### Problem 24 — Parameterized query from Python

**Solution.**
```python
from google.cloud import bigquery

client = bigquery.Client()

sql = """
SELECT user_id, COUNT(*) AS n
FROM `p.d.events`
WHERE DATE(event_ts) BETWEEN @start AND @end
  AND event_type = @kind
GROUP BY user_id
ORDER BY n DESC
LIMIT @top_n
"""

job = client.query(sql, job_config=bigquery.QueryJobConfig(query_parameters=[
    bigquery.ScalarQueryParameter("start", "DATE",  "2026-04-01"),
    bigquery.ScalarQueryParameter("end",   "DATE",  "2026-04-30"),
    bigquery.ScalarQueryParameter("kind",  "STRING","purchase"),
    bigquery.ScalarQueryParameter("top_n", "INT64", 100),
]))
df = job.to_dataframe()
```

**Why parameters.** Same as MySQL/Postgres — never f-string user input. BQ also caches by query text, so identical parameterized queries hit the cache; f-string variants don't.

**Follow-ups.** Array parameters (`bigquery.ArrayQueryParameter("ids","INT64",[1,2,3])`). Struct parameters. Asynchronous job polling for long queries.

---

### Problem 25 — Load a Parquet folder from GCS, partitioned + clustered

**Solution.**
```python
from google.cloud import bigquery

client = bigquery.Client()

job = client.load_table_from_uri(
    "gs://my-bucket/events/dt=2026-04-27/*.parquet",
    "p.d.events",
    job_config=bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        time_partitioning=bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="event_ts",
        ),
        clustering_fields=["user_id", "event_type"],
        # Schema is inferred from parquet — no schema= needed
    ),
)
print("Loading...")
job.result()
print(f"Loaded {job.output_rows:,} rows; bytes: {job.output_bytes:,}")
```

**Real-world.** Daily ingestion job — usually triggered by Cloud Scheduler -> Cloud Function -> this code, or by Airflow / Cloud Composer.

**Follow-ups.** Ingest with schema validation (`schema=` + `autodetect=False`). Partition expiration (`partition_expiration_days`). Idempotency key in job ID to prevent dupes.

---

### Problem 26 — Stream events into BigQuery (modern path)

**Statement.** A FastAPI service receives webhooks; events should land in BQ within seconds.

**Recommended pattern:**
```
FastAPI -> Pub/Sub topic -> Pub/Sub BigQuery subscription -> table
```

Pub/Sub's BigQuery subscriptions write directly to a table — no Dataflow needed for simple pass-through.

```python
# webhook handler
from google.cloud import pubsub_v1
publisher = pubsub_v1.PublisherClient()
TOPIC = publisher.topic_path(PROJECT, "webhook-events")

@app.post("/hook")
async def hook(payload: dict):
    publisher.publish(TOPIC, data=json.dumps(payload).encode("utf-8")).result()
    return {"status": "queued"}
```

Set up the BigQuery subscription via gcloud or Terraform; specify a target table; Pub/Sub handles batching and retries.

**Real-world.** Standard webhook ingest pattern in 2026. Avoids a Dataflow job for simple ETL; you get exactly-once writes; durability against BQ outages.

**Follow-ups.** Use Storage Write API directly for highest throughput + transactional semantics. Dataflow for transformations. Datastream for CDC from Postgres / MySQL.

---

### Problem 27 — Read 5GB of results into pandas fast

**Statement.** A query returns ~10M rows. The default `to_dataframe()` is painfully slow.

**Solution.**
```python
from google.cloud import bigquery
from google.cloud import bigquery_storage

bq = bigquery.Client()
bqs = bigquery_storage.BigQueryReadClient()

df = bq.query("SELECT user_id, total FROM `p.d.user_totals`").to_dataframe(bqstorage_client=bqs)
# 5–20× faster for big results — uses Arrow/gRPC instead of REST
```

Even faster: skip pandas and read straight into Arrow:
```python
table = bq.query(sql).to_arrow(bqstorage_client=bqs)
# zero-copy interop with polars: pl.from_arrow(table)
```

**Real-world.** Any time you bring big data to your laptop — model training, batch scoring, deep EDA.

**Follow-ups.** Use BigFrames to keep computation in BQ. Stream results via `RowIterator` for memory-bounded processing.

---

### Problem 28 — DataFrame -> BigQuery with proper schema

**Solution.**
```python
import pandas as pd
from google.cloud import bigquery
from datetime import datetime

df = pd.DataFrame({
    "user_id": [1, 2, 3],
    "name":    ["Ada", "Bob", "Cal"],
    "score":   [88.5, 72.0, 95.5],
    "joined":  [datetime(2026,1,1), datetime(2026,1,2), datetime(2026,1,3)],
})

client = bigquery.Client()
job = client.load_table_from_dataframe(
    df,
    "p.d.users_load",
    job_config=bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        schema=[
            bigquery.SchemaField("user_id", "INT64",     mode="REQUIRED"),
            bigquery.SchemaField("name",    "STRING",    mode="REQUIRED"),
            bigquery.SchemaField("score",   "FLOAT64"),
            bigquery.SchemaField("joined",  "TIMESTAMP", mode="REQUIRED"),
        ],
    ),
)
job.result()
```

**Pitfall.** Without an explicit schema, the loader infers types — sometimes wrongly (a column with one all-numeric day becomes INT, breaking the next load with a string). Always specify schema for production loads.

**Follow-ups.** Use `pyarrow` directly for huge frames (skip pandas). Use partitioned `WRITE_TRUNCATE_DATA` to replace just one partition.

---

### Problem 29 — Find the join skew killing your query

**Statement.** A query takes 30 minutes. Query plan shows one stage taking 95% of the slot-ms.

**Diagnosis.** Skew on a join key. Some keys have millions of rows, some have a handful — the worker assigned the hot key never finishes.

**Solution patterns:**
```sql
-- 1. Filter or sample the skewed key
SELECT * FROM big_table b JOIN small_table s ON b.k = s.k
WHERE b.k IS NOT NULL AND b.k != 'unknown';     -- "unknown" was 60% of rows

-- 2. Salting — break up the hot key
WITH big_salted AS (
  SELECT *, MOD(FARM_FINGERPRINT(CAST(some_col AS STRING)), 10) AS salt FROM big_table
),
small_replicated AS (
  SELECT s.*, x.salt
  FROM small_table s, UNNEST(GENERATE_ARRAY(0, 9)) AS salt
)
SELECT *
FROM big_salted b JOIN small_replicated s
  ON b.k = s.k AND b.salt = s.salt;

-- 3. Broadcast: hint the small side as a broadcast (BQ usually picks it automatically)
```

**Real-world.** Skew is the most common cause of "this query was fine yesterday and is dying today."

**Follow-ups.** Detect skew with `APPROX_TOP_COUNT(join_key, 10)`. Pre-aggregate the large side before joining.

---

### Problem 30 — When BQ is using clustering — verify

**Solution.** Inspect the query plan and `bytes_processed` after a partition + cluster filter:

```python
sql_clustered = """
SELECT COUNT(*) FROM `p.d.events`
WHERE DATE(event_ts) = '2026-04-27' AND user_id = 42
"""

job = client.query(sql_clustered)
result = job.result()
print(f"Bytes processed: {job.total_bytes_processed:,}")
# When clustering helps: only a few MB even on a TB-scale table.
# When it doesn't: full partition scanned (~ partition size).
```

If clustering isn't helping, check:
- Are you filtering on the leftmost cluster column? Filtering only on column 2 doesn't prune.
- Is the column low-cardinality? With <1000 distinct values clustering rarely helps.
- Is `user_id` actually clustered? `bq show p:d.events` shows `Clustering` setting.

**Real-world.** Clustering is "free if used correctly, useless if not." Always validate.

**Follow-ups.** ALTER the cluster columns. Check INFORMATION_SCHEMA for cluster ordering history.

---

### Problem 31 — CTE inlining and the "subquery DAG" trap

**Statement.** A WITH-CTE used 3 times in a query gets executed 3 times — surprising people coming from Postgres where CTEs are usually optimized barriers.

**Real-world.** A query with a heavy CTE used in 4 unions can scan its source 4×. To force a single computation:

```sql
-- NOT OK: CTE inlined 4 times
WITH big AS (SELECT user_id, ... FROM huge WHERE ...)
SELECT 'a', COUNT(*) FROM big WHERE ...
UNION ALL SELECT 'b', COUNT(*) FROM big WHERE ...
UNION ALL SELECT 'c', COUNT(*) FROM big WHERE ...
UNION ALL SELECT 'd', COUNT(*) FROM big WHERE ...

-- OK: materialize once into a scratch / temp table
CREATE TEMP TABLE big AS SELECT user_id, ... FROM huge WHERE ...;
SELECT 'a', COUNT(*) FROM big WHERE ...
UNION ALL SELECT 'b', COUNT(*) FROM big WHERE ...;
```

Or use `WITH (recursive)` and `EXPLAIN` to see the plan.

**Real-world.** If your query plan shows the same source scan many times, materialize the CTE.

**Follow-ups.** Hint with `OPTIONS (...)`. Use a session temp table.

---

### Problem 32 — Cache busting (intentional)

**Statement.** A scheduled job needs fresh results — don't return cache.

**Solution.**
```python
job_config = bigquery.QueryJobConfig(use_query_cache=False)
client.query(sql, job_config=job_config)
```

By default BigQuery caches successful query results for 24h, keyed by exact query text + dataset state. Cache hits are free. The query cache is invalidated when underlying data changes — but only by the streaming/load path; manual edits via DML may not invalidate as expected.

**Real-world.** Most scheduled queries should *use* the cache (it's free and fast). Bust only when you genuinely need fresh data after a manual write.

**Follow-ups.** `query_cache` is per-table — depends on whether the query is over deterministic functions. `CURRENT_TIMESTAMP()` makes the query non-cacheable.

---

### Problem 33 — Train a logistic regression in BQML

**Solution.**
```sql
CREATE OR REPLACE MODEL `p.d.churn_lr`
OPTIONS (
    model_type = 'LOGISTIC_REG',
    input_label_cols = ['churned'],
    auto_class_weights = TRUE,
    data_split_method = 'AUTO_SPLIT',
    enable_global_explain = TRUE
)
AS
SELECT
    churned,                                      -- label
    days_since_last_login,
    n_logins_30d,
    total_spend_90d,
    country
FROM `p.d.training_features`;

-- evaluate on the held-out split
SELECT * FROM ML.EVALUATE(MODEL `p.d.churn_lr`);

-- inspect feature importances (works thanks to enable_global_explain)
SELECT * FROM ML.GLOBAL_EXPLAIN(MODEL `p.d.churn_lr`);
```

**Real-world.** Baseline classifier in 30 seconds, no Python. Often "good enough" for early-stage products. For deep models, BQML calls Vertex AI under the hood — same SQL surface.

**Follow-ups.** XGBoost in BQML (`model_type='BOOSTED_TREE_CLASSIFIER'`). K-means clustering. ARIMA forecasting.

---

### Problem 34 — Inference at scale on warehouse data

**Statement.** Score 100M user rows daily through an existing BQML model.

**Solution.**
```sql
CREATE OR REPLACE TABLE `p.d.daily_scores`
PARTITION BY day
AS
SELECT
    CURRENT_DATE() AS day,
    user_id,
    predicted_churned_probs[OFFSET(0)].prob AS p_churn
FROM ML.PREDICT(MODEL `p.d.churn_lr`,
    (SELECT * FROM `p.d.live_features` WHERE DATE(updated_at) = CURRENT_DATE())
);
```

**Real-world.** Inference where the data lives — no ETL, no Python service. Scales to billions of rows trivially. For models trained outside BQ, `ML.PREDICT` works on imported TF / ONNX / Vertex AI endpoints.

**Follow-ups.** Threshold-based action (insert only when `p_churn > 0.7`). Hourly inference instead of daily. Row-level explanations with `ML.EXPLAIN_PREDICT`.

---

### Problem 35 — Vector embeddings + nearest-neighbor in BQ

**Statement.** Build a "find similar articles" feature using BQ-native embeddings.

**Solution.**
```sql
-- one-time: create the embedding model (Vertex AI text-embedding-004 endpoint)
CREATE OR REPLACE MODEL `p.d.text_embed`
REMOTE WITH CONNECTION `region-us.embedding-conn`
OPTIONS (endpoint = 'text-embedding-004');

-- generate embeddings for articles
CREATE OR REPLACE TABLE `p.d.article_embeddings` AS
SELECT article_id,
       ml_generate_embedding_result AS embedding
FROM ML.GENERATE_EMBEDDING(
    MODEL `p.d.text_embed`,
    (SELECT article_id, content AS content FROM `p.d.articles`)
);

-- create a vector index for fast NN search at scale
CREATE VECTOR INDEX article_index
ON `p.d.article_embeddings` (embedding)
OPTIONS (distance_type='COSINE', index_type='IVF');

-- query: find 10 nearest articles to article 42
SELECT *
FROM VECTOR_SEARCH(
    TABLE `p.d.article_embeddings`,
    'embedding',
    (SELECT embedding FROM `p.d.article_embeddings` WHERE article_id = 42),
    top_k => 10,
    distance_type => 'COSINE'
);
```

**Real-world.** Foundation for RAG systems where the corpus already lives in BQ. Module 10 covers full RAG.

**Follow-ups.** Hybrid search (vector + keyword). Filter pushdown into VECTOR_SEARCH. Cross-modal embeddings.

---

### Problem 36 — End-to-end: model + features + scoring schedule

**Statement.** Schedule daily training, scoring, and a metric backfill — all in BQ + dbt.

**Sketch:**
```yaml
# dbt project layout
models/
  staging/
    stg_events.sql            # cleaning
    stg_users.sql
  features/
    user_daily_features.sql   # incremental, partitioned
  models/
    churn_features.sql        # joined feature row per active user
  scoring/
    churn_predictions.sql     # SELECT FROM ML.PREDICT(MODEL ..., ...)
  metrics/
    churn_metric_daily.sql    # accuracy on labeled set
```

```sql
-- features/user_daily_features.sql
{{ config(materialized='incremental', partition_by={'field':'day','data_type':'date'},
          incremental_strategy='insert_overwrite') }}
SELECT DATE(event_ts) AS day, user_id,
       COUNT(*) AS n_events,
       COUNTIF(event_type='purchase') AS n_purchases
FROM {{ ref('stg_events') }}
{% if is_incremental() %}
WHERE DATE(event_ts) >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
{% endif %}
GROUP BY day, user_id;
```

Schedule with **Cloud Composer (Airflow)** or **dbt Cloud**: nightly `dbt run` + `dbt test`. Failures alert on Slack. Lineage graph shows feature -> model -> metric path.

**Real-world.** This is how production analytics teams ship ML on warehouse data. Module 12 (MLOps) extends this with model registries, serving, and monitoring.

**Follow-ups.** Vertex Pipelines for ML-orchestrated workflows. Feature store (Tecton, Feast) on top of BQ for online serving.

---

## 16. Three mini-projects

### Mini-project A — Build a public-data analytics dashboard
Pick a BQ public dataset (`bigquery-public-data.github_repos` or `wikipedia.pageviews_*`). Build five queries that answer interesting questions, each tuned to scan less than 1 GB. Productionize with: a partitioned summary table (refreshed daily), a materialized view for the hottest dashboard query, and a Streamlit / Looker Studio UI.

**Skills exercised:** every section. Constraints force partitioning + clustering + approximate aggregations.

### Mini-project B — A tiny dbt + BigQuery feature pipeline
Set up a dbt project with three layers: `stg_*` (cleaning), `feat_*` (per-entity features, incremental partitioned), `mart_*` (training tables, scoring views). At least 5 models with 10+ tests. Schedule nightly. Compare cost of full-refresh vs incremental builds.

**Skills exercised:** §10 dbt patterns, partitioning strategy, incremental builds.

### Mini-project C — Streaming-to-BQ pipeline with FastAPI ingestion
A FastAPI service exposes a webhook. Webhooks publish to Pub/Sub. Pub/Sub -> BigQuery subscription writes to a partitioned events table. A dbt model rolls up events nightly. Failure modes you must handle: schema evolution, dead-letter queue for malformed events, idempotency by event ID.

**Skills exercised:** Module 4 (FastAPI) + this module's streaming + dbt incremental.

---

## 17. Real-world usage map

| Concept | Where it returns later |
|---|---|
| ARRAY/STRUCT denormalization | LLM dataset prep — chats stored as `messages ARRAY<STRUCT<role,content>>` |
| HLL sketches | LLM observability — daily distinct users without re-scan (Module 13) |
| Materialized views | Cached aggregates feeding RAG retrieval pipelines (Module 10) |
| BQ vector index | First-pass vector search before specialized vector DBs (Module 10) |
| BQML `ML.PREDICT` at scale | Batch scoring 100M rows — Module 12 (MLOps) |
| Partition + cluster | Feature stores backed by BQ (Module 12); cost stays sane |
| dbt incremental models | The standard ETL pattern in any data platform you'll join |
| INFORMATION_SCHEMA.JOBS | Cost attribution, anomaly detection — Module 13 |
| `_PARTITIONTIME` | Lineage/audit when source timestamps are unreliable |
| Federated GCS queries | One-shot exploration of model artifacts / logs |

---

## 18. Interview pitfalls — what NOT to say

- **"BigQuery has indexes like Postgres."** It doesn't. Partitioning + clustering replace them.
- **"I'd just `SELECT *` and filter in pandas."** That's the most expensive way to use BQ. Filter and aggregate in SQL.
- **"`COUNT(DISTINCT)` is fine on a billion rows."** It's not — it's expensive. Use `APPROX_COUNT_DISTINCT` for analytics.
- **"I'll partition by `country`."** Partition keys with low cardinality (a few hundred values) work for integer-range. For high-cardinality string filters, use **clustering** instead.
- **"I'll add 10 cluster columns to be safe."** BQ allows up to 4. More clutters the cluster effectiveness; fewer focused columns are better.
- **"Streaming is the default for ingest."** Batch from GCS Parquet is far cheaper. Stream only when latency requires it.
- **"BigQuery transactions are like Postgres."** Limited multi-statement scripts only. No general row-level locks. Don't run OLTP workloads on BQ.
- **"I forgot the partition filter — it's just a small extra cost."** On a TB table, "small" is \$5. On 100 TB, \$500. Use `require_partition_filter`.
- **"`OFFSET` for pagination is fine."** Same as Postgres — keyset is better. For huge results, the Storage Read API streams.
- **"I'll JOIN this 1B-row table to itself."** Window functions + `QUALIFY` usually replace the self-join with one scan.
- **"BQ ML is just for analysts."** It's also the cheapest way to score billions of rows on warehouse data — even ML teams use it for batch inference.

**How to communicate.** When asked to design a BQ table, narrate (1) partition column + reason, (2) cluster columns + leftmost-prefix awareness, (3) expected query patterns, (4) cost guard rails (`require_partition_filter`, `maximum_bytes_billed`), (5) ingest path (load vs stream), (6) downstream layer (raw -> staging -> mart with dbt).

---

## 19. Cheatsheet

```text
HIERARCHY
  project -> dataset -> table | view | materialized view | routine
  fully qualified: `proj.dataset.table`  (backticks for hyphens)

DIALECT
  GoogleSQL (default). Never legacy. Never `[proj:ds.tbl]`.

TABLE DDL
  CREATE [OR REPLACE] TABLE `p.d.t`
  ( cols... )
  PARTITION BY DATE(ts) | DATE_TRUNC(ts, MONTH) | RANGE_BUCKET(...) | _PARTITIONDATE
  CLUSTER BY col1, col2, col3, col4   (max 4)
  OPTIONS (
    partition_expiration_days = N,
    require_partition_filter  = TRUE,        -- always for prod fact tables
    description               = '...'
  );

  ALTER TABLE ... SET OPTIONS (clustering_fields = ['x','y']);
  ALTER TABLE ... ADD COLUMN x INT64;

USEFUL DIALECT FEATURES
  QUALIFY ROW_NUMBER() OVER (...) = 1     -- filter on window fn output
  SELECT * EXCEPT (col1, col2)
  SELECT * REPLACE (LOWER(email) AS email)
  SAFE_CAST(s AS INT64) | SAFE_DIVIDE(a,b)
  IFNULL / COALESCE / NULLIF
  DATE_TRUNC(d, MONTH) | DATE_DIFF(d1,d2,DAY) | DATE_ADD(d, INTERVAL 7 DAY)
  TIMESTAMP_TRUNC | TIMESTAMP_DIFF | TIMESTAMP_ADD
  GENERATE_DATE_ARRAY(s, e, INTERVAL 1 DAY)
  CASE WHEN ... THEN ... ELSE ... END

ARRAY / STRUCT
  [STRUCT(a, b)]              build inline
  ARRAY<STRUCT<...>>          column type
  ARRAY_AGG(x ORDER BY ...)   group -> array
  ARRAY_LENGTH(a)             size
  UNNEST(arr) [WITH OFFSET pos]   explode to rows
  (SELECT SUM(...) FROM UNNEST(arr))   aggregate inside the row

JSON
  JSON_VALUE(json, '$.a.b')   scalar -> STRING
  JSON_QUERY(json, '$.a')     subtree -> JSON
  JSON_QUERY_ARRAY(json, '$.tags')
  type as JSON, not STRING

APPROX
  APPROX_COUNT_DISTINCT(x)
  APPROX_QUANTILES(x, 100)[OFFSET(95)]    p95
  APPROX_TOP_COUNT(x, 10)
  HLL_COUNT.INIT / .MERGE / .EXTRACT      sketch -> store -> merge later

WINDOWS (same as ANSI; with QUALIFY)
  ROW_NUMBER | RANK | DENSE_RANK | NTILE
  LAG | LEAD | FIRST_VALUE | LAST_VALUE
  SUM/AVG/COUNT OVER (PARTITION BY k ORDER BY o ROWS BETWEEN ...)

PARTITION & CLUSTER (rules)
  PARTITION on what queries FILTER (almost always DATE(event_ts))
  CLUSTER on what queries FILTER + JOIN — high cardinality first
  require_partition_filter = TRUE on prod
  partition_expiration_days for retention

COST CONTROLS
  Dry run:
    job_config = QueryJobConfig(dry_run=True, use_query_cache=False)
    print(job.total_bytes_processed)
  Hard cap:
    QueryJobConfig(maximum_bytes_billed=N)
  Cache:
    use_query_cache=False to bust intentionally
  Custom quota: per-user/project daily byte cap

PYTHON CLIENT (google-cloud-bigquery)
  client = bigquery.Client(project=P)
  client.query(sql).to_dataframe()                      run + results
  client.query(sql, job_config=QueryJobConfig(query_parameters=[
      ScalarQueryParameter("name","TYPE",value),
      ArrayQueryParameter("ids","INT64",[1,2,3]),
  ]))
  client.load_table_from_uri("gs://...", "p.d.t", job_config=LoadJobConfig(
      source_format=SourceFormat.PARQUET,
      write_disposition="WRITE_APPEND",
      time_partitioning=TimePartitioning(field="event_ts"),
      clustering_fields=["user_id"],
  )).result()
  client.load_table_from_dataframe(df, "p.d.t", job_config=LoadJobConfig(
      schema=[SchemaField("x","INT64"), ...],
      write_disposition="WRITE_TRUNCATE",
  ))
  client.insert_rows_json("p.d.t", rows)                streaming insert (legacy)

STORAGE READ API (fast result download)
  bqs = bigquery_storage.BigQueryReadClient()
  df = client.query(sql).to_dataframe(bqstorage_client=bqs)
  table = client.query(sql).to_arrow(bqstorage_client=bqs)

PANDAS-GBQ / BIGFRAMES
  pd.read_gbq(sql, project_id=P)
  df.to_gbq(table_ref, if_exists='replace')
  bigframes.pandas: pandas API, computes on BQ slots

MATERIALIZED VIEWS
  CREATE MATERIALIZED VIEW `p.d.mv` PARTITION BY day AS SELECT ... GROUP BY ...;
  refreshes incrementally; queries on base table can rewrite to use MV

BQML
  CREATE MODEL `p.d.m` OPTIONS(model_type='LOGISTIC_REG', input_label_cols=['y']) AS SELECT ...;
  ML.EVALUATE(MODEL ...)
  ML.PREDICT(MODEL ..., TABLE ...)
  ML.GLOBAL_EXPLAIN | ML.EXPLAIN_PREDICT
  Vector: ML.GENERATE_EMBEDDING + CREATE VECTOR INDEX + VECTOR_SEARCH

dbt-bigquery
  {{ config(materialized='incremental',
            partition_by={'field':'day','data_type':'date'},
            cluster_by=['country'],
            incremental_strategy='insert_overwrite') }}
  {% if is_incremental() %} ... {% endif %}
  ref('upstream_model'); source('raw','table')

INFO_SCHEMA (audit / cost)
  region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT     job history
  ...JOBS_BY_USER, ...JOBS_BY_FOLDER, ...JOBS_BY_ORGANIZATION
  total_bytes_billed, total_slot_ms, query (text)
  TABLE_STORAGE for size; PARTITIONS for partition stats

ANTI-PATTERNS
  SELECT *, no partition filter, COUNT(DISTINCT) on huge tables
  streaming for batch data, CSV when source is parquet
  inv schema; no require_partition_filter; admin role on app SAs
  ad-hoc procedural SQL instead of dbt
  cross-region data + queries
```

---

## 20. Prerequisites & next steps

**Prerequisites covered? You can:**
- Read and write GoogleSQL with confidence — including ARRAY/STRUCT, JSON, window functions, and QUALIFY.
- Design tables with the right partition + cluster choice based on actual query patterns.
- Estimate and cap query cost; spot expensive accidents in INFORMATION_SCHEMA.
- Use BigQuery from Python — client library, parameterized queries, fast reads via Storage Read API.
- Choose between batch loads, streaming, and federated queries by use case.
- Build incremental dbt models with insert-overwrite and tests.
- Apply column-level security, row-level policies, and least-privilege IAM.
- Train and serve simple ML models in BQML; do vector search on warehouse data.

**Next steps in the bible:**
- **Module 6 — Cloud foundations.** IAM, service accounts, networking, Cloud Run/Functions/GKE, secrets management, deploy targets for everything you build.
- **Module 7 — Classical ML.** BigQuery becomes the source of truth for features and labels; many models train on data extracted from BQ.
- **Module 12 — MLOps.** Workflows, model registries, monitoring — BQ is often the metric store.

**External study (only if you want depth):**
- Google's *BigQuery: The Definitive Guide* — the most comprehensive reference.
- The BigQuery release notes — features ship monthly; the docs are excellent.
- *Fundamentals of Data Engineering* (Reis & Housley) — warehouse-agnostic but covers the right mental models.
- Felipe Hoffa's blog (long-time Google BQ advocate) for clever query patterns.

---

*End of Module 5. Module 6 covers cloud foundations — AWS, GCP, Azure for ML serving — same structure, 35+ problems.*
