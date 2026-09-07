# Full Stack Stage Contract

Use this reference when a rough request must become a stable full-stack delivery plan.

## Workspace

All artifacts live under:

`docs/full-stack-development/requirements/<feature-slug>/`

The workspace is agent-owned. The user confirms and corrects; the user is not expected to supply architecture, interaction, API, data, state, or acceptance detail from scratch.

## Stage File

`00-stage.json` is mandatory.

It must track:

- `currentStage`
- `nextAllowedStage`
- `approvals.requirementsApproved`
- `approvals.visualDesignApproved`
- `approvals.implementationApproved`
- lifecycle hook evidence for the current transition
- blocked gates
- change policy
- latest change id

Generated empty templates are not enough. Pencil/Figma requires user-confirmed requirements.

## Full-Stack Requirement Layers

Required layers:

| Layer | Required Content |
| --- | --- |
| rough request | raw ask, agent interpretation, scope, unknowns |
| business requirements | why, success metrics, business rules, priority, risk |
| product requirements | users, tasks, workflows, feature scope, non-goals |
| information architecture | objects, hierarchy, navigation, data fields, content priority |
| interaction matrix | triggers, actions, feedback, permissions, keyboard behavior |
| state requirements | loading, empty, error, success, disabled, editing, mobile |
| backend/data requirements | entities, schema, storage, migrations, validation, retention |
| API contract | endpoints/actions, inputs, outputs, errors, auth, idempotency |
| frontend contract | routing, component boundaries, state management, responsive behavior |
| HeroUI visual contract | official HeroUI components, Pencil/Figma exports, no hand-written UI |
| engineering contract | implementation boundaries, tests, observability, deployment |
| acceptance contract | how correctness is judged, commands, screenshots, failure criteria |

## Gates

Before Pencil/Figma:

- `run_lifecycle_hook` passes for the relevant `before` stage hook.
- Fixed workspace exists under `docs/full-stack-development/requirements/<feature-slug>/`.
- `00-stage.json` exists and marks requirements approved.
- IA, interaction, state, backend/data, API, frontend, engineering, and acceptance contracts exist when applicable.
- `review_requirement_workspace_stage` passes for `targetStage: "visual-design"`.
- For React Web UI, use `hero-ui-craft`.

Before implementation:

- `run_lifecycle_hook` passes for the relevant `before` implementation-stage hook.
- Visuals are approved when UI exists.
- Visual evidence passes `review_visual_evidence`, including desktop, mobile, component-detail, state-matrix, approval record, and current change id.
- Backend/data/API contracts are approved when server work exists.
- A development flow profile is selected with `select_development_flow_profile`: `strict-fullstack`, `strict-ui`, `light-change`, or `debug-fix`.
- The implementation plan includes a Superpowers execution handoff from `plan_superpowers_execution_handoff`, covering TDD, subagent-driven or executing-plans execution, code review, verification-before-completion, and finishing branch workflow.
- `review_requirement_workspace_stage` passes for `targetStage: "implementation"`.

Before completion:

- `run_lifecycle_hook` passes for the relevant verification or completion hook.
- Tests pass.
- Build passes.
- Browser screenshots pass when UI exists.
- Accessibility checks pass when UI exists.
- API/data migration checks pass when backend/data changed.
- Acceptance contract is satisfied.

## Flow Profiles

Use a lighter profile only when its constraints are truly met; otherwise fall back to `strict-fullstack`.

| Profile | Use When | Required Gate Shape |
| --- | --- | --- |
| `strict-fullstack` | Product, UI, backend, API, data, auth, or acceptance contracts may change. | Full requirement workspace, visual evidence when UI applies, backend/API audit when applicable, code review, completion gate. |
| `strict-ui` | React Web UI, HeroUI, visual design, responsive state, or interaction behavior changes without backend/API changes. | HeroUI official context, Pencil/Figma evidence, visual inspection metrics, component graph audit, completion gate. |
| `light-change` | Small docs, copy, config, or narrowly bounded code changes that do not alter product scope, IA, UI, backend, API, data, auth, or acceptance behavior. | Change record when requirements changed, targeted verification, code review for code changes, completion gate. |
| `debug-fix` | Bug, failed test, broken build, regression, or unexpected behavior. | Root-cause evidence, failing regression test before production fix, targeted tests, fresh verification, completion gate. |

## Superpowers Execution Handoff

Implementation planning must hand off to Superpowers discipline:

- `superpowers:test-driven-development` for failing tests before production code.
- `superpowers:subagent-driven-development` for independent tasks when subagents are available.
- `superpowers:executing-plans` only as a fallback for tightly coupled tasks or unavailable subagents.
- `superpowers:requesting-code-review` after task slices and before final completion.
- `superpowers:verification-before-completion` before any pass/complete/verified claim.
- `superpowers:finishing-a-development-branch` after tests pass and integration choice is needed.

Required execution evidence: task brief, task report, review package, `.superpowers/sdd/progress.md`, final code review report, and final acceptance report.

## Lifecycle Hooks

The plugin uses internal lifecycle hooks because current plugin validation rejects a top-level `hooks` field in `.codex-plugin/plugin.json`.

Use MCP tools instead:

- `list_lifecycle_hooks`: lists registered `before` and `after` hooks for every core stage.
- `review_lifecycle_hook_coverage`: blocks missing hook coverage.
- `run_lifecycle_hook`: validates that the required gate/tool evidence exists before entering or leaving a stage.

Every core stage must have both a `before:<stage>` and `after:<stage>` hook:

- `rough-intake`
- `requirement-discovery`
- `product-scope`
- `product-spec`
- `ia-interaction-state`
- `backend-api-frontend-contract`
- `visual-requirements`
- `visual-design-ready`
- `visual-design-in-progress`
- `visual-approved`
- `implementation-plan-ready`
- `implementation-in-progress`
- `implementation-complete`
- `verification-in-progress`
- `verified`
- `released`

Hook evidence is not a substitute for the underlying gate. It is the stage-transition wrapper that proves the required gates were actually run.

## Requirement Changes

Every change after initial intake must create a change record under:

`docs/full-stack-development/requirements/<feature-slug>/changes/`

The change record must include:

- user change request
- impacted layers
- artifacts to update
- invalidated approvals
- stage regression target
- required re-verification

If a change affects product, IA, interaction, state, frontend, HeroUI, backend, data, API, engineering, or acceptance, regress to the earliest impacted stage before editing design or code.

## HeroUI Boundary

HeroUI remains the React Web UI system of record. When frontend UI is involved:

- Read and follow `hero-ui-craft`.
- Read official HeroUI React `AGENTS.md` first.
- Use `@heroui/react` official components when available.
- Do not hand-write or clone HeroUI components.
- Use Pencil/Figma before implementation.
- Use `generate_design_board_inventory` before design work and `review_visual_evidence` before implementation.
