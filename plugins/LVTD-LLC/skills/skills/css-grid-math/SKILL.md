---
name: css-grid-math
description: "Derive and debug CSS Grid layout math for grid coordinates, line placement, spans, negative indexes, fr units, minmax(), fit-content(), repeat(), auto-fill, and auto-fit. Use when building grid systems, explaining track sizing, troubleshooting fr distribution, placing items by line numbers, or converting a layout sketch into CSS Grid formulas."
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: CSS Grid Math
  category: Frontend
  tags: frontend,css,grid,layout,math
---

# CSS Grid Math

Use this skill when a grid needs to be reasoned about as a coordinate and sizing system. It helps calculate where items land, how tracks divide space, and why flexible tracks do not always produce expected widths.

## Quick Start

1. Read `guidelines.md` to select the smallest relevant file set.
2. Load `references/grid-layout/rules.md` for implementation decisions.
3. Load `references/grid-layout/examples.md` when editing code.
4. Use `workflows/debug-grid-layout.md` for multi-step derivation or debugging.

## Contents

| Resource | Purpose |
|----------|---------|
| `guidelines.md` | Routes tasks to the right reference files |
| `references/source-map.md` | Book source and chapter/section traceability |
| `references/grid-layout/knowledge.md` | Core concepts and terminology |
| `references/grid-layout/rules.md` | Practical rules, guidelines, and exceptions |
| `references/grid-layout/examples.md` | Bad/good examples and refactoring approach |
| `references/grid-layout/patterns.md` | Reusable formula and implementation patterns |
| `references/grid-layout/checklist.md` | Review checklist and red flags |
| `workflows/debug-grid-layout.md` | Step-by-step workflow |

## Source

Derived from *Math for Web Design* by Paul McFedries, Chapter 4: CSS Grid math.
Citations are tracked in `references/source-map.md`.
