# Sources: map and data motion

Every URL below was opened during this research session (WebFetch, curl of the raw file, or the X API).
Numbers are stable: the reference files and preset JSONs cite them as `[n]`.
Templates: GD = globe-to-country dive, SF = satellite flyover, VR = vector route map, WR = watercolor route map,
CH = self-drawing chart, CU = count-up stat, VS = versus timeline, AV = audio visualizer.

## Practitioners on X

| # | Who | Why they count | Post | What we took | Used by |
|---|---|---|---|---|---|
| 1 | John Burn-Murdoch (@jburnmurdoch) | Chief data reporter, Financial Times; known for the FT Covid charts | https://x.com/jburnmurdoch/status/1369657097227546626 | Reveal context gradually; set the lower extent so it does not read as a hard floor; light gridlines instead of a dark baseline | CH, VS |
| 2 | John Burn-Murdoch | same | https://x.com/jburnmurdoch/status/1369657055494238215 | On a line chart, extending the y-axis to zero can add no clarity | CH, VS |
| 3 | John Burn-Murdoch | same | https://x.com/jburnmurdoch/status/1256313195095977986 | "Narrative legend": put the key's symbols into the subtitle text to cut on-chart labels | CH, VS |
| 4 | John Burn-Murdoch | same | https://x.com/jburnmurdoch/status/1419917498225512448 | Novel, non-standard designs impress few and are understood by fewer; prefer standard forms | CH, VS, CU |
| 5 | Joshua Stevens (@jscarto) | Cartographic editor at maps.com, former data-viz lead at NASA Earth Observatory | https://x.com/jscarto/status/2114826779596599409 | Build maps and graphics as SVG so they can be animated | VR, WR, GD |
| 6 | Steven Bernard (@sdbernard) | FT senior visual journalist and cartographer | https://x.com/sdbernard/status/1709835565384765780 | Sea-ice map animation with Blender relief; 720×720 square cut for social | GD, SF |
| 7 | Steven Bernard | same | https://x.com/sdbernard/status/1122180337612787713 | Terrain recipe: one plane for terrain, one emission plane, a cube for mist, rendered in Cycles | SF |
| 8 | John Nelson (@John_M_Nelson) | Esri cartographer, map-design writer | https://x.com/John_M_Nelson/status/2027406545420493180 (quoting https://x.com/ArcGISStoryMaps/status/2027111557809819782) | Calls subtle ambient symbol motion (lava creeping, smoke billowing) a masterclass: small looping motion, not big moves | GD, VR, WR |

## Articles, docs and specs: maps

| # | Source | Who | URL | What we took | Used by |
|---|---|---|---|---|---|
| 10 | MapLibre GL JS `FlyToOptions` | MapLibre maintainers | https://maplibre.org/maplibre-gl-js/docs/API/type-aliases/FlyToOptions/ | `curve` default 1.42 (avg from van Wijk 2003 user study; 1 = circular motion); `speed` default 1.2 screenfuls/s; `minZoom`, `maxDuration` | GD, SF |
| 11 | MapLibre `camera.ts` and `util.ts` source | MapLibre | https://github.com/maplibre/maplibre-gl-js/blob/main/src/ui/camera.ts and https://github.com/maplibre/maplibre-gl-js/blob/main/src/util/util.ts | Duration = 1000·S/V ms; `rho` limited by `minZoom`; default easing `bezier(0.25, 0.1, 0.25, 1)` | GD, SF |
| 12 | d3 `interpolateZoom` | Mike Bostock / d3 | https://d3js.org/d3-interpolate/zoom | van Wijk & Nuij smooth zoom-pan; default rho √2; `.duration` gives a recommended ms length; scale by V | GD, SF, VR |
| 13 | d3-geo math (`geoInterpolate`, `geoDistance`) | d3 | https://d3js.org/d3-geo/math | Great-arc interpolation between two lon/lat points | SF, VR, WR |
| 14 | "Building Cinematic Route Animations with MapboxGL" | Chris Whong, Moritz Förster (Mapbox), 2022 | https://www.mapbox.com/blog/building-cinematic-route-animations-with-mapboxgl | Route revealed with `line-gradient` step on progress; bearing sweeps 200° over the clip; lerp-smoothed follow camera; custom fly-in from a globe view instead of `flyTo`; capture at 1000/60 ms per frame; 1280×720 and 1080×1080 outputs | SF, VR |
| 15 | Mapbox example "Animate the camera along a path" | Mapbox docs | https://docs.mapbox.com/mapbox-gl-js/example/free-camera-path/ | pitch 65, terrain exaggeration 1.5, camera altitude 4000 m, line width 5, round cap/join, camera and target on two paths | SF, VR |
| 16 | Mapbox example "Fly to a location" with options | Mapbox docs | https://docs.mapbox.com/mapbox-gl-js/example/flyto-options/ | zoom 1 → 12.5, pitch 0 → 75, bearing 0 → 130 over 12 s; satellite style; fog `horizon-blend` 0.4; terrain 1.5 | GD, SF |
| 17 | Mapbox example "Animate a line" (ant path) | Mapbox docs | https://docs.mapbox.com/mapbox-gl-js/example/animate-ant-path/ | Underlay line width 6 opacity 0.4 + dashed line width 6, dasharray `[0,4,3]` stepped every 50 ms | VR |
| 18 | Mapbox Style Spec: layers | Mapbox | https://docs.mapbox.com/style-spec/reference/layers/ | `line-trim-offset` (GL JS ≥ 2.9) trims a GeoJSON line by 0–1 progress; `line-width` in px | VR, SF |
| 19 | Mapbox guide "Globe and Atmosphere" | Mapbox | https://docs.mapbox.com/mapbox-gl-js/guides/globe/ | Fog values: horizon-blend 0.02, star-intensity 0.6, space-color rgb(11,11,25) | GD |
| 20 | Mapbox guide "Projections" | Mapbox | https://docs.mapbox.com/mapbox-gl-js/guides/projections/ | Globe for most maps; Equal Earth / Natural Earth / Winkel Tripel for thematic world maps; Albers / Lambert conformal conic for one country; adaptive projections drift to Mercator as you zoom | GD, VR |
| 21 | Mapbox attribution guide | Mapbox | https://docs.mapbox.com/help/dive-deeper/attribution/ | Static/print: "© Mapbox, © OpenStreetMap"; satellite styles also need "© Maxar" | GD, SF, VR |
| 22 | OSMF Attribution Guidelines | OpenStreetMap Foundation | https://osmfoundation.org/wiki/Licence/Attribution_Guidelines | Video where the map is a major component: credit in a map corner plus end credits/description; on screen long enough to read; need not stay during pans/zooms; "© OpenStreetMap contributors" acceptable | all maps |
| 23 | OSMF Tile Usage Policy | OSMF | https://operations.osmfoundation.org/policies/tiles/ | No bulk/pre-emptive fetching; headless bots that pan/zoom are banned; generic user agents blocked → never render video from tile.openstreetmap.org | all maps |
| 24 | Natural Earth terms of use | Natural Earth | https://www.naturalearthdata.com/about/terms-of-use/ | Public domain, no credit required, commercial use fine | GD, VR, WR |
| 25 | Blue Marble: Next Generation | NASA Earth Observatory | https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/ | 500 m/pixel monthly composites (2004), topography/bathymetry variants; credit "NASA Earth Observatory" (imagery by Reto Stöckli) | GD, SF |
| 26 | Earth at Night maps (Black Marble) | NASA Earth Observatory | https://science.nasa.gov/earth/earth-observatory/earth-at-night/maps | 2016 night lights at 3600×1800, 13500×6750 (3 km), 86400×43200 (500 m, 21600² tiles); JPEG and GeoTIFF | GD, SF |
| 27 | NASA images and media usage guidelines | NASA | https://www.nasa.gov/nasa-brand-center/images-and-media/ | Generally not copyrighted in the US; acknowledge NASA; no implied endorsement; insignia/logos protected | GD, SF |
| 28 | Esri World Imagery (Data Appliance doc) | Esri | https://doc.arcgis.com/en/data-appliance/latest/imagery-elevation/world-imagery.htm | Attribution string "Sources: Esri, Maxar, Earthstar Geographics, and the GIS User Community"; licence via Esri agreement | SF |
| 29 | EOxCloudless licence summary | EOX IT Services | https://cloudless.eox.at/documentation/license | Non-commercial CC BY-NC-SA 4.0; commercial use needs an EOX licence; attribution text; no ESA/EC endorsement | SF |
| 30 | Google Earth Studio attribution | Google | https://earth.google.com/studio/docs/attribution/ | Credit "Google Earth" + providers visible whenever content shows; render watermarks it per frame; no licence without attribution | SF |
| 31 | Stamen Watercolor (Stadia Maps) | Stadia Maps | https://docs.stadiamaps.com/map-styles/stamen-watercolor/ | Credit Stadia Maps, Stamen Design, OpenStreetMap; missing tiles above z16 | WR |
| 32 | "A Guide to Simulating Watercolor Paint with Generative Art" | Tyler Hobbs (generative artist), 2017 | https://www.tylerxhobbs.com/words/a-guide-to-simulating-watercolor-paint-with-generative-art | Recursive midpoint deformation; base polygon ~7 rounds, +4–5 per layer; ~4% opacity per layer; 30–100 layers; per-segment variance; texture masks | WR |
| 33 | MDN `<feDisplacementMap>` | MDN | https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/feDisplacementMap | feTurbulence (baseFrequency 0.05, numOctaves 2) + displacement scale 50 → wobbly edges; formula scale·(C−0.5) | WR |
| 34 | GSAP DrawSVGPlugin docs | GSAP | https://gsap.com/docs/v3/Plugins/DrawSVGPlugin/ | Draw a stroke via dashoffset; `"0 5%"` → `"95% 100%"` moves a fixed-size dash; Firefox length bug, overshoot to 102% | VR, WR, CH |
| 35 | GSAP MotionPathPlugin docs | GSAP | https://gsap.com/docs/v3/Plugins/MotionPathPlugin/ | `motionPath:{path, align, autoRotate:true, alignOrigin:[0.5,0.5]}` for a traveler icon | VR, WR, SF |
| 36 | "Introducing Phosphor" | Joshua Stevens | https://www.joshuastevens.net/blog/introducing-phosphor/ | Ramps must change lightness monotonically; interpolate in Oklab; avoid red/green of similar lightness | GD, SF, VS, CH |

## Articles, docs and studies: data

| # | Source | Who | URL | What we took | Used by |
|---|---|---|---|---|---|
| 40 | FT Visual Vocabulary | Financial Times Visual Journalism Team | https://github.com/Financial-Times/chart-doctor/tree/main/visual-vocabulary | Columns "must always start at 0"; change-over-time forms (line, column, slope); "choosing the correct time period" for context | CH, VS |
| 41 | "Why our column and bar charts start at zero" | Datawrapper Academy | https://www.datawrapper.de/academy/why-our-column-and-bar-charts-start-at-zero | Truncated bar axes mislead (Pandey et al. 2015); alternatives: dot plot, line chart, plot the differences | CH |
| 42 | "What to consider when creating line charts" | Datawrapper Academy | https://www.datawrapper.de/academy/what-to-consider-when-creating-line-charts | Lines need not start at 0 (add a zero line if values approach 0); grey context lines; thicker key line; label colours match lines; markers only for irregular intervals; plain "Curved" interpolation | CH, VS |
| 43 | "A detailed guide to colors in data vis style guides" | Lisa Charlotte Muth (Datawrapper), 2022 | https://www.datawrapper.de/blog/colors-for-data-vis-style-guides | Grey for context; strongest colour for the key series; 3:1 contrast for marks, 4.5:1 for text; grids lighter than labels | CH, VS, CU |
| 44 | "How to design a useful color key" | Lisa Charlotte Muth, 2023 | https://www.datawrapper.de/blog/color-keys-for-data-visualizations | Direct labels beat keys; line charts are easiest to label directly | CH, VS |
| 45 | "Why many Datawrapper charts don't include axis labels" | Datawrapper Academy | https://www.datawrapper.de/academy/why-datawrapper-does-not-include-axis-labels-for-many-charts | Put units in the title/description; append the unit to the first tick | CH, VS |
| 46 | "Animated Transitions in Statistical Data Graphics" | Jeffrey Heer & George Robertson, IEEE InfoVis 2007 | https://idl.cs.washington.edu/files/2007-AnimatedTransitions-InfoVis.pdf | ~1 s transitions; slow-in slow-out; stage complex changes (axis rescale separate from values); stagger to reduce occlusion; tested 1.25 s and 2 s staged | CH, VS, CU |
| 47 | "Object Constancy" | Mike Bostock | https://bost.ocks.org/mike/constancy/ | Key-function joins so each mark keeps its identity; animate only when it aids understanding; else cross-fade or cut | CH, VS |
| 48 | "Enhance your data storytelling with animated charts" | Flourish | https://flourish.studio/blog/animated-charts/ | Break the story into steps; racing bars for rank change; annotations instead of clutter | CH, VS |
| 49 | CountUp.js README and source | Jamie Perkins (inorganik) | https://github.com/inorganik/countUp.js | Default 2 s, easeOutExpo; "smart easing": above 999, run linear then ease the last 333 units | CU, VS |
| 50 | MDN `font-variant-numeric` | MDN | https://developer.mozilla.org/en-US/docs/Web/CSS/font-variant-numeric | `tabular-nums` = equal-width figures (no jitter while counting) | CU, VS, CH |
| 51 | MDN `Intl.NumberFormat()` | MDN | https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat/NumberFormat | `notation:"compact"` (988M), significant-digit rules, `signDisplay:"exceptZero"` (+55%) | CU, VS, CH |
| 52 | Material 3 motion tokens (material-web source) | Google Material Design | https://github.com/material-components/material-web/blob/main/tokens/versions/v0_192/_md-sys-motion.scss | emphasized-decelerate cubic-bezier(0.05,0.7,0.1,1); durations short 50–200 ms, medium 250–400, long 450–600, extra-long 700–1000 | CU, CH, VS |
| 53 | easings.net (`src/easings.yml`) | Andrey Sitnik | https://github.com/ai/easings.net/blob/master/src/easings.yml | CSS curves: easeOutExpo (0.16,1,0.3,1), easeOutCubic (0.33,1,0.68,1), easeOutQuart (0.25,1,0.5,1), easeInOutCubic (0.65,0,0.35,1), easeInOutSine (0.37,0,0.63,1) | all |

## Docs and specs: sound visualizer

| # | Source | Who | URL | What we took | Used by |
|---|---|---|---|---|---|
| 60 | Web Audio API spec, AnalyserNode | W3C Audio WG | https://webaudio.github.io/web-audio-api/ | fftSize default 2048, power of 2 in 32–32768; smoothingTimeConstant 0.8; dB range −100…−30; Blackman window; smoothing X̂ = τ·X̂prev + (1−τ)·|X| | AV |
| 61 | MDN `AnalyserNode` | MDN | https://developer.mozilla.org/en-US/docs/Web/API/AnalyserNode | frequencyBinCount = fftSize/2 | AV |
| 62 | Remotion `visualizeAudio()` | Remotion | https://www.remotion.dev/docs/visualize-audio | numberOfSamples power of 2 (16 for lows/mids/highs, more for bars); smoothing averages prev/current/next frame; bass dominates, so convert with 20·log10 and map −100…−30 dB | AV |
| 63 | three.js `webaudio_visualizer` example | three.js | https://github.com/mrdoob/three.js/blob/dev/examples/webaudio_visualizer.html | fftSize 128 → 64-bin `DataTexture` fed to a shader | AV |
| 64 | p5.sound `fft.js` | Processing Foundation | https://github.com/processing/p5.js-sound/blob/main/src/fft.js | smoothing 0.8, 1024 bins; bands bass 20–140, lowMid 140–400, mid 400–2600, highMid 2600–5200, treble 5200–14000 Hz | AV |
| 65 | MilkDrop preset authoring guide | Ryan Geiss (MilkDrop author) | https://www.geisswerks.com/milkdrop/milkdrop_preset_authoring.html | bass/mid/treb ≈1 normal, <0.7 quiet, >1.3 loud; `_att` versions damped; `zoom += 0.1*(vol−1)` style mapping | AV |
| 66 | FFmpeg filters (showcqt, showfreqs, showwaves) | FFmpeg | https://ffmpeg.org/ffmpeg-filters.html | showcqt: log/musical scale E0–D#10, default 1920×1080, sono_g 3; showfreqs: win_size 2048, fscale log option, averaging; showwaves modes and scales | AV |
| 67 | "Character representation of grey scale images" | Paul Bourke | https://paulbourke.net/dataformats/asciiart/ | 70-level and 10-level ramps (" .:-=+*#%@"); sample half as often vertically | AV |
| 68 | librosa `beat.py` | librosa | https://github.com/librosa/librosa/blob/main/librosa/beat.py | beat_track defaults: sr 22050, hop_length 512, start_bpm 120, tightness 100 | AV |
| 69 | "Peak programme meter" | Wikipedia | https://en.wikipedia.org/wiki/Peak_programme_meter | Type I 5 ms integration, falls 20 dB in 1.7 s; Type II 10 ms, 24 dB in 2.8 s | AV |
| 70 | "VU meter" | Wikipedia | https://en.wikipedia.org/wiki/VU_meter | 300 ms rise time to 99%; 1–1.5% overshoot | AV |
| 71 | HyperFrames `hyperframes-creative` skill: `references/audio-reactive.md` + `scripts/extract-audio-data.py` | HeyGen HyperFrames | installed skill (`~/.claude/skills/hyperframes-creative/`), repo https://github.com/heygen-com/hyperframes | FFT 4096 @ 44.1 kHz ≈ 10.8 Hz/bin; 30 Hz–16 kHz log bands; per-band normalization; per-frame `tl.call` sampling; text 3–6% scale, shapes 10–30% | AV, CU |

## Cinematic analysis

Thin for this family. The closest long-form craft analysis we opened is the Mapbox cinematic route post [14] (how a
follow camera is staged for documentary-style route films) and Steven Bernard's FT animation threads [6][7]. Heer &
Robertson [46] is the research backbone for chart animation timing. No title-designer or editor interviews were
relevant enough to encode.
