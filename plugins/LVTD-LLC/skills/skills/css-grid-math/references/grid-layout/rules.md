# CSS Grid Math Rules

Rules for applying css grid math in production front-end work.

Source: Chapter 4: CSS Grid math; see `../source-map.md`.

## Core Rules

### 1. Model placement with line numbers

Convert item start/end positions into line coordinates before guessing CSS.

### 2. Subtract gaps before dividing fr space

Available fr space is the container space left after fixed tracks and gaps.

### 3. Remember that fr is leftover space

Intrinsic minimums, maxes, and content constraints can change the actual distribution.

### 4. Use negative lines for edge anchoring

Use -1 and related indexes when items should track the end of a changing grid.

### 5. Use minmax() for resilient cards

Avoid fixed card columns when content and viewport size vary.

### 6. Choose auto-fit or auto-fill deliberately

Use auto-fit when empty tracks should collapse; auto-fill when the track rhythm should remain.

## Guidelines

Less strict recommendations:

- Write the grid as algebra when track sizes are not obvious.
- Name lines when numeric placement becomes hard to read.
- Account for box sizing and gaps before solving track widths.
- Inspect computed track sizes in DevTools when intrinsic content participates.

## Exceptions

When these rules may be relaxed:

- **Dense unknown content**: Auto-placement can be preferable to line math when item count and size vary widely.
- **One-dimensional layout**: Use flexbox when only one axis needs distribution.

## Quick Reference

| Rule | Summary |
|------|---------|
| Model placement with line numbers | Convert item start/end positions into line coordinates before guessing CSS. |
| Subtract gaps before dividing fr space | Available fr space is the container space left after fixed tracks and gaps. |
| Remember that fr is leftover space | Intrinsic minimums, maxes, and content constraints can change the actual distribution. |
| Use negative lines for edge anchoring | Use -1 and related indexes when items should track the end of a changing grid. |
| Use minmax() for resilient cards | Avoid fixed card columns when content and viewport size vary. |
| Choose auto-fit or auto-fill deliberately | Use auto-fit when empty tracks should collapse; auto-fill when the track rhythm should remain. |
