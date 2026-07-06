# Safe Speed Wins

Apply these only after measuring. Keep the test suite faithful enough that passing tests still mean production behavior is covered.

## Settings Checklist

| Area | Typical Test Override | Check |
|------|-----------------------|-------|
| Password hashing | Fast hasher such as MD5 for tests | No test asserts production hash cost |
| Debug mode | `DEBUG = False` | Debug-specific behavior has separate tests if needed |
| DB serialization | `DATABASES["default"]["TEST"]["SERIALIZE"] = False` | Suite does not depend on serialized rollback |
| File storage | In-memory or temp-dir storage | File behavior under test still uses a real file when needed |
| Cache | LocMem, Dummy, fake Redis, or per-worker cache | Cache behavior tests use a representative backend |
| Task queues | Eager, sync, or in-memory brokers | Worker integration has separate coverage |
| Instrumentation | Disable debug toolbar, APM, Sentry/Rollbar setup | Error-reporting integration is tested elsewhere |
| Static files | Avoid WhiteNoise startup scans during tests | Static-file behavior has targeted tests |

## Local Database Reuse

Use database reuse for repeated local runs:

```bash
python manage.py test --keepdb
pytest --reuse-db
pytest --create-db
```

Force a rebuild after:

- Switching branches with migration changes.
- Editing, deleting, renaming, or squashing migrations.
- Renaming apps or models.
- Upgrading Django or database drivers.
- Seeing unexplained schema-related failures.

## Migrations

Prefer migration squashing over bypassing migrations. Long migration histories slow database creation and increase CI setup time, but disabled migrations can hide production schema behavior.

If a project uses no-migration local shortcuts:

- Keep them out of CI or add a CI job that runs migrations for real.
- Avoid depending on no-migration behavior in tests.
- Revisit the shortcut after migration squashing.

## Slow Test Markers

Local runs may skip marked slow tests, but CI should still run them.

```bash
python manage.py test --exclude-tag slow
python manage.py test --tag slow

pytest -m "not slow"
pytest -m "slow"
```

Use strict marker registration in pytest so typoed marks do not silently change coverage.
