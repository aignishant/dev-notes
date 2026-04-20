# 18 — Microservices: Complete Interview Guide
## Scenario-Based Questions with Python Examples

> **Cross-reference:** File 06 (System Design), File 07 (Async), File 09 (DevOps), File 17 (FastAPI)

---

## 18.1 Microservices Fundamentals

### Q1: What are microservices? Explain core principles.

**Answer:**

```
Microservices = Architecture style where an application is a collection of
small, independent, loosely-coupled services.

Core Principles:
  1. Single Responsibility:  Each service does ONE thing well
  2. Independent Deployment:  Deploy one service without affecting others
  3. Decentralized Data:      Each service owns its database
  4. API-First Communication: Services talk via APIs, not shared memory
  5. Fault Isolation:         One service failure shouldn't cascade
  6. Technology Diversity:    Each service can use different tech stack

Monolith vs Microservices:
┌──────────────────────────────────────────────────────────────┐
│ MONOLITH                                                     │
│ ┌─────────────────────────────────────────────────────────┐  │
│ │  Users │ Orders │ Payments │ Notifications │ Analytics  │  │
│ │              Shared Database                            │  │
│ └─────────────────────────────────────────────────────────┘  │
│ Single deployment unit                                       │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ MICROSERVICES                                                │
│                     API Gateway                              │
│                    ┌─────────┐                               │
│        ┌──────────┤         ├──────────┐                    │
│        ▼          ▼         ▼          ▼                    │
│   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐             │
│   │ User   │ │ Order  │ │Payment │ │Notify  │             │
│   │Service │ │Service │ │Service │ │Service │             │
│   │PostgreSQL│ │MongoDB│ │Stripe  │ │Redis   │             │
│   └────────┘ └────────┘ └────────┘ └────────┘             │
│   Each has its own database and deployment                   │
└──────────────────────────────────────────────────────────────┘
```

---

### Q2: When should you NOT use microservices?

**Answer:**

```
❌ DO NOT use microservices when:
  - Small team (< 5 developers)
  - Simple domain with few features
  - Startup MVP phase (build monolith first, split later)
  - Tight coupling between domains (everything needs everything)
  - No DevOps maturity (no CI/CD, no containerization)

✅ USE microservices when:
  - Large team (> 10 developers, multiple squads)
  - Independent scaling needs (search service needs 10x compute)
  - Different tech requirements (ML service needs GPUs)
  - Rapid, independent deployments needed
  - Fault isolation is critical (payment failure shouldn't break search)

The "Monolith First" approach (recommended by Martin Fowler):
  Phase 1: Build well-structured monolith with clear module boundaries
  Phase 2: Identify pain points (scaling, deployment, team ownership)
  Phase 3: Extract services one at a time where it makes sense
```

---

## 18.2 Communication Patterns

### Q3: Explain synchronous vs asynchronous communication between services.

**Answer:**

```python
# ═══════════════════════════════════════
# SYNCHRONOUS: REST / gRPC — Request/Response
# ═══════════════════════════════════════
# Use when: You need an immediate response
# Examples: User login, get product details, validate payment

# Order service calls User service directly
import httpx

class UserServiceClient:
    def __init__(self, base_url="http://user-service:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=5.0)

    async def get_user(self, user_id: int):
        try:
            response = await self.client.get(f"{self.base_url}/users/{user_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        except httpx.ConnectError:
            raise ServiceUnavailable("User service is down")

# With circuit breaker pattern
class CircuitBreaker:
    """Prevents cascading failures by failing fast when service is down."""
    def __init__(self, failure_threshold=5, recovery_timeout=30):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None
        self.state = "CLOSED"   # CLOSED → OPEN → HALF_OPEN → CLOSED

    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise ServiceUnavailable("Circuit breaker OPEN")

        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise

user_circuit = CircuitBreaker(failure_threshold=5, recovery_timeout=30)

async def get_user_safe(user_id):
    return await user_circuit.call(user_client.get_user, user_id)


# ═══════════════════════════════════════
# ASYNCHRONOUS: Message Queue — Event-Driven
# ═══════════════════════════════════════
# Use when: You DON'T need immediate response
# Examples: Send email, update analytics, generate report

# Publisher (Order Service)
"""
import aio_pika

async def publish_order_created(order):
    connection = await aio_pika.connect("amqp://rabbitmq:5672")
    channel = await connection.channel()
    exchange = await channel.declare_exchange("orders", aio_pika.ExchangeType.TOPIC)

    await exchange.publish(
        aio_pika.Message(
            body=json.dumps({
                "event": "order.created",
                "order_id": order.id,
                "user_id": order.user_id,
                "total": order.total,
                "timestamp": datetime.utcnow().isoformat()
            }).encode()
        ),
        routing_key="order.created"
    )
"""

# Consumer (Notification Service)
"""
async def on_order_created(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body)
        await send_order_confirmation_email(
            user_id=data["user_id"],
            order_id=data["order_id"]
        )
"""
```

---

### Q4: What is an API Gateway? Why is it important?

```
API Gateway sits between clients and microservices.

Client → API Gateway → [Service A, Service B, Service C]

Responsibilities:
  1. Request Routing:    Route /users to User Service, /orders to Order Service
  2. Authentication:     Validate JWT tokens once, not in every service
  3. Rate Limiting:      Protect services from abuse
  4. Load Balancing:     Distribute requests across service instances
  5. Response Caching:   Cache frequent responses
  6. Request Aggregation: Combine multiple service responses into one
  7. Protocol Translation: REST → gRPC, WebSocket → HTTP
  8. Logging/Monitoring: Centralized request logging

Tools: Kong, Traefik, AWS API Gateway, Nginx, FastAPI (custom)
```

```python
# Simple API Gateway with FastAPI
from fastapi import FastAPI, Request
import httpx

gateway = FastAPI(title="API Gateway")

SERVICE_REGISTRY = {
    "users": "http://user-service:8000",
    "orders": "http://order-service:8001",
    "products": "http://product-service:8002",
}

@gateway.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(service: str, path: str, request: Request):
    if service not in SERVICE_REGISTRY:
        raise HTTPException(404, "Service not found")

    # Forward request to appropriate service
    target_url = f"{SERVICE_REGISTRY[service]}/{path}"

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            content=await request.body(),
            params=request.query_params,
        )

    return JSONResponse(
        status_code=response.status_code,
        content=response.json()
    )
```

---

## 18.3 Data Management

### Q5: How do you handle data consistency across microservices?

```python
"""
Each service owns its database → No shared database!
Challenge: How to maintain consistency across services?

═══════════════════════════════════════
Pattern 1: SAGA — Distributed transactions as a sequence of local transactions
═══════════════════════════════════════

Order Saga (Choreography):
  1. Order Service:   Create order (status=PENDING)
  2. Payment Service: Charge customer (listen for order.created)
  3. Inventory Service: Reserve stock (listen for payment.completed)
  4. Order Service:   Confirm order (listen for stock.reserved)

  If any step fails → Compensating actions (rollback):
  - Payment failed → Cancel order
  - Stock unavailable → Refund payment → Cancel order
"""

# Saga Orchestrator pattern
class OrderSaga:
    """Orchestrates the order creation process across services."""

    def __init__(self, order_service, payment_service, inventory_service):
        self.order_svc = order_service
        self.payment_svc = payment_service
        self.inventory_svc = inventory_service

    async def create_order(self, user_id: int, items: list) -> dict:
        order = None
        payment = None

        try:
            # Step 1: Create order
            order = await self.order_svc.create(user_id, items, status="PENDING")

            # Step 2: Process payment
            payment = await self.payment_svc.charge(user_id, order.total)

            # Step 3: Reserve inventory
            await self.inventory_svc.reserve(items)

            # Step 4: Confirm order
            await self.order_svc.update_status(order.id, "CONFIRMED")
            return {"order_id": order.id, "status": "CONFIRMED"}

        except PaymentError as e:
            # Compensate: Cancel order
            if order:
                await self.order_svc.update_status(order.id, "CANCELLED")
            raise

        except InventoryError as e:
            # Compensate: Refund + cancel order
            if payment:
                await self.payment_svc.refund(payment.id)
            if order:
                await self.order_svc.update_status(order.id, "CANCELLED")
            raise


"""
═══════════════════════════════════════
Pattern 2: Event Sourcing — Store events, derive state
═══════════════════════════════════════
Instead of storing current state, store ALL events.
Current state = replay all events.

Events:
  1. OrderCreated(order_id=1, items=[...], total=99.99)
  2. PaymentProcessed(order_id=1, payment_id=42)
  3. ItemShipped(order_id=1, tracking="ABC123")

Benefits:
  - Complete audit trail
  - Can rebuild state at any point in time
  - Natural fit for event-driven microservices

═══════════════════════════════════════
Pattern 3: CQRS — Separate read and write models
═══════════════════════════════════════
Command (Write):  Optimized for writes → normalized DB
Query (Read):     Optimized for reads → denormalized/cached
Sync via events between write and read sides.
"""
```

---

## 18.4 Scenario-Based Microservices Questions

### Scenario 1: "Service A depends on Service B, which is down. How do you handle this?"

**Answer:**

```python
"""
Multiple strategies depending on the situation:
"""

# Strategy 1: Circuit Breaker (prevent cascading failures)
# Already shown above — fail fast instead of waiting

# Strategy 2: Fallback / Degraded mode
async def get_product_recommendations(user_id):
    try:
        # Try ML recommendation service
        return await recommendation_service.get(user_id)
    except ServiceUnavailable:
        # Fallback: return popular products instead
        return await get_popular_products()    # Cached, always available

# Strategy 3: Cache previous responses
async def get_user_profile(user_id):
    # Try live service first
    try:
        profile = await user_service.get(user_id)
        await cache.set(f"profile:{user_id}", profile, ttl=3600)
        return profile
    except ServiceUnavailable:
        # Return cached version
        cached = await cache.get(f"profile:{user_id}")
        if cached:
            return {**cached, "_cached": True}  # Flag as stale
        raise

# Strategy 4: Retry with backoff
# See File 13, Scenario 10

# Strategy 5: Bulkhead pattern — isolate resource pools
"""
Service A has separate thread/connection pools for each dependency:
  - Pool for Service B: 20 threads
  - Pool for Service C: 10 threads
  - Pool for Database: 15 threads

If Service B exhausts its pool, Service C and Database still work.
Without bulkhead: Service B exhausts ALL threads → entire Service A down.
"""
```

---

### Scenario 2: "You need to migrate from monolith to microservices. How?"

**Answer:**

```
Step-by-step migration (Strangler Fig Pattern):

Phase 1: Identify Boundaries
  - Map domain boundaries (DDD: Bounded Contexts)
  - Example: User Management, Order Processing, Inventory, Notifications

Phase 2: Introduce API Gateway
  ┌────────┐     ┌──────────┐     ┌──────────┐
  │ Client │────▶│ Gateway  │────▶│ Monolith │
  └────────┘     └──────────┘     └──────────┘
  Gateway routes ALL traffic to monolith initially.

Phase 3: Extract first service (lowest risk)
  Choose: Notifications (independent, low coupling)
  ┌────────┐     ┌──────────┐     ┌──────────┐
  │ Client │────▶│ Gateway  │──┬─▶│ Monolith │
  └────────┘     └──────────┘  │  └──────────┘
                               │  ┌────────────┐
                               └─▶│Notification│
                                  │  Service   │
                                  └────────────┘

Phase 4: Extract more services one at a time
  Priority: Most independent → most coupled
  Each extraction:
    1. Create new service with its own DB
    2. Migrate data
    3. Route traffic via gateway
    4. Remove code from monolith
    5. Monitor for issues

Phase 5: Monolith becomes another service or disappears
```

---

### Scenario 3: "How do you trace a request across 5 microservices?"

**Answer:**

```python
"""
Distributed Tracing: Follow a request across multiple services

Tools: Jaeger, Zipkin, OpenTelemetry, AWS X-Ray

Concept:
  - Trace ID: Unique ID for the entire request chain
  - Span:     One operation within a service
  - Parent Span: Links spans together

Request flow:
  Client → API Gateway → Order Service → Payment Service → Notification Service
  Trace ID: abc-123 follows through ALL services
"""

# OpenTelemetry with FastAPI
"""
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Setup
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(agent_host_name="jaeger", agent_port=6831)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Auto-instrument FastAPI and HTTPX
FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()

# Custom spans for business logic
tracer = trace.get_tracer("order-service")

async def create_order(user_id, items):
    with tracer.start_as_current_span("create_order") as span:
        span.set_attribute("user_id", user_id)
        span.set_attribute("item_count", len(items))

        with tracer.start_as_current_span("validate_inventory"):
            await inventory_service.check(items)

        with tracer.start_as_current_span("process_payment"):
            await payment_service.charge(user_id, total)

        span.set_attribute("order.status", "completed")
"""

# Correlation ID middleware (simpler alternative)
import uuid

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

# Pass correlation ID to downstream services
async def call_downstream(url, correlation_id):
    async with httpx.AsyncClient() as client:
        return await client.get(url, headers={"X-Correlation-ID": correlation_id})
```

---

### Scenario 4: "Two services need the same data. How do you handle it?"

```
Options:

1. API Call (Synchronous):
   Order Service → GET /users/123 → User Service
   ✅ Always fresh data
   ❌ Runtime dependency, latency, failure coupling

2. Event-Driven Data Replication:
   User Service → publishes "user.updated" → Order Service stores local copy
   ✅ No runtime dependency
   ❌ Eventual consistency (data might be stale for seconds)
   ✅ Best for: Read-heavy, tolerates slight staleness

3. Shared Library / Package:
   Common data definitions in a shared package
   ✅ Code reuse
   ❌ Creates coupling, versioning challenges

4. API Composition (at Gateway level):
   Gateway calls both services, merges responses
   ✅ Services stay independent
   ❌ Gateway complexity

RECOMMENDATION:
  - If service B RARELY needs data from A → API call + cache
  - If service B FREQUENTLY needs data from A → Event-driven local copy
  - If data consistency is CRITICAL → Synchronous API call
```

---

### Scenario 5: "How do you deploy and version microservice APIs?"

```python
"""
API Versioning Strategies:

1. URL versioning (most common):
   /api/v1/users
   /api/v2/users

2. Header versioning:
   Accept: application/vnd.myapp.v2+json

3. Query parameter:
   /api/users?version=2
"""

# FastAPI versioning
from fastapi import APIRouter

# v1 router
v1_router = APIRouter(prefix="/api/v1")

@v1_router.get("/users/{user_id}")
async def get_user_v1(user_id: int):
    """V1: Returns basic user info."""
    return {"id": user_id, "name": "Alice"}

# v2 router — extended response
v2_router = APIRouter(prefix="/api/v2")

@v2_router.get("/users/{user_id}")
async def get_user_v2(user_id: int):
    """V2: Returns extended user info with preferences."""
    return {"id": user_id, "name": "Alice", "preferences": {}, "avatar_url": "..."}

app.include_router(v1_router)
app.include_router(v2_router)

"""
Deployment Strategies:

1. Blue-Green Deployment:
   Blue (current) ← traffic
   Green (new) — test, then switch traffic
   Instant rollback: switch back to Blue

2. Canary Deployment:
   Route 5% traffic to new version
   Monitor metrics (error rate, latency)
   Gradually increase to 100%

3. Rolling Deployment:
   Replace instances one at a time
   Old and new versions run simultaneously briefly

4. Feature Flags:
   Deploy code, but toggle features via config
   if feature_flags.is_enabled("new_checkout"):
       return new_checkout_flow()
   else:
       return old_checkout_flow()
"""
```

---

### Scenario 6: "How do you handle service discovery?"

```
Problem: Services need to find each other, but IPs change (containers restart, scale).

Solutions:

1. DNS-based (Kubernetes default):
   service-name.namespace.svc.cluster.local
   K8s automatically resolves to current pods

2. Service Registry (Consul, Eureka):
   Services register on startup, deregister on shutdown
   Others query registry to find service instances

3. Environment Variables:
   USER_SERVICE_URL=http://user-service:8000
   Simple but requires restart to update

4. Sidecar Proxy (Service Mesh — Istio, Linkerd):
   Each service has a proxy sidecar that handles:
   - Service discovery
   - Load balancing
   - TLS encryption
   - Retry/timeout
   - Observability
```

---

### Scenario 7: "Design a notification microservice"

```python
"""
Requirements:
  - Send notifications via email, SMS, push, in-app
  - Handle 100K+ notifications/day
  - Priority support (urgent vs normal)
  - Template management
  - Delivery tracking

Architecture:
  ┌──────────┐     ┌──────────────┐     ┌────────────────┐
  │ Any      │────▶│ Notification │────▶│ Kafka/RabbitMQ │
  │ Service  │     │ API          │     │ Priority Queues│
  └──────────┘     └──────────────┘     └───────┬────────┘
                                                │
                                    ┌───────────┼────────────┐
                                    ▼           ▼            ▼
                              ┌──────────┐ ┌─────────┐ ┌─────────┐
                              │ Email    │ │ SMS     │ │ Push    │
                              │ Worker   │ │ Worker  │ │ Worker  │
                              │(SendGrid)│ │(Twilio) │ │(Firebase)│
                              └──────────┘ └─────────┘ └─────────┘
"""

# Notification Service API
from fastapi import FastAPI
from pydantic import BaseModel
from enum import Enum

class Channel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"

class Priority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class NotificationRequest(BaseModel):
    user_id: int
    channels: list[Channel]
    template_id: str
    template_data: dict
    priority: Priority = Priority.NORMAL

@app.post("/notifications")
async def send_notification(request: NotificationRequest):
    """Queue notification for delivery."""
    for channel in request.channels:
        queue_name = f"notifications.{request.priority.value}"

        await message_broker.publish(
            queue=queue_name,
            message={
                "user_id": request.user_id,
                "channel": channel.value,
                "template_id": request.template_id,
                "template_data": request.template_data,
                "created_at": datetime.utcnow().isoformat(),
            }
        )

    return {"status": "queued", "channels": request.channels}
```

---

## 18.5 Microservices Checklist — Senior Interview

```
✅ Can you explain when NOT to use microservices?
✅ Do you understand the CAP theorem?
✅ Can you design a SAGA for distributed transactions?
✅ Do you know circuit breaker, bulkhead, retry patterns?
✅ Can you implement event-driven architecture?
✅ Do you understand eventual consistency?
✅ Can you set up distributed tracing?
✅ Do you know service discovery and API gateway patterns?
✅ Can you design a migration from monolith?
✅ Do you understand database-per-service pattern?
✅ Can you handle service versioning and backward compatibility?
✅ Do you know deployment strategies (blue-green, canary)?
```

---
