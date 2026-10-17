---
name: django-test-performance
description: Improve slow Django test suites through measured profiling, safe test settings, database and migration tuning, parallel execution, test-data cleanup, and CI workflow changes. Use when Django or pytest-django tests are slow, CI test jobs take too long, database setup dominates runtime, or a user asks for a prioritized speedup plan rather than isolated test fixes.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django Test Performance
  category: Django
  tags: django,testing,performance,pytest,ci
---

# Django Test Performance

Use this as the orchestration skill for speeding up a Django test suite. Do not start by changing settings blindly; first measure the suite and then pick the smallest safe optimization with a repeatable verification command.

## Core Workflow

1. Establish a baseline.
   - Run the same command developers or CI use.
   - Capture wall-clock time, runner, settings module, database backend, worker count, and branch.
   - If the cause is unclear, use `django-test-profiling` before changing behavior.

2. Classify the dominant cost.
   - Startup/import/discovery: reduce collection scope and expensive app initialization.
   - Database creation/migrations: reuse DB locally, squash migration history, or improve database storage.
   - Per-test setup: reduce fixture data, use factories, and use `setUpTestData`.
   - External backends: replace file storage, cache, task queues, and instrumentation with test-safe backends.
   - Long tail of tests: parallelize after isolation checks.

3. Apply low-risk wins first.
   - Fast password hasher.
   - `DEBUG = False` in tests.
   - Disable database serialization when serialized rollback is not needed.
   - Disable debug toolbar, Sentry/Rollbar/APM initialization, and other instrumentation.
   - In-memory or local test backends for storage, cache, and task queues.
   - See [speed-wins.md](references/speed-wins.md).

4. Improve data and structure.
   - Use `django-test-data` for factory, fixture, `setUpTestData`, `TestCase`, and integration-vs-unit decisions.

5. Improve migrations and database setup.
   - Use `--keepdb` or `--reuse-db` for local repeat runs.
   - Force rebuilds when migration history changes.
   - Prefer squashing migrations over disabling migrations globally.
   - Keep the test database backend close to production unless the project is database-agnostic.

6. Parallelize only when safe.
   - Use `django-test-parallelization` for order isolation, shared resources, and worker configuration.

7. Re-measure with the original baseline command.
   - Report before/after runtime and the changed risk surface.
   - Keep or revert each optimization based on measured impact and behavioral fidelity.

## Default Commands

```bash
time python manage.py test
python manage.py test --timing
python manage.py test --keepdb

time pytest
pytest --durations 20
pytest --reuse-db
pytest --create-db
```

## Decision Rules

- If you cannot name the bottleneck, profile first.
- If a setting changes production-like behavior, keep the override narrow and document why tests remain representative.
- Avoid broad `TESTING = True` branches in application code; use explicit settings and test helpers.
- Do not swap PostgreSQL/MySQL/MariaDB projects to SQLite just for speed unless production is SQLite or the project intentionally supports many backends.
- Do not disable migrations as the normal path. If a legacy project insists, run real migrations in CI.
- Keep local speed shortcuts from hiding CI coverage. CI should run slow tests and migration-realistic paths somewhere.

## Handoff Map

| Situation | Use |
|-----------|-----|
| Need timings, slow-test lists, flame graphs, or cProfile output | `django-test-profiling` |
| Enabling `--parallel`, `pytest-xdist`, or debugging random failures | `django-test-parallelization` |
| Fixture bloat, factories, `setUpTestData`, `TestCase` class choices | `django-test-data` |
| Mocking settings, HTTP, time, output, or command input safely | `django-targeted-mocking` |
| CI cache, split jobs, slow markers, runner scale | `django-ci-test-optimization` |

## Verification

Before finishing, provide:

- Baseline and final runtime from the same command.
- A ranked list of changes made or recommended.
- Risks introduced by each test-only override.
- Commands the project should keep for local and CI verification.
