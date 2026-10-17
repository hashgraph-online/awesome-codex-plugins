---
name: stage-gate-reviewer
description: Use before moving from requirements to design, design to implementation, implementation to verification, or verification to release.
---

# Stage Gate Reviewer

This skill decides whether a stage may proceed. A stage cannot pass by self-declaration.

## Input Artifacts

- `00-stage.json`
- `00-artifact-registry.json`
- Current stage artifacts
- Evidence inventory when verifying completion

## Output Artifact

- `docs/full-stack-development/requirements/<feature-slug>/00-gate-report.md`

## Required MCP Tool

- `review_stage_gate`
- `review_requirement_workspace_stage`
- `review_visual_evidence`
- `review_completion_gate`

## Hard Stops

- No visual design without approved requirements.
- No UI implementation without approved Pencil/Figma visuals reviewed by `review_visual_evidence`.
- No verification pass without test, build, screenshot when UI applies, code review, and acceptance evidence.

## Pressure Test Responsibility

- Jump-to-design requests must block.
- Jump-to-code requests must block.
- A `visualDesignApproved` boolean without visual evidence must block.
- Verification with missing evidence must block.

## Next Gate

- The next stage named by `review_stage_gate.nextAllowedStage`.
