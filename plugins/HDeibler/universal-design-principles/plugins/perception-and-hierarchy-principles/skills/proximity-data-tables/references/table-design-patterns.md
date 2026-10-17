# Table design: patterns and references

A reference complementing `proximity-data-tables` with deeper design patterns and historical context.

## Tabular data design history

The visual conventions for tabular data are remarkably old and remarkably stable:

- **Accounting ledgers** (Italian double-entry bookkeeping, ~1494, codified by Pacioli) established columnar layout, right-alignment for numerics, totals at the bottom, headers at the top — the same conventions used in modern data tables.
- **Census tables** (19th century onward) added subgrouping and hierarchical headers.
- **Tufte's *Visual Display*** (1983) and *Envisioning Information* (1990) catalog the best-and-worst of statistical tables, with strong opinions about chartjunk and over-decoration.

The web's table design briefly forgot these conventions in the 2010s (CSS-styled "card grids" replaced semantic tables for tabular data) and is now relearning them. `<table>` with semantic `<th>`, `<td>`, `<tfoot>` is once again the right element for tabular data.

## Density patterns

Three established densities, each with its use:

| Density | Row height | Use case |
|---|---|---|
| Comfortable | 48–56 px | Default for general apps; mixed proficiency users |
| Compact | 32–40 px | Power users, dense datasets, spreadsheet-like |
| Hyperdense | 20–28 px | Specialized tools (trading, IDEs, monitoring); experts only |

Don't mix densities in the same table. Don't try to be "compact but readable" with mid-sized padding — you'll please neither density mode.

## Alignment conventions

Strong conventions, broken at your peril:

- **Text columns: left-align** in LTR scripts. Right-align text reads as decorative.
- **Numeric columns: right-align** so digit positions stack.
- **Date columns: left-align** if formatted as text ("May 2"), right-align if numeric/ISO ("2026-05-02").
- **Action / status columns: center or left**, depending on density.
- **Headers**: align to match the column data they label. Numeric column → right-aligned header.

## Numeric formatting

Tabular numbers benefit from `font-variant-numeric: tabular-nums` — equal-width digits so columns align by digit position. Without it, "1,000" and "9,999" don't align even though they have the same character count.

Decimal precision should be consistent within a column. Don't show "$2", "$10.00", and "$1,200.50" in the same column — pick one precision.

## Group separators

When rows are grouped (by date, status, owner, etc.):

- **Subtle row of slightly-darker background** carrying the group label (least obtrusive).
- **Group label as a tinted band** with the group key (clearer; takes more space).
- **Visible gap before the next group** (extra row padding).

Don't use heavy borders to separate groups; the page becomes a grid prison.

## Sticky headers

For tables that scroll vertically (≥ 20 rows visible):

```css
thead { position: sticky; top: 0; z-index: 1; background: white; }
thead th {
  border-bottom: 1px solid hsl(0 0% 88%);
  box-shadow: 0 1px 0 hsl(0 0% 88%);  /* slight shadow when scrolled */
}
```

The shadow appears only when content is scrolled beneath the header, providing visual feedback that the header is "floating."

## Sortable columns

Sortable columns need a clear affordance:

- Cursor pointer on header hover.
- Sort direction indicator (↑ / ↓ / ↕) visible on hover; current-sort indicator persistent on the active column.
- Click cycles ascending → descending → unsorted, or just toggles ascending/descending.

Keyboard: enter to toggle sort on the focused header.

## Selection and bulk actions

For tables with row selection:

- Checkbox column at the *left* (precedes data, doesn't disturb scanning).
- "Select all" checkbox in the header cell, with indeterminate state when partial.
- Bulk-action toolbar appears above the table when selection > 0 — contextually showing only relevant actions.

## Cross-domain examples

### Spreadsheet conventions

Excel, Google Sheets, Airtable: cell selection, fill handles, formula bars. The grid is the universal interface for tabular data; web tables that pretend to be cards reinvent something users already know how to use.

### Train and flight schedules

Mass-transit timetables maximize information per square inch. Times are right-aligned (compare departure times across destinations). Service notes (holiday-only, late-night) are footnoted with superscript markers. Header cells are color-coded by service category.

These conventions evolved over a century of riders learning to scan; software tables can borrow heavily.

### Stock-market tables

Newspaper stock tables (largely extinct) packed 6–8 columns per ticker (last, high, low, change, volume, P/E, dividend, yield) at maybe 6pt type. They worked because the layout was so consistent that frequent users developed spatial memory; new users struggled.

The pattern: dense data with consistent layout earns power-user efficiency at the cost of new-user friction. Choose deliberately.

## Edge cases

### Responsive tables

A wide table on a 375px screen is unusable. Patterns:

- **Horizontal scroll** within the table region — preserves table structure, costs scrolling.
- **Stacked rows** at mobile — each "row" becomes a card with field/value pairs. Loses cross-row scanning.
- **Priority columns** — show only the 2–3 most important columns on mobile; expand to detail view on tap.

Each pattern has trade-offs; pick based on the user's primary task.

### Tables with mixed cell types

When some cells are numbers, some are dates, some are status badges, some are images — alignment becomes fraught. Default to:

- Each cell aligned per its type (number right, text left, etc.).
- Header alignment matches its cell type.
- Status cells with badges — center the badge in the cell, or left-align if cells are wide.

## Resources

- **Tufte, E. R.** (1983, 1990, 1997). The full *Envisioning Information* / *VDQI* / *Visual Explanations* trilogy.
- **Few, S.** *Show Me the Numbers* (2004) — practical statistical-table design.
- **Material Design Tables docs** — material.io.
- **Adam Silver** — "Designing Data Tables" series on adamsilver.io.
