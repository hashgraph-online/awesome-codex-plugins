# Advanced Python Patterns

Reference for complex patterns. Read when the main SKILL.md points you here.

## Table of Contents
1. Generic Protocols
2. Async Generators for Streaming
3. Thread-Safe Singletons
4. Custom Decorators with ParamSpec
5. Sentinel Objects
6. ContextVar for Request-Scoped State
7. Enum with Behavior

---

## 1. Generic Protocols

When a Protocol needs to work across multiple types:

```python
from typing import Protocol, TypeVar

T = TypeVar("T")

class Repository(Protocol[T]):
    """Generic repository — works for any entity type."""
    async def get(self, id: str) -> T | None: ...
    async def save(self, entity: T) -> None: ...
    async def delete(self, id: str) -> bool: ...

class UserRepo:
    """Satisfies Repository[User] without inheriting from it."""
    async def get(self, id: str) -> User | None: ...
    async def save(self, entity: User) -> None: ...
    async def delete(self, id: str) -> bool: ...

async def sync_entities(source: Repository[T], target: Repository[T]) -> int:
    """Works with any Repository — User, Document, Config, etc."""
    ...
```

The generic `T` flows through — `sync_entities(user_repo, backup_repo)` infers `T = User`. No registration, no base class.

---

## 2. Async Generators for Streaming

Yield events as they happen, don't batch-then-yield:

```python
from collections.abc import AsyncGenerator

async def stream_embeddings(
    texts: list[str],
    batch_size: int = 32,
) -> AsyncGenerator[EmbeddingResult, None]:
    """Yield embeddings as each batch completes — true streaming."""
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        results = await embed_batch(batch)
        for text, embedding in zip(batch, results, strict=True):
            yield EmbeddingResult(text=text, embedding=embedding, batch_index=i)
```

Callers get results incrementally:

```python
async for result in stream_embeddings(documents):
    await index_document(result)  # process as they arrive
```

For concurrent production + consumption on Python 3.11+, pair an `asyncio.Queue` with `TaskGroup` so producer failures cancel the consumer and still propagate:

```python
import asyncio
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class _Done:
    pass

_DONE = _Done()

async def producer(queue: asyncio.Queue[Item | _Done], items: list[Input]) -> None:
    try:
        for item in items:
            await queue.put(await process(item))
    finally:
        queue.put_nowait(_DONE)  # unbounded queue: completion cannot block

async def consumer(queue: asyncio.Queue[Item | _Done]) -> list[Item]:
    results: list[Item] = []
    while True:
        item = await queue.get()
        if isinstance(item, _Done):
            return results
        results.append(item)

async def run_pipeline(items: list[Input]) -> list[Item]:
    queue: asyncio.Queue[Item | _Done] = asyncio.Queue()
    async with asyncio.TaskGroup() as tasks:
        tasks.create_task(producer(queue, items))
        consumer_task = tasks.create_task(consumer(queue))
    return consumer_task.result()
```

On older Python versions, use the repository's structured-concurrency abstraction. Do not start detached producer and consumer tasks: sibling cancellation and failure propagation are part of the contract.

---

## 3. Thread-Safe Singletons

Serialize acquisition for expensive initialization when shutdown is supported:

```python
import threading

_instance: ExpensiveClient | None = None
_lock = threading.Lock()

def get_client() -> ExpensiveClient:
    """Create or acquire the shared client under the lifecycle lock."""
    global _instance
    with _lock:
        if _instance is None:
            _instance = ExpensiveClient()
        return _instance

def close_client() -> None:
    """Close during application shutdown, after active users have quiesced."""
    global _instance
    with _lock:
        if _instance is not None:
            _instance.close()
            _instance = None
```

The lock makes acquisition atomic with lifecycle state changes. It does not make a borrowed client safe from concurrent close: call `close_client` only after new acquisitions are stopped and active users have quiesced.

For class-level singletons, use `ClassVar` + class lock:

```python
from typing import ClassVar

class CircuitBreaker:
    _instances: ClassVar[dict[str, CircuitBreaker]] = {}
    _instances_lock: ClassVar[threading.Lock] = threading.Lock()

    @classmethod
    def for_provider(cls, provider: str) -> CircuitBreaker:
        key = provider.lower()
        with cls._instances_lock:
            if key not in cls._instances:
                cls._instances[key] = cls(provider=key)
            return cls._instances[key]
```

---

## 4. Custom Decorators with ParamSpec

Preserve the decorated function's signature for type checkers:

```python
import functools
import time
from typing import ParamSpec, TypeVar
from collections.abc import Callable, Awaitable

P = ParamSpec("P")
R = TypeVar("R")

def timed(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    """Async timing decorator — preserves signature for type checkers."""
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.monotonic()
        result = await func(*args, **kwargs)
        elapsed = (time.monotonic() - start) * 1000
        logger.info("Call completed", extra={"func": func.__name__, "ms": elapsed})
        return result
    return wrapper

@timed
async def fetch_user(user_id: str, include_profile: bool = False) -> User:
    ...
# Type checker knows: fetch_user(user_id: str, include_profile: bool = False) -> User
```

Without `ParamSpec`, the decorator erases the signature and the type checker only sees `(*args, **kwargs) -> Any`.

---

## 5. Sentinel Objects

When `None` is a valid value and you need a distinct "not provided" signal:

```python

class _Sentinel:
    """Singleton sentinel — distinct from None, False, 0, ''."""
    _instance: _Sentinel | None = None

    def __new__(cls) -> _Sentinel:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "MISSING"

    def __bool__(self) -> bool:
        return False

MISSING = _Sentinel()

def update_config(
    timeout: float | _Sentinel = MISSING,
    retries: int | _Sentinel = MISSING,
) -> None:
    """Only update fields that were explicitly passed."""
    if not isinstance(timeout, _Sentinel):
        config.timeout = timeout
    if not isinstance(retries, _Sentinel):
        config.retries = retries
```

This distinguishes `update_config(timeout=None)` (explicitly set to None) from `update_config()` (not provided).

---

## 6. ContextVar for Request-Scoped State

Thread-safe, async-safe state without passing context through every function:

```python
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="unknown")
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)

# Set at the request boundary (middleware)
async def middleware(request: Request, call_next: Callable) -> Response:
    token = request_id_var.set(request.headers.get("X-Request-ID", generate_id()))
    try:
        return await call_next(request)
    finally:
        request_id_var.reset(token)  # clean up

# Read anywhere in the call stack — no parameter threading
def get_log_context() -> dict[str, str]:
    return {"request_id": request_id_var.get(), "user_id": user_id_var.get() or "anonymous"}
```

`ContextVar` is the correct replacement for thread-locals in async code. Each task gets its own copy automatically.

---

## 7. Enum with Behavior

When enum members need associated logic, attach it as methods:

```python
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    @property
    def allows_traffic(self) -> bool:
        return self in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    @property
    def label(self) -> str:
        _LABELS: dict[CircuitState, str] = {
            CircuitState.CLOSED: "healthy",
            CircuitState.OPEN: "down",
            CircuitState.HALF_OPEN: "probing",
        }
        return _LABELS[self]
```

Behavior lives with the data, not in a separate switch statement. Adding a new state without implementing `label` causes a `KeyError` — not a silent default.

For simple string unions without behavior, prefer `Literal`:

```python
# No behavior needed → Literal is simpler
Provider = Literal["openai", "anthropic", "google", "deepseek"]

# Behavior needed → Enum is better
class CircuitState(Enum): ...
```
