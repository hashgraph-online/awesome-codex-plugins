# Rendered Evidence

Read this rule only when browser capability exists or a user supplies a rendered-evidence JSON handoff.

## Capability gate

- Do not install Playwright, Axe, a browser, or dependencies to obtain rendered evidence.
- Without a valid handoff, report `static_only` or `unavailable`; do not claim visual hierarchy, actual contrast, keyboard, accessibility, or behavior passed.
- Validate a handoff with `scripts/collect-rendered-evidence.sh --input <capture.json>` before citing it.

## Evidence minimum

Every rendered observation needs a surface/URL, viewport width and height, state, locator, capture time, and at least one observed fact: bounding rectangle, overflow, computed style primitive, focus-visible observation, or motion-preference observation.

Use project breakpoints when known; otherwise inspect 375, 768, and 1280 widths. Inspect only states the actual surface exposes. A screenshot may support hierarchy, spacing, or asset-fit discussion, but not semantic, keyboard, WCAG, or end-to-end behavior claims.

## Finding boundary

A rendered finding records the viewport, state, locator, captured values, and the exact claim it supports. Static findings remain static unless an observed rendered fact independently confirms the claim.

## Sources

> Claims checked 2026-09-21. No external source was used in this file.

The capability gate and the minimum evidence fields are this package's own contract. The tool names Playwright and Axe appear only as things not to install, and no external document is cited.
