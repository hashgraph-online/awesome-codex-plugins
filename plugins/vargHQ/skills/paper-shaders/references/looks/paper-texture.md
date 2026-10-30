# Paper texture

Crumpled, folded or printed paper as a full-frame background, or as a finish laid over a still, a poster or a title card. For editorial, craft, collage, zine and documentary looks. 16:9, 9:16 and 1:1; 4–10 s.

## How the pros do it
- Use Paper's PaperTexture: it works standalone or over an image. Surface patterns: `roughness` (fine grain), `fiber` (curly threads), `folds` (straight fold lines with `foldSizeX/Y`, `foldOffsetX/Y`), `wrinkles` (repeating facets), `crumples` (`crumpleCount` 2–15 irregular facets), `drops` (water marks). [5][18]
- `angle` sets the light direction (clockwise from the top) and the direction of laid-paper rows; combine it with `seed` (0–1000) for endless variations. [5][18]
- `roughnessRows` 0 = even scatter, 1 = laid-paper stripes; `roughnessSize` sets grain size. [5]
- Over an image: `blending` 1 multiplies the image with the paper pattern, 0 keeps original colours; `distortion` (-1..1) bends the image with the surface; `clip: true` cuts the sheet to the image's alpha. [5][18]
- `colorPaper` with alpha (Paper's Flat uses #ffffffa8) lets `colorBack` show through for tinted stock. [18][20]
- The shader is static: changing `frame` does nothing. Animate it with the timeline instead: sweep `angle` 15–20° across the shot with `paramsAt`, or a 2–3% scale push on the host. [20]
- The rebuilt shader added fold lines, wrinkles, crumples, stripes, clipping and image blends specifically so designs read as real paper. [2]
- For printed paper, pair it with print-like content: round halftone dots, slight ink bleed, grid jitter, warm inks instead of digital primaries; apply grain separately from the halftone. [33]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `signature` | White sheet, folds, wrinkles, drops | scale 0.9; back #D3D2AB, paper #FFFFFF, shadow #CCCCCC; distortion 0.75, angle 300→320 over 10 s, seed 4; roughness 0.4/size 0.5, fiber 0.4/0.5, folds 0.5 (size 1/1), wrinkles 1 (size 0.65), drops 0.4 |
| `kraft` | Brown kraft, coarse fibers | back #6B4E2E, paper #C49A6C, shadow #8A6A45; seed 112, angle 300→315; roughness 0.7/0.4, fiber 0.8/0.7, crumples 0.6 (count 5), drops 0.1 |
| `newsprint` | Grey-cream, laid rows, one fold | back #D9D2C0, paper #ECE6D6, shadow #B9B09A; angle 0, seed 455; roughness 1/0.5, rows 0.6, fiber 0.7/1, folds 0.35 (x 0.5, y 1), drops 0.2 |
| `poster` | Folded poster over the user's art | back #FFFFFF00, paper #F7F3EAB5, shadow #B3B3B3; distortion -0.3, clip true, angle 236, seed 613; roughness 0.15/0.25, fiber 0.5, folds 1 (x 0.4, y 0.89) |
| `print` | Crumpled print, 4 facets | shadow #B3B3B3; distortion -0.5, angle 60, seed 49; roughness 0.4/0.25, fiber 0.4, crumples 1 (count 4) |

All presets: blending 1, timeScale 0 (static), every unused pattern at 0.

## Timing and numbers
- Light sweep: `angle` +15–20° over 10 s (linear) is enough to make the paper feel physical; more reads as a moving lamp.
- Distortion over an image: |0.3–0.75|; above 0.8 text in the image visibly bends.
- Type on paper: warm black #231F20, or a riso ink; avoid pure #000000. [33]

## Build it
1. Copy `paper-finish` or Paper's `paper-paper-texture-{default,creased,flat,spread}` from `vargHQ/skills/paper-shaders`; set `image` to the user's own still when used as a finish. [20]
2. Mount through `paperFrameSource` with `paramsAt: t => ({ angle: 300 + 20 * t / 10 })`. [20]
3. Reveals on paper: HyperFrames `torn-paper-rip`, `paper-collage-reveal`, `ink-bleed-reveal`. [39]

## Mistakes that look amateur
- Every pattern turned up at once → pick one hero (folds or crumples or wrinkles) plus roughness and fiber. [5]
- Same `seed` for every scene → change the seed per scene so creases do not repeat.
- Expecting `frame` to animate it → static shader; animate `angle` or the host. [20]
- `distortion` 1 over a poster with text → 0.3–0.5. [18]
- Pure white paper with grey shadows only → tint `colorPaper` (cream, kraft) for warmth. [18]
- Applying the shader to someone else's artwork → only the user's own or licensed images. [20]

## Sources
[2] Stephen Haney — new paper shader — https://x.com/stephenhaney/status/2105007065106419936
[5] Ksenia Kondrashova — PaperTexture rebuilt — https://x.com/uuuuuulala/status/2105014895309938878
[18] Paper — Shaders reference — https://shaders.paper.design/llms.txt
[20] vargHQ — paper-shaders skill — `paper-finish`, Paper Default/Creased/Flat/Spread values, static-shader rule
[33] Paper blog — Retro print CMYK halftone — https://paper.design/blog/retro-print-cmyk-halftone-shader
[39] HeyGen HyperFrames registry — `torn-paper-rip`, `paper-collage-reveal`, `ink-bleed-reveal`
