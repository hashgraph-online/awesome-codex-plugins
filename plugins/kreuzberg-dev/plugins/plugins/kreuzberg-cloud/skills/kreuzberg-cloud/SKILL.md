---
name: kreuzberg-cloud
description: >-
  Managed Kreuzberg document intelligence at api.kreuzberg.dev. Use when the
  user wants cloud extraction with webhook delivery, presigned uploads for
  large files, document versioning and diffing, sandbox keys, or per-project
  usage tracking — instead of running the local kreuzberg CLI. Covers
  authentication, the 12 REST endpoints, request/response shapes, error
  model, and SDK options.
license: MIT
metadata:
  author: kreuzberg-dev
  version: "0.1.0"
  repository: https://github.com/kreuzberg-dev/kreuzberg-cloud
---

# Kreuzberg Cloud

Kreuzberg Cloud is the managed extraction API hosted at
`https://api.kreuzberg.dev`. It exposes the same Rust extraction engine as
the local `kreuzberg` CLI, with two extras: jobs are asynchronous (webhook
or polling delivery) and large files go through presigned uploads instead
of in-band base64.

Use this skill when writing code that:

- Hits `api.kreuzberg.dev` directly via HTTP.
- Uses the `@kreuzberg/cloud` (npm) or `kreuzberg-cloud-sdk` (PyPI) SDKs.
- Configures webhooks, sandbox keys, or usage queries.

## v0.1.0 limitation

The `kreuzberg-cloud` plugin v0.1.0 ships **skills only — no MCP server**.
The `kreuzberg-cloud` CLI binary that hosts the MCP server lands in plugin
v0.2.0. Until then, prefer one of:

1. The TypeScript SDK (`@kreuzberg/cloud`) — ESM, tree-shakable, generated
   from the OpenAPI 3.1 spec.
2. The Python SDK (`kreuzberg-cloud-sdk`) — sync + async, `from_sandbox()`
   helper for evaluation.
3. Raw `curl` — every example below shows the curl form first.

## When cloud vs local

| Situation | Use |
|---|---|
| You already have the `kreuzberg` CLI installed and the file is on disk | Local (`kreuzberg` plugin) |
| File is on a remote URL or in S3 / GCS | Cloud |
| Need OCR for languages the local Tesseract install doesn't have | Cloud |
| File is larger than ~50 MB | Cloud (presigned uploads) |
| Want webhook delivery rather than blocking the caller | Cloud |
| Batch of mixed documents with shared options | Either; cloud parallelizes server-side |
| No network access, air-gapped environment | Local |
| Evaluating before committing to install | Cloud sandbox key |

## Getting an API key

Three options, in order of preference for production:

1. **Production key** — sign up at <https://kreuzberg.dev/cloud>, mint a key
   from the dashboard. Format: `sk_live_*`.
2. **Sandbox key** — no signup, 24-hour TTL, 50-page quota, rate-limited to
   10 keys per IP per 24 hours. Format: `sk_sandbox_*`. See the
   `sandbox-keys` skill.
3. **Local `~/.kreuzberg/cloud.toml`** — for shell sessions, put the key in:

   ```toml
   # ~/.kreuzberg/cloud.toml
   api_key = "sk_live_..."
   ```

The plugin's `SessionStart` hook checks `KREUZBERG_API_KEY` env var first,
then `~/.kreuzberg/cloud.toml`, and emits a setup reminder if neither is
present.

## Authentication

Every request — except `POST /v1/sandbox/key` — uses a Bearer token:

```bash
curl https://api.kreuzberg.dev/v1/usage \
  -H "Authorization: Bearer $KREUZBERG_API_KEY"
```

Both `sk_live_*` and `sk_sandbox_*` go in the same header. The server
resolves project context from the key.

## Base URL and versioning

- Base: `https://api.kreuzberg.dev`
- Path prefix: `/v1/` for all extraction, jobs, sandbox, uploads, usage
  endpoints. Health endpoints (`/healthz`, `/readyz`) are unversioned.
- The OpenAPI 3.1 spec is published at
  <https://api.kreuzberg.dev/openapi.json>; full reference at
  <https://docs.kreuzberg.cloud>.

## The 12 endpoints

Twelve operations across seven tag groups:

### health (2)

| Method | Path | Purpose |
|---|---|---|
| GET | `/healthz` | Liveness — returns 200 if the process is up. |
| GET | `/readyz` | Readiness — returns 200 only when downstream deps are healthy. |

Neither requires auth. Use `/readyz` for uptime monitors and `/healthz`
for load-balancer health checks.

### extract (1)

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/extract` | Submit one or more documents (or URLs) for extraction. |

Accepts `application/json` (base64 documents) or `multipart/form-data`
(binary file parts). Returns `202 Accepted` with `job_ids` (extraction
jobs) and `crawl_job_ids` (URL-crawl jobs). Pair with `GET /v1/jobs/{id}`
to retrieve results — or supply a `webhook` block to receive them
asynchronously. See the `offloading-extraction` skill.

### jobs (1)

| Method | Path | Purpose |
|---|---|---|
| GET | `/v1/jobs/{id}` | Get the current status and (if terminal) result of a job. |

Accepts both extraction job IDs and crawl job IDs. Response shape varies:
extraction jobs return `JobResponse`, crawl jobs return `CrawlJobResponse`.
See the `tracking-cloud-jobs` skill.

### documents (4)

| Method | Path | Purpose |
|---|---|---|
| GET | `/v1/documents/{document_id}` | Latest version of a document with its extraction result. |
| GET | `/v1/documents/{document_id}/diff?from={v}&to={v}` | Compute a diff between two versions (sync, async fallback on budget). |
| GET | `/v1/documents/{document_id}/diff/{diff_job_id}` | Poll the status of an async diff job. |
| GET | `/v1/documents/{document_id}/versions` | List all versions of a document (paginated). |

For applications that re-process the same document over time. Each
extraction returns a `document_id` that's stable across versions.

### uploads (2)

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/uploads/presign` | Generate per-file presigned PUT URLs. |
| POST | `/v1/uploads/confirm` | Confirm the uploads and start processing. |

Three-step flow for files larger than ~50 MB: presign → PUT to storage →
confirm. See the `presigned-uploads` skill.

### sandbox (1)

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/sandbox/key` | Mint an ephemeral sandbox API key. |

24-hour TTL, 50-page quota, 10 keys per IP per 24 hours. No auth required.
See the `sandbox-keys` skill.

### usage (1)

| Method | Path | Purpose |
|---|---|---|
| GET | `/v1/usage` | Per-project usage statistics and remaining quota. |

Accepts optional `start` and `end` ISO-8601 query params. Defaults to the
current calendar month. See the `managing-cloud-usage` skill.

## Key request / response shapes

### `ExtractJsonRequest`

```json
{
  "documents": [
    {
      "filename": "invoice.pdf",
      "mime_type": "application/pdf",
      "data": "<base64>"
    }
  ],
  "urls": [
    { "url": "https://example.com/docs" }
  ],
  "options": {
    "extraction_config": {
      "output_format": "markdown",
      "ocr": { "backend": "tesseract", "language": "eng" }
    }
  },
  "crawl_config": {
    "max_depth": 2,
    "max_pages": 50,
    "stay_on_domain": true
  },
  "webhook": {
    "url": "https://example.com/webhook",
    "secret": "shared-hmac-secret",
    "metadata": { "request_id": "abc123" }
  }
}
```

Either `documents` or `urls` is required (or both). `webhook`, `options`,
and `crawl_config` are optional.

### `ExtractResponse` (202)

```json
{
  "job_ids": ["550e8400-e29b-41d4-a716-446655440000"],
  "crawl_job_ids": ["660e9400-f39c-51e5-b827-557766551111"],
  "status": "pending"
}
```

### `JobResponse` (200)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "invoice.pdf",
  "status": "completed",
  "created_at": "2025-12-21T10:00:00Z",
  "processing_time_ms": 1234,
  "result": {
    "content": "Invoice total: $1,234.56",
    "mime_type": "text/markdown",
    "tables": [],
    "images": [],
    "metadata": { "title": "Invoice #12345" }
  }
}
```

### `JobStatus` enum

```text
awaiting_upload | pending | processing | chunking | aggregating
                | completed | partial_success | failed | cancelled
```

Terminal states: `completed`, `partial_success`, `failed`, `cancelled`.
Stop polling when any of those appears.

### `UsageResponse` (200)

```json
{
  "period_start": "2026-05-01",
  "period_end": "2026-06-01",
  "total_pages": 5432,
  "total_documents": 87,
  "total_failed": 2,
  "quota_limit": 100000,
  "quota_remaining": 94568,
  "by_mime_type": {
    "application/pdf": { "documents": 65, "pages": 3200, "failed": 1 }
  }
}
```

## Error model

All errors are JSON with at least an `error` string field. Status codes
follow REST conventions:

| Status | Meaning | Typical cause |
|---|---|---|
| `400` | Bad request | Missing required field, malformed body, invalid UUID. |
| `401` | Unauthorized | Missing or invalid `Authorization` header. |
| `404` | Not found | Job / document ID doesn't exist in this project. |
| `429` | Rate limited | Sandbox-key IP throttle or per-key quota. |
| `500` | Server error | Database failure, worker crash — retry with backoff. |
| `503` | Service unavailable | Downstream dep unhealthy — retry. |

The SDKs surface these as typed exceptions: `AuthError`, `ValidationError`,
`NotFoundError`, `RateLimitError` (carries `retry_after`), `ServerError`,
`TimeoutError`, all extending `KreuzbergCloudError` (Python) /
`KreuzbergError` (TypeScript).

## Concrete examples

### Sandbox onboarding (no signup)

```bash
# Mint an ephemeral key.
curl -X POST https://api.kreuzberg.dev/v1/sandbox/key
# → { "api_key": "sk_sandbox_...", "expires_at": "...", "pages_remaining": 50 }
```

```ts
import { KreuzbergCloud } from "@kreuzberg/cloud";
const client = await KreuzbergCloud.fromSandbox();
const result = await client.extractAndWait({
  file: new Blob(["Hello world"], { type: "text/plain" }),
});
console.log(result.result?.content);
```

```python
from kreuzberg_cloud import AsyncKreuzbergCloud
async with await AsyncKreuzbergCloud.from_sandbox() as client:
    job = await client.extract_and_wait(file=b"hello world")
    print(job.status, job.result and job.result.content)
```

### Single-file extract → poll

```bash
# 1. Submit.
JOB_ID=$(curl -sX POST https://api.kreuzberg.dev/v1/extract \
  -H "Authorization: Bearer $KREUZBERG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {"filename": "invoice.pdf", "mime_type": "application/pdf",
       "data": "'"$(base64 -w0 invoice.pdf)"'"}
    ],
    "options": {"extraction_config": {"output_format": "markdown"}}
  }' | jq -r '.job_ids[0]')

# 2. Poll until terminal.
curl -s https://api.kreuzberg.dev/v1/jobs/$JOB_ID \
  -H "Authorization: Bearer $KREUZBERG_API_KEY"
```

## Other skills

- `offloading-extraction` — full `POST /v1/extract` workflow with options.
- `tracking-cloud-jobs` — polling cadence, webhook signatures.
- `presigned-uploads` — three-step flow for files >50 MB.
- `versioning-documents` — retrieve a document, list its versions, diff two versions.
- `managing-cloud-usage` — quota and per-MIME breakdown.
- `sandbox-keys` — when to recommend sandbox over production keys.

## References

- API docs: <https://docs.kreuzberg.cloud>
- OpenAPI spec: <https://api.kreuzberg.dev/openapi.json>
- TypeScript SDK: <https://www.npmjs.com/package/@kreuzberg/cloud>
- Python SDK: <https://pypi.org/project/kreuzberg-cloud-sdk/>
- Pricing and signup: <https://kreuzberg.dev/cloud>
