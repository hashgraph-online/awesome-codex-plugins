---
slug: muapi-color-analysis-board
name: muapi-color-analysis-board
version: "1.0.0"
description: Turn a portrait photo into a high-end editorial "Color Analysis Board" in a luxury fashion-magazine style (Dior / Ralph Lauren aesthetic) — best colors, undertone, makeup guide, capsule wardrobe, hair & jewelry recommendations, all laid out on a clean beige/ivory grid.
acceptLicenseTerms: true
---


# Color Analysis Board

**Turn a portrait photo into a high-end editorial "Color Analysis Board" in a luxury fashion-magazine style (Dior / Ralph Lauren aesthetic) — best colors, undertone, makeup guide, capsule wardrobe, hair & jewelry recommendations, all laid out on a clean beige/ivory grid.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `person_image` | image_url | yes | — | A clear, well-lit portrait of the person. Front-facing, neutral background, and natural lighting give the strongest color reads (undertone, hair, eyes). Avoid heavy filters or makeup that masks the natural complexion. |


## Steps

### Phase A — Color Analysis Board Generation

If `{{person_image}}` is not provided, ask the user to upload a clear front-facing portrait. Make sure the face is well-lit with natural color (no heavy filters, color-cast lighting, or sunglasses) — the model needs accurate skin, hair, and eye color to pick the right palette.

Once the photo is available, submit ONE step to generate the color analysis board:

1. **Color Analysis Board Generation** — `muapi image edit` (model=`gpt-image-2-image-to-image`):
   - Reference Image: `{{person_image}}`
   - Image size: `3840x2160` (16:9 landscape) — magazine-spread aspect ratio
   - Background: `auto`
   - Output format: `png`
   - Quality: `auto`
   - Moderation: `low`
   - Prompt:
     ```
     Create a high-end editorial "Color Analysis Board" from this portrait in a luxury fashion magazine style (Dior / Ralph Lauren aesthetic). Clean beige/ivory background, warm tones, soft diffused lighting, ultra-detailed photorealistic quality, consistent lighting, minimal elegant typography, grid-based layout.

     Main portrait: enhanced natural beauty (same identity, smooth skin, soft glow, realistic texture)
     Top section: "Your Best Colors" with fabric swatches with the best algorithm choices
     Undertone panel: warm / neutral / cool with marked result.
     Colors to avoid
     Neutrals that work
     Prints that flatter
     Makeup guide: eyeshadows, blush, lips, highlighter
     "You in your colors": multiple outfit best variations
     Hair colors: best.
     Jewelry
     Style notes

     Capsule wardrobe: coordinated outfits, shoes, bags, accessories
     Style: best style for me
     ```

Present the generated board to the user. Suggest variations they can try: a different source portrait (different lighting / hairstyle for comparison), or asking to bias the palette toward a season (e.g. "spring warm" vs "winter cool") or a specific brand aesthetic (e.g. minimalist Scandinavian, Old Money, streetwear).

## Trigger Keywords

`color analysis`, `color analysis board`, `personal color palette`, `seasonal color analysis`, `undertone analysis`, `style guide board`, `fashion color board`, `capsule wardrobe board`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
- Source schema reference: `gpt-image-v2-edit` (from the source workflow JSON) maps to `gpt-image-2-image-to-image` in the muapi catalog.
- The output is intentionally 16:9 (3840×2160) so it reads as a magazine spread / desktop wallpaper / Pinterest landscape board. For IG-feed square or 9:16 vertical, request a re-crop or re-run with a different `image_size`.
