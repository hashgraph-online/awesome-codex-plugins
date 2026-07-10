---
name: raster-logo-svg
description: Wrap raster logos (webp, png, jpg) in self-contained SVG files via base64 embedding for pixel-perfect matches. Use when creating logo SVGs, converting webp/png to svg, fixing hand-drawn logos that do not match the source, or preparing plugin/README logo assets without a vector source file.
---

# raster-logo-svg

Create an **SVG wrapper** around an existing raster logo so the output is **pixel-identical** to the source. This is not true vectorization.

## Choose the approach

| Need | Do |
|------|-----|
| Match an existing raster logo exactly | **Embed** (this skill) |
| Crisp at any size, editable paths | Export from Figma/Illustrator, or commission true vector |
| Quick monochrome outline | Potrace (usually wrong for brand logos with color/gold/type) |
| Hand-redrawn paths | Only if no raster exists and user accepts approximation |

Default to **embed** when a `.webp`, `.png`, or `.jpg` logo already exists and the user wants `.svg`.

## Workflow

1. **Source of truth** — keep the raster (e.g. `docs/logo.webp`). Do not delete it.
2. **Generate SVG** — run the script from repo root or skill directory:

```bash
python3 skills/raster-logo-svg/scripts/embed-logo.py docs/logo.webp -o docs/logo.svg -l "project-name"
```

Requires **ImageMagick** (`magick identify`) for dimensions. Install: `brew install imagemagick`.

3. **README** — prefer the **raster** in GitHub README for reliable rendering:

```markdown
<img src="docs/logo.webp" alt="project-name" width="580" />
```

Use the **SVG** for plugin manifests, favicons, npm package icons, or anywhere a `.svg` path is required.

4. **Verify** — open the SVG locally; it must look identical to the raster. Do not commit temp traces (`icon-traced.svg`, potrace output, failed hand-drawn attempts).

## Output format

The script produces:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 W H" role="img" aria-label="…">
  <image width="W" height="H" href="data:image/webp;base64,…"/>
</svg>
```

- `viewBox` matches source pixel dimensions from `magick identify`.
- MIME: `image/webp`, `image/png`, or `image/jpeg` from file extension.
- Self-contained: no external `href="logo.webp"` (breaks when SVG is copied alone).

## Tradeoffs (tell the user when relevant)

- **Pros:** Perfect visual match, fast, no design source needed.
- **Cons:** Not true vector; upscaling very large may soften (same as the raster).
- **Size:** SVG file ≈ base64(raster) + ~200 bytes overhead (~33% larger than raw binary).

## Do not

- Hand-draw paths to “recreate” a brand logo when the raster exists — results rarely match.
- Use potrace/ImageMagick trace for full-color wordmarks.
- Replace the canonical raster with only SVG unless the user explicitly drops the raster.
- Embed secrets or sensitive images in public repos without user confirmation.

## Optional: external-reference SVG

Only for local tooling that resolves sibling files (not GitHub README `<img src="logo.svg">`):

```xml
<image href="logo.webp" width="1163" height="350"/>
```

Prefer **base64 embed** for portable `.svg` files.

## Example (designer-skill)

```bash
python3 skills/raster-logo-svg/scripts/embed-logo.py \
  docs/designer-skill-mcp-logo.webp \
  -o docs/designer-skill-mcp-logo.svg \
  -l "designer-skill-mcp"
```

README uses `designer-skill-mcp-logo.webp`; plugin/icon paths can use the `.svg`.
