# Data Tables & Lists

Data tables are one of the most common UI patterns in enterprise and admin applications. Well-designed tables help users scan, compare, sort, filter, and act on structured data efficiently.

---

## Table Layout Patterns

### Basic Table Structure

```html
<table class="data-table" role="grid" aria-label="User accounts">
  <thead>
    <tr>
      <th scope="col" aria-sort="ascending">
        <button class="sort-button">
          Name <span class="sort-icon">↑</span>
        </button>
      </th>
      <th scope="col">Email</th>
      <th scope="col">Role</th>
      <th scope="col">Actions</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Alice Smith</td>
      <td>alice@example.com</td>
      <td><span class="badge badge--admin">Admin</span></td>
      <td>
        <button class="btn-icon" aria-label="Edit Alice Smith">✏️</button>
        <button class="btn-icon" aria-label="Delete Alice Smith">🗑️</button>
      </td>
    </tr>
  </tbody>
</table>
```

### Fixed Headers

Keep headers visible while scrolling long tables.

```css
.data-table-container {
  max-height: 600px;
  overflow-y: auto;
}

.data-table thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: white;
  box-shadow: 0 1px 0 #e5e7eb;
}
```

### Fixed Columns

Keep identifier columns visible during horizontal scroll.

```css
.data-table td:first-child,
.data-table th:first-child {
  position: sticky;
  left: 0;
  z-index: 2;
  background: white;
  box-shadow: 1px 0 0 #e5e7eb;
}

/* Corner cell needs highest z-index */
.data-table thead th:first-child {
  z-index: 3;
}
```

### Column Resizing

```javascript
function initColumnResize(table) {
  const headers = table.querySelectorAll('th');

  headers.forEach(header => {
    const resizer = document.createElement('div');
    resizer.className = 'column-resizer';
    header.appendChild(resizer);

    let startX, startWidth;

    resizer.addEventListener('mousedown', (e) => {
      startX = e.clientX;
      startWidth = header.offsetWidth;
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    });

    function handleMouseMove(e) {
      const newWidth = Math.max(60, startWidth + (e.clientX - startX));
      header.style.width = `${newWidth}px`;
    }

    function handleMouseUp() {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    }
  });
}
```

```css
.column-resizer {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  cursor: col-resize;
  background: transparent;
}

.column-resizer:hover,
.column-resizer:active {
  background: #3b82f6;
}
```

### Responsive Table Strategies

| Strategy | When to Use |
|----------|-------------|
| Horizontal scroll | Many columns, data must stay tabular |
| Column hiding | Secondary columns can be hidden on mobile |
| Card layout | Reflow rows into stacked cards below breakpoint |
| Priority columns | Show only high-priority columns, expand for more |

#### Card Reflow Pattern

```css
@media (max-width: 768px) {
  .data-table thead {
    display: none;
  }

  .data-table tr {
    display: block;
    margin-bottom: 12px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 12px;
  }

  .data-table td {
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    border: none;
  }

  .data-table td::before {
    content: attr(data-label);
    font-weight: 600;
    color: #6b7280;
  }
}
```

---

## Sorting

### Sort Interaction

```
┌──────────────────────────────────────────────────────────────┐
│ Name ↑        │ Email          │ Created ↕     │ Status      │
├──────────────────────────────────────────────────────────────┤
│ Alice Smith   │ alice@ex.com   │ 2025-01-15    │ Active      │
│ Bob Jones     │ bob@ex.com     │ 2025-02-01    │ Active      │
│ Carol Lee     │ carol@ex.com   │ 2024-12-20    │ Inactive    │
└──────────────────────────────────────────────────────────────┘

↑  = Ascending (currently active)
↕  = Sortable but not active
```

#### Sort State Indicators

| Symbol | Meaning |
|--------|---------|
| ↑ | Sorted ascending |
| ↓ | Sorted descending |
| ↕ | Sortable (click to sort) |
| (none) | Not sortable |

#### Best Practices

- Click column header to sort ascending, click again for descending, third click to clear
- Always show sort direction indicator on the active column
- Use `aria-sort="ascending"` / `aria-sort="descending"` for screen readers
- Default sort should match the most common use case
- Support multi-column sort with Shift+Click (show sort priority numbers)

---

## Filtering

### Filter Bar Pattern

```
┌──────────────────────────────────────────────────────────────┐
│ 🔍 Search users...     [Status ▼] [Role ▼] [Date range ▼]   │
│                                                              │
│ Active filters: Status: Active ✕  │  Role: Admin ✕  [Clear] │
├──────────────────────────────────────────────────────────────┤
│ Showing 24 of 156 users                                      │
```

### Filter Types by Data

| Data Type | Filter UI |
|-----------|-----------|
| Text | Search input (debounced, 300ms) |
| Enum/Category | Dropdown or checkbox group |
| Boolean | Toggle switch |
| Date | Date range picker |
| Number | Range slider or min/max inputs |
| Tags | Multi-select with typeahead |

### Filter Placement

```
Filter placement decision:
├── Few filters (1-3)?
│   └── → Inline filter bar above table
├── Many filters (4-8)?
│   └── → Collapsible filter panel (sidebar or above table)
└── Complex filters with dependencies?
    └── → Dedicated filter modal or side panel
```

### Active Filter Display

- Show active filters as dismissible chips/tags
- Include "Clear all filters" action when any filter is active
- Show result count that updates as filters change
- Persist filters in URL params for shareable filtered views

---

## Pagination vs. Infinite Scroll vs. Virtual Scrolling

### Decision Tree

```
How should users navigate through data?
├── User needs to reach specific pages or find exact position?
│   └── → Pagination
├── Content is browsable/exploratory (social feed, catalog)?
│   ├── Total items < 1,000?
│   │   └── → Infinite scroll
│   └── Total items > 1,000?
│       └── → Infinite scroll with "jump to" option
├── All data must be in DOM for client-side operations?
│   └── → Virtual scrolling (windowed rendering)
└── Data set is very large (10,000+ rows)?
    └── → Server-side pagination OR virtual scrolling
```

### Pagination

```
┌──────────────────────────────────────────────────────────────┐
│ Showing 1-25 of 156               Rows per page: [25 ▼]     │
│                                                              │
│ [← Prev]  1  2  3  ...  6  7  [Next →]                      │
└──────────────────────────────────────────────────────────────┘
```

**Pagination best practices:**
- Show current range ("Showing 1-25 of 156")
- Allow page size selection (10, 25, 50, 100)
- Show first/last page links for long ranges
- Use ellipsis for large page counts
- Keyboard accessible (arrow keys between pages)

### Infinite Scroll

```javascript
const observer = new IntersectionObserver(
  (entries) => {
    if (entries[0].isIntersecting) {
      loadNextPage();
    }
  },
  { rootMargin: '200px' } // Trigger 200px before reaching end
);

observer.observe(document.querySelector('.load-trigger'));
```

**Infinite scroll best practices:**
- Show loading indicator at bottom during fetch
- Preserve scroll position on back navigation
- Provide "Back to top" button after scrolling
- Show total count if known ("Showing 75 of ~500")
- Combine with a "Load more" button as fallback

### Virtual Scrolling

Only render rows visible in the viewport.

```javascript
// Virtual scroll concept
function getVisibleRows(scrollTop, viewportHeight, rowHeight, totalRows) {
  const startIndex = Math.floor(scrollTop / rowHeight);
  const endIndex = Math.min(
    startIndex + Math.ceil(viewportHeight / rowHeight) + 1,
    totalRows
  );

  return {
    startIndex,
    endIndex,
    offsetY: startIndex * rowHeight,
    totalHeight: totalRows * rowHeight
  };
}
```

**Virtual scrolling best practices:**
- Keep row height consistent or measure dynamically
- Render buffer rows above and below viewport (5-10 rows)
- Show scroll position indicator for long lists
- Support keyboard navigation (arrow keys, Page Up/Down)

---

## Bulk Selection & Actions

### Selection Patterns

```
┌──────────────────────────────────────────────────────────────┐
│ ☑ Select all (24 on this page)     [Select all 156 →]       │
│ 3 selected  [Delete] [Export] [Change status ▼]  [✕ Clear]   │
├──────────────────────────────────────────────────────────────┤
│ ☑ │ Alice Smith   │ alice@ex.com   │ Active    │             │
│ ☐ │ Bob Jones     │ bob@ex.com     │ Active    │             │
│ ☑ │ Carol Lee     │ carol@ex.com   │ Inactive  │             │
│ ☑ │ Dave Park     │ dave@ex.com    │ Active    │             │
└──────────────────────────────────────────────────────────────┘
```

### Selection Interactions

| Action | Behavior |
|--------|----------|
| Click checkbox | Toggle individual row |
| Shift + Click | Select range from last selected |
| Header checkbox | Select/deselect all on current page |
| "Select all N" | Select across all pages |

### Bulk Action Bar

```css
.bulk-action-bar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #eff6ff;
  border-bottom: 1px solid #bfdbfe;
}
```

**Best practices:**
- Show bulk action bar only when items are selected
- Display count of selected items
- Require confirmation for destructive bulk actions
- Show progress indicator for long-running bulk operations
- Allow cancellation of in-progress bulk operations

---

## Row Expansion & Detail

### Expandable Rows

```
┌──────────────────────────────────────────────────────────────┐
│ ▶ │ Order #1234  │ Alice Smith │ $149.00  │ Shipped         │
│ ▼ │ Order #1235  │ Bob Jones   │ $89.50   │ Processing      │
│   ├──────────────────────────────────────────────────────────┤
│   │ Items: Widget A (×2), Gadget B (×1)                     │
│   │ Tracking: 1Z999AA10123456784                             │
│   │ Estimated delivery: Jan 20, 2025                         │
│   ├──────────────────────────────────────────────────────────┤
│ ▶ │ Order #1236  │ Carol Lee   │ $250.00  │ Delivered       │
└──────────────────────────────────────────────────────────────┘
```

**Best practices:**
- Use chevron (▶/▼) to indicate expandability
- Expand only one row at a time (accordion) or allow multiple
- Keep expanded content visually connected to the parent row
- Indent or inset expanded content for visual hierarchy

### Inline Editing

```javascript
function enableInlineEdit(cell) {
  const currentValue = cell.textContent;
  const input = document.createElement('input');
  input.value = currentValue;
  input.className = 'inline-edit-input';

  cell.replaceChildren(input);
  input.focus();
  input.select();

  input.addEventListener('blur', () => saveEdit(cell, input.value, currentValue));
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') input.blur();
    if (e.key === 'Escape') {
      input.value = currentValue;
      input.blur();
    }
  });
}
```

```css
.inline-edit-input {
  width: 100%;
  padding: 4px 8px;
  border: 2px solid #3b82f6;
  border-radius: 4px;
  font: inherit;
  background: #eff6ff;
}
```

**Inline edit guidelines:**
- Double-click or click edit icon to activate
- Show clear visual change (border, background) when in edit mode
- Save on blur or Enter, cancel on Escape
- Validate before saving, show errors inline
- Show saving indicator (spinner) during async save

---

## Empty States & Loading

### Empty State Patterns

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│                    📋                                         │
│              No results found                                │
│                                                              │
│    Your search "xyz" didn't match any users.                 │
│    Try adjusting your filters or search terms.               │
│                                                              │
│              [Clear filters]  [Add new user]                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

| Empty State Type | Message Pattern |
|-----------------|-----------------|
| No data yet | Explain what will appear + CTA to create first item |
| No search results | Acknowledge query + suggest adjustments |
| Filtered to empty | Show active filters + "Clear filters" button |
| Error loading | Explain what happened + "Retry" button |

### Loading Skeletons

```css
.skeleton-row {
  display: flex;
  gap: 16px;
  padding: 12px 16px;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

.skeleton-cell {
  height: 16px;
  background: #e5e7eb;
  border-radius: 4px;
}

.skeleton-cell--name { width: 150px; }
.skeleton-cell--email { width: 200px; }
.skeleton-cell--status { width: 80px; }

@keyframes skeleton-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
```

**Loading best practices:**
- Show skeleton that matches table structure (column widths)
- Show 5-10 skeleton rows regardless of expected count
- Transition smoothly from skeleton to real data
- Keep headers visible during loading
- Show spinner only for subsequent page loads, not initial

---

## Table Toolbar

### Standard Toolbar Layout

```
┌──────────────────────────────────────────────────────────────┐
│ Users (156)                                                  │
│                                                              │
│ 🔍 Search...   [Status ▼] [Role ▼]  │  [Export ▼] [+ Add]   │
│                                                              │
│ Active filters: Status: Active ✕     │  Showing 1-25 of 156 │
├──────────────────────────────────────────────────────────────┤
│ ☐ │ Name ↕       │ Email         │ Role    │ Status │ ⋮     │
```

### Column Visibility Toggle

```
┌─────────────────────────────┐
│ Columns                     │
├─────────────────────────────┤
│ ☑ Name                      │
│ ☑ Email                     │
│ ☑ Role                      │
│ ☐ Created date              │
│ ☐ Last login                │
│ ☑ Status                    │
├─────────────────────────────┤
│ [Reset to default]          │
└─────────────────────────────┘
```

---

## Accessibility

### Table Accessibility Checklist

- [ ] Use semantic `<table>`, `<thead>`, `<tbody>`, `<th>`, `<td>` elements
- [ ] Add `scope="col"` to column headers, `scope="row"` to row headers
- [ ] Use `aria-sort` on sortable column headers
- [ ] Provide `aria-label` or `aria-labelledby` on the table
- [ ] Ensure keyboard navigation works (Tab between interactive elements)
- [ ] Row actions accessible via keyboard (Enter/Space to activate)
- [ ] Bulk selection announced to screen readers ("3 rows selected")
- [ ] Pagination controls are keyboard accessible
- [ ] Sort changes announced via `aria-live` region

### Keyboard Navigation

| Key | Action |
|-----|--------|
| Tab | Move to next interactive element |
| Shift + Tab | Move to previous interactive element |
| Enter / Space | Activate button, toggle checkbox, start inline edit |
| Escape | Cancel inline edit, close dropdown |
| Arrow keys | Navigate within dropdowns or between rows (if using `role="grid"`) |

---

## Key Metrics

| Metric | Value | Context |
|--------|-------|---------|
| Rows per page default | 25 | Balance between scanning and loading |
| Max visible columns | 7-10 | Before horizontal scroll or hiding |
| Search debounce | 300ms | Delay before triggering search |
| Skeleton rows | 5-10 | During initial load |
| Column min width | 60px | Minimum resizable width |
| Row height | 40-52px | Comfortable click/tap target |
| Bulk action confirm | Always | For destructive operations |

---

## Anti-Patterns

1. **No sort indicators** - Users can't tell which column is sorted or in which direction
2. **Client-side sort on server-paginated data** - Sorts only the visible page, not the full dataset
3. **Pagination without count** - Users don't know how much data exists
4. **Tiny action buttons** - Hard to click, especially on touch devices
5. **No empty state** - Blank table with headers but no guidance
6. **Inline editing without undo** - Users can't recover from accidental changes
7. **Checkbox column without bulk actions** - Selection exists but does nothing
8. **Filter resets on navigation** - Losing filter state when leaving and returning
9. **No loading state between pages** - Content jumps, users lose context
10. **Forced horizontal scroll on mobile** - Use card reflow instead

---

## Sources

- [Baymard Institute - Data Table Usability](https://baymard.com/blog/data-table-design)
- [Nielsen Norman Group - Data Tables](https://www.nngroup.com/articles/data-tables/)
- [Smashing Magazine - Design Patterns for Complex Data Tables](https://www.smashingmagazine.com/2019/02/complex-web-tables/)
- [TanStack Table](https://tanstack.com/table/) - Headless table library
- [AG Grid - Best Practices](https://www.ag-grid.com/javascript-data-grid/) - Enterprise grid reference
- [Ant Design - Table Component](https://ant.design/components/table) - Pattern reference
