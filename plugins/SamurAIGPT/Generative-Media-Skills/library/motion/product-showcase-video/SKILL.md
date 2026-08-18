---
slug: muapi-product-showcase-video
name: muapi-product-showcase-video
version: "1.0.0"
description: Create a dynamic product showcase with explosive ingredient arrangements, followed by a realistic motion animation.
acceptLicenseTerms: true
---


# Product Showcase Video

**Create a dynamic product showcase with explosive ingredient arrangements, followed by a realistic motion animation.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `product_image` | image_url | yes | — | A clear photo of the product to be showcased. |
| `ingredients_description` | text | no | fresh and raw ingredients | Description of the ingredients to fly around the product. |
| `brand_colors` | text | no | matching brand colors | The primary colors to use for the background. |


## Steps

### Phase A — Dynamic Product Image Generation

If `{{product_image}}` is not provided, ask the user to upload a photo of their product.

Once the photo is available, submit the plan with ONE step to create the dynamic advertisement image:

1. **Dynamic Image Generation** — `muapi image edit` (model=`bytedance-seedream-v4.5-edit`):
   - Reference Image: `{{product_image}}`
   - Prompt: `Photograph this product in a dramatic modern scene accompanied by an explosive outward dynamic arrangement of {{ingredients_description}} flying around the product, signifying its freshness and nutritional value. Promo ad shot, without text, product is emphasized, with {{brand_colors}} as the background. High-quality commercial lighting, sharp detail, vibrant colors.`
   - Aspect ratio: 1:1 or 4:5

Present the generated dynamic image to the user for approval.

### Phase B — Realistic Motion Animation

Once the image is approved, submit the plan to animate the scene:

1. **Video Generation** — `muapi video from-image` (model=`seedance-v1.5-pro-i2v-fast`):
   - Reference Image: The dynamic image from Phase A.
   - Prompt: `Create a realistic motion animation of the scene. The ingredients fly outwards from the product in slow motion, with subtle lighting shifts and camera movement. Cinematic quality, smooth animation, professional product commercial vibe.`
   - Aspect ratio: 1:1 or 4:5

After generation, present the final product showcase video.

## Trigger Keywords

`product showcase video`, `dynamic product ad`, `ingredient explosion`, `fresh product animation`, `commercial video`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
