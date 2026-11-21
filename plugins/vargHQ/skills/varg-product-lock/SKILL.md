---
name: varg-product-lock
description: >-
  Turns product photos into AI video shots that keep the product identical: a lock sheet (fixed
  geometry, fixed surface, allowed motion), a reference pack of 2-4 angles passed as @image roles
  to Seedance 2.5 or Kling 4, a camera-risk ladder (locked frame → push-in → slide → small orbit),
  banned motion words, one action per 4-6 s shot, a drift check with varg video_analyze, and the
  real packshot composited back where text must be exact. Fixes the #1 "looks fake" tell in AI
  product ads: warped logos, melted labels, products that change shape or size between shots. Use
  when a product drifts, morphs, changes color or loses its label in AI video, when someone asks
  for "consistent product", "keep my logo", "product looks different in every shot", or before a
  batch of product videos for TikTok Shop, Meta or Amazon. Not for people and characters staying
  the same (use varg-consistent-characters or varg-character-design).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - curl
    homepage: https://varg.ai/how-to
compatibility: >-
  Needs a VARG_API_KEY with curl (see the varg-ai skill) or the varg MCP connection
  (https://mcp.varg.ai/mcp). ffmpeg for compositing the real packshot back in.
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# Keep the product identical in every AI shot

AI video models redraw the product in every frame. With one photo they guess the hidden sides, and long, soft or printed products drift: wedges turn into blocks, labels melt, cans invent a back. This skill locks the product before any clip is generated and checks every clip after.

Generation runs on varg: REST `https://api.varg.ai/v2` (the `varg-ai` skill) or the MCP server `https://mcp.varg.ai/mcp`.

## 1. Write the lock sheet (one per product)

```
PRODUCT: car seat gap filler, single piece
FIXED GEOMETRY: long thin wedge, ~50 cm long, ~4 cm wide at the top, tapering; seatbelt slot near one end
FIXED SURFACE: black leather-like cover, contrast stitching along the top edge, no logo
ALLOWED MOTION: held, slid into a gap, objects dropped on top; never bent, squeezed or rotated fast
NEVER: boxy, shorter, glossy, another color, a second slot
```

Separate geometry, surface and motion; never mix an old and a new label in the references ([seedance.tv](https://www.seedance.tv/blog/how-to-keep-product-shape-consistent-in-ai-video-ads)).

## 2. Build the reference pack

| Ref | What | How |
|---|---|---|
| `@image1` hero | front three-quarter, clean, ≥1080 px | the supplier photo, or `gpt_image_2_5` to fix text |
| `@image2` profile | the side that shows true shape and size | `nano_banana_2_1` edit of the hero: "the exact same product from the side on white" (5 credits) |
| `@image3` detail | label, logo or material close-up | crop of the real photo |
| `@image4` scale | in a hand or next to a known object | optional |

Seedance 2.5 takes up to 9 images, Kling 4 up to 7 references per video, Veo 3.1 Ingredients up to 3. Give each image one role in the prompt: "@image2 only shows the true side profile, not the background" ([AuraJZ/ai-product-video](https://github.com/AuraJZ/ai-product-video)).

## 3. Prompt with a lock block, then one action

```
Product lock. @image1 is the exact product, front three-quarter view; @image2 is the same product from
the side, showing its true long thin wedge shape (about 50 cm long, 4 cm wide). The product keeps this
exact shape and size: it does not become boxy, does not shorten, does not change color, stitching or the
seatbelt slot. Never re-describe it beyond this.
<scene, one simple action, slow and steady, camera holds still with a slight handheld drift>
Real footage look, no music, no text, no subtitles.
```

- One action per 4–6 s shot. Late frames drift more: cut before the warp.
- **Camera-risk ladder:** locked frame → slow push-in → lateral slide → small orbit (15°) → full spin. Climb one step only when the step below holds.
- **Banned words:** spin, 360, whip, fast zoom, morph, transform, "dramatic zoom into the label".
- Describe the product's color apart from the scene light, or the light recolors it.
- Hands cover the product → it redraws what was covered. Grip a plain face; cut before an occlusion.

## 4. Check every clip, rerun only what fails

```bash
curl -s -X POST https://api.varg.ai/v2/tools/video_analyze/call -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" -d '{"model":"video-analyze","video_url":"CLIP_URL",
  "prompt":"Compare the product in this clip with this description: <lock sheet>. For the first, middle and last second: does shape, size, color, label and every fixed detail match? Answer PASS or FAIL per attribute with the second where it breaks."}'
```

About 5 credits per clip. FAIL on any fixed attribute → rerun that shot only, with a shorter duration or one step down the camera ladder. Make 3–4 takes of a hero shot and keep the most stable.

## 5. Put the real product back where text must be exact

For the hero close-up, use the real packshot: a slow push-in on the photo (`zoompan`) or the generated scene with the packshot overlaid on a static shot:

```bash
ffmpeg -loop 1 -i packshot.png -vf "scale=1300:-2,zoompan=z='min(zoom+0.0008,1.12)':d=150:s=1080x1920:fps=30" -t 5 -pix_fmt yuv420p hero.mp4
```

Curved labels on moving bottles need planar tracking (Mocha) in post; avoid those shots if you can.

## Tested

2026-10-28, car seat gap filler. With one photo, `seedance_2_5` turned the long wedges into boxy blocks in the reveal shot. With the lock sheet, a side-profile reference made by `nano_banana_2_1` (5 credits) and the lock block above, the same shot kept the long wedge shape, the color and the stitching for the whole 6 s (231 credits). Before/after: https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_332df2a110a0.mp4

## Related skills

`varg-unboxing-video` and `varg-product-hook` (shots that need the lock), `product-photo-to-video`, `varg-consistent-characters` (people, not products), `varg-ai`.
