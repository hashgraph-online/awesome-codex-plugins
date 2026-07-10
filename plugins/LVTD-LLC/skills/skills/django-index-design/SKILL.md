---
name: django-index-design
description: Design safe Django and PostgreSQL indexes from measured query plans, including B-tree, composite, covering, partial, expression, GIN/JSONB, BRIN, and concurrent migration patterns. Use when a Django query plan suggests missing or mismatched indexes, a production table needs an index without write downtime, or existing indexes need review.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django Index Design
  category: Django
  tags: django,database,indexes,postgres,performance
---

# Django Index Design

Use this skill to add or change indexes only after profiling shows a specific query can benefit. Indexes speed selected reads and constraints, but they add write cost, migration risk, and maintenance overhead.

## Workflow

1. Start from a query plan.
   - Capture the SQL, filters, joins, ordering, selected columns, table sizes, and current indexes.
   - Confirm that the query is important enough to optimize.

2. Choose the index shape.
   - Equality filters first, then range/order fields when useful.
   - Match `ORDER BY` for `LIMIT` queries when possible.
   - Use partial indexes for highly queried subsets.
   - Use covering indexes only when selected columns are stable and index-only scans are plausible.
   - Use GIN for JSONB containment, arrays, and full-text patterns; do not expect a B-tree to solve those.

3. Express the index in Django models or migrations.
   - Prefer `Meta.indexes` for normal model-owned indexes.
   - Prefer `AddIndexConcurrently` and `RemoveIndexConcurrently` for live PostgreSQL tables.
   - Use raw SQL only when Django cannot express the index.

4. Validate on production-like data.
   - Re-run `QuerySet.explain()` or `EXPLAIN ANALYZE`.
   - Verify the planner uses the index for the target query.
   - Check write-path impact when the indexed table is hot.

See [index-patterns.md](references/index-patterns.md) for index examples and migration templates.

## Production Rules

- For PostgreSQL live tables, use concurrent index operations and set the migration `atomic = False`.
- Keep names short, stable, and explicit.
- Do not add duplicate indexes that are already covered by a unique constraint or a left-prefix composite index.
- Remove unused indexes only after checking production usage and deployment rollback needs.

## Verification

Finish with before/after plan evidence, the exact migration operation, and the operational risk assessment for locks, writes, and rollback.
