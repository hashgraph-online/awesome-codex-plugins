---
slug: muapi-multi-angle-shots
name: muapi-multi-angle-shots
version: "1.0.0"
description: Generate a complete set of multi-angle product shots — front, side, back, top-down, and 45-degree perspective — for comprehensive product visualization.
acceptLicenseTerms: true
---


# Multi-Angle Shots

**Generate a complete set of multi-angle product shots — front, side, back, top-down, and 45-degree perspective — for comprehensive product visualization.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `product_name` | text | yes | — | The product to photograph (e.g. "black leather sneaker", "glass perfume bottle", "smartwatch"). |
| `product_image` | image_url | no | — | Optional reference product image to use as base. |
| `background_style` | text | no | pure white studio | Background/environment (e.g. "pure white studio", "dark moody grey", "natural marble surface", "lifestyle context"). |
| `lighting` | text | no | soft studio lighting, product photography | Lighting style (e.g. "dramatic side lighting", "flat lay top-down", "rim lighting", "natural daylight"). |
| `category` | text | no | general product | Product category to tailor angle logic (e.g. "footwear", "watch/jewelry", "electronics", "beverage bottle", "skincare"). |


## Steps

Submit a single the plan with all angles in parallel.

### All Angles (Parallel)

1. **Front view** — `muapi image generate` (model=`ai-product-photography`) if `{{product_image}}` provided, else `muapi image generate` (model=`nano-banana-pro`):
   - Prompt: `{{product_name}} — perfectly centered FRONT VIEW, eye-level angle. {{background_style}} background. {{lighting}}. Sharp focus, commercial product photography, ultra detailed, no props.`
   - Aspect ratio: 1:1

2. **Side / 3/4 angle view** — same model as step 1:
   - Prompt: `{{product_name}} — elegant 3/4 SIDE ANGLE view, slight perspective showing depth and form. {{background_style}} background. {{lighting}}. Shows product silhouette and side detail, commercial photography.`
   - Aspect ratio: 1:1

3. **Back view** — same model as step 1:
   - Prompt: `{{product_name}} — BACK VIEW, centered, showing rear details, finishes, and labels if any. {{background_style}} background. {{lighting}}. Product photography, equal detail to front shot.`
   - Aspect ratio: 1:1

4. **Top-down / flat lay** — `muapi image generate` (model=`ai-product-shot`) if `{{product_image}}` provided, else `muapi image generate` (model=`bytedance-seedream-v4.5`):
   - Prompt: `{{product_name}} — perfectly overhead TOP-DOWN flat lay view, camera pointing straight down. {{background_style}} surface. Flat lay product photography, even lighting, no shadows at edges, symmetrically placed.`
   - Aspect ratio: 1:1

5. **Hero glamour shot** — `muapi image generate` (model=`nano-banana-pro`):
   - Prompt: `{{product_name}} — dynamic low-angle HERO SHOT, slightly below eye level looking up at product. Dramatic {{lighting}}, slight depth of field, editorial product photography. {{background_style}} background. Premium commercial advertising quality.`
   - Aspect ratio: 4:5

After generation:
- Present all 5 angles in a grid layout description
- Suggest adding a 360° spin video with `kling-v3.0-pro-image-to-video`
- Offer to upscale any angle with `ai-image-upscaler`

## Notes
- For footwear: emphasize sole view as a 6th angle if requested.
- For watches/jewelry: suggest a macro detail shot as an additional step.
- For electronics: add "showing all ports, buttons, and screen" to front and side prompts.
- `ai-product-photography` is ideal when a reference image is provided — it preserves product identity.

## Trigger Keywords

`multi angle`, `multiple angles`, `360 product`, `product angles`, `all sides`, `front back side`, `product views`, `angle shots`, `product photography set`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
