# 🏛️ System Design

> 25+ projects, fully designed end-to-end. Cloud + on-prem + architecture.

<span class="phase-status phase-done">Phase 16 — Tier 1 complete + Tier 2 batch 1 (4 designs)</span>

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

## ✅ Tier 2 — first batch (4 of 20 live)

<div class="grid cards" markdown>

-   :material-database-cog: **[Distributed Cache (Redis-style)](tier-2-important/01-distributed-cache.md)**

    ---

    Sharded in-memory KV with consistent hashing, async replication, lazy + active expiry. The infrastructure piece behind every tier-1 design.

-   :material-bell-ring: **[Notification Service](tier-2-important/02-notification-service.md)**

    ---

    Push + email + SMS at 1 B/day. Two-stage Kafka pipeline (resolve → deliver), idempotency via Redis SETNX, frequency caps + quiet hours, HTTP/2 multiplexed APNs.

-   :material-spider: **[Web Crawler](tier-2-important/03-web-crawler.md)**

    ---

    Politely fetch billions of pages with per-domain queues, Bloom-filter URL dedup, SimHash content dedup, headless-Chrome lane for JS-heavy sites.

-   :material-magnify-plus: **[Search Autocomplete](tier-2-important/04-search-autocomplete.md)**

    ---

    Sub-50 ms suggestions via FST + per-node top-K. Edge cache collapses 10× QPS; hourly index swap; trending injection through Kafka stream.

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
