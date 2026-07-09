# JavaScript UI Math Knowledge

Core concepts and foundational understanding for javascript ui math.

## Overview

Use this skill for numeric browser behavior that needs predictable edge-case handling. It helps avoid common JavaScript traps around coercion, precision, modulo behavior, rounding, randomization, and BigInt.

Source: Chapter 2: Math basics for JavaScript; see `../source-map.md`.

## Key Concepts

### Number

**Definition**: JavaScript's double-precision floating-point numeric type for ordinary arithmetic.

### BigInt

**Definition**: An integer type for values beyond safe Number integer range, with separate operation rules.

### NaN

**Definition**: A special numeric value representing an invalid number result.

### Infinity

**Definition**: A special numeric value representing values beyond finite numeric bounds.

### Remainder

**Definition**: JavaScript's % operator result, which keeps the sign of the dividend.

### Modulo wrapping

**Definition**: A normalized cyclic calculation commonly needed for carousels, sliders, and indexes.

## Terminology

| Term | Definition |
|------|------------|
| safe integer | An integer that can be represented exactly by Number. |
| nullish coalescing | The ?? operator, useful when 0 and empty string are valid values. |
| operator precedence | The order JavaScript uses to group expressions. |
| seed | A starting value that lets pseudo-random sequences repeat. |
| bankers rounding | Tie-to-even rounding used in some numeric domains. |

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
| Number | JavaScript's double-precision floating-point numeric type for ordinary arithmetic. |
| BigInt | An integer type for values beyond safe Number integer range, with separate operation rules. |
| NaN | A special numeric value representing an invalid number result. |
| Infinity | A special numeric value representing values beyond finite numeric bounds. |
| Remainder | JavaScript's % operator result, which keeps the sign of the dividend. |
