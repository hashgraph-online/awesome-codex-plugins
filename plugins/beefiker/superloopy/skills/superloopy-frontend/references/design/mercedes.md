# Mercedes-Benz — Design Tokens (loopy-native)
> Category: luxury-auto-tooling · Signature: chrome-silver luxury — bespoke serifed-detail sans, deep black canvas

## Signature & atmosphere
Mercedes-Benz feels like polished metal under gallery light: a deep black-to-graphite canvas where silver and white carry the luxury, paced with the unhurried confidence of a marque that invented the category. The recognizable idea is restraint-as-status — the bespoke Corporate A/S typeface (with its faintly serifed detailing) handles every word, the palette refuses bright accent color, and depth comes from soft silver gradients rather than hard borders. Quietly expensive.

## Color (hex · --var · role)
- `#0C0C0C` `--bg` — primary dark canvas; alternating white `#FFFFFF` content sections
- `#FFFFFF` `--fg` — primary text on dark; `#0C0C0C` `--fg-on-light` on white sections
- `#00ADEF` `--primary` — Mercedes interactive blue, links and active states ONLY (never a large fill)
- `#B0B3B8` `--silver` — chrome-silver secondary text / hairline accents / metadata
- `#1A1A1C` `--surface` — raised card surface on the dark canvas
- `#6E7174` `--muted` — tertiary labels; `#33363A` `--border` — hairline divider on dark, `#E2E4E6` on light
- Gradient `--chrome`: `linear-gradient(#FFFFFF, #C7CACE)` for metallic emphasis. Contrast: `#B0B3B8` on `#0C0C0C` ≈ 8.5:1 — strong; the silver is legible, not just decorative.

## Typography
- Stack: `"MB Corpo A Title", "MB Corpo S Text", "Corporate A", Georgia, system-ui, sans-serif` — bespoke family with subtle serifed detailing; serif-ish fallback preserves the character.
- Display 56px / 400 / 1.15 / -0.2px · H2 36px / 400 / 1.20 · H3 24px / 500 / 1.25 · Body 16px / 400 / 1.60 · Body-lead 19px / 400 / 1.55 · Label 13px / 500 / 1.20 / +0.3px
- Active weights: 400 (display + body), 500 (UI emphasis). Display is light-by-comparison — weight 400 at 56px is the luxury voice; never bold the hero.

## Spacing, radius, depth, motion
- Base 8px; scale 8 · 16 · 24 · 32 · 48 · 64 · 80 · 120 (gallery pacing between modules).
- Radius scale 0 · 4 · 8px — gently softened, never pill. Cards at 8px, buttons at 4px.
- Depth strategy: soft silver gradients + dark/light alternation over hard shadows. One elevation `rgba(0,0,0,0.35) 0 8px 32px` for floating panels on dark; the chrome gradient does the luxury lifting. Motion 240–320ms ease-in-out, slow and weighted — transform/opacity only.

## Components (key)
- Primary CTA: bg `#FFFFFF` / text `#0C0C0C` / padding 14px 32px / radius 4px / no border / hover applies `--chrome` metallic gradient + subtle lift, active dims 6%, focus 2px `#00ADEF` ring.
- Secondary button: transparent / text `#FFFFFF` / 1px `#B0B3B8` border / radius 4px / hover border + text shift toward `#FFFFFF`, faint silver glow.
- Stat panel on dark: `#1A1A1C` surface, silver `#B0B3B8` UPPERCASE label, 36px/400 white figure, hairline `#33363A` top border.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep display at weight 400 (light-feeling at scale); let silver `#B0B3B8` carry secondary hierarchy; use the chrome gradient for metallic emphasis, not flat fills.
- Don't: reach for bold weight on the hero — the instinct that "luxury auto = heavy confident headline" inverts Mercedes; the calm 400 is the status signal.
- Don't: paint `#00ADEF` onto buttons or backgrounds — the reflex to use the brand blue as a CTA fill cheapens it; blue is for links and focus only, white is the action color.
- Don't: replace silver gradients with hard 1px borders everywhere — the metallic soft-edge IS the chrome luxury; borders alone read as a generic dark dashboard.

## Example component prompts
- "Hero on `#0C0C0C`: full-bleed vehicle photo, headline 56px MB Corpo A Title weight 400, -0.2px tracking, line-height 1.15, white text; white CTA with chrome-gradient hover, 4px radius."
- "Stat panel on `#1A1A1C`: UPPERCASE 13px/500/+0.3px `#B0B3B8` label, 36px/400 `#FFFFFF` figure, 1px `#33363A` top border, 8px radius."
- "Primary button: `#FFFFFF` bg, `#0C0C0C` text, 14px 32px padding, 4px radius; hover swaps to `linear-gradient(#FFFFFF,#C7CACE)` with a 2px lift in 280ms ease-in-out."
