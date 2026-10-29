# Models, pipelines and prompts (October 2026)

Prices change: take them only from `estimate_cost` / `list_models` at run time. The ranges below come from varg's live pricing rules on 2026-10-23, for orientation (1 credit = 1 cent).

## Model map by job (varg ids)

| Job | Pick | Alternatives | Notes |
|---|---|---|---|
| Cut-out of the real photo | `bria_guided_remove_background` | `gpt_image_2_5` edit (transparent) | Keeps original pixels |
| Hero packshot from a real photo | `gpt_image_2_5` edit | `nano_banana_2_1` | GPT Image 2.5 is best on small label text |
| Scene stills that keep the label | `nano_banana_2_1` with the cut-out as a reference | `seedream_5_pro`, `flux_3_image`, `krea_3` | Never regenerate the product from text |
| Product in a hand | `bria_fibo_edit_1_5_product_holding` | `nano_banana_2_1` (person + product refs) | Only the arm and hand change |
| Try-on | `bria_fibo_edit_1_5_virtual_try_on` | `gpt_image_2_5` | Check against the real garment |
| New angle of the product | `qwen_angles` | — | Real side views for reveals and orbits |
| Storyboard sheet, exact text | `gpt_image_2_5` | `ideogram_v4_5` | Quote text as EXACT |
| Creator / actor still | `nano_banana_2_1` | `gpt_image_2_5` | Phone-real JSON prompt |
| Hero video, talking actor in one pass | `seedance_2_5` | — | ≤9 image refs, 4–30 s, native dialogue; priciest, ~2× by route; ~3 tries per keeper |
| Cheaper multi-shot, keyframes | `kling_v4` | `kling_v4_flash` (drafts) | 30 s, 7 reference elements; often right first try |
| B-roll volume | `wan_3` | `minimax_h3_max_turbo` | Best value |
| Glass, metal reflections | `veo_3_1` | `veo_3_1_fast` | 4/6/8 s only |
| Fast, legible on-screen text | `omni_flash_1_1` | — | Role tags for product in hand |
| Listing loop / 360° | `pixelcut_looping_video` | `minimax_h3_max_camera_controls` | Safest label fidelity |
| Presenter with speech, one call | `creatify_boreal` | `heygen_video_1` | Post-trained on ads; ~720p class |
| Recast a winning ad | `minimax_h3_max_recast` | — | New actors, same motion |
| Voice | `eleven_v4` | `eleven_v4_turbo` | ~3.5 words per second |
| Lip-sync / re-voice | `sync_v3` | `veed_fabric_1_0`, `minimax_h3_max_lipsync`, `omnihuman_v2` | Fix or translate; native audio is better for new takes |
| Captions | `whisper_large_v3` + render | — | Safe zone |
| Music bed | `mureka_9_5` | `eleven_music_v2_5` | Set the duration; licensed per platform |

Sora is not an option: its API shut on 2026-09-24.

## Pipelines

**A. Product photo → product video (10–20 s, no person).** Truth sheet → cut-out → hero still → 8–12 panel storyboard sheet (approve) → one `seedance_2_5` multi-shot clip with PRODUCT LOCK → repair drifting shots from first/last frames → real packshot over the last second → edit. ~250–1,000 credits at 720p. Skill: `product-photo-to-video`.

**B. AI UGC ad (15–30 s).** Angle + script (facts, no testimonials) → creator still + identity sheet → product in hand (`bria_fibo_edit_1_5_product_holding`) → `seedance_2_5` takes with creator + product refs and quoted lines; render the hook first, reuse its audio as `@audio1` → reject pass → edit. ~300–1,000 credits; Kling/Wan mix ~200–300. Skill: `ai-ugc-ad-video`.

**C. Hands-only ASMR unboxing (15–30 s).** 12-panel ASMR sheet → `seedance_2_5` or `kling_v4` with "natural ASMR only, no background music" → one hand anchored on the box base. ~240–1,400 credits.

**D. Competitor outlier → new concepts.** List the competitor's ads running 30+ days (Meta Ad Library) → transcribe → find the promise repeated in 4–5+ of them (the validated angle) → rewrite for your product and a different buyer → produce with A or B. Copy structure, never footage, script or actor.

**E. Winner → test set.** Decode the winner (hook, argument, buyer, format) → one-variable tests → 3–5 new openers on the body. Skill: `ad-creative-testing`.

**Test set budget (one reported worked example):** 10 concepts drafted, 4 finished, 1 winner at 1080p with 5 hook variants ≈ 4,000–4,500 credits on a clean path, 8,000–15,000 with realistic rejects. For comparison (outside varg): Arcads ~$11/video, human UGC $150–$1,500 per video plus usage rights.

## Prompt rules that hold across models

- One job per reference, with a boundary: "@image1 defines the product ONLY; ignore its background".
- Spell the label out in order; "correctly spelled, legible whenever in focus".
- Write every spoken line in quotes with timings. Ask for "no music, no captions, no on-screen text" in generation; add them in the edit.
- Prompt the camera's flaws for UGC (handheld tremor, autofocus hunts, rolling shutter, noise) and a breath or swallow between lines.
- Shots ≥1.5 s, one camera move each. Lock the camera in both frames for first/last-frame shots.
- An explicit "add no…" list stops invented props, splashes and steam.

## Prompt files

- Product shots, storyboard sheet, PRODUCT LOCK, locked loop, background swap, try-on: `product-photo-to-video/references/prompts.md`
- UGC creator still, realistic vlog take, street interview, camcorder vlog, voice lock, Creatify: `ai-ugc-ad-video/references/prompts.md`
- Hooks: `product-video-hooks/references/hook-bank.md`

Sources: varg live pricing and model specs (https://varg.ai/models/llms.txt), [Masonry product-ad model test](https://masonry.so/blog/best-ai-video-model-for-product-ads), [Luma Seedance guide](https://lumalabs.ai/learning-center/articles/seedance-2.0-complete-guide), [fal skills](https://github.com/fal-ai-community/skills), X posts in [sources.md](sources.md).
