# Mistral — Design Tokens (loopy-native)
> Category: ai-labs · Signature: golden-hour warmth + billboard weight-400 display, sharp corners

## Signature & atmosphere
Mistral feels like late-afternoon light over southern France rendered in code — every surface glows amber, shadows carry golden tint, and the brand orange burns through like a signal fire. The recognizable idea is total warm-temperature commitment paired with hard, near-zero-radius geometry: soft color, sharp edges. Huge display type lands like a billboard or protest poster — declarations, not descriptions.

## Color (hex · --var · role)
- `#fffaeb` `--bg` — warm ivory (never pure white); `#1f1f1f` `--fg` — warm near-black (not `#000`)
- `#fff0c2` `--card` — cream surface / secondary button; `#ffffff` reserved for max-contrast popovers
- `#fa520f` `--primary` — Mistral orange; highest-signal brand moments
- `#ff8105` `--accent` — block orange; `#ffa110` sunshine amber for interactive warmth
- `#ffd900` bright yellow — top of the signature block gradient
- `#3d3d3d` `--muted` — warm dark gray secondary text
- `#1f1f1f` `--border` via dark fills; `hsl(240 6% 90%)` the lone cool gray, inputs only
- Block gradient: `#ffd900 → #ffe295 → #ffa110 → #ff8105 → #fb6424 → #fa520f`. Contrast: `#3d3d3d` on `#fffaeb` ≈ 9:1.

## Typography
- Stack: `"Mistral Sans", Arial, system-ui, sans-serif` — a single grotesque does everything; hierarchy via SIZE, never weight.
- Display 82px / **400** / 1.00 / -2.05px · H2 56px / 400 / 0.95 · H3 48px / 400 / 0.95 · Card-title 32px / 400 / 1.15 · Feature 24px / 400 / 1.33 · Body 16px / 400 / 1.50 · Uppercase-CTA 16px / 400 / 1.50 UPPERCASE
- Weight is 400 everywhere — even at 82px. Ultra-tight line-heights (0.95–1.00) at display make poster-dense blocks.

## Spacing, radius, depth, motion
- Base 8px; scale 4/8/10/12/16/20/24/32/40/48/64/80/100px; section gaps 80–100px.
- Radius scale: near-zero. Sharp architectural corners are the default — 0px on most surfaces, tiny 2–4px at most.
- Depth strategy: one extraordinarily complex WARM shadow — five cascading amber layers, e.g. `rgba(127,99,21,0.12) -8px 16px 39px, rgba(127,99,21,0.1) -33px 64px 72px, rgba(127,99,21,0.06) -73px 144px 97px`. Creates a "floating in golden light" lift.
- Motion 150–220ms ease-out; transform/opacity only.

## Components (key)
- Primary CTA: bg `#1f1f1f` / text `#ffffff` / padding 12px / radius 0 / no border / hover lighten to `#3d3d3d`.
- Cream secondary: bg `#fff0c2` / text `#1f1f1f` / radius 0 / no border — the warm, inviting alt.
- Block identity: a gapless row of squares stepping `#ffd900 → #ffa110 → #fa520f`, sharp corners — the brand DNA.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep the whole palette warm (ivory/cream/amber/orange); set display at 82px / -2.05px and let SIZE carry hierarchy; tint shadows amber `rgba(127,99,21,...)`; keep corners sharp.
- Don't: round the corners — the wrong instinct is "soft brand color wants soft edges"; the tension between warm color and hard geometry IS Mistral. Don't bold anything (400 only). Don't use cool grays, cool shadows, or pure `#fff`/`#000`. Don't drop hero type below ~48px on desktop.

## Example component prompts
- "Hero on `#fffaeb`: H1 82px / 400 / line-height 1.0 / -2.05px in `#1f1f1f`; dark CTA `#1f1f1f` white text, 12px padding, 0 radius; cream secondary `#fff0c2`."
- "Card on `#fff0c2`, 0 radius; golden shadow `rgba(127,99,21,0.12) -8px 16px 39px, rgba(127,99,21,0.06) -73px 144px 97px`; title 32px/400, body 16px/1.50."
- "Block identity: gapless squares `#ffd900`, `#ffa110`, `#fa520f`, sharp corners, no gaps."
