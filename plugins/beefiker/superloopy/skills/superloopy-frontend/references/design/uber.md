# Uber — Design Tokens (loopy-native)
> Category: consumer · Signature: transit-map confidence — pure black/white, pill everything, no mid-tones

## Signature & atmosphere
A black-and-white universe where every pixel earns its place and nothing decorates. The recognizable idea is a stark duality — true `#000000` and pure `#ffffff` with almost no diluting mid-grays in the chrome — read as the restraint of a brand established enough to whisper. Headlines hit like a billboard in a square, engineered geometric sans; pill-shaped controls (999px) make the whole surface feel thumb-friendly. Warmth comes only from human illustration set against the monochrome.

## Color (hex · --var · role)
- `#000000` `--bg-dark` / `--fg` / `--primary` — true black does triple duty: footer bg, headline ink, primary button; `#ffffff` `--bg` / `--on-primary` — surface and inverse text
- `#4b4b4b` `--muted` — secondary text & footer links; `#afafaf` `--muted-2` — tertiary/placeholder
- `#efefef` `--chip` — filter/nav chip bg; `#e2e2e2` `--hover` — white-button hover; `#f3f3f3` `--hover-light`
- Link: `#0000ee` `--link` (body), white/black on their surfaces
- No semantic color palette and no gradients — hierarchy is entirely black/white blocks + shadow. Contrast: `--fg` on white = 21:1; white on `--primary` = 21:1.

## Typography
- Stack: `"UberMove"` (headlines, geometric, square) + `"UberMoveText"` (body/UI), system-ui fallback. Strict role boundary — never crossed. Substitute: Inter or DM Sans.
- Display 52/700/1.23 · Section 36/700/1.22 · Card title 32/700/1.25 · Sub-heading 24/700/1.33 · Small heading 20/700/1.40 · Nav 18/500/1.33 · Body/Button 16/400-500/1.25-1.50 · Caption 14/400-500 · Micro 12/400/1.67
- Functional only: no letter-spacing, no text-transform, no ornament. Headings are exclusively 700; body/UI is 400–500.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 6 · 8 · 10 · 12 · 14 · 16 · 18 · 20 · 24 · 32; sections 64–96px apart, but elements within group tightly (efficient, not airy).
- Radius: content card 8px · featured 12px · everything interactive 999px (buttons, chips, nav) · circle 50% (avatar, menu toggle). Sharp corners never appear on interactive elements.
- Depth = whisper-soft black shadows only, structural never decorative. Card `rgba(0,0,0,.12) 0 4px 16px`; elevated `rgba(0,0,0,.16) 0 4px 16px`; FAB `rgba(0,0,0,.16) 0 2px 8px`; pressed `rgba(0,0,0,.08) inset`. No colored/layered/glow shadows.
- Motion: minimal; press uses inset shadow; focus `rgb(255,255,255) 0 0 0 2px inset`.

## Components (key)
- Primary CTA: bg `#000000` / text `#ffffff` / padding 10px 12px / radius 999px / no border. Secondary: white bg, black text, hover → `#e2e2e2`. Pair black + white for dual actions.
- Category pill nav: `#efefef` bg, black text, 14px 16px padding, 999px radius; active inverts to black bg + white text.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: commit to true `#000000`/`#ffffff` — the stark contrast IS the brand; add warmth via illustration, not color.
- Don't: soften the duality with off-whites or near-blacks because "pure black is harsh" — the uncompromising contrast is deliberate.
- Don't: round buttons to less than 999px — the full pill is a core identity element, not a style choice.
- Don't: apply heavy drop shadows — depth is whisper-subtle (0.08–0.16) and carried by black/white section contrast.

## Example component prompts
- "Hero on `#ffffff`: 52px/700 UberMove headline (line-height 1.23) in `#000000`, 16px/400 `#4b4b4b` subtitle at 1.50; `#000000` pill CTA (999px, 10px 12px padding) with white text."
- "Category nav: horizontal pills, each `#efefef` bg, `#000000` text, 14px 16px padding, 999px radius, UberMoveText 14/500; active pill inverts to black bg + white text."
- "Feature card on white, 8px radius, `rgba(0,0,0,.12) 0 4px 16px` shadow; 24px/700 UberMove title, 16px `#4b4b4b` body, black pill CTA at the bottom."
