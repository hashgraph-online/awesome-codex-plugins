---
slug: muapi-product-ad-cinematic
name: muapi-product-ad-cinematic
version: "1.0.0"
description: Cinematic 5–10s product ad from a product photo + brand brief.
acceptLicenseTerms: true
---


# Cinematic Product Ad

**Cinematic 5–10s product ad from a product photo + brand brief.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `product_image` | image_url | yes | — | URL of the product photo (must already be uploaded). |
| `brand_brief` | text | yes | — | Mood / style direction (e.g. "luxury minimal", "playful"). |
| `duration_sec` | int | no | 6 | Final video length in seconds (5–10). |


## Steps

This skill has TWO phases separated by a user pick. Submit them as two
separate the plan calls — never bundle downstream steps into the
first plan.

### Phase A — variant exploration (cheap)

Submit ONE the plan containing only:

1. **Hero frame variants** — 4 separate `muapi image generate` nodes
   (model=nano-banana-2, aspect_ratio=16:9 by default).
   - Each prompt restyles the product against the brand brief mood. Vary
     lighting, palette, framing, and lens between variants. Keep product
     geometry intact.
   - Reference the user's `product_image` if the model supports image
     conditioning; otherwise describe the product in detail.

After the plan executes, end your turn with a brief message listing the 4
asset_ids and asking the user which one to take forward (e.g.
"Pick a hero (asset_1, asset_2, asset_3, or asset_4)?"). Wait.

### Phase B — commit on the picked hero (expensive)

Once the user replies with their pick, submit a SECOND the plan:

1. **Upscale** the picked frame — `enhance_image` (operation=upscale).
2. **Animate** the upscaled frame — `muapi video from-image` (model=kling-v3.0-standard-image-to-video,
   duration={{duration_sec}}, prompt="slow cinematic push-in, soft
   volumetric light, subtle product micro-rotation"). Reference the
   upscale's URL with `$nX.url`.
3. **Background music** — `muapi audio create` (kind=music) — runs in parallel
   with the upscale/animate. Style derived from `brand_brief` (luxury →
   "ambient cinematic, warm strings, slow tempo, instrumental"). Duration
   ≈ video length.
4. Return the upscaled hero image and the final video.

## Notes
- If the brief mentions "luxury", bias the palette to gold/black; for "playful",
  bias to bright/saturated.
- If video gen fails after failover, fall back to a still-frame slideshow
  (just return the upscaled hero + music).
- Don't auto-confirm step 4 — its cost (~80 cr) deserves a user nod.

## Trigger Keywords

`product ad`, `commercial`, `cinematic ad`, `product video`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
