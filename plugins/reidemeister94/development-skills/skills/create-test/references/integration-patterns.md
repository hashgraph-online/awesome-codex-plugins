# Integration Patterns Reference — Real Database Testing

## PostgreSQL Test Isolation Strategies

### Strategy 1: Transaction Rollback (Default — Use This First)

Wrap each test in a transaction that rolls back automatically. Sub-millisecond cleanup, hundreds of tests in milliseconds.

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

@pytest.fixture(scope="session")
def db_engine(postgres_container):
    """One engine per test session — shares the connection pool."""
    url = postgres_container.get_connection_url()
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Each test gets a session wrapped in a transaction that rolls back."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
```

**Limitation:** Cannot test code that issues explicit COMMIT. Use Template DB for those cases.

### Strategy 2: TRUNCATE CASCADE (When Code Commits)

```python
@pytest.fixture(scope="function")
def db_session(db_engine):
    """Clean state via TRUNCATE — works even when code under test commits."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()
    # Cleanup: truncate all tables in reverse FK order
    with db_engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))
        conn.commit()
```

### Strategy 3: Template DB + tmpfs (Full Isolation, ~87ms/clone)

```bash
# Docker with tmpfs — 23x faster than disk
docker run -p 5435:5432 --tmpfs /var/lib/pg/data \
  -e PGDATA=/var/lib/pg/data -e POSTGRES_PASSWORD=postgres postgres:16-alpine
```

```python
# Create template once, clone per test
@pytest.fixture(scope="session")
def template_db(postgres_container):
    """Apply migrations to the container's default database, used as template."""
    url = postgres_container.get_connection_url()  # connects to "testdb"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    # Seed reference data if needed
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO ref_table ..."))
        conn.commit()
    engine.dispose()
    return url

@pytest.fixture(scope="function")
def test_db(template_db, postgres_container):
    """Clone the template database for each test — full isolation."""
    import uuid
    db_name = f"test_{uuid.uuid4().hex[:8]}"
    template_name = template_db.rsplit("/", 1)[1]  # "testdb"
    admin_url = template_db.rsplit("/", 1)[0] + "/postgres"
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE {db_name} TEMPLATE {template_name}"))
    yield template_db.rsplit("/", 1)[0] + f"/{db_name}"
    with admin_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE {db_name}"))
    admin_engine.dispose()
```

### Strategy Decision

```
Does your code under test issue explicit COMMIT?
├── No → Transaction Rollback (fastest)
└── Yes → ↓
    Does the test need DDL changes (ALTER TABLE, CREATE INDEX)?
    ├── No → TRUNCATE CASCADE
    └── Yes → Template DB clone (~87ms/test)
```

---

## Testcontainers Setup

### Session-Scoped Container (Recommended Default)

```python
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL once for the entire test session."""
    with PostgresContainer(
        image="postgres:16-alpine",
        username="test",
        password="test",
        dbname="testdb",
    ) as postgres:
        yield postgres
    # Container auto-destroyed on exit

@pytest.fixture(scope="session")
def db_url(postgres_container):
    """Dynamic connection URL — never hardcode ports."""
    return postgres_container.get_connection_url()
```

**Rules:**
- Never hardcode ports — use `get_connection_url()` / `get_exposed_port()`
- Use `postgres:16-alpine` for minimal startup overhead
- Session scope for container, function scope for test isolation
- For pytest-xdist parallel workers: each worker gets its own container

### asyncpg Variant (FastAPI / async projects)

```python
import asyncio
import pytest
import asyncpg

# In pyproject.toml: [tool.pytest.ini_options] asyncio_mode = "auto"

@pytest.fixture(scope="session", loop_scope="session")
async def db_pool(postgres_container):
    host = postgres_container.get_container_host_ip()
    port = postgres_container.get_exposed_port(5432)
    pool = await asyncpg.create_pool(
        host=host, port=port,
        user="test", password="test", database="testdb",
        min_size=2, max_size=5,
    )
    # Run migrations
    async with pool.acquire() as conn:
        await conn.execute(open("schema.sql").read())
    yield pool
    await pool.close()

@pytest.fixture(scope="function", loop_scope="session")
async def db_conn(db_pool):
    """Per-test connection with transaction rollback."""
    conn = await db_pool.acquire()
    tx = conn.transaction()
    await tx.start()
    yield conn
    await tx.rollback()
    await db_pool.release(conn)
```

### Safety Guard (Protect Against Accidental Production Writes)

```python
@pytest.fixture(autouse=True)
def _guard_database_name(db_url):
    """Fail fast if somehow connected to a non-test database."""
    assert "test" in db_url.lower() or "localhost" in db_url.lower(), \
        f"SAFETY: Refusing to run tests against non-test database: {db_url}"
```

### pytest-xdist Worker-Scoped Containers

When running tests in parallel with `pytest-xdist`, each worker needs its own container to avoid port conflicts:

```python
@pytest.fixture(scope="session")
def postgres_container(worker_id):
    """Each xdist worker gets its own PostgreSQL container."""
    if worker_id == "master":
        # Not running with xdist — single container
        with PostgresContainer("postgres:16-alpine") as pg:
            yield pg
    else:
        # xdist worker — unique container per worker
        with PostgresContainer("postgres:16-alpine") as pg:
            yield pg
```

Run with: `pytest -n auto` (auto-detect CPU cores)

---

## Factory Fixtures Pattern

### The `make_` Prefix Convention

Return callables, not fixed objects. Callers override only what matters for their test.

```python
@pytest.fixture
def make_customer(db_session):
    """Factory: create Customer with sensible defaults, override as needed."""
    created = []

    def make(
        name="Test Customer",
        email="test@example.com",
        tier="standard",
        **overrides,
    ):
        customer = Customer(name=name, email=email, tier=tier, **overrides)
        db_session.add(customer)
        db_session.flush()  # get the ID without committing
        created.append(customer)
        return customer

    yield make
    # Cleanup handled by transaction rollback — no manual delete needed

@pytest.fixture
def make_order(db_session, make_customer):
    """Composable factory: auto-creates customer if not provided."""
    def make(customer=None, product="Widget", quantity=1, **overrides):
        if customer is None:
            customer = make_customer()
        order = Order(
            customer_id=customer.id,
            product=product,
            quantity=quantity,
            **overrides,
        )
        db_session.add(order)
        db_session.flush()
        return order
    yield make
```

The `make_` pattern above is sufficient for most projects. No external factory library needed.

---

## Database Migration Testing (Alembic)

### Up/Down Round-Trip Verification

```python
"""Test that every migration can be applied and rolled back cleanly."""
import pytest
from alembic.config import Config
from alembic import command

@pytest.fixture(scope="session")
def alembic_cfg(db_url):
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg

def test_migrations_up_down_roundtrip(alembic_cfg):
    """Apply all migrations, roll back one by one, reapply all."""
    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")  # must succeed = round-trip clean

def test_each_migration_reversible(alembic_cfg):
    """Each individual migration must be reversible."""
    command.upgrade(alembic_cfg, "head")
    # Walk back one revision at a time
    command.downgrade(alembic_cfg, "-1")
    command.upgrade(alembic_cfg, "+1")
```

### Data Preservation Test

```python
def test_migration_preserves_data(alembic_cfg, db_session):
    """Seed data before migration, verify it survives."""
    command.upgrade(alembic_cfg, "abc123")  # migrate to revision before target
    db_session.execute(text("INSERT INTO users (name) VALUES ('Alice')"))
    db_session.commit()

    command.upgrade(alembic_cfg, "def456")  # apply the migration under test

    result = db_session.execute(text("SELECT name FROM users")).fetchone()
    assert result[0] == "Alice"
```

---

## Docker Compose for Multi-Service Test Environments

### Template: Backend + PostgreSQL

```yaml
# docker-compose.test.yml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: testdb
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"  # Non-default port to avoid conflicts
    tmpfs:
      - /var/lib/postgresql/data  # RAM-backed for speed
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test -d testdb"]
      interval: 2s
      timeout: 5s
      retries: 5

  app:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://test:test@postgres:5432/testdb
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "8001:8000"
```

For multi-service E2E setups, use `docker compose -f docker-compose.test.yml up -d --wait` in a session-scoped fixture. Playwright runs on host pointing at `localhost:<port>`.

---

## PostgreSQL-Specific Test Patterns

### Testing Constraints and Triggers

```python
def test_unique_email_constraint(db_session, make_customer):
    """DB constraint prevents duplicate emails."""
    make_customer(email="same@test.com")
    with pytest.raises(IntegrityError):
        make_customer(email="same@test.com")

def test_updated_at_trigger(db_session, make_customer):
    """Trigger auto-updates timestamp on row change."""
    customer = make_customer()
    original_updated = customer.updated_at
    customer.name = "Changed"
    db_session.flush()
    db_session.refresh(customer)
    assert customer.updated_at > original_updated
```

### Testing Complex Queries

```python
def test_revenue_report_aggregation(db_session, make_order):
    """Revenue report sums correctly across tiers."""
    make_order(quantity=10, unit_price=100, customer_tier="standard")
    make_order(quantity=5, unit_price=200, customer_tier="premium")
    make_order(quantity=1, unit_price=50, customer_tier="standard")

    report = generate_revenue_report(db_session)

    assert report["standard"]["total"] == pytest.approx(1050.0)
    assert report["premium"]["total"] == pytest.approx(1000.0)
    assert report["grand_total"] == pytest.approx(2050.0)
```
