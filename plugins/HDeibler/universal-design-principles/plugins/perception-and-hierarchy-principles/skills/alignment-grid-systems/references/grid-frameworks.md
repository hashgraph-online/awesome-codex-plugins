# Grid frameworks: practical reference

A reference complementing `alignment-grid-systems` with practical web-grid framework details.

## CSS Grid (the modern foundation)

CSS Grid is the layout primitive most modern web design uses. Key properties:

- `grid-template-columns: repeat(12, 1fr)` — 12 equal columns.
- `gap: 24px` — consistent gutter.
- `grid-column: span 4` — element spans 4 columns.
- `grid-template-areas` — named regions for complex layouts.

CSS Grid handles responsive grid behavior cleanly via media queries that change `grid-template-columns`.

## Container queries

Newer than media queries. Lets a component respond to its container's width rather than the viewport's:

```css
@container (min-width: 600px) {
  .card { grid-template-columns: 1fr 2fr; }
}
```

Useful for components used in multiple contexts (sidebar vs. full-width main).

## Tailwind CSS

Tailwind ships utility classes that make grid composition explicit:

```html
<div class="grid grid-cols-12 gap-6">
  <div class="col-span-8">Main</div>
  <div class="col-span-4">Sidebar</div>
</div>
```

Default 12-column grid; configurable.

## Bootstrap

Older but still widely used. 12-column grid via class names:

```html
<div class="row">
  <div class="col-md-8">Main</div>
  <div class="col-md-4">Sidebar</div>
</div>
```

## Material Design grid

Material 3 specifies a responsive 4 / 8 / 12 column grid:
- **Compact** (< 600px): 4 columns.
- **Medium** (600–1239px): 8 columns.
- **Expanded** (≥ 1240px): 12 columns.

Gutter and margin scales documented per breakpoint.

## Apple HIG layout

Apple doesn't formalize a column-grid in the same way; HIG documents safe-area insets, dynamic sizing, and layout margins per device. The result feels less rigid than Material but achieves alignment through component-level spacing tokens.

## Building your own grid spec

A minimal grid spec includes:

- Column count per breakpoint.
- Gutter widths per breakpoint.
- Margin / padding at the page edges per breakpoint.
- Container max-width.
- Spacing scale (e.g., 4, 8, 12, 16, 24, 32, 48, 64).

Document these in your design system; reference them everywhere.

## Resources

- **CSS Grid spec** — w3.org/TR/css-grid-2.
- **Tailwind grid docs** — tailwindcss.com.
- **Material Design layout** — m3.material.io.
- **Refactoring UI** — chapters on grid and layout systems.
