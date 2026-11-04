---
name: transition-craft
description: >-
  Six transitions with exact presets and the editing rules behind them: photo collage burst, Droste
  recursive zoom into a screen, impact tile-flip mosaic, bokeh light-spot transition, 3D photo cloud
  gallery and a camera-shake distort cut. Presets give the core length in frames, where the peak lands
  on the beat, log-space zooms, shake amplitude, frequency and decay, motion-blur shutter angle, bokeh
  sizes, tile counts and stagger, from Walter Murch, Dan Ebberts' decaying-sine expression, Boris FX,
  Maxon and Unreal camera-shake defaults, measured transition durations and editors on X. Use when a
  video needs a transition on the beat, an infinite zoom, a shake cut, a bokeh or photo-collage
  transition. NOT for plain crossfades and xfade wipes (varg-video-edit-library lists every ffmpeg
  xfade).
license: MIT
compatibility: >-
  HyperFrames 0.8 (npx hyperframes; brings Chrome, needs Node 22 and ffmpeg) or Remotion 4. Shake and
  zoom cuts also run as ffmpeg filter chains. No API key.
metadata:
  author: vargHQ
  version: "0.1.0"
  varg.cost.typical: "0 credits; renders locally"
  varg.runtime.typical: "minutes per template, mostly render time"
  varg.models: "none"
  varg.outputs: "mp4, webm or mov (alpha) from HyperFrames or Remotion"
  varg.presets: "6 templates, 29 presets"
---

# Transition craft: six transitions timed the way editors cut

Six transitions that hide the cut at the moment of peak coverage and land that peak on the beat. Zooms run in log space, shakes decay, and the settle carries the length rather than the effect.

## Gates

- **Beat first.** Get the beat grid (or the cut points) before timing anything; transitions peak on the downbeat or one frame before it.
- **Your own media.** Photos and clips in collages and galleries must be the person's own or licensed.
- **Seek-safe.** Every value is a function of timeline time; randomness is seeded by frame. No `Date.now()`, `requestAnimationFrame` or unseeded `Math.random()`.
- **No credits here.** These templates render locally for free. Generated footage, voice or music is the varg-ai skill: call `estimate_cost` and wait for the person's approval before any generation.

## Pick a template

6 templates, 29 presets. Each reference file has the same sections: how the pros do it (every rule cited), presets, timing and numbers, how to build it, mistakes that look amateur, sources. Each JSON file holds the same presets as machine-readable values.

| Template | Use it for | Presets | Files |
|---|---|---|---|
| **Bokeh light-spot transition** | The shot defocuses into giant highlight bokeh, cuts under the blur, and the next shot resolves into focus. | Warm night, Clean circle, Flash-through, Anamorphic oval, Vertical soft | [`bokeh-light-spot.md`](references/bokeh-light-spot.md) · [`json`](assets/presets/bokeh-light-spot.json) |
| **Droste recursive zoom** | Push into a screen that holds the same frame, levels deep, and land on the next shot. | Monitor push, Phone portal (vertical), Picture-frame loop, Escher twist, Pull-out reveal | [`droste-recursive-zoom.md`](references/droste-recursive-zoom.md) · [`json`](assets/presets/droste-recursive-zoom.json) |
| **3D photo cloud gallery** | Photos hang in a deep 3D cloud, fading into same-colour fog as the camera swings through and lands on a hero photo. | White fog swing, Dark void, Vertical column, Slow drift loop | [`photo-cloud-gallery.md`](references/photo-cloud-gallery.md) · [`json`](assets/presets/photo-cloud-gallery.json) |
| **Photo collage burst** | Photos, shapes or words thrown in from the edges pile into a churning collage that covers a hidden cut to the next shot. | Photos, Shapes, Words, Mixed, Polaroid drop (3D) | [`photo-collage-burst.md`](references/photo-collage-burst.md) · [`json`](assets/presets/photo-collage-burst.json) |
| **Camera-shake distort cut** | An impact cut: the shot hops, punches in and bends into the cut; the next shot lands punched-in, mirror-filled, shakes and settles. | Bass hit, Handheld snap, Earthquake, Vertical reel, Staccato | [`shake-distort-cut.md`](references/shake-distort-cut.md) · [`json`](assets/presets/shake-distort-cut.json) |
| **Impact tile-flip mosaic** | On a hit, the shot breaks into lit tiles that flip in a feathered, randomised wave to reveal the next shot. | Impact centre, Diagonal sweep, Random scatter, Fine mosaic (split-flap), Bold blocks | [`tile-flip-mosaic.md`](references/tile-flip-mosaic.md) · [`json`](assets/presets/tile-flip-mosaic.json) |

## Workflow

1. **Match the request** to a template and one or two presets from the table. Say which and why in one line, and show the person the preset names with their one-line looks before building anything.
2. **Read the reference** for that template, and load its JSON. Take values from the JSON; do not re-guess them.
3. **Build it** the way the reference's "Build it" section says, starting from the named HyperFrames blocks or varg components where it names them. Drive every value from timeline time so any frame renders the same on a re-render.
4. **Fit it to the brand:** swap in the person's colors and fonts only where the reference allows, then re-check contrast and safe zones with the numbers in "Timing and numbers".
5. **Check a draft:** render stills at the key moments (entrance, hold, exit), go through "Mistakes that look amateur", and fix before the final render.


## Rules that hold for every template

1. Hide the hard cut at peak coverage (max blur, full pile, mid-flip, peak velocity); never cut on a readable frame.
2. Peak on the downbeat (or 1 frame early to jolt); 6–12 frames late reads relaxed.
3. Short core: impact 0.10–0.25 s, whip/zoom 0.15–0.30 s, fast blur 0.20–0.40 s; let the settle carry length; halve anything that feels slow.
4. Every zoom/dolly in log space: scale = k^e, tween e.
5. Arrive fast then slow (expo.out / cubic-bezier(.25,0,.11,1)); new shots cut in at 1.2–1.5x and settle to 1x over 0.5–1.2 s.
6. Shakes = A·sin(2πft)/e^(decay·t); impacts 8–14 Hz, decay 4–8; handheld 1–3 Hz; mirror edges, never black.
7. Motion blur 180°, 5–10 samples.
8. Eye-trace across the cut; emotion beats 3D continuity (Murch 51/23/10/7/5/4).
9. Seed every random; drive from timeline time.
10. 2-frame chromatic kick on hard impact cuts; if it reads as a filter, halve every value.

## Built from

Walter Murch; Dan Ebberts; Boris FX / Maxon Universe / Unreal docs; Zaid Alkuheli (OverseerOS); van Wijk & Nuij; Tony Zhou; David DeSandro / GSAP; X: @RajAdonis, @Pashoke1, @goopsoup_.

Every rule in the references cites its source by number. The full list, with links and what was taken from each, is in [`references/sources.md`](references/sources.md). Values marked as house defaults in a reference are our own starting points where no expert published a number.

## Related skills

- [varg-video-edit-library](../varg-video-edit-library/): 206 named edits for existing footage (cuts, transitions, headlines, UI, numbers).
- [motion-formats](../motion-formats/): full formats built from these moves.
- HyperFrames registry (`npx hyperframes catalog --query "…"`): about 450 ready-made blocks; the references name the ones to start from.
