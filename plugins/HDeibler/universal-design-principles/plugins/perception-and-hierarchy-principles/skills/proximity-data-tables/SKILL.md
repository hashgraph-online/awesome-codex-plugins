---
name: proximity-data-tables
description: 'Use this skill when designing or fixing data tables and tabular layouts — row spacing, column spacing, header treatment, group separators, total rows, sticky headers, dense vs. comfortable variants. Trigger when the user is laying out a table, deciding density, debugging "rows that are hard to follow," picking when to add zebra striping, or arguing for/against borders. Sub-aspect of `proximity`; read that first if you haven''t already.'
---

# Proximity in data tables

Tables stress proximity in two directions at once: rows should read as discrete records (vertical proximity binding cells of the same row, separating them from cells of neighbor rows), and columns should read as semantic groupings (horizontal proximity within a column header, between header and cells). Most table problems are proximity problems disguised as styling problems.

## The two-axis proximity ladder

In a table, you're managing two perpendicular spacing systems:

```
Vertical:
  Inside a row (cell padding)        — ~12-16px
  Between rows                       — ~0 (or thin border for separation)
  Header to first row                — slightly more than between rows
  Footer / total row                 — distinctly more than between rows

Horizontal:
  Within a cell (text to edge)       — ~12-16px
  Between columns                    — ~0 (cell border or just padding)
  Numeric columns: tabular-nums + right alignment for column-internal proximity
```

The classic mistake is uniform padding everywhere — every gap the same — so the eye can't tell rows from columns from groups.

## Dense vs. comfortable variants

Tables come in two density modes; pick deliberately:

```
Comfortable (default for most apps):
  Cell padding:  py-3 px-4   (12px / 16px)
  Row height:    ~48px
  Best for:      moderate datasets, mixed user proficiency

Dense (power-user / spreadsheet-like):
  Cell padding:  py-1.5 px-3  (6px / 12px)
  Row height:    ~32px
  Best for:      high-frequency scanning, expert users, datasets >50 rows visible
```

Don't mix densities in the same table. Don't try to be "compact but readable" with mid-sized padding — it ends up neither dense enough for power users nor comfortable enough for casual ones.

## Header proximity

The header should bind to its column (vertically tight to the column it labels) but separate clearly from the data rows.

```html
<style>
  .table { width: 100%; border-collapse: collapse; }
  .table th, .table td { padding: 0.75rem 1rem; text-align: left; }
  .table th {
    font-size: 0.75rem;
    font-weight: 600;
    color: hsl(0 0% 35%);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    border-bottom: 1px solid hsl(0 0% 88%);   /* separates header from data */
    padding-bottom: 0.5rem;                    /* tighter to the underline */
  }
  .table td { border-bottom: 1px solid hsl(0 0% 95%); }   /* very subtle row separator */
  .table tbody tr:hover { background: hsl(0 0% 98%); }
</style>

<table class="table">
  <thead>
    <tr>
      <th>Customer</th>
      <th style="text-align: right;">Amount</th>
      <th style="text-align: right;">Days late</th>
      <th>Status</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Acme Co.</td>
      <td style="text-align: right; font-variant-numeric: tabular-nums;">$2,480.00</td>
      <td style="text-align: right; font-variant-numeric: tabular-nums;">14</td>
      <td><span class="badge badge-warning">Pending</span></td>
    </tr>
    <!-- … -->
  </tbody>
</table>
```

The header sits in its own row, visually distinct (smaller, uppercase, lower contrast, with a stronger underline). Data rows have a subtle hairline separator that suggests row boundaries without dominating.

## Numeric column proximity

Numbers in a column should align *within the column*, so the eye can scan vertically and compare magnitudes:

- **Right-align** numeric columns. Left-aligned numbers don't compare.
- **Tabular nums** (`font-variant-numeric: tabular-nums`) so digits occupy equal width. Without this, "1,000" and "9,999" don't align by digit position.
- **Same number of decimals** in every cell of a column. "$2.5", "$10.00", "$1,200" don't align. Pick a precision and stick to it.

```html
<td style="text-align: right; font-variant-numeric: tabular-nums;">$2,480.00</td>
<td style="text-align: right; font-variant-numeric: tabular-nums;">$10.00</td>
<td style="text-align: right; font-variant-numeric: tabular-nums;">$98,001.50</td>
```

Now the eye can scan the column and see magnitude differences instantly.

## Group separators

When rows belong to logical groups (orders by month, projects by team, transactions by status), encode the grouping with a *visible gap* and an optional sub-header — not by adding a heavy border:

```html
<table class="table">
  <thead>…</thead>
  <tbody>
    <tr class="group-header">
      <td colspan="4">May 2026</td>
    </tr>
    <tr><td>…</td>…</tr>
    <tr><td>…</td>…</tr>

    <tr class="group-header">
      <td colspan="4">April 2026</td>
    </tr>
    <tr><td>…</td>…</tr>
    <tr><td>…</td>…</tr>
  </tbody>
</table>

<style>
  .group-header td {
    font-size: 0.75rem;
    font-weight: 600;
    color: hsl(0 0% 35%);
    background: hsl(0 0% 97%);
    padding-top: 1rem;        /* extra space above this row separates groups */
    padding-bottom: 0.5rem;
  }
</style>
```

The extra top padding on group headers creates a perceptual gap; the slight background tint reinforces it. The user reads months as groups, transactions as group members.

## Total / summary rows

Total rows should bind to the data they summarize (close vertically) and stand out from regular rows (heavier weight, possibly a top border):

```html
<tfoot>
  <tr style="font-weight: 600; border-top: 2px solid hsl(0 0% 88%);">
    <td>Total</td>
    <td colspan="2" style="text-align: right; font-variant-numeric: tabular-nums;">$24,800.00</td>
    <td></td>
  </tr>
</tfoot>
```

The 2px top border separates the summary from data rows. Bold weight signals "this is summary, not a regular row." Same column alignment as the data above.

## Zebra striping (alternating row backgrounds)

Use sparingly. Zebra striping helps the eye track across very wide rows (~7+ columns) but adds visual noise to compact tables.

- **Use it**: wide tables, many columns, where the user must trace a single row across.
- **Skip it**: 3–5 column tables where row tracking isn't a problem; a hover background is enough.
- **Make it subtle**: `hsl(0 0% 98%)` against white — visible but not distracting. Anything stronger competes with the data.

## Anti-patterns

- **Heavy borders everywhere.** Every cell bordered, every row separated, every column ruled. The page becomes a grid prison; data drowns in chrome. Strip borders; let alignment and subtle separation do the work.
- **Equal padding top and bottom on rows.** With no row separator and equal padding, rows blur into a wall of text. Add either a hairline separator or a slight row-zebra.
- **Numeric and text columns aligned the same way.** Numbers left-aligned mean the eye can't compare magnitudes; text right-aligned means the eye can't follow words.
- **Inconsistent decimal precision.** One column shows "$2", "$2.5", "$2.50", "$2.501" — eye scan fails. Pick a precision per column.
- **Sticky header with no separator.** Sticky headers that float over scrolling data without a clear border merge into the data; users don't realize what's a header.

## Heuristics

1. **The single-finger trace.** Can you trace any row with one finger from left to right without losing your place? If not, row separation is too weak (or the row is too tall).
2. **The numeric-column scan.** Look down a numeric column. Can you spot the largest value at a glance? If not, alignment or tabular-nums is missing.
3. **Strip the chrome.** Mentally remove every border and background. Does the table still parse? If yes, your chrome is doing redundant work; trim it.

## Related sub-skills

- **`proximity`** (parent).
- **`proximity-form-fields`** — same principle on input layouts.
- **`hierarchy-typographic`** — header styling lives at the intersection of hierarchy and proximity.
- **`signal-to-noise-ratio`** — tables are a primary case for SNR discipline.
- **`legibility`** — tabular numerals and alignment are legibility decisions as much as proximity ones.
