# CI Patterns

## Dependency Caching

Cache pip's download/cache directory:

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-${{ runner.os }}-${{ hashFiles('**/requirements*.txt', '**/pyproject.toml', '**/uv.lock') }}
```

For Jenkins, Travis, or other systems, use the platform cache mechanism for equivalent package-manager cache paths.

## Slow Test Split

Django runner:

```bash
python manage.py test --exclude-tag slow
python manage.py test --tag slow
```

pytest:

```bash
pytest -m "not slow"
pytest -m "slow"
```

In pytest config, register the marker and use strict marker handling:

```ini
[pytest]
addopts = --strict-markers
markers =
    slow: tests that are intentionally excluded from fast local runs
```

## Worker Parallelism

Use project-level parallelism only after the suite passes parallel safety checks.

```bash
python manage.py test --parallel
pytest -n auto --dist loadscope
```

If CI splits across machines, keep each shard's setup cost in mind. Too many shards can spend more time creating databases and installing dependencies than running tests.

## Database Fidelity

Keep CI close to production:

- PostgreSQL production apps should test against PostgreSQL.
- MySQL/MariaDB production apps should test against the matching family.
- SQLite is appropriate when production is SQLite or the project explicitly supports multiple database engines.

If local test settings disable migrations for speed, CI should include a migration-realistic job.

## CI Timing Report

When improving CI, report:

- Dependency install time before/after.
- Test database setup time before/after.
- Test execution time before/after.
- Number of workers/shards.
- Cache hit/miss status.
- Longest remaining job.
