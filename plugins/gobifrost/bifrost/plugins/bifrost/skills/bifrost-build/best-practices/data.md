# Data Practices: Tables, Policies, Files, Configs

`references/tables.md` and `references/files.md` explain the surfaces and their Python/web differences. This file is the set of decisions that prevent exposure, duplication, and silent data loss.

## Tables

### Policies are the only boundary for browser access

**Rule:** Any table an App reads or writes through `useTable` / `tables.*` must carry explicit `policies` before the App ships. New tables start with admin bypass only. Write a rule per action, keyed on the caller, and test with a user who should see rows and one who should not.

**Why:** An App talks to the table directly; there is no workflow in between to filter. `{"actions": ["read"], "when": null}` means every authenticated user in scope reads every row.

```yaml
# tables/tickets.policies.yaml  (bifrost tables create --name tickets --policies @tables/tickets.policies.yaml)
policies:
  - name: own_org_read
    actions: [read]
    when: { eq: [{ row: organization_id }, { user: organization_id }] }
  - name: owner_write
    actions: [create, update, delete]
    when: { eq: [{ row: created_by }, { user: user_id }] }
  - name: service_desk_all
    actions: [read, update]
    when: { call: has_role, args: ["service_desk"] }
```

References available: `{row: id|organization_id|created_by|updated_by|created_at|updated_at|<data field>}`, `{user: user_id|email|organization_id|is_platform_admin|role_ids|role_names}`, `{call: has_role, args: [...]}`, and `{claims: <name>}` as the right-hand side of `in`. Operators are the JSON AST (`and`, `or`, `not`, `eq`, `neq`, `lt/lte/gt/gte`, `in`, `is_null`); there is no string DSL to inject into.

### Decide who may write, not just who may read

**Rule:** Grant `create`/`update`/`delete` to the narrowest principal; prefer "creator only" (`row.created_by == user.user_id`) or a role. Remember `update` is evaluated against the pre-update row, so state-transition rules ("cannot un-finalize") belong in a workflow.

**Why:** A read-only portal with a permissive write rule lets a customer edit another customer's record from the browser console.

### Store the grant, then let a claim read it

**Rule:** When access depends on more than the caller's org or role (sites, categories, accounts), materialize one grant row per `(user_id, composite_key)` in a table the user can read only for their own rows, define a `list` claim that selects the key, and compare the protected table's key with `{"in": [{"row": "access_key"}, {"claims": "<claim>"}]}`.

**Why:** Claims select one scalar per source row; separate per-dimension claims lose pairings and create a Cartesian product. Policies cannot join tables, so the join is denormalized into the grant row.

```bash
bifrost claims create --name allowed_site_keys --type list \
  --query '{"table": "site_grants", "where": {"eq": [{"row": "user_id"}, {"user": "user_id"}]}, "select": "access_key"}'
```

### Stable IDs and natural keys; upsert for idempotency

**Rule:** Choose the row ID up front when the row represents an external or natural entity (`tables.upsert("devices", external_id, data)` / `tables.insert(..., id=...)`); use `bulk_upsert` for sync jobs. Reserve plain `insert` for genuinely new, user-created rows.

**Why:** Sync and triggered workflows re-run; `insert` keyed on nothing produces duplicates and no way to update.

```python
await tables.bulk_upsert("devices", [{"id": d["external_id"], "data": project(d)} for d in page])
```

### Query with the DSL, bounded, ordered, paged

**Rule:** Build `where` from typed values (`{"status": {"eq": status}}`, `{"id": {"in_": ids}}` in Python / `in` in TypeScript). Always pass `limit`, an explicit `order_by`, and paginate with `after_document_id` (Python) or `page`/`pageSize` (web). Do not accept a caller-built `where` dict as a workflow parameter.

**Why:** The DSL is safe against injection, but a caller-supplied filter still lets the caller choose what to read; `limit` defaults to 100 and caps at 1000, so "fetch all" is both slow and wrong.

```python
# Bad: caller decides the predicate.
@workflow
async def search(where: dict) -> dict:
    return await tables.query("tickets", where=where)

# Good: parameters mapped onto a fixed predicate.
@workflow
async def search(status: str = "open", limit: int = 50) -> dict:
    status = status if status in {"open", "closed"} else "open"
    return await tables.query("tickets", where={"status": {"eq": status}}, order_by="updated_at", order_dir="desc", limit=min(limit, 200))
```

`contains`, `starts_with`, `ends_with`, `has_key` work in one-shot queries, not in `useTable` live filters; `ilike` does not exist.

### Know which `delete` you are calling

**Rule:** In Python, `tables.delete_document(table, id)` removes a row and `tables.delete(table_id)` drops the table. In the web SDK, `tables.delete(table, id)` removes a row. Write a test that would fail if the wrong object were deleted before shipping a destructive path.

**Why:** The Python name collision has destroyed tables in development.

### Project before you return

**Rule:** Workflows return `{"id": doc.id, **selected_fields}`; do not spread `doc.data` wholesale when the row holds fields the caller should not see (internal notes, cost, other users' IDs).

**Why:** Table rows accumulate fields over time; a workflow that returns the whole document leaks the next field someone adds.

## Files

### Paths come from your layout and immutable IDs

**Rule:** Compose managed-file paths from a fixed prefix and UUIDs: `documents/orgs/<org UUID>/sites/<site UUID>/<doc UUID>.pdf`. Store the human filename in a table row. Never place a user-supplied name, or any string containing `/` or `..`, into a path.

**Why:** Policies evaluate the resolved path; a traversal that lands inside a permitted prefix passes. UUID paths also survive renames without rewriting policies or grants.

```python
# Bad
await files.write_bytes(f"uploads/{customer}/{upload.filename}", data, location="documents")

# Good
path = f"documents/orgs/{context.org_id}/{doc_id}.pdf"
await files.write_bytes(path, data, location="documents")
await tables.insert("documents", {"doc_id": doc_id, "display_name": upload.filename, "path": path})
```

### Grant file access by prefix, with `list` separate from `read`

**Rule:** Write file policies per action on the narrowest prefix; use `path_within_any` with a list claim for dynamic hierarchies; grant `list` only where enumeration is intended (navigate via an authorization-filtered table instead).

**Why:** `read` on a document does not imply `list` on its parent; a broad `list` rule reveals every sibling's existence.

```json
{
  "policies": [
    {
      "name": "read_granted_documents",
      "actions": ["read"],
      "when": { "path_within_any": [{ "file": "path" }, { "claims": "allowed_document_prefixes" }] }
    }
  ]
}
```

### Signed URLs are short-lived capabilities

**Rule:** Issue `files.get_signed_url(path, method="GET"|"PUT", content_type=..., location=..., expires_in=600)` from a workflow only after the workflow has verified the caller may access that specific path, and return the URL to the requesting user only. Keep `expires_in` at minutes, set `content_type` for uploads, and never store a signed URL in a table or log.

**Why:** A signed URL bypasses policy checks for its lifetime; a long-lived or logged one is a leaked file.

### Validate uploads before trusting them

**Rule:** For browser uploads via `files.upload(path, blob, {location, contentType})` or a signed PUT, enforce size and content type in the policy-protected location design and re-validate in any workflow that processes the file (magic bytes for PDFs/images, size caps, no execution of content).

**Why:** A content-type header is caller-controlled; processing a disguised file is the classic path to a worker compromise.

### Solution locations and runtime data

**Rule:** Declare each location in `.bifrost/files.yaml` with a business name; write runtime files only through `files.*` with `location=`; never treat `workspace` as a data location and never put user data under app or workflow source.

**Why:** Deploy owns declarations and preserves runtime bytes; files written to source paths are replaced on the next deploy.

## Configs and secrets

### Read with a default; fail clearly when a required value is missing

**Rule:** `config.get(key, default=...)` for optional settings; for required ones, raise a message naming the key and where to set it.

**Why:** A `None` that propagates into an API URL surfaces as a confusing downstream error instead of "set `psa_api_url` under Configs".

```python
api_url = await config.get("psa_api_url")
if not api_url:
    raise RuntimeError("Config 'psa_api_url' is not set for this organization")
```

### Secret values never leave the workflow

**Rule:** Store secrets with `config.set(key, value, is_secret=True)` only from an explicit admin workflow or the CLI/UI, and consume them only to make calls. Do not return, log, compare-and-echo, or place them in results, tables, files, prompts, or App code.

**Why:** Results and logs are visible to the caller; `is_secret` encrypts at rest and triggers output redaction for values fetched via `config.get()`, but it cannot protect a value you copied elsewhere.

### `config.set()` / `delete()` mutate shared environment state

**Rule:** Treat config writes like mapping writes: explicit admin workflows, named in the plan and handoff, never in a user-facing request path. From a Solution workflow they still write the shared org/global namespace, not private install storage.

**Why:** A workflow that "caches" a value with `config.set()` on every run overwrites operator-set configuration and shows up as unexplained config churn.

## Checklist

- Every App-accessed table has read and write policies tested with an allowed and a denied user.
- Multi-dimension access uses grant rows + one list claim with a composite key.
- Natural-key rows use `upsert`/`bulk_upsert`; queries bounded, ordered, paged; no caller-built `where`.
- Delete calls target the intended object and a test proves it.
- File paths built from prefixes + UUIDs; `list` granted deliberately; signed URLs short-lived and never stored.
- Required configs fail with a named key; secrets never leave the workflow; config writes are admin-only and reported.
