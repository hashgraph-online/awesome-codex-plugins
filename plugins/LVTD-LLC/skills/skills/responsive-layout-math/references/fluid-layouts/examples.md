# Responsive Layout Math Examples

Code examples demonstrating responsive layout math principles.

Source: Chapter 6: The mathematics of responsive design; see `../source-map.md`.

## Bad and Good Examples

### Fixed hero image

```css
.hero img {
  width: 1600px;
  height: 900px;
}
```

**Problems**:
- The image overflows small screens and does not preserve a responsive relationship to its container.

```css
.hero img {
  display: block;
  width: 100%;
  height: auto;
}
```

**Why it works**:
- The image scales with the containing block and preserves its intrinsic aspect ratio.
### Fluid container

```css
.page {
  width: 960px;
}
```

**Problems**:
- The container is fixed even when the viewport is narrower or much wider.

```css
.page {
  width: min(100% - 2rem, 70rem);
  margin-inline: auto;
}
```

**Why it works**:
- The container has a fluid available width and a readable maximum line length.


## Refactoring Walkthrough

### Before

A value is hard-coded because it looked right in one viewport or one data state.

### After

1. Name the value being solved.
2. Identify the reference value and unit.
3. Express the relationship as a bounded formula.
4. Test the formula at minimum, middle, and maximum states.
