---
name: figma-click-flow
description: "Draw or refresh a static click-flow overlay on laid-out Figma screens from prototype reactions or explicit pairs, using the existing SVG recipe and verified targets."
license: MIT
compatibility: >-
  Writes to a Figma Design file through figma-console-mcp (figma_execute, Desktop Bridge plugin
  in Figma Desktop) or through the official Figma MCP server (use_figma, Full seat, not
  validated by this repo; the recipe guards figma.loadAllPagesAsync, which Figma lists as not
  implemented there). Requires the figma-canon and figma-preflight skills.
metadata:
  author: Thiago Xikota
  version: "1.2.0"
---

# Click-flow overlay

Draw a static overlay on an existing laid-out section: origin dots, rounded
elbows and open arrows at destinations. It documents a flow; it does not create
product screens, wire a missing prototype or authorize new destinations.

Inputs: sectionId and mode (`from-prototype`, `explicit` or heuristic
`auto-layout`); explicit pairs are `{from,to}`, without a label field. Reuse
known authorized targets. If no pairs are found, report the gap instead of
drawing an empty success. Heuristic adjacency needs visual confirmation and
must not silently turn row order into a product decision.

Use `figma-preflight`, the file lock and the available write path. Design does
not support `createConnector`/cloning existing CONNECTOR nodes; use this
skill’s `references/draw-overlay.js`, parameterized without rewriting its
fragile coordinate logic. The official `use_figma` path was not validated by
this repo; obey its current runtime instructions and verify every result.

[overlay-details.md](references/overlay-details.md) preserves configuration,
geometry, page/section coordinates, mode semantics, dropped pairs, capture and
cleanup recipes. Read the applicable sections when drawing or diagnosing.
The recipe replaces the prior named overlay, so scope/ownership of that target
must be correct. Timeout/partial error requires read-back before rerun.

Verify origins on real controls, destinations, crossings, section-local
placement, count and visible geometry at a useful scale. Use plugin capture
when available and respect REST budgets. Keep project accent/canon instead of
forcing the default red. Split a dense graph when necessary for readability,
not by an arbitrary task-wide count. Report ids and dropped/uncertain pairs.
