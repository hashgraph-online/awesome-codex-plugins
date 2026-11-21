# Contour lines

A topographic map of isolines whose terrain slowly reshapes: a background for travel, outdoor, data, strategy and "the landscape is changing" stories. 16:9, 9:16 and 1:1; 8–10 s.

## How the pros do it
- Paper Shaders has no contour shader; write one fragment shader. Terrain = fBM heightfield; natural relief uses gain 0.5 (Hurst H = 1), which IQ measured against real mountain profiles. [22]
- Use 5 octaves, frequency ×2 per octave with a 0.5 rad domain rotation and a shift, or detune the lacunarity to 2.01 so octave peaks do not line up into artifacts. [22][25]
- One level of domain warp (`h = fbm(p + 4q)`) turns round blobs into ridges and valleys; a second octave fed back from the base layer adds realism. [16][21]
- Draw lines at constant pixel width, not constant height: compute the distance to the isoline as `|f| / |∇f|`, with the gradient from `dFdx`/`dFdy` (or `fwidth`), then `smoothstep(1·eps, 2·eps, de)`. Without this, lines get fat on flat ground and vanish on slopes. [23]
- Cartographic hierarchy: contours are brown on USGS maps; heavier index contours carry the elevation label; the interval is stated in the legend (10 ft for flat ground, 100 ft+ for steep). Make every 5th line the heavier index line. [34]
- Close lines mean steep ground, wide spacing means flat; keep a minimum spacing on screen (about 6 px at 1080p) by capping the number of levels, or steep areas alias into moiré. [23][34]
- Animate slowly: drift the noise domain at 0.03–0.06 units/s and scroll the level offset (`h + 0.015·t`) so lines march uphill. All from timeline seconds. [20]
- fBM in polar coordinates is a variation for a circular "radar" terrain. [8]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `signature` | Bone lines on charcoal | bg #121212; minor #EDE6D8 at 40%, index #EDE6D8; 22 levels, index every 5th; widths 1.4 / 2.8 px at 1080p |
| `survey` | USGS-style brown on cream, labels | bg #F3EBDC; minor #A0703F at 60%, index #8B5A2B; labels IBM Plex Mono 500, 18 px |
| `night` | Cyan on blue-black, glowing index lines | bg #050B14; minor #7FD4FF at 35%, index #7FD4FF; glow radius 6 px, 35% |
| `blueprint` | White lines on blueprint blue with grid | bg #1F4FA0; minor #E8F1FF at 40%, index #E8F1FF; 64 px grid at 12% |

Shared: fbm 5 octaves, gain 0.5, lacunarity 2.01, 0.5 rad rotation; freq 1.6 (on height-normalised uv); drift 0.04/s; level scroll 0.015/s.

## Timing and numbers
- Line widths at 1080p: minor 1.2–1.5 px, index 2.5–3 px; AA band ±0.75 px around the width.
- Levels: 18–26 across the height range; fewer for 9:16 phone viewing.
- Speed: a feature should move less than 5% of frame height per second, or the map reads as liquid.
- Labels (survey): index lines only, monospace 16–18 px at 1080p, rotated along the line, with a 4 px gap cut in the line. Font: IBM Plex Mono (OFL-1.1).

## Build it
1. Fragment shader skeleton:
   ```glsl
   float h = fbm(p*1.6 + vec2(0.0, u_t*0.04)) + 0.35*fbm(p*0.8 + 4.0*q);  // q = vec2(fbm(p), fbm(p+vec2(5.2,1.3)))
   float L = (h + 0.015*u_t) * 22.0;
   float de = abs(fract(L + 0.5) - 0.5) / fwidth(L);          // distance in pixels to nearest isoline
   float idx = step(mod(floor(L + 0.5), 5.0), 0.5);           // every 5th line
   float w = mix(1.4, 2.8, idx);
   float line = 1.0 - smoothstep(w*0.5 - 0.75, w*0.5 + 0.75, de);
   ```
   `u_t` = timeline seconds (never a clock). [22][23][25]
2. HyperFrames: wrap the shader in a frame source (`registerFrameSource({ ready, render(seconds) })`) the same way the paper-shaders skill does; Remotion: draw in `useLayoutEffect` from `useCurrentFrame()/fps`. [20]
3. Paper fallback for filled elevation bands (terraces) rather than lines: SimplexNoise with `stepsPerColor: 10`, `softness: 0`. [18]

## Mistakes that look amateur
- Thresholding `fract(h·N)` directly → uneven line weight; divide by `fwidth` (distance estimate). [23]
- All lines the same weight → heavier index line every 5th. [34]
- 40+ levels → moiré on steep ground; cap so spacing stays ≥ 6 px. [23]
- Blobby single-octave noise → 5 octaves, gain 0.5, plus one warp. [21][22]
- Fast morph → drift ≤ 0.06/s. 
- Labels on every line → index lines only. [34]

## Sources
[8] Ksenia Kondrashova — fBm noise in polar coordinates — https://x.com/uuuuuulala/status/1696846819244863949
[16] Mirza Beig — domain-warp feedback octave — https://x.com/TheMirzaBeig/status/1734567042882175412
[18] Paper — Shaders reference — https://shaders.paper.design/llms.txt — SimplexNoise stepsPerColor
[20] vargHQ — paper-shaders skill — frame-source pattern, timeline-only time
[21] Inigo Quilez — Domain warping — https://iquilezles.org/articles/warp/
[22] Inigo Quilez — fBM — https://iquilezles.org/articles/fbm/
[23] Inigo Quilez — Distance estimation — https://iquilezles.org/articles/distance/
[25] The Book of Shaders ch. 13 — https://thebookofshaders.com/13/
[34] USGS — US Topo map symbol guide — https://www.usgs.gov/ngp-standards-and-specifications/us-topo-map-symbol-guide
[24] Inigo Quilez — Palettes — https://iquilezles.org/articles/palettes/ — glow tint for `night`
