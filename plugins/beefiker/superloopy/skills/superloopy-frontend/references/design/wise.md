# Wise — Design Tokens (loopy-native)
> Category: fintech/crypto · Signature: weight-900 lime-green headlines at 0.85 line-height, buttons that grow

## Signature & atmosphere
Wise looks like money without borders shouted on a protest sign: display type set at weight 900 with a line-height of 0.85 so letters nearly stack, dense and urgent. The recognizable hue is lime green (`#9fe870`) — a fresh, optimistic accent that rejects corporate banking blue, paired with a deep forest-green text on the button itself. Interaction is physical: buttons scale up on hover and compress on press rather than swapping color.

## Color (hex · --var · role)
- `#ffffff`/off-white `--bg`; `#0e0f0c` `--fg` — near-black with a faint green undertone (text + dark sections)
- `#9fe870` `--primary` — Wise Green, CTA fill + accent; `#163300` `--primary-fg` — dark-green text ON the green button
- `#cdffad` `--primary-hover` — pastel-green hover accent; `#e2f6d5` `--muted` — soft mint surface/badge bg
- `#454745` secondary text/border; `#868685` muted/tertiary; `#e8ebe6` `--card` — green-tinted light surface
- `#054d28` success (positive); `#d03238` `--destructive`; `#ffd11a` warning
- `rgba(14,15,12,0.12)` `--border` — ring/hairline border
- Contrast note: NEVER put green text on green — pair `#9fe870` bg with `#163300` text (passes); `#0e0f0c` on white is maximal.

## Typography
- Stack: `"Wise Sans", Inter, sans-serif` display; `Inter, Helvetica, Arial, sans-serif` body. OpenType `"calt"` on ALL text.
- Display-mega 126/900/0.85 · Display-hero 96/900/0.85 · H2 64/900/0.85 · H3 40/900/0.85 · Alt-heading 78/600/1.10/-2.34px (Inter) · Card-title 26/600/1.23/-0.39px · Feature 22/600/1.25/-0.396px · Body 18/400/1.44/+0.18px · Body-semibold 18/600/1.44 · Button 18-22/600/1.0-1.44 · Caption 14/400-600 · Small 12/400-600
- Display is weight 900 (heaviest in any fintech system) at 0.85 line-height; body Inter defaults to weight 600 — confident, never light.

## Spacing, radius, depth, motion
- Base 8px; scale 2 · 3 · 4 · 5 · 8 · 10 · 12 · 16 · 18 · 20 · 22 · 24.
- Radius: 2 (inputs) · 10 (combobox) · 16 (small cards/buttons) · 20 · 30 (feature cards) · 40 (tables/large) · 9999 (buttons/images) · 50% (icons).
- Depth strategy: ring shadows only — `rgba(14,15,12,0.12) 0 0 0 1px`; input focus `rgb(134,134,133) 0 0 0 1px inset`. No drop shadows.
- Motion: hover `scale(1.05)`, active `scale(0.95)` on interactive elements (GPU transform) — the signature physicality, ~150ms ease.

## Components (key)
- Primary CTA: bg `#9fe870` / text `#163300` / padding 5px 16px / radius 9999px. Hover `scale(1.05)`; active `scale(0.95)`; focus inset ring + outline.
- Secondary pill: `rgba(22,51,0,0.08)` bg / `#0e0f0c` text / radius 9999px / same scale behavior.
- Card: radius 30px, `1px solid rgba(14,15,12,0.12)` (or `#9fe870` accent), ring shadow; title 22/600, body 18/400.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: set display at weight 900 with line-height 0.85 — the extreme density IS the brand.
- Do: animate buttons with `scale(1.05)`/`scale(0.95)` instead of color hover.
- Don't: use a light display weight — the instinct to lighten huge type kills the identity; only 900.
- Don't: flood a large surface with `#9fe870` — green is for buttons/accents/badges, not full backgrounds.
- Don't: set body in weight 400 by default reflex — Inter 600 is the confident reading weight; and never green-on-green.

## Example component prompts
- "Hero on off-white: headline 96px Wise Sans weight 900 line-height 0.85 'calt' `#0e0f0c`; green pill CTA bg `#9fe870` text `#163300` radius 9999px padding 5px 16px, hover transform scale(1.05) active scale(0.95)."
- "Card: radius 30px, `1px solid rgba(14,15,12,0.12)`, ring shadow `rgba(14,15,12,0.12) 0 0 0 1px`; title 22px Inter weight 600 -0.396px; body 18px weight 400 line-height 1.44 +0.18px `#454745`."
