# Module 4 — FastAPI (with Pydantic 2)

> **Bible Module 4 of 14.** Self-contained. Written for **FastAPI 0.115+, Pydantic 2.x, Python 3.12+, SQLAlchemy 2.x async, Uvicorn 0.30+**. All code runnable as-is. Assumes Modules 1–3.

---

## 0. Goal, reader, and how to use this module

**Goal.** After this module you can: design and build production-grade HTTP APIs in FastAPI; structure a real codebase (not a single `main.py`); use Pydantic 2 for validation and serialization; integrate with the database layer from Module 3 via async sessions; implement OAuth2 with JWTs; test routes end-to-end; ship behind Uvicorn/Gunicorn in Docker; and reason about latency, concurrency, and observability well enough to debug production issues.

**Target reader.** Modules 1–3 done, or comfortable with Python, type hints, and SQL. No web-framework experience required.

**How to use it.** Same as before. Do all 36 problems before reading the solutions.

**Prerequisites.** Modules 1–3.
**Next steps.** Modules 7+ (ML, LLM, agents) — every model and agent eventually serves through a FastAPI surface in production. Module 13 (LLMOps) reuses these patterns.

---

## 1. FastAPI in the landscape

| Use case | Right tool |
|---|---|
| Modern HTTP/JSON APIs, async, type-safe | **FastAPI** |
| Server-rendered HTML, ORM-heavy CRUD admin sites | Django |
| Tiny synchronous service, full control | Flask |
| Maximum performance, type-first | Litestar (formerly Starlite) |
| Streaming + GraphQL gateway | Strawberry / Ariadne on FastAPI |
| Sub-millisecond, embedded | Rust (Axum / Actix) — call from Python via HTTP |

FastAPI sits on **Starlette** (HTTP/ASGI) + **Pydantic** (validation). It gives you:
- Type-driven request/response validation — your function signature *is* the schema.
- Automatic OpenAPI 3.1 docs at `/docs`.
- Async-native; sync routes work too.
- A first-class **dependency injection** system (covered in §5 — the most important feature).

**One-line summary.** "Flask if Flask had been invented in 2025, with type hints, async, and zero-config docs."

---

## 2. Hello world + project structure

### 2.1 Hello world

```python
# main.py
from fastapi import FastAPI

app = FastAPI(title="My API", version="1.0.0")

@app.get("/")
def root():
    return {"message": "hello"}
```

```bash
uv add fastapi uvicorn[standard]
uv run uvicorn main:app --reload
# open http://localhost:8000/docs  — Swagger UI auto-generated
# open http://localhost:8000/redoc — ReDoc UI also auto-generated
```

### 2.2 The structure you should use from day one

A single `main.py` is fine for hello world; nothing else. Use this layout:

```
my-api/
├── pyproject.toml
├── .env                          # never committed
├── alembic/                      # migrations (Module 3)
├── src/
│   └── my_api/
│       ├── __init__.py
│       ├── main.py               # FastAPI() instance + router includes
│       ├── config.py             # pydantic-settings — load env/secrets
│       ├── db.py                 # engine, session, get_session dependency
│       ├── deps.py               # cross-cutting dependencies
│       ├── security.py           # auth, JWT, hashing
│       ├── models/               # SQLAlchemy models
│       │   ├── __init__.py
│       │   ├── user.py
│       │   └── order.py
│       ├── schemas/              # Pydantic models (request/response)
│       │   ├── __init__.py
│       │   ├── user.py
│       │   └── order.py
│       ├── routers/              # one file per resource
│       │   ├── __init__.py
│       │   ├── users.py
│       │   └── orders.py
│       └── services/             # business logic — no FastAPI here
│           ├── __init__.py
│           └── billing.py
└── tests/
    ├── conftest.py
    ├── test_users.py
    └── test_orders.py
```

Two rules:

1. **`schemas/` are Pydantic, `models/` are SQLAlchemy.** Never let a SQLAlchemy model leak into a route response — they're tightly coupled to the DB session lifecycle and will mysteriously fail when accessed after the session closes.
2. **`services/` contains business logic.** Routers are *thin* — they parse input, call a service, return output. The service knows nothing about FastAPI; it can be tested with no HTTP at all.

### 2.3 Settings via pydantic-settings

```python
# src/my_api/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_")

    database_url: str
    jwt_secret:   str = Field(..., min_length=32)
    jwt_alg:      str = "HS256"
    debug:        bool = False
    cors_origins: list[str] = []

settings = Settings()    # reads from env + .env file; raises if required vars missing
```

```bash
# .env  (NEVER committed)
APP_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/myapp
APP_JWT_SECRET=use_a_real_secret_at_least_32_chars_long
APP_DEBUG=true
APP_CORS_ORIGINS=["http://localhost:3000"]
```

`pydantic-settings` validates types and required-ness at boot. The app **fails to start** if a critical secret is missing — that's the right failure mode.

---

## 3. Path, query, body — and Pydantic 2 models

### 3.1 The four ways data arrives in a request

```python
from fastapi import FastAPI, Path, Query, Header, Cookie, Body
from pydantic import BaseModel

app = FastAPI()

# Path parameter — part of the URL
@app.get("/users/{user_id}")
def get_user(user_id: int):                     # validated as int automatically
    return {"id": user_id}

# Query parameter — after the ?
@app.get("/users")
def list_users(
    limit: int = Query(20, ge=1, le=100),       # 1..100, default 20
    offset: int = 0,
    search: str | None = None,
):
    return {"limit": limit, "offset": offset, "search": search}

# Body — JSON in the request
class UserCreate(BaseModel):
    name: str
    email: str
    age: int | None = None

@app.post("/users")
def create_user(user: UserCreate):
    return {"created": user.model_dump()}

# Header / Cookie
@app.get("/me")
def me(x_request_id: str | None = Header(default=None)):
    return {"request_id": x_request_id}
```

The signature *is* the contract. Wrong types → 422 with structured errors; correct types are guaranteed inside the function.

### 3.2 Pydantic 2 — what you actually need

Pydantic 2 (released late 2023) is dramatically faster than v1 (validation in Rust) and has a cleaner API. Use v2 syntax everywhere.

```python
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name:    str           = Field(..., min_length=1, max_length=100)
    email:   EmailStr                                    # validates email format
    age:     int | None    = Field(None, ge=13, le=120)
    tags:    list[str]     = Field(default_factory=list, max_length=10)
    created: datetime      = Field(default_factory=datetime.utcnow)

    @field_validator("name")
    @classmethod
    def name_no_special_chars(cls, v: str) -> str:
        if not v.replace(" ", "").isalpha():
            raise ValueError("name must be letters and spaces only")
        return v
```

**Things to know:**
- `extra="forbid"` rejects unknown fields. Use it on input schemas to catch typos.
- `EmailStr`, `HttpUrl`, `IPvAnyAddress` etc. are built-in types — `pip install pydantic[email]` for `EmailStr`.
- Use `Field(..., ge=, le=, min_length=, max_length=, pattern=)` instead of writing validators when possible.
- `field_validator` for cross-field-free, single-field logic. `model_validator(mode="after")` for cross-field.
- `model_dump()` (was `.dict()`), `model_dump_json()` (was `.json()`), `model_validate()` (was `parse_obj()`).

### 3.3 Common Pydantic patterns

```python
# Allow string OR int for a field that accepts either
from typing import Union
class Mixed(BaseModel):
    value: Union[int, str]

# Discriminated unions for polymorphic input
from typing import Literal

class Cat(BaseModel):
    kind: Literal["cat"]
    purrs: bool

class Dog(BaseModel):
    kind: Literal["dog"]
    breed: str

class Animal(BaseModel):
    pet: Cat | Dog = Field(discriminator="kind")

# Aliases — accept JSON keys that don't match Python attribute names
from pydantic import AliasChoices
class User(BaseModel):
    user_id: int = Field(alias="userId", validation_alias=AliasChoices("userId","user_id"))
    model_config = ConfigDict(populate_by_name=True)
```

### 3.4 Validation errors — what the client sees

A request that fails validation returns 422 with a structured body:

```json
{"detail": [
  {
    "type": "string_too_short", "loc": ["body","name"],
    "msg": "String should have at least 1 character",
    "input": "", "ctx": {"min_length": 1}
  }
]}
```

This is the OpenAPI standard. Don't try to re-format it — frontends and clients expect this shape.

---

## 4. Response models, status codes, error handling

### 4.1 The most important pattern: input vs output schemas

**You almost always want different schemas for input and output.** A `User` from the DB has an `id`, `created_at`, and never a `password`. The input on `POST /users` has a `password` and no `id`. Don't share one schema.

```python
class UserCreate(BaseModel):                       # input
    email: EmailStr
    password: str = Field(min_length=8)
    name: str

class UserPublic(BaseModel):                       # output — what clients see
    id: int
    email: EmailStr
    name: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True) # allows building from ORM object

@app.post("/users", response_model=UserPublic, status_code=201)
def create_user(payload: UserCreate):
    user_db = save_to_db(payload)                  # SQLAlchemy User
    return user_db                                  # auto-coerced to UserPublic
```

**`response_model=` is more than docs.** FastAPI strips fields not in the response model. If you accidentally return a SQLAlchemy User, the `password_hash` column won't leak — `response_model` is a security boundary.

### 4.2 Status codes and `HTTPException`

```python
from fastapi import HTTPException, status

@app.get("/users/{uid}", response_model=UserPublic)
def get_user(uid: int):
    user = db.get(uid)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user not found")
    return user
```

**The status codes you need to know:**

| Code | Use |
|---|---|
| 200 | OK — successful GET / non-create POST |
| 201 | Created — successful resource-creating POST/PUT |
| 202 | Accepted — async work scheduled |
| 204 | No Content — successful DELETE / no-body PUT |
| 400 | Bad Request — caller error not covered by 422 |
| 401 | Unauthorized — missing/invalid auth |
| 403 | Forbidden — authenticated but not allowed |
| 404 | Not Found |
| 409 | Conflict — uniqueness/version violation |
| 422 | Unprocessable Entity — Pydantic validation failure |
| 429 | Too Many Requests — rate-limited |
| 500 | Internal Server Error — your bug |
| 502/503/504 | Bad gateway / unavailable / gateway timeout — downstream/infra |

**4xx is the client's fault. 5xx is yours.** Mixing them up is the most common API error.

### 4.3 Custom exception handlers

For app-wide error mapping, use a handler — not `try/except` in every route.

```python
from fastapi import Request
from fastapi.responses import JSONResponse

class NotFound(Exception):
    def __init__(self, what: str): self.what = what

@app.exception_handler(NotFound)
async def not_found_handler(request: Request, exc: NotFound):
    return JSONResponse(status_code=404, content={"detail": f"{exc.what} not found"})
```

Now any route that `raise NotFound("user")` returns `{"detail": "user not found"}` with 404. Centralizes error mapping; routes stay clean.

### 4.4 Pagination response shape

There are two common patterns. Pick one and use it consistently.

**Cursor (recommended for anything that grows).**
```python
class UserPage(BaseModel):
    items: list[UserPublic]
    next_cursor: str | None
```

**Offset/limit (only for small datasets).**
```python
class UserPage(BaseModel):
    items: list[UserPublic]
    total: int
    limit: int
    offset: int
```

Avoid mixing them across endpoints. Inconsistency is its own bug.

---

## 5. Dependency injection — FastAPI's killer feature

A "dependency" is a callable whose return value is injected into your route. It runs *before* the route, can raise to short-circuit, and can yield with cleanup. It's the cleanest pattern for: DB sessions, current user resolution, settings access, cross-cutting concerns.

### 5.1 The basics

```python
from fastapi import Depends

def common_params(q: str | None = None, limit: int = 10):
    return {"q": q, "limit": limit}

@app.get("/items")
def list_items(params = Depends(common_params)):
    return params
```

A dependency *is* a function with the same parameter conventions as a route. Reusable across routes; FastAPI caches it within a request (so calling it 5 times in one request runs once by default).

### 5.2 The DB session pattern (the one you'll use everywhere)

```python
# src/my_api/db.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator
from .config import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session                              # route runs here
        # session.close() implied by async-with
```

```python
# src/my_api/routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_session
from ..models.user import User
from ..schemas.user import UserPublic

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{uid}", response_model=UserPublic)
async def get_user(uid: int, session: AsyncSession = Depends(get_session)):
    user = await session.get(User, uid)
    if not user: raise HTTPException(404)
    return user
```

The dependency yields a session per request, automatically closed. Sessions are NOT shared across requests — that would corrupt them.

### 5.3 Sub-dependencies

Dependencies can depend on other dependencies. FastAPI builds the graph and runs them in order.

```python
from fastapi import Header, HTTPException

def require_api_key(x_api_key: str = Header()):
    if not is_valid_key(x_api_key):
        raise HTTPException(401, "invalid api key")
    return x_api_key

def get_current_user(api_key: str = Depends(require_api_key),
                     session: AsyncSession = Depends(get_session)):
    return resolve_user_from_key(api_key, session)
```

Every route that injects `get_current_user` gets API key validation + user resolution for free. No duplication.

### 5.4 Yield dependencies (cleanup)

Use `yield` for resources that need cleanup:

```python
async def get_session():
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()
```

This pattern auto-commits on success, auto-rolls-back on exception. Routes don't need transaction management at all.

### 5.5 Dependency overrides — for testing

```python
def fake_user():
    return User(id=1, email="test@x", name="Test")

app.dependency_overrides[get_current_user] = fake_user
# all routes that depend on get_current_user now get the fake
```

This is how you test auth-protected routes without real auth in tests. Reset with `app.dependency_overrides.clear()`.

### 5.6 Class-based dependencies

For dependencies with a lot of state or wiring, use a class:

```python
class Pagination:
    def __init__(self, limit: int = 20, offset: int = 0):
        if limit > 100: limit = 100
        self.limit, self.offset = limit, offset

@app.get("/orders")
def list_orders(p: Pagination = Depends()):       # FastAPI uses Pagination's __init__ signature
    return {"limit": p.limit, "offset": p.offset}
```

Equivalent to `Depends(Pagination)`; the bare `Depends()` works because the type hint provides the callable.

---

## 6. Async vs sync routes — picking right

This decision matters more than developers think. Get it wrong and your latency multiplies by 10x.

### 6.1 The rules

- **Define a route `async def`** if it does I/O — DB calls, HTTP calls, file I/O.
- **Define it `def`** (sync) if it's pure CPU work or a tight loop.
- Inside an `async def`, **never call a blocking function**. That includes `requests.get`, sync `psycopg2`, `time.sleep`, etc. They block the entire event loop.

### 6.2 What FastAPI does behind the scenes

- `async def` route -> runs directly on the event loop. One worker can handle thousands of in-flight requests because they `await` on I/O.
- `def` (sync) route -> FastAPI runs it in a **threadpool** (default size 40). The event loop is not blocked, but you're limited by thread count.

### 6.3 The mistake everyone makes once

```python
import requests

@app.get("/external")          # WARNING: async route + blocking call = disaster
async def external():
    r = requests.get("https://example.com")    # blocks the event loop
    return {"status": r.status_code}
```

Under load, this freezes other handlers. Fix:

```python
import httpx

@app.get("/external")
async def external():
    async with httpx.AsyncClient() as client:
        r = await client.get("https://example.com")
    return {"status": r.status_code}
```

Or — if you must call a sync function — push it to a thread:

```python
import asyncio
async def external():
    r = await asyncio.to_thread(requests.get, "https://example.com")
    return {"status": r.status_code}
```

### 6.4 The "shared httpx client" pattern

Don't create a new `httpx.AsyncClient` per request — that re-establishes connection pools. Share one for the app's lifetime:

```python
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Request

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=10)
    yield
    await app.state.http.aclose()

app = FastAPI(lifespan=lifespan)

@app.get("/external")
async def external(request: Request):
    r = await request.app.state.http.get("https://example.com")
    return {"status": r.status_code}
```

`lifespan` is the modern replacement for `startup`/`shutdown` events.

---

## 7. Authentication & authorization

Two distinct concerns:
- **Authentication** — who are you?
- **Authorization** — what are you allowed to do?

### 7.1 Password hashing — the absolute floor

```python
from passlib.context import CryptContext

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plaintext: str) -> str:
    return pwd.hash(plaintext)

def verify_password(plaintext: str, hashed: str) -> bool:
    return pwd.verify(plaintext, hashed)
```

**Rules:**
- Never store plaintext. Never use MD5 or SHA-256 directly — they're not slow enough.
- bcrypt or argon2id only. Both are deliberately slow + salt-included.
- Hash format already contains the salt and cost — store the whole hash string.
- **Version-pin warning.** `passlib==1.7.4` is the latest release and predates `bcrypt>=4.1`; the combination prints harmless warnings and (rarely) errors during self-test. Pin `bcrypt<4.1` with passlib, or migrate to `argon2-cffi` directly, or use `bcrypt` directly without passlib.

### 7.2 OAuth2 password flow + JWT — the standard

This is the canonical FastAPI auth example. Memorize it.

```python
# security.py
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .config import settings
from .db import get_session
from .models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(sub: str, extra: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": sub, "iat": now, "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)}
    if extra: payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "invalid token")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    payload = decode_token(token)
    user = await session.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(401, "user not found")
    return user

# the auth router
auth = APIRouter(prefix="/auth", tags=["auth"])

@auth.post("/token")
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    user = await session.scalar(select(User).where(User.email == form.username))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "incorrect username or password")
    return {"access_token": create_access_token(str(user.id)), "token_type": "bearer"}
```

```python
# protected route
@app.get("/me", response_model=UserPublic)
async def me(user: Annotated[User, Depends(get_current_user)]):
    return user
```

### 7.3 Refresh tokens

Access tokens are short-lived (15-30 min). Refresh tokens are long-lived (days/weeks) and used to obtain new access tokens. Store **only refresh tokens** (or their hash) in the DB; revoke them on logout/breach.

### 7.4 Authorization (RBAC) — keep it simple

```python
def require_role(role: str):
    def dep(user: User = Depends(get_current_user)):
        if role not in user.roles:
            raise HTTPException(403, "forbidden")
        return user
    return dep

@app.delete("/posts/{post_id}", status_code=204)
async def delete_post(post_id: int, _: User = Depends(require_role("admin"))):
    ...
```

The dependency factory pattern (`require_role(role)` returns a dep) is the cleanest way to parametrize.

For complex permissions (per-resource), pass the resource ID into a dependency that loads the resource and checks ownership.

### 7.5 What NOT to do

- **Don't put secrets in JWTs.** Anyone with the token can decode the payload. JWTs are signed, not encrypted.
- **Don't roll your own crypto.** Use the libraries.
- **Don't validate JWTs without checking `alg`.** The "alg=none" attack is real. Always pass `algorithms=[...]` explicitly.
- **Don't skip `exp` validation.** Always include and check expiration.
- **Don't store JWTs in `localStorage`** if XSS is a risk — use HttpOnly cookies.


---

## 8. Middleware, CORS, and request context

### 8.1 Middleware basics

Middleware wraps every request — a single function that runs before and after the route. Use sparingly; per-request work adds up.

```python
import time, uuid
from fastapi import FastAPI, Request

app = FastAPI()

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id           # available in routes via request.state
    start = time.perf_counter()
    response = await call_next(request)             # runs the route
    elapsed = time.perf_counter() - start
    response.headers["x-request-id"] = request_id
    response.headers["x-elapsed-ms"] = f"{elapsed*1000:.1f}"
    return response
```

The `request.state.x` slot is your per-request scratchpad. Don't put heavy objects there.

### 8.2 CORS

If a browser frontend on a different origin will call your API, you need CORS — otherwise the browser blocks responses.

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,            # explicit list, never "*" in prod with creds
    allow_credentials=True,
    allow_methods=["GET","POST","PUT","DELETE","PATCH"],
    allow_headers=["*"],
    expose_headers=["x-request-id"],
)
```

**Watch out:** `allow_origins=["*"]` + `allow_credentials=True` is invalid per the spec; browsers will reject. Use explicit origins.

### 8.3 Built-in middlewares worth knowing

- `GZipMiddleware` — compresses responses > 1 KB.
- `TrustedHostMiddleware` — rejects requests with unknown `Host` header (anti-Host-header injection).
- `HTTPSRedirectMiddleware` — only behind a real proxy that sets `X-Forwarded-Proto`.

```python
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1024)
```

---

## 9. Background tasks, queues, and scheduled work

### 9.1 `BackgroundTasks` — for fire-and-forget after a response

```python
from fastapi import BackgroundTasks

def send_welcome_email(email: str):
    # this runs AFTER the response is sent
    smtp_send(email, "Welcome!")

@app.post("/users", status_code=201)
async def create_user(payload: UserCreate, bg: BackgroundTasks):
    user = save(payload)
    bg.add_task(send_welcome_email, user.email)
    return user
```

`BackgroundTasks` runs in the same process. Use it only for fast, fire-and-forget side effects: emails, audit log writes, cache warming. Anything that can fail and matters → use a real queue.

### 9.2 The grown-up version — Celery / RQ / Dramatiq

For retries, scheduling, fan-out, or any task that must not be lost on a worker crash:

```python
# tasks.py — using Celery
from celery import Celery

celery = Celery("myapp", broker="redis://localhost:6379/0")

@celery.task(bind=True, max_retries=3, default_retry_delay=10)
def send_welcome_email(self, email: str):
    try:
        smtp_send(email, "Welcome!")
    except Exception as exc:
        raise self.retry(exc=exc)
```

```python
# in your route
from .tasks import send_welcome_email

@app.post("/users")
async def create_user(payload: UserCreate):
    user = save(payload)
    send_welcome_email.delay(user.email)            # enqueues; returns immediately
    return user
```

**When to pick:**
- **Celery:** mature, broad ecosystem, complex but proven. Default for big apps.
- **RQ:** Redis-only, simpler, smaller surface. Good for medium projects.
- **Dramatiq:** modern, minimal, opinionated. Increasingly popular.

For periodic schedules (cron-like): **Celery Beat**, **APScheduler**, or **Temporal** for serious workflow durability.

### 9.3 The async-task-from-async-route gotcha

Spawning `asyncio.create_task(...)` inside a route works but the task is unmanaged — if the process restarts, it's lost. Background tasks for important work belong in a queue, not in-process.

---

## 10. WebSockets and Server-Sent Events

For realtime: **WebSockets** (bidirectional) or **SSE** (server -> client only). For LLM streaming responses, SSE is usually plenty.

### 10.1 WebSocket basics

```python
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/chat/{room}")
async def chat(ws: WebSocket, room: str):
    await ws.accept()
    try:
        while True:
            msg = await ws.receive_text()
            await ws.send_text(f"[{room}] {msg}")
    except WebSocketDisconnect:
        # cleanup
        pass
```

For multi-user broadcast, store connections per room and fan-out:

```python
class RoomManager:
    def __init__(self):
        self.rooms: dict[str, set[WebSocket]] = {}
    async def join(self, room, ws):
        self.rooms.setdefault(room, set()).add(ws)
    async def leave(self, room, ws):
        self.rooms.get(room, set()).discard(ws)
    async def broadcast(self, room, msg):
        for ws in list(self.rooms.get(room, [])):
            try: await ws.send_text(msg)
            except: self.rooms[room].discard(ws)
```

For multi-process/multi-server fanout, route messages through Redis pub/sub or a real message bus. WebSocket connections are sticky to one process.

### 10.2 SSE — the right tool for LLM streaming

```python
from sse_starlette.sse import EventSourceResponse
import asyncio

async def token_stream():
    for token in ["Hello", " ", "world", "!"]:
        await asyncio.sleep(0.1)
        yield {"event": "message", "data": token}

@app.get("/chat/stream")
async def chat_stream():
    return EventSourceResponse(token_stream())
```

The browser receives `text/event-stream` and processes events as they arrive. Most LLM streaming UIs use this pattern (Module 10/13 will reuse this).

---

## 11. Testing FastAPI apps

### 11.1 The TestClient pattern

```python
# tests/test_users.py
from fastapi.testclient import TestClient
from my_api.main import app

client = TestClient(app)

def test_create_user():
    r = client.post("/users", json={"email":"a@x.com","password":"longenough","name":"Ada"})
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "a@x.com"
    assert "password" not in body                   # response_model strips it

def test_get_user_404():
    r = client.get("/users/99999")
    assert r.status_code == 404
```

The `TestClient` is a synchronous wrapper over httpx that drives the ASGI app in-process — no real server needed. It supports async routes transparently.

### 11.2 Async tests with httpx

For genuinely async test code (e.g. concurrent requests):

```python
import pytest, httpx
from httpx import ASGITransport

@pytest.mark.asyncio
async def test_concurrent():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        responses = await asyncio.gather(*[ac.get(f"/users/{i}") for i in range(1, 11)])
    assert all(r.status_code == 200 for r in responses)
```

### 11.3 Overriding dependencies

This is the *the* technique for fast, reliable tests.

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from my_api.main import app
from my_api.deps import get_current_user
from my_api.models import User

def fake_user():
    return User(id=1, email="test@x", name="Tester", roles=["admin"])

@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = fake_user
    yield TestClient(app)
    app.dependency_overrides.clear()
```

Auth-protected routes now run with `fake_user` injected — no real JWT issuance needed in tests.

### 11.4 The DB-in-tests pattern

Two viable approaches:

**(a) SQLite in-memory per test.** Fast, no setup. Behavior differs from your prod DB in subtle ways (no real concurrency, lax SQL).

**(b) Real DB via testcontainers.** Slower start-up, but identical to production. Strongly recommended for any non-trivial app.

```python
# pytest-postgresql + transactional test pattern
@pytest.fixture
async def session(test_engine):
    async with test_engine.connect() as conn:
        trans = await conn.begin()
        async with AsyncSession(bind=conn) as s:
            yield s
        await trans.rollback()                      # everything in this test is rolled back
```

---

## 12. Database integration patterns

(Module 3 covered DBs in depth. Here are the FastAPI-specific shapes.)

### 12.1 Repository pattern — keeping the DB at arm's length

Routers shouldn't write SQL. Wrap DB access in a class:

```python
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def by_id(self, id: int) -> User | None:
        return await self.session.get(User, id)

    async def by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).where(User.email == email))

    async def create(self, data: UserCreate) -> User:
        u = User(email=data.email, name=data.name, password_hash=hash_password(data.password))
        self.session.add(u)
        await self.session.flush()                  # generates ID without committing
        return u

# Dependency
async def get_user_repo(s: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(s)

# Route
@router.get("/{uid}", response_model=UserPublic)
async def get_user(uid: int, repo: UserRepository = Depends(get_user_repo)):
    user = await repo.by_id(uid)
    if not user: raise HTTPException(404)
    return user
```

Now your route is ~3 lines. Repository is unit-testable without HTTP. Service-layer methods sit on top, composing repositories.

### 12.2 Pagination dependency

```python
from typing import Annotated

class CursorPage:
    def __init__(self, after: int | None = None, limit: int = Query(20, ge=1, le=100)):
        self.after = after; self.limit = limit

@router.get("", response_model=UserPage)
async def list_users(p: Annotated[CursorPage, Depends()],
                     repo: UserRepository = Depends(get_user_repo)):
    users = await repo.page_after(p.after, p.limit)
    next_cursor = users[-1].id if len(users) == p.limit else None
    return {"items": users, "next_cursor": next_cursor}
```

### 12.3 Idempotency keys

For unsafe operations (create, charge), accept an `Idempotency-Key` header. Store responses by key for 24h:

```python
async def idempotent(request: Request, key: str | None = Header(None, alias="Idempotency-Key")):
    if not key: return None
    cached = await redis.get(f"idem:{key}")
    if cached: return json.loads(cached)
    return None    # caller proceeds normally; you cache the response after
```

Used by every payment API on earth (Stripe pioneered the pattern).

---

## 13. File uploads, downloads, and static files

### 13.1 Uploads

```python
from fastapi import UploadFile, File

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if file.content_type not in {"image/png", "image/jpeg"}:
        raise HTTPException(415, "unsupported type")
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(413, "too large")
    # stream to disk to avoid loading the whole file in RAM
    with open(f"/tmp/{file.filename}", "wb") as out:
        while chunk := await file.read(1024 * 1024):
            out.write(chunk)
    return {"filename": file.filename}
```

For real-world apps, **don't store uploads on the local filesystem.** Stream to S3 / GCS / Azure Blob directly. Use presigned URLs so clients upload directly to the bucket and your API never touches the bytes.

### 13.2 Downloads

```python
from fastapi.responses import FileResponse, StreamingResponse

@app.get("/files/{name}")
def download(name: str):
    return FileResponse(f"/tmp/{name}", filename=name)

@app.get("/report.csv")
async def report_csv():
    async def gen():
        yield "id,name\n"
        async for row in stream_rows():
            yield f"{row.id},{row.name}\n"
    return StreamingResponse(gen(), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=report.csv"})
```

`StreamingResponse` is essential for any large or streaming response: CSV exports, ML predictions over large inputs, SSE.

---

## 14. API design — versioning, errors, conventions

### 14.1 Versioning strategy — pick one and stick to it

Three common approaches:

1. **URL prefix:** `/v1/users`, `/v2/users`. Most common, easiest to route.
2. **Header:** `X-API-Version: 2`. Cleaner URLs but harder to test from a browser.
3. **Media type:** `Accept: application/vnd.myapi.v2+json`. Most "RESTful," least practical.

Pick (1) unless you have a strong reason. In FastAPI:

```python
v1 = APIRouter(prefix="/v1")
v2 = APIRouter(prefix="/v2")
v1.include_router(users_router)        # legacy schema
v2.include_router(users_v2_router)     # current
app.include_router(v1)
app.include_router(v2)
```

### 14.2 Error response shape

Adopt a single error envelope for 4xx/5xx:

```json
{"detail": "human readable", "code": "USER_NOT_FOUND", "request_id": "..."}
```

Always include `request_id` so users can quote it back to support and you find the trace immediately.

### 14.3 Resource conventions

- **Nouns, plural, lowercase.** `/users`, `/orders/{id}`.
- **GET reads, POST creates, PUT replaces, PATCH partial-updates, DELETE.**
- **Return 201 + Location header** for create.
- **Return 204** for delete (no body).
- **HEAD** = same as GET but no body — useful for existence checks.

---

## 15. Observability — logs, traces, metrics

### 15.1 Structured logging — set up correctly

```python
import logging, sys, structlog

def configure_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")

configure_logging()
log = structlog.get_logger()

@app.middleware("http")
async def log_middleware(request: Request, call_next):
    rid = request.headers.get("x-request-id", str(uuid.uuid4()))
    structlog.contextvars.bind_contextvars(request_id=rid, path=request.url.path)
    log.info("request_start")
    try:
        response = await call_next(request)
    except Exception:
        log.exception("request_error")
        raise
    log.info("request_end", status=response.status_code)
    structlog.contextvars.clear_contextvars()
    return response
```

Every log line is JSON with `request_id`, `path`, `status` — making distributed search trivial in any log aggregator.

### 15.2 OpenTelemetry — distributed tracing

```bash
uv add opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-exporter-otlp
```

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
FastAPIInstrumentor.instrument_app(app)
```

This auto-instruments every route. Add `SQLAlchemyInstrumentor`, `HTTPXInstrumentor`, `RedisInstrumentor` for end-to-end traces from incoming request to DB query and back.

### 15.3 Prometheus metrics

```python
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

REQUEST_COUNT = Counter("requests_total", "All requests", ["method","route","status"])
REQUEST_LATENCY = Histogram("request_seconds", "Latency", ["route"])

@app.middleware("http")
async def metrics_middleware(request, call_next):
    route = request.url.path
    with REQUEST_LATENCY.labels(route).time():
        response = await call_next(request)
    REQUEST_COUNT.labels(request.method, route, response.status_code).inc()
    return response

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

For high-cardinality endpoints, normalize routes (`/users/{id}` not `/users/123`) — otherwise Prometheus chokes.

---

## 16. Deployment — Uvicorn, Gunicorn, Docker

### 16.1 Process model

- **Uvicorn** is an ASGI server. Single process by default.
- **Gunicorn** is a process manager. Runs multiple worker processes.
- The standard production command runs Gunicorn with Uvicorn workers:

```bash
gunicorn my_api.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 --timeout 30
```

`-w 4` = 4 worker processes. Sized to `(2 * CPU_cores) + 1` per Gunicorn's docs, but with async I/O-bound workloads, fewer workers (matching CPU cores) is usually right.

### 16.2 The minimal production Dockerfile

```dockerfile
FROM python:3.12-slim

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ ./src/
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["gunicorn", "my_api.main:app",
     "-k", "uvicorn.workers.UvicornWorker",
     "-w", "4", "-b", "0.0.0.0:8000",
     "--timeout", "30",
     "--access-logfile", "-"]
```

Multi-stage builds, slim base image, frozen lockfile, no dev deps in prod, logs to stdout. Boring is good.

### 16.3 Health checks and graceful shutdown

```python
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/ready")
async def ready(session: AsyncSession = Depends(get_session)):
    await session.execute(text("SELECT 1"))         # check DB
    return {"status": "ready"}
```

- **Liveness (`/health`)** — "the process is alive, don't restart me." Cheap; no dependencies.
- **Readiness (`/ready`)** — "I can serve traffic." Checks DB, cache, etc.

Kubernetes uses both. Don't combine them — failing readiness drains traffic; failing liveness restarts.

For graceful shutdown, the `lifespan` context manager handles cleanup. Set Gunicorn `--graceful-timeout 30` to allow in-flight requests to finish.

---

## 17. Anti-patterns

| Anti-pattern | Right way |
|---|---|
| Single `main.py` for the whole app | Routers per resource; thin routes; services for logic |
| One Pydantic schema for input + output | Separate `Create`, `Update`, `Public` |
| Returning SQLAlchemy models directly | Use `response_model=` (or DTOs) |
| `requests.get(...)` in an async route | `httpx.AsyncClient`, shared via `lifespan` |
| New httpx client per request | One client, shared via `app.state` |
| `time.sleep(...)` in async | `await asyncio.sleep(...)` |
| Blocking DB driver in async route | `aiomysql`/`asyncpg` + async SA |
| Long task in `BackgroundTasks` | Real queue (Celery/RQ/Dramatiq) |
| `Exception` -> 200 with `{"error": ...}` | Use proper status codes (4xx/5xx) |
| `allow_origins=["*"]` with credentials | Explicit origins |
| Catching `Exception` and swallowing | Catch specific; let others bubble to handler |
| JWT secret in code | Env var via `pydantic-settings` |
| MD5/SHA-256 for passwords | bcrypt or argon2id |
| Storing sessions in-process | Redis (multi-server safe) |
| `OFFSET` pagination in big tables | Cursor-based |
| Logging unstructured text | Structured JSON via structlog |
| One worker, one process | Gunicorn with N workers |
| Putting auth logic in every route | Dependency injection |

---

## 18. Thirty-six problems (with full structure)

Each problem follows: **Statement → Intuition → Brute force → Optimized → Complexity → Edge cases → Real-world → Follow-ups.**
**Section breakdown:** 8 Routes & validation (P1–P8), 5 Dependency injection (P9–P13), 5 Auth (P14–P18), 5 DB integration (P19–P23), 4 Streaming/WS (P24–P27), 4 Testing (P28–P31), 5 Production/perf (P32–P36).

---

### Problem 1 — A typed CRUD route for products

**Statement.** Build POST/GET/PUT/DELETE `/products` with input schema, public output schema, and proper status codes.

**Solution.**
```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict

class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name:  str   = Field(..., min_length=1, max_length=200)
    price: int   = Field(..., ge=0)                 # cents — never float for money
    sku:   str   = Field(..., pattern=r"^[A-Z0-9-]{3,20}$")

class ProductPublic(BaseModel):
    id: int; name: str; price: int; sku: str
    model_config = ConfigDict(from_attributes=True)

app = FastAPI()
DB: dict[int, dict] = {}                            # toy in-memory store
_next = 1

@app.post("/products", response_model=ProductPublic, status_code=201)
def create_product(p: ProductCreate):
    global _next
    obj = {"id": _next, **p.model_dump()}
    DB[_next] = obj; _next += 1
    return obj

@app.get("/products/{pid}", response_model=ProductPublic)
def get_product(pid: int):
    if pid not in DB: raise HTTPException(404, "product not found")
    return DB[pid]

@app.put("/products/{pid}", response_model=ProductPublic)
def replace_product(pid: int, p: ProductCreate):
    if pid not in DB: raise HTTPException(404)
    DB[pid] = {"id": pid, **p.model_dump()}
    return DB[pid]

@app.delete("/products/{pid}", status_code=204)
def delete_product(pid: int):
    DB.pop(pid, None)
```

**Real-world.** This is the spine of every CRUD service. The split between `Create` (no `id`) and `Public` (with `id`) is non-negotiable.

**Follow-ups.** PATCH for partial update (`exclude_unset=True` on the schema). Idempotency-Key on POST.

---

### Problem 2 — Query parameter validation with Annotated

**Statement.** A `/search` endpoint takes `q` (1–100 chars), `page` (≥1), `size` (1–50), `sort` from a fixed set.

**Solution.**
```python
from typing import Annotated, Literal
from fastapi import Query

@app.get("/search")
def search(
    q:    Annotated[str, Query(min_length=1, max_length=100)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=50)] = 20,
    sort: Annotated[Literal["price","-price","name","-name"], Query()] = "name",
):
    return {"q": q, "page": page, "size": size, "sort": sort}
```

**Why `Annotated`.** Modern style separates the type from the validation metadata cleanly, plays well with `mypy`, and is what FastAPI's docs recommend.

**Follow-ups.** Multi-valued query params (`tags=a&tags=b`) with `list[str]`. Date ranges with `start: date | None = None`.

---

### Problem 3 — Field validators with cross-field rules

**Statement.** A `BookingCreate` schema requires `end > start` and `passengers <= max_capacity_for_route(route_id)`.

**Solution.**
```python
from datetime import datetime
from pydantic import BaseModel, model_validator

class BookingCreate(BaseModel):
    route_id:   int
    start:      datetime
    end:        datetime
    passengers: int

    @model_validator(mode="after")
    def check_times(self):
        if self.end <= self.start:
            raise ValueError("end must be after start")
        if (self.end - self.start).total_seconds() > 24*3600:
            raise ValueError("booking cannot exceed 24h")
        return self
```

**Why `model_validator`** (and not `field_validator`)? Cross-field checks need the full model.

**Follow-ups.** Lookups against the DB belong in the *route*, not the schema — Pydantic models should be DB-agnostic.

---

### Problem 4 — Custom OpenAPI schema enrichments

**Statement.** Add description, examples, and tags so the auto-docs are usable.

**Solution.**
```python
from pydantic import BaseModel, Field, ConfigDict

class UserCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"email": "ada@x.com", "password": "longenough", "name": "Ada"}]
    })
    email: str = Field(..., description="User's primary email")
    password: str = Field(..., min_length=8, description="At least 8 chars")
    name: str

@app.post("/users", tags=["users"], summary="Register a new user",
          description="Creates a user account and triggers a welcome email.")
def create_user(u: UserCreate): ...
```

**Real-world.** Frontend devs and SDK generators read this. Treat docs like an API artifact.

**Follow-ups.** Multiple examples per endpoint (named). Operation IDs (`operation_id="users:create"`) for consistent SDK method names.

---

### Problem 5 — Conditional 304 Not Modified with ETag

**Statement.** Cache-friendly GET. Compute an ETag from the resource version; return 304 if `If-None-Match` matches.

**Solution.**
```python
import hashlib
from fastapi import Header, Response

@app.get("/products/{pid}")
def get_product(pid: int, response: Response,
                if_none_match: str | None = Header(default=None)):
    p = DB.get(pid)
    if not p: raise HTTPException(404)
    etag = hashlib.md5(repr(p).encode()).hexdigest()
    if if_none_match == etag:
        return Response(status_code=304)
    response.headers["etag"] = etag
    response.headers["cache-control"] = "private, max-age=60"
    return p
```

**Real-world.** Saves bandwidth. CDNs and browsers honor it. The DB-derived version (e.g. `updated_at`) is a better ETag than hashing the whole body.

**Follow-ups.** `Last-Modified` + `If-Modified-Since` (older but still relevant). Strong vs weak ETags.

---

### Problem 6 — File download (streaming, large)

**Statement.** Stream a CSV report row-by-row from the DB; never materialize the whole file in RAM.

**Solution.**
```python
from fastapi.responses import StreamingResponse

@app.get("/orders/export.csv")
async def export_orders(session: AsyncSession = Depends(get_session)):
    async def gen():
        yield "id,user_id,amount\n"
        result = await session.stream(select(Order).order_by(Order.id))
        async for row in result.scalars():
            yield f"{row.id},{row.user_id},{row.amount}\n"
    return StreamingResponse(
        gen(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="orders.csv"'},
    )
```

**Real-world.** Reports, log exports, ML predictions on bulk inputs. Without streaming, big exports OOM the worker.

**Follow-ups.** Compress on the fly (`gzip`). Resume support via `Range` header.

---

### Problem 7 — Custom exception handler with structured detail

**Solution.**
```python
class DomainError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code, self.message, self.status = code, message, status

@app.exception_handler(DomainError)
async def handle_domain(request: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status, content={
        "code": exc.code, "detail": exc.message,
        "request_id": getattr(request.state, "request_id", None),
    })

@app.post("/transfer")
async def transfer():
    raise DomainError("INSUFFICIENT_FUNDS", "balance too low", status=409)
```

**Real-world.** A consistent error envelope is one of the highest-leverage decisions in API design. SDKs can switch on `code` reliably.

**Follow-ups.** Error catalog endpoint (`GET /errors`) for clients to introspect codes and messages.

---

### Problem 8 — Body too large / content-type validation

**Statement.** Reject requests > 1 MB; reject non-JSON bodies on `POST /events`.

**Solution.**
```python
from fastapi import Request, HTTPException

MAX_BODY_BYTES = 1 * 1024 * 1024

@app.middleware("http")
async def body_size_limit(request: Request, call_next):
    cl = request.headers.get("content-length")
    if cl and int(cl) > MAX_BODY_BYTES:
        return JSONResponse(status_code=413, content={"detail": "payload too large"})
    return await call_next(request)

@app.post("/events")
async def post_event(request: Request):
    if request.headers.get("content-type", "").split(";")[0].strip() != "application/json":
        raise HTTPException(415, "expected application/json")
    payload = await request.json()
    return {"received": payload}
```

**Real-world.** Bots and confused clients send all kinds of garbage. Size and type checks are the floor.

**Follow-ups.** Per-route limits. Streaming uploads with chunked verification.

---

### Problem 9 — Pagination as a class-based dependency

**Solution.**
```python
from fastapi import Query
from typing import Annotated

class CursorPage:
    def __init__(self,
                 after_id: Annotated[int | None, Query()] = None,
                 limit:    Annotated[int, Query(ge=1, le=100)] = 20):
        self.after_id = after_id
        self.limit = limit

@app.get("/orders")
async def list_orders(p: Annotated[CursorPage, Depends()],
                      session: AsyncSession = Depends(get_session)):
    stmt = select(Order).order_by(Order.id).limit(p.limit)
    if p.after_id is not None:
        stmt = stmt.where(Order.id > p.after_id)
    rows = (await session.scalars(stmt)).all()
    next_cursor = rows[-1].id if len(rows) == p.limit else None
    return {"items": rows, "next_cursor": next_cursor}
```

**Real-world.** Same `CursorPage` reused across every list endpoint — uniform pagination across your API for free.

**Follow-ups.** Encode `next_cursor` as opaque base64. Compound cursors for multi-key sort.

---

### Problem 10 — Per-request rate limiting via dependency

**Solution.**
```python
import time, redis.asyncio as aioredis
from fastapi import HTTPException, Depends, Request

redis_client = aioredis.from_url("redis://localhost", decode_responses=True)

async def rate_limit(request: Request, limit: int = 100, window: int = 60):
    ip = request.client.host
    bucket = f"rl:{ip}:{int(time.time()) // window}"
    n = await redis_client.incr(bucket)
    if n == 1: await redis_client.expire(bucket, window)
    if n > limit:
        raise HTTPException(429, "too many requests",
                            headers={"Retry-After": str(window)})

@app.get("/expensive", dependencies=[Depends(rate_limit)])
async def expensive():
    return {"ok": True}
```

**Real-world.** Per-IP and per-user limits in front of expensive endpoints. For real production, use `slowapi` or move limiting to the API gateway / load balancer.

**Follow-ups.** Sliding-window log via sorted sets (Module 3 P31). Different limits per user tier.

---

### Problem 11 — Caching dependency with TTL

**Solution.**
```python
import json, hashlib

def cached(ttl: int = 60):
    async def dep(request: Request):
        if request.method != "GET": return None
        key = f"cache:{hashlib.sha256(str(request.url).encode()).hexdigest()}"
        cached = await redis_client.get(key)
        if cached:
            request.state.cache_hit = True
            return json.loads(cached)
        return None
    return dep

@app.get("/products")
async def list_products(_cache = Depends(cached(60)), session: AsyncSession = Depends(get_session)):
    if _cache is not None: return _cache
    items = (await session.scalars(select(Product))).all()
    payload = [{"id": p.id, "name": p.name, "price": p.price} for p in items]
    await redis_client.setex(f"cache:{...}", 60, json.dumps(payload))   # write-back
    return payload
```

A nicer middleware-based version centralizes write-back; the dependency is fine for a few hot endpoints.

**Real-world.** Most read-heavy endpoints want this. Cache invalidation belongs to writes — bump a version stamp on writes, include it in the cache key.

**Follow-ups.** Stampede protection (Module 3 P30). ETag-aware cache.

---

### Problem 12 — Settings as a typed dependency

**Solution.**
```python
from functools import lru_cache
from .config import Settings

@lru_cache
def get_settings() -> Settings:
    return Settings()

@app.get("/config-test")
def test(settings: Settings = Depends(get_settings)):
    return {"debug": settings.debug}
```

`@lru_cache` makes it a singleton. Tests can override:

```python
app.dependency_overrides[get_settings] = lambda: Settings(database_url="sqlite:///:memory:", jwt_secret="x"*32)
```

**Real-world.** This is how every FastAPI codebase handles config — not module-level globals.

---

### Problem 13 — Per-tenant DB session

**Statement.** Multi-tenant SaaS where the tenant is in a header. Return a session that uses the tenant's DB schema.

**Solution.**
```python
async def get_tenant_session(x_tenant_id: str = Header(...)) -> AsyncSession:
    if not is_valid_tenant(x_tenant_id):
        raise HTTPException(403, "unknown tenant")
    async with SessionLocal() as session:
        await session.execute(text(f"SET search_path TO {x_tenant_id}_schema"))   # Postgres
        yield session

@app.get("/orders")
async def orders(session: AsyncSession = Depends(get_tenant_session)):
    return await session.scalars(select(Order))
```

**Real-world.** Schema-per-tenant is one valid multitenancy approach. Alternatives: row-level (cheaper, harder to isolate) or DB-per-tenant (most expensive, strongest isolation). The dependency-based pattern works for any of them.

**Follow-ups.** RLS (Row-Level Security) policies in Postgres. Tenant from JWT claim instead of header.

---

### Problem 14 — Login + JWT issuance

**Solution.** See §7.2 `auth.post("/token")`. The full flow:

```python
@auth.post("/token")
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()],
                session: AsyncSession = Depends(get_session)):
    user = await session.scalar(select(User).where(User.email == form.username))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "incorrect username or password")
    return {
        "access_token": create_access_token(str(user.id)),
        "token_type": "bearer",
    }
```

**Edge cases.** Constant-time comparison: `passlib`'s `verify` is already constant-time. Don't replace with `==`.

**Real-world.** This pattern works for B2C apps. For machine-to-machine, use the **client_credentials** grant. For "Sign in with Google," use **authorization_code** with a library like `authlib`.

**Follow-ups.** Refresh tokens (P15). Account lockout after N failed attempts. Email/SMS 2FA.

---

### Problem 15 — Refresh tokens

**Solution.**
```python
import secrets, hashlib

REFRESH_EXPIRE_DAYS = 14

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id:      Mapped[int]
    user_id: Mapped[int]
    token_hash: Mapped[str]                          # SHA-256 of raw token
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None] = mapped_column(default=None)

def issue_refresh(user_id: int, session) -> str:
    raw = secrets.token_urlsafe(64)
    h = hashlib.sha256(raw.encode()).hexdigest()
    session.add(RefreshToken(user_id=user_id, token_hash=h,
                             expires_at=datetime.utcnow() + timedelta(days=REFRESH_EXPIRE_DAYS)))
    return raw

@auth.post("/refresh")
async def refresh(refresh_token: Annotated[str, Body(...)],
                  session: AsyncSession = Depends(get_session)):
    h = hashlib.sha256(refresh_token.encode()).hexdigest()
    rt = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == h))
    if not rt or rt.revoked_at or rt.expires_at < datetime.utcnow():
        raise HTTPException(401, "invalid refresh token")
    return {"access_token": create_access_token(str(rt.user_id)), "token_type": "bearer"}

@auth.post("/logout")
async def logout(refresh_token: Annotated[str, Body(...)],
                 session: AsyncSession = Depends(get_session)):
    h = hashlib.sha256(refresh_token.encode()).hexdigest()
    rt = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == h))
    if rt: rt.revoked_at = datetime.utcnow(); await session.commit()
    return {"ok": True}
```

**Real-world.** Storing only the hash means a DB leak doesn't grant attackers active tokens. Rotate the refresh token on each use ("refresh token rotation") for extra defense.

**Follow-ups.** Detect refresh-token reuse → revoke entire family (token theft signal).

---

### Problem 16 — Role-based access (RBAC)

**Solution.**
```python
def require_roles(*required):
    def dep(user: User = Depends(get_current_user)):
        if not set(required) & set(user.roles or []):
            raise HTTPException(403, f"need one of {required}")
        return user
    return dep

@app.delete("/posts/{pid}", status_code=204)
async def delete_post(pid: int, user: User = Depends(require_roles("admin", "moderator"))):
    ...
```

**Real-world.** Roles work for most apps. For per-resource permissions ("can this user edit *this* post?") add an ownership check inside the route.

**Follow-ups.** Permission strings (`"posts:delete"`) over role names — more flexible. ABAC (attribute-based) for complex policies.

---

### Problem 17 — API key auth (for service-to-service)

**Solution.**
```python
import hmac, hashlib

async def get_service(x_api_key: str = Header(...), session: AsyncSession = Depends(get_session)):
    # store hashed keys; compare hashes in constant time
    h = hashlib.sha256(x_api_key.encode()).hexdigest()
    svc = await session.scalar(select(ServiceAccount).where(ServiceAccount.key_hash == h))
    if not svc:
        raise HTTPException(401, "invalid api key")
    return svc

@app.post("/internal/replay", dependencies=[Depends(get_service)])
async def replay(): ...
```

**Real-world.** Internal APIs and machine-to-machine. API keys are simpler than full OAuth2 client_credentials but lack token expiry — rotate manually or pair with short-lived JWTs.

**Follow-ups.** Hash with HMAC-SHA-256 + per-service secret. Key prefixes for searchability (`sk_live_...`).

---

### Problem 18 — CSRF protection (for cookie-auth flows)

**Statement.** A web app uses cookie-based auth. Implement CSRF token check.

**Solution (double-submit cookie pattern).**
```python
import secrets
from fastapi import Cookie, HTTPException

@app.get("/csrf")
def get_csrf_token(response: Response):
    token = secrets.token_urlsafe(32)
    response.set_cookie("csrf_token", token, samesite="strict", secure=True, httponly=False)
    return {"csrf_token": token}

async def require_csrf(x_csrf_token: str | None = Header(None),
                       csrf_token: str | None = Cookie(None)):
    if not x_csrf_token or x_csrf_token != csrf_token:
        raise HTTPException(403, "csrf token mismatch")

@app.post("/posts", dependencies=[Depends(require_csrf)])
async def create_post(): ...
```

**Real-world.** Only relevant when you authenticate via cookies. For pure API + JWT in `Authorization` header, CSRF isn't applicable. `SameSite=Strict` cookies eliminate most CSRF without tokens.

**Follow-ups.** Synchronizer-token pattern (server-side store). Per-form tokens.

---

### Problem 19 — Repository pattern for clean routes

**Solution (full pattern).**
```python
class UserRepository:
    def __init__(self, session: AsyncSession): self.s = session
    async def by_id(self, uid: int) -> User | None: return await self.s.get(User, uid)
    async def by_email(self, email: str) -> User | None:
        return await self.s.scalar(select(User).where(User.email == email))
    async def create(self, c: UserCreate) -> User:
        u = User(email=c.email, name=c.name, password_hash=hash_password(c.password))
        self.s.add(u); await self.s.flush(); return u
    async def page(self, after: int | None, limit: int) -> list[User]:
        stmt = select(User).order_by(User.id).limit(limit)
        if after: stmt = stmt.where(User.id > after)
        return list(await self.s.scalars(stmt))

async def get_user_repo(s: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(s)
```

Routes become trivial:
```python
@router.get("/{uid}", response_model=UserPublic)
async def get_user(uid: int, repo: UserRepository = Depends(get_user_repo)):
    user = await repo.by_id(uid)
    if not user: raise HTTPException(404)
    return user
```

**Real-world.** Worth the abstraction in any codebase > a few thousand lines. Tests mock `UserRepository`, not the entire DB.

**Follow-ups.** Service layer on top — `UserService(UserRepository, EmailRepository, ...)` with multi-step business logic.

---

### Problem 20 — Atomic create-with-side-effects

**Statement.** Creating an order should: (1) insert row, (2) decrement stock, (3) enqueue email — atomically wrt the DB writes.

**Solution.**
```python
@router.post("", response_model=OrderPublic, status_code=201)
async def create_order(payload: OrderCreate, bg: BackgroundTasks,
                       session: AsyncSession = Depends(get_session)):
    async with session.begin():                                # transaction
        product = await session.get(Product, payload.product_id, with_for_update=True)
        if not product or product.stock < payload.qty:
            raise HTTPException(409, "out of stock")
        product.stock -= payload.qty
        order = Order(product_id=product.id, qty=payload.qty,
                      total_cents=product.price * payload.qty)
        session.add(order)
        await session.flush()                                  # get order.id
    # only enqueue email AFTER the transaction commits — never inside
    bg.add_task(send_order_confirmation, order.id)
    return order
```

**Why outside the transaction.** A queued email for an order that fails to commit is a phantom — confusing for users and support. Enqueue only after commit.

**Real-world.** Bookings, charges, inventory. The `with_for_update` lock prevents oversold stock.

**Follow-ups.** Idempotency-Key for retry safety. Outbox pattern: store events in a DB table within the same tx, separate worker forwards to message bus.

---

### Problem 21 — Bulk endpoint with partial failures

**Statement.** `POST /users/bulk` accepts up to 1000 users; report per-row success/failure.

**Solution.**
```python
class BulkUsersIn(BaseModel):
    users: list[UserCreate] = Field(..., max_length=1000)

class BulkUsersOut(BaseModel):
    results: list[dict]   # [{"index": 0, "ok": True, "id": 1}, {"index": 1, "ok": False, "error": "duplicate email"}]

@router.post("/bulk", response_model=BulkUsersOut)
async def bulk_create(payload: BulkUsersIn, repo: UserRepository = Depends(get_user_repo)):
    results = []
    for i, u in enumerate(payload.users):
        try:
            saved = await repo.create(u)
            results.append({"index": i, "ok": True, "id": saved.id})
        except IntegrityError as e:
            results.append({"index": i, "ok": False, "error": "duplicate email"})
    return {"results": results}
```

**Real-world.** Bulk endpoints should usually be 207 Multi-Status semantics (success + per-item status), not 200/400. Don't fail the whole batch for one bad row unless that's the explicit semantics.

**Follow-ups.** True transactional bulk (all-or-nothing). Streaming results for very large batches.

---

### Problem 22 — Optimistic locking on update

**Solution.**
```python
class ProductUpdate(BaseModel):
    name:    str | None = None
    price:   int | None = None
    version: int                                        # required — caller's current view

@router.patch("/{pid}")
async def update_product(pid: int, u: ProductUpdate, session: AsyncSession = Depends(get_session)):
    p = await session.get(Product, pid)
    if not p: raise HTTPException(404)
    if p.version != u.version:
        raise HTTPException(409, {"detail":"stale", "current_version": p.version})
    if u.name is not None:  p.name = u.name
    if u.price is not None: p.price = u.price
    p.version += 1
    await session.commit()
    return p
```

**Real-world.** Prevents the lost-update problem (Module 3 P27) without holding row locks across the API call. UI sends back the version it last saw; server rejects on mismatch.

**Follow-ups.** Hidden version via `If-Match` ETag header (more RESTful). SQLAlchemy `version_id_col` (Module 3 P21) for automatic handling.

---

### Problem 23 — Search with pagination, total, and DB-side filtering

**Solution.**
```python
class UserSearchOut(BaseModel):
    items: list[UserPublic]
    total: int
    page: int
    size: int

@router.get("", response_model=UserSearchOut)
async def search_users(q: str | None = None, page: int = Query(1, ge=1),
                       size: int = Query(20, ge=1, le=100),
                       session: AsyncSession = Depends(get_session)):
    base = select(User)
    if q: base = base.where(User.name.ilike(f"%{q}%"))   # DB-side filter
    total = await session.scalar(select(func.count()).select_from(base.subquery()))
    items = list(await session.scalars(base.order_by(User.id).offset((page-1)*size).limit(size)))
    return {"items": items, "total": total, "page": page, "size": size}
```

**Note.** Offset pagination is fine for search results because users won't paginate past page ~20 anyway. For unbounded lists (admin views), use cursor.

**Follow-ups.** Postgres trigram (`pg_trgm`) for fuzzy search. ElasticSearch when you outgrow `ILIKE`.

---

### Problem 24 — SSE token streaming (LLM-style)

**Solution.**
```python
import asyncio
from sse_starlette.sse import EventSourceResponse

async def fake_llm(prompt: str):
    for token in f"You said: {prompt}".split():
        await asyncio.sleep(0.05)
        yield {"event": "token", "data": token}
    yield {"event": "done", "data": ""}

@app.get("/chat/stream")
async def chat_stream(prompt: str):
    return EventSourceResponse(fake_llm(prompt))
```

**Client side (browser).**
```javascript
const es = new EventSource("/chat/stream?prompt=hello");
es.addEventListener("token", e => console.log(e.data));
es.addEventListener("done",  () => es.close());
```

**Real-world.** Every LLM chat UI uses this. Lower latency than waiting for full response; handles network interruption better than WebSocket for one-way streams.

**Follow-ups.** Cancellation — detect client disconnect via `await request.is_disconnected()` and stop generation. `keepalive` events to defeat proxy timeouts.

---

### Problem 25 — WebSocket chat with rooms

**Solution.**
```python
from fastapi import WebSocket, WebSocketDisconnect

class RoomManager:
    def __init__(self): self.rooms: dict[str, set[WebSocket]] = {}
    async def join(self, room, ws):  self.rooms.setdefault(room, set()).add(ws)
    async def leave(self, room, ws): self.rooms.get(room, set()).discard(ws)
    async def broadcast(self, room, msg):
        for ws in list(self.rooms.get(room, [])):
            try: await ws.send_json(msg)
            except: self.rooms[room].discard(ws)

mgr = RoomManager()

@app.websocket("/ws/{room}")
async def ws_chat(ws: WebSocket, room: str):
    await ws.accept()
    await mgr.join(room, ws)
    try:
        while True:
            data = await ws.receive_json()
            await mgr.broadcast(room, {"user": data.get("user"), "text": data.get("text")})
    except WebSocketDisconnect:
        await mgr.leave(room, ws)
```

**Real-world.** Single-process apps only. For multi-server, route via Redis pub/sub: each server subscribes; broadcasts publish; subscribers fan out to local connections.

**Follow-ups.** Auth on WebSocket (token in query param or first message). Reconnect with last-message-id (resume).

---

### Problem 26 — Streaming file upload to S3

**Statement.** Avoid loading large uploads into memory; pipe directly from request body to object storage.

**Solution (sketch).**
```python
import aioboto3

@app.post("/upload-stream")
async def upload(request: Request, name: str):
    session = aioboto3.Session()
    async with session.client("s3") as s3:
        # multipart upload for large files
        mp = await s3.create_multipart_upload(Bucket="my-bucket", Key=name)
        upload_id = mp["UploadId"]
        parts = []
        chunk_no = 1
        async for chunk in request.stream():
            if not chunk: continue
            r = await s3.upload_part(Bucket="my-bucket", Key=name,
                                     PartNumber=chunk_no, UploadId=upload_id, Body=chunk)
            parts.append({"PartNumber": chunk_no, "ETag": r["ETag"]})
            chunk_no += 1
        await s3.complete_multipart_upload(Bucket="my-bucket", Key=name,
                                           UploadId=upload_id,
                                           MultipartUpload={"Parts": parts})
    return {"key": name}
```

**Real-world.** This is rarely the right pattern — **presigned URLs** (client uploads directly to S3) is better: lower API cost, no bandwidth through your server, no timeout issues.

**Follow-ups.** Generate presigned PUT URL: `s3.generate_presigned_url("put_object", ...)`. Client uploads directly; backend just returns the URL.

---

### Problem 27 — Server-Sent Events with cancellation

**Solution.**
```python
@app.get("/long-stream")
async def long_stream(request: Request):
    async def gen():
        for i in range(1000):
            if await request.is_disconnected():
                break                                       # client gone — stop work
            await asyncio.sleep(0.5)
            yield {"data": str(i)}
    return EventSourceResponse(gen())
```

**Real-world.** Saves compute on dropped clients (mobile network drops, browser tab closes). Especially important when each token costs LLM API money.

**Follow-ups.** Use `asyncio.timeout` to bound generation. Heartbeat events to keep connection alive through proxies.

---

### Problem 28 — End-to-end test of CRUD

**Solution.**
```python
# tests/test_products.py
def test_create_get_delete_product(client):
    r = client.post("/products", json={"name":"Pen", "price":150, "sku":"PEN-001"})
    assert r.status_code == 201
    pid = r.json()["id"]

    r = client.get(f"/products/{pid}")
    assert r.status_code == 200
    assert r.json()["sku"] == "PEN-001"

    r = client.delete(f"/products/{pid}")
    assert r.status_code == 204

    r = client.get(f"/products/{pid}")
    assert r.status_code == 404

def test_invalid_input(client):
    r = client.post("/products", json={"name":"", "price":-10, "sku":"x"})
    assert r.status_code == 422
    errors = {tuple(e["loc"]): e["type"] for e in r.json()["detail"]}
    assert ("body", "name") in errors
    assert ("body", "price") in errors
```

**Real-world.** This is the test layer that catches integration bugs (routing, validation, status codes). Combine with unit tests on services for fast inner-loop tests.

**Follow-ups.** `pytest --cov=src/my_api` for coverage. Snapshot-test the OpenAPI schema to detect accidental breaking changes.

---

### Problem 29 — Test with overridden dependency

**Solution.**
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from my_api.main import app
from my_api.security import get_current_user
from my_api.models import User

class FakeUser(User):
    def __init__(self):
        self.id = 1; self.email = "test@x"; self.name = "Test"; self.roles = ["admin"]

@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: FakeUser()
    yield TestClient(app)
    app.dependency_overrides.clear()

# tests/test_admin.py
def test_admin_only(client):
    r = client.delete("/posts/1")
    assert r.status_code in {204, 404}             # success or not-found, never 403
```

**Real-world.** This is the highest-leverage test pattern in FastAPI. Skips real auth in tests; routes still exercise their full logic.

**Follow-ups.** Per-test override (use the dependency_overrides via context manager). Fake DB session that runs against an in-memory SQLite.

---

### Problem 30 — Async test of concurrent calls

**Solution.**
```python
import pytest, asyncio, httpx
from httpx import ASGITransport
from my_api.main import app

@pytest.mark.asyncio
async def test_concurrent_increments():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as ac:
        # 50 concurrent POSTs — your endpoint must handle them safely
        responses = await asyncio.gather(*[ac.post("/counter/incr") for _ in range(50)])
    assert all(r.status_code == 200 for r in responses)
    final = (await ac.get("/counter")).json()["value"]
    assert final == 50          # if not, you have a race condition
```

**Real-world.** Catches concurrency bugs in dev. Race conditions are nearly invisible under low load.

**Follow-ups.** Stress test with `locust`. Chaos test (random latency, random failures via a middleware in test mode).

---

### Problem 31 — Snapshot-testing the OpenAPI

**Solution.**
```python
# tests/test_openapi.py
from my_api.main import app

def test_openapi_snapshot(snapshot):    # using `pytest-snapshot`
    schema = app.openapi()
    snapshot.assert_match(json.dumps(schema, indent=2, sort_keys=True), "openapi.json")
```

If the schema changes, the test fails — forcing a deliberate review of API breakage. Approve with `--snapshot-update`.

**Real-world.** Cheap insurance against accidental API breakage. SDK consumers will thank you.

**Follow-ups.** Diff against a published spec (`openapi-diff` tool) to flag breaking changes specifically.

---

### Problem 32 — Health and readiness endpoints

**Solution.**
```python
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/ready")
async def ready(session: AsyncSession = Depends(get_session)):
    try:
        await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=2)
        await asyncio.wait_for(redis_client.ping(), timeout=1)
    except Exception as e:
        raise HTTPException(503, f"not ready: {e}")
    return {"status": "ready"}
```

**Real-world.** Kubernetes uses `/health` as liveness (process is alive — don't restart) and `/ready` as readiness (drains traffic if it fails). Don't combine them.

**Follow-ups.** Per-dependency health (`{"db":"ok","cache":"ok","queue":"degraded"}`). Cached readiness (avoid hammering deps).

---

### Problem 33 — Graceful shutdown with lifespan

**Solution.**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    app.state.http = httpx.AsyncClient(timeout=10)
    app.state.engine = create_async_engine(settings.database_url)
    yield
    # shutdown — finish in-flight requests then clean up
    await app.state.http.aclose()
    await app.state.engine.dispose()

app = FastAPI(lifespan=lifespan)
```

Combined with `gunicorn --graceful-timeout 30`, the server waits for in-flight requests up to 30s before forcing shutdown.

**Real-world.** Without graceful shutdown, deploys cause user-visible 502s. The lifespan + Gunicorn timeout handles this.

**Follow-ups.** Drain probes (return 503 on `/ready` during shutdown so the LB stops sending traffic). Long-running requests need a deadline mechanism.

---

### Problem 34 — Behind a reverse proxy (X-Forwarded-For, root_path)

**Statement.** App is behind nginx at `https://example.com/api/v1/`. Logs show `127.0.0.1` for client IPs; OpenAPI URL is wrong.

**Solution.**
```python
app = FastAPI(root_path="/api/v1")           # OpenAPI URL becomes correct

# Run with proxy headers respected
# uvicorn my_api.main:app --proxy-headers --forwarded-allow-ips="*"
```

```python
@app.get("/echo-ip")
async def echo_ip(request: Request):
    return {"ip": request.client.host}      # now reflects X-Forwarded-For (with --proxy-headers)
```

**Real-world.** Every prod deploy. Without `--proxy-headers`, IP-based logic and rate-limits all see the LB's IP.

**Follow-ups.** Set `forwarded-allow-ips` to your LB's IPs (not `*`) for security. Trust forwarded HTTPS only from known proxies.

---

### Problem 35 — Reusing httpx client and timeouts

**Solution.**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    timeout = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)
    limits  = httpx.Limits(max_keepalive_connections=20, max_connections=100)
    app.state.http = httpx.AsyncClient(timeout=timeout, limits=limits)
    yield
    await app.state.http.aclose()

@app.get("/proxy")
async def proxy(request: Request, url: str):
    try:
        r = await request.app.state.http.get(url)
    except httpx.TimeoutException:
        raise HTTPException(504, "upstream timeout")
    return {"status": r.status_code, "len": len(r.content)}
```

**Why.** A new client per request creates a new TLS handshake and connection pool — at scale, this is your latency. One shared client reuses connections, dramatically improving throughput.

**Real-world.** Mandatory for any API that calls outward (LLM APIs, third-party services). Without timeouts, a slow upstream hangs your workers indefinitely.

**Follow-ups.** Per-host pool sizing. Retry middleware with `httpx.HTTPTransport(retries=3)`. Circuit breaker (`tenacity` or custom).

---

### Problem 36 — Profile a slow endpoint

**Statement.** `/dashboard` returns in 4 seconds. Find why.

**Solution.**
```python
import time, structlog
log = structlog.get_logger()

@app.middleware("http")
async def slow_request_log(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    if elapsed_ms > 500:
        log.warning("slow_request", path=request.url.path,
                    status=response.status_code, ms=elapsed_ms)
    return response
```

Then add SQLAlchemy timing:
```python
from sqlalchemy import event

@event.listens_for(engine.sync_engine, "before_cursor_execute")
def before(conn, cursor, statement, params, context, executemany):
    context._t0 = time.perf_counter()

@event.listens_for(engine.sync_engine, "after_cursor_execute")
def after(conn, cursor, statement, params, context, executemany):
    elapsed = (time.perf_counter() - context._t0) * 1000
    if elapsed > 100:
        log.warning("slow_query", ms=elapsed, sql=statement[:200])
```

For pure profiling, attach `py-spy` to the running process (Module 1 §18.3). For distributed traces, OpenTelemetry (§15.2) with a Jaeger / Tempo backend.

**Real-world.** Slow dashboards are almost always: (1) N+1 queries, (2) one bad query missing an index, or (3) an unbounded list. Trace data tells you which.

**Follow-ups.** Flame graphs from py-spy. Database query plans (`EXPLAIN`). Per-handler latency histograms in Prometheus.

---

## 19. Three mini-projects

### Mini-project A — A small e-commerce API
Domain: products, orders, users. Stack: FastAPI + async SQLAlchemy + PostgreSQL + Redis. Implement: register/login/refresh, list/get/create products (admin-only), place order (with stock decrement and idempotency), order history, status webhook handler. Add Alembic migrations, structured logging, OpenTelemetry, Dockerfile, docker-compose with Postgres+Redis. ~25 tests covering happy path + 3 failure modes per endpoint.

**Skills exercised:** every section of this module + Modules 2–3.

### Mini-project B — A streaming chat backend
WebSocket-based chat with rooms and presence. SSE-based "AI replies" endpoint (mock the LLM with a token-by-token generator from §10.2). Redis pub/sub for multi-instance broadcast. JWT auth on WebSocket via query param. Frontend: a tiny HTML page with `<script>`. Goal: handle 1000 concurrent connections on a single uvicorn worker.

**Skills exercised:** WebSockets, SSE, async patterns, Redis pub/sub, lifespan.

### Mini-project C — An API gateway / BFF
A FastAPI service that aggregates 3+ downstream microservices (mocked with httpbin or your own). Adds: auth, rate limiting, request correlation IDs, retries, circuit breaker for one downstream, response caching, audit log to a queue. Document with OpenAPI; ship in Docker; load-test with `locust` and capture p50/p95/p99 latency.

**Skills exercised:** middleware, dependencies, observability, async HTTP, caching strategy.

---

## 20. Real-world usage map

| Concept | Where it returns later |
|---|---|
| Pydantic 2 schemas | Module 7 (ML) for inference request/response; Module 11 (agents) for tool args |
| `response_model` | Strict serialization of model outputs in Module 13 (LLMOps) |
| Dependency injection | Per-request DB session, per-request LLM client, per-request agent context |
| OAuth2 + JWT | Multi-tenant LLM apps; per-user usage quotas |
| Lifespan | Loading ML models once at startup; opening LLM clients |
| SSE streaming | LLM token streaming UIs everywhere in Modules 10/13 |
| WebSockets | Live agent updates; collaborative editing surfaces |
| BackgroundTasks | Post-response logging, embeddings indexing |
| Repository pattern | Test seam between API and DB in any module that persists data |
| Idempotency-Key | Charge-once semantics for paid LLM calls |
| Health/Readiness | Kubernetes deploys for ML serving (Module 12) |
| OpenTelemetry | Tracing model serving and agent loops |
| Structured logs | LLM observability (langfuse/langsmith ingestion) |

---

## 21. Interview pitfalls — what NOT to say

- **"I'll use Flask because it's simpler."** Defensible 5 years ago. Today, FastAPI is comparably simple, async-native, and gives you typing + docs for free. Justify the choice if you avoid it.
- **"I make all routes async because async is faster."** Only for I/O. CPU-bound async routes still block the loop.
- **"I share one database session across requests."** Never. Per-request session via dependency.
- **"I return SQLAlchemy models directly."** They're tied to a session; serialization will fail or leak fields. Use `response_model`.
- **"Pydantic validation is slow."** v2 is in Rust — typically faster than the manual checks people replace it with. Measure before optimizing it away.
- **"I caught all exceptions and returned 200."** Then your client can't distinguish success from failure. Use proper status codes.
- **"`allow_origins=['*']` and we're done."** Not with credentials, not in production.
- **"JWTs are encrypted."** They're signed. The payload is base64 — anyone can read it. Don't put secrets there.
- **"I'll roll my own auth."** Don't. Use `OAuth2PasswordBearer` + `pyjwt` + `passlib`.
- **"`requests` works fine in my async handler."** It blocks the event loop. Use `httpx` or `to_thread`.
- **"I scaled by adding more workers."** First check whether your async code is actually awaiting; a blocking call serializes everything.
- **"BackgroundTasks for sending an important email."** It runs in-process. Crash → email lost. Use a real queue.
- **"`OFFSET 1000000` is fine."** No. Cursor pagination.

**How to communicate during an interview.** When asked to design an endpoint: state (1) input schema and validation, (2) auth/authz, (3) DB queries (with the join cardinality), (4) failure modes and status codes, (5) idempotency, (6) observability hooks. This signals seriousness.

---

## 22. Cheatsheet

```text
APP SETUP
  app = FastAPI(title=..., version=..., lifespan=lifespan)
  app.include_router(router, prefix="/v1")
  app.add_middleware(GZipMiddleware, minimum_size=1024)

ROUTES
  @app.get / .post / .put / .patch / .delete / .head / .options
  path: /users/{uid}        — uid in signature
  query: limit: int = Query(20, ge=1, le=100)
  header: x_req: str = Header(None)
  cookie: c: str = Cookie(None)
  body:   payload: ModelIn

PYDANTIC 2
  class M(BaseModel):
      model_config = ConfigDict(extra="forbid", from_attributes=True)
      x: int = Field(..., ge=0, le=100)
      y: str = Field("default", min_length=1, max_length=50, pattern=r"...")
      tags: list[str] = Field(default_factory=list, max_length=10)

      @field_validator("x")
      @classmethod
      def chk(cls, v): ...

      @model_validator(mode="after")
      def chk_pair(self): ...

  m.model_dump() / .model_dump_json() / Model.model_validate(d)

RESPONSE
  @app.get("/x", response_model=Out, status_code=200, response_model_exclude_none=True)
  raise HTTPException(404, detail="...")
  return Response(status_code=204)
  return JSONResponse(content=..., status_code=...)
  return StreamingResponse(generator, media_type="text/csv", headers={...})
  return EventSourceResponse(generator)        # SSE — sse-starlette

DEPENDENCY INJECTION
  def dep(...) -> X: ...
  Annotated[X, Depends(dep)]      # modern style
  yield-deps for cleanup: try/finally inside; commit on success
  app.dependency_overrides[dep] = fake     # in tests; clear() to reset
  Depends() (with type hint) for class-based deps

ASYNC RULES
  async def for I/O routes; def for pure CPU
  never call blocking funcs in async (httpx not requests; aiomysql not pymysql)
  shared client via lifespan; request.app.state.http
  asyncio.to_thread(sync_fn, args) as escape hatch

AUTH (OAuth2 password flow + JWT)
  scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
  jwt.encode(payload, secret, algorithm=alg)
  jwt.decode(tok,    secret, algorithms=[alg])     # ALWAYS list
  passlib.CryptContext(["bcrypt"]).hash / .verify   # constant-time
  refresh tokens: hash before storing, rotate on use

CORS
  CORSMiddleware(allow_origins=[...], allow_credentials=True,
                 allow_methods=[...], allow_headers=["*"])
  no "*" with credentials

MIDDLEWARE
  @app.middleware("http")
  async def m(request, call_next):
      pre...
      response = await call_next(request)
      post...
      return response

  request.state.x  per-request scratchpad

ERRORS
  @app.exception_handler(MyExc)
  async def h(request, exc): return JSONResponse(...)

STATUS CODES
  200 OK | 201 Created | 202 Accepted | 204 No Content
  400 Bad | 401 Unauth | 403 Forbid | 404 Not Found
  409 Conflict | 422 Validation | 429 Rate
  500 Bug | 502/503/504 downstream

WEBSOCKETS / SSE
  @app.websocket("/ws"): await ws.accept(); ws.send_text/json; receive_text/json
  WebSocketDisconnect on hangup
  sse-starlette EventSourceResponse(gen) where gen yields {"event":..., "data":...}
  await request.is_disconnected()  for SSE cancellation

TESTING
  TestClient(app); .get/.post/.put/.delete with json=, params=, headers=
  app.dependency_overrides[get_current_user] = fake_user
  pytest fixtures in conftest.py
  ASGITransport for true async tests with httpx.AsyncClient

DEPLOY
  gunicorn my_api.main:app -k uvicorn.workers.UvicornWorker -w N -b 0.0.0.0:8000 --timeout 30 --graceful-timeout 30
  uvicorn ... --proxy-headers --forwarded-allow-ips="<lb-ips>"
  /health (liveness) | /ready (readiness, checks deps)
  lifespan for startup/shutdown resources

OBSERVABILITY
  structlog JSON logs with request_id contextvar
  OpenTelemetry: FastAPIInstrumentor + SQLAlchemyInstrumentor + HTTPXInstrumentor
  Prometheus: Counter / Histogram / generate_latest

PERF CHECKLIST
  one shared httpx client; sane timeouts (connect/read/write/pool)
  async DB driver; selectinload to fix N+1
  GZipMiddleware for big responses
  Redis cache on hot reads
  cursor pagination; never OFFSET on big tables
  rate limit at edge AND in app
```

---

## 23. Prerequisites & next steps

**Prerequisites covered? You can:**
- Lay out a multi-resource FastAPI codebase with routers, schemas, models, services.
- Validate input with Pydantic 2 (field + model validators, discriminated unions).
- Pick correct status codes and design consistent error envelopes.
- Use the dependency injection system for DB sessions, auth, settings, pagination, rate limits.
- Implement OAuth2 password flow with JWT access + refresh tokens.
- Choose between async and sync routes correctly; share `httpx.AsyncClient` via lifespan.
- Stream tokens via SSE and bidirectional traffic via WebSocket.
- Test thoroughly with TestClient and overridden dependencies.
- Deploy behind Gunicorn+Uvicorn in Docker with health/readiness probes.
- Wire up structured logging, OpenTelemetry tracing, and Prometheus metrics.

**Next steps in the bible:**
- **Module 5 — BigQuery & warehousing.** Big-data SQL on top of what you learned in Module 3.
- **Module 6 — Cloud foundations.** AWS/GCP/Azure for ML serving (the deploy target for everything you build).
- **Module 7 — Classical ML.** The first time we'll wrap a real model in a FastAPI inference endpoint.
- **Module 13 — LLMOps.** Reuses streaming, auth, observability patterns from this module for LLM apps.

**External study (only if you want depth):**
- The official FastAPI docs (Sebastián Ramírez writes them like a tutorial — work through the entire "Tutorial" + "Advanced User Guide").
- *Architecture Patterns with Python* (Percival & Gregory) — repository, unit-of-work, service layer patterns. Maps directly onto FastAPI codebases.
- The Pydantic 2 migration guide if you have v1 code.

---

*End of Module 4. Module 5 covers BigQuery, partitioning, clustering, performance tuning, and cost control — same structure, 35+ problems.*
