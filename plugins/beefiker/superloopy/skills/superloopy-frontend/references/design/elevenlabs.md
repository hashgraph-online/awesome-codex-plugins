# ElevenLabs — Design Tokens (loopy-native)
> Category: ai-labs · Signature: whisper-thin weight-300 display + sub-0.1 multilayer shadows

## Signature & atmosphere
ElevenLabs feels like a premium audio brochure: a near-white room where light, thin type and barely-there shadows do everything. The recognizable idea is lightness-as-impact — display headings set in weight 300 read like sound waves rendered as type, drawing the eye through vast whitespace by being delicate rather than loud. Warm stone undertones keep the purity from going clinical.

## Color (hex · --var · role)
- `#ffffff` `--bg` — pure white; `#000000` `--fg` — black text and dark pills
- `#f5f5f5` `--card` — light gray surface; `#f5f2ef` warm stone (used at 80% alpha for featured surfaces)
- `#000000` `--primary` — black pill CTA fill
- accent: ElevenLabs is intentionally achromatic — "accent" is the warm stone surface + warm-tinted shadow, not a hue
- `#4e4e4e` `--muted` — secondary text; `#777169` warm-gray tertiary / decorative underlines
- `#e5e5e5` `--border` — explicit hairline; `rgba(0,0,0,0.05)` ultra-subtle bottom borders
- Contrast: `#4e4e4e` on white ≈ 8:1 (strong body); `#777169` ≈ 5:1 (muted but OK).

## Typography
- Stack: display `"Waldenburg", system-ui, sans-serif`; display-bold `"WaldenburgFH"`; body `Inter, system-ui, sans-serif`; code `"Geist Mono", ui-monospace, monospace`.
- Display 48px / **300** / 1.08 / -0.96px · H2 36px / 300 / 1.17 · Card-title 32px / 300 / 1.13 · Body 18px / 400 / 1.60 / +0.18px · Body-sm 16px / 400 / 1.50 / +0.16px · Button 15px / 500 / 1.47 · Uppercase-CTA WaldenburgFH 14px / 700 / 1.10 / +0.7px UPPERCASE
- Body Inter carries POSITIVE tracking (+0.14 to +0.18px) — airy reading rhythm against tight display.

## Spacing, radius, depth, motion
- Base 8px; scale 4/8/12/16/18/20/24/28/32/40px; Apple-grade section gaps.
- Radius scale 4 / 8 / 10 / 16 / 20 / 24 / 30 (warm CTA) / 9999px (pills).
- Depth strategy: stacked shadows at sub-0.1 opacity, each combining inset + outline + lift. Card ring: `rgba(0,0,0,0.06) 0 0 0 1px, rgba(0,0,0,0.04) 0 2px 4px`. Featured CTA uses a WARM shadow `rgba(78,50,23,0.04) 0 6px 16px` — shadows carry color, not just darkness.
- Motion 150–220ms ease-out; transform/opacity only.

## Components (key)
- Primary black pill: bg `#000000` / text `#ffffff` / padding 0 14px (pill height) / radius 9999px / hover slight lift.
- Warm stone CTA (signature): bg `rgba(245,242,239,0.8)` / text `#000` / asymmetric padding 12px 20px 12px 14px / radius 30px / shadow `rgba(78,50,23,0.04) 0 6px 16px`.
- White pill (secondary): bg `#fff`, 9999px, shadow `rgba(0,0,0,0.4) 0 0 1px, rgba(0,0,0,0.04) 0 4px 4px`.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: set display in Waldenburg weight 300; stack inset+outline+lift shadows under 0.1 opacity; give body Inter positive tracking; tint featured shadows warm `rgba(78,50,23,...)`.
- Don't: bold the headings — the wrong instinct is "make the H1 heavier to grab attention"; here 300 IS the grab. Don't use shadows over 0.1 opacity. Don't drop the inset half-pixel border. Don't apply negative tracking to body, and don't introduce a brand hue.

## Example component prompts
- "Hero on white: H1 Waldenburg 48px / 300 / line-height 1.08 / -0.96px in `#000`; subhead Inter 18px / 400 / 1.60 / +0.18px in `#4e4e4e`; black pill CTA + warm stone CTA `rgba(245,242,239,0.8)`, 30px radius, warm shadow `rgba(78,50,23,0.04) 0 6px 16px`."
- "Card: white, 20px radius, shadow `rgba(0,0,0,0.06) 0 0 0 1px, rgba(0,0,0,0.04) 0 2px 4px`; title Waldenburg 32px/300, body Inter 16px/1.50/+0.16px in `#4e4e4e`."
- "Uppercase CTA label: WaldenburgFH 14px / 700 / UPPERCASE / +0.7px."
