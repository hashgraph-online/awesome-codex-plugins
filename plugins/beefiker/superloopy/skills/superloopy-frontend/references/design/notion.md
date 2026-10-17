# Notion — Design Tokens (loopy-native)
> Category: productivity/saas · Signature: warm-paper minimalism, whisper borders

## Signature & atmosphere
Notion feels like quality stationery rather than software — a blank page that steps out of the way. The trick is warmth hiding inside neutrality: the canvas is pure white but the ink is a 95%-opacity near-black, and every gray carries a faint yellow-brown undertone so nothing reads as cold glass. Structure is drawn with borders thin enough to be felt before they are seen, and depth comes from stacked near-invisible shadows, never from a single hard drop.

## Color (hex · --var · role)
- `#ffffff` `--bg` — page + card background
- `rgba(0,0,0,0.95)` `--fg` — foreground; deliberately NOT pure black, a softening micro-warmth
- `#0075de` `--primary` — Notion Blue; the only saturated chrome color, CTAs + links
- `#005bab` `--primary-active` — pressed/hover-dark variant of primary
- `#f6f5f4` `--muted-surface` — warm off-white for alternating section bands (yellow undertone is the point)
- `#615d59` `--muted` — secondary text/descriptions (~5.5:1 on white, AA)
- `#a39e98` `--placeholder` — placeholder + disabled text
- `rgba(0,0,0,0.1)` `--border` — whisper border, used everywhere
- `#f2f9ff` `--badge-bg` / `#097fe8` `--badge-fg` — tinted pill badge (text ~4.5:1 on badge bg, AA-large)
- `#31302e` `--surface-dark` — warm dark section background

## Typography
- Stack: `Inter, -apple-system, system-ui, "Segoe UI", Helvetica, Arial` — Notion ships a tuned Inter; intent is neutral-but-warm reading.
- Display 64/700/1.00/-2.125px · H2 48/700/1.00/-1.5px · H3 26/700/1.23/-0.625px · CardTitle 22/700/1.27/-0.25px
- Body 16/400/1.50/normal · BodyMed 16/500/1.50 · Nav 15/600/1.33 · Caption 14/500/1.43
- Badge 12/600/1.33/+0.125px (the only positive tracking — widens small text for legibility)
- OpenType `"lnum"` + `"locl"` on display/heading text.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 80 · 120 (section gaps live at 64–120).
- Radius: 4px buttons/inputs · 8px small cards · 12px standard cards · 16px hero cards · 9999px pills.
- Depth strategy: **borders + stacked tonal shadows**. Card = 4-layer stack, each layer ≤0.04 opacity (`0 4px 18px rgba(0,0,0,.04)` + 3 fainter). Deep = 5 layers to 52px blur at 0.05. Never one hard shadow.
- Motion: 150–200ms ease; press = `scale(0.9)`, hover = `scale(1.05)`; transform/opacity only.

## Components (key)
- Primary CTA: bg `#0075de` / text `#ffffff` / padding 8px 16px / radius 4px / border `1px solid transparent`. Hover → bg `#005bab`; active → `scale(0.9)`; focus → 2px outline + soft shadow.
- Pill badge: bg `#f2f9ff`, text `#097fe8`, padding 4px 8px, radius 9999px, 12px/600/+0.125px. Status + "New" tags.
- Alternating band: full-width section toggling `#ffffff` ↔ `#f6f5f4`, 64–80px vertical padding, content max-width ~1200px centered. This rhythm IS the layout.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: tint grays warm (`#f6f5f4`, `#615d59`) and keep borders at `rgba(0,0,0,0.1)`.
- Don't: reach for pure black `#000000` text — the 95% near-black is the whole softness; pure black reads clinical.
- Don't: use a single `box-shadow: 0 2px 8px rgba(0,0,0,0.2)` — that one heavy drop kills the embedded-in-paper feel. Stack faint layers instead.

## Example component prompts
- "Hero on `#ffffff`: headline 64px Inter weight 700, line-height 1.00, letter-spacing -2.125px, color `rgba(0,0,0,0.95)`. Subtitle 20px/600/1.40 in `#615d59`. Blue CTA `#0075de`, 4px radius, 8px 16px padding, white text, hover `#005bab`."
- "Card: `#ffffff`, `1px solid rgba(0,0,0,0.1)`, 12px radius, shadow `0 4px 18px rgba(0,0,0,.04), 0 2px 7.8px rgba(0,0,0,.027), 0 .8px 2.9px rgba(0,0,0,.02), 0 .175px 1px rgba(0,0,0,.01)`. Title 22px/700/-0.25px."
- "Pill badge `#f2f9ff` bg, `#097fe8` text, 9999px radius, 4px 8px padding, 12px/600/+0.125px."
