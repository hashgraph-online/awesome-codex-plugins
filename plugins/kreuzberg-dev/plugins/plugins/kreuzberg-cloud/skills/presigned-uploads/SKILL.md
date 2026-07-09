---
name: presigned-uploads
description: Use when the user has files larger than ~50 MB to extract via the cloud, or when base64-encoding the body would be wasteful. Covers the three-step presign / PUT / confirm flow against POST /v1/uploads/presign and POST /v1/uploads/confirm.
---

# Presigned uploads

For files larger than about 50 MB, skip the base64-in-JSON body of
`POST /v1/extract` and use the three-step presigned-upload flow instead.
The client uploads bytes directly to object storage, then tells the API to
start processing.

## When to reach for this

- Single file > 50 MB.
- Batch with aggregate body size > 100 MB.
- Bandwidth-constrained environments where double-encoding (base64 + TLS
  - worker) wastes throughput.
- File already lives in S3 / GCS and you can stream rather than buffer.

## The three steps

```text
1. POST /v1/uploads/presign  → batch_id + per-file presigned PUT URLs
2. PUT <upload_url>          → upload each file's bytes directly
3. POST /v1/uploads/confirm  → start extraction, returns job_ids
```

Step 1 returns one `upload_url` per document. Step 3 cannot run until
every PUT in step 2 succeeds.

## Step 1 — presign

```bash
curl -X POST https://api.kreuzberg.dev/v1/uploads/presign \
  -H "Authorization: Bearer $KREUZBERG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {"filename": "scan.pdf", "mime_type": "application/pdf"},
      {"filename": "report.docx", "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    ],
    "config": {"output_format": "markdown"},
    "webhook": {"url": "https://hooks.example.com/x"}
  }'
```

### Response

```json
{
  "batch_id": "batch_550e8400-e29b-41d4-a716",
  "uploads": [
    {
      "job_id": "550e8400-...",
      "upload_url": "https://storage.googleapis.com/kreuzberg-dev-uploads/...",
      "object_key": "projects/abc123/uploads/550e8400-...",
      "method": "PUT",
      "expires_in_secs": 3600
    },
    {
      "job_id": "660e9400-...",
      "upload_url": "https://storage.googleapis.com/kreuzberg-dev-uploads/...",
      "object_key": "projects/abc123/uploads/660e9400-...",
      "method": "PUT",
      "expires_in_secs": 3600
    }
  ]
}
```

Keep the `batch_id` — you need it for step 3. URLs expire in 3600 seconds
(1 hour); upload before then.

## Step 2 — PUT to each upload URL

The presigned URL is signed by Google Cloud Storage; PUT directly to it,
**without** an `Authorization` header. Set `Content-Type` to match the
`mime_type` declared in step 1:

```bash
curl -X PUT "<upload_url>" \
  -H "Content-Type: application/pdf" \
  --data-binary @scan.pdf
```

A successful upload returns `200 OK` with no body. Do this for every
entry in `uploads` before moving on.

## Step 3 — confirm

```bash
curl -X POST https://api.kreuzberg.dev/v1/uploads/confirm \
  -H "Authorization: Bearer $KREUZBERG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"batch_id": "batch_550e8400-e29b-41d4-a716"}'
```

### Response (202)

```json
{
  "job_ids": ["550e8400-...", "660e9400-..."],
  "status": "processing"
}
```

These are the same `job_id` values returned in step 1's `uploads` array.
From here, the flow is identical to `offloading-extraction` — poll
`GET /v1/jobs/{id}` or wait for the webhook.

## End-to-end curl example

```bash
#!/usr/bin/env bash
set -euo pipefail
API="https://api.kreuzberg.dev"
KEY="$KREUZBERG_API_KEY"
FILE="scan.pdf"

# 1. Presign
resp=$(curl -fsS -X POST "$API/v1/uploads/presign" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"documents":[{"filename":"'"$FILE"'","mime_type":"application/pdf"}]}')

batch_id=$(echo "$resp" | jq -r .batch_id)
upload_url=$(echo "$resp" | jq -r '.uploads[0].upload_url')

# 2. PUT
curl -fsS -X PUT "$upload_url" \
  -H "Content-Type: application/pdf" \
  --data-binary "@$FILE"

# 3. Confirm
curl -fsS -X POST "$API/v1/uploads/confirm" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"batch_id":"'"$batch_id"'"}' | jq .
```

## Errors

| Status | Where | Cause |
|---|---|---|
| `400` | presign | Empty `documents`, bad MIME, missing `filename`. |
| `403` | PUT | URL expired (>1h since presign) or `Content-Type` mismatch. |
| `400` | confirm | One or more uploads missing in storage. |
| `401` | presign/confirm | Bad Bearer token. |

If `confirm` returns `400` complaining about a missing upload, retry the
PUT for that specific `object_key` — confirmation requires every file to
be present in storage first.

## When not to use this

For files under ~5 MB, the JSON `data` field is simpler and lower-latency
(one round trip instead of three). See the `offloading-extraction` skill.
