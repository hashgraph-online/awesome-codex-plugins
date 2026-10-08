# The Game Lab's calls, takes and rules

`import { lab } from '@homie-rocks/studio/lab'` (also `lab` from `@homie-rocks/studio/port`, and `HomiePort.lab` in a
static game). Outside the lab every call is a no-op and `lab.on` is false.

## The calls

| Call | What it is for |
| --- | --- |
| `lab.on` | True in a lab pane. Guard per-frame reporting with it. |
| `lab.time.dt(t, max = 0.05)` | Seconds since the last frame, capped. Call once a frame with requestAnimationFrame's time. |
| `lab.time.now()`, `.frame`, `.fps`, `.scale`, `.paused` | The clock (performance.now(); the lab's in the lab), the frame number, frames a second, the speed. |
| `lab.tunables(json)` | tunables.json's values by name (`T.knockSpeed`); in the lab, the sliders' values. |
| `lab.phase(name \| null, note?)` | The phase from now on (until the next call). Short capitals; a note saying what it is for. |
| `lab.track(name, value, unit?)` | A number this frame, graphed New against Today. |
| `lab.pose(name, { x, y, ... })` | A small picture this frame, for overlays. |
| `lab.past(name, count, every)` | The last poses, newest first, not this frame's. |
| `lab.camera({ name: preset })` | Preset views as buttons; returns a function giving the active preset (the first outside the lab). |
| `lab.overlay(name, (ctx, ...rest) => {})` | An overlay the lab can switch on, drawn by the game. |
| `lab.draw(ctx, ...rest)` | Draws the overlays that are on (call it in world space, pass the scale). |
| `lab.stage` | The take's stage name, or null (always null outside the lab). |
| `lab.random()` | Dice for juice: the lab's second stream; Math.random() outside. |
| `lab.hold()`, `lab.ready()` | A game that loads assets after its page's load event: hold early, ready when it can play. |

## What the lab drives in the page

The harness (lab/harness.js) is the page's first script in a lab pane. requestAnimationFrame, performance.now(),
Date.now() and `new Date()`, setTimeout and setInterval run on the lab's clock; Math.random() is seeded;
localStorage and sessionStorage are the take's own, in memory; keys and pointer presses come from the take (or, while
recording, the person's, held back to the next frame and given to both panes); focus and visibility changes never
reach the game. A game that reads another clock (an AudioContext's time, a fetch's timing, crypto random numbers)
for gameplay will not replay the same: the lab shows "Replays differ at F<n>". Find what that frame read.

## tunables.json

One tunable a line; the lab writes kept values back in this shape:

```json
{
  "knockSpeed": { "value": 950, "min": 200, "max": 2000, "step": 10, "unit": "px/s", "group": "Knock", "note": "How fast a bumped body leaves" },
  "hitStopMs": { "value": 70, "min": 0, "max": 200, "step": 5, "unit": "ms", "group": "Knock", "note": "The hit lands before it flies" }
}
```

A bare number is a value with no range. A kept value outside its range moves the range's end.

## lab.json: takes

```json
{
  "v": 1,
  "default": "knock",
  "takes": {
    "knock": {
      "note": "Bump the dummy beside you",
      "seconds": 2.2, "seed": 7, "stage": "dummy", "device": "desk", "fps": 60, "view": "close", "track": "speed",
      "overlays": ["onion"],
      "storage": { "homie-saves.local.<game>": { "saves": {}, "stats": {}, "fallen": [] } },
      "inputs": [
        { "at": 0.5, "key": "Space", "hold": 0.1 },
        { "at": 1.0, "down": "ArrowRight" }, { "at": 1.6, "up": "ArrowRight" },
        { "at": 2.0, "pointer": "down", "x": 120, "y": 600, "id": 2, "pt": "touch" }
      ]
    }
  }
}
```

Times are seconds; x and y are CSS pixels of the page at the device's size (desk 1280x800, phone 390x844). `storage`
seeds localStorage (a saved hero, so a "make your hero" panel does not cover the take). `homie-studio game new` copies
lab.json with the game and renames its save keys to the new id.

## Multiplayer rules for a feel change

1. Every screen draws it: from an event the host sends, or from a change in the snapshot. Never only on the host.
2. The host owns gameplay: holds, pushes, slides. A replica's body is taken (`net.take`) for as long as the host
   drives it, hit-stop included.
3. Motion is a curve of time (`1 - (1 - u) ** n` over a duration), never a per-frame multiply: the same distance at
   12, 30 and 60 frames a second.
4. Juice rolls `lab.random()`.
5. Two fresh browsers must still finish a round: `homie-studio check <game>`.

## What `lab check` writes

`.studio/lab/<game>/check-<time>/`: summary.json (per build: phases with frames and ms, each track's peak, when and
where it ends, JavaScript per frame, errors; whether a replay matched), REPORT.md (New against Today), sheet.png
(the lab at each phase's start), still.jpg (the whole page at the busiest moment).
