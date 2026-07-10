---
name: django-test-profiling
description: Profile and measure slow Django test suites with Django's runner, pytest-django, shell timing, py-spy, cProfile, pytest durations, and profiler visualizations. Use when a Django project has slow tests, unclear test-runtime bottlenecks, CI timing problems, startup overhead, database setup overhead, or a request to find the slowest tests before optimizing.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django Test Profiling
  category: Django
  tags: django,testing,profiling,pytest,performance
---

# Django Test Profiling

Use this skill before changing a Django test suite for speed. Measurement decides which optimization is worth doing; otherwise it is easy to spend time on harmless settings while the real cost sits in startup, database setup, fixture construction, or a small set of slow tests.

## Measurement Workflow

1. Capture a full wall-clock baseline.
   - Prefer shell timing because it includes Python startup, Django import time, test discovery, database setup, and teardown.
   - Record the exact command, environment, and repeat count.

2. Separate framework phases when possible.
   - For Django's runner, use `--timing` to see database setup and teardown.
   - For pytest, compare shell timing with `pytest --durations`.

3. Find the slowest tests.
   - For pytest-django, start with `pytest --durations 20`.
   - For Django's runner, use an existing slow-test plugin or a small custom runner only when the project does not already have one.

4. Profile only after you know where the time goes.
   - Use `py-spy` first for a low-overhead whole-run view.
   - Use `cProfile` when you need exhaustive Python call data.

5. Convert the result into a ranked action list.
   - Identify whether the expensive part is startup, database creation, repeated setup, test data, query count, I/O, cache/file/storage access, or a specific test body.
   - Hand off to `django-test-performance`, `django-test-data`, or `django-test-parallelization` when the next step fits those skills.

## Commands

```bash
time python manage.py test
python manage.py test --timing
pytest --durations 20
```

For profiling command variants and interpretation guidance, read [profiler-commands.md](references/profiler-commands.md).

## Decision Rules

- Treat shell timing as the authoritative user-visible duration.
- Use Django `--timing` when database setup or teardown may dominate.
- Optimize the slowest measured tests first, not the tests that look suspicious.
- Put noisy duration reports in CI logs when they distract from normal local runs.
- Use `py-spy --subprocesses` when the test runner uses child processes.
- Sort cProfile by cumulative time first; inspect self-time only after you understand the caller chain.

## Common Mistakes

- Trusting a framework's final "ran in X seconds" line as the complete runtime.
- Comparing Django runner timing and pytest timing as if they measure identical phases.
- Profiling everything before finding slow tests.
- Reading unsorted cProfile output and chasing import internals.
- Expecting sampling profiles to catch every short hot path.
- Optimizing a helper without checking how often it is reached by tests.

## Verification

Before reporting findings, include:

- The exact baseline command and measured wall-clock time.
- The slowest tests or slowest phases.
- The profiler used, if any, and why it was appropriate.
- The top 3 practical next actions, ordered by expected impact.
