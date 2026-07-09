# OpenAI — Design Tokens (loopy-native)
> Category: ai-labs · Signature: monochrome restraint + generous near-black-on-white

## Signature & atmosphere
OpenAI reads as quiet institutional confidence: almost entirely black on white, with color held in reserve so the few moments it appears land hard. The recognizable idea is disciplined neutrality — a research-lab calm where typography and whitespace carry the page and nothing decorative competes for attention. It feels assured precisely because it refuses to shout.

## Color (hex · --var · role)
- `#ffffff` `--bg` — clean white; `#0d0d0d` `--fg` — near-black text (soft, not pure `#000`)
- `#f7f7f8` `--card` — faint gray surface, barely lifted from bg
- `#0d0d0d` `--primary` — black fill for primary CTAs (the brand is monochrome; black IS the action color)
- `#10a37f` `--accent` — signature teal-green; sparing use for product/brand moments only
- `#6e6e80` `--muted` — secondary text (cool neutral gray); `#8e8ea0` tertiary
- `#e5e5e5` `--border` — hairline divider; `#d9d9e3` emphasized
- `#e02e2e` `--destructive` — error red; focus ring `#0d0d0d` at 2px or teal where on-brand
- Contrast: `#6e6e80` on `#ffffff` ≈ 4.7:1 — OK for body, bump to `#0d0d0d` for small labels.

## Typography
- Stack: UI/display `"OpenAI Sans", "Söhne", system-ui, sans-serif`; code `ui-monospace, "SF Mono", Menlo, monospace`. One grotesque sans does almost everything — hierarchy via size, not family.
- Display 56px / 600 / 1.05 / -0.02em · H2 40px / 600 / 1.10 / -0.01em · H3 24px / 600 / 1.20 · Body 17px / 400 / 1.55 · Body-sm 15px / 400 / 1.50 · Label 13px / 500 / 1.30 / +0.01em
- Headings use a confident 600 with mild negative tracking; body stays plain 400.

## Spacing, radius, depth, motion
- Base 8px; scale 4/8/12/16/24/32/48/64/96px; section gaps 96px+ (lots of air).
- Radius scale 6 / 8 / 12 / 16px; pills (9999px) for tags and some buttons.
- Depth strategy: borders + faint surface shifts over shadows. Elevated card: `rgba(0,0,0,0.06) 0 1px 3px, rgba(0,0,0,0.04) 0 8px 24px`. Most containment is a 1px `#e5e5e5` line.
- Motion 120–200ms, ease-out; transform/opacity only.

## Components (key)
- Primary CTA: bg `#0d0d0d` / text `#ffffff` / padding 12px 20px / radius 9999px (pill) / no border / hover lighten to `#2d2d2d`, active scale 0.99, focus 2px `#0d0d0d` ring with 2px offset.
- Secondary button: bg `#ffffff` / text `#0d0d0d` / 1px `#d9d9e3` border / radius 9999px / hover bg `#f7f7f8`.
- Doc/article block: max-width ~720px reading column, body 17px/1.55, generous paragraph spacing — the lab-paper layout.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep the page monochrome and let whitespace do the work; reserve teal `#10a37f` for rare brand moments; use pill buttons in black.
- Don't: reach for a blue "tech" accent or gradient hero — the wrong instinct here is adding color for energy. Don't use pure `#000`. Don't stack heavy drop-shadows; a 1px border is the default containment. Don't crowd the reading column past ~720px.

## Example component prompts
- "Hero on `#ffffff`: H1 OpenAI Sans 56px / 600 / line-height 1.05 / -0.02em in `#0d0d0d`; subhead 17px / 400 / 1.55 in `#6e6e80`; black pill CTA `#0d0d0d` with white text, 9999px radius, 12px 20px padding."
- "Card on `#f7f7f8` with 1px `#e5e5e5` border, 12px radius, shadow `rgba(0,0,0,0.06) 0 1px 3px`; title 24px/600, body 15px/1.50 in `#6e6e80`."
- "Section label 13px / 500 / +0.01em in `#6e6e80`, no uppercase — quiet, not a meta-tag."
