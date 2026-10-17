# Shopify — Design Tokens (loopy-native)
> Category: consumer · Signature: a keynote in the dark — featherweight type etched in light, one neon pulse

## Signature & atmosphere
The marketing surface stages commerce like a cinematic premiere: an abyss of near-black carrying a faint forest-green undertone, with each section scrolling like its own keynote slide. The recognizable idea is the paradox of monumental, featherweight type — 96px headlines at weight 330 that feel etched in light rather than printed in ink. Color is rationed to near-zero; Shopify Neon Green (`#36F4A4`) pulses only on focus rings and accents, bioluminescent against the void.

## Color (hex · --var · role)
- `#000000` `--bg` — true-black root; `#02090A` `--card` — card surface (green undertone); `#061A1C` `--surface` — section bg; `#102620` `--surface-2` — elevated/header
- `#ffffff` `--fg` — only text color that matters on dark; `#a1a1aa` `--muted` — the quiet voice; `#71717a` `--muted-2`; `#52525b`/`#3f3f46` `--disabled`/`--divider`
- `#36f4a4` `--primary` — Neon Green, focus + critical accent only; `#c1fbd4` Aloe / `#d4f9e0` Pistachio — soft atmospheric green washes
- `#1e2c31` `--border` — barely-visible card boundary on dark
- Contrast: `--fg` on `--bg` = 21:1; `--muted` on `--bg` ≈ 9:1. Neon green is for 2px rings/small accents, never body text.

## Typography
- Stack: `"NeueHaasGrotesk"` (display, refined Helvetica descendant) + `"Inter Variable"` (body), `ss03` OpenType feature on both. Substitute: Helvetica Now / Inter.
- Display variable weights live between stops: 330 / 360 / 400 / 500 / 750.
- Display 96/330/0.96 · H1 70/330/1.00 · H2 55/330/1.16 · H4 32/360/1.14/0.32px · Body-large 20/500/1.40 · Body 18/400/1.56 · Body-medium 18/550/1.56 · Button 16/400 · Nav 18/500/0.72px · Caption 14/500/0.28px · Label 12/400/0.72px uppercase
- Where most SaaS shouts in bold, Shopify whispers at scale — display stays 330–400.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 24 · 28 · 32 · 40 · 64; section gaps run 80–120px of pure black for keynote pacing.
- Radius: tag 4px · card/input 8px · featured/non-pill button 12px · top-rounded 20px (20 20 0 0) · pill 9999px
- Depth = multi-layer stacked shadows + inset glow, never a single drop. Resting card: `rgba(0,0,0,.1) 0 0 0 1px, …0 2px 2px, …0 4px 4px, …0 8px 8px` + `rgba(255,255,255,.03) 0 1px 0 inset` (top-edge glow). On dark, shadow reads as ambient occlusion.
- Motion: box-shadow 300ms ease, transform 200ms ease; focus `0 0 0 2px #36f4a4`.

## Components (key)
- Primary CTA: bg `#ffffff` / text `#000000` / 2px transparent border / radius 9999px / padding 12px 26px 12px 16px (asymmetric). Focus: 2px `#36f4a4` ring. Ghost variant: transparent, 2px white border, fills white on hover.
- Feature card: `#02090A` bg, 1px `#1e2c31` border, 12px radius, the multi-layer shadow + inset white glow, 32/360 white heading, 18/400 `#a1a1aa` body.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep display type at weight 330–400 — the ethereal lightness is the entire signature.
- Don't: reach for weight 600–700 on display because "headlines should be bold" — heavy weight kills the etched-in-light effect.
- Don't: introduce any warm color (orange/red/yellow) — the palette is strictly cool greens, teals, neutrals.
- Don't: use a single box-shadow — flatness gives it away; the stacked layers + inset glow are the system.

## Example component prompts
- "Hero on `#000000`: NeueHaasGrotesk 96px/330 white headline, 20px/500 `#a1a1aa` subtitle, two 9999px pills — white-filled (black text) and ghost (2px white border)."
- "Feature card on `#02090A`: 1px `#1e2c31` border, 12px radius, multi-layer shadow (1px ring + 2/4/8px blur at 10% black + `rgba(255,255,255,.03)` inset), 32px/360 white heading, 18px/400 `#a1a1aa` body."
- "Sticky nav: transparent, becomes `#102620` on scroll, white logo left, 18px/500 nav links at 0.72px tracking, white pill 'Start for free' right."
