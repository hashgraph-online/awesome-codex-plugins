# JavaScript UI Math Patterns

Reusable patterns for javascript ui math.

Source: Chapter 2: Math basics for JavaScript; see `../source-map.md`.

## Pattern: Float equality

### Intent

Use an epsilon tolerance for decimal comparisons.

### Structure

```text
Math.abs(a - b) < Number.EPSILON * scale
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.
## Pattern: Random integer

### Intent

Generate an integer in [min, max].

### Structure

```text
Math.floor(Math.random() * (max - min + 1)) + min
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.
## Pattern: Display rounding

### Intent

Round for presentation without mutating internal state.

### Structure

```text
new Intl.NumberFormat(locale, options).format(value)
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.


## Pattern Selection Guide

| Pattern | Use |
|---------|-----|
| Float equality | Use an epsilon tolerance for decimal comparisons. |
| Random integer | Generate an integer in [min, max]. |
| Display rounding | Round for presentation without mutating internal state. |
