# Bugatti — Design Tokens (loopy-native)
> Category: luxury-auto-tooling · Signature: cinema-black monochrome — monumental display type, scale as hierarchy

## Signature & atmosphere
Bugatti behaves like a feature film you are standing inside: a pure-black room with full-bleed vehicle footage and a single typographic moment laid over it. The recognizable idea is scale-as-hierarchy — display type runs to architectural size (200px+) so a headline reads like a wordmark across a showroom floor, while the palette refuses any color so it never competes with the lacquer of the car itself. It is a black velvet display stand, not a website.

## Color (hex · --var · role)
- `#000000` `--bg` — the entire canvas, pure HTML black, no off-black, no tint
- `#FFFFFF` `--fg` — all text, borders, and CTAs; white is the only resting chrome color
- `#999999` `--muted` — the single gray: secondary borders, disabled states, the thinnest hairlines (treat as 75%-volume white, never a color)
- `--card`: none — there is no card surface; "separate" things sit on the same black with a 1px `#999999` frame
- `--primary` / `--accent`: none by design — do not introduce a brand blue or hazard color
- `--border` `#FFFFFF` (1px) for primary outlines / `#999999` for secondary frames. Contrast: white on black = 21:1; the system lives at maximum contrast.

## Typography
- Stack: display `"Bugatti Display", "Unbounded", ui-sans-serif, system-ui`; UI `"Bugatti Mono", "Space Mono", ui-monospace, monospace`; body `"Bugatti Text", "Inter", sans-serif`. Three-role custom family.
- Monumental Hero 200–288px / 400 / 1.00 / 0 / UPPERCASE — the defining gesture, architectural scale · Mid Display 60px / 400 / 1.00 / +1.4px · Section 36px / 400 / 1.11 · Body 16px / 400 / 1.50 · UI Label (mono) 14px / 400 / 1.43 / +1.4px / UPPERCASE
- Active weight is 400 everywhere — there is no bold. Hierarchy is size, never weight. Mono caps own every label, button, and caption.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 6 · 12 · 36 · 48 · 64 — six values only, no in-between invention.
- Radius scale 0 · 6 · 9999px — rectangle, one small utility radius, or full pill; nothing between (12/16/20/24 are forbidden).
- Depth strategy: borders + a single legibility vignette over media — no drop shadows, no glows, no glassmorphism. Elevation is a 1px hairline. The only "gradient" is `rgba(0,0,0,0.4) → transparent` bottom-up over hero footage. Motion 200–300ms ease, quiet — opacity/border only, never bouncy.

## Components (key)
- Primary CTA: transparent bg / text `#FFFFFF` mono 14px/400/+1.4px UPPERCASE / 1px `#FFFFFF` border / radius 9999px / padding 12px 24px / hover fills white with black text, active opacity ~0.7, focus 1px white ring.
- Secondary (utility): transparent / 1px `#999999` border / radius 6px / padding 6px 12px / hover border → `#FFFFFF`.
- Hero: full-bleed 21:9 vehicle video, monumental UPPERCASE headline 200px+ over the legibility vignette, one pill CTA 48–64px below — no card, no grid.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: land one monumental 200px+ headline per page; keep the canvas pure `#000000`; size, not weight, makes hierarchy; mono-caps every button and label.
- Don't: bold a headline for impact — the reflex that "emphasis = heavier weight" is absent here; everything is 400 and you make it bigger instead.
- Don't: add any accent color — the instinct to drop in a brand blue or CTA color competes with the car paint and breaks the velvet-stand austerity.
- Don't: use rounded rectangles between 6px and 9999px — the "friendly soft card" reflex is vulgar in this system; commit to rectangle, tiny utility radius, or full pill.

## Example component prompts
- "Monumental hero: UPPERCASE headline in Bugatti Display 240px, weight 400, line-height 1.00, `#FFFFFF` on pure `#000000`; full-bleed 21:9 vehicle video behind with a `rgba(0,0,0,0.4) → transparent` bottom-up vignette."
- "Pill CTA: transparent bg, 1px `#FFFFFF` border, 9999px radius, 12px 24px padding, Bugatti Mono 14px/400/+1.4px UPPERCASE white label; hover fills white with black text in 250ms ease."
- "Nav strip: pure `#000000`, UPPERCASE mono 14px/+1.4px links in `#FFFFFF`, centered wordmark, no dividers, hover is opacity dim only — no color change."
