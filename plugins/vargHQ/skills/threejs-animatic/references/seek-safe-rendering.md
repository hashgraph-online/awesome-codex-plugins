# Seek-safe rendering: from browser to MP4

The animatic is reviewed live in a browser, but the MP4 must be rendered frame by frame: a screen recording drops
frames, drifts from the music and differs on every run. Both render paths below call the same function,
`film.pose(t)`, so they agree with each other and with the review UI.

## The contract (non-negotiable)

1. **What is on screen is a pure function of t.** `pose(t)` resets the set, runs the blocking for t, applies the
   shot camera. No `Date.now()`, `performance.now()`, `clock.getDelta()` or `requestAnimationFrame` deltas in the
   film code (the review UI may use the wall clock for playback only).
2. **No unseeded randomness.** `Math.random()` gives a different film every load. Use a seeded PRNG
   (`rng(seed)`, mulberry32) for scatter, and sines of time for noise and shake.
3. **No state carried between frames.** No `x += v * dt`, no "last yaw", no particles that integrate. HyperFrames
   renders frames in parallel workers (8 at once on a laptop), each seeking to arbitrary times, so a frame
   never sees its predecessor. Integrate speeds in closed form.
4. **Nothing loaded at seek time.** Models, textures and fonts load before the first render. CPU work after
   loading (big procedural meshes, shader compiles, a canvas texture that needs a web font) registers a promise on
   `window.__hf.buildReady["name"]` in HyperFrames, or holds the page's ready flag in the capture path.
5. **Fixed output size.** `renderer.setPixelRatio(1)`, `setSize(w, h, false)`, camera aspect = w / h,
   `preserveDrawingBuffer: true` so the canvas can be read after rendering.
6. **Cuts live in one place.** Shot start/end are the only cut times; every visibility window reads them. A
   literal written near a cut (`t > 3.9` against a cut at 4.0) pops the next shot's objects in for a frame or two.
7. **No text in references.** Labels are flagged and hidden in every export.

`bun tools/check.ts` tests 1–3: it renders the same moments in a different order and compares the pixels.

## Path A: capture over CDP (no npm)

The starter's `?export=1` view shows only the canvas at the export size and installs three hooks:

- `__seek(t[, shotId, localTime])` renders that moment;
- `__frame(...same)` renders it and returns the canvas as a PNG data URL;
- `__film` describes title, fps, duration, size and shots.

`tools/capture.ts` launches headless Chrome through a small Chrome DevTools Protocol client (`tools/cdp.ts`:
spawn Chrome with `--remote-debugging-port=0`, read the port from `DevToolsActivePort`, talk over Bun's built-in
WebSocket), calls `__frame(i / fps)` for every frame and pipes the PNGs into
`ffmpeg -f image2pipe -c:v png -i - … libx264 -pix_fmt yuv420p`. Frame i shows exactly t = i / fps, the same
sampling HyperFrames uses. The demo renders 240 frames at 854×480 in about 5 s on software WebGL.

Chrome flags that matter: `--headless=new --use-angle=swiftshader --enable-unsafe-swiftshader`. SwiftShader is
software WebGL: it works without a GPU (CI, servers, sandboxes) and gives the same pixels every run. A fresh
`--user-data-dir` per run is also required for remote debugging on recent Chrome.

For a one-off still without the tools, plain Chrome works if you give the page time to load three.js from the CDN
and draw: `chrome --headless=new --use-angle=swiftshader --enable-unsafe-swiftshader --virtual-time-budget=8000
--window-size=854,480 --screenshot=out.png "http://localhost:8777/?export=1"`. Without `--virtual-time-budget`
the screenshot fires before the first WebGL frame and comes out blank.

Modes of the capture tool:

| command | output |
|---|---|
| `bun tools/capture.ts` | the whole film, colour |
| `bun tools/capture.ts --shots s02,s03 --grey --out renders/run_A.mp4` | one video-to-video run: the shots back to back by local time, a tail to whole seconds (min 4 s), greyscale; plus `run_A.json` with each shot's in/out inside the clip and its place on the timeline |
| `bun tools/capture.ts --stills --size 1536x864` | START, middle and END PNG of every shot (for still boards and image edits) |
| `bun tools/capture.ts --look --stills` | the same stills with the optional look blockout on (`js/look.js`, see look-blockout.md), into `renders/look/`; never the v2v reference |

The tail keeps the blocking running past the last shot's end while the camera holds its END key. Check it: a 2 s
shot rendered alone gets a 2 s tail, and in the starter that tail shows a later action (an arm rising into the
frame). Group shots so the tail stays short, or plan the action of the tail.

## Path B: HyperFrames (HTML → MP4)

Use it when the animatic itself is a deliverable, needs HTML text over the 3D (titles, captions, callouts that
track a 3D point), audio mixed in, or the HyperFrames Studio for edits. `bun tools/make_hf.ts` writes `hf/`:

```html
<div id="root" data-composition-id="main" data-start="0" data-duration="10" data-width="854" data-height="480">
  <canvas id="gl" width="854" height="480" data-layout-allow-overflow></canvas>
</div>
<script> window.__timelines["main"] = gsap.timeline({ paused: true }); </script>
<script type="module">
  import { createFilm, createVideoRenderer } from './js/film.js';
  const film = createFilm(edits), renderer = createVideoRenderer(document.getElementById('gl'), 854, 480);
  function renderAt(t) { film.pose(t); renderer.render(film.set.scene, film.camera); }
  window.addEventListener('hf-seek', e => renderAt(e.detail.time));
  renderAt(window.__hfThreeTime || 0);
</script>
```

- `data-duration` on the root is required: the three adapter cannot infer a length from the scene, and the render
  fails with "zero duration" without it.
- The import map pins `three` (and `three/addons/` if you use addons) to the same version; a missing addons entry
  broke one build on the first try.
- `data-layout-allow-overflow` on a full-bleed canvas silences the layout check's "content touches the frame
  edge" warning, which is about text, not 3D.
- Text as HTML over the canvas stays sharp. To pin a label to a 3D object, project its world position every frame
  (`v.project(camera)` → pixels) and place the HTML element there; draw leader lines in an SVG on top.
- Validate: `npx hyperframes lint hf`, `npx hyperframes check hf`, then
  `npx hyperframes snapshot hf --at <times>` on the last frame before each cut, `(ceil(cut · fps) − 1) / fps`, and
  the first frame after it. Then `npx hyperframes render hf -o renders/animatic_hf.mp4`. The demo: lint 0/0,
  check passed, 10 s rendered in about 6 s. Render time grows with frame count and scene weight, not film length
  alone: keep heavy shaders and shadows out of a previz.

## Troubleshooting

| symptom | cause, fix |
|---|---|
| blank or black frames | captured before the first render (wait for the ready flag), or `preserveDrawingBuffer` is off and the canvas was read in a later task |
| a mesh renders as a flat black cutout | lit by one light from behind, no fill: add a `HemisphereLight` |
| frames differ between runs | `Math.random`, a clock, or state carried between frames; `tools/check.ts` finds it |
| an object pops in for one frame at a cut | a visibility window with its own literal instead of the cut constant |
| page "not ready" timeout | the CDN import failed (offline, firewall): vendor `three.module.js` and change the import map |
| the whole review page is hidden | a body state class equal to a component class (`body.guides` + `.guides {display:none}`): prefix state classes (`is-guides`) |
| keys do nothing right after load | the current shot is chosen in the first animation frame: select it synchronously at init |
| audio will not seek in the review | a static server without HTTP Range support: fetch the track into a blob URL |
| console error on raycast | sprites need `raycaster.camera` set |
| map shows only fog | the map camera is 30 m up: switch fog off while rendering the map |
