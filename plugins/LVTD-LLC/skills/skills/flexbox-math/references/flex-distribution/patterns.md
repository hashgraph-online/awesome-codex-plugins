# Flexbox Math Patterns

Reusable patterns for flexbox math.

Source: Chapter 5: Flexbox math; see `../source-map.md`.

## Pattern: Grow allocation

### Intent

Allocate positive free space by grow ratio.

### Structure

```text
itemGrowth = freeSpace * itemGrow / totalGrow
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.
## Pattern: Shrink allocation

### Intent

Allocate negative space by scaled shrink factor.

### Structure

```text
scaled = flexShrink * flexBaseSize
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.
## Pattern: Equal flex children

### Intent

Ignore intrinsic basis for equal columns.

### Structure

```text
flex: 1 1 0; min-width: 0;
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.


## Pattern Selection Guide

| Pattern | Use |
|---------|-----|
| Grow allocation | Allocate positive free space by grow ratio. |
| Shrink allocation | Allocate negative space by scaled shrink factor. |
| Equal flex children | Ignore intrinsic basis for equal columns. |
