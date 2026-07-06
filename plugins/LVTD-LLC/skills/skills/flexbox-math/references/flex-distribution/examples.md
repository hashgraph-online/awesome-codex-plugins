# Flexbox Math Examples

Code examples demonstrating flexbox math principles.

Source: Chapter 5: Flexbox math; see `../source-map.md`.

## Bad and Good Examples

### Unexpected unequal columns

```css
.item {
  flex: 1 1 auto;
}
```

**Problems**:
- The auto basis lets intrinsic content affect the starting size, so equal grow values may not create equal columns.

```css
.item {
  flex: 1 1 0;
  min-width: 0;
}
```

**Why it works**:
- A zero basis and shrink-safe minimum create equal distribution.
### Text refuses to shrink

```css
.toolbar-title {
  flex: 1;
}
```

**Problems**:
- The child may still honor its min-content width and overflow.

```css
.toolbar-title {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}
```

**Why it works**:
- Allow shrinkage explicitly and define overflow behavior.


## Refactoring Walkthrough

### Before

A value is hard-coded because it looked right in one viewport or one data state.

### After

1. Name the value being solved.
2. Identify the reference value and unit.
3. Express the relationship as a bounded formula.
4. Test the formula at minimum, middle, and maximum states.
