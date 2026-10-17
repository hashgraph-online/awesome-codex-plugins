---
name: django-orm-query-optimization
description: Optimize Django ORM query loading by fixing N+1 queries, duplicate related-object queries, over-fetching, serializer/template query loops, and inappropriate select_related, prefetch_related, only, or defer usage. Use when a Django page, API, admin view, template, serializer, or queryset issues too many queries or loads more model data than needed.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django ORM Query Optimization
  category: Django
  tags: django,orm,querysets,performance,n-plus-one
---

# Django ORM Query Optimization

Use this skill for query-count and object-loading problems. The usual target is an N+1 pattern where each rendered row or serialized object triggers more database work.

## Workflow

1. Prove the query pattern.
   - Capture query count and duplicate SQL for the slow path.
   - Identify the loop, serializer field, template access, admin display, or model property triggering related queries.

2. Choose the loading strategy.
   - Use `select_related()` for single-valued relationships: `ForeignKey` and `OneToOneField`.
   - Use `prefetch_related()` for many-valued relationships: reverse FK and many-to-many.
   - Use `Prefetch()` when the related queryset needs filters, ordering, annotations, or nested `select_related()`.
   - Use `values()` or `values_list()` when model instances are unnecessary.
   - Use `only()` or `defer()` only when large columns are truly unused.

3. Keep access consistent.
   - If you prefetch `items`, do not later call `items.filter(...)` and expect the prefetch cache to help.
   - If using `iterator()` with `prefetch_related()`, provide `chunk_size`.
   - Avoid putting broad prefetches into default managers unless every caller needs them.

4. Add a focused regression check when useful.
   - Use a query-count assertion around the exact view or serializer path.
   - Avoid brittle global query-count tests.

See [relationship-and-column-loading.md](references/relationship-and-column-loading.md) for examples and review cues.

## Anti-Patterns

- Adding `prefetch_related()` to every queryset without checking memory.
- Using `only()` and then touching deferred fields in a loop.
- Optimizing a queryset but leaving serializer method fields to issue per-row queries.
- Hiding queries in `__str__()`, model properties, template includes, or admin list methods.

## Verification

Show the query count and duplicate-query pattern before and after, plus any wall-time or memory change.
