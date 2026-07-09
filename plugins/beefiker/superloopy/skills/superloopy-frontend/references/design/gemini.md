# Gemini — Design Tokens (loopy-native)
> Category: ai-labs · Signature: the four-stop blue→violet→pink gradient as the whole identity

## Signature & atmosphere
Gemini feels like Google Material that learned to glow. The base is calm, near-white Material surface, but one element always carries the signature multi-stop gradient — sweeping blue into violet into a warm pink — and that single arc of color is the entire brand. The idea to get right is restraint plus one bloom: the page is quiet and systematic everywhere except the one place the gradient lives (a headline word, a spark icon, a focus border), where it does all the talking.

## Color (hex · --var · role)
- `#ffffff` `--bg` — page background (Material light); `#1f1f1f` `--fg` — text (warm near-black, never pure `#000`)
- `#f8f9fa` `--card` — raised surface, one tick off bg; `#202124` dark-mode surface
- `#4285f4` `--primary` — Google blue; the gradient's anchor and default action color
- `#4285f4 → #9b72cb → #d96570` `--gradient` — the signature: blue → violet → coral-pink (use on text via background-clip, on icons, on focus rings — never as a flat fill behind body copy)
- `#9b72cb` `--accent` — the violet midpoint; standalone accent when one color is needed
- `#5f6368` `--muted` — secondary text (Material gray 700); `#80868b` tertiary
- `#dadce0` `--border` — Material hairline; `#e8eaed` filled divider
- `#d93025` `--destructive` — Material red. Contrast: `#5f6368` on `#fff` ≈ 5.9:1, body-safe; keep the pink gradient stop off small text — it dips below 4.5:1.

## Typography
- Stack: `"Google Sans", "Google Sans Text", Roboto, system-ui, sans-serif`. Google Sans for display/headings, Google Sans Text or Roboto for body — geometric, open, optically friendly.
- Display 57px / 400 / 1.12 / -0.25px · H1 45px / 400 / 1.16 · H2 36px / 400 / 1.22 · Title 22px / 500 / 1.27 · Body 16px / 400 / 1.50 · Label 14px / 500 / 1.43 / +0.1px
- Material type scale: headlines stay weight 400 (regular), labels/buttons step to 500. The gradient word in a headline keeps the same 400 weight — color carries the emphasis, not weight.

## Spacing, radius, depth, motion
- Base 8px; scale 4/8/12/16/24/32/48/64px; Material density.
- Radius scale 8 / 12 / 16 / 28px — large, friendly corners; pill (9999px) for chips and the prompt bar.
- Depth strategy: Material tonal elevation, not heavy drops — surfaces lighten/tint with elevation; reserve `rgba(60,64,67,0.15) 0 1px 3px` for the highest layer only. Mostly flat with hairline `#dadce0`.
- Motion 200–300ms Material standard easing `cubic-bezier(0.2,0,0,1)`; the gradient can slowly animate hue/position on hero elements.

## Components (key)
- Primary CTA: bg `#4285f4` / text `#fff` / padding 10px 24px / radius 9999px (pill) / no border / hover tonal-darken + `rgba(60,64,67,0.15) 0 1px 3px` / focus 2px gradient ring. Tonal variant: bg `#e8f0fe`, text `#1967d2`.
- Prompt bar (signature): full-pill input, `#f8f9fa` fill, 1px `#dadce0` border that animates to the blue→violet→pink gradient on focus; spark/Gemini icon rendered in the gradient via background-clip.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: deploy the gradient on exactly one focal element per view (a word, an icon, a focus border) and keep everything else Material-neutral; render headlines at weight 400; use pill radius for actions and chips.
- Don't: paint the gradient as a full-bleed background behind text — the wrong instinct is "more gradient = more Gemini"; it's a single accent, not wallpaper. Don't reach for bold 600–700 headlines (Material display is 400). Don't use `#000`/`#fff` for text — warm `#1f1f1f` on near-white. Don't tint the gradient stops cool-only; the warm pink stop is mandatory or it reads as generic blue-purple.

## Example component prompts
- "Hero on `#ffffff`: H1 Google Sans 57px / weight 400 / line-height 1.12, color `#1f1f1f`, with one word filled by the gradient `#4285f4 → #9b72cb → #d96570` via background-clip:text; subhead Google Sans Text 16px / 400 / 1.50 in `#5f6368`."
- "Prompt bar: full-pill input, `#f8f9fa` fill, 1px `#dadce0` border; on focus the border becomes a 2px gradient `#4285f4→#9b72cb→#d96570`; spark icon left, gradient-clipped."
- "Primary button: blue `#4285f4`, white text, pill radius, 10px 24px padding, Material easing hover with `rgba(60,64,67,0.15) 0 1px 3px`."
- "Tonal chip row: `#e8f0fe` fill, `#1967d2` text, pill radius, 14px/500 label."
