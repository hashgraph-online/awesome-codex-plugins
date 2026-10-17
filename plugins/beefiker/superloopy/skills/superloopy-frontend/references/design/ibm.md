# IBM — Design Tokens (loopy-native)
> Category: brand-web-media · Signature: Carbon grid rigor, one blue, light-weight display, zero-radius rectangles

## Signature & atmosphere
IBM reads like an engineering spec that learned to be elegant: a stark white sheet, near-black text, and a single electric blue that never wavers. The recognizable idea is restraint-as-confidence — display headlines drop to weight 300 so the type whispers while the content carries corporate gravity, and every corner stays a sharp 0px rectangle. Depth is a stack of grays, not a stack of shadows; the whole surface behaves like a thin skin over a strictly tokenized (`--cds-*`) system.

## Color (hex · --var · role)
- `#ffffff` `--bg` — page canvas; `#161616` `--fg` — Gray 100 text, dark masthead/footer (warm-neutral near-black, not `#000`)
- `#0f62fe` `--primary` — IBM Blue 60: the sole chromatic hue — buttons, links, focus, active rails
- `#0353e9` primary-hover; `#002d9c` Blue 80 active/pressed; `#0043ce` Blue 70 link-hover; `#edf5ff` Blue 10 selected-row tint
- `#525252` `--muted` — Gray 70 secondary text (≈7:1 on white); `#6f6f6f` Gray 60 placeholder/disabled
- `#c6c6c6` `--border` — Gray 30 dividers/input underline; `#e0e0e0` Gray 20 subtle outline
- `#f4f4f4` `--card` — Gray 10 layer-01 surface; `#e8e8e8` clickable-card hover
- `#da1e28` `--destructive` — Red 60; `#24a148` success; `#f1c21b` warning
- Note: ships a real semantic palette (it is a dashboard system), but core marketing UI is monochrome + one blue. A second accent hue is a defect.

## Typography
- Stack: `"IBM Plex Sans", "Helvetica Neue", Arial, sans-serif`; mono `"IBM Plex Mono", Menlo, monospace`; rare serif `"IBM Plex Serif"`
- Display-01 60px / 300 / 1.17 / 0 · Display-02 48px / 300 / 1.17 · Heading-01 42px / 300 / 1.19 (light at scale = the signature)
- H2 32px / 400 / 1.25 · H3 24px / 400 / 1.33 · Card title 20px / 600 / 1.40
- Body 16px / 400 / 1.50 · Body-emphasis 16px / 600 / 1.50 · Compact 14px / 400 / 1.29 / +0.16px
- Caption 12px / 400 / 1.33 / +0.32px · Code 14px IBM Plex Mono / 400 / +0.16px
- Three weights only — 300 display, 400 body, 600 emphasis; weight 700 does not exist in the scale. Micro-tracking lives only at 14px (+0.16) and 12px (+0.32), never on display.

## Spacing, radius, depth, motion
- Base 8px (Carbon 2x grid); component scale 2 · 4 · 8 · 12 · 16 · 24 · 32 · 40 · 48px; layout scale 16 · 24 · 32 · 48 · 64 · 80 · 96 · 160px; section rhythm 48px (hero 80–96px)
- Radius: `0` on buttons, inputs, cards, tiles (the dominant treatment); `24px` only on pill tags; `50%` avatars — that is the entire scale
- Depth strategy: tonal layering, not shadows. Tier by background value — `#ffffff` → `#f4f4f4` → `#e0e0e0`. Shadows reserved for true floats: dropdowns/modals `0 2px 6px rgba(0,0,0,0.3)`. Active input/tab = `2px solid #161616` bottom-border.
- Motion: ~110ms `cubic-bezier(0,0,0.38,0.9)` (Carbon productive ease); state changes swap token color, no lift.

## Components (key)
- Primary CTA: bg `#0f62fe` / text `#ffffff` / asymmetric padding 14px 63px 14px 15px (trailing-icon room) / radius 0 / height 48px / hover `#0353e9` / active `#002d9c` / focus `2px solid #0f62fe` inset + `1px solid #ffffff` inner ring
- Carbon input (bottom-border): bg `#f4f4f4` / text `#161616` / padding 0 16px / height 40px / no side or top border / `2px solid transparent` bottom that becomes `#161616`, focus `#0f62fe`, error `#da1e28` — never a fully boxed field

## Do / Don't (anti-convention — name the wrong instinct)
- Do: set display 42px+ at weight 300; keep 0px radius on buttons/inputs/cards; create depth by layering gray surfaces; use one blue everywhere.
- Don't: round corners — the universal "soften it" instinct is the most common Carbon violation; 0px is law (only pill tags + avatars escape).
- Don't: reach for weight 700 on a headline — the scale stops at 600, and display is *lighter* not heavier (300).
- Don't: drop a `box-shadow` to lift a card, or add a second accent hue — flat tonal layering and one blue are the system.

## Example component prompts
- "Hero on `#ffffff`: H1 IBM Plex Sans 60px / weight 300 / line-height 1.17 in `#161616`; subhead 16px/400/1.50 in `#525252`, max-width 640px; Blue CTA `#0f62fe` fill, white text, 0px radius, 48px tall, padding 14px 63px 14px 15px."
- "Carbon field: `#f4f4f4` bg, 0px radius, 40px tall, 16px horizontal padding; label above 12px/400/+0.32px in `#525252`; bottom-border `2px solid transparent` → `#0f62fe` on focus; placeholder `#6f6f6f`."
- "Tile grid on `#f4f4f4`: cards at 0px radius, 16px padding, no shadow; title 20px/600/1.40 `#161616`, body 14px/400/+0.16px `#525252`; hover shifts bg to `#e8e8e8`, arrow icon bottom-right."
