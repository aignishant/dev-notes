# Glossary

> Every technical term used across the bible, defined in plain English. If a term in any chapter wasn't clear, look it up here.

<span class="phase-status phase-done">Phase 14 — Resources</span>

---

## A

**ABR (Adaptive Bitrate)**
Streaming technique where the player switches video quality (bitrate) based on available bandwidth. HLS and DASH both implement ABR.

**ACID**
Database transaction guarantees: **A**tomicity (all-or-nothing), **C**onsistency (constraints preserved), **I**solation (concurrent txns don't interfere), **D**urability (committed data survives crash).

**Aho-Corasick**
String-matching algorithm that finds many patterns in text simultaneously. Used in spam filters, intrusion detection.

**Amortised**
Average cost over a sequence of operations. Python `list.append` is amortised O(1) — most appends are constant; occasional resizes are O(N), but spread across N appends → O(1) average.

**Anti-entropy**
Process by which replicas reconcile divergent state. Merkle trees + repair sweeps in Cassandra are the canonical example.

**API Gateway**
The "front door" that auth, rate-limit, route, and observe traffic for a fleet of microservices. Examples: Envoy, Kong, AWS API Gateway.

**A***
Heuristic-guided shortest-path algorithm. Uses an admissible heuristic to prune the search.

**At-least-once delivery**
Message will be delivered ≥ 1 time. Consumers must be idempotent.

**At-most-once delivery**
Message will be delivered ≤ 1 time (may be lost). Cheaper but unreliable.

---

## B

**B-tree**
Balanced multi-way search tree. Disk-friendly. Powers MySQL, Postgres, SQLite indexes.

**Backtracking**
Search technique that builds candidates incrementally and abandons (backtracks) when a candidate can't be extended.

**Bellman-Ford**
Shortest-path algorithm that handles negative edge weights. O(VE).

**BFS (Breadth-First Search)**
Graph traversal that explores neighbours level by level. Finds unweighted shortest path.

**BFT (Byzantine Fault Tolerance)**
Consensus despite arbitrary (including malicious) failures. Required for blockchains.

**Bloom filter**
Space-efficient probabilistic set. Says "definitely not in set" or "probably in set." False positives possible; false negatives never.

**Bucket sort**
Sort by distributing items into buckets, then sorting each. O(N+K) for uniformly distributed input.

---

## C

**Cache stampede / Thundering herd**
When a popular cache entry expires, many simultaneous requests recompute it. Mitigation: locking, soft TTL, request coalescing.

**CAP theorem**
A distributed system can guarantee at most 2 of: Consistency, Availability, Partition-tolerance. In practice, partition is unavoidable, so the choice is C-vs-A.

**Cardinality**
Number of distinct values. "User_id has high cardinality"; "country has low cardinality."

**Cassandra**
Wide-column, eventually-consistent KV. Dynamo-inspired.

**Causal consistency**
If A happens-before B, every replica sees A before B. Concurrent ops can be reordered freely.

**CDN (Content Delivery Network)**
Geographically distributed caching layer. Serves static content from the edge close to users.

**Checkpoint**
Periodic snapshot of in-memory state to disk. Lets a system recover from crash without replaying the full log.

**CMAF (Common Media Application Format)**
Container format for streaming; enables LL-HLS and DASH from a single pipeline.

**Compaction**
LSM-tree process that merges multiple SSTable files into fewer larger ones, deduplicating and removing tombstones.

**Consistent hashing**
Hashing scheme where adding/removing a node only relocates K/N keys. Used in caches, KV stores.

**Consumer group**
Kafka concept. A group of consumers cooperatively reading a topic; each partition is owned by exactly one consumer in the group.

**CRDT (Conflict-free Replicated Data Type)**
Data structure designed for eventually-consistent merging without conflicts. Used in collaborative editing.

---

## D

**DAG (Directed Acyclic Graph)**
Directed graph with no cycles. Used in build systems, workflow orchestration, dependency resolution.

**DDoS (Distributed Denial of Service)**
Coordinated attack from many sources to overwhelm a service.

**Deadlock**
Two or more threads each waiting for a resource the other holds. None makes progress.

**Delta encoding**
Storing only the difference between versions, not the full data. Saves bandwidth/space.

**DFS (Depth-First Search)**
Graph traversal that explores as deep as possible before backtracking. Used for cycle detection, topological sort.

**Dijkstra's algorithm**
Shortest-path algorithm for non-negative weights. O((V+E) log V) with a heap.

**DLL (Doubly Linked List)**
Linked list with prev + next pointers. O(1) removal of arbitrary nodes when given a reference.

**DLQ (Dead-Letter Queue)**
Queue holding messages that failed processing after max retries. Operator inspection / manual replay.

**DNS (Domain Name System)**
Translates hostnames to IPs. Hierarchical, distributed, cached.

**Druid / Pinot**
OLAP databases for sub-second analytical queries on streaming data.

**DSU (Disjoint Set Union / Union-Find)**
Data structure for tracking partitions of a set. O(α(N)) per op with path compression + rank.

**Dynamo / DynamoDB**
Amazon's eventually-consistent KV. Inspired Cassandra.

**Dynamic programming (DP)**
Optimisation technique that decomposes problems into overlapping subproblems and memoises results.

---

## E

**Eager / lazy evaluation**
Eager: compute immediately. Lazy: defer until needed. Streams/iterators are lazy.

**Edge cache**
Cache located at the network edge (CDN POP, browser). First line of defense for read-heavy systems.

**Erasure coding**
Storage redundancy via parity. Tolerates K failures with less overhead than K+1× replication.

**Eventual consistency**
All replicas converge to the same state if no new writes happen. Reads may see stale data temporarily.

**Exactly-once delivery**
Message delivered precisely once. Hard in distributed systems; usually = at-least-once + idempotent consumer.

**Expiry / TTL (Time To Live)**
How long a cache entry remains valid before being evicted/refetched.

---

## F

**Failover**
Automatic transition to a standby when the primary fails.

**Fanout**
Distributing a single message to many consumers. Push-fanout (write copy to each), pull-fanout (read at query time).

**FIFO (First In First Out)**
Queue ordering. Opposite: LIFO (stack).

**Flink**
Streaming computation engine. Watermarks, exactly-once.

**Flow control**
Mechanism to prevent a fast producer from overwhelming a slow consumer. TCP windowing, reactive streams.

**FST (Finite State Transducer)**
Compressed trie that maps strings to values. Used in Lucene's term index.

**Functional dependency / determinant**
In database normalisation, X → Y means X determines Y.

---

## G

**Garbage collection (GC)**
Automatic memory management. Pauses (stop-the-world) are a common bottleneck in JVM systems.

**Geohash / H3**
Encoding lat/lng into a single string/integer for spatial indexing.

**gRPC**
RPC framework using HTTP/2 + Protocol Buffers. Lower latency than REST.

**Gossip protocol**
Decentralised information dissemination — each node periodically syncs with random peers. Used in Cassandra, Consul.

---

## H

**HDFS (Hadoop Distributed File System)**
Append-mostly distributed file system. NameNode + DataNodes.

**Heartbeat**
Periodic "I'm alive" signal between nodes. Absence = node assumed dead.

**Heap**
Tree-based priority queue. Min-heap = smallest at root.

**HLL (HyperLogLog)**
Probabilistic data structure for cardinality estimation. ~12 KB → estimate billions of uniques with ~1% error.

**HLS (HTTP Live Streaming) / DASH**
Adaptive video-streaming protocols. HLS = Apple; DASH = MPEG.

**Hot key / hot partition**
A single key receiving disproportionate traffic, overloading one shard. Mitigation: salt the key, replicate.

**HPA (Horizontal Pod Autoscaler)**
Kubernetes feature that scales pod replicas based on CPU/memory/custom metrics.

---

## I

**Idempotency**
Property where repeated execution of an operation has the same effect as one execution. Critical for at-least-once systems.

**Idempotency key**
Client-provided unique ID per intended operation; server dedupes on retry.

**ILM (Index Lifecycle Management)**
Elasticsearch / OpenSearch policy for transitioning indices through hot → warm → cold → delete.

**Indexing**
Pre-computing data structures to speed up reads at the cost of write speed.

**Ingest**
Writing data into a system (logs, analytics, streaming).

**ISR (In-Sync Replica)**
Kafka set of replicas that are caught up with the leader.

---

## J

**Jaccard similarity**
Set similarity = |A ∩ B| / |A ∪ B|. Used in near-duplicate detection.

**JIT (Just-In-Time compilation)**
Compile bytecode → native code at runtime. JVM, V8, PyPy.

**JMX**
Java metrics exposure. Often used by Kafka, Cassandra.

**Journal / WAL (Write-Ahead Log)**
Append-only durable log. All mutations go here first; system state is rebuilt by replaying.

---

## K

**KMP (Knuth-Morris-Pratt)**
String matching in O(N + M) by precomputing failure function.

**Knapsack**
Classic DP: pick items with max value subject to weight constraint.

**KRaft**
Kafka's Raft-based metadata service replacing ZooKeeper.

**Kubernetes**
Container orchestrator. Schedules pods across nodes; provides service discovery, scaling, rollouts.

---

## L

**Lamport clock / vector clock**
Logical time. Lamport: single counter; vector: per-node counters. Used to order events in distributed systems.

**Latency**
Time from request to response. p50, p99, p99.9 percentiles matter more than average.

**Leader election**
Choosing one node from a group as the primary. Raft, ZooKeeper, etcd.

**Linearizability**
The strongest single-object consistency: every operation appears to take effect at some instant between its start and finish. Easy to reason about; expensive to provide.

**LL-HLS (Low-Latency HLS)**
Variant of HLS with chunked transfer for ~2 s latency vs ~10 s.

**Load balancer**
Distributes requests across backends. L4 (TCP) or L7 (HTTP).

**LSM tree (Log-Structured Merge tree)**
Storage engine optimised for writes: in-memory memtable + immutable SSTables on disk + background compaction.

**LRU (Least Recently Used)**
Cache eviction policy: evict the least-recently-accessed item.

---

## M

**MapReduce**
Distributed batch processing. Map → shuffle → reduce.

**Memcached**
In-memory KV cache; simpler than Redis; sharded by client.

**Memoisation**
Caching function results for the same input. Foundation of top-down DP.

**Merkle tree**
Tree of hashes; comparing roots tells you whether two large datasets are equal in O(1). Used in anti-entropy, blockchains, Git.

**Microservice**
Small, independently deployable service owning a single domain.

**MQTT**
Lightweight pub/sub protocol for IoT.

**mTLS (mutual TLS)**
Both client and server present certificates. Server-to-server auth in service meshes.

---

## N

**Nagle's algorithm**
TCP optimisation that batches small packets. `TCP_NODELAY` disables it for low-latency apps.

**NoSQL**
Catch-all for non-relational stores: KV (Dynamo), document (Mongo), wide-column (Cassandra), graph (Neo4j).

---

## O

**OLAP / OLTP**
**O**n**L**ine **A**nalytical **P**rocessing — ad-hoc analytical queries (Druid, ClickHouse). **O**n**L**ine **T**ransaction **P**rocessing — many small ACID transactions (Postgres, MySQL).

**Outbox pattern**
Reliable event publishing: write event + business state in one DB transaction; separate process reads from outbox table and publishes.

---

## P

**Partition tolerance**
A system continues operating when network divides it into groups that can't communicate.

**Paxos**
Family of consensus algorithms. Famously hard to implement; Raft is the more approachable alternative.

**PII (Personally Identifiable Information)**
Names, emails, addresses, etc. Subject to regulation (GDPR, CCPA).

**Polling vs push**
Polling: client periodically asks for updates. Push: server sends as they happen. Push scales better; polling is simpler.

**Pratt parser**
Top-down operator-precedence parser.

**Pre-aggregation / rollup**
Computing aggregates (counts, sums) at ingest to make queries cheap. Druid, Pinot core technique.

**Prefix sum / cumulative sum**
Pre-compute `prefix[i] = sum(arr[0..i])`. Lets you query range sums in O(1).

**Push fanout vs pull fanout**
Push: write copy of each post to every follower's timeline. Pull: query followees at read time. Hybrid is the production answer.

---

## Q

**QPS (Queries Per Second)**
Throughput measure. Often used loosely to mean RPS (requests/sec).

**QUIC**
UDP-based transport that powers HTTP/3.

**Quorum**
Minimum number of nodes that must agree for a write/read to be considered successful. R + W > N → strong consistency.

---

## R

**Raft**
Consensus algorithm; simpler than Paxos. Powers etcd, Consul, CockroachDB.

**Rate limiting**
Capping requests per (client, time window). Token bucket, leaky bucket, sliding window.

**RBAC (Role-Based Access Control)**
Permissions assigned to roles; users get roles. Simpler than per-user grants.

**RCU (Read-Copy Update)**
Linux kernel synchronisation: readers don't lock; writers create new copy + atomic swap.

**Read repair**
Lazy consistency repair: when a read finds divergent replicas, write the merged value back.

**Redis**
In-memory KV with rich data types (lists, sets, sorted sets, streams). Persistence optional.

**Replication**
Maintaining copies of data on multiple nodes. Sync = wait for replicas before ack; async = ack first, replicate after.

**RESTful**
HTTP-based API style. Resources, verbs (GET/POST/PUT/DELETE), stateless.

**Retry budget**
Cap on retries to prevent retry storms during partial outages.

**Rolling deploy / blue-green / canary**
Deploy strategies. Rolling: replace one at a time. Blue-green: stand up parallel fleet, switch. Canary: small % first, expand.

---

## S

**Saga**
Multi-step transaction with compensating actions for rollback. Used when distributed 2PC is too expensive.

**Sharding**
Splitting data across multiple nodes by some key. Horizontal partitioning.

**Sigmoid / softmax**
ML activation functions. Sigmoid: scalar → (0,1). Softmax: vector → probability distribution.

**SimHash**
Locality-sensitive hash. Similar inputs → similar hashes (Hamming-close). Used in near-duplicate detection.

**Sloppy quorum**
Quorum write that includes "next-best" nodes if primaries are down. Combined with hinted handoff.

**Snowflake ID**
Twitter's distributed unique-ID scheme: timestamp + machine ID + sequence.

**SPOF (Single Point of Failure)**
Component whose failure brings down the system. Goal: eliminate them.

**SRE (Site Reliability Engineering)**
Google's practice of running production systems with software-engineering rigour. SLOs, error budgets, postmortems.

**SSTable (Sorted String Table)**
Immutable on-disk file in an LSM engine. Sorted, with sparse index + bloom filter.

**Stale read**
A read that returns data older than the latest committed write. Common in eventually-consistent systems.

**Sticky session**
Load balancer routes a user's requests to the same backend. Simpler stateful apps; complicates scaling.

---

## T

**TCP three-way handshake**
SYN → SYN-ACK → ACK. Connection establishment.

**Throttling**
Rejecting / delaying requests when over rate. Mitigates overload.

**Tombstone**
Marker indicating a deleted record. LSM trees use tombstones; full delete happens during compaction.

**Topological sort**
Linear ordering of a DAG such that for every edge u → v, u precedes v.

**Transaction**
Group of operations executed atomically. ACID provides guarantees.

**Trie (Prefix Tree)**
Tree where each edge is labelled with a character; paths spell strings. Used for autocomplete, IP routing.

**Two-phase commit (2PC)**
Distributed transaction protocol. Coordinator + participants. Blocking; bad for high availability.

---

## U

**UDP**
Datagram protocol. Unreliable, fast. Used in DNS, gaming, voice.

**Upsert**
"Update if exists, insert otherwise."

---

## V

**Vector clock**
Per-node counter map. Lets you determine if events are causally related or concurrent.

**Vnode (virtual node)**
Each physical node owns many virtual positions on the consistent-hash ring. Smoother rebalance on add/remove.

---

## W

**WAL (Write-Ahead Log)**
See *Journal*.

**Watermark**
Streaming concept: timestamp threshold beyond which events are considered late. Enables event-time semantics.

**WebSocket**
Persistent bidirectional connection over TCP. Used for chat, live updates.

**Window**
Streaming aggregation boundary: tumbling (non-overlapping), sliding (overlapping), session (gap-bounded).

**Write amplification**
Ratio of bytes written to disk vs bytes written by application. LSM compaction can be 10×+.

---

## Z

**ZooKeeper**
Coordination service. Sequential nodes, watches, leader election. Used by Kafka pre-KRaft, HDFS, Hadoop.

**zstd**
Modern compression: 3× faster than gzip, similar ratio. Default for Kafka, ClickHouse, RocksDB.

---

## Greek letters used

- **α (alpha)** — inverse Ackermann function. Effectively constant for any input N up to 2^65536.
- **σ (sigma)** — alphabet size in string algorithms.
- **ε (epsilon)** — small number; "ε-approximation" = within ε of optimal.
- **Δ (delta)** — change / difference.
- **λ (lambda)** — anonymous function; rate parameter.
- **μ (mu)** — mean / mu-recursion.
- **θ (theta)** — tight asymptotic bound (vs O = upper, Ω = lower).
- **π (pi)** — failure function in KMP; constant 3.14159…
