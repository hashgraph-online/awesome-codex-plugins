# Using a sheet in later images and video

Limits and field names come from varg's model specs (`https://varg.ai/models/<model>.md`, catalog 2026-10-23) and the public schemas at `https://api.varg.ai/v2/tools/{image|video}?model=<id>`. On varg, every model takes media as top-level `files: [{url}]`; varg maps them to the route's native field. Provider-specific fields go under `provider_options.<provider>` and only apply when that provider runs the job, so pin the route (pass the route key as `model`) when you use them.

## Image models

| Model | Refs on varg | How to name refs in the prompt | Notes |
|---|---|---|---|
| `nano_banana_2_1` | ≤10 `files` | "First reference image is …, second is …" | Tested: whole sheet and face + body crops both held identity in a new scene; style swaps from the sheet work |
| `nano_banana_pro` | ≤10 | same | References only work on the `google:nano_banana_pro` route |
| `gpt_image_2_5` | ≤10 | by content ("the woman in the face photo"); order is unreliable | Strict on swimwear and on "girl"; default output ~1088 px |
| `gpt_image_2` | ≤10 | by content | `provider_options.openai.input_fidelity: "high"` for face preservation |
| `seedream_5_pro` | ≤10 | "the person in image 1" | Best photoreal skin; accepts IP names but keep them out anyway |
| `flux_3_image` | ≤10 | by content | `provider_options.fal.safety_tolerance` (0–4 on varg) |
| `krea_3` | ≤8 | by content | `thinking_mode`, `negative_prompt` |
| `qwen_image_3` | ≤3 | — | Labelled bibles, comic strips |
| `grok_imagine_image_2` | ≤3 | — | Not seed-reproducible |
| `soul`, `phota` | text only on varg (`phota` takes `[[profile_id]]`) | — | Use for a photoreal hero face, then sheet it with an edit model |

Prompt shape for edits: **who each reference is → what changes (scene, pose, light, camera) → a short preserve clause naming the signature details**. Store the preserve clause in the character card and paste it verbatim every time.

## Video models

| Model | Mode | Fields | Ref names | What to feed |
|---|---|---|---|---|
| `seedance_2_5` | reference (≤9 images, ≤3 videos, ≤3 audio) or first frame | `files`; fal route: `image_urls`, `video_urls`, `audio_urls`, `task` | `@image1`, `@video1`, `@audio1` | A ≤6-panel sheet or face + body crops; a voice clip as `@audio1` |
| `kling_v4` | first frame, or elements (≤7) + images (≤10) + videos (≤5) + voices (≤3) | `provider_options.fal.elements[{frontal_image_url, reference_image_urls[1–3]}]`, `image_urls`, `start_image_url` | `@Element1`, `@Image1` | Approved still as first frame; or cropped turnaround as one element (front + 3/4, side, back) |
| `kling_v3_pro_reference_to_video` | reference (≤7) | `image_urls`, `start_image_url`, `end_image_url` | `@Image1` | Crops |
| `wan_3` | reference (≤10 images, ≤5 videos, ≤5 audio) or first frame | `provider_options.fal.reference_image_urls`, `reference_video_urls`, `start_image_url` | "Image 1", "Video 1" | Sheet + a reference video for swaps |
| `vidu_q4` | reference (no text-only mode) | `reference_image_urls`, `reference_audio_urls` | `[@reference_image_1]` | Single clean views + voice |
| `omni_flash_1_1` | reference or first frame | `image_urls`, `reference_video_urls`, `image_url` | `<IMAGE_REF_0>` | ≤3 clean views |
| `grok_imagine_1_5` | reference (≤7) or first frame | `reference_image_urls`, `image_url` | `<IMAGE_0>` | Single clean views |
| `minimax_h3_max` | reference (≤12 files) + optional first/middle/end frame | `reference_image_urls`, `reference_video_urls`, `image_url` | "Image 1" | Sheet as identity + a motion video |
| `minimax_h3_max_recast` | swap people in a 5–30 s video | `video_url`, `reference_image_urls` (one per person, ≤4), `enhance_realism` | "the person in the first photo" | **One clean full-body photo per person, never a sheet** (each panel may read as a person) |
| `minimax_h3_lora` | your LoRA (≤3) + refs | `provider_options.fal.loras[{path, scale}]` | — | For 20+ shot series or a mascot |
| `heygen_video_1` | references (≤12 total) | `provider_options.heygen.reference_images`, `reference_audio`, `image`, `seed` | `@Image1` | Product + person |
| `veo_3_1` | first/last frame only on varg | `image_url`, `first_frame_url`, `last_frame_url` | — | An approved still |

### Tested on 2026-10-27 (Nonna Rosa, 5 s, 9:16, 720p, audio)

| Setup | Result | Credits |
|---|---|---|
| `seedance_2_5`, whole sheet as `@image1` + "no grid, no labels" | No grid leak, identity held; the camera added an unplanned pass-by | 203 |
| `seedance_2_5`, face crop `@image1` + body crop `@image2` | Steadiest face, one continuous shot | 203 |
| `kling_v4`, approved scene still as first frame | Most faithful to the still, including its unwanted scooter logo | 83 |

Clips: [whole sheet](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_7ef0dc5f2285.mp4) · [crops](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_6489606dc55b.mp4) · [still → Kling 4](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_9924ae2c4d99.mp4)

## Call shapes

```json
// Seedance 2.5, reference mode pinned (use when a clip opens on the sheet)
{ "model": "fal:bytedance/seedance-2.5/reference-to-video",
  "files": [{ "url": "<sheet>" }], "duration": 8, "resolution": "720p", "aspect_ratio": "9:16",
  "prompt": "@image1 = <name>, identity only. <shot>. Do not copy the sheet layout, labels or grey backdrop. No grid, no picture-in-picture, no on-screen text." }

// Kling 4.0, one element from turnaround crops (pinned so the provider options apply)
{ "model": "fal:fal-ai/kling-video/v4/reference-to-video", "duration": 8, "resolution": "1080p",
  "prompt": "@Element1 walks through the market at dusk, turns to camera and smiles.",
  "provider_options": { "fal": { "elements": [
    { "frontal_image_url": "<front>", "reference_image_urls": ["<three-quarter>", "<side>", "<back>"] } ] } } }

// Recast: your own footage, one photo per new person
{ "model": "minimax_h3_max_recast",
  "prompt": "The man on the left becomes the person in the first photo.",
  "provider_options": { "fal": { "video_url": "<your clip>", "reference_image_urls": ["<full-body photo>"], "enhance_realism": true } } }
```

Route keys for each model are in the "Routes" table of its spec. Check which route ran before batching.

## Exclusion lines

```
Use the references for identity only (face, hair, body, wardrobe). Do not copy the sheet layout,
labels, panel borders, grey backdrop or studio lighting. No grid, no split screen, no
picture-in-picture, no on-screen text. One <person> only, fully themselves from the first frame,
not a fade or morph.
```

With several references, add a winner rule: "Where @image1 (the scene still) and @image2 (the sheet) differ in pose, light or setting, @image1 wins; @image2 only defines the person."

## Drift: causes and fixes

| Cause | Fix |
|---|---|
| Face small on the sheet (too many panels) | ≤6 panels, or add a face crop as its own reference |
| Several faces in one reference | One character per sheet; role names when there are several people |
| White or busy background on the sheet | Flat light grey; crop source photos to the person |
| Dramatic light on the sheet | Even light on the sheet; put the light in the shot prompt |
| Missing back or profile | Add the view (or `qwen_angles` from the approved front) |
| Two outfits or two versions in the refs | One sheet per look; delete stale versions |
| Props, capes, busy hands | Empty hands on the sheet, a separate prop sheet, little hand action |
| Chaining from a drifted clip | Re-anchor every shot on the original sheet |
| Many variables changed at once | Change one thing per run; keep duration, ratio and file order fixed |
| Fast moves, long clips | Shorter clips, calmer camera, a 480p test shot first |
| Identity sentence reworded between shots | Freeze it in the card and paste it verbatim |

When references stop holding (20+ shots, a mascot that must never drift), train: `minimax_h3_lora` (fal trainer, 10+ clips or images), Higgsfield Soul ID (real people, on Higgsfield) or a Phota profile (`[[profile_id]]`).
