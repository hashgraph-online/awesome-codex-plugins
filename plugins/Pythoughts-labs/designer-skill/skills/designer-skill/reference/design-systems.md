# Design Systems

Make approved decisions reusable without requiring every project to adopt a new architecture. SKILL.md governs authorization, preservation and evidence. Inspect the current token model, consumers, platforms and generation pipeline before editing.

## Token ownership

Use primitives for raw scales and semantic aliases for purpose. Component tokens are optional and justified by a component-specific need. Primitive names such as `blue-500` or `space-4` are valid; semantic names such as `text-primary` should remain meaningful when values change. Do not confuse these two naming layers.

Preserve a healthy CSS-variable, Sass, platform-native or generated-token system. When tool interchange is needed, DTCG 2025.10 is a stable community specification, not a W3C Recommendation. Validate the chosen format version and platform transforms; do not assume every tool supports every token type or resolver feature.

Before generating assets, reject missing aliases, cycles, wrong types, duplicate emitted names and unsupported transforms. Commit source and generated output consistently. Add deterministic generation checks and hashes to CI. Do not change existing token names silently; use an explicit alias/deprecation window for migrations.

Theme, brand, contrast and density are separate concerns. Semantic overrides are often sufficient, but primitive or component overrides can be legitimate in another architecture. Do not turn one layering strategy into a universal ban.

## Explicit theme selection must override the operating system

This example uses an automatic mode only when the root has no explicit theme. Token values are illustrative, not a replacement for the project's identity.

```css
:root,
:root[data-theme="light"] {
  color-scheme: light;
  --surface: #ffffff;
  --text-primary: #161616;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme]) {
    color-scheme: dark;
    --surface: #161616;
    --text-primary: #f5f5f5;
  }
}

:root[data-theme="dark"] {
  color-scheme: dark;
  --surface: #161616;
  --text-primary: #f5f5f5;
}

body {
  background: var(--surface);
  color: var(--text-primary);
}
```

Automatic mode removes `data-theme`; explicit light/dark sets the matching value. Persist user intent, avoid hydration mismatch and test the initial render. Pure white and off-black are valid here; no hue is intrinsically forbidden.

Test all six combinations of OS light/dark and user auto/light/dark. Also check applicable forced-colors behavior, contrast, native control appearance and focus. Do not presume dark themes need a fixed percentage of desaturation or elevation lightening.

## Component contracts

Document purpose, anatomy, variants, public API, applicable states, interaction transitions, responsive behavior, accessible names and focus behavior. State what is not applicable rather than fabricating irrelevant states. Specify composition boundaries and controlled/uncontrolled behavior where the platform supports them.

Use existing naming conventions unless changing them is authorized. A new component must not silently rename established domain concepts. Include an example, a misuse case and a test for critical interactions. A visual variant cannot remove an accessible name, hide a required action or alter a data contract accidentally.

## Motion and content tokens

Define duration/easing roles only for distinct behavior. Avoid prescribing one universal duration scale. Reduced-motion mode must preserve state information without requiring movement. Do not rely on a zero-duration animation firing an event to complete business logic.

Locale, text direction, formatting and content expansion are part of the system. Test long names, missing optional content, numeric alignment and translated labels. A design system does not authorize invented endorsements, metrics or identities.

## Migration, acceptance and rollback

Map every changed token or component to its consumers. Validate all affected themes and states. Run deterministic generation, type/behavior checks and controlled visual comparisons before removing aliases. Document dependency and minimum-version changes.

Record source revision, generated hashes, rendered artifacts and reviewer decisions. A passing automated scan does not prove complete accessibility conformance. Follow exact applicable WCAG criteria; disabled-control contrast beyond the standard is a separately labeled project policy.

Roll back source mappings and generated assets together, preserving unrelated changes. Do not change screenshot baselines merely to conceal an unexplained difference. Keep the previous token mapping available until the migration is verified.

## Primary sources

Verified 2026-09-04.

- [DTCG technical reports 2025.10](https://www.designtokens.org/TR/2025.10/)
- [WCAG contrast, including inactive-control exceptions](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- [Controlled visual comparisons](https://playwright.dev/docs/test-snapshots)
