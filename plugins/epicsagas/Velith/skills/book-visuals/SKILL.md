---
name: book-visuals
description: "Book visual system: art bible and look lock, figure plan per chapter, code-rendered diagrams/charts/technical drawings, diffusion-generated illustrations and spot art, photo sourcing policy, cover, model-agnostic prompt compilation, vision QA, and asset validation for print and EPUB. Every image matches the book, the chapter, and the author's brief regardless of which image model renders it."
argument-hint: "[project-dir] [plan|lock|render|generate|add \"prompt\" --chapter N --type T|check|all] [--execute]"
---

# Book Visuals

Goal: every image in the book looks like it belongs to this book, sits where the text needs it, and is release-ready on the first export. Images that vary with the model, drift between chapters, or decorate instead of doing work are the visual equivalent of AI prose tells.

Read `${CLAUDE_PLUGIN_ROOT}/skills/loom/quality-bar.md` (the visual section) and the genre skill's **Visuals** section.

## Why images go wrong, and the fix

| Cause | Fix in this pipeline |
|-------|----------------------|
| No shared visual spec; each prompt invents a style | `art-bible.md`: one canonical look, palette, medium, composition rules, character and setting constants, negative rules. Every prompt is derived from it |
| Free-form prompts differ per backend | `velith.mjs images compile`: one structured image spec → per-backend prompt syntax (Midjourney, gpt-image, Stable Diffusion/FLUX, Imagen, Ideogram) with the art bible baked in |
| Diagrams and drawings rendered by diffusion models | Never. Diagrams, charts, technical drawings, maps' base layers are **code-rendered** (Mermaid, D2, Graphviz, SVG, matplotlib/Vega) by `figure-engineer`. Text-accurate, editable, print-safe |
| No rejection loop | `art-director` reads every generated image (vision), scores it against the art bible, rejects and regenerates with corrected prompts; reviews the full contact sheet for consistency |
| Images bolted on after drafting | Figure plan in the outline; chapter-writer places figure references with captions while drafting; fact-checker verifies figures match text |
| Assets fail at export | `velith.mjs images check`: dimensions, aspect, size, color mode notes, alt text, broken references, manifest coverage |

## Image types and who makes them

| Type | Made by | Method | Used in |
|------|---------|--------|---------|
| Diagram (architecture, flow, sequence, concept map) | `figure-engineer` | Mermaid / D2 / Graphviz → SVG (+ PNG for print) | technical, nonfiction, academic |
| Chart (data) | `figure-engineer` | matplotlib / Vega-Lite from a data file in `sources/` | nonfiction, academic, technical |
| Technical drawing, floor plan, schematic, 도면 | `figure-engineer` | SVG with real dimensions, or TikZ; DXF export on request | technical, nonfiction, game |
| Table-as-figure, comparison matrix | `figure-engineer` | Markdown table first; SVG only when layout demands | all |
| Map (fantasy, historical, game world) | `figure-engineer` base (SVG from bible geography) + `illustrator` stylization | hybrid | fiction, game, nonfiction |
| Scene illustration, full-page, chapter header, spot art | `illustrator` | diffusion backend with art bible + references | fiction, poetry, children's, memoir |
| Character sheet, setting reference | `illustrator` (after look lock) | diffusion; becomes reference for later images | fiction, game, screenplay pitch |
| Photograph | author or licensed stock; pipeline sources and records license | never generated for documentary use; AI-generated "photos" only as clearly stylized art with disclosure | nonfiction, memoir, technical |
| Cover | `cover-designer` | diffusion for art + typography spec; Ideogram-class model if title text must be in-image | all |
| Ornaments, dividers, drop caps | `figure-engineer` | SVG, consistent with art bible | all |

## Workflow

### 1. Art bible (`/book-visuals plan`)

Invoke `art-director`. It reads `PRD.md`, `STYLE.md`, `bible.md`, `outline.md`, existing drafts, and any author-supplied references in `visuals/ref/`, then writes:

- `art-bible.md` (human) and `.velith/art-bible.json` (machine): medium, technique, movement or era descriptors (never living artists' names), line, palette with roles, value range, lighting, texture, detail level, composition rules, safe margins, aspect per placement, mood words, negative rules; character and setting constants (fiction); figure system (diagram grammar, node and edge semantics, font, color roles, caption style, grayscale survivability) for nonfiction and technical; photo policy; backend profile.
- `visuals/plan.md` and `visuals/manifest.json`: the figure list. Per image: id, chapter, placement, type, purpose (what the reader learns or feels that the text alone cannot deliver), maker, source data or scene, caption, alt text, status.

For nonfiction and technical books, the figure list is part of the argument: each figure has a purpose sentence, and a figure without one is cut. For fiction, 0-4 illustrations per chapter by weight; a chapter can have none.

### 2. Look lock (`/book-visuals lock`)

Before producing volume, produce three candidate style samples of the same subject (the book's most representative image) with three variants of the art bible. The author picks one. Record the choice, the reference image path, and the backend settings (style reference, seed) in the art bible. **Required stop.** For books with no diffusion images (pure technical), the look lock is a rendered sample figure instead.

### 3. Produce

- `figure-engineer` renders every code-based figure: source file in `visuals/figures/src/`, output SVG and PNG (300 dpi at final size) in `visuals/figures/`. Verifies labels against the chapter text and the bible's term rules. Every figure survives grayscale.
- `illustrator` compiles prompts (`velith.mjs images compile`), generates when an image tool is available (`--execute`) or hands the compiled prompt pack to the author, then runs vision QA on each result: reads the image, scores against the art bible (palette, medium, character constants, composition, artifacts, text contamination), rejects and regenerates with a corrected prompt up to three times, then escalates.
- `cover-designer` works from the art bible, produces concepts and the print/ebook/audiobook/marketing variants, and hands the chosen art to `art-director` for the consistency review.
- Photos: `art-director` writes the shot list or stock brief, records license and attribution in `visuals/manifest.json`, applies the treatment defined in the art bible.

### 4. Author brief (`/book-visuals add "prompt" --chapter N --type T`)

The author's prompt is an intent, not the final prompt. `art-director` interprets it through the art bible and the chapter's content, writes the spec, and the appropriate maker produces it. The result matches the book even if the author's prompt named a different style; if the author explicitly wants to break the art bible, they say so and the exception is recorded.

### 5. Check (`/book-visuals check`)

`node ${CLAUDE_PLUGIN_ROOT}/velith.mjs images check <project-dir>`: every manifest entry has a file; dimensions meet the placement minimum; aspect within 5%; file size within EPUB budget; every image reference in drafts resolves and has alt text; every file in `visuals/` is in the manifest. Then `art-director` reviews the contact sheet: consistency across all images and the cover, one final pass.

### 6. Integrate

Chapter-writer already placed references during drafting for planned figures:

```markdown
![Alt text that describes the figure for a reader who cannot see it](../visuals/figures/ch03-fig01.svg)

*Figure 3.1 — Caption in the book's voice, one sentence, ends with a period.*
```

Illustrations added after drafting are inserted by `illustrator` at the manifest's placement. `book-publish` resolves paths with `--resource-path` and prefers SVG for EPUB and PNG for PDF.

## Print and screen constraints

- Print interior: 300 dpi at final size; grayscale-safe unless the book is color; CMYK conversion at the printer's step, note it in `PUBLISH-NOTES.md`; bleed 3 mm / 0.125 in for full-bleed images.
- EPUB: JPEG or PNG, sRGB, each < 500 KB, SVG allowed for figures (EPUB 3), total image payload under 20 MB. Alt text required.
- Placement minimums: full-page 1600×2400, chapter header 2400×800, inline 1200×1200, spot 800×800, cover front 1600×2560 (2500×3750 recommended), audiobook 3200×3200, social 1200×628.
- Text in images: only on the cover, and only via a text-capable model or typography added in the layout step. Everything else: no text in the image; labels go in SVG or captions.

## Output structure

```
{project-dir}/
├── art-bible.md
├── visuals/
│   ├── plan.md
│   ├── manifest.json
│   ├── ref/                 # author references, look-lock samples, character sheets
│   ├── figures/src/         # .mmd .d2 .dot .svg .py .json sources
│   ├── figures/             # rendered svg + png
│   ├── illustrations/       # ch{NN}-{slug}.jpg|png
│   ├── photos/              # licensed, with LICENSES.md
│   └── prompts/             # compiled prompt packs per image, per backend
└── publish/cover/           # cover art and variants (unchanged path)
```

## Gate

Art bible exists with a recorded look lock. Manifest covers every planned image with status `done` or an author-accepted `deferred`. `images check` passes. Art-director consistency review recorded in `visuals/plan.md`.

## Post-completion

```bash
node ${CLAUDE_PLUGIN_ROOT}/velith.mjs scan [project-dir]
```
