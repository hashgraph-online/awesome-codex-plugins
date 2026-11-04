---
name: media-judge
description: >-
  Judge a finished AI-made video, image or track by measuring it, then rank takes on the defects found. One command
  reads every frame and writes facts with timestamps and evidence: broken frames, banding after a simulated X or
  YouTube upload, numbers that jiggle, spelling, too much on screen, nothing leading the eye, motion with no cause,
  pinned graphics, sliding labels, a face, outfit or light that changed, sound after the cut, loudness, voice against
  the script, and distance to references against the template. A fresh agent settles only what eyes can settle. No
  score out of 10. Use when someone says "review this video", "check my render", "self-review", "QA", "judge",
  "critique", "score these takes", "pick the best take", "does it match the reference", "it looks like a template",
  "is it ready to post", "reverse engineer this reel", or after any agent finishes a film, short drama, reel or ad.
  Not for making or repairing media (varg-ai, varg-video-editing) or ad law (ai-ad-compliance-check).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      bins:
        - ffmpeg
        - ffprobe
        - uv
    homepage: https://github.com/vargHQ/skills/tree/main/media-judge
compatibility: >-
  Needs ffmpeg built with libvmaf (the banding test; brew's build has it) and uv, which installs OpenCV, NumPy, RapidOCR
  and a spell checker on first run. Runs on a laptop CPU with no API key and no credits. Downloads two small OpenCV
  face models from Hugging Face on first use. Voice against a script needs faster-whisper (uv run --with faster-whisper).
allowed-tools: Bash(uv:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write
---

# Media judge

**Measure, don't grade.** A judgment here is a time, a number and a picture. "Looks great", "8/10" and "feels premium"
are not findings, and neither is any adjective with no measurement behind it.

Code finds the moment and a fresh pair of eyes reads only that moment, in that order, because the other way round fails:
12 vision models scored at most 54.1% on spotting temporal glitches; Claude Opus caught 17.5% of them, Gemini 3 Flash
said "glitch" to about 87% of clean clips ([TempGlitch](https://arxiv.org/abs/2605.21443), gameplay clips). Uniform sampling
at 0.5 fps caught 11.81% of faults under 0.2 s ([SynFlash](https://arxiv.org/abs/2603.17374)), and GPT-4 preferred its own
output 0.705 and 0.912 of the time on tasks where people saw equal quality ([Panickssery et al.](https://arxiv.org/abs/2404.13076)). So:

1. **Facts:** `judge.py` reads every frame and every sample. It does not sample.
2. **Eyes:** a fresh agent opens only the evidence and answers narrow questions.
3. **Verdict:** counted defects. Ranking follows from the counts, never from a feeling.

**What this has been tested on.** Planted defects in footage it never saw while being tuned: 18 of 22 caught, 6 of 8 clean controls (25 of 25 and 10 of 10 on the footage it was tuned on). In a blind test on 19 anonymous clips, an agent with this skill found 12 of 14 planted defects, with no false claims on clean clips, using 116k tokens. An agent given only the failure list found 11 of 14, using 197k tokens, and reported the banding without an upload test. So the list itself does a lot. This adds repeatable numbers, the upload test, and fewer tokens. Both missed a face swap they weren't told to look for, so use `--one-character`.

## 1. Who judges

If you made this media, you do not judge it in this context. Start a fresh agent with no knowledge of the prompts or
of how it was made, and give it only the file, this skill, the brief (what it must say, names, product) and the
references. If you cannot start one, write `self-judged` at the top of the verdict.

## 2. Run the measurements

```bash
uv run scripts/judge.py video film.mp4 --out runs/film \
  --allow "varg,Seedance"          # brand and product names for the spell check
```

Takes about a minute for a 12 s clip and about 5 minutes for a 47 s 1080p film on a busy laptop. Add what you know, because each flag
turns a report into a test:

| Flag | Use it when | What it turns on |
|---|---|---|
| `--one-character` | the brief says one person, or the same person across shots | face changes become flags. Without it a swap is only a number in `neighbour_pairs`, and a blind run of this skill missed one that way |
| `--groups '[[0,1,2],[5,6]]'` | these shots share one scene | outfit and light jumps become flags |
| `--expected lines.txt` | you know the on-screen text | every line must appear |
| `--script voice.txt` | there is a voice-over | word error rate, with `--with faster-whisper` |
| `--refs ref.mp4` | it copies a reference | pair sheet and distance per shot |
| `--template tpl.mp4` | it was built from a template | margin: closer to references or to template |
| `--labels labels.json` | you have the render's anchors | exact label drift against its target |
| `--platform x\|youtube\|reels\|tiktok\|shorts` | you know where it goes | upload simulation and safe zones |
| `--size 1080x1920` | a size was requested | size becomes a blocker |
| `--music-only` | no voice in the piece | skips voice tests |

Images and tracks: `judge.py image poster.png --out runs/poster [--ref ref.png]` and `judge.py audio track.mp3 --out runs/track`.

Exit code 0 means nothing was flagged, 1 means flags to look at, 2 means the tool failed.

## 3. Read the report

Open `runs/film/report.md`. Each check is in one of four states:

- `flagged`: over its threshold. Open the evidence before you believe it.
- `clear`: measured and under the threshold. It says nothing beyond that one measurement.
- `info`: a number with no pass or fail, usually because nothing could be tested (no moving shot to test pinning, no counter on screen).
- `not_run`: a tool or model was missing.

A clear report does not mean a good video. "Not settled by this run" at the bottom of the report lists what is still open.
`references/checks.md` explains each check: how it works, its threshold and its source, what false flags look like.
Read the entry before overturning or trusting a flag on a check you have not used before.

Expect to overturn flags. On a real 47 s film we overturned all 4 spelling candidates we opened (OCR misreading small interface text), a subtitle measured while fading in, and a keyboard read as a pinned graphic. The upload banding and the unreadable screens were real.

## 4. Use your eyes on what code flagged

Work through `questions` in `runs/film/facts.json`. Each one names the frames to open and one narrow question. Read
`references/eyes.md` first. The rules that change results:

- Open `contact_sheet_*.jpg` and each flagged `evidence` file. Do not judge from memory of the prompt.
- Ask "describe" and "what is unusual", never "what is wrong" (57.2% against 29.5% on [GlitchBench](https://arxiv.org/abs/2312.05291)).
- Answer per shot, with yes or no, a time, and something you can quote from the frame to prove you looked.
- Do not estimate where people look. Models score about 0.34 to 0.41 against real gaze. Use the heat map.
- Ask for observations, not verdicts, and let code decide (`references/observe-prompt.txt`). Never ask "which is better?" once: our judge picked the take shown second 75% of the time.
- A hunch without evidence goes under "Hints", never in the defect list.

Code cannot settle these, so eyes decide, using the measured moments: whether a move has a cause, whether a pinned
graphic should be pinned, whether the most salient thing is the right thing, whether an outfit or light change is
intended, and whether it looks like the references or just near them.

## 5. Challenge it

One pass, then stop (three at most).

- **For each finding:** what would make this not a defect? Is it in the brief? Is it OCR misreading a word? Is the
  "late sound" an unrelated noise near a cut? Open the frames again at source size. Keep the finding, or overturn it and write why.
- **For each `clear` that matters:** open one example. A check that stops firing looks exactly like a clean video.
- **Stranger test:** can you name three things in these frames that could only come from this brief? If not, report how many you found.
- **Re-measure after a fix.** A fix is not done until the same command stops flagging it, and nothing new appears.

## 6. Write the verdict

```markdown
# Verdict: film.mp4
self-judged: no · ran 27 checks, 21 clear · not settled: lip sync, voice script

State: stopped (2 blockers)

| Severity | Time | Where | Measured | Evidence | Fix | Cost |
|---|---|---|---|---|---|---|
| blocker | 00:05.00 | whole frame | 2 black frames between lit frames | evidence/black_120.jpg | trim 2 frames at the seam | edit |
| major | 00:06-00:10 | dark gradient | CAMBI 4.1 source, 9.8 after upload at 2 Mbps | evidence/banding_3.jpg | add grain before encoding, or lift blacks | edit |

## Eyes
Shot 3, 00:07.20: label "Battery" points at the cell in the first frame and sits 90 px left of it in the last.

## Hints (no measurement behind these)
...

## Not checked
Mispronounced names. Whether the real X encoder matches the simulation.
```

Every row has a time, a number, a file and a fix. Cost is `cut`, `edit` or `retake`. Fix the cheapest first and name what stays as it is.
Severity comes from `SEVERITY` in `scripts/mj_rank.py`. Change it there if a piece needs different rules, and say so.

Then save what eyes settled in `runs/film/overrides.json`, so it counts in the ranking and the reason stays on record:

```json
{"overturned": {"spelling": "all three are OCR misreads, checked each crop"},
 "eyes": [{"severity": "major", "t": 7.2, "what": "label Battery no longer touches the cell"}]}
```

**The score** is the count. `State` is `stopped` with any blocker, `needs a look` with a major flag, `no measured defect` otherwise.
`ran 27, 21 clear` is the only number out of something. Do not blend these into one mark.

## 7. Rank takes

```bash
uv run scripts/judge.py rank runs/take1 runs/take2 runs/take3 --out runs/ranking
```

The order is blockers, then major flags, then minor flags, then the reference margin. `ranking.md` says why each take
beats the next, and it counts each run's `overrides.json`. For takes tied on facts, judge each take alone with observations and let code decide, then use pairs in both
orders where a flip stays a tie. See `references/llm-judge.md` for the protocol and how to write criteria.

## 8. Compare with a reference or a template

`--refs` aligns shots by picture and writes `evidence/reference_pairs_0.jpg`, ours next to theirs, worst pairs first,
with distances for structure, palette, composition, texture and tone, plus shot-length rhythm. Open the sheet. Numbers
say where it differs. Eyes say whether that matters.

With both `--refs` and `--template` you get `margin = distance to template - distance to references`. Above 0 means closer to
the references. These distances are hand-built on OpenCV features. No study validates them for taste, so treat a small
margin as a tie and look at the sheet.

## 9. Reverse engineer a finished piece

```bash
uv run scripts/judge.py reverse ad.mp4 --out runs/ad
```

This writes a shot list from measurement: start, length, camera move and speed, shake, palette, lightness, where the
focus sits, on-screen text, sound events, tempo, loudness, cuts per 10 s. Then open the sheets and add what code cannot
measure: the hook, the lens, the light, the intent. Mark those as estimates. Nothing recovers the prompt or the seed. Say so.

## 10. Keep the judge honest

- `tests/make_fixtures.py` plants one known defect per clip in real footage, and `tests/run_bench.py` reports catches,
  misses and false flags. Run it after changing a check. Add a fixture every time a person finds something the judge missed.
- `scripts/thresholds.json` holds every threshold with `status`: `published`, `convention` or `calibrated_on_fixtures`.
  Only a few are published. Calibrate the rest on your own references and keep the labelled pass and fail beside them.
- Keep some checks out of any automatic loop, and look at a sample by hand. A judge an agent can optimize will get gamed:
  ranking takes on lip-sync score alone brought back lip smacking, and a still video scores perfectly on temporal consistency.

## Limits

The attention map is a fast contrast, colour and motion model, far weaker than DeepGaze or ViNet. Use it as a report and swap in a better
model if a decision depends on it. The upload test is a simulation, since X and YouTube do not publish their delivered encoders, so one private
upload beats it. BT.1359's sync numbers were measured on lip sync, not on cuts. OCR misreads stylized type and misses text it cannot see.
Whisper can repair a mispronounced word, so it hears what it expects. Code proves something is broken or correct, not that it is good.

## Related

- `references/checks.md`: every check, threshold, source and false-flag pattern
- `references/eyes.md`: questions and rules for the vision pass
- `references/llm-judge.md`: LLM as a judge, bias measured on our own clips, the protocol, how to write a criterion
- `references/ranking.md`: gates, ties, pairs, and how not to get gamed
- `references/build-your-own.md`: how to build this yourself, step by step, with code that ran
- `references/tools.md`: other creators' tools and what each does better than this one
- `prompt.md`: paste-in prompts, for judging one video and for building your own judge
- `code-to-video-previz` `scripts/judge_pack.py`: pack and score a blind pair round
- `varg-video-prompting` section 9: the checklist used while making clips, `varg-video-editing` for fixes, `video-moodboard` for look checks before the render
