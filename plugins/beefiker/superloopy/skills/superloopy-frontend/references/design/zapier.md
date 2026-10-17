# Zapier — Design Tokens (loopy-native)
> Category: productivity/saas · Signature: cream-paper warmth, border-first structure

## Signature & atmosphere
Zapier rejects cold developer-tool minimalism for the feel of an organized paper notebook — an unbleached-cream canvas with near-black ink carrying a faint reddish-brown warmth, so the page reads human rather than mechanical. Hero headlines are set in a wide geometric display face crushed to a 0.90 line-height, stacking like architectural blocks, while Inter handles all the functional work and a thin serif appears only for editorial grace notes. Structure is drawn with warm sand borders, not shadows: this design is grounded and tangible, never floating.

## Color (hex · --var · role)
- `#fffefb` `--bg` — cream canvas + card/button surfaces; never pure white
- `#201515` `--fg` — Zapier Black; warm near-black with reddish undertone, headings + dark buttons
- `#fffdf9` `--surface-2` — barely-distinct alternate cream tint
- `#ff4f00` `--accent` — Zapier Orange; primary CTA + active underlines only
- `#36342e` `--body` — dark charcoal body text
- `#939084` `--muted` — tertiary/muted labels
- `#c5c0b1` `--border` — warm sand; the structural backbone
- `#eceae3` `--surface-3` — light sand for secondary/ghost buttons
- Active-tab underline `rgb(255,79,0) 0 -4px 0 0 inset`; hover underline `rgb(197,192,177) 0 -4px 0 0 inset`.

## Typography
- Stack: `"Degular Display"` (hero only); `Inter, Helvetica, Arial` (everything functional); `"GT Alpina"` (editorial serif). Substitute a wide geometric display + Inter if Degular is unavailable.
- DisplayXL 80/500/0.90/normal · DisplayHero 56/500/0.90–1.10/0–1.12px · DisplaySM 40/500/0.90
- H2 48/500/1.04 (Inter) · EditorialH 48/250/normal/-1.92px (GT Alpina) · Sub 32/400/1.25
- CardTitle 24/600/normal/-0.48px · BodyLg 20/400–500/1.00–1.20/-0.2px · Body 16/400–500/1.20–1.25/-0.16px
- Button 16/600/normal · CaptionUpper 14/600/normal/+0.5px UPPERCASE · Micro 12/600/0.90–1.33/+0.5px
- Signature: Degular at 0.90 line-height = vertically compressed hero blocks; GT Alpina stays thin (250–300) with -1.6 to -1.92px tracking.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 6 · 8 · 10 · 12 · 16 · 20 · 24 · 32 · 40 · 48 · 56 · 64 · 72.
- Radius: 3px tiny · 4px orange CTA/tags · 5px cards/containers · 8px featured cards/large buttons/tabs · 14px social icons · 20px pills.
- Depth strategy: **borders, not shadows**. Sand `1px solid #c5c0b1` for standard containment, `#36342e` for emphasis. Only "shadow" is the inset tab underline.
- Motion: subtle border-color intensify on hover; tabs swap inset underline color without layout shift.

## Components (key)
- Primary CTA (orange): bg `#ff4f00` / text `#fffefb` / padding 8px 16px / radius 4px / `1px solid #ff4f00`.
- Large dark CTA: bg `#201515` / text `#fffefb` / padding 20px 24px (deliberately spacious) / radius 8px. Hover → bg `#c5c0b1`, text `#201515`.
- Tab nav: transparent, Inter 16/500 `#201515`, padding 12px 16px; active = `box-shadow: rgb(255,79,0) 0 -4px 0 0 inset`, hover = sand inset underline.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: use warm cream `#fffefb` and warm-black `#201515`, and draw structure with sand `#c5c0b1` borders.
- Don't: reach for pure white `#ffffff` / pure black `#000000` — the warm shift is the entire personality; neutral B/W flattens it to generic SaaS.
- Don't: add `box-shadow` elevation to cards — Zapier is border-first; floating shadow cards break the grounded paper feel. (And don't pill the primary CTA — pills are for tags/social only.)

## Example component prompts
- "Hero on `#fffefb`: headline 56px Degular Display weight 500, line-height 0.90, `#201515`. Subtitle 20px Inter/400/1.20, `#36342e`. Orange CTA `#ff4f00`, 4px radius, 8px 16px padding, `#fffefb` text; plus dark CTA `#201515`, 8px radius, 20px 24px padding."
- "Card: `#fffefb`, `1px solid #c5c0b1`, 5px radius, no shadow. Title 24px Inter/600/-0.48px."
- "Tab nav: Inter 16/500 `#201515`, 12px 16px padding, active `box-shadow: rgb(255,79,0) 0 -4px 0 0 inset`, hover `rgb(197,192,177) 0 -4px 0 0 inset`."
