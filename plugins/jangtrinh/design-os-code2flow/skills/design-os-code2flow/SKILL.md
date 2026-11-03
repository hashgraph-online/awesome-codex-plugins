---
name: design-os-code2flow
description: "Use when working with DESIGN:OS Code2Flow — Local-first AST codebase-to-user-flow mapper and 11-heuristic UX gap auditor across 7 frontend and mobile frameworks."
---

# DESIGN:OS Code2Flow (`design-os-code2flow`)

Statically analyze Next.js, React Router, TanStack Router, Expo Router, SwiftUI, Flutter, and Jetpack Compose repositories to generate Mermaid user-flow graphs and catch dead-end screens, missing error boundaries, and unguarded auth routes.

## When to Use

Activate this skill when the user asks to:
- `"Scan this Next.js App Router repository with code2flow, generate the Mermaid user-flow diagram, and list all high-severity UX gaps."`
- `"Audit our SwiftUI navigation stack for dead-end screens, missing loading/error states, and unguarded destructive actions."`
- `"Export a JSON + Markdown user-flow topology report for our PR review gate."`

## Progressive Disclosure Routing (`What loads when`)

1. **Always Loaded**: `skills/design-os-code2flow/SKILL.md` (this router — keeps context lean).
2. **On Demand — Prompt Recipes**: Load `docs/cookbook.md` when selecting multi-step workflows or copy-paste prompt templates.
3. **On Demand — Diagnostics**: Load `commands/doctor.md` or run `python3 scripts/self_check.py` when verifying installation or troubleshooting.
4. **On Demand — Ecosystem Discovery**: Load `llms.txt` when cross-referencing companion `DESIGN:OS` engines.

## Core Execution Workflow

1. **Inspect Context**: Read the target repository or workspace constraints before mutating files.
2. **Execute Deterministically**: Run `npm test` or `node bin/code2flow.mjs audit .` rather than guessing outputs freehand.
3. **Verify Quality Gates**: Run `python3 scripts/self_check.py` and confirm zero errors before reporting completion.

## Quality Bar & Anti-Scope

### It's working if...
- `python3 scripts/self_check.py` exits `0`.
- Outputs match the `DESIGN:OS` 2:1 axonometric B&W art direction and deterministic verification gates.
- Execution remains 100% local with zero external telemetry (`PRIVACY.md`).

### When NOT to use
- Pure backend microservices or CLI tools with no screen/route navigation graph.
- Visual pixel-level contrast or typography inspection (pair with `design-os` or `design-os-figma-plugin`).
- Runtime profiling of database query latency.
