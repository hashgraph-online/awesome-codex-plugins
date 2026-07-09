# Warp — Design Tokens (loopy-native)
> Category: dev-tools · Signature: warm campfire-dark with single-weight Matter and zero accent color

## Signature & atmosphere
Warp markets a terminal like a lifestyle brand: the dark is warm — charred-wood and dark-earth tones, never the cold blue-black other dev tools default to — and text is a barely-cream parchment that makes the canvas feel inviting rather than austere. The recognizable move is restraint through warmth: an almost-monochromatic gray palette, one typeface at one weight doing nearly everything, and nature photography interleaved with terminal screenshots. Nothing floats, nothing shouts; the page reads like a contemplative magazine spread.

## Color (hex · --var · role)
- warm near-black `--bg` — earthy dark canvas with warm gray undertone (NOT cold/blue black); `#faf9f6` `--fg` — warm parchment text (never pure `#ffffff`)
- `#353534` `--primary` — earth-gray button fill and dark interactive surfaces (warm, not cold)
- `#afaeac` `--muted` — body text / button labels (the workhorse reading color); `#868584` tertiary/nav labels
- `#666469` `--link` — muted purple-tinted underlined links in content
- `rgba(226,226,226,0.35)` `--border` — semi-transparent ghost border for card containment; `rgba(255,255,255,0.04)` ultra-subtle surface veil
- No semantic accent colors — the system is deliberately monochromatic; state is shown via opacity and underline, not hue. Contrast: `#afaeac` on warm-black ≈ 7:1; reserve `#868584` for secondary labels, not long body.

## Typography
- Stack: `"Matter", ui-sans-serif, system-ui` (display + body, Regular), `"Matter Medium"` for emphasis only, `"Geist Mono"` / `"Matter Mono"` for code, `Inter` as a narrow UI supplement.
- Display 80px / 400 / 1.00 / -2.4px · Section 56px / 400 / 1.20 / -0.56px · Feature 40px / 400 / 1.10 / -0.4px
- Body-lg 20px / 400 / 1.40 / -0.2px · Body 18px / 400 / 1.30 / -0.18px · Nav/UI 16px / 400 / 1.20 · Button 16px / 500 (Matter Medium)
- Micro-label 12px / 400 / 1.35 / **+2.4px uppercase** (editorial categorization signal); Caption 14px / 400 / **+1.4px uppercase**.

## Spacing, radius, depth, motion
- Base 8px; scale 4 / 8 / 12 / 16 / 24 / 32 / 36px; section gaps 80–120px, contemplative editorial pacing.
- Radius: 6px tags · 8px images/cards · 10px video · 12–14px feature cards · 50px pill buttons · 200px progress bars.
- Depth is near-flat: nothing casts a real shadow. Level 1 surface veil `rgba(255,255,255,0.04)`; Level 2 ghost border `rgba(226,226,226,0.35) 1px`; photography supplies atmospheric depth shadows can't. No glass/blur, no gradients.
- Motion: minimal — opacity/brightness shifts on hover, no dramatic color change; content cards barely react.

## Components (key)
- Primary CTA (dark pill): bg `#353534` / text `#afaeac` / padding ~10px / radius 50px — restrained and muted, never a bright attention-grabber.
- Inline tag: bg `rgba(255,255,255,0.16)` / text `#000000` / radius 6px / padding 1px 6px.
- Photography card: full-bleed nature image with overlay text, 8–12px radius, interleaved between terminal screenshots — this pairing is the brand, not decoration.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep text warm parchment `#faf9f6` — the reflex to type `#ffffff` for "primary text" reads cold and wrong here.
- Don't: add a bold accent color (blue/green/red CTA) — the whole identity is monochromatic warm gray; an accent breaks it.
- Don't: use weight 700 anywhere — Matter Regular (400) carries even headlines; Medium (500) is the ceiling and only for emphasis.
- Don't: build a cold/blue-tinted dark background — the warmth in the black is the entire mood.
- Don't: reach for drop shadows or glassmorphism — depth comes from photography, ghost borders, and 4%-opacity veils.

## Example component prompts
- "Hero on warm near-black: heading 80px Matter Regular weight 400, line-height 1.00, letter-spacing -2.4px, color `#faf9f6`. Dark pill CTA bg `#353534`, text `#afaeac`, 50px radius, ~10px padding. No accent color."
- "Feature card: warm-dark bg, ghost border `rgba(226,226,226,0.35)` 1px, 12px radius. Heading 40px Matter Regular 400 / -0.4px; body 18px Matter Regular 400 in `#afaeac`."
- "Category label: Matter Regular 12px, uppercase, letter-spacing +2.4px, color `#868584` — magazine-editorial tag above a section."
