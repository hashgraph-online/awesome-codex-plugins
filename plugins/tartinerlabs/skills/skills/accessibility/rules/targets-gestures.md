---
title: Touch Targets and Gestures
impact: HIGH
tags: target-size, gestures, drag, swipe, motor, switch-control
wcag: 2.5.1, 2.5.7, 2.5.8
---

**Rule**: Targets are large enough to hit, and every action that needs a complex gesture or dragging also works with a single tap or click.

**Why**: Tremors, limited dexterity, and assistive pointers make small targets and precise gestures hard or impossible. WCAG requires single-pointer alternatives to path-based and multi-point gestures (2.5.1), and — new in WCAG 2.2 — alternatives to dragging (2.5.7) and a minimum target size of 24×24 CSS px or enough spacing (2.5.8). Platform guidance is larger: 44×44 pt on Apple platforms, 48×48 dp on Android.

### When Building

- **Platform minimums** for touch: 44×44 pt (Apple), 48×48 dp (Android); at least 24×24 CSS px on the web, larger for primary touch actions
- **Hit area, not icon size** — pad small icons rather than enlarging the artwork
- **Spacing** between adjacent targets so a slightly-off tap doesn't hit the neighbour
- **Every drag has a tap alternative** — reorder with "Move up/down" or a menu; sliders also take tap and keyboard; drag-and-drop uploads also have a file picker
- **Multi-finger and path gestures** (pinch, two-finger swipe, draw a path) have a button alternative — zoom controls next to a pinch-zoomable map
- **Swipe actions** are also available from a menu or edit mode, and as screen reader custom actions (platform guides)
- **Actions fire on release**, so a user can slide off a target to cancel

### When Auditing

- Icon buttons with hit areas below the platform minimum
- Reorderable lists, sliders, and canvases that only support dragging
- Swipe-only actions with no menu or custom-action alternative
- Pinch or multi-finger gestures with no alternative control

### Incorrect

```tsx
<SortableList items={items} onReorder={setItems} />  {/* drag handles only */}
```

### Correct

```tsx
<SortableList items={items} onReorder={setItems}
  renderActions={(item) => <ItemMenu actions={["Move up", "Move down"]} item={item} />} />
```

### Alternatives

Inline links in a paragraph are exempt from the target-size minimum, as are targets whose size is essential to the information (pins on a map at true scale) — but give those a list or search alternative.
