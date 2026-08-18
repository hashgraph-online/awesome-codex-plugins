# Color Math Accessibility Checklist

Use when applying or reviewing color math accessibility.

Source: Chapter 7: The mathematics of color; see `../source-map.md`.

## Before You Start

- [ ] Identify the UI behavior or layout value being calculated.
- [ ] List all known inputs and units.
- [ ] Decide whether the browser can solve the relationship declaratively.

## Review Checks

- [ ] List semantic color roles before picking values.
- [ ] Calculate contrast for text, icons, borders, and disabled states.
- [ ] Validate hover, focus, selected, and error states.
- [ ] Check light and dark mode independently.
- [ ] Composite opacity and blend modes over real backgrounds.

## Red Flags

Stop and address if you find:

- Palette looks balanced but text fails contrast: Run luminance and contrast calculations, not hue harmony checks.
- Dark mode feels muddy: Adjust perceptual lightness and chroma rather than inverting RGB.
- Overlay text changes by page section: Composite foreground colors against each actual background.

## Quick Reference

| Aspect | Ideal | Acceptable | Red Flag |
|--------|-------|------------|----------|
| Units | Named and consistent | Converted locally | Mixed without conversion |
| Bounds | Min and max tested | One bound tested | No boundary checks |
| Ownership | CSS or JS clearly owns math | Boundary documented | Same formula duplicated |
