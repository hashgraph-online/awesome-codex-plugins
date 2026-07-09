# CSS Math Units Examples

Code examples demonstrating css math units principles.

Source: Chapter 3: Math basics for CSS; see `../source-map.md`.

## Bad and Good Examples

### Compounding em sizes

```css
.card { font-size: 1.25em; }
.card h2 { font-size: 1.5em; }
```

**Problems**:
- The h2 size compounds from the card font size, which may be larger than intended.

```css
.card { font-size: 1rem; }
.card h2 { font-size: 1.5rem; }
```

**Why it works**:
- Use rem when the heading should follow the root scale rather than compound locally.
### Content-box width surprise

```css
.panel {
  width: 20rem;
  padding: 2rem;
  border: 1px solid;
}
```

**Problems**:
- The rendered box is wider than 20rem under the default content-box model.

```css
.panel {
  box-sizing: border-box;
  width: 20rem;
  padding: 2rem;
  border: 1px solid;
}
```

**Why it works**:
- The declared width includes content, padding, and border.


## Refactoring Walkthrough

### Before

A value is hard-coded because it looked right in one viewport or one data state.

### After

1. Name the value being solved.
2. Identify the reference value and unit.
3. Express the relationship as a bounded formula.
4. Test the formula at minimum, middle, and maximum states.
