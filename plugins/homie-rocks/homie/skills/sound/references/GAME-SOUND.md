# Sound in a game

What makes a web game sound finished, and the ways a correct-looking sound system goes quiet. Each
rule below was learned by a game that broke it.

## What the game owes a player

- **Every action answers with a sound**, on the frame it happens: a press that does something makes
  a sound; a press that is refused makes a different one (`deny`). Movement itself does not need a
  sound per press, but landing, bumping and stopping do.
- **Sound starts on the first touch**, with no "tap for sound" screen: browsers keep audio suspended
  until a gesture, so resume inside the first `pointerdown`, `touchend` or `keydown` (the player's
  `sound.js`, or the port toolkit, does it). On iOS a held stick is only a gesture when the finger
  lifts, so the first tap or release is when sound begins; the silent switch mutes Web Audio unless
  `navigator.audioSession.type = 'playback'`.
- **Music carries the round**: calm at the start, a change when it gets tense, something for the last
  ten seconds, a stinger for the result. A round that is all one intensity has no shape; silence
  followed by a hit is worth more than a louder loop.
- **It sounds good on a phone speaker and on a TV.** A phone plays almost nothing under 300 Hz: every
  important sound needs energy between 500 Hz and 4 kHz (a knock on a thud, an upper harmonic on a
  bass). Measure it: `sound.mjs analyze` gives the loss through a phone-speaker curve.
- **Nothing clips** when many things happen at once: sounds share a bus that ends in a gentle limiter,
  and each sound is capped at a few voices (`sound.js` keeps four of a name and 24 in all).

## Levels that work

| what | level |
| --- | --- |
| music bed under play | -18 to -20 LUFS (`score --lufs -18`) |
| title or menu music | -14 LUFS |
| effects | the four classes: ui -20, small -16, normal -12, big -9 dB (loudest 50 ms) |
| a whole game while played | -16 to -12 LUFS measured off its output (the playtest's sound row) |

Duck the music for the moments that matter (`sound.duck(0.4, 0.5)` for a knockout or a line of
speech) instead of raising the effect.

## Repetition

- A sound heard many times a round needs **variants** (three takes a touch apart in pitch) and a
  little random pitch on each play; the same sample fired twenty times in a row reads as a machine gun.
- Signals the player must learn (start, win, lose, a warning) stay **the same every time**.
- A long session should not loop one 8-bar clip for ten minutes: make two or three sections and move
  between them with the game's state.

## Changing music with the game

- Every loop the same tempo and key; switch on the **next bar line**
  (`next = start + ceil((now - start) / bar) * bar` on the audio clock), which `sound.section()` does.
- Use the audio clock (`AudioContext.currentTime`), not timers, to schedule anything musical. A timer
  or a `requestAnimationFrame` pump skips beats it sees late, and a loaded machine makes it late: a
  bar counter that rides a pump lost three quarters of its sections under load while the audio
  itself played on. Work the bar out from the audio clock each time you need it.
- A live arrangement's position is `bar % total bars`: changing the total while it plays makes the
  playhead jump. Change the content of a section, not the arrangement's length.
- A section that plays once as an intro and a lap that repeats are different lengths: compute the lap
  from the repeating part only.
- A cue that names a sound that does not exist fails silently in most engines: check every name a
  cue or a section uses against what was loaded, once, at start.
- A gain, a bus or a send changed after a sound was wired may never reach the running graph (a loader
  that skips "already wired" sounds). Set levels before the first play, or rebuild the node.
- An `AudioContext` clock stalls while the machine is busy (a render, a capture), so a long set drifts
  from wall time: correct its start offset, never its cues.
- A module served from cache after a change runs the old code: version its URL (`?v=2`) when you
  change it on a live page.

## Events, not counts

When sounds follow a game's event list (hits, pickups), give each event a rising sequence number and
play every event newer than the last one played, in order. A list's length is not a signal: an
expired event replaced at the same length, or two events in one frame, are lost otherwise.

## Mixing effects into a running bed

Send one-shots (hits, chimes, slams) straight to the final bus, not through the music's filters: a hit
routed through a lowpass meant for the bed disappears into it. Bright noise belongs on the bright
one-shots only. Never raise the master to make hits stand out; lower the bed or duck it.

## Proving it

Scheduling a node is not proof that anything is audible. Three instruments, cheapest first:

1. `sound.mjs analyze <file>` on each asset: level, start, clipping, phone loss, and its picture.
2. The `playtest` skill's sound row: the game's real output copied off its graph while it is played;
   loudness, clipping, gaps, whether actions answer, whether music ever started.
3. An offline render of the game's own audio graph (`OfflineAudioContext` in headless Chrome) with a
   clock you can set: it finds NaN voices (a NaN anywhere silences the whole graph) and feedback loops
   that double their gain, without playing anything out loud. `currentTime` stays 0 offline, so give
   the game's audio a clock the render can drive.

## A log for a recorder

`sound.js` keeps a log of everything it schedules when a recorder asks for one, and only then: the
recorder sets `window.__homieSoundCapture = { events: [] }` before the page's scripts run, and each
`play`, each music loop, each stop, duck and fader move is pushed onto `events` with `performance.now()`
and what is needed to mix it again (the file's address, gain, playback rate, pan, loop, delay). The
head of `sound.js` lists the events. The `video` skill's `trailer` films the game frame by frame and
rebuilds its sound from that log and the game's own files. A game with audio code of its own can push
the same events, and only what is in the log is in the trailer's sound.

A visual check can never hear a game. Report numbers, and look at the spectrogram.
