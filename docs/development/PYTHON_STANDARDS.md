# ForgeSyte Python Development Standards

This document outlines the standards all developers must follow when contributing Python code to ForgeSyte. These standards ensure code is production-ready, maintainable, resilient, and consistent across the project.

## Table of Contents

1. [Core Principles](#core-principles)
2. [Python Language Standards](#python-language-standards)
3. [Architectural Design & Patterns](#architectural-design--patterns)
4. [Resilience and Error Handling](#resilience-and-error-handling)
5. [Performance and Observability](#performance-and-observability)
6. [Testing Standards](#testing-standards)
7. [Development Workflow & Mandatory Tools](#development-workflow--mandatory-tools)

---

## Core Principles

### Prioritize Simplicity
Write clean, readable, and maintainable code. Avoid unnecessary complexity. Simple solutions are easier to understand, maintain, and debug.

### Maintainability over Cleverness
Choose obvious, straightforward solutions over clever hacks. Your code will be read and modified by other developers. Make their job easier.

### Self-Documenting Code
Use meaningful variable and function names that clearly express intent. Reduce the need for excessive comments through clear, expressive code.

**Good:**
```python
def calculate_total_price(items: list[Item], tax_rate: Decimal) -> Decimal:
    subtotal = sum(item.price * item.quantity for item in items)
    return subtotal * (1 + tax_rate)
```

**Avoid:**
```python
def calc_tp(i, tr):  # What does tp mean? What are i and tr?
    s = sum(x[0] * x[1] for x in i)
    return s * (1 + tr)
```

---

## Python Language Standards

### Style Guidelines
Strictly follow **PEP 8** style guidelines. Format code with `black` and lint with `ruff` before committing.

### Type Safety
Use **type hints** for all functions and modules. Type hints serve as executable documentation and catch bugs early.

```python
def process_order(order_id: str, items: list[str]) -> dict[str, int]:
    """Process an order and return item counts."""
    return {item: 1 for item in items}
```

**For Financial Values:** Always use `Decimal` instead of `float` to avoid precision errors in calculations.

```python
from decimal import Decimal

class Product(BaseModel):
    price: Decimal  # NOT float
    tax_rate: Decimal

def calculate_total(price: Decimal, quantity: int, tax_rate: Decimal) -> Decimal:
    subtotal = price * quantity
    return subtotal * (1 + tax_rate)
```

### Path Management
Prefer `pathlib.Path` over `os.path` for all file and directory operations. It's more modern and cross-platform.

```python
# Good
from pathlib import Path
config_file = Path("./config/settings.json")
if config_file.exists():
    data = json.loads(config_file.read_text())

# Avoid
import os
config_file = "./config/settings.json"
if os.path.exists(config_file):
    with open(config_file) as f:
        data = json.load(f)
```

### Documentation
Write comprehensive **docstrings** for all classes and functions. Use the Google-style or NumPy-style docstring format consistently.

```python
def export_data(
    source_file: Path,
    output_format: str,
    include_metadata: bool = True
) -> Path:
    """
    Export data from a source file in the specified format.
    
    Args:
        source_file: Path to the source data file
        output_format: Target format (csv, json, parquet)
        include_metadata: Whether to include metadata in output
        
    Returns:
        Path to the exported file
        
    Raises:
        FileNotFoundError: If source file does not exist
        ValueError: If output_format is not supported
    """
    if not source_file.exists():
        raise FileNotFoundError(f"Source file not found: {source_file}")
    
    # Implementation...
```

### Configuration Management
Manage configuration via **environment variables** or configuration files, never hard-code sensitive values.

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    database_url: str
    api_key: str
    debug_mode: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Usage
settings = Settings()
```

---

## Architectural Design & Patterns

### Separation of Concerns
Decouple the API layer from core business logic. Extract business rules into **dedicated service classes**.

```python
# ❌ Bad: Business logic mixed with API
@app.post("/orders")
def create_order(request: OrderRequest):
    order = Order(**request.dict())
    # Calculate tax, apply discounts, validate inventory all here
    ...
    db.add(order)
    return order

# ✅ Good: Business logic in service class
class OrderService:
    def create_order(self, request: OrderRequest) -> Order:
        order = Order(**request.dict())
        self._calculate_tax(order)
        self._apply_discounts(order)
        self._validate_inventory(order)
        return order

@app.post("/orders")
def create_order(request: OrderRequest, service: OrderService):
    order = service.create_order(request)
    db.add(order)
    return order
```

### Decoupling with Protocols
Use **Protocols** (structural typing) to define interfaces. Components should interact through contracts, not concrete implementations.

```python
from typing import Protocol

class DataStore(Protocol):
    """Any class implementing these methods can be used."""
    def get(self, key: str) -> Any: ...
    def set(self, key: str, value: Any) -> None: ...

class DatabaseStore:
    def get(self, key: str) -> Any:
        return db.query(key)
    
    def set(self, key: str, value: Any) -> None:
        db.store(key, value)

class CacheStore:
    def get(self, key: str) -> Any:
        return cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        cache.set(key, value)

def save_result(store: DataStore, key: str, value: Any):
    """Works with any DataStore-compatible implementation."""
    store.set(key, value)
```

### The Registry Pattern
Avoid long `if-elif` chains for algorithms or exporters. Use a **central registry** to map keys to behaviors.

```python
# ❌ Bad: Hard to extend, violates Open/Closed Principle
def export_data(format: str, data: list[dict]):
    if format == "csv":
        return export_csv(data)
    elif format == "json":
        return export_json(data)
    elif format == "parquet":
        return export_parquet(data)
    else:
        raise ValueError(f"Unknown format: {format}")

# ✅ Good: Easy to extend without modifying core code
EXPORTERS: dict[str, Callable] = {}

def register_exporter(format: str):
    def decorator(func: Callable):
        EXPORTERS[format] = func
        return func
    return decorator

@register_exporter("csv")
def export_csv(data: list[dict]) -> bytes:
    ...

@register_exporter("json")
def export_json(data: list[dict]) -> bytes:
    ...

def export_data(format: str, data: list[dict]) -> bytes:
    if format not in EXPORTERS:
        raise ValueError(f"Unknown format: {format}")
    return EXPORTERS[format](data)
```

### Composition over Inheritance
Prefer composition or **mixins** to add functionality. Avoid creating deep, brittle inheritance hierarchies.

```python
# ❌ Bad: Fragile inheritance chain
class User(BaseModel): ...
class PremiumUser(User): ...
class AdminUser(PremiumUser): ...
class AdminPremiumUser(AdminUser): ...  # This gets messy fast

# ✅ Good: Compose behaviors
class User(BaseModel):
    email: str

class PremiumMixin:
    def get_premium_features(self): ...

class AdminMixin:
    def get_admin_features(self): ...

class PremiumUser(User, PremiumMixin): ...
class AdminUser(User, AdminMixin): ...
class AdminPremiumUser(User, PremiumMixin, AdminMixin): ...
```

### Avoid Singletons
Don't use the Singleton pattern. Python **modules** are the idiomatic way to handle shared global state.

```python
# ❌ Bad: Singleton pattern
class DatabaseConnection:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# ✅ Good: Module-level singleton
# database.py
_connection = None

def get_connection():
    global _connection
    if _connection is None:
        _connection = create_connection()
    return _connection
```

---

## Resilience and Error Handling

### The Retry Pattern
Wrap all operations involving **external services, APIs, or LLMs** in retry logic. Use the `tenacity` library.

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_gemini_api(prompt: str) -> str:
    """Call Gemini API with automatic retries on transient failures."""
    response = gemini_client.generate(prompt)
    return response.text
```

### Exponential Backoff
Implement retries with exponential delays to prevent overloading failing services.

- First retry: 2 seconds
- Second retry: 4 seconds (up to 10 seconds max)
- Third retry: 8 seconds (capped at 10 seconds)

### Specific Exceptions
Catch specific errors, not generic exceptions. Provide meaningful feedback.

```python
# ❌ Bad: Too broad
try:
    user = get_user(user_id)
except Exception:
    return {"error": "Something went wrong"}

# ✅ Good: Specific exceptions
try:
    user = get_user(user_id)
except UserNotFoundError:
    raise HTTPException(status_code=404, detail="User not found")
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="Database error")
```

### Fallbacks
Design systems with backup routes or default behaviors when primary calls fail.

```python
def get_exchange_rate(currency: str) -> Decimal:
    """Get exchange rate with fallback to cached value."""
    try:
        return fetch_live_rate(currency)  # Primary
    except APIError:
        logger.warning(f"Could not fetch live rate for {currency}")
        cached_rate = get_cached_rate(currency)
        if cached_rate:
            return cached_rate  # Fallback
        raise RateUnavailableError(currency)
```

---

## Performance and Observability

### Structured Logging
Replace all `print` statements with **logging**. This allows monitoring, integration with Sentry, and better debugging.

```python
import logging

logger = logging.getLogger(__name__)

# ❌ Bad
print("Processing order", order_id)

# ✅ Good
logger.info("Processing order", extra={"order_id": order_id})
logger.error("Failed to process order", extra={"order_id": order_id, "error": str(e)})
```

### Lazy Loading & Generators
Use **generators** (`yield`) for large datasets to stream data row-by-row, keeping memory overhead low.

```python
# ❌ Bad: Loads entire dataset into memory
def get_all_users() -> list[User]:
    return db.query(User).all()  # All 1M users in memory!

# ✅ Good: Stream results
def get_all_users() -> Generator[User, None, None]:
    for user in db.query(User).yield_per(1000):
        yield user

# Usage
for user in get_all_users():
    process_user(user)
```

### Strategic Caching
Use `functools.cache` for expensive computations. Implement **TTL (Time-To-Live) caches** for data that changes over time.

```python
from functools import lru_cache
from cachetools import TTLCache
import time

# Fixed cache for pure functions
@lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# TTL cache for data that expires
exchange_rate_cache = TTLCache(maxsize=100, ttl=3600)  # 1 hour

def get_exchange_rate(currency: str) -> Decimal:
    if currency in exchange_rate_cache:
        return exchange_rate_cache[currency]
    rate = fetch_rate(currency)
    exchange_rate_cache[currency] = rate
    return rate
```

### Health Checks
Include a **`/health`** endpoint in all services for infrastructure monitoring (Kubernetes, load balancers, etc.).

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health_check() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "healthy"}

@app.get("/health/detailed")
def detailed_health() -> dict[str, Any]:
    """Detailed health check with dependency status."""
    return {
        "status": "healthy",
        "database": "connected",
        "cache": "connected",
        "api_latency_ms": 12
    }
```

---

## Testing Standards

### Isolated Environments
Use **in-memory databases** (like SQLite) for testing. Never touch production data.

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

@pytest.fixture
def test_db():
    """In-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(bind=engine)

def test_create_user(test_db: Session):
    user = create_user(test_db, "alice@example.com")
    assert user.email == "alice@example.com"
    # Data only exists in memory, automatically cleaned up
```

### Coverage Goals
Aim for **80%+ test coverage**. Ensure success paths, invalid inputs, and edge cases are all tested.

```bash
pytest --cov=src --cov-report=term-missing
```

### Mocking
Always mock external dependencies to ensure tests are fast and reliable.

```python
from unittest.mock import patch, MagicMock

@patch("myapp.services.call_gemini_api")
def test_generate_summary(mock_gemini):
    mock_gemini.return_value = "Summary text"
    result = generate_summary("long text")
    assert result == "Summary text"
    mock_gemini.assert_called_once()
```

---

## Development Workflow & Mandatory Tools

Before committing any code, run these tools to ensure compliance:

### 1. Formatting
```bash
black . && isort .
```

### 2. Linting
```bash
ruff check --fix .
```

### 3. Type Checking
```bash
mypy . --no-site-packages
```

### 4. Testing
```bash
pytest
```

### Complete Check Before Commit
```bash
# All at once
black . && isort . && ruff check --fix . && mypy . --no-site-packages && pytest
```

---

## Quick Reference

| Tool | Command | Purpose |
|------|---------|---------|
| Black | `black .` | Code formatting |
| isort | `isort .` | Import sorting |
| Ruff | `ruff check --fix .` | Linting and style |
| Mypy | `mypy . --no-site-packages` | Type checking |
| Pytest | `pytest` | Run tests |
| Coverage | `pytest --cov=src` | Check test coverage |

---

## See Also

- **AGENTS.md** - Agent-specific workflows and git conventions
- **ARCHITECTURE.md** - System architecture and design decisions
- **CONTRIBUTING.md** - Contribution guidelines
- **PLUGIN_DEVELOPMENT.md** - Plugin development guide
