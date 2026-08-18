# CSS Math Units Knowledge

Core concepts and foundational understanding for css math units.

## Overview

Use this skill to trace how CSS values become computed layout values. It is useful for unit conversion, inherited size multiplication, calc expressions, custom property math, and box model sizing.

Source: Chapter 3: Math basics for CSS; see `../source-map.md`.

## Key Concepts

### Absolute unit

**Definition**: A unit such as px that is resolved without depending on the parent element.

### Relative unit

**Definition**: A unit such as em, rem, %, or viewport units that depends on another value.

### Computed value

**Definition**: The value after CSS has resolved inheritance, variables, and many relative units.

### Used value

**Definition**: The value after layout constraints have been applied.

### Box sizing

**Definition**: The rule that determines whether width/height include content only or include padding and border.

### CSS math function

**Definition**: A function such as calc(), min(), max(), or clamp() that combines or constrains values.

## Terminology

| Term | Definition |
|------|------------|
| em | Relative to the current element font size, or parent context depending on property. |
| rem | Relative to the root element font size. |
| calc() | CSS expression evaluator for compatible units. |
| clamp() | min/preferred/max constraint function. |
| border-box | Box model where declared width includes content, padding, and border. |

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
| Absolute unit | A unit such as px that is resolved without depending on the parent element. |
| Relative unit | A unit such as em, rem, %, or viewport units that depends on another value. |
| Computed value | The value after CSS has resolved inheritance, variables, and many relative units. |
| Used value | The value after layout constraints have been applied. |
| Box sizing | The rule that determines whether width/height include content only or include padding and border. |
