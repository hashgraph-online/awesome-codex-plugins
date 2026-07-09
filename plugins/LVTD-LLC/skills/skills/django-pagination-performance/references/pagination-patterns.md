# Pagination Performance Patterns

## Django `Paginator`

```python
from django.core.paginator import Paginator

qs = Order.objects.filter(status="open").order_by("-created_at", "-id")
paginator = Paginator(qs, per_page=50)
page = paginator.get_page(request.GET.get("page", 1))
```

Use when arbitrary page numbers and count semantics matter. Keep querysets ordered for consistent pagination and index the filter/order pattern.

Watch for:

- Slow count queries.
- Slow high page numbers due to `OFFSET`.
- User-supplied page sizes without caps.

## Keyset Pagination

```python
from django.db.models import Q

def order_page(cursor_created_at=None, cursor_id=None, limit=50):
    qs = Order.objects.filter(status="open").order_by("-created_at", "-id")

    if cursor_created_at and cursor_id:
        qs = qs.filter(
            Q(created_at__lt=cursor_created_at)
            | Q(created_at=cursor_created_at, id__lt=cursor_id)
        )

    return list(qs[:limit])
```

Use a deterministic ordering and carry the last row's ordering values as the next cursor. Add a matching index such as `(status, -created_at, -id)` where supported by the backend.

## DRF Cursor Pagination

```python
from rest_framework.pagination import CursorPagination

class OrderCursorPagination(CursorPagination):
    page_size = 50
    ordering = ("-created_at", "-id")
```

DRF cursor pagination is a good default for large append-style API result sets. It supports forward/reverse navigation, not arbitrary page numbers. Restrict user ordering fields if using ordering filters with cursor pagination.

## Count Query Options

When exact counts are expensive:

- Remove count from the API contract if clients only need `next`.
- Cache approximate counts for dashboards.
- Cap accessible offset pages.
- Use cursor pagination where the UI does not need totals.

Do not silently replace exact counts with approximations unless the product contract allows it.

## Review Checklist

- Is there a stable `order_by()`?
- Does the ordering include a tie breaker?
- Does an index support the filter plus order?
- Is page size capped?
- Does the UI truly need total count and arbitrary page jump?
- Have insertions and deletions between page requests been considered?
