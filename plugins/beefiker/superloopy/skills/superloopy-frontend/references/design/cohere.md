# Cohere — Design Tokens (loopy-native)
> Category: ai-labs · Signature: 22px-rounded white cards + serif display, blue only on touch

## Signature & atmosphere
Cohere reads as an enterprise command deck: bright, orderly, and built so AI feels like serious infrastructure rather than a toy. The one recognizable move is the oversized 22px card radius — every container softens into the same cloud-like rounding, which makes a black-and-white page feel approachable without adding color. It is restraint engineered to read as authority.

## Color (hex · --var · role)
- `#ffffff` `--bg` — bright white; `#000000` `--fg` — true black for display headlines (one of the few brands that earns pure black)
- `#fafafa` `--card` — snow surface, faint lift; bordered, rarely shadowed
- `#000000` `--primary` — dark solid CTA fill
- `#1863dc` `--accent` — interaction blue; appears ONLY on hover/focus/active, never at rest
- `#212121` body text; `#93939f` `--muted` — cool slate, footer/tertiary (slight violet tint)
- `#f2f2f2` `--border` — lightest hairline; `#d9d9dd` `--border-strong` — cool gray divider
- `#9b60aa` input-focus border (muted violet). Contrast: `#93939f` on white ≈ 3.4:1 — labels only, never body.
- Deep purple/violet is reserved for full-width photographic bands, never card fills.

## Typography
- Stack: display serif `"CohereText", "Space Grotesk", system-ui, serif`; UI sans `"Unica77", Inter, system-ui, sans-serif`; code `"CohereMono", ui-monospace, monospace`. Serif declares, sans does the work.
- Display 72px / 400 / 1.00 / -1.44px · Display-2 60px / 400 / 1.00 / -1.2px · H2 48px / 400 / 1.20 / -0.48px · H3 32px / 400 / 1.20 / -0.32px · Body 16px / 400 / 1.50 · Button-sm 14px / 500 / 1.7 · Mono label 14px / 400 / 1.40 / +0.28px UPPERCASE
- Almost everything is weight 400; tight negative tracking at display scale does the heavy lifting.

## Spacing, radius, depth, motion
- Base 8px; scale 6/8/12/16/20/22/24/32/40/56px; section gaps 56–60px.
- Radius scale 4 / 8 / 16 / 20 / **22** / 9999px. 22px is the signature on all primary cards/images.
- Depth strategy: borders + light/dark band contrast, near zero shadow. White cards "lift" by sitting on a purple band, not by casting shadow.
- Motion 150–200ms ease-out; the key transition is text/icon color sliding to `#1863dc` on hover.

## Components (key)
- Ghost primary button: transparent bg / text `#000000` / no border at rest / hover text → `#1863dc` at 0.8 opacity / focus 2px solid `#1863dc` outline. Invisible until touched.
- Dark solid CTA: bg `#000000` / text `#ffffff` / pill or 22px radius / on light surfaces.
- 22px card: bg `#ffffff`, 1px `#f2f2f2` border, 22px radius, ~28px padding — THE Cohere object.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: round every primary card to 22px; keep `#1863dc` strictly for interactive states; make the default button a ghost (transparent) that colors only on hover.
- Don't: give buttons a visible fill/border at rest — the wrong instinct is "a button needs a box." Don't use 8px or 12px on primary cards; the 22px radius is load-bearing identity. Don't warm the grays or fill cards with purple. Don't use blue at rest.

## Example component prompts
- "Hero on `#ffffff`: H1 CohereText 72px / 400 / line-height 1.0 / letter-spacing -1.44px in `#000`; subhead Unica77 18px / 400 / 1.4; ghost button, black text, hover color to `#1863dc`."
- "Card: white, 22px radius, 1px `#f2f2f2` border, no shadow; title Unica77 32px/400 / -0.32px, body 16px/1.5 in `#93939f`."
- "Section label CohereMono 14px / 400 / UPPERCASE / +0.28px in `#93939f`."
