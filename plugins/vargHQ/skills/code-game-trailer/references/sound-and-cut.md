# Sound, the cut and the deliverables

## The beat grid comes first

Pick the tempo before the shots: every shot length is a whole number of beats, so every cut lands on
a beat. At 100 BPM a beat is 0.6 s and a bar 2.4 s. The example: 5 + 5 + 3 + 4 + 2 + 5 + 4 + 3 = 31
beats = 18.6 s. Odd shot lengths (3 or 5 beats) keep it from feeling mechanical.

## Option A: score.ts (free, written in code)

`bun scripts/score.ts director.json` reads the director (bpm, roles) and `capture/manifest.json`
(frame counts and game events) and writes two 48 kHz WAVs beside the director:

- `music.wav`: an i-VI-III-VII pad (Am F C G in A; `--key` moves it) with a one-pole filter that opens in
  `escalation`/`hero`; a sine bass; kicks on `mechanic` beats, kicks + hats on `escalation`; a 4-beat
  noise riser that lands on the hero shot's first `gate` event (or its first frame); a boom on that event
  and on the first frame of `title`; Schroeder reverb on pads and impacts.
- `sfx.wav`: per `spark` a pentatonic chime that climbs with the chain, per `gate` a whoosh, a chord and
  a boom, per `hit` a thud, anything else a tick. Times are `shot start + frame / fps`, the same arithmetic
  `cut.ts` uses, so sounds sit on the frame where the event happened (slow-motion shots included).

It takes under a second for 18.6 s. It sounds like a competent temp score, not a composer.

## Option B: a varg track

1. Price it: `estimate_cost({ "tool": "music", "input": { "model": "mureka_9_5", "prompt": "…", "duration": 20 } })`
   and quote the price in dollars to the person paying. Generate only after a yes.
2. `generate_music({ "model": "mureka_9_5", "prompt": "dark cinematic game trailer bed, 100 BPM, low
   drone, soft pulse building to driving drums, riser into one big hit at 0:11, then a held chord,
   instrumental, no vocals", "duration": 20, "instrumental": true })`. Always pass `model` and
   `duration`: the tool's default model is far more expensive (the `varg-ai` skill lists mureka_9_5 at
   ~25 credits and eleven_music_v2_5 at ~158), and without `duration` music runs long.
3. `bun scripts/beats.ts music.mp3` → BPM and the first beat. Put `"bpm"` and
   `"music": { "file": "music.mp3", "offset": <first beat> }` in the director and re-time shots in beats.
   Measured on the score.ts bed: 99.79 BPM for 100, first beat 0.572 s against a grid at 0.6 s.
4. Keep `sfx.wav` from score.ts for the game sounds: `cut.ts --music music.mp3 --sfx sfx.wav`.

A model rarely hits a requested time exactly ("hit at 0:11"): after `beats.ts`, look at the strong
onsets it lists and move the hero shot to the nearest big one.

## cut.ts, step by step

1. One image-sequence input per shot, in director order; per-shot `fade` filters (`fade_in`,
   `fade_out` from/to black, `flash_in` from white).
2. `concat`, then `--grade`: `eq=contrast=1.04:saturation=1.06,vignette=angle=PI/5`. `--grain N` adds
   temporal grain: it hides banding but cost 209 MB for 18.6 s at crf 16 (vs 19 MB without, crf 18).
   At crf 18 the near-black sky showed no banding even with a 3x level stretch, so grain is off by default.
3. Sound: music (from `offset`) + sfx mixed with `amix normalize=0`, trimmed/padded to the picture,
   0.8 s fade at the end, then two-pass `loudnorm` (measure, then apply `measured_*` with `linear=true`)
   to -14 LUFS integrated and -1.5 dBTP. At -1 dBTP the AAC file measured -0.7 dBFS true peak.
4. H.264 high, crf 18, preset slow, yuv420p, `+faststart`; AAC 192k. 18.6 s cut in 9.7 s on an M4 Pro.

## Previews and cut-downs

Gallery preview (1280x720, 6-10 s, 0.4-2 MB):

```bash
ffmpeg -ss 11.4 -i master.mp4 -t 6.6 -vf scale=1280:-2:flags=lanczos -c:v libx264 -preset slow -crf 20 \
  -pix_fmt yuv420p -an -movflags +faststart preview.mp4
```

Measure before choosing the window; at these settings the example's shots cost (KB per second):

| s1 crane | s2 HUD | s3 skim | s4 ember storm | s5 fly-by | s6 gate | s7 title | s8 end card |
|---|---|---|---|---|---|---|---|
| 238 | 379 | 485 | 721 | 545 | 364 | 278 | 86 |

An 8.8 s window over the storm came out at 4.1 MB; the 6.6 s gate + title + end card window at 1.88 MB.
Keep titles and HUD at least 64 px from the left and right edges (the example's HUD sits at 6.5vh = 70 px).

Vertical cut-downs (9:16) for TikTok/Reels/Shorts: capture again at `--size 1080x1920` with cameras
re-framed for the tall frame rather than cropping the 16:9 master (not tested in this build: the HUD and
card use vh units, so they scale, but every camera needs a new look); see `short-form-ffmpeg-cookbook`.

## check.ts: what the numbers mean

| line | good | if not |
|---|---|---|
| `dup` per gameplay shot | 0 | something moves on a clock the virtual clock does not see, or the game paused |
| `frozen` on cards | < 1.2 s | keep something alive on cards (the embers in `card.html`) |
| `black` | 0 outside fades | captured before the first render; set `ready` after the first frame |
| `motion` | 2-10 for gameplay | > 25: strobing or a cut inside a shot |
| loudness | -14 ±1 LUFS, peak ≤ -1 dBFS | re-run cut.ts; `--tp -2` if the peak is still high |
| text | only your game's words | debug words, franchise names, claims without proof are flagged |

The example's final run: 0 duplicates and 0 black frames in all gameplay shots, -13.7 LUFS, -1.4 dBFS
true peak, 1920x1080 30 fps H.264 + AAC, no warnings. Then look at the sheet: the first sheet of this
example passed every number and still showed a three-second opening in which the hero never entered
the frame.
