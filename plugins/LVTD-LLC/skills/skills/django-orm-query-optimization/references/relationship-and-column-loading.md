# Relationship And Column Loading

## `select_related()` For Single-Valued Joins

```python
orders = (
    Order.objects
    .select_related("account", "billing_address")
    .filter(status="open")
)
```

Use when each row points to one related row. This joins related tables into the main query.

Good fit:

- `ForeignKey`
- `OneToOneField`
- Serializer fields that read `order.account.name`
- Templates that render one related object per row

## `prefetch_related()` For Many-Valued Relations

```python
from django.db.models import Prefetch

orders = (
    Order.objects
    .filter(status="open")
    .prefetch_related(
        Prefetch(
            "line_items",
            queryset=LineItem.objects.select_related("product").order_by("position"),
        )
    )
)
```

Use when each parent has many children. Django issues a second query and joins results in Python.

Watch for large `IN` clauses and memory use on very large parent querysets.

## Prefetch Cache Trap

This uses the prefetch cache:

```python
for order in orders:
    list(order.line_items.all())
```

This issues new queries because it asks a different question:

```python
for order in orders:
    order.line_items.filter(refunded=False)
```

If the filtered set is needed, put the filter in `Prefetch(queryset=...)` and use `to_attr` if it should not replace the default relation cache.

```python
orders = Order.objects.prefetch_related(
    Prefetch(
        "line_items",
        queryset=LineItem.objects.filter(refunded=False),
        to_attr="active_line_items",
    )
)
```

## Column Loading

Use `values()` when model behavior is unnecessary:

```python
rows = Order.objects.filter(status="open").values(
    "id",
    "account__name",
    "created_at",
)
```

Use `only()` and `defer()` sparingly:

```python
articles = Article.objects.only("id", "slug", "title")
```

They help most when avoiding large text/blob fields or expensive type conversion. They can hurt if deferred fields are later accessed, because each access can issue another query.

## Review Checklist

- Which line evaluates the queryset?
- Which attributes are accessed inside loops, serializers, templates, admin methods, and properties?
- Is the relation single-valued or many-valued?
- Does the optimized queryset preserve ordering and permissions?
- Did the change reduce query count without excessive memory growth?
