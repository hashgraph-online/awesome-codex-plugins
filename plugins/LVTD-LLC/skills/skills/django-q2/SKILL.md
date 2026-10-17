---
name: django-q2
description: "Use when adding, changing, testing, or debugging Django Q2 background tasks, scheduled jobs, qcluster workers, Redis broker configuration, or ORM broker fallback in Django projects."
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django Q2
  category: Django
  tags: django,django-q2,background-jobs,redis
---

# Django Q2 Background Jobs

Use this before touching task enqueueing, schedules, worker deployment,
`Q_CLUSTER`, or code imported by Django Q2 workers.

## Configuration Checks

- The dependency is `django-q2`; the Python import path is `django_q`.
- `django_q` is in `INSTALLED_APPS`; its migrations provide task result,
  schedule, and broker models.
- Find `Q_CLUSTER` in the project's settings module before changing task,
  worker, or broker behavior.
- Confirm the configured broker. Redis is common, often through an environment
  variable such as `REDIS_URL`; the ORM broker is useful for low-throughput or
  Redis-free deployments.
- Confirm the project's worker command. The base command is
  `python manage.py qcluster`, but projects may wrap it with `uv`, Poetry,
  Docker Compose, process managers, or platform-specific worker declarations.
- If Redis is removed as the broker, review any Redis-dependent cache, health
  check, Docker, deployment, and documentation references separately.

## Mental Model

- Web code calls `async_task(...)` or creates `Schedule` rows.
- The broker stores queued task packages until a `qcluster` process reserves
  work.
- Worker processes execute importable Python functions and save results or
  failures.
- The scheduler runs inside the cluster. Schedules are database rows; they do
  nothing unless `qcluster` is running.

## Adding Tasks

1. Put the task function in the app that owns the behavior, usually a
   `tasks.py` module or another importable module already used by the project.
2. Keep the function importable at module import time. Do not rely on request
   objects, local closures, or process-local state.
3. Pass durable identifiers such as primary keys, not model instances, open
   files, connections, or large payloads.
4. Make the task idempotent. Redis does not give exactly-once execution
   guarantees, and receipt-based brokers can re-run work.
5. If the task depends on a just-saved database row, enqueue it from
   `transaction.on_commit(...)`.

```python
def send_welcome_email(user_id: int) -> None:
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.get(pk=user_id)
    ...
```

```python
from django.db import transaction
from django_q.tasks import async_task

transaction.on_commit(
    lambda: async_task("myapp.tasks.send_welcome_email", user.pk)
)
```

Use `q_options` when Django Q2 options would collide with task kwargs:

```python
async_task(
    "myapp.tasks.rebuild_report",
    report_id,
    q_options={"timeout": 300, "group": "reports"},
)
```

## Scheduling Work

Prefer named, idempotent schedules created by a migration, admin action, or
setup command. Avoid creating schedules unconditionally at import time or app
startup.

```python
from django_q.models import Schedule

Schedule.objects.get_or_create(
    name="clear-expired-sessions",
    defaults={
        "func": "django.core.management.call_command",
        "args": "'clearsessions'",
        "schedule_type": Schedule.HOURLY,
    },
)
```

Use `Schedule.objects.get_or_create(name=..., defaults={...})` when seeding
schedules so repeated setup does not duplicate jobs. Cron schedules require the
optional `croniter` dependency; do not use `Schedule.CRON` unless the project
includes it.

Missed schedules catch up by default. Set `Q_CLUSTER["catch_up"] = False` when
a job should run once after downtime instead of replaying every missed interval.

## Broker Choices

### Redis Broker

Use Redis when the project already depends on it for workers or deployment:

```python
Q_CLUSTER = {
    "name": "...",
    "timeout": 3600,
    "workers": 4,
    "redis": REDIS_URL,
}
```

Redis is fast and usually fits projects that already run Redis for cache,
Docker, or deployment workers. The default Redis broker does not support
delivery receipts. If a worker host dies catastrophically while executing a
task, the in-flight package can be lost; if task code raises, Django Q2 records
a failure. Use idempotent task design, explicit retries in task code where
needed, and monitoring for failures.

### ORM Broker

Use the Django database broker only for low-throughput deployments, local
simplicity, or environments where Redis is unavailable:

```python
Q_CLUSTER = {
    "name": "...",
    "timeout": 3600,
    "retry": 4800,
    "workers": 4,
    "max_attempts": 2,
    "orm": "default",
}
```

When switching to ORM:

- Remove the `"redis"` broker key; configure one broker per cluster unless you
  intentionally use custom clusters.
- Run migrations for `django_q`. If the broker uses a non-default database
  alias, run migrations with `--database <alias>`.
- Increase `"poll"` above the default `0.2` seconds, for example `"poll": 2.0`,
  when you need lower database polling pressure and can tolerate higher queue
  pickup latency.
- The ORM broker enables the Queued Tasks admin table.
- Review Redis-dependent cache, health check, Docker, and deployment settings
  separately. Schedules are always database rows; the broker setting controls
  queued task packages, not the schedule table.

## Testing

- Test task business logic by calling the function directly.
- Test enqueueing with synchronous mode:
  - per call: `async_task("myapp.tasks.fn", arg, sync=True)`
  - per test: override `Q_CLUSTER["sync"] = True`
- For worker/broker integration, run
  the project's `qcluster` command in a separate process and wait for
  `result(task_id, 200)` or a similar bounded wait; do not rely on arbitrary
  sleeps.
- Use `pytest.mark.django_db(transaction=True)` when a real worker process must
  observe committed database rows.

## Debugging Checklist

- Is a `qcluster` process running with the same settings module, `SECRET_KEY`,
  broker URL, and cluster name as the web process?
- Can the worker import the dotted task path?
- Did database migrations run, including `django_q` migrations?
- Is Redis reachable from both web and worker containers, or is the ORM broker
  polling the expected database?
- Did a scheduled task duplicate because setup created another `Schedule` row
  with no stable name?
- Did downtime trigger schedule catch-up?
- Is task failure visible in Django admin, logs, or the configured error
  reporter?

## References

- Official docs: https://django-q2.readthedocs.io/en/master/
- Upstream repo: https://github.com/django-q2/django-q2
