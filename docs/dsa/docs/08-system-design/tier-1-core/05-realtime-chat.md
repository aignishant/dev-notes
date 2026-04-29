# WhatsApp / Messenger (real-time chat)

> Design a real-time chat. 1:1 and group messaging, online presence, typing indicators, read receipts, end-to-end encryption, multi-device sync. The "long-lived connections + delivery guarantees" question.

<span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Discord</span> &nbsp; <span class="company-tag">Slack</span> &nbsp; <span class="company-tag">Google</span> &nbsp; <span class="phase-status phase-done">Tier-1 SD design</span>

---

## 1. 🎤 The interview scenario

> *"Design WhatsApp / Messenger. Users can chat 1:1 and in groups (up to 1000 members). Messages must be delivered in order, with delivery + read receipts. End-to-end encrypted. Works across multiple devices per user. Scale: 2B MAU, 100B messages/day, hundreds of millions concurrent connections."*

45-min slot. Interviewers usually push hardest on **how do you maintain 100M+ persistent connections** (gateways) and **how do you guarantee delivery** (offline + retry + dedupe).

---

## 2. ❓ Clarifying questions

### Functional

1. **1:1 only, or groups?** Group size limit?
2. **Multi-device?** Same account on phone + desktop + web?
3. **End-to-end encryption?** WhatsApp yes; Slack no (server can read).
4. **Media?** Images, video, voice notes, files?
5. **Calls?** Voice/video out-of-scope unless explicitly asked.
6. **Read receipts? Typing indicator? Presence?**
7. **Search?** In scope (server-side or client-side)?

### Non-functional

8. **Latency?** p99 message-delivered < 500ms when both online.
9. **Delivery semantics?** At-least-once with dedupe (effectively exactly-once perceived).
10. **Ordering?** Per-conversation FIFO; cross-conversation no guarantee.
11. **Retention?** Forever, or N days? GDPR right-to-delete.
12. **Availability?** 99.99%.

### Defaults

| Question | Assume |
|---|---|
| 1:1 + groups (up to 1000) | yes |
| Multi-device | yes |
| E2E | yes (Signal-style double ratchet) |
| Media | yes, server stores ciphertext blob |
| Retention | forever; right-to-delete supported |

---

## 3. 📋 Requirements

### Functional

- **F1.** Send / receive 1:1 and group messages.
- **F2.** Delivery + read receipts (per-recipient in groups).
- **F3.** Online presence + typing indicator.
- **F4.** Multi-device sync (same conversation on N devices).
- **F5.** Media attachments (image/video/file/voice).
- **F6.** End-to-end encryption.
- **F7.** Search history (client-side under E2E).

### Non-functional

- **N1.** p99 delivery < 500ms when both online.
- **N2.** At-least-once delivery + idempotent client dedupe.
- **N3.** Per-conversation strict order.
- **N4.** 99.99% availability.
- **N5.** Hundreds of millions concurrent persistent connections.
- **N6.** Privacy: server cannot read content (E2E).

### Out of scope

- Voice/video call infra, payments (where supported), business messaging APIs.

---

## 4. 🧮 Capacity estimation

| Metric | Calc | Value |
|---|---|---|
| MAU | given | 2B |
| Concurrent online | ~25% of MAU | **500M** |
| Messages / day | given | 100B |
| Messages / sec (avg) | 100B / 86400 | ~1.15M |
| Messages / sec (peak 3×) | | **~3.5M** |
| Avg msg size (text) | with metadata, ciphertext | ~1 KB |
| Daily storage (text) | 100B × 1 KB | **~100 TB / day** |
| Media storage (10% have media, avg 500 KB) | | **~5 PB / day** |
| Connection servers (each handles ~1M conns) | 500M / 1M | **~500 gateway servers** |

---

## 5. 🏗️ High-level architecture

```mermaid
flowchart LR
    DeviceA[Device A] -->|TLS persistent| GW1[Gateway / Conn Server]
    DeviceB[Device B] -->|TLS persistent| GW2[Gateway / Conn Server]

    GW1 --> Router[Message Router]
    Router --> MsgStore[(Message Store<br/>per-conversation log)]
    Router --> Pub[Pub/Sub Bus]
    Pub --> GW2

    GW2 -->|push (offline)| FCM[FCM / APNs]

    MsgStore --> Storage[(HBase / Cassandra)]
    Router --> Presence[Presence Service]
    Router --> Receipts[Receipts Service]
    DeviceA -->|media upload| Media[Media Service]
    Media --> Object[(S3-class)]
```

### Send path

1. Device A holds a persistent TLS connection to Gateway.
2. Device A encrypts message with recipient's session key (Signal protocol). Sends ciphertext + envelope (recipient_id, conversation_id, msg_id, ts) to Gateway.
3. Gateway forwards to **Router**.
4. Router persists in **Message Store** (per-conversation append-only log).
5. Router publishes on **Pub/Sub bus** keyed by recipient_id.
6. Recipient's Gateway picks up via subscription → pushes over Device B's open connection.
7. If Device B is offline: Router triggers **push notification** (FCM / APNs) and message stays queued.
8. Device B acknowledges receipt → Router updates delivery status, notifies Sender.

### Read receipt path

9. When user opens chat: Device sends READ event for last seen msg_id.
10. Router updates per-recipient receipt; notifies Sender if requested.

### Offline + multi-device

11. Each user has N devices. Per-device "fanout queue" persists messages until each device acks.
12. New device pairing: existing device transfers session keys (E2E preserved).

---

## 6. 📦 Data model & storage

### Message store — per-conversation log (HBase / Cassandra)

```
conversation:<conv_id>:<msg_id> -> {
   sender_id,
   ciphertext,
   envelope_meta,
   server_ts
}
```

- `msg_id` = monotonic per-conversation (server-assigned snowflake).
- Wide-row pattern: rows ordered by `msg_id` for fast range scan.
- TTL optional (vanish messages, GDPR right-to-delete).

### Per-device delivery queue (Redis cluster)

```
queue:<user_id>:<device_id>  -> ZSET of (msg_id, server_ts)
```

Removed on ack from device. If queue grows >N, fall back to push notification only.

### Conversations (catalog DB)

```sql
CREATE TABLE conversations (
    conv_id   BIGINT PRIMARY KEY,
    type      TEXT,          -- DIRECT / GROUP
    created   TIMESTAMP
);

CREATE TABLE conversation_members (
    conv_id   BIGINT,
    user_id   BIGINT,
    role      TEXT,
    joined_at TIMESTAMP,
    PRIMARY KEY (conv_id, user_id)
);

CREATE TABLE user_conversations (
    user_id   BIGINT,
    conv_id   BIGINT,
    last_seen_msg_id BIGINT,
    last_read_msg_id BIGINT,
    PRIMARY KEY (user_id, conv_id)
);
```

### Presence (Redis, ephemeral)

```
presence:<user_id>  -> {status: ONLINE/AWAY/OFFLINE, last_seen, devices: {dev_id: gw_id}}
```

TTL 60s; gateway heartbeats refresh.

### Encryption keys

E2E client-managed. Server only stores **public prekey bundles** (Signal protocol):

```
prekeys:<user_id>:<device_id> -> [identity_key, signed_prekey, one_time_prekeys[]]
```

---

## 7. 🔌 API design

| Method | Path | Description |
|---|---|---|
| WS | `/v1/connect` | Persistent TLS WebSocket / custom protocol. |
| GET | `/v1/conversations` | List conversations + last messages. |
| GET | `/v1/conversations/{id}/messages?cursor=...` | History (ciphertext). |
| POST | `/v1/messages` | Send message envelope. |
| POST | `/v1/messages/{id}/ack` | Mark delivered. |
| POST | `/v1/messages/{id}/read` | Mark read. |
| POST | `/v1/media/uploads` | Get presigned URL for ciphertext blob. |
| GET | `/v1/keys/{user_id}/{device_id}` | Fetch prekey bundle. |

**Wire format**: protobuf over TLS. WhatsApp historically used XMPP-derived; Signal uses protobuf.

---

## 8. 🔧 Component-by-component deep dive

### Gateway (long-lived connections)

```python
# Pseudocode — connection server holds millions of TCP sockets via async I/O.
import asyncio

clients: dict[int, "Conn"] = {}  # device_id → Conn

class Conn:
    def __init__(self, device_id: int, user_id: int, writer):
        self.device_id, self.user_id = device_id, user_id
        self.writer = writer

    async def push(self, frame: bytes):
        self.writer.write(frame)
        await self.writer.drain()

async def handle_client(reader, writer):
    auth = await read_frame(reader)             # JWT
    user_id, device_id = verify_jwt(auth)
    conn = Conn(device_id, user_id, writer)
    clients[device_id] = conn
    register_with_presence(user_id, device_id)
    try:
        async for frame in iter_frames(reader):
            await router_send(user_id, device_id, frame)
    finally:
        del clients[device_id]
        deregister_presence(user_id, device_id)
```

In production: epoll/kqueue + Erlang/OTP (WhatsApp's actual choice) or Rust/Go with millions of connections per host.

### Router (delivery)

```python
def route_message(env):
    msg_id = snowflake.next_id()
    msg_store.append(env.conv_id, msg_id, env.ciphertext, env.sender)

    members = list_conversation_members(env.conv_id)
    for m in members:
        if m == env.sender:
            continue
        for dev in user_devices(m):
            redis.zadd(f"queue:{m}:{dev}", {msg_id: server_ts()})
            gw = presence.gateway_for(m, dev)
            if gw:
                pubsub.publish(f"gw:{gw}", encode_push(m, dev, env, msg_id))
            else:
                fcm.queue_push(m, dev, env.conv_id)
    return msg_id
```

### Per-device ack + dedupe

Client tracks last `msg_id` seen per conversation. On reconnect, syncs from `(last_seen_msg_id+1)` forward. Idempotent: same `msg_id` ignored if already applied.

### Group fanout

Per-message: enumerate group members (cap 1000), fanout. For each member's devices, queue + push. For very large groups (~1000) the fanout cost is bounded; for "broadcast lists" or "channels" (millions) use a different fan-out-on-read model.

### Signal Double Ratchet (E2E key schedule)

Each conversation has a Signal session. New message → new symmetric key derived via DH ratchet + chain key. Compromise of one key doesn't compromise past or future messages (forward + post-compromise security).

```python
# Sketch only — production must use audited libs (libsignal).
def encrypt(plaintext, sending_key, sending_chain):
    sending_chain.advance()
    msg_key = sending_chain.derive_msg_key()
    return aes_gcm_encrypt(plaintext, msg_key)
```

---

## 9. 📈 Scaling journey

| Stage | MAU | Architecture |
|---|---|---|
| **Day 1** | <100K | Single gateway, single Postgres. |
| **10M** | 10M | Gateway pool with consistent hash → user-pinned. Redis pub/sub for inter-gateway routing. |
| **500M** | 500M | Sharded message store (per-conversation), Cassandra; FCM/APNs at scale; per-region routing. |
| **2B** | 2B | Multi-region active-active with per-user home region; gossip ring across gateways; Erlang/OTP processes per user. |

**Inflection point**: at ~50M, **single-region gateway breaks** on connection cost. Shard users by region; use regional gateways that exchange via global bus.

---

## 10. ☁️ Cloud deployment

| Layer | AWS | GCP | Azure |
|---|---|---|---|
| Load balancer (TCP) | NLB | TCP LB | LB |
| Gateways | EC2 / EKS, c-class compute | GCE / GKE | VMSS / AKS |
| Pub/Sub bus | MSK / Kinesis | Pub/Sub | Event Hubs |
| Message store | Keyspaces (Cassandra) | Bigtable | Cosmos DB |
| Push | SNS | FCM (native) | Notification Hub |
| Media | S3 + CloudFront | GCS | Blob |
| Presence cache | ElastiCache | Memorystore | Redis Cache |

**Cost**: gateways are CPU-bound on TLS handshake + epoll concurrency. ~$1-2/connection/year at scale; multiply by hundreds of millions concurrent.

---

## 11. 🏠 Local / on-prem deployment

- **Bare-metal**: per-region gateway tier; Cassandra + Kafka self-hosted; HAProxy / Envoy for TLS termination.
- **Docker compose dev**:

```yaml
services:
  gateway: { build: ./gateway, ports: ["8443:8443"] }
  router:  { build: ./router }
  cassandra: { image: cassandra:5 }
  kafka: { image: bitnami/kafka }
  redis: { image: redis:7 }
```

- **Edge gateways**: regional PoPs reduce client latency; encrypted bundles still processed centrally.

---

## 12. 🧬 Architecture deep-dive

### Microservices

| Service | Owns |
|---|---|
| Gateway | Persistent connections, TLS, frame parsing. |
| Router | Persist + dispatch + dedupe. |
| Presence | Online status, last-seen. |
| Receipts | Delivery + read state. |
| Media | Ciphertext blob storage. |
| Key directory | Public prekey bundles. |
| Push | FCM / APNs adapter. |
| Group | Membership + per-conversation metadata. |

### Sync vs async

- Sync within a single hop: gateway ↔ router; router ↔ store.
- Async cross-region: pub/sub bus.

### Why Erlang/OTP at WhatsApp?

Each user → an OTP process. Process supervises connection state, retries, cleanup. Crash isolation: one user crashing doesn't affect others. Scales to millions of concurrent processes per host.

### Sagas

Group "leave conversation" saga: remove from members → emit notice → cancel pending fanouts → recompute prekey directory. Compensations on partial failure.

---

## 13. ⚖️ Bottlenecks & trade-offs

| Bottleneck | Cause | Fix |
|---|---|---|
| TLS handshake CPU | Millions of new connects/min | Session resumption + TCP Fast Open. |
| Group fanout | 1000-member group | Cap, or use channel-mode (fanout-on-read). |
| Hot conversation | Active group with 100 msgs/min | Per-conv shard; back-pressure. |
| Storage growth | 100 TB/day | Tiered storage; compress old; offload to colder media tier. |
| Cross-region delivery | Sender India, recipient US | Write to home region of recipient; replicate via global bus. |

### E2E vs server features

| Feature | Possible under E2E? |
|---|---|
| Search (full-text) | No on server; client-side only. |
| Spam detection | Limited — only via metadata. |
| Forwarding limits | Yes — enforced at metadata layer. |
| Group admin tools | Mostly yes — admin metadata not encrypted. |
| Backup | E2E backup needs user key escrow (cloud backup is opt-in). |

E2E imposes hard tradeoffs. WhatsApp accepts them; Slack doesn't.

---

## 14. 🔒 Security

- **E2E**: Signal protocol — X3DH key agreement + double ratchet. Per-message keys never reused.
- **Forward secrecy** + **post-compromise security**.
- **Sealed sender** (Signal feature, partial WhatsApp) — recipient can verify sender without server seeing identity.
- **Server hardening**: gateways minimal-trust; no plaintext access.
- **Anti-abuse**: flag accounts on metadata patterns (mass-message bursts, brand-new accounts adding many contacts).
- **Lawful access**: WhatsApp can disclose metadata (who messaged whom when), not content.

---

## 15. 📊 Monitoring & observability

| Signal | Metric |
|---|---|
| Latency | Send→ack p99, send→delivered p99 |
| Connections | Concurrent count per gateway, churn rate |
| Lost messages | Acks not received within retry window |
| Push delivery | FCM/APNs success rate |
| Region replication lag | < 2s p99 |

### SLOs

- Delivery success > 99.99% within 30s.
- Cross-region replication p99 < 2s.
- Gateway concurrent connection limit > 1M / host.

---

## 16. 🛡️ Reliability

- **At-least-once + dedupe**: every message has unique server `msg_id`. Client dedupes. Effectively exactly-once perceived.
- **Retry** push if FCM fails; exponential backoff up to 24h, then drop with notice.
- **Gateway failover**: client reconnects to next gateway; sticky-session via consistent hashing on user_id.
- **Backpressure**: if router overloaded, gateways shed load (delay non-message frames).
- **Chaos**: gateway crash test; full region brownout drill quarterly.

---

## 17. 🤔 Common follow-up questions

??? question "How does multi-device work under E2E?"

    Each device has its own identity key; group sessions deliver one message-key per device. New device pairing: existing device transfers per-conversation session keys via QR-code handshake. Server stores prekey bundles for each device.

??? question "How do you guarantee per-conversation order?"

    Server assigns monotonic `msg_id` per `conv_id`. Recipients apply messages in `msg_id` order. If client receives out-of-order, it buffers and waits.

??? question "What happens if 1M users all open the app at once (e.g. football match)?"

    Connection rate spikes hit gateways. Mitigations: TLS session resumption, gradual reconnect (jittered backoff at client), pre-warm capacity by city. Push notifications are the failsafe — even if WS reconnect fails, push still arrives.

??? question "How do you store 100 TB / day forever?"

    Tier: hot (last 30d) on Cassandra SSD; warm (30-365d) on HDD; cold on object store (compressed). Per-conversation rolling indices. Cost: petabytes / year — sustained.

??? question "How do you support 'unsend' / 'delete for everyone'?"

    Server emits a tombstone message addressed to all conversation members. Clients on receipt remove the original from local storage. Deletion is best-effort: a member who never reconnects keeps the message until they sync.

??? question "What about group calls / video?"

    Separate SFU (selective forwarding unit) infrastructure. Out-of-scope here; uses WebRTC + media servers.

??? question "How do you handle a banned user re-registering?"

    Phone-number → identity binding; ban registry checked at registration. Anti-evasion via device fingerprint, but tradeoff with user privacy.

??? question "How do read receipts work in groups?"

    Per-recipient state. Group sender sees "read by N/M". Storage: a small bitset / list per message per group, updated as receipts arrive.

---

## 18. 🐍 Python for tricky pieces

### Idempotent client send (UUID-based dedupe)

```python
import uuid

def send_message(conv_id: str, body: str):
    client_msg_id = str(uuid.uuid4())
    payload = {
        "client_msg_id": client_msg_id,
        "conv_id": conv_id,
        "ciphertext": encrypt(body, conv_id),
    }
    while True:
        try:
            resp = ws.send(payload, timeout=5)
            return resp["server_msg_id"]
        except Timeout:
            continue   # safe; server dedupes on client_msg_id
```

### Server-side dedupe (per-sender bloom filter)

```python
class DedupeWindow:
    def __init__(self):
        self.recent: dict[str, set] = {}      # sender → {client_msg_id seen in last 5 min}

    def is_dup(self, sender: str, client_msg_id: str) -> bool:
        s = self.recent.setdefault(sender, set())
        if client_msg_id in s:
            return True
        s.add(client_msg_id)
        # eviction by time bucket — omitted
        return False
```

### Presence heartbeats

```python
async def heartbeat_loop(user_id: int, device_id: int):
    while connected:
        await redis.hset(f"presence:{user_id}", device_id, gateway_id)
        await redis.expire(f"presence:{user_id}", 60)
        await asyncio.sleep(20)
```

---

## 19. 🌐 Real-world references

- **WhatsApp Engineering** — "1 million tcp connections" classic post on Erlang/FreeBSD tuning.
- **Signal protocol** — https://signal.org/docs (Double Ratchet, X3DH, Sesame).
- **Discord** — "How Discord stores billions of messages" (Cassandra), "How Discord scaled Elixir to 5M concurrent users".
- **Slack** — "Real Time Messaging at Slack" (engineering blog).
- **Famous outage**: Discord Cassandra "tombstone explosion" outage (2017) — taught the industry to TTL-aware row design.

---

## 20. 📝 One-page cheatsheet

```
REAL-TIME CHAT — DAY OF INTERVIEW

REQUIREMENTS
  2B MAU, 500M concurrent online
  100B msgs/day, ~3.5M msgs/sec peak
  p99 delivery <500ms when both online
  At-least-once + dedupe (= exactly-once perceived)
  Per-conversation FIFO
  E2E (Signal protocol)
  Multi-device sync

CAPACITY
  ~500 gateway servers (1M conns each)
  100 TB/day text + 5 PB/day media (ciphertext)

ARCHITECTURE
  Persistent WS to gateway → router → message store
  Pub/sub bus across gateways (cross-region)
  Per-device delivery queue (Redis)
  Push fallback (FCM/APNs) when offline
  Per-conversation monotonic msg_id

E2E
  Signal: X3DH + double ratchet
  Forward + post-compromise secrecy
  Server stores public prekey bundles only
  Multi-device: pair via QR; per-device session

DATA
  conversation:<id> wide row in Cassandra
  user_conversations (last_seen, last_read)
  queue:<user>:<device> (Redis ZSET)
  presence:<user> (Redis, TTL 60s)

DELIVERY
  At-least-once: server retries
  Client dedupes by client_msg_id
  Per-conv FIFO via server-assigned msg_id

GROUPS
  Up to 1000; fanout server-side
  Channels (millions) → fanout-on-read

TRADE-OFFS
  E2E precludes server-side search (client-side only)
  E2E limits spam tools (metadata only)
  Fanout-on-write for groups; fanout-on-read for channels
  Hot/warm/cold storage tiers

RELIABILITY
  Sticky sessions via consistent hash
  Push as failsafe
  Reconnect with jitter
  Chaos: gateway kill weekly

INTERVIEW TIPS
  Ask: 1:1 vs group? E2E? Multi-device?
  Mention long-lived connection scaling
  Don't forget offline + push
  Order = monotonic msg_id, NOT timestamps
```
