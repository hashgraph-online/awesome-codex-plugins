# Hand-drawn radial burst

A sunburst of blocky rays, shaded with ordered dither and "boiling" like hand-drawn animation: a few slightly different drawings cycled at a low frame rate. For hooks, reveals, title cards and comic-style emphasis. 16:9, 9:16 and 1:1; 4–8 s.

Rights note: this describes a technique only. Do not trace, copy or imitate any specific illustrator's drawings; generate the rays procedurally.

## How the pros do it
- Build it in polar coordinates: `r = length(pos)·2`, `a = atan(pos.y, pos.x)`, then make the radius a function of the angle. Ray index = `floor(a / 2π · RAYS)`. [26]
- Hand-drawn feel comes from stepped time, not smooth motion: quantise time with `t = floor(t·n)/n`. A shader artist uses n = 24 for a "hand-drawn" fire; for a boil, step slower. [15]
- Line boil = a short loop of near-identical drawings: one practitioner traces 4 drawings and plays them at 8 fps on a loop. Here, each "drawing" is a new random seed for ray length, width and wobble. [38]
- Use 8 drawings at 80 ms each (12.5 fps): `seed = mod(floor(t / 0.08), 8.0)`; the loop repeats every 0.64 s, so it never reads as a GIF stutter but still boils.
- Shade the rays with ordered dither instead of gradients: 4x4 Bayer (level 1) is the most pleasing small matrix; normalise thresholds by the matrix size. [27][29]
- Keep dither cells and blocks large enough for video (4 px dither, 8 px blocks at 1080p); hi-contrast fine dither is destroyed by YouTube. [12]
- Keep the dither grid fixed to the screen while the rays boil underneath; moving the grid makes it swim. [10]
- For print variants, misregister a second ink by 2–4 px and multiply, and use warm black on off-white rather than #000 on #FFF. [33]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `signature` | Cream rays on warm black | bg #141210, ink #F2EEE3; 32 rays, width jitter 45%, length jitter 35%; 12 radial steps; 8 px blocks; 4x4 Bayer, 4 px cells; boil 8 drawings × 80 ms |
| `print` | Black ink on newsprint | bg #FBFAF4, ink #231F20; 8x8 Bayer, 3 px cells; paper grain 15% |
| `negative` | White on black, slow turn | bg #000000, ink #FFFFFF; 40 rays; rotation 4°/s (stepped with the boil) |
| `riso` | Pink + blue riso, misregistered | bg #FBFAF4, ink #FF48B0, 2nd ink #0078BF offset (3, -2) px, multiply |

## Timing and numbers
- Boil: 80 ms per drawing (12.5 fps); 8 drawings; ray endpoints wobble ±3 px at 1080p between drawings.
- Entrance: rays grow from r = 0 to full length over 0.4 s (5 boil steps), stepped, not eased; exit in 0.24 s (3 steps).
- Rays: 24–40; ray width at the rim 1.2–2× the gap; inner hole 6–10% of frame height for a logo or word.
- Radial falloff for dither tone: `tone = 1 - smoothstep(0.05, 1.1, r)`.

## Build it
1. Fragment shader:
   ```glsl
   float s = mod(floor(u_t/0.08), 8.0);                     // boil seed
   vec2 px = floor(gl_FragCoord.xy/8.0)*8.0;                // 8 px blocks
   vec2 p = (px - 0.5*u_res)/u_res.y;  float r = length(p)*2.0, a = atan(p.y,p.x);
   float k = floor(a/6.2831853*32.0);                       // ray index
   float len = 0.75 + 0.35*(hash(vec2(k,s))-0.5);
   float wid = 0.5 + 0.45*(hash(vec2(k,s+17.0))-0.5);
   float inRay = step(abs(fract(a/6.2831853*32.0)-0.5), wid*0.5) * step(floor(r*12.0)/12.0, len);
   float tone = 1.0 - smoothstep(0.05, 1.1, r);
   float ink = inRay * step(bayer4(floor(gl_FragCoord.xy/4.0)), tone);
   ```
   `u_t` = timeline seconds only. [26][27][29]
2. HyperFrames: `sun-burst` block (cream and black rays turning) as a start, then add `ordered-dither-pass` over it; or the custom shader as a frame source. [39]
3. Paper fallback for crisp, non-hand-drawn sectors: Swirl with `twist: 0` ("straight sectoral shapes"), `bandCount: 12`, `softness: 0`, two colours. [18]

## Mistakes that look amateur
- Smooth continuous rotation → step everything on the boil clock. [15][38]
- Boil at 24–30 fps → 8–12.5 fps; faster reads as noise. [38]
- Smooth gradients inside rays → ordered dither. [27]
- 1–2 px dither → 3–4 px at 1080p. [12]
- Identical rays → jitter width and length per ray per drawing.
- Tracing a known artist's burst → procedural only.

## Sources
[10] Lucas Pope — sphere-mapped dither — https://x.com/dukope/status/933700786260910080
[12] Lucas Pope — hi-contrast dither on YouTube — https://x.com/dukope/status/490854690297364480
[15] Mirza Beig — hand-drawn stepped time — https://x.com/TheMirzaBeig/status/2007826704769618278
[18] Paper — Shaders reference — https://shaders.paper.design/llms.txt — Swirl twist 0
[26] The Book of Shaders ch. 07 — https://thebookofshaders.com/07/
[27] Surma — Ditherpunk — https://surma.dev/things/ditherpunk/
[29] Wikipedia — Ordered dithering — https://en.wikipedia.org/wiki/Ordered_dithering
[33] Paper blog — Retro print CMYK halftone — https://paper.design/blog/retro-print-cmyk-halftone-shader
[38] Jason Boone — line boil animations, PremiumBeat — https://www.premiumbeat.com/blog/how-to-create-line-boil-animations/
[39] HeyGen HyperFrames registry — `sun-burst`, `ordered-dither-pass`
[35] risoinks colour table — https://rdrr.io/github/anfederico/risoinks/src/R/color.R — riso ink hex values
