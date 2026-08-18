# Django Database Performance Diagnostic Flow

## Evidence Template

Record these before making changes:

- Slow path: URL, command, Celery task, report, or queryset.
- Inputs: account, date range, filters, pagination cursor, fixture, or anonymized parameters.
- Baseline: wall time, DB time, query count, peak memory if relevant.
- Top SQL: normalized SQL text, table names, row count estimates, actual rows if available.
- Data shape: table sizes, important cardinalities, indexes already present.
- Runtime: Django version, database backend and version, debug/prod-like settings.

## Routing

| Symptom | Likely Cause | Next Skill |
| --- | --- | --- |
| Query count grows with rows rendered | N+1 related-object loading | `django-orm-query-optimization` |
| One query dominates DB time | Missing index, poor join order, bad filter shape | `django-query-plan-reading`, then `django-index-design` |
| View is fast for page 1 and slow for high page numbers | Offset pagination cost | `django-pagination-performance` |
| Worker memory spikes while looping rows | QuerySet result cache or model instantiation | `django-queryset-batch-processing` |
| Code counts, sums, or flags inside Python loops | Work should move to SQL expressions | `django-db-side-computation` |
| Dashboard/report query is slow but can be stale | Precomputed read model | `django-materialized-views` |
| Local reproduction unclear | Missing trace or representative data | `django-query-profiling` |

## Investigation Order

1. Confirm the slow path and collect a baseline.
2. Find the actual SQL and query count.
3. Reproduce locally or in a safe staging shell with production-like data volume.
4. Read the query plan for dominant SQL.
5. Change one thing.
6. Re-measure the same path.

## Common False Starts

- Adding an index without proving the query can use it.
- Adding `prefetch_related()` to a queryset that later calls a different filtered related manager.
- Using `only()` or `defer()` and then touching the deferred fields in a loop.
- Optimizing a local SQLite plan when production is PostgreSQL.
- Measuring with `DEBUG=True`, toolbar enabled, or tiny fixtures and treating that as production evidence.
- Improving SQL time while moving the bottleneck to serializer CPU or Python memory.

## Before/After Report

Use a compact PR note:

```text
Path: GET /orders/?status=open&page=42
Baseline: 1.8s wall, 241 queries, 1.4s DB, peak 320 MB
Change: Prefetch line items and move item count to annotation
After: 310 ms wall, 4 queries, 180 ms DB, peak 115 MB
Verification: existing API tests pass; added query-count regression test
Residual risk: production table has wider tenant cardinality than staging
```
