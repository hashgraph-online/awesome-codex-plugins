# Framer — Design Tokens (loopy-native)
> Category: brand-web-media · Signature: pure-black void, spring-compressed display tracking, one electric blue

## Signature & atmosphere
Framer is a nightclub built for web designers — an absolute-black canvas where every screenshot and headline floats in deep space. The recognizable idea is compression: GT Walsheim display type pulled to brutal negative tracking (down to -5.5px at 110px) so words feel spring-loaded, dense, about to snap open. A single cold blue does all the accent work, and the product UI itself is the hero art. Dark is not a theme here; the void is the point.

## Color (hex · --var · role)
- `#000000` `--bg` — true void canvas, not charcoal; `#FFFFFF` `--fg` — headings, high-emphasis text
- `#0099FF` `--primary` — the sole accent: links, ring borders, focus, interactive highlights
- `#A6A6A6` `--muted` — body copy, descriptions, dimmed labels on dark
- `rgba(0,153,255,0.15)` `--border` — signature blue ring shadow that brands every bordered element; `#090909` near-black ring for quiet containment
- `rgba(255,255,255,0.1)` `--card` — frosted-glass surface on dark (the translucent button/panel fill)
- `rgba(255,255,255,0.6)` tertiary text/placeholder; `rgba(255,255,255,0.5)` frosted hover
- Note: this is a one-accent-color system. Do not introduce a second hue — blue is the only chromatic event on the page.

## Typography
- Stack: GT Walsheim (display, weight 500 only) → Inter Variable (body/UI, heavy OpenType usage); mono Azeret Mono, rounded Open Runde for micro-labels
- Display 110px / 500 / 0.85 / -5.5px — extreme compression, the signature gesture
- Section display 85px / 500 / 0.95 / -4.25px · Section heading 62px / 500 / 1.00 / -3.1px · Feature 32px / 500 / 1.13 / -1px
- Card title 24px / 400 / 1.30 / -0.01px (Inter, features cv01 cv05 cv09 cv11 ss03 ss07) · Sub-head 20px / 600 / -0.8px
- Body 15–18px / 400 / 1.30 / -0.01px · Label 13px / 500 · Caption 14px / 400
- Display is weight 500 only — medium is the brand voice; Inter runs 6+ OpenType features for a custom feel even at body size.

## Spacing, radius, depth, motion
- Base 8px; scale 2 · 4 · 6 · 8 · 10 · 12 · 15 · 20 · 30 · 35; sections 80–120px apart (void as dramatic pause)
- Radius: 1px micro · 8px standard components · 10–12px cards/screenshots · 15–20px large containers · 40px nav pills · 100px primary CTA pills
- Depth strategy: borders + rings, inverted from light-theme. Blue ring `rgba(0,153,255,0.15) 0 0 0 1px` for containment; floating elevation = `rgba(255,255,255,0.1) 0 0.5px 0 0.5px` top highlight + `rgba(0,0,0,0.25) 0 10px 30px` ambient. No heavy glass blur.
- Motion: scale transforms (~0.85 factor) and opacity reveals; subtle blue-glow auras behind key areas.

## Components (key)
- Primary CTA (Solid White Pill): bg `#FFFFFF` / text `#000000` / radius 100px / padding 10px 15px — clean, unmissable on black
- Frosted Pill (secondary): bg `rgba(255,255,255,0.1)` / radius 40px / black text — ambient glass button living on the dark surface
- Dark card: `#090909` fill, blue ring `rgba(0,153,255,0.15) 0 0 0 1px` border, 10–12px radius, white Inter heading, `#A6A6A6` body; hover lifts the ring glow slightly.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep the background pure `#000000`; apply -3px to -5.5px tracking on display — the compression is non-negotiable.
- Don't: reach for a "comfortable" warm dark like `#1a1a1a` or `#2d2d2d` — the instinct to soften black is wrong; the void must be absolute.
- Don't: bold the display (700+) — GT Walsheim is weight 500 only.
- Don't: add positive letter-spacing or a second accent color — everything is compressed and blue-only.

## Example component prompts
- "Hero on `#000000`: 110px GT Walsheim heading weight 500, letter-spacing -5.5px, line-height 0.85, white, with a solid white pill CTA (radius 100px) carrying black text."
- "Feature card on black: 12px radius, 1px blue ring shadow `rgba(0,153,255,0.15) 0 0 0 1px`, white Inter heading 22px/700, `#A6A6A6` body, no warm-grey fill."
