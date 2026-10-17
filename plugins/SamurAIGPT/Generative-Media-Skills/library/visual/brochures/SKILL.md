---
slug: muapi-brochures
name: muapi-brochures
version: "1.0.0"
description: Generate a professional multi-page brochure design — cover, inner spread, and back cover — for business, real estate, events, or product launches.
acceptLicenseTerms: true
---


# Brochure Designer

**Generate a professional multi-page brochure design — cover, inner spread, and back cover — for business, real estate, events, or product launches.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `brand_name` | text | yes | — | The company or brand name featured in the brochure. |
| `topic` | text | yes | — | What the brochure is about (e.g. "luxury apartments in Dubai", "annual company report 2024", "new product catalog", "health clinic services"). |
| `style` | text | no | modern, professional, premium | Brochure visual style (e.g. "minimalist luxury", "bold colorful", "corporate formal", "creative editorial"). |
| `color_scheme` | text | no | navy blue and gold | Primary color palette (e.g. "forest green and cream", "black and white with red accents"). |
| `format` | text | no | tri-fold | Brochure format — "tri-fold", "bi-fold", "single page", "A4 portrait". |
| `brand_logo` | image_url | no | — | Optional brand logo to include in the design. |


## Steps

Submit the plan with THREE parallel steps (front, inside, back).

### All Pages in Parallel

1. **Front cover** — If `{{brand_logo}}` provided, use `muapi image edit` (model=`gpt4o-edit`); else `muapi image generate` (model=`gpt4o-text-to-image`):
   - Prompt: `Professional {{format}} brochure FRONT COVER for {{brand_name}} — {{topic}}. {{style}} design, {{color_scheme}} color scheme. Bold headline area, hero image, brand name prominently displayed, luxury print-quality design. A4 portrait format, high resolution, commercial print ready. Clean professional layout.`
   - Aspect ratio: 2:3 (portrait A4)

2. **Inner spread / main content** — `muapi image generate` (model=`bytedance-seedream-v4.5`):
   - Prompt: `Professional {{format}} brochure INNER SPREAD for {{brand_name}} — {{topic}}. {{style}} interior layout with: headline section, 3 columns of body text placeholder, feature icons/images, pull quote, infographic element. {{color_scheme}} accents. Balanced grid layout, professional typography hierarchy. Print-ready design.`
   - Aspect ratio: For tri-fold: 3:2 (landscape showing all 3 panels). For A4/bi-fold: 2:1 (landscape double spread).

3. **Back cover** — `muapi image generate` (model=`bytedance-seedream-v4.5`):
   - Prompt: `Professional {{format}} brochure BACK COVER for {{brand_name}}. {{style}}, {{color_scheme}}. Includes: contact information section, QR code placeholder, address/website/social media icons area, subtle brand pattern or texture. Clean, minimal back cover design. A4 portrait format.`
   - Aspect ratio: 2:3

After generation:
- Present all three panels in order: Cover → Inner → Back
- Offer to adjust color, layout, or add specific content to any panel
- Suggest exporting as a canvas composition with all pages arranged

## Notes
- Always use placeholder text blocks ("Lorem ipsum") rather than generating false content.
- For real estate brochures, add property photography prompts as a 4th step.
- For event brochures, emphasize date/venue hierarchy in the front cover prompt.

## Trigger Keywords

`brochure`, `flyer`, `leaflet`, `pamphlet`, `bi-fold`, `tri-fold`, `company brochure`, `marketing brochure`, `product brochure`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
