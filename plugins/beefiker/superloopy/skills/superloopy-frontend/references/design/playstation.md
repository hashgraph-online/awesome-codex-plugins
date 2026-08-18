# PlayStation — Design Tokens (loopy-native)
> Category: luxury-auto-tooling · Signature: quiet-authority light-300 display + a power-on hover that scales 1.2×

## Signature & atmosphere
PlayStation carries itself like the marketing wing of a premium electronics brand: a vertical channel of alternating surfaces — near-black hero, paper-white content, cobalt-blue footer — that lets product renders do the emotional work while the chrome stays calm. The recognizable idea is two-part: display type runs at weight 300 (a whisper, closer to a luxury-watch ad than a game store), and every interactive element performs the same "power-on" hover — cyan fill, white border, blue ring, and a literal 1.2× scale-up.

## Color (hex · --var · role)
- `#FFFFFF` `--bg` — paper-white content canvas; `#000000` masthead/hero; `#0070cc` footer anchor
- `#000000` `--fg` — display headlines on white; `#1F1F1F` `--fg-body` deep charcoal body / link-at-rest
- `#0070cc` `--primary` — PlayStation Blue, brand anchor, primary CTA fill, footer
- `#1EAEDB` `--accent` — PlayStation Cyan, hover/focus/active ONLY — never a resting background or text
- `#D53B00` `--commerce` — Commerce Orange, Store/buy CTAs and price callouts only; active `#AA2F00`
- `#6B6B6B` `--muted` body-gray · `#CCCCCC` mute-gray · `#F5F7FA` ice-mist surface · `#F3F3F3` divider
- `#C81B3A` `--destructive` form errors. Contrast: `#6B6B6B` on white ≈ 5.0:1 — body-safe.

## Typography
- Stack: `"SST", "Playstation SST", Arial, Helvetica, sans-serif` — Sony's proprietary global family; the weight-300-at-scale is the signature. No serif anywhere.
- Hero Display 54px / 300 / 1.25 / -0.1px · Hero-L 44px / 300 / 1.25 · Large 35px / 300 / 1.25 · Mid 28px / 300 / 1.25 · Compact Display 22px / 300 / 1.25 · Body 18px / 400 / 1.50 · Button 18px / 500 / 1.25 / +0.4px · Buy-CTA 18px / 700 / 1.25 / +0.45px · Caption 14px / 500 / 1.50
- Active weights climb with the layer: 300 (display 22px+), 400 (body), 500 (captions/buttons), 700 (buy). No all-caps — sentence/title case only.

## Spacing, radius, depth, motion
- Base 8px; section padding 48–96px (gallery pace, each module its own room).
- Radius scale 2 · 3 · 6 · 12 · 19 · 24 · 36 · 48 · 999px — rich, hierarchy-driven (3px utility inputs, 12px media, 24px features, 999px CTAs). Never 0px.
- Depth strategy: layered but restrained — shadows at `rgba(0,0,0,0.06/0.08/0.16)` for normal cards, then a dramatic `rgba(0,0,0,0.8) 0 5px 9px` only when a card floats over hero photography; no middle ground. Two section gradients (`#121314→#000000` dark, `#FFFFFF→#F5F7FA` light), nowhere else. Motion ~180ms ease on bg/transform/shadow.

## Components (key)
- Primary CTA: bg `#0070cc` / text `#FFFFFF` SST 18px/500/+0.4px / radius 999px / padding ~12px 24px / hover (signature): fill → `#1EAEDB`, 2px `#FFFFFF` border appears, 2px `#0070cc` outer ring blooms, `transform: scale(1.2)`; active opacity 0.6; focus = `0 0 0 2px #0070cc` ring.
- Commerce CTA: bg `#D53B00` / white 18px/700/+0.45px / 999px radius; active `#AA2F00`; hover follows the same cyan-invert + 1.2× scale.
- Game tile: 3:4 cover, 12px radius, feather `rgba(0,0,0,0.08) 0 5px 9px` shadow, 14px/700 title, mini 999px CTA.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: set every display headline 22px+ at weight 300; apply the full hover signature (cyan + white border + blue ring + 1.2× scale) to every primary button; alternate dark/white/blue surfaces.
- Don't: bold the display — the reflex that "game/retail = punchy heavy headline" is exactly inverted; weight 300 quiet-authority is the voice and 700 display reads as another game store.
- Don't: let cyan `#1EAEDB` appear at rest — the instinct to use the bright accent as a default fill or text breaks it; cyan only exists in motion.
- Don't: square the corners or skip the 1.2× hover lift — the "minimal flat button" reflex erases the power-on interaction that is PlayStation's signature; pick a radius from the scale, never 0.

## Example component prompts
- "Primary CTA: `#0070cc` fill, white SST 18px/500/+0.4px, 999px radius, 12px 24px padding; on hover fill → `#1EAEDB`, 2px white border, 2px `#0070cc` outer ring, scale 1.2×, 180ms ease."
- "Hero on `#000000`: 54px SST weight 300, -0.1px tracking, 1.25 line-height, white; one primary CTA with the standard hover. No all-caps."
- "Game tile: 3:4 cover, 12px radius, `rgba(0,0,0,0.08) 0 5px 9px` shadow, 14px/700 title, 12px/500 platform tag, mini 999px `#0070cc` CTA."
