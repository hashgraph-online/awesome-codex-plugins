# Content discovery

Load this reference for Phase 1 of a new presentation.

## Phase 1: Content Discovery (New Presentations)

**Ask ALL questions together** so the user fills everything out at once. If the current environment provides a native structured-question UI, use it; otherwise ask in one concise message with clearly numbered choices:

**Question 1 — Purpose** (header: "Purpose"):
What is this presentation for? Options: Pitch deck / Teaching-Tutorial / Conference talk / Internal presentation

**Question 2 — Length** (header: "Length"):
Approximately how many slides? Options: Short 5-10 / Medium 10-20 / Long 20+

**Question 3 — Content** (header: "Content"):
Do you have content ready? Options: All content ready / Rough notes / Topic only

**Question 4 — Density** (header: "Density"):
How dense should the deck feel? Options:

- "Low density / speaker-led" — Big ideas, fewer words, more visual breathing room
- "High density / reading-first" — More self-contained detail for async reading

**Do not ask about inline editing during Phase 1.** Users should not have to choose editing behavior before seeing a draft. Inline editing is a post-draft affordance: include it by default unless the user explicitly asks for a locked/export-only file.

Remember the user's density choice. It affects slide count, typography scale, amount of text per slide, layout density, and whether to favor cinematic presenter slides or self-contained reading slides.

If user has content, ask them to share it.

### Step 1.2: Image Evaluation (if images provided)

If user selected "No images" → skip to Phase 2.

If user provides an image folder:

1. **Scan** — List all image files (.png, .jpg, .svg, .webp, etc.)
2. **Inspect each image** — Use the agent's available image-understanding capability. If image reading is unavailable, use filenames/metadata and ask the user to clarify only when needed
3. **Evaluate** — For each: what it shows, USABLE or NOT USABLE (with reason), what concept it represents, dominant colors. Classify each asset's authority the way [`image-first.md`](../../superloopy-frontend/references/image-first.md) does — authorized capture, approved generated asset, or supplied reference — and never present a rebuilt mock as a real product screenshot or use marks the user is not authorized to show
4. **Co-design the outline** — Curated images inform slide structure alongside text. This is NOT "plan slides then add images" — design around both from the start (e.g., 3 screenshots → 3 feature slides, 1 logo → title/closing slide)
5. **Confirm the outline** using the same structured-question mechanism when available: "Does this slide outline and image selection look right?" Options: Looks good / Adjust images / Adjust outline

**Logo in previews:** If a usable logo was identified, embed it (base64) into each style preview in Phase 2 — the user sees their brand styled three different ways.
