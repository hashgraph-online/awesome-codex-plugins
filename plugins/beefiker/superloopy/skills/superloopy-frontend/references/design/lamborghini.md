# Lamborghini — Design Tokens (loopy-native)
> Category: luxury-auto-tooling · Signature: total-black stage, gold headlight, type that SHOUTS

## Signature & atmosphere
Lamborghini is a cathedral of darkness — true `#000000` floods the viewport and refuses to lift to gray, and every element emerges from it like a machine under one spotlight. The one recognizable idea: a single gold accent cutting the black like a headlight at night, paired with enormous uppercase type set at regular weight. Corners are dead-sharp (0px). The mood is nocturnal, theatrical, deliberately intimidating.

## Color (hex · --var · role)
- `#000000` `--bg` — absolute black, the dominant surface (NOT dark gray — substituting `#111`/`#1a1a1a` breaks it); `#FFFFFF` `--fg` — primary text/marks
- `#FFC000` `--primary` — Lamborghini Gold, the SOLE chromatic color; primary CTA fills only, never decoration
- `#917300` `--primary-hover` — deep amber for gold-button pressed/hover
- `#202020` `--surface` — Charcoal, the elevated card/panel tone above black; `#181818` `--surface-2` — footer / deep sections (barely off black)
- `#F5F5F5` `--fg-soft` — secondary text slightly softer than white; `#7D7D7D` `--muted` — metadata; `#969696` — disabled/subtle labels
- `#494949` `--border-dark` — section-divider rules on black (elevation by tone, not line)
- `rgba(0,0,0,0.7)` `--overlay` — modal/video dim; `#3860BE` link-hover · `#29ABE2` info accent

## Typography
- Stack: `"LamboType", Roboto, "Helvetica Neue", Arial, sans-serif` — Neo-Grotesk with 12° angled terminals and hexagonal construction. Always upright, never italic. Weight 400 carries the headlines.
- Hero Display 120px / 400 / 0.92 · Display-2 80px / 400 / 1.13 · Section 54px / 400 / 1.19 · Sub-section 40px / 400 / 1.15 — all `text-transform: uppercase`
- Body 16px / 400 / 1.50 · Button 16px / 400 (gold) · Ghost button 14.4px / 400 / +0.2px uppercase · Label 12px / 400 / 1.83 / +0.96px uppercase · Micro 10px / 400

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48 · 56. Section padding 48–56px vertical / 40px horizontal. Button padding 16px (ghost) / 24px (gold).
- Radius: 0px on everything — buttons, cards, images. Only toggle switches round (20px). Sharp angles are non-negotiable.
- Depth strategy: tonal-shift on black — `#000` → `#181818` → `#202020` → `#494949` literally lights elevated elements, inverting the shadow model. No drop shadows (invisible on black anyway), no gradients on UI. Motion: color/opacity shifts only, no scale or translate.

## Components (key)
- Gold CTA (primary): bg `#FFC000` / text `#000000` / padding 24px / radius 0 / no border. Hover `#917300`. Reserved for "Discover More" / "Start Configuration" — the only gold in the view.
- Ghost CTA (secondary, dark bg): transparent / text `#FFFFFF` / 1px solid `#FFFFFF` at opacity 0.5 / padding 16px / radius 0. Hover lifts opacity to 0.7.
- Section divider: 1px solid `#202020` bottom border on black — elevation purely by tone shift, no shadow.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep the background true `#000000`; set all display type uppercase at weight 400; let vast black expanses act as the whitespace that frames each element.
- Don't: reach for bold (700) to emphasize a headline — the instinct that "big type must be heavy" is wrong here; LamboType at 400 is already the shout, and weight variation muddies it.
- Don't: round corners or add gradients — the reflex toward soft 8px radii and gradient fills contradicts the angular vehicle line.
- Don't: introduce a second accent color — anything beyond gold dilutes the single-headlight idea.

## Example component prompts
- "Hero on true `#000000`: model name 'TEMERARIO' in LamboType 120px/400 uppercase white, line-height 0.92, vertically centered; one gold `#FFC000` 'Discover More' button below — 0px radius, 24px padding, black text."
- "Ghost button: transparent, 1px solid white at 50% opacity, white text 14.4px uppercase +0.2px tracking, padding 16px, on black; hover raises opacity to 0.7."
- "News card on `#202020`: white uppercase heading 40px/400, body `#7D7D7D` 16px/1.50, divider as 1px `#202020` bottom border — no shadow, sharp corners."
