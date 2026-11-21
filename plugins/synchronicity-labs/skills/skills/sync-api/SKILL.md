---
name: sync-api
description: Build sync. labs (sync.so) lipsync, dubbing and talking-image generation into an app, backend, script or pipeline with the sync. REST API or the official Python (syncsdk) and TypeScript (@sync.so/sdk) SDKs. Covers API keys, uploads, creating generations with idempotency keys, webhooks with signature checks, polling, models, cost estimates, error handling and concurrency limits. Use whenever code calls or should call the sync. API, for example "add lipsync to my Next.js app", "write a Python script that dubs videos with sync.", "handle sync. webhooks", "why does my sync. request return 429", or reviewing an existing sync. integration. Not for making one video in this chat (lipsync, talking-photo, translate-and-dub).
license: MIT
compatibility: Needs network access and a sync. API key in SYNC_API_KEY. Python 3.8+ or Node 18+ for the SDKs.
---

# Build with the sync. API

[sync. labs](https://sync.so) | [API integration guide](https://sync.so/docs/plugins-and-extensions/agent-skills/sync-api)

Builds a server-side integration that uploads media, saves each request before submitting it, tracks jobs to completion, and retries without starting duplicate paid work.

## Ground rules

- **Server-side only.** The API key goes in `SYNC_API_KEY` on the server, never in browser or mobile code. Browsers talk to your backend, and your backend talks to sync. Keys come from https://sync.so/settings/api-keys.
- **Base URL** `https://api.sync.so/v2`, header `x-api-key`.
- **SDKs:** Python `pip install syncsdk` (`from sync import Sync`), TypeScript `npm i @sync.so/sdk` (`new SyncClient()`). Both read `SYNC_API_KEY`. The SDKs cover generations (`create`, `get`, `list`). Some newer request fields can lag behind the API: image inputs, `dubParams`, `dialogueEdit`, `projectId`, uploads and cost estimates. When the installed SDK's types don't include one, call the endpoint over HTTP as the references show, instead of forcing the types.
- **Docs for anything not covered here:** https://sync.so/docs/llms-full.txt, plus the error catalog at `GET https://api.sync.so/v2/errors`, which needs no key.

## The flow to implement

1. **Get the media into sync.** Public `https://` URLs work directly. For user uploads or local files, use the three-step asset upload (presigned URL, `PUT`, register) and keep the returned asset ID. Don't proxy large files through your own API.
2. **Create the generation** with `POST /v2/generate` (SDK `generations.create`): the `model`, one visual input (video, or an image with sync-3) and one speech input (audio, or text with an ElevenLabs `voiceId`), plus optional `options`, `webhookUrl` and `outputFileName`. Send an `Idempotency-Key` header. Create the key once per user action, store it with your job record before the request, and reuse it on every retry. A retry with the same key and body replays the original generation instead of starting a paid duplicate.
3. **Find out when it's done.** Prefer a `webhookUrl`, and verify the `Sync-Signature` header ([references/webhooks.md](references/webhooks.md)). Keep polling `GET /v2/generate/{id}` as a fallback: with `?wait=true&timeout=10` the server holds the request open up to 10 seconds. Terminal statuses are `COMPLETED`, `FAILED` and `REJECTED`. The video is at `outputUrl`. Copy it to your own storage if you need to keep it.
4. **Handle errors.** Use the table in [references/api.md](references/api.md). The cases that matter most are a `429 concurrency_limit_reached` (wait `retryAfterSeconds`, then retry with the same key), plan and credit errors (stop and tell the user), and unknown outcomes after a timeout (retry with the same key, never a new one).

Full examples: [references/python.md](references/python.md) and [references/typescript.md](references/typescript.md). REST with curl: [references/api.md](references/api.md).

## Choosing options

- **Model:** default to `sync-3`, the most capable: it handles close-ups, profile angles, occlusion and still images. `lipsync-2-pro` and `lipsync-2` cost less per second. Take current model names from `GET /v2/models` rather than hard-coding a list. Get prices from `POST /v2/generations/estimate` (`{"model", "duration"}`), not from constants in code, because pricing differs by plan.
- **`sync_mode`**, for when the audio and video lengths differ: `bounce` (the default), `loop`, `cut_off`, `silence` or `remap`. Expose it to users when they upload mismatched clips.
- **Several faces:** set `options.active_speaker_detection`, for example `{"auto_detect": true}`, or point at the speaker with `frame_number` and `coordinates`.
- **Dubbing:** one video input and `dubParams: {"providerName": "elevenlabs", "targetLang": "es"}`, with no audio input.
- **Different audio on different parts of one video:** use `segments`. See https://sync.so/docs/developer-guides/segments.

## Scale

- Each plan caps how many generations run at once. The 429 response carries `concurrencyLimit` and `retryAfterSeconds`, plus `X-Sync-Concurrency-Limit` and `Retry-After` headers. Queue jobs on your side and keep at most that many in flight. Creating generations is also rate-limited, at about 100 a minute.

## Before you hand the code back

- No key in source, logs or client bundles. `.env` files are ignored by git.
- Every create carries an idempotency key that is stored before the call and reused on retry.
- The webhook handler verifies the signature against the raw body, answers `2xx` quickly, and tolerates duplicate deliveries.
- Long jobs are tracked in your own store with their generation ID, not held in a request that's waiting.
- Test with a short clip first. Generations are billed, so use `POST /v2/generations/estimate` to show the cost before an expensive run.
