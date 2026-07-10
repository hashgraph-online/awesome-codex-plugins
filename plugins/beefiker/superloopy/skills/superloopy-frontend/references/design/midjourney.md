# Midjourney — Design Tokens (loopy-native)
> Category: ai-labs · Signature: pure-black gallery where the imagery is the only color

## Signature & atmosphere
Midjourney feels like walking into a dark gallery where the art glows on the walls and everything else disappears. The interface is near-pure black with the chrome reduced to a whisper — thin light-gray text, hairline dividers, no buttons fighting for attention. The recognizable idea: the UI vanishes so the generated images carry 100% of the color and emotion. Every design decision is subtraction. The site is a frame, not a poster.

## Color (hex · --var · role)
- `#0a0a0a` `--bg` — near-black canvas (a hair off pure `#000` to avoid OLED smearing); `#000000` acceptable for full-bleed image backdrops
- `#fafafa` `--fg` — primary text (soft white, never harsh `#fff`)
- `#141414` `--card` — surface card, barely lifted from bg; `#1c1c1c` raised panel
- `#fafafa` `--primary` — there is no brand hue; the primary action is white-on-black (inverted), letting imagery own all color
- `#8a8a8a` `--muted` — secondary text (mid gray); `#5a5a5a` tertiary/disabled
- `rgba(255,255,255,0.08)` `--border` — hairline divider; `rgba(255,255,255,0.14)` emphasized
- `rgba(255,255,255,0.04)` `--surface-subtle` — hover fill / glass chip on black
- `#e5484d` `--destructive` — restrained red, used sparingly. Contrast: `#8a8a8a` on `#0a0a0a` ≈ 5.2:1 (body-ok); the system has no accent color by design — any color on screen should come from generated images.

## Typography
- Stack: display `"Times New Roman", Georgia, serif` (editorial, gallery-label feel for hero numerals/wordmark); UI `system-ui, -apple-system, "Helvetica Neue", sans-serif`. The serif/sans contrast evokes museum signage.
- Display 72px / 400 / 1.05 / -1px (serif, gallery-poster scale) · H1 40px / 400 / 1.10 · H2 28px / 400 / 1.20 · Body 15px / 400 / 1.55 (sans) · Label 12px / 500 / 1.30 / +0.4px UPPERCASE · Caption 12px / 400 / 1.40 (image metadata)
- Headings stay weight 400 — the gravitas comes from scale and serif, never from bold. Tiny uppercase tracked labels do the wayfinding.

## Spacing, radius, depth, motion
- Base 8px; scale 4/8/12/16/24/32/48/64px; tight image grids with 2–8px gutters (the masonry breathes via the images, not whitespace).
- Radius scale 4 / 8 / 12px — modest; imagery is usually square/sharp-cornered. Pill only for filter chips.
- Depth strategy: no shadows — depth comes from the image lightboxing over a dimmed `rgba(0,0,0,0.7)` scrim. Cards are flat with hairline borders. The black absorbs all elevation cues.
- Motion 150–250ms ease-out; image fade-in on load, gentle scrim dim on lightbox open; nothing bouncy.

## Components (key)
- Primary CTA: bg `#fafafa` / text `#0a0a0a` / padding 10px 20px / radius 8px / no border / hover dim to `#e5e5e5` / focus 2px `rgba(255,255,255,0.4)` ring. (Inverted — white button is the loudest thing allowed.)
- Image tile (signature): edge-to-edge generated image in a masonry/4-up grid, 4px radius, 4px gutter; overlay controls (upscale/vary) appear only on hover as `rgba(0,0,0,0.5)` scrim with white glyphs — zero chrome at rest.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep the entire palette black/white/gray and let generated images be the only saturated color; render hero type in serif at weight 400; remove every control that can hide until hover.
- Don't: introduce a brand accent hue — the wrong instinct is "add a signature color"; Midjourney's signature is the absence of one. Don't use pure `#000`/`#fff` (use `#0a0a0a`/`#fafafa`). Don't add drop shadows or glass cards; flatness keeps focus on imagery. Don't bold the display type or fill the screen with persistent buttons — restraint is the aesthetic.

## Example component prompts
- "Hero on `#0a0a0a`: H1 in Times New Roman 72px / weight 400 / -1px in `#fafafa`; one tracked uppercase label below in 12px/500/+0.4px `#8a8a8a`; white `#fafafa` CTA with black text, 8px radius."
- "Masonry image grid: 4 columns, 4px gutter, 4px radius tiles, edge-to-edge images on `#0a0a0a`; hover reveals `rgba(0,0,0,0.5)` scrim with white action glyphs."
- "Lightbox: image centered over `rgba(0,0,0,0.7)` scrim, metadata caption in 12px/400 `#8a8a8a`, no card chrome."
- "Filter bar: glass chips `rgba(255,255,255,0.04)` fill, hairline `rgba(255,255,255,0.14)` border, 12px uppercase label `#fafafa`, pill radius."
