# CSS Math Units Checklist

Use when applying or reviewing css math units.

Source: Chapter 3: Math basics for CSS; see `../source-map.md`.

## Before You Start

- [ ] Identify the UI behavior or layout value being calculated.
- [ ] List all known inputs and units.
- [ ] Decide whether the browser can solve the relationship declaratively.

## Review Checks

- [ ] Identify whether each unit is absolute or relative.
- [ ] Find the parent/root/reference value for each relative unit.
- [ ] Resolve custom properties into the final expression.
- [ ] Check box-sizing before calculating final dimensions.
- [ ] Verify min/max/clamp bounds at extreme viewport widths.

## Red Flags

Stop and address if you find:

- Font sizes grow unexpectedly: Look for nested em multiplication.
- Box is wider than declared width: Check content-box padding and border.
- calc() is invalid: Check missing spaces around operators or incompatible units.

## Quick Reference

| Aspect | Ideal | Acceptable | Red Flag |
|--------|-------|------------|----------|
| Units | Named and consistent | Converted locally | Mixed without conversion |
| Bounds | Min and max tested | One bound tested | No boundary checks |
| Ownership | CSS or JS clearly owns math | Boundary documented | Same formula duplicated |
