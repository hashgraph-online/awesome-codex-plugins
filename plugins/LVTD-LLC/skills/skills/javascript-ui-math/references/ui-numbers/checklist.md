# JavaScript UI Math Checklist

Use when applying or reviewing javascript ui math.

Source: Chapter 2: Math basics for JavaScript; see `../source-map.md`.

## Before You Start

- [ ] Identify the UI behavior or layout value being calculated.
- [ ] List all known inputs and units.
- [ ] Decide whether the browser can solve the relationship declaratively.

## Review Checks

- [ ] Check if 0, empty string, null, and undefined are distinct in the UI state.
- [ ] Guard NaN and Infinity before writing to DOM or CSS.
- [ ] Normalize negative wrapping values.
- [ ] Keep internal floats unrounded until display time.
- [ ] Avoid BigInt unless integer range truly requires it.

## Red Flags

Stop and address if you find:

- Carousel goes to -1: Normalize remainder into modulo.
- 0 is ignored as an option: Replace || defaulting with ?? where appropriate.
- Displayed sum is 0.30000000000000004: Round for display or use integer units.

## Quick Reference

| Aspect | Ideal | Acceptable | Red Flag |
|--------|-------|------------|----------|
| Units | Named and consistent | Converted locally | Mixed without conversion |
| Bounds | Min and max tested | One bound tested | No boundary checks |
| Ownership | CSS or JS clearly owns math | Boundary documented | Same formula duplicated |
