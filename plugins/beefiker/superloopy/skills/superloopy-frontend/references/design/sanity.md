# Sanity — Design Tokens (loopy-native)
> Category: dev-tools · Signature: achromatic near-black control room with coral CTA and universal blue-on-hover

## Signature & atmosphere
Sanity renders a structured-content platform as a nocturnal command center — near-black, precise, and built for people who live in terminals, where dark isn't a "mode" but the natural state of the tool. Two ideas define it: a ruthlessly achromatic gray scale (no warm or cool bias, pure neutral discipline) punctuated by vivid signal colors, and a single rule that every interactive element shifts to the same electric blue on hover, like activation lights in a dark room. Headlines use extreme negative tracking so the type reads machined, like precision-cut steel.

## Color (hex · --var · role)
- `#0b0b0b` `--bg` — near-black canvas (the primary identity, not a toggle); `#ffffff` `--fg` — primary text on dark, max legibility
- `#212121` `--card` — elevated surface (cards, inputs); `#353535` `--border` — visible divider/border between dark layers
- `#f36458` `--primary` — coral-red CTA, the only warm touch; text on it `#ffffff`
- `#0052ef` `--accent` / `--focus` — electric blue, the **universal hover/active color** across every interactive element
- `#b9b9b9` `--muted` — body/secondary text; `#797979` tertiary/metadata/placeholder
- `#19d600` success (wide-gamut `color(display-p3 .27 1 0)`); `#dd0000` `--destructive`. Contrast: `#b9b9b9` on `#0b0b0b` ≈ 9:1; `#797979` ≈ 4.3:1 — fine for metadata, borderline for sustained body.

## Typography
- Stack: `"Waldenburg", Inter, "Space Grotesk", ui-sans-serif, system-ui` (display + UI, one face both registers); `"IBM Plex Mono", ui-monospace, monospace` (code + technical labels). Substitute Inter/Space Grotesk externally — geometric, slightly condensed.
- Display 112px / 400 / 1.00 / -4.48px · Hero-2 72px / 400 / 1.05 / -2.88px · Section 48px / 400 / 1.08 / -1.68px · Heading 32px / 425 / 1.24 / -0.32px
- Body-lg 18px / 400 / 1.50 / -0.18px · Body 16px / 400 / 1.50 · Caption 13px / 400-500 / 1.30-1.50
- Narrow weight range (400–425 for almost everything; 500–600 only on 11px uppercase labels). OpenType `"cv01","cv11","cv12","cv13","ss07"` on display. Mono uppercase for technical metadata.

## Spacing, radius, depth, motion
- Base 8px; scale 1 / 2 / 4 / 6 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96–120px; section gaps 64–120px (each section reads like its own focused slide).
- Radius: 3px inputs · 4–5px secondary buttons/tags · 6px standard cards · 12px large/feature cards · 99999px pill buttons & badges. Note the hard jump — nothing lives between 12px and full-pill.
- Depth is colorimetric, not shadow-based: ground `#0b0b0b` → elevated `#212121` → prominent `#353535` → inverted `#ffffff`. Containment is `1px solid #212121/#353535`; focus is a `0 0 0 2px #0052ef` ring. No offset drop shadows.
- Motion 150ms; the only flourish is the consistent blue-on-hover transition.

## Components (key)
- Primary CTA (coral pill): bg `#f36458` / text `#ffffff` / padding 8px 16px / radius 99999px / **hover bg `#0052ef`** + white text.
- Secondary (dark pill): bg `#0b0b0b` / text `#b9b9b9` / radius 99999px / hover bg `#0052ef`.
- Dark content card: bg `#212121` / border `1px solid #353535` / radius 6px / padding 24px / title `#ffffff`, body `#b9b9b9`, an 11px IBM Plex Mono uppercase tag in `#797979` at the top.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: hover EVERY interactive element to the same `#0052ef` — the instinct to give each button its own hover tint breaks the unified activation signal.
- Don't: warm or cool the grays — Sanity's neutrals are pure achromatic; a tinted gray ramp is the giveaway of a knock-off.
- Don't: use border-radius between 13px and 99998px — the scale jumps straight from 12px to full-pill, nothing in between.
- Don't: mix coral CTA and electric blue in the same element — coral is rest state, blue is activation; they don't co-occur.
- Don't: reach for drop shadows — depth is surface-color steps (`#0b0b0b`→`#212121`→`#353535`); shadows are invisible here anyway.

## Example component prompts
- "Feature section on `#0b0b0b`: heading 48px (Inter/Space Grotesk substitute) weight 400, letter-spacing -1.68px, white text; body 16px `#b9b9b9` line-height 1.50. Coral `#f36458` pill CTA + dark `#0b0b0b` pill, both hover to `#0052ef`."
- "Card grid on `#0b0b0b`: cards bg `#212121`, `1px solid #353535`, 6px radius, 24px padding. Title 24px white -0.24px; body 13px `#b9b9b9`; IBM Plex Mono uppercase tag 13px `#797979` on top."
- "Text input: bg `#0b0b0b`, `1px solid #212121`, 3px radius, 8px 12px, placeholder `#797979`, focus `0 0 0 2px #0052ef` ring."
