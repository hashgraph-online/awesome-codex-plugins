# Halftone footage

Turns real footage into halftone print (one ink on paper, or CMY process screens forming rosettes), an LED wall of round diodes, or a flat colour mosaic. Use it for editorial, comic, poster and music beats, and for print-themed intros. Works in 16:9, 9:16 and 1:1. Shots run 2–8 s and read best at full screen.

## How the pros do it
- **Dot area tracks tone.** Use radius ∝ sqrt(coverage), so the inked area is proportional to darkness. A plain radius = k·(0.1 + luma) is the quick version. [32]
- **One colour per cell,** sampled at the cell centre, so colour edges never cut a dot in half. [33][32]
- **Rotate screens:** CMYK at 15° / 75° / 0° / 45° (C / M / Y / K). Identical overlapping grids make moiré, and rotated ones form rosettes. [32][31][29]
- **Line screens:** newsprint is about 85 lpi and coated paper 85–185 lpi. Round dots meet at 70% tone, square dots at 50% (detailed images, but harsh on skin). [31]
- **Anti-alias the dot edge** with `smoothstep` over about 0.02 of a cell, or `fwidth`. Hard thresholds alias badly on screens. [32]
- **Print inks, not RGB primaries:** C #00B3FF, M #FC4F9D, Y #FFD900, K #231F20 on paper #FBFAF4. Blend dots subtractively (multiply), and add slight grid noise for a loose print head. [33]
- **Make it read as print.** HyperFrames' Editorial Halftone uses a real four-angle CMYK raster with a warm paper base. It is tuned only by amount (0.75–1) and size (0.15–0.55), judged at output resolution. A "transparent dot texture over unchanged footage" is rejected. [29]

## Presets
| Preset | Look | Key values (1080p) |
|---|---|---|
| `ink-on-paper` | One dark ink on warm newsprint | cell 12 px (90 lines per frame height), 45° screen; ink #1B1B1F, paper #F4EFE3; shadow-lift curve 0/0.08 0.5/0.62 1/1; pre-blur σ 3; AA σ 0.6 |
| `cmy-color-screen` | Process-colour rosettes | cell 10 px; C from R at 15°, M from G at 75°, Y from B at 0° (K at 45° if added); subtractive |
| `led-wall` | Stadium LED screen | 12 px cells, round diode r 5.2 px, dark gaps; brightness boost imax 0.55; diode glow σ 5 at 0.6 |
| `square-mosaic` | Flat tiles with grout | 24 px tiles, 2 px #000000 grout |

## Timing and numbers
- Cell size vs viewing: 9:16 phone viewing needs cells ≥ 10 px at 1080 wide. Below 8 px the encoder smears the dots into grey (YouTube and Instagram re-encode).
- Lift shadows before screening: dark footage turns into solid ink. Aim the mid-grey subject at 35–60% coverage.
- Pre-blur the luma by σ ≈ cell/4 before thresholding. This approximates centre-of-cell sampling for the threshold method.
- Never animate the screen grid. Keep it fixed and let the footage move under it. A moving grid shimmers.
- Transitions: grow `halftone` from 0 → 0.94 over 12 frames (`power2.out`), or use the registry `halftone-dissolve` between shots.

## Build it
**ffmpeg (ink-on-paper, tested):** a pre-rendered rotated "spot function" screen feeds the `threshold` filter: output = luma < screen ? ink : paper. It is fast, and the dots grow with tone.
```bash
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 in.mp4)   # generated inputs are endless: always cap the output
S="255*clip(1-PI/2*(pow((mod((X*0.70711+Y*0.70711+8192),12)-6)/(12/sqrt(2)),2)+pow((mod((Y*0.70711-X*0.70711+8192),12)-6)/(12/sqrt(2)),2)),0,1)"
ffmpeg -i in.mp4 \
 -f lavfi -i "color=c=black:s=1920x1080:r=30,format=gray,geq=lum='$S',trim=end_frame=1,loop=-1:size=1,format=gbrp" \
 -f lavfi -i "color=c=0x1B1B1F:s=1920x1080:r=30,format=gbrp" -f lavfi -i "color=c=0xF4EFE3:s=1920x1080:r=30,format=gbrp" \
 -filter_complex "[0:v]format=gray,curves=all='0/0.08 0.5/0.62 1/1',gblur=sigma=3,format=gbrp[l];[l][1:v][2:v][3:v]threshold,gblur=sigma=0.6,format=yuv420p[v]" \
 -map "[v]" -map '0:a?' -t "$DUR" -c:v libx264 -crf 14 out.mp4
```
- Screen math: rotate (X, Y) by θ, take the distance d from the cell centre normalised by half the cell diagonal, and set threshold = 255·(1 − π/2·d²). The ink area then equals the darkness.
- CMY: `extractplanes` R, G and B, threshold each against its own screen at 15° / 75° / 0°, then `mergeplanes`.
- LED wall: `pixelize=w=12:h=12`, multiply by a pre-rendered round-diode mask, boost brightness, then add a small glow. Mosaic: `pixelize=w=24:h=24` times a grout mask.
- Use crf ≤ 14 for delivery, because dots are high-frequency detail. All chains are in `assets/presets/halftone-footage.json`.

**HyperFrames:** Editorial Halftone payload `{"intensity":1,"adjust":{"contrast":0.04,"saturation":0.04},"effects":{"halftone":0.94,"halftoneSize":0.36}}`. For one ink, use the Monochrome Screen Print recipe. For two inks, Two-Ink Editorial Print (vermilion/teal). [29] Registry: `halftone-field` (plasma LED wall under type) and `halftone-dissolve` (transition). Paper Shaders' `halftone-dots` and `halftone-cmyk` take stills only, not `<video>`.

**Remotion:** `halftone({shape: 'circle', dotSize: 12, rotation: 45, colorMode: 'solid', dotColor: '#1B1B1F'})` over a paper-coloured `<Solid>`. For the LED wall, `colorMode: 'source', dotSpacing: 12, dotSize: 10`. [28]

## Mistakes that look amateur
- 0° screen for single ink (the dot rows read as a grid) → 45° for K or a single ink.
- Identical angles for colour screens (moiré) → 15 / 75 / 0 / 45.
- Pure RGB dots on pure white → print inks and a warm paper hex.
- Dark footage becoming a black slab → lift shadows first.
- Dots < 8 px on social video (the encoder turns them into mush) → ≥ 10 px cells and crf ≤ 14.
- A dot overlay multiplied over the unchanged image → actually re-render the image as dots.

## Sources
[10] FFmpeg Filters Documentation — https://ffmpeg.org/ffmpeg-filters.html
[28] Remotion — halftone() — https://www.remotion.dev/docs/effects/halftone
[29] HyperFrames — media-treatment recipes — https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/media-use/references/media-treatment-recipes.md
[31] Wikipedia — Halftone — https://en.wikipedia.org/wiki/Halftone
[32] Maxime Heckel — Shades of Halftone — https://blog.maximeheckel.com/posts/shades-of-halftone/
[33] Paper (Ksenia Kondrashova, Agu Seguí) — Retro print: CMYK halftone shader — https://paper.design/blog/retro-print-cmyk-halftone-shader
