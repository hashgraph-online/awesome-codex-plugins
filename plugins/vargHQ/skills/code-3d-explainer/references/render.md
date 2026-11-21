# Rendering: determinism, the two paths, measured speed

## The contract

`window.__film = { ready, fps, duration, width, height, render(t), labels() }` and an `hf-seek` listener,
both calling the same `render(t)`:

1. What is on screen is a pure function of t: camera from keys, every part from t, labels from t. No
   `Date.now()`, no `requestAnimationFrame` deltas, no state carried between frames. Even "keep a label
   while its anchor was visible in the last 0.25 s" is computed from the camera pose at t − 0.25.
2. Seeded randomness only (`rng(seed)` mulberry32; `hash(i)` per instance).
3. Everything heavy happens before `ready` resolves: geometry, fonts (`document.fonts.load` for each face
   in `story.fonts`), label measurement. HyperFrames waits on `window.__hf.buildReady[...]`, registered
   synchronously in the same module.
4. Fixed size: `setPixelRatio(1)`, `setSize(1920, 1080)`, `preserveDrawingBuffer: true`.
5. Text is HTML, so a frame is a screenshot of the page, not a canvas readback.

Proof: `bun scripts/capture.ts <project> --check 10` renders 10 times forward in one tab and in reverse in
another and compares pixels. The cell: PASS, byte-identical.

## Path A: scripts/capture.ts (no npm)

Spawns system Chrome headless with a fresh profile, talks DevTools protocol over Bun's WebSocket, opens N
tabs, renders frame i = t i/fps in whichever tab is free, screenshots it (`Page.captureScreenshot`), and
pipes frames in order into `ffmpeg -f image2pipe … libx264 -pix_fmt yuv420p -movflags +faststart`.

```bash
bun scripts/capture.ts examples/animal-cell --out master.mp4 --labels qa/labels.json --crf 18
bun scripts/capture.ts examples/animal-cell --stills 2.6,8.4,20.5 --still-dir qa/stills
bun scripts/capture.ts examples/animal-cell --from 12 --to 15 --format jpeg --out /tmp/draft.mp4
bun scripts/capture.ts examples/animal-cell --eval "__film.anchors()"
bun scripts/capture.ts examples/animal-cell --check 10
```

Measured 2026-11-10, Apple M4 Pro (14 cores), Chrome 157 headless, three r185, 1920×1080, the cell scene
(~2,800 instanced ribosomes, DOF + bloom):

| setting | speed |
|---|---|
| full film, 630 frames, PNG, 4 tabs, GPU (Metal) | 51–54 s = **11.7 frames/s**, 55–65 s with load (9.0 frames/s when the machine was busy) |
| heaviest 3 s (cutaway), PNG, 1 / 2 / 4 / 8 tabs | 5.7 / 8.2 / 9.1 / 10.3 frames/s |
| same, JPEG q95, 4 tabs | 27.6–34.3 frames/s (SSIM 0.98 vs PNG on this grainy dark film): use for drafts |
| same, SwiftShader (software GL, no GPU), 4 tabs | 0.9 frames/s (1.1 s per frame) |
| page load, three from jsDelivr / vendored | 2–13 s / 0.4–0.9 s |

PNG encoding inside Chrome is the bottleneck, not WebGL: JPEG is 3× faster. Headless Chrome on macOS uses
the Metal GPU by default (no flags); on Linux without a GPU it falls back to SwiftShader, which is ~10×
slower but byte-stable.

## Path B: HyperFrames (bunx hyperframes@0.9.15)

The example's `index.html` is also a valid HyperFrames composition: root
`<div data-composition-id="main" data-no-timeline data-duration="21" data-width="1920" data-height="1080">`,
a full-bleed canvas with `data-layout-allow-overflow`, local `@font-face` files, the `hf-seek` listener and
`__hf.buildReady`.

```bash
bunx hyperframes@0.9.15 lint examples/animal-cell      # 0 errors (1 false warning on the label scrim)
bunx hyperframes@0.9.15 render examples/animal-cell -o master_hf.mp4
```

Measured: 630 frames in **22.5 s** (8 workers, hardware GPU, screenshot capture), SSIM 0.983 against the
capture.ts master; frames look identical. Use it when you want audio mixing, Studio edits or speed; use
capture.ts when you need `--labels` (the QA boxes), `--check`, stills or no Node toolchain.

Lint findings we fixed: `missing_timeline_registry` / `missing_data_no_timeline` (a three-only
composition needs `data-no-timeline`, or every render waits 45 s for a GSAP timeline), named fonts need
local `@font-face` files (we ship Inter and JetBrains Mono, OFL).

## Troubleshooting

| symptom | cause, fix |
|---|---|
| render hangs, or "page has no window.__film" | a CDN import never arrived (we lost a run to a DNS outage). capture.ts now times out each DevTools call (`--timeout`, 90 s). Run `bash scripts/vendor_three.sh <project>` to serve three.js from the project |
| a part renders as one flat colour | its faces are back faces (lathe profile top→bottom, or inverted winding): `solid()` draws back faces as the flat cut cap |
| a red/orange line across a sphere at rest | the reveal range does not cover the object (`range` must span the object's size, in object units) |
| the interior is all blurred or all sharp | a transparent shell wrote the DOF depth: set `userData.noDepth = true` on shells |
| a white blob on a sphere | specular + bloom: lower the specular, raise the bloom threshold |
| something huge and blurry fills half a frame | a scattered part sits on the camera path: reject parts near the sampled path |
| a label jumps on the end card | column layout computed from visible labels only: lay out the whole column |
| ImageMagick cannot draw text (no FreeType/Ghostscript), ffmpeg has no drawtext | `scripts/sheet.ts` draws timestamps as seven-segment rectangles; all film text is HTML |
