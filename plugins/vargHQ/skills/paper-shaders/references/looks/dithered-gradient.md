# Dithered gradient

A moving two-tone field built from ordered-dither dots, like newsprint, a riso print or an old monochrome screen. For interstitials, end cards, retro tech and editorial looks. 16:9, 9:16 and 1:1; 6–10 s.

## How the pros do it
- Use Paper's Dithering: `colorBack` + `colorFront`, a moving source `shape` (simplex, warp, dots, wave, ripple, swirl, sphere), `type` random / 2x2 / 4x4 / 8x8 Bayer, and `size` = pixel size of the dither grid (1–20). [18][19]
- Mount pixel looks at `minPixelRatio: 1` so cells land on output pixels; `size` is multiplied by the pixel ratio, so `size: 3` = 3 px cells at 1080p. [19][20]
- Ordered dithering tiles a threshold map: 4x4 Bayer produces 17 distinct patterns with two colours; the matrices are M2 = [0 2; 3 1]/4 and the 4x4/8x8 built from it recursively. [27][29]
- Bayer level 1 (4x4) and level 3 (16x16) look the best; dither in linear light, because sRGB dithering makes a gradient "bright way too quickly". [27]
- Keep cells big enough for video: Obra Dinn's 640x360 dither pixels were too big for the eye to blend at fullscreen, and its creator found hi-contrast dither "looks terrible on YouTube". At 1080p use 3–4 px cells; 1–2 px cells turn into grey mush after the platform re-encode. [12][41]
- If the output will be scaled (a 9:16 crop, a phone preview), blue noise survives downscaling better than Bayer; Bayer keeps more tonal range for characters and important objects. [11][13]
- A parameterised recipe that works on real UI: 4x4 Bayer, pixel block 2–9 px, threshold (m + 0.5)/16, 2–8 levels per channel. [17]
- Never scale or move the dither grid itself: screen-space dither "swims" when the image under it moves. Animate the source shape, keep the grid fixed; games solve this with surface-stable or sphere-mapped patterns. [10][14]
- Dither in shader code: `floor(col * SHADES + bayer) / SHADES`; white noise instead of Bayer gives a grungy look. [28]
- Use dithering "as little as possible": two inks, one tonal ramp. [41]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `signature` | Pale blue on near-black, warped field | speed 0.5; back #0B0B0F, front #9CC2FF; shape warp, type 4x4, size 3; minPixelRatio 1 |
| `newsprint` | Warm black on newsprint | speed 0.4; back #FBFAF4, front #231F20; shape simplex, type 8x8, size 3 |
| `riso` | Fluorescent pink on paper, optional riso-blue second layer | speed 0.5; back #FBFAF4, front #FF48B0; shape wave, type 4x4, size 4; 2nd layer #0078BF, frame +1500 ms, offset 3,2 px, multiply |
| `phosphor` | Green phosphor, chunky 2x2 | speed 0.6; back #020A04, front #41FF7A; shape ripple, type 2x2, size 4 |

## Timing and numbers
- Cell size at 1080p: 3 px (fine print), 4 px (riso / screen), 6–8 px (deliberately pixel-art). At 2160p double it.
- Speed 0.4–0.6: the field should drift about one cell per frame or less, or the pattern buzzes.
- Two inks only; for a second ink, duplicate the layer, change `colorFront`, offset 2–4 px and set `mix-blend-mode: multiply` (riso misregistration). [33]
- Delivery: export 1080p at high bitrate (or ProRes for review); check the uploaded file, not the local render. [11]

## Build it
1. Copy the varg `retro-dither` preset or Paper's `paper-dithering-*` from `vargHQ/skills/paper-shaders`; keep `mount.minPixelRatio: 1`. [20]
2. Mount through `paperFrameSource` at speed 0, frame from the timeline. [20]
3. To dither an existing scene or footage still instead, use HyperFrames `ordered-dither-pass` (Bayer, stateless per frame, reveal from 2-tone noise) or `halftone-field`. [39]

## Mistakes that look amateur
- 1–2 px cells at 1080p → 3–4 px; fine dither dies on upload. [12]
- Zooming or panning the dither layer → animate the shape underneath; keep the grid screen-fixed. [10][14]
- Full RGB dither with 4+ colours → two inks. [41]
- sRGB thresholds → linearise first, or the ramp blows out. [27]
- Default `minPixelRatio: 2` → cells get resampled and blur; set 1. [20]
- Pure #000/#FFF on paper looks → warm black #231F20 on #FBFAF4. [33]

## Sources
[10] Lucas Pope — sphere-mapped dither — https://x.com/dukope/status/933700786260910080
[11] Lucas Pope — blue noise vs Bayer when downscaled; 1080p60 ProRes — https://x.com/dukope/status/1300260173919866880, https://x.com/dukope/status/1300259933414330368
[12] Lucas Pope — hi-contrast dither on YouTube — https://x.com/dukope/status/490854690297364480
[13] Lucas Pope — blue-noise tonal range — https://x.com/dukope/status/525304273488211968
[14] Rune Skovbo Johansen — surface-stable dithering — https://x.com/runevision/status/1666067893447000066
[17] Kubai087 — ordered dither recipe — https://x.com/Kubai087/status/2115091203465290087
[18] Paper — Shaders reference — https://shaders.paper.design/llms.txt
[19] Paper — dithering.ts source — https://github.com/paper-design/shaders — Bayer tables, `size * u_pixelRatio`
[20] vargHQ — paper-shaders skill — `retro-dither`, `minPixelRatio: 1`
[27] Surma — Ditherpunk — https://surma.dev/things/ditherpunk/
[28] Xor — GM Shaders Mini: Dither — https://mini.gmshaders.com/p/gm-shaders-mini-dither
[29] Wikipedia — Ordered dithering — https://en.wikipedia.org/wiki/Ordered_dithering
[33] Paper blog — Retro print CMYK halftone — https://paper.design/blog/retro-print-cmyk-halftone-shader
[39] HeyGen HyperFrames registry — `ordered-dither-pass`, `halftone-field`
[41] Lucas Pope — Adventures in One Bit, PlayStation Blog — https://blog.playstation.com/2019/10/17/return-of-the-obra-dinn-adventures-in-one-bit-out-tomorrow/
[35] risoinks colour table — https://rdrr.io/github/anfederico/risoinks/src/R/color.R — Fluorescent Pink #FF48B0, Blue #0078BF
