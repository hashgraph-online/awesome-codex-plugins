---
slug: muapi-blog-header
name: muapi-blog-header
version: "1.0.0"
description: Create a professional, eye-catching blog post header image sized for web (1200×628) with optional title composition guidance.
acceptLicenseTerms: true
---


# Blog Header

**Create a professional, eye-catching blog post header image sized for web (1200×628) with optional title composition guidance.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `topic` | text | yes | — | The blog post topic or title (e.g. "10 productivity hacks for remote developers"). |
| `publication_style` | text | no | clean, editorial, modern, professional | Visual style matching the blog's brand (e.g. "dark tech blog", "warm lifestyle", "minimalist corporate"). |
| `dominant_color` | text | no | — | Optional primary color direction (e.g. "deep blue", "warm amber", "monochrome"). |


## Steps

Generate a single, publication-quality blog header in one shot — no plan needed unless the user requests variants.

1. Derive a strong visual metaphor for `{{topic}}`:
   - Avoid cliché stock photo compositions (handshake, lightbulb alone).
   - Prefer: dynamic flat lay, abstract concept visualization, illustrated scene, or dramatic lifestyle moment.
2. Build the image prompt:
   - Subject derived from the metaphor above.
   - Style: `{{publication_style}}, editorial photography, 16:9 wide, professional blog header, `
     `ample negative space on the left side for title text overlay, {{dominant_color}} color palette`.
   - Tier: quality.
   - Aspect ratio: 1.91:1 (standard Open Graph / blog hero).
3. Call `muapi image generate` (model=gpt-image-2-text-to-image, aspect_ratio=21:9).

### Deliverables

Return:
- The header image asset.
- **Title placement guidance**: where to overlay the blog title for best readability.
- **Quick alt-text**: SEO-friendly image alt text (1 sentence).

## Notes
- Leave empty space (negative space) intentionally so titles can be overlaid without clashing.
- If the user uploads an existing brand photo, use `muapi image edit` to adapt it instead of generating from scratch.
- For dark-mode blogs, suggest a dark background; for light, keep backgrounds bright.

## Trigger Keywords

`blog header`, `blog image`, `article image`, `featured image`, `og image`, `open graph image`, `hero image`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
