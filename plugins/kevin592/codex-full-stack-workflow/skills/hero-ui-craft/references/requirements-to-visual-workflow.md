# Requirements To Visual Workflow

Use this reference when a front-end request starts as a rough idea, product ask, screenshot, dashboard request, redesign request, or ambiguous workflow.

## Principle

用户通常只能说清楚“大概要什么功能”。用户不应该被要求先给出信息架构、交互矩阵、状态图、工程拆分或验收标准。

Agent owns requirement clarification. The agent drafts the requirement workspace, marks assumptions, asks focused questions, records confirmations, and keeps the current stage explicit.

Information architecture, interaction matrix, state requirements, engineering constraints, and acceptance criteria are requirement layers. They are not optional outputs after design.

## Fixed Project Workspace

All requirement artifacts must be written into the target project under:

`docs/full-stack-development/requirements/<feature-slug>/`

Required files:

| File | Layer | Required Output |
| --- | --- | --- |
| `00-stage.json` | Stage source of truth | Current stage, next allowed stage, approvals, blocked gates, change policy |
| `01-rough-request.md` | 粗需求 | Raw user ask, agent interpretation, scope, unknowns, confirmation log |
| `02-business-requirements.md` | 业务需求 | Why this matters, success metrics, business rules, risks, priority |
| `03-product-requirements.md` | 产品需求 | Roles, tasks, primary workflow, feature scope, non-goals |
| `04-information-architecture.md` | 信息架构需求 | Information objects, hierarchy, navigation, data fields, content priority |
| `05-interaction-matrix.md` | 交互需求 | Trigger, actor, component, system response, feedback, permission, keyboard behavior |
| `06-state-requirements.md` | 状态需求 | Empty, loading, error, exception, editing, success, disabled, mobile states |
| `07-visual-requirements.md` | 视觉需求 | Density, layout principles, component style, semantic color, forbidden visual taste |
| `08-engineering-contract.md` | 工程需求 | HeroUI context, Official Component First, component mapping, data model, responsive rules, exception log |
| `09-acceptance-contract.md` | 验收需求 | How to judge correctness, functional checks, visual checks, HeroUI compliance, screenshot checks |
| `10-visual-confirmation-plan.md` | 视觉确认 | Pencil/Figma desktop, mobile, component detail, state matrix, approval record |
| `changes/0000-initial-intake.md` | Change log | Initial request record |

Each Markdown requirement file must include:

- Agent draft
- Assumptions to verify
- Questions for user confirmation
- User confirmation

## Stage Model

`00-stage.json` is mandatory. Use it to know where the work is:

| Stage | Meaning | Next Gate |
| --- | --- | --- |
| `rough-intake` | Rough request captured; agent is drafting requirements | requirements |
| `requirements-drafting` | Some requirement artifacts are missing or not confirmed | requirements |
| `visual-design-ready` | `00` through `09` exist and may enter Pencil/Figma | visual-design |
| `visual-awaiting-approval` | Visual plan exists, but exported images are not approved | visual-approval |
| `implementation-ready` | Visual images are approved and implementation may start | implementation |
| `verification` | Code exists and is being validated against acceptance | completion |

## Gates

Before Pencil/Figma:

- Files `00-stage.json` through `09-acceptance-contract.md` must exist in the fixed workspace.
- Generated empty templates are not enough.
- `00-stage.json` must mark `approvals.requirementsApproved: true` or `currentStage: "visual-design-ready"` after user confirmation of the requirement workspace.
- `review_requirement_workspace_stage` must return `pass` for `targetStage: "visual-design"`.
- Loose files in chat, outputs, or another docs directory do not satisfy the gate.

Before implementation:

- `10-visual-confirmation-plan.md` must exist.
- Pencil/Figma exports must include desktop full-screen image, mobile full-screen image, component detail image, and state matrix image.
- User approval must be recorded.
- `review_requirement_workspace_stage` must return `pass` for `targetStage: "implementation"`.

## Requirement Changes

When the user changes or upgrades the requirement:

1. Call `plan_requirement_change`.
2. Append a change file under `docs/full-stack-development/requirements/<feature-slug>/changes/`.
3. Update impacted requirement files.
4. Update `00-stage.json`.
5. Regress the stage to the earliest impacted requirement layer.
6. Re-run `review_requirement_workspace_stage`.
7. Re-export Pencil/Figma visuals if the change affects product, IA, interaction, state, visual, or engineering requirements.
8. Treat previous implementation as stale when the change lands after code has started.

## HeroUI Contract

`08-engineering-contract.md` must include:

- Official HeroUI React `AGENTS.md` is the first source of truth.
- Component docs come from `.heroui-docs/react/` or `@heroui/react-mcp@latest`.
- Official Component First: use `@heroui/react` whenever HeroUI provides the component.
- No hand-written UI: Base UI, Radix UI, CVA, local `components/ui`, local variant factories, and shadcn-style clones are blocked when HeroUI has an official component.
- Exception log: only when HeroUI has no official component. Record the official source checked, missing capability, smallest local implementation scope, and verification.
- CSS import order: `@import "tailwindcss";` before `@import "@heroui/styles";`.

No implementation may start until fixed workspace requirements, visual exports, and user approval all pass.
