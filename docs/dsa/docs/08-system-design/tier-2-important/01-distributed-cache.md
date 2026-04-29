# Distributed Cache (Redis-style)

> A multi-node in-memory cache shared across services. Cuts DB load by 10-100×. Asked at every product company.

<span class="phase-status phase-done">Phase 16 — Tier 2</span>

---

## 1. 🎤 Scenario

> *"Design a distributed cache like Redis / Memcached. It must be horizontally scalable, support TTLs, survive node failures, and serve at sub-millisecond p99 latency."*

A 45-60 minute SD round. Interviewer probes:

- **Sharding** — how does data spread across nodes?
- **Replication** — how do we survive node loss?
- **Eviction** — what happens when memory fills?
- **Consistency** — is `set` then `get` guaranteed to see the new value?

---

## 2. ❓ Clarifying questions

1. **Workload mix?** Read-heavy (90/10) typical.
2. **Eviction needed?** Yes — fixed memory per node.
3. **Persistence?** Snapshot to disk? Replay log?
4. **Consistency model?** Strong, eventual, or session?
5. **Multi-region?** Single-region first; geo-replicate as v2.
6. **TTL granularity?** Per-key seconds-precision typically.
7. **Auth?** Internal cluster behind VPC; ACL inside.

---

## 3. ✅ Requirements

**Functional**

- `GET key` → value or miss.
- `SET key value [EX seconds]` → success.
- `DEL key`.
- `EXPIRE key seconds`.
- `INCR key` (atomic counter).

**Non-functional**

- p99 < 1 ms intra-DC reads.
- 99.99% availability.
- 10M ops/sec across cluster.
- Memory ≤ 80% before eviction kicks in.
- Survive single-node loss with no data loss for replicated keys.

**Out of scope (v1)**

- Multi-region replication.
- Pub/sub channels.
- Lua scripting (mention as extension).

---

## 4. 📐 Capacity estimation

- 1 KB avg value × **100 M keys** = **100 GB** working set.
- p99 < 1 ms read budget → memory only; no disk on hot path.
- 10 M ops/sec ÷ ~200 K ops/sec/node = **50 nodes** minimum.
- Replicated 2× → **100 nodes**.
- Network: 10 M ops × 1 KB = **80 Gbps** intra-cluster.

---

## 5. 🏛️ High-level architecture

```mermaid
flowchart LR
  C[Clients] --> P[Smart proxy / library<br/>computes shard]
  P -->|hash(key)| S1[Shard 1<br/>Primary]
  P -->|hash(key)| S2[Shard 2<br/>Primary]
  P --> S3[Shard 3<br/>Primary]
  S1 -.async repl.-> R1[Replica 1]
  S2 -.async repl.-> R2[Replica 2]
  S3 -.async repl.-> R3[Replica 3]
  S1 & S2 & S3 --> M[Cluster manager<br/>health + topology]
```

- **Smart client** owns the hash ring → routes directly to the right shard. No proxy hop on the hot path.
- **Cluster manager** (Sentinel-style) holds topology + handles failover.
- **Replication** is async per primary → 1 hot standby.

---

## 6. 💾 Data model

Pure in-memory. Per shard:

| Key type | Implementation |
|---|---|
| String | `dict[str, bytes]` + ttl heap |
| Hash | `dict[str, dict[str, bytes]]` |
| List | doubly-linked list |
| Set | `set[bytes]` |
| Sorted set | skiplist + dict |
| Counter | int64 with atomic incr |

Plus a **TTL min-heap** per shard for lazy + active expiry.

---

## 7. 🌐 API

```
GET     /key                   →  200 value | 404 miss
PUT     /key {value, ttl}      →  204
DELETE  /key                   →  204
POST    /key/incr              →  200 {value}
```

In production, use the binary RESP protocol (Redis) or memcached-text — they are 10× cheaper than JSON over HTTP/1.1.

---

## 8. 🧩 Component deep-dive

### Consistent hashing — the routing core

```python
import bisect
import hashlib


class HashRing:
    def __init__(self, vnodes: int = 150):
        self.vnodes = vnodes
        self._ring: list[int] = []           # sorted hashes
        self._hash_to_node: dict[int, str] = {}

    def _hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node_id: str):
        for i in range(self.vnodes):
            h = self._hash(f"{node_id}#{i}")
            bisect.insort(self._ring, h)
            self._hash_to_node[h] = node_id

    def remove_node(self, node_id: str):
        keep = [h for h in self._ring if self._hash_to_node[h] != node_id]
        self._ring = keep
        self._hash_to_node = {
            h: self._hash_to_node[h] for h in keep
        }

    def get_node(self, key: str) -> str:
        if not self._ring:
            raise RuntimeError("empty ring")
        h = self._hash(key)
        idx = bisect.bisect(self._ring, h) % len(self._ring)
        return self._hash_to_node[self._ring[idx]]
```

??? note "Why virtual nodes?"

    A bare ring with N physical nodes has variance issues — when one leaves, all its keys move to one neighbour. With ~150 vnodes per physical node, removal redistributes uniformly across all surviving nodes. DynamoDB and Cassandra both use this trick.

### Per-shard storage

```python
import time
import heapq
from threading import RLock


class ShardStore:
    def __init__(self, max_bytes: int):
        self.data: dict[str, bytes] = {}
        self.expires: dict[str, float] = {}
        self.expiry_heap: list[tuple[float, str]] = []   # (deadline, key)
        self.bytes_used = 0
        self.max_bytes = max_bytes
        self.lock = RLock()

    def set(self, k: str, v: bytes, ttl_s: float | None = None):
        with self.lock:
            self._lazy_expire()
            self._evict_if_needed(len(v))
            if k in self.data:
                self.bytes_used -= len(self.data[k])
            self.data[k] = v
            self.bytes_used += len(v)
            if ttl_s is not None:
                deadline = time.time() + ttl_s
                self.expires[k] = deadline
                heapq.heappush(self.expiry_heap, (deadline, k))

    def get(self, k: str) -> bytes | None:
        with self.lock:
            self._lazy_expire()
            return self.data.get(k)

    def _lazy_expire(self):
        now = time.time()
        while self.expiry_heap and self.expiry_heap[0][0] <= now:
            _, k = heapq.heappop(self.expiry_heap)
            # Validate — entry could have been refreshed
            if self.expires.get(k, float("inf")) <= now:
                self._delete(k)

    def _evict_if_needed(self, incoming: int):
        # Random-LRU sample (Redis-style): pick K random keys, evict oldest
        K = 5
        while self.bytes_used + incoming > self.max_bytes and self.data:
            sample = list(self.data.keys())[:K]    # deterministic for tests
            victim = sample[0]                      # in real: by LRU stamp
            self._delete(victim)

    def _delete(self, k: str):
        v = self.data.pop(k, None)
        if v is not None:
            self.bytes_used -= len(v)
        self.expires.pop(k, None)
```

### Replication (async)

```python
class Primary:
    def __init__(self, store: ShardStore, replicas: list["Replica"]):
        self.store = store
        self.replicas = replicas

    async def set(self, k, v, ttl=None):
        self.store.set(k, v, ttl)
        # Fire-and-forget; replicas catch up via op log
        for r in self.replicas:
            asyncio.create_task(r.replay({"op": "SET", "k": k, "v": v, "ttl": ttl}))
```

Strong consistency would require quorum writes (Raft), at the cost of latency. **Most caches choose async** — if you lose a few sub-second writes during failover, the source of truth (DB) refills the cache.

---

## 9. 📈 Scaling journey

| Stage | Setup | Trade-off |
|---|---|---|
| Day 1 | Single node Redis | < 5 GB; no HA |
| Month 1 | Primary + replica | Read scaling; manual failover |
| Year 1 | 16 shards × 2 replicas | Automated failover via Sentinel |
| Year 2 | 64 shards; consistent hashing | Self-managed routing |
| Year 3 | Geo-replicated; CRDTs for active-active | Eventual consistency across regions |

---

## 10. ☁️ Cloud deployment

- **AWS**: ElastiCache (Redis cluster mode) — sharded, replicated, automatic failover. Cost: ~$0.04/hr per cache.r6g.large.
- **GCP**: Memorystore for Redis — similar offering.
- **Azure**: Cache for Redis Premium tier — clustering + persistence.

Self-managed on EC2: ~30% cheaper but you own ops (failover scripts, AMI hardening, patch cycles).

---

## 11. 🏠 On-prem / local

- **Docker Compose** for dev: 3 Redis nodes + Sentinel.
- **Kubernetes** with the Redis Operator (Bitnami / Spotahome) for prod.
- Bare-metal: Linux + numactl + huge pages (2 MB pages cut TLB miss rate ~5×).

---

## 12. 🏗️ Architecture deep-dive

??? question "Why client-side sharding instead of proxy?"

    A proxy adds a hop (50-200 µs) and a single point of contention. Smart clients embed the hash ring; routing is 0.5 µs of CPU. Twemproxy / mcrouter are valid alternatives if you can't ship a fat client.

??? question "Failover sequence on primary loss"

    1. Sentinel detects via gossip (~5 s).
    2. Quorum vote elects new primary from replicas.
    3. Topology update broadcast to clients.
    4. Clients invalidate their hash ring → start writing to new primary.
    5. Old primary, on rejoin, becomes a replica.

---

## 13. 🧨 Bottlenecks + fixes

| Bottleneck | Fix |
|---|---|
| Hot key on one shard | Add a local L1 cache; key-level replication; randomised key shading (`key#1`, `key#2`) |
| Big-object stalls (e.g. 50 MB value) | Reject > N bytes; encourage chunking |
| TTL storm (1 M keys expire same second) | Add jitter ±10% to TTLs |
| Network saturation on replication | Compress; rate-limit replication channel |
| GC pauses (managed languages) | Use C/Rust core; off-heap allocators |

---

## 14. 🔒 Security

- **TLS** between clients and cluster.
- **ACLs** per user (Redis 6+): commands + key-prefix scoped.
- **VPC isolation** in cloud; never expose the cache port publicly.
- **Encryption at rest** for snapshots (KMS-managed keys).
- **Audit log** for admin commands.

---

## 15. 📊 Monitoring

| Signal | Why |
|---|---|
| `ops/sec` per shard | Hot-shard detection |
| Hit / miss ratio | Cache effectiveness |
| Memory % used | Eviction pressure |
| Replication lag | Failover risk |
| p99 GET latency | The user-visible SLO |
| Connection count | Approaching `maxclients` |

Alert if any shard hit-ratio drops > 10% week-over-week.

---

## 16. 🧱 Reliability

- **Circuit breaker** in the client: skip cache + go to DB on shard outage.
- **Stale-while-revalidate**: serve expired entry while async-refreshing.
- **Bulk-eviction throttling**: cap deletions to 1 K/sec to avoid blocking the event loop.
- **Chaos testing**: kill a primary in prod once a quarter (Netflix Chaos Monkey-style).

---

## 17. ❓ Follow-up questions

??? question "What's the difference between Redis and Memcached?"

    Memcached: pure key-value, multi-threaded, no persistence. Redis: rich types (lists, sets, sorted sets), single-threaded, persistence (RDB/AOF), replication, pub/sub, Lua. Use Memcached for raw speed on simple KV; Redis for everything else.

??? question "Cache-aside vs write-through vs write-back?"

    - **Cache-aside**: app reads cache, on miss reads DB + writes cache. Simple, can serve stale.
    - **Write-through**: writes go to cache + DB synchronously. Strong consistency, slower writes.
    - **Write-back**: writes go to cache; async flushed to DB. Fastest, can lose data on crash. Mostly used for ephemeral stats.

??? question "How do you invalidate a cache?"

    "There are only two hard things…" Patterns: TTL (simplest), explicit `DEL` from the writer, pub/sub fanout to invalidate, version stamps in keys (`user:42:v3`).

??? question "What if the cache is down?"

    App falls back to DB. Use circuit breaker so the app doesn't keep hammering. Pre-warm cache before declaring it healthy again.

??? question "Thundering herd on cold cache?"

    Use **request coalescing**: first request misses + computes; concurrent requests for the same key wait on the same future. Twitter calls this "single-flight".

---

## 18. 🐍 Python tricks

```python
# Consistent hashing in 8 lines (rough)
def shard_for(key: str, ring: list[tuple[int, str]]) -> str:
    h = int(hashlib.md5(key.encode()).hexdigest(), 16)
    idx = bisect.bisect_left([k for k, _ in ring], h) % len(ring)
    return ring[idx][1]

# Lazy + active expiry combo
def get(self, k):
    if k in self.expires and time.time() >= self.expires[k]:
        self._delete(k)
        return None
    return self.data.get(k)
```

---

## 19. 🌍 Real-world references

- **Redis architecture** — antirez's blog (the founder).
- **AWS ElastiCache best practices** — official whitepaper.
- **Memcached at Facebook** — *Scaling Memcache at Facebook* (NSDI '13). McRouter, regional pools, lease keys.
- **Twitter cache-aside patterns** — engineering blog.
- **DynamoDB DAX** — for the DynamoDB-coupled case.

---

## 20. 🃏 Cheatsheet

- **Sharding**: consistent hashing with vnodes (~150).
- **Replication**: async primary→replica; sentinel for failover.
- **Eviction**: random-LRU sampling (Redis style); approximation is fine.
- **Expiry**: lazy on read + active probe sweep.
- **Consistency**: pick eventual; cache is not the truth.
- **Hot key**: local L1 + key shading.
- **Failure mode**: bypass → DB; circuit breaker.
- **Numbers**: 200 K ops/sec/node; p99 < 1 ms intra-DC.
