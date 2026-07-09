---
name: django-materialized-views
description: Model, migrate, refresh, and verify PostgreSQL materialized views in Django for expensive report or dashboard queries that can tolerate stale data. Use when ORM/index/query rewrites are not enough, the result is read often, freshness can be bounded, and a Django app needs unmanaged models, RunSQL migrations, refresh commands, or concurrent refresh.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django Materialized Views
  category: Django
  tags: django,database,materialized-views,postgres,performance
---

# Django Materialized Views

Use this skill when an expensive read query is reused often and can tolerate controlled staleness. Try query-plan, index, and ORM expression improvements first; materialized views add operational state.

## Workflow

1. Confirm fit.
   - The source query is expensive and stable.
   - Consumers can accept stale data.
   - Refresh cadence, ownership, and failure behavior are clear.
   - PostgreSQL is the target database.

2. Design the materialized view.
   - Define the SQL query and output columns.
   - Add a unique column or unique column set if concurrent refresh is required.
   - Add indexes for consumer queries against the view.

3. Integrate with Django.
   - Create the view with `RunSQL`.
   - Represent it as an unmanaged model with `managed = False`.
   - Keep the unmanaged model fields aligned with the SQL output.
   - Make writes impossible at the application boundary.

4. Implement refresh.
   - Use `REFRESH MATERIALIZED VIEW` for simple refreshes.
   - Use `REFRESH MATERIALIZED VIEW CONCURRENTLY` only when the view is already populated and has a qualifying unique index.
   - Schedule refresh through a management command, task queue, or database job.

See [materialized-view-patterns.md](references/materialized-view-patterns.md) for migration, model, and refresh templates.

## Safety Notes

- A materialized view returns stored data; it is not automatically current.
- Concurrent refresh avoids locking out reads but has prerequisites and still allows only one refresh at a time per view.
- Refreshing a large view can be a major database workload. Measure it separately from reads.

## Verification

Validate the SQL against source tables, test the unmanaged model reads, prove refresh behavior, and measure read latency before/after.
