# Django Materialized View Patterns

## Migration

```python
from django.db import migrations

VIEW_SQL = """
CREATE MATERIALIZED VIEW account_order_summary AS
SELECT
    account_id,
    count(*) AS order_count,
    sum(total_cents) AS total_cents,
    max(created_at) AS latest_order_at
FROM orders_order
GROUP BY account_id
WITH DATA;
"""

DROP_SQL = "DROP MATERIALIZED VIEW IF EXISTS account_order_summary;"

class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0042_previous"),
    ]

    operations = [
        migrations.RunSQL(VIEW_SQL, reverse_sql=DROP_SQL),
        migrations.RunSQL(
            "CREATE UNIQUE INDEX account_order_summary_pk ON account_order_summary (account_id);",
            reverse_sql="DROP INDEX IF EXISTS account_order_summary_pk;",
        ),
    ]
```

Use separate indexes for consumer filters and ordering if the view is queried in multiple ways.

## Unmanaged Model

```python
from django.db import models

class AccountOrderSummary(models.Model):
    account_id = models.BigIntegerField(primary_key=True)
    order_count = models.BigIntegerField()
    total_cents = models.BigIntegerField()
    latest_order_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "account_order_summary"
```

Do not call `save()` on unmanaged materialized-view models. Keep them read-only in services, admin, and serializers.

## Refresh Command

```python
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

class Command(BaseCommand):
    def handle(self, *args, **options):
        if connection.in_atomic_block:
            raise CommandError("Concurrent materialized view refresh cannot run in a transaction.")

        previous_autocommit = connection.get_autocommit()
        connection.set_autocommit(True)
        try:
            with connection.cursor() as cursor:
                cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY account_order_summary")
        finally:
            connection.set_autocommit(previous_autocommit)
```

Use non-concurrent refresh for initial population or when reads can be blocked during refresh. `CONCURRENTLY` cannot be combined with `WITH NO DATA` and requires at least one unique index using only column names and covering all rows.

## Alternatives To Check First

- Add or change an index.
- Rewrite ORM with annotations, filtered aggregates, `Exists()`, or `Subquery()`.
- Store a denormalized counter updated transactionally.
- Use a normal view if the query is clearer but not expensive.
- Use a reporting replica or warehouse for OLAP-heavy workloads.

## Review Checklist

- What staleness is acceptable?
- Who refreshes the view and how are failures surfaced?
- Can two refreshes overlap?
- Are permissions and migrations safe in every deployment environment?
- Does the unmanaged model exactly match the SQL output?
