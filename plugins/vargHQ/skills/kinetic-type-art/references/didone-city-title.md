# Didone city title

A two-word place name stacked in Didone capitals (for example, one word over the other), first traced as hairline outlines, then filled; it holds, then springs wide as horizontal strokes extend and a round letter opens into a capsule. For fashion, travel, events, city launches. 16:9, 9:16, 1:1; 4-6 s.

## How the pros do it
- Pick a true Didone: strong thick/thin contrast, vertical stress, unbracketed hairline serifs, ball terminals [28]. Bodoni Moda (opsz 6-96, wght 400-900) or Playfair Display (wght 400-900) [27][29].
- Set it big. At small sizes the thick verticals "dazzle" and hairlines vanish; use the large optical size for display [28].
- Didone looks at home in fashion mastheads and glossy print; keep the palette restrained (ink on paper, or paper on black) [28].
- Trace first: a stroke-only pass of the outlines reads as drawing; kinetic type built from strokes rather than fills is its own look [7].
- The spring needs anticipation (a slight squeeze before the stretch), overshoot, and a hold; keep the visual weight steady while shapes stretch [39].
- Track the caps +0.02 to +0.06em at this size; Didone caps tighten optically when huge [22].
- Use one ease family for the whole move; `back.out` gives the spring, `power3.inOut` the squeeze [21].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `didone-city-title.ink` | Black Didone on paper, hairline trace then fill | Bodoni Moda 900, opsz 96, ink #111111 on #F2EFE8, stroke 1.5 px |
| `didone-city-title.night` | Paper-white Didone on black, gold hairline | Playfair Display 900, #F2EFE8 on #0B0B0D, trace stroke #BB8B41 (riso flat gold [30]) |
| `didone-city-title.stretch` | Hold short, spring very wide (E arms run to frame edge) | arm extension 3.5x, O to capsule 2.2x width, `back.out(1.8)` |

## Timing and numbers (5 s = 150 f)
- 0-36 f: trace outlines (stroke-dashoffset from length to 0), letters staggered 3-4 f, `power2.inOut`.
- 36-48 f: fill fades up 0 to 1 while stroke fades out (12 f).
- 48-84 f: hold (36 f, 1.2 s).
- 84-90 f: anticipation, word squeezes to 96% width (6 f, `power2.in`).
- 90-108 f: spring wide. E arms (horizontal strokes) extend 2.5-3.5x, O splits at its vertical centre and its halves slide apart joined by straight lines (capsule), 18 f `back.out(1.6)`; other letters spread with the new width.
- 108-150 f: hold (moving hold of a 1-2% drift) [39].
- Size: cap height 22-28% of frame height in 16:9 (each line), 13-16% of height in 9:16 with the two words stacked; line gap 0.08-0.12 of cap height.
- Margins: lockup never closer than 5% to frame edges after the spring.

## Build it
1. Convert the words to SVG paths at mount (opentype.js on the OFL font file) so each glyph's contours are editable.
2. Trace pass: draw paths with `fill: none; stroke` and animate `stroke-dashoffset` from `getTotalLength()` (registry `hw-write-title` and `stitched-text-draw` show the dash approach [41]).
3. Spring: for E, move the right-hand points of each arm's contour by `dx`; for O, split the contour at x = centre and translate the left/right halves by `±dx`, bridging with straight segments (top and bottom stay hairline thin).
4. Reflow: shift subsequent glyphs by the cumulative `dx` so spacing stays even.
5. Remotion: same paths; compute `dx` with `spring()` or `interpolate` + a back easing.

## Mistakes that look amateur
- Using a Didone at text size or a light weight for the hero → hairlines vanish [28]; use opsz 96 and wght 700-900.
- Scaling the whole word horizontally for the "spring" → thick strokes get fat and contrast breaks; extend only the horizontal strokes.
- No anticipation and no hold → reads as a glitch, not a spring [39].
- Mixing a second display face into the lockup → keep one Didone plus at most a small grotesque label.
- Trace with a thick stroke → loses the hairline elegance; 1-2 px at 1080p.
- Bright saturated palette → fights the fashion register; ink/paper/gold.

## Sources
[7] @tsumiki_room, stroke-font kinetic study — https://x.com/tsumiki_room/status/2096229986827182422
[21] GSAP Eases — https://gsap.com/docs/v3/Eases/
[22] Butterick, Letterspacing — https://practicaltypography.com/letterspacing.html
[27] google/fonts METADATA — https://github.com/google/fonts — axes, licenses
[28] Didone (Wikipedia) — https://en.wikipedia.org/wiki/Didone_(typography) — features, dazzle, optical sizes, mastheads
[29] Bodoni* README — https://github.com/indestructible-type/Bodoni — optical sizes, OFL
[30] Riso inks — https://rdrr.io/github/anfederico/risoinks/src/R/color.R — flat gold
[39] Netguru, 12 principles — https://www.netguru.com/blog/illustrators-eye-12-principles-of-animation — anticipation, moving hold
[41] HyperFrames registry — https://github.com/heygen-com/hyperframes/tree/main/registry — hw-write-title, stitched-text-draw
