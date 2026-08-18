# Shared Resources

Parallel workers share more than the database. Audit every resource that can persist across processes.

## Resource Audit

| Resource | Risk | Preferred Fix |
|----------|------|---------------|
| Django cache | Key collisions and stale values | Test-only key function or per-worker cache location |
| Files/media storage | Path collisions and cleanup races | Per-worker temp root |
| External HTTP service | Rate limits or cross-test state | Mock HTTP or isolate account/project |
| Task queue | Workers consuming each other's jobs | In-memory/eager mode or per-worker queue |
| Ports/sockets | Bind collisions | Allocate dynamic ports |
| Global settings/class attrs | State leaks between tests | Patch in the narrowest scope and restore |
| Lock-protected external resource | Hidden serialization | Lock only the critical section |

## Sharding Pattern

Prefer deriving a worker-specific suffix from process or pytest-xdist worker identity.

```python
import os

def parallel_worker_suffix() -> str:
    return os.environ.get("PYTEST_XDIST_WORKER") or str(os.getpid())
```

Use the suffix in temp directories, cache locations, queue names, and resource names. Keep this in test settings or test helpers so production behavior is untouched.

## Cache Key Function

For Django cache backends that support `KEY_FUNCTION`, include a worker suffix in test settings.

```python
import os

def parallel_cache_key(key, key_prefix, version):
    worker = os.environ.get("PYTEST_XDIST_WORKER") or str(os.getpid())
    return f"{worker}:{key_prefix}:{version}:{key}"
```

Do not use worker-specific cache keys in production; normal application processes need shared cache semantics.

## Locking Pattern

Use locks only when sharding is impossible.

- Keep the locked block as small as possible.
- Lock around the shared resource, not the whole test.
- Use a project-standard lock helper when one exists.
- Avoid one global lock for unrelated resources.

## Debug Checklist

- Does the failing test pass alone?
- Does it fail only with `--parallel` or `pytest -n`?
- Does it fail in a fixed order run?
- Which resource does the test mutate outside the test database?
- Can that resource be named per worker?
- If not, what is the smallest lockable section?
