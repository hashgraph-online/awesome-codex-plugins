---
name: maps-and-data-motion
description: >-
  Eight map and data animations with exact presets: globe-to-country dive, satellite flyover between
  two places, vector route map, watercolor travel route, self-drawing bar and line chart, count-up
  statistic, versus timeline (two numbers diverging over the years) and an audio visualizer (silk
  ribbons, wireframe terrain, ASCII stream). Presets give camera paths on the van Wijk zoom-pan curve,
  flight durations, line widths, chart rules (bars from zero, one accent series, direct labels),
  number formats and count-up easing, and FFT sizes, log bands and attack/release for audio, from Heer
  & Robertson's animation study, MapLibre and Mapbox, Datawrapper, John Burn-Murdoch (FT), the W3C Web
  Audio spec and MilkDrop. Map credits and tile licences are part of every preset. Use when a video
  needs an animated travel map, a route between cities, a flyover, an animated chart or statistic, or
  a music visualizer. NOT for interactive web maps or dashboards.
license: MIT
compatibility: >-
  HyperFrames 0.8 (npx hyperframes; brings Chrome, needs Node 22 and ffmpeg) or Remotion 4. Maps use
  MapLibre GL or SVG from Natural Earth; audio analysis precomputed with ffmpeg or the Web Audio API
  offline. No API key for vector maps; satellite tiles need the provider's plan.
metadata:
  author: vargHQ
  version: "0.1.0"
  varg.cost.typical: "0 credits; renders locally"
  varg.runtime.typical: "minutes per template, mostly render time"
  varg.models: "none"
  varg.outputs: "mp4, webm or mov (alpha) from HyperFrames or Remotion"
  varg.presets: "8 templates, 25 presets"
---

# Maps and data motion: travel maps, charts, counters and audio visualizers

Eight animations where the data or the place is the story. One paused timeline drives the camera, the numbers and the audio bands, so a frame renders the same on every pass, and the map credits are designed in rather than pasted on.

## Gates

- **Licensed tiles and credits.** Vector maps from Natural Earth (public domain) need no credit. Satellite and street tiles need the provider's plan and its credit string on screen; never render from tile.openstreetmap.org.
- **The person's real numbers.** Charts and counters show data the person gives you, with its source; never round a number into a different claim.
- **Seek-safe.** Every value is a function of timeline time; randomness is seeded by frame. No `Date.now()`, `requestAnimationFrame` or unseeded `Math.random()`.
- **No credits here.** These templates render locally for free. Generated footage, voice or music is the varg-ai skill: call `estimate_cost` and wait for the person's approval before any generation.

## Pick a template

8 templates, 25 presets. Each reference file has the same sections: how the pros do it (every rule cited), presets, timing and numbers, how to build it, mistakes that look amateur, sources. Each JSON file holds the same presets as machine-readable values.

| Template | Use it for | Presets | Files |
|---|---|---|---|
| **Audio visualizer** | Turns a soundtrack into silk ribbons, a scrolling wireframe terrain or an ASCII character field. | Silk ribbons, Wire terrain, ASCII stream | [`audio-visualizer.md`](references/audio-visualizer.md) · [`json`](assets/presets/audio-visualizer.json) |
| **Count-up statistic** | One big number counts to its value over footage or a plain background, lands with a small pulse and holds with a label. | Centre hero, Corner tag, Lower band, Split compare | [`count-up-stat.md`](references/count-up-stat.md) · [`json`](assets/presets/count-up-stat.json) |
| **Globe-to-country dive** | A globe turns and zooms onto one country, which lights up and gets a label. | Night globe, Atlas paper, Flat brand | [`globe-country-dive.md`](references/globe-country-dive.md) · [`json`](assets/presets/globe-country-dive.json) |
| **Satellite flyover between two places** | Camera lifts off over place A on satellite imagery, flies an arc and settles over place B while the route draws. | Daylight, City lights, Slate | [`satellite-flyover.md`](references/satellite-flyover.md) · [`json`](assets/presets/satellite-flyover.json) |
| **Self-drawing bar and line chart** | Bars grow from a zero baseline or a line draws with its value riding the tip, then one datum is highlighted. | Bars, Line, Editorial | [`self-drawing-chart.md`](references/self-drawing-chart.md) · [`json`](assets/presets/self-drawing-chart.json) |
| **Vector route map** | A route draws itself across a flat vector map with a traveller riding the line and stops popping in. | Clean light, Night transit, Multi-stop itinerary | [`vector-route-map.md`](references/vector-route-map.md) · [`json`](assets/presets/vector-route-map.json) |
| **Versus timeline** | Two values move in opposite directions on a shared axis while a year counter ticks, ending with a gap callout. | Light paper, Dark ink, Footage overlay | [`versus-timeline.md`](references/versus-timeline.md) · [`json`](assets/presets/versus-timeline.json) |
| **Watercolor travel route** | A hand-painted watercolour map where a dashed ink route draws between two places with handwritten labels. | Travel journal, Bold wash, Antique | [`watercolor-route-map.md`](references/watercolor-route-map.md) · [`json`](assets/presets/watercolor-route-map.json) |

## Workflow

1. **Match the request** to a template and one or two presets from the table. Say which and why in one line, and show the person the preset names with their one-line looks before building anything.
2. **Read the reference** for that template, and load its JSON. Take values from the JSON; do not re-guess them.
3. **Build it** the way the reference's "Build it" section says, starting from the named HyperFrames blocks or varg components where it names them. Drive every value from timeline time so any frame renders the same on a re-render.
4. **Fit it to the brand:** swap in the person's colors and fonts only where the reference allows, then re-check contrast and safe zones with the numbers in "Timing and numbers".
5. **Check a draft:** render stills at the key moments (entrance, hold, exit), go through "Mistakes that look amateur", and fix before the final render.


## Rules that hold for every template

1. One paused timeline drives everything: map cameras via per-frame `jumpTo` (never `flyTo`'s own clock), counters via a tweened proxy, audio via precomputed per-frame arrays.
2. Camera moves use the van Wijk zoom-pan curve (rho 1.42 in MapLibre, √2 in d3), scale interpolated in log space, about one zoom level per second.
3. About 1 s per simple transition, slow-in slow-out, staged (axis/camera first, values/colour second), stagger 0.05–0.08 s (Heer & Robertson).
4. Bars start at zero, lines need not; one accent series, the rest grey; direct labels instead of legends; units in the subtitle.
5. Numbers: tabular figures, compact notation, 2–3 significant digits, signed deltas; count with easeOutExpo cubic-bezier(0.16,1,0.3,1), linear-then-ease above 999.
6. Build maps as vector (SVG/canvas from Natural Earth, public domain) so every part animates; raster only for imagery.
7. Credits are part of the design: OSM corner credit while the map leads, © Mapbox / © Maxar, the Esri string, the Google Earth watermark; EOX imagery is non-commercial unless licensed; never render from tile.openstreetmap.org.
8. Audio: FFT 4096 per frame, log bands 30 Hz–16 kHz, dB −100…−30, per-band normalisation, fast attack / 150–600 ms release, text reacts at most 4–6%.
9. Holds get only quiet ambient motion (shimmer, dash crawl, 1–2% push-in), never bouncing.

## Built from

Heer & Robertson (InfoVis 2007); MapLibre/Mapbox docs and source; Datawrapper (Lisa Charlotte Muth); John Burn-Murdoch (FT); W3C Web Audio + Remotion + HyperFrames audio guide; Ryan Geiss (MilkDrop); Tyler Hobbs; CountUp.js; cartographers Joshua Stevens, Steven Bernard, John Nelson.

Every rule in the references cites its source by number. The full list, with links and what was taken from each, is in [`references/sources.md`](references/sources.md). Values marked as house defaults in a reference are our own starting points where no expert published a number.

## Related skills

- `remotion-maps` on varg how to: map building blocks for Remotion.
- [varg-video-edit-library](../varg-video-edit-library/): number and chart edits on footage.
- HyperFrames registry (`npx hyperframes catalog --query "…"`): about 450 ready-made blocks; the references name the ones to start from.
