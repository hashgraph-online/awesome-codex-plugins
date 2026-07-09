# Responsive Layout Math Checklist

Use when applying or reviewing responsive layout math.

Source: Chapter 6: The mathematics of responsive design; see `../source-map.md`.

## Before You Start

- [ ] Identify the UI behavior or layout value being calculated.
- [ ] List all known inputs and units.
- [ ] Decide whether the browser can solve the relationship declaratively.

## Review Checks

- [ ] Identify the parent box for every percentage.
- [ ] Define minimum and maximum acceptable sizes before writing clamp().
- [ ] Use structural breakpoints only where the layout actually changes.
- [ ] Check classic and modern viewport units for mobile full-height regions.
- [ ] Verify at narrow, mid, wide, and zoomed viewports.

## Red Flags

Stop and address if you find:

- Layout jumps too abruptly: Use clamp() or proportional sizing before adding more breakpoints.
- 100vh section cuts off on mobile: Evaluate svh, lvh, dvh, or min-height instead.
- Nested columns are unexpectedly narrow: Trace percentage calculations through parent boxes.

## Quick Reference

| Aspect | Ideal | Acceptable | Red Flag |
|--------|-------|------------|----------|
| Units | Named and consistent | Converted locally | Mixed without conversion |
| Bounds | Min and max tested | One bound tested | No boundary checks |
| Ownership | CSS or JS clearly owns math | Boundary documented | Same formula duplicated |
