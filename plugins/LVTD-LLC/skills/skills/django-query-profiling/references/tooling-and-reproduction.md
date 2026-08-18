# Query Profiling Tooling and Reproduction

## APM And Trace Data

Use APM when the slow path happens in production and needs real traffic context.

Collect:

- Transaction name, URL, job name, or command name.
- Total duration, DB duration, external-call duration, and queue time.
- Slow SQL statements and stack frames if available.
- Parameters that materially change cardinality, such as tenant, date range, filters, and page number.

Treat APM output as a lead. Reproduce before editing unless the fix is an emergency mitigation.

## Django Debug Toolbar

Use Django Debug Toolbar for local server-rendered pages. It shows query count, SQL, duplicate queries, and timing.

Do not rely on it alone for API views, streaming responses, background jobs, or production timings. For those, wrap the code path with targeted logging.

## Targeted Query Logging

For a local shell, test, or temporary diagnostic branch:

```python
from django.db import connection, reset_queries
from django.test.utils import CaptureQueriesContext

reset_queries()
with CaptureQueriesContext(connection) as ctx:
    response = client.get("/orders/?status=open")

print(len(ctx))
for query in ctx.captured_queries[:20]:
    print(query["time"], query["sql"])
```

Use `CaptureQueriesContext` in tests only for narrow regression coverage. Avoid broad query-count assertions that break on harmless framework changes.

## Local Reproduction

Build the smallest repeatable reproduction:

```python
from time import perf_counter

def run():
    start = perf_counter()
    rows = list(
        Order.objects.filter(status="open")
        .select_related("account")
        [:100]
    )
    return len(rows), perf_counter() - start
```

Run it against data volume that resembles the slow tenant or report. Tiny fixture databases can hide planner and N+1 problems.

## Finding The ORM Source

Search in this order:

1. Table name from SQL.
2. Model class `Meta.db_table` or default app/model table.
3. Column names from filters, joins, or `ORDER BY`.
4. View, viewset, manager, serializer, form, template, or task that owns the path.
5. Model properties or `__str__()` methods used during serialization or rendering.

Check code that runs after the initial queryset: serializer method fields, template includes, admin list display, permissions, and logging can all issue hidden queries.

## Profiling Pitfalls

- `DEBUG=True` changes query recording and can add debug-only work.
- `connection.queries` only records queries when debug cursor behavior is enabled.
- Query timings from SQLite do not predict PostgreSQL plans.
- Query count is not the same as total latency; one bad query can dominate.
- Total DB time can improve while Python serialization remains the bottleneck.
