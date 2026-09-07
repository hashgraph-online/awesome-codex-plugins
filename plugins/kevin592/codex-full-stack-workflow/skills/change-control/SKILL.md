---
name: change-control
description: Use whenever the user changes, upgrades, or corrects requirements after initial intake.
---

# Change Control

This skill records requirement changes, calculates impacted artifacts, marks stale downstream contracts, invalidates approvals, and regresses to the earliest impacted stage.

## Input Artifacts

- User change request
- `00-stage.json`
- `00-artifact-registry.json`
- Existing approved artifacts

## Output Artifact

- `docs/full-stack-development/requirements/<feature-slug>/changes/<change-id>-change-request.md`

## Required MCP Tool

- `plan_change_impact`
- `mark_artifacts_stale`
- `plan_requirement_change`
- `review_stage_gate`

## Hard Stops

- Do not directly edit code after a requirement change.
- Do not keep old visual approval when IA, interaction, state, visual, frontend, API, or product contracts changed.
- Do not keep implementation approval when behavior or engineering contracts changed.

## Pressure Test Responsibility

- Role changes regress to product scope.
- Field/action/state changes regress to IA, interaction, and state.
- API/auth changes regress to backend/API/frontend contract.
- Acceptance command changes regress to verification.

## Next Gate

- Re-run `review_stage_gate` for the regressed stage before design or implementation continues.

