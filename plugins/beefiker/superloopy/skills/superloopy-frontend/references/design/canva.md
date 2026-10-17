# Canva — Design Tokens (loopy-native)
> Category: productivity/saas · Signature: blue→purple gradient optimism, friendly rounded chrome

## Signature & atmosphere
Canva feels like creativity with the intimidation removed — bright, encouraging, and visibly "anyone can do this." The recognizable idea is its blue-to-purple brand gradient, used as a hero wash and on the headline accent, signaling playful possibility over professional austerity. Everything is rounded and roomy; the canvas stays white so user-made designs can be the color, while the chrome carries the gradient and a single confident purple-blue.

## Color (hex · --var · role)
- `#ffffff` `--bg` — workspace/page background; `#0d1216` `--fg` — foreground (near-black with cool cast, not pure black)
- `#8b3dff` `--primary` — Canva purple; primary buttons, brand chrome
- `#7700c2` `--primary-active` — pressed purple
- `#00c4cc` `--accent-teal` — secondary brand teal; highlights, illustrations
- `#01a3a4` `--accent-teal-deep` — teal on light surfaces (text/icon contrast)
- gradient `--brand-gradient` — `linear-gradient(90deg, #6420ff 0%, #00c4cc 100%)` (blue-purple → teal); hero washes + headline text-fill
- `#0d1216cc` `--muted` — secondary text (~80% ink); `#7a7a7a` tertiary
- `#e2e5e9` `--border` — light hairline divider
- `#f2f3f5` `--muted-surface` — alternating band / panel background

## Typography
- Stack: `"Canva Sans", "Noto Sans", -apple-system, system-ui, sans-serif` — geometric-humanist, rounded terminals; intent is friendly and unintimidating.
- Display 64/700/1.05/-1.5px · H1 48/700/1.10/-1px · H2 34/600/1.20 · CardTitle 22/600/1.25 · Body 18/400/1.55 · BodySm 16/400/1.50 · Nav 16/600/1.30 · Label 13/600/1.3/+0.2px
- Display weight is bold (700) but the rounded letterforms keep it warm; gradient text-fill on a hero word is a signature move.

## Spacing, radius, depth, motion
- Base 8px (4px micro); scale 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96px; section gaps 64–96px.
- Radius: **generous and friendly** — 8px inputs · 12px buttons · 16px cards · 24px feature media · 9999px pills/avatars.
- Depth strategy: **soft single shadows + light borders**. Card `0 2px 8px rgba(13,18,22,0.08)`; hover lifts `0 8px 24px rgba(13,18,22,0.12)`; floating panels get a slightly larger soft shadow. No harsh edges.
- Motion 150–250ms ease-out; hover scale `1.02` on cards, buttons brighten; transform/opacity only.

## Components (key)
- Primary CTA: bg `#8b3dff` / text `#ffffff` / padding 12px 24px / radius 12px / no border / weight 600. Hover → `#7700c2`; active → darken + `scale(0.98)`; focus → 3px `rgba(139,61,255,0.3)` ring.
- Gradient CTA (hero): fill `linear-gradient(90deg,#6420ff,#00c4cc)`, white text, 9999px or 12px radius — the "Start designing" hero button.
- Tool tile: white bg, 16px radius, soft shadow, illustrative icon, 16px/600 label, hover lifts + scale `1.02`.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: use the blue-purple gradient (`#6420ff → #00c4cc`) as the signature on hero washes and one headline word; keep radii generous (12–24px) and shadows soft.
- Don't: render the whole UI in flat single-tone purple and call it Canva — the *gradient* is the identity; a flat purple page loses the optimism.
- Don't: tighten corners to 4–6px "pro tool" geometry or use hard drop shadows — the friendly, rounded, soft-shadow feel is what removes intimidation. Avoid pure `#000`/`#fff` ink.

## Example component prompts
- "Hero on `#ffffff` (or faint gradient wash): H1 Canva Sans 48px / weight 700 / 1.10 / -1px in `#0d1216`, with one word filled by `linear-gradient(90deg,#6420ff,#00c4cc)`; subhead 18px/400/1.55 in `#0d1216cc`; gradient CTA, white text, 12px radius, 12px 24px padding."
- "Tool tile grid: white cards, 16px radius, shadow `0 2px 8px rgba(13,18,22,0.08)`, illustrative icon, label 16px/600, hover `scale(1.02)` + `0 8px 24px rgba(13,18,22,0.12)`."
- "Purple CTA `#8b3dff`, white text 600, 12px radius, 12px 24px padding, hover `#7700c2`, focus ring 3px `rgba(139,61,255,0.3)`."
