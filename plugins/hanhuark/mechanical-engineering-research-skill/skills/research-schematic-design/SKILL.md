---
name: research-schematic-design
description: Create publication-quality, editable scientific and engineering schematics with explicit physical meaning, exact labels, visual hierarchy, and provenance. Use for experimental facilities, thermal-fluid mechanisms, workflows, graphical abstracts, system architectures, or research diagrams.
---

# Research Schematic Design

## Purpose

Create figures that clarify a scientific claim without inventing evidence. A publication schematic is an engineering artifact: its geometry, flow directions, symbols, labels, color semantics, and stated scale must agree with the manuscript, data, and method.

## Route To References

- Read `references/schematic-brief.md` to turn the request into a complete technical brief.
- Read `references/schematic-workflow.md` to choose native-vector, hybrid, or image-editing production.
- Read `references/scientific-visual-qa.md` before delivering or inserting a figure into a manuscript, slide deck, proposal, or poster.
- Start from `assets/templates/schematic-brief.yaml` when the user needs a reusable figure specification.

## Core Rules

- Default to an editable, native-vector source for system diagrams, facility schematics, workflows, labels, arrows, dimensions, equations, and legends. Use SVG, PowerPoint objects, or another requested editable format.
- Use image generation only for visual concepts, non-semantic textures, or a reference composition. Never trust generated in-image text, arrow direction, numerical values, symbols, dimensions, or geometry as the final scientific content.
- Recreate every final label, arrow, line, icon, legend, and quantitative annotation deterministically after a generated concept is selected.
- Distinguish measured apparatus, simulated domains, proposed systems, conceptual mechanisms, and illustrative elements. Do not depict unmeasured mechanisms as observed facts.
- Preserve source and rights boundaries. Do not trace or reproduce a third party's figure without permission; use supplied references for inspiration and create an original composition.

## Workflow

1. Identify the figure's single job: explain a facility, mechanism, workflow, comparison, or overall research story.
2. Build the schematic brief: audience, target size, required components, exact labels and units, connections, evidence class, visual hierarchy, and exclusions.
3. Choose the production lane:
   - **Native vector:** default for facilities, flow paths, process diagrams, methods, system architectures, and graphical abstracts with exact labels.
   - **Hybrid:** generate one or more concept frames for composition or material cues, then reconstruct the accepted concept as editable vector objects.
   - **Controlled image edit:** use only when a supplied image must retain visual information; overlay all technical annotations as deterministic vector elements.
4. Build the source artifact and a rendered preview. Keep the figure uncluttered, with one visual grammar for arrows, line weights, colors, labels, and callouts.
5. Run the scientific visual QA before delivery. Verify every label against the source material and inspect the figure at final use size.

## Required Output

When creating a final schematic, deliver:

- an editable source artifact;
- a publication or presentation preview in the requested format;
- the completed brief or a compact provenance note identifying source material, generated illustrative elements, and non-scale elements; and
- the exact visual and technical checks performed.

Do not call a schematic final when only a concept image exists or when final-size legibility has not been inspected.
