# Python Patterns & Standards

Team Python patterns referenced during Research and Implementation phases.

---

## Architecture Patterns

### Layered Architecture

```
app/
├── api/endpoint/         # FastAPI route handlers
├── config/settings.py    # Pydantic-based configuration
├── log/                  # Logging configuration
├── model/
│   ├── model.py          # Domain models & enums
│   ├── requests/         # API request models
│   └── responses/        # API response models
├── repository/
│   └── query/            # SQL queries by domain
├── service/              # Business logic
├── utils/                # Shared utilities
└── main.py               # App initialization & lifespan
```

**Flow:** API Endpoint → Service → Repository → Database

### Dependency Injection

Use FastAPI's `Depends()` with lifespan-managed singletons:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await asyncpg.create_pool(dsn=settings.db_url)
    repository = TaskRepository(pool)
    service = TaskService(repository, settings)
    yield {"task_service": service, "settings": settings}
    await pool.close()

def get_task_service(request: Request) -> TaskService:
    return request.state.task_service

@router.post("/tasks")
async def create_task(service: TaskService = Depends(get_task_service)):
    return await service.create_task(...)
```

**Rules:** Functions receive ALL deps as parameters. No globals, no internal instantiation. Singletons in lifespan, accessed via request.state.

### Service Layer

```python
class UserService:
    def __init__(self, repository: UserRepository, settings: Settings):
        self.repository = repository
        self.settings = settings

    async def get_status(self, request: StatusRequest) -> StatusResponse:
        items = await self.repository.get_items(request.filters)
        return StatusResponse(items=items, total=len(items))
```

### Repository

```python
class TaskRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_by_id(self, task_id: UUID) -> Task | None:
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(QUERY_GET_TASK, task_id)
            return Task.model_validate(dict(record)) if record else None
```

---

## Pydantic Patterns

### Model Organization

| Type | Location | Purpose |
|------|----------|---------|
| Domain | `model/model.py` | Core entities, enums |
| Request | `model/requests/` | API input validation |
| Response | `model/responses/` | API output serialization |
| Config | `config/settings.py` | Environment & secrets |

### Computed Fields

```python
class BulbStatus(BaseModel):
    allocated_bars: int
    total_bars: int

    @computed_field
    @property
    def is_complete(self) -> bool:
        return self.allocated_bars >= self.total_bars
```

### Field Validators

```python
class OrderItem(BaseModel):
    sort: str = "asc"

    @field_validator("sort", mode="before")
    @classmethod
    def normalize_sort(cls, v: Any) -> str:
        return v.lower() if isinstance(v, str) else v
```

### Factory Methods

```python
class Task(BaseModel):
    id: UUID
    status: str

    @classmethod
    def from_db_record(cls, record: Record) -> "Task":
        return cls.model_validate(dict(record))
```

### Settings with Secrets

```python
class PGSQLSettings(BaseSettings):
    db_password: SecretStr = Field(alias="pgsql_password")

    @computed_field
    @property
    def db_url(self) -> str:
        password = quote_plus(self.db_password.get_secret_value())
        return f"postgresql://{self.db_user}:{password}@{self.db_host}/{self.db_name}"

    @classmethod
    def from_aws_secret(cls, secret: dict) -> "PGSQLSettings":
        return cls(pgsql_password=SecretStr(secret["password"]))
```

---

## Database Patterns

### Connection Pool

```python
pool = await asyncpg.create_pool(
    dsn=settings.db_url,
    min_size=3, max_size=10,
    max_inactive_connection_lifetime=600,
)
```

### Query Organization

```
repository/query/
├── bulb/bulb_query.py
├── production/production_query.py
└── shared_query.py
```

### Parameterized Queries (asyncpg: $1, $2...)

```python
records = await conn.fetch(
    "SELECT * FROM tasks WHERE status = $1 AND date > $2",
    "active", datetime(2024, 1, 1)
)
```

### CTEs

```python
QUERY = """
WITH aggregated AS (
    SELECT id, SUM(qty) as total
    FROM items GROUP BY id
)
SELECT * FROM aggregated WHERE total > $1
"""
```

### PostgreSQL Conventions

| Area | Guideline |
|------|-----------|
| Naming | snake_case, plural tables |
| PK | BIGSERIAL, `<table>_id` |
| Timestamps | `created_at`, `updated_at` (TIMESTAMPTZ) |
| Constraints | NOT NULL, UNIQUE, FK in DB |
| Indexing | Index query patterns, not every column |

---

## Error Handling

```python
class ServiceError(Exception):
    """Base for service errors."""

class ValidationError(ServiceError):
    """Input validation failed."""

class NotFoundError(ServiceError):
    """Resource not found."""

async def get_item(item_id: UUID, service: Service = Depends(get_service)):
    try:
        return await service.get_item(item_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Item not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Logging

```python
from pyinnovation.utils.logging_utils import get_logger
logger = get_logger(name="my_service", log_level=settings.log_level)

logger.info(f"Task {task_id}: Processing started")
logger.error(f"Task {task_id}: Failed", exc_info=True)
```

Structured JSON for CloudWatch. Correlation ID via `X-Request-ID`. Filter health checks. DEBUG for dev, INFO for prod.

---

## Testing

Stack: `pytest` + `pytest-asyncio`, `pytest-mock`, `pytest-cov`. Coverage: 70-80%.

```python
@pytest.fixture
def mock_repository() -> MagicMock:
    repo = MagicMock(spec=TaskRepository)
    repo.get_by_id = AsyncMock()
    return repo

@pytest.fixture
def service(mock_repository, settings) -> TaskService:
    return TaskService(repository=mock_repository, settings=settings)

def test_pagination_validation():
    with pytest.raises(ValidationError):
        Pagination(page_size=0)

def test_create_task(client, mock_service):
    app.dependency_overrides[get_service] = lambda: mock_service
    mock_service.create_task = AsyncMock(return_value=TaskResponse(id=uuid4()))
    response = client.post("/tasks", json={"name": "test"})
    assert response.status_code == 201
    mock_service.create_task.assert_called_once()
    app.dependency_overrides.clear()
```

---

## Git & Versioning

| Branch | Purpose |
|--------|---------|
| `main` | Production |
| `staging` | UAT/pre-prod |
| `dev` | Daily development |
| `feat/<JIRA>-desc` | Features |
| `fix/<JIRA>-desc` | Bug fixes |

Prefixes: `feat:`, `fix:`, `docs:`, `chore:`, `bump:`. Squash commits. PR + review to `main`.

---

## Code Quality

```makefile
make setup-dev-env    # Install dev tools + pre-commit
make test             # Run pytest
make lint             # Run ruff
make requirements.txt # Compile dependencies
```

```yaml
repos:
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/commitizen-tools/commitizen
    hooks:
      - id: commitizen
        stages: [commit-msg]
```

---

## Performance Patterns

### DataFrame: Never iterrows()

`iterrows()` is O(n) with Python-speed per-row overhead. Always prefer vectorized operations.

| Instead of | Use |
|------------|-----|
| `for _, row in df.iterrows()` | Vectorized: `df["col"] = df["a"] + df["b"]` |
| Loop to build list of dicts | `df.to_dict("records")` |
| Loop to group and aggregate | `df.groupby("key").agg(...)` |
| Loop with conditional logic | `df.loc[mask]` or `np.where()` |

### Database: Parallelize Independent Queries

Sequential I/O-bound queries to the same DB waste wall-clock time. Use concurrent execution for independent queries.

```python
# WRONG: sequential — total time = sum of all queries
result_a = await repo.get_orders(customer_id)
result_b = await repo.get_invoices(customer_id)
result_c = await repo.get_shipments(customer_id)

# RIGHT: concurrent — total time = max of all queries
result_a, result_b, result_c = await asyncio.gather(
    repo.get_orders(customer_id),
    repo.get_invoices(customer_id),
    repo.get_shipments(customer_id),
)

# RIGHT (sync): ThreadPoolExecutor for blocking DB calls
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=3) as pool:
    futures = {
        pool.submit(repo.get_orders, customer_id): "orders",
        pool.submit(repo.get_invoices, customer_id): "invoices",
        pool.submit(repo.get_shipments, customer_id): "shipments",
    }
    results = {tag: f.result() for f, tag in futures.items()}
```

**When to apply:** 2+ independent queries to the same DB in the same function. Not applicable when query B depends on query A's result.

### Database: JOIN Instead of Fetch-Then-Filter

Two round trips where one SQL statement suffices is a latency and consistency anti-pattern.

```python
# WRONG: fetch IDs, then fetch by IDs — 2 round trips
order_ids = await conn.fetch("SELECT order_id FROM orders WHERE status = $1", "open")
ids = [r["order_id"] for r in order_ids]
items = await conn.fetch(f"SELECT * FROM items WHERE order_id = ANY($1)", ids)

# RIGHT: single query with JOIN
items = await conn.fetch("""
    SELECT i.*
    FROM items i
    JOIN orders o ON o.order_id = i.order_id
    WHERE o.status = $1
""", "open")

# RIGHT: single query with IN (subquery)
items = await conn.fetch("""
    SELECT * FROM items
    WHERE order_id IN (SELECT order_id FROM orders WHERE status = $1)
""", "open")
```

**When to apply:** Pattern "query 1 for IDs → query 2 with WHERE IN (IDs)". Exceptions: when the intermediate result is needed for other logic, or when the ID set must be logged/cached.

---

## Quick Reference

| Need | Do This |
|------|---------|
| Type hint | `list[str]`, `dict[str, int]`, `str \| None` |
| Data class | Pydantic `BaseModel` |
| Settings | Pydantic `BaseSettings` |
| Dependency | Pass as parameter, `Depends()` |
| Side effect | Isolate, make explicit |
| Long function | Split (max 50-70 lines) |
| DataFrame input | `.copy()` first |

## What NOT to Do

| Anti-Pattern | Instead |
|--------------|---------|
| `from typing import List, Dict` | Built-in `list`, `dict` |
| Global state / singletons | Lifespan + DI |
| Catch-all `except Exception` | Specific exceptions |
| Raw dicts for structured data | Pydantic models |
| Hardcoded values | `BaseSettings` |
| 100+ line functions | Split |
| Comments for obvious code | Delete |
| Over-engineering | Solve current problem only |
| Modify input DataFrames | `df.copy()` first |
| `df.iterrows()` | Vectorized ops, `to_dict("records")`, `groupby` |
| Sequential independent DB queries | `asyncio.gather()` or `ThreadPoolExecutor` |
| Fetch IDs → WHERE IN (IDs) | JOIN or IN (subquery) in one query |
