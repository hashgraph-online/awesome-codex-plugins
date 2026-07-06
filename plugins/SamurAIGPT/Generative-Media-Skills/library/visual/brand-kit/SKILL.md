---
slug: muapi-brand-kit
name: muapi-brand-kit
version: "1.0.0"
description: Generate a cohesive brand visual kit — logo concept, color palette moodboard, and typography pairing suggestions.
acceptLicenseTerms: true
---


# Brand Kit

**Generate a cohesive brand visual kit — logo concept, color palette moodboard, and typography pairing suggestions.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `brand_name` | text | yes | — | Name of the brand. |
| `industry` | text | yes | — | Industry or niche (e.g. "sustainable fashion", "fintech startup", "artisan bakery"). |
| `personality` | text | no | modern, trustworthy, approachable | 3–5 brand personality adjectives (e.g. "bold, edgy, youthful" or "elegant, minimal, luxury"). |
| `color_preference` | text | no | — | Optional color direction (e.g. "earthy greens and terracotta", "monochrome with gold accents"). |


## Steps

Generate a multi-asset brand exploration in one parallel plan.

### Phase A — Visual exploration (parallel)

Submit ONE the plan with:

1. **Logo concept A** — `muapi image generate` (model=gpt-image-2-text-to-image, aspect_ratio=1:1):
   - Style: minimalist wordmark or lettermark on white background, flat design.
   - Prompt: "Minimalist logo for '{{brand_name}}', {{industry}} brand, {{personality}} personality. Clean vector-style, white background, professional. {{color_preference}}".

2. **Logo concept B** — `muapi image generate` (model=nano-banana-2, aspect_ratio=1:1):
   - Style: icon + wordmark combination.
   - Prompt: "Modern logo mark + wordmark for '{{brand_name}}', {{industry}}, {{personality}}. Bold, distinctive, scalable icon design, white background. {{color_preference}}".

3. **Moodboard / Color palette** — `muapi image generate` (model=nano-banana-pro, aspect_ratio=16:9):
   - A flat design moodboard showing: 5 brand colors (as swatches with hex-like labels), lifestyle photography inspo tiles, texture samples.
   - Prompt: "Brand moodboard for a {{personality}} {{industry}} brand called '{{brand_name}}'. Show 5 color palette swatches, 4 lifestyle photo tiles, typography samples. Flat lay design, white background. {{color_preference}}".

4. **Pattern / texture asset** — `muapi image generate` (model=nano-banana-2, aspect_ratio=1:1):
   - A seamless brand pattern or texture for use in backgrounds, packaging, stationery.
   - Prompt: "Seamless brand pattern for {{brand_name}}, {{industry}}, {{personality}} aesthetic. Subtle, tileable, modern. {{color_preference}}".

### Phase B — Deliverables summary

After the plan completes, return:
- Asset references (logo A, logo B, moodboard, pattern).
- **Color palette recommendation**: 5 hex codes with roles (Primary, Secondary, Accent, Neutral Light, Neutral Dark).
- **Typography pairing**: 2 Google Font pairings appropriate for the brand personality.
- **Usage guidance**: when to use each logo variant, color do/don'ts.

## Notes
- If the user has reference images in the session, analyze their style before generating.
- Suggest logo A for digital-first brands, logo B for physical/retail brands.
- All four assets run in parallel for speed.

## Trigger Keywords

`brand kit`, `brand identity`, `logo`, `branding`, `brand design`, `visual identity`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
