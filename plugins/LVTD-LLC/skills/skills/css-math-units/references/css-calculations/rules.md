# CSS Math Units Rules

Rules for applying css math units in production front-end work.

Source: Chapter 3: Math basics for CSS; see `../source-map.md`.

## Core Rules

### 1. Trace the reference value for relative units

Know what em, rem, %, and viewport units reference before calculating.

### 2. Use rem for stable system scale

Use rem for global spacing and type values that should not compound unexpectedly.

### 3. Use em when component-local scaling is intentional

Use em for values that should follow the component font size.

### 4. Use calc() for mixed compatible units

Combine percentages with fixed offsets where the browser can resolve both sides.

### 5. Use border-box for predictable component sizing

Set or account for box-sizing before calculating widths.

### 6. Treat custom properties as substitutions

A CSS variable can carry a unit or unitless number; verify it creates a valid final expression.

## Guidelines

Less strict recommendations:

- Prefer `box-sizing: border-box` for layout components.
- Keep unitless custom properties for reusable ratios and multipliers.
- Use `min()` and `max()` when one bound is enough; use `clamp()` when both bounds matter.
- Avoid deep em compounding unless that hierarchy is intentional.

## Exceptions

When these rules may be relaxed:

- **Typography-specific local scale**: em values can be the right choice for icon sizes and inline spacing.
- **Legacy browser constraints**: Some newer CSS math functions may need fallbacks depending on support targets.

## Quick Reference

| Rule | Summary |
|------|---------|
| Trace the reference value for relative units | Know what em, rem, %, and viewport units reference before calculating. |
| Use rem for stable system scale | Use rem for global spacing and type values that should not compound unexpectedly. |
| Use em when component-local scaling is intentional | Use em for values that should follow the component font size. |
| Use calc() for mixed compatible units | Combine percentages with fixed offsets where the browser can resolve both sides. |
| Use border-box for predictable component sizing | Set or account for box-sizing before calculating widths. |
| Treat custom properties as substitutions | A CSS variable can carry a unit or unitless number; verify it creates a valid final expression. |
