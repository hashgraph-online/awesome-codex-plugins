# Django Index Design Patterns

## Model Indexes

```python
from django.db import models

class Order(models.Model):
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE)
    status = models.CharField(max_length=32)
    created_at = models.DateTimeField()
    metadata = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(
                fields=["account", "status", "-created_at"],
                name="order_acct_status_created_idx",
            ),
            models.Index(
                fields=["created_at"],
                condition=models.Q(status="open"),
                name="order_open_created_idx",
            ),
            models.Index(
                fields=["account"],
                include=["status", "created_at"],
                name="order_account_cover_idx",
            ),
        ]
```

Use `condition` for partial indexes and `include` for covering indexes where the backend supports them. PostgreSQL requires immutable functions in index expressions and partial-index conditions.

## PostgreSQL-Specific Indexes

```python
from django.contrib.postgres.indexes import BrinIndex, GinIndex
from django.db import models

class Event(models.Model):
    occurred_at = models.DateTimeField()
    payload = models.JSONField(default=dict)

    class Meta:
        indexes = [
            BrinIndex(fields=["occurred_at"], name="event_occurred_brin"),
            GinIndex(
                fields=["payload"],
                name="event_payload_gin",
                opclasses=["jsonb_path_ops"],
            ),
        ]
```

Use BRIN for very large append-heavy tables where physical order correlates with the indexed value. Use GIN for JSONB containment and other multi-value search patterns. Confirm the exact lookup operator matches the operator class.

## Concurrent Index Migration

```python
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models

class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("orders", "0042_previous"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="order",
            index=models.Index(
                fields=["account", "status", "-created_at"],
                name="order_acct_status_created_idx",
            ),
        ),
    ]
```

Use `RemoveIndexConcurrently` for live PostgreSQL index removal. `CONCURRENTLY` is not supported inside a transaction, so `atomic = False` is required.

## Design Heuristics

- Equality filter plus ordering: index equality columns before the ordered column.
- Range filter plus ordering: test both orders with `EXPLAIN`; the planner may need one shape more than the other.
- Partial index: condition must match the query predicate closely.
- Covering index: include only columns needed to avoid heap fetches; do not include large or frequently updated columns casually.
- Expression index: ensure the query uses the same expression, collation, cast, and operator class.
- JSONB: index the containment/search pattern, not just the field because it "contains JSON."

## Review Checklist

- Does an existing index or constraint already cover the query?
- Is the query frequent and important enough to pay write overhead?
- Does the index name fit database limits and Django naming rules?
- Is the migration safe for production table size and write rate?
- Does the before/after plan prove the intended change?
