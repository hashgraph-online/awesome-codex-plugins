# A gameplay trailer (15 to 60 seconds)

Real footage of the studio's own game, cut on the beat of the studio's own music. Free: no
provider, no model, nothing generated.

## 0. The short way: `trailer`

```sh
npm run dev      # as a background task
node <video.mjs> trailer <slug> --game <id> --url http://127.0.0.1:8787 --seconds 45 --length 20 --title "GAME NAME"
```

One command does sections 2 to 5 below a different way, and needs no song:

1. **Films frame by frame** (`record-fixed.mjs`): the page's clock is the recorder's. Each film frame,
   `requestAnimationFrame`, `performance.now`, `Date`, `setTimeout`, `setInterval`, CSS animations and
   transitions and Web Animations move on by exactly 1/fps, the page draws, the frame is copied. A
   countdown on a timer, a callout faded by CSS and the game loop stay in step, and no frame is held.
   `capture.json` gives `realSeconds` and `speed` (film seconds per real second).
2. **Rebuilds the sound** from the capture log (`events.json`): the `sound` skill's `sound.js` pushes
   every sound it schedules onto `window.__homieSoundCapture.events` when a recorder set that global
   before the page ran (file, gain, rate, pan, loop, delay; stops, ducks, fader moves). The files are
   fetched from the page's own origin and mixed at 48 kHz: `sound.wav`, `sfx.wav`, `music.wav`.
   The player's compressor is stood in for by a peak limiter at -1 dBFS.
3. **Picks the shots** from that log: each effect's start scores its tenth of a second, divided by the
   square root of how often that sound played, plus 0.35 of the picture's motion. With music in the
   log, a shot is one bar (two when a bar is under 1.2 s, half when over 2.6 s), the bed is the game's
   own `music.wav` from one of its bar lines, and only `sfx.wav` is cut with the picture.
4. **Cards and three deliveries**: an end card (`--end`, `--sub`, `--small`), a title card with
   `--title`, in the game's look; 16:9, 1:1 and 9:16, each -14 LUFS.

What it does not cover, exactly:

- Sound that does not go through `sound.js` (the game's own oscillators, an `<audio>` element, speech):
  not in the mix. A game with its own audio code can push the same events (the head of `sound.js`
  lists them). No events at all: a silent film and a warning; use `capture` (it records the speaker).
- The audio clock, `<video>`/`<audio>` elements, Web Workers and the network are not on the virtual
  clock. The big screen (`/<id>/tv`, the default) follows a live room on a relay that keeps real time:
  at a `speed` near 1 the film is right; well under 1 the room runs fast in the film, and the result
  warns. Render smaller (`--scale`), or use `capture`. Rendering is never run faster than real time
  unless `--no-pace` (for a page with no server behind it).
- Steps (`--steps`) are wait, waitFor, click, tap, key, keys, type, focus and caption, timed on the
  film's clock; no cursor is drawn, and hover, drag, scroll and goto belong to `record`.
- A computer's page only (no phone emulation); the 9:16 and 1:1 files are made from the 16:9 film.
- The highlights are a score, not a judgement: read `shotsPlayed`, look at the sheet, edit `work/edl.json`.

`--keep-capture` re-edits the film already made. Sections 5 and 6 below still apply (look, check, publish).

## 1. The music

The bed is a song from the `music` skill (`--song <slug>` everywhere below): its plan gives the
exact tempo and its bar lines. The best trailer bed has a clear beat and a lift in its first few
bars; `--bed-from-bar <k>` starts the trailer at a later bar (a chorus). With no song, the
trailer runs on the game's own sound and cuts every two seconds.

## 2. The capture

```sh
npm run dev      # as a background task: the studio's site at http://127.0.0.1:8787
node <video.mjs> capture <slug> --game <id> --url http://127.0.0.1:8787 --seconds 60
```

- If another site already holds port 8787, start this one with
  `npx --no-install homie-studio dev --port <free port>`, and check the address answers with
  this studio's name before capturing.
- Stop it afterwards with `npx --no-install homie-studio dev --stop` (this studio's server and
  nothing else).
- It opens the game's big screen (`/<id>/tv`): a spectator in a live public room. The room starts
  at once with bots in empty seats, so there is always a round to film. Nothing is pressed.
- The picture is Chrome's own frame stream with the time each frame was shown; it is laid onto
  30 fps, and a frame the page did not paint in time is held and counted (`heldFrames`). The
  sound is copied off the game's WebAudio output on the audio clock, which is fitted to the page
  clock, so a hit and its sound stay on the same frame.
- Capture two or three times the trailer's length: the edit picks the best moments.
- `--view play` films a seat instead of the big screen, but that seat is taken by the capture and
  stands still (its avatar is idle, and the room counts it). Prefer the big screen. Never script a
  player to look good for the camera: what is filmed is the game as it plays.
- A 3D game on a laptop: check `sourceFps` in `capture.json`; under 30, capture again with fewer
  other programs running, or a smaller `--width`/`--height`.

## 3. Cards

```sh
node <video.mjs> card <slug> --name title --text "GAME NAME" --sub "a one-line promise"
node <video.mjs> card <slug> --name end --text "Play free" --sub "<the play link>" --small "Real gameplay. Empty seats are filled by bots."
```

Cards are drawn in Chrome at 1920x1080 and 1080x1920 (no font setup needed). Keep the title to a
word or three; the end card is where people go next.

## 4. The edit

```sh
node <video.mjs> edl <slug> --length 30 --song <music slug> --title "GAME NAME"
```

`work/edl.json`: a title card of one bar, shots of one bar (two beats when a bar is longer than
2.6 s), the end card on what is left (at least 2.5 s). Shots are the busiest non-overlapping
windows of the capture, measured as motion, that do not look like a shot already picked, shown in
the order they happened. Each shot pushes in slowly (to 1.25x by default, `--push 1` for none)
toward where the picture changes most: a camera move on the real footage, nothing added. Every
cut is on a bar line. Edit it by hand: swap a shot for a better moment (`in` is seconds into the capture),
make one shot two bars long (and shorten another), move the song's start. Keep the total.

## 5. Cut, check, look

```sh
node <video.mjs> cut <slug>
node <video.mjs> sync <slug>
node <video.mjs> sheet <slug> --in videos/<slug>/<slug>.mp4 --every 0.5
node <video.mjs> sheet <slug> --in videos/<slug>/<slug>-vertical.mp4
```

- 16:9 is 1920x1080; 9:16 is 1080x1920 with the whole game frame across the middle over a
  blurred, darkened fill of itself (a crop would hide the action at the edges).
- Sound: the song, with the game's own sound 8 dB under it where the game made any, both
  deliveries at -14 LUFS and -1.5 dBTP; H.264 High, yuv420p in limited range, converted to and tagged
  BT.709, faststart. `--square` adds 1:1 (1080x1080; `card … --square` draws its cards).
- Cuts are counted in frames: each cut is on the frame nearest its bar line (`cuts` in the result
  gives the frame, the time and how far from the bar it is, never over half a frame), every frame's
  timestamp is its number over 30, and the film is exactly its frames long. A bar of 1.875 s is
  56.25 frames: the shots run 56, 57, 56, 56 frames, and nothing drifts.
- `sync` must pass (every cut within a frame of its beat), and the contact sheets must show the
  game, readable, at every cell. A beat with no onset right on it (a rest, a pickup note just
  before the bar) is listed, not judged: never move a cut off its bar to make the check pass.
- A fixed camera on a whole arena reads small on a phone: prefer moments where players are close
  together, or a bigger push (`--push 1.5`).

## 6. Publish

```sh
node <video.mjs> add <slug> --title "GAME NAME trailer" --kind trailer --for-game <id> --for-song <music slug> --publish
node <video.mjs> publish <slug>
```

The page gets a Play button for the game and the capture's honesty line ("recorded from the
game running in a live public room; seats without a person are the game's own bots").
