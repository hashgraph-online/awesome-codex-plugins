# Miro — Design Tokens (loopy-native)
> Category: productivity/saas · Signature: infinite white canvas, pastel sticky-note accents

## Signature & atmosphere
Miro feels like an endless whiteboard the moment before a workshop starts — bright, open, and quietly inviting you to put something down. The recognizable idea is a near-pure-white canvas dotted with soft pastel "sticky" surfaces (coral, teal, rose, moss, orange) that map to collaboration contexts rather than decoration. Structure stays barely-there: a single hairline ring instead of borders, geometric type, and motion that feels like things sliding across a board.

## Color (hex · --var · role)
- `#ffffff` `--bg` — the canvas; `#1c1c1e` `--fg` — foreground (near-black, faint cool cast, not pure black)
- `#5b76fe` `--primary` — Blue 450; primary interactive, links, CTAs
- `#2a41b6` `--primary-active` — pressed blue
- `#00b473` `--success` — positive states
- Pastel accent surfaces (light): coral `#ffc6c6` · rose `#ffd8f4` · teal `#c3faf5` · orange `#ffe6cd` · pink `#fde0f0` — sticky-note section fills, paired with dark text
- Pastel dark partners: coral `#600000` · teal/moss `#187574` · yellow `#746019` — for text/icon on light pastels
- `#555a6a` `--muted` — secondary text (~6.6:1 on white, AA)
- `#a5a8b5` `--placeholder` — input placeholder
- `#c7cad5` `--border` — button border; ring `rgb(224,226,232)` for shadow-as-border

## Typography
- Stack: display `"Roobert PRO Medium", system-ui, sans-serif` with OpenType `"blwf","cv03","cv04","cv09","cv11"`; body `"Noto Sans"` with `"liga" 0,"ss01","ss04","ss05"`. Intent: confident geometric display, neutral humanist body.
- Display 56/400/1.15/-1.68px · H2 48/400/1.15/-1.44px · CardTitle 24/400/1.15/-0.72px · Subhead 22/400/1.35/-0.44px (Noto) · Body 18/400/1.45 · BodySm 16/400-600/1.50/-0.16px · Button 17.5/700/1.29/+0.175px · Caption 14/400/1.71 · Micro 10.5/400/0.90 uppercase
- Signature is the *low* display weight: Roobert at 400 with heavy negative tracking — not bold. The OpenType character variants are part of the geometric look.

## Spacing, radius, depth, motion
- Base 8px (with 4px micro); scale 4 · 8 · 12 · 16 · 24 · 32 · 48px.
- Radius: 8px buttons · 10–12px small cards · 20–24px panels · 40–50px large containers (the big radii read as rounded sticky surfaces).
- Depth strategy: **ring-shadow, not drops** — `rgb(224,226,232) 0 0 0 1px` acts as a soft hairline; pastel surface contrast supplies the rest. Heavy shadows are avoided.
- Motion: smooth Framer-style ease, 150–300ms; elements slide/scale like cards on a board; transform/opacity only.

## Components (key)
- Primary CTA: bg `#5b76fe` / text `#ffffff` / padding 7px 12px (button text 17.5/700) / radius 8px / no border. Hover → darken toward `#2a41b6`; focus → ring shadow.
- Outlined secondary: transparent bg, `1px solid #c7cad5`, 8px radius, 7px 12px padding.
- Pastel feature card: pastel fill (e.g. `#c3faf5`), 12–24px radius, dark-pastel text (`#187574`), ring `rgb(224,226,232) 0 0 0 1px` — one accent per section.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep display at Roobert weight 400 with strong negative tracking (-1.68px @ 56px) and apply the OpenType variants; use one pastel sticky surface per section.
- Don't: bump display to 600–700 to make it "pop" — the calm geometric 400 weight is the voice; bold breaks it.
- Don't: stack heavy box-shadows — depth is a single ring (`rgb(224,226,232) 0 0 0 1px`). And don't mix more than two pastels in one section or it stops reading as organized.

## Example component prompts
- "Hero on `#ffffff`: H1 Roobert PRO Medium 56px / weight 400 / line-height 1.15 / -1.68px in `#1c1c1e`; subhead Noto Sans 22px/400/1.35 in `#555a6a`; Blue CTA `#5b76fe`, white button text 17.5/700, 8px radius."
- "Pastel feature card: bg `#ffc6c6` (coral), 20px radius, ring `rgb(224,226,232) 0 0 0 1px`, title 24px/400/-0.72px in `#600000`, body Noto Sans 16px/400/1.50."
- "Outlined secondary button: transparent bg, `1px solid #c7cad5`, 8px radius, 7px 12px padding, label 17.5/700/+0.175px in `#1c1c1e`."
