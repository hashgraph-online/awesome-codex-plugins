# Flexbox Math Rules

Rules for applying flexbox math in production front-end work.

Source: Chapter 5: Flexbox math; see `../source-map.md`.

## Core Rules

### 1. Find flex-basis first

Do not reason about grow or shrink until each item base size is known.

### 2. Distribute positive free space by grow weights

If the container is larger than base sizes plus gaps, use flex-grow ratios.

### 3. Distribute negative free space by scaled shrink factors

Shrink uses factor times base size, so large items usually shrink more.

### 4. Account for min and max constraints after distribution

Constraints can freeze items and force a second pass of distribution.

### 5. Use flex shorthand intentionally

Avoid ambiguous flex values when the basis matters.

### 6. Prefer grid for two-dimensional placement

Use flexbox for one-dimensional distribution and alignment.

## Guidelines

Less strict recommendations:

- Set min-width: 0 on flex children that need to shrink text or overflow-prone content.
- Use flex: 1 1 0 for equal distribution that ignores intrinsic widths.
- Use flex: 0 0 auto for fixed-size controls.
- Treat gaps as consumed space before free-space distribution.

## Exceptions

When these rules may be relaxed:

- **Intrinsic content controls size**: Some UI elements should keep content-based width rather than equalize.
- **Wrapped rows**: Once flex-wrap creates multiple lines, each line distributes space independently.

## Quick Reference

| Rule | Summary |
|------|---------|
| Find flex-basis first | Do not reason about grow or shrink until each item base size is known. |
| Distribute positive free space by grow weights | If the container is larger than base sizes plus gaps, use flex-grow ratios. |
| Distribute negative free space by scaled shrink factors | Shrink uses factor times base size, so large items usually shrink more. |
| Account for min and max constraints after distribution | Constraints can freeze items and force a second pass of distribution. |
| Use flex shorthand intentionally | Avoid ambiguous flex values when the basis matters. |
| Prefer grid for two-dimensional placement | Use flexbox for one-dimensional distribution and alignment. |
