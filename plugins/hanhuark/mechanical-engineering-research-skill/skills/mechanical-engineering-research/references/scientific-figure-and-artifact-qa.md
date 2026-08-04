# Scientific Figure And Artifact QA

Use this reference for publication figures, tables, Word files, PDFs, spreadsheets, slide decks, posters, and final deliverable audits.

## Figure Role

Give every figure or table one scientific job. Record the question it answers, claim it supports, source data, generation script, and manuscript location.

Prefer relationship-first schematics that show the physical system, raw observables, transformations or equations, model stages, outputs, and feedback. Distinguish physical causality from data flow. Include a representative raw case before aggregate/model results when it builds trust in the analysis.

## Final-Size Figure Check

Render at the actual manuscript or slide size and inspect:

- font family and legibility;
- clipping, overlap, marker occlusion, and annotation collisions;
- axis variable, units, range, scale, and significant digits;
- logical legend and category order;
- color and grayscale distinguishability;
- panel labels and cross-panel comparability;
- raster resolution and editable/vector source where appropriate;
- uncertainty representation and claim limits;
- caption completeness and consistency with the plotted data.

Do not encode one typeface, forced float specifier, or punctuation rule as universal. Follow the venue and verify the rendered result.

## Manuscript Integration

- Cite and interpret every main figure and table.
- Place each item reasonably near its first substantive discussion.
- Keep evidence needed for the main conclusion in the main manuscript. Use supplements for derivations, preprocessing, robustness detail, and secondary diagnostics.
- Use labels and cross-references rather than hard-coded numbers.
- After moving or removing content, audit numbering, captions, permissions, and narrative roles.

## Artifact-Level QA

Use a format-specific skill or renderer when available. Inspect the delivered artifact, not only source text.

For Word/PDF:

- render every page or a complete contact sheet;
- check page count, headers/footers, broken glyphs, equations, cross-references, tracked changes/comments, metadata, and blank or clipped pages;
- scan for placeholders, prompts, revision residue, and hidden instructions.

For spreadsheets:

- inspect formulas, ranges, units, hidden sheets/rows, filters, named ranges, charts, error values, and source links;
- distinguish formulas from pasted values and verify representative calculations.

For presentations/posters:

- inspect every slide at presentation size;
- check content collisions, crop, media, notes, font substitution, aspect ratio, and transition logic;
- keep technical visuals dominant and move dense support material to backup slides.

Text extraction can detect content differences but cannot verify visual equivalence. Raster comparison can detect layout changes but cannot establish semantic equality. Use both when comparing clean and marked PDFs.

## Completion Gate

Report the exact artifact path, generation command, renderer or engine, test result, and any page/slide/sheet not visually checked. Do not call an artifact submission-ready when only the source compiled.
