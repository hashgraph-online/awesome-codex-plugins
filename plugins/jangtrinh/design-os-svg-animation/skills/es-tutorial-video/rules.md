# Rules for tutorial videos

Each rule: Statement, Keep it (how to comply), Rejected when (what fails it), Checked by (`validate:<check>` is mechanical,
`look:<n>` is an eye-check in `look.md`, `build:gate` is enforced by `build.mjs`, `review` is a human judgment).
The validator rejects facts only; taste stays in `look.md`.

## R1 Verbatim evidence only
Statement: every excerpt on screen is copied from the build record by a script.
Keep it: `extract-evidence.py` writes `data/evidence.js`; the timeline reads `E[key]` through `tl.ex` / `tl.val` / `tl.line`.
The `AGENT_OK` line is the LAST sentinel of its file. A terminal command is one that was really run (copy it from the receipt).
Rejected when: an evidence entry is not `{path, lines|value}`, or on-screen text was typed into the timeline by hand.
Checked by: validate:evidence-shape, review

## R2 No home path on screen or in committed media
Statement: no absolute home path appears in any committed file, image metadata or video metadata.
Keep it: the extractor asserts `'/Users/' not in text`; run `mogrify -strip` on Blender stills (Blender writes the absolute `.blend`
path into the image); keep Blender metadata stamps off in renders; then `git grep --cached -l "/Users/"` is empty.
Rejected when: `/Users/` occurs in the config, evidence, timeline, voice script, `assets/`, `data/`, `ref/` or a staged MP4/JPG/PNG.
Checked by: validate:no-home-path

## R3 The music licence file is never committed
Statement: the licence of the track forbids redistributing it as a standalone file, looped, or inside a mix.
Keep it: project `.gitignore` lists `audio/` and `out/*.wav`; keep a screenshot of the licence page under `data/` if the licence needs proof.
Rejected when: `music.file`, `music.bed` or `out/tutorial-audio.wav` is not git-ignored.
Checked by: validate:gitignore-music

## R4 A chapter clip fits its window
Statement: a voice clip must end at least 0.3 s before its chapter ends, after the 0.5 s lead (clip <= window - 0.8 s).
Keep it: widen the chapter with integer-bar `WARP` knots borrowed from a chapter with slack; the mix reads chapter times from the timeline.
Rejected when: a segment has no chapter, no clip, or `end > chapter end - 0.3`.
Checked by: validate:script-clips

## R5 The bar grid is measured, not guessed
Statement: beat times come from the music file, measured with numpy (comb filter, downbeat phase), on the bed that is actually mixed.
Keep it: record the method in `grid.measuredBy`; chapter boundaries sit on downbeats; loops splice on a downbeat (`build-music-bed.py`).
Rejected when: `grid.measuredBy` is empty or still says "not measured".
Checked by: validate:config-schema

## R6 Captions never overlap
Statement: each caption window exits before the next one enters.
Keep it: `tl.cap(a, z, vi, en)` windows are ordered and `z` of one is `<=` `a` of the next.
Rejected when: a caption's end is later than the next caption's start.
Checked by: validate:captions-overlap, look:1

## R7 Two owner gates, enforced by the build
Statement: the owner approves the storyboard and the voice script before any voice credit is spent, and approves the result before merge or publish.
Keep it: record who and when in `approvals.storyboard` and `approvals.script`; `build.mjs mix` and `render --full` refuse while either is `null`;
the build and the kit make no network call; this skill never pushes, opens a PR or touches `docs/index.html`.
Rejected when: `mix` or a full render runs with an approval null (the build refuses, exit 1), or a script in this skill calls a voice or network API.
Checked by: build:gate, review

## R8 Show with `display=''`, hide with `display:none`
Statement: a hard-coded `display:block` overrides the stylesheet and flattens `display:grid` cards.
Keep it: the kit scene does `style.display = ''`; project code never sets a display value to show an element.
Rejected when: a project script assigns `display = 'block'` or `display: block`.
Checked by: validate:display-block

## R9 Beat frames have 3-digit names
Statement: a long film has more than 99 bars and the montage sorts by name.
Keep it: render beats with the kit (`bNNN.jpg`, plus `first.jpg`).
Rejected when: a file in `out/beats-*/` is not `first.jpg` or `bNNN.jpg`.
Checked by: validate:beat-names

## R10 Every image the timeline names exists
Statement: evidence without its picture is a claim.
Keep it: sequences are `pattern` with `%03d`, first and last frame must exist.
Rejected when: a path in a chapter card or element does not exist under the project.
Checked by: validate:assets-exist

## R11 Fonts are ready before any capture
Statement: Vietnamese glyph subsets load lazily; an early capture loses letters.
Keep it: the kit's `__framesReady` awaits `document.fonts.ready`; do not capture around it.
Rejected when: Geist or Geist Mono is not loaded at capture time.
Checked by: look:L1

## R12 One camera for every phase of a build
Statement: wire, clay and hi-fi stills of different phases come from the same camera, so wipes do not jump.
Keep it: write the camera to `data/<slug>-camera.json` and pass it to every render pass.
Rejected when: a wipe between phases shows the part at a different angle or scale.
Checked by: look:3

## R13 The hand-over states what was not verified
Statement: a report that only says "done" is not evidence.
Keep it: follow the hand-over block in `SKILL.md` (not verified first, paths, command and result per claim, open gate).
Rejected when: the hand-over lacks the NOT-verified line, a command result, or says "should work" / "looks good".
Checked by: review

## R14 Grid, duration and credit live in the config only
Statement: one place per fact; the timeline reads `D.CONFIG`, the mix and the bed builder read the same file.
Keep it: change `tutorial.config.json`, then re-run the contract check; never copy a BPM or a duration into a script.
Rejected when: the config fails the kit schema, lists a missing file, or `contract.json` was hand-edited.
Checked by: validate:config-schema, validate:contract-intact, validate:timeline-eval

## R15 There is a chapter that says what the build does not prove
Statement: the video must state the limits of the build (what is not measured, not manufactured, not accepted).
Keep it: copy the limit sentences from the build's own README/state, as evidence entries.
Rejected when: no chapter or caption carries a limit from the build record.
Checked by: look:6

## R16 Voice generation is one deliberate batch
Statement: every generation call spends credit, and a clone voice drifts between models.
Keep it: A/B one sentence on 2-3 models and let the owner choose; generate all segments once, fetch them at once; never retry a failed call automatically.
Rejected when: a second generation of the same segment is requested without the owner's word.
Checked by: review

## R17 A scaffold is not a tutorial
Statement: a project with no chapter, no element or no voice segment is unfinished work and is not handed over.
Keep it: author the timeline from the approved storyboard and the script from the approved text before validating for hand-over.
Rejected when: the timeline has no chapter or no element, or the voice script has no segment.
Checked by: validate:timeline-authored, validate:script-authored
