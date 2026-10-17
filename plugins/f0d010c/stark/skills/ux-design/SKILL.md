---
name: ux-design
description: Use when the user asks for UX, product flow, user journey, wireframes, usability, conversion, onboarding, checkout, signup, navigation, forms, state design, dashboard workflows, command palettes, settings, permissions, long-running task progress, admin/internal tools, activation, retention, or making an app easier to use over time. Designs and audits user experience flows, information architecture, content hierarchy, forms, onboarding, dashboards, settings, empty/loading/error/permission/success states, recovery paths, and repeated-use product ergonomics before visual polish. Pair with platform UI skills after the UX flow is clear.
---

# ux-design - product flow before pixels

Use this skill when the product has to be understandable and usable, not just attractive. The output should make the user path clearer, reduce unnecessary decisions, and define states that survive real use.

## What This Skill Can Do

- Map core user journeys, task paths, branching flows, and recovery paths.
- Define information architecture, navigation, labels, content groups, and page/screen inventory.
- Design onboarding, activation, checkout, signup, forms, settings, dashboards, command palettes, and internal workflows.
- Specify empty, loading, error, permission, success, stale, retry, resume, and audit states.
- Define task ergonomics: frequency, risk, cognitive load, control model, speed paths, error prevention, recovery, and evidence tasks.
- Choose usable workflow patterns: guided setup, wizard with review, command surface, priority queue, master/detail, monitoring board, workbench, settings, permission matrix, transparent checkout, task-led docs, agent progress, collaboration thread, and mobile priority stack.
- Evaluate polished UI with heuristic review, cognitive walkthrough prompts, severity ranking, evidence, first repair, and re-check.
- Validate usability with scenario tests for first-run, returning-user, error/recovery, keyboard-only, and mobile/touch paths.
- Audit an existing UI for usability, hierarchy, conversion, repeated-use friction, accessibility risks, and missing states.
- Hand a compact UX decision brief to platform skills so visual design does not erase the product job.

## Step 1 - Identify the job and user mode

Before designing screens, state the smallest useful context:

- Primary job: what the user is trying to finish.
- User mode: first-time, returning, power user, admin, buyer, creator, operator, or support.
- Frequency: one-time, occasional, daily, or high-volume repeated use.
- Risk: low-risk browse, reversible edit, money/data/security impact, or destructive action.

If any of these are unclear and materially affect the flow, ask one short question. If the answer is easy to infer from the request, infer it and continue.

Do not interrogate the user with a product-strategy questionnaire before helping. The skill should make useful assumptions, name them briefly, and move.

## Step 2 - Map the flow

Write the minimum useful path:

1. Entry point
2. First meaningful action
3. Required decision
4. Feedback after action
5. Success state
6. Recovery path when something fails

Prefer fewer screens when the user is trying to finish one job. Prefer separate steps when the user is making risky, costly, or hard-to-reverse decisions.

## Step 2.5 - Produce the UX decision brief

Before visual design or code, write a compact brief. Keep it short enough to pass into another skill:

```md
UX decision brief
- Job: ...
- User mode: ...
- Frequency/risk: ...
- Pattern: ...
- Primary action: ...
- Secondary actions: ...
- Core path: entry -> action -> feedback -> success
- Recovery path: ...
- Required states: empty, loading, partial, error, permission, success, long-running
- Handoff constraints: ...
```

This brief is the contract. The platform skill may change visual treatment, but it must not erase the chosen job, action hierarchy, state coverage, or recovery path.

## Step 2.6 - Produce the task ergonomics contract

For serious product UI, repeated-use workflows, risky actions, forms, checkout, dashboards, editors, agent runs, admin tools, settings, or any request that says "usable", "ergonomic", "not only good looking", or "real product", read `../../references/ux-patterns/task-ergonomics.md`.

Write the compact contract before visual design:

```md
Task ergonomics contract
- Core task:
- User mode:
- Frequency/risk:
- Success metric:
- Cognitive load:
- Control model:
- Speed path:
- Error prevention:
- Recovery:
- State matrix:
- Evidence plan:
```

This is stricter than the UX decision brief. It protects the tenth use, the error path, and the risky action path.

For forms, settings, checkout, onboarding, signup, admin configuration, filters, generation prompts, or any user input that can fail, also read `../../references/ui-patterns/form-state-validation-system.md` before visual design or implementation. Add the form job, risk, pattern, field anatomy, validation timing, state model, preservation/recovery, review/confirmation, schema/library ownership, accessibility, responsive behavior, and QA checks to the UX handoff.

For onboarding, activation, empty dashboards, no-results screens, setup/import flows, permission gates, trial starts, workspace creation, or first project creation, read `../../references/ux-patterns/first-run-empty-state-system.md` before visual design. Define user promise, first value action, minimum/deferrable setup, sample/demo content, empty-state type, CTAs, permission timing, progress/resume model, recovery states, contextual teaching, success handoff, and QA evidence.

For navigation, information architecture, app shells, docs platforms, dashboards, admin/settings, workspaces, command palettes, breadcrumbs, tabs, or multi-route products, also read `../../references/ui-patterns/navigation-information-architecture.md` before visual design or implementation. Add the primary objects, route map, navigation model, current-location model, search/command model, breadcrumb/tab behavior, deep-link/state model, route states, mobile replacement, focus/scroll restoration, and QA checks to the UX handoff.

## Step 3 - Design the states

Every production UI needs these states:

- Empty: what the user sees before data exists.
- Loading: what changes while the system is working.
- Partial: some data exists, some is missing.
- Error: what failed, why it matters, and the next action.
- Permission: what is blocked and how to request access.
- Success: what happened and what the user can do next.
- Long-running: progress, cancellation, retry, and resume behavior.

Do not ship only the happy path.

For public demos and generated proof projects, include at least one non-happy state in the visible UI: an empty state, blocked permission, failed sync, queued job, retry panel, stale data banner, or partial result. This makes the output feel like a real product instead of a polished poster.

## Step 3.5 - Choose the usability pattern

For serious product UI or any request that says "usable", "not only good looking", "real product", "ergonomic", "dashboard", "editor", "checkout", "agent run", "settings", "permissions", "docs", or "mobile task", read `../../references/ux-patterns/usability-pattern-matrix.md` after `task-ergonomics.md`.

Write the compact pattern brief before visual design:

```md
Usability pattern brief
- Product job:
- User mode:
- Frequency/risk:
- Pattern chosen:
- Why this pattern fits:
- Primary action:
- Secondary actions:
- Speed path:
- Error prevention:
- Recovery path:
- Required states:
- Keyboard/touch model:
- Rejected patterns:
- Evidence tasks:
```

The selected pattern should reduce the riskiest failure mode. Reject patterns that optimize the wrong use, such as a marketing hero for repeated operations, a wizard for high-volume triage, a grid of cards for comparison, or a dashboard for a single linear task.

## Step 3.6 - Define usability scenario tests

For serious product UI, "not only good looking" work, UX audits, risky/repeated workflows, attractive-but-confusing UI, or final QA, read `../../references/ux-patterns/usability-heuristic-evaluation.md` after the usability pattern matrix and before scenario testing. Rank findings with severity, name evidence, choose the first repair, and re-check the same task step.

Then read `../../references/ux-patterns/usability-scenario-testing.md` after the heuristic evaluation.

Write the compact scenario test before final visual polish or delivery:

```md
Usability scenario test
- Surface:
- User persona/mode:
- Core task:
- First-run scenario:
- Returning-user scenario:
- Error/recovery scenario:
- Keyboard-only scenario:
- Mobile/touch scenario:
- Success criteria:
- Friction budget:
- Evidence captured:
- Usability failures:
- Fix applied:
- Re-check:
- Remaining risk:
```

The scenario test is the proof layer. A screen is not "usable" just because the task ergonomics contract sounds good; the main task, recovery path, keyboard path, and mobile path need evidence or clearly named remaining risk.

## Step 4 - Reduce cognitive load

Apply these rules:

- Put the next action where the user's eye already is.
- Use one primary action per surface.
- Group by task, not by database object.
- Prefer progressive disclosure over dense first screens.
- Keep labels concrete: "Invite teammate", not "Manage".
- Make defaults safe and visible.
- Keep destructive actions separated, confirmed, and undoable when possible.
- Make repeated actions faster than first-time actions.

For high-frequency tools, optimize scan speed, keyboard flow, saved filters, bulk actions, and stable layout. For consumer onboarding, optimize motivation, trust, and the shortest path to first value.

## Step 4.5 - Match the product type

Use the product type to decide what "good UX" means:

| Product type | Optimize for | Avoid |
|---|---|---|
| SaaS dashboard | fast scanning, saved filters, drilldowns, clear priority, visible operational thesis | marketing-page spacing, decorative cards, hidden filters, generic CRM furniture |
| CRM/admin/internal tool | repeat speed, bulk actions, auditability, permissions, domain-specific task language | oversized empty space, playful copy, modal chains, interchangeable labels |
| Creative/editor tool | canvas focus, tool discoverability, undo/redo, stable panels | layout shifts, buried controls, destructive defaults |
| Marketplace/ecommerce | trust, comparison, price/shipping clarity, recovery | surprise costs, forced account creation, vague stock states |
| Onboarding/setup | first value, motivation, resumability, skip paths | long forms before value, fake progress, no return path |
| AI agent/tool run | plan preview, progress, artifacts, retry, stop/resume | invisible work, ambiguous completion, no trace of outputs |

If the request sounds like a real product people will use repeatedly, bias toward operational density and predictable navigation. If it is a one-off marketing page, bias toward clarity, brand memory, and conversion path.

## Step 4.6 - Load a contextual pattern brief

If the product type clearly matches one of these contexts, read the matching brief before choosing the final UX pattern:

| Context | Read |
|---|---|
| Any serious product surface, repeated workflow, risky action, form, checkout, dashboard, editor, agent run, or usability audit | `../../references/ux-patterns/task-ergonomics.md` |
| Workflow structure, usability pattern choice, repeated/risky/stateful product work, or "not only good looking" | `../../references/ux-patterns/usability-pattern-matrix.md` |
| Onboarding, activation, empty dashboards, no-results, setup/import, permission gates, trials, workspace/project creation | `../../references/ux-patterns/first-run-empty-state-system.md` |
| Heuristic review, cognitive walkthrough, severity triage, attractive-but-confusing UI, or polished surfaces that may still fail the task | `../../references/ux-patterns/usability-heuristic-evaluation.md` |
| Scenario validation, final usability QA, keyboard/mobile/error path proof, or "is this actually usable?" | `../../references/ux-patterns/usability-scenario-testing.md` |
| Navigation, information architecture, app shell, docs, dashboards, settings, workspaces, command/search, breadcrumbs, or tabs | `../../references/ui-patterns/navigation-information-architecture.md` |
| Agent/tool run, background automation, long-running export/import | `../../references/ux-patterns/ai-agent-run.md` |
| SaaS dashboard, CRM, admin panel, internal tool, support queue | `../../references/ux-patterns/operational-dashboard.md` |
| First-run setup, trial activation, import/setup flow | `../../references/ux-patterns/activation-onboarding.md` + `../../references/ux-patterns/first-run-empty-state-system.md` |
| Checkout, paywall, pricing, upgrade, plan comparison | `../../references/ux-patterns/checkout-upgrade.md` |
| Editor, builder, canvas, creative tool, IDE-like surface | `../../references/ux-patterns/editor-canvas.md` |

Use a brief only when the context fits. If no brief fits, proceed from the product type table and the user's actual constraints.

The brief should influence the UX decision brief, especially:

- Pattern
- Primary and secondary actions
- Required states
- Recovery path
- Frequency/risk treatment
- Speed path
- Error prevention
- Evidence tasks
- Scenario tests
- Handoff constraints

Do not copy a referenced app or blindly apply a pattern because it is common. A shipped screen is evidence that a real product team used a decision, not proof that it is best for every product.

## Step 5 - Choose the UX pattern

Pick one pattern and name it before visual design:

| Need | Pattern |
|---|---|
| First run | Guided setup with skip/resume |
| Complex creation | Wizard with review step |
| Frequent operations | Command surface + saved views |
| Data-heavy work | Master/detail + filters + bulk actions |
| Monitoring | Dashboard with priority stack and drilldown |
| Settings | Searchable grouped settings + inline validation |
| Checkout/signup | Short form + transparent cost/risk + recovery |
| Collaboration | Activity timeline + comments + ownership |
| AI/tool execution | Plan preview + progress + artifacts + retry |
| Public demo/proof project | Product-specific job + proof surface + one non-happy state |

If two patterns fit, pick the one that reduces the riskiest failure mode. For example, choose a wizard over a single dense form when errors are costly, but choose command surface + saved views for repeated internal operations.

## Step 6 - Hand off to UI

After the UX shape is clear, route to the platform skill:

- Web visuals: `../web-design/SKILL.md`
- Windows visuals: `../windows-design/SKILL.md`
- Apple visuals: `../apple-design/SKILL.md`
- Android visuals: `../android-design/SKILL.md`
- Cross-platform translation: `../cross-platform-design/SKILL.md`

Pass the UX decisions into that skill as constraints. Do not let visual direction erase task flow, state coverage, or platform idioms.

When a contextual pattern brief was used, include its name in the handoff constraints so the platform skill knows which product behavior must survive visual design.

## UX audit checklist

Before final delivery, check:

1. Is the primary job obvious in the first screen?
2. Can a new user reach first value without reading documentation?
3. Can a returning user repeat the core task faster?
4. Are empty, loading, error, permission, and success states defined?
5. Is there one clear primary action per surface?
6. Are risky actions confirmed, separated, or undoable?
7. Do form errors appear near the fields they describe?
8. Does the layout support scanning, not just looking good in a screenshot?
9. Does navigation match the user's mental model?
10. Is the next step clear after every action?
11. Does the repeated path get faster after first use?
12. Are focus, touch targets, and keyboard paths usable for the selected surface?
13. Are validation and recovery close to the user's input/action and is user input preserved?
14. Is friction applied only where risk justifies it?

If any answer is no, fix the flow before polishing visuals.
