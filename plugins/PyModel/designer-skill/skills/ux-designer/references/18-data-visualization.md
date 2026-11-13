# Data Visualization & Dashboard UX

Data visualization and dashboard design are specialized UX disciplines critical for enterprise products and analytics interfaces. This reference covers chart selection, dashboard layout, data tables, and accessibility for data-heavy interfaces.

---

## Chart Selection

### When to Use Each Chart Type

| Data Relationship | Recommended Chart | Avoid |
|-------------------|------------------|-------|
| **Part of whole** | Pie (≤5 slices), donut, stacked bar, treemap | Pie with >5 slices |
| **Comparison** | Bar (vertical/horizontal), grouped bar | 3D bars, radar (hard to read) |
| **Trend over time** | Line, area, sparkline | Pie (no time axis) |
| **Distribution** | Histogram, box plot, violin plot | Pie or bar |
| **Correlation** | Scatter plot, bubble chart | Line (implies time) |
| **Ranking** | Horizontal bar (sorted), lollipop chart | Vertical bar (hard to label) |
| **Geographic** | Choropleth map, dot map | Bar chart for location data |
| **Hierarchy** | Treemap, sunburst | Nested pie charts |
| **Flow/process** | Sankey diagram, funnel | Bar chart |
| **Single value** | KPI card, gauge, big number | Chart with one data point |

### Chart Decision Tree

```
What are you showing?
├── Single number → KPI card / big number display
├── Change over time?
│   ├── Few series (1-3) → Line chart
│   ├── Many series → Small multiples or highlight key lines
│   └── Cumulative → Stacked area chart
├── Comparing categories?
│   ├── Few categories (≤6) → Vertical bar chart
│   ├── Many categories → Horizontal bar chart (easier labels)
│   └── Two variables → Grouped or stacked bar
├── Part of a whole?
│   ├── Few parts (≤5) → Pie or donut chart
│   ├── Many parts → Treemap or stacked bar
│   └── Hierarchical → Sunburst or treemap
├── Relationship between variables?
│   ├── Two variables → Scatter plot
│   └── Three variables → Bubble chart (size = 3rd variable)
└── Distribution?
    ├── Single variable → Histogram
    └── Multiple groups → Box plot or violin plot
```

---

## Dashboard Layout

### Information Hierarchy

```
┌─────────────────────────────────────────────────────┐
│  KPI Cards (most important metrics at a glance)     │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐            │
│  │ $42K │  │ 1.2K │  │ 89%  │  │ 4.2s │            │
│  │ Rev  │  │Users │  │ Sat  │  │ Load │            │
│  │ ↑12% │  │ ↑8%  │  │ ↓2%  │  │ ↑0.3 │            │
│  └──────┘  └──────┘  └──────┘  └──────┘            │
├─────────────────────────────────────────────────────┤
│  Primary chart (main trend or most viewed data)     │
│  ┌─────────────────────────────────────────────┐    │
│  │  📈 Revenue Over Time                       │    │
│  │  ▁▂▃▅▆▇█▇▆▅▆▇██▇▅▆▇█                      │    │
│  └─────────────────────────────────────────────┘    │
├─────────────────────┬───────────────────────────────┤
│  Secondary chart 1  │  Secondary chart 2            │
│  ┌───────────────┐  │  ┌───────────────────────┐    │
│  │ 🥧 By Source  │  │  │ 📊 By Region          │    │
│  └───────────────┘  │  └───────────────────────┘    │
├─────────────────────┴───────────────────────────────┤
│  Data table (details on demand)                     │
│  ┌─────────────────────────────────────────────┐    │
│  │  Name  │ Revenue │ Users │ Conversion       │    │
│  │  ...   │  ...    │  ...  │  ...             │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### Layout Principles

- **Top**: KPI summary cards (3-6 metrics)
- **Middle**: Primary visualizations (1-2 charts)
- **Bottom**: Secondary charts and detail tables
- **Shneiderman's mantra**: Overview first, zoom and filter, details on demand
- Use consistent grid (12-column for flexibility)
- Group related metrics visually

### KPI Card Design

```
┌────────────────────────┐
│  Revenue          ⓘ    │   ← Label + info tooltip
│  $42,350               │   ← Big number (primary)
│  ↑ 12.3% vs last month │   ← Trend with comparison
│  ▁▂▃▅▆▇█▇▆▅           │   ← Sparkline (optional)
└────────────────────────┘

Colors:
  ↑ Green = positive trend (contextual — could be red for cost metrics)
  ↓ Red = negative trend
  → Gray = no change
```

- Display the most important number prominently
- Include comparison period and trend direction
- Add sparkline for quick trend visualization
- Info icon for metric definition/calculation
- Contextual coloring (up isn't always good — e.g., error rate)

### Customizable Dashboards

- Drag-and-drop widget rearrangement
- Resizable panels with snap-to-grid
- Add/remove widgets from a library
- Save multiple dashboard layouts
- Share dashboards with team members
- Reset to default layout option

---

## Color in Data Visualization

### Palette Types

```
Sequential (low → high):
  □ → ■  Light blue → Dark blue
  Use for: continuous data, heatmaps, density

Diverging (negative ← neutral → positive):
  ■ ← □ → ■  Red ← White → Blue
  Use for: data with a meaningful midpoint (profit/loss, deviation)

Categorical (distinct groups):
  ■ ■ ■ ■ ■  Blue, Orange, Green, Red, Purple
  Use for: comparing distinct categories, legend items
  Maximum: 6-8 distinct colors before confusion
```

### Colorblind-Safe Palettes

```
❌ Red vs. Green (indistinguishable for ~8% of males)
✅ Blue vs. Orange (safe for most colorblind types)

Recommended categorical palette (colorblind-safe):
  #4477AA  #EE6677  #228833  #CCBB44  #66CCEE  #AA3377
  Blue     Rose     Green    Gold     Cyan     Purple
```

**Rules:**
- Never use color as the only differentiator
- Add patterns, shapes, or labels as secondary encoding
- Test with colorblind simulation tools
- Provide alternative text descriptions for all charts
- Data marks need 3:1 contrast against the chart background (WCAG 1.4.11). Categorical colors rarely reach 3:1 against each other (this palette does not), which is why a second encoding — direct labels, patterns, shapes or a 1px separator in the background color — is required, not optional

---

## Interaction Patterns

### Hover Tooltips

```
     ┌──────────────────────┐
     │ January 2025         │
     │ Revenue: $42,350     │
     │ Users: 1,234         │
     │ ↑ 12% vs Dec 2024   │
     └──────────┬───────────┘
                │
    ▁▂▃▅▆▇█▇▆▅▆▇██
            ▲ cursor position
```

- Show on hover (desktop) or tap (mobile)
- Include exact values, context, and comparison
- Position near cursor without obscuring the data point
- Follow cursor smoothly (no jittering)
- Dismiss on mouse-out or tap elsewhere

### Drill-Down

```
Overview: Revenue by Region
┌─────────────────────────┐
│  📊 Americas | EMEA     │  ← Click "Americas"
└─────────────────────────┘
            ↓
Detail: Revenue by Country (Americas)
┌─────────────────────────┐
│  📊 US | CA | BR | MX   │  ← Click "US"
└─────────────────────────┘
            ↓
Granular: Revenue by State (US)
┌─────────────────────────┐
│  📊 CA | TX | NY | FL   │
└─────────────────────────┘

Breadcrumb: All Regions > Americas > US
[← Back to Americas]
```

- Clear visual affordance that elements are clickable
- Breadcrumb navigation showing drill-down path
- "Back" button to return to previous level
- Maintain filters and time range across drill-downs

### Filtering & Time Range

```
┌─────────────────────────────────────────────────────┐
│  Time: [Last 30 days ▾]  Region: [All ▾]  [⟳]     │
│        [Custom range...]  Segment: [All ▾]          │
├─────────────────────────────────────────────────────┤
│  Active filters: [Americas ✕] [Enterprise ✕] [Clear]│
└─────────────────────────────────────────────────────┘
```

- Persistent filter bar visible at all times
- Show active filters as removable chips
- Preset time ranges (Today, 7d, 30d, 90d, YTD, Custom)
- Filters apply to all dashboard widgets simultaneously
- "Reset filters" to return to default view
- Date range picker with calendar and quick presets

### Zoom & Pan (Time-Series)

- Click-drag to select a time range (brush selection)
- Mouse wheel to zoom in/out on time axis
- Reset zoom button always visible when zoomed
- Mini-timeline showing selected range in context

---

## Responsive Charts

### Mobile Considerations

```
Desktop: Full chart with legend, axis labels, gridlines
Tablet:  Simplified chart, condensed legend
Mobile:  Sparkline or KPI card, tap for full chart

Breakpoints:
  > 1024px:  Full dashboard grid
  768-1024:  2-column grid, condensed charts
  < 768px:   Single column, KPI cards + expandable charts
```

- Prioritize KPI cards on mobile (most information-dense)
- Collapse charts to sparklines with "Expand" option
- Horizontal scrolling for wide data tables (with shadow indicators)
- Stack dashboard columns vertically on narrow screens
- Touch-friendly tooltips (tap instead of hover)

### Small Multiples

```
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│US ▁▅█│ │UK ▁▃▅│ │DE ▁▂▃│ │JP ▅▃▁│
└──────┘ └──────┘ └──────┘ └──────┘
```

- Same scale across all multiples for fair comparison
- Consistent axes (shared y-axis range)
- Label each clearly (top-left corner)
- Effective for comparing trends across many categories

---

## Data Tables

### Core Features

```
┌──┬──────────┬──────────┬─────────┬────────┬──────┐
│☐ │ Name ↕   │ Revenue ↓│ Users ↕ │ Conv.  │ ···  │
├──┼──────────┼──────────┼─────────┼────────┼──────┤
│☐ │ Acme Inc │ $42,350  │ 1,234   │ 3.4%   │ ···  │
│☑ │ Beta Co  │ $38,200  │ 987     │ 4.1%   │ ···  │
│☐ │ Gamma    │ $35,100  │ 856     │ 2.8%   │ ···  │
├──┴──────────┴──────────┴─────────┴────────┴──────┤
│ ☑ 1 selected  [Export] [Delete]                   │
├──────────────────────────────────────────────────┤
│ Showing 1-25 of 342  [← 1 2 3 ... 14 →]         │
└──────────────────────────────────────────────────┘
```

### Table Interaction Patterns

| Feature | Implementation |
|---------|---------------|
| **Sorting** | Click column header, toggle asc/desc, show arrow indicator |
| **Filtering** | Per-column filter dropdowns or global search |
| **Pagination** | 10/25/50/100 rows per page, page numbers, prev/next |
| **Infinite scroll** | For exploration (prefer pagination for data analysis) |
| **Row selection** | Checkbox column, shift-click for range, bulk actions bar |
| **Column resizing** | Drag column borders, double-click to auto-fit |
| **Column reordering** | Drag column headers |
| **Pinned columns** | Pin first 1-2 columns on horizontal scroll |
| **Inline editing** | Click to edit cell, Enter to save, Esc to cancel |
| **Row expansion** | Expand row for nested detail without leaving the table |
| **Export** | CSV, Excel, PDF — selected rows or all |

### Pagination vs. Infinite Scroll

| Use Pagination | Use Infinite Scroll |
|----------------|-------------------|
| Data analysis tasks | Content browsing |
| Need to return to specific position | Feed/timeline content |
| Large datasets (1000+ rows) | Progressive loading |
| Printable/exportable views | Mobile-first interfaces |

---

## Empty & Error States

### Data States

```
Loading:
┌─────────────────────────────┐
│  ░░░░░░░░░░░░░░░░░░░░░░░░ │   ← Skeleton chart
│  ░░░░░░░░░░░░░░░░░░░░░░░░ │
│  ░░░░░░░░░░░░░░░░░░░░░░░░ │
└─────────────────────────────┘

No data:
┌─────────────────────────────┐
│      📊                     │
│  No data for this period    │
│  Try a different date range │
│  or adjust your filters.   │
│  [Reset filters]            │
└─────────────────────────────┘

Error:
┌─────────────────────────────┐
│      ⚠️                     │
│  Unable to load chart data  │
│  [Retry]  [Report issue]    │
└─────────────────────────────┘

Partial data:
┌─────────────────────────────┐
│  📈 Revenue (partial data)  │
│  ▁▂▃▅▆▇█▇▆ ░░░             │
│  ℹ️ Data available through  │
│  Jan 15. Processing...      │
└─────────────────────────────┘
```

### Stale Data Indicators

- Show "Last updated: X minutes ago" for live dashboards
- Auto-refresh indicator with countdown
- Manual refresh button
- Visual indicator (dimmed chart, banner) for stale data
- Alert when data is significantly outdated

---

## Accessibility

### Chart Accessibility

- **Alt text**: Descriptive summary of what the chart shows
- **Data table alternative**: Provide raw data table for every chart
- **Keyboard navigation**: Tab through data points, arrow keys within chart
- **Screen reader**: Announce data points, trends, and outliers
- **High contrast**: Ensure chart elements meet 3:1 contrast minimum
- **Pattern fills**: Use patterns in addition to colors for categories

```html
<!-- role="img" goes on the chart itself; on the <figure> it would hide the data-table link from assistive technology -->
<figure>
  <canvas id="revenue-chart" role="img" aria-label="Revenue trend showing 12% growth from January to December 2025, with a peak of $52K in November"></canvas>
  <figcaption>
    Monthly revenue, Jan-Dec 2025.
    <a href="#revenue-data-table">View as data table</a>
  </figcaption>
</figure>
```

### Data Table Accessibility

- Use semantic `<table>`, `<thead>`, `<tbody>`, `<th scope>` markup
- `aria-sort` on sortable column headers
- `aria-selected` on selected rows
- `aria-describedby` for column filter descriptions
- Announce row count and current position to screen readers
- Keyboard navigation: Tab between cells, Enter to activate

---

## Key Metrics

| Metric | Target | Context |
|--------|--------|---------|
| Dashboard load time | < 3s | Including data fetch |
| Chart render time | < 500ms | After data available |
| Tooltip response | < 100ms | On hover/tap |
| Data refresh interval | 15-60s | Live dashboards |
| Color contrast (data) | ≥ 3:1 | Adjacent data colors |
| Max chart categories | 6-8 | Before readability drops |
| Max KPI cards | 3-6 | Above fold visibility |

---

## Anti-Patterns

1. **3D charts** — Add visual noise without informational value
2. **Pie charts with 10+ slices** — Impossible to compare small slices
3. **Dual y-axes** — Misleading correlation; use small multiples instead
4. **Truncated y-axis** — Starting y-axis above zero exaggerates differences
5. **Rainbow color schemes** — Colorblind-unfriendly and visually noisy
6. **Chart junk** — Decorative gridlines, borders, and backgrounds
7. **No loading states** — Blank areas while data fetches
8. **Auto-refresh without warning** — Dashboard changes while user is analyzing
9. **Tooltip that obscures data** — Covering the very thing user is trying to read
10. **Color-only encoding** — No patterns, labels, or shapes as redundant encoding

---

## Sources

- [Edward Tufte: The Visual Display of Quantitative Information](https://www.edwardtufte.com/) — Data visualization theory
- [Material Design: Data Visualization](https://m3.material.io/styles/color/dynamic/choosing-a-scheme) — Google guidelines
- [D3.js Gallery](https://d3-graph-gallery.com/) — Implementation patterns
- [Chartability](https://chartability.fizz.studio/) — Chart accessibility audit toolkit
- [ColorBrewer](https://colorbrewer2.org/) — Colorblind-safe palettes
- [Stephen Few: Information Dashboard Design](https://www.perceptualedge.com/) — Dashboard principles
- [WAI: Images Tutorial](https://www.w3.org/WAI/tutorials/images/complex/) — Complex image accessibility
