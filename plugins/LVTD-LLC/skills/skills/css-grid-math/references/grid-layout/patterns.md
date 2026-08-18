# CSS Grid Math Patterns

Reusable patterns for css grid math.

Source: Chapter 4: CSS Grid math; see `../source-map.md`.

## Pattern: Fr distribution

### Intent

Subtract fixed tracks and gaps, then divide leftover space by total fr units.

### Structure

```text
track = remaining * trackFr / totalFr
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.
## Pattern: Full-width item

### Intent

Use grid-column: 1 / -1 to span all explicit columns.

### Structure

```text
grid-column: 1 / -1;
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.
## Pattern: Responsive card grid

### Intent

Use repeat(auto-fit, minmax(minTrack, 1fr)).

### Structure

```text
grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
```

### When to Use

- Use when the relationship should be derived instead of guessed.
- Use when the same calculation appears in multiple UI states.


## Pattern Selection Guide

| Pattern | Use |
|---------|-----|
| Fr distribution | Subtract fixed tracks and gaps, then divide leftover space by total fr units. |
| Full-width item | Use grid-column: 1 / -1 to span all explicit columns. |
| Responsive card grid | Use repeat(auto-fit, minmax(minTrack, 1fr)). |
