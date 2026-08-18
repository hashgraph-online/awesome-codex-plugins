---
name: django-query-plan-reading
description: Read and compare Django/PostgreSQL query execution plans using QuerySet.explain(), EXPLAIN, EXPLAIN ANALYZE, scan types, joins, estimates, actual timing, buffers, and row counts. Use when one SQL query dominates Django latency or when an index, ORM rewrite, pagination change, or materialized view needs proof from a query plan.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django Query Plan Reading
  category: Django
  tags: django,database,query-plans,postgres,performance
---

# Django Query Plan Reading

Use this skill when the expensive unit is a specific SQL statement or queryset. The goal is to explain why the database is doing work, not to guess from the ORM code.

## Workflow

1. Get the exact query.
   - Prefer the queryset that produced it.
   - If starting from logged SQL, include bound parameters or representative literals.

2. Generate a plan.
   - Use `queryset.explain()` for ORM-owned SQL.
   - Use database `EXPLAIN` for raw SQL, views, materialized views, or SQL copied from logs.
   - Use `analyze=True` only in a safe environment because the database executes the query.

3. Read from the deepest node outward.
   - Identify table scans, index scans, joins, sorts, aggregations, and limits.
   - Compare estimated rows with actual rows when using analyze.
   - Look for high-cost nodes that feed many rows to later nodes.

4. Decide the next change.
   - Missing selective access path: use `django-index-design`.
   - Query shape prevents useful index access: rewrite filters, ordering, or join strategy.
   - Large unavoidable aggregation: consider `django-db-side-computation` or `django-materialized-views`.
   - Deep offset cost: use `django-pagination-performance`.

5. Re-run the same plan after the change.
   - Compare scan type, row counts, sort nodes, heap fetches, buffers, planning time, and execution time.

See [explain-checklist.md](references/explain-checklist.md) for plan-reading cues and before/after review notes.

## Safety Notes

- `EXPLAIN ANALYZE` executes the query. Avoid it for mutations, unsafe functions, and production paths unless you know the impact.
- A sequential scan is not automatically bad. It can be best when the table is small or the predicate returns much of the table.
- A used index is not automatically good. Random heap access, bad cardinality estimates, or a post-index sort can still dominate.

## Verification

Finish with the before/after plan excerpt and a plain explanation of which node changed and why that matters.
