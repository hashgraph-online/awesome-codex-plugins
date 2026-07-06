# Frontend Math Foundations Patterns

Reusable patterns for frontend math foundations.

Source: Chapter 1: Web dev math fundamentals; see `../source-map.md`.

## Pattern: Linear interpolation

### Intent

Find a value between two endpoints.

### Structure

```text
value = start + (end - start) * t
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.
## Pattern: Aspect ratio

### Intent

Solve height from width and ratio.

### Structure

```text
height = width * ratioHeight / ratioWidth
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.
## Pattern: Distance

### Intent

Use the Pythagorean relationship for x/y distance.

### Structure

```text
distance = sqrt(dx * dx + dy * dy)
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.


## Pattern Selection Guide

| Pattern | Use |
|---------|-----|
| Linear interpolation | Find a value between two endpoints. |
| Aspect ratio | Solve height from width and ratio. |
| Distance | Use the Pythagorean relationship for x/y distance. |
