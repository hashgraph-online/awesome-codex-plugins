# Marbled ink

Colours folding into each other like marbled paper or ink on water. A rich, slow background for book, fashion, beauty, music and editorial titles. 16:9, 9:16 and 1:1; 8–10 s.

## How the pros do it
- Paper's Warp is the ready shader for this: noise and swirl warps over a base pattern (`checks`, `stripes`, `edge`), documented as "great for fluid, smoky, or marbled effects". `proportion` sets the colour split, `softness` the edge, `distortion` the noise warp, `swirl` + `swirlIterations` (2–20) the folding, `shapeScale` the base pattern zoom. [3][18]
- Marbling in custom GLSL is Inigo Quilez's domain warping: `f(p) = fbm(p + 4r)`, `r = (fbm(p + 4q + (1.7, 9.2)), fbm(p + 4q + (8.3, 2.8)))`, `q = (fbm(p), fbm(p + (5.2, 1.3)))`. The offsets only decorrelate the noise. [21]
- Colour from the warp's internals, not just f: ramp by f, then mix toward a third colour by |q| and a fourth by r. This gives the veined, layered look. [21][25]
- Animate by drifting the inner warp: The Book of Shaders adds `0.15 × t` and `0.126 × t` to the two r components (different rates so it never visibly repeats). [25]
- fBM for marble: 5 octaves, amplitude 0.5, frequency ×2, and rotate the domain 0.5 rad + shift 100 per octave to avoid axis-aligned artifacts; IQ also suggests detuning 2.0 to 2.01/1.99. [22][25]
- Extra realism: feed one more octave back into the warp from the base layer, as real-time VFX artists do for smoky orbs. [16]
- Physical marbling drops colours one after another, each spreading slightly less than the last, then combs and rakes them: give the first colour the largest share (`proportion` 0.35–0.5) and use `stripes` (a combed pass) with high swirl for the comb look. [40]
- Marble is the oldest procedural texture in film VFX: Perlin's noise built marble, fire and water and won a technical Academy Award. Slow, low-frequency warps read as stone; fast ones read as liquid. [21][42]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `signature` | Lavender and ink veins in warm white | Warp, speed 1.0; scale 1.2, rotation 30; #141218 #E9E4DA #8C7BD8 #E9E4DA; proportion 0.35, softness 0.15, distortion 0.25, swirl 0.85, iterations 10, stripes, shapeScale 0.3 |
| `ink` | Black veins in pale mint, hard edges | Warp, speed 1.5; scale 1.2, rotation 44; #111314 #9FAEAB #F3FEE7 #F3FEE7; proportion 0.05, softness 0, distortion 0.25, swirl 0.8, iterations 10, checks, shapeScale 0.28 |
| `ember` | Oxblood, rose, apricot folds | Warp, speed 1.5; scale 2.5, rotation 1.35; #3B1515 #954751 #FFC085; proportion 0.5, softness 1, distortion 0.09, swirl 0.9, iterations 6, checks, shapeScale 0.25 |
| `sage` | Moss, sage, bone on a split edge | Warp, speed 1.2; rotation 160; #1E2A22 #8FA88A #E6EBD9; proportion 0.45, softness 0.6, distortion 0.2, swirl 0.85, iterations 8, edge, shapeScale 0.5 |

Custom GLSL alternative (all presets): warp gain 4.0, q/r offsets as above, fbm 5 octaves / gain 0.5 / lacunarity 2.0 / 0.5 rad rotation, drift r by (0.15t, 0.126t); colours c0..c3 from the preset.

## Timing and numbers
- Warp's internal clock is `0.0625 × (u_time + offset)`, so it needs higher timeScale than other shaders: 1.0–1.5 for a slow 10 s background (Paper ships Live Ink at 2.5 and Passion at 3). [19][20]
- `softness` 0 = ink-sharp veins; 0.15 = polished stone; 1 = watercolour. [18]
- Title over marble: a 600–800 weight serif or grotesk in the background's lightest colour on a 30–40% dark scrim, or the darkest colour on light marble.

## Build it
1. Paper route: copy `paper-warp-live-ink` / `paper-warp-passion` from `vargHQ/skills/paper-shaders`, paste the params above, mount through `paperFrameSource`. [20]
2. Custom route: one fragment shader with IQ's `pattern(p, out q, out r)` and the four-colour mix; uniform `u_time = seconds` from the timeline only. [21][25]
3. Ready blocks in the HyperFrames registry: `marble` (ink-dark veins through white, WebGPU), `fractal-noise`, `domain-warp-dissolve` for a transition. [39]

## Mistakes that look amateur
- Single fbm with no warp → looks like clouds, not marble; warp at least twice (q and r). [21]
- Same speed on both r components → visible repetition; use 0.15 and 0.126. [25]
- No domain rotation between octaves → axis-aligned streaks; rotate 0.5 rad. [22][25]
- Warp at speed 0.3 copied from a mesh preset → almost frozen; Warp needs 1.0+. [19]
- Five saturated colours at equal share → one dominant ground colour plus 2–3 veins. [40]
- Complementary hues adjacent (red next to green) → brown seams; separate with the ground colour. [20]

## Sources
[3] Stephen Haney — Warp shader — https://x.com/stephenhaney/status/1882113262092976634
[16] Mirza Beig — domain-warp feedback octave — https://x.com/TheMirzaBeig/status/1734567042882175412
[18] Paper — Shaders reference — https://shaders.paper.design/llms.txt
[19] Paper — warp.ts source — https://github.com/paper-design/shaders — `t = .0625*(u_time+offset)`
[20] vargHQ — paper-shaders skill — Paper Live Ink / Passion values
[21] Inigo Quilez — Domain warping — https://iquilezles.org/articles/warp/
[22] Inigo Quilez — fBM — https://iquilezles.org/articles/fbm/
[25] Patricio Gonzalez Vivo, Jen Lowe — The Book of Shaders ch. 13 + clouds.frag — https://thebookofshaders.com/13/
[39] HeyGen HyperFrames registry — `marble`, `fractal-noise`, `domain-warp-dissolve`
[40] Wikipedia — Paper marbling — https://en.wikipedia.org/wiki/Paper_marbling
[42] Ken Perlin — Noise and Turbulence — https://mrl.cs.nyu.edu/~perlin/doc/oscar.html
