---
slug: muapi-logo-generator
name: muapi-logo-generator
version: "1.0.0"
description: Quickly generate a single polished logo for any brand — fast, focused, single output with clean vector aesthetic and accurate brand name text.
acceptLicenseTerms: true
---


# Logo Generator

**Quickly generate a single polished logo for any brand — fast, focused, single output with clean vector aesthetic and accurate brand name text.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `brand_name` | text | yes | — | The brand or company name to put in the logo. |
| `style` | text | no | modern wordmark with icon, minimal | Logo style (e.g. "monogram initials", "icon + text horizontal", "bold sans-serif wordmark", "badge/emblem", "abstract mark"). |
| `industry` | text | no | technology | Industry context to guide the icon metaphor (e.g. "food & beverage", "health & wellness", "finance", "creative agency"). |
| `colors` | text | no | brand blue and white | Color scheme (e.g. "black and gold", "forest green and cream", "electric purple gradient"). |
| `background` | text | no | white | Background color for logo — "white", "black", or "transparent". |


## Steps

Submit the plan with ONE step:

1. **Logo** — `muapi image generate` (model=`ideogram-v3-t2i`):
   - Prompt: `Professional logo for "{{brand_name}}" — {{style}}, {{industry}} brand. Color scheme: {{colors}}. {{background}} background. Clean, scalable, vector-quality logo design. Legible brand name text, balanced proportions. Modern 2025 logo design, no drop shadows, no gradients unless requested, isolated on {{background}} background.`
   - Aspect ratio: 1:1
   - If `{{style}}` mentions "horizontal" or "wide" layout: aspect ratio 2:1

After generation:
- Present the logo
- Ask if they want: a dark mode version, an icon-only version, or a full branding package
- If they want the full package, suggest the `logo-branding` skill

## Notes
- Ideogram v3 is the best model for accurate text rendering in logos — always use it for logos with text.
- Always check: is the brand name spelled correctly? If not, retry with the exact spelling bolded in the prompt.
- For badge/emblem styles, add "circular badge layout, contained design" to the prompt.
- For abstract marks (no text), switch to `flux-2-pro` for more creative symbol generation.

## Trigger Keywords

`logo generator`, `make a logo`, `create logo`, `design a logo`, `quick logo`, `generate logo`, `logo for my brand`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
