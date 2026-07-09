---
name: javascript-ui-math
description: "Use JavaScript number math safely for front-end UI behavior, including expressions, precedence, coercion, NaN, Infinity, floating-point precision, BigInt limits, modulo wrapping, rounding, random values, and repeatable UI randomness. Use when building sliders, carousels, counters, animation values, randomized UI, financial-ish display values, or debugging numeric edge cases in browser JavaScript."
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: JavaScript UI Math
  category: Frontend
  tags: frontend,javascript,ui,math,debugging
---

# JavaScript UI Math

Use this skill for numeric browser behavior that needs predictable edge-case handling. It helps avoid common JavaScript traps around coercion, precision, modulo behavior, rounding, randomization, and BigInt.

## Quick Start

1. Read `guidelines.md` to select the smallest relevant file set.
2. Load `references/ui-numbers/rules.md` for implementation decisions.
3. Load `references/ui-numbers/examples.md` when editing code.
4. Use `workflows/debug-ui-number-logic.md` for multi-step derivation or debugging.

## Contents

| Resource | Purpose |
|----------|---------|
| `guidelines.md` | Routes tasks to the right reference files |
| `references/source-map.md` | Book source and chapter/section traceability |
| `references/ui-numbers/knowledge.md` | Core concepts and terminology |
| `references/ui-numbers/rules.md` | Practical rules, guidelines, and exceptions |
| `references/ui-numbers/examples.md` | Bad/good examples and refactoring approach |
| `references/ui-numbers/patterns.md` | Reusable formula and implementation patterns |
| `references/ui-numbers/checklist.md` | Review checklist and red flags |
| `workflows/debug-ui-number-logic.md` | Step-by-step workflow |

## Source

Derived from *Math for Web Design* by Paul McFedries, Chapter 2: Math basics for JavaScript.
Citations are tracked in `references/source-map.md`.
