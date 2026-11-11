# Briefing the game (Claude Fable 5.2 / Claude Code)

The trailer can only show what the game has. Brief the game with the trailer in mind: one strong
look, one verb you can read in two seconds, one moment worth slow motion.

## What spread on launch day (X, 2026-11-09/10)

| post | what | reach | notes |
|---|---|---|---|
| [@felixrieseberg](https://x.com/felixrieseberg/status/2119925633564463609) | rainy-port 3D FPS, playable in the browser; models, sounds, textures from code | 2.3M views, 6.2k bookmarks | one-shot prompts, no human feedback; ~$550 API, ~8 h |
| [@kevin_t_ngo](https://x.com/kevin_t_ngo/status/2119868968307695818) | lantern boat ride through 8 dreamlike worlds (docks, carnival, cherry trees, lantern forest, flooded library, cave, snow, aurora) | 388k | |
| [@mattshumer_](https://x.com/mattshumer_/status/2119870965106483384) | voxel engine with sound from a single prompt | 222k | |
| [@ericmaskfr](https://x.com/ericmaskfr/status/2119910195325481026) | 80s-Miami open-world crime game: cops, cars, garage, missions, all sounds generated in Python | 148k | 2 h 14 min; framed as a clone of a famous franchise (do not copy that) |

Every one of them was posted as a **video**: what people shared was the recording.

## The example of a good one-shot brief

@ericmaskfr's prompt (verbatim):

> you're a senior game dev. build a third-person open-world crime game in a sunny 80s miami-style
> city. make the loop tight: walk, fight, steal a car, get chased, earn money, spend it. every system
> feeds the next: crimes bring heat, heat brings cops, missions pay, money unlocks the garage. cars need
> weight: gears, skids, real crashes. the city has to feel alive with traffic, people and day into
> night. no audio files, generate every sound in code. after each system, play it yourself, screenshot
> it and fix what looks wrong. don't stop until a stranger could play for 10 minutes without hitting a bug

Why it works: a role; a loop stated as verbs; systems that feed each other (so escalation exists for
the trailer); one feel requirement ("cars need weight"); a no-assets rule; a self-test loop with
screenshots and a stopping condition a stranger could judge.

## Three original brief templates

**Arcade flyer (the Lantern Canyon pattern)**
> Build a single-file browser game in three.js (pin the version from jsDelivr, no downloaded assets).
> The player is a [paper lantern glider / a seed on the wind / a tiny drone] moving forward through
> [a dusk canyon / a flooded city / a forest at night]; arrows steer, Space boosts. Collect [sparks],
> chain them for a multiplier, pass through [gates] for a bonus. Look: near-black sky, one warm key
> colour [#ff5315] on the player, a cool fill [teal], haze, bloom. HUD in HTML, top corners, clean
> type. Speed and particle density rise with distance. Generate every model, texture and sound in code.
> Play it yourself after each feature, screenshot, fix what looks wrong.

**Arena survival**
> Build a single-file browser game in three.js: a top-down arena at night where [a lighthouse keeper]
> holds off [waves of shadow crabs] with [a sweeping light beam]. Mouse aims, click pulses. Waves grow;
> every 5th wave a boss. Each hit sparks; the boss dies in a slow shockwave. Strong silhouettes, one
> accent colour, fog. No assets, all sound in code. Test each wave yourself and fix what looks wrong.

**Exploration diorama**
> Build a small explorable world in one HTML file with three.js: [a floating island village at dawn].
> WASD walks, the camera follows. Three places to discover, each with a light, a sound and a short
> line of text. Day turns to dusk over 3 minutes. Everything procedural, no assets, all sound in code.
> Walk the whole island yourself, screenshot each place, fix what looks wrong.

## Append this to any brief: the trailer hooks

> Make it recordable: expose `window.__game = { ready, renderer, camera, scene, player, setup(opts),
> events }`. `ready` turns true after everything loaded and the first frame rendered. `setup(opts)`
> resets to a known state (level or distance, score, hud on/off, autopilot). Push sound-worthy moments
> to `events` as `{ type }`. Animate only from requestAnimationFrame time or performance.now deltas.
> Generate the level from its own seeded random stream, separate from effects. Add an attract-mode
> autopilot that plays well. HUD in vh units with at least 6vh side margins; no debug text unless
> `?debug`. No real brands, logos, franchises or real people.

## Game-side lessons from building Lantern Canyon

- **Separate random streams.** World generation, level layout and effects each get a seeded stream.
  Adding decorative lanterns once moved every pickup and broke the scripted inputs.
- **Expose the layout** (`__game.layout`: pickups, gates, obstacles) so inputs can be planned and searched
  instead of guessed.
- **An autopilot** made 6 of 8 shots trivial; only the shot that sells the controls used keys.
- **Hooks for trailer cameras**: an `anchor` (player position, level heading, no roll) and fixed `place(s)`
  objects along the level. Cameras parented to a banking player make people seasick.
- **Look at the game from trailer angles early.** Low and wide cameras found what the chase camera never
  showed: rim slivers, sprites that turned into blobs near the lens, a pillar that read as a red pole.
  Fade camera-near sprites in `onBeforeRender` (it receives the camera actually used).
- **Readable hero object.** The lantern went through 3 passes: a white over-bloomed blob → a striped
  barrel → a fresnel "paper" shader (bright core, dark edge, ribs) with veined, translucent wings.
- **Light for the palette, not realism.** Near-black sky, teal hemisphere + a teal moon from the right,
  a warm low dusk light, a small warm point light on the player; the river reflects the sky gradient in a
  30-line shader. The first pass, with a strong point light, painted everything orange.
