# Tables and Policies

Bifrost tables store JSON documents with optional schema hints and row-level policies. Design schema, identity, access, and query patterns together before building UI around a table.

Use `../generated/python-sdk-signatures.md` and `../generated/web-sdk-surface.md` for exact signatures.

## Ownership and creation

- A Solution-owned table is declared in its manifest and changed by deploy.
- A loose table is created/updated with the table CLI.
- Table rows are environment data. Review backup/replacement behavior separately from schema deployment.

New tables normally have only an admin-bypass policy. Ordinary users cannot safely read or write until explicit policies exist. Test policies with realistic non-admin callers and with rows that should and should not match.

Choose stable field names and a durable row-ID strategy. Renaming a table breaks SDK lookups by name; search every app/workflow reference before doing it.

## Python and web operations differ

| Intent | Python workflow SDK | Web app SDK | Important difference |
|---|---|---|---|
| Insert one | `tables.insert(name, data)` | `tables.insert(name, data)` | Similar |
| Insert batch | `tables.insert_batch(name, documents)` | `tables.insert(name, [{data, id?}])` | Different method/item shape |
| Upsert one | `tables.upsert(name, id, data)` | `tables.upsert(name, {id, data})` | Positional ID versus object |
| Update row | `tables.update(name, id, data)` | `tables.update(name, id, data)` | Merge update |
| Delete row | `tables.delete_document(name, id)` | `tables.delete(name, id)` | Different method name |
| Delete rows | `tables.delete_batch(name, ids)` | `tables.delete(name, ids)` | Different method name |
| Delete table | `tables.delete(table_id)` | No app-SDK equivalent | Python `delete` destroys the table |
| Query | keyword arguments | one options object | Return/hook shapes differ |
| Filtered count | `tables.count(name, where=...)` | Not supported | Web count is unfiltered |

### Critical delete trap

In Python, `tables.delete(table_id)` deletes the entire table and its data. Delete a row with `delete_document`; delete rows with `delete_batch`.

In the web SDK, `tables.delete(table, idOrIds)` deletes rows and never the table.

Resolve the table and intended row IDs before destructive calls. Add a test that would fail if the wrong object were deleted.

## Python result shape

Python returns models with attribute access:

```python
from bifrost import tables

result = await tables.query(
    "tickets",
    where={"status": "open"},
    order_by="created_at",
    order_dir="desc",
    limit=50,
)

for document in result.documents:
    print(document.id, document.data.get("title"))
```

Use `document.id`, `document.data`, and `result.documents`/`result.total`. Do not subscript `DocumentData` or `DocumentList` as dictionaries.

## Web result shape

Imperative `tables.query()` returns documents with fields nested under `.data`. React `useTable` and `useInfiniteTable` return flattened rows: custom data fields and metadata such as `id` are at the row's top level.

```tsx
import { useTable } from "bifrost";

const { rows, total, loading, error } = useTable("tickets", {
  where: { status: "open" },
  page: 1,
  pageSize: 25,
  order_by: "created_at",
  order_dir: "desc",
});

const firstTitle = rows[0]?.title;
```

Render loading, empty, error, access-denied, and pagination states. Live inserts outside the current page can remain outside the visible window; do not imply that every realtime event appears on the current page.

## Filter DSL

Both SDKs use field-keyed filters. Common operators are `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `is_null`, `has_key`, `contains`, `starts_with`, and `ends_with`.

- Python commonly uses `in_`; TypeScript uses `in`.
- Do not use `ilike`; it is not a valid filter and can be ignored. Use `contains` for case-insensitive substring matching.
- `contains`, `starts_with`, `ends_with`, and `has_key` work in one-shot queries but not in `useTable` live-subscription filters. Use an imperative query when those operators are required.

Test filtering with nulls, types, pagination, ordering ties, and values containing punctuation or mixed case.

## Errors and permissions

Missing rows normally return `None`/`null`; missing tables and denied access may raise surface-specific errors. In the browser, handle `TableNotFoundError` and `TableAccessDeniedError` distinctly when the user can act differently.

Do not treat an empty Python `tables.query()` as proof that a shared table exists: Solution lookup can convert some missing-table reads into an empty list. Validate setup when absence would be an error.

## Claim-backed authorization projections

Use flattened grant rows when access depends on more than one resource dimension. Store immutable UUID components alongside one scalar composite key:

```text
document_access_grants
├── user_id
├── site_id
├── category_id
└── access_key       # "<site UUID>:<category UUID>"
```

The grant table must let a principal read only its own rows. A list claim can then select `access_key`, and the protected table compares it exactly:

```json
{
  "in": [
    {"row": "access_key"},
    {"claims": "allowed_document_access_keys"}
  ]
}
```

Keep this composite boundary for protected rows. Separate `allowed_site_ids` and `allowed_category_ids` claims lose the original pairings and can create an unintended Cartesian product.

The component claims are still useful for reference-data navigation. Policies on site, building, floor, or category catalog tables may compare their UUID field with the matching component claim so the app lists only entitled labels. Build cascading choices from the user's original grant rows to preserve which categories belong to each permitted site. A navigation result never replaces the composite policy on the protected table.

Claims select one scalar field per source row and do not flatten a JSON list. Materialize one grant value per row. Use UUIDs in keys and references so renaming a display label does not rewrite policies, grants, or storage paths.

## Solution scope and shared fallback

Solution context resolves its own table first. With `allow_outbound_access: true`, a miss may fall back by name to an eligible install-org and then global loose table. Shared fallback tables are read-only from the Solution; the flag does not permit row mutation outside the install. Policies still apply after resolution. To reach another install's table directly from your own code, pass `solution=` (install UUID or slug) to `tables.query`/`get`/`insert`; the target's `allow_inbound_access` gate decides. See `solution-resource-access.md`.

Prefer Solution-owned tables for portable features. If relying on a shared table, document the dependency and test local preview and deployed behavior. Read `solution-resource-access.md` for the exact matrix.

## Verification checklist

- Confirm owner, scope, stable name, schema, and ID strategy.
- Verify policies with allowed and denied non-admin callers.
- Test insert, query, update, row delete, empty results, malformed data, and concurrency as relevant.
- Verify web flattened rows versus imperative/Python nested rows.
- Confirm live updates, pagination, and long-content rendering in the app.
- Back up or explicitly approve any destructive schema/table/data operation.
