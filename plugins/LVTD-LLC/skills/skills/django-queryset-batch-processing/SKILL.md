---
name: django-queryset-batch-processing
description: Process large Django querysets and write-heavy jobs with memory-safe reads, values/values_list, iterator chunking, set-based update/delete, bulk_create, bulk_update, F expressions, Func expressions, and batch sizing. Use when a Django command, task, migration, report, or loop reads or writes many rows and is slow, memory-heavy, or query-heavy.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django QuerySet Batch Processing
  category: Django
  tags: django,querysets,batch-processing,orm,performance
---

# Django QuerySet Batch Processing

Use this skill when Django code processes many rows. The goal is to avoid loading unnecessary model instances, avoid queryset result-cache blowups, and move writes into set-based database operations when behavior allows.

## Workflow

1. Identify the per-row work.
   - Is it read-only export/reporting?
   - Does it need model methods, validation, or signals?
   - Can the database compute or update the value directly?

2. Choose the read pattern.
   - Use `values()` or `values_list()` for scalar exports and reports.
   - Use `iterator(chunk_size=...)` when model instances are needed but queryset caching is not.
   - Keep ordering deliberate; unnecessary ordering costs work.

3. Choose the write pattern.
   - Use `QuerySet.update()` with `F()` or expressions for uniform updates.
   - Use `bulk_update()` when each object has a different value.
   - Use `bulk_create()` for inserts, with conflict options only when the project supports their semantics.
   - Fall back to per-instance `save()` only when hooks, validation, side effects, or signals are required.

4. Control batch size.
   - Keep transactions bounded.
   - Avoid huge `IN` lists and oversized `CASE` updates.
   - Monitor locks, replication lag, and memory for production jobs.

See [batch-patterns.md](references/batch-patterns.md) for examples and caveats.

## Safety Notes

- Bulk update/delete operations do not call each model instance's `save()` or `delete()` methods.
- Bulk operations can skip application-level side effects and signals.
- Long transactions can hold locks and delay vacuum or replication.

## Verification

Measure rows processed per second, query count, memory, transaction duration, and correctness on a representative batch.
