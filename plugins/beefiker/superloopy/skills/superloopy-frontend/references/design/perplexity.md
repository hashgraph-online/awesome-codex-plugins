# Perplexity — Design Tokens (loopy-native)
> Category: ai-labs · Signature: teal-petrol accent + answer-engine clarity, source-cite rhythm

## Signature & atmosphere
Perplexity feels like a research answer rendered with calm precision: a near-neutral canvas where a single petrol-teal accent organizes everything and inline citations give the page its rhythm. The recognizable idea is answer-engine clarity — typography tuned for dense, scannable reading, with the teal acting as a consistent "this is a link/source" signal. It reads trustworthy because it looks like it shows its work.

## Color (hex · --var · role)
- `#ffffff` `--bg` (light) / `#091717` dark-mode bg — deep petrol near-black; `#13343b` `--fg` — petrol ink, softer than `#000`
- `#f7f8f8` `--card` — faint cool surface; dark `#1f2a2a`
- `#20808d` `--primary` — Perplexity teal/petrol; links, CTAs, brand signal
- `#13a4b4` `--accent` — brighter teal for hover/active and dark-mode emphasis
- `#64726f` `--muted` — cool slate secondary text; `#8a9a96` tertiary
- `#e3e6e4` `--border` — cool hairline; dark `#2a3636`
- `#c0392b` `--destructive`. Contrast: teal `#20808d` on white ≈ 4.6:1 — fine for links/large text, darken to `#13343b` for small body.

## Typography
- Stack: UI/display `"FK Grotesk", "Inter", system-ui, sans-serif`; reading serif optional `"Tiempos", Georgia, serif` for long answers; code `ui-monospace, "SF Mono", monospace`.
- Display 48px / 600 / 1.10 / -0.01em · H2 32px / 600 / 1.15 · H3 22px / 600 / 1.25 · Body 16px / 400 / 1.65 (tuned for long answers) · Body-sm 14px / 400 / 1.55 · Citation 12px / 500 / 1.30 (superscript-style source chips) · Label 13px / 500 / +0.01em
- Body line-height runs generous (1.65) because the product is reading-heavy.

## Spacing, radius, depth, motion
- Base 8px; scale 4/8/12/16/20/24/32/48px; comfortable but compact (answer density over magazine air).
- Radius scale 6 / 8 / 12 / 16px; citation chips 6px or pill.
- Depth strategy: borders + faint surface tint over shadows. Card: 1px `#e3e6e4` border, optional `rgba(0,0,0,0.05) 0 1px 2px`. Dark mode leans on petrol surface steps, not shadow.
- Motion 120–180ms ease-out; transform/opacity only.

## Components (key)
- Primary CTA: bg `#20808d` / text `#ffffff` / padding 10px 18px / radius 12px / hover `#13a4b4`, active scale 0.99, focus 2px `#20808d` ring 2px offset.
- Ask/search bar (signature): full-width pill or 16px-radius input, 1px `#e3e6e4` border, teal focus ring, trailing send button in `#20808d`.
- Source citation chip: inline 12px/500 chip, faint `#f7f8f8` bg, teal `#20808d` number, 6px radius — the rhythm element.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: use one petrol-teal `#20808d` as the single accent across links/CTAs/citations; tune body to 1.65 line-height for long answers; treat the search/ask bar as the hero object; render citations as inline chips.
- Don't: add a second bright accent or a purple/blue "AI" gradient — the wrong instinct is decorating an answer engine. Don't tighten body line-height below 1.5 (reading product). Don't bury citations in plain text; the chip rhythm is the identity. Don't use pure `#000`/`#fff` in dark mode — petrol-tinted neutrals.

## Example component prompts
- "Hero on `#ffffff`: H1 FK Grotesk 48px / 600 / 1.10 / -0.01em in `#13343b`; subhead 16px / 400 / 1.65 in `#64726f`; large ask bar with 16px radius, 1px `#e3e6e4` border, teal `#20808d` send button."
- "Answer card: white, 1px `#e3e6e4` border, 12px radius; body 16px/1.65 in `#13343b`; inline citation chips 12px/500, `#f7f8f8` bg, `#20808d` number, 6px radius."
- "Dark mode panel on `#091717`: body in `#dfe8e6`, links `#13a4b4`, surface step `#1f2a2a`, border `#2a3636`."
