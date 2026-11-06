---
name: video-sound
description: >-
  Make the sound of any video so it feels real: AI voices that don't sound fake (cast from candidates a person picks,
  directed with each model's documented tags), dialogue and narration written for the ear with pauses, breaths and
  small actions, sound effects on the right frame, music planned bar by bar with a quiet part, and a measured mix.
  Built from 480 sourced findings (Walter Murch, Randy Thom, Ben Burtt, trailer editors, NPR, voice directors, model
  docs, HyperFrames, earshot) plus paid tests. An agent can't hear, so every step writes numbers: a cue sheet, scripts
  that build and grade the mix (LUFS, true peak, voice over music, effects within a frame, cuts on the beat, dead
  air), a voice audition page and an audio LLM judge that shortlists takes. Use for "add sound", "voiceover", "sound
  design", "music for my video", "make the AI voice sound real", "pick the best take", "SFX", "mix", "launch video
  audio", "trailer sound", in HyperFrames, Remotion or AI films. Not for making a song as the product.
license: MIT
metadata:
  author: vargHQ
  version: "1.1.0"
  openclaw:
    requires:
      anyBins:
        - python3
        - ffmpeg
    homepage: https://github.com/vargHQ/skills/tree/main/video-sound
compatibility: >-
  Works in any agent with a shell. scripts/sound.py needs Python 3.9+ and ffmpeg (stdlib only); `beats` and `fit`
  need librosa (run them with `uv run --with librosa`). scripts/audition.py renders through the varg API
  (VARG_API_KEY) or scores takes made elsewhere. Generation on varg costs about $0.01-0.02 per voice line, $0.01-0.06
  per sound effect and $0.05 per 20 s music bed; mixing and checks are free.
allowed-tools: Bash(python3:*) Bash(ffmpeg:*) Bash(ffprobe:*) Bash(uv:*) Bash(curl:*) Read Write Edit
---

# Video sound

Picture gets the attention; sound decides whether it feels real. Agents make sound badly for three reasons: they
can't hear, they put an effect on every cut, and they let music bury the words. This skill fixes all three with a
plan written before picture, people's ears where taste is needed, and numbers everywhere else.

What the evidence says (full guide: https://claude.ai/artifact/Hw1EFJw4Xr86XcP8QpVt1V; sources in
`references/evidence.md`):

- **Pros use few effects.** In measured launch films about 85% of hard cuts have no sound of their own and there
  are about 2 whooshes per film (Cinetic); a strong accent lands on only 4-25% of cuts (earshot, 8 films).
- **Bare text makes a rushed voice.** Our test on `eleven_v4`: the bare line ran 231 words/min with a 0.36 s pause;
  punctuation took it to 207 and 0.51 s; breath and sniff tags to 194 and 0.92 s plus an exhale before the first
  word. 0 of 16 takes read a tag aloud; 16 of 16 kept every word.
- **Music models keep tempo, not structure.** 3 of 3 ElevenLabs Music takes held 120 BPM; 0 of 3 made the planned
  half-bar of silence and hit; 1 of 3 came back 29 s instead of 20. Ask the model for tempo, key, instruments and
  order; make stops, drops and the exact length in the edit.
- **Measure every effect.** 1 of 5 generated effects came back silent (a 1 s click peaking at -54 dBFS).
- **Designed vs plain, same lines, both at -14 LUFS:** the designed mix passed 8 of 8 checks; the plain one had the
  music 7 dB louder than the voice in the speech band, 3 of 4 cuts off the beat and 1.2 s of dead air.

## Rules

1. **Sound before picture.** Write the sound plan and record the voice first ("radio cut", Ken Burns' editor; Baby
   Driver started as a radio play). The voice's word times and the music's bar lines set the cuts.
2. **Every sound has a reason on screen and a time in `cues.json`.** No effect without a visible cause. Few and exact.
3. **Direct with each model's documented syntax** (`references/voice.md`), never with adjectives alone. Prompt
   behaviour, not emotion.
4. **Give lines room.** Fewer words per clip; keep the breath before a thought; hold after a key line.
5. **Music leaves room for words:** at least 10 dB under the voice in 300 Hz-4 kHz, ducked fast down and slow up.
6. **Room tone under everything.** Silence is a choice, used once or twice, eased into, never digital zero by accident.
7. **Measure, then ask a person to listen.** Scripts grade the mix; a person picks the voice and signs off the mix
   on headphones and a phone speaker. Never claim you heard something.
8. **Licences and consent.** Clone only voices you have the right to use; check music and sound licences
   (`references/music.md`, `references/sfx.md`).

## Files you produce

```
sound/brief.md       type, platform + loudness target, length, who speaks, music yes/no, budget
sound/plan.md        beat-by-beat sound plan: time | picture | voice | music | effects | ambience | silence
sound/lines.md       one row per line: id | who | text exactly as sent | direction | pause after | shot
sound/audition/      candidate takes + audition.html; the pick goes into brief.md
sound/vo/            approved line files + word timings
sound/music/         bed, beats.json, the fitted bed
sound/sfx/           one file per effect, measured
sound/cues.json      every sound with its time (format: references/cue-sheet.md)
sound/mix.wav        the master, mix_stems/, mix_report.json, check.json, sheet.png / preview.mp4
```

## Step by step

### 0. Brief

Fill `brief.md`. Pick the video type in `references/types.md` (launch, cinematic film, music video, trailer or ad,
UGC or talking character, narrated explainer or code demo): it says what leads (music, voice or the room), how much
music, how many effects and the signature move. Pick the platform: social and YouTube -14 LUFS, podcasts -16,
streaming speech -18, broadcast -23 or -24 (`references/mix.md`).

### 1. Sound plan (before any picture is generated)

If the `video-script` skill wrote `script.md`, start from it: its `spoken` column becomes `lines.md`, its `sound`
column seeds `plan.md`, and its `wpm:` line is replaced by the measured pace of the chosen voice. Write `plan.md`,
one row per beat of the video. For each music cue: start, stop, emotion, intensity, perspective and
"why this, why now?". Choose the 3-6 moments that get an accent (reveal, key action, logo) and the one silence.
At most 5 layers in any 5 s (Murch). **STOP** if the person has not seen the script: show `plan.md` and `lines.md`.

### 2. Lines for the ear

Write `lines.md` (`references/dialogue.md`): plain spoken words, one idea per sentence, contractions, round numbers,
sentences one breath long; cut every line the picture already says. Mark pauses, breaths and small actions with the
model's own tags. For two speakers, write them as one exchange with cut-offs (`—`) and interjections.

### 3. Cast: candidates, then a person picks

Characters already cast by the `character-passport` skill keep the voice in their `cast/<id>.md` voice block and its
approved take; audition only the voices still open (usually the narrator). Render the 1-2 hardest lines in 3-5 voices, 2 takes each (`references/voice.md` has casting notes, voice design
prompts and per-model syntax):

```bash
python3 scripts/audition.py plan sound/lines_hard.md sound/voices.json -o sound/audition/audition.json --takes 2
python3 scripts/audition.py render sound/audition/audition.json          # prints the price; --yes after approval
uv run --with librosa python3 scripts/audition.py score sound/audition/audition.json
python3 scripts/audition.py page sound/audition/audition.json -o sound/audition/audition.html
```

On varg an identical request returns the cached file for free: change the text slightly (a trailing space) for a
second take. With the varg MCP instead of a key, generate with `call_tool` (`tool: "speech"`, `wait: false`, then
`get_job`), put each file path in `audition.json` and run `score` and `page`. **STOP:** the person listens and picks.
Write the voice id, model and settings into `brief.md`.

Too many takes to play them all? Shortlist with an audio LLM judge, never pick with one (`references/judge.md`). A
vague "which is better?" judge picked the plain mix over the designed one every time in our test, and picked between
identical takes. Ask yes/no questions about one take at a time, let code decide, compare survivors two at a time in
both orders, and count only verdicts that agree: `python3 scripts/judge_takes.py prompt | check | make | tally`.

### 4. Record every line

Render all lines in the chosen voice. Transcribe each take with word timestamps and compare with the script: models
drop or invent words. Re-render only wrong lines. Keep quiet breaths; don't denoise or level natural sentence
declination (4-6 dB is normal speech). For generated films, decide per shot: keep native dialogue, or mute it and
lay the TTS line, then lip-sync with one clean voice (`references/dialogue.md`).

### 5. Music

Prompt with the five answers (genre, mood, instruments, tempo with BPM and key, era) and narrate the arrangement in
order ("start with just ... then bring in ..."). Instrumental under a voice; a bed that "feels incomplete". Then:

```bash
uv run --with librosa python3 scripts/sound.py beats sound/music/bed.mp3 -o sound/music/beats.json
uv run --with librosa python3 scripts/sound.py fit sound/music/bed.mp3 --to 30 -o sound/music/bed_fit.wav
```

Check the downbeats against where instruments enter (the tracker can be half a bar off). Snap picture cuts to the
grid (launch and music videos) or to the one or two big changes (story pieces). Make stops and drops in the edit:
cut the bed on a bar line and bring it back on a later downbeat (`references/music.md`).

### 6. Effects

List the on-screen events; give sounds only to the chosen ones (`references/sfx.md` has the table: clicks, typing,
pops, whooshes, the logo ending). Generate or retrieve one file per event and measure it
(`python3 scripts/sound.py measure sfx/x.wav`): a generated effect can come back silent or with a long lead-in.
Impacts and clicks align by onset; whooshes and risers by their peak (`"align": "peak"`).

### 7. Mix, check, look

```bash
python3 scripts/sound.py mix sound/cues.json -o sound/mix.wav
python3 scripts/sound.py check sound/mix.wav --cues sound/cues.json > sound/check.json   # exit 1 on a failure
python3 scripts/sound.py preview sound/mix.wav --cues sound/cues.json -o sound/preview.mp4
```

The mix ducks the music hardest in the voice band (lows 35%, 300 Hz-4 kHz 100%, highs 65% of `duck.depth_db`),
fades every clip edge, loops the room tone under everything and masters to the platform with an oversampled limiter.
Fix every failed check before showing anyone. Run the cheap-tells audit in `references/sfx.md`.

### 8. A person listens

**STOP:** share `preview.mp4` (and the muxed video). Ask for headphones and a phone speaker. Write their notes into
`plan.md`, fix, re-check. Then `python3 scripts/sound.py mux video.mp4 sound/mix.wav -o final.mp4`.

### Code videos and generated films

- **HyperFrames:** put the finished `mix.wav` on one audio track, or place stems as `<audio>` elements with volume
  automation; `npx hyperframes audio <file> --json` reports a file's peak. **Remotion:** one `<Audio>` per stem;
  size the composition to the voice with `calculateMetadata`.
- **Seedance, Kling, Veo:** prompt the sound you want (or "NO MUSIC ... only diegetic sound ... inside <>") and list
  the shot's sounds; Seedance 2.5 always outputs audio. Keep good native dialogue, rebuild music and effects in post.

## Never

An effect on every cut · the same sample machine-gunned · synth beeps for physical things · music with lyrics under
narration · music louder than words · a fade-out instead of a real ending · dead digital silence between lines ·
SSML `<break>` on Eleven v4/v3 · emotion adjectives instead of behaviour · naming an artist or song in a music prompt
· cloning a voice without consent · claiming you listened.

## Files in this skill

- `references/voice.md`: casting candidates, voice design prompts, exact tag syntax per TTS model, consistency, consent
- `references/dialogue.md`: writing for the ear, pauses, breaths, small actions, dialogue inside video models
- `references/sfx.md`: what gets a sound and when, layering, prompting effect models, licences, the cheap tells
- `references/music.md`: how much music, tempo and bars, prompting per model, editing to length, licences
- `references/mix.md`: loudness targets per platform, ducking, EQ, checks, what the views evidence says
- `references/types.md`: launch, cinematic film, music video, trailer or ad, UGC, narrated explainer
- `references/cue-sheet.md`: the `cues.json` format
- `references/judge.md`: ranking takes with an LLM judge without bias: the criteria and who checks each, our test, twelve rules, the prompts
- `references/evidence.md`: the tests and every sourced finding with its quote and link
- `references/goal-prompt.md`: the whole skill as one copy-paste prompt
- `scripts/sound.py`: measure, beats, fit, mix, check, sheet, preview, mux
- `scripts/audition.py`: voice candidates, rendered, measured and put on one page to pick from
- `scripts/judge_takes.py`: judge prompts, code verdicts on one take, blind pair files in both orders, a tally of agreeing wins
- `examples/launch-20s/`: the 20 s launch soundtrack from the tests (cue sheets, beat map, checks)
