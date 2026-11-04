# Prompts

Two paste-in prompts. The first judges one finished piece. The second makes an agent build its own judge from nothing.

## Prompt 1: judge this video

Paste this into a fresh agent that did not make the video. Fill in the four lines at the top.

```text
File: <path to the video>
Brief: <what it must say, the product and any names, one line each>
References: <paths or links, or none>
Going to: <X, YouTube, Reels, TikTok, Shorts>

You are judging a finished video that an AI agent made. You did not make it. You have not seen its prompts. Do not ask for them.

Measure, don't grade. A finding is a time, a number and a picture. Never write a score out of 10, and never write "looks great" or any other adjective with no measurement behind it.

1. Install the judge if it is missing: npx -y skills add vargHQ/skills --skill media-judge -y
   Then read its SKILL.md and do what it says.
   If you cannot install anything, use ffmpeg and any Python you have, and say which checks you could not run.

2. Run it, with every flag the brief lets you use:
   uv run <skill folder>/scripts/judge.py video <file> --out judge_run --platform <where> --allow "<brand words>" [--refs <refs>] [--one-character] [--expected <lines file>] [--script <voice file>]

3. Open judge_run/report.md. Read every flagged item and open its evidence file. Never trust a flag you have not looked at. A flag you overturn stays in the report, with your reason.

4. Open judge_run/evidence/contact_sheet_*.jpg and answer each entry in "questions" in judge_run/facts.json, one at a time. Describe what is in the frame first. Ask what is unusual, never what is wrong. Quote something you can see in the frame in each answer.

5. For these twelve, write one row each: measured value, or "not testable here" and why.
   1 Everything is the same size.
   2 Nothing leads the eye.
   3 Too much on screen for the product to read.
   4 Motion with no cause.
   5 Graphics stuck to the screen instead of living in the scene.
   6 Labels that slide off what they point at.
   7 Dark scenes that break into bands and blocks after upload.
   8 Numbers that jiggle while they count.
   9 A face, outfit or light that changed between shots.
   10 A sound that lands after the cut instead of on it.
   11 A spelling mistake anywhere on screen.
   12 It looks like the template, not like the references.

6. Challenge your own list once. For each finding, what would make it not a defect? For each "clear" that matters, open one example and check it.

7. Report in this order:
   State: stopped (any blocker), needs a look (any major flag), or no measured defect.
   Counts: checks run, clear, blockers, major, minor.
   A table: severity, time, where, measured value, evidence file, the exact fix, cost (cut, edit or retake).
   What stays as it is.
   Hints: opinions with no measurement behind them, marked as such.
   Not checked: everything you could not test, with the reason.

If you could not hear the audio, write "measured, not heard". If you found nothing, say what you measured and what you did not. Do not invent a defect to look useful, and do not pass something you did not check.
```

## Prompt 2: build your own judge

Paste this into an agent in an empty folder, with one real clip from your own work.

```text
Build a judge for video that AI agents make. It measures and never grades: every finding is a time, a number and an evidence image.
Read https://github.com/vargHQ/skills/tree/main/media-judge/references/build-your-own.md first and follow its order.

Rules:
- Python with OpenCV and NumPy, ffmpeg for decode and encode, run through uv. CPU only. One command per file, one JSON and one report out.
- Read every frame. Do not sample for detection. Sampled frames are only for showing to a model afterwards.
- Every threshold lives in one JSON file with a status: published with a link, convention, or calibrated by you. Never invent a published number.
- Four states for every check: flagged, clear, info (a number with no pass or fail), not_run. Never let a skipped check look clean.

Build in this order, and do not start a step until the last one works on real footage:
1. Black, frozen, repeated and single glitch frames, flicker, flash count, shot list. Mind that ffmpeg's detect filters default to 2 s.
2. Test bench: take my clip and plant one defect per copy at a known time, plus untouched controls. Report catches, misses and false flags. Run it after every change from now on.
3. Upload test: encode at 2048 kbps at 1280x720 and measure CAMBI before and after on dark shots.
4. OCR with word tracks: spelling with an allow list, words on screen, reading time, contrast, safe zones, block heights.
5. Counters: a digit that keeps its value must not move while its neighbours count.
6. Camera against object motion, moves that start with nothing near them, regions that stay still while the scene moves, label drift against its surroundings.
7. Face identity, torso colour and side light across shots.
8. Loudness, clipping, drop-outs, signed offset of sound at each cut with a shift test against chance, beats only when the pulse is clear.
9. Reference comparison: align shots, measure palette, composition, texture, tone and rhythm, and write ours-and-theirs pair sheets. Margin = distance to template minus distance to references.
10. A vision pass in a fresh context that sees only flagged moments. A ranker: blockers, then major, then minor, then margin. For ties, compare pairs in both orders and treat a flip as a tie.

When you finish, show me the bench table, one real report and the list of what it still cannot test. Do not tell me it works unless the bench says so.
```
