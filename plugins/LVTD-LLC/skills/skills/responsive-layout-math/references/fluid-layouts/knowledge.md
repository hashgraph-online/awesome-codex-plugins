# Responsive Layout Math Knowledge

Core concepts and foundational understanding for responsive layout math.

## Overview

Use this skill to turn fixed layout intentions into proportional, bounded, and testable responsive CSS. It is strongest when the task involves deriving a formula rather than picking arbitrary breakpoint values.

Source: Chapter 6: The mathematics of responsive design; see `../source-map.md`.

## Key Concepts

### Fluid layout

**Definition**: A layout whose dimensions respond continuously to available space instead of jumping only at breakpoints.

### Breakpoint

**Definition**: A condition where layout structure changes because the available space crosses a meaningful threshold.

### Viewport unit

**Definition**: A unit based on the visible browser viewport; choose modern small, large, or dynamic viewport units when mobile browser chrome matters.

### Clamp formula

**Definition**: A three-part CSS constraint: minimum, preferred fluid value, and maximum.

### Nested percentages

**Definition**: Percentages compound against containing blocks, so local context matters more than the global viewport.

## Terminology

| Term | Definition |
|------|------------|
| vw/vh | Classic viewport width and height units. |
| sv* | Small viewport units; useful when browser UI is expanded. |
| lv* | Large viewport units; useful for the largest available viewport. |
| dv* | Dynamic viewport units; update as browser UI changes. |
| preferred value | The middle value in clamp(), often a linear expression. |

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
| Fluid layout | A layout whose dimensions respond continuously to available space instead of jumping only at breakpoints. |
| Breakpoint | A condition where layout structure changes because the available space crosses a meaningful threshold. |
| Viewport unit | A unit based on the visible browser viewport; choose modern small, large, or dynamic viewport units when mobile browser chrome matters. |
| Clamp formula | A three-part CSS constraint: minimum, preferred fluid value, and maximum. |
| Nested percentages | Percentages compound against containing blocks, so local context matters more than the global viewport. |
