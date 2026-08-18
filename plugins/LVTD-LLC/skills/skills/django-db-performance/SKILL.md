---
name: django-db-performance
description: Diagnose and improve slow Django database-backed endpoints with evidence-first profiling, query-plan review, index selection, ORM loading fixes, batching, database-side computation, materialized views, and pagination choices. Use when a Django view, API, job, report, queryset, or database query is slow and the right optimization path is not obvious.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django DB Performance
  category: Django
  tags: django,database,performance,orm,profiling
---

# Django DB Performance

Use this as the orchestration skill for Django database performance work. Start with measured evidence, reproduce the slow path, and route to the smallest optimization that changes the measured bottleneck.

## Core Workflow

1. Capture the symptom.
   - Identify the exact endpoint, command, task, report, or queryset.
   - Record current wall-clock time, query count, slow SQL, database backend, data volume, and Django version.
   - Keep the original request parameters or fixture that reproduces the issue.

2. Profile before changing code.
   - Use APM traces, database slow-query logs, Django Debug Toolbar, `connection.queries`, or targeted logging.
   - If the expensive query is known, use `QuerySet.explain()` or database `EXPLAIN`.
   - For API endpoints, profile serializers and permission checks as well as querysets.

3. Classify the dominant problem.
   - Many repeated similar queries: use `django-orm-query-optimization`.
   - One or two expensive SQL statements: use `django-query-plan-reading` and `django-index-design`.
   - Large memory use or long loops over querysets: use `django-queryset-batch-processing`.
   - Python loops computing counts, totals, flags, or latest related rows: use `django-db-side-computation`.
   - Slow aggregate/report query that is acceptable when stale: use `django-materialized-views`.
   - Slow or inconsistent list pages: use `django-pagination-performance`.
   - Unclear evidence: use `django-query-profiling`.

4. Apply one change at a time.
   - Prefer the narrowest change with a clear expected effect.
   - Avoid adding indexes, prefetches, or materialized views speculatively.
   - Confirm that the optimization helps real production-like data, not only tiny fixtures.

5. Verify and document the result.
   - Re-run the same request or command with the same parameters.
   - Compare query count, total DB time, wall-clock time, memory, and query plan.
   - Keep before/after evidence in the PR or final report.

See [diagnostic-flow.md](references/diagnostic-flow.md) for routing checklists, common symptoms, and before/after evidence templates.

## Modern Django Notes

- Prefer `QuerySet.explain()` for ORM query plans before dropping to raw `EXPLAIN`.
- Prefer native Django/PostgreSQL migration operations such as `AddIndexConcurrently` over hand-written concurrent index SQL when they fit.
- Prefer ORM expressions, `Subquery`, `Exists`, `Window`, `GeneratedField`, and `db_default` when they make database work explicit and portable enough.
- Treat every backend-specific optimization as conditional on the project database. PostgreSQL patterns do not automatically apply to MySQL, MariaDB, SQLite, or Oracle.

## Verification

- Show the slow path is still functionally correct.
- Show the measured bottleneck improved.
- Show the optimization did not create a worse query, stale data bug, write-path regression, or memory spike.
