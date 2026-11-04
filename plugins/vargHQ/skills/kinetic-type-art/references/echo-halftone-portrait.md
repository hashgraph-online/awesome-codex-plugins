# Echo stack over halftone portrait

Two words repeated in stacked echoes (each copy offset and fainter) over a dot-screened portrait; the type tears away and leaves the face as contour moire lines. A 3-5 s poster-like opener for music, fashion, events. 16:9, 9:16, 1:1.

## How the pros do it
- An echo is N ghost copies of the moving element at time t - i·delta with opacity stepped down per ghost; the registry clamps echoes to 2-6 and lag to 0.03-0.3 s (default 4 and 0.09 s) [41].
- Echoes collapse into the settled element at rest, so the stack reads as motion, then resolves [41].
- Classic halftone screens sit at 0, 15, 45 and 75 degrees; the overlap makes a rosette moire that viewers accept, while other angle pairs make obvious moire [40]. For a deliberate contour moire, do the opposite: overlay two line screens a few degrees apart.
- Print the portrait as two inks: dot screen in one ink, type in the other, overprinted [5][30].
- Halftone and print texture as a shader on a still: Paper Shaders HalftoneDots (classic/gooey/holes/soft, square or hex grid) and HalftoneCmyk [42].
- Photocopy-grade grain on the portrait: levels crush and speckle grain [31].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `echo-halftone-portrait.mono` | Black dot portrait on paper, black echo type | paper #F2EFE8, ink #111111, dot cell 10 px at 45deg, 5 echoes, lag 0.06 s |
| `echo-halftone-portrait.riso` | Blue dots, fluorescent pink echoes | dots #3255A4, type #FF48B0 [30], multiply, paper #F4F1EA |
| `echo-halftone-portrait.night` | White dots on black, red echo stack | bg #0B0B0D, dots #F2EFE8, type #F15060 [30] |

## Timing and numbers (4 s = 120 f)
- 0-12 f: portrait dots grow from 0 to full size (dot radius ∝ luminance), `power2.out`.
- 12-60 f: words slam in on beats 1 and 2 (at 120 BPM: 15 f and 30 f); each arrival sweeps 400-700 px with 5 echoes at 0.06 s lag, opacities 0.8/0.6/0.4/0.25/0.12.
- 60-84 f: hold the stack (echoes frozen as a static repeat stack, offsets 0.18-0.25 of cap height).
- 84-96 f: tear: the type layer is masked away with a jagged horizontal tear moving top to bottom (12 f, `power2.in`); behind it the dot screen switches to two line screens (period 6-8 px, angles 0 and 3-6 deg), creating contour moire on the face.
- 96-120 f: hold moire portrait.
- Type: condensed caps (Anton, League Gothic) cap height 20-30% of frame height; +0.02em tracking.
- Dot cell: 8-12 px at 1080p (16:9), 10-14 px for 9:16 so it survives compression.

## Build it
1. Portrait: run the photo through paper-shaders `halftone-overlay` (HalftoneDots) or a canvas dot screen sampling luminance on a rotated grid (45 deg) [42].
2. Echo type: HyperFrames `echo-trail` (time-offset ghosts) for the arrival, then freeze into a static stack of clones with fixed offsets [41].
3. Moire: two canvases of parallel lines whose thickness follows luminance; rotate the second by 3-6 deg; multiply both.
4. Tear: SVG mask with a jagged polyline edge (seeded points every 20-40 px) translated down.
5. ffmpeg variant for footage: `format=gray,eq=contrast=1.4,noise=alls=10:allf=t` before the dot pass [33].

## Mistakes that look amateur
- Dot cell too small → H.264 smears it to grey; keep 8 px+ at 1080p.
- Screens at random angles → unplanned moire everywhere; use 45 deg for a single screen [40].
- Echo copies at equal opacity → reads as duplicate text, not motion; step opacity down.
- Echo stack never resolves → collapse or freeze it deliberately [41].
- Moire lines too thin → aliasing flicker; 2-4 px lines.
- Using a real person's photo without rights → use your own or licensed photos.

## Sources
[5] @natAndrewson, riso print — https://x.com/natAndrewson/status/1262744907355058186
[30] Riso inks — https://rdrr.io/github/anfederico/risoinks/src/R/color.R
[31] Envato Tuts+, photocopy textures — https://design.tutsplus.com/tutorials/how-to-create-photocopy-and-xerox-textures--cms-109034
[33] FFmpeg filters — https://ffmpeg.org/ffmpeg-filters.html
[40] US10560604B2, Halftone screens — https://patents.google.com/patent/US10560604 — 0/15/45/75 deg, rosette moire
[41] HyperFrames registry, echo-trail — https://github.com/heygen-com/hyperframes/tree/main/registry — 2-6 echoes, 0.03-0.3 s lag
[42] varg paper-shaders — https://github.com/vargHQ/skills/tree/main/paper-shaders — HalftoneDots, HalftoneCmyk
