---
name: magic-hour-brand-kit
description: Create, extend or apply a reusable brand kit with Magic Hour imagery, exact logos and colors, editable layouts and a practical brand guide. Use for visual identities, brand books and coordinated branded assets when Magic Hour is the chosen media provider.
license: MIT
metadata:
  author: magichourhq
  version: "1.0.0"
---

# Magic Hour brand kit

Turn a brand brief into reusable source files and finished applications. A mood board or image of a brand book is not a usable brand kit.

Use the connected Magic Hour creation MCP at `https://mcp.magichour.ai/`; otherwise follow the [connection guide](https://github.com/magichourhq/skills/blob/main/docs/quickstart.md#connect-once) or the project's existing [API integration](https://docs.magichour.ai/api-reference). Read the current tool schema and verify `account_retrieve` before paid work. Never request an API key in a public message or commit it.

## Start from what the user has

- **Apply:** existing logo, palette and type are authoritative. Produce the requested application without redesigning the identity.
- **Extend:** keep approved assets; propose only the missing decisions needed for this job.
- **Create:** infer a coherent direction from audience, product, positioning and references. When the user delegates design choices, select a direction and proceed. Present alternatives only if requested or a consequential decision is unresolved.

Extract requirements from supplied files and prior context. Ask for missing source assets or a blocking business fact, not a questionnaire of technical parameters. Show the intended deliverables and generation allowance briefly; existing authorization covers work within that allowance.

## Establish one reusable identity

Save a concise `brand.md` beside the assets: approved logo source, colors with exact values, font names and available licenses, type hierarchy, spacing, image treatment, tone, protected details and prohibited claims. Reuse an existing project brief instead of introducing another registry.

For an existing identity, preserve its actual vector/logo files. For a new simple mark, create an original editable SVG when the available design tools support it. Magic Hour image generation produces raster images; an SVG containing an embedded PNG does not become an editable vector logo. Label raster concepts as concepts. Do not promise trademark clearance or a unique registrable mark.

Keep exact wordmarks, legal copy and colors in deterministic layout layers. Use AI Image Generator for original imagery and AI Image Editor with the approved product or identity reference for controlled applications. A generated logo approximation must not silently replace the master. Inspect the actual output before approving it.

## Make the kit usable

For a starter kit, deliver the smallest set that serves the brief: identity source, light/dark logo variants where needed, color/type rules, one finished application and a readable guide. If the user requests a complete rollout, read [applications and exports](references/applications.md) and finish the named placements. Do not replace requested deliverables with a contact sheet of mockups.

Generate one representative application before expanding a costly set. Reuse accepted assets; read current costs and stay inside the authorized budget. Persist each created project ID, poll that ID with `wait_for_image_project`, download the exact returned URL, and inspect dimensions, label fidelity and composition. A timeout or expired link calls for retrieval, not another paid creation.

Render the guide and applications at their actual delivery size. Check legibility, exact logo and copy, padding and clipping. A logo on a gradient needs inspection at both light and dark areas. Separate screen RGB examples from printer-specific CMYK, bleed and production requirements.

Return the finished application first, then the guide and editable sources with a short file index. Preserve font dependency and any source watermark. State what was actually generated, composed and reviewed. On a revision, change only affected outputs: a headline edit should not regenerate product photography; a palette revision may require re-exporting layouts but not recreating an unchanged logo.
