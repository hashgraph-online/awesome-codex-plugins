# CSS Grid Math Checklist

Use when applying or reviewing css grid math.

Source: Chapter 4: CSS Grid math; see `../source-map.md`.

## Before You Start

- [ ] Identify the UI behavior or layout value being calculated.
- [ ] List all known inputs and units.
- [ ] Decide whether the browser can solve the relationship declaratively.

## Review Checks

- [ ] Count grid lines, not just visible cells.
- [ ] Subtract gap space from the container before solving track sizes.
- [ ] Check whether content minimums are constraining flexible tracks.
- [ ] Decide whether empty auto-repeat tracks should collapse.
- [ ] Use DevTools grid overlay to verify line placement.

## Red Flags

Stop and address if you find:

- fr columns are not equal: Check fixed tracks, gaps, min-content constraints, and max constraints.
- Item is one column off: Recount grid lines and inspect start/end line values.
- auto-fill leaves empty columns: Use auto-fit if empty tracks should collapse.

## Quick Reference

| Aspect | Ideal | Acceptable | Red Flag |
|--------|-------|------------|----------|
| Units | Named and consistent | Converted locally | Mixed without conversion |
| Bounds | Min and max tested | One bound tested | No boundary checks |
| Ownership | CSS or JS clearly owns math | Boundary documented | Same formula duplicated |
