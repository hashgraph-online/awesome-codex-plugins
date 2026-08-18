---
name: tracking-cloud-jobs
description: Use when an extraction job has been submitted and the result needs to be retrieved. Covers GET /v1/jobs/{id}, polling cadence with exponential backoff, terminal status detection, and webhook delivery (signature verification, retry semantics).
---

# Tracking cloud jobs

Every `POST /v1/extract` returns a job ID. The actual result arrives one
of two ways:

1. **Polling** — `GET /v1/jobs/{id}` until status is terminal.
2. **Webhook** — a callback you registered at submit time fires when the
   job is done.

Pick polling when latency tolerance is short and you control the caller.
Pick webhooks when you can't block, or when the job runs minutes long.

## Endpoint

```text
GET https://api.kreuzberg.dev/v1/jobs/{id}
Authorization: Bearer $KREUZBERG_API_KEY
```

Accepts both extraction job IDs (from `job_ids`) and crawl job IDs (from
`crawl_job_ids`). The response schema is `JobLookupResponse`, a union of
`JobResponse` (extraction) and `CrawlJobResponse` (crawl).

## Response (200)

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

`result` is `null` until the job reaches a terminal state.

## Status lifecycle

```text
awaiting_upload  →  pending  →  processing  →  chunking  →  aggregating  →  completed
                                                                          →  partial_success
                                                                          →  failed
                                                          (any time)      →  cancelled
```

**Terminal statuses** — stop polling when status is one of:

- `completed` — `result` is populated.
- `partial_success` — `result` is populated; check
  `result.metadata.warnings` for the partial cause.
- `failed` — `result` is `null`; an error was logged server-side.
- `cancelled` — `result` is `null`; the job was cancelled before
  completion.

## Polling cadence

Use exponential backoff capped at 30 seconds. Most extractions finish in
under 5 seconds; large PDFs with OCR may take minutes.

```bash
#!/usr/bin/env bash
set -euo pipefail
JOB_ID="$1"
delay=1
while true; do
  body=$(curl -fsS \
    -H "Authorization: Bearer $KREUZBERG_API_KEY" \
    "https://api.kreuzberg.dev/v1/jobs/$JOB_ID")
  status=$(echo "$body" | jq -r .status)
  case "$status" in
    completed|partial_success|failed|cancelled)
      echo "$body" | jq .; exit 0;;
  esac
  sleep "$delay"
  delay=$(( delay * 2 > 30 ? 30 : delay * 2 ))
done
```

### TypeScript SDK

The SDK does the backoff for you:

```ts
import { KreuzbergCloud } from "@kreuzberg/cloud";
const client = new KreuzbergCloud({ apiKey: process.env.KREUZBERG_API_KEY! });

const result = await client.waitForJob(jobId, {
  timeoutMs: 5 * 60_000,
  pollIntervalMs: 1000, // starting interval; backs off internally
});
console.log(result.status, result.result?.content);
```

### Python SDK

```python
from kreuzberg_cloud import KreuzbergCloud

with KreuzbergCloud(api_key=...) as client:
    job = client.wait_for_job(job_id, timeout=300)
    print(job.status, job.result and job.result.content)
```

## Webhooks

Register a webhook at submit time by including a `webhook` block in the
`POST /v1/extract` body:

```json
{
  "webhook": {
    "url": "https://hooks.example.com/kreuzberg",
    "secret": "32-byte-shared-secret",
    "metadata": { "request_id": "abc123" }
  }
}
```

When the job reaches a terminal status, the server POSTs the full
`JobResponse` (or `CrawlJobResponse`) to `url`. The `metadata` you
supplied is echoed back inside the payload.

### Signature verification

The server signs each webhook delivery with an HMAC computed over the raw
JSON body using `secret`. The signature header name and exact algorithm
(SHA-256, hex-encoded) are documented at <https://docs.kreuzberg.cloud>;
treat them as the source of truth — do not hard-code header names from
this skill.

Verification pattern (Python, illustrative):

```python
import hmac, hashlib
def verify(body: bytes, signature_hex: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_hex)
```

Reject any delivery whose signature does not match. Always pass `secret`
to `POST /v1/extract` for production — unsigned webhooks can be forged.

### Retry semantics

Webhook deliveries retry on non-2xx responses with exponential backoff
over several hours. Keep your handler idempotent — the same `job_id` may
be delivered more than once on transient failures.

### When to prefer webhooks vs polling

| Prefer webhooks | Prefer polling |
|---|---|
| You can run an HTTP server | CLI / one-shot scripts |
| Jobs run minutes long | Jobs finish in seconds |
| Batch of many jobs | A single foreground job |
| Caller can't block | Caller is already blocking |
| You want exactly one delivery per terminal state | You want strict consistency in your own loop |

## Crawl jobs

`GET /v1/jobs/{crawl_job_id}` returns `CrawlJobResponse` (different shape
from `JobResponse`). The crawl job lists each per-document `job_id` that
was spawned; iterate through those to fetch individual extraction results.

## Errors

| Status | Meaning | Action |
|---|---|---|
| `400` | Malformed UUID | Verify the ID came from `job_ids` / `crawl_job_ids`. |
| `401` | Bad API key | Check `Authorization` header. |
| `404` | Job not found | Wrong project key, or job purged. |
| `503` | DB unavailable | Retry with backoff. |
