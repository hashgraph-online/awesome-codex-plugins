# Globe-to-country dive

A spinning globe that turns and zooms down onto one country, which lights up and gets a label. Use it to open a story
set in a place ("This is Portugal"), for "where we ship" explainers, travel intros and news context. Formats 16:9,
9:16 and 1:1; typical length 7–10 s (preset default 9 s).

## How the pros do it
- **Use a smooth zoom-pan curve, not two separate moves.** The standard is van Wijk & Nuij's path: MapLibre's `flyTo`
  uses curve (rho) 1.42, the average picked by users in van Wijk's study; 1 gives a circular arc; d3 uses √2. Duration
  in MapLibre is `1000 · S / V` ms with V = speed 1.2 screenfuls/s. For video, compute the path yourself and drive it
  from timeline time. [10][11][12]
- **Keep the dive readable: about one zoom level per second.** Mapbox's own showcase flies zoom 1 → 12.5 (with pitch
  0 → 75 and bearing 0 → 130) in 12 s, ≈ 0.96 zoom levels/s. A globe-to-country dive covers only 3–5 levels, so 3.5–4.5 s
  is enough; faster than ~1.5 levels/s smears labels. [16]
- **Interpolate scale in log space and rotation along the great arc.** Constant zoom speed means `scale(t) = s0·(s1/s0)^e(t)`;
  the globe's centre should travel along `d3.geoInterpolate(from, to)` so it never cuts through the planet. [12][13]
- **Pick the projection for the end frame.** Globe for world-to-region moves; for the final country frame use a conic
  (Albers equal-area or Lambert conformal conic) when the country is large, because globe/orthographic shows only one
  hemisphere and conics minimise distortion for one region. Equal Earth / Natural Earth are for whole-world thematic frames. [20]
- **Stage the move.** Heer & Robertson found staged animation (one kind of change at a time) beats doing everything at
  once; finish most of the rotation before the last part of the zoom, and only then change colours. Use slow-in slow-out. [46]
- **Draw the map as vector (SVG or canvas from GeoJSON), not as tiles,** so every border, fill and label can be
  animated and the render is deterministic. Stevens' tip: make maps as SVG so they can be animated. [5]
- **Add only subtle ambient motion on the hold:** city lights shimmering, a slow atmosphere drift; John Nelson calls
  this kind of quiet symbol motion a masterclass. No bouncing. [8]
- **Data you can use freely:** Natural Earth vectors are public domain (no credit needed). NASA Black Marble night
  lights come at 3600×1800, 13500×6750 (3 km) and 86400×43200 (500 m); NASA imagery is generally not copyrighted, but
  credit NASA and never imply endorsement or use NASA logos. [24][26][27]
- **If you use OSM-based tiles,** put "© OpenStreetMap contributors" in a corner while the map is a major element and in
  the description/credits; it need not stay up during pans and zooms, but must be readable. Never render from
  tile.openstreetmap.org: headless bulk fetching is banned. [22][23]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `globe-country-dive.night-globe` | Dark space, city-lights globe, warm gold country | bg #05070D, Black Marble 13500×6750 texture, atmosphere rim #3A6EA5 at 35%, highlight #FFC861 border 3 px + glow 12 px, label Inter 800 |
| `globe-country-dive.atlas-paper` | Printed atlas: paper ocean, cream land, terracotta country | ocean #DCE7EA, land #F3EEE2, borders #9A8F7E 1 px, highlight #C8553D, graticule #BFCBD0 0.5 px, label Fraunces 700 |
| `globe-country-dive.flat-brand` | Flat two-tone globe for brand explainers | ocean = brand bg, land 12% lighter, highlight = brand accent, no texture, label Inter 700 |

## Timing and numbers
Default 9 s = 270 frames at 30 fps.

| Beat | Time (s) | Frames | Motion | Ease |
|---|---|---|---|---|
| Globe in + idle spin | 0.0–1.2 | 0–36 | fade/scale 0.92→1 in 0.6 s; spin 4°/s | emphasized-decelerate `cubic-bezier(0.05,0.7,0.1,1)` [52] |
| Telegraph target | 1.2–2.0 | 36–60 | target outline pulses once (stroke 1→3 px) | `power2.out` |
| Dive | 2.0–6.3 | 60–189 | rotation done by 70% of the dive; log-scale zoom to `fitExtent` with 12% padding | `cubic-bezier(0.65,0,0.35,1)` easeInOutCubic [53] |
| Reveal | 6.3–7.2 | 189–216 | neighbours dim to 35% opacity, country fill 0→100%, border draws 0.8 s | `power2.out` |
| Label | 7.2–7.8 | 216–234 | label rises 24 px, fades in | emphasized-decelerate [52] |
| Hold | 7.8–9.0 | 234–270 | ambient shimmer only (2–4% opacity wobble) | sine |

- Zoom budget: 3–5 zoom levels over 3.5–4.5 s (≈1 level/s, from [16]).
- Globe size at rest: diameter 84% of frame height (16:9), 78% of width (9:16), 80% of the short side (1:1).
- Final country frame: fit to the safe area with 12% padding; in 9:16 fit to the middle 60% of height so captions
  and platform UI keep the top 12% and bottom 22% clear (house default; check each platform's overlay).
- Label: 6–7% of frame height (Inter 800, letter-spacing −0.01em); sub-label 2.6% (Inter 500). Contrast ≥ 4.5:1 [43].
- Attribution corner text: 1.4–1.6% of frame height, 70% opacity, bottom-right, visible ≥ 3 s on the final hold.
- Graticule: 15° spacing, 0.5 px at 1080p.

## Build it
1. Start from the HyperFrames `world-map` block (D3 Natural Earth projection with a rotating globe inset) or the varg
   `remotion-maps` skill; do not rebuild the projection code. Data: Natural Earth 1:110m for the globe, 1:50m for the
   country close-up (public domain) [24].
2. Render the globe with `d3.geoOrthographic().clipAngle(90)`; for the night look draw the Black Marble equirectangular
   texture onto a three.js sphere (or a canvas re-projection) and the vector borders on top.
3. Drive everything from one paused GSAP timeline: a proxy object `{t:0}` tweened 0→1; on update compute
   `center = d3.geoInterpolate(start, target)(stage1(t))`, `scale = s0*Math.pow(s1/s0, stage2(t))`, then
   `projection.rotate([-center[0], -center[1]]).scale(scale)` and redraw paths. No `requestAnimationFrame`, no wall clock.
4. For large countries (span > ~15°), crossfade over 0.4 s to an Albers/LCC projection fitted with `fitExtent` at the
   end of the dive; small countries can stay orthographic. [20]
5. If you need real satellite or vector tiles (MapLibre), compute the camera per frame with `d3.interpolateZoom`
   (rho 1.42) and call `map.jumpTo()`, then wait for the map's `idle` before the frame is captured. Never use `flyTo`'s
   internal clock in a render. [10][11][12]

## Mistakes that look amateur
- Zooming linearly in scale (it rockets at the end) → interpolate scale exponentially / on a van Wijk curve. [12]
- Rotating and zooming and recolouring all at once → stage: rotate, then zoom, then colour. [46]
- Mercator world at the start (Greenland the size of Africa) → globe or Equal Earth for the world frame. [20]
- Label appears before the camera has settled → start the label after the move is ≥ 95% done.
- Tile seams, blurry raster at high zoom (Blue Marble is 500 m/px, soft past ~zoom 7) → vector borders on top, cap the zoom. [25]
- Missing or unreadable credit for OSM/Mapbox data → corner credit while the map is the focus + credits/description. [21][22]
- Globe spinning fast during the hold → ≤ 4°/s, or stop.

## Sources
[5] Joshua Stevens (cartographic editor, ex-NASA EO data-viz lead) — "Make your maps and graphics in SVG" — https://x.com/jscarto/status/2114826779596599409 — vector maps animate
[8] John Nelson (Esri cartographer) — subtle map animation post — https://x.com/John_M_Nelson/status/2027406545420493180 — quiet ambient motion
[10] MapLibre — FlyToOptions — https://maplibre.org/maplibre-gl-js/docs/API/type-aliases/FlyToOptions/ — curve 1.42, speed 1.2
[11] MapLibre — camera.ts / util.ts — https://github.com/maplibre/maplibre-gl-js/blob/main/src/ui/camera.ts — duration formula, default easing
[12] d3 — interpolateZoom — https://d3js.org/d3-interpolate/zoom — van Wijk path, rho √2
[13] d3 — geo math — https://d3js.org/d3-geo/math — geoInterpolate great arcs
[16] Mapbox — flyto-options example — https://docs.mapbox.com/mapbox-gl-js/example/flyto-options/ — zoom 1→12.5 in 12 s
[20] Mapbox — Projections guide — https://docs.mapbox.com/mapbox-gl-js/guides/projections/ — projection choice
[21] Mapbox — Attribution — https://docs.mapbox.com/help/dive-deeper/attribution/ — credit strings
[22] OSMF — Attribution Guidelines — https://osmfoundation.org/wiki/Licence/Attribution_Guidelines — video credit rules
[23] OSMF — Tile Usage Policy — https://operations.osmfoundation.org/policies/tiles/ — no bulk/headless fetching
[24] Natural Earth — Terms — https://www.naturalearthdata.com/about/terms-of-use/ — public domain
[25] NASA EO — Blue Marble NG — https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/ — 500 m/px
[26] NASA EO — Earth at Night maps — https://science.nasa.gov/earth/earth-observatory/earth-at-night/maps — night-light resolutions
[27] NASA — Images and media guidelines — https://www.nasa.gov/nasa-brand-center/images-and-media/ — usage rules
[43] Lisa Charlotte Muth — colours in style guides — https://www.datawrapper.de/blog/colors-for-data-vis-style-guides — contrast
[46] Heer & Robertson — Animated Transitions (InfoVis 2007) — https://idl.cs.washington.edu/files/2007-AnimatedTransitions-InfoVis.pdf — staging
[52] Material 3 motion tokens — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss — easing
[53] easings.net — https://github.com/ai/easings.net/blob/master/src/easings.yml — cubic-bezier values
