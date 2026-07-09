# Spotify — Design Tokens (loopy-native)
> Category: consumer · Signature: a theater of near-black where only album art and one green glow

## Signature & atmosphere
Every surface is a shade of charcoal so the UI recedes and the content — album art, podcast covers, playlist images — becomes the only source of color. The recognizable idea is "content-first darkness": depth is built from shade variation (`#121212` → `#1f1f1f`), never light surfaces. The lone functional accent is Spotify Green (`#1ed760`), reserved for the play button and active state. Pill-and-circle geometry plus heavy shadows make it feel like a premium audio device.

## Color (hex · --var · role)
- `#121212` `--bg` — deepest page background; `#181818` `--surface` — cards/sidebar; `#1f1f1f` `--surface-2` — interactive button surfaces
- `#ffffff` `--fg` — primary text; `#b3b3b3` `--muted` — secondary text, inactive nav, dividers
- `#1ed760` `--primary` — brand green, play/active/CTA only (`#1db954` border variant)
- `#252525`/`#272727` `--card` — elevated card; `#4d4d4d` `--border`; `#7c7c7c` `--border-muted` — outlined buttons
- `#f3727f` `--destructive` · `#ffa42b` `--warning` · `#539df5` `--info`
- Contrast: `--fg` on `--bg` ≈ 17:1; `--muted` on `--bg` ≈ 7:1 (keep ≥ 14px). Green is for fills/icons, not body text.

## Typography
- Stack: `"SpotifyMixUITitle"` (titles) + `"SpotifyMixUI"` (UI/body), from the CircularSp family with a global script fallback chain (Arab, Hebr, Cyrl, Grek, Deva, CJK). Substitute: Circular Std or Inter.
- Section title 24/700 · Feature heading 18/600/1.30 · Body-bold 16/700 · Body 16/400 · Button 14/700/0.14px · Nav-active 14/700 · Nav-inactive 14/400 · Small 12/400 · Micro 10/400
- Signature: button labels are UPPERCASE with wide tracking 1.4–2px — a systematic "label voice" distinct from content.
- Weight is a bold/regular binary: 700 or 400, 600 used sparingly. Range is compact (10–24px) — this is an app, not a magazine.

## Spacing, radius, depth, motion
- Base 8px; scale 2 · 4 · 6 · 8 · 12 · 16 · 20; dense by intent — dark background gives visual rest without large gaps.
- Radius: badge 2px · input/small 4px · album/card 6–8px · panel 10–20px · pill 500px · full pill 9999px · circle 50% (play, avatar)
- Depth = heavy shadows that read on dark. Card hover `rgba(0,0,0,.3) 0 8px 8px`; dialog/menu `rgba(0,0,0,.5) 0 8px 24px`; input inset combo `rgb(18,18,18) 0 1px 0, rgb(124,124,124) 0 0 0 1px inset`.
- Motion: subtle background lightening on hover; scale on press; transform/opacity only.

## Components (key)
- Primary pill (nav/secondary): bg `#1f1f1f` / text `#ffffff` or `#b3b3b3` / padding 8px 16px / radius 9999px. Outlined: transparent, 1px `#7c7c7c`, white text.
- Circular play: bg `#1ed760` / icon `#000000` / padding 12px / radius 50% — the one green moment.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: build depth from shade variation and lean on heavy shadows (0.3–0.5 opacity) that are visible on dark.
- Don't: use light surfaces for primary UI — the dark immersion is the product, not a theme toggle.
- Don't: use green decoratively or as a background — it's strictly functional (play/active/CTA).
- Don't: use thin/subtle shadows — on near-black they vanish; and don't relax line-heights, the type is dense.

## Example component prompts
- "Dark card: `#181818` bg, 8px radius. Title 16px SpotifyMixUI 700 white, subtitle 14px/400 `#b3b3b3`; hover shadow `rgba(0,0,0,.3) 0 8px 8px`."
- "Pill button: `#1f1f1f` bg, white text, 9999px radius, 8px 16px padding, 14px/700 UPPERCASE, 1.4px tracking."
- "Circular play button: `#1ed760` bg, `#000000` icon, 50% radius, 12px padding; search input `#1f1f1f`, 500px radius, inset border `rgb(124,124,124) 0 0 0 1px inset`."
