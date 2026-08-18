# Responsive Layout Math Rules

Rules for applying responsive layout math in production front-end work.

Source: Chapter 6: The mathematics of responsive design; see `../source-map.md`.

## Core Rules

### 1. Start with the containing block

Compute percentages against the parent that actually establishes layout, not against the viewport by habit.

### 2. Use breakpoints for structural changes

Use media queries when rows, columns, navigation, or content order changes.

### 3. Use clamp() for continuous scaling

Use clamp(min, preferred, max) for widths, type, gaps, and padding that should scale smoothly.

### 4. Prefer range syntax for readability

Write media query conditions as ranges when it makes lower and upper bounds explicit.

### 5. Choose viewport units by mobile behavior

Avoid 100vh for mobile full-height UI unless browser chrome behavior is acceptable.

### 6. Bring in JavaScript only for runtime facts

Use JavaScript when the formula depends on measured content, scroll state, or container data CSS cannot express.

## Guidelines

Less strict recommendations:

- Use percentages for relationships inside a known parent.
- Use rem for spacing that should respect root font settings.
- Use clamp() when a value has known minimum and maximum bounds.
- Test narrow, middle, and wide widths; formula bugs often hide in the middle.

## Exceptions

When these rules may be relaxed:

- **Fixed assets**: A fixed pixel dimension can be valid for icons, hairlines, and known media crops.
- **Content-driven components**: Use container queries or JavaScript measurement when viewport width is not the real constraint.

## Quick Reference

| Rule | Summary |
|------|---------|
| Start with the containing block | Compute percentages against the parent that actually establishes layout, not against the viewport by habit. |
| Use breakpoints for structural changes | Use media queries when rows, columns, navigation, or content order changes. |
| Use clamp() for continuous scaling | Use clamp(min, preferred, max) for widths, type, gaps, and padding that should scale smoothly. |
| Prefer range syntax for readability | Write media query conditions as ranges when it makes lower and upper bounds explicit. |
| Choose viewport units by mobile behavior | Avoid 100vh for mobile full-height UI unless browser chrome behavior is acceptable. |
| Bring in JavaScript only for runtime facts | Use JavaScript when the formula depends on measured content, scroll state, or container data CSS cannot express. |
