---
name: perf
description: Make a studio's game run faster with a measured loop, and keep only what really helped. Measure a baseline on a computer and an emulated phone in real Chrome on the GPU (frame times p50/p95/long frames, the game's JavaScript and the main thread per frame, time to the first meaningful frame, to the game's first frame and to playable, what it downloads, the heap, netplay messages a second, the host against a replica), profile it to name the hot functions and the biggest files, then try one small change at a time, each measured against the build to beat in alternating runs and kept only when it is better beyond the noise, nothing guarded got worse and the two-browser check still passes; anything else is reverted. Ends with a report in the studio's perf/ folder. Use when someone asks to make a game faster, smoother or lighter, to find out why it stutters, lags, loads slowly or drains a phone, to tune particles, shadows, lighting or bots for frame rate, or to run a performance or optimisation pass overnight.
---

# Make a game faster, honestly

The question is never "does it feel faster". It is: **is this build measurably better than the one before it, beyond
the noise, without looking or playing any differently, and does it still work?** Every number here comes from a real
Chrome on this computer's GPU, two browsers in a room (the host runs the rules and the bots, the replica draws from
snapshots), playing the same seeded presses every run.

One script: `scripts/perf.mjs` in this skill's folder (Claude Code:
`node "${CLAUDE_PLUGIN_ROOT}/skills/perf/scripts/perf.mjs" <command>`), run from inside the studio. It drives the
studio's own `@homie-rocks/studio` (0.19.0 or later: `homie-studio perf`, `perf compare`, `check`, `build --maps`;
0.19.1 also reads whether each big script is minified),
opens at most two browsers at a time, all muted, and writes everything it measures under `.perf/<game>/`
(git-ignored). It prints paths and a few numbers, never the data: read the files it names.

## 0. Before anything

- `df -h .`: keep 10 GB free (it keeps every build it measures). The computer may be shared: every run records the
  load, waits for a calm minute, and a run that started busy is taken again and left out. Never start other heavy work
  (a render, a build of something else, more browsers) while a loop runs.
- Start the site as a background task that outlives the command (Claude Code: the Bash tool's `run_in_background`):
  `npm run dev` (another port: `npx --no-install homie-studio dev --port <n>`). Never `npm run build` by hand while a
  loop runs: the script builds and swaps builds itself and checks the site serves exactly the build it means to measure
  (every file by SHA-256, and the game page as built). Scripts the site's Worker adds to the game page are the site's,
  not the build's: HOMIE_NET, and any a studio's own Worker injects (a small shim) are set aside, listed in BASELINE.md,
  and must stay the same through the loop. Don't change the Worker in the middle of a loop; start a new one.
- Commit or stash what the person is working on first: `try` only ever touches `games/<game>/`, and a revert puts that
  folder back to the kept build.

## 1. The baseline

```sh
node <perf.mjs> baseline <game> --url http://127.0.0.1:8787 [--goal phone.host.frame.p95] [--runs 6] [--seconds 15]
```

It builds the game keeping its source map (never shipped), runs the two-browser check (it must pass: a game that does
not work is not made faster), measures `--runs` runs per device, profiles one run per device, and writes `BASELINE.md`
in the loop's folder: every number with its run-to-run spread, the load during each run, the hottest functions (read
through the source map: `draw (src/main.ts:620)`, not `Xe`), what a player downloads, and **what to try first**,
each hint naming the number it read. Ten to fifteen minutes; poll its output, never end your turn while it runs.

**The goal** is one metric, lower is better (`perf.mjs goals` lists them):

| the person said | goal |
| --- | --- |
| "it stutters on my phone", "make it smoother" | `phone.host.frame.p95` (and `frame.over50`: hitches) |
| "it runs fine but my phone gets hot", frames already at 16.7 ms | `phone.host.busy` (main thread per frame) |
| "it takes ages to load" | `phone.host.load.playable` (4G, slow CPU), `phone.host.load.prePlayKb` (what was really fetched before play) or `bytes.jsGzip` |
| "is the scene too heavy for a phone" | `phone.host.render.calls` / `render.triangles` (the renderer's own counters while playing, when the game exposes them) |
| "I can move before my character has loaded", "it shows too early" | `phone.host.load.ready` (the game's own `net.playable()`) against `load.playable` (control-ready); the headline says the arrival mode, and "ready … after the cover had lifted" means the game should declare `arrival: 'game'` |
| "it opens on a blank screen" | `phone.host.load.look` (the first meaningful frame: the play page's arrival card, 0.26.0) |
| "it lags when lots of people play" | `phone.host.busy` (the host runs the rules) or `phone.host.net.kbOut` (its upload) |

Read BASELINE.md before choosing. **If frames already keep pace with the display (p95 about 16.7 ms), a faster frame
cannot show on this profile**: aim at `busy` (CPU per frame is battery and headroom on a slower phone), or measure a
slower phone with `--cpu 6` or `8`. A goal can be changed per change with `try --goal` (a change aimed at load time is
judged on load time); everything else stays guarded.

## 2. One change at a time

Pick the change from the profile and the hints, smallest first. Make **one** change in `games/<game>/`, then:

```sh
node <perf.mjs> try <game> --name "<the one change, in a line>" --looks same --plays same
```

It builds, runs the two-browser check (two fresh browsers must finish a round together), then measures the kept build
and the changed one **in turns** (before, after, after, before, …), `--runs` each per device. Each before-run and the
after-run beside it are a pair, so a computer that got busier halfway hits both sides of every pair and cancels. Then
`homie-studio perf compare`:

- **KEEP** only when the goal is better beyond the noise: a one-sided signed-rank test on the pairs (Wilcoxon, exact)
  p < 0.05 (with 6 pairs: the change wins at least 5 and loses only the closest), the 95% bootstrap interval of the
  change below zero, and at least 3% better (`--min` at baseline). And no guard got worse (frame time, main thread per
  frame, time to playable, heap, the host's upload: worse in every pair, or p < 0.01, and at least 5%).
- **REVERT** otherwise: `games/<game>/` goes back to the kept source (that folder only; files the change added are
  removed) and the kept build is served again. A change that measures the same is reverted: it costs reading, not
  frames. Never re-run a REVERT hoping for a luckier draw; change something else.
- **BLOCKED**: too many runs started on a busy computer. Nothing is decided and the change stays in place: run the same
  `try` again later, or `revert`.

`--looks` and `--plays` are required, every time. `same` is a promise the screenshots are checked against (brightness,
contrast, detail, colour of each run's host screen, against their own run-to-run spread); anything else is said in
words (`--looks "shadows are softer at the edge"`) and goes into the report. A change made for how a move feels (the
`lab` skill: a hit-stop, sparks, a squash) is measured here when it costs frames: its `--looks` and `--plays` name it. **Never trade how the game looks or plays
for frames without the person agreeing first**; then say it. Fewer bots, a lower resolution, fewer particles, shorter
view distance and fewer physics steps are all trades, not optimisations.

`--measure` (a change kept for another reason: how a move feels, from the `lab` skill): the same build, check, paired
runs and comparison, reported as MEASURED with the verdict and every number, and **nothing is reverted**: the change
stays in games/<game>/ and is served, and the build to beat stays what it was. Say what it costs in those numbers.

Each `try` takes ten to twenty minutes. Its folder (`experiments/<n>-<name>/`) has `RESULT.md`, `change.patch`, the
runs and `compare.json`. `status <game>` lists the loop so far; `revert <game>` drops a change you made but never
measured.

What usually helps, roughly in order (`references/METHOD.md` has the detail and the traps):

1. Work you do every frame that you could do once: gradients, paths, strings, `new` arrays and objects, `measureText`,
   querying the DOM, reading `location` or `localStorage`.
2. Work per thing that can be work per group: one path for many shapes, instancing in three.js, fewer state changes
   (composite modes, materials), fewer draw calls.
3. Garbage: a high `gcPct` or hitches every few seconds mean allocation in the loop.
4. Downloads: nothing that is never imported, big things after the first frame, and a minified copy (the same library
   version) of a script BASELINE.md says is **not minified**. That is read from the code (whitespace, comments, names),
   never from how well it gzips: minified JavaScript gzips about as well as source text, and a bundle with three.js in
   it carries the shaders as GLSL source in strings, which no minifier touches. Minifying it again gains nothing.
5. Netplay: snapshots that send what did not change; the host's upload grows with every seat (`net.kbOut`).

## 3. The report

```sh
node <perf.mjs> report <game>
```

It writes `perf/<game>/` in the studio, to commit with the kept changes:

- `README.md`: the goal, the result (first build against the kept one, with the change, the interval and p for the goal
  and every guard), every change tried and why it was kept or reverted, what changed in how it looks or plays, where the
  time went, what a player downloads, and how it was measured;
- `numbers.json`: the same numbers;
- `before-after/`: the host's screen before and after per device, and each kept change as a patch.

With more than one change kept, it measures the first build against the kept one again (in turns) so the result is the
whole effect, not a sum of steps. Then tell the person the result in one or two sentences, numbers first, and say
plainly when nothing was kept: "nothing I tried was faster beyond the noise" is a result.

## Never

- Never say a change made it faster from the code, one run, a profile, or a number inside the noise. Only `try`'s KEEP
  says that, and the report's interval says how much.
- Never keep a change the two-browser check failed on, or one that changes how the game looks or plays without saying
  so (and without the person's yes).
- Never judge frames on a software renderer (SwiftShader: a Linux VM, a cloud session): those runs are BLOCKED. The
  phone here is an emulation (a slower CPU and 4G on this computer's GPU): it ranks changes; before promising a real
  phone's frame rate, try one (or the iOS Simulator).
- Never run more browsers beside a loop, and never trust numbers taken while the computer was busy: rerun them.
- Never leave a room open on a live site: measure against `npm run dev`; each run opens a fresh room of its own.

## Measured, not estimated

Two numbers here are easy to confuse with ones that come from the game's files, and they are not the same thing:

- **First-play traffic** (`load.prePlayKb`, and "Fetched before playable" in the reports): every request the browser
  made up to the moment the game was playable, on the wire, one run on one device. The shipped payload (`bytes.*`,
  `perf sizes`, the asset check's download figure) totals the built folder, which also holds files the game never
  asks for and music it streams later. A run that never became playable has no pre-play number at all.
- **Runtime scene cost** (`render.calls`, `render.triangles`): the renderer's counters while the game is played, read
  from the port probe when the game exposes them: `exposePort(net, { extra: { drawCalls: () =>
  renderer.info.render.calls, triangles: () => renderer.info.render.triangles } })`. They include procedural geometry,
  repeated characters, effects and shadow passes, which an inventory estimate from the asset manifest does not. A
  game that exposes neither has no such metric: "not measured", never zero.

An address this computer's Node.js cannot look up (a browser on the same computer may still open it) stops the loop
as BLOCKED, "network preflight failed, before any page or game was opened": measure against the local site
instead. It is never reported as the game or the site failing. `check`, `perf`, `shoot`, `port check`, the
playtest and a deploy's read-back all say it in these words.
