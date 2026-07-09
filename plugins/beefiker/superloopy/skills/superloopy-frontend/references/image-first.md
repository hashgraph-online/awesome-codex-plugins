# Image-First Discipline

Models build mediocre UI from a text prompt because prose underspecifies a layout — the gaps get filled with trained averages (centered dark hero, purple gradient, three equal cards). Fix it by committing to a concrete **visual target before coding**, so implementation becomes *translation* (high-fidelity, low-freedom) instead of *invention* (low-fidelity, infinite defaults).

## Order (mandatory for visually-important work)

1. **Secure a visual target.** In priority order:
   - Generate the design image(s) with an image-generation tool if one is available in this runtime.
   - Else capture a real reference site at a fixed viewport with the browser (reuse `superloopy-clone`'s computed-style + screenshot tooling).
   - Else use a user-provided mock/Figma, or — last resort — an authored layout sketch.
2. **Deep-analyze the target into a written spec.** Extract, enumerated: exact text/headlines/CTA wording, type scale + weight relationships, spacing/gutter rhythm, radius logic, button shapes/hierarchy, full color palette, grid logic, repeated motifs. This spec is the de-facto DESIGN.md (or its deltas) — write it to the evidence root.
3. **Implement to match the spec**, not "inspired by" it.
4. **Visual-QA compares the built UI back to the target** (Phase 3 of the skill).

## Decomposition (when generating images)

One image **per section**, never one compressed multi-section board — resolution budget per section is what keeps type, spacing, and component detail legible enough to extract faithfully. If a section is unclear, generate a fresh, closer image rather than cropping (cropping destroys spacing/scale relationships). Force a non-default composition: pick a deliberate hero architecture and section system; do not default to the left-text/right-image hero.

## Anti-drift implementation rules

- Be visually faithful to the target, translated into real frontend — not a generic reinterpretation.
- Do not simplify distinctive sections into default templates, collapse generous spacing, or swap a signature component for a plain row.
- Every token still traces to DESIGN.md; the target sets the values, the contract enforces them.

## Degrade path (no imagegen available)

If this runtime has no image-generation tool, do **not** skip the discipline — secure a reference site capture or a provided mock instead, and still produce the **written target spec** before coding. The value is the explicit, inspectable target; the generation method is interchangeable. Record the target (image, screenshot, or spec) as an artifact under `.superloopy/evidence/frontend/` so visual-QA has something to compare against.
