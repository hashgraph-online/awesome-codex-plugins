# DB-Side Computation Patterns

## Aggregate Instead Of Counting In Python

```python
from django.db.models import Count, Q, Sum

accounts = Account.objects.annotate(
    open_order_count=Count("orders", filter=Q(orders__status="open")),
    open_order_total=Sum("orders__total_cents", filter=Q(orders__status="open"), default=0),
)
```

Use filtered aggregates when multiple conditional counts or sums are needed from the same relationship.

## `Exists()` For Boolean Flags

```python
from django.db.models import Exists, OuterRef

recent_orders = Order.objects.filter(
    account_id=OuterRef("pk"),
    created_at__gte=cutoff,
)

accounts = Account.objects.annotate(has_recent_orders=Exists(recent_orders))
```

`Exists()` can be more efficient than counting when all you need is yes/no.

## Scalar `Subquery()` For Latest Related Value

```python
from django.db.models import OuterRef, Subquery

latest_order = (
    Order.objects
    .filter(account_id=OuterRef("pk"))
    .order_by("-created_at")
)

accounts = Account.objects.annotate(
    latest_order_total=Subquery(latest_order.values("total_cents")[:1])
)
```

Use a slice to limit a scalar subquery to one row and `values()` to one column.

## Grouping With `values()`

```python
totals = (
    Order.objects
    .filter(created_at__gte=start)
    .values("account_id")
    .annotate(total_cents=Sum("total_cents"))
    .order_by()
)
```

Clear ordering when it would add unintended grouping or sorting work.

## Generated Same-Row Values

```python
from django.db import models
from django.db.models import F
from django.db.models.functions import Cast

class LineItem(models.Model):
    quantity = models.PositiveIntegerField()
    unit_price_cents = models.PositiveIntegerField()
    total_cents = models.GeneratedField(
        expression=Cast(F("quantity"), output_field=models.BigIntegerField()) * F(
            "unit_price_cents"
        ),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )
```

Use `GeneratedField` for deterministic expressions that reference fields in the same row. Check backend restrictions; PostgreSQL requires persisted generated columns and immutable expressions.

## Review Checklist

- Is the computation exact or can it be stale?
- Does the query produce one row per expected object?
- Did `values()`, `annotate()`, and `order_by()` order create the intended grouping?
- Are join and filter columns indexed?
- Would a materialized view or denormalized counter be safer for a hot report?
