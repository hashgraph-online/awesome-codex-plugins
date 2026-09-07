---
name: full-stack-development
description: MUST use first when Codex works on a product, feature, app, website, landing page, brand site, admin system, backend, database, API, front-end design draft, Pencil/Figma design, full-stack implementation, or any rough goal needing requirements, architecture, design, implementation, verification, or requirement-change handling. When brainstorming also applies, this skill's requirement-discovery and fixed workspace run before brainstorming, visual companion, Pencil/Figma, or code.
---

# Full Stack Development

This is the top-level delivery skill for full-stack product work and the general Codex product development plugin. It owns requirement clarification, Artifact Registry, Stage Gate review, backend/frontend contracts, visual approval, implementation gates, change handling, Completion Gate review, and verification.

HeroUI is not the top-level workflow. HeroUI is the front-end layer. Use `hero-ui-craft` as the required frontend UI sub-skill when a task reaches React Web UI, Pencil/Figma, HeroUI components, or visual verification.

## Entry Arbitration

If the user asks for a product, website, landing page, brand site, admin system, app, front-end design draft, Pencil/Figma design, or says "do not develop yet", this skill is the entry workflow.

When `brainstorming` also applies, do not let it replace this workflow. Treat brainstorming as optional raw material inside requirement discovery only after the fixed workspace has been started. Do not offer a visual companion, browser preview, Pencil/Figma drawing, or implementation before `generate_requirement_workspace` creates `docs/full-stack-development/requirements/<feature-slug>/` and the current stage is recorded in `00-stage.json`.

For a one-line request such as "I want a high-end coffee brand website, make the front-end design draft first, do not develop", the first observable actions must be:

1. Inspect the workspace.
2. Run lifecycle hook coverage when available.
3. Call `generate_requirement_workspace`.
4. Draft requirement-discovery artifacts in the fixed workspace.
5. Report that Pencil/Figma and implementation are blocked until requirement review and user confirmation pass.

## Core Rule

The user only needs to provide a rough goal, corrections, and confirmations. The agent must draft the missing structure: business requirements, product requirements, information architecture, interaction matrix, state requirements, backend/data/API contracts, frontend/HeroUI contracts, visual requirements, and acceptance criteria.

Do not begin Pencil/Figma or implementation from chat-only requirements.

## Fixed Workspace

For every feature, create or update:

`docs/full-stack-development/requirements/<feature-slug>/`

Then use the local MCP tools to generate/review the gate:

- `generate_requirement_workspace`
- `review_requirement_workspace_stage`
- `plan_requirement_change`
- `list_artifact_contracts`
- `review_artifact_contract`
- `review_stage_gate`
- `plan_change_impact`
- `mark_artifacts_stale`
- `inspect_tailwind_ui_reference`
- `plan_tailwind_hero_ui_adoption`
- `plan_visual_design_orchestration`
- `generate_design_board_inventory`
- `review_visual_design_orchestration`
- `review_visual_evidence`
- `review_completion_gate`
- `review_visual_inspection_metrics`
- `review_hero_ui_component_graph_audit`
- `review_backend_contract_audit`
- `review_code_review_gate`
- `review_hero_ui_docs_freshness`
- `select_development_flow_profile`
- `plan_superpowers_execution_handoff`
- `list_lifecycle_hooks`
- `review_lifecycle_hook_coverage`
- `run_lifecycle_hook`

The workspace must contain a current `00-stage.json`. It is the source of truth for the current phase and approvals.

## Required Flow

1. Inspect the project stack, package manager, framework, data layer, API style, deployment target, and existing UI system.
2. Run `list_lifecycle_hooks` and `review_lifecycle_hook_coverage` before stage work if the workspace does not already record hook coverage.
3. For every stage transition, call `run_lifecycle_hook` with `event: "before"` before entering the stage and `event: "after"` before leaving the stage. Missing required hook evidence blocks the transition.
4. Create the fixed requirement workspace under `docs/full-stack-development/requirements/<feature-slug>/`.
5. Draft requirements as agent-owned artifacts. Mark assumptions and focused user questions.
6. Get user confirmation and update `00-stage.json` with `approvals.requirementsApproved: true` or `currentStage: "visual-design-ready"`.
7. If the feature has React Web UI, use `hero-ui-craft` before Pencil/Figma.
8. Run `review_requirement_workspace_stage` for `targetStage: "visual-design"` before Pencil/Figma.
9. If the user provides TailwindUI/Tailwind Plus local material, run `inspect_tailwind_ui_reference` and `plan_tailwind_hero_ui_adoption`; treat it as reference-only.
10. Run `plan_visual_design_orchestration` and `generate_design_board_inventory` to define required Pencil/Figma boards.
11. Export desktop, mobile, component-detail, and state-matrix images from Pencil/Figma.
12. Get user approval for visuals and write the approval record.
13. Run `review_visual_design_orchestration` and `review_visual_evidence`; a visual-approved flag alone is not enough.
14. Run `review_requirement_workspace_stage` and `review_stage_gate` for `targetStage: "implementation"` before code.
15. Before writing the implementation plan, run `select_development_flow_profile` and record exactly one profile: `strict-fullstack`, `strict-ui`, `light-change`, or `debug-fix`.
16. After the implementation plan is drafted, run `plan_superpowers_execution_handoff` and attach the Superpowers execution chain: TDD, subagent-driven or executing-plans, code review, verification-before-completion, and finishing branch workflow.
17. Implement backend, data, API, frontend, tests, and verification according to the workspace, selected flow profile, lifecycle hooks, and Superpowers execution handoff.
18. Run project tests, build, browser screenshots, accessibility checks, HeroUI quality review, visual inspection metrics, component graph audit, backend contract audit, code review gate, and docs freshness review when applicable.

## Requirement Changes

When the user changes or upgrades requirements:

- Call `plan_requirement_change`.
- Append the change record under `docs/full-stack-development/requirements/<feature-slug>/changes/`.
- Update impacted requirement artifacts.
- Update `00-stage.json`.
- Regress to the earliest impacted stage.
- Re-run the relevant review gate.
- Treat prior visuals or implementation as stale if the change affects product, IA, interaction, state, visual, engineering, API, data, or acceptance contracts.

## Hard Stops

- No brainstorming visual companion, browser preview, Pencil/Figma drawing, or code before requirement discovery starts the fixed workspace for product/site/design requests.
- No Pencil/Figma without a fixed workspace and approved requirements.
- No implementation without approved Pencil/Figma visuals when UI is involved.
- No frontend UI implementation that bypasses `hero-ui-craft` and official HeroUI checks.
- No backend/API/database implementation when data contracts, API contracts, auth/permission rules, errors, migration impact, and acceptance tests are missing.
- No implementation plan without a declared flow profile.
- No implementation after planning unless the Superpowers execution handoff is attached.
- No stage transition without the matching `run_lifecycle_hook` evidence.
- Do not add `hooks` to `.codex-plugin/plugin.json`; current plugin validation rejects that manifest field. Use the internal lifecycle hook registry and MCP hook runner.
- No “just update code” after requirement changes; record the change and regress the stage first.
- No stage may pass by self-declaration. Use Stage Gate and artifact evidence.
- No completion claim without the Completion Gate: fresh tests, build, screenshots when UI applies, code review, and final acceptance evidence.

## Lifecycle Skills

- `requirement-discovery`: drafts the first structured contract from a rough goal.
- `artifact-contract-manager`: owns Artifact Registry and artifact PASS rules.
- `stage-gate-reviewer`: decides whether the next stage can proceed.
- `stage-gate-reviewer`: must consume lifecycle hook evidence alongside stage gate results.
- `change-control`: records requirement changes and regresses stages.
- `tailwind-reference-adapter`: indexes local TailwindUI/Tailwind Plus material as reference-only and maps it back to HeroUI.
- `visual-design-orchestrator`: plans and reviews the one-pass Pencil/Figma execution workflow.
- `visual-evidence-gate`: reviews Pencil/Figma desktop, mobile, component-detail, state-matrix, approval, and staleness evidence.
- `implementation-planner`: creates implementation plans with TDD and evidence gates, selects the flow profile, and attaches the Superpowers execution handoff before implementation begins.
- `quality-auditor`: audits visual metrics, HeroUI component graph, backend/API contracts, code review evidence, and docs freshness.
- `completion-verifier`: blocks false completion claims until evidence is complete.

## References

Read `references/full-stack-stage-contract.md` when creating or reviewing the workspace, handling requirement changes, or deciding whether the current stage allows design or implementation.
