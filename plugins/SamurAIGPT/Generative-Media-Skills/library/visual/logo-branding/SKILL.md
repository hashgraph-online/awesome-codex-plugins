---
slug: muapi-logo-branding
name: muapi-logo-branding
version: "1.0.0"
description: Design a professional logo with full branding package — primary logo, variations (dark/light/icon-only), color palette, and real-world application mockups.
acceptLicenseTerms: true
---


# Logo + Branding Package

**Design a professional logo with full branding package — primary logo, variations (dark/light/icon-only), color palette, and real-world application mockups.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `brand_name` | text | yes | — | The brand or company name to design a logo for. |
| `industry` | text | yes | — | Industry or business type (e.g. "luxury spa", "AI SaaS startup", "organic food brand", "architecture firm"). |
| `style_preference` | text | no | modern, minimal, versatile | Logo style direction (e.g. "wordmark only", "icon + text", "monogram", "abstract mark", "bold geometric"). |
| `color_preference` | text | no | — | Optional preferred colors or palette direction (e.g. "navy and gold", "earthy greens", "vibrant purple and white"). |
| `mood` | text | no | professional, trustworthy, premium | Brand personality (e.g. "playful and fun", "bold and disruptive", "calm and wellness-focused"). |


## Steps

Submit the plan with all steps in parallel.

### Phase A — Logo Concepts (3 Variations)

1. **Logo concept 1 — Primary** — `muapi image generate` (model=`ideogram-v3-t2i`):
   - Prompt: `Professional logo design for "{{brand_name}}" — {{industry}} brand. {{style_preference}} style. {{mood}} personality. {{color_preference}} color palette. Clean vector-style logo, white background, no gradients unless requested, scalable mark. Include brand name typeset below icon if applicable. Logo design, isolated on white, professional quality.`
   - Aspect ratio: 1:1

2. **Logo concept 2 — Alternative style** — `muapi image generate` (model=`flux-2-pro`):
   - Prompt: `Alternative logo concept for "{{brand_name}}" — {{industry}}. Different approach from standard: explore typographic treatment or geometric abstraction. {{mood}} feel. {{color_preference}}. Professional logo design on white background, vector aesthetic.`
   - Aspect ratio: 1:1

3. **Logo concept 3 — Icon/mark only** — `muapi image generate` (model=`gpt4o-text-to-image`):
   - Prompt: `Brand icon/logomark only (no text) for {{brand_name}} — {{industry}} company. {{mood}} personality. Simple, memorable, scalable icon that works at 32px and 512px. {{color_preference}} or complementary palette. Clean white background, professional vector-quality icon design.`
   - Aspect ratio: 1:1

### Phase B — Brand Application Mockup

4. **Real-world mockup** — `muapi image generate` (model=`nano-banana-pro`):
   - Prompt: `{{brand_name}} logo brand mockup presentation — shows logo applied to: business card (front/back), coffee cup, letterhead, and favicon. Professional branding agency presentation style, clean white/grey background, photorealistic mockups with consistent {{mood}} brand feel.`
   - Aspect ratio: 16:9

After generation:
- Present all 3 logo concepts and ask user to pick a favorite
- Once selected, offer: dark/light variations, SVG-ready export prompt, and social media profile icon crop
- Suggest running the `design-guide` skill for a full brand system

## Notes
- Ideogram v3 excels at text legibility in logos — use it for wordmark-heavy concepts.
- Flux 2 Pro gives the most creative abstract mark interpretations.
- Always check that the brand name text is correctly spelled in the generated logo.

## Trigger Keywords

`logo`, `logo design`, `brand logo`, `logo branding`, `logo creator`, `design logo`, `branding package`, `logo generator`, `brand identity logo`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
