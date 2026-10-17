---
name: django-pagination-performance
description: Improve Django and Django REST Framework pagination for large querysets using bounded page sizes, stable ordering, indexed ordering, offset limits, keyset pagination, DRF CursorPagination, and count-query tradeoffs. Use when list pages, admin views, APIs, exports, or infinite scroll become slow, inconsistent, or memory-heavy as result sets grow.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django Pagination Performance
  category: Django
  tags: django,pagination,performance,querysets,drf
---

# Django Pagination Performance

Use this skill when a Django list view or API slows down as pages get deeper or result sets grow. Pagination is a query-design problem as much as a response-shaping problem.

## Workflow

1. Confirm the list contract.
   - Is arbitrary page access required, or only next/previous?
   - Does the UI need a total count?
   - Can ordering be fixed and stable?
   - What page size limit is acceptable?

2. Measure the current query.
   - Capture SQL for the page query and count query.
   - Check ordering, indexes, and high page numbers.
   - Use `QuerySet.explain()` for deep pages.

3. Choose the pagination style.
   - Use Django `Paginator` for moderate result sets and arbitrary page access.
   - Use capped offset pagination when page numbers are useful but deep pages should be limited.
   - Use keyset/cursor pagination for large feeds, timelines, logs, and infinite scroll.
   - Use DRF `CursorPagination` for API next/previous navigation with stable ordering.

4. Make ordering deterministic.
   - Use a unique or nearly unique immutable ordering field.
   - Add a primary-key tie breaker when needed.
   - Ensure the index matches filters plus ordering.

See [pagination-patterns.md](references/pagination-patterns.md) for Django and DRF examples.

## Safety Notes

- Deep `LIMIT/OFFSET` pages can be slow because the database still walks skipped rows.
- Unordered querysets produce inconsistent pages.
- Cursor pagination restricts arbitrary page jumps and user-controlled ordering.
- Large exact counts can dominate list latency.

## Verification

Measure first page, representative deep page, count query, and insertion/deletion consistency for the chosen pagination contract.
