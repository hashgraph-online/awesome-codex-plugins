# Engineering & Performance

Use the actual platform, framework, installed versions and product support policy. SKILL.md owns execution scope and evidence requirements. Examples in other references are not mandates to install React, Motion, GSAP or any other library.

## Component and state design

Inspect adjacent components and tokens first. Reuse a sound existing primitive instead of inventing a parallel one. Extract shared behavior when its responsibilities are clear; a fixed repetition count is not a law. Preserve navigation, data contracts, keyboard behavior and user content.

Specify applicable states and transitions. Loading, empty, failure, success, disabled, focus and recovery are relevant only when the component can actually enter them. Do not invent eight states for a static label. Use explicit state models for mutually exclusive conditions and test recovery, cancellation and repeated actions.

For React projects, inspect client/server boundaries and compiler configuration before adding memoization. Isolate genuinely interactive work where the framework supports it. For Vue, Svelte, native or server-rendered applications, use their actual primitives. Performance claims require measurement, not a component naming convention.

## CSS and responsiveness

Use project tokens for shared decisions. Semantic tokens describe purpose; primitive tokens may describe a scale or value. New color syntax is optional when the existing representation is correct and supported. Do not mandate token migration for a one-line repair.

Prefer content-driven layout, logical properties, sensible intrinsic sizing and container queries when supported. Choose viewport sizes from product requirements, then test narrow widths, zoom/reflow, long strings, translation expansion, RTL where relevant, and actual input modalities. Do not force every two-column region to collapse at an arbitrary breakpoint.

Fix the cause of overflow. A blanket `overflow-x: hidden` can conceal inaccessible content and clipped focus indicators. Intentional tables, maps and carousels may need a documented scrolling region. Use safe-area insets for edge-attached controls when required. Choose `svh`, `dvh` or another height strategy according to whether stability or dynamic viewport fitting is needed.

Use native dialog/popover behavior or the established accessible primitive when it meets requirements. Check focus restoration, Escape, dismissal and layering. Portals and top-layer APIs solve different problems; neither removes the need for behavior tests.

For a new CSS API, record feature, checked date, primary documentation, target browsers and fallback. Baseline status alone is not the application's compatibility policy.

## Motion and rendering

Use motion to clarify a state change or spatial relationship, not to obstruct a task. Prefer a static reduced-motion alternative when movement is unnecessary. Avoid depending on animation-end events for essential state transitions when animations may be disabled.

Transform and opacity are useful starting points for efficient animation; actual compositing depends on the browser, property and surrounding content. Measure traces on target devices. Do not assert that every CSS or WAAPI animation is off-main-thread, that every JavaScript animation is slow, or that a fixed blur threshold guarantees performance.

Use CSS for straightforward state transitions; choose a library for behavior it materially simplifies. Bound expensive layers and effects. Add `will-change` only after measurement justifies it. Clean up listeners, observers, timers and animations. Do not add a second animation engine merely for a small effect.

## Accessibility

Use semantic controls, accessible names, programmatically associated labels and clear error recovery. Preserve visible focus and check keyboard order and focus restoration. `:focus-visible` is a browser heuristic, not a guarantee that only keyboard users receive focus indication. Meaningful images need useful alternatives; decorative images generally need `alt=""`.

WCAG contrast guidance: ordinary text generally needs 4.5:1. Large text is **18pt regular or 14pt bold**, equivalent to **24 CSS px or approximately 18.67 CSS px**, and generally needs 3:1. Do not substitute 18px/14px. Inactive controls and logotypes have defined exceptions; a stricter project policy must be labeled as policy, not the standard.

WCAG 2.2 AA target sizing is **24 by 24 CSS pixels**, with defined spacing and other exceptions. A **44 by 44** project target is a useful stricter choice, not a universal AA requirement. Inspect applicable non-text contrast, focus visibility and focus-obscuring requirements separately.

Automated accessibility tools identify some issues, not complete conformance. Add applicable manual keyboard and assistive-technology checks. Mark unavailable checks NOT_RUN; never replace them with an invented percentage or a passing style score.

## Verification and observability

Capture the primary user task, relevant failure paths, source revision, command, environment, exit status and evidence artifact. Measure before and after under comparable conditions. Record changed dependencies and compatibility impacts.

Separate field and lab data. The good Core Web Vitals field thresholds at the 75th percentile are LCP at most 2.5 seconds, INP at most 200 milliseconds and CLS at most 0.1. A local lab measurement or Lighthouse score is not a field result.

For visual comparisons, stabilize fixtures, fonts, browser, viewport, device scale and operating system. Inspect changes rather than automatically accepting new screenshots. A screenshot match does not establish usability or accessibility. Static `review_and_gate` evidence does not certify an interface it never rendered.

## Primary sources

Verified 2026-09-04. Recheck version-sensitive facts before adopting a new API.

- [WCAG contrast and large-text definitions](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- [WCAG target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
- [Playwright accessibility testing](https://playwright.dev/docs/accessibility-testing)
- [Playwright visual comparisons](https://playwright.dev/docs/test-snapshots)
- [Core Web Vitals thresholds](https://web.dev/articles/defining-core-web-vitals-thresholds)
