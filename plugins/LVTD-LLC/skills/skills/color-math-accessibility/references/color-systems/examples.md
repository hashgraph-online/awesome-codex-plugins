# Color Math Accessibility Examples

Code examples demonstrating color math accessibility principles.

Source: Chapter 7: The mathematics of color; see `../source-map.md`.

## Bad and Good Examples

### Transparent foreground assumption

```css
.button {
  color: rgb(255 255 255 / .65);
  background: #2563eb;
}
```

**Problems**:
- The nominal foreground is white, but the rendered color is white composited over blue.

```css
.button {
  color: #fff;
  background: #1d4ed8;
}
```

**Why it works**:
- Use the final rendered foreground/background pair when calculating contrast.
### Naive dark mode

```css
:root.dark {
  filter: invert(1);
}
```

**Problems**:
- Full inversion changes brand hues, image colors, and perceptual relationships indiscriminately.

```css
:root {
  --surface: oklch(98% 0.01 250);
  --text: oklch(20% 0.02 250);
}
:root.dark {
  --surface: oklch(18% 0.02 250);
  --text: oklch(94% 0.01 250);
}
```

**Why it works**:
- Semantic tokens let lightness and chroma shift intentionally.


## Refactoring Walkthrough

### Before

A value is hard-coded because it looked right in one viewport or one data state.

### After

1. Name the value being solved.
2. Identify the reference value and unit.
3. Express the relationship as a bounded formula.
4. Test the formula at minimum, middle, and maximum states.
