---
name: edit-footage-with-code
description: >-
  Edit real footage with an agent: turn raw takes of a talking head, podcast, vlog, course or ad into a clean cut, then
  add captions, B-roll, motion graphics and sound with HyperFrames or Remotion. Reads the take as text and audio, removes
  dead air, retakes and stumbles without clipping words, writes the cut as an edit list a person can review, keeps every
  graphic on the spoken word, and checks the result with numbers and frames before a person watches; tested scripts
  and defaults from 2,318 editors' posts. Use for "edit this video", "cut my footage", "remove the pauses", "cut the dead air", "clean up my talking
  head", "rough cut", "edit with HyperFrames", "edit with Remotion", "make it look edited", when an agent's edit keeps
  coming back wrong, or to rank cuts with an unbiased LLM judge ("which edit is better").
  Not for generating video from a prompt (varg-ai), for choosing a hosted editing service
  (varg-video-editing), or for finding music, B-roll or sound effects (video-asset-sources).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.2"
  openclaw:
    requires:
      bins:
        - ffmpeg
        - ffprobe
        - python3
    homepage: https://github.com/vargHQ/skills/tree/main/edit-footage-with-code
compatibility: >-
  Scripts need Python 3 and ffmpeg, nothing else (standard library only). Transcription is local through HyperFrames, or any tool that gives word
  timestamps as JSON. HyperFrames or Remotion is needed only for overlays. Nothing here calls a paid service.
allowed-tools: Bash(ffmpeg:*) Bash(ffprobe:*) Bash(python3:*) Bash(npx:*) Read Write Edit
---

# Edit footage with code

> Step 8 of 10 in [How to make a video with an AI agent in ten steps](https://varg.ai/how-to/make-a-video-in-ten-steps). The full guide, with every test and source: https://varg.ai/how-to/edit-a-video-with-hyperframes-and-agents (as Markdown: add `.md`).

An agent can cut footage well when it stops trying to do everything at once. The people getting usable edits work in the same stages, whatever engine or language they use: read the take as text, agree a plan, cut the speech, lock the audio, then add picture on top, sound last. One prompt on long raw footage is the most repeated failure.

Which engine matters less than this order. Cut with ffmpeg and word timings. Add overlays in whichever engine the project already uses.

| Situation | Use |
|---|---|
| A plain cut with few graphics | ffmpeg only: stop after step 5 |
| Graphics on a cut, HTML-first, agent does the checks | HyperFrames: [references/hyperframes.md](references/hyperframes.md) |
| React codebase, brand system, or data-driven batches | Remotion: [references/remotion.md](references/remotion.md) |
| A person will finish in Resolve or Premiere | Any of the above, plus the FCPXML from step 5 |

## Rules that do not bend

1. **Never overwrite the source.** Write to new files.
2. **Cut only in the silence between words**, at the quietest 10 ms slice. Never inside a word.
3. **Word timestamps say which words, not where to cut.** ASR stretches words across pauses. On our test clip, gaps between words found 1 of 13 real pauses.
4. **No plan, no cut.** Show the plan and wait for a yes, unless the person asked for no stops.
5. **Spoken cut first, nothing else until it is locked:** no captions, no graphics, no music.
6. **Every graphic, caption and sound keys to a word**, looked up in a file, never estimated.
7. **Green checks are not approval.** Look at frames. A person listens.
8. **Show numbers, names and prices exactly as spoken.** Never invent a stat, a testimonial or a piece of UI.

## The loop

### 1. Intake

```bash
ffprobe -v error -show_entries format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,color_transfer -of json take.mp4
```

- The two rates differ at all (phones run slow: 29.99 drifts up to 0.16 s over 12 minutes), or the rate is unlike the project's: conform first with `ffmpeg -i take.mov -vf fps=30,format=yuv420p -fps_mode cfr -c:a copy take.mp4`. Never `-r 30`.
- `color_transfer` of HLG or PQ: phone HDR. Convert to SDR before anything, and do not grade your way out.
- Read `rules.md` and `style/<format>.md` if they exist. No style file on a new format: write one from 3-5 references ([references/notes-and-rules.md](references/notes-and-rules.md)).
- A short video from a long ramble is the hardest case. If the person can still shoot, a short script beats carving one out.

### 2. Read the take

```bash
npx hyperframes transcribe take.mp4 -d edit --model small.en --json     # or any word-level JSON: [{text,start,end}]
python3 <skill>/scripts/analyze_take.py take.mp4 --words edit/transcript.json --out edit
# with a local Whisper-family model, always make this second pass: it is what exposes retakes
python3 <skill>/scripts/transcribe_islands.py take.mp4 --take-json edit/take.json --out edit/islands
python3 <skill>/scripts/analyze_take.py take.mp4 --words edit/islands/words.json --punct-from edit/transcript.json --out edit
```

Read `edit/review.md`, then read the whole transcript yourself. The script measures this file's room and voice, finds real pauses from the audio, keeps cuts clear of slates, fades and camera changes in the picture, and lists retake and filler candidates. It writes a draft `edit/edl.json`. **It is a draft.** It only cuts a retake when the repeat covers most of the earlier attempt, because parallel wording ("trying to go to the moon... trying to go to the space station") looks like a retake and is not. It never cuts fillers unless told to. A false cut is worse than a missed one.

Why two passes: Whisper tidies repeats into one clean sentence and stretches words across pauses. Given one stretch of speech at a time, it cannot. On our test clip the island pass raised pauses visible in word timings from 1 to 12 of 13, cut badly placed words from 23 to 2, and exposed a false start and a real stutter the first pass had hidden. It took about a minute and a half for an 85 s clip, so skip it on footage you know is clean or when using an engine that keeps fillers.

Before cutting a retake or a stutter, transcribe a short stretch around it alone and check its energy. Even the island pass can place words badly inside a long stretch, and ASR writes "you know" over an "um". The script's retake boundaries are a starting point.

Keep these rules in mind while reading:

- Prefer a word-level engine that keeps fillers when an API is allowed (ElevenLabs Scribe). Whisper-family models often drop um and uh, so listen before believing the transcript is clean. A fresh transcript of the cut can also reveal stutters the first one hid.
- Take text from the script if there is one. Keep only the times from ASR.
- Do not assume the last take is best. In one worked example it won 1 of 4 scenes. Choose on completeness and cleanliness, and disqualify a take with a dead pause mid-sentence.
- Look at frames only at decision points. Reading a 12 KB transcript beats burning tokens on every frame.
- Several speakers: separate them before choosing content.

### 3. Propose, then wait

Write 4-8 plain sentences: shape, takes chosen, what gets cut, target length, what stays for later. List every removed pause that sits right before a number or a punchline, since no detector can tell a deliberate beat from a stumble. Stop until the person says yes.

### 4. Write the edit as a file

Change `in` and `out` in `edit/edl.json` by hand. Write the reason for each big decision next to it. Choose ranges by word, assemble by story beat rather than file order, and keep the strongest line for a cold open if the format wants one. For multi-take jobs, use one sub-agent per scene plus a verifier.

Defaults for every number, with what changes them: [references/numbers.md](references/numbers.md).

### 5. Rough cut, then lock the sound

```bash
python3 <skill>/scripts/build_cut.py edit/edl.json --take take.mp4    # writes cut.sh, clips.html, Cut.tsx, cut.fcpxml
sh edit/cut.sh                                                        # edit/acut.mp4, about a minute
npx hyperframes transcribe edit/acut.mp4 -d edit/heard --model small.en --json
python3 <skill>/scripts/qa_cut.py edit/acut.mp4 --edl edit/edl.json --heard edit/heard/transcript.json --intended edit/intended.json --out qa --no-loudness
```

- Read `word_diff` and `doubled_words` in `qa/qa.json`. ASR invents some stutters and hides others, so settle each one by transcribing that stretch alone and reading its energy.
- **Trust `hot_joins`, not the transcript, for clipped words.** On our test clip, cutting 140 ms of speech at every join still matched the clean cut's transcript at 99.1%, because ASR fills in word ends. The audio check at the join caught 12 of 13 cuts, against 0 of 13 on the clean version.
- Look at `qa/joins.jpg`. It catches what audio checks cannot: on our test clip, a slate flashed for one frame at a join with every audio check green.
- A flash near a join: move that segment's `in` or `out` by a few frames, then rerun `build_cut.py`, which recomputes everything else.
- Use the one filter graph in `cut.sh`. On our test clip, per-segment AAC extracts joined with `-c copy` drifted +300 ms over 14 cuts, about 21 ms per cut (@hassancs91 measured 15-20 ms). The filter graph matched the edit list to the frame.
- A join with no silence to cut in (two words run together) stays flagged. Check its levels and transcript, then pass `--accept-join <seconds>`, and list it for the person to hear first. Give that join its own fade with `fade_in_ms` or `fade_out_ms` on the segment.
- Give the person a way to review: the cut, the list of what was removed and why, the joins sheet. They listen to the joins. Move on only when the audio flows.
- If joins keep sounding wrong, stop re-prompting. Hand over `cut.fcpxml` for a hand trim in Resolve or Final Cut. @ladprofit, who publishes the best numbers we found, still trims jump cuts by hand.

### 6. Stills before motion

One still per scene on a contact sheet, or 4-6 key frames. Give a target image when you have one: it reduces rounds more than prompt wording. Fixing a still takes seconds, fixing an animation takes a render. For a new format, render a 15-25 s sample before the rest.

### 7. Picture on top

- Time everything from the cut's own transcript, `edit/heard/transcript.json`. Do not push single-pass word times through the edit list: on our test clip that lost 23 of 222 words. With an engine you trust (Scribe, or the island pass), computing output times from the list is exact and needs no second transcript; re-transcribe as the check.
- Punch-ins need spare pixels: a 1.5x crop on 1080p goes soft. Render the cut larger than the composition if you plan to zoom much.
- Keep one timing file and a cue sheet. No frame number written as a literal in a component. Round every time to whole frames from the frame number: a value rounded to 4 decimals can land a frame late.
- A transcript's word times stay loose around pauses, even on the cut: one tester saw a word start about 1 s early. Compare every cue with the speech list from a fresh analysis of the cut, and for a cue that must land exactly, transcribe its window alone.
- Build motion plates separately, then composite. Each element enters on its word. Do not reveal unrelated things at once, or cover the face.
- Hold back. "Heavy motion, lots of text" is itself a named failure. Keywords on screen, sentences in captions. B-roll needs to add new information, or it goes.
- Real UI only.

For source files: `video-asset-sources`. For named effects: `varg-video-edit-library`, `caption-styles`, `title-design`, `transition-craft`, the HyperFrames registry. Other people's kits, job by job: [references/other-skills.md](references/other-skills.md).

### 8. Sound last

Voice chain, then music under speech if the format wants it, then a few effects tied to visible events, then loudness measured on the final mix. Start with no whooshes: the agent's default is to add them, and people remove them. **You cannot hear this.** Report the numbers, and flag the music for a person. For anything beyond a plain voice-and-bed mix, use the `video-sound` skill, which builds and grades the mix with scripts.

### 9. Check your own work, at most 3 passes

```bash
python3 <skill>/scripts/qa_cut.py out.mp4 --heard heard.json --intended edit/intended.json --out qa
```

It fails on: length off the edit list, joins that cut through speech, pauses over 0.6 s, an opening on silence, loudness off -14 LUFS, true peak over -1.5 dBTP, black frames, flash frames, under 95% of intended words heard, and a phrase said twice in a row. Change the limits with its flags for your format. It writes `contact.jpg` and `joins.jpg`, which you must look at. Also check every cut boundary, the first and last 2 s, names and prices on screen, and that nothing private shows. Then list what you could not verify.

### 10. The person watches. Then notes, rules, and stopping

Ask them to watch all of it with sound before anything changes. Then one batch of notes, each with a timestamp. Freeze what is approved. Turn each note into a rule. Stop when a full watch produces no note that would block publishing.

The note formats, the rule file, the style file and the stop rule: [references/notes-and-rules.md](references/notes-and-rules.md).

### 11. Deliver

One full render, then check the exported file, not the preview. Hand over the MP4, the SRT, the edit file and the timeline. Never publish without the person's yes.

## Comparing cuts

To compare versions or to tell whether a change made edits better, use a blind judge: [references/judge.md](references/judge.md) and [references/judge-prompt.md](references/judge-prompt.md). On one pair it can say "clear", "leaning" or "too close". Its real strength is across many footages. Scripts own time and motion, and a person owns sound.

Know the bar: in the largest test we found, the best agent passed 15 of 56 real editing tasks, and human editors preferred the reference edit in 83.5% of judgments. Most failures were craft, not defects: agents check for faults, and editors judge polish, shot selection and rhythm. Passing every check here does not make a cut good.

## Prompts

Ready prompts for the person to paste, and for you to hand to sub-agents: [references/prompts.md](references/prompts.md). A `/goal` prompt that runs this whole loop: [references/goal-prompt.md](references/goal-prompt.md).

## When it goes wrong

Symptoms you can detect, with fixes: [references/failures.md](references/failures.md). Who said what, what we tested and what nobody has measured: [references/sources.md](references/sources.md).
