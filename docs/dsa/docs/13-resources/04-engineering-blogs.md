# Engineering Blogs

> The blogs that consistently publish substantive content. Skim weekly; read deeply when relevant. Each entry includes one **landmark post** worth reading even if you read nothing else from that source.

<span class="phase-status phase-done">Phase 14 — Resources</span>

---

## Top-tier — read religiously

### Netflix Tech Blog

`netflixtechblog.com`

- Open Connect (CDN), microservices migration, chaos engineering, A/B testing platform.
- **Landmark**: *"How Netflix Scales its API"* — how they evolved from monolith to BFF (backend-for-frontend) pattern.

### Uber Engineering

`eng.uber.com`

- Real-time dispatch, geo-spatial systems (H3 hex grid), Cadence (now Temporal), schemaless DB.
- **Landmark**: *"H3: Uber's Hexagonal Hierarchical Spatial Index"* — geo-indexing at city scale.

### Stripe Engineering

`stripe.com/blog/engineering`

- Idempotency, distributed systems, payments at scale, API design.
- **Landmark**: *"Designing robust and predictable APIs with idempotency"* — the gold standard on idempotency keys.

### Discord Engineering

`discord.com/category/engineering`

- Storing trillions of messages on Cassandra/ScyllaDB, real-time voice, Elixir at scale.
- **Landmark**: *"How Discord Stores Trillions of Messages"* — bucketed Cassandra schema design.

### Cloudflare Blog

`blog.cloudflare.com`

- DDoS mitigation, BGP, TLS performance, Workers (edge compute), DNS internals.
- **Landmark**: *"How we built the most efficient inverse proxy"* — Pingora / Rust replacement of nginx.

### Meta Engineering

`engineering.fb.com`

- TAO graph, social graph at scale, MySQL hacks, Hack/HHVM, content moderation infra.
- **Landmark**: *"TAO: The power of the graph"* — social graph caching layer.

### Google Research / Google Cloud blog

`research.google` and `cloud.google.com/blog`

- Distributed systems papers, ML infra, search ranking architecture.
- **Landmark**: *"Spanner: Google's Globally-Distributed Database"* (also a paper) — TrueTime + globally consistent transactions.

### High Scalability

`highscalability.com`

- Aggregator: weekly summaries of how systems scale. Excellent breadth.
- **Landmark**: any post tagged "real life architecture" — case studies.

---

## Strong tier — sample regularly

### Slack Engineering — `slack.engineering`
Sharded Mailbox service, websocket scaling, search.
**Landmark**: *"Real-time messaging at Slack scale."*

### Airbnb Engineering — `medium.com/airbnb-engineering`
Search ranker, React Native at scale, ML at the platform level.
**Landmark**: *"Embedding-based Real-time Search at Airbnb."*

### LinkedIn Engineering — `engineering.linkedin.com`
Kafka was born here; Pinot, Espresso, feed ranking.
**Landmark**: *"Kafka: a Distributed Messaging System for Log Processing."*

### GitHub Engineering — `github.blog/category/engineering`
MySQL at scale, Git internals, Actions infra.
**Landmark**: *"Partitioning GitHub's relational databases to handle scale."*

### Shopify Engineering — `shopify.engineering`
Pod sharding, Black-Friday-prep posts, Rails at scale.
**Landmark**: *"How Shopify Scales to Handle Flash Sales from Kanye West."*

### Dropbox Tech Blog — `dropbox.tech`
Magic Pocket (custom storage), edge network, Atlas.
**Landmark**: *"Inside the Magic Pocket"* — exabyte-scale custom storage.

### Twitch Engineering — `blog.twitch.tv/engineering`
Live streaming infra, transcoder fleet, IRC chat at scale.
**Landmark**: *"How VODs are Made at Twitch."*

### DoorDash Engineering — `doordash.engineering`
Dispatch, ETA modeling, Cassandra usage.
**Landmark**: *"Building DoorDash's Cassandra Cluster."*

### Spotify Engineering — `engineering.atspotify.com`
Backstage (developer portal), recommendation infra, audio delivery.
**Landmark**: *"Discover Weekly: How Spotify Mastered Personalization."*

### Pinterest Engineering — `medium.com/pinterest-engineering`
Image serving at scale, search ranking, ML platform.
**Landmark**: *"Pinterest's Backbone: how we scale to 250M MAU."*

### Booking.com — `booking.ai` and `medium.com/booking-com-data-science`
Search ranking, A/B testing, ML in production.
**Landmark**: *"150 successful machine learning models at Booking.com."*

### Reddit Engineering — `reddit.com/r/RedditEng`
Sharded Postgres, comment ranking, real-time feeds.
**Landmark**: *"How Reddit Scaled to 100M+ users."*

### Lyft Engineering — `eng.lyft.com`
Envoy was born here; pricing, dispatch, Locust load-testing.
**Landmark**: *"Announcing Envoy: a Service Mesh Story."*

### Yelp Engineering — `engineeringblog.yelp.com`
Search infra, Kafka at scale, real-time recommendations.

### Pinterest, Quora, Asana, Reddit — all have solid engineering blogs at varying frequency.

---

## Specialised blogs

### Databases / Storage
- **CockroachDB** (`cockroachlabs.com/blog`) — distributed SQL
- **TigerBeetle** (`tigerbeetle.com/blog`) — financial DB design
- **PlanetScale** (`planetscale.com/blog`) — Vitess at scale
- **MotherDuck / DuckDB** — embedded OLAP
- **Materialize** — streaming SQL
- **TimescaleDB** — time-series Postgres

### Search / Information retrieval
- **Elastic blog** — Elasticsearch internals
- **Algolia blog** — search-as-you-type
- **Vespa** — Yahoo's search/recommendation platform

### Streaming / messaging
- **Confluent blog** — Kafka deep dives
- **Materialize** — incremental view maintenance
- **RisingWave** — streaming SQL

### ML platforms
- **Anthropic / OpenAI engineering blogs** (when available)
- **Hugging Face blog** — training infra
- **Eugene Yan** (`eugeneyan.com`) — practical ML systems
- **Chip Huyen** (`huyenchip.com`) — designing ML systems

### Performance / low-level
- **Brendan Gregg** (`brendangregg.com`) — Linux performance
- **Marc Brooker** (`brooker.co.za`) — AWS/distributed systems insights
- **Aphyr / Jepsen** (`jepsen.io`) — DB consistency testing
- **Daniel Lemire** (`lemire.me`) — micro-optimisation, SIMD

### Cloud-native / infra
- **AWS Architecture Blog** — well-architected patterns
- **Google Cloud Blog** — case studies + GCP internals
- **Microsoft Azure Architecture Center** — reference architectures

---

## Aggregators worth subscribing to

- **High Scalability** — weekly system architecture deep-dives
- **The Pragmatic Engineer** (Gergely Orosz) — paid newsletter, big-tech insider perspectives
- **Pointer.io** — curated engineering links weekly
- **Architecture Notes** (`architecturenotes.co`) — visual system design breakdowns
- **System Design Newsletter** — weekly digest
- **ByteByteGo** (Alex Xu) — visual system design

---

## How to read engineering blogs

1. **Subscribe to RSS, not email.** Feedly + a 30-min Saturday session > daily distractions.
2. **Read the landmark posts of the top 10 first.** That's ~20 hours of reading and it'll outpace 6 months of skimming new posts.
3. **Note down the patterns, not the products.** "Booking.com built a per-property availability cache" → the takeaway is *availability cache as a pattern*, not "we should use Booking.com's stack."
4. **Trace one architecture per week.** Print it; redraw it from memory; identify the parts you'd struggle to explain. Read those parts again.
5. **Beware survivorship bias.** Every blog post is the success story. The systems that didn't work don't get blog posts.

---

## What to read on a 4-hour flight

If you have a single block of 4 hours:

1. *"How Discord Stores Trillions of Messages"* (Discord)
2. *"TAO: The power of the graph"* (Meta)
3. *"H3: Uber's Hexagonal Spatial Index"* (Uber)
4. *"Designing robust APIs with idempotency"* (Stripe)
5. *"Inside the Magic Pocket"* (Dropbox)
6. *"How Netflix scales its API"* (Netflix)
7. *"Real-time messaging at Slack scale"* (Slack)
8. *"Kafka: A Distributed Messaging System"* (LinkedIn paper)

That's the curriculum. Eight posts ≈ four hours ≈ roughly the foundation knowledge for an interview at any of these companies.
