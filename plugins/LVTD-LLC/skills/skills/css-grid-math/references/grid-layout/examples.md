# CSS Grid Math Examples

Code examples demonstrating css grid math principles.

Source: Chapter 4: CSS Grid math; see `../source-map.md`.

## Bad and Good Examples

### Ignoring gaps in fr math

```css
.grid {
  width: 900px;
  display: grid;
  gap: 24px;
  grid-template-columns: 1fr 1fr 1fr;
}
```

**Problems**:
- Each track is not 300px because the two gaps consume 48px first.

```css
/* Track width = (900px - 48px) / 3 = 284px */
.grid {
  display: grid;
  gap: 24px;
  grid-template-columns: repeat(3, 1fr);
}
```

**Why it works**:
- Subtract fixed spacing before distributing flexible tracks.
### Fixed product grid

```css
.cards {
  grid-template-columns: repeat(4, 240px);
}
```

**Problems**:
- Fixed repetitions overflow or leave awkward empty space.

```css
.cards {
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
}
```

**Why it works**:
- The grid creates as many bounded flexible tracks as fit.


## Refactoring Walkthrough

### Before

A value is hard-coded because it looked right in one viewport or one data state.

### After

1. Name the value being solved.
2. Identify the reference value and unit.
3. Express the relationship as a bounded formula.
4. Test the formula at minimum, middle, and maximum states.
