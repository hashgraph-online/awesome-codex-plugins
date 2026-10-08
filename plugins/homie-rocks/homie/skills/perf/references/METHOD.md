# The method behind the loop

How a game gets faster without anybody fooling themselves, and the ways a measurement lies.

## What one run is

Two headless Chromes on this computer's GPU (`--use-angle=metal` on a Mac), each a separate process with its own
throwaway profile, open the game's play page with `?room=perf-…`: a fresh room nobody else is in, so every run starts
the same way (round 1, the same bots). The first is the host, the second a replica. Both are the same device:

| device | what it is |
| --- | --- |
| computer | 1280x800 at 2x, this computer's CPU and GPU |
| phone | 390x844 at 3x, touch, a phone's user agent, Chrome's CPU throttle at 4x (`--cpu`), 4G (9 Mbit/s down, 1.5 up, 85 ms) |

Chrome's throttle suspends the page's thread in slices, so on a fast computer it stretches work less than its rate:
on an Apple M4, "4x" measured between 2.4x and 3.8x from run to run (that spread is part of the phone's noise). Every
phone run times the same loop of arithmetic before and after the throttle and records the real slow-down
(`cpuMeasured`); BASELINE.md and the report say it. For a slower phone, raise `--cpu`.

Both play the same seeded presses (hold a direction most of a second, now and then the action) through a 3 s warm-up
and the measured window. Before the window a garbage collection runs, so the heap's growth over the window is the
game's own. A profiled run profiles in a second window, never the measured one: a profiler slows what it watches.

What is read, per browser:

- **frames**: the time between animation frames in the game's frame (every `requestAnimationFrame` callback is
  wrapped before the game's first script runs). At 60 Hz the floor is 16.7 ms; p95 is what stutter feels like; frames
  over 50 ms are hitches anyone sees.
- **work**: milliseconds of the game's JavaScript inside those callbacks. A page's clock is coarsened to 0.1 ms (with
  jitter), so use `work.mean` over a window, not a single frame.
- **busy**: Chrome's own count of the page's main-thread time (scripts, style, layout, socket messages, the play page
  around the game) per frame. The best single number for CPU per frame.
- **load**: from opening the page to the game's first animation frame, to a seat, to playable (seated, with the body
  the game's port probe reports); the game's files on the wire, the biggest first.
- **heap**: the JavaScript heap after a garbage collection at the end; its growth per minute.
- **net**: netplay messages and kilobytes a second on the room's socket, each way, and the helper's own counters
  (snapshot rate and size, inputs a second, interpolation delay).

## Why in turns, and why so many runs

On a shared computer the same build measures differently from run to run: another app wakes up, a garbage collection
lands in the window, the scheduler puts the page on a slower core, the bots wander somewhere busier. Measured on an
Apple M4 while other work ran: the main thread per frame moved about 20% (the middle half of five runs), the time to
playable about 1.5%, the heap about 1%. So:

- a difference between two single runs means nothing;
- the build to beat is measured again beside every change, in turns (before, after, after, before), so drift hits both;
- each before-run and the after-run beside it are a pair; the test is on the pairs' ratios (Wilcoxon signed-rank,
  exact), so a drift that hits both sides of a pair cancels. In the same drift above, a change 8% faster measured
  through it is invisible to a test of every run against every run, and plain in six pairs out of six;
- a change counts only when the test says it is unlikely to be chance (p < 0.05: with 6 pairs, at least 5 wins and
  only the closest pair lost), the bootstrap interval of the change stays below zero, and it is at least 3% better.
  A change the size of the noise will not pass; that is the point. A small real gain needs more runs
  (`baseline --runs 10`), not a luckier draw;
- guards are stricter (worse in every pair or p < 0.01, and at least 5%), because checking a dozen guards at 0.05
  would flag a regression by chance on most changes.

Sizes on disk never vary: any change of at least 1% counts.

## Picking the goal from the baseline

- Frames already at the display's rate: frame time cannot improve on this profile. Aim at `busy`, or slow the phone
  further (`--cpu 6` or `8`) until the frames show the cost, then aim at `frame.p95`.
- A median frame over 18 ms: the steady cost is the problem; start with the hottest game function.
- Frames over 50 ms but a fine median: something runs now and then (a spawn, a big message, a texture upload, a
  garbage collection). Look at `gcPct` and long tasks.
- "(program)" large in the profile: Chrome's own drawing and compositing. Fewer draw calls and state changes, smaller
  canvases and fewer full-screen fills help; JavaScript changes will not.
- The host's `busy` well above the replica's: the rules, bots and snapshots cost; the replica only draws.

## Changes that usually help, and their traps

| change | trap |
| --- | --- |
| make once what is made every frame (gradients, paths, arrays, strings, measured text) | a cache keyed on the wrong thing (screen size, device pixel ratio) draws stale |
| batch: one path for many shapes, instanced meshes, fewer material or composite switches | draw order changes what overlaps: look at the screenshots |
| stop allocating in the loop (reuse vectors and arrays) | shared scratch objects returned to callers get overwritten |
| skip work for what is off screen or far away | a body that pops in, a sound that stops |
| minified builds of the same library version | a different version is a different game; minify only a file `perf sizes` reads as not minified, keep its name and licence |
| load big things after the first frame | a game that is "playable" but blank for a second has moved the wait, not removed it |
| send less netplay: only what changed, coarser numbers | the replica's interpolation and the host's checks read those numbers |

Trades, never optimisations (say them, and only with the person's yes): a lower resolution or pixel ratio, fewer bots,
particles or physics steps, shorter view distance, softer or smaller shadows, a lower snapshot rate.

## How a measurement lies

- **A software renderer fakes a stuck game.** SwiftShader draws WebGL at a few frames a second; those runs are BLOCKED.
- **An emulated phone is not a phone.** It has this computer's GPU: a shader-heavy game that holds 60 fps here can
  crawl on a real phone. It ranks changes; say "emulated" with every phone number.
- **A capped frame rate hides cost.** At 60 Hz a frame that takes 2 ms and one that takes 12 ms both read 16.7 ms.
- **The wrong build.** The loop swaps builds under a running dev server; it checks every served file's SHA-256 before
  each run, and the game page against the build's: every script of the build's page, byte for byte and in order, and
  the markup between them. Scripts the site adds (HOMIE_NET, a shim a studio's own Worker injects) are set aside, listed
  in BASELINE.md, and must be the same before every run: a stale page (another bundle's name), a changed inline script
  or a Worker changed mid-loop stops the run. Never build by hand while it runs.
- **Compression is not minification.** Minified JavaScript gzips to a quarter or a third of its bytes (three.js's own
  minified builds: 24-26%), more than indented source does (20%), and a bundle with three.js in it carries its shaders as
  GLSL source in strings, line by line, which no minifier touches (thousands of lines in a minified bundle). `perf sizes`
  reads each big script's code instead: whitespace (about 1-2% minified, 15-30% indented), comments, and names outside its
  strings, with the share that is GLSL shader source said apart.
- **A busy computer.** Every run records the 1-minute load before and after and how busy all cores were in its window.
  A run that started over the bar (0.8 per core) is taken again and left out.
- **A profile is not a measurement.** It names where time goes; only the alternating runs say whether a change helped.
- **The first frame is not playable.** `load.playable` waits for a seat and a body; a game that draws early and
  connects late has moved the wait.
- **Control-ready is not the game's own "ready".** `load.playable` is what the probe can see (a seat, a body, the
  loading cover gone). `load.ready` is when the game itself called `net.playable()`. Each run records the arrival
  mode (`load.arrival.mode`: `auto`, `game`, or `seat` for an older helper) and, under `auto`, how long after the
  cover lifted the game's word came (`lateMs`). A run whose browser ended its window cut off from the room (the
  helper's link: `reconnecting`, `alone`, `offline`, `closed`) is BLOCKED and left out: it was not two browsers
  playing together.
