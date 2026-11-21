---
name: model-split-screen
description: >-
  Make the "same prompt, two models" comparison video that every model launch produces (Claude Fable 5.2 vs
  Opus 5.5, Seedance vs Kling, Eevee vs Cycles): run one prompt twice under the same rules, log the real time
  and cost of each run, then lay the two results side by side (1920×1080) or stacked (1080×1920), started on
  the same frame, each with its name and its time and cost under it, optionally blind ("A" and "B" until the
  last seconds, then the reveal) and with a winner frame. scripts/split.py does the layout with ffmpeg and
  Pillow, so it works with an ffmpeg built without drawtext. Use when someone asks for a model comparison
  video, "Fable vs Opus", "same prompt two models", a side-by-side or split-screen comparison with cost and
  time, a blind "guess which one" test, or A/B of two renders or two edits. Not for a split screen inside a
  story edit (varg-video-edit-library), comparing many models in a grid of stills (gpt-image-2-6), or
  making the clips themselves (blender-code-film, code-game-trailer, varg-ai).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
compatibility: >-
  Python 3 with Pillow (`pip install pillow`), ffmpeg and ffprobe. A font: Inter Bold if installed, else Arial
  Bold (macOS) or DejaVu Sans Bold (Linux), or pass --font. A 9 s 1920×1080 split renders in under 2 s on an
  Apple Silicon Mac. The two clips come from anywhere; no key needed.
allowed-tools: Bash(python3:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# Same prompt, two models

Every model launch fills X with the same format: one prompt, two models, two results side by side, and
the bill under each. On Claude Fable 5.2's launch day (2026-11-09) it was the fifth biggest format, with 824k
views across 9 posts. Cost and minutes have become part of the caption:

- [@EnvolDev](https://x.com/EnvolDev/status/2119907318729245180), "Cathedral of Ice": Fable $81.10 in
  1 h 57 min vs Opus $45.97 in 3 h 11 min (291k views).
- [@MrTacticalX](https://x.com/MrTacticalX/status/2119955647542542439), a glass pool at sunset and at night:
  Fable 1 h 30 min, $57.87 vs Opus 68 min, $14.39 (172k views).
- [@kinderlayer](https://x.com/kinderlayer/status/2120112222227648957) ran it blind: "guess which one".

The comparison only means something when both runs had the same chance. Most of this skill is about the
runs, not the layout.

## 1. Ask first

1. **Which two**: two models (Fable 5.2 vs Opus 5.5), two video models (Seedance 2.5 vs Kling 4 on varg),
   two settings (effort low vs high), or two renders of one scene (Eevee vs Cycles).
2. **Frame**: side by side 1920×1080 for X and YouTube, stacked 1080×1920 for Reels, TikTok and Shorts.
3. **Open or blind**: names on screen from the start, or "A" and "B" with the reveal in the last 2–3 s.
4. **Winner frame**: none, or an orange frame around the one the person (not the agent) picks.

## 2. Run both under the same rules

- **One prompt, word for word**, saved to `prompt.txt` before the first run. No follow-up messages to one run
  that the other did not get. If a run needed a nudge, say so in its caption.
- **Same tools and skills** installed for both, same machine, same time limit, same output size and length.
- **Fresh session per run.** Neither run sees the other's output.
- **Log while it runs**, not from memory: start and end time, tokens and dollars from the usage report (Claude
  Code `/cost`, the API's usage, varg's `get_job_cost`), number of turns or retries. Write `runs.json`:

```json
{"prompt": "…", "left": {"name": "Claude Fable 5.2", "minutes": 117, "usd": 81.10, "nudges": 0},
 "right": {"name": "Claude Opus 5.5", "minutes": 191, "usd": 45.97, "nudges": 0}}
```

- **Same moment in both clips.** Trim each result to the same beat (the first frame where the scene is
  readable); the script then starts both on frame 1. A shorter clip holds its last frame.
- Keep both full results. People ask for them in the replies.

## 3. Lay them out

```bash
python3 scripts/split.py \
  --left fable.mp4  --left-name "Claude Fable 5.2" --left-stats "1 h 57 min · \$81.10" \
  --right opus.mp4  --right-name "Claude Opus 5.5" --right-stats "3 h 11 min · \$45.97" \
  --title "Same prompt, two models" --prompt "A cathedral of ice, a ship, a whale" -o split.mp4

# vertical, blind until the last 3 s, with a winner frame after the reveal
python3 scripts/split.py --layout stack --blind 3 --winner left … -o split-9x16.mp4
```

- The title band holds one short line and the prompt in quotes, shortened to fit (the full prompt goes in the
  post text or the first reply).
- Stats are the measured numbers from `runs.json`, in the same units on both sides.
- `--music bed.mp3` adds a bed cut to the film, faded out over the last second, at -14 LUFS. Keep it
  quiet or leave it out: people watch comparisons muted and pause on frames.
- `--duration 12` cuts both to 12 s; default is the longer clip.

## 4. Check before posting

- Pause on 3 frames: names under the right clips (swapped labels are the classic mistake), stats readable on a
  phone, nothing important cut by the panel crop.
- In blind mode, scrub to the reveal: the names must appear exactly when the "A"/"B" labels go.
- The caption repeats the numbers and says what was the same (prompt, tools, time limit) and what was not.
- No logos or brand marks in the title band unless they are the products being compared.

## 5. Post copy that has worked

- Lead with the surprise in numbers: "Fable took 1 h 57 min and $81; Opus took 3 h 11 min and $46. Same
  prompt."
- Put the full prompt in the first reply, and both full-length results in the second.
- For blind posts, ask one question ("which one is Fable?") and reveal in a reply after a few hours.

## Files

- `scripts/split.py`: the layout (side or stack, open or blind, winner frame, music bed). `--help` for flags.
- `examples/eevee-vs-cycles/`: this skill's own test, the same Blender scene (blender-code-film) rendered by
  Eevee and by Cycles, with measured seconds per frame.

Related: `blender-code-film`, `code-game-trailer`, `short-form-ffmpeg-cookbook` (crops and exports),
`varg-ai` (Seedance vs Kling on one key).
