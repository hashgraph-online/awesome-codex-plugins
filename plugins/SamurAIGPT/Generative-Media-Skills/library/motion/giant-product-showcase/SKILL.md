---
slug: muapi-giant-product-showcase
name: muapi-giant-product-showcase
version: "1.0.0"
description: Create a dramatic "Giant Product" visual where a regular item is showcased as a massive, building-sized object next to a person, then optionally animate the scene.
acceptLicenseTerms: true
---


# Giant Product Showcase

**Create a dramatic "Giant Product" visual where a regular item is showcased as a massive, building-sized object next to a person, then optionally animate the scene.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `product_image` | image_url | yes | — | A clear image of the product to be made giant. |
| `person_description` | text | no | a stylishly dressed man | Description of the person standing next to the giant product. |


## Steps

### Phase A — Giant Product Visualization

If `{{product_image}}` is not provided, ask the user to upload a photo of the product.

Once the photo is available, submit the plan with ONE step to create the giant product scene:

1. **Scene Generation** — `muapi image edit` (model=`nano-banana-2-edit`):
   - Reference Image: `{{product_image}}`
   - Prompt: `A professional commercial photograph featuring a massive, giant-sized version of the product from the reference image. The product is the size of a person and is standing on a clean, modern floor. Next to the giant product, {{person_description}} is leaning against it or standing nearby, highlighting the enormous scale. High-end product photography, soft studio lighting, realistic reflections, 8k resolution.`
   - Aspect ratio: 3:4 or 4:5

Present the generated giant product image to the user for approval.

### Phase B — Animation (Optional)

After the image is generated, ask the user if they would like to animate the scene into a cinematic showcase video.

If requested, submit the plan with ONE step:

1. **Video Generation** — `muapi video from-image` (model=`veo3.1-fast-image-to-video`):
   - Reference Image: The giant product image from Phase A.
   - Prompt: `Cinematic slow-motion camera movement around the giant product. The person next to it moves naturally, looking at the camera or adjusting their pose. Dynamic lighting, high-quality textures, professional commercial vibe.`
   - Aspect ratio: 9:16 or 4:5

After generation, present the final product showcase video.

## Trigger Keywords

`giant product`, `massive object`, `product showcase`, `scale comparison`, `product animation`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
