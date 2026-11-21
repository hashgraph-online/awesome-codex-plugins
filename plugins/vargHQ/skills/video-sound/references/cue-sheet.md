# cues.json: the soundtrack as data

One file holds every sound in the video with its time. `scripts/sound.py mix` builds the mix from it,
`sound.py check` grades the mix against it, `sound.py sheet` draws it. Times are seconds from the first frame.

```json
{
  "duration": 20.0,
  "fps": 30,
  "platform": "youtube",
  "target": { "lufs": -14, "true_peak": -1.0 },
  "duck": { "depth_db": 10, "ramp": 0.25 },
  "checks": { "voice_over_music_db": 10 },
  "beats": "beats.json",
  "cut_on": "beats",
  "cuts": [2.0, 4.0, 8.0, 12.5, 16.0],
  "silences": [ { "start": 12.0, "end": 12.5, "why": "half a bar of nothing before the logo hit" } ],
  "tracks": [
    { "id": "L01",  "role": "voice",    "file": "vo/L01.wav",   "start": 0.6 },
    { "id": "L02",  "role": "voice",    "file": "vo/L02.wav",   "start": 8.4, "gain_db": 1.5 },
    { "id": "bed",  "role": "music",    "file": "music/bed_fit.wav", "start": 0, "gain_db": -8,
      "fade_in": 0.3, "fade_out": 1.5, "length": 20 },
    { "id": "room", "role": "ambience", "file": "sfx/room.wav", "start": 0, "loop": true, "gain_db": -26 },
    { "id": "whoosh", "role": "sfx", "file": "sfx/whoosh.wav", "start": 11.55, "at": 12.5,
      "trim_lead": false, "moment": "logo slams in; whoosh peaks on the hit" },
    { "id": "hit",  "role": "sfx",      "file": "sfx/hit.wav",  "start": 12.5, "moment": "logo lands" },
    { "id": "click", "role": "sfx",     "file": "sfx/click.wav", "start": 4.0, "gain_db": -6, "moment": "cursor clicks Export" }
  ]
}
```

## Fields

| field | meaning |
|---|---|
| `duration` | the video length in seconds; the mix is padded or cut to exactly this |
| `fps` | frame rate; "on time" means within one frame (33 ms at 30 fps) |
| `platform` | `youtube`, `tiktok`, `reels`, `x` (-14 LUFS), `web`, `podcast` (-16), `broadcast` (-23); all -1 dBTP |
| `target` | overrides the platform's LUFS and true peak |
| `duck.depth_db` | how far the music drops while anyone speaks (dB); `ramp` = seconds to get there and back |
| `checks.voice_over_music_db` | the minimum gap between voice and music during every line (default 10 dB) |
| `beats` | path to the `sound.py beats` output, or the object itself |
| `cut_on` | `beats` or `downbeats`: which grid the `cuts` must land on |
| `cuts` | the picture's cut times, copied from the edit (HyperFrames / Remotion timeline) |
| `silences` | planned silence; `check` will not flag these as dead air |
| `tracks[].role` | `voice`, `music`, `sfx` or `ambience`; voice drives ducking; ambience usually loops |
| `tracks[].start` | where the file starts on the timeline |
| `tracks[].at` | the moment the sound belongs to (defaults to `start`); `check` compares the real onset with it |
| `tracks[].trim_lead` | sfx only, default true: cut the file's own silent lead-in so the sound starts at `start` |
| `tracks[].trim_start`, `length` | use a slice of the file |
| `tracks[].gain_db`, `fade_in`, `fade_out`, `loop` | level and shape of the cue |
| `tracks[].moment` | free text: what happens on screen. Keeps the sound tied to a reason |

## Why a whoosh has `trim_lead: false` and an earlier `start`

A whoosh or riser builds toward its peak. Line up its loudest point, not its first sample, with the event:
`start = event - time_of_peak_in_file`. `sound.py measure whoosh.wav` and the sheet show where the peak is.
Impacts, clicks and pops start at their onset, so leave `trim_lead` on and set `start` to the event.

## Where the times come from

- Cuts and on-screen events: the composition (HyperFrames `data-start`, Remotion `from` / `durationInFrames`).
- Voice line starts: the voice-over plan; real word times from a transcript with word timestamps.
- Beats: `sound.py beats music.wav -o beats.json`.
