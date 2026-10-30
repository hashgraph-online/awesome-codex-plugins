# Satellite flyover between two places

A camera that lifts off over one place on satellite imagery, flies along an arc and settles over a second place,
with the path drawn as it goes. Use it for "from A to B" moments: a trip, a shipment, a relocation, a launch. Formats
16:9, 9:16 and 1:1; typical length 6–10 s (preset default 8 s).

## How the pros do it
- **Pull out, travel, push in, on one van Wijk curve.** MapLibre's `flyTo` defaults (curve 1.42, speed 1.2) are the
  reference; `minZoom` caps how far out the arc goes. For a render, compute the path yourself and set the length in
  seconds instead of letting speed decide it. [10][11][12]
- **Tilt only near the ground.** Mapbox's flyover showcase ends at pitch 75 and bearing 130 after a 12 s fly from
  zoom 1 to 12.5, and its follow-camera example uses pitch 65 with terrain exaggerated 1.5×. Keep pitch at 0 while high
  (it hides the destination) and ramp it in during the last 30% of the move. [15][16]
- **Rotate slowly and constantly.** Mapbox's cinematic route films sweep the bearing 200° over the whole clip at a
  constant rate and smooth the camera with a lerp so the subject drifts back to centre. [14]
- **Do not chain `flyTo` for the fly-in.** Mapbox's team wrote a custom transition from a high globe view because
  `flyTo` was hard to blend with the free camera; capture frames on a fixed time step (they used 1000/60 ms). [14]
- **Use atmosphere at low zoom.** Fog with a soft horizon (the showcase uses `horizon-blend` 0.4; the globe guide
  shows 0.02 with stars at 0.6) sells the altitude. [16][19]
- **Terrain from elevation, not from guesswork.** FT's Steven Bernard builds relief scenes from a terrain plane, an
  emission plane and a mist volume in Blender; in GL JS, add a raster-dem source with exaggeration 1.5. [7][15]
- **Know the imagery licence before you render:**
  - Mapbox satellite: "© Mapbox © OpenStreetMap" plus "© Maxar". [21]
  - Esri World Imagery: "Sources: Esri, Maxar, Earthstar Geographics, and the GIS User Community", under Esri's licence. [28]
  - EOxCloudless: free only for non-commercial use (CC BY-NC-SA 4.0); commercial needs an EOX licence. [29]
  - Google Earth Studio: credit "Google Earth" and providers, burned in per frame; no licence without attribution. [30]
  - NASA Blue Marble (500 m/px) and Black Marble night lights: public domain, credit NASA. They are soft beyond about
    zoom 7, so use them for the high part of the arc only. [25][26][27]
- **Draw the route on top, in sync with the camera:** progress drives both the camera position and the line reveal
  (`line-gradient` step or `line-trim-offset`). [14][18]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `satellite-flyover.daylight` | True-colour satellite, white route, soft blue haze | route #FFFFFF 5 px + 10 px glow at 25%, pins #FF4D3D, fog horizon-blend 0.4, pitch 0→60, terrain 1.5× |
| `satellite-flyover.city-lights` | Night Earth, gold lights, cyan route | NASA Black Marble 13500×6750, route #6FE3FF 4 px + glow 14 px at 35%, pins #FFC861, space #05070D |
| `satellite-flyover.slate` | Desaturated graphite basemap, one accent route | basemap desaturate 100%, brightness 55%, route = brand accent 5 px, pins white 14 px with 3 px accent ring |

## Timing and numbers
Default 8 s = 240 frames at 30 fps.

| Beat | Time (s) | Frames | Camera | Overlay |
|---|---|---|---|---|
| Establish A | 0.0–0.8 | 0–24 | zoom zA (10–12), pitch 45, slow 2°/s orbit | pin A drops (0.35 s, `back.out(1.6)`), label A |
| Lift | 0.8–2.2 | 24–66 | zoom out on the van Wijk curve, pitch 45→0 | label A fades by 1.6 s |
| Travel | 2.2–5.6 | 66–168 | peak zoom = fit both points (or `minZoom`), bearing drift ≤ 15° total | route draws with progress |
| Descend | 5.6–7.0 | 168–210 | zoom in to zB, pitch 0→60 in last 30% | pin B drops at 6.8 s |
| Settle | 7.0–8.0 | 210–240 | hold, 2°/s orbit | label B, attribution |

- Path: rho 1.42 (MapLibre default) [10]; move ease `cubic-bezier(0.65,0,0.35,1)` [53]; total move 4.5–6 s for
  intercontinental, 3–4 s within one country.
- Zoom rate ceiling: ≈1 zoom level/s average (Mapbox showcase: 11.5 levels in 12 s) [16].
- Route line: 4–6 px at 1080p (Mapbox examples use 5–6) with round cap/join [15][17]; glow = same colour, 2–3× width, 25–35% opacity.
- Long-haul routes: great-circle via `d3.geoInterpolate`, 128 samples [13]; road/rail: real geometry simplified to ≤ 2 px error.
- Terrain exaggeration 1.5; camera altitude for close passes ≈ 4000 m [15].
- Output: render at the delivery size (1920×1080, 1080×1920, 1080×1080); Mapbox's team used 1280×720 and 1080×1080 with a 60 fps step [14].
- 9:16: keep both pins inside the middle 60% of height; labels never in the bottom 22% (house default).

## Build it
1. Starting points: the HyperFrames `nyc-paris-flight` block (pre-rendered realistic map + plane + landing pop) when a
   still map image is enough; `us-map-flow` for arcs over a flat map; the varg `remotion-maps` skill (MapLibre, Mapbox,
   MapTiler, CesiumJS flyovers) when you need live imagery and terrain.
2. Compute the whole camera path up front: `const zi = d3.interpolateZoom.rho(1.42)([ax, ay, wA], [bx, by, wB])` in
   Web-Mercator pixel space; map each frame's `[cx, cy, w]` back to lng/lat + zoom. [12]
3. Per frame (from the timeline, not a clock): `map.jumpTo({center, zoom, pitch, bearing})`; reveal the route with
   `line-trim-offset: [p, 1]` or a `line-gradient` step at progress `p`; then hold the frame until the map reports
   `idle`. Remotion: `delayRender` until idle; HyperFrames: drive from the paused timeline and let the renderer wait. [14][18]
4. Footage-only fallback (Google Earth Studio export): keep its burned-in attribution, overlay the route as SVG
   tracked to the two pins, and grade with ffmpeg `eq=saturation=0:brightness=-0.12` for the slate look.

## Mistakes that look amateur
- Straight line across a globe for a flight → great-circle arc. [13]
- Pitch 60 at the top of the arc (horizon fills the frame, destination hidden) → pitch 0 while high. [16]
- Camera jitter from following raw route points → lerp-smooth the target. [14]
- Rendering with the map's own animation clock → per-frame `jumpTo` from timeline time, wait for `idle`.
- Blurry close-ups from Blue Marble/Black Marble → switch to higher-resolution licensed imagery below ~zoom 7. [25][26]
- Cropping or covering the imagery attribution → keep provider credits readable. [21][28][30]
- EOX imagery in a paid ad without a commercial licence → licence it or use another source. [29]

## Sources
[7] Steven Bernard (FT) — Lake Garda Blender settings — https://x.com/sdbernard/status/1122180337612787713 — relief recipe
[10] MapLibre — FlyToOptions — https://maplibre.org/maplibre-gl-js/docs/API/type-aliases/FlyToOptions/ — defaults
[11] MapLibre — camera.ts — https://github.com/maplibre/maplibre-gl-js/blob/main/src/ui/camera.ts — duration formula
[12] d3 — interpolateZoom — https://d3js.org/d3-interpolate/zoom — path math
[13] d3 — geo math — https://d3js.org/d3-geo/math — great arcs
[14] Chris Whong & Moritz Förster (Mapbox) — Cinematic route animations — https://www.mapbox.com/blog/building-cinematic-route-animations-with-mapboxgl — follow camera, 200° sweep, frame capture
[15] Mapbox — free camera path example — https://docs.mapbox.com/mapbox-gl-js/example/free-camera-path/ — pitch 65, terrain 1.5, 4000 m
[16] Mapbox — flyto-options example — https://docs.mapbox.com/mapbox-gl-js/example/flyto-options/ — 12 s fly, fog 0.4
[17] Mapbox — ant path example — https://docs.mapbox.com/mapbox-gl-js/example/animate-ant-path/ — line width 6
[18] Mapbox — Style Spec layers — https://docs.mapbox.com/style-spec/reference/layers/ — line-trim-offset
[19] Mapbox — Globe guide — https://docs.mapbox.com/mapbox-gl-js/guides/globe/ — fog values
[21] Mapbox — Attribution — https://docs.mapbox.com/help/dive-deeper/attribution/ — © Maxar for satellite
[25] NASA EO — Blue Marble NG — https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/ — 500 m/px
[26] NASA EO — Earth at Night — https://science.nasa.gov/earth/earth-observatory/earth-at-night/maps — night lights
[27] NASA — media guidelines — https://www.nasa.gov/nasa-brand-center/images-and-media/ — credit, no endorsement
[28] Esri — World Imagery — https://doc.arcgis.com/en/data-appliance/latest/imagery-elevation/world-imagery.htm — attribution
[29] EOX — Cloudless licence — https://cloudless.eox.at/documentation/license — NC vs commercial
[30] Google — Earth Studio attribution — https://earth.google.com/studio/docs/attribution/ — burned-in credit
[53] easings.net — https://github.com/ai/easings.net/blob/master/src/easings.yml — easeInOutCubic
