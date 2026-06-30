# Mercury — Design Tokens (loopy-native)
> Category: fintech/crypto · Signature: cool near-white canvas, violet-blue precision, hairline borders over shadow

## Signature & atmosphere
Mercury feels like banking redrawn by a design tool: clinical, quiet, exact. Surfaces are a faintly cool off-white, structure comes from 1px hairline borders rather than shadow, and a single indigo-violet does all the signalling. The one idea to land is restraint-as-confidence — nothing decorative, every pixel load-bearing, the way a well-built dashboard implies the money beneath it is handled.

## Color (hex · --var · role)
- `#ffffff` `--bg` — base canvas; `#f7f7f8` `--bg-subtle` — cool gray section fill (faint blue undertone, never warm)
- `#1a1a2e` `--fg` — near-black with a blue cast for headings + body
- `#5266eb` `--primary` — indigo-violet; CTA fills, links, active states. The one signal hue.
- `#4254d4` `--primary-hover` — pressed/hover violet (darken ~8%)
- `#6b7280` `--muted` — secondary text (cool slate); `#9ca3af` tertiary/placeholder
- `#e5e7eb` `--border` — hairline divider; `#d1d5db` emphasized border
- `#fbfbfc` `--card` — card surface, a hair above canvas
- `#e11d48` `--destructive` — rose-red; `#16a34a` success (positive balance). Contrast: `#6b7280` on `#ffffff` ≈ 4.6:1, body-safe but avoid for sub-12px.

## Typography
- Stack: `"Inter", system-ui, -apple-system, sans-serif` everywhere; `ui-monospace, "SF Mono", monospace` for figures/balances. Tabular numerals (`font-variant-numeric: tabular-nums`) on all money values.
- Display 56/600/1.08/-0.02em · H1 40/600/1.12/-0.02em · H2 30/600/1.20/-0.01em · Card-title 20/600/1.30 · Body-lg 18/400/1.55 · Body 16/400/1.55 · Label 13/500/1.20/+0.01em · Mono-figure 16/500/1.20 tabular
- Headings sit at weight 600 with tight negative tracking; never 700+. Body is a calm 400.

## Spacing, radius, depth, motion
- Base 4px; scale 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96. Section padding 64–96px.
- Radius: 6 (inputs/chips) · 8 (buttons) · 12 (cards) · 16 (modals/panels). No fully-round pills.
- Depth strategy: BORDERS first. Hairline `1px solid #e5e7eb` defines almost everything. Reserve one soft shadow for floating layers: `rgba(16,24,40,0.06) 0 4px 12px`. No layered drop shadows.
- Motion: 120–180ms ease-out; transform/opacity only; subtle border-color and bg transitions on hover.

## Components (key)
- Primary CTA: bg `#5266eb` / text `#ffffff` / padding 10px 18px / radius 8px / no border. Hover `#4254d4`; active translateY(1px); focus `0 0 0 3px rgba(82,102,235,0.25)` ring.
- Secondary button: bg `#ffffff` / text `#1a1a2e` / `1px solid #e5e7eb` / radius 8px; hover bg `#f7f7f8`, border `#d1d5db`.
- Data card / balance tile: `#fbfbfc` surface, `1px solid #e5e7eb`, radius 12px, 24px padding; figure in mono tabular 16/500, label 13/500 `#6b7280`.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: build structure from 1px hairline borders, not shadows — the dashboard look is flat and edged.
- Do: set money figures in a monospace with tabular numerals so columns align to the pixel.
- Don't: warm the grays — the instinct to soften with beige/cream breaks Mercury's cool clinical tone; keep blue-cast neutrals.
- Don't: use full-pill (9999px) buttons — radius tops out at 16; pills read consumer-app, not institutional.
- Don't: scatter accent colors — one indigo does all signalling; extra hues read as noise on a finance surface.

## Example component prompts
- "Dashboard card on `#fbfbfc`, `1px solid #e5e7eb`, radius 12px, 24px padding: label 13px Inter weight 500 `#6b7280`, balance in monospace 28px weight 500 tabular-nums `#1a1a2e`; indigo `#5266eb` 'Move money' button radius 8px padding 10px 18px white text."
- "Hero on `#ffffff`: H1 Inter 40px weight 600 -0.02em `#1a1a2e`; subhead 18px weight 400 1.55 `#6b7280`; primary CTA `#5266eb`, hover `#4254d4`, focus ring `0 0 0 3px rgba(82,102,235,0.25)`. No drop shadow, hairline borders only."
