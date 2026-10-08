---
name: lab
description: Build a Game Lab for one mechanic of a studio's game (the jump, a hit, a dash, a drift, a landing) and iterate on how it FEELS with the creator, side by side. The lab plays one short take in two builds at once, New (the working tree) and Today (the last commit), on one clock with the same seed and presses, slowed to a tenth or stepped a frame at a time, with a timeline of named phases, graphs of tracked values New against Today, the game's own onion skins and arcs, preset views, a phone-size view, and live sliders that write kept values back into the game's tunables.json. Use when someone says "iterate on the jump", "make the hit feel punchier", "tune the drift", "the dash feels floaty", "the landing is stiff", "add juice", "hit-stop", "squash and stretch", "screen shake", or asks for an animation or feel editor for their game.
---

# The Game Lab: one mechanic, New against Today

A studio is the folder with `studio.json`. The lab is `npx --no-install homie-studio lab <game>` (from
`@homie-rocks/studio` 0.20.0): a page on this computer that plays a **take** (games/<game>/lab.json) in **New** (the
working tree, rebuilt on every save) beside **Today** (HEAD, or `--today <ref>`). Both run on the lab's clock: frame f
is exactly f/fps seconds, the dice are seeded, the presses land on the same frames, so a take plays the same every
time and the two builds can be compared frame by frame. The page checks that too: "Replays match" (or where they
differ). `homie-studio lab check <game>` plays the same take headless and writes numbers, a contact sheet and a still.

The game opts in with a few calls from `@homie-rocks/studio/lab` (every one a no-op outside the lab, so they stay in
the game). `references/API.md` has every call, the take format and the multiplayer rules; `references/PRINCIPLES.md`
has the principles of feel this skill works from, with honest sources.

## 0. Before anything

- `df -h .`: keep 10 GB free. Commit or stash what the person is working on: Today is a commit, and the lab never
  touches git beyond reading it (Today is built from git's own checkout of the ref, in `.studio/lab/`, git-ignored).
- Name the mechanic in one line with the person ("the bump in Gem Rush: you wave, a body near you flies"), and find it
  in the code: the input that starts it, the state it changes, where it is drawn. Say which numbers shape it.

## 1. Instrument it, change nothing, commit

Make the lab able to see the mechanic **without changing how it feels** (Today must be the game as it is):

1. **tunables.json** next to game.json: move the numbers that shape the mechanic into it, at their current values,
   each with a range, a unit, a group and a note in plain words. Read them with `const T = lab.tunables(tuning)`.
2. **Phases** at its natural beats: `lab.phase('LAUNCH', 'Leaves at full speed, slows evenly')`, `lab.phase(null)`
   when it is over. Short capital names; the note says what the phase is FOR. Name today's phases honestly: a
   mechanic with no anticipation has no COIL.
3. **Tracks** that show its motion: speed, height, distance, squash, a camera's offset (`lab.track(name, v, unit)`).
   Speed from the position each frame (distance / dt) is honest whatever the code does inside.
4. **Poses and overlays**: `lab.pose('subject', { x, y, sx, sy, a })` each frame, and the game's own `onion` (ghosts
   every few frames), `arcs` (the path with a dot a frame: spacing) and a `reach` or hit box (`lab.overlay`), drawn
   by `lab.draw(ctx, scale)` in world space.
5. **Views**: `lab.camera({ game: null, close: { zoom: 2.4 }, arena: { whole: true } })`; 3D: side, front, top, orbit.
6. **Characters** (`@homie-rocks/studio/animate`): pass the lab's tunables to `loadCharacter(models, url, { tune: T })`
   and copy its `ANIM_TUNING` (fade, walkSpeed, runSpeed, actSpeed, jumpStretch, landSquash, squashHz, lean, flinch,
   lookAt, spring) into tunables.json's "Motion" group: the clips' blends, the squash and stretch and the lean become
   sliders too. Report the character's own `state` (IDLE, RUN, JUMP, FALL, LAND, ATTACK, HIT) as phases when the move
   is an animation. The `hero-rush-3d` starter's takes ("jump", "swing") show it; the `animate` skill has the rest.
6. **A stage** when the mechanic needs a target (a dummy to hit, a ledge to jump from): `lab.stage === 'dummy'`
   where the round starts. Only the lab ever sets it. Keep a real-play take too.
7. **A take** in lab.json: a few seconds, a seed, the presses (`{ "at": 0.5, "key": "Space" }`), the view and track
   to open on. Or record one: press REC in the lab and play it in NEW (both builds get the presses).

Guard allocation: report from one `if (lab.on) labReport(dt)` a frame. Then:

```sh
npx --no-install homie-studio lab check <game>     # phases show, replays match, New = Today
git commit -m "Lab: instrument <the mechanic> (no change to how it feels)"
```

## 2. Look for what it is missing, with the person

Open the lab (`npx --no-install homie-studio lab <game>`, a background task; give the person the link; never open a
browser yourself) and read the take at ¼ speed with the onion skin and arcs on. Say what you see in the terms of
`references/PRINCIPLES.md`: no anticipation, no impact moment (hit-stop), even spacing (no ease), a creep and a pop at
the end, no follow-through or overlap, a rigid body (no squash and stretch), a camera that never reacts.

References: describe the principle and, if it helps, a well-known game where anyone can see it, in your own words.
Never copy another game's art, code, sounds or frame data, and never state another game's exact numbers unless you
measured them yourself from footage the person can see or a public source you name.

## 3. Propose it as phases and tunables, then build New

Write the proposal as the phases the move will have and the number that shapes each one, for example:

> HIT-STOP 70 ms (the body holds, white, squashed) → LAUNCH (leaves at 1500 px/s, stretched 30%) → SLIDE (eases into
> the stop over 185 px, the same at 12 fps as at 60) → SETTLE 260 ms (squash, then a wobble: overlap).

Change the game in the working tree; the lab rebuilds New on save and replays the take. Then:

```sh
npx --no-install homie-studio lab check <game>     # New against Today: phases, peaks, JavaScript per frame
```

Read REPORT.md and **look at sheet.png** (the lab at each phase's start, New beside Today) before you say anything
about it. Tell the person in a few lines: which phases New has that Today did not, the numbers that moved, and what
to watch for in the lab. The person tunes with the sliders and presses **Keep in code** (written into
tunables.json, one line a value), or tells you, and you run `npx --no-install homie-studio lab set <game> name=value`.

## 4. Multiplayer: every screen, the host's rules

A studio game is played in a room. A feel change must look the same on every screen and keep the two-browser check
green:

- **Presentation from what every screen already has**: an event the host sends (`net.send('knock', { slot, dx, dy })`)
  or a change in the snapshot (a slime's hit points dropping). Flashes, squash, sparks and numbers are drawn locally.
- **Gameplay on the host**: a hit-stop that holds a body, a push, a slide's curve. Make motion frame-rate independent
  (a curve of time, not a per-frame multiply), so a 30 fps phone moves the same distance.
- **Juice dice**: `lab.random()` for particles and shake, never Math.random(): the world's dice must be the same in
  both builds for the lab to compare them, and lab.random() is Math.random() outside the lab.
- A change that moves gameplay (a push that puts a target out of reach) shows in the lab's numbers: read them. One
  push in this skill's own proof took a slime out of reach and the next two strikes missed; a lunge fixed it.

Then the game's own check: `npm run dev` (background), `npx --no-install homie-studio check <game> --url
http://127.0.0.1:8787`. It must pass before anything is kept.

## 5. When a feel change costs frames, say so with numbers

`lab check` prints the game's JavaScript per frame, New against Today, on the same frames (the mean: Chrome times a
page in steps of about 0.1 ms). It is a hint. For the real cost, the `perf` skill measures both builds in a room, on
an emulated phone, in alternating pairs: `perf.mjs baseline <game>` with games/<game>/ at Today (`git stash` the
change, or check out HEAD's copy of the folder), then the change back and `perf.mjs try <game> --name "<the feel
change>" --looks "<what looks different>" --plays "<what plays different>" --measure`. **--measure is required here**:
without it `try` reverts anything that is not faster, and a feel change is kept for its feel, not its speed. Tell the
person the result in numbers: frames (p95), the main thread per frame, time to playable, against Today. In this
skill's own proof the bump cost 0.09 ms of main thread a frame on the emulated phone (1.48 to 1.57 ms, +4.9%, within
the noise) with frames unchanged at 16.7 ms. Never say a feel change is free from the code.

## 6. Keep what the person likes, then commit

The person decides. Revert what they did not like (only those lines, in games/<game>/), keep the rest, run
`lab check` and the two-browser check once more, then commit with the phases in the message:

```sh
git add games/<game> && git commit -m "<Game>: the bump lands (hit-stop 70 ms), flies stretched, eases out, settles"
```

Record a side-by-side clip the person can share with the `video` skill's `record`, driving the lab page itself:
`references/record-lab.json` is a steps file (play at 1x, then ¼ with the onion skin, then step through the phases).
`node <video.mjs> record lab-<game> --steps <steps> --url http://127.0.0.1:8790`. Stop the lab when done:
`npx --no-install homie-studio lab --stop` (this studio's only; it also removes the checkouts Today was built from).

## Where people see it

- **Claude Code**: the link `http://127.0.0.1:8790/<game>/` (run the lab as a background task).
- **Claude Desktop and claude.ai** (Homie Studio's local tools): the `game_lab` tool starts the lab and answers with
  a card: a still of New beside Today at the take's busiest moment, the phases of each, the numbers, and Open.
- **Anyone**: the recorded clip, and the commit, whose message names the phases.

## Never

- Never say it feels better from the code. Show the take; the person feels it.
- Never change Today: instrumenting changes nothing a player feels, and is committed on its own first.
- Never put a lab call where it allocates every frame outside the lab (`if (lab.on)` around reporting).
- Never use Math.random() for juice, or read a clock other than requestAnimationFrame's time and net.now().
- Never edit a take to make New look better; record a new one and say why.
- Never leave the lab running when the work is done (`lab --stop`), or open a browser for the person.
