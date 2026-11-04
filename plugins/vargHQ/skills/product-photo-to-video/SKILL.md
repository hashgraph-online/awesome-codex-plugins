---
name: product-photo-to-video
description: >-
  Turn a product photo into a product video ad that keeps the real product. Builds TikTok, Reels,
  TikTok Shop b-roll and listing videos from one to three product photos: a product truth sheet
  (label text letter by letter, colours, parts), a cut-out, a hero still, an 8–12 panel storyboard
  sheet, then one multi-shot Seedance 2.5 or Kling 4 clip with a PRODUCT LOCK block, a repair pass
  on drifting shots, and the real packshot composited on the last second. Formats: hands-only ASMR
  unboxing, macro pour or texture, ingredient burst or exploded view, product in use, 360° loop,
  product in a hand, apparel try-on. Never ships a Ken Burns slideshow. Use when someone has
  product photos and wants a product video, packshot animation, unboxing, ASMR product video,
  listing video or AI b-roll without filming. NOT for a person talking about the product (use
  ai-ugc-ad-video), TikTok Shop presenter videos (use tiktok-shop-video), or still listing images
  (use a product-photo skill).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  varg.cost.typical: "~250–1,000 credits per 15 s video at 720p including one repaired shot (estimate)"
  varg.cost.estimate_tool: "varg:estimate_cost"
  varg.runtime.typical: "15–40 min"
  varg.models: "bria_guided_remove_background, gpt_image_2_5, nano_banana_2_1, bria_fibo_edit_1_5_expand, bria_fibo_edit_1_5_product_holding, bria_fibo_edit_1_5_virtual_try_on, qwen_angles, seedance_2_5, kling_v4, wan_3, pixelcut_looping_video, minimax_h3_max_camera_controls, ffmpeg"
  varg.outputs: "mp4 9:16 1080x1920, mp4 1:1 or 16:9 for product pages"
  openclaw:
    requires:
      env:
        - VARG_API_KEY
    primaryEnv: VARG_API_KEY
    homepage: https://varg.ai
compatibility: >-
  Needs the varg MCP connection (https://mcp.varg.ai/mcp) or a VARG_API_KEY with curl (see the
  varg-ai skill). Compositing and export use ffmpeg locally or the varg ffmpeg tool.
allowed-tools: Bash(curl:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# Turn a product photo into a product video ad

What wins in late 2026 is one impossible but tactile moment built around the real product: a macro pour, a lid snap, an ingredient burst, a hands-only unboxing. What fails: logo-first "cinematic" b-roll, still-photo slideshows (TikTok Shop bans them in shoppable videos), and any frame where the model rewrote the label.

Generation runs on varg (MCP `call_tool` or `POST https://api.varg.ai/v2/tools/{image|video}/call`). **Quote with `estimate_cost` and wait for a yes before each paid step.** A still costs cents to fix; a clip costs dollars, so approve stills first.

## 1. Product truth sheet (free, do it first)

From the photos and the product page, write:

```
PRODUCT: <name, size, e.g. "30 ml amber glass dropper bottle, gold cap">
LABEL (exact, in order): "NORTHLINE" / "VITAMIN C" / "30 ML"
COLOURS: body #F4A23B, cap #C9A227, label #FFFFFF
PARTS / IN THE BOX: bottle, dropper, box
SCALE: fits in the palm
CLAIMS WE CAN SHOW: absorbs in ~30 s (visible), lightweight texture
NEVER: change shape, size, colour or material; add text; fake results (fizz, instant clearing)
```

Photos: clean, straight-on, label readable. "If the label isn't readable in the reference, the model invents its own text."

## 2. Cut-out and hero still

1. Cut-out: `bria_guided_remove_background` (keeps the original pixels).
2. Hero still: `gpt_image_2_5` edit, "keep the uploaded product exactly unchanged, replace only the background with [environment], match reflections and contact shadows, no product deformation, no added labels". `nano_banana_2_1` is cheaper but may need small packaging text fixed.
3. 9:16 canvas: `bria_fibo_edit_1_5_expand`. Real side views for reveals: `qwen_angles` (exact angles, not invented sides).
4. Check at 100%, letter by letter, colour by eyedropper. Reject and redo, don't "fix later".

Product in a hand: `bria_fibo_edit_1_5_product_holding`. Apparel on a person: `bria_fibo_edit_1_5_virtual_try_on` (check stitching, print and logo; AI try-on smooths texture and length).

## 3. Storyboard sheet (approve before video)

`gpt_image_2_5`, 8–12 panels, each ≥1.5 s with one camera move, POV hands only for no-face formats. Template: [references/prompts.md](references/prompts.md) P1. Sequence that works: product on the surface, hands enter → open and reveal → the most tactile moments → in use → the result in macro → hero packshot. Show it to the person.

## 4. One multi-shot clip with PRODUCT LOCK

`seedance_2_5`, 10–15 s, `@image1` = the cut-out, `@image2` = the approved sheet ("follow its shot order, never show its panels, numbers or text"), audio on for foley, "no background music" unless wanted, last second held clean for the end card. Template: [references/prompts.md](references/prompts.md) P2.

Cheaper: `kling_v4` multi-shot (often right first time) or `wan_3` (best value for b-roll volume). Drafts: `kling_v4_flash`.

Safest for listings and loops: `pixelcut_looping_video` (locked camera, seamless loop, `motion: spin` for 360°). Exact orbit around a packshot: `minimax_h3_max_camera_controls`.

## 5. Repair, don't reroll

Reject any shot where the pack, label, shape, colour, part count or hand count drifts. Regenerate only that shot from first and last frames (`seedance_2_5` first/last-frame mode, `kling_v4` `end_image_url`), **camera locked in both frames** or it invents a move. Reliability ladder, best first:

1. Composite the real product PNG and label over AI footage (real pixels)
2. Locked camera, only the environment moves (liquid, fog, hands)
3. Reference on every shot + PRODUCT LOCK + label spelled out
4. One job per reference ("defines the product ONLY")
5. First/last frames from approved stills
6. A hand anchored on the box base; hands at the product's edges
7. Push-ins and parallax instead of full spins of unseen sides

Common failures and fixes: [references/failures.md](references/failures.md).

## 6. Composite the truth and export

- Lay the real packshot PNG (and copy, if any) over the clean last second:

  ```bash
  # packshot.png = the real cut-out with alpha; 13 = where the clean last seconds start
  ffmpeg -i clip.mp4 -loop 1 -i packshot.png -filter_complex "[1:v]scale=760:-1[p];[0:v][p]overlay=(W-w)/2:(H-h)/2:shortest=1:enable='gte(t,13)'" -c:v libx264 -crf 18 -c:a copy hero.mp4
  ```

  Tested on FFmpeg 6.0: the packshot appears from 13 s and the clip keeps its length.

- Edit, captions, CTA, loudness and the 4:5 cut: `ecommerce-video-edit`. A 1:1 or 16:9 15–30 s cut with no hard sell for the product page.
- Label realistic AI footage (TikTok AIGC toggle; Amazon `contains-synthetic-performer` if a photoreal person appears). Never show the product doing more than it can.

## Formats

| Format | Model | Notes |
|---|---|---|
| Hands-only ASMR unboxing | `seedance_2_5` / `kling_v4` | 12-panel ASMR sheet; "natural ASMR only"; one hand stays on the box base |
| Macro pour / texture / splash | `seedance_2_5` | Locked camera on the pack; only the liquid moves |
| Ingredient burst / exploded view | `gpt_image_2_5` still → `seedance_2_5` | Real parts in their real order |
| Food process film ending on the product | `seedance_2_5` | 8–12 beats of 2–3 s, match cuts, 110–120 BPM |
| 360° loop for listings | `pixelcut_looping_video` | Safest label fidelity |
| Product in use (kitchen, bathroom) | `nano_banana_2_1` stills → `kling_v4` | Hands at edges, real scale cue |
| Apparel on a model | `bria_fibo_edit_1_5_virtual_try_on` → `seedance_2_5` | One `@image` per garment, "EXCLUSIVE reference" |

Costs on varg (live rules, Oct 2026; quote exact jobs with `estimate_cost`): a 15 s product video is roughly 250–1,000 credits at 720p (Seedance 2.5 is the priciest and varies ~2× by route; Kling 4 ~16 credits/s, Wan 3 ~10 credits/s at 720p).

## Related

`ecommerce-video-ads` · `varg-product-hook` (UGC-style hook clip of the product in use) · `ecommerce-video-edit` · `ai-ugc-ad-video` · `tiktok-shop-video` · `varg-ai`

Sources: [varg how-to: turn a product photo into a video](https://varg.ai/how-to/turn-a-product-photo-into-a-video), [fal commercial skill](https://github.com/fal-ai-community/skills/blob/main/skills/commercial/references/prompt-patterns.md), [Masonry controlled test](https://masonry.so/blog/best-ai-video-model-for-product-ads), [Luma Seedance guide](https://lumalabs.ai/learning-center/articles/seedance-2.0-complete-guide), [OpenAI image prompting cookbook](https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide), X posts by @abxxai, @Ciri_ai, @HeyRu0by, @Strength04_X, @yourPlugAI.
