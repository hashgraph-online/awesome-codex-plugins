---
name: implementation-planner
description: Use after requirements, contracts, and visual gates pass to create a TDD-ready implementation plan.
---

# Implementation Planner

This skill creates a task-by-task implementation plan that can be executed with TDD and reviewed after each task.

It is also the bridge from full-stack product contracts into Superpowers execution discipline. Every implementation plan must declare its lifecycle intensity and include a concrete handoff to the execution skills that will carry the work.

## Input Artifacts

- `00-stage.json`
- `00-artifact-registry.json`
- Product, IA, interaction, state, backend/API/frontend, visual, and acceptance contracts
- Visual confirmation when UI applies

## Output Artifact

- `docs/full-stack-development/requirements/<feature-slug>/05-implementation/implementation-plan.md`

## Required MCP Tool

- `review_stage_gate`
- `review_artifact_contract`
- `review_visual_evidence` when UI applies
- `generate_frontend_verification_checklist` when UI applies
- `select_development_flow_profile`
- `plan_superpowers_execution_handoff`

## Hard Stops

- Do not plan implementation when requirements are unapproved.
- Do not plan UI implementation when Pencil/Figma evidence is missing, incomplete, stale, or not reviewed.
- Do not create tasks without test commands and expected failure reasons.
- Do not create an implementation plan without one flow profile: `strict-fullstack`, `strict-ui`, `light-change`, or `debug-fix`.
- Do not begin implementation until `plan_superpowers_execution_handoff` has attached TDD, subagent-driven or executing-plans, requesting-code-review, verification-before-completion, and finishing-a-development-branch.
- Do not let `light-change` bypass change records or completion evidence when requirements or code changed.
- Do not let `debug-fix` skip root-cause evidence or a failing regression test before the fix.

## Pressure Test Responsibility

- Plans without failing tests block.
- Plans without exact files block.
- Plans without verification commands block.
- Plans without a flow profile block.
- Plans without Superpowers execution handoff block.

## Flow Profiles

| Profile | Use When | Required Emphasis |
| --- | --- | --- |
| `strict-fullstack` | Product, UI, backend, API, data, auth, or acceptance contracts may change. | Full requirements workspace, visual evidence when UI applies, backend/API audit, code review, completion gate. |
| `strict-ui` | React Web UI, HeroUI, visual design, responsive state, or interaction behavior changes without backend/API changes. | HeroUI official docs, Pencil/Figma evidence, visual inspection metrics, component graph audit. |
| `light-change` | Small docs, copy, config, or narrowly bounded code changes that do not alter product scope, IA, UI, backend, API, data, auth, or acceptance behavior. | Change record when requirements changed, targeted verification, completion gate. |
| `debug-fix` | Bug, failed test, broken build, regression, or unexpected behavior. | Root-cause investigation, failing regression test, targeted fix, fresh verification. |

## Superpowers Execution Handoff

After the implementation plan passes this skill, attach this handoff:

- `superpowers:test-driven-development`: production code requires a previously observed failing test.
- `superpowers:subagent-driven-development`: default for independent tasks; use one fresh implementer and one reviewer per task.
- `superpowers:executing-plans`: fallback only when subagents are unavailable or tasks are tightly coupled.
- `superpowers:requesting-code-review`: required after each substantial task and before final completion.
- `superpowers:verification-before-completion`: fresh evidence before any completion claim.
- `superpowers:finishing-a-development-branch`: structured branch finish after tests pass.

Required execution artifacts: task brief, task report, review package, `.superpowers/sdd/progress.md`, final code review report, and final acceptance report.

## Next Gate

- `implementation-in-progress` may start only after the implementation plan artifact passes review, a flow profile is selected, and the Superpowers execution handoff is attached.
