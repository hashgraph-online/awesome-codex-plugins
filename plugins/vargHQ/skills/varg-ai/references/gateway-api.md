# varg API Reference (v2)

The varg API at `api.varg.ai/v2` is a unified REST API for generating images, videos, speech, music, and full rendered videos with a single API key. Use this for one-off asset generation without building a full TSX template, or `POST /v2/render` for cloud rendering.

## Authentication

```
Authorization: Bearer varg_xxx
```

Get your API key at https://varg.ai/dashboard/api. Only `GET /v2/pricing` is public.

## Base URL

```
https://api.varg.ai/v2
```

---

## Core concepts

| Concept | Example | What it is |
|---------|---------|------------|
| **Tool** | `image`, `video`, `speech` | A capability with its own endpoint (`POST /v2/image`) |
| **Model** | `seedance_2_5`, `nano_banana_2_1` | The `model` field. One model can be served by multiple providers |
| **Provider** | `fal`, `elevenlabs` | Who runs the generation. varg picks automatically, or pin with `fal:flux_schnell` |

Model ids use underscores (`seedance_2_5`, `nano_banana_2_1`). Dashed spellings (`seedance-2-5`) are accepted and normalized. Full list: `https://varg.ai/models/llms.txt`.

---

## Generation endpoints

All return `202 Accepted` with a job. Poll `GET /v2/jobs/{id}` until terminal.

### Generate Image

```bash
POST /v2/image
```

```json
{
  "model": "nano_banana_2_1",
  "prompt": "a sunset over mountains, cinematic, golden hour",
  "aspect_ratio": "16:9"
}
```

Image editing: send a source image in `files` with `nano_banana_2_1` or `gpt_image_2_5` (both edit when `files` are present). Upscaling: `clarity_upscaler`, `aura_sr`, `topaz`.

### Generate Video

```bash
POST /v2/video
```

```json
{
  "model": "seedance_2_5",
  "prompt": "a bird soaring over mountains, aerial shot",
  "duration": 5,
  "aspect_ratio": "16:9"
}
```

Image-to-video (start frame in `files` — varg routes to the model's i2v variant automatically):
```json
{
  "model": "seedance_2_5",
  "prompt": "person starts walking forward",
  "files": [{ "url": "https://s3.varg.ai/files/acc_x/character.png" }],
  "duration": 5
}
```

Lipsync (image or video + audio in `files`): `veed_fabric_1_0`, `minimax_h3_max_lipsync`, `sync_v3`, `omnihuman_v2`. Video upscale: `topaz_video`, `seedvr_video`.

### Generate Speech

```bash
POST /v2/speech
```

```json
{
  "model": "eleven_v4",
  "text": "Welcome to our product showcase.",
  "voice": "rachel"
}
```

### Generate Music

```bash
POST /v2/music
```

```json
{
  "model": "mureka_9_5",
  "prompt": "upbeat electronic, rising energy",
  "duration": 15
}
```

### Transcribe Audio

```bash
POST /v2/transcription
```

```json
{
  "model": "whisper",
  "audio_url": "https://example.com/audio.mp3"
}
```

### FFmpeg operations

One endpoint, operation selected by `model`:

```bash
POST /v2/ffmpeg
```

| Model | Operation | Key fields |
|-------|-----------|------------|
| `trim` | Trim | `url`, `start`, `end` or `duration`, `precise` |
| `resize` | Resize | `url`, `width`/`height`, `fit` (cover/contain/stretch) |
| `slice` | Slice into segments | `video_url`, `every`/`at`/`count`/`ranges`, `thumbnails` |
| `ffmpeg` | Generic command | `command` with `{{in_1}}`/`{{out_1}}`, `input_files`, `output_files` |

```json
{
  "model": "trim",
  "url": "https://s3.varg.ai/files/acc_x/video.mp4",
  "start": 2.5,
  "duration": 5
}
```

All ffmpeg ops cost ~6 credits. To probe media metadata (dimensions, duration) synchronously without a job, use `POST /v2/files/probe` with `{"url": "..."}`.

### Render (cloud video composition)

```bash
POST /v2/render
```

```json
{
  "code": "<TSX code string with export default>",
  "mode": "strict",
  "output": "video",
  "verbose": false
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | `string` | Yes | TSX code with `export default` returning a `<Render>` element |
| `mode` | `"strict" \| "preview"` | No | `"preview"` uses placeholders for failed generations |
| `output` | `"video" \| "frames"` | No | `"frames"` skips stitching for image-only renders |
| `verbose` | `boolean` | No | Detailed logging (default: false) |

Render is a regular job — poll `GET /v2/jobs/{id}`, final video at `output.outputs[0].url`. Billing: flat ~5 credit stitching fee + each AI sub-generation billed as its own job. See [cloud-render.md](cloud-render.md) for the full workflow and TSX format.

### Upload File

```bash
POST /v2/files
Content-Type: image/jpeg        # the file's media type
X-Filename: photo.jpg           # optional
X-Content-Hash: sha256:<hex>    # optional, enables dedup
```

Raw binary body. **Max 200MB.** Returns `{"file_id": "file_xxx", "url": "https://s3.varg.ai/...", ...}`.

Import by URL instead of uploading bytes:

```bash
POST /v2/files/import
{"url": "https://example.com/photo.jpg"}
```

Dedup pre-check before uploading: `GET /v2/files/check?hash=sha256:<hex>`.

---

## Job Lifecycle

```
queued → submitting → running → completed | failed | cancelled
```

All generation endpoints return `202 Accepted` with a job:

```json
{
  "id": "job_a1b2c3d4e5f6",
  "status": "queued",
  "tool": "video",
  "input": { "model": "seedance_2_5", "prompt": "..." },
  "estimated_cost_cents": 221,
  "pricing": { "estimated": 221, "billing": "metered" },
  "urls": {
    "self": "https://api.varg.ai/v2/jobs/job_a1b2c3d4e5f6",
    "status": "https://api.varg.ai/v2/jobs/job_a1b2c3d4e5f6/status",
    "cancel": "https://api.varg.ai/v2/jobs/job_a1b2c3d4e5f6/cancel",
    "retry": "https://api.varg.ai/v2/jobs/job_a1b2c3d4e5f6/retry"
  }
}
```

### Poll for Result

```bash
GET /v2/jobs/{id}
```

When `status: "completed"`, the result is in `output.outputs[]`:

```json
{
  "id": "job_a1b2c3d4e5f6",
  "status": "completed",
  "output": {
    "version": "v1",
    "outputs": [
      {
        "url": "https://s3.varg.ai/files/acc_x/file_abc.mp4",
        "file_id": "file_abc123",
        "media_type": "video/mp4",
        "thumbnail_url": "https://s3.varg.ai/thumbs/file_abc123.jpg"
      }
    ]
  },
  "actual_cost_cents": 221
}
```

Lightweight polling (includes `progress` 0..1 and `progress_message`):

```bash
GET /v2/jobs/{id}/status
```

There is **no SSE stream** — poll, or use webhooks.

### Webhooks (instead of polling)

Add `options.webhook_url` to any generation request. When the job reaches a terminal status, varg POSTs the job snapshot to your URL, signed with `X-Varg-Signature: v1=<hmac-sha256>`, with 8 retries.

```json
{
  "model": "seedance_2_5",
  "prompt": "...",
  "options": { "webhook_url": "https://example.com/varg-hook" }
}
```

### Job actions

```bash
POST /v2/jobs/{id}/cancel    # abort a running job (409 if terminal)
POST /v2/jobs/{id}/retry     # retry a failed job
POST /v2/jobs/{id}/refresh   # force re-poll of the provider
GET  /v2/jobs/{id}/price     # pricing breakdown (estimated/actual/billed_units)
GET  /v2/jobs                # list your jobs
```

### Idempotency

Pass `Idempotency-Key: <any unique string>` on job-creating POSTs. Retrying with the same key returns the existing job (`200`) instead of creating and charging a new one (`202`). Use this to make retries safe.

---

## Tools discovery (for agents)

Discover the API surface at runtime without docs:

```bash
GET  /v2/tools                          # list all tools
GET  /v2/tools/{tool_key}               # input JSON Schema + output shape + worked example
GET  /v2/tools/{tool_key}?model=X       # explicit per-provider options for model X
POST /v2/tools/{tool_key}/call          # generic call (same as POST /v2/{tool_key})
```

---

## Cache Behavior

Identical requests (same model + prompt + parameters) return a completed job instantly with `actual_cost_cents: 0` and `pricing.cached: true`. **Cache hits are free.**

---

## Pricing & Billing

The `*_cost_cents` fields count credits (1 = 1 credit). Flow: **reserve** estimated cost at creation (402 if insufficient) → **commit** on completion → **release** on failure.

```bash
GET  /v2/pricing              # public model catalog with prices (no auth)
POST /v2/estimate             # price a request WITHOUT creating a job (same body as generation)
GET  /v2/billing/balance      # balance breakdown
GET  /v2/billing/usage        # usage records (?from=&to=)
GET  /v2/billing/transactions # ledger (spend/topup history)
```

Balance response:

```json
{
  "available": 8200,
  "reserved": 300,
  "total_balance": 8500,
  "subscription_balance": 5000,
  "rollover_balance": 2000,
  "onetime_balance": 1500
}
```

`available` = total − reserved (what you can spend right now).

---

## BYOK

**BYOK via the API is not available in v2.** The v1 `X-Provider-Key-*` headers were not ported. All API requests bill varg credits. For local rendering with your own provider keys (env `FAL_KEY`, etc.), see [byok.md](byok.md).

---

## TypeScript Client

For programmatic access from TypeScript:

```typescript
import { createVarg } from "vargai/ai"

const varg = createVarg({ apiKey: process.env.VARG_API_KEY! })

// Use as Vercel AI SDK provider
import { generateImage } from "ai"

const result = await generateImage({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: "a sunset over mountains"
})
```

The `vargai/ai` package implements the Vercel AI SDK `ProviderV3` interface, exposing:
- `varg.imageModel(id)` -- returns `ImageModelV3`
- `varg.videoModel(id)` -- returns `VideoModelV3`
- `varg.speechModel(id)` -- returns `SpeechModelV3`
- `varg.musicModel(id)` -- returns `MusicModelV3`

---

## Error Responses

All errors use one envelope:

```json
{
  "error": {
    "code": "insufficient_balance",
    "message": "Insufficient balance to run this job"
  }
}
```

| Status | Code | Meaning |
|--------|------|---------|
| 400 | `invalid_request`, `invalid_json` | Malformed body |
| 401 | `unauthorized` | Invalid or missing API key |
| 402 | `insufficient_balance` | Balance too low to reserve estimated cost |
| 404 | `model_not_found`, `tool_not_found`, `job_not_found`, `file_not_found` | Unknown resource |
| 409 | — | Job already terminal (cancel/refresh) |
| 413 | `file_too_large` | Upload over 200MB |
| 422 | `invalid_request` | Body failed schema validation |
| 429 | `rate_limited` | Too many requests — honor `Retry-After` |
| 503 | `no_pricing` | Model temporarily has no active pricing |

Rate limiting is a sliding window per API key; responses carry `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

---

## Migrating from v1

| v1 | v2 |
|----|----|
| `api.varg.ai/v1` | `api.varg.ai/v2` |
| `job_id` field | `id` field |
| `output.url` (single) | `output.outputs[]` (array, each with `file_id`) |
| `GET /jobs/{id}/stream` (SSE) | Removed — poll or `options.webhook_url` |
| `DELETE /jobs/{id}` | `POST /jobs/{id}/cancel` |
| `GET /balance` | `GET /billing/balance` |
| `GET /usage` | `GET /billing/usage` |
| `POST /ffmpeg/trim` etc. | Single `POST /ffmpeg`, op selected by `model` |
| `POST /ffmpeg/probe` | `POST /files/probe` |
| `GET /voices` | Not ported — pass `voice` by name |
| `render.varg.ai/api/render` | `POST api.varg.ai/v2/render` |
| `X-Provider-Key-*` BYOK headers | Removed |
| Files max 50MB | Max 200MB |
| Flat error shape | `{"error": {"code", "message"}}` envelope |
