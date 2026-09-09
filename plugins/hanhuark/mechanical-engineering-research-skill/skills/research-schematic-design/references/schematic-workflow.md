# Schematic Production Workflow

## Select A Production Lane

### Native Vector

Use for nearly all technical schematics. Construct the figure directly as SVG, PowerPoint objects, or another requested editable format when exact geometry, labels, arrows, units, equations, or placement matters.

Keep semantic groups separate: apparatus or system geometry, physical arrows, data-flow arrows, labels, dimensions, legend, and purely illustrative elements. This makes later edits and manuscript resizing reliable.

### Hybrid Concept To Vector

Use image generation only to explore composition, perspective, material appearance, or a visual metaphor that the scientific brief already supports. Request no text, numbers, equations, labels, arrows, or dimensions in the generated concept. Select a concept, then reconstruct it as editable vector geometry and add all technical content deterministically.

### Controlled Image Edit

Use a supplied image when it carries real experimental or material information that a redraw would lose. Keep the source image intact, crop only when the interpretation remains valid, and place technical overlays in a separate editable layer. Do not use an image editor to silently change a measured feature.

## Image-Generation Prompt Pattern

Use a structured prompt only after the scientific brief is complete:

```text
Use case: scientific-educational
Asset type: concept reference for an engineering schematic
Primary request: <visual composition only>
Subject: <system or mechanism already supported by the brief>
Style/medium: clean technical illustration with restrained color and clear object separation
Composition/framing: <viewpoint and hierarchy>
Constraints: no text, no numbers, no equations, no labels, no dimensions, no legends, no watermark; do not add components or mechanisms not listed in the brief
Avoid: decorative effects that obscure geometry or imply unmeasured physical behavior
```

Treat the result as a composition reference, not a scientific source. Iterate one visual change at a time and preserve stated invariants.

## Vector Construction Rules

- Use actual arrowheads and paths rather than raster arrows. Differentiate heat, mass, fluid, electrical, acoustic, and data paths by a documented visual convention.
- Make labels selectable text. Keep units, symbols, and subscripts in the requested notation.
- Use an accessible palette with a legend when colors carry meaning. Do not use color alone to distinguish critical categories.
- Keep line weight, corner style, arrow style, and typography consistent. Use whitespace to separate subsystems.
- Use perspective or 3D effects only when they clarify a real spatial relationship. Otherwise prefer a clean orthographic or cutaway view.
- Mark a diagram `not to scale` when it is conceptual or when its proportions could be misread as measured geometry.

## Provenance Note

Record the source documents, photos, CAD, data, or user descriptions used; the final editable source path; the rendering method; and which elements are conceptual or generated for illustration. Do not claim that generated illustrative content was measured or simulated.
