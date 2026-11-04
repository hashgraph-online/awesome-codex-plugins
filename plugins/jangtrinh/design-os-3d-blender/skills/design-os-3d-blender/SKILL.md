---
name: design-os-3d-blender
description: "Use when working with DESIGN:OS 3D Blender Agent — Parametric 3D mechanical parts generator, headless Blender Python (`bpy`) pipeline, and embedded Three.js CAD showcase engine."
---

# DESIGN:OS 3D Blender Agent (`design-os-3d-blender`)

Generate dimensionally accurate gears, enclosures, drone frames, and exploded mechanical assemblies from plain-English specs or JSON parameters, complete with glTF/STL exports and interactive browser inspection.

## When to Use

Activate this skill when the user asks to:
- `"Generate a parametric 24-tooth helical gear and mounting bracket in headless Blender and export glTF + STL artifacts."`
- `"Build an interactive Three.js CAD viewer page with exploded-view scrubbing, wireframe toggle, and orthographic camera presets."`
- `"Audit the exported mesh topology for non-manifold edges, zero-area faces, and bounding-box dimensional tolerances."`

## Progressive Disclosure Routing (`What loads when`)

1. **Always Loaded**: `skills/design-os-3d-blender/SKILL.md` (this router — keeps context lean).
2. **On Demand — Prompt Recipes**: Load `docs/cookbook.md` when selecting multi-step workflows or copy-paste prompt templates.
3. **On Demand — Diagnostics**: Load `commands/doctor.md` or run `python3 scripts/self_check.py` when verifying installation or troubleshooting.
4. **On Demand — Ecosystem Discovery**: Load `llms.txt` when cross-referencing companion `DESIGN:OS` engines.

## Core Execution Workflow

1. **Inspect Context**: Read the target repository or workspace constraints before mutating files.
2. **Execute Deterministically**: Run `python3 scripts/self_check.py` or `python3 scripts/self_check.py` rather than guessing outputs freehand.
3. **Verify Quality Gates**: Run `python3 scripts/self_check.py` and confirm zero errors before reporting completion.

## Quality Bar & Anti-Scope

### It's working if...
- `python3 scripts/self_check.py` exits `0`.
- Outputs match the `DESIGN:OS` 2:1 axonometric B&W art direction and deterministic verification gates.
- Execution remains 100% local with zero external telemetry (`PRIVACY.md`).

### When NOT to use
- Sheet-metal or paperboard folding dielines where 2D crease patterns govern topology (use `design-os-origami`).
- Organic character sculpting or AAA rigged game characters requiring manual ZBrush artistry.
- 2D vector UI motion walkthroughs (use `design-os-svg-animation`).
