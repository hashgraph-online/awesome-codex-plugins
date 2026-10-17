---
name: alignment-grid-systems
description: 'Use this skill when designing or evaluating a grid system — picking column counts, gutter widths, breakpoints, baseline grids, or modular grids. Trigger when designing a new layout system, when an existing layout feels disorderly, when picking responsive breakpoints, or when reviewing a design that "doesn''t sit on a grid." Sub-aspect of `alignment`; read that first.'
---

# Grid systems

A grid is the explicit alignment scaffold a design uses. It provides the columns, rows, and gutters that every element snaps to. Most successful design systems share one important trait: they enforce a grid that designers and engineers can both reason about.

## Grid types

### Column grid

The most common type in web design. The page is divided into N equal columns separated by gutters; elements span 1 to N columns.

```css
.layout {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 24px;          /* gutter */
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}
```

Common column counts:
- **12 columns** — the de facto web standard. Divides cleanly into 2, 3, 4, 6 columns.
- **8 columns** — common on smaller widths.
- **6 / 4 columns** — common on tablet / mobile.
- **24 columns** — used in some dense enterprise systems for finer control.

The 12-column grid is the safe default; deviate only with specific reason.

### Modular grid

Adds horizontal subdivision in addition to columns. Useful for image-heavy or magazine-style layouts where elements need to align both horizontally and vertically.

### Baseline grid

A grid of horizontal lines at the leading interval of body text. Headings, body, and other type all snap to these baselines, producing perfect vertical rhythm. Hard to enforce in CSS but possible with careful line-height and margin discipline.

### Hierarchical / asymmetric grid

A grid optimized for one specific layout — different columns for different regions of the page. Common in marketing layouts.

## Gutter widths

The space between columns. Common scales:

- **Compact**: 8–16px (dense apps, dashboards).
- **Standard**: 16–24px (most apps).
- **Generous**: 32–48px (marketing pages, magazine layouts).

The gutter should feel proportional to the column width. A 24px gutter on a 1200px-wide grid gives ~3% of horizontal space to gutters — a reasonable balance.

## Margins and bleed

The space at the page edges (outside the grid):

- **Container max-width** — typical 1140–1280px for content sites; up to 1440px for wider layouts.
- **Edge margin** — the padding inside the container at the screen edge. Typical 16–48px depending on breakpoint.

Some layouts deliberately "bleed" content to the screen edges (full-bleed images, edge-flush nav). Mix bleed and contained content carefully; the rhythm needs to remain coherent.

## Responsive grid behavior

A grid system needs to behave at every breakpoint. Common pattern:

```css
.layout {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(4, 1fr);  /* mobile: 4 columns */
}

@media (min-width: 768px) {
  .layout {
    gap: 20px;
    grid-template-columns: repeat(8, 1fr);  /* tablet: 8 columns */
  }
}

@media (min-width: 1024px) {
  .layout {
    gap: 24px;
    grid-template-columns: repeat(12, 1fr);  /* desktop: 12 columns */
  }
}
```

Components reference column spans (`grid-column: span 4`); the meaning of "span 4" changes with breakpoint, but the component code stays the same.

## Tools

- **CSS Grid** is the modern foundation; flex layouts handle simpler cases.
- **Container queries** (CSS) let components respond to their container's width, not just the viewport — useful in dashboards.
- **Storybook / design tokens** can codify the grid spec.
- **Figma / Sketch grid plugins** — most design tools have built-in grid support; use it.

## Anti-patterns

- **Inconsistent gutters.** A 16px gutter in one region, 24px in another. The eye reads it as different grids.
- **Pixel-perfect at one breakpoint, broken at others.** A grid that works at 1440px but is misaligned at 1280px because columns weren't tested.
- **Mixing column-grid and free-form layout.** Components designed to span 4 grid columns interspersed with pixel-positioned elements. The grid rhythm collapses.
- **Component widths that ignore the grid.** Cards that are 287px wide in a 12-column grid where columns are 80px. Edges don't align with anything.

## Heuristics

1. **Show the grid.** Toggle a CSS overlay showing column lines. Every element's edge should land on a column or a half-column.
2. **Test at every breakpoint.** A grid design isn't done until you've checked 320, 768, 1024, 1280, and your widest target.
3. **The snap test.** When designers move components, do they snap to the grid? If you find yourself fighting your own grid, the grid spec is wrong.

## Related sub-skills

- **`alignment`** (parent).
- **`alignment-text-and-numerics`** — alignment within typography and tabular data.
- **`hierarchy-spatial`** — spatial hierarchy operates on a grid.
- **`fibonacci-sequence`** — proportional grid stops often follow Fibonacci-like ratios.

## Resources

- **Müller-Brockmann, J.** *Grid Systems in Graphic Design* (1981) — the canonical text.
- **CSS Grid spec** (W3C) — modern layout primitive.
- **Tailwind, Bootstrap grid docs** — practical implementations.
