---
name: character-passport
description: >-
  Cast an AI video before anything moves: for every character and hero prop, a passport (one paragraph, every
  visible detail, pasted word for word into every prompt), a turnaround sheet in the moodboard's look, six
  expressions written as cause + physical tells, a measured voice line (pace in words per minute, accent, one verbal
  habit), and for props the materials, wear and how they move and sound. Includes anti-slop design rules, a prompt
  builder that refuses paraphrased passports, code routes (three.js, VRM, SVG face rig) and tested reference sites.
  Use for "make a character", "consistent character", "character sheet", "turnaround", "character bible",
  "expression sheet", "voice for my character", "prop sheet", "same person in every shot", or characters that look
  generic, plastic or different from shot to shot. Not for category looks (varg-character-design), real actor photos
  in multi-scene ads (varg-consistent-characters) or the film's look (video-moodboard).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.2"
  openclaw:
    requires:
      anyBins:
        - python3
    homepage: https://github.com/vargHQ/skills/tree/main/character-passport
compatibility: >-
  Works in any agent with a shell. scripts/prompt.py needs Python 3; crop_sheet.py needs Pillow; voice_check.py
  needs ffmpeg. Images and voices through varg (MCP https://mcp.varg.ai/mcp or VARG_API_KEY): about $0.05 per
  image on Nano Banana 2.1 and $0.01 per voice take on Gemini 3.8 Flash TTS. Code routes need a browser or bun.
allowed-tools: Bash(python3:*) Bash(curl:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# Character passport

> Step 5 of 10 in [How to make a video with an AI agent in ten steps](https://varg.ai/how-to/make-a-video-in-ten-steps). The full guide, with every test and source: https://varg.ai/how-to/design-characters-and-props-for-ai-video (as Markdown: add `.md`).

Character slop comes from letting the model choose the face, the clothes and the feeling. This skill takes those
choices back, one checkable line at a time, and proves each step on a still before any video is paid for.

What our test showed (Nano Banana 2.1, 2026-11-03, full write-up: https://varg.ai/how-to/design-characters-and-props-for-ai-video):

- **The passport gets you halfway; the sheet finishes the job.** Two blind AI judges scored "same person across four
  shots" 2/10 for the moodboard's one-line subject, 5/10 for the passport alone, and 7.5-8.5/10 with a sheet as
  Image 1. Grey and moodboard-lit sheets tied; neither leaked its grid or backdrop.
- **Big features survive, small and side-specific ones don't.** Collar, scarf, hair and eye shadows: 89-100%.
  Hair behind the right ear 0/23, scar on the left 0/14 (mirrored), salt-marked boots 0/12, worn umbrella handle
  0/22 when its own prop sheet was not attached.
- **Cause + tells beats adjectives for acting.** Stills: more real (7 vs 5) and less theatrical (3.5 vs 6).
  Video, same start frame: the adjective prompt made Kling 4 under-act and Seedance 2.5 over-act into a snarl;
  cause + tells + timing played as written on both (one clip each).
- **Measure the voice.** "Slow, half-second pauses" came out at 92 wpm against a 130 target; the corrected line
  landed at 129.

## Files you produce

```
cast/<id>.md        one per character and hero prop: premise, ```passport, ```voice or ```motion, never-change list
cast/<id>-sheet.png turnaround sheet (approved), plus panels/ cut by scripts/crop_sheet.py
cast/<id>-faces.png six-expression sheet (characters)
cast/<id>-voice.wav approved voice take + its voice_check.py result
cast/board.md       the cast at a glance: one row per character/prop with sheet, faces, voice, status
```

## Step by step

### 0. Inputs

Read `moodboard.md` (video-moodboard) for the look block and `script.md` / `story.md` for what each character does.
No moodboard yet: run video-moodboard first, or write a 3-line look block (light, palette, film stock) and say so.

### 1. Design the person before the picture

Answer in `cast/<id>.md`, one line each: premise (who, in one sentence) · job and history · what they want in this
film and what stops them · one visible flaw · one BIG signature detail readable at phone size · a silhouette that reads
as a black shape · why each garment is on them (job, money, weather, era). Category looks (grandmas, big guys,
mascots, beautiful women, cartoon): open the matching varg-character-design recipe.
Rules and the slop-tell list: [references/design.md](references/design.md).

### 2. Write the passport

One paragraph, fixed order: who (name, age as a number, origin, job) → height, build, posture → face top to bottom
→ skin → hair → clothes outer to inner, top to bottom, each with colour, material and one sign of wear → hands.
Only what a camera sees; side and size for every mark (then check it: models mirror sides); no value words; no
detail that hides another (a scarf over the missing button); under ~900 characters. Put it in a
```passport fenced block. Template and filled examples: [references/passport.md](references/passport.md).

### 3. Turnaround sheet in the moodboard look

Front, side, back full body (same scale, one ground line, empty hands) over three big close-ups (front,
three-quarter, profile). Light it with the film's key direction and colour temperature, the film stock's texture,
a plain backdrop in the palette's darkest tone, and a fill that keeps every feature readable. Use flat 18% grey
instead when the character moves between very different lights. Prompts: [references/sheets.md](references/sheets.md).

**Check** the sheet against the passport line by line; fix misses with an edit pass on the sheet, not a re-roll.
Cut panels: `python3 scripts/crop_sheet.py cast/<id>-sheet.png --out cast/<id>-panels`.

### 4. Six expressions (characters)

Pick six moments the film needs. Write each as **a cause in the film + physical tells** (brows, lids, mouth,
jaw, head, breath), never an adjective. Default set: listening (rest face), real laugh, anger held in, worry,
startle, contempt. Generate one 3x2 sheet with the turnaround as Image 1. Tells per emotion and what video models
get wrong: [references/acting.md](references/acting.md).

### 5. Voice line (characters who speak)

Write a ```voice block: pace in words per minute + where the pauses go · pitch and texture · accent (region,
class, first language) · one verbal habit · default emotion. Generate a test line in the character's words, then
`python3 scripts/voice_check.py take.wav --text "<line>" --target-wpm <n>`. Fix the instruction, not the target,
until it passes. Then listen for the accent: no script checks it. Details and model notes:
[references/voice.md](references/voice.md).

### 6. Props

Every object the camera lingers on or a character touches twice gets its own `cast/<id>.md`: a ```passport
(what it is, materials and finish, size, wear and where it comes from, never-change) and a ```motion block
(weight, how it moves, what it sounds like). Sheet: five views on the same backdrop, no hands, one close-up of
the wear. Attach the prop sheet as Image 2 in every shot where the prop must read: without it, the worn handle came
out right 0 of 22 times. [references/props.md](references/props.md).

### 7. Use them in every shot

Build each shot prompt with the script, so the passports go in word for word and the prompt stays under the
model's limit:

```bash
python3 scripts/prompt.py build --sheet "Vesna" --shot "Close-up, 50mm: ..." \
  --cast cast/vesna.md --cast cast/umbrella.md --look moodboard.md [--video]
python3 scripts/prompt.py check prompts/*.txt --cast cast/vesna.md --cast cast/umbrella.md   # before any batch
```

Images: the sheet (or its panels) as Image 1, prop sheet as Image 2, location master as Image 3, each named by
job, plus a winner rule. Video: animate an approved still (Kling 4), or give Seedance 2.5 the face close-up and the
full-body front. Model table: [references/generate.md](references/generate.md). On GPT Image 2.6 / ChatGPT: [references/gpt-image.md](references/gpt-image.md).

### 8. Judge and rank takes

Code first: `scripts/face_check.py` for identity, `scripts/voice_check.py` for pace, `scripts/prompt.py check` for
passports. Then AI judges on one binary criterion per call, blind, reference first, three model families, takes
ranked in pairs in both orders. Calibrate each criterion against people (`scripts/judge_agreement.py`) before
trusting it. Rubric, judge prompt and the biases to design against: [references/judge.md](references/judge.md).

### 9. STOP for approval

Show `cast/board.md` with sheet, faces, prop sheet and the voice take's numbers. Nothing moves before a yes.

## Other routes

- **Build them in code** when the shape must be exact or reused a lot: a three.js blockout or VRM puppet rendered
  from four cameras, an SVG face rig driven by FACS action units, a PBR prop, or image-to-3D from an approved front
  view; then one image-edit pass dresses it in the film's look (tested: same pose, proportions and prop placement).
  Code in `code/`, routes and gotchas in [references/code.md](references/code.md).
- **Find references first** (real faces, costumes, props, accents): [references/reference-sites.md](references/reference-sites.md)
  and the find-references skill.

## Never

"beautiful", "perfect", "stunning", "flawless", "cinematic" in a passport · a celebrity's or a living actor's name ·
paraphrasing a passport between shots · props in the character's hands on the sheet · two looks on one sheet ·
expressions as bare adjectives · a voice without a measured take · brand names (they draw logos) · real people's
faces without consent.

## Files in this skill

- `references/design.md`: designing a specific person; the slop tells
- `references/passport.md`: template, rules, filled examples
- `references/sheets.md`: turnaround, expression and prop sheet prompts; moodboard vs grey
- `references/acting.md`: six expressions with physical tells; making emotion read as real in video
- `references/voice.md`: the voice line, pace numbers, accents, verbal habits, TTS models
- `references/props.md`: prop passport, materials, wear, motion and sound
- `references/generate.md`: models and reference order for stills and video
- `references/gpt-image.md`: GPT Image 2.6 (ChatGPT's model): settings, measured drift, fixes, prompts
- `references/code.md`: three.js, VRM, SVG and Blender routes
- `references/reference-sites.md`: tested sites for faces, costumes, props, poses and accents
- `references/people.md`: who to learn from on X and in the craft, why to trust them, and red flags
- `references/x-evidence.md`: 200+ techniques from X by topic, verbatim, with links and metrics
- `references/craft-evidence.md`: design, slop, acting, voice, prop and sheet rules from studios, research and model guides, with quotes
- `references/evidence.md`: the blind-judged test behind this skill (numbers, prompts, cost)
- `references/judge.md`: judging and ranking takes with AI judges: rubric, prompt, protocol, biases
- `references/judge-evidence.md`: the research behind judge.md (biases with numbers, VLM failure modes, sources)
- `references/goal-prompt.md`: the whole skill as one copy-paste prompt
- `scripts/prompt.py`, `scripts/voice_check.py`, `scripts/crop_sheet.py`, `scripts/face_check.py` (identity by face
  embedding), `scripts/judge_agreement.py` (judge vs judge vs human: kappa, TPR, TNR)
- `code/`: tested three.js blockout turnaround, VRM expression sheet, SVG FACS face rig, PBR prop, GLB turnaround,
  image-to-3D client scripts, and `shoot.ts` (Bun + Playwright headless renderer)
- `examples/vesna/`: the worked example (passport, voice, six expressions, umbrella, all image URLs)
