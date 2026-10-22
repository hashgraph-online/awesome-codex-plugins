# The score language

A score is JSON: tempo and key, instruments, sections in whole bars, an arrangement. `sound.mjs
score` renders it the same way every time (every random choice is seeded), so the score IS the
music: commit it, and the audio regenerates byte for byte.

## A worked example (48 s, three sections, two loops)

```json
{
  "title": "Night Market Theme",
  "bpm": 128, "key": "A minor", "beatsPerBar": 4, "stepsPerBeat": 4, "swing": 0,
  "instruments": {
    "lead":  { "preset": "pulse-lead", "db": -9,  "pan": 0.1, "stepsPerBeat": 2, "echo": { "beats": 0.75, "feedback": 0.3, "mix": 0.2 }, "reverb": 0.15 },
    "arp":   { "preset": "pluck",      "db": -15, "pan": -0.35, "reverb": 0.2 },
    "bass":  { "preset": "saw-bass",   "db": -10, "duck": 0.35, "reverb": 0 },
    "pad":   { "preset": "pad",        "db": -17, "duck": 0.5, "reverb": 0.3 },
    "drums": { "preset": "kit",        "db": -7,  "reverb": 0.05 }
  },
  "sections": [
    { "name": "intro", "bars": 4, "chords": "Am F C G",
      "play": { "pad": "chords", "arp": "arp:16", "drums": "hats" } },
    { "name": "main", "bars": 8, "chords": "Am F C G",
      "play": {
        "lead": "A4 . C5 . E5 - D5 C5 | B4 . G4 . B4*2 C5 D5 | E5 - . C5 A4 . C5 D5 | E5*3 . G5*2 E5*2 | F5 . E5 D5 C5 - A4 . | C5 . B4 . A4*2 G4*2 | A4 . C5 . E5 . A5 - | G5*4 E5*4",
        "bass": "root8", "pad": "chords", "arp": "arp:16", "drums": "four" } },
    { "name": "chase", "bars": 4, "chords": "Dm E Am Am",
      "play": {
        "lead": { "notes": "D5 E5 F5 A5 | G#5*2 E5*2 | A5 E5 C5 A4 | E5*4", "stepsPerBeat": 1 },
        "bass": "pulse", "arp": "arp-updown:16", "drums": "break+fill" } }
  ],
  "arrangement": ["intro", "main", "chase", "main"],
  "loops": ["main", "chase"],
  "master": { "lufs": -14 }
}
```

## The top

| field | meaning |
| --- | --- |
| `bpm` | 40 to 240 |
| `beatsPerBar` | 4 by default (3 for a waltz) |
| `stepsPerBeat` | the grid of a notes pattern: 4 = sixteenth notes (default), 2 = eighths, 1 = quarters. An instrument or a single pattern can set its own |
| `swing` | 0 to 0.5: every second step comes that fraction of a step late (0.2 to 0.33 is a shuffle) |
| `arrangement` | section names in playing order; a section can repeat. Default: the sections in order |
| `loops` | sections to render as seamless loops for the game (`--loops` overrides; `all` for every one) |
| `master.lufs` | -14 for a page or a trailer, -18 to -20 for a bed under game effects (`--lufs` overrides) |
| `room` | the shared reverb's size, 0 to 1 (0.55 by default) |

## Instruments

`{ "preset", "db", "pan", "octave", "legato", "echo", "reverb", "duck", "stepsPerBeat", "tone" }`

- `db` the level (-10 by default). Start the lead around -9, drums -7, bass -10, pads -17, and move
  one at a time while listening to the numbers (`analyze` a stem).
- `pan` -1 (left) to 1 (right). Keep the bass and kick in the middle.
- `octave` shifts every note of the instrument by octaves.
- `legato` how much of each step a note holds (0.92 by default; 0.5 is staccato).
- `echo` `{ beats, feedback, mix, pingpong }`: a tempo-synced echo (0.75 beats is the dotted eighth).
- `reverb` the send to the shared room, 0 to 1.
- `duck` 0 to 0.95: the instrument dips on every kick and comes back within half a beat (the pump
  that makes a pad breathe with the drums). Only when the section has a kick.
- `tone` (drums) shifts the kit's pitch in semitones.

Presets (`sound.mjs presets` lists them with what each is for): leads `pulse-lead`, `square-lead`,
`saw-lead`, `soft-lead`, `bell`; keys `epiano`, `pluck`, `organ`; pads `pad`, `warm-pad`; basses
`saw-bass`, `square-bass`, `triangle-bass`, `sub-bass`; drums `kit`, `chip-kit`.

## Chords

`"chords": "Am F C G"` is one chord a bar, repeated to fill the section. With bars marked,
`"Am F | C G | Dm | E7"` puts two chords in a bar when you write two. Qualities: major (`C`),
`m`, `7`, `maj7`, `m7`, `m9`, `9`, `add9`, `6`, `m6`, `5`, `dim`, `dim7`, `m7b5`, `aug`, `sus2`,
`sus4`, `7sus4`; a slash puts another note in the bass (`C/E`). Sharps and flats: `F#m`, `Bb`.

## Patterns

A pattern is either generated from the chords, or written note by note.

**From the chords**: `root` (the root held for the chord), `root8` (eighth-note roots; `root8:16`
for sixteenths), `pulse` (sixteenth-note roots, a driving bass), `octaves` (root and its octave in
turn), `chords` (the chord held: a pad), `stabs` (short chords on the off-beats), `arp`, `arp-down`,
`arp-updown` (the chord's notes one at a time; `:16` sixteenths by default, `:8` eighths). The bass
plays low, pads in the middle, arpeggios an octave up; `octave` moves any of them.

**Notes**: one token per step of the pattern's grid.

| token | meaning |
| --- | --- |
| `A4`, `C#5`, `Bb3` | a note (A4 = 440 Hz; octaves change at C) |
| `.` | a rest |
| `-` | hold the previous note one more step |
| `A4*3`, `.*4` | a note or rest lasting 3 (or 4) steps |
| `[A3 C4 E4]` | a chord |
| `A4!` | an accent (louder); with a length: `A4!*2` |
| a vertical bar | a bar line: optional, but when you write them every bar must be full, which catches a miscounted bar |

A pattern shorter than its section repeats (a one-bar riff over eight bars). With the default grid a
bar of 4/4 is 16 tokens; for a melody in eighth notes give the instrument `"stepsPerBeat": 2` (8
tokens a bar), and a single section can differ with `{ "notes": "…", "stepsPerBeat": 1 }`.

**Drums**: a groove by name, `four` (four on the floor), `backbeat`, `half` (half-time), `break`,
`shuffle`, `hats`, `pulse` (kick only), `none`; `+fill` puts a snare and tom fill in the section's last
bar (`"break+fill"`). Or write the bar yourself, one line per drum, `x` a hit, `X` an accent, `.`
nothing, 16 cells a bar in 4/4 (the line repeats every bar):

```json
"drums": { "kick": "x.....x...x.....", "snare": "....x.......x...", "hat": "x.x.x.x.x.x.x.x.", "openhat": "..............x.", "fill": true }
```

Drums: `kick`, `snare`, `clap`, `hat`, `openhat`, `tom`, `rim`, `shaker`.

## What makes it good

- **A hook in the first bars.** The main melody should be singable: mostly steps, one leap, a note
  held at the end of a phrase. Repeat it; change the last bar of the repeat.
- **Contrast between sections**: the calm section drops the drums or the bass; the chase doubles
  the bass rhythm and adds the break; the final seconds go up a key or add the open hat.
- **Space for the game's effects.** A bed at -18 LUFS with the lead an octave away from the effects'
  range; `duck` the pad and bass under the kick, and `sound.duck()` the music for big hits.
- **Loops in 4 or 8 bars**, every loop the same tempo and key, so the game can switch on a bar line.
- Listen with numbers: `analyze` each stem; a stem more than 12 dB under its neighbours is inaudible
  in the mix, and a struck sound (a pluck, a bell) sits about 9 dB under a held one at the same peak,
  so lengthen its decay instead of pushing its level.

## Errors that name the fix

A bar with the wrong number of steps, an unknown chord quality, a section that plays an instrument not
in `instruments`, an arrangement naming a missing section: each stops the render with a sentence
saying what and where. Fix that and render again; a render is free.
