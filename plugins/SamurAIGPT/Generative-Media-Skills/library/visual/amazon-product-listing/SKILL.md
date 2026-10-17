---
slug: muapi-amazon-product-listing
name: muapi-amazon-product-listing
version: "1.0.0"
description: Generate a complete Amazon product listing image set — hero image, lifestyle shot, infographic with features, and comparison/detail closeups optimized for Amazon standards.
acceptLicenseTerms: true
---


# Amazon Product Listing Pack

**Generate a complete Amazon product listing image set — hero image, lifestyle shot, infographic with features, and comparison/detail closeups optimized for Amazon standards.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `product_name` | text | yes | — | The product name (e.g. "Stainless Steel Water Bottle 32oz"). |
| `product_category` | text | yes | — | Amazon category (e.g. "Kitchen & Dining", "Sports & Outdoors", "Electronics"). |
| `key_features` | text | yes | — | Comma-separated top features to highlight (e.g. "leak-proof lid, BPA-free, keeps cold 24h, fits cupholder"). |
| `target_buyer` | text | no | general consumer | Who buys this (e.g. "athletes", "busy moms", "office workers aged 25-45"). |
| `product_image` | image_url | no | — | Optional existing product photo to use as base reference. |


## Steps

Submit a SINGLE the plan with all steps running in parallel.

### All 4 Images (Parallel)

1. **Hero image (white background)** — `muapi image generate` (model=`ai-product-photography`) if `{{product_image}}` provided, else `muapi image generate` (model=`gpt4o-text-to-image`):
   - Prompt: `Professional Amazon main listing hero image of {{product_name}}. Pure white background #FFFFFF. Product centered, perfectly lit with soft studio lighting, no shadows. High resolution, commercial product photography, sharp focus on all details, 2000x2000px equivalent quality.`
   - Aspect ratio: 1:1

2. **Lifestyle/context shot** — `muapi image generate` (model=`ai-product-shot`) if `{{product_image}}` provided, else `muapi image generate` (model=`nano-banana-pro`):
   - Prompt: `Amazon lifestyle image of {{product_name}} being used by {{target_buyer}} in a natural setting. {{product_category}} product in real-life use context. Warm natural lighting, aspirational but relatable, slight bokeh background. Commercial lifestyle photography, professional quality.`
   - Aspect ratio: 1:1

3. **Feature infographic** — `muapi image generate` (model=`gpt4o-text-to-image`):
   - Prompt: `Amazon product detail page infographic for {{product_name}}. Shows product with 4-5 callout arrows highlighting these key features: {{key_features}}. Clean white or light grey background, professional typography, bold feature labels with icons. Amazon A+ content style, feature benefit layout, commercial design.`
   - Aspect ratio: 1:1

4. **Closeup detail shot** — `muapi image generate` (model=`nano-banana-pro`):
   - Prompt: `Extreme closeup macro product detail shot of {{product_name}} — focus on premium materials, texture, quality craftsmanship. Studio lighting, white background, ultra sharp focus, demonstrates quality. Amazon product detail image showing materials/finish.`
   - Aspect ratio: 1:1

After generation:
- Present all 4 images in order (main > lifestyle > infographic > detail)
- Suggest uploading to canvas to arrange as a listing mockup
- Offer to generate 3 additional A+ content module images

## Notes
- Amazon requires main image on pure white background — enforce this strictly.
- Key features should be visually distinct and scannable in the infographic.
- For electronics, add "showing ports, buttons, and connections clearly" to the detail shot.

## Trigger Keywords

`amazon listing`, `amazon product`, `product listing`, `ecommerce listing`, `amazon images`, `product photography amazon`, `listing images`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
