# Design-system contract and `DESIGN.md` schema

Use this reference when a changed visual claim needs new or updated app-defined semantics, or when an approved new/redesigned direction needs a coherent token contract. It does not expand a narrow nonvisual change into design work: that path may record `Design impact: unchanged` and `Visual evidence: not applicable` with behavioral, accessibility, and regression evidence.

## Choose the authority before the format

Inspect the repository's existing tokens, theme, style layer, component library, platform conventions, and representative UI before writing a design artifact. The project's current design source of truth remains authoritative.

- If `DESIGN.md` is already the established source, update it directly.
- If another source owns the system, update that source first. Use `DESIGN.md` only as a scoped mapping/receipt that links every changed app-defined semantic back to, and stays synchronized with, that owner.
- If the repository has no equivalent and a visual claim genuinely needs app-defined semantics, a scoped `DESIGN.md` may establish those affected decisions without requiring a repository-wide redesign.
- The absence of a formal design-system document is not a blocker and never means “no UI work.” Preserve working conventions and introduce only the minimum coherent contract required by the changed visual claim.

When material unknowns would change the visual direction or source of truth, ask the minimum necessary questions and batch independent unknowns. Otherwise document the evidence, assumption, and confidence and continue within the existing authority.

Loading this schema does not by itself select anti-slop, SEO, measured-quality, or a universal visual matrix. Anti-slop stays limited to its declared marketing/editorial or approved new-direction scope. SEO stays limited to the current crawlable public Web target or a distinct deployed public Web target in scope. Verify changed visual semantics across the target-derived browser/OS/input and breakpoint matrix, and create visual artifacts only for changed visual claims or interactions with a visible-state/layout consequence.

## Seven-section schema for a new or redesigned direction

Use the complete schema for an approved new or redesigned visual direction. For a visual delta inside an existing system, document only the affected sections and roles. Every new app-owned visual value traces to one authoritative token or an explicitly synchronized platform value; do not move runtime-owned native values into product tokens.

1. **Atmosphere / signature** — one paragraph naming how it *feels* (the one recognizable idea), not what it does. e.g. "weight-300 elegance, shadows tinted toward twilight" or "dark-native, content emerges from black, one signature heading weight". The signature is the compression key that makes every later token cohere.
2. **Color** — record each project-native color token, its resolved value or dynamic-value rule, and semantic role. Preserve the authoritative representation: CSS custom properties and CSS color syntax on Web, Android resources or Compose tokens, Apple asset catalogs or Swift values, Qt palette/QColor roles, or the repository's equivalent. Define only the roles the product needs, including state and dynamic light/dark/high-contrast variants where applicable. Pre-check contrast for the target's applicable text and non-text criteria and note adjusted values.
3. **Typography** — define a ramp per semantic role using the project's native units and APIs: CSS `rem`/`px`, Android `sp`, Apple points and text styles, Qt logical pixels or inherited platform fonts, or the repository equivalent. Record weight, line height, tracking, fallback, scaling behavior, and platform text-style ownership where applicable.
4. **Spacing** — preserve or establish a project-native base and named scale in the authoritative unit system (`rem`, logical px, dp, points, toolkit metrics, or equivalent). Values should follow that scale unless a platform metric, content constraint, or documented optical correction owns the exception; 4 px is an example, not a universal base.
5. **Components** — per component, define structure, semantic roles, content behavior, geometry, and every target-supported state and input path. Use the platform's native state and styling vocabulary rather than importing hover, radius, border, or CSS concepts where they do not apply.
6. **Motion** — define duration or spring behavior, continuity, interruption, and reduced-motion behavior. Prefer compositor-friendly or platform-native mechanisms appropriate to the actual renderer; do not impose Web-only transform/opacity/filter rules on native toolkits.
7. **Depth** — choose a coherent strategy supported by the platform and product, such as tonal hierarchy, material/elevation, borders, shadows, or native grouping. Do not mix unrelated systems without an explicit ownership reason.

## Authoring loopy-native token sets

Write your own token references — do not copy third-party design files. Two ways in:

- **From an existing UI**: inspect ground-truth values with the appropriate rendered-surface and repository tools rather than estimating. Keep the existing source authoritative; when a receipt is needed, map only the affected values into the schema and link them back to that source.
- **From a direction**: pick a committed aesthetic from the Design Read, then define exact tokens in the project's native representation. Record each color token, resolved value or dynamic rule, and role; add a short Do/Don't list that names the wrong instinct (for example, “Don't use a heavy display weight when the established voice is light”); and provide buildable examples using the target's real token names, units, and APIs rather than vague color or spacing language.

Keep the system lean. Add a token only when a component needs it, and add it to the authoritative design source first; synchronize any scoped `DESIGN.md` mapping in the same change.

## Web-oriented example token sets (loopy-native, illustrative)

Author your own only when a new or redesigned direction requires it. These examples intentionally use Web syntax to show shape and altitude; they are never defaults and their CSS variables, hex colors, pixel values, and interaction states must not be copied into a native target. Translate semantic roles into that target's authoritative tokens, units, platform states, and APIs.

### Calm SaaS (light, trustworthy)
- **Signature**: quiet confidence; generous whitespace, one restrained accent, content over chrome.
- **Color**: bg `#FBFCFD --bg`, fg `#0F1729 --fg` (near-black, not #000), primary `#2563EB --primary`, on-primary `#FFFFFF`, muted `#5B6472 --muted`, border `#E6E9EE --border`, card `#FFFFFF --card`. Accent used once per view.
- **Type**: stack Geist/General Sans. Display 48/600/1.05/-0.8px · H2 30/600/1.1 · body 16/400/1.6 · label 13/500/0.2px.
- **Spacing**: base 4; section padding `--space-20` (80px); card padding `--space-6`.
- **Depth**: borders-only + one soft tonal shadow `0 1px 2px rgba(15,23,41,.06), 0 8px 24px rgba(15,23,41,.06)`.
- **Motion**: 160-220ms ease-out; press scale 0.98.

### Editorial Dark (premium, content-faith)
- **Signature**: dark-native; text emerges from near-black; one signature heading weight; color used sparingly as punctuation.
- **Color**: bg `#0A0B0D --bg`, fg `#F2F3F5 --fg` (not pure white), surface `#141619 --surface`, primary `#E8533F --primary`, muted `#8A9099 --muted`, border `rgba(255,255,255,.08) --border`.
- **Type**: stack Cabinet Grotesk + a real serif for display. Display 72/510/1.0/-1.5px · H2 36/510/1.05 · body 17/400/1.65.
- **Spacing**: base 4; large rhythm (`--space-24` between sections); tight inside cards.
- **Depth**: tonal luminance stacking on dark surfaces; inset hairlines, no heavy drop shadows.
- **Motion**: 200-300ms; subtle reveal on scroll via IntersectionObserver; reduced-motion disables transforms.
