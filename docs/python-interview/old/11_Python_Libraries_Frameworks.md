# 11 — Python Libraries & Frameworks
## Interview Questions with Examples

---

## 11.1 FastAPI

### Q1: Explain FastAPI and build a production-ready API.

```python
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uvicorn

app = FastAPI(title="User API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models — automatic validation & serialization
class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(..., ge=0, le=150)

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    model_config = {"from_attributes": True}   # SQLAlchemy compatibility

# Dependency injection
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints
@app.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List users with pagination."""
    return db.query(User).offset(skip).limit(limit).all()

@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Background tasks
from fastapi import BackgroundTasks

@app.post("/users/{user_id}/notify")
async def notify_user(user_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_notification, user_id)
    return {"message": "Notification queued"}

# WebSocket
from fastapi import WebSocket

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

"""
FastAPI vs Flask vs Django:
  FastAPI: Async, auto-docs, Pydantic validation, modern — best for APIs
  Flask:   Simple, flexible, synchronous — best for small apps
  Django:  Batteries-included, ORM, admin — best for full web apps
"""
```

---

## 11.2 Django Essentials

### Q2: Key Django concepts for interviews.

```python
"""
Django Architecture: MTV (Model-Template-View)
  Model:    Database schema (ORM)
  Template: HTML rendering
  View:     Business logic (like Controller in MVC)

Key Components:
  - ORM:          Model classes → SQL tables
  - Migrations:   Schema version control
  - Admin:        Auto-generated admin interface
  - Middleware:    Request/response processing pipeline
  - Signals:      Decoupled event notifications
  - Forms:        Input validation
  - Auth:         User authentication built-in
"""

# Django Model
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    published_at = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField('Tag', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['published_at']),
            models.Index(fields=['author', 'published_at']),
        ]

    def __str__(self):
        return self.title

# QuerySet operations (lazy evaluation!)
Article.objects.filter(published_at__isnull=False)         # Published articles
Article.objects.exclude(author__is_active=False)            # Active authors
Article.objects.annotate(tag_count=Count('tags'))           # Add computed field
Article.objects.select_related('author')                    # JOIN (FK)
Article.objects.prefetch_related('tags')                    # Separate query (M2M)
Article.objects.values('author__username').annotate(count=Count('id'))  # GROUP BY

# Django REST Framework (DRF) — for APIs
from rest_framework import serializers, viewsets

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'author', 'published_at']

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['author', 'published_at']
```

---

## 11.3 Pandas & Data Processing

### Q3: Essential Pandas operations for interviews.

```python
import pandas as pd
import numpy as np

# ═══════════════════════════════════════
# Data loading & inspection
# ═══════════════════════════════════════
df = pd.read_csv("data.csv")
df.head()                  # First 5 rows
df.info()                  # Column types, null counts
df.describe()              # Statistical summary
df.shape                   # (rows, columns)
df.dtypes                  # Column data types
df.isnull().sum()          # Null counts per column

# ═══════════════════════════════════════
# Selection & Filtering
# ═══════════════════════════════════════
df['column']                           # Single column (Series)
df[['col1', 'col2']]                   # Multiple columns
df.loc[0:5, 'name':'email']           # Label-based selection
df.iloc[0:5, 0:3]                      # Integer-based selection
df[df['age'] > 30]                     # Boolean filtering
df.query("age > 30 and city == 'NYC'") # Query string

# ═══════════════════════════════════════
# Transformations
# ═══════════════════════════════════════
df['new_col'] = df['price'] * df['quantity']        # Vectorized operation
df['category'] = df['amount'].apply(lambda x: 'high' if x > 100 else 'low')
df['date'] = pd.to_datetime(df['date_str'])
df['year'] = df['date'].dt.year

# ═══════════════════════════════════════
# GroupBy & Aggregation
# ═══════════════════════════════════════
df.groupby('department').agg(
    avg_salary=('salary', 'mean'),
    max_salary=('salary', 'max'),
    employee_count=('id', 'count')
).reset_index()

# Pivot table
pd.pivot_table(df, values='sales', index='region',
               columns='quarter', aggfunc='sum', fill_value=0)

# ═══════════════════════════════════════
# Merging & Joining
# ═══════════════════════════════════════
merged = pd.merge(orders, customers, on='customer_id', how='left')
concat = pd.concat([df1, df2], ignore_index=True)

# ═══════════════════════════════════════
# Handling missing data
# ═══════════════════════════════════════
df.dropna(subset=['critical_column'])
df.fillna({'age': df['age'].median(), 'city': 'Unknown'})
df['value'] = df['value'].interpolate(method='linear')

# ═══════════════════════════════════════
# Performance tips
# ═══════════════════════════════════════
# Use vectorized operations (NOT iterrows!)
# ❌ Slow
for idx, row in df.iterrows():
    df.at[idx, 'new'] = row['a'] + row['b']

# ✅ Fast — vectorized
df['new'] = df['a'] + df['b']

# Use categorical for repeated strings
df['status'] = df['status'].astype('category')  # Huge memory savings

# Use chunking for large files
for chunk in pd.read_csv('huge.csv', chunksize=10000):
    process(chunk)
```

---

## 11.4 Pydantic

### Q4: Pydantic for data validation (used by FastAPI).

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime
from enum import Enum

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    due_date: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list, max_length=10)

    @field_validator('title')
    @classmethod
    def title_must_not_be_empty(cls, v):
        if v.strip() == "":
            raise ValueError("Title cannot be blank")
        return v.strip()

    @field_validator('tags')
    @classmethod
    def tags_must_be_lowercase(cls, v):
        return [tag.lower().strip() for tag in v]

    @model_validator(mode='after')
    def validate_due_date(self):
        if self.due_date and self.due_date < datetime.now():
            raise ValueError("Due date must be in the future")
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"title": "Review PR", "priority": "high", "tags": ["code"]}
            ]
        }
    }

# Usage
task = TaskCreate(title="  Review PR  ", priority="high", tags=["Code", "REVIEW"])
print(task.model_dump())
# {'title': 'Review PR', 'description': None, 'priority': 'high',
#  'due_date': None, 'tags': ['code', 'review']}

# Validation error
try:
    TaskCreate(title="", priority="invalid")
except Exception as e:
    print(e)  # Detailed validation errors

# Settings management
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"
    debug: bool = False
    api_key: str

    model_config = {"env_file": ".env", "env_prefix": "APP_"}

settings = Settings()  # Reads from env vars: APP_DATABASE_URL, APP_API_KEY, etc.
```

---

## 11.5 Celery

### Q5: Async task processing with Celery.

```python
"""
Celery Architecture:
  Producer (web app) → Broker (Redis/RabbitMQ) → Worker (Celery) → Backend (results)

When to use Celery:
  - Email sending
  - Report generation
  - Image/video processing
  - ML model inference
  - Scheduled tasks (cron-like)
  - Any long-running task that shouldn't block the web request
"""

from celery import Celery, chain, group, chord

app = Celery('tasks', broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/1')

app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    task_acks_late=True,                # Acknowledge after completion
    worker_prefetch_multiplier=1,       # Fair scheduling
    task_reject_on_worker_lost=True,    # Requeue on worker crash
)

@app.task(bind=True, max_retries=3)
def process_order(self, order_id):
    try:
        order = get_order(order_id)
        charge_payment(order)
        return {"status": "success", "order_id": order_id}
    except PaymentError as exc:
        self.retry(exc=exc, countdown=2 ** self.request.retries)

# Periodic tasks (Celery Beat)
app.conf.beat_schedule = {
    'cleanup-every-hour': {
        'task': 'tasks.cleanup_old_sessions',
        'schedule': 3600.0,
    },
    'daily-report': {
        'task': 'tasks.generate_daily_report',
        'schedule': crontab(hour=0, minute=0),
    },
}
```

---
