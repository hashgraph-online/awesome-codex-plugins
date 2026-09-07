---
name: visual-evidence-gate
description: Use after requirements are approved and before UI implementation when a product feature needs Pencil or Figma visual design evidence.
---

# Visual Evidence Gate

This skill turns Pencil/Figma images into a machine-reviewable handoff contract. It is the bridge between requirement approval, visual design, and HeroUI implementation.

## Input Artifacts

- `00-stage.json`
- `00-artifact-registry.json`
- Product, IA, interaction, state, frontend/HeroUI, and acceptance contracts
- `10-visual-confirmation-plan.md`
- Pencil or Figma exports and approval record

## Output Artifact

- `docs/full-stack-development/requirements/<feature-slug>/04-visual/visual-evidence.md`

## Required MCP Tool

- `generate_design_board_inventory`
- `review_visual_evidence`
- `review_stage_gate`

## Hard Stops

- Do not start Pencil/Figma until requirement approval and the visual-design stage gate pass.
- Do not start UI implementation from a single screenshot, chat approval, or desktop-only export.
- Do not accept visual approval without desktop, mobile, component-detail, and state-matrix boards.
- Do not reuse stale visuals after `00-stage.json.latestChangeId` changes.
- Do not let `approvals.visualDesignApproved: true` bypass `review_visual_evidence`.

## Pressure Test Responsibility

- Desktop-only export must block.
- Missing component-detail coverage must block.
- Missing state-matrix coverage must block.
- Missing user approval record must block.
- Stale change id must block after a requirement change.

## Next Gate

- `implementation` may start only when `review_visual_evidence.status` is `pass` and `review_stage_gate` also passes for `targetStage: "implementation"`.

