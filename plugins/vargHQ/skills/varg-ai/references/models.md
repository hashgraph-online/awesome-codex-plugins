# Model Catalog

All prices are in credits. Never convert them to money: what a credit costs depends on the user's plan.

> **Catalog snapshot: 2026-10-26.** Models change monthly. Before using a model that is not in the tables below, or if a call fails with "unknown model", check the live index: `https://varg.ai/models/llms.txt` (every model, one line each) and `https://varg.ai/models/<model>.md` (full spec: inputs, durations, resolutions, routes). Prices: `GET https://api.varg.ai/v2/pricing` (public) or price the exact request with `POST /v2/estimate` (same body as the generation call, no job created).
>
> Credits below are **typical** prices for the stated settings, worked out from the live pricing rules. Video is billed per second and per resolution, so a 10s 1080p clip can cost 4-5x a 5s 720p clip.

**Quality ranks** come from the Artificial Analysis arenas (artificialanalysis.ai, checked 2026-10-26): T2V = text-to-video with audio, I2V = image-to-video with audio, T2I = text-to-image, Edit = image editing. The top 6-7 video models sit within about 20 Elo of each other, a statistical tie, so choose among them on price, duration and features.

## Quick Reference: Recommended Defaults

| Task | Model | Credits (~) | Why |
|------|-------|-------------|-----|
| **Video (default, hero shots)** | `seedance_2_5` | ~210 per 5s 720p, ~480 per 5s 1080p | Top tier in both T2V (#5) and I2V (tied #1). 4-30s, up to 9 image refs, native audio. |
| Video (best value) | `wan_3` | ~53 per 5s 720p, ~105 per 5s 1080p | **#1 T2V**, top-tier I2V, 2-30s, refs. A quarter of Seedance 2.5's price. |
| Video (long single shot, multi-shot) | `kling_v4` | ~82 per 5s 720p, ~123 per 5s 1080p | Up to 30s, multi-shot prompts, 7 reference elements, keyframes. New, not ranked yet. |
| Video (fast drafts) | `minimax_h3_max_turbo` | ~42 per 5s 1080p | Close to H3 Max quality for half the price. Use it to test motion before paying for hero shots. |
| Video (cheapest with audio) | `grok_imagine_1_5_lite` / `veo_3_1_lite` | ~16 / ~26 per 5s | Previews and throwaway B-roll. |
| Image (default, gen + edit) | `nano_banana_2_1` | ~6 (1K), ~8 (2K), ~16 (4K) | T2I #4, Edit tied #3. One model for generating and editing: pass `{ text, images }` to edit. |
| Image (top quality) | `gpt_image_2_5` | ~11 medium, ~23 high | **#1 T2I and #1 Edit.** Use for hero stills, ads and anything with dense text. |
| Image (cheap) | `muse_image` / `grok_imagine_image` | ~1 / ~3 | Muse is #8 T2I for about 1 credit. |
| Image (logos, SVG) | `ideogram_vector` | ~14+ | Editable SVG output. |
| Speech (default) | `eleven_v4` | ~84 per typical line | #2 TTS arena (tied with #1), 90+ languages, audio tags. |
| Speech (fast, cheap) | `eleven_v4_turbo` | ~42 per typical line | **#1 TTS arena**, ~100 ms latency, half the price of v4. |
| Background music | `mureka_9_5` | ~25 | Instrumental only, the best non-Suno model on the instrumental board. Use it as the BGM bed. |
| Song with vocals/lyrics | `lyria_3_5` | ~11 | Full songs up to ~3 min. Without "instrumental" in the prompt it may add vocals. |
| Talking head (image + audio) | `veed_fabric_1_0` | ~160-470 | Simplest pipeline; `TalkingHead` component supports it. |
| Talking head, long or 2K | `minimax_h3_max_lipsync` | ~10/s at 768P, ~20/s at 1080P | 5s to 15 min of audio, up to 2K. REST/MCP only, not yet wired into `TalkingHead`. |
| Lipsync onto existing video | `sync_v3` | ~105 | Video + audio in, lip-synced video out. |
| Transcription | `whisper_large_v3` | ~6 | Used by `<Captions>`. |

## Video Models

Use with `varg.videoModel("id")`. Credits are for **5 seconds at 720p without native audio** unless noted.

| Model ID | Credits (~5s) | Duration | Resolutions | Native audio | Rank / notes |
|----------|---------------|----------|-------------|--------------|--------------|
| `seedance_2_5` | ~210 (1080p ~480) | 4-30s | 480p/720p/1080p | yes | T2V #5, I2V tied #1. Flagship Seedance: up to 9 images, 3 videos and 3 audio refs. **Default.** |
| `wan_3` | ~53 (1080p ~105) | 2-30s | 480p/720p/1080p | provider option `fal.audio` | **T2V #1**, I2V tied top. First/last frame and refs (≤10 images, ≤5 videos, ≤5 audio). Best value. |
| `heygen_video_1` | ~16 | 5-15s | 480p-2K | built in (see spec) | T2V #4. Strong with people and dialogue, and very cheap. |
| `flux_3_max` | ~89 | 5-20s | 720p/1080p | yes | T2V #6, I2V tied #1. First/last frame and keyframes. |
| `flux_3` | ~89 (1080p ~152) | 5-10s | 720p/1080p | yes | T2V #8. Also does video-to-video. `flux_3_draft` is ~1/3 the price for previews. |
| `minimax_h3_max` | ~42 at 768P, ~84 at 1080P | 1-15s | 480P/768P/1080P | no | T2V #7. Strong prompt adherence. Can sync to an audio track. |
| `minimax_h3_max_turbo` | ~42 at 1080P | 1-15s | 480P/768P/1080P | no | Nearly H3 Max quality at half the price. Good for drafts. |
| `omni_flash_1_1` | ~53 | 3-10s | 720p-4K | built in (see spec) | Google Gemini Omni Flash 1.1. T2V #10, I2V tied top. ~30s generation, the fastest top-tier model. Also edits video. |
| `kling_v4` | ~82 (1080p ~123) | 3-30s | 720p/1080p | yes | Kling 4.0 (Oct 2026). Multi-shot, 7 refs, 10 keyframes, video edit. Not ranked yet. |
| `kling_v4_flash` | ~82 | up to 20s | 720p | yes | Fast Kling 4.0 drafts. |
| `seedance_2` | ~115 | 4-15s | up to 4K | yes | Previous Seedance (T2V #9). Use 2.5 unless you need 4K. |
| `seedance_2_mini` | ~74 | 4-15s | 720p | — | Cheapest Seedance. Strict moderation. |
| `seedance_2_fast_preview` | ~42 | 5-15s | — | — | Legacy Seedance 2 Fast (PiAPI). |
| `seedance_2_preview` | ~53 | 5-15s | — | — | Legacy Seedance 2 (PiAPI). Prefer `seedance_2_5`. |
| `grok_imagine_1_5` | ~74 | 1-15s | up to 1080p | built in (see spec) | T2V #12. Multi-reference. |
| `grok_imagine_1_5_lite` | ~16 | 1-15s | up to 1080p | built in (see spec) | Cheapest video with native audio. |
| `veo_3_1` | ~105 silent / ~210 with audio | 4, 6 or 8s only | 720p/1080p/4K | yes | Google Veo 3.1. T2V #21, better at I2V. `veo_3_1_fast` (~53/~79) and `veo_3_1_lite` (~16/~26) are cheaper. |
| `kling_v3` | ~59 (~88 with audio) | 3-15s (integer) | — | yes | Kling 3.0 Pro, the AA anchor (1000 Elo), clearly below the models above. Kept for existing projects. |
| `kling_v3_standard` | ~59 | 3-15s (integer) | — | yes | Standard tier. |
| `happy_horse` | ~74 | — | 720p/1080p | — | Alibaba. Expressive character motion (T2V #13). |
| `vidu_q4` | ~50 | 3-16s | 540p-4K | yes | Needs an image: first frame, or reference images plus voice clips. No text-only mode. |
| `ltx_2_19b_distilled` | 53 flat | — | — | yes | Uses `num_frames`, not `duration`, and `video_size`, not `aspect_ratio`. |
| `kling_v2_6` | ~59 (~74 with audio) | 3-15s | — | yes | Legacy. |
| `kling_v2_5` / `kling_v2` | 147 | **5 or 10 ONLY** | — | — | Legacy. Any other duration gives a 422 error. |
| `wan_2_5` | 158 | — | — | — | Legacy. Use `wan_3`. |

**Removed:** `sora_2`, `sora_2_pro` and `sora_2_remix` are gone (OpenAI shut the Sora API on 2026-09-24). `minimax` and `kling_v2_1` are no longer in the catalog. Any of these returns "unknown model".

### Video Editing, Extension, Motion Control

| Model ID | Notes |
|----------|-------|
| `seedance_2_5` | Video refs, edit and extend modes (`files` with a video). |
| `kling_v4` | Video edit (video-to-video) and keyframes. |
| `omni_flash_1_1` | Fast video edit (~4 credits/s). |
| `minimax_h3_max_extend` / `minimax_h3_max_turbo_extend` | Continue a clip by up to 15s. |
| `minimax_h3_max_insert` | Insert a new 5-13s scene into existing footage. |
| `minimax_h3_max_recast` | Swap the people in a video for people from up to 4 photos. |
| `minimax_h3_max_relight` / `id_v2v_relight` | Relight a video. |
| `minimax_h3_max_camera_controls` | Keyframed camera moves around a single image. |
| `id_v2v` | Restyle a video from an edited first frame, keeping identity and motion. |
| `kling_v3_pro_motion_control` | Motion transfer from a reference video. |
| `grok_imagine_edit` | Text-prompted video edit (xAI). |
| `topaz_video` / `seedvr_video` / `sima_video_upscaler` | Video upscale. |

### Lipsync / Talking Head Models

No independent leaderboard exists for lipsync, so these recommendations come from varg's own pipelines.

| Model | Pipeline | Credits (~) | Best for |
|-------|----------|-------------|----------|
| `veed_fabric_1_0` | Image + audio -> video | ~160-470 | **Talking heads in TSX** (recommended, works with `TalkingHead`). 480p or 720p. |
| `minimax_h3_max_lipsync` | Image + audio -> video | ~10/s (768P) to ~20/s (1080P) | Long talks (5s-15 min), up to 2K. REST/MCP. |
| `sync_v3` | Video + audio -> video | ~105 | Adding lip movement to an existing clip. `sync_v2` (53) and `sync_v2_pro` (84) are cheaper. |
| `omnihuman_v2` | Image + audio -> video | ~294+ | Full-body gestures, up to 5 min. Replaces `omnihuman_v1_5`. |
| `heygen_avatar_v` | Script -> avatar video | ~1050 | Stock HeyGen avatars. |

**VEED Fabric workflow** (recommended for TSX):
```tsx
const portrait = Image({ model: varg.imageModel("nano_banana_2_1"), prompt: "..." });
const talking = Video({
  model: varg.videoModel("veed_fabric_1_0"),
  keepAudio: true,
  prompt: { images: [portrait], audio: speechSegment },
  providerOptions: { varg: { fal: { resolution: "720p" } } },  // 480p or 720p only
});
```

### Video Prompt Format

**Text-to-video** (string prompt):
```tsx
Video({ model: varg.videoModel("seedance_2_5"), prompt: "a cat playing piano", duration: 5 })
```

**Image-to-video** (object prompt, ONE image = the first frame):
```tsx
Video({
  model: varg.videoModel("seedance_2_5"),
  prompt: { text: "cat starts playing keys", images: [catImage] },
  duration: 5
})
```

**Multi-reference** (several images = references, not a first frame). Only for models that take references: `seedance_2_5` (≤9), `wan_3` (≤10), `kling_v4` (≤7), `omni_flash_1_1`, `grok_imagine_1_5`, `minimax_h3_max`. Other models fail or ignore the extra images.
```tsx
Video({
  model: varg.videoModel("seedance_2_5"),
  prompt: { text: "the woman from the first image walks into the cafe from the second image", images: [character, location] },
  duration: 8
})
```

**Lipsync, image + audio** (recommended, VEED):
```tsx
Video({
  model: varg.videoModel("veed_fabric_1_0"),
  keepAudio: true,
  prompt: { images: [portrait], audio: voiceover }
})
```

**Lipsync, video + audio** (for a pre-animated video):
```tsx
Video({
  model: varg.videoModel("sync_v3"),
  prompt: { video: animatedCharacter, audio: voiceover }
})
```

### Native Audio and Provider Options (video)

```tsx
Video({
  model: varg.videoModel("seedance_2_5"),
  prompt: "...",
  duration: 5,
  aspectRatio: "9:16",
  audio: "native",   // native audio: dialogue, SFX, ambience. Also keeps the audio in the render.
})
```

- **Native audio:** use `audio: "native"` on `Video()`. It sends the unified `audio` field, which works on `seedance_2_5`, `kling_v4`, `kling_v3`, `flux_3`, `flux_3_max` and `veo_3_1`. Over raw REST, send `"audio": true`. Models marked "built in" or "provider option" in the table ignore that field: check their spec page (`https://varg.ai/models/<id>.md`), e.g. `wan_3` takes `providerOptions: { varg: { fal: { audio: true } } }`.
- **Provider options must be namespaced by provider**, e.g. `providerOptions: { varg: { fal: { resolution: "1080p" } } }` or `{ varg: { piapi: { input: { resolution: "1080p" } } } }`. A flat bag such as `providerOptions: { varg: { generate_audio: true } }` is **silently dropped by the API**. Each model's spec page lists its provider options per route.
- **Resolution:** the default is usually 720p. Over REST, pass the unified `"resolution": "1080p"`. In TSX, pass it in the provider namespace of the route that runs the job (see the model's spec page).

---

## Image Models

Use with `varg.imageModel("id")`. Credits are per image.

| Model ID | Credits (~) | Prompt Format | Rank / notes |
|----------|-------------|---------------|--------------|
| `nano_banana_2_1` | ~6 (1K), ~8 (2K), ~16 (4K) | `string` or `{ text, images }` | T2I #4, Edit tied #3. **Default.** Generation and editing in one model: with `images` it edits / keeps the subject consistent. Extreme aspect ratios. |
| `gpt_image_2_5` | ~2 low, ~11 medium, ~23 high, ~43 max | `string` or `{ text, images }` | **#1 T2I and #1 Edit.** Best for text-heavy designs, ads and hero stills. |
| `grok_imagine_image_2` | ~6 (2K ~8) | `string` or `{ text, images }` | T2I #6. Strong text rendering. |
| `muse_image` | ~1 | `string` or `{ text, images }` | T2I #8 (Meta). Can look things up and run code for charts, QR codes and diagrams. Best quality per credit. |
| `flux_3_image` | ~3 (1K) and up, priced per megapixel | `string` or `{ text, images }` | T2I #13. Native 2K/4K, layout control, up to 10 refs. `flux_3_image_klein` is cheaper. |
| `seedream_5_pro` | ~12-16 | `string` or `{ text, images }` | Edit #8 (stronger at editing than at generation). Up to 10 refs. |
| `krea_3` | ~3 (2K ~6) | `string` or `{ text, images }` | Edit tied #3 (Ultra mode). Up to 8 input images. |
| `qwen_image_3` | ~5+ | `string` or `{ text, images }` | Dense text in 12 languages, comics, infographics. |
| `nano_banana_pro` | ~16 (4K ~32) | `string` | Previous default (T2I #11). Kept for cache continuity on existing projects. |
| `nano_banana_pro/edit` | ~16 | `{ text, images }` | Previous edit default. |
| `nano_banana_2` / `nano_banana_2/edit` | ~6-68 | `{ text, images? }` | Superseded by `nano_banana_2_1`. |
| `ideogram_v4_5` | ~3 low, ~6 medium, ~23 high | `string` or `{ text, images }` | Typography and posters. Ranks lower than the models above on general images. Quality, mask and precision go in `providerOptions.varg.fal`. |
| `ideogram_vector` | ~14+ | `string` or image | **SVG output**: logos and icons. |
| `recraft_v4_1_flash` | ~1 | `string` | Very cheap illustration and photo, with palette control. |
| `grok_imagine_image` / `grok_imagine_image/edit` | ~3 | `string` / `{ text, images }` | Cheapest. Good for placeholders. |
| `soul` | ~5 | `string` | Higgsfield character styles (100+ presets). UGC look. |
| `bria_fibo_2` | ~5 | `string` | Trained on licensed data only (commercially safe). |
| `bria_fibo_edit_1_5_virtual_try_on` / `_product_holding` | ~5 | `{ text, images }` | Put garments on a person, or put a product in a hand. |
| `bria_guided_remove_background` | ~4 | image | Background removal with real alpha. |
| `qwen_angles` | ~9 | `{ text, images }` | New camera angle of a subject. |
| `topaz` / `seedvr` / `clarity_upscaler` | ~2-17 | image | Upscaling. |

### Image Prompt Examples

**Text-to-image:**
```tsx
Image({ model: varg.imageModel("nano_banana_2_1"), prompt: "a sunset over the ocean", aspectRatio: "16:9" })
```

**Reference editing / character consistency** (same model, pass the reference in `images`):
```tsx
Image({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: { text: "same person in a tropical beach setting", images: [referenceImage] },
  aspectRatio: "9:16"
})
```

### Aspect Ratios (images and videos)

| Ratio | Pixels | Use Case |
|-------|--------|----------|
| `16:9` | 1920 x 1080 | YouTube, landscape video |
| `9:16` | 1080 x 1920 | TikTok, Reels, Shorts |
| `1:1` | 1080 x 1080 | Instagram feed, square |
| `4:3` | 1440 x 1080 | Classic TV, presentations |
| `3:4` | 1080 x 1440 | Portrait photos |
| `4:5` | 1080 x 1350 | Instagram portrait (recommended for feed) |
| `21:9` | 2520 x 1080 | Cinematic widescreen |

Most models support all standard ratios. Veo 3.1 and Omni Flash support only 16:9 and 9:16.

---

## Speech Models

Use with `varg.speechModel("id")`. Speech is billed per character; the credits below are for a typical sentence or two. Use `POST /v2/estimate` with your actual `text` for the real price.

| Model ID | Credits (~) | Rank / notes |
|----------|-------------|--------------|
| `eleven_v4_turbo` | ~42 | **#1 TTS arena.** ~100 ms latency, half the price of v4. |
| `eleven_v4` | ~84 | #2 (tied with Turbo). Most expressive: 90+ languages, audio tags such as `[whispers]` and `[laughs]`, voice clones. **Default.** |
| `gemini_3_8_flash_tts` | ~48 | #5. 130 languages, 30 voices, style instructions, two-speaker dialogue. |
| `gemini_3_8_flash_lite_tts` | ~32 | Cheap: 101 languages. |
| `eleven_v3` | ~210 | Previous gen (#20). v4 is better and cheaper. |
| `eleven_multilingual_v2` | ~210 | Legacy. |
| `eleven_turbo_v2_5` / `eleven_flash_v2_5` | ~105 | Legacy fast models. Use `eleven_v4_turbo`. |
### Available Voices

ElevenLabs default (premade) voices. Pass the `voice_id` directly in the `voice` prop.

| Name | Voice ID | Gender | Accent | Style |
|------|----------|--------|--------|-------|
| Adam | `pNInz6obpgDQGcFmaJgB` | Male | American | Dominant, firm |
| Alice | `Xb7hH8MSUJpSbSDYk0k2` | Female | British | Clear, engaging |
| Bella | `hpp4J3VqNfWAUOO0d1Us` | Female | American | Professional, warm |
| Bill | `pqHfZKP75CvOlQylNhV4` | Male | American | Wise, mature |
| Brian | `nPczCjzI2devNBz1zQrb` | Male | American | Deep, resonant |
| Callum | `N2lVS1w4EtoT3dr4eOWO` | Male | American | Husky, character |
| Charlie | `IKne3meq5aSn9XLyUdCD` | Male | Australian | Confident, energetic |
| Chris | `iP95p4xoKVk53GoZ742B` | Male | American | Charming, casual |
| Daniel | `onwK4e9ZLuTAKqWW03F9` | Male | British | Steady, broadcast |
| Eric | `cjVigY5qzO86Huf0OWal` | Male | American | Smooth, trustworthy |
| George | `JBFqnCBsd6RMkjVDRZzb` | Male | British | Warm, storyteller |
| Harry | `SOYHLrjzK2X1ezoPC6cr` | Male | American | Fierce, character |
| Jessica | `cgSgspJ2msm6clMCkdW9` | Female | American | Playful, bright |
| Laura | `FGY2WhTYpPnrIDTdsKH5` | Female | American | Enthusiastic, quirky |
| Liam | `TX3LPaxmHKxFdv7VOQHJ` | Male | American | Energetic, social media |
| Lily | `pFZP5JQG7iQjIQuC4Bku` | Female | British | Velvety, refined |
| Matilda | `XrExE9yKIg1WjnnlVkGX` | Female | American | Knowledgeable, professional |
| River | `SAz9YHcvj6GT2YYXdXww` | Neutral | American | Relaxed, informative |
| Roger | `CwhRBWXzGAHq8TQ4Fs17` | Male | American | Laid-back, casual |
| Sarah | `EXAVITQu4vr4xnSDxMaL` | Female | American | Mature, reassuring |
| Will | `bIHbv24MWmeRgasZH58o` | Male | American | Relaxed, optimistic |

**Recommended:** `Sarah`, `Brian`, `Matilda`, `George`, `Jessica` cover most use cases.

> Any valid ElevenLabs `voice_id` can also be passed directly — not limited to this list.

The premade voices work with `eleven_v4`, `eleven_v4_turbo` and the older ElevenLabs models. Gemini TTS uses its own voice names (see its spec page).

### Speech Usage

```tsx
const voice = Speech({
  model: varg.speechModel("eleven_v4"),
  voice: "EXAVITQu4vr4xnSDxMaL",
  children: "Welcome to our product showcase."
})
```

---

## Music Models

Use with `varg.musicModel("id")`. **Always set `duration`.**

| Model ID | Credits (~) | Rank / notes |
|----------|-------------|--------------|
| `mureka_9_5` | ~25 | **Instrumental only.** Tied #3 on the AA instrumental board, the best model on varg for instrumentals. **Default for background music.** Prompt up to 1,024 characters. |
| `lyria_3_5` | ~11 | Google Lyria 3.5. Full songs up to ~3 min **with vocals and lyrics**, or instrumentals. Put structure and lyrics in the prompt, and say "instrumental, no vocals" for a bed. |
| `eleven_music_v2_5` | ~158 | ElevenLabs songs with vocals, 3s-10 min. Ranks below Mureka and Lyria. |
| `music_v1` / `eleven_music` | ~79 | Previous default (ElevenLabs Music v1). Kept for existing projects. |

Suno v6 leads both music boards but is not on varg.

### Music Usage

```tsx
<Music
  model={varg.musicModel("mureka_9_5")}
  prompt="upbeat electronic, rising energy, synth arpeggios"
  duration={15}
  volume={0.3}
  ducking    // Auto-lower under speech
/>
```

**Important**: Always set `duration` on Music. Without it the model picks its own length (often 60s+), which extends the video.

---

## Transcription Models

| Model ID | Credits (~) | Notes |
|----------|-------------|-------|
| `whisper` | 6 | OpenAI Whisper via fal. |
| `whisper_large_v3` | 6 | Whisper large model. Best accuracy per credit. |
| `groq_whisper_large_v3_turbo` | ~53 | Fastest (Groq). |

Live catalog: `GET https://api.varg.ai/v2/pricing` · All model specs: `https://varg.ai/models/llms.txt`.
