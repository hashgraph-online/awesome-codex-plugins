---
title: Surfaces
impact: MEDIUM
tags: cards, radius, shadow, elevation, blur, components
---

**Rule**: Define one radius scale, one shadow style, and a small set of surface roles. Use a card when content needs its own container, not around everything. Never put a card inside a card.

**Evidence**: Gestalt common region (Palmer 1992) shows that a boundary groups everything inside it. Every extra card adds a boundary and a group, so wrapping everything in cards adds visual noise without adding grouping. Apple's HIG and Material 3 define elevation and shape scales for the same reason.

### When Building

- **A radius scale** of three or four steps (for example 8, 12, 20, plus full pill). Nested corners stay concentric: inner radius = outer radius − padding.
- **One shadow style**, soft and low-contrast, in one or two strengths. In dark mode, show elevation with lighter surfaces instead of shadows.
- **Cards by role.** A card is for a self-contained object the user can act on (an item, a plan, a tile). Lists, settings, and plain text sit on the background or in the platform's grouped list.
- **No card inside a card.** For nested grouping, use spacing, a divider, or a tinted inset area.
- **A small component set**: one card style, one list row, one sheet, one chip. Variants come from content, not from new shapes.
- **Blur or material only over scrolling content**: tab bars, toolbars, and sheets floating above a list. Not on static cards. Keep text over blur legible in both modes.
- **Showcase screens may go bigger**: larger radii, stronger floating shadows, overlapping tiles. Daily screens use the same scale at its smaller end.

### When Auditing

- Every block wrapped in a card with the same radius and shadow
- Cards nested inside cards
- More than four radius values, or inner corners larger than outer ones
- Several shadow styles on one screen, or harsh dark shadows
- Blur on static elements, or text that becomes unreadable over blur
- Near-identical components that differ by a few points

### Incorrect

```css
.section { border-radius: 16px; box-shadow: 0 4px 12px rgb(0 0 0 / .25); }
.section .item { border-radius: 16px; box-shadow: 0 2px 8px rgb(0 0 0 / .3); }
```

### Correct

```css
.section { border-radius: var(--radius-lg); background: var(--surface-raised); }
.section .item + .item { border-top: 1px solid var(--divider); }
```

### Why This Matters

Boxes everywhere make a screen look like a template, because templates box everything. A few deliberate surfaces with a consistent shape scale look designed, and leave the background room to separate groups with space.

### Alternatives

Card-based products (wallets, boards, galleries) can make cards the main surface, but they still avoid nesting and use one card style. Platform system containers (grouped lists, Material cards) count as the platform's surface system: use them as they are.
