---
name: django-query-profiling
description: Find the Django ORM code and request path responsible for slow SQL by using APM traces, slow query logs, Django Debug Toolbar, query logging, and local reproduction. Use when a Django database performance issue is suspected but the exact queryset, view, serializer, template, or job causing it is not yet proven.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django Query Profiling
  category: Django
  tags: django,database,profiling,apm,debug-toolbar
---

# Django Query Profiling

Use this skill to turn a vague slow-Django report into a specific queryset, SQL statement, and reproducible scenario.

## Workflow

1. Start from the user-visible slow path.
   - Record the URL, API action, background task, management command, or report.
   - Capture request parameters, user or tenant shape, pagination state, and data volume.

2. Collect production or staging evidence.
   - Prefer APM transaction traces when available.
   - Use database slow-query logs for SQL that is slow independent of Python.
   - Use Django Debug Toolbar for server-rendered pages in local development.
   - For APIs or jobs, add targeted query logging around the suspicious block.

3. Map SQL back to Django code.
   - Search model table names and column names.
   - Inspect view `get_queryset()`, serializer fields, template loops, managers, model properties, and signal handlers.
   - Check whether related-object access happens after the initial queryset was evaluated.

4. Reproduce locally or in a safe shell.
   - Use production-like row counts when possible.
   - Disable unrelated instrumentation and debug-only middleware when measuring.
   - Keep a repeatable script, test, or shell snippet that exercises the slow path.

5. Route the fix.
   - Query count issue: use `django-orm-query-optimization`.
   - One slow SQL statement: use `django-query-plan-reading`.
   - Large loops or writes: use `django-queryset-batch-processing`.

See [tooling-and-reproduction.md](references/tooling-and-reproduction.md) for concrete profiling snippets and pitfalls.

## Good Evidence

- Query count before/after for the specific path.
- The slow SQL or normalized SQL fingerprint.
- Stack or code pointer that explains where the SQL originates.
- Timing from the same environment and representative data shape.

## Verification

Do not finish profiling with only a hunch. Finish with a named queryset, code path, and command or request that another agent can re-run.
