---
name: css-math-units
description: "Explain, derive, and debug CSS math for measurement units, calc(), min(), max(), clamp(), custom properties, inheritance, em/rem scaling, percentages, viewport units, and box model formulas. Use when CSS dimensions compute unexpectedly, when mixing units, when building scalable spacing/type systems, or when reviewing box sizing and inherited values."
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: CSS Math Units
  category: Frontend
  tags: frontend,css,units,layout,math
---

# CSS Math Units

Use this skill to trace how CSS values become computed layout values. It is useful for unit conversion, inherited size multiplication, calc expressions, custom property math, and box model sizing.

## Quick Start

1. Read `guidelines.md` to select the smallest relevant file set.
2. Load `references/css-calculations/rules.md` for implementation decisions.
3. Load `references/css-calculations/examples.md` when editing code.
4. Use `workflows/debug-css-calculation.md` for multi-step derivation or debugging.

## Contents

| Resource | Purpose |
|----------|---------|
| `guidelines.md` | Routes tasks to the right reference files |
| `references/source-map.md` | Book source and chapter/section traceability |
| `references/css-calculations/knowledge.md` | Core concepts and terminology |
| `references/css-calculations/rules.md` | Practical rules, guidelines, and exceptions |
| `references/css-calculations/examples.md` | Bad/good examples and refactoring approach |
| `references/css-calculations/patterns.md` | Reusable formula and implementation patterns |
| `references/css-calculations/checklist.md` | Review checklist and red flags |
| `workflows/debug-css-calculation.md` | Step-by-step workflow |

## Source

Derived from *Math for Web Design* by Paul McFedries, Chapter 3: Math basics for CSS.
Citations are tracked in `references/source-map.md`.
