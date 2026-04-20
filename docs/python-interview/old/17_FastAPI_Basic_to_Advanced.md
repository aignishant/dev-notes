# 17 — FastAPI: Basic to Advanced
## Complete Interview Questions with Real-World Scenarios

> **Cross-reference:** File 07 (Async), File 08 (ORM), File 11 (Framework Comparison)

---

## 17.1 FastAPI Basics

### Q1: Why FastAPI over Flask/Django? When to choose each?

**Answer:**

```
FastAPI:
  ✅ Async by default (built on Starlette)
  ✅ Automatic OpenAPI/Swagger docs
  ✅ Pydantic validation built-in
  ✅ Type-hint driven — catches errors at dev time
  ✅ Extremely fast (comparable to Node.js/Go)
  Best for: APIs, microservices, ML model serving, real-time apps

Flask:
  ✅ Simple, minimal, easy to learn
  ✅ Huge ecosystem of extensions
  ✅ Synchronous by default (simpler mental model)
  Best for: Small apps, prototypes, legacy sync codebases

Django:
  ✅ Batteries-included (admin, ORM, auth, forms)
  ✅ Mature ecosystem, large community
  ✅ Django REST Framework for APIs
  Best for: Full web apps, admin-heavy apps, rapid prototyping

Decision Guide:
  Building a REST API for microservices → FastAPI
  Building a full web app with admin panel → Django
  Quick prototype or simple webhook → Flask
  Need async + WebSocket + high perf → FastAPI
  Team already knows Django → Django REST Framework
```

---

### Q2: Explain FastAPI's request lifecycle and dependency injection.

```python
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

app = FastAPI(title="User Service", version="2.0.0")

# ═══════════════════════════════════════
# Pydantic Models — request/response validation
# ═══════════════════════════════════════
class UserCreate(BaseModel):
    """Request model — validates incoming data automatically."""
    name: str = Field(..., min_length=2, max_length=50, examples=["Alice"])
    email: EmailStr
    age: int = Field(..., ge=18, le=120)
    role: str = Field(default="user", pattern="^(user|admin|moderator)$")

class UserResponse(BaseModel):
    """Response model — controls what data is returned."""
    id: int
    name: str
    email: str
    role: str
    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    """Partial update — all fields optional."""
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[EmailStr] = None
    age: Optional[int] = Field(None, ge=18, le=120)


# ═══════════════════════════════════════
# Dependency Injection — the core of FastAPI
# ═══════════════════════════════════════

# Simple dependency: Database session
async def get_db():
    """Yields a DB session, ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency with logic: Authentication
async def get_current_user(request: Request, db=Depends(get_db)):
    """Extract and validate auth token."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = await verify_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

# Dependency chain: Role-based access
def require_role(required_role: str):
    """Factory that creates a role-checking dependency."""
    async def role_checker(user=Depends(get_current_user)):
        if user.role != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker


# ═══════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════
@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db=Depends(get_db)):
    """
    Create a new user.

    - **name**: 2-50 characters
    - **email**: Valid email address
    - **age**: 18-120
    """
    # Check duplicate email
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(**user_data.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db=Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    updates: UserUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Partial update — only provided fields are changed."""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Only update fields that were explicitly sent
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db=Depends(get_db),
    admin=Depends(require_role("admin"))
):
    """Admin only — delete a user."""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
```

---

### Q3: How do Query Parameters, Path Parameters, and Request Body work?

```python
from fastapi import Query, Path, Body

@app.get("/products")
async def search_products(
    # Query parameters — from URL: /products?q=laptop&min_price=100&page=1
    q: str = Query(None, min_length=1, max_length=100, description="Search term"),
    category: Optional[str] = Query(None, enum=["electronics", "books", "clothing"]),
    min_price: float = Query(0, ge=0, alias="min-price"),
    max_price: float = Query(10000, le=100000, alias="max-price"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", enum=["price", "name", "created_at"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
):
    """Search products with filtering, sorting, pagination."""
    query = db.query(Product)

    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if category:
        query = query.filter(Product.category == category)

    query = query.filter(Product.price.between(min_price, max_price))
    offset = (page - 1) * per_page
    return query.order_by(sort_by).offset(offset).limit(per_page).all()


@app.get("/products/{product_id}/reviews/{review_id}")
async def get_review(
    # Path parameters — from URL: /products/42/reviews/7
    product_id: int = Path(..., ge=1, description="Product ID"),
    review_id: int = Path(..., ge=1, description="Review ID"),
):
    pass
```

---

## 17.2 Intermediate FastAPI

### Q4: Explain middleware, error handling, and background tasks.

```python
import time
import logging
from fastapi import BackgroundTasks, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# ═══════════════════════════════════════
# Custom Middleware — runs on EVERY request
# ═══════════════════════════════════════
class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        request_id = str(uuid.uuid4())

        # Add request ID to state for logging
        request.state.request_id = request_id

        response = await call_next(request)

        duration = time.perf_counter() - start
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.4f}"

        logger.info(f"{request.method} {request.url.path} "
                    f"status={response.status_code} duration={duration:.4f}s")
        return response

app.add_middleware(RequestTimingMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://myapp.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════
# Global Exception Handlers
# ═══════════════════════════════════════
class AppException(Exception):
    def __init__(self, status_code: int, detail: str, error_code: str = None):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_code": exc.error_code,
            "request_id": getattr(request.state, "request_id", None),
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# ═══════════════════════════════════════
# Background Tasks — fire-and-forget
# ═══════════════════════════════════════
async def send_welcome_email(email: str, name: str):
    await email_service.send(
        to=email,
        subject="Welcome!",
        body=f"Hello {name}, welcome to our platform!"
    )

async def log_activity(user_id: int, action: str):
    await db.execute(
        "INSERT INTO activity_log (user_id, action) VALUES ($1, $2)",
        user_id, action
    )

@app.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    user = User(**user_data.model_dump())
    db.add(user); db.commit(); db.refresh(user)

    # These run AFTER the response is sent
    background_tasks.add_task(send_welcome_email, user.email, user.name)
    background_tasks.add_task(log_activity, user.id, "signup")

    return user
```

---

### Q5: WebSocket implementation in FastAPI.

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

class ConnectionManager:
    """Manages WebSocket connections for real-time features."""

    def __init__(self):
        # room_id → set of connections
        self.rooms: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        self.rooms.get(room_id, set()).discard(websocket)
        if room_id in self.rooms and not self.rooms[room_id]:
            del self.rooms[room_id]

    async def broadcast(self, room_id: str, message: dict, exclude=None):
        for ws in self.rooms.get(room_id, set()):
            if ws != exclude:
                try:
                    await ws.send_json(message)
                except Exception:
                    self.disconnect(ws, room_id)

manager = ConnectionManager()

@app.websocket("/ws/chat/{room_id}")
async def chat_websocket(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_json()
            # Broadcast message to all users in the room
            await manager.broadcast(room_id, {
                "user": data.get("user", "Anonymous"),
                "message": data["message"],
                "timestamp": time.time()
            }, exclude=None)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast(room_id, {"system": "A user left the chat"})
```

---

## 17.3 Advanced FastAPI

### Q6: How to structure a large FastAPI project?

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app creation, startup/shutdown
│   ├── config.py            # Settings (pydantic-settings)
│   ├── dependencies.py      # Shared dependencies (get_db, auth)
│   ├── middleware.py         # Custom middleware
│   ├── exceptions.py        # Custom exception classes
│   │
│   ├── api/                 # Route handlers (thin layer)
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py    # Combines all v1 routers
│   │   │   ├── users.py
│   │   │   ├── orders.py
│   │   │   └── products.py
│   │   └── v2/
│   │       └── ...
│   │
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── order.py
│   │
│   ├── schemas/             # Pydantic models (request/response)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── order.py
│   │
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   └── order_service.py
│   │
│   ├── repositories/        # Database access layer
│   │   ├── __init__.py
│   │   └── user_repo.py
│   │
│   └── core/                # Utilities
│       ├── database.py      # Engine, SessionLocal
│       ├── security.py      # JWT, hashing
│       └── logging.py
│
├── tests/
├── alembic/                 # Database migrations
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.router import api_router
from app.config import settings
from app.middleware import RequestTimingMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    await init_db()
    await init_redis()
    await preload_ml_model()
    print("Application started")
    yield
    # Shutdown
    await close_db()
    await close_redis()
    print("Application stopped")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(RequestTimingMiddleware)
app.include_router(api_router, prefix="/api/v1")


# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1 import users, orders, products

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])


# app/services/user_service.py — Business logic layer
class UserService:
    def __init__(self, db: Session, cache: Redis):
        self.db = db
        self.cache = cache

    async def create_user(self, data: UserCreate) -> User:
        existing = self.db.query(User).filter(User.email == data.email).first()
        if existing:
            raise AppException(409, "Email already registered", "DUPLICATE_EMAIL")

        user = User(**data.model_dump())
        user.password_hash = hash_password(data.password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # Invalidate cache
        await self.cache.delete(f"users:list")
        return user
```

---

### Scenario: "Design a Rate-Limited API with Authentication in FastAPI"

```python
import time
from collections import defaultdict
from fastapi import Request, HTTPException

# ═══════════════════════════════════════
# Rate Limiting Middleware
# ═══════════════════════════════════════
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.rpm = requests_per_minute
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()

        # Clean old entries
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if now - t < 60
        ]

        if len(self.requests[client_ip]) >= self.rpm:
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded", "retry_after": 60},
                headers={"Retry-After": "60"}
            )

        self.requests[client_ip].append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(
            self.rpm - len(self.requests[client_ip])
        )
        return response

# ═══════════════════════════════════════
# JWT Authentication
# ═══════════════════════════════════════
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=24))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(request: Request, db=Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).get(int(user_id))
    if not user:
        raise credentials_exception
    return user

@app.post("/auth/login")
async def login(email: str, password: str, db=Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
```

---

### Q7: How do you test FastAPI applications?

```python
from fastapi.testclient import TestClient
import pytest

# Synchronous testing
client = TestClient(app)

def test_create_user():
    response = client.post("/users", json={
        "name": "Alice",
        "email": "alice@test.com",
        "age": 30
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alice"
    assert "id" in data

def test_create_user_invalid_email():
    response = client.post("/users", json={
        "name": "Alice",
        "email": "not-an-email",
        "age": 30
    })
    assert response.status_code == 422   # Validation error

# Async testing with pytest-asyncio
import httpx

@pytest.mark.asyncio
async def test_async_endpoint():
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/users/1")
        assert response.status_code == 200

# Testing with dependency overrides
def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
```

---
