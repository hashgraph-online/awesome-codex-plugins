# Lock sound and voice before picture

The full method (casting candidates, per-model voice tags, effects, music edits, a mix graded by script) is the
`video-sound` skill: https://github.com/vargHQ/skills/tree/main/video-sound . This page is the short version for
previs.

For any project with voice-over, dialogue or a song, the track is finished and approved before anchors, previz or
any video run. Pictures are then cut to it, never the other way round. Claude can time every frame and still cannot
hear one of them ("Claude can animate every frame of your motion video and still can't hear a single one of them",
https://x.com/Asteri_eth/status/2117629600901534024), so sound is written down as numbers it can check. One creator
cut the song first and built the picture to its beat (https://x.com/aicreataro/status/2108091976574988390).

Silent pieces (music added at the end, no lines) skip this step; still put the planned hits in `beats.json` if cuts
must land on them.

Output: `assets/audio.wav` (the locked mix or the locked VO/dialogue stem), `beats.json`, `lines.md`, and
`"song": "assets/audio.wav"` + `bpm` in `storyboard.json` so the previz plays against it.

## 1. Write the lines for the ear

If your AI characters sound fake, "the fix is almost always in how you write and DIRECT the dialogue"
(https://x.com/second_bassoon/status/2117307653320007954). Five fixes from that thread:

1. **Watch the punctuation.** Commas, full stops, dashes and ellipses are how the model paces a line; a missing full
   stop runs two thoughts together.
2. **Short lines with pauses on purpose.** Break a long line into two or three short ones and mark where the breath
   goes.
3. **Bodily actions as punctuation.** A sniffle, a swallow, a breath between lines ("the biggest improvement BY FAR").
4. **Anchor gestures.** Write a small action into the line's direction: "he lifts his finger as if to say 'one sec'".
5. **Split the generation in two.** Generate a long exchange as two shorter takes and join them, instead of one long
   take that drifts.

`lines.md`: one row per line with speaker, text exactly as sent, the direction (pause, breath, small action), and the
shot ids it plays over. On `eleven_v4`, audio tags such as `[whispers]` and `[laughs]` carry the direction
(`varg-ai/references/models.md`).

## 2. Audition 2-3 voices, the person picks

- Render the same 1-2 hardest lines in 2-3 voices (premade voice ids and models: `varg-ai/references/models.md`;
  `eleven_v4` is the expressive default, `eleven_v4_turbo` half the price, `gemini_3_8_flash_tts` does two-speaker
  dialogue). Estimate first; a typical line is tens of credits, so an audition costs little but is still spend:
  ask before running it.
- An audio-capable model (Claude has no audio input) or measurements may pre-screen more candidates and bring the best few (one agent "built a judge and tested the TTS model
  until it found a few candidates", https://x.com/LLMJunky/status/2106411941497389342), but **the person listens and
  picks**. Record the choice and the voice id in `brief.md`.
- Then render all lines in the chosen voice. Re-render only the lines that are wrong; keep approved takes.

## 3. The music

- The person's song: measure it (BPM, downbeats, sections, word timings). `varg-music-video`, if installed, does this
  in its "Measure the song" step and writes a `songmap.json` with the same fields as `beats.json` below.
- No song: generate a bed with an exact `duration` (`mureka_9_5` instrumental, or `eleven_music_v2_5` with vocals;
  `varg-ai/references/models.md`), state the BPM in the prompt, then measure what came back: the model's BPM is a
  request, not a fact.
- Mix VO over music only after both are approved; duck the bed under lines.

## 4. beats.json: every beat, every line, every hit

```json
{ "track": "assets/audio.wav", "duration": 30.0, "bpm": 120,
  "beats": [0.50, 1.00, 1.50], "downbeats": [0.50, 2.50, 4.50],
  "sections": [{ "name": "hook", "start": 0.0, "end": 3.0 }],
  "lines": [{ "id": "L01", "speaker": "A", "text": "One sec.", "start": 0.62, "end": 1.20 }],
  "pauses": [{ "after": "L01", "start": 1.20, "end": 1.65, "kind": "breath" }],
  "sfx": [{ "t": 4.50, "name": "door slam", "moment": "s03 cut", "shot": "s03" }] }
```

- Line starts and ends: transcribe the stem with word timestamps (the varg `transcription` tool, `whisper_large_v3`),
  then check pauses with `ffmpeg -i assets/audio.wav -af silencedetect=noise=-35dB:d=0.25 -f null -`.
- **SFX with timestamps, tied to a named moment** (a cut, a hit, a door). earshot
  (https://github.com/Leonxlnx/earshot) lands each effect within 5 ms of its named moment; a hit 80 ms after the
  cut already reads wrong. Place them by time, not by ear in a timeline.
- Look at the sound: `ffmpeg -i assets/audio.wav -lavfi showspectrumpic=s=1920x512 audio_spectrum.png` gives a picture
  Claude can read next to the frames (earshot does this as one sheet of frames + spectrogram).

## 5. Every cut lands on this track

- Re-time `storyboard.json` to `beats.json`: every shot `start` / `end` is a downbeat (song) or a line or pause
  boundary (VO, dialogue). A cut in the middle of a word is a bug.
- Lip-synced shots take their voice slices from the locked track (`references/seedance-v2v.md`); Seedance runs for
  these shots go out with `audio: false`.
- After the lock, a changed line is a re-time: update `lines.md`, `beats.json`, the storyboard and the previz in one
  pass, as with any director's note.
