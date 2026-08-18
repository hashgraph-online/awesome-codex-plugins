# Ferrari — Design Tokens (loopy-native)
> Category: luxury-auto-tooling · Signature: chiaroscuro editorial — one red spark in a black room

## Signature & atmosphere
Ferrari reads like a hardbound yearbook, not a storefront: inky-black spreads cut against crisp white panels, paged through with the gravity of an art catalogue. The single recognizable idea is restraint — Rosso Corsa appears once per view, like a brake light in the dark, and everything else lives in black, white, and a tight gray ramp. Corners are nearly square (2px), so the whole thing feels machined rather than soft.

## Color (hex · --var · role)
- `#000000` `--bg` — cinematic background (true black, the void that makes imagery float); `#FFFFFF` `--fg-on-dark` — text/marks on black
- `#FFFFFF` `--surface` — editorial white panels; `#181818` `--fg` — body text on white (warm near-black, NOT pure `#000` — improves readability)
- `#DA291C` `--primary` — Rosso Corsa, the ONLY brand color; CTA fills and brand-critical moments only
- `#B01E0A` `--primary-hover` · `#9D2211` `--primary-active` — deepened reds for state
- `#303030` `--surface-dark` — footer / newsletter panels, lifted off black for depth
- `#666666` `--muted` — secondary text; `#8F8F8F` `--muted-2` — metadata/timestamps; `#969696` — placeholder/disabled
- `#CCCCCC` `--border` — input and divider lines on white
- `#03904A` success · `#F13A2C` warning (deliberately orange-shifted away from brand red so alerts ≠ brand) · `#4C98B9` info

## Typography
- Stack: `"FerrariSans", Arial, Helvetica, sans-serif` for narrative (headings, body, buttons); a secondary uppercase label face for annotations. Default voice is weight 500, not 700.
- Display 26px / 500 / 1.20 / normal · H2 24px / 400 / 1.20 · Subhead 18px / 700 / 1.20 · Body 16px / 400 / 1.40 · Button 16px / 400 / lh-normal / +1.28px tracking · Nav 13px / 600 / +0.13px
- Label 12px / 400 / 1.27 / +1px tracking, `text-transform: uppercase` — the structural-annotation register, kept separate from narrative type

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 20 · 24 · 40 · 80 (40–80 between major sections). Button padding 12px/10px — compact, deliberate.
- Radius: 2px default (buttons/inputs), 8px modals only, 50% for dots/avatars. Razor precision is the point.
- Depth strategy: tonal-shift + photography, not shadows. Layering is black↔white section contrast and `hsla(0,0%,7%,0.8)` overlays. One whisper shadow (`rgb(153,153,153) 1px 1px 1px 0`) reserved for cookie/dropdown chrome. Motion: hard cuts between sections; color/opacity transitions only, no scale.

## Components (key)
- Primary CTA (red, dark bg): bg `#DA291C` / text `#FFFFFF` / padding 12px 10px / radius 2px / no border. Hover `#B01E0A`, active `#9D2211`, focus 2px solid outline. One per screen, max.
- White CTA (light bg): bg `#FFFFFF` / text `#000000` / 1px solid `#000000` / radius 2px / tracking +1.28px. Ghost variant: transparent / 1px solid `#FFFFFF` / white text on dark imagery.
- Editorial card: white bg, no border, no shadow; full-bleed 16:9 image, FerrariSans heading (16–24px) under it, uppercase label (12px/+1px) as the category tag.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep `#181818` (not `#000`) for body text on white; alternate black cinematic and white editorial sections for the page-turn rhythm; let one red element carry the whole screen.
- Don't: scatter Rosso Corsa as a theme color — the instinct to "use the brand color generously" kills it; it is a single signal, not a wash.
- Don't: round corners past 2px or add card shadows — the reflex toward friendly 8–12px radii and drop-shadow "elevation" reads as generic SaaS, not coachwork.
- Don't: set FerrariSans headings in uppercase — uppercase belongs only to the label face.

## Example component prompts
- "Hero on `#000000`: centered emblem at top, 80px top padding, one headline in FerrariSans 26px/500 white, an uppercase label 12px/+1px tracking in `#969696` below — no other color."
- "Subscribe band on `#303030`: white FerrariSans 24px/500 heading, `#8F8F8F` 13px subtitle, transparent input with 1px `#CCCCCC` border, and a single `#DA291C` button (white text, 2px radius, 12px/10px padding)."
- "Editorial card on white: 16:9 image, FerrariSans 16px/700 `#181818` heading, uppercase category label 11px/+1px `#8F8F8F` — no border, no shadow, 2px radius."
