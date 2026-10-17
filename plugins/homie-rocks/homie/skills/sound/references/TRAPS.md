# Traps: ffmpeg, expressions and synthesis

Each of these produced silence, the wrong level or a click while every command exited 0.

## ffmpeg

- **Exit code 0 is not audio.** A graph that failed part-way still writes a file whose header promises
  sound. Read it back: `ffprobe -v error -show_entries format=duration:stream=sample_rate,channels -of json <file>`,
  and measure it (`sound.mjs analyze`). A duration of 0, or one far from what you asked for, is a
  failed render with the right name.
- **`c=2` on a source makes one channel.** `aevalsrc` and friends want a layout name (`c=stereo`,
  `c=mono`) or `2c`; a bare number is read as a channel mask. Ask for the count on the output
  (`-ac 2 -ar 48000`) and the source cannot be wrong about it.
- **`amix` divides by the number of inputs** unless `normalize=0`: the levels you asked for never
  arrive and nothing says so. (`sound.mjs mix` sums in JavaScript at the levels written.)
- **`adelay` takes one value per channel** (`adelay=500|500`); a single value delays the left channel only.
- **mp3 pads both ends with silence**: an effect starts late and a loop gaps at the wrap. Effects and
  loops are WAV or Ogg; mp3 is for a page's player only.
- **`<audio loop>` gaps at the wrap** in every browser: loop a decoded buffer in Web Audio
  (`source.loop = true`).
- There may be no `drawtext` in the user's ffmpeg build (it needs freetype): draw labels in a browser
  or an image instead.
- `loudnorm` needs 400 ms blocks: integrated LUFS of a 0.2 s effect is meaningless. Level short
  effects by their loudest 50 ms (what `sound.mjs` does).
- Encoders differ: many ffmpeg builds have no `libvorbis`; `libopus` in an `.ogg` is the fallback.
  Older Safari cannot decode Ogg at all, so ship a WAV beside it.

## aevalsrc expressions

- **No comparison operators.** `t>=1` fails with a misleading "Missing ')'". Use `gte(t,1)`,
  `lte()`, `gt()`, `lt()`, `between(t,a,b)`. There is no `sqr()`: `pow(x,2)`.
- **`0*inf` is NaN and a NaN silences the whole sum.** An envelope like `exp(-(t-a)*k)*gte(t,a)`
  overflows before the gate: write `exp(-max(0,t-a)*k)`.
- **`random(x)` keeps its state in variable slot x** and overwrites it; put every `random` in one slot
  (9) and keep `st()/ld()` state in 0..7. There is one random stream: to decorrelate a right channel,
  advance it (`0*random(9)+…`). The first use of a slot must be its `st()`.
- Quotes, backslashes, semicolons and brackets belong to ffmpeg's graph parser, not the expression;
  keep expressions to arithmetic and functions. Very long expressions (a few thousand characters)
  are fragile: split the terms across parts, they sum to the same thing.
- `PI` may be missing: write `6.28318` for 2π.
- One expression renders mono; two (left, right) render true stereo.

## Pitch and phase

- **In `synth.mjs` a number is hertz, always.** `freq: 110` is 110 Hz and `slide.to: 45` is 45 Hz.
  A note is a name (`freq: "A2"`) or a MIDI number said out loud (`midi: 45`, `slide.toMidi: 45`,
  or `hzOfMidi(45)`). There is no guessing by size: a number of 127 or less used to be read as a
  MIDI note, and every bass note is a frequency under 127 Hz, so a 110 Hz bass came out at 4.7 kHz.
- **A pitch bend is a change of frequency, integrated into phase.** `sin(2*PI*f(t)*t)` with a
  changing `f` sweeps at twice the intended rate and runs backwards on the way down; the phase must be
  the integral of the frequency (what `synth.mjs` does every sample). A scoop from below in closed
  form is `+2π·df·τ·exp(-(t-a)/τ)` added to the phase.
- Vibrato depth scales with pitch: ±0.4% of the frequency is about ±7 cents at any note.
- A tremolo on one note is one voice whose envelope clock wraps (`mod(max(0,t-a)*rate,1)/rate`),
  with the phase left running; restarting the phase each time clicks.
- An uneven pulse wave (duty other than 50%) has a DC offset: subtract `2·duty - 1`, or high-pass the
  result, or it clicks at every start and stop.

## Loops and width

- **A held sound loops without a click only if every frequency in it, beating pairs included, is a
  whole multiple of 1/loop-length** (0.125 Hz for an 8 s loop) and no channel starts at a phase
  offset. Notes whose envelope closes before the loop point are exempt. Or render the section three
  times and keep the middle (what `sound.mjs score` does).
- **Limit a loop before cutting it, not after.** A limiter run over the cut loop starts at full gain
  and ends wherever the last bar left it: a step of gain at the wrap. `score` limits across the
  three copies. A note, an echo or a reverb longer than the whole section still cannot repeat: the
  seam goes over 1 and the report warns; make the section longer or the tail shorter.
- **A 1-3 ms delay between channels widens a transient but cancels a held tone** in mono (a phone
  speaker folds to mono): correlation fell to -0.2 and the note lost 4 dB. Widen held sounds by
  detuning or by panning different notes, never by a channel offset; offset only the attacks.
- Measure width with the stereo correlation and the mono loss (`analyze` gives both). Negative
  correlation means parts cancel on a phone.

## Levels

- A struck sound (a pluck, a bell, a mallet) sits about 9 dB RMS under a held one at the same peak.
  Lengthen its decay rather than raising its fader, then compare stems with their gains applied.
- A generated room tone or ambience can carry a steady hum (a narrow line in the spectrum): `analyze`
  lists narrow tones; notch them or regenerate. Each one comes with `prominenceDb` (over its
  neighbours, which a filter does not change: the neighbours fall with it), `levelDb` (how loud it
  is, dBFS), `energyShare` and `presentShare` (the share of the file it is there). Only a tone that
  is prominent, above -60 dBFS and there 60% of the time or more is called steady; a melody's brief
  high partial is listed and not warned about. Read its level and share to judge it.
- Check every render at its head and tail as well as its peak: silence at the start of an effect is
  latency; a tail cut mid-ring is a click.

## Provider renders (when a model made the audio)

- A paid render can land minutes after the command that asked for it timed out or failed. Before
  asking again, list the output folder by time: the same request twice is twice the bill.
- Before cutting a straight loop out of a swung track, find the onsets in the rendered file: a hit a
  few ms early is a musical flam, not an error, and triplet grids suit a shuffle.
