# Flexbox Math Checklist

Use when applying or reviewing flexbox math.

Source: Chapter 5: Flexbox math; see `../source-map.md`.

## Before You Start

- [ ] Identify the UI behavior or layout value being calculated.
- [ ] List all known inputs and units.
- [ ] Decide whether the browser can solve the relationship declaratively.

## Review Checks

- [ ] Identify the main axis.
- [ ] Record each item flex-basis and gap.
- [ ] Determine whether free space is positive or negative.
- [ ] Apply grow or shrink distribution.
- [ ] Check min/max constraints and wrapping behavior.

## Red Flags

Stop and address if you find:

- Equal flex values produce unequal widths: Check flex-basis and intrinsic content.
- Long text breaks the row: Add min-width: 0 and explicit overflow behavior.
- One item stops shrinking: Check min-width, min-content, and frozen constraint behavior.

## Quick Reference

| Aspect | Ideal | Acceptable | Red Flag |
|--------|-------|------------|----------|
| Units | Named and consistent | Converted locally | Mixed without conversion |
| Bounds | Min and max tested | One bound tested | No boundary checks |
| Ownership | CSS or JS clearly owns math | Boundary documented | Same formula duplicated |
