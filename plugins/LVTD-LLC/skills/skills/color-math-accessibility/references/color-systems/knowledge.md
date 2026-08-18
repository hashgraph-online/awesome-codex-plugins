# Color Math Accessibility Knowledge

Core concepts and foundational understanding for color math accessibility.

## Overview

Use this skill when colors need to be explainable, accessible, and reproducible. It focuses on color math that affects real UI outcomes: contrast, palette relationships, perceptual lightness, opacity, and blending.

Source: Chapter 7: The mathematics of color; see `../source-map.md`.

## Key Concepts

### RGB

**Definition**: An additive device-oriented color model with red, green, and blue channels.

### HSL

**Definition**: A cylindrical representation using hue, saturation, and lightness; useful for simple hue relationships.

### LAB

**Definition**: A perceptual color space intended to better match human lightness and color differences.

### OKLCH

**Definition**: A perceptual color format using lightness, chroma, and hue; useful for modern design token work.

### Contrast ratio

**Definition**: A ratio computed from relative luminance values to estimate text/background legibility.

### Alpha compositing

**Definition**: The calculation that combines a partially transparent foreground with a background.

## Terminology

| Term | Definition |
|------|------------|
| Hue | The angular color family, often measured in degrees. |
| Saturation | Color intensity in HSL-like models. |
| Chroma | Perceptual colorfulness in LCH-like models. |
| Relative luminance | A weighted linear-light measure used in WCAG contrast math. |
| AA/AAA | WCAG conformance levels with different contrast thresholds. |

## How It Relates To

- **frontend-math-foundations**: Use for first-principles formulas and CSS-vs-JavaScript ownership decisions.
- **css-math-units**: Use when the calculation depends on CSS units, inheritance, or the box model.
- **responsive-layout-math**: Use when the calculation depends on viewport or container size.

## Common Misconceptions

- **Myth**: The browser just guesses layout math.
  **Reality**: CSS and JavaScript apply deterministic formulas; unexpected results usually come from using the wrong reference value.
- **Myth**: More breakpoints or constants make design more precise.
  **Reality**: Good formulas often reduce breakpoints and make behavior more predictable between known sizes.

## Quick Reference

| Concept | One-Line Summary |
|---------|------------------|
| RGB | An additive device-oriented color model with red, green, and blue channels. |
| HSL | A cylindrical representation using hue, saturation, and lightness; useful for simple hue relationships. |
| LAB | A perceptual color space intended to better match human lightness and color differences. |
| OKLCH | A perceptual color format using lightness, chroma, and hue; useful for modern design token work. |
| Contrast ratio | A ratio computed from relative luminance values to estimate text/background legibility. |
