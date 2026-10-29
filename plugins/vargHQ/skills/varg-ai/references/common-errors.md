# Common Errors & Debugging

## Unknown Model / Model Removed

**Error**: `unknown model`, 404 or 422 naming the model.

**Cause**: The model was renamed or retired. `sora_2`, `sora_2_pro` and `sora_2_remix` are discontinued (OpenAI closed the Sora API on 2026-09-24). `minimax` and `kling_v2_1` are no longer in the catalog. Dotted ids (`seedance_2.5`) are wrong; ids use underscores (`seedance_2_5`).

**Fix**: Pick a current model from [models.md](models.md), or look it up in `https://varg.ai/models/llms.txt`. For Sora-style prompts use `seedance_2_5` or `wan_3`.

---

## Duration Constraint Violations

**Error**: `422 Unprocessable Entity` on a video call.

| Model | Allowed `duration` |
|---|---|
| `seedance_2_5` | integer 4-30 |
| `seedance_2` / `seedance_2_mini` | integer 4-15 |
| `seedance_2_preview` / `seedance_2_fast_preview` | integer 5-15 |
| `wan_3` | integer 2-30 |
| `kling_v4` | integer 3-30 (`kling_v4_flash` up to 20) |
| `kling_v3` / `kling_v2_6` | integer 3-15 |
| `veo_3_1` (+ fast/lite) | **4, 6 or 8 only** |
| `omni_flash_1_1` | integer 3-10 |
| `minimax_h3_max` | 1-15 |
| `kling_v2_5` / `kling_v2` | **5 or 10 only** |

**Fix**: Use an integer in the model's range. For a longer scene, chain several clips (see recipes.md) or use a 30s-capable model (`seedance_2_5`, `wan_3`, `kling_v4`).

---

## Multiple Images in Video Prompt

**Error**: Generation fails, or the extra images are ignored.

**Cause**: `Video({ prompt: { images: [img1, img2] } })` on a model that only does image-to-video from one first frame.

**Fix**: One image = first frame, which every image-to-video model accepts. Several images = references, which only `seedance_2_5` (≤9), `wan_3` (≤10), `kling_v4` (≤7), `omni_flash_1_1`, `grok_imagine_1_5` and `minimax_h3_max` accept. With these, name what each image is in the prompt ("the woman from the first image, in the room from the second image").
```tsx
// Image-to-video, any model
Video({ prompt: { text: "...", images: [singleImage] }, ... })

// Multi-reference, reference-capable models only
Video({ model: varg.videoModel("seedance_2_5"), prompt: { text: "...", images: [character, location] }, ... })
```

---

## Silent Video / Provider Options Ignored

**Error**: You asked for native audio (or a resolution or other option) and the output ignores it. The SDK may warn: `providerOptions.varg contains no provider namespace`.

**Cause**: Options passed as a flat bag. The varg API only forwards options nested under the **underlying provider** key (`fal`, `piapi`, `byteplus`, `elevenlabs`, ...), and drops everything else.

**Fix**:
```tsx
// CORRECT: native audio uses the unified field
Video({ model: varg.videoModel("seedance_2_5"), prompt: "...", audio: "native" })

// CORRECT: provider-specific option, namespaced under the provider
providerOptions: { varg: { fal: { resolution: "720p" } } }

// WRONG: flat bag, silently dropped
providerOptions: { varg: { generate_audio: true } }

// CORRECT only with the direct fal provider (BYOK local render, not createVarg)
providerOptions: { fal: { generate_audio: true } }
```

Each model's spec page (`https://varg.ai/models/<id>.md`) lists its options per provider route. `audio: "native"` needs vargai ≥ 0.4.0-alpha124 (`bunx vargai@alpha`).

---

## JSX Syntax for Media Creation

**Error**: Image/Video/Speech don't generate anything.

**Cause**: Using JSX syntax `<Image prompt="..." />` instead of function calls.

**Fix**: Media generation must use function calls:
```tsx
// CORRECT
const img = Image({ model: varg.imageModel("nano_banana_2_1"), prompt: "..." })

// WRONG
const img = <Image model={varg.imageModel("nano_banana_2_1")} prompt="..." />
```

JSX is only for composition components: `<Render>`, `<Clip>`, `<Music>`, `<Captions>`, `<Title>`, `<Overlay>`, `<Split>`, `<Grid>`, `<Packshot>`.

---

## Image Edit: Missing Images

**Error**: "images is required", or the result ignores the reference.

**Cause**: An `/edit` model (`nano_banana_pro/edit`, `nano_banana_2/edit`, `grok_imagine_image/edit`) called with a plain string prompt, or a reference you meant to keep was never passed.

**Fix**: Pass references as `{ text, images }`. `nano_banana_2_1`, `gpt_image_2_5` and the other current models take both forms. With `images` they edit, without them they generate.
```tsx
// CORRECT: editing / character consistency
Image({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: { text: "same person on a beach", images: [referenceImage] }
})

// WRONG: the reference is never sent, so the face changes
Image({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: "same person on a beach"
})
```

## Legacy nano_banana_pro: Wrong Prompt Format

`nano_banana_pro` (no `/edit`) only takes a plain string. Pass references to `nano_banana_pro/edit` instead, or switch to `nano_banana_2_1`, which takes both.

---

## Music Duration Not Set

**Error**: Video output is unexpectedly long (30-60+ seconds).

**Cause**: `<Music>` without `duration` prop. the music model picks its own length (often 60s+), which extends the entire video.

**Fix**: Always set `duration` to match total video length:
```tsx
<Music model={varg.musicModel("mureka_9_5")} prompt="upbeat" duration={15} />
```

---

## Clip Duration Mismatch

**Error**: Black frames, audio desync, or unexpected pacing.

**Cause**: `<Clip duration={10}>` wrapping a `Video({ duration: 5 })`. The clip duration doesn't match the inner video.

**Fix**: Match clip duration to video duration:
```tsx
const vid = Video({ ..., duration: 5 })
<Clip duration={5}>{vid}</Clip>
```

Or use `cutFrom`/`cutTo` to trim:
```tsx
const vid = Video({ ..., duration: 5 })
<Clip cutFrom={0.3} cutTo={2.5}>{vid}</Clip>
```

---

## 402 Insufficient Balance

**Error**: `"Insufficient balance. Required: X credits, available: Y credits"`

**Cause**: Not enough credits for the requested generation.

**Fix**: 
- Check balance: `GET https://api.varg.ai/v2/billing/balance` (the `available` field)
- Estimate before running: `POST /v2/estimate` with the same body
- Use cheaper models (see [models.md](models.md))

---

## Cache Miss When Prompt Changed Slightly

**Error**: Generation runs again instead of hitting cache, costing additional credits.

**Cause**: Even minor changes to prompts (extra space, different capitalization, reworded sentence) produce a different cache key.

**Fix**: When iterating on a multi-clip render, keep unchanged prompts EXACTLY the same -- character-for-character. Only modify the specific parts that need to change.

---

## Import Statements in Render Service

**Error**: Code fails to evaluate in the render service.

**Cause**: The render service strips import statements and provides globals. Only `vargai/*` imports are allowed.

**Fix for render service**: Don't import anything. All components and providers are auto-provided as globals:
```tsx
// In render service (no imports needed)
const img = Image({ model: varg.imageModel("nano_banana_2_1"), prompt: "..." })
export default <Render>...</Render>
```

**Fix for local CLI rendering**: Use the JSX pragma and imports:
```tsx
/** @jsxImportSource vargai */
import { Render, Clip, Image, Video } from "vargai/react"
import { createVarg } from "vargai/ai"
```

---

## Timeout / Stalled Renders

**Error**: Render job stays in "processing" or times out after 10-15 minutes.

**Cause**: Complex renders with many AI generation calls can take 15+ minutes. Video models like seedance_2_5 take 3-5 minutes per clip (omni_flash_1_1 and minimax_h3_max_turbo are faster).

**Fix**:
- Use `--preview` first to validate structure
- Break very long sequences into separate render jobs
- Use faster/cheaper models for prototyping (flux_schnell, ltx_2_19b_distilled)
- Check job progress: `GET /v2/jobs/{id}/status` (`progress` 0..1, `progress_message`)

---

## Warm-Up Frames in AI Video

**Issue**: First 0.3-0.5 seconds of AI-generated video often contains static/blurry frames as the model "warms up."

**Fix**: Use `cutFrom` on clips to trim these frames:
```tsx
<Clip cutFrom={0.3} duration={4.7}>{video}</Clip>
```

This is especially useful for fast-cut edits and montages.

---

## FFmpeg Composition Failure (exit code 254, 1, etc.)

**Error**: `Failed with exit code 254` during the editly/ffmpeg step, AFTER all AI generation succeeds.

**Common causes**:
1. **Missing output directory** -- the `output/` folder doesn't exist. FFmpeg cannot create directories.
   Fix: `mkdir -p output` before rendering, or use `-o /path/that/exists/video.mp4`.
2. **Corrupted input file** -- a temp file was cleaned up or is 0 bytes.
   Fix: Clear `.cache/ai/` and re-render (regenerates all assets).
3. **FFmpeg version incompatibility** -- very old or very new ffmpeg may not support all filters.
   Fix: Use ffmpeg 6.x-8.x. Run `ffmpeg -version` to check.

**Debugging**: Run with `--verbose` flag to see the full ffmpeg command, then run it manually in your terminal to see the actual stderr error message.

**Note**: The SDK currently swallows ffmpeg stderr (fix pending in vargHQ/sdk#167). Until merged, `--verbose` + manual re-run is the only way to see the real error.

---

## Missing Provider API Key

**Error**: `ELEVENLABS_API_KEY not set` or image/video generation returns "Unauthorized".

**Cause**: Using direct provider imports (`fal`, `elevenlabs` from `"vargai/ai"`) without the corresponding API key in `.env`.

**Fix (recommended)**: Use the `varg` provider with a single key:
- Set `VARG_API_KEY` in `.env`
- Use `varg.imageModel(...)`, `varg.speechModel(...)` etc. instead of `fal.*` / `elevenlabs.*`
- All providers route through `api.varg.ai` -- one key for everything

**Fix -- Option B**: Add individual provider keys to `.env`:
```
FAL_API_KEY=fal_xxxxx
ELEVENLABS_API_KEY=sk_xxxxx
```

**Note**: Bun auto-loads `.env` from the project root. No `dotenv` needed.

---

## Cannot Find Module 'vargai/jsx-dev-runtime'

**Error**: `Cannot find module 'vargai/jsx-dev-runtime'` when running `bun run render`.

**Cause**: The render CLI copies your file to an internal cache directory where the `vargai` tsconfig path alias doesn't resolve correctly. This affects Bun <= 1.3.x.

**Fix -- use relative imports**:
```tsx
/** @jsxImportSource ./sdk/src/react/runtime */
import { Render, Clip, Image, Video, Speech } from "./sdk/src/react/index.ts";
import { fal, elevenlabs } from "./sdk/src/ai-sdk/index.ts";
```

This triggers the CLI's "relative import" code path, which imports your file directly from its original location instead of copying it.

**Alternative**: If your file has no relative imports and no top-level await, the standard `@jsxImportSource vargai` + `"vargai/react"` imports should work via the CLI's cache-copy mechanism.

---

## VEED/Lipsync Videos Regenerate Despite Same Prompts

**Symptom**: VEED lipsync videos regenerate (costing credits + time) even though you didn't change any Video prompts.

**Cause**: The cache key for Video includes the duration and URL of speech segments used as audio input. ElevenLabs TTS is non-deterministic -- re-running `Speech()` with identical text/voice/model can produce audio with slightly different durations (by milliseconds). This changes the cache key for all downstream Video elements.

**Cascade**: Speech re-gen -> different segment durations -> different segment URLs -> different Video cache keys -> all VEED videos miss cache -> full regeneration.

**Fix**: When iterating on visuals, keep the `Speech()` call and all its parameters EXACTLY the same. Don't add/remove/reorder speech lines, don't change the voice or model. If you need to change speech content, expect all lipsync videos to regenerate.

**Cost impact**: Each VEED lipsync video costs 50-80 credits. A 4-clip narrator video wastes 200-300 credits on unnecessary regeneration.
