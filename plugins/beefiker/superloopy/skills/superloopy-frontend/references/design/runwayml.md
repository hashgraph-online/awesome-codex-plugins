# RunwayML — Design Tokens (loopy-native)
> Category: ai-creative · Signature: the interface disappears so the footage can speak

## Signature & atmosphere
Runway feels like scrolling through a film reel that happens to have a website wrapped around it. The chrome retreats almost to nothing — no shadows, hairline borders, cool-gray text — so full-bleed cinematic imagery becomes the only thing with presence. The recognizable move is total typographic monoculture: one geometric sans carries everything from a 48px title to an 11px tag, and headlines compress to film-title density with negative tracking.

## Color (hex · --var · role)
- `#000000` `--bg` — page background (true black, not charcoal); `#ffffff` `--fg` — text on dark, light-section background
- `#1a1a1a` `--card` — elevated dark surface; `#030303` `--bg-layer` — near-imperceptible second dark plane
- `#404040` `--fg-on-light` — body text on light sections; `#767d88` `--muted` — secondary text, distinctly cool blue-gray (never warm)
- `#7d848e` `--muted-2` — tertiary/metadata; `#a7a7a7` `--faint` — timestamps, de-emphasized
- `#27272a` `--border` — the single dark-mode border, barely visible; `#c9ccd1` `--border-light` — divider on light sections
- `#e9ecf2` `--surface-light` — cool-tinted light section panel
- No accent color exists. Chroma comes only from photographic/video content. Contrast: `--muted` on `#000` ~4.6:1 — keep it to secondary copy, not long body.

## Typography
- Stack: `abcNormal, "DM Sans", Inter, sans-serif` — one geometric sans, complete expression through size/case/tracking, never family-switching
- Display 48px / 400 / 1.00 / -1.2px · H2 40px / 400 / 1.00–1.10 / -1.0px · H3 36px / 400 / 1.00 / -0.9px
- Card title 24px / 400 / 1.00 / 0 · Body 16px / 400–600 / 1.40 / -0.16px
- Label 14px / 500 / 1.30 / +0.35px UPPERCASE · Micro 11px / 450 / 1.30 / 0 UPPERCASE (450 is the signature intermediate weight)

## Spacing, radius, depth, motion
- Base 8px; scale 4·6·8·12·16·20·24·32·48·64·78; section gaps 48–78px
- Radius: 4px buttons · 6px links · 8px image cards · 16px alert containers — subtly rounded, never pill
- Depth strategy: dark/light section alternation + photographic depth-of-field. Zero box-shadow anywhere — cinema gets depth from lighting, not drop shadows
- Motion: 150–250ms ease-out on opacity/transform only; text overlays fade rather than slide

## Components (key)
- Primary CTA: transparent or dark bg / `#ffffff` text / 8px 16px padding / 4px radius / minimal or no border / hover lifts opacity toward full white / active dims / focus 2px outline. Restrained — it blends into editorial flow
- Cinematic hero: full-viewport image or video, headline 48px/400/-1.2px white over a dark gradient overlay, single line of `--muted` subcopy beneath; the footage is the hero, text is the caption

## Do / Don't (anti-convention — name the wrong instinct)
- Do: let one image fill the frame and keep the UI nearly invisible — borders hairline, shadows absent
- Don't: reach for weight 600–700 to make a headline feel important — 400 at 48px with -1.2px tracking is the voice; bold reads as a different, lesser brand
- Don't: warm up the grays. The instinct to use `#888` neutral is wrong — secondary text is cool blue-gray (`#767d88`)
- Don't: round to pill or add an accent color — Runway has no brand hue, only photographic color

## Example component prompts
- "Full-bleed hero, `#000000` bg with a cinematic 16:9 video overlaid by a top-to-bottom black gradient; headline `abcNormal` 48px weight 400 line-height 1.0 letter-spacing -1.2px in `#ffffff`; one subline 16px in `#767d88`."
- "Research grid: one 50%-width card with an 8px-radius image + 24px/400 title, beside two stacked smaller cards; titles `#ffffff` on dark, `#404040` on light; no shadows."
- "Section label `abcNormal` 11px weight 450 uppercase letter-spacing +0.35px in `#767d88`, no background, no border."
