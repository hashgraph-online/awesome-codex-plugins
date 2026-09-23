# Image Analysis

Use this inventory for dense or multi-state screens. For a simple screen, keep
only the notes needed to implement and verify it; the template is optional.

## Evidence Grades

- `SOURCE`: directly visible in the image, measured from metadata or screenshot,
  confirmed in code, or confirmed by the user.
- `PARTIAL`: likely but incomplete, such as a readable layout with an uncertain
  icon meaning.
- `GUESS`: inference without direct evidence. State reversible visual decisions;
  resolve consequential business or scope decisions before implementing them.

## UI_RECON.md Template

```markdown
# <screen-name> UI Recon

## Input
- Source image:
- Design size:
- Design size source:
- Target:

## Screen Summary
- Screen type:
- Primary user goal:
- Scroll behavior:
- Responsive expectation:

## Layout
| Region | Bounds / proportion | Description | Evidence |
|---|---:|---|---|
| Root |  |  | SOURCE |

## Component Tree
| Component | Parent | Visual role | Implementation candidate | Evidence |
|---|---|---|---|---|

## Text Inventory
| Text | Location | Confidence | Notes |
|---|---|---:|---|

## Design Tokens
- Colors:
- Typography:
- Spacing:
- Radius:
- Borders:
- Shadows:
- Motion:

## Assets And Icons
| Asset/Icon | Meaning | Available locally? | Evidence |
|---|---|---|---|

## States And Interactions
| Element | State/interaction | Evidence | Needs confirmation? |
|---|---|---|---|

## Interactive Control Inventory
| Element | Control type | Visible state | Required implementation | Hidden behavior known? | Evidence |
|---|---|---|---|---|---|

## Open Questions
- `<question>`

## Implementation Notes
- `<note>`
```

## Analysis Checklist

### Screen Type

Classify the screen because it changes implementation priorities:

- Marketing or landing page.
- Dashboard or admin page.
- Data table or CRUD page.
- Form or wizard.
- Modal, drawer, popover, tooltip.
- Mobile app screen.
- Empty, loading, error, or success state.
- Chart, map, editor, canvas, or media-heavy screen.

### Layout

Record the visible structure:

- Root frame size.
- Primary columns/rows.
- Fixed header/sidebar/footer.
- Content max width.
- Section rhythm and gutters.
- Alignment: left, centered, strict grid, asymmetric.
- Scroll assumptions: no scroll, vertical scroll, internal scroll panel.

### Components

Prefer semantic components over raw boxes:

- Button, icon button, segmented control.
- Tabs, menu, breadcrumb, pagination.
- Input, select, date picker, search, checkbox, switch.
- Table, list, card, stat tile, timeline.
- Dialog, drawer, popover.
- Chart, map, media viewer.

If a component's semantic role is unclear, inspect context first; ask when the
remaining ambiguity changes its behavior or business meaning.

### Interactive Control Inventory

Create an explicit inventory for every visible control. This prevents a visual
clone from becoming a static screenshot.

Classify each element:

- `semantic`: the image clearly shows a known control type.
- `decorative`: the element is purely visual and not a user control.
- `unclear`: the element may be a control but its role is ambiguous; resolve from
  context or record the affected behavior as a gap.

Default semantic mappings:

| Visual evidence | Treat as | Minimum behavior |
|---|---|---|
| Text field, search field, numeric field | Input | Focusable, value shown, editable unless visibly disabled |
| Dropdown/select with chevron | Select or combobox | Focusable, opens or exposes known options; otherwise preserve visible value and record missing options |
| Button/CTA/icon button | Button | Focusable/clickable; no-op or mocked handler only when real action is unknown |
| Tabs/segmented control | Tabs | Active tab state and switching among known panels; record unknown panel content |
| Checkbox/radio/switch | Form control | Checked/unchecked/disabled state from image |
| Accordion/collapse row | Disclosure | Expanded/collapsed state; toggle visible content when known |
| Table with headers/rows | Table | Semantic table; sorting/filtering only when evidenced or confirmed |
| Pagination/stepper | Navigation control | Current state visible; navigation over known data only |

If options, panels, modal content, destination routes, backend actions, or data
effects are not visible or known from the project, record the missing behavior.
Ask if it is needed to fulfill the requested workflow; continue independent
visible work. Do not fabricate business content or use unknown hidden behavior
as a reason to make the visible control non-semantic. No-op and mock handlers
must be reported as incomplete or prototype behavior.

### Text

Preserve readable text exactly. Mark uncertain text as `PARTIAL` or `GUESS`;
resolve business-critical labels and report any remaining transcription gaps.

### Visual Tokens

Extract tokens with practical granularity:

```json
{
  "color": {
    "background": "",
    "surface": "",
    "primaryText": "",
    "secondaryText": "",
    "accent": "",
    "border": ""
  },
  "typography": {
    "display": "",
    "heading": "",
    "body": "",
    "caption": ""
  },
  "spacing": {
    "baseUnit": "",
    "sectionGap": "",
    "componentGap": "",
    "contentPadding": ""
  },
  "shape": {
    "smallRadius": "",
    "mediumRadius": "",
    "largeRadius": ""
  }
}
```

### Interaction And Hidden Behavior

A static image rarely proves hidden behavior. Resolve these from project/user
evidence when required by the requested workflow:

- Does clicking this open a modal, route, drawer, or dropdown?
- Are rows selectable?
- Is this chart interactive?
- Does the sidebar collapse?
- Does the table have sorting, filtering, pagination, or virtual scroll?

However, do not ask whether an obvious control should be semantic. If the image
clearly shows tabs, inputs, selects, buttons, checkboxes, switches, accordions,
or table rows, implement the visible control semantics by default. Ask about
missing hidden behavior only when that decision blocks the requested outcome.

## Ambiguity Examples

Check these ambiguities against context; ask when their meaning matters and
cannot be inferred, while continuing independent implementation:

- A top-right bell-like glyph might be notification or activity.
- A blue chip might be selected, focused, or merely highlighted.
- A chart has no axis labels or data source.
- A blurry label could change business meaning.
- A button could be primary action or destructive action.
- A card could be a clickable item or static information.
- A dropdown's current value is visible, but its option list is not.
- A tab control is visible, but the inactive tab panels are not shown.
