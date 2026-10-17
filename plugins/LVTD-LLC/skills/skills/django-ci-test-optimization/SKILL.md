---
name: django-ci-test-optimization
description: Optimize Django and pytest-django test execution in CI with cache configuration, slow-test splitting, database reuse strategy, parallel workers, pytest-xdist, CircleCI/GitHub Actions/Jenkins/Travis patterns, and full-coverage safeguards. Use when CI test jobs are slow, flaky under parallelism, missing slow-test coverage, or need a local-vs-CI test command design.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django CI Test Optimization
  category: Django
  tags: django,testing,ci,pytest,github-actions
---

# Django CI Test Optimization

CI optimization should reduce feedback time without reducing confidence. Keep fast local commands and full CI coverage distinct, then make the CI path faster with caching, parallelism, and sensible split points.

## CI Workflow

1. Capture current CI timing.
   - Separate dependency install, test database setup, test execution, and artifact upload.
   - Compare CI time with local wall-clock time to spot environment-only overhead.

2. Cache dependencies first.
   - Use CI-native cache primitives for pip or package-manager caches.
   - Cache the package download cache, not an unsafe mutable virtualenv unless the project already supports that pattern.

3. Keep local shortcuts honest.
   - Local runs may skip slow tests or reuse databases.
   - CI should run slow tests and at least one migration-realistic database setup path.

4. Split tests deliberately.
   - Split slow vs normal tests when slow markers are meaningful.
   - Use parallel workers after the suite is safe under `django-test-parallelization`.
   - Avoid duplicating expensive setup across too many shards.

5. Scale hardware only after obvious waste is removed.
   - Faster runners can be the pragmatic answer, but they hide inefficient setup when used too early.

Read [ci-patterns.md](references/ci-patterns.md) for command and configuration patterns.

## Decision Rules

- Cache dependency downloads before rewriting test code for CI-only speed.
- Register pytest marks strictly so `slow` typos do not silently change coverage.
- If local commands exclude slow tests, add a CI job that includes them.
- If using no-migration local shortcuts, add a CI path that runs real migrations.
- Split by tags when test categories are intentionally different; split by workers when the suite is homogeneous enough.
- Use timing data to choose shard boundaries.

## Common Mistakes

- Caching the wrong path and seeing no improvement.
- Letting slow tests disappear from CI after adding local skip defaults.
- Running too many shards and paying database/setup cost repeatedly.
- Using SQLite in CI for a PostgreSQL/MySQL production app.
- Enabling parallel CI workers before fixing shared resources.
- Treating larger runners as a substitute for profiling.

## Verification

Before finishing:

- CI still runs all required test categories.
- Cache keys change when dependencies change.
- Test split commands are documented and reproducible locally where possible.
- Slow-test or worker split reduces wall-clock time in actual CI logs.
- A debugging fallback command exists for serial reproduction.
