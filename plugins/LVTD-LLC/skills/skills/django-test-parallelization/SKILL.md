---
name: django-test-parallelization
description: Safely parallelize Django and pytest-django test suites with Django --parallel, pytest-xdist, test isolation checks, randomized order detection, shared-resource sharding, locks, and load balancing. Use when enabling parallel tests, diagnosing failures under parallel execution, handling flaky Django tests, or making caches, files, queues, and external resources safe across workers.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django Test Parallelization
  category: Django
  tags: django,testing,parallelization,pytest,xdist
---

# Django Test Parallelization

Parallel test execution is a multiplier after a suite is isolated. Treat failures under parallel execution as evidence of hidden shared state until proven otherwise.

## Readiness Workflow

1. Measure serial runtime first.
   - If the suite is already dominated by startup or database creation, parallelism may not help enough on its own.

2. Check isolation before enabling parallelism as the default.
   - Run in reverse order.
   - Run with randomized order when reverse order is not enough.
   - Preserve random seeds so failures can be reproduced.

3. Enable the runner deliberately.
   - Django runner: install `tblib`, then run `python manage.py test --parallel`.
   - pytest-django: install `pytest-xdist`, then run `pytest -n auto`.

4. Classify failures.
   - Order-dependent failures usually come from mutated globals, class attributes, settings, caches, monkeypatches, or database assumptions.
   - Parallel-only failures usually come from shared resources such as files, cache keys, ports, queues, external services, or temporary directories.

5. Make resources worker-safe.
   - Prefer sharding per process or worker.
   - Use locks only when the resource cannot be partitioned.
   - Keep lock scope narrow.

6. Balance work after it is correct.
   - Split large test classes or modules only when measurement shows one group holds back the parallel run.

## Commands

```bash
python -m pip install tblib
python manage.py test --parallel
python manage.py test --parallel 1
python manage.py test --reverse

python -m pip install pytest-xdist
pytest -n auto
pytest -n auto --dist loadscope
```

For shared-resource patterns, read [shared-resources.md](references/shared-resources.md).

## Decision Rules

- Add parallel testing early in new projects; older serial suites often have hidden isolation assumptions.
- Use CI reverse-order testing as a low-friction guard against order dependencies.
- Use random order when reverse order misses a suspected dependency, and capture the seed.
- Prefer `pytest -n auto --dist loadscope` for Django `TestCase`-heavy suites because class/module setup can be expensive.
- Shard resources before reaching for locks.
- Put process-specific behavior in test settings only, not production settings.
- Split large test groups only after profiling shows an imbalance.

## Common Mistakes

- Assuming database transaction isolation protects caches, files, task queues, or external systems.
- Mutating class attributes, globals, app settings, or cache entries without restoring them.
- Enabling random order without preserving the seed.
- Using a single lockfile for too much work and accidentally serializing the suite.
- Letting pytest-xdist split related tests so finely that setup cost is duplicated.
- Making parallelism the default before the suite passes reliably under order-isolation checks.

## Verification

Before calling parallelization complete:

- Serial run passes.
- Reverse or random-order run passes, or known failures are fixed.
- Parallel run passes at least twice.
- Any shared-resource sharding lives in test configuration.
- CI has a serial fallback command for debugging.
