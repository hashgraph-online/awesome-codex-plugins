# QuerySet Batch Processing Patterns

## Read Scalar Data Without Model Instances

```python
rows = (
    Order.objects
    .filter(status="open")
    .values("id", "account_id", "total_cents")
)

for row in rows:
    export_row(row["id"], row["account_id"], row["total_cents"])
```

Use `values_list("id", flat=True)` when you need one column.

## Stream Model Instances

```python
for order in (
    Order.objects
    .filter(status="open")
    .select_related("account")
    .iterator(chunk_size=2000)
):
    process(order)
```

If this queryset uses `prefetch_related()`, provide `chunk_size` so Django observes the prefetches during iteration.

## Set-Based Updates

```python
from django.db.models import F

updated = (
    Account.objects
    .filter(plan="trial", trial_days_used__lt=F("trial_days_total"))
    .update(trial_days_used=F("trial_days_used") + 1)
)
```

Use for uniform updates that do not require per-instance hooks.

## Different Value Per Row

```python
batch = []
for account in Account.objects.filter(active=True).iterator(chunk_size=1000):
    account.health_score = calculate_score(account)
    batch.append(account)

    if len(batch) == 1000:
        Account.objects.bulk_update(batch, ["health_score"], batch_size=1000)
        batch.clear()

if batch:
    Account.objects.bulk_update(batch, ["health_score"], batch_size=1000)
```

If `calculate_score()` can be expressed with annotations or SQL expressions, prefer `update()` or `django-db-side-computation`.

## Bulk Inserts

```python
AuditEvent.objects.bulk_create(
    [AuditEvent(account_id=account_id, event_type="sync") for account_id in account_ids],
    batch_size=1000,
)
```

Check the project's database backend before using conflict options. Confirm whether primary keys are populated after insertion in the supported backend/version.

## Batch Job Checklist

- Is per-row `save()` actually required?
- Can the update be expressed as `update()` with `F()`?
- Can export code use `values()` instead of model instances?
- Is queryset caching avoided with `iterator()`?
- Is each transaction small enough for locks, retries, and rollback?
- Are side effects, signals, timestamps, and audit requirements handled intentionally?
