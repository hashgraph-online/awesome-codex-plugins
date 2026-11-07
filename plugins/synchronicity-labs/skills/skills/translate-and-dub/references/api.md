<!-- Generated from shared/api.md by scripts/sync_shared.py. Edit the shared file, not this copy. -->

# sync. REST API, for when the MCP tools aren't connected

Base URL `https://api.sync.so/v2`. Authenticate every request with `x-api-key: $SYNC_API_KEY`, and keep the key out of chat and logs. Full reference: https://sync.so/docs/llms-full.txt.

## Upload a local file

```bash
SIZE=$(wc -c < ./clip.mp4 | tr -d ' ')
curl -sS https://api.sync.so/v2/assets/upload -H "x-api-key: $SYNC_API_KEY" -H 'Content-Type: application/json' \
  -d "{\"fileName\":\"clip.mp4\",\"contentType\":\"video/mp4\",\"size\":$SIZE}"
# -> {"uploadUrl": "...", "url": "...", "expiresIn": ...}
curl -sS --fail -X PUT -H 'Content-Type: video/mp4' --data-binary @./clip.mp4 "<uploadUrl>"   # no API key on this request
curl -sS https://api.sync.so/v2/assets -H "x-api-key: $SYNC_API_KEY" -H 'Content-Type: application/json' \
  -d '{"url":"<url>","type":"VIDEO"}'
# -> {"id": "<assetId>", ...}
```

## Estimate the cost

```bash
curl -sS https://api.sync.so/v2/generations/estimate -H "x-api-key: $SYNC_API_KEY" -H 'Content-Type: application/json' \
  -d '{"model":"sync-3","duration":12.5}'
# -> {"estimatedGenerationCost": <USD>, "estimatedCredits": <credits or null>, "estimatedFrameCount": ...}
```

`duration` is the billable output length in seconds, which is usually the speech length. Measure it with `ffprobe -v error -show_entries format=duration -of csv=p=0 file` when ffprobe is installed. For a script, estimate about 2.5 words per second and say the quote is approximate.

## Create a generation

Generate one key per intended generation (a UUID), save it, and reuse it on every retry of that same request. Retrying with the same key and body returns the original generation instead of charging twice.

```bash
curl -sS https://api.sync.so/v2/generate -H "x-api-key: $SYNC_API_KEY" -H 'Content-Type: application/json' \
  -H "Idempotency-Key: $KEY" \
  -d '{
    "model": "sync-3",
    "input": [
      {"type": "video", "assetId": "<videoAssetId>"},
      {"type": "audio", "assetId": "<audioAssetId>"}
    ],
    "options": {"sync_mode": "bounce"},
    "outputFileName": "my_clip_v2"
  }'
# -> 201 {"id": "<generationId>", "status": "PENDING", ...}
```

Input variants:

- **Image instead of video** (sync-3 only): `{"type": "image", "url": "..."}` or `{"type": "image", "assetId": "..."}`.
- **A script instead of audio:** `{"type": "text", "provider": {"name": "elevenlabs", "voiceId": "<voiceId>", "script": "Hello there"}}`. List voices with `GET /v2/voices`, and skip any voice that carries a `restriction`.
- **Dubbing:** send only the video input plus `"dubParams": {"providerName": "elevenlabs", "targetLang": "es"}`. `sourceLang` defaults to `auto`.

## Wait for the result

```bash
curl -sS "https://api.sync.so/v2/generate/<generationId>?wait=true&timeout=10" -H "x-api-key: $SYNC_API_KEY"
```

Repeat until `status` is `COMPLETED`, `FAILED` or `REJECTED`. The completed video is at `outputUrl`. For apps, prefer a `webhookUrl` on the create request over polling.

## Errors worth handling

| Response | Meaning | What to do |
| --- | --- | --- |
| 429 `concurrency_limit_reached` | The plan's limit on simultaneous generations is reached. | Wait `retryAfterSeconds`, or until one finishes, then retry with the same key. |
| 402 `generation_plan_duration_exceeded`, `insufficient_credits`, `free_tier_generations_exhausted`, `plan_feature_unavailable` | Plan or balance limit. | Quote the message and stop. Don't retry. |
| 409 `DUPLICATE_SUBMISSION` | An identical unkeyed request was sent in the last 60 seconds. | Poll the returned `generationId`. |
| 409 `IDEMPOTENCY_KEY_CONFLICT` | The key was already used with different inputs. | Restore the original request, or use a new key for a genuinely new generation. |
| 503 or 504 with an unknown outcome | The job may or may not have started. | Retry with the same key, which replays it if it started. Never switch to a fresh key to get around it. |
| 422 | The input was rejected (format, resolution, face selection, model limit). | Explain the message and fix the input. Repeating the same request won't help. |
