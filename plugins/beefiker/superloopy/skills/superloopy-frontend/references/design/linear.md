# Linear — Design Tokens (loopy-native)
> Category: dev-tools · Signature: information emerging from near-black through calibrated white-opacity steps

## Signature & atmosphere
Linear feels like instrument-panel precision rendered in the dark. The whole surface is near-black, and everything you see — text, borders, cards — is a measured step of white opacity rising out of that void rather than a separate color. The one recognizable idea: hierarchy is built from luminance, not chroma, with a single indigo-violet reserved as the only chromatic note.

## Color (hex · --var · role)
- `#08090a` `--bg` — marketing background (not pure black; faint cool cast); `#f7f8f8` `--fg` — foreground (warm-white, never `#ffffff` — softer on dark)
- `#0f1011` `--panel` — sidebar/panel; `#191a1b` `--card` — elevated surface
- `#5e6ad2` `--primary` — brand indigo for CTA fills; `#7170ff` `--accent` — interactive violet (links, active); `#828fff` `--accent-hover`
- `#8a8f98` `--muted` — placeholder/metadata; `#62666d` — most-subdued (timestamps, disabled)
- `rgba(255,255,255,0.08)` `--border` — standard hairline; `rgba(255,255,255,0.05)` — subtle hairline (the default divider)
- `#27a644` / `#10b981` `--success` — status dots only
- Contrast: `--muted` on `--bg` clears AA for large text; reserve `#62666d` for non-essential text.

## Typography
- Stack: `Inter Variable` (UI + display), `Berkeley Mono` for code/technical labels. Set `font-feature-settings: "cv01","ss03"` globally — these alternates ARE the Linear letterform.
- Display 48px/510/1.0/-1.056px · Display-XL 72px/510/1.0/-1.584px · H1 32px/400/1.13/-0.704px · H2 24px/400/1.33/-0.288px · H3 20px/590/1.33/-0.24px
- Body 16px/400/1.5/0 · Body-emphasis 16px/510/1.5 · Small 15px/400/1.6/-0.165px · Label 13px/510/1.5/-0.13px
- Weight system is three-tier: 400 read, 510 emphasize, 590 announce. The 510 between-weight is the signature.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 24 · 32 (with 7/11px micro-optical nudges where alignment demands).
- Radius: 6px buttons/inputs · 8px cards · 12px panels · 9999px pills · 50% icon buttons.
- Depth = tonal-shift, not shadow. Surfaces climb by raising white-opacity (`0.02 → 0.04 → 0.05`); borders are the structure. Inset `rgba(0,0,0,0.2) 0 0 12px inset` for recessed panels. Reserve real shadow stacks for popovers/command palette only.
- Motion: 120–200ms, ease-out; transform/opacity only.

## Components (key)
- Primary CTA: bg `#5e6ad2` / text `#ffffff` / padding 8px 16px / radius 6px / no border. Hover lighten toward `#828fff`; active darken; focus ring via layered shadow.
- Ghost button (the workhorse): bg `rgba(255,255,255,0.02)` / text `#e2e4e7` / 6px radius / `1px solid rgba(255,255,255,0.08)`. Near-transparent fill is the rule.
- Command palette: `#191a1b` bg, `1px solid rgba(255,255,255,0.08)`, 12px radius, multi-layer black shadow stack; 16px/400 input, 13px/510 result labels.

## Do / Don't (anti-convention)
- Do: build elevation by stepping the background's white-opacity up; let borders carry structure.
- Don't: reach for weight 600–700 on display — 510 is the voice; bold reads as a different brand.
- Don't: use pure `#ffffff` text or solid opaque borders on dark — warm-white `#f7f8f8` and translucent hairlines are non-negotiable.
- Don't: drop the `"cv01","ss03"` features — without them it's generic Inter, not Linear's.

## Example component prompts
- "Hero on `#08090a`: headline 48px Inter Variable weight 510, line-height 1.0, letter-spacing -1.056px, color `#f7f8f8`, font-feature-settings 'cv01','ss03'. Subtitle 18px/400/1.6 in `#8a8f98`. Indigo CTA `#5e6ad2`, 6px radius, 8px 16px; plus ghost button `rgba(255,255,255,0.02)` bg, `1px solid rgba(255,255,255,0.08)`."
- "Card: `rgba(255,255,255,0.02)` bg, `1px solid rgba(255,255,255,0.08)`, 8px radius, NO drop shadow. Title 20px/590 letter-spacing -0.24px `#f7f8f8`; body 15px/400 `#8a8f98` letter-spacing -0.165px."
