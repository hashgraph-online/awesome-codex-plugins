---
name: book-illustrate
description: "Generate interior illustrations for book chapters. Analyzes scenes, creates style-consistent illustration prompts, and produces illustration plan with placement metadata."
---

# Interior Illustration Pipeline

Orchestrates the illustration generation process for book chapters.

## Prerequisites

- Project must have `PRD.md` and at least one chapter draft in `drafts/`
- `STYLE.md` should exist for art direction (falls back to genre defaults if missing)

## Pipeline

### Step 1: Generate Illustration Plan

Invoke the `illustrator` agent:

```
Read the book's PRD.md, STYLE.md, outline.md, and all chapter drafts in drafts/.
For each chapter, identify 2-4 key visual moments suitable for illustration.
Generate style-consistent illustration prompts with a reusable style seed.
Output the complete plan to publish/illustrations/plan.md and manifest.json.
```

The agent will:
1. Read STYLE.md for art direction (or infer from genre)
2. Scan each chapter for illustration-worthy scenes
3. Create a style seed prompt for consistency
4. Generate prompts for each scene in multiple tiers
5. Write the plan and manifest

### Step 2: Review Plan

Present the illustration plan to the user for review:
- Total illustration count
- Per-chapter distribution
- Style seed summary
- Key scenes selected

Ask the user to approve, modify scene selections, or adjust the style direction.

### Step 3: Execute (Optional — requires image generation tools)

If image generation MCP tools are available (claude-image-gen, Replicate, etc.):
- Generate images using the prompts from the plan
- Save to `publish/illustrations/ch{NN}-{scene-slug}.jpg`
- Optimize file sizes (compress to <500KB for EPUB compatibility)

If no image generation tools are available:
- The plan.md serves as the executable spec
- User can use the prompts in Midjourney, DALL-E, Stable Diffusion, or any external tool
- Place generated images in `publish/illustrations/` following the naming convention

### Step 4: Integration

Insert illustration references into chapter drafts:

```markdown
![{alt text}](../illustrations/ch{NN}-{slug}.jpg)
```

Placement rules:
- `chapter-header`: After the chapter title heading
- `full-page`: On its own line, between paragraphs at the scene location
- `inline`: Within the paragraph flow
- `spot`: As a decorative element at section breaks

## Output Structure

```
publish/illustrations/
├── plan.md                    # Illustration plan with prompts
├── manifest.json              # Machine-readable summary
├── ch01-opening-scene.jpg     # Generated images (if executed)
├── ch01-climax.jpg
├── ch02-meeting.jpg
└── ...
```

## EPUB Compatibility

- All images: JPEG format, RGB, sRGB color space
- Target: <500KB per image for reasonable EPUB file size
- Recommended dimensions: 800x1200px (full-page), 1600x533px (header), 600x600px (inline/spot)
- pandoc automatically embeds images referenced in markdown

## Post-Completion

Update the project dashboard status:

```bash
node {PLUGIN_ROOT}/skills/book-status/scripts/scan-project.js [project-dir] --plugin-root={PLUGIN_ROOT}
```
