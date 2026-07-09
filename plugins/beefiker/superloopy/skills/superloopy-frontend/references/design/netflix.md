# Netflix — Design Tokens (loopy-native)
> Category: consumer · Signature: pure-black cinema, one red, artwork is the only color

## Signature & atmosphere
Netflix feels like a dark theater the moment the lights drop: the background is true black so poster artwork glows like a screen. The one recognizable idea is the single saturated red — used for the logo, the play affordance, and the sign-in CTA, and nowhere else. There is no chrome competing with content; the UI is a quiet grid of thumbnails that swell on hover, and every neutral is a cool gray pulled toward black.

## Color (hex · --var · role)
- `#000000` `--bg` — page/canvas (true black, intentional); `#141414` `--surface` — app shell / rows behind artwork
- `#ffffff` `--fg` — primary text; `#b3b3b3` `--muted` — secondary copy, metadata; `#808080` tertiary/disabled
- `#e50914` `--primary` — Netflix Red; CTA fill, logo, focus accent (hover `#f6121d`, pressed `#c00812`)
- `#181818` `--card` — tile/menu surface a step above black; `#232323` `--surface-2` — hover row / dropdown
- `#333333` `--border` — input outline / divider on dark; `#564d4d` muted border
- `#46d369` success (plan confirmation) · `#e87c03` warning · `#e50914` doubles as destructive
- Contrast: `--muted #b3b3b3` on `#000` ≈ 9:1; keep body ≥ 14px. Red is functional (play / sign in) — never a background wash.

## Typography
- Stack: `"Netflix Sans", "Helvetica Neue", Helvetica, Arial, sans-serif`. Substitute: Inter or Helvetica Neue.
- Display 56px / 700 / 1.10 / -0.5px (billboard) · H1 32px / 700 / 1.20 · H2 24px / 500 / 1.25 · Body 18px / 400 / 1.50 · UI 16px / 400 / 1.40 · Label 14px / 500 / 1.30 · Caption 13px / 400 (metadata, rating)
- Signature: marketing display goes heavy (700) and big for cinematic punch, but in-app UI stays calm at 400–500. Two registers, one family.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 24 · 32 · 48 · 60; rows are dense, gutters tight so more artwork fits.
- Radius: 4px tiles/cards · 4px inputs · 4px buttons (Netflix is square-ish, low radius) · 50% avatars. The brand is sharp, not pill-soft.
- Depth = scale + dark gradient scrims, not drop shadows: tile hover `scale(1.08)` lifts it forward; artwork text gets `linear-gradient(rgba(0,0,0,0) 0%, rgba(0,0,0,0.7) 100%)` bottom scrim. Modals use `rgba(0,0,0,0.7)` backdrop.
- Motion: hover scale 300ms ease, billboard crossfade ~400ms; transform/opacity only.

## Components (key)
- Primary CTA: bg `#e50914` / text `#fff` / padding 12px 24px / radius 4px / weight 500 / hover `#f6121d` / pressed `#c00812` / focus 2px white ring. Large hero variant: 16px 32px, 18px label.
- Title tile (signature): artwork fills a 16:9 (or 2:3 poster) card, radius 4px; on hover scale 1.08 + reveal metadata row over a bottom scrim; sibling tiles slide aside; play/add icons appear as circular outlined buttons.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: use true `#000` as canvas; keep radii low (4px) and corners sharp; let artwork supply all the color; drive depth with hover scale + gradient scrims.
- Don't: round buttons into pills — Netflix is squared at 4px, the soft-pill instinct is wrong here. Don't lighten the background to a charcoal "dark mode" gray — the pure black is the cinema. Don't use red as a decorative fill or section background — it's play/CTA/logo only. Don't add box-shadows to tiles; scale is the elevation.

## Example component prompts
- "Billboard hero on `#000`: full-bleed 16:9 artwork with bottom scrim `linear-gradient(rgba(0,0,0,0), rgba(0,0,0,.7))`; title Netflix Sans 56px/700/-0.5px white; synopsis 18px/400/1.50 in `#b3b3b3`; red `#e50914` play CTA, white label, radius 4px, padding 12px 24px."
- "Title row: horizontal scroll of 2:3 poster tiles radius 4px on `#141414`; hover scale(1.08) 300ms, reveal metadata over scrim, neighbors shift; circular outlined play + add buttons."
- "Sign-in card on `#000`: inputs `#333` border on `#141414`, white text, radius 4px; red `#e50914` submit, 16px/500."
