# Vector route map

A clean, flat vector map where a route draws itself from start to finish, a small traveller (plane, car, dot) rides
the line, and stops pop in as it passes them. Use it for itineraries, delivery and logistics stories, road trips,
expansion maps. Formats 16:9, 9:16 and 1:1; typical length 6–10 s (preset default 8 s).

## How the pros do it
- **Build the map as vector so each part can move.** Make maps as SVG so they can be animated (Joshua Stevens);
  Natural Earth vectors are public domain and need no credit. [5][24]
- **Reveal the line with a dash offset tied to progress.** DrawSVG animates `stroke-dashoffset`/`stroke-dasharray`;
  `drawSVG:"0 5%" → "95% 100%"` slides a fixed-length dash along the path. In Mapbox/MapLibre GL, `line-trim-offset`
  (GL JS ≥ 2.9) or a `line-gradient` step does the same on a GeoJSON line. [14][18][34]
- **Keep the traveller glued to the line tip.** Use one progress value for both: `motionPath` with
  `autoRotate:true` and `alignOrigin:[0.5,0.5]` for the icon, `drawSVG` for the stroke, same timeline position. [35]
- **Ant-path for "in transit" holds.** Mapbox's pattern: an underlay line (width 6, opacity 0.4) under a dashed line
  (width 6, dasharray `[0,4,3]`) whose dash offset steps every 50 ms. For video, advance the dash phase from timeline
  time instead of a timer. [17]
- **Use great-circle curves for flights, real geometry for roads.** `d3.geoInterpolate` gives the great arc; road
  routes come from GPX/GeoJSON simplified to the output resolution. [13]
- **Slow-in slow-out on the draw, with stops as beats.** Heer & Robertson: about 1 s per simple transition, ease in and
  out, and stage complex changes. For a multi-stop route, ease each leg separately and dwell 0.3–0.5 s at each stop. [46]
- **Follow camera only when the route leaves the frame.** Mapbox's cinematic films lerp the camera toward the line tip
  so it drifts back to centre; if the whole route fits, keep the camera still and let the line do the work. [14]
- **Quiet ambient motion on the hold** (pulsing destination ring, slow dash crawl), not bouncing icons. [8]
- **Credit the data you used:** OSM-derived basemaps need "© OpenStreetMap contributors" in a corner while the map is
  the focus, plus credits; Mapbox styles add "© Mapbox". Natural Earth needs nothing. [21][22][24]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `vector-route-map.clean-light` | Light grey land, white water, one bold accent route | bg/water #F4F6F8, land #E3E7EB, borders #C9D0D6 1 px, route #2F6BFF 6 px, stop dots 12 px white with 3 px route-colour ring, label Inter 600 |
| `vector-route-map.night-transit` | Dark navy map, glowing route, ant-path crawl on hold | water #0B1220, land #16213A, borders #26355A, route #4FD1C5 5 px + glow 12 px at 30%, ant dash `14 10` px crawling 40 px/s |
| `vector-route-map.multi-stop` | Itinerary with numbered stops and leg labels | legs drawn one by one, numbered badges 28 px (Inter 700 on accent), dwell 0.4 s per stop, leg distance label 2.4% frame height |

## Timing and numbers
Default 8 s = 240 frames at 30 fps (single leg).

| Beat | Time (s) | Frames | Motion | Ease |
|---|---|---|---|---|
| Map in | 0.0–0.6 | 0–18 | map fades 0→1, scale 1.03→1 | emphasized-decelerate `cubic-bezier(0.05,0.7,0.1,1)` [52] |
| Start pin | 0.6–1.0 | 18–30 | pin pops 0→1.1→1, label A | `back.out(1.6)` |
| Draw | 1.0–5.8 | 30–174 | route draws, traveller rides tip | easeInOutSine `cubic-bezier(0.37,0,0.63,1)` [53] |
| Arrive | 5.8–6.4 | 174–192 | end pin pops, ring pulse 1→1.8 scale, 0.6 s | `power2.out` |
| Hold | 6.4–8.0 | 192–240 | label B, optional ant-path crawl, attribution | linear |

- Draw speed (house default): a constant on-screen speed of 25–45% of the frame width per second; split long routes into legs.
- Multi-stop (house default): per leg 0.8–1.4 s + 0.3–0.5 s dwell; total ≤ 8 legs per 10 s.
- Line widths at 1080p: route 5–6 px (Mapbox examples use 5–6) [15][17]; casing/halo 2 px wider in the background
  colour; borders 1 px; coastlines 1 px at 60% opacity.
- Traveller icon: 3.5–4.5% of frame height, `autoRotate:true` (add 90° offset if the artwork points up) [35].
- Labels: city names 2.4–2.8% of frame height (Inter 600), titles 5–6%; always on a 4.5:1 contrast halo or plate [43].
- Projection: whole-world routes in Equal Earth or Natural Earth; one country in Albers/LCC; city scale in Web
  Mercator [20].

## Build it
1. Start from the HyperFrames `us-map-flow` block (arcs between cities over a base map) or `svg-stroke-trace`
   component (draws an authored path from its measured length); `offset-path-traveler` moves a slotted icon along a
   path with tangent rotation. For a GL basemap, use the varg `remotion-maps` skill.
2. Project the route GeoJSON with d3 (`geoPath(projection)`) into one SVG `<path>`; measure `getTotalLength()`.
3. One paused GSAP timeline: `tl.fromTo(route, {drawSVG:"0%"}, {drawSVG:"100%", duration:4.8, ease:"sine.inOut"}, 1.0)`
   and on the same position `tl.to(icon, {motionPath:{path:route, align:route, autoRotate:true, alignOrigin:[0.5,0.5]}, duration:4.8, ease:"sine.inOut"}, 1.0)`. [34][35]
4. Stops: precompute each stop's progress along the path; schedule its pop at that timeline time so it fires exactly
   when the tip passes.
5. Ant-path hold: set `stroke-dasharray:"14 10"` on a duplicate path and tween `strokeDashoffset` linearly from 0 to
   −(24 × n) so the dash crawls; never use `setInterval`. [17]

## Mistakes that look amateur
- Icon drifting ahead or behind the line tip → drive both from one progress value. [35]
- Straight lines for flights on a world map → great-circle arcs. [13]
- Line drawn at constant speed through a 2 s straight and a 0.2 s twisty bit, so it looks erratic → ease per leg and
  dwell at stops. [46]
- Labels overlapping the route → offset labels to the outer side of the curve and add a halo.
- Hairline route (1–2 px) that disappears after compression → 5–6 px at 1080p. [15][17]
- Missing data credit → OSM/Mapbox credit in a corner while the map leads. [21][22]

## Sources
[5] Joshua Stevens — SVG tip — https://x.com/jscarto/status/2114826779596599409 — vector maps animate
[8] John Nelson — subtle map animation — https://x.com/John_M_Nelson/status/2027406545420493180 — quiet motion
[13] d3 — geo math — https://d3js.org/d3-geo/math — great arcs
[14] Mapbox (Whong, Förster) — Cinematic route animations — https://www.mapbox.com/blog/building-cinematic-route-animations-with-mapboxgl — progress-driven reveal, lerp camera
[15] Mapbox — free camera path — https://docs.mapbox.com/mapbox-gl-js/example/free-camera-path/ — line width 5
[17] Mapbox — ant path — https://docs.mapbox.com/mapbox-gl-js/example/animate-ant-path/ — dash pattern
[18] Mapbox — Style Spec — https://docs.mapbox.com/style-spec/reference/layers/ — line-trim-offset
[20] Mapbox — Projections — https://docs.mapbox.com/mapbox-gl-js/guides/projections/ — projection choice
[21] Mapbox — Attribution — https://docs.mapbox.com/help/dive-deeper/attribution/
[22] OSMF — Attribution Guidelines — https://osmfoundation.org/wiki/Licence/Attribution_Guidelines
[24] Natural Earth — Terms — https://www.naturalearthdata.com/about/terms-of-use/
[34] GSAP — DrawSVGPlugin — https://gsap.com/docs/v3/Plugins/DrawSVGPlugin/
[35] GSAP — MotionPathPlugin — https://gsap.com/docs/v3/Plugins/MotionPathPlugin/
[43] Lisa Charlotte Muth — colours in style guides — https://www.datawrapper.de/blog/colors-for-data-vis-style-guides
[46] Heer & Robertson 2007 — https://idl.cs.washington.edu/files/2007-AnimatedTransitions-InfoVis.pdf
[52] Material 3 motion tokens — https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss
[53] easings.net — https://github.com/ai/easings.net/blob/master/src/easings.yml
