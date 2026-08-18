# Frontend Math Foundations Checklist

Use when applying or reviewing frontend math foundations.

Source: Chapter 1: Web dev math fundamentals; see `../source-map.md`.

## Before You Start

- [ ] Identify the UI behavior or layout value being calculated.
- [ ] List all known inputs and units.
- [ ] Decide whether the browser can solve the relationship declaratively.

## Review Checks

- [ ] Write down the value being solved.
- [ ] List inputs and units.
- [ ] Choose arithmetic, ratio, linear equation, inequality, geometry, or coordinates.
- [ ] Decide whether CSS or JavaScript owns the calculation.
- [ ] Test minimum, maximum, and representative middle cases.

## Red Flags

Stop and address if you find:

- Formula works only for one viewport: Look for fixed values where ratios or linear equations belong.
- CSS and JS duplicate the same calculation: Pick one owner and expose tokens or measured values across the boundary.
- Layout math is hard to explain: Name intermediate values and preserve units.

## Quick Reference

| Aspect | Ideal | Acceptable | Red Flag |
|--------|-------|------------|----------|
| Units | Named and consistent | Converted locally | Mixed without conversion |
| Bounds | Min and max tested | One bound tested | No boundary checks |
| Ownership | CSS or JS clearly owns math | Boundary documented | Same formula duplicated |
