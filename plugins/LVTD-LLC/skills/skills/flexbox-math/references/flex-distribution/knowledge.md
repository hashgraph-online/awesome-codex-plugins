# Flexbox Math Knowledge

Core concepts and foundational understanding for flexbox math.

## Overview

Use this skill for one-dimensional layout distribution. It focuses on the arithmetic that determines base sizes, free space, grow allocation, shrink allocation, and constraint clamping.

Source: Chapter 5: Flexbox math; see `../source-map.md`.

## Key Concepts

### Flex base size

**Definition**: The starting size for each item before free space is distributed.

### Positive free space

**Definition**: Extra main-axis space distributed by flex-grow.

### Negative free space

**Definition**: Overflow that must be removed by flex-shrink.

### Flex grow factor

**Definition**: A weight controlling how positive free space is allocated.

### Flex shrink factor

**Definition**: A weight controlling how negative free space is removed, scaled by base size.

### Flex shorthand

**Definition**: The combined grow, shrink, and basis declaration.

## Terminology

| Term | Definition |
|------|------------|
| main axis | The axis controlled by flex-direction. |
| cross axis | The perpendicular axis. |
| flex-basis | The preferred main-axis size before grow/shrink. |
| min-width/min-height | Lower constraints that can block shrinkage. |
| max-width/max-height | Upper constraints that can cap growth. |

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
| Flex base size | The starting size for each item before free space is distributed. |
| Positive free space | Extra main-axis space distributed by flex-grow. |
| Negative free space | Overflow that must be removed by flex-shrink. |
| Flex grow factor | A weight controlling how positive free space is allocated. |
| Flex shrink factor | A weight controlling how negative free space is removed, scaled by base size. |
