# Type specimen grid

One word set many ways (weights, widths, sizes, cases, styles) on a ruled Swiss grid, intercut with photos, like a printed type specimen in motion. Good for brand launches, font or product name reveals, editorial intros. 16:9, 9:16, 1:1; 10-15 s.

## How the pros do it
- Lay the grid before the type: a mathematical grid, asymmetric placement, a grotesque sans, photography instead of illustration [25].
- Use one variable family for most of the cells so the variety comes from axes, not from unrelated fonts: weight, width and optical size are separate axes [26]. Archivo gives wdth 62-125 and wght 100-900 in one file [27].
- When animating axes, animate `font-variation-settings` directly; CSS variables do not interpolate, and any axis you leave out resets to default [26].
- Use a Didone with optical sizes for the serif cells: big sizes take the high-contrast cut, small ones the sturdier cut [28][29].
- Track caps open (+0.05 to +0.12em), never track lowercase, tighten very large lowercase [22].
- Specimen meta (name, weight, size in pt, glyph count) set in mono at label size, as a printed specimen would.
- Variable display fonts are the go-to for titles and type animation [6].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `type-specimen-grid.swiss` | 18 cells on a 6x3 ruled grid, black on paper, red accent cell | Archivo wght 100-900 x wdth 62-125, Inter labels, rules 1 px #111111 at 40%, paper #F2EFE8, accent #E4002B |
| `type-specimen-grid.riso` | Same grid printed in two riso inks with overprint | ink 1 #3255A4, ink 2 #FF48B0 [30], multiply, 2 px misregistration |
| `type-specimen-grid.serif` | Didone + grotesque pairing, waterfall of sizes | Bodoni Moda opsz 6-96 + Inter, sizes 12/18/28/44/72/120/200 px |

## Timing and numbers
- 18 settings in 14 s at 120 BPM = 28 beats: one new cell per beat for 18 beats (9 s), photo cuts on beats 6, 12, 18 for 2 beats each, final 4 beats hold on the hero cell.
- Each cell: type appears with a hard cut (0 f) or a 6-8 f mask wipe from the cell edge, `power3.out`; never fade.
- Axis morph inside a cell: 12-18 f, `power2.inOut`, per-character stagger 0.04-0.06 s (registry default 0.06 s [41]).
- Grid at 1920x1080: 6 columns x 3 rows, 96 px margin, 24 px gutter, cell 272 x 272 px; at 1080x1920: 3 columns x 6 rows; at 1080x1080: 3 x 3 with 2 pages.
- Rules: 1 px at 1080p, ink at 35-45% opacity; labels Inter 500 14-16 px caps +0.1em or JetBrains Mono 400 14 px.
- Cell word size: fill 70-85% of cell width (fit-text measured once at mount).

## Build it
1. HyperFrames: start from the `swiss-grid` example for the grid, and `variable-font-flex` or `variable-axis-type` for axis morphs [41].
2. Measure each cell's word width once (canvas `measureText` or a userland measurer [9]) and solve font-size for the target fill.
3. Build cells as absolutely positioned divs on the grid; reveal each with `clip-path: inset()` tweens on the beat.
4. Photos: cut in full-cell or full-frame for 2 beats, cropped to the grid; desaturate 0-30% to sit with the type.
5. Remotion: identical layout; axis values from `interpolate(frame, ...)` written into `fontVariationSettings`.

## Mistakes that look amateur
- 18 different fonts instead of one family's axes → reads as a font menu, not a specimen; vary axes, add at most 2 contrast faces.
- Animating `--wght` CSS variables → nothing moves; animate `font-variation-settings` [26].
- Hairline Didone set small → it "dazzles"; use the small optical size [28].
- Centered symmetric layout → loses the Swiss feel; anchor to columns asymmetrically [25].
- Letterspaced lowercase → do not [22].
- Fades between cells → hard cuts or wipes on the beat.

## Sources
[5] @natAndrewson, riso print — https://x.com/natAndrewson/status/1262744907355058186 — two-ink riso set
[6] @ilovetypography, variable font picks — https://x.com/ilovetypography/status/1576905152849510401 — variable display faces for animation
[9] @_chenglou, text measurement — https://x.com/_chenglou/status/2037713766205608234 — measure without reflow
[22] Butterick, Letterspacing — https://practicaltypography.com/letterspacing.html
[25] PRINT, Swiss Style — https://www.printmag.com/?p=1387 — grid, asymmetry, grotesque, photography
[26] web.dev, Variable fonts — https://web.dev/articles/variable-fonts — axes and animation caveats
[27] google/fonts METADATA — https://github.com/google/fonts — Archivo axes, licenses
[28] Didone (Wikipedia) — https://en.wikipedia.org/wiki/Didone_(typography) — optical sizes, dazzle
[29] Bodoni* README — https://github.com/indestructible-type/Bodoni — optical sizes, OFL
[30] Riso inks — https://rdrr.io/github/anfederico/risoinks/src/R/color.R — ink hexes
[41] HyperFrames registry — https://github.com/heygen-com/hyperframes/tree/main/registry — swiss-grid, variable-font-flex
