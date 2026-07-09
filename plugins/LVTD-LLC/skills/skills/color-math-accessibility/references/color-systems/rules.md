# Color Math Accessibility Rules

Rules for applying color math accessibility in production front-end work.

Source: Chapter 7: The mathematics of color; see `../source-map.md`.

## Core Rules

### 1. Check contrast from final rendered colors

Opacity, blending, and backgrounds can change the actual contrast users see.

### 2. Use perceptual spaces for palette scaling

Prefer OKLCH/LAB thinking when generating light/dark ramps or consistent steps.

### 3. Do not rely on naive inversion for dark mode

Invert perceived lightness and adjust chroma/hue deliberately.

### 4. Choose harmony by hue relationship, then validate contrast

Complementary or triadic math does not guarantee accessible UI.

### 5. Keep color roles semantic

Tokens should describe intent such as text, surface, border, danger, and accent.

### 6. Calculate alpha over the actual background

Transparent text or overlays must be composited before contrast review.

## Guidelines

Less strict recommendations:

- Use HSL for quick hue rotations and simple teaching examples.
- Use OKLCH for production palette ramps when browser support and tooling allow it.
- Treat contrast thresholds as a floor, not a full readability guarantee.
- Check non-text UI affordances as well as body text.

## Exceptions

When these rules may be relaxed:

- **Logos and decorative marks**: Brand marks may not follow text contrast rules, but adjacent text still must.
- **Large display text**: Large text has lower WCAG contrast thresholds than normal text.

## Quick Reference

| Rule | Summary |
|------|---------|
| Check contrast from final rendered colors | Opacity, blending, and backgrounds can change the actual contrast users see. |
| Use perceptual spaces for palette scaling | Prefer OKLCH/LAB thinking when generating light/dark ramps or consistent steps. |
| Do not rely on naive inversion for dark mode | Invert perceived lightness and adjust chroma/hue deliberately. |
| Choose harmony by hue relationship, then validate contrast | Complementary or triadic math does not guarantee accessible UI. |
| Keep color roles semantic | Tokens should describe intent such as text, surface, border, danger, and accent. |
| Calculate alpha over the actual background | Transparent text or overlays must be composited before contrast review. |
