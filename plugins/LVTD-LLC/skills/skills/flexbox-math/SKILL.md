---
name: flexbox-math
description: "Calculate and debug Flexbox layout math for flex base size, flex-basis, flex-grow, flex-shrink, the flex shorthand, fractional grow values, and min/max constraints. Use when flex items resize unexpectedly, when distributing free space along one axis, when comparing flexbox with grid, or when deriving predictable card, nav, toolbar, and row layouts."
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Flexbox Math
  category: Frontend
  tags: frontend,css,flexbox,layout,math
---

# Flexbox Math

Use this skill for one-dimensional layout distribution. It focuses on the arithmetic that determines base sizes, free space, grow allocation, shrink allocation, and constraint clamping.

## Quick Start

1. Read `guidelines.md` to select the smallest relevant file set.
2. Load `references/flex-distribution/rules.md` for implementation decisions.
3. Load `references/flex-distribution/examples.md` when editing code.
4. Use `workflows/debug-flex-distribution.md` for multi-step derivation or debugging.

## Contents

| Resource | Purpose |
|----------|---------|
| `guidelines.md` | Routes tasks to the right reference files |
| `references/source-map.md` | Book source and chapter/section traceability |
| `references/flex-distribution/knowledge.md` | Core concepts and terminology |
| `references/flex-distribution/rules.md` | Practical rules, guidelines, and exceptions |
| `references/flex-distribution/examples.md` | Bad/good examples and refactoring approach |
| `references/flex-distribution/patterns.md` | Reusable formula and implementation patterns |
| `references/flex-distribution/checklist.md` | Review checklist and red flags |
| `workflows/debug-flex-distribution.md` | Step-by-step workflow |

## Source

Derived from *Math for Web Design* by Paul McFedries, Chapter 5: Flexbox math.
Citations are tracked in `references/source-map.md`.
