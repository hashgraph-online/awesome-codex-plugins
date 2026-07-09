---
slug: muapi-url-to-design
name: muapi-url-to-design
version: "1.0.0"
description: Analyze a website URL and generate a redesigned, improved UI — recreate the visual design with modern aesthetics, better hierarchy, and fresh brand direction.
acceptLicenseTerms: true
---


# URL to Design

**Analyze a website URL and generate a redesigned, improved UI — recreate the visual design with modern aesthetics, better hierarchy, and fresh brand direction.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `url` | text | yes | — | The website URL to analyze and redesign (e.g. "https://example.com/pricing"). |
| `page_type` | text | no | landing page | Type of page — "landing page", "pricing page", "product page", "dashboard", "about page". |
| `redesign_style` | text | no | modern, minimal, premium, dark mode | The target visual style for the redesign (e.g. "glassmorphism, vibrant gradient", "clean corporate, light mode"). |
| `keep_brand` | text | no | yes | Whether to keep existing brand colors/logo — "yes" or "no" (fully reimagine). |
| `screenshot` | image_url | no | — | Optional screenshot of the current page if URL cannot be crawled. |


## Steps

### Phase A — Redesign Generation

Submit the plan with TWO parallel steps:


1. **Full-page redesign mockup** — If `{{screenshot}}` is provided, use `muapi image edit` (model=`gpt4o-edit`); otherwise use `muapi image generate` (model=`gpt4o-text-to-image`):
   - Prompt: `Professional UI/UX redesign of a {{page_type}} for the website at {{url}}. {{redesign_style}} design. Modern web design, 2025 aesthetic. Includes: hero section with clear headline and CTA button, features/benefits section, social proof, clean footer. Pixel-perfect, Figma-quality mockup. Desktop viewport, 1440px width design.`
   - If `{{keep_brand}}` is "no", add: `Completely reimagined brand identity, new color palette.`
   - Aspect ratio: 9:16 (tall to show full page sections)

2. **Mobile version mockup** — `muapi image generate` (model=`bytedance-seedream-v4.5`):
   - Prompt: `Mobile-first responsive redesign of the same {{page_type}} — {{redesign_style}} style. iPhone 15 Pro frame, scrollable layout. Clean mobile navigation, thumb-friendly CTAs, optimized for 390px width. Modern 2025 mobile UI design.`
   - Aspect ratio: 9:19.5

After generation:
- Present both desktop and mobile mockups side by side
- Provide a written summary of design improvements made
- Offer to generate specific sections (hero, pricing cards, testimonials) as separate assets

## Notes
- If the URL is unreachable, ask the user to provide a screenshot or describe the current design.
- Always improve: typography hierarchy, whitespace, CTA visibility, and mobile responsiveness.

## Trigger Keywords

`url to design`, `redesign website`, `website redesign`, `ui redesign`, `landing page design`, `page redesign`, `website to design`, `convert url to design`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
