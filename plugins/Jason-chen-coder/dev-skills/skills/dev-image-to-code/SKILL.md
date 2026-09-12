---
name: dev-image-to-code
description: >
  Implement a frontend from a UI screenshot or design image in an existing
  project or a runnable standalone page. Use for "UI图生成代码", "看图写页面",
  "根据设计图实现", "screenshot to code", or "image to code" requests.
  Preserve visual fidelity and working control semantics, then verify in a
  real renderer. Not for redesigns without a reference image.
---

# Dev Image To Code

Use the image as the visual source of truth, the design size as the coordinate
baseline, and a rendered screenshot as verification evidence. Match the supplied
design before adding any user-requested improvements.

## Load Baseline

Read `references/dev-baseline.md` once per task. Keep changes scoped to the
requested screen and reuse the project's components, themes, wrappers, state,
i18n, routing, and tests.

## Inputs And Decisions

- A UI image is required. Inspect it directly, including important small details.
- Use a supplied design size. Otherwise inspect image metadata and use its pixel
  dimensions as a provisional baseline; record `inferred-from-image-pixels`.
  Ask about size only when cropping, scaling, or device pixel ratio would
  materially change the reconstruction.
- Infer the stack from the target project. For a standalone request without a
  stack, use minimal runnable HTML/CSS/JS.
- Resolve uncertainty from the image, project code, assets, and user notes first.
  Make reversible visual choices using that evidence and state consequential
  assumptions. Ask only when missing information materially affects scope,
  business meaning, fidelity requirements, or an action's effects. Continue
  independent work while the affected decision waits.
- Do not invent hidden backend behavior, permissions, payments, data contracts,
  routes, or business-critical copy from a static image.

Read [input-contract.md](references/input-contract.md) for ambiguous intake,
missing assets, or uncertain dimensions.

## Reconstruct

1. Inspect the target route, nearby screens, local design tokens, icon libraries,
   and layout/scaling conventions before choosing implementation primitives.
2. Identify the image's layout, text, assets, visual tokens, visible states, and
   controls. Keep concise working notes; use the structured inventory in
   [image-analysis.md](references/image-analysis.md) for dense or multi-state UIs.
3. Match geometry and hierarchy first, then typography, spacing, colors, and
   details. Preserve readable source copy and use source assets when available.
   Identify missing assets or unreadable text without presenting approximations
   as source facts.
4. Implement semantic controls and the evidenced states. Use conservative
   responsive constraints while preserving the supplied breakpoint; one image
   cannot prove unshown breakpoint fidelity.

For framework, mobile, chart, or standalone choices, read
[implementation-paths.md](references/implementation-paths.md).

## Control Semantics

Do not turn visible controls into inert boxes. Buttons and form fields must be
real native or project controls, with appropriate focus, keyboard, selected,
disabled, and expanded behavior. Tabs, menus, accordions, dialogs, and steppers
need stateful components. Tabular data needs table/grid semantics.

Separate control semantics from hidden business behavior. Implement editing,
selection, and expansion when the relevant values or content are known. For an
unknown action or hidden panel, preserve the visible control and document the
missing behavior; do not fabricate a successful submission or destination.
Prototype mocks are acceptable within the requested prototype scope, but must
be reported as mocks. A no-op handler is a gap, not a completed interaction.

## Verify And Deliver

Render at the design width and height, inspect an actual screenshot, and compare
it to the source. Check missing assets, clipping, overlap, text, and runtime
errors. Smoke-test implemented controls with assertions about their visible
effects, not just successful clicks. Verify requested additional viewports in
the real renderer. For Flutter or native apps, use their platform renderer.

Fix visible drift and rerun affected checks. Report remaining input or runtime
limitations explicitly; code inspection alone cannot establish visual fidelity.
Do not claim exact pixel matching from an approximate baseline or incomplete
assets.

Keep evidence proportional: screenshot paths, relevant commands, and a brief
comparison with known gaps usually suffice. Create `UI_RECON.md`, token files,
component maps, or `VISUAL_REPORT.md` only when complexity, repeated review, or
the user calls for them. Do not create empty templates or mandatory scorecards.
Read [visual-verification.md](references/visual-verification.md) for commands,
interaction assertions, optional report templates, and diff interpretation.

## Bundled Tools

Resolve script paths from the absolute directory containing this `SKILL.md`.

- `scripts/image-metadata.mjs`: Read source image dimensions.
- `scripts/screenshot-page.mjs`: Capture the web page at a chosen viewport.
- `scripts/visual-diff.mjs`: Write an image comparison and optional diff image.
- `scripts/interaction-smoke.mjs`: Run focus/click/fill/select checks with
  optional value, focus, or attribute assertions; inspect the JSON results.

The browser helpers require Playwright and a working browser runtime. Use
existing project tooling when equivalent. Report an unavailable renderer as a
verification limitation rather than replacing screenshot evidence with a claim.
