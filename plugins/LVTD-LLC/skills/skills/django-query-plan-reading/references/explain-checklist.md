# Query Plan Reading Checklist

## Getting A Plan From Django

```python
qs = Order.objects.filter(account_id=account_id, status="open").order_by("-created_at")
print(qs.explain())
print(qs.explain(analyze=True, verbose=True, buffers=True))
```

Use `analyze=True` only when executing the query is safe. `buffers=True` is PostgreSQL-specific and helps distinguish CPU work from page reads.

## What To Look For

| Plan Cue | Meaning | Common Response |
| --- | --- | --- |
| `Seq Scan` on a large table with selective filter | No useful access path or planner rejected it | Consider matching index or rewrite filter |
| `Index Scan` plus many rows removed by filter | Index finds too broad a set | Consider composite or partial index |
| `Bitmap Heap Scan` | Many index matches batched before heap access | Often fine; check heap blocks and row counts |
| `Sort` before `Limit` | Database sorted more rows than returned | Consider index matching filter plus ordering |
| Estimated rows far from actual rows | Planner statistics are stale or distribution is skewed | Run `ANALYZE`; consider extended stats or query rewrite |
| Nested loop with large inner repetitions | Join strategy may be expensive | Check indexes on join keys and row estimates |
| High heap fetches for index-only scan | Visibility map or selected columns prevent index-only benefit | Vacuum/analyze or revisit covering index expectations |

## Reading Order

1. Start at the most indented leaf nodes.
2. For each node, ask how many rows it produces and whether that matches the estimate.
3. Move outward and identify where rows multiply, sort, group, or get discarded.
4. Focus on the node with the highest actual time contribution, not the first scary-looking scan type.

## Before/After Notes

Keep a compact comparison:

```text
Before: Seq Scan on orders, actual rows 2,850,000, sort on created_at, execution 1380 ms.
After: Index Scan using orders_open_created_idx, actual rows 50, no sort, execution 18 ms.
Why: partial index matches status=open and ordering, so PostgreSQL can stop at LIMIT.
```

## Planner Reality Checks

- Run `VACUUM ANALYZE` or `ANALYZE table_name` in a safe environment when statistics are stale.
- Check table size and predicate selectivity before assuming an index should win.
- Check whether the `WHERE` clause exactly matches a partial index condition.
- Check collation, operator class, casts, functions, and expression shape for functional indexes.
- Check whether selected columns make a covering index realistic.
