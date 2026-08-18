---
name: visual-design-orchestrator
description: Use after requirements are approved to run the one-pass Pencil or Figma workflow that creates visual boards, exports images, records approval, and hands off to implementation gates.
---

# Visual Design Orchestrator

This skill coordinates the design-tool execution path. It does not replace user approval or visual evidence review; it makes the steps explicit and repeatable.

## Input Artifacts

- `00-stage.json`
- `10-visual-confirmation-plan.md`
- Product, IA, interaction, state, visual, HeroUI, and acceptance contracts
- HeroUI component mapping
- Optional TailwindUI reference index

## Output Artifact

- `docs/full-stack-development/requirements/<feature-slug>/04-visual/visual-evidence.md`

## Required MCP Tool

- `plan_visual_design_orchestration`
- `generate_design_board_inventory`
- `review_visual_design_orchestration`
- `review_visual_evidence`
- `review_stage_gate`

## Hard Stops

- Do not start Pencil/Figma until the requirement workspace passes `review_requirement_workspace_stage` for visual design.
- Do not skip Pencil `get_editor_state(include_schema: true)`.
- Do not skip required Figma skills before Figma write operations.
- Do not proceed with only chat approval; write the approval record into `visual-evidence.md`.
- Do not proceed to implementation until `review_visual_design_orchestration`, `review_visual_evidence`, and `review_stage_gate` all pass.

## Pressure Test Responsibility

- Missing design board inventory must block.
- Missing desktop, mobile, component-detail, or state-matrix export must block.
- Missing user approval record must block.
- Stale visual evidence after requirement change must block.

## Next Gate

- `implementation-planner` may run only after visual orchestration and visual evidence both pass.

