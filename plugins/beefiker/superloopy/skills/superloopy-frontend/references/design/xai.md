# xAI — Design Tokens (loopy-native)
> Category: ai-creative · Signature: monospace as luxury on warm near-black

## Signature & atmosphere
xAI communicates through absence. A single warm near-black background, pure white text, no gradients, no accent color, no illustration — restraint pushed until it reads as confidence. The one unforgettable move is using a monospace face as the display type at extreme scale (think 320px, weight 300): fixed-width characters at that size feel architectural, positioning the brand as infrastructure built by people who live in terminals rather than a consumer product.

## Color (hex · --var · role)
- `#1f2228` `--bg` — the universal canvas, a warm near-black with a faint blue undertone (never pure `#000000`)
- `#ffffff` `--fg` — the singular text, link, and foreground color; in this system white is the voice, not a surface
- `rgba(255,255,255,0.7)` `--fg-secondary` — descriptions, supporting copy
- `rgba(255,255,255,0.5)` `--fg-muted` — labels, and the hover color (links dim, not brighten)
- `rgba(255,255,255,0.3)` `--fg-faint` — placeholders, disabled text
- `rgba(255,255,255,0.1)` `--border` — standard hairline; `rgba(255,255,255,0.2)` `--border-strong` — active/emphasis borders
- `rgba(255,255,255,0.03)` `--surface` — barely-there card lift; `rgba(255,255,255,0.08)` `--surface-hover`
- `rgb(59,130,246 / 0.5)` `--ring` — keyboard focus only. Everything is white-on-dark; resist any other hue.

## Typography
- Stack: display/buttons `"GeistMono", ui-monospace, "Roboto Mono", Menlo, monospace` · body/headings `"universalSans", system-ui, sans-serif` — two faces, zero role overlap
- Display-hero 320px / 300 / 1.50 / normal (monospace; scales to ~48–64px on mobile) · H2 30px / 400 / 1.20 / normal (sans)
- Body 16px / 400 / 1.50 · Label 14px / 400 / 1.50 · Meta 12px / 400 / 1.50
- Button 14px / 400 / 1.43 / **+1.4px UPPERCASE** in GeistMono — the tracked-out monospace label is mandatory and non-negotiable

## Spacing, radius, depth, motion
- Base 8px; deliberately sparse scale 4·8·24·48 — large jumps, hierarchy through whitespace not granularity; section padding 48–96px
- Radius: `0px` default (brutalist sharpness); `4px` only on occasional secondary containers — never 8px+, never pill
- Depth strategy: borders + opacity, never shadow. Elements "activate" by their border brightening from 0.1→0.2 on interaction; subtle 0.03→0.08 surface shifts; typographic scale contrast supplies the rest
- Motion: 120–200ms ease; hover DIMS interactive elements to 0.5 opacity (the reverse of convention)

## Components (key)
- Primary CTA: `#ffffff` bg / `#1f2228` text / 12px 24px / 0px radius / GeistMono 14px uppercase +1.4px / hover bg `rgba(255,255,255,0.9)`. Ghost variant: transparent + `1px solid rgba(255,255,255,0.2)`, hover bg `rgba(255,255,255,0.05)`
- Monospace tag: transparent bg, `1px solid rgba(255,255,255,0.2)`, 0px radius, GeistMono 12px uppercase +1px, 4px 8px padding

## Do / Don't (anti-convention — name the wrong instinct)
- Do: dim interactive elements on hover to `rgba(255,255,255,0.5)` — the inverse of the usual "brighten on hover" reflex
- Don't: reach for `#000000`. The wrong instinct is "pure black is more dramatic"; xAI's warm `#1f2228` is the brand and prevents harsh strain
- Don't: bold the display headline. 300–400 weight only — a heavy monospace at scale reads brutish, not precise
- Don't: round corners or add an accent color — sharp 0px and strict white-on-dark monochrome are the identity

## Example component prompts
- "Hero on `#1f2228`: headline `GeistMono` 72px weight 300 in `#ffffff` centered; subtitle `universalSans` 18px `rgba(255,255,255,0.7)` max-width 600px; primary button (white bg, `#1f2228` text, 0px radius, GeistMono 14px uppercase +1.4px, 12px 24px) and a ghost button (`1px solid rgba(255,255,255,0.2)`)."
- "Card: `rgba(255,255,255,0.03)` bg, `1px solid rgba(255,255,255,0.1)`, 0px radius, 24px padding, no shadow; hover border → `rgba(255,255,255,0.2)`."
- "Monospace badge: transparent, `1px solid rgba(255,255,255,0.2)`, 0px radius, GeistMono 12px uppercase +1px, 4px 8px."
