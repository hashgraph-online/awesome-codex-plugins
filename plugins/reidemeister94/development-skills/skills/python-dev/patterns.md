# Python Patterns & Standards

Team Python standards. Read during Phase 1 (Research) and referenced during Phase 3 (Implement).

Two layers: **Principles** (durable WHY — read first, internalize) and **Tactics** (concrete patterns — apply directly).

---

## Principles

### 1. Critical thinking — the meta-rule

When a reviewer, a paper, a "best-practice" article, or another agent prescribes a change, validate against THIS codebase and THIS task before acting. Does the claim match what the code does? Is the fix worse than the disease? Does the codebase already document a reason for the current state (comments, chronicles, memory entries)? "Best practice" without a why-for-here is cargo cult.

User confirmation validates the decision to proceed; the analysis stays your responsibility.

### 2. Simplicity & deletion bias

- **Default to deletion.** Dead code, archaeological comments ("changed to X to be consistent with Y"), empty subclasses, unused settings, commented-out blocks — git remembers them.
- **One source of truth.** When a fact lives in N places, drift is inevitable. Schema names belong in one Enum property, not five hardcoded literals.
- **Three similar lines beat a premature abstraction.** Don't introduce a helper / class / generic until the second or third caller demonstrably needs it.
- **Don't preserve "for later" without a date.** Commented-out experiments rot; if you must keep one, add a TODO with a removal date and a ticket reference.

### 3. Architecture: depth, seams, types as contract

- **Deletion test (Ousterhout).** For any module that looks shallow (interface complexity ≈ implementation complexity), imagine deleting it. If complexity reappears across callers, the module earned its keep — deepen it. If it disappears, the module was a pass-through; inline it.
- **One adapter = hypothetical, two = real (Feathers).** Don't introduce a seam until something genuinely varies across it. An interface with one implementation, no mock/alt-impl, and no roadmap for a second is speculation, not leverage.
- **Phantom polymorphism is recognizable.** Empty subclasses that exist only to give a construction site a distinct name fail the deletion test cleanly. Collapse to parameterization or capability flags.
- **The type system is the contract.** When two concepts exist (a DB row vs an enriched response), make them two types. A class hierarchy is more readable, safer, and harder to drift than a marker dict, a sidecar allowlist, or a `json_schema_extra` flag.

### 4. Defaults & information hygiene

- **Default-on-safe.** When the asymmetry is "right by default = harmless, wrong by default = production crash or security leak," invert the default. Opt-in beats opt-out for risky behavior.
- **Fail at boot, not at first request.** Validate config presence and shape during FastAPI lifespan. Expensive resolution (Secrets Manager fetch, network probes) can defer to first use — but a process that boots green and 500s every request will pass readiness probes and replace healthy tasks.
- **Never leak `str(e)` to clients.** Internal exception messages are OWASP A04 Information Disclosure. Log the full traceback; return sanitized `{"detail": "Internal server error"}`.
- **`json_schema_extra` is for OpenAPI examples only.** Do NOT stash internal flags there — they leak into the public schema. Use class inheritance, `Annotated[..., Marker]`, or a typed registry instead.

### 5. Async, FastAPI, exception handling

- **One global `Exception` handler in `create_app`.** Per-endpoint `try / except Exception → HTTPException(500, f"...{str(e)}")` is triple-wrong: duplication, information leakage, and double-logging (Starlette already converts unhandled exceptions). Register one handler; let endpoints raise straight.
- **`except BaseException` is a trap in async code.** `asyncio.CancelledError` inherits from `BaseException` since Python 3.8. `except Exception` does not catch it, but `except BaseException` (or bare `except:`) does. Swallowing it breaks structured concurrency.
- **Middleware order is LIFO and load-bearing.** The last `add_middleware` call wraps closest to the ASGI root → runs FIRST on the inbound path. Pin the order in a test so future reordering breaks loudly.
- **`@lru_cache(maxsize=1)` on `get_settings()`.** Canonical FastAPI pattern; lets tests override via `app.dependency_overrides`. Call `get_settings.cache_clear()` when tests mutate env between imports.
- **`TestClient(raise_server_exceptions=False)` for tests that exercise the global handler.** With `True` (default), TestClient re-raises unhandled exceptions to the test side even when handlers caught them — you would be testing the debug aid, not production.

### 6. External SDKs — adapter at lifespan

- **Construct heavy clients once.** boto3 clients incur metaprogramming cost on every `client(...)` call and are not thread-safe to construct concurrently. Build once at lifespan; inject into services.
- **Wrap blocking SDK calls in `asyncio.to_thread` at the adapter layer.** Services stay async-clean. Tests mock the adapter, not the SDK.
- **The adapter is a real seam.** Hides the SDK shape, owns the lifecycle, gives you one place to add retries, timeouts, or instrumentation.

### 7. Pydantic — models as contract

- **Use inheritance to split concerns.** If a response model carries both DB-mapped fields and computed / Python-only fields, declare a `*DbRow` base with the columns and have the response subclass add the enrichment + `@computed_field` properties. The hierarchy IS the contract.
- **Pass the DB-row class — not the enriched subclass — to query builders and aggregation utilities.** A computed field literally cannot end up in SQL.
- **`@computed_field` for read-only derived properties; `Field(default=...)` for service-populated values.**
- **Separate request models from response models; never merge.**

### 8. Comments

- **WHY, not WHAT.** Identifiers and structure explain WHAT. Comments explain why the code looks unusual: a hidden constraint, a workaround for an upstream bug, an invariant that isn't obvious from the call sites.
- **Delete archaeological comments.** "Changed to 400 to be consistent with X", "no longer needed here", "note: this used to be Y" — that's PR-description material and rots into noise.
- **Scale the WHY to the flow's intricacy.** Trivial code earns no comment; an obscure or tangled flow earns a fuller WHY — a few lines spelling out the reasoning is right when the logic genuinely demands it. Cap multi-paragraph rationale: link out (`see chronicle 00xx`, `see docs/...`) past a short block.

### 9. Tests mirror production

- **Test the behavior, not the leak.** If a test asserts a leaked-string error payload, the test is part of the bug. Fix both.
- **Repository tests assert what the repository contractually does**, not what callers historically did with its errors. If you change the contract (a repository now raises a domain error instead of `HTTPException`), update tests in the same commit.
- **Test tiers earn their keep only if they catch distinct bug shapes.** Snapshot tests mocked at the service layer are the weakest — convert to integration assertions where the cost is similar.

### 10. Maximize simplicity *while keeping all features*

When you remove a wrapper, an abstraction, an indirection, validate that no behavior is silently lost.

1. **List the responsibilities** of the thing being removed (logging context? error translation? observability span attrs?).
2. **For each, ask: is it covered elsewhere by infrastructure** you can rely on (FastAPI's exception layer, the observability platform's request span, Starlette's `ServerErrorMiddleware`)?
3. **If yes, delete with confidence.** If no, move the unique responsibility to the right infrastructure layer BEFORE deleting.

---

## Architecture

### Layered

```
app/
├── api/                     # FastAPI routers, by domain
├── config/settings.py       # Pydantic BaseSettings hierarchy
├── log/                     # Logging config builder
├── model/                   # Pydantic models, domain-driven
│   ├── common/              # cross-cutting types (enums, base classes)
│   ├── order/               # one subpackage per domain
│   │   ├── models.py
│   │   ├── requests.py
│   │   └── responses.py
│   └── ...
├── repository/              # asyncpg + query builders
│   └── query/               # SQL strings, organized by domain
├── service/                 # business logic
├── utils/                   # shared utilities, adapters
├── exception_handlers.py    # all FastAPI exception handlers
├── middleware.py            # middleware stack wiring, order pinned
├── lifespan.py              # async resource manager
└── main.py                  # slim entrypoint: create_app() + module-scope app
```

Flow: **API → Service → Repository → asyncpg → PostgreSQL**.

### Lifespan-managed singletons

```python
settings = get_settings()  # module-scope; lifespan closes over it


@asynccontextmanager
async def lifespan(app: FastAPI):
    rt = RuntimeResources()  # pre-bind so 'finally' can drain on partial init failure
    try:
        rt = await _initialise_runtime(app, settings)
        yield rt.services  # TypedDict accessible via request.state
    except asyncio.CancelledError:
        logger.info("Shutdown signal received")
        raise  # preserve structured concurrency
    except Exception:
        logger.error("Resource init failed", exc_info=True)
        raise
    finally:
        await _teardown_runtime(rt)
```

`RuntimeResources` is a dataclass with `slots=True`; every field is `None`-able so partial init failures still drain gracefully through `_teardown_runtime`. The pre-bind on the first line of `lifespan` matters: if `_initialise_runtime` raises before rebinding `rt`, the `finally` block still sees a valid (all-`None`) `RuntimeResources` and exits cleanly.

### Dependency injection — `Depends()` + `request.state` TypedDict

```python
class RuntimeServices(TypedDict):
    order_service: OrderService
    settings: Settings


def get_order_service(request: Request) -> OrderService:
    return _get_state(request, "order_service")


@router.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(
    payload: CreateOrderRequest,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    return await service.create(payload)
```

**Rules:**
- Functions receive all dependencies as parameters. No globals. No internal instantiation.
- Singletons constructed in `lifespan`, accessed via `request.state` keyed by a TypedDict.
- The TypedDict documents the contract — missing keys raise an explicit `RuntimeError` at the accessor, not a sanitized 500 mid-request.

### State sentinel

```python
_MISSING = object()


def _get_state(request: Request, key: str) -> Any:
    value = getattr(request.state, key, _MISSING)
    if value is _MISSING:
        raise RuntimeError(f"lifespan never attached '{key}' to request.state")
    return value
```

A sentinel distinguishes "key never attached" from "key attached to `None`". Lets legitimate `None` values through without a false-positive `AttributeError`, and surfaces the specific missing key in logs.

### App factory + module-scope singleton

```python
def create_app() -> FastAPI:
    settings = get_settings()
    observability_client = get_observability_client()
    app = FastAPI(
        lifespan=lifespan,
        docs_url=f"{settings.api_prefix}/docs",
        openapi_url=f"{settings.api_prefix}/openapi.json",
    )
    wire_middleware_stack(app)
    register_exception_handlers(app)
    app.include_router(build_api_router(settings))
    # Instrumentation that monkey-patches must run before the first ASGI scope.
    instrument_fastapi(observability_client, app, settings.api_prefix)
    return app


app = create_app()  # module-scope; gunicorn workers re-import post-fork
```

The router is built dynamically at call time (not at import) so settings mutations between imports are observed (`get_settings.cache_clear()` then re-call).

---

## Pydantic models

### Domain-driven layout

`app/model/<domain>/{models.py, requests.py, responses.py}`. Cross-cutting types in `app/model/common/`. `__init__.py` re-exports for a clean public API.

### DB-row vs response — split by inheritance

```python
class OrderDbRow(BaseModel):
    order_id: str
    customer_id: str
    status: str
    created_at: datetime
    quantity: int = 0  # SQL COALESCEs nullable counts to 0


class OrderModel(OrderDbRow):
    # service-populated enrichment
    breakdown: BreakdownResult | None = Field(default=None)

    @computed_field
    @property
    def is_complete(self) -> bool:
        return self.status == "shipped"
```

- Query builder and aggregation utilities walk `OrderDbRow.model_fields` — computed fields and service-populated fields cannot accidentally end up in `SELECT`.
- Service layer returns `OrderModel`; the endpoint's `response_model` references `OrderModel`.
- A new column added to `OrderDbRow` automatically flows into filter / order validation. A new Python-only field on the subclass is structurally barred from SQL.

### Request and response — never merge

Naming convention:
- `*Request` — API input model (path/query/body).
- `*DbRow` — DB-shape contract (one row, exact `SELECT` columns).
- `*Model` — domain shape, often `class FooModel(FooDbRow)` adding service-populated fields + `@computed_field` properties. For single-resource endpoints, `*Model` IS the `response_model`.
- `*Response` — API output envelope when wrapping a list, pagination, or aggregate metadata (`OrderListResponse` holding `items: list[OrderModel]` + `total: int`).

Never reuse a `*Request` as a `*Response` or vice versa.

### Validators and computed fields

```python
class OrderItem(BaseModel):
    sort: str = "asc"

    @field_validator("sort", mode="before")
    @classmethod
    def normalize_sort(cls, v: Any) -> str:
        return v.lower() if isinstance(v, str) else v


class Allocation(BaseModel):
    allocated: int
    total: int

    @computed_field
    @property
    def is_fulfilled(self) -> bool:
        return self.allocated >= self.total
```

`@field_validator` runs on assignment; `@computed_field` is a read-only derived property (serialized in `model_dump`, surfaces in OpenAPI). Service-populated values use `Field(default=...)`, not `@computed_field`.

### Factory methods

```python
class Order(BaseModel):
    order_id: str
    status: str

    @classmethod
    def from_db_record(cls, record: Record) -> "Order":
        return cls.model_validate(dict(record))
```

Repositories return typed models. A schema rename surfaces as a Pydantic `ValidationError` at the repository seam — not as a `KeyError` deep in the service layer.

### Settings — `BaseSettings`, secrets, nested layout

```python
class PGSQLSettings(BaseSettings):
    pgsql_host: str = Field(default="localhost")
    pgsql_port: int = Field(default=5432)
    pgsql_user: str
    pgsql_password: SecretStr
    pgsql_name: str

    @computed_field
    @property
    def db_url(self) -> str:
        pwd = quote_plus(self.pgsql_password.get_secret_value())
        return f"postgresql://{self.pgsql_user}:{pwd}@{self.pgsql_host}:{self.pgsql_port}/{self.pgsql_name}"

    @classmethod
    def from_aws_secret(cls, secret: dict) -> "PGSQLSettings":
        return cls(
            pgsql_host=secret["host"],
            pgsql_port=int(secret["port"]),
            pgsql_user=secret["username"],
            pgsql_password=SecretStr(secret["password"]),
            pgsql_name=secret["dbname"],
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```

- `SecretStr` for sensitive values — never logged, never serialized by default.
- Compute `db_url` lazily via `@computed_field`.
- AWS Secrets Manager loading isolated to a classmethod `from_aws_secret`.
- `@lru_cache(maxsize=1)` so `Settings()` is constructed once; call `cache_clear()` in tests that mutate env vars between imports.

### `json_schema_extra` — examples only

ALLOWED:

```python
class CreateOrderRequest(BaseModel):
    order_id: str
    quantity: int

    model_config = {
        "json_schema_extra": {
            "examples": [{"order_id": "AB-001", "quantity": 5}],
        },
    }
```

FORBIDDEN:
- `json_schema_extra={"db_column": False}` and similar internal markers — they leak into the public OpenAPI schema (OWASP A04 information disclosure).
- Any non-example flag. If the field is in the model, the field is in the schema; if you don't want it in the schema, don't put it in the model.

---

## Database (asyncpg)

### Connection pool

```python
pool = await asyncpg.create_pool(
    dsn=settings.db_url,
    min_size=3,
    max_size=10,
    max_inactive_connection_lifetime=600,
)
```

Built once in `lifespan`, cleaned up in `finally`.

### Parameterized queries — never f-string interpolation of user input

```python
records = await conn.fetch(
    "SELECT * FROM orders WHERE status = $1 AND created_at > $2",
    "open", datetime(2026, 1, 1),
)
```

Schema names that vary per request (e.g., one of two known schemas resolved from an Enum) use `.format(schema=...)` against the Enum-provided value — never user input. Use `$N` placeholders for everything else.

### Repository returns typed models, not records

```python
class OrderRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_by_id(self, order_id: str) -> OrderModel | None:
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(QUERY_GET_ORDER_BY_ID, order_id)
        return OrderModel.from_db_record(record) if record else None
```

A schema rename on `orders` surfaces as `ValidationError` at this seam, not as a `KeyError` deeper in the service.

### Query organization

```
repository/query/
├── order/order_query.py
├── customer/customer_query.py
└── shared_query.py
```

Queries are module-level constants. Schema substitution uses `.format()` against an Enum-provided value.

### Parallelize independent queries

```python
# Sequential — total = sum of all queries
orders = await repo.get_orders(customer_id)
invoices = await repo.get_invoices(customer_id)
shipments = await repo.get_shipments(customer_id)

# Concurrent — total = max of all queries
orders, invoices, shipments = await asyncio.gather(
    repo.get_orders(customer_id),
    repo.get_invoices(customer_id),
    repo.get_shipments(customer_id),
)
```

Applies when two or more independent queries hit the same DB in the same function. Not applicable when query B depends on query A's result.

### JOIN over fetch-then-filter

```python
# Anti-pattern — two round trips
order_rows = await conn.fetch("SELECT order_id FROM orders WHERE status = $1", "open")
ids = [r["order_id"] for r in order_rows]
items = await conn.fetch("SELECT * FROM items WHERE order_id = ANY($1)", ids)

# Correct — single query
items = await conn.fetch(
    """
    SELECT i.*
    FROM items i
    JOIN orders o ON o.order_id = i.order_id
    WHERE o.status = $1
    """,
    "open",
)
```

Exception: when the intermediate result is needed for other logic, or must be logged / cached.

### Transactions

`async with conn.transaction():` for multi-statement units of work. Single-statement reads do not need an explicit transaction (asyncpg manages it).

### PostgreSQL conventions

| Area | Rule |
|---|---|
| Naming | snake_case, plural tables |
| PK | `BIGSERIAL`, named `<table>_id` |
| Timestamps | `created_at`, `updated_at` as `TIMESTAMPTZ` |
| Constraints | `NOT NULL`, `UNIQUE`, `FK` enforced in DB, not just app |
| Indexing | Index actual query patterns; don't shotgun |

---

## Async, FastAPI, exception handling

### One global handler + domain hierarchy

```python
# app/service/errors.py
class ServiceError(Exception):
    """Base for service errors."""


class NotFoundError(ServiceError):
    """Resource not found."""


class InvalidFilterError(ServiceError):
    def __init__(self, field_name: str, message: str):
        super().__init__(message)
        self.field_name = field_name


class ProcedureAlreadyRunningError(ServiceError):
    """Procedure already in progress for this key."""


# app/exception_handlers.py
def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Resource not found"})

    @app.exception_handler(InvalidFilterError)
    async def _invalid_filter(_: Request, exc: InvalidFilterError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": f"Invalid filter value for field '{exc.field_name}'"},
        )

    @app.exception_handler(ProcedureAlreadyRunningError)
    async def _already_running(_: Request, exc: ProcedureAlreadyRunningError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": "Procedure already running"})

    @app.exception_handler(Exception)
    async def _catch_all(_: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception", exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```

**Rules:**
- Domain errors raised straight from service / repository — never wrapped in `HTTPException`.
- Handler `detail` strings are hardcoded — never `str(exc)` (information disclosure).
- One catch-all `Exception` handler returns sanitized 500 + logs the full traceback.
- No per-endpoint `try / except → HTTPException`.

### `CancelledError` re-raise

```python
try:
    await long_running_work()
except asyncio.CancelledError:
    logger.info("Shutdown signal received")
    raise  # preserve structured concurrency
except Exception as e:
    logger.error(f"Worker failed: {e}", exc_info=True)
    raise
```

`asyncio.CancelledError` inherits from `BaseException`. `except Exception` does not catch it (correct). `except BaseException` (or bare `except:`) does and breaks graceful shutdown — avoid.

### Middleware order — LIFO, pinned by test

The last `add_middleware` call wraps the ASGI root → runs FIRST on inbound. Declare the order in one list and add in reverse:

```python
MIDDLEWARE_STACK_OUTER_TO_INNER: list[tuple[type, dict]] = [
    (CorrelationIdMiddleware, {"header_name": "X-Request-ID"}),
    (GZipMiddleware, {"minimum_size": 1024}),
    (CORSMiddleware, {"allow_origins": ["*"], "allow_methods": ["*"], "allow_headers": ["*"]}),
    (AuthMiddleware, {}),
]


def wire_middleware_stack(app: FastAPI) -> None:
    for cls, kwargs in reversed(MIDDLEWARE_STACK_OUTER_TO_INNER):
        app.add_middleware(cls, **kwargs)
```

Lock with a unit test that compares `app.user_middleware` against the declared list.

### Background tasks — bounded queue + worker pool

```python
queue: asyncio.Queue = asyncio.Queue(maxsize=256)  # backpressure producers


async def worker() -> None:
    while True:
        item = await queue.get()
        try:
            await process(item)
        except Exception as e:
            logger.error(f"worker: {e}", exc_info=True)
        finally:
            queue.task_done()


workers = [asyncio.create_task(worker()) for _ in range(5)]

# at shutdown:
for w in workers:
    w.cancel()
await asyncio.gather(*workers, return_exceptions=True)
```

`maxsize` prevents unbounded growth from a slow downstream. `return_exceptions=True` during shutdown so one worker's exception doesn't block the others from completing cancellation.

### Adapter pattern for heavy SDKs

```python
class ExternalServiceAdapter:
    def __init__(self, client: "ExternalClient"):
        self._client = client  # heavy client constructed once at lifespan

    @classmethod
    async def build(cls, region: str) -> "ExternalServiceAdapter":
        client = await asyncio.to_thread(make_external_client, region_name=region)
        return cls(client)

    async def call(self, payload: dict) -> dict:
        return await asyncio.to_thread(self._client.invoke, payload)
```

- Construct heavy clients once at lifespan (metaprogramming cost, thread-safety constraints).
- Wrap blocking SDK calls in `asyncio.to_thread` so the event loop stays unblocked.
- Services depend on the adapter, never the SDK directly. Tests mock the adapter.

---

## Logging & observability

### Structured JSON logs

```python
# app/log/logging_conf.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "correlation_id": {"()": "asgi_correlation_id.CorrelationIdFilter"},
    },
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(correlation_id)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["correlation_id"],
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
```

X-Request-ID propagated by `asgi-correlation-id` middleware; the `correlation_id` filter attaches it to every log record automatically.

### Logger acquisition

```python
logger = logging.getLogger(__name__)

logger.info("Order %s: processing started", order_id)
logger.error("Order %s: failed", order_id, exc_info=True)
```

Use `%`-style format placeholders, not f-strings — lazy evaluation skips string-building when the log level filters the record out.

### Instrumentation that monkey-patches must run BEFORE first ASGI scope

OpenTelemetry / observability instrumentations that wrap FastAPI typically replace `app.build_middleware_stack`. Starlette calls that method on the FIRST ASGI scope (lifespan startup or first request) and caches the result. Calling `instrument_fastapi(app)` inside `lifespan` patches a method that has already been called — the stack is already built and the instrumentation silently no-ops.

**Rule:** invoke instrumentation in `create_app()`, AFTER `wire_middleware_stack`, BEFORE `return app`. Lock with a test that asserts the instrumentation hook ran at module-import time.

### Health endpoint

A single `GET /health` returning `{"status": "ok"}`. No DB probe — readiness is the ASGI scope being served. Deep probes belong to a separate `/ready` endpoint that hits the pool.

---

## Testing

### Four tiers

| Tier | Directory | Mocks at | Catches |
|---|---|---|---|
| Unit | `tests/` | Service layer (or below) | Logic errors in individual functions |
| Golden / Snapshot | `tests/golden/` | Repository layer | API contract regressions (shape, serialization) |
| E2E Replay | `tests/e2e/` | DB layer (replay fixtures) | Full endpoint regressions without a live DB |
| Integration | `tests/integration/` | Nothing | Full-stack bugs: endpoint → service → repository → SQL |

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
minversion = "7.3"
addopts = "-ra -q -m 'not integration and not e2e'"
testpaths = ["tests"]
asyncio_mode = "auto"
log_cli = true
markers = [
    "golden: snapshot/regression tests at the API contract boundary",
    "integration: requires a real database",
    "e2e: end-to-end replay tests",
]
```

Run commands:

```bash
pytest tests/ -x -q                 # unit + golden (default)
pytest tests/ -x -q -m e2e          # e2e only
pytest tests/ -x -q -m integration  # integration only (requires DB env)
pytest tests/ -x -q -m ''           # everything
```

### `asyncio_mode="auto"` — no decorator on every test

```python
async def test_get_order_by_id(repository: OrderRepository) -> None:
    order = await repository.get_by_id("OR-001")
    assert order is not None
    assert order.order_id == "OR-001"
```

### `TestClient` configuration

```python
@pytest.fixture
def client(app: FastAPI) -> TestClient:
    # raise_server_exceptions=False: mirror production exception path.
    # True (default) re-raises unhandled exceptions even when the global handler caught them.
    return TestClient(app, raise_server_exceptions=False)
```

### Autouse `dependency_overrides` reset

```python
@pytest.fixture(autouse=True)
def _reset_app_dependency_overrides(app: FastAPI):
    yield
    app.dependency_overrides.clear()
```

Tests that set overrides do not have to remember to clean up; the autouse fixture guarantees test isolation.

### Mock with `spec=` for typed seams

```python
@pytest.fixture
def mock_repository() -> MagicMock:
    repo = MagicMock(spec=OrderRepository)
    repo.get_by_id = AsyncMock()
    repo.list = AsyncMock()
    return repo


@pytest.fixture
def mock_service() -> MagicMock:
    svc = MagicMock(spec=OrderService)
    svc.create = AsyncMock()
    svc.get_by_id = AsyncMock()
    return svc


def test_create_order_returns_201(client: TestClient, mock_service: MagicMock):
    app.dependency_overrides[get_order_service] = lambda: mock_service
    mock_service.create.return_value = OrderModel(
        order_id="OR-001",
        customer_id="CU-1",
        status="open",
        created_at=datetime(2026, 1, 1),
        quantity=3,
    )

    response = client.post("/orders", json={"customer_id": "CU-1", "quantity": 3})

    assert response.status_code == 201
    mock_service.create.assert_called_once()
```

`spec=` makes the mock fail loudly when production code calls a method that does not exist on the real class — a rename surfaces at test time.

### Integration tests against a real DB

`tests/integration/conftest.py` builds a real `asyncpg.Pool` against the dev DB; if unreachable, tests `pytest.skip()`. Auth middleware passes through when the auth env vars are not set (observe-only mode in dev). Real repositories + services wired via `app.dependency_overrides`.

---

## Tooling & code quality

### Python version

**Python 3.14.** Built-in generic types (`list[str]`, `dict[str, int]`), PEP 604 unions (`str | None`), `match` statements. No `from __future__ import annotations` — unnecessary on 3.14.

### Ruff (lint + format)

```toml
[tool.ruff]
line-length = 100
```

```bash
ruff check .
ruff format .
```

### Dependency management — `uv pip compile`

```
requirements.in        # human-edited, pinned with == X.Y.* patterns
requirements.txt       # generated, fully-resolved lockfile
requirements-dev.in    # dev tooling
requirements-dev.txt   # generated
```

```bash
uv pip compile requirements.in -o requirements.txt --upgrade
uv pip compile requirements-dev.in -o requirements-dev.txt --upgrade
```

Version pin pattern: `==X.Y.*` for libraries with active minor cadence (FastAPI, Pydantic), `==X.*` for tools (ruff, pytest, commitizen). Git dependencies pinned to a tag, not a branch.

### Pre-commit

```yaml
exclude: '.git|.tox|helm/|.ipynb|.csv'
default_stages: [pre-commit]
fail_fast: true

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-toml
      - id: check-yaml
      - id: check-merge-conflict

  - repo: https://github.com/commitizen-tools/commitizen
    rev: v4.9.1
    hooks:
      - id: commitizen
        stages: [commit-msg]

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: 'v0.14.3'
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

`fail_fast: true` — stop on first hook failure (cheap signal beats long logs).

### Versioning — commitizen + conventional commits

```bash
cz bump --increment patch   # or minor / major
```

```toml
[tool.commitizen]
version = "0.0.1"
tag_format = "$version"
version_files = ["VERSION", "pyproject.toml:version", "app/main.py:app_version"]
bump_message = "bump: version $current_version -> $new_version"
update_changelog_on_bump = true
annotated_tag = true
```

Commit prefixes: `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`, `perf`, `ci`, `build`, `bump`.

### Function length

~50-60 lines (soft guide, not a hard cap). Beyond that, the function is usually doing too much — extract a well-named helper (normal name, no underscore prefix unless intentionally private). Cohesion beats line-counting.

---

## Performance

### Generators for large data

```python
# asyncpg server-side cursor — stream rows without materializing the full result set
async def big_rows(pool: Pool) -> AsyncIterator[dict]:
    async with pool.acquire() as conn, conn.transaction():
        async for record in conn.cursor(QUERY):
            yield dict(record)
```

`conn.cursor()` requires an open transaction (asyncpg constraint). Use this when the result set is too large to hold in memory; otherwise `await conn.fetch(...)` is simpler.

### Dict lookups over list scans

```python
# O(n) per lookup
matches = [item for item in items if item.id == target_id]

# O(1) per lookup
by_id = {item.id: item for item in items}
match = by_id.get(target_id)
```

### Pandas — never `iterrows()`

| Anti-pattern | Replacement |
|---|---|
| `for _, row in df.iterrows()` | Vectorized: `df["c"] = df["a"] + df["b"]` |
| Build list of dicts in a loop | `df.to_dict("records")` |
| Manual group & aggregate | `df.groupby("k").agg(...)` |
| Conditional logic in a loop | `df.loc[mask]` or `np.where()` |

### Small data — `list[dict]` beats DataFrame

For under ~10k rows of one-shot processing, `list[dict]` with pure Python is simpler and often faster than spinning up a DataFrame. Reach for pandas / polars only when vectorization, grouping, or numerical kernels pay for themselves.

### DataFrame inputs

Always `.copy()` a DataFrame before mutation. Silent caller mutation is a regression vector.

---

## Quick reference

| Need | Do |
|---|---|
| Type hint | `list[str]`, `dict[str, int]`, `str \| None` |
| Data class | Pydantic `BaseModel` |
| Settings | Pydantic `BaseSettings` + `@lru_cache(maxsize=1)` on `get_settings` |
| Sensitive value | `SecretStr` |
| Async DB | `asyncpg` pool, parameterized queries, repository returns typed models |
| Background work | Bounded `asyncio.Queue` + worker tasks, cancel-on-shutdown |
| Heavy SDK | Adapter class constructed at lifespan, blocking calls in `asyncio.to_thread` |
| Independent queries | `asyncio.gather` |
| Two-step DB read | One JOIN |
| Error in route | Raise domain exception (no `try / except → HTTPException`) |
| Domain to HTTP | One handler per type in `exception_handlers.py`, hardcoded `detail` |
| Test async function | `asyncio_mode="auto"` |
| Test FastAPI client | `TestClient(app, raise_server_exceptions=False)` |
| Mock typed seam | `MagicMock(spec=Class)` + `AsyncMock` for async methods |
| Override dependency in test | `app.dependency_overrides[dep] = ...` + autouse reset fixture |
| Log | `logging.getLogger(__name__)`, `%`-format placeholders, structured JSON |
| Request ID | `asgi-correlation-id` middleware, `correlation_id` log filter |
| Lint / format | `ruff check .` / `ruff format .` (line-length 100) |
| Update deps | edit `*.in`, then `uv pip compile *.in -o *.txt --upgrade` |
| Commit | Conventional commit (`feat:`, `fix:`, ...); `cz bump` for version |

---

## What NOT to do

| Anti-pattern | Correct approach |
|---|---|
| `from typing import List, Dict, Optional` | Built-in `list`, `dict`, `X \| None` |
| Per-endpoint `try / except → HTTPException` | One global handler + domain exception hierarchy |
| `HTTPException(500, str(e))` anywhere | Sanitized `{"detail": "Internal server error"}`; log traceback |
| `except BaseException` | `except asyncio.CancelledError: raise` + `except Exception` |
| `f"SELECT ... WHERE id = {user_input}"` | `"SELECT ... WHERE id = $1"`, `(user_input,)` |
| Repository returns raw `asyncpg.Record` | Repository returns typed Pydantic model (`model_validate`) |
| Settings as module globals | `BaseSettings` + `@lru_cache(maxsize=1)` accessor |
| `SecretStr` value in a log line | Log the field name only; never the value |
| Hardcoded schema / domain literal in N places | Single Enum property as source of truth |
| Empty subclass for "polymorphism" | Parameterize the base; collapse the subclass |
| `json_schema_extra={"internal_flag": True}` | Class inheritance or `Annotated[..., Marker]` |
| Pandas `iterrows()` | Vectorized ops, `to_dict("records")`, `groupby` |
| Sequential independent DB queries | `asyncio.gather` |
| Fetch IDs then `WHERE IN (IDs)` | One JOIN or subquery |
| Mutate input DataFrame | `df.copy()` first |
| `TestClient(app)` without `raise_server_exceptions=False` | Set `False` to mirror production exception path |
| `MagicMock()` without `spec=` | `MagicMock(spec=Class)` — catches renames |
| Forgotten `dependency_overrides.clear()` | Autouse fixture clears between tests |
| Instrumentation `instrument_fastapi(app)` in `lifespan` | Call in `create_app` AFTER middleware wiring |
| `import` inside a function / method | All imports at module top |
| Comment that restates the next line | Delete it |
| Archaeological comment ("changed to X to be consistent...") | Delete; the diff is the history |
