---
name: sound
description: Make a game's sound effects and synthesized music on the creator's own computer, free, with no provider or account — a set of effects (jump, coin, hit, explosion, win, lose, UI) rendered from presets, a short synthesized theme or score from chords and patterns with stems and seamless section loops, a mix of any audio files and expressions — measured for loudness, clipping, late starts and what a phone speaker loses, then wired into the game with a small player that starts on the first touch and switches music on bar lines. Use when someone asks for sound effects, SFX, game audio, a chiptune or synth theme, background music without a paid service, music that changes with the game, or says a game is silent.
---

# Sound for a studio's game

Everything here runs on this computer with Node 22 and ffmpeg: nothing is sent anywhere and nothing
costs money. Sung songs and produced music from a model are the `music` skill (ElevenLabs, paid);
this skill is effects and synthesized music. They share the studio's `music/` folder and manifest, so
a synthesized theme gets a song page just like a rendered one.

One script: `scripts/sound.mjs` in this skill's folder (Claude Code:
`node "${CLAUDE_PLUGIN_ROOT}/skills/sound/scripts/sound.mjs" <command>`), run from inside the studio
(the folder with `studio.json`). Every command takes `--json`.

```sh
node <sound.mjs> check        # node, ffmpeg and its encoders, the studio and its games
node <sound.mjs> presets      # every effect preset, instrument, groove and pattern, one line each
```

No ffmpeg: offer `brew install ffmpeg` (macOS) or the system package; the person approves.
Finish in this turn: an effect set takes seconds, a one-minute score under a minute.

## 1. Effects

```sh
node <sound.mjs> sfx <set> --kit arcade --for-game <id>          # a kit: arcade, platformer, shooter, party, ui
node <sound.mjs> sfx <set> --only jump,coin,hit,win --style retro   # just these, crunchy 8-bit
node <sound.mjs> sfx <set> --spec music/<set>/effects.json        # your own list (below)
```

It writes `music/<set>/sfx/<name>-<n>.wav` and an Ogg copy of each, `music/<set>/sfx.json` (the
spec and every file's measured level), a reel to listen to (`<set>.mp3`) and its picture
(`<set>-reel.png`, a spectrogram over the waveform). **Open the picture and look**: a sound you
cannot hear is still a sound you can see. Then read the warnings; each one is something a person will
hear wrong, with the fix.

A spec is `{ "style": "clean", "variants": 3, "effects": [ { "name": "stomp", "preset": "land", "pitch": -3, "length": 1.2, "level": "big" } ] }`:
`preset` is any name from `presets` (the effect's name is used when it is one), `pitch` in
semitones, `length` a stretch, `seed` another take, `style` clean, retro or soft, `level` ui,
small, normal, big or a number in dB. Name effects after what happens in the game (`stomp`,
`gem`, `ko`), not after the preset.

- **Variants** (three by default) are the same recipe a touch higher or lower, so a sound heard fifty
  times a round does not machine-gun. Signals heard once a round (win, lose, go, countdown) get one take.
- **Levels** are set by the loudest 50 ms of each effect into four classes (ui -20, small -16,
  normal -12, big -9 dB), then held under -1 dBFS. The set sits together in a mix without balancing.
- **Every effect must start at once** (a hit that starts 30 ms late feels laggy) and **must reach a
  phone speaker**: under about 300 Hz a phone plays almost nothing, so a thud needs a knock on top.
  The warnings measure both.

## 2. A synthesized theme or score

Write `music/<slug>/score.json` (the full language, with a worked example: `references/SCORE.md`):
tempo, key, instruments (presets with a level, pan, echo in beats, reverb send, a duck under the
kick), sections in whole bars with chords and one pattern per instrument, an arrangement, and the
sections to loop. Then:

```sh
node <sound.mjs> score <slug> --spec music/<slug>/score.json --loops main,chase
```

- It renders the mix (-14 LUFS for a page; `--lufs -18` for a bed under a game's effects), the page
  mp3, a 24-bit master kept off the site, one stem per instrument plus the room (they sum to the
  mix), and **seamless loops** of the sections you name: each is rendered three times in a row and
  the middle copy kept, so reverb and echoes that ring over the loop point are already in its head.
  The report gives each loop's seam (1 or less is seamless) and its exact bar length. A loop over 1
  is in `warnings` and the summary says NOT SEAMLESS (`loopsSeamless: false`): an empty warnings
  list means the loops were checked and pass. The master's limiter is applied across the three
  copies, so a loud loop keeps its seam; nothing is faded at the loop point and no bar is shortened.
- `plan.json` holds the bar grid, so the `video` skill cuts a trailer on this music's bar lines.
- Look at `<slug>.png` and read the numbers: loudness, true peak, and what it measures through a phone
  speaker. Say them in your report, not adjectives.
- Write music a person would hum: a hook in the first bars, a clear melody over simple chords, a
  change every 4 or 8 bars. A score for a game is sections of the same tempo and key (calm, chase,
  final seconds) so the game can move between them on a bar line.

## 3. A mix of anything

```sh
node <sound.mjs> mix <slug> --spec music/<slug>/mix.json
```

Parts are audio files (a recording, a render, a loop), ffmpeg `aevalsrc` expressions (one, or two for
left and right), or effect presets, each placed (`at` seconds), levelled (`db`), panned, faded, repeated
and filtered with an ffmpeg `-af` chain. They are summed at exactly the levels written (no automatic
normalisation), limited, and brought to `master.lufs` if you give one. Expressions have traps that
fail silently: read `references/TRAPS.md` before writing one.

## 4. Into the game

```sh
node <sound.mjs> wire <set> <score slug> --game <id>
```

It copies the files into the game (`public/sound/`, or `sound/` for a static game), writes
`sound.json` (what exists) and `sound.js` (the player) and prints the two lines to add. Then, in the
game's code:

```js
import { createSound } from './sound.js';
const sound = createSound({ base: 'sound/' });
sound.music('<score slug>');                    // once, at the top: it starts on the first touch
sound.play('coin');                             // where the thing happens
sound.play('coin', { pitch: combo });           // a climbing combo; pan -1..1 for where it is
sound.section('chase');                         // the next loop, exactly on the next bar line
sound.duck(0.4, 0.5);                           // music down for a big hit
```

- **Sound starts on the first touch or key, with no "tap for sound" screen**: the player resumes audio
  inside the first gesture. A sound asked for before that is dropped, not queued.
- **Every browser plays its own sounds** for what it sees: call `play` where the each browser
  draw the event (a pickup that shows up in a snapshot, a hit that lands on screen), not only in the
  rules handlers. In a rules game emit a declared effect and play it from room.on in the view; the server has no speaker.
- Loops go out as Ogg with a WAV fallback (older Safari cannot decode Ogg): the player takes the first
  one the browser decodes. `wire` prints the real download size; keep a game's sound under about 3 MB.
- Each variant of an effect, and each loop, is a list of files tried in order (`["jump.ogg", "jump.wav"]`);
  a list of one file is fine.
- A trailer filmed frame by frame gets its sound from this player's own log of what it scheduled
  (off unless a recorder asks; `references/GAME-SOUND.md`, "A log for a recorder"): sound that goes
  through `sound.play` and `sound.music` is in the trailer, sound made any other way is not.
- Rules for game sound (every action answers, what repeats, music under effects, intensity changes on
  bar lines, the live-loop traps): `references/GAME-SOUND.md`.
- For sound made live in the browser (a synth voice per player, pitch that follows speed, a beat
  clock), the open engine package `@homie-rocks/audio` has the building blocks; install it exactly
  pinned (`npm install --save-exact @homie-rocks/audio@0.1.0`).

## 5. Prove it, and publish it

Build, run the game, and let the `playtest` skill's sound row listen: it copies what the game really
sends to the speaker while it is played, and says how loud it is, whether it clips, what a phone loses,
whether actions answer with a sound, and whether the music ever started. Never say a game "has sound"
from the code alone.

```sh
node <sound.mjs> add <slug> --title "<Title>" --blurb "<one line>" [--for-game <id>] --publish
node <sound.mjs> publish <slug>        # rebuild and redeploy the site; the page answers 200
```

An effect set gets a page with its reel and every effect to download; a score gets its player, its
loops and its stems. The credits line says they were synthesized from code (no samples, no model).
Commit `music/<slug>/` specs and the manifest; the audio files stay out of git (the studio's
`.gitignore`) and regenerate from the spec, byte for byte.

## Tell the person

The page or the game, what was made (how many effects, the theme's length and bars), the loudness
numbers, the warnings you fixed and any you did not, and that it cost nothing.

## Never

- Never ship a sound you have not measured and looked at.
- Never use a mp3 for an effect or a loop: encoders pad the start with silence (a late hit) and the
  ends (a gap at the loop). WAV or Ogg.
- Never imitate a real song, artist or brand jingle.
