# CSS Math Units Patterns

Reusable patterns for css math units.

Source: Chapter 3: Math basics for CSS; see `../source-map.md`.

## Pattern: Readable max width

### Intent

Combine fluid available width with a hard maximum.

### Structure

```text
width: min(100% - 2rem, 64rem);
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.
## Pattern: Tokenized spacing

### Intent

Use unitless custom properties as multipliers.

### Structure

```text
--space-scale: 1.25; gap: calc(1rem * var(--space-scale));
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.
## Pattern: Box model equation

### Intent

Content-box rendered width includes padding and border.

### Structure

```text
rendered = width + paddingLeft + paddingRight + borderLeft + borderRight
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.


## Pattern Selection Guide

| Pattern | Use |
|---------|-----|
| Readable max width | Combine fluid available width with a hard maximum. |
| Tokenized spacing | Use unitless custom properties as multipliers. |
| Box model equation | Content-box rendered width includes padding and border. |
