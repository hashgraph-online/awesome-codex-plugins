# Vercel — Design Tokens (loopy-native)
> Category: dev-tools · Signature: gallery-white minimalism where borders live in the shadow layer

## Signature & atmosphere
Vercel feels like an empty white gallery built by compiler engineers — every pixel earns its place, and the design strips itself down until only structure is left. The recognizable trick: there are almost no CSS borders; outlines are drawn as zero-blur, 1px-spread box-shadows, so edges feel like crisp lines floating just above the page. Headlines are compressed with extreme negative tracking, as if the type were minified for production.

## Color (hex · --var · role)
- `#ffffff` `--bg` — page/cards; `#171717` `--fg` — text/headings (warm near-black, deliberately not `#000000` for micro-softness)
- `#171717` `--primary` — dark CTA fill; text on it is `#ffffff`
- `#4d4d4d` `--muted` — body/description; `#666666` — tertiary; `#808080` — placeholder/disabled
- `#ebebeb` `--border` — visible light ring/divider; `#fafafa` — subtle surface tint + the inner-glow ring in card shadows
- `#0072f5` `--link` — link blue; `hsla(212,100%,48%,1)` `--focus` — accessibility focus ring
- Workflow accents (use only in pipeline context): `#0a72ef` develop · `#de1d8d` preview · `#ff5b4f` ship
- Contrast: `--muted #4d4d4d` on white passes AA; keep `#808080` for non-text/placeholder only.

## Typography
- Stack: `Geist` (sans, display + UI), `Geist Mono` (code, uppercase technical labels). Enable `font-feature-settings: "liga"` on all Geist; `"tnum"` on tabular captions.
- Display 48px/600/1.0–1.17/-2.4 to -2.88px · Section 40px/600/1.2/-2.4px · Card-title 24px/600/1.33/-0.96px
- Body-lg 20px/400/1.8/0 · Body 18px/400/1.56/0 · Body-sm 16px/400/1.5/0 · Button/Link 14px/500/1.43/0
- Three weights, strict roles: 400 body, 500 UI/interactive, 600 headings. No 700 except 7px micro-badges. Tracking scales with size: -2.4px@48 → -0.96px@24 → 0@14.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 32 · 40 (note the jump from 16 straight to 32 — no 20/24).
- Radius: 6px buttons · 8px cards · 12px image/featured cards · 9999px badges only · 64–100px nav pills.
- Depth = shadow-as-border. Foundation: `0 0 0 1px rgba(0,0,0,0.08)`. Card stack layers it: `rgba(0,0,0,0.08) 0 0 0 1px, rgba(0,0,0,0.04) 0 2px 2px, rgba(0,0,0,0.04) 0 8px 8px -8px, #fafafa 0 0 0 1px` — the inner `#fafafa` ring is the glow. Never exceed ~0.1 opacity.
- Motion: 150ms ease, transform/opacity only; hover = subtle shadow intensification.

## Components (key)
- Primary CTA (dark): bg `#171717` / text `#ffffff` / padding 8px 16px / radius 6px / no border. Focus: `2px solid hsla(212,100%,48%,1)` outline.
- Ghost button: bg `#ffffff` / text `#171717` / radius 6px / `rgb(235,235,235) 0 0 0 1px` ring (no real border). Hover shifts fill dark.
- Workflow pipeline: three horizontal steps Develop→Preview→Ship, each a `Geist Mono` uppercase label in its accent (`#0a72ef`/`#de1d8d`/`#ff5b4f`) over a 24px/600 title.

## Do / Don't (anti-convention)
- Do: replace `border: 1px solid` with `box-shadow: 0 0 0 1px rgba(0,0,0,0.08)` — the entire edge system lives in the shadow layer.
- Don't: use positive letter-spacing on Geist display — it always runs negative; loose tracking kills the compressed-infrastructure feel.
- Don't: cap headlines at weight 700 — 600 is the ceiling; weight isn't the hierarchy tool, size and tracking are.
- Don't: drop the inner `#fafafa` ring from card shadows — it's the subtle glow that makes the surface read as built, not floating.

## Example component prompts
- "Hero on `#ffffff`: headline 48px Geist weight 600, line-height 1.0, letter-spacing -2.4px, color `#171717`. Subtitle 20px/400/1.8 in `#4d4d4d`. Dark CTA `#171717` 6px radius 8px 16px; ghost button white with shadow-border `0 0 0 1px rgba(0,0,0,0.08)`."
- "Card: white bg, NO css border, shadow stack `rgba(0,0,0,0.08) 0 0 0 1px, rgba(0,0,0,0.04) 0 2px 2px, #fafafa 0 0 0 1px`, radius 8px. Title 24px/600 letter-spacing -0.96px; body 16px/400 `#4d4d4d`."
