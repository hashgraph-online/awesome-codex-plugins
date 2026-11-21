# Cloud Render Mode

Send TSX code to `POST https://api.varg.ai/v2/render`. No local dependencies needed -- just a `VARG_API_KEY` and `curl`.

The render service handles all asset generation (images, video, speech, music) and video composition (ffmpeg) in the cloud. Rendering is a regular varg job: submit, poll `GET /v2/jobs/{id}`, get the final `.mp4` URL from `output.outputs[0].url`.

## TSX Format

In cloud mode, **no imports are needed**. All components and providers are auto-injected as globals.

**Available globals:**

| Category | Names |
|----------|-------|
| Components | `Render`, `Clip`, `Image`, `Video`, `Speech`, `Music`, `Captions`, `Title`, `Subtitle`, `Overlay`, `Split`, `Grid`, `Slot`, `Slider`, `Swipe`, `Packshot`, `TalkingHead` |
| Providers | `varg` (recommended), `fal`, `elevenlabs`, `higgsfield`, `openai`, `replicate`, `google`, `together` |
| Data | `VOICES` (voice name to ElevenLabs ID mapping) |

The user's `VARG_API_KEY` (from the `Authorization` header) is automatically used for all AI generation calls. No `createVarg()` needed. Use `varg.*` for all models -- same syntax as local render mode.

### Minimal Example

```tsx
const img = Image({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: "a cozy cabin in mountains at sunset, warm golden light",
  aspectRatio: "16:9"
});

export default (
  <Render width={1920} height={1080}>
    <Clip duration={3}>{img}</Clip>
  </Render>
);
```

### Full Example (video + speech + music + captions)

```tsx
const hero = Image({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: "cinematic portrait of a warrior princess, golden hour lighting",
  aspectRatio: "9:16"
});

const scene = Video({
  model: varg.videoModel("seedance_2_5"),
  prompt: { text: "warrior walks forward through misty forest, camera follows", images: [hero] },
  duration: 5
});

const voice = Speech({
  model: varg.speechModel("eleven_v4"),
  voice: "rachel",
  children: "In a world beyond imagination..."
});

export default (
  <Render width={1080} height={1920} fps={30}>
    <Music model={varg.musicModel("mureka_9_5")} prompt="epic orchestral, rising tension" duration={10} volume={0.3} />
    <Clip duration={5}>
      {scene}
      <Title position="bottom">The Last Guardian</Title>
    </Clip>
    <Captions src={voice} style="tiktok" withAudio />
  </Render>
);
```

## Restrictions

- Must have `export default` returning a `<Render>` element
- No named exports (`export const x = ...` is forbidden)
- No external imports (`vargai/*` imports are allowed but stripped -- globals replace them)
- No `require()` calls
- Image `src` values must be `http://` or `https://` URLs
- Max 5 concurrent jobs, 10 requests/minute per user
- 15-minute job timeout

## Workflow

### Step 1: Write TSX code to a file

Write the TSX code to a local `.tsx` file for reference and iteration:

```bash
cat > video.tsx << 'EOF'
const img = Image({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: "a sunset over mountains",
  aspectRatio: "16:9"
});

export default (
  <Render width={1920} height={1080}>
    <Clip duration={3}>{img}</Clip>
  </Render>
);
EOF
```

### Step 2: Submit to render service

```bash
curl -s -X POST https://api.varg.ai/v2/render \
  -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"code\": $(cat video.tsx | jq -Rs .)}"
```

Response (`202 Accepted`) is a standard varg job:

```json
{
  "id": "job_a1b2c3d4e5f6",
  "status": "queued",
  "tool": "render",
  "estimated_duration_ms": 35000,
  "urls": {
    "self": "https://api.varg.ai/v2/jobs/job_a1b2c3d4e5f6",
    "status": "https://api.varg.ai/v2/jobs/job_a1b2c3d4e5f6/status",
    "cancel": "https://api.varg.ai/v2/jobs/job_a1b2c3d4e5f6/cancel"
  }
}
```

> **Note**: The submit and poll examples use [`jq`](https://jqlang.github.io/jq/) for JSON parsing. If `jq` is not available, extract fields with `grep -o '"id":"job_[^"]*"' | cut -d'"' -f4`.

### Step 3: Poll for result

Poll every 10-15 seconds until `status` is `"completed"`, `"failed"`, or `"cancelled"`:

```bash
curl -s https://api.varg.ai/v2/jobs/JOB_ID \
  -H "Authorization: Bearer $VARG_API_KEY"
```

While running, `GET /v2/jobs/JOB_ID/status` gives lightweight progress (`progress` 0..1, `progress_message` like `"stitching 3/8 (40%)"`).

Completed response:

```json
{
  "id": "job_a1b2c3d4e5f6",
  "status": "completed",
  "output": {
    "version": "v1",
    "outputs": [
      {
        "url": "https://s3.varg.ai/files/acc_x/render_abc.mp4",
        "file_id": "file_render_abc",
        "media_type": "video/mp4",
        "thumbnail_url": "https://s3.varg.ai/thumbs/file_render_abc.jpg"
      }
    ]
  },
  "actual_cost_cents": 5
}
```

On success, present `output.outputs[0].url` to the user. AI sub-generation assets are linked to the render job and available via `GET /v2/files` — if the render fails partway, completed assets are still recoverable there.

On failure, the `error` field describes what went wrong:

```json
{
  "status": "failed",
  "error": { "code": "insufficient_balance", "message": "Insufficient balance" }
}
```

Retry a failed render with `POST /v2/jobs/JOB_ID/retry` — cached sub-generations are reused for free.

### Alternative: webhook instead of polling

Add `"options": {"webhook_url": "https://your-server/hook"}` to the request body — varg POSTs the job snapshot when the render finishes (signed `X-Varg-Signature`, 8 retries). There is no SSE stream in v2.

For the full API reference (rate limits, error codes, all endpoints), see [gateway-api.md](gateway-api.md).
