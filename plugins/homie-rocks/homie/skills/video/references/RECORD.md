# Recording a page while a script drives it

`record` (scripts/record-page.mjs) records any web page in real time while a steps file drives it:
clicks, taps, keys, typing, scrolls, drags, and waits for a selector, a text or a state. Use it for
a studio's own game page (land, press Play, play a little), a site walkthrough, a product demo or a
tutorial. `capture` is still the one for a trailer's gameplay (the game's big screen, nothing pressed).

```sh
npm run dev                                                    # background task; the site at http://127.0.0.1:8787
node <video.mjs> record <slug> --steps <steps.json> --url http://127.0.0.1:8787
node <video.mjs> record <slug> --steps <steps.json> --url http://127.0.0.1:8787 --device phone --name phone
node <video.mjs> sheet <slug> --in videos/<slug>/work/record/recording.mp4
```

Outside a studio (any project, any address): `node <skill folder>/scripts/record-page.mjs --steps
<steps.json> --out <folder>`. It needs Chrome, ffmpeg and `puppeteer-core` (a studio has it; elsewhere
install it yourself with `npm install --no-save puppeteer-core`).

The take lands in `videos/<slug>/work/record/` (`--name <take>`: `work/record-<take>/`):

- `recording.mp4`: 1920x1080 at 30 fps for a computer, 1080x1920 for a phone (`--device phone`: a
  360x640 page at 3x, touch on, a phone's user agent), H.264, faststart;
- `recording.json`: every step with the second it started and how long it took, what its own frame
  received while it ran (`received`: keys, pointer presses, touches, or "another page opened"), the
  page's and the game's real frame rates, frames painted and held, the GPU renderer, warnings;
- `captions.vtt` when steps have captions (copy it to `videos/<slug>/captions.vtt` for the page).

The command prints a few lines (`--json`: a small object of paths and numbers, never media).

## The steps file

```json
{
  "path": "/gem-rush/",
  "device": "computer",
  "tail": 2,
  "steps": [
    { "wait": 1500, "caption": "Gem Rush, on the studio's own site" },
    { "click": "a[data-play]", "caption": "Press Play" },
    { "waitFor": { "frame": "game", "selector": "canvas" }, "timeout": 30000 },
    { "key": "ArrowRight", "hold": 900, "frame": "game" }
  ]
}
```

Where it starts: `"url"` (any address), or `"path"` joined to `--url` (the local `dev` site or the
live one). The page is opened and settled (`"settle"`, 1.5 s), then the recording starts and the steps
run one after another, at the speed they take. It ends `"tail"` seconds after the last step, or at
`--seconds` (120 by default, 600 at most).

Every step is one of these (`{ "click": "a" }` is short for `{ "do": "click", "selector": "a" }`). Any
step takes `"caption"` (a cue from the second it starts, `"captionSeconds"` long, 3 by default),
`"timeout"` (ms, 20000) and `"optional": true` (a failure is noted and the steps go on).

| Step | What it does |
| --- | --- |
| `{ "wait": 1500 }` | Waits, in milliseconds. |
| `{ "waitFor": "<selector>" }` | Until it is visible. `{ "waitFor": { "text": "Round 2" } }`, `{ "waitFor": { "js": "window.game?.started" } }` (any expression, true when it is), `{ "waitFor": { "frame": "game" } }` (until the frame exists). |
| `{ "click": "<selector>" }` | The cursor glides there (`"ms"`, 450), a press ring, a real click. `"at": [x, y]` instead of a selector (CSS pixels, or 0..1 of the page), `"offset": [0.5, 0.7]` inside the element. On a phone, a tap. |
| `{ "tap": "<selector>" }` | A touch tap, with a ring. |
| `{ "drag": { "selector": "canvas", "offset": [0.5, 0.7], "to": [90, 0], "ms": 500, "hold": 900 } }` | A held press that moves by `to` (CSS pixels) over `ms`, then held: a virtual stick on a phone, a drag on a computer. |
| `{ "hover": "<selector>" }` | The cursor glides there; hover styles answer. |
| `{ "key": "ArrowRight", "hold": 900 }` | One key held for `hold` ms. `"Shift+ArrowUp"` holds both. `"times": 3` repeats it. |
| `{ "keys": ["ArrowUp", "ArrowLeft"], "hold": 300, "gap": 120 }` | Several, one after another. |
| `{ "type": "Owl", "into": "input[name=nick]" }` | Clicks into the field, then types at `"delay"` ms a letter (70). |
| `{ "scroll": 600 }` | Scrolls by wheel over time (`"ms"`), never a jump. `{ "scroll": { "to": "#pricing" } }` brings it to the top quarter. |
| `{ "focus": "game" }` | Gives a frame the keyboard (a play page usually does it itself). |
| `{ "goto": "/games/" }` | Opens another address (a path joins `--url`). |
| `{ "caption": "…" }` | A caption on its own, with no action. |

`"frame"` on any step names where its selector, keys or check are: `"game"` (a studio game's own
frame, `/<id>/__game/`), a piece of a frame's address, or the page itself (the default). Keys go to
the frame that has the keyboard; `"frame": "game"` gives it to the game first.

Examples:

- `references/examples/studio-play.json`: a studio's own game from its landing: Play, then the arrow
  keys, on a computer.
- `references/examples/studio-play-phone.json`: the same on a phone: a tap on Play, then the game's own
  touch stick, dragged and held.
- `references/examples/site-walkthrough.json`: an ordinary page (example.com): a scroll and a hover.

The two studio examples are tested: `scripts/studio-check.mjs --record` records both against a new
studio's Gem Rush under `homie-studio dev` (CI runs it on Linux), and fails when a step fails or the
game's frame received none of the input.

For another game: its id in `path`, and its own controls (`games/<id>/src`: what its keydown and
pointer handlers listen for).

## Honest frames, at real speed

- **Real time.** The steps run at the speed the page answers; the film lasts exactly as long as the
  recording. Nothing is sped up, slowed down, cut or reordered in the take; any edit comes after, in
  the open.
- **Every frame is one the page drew.** Chrome's compositor frames are kept with the time each was
  presented and laid onto 30 fps by holding the newest one. A moment the page did not repaint is held,
  and counted (`heldFrames`); a still page lasts as long as it showed. Never interpolated, never
  blended (the test suite guards it): **interpolated frames are fabrication.**
- **A GPU, or say so.** Headless Chrome runs on the GPU flags; a software renderer (SwiftShader, on a
  machine without a GPU) draws a WebGL game at a few frames a second and makes it look stuck. The
  result names the renderer and the page's own frame rate (`pageFps`, measured with
  requestAnimationFrame in the page and in the game's frame); under 20, or on a software renderer, it
  warns, and the recording shows a slow computer, not the game. Record on a computer with a GPU, or at
  `--scale 0.67`. `--min-fps 20` makes such a take fail instead.
- **Delivered is not correct.** `received` says the keys and taps reached the game's frame; it does not
  say the game did the right thing with them. Look at the take (`sheet`) before anyone else does.
- **The cursor is the recorder's.** The arrow and the press rings are drawn over the page to show where
  the script pointed and pressed (`--no-cursor` leaves them out). The take's honesty line says so, and
  `add --file <the take>` puts it on the video page.
- **Sound.** A studio game's own WebAudio (its `/__game/` frame), on the picture's clock: steady
  presses land within a frame or two of their sound. Any other page records silent; a bed or a voice-over
  is added in the edit.
- **Bots are bots.** A studio game fills empty seats with its own bots: never caption them as people.
- **Mask before it is public.** A recording shows no address bar, but a page can print its own
  address: a local `dev` address, a room code, a QR code that joins a room (the big screen's). Decode
  every QR in a public video. The recorder's visits are tagged as the studio's own QA, so the studio's
  stats never count them as visitors.

## Frame by frame instead of real time

`record-fixed.mjs` (what `trailer` films with) takes the same steps file but steps the page's clock
1/fps a frame instead of filming it live: no held frames on a slow page, and waits and holds are in
film time. It has wait, waitFor, click, tap, key, keys, type, focus and caption only, draws no cursor,
films a computer's page only, and its sound comes from the game's sound log, not from the speaker.
`references/TRAILER.md` section 0 says what its clock does and does not reach.

## Disk and size

A take keeps every painted frame as a JPEG until it is encoded (about 150 KB each at 1080p, up to 60
a second), then deletes them. It stops below 10 GB free (`--min-free-gb`). Check `df -h .` first.
