---
name: responsive-layout-math
description: "Derive, review, and debug responsive web layout math for fluid widths, media query ranges, viewport units, percentages, and CSS clamp() formulas. Use when building responsive layouts, converting fixed designs to fluid CSS, calculating breakpoints, choosing vw/svw/lvw/dvw units, or deciding whether CSS math or JavaScript measurement should own a layout behavior."
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Responsive Layout Math
  category: Frontend
  tags: frontend,css,responsive-design,layout,math
---

# Responsive Layout Math

Use this skill to turn fixed layout intentions into proportional, bounded, and testable responsive CSS. It is strongest when the task involves deriving a formula rather than picking arbitrary breakpoint values.

## Quick Start

1. Read `guidelines.md` to select the smallest relevant file set.
2. Load `references/fluid-layouts/rules.md` for implementation decisions.
3. Load `references/fluid-layouts/examples.md` when editing code.
4. Use `workflows/design-fluid-layout.md` for multi-step derivation or debugging.

## Contents

| Resource | Purpose |
|----------|---------|
| `guidelines.md` | Routes tasks to the right reference files |
| `references/source-map.md` | Book source and chapter/section traceability |
| `references/fluid-layouts/knowledge.md` | Core concepts and terminology |
| `references/fluid-layouts/rules.md` | Practical rules, guidelines, and exceptions |
| `references/fluid-layouts/examples.md` | Bad/good examples and refactoring approach |
| `references/fluid-layouts/patterns.md` | Reusable formula and implementation patterns |
| `references/fluid-layouts/checklist.md` | Review checklist and red flags |
| `workflows/design-fluid-layout.md` | Step-by-step workflow |

## Source

Derived from *Math for Web Design* by Paul McFedries, Chapter 6: The mathematics of responsive design.
Citations are tracked in `references/source-map.md`.
