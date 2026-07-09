# CSS Grid Math Knowledge

Core concepts and foundational understanding for css grid math.

## Overview

Use this skill when a grid needs to be reasoned about as a coordinate and sizing system. It helps calculate where items land, how tracks divide space, and why flexible tracks do not always produce expected widths.

Source: Chapter 4: CSS Grid math; see `../source-map.md`.

## Key Concepts

### Grid line

**Definition**: A numbered boundary between grid tracks; placement references lines, not cells.

### Span

**Definition**: A placement length measured across a number of tracks.

### Negative index

**Definition**: A grid line count from the end edge of the explicit grid.

### fr unit

**Definition**: A flex fraction of leftover space after fixed and intrinsic sizing constraints.

### Track sizing function

**Definition**: A formula or keyword that determines a row or column track size.

### auto-fit/auto-fill

**Definition**: Repeat algorithms that create as many tracks as fit, with different handling of empty tracks.

## Terminology

| Term | Definition |
|------|------------|
| explicit grid | Tracks declared by grid-template rows or columns. |
| implicit grid | Tracks created automatically when content is placed outside the explicit grid. |
| minmax() | Track sizing function with lower and upper bounds. |
| fit-content() | A track size capped by an available maximum. |
| gap | Space between tracks that reduces available distribution space. |

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
| Grid line | A numbered boundary between grid tracks; placement references lines, not cells. |
| Span | A placement length measured across a number of tracks. |
| Negative index | A grid line count from the end edge of the explicit grid. |
| fr unit | A flex fraction of leftover space after fixed and intrinsic sizing constraints. |
| Track sizing function | A formula or keyword that determines a row or column track size. |
