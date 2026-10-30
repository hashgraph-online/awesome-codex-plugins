# Droste recursive zoom

The camera pushes into a screen (monitor, phone, picture frame, TV) that shows the same frame, which holds the same
screen again, levels deep; after a few levels the innermost screen becomes the next shot and the push lands on it.
Use it for "a video inside the video" reveals, app/website launches, recursion jokes and chapter openers. Works in
16:9, 9:16 and 1:1; 3–5 s (4 s default). A reverse pull-out works as an outro.

## How the pros do it
- Zoom in log space. A zoom by a constant factor costs the eye the same anywhere, so the even-looking zoom is
  exponential: scale(t) = k^(t / T), not a linear scale ramp. [16]
- Drive every level from one parent/camera transform and use exponential scale on it — that is the accepted fix when an
  infinite zoom looks uneven between levels. [17][18]
- Pick the nesting ratio k from the screen: if the screen occupies 1/4 of the frame width, each level is 4× smaller,
  so k = 4 and one full level of push = scale × 4. The loop is seamless when the push per cycle equals k exactly. [17][18]
- Only render as deep as you can see: levels = ceil(log(frame width in px / 2) / log k); at 1920 px and k = 4 that is
  7, at k = 2.5 it is 8. Deeper levels are sub-pixel noise. (Derived from [16].)
- Push 2–4 levels in a 4 s transition — about 0.6–1.0 s per level; faster than 0.4 s per level reads as a flash, not a
  recursion.
- Ease the exponent, not the scale: ease-in on the first 20–30 % of the exponent, constant rate in the middle, then a
  decelerating catch on the last level (things move at full speed and only slow down at the end). [16][42]
- The twisted Escher version is a conformal map: take log of the coordinates, multiply by c = i2π / (ln α + i2π),
  take exp; Lenstra's reading of Print Gallery gives α = 256. Advance the zoom by adding to the log-radius. [19][20][45]
- Satoshi Kon used "zoom out from a TV" as a scene transition — the same move run backwards, so the pull-out variant has
  a strong editorial precedent. [4]
- Land on the screen centre where the eye already is; eye-trace across the landing matters more than the 3D space of the
  rooms you passed through (Murch ranks 3D space last). [1][2]
- Generate the outer plate with an image model: "Droste effect" works as a shorthand prompt for recursive images; then
  key the screen area and rebuild the recursion in code so it is exact. [49]
- Use radial motion blur only at peak speed (180° shutter equivalent, 5–10 samples). [7][15]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `droste-recursive-zoom.monitor-push` | Desk monitor shows the frame; push 3 levels, land on next shot | k = 4, render 7 levels, push 3 levels in 4.0 s, exponent ease: power2.in 0–0.9 s, linear, expo.out last 0.8 s, radial blur peak 10 px |
| `droste-recursive-zoom.phone-portal` | Vertical: hand-held phone screen recursion | 9:16, screen width 40 % → k = 2.5, 8 levels, push 4 levels in 3.6 s, cubic-bezier(.25,0,.11,1) on the last level |
| `droste-recursive-zoom.picture-frame-loop` | Gallery frame on a wall, endless loop for backgrounds | k = 3, constant exponent rate 1 level / 1.2 s, loop length = 1 level exactly, no blur |
| `droste-recursive-zoom.escher-twist` | Spiral Droste: the frame curls into itself while zooming | log-polar shader, α = k² per turn (Print Gallery: 256), twist 1 turn per 2 levels, 4.0 s |
| `droste-recursive-zoom.pull-out` | Reverse: start inside the screen, pull out through 3 levels to reveal the room | same k, exponent eased power3.out from start, 3.0 s |

## Timing and numbers
- 4.0 s at 30 fps = 120 f. monitor-push: hold 0–0.3 s · ease-in 0.3–0.9 s · cruise 0.9–3.2 s · catch 3.2–4.0 s.
- Exponent e(t) goes 0 → 3 (levels); scale = k^e. At k = 4 the total zoom is 64×.
- Seam: feather the screen-edge mask 1–2 px at 1080p; add a 2–4 % dark bezel or glass reflection so seams read as hardware.
- Screen glare overlay at 6–10 % opacity, screen-blended, constant per level so it repeats identically.
- Radial blur: 0 px below 0.5 levels/s, up to 8–12 px at peak (≥ 2 levels/s); never on the landing frame.
- The cut to the next shot happens at the level whose screen equals the frame (scale = k^n exactly); land it on a downbeat.

## Build it
- HyperFrames: `zoom-through-transition` (zoom through a focal card into the next scene) and `cinematic-zoom` are the
  closest blocks; `parallax-zoom` for a layered room. Build the recursion yourself:
1. Make one "plate" element: the outer shot with a transparent screen rectangle (position x, y, w, h).
2. Nest N copies: copy i is scaled by 1/k^i and translated so it sits in the screen rect of copy i−1 (compute in px once).
3. Animate a single wrapper: `scale = Math.pow(k, e)`, with the transform-origin at the screen centre (the fixed point of
   the similarity transform). Tween `e` on the GSAP timeline, never the scale directly.
4. When e passes an integer, you can drop the outermost copy and add one inside (or wrap e modulo 1 for loops).
5. Replace the innermost plate with the next shot's video for the landing.
- Escher twist: a fragment shader (Paper/Three/raw WebGL) — `z = log(uv - centre)`; `z *= c`; `z.x += timeLog`;
  `uv = exp(z)`; sample the plate with `mod(log|uv|, log α)` for repetition. Drive `timeLog` from timeline time.
- Remotion: compute `e = interpolate(frame, ...)` with `Easing.bezier`, `scale = Math.pow(k, e)`; for shaders use
  `@remotion/three` with `useCurrentFrame` (no `useFrame`). [32]
- Footage-only fallback: ffmpeg `xfade=transition=zoomin:duration=0.6` is a single-level zoom, not a recursion.

## Mistakes that look amateur
- Linear scale keyframes → the zoom races at the start and crawls at the end of each level; tween the exponent.
- Each level animated separately → drift and visible seams; one parent transform. [17]
- Transform-origin at frame centre when the screen is off-centre → the recursion slides sideways; origin = screen centre.
- Rendering 12+ levels → sub-pixel shimmer and slow renders; stop at the visible depth.
- Blur on the landing frame → the payoff is soft; blur only at peak speed.
- A different crop on each level (re-generated images) → it stops being the same frame; use one plate, copied.
- Screen content with its own UI chrome scaling separately → bake chrome into the plate.

## Sources
[1] Filmdaft — Murch's Rule of Six — https://filmdaft.com/walter-murchs-rule-of-six-the-editors-formula-for-choosing-the-right-cut/ — eye-trace over 3D space
[2] No Film School — Murch's 6 rules — https://nofilmschool.com/2016/11/6-rules-good-cutting-according-oscar-winning-editor-walter-murch — sacrifice 3D space first
[4] Tony Zhou — Satoshi Kon: Editing Space & Time (transcript) — https://voicetube.com/videos/32481 — "zoom out from a TV"
[7] StudioBinder — 180° shutter — https://www.studiobinder.com/blog/what-is-the-180-degree-shutter-rule/
[15] Remotion — CameraMotionBlur — https://www.remotion.dev/docs/motion-blur/camera-motion-blur
[16] Reach & North (restating van Wijk & Nuij) — https://ar5iv.labs.arxiv.org/html/1801.09358 — constant-factor zoom = constant perceived cost; exponential zoom
[17] Adobe Community — Infinite zoom loop (Roland Kahlenberg) — https://community.adobe.com/t5/after-effects-discussions/infinite-zoom-loop-effect/td-p/9884846 — one parent, exponential scale
[18] Noah Litvin, Envato Tuts+ — Droste zoom — https://photography.tutsplus.com/tutorials/endlessly-zoom-into-your-own-droste-effect--ae-12897 — precomp + scale method
[19] Jie Chen — Escher's Print Gallery and the conformal mapping — https://jiechenjiechen.github.io/blog/2026/escher — log/multiply/exp, α = 256
[20] Universiteit Leiden — Escher and the Droste effect — https://pub.math.leidenuniv.nl/~smitbde/escherdroste/
[32] Remotion — @remotion/three — https://www.remotion.dev/docs/three
[42] Raptor (@RajAdonis) — https://x.com/RajAdonis/status/2113906813020344579 — full speed, then slow
[43] Lionel Radisson (@MAKIO135) — https://x.com/MAKIO135/status/1742550379911401900 — loop reference
[44] Nicolas Daniel (@nicolasdnl) — https://x.com/nicolasdnl/status/1743599237886099583 — screensaver loop reference
[45] Massimo (@Rainmaker1973) — https://x.com/Rainmaker1973/status/1639251479461502977 — Leiden twist animation
[49] fofr (@fofrAI) — https://x.com/fofrAI/status/1993709106075767222 — "Droste effect" prompt shorthand
