---
name: color-math-accessibility
description: "Calculate, review, and generate web color systems using RGB, HSL, LAB, OKLCH, contrast ratios, luminance, opacity, blend modes, and light/dark mode transformations. Use when auditing accessible colors, converting color models, deriving palettes, checking WCAG contrast, building theme tokens, or debugging opacity and CSS blend math."
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Color Math Accessibility
  category: Frontend
  tags: frontend,css,color,accessibility,design-systems
---

# Color Math Accessibility

Use this skill when colors need to be explainable, accessible, and reproducible. It focuses on color math that affects real UI outcomes: contrast, palette relationships, perceptual lightness, opacity, and blending.

## Quick Start

1. Read `guidelines.md` to select the smallest relevant file set.
2. Load `references/color-systems/rules.md` for implementation decisions.
3. Load `references/color-systems/examples.md` when editing code.
4. Use `workflows/audit-color-system.md` for multi-step derivation or debugging.

## Contents

| Resource | Purpose |
|----------|---------|
| `guidelines.md` | Routes tasks to the right reference files |
| `references/source-map.md` | Book source and chapter/section traceability |
| `references/color-systems/knowledge.md` | Core concepts and terminology |
| `references/color-systems/rules.md` | Practical rules, guidelines, and exceptions |
| `references/color-systems/examples.md` | Bad/good examples and refactoring approach |
| `references/color-systems/patterns.md` | Reusable formula and implementation patterns |
| `references/color-systems/checklist.md` | Review checklist and red flags |
| `workflows/audit-color-system.md` | Step-by-step workflow |

## Source

Derived from *Math for Web Design* by Paul McFedries, Chapter 7: The mathematics of color.
Citations are tracked in `references/source-map.md`.
