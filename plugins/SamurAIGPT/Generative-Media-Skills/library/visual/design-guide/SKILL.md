---
slug: muapi-design-guide
name: muapi-design-guide
version: "1.0.0"
description: Create a comprehensive brand design guide — color palette, typography pairings, UI component previews, and visual identity rules with example mockups.
acceptLicenseTerms: true
---


# Brand Design Guide

**Create a comprehensive brand design guide — color palette, typography pairings, UI component previews, and visual identity rules with example mockups.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `brand_name` | text | yes | — | The brand or product name. |
| `industry` | text | yes | — | Industry/niche (e.g. "fintech startup", "organic skincare", "luxury hotel chain"). |
| `style_direction` | text | no | modern, minimal, premium | Design aesthetic (e.g. "bold and playful", "corporate and trustworthy", "dark luxury"). |
| `primary_color` | text | no | — | Optional brand primary color (hex code or color name, e.g. "#3898EC" or "deep navy"). |
| `existing_logo` | image_url | no | — | Optional existing logo to extract brand cues from. |


## Steps

This skill runs THREE parallel generation phases, all in a single the plan.

### Phase A — Color & Typography Reference Card

1. **Color palette card** — `muapi image generate` (model=`bytedance-seedream-v4.5`):
   - Prompt: `Clean design guide color palette card for {{brand_name}} — {{style_direction}} style brand for {{industry}}. Shows 5 swatches: primary, secondary, accent, background, text. Each swatch labeled with hex code. Modern design reference card, white background, editorial typography, flat design.`
   - If `{{primary_color}}` is given, include it: `primary color is {{primary_color}}`
   - Aspect ratio: 16:9

2. **Typography pairing preview** — `muapi image generate` (model=`bytedance-seedream-v4.5`):
   - Prompt: `Brand typography pairing sheet for {{brand_name}} — {{style_direction}}. Shows heading font (large, bold), subheading font (medium), body font (small regular), and caption font. Includes font names, sizes, and usage rules. Clean white background, professional design reference.`
   - Aspect ratio: 16:9

### Phase B — UI Component Preview

3. **UI components mockup** — `muapi image generate` (model=`gpt4o-text-to-image`):
   - Prompt: `{{brand_name}} brand design system UI kit — {{style_direction}} for {{industry}}. Shows: primary button, secondary button, input field, card component, badge/tag, icon set sample. Consistent brand colors and fonts. Professional design spec sheet, light mode, high detail, Figma-style component documentation.`
   - Aspect ratio: 4:3

### Phase C — Brand Application Mockup

4. **Real-world mockup** — `muapi image generate` (model=`nano-banana-pro`):
   - Prompt: `{{brand_name}} brand identity applied to real-world mockups — {{style_direction}} style for {{industry}}. Shows business card, letterhead, and mobile app icon all with consistent brand identity. Professional brand presentation, clean background, photorealistic mockups.`
   - If `{{existing_logo}}` provided, use `muapi image edit` (model=`nano-banana-pro-edit`) with it as reference.
   - Aspect ratio: 4:3

After all assets generate:
- Present all 4 assets together as a cohesive design guide
- Provide a written text summary with: suggested font stack, hex codes, spacing rules, and do/don't guidelines
- Offer to generate a social media template or logo next

## Notes
- All prompts should reinforce {{style_direction}} consistently across all phases.
- If {{primary_color}} is blank, derive one from the {{industry}} and {{style_direction}} context.

## Trigger Keywords

`design guide`, `brand guide`, `style guide`, `design system`, `brand identity`, `visual identity`, `brand colors`, `typography`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
