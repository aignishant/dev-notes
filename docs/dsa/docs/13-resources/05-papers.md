# Must-Read Papers

> The papers that shaped how systems are built. Read in this order; don't skip the ones that look "old."

<span class="phase-status phase-done">Phase 14 — Resources</span>

---

## How to read a systems paper

1. **First pass (15 min)**: title, abstract, intro, conclusion. Skip the math.
2. **Second pass (1 hr)**: figures, system diagram, evaluation section. Skim the proofs.
3. **Third pass (3+ hr)**: every line. Re-derive the algorithm. Implement a toy version if it's tractable.

**Most papers are second-pass-only**. The ones marked ⭐ deserve the third pass.

---

## Foundational distributed systems

### ⭐ The Google File System (Ghemawat, Gobioff, Leung — SOSP 2003)
The grandparent of HDFS, Colossus, and every blob store. Single master + chunkservers; append-mostly workload; replication for durability.
**Read for**: master/worker pattern, append-only design, lease-based mutations.

### ⭐ MapReduce: Simplified Data Processing on Large Clusters (Dean, Ghemawat — OSDI 2004)
The functional-programming-meets-distributed-systems paper that launched the Big Data era.
**Read for**: how to think about partitioning + reduction; fault tolerance via re-execution.

### ⭐ Bigtable: A Distributed Storage System for Structured Data (Chang et al. — OSDI 2006)
Wide-column store. SSTable + memtable + tablet servers. Direct ancestor of HBase, Cassandra, Accumulo.
**Read for**: SSTable design, locality groups, tablet splitting.

### ⭐ Dynamo: Amazon's Highly Available Key-Value Store (DeCandia et al. — SOSP 2007)
Eventually-consistent KV. Consistent hashing + vector clocks + sloppy quorum + Merkle trees.
**Read for**: AP-side of CAP; the trade-offs Cassandra inherited.

### ⭐ Paxos Made Simple (Lamport — 2001)
Consensus, simplified. (Despite the title, it's not actually simple — but everything before it was worse.)
**Read for**: the multi-decree consensus problem and why it's hard.

### ⭐ In Search of an Understandable Consensus Algorithm (Ongaro, Ousterhout — Raft, ATC 2014)
Raft. Same problem as Paxos, but explained in a way humans can implement.
**Read for**: leader election, log replication, safety property proofs.

### ZooKeeper: Wait-free coordination for Internet-scale systems (Hunt et al. — ATC 2010)
Coordination primitive that thousands of systems depend on (Kafka pre-KRaft, HDFS NameNode HA, Mesos…).
**Read for**: zab consensus protocol, watch + sequential nodes pattern.

### Chubby: The Chubby lock service for loosely-coupled distributed systems (Burrows — OSDI 2006)
Google's predecessor to ZooKeeper.
**Read for**: lock service as primitive; the "DNS in a tree" abstraction.

---

## Storage / databases

### ⭐ Spanner: Google's Globally-Distributed Database (Corbett et al. — OSDI 2012)
SQL semantics + globally consistent transactions via TrueTime (atomic clocks + GPS).
**Read for**: how Google trades hardware for clean semantics.

### F1: A Distributed SQL Database That Scales (Shute et al. — VLDB 2013)
The query layer on top of Spanner that replaced Google's main MySQL deployment.

### Bigtable + Spanner together explain Cloud Spanner.

### The Log-Structured Merge-Tree (O'Neil et al. — 1996)
LSM trees, the data structure behind RocksDB, Cassandra, BigTable, ScyllaDB.
**Read for**: write-optimised storage; level vs size-tiered compaction.

### B-tree paper (Bayer & McCreight, 1972)
The data structure powering every traditional RDBMS index.
**Skim for**: why B-trees beat binary trees on disk.

### ⭐ Calvin: Fast Distributed Transactions for Partitioned Database Systems (Thomson et al. — SIGMOD 2012)
Deterministic execution of transactions in a pre-decided order.
**Read for**: an alternative paradigm to 2PC.

### Aurora: a fast, available cloud-native database (Verbitski et al. — SIGMOD 2017)
AWS Aurora. Storage layer separated from compute; redo-log streaming.
**Read for**: cloud-native MySQL/Postgres re-architecture.

---

## Streaming / messaging

### ⭐ Kafka: a Distributed Messaging System for Log Processing (Kreps et al. — NetDB 2011)
The original Kafka paper. Append-only log as a primitive.
**Read for**: log-as-database thinking.

### Apache Flink: Stream and Batch Processing in a Single Engine (Carbone et al. — IEEE 2015)
Watermarks, event-time semantics, exactly-once.
**Read for**: how to do streaming aggregations correctly.

### MillWheel: Fault-Tolerant Stream Processing at Internet Scale (Akidau et al. — VLDB 2013)
Google's predecessor to Dataflow / Beam.
**Read for**: low-watermark gossip, exactly-once via idempotent records.

### The Dataflow Model (Akidau et al. — VLDB 2015)
Beam / Dataflow. Watermarks + triggers + windowing.
**Read for**: a clean theory of streaming aggregation.

---

## Compute / cluster scheduling

### Borg: Large-scale cluster management at Google (Verma et al. — EuroSys 2015)
Predecessor to Kubernetes.
**Read for**: bin-packing, priorities, oversubscription.

### Mesos: a Platform for Fine-Grained Resource Sharing in the Data Center (Hindman et al. — NSDI 2011)
Two-level scheduler.
**Read for**: contrast with Borg/K8s monolithic schedulers.

### Omega: flexible, scalable schedulers for large compute clusters (Schwarzkopf et al. — EuroSys 2013)
Optimistic concurrent scheduling.

---

## Indexing / search

### ⭐ The Anatomy of a Large-Scale Hypertextual Web Search Engine (Brin, Page — 1998)
The original Google paper. PageRank, inverted indexes.
**Read for**: web-scale crawling + indexing pipelines.

### Lucene's BKD trees (Pyro paper, 2003) and FST tries
Background reading for understanding Elasticsearch / Solr.

### ⭐ Pinot: Realtime OLAP for 530 Million Users (Im et al. — SIGMOD 2018)
LinkedIn's columnar OLAP for real-time dashboards.

### Druid: A Real-time Analytical Data Store (Yang et al. — SIGMOD 2014)
Imply's commercial offering. Similar space to Pinot / ClickHouse.

---

## Networking

### A Brief History of the Internet (Leiner et al. — 1997)
Background. Skim.

### BBR: Congestion-Based Congestion Control (Cardwell et al. — Communications of the ACM 2017)
Google's TCP congestion control rethink.
**Read for**: model-based vs loss-based congestion control.

### The QUIC paper (Langley et al. — SIGCOMM 2017)
Transport protocol underlying HTTP/3.

---

## Caching / CDN

### Web Caching with Consistent Hashing (Karger et al. — STOC 1997)
Consistent hashing — the algorithm behind every distributed cache.

### Akamai's CDN papers (various)
Search "Akamai SIGCOMM" for foundational CDN architecture papers.

---

## Concurrency / consistency

### ⭐ Linearizability: A Correctness Condition for Concurrent Objects (Herlihy, Wing — 1990)
The formal definition of linearizable.
**Read for**: vocabulary you'll use for the rest of your career.

### CAP Twelve Years Later (Brewer — IEEE 2012)
The clarifying follow-up to the original CAP theorem talk.

### Highly Available Transactions: Virtues and Limitations (Bailis et al. — VLDB 2014)
What "weakly consistent" actually means.

### ⭐ Designing Data-Intensive Applications (Kleppmann — book, 2017)
Not a paper; the synthesis of all of the above. **If you read one thing on this list, read this book.**

---

## Networking-adjacent fault tolerance

### ⭐ The Byzantine Generals Problem (Lamport, Shostak, Pease — 1982)
Background for blockchain + BFT consensus.
**Read for**: classical formulation; skip the proofs unless going into BFT.

### Practical Byzantine Fault Tolerance (Castro, Liskov — OSDI 1999)
The first practical BFT algorithm.

### Honeybadger BFT (Miller et al. — CCS 2016)
Modern asynchronous BFT.

---

## ML systems

### ⭐ Attention is All You Need (Vaswani et al. — NeurIPS 2017)
Transformers. The most-cited ML paper of the decade.

### TensorFlow: A System for Large-Scale Machine Learning (Abadi et al. — OSDI 2016)
Dataflow graph + worker fleet.

### Scaling Distributed Machine Learning with the Parameter Server (Li et al. — OSDI 2014)
Parameter server architecture.

### Megatron-LM and Pathways (Google) — modern LLM training infra.

---

## Reading order — a 12-week curriculum

| Week | Paper |
|---|---|
| 1 | GFS |
| 2 | MapReduce |
| 3 | Bigtable |
| 4 | Dynamo |
| 5 | Paxos Made Simple |
| 6 | Raft |
| 7 | Spanner |
| 8 | Kafka |
| 9 | Flink (or Dataflow) |
| 10 | LSM-Tree |
| 11 | Linearizability |
| 12 | Pick one of: BBR, F1, Borg, ZooKeeper |

After this curriculum, you'll have the vocabulary and intuition for ~90% of any system-design interview question.

---

## Where to find them

- **Papers We Love** (`paperswelove.org`) — curated list with discussion videos.
- **morningpaper.acm.org** (Adrian Colyer) — daily summaries; an entire archive worth mining.
- **dblp.org** — search by author/title.
- **Sci-Hub / arXiv** — for free PDFs.
- **The Morning Paper** archive — Colyer's posts for ~5 years; gold standard summaries.

If a paper feels impossible, find Colyer's summary first; it's usually a third the length and 80% of the substance.
