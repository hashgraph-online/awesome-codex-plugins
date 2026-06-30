# Frontend Math Foundations Examples

Code examples demonstrating frontend math foundations principles.

Source: Chapter 1: Web dev math fundamentals; see `../source-map.md`.

## Bad and Good Examples

### Aspect ratio by fixed height

```css
.media {
  width: 320px;
  height: 180px;
}
```

**Problems**:
- The ratio is implicit and may be broken when width changes.

```css
.media {
  aspect-ratio: 16 / 9;
  width: min(100%, 40rem);
}
```

**Why it works**:
- The width can change while the ratio remains explicit.
### Unclear mixed calculation

```js
const x = w - p * 2 / 3;
```

**Problems**:
- The intended grouping and units are unclear.

```js
const horizontalPadding = padding * 2;
const contentWidth = containerWidth - horizontalPadding;
const columnWidth = contentWidth / 3;
```

**Why it works**:
- Named intermediate values make the algebra inspectable.


## Refactoring Walkthrough

### Before

A value is hard-coded because it looked right in one viewport or one data state.

### After

1. Name the value being solved.
2. Identify the reference value and unit.
3. Express the relationship as a bounded formula.
4. Test the formula at minimum, middle, and maximum states.
