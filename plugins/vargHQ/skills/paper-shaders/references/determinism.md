# Determinism: one frame, one picture

A render engine asks for frame 0, then frame 1, often from several browser workers at once and sometimes out of order. A shader layer is safe only if the picture depends on nothing but the time it is asked for.

## The time model

Paper Shaders draws `u_time = frame / 1000`, where `frame` is milliseconds. With `speed` above 0 the mount advances `frame` from `requestAnimationFrame`, which is a wall clock. With `speed: 0`, `frame` alone sets the picture, and `ShaderMount.setFrame()` draws synchronously because no animation loop is running.

So the skill always mounts at speed 0 and computes

```
frame = motion.frame + seconds × 1000 × motion.timeScale
```

from the timeline. `seconds` counts from the start of the clip or sequence, `motion.timeScale` is the number Paper's editor calls `speed`, and `motion.frame` offsets where the motion starts. Nothing else may feed the picture: no `Date.now()`, `performance.now()`, unseeded `Math.random()` or `requestAnimationFrame` in scene code. Params that change over time go through `paramsAt(seconds)`, a pure function of time.

## HyperFrames

`paper-preset.js` returns a frame source for `window.__hyperframes.registerFrameSource`:

```html
<div id="bg" class="clip" data-composition-id="bg" data-start="0" data-duration="6"
     data-track-index="0" data-no-timeline data-layout-allow-overflow></div>

<script type="module">
  import * as PS from "https://cdn.jsdelivr.net/npm/@paper-design/shaders@0.0.82/dist/index.js";
  import { paperFrameSource } from "./paper-preset.js";
  import preset from "./presets/brand-mesh.json" with { type: "json" };
  window.__hyperframes.registerFrameSource(paperFrameSource(PS, document.getElementById("bg"), preset));
</script>
```

- **The host** is a timed clip: `class="clip"`, its own `data-composition-id`, `data-start`, `data-duration`, `data-track-index`. Add `data-no-timeline`; without it lint reports `missing_timeline_registry` and every render waits 45 s for a timeline that never comes. `data-layout-allow-overflow` tells `hyperframes check` that full-bleed art is intended.
- **Register early.** The runtime boots on `DOMContentLoaded`. A module script with static imports runs before that, so register at the top level. Do not `await` anything before the call; put slow work in `ready`.
- **`ready`** loads every image (noise textures included), preprocesses logos, creates the mount and waits for the canvas to get its real size. Capture does not start until it resolves.
- **`render(seconds)`** sets params from `paramsAt`, then calls `setFrame`. HyperFrames calls it in any order and from parallel workers.
- **One source per host.** Each scene that shows a shader needs its own host and source. Each host owns a WebGL context, and Chrome drops the oldest contexts once a page holds about 16, so keep a composition well under that (the preset reel uses 9).
- **Many looks, one context.** `paperSequenceSource(PS, host, presets, { each })` shows preset i during seconds [i × each, (i + 1) × each), disposing the previous mount and creating the next inside `render` (which then returns a promise HyperFrames waits for). Checked with out-of-order snapshots across preset boundaries in the 124-preset gallery: identical pixels.
- **Library loading.** The templates import the static ES module build from jsDelivr with an exact version; it loads before the first frame. For offline or hermetic renders, copy the package's `dist/` folder with its `LICENSE` and `NOTICE` into `vendor/paper-shaders@0.0.82/` in the project and import `./vendor/paper-shaders@0.0.82/dist/index.js`.

### What was measured

On an M1 Pro (HyperFrames 0.8.206, Chrome with ANGLE Metal, hardware GPU):

- Snapshots of the same instants taken forwards and backwards in separate browser runs had identical decoded pixels (`scripts/check-determinism.mjs`).
- Frames from `render --format png-sequence` with two parallel workers matched those snapshots pixel for pixel. The sequence is numbered from 1: `frame_000013.png` is frame 12.
- The 22.5 s 1080p preset reel, 9 shader hosts, rendered in about 22 s.

## Remotion

Use `templates/remotion/ShaderBackground.tsx`. It mounts once per preset under `delayRender`, then draws in `useLayoutEffect` on every render, which runs after React commits the frame and before the browser paints it. Render with `--gl=angle`, or the headless browser may have no WebGL context.

Do not drive Paper's React components (`<MeshGradient speed={0} frame={…}>`) for renders. Their first draw waits on asynchronous image loading and their frame updates run in `useEffect`, which nothing ties to Remotion's capture.

Measured with Remotion 4.0.539: frames 15, 45 and 75 from a parallel PNG-sequence render, covering a background, a LiquidMetal logo from `staticFile()` and a GodRays `paramsAt` ramp, were identical to stills rendered one at a time.

## Resolution and pixel ratio

- `minPixelRatio` defaults to 2: the canvas renders at twice the composition size and the browser scales it down, which anti-aliases edges. At 1080p that is a 3840×2160 canvas, exactly Paper's default `maxPixelCount` of 8,294,400 pixels. For 4K output pass a larger `maxPixelCount` (3840 × 2160 × 4) or accept 1×.
- Pixel looks (Dithering, ImageDithering, DotGrid) set `mount.minPixelRatio: 1` in the preset, so cells land on output pixels instead of being resampled.
- `u_pixelRatio` scales grain and dither sizes. Keep the same `minPixelRatio` for drafts and finals, or the texture changes size between them.

## Across machines

The same machine in the same GPU mode renders identical frames. A different GPU, or GPU against SwiftShader, can move pixels slightly. For identical renders across machines, use `npx hyperframes render --docker` (pinned Chromium, fonts and FFmpeg), or `--no-browser-gpu` (SwiftShader) everywhere. `node scripts/check-determinism.mjs <project> --software` checks the SwiftShader path.

Shader time is a `mediump` float. Desktop GPUs run it at 32 bits; keep `motion.frame` offsets under about 100,000 ms anyway, so a project that also previews on a phone keeps its precision.

## Symptoms

| Symptom | Cause | Fix |
|---|---|---|
| First frame black or tiny | Captured before images loaded or before the canvas was sized | Mount through `mountPreset` or `paperFrameSource`; give the host a real size |
| `image for uniform … must be fully loaded` | An unloaded image passed to `ShaderMount` | Pass URLs and let `presetToMount` load them |
| `SecurityError`, tainted canvas | Cross-origin logo or still without CORS headers | Serve images from the project |
| `preset "…" has no value for u_…` | The preset leaves a uniform unset | Add the param; run `validate-presets.mjs` |
| Frames differ between workers or runs | Scene code reads a clock or `Math.random`, or speed is not 0 | Drive everything from `seconds` |
| Render waits 45 s before starting | Host is missing `data-no-timeline` | Add it |
| A layer turns black mid-render | WebGL context lost: too many shader hosts in one page | Fewer hosts per composition |
| Remotion renders an empty canvas | No WebGL in headless Chrome | Render with `--gl=angle` |
