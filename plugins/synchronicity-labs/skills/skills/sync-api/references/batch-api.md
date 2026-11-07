<!-- Generated from shared/batch-api.md by scripts/sync_shared.py. Edit the shared file, not this copy. -->

# sync. Batch API

`POST /v2/batch` takes many `/v2/generate` requests in one submission. sync. queues them, tracks every row and gives you one results file, plus a webhook when the batch finishes. Full guide: https://sync.so/docs/api-reference/guides/batch-processing.

## When to use it

The Batch API is for Scale plans and above. A batch holds 20 to 500 rows, or the account's own limit, and each row's inputs can be up to 30 seconds. sync. queues the rows outside the plan's generation concurrency, so a batch doesn't hold up the account's other work, and results can take up to about 24 hours.

Below Scale, `POST /v2/batch` answers `402 plan_feature_unavailable` with `requiredPlan: "scale"`.

## When not to use it

A batch is a queued pipeline for large, slow runs, not a faster way to send a few generations. For a handful of jobs, or any run that should start now, send normal requests side by side instead: one `POST /v2/generate` per job, each with its own idempotency key, keeping at most the plan's concurrency limit in flight. Through the sync. MCP server, `jobs_create-many` does that for 2 or more independent jobs on any paid plan, when the client lists it.

## Validate first

- Always send `dry_run: true` first. It validates the rows against the plan's limits, creates nothing, and returns `{"status": "VALIDATED"}`.
- `400` means too many rows for the plan. `429 concurrency_limit_reached` means too many batches are running. Wait `retryAfterSeconds`, or split the rows. `402 plan_feature_unavailable` means the plan has no batch access: run the rows as normal requests instead.
- Batches only take `/v2/generate` rows, and rows with inputs over 30 seconds may be refused.

## Request

```bash
curl -sS https://api.sync.so/v2/batch -H "x-api-key: $SYNC_API_KEY" -H 'Content-Type: application/json' -d '{
  "rows": [
    {"request_id": "lead-001", "endpoint": "/v2/generate",
     "payload": {"model": "sync-3", "input": [{"type": "video", "assetId": "<videoAssetId>"}, {"type": "audio", "assetId": "<audioAssetId>"}]}}
  ],
  "dry_run": true,
  "webhook_url": "https://example.com/hooks/sync-batch"
}'
```

- `request_id` must be unique within the batch, and links each result line to its row.
- `payload` is the same body as `POST /v2/generate`. Upload local files first and reference them by `assetId`.
- A JSONL file in a multipart `input` field works too, up to 5 MB.
- Batch creation is not idempotent. If a create request times out, list your batches with `GET /v2/batch` before sending it again, so the same rows don't run twice.

## Status and results

- `GET /v2/batch/{id}` returns `status` (`PENDING`, `JOBS_CREATED`, `PROCESSING`, `COMPLETED` or `FAILED`), `metrics` (`total_generations`, `success_count`, `failed_count`, `pending_count`) and `outputUrl`. Check every minute or so. It's slow work, and tight polling doesn't speed it up.
- When it's `COMPLETED`, a `GET` to `outputUrl` with the API key redirects (302) to a signed JSONL file. Fetch that signed URL without the key. Each line holds `request_id`, `status`, `error` and `response`. The video is at `response.output_url`, in snake_case.
- With `webhook_url` set, sync. posts once the batch finishes, signed like generation webhooks (`Sync-Signature`). The notification can arrive more than once, so dedupe on the batch `id`.

## Dialogue edit rows (early access)

On Scale, a large run of one recording personalized many ways, such as one version per recipient's name in the presenter's own voice, can render as batch rows. Make one dialogue-edit preview per variant first (see the edit-dialogue skill). Then submit one row per completed preview: the same source video as the only input, plus `"dialogueEdit": {"id": "<previewId>"}`. This is enabled per organization. The `dry_run` response says whether it's available. Preview requests are limited to 30 a minute, so pace them. For a few variants, or on other plans, render each preview with its own Edit Dialogue video request instead.
