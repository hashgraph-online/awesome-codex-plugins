# Tesla — Design Tokens (loopy-native)
> Category: luxury-auto-tooling · Signature: radical subtraction — photography is everything, UI is nearly nothing

## Signature & atmosphere
Tesla is a digital showroom built by removing things: full-viewport car photography, one blue button, and almost no chrome. The recognizable idea is that whitespace is the luxury signal — each section is a full screen showing exactly one message (one car, one name, one CTA pair), so scrolling feels like walking a gallery, not reading a feed. No shadows, no gradients, no borders, no patterns. The product carries all emotional weight; the interface exists only to get out of the way.

## Color (hex · --var · role)
- `#FFFFFF` `--bg` — dominant surface for everything (page, nav, panels, secondary buttons)
- `#171A20` `--fg` — Carbon Dark, primary heading/nav text (warm near-black, blue undertone); also the dark-mode surface
- `#3E6AE1` `--primary` — Electric Blue, the ONLY chromatic color; primary CTA fills exclusively
- `#393C41` `--fg-body` — Graphite, default paragraph text; `#5C5E62` `--muted` — Pewter, tertiary/sub-links; `#8E8E8E` `--placeholder` — Silver Fog, input placeholders/disabled
- `#F4F4F4` `--surface-alt` — Light Ash, barely-there section differentiation; `#EEEEEE` `--border` — Cloud Gray dividers; `#D0D1D2` `--border-2` — subtle UI delineation
- `rgba(255,255,255,0.75)` `--nav-frost` — frosted-glass nav backdrop on scroll
- No semantic palette — error/success follow browser defaults; the blue CTA is the sole interactive signal

## Typography
- Stack: `"Universal Sans Display", -apple-system, Arial, sans-serif` (hero only) and `"Universal Sans Text", -apple-system, Arial, sans-serif` (everything else). Same typeface optically corrected at two sizes. No OpenType features, no italics, no uppercase.
- Hero Title 40px / 500 / 1.20 / normal tracking · Product Name 17px / 500 / 1.18 · Nav Item 14px / 500 / 1.20 · Body 14px / 400 / 1.43 · Button 14px / 500 / 1.20
- Only two weights: 500 (headings/UI) and 400 (body). No bold, no light. `letter-spacing: normal` at every level — the typeface speaks for itself.

## Spacing, radius, depth, motion
- Base 8px; common 8 · 16 · 24. Layout is full-viewport sections (100vh), content centered vertically; button padding minimal (4px outer, 4px 16px nav). Card gaps ~16px.
- Radius: 0px default, 4px on buttons (barely perceptible), ~12px on large category cards, 50% for carousel dots.
- Depth strategy: none — no box-shadows. Layering via z-index, opacity (frosted nav), and photography. Motion: every interactive transition is `0.33s` (color/background/border only) — consistency in timing matters as much as color; no scale/translate.

## Components (key)
- Primary CTA: bg `#3E6AE1` / text `#FFFFFF` / 14px/500 / radius 4px / min-height 40px / width ~200px / 3px transparent border reserving focus animation. Hover subtly darkens; transitions 0.33s.
- Secondary CTA: bg `#FFFFFF` / text `#393C41` / same dimensions and 4px radius. Paired side-by-side with primary, max two per screen.
- Category card: full-bleed landscape photo, ~12px radius, overflow hidden, white label in the top-left corner — no overlay gradient, contrast comes from the image itself.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: let photography dominate every screen and treat whitespace as the luxury; keep all transitions at 0.33s; use `#3E6AE1` for primary CTAs only.
- Don't: add box-shadows for "elevation" — the universal instinct to lift cards with shadow contradicts the flat gallery aesthetic; separation is spacing, not shadow or borders.
- Don't: use uppercase or bold to add emphasis — Tesla's confidence is lowercase calm at weight 400–500; reaching for 700 or `text-transform: uppercase` breaks the understatement.
- Don't: fill the viewport with multiple CTAs or stack messages — the reflex to maximize density per screen destroys the one-message-per-viewport rhythm.

## Example component prompts
- "Hero: full-viewport background image, centered 'Model Y' in Universal Sans Display 40px/500 white, subtitle below, then two side-by-side buttons — primary `#3E6AE1` 'Order Now' and white `#393C41` 'View Inventory', both 4px radius, 40px height."
- "Navigation: spaced-letter wordmark left, five text buttons 14px/500 `#171A20` centered, three icon buttons right — white background, no shadow, no border."
- "Category card: full-bleed landscape photo, 12px radius, overflow hidden, white label 'Sport Sedan' top-left, no overlay gradient."
