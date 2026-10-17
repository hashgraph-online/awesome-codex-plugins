# Responsive Layout Math Patterns

Reusable patterns for responsive layout math.

Source: Chapter 6: The mathematics of responsive design; see `../source-map.md`.

## Pattern: Bounded fluid spacing

### Intent

Use clamp(min, preferred, max) for padding and gaps that should scale but not collapse.

### Structure

```text
padding-inline: clamp(1rem, 4vw, 4rem);
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.
## Pattern: Range breakpoint

### Intent

Use range media query syntax for structural changes.

### Structure

```text
@media (48rem <= width < 72rem) { .layout { grid-template-columns: 1fr 2fr; } }
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.
## Pattern: Fluid preferred value

### Intent

Interpolate between two sizes across a viewport range.

### Structure

```text
preferred = minSize + slope * (100vw - minViewport)
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.


## Pattern Selection Guide

| Pattern | Use |
|---------|-----|
| Bounded fluid spacing | Use clamp(min, preferred, max) for padding and gaps that should scale but not collapse. |
| Range breakpoint | Use range media query syntax for structural changes. |
| Fluid preferred value | Interpolate between two sizes across a viewport range. |
