---
name: offloading-extraction
description: Use when the user wants to extract a document via the cloud rather than the local kreuzberg CLI. Covers POST /v1/extract — JSON vs multipart bodies, URL crawls, options block, webhook attachment, and the async response shape.
---

# Offloading extraction

`POST /v1/extract` is the single submit endpoint. It returns `202 Accepted`
with `job_ids` (extraction) and `crawl_job_ids` (URL crawls) — never the
extraction result inline. Pair every submit with either a poll loop
(`tracking-cloud-jobs` skill) or a webhook.

## When to reach for this

- File is on a remote URL.
- File is on disk but the local `kreuzberg` CLI is not installed.
- You want server-side parallelism for a batch.
- The user wants webhook-delivered results to skip blocking.
- File is larger than ~50 MB → use `presigned-uploads` instead — the
  base64 JSON body is too big.

## Endpoint

```text
POST https://api.kreuzberg.dev/v1/extract
Authorization: Bearer $KREUZBERG_API_KEY
Content-Type: application/json | multipart/form-data
```

Returns `202 Accepted` with `ExtractResponse`.

## Three submission shapes

### 1. Base64 JSON (small files, <5 MB recommended)

```bash
curl -X POST https://api.kreuzberg.dev/v1/extract \
  -H "Authorization: Bearer $KREUZBERG_API_KEY" \
  -H "Content-Type: application/json" \
  -d @- <<JSON
{
  "documents": [
    {
      "filename": "invoice.pdf",
      "mime_type": "application/pdf",
      "data": "$(base64 -w0 invoice.pdf)"
    }
  ],
  "options": {
    "extraction_config": {
      "output_format": "markdown",
      "ocr": { "backend": "tesseract", "language": "eng" }
    }
  }
}
JSON
```

### 2. Multipart (binary, recommended for anything over ~1 MB)

```bash
curl -X POST https://api.kreuzberg.dev/v1/extract \
  -H "Authorization: Bearer $KREUZBERG_API_KEY" \
  -F "file=@invoice.pdf;type=application/pdf" \
  -F 'options={"extraction_config":{"output_format":"markdown"}};type=application/json'
```

Add a `webhook` part as a JSON string:

```bash
  -F 'webhook={"url":"https://hooks.example.com/x","secret":"shh"};type=application/json'
```

### 3. URL crawl

```bash
curl -X POST https://api.kreuzberg.dev/v1/extract \
  -H "Authorization: Bearer $KREUZBERG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [{"url": "https://example.com/docs"}],
    "crawl_config": {"max_depth": 2, "max_pages": 50, "stay_on_domain": true},
    "webhook": {"url": "https://hooks.example.com/x"}
  }'
```

URL crawls return `crawl_job_ids` instead of (or alongside) `job_ids`.

## Response (202)

```json
{
  "job_ids": ["550e8400-e29b-41d4-a716-446655440000"],
  "crawl_job_ids": [],
  "status": "pending"
}
```

`status` is always `pending` at submit time; the per-job status is
retrieved via `GET /v1/jobs/{id}`.

## The `options` block

Shape mirrors the local `ExtractionConfig`:

```json
{
  "extraction_config": {
    "output_format": "markdown",
    "ocr": { "backend": "tesseract", "language": "eng+deu" },
    "extract_tables": true,
    "extract_images": false,
    "chunking": { "max_chars": 4000, "overlap": 200 }
  }
}
```

Supported `output_format` values: `markdown`, `text`, `json`, `djot`,
`html`. Default is `markdown`.

## The `webhook` block

```json
{
  "url": "https://hooks.example.com/x",
  "secret": "shared-secret-32-bytes-min",
  "metadata": { "request_id": "abc123", "user_id": "u_42" }
}
```

`secret` is the HMAC key used to sign the webhook payload — see
`tracking-cloud-jobs` for verification. `metadata` is echoed back in the
delivered payload, useful for correlating server-side requests.

## TypeScript SDK

```ts
import { KreuzbergCloud } from "@kreuzberg/cloud";
import { readFile } from "node:fs/promises";

const client = new KreuzbergCloud({ apiKey: process.env.KREUZBERG_API_KEY! });

const data = await readFile("invoice.pdf");
const job = await client.extract({
  file: { name: "invoice.pdf", data, mimeType: "application/pdf" },
  options: { extractionConfig: { outputFormat: "markdown" } },
});
console.log(job.id, job.status);
```

For submit + wait in one call:

```ts
const result = await client.extractAndWait({
  file: { name: "invoice.pdf", data },
});
console.log(result.result?.content);
```

## Python SDK

```python
from pathlib import Path
from kreuzberg_cloud import KreuzbergCloud

with KreuzbergCloud(api_key=os.environ["KREUZBERG_API_KEY"]) as client:
    job = client.extract(file=Path("invoice.pdf"))
    print(job.id, job.status)
```

Submit + wait:

```python
job = client.extract_and_wait(file=Path("invoice.pdf"))
print(job.result.content if job.result else job.status)
```

## Batch submission

JSON: pass multiple entries in `documents`. Multipart: repeat the `file`
part. SDKs expose `extractBatch` / `extract_batch` helpers that fan out
correctly per platform (parallel HTTP for the async Python client,
sequential for the sync one).

## Errors

| Status | Cause | Fix |
|---|---|---|
| `400` | Empty `documents` and `urls` | Provide at least one. |
| `400` | Bad MIME type | Use a real RFC 6838 type, e.g. `application/pdf`. |
| `401` | Missing Bearer | Set `Authorization` header. |
| `413` | Request body too large | Switch to presigned uploads. |
| `429` | Quota or rate limit | Backoff; check `quota_remaining` via `/v1/usage`. |

## Next step

After every submit, hand off to the `tracking-cloud-jobs` skill — cloud
extraction is asynchronous and the result is delivered via either polling
or webhook callback. Never assume a result is ready immediately after the
`202` response.
