# 09 — Testing & DevOps Interview Questions
## Complete Questions with Python Examples

---

## 9.1 Testing with pytest

### Q1: Explain Python testing best practices with pytest.

```python
# ═══════════════════════════════════════
# Basic pytest
# ═══════════════════════════════════════
# test_calculator.py
def add(a, b):
    return a + b

def test_add_positive():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-1, -1) == -2

def test_add_zero():
    assert add(0, 0) == 0

# Run: pytest test_calculator.py -v

# ═══════════════════════════════════════
# Fixtures — setup/teardown for tests
# ═══════════════════════════════════════
import pytest

@pytest.fixture
def sample_user():
    """Create a test user — runs before each test that uses it."""
    user = {"name": "Alice", "email": "alice@test.com", "age": 30}
    yield user
    # Teardown code runs after test completes
    print("Cleaning up test user")

@pytest.fixture
def db_session():
    """Database session with automatic rollback."""
    session = create_test_session()
    yield session
    session.rollback()
    session.close()

def test_user_name(sample_user):
    assert sample_user["name"] == "Alice"

def test_user_email(sample_user):
    assert "@" in sample_user["email"]

# Fixture scopes
@pytest.fixture(scope="module")     # Once per test module
def expensive_resource():
    return load_ml_model()

@pytest.fixture(scope="session")    # Once per entire test run
def database():
    return create_test_database()

# ═══════════════════════════════════════
# Parametrize — test multiple inputs
# ═══════════════════════════════════════
@pytest.mark.parametrize("input_val, expected", [
    (1, 1),
    (2, 4),
    (3, 9),
    (0, 0),
    (-3, 9),
])
def test_square(input_val, expected):
    assert input_val ** 2 == expected

@pytest.mark.parametrize("email, is_valid", [
    ("user@example.com", True),
    ("invalid-email", False),
    ("", False),
    ("user@.com", False),
    ("a@b.c", True),
])
def test_email_validation(email, is_valid):
    assert validate_email(email) == is_valid

# ═══════════════════════════════════════
# Testing exceptions
# ═══════════════════════════════════════
def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        1 / 0

def test_value_error_message():
    with pytest.raises(ValueError, match="must be positive"):
        create_account(balance=-100)

# ═══════════════════════════════════════
# Mocking — isolate units under test
# ═══════════════════════════════════════
from unittest.mock import Mock, patch, MagicMock

# Mock external dependencies
def get_user_data(user_id):
    response = requests.get(f"https://api.example.com/users/{user_id}")
    return response.json()

def test_get_user_data():
    with patch("mymodule.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"name": "Alice", "id": 1}
        mock_get.return_value.status_code = 200

        result = get_user_data(1)

        assert result["name"] == "Alice"
        mock_get.assert_called_once_with("https://api.example.com/users/1")

# Mock as decorator
@patch("mymodule.send_email")
@patch("mymodule.db.save")
def test_create_user(mock_save, mock_email):
    mock_save.return_value = {"id": 1, "name": "Alice"}
    create_user("Alice", "alice@test.com")
    mock_save.assert_called_once()
    mock_email.assert_called_once()

# ═══════════════════════════════════════
# Async testing
# ═══════════════════════════════════════
import pytest_asyncio

@pytest.mark.asyncio
async def test_async_fetch():
    result = await async_fetch_data("https://example.com")
    assert result is not None

# ═══════════════════════════════════════
# Test organization best practices
# ═══════════════════════════════════════
"""
tests/
├── conftest.py           # Shared fixtures
├── unit/
│   ├── test_models.py
│   └── test_services.py
├── integration/
│   ├── test_api.py
│   └── test_database.py
└── e2e/
    └── test_workflows.py

# conftest.py — shared fixtures auto-discovered by pytest
@pytest.fixture(autouse=True)
def reset_database(db_session):
    yield
    db_session.rollback()

# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "slow: marks tests as slow",
    "integration: marks integration tests",
]
addopts = "-v --tb=short --strict-markers"
"""

# Markers — categorize tests
@pytest.mark.slow
def test_large_dataset_processing():
    pass

@pytest.mark.integration
def test_database_connection():
    pass

# Run: pytest -m "not slow"         # Skip slow tests
# Run: pytest -m integration        # Only integration tests
# Run: pytest --cov=mypackage       # With coverage report
```

---

## 9.2 Docker & Containerization

### Q2: Docker essentials for Python developers.

```dockerfile
# ═══════════════════════════════════════
# Production Dockerfile for Python app
# ═══════════════════════════════════════
# Multi-stage build — smaller final image
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

# Security: don't run as root
RUN useradd --create-home appuser
WORKDIR /home/appuser/app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local
COPY . .

# Ensure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH

USER appuser
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/myapp
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d myapp"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine

volumes:
  pgdata:
```

---

## 9.3 CI/CD & Git

### Q3: CI/CD pipeline and Git workflow.

```yaml
# .github/workflows/ci.yml (GitHub Actions)
name: CI Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint
        run: ruff check .

      - name: Type check
        run: mypy src/

      - name: Test with coverage
        run: pytest --cov=src --cov-report=xml -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

```bash
# Git workflow essentials
git flow feature start my-feature    # Create feature branch
git rebase -i HEAD~3                 # Squash commits before merge
git cherry-pick abc123               # Apply specific commit
git bisect start                     # Find bug-introducing commit
git stash                            # Temporarily save changes
git log --oneline --graph            # Visual branch history
```

---

## 9.4 Logging & Monitoring

### Q4: Production-grade logging in Python.

```python
import logging
import json
from datetime import datetime

# ═══════════════════════════════════════
# Structured logging setup
# ═══════════════════════════════════════
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        return json.dumps(log_data)

def setup_logging():
    logger = logging.getLogger("myapp")
    logger.setLevel(logging.INFO)

    # Console handler with JSON formatting
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    # File handler for errors
    error_handler = logging.FileHandler("errors.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    logger.addHandler(error_handler)

    return logger

logger = setup_logging()

# Usage
logger.info("User logged in", extra={"extra_data": {"user_id": 42, "ip": "1.2.3.4"}})
logger.error("Payment failed", extra={"extra_data": {"order_id": 123, "amount": 99.99}})
```

---
