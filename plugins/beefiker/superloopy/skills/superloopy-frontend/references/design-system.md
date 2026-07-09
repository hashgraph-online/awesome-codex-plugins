# Design System (DESIGN.md) Schema

A DESIGN.md is the single source of truth for a UI: tokens live here, and every component traces back to them. This is what turns per-component improvisation (the root of inconsistent slop) into one coherent vocabulary. **No design system = no UI work.**

## The 7 sections

Author DESIGN.md with these sections. Every value is a token; no raw hex or magic numbers live in components.

1. **Atmosphere / signature** — one paragraph naming how it *feels* (the one recognizable idea), not what it does. e.g. "weight-300 elegance, shadows tinted toward twilight" or "dark-native, content emerges from black, one signature heading weight". The signature is the compression key that makes every later token cohere.
2. **Color** — every color as `hex + CSS variable + semantic role`. Define the full set: background, foreground, primary, on-primary, secondary, accent, card, muted, border, destructive, ring. Pre-check contrast (text/background pairs ≥ 4.5:1, large/UI ≥ 3:1) and note any adjusted value.
3. **Typography** — a full ramp per role: `size (px/rem) · weight · line-height · letter-spacing` (+ OpenType features if used). Name the font stack and its intent.
4. **Spacing** — a base unit (4px) and a named scale (`--space-1 … --space-24`); every margin/padding/gap is a multiple. Note deliberate off-grid optical values if any.
5. **Components** — per component: background, text, padding, radius, border, font, and every state (hover/active/focus/disabled). Spell out any signature component as a buildable recipe.
6. **Motion** — the physics (duration ranges, easing/spring), GPU-composited only (transform/opacity/filter). Define reduced-motion behavior.
7. **Depth** — commit to one strategy (tonal shift vs shadows vs borders) and a single elevation ladder. Do not mix.

## Authoring loopy-native token sets

Write your own token references — do not copy third-party design files. Two ways in:

- **From an existing UI**: extract ground-truth values with the browser (computed styles, as in `superloopy-clone`) rather than estimating, then encode them in the 7-section schema.
- **From a direction**: pick a committed aesthetic from the Design Read, then define exact tokens. Encode each color as `hex + variable + role`, add a short Do/Don't list that names the wrong instinct (e.g. "Don't use weight 600-700 for display — 300 is the voice"), and a few copy-paste example component prompts at the right altitude (cite px and hex, not "dark gray").

Keep the system lean — a design system that grows every week is dying. Add a token only when a component needs it, and add it to DESIGN.md first.

## Example token sets (loopy-native, illustrative)

Author your own per project; these show the shape and altitude.

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
