# Color Math Accessibility Patterns

Reusable patterns for color math accessibility.

Source: Chapter 7: The mathematics of color; see `../source-map.md`.

## Pattern: Contrast ratio

### Intent

Compute (L1 + 0.05) / (L2 + 0.05), where L1 is lighter.

### Structure

```text
ratio = (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.
## Pattern: Hue harmony

### Intent

Derive related hues by adding degree offsets.

### Structure

```text
complement = (hue + 180) % 360
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.
## Pattern: Alpha compositing

### Intent

Composite transparent foreground before judging contrast.

### Structure

```text
out = fg * alpha + bg * (1 - alpha)
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.


## Pattern Selection Guide

| Pattern | Use |
|---------|-----|
| Contrast ratio | Compute (L1 + 0.05) / (L2 + 0.05), where L1 is lighter. |
| Hue harmony | Derive related hues by adding degree offsets. |
| Alpha compositing | Composite transparent foreground before judging contrast. |
