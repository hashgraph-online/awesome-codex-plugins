# Generation

Load this reference for Phase 3 (generating the deck) and Phase 4 (PPT conversion). The fixed-stage rules in `SKILL.md` and the Phase 5 visual-QA evidence gate bind every generated deck.

## Phase 3: Generate Presentation

Generate the full presentation using content from Phase 1 (text, or text + curated images) and style from Phase 2.

If images were provided, the slide outline already incorporates them from Step 1.2. If not, CSS-generated visuals (gradients, shapes, patterns) provide visual interest — this is a fully supported first-class path.

Apply the user's density choice throughout the deck:

- **Low density / speaker-led:** Use more slides with fewer ideas per slide. Favor large headings, short phrases, visual metaphors, section beats, quote/statement slides, and presenter-friendly pacing.
- **High density / reading-first:** Make slides more self-contained. Use structured grids, comparison tables, annotated diagrams, captions, and concise explanatory copy. Keep hierarchy strong so it feels designed, not like a document pasted onto slides.

If the user's stated needs are mixed, choose the closer of the two modes instead of inventing a middle option: live audience persuasion defaults low-density; async circulation or detailed review defaults high-density.

Never let high density become visual clutter. If a high-density slide starts to overflow, split it or redesign it into a clearer structure.

If the user selected a bold template from `bold-template-pack`, read that one template's full `design.md` before generating. Do not read the other bold templates. Treat `design.md` as the design recipe:

- Preserve its fonts, palette, decorative vocabulary, spacing rhythm, and component grammar.
- Generate the final deck as a fixed 1920×1080 stage scaled uniformly to the viewport, regardless of whether the source template originally used `deck-stage.js` or viewport-fluid CSS.
- Treat viewport-fluid values in `design.md` as design proportions to translate into 1920×1080 stage coordinates. Do not keep them as live viewport reflow rules in the final deck.
- Keep the output as a single self-contained Frontend Slides HTML file.
- Do not copy demo slide content or mimic the source template too literally.
- Use `template.html` only as a last-resort implementation reference for the selected template.
- After generating, verify both content overflow and panel overlap in rendered browser screenshots. `scrollHeight` checks alone are not enough because grid panels can visually cover each other.

If the user selected a self-generated custom wildcard, treat that preview's CSS and layout as the design recipe:

- Preserve its fonts, palette, decorative vocabulary, spacing rhythm, grid logic, and component grammar.
- Expand the same visual system across the full deck. Do not switch to a preset or bold template after the user has chosen the custom direction.
- Design any missing slide layouts from that system rather than importing patterns from another style.
- Keep the output fixed-stage, single-file, and visually verified like every other deck.

**Before generating, read these supporting files:**

- [html-template.md](../html-template.md) — HTML architecture and JS features
- [viewport-base.css](../viewport-base.css) — Mandatory CSS (include in full)
- [animation-patterns.md](../animation-patterns.md) — Animation reference for the chosen feeling. Its patterns follow the frontend skill's shared motion floor ([`motion-core.md`](../../superloopy-frontend/references/motion-core.md)): animate transform/opacity/filter only, and respect `prefers-reduced-motion`

**Key requirements:**

- Single self-contained HTML file, all CSS/JS inline
- Include the FULL contents of viewport-base.css in the `<style>` block
- Use fonts from Fontshare or Google Fonts — never system fonts
- Add detailed comments explaining each section
- Every section needs a clear `/* === SECTION NAME === */` comment block

## Phase 4: PPT Conversion

When converting PowerPoint files:

> **Helper script paths:** the packaged scripts live in THIS skill's directory, not the user's project. In every command below, `$SKILL_DIR` means this skill's base directory (announced when the skill loads) — e.g. `SKILL_DIR=~/.claude/skills/slides`. Running `bash scripts/...` from the project root will fail with "No such file or directory".

1. **Extract content** — Run `python "$SKILL_DIR/scripts/extract-pptx.py" <input.pptx> <output_dir>` (install python-pptx if needed: `pip install python-pptx`)
2. **Confirm with user** — Present extracted slide titles, content summaries, and image counts
3. **Style selection** — Proceed to Phase 2 for style discovery
4. **Generate HTML** — Convert to chosen style, preserving all text, images (from assets/), slide order, and speaker notes (as HTML comments)
