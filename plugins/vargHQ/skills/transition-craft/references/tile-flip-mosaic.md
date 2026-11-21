# Impact tile-flip mosaic

On a hit, the shot breaks into a grid of tiles that catch light as they flip, one wave at a time, to show the next shot
on their backs; the wave front is feathered and slightly randomised. Use it on a drop, a reveal, a before/after or a
brand sting. Works in 16:9, 9:16 and 1:1; 5 s with holds (default), of which the flip wave is 0.8–1.4 s.

## How the pros do it
- Each tile is a two-faced card: front = shot A, back = shot B pre-rotated 180°, `transform-style: preserve-3d`,
  `backface-visibility: hidden`, flip with rotateY(180deg). [23]
- Put `perspective` on the grid parent, not `perspective()` on each tile, so all tiles share one vanishing point and the
  wall reads as one surface. 100 px is extreme, 2000 px subtle; DeSandro's card uses 600 px. [24][23]
- Order the wave with a grid stagger: `stagger: { grid: [rows, cols], from: [x, y], amount, ease }` — `from` is the impact
  point in 0–1 coordinates, `amount` the whole wave length, and an ease on the distribution shapes the front. [21]
- Feather the front: add ±15–25 % seeded random jitter to each tile's delay on top of the distance stagger; pure
  `from: "random"` loses the impact origin, pure distance looks mechanical.
- Grid transitions are now one-click plugin effects all over editor feeds, so defaults read as a preset — vary jitter,
  tile size and light to look made. [47][48]
- Start the wave with the impact: a 2-frame chromatic kick on the hit frame, then the flip. [41]
- The impact itself is short: flash/punch/impact moments sit in the 0.10–0.25 s band. [8]
- Use the grid as Kon's "object wiping the frame": the wave front is the wipe edge, so the eye follows it to where
  shot B's subject appears. [4][1]
- Settle the flip with a tiny overshoot (decaying oscillation, 1–3° past 180°) rather than a dead stop. [10]
- If it looks like a filter, halve the light, jitter and shake values. [41]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `tile-flip-mosaic.impact-center` | Hit in the centre, lit tiles flip outward | 16:9 grid 12×7, from [0.5,0.5], amount 0.8 s ease power2.inOut, jitter ±20 %, tile flip 0.42 s power3.inOut, perspective 1400 px, edge light peak 1.8× brightness, 2-frame RGB kick 8 px |
| `tile-flip-mosaic.diagonal-sweep` | Clean diagonal wave from the top-left | 16×9 grid, from [0,0], amount 1.0 s ease none, jitter ±10 %, flip 0.36 s, perspective 1800 px |
| `tile-flip-mosaic.random-scatter` | Scattered, glittery flip, no single origin | 10×6, from "random", amount 1.1 s, flip 0.3 s power2.inOut, light peak 1.5× |
| `tile-flip-mosaic.fine-mosaic` | Small tiles flip on the X axis like a split-flap board | 24×14 (16:9) / 14×24 (9:16), rotateX, from [0.5,1] (bottom), amount 1.2 s, flip 0.28 s, perspective 2000 px |
| `tile-flip-mosaic.bold-blocks` | Few big tiles, heavy and dramatic | 6×4, from impact point, amount 0.6 s, flip 0.55 s back.out(1.2), perspective 700 px, shadow under tiles 40 % |

## Timing and numbers
- 5.0 s at 30 fps = 150 f: hold A 0–1.6 s · impact frame f48 (on the downbeat) with 2-frame RGB kick · wave f48–f84
  (0.8 s amount + 0.42 s tile = wave ends ≈ 1.2 s after impact) · hold B to 5.0 s.
- Grids in this file are written columns × rows; the JSON uses GSAP's `[rows, cols]` order.
- Grid size by format at 1080p: 16:9 12×7 (~160 px tiles) · 9:16 7×12 · 1:1 9×9 (120 px). Keep tiles square ±10 %.
- Gap between tiles during the flip: 2–4 px dark gutter (#000 at 60 %) appears only while tiles are rotating (rotation
  between 10° and 170°).
- Edge light: brightness follows 1 + (peak − 1) · sin(θ) where θ is the flip angle (peak at 90° when the tile is
  edge-on), plus a specular gradient sweeping 0 → 100 % across the tile during the flip.
- Overshoot: rotate to 183° then settle to 180° over 0.15 s.
- Z lift during the flip: translateZ 0 → 30–60 px → 0 so tiles do not clip each other.

## Build it
- HyperFrames: `transitions-grid` (showcase of grid tile transitions), `grid-pixelate-wipe` (staggered square
  dissolve) and `wordmark-tiles` are the starting blocks; `chromatic-aberration-wipe` for the hit frame. `npx
  hyperframes add transitions-grid chromatic-aberration-wipe`.
1. Build the grid as `rows × cols` divs; each holds two faces whose `background` is the same full-frame image/video
   frame positioned with `background-position: -x -y` and `background-size: frameW frameH` (for video, use a canvas
   that draws the current frame once per frame, or a clip-path on two full-frame video layers per tile row).
2. Compute delay per tile: `d = dist(tile, origin) / maxDist * amount + jitter(seed, i) * amount * 0.2`.
3. One paused timeline: `tl.to(tile, { rotationY: 183, z: 40, duration: 0.3, ease: "power3.in" }, impact + d)
   .to(tile, { rotationY: 180, z: 0, duration: 0.12, ease: "power2.out" })`; a brightness tween keyed to the same times.
4. On the hit frame add the RGB split (2 frames) and a 6–8 frame shake (see `shake-distort-cut`).
- Remotion: compute each tile's progress with `interpolate(frame - delayFrames, [0, 13], [0, 180])` and render faces with
  `<OffthreadVideo>` clipped by `clipPath: inset(...)`.
- ffmpeg fallback: `xfade=transition=pixelize:duration=0.8` (flat, no flip) or `xfade=transition=hlslice`.

## Mistakes that look amateur
- Every tile on its own `perspective()` → each tile has its own vanishing point; the wall shatters.
- Pure random order → no sense of impact; keep a distance stagger with jitter.
- Tiles flipping with no light change → looks like a slideshow; tie brightness to the flip angle.
- Uneven tile sizes from rounding (last column thinner) → compute tile size from the frame and allow 1 px overlap.
- Gutters visible before the hit → only open gutters while rotating.
- Wave too slow (> 1.5 s) → the impact is gone; the whole wave under 1.4 s.
- Flip on the wrong axis for the format → vertical frames read better with rotateX waves bottom-to-top.

## Sources
[1] Filmdaft — Murch's Rule of Six — https://filmdaft.com/walter-murchs-rule-of-six-the-editors-formula-for-choosing-the-right-cut/ — eye-trace
[4] Tony Zhou — Satoshi Kon: Editing Space & Time (transcript) — https://voicetube.com/videos/32481 — objects wiping the frame
[8] Zaid Alkuheli, OverseerOS — transition durations — https://www.overseeros.com/blog/how-long-should-video-transitions-be — impact band 0.10–0.25 s
[10] Dan Ebberts — bounce and overshoot — http://www.motionscript.com/articles/bounce-and-overshoot.html — decaying settle
[21] GSAP — Staggers — https://gsap.com/docs/v3/Staggers/ — grid, from, amount, ease
[23] David DeSandro — Card Flip — https://3dtransforms.desandro.com/card-flip — preserve-3d, backface, 600 px
[24] David DeSandro — Perspective — https://3dtransforms.desandro.com/perspective — shared vanishing point, 100 vs 2000 px
[41] Yaori (@Pashoke1) — https://x.com/Pashoke1/status/2115041115590037582 — 2-frame chromatic kick; halve values if it looks like a filter
[47] Siraj (@SirajEdits) — https://x.com/SirajEdits/status/2115785675949650408 — grid transitions as one-click effects
[48] aescripts / kewin.wav — https://x.com/aescripts/status/2115832815606546677 — grid animation trend
