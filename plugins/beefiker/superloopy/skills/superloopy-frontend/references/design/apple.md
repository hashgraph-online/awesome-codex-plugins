# Apple — Design Tokens (loopy-native)
> Category: consumer · Signature: chrome disappears so the object is the only thing on stage

## Signature & atmosphere
The interface is engineered to vanish. Broad neutral fields and quiet typography do nothing but frame the product photograph, which carries all the expressive weight. The one recognizable move is the binary rhythm — a deep black gallery scene cuts to a pale gray field, and that contrast (not shadow, not color) does the layering. Restraint reads as confidence: a single blue is the only thing allowed to point at an action.

## Color (hex · --var · role)
- `#000000` `--bg-dark` — immersive hero canvas; `#f5f5f7` `--bg` — pale light field (not white) for feature bands; `#ffffff` `--card` — retail/list surfaces
- `#1d1d1f` `--fg` — near-black ink, primary text on light (never pure `#000` for body)
- `#0071e3` `--primary` — action fill + focus signal; `#0066cc` `--link` — inline link tuned for body; `#2997ff` `--link-on-dark` — brighter link on dark scenes
- `#6e6e73` `--muted` — secondary copy; `#d2d2d7` `--border` — soft hairline; `#86868b` `--border-strong` — field outlines in configurators
- `#272729`–`#2a2a2c` `--surface-dark-1..4` — graphite stepping for dark controls
- Contrast: `--fg` on `--bg` ≈ 16:1; `--primary` on white ≈ 4.6:1 — keep blue text ≥ 17px or pair with white fill.

## Typography
- Stack: `"SF Pro Display"` for display/headlines, `"SF Pro Text"` for UI/body (fallbacks Helvetica Neue, Arial). Substitute: Inter Tight (display) + Inter (text).
- Hero 56/600/1.07/-0.28px · Section 48/500/1.08/-0.14px · Product H2 40/600/1.10 · H3 28/600/1.14/0.2px · Body 17/400/1.47/-0.37px · Body-emphasis 17/600/1.24 · Label 14/400-600/1.3/-0.22px · Micro 12/400/1.0/-0.12px
- 600 is the dominant emphasis weight; 700 is rare; 300 appears only on large lines for contrast.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 20 · 24 · 40 · 64; commerce sections compress to 8–20px intervals
- Radius by class: control 8–12px · card/panel 16–18px · spotlight shell 28–36px · capsule CTA 980px · circle 50% — never one radius for all
- Depth = tonal contrast + surface stepping, not shadow stacks. Light: border containment (`--border`). Dark: graphite steps (`--surface-dark-1` → `-4`). Shadow only as a faint card lift `0 2px 8px rgba(0,0,0,.08)`.
- Motion: 200–400ms ease; press shrinks scale slightly; transform/opacity only.

## Components (key)
- Primary CTA: bg `#0071e3` / text `#ffffff` / padding 8px 16px / radius 8px / no border. Dark variant: bg `#1d1d1f`, white text. Capsule variant: same fills, radius 980px. Focus: 4px `#0071e3` ring; active: scale 0.98.
- Configurator option tile: white card, 12–18px radius, 1px `#86868b` border, 17px body, circular `50%` selection control; selected = `#0071e3` ring + fill dot.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: let the photograph be the loudest layer; reserve blue strictly for actions and links.
- Don't: pure `#000000` for body text — that's `#1d1d1f`; the only true black is the hero canvas.
- Don't: flatten every corner to one radius — Apple runs a deliberate radius ladder (8 → 18 → 980).
- Don't: add a second accent color or a glow — if everything is blue, hierarchy collapses.

## Example component prompts
- "Product hero on `#000000`: SF Pro Display 56px/600 headline at -0.28px tracking, 17px/400 `#86868b` subcopy, two capsule CTAs (980px radius) — `#0071e3` fill and `#1d1d1f` fill, white text."
- "Feature band on `#f5f5f7`: image-first card at 18px radius, 17px/400 `#1d1d1f` body, faint `0 2px 8px rgba(0,0,0,.08)` lift, no border."
- "Configurator panel on `#ffffff`: 12px-radius option tiles, 1px `#86868b` borders, 50% circular selectors, selected tile gets a `#0071e3` ring."
