---
name: dev-image-to-code
description: >
  UI image to code methodology. Use when the user provides a UI screenshot,
  design mock, app screen, dashboard image, mobile screen, web page image, or
  says "UI图生成代码", "看图写页面", "根据设计图实现", "screenshot to code",
  "image to code", or asks Codex to implement a frontend from an image. Requires
  a UI image plus a design size when available, forces clarification for every
  uncertainty, then reconstructs the UI in the target project or a runnable
  standalone app with browser screenshot verification and visual diff evidence.
---

# Dev Image To Code

Turn a UI image into runnable code without guessing past the evidence. Treat the
image as the visual truth, the design size as the coordinate system, and the
browser screenshot as the acceptance gate.

## Iron Rule

The UI image is the visual source of truth. The design size is the coordinate
system. Any layout, copy, component meaning, interaction, responsive behavior, or
implementation choice that cannot be confirmed from the image, the project, or
the user is `GUESS`; stop and ask the user before implementing it.

Do not "make it nicer" while reconstructing. First match the image, then improve
only when the user asks.

## Interaction Rule

Do not turn visible controls into inert boxes. When the image clearly shows a
known UI control, preserve its component semantics even in a standalone
prototype:

- Buttons must be real buttons or project button components.
- Inputs, textareas, selects, date pickers, checkboxes, switches, and radios
  must be real form controls or project form components.
- Tabs, segmented controls, accordions, menus, dropdowns, dialogs, pagination,
  tables, and steppers must be modeled as interactive/stateful components.
- Visible states such as active, selected, disabled, expanded, checked, focused,
  loading, and error must be recorded and implemented when evidenced.

Separate `component semantics` from `hidden behavior`: a screenshot may prove
"this is a tab control" without proving what the other tab panels contain. Build
the proven control semantics, then ask before inventing hidden panels, backend
actions, data options, routes, or workflow effects.

## Required Inputs

- UI image: required.
- Design size: required when the user knows it, for example `1440x900`,
  `375x812`, or `1193x774`.

If the user provides only an image, ask for the design size first. If the user
says they do not have it, run `scripts/image-metadata.mjs` or inspect the image
metadata and use the image pixel size as the fallback design size. Record the
source as `user-provided` or `inferred-from-image-pixels`.

Read `references/input-contract.md` for exact intake rules and clarification
examples.

## Workflow

### Step 0: Create The Evidence Folder

For each reconstruction task, create or reuse a small evidence folder near the
work being changed, for example `UI_RECON/<screen-name>/` or
`RECON/dev-image-to-code/<screen-name>/`. Keep this lightweight in existing repos.

Expected files:

- `UI_RECON.md`: image facts, design size, evidence grades, user confirmations.
- `design-tokens.json`: colors, typography, spacing, radius, shadows, motion.
- `component-map.md`: visual element to code/component mapping.
- `screenshots/`: source image, implementation screenshot, optional diff image.
- `VISUAL_REPORT.md`: final comparison, scores, gaps, verification commands.

Read `references/visual-verification.md` for deliverable templates.

### Step 1: Inspect The Project Before Coding

If inside an existing project, inspect the real stack before choosing an
implementation:

- Project instructions such as `AGENTS.md`, `CLAUDE.md`, `.design-context.md`.
- Package files and framework entry points.
- Existing theme variables, design tokens, rem rules, breakpoints, icon sets.
- Existing reusable components and nearby pages with the same visual language.

Prefer the project design system and component library. Only create new styling
primitives when the project has no usable local pattern.

### Step 2: Analyze The Image Before Coding

Produce a structured image analysis before editing production code:

- Screen type: marketing page, dashboard, form, table, modal, mobile app, etc.
- Layout: root frame, grid, sections, alignment, scroll assumptions.
- Component tree: navigation, cards, buttons, inputs, tables, tabs, charts.
- Text inventory: visible copy, uncertain OCR, truncation, label hierarchy.
- Visual tokens: color, typography, spacing, radius, borders, shadows.
- Assets: photos, illustrations, icons, logos, maps, charts, empty states.
- States and interactions: selected, disabled, hover, expanded, error, loading.
- Interactive controls: classify every visible control as `semantic`,
  `decorative`, or `unclear`; `unclear` controls require a question before
  implementation.
- Evidence grade for each important conclusion: `SOURCE`, `PARTIAL`, or `GUESS`.

Read `references/image-analysis.md` for the analysis schema and question policy.

### Step 2.5: Clarify Every Uncertainty

If anything material is unclear, ask the user and wait. Ask short, concrete
questions. Do not hide uncertainty in implementation.

Examples:

- "The top-right icon could be notification or settings. Which is it?"
- "Is this area a real data table or a static summary list?"
- "Should the page be responsive beyond the provided `1440x900` design?"
- "I cannot read the small label under the chart. What should it say?"

### Step 3: Choose The Implementation Path

Use this decision tree:

| Input and context | Path |
|---|---|
| Existing app with matching component library | Reuse local components and theme first |
| Existing app without matching components | Build scoped components in the local style |
| Standalone web screen | Generate minimal runnable HTML/CSS/JS or requested framework |
| React/Vue/Next screen | Use the existing framework and routing conventions |
| Flutter screen | Use existing widgets/theme and verify with Flutter tests/screenshots when available |
| Mobile screenshot | Preserve the design width, define viewport scaling, keep touch targets usable |
| SaaS/admin/table/form UI | Preserve data semantics, component states, density, and scanability |
| Multi-image or multi-state UI | Build shared components first, then states/routes |
| Chart/map/canvas/3D-heavy UI | Ask for data and interaction semantics before coding; static approximation must be explicit |

Read `references/implementation-paths.md` for path details and boundaries.

### Step 4: Implement From Evidence

Use the design size as the coordinate baseline. Convert exact pixel facts into
project-appropriate units only after understanding the repo's scaling system.

Implementation discipline:

- Keep changes scoped to the requested screen or component.
- Preserve existing wrappers, state management, i18n, theme, routing, and tests.
- Use real text from the image or user confirmation. Mark unreadable text until
  confirmed.
- Use familiar icons from the project icon set when the icon meaning is known.
- Implement clear controls with real semantic components, not static `div`
  lookalikes. For tabs/selects/inputs/buttons, keep focus, keyboard, active, and
  disabled states available through the native element or project component.
- Avoid decorative additions that are not present in the source image.
- Do not invent backend behavior, permissions, search, payments, or data APIs
  from a static image.

### Step 5: Verify In A Real Renderer

Run the smallest meaningful project verification, then render the UI at the
design size:

- Start the app or open the standalone page.
- Capture a screenshot at the design width and height.
- Check console/runtime errors.
- Check text overflow, clipping, overlap, missing assets, and broken states.
- Smoke-test visible interactions that were implemented, such as focusing
  inputs, opening/selecting dropdowns, switching tabs, expanding accordions, and
  pressing visible buttons with mocked/no-op handlers where backend behavior is
  unknown.
- Compare the implementation screenshot against the source image.

Use `scripts/screenshot-page.mjs` and `scripts/visual-diff.mjs` when a web page
can be rendered in Playwright. Use platform-specific verification for Flutter or
native targets when browser rendering is not relevant.

### Step 6: Score And Iterate

Score only what evidence supports:

- Structure fidelity.
- Visual fidelity.
- Text fidelity.
- Component semantics.
- Interaction/state fidelity.
- Responsive behavior.
- Project consistency.
- Maintainability.

If verification finds visible drift, iterate until the remaining gaps are either
fixed, explicitly accepted by the user, or documented as impossible with current
inputs.

## Evidence Grades

- `SOURCE`: clear in the image, measured from metadata/screenshot, confirmed by
  source code, or confirmed by the user.
- `PARTIAL`: likely, but one piece of evidence is missing or ambiguous.
- `GUESS`: plausible visual inference only. Do not implement material `GUESS`
  items without asking the user.

## Capability Boundaries

Can do well:

- Pixel-oriented reconstruction of a single visible screen.
- Existing-app implementation using local components and design tokens.
- Standalone web prototypes from a clear UI image.
- Admin, SaaS, form, table, card, modal, empty-state, and mobile screens.

Can approximate with explicit limits:

- Charts without data definitions.
- Maps without provider or layer details.
- Icons and fonts that cannot be identified.
- Responsive layouts from one breakpoint.
- Complex animations from a static image.

Do not promise from one static image:

- Real backend logic, permissions, payments, search, recommendation, or workflow
  rules.
- Hidden screens, complete design systems, or all responsive breakpoints.
- Canvas/WebGL/3D internals without interaction and data evidence.

## Bundled Resources

- `scripts/image-metadata.mjs`: Read image dimensions for the design-size
  fallback.
- `scripts/screenshot-page.mjs`: Capture a browser screenshot at a design size.
- `scripts/visual-diff.mjs`: Compare two images in a browser canvas and write a
  diff report.
- `scripts/interaction-smoke.mjs`: Run focus/click/select smoke checks for
  semantic controls and write a JSON report.
- `references/input-contract.md`: Intake and clarification protocol.
- `references/image-analysis.md`: UI analysis schema and evidence grading.
- `references/implementation-paths.md`: Framework and target decision tree.
- `references/visual-verification.md`: Deliverable templates and scoring.
