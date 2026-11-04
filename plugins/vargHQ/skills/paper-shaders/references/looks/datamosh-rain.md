# Datamosh rain

Coloured compression debris (macroblocks, smears, colour shears) falling in vertical streams over a near-black field. A background for tech, music, gaming and glitch openers, or behind a hacker-style title. 16:9, 9:16 and 1:1; 6–10 s.

## How the pros do it
- Paper Shaders has no glitch shader; write one fragment shader. Base the debris on real codec units: video macroblocks are 16x16 samples, subdivided into smaller transform and prediction blocks. Use 16 px blocks with 8 px and 4 px sub-blocks at 1080p. [36]
- Datamoshing is deliberate compression artifact: DCT blocks and smears that a codec leaves when data is missing. Copy those shapes (square blocks, vertical smear trails, colour shifts), not random noise. [37]
- Streams: one column per block (120 columns across 1920 px); per column a hashed fall speed between 120 and 600 px/s; a cell is on when `hash(column, cell) > 0.82` (18% density). [36]
- Re-roll block colours and sub-block splits on a stepped clock (12.5 fps, `floor(t·12.5)`), while the fall itself stays smooth; stepped time is what sells the digital stutter. [15]
- Smear: each lit block leaves a trail of 3–8 blocks above it fading by ×0.85 per block, like a predicted frame copying stale data.
- Colour shear: sample the debris mask with a 2–6 px horizontal offset per RGB channel inside a block.
- Keep blocks ≥ 8 px and avoid single-pixel noise: fine hi-contrast detail is what platform re-encodes destroy. [12][11]
- Palette from a cosine palette or a short list of 3–4 hex inks on near-black; integer `c` in IQ's formula keeps cycles seamless. [24]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `signature` | Pink, mint, bone on near-black | bg #060608; #FF3B6B #3BFFD5 #F5F0E6; 16 px blocks (8/4 sub); speed 120–600 px/s; density 18%; trail 3–8 blocks ×0.85; re-roll 12.5 fps; shear 2–6 px |
| `datamosh` | Magenta, cyan, acid lime, white; heavy smear | bg #050506; #FF00A8 #00E5FF #B6FF00 #FFFFFF; density 26%; trail 5–12 blocks |
| `phosphor` | Green terminal rain | bg #010A04; #2BFF88 #0E7A3E #B8FFD9; trail ×0.9; no shear |
| `ember` | Orange sparks, slow | bg #0A0402; #FF6C2F #FFB511 #B3260E; speed 80–360 px/s |
| `ice` | Pale cyan shards, sparse, fast | bg #02060C; #9CE8FF #4982CF #F2FBFF; density 12%; speed 240–900 px/s |

All: scanlines 6% opacity, 2-frame "keyframe flash" (whole field brightens 30%) every 2.5–4 s on a hashed schedule.

## Timing and numbers
- Fall speeds in px/s at 1080p; scale by frame height for other sizes (9:16 at 1920 tall: ×1.78).
- Stepped re-roll at 12.5 fps = every 80 ms; at 30 fps output that is a change every 2–3 frames.
- Leave a calm zone: dim debris to 30% inside the title's box (a rounded rect mask) so type stays readable.

## Build it
1. Fragment shader:
   ```glsl
   float col = floor(gl_FragCoord.x/16.0);
   float spd = mix(120.0, 600.0, hash(vec2(col, 1.0)));
   float y = gl_FragCoord.y + spd*u_t;
   float cell = floor(y/16.0);
   float roll = floor(u_t*12.5);                            // stepped re-roll clock
   float on = step(0.82, hash(vec2(col, cell)));
   float trail = 0.0; for (int k=1;k<8;k++) trail = max(trail, step(0.82, hash(vec2(col, cell - float(k)))) * pow(0.85, float(k)));
   vec3 c = palette(hash(vec2(col*7.0+cell, roll)));
   ```
   Add 8/4 px sub-blocks by a second hash on `floor(gl_FragCoord/8)`; RGB shear by evaluating the mask at x±shift per channel. `u_t` = timeline seconds. [36][15]
2. Wrap as a frame source in HyperFrames (as the paper-shaders skill does) or draw per frame in Remotion. [20]
3. Glitch transitions in and out: HyperFrames `glitch` block; RGB text: `caption-glitch-rgb`, `rgb-glitch-text`. [39]

## Mistakes that look amateur
- Per-pixel TV static → square 16/8/4 px blocks. [36]
- Everything re-rolling at 30–60 fps → 12.5 fps re-roll, smooth fall. [15]
- Rainbow palettes → 3–4 inks on near-black.
- Debris over the headline → 30% calm zone.
- 2–4 px debris → ≥ 8 px; fine detail dies on upload. [12]
- Wall-clock or `Math.random()` per frame → hash of (column, cell, step) only. [20]

## Sources
[11] Lucas Pope — compression of fine texture — https://x.com/dukope/status/1300260173919866880
[12] Lucas Pope — hi-contrast detail on YouTube — https://x.com/dukope/status/490854690297364480
[15] Mirza Beig — stepped time — https://x.com/TheMirzaBeig/status/2007826704769618278
[20] vargHQ — paper-shaders skill — frame-source pattern, determinism rules
[24] Inigo Quilez — Palettes — https://iquilezles.org/articles/palettes/
[36] Wikipedia — Macroblock — https://en.wikipedia.org/wiki/Macroblock
[37] Wikipedia — Compression artifact / datamoshing — https://en.wikipedia.org/wiki/Datamoshing
[39] HeyGen HyperFrames registry — `glitch`, `caption-glitch-rgb`, `rgb-glitch-text`
[35] risoinks colour table — https://rdrr.io/github/anfederico/risoinks/src/R/color.R — Orange #FF6C2F, Sunflower #FFB511 for `ember`
