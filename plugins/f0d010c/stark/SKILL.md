---
name: stark
description: Use for UI/UX design, product flows, frontend or native interface design, design audits, design translation, asset planning, motion direction, design tokens, or distinctive non-generic apps and websites. Covers web and React, Windows and WinUI/Mica, Apple and SwiftUI, Android and Jetpack Compose/Material, cross-platform UI, and token export. Route to the focused skill, then load only the references required for the selected surface and failure mode.
---

# Stark

Stark is a design router for AI coding agents. Use it to make product, platform, visual, interaction, and quality decisions before implementation.

## Operating rule

Keep context proportional to the task:

1. Select no more than two routed skills.
2. Load two core references for the selected surface.
3. Add at most two conditional references for a specific risk or failure mode.
4. Load post-render gates only after rendered evidence exists.

Do not read the entire reference library. Use `references/ui-patterns/README.md`, `references/ux-patterns/README.md`, and `references/web-patterns/README.md` as catalogs when the tables below do not cover the request.

## Route the request

| Request | Routed skill |
|---|---|
| Web UI, landing page, dashboard, React, Next, Astro, Tailwind | `skills/web-design/SKILL.md` |
| Product flow, onboarding, checkout, IA, usability, forms | `skills/ux-design/SKILL.md` |
| Windows, WinUI, WPF, Fluent | `skills/windows-design/SKILL.md` |
| Apple, iOS, iPadOS, macOS, SwiftUI | `skills/apple-design/SKILL.md` |
| Android, Material, Jetpack Compose | `skills/android-design/SKILL.md` |
| Tauri, Electron, React Native, Flutter, CMP, shared UI | `skills/cross-platform-design/SKILL.md` |
| Design tokens, themes, token export | `skills/design-tokens/SKILL.md` |
| Platform is genuinely unclear | `skills/design-router/SKILL.md` |

Combine UX with one platform skill when the request includes both workflow and implementation. Preserve the UX brief when platform guidance is applied.

Use `scripts/detect_platform.py` only as a deterministic fallback. Treat `ambiguous` as a request for one short clarification, not permission to default to web.

## Select a reference bundle

Choose one primary bundle. Read its two core references. Add conditional references only when their trigger is present.

### Product application

Core:

- `references/ux-patterns/task-ergonomics.md`
- `references/ui-patterns/interaction-state-matrix.md`

Conditional:

- Responsive or multi-viewport: `references/ui-patterns/responsive-adaptation-gate.md`
- Complex navigation: `references/ui-patterns/navigation-information-architecture.md`
- Direct manipulation: `references/ui-patterns/interaction-physics-direct-manipulation.md`
- Reusable components: `references/ui-patterns/component-api-variant-contract.md`

### Landing page or product proof

Core:

- `references/ui-patterns/creative-direction.md`
- `references/ui-patterns/page-proof-architecture.md`

Conditional:

- Conversion or pricing: `references/ui-patterns/conversion-proof-system.md`
- Distinct identity: `references/ui-patterns/brand-identity-motif-system.md`
- Product media: `references/ui-patterns/asset-realism-matrix.md`
- Cinematic surface: `references/ui-patterns/cinematic-landing-system.md`

### Animation-led surface

Core:

- `references/ui-patterns/animation-creation.md`
- `references/ui-patterns/choreography-state-machine.md`

Conditional:

- Library selection: `references/ui-patterns/motion-library-playbooks.md`
- Authored timelines or Rive/Lottie: `references/ui-patterns/designer-authored-motion-handoff.md`
- Heavy runtime: `references/ui-patterns/performance-budget-contract.md`
- Acceptance frames: `references/ui-patterns/motion-frame-qa-contract.md`

### Dashboard or analytics

Core:

- `references/ui-patterns/dashboard-insight-hierarchy.md`
- `references/ui-patterns/data-visualization-library-selection.md`

Conditional:

- Realistic fixtures: `references/ui-patterns/product-data-content-system.md`
- Dense repeated work: `references/ux-patterns/task-ergonomics.md`
- Responsive replacement: `references/ui-patterns/adaptive-composition-system.md`
- Data states: `references/ui-patterns/interaction-state-matrix.md`

### Design system or reusable library

Core:

- `references/ui-patterns/design-system-production-loop.md`
- `references/ui-patterns/token-implementation-contract.md`

Conditional:

- Public component API: `references/ui-patterns/component-api-variant-contract.md`
- State coverage: `references/ui-patterns/component-state-gallery.md`
- Theme and density: `references/ui-patterns/theme-mode-density-system.md`
- Automation: `references/ui-patterns/frontend-quality-automation-gate.md`

### Audit or repair

Core:

- `references/ui-patterns/ui-audit-rubric.md`
- `references/ui-patterns/visual-repair-playbook.md`

Conditional:

- Usability concern: `references/ux-patterns/usability-heuristic-evaluation.md`
- Accessibility concern: `references/ui-patterns/accessibility-acceptance-gate.md`
- Generic or repetitive output: `references/ui-patterns/design-fingerprint-diversity-gate.md`
- Implementation drift: `references/ui-patterns/implementation-review-loop.md`

### Research or reference-led work

Core:

- `references/ui-patterns/reference-board-workflow.md`
- `references/ui-patterns/research-synthesis-contract.md`

Conditional:

- Compare against a stronger example: `references/ui-patterns/benchmark-repair-loop.md`
- Avoid copying identity: `references/ui-patterns/reference-analysis.md`

### First-run or risky flow

Core:

- `references/ux-patterns/first-run-empty-state-system.md`
- `references/ux-patterns/task-flow-acceptance-harness.md`

Conditional:

- Forms and validation: `references/ui-patterns/form-state-validation-system.md`
- Checkout or trust: `references/ui-patterns/conversion-proof-system.md`
- Permissions and accessibility: `references/ui-patterns/accessibility-interaction-contract.md`

## Produce a compact decision brief

Before code, state:

- product job and primary user;
- target platform and implementation track;
- primary object and action;
- selected structural pattern;
- visual direction and one product-specific motif;
- required states and recovery path;
- responsive or native adaptation;
- motion level and library owner, if any;
- selected references and why they apply;
- acceptance evidence.

Keep this brief actionable. Do not turn it into a design essay.

## Implement and validate in stages

1. Define the product object, primary action, states, and recovery.
2. Choose platform idiom and structural pattern.
3. Choose typography, material, assets, and motion according to the surface.
4. Implement in the user's existing stack unless a change is explicitly requested.
5. Inspect the rendered result.
6. Load only the relevant post-render gate:
   - visual: `references/ui-patterns/rendered-quality-gate.md`
   - usability: `references/ux-patterns/rendered-usability-acceptance-gate.md`
   - typography: `references/ui-patterns/rendered-typography-quality-gate.md`
   - advanced libraries: `references/ui-patterns/capability-stack-rendered-gate.md`
7. Apply the highest-impact repair and re-check the failed evidence.

## Commands

Use command briefs when the user explicitly asks for one of these modes:

| Mode | Command |
|---|---|
| General design | `commands/stark.md` |
| Audit | `commands/stark-audit.md` |
| Full design direction | `commands/stark-director.md` |
| Quality scoring | `commands/stark-quality.md` |
| Browser/runtime QA | `commands/stark-qa.md` |
| Release-quality gate | `commands/stark-quality-gate.md` |
| Usability | `commands/stark-usability.md` |
| Animation | `commands/stark-animation.md` |
| Assets | `commands/stark-assets.md` |
| Reference research | `commands/stark-reference-board.md` |
| Second attempt | `commands/stark-regenerate.md` |
| Design translation | `commands/stark-translate.md` |
| Dogfood evaluation | `commands/stark-dogfood.md` |

## Helper scripts

- Use `scripts/detect_platform.py` only when semantic platform routing remains ambiguous.
- Use `scripts/token_export.py` when converting Stark token bundles to CSS, Tailwind, SwiftUI, Compose, or WinUI.
- Maintainers use `scripts/validate_repository.py` and `scripts/build_package.py`; they are not part of normal design execution.

## Guardrails

- Prefer product-specific structure over generic cards, gradients, and slogans.
- Do not force expressive landing-page composition onto repeated-use tools.
- Preserve keyboard, focus, semantics, reflow, reduced motion, and recovery paths.
- Treat advanced libraries as dependencies with an owner, fallback, budget, QA probe, and removal rule.
- Borrow principles from references, never trade dress, proprietary assets, or copied layouts.
- Do not claim rendered quality without rendered evidence.
- Keep the user's framework and conventions unless the request clearly authorizes a change.
