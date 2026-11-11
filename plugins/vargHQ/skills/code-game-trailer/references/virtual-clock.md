# The virtual clock: exact frames from a game that thinks it runs in real time

A game written for play reads the time (`requestAnimationFrame(t)`, `performance.now()`, `clock.getDelta()`)
and moves things by the elapsed time. Recorded in real time, each captured frame covers whatever time the
screenshot took: measured on the example at 1080p, 84.5 ms on average and up to 150 ms per frame, so the
video plays 2.5x too fast and jumps. The fix is old and simple (it is how tools like timecut/timesnap
record pages): **replace the page's clocks before its scripts run**, then advance time by exactly
1/fps per frame and screenshot in between. The game is unchanged and cannot tell.

## What `scripts/virtual-clock.js` replaces

| API | behaviour under the clock |
|---|---|
| `requestAnimationFrame` / `cancelAnimationFrame` | callbacks wait in a queue; `__vc.step(ms)` runs each queued callback once with the new time |
| `performance.now()` | virtual milliseconds since page start |
| `Date.now()`, `new Date()`, `Date()` | a fixed epoch (2026-11-09 18:00 UTC) + virtual time; `new Date(x)` unchanged |
| `setTimeout`, `setInterval`, `clear*`, `requestIdleCallback` | fire in time order inside `step()` |
| CSS animations, transitions, `element.animate()` | paused and set from the virtual clock every step (HUD pops, title cards) |
| `Math.random` | seeded mulberry32 (`window.__VC_CONFIG.seed`): the same particles every run |

Not replaced (a game that depends on these is not frame-exact; fix the game or accept it):
`AudioContext.currentTime` (audio scheduling; visuals usually do not read it), `event.timeStamp`,
Web Workers and OffscreenCanvas in workers (the clock is not injected there), `<video>` playback,
`crypto.getRandomValues`, physics engines that run on their own `setInterval` in a worker.

## Load phases (why every shot starts identically)

1. **Real time, no virtual time passes.** `capture.ts` navigates and waits until `document.readyState ===
   'complete'` and the page has queued a frame (or the `ready` expression is already true). CDN modules
   download during this phase; zero-delay timers at virtual time 0 are flushed. However long the
   network takes, the game is still at t = 0.
2. **Virtual time.** Frames are stepped until the `ready` expression is true. The number of steps is the
   same every run, so the state at "ready" is too.
3. `setup` (your JS), `warmup` seconds stepped without screenshots, then the recorded frames.

If assets load asynchronously (textures, fonts, glTF) the game must set its ready flag only after they
arrived, or a slow network decides which frame they pop in.

## Checking it

- `capture.ts … --verify --only <shot>`: renders the first 45 frames of a shot twice from fresh loads as
  PNG and compares hashes. The example: 45/45 identical for a shot with scripted keys and for a slow-motion
  shot (GPU, same machine). Across different GPUs pixels can differ slightly; use `--gl swiftshader` when
  you need identical pixels on any machine (measured 509 ms per 1080p frame, about 10x slower).
- No screenshot lag: a test page coloured by frame index showed exactly the stepped frame in every
  screenshot (`Page.captureScreenshot` composites a fresh frame).
- `check.ts` counts duplicate frames per shot. A duplicate in gameplay means something moved on a clock
  the virtual clock does not control (or the game paused).

## Games that integrate state frame by frame

The clock steps frames strictly in order, one at a time, so `x += v * dt` games are fine: `dt` is exactly
1/fps (× `speed`), every run. Two traps:
- **`dt` clamps.** Many games clamp `dt` (e.g. to 0.05 s). Slow motion (`speed < 1`) only makes `dt`
  smaller, which is safe; fast-forward above the clamp changes the physics.
- **Per-frame constants** (`x += 0.1` per frame, no `dt`): deterministic, but tied to the capture fps.
  Capture at the fps the game was tuned for, or fix the game to use `dt`.

Parallel or out-of-order rendering (HyperFrames workers) needs a game that is a pure function of time
(see `threejs-animatic/references/seek-safe-rendering.md`); most agent-built games are not, which is
why this skill renders sequentially in one tab.

## Playwright instead of the built-in CDP client

The scripts use a 150-line CDP client so there is nothing to install. The same idea in Playwright with the
system Chrome (a sketch: the tested path in this skill is the CDP client):

```ts
import { chromium } from 'playwright-core';           // bun add -d playwright-core (no browser download)
const browser = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.addInitScript({ content: 'window.__VC_CONFIG={seed:7};' });
await page.addInitScript({ path: 'scripts/virtual-clock.js' });
await page.goto(url);
await page.keyboard.down('ArrowLeft');
await page.evaluate(() => (window as any).__vc.step(1000 / 30));
await page.screenshot({ path: 'f00000.jpg', type: 'jpeg', quality: 92 });
```

## Troubleshooting

| symptom | cause, fix |
|---|---|
| `page never queued a frame` | the page threw before starting its loop: the error is printed; a syntax error fails fast |
| `not ready after 600 frames` | the `ready` expression never became true; check the name, or the game waits for a click (`setup` can start it) |
| frames identical within a shot | the game's loop is not on `requestAnimationFrame` (a worker, `setInterval` in a worker, a video) |
| HUD numbers jump or animations finish instantly | a CSS animation created before the clock saw it: it is adopted at its current time; trigger HUD animations from game code |
| the process hangs after "manifest" | a timer still pending in the recorder (fixed here: clear timeouts, never race `Bun.sleep`) |
| first frame differs between runs | assets that load after "ready", or `Math.random` read in a worker |
