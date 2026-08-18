---
name: hero-ui-craft
description: Use when Codex works on any front-end implementation, UI polish, dashboard, product screen, internal tool, design system, React component, Tailwind CSS v4 surface, HeroUI React v3 setup, shadcn-to-HeroUI migration, or any task that should use HeroUI. Enforces official HeroUI context, Pencil/Figma component-detail visual approval before coding, HeroUI component selection, and final visual/accessibility verification.
---

# hero-ui-craft

Use this skill as the front-end craft layer for HeroUI React v3 and Tailwind CSS v4 work.

Core principle: front-end quality starts before design. Requirements are a layered, testable contract, not one sentence.

## Non-Negotiable Gate

Do not write or edit front-end implementation code until all of these are true:

1. You inspected the target project.
2. You read the bundled official HeroUI React `references/official/react/AGENTS.md` first.
3. You synced project-local HeroUI context with `npx heroui-cli@latest agents-md --react --output AGENTS.md` when working in a target project, or explained why the target is not a React web project.
4. You used `.heroui-docs/react/`, the official `heroui-react` MCP server, or the bundled `llms-components.txt` docs to check the selected components.
5. You created or updated the fixed project requirement workspace at `docs/full-stack-development/requirements/<feature-slug>/`.
6. You wrote `00-stage.json` and kept it current. This stage file is the source of truth for whether the task is in rough intake, requirements, visual design, visual approval, implementation, or verification.
7. You completed the Requirement Pipeline inside that fixed workspace: 粗需求 -> 业务需求 -> 产品需求 -> 信息架构需求 -> 交互需求 -> 状态需求 -> 视觉需求 -> 工程需求 -> 验收需求.
8. `00-stage.json` has `approvals.requirementsApproved: true` or `currentStage: "visual-design-ready"` after user confirmation of the requirement workspace.
9. You ran `review_requirement_workspace_stage` and it passed for `targetStage: "visual-design"` before Pencil/Figma visual work.
10. You mapped every visible UI need to an official HeroUI component or documented a verified HeroUI gap.
11. You created or updated Pencil/Figma visuals before coding.
12. The visuals include full desktop, full mobile, component-detail, and state-matrix images.
13. The user approved the exported images.
14. You ran `review_requirement_workspace_stage` and it passed for `targetStage: "implementation"` before writing implementation code.

If any item is missing, stop before implementation and complete the missing step.

## Workflow

1. Inspect the project.
   - Identify framework, package manager, React version, Tailwind version, CSS entry file, and existing component library.
   - If shadcn or `@/components/ui/*` is present, treat the task as a migration boundary and avoid adding new shadcn usage.

2. Load official HeroUI context.
   - First read `references/official/react/AGENTS.md`, the official HeroUI React v3 `agents-md` output bundled with this plugin.
   - Use `references/official/react/llms.txt` as the quick index.
   - Use `references/official/react/llms-components.txt` for component selection and props.
   - Use `references/official/react/llms-patterns.txt` for recipes, composition, styling, and theming.
   - Use `references/official/react/llms-full.txt` only for deep lookup.
   - In the target project, prefer `npx heroui-cli@latest agents-md --react --output AGENTS.md` to sync project-local docs too.
   - Confirm `@heroui/react` and `@heroui/styles` are installed or plan installation.
   - Confirm CSS import order: `@import "tailwindcss";` before `@import "@heroui/styles";`.
   - Use the official HeroUI MCP server `heroui-react` to inspect component docs, props, source styles, and theme variables.

3. Create the requirement workspace before Pencil/Figma.
   - The user only needs to provide a rough goal, business context, corrections, and confirmations. Do not expect the user to already know information architecture, interaction structure, state coverage, engineering boundaries, or acceptance criteria.
   - Call `generate_requirement_workspace` from the rough request and write every returned file into `docs/full-stack-development/requirements/<feature-slug>/` in the target project.
   - Required files: `00-stage.json`, `01-rough-request.md`, `02-business-requirements.md`, `03-product-requirements.md`, `04-information-architecture.md`, `05-interaction-matrix.md`, `06-state-requirements.md`, `07-visual-requirements.md`, `08-engineering-contract.md`, `09-acceptance-contract.md`, `10-visual-confirmation-plan.md`, and `changes/0000-initial-intake.md`.
   - agent 必须起草信息架构、交互矩阵、状态需求、工程合同和验收合同；用户只负责确认、纠偏和回答聚焦问题。
   - Each Markdown file must include Agent draft, Assumptions to verify, Questions for user confirmation, and User confirmation.
   - Generated empty templates are not enough. Do not enter Pencil/Figma until the requirement workspace is drafted, user-confirmed, and `00-stage.json` marks `approvals.requirementsApproved: true` or `currentStage: "visual-design-ready"`.
   - Run `review_requirement_workspace_stage` before Pencil/Figma. If it returns `blocked`, keep drafting, asking focused questions, and updating the workspace.
   - Information architecture, interaction matrix, state requirements, engineering requirements, and acceptance requirements are requirement layers, not optional design extras.

4. Plan the UI before design work.
   - Call `plan_hero_ui_system` for screens, redesigns, dashboards, tools, or ambiguous visual direction.
   - Call `select_hero_ui_components` to map product needs to official HeroUI components.
   - If the user provides TailwindUI/Tailwind Plus local material, call `inspect_tailwind_ui_reference` and `plan_tailwind_hero_ui_adoption`; use it as reference-only and translate all implementation back to HeroUI.
   - Keep operational software dense, quiet, and scannable.

5. Produce visual confirmation before code.
   - Call `plan_visual_confirmation`.
   - Call `plan_visual_design_orchestration` before using Pencil or Figma.
   - Use Pencil or Figma.
   - With Pencil, call `get_editor_state(include_schema: true)` before other Pencil tools.
   - With Figma, load the required Figma skills before write operations.
   - Export images and ask the user to approve them before implementation.
   - Call `review_visual_design_orchestration` and `review_visual_evidence` before implementation.

6. Implement with HeroUI.
   - Import components from `@heroui/react`.
   - Official Component First: use official HeroUI components for every UI primitive and composed product surface whenever HeroUI provides one.
   - Do not hand-write UI components, style variants, or local primitives that duplicate HeroUI components.
   - Hand-written UI is allowed only when HeroUI has no official component for the need, after checking official docs/MCP, and you must document the exception with the missing component, source checked, reason, and smallest possible local scope.
   - Use HeroUI v3 component APIs and Tailwind v4 styles.
   - Do not add `HeroUIProvider` for React v3. Use `I18nProvider` only when locale setup is required.
   - Use theme variables and semantic surfaces before raw Tailwind color families.
   - Use `gap-*`, not `space-x-*` or `space-y-*`.
   - Use `size-*` when width and height are equal.
   - Use icon buttons with tooltips where the symbol is not self-explanatory.

7. Review and verify.
   - If the user changes or upgrades requirements, call `plan_requirement_change`, append the change record under `docs/full-stack-development/requirements/<feature-slug>/changes/`, update impacted requirement files, and 回退 `00-stage.json` to the earliest impacted stage.
   - Re-run `review_requirement_workspace_stage` after every requirement change.
   - Call `review_hero_ui_quality` on changed JSX/TSX/HTML/CSS.
   - Call `review_hero_ui_component_graph_audit` on changed TSX/JSX files.
   - Call `review_visual_inspection_metrics` when screenshot or image-analysis metrics exist.
   - Call `review_hero_ui_docs_freshness` before release when bundled official docs are used.
   - Call `generate_frontend_verification_checklist` before final QA.
   - Run `npx heroui-cli@latest doctor` when the HeroUI CLI can run in the target project.
   - Run the project's lint, typecheck, tests, build, and browser screenshots.

## Hard Rules

- Do not code front-end implementation before user-approved Pencil/Figma images exist.
- Do not start Pencil/Figma before the fixed requirement workspace exists and `review_requirement_workspace_stage` passes for visual design.
- Do not write implementation before `review_requirement_workspace_stage` passes for implementation.
- Do not keep requirement files only in chat or temporary output files. They must be written under `docs/full-stack-development/requirements/<feature-slug>/` in the target project.
- Do not ask the user to supply information architecture, interaction matrix, state matrix, engineering contract, or acceptance criteria from scratch. Draft them as agent-owned artifacts and ask focused confirmation questions.
- Any 需求变更 after visual design or implementation must be recorded in `changes/`, must update `00-stage.json`, and must regress the stage to the earliest impacted requirement layer before more design or code.
- Do not treat information architecture, interaction matrix, state diagrams, engineering constraints, or acceptance criteria as optional. They are requirements.
- Official Component First: Do not hand-write UI when an official HeroUI component exists.
- Do not use Base UI, Radix UI, CVA, or local variant factories to recreate Button, Card, Badge, Input, Select, Tabs, Table, Drawer, Modal, Tooltip, Popover, Form, or other official HeroUI components.
- Hand-written UI is only when HeroUI has no official component, and the implementation must document the exception.
- Do not import local shadcn components such as `@/components/ui/button`.
- Do not use `@nextui-org/react` for HeroUI v3 work.
- Do not add `HeroUIProvider` for React v3 unless official docs have changed and you verified that change.
- Do not skip HeroUI official docs/MCP checks for selected components.
- Do not copy TailwindUI/Tailwind Plus or Catalyst source into the plugin or project; use it only as local visual reference and implement with HeroUI.
- Do not let text overflow, overlap, or resize fixed-format controls.
- Do not create decorative gradient orb, bokeh, or one-note color themes.
- Do not use visible instructional text to explain basic UI controls.

## When To Read References

Read `references/hero-ui-official-workflow.md` when setting up HeroUI, migrating from shadcn, or checking official consistency.

Read `references/visual-confirmation.md` when preparing Pencil/Figma images or deciding what must be shown before user approval.

Read `references/requirements-to-visual-workflow.md` when a front-end request starts from a rough idea, screenshot, product ask, or ambiguous workflow.

Read `references/official/react/AGENTS.md` before any HeroUI React front-end implementation. It is the official generated agent index and has priority over remembered HeroUI knowledge.

## MCP Tools

- `generate_requirement_workspace`: Use to create the fixed project requirement workspace from a rough user request.
- `review_requirement_workspace_stage`: Use to block Pencil/Figma or implementation unless the fixed workspace stage passes.
- `plan_requirement_change`: Use when requirements change or upgrade; records the change, identifies impacted artifacts, and regresses the stage.
- `plan_frontend_requirement_pipeline`: Use for a high-level overview of the layered requirement contract.
- `generate_requirement_artifact_templates`: Legacy compatibility only. Do not use as the primary gate for new work; use `generate_requirement_workspace`.
- `review_frontend_requirement_contract`: Legacy compatibility only. Do not use as the primary gate for new work; use `review_requirement_workspace_stage`.
- `plan_hero_ui_system`: Use before implementing a substantial HeroUI UI surface.
- `list_hero_ui_agent_docs`: Use to see bundled official HeroUI React agent docs and their priority order.
- `get_hero_ui_agent_doc`: Use with `doc: "agents"` before implementation; use other docs only as needed.
- `select_hero_ui_components`: Use when mapping product needs to official HeroUI components.
- `plan_visual_confirmation`: Use before coding to define Pencil/Figma image requirements.
- `plan_visual_design_orchestration`: Use to plan the one-pass Pencil/Figma flow.
- `review_visual_design_orchestration`: Use to verify the visual tool flow produced complete handoff evidence.
- `inspect_tailwind_ui_reference`: Use to inspect local TailwindUI folders without copying source.
- `plan_tailwind_hero_ui_adoption`: Use to map TailwindUI references back to HeroUI and Tailwind v4 rules.
- `review_hero_ui_quality`: Use after editing UI code or before final review.
- `review_hero_ui_component_graph_audit`: Use to audit official HeroUI imports and local shadow components.
- `review_visual_inspection_metrics`: Use to block blank, high-diff, overlapping, clipped, or contrast-broken screenshots.
- `review_hero_ui_docs_freshness`: Use to verify bundled HeroUI official docs are fresh and complete.
- `generate_frontend_verification_checklist`: Use before final verification.

The local tools are read-only and deterministic. The plugin also exposes the official `heroui-react` MCP server for current component documentation and source inspection.
