# Managed Files

Use this reference for application/user data such as uploads, reports, attachments, and generated documents. Do not confuse managed runtime files with source stored in instance `_repo`.

## Choose the correct file kind

| File kind | Owner and authoring path |
|---|---|
| Solution app/workflow source | Local workspace; deploy with the Solution |
| Loose workflow/module/v1 app source | Instance `_repo`; edit with unqualified `bifrost files` commands |
| Solution runtime/user data | A location declared in `.bifrost/files.yaml`; access with Solution context or supported `--solution` CLI options |
| Loose runtime/user data | An instance location plus organization/file-policy scope |

Never edit deployed Solution source through runtime file APIs. Never store user uploads alongside local app source.

## Declare Solution locations

Declare portable location names in `.bifrost/files.yaml`:

```yaml
locations:
  - documents
  - finance
```

Use business/domain names, not internal storage prefixes. `workspace` is reserved and is not a Solution runtime location. Deploy owns the declarations; runtime bytes remain environment data and survive ordinary source edits.

Deploy creates an admin policy at a declared Solution root so platform admins can seed it. This does not grant ordinary users access. Add explicit file policies for the operations and principals the feature requires.

## Access from a v2 app

Use text methods for small text and signed upload/download paths for large or binary browser payloads:

```tsx
import { files, useFiles } from "bifrost";

const listing = useFiles("invoices/", {
  location: "finance",
  includeMetadata: true,
});

await files.write("notes/today.txt", "ready", { location: "finance" });
const note = await files.read("notes/today.txt", { location: "finance" });
await files.upload("photos/job-123.jpg", photo, {
  location: "job-photos",
  contentType: photo.type,
});
const blob = await files.download("exports/report.pdf", { location: "finance" });
```

`useFiles` supplies loading, error, denied, empty, metadata, and refresh state. Render those states deliberately. The app provider carries its app/Solution/org context; do not embed environment IDs in source. Use the browser SDK directly for ordinary policy-checked uploads; add a workflow only when the feature needs server-side validation or orchestration beyond file access.

## Access from a workflow

```python
from bifrost import files

await files.write("reports/status.txt", "ready", location="documents")
content = await files.read("reports/status.txt", location="documents")
pdf = await files.read_bytes("reports/status.pdf", location="documents")
signed = await files.get_signed_url(
    "uploads/input.csv",
    method="PUT",
    location="documents",
)
```

Use `write_bytes`/`read_bytes` for small binary values and signed URLs for large transfers. Consult `../generated/python-sdk-signatures.md` for the exact available options and return types.

## Move files

`files.move` and `files.move_many` relocate files inside one non-workspace location (for example a Solution's `docs` location) without downloading them. Each call runs as one durable `files.move` platform job:
- Bytes are copied server-side.
- The file's metadata row moves with it, so path-prefix file policies grant access at the new path.
- The original is deleted only after the copy is verified.

```python
from bifrost import files

final_path = await files.move("campus-a/plan.pdf", "campus-b/plan.pdf", location="docs")
results = await files.move_many(
    [{"source": "campus-a/a.pdf", "destination": "campus-b/a.pdf"},
     {"source": "campus-a/b.pdf", "destination": "campus-b/b.pdf"}],
    location="docs",
    on_conflict="rename",  # "error" (default) fails an item whose destination exists
)
```

**Requests and authorization**
- Up to 500 items per call, and the summed length of all source and destination paths must be at most 200,000 characters; otherwise the request is a 422. Use `move_many` for more than one file, since every `move` is its own job.
- Each item needs `read` and `delete` on the source and `write` on the destination. These are checked when the job is queued. Under `on_conflict="rename"`, the job also checks `write` on any `name (n)` it copies to, resumes, or adopts, as the requesting user with that user's current roles; a denial is an audited 403 `forbidden` for that item, and any existing copy is kept.
- A Solution install with inbound access disabled refuses moves from callers outside it with an audited 403, as it refuses their reads.
- Items succeed or fail independently. `move_many` returns results in request order, with `status_code` and `error` per item.
- Item status codes are 200, 400, 403, 404, 409 and 500. Per-item error codes include `file_exists`, `no_available_name`, `not_found`, `source_changed`, `destination_changed`, `copy_verification_failed`, `source_delete_unconfirmed`, `source_missing_during_resume` (500), `recovery_ambiguous` (500), `cleanup_failed` (500), `storage_unavailable` (500), `not_attempted` (500) and `internal_error`. A destination path longer than 1993 characters, or whose S3 key (`<location>/<scope>/<path>`) is longer than 2493 characters, is a per-item 400 `path_too_long`; the stored limits are 2000 and 2500, and 7 characters are kept free for a ` (1000)` rename suffix. A 403 is the literal `forbidden`.

**Errors in the Python SDK**
- `files.move` raises `FileMoveError` (with `.status_code`, `.error`, `.job_id`) when the item fails. `files.move_many` does not raise for item failures; check each result's `status_code`.
- If the job itself fails or is cancelled, both raise `FileMoveJobError` (a `RuntimeError`) with `.job_id`, `.code` (for example `storage_unavailable` after 3 consecutive storage failures, or `checkpoint_failed`) and `.results`, the per-item results when the job recorded any (otherwise `None`). Unattempted items carry 500 `not_attempted`.
- If the wait times out, `TimeoutError` is raised and the job may still be running.

**Retries and recovery**
- A retry of the same request is safe. Based on what the interrupted run left behind, it resumes the marked copy, adopts it (`adopted: true`) when the source is already gone, or reports an already moved file as success. `adopted: true` appears on both an adopted copy and an already-moved success.
- A resumed copy is never deleted when it fails, because the earlier run may have issued the source delete. A failed resume leaves the copy for a later retry or for an operator.
- When the source is gone and more than one candidate holds this item's copy (for example, copies of two same-size versions from separate interrupted runs), the item fails 500 `recovery_ambiguous` and every copy is kept for an operator, because nothing durable says which version is newest.

**Timing**
- Moves in one location and scope run one job at a time, so a single move can wait behind a large batch in the same location.
- A calling workflow must set its own `timeout_seconds` high enough. The SDK waits up to 4 hours by default, and the job itself is limited to 4 hours.
- A batch of very large files that would exceed 4 hours should be split.

**Limits and residual risks**
- Browser uploads through signed URLs take no lock:
  - An upload that lands on the **destination** while a copy of 5 GiB or less runs is overwritten. Larger copies refuse instead.
  - An upload that lands on the **destination** after the move has verified its copy there replaces the moved file, exactly as if it had landed just after the move finished. The move still succeeds.
  - An upload that lands on the **source** within milliseconds of its delete is lost.
- A source deleted outside a move is a plain 404. A source without a metadata row cannot be resumed or adopted after an interruption.
- Retrying an identical request while its job is still queued returns that job, including any 403s it recorded, even if the policy has since changed. Only a request from the same user, checked as the same run user with the same Full Access, reuses a job.

**Deployment requirements**
- The bucket credentials need `s3:ListBucket`. Without it, `HeadObject` on a missing key returns 403 instead of 404. The engine treats a 403 as a storage-level error, so the item fails 500 `storage_unavailable` instead of 404. Three consecutive such failures stop the job with `storage_unavailable`, and the remaining items are marked 500 `not_attempted`.
- Configure an `AbortIncompleteMultipartUpload` lifecycle rule on the bucket.
- Keep PgBouncer and Postgres idle-transaction timeouts above the longest single-part copy.

The CLI moves one file: `bifrost files move SOURCE DESTINATION --location docs [--solution INSTALL] [--rename]`.

## CLI boundaries

Unqualified `bifrost files` commands target instance `_repo`/`workspace`. On commands that accept it, `--solution <install>` targets installed Solution runtime files and defaults to the Solution location rules. Check `../generated/cli-reference.md` because not every file verb supports every scope.

The CLI read/write surface is text-only. `files write` replaces the complete file; it is not a patch operation.

## Policies and Solution fallback

File policy checks apply independently at every tier. Grant only the actions required for the path prefix: read, list, write, delete, or signed access as supported by the policy model.

For many dynamic hierarchical grants, use one root file policy with the file-only `path_within_any` predicate and a list claim:

```json
{
  "policies": [
    {
      "name": "read_granted_resources",
      "actions": ["read"],
      "when": {
        "path_within_any": [
          {"file": "path"},
          {"claims": "allowed_resource_paths"}
        ]
      }
    }
  ]
}
```

Back `allowed_resource_paths` with a flattened grant table containing one `user_id` and one `path_prefix` per row. The predicate matches the exact prefix or a slash-delimited descendant; sibling string prefixes do not match. Missing, malformed, non-list, and empty/root claim values fail closed.

Build paths from immutable UUIDs, for example `documents/sites/<site UUID>/categories/<category UUID>/pdf/<document UUID>/file.pdf`. Keep view and source-download representations under different path segments so their grants can differ without per-file claim values. A label rename then changes only reference data.

`path_within_any` is intentionally unavailable to table policies. Use indexed exact composite-key membership for table rows. Also treat `list` separately: permission to a descendant does not imply permission to enumerate every ancestor directory. Prefer an authorization-filtered table for navigation and grant file reads only when opening the selected resource.

With `allow_outbound_access: false`, a Solution can access only its declared owned location. With it enabled, reads/list/exists/signed-read can fall back through eligible install-org and global file tiers. Writes and deletes still target the Solution-owned tier; the flag does not authorize modification of shared files. To read another install's declared location directly, pass `solution=` (install UUID or slug) to `files.read`; the target's `allow_inbound_access` gate decides. See `solution-resource-access.md`.

Read `solution-resource-access.md` for the exact runtime matrix.

## Verification

- Verify the location is declared where required.
- Test an allowed caller and a denied caller when policies matter.
- Exercise empty, missing-file, denied, large/binary, and replacement behavior as relevant.
- Confirm the app does not expose a token, secret, or unrestricted signed URL.
- Treat local-preview file writes as real instance mutations and report seeded/deleted data in the handoff.
