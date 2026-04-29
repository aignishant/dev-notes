# 🏛️ System Design

> 25+ projects, fully designed end-to-end. Cloud + on-prem + architecture.

<span class="phase-status phase-done">Phase 17 — All Tier 1 + Tier 2 + Tier 3 live (30 designs)</span>

When complete, this section will be a **complete system-design book**, larger and more detailed than Alex Xu's *System Design Interview* (vols 1 & 2 combined).

---

## ✅ Tier 1 — The Core 5 (all five live)

<div class="grid cards" markdown>

-   :material-link-variant: **[URL Shortener (TinyURL/Bitly)](tier-1-core/01-url-shortener.md)**

    ---

    The canonical first SD problem. Base62 encoding, 100B URLs, 350K reads/sec. Read-heavy, cache-heavy. The **template** for every other design page.

-   :material-twitter: **[Twitter / X Feed](tier-1-core/02-twitter-feed.md)**

    ---

    Social timeline at 500M MAU. Push vs pull fanout, the celebrity problem, hybrid model. Snowflake IDs, Redis ZSET timelines, Kafka fanout.

-   :material-play-circle: **[YouTube / Netflix (video streaming)](tier-1-core/03-video-streaming.md)**

    ---

    Petabyte-scale video at 2B MAU. Adaptive bitrate, HLS/DASH, transcode farm, multi-CDN, Open-Connect-style edge caches. Egress is the cost.

-   :material-car: **[Uber / Lyft (ride sharing)](tier-1-core/04-ride-sharing.md)**

    ---

    Real-time matching at 30M rides/day. H3 spatial index, surge pricing, per-city sharding, idempotent payments, trip state machine.

-   :material-chat: **[WhatsApp / Messenger (chat)](tier-1-core/05-realtime-chat.md)**

    ---

    Hundreds of millions of persistent connections. E2E (Signal protocol), at-least-once + dedupe, multi-device sync, push fallback. Erlang/OTP scale.

</div>

Every page follows the same 20-section shape. Once you've read one, you've read the contract for them all.

---

## ✅ Tier 2 — Important 18 (all live)

<div class="grid cards" markdown>

-   :material-database-cog: **[Distributed Cache (Redis-style)](tier-2-important/01-distributed-cache.md)**

    ---

    Sharded in-memory KV with consistent hashing, async replication, lazy + active expiry. The infrastructure piece behind every tier-1 design.

-   :material-bell-ring: **[Notification Service](tier-2-important/02-notification-service.md)**

    ---

    Push + email + SMS at 1 B/day. Two-stage Kafka pipeline, idempotency via Redis SETNX, frequency caps + quiet hours, HTTP/2 multiplexed APNs.

-   :material-spider: **[Web Crawler](tier-2-important/03-web-crawler.md)**

    ---

    Politely fetch billions of pages with per-domain queues, Bloom-filter URL dedup, SimHash content dedup, headless-Chrome lane for JS-heavy sites.

-   :material-magnify-plus: **[Search Autocomplete](tier-2-important/04-search-autocomplete.md)**

    ---

    Sub-50 ms suggestions via FST + per-node top-K. Edge cache collapses 10× QPS; hourly index swap; trending injection through Kafka stream.

-   :material-instagram: **[Instagram (photo feed)](tier-2-important/05-instagram.md)**

    ---

    Hybrid push/pull fanout with celebrity threshold; Redis ZSET timelines capped at 1K; Snowflake IDs; CDN-fronted media.

-   :material-folder-sync: **[Dropbox / Google Drive](tier-2-important/06-dropbox.md)**

    ---

    Content-defined chunking with rolling hash; SHA-keyed block dedup; namespace-partitioned metadata; conflict resolution.

-   :material-chart-line: **[Stock Exchange / Trading](tier-2-important/07-stock-exchange.md)**

    ---

    Per-symbol single-threaded matching engine; LMAX Disruptor ring buffer; nanosecond order book with bid/ask heaps.

-   :material-code-tags: **[Online Code Judge](tier-2-important/08-online-judge.md)**

    ---

    Sandboxed execution via nsjail/Firecracker; per-language time multipliers; Redis ZSET leaderboard; winnowing-fingerprint plagiarism.

-   :material-food: **[Food Delivery (DoorDash/Swiggy)](tier-2-important/09-food-delivery.md)**

    ---

    OrderState machine with allowed-transition map; Redis GEO dispatcher; ML ETA = prep + travel + last-mile; H3-cell surge.

-   :material-cart: **[E-commerce (Amazon)](tier-2-important/10-ecommerce.md)**

    ---

    Saga checkout (reserve → charge → confirm); Redis WATCH inventory reservation with TTL; multi-warehouse partitioning.

-   :material-bed: **[Hotel / Stay Booking](tier-2-important/11-hotel-booking.md)**

    ---

    FOR UPDATE inventory date-row locking; two-stage search (ES top-200 → availability filter); currency locked at quote time.

-   :material-credit-card: **[Payment System (Stripe)](tier-2-important/12-payment-system.md)**

    ---

    Append-only double-entry ledger; idempotency cache pattern; multi-acquirer router; webhook retries up to 12 h.

-   :material-cursor-default-click: **[Ad Click Tracking](tier-2-important/13-ad-click-tracking.md)**

    ---

    HMAC-signed URLs; Redis SET NX dedup; Flink streaming aggregation; dual-write Druid + Redis; sub-150 ms bot filter.

-   :material-file-document-multiple: **[Distributed Logging](tier-2-important/14-distributed-logging.md)**

    ---

    Kafka → parser → ES (hot) + S3 (cold); ILM rollover; per-tenant per-day indices; schema-on-read with allowlist.

-   :material-broadcast: **[Live Streaming (Twitch)](tier-2-important/15-live-streaming.md)**

    ---

    RTMP/SRT regional ingest; GPU ABR transcode; CMAF chunked → LL-HLS for ~2 s lag; multi-CDN egress.

-   :material-clipboard-list-outline: **[Distributed Task Queue](tier-2-important/16-distributed-task-queue.md)**

    ---

    Redis Streams broker; consumer groups for at-least-once; ZSET delayed jobs; exponential-backoff retries → DLQ; per-tenant fairness.

-   :material-chart-multiline: **[Real-Time Analytics (Druid)](tier-2-important/17-real-time-analytics.md)**

    ---

    Kafka in → realtime indexer + batch indexer; rollup at ingest with HLL; bitmap-indexed columnar segments; sub-30 s freshness.

-   :material-gamepad-variant: **[Online Multiplayer Game](tier-2-important/18-online-multiplayer-game.md)**

    ---

    UDP authoritative server at 60 Hz; client-side prediction + reconciliation; delta-encoded snapshots; MMR matchmaking; anti-cheat.

</div>

---

## ✅ Tier 3 — Bonus 5 (all live)

<div class="grid cards" markdown>

-   :material-folder-network: **[Distributed File System (HDFS)](tier-3-bonus/01-distributed-file-system.md)**

    ---

    NameNode/DataNode split; rack-aware 3× replication; QJM edit log; tiered storage; erasure coding for cold data.

-   :material-key-variant: **[Distributed KV Store (Dynamo)](tier-3-bonus/02-distributed-kv-store.md)**

    ---

    Consistent-hashing ring with vnodes; tunable R/W/N quorums; vector clocks; Merkle anti-entropy; hinted handoff.

-   :material-message-bulleted: **[Pub/Sub System (Kafka)](tier-3-bonus/03-pubsub-system.md)**

    ---

    Partitioned append-only log; ISR replication with high-watermark; consumer-group rebalance; idempotent + transactional producers.

-   :material-gate: **[API Gateway (Envoy/Kong)](tier-3-bonus/04-api-gateway.md)**

    ---

    Plugin chain (TLS → auth → rate limit → proxy → log); JWKS cache; Redis Lua token-bucket; circuit breakers; xDS hot reload.

-   :material-source-branch: **[CI/CD Pipeline](tier-3-bonus/05-cicd-pipeline.md)**

    ---

    DAG scheduler from YAML; ephemeral runners with warm pool; content-addressed cache; OIDC-federated secrets; cosign-signed artifacts.

</div>

---

## The 30 projects

### Tier 1: The Core 5 (~40 pages each — deepest dives)

1. **URL Shortener** (TinyURL/Bitly)
2. **Twitter/X Feed** (social media timeline)
3. **YouTube/Netflix** (video streaming)
4. **Uber/Lyft** (ride sharing)
5. **WhatsApp/Messenger** (real-time chat)

### Tier 2: The Important 20 (~25 pages each)

6. Instagram · 7. Dropbox/Google Drive · 8. Search Autocomplete · 9. Notification Service · 10. Distributed Cache · 11. Stock Exchange / Trading System · 12. Rate Limiter · 13. Web Crawler · 14. Newsfeed System · 15. Online Code Judge · 16. Food Delivery (Swiggy/Zomato/DoorDash) · 17. E-commerce (Amazon) · 18. Hotel/Stay Booking (Booking.com / Airbnb) · 19. Payment System (PayPal / UPI) · 20. Ad Click Tracking · 21. Distributed Logging · 22. Live Streaming · 23. Distributed Task Queue · 24. Real-time Analytics · 25. Online Multiplayer Game Backend.

### Tier 3 Bonus (~15 pages each)

26. Distributed File System (HDFS-like) · 27. Distributed Key-Value Store (DynamoDB-like) · 28. Pub/Sub System (Kafka-like) · 29. API Gateway · 30. CI/CD Pipeline System.

---

## Each project page contains 20 sections

(Quoting the v3 spec — every project gets all of these, fully written.)

1. The interview scenario
2. Clarifying questions (functional + non-functional + scope)
3. Requirements (functional, non-functional, out-of-scope)
4. Capacity estimation (back-of-envelope math, with numbers)
5. High-level architecture (Mermaid diagram + read/write paths)
6. Data model & storage choice (SQL vs NoSQL, schema, sharding, indexing, replication)
7. API design (REST/gRPC, request/response shapes, auth, versioning)
8. Component-by-component deep dive (Python code for key pieces)
9. Scaling journey (Day 1 → Year 3 → 100M users)
10. **Cloud deployment** — AWS, GCP, Azure equivalents, cost estimation
11. **Local / on-prem deployment** — bare-metal, Kubernetes, Docker Compose
12. **Architecture deep-dive** — microservices, sync vs async, CQRS, sagas
13. Bottlenecks, trade-offs, fixes
14. Security (AuthN/AuthZ, encryption, DDoS, GDPR, audit logs)
15. Monitoring & observability (RED + USE, logs, traces, alerts, SLO/SLI/SLA)
16. Reliability (circuit breakers, retries, fallbacks, chaos)
17. Common follow-up questions (5–10, fully answered)
18. Python code for tricky pieces (consistent hashing, rate limiter, Bloom filter, LRU, Snowflake IDs…)
19. Real-world references (engineering blogs, public vs speculation, famous outages)
20. One-page cheatsheet (day-of-interview revision card)

Plus: **System design fundamentals** chapters (databases deep-dive, caching, message queues, microservices, cloud primer, Kubernetes, observability stack).

---

In the meantime, head back to [Roadmap](../00-roadmap/index.md).
