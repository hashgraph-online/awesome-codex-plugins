# Google — Design Tokens (loopy-native)
> Category: consumer · Signature: white paper, one tinted shadow, four primary hues used as punctuation

## Signature & atmosphere
Google feels like a clean sheet of paper under even light: a near-white canvas, generous air, and a single floating surface that casts a soft tinted shadow. The recognizable idea is Material restraint — color is rare and load-bearing, so the four brand hues (blue, red, yellow, green) read as punctuation, never decoration. Everything is rounded, legible, and a little friendly; the product disappears so the content and the one blue action stand out.

## Color (hex · --var · role)
- `#ffffff` `--bg` — page canvas; `#202124` `--fg` — text (warm near-black, not `#000`)
- `#1a73e8` `--primary` — Google Blue; primary CTA, links, active state (hover `#1765cc`, pressed `#185abc`)
- `#4285f4` `--accent` — lighter brand blue for fills on dark / focus tint
- `#5f6368` `--muted` — secondary text, icons; `#80868b` tertiary/placeholder
- `#dadce0` `--border` — hairline dividers and input outlines; `#f1f3f4` `--card` — quiet gray surface / chip fill
- `#d93025` `--destructive` — error (Google Red); `#1e8e3e` success (green); `#f9ab00` warning (yellow)
- Contrast: `--muted #5f6368` on white ≈ 5.9:1 (fine for body, tight at 12px). Brand red/yellow/green are status + logo only — never a CTA fill except blue.

## Typography
- Stack: `"Google Sans", "Product Sans", Roboto, Arial, sans-serif` for display/UI; `Roboto, Arial, sans-serif` for body; `"Roboto Mono", monospace` for code. Substitute: Inter / Roboto.
- Display 57px / 400 / 1.12 / -0.25px · Headline 36px / 400 / 1.22 · Title 22px / 500 / 1.27 · Body-large 16px / 400 / 1.50 / +0.15px · Body 14px / 400 / 1.43 / +0.25px · Label 14px / 500 / 1.43 / +0.10px (button)
- Signature: display/headline stay at weight 400 — the geometric Google Sans carries presence at regular weight; 500 is reserved for titles and button labels.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64; touch targets 48px min.
- Radius: 4px inputs/chips · 8px cards · 24px buttons (pill-ish) · 28px FAB · 50% avatars. Material 3 leans large radii.
- Depth = tinted ambient shadows, not gray drops: resting `0 1px 2px rgba(60,64,67,0.30), 0 1px 3px 1px rgba(60,64,67,0.15)`; raised `0 1px 3px rgba(60,64,67,0.30), 0 4px 8px 3px rgba(60,64,67,0.15)`. Shadow color is `#3c4043`, never pure black.
- Motion: 200–300ms standard easing `cubic-bezier(0.2, 0, 0, 1)`; ripple on press; transform/opacity only.

## Components (key)
- Primary CTA (filled): bg `#1a73e8` / text `#fff` / padding 0 24px, height 36–40px / radius 20px (pill) / no border / hover `#1765cc` + state-layer 8% white overlay / pressed `#185abc` / focus 2px `#1a73e8` ring offset.
- Search field (signature): white pill, radius 24px, 1px `#dadce0` border, resting shadow on focus `0 1px 6px rgba(32,33,36,0.28)` and border drops; leading search icon `#5f6368`, height 44–48px.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep display headlines at weight 400; use tinted `#3c4043` shadows; round buttons to a pill (20–24px); reserve red/yellow/green for status and logo.
- Don't: bold the display type to 600–700 — the geometric sans is designed to read at 400. Don't use pure-black `#000` shadows or text (use `#202124` / `#3c4043`). Don't fill a CTA in brand red or green — blue is the only action color. Don't square the buttons.

## Example component prompts
- "Hero on `#ffffff`: headline Google Sans 36px / 400 / 1.22 in `#202124`; body Roboto 16px / 400 / 1.50 / +0.15px in `#5f6368`; filled blue CTA `#1a73e8`, white label 14px/500, height 40px, radius 20px pill."
- "Material card on `#ffffff`, radius 8px, shadow `0 1px 2px rgba(60,64,67,.30), 0 1px 3px 1px rgba(60,64,67,.15)`; title 22px/500, body 14px/400/1.43 in `#5f6368`; chip row fills `#f1f3f4`, radius 4px."
- "Search pill: white, radius 24px, 1px `#dadce0`, leading icon `#5f6368`; on focus drop border + shadow `0 1px 6px rgba(32,33,36,.28)`."
