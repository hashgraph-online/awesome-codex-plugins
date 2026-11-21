---
name: video-animate
description: >-
  Animate a video once the previz, characters, moodboard, script and sound exist. Decide per element whether code,
  AI video or both makes it, pick Seedance 2.5 or another model per shot, run a cheap 480p pass before paying for
  quality, choose one long generation or short clips, roll takes that differ only in performance, cut picture to the
  locked track, and generate plates the next agent can add motion design to and edit. Built from working AI
  filmmakers, vendor guides, sync standards and the film and animation canon, with frame counts, prompts, a take
  checker and a database directory. Use for "animate my previz", "Blender to Seedance",
  "three.js to video", "grey box to video", "which model for this shot", "Seedance or Kling", "long take or short
  clips", "480p draft", "animate to the beat", "cartoon timing", "music video from my previz", "footage ready for
  motion design". Not for building the previz (threejs-animatic, varg-previz), making the sound (video-sound) or
  the final edit (varg-video-editing).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.1"
  openclaw:
    requires:
      anyBins:
        - python3
        - ffmpeg
    homepage: https://github.com/vargHQ/skills/tree/main/video-animate
compatibility: >-
  Works in any agent with a shell. scripts/take_check.py needs Python 3 and ffmpeg (standard library only).
  Generation needs the varg MCP connection (https://mcp.varg.ai/mcp) or a VARG_API_KEY. Prices are in credits, checked
  2026-11-03: confirm each with estimate_cost before spending.
allowed-tools: Bash(python3:*) Bash(ffmpeg:*) Bash(ffprobe:*) Bash(curl:*) Read Write Edit
---

# Video animate

> Step 7 of 10 in [How to make a video with an AI agent in ten steps](https://varg.ai/how-to/make-a-video-in-ten-steps). The full guide, with every test and source: https://varg.ai/how-to/animate-a-previz-with-ai-video-models (as Markdown: add `.md`).

You already have the hard parts: an approved previz in Blender or three.js, characters, a moodboard, a script and
locked sound. This skill turns them into footage. One idea runs through all of it: **give each variable one owner,
and change it in the layer where changing it is cheapest and most exact.**

| Layer | Owns | Why |
|---|---|---|
| Previz | camera, blocking, timing | Free and exact. Change one thing and nothing else moves |
| Video model | look, performance, skin, cloth, weather, crowds | Plausible, but every call re-rolls whatever you left open |
| Code | text, numbers, UI, logos, charts, captions | Right to the character and the frame, every render |
| Edit | sync, final rhythm, cadence, retiming | Free, reversible, re-rolls nothing |

Something missing? Go back first: `find-references`, `video-moodboard`, `video-script`, `character-passport`,
`video-sound`, then `threejs-animatic` or `varg-previz`. No previz at all and only 1 to 3 simple shots: approve a still
per shot and use image-to-video (`varg-video-prompting`).

## What the evidence says

- **Simple blockouts beat detailed ones.** In nemopi's same-structure test, half-finished 3D leaked CG into 10 of 15
  shots and colour-coded blocks into 0 of 15 (https://x.com/nemopi/status/2076877246497976329, self-reported, Seedance
  2.0). ByteDance agrees: "Simple, coarse-grained 3D clay-model video generally works better as a reference."
  (https://docs.byteplus.com/en/docs/ModelArk/2607689). Nobody has compared a fully lit render against grey.
- **A cheap pass pays, but a plain re-run is a new take.** Seedance Draft to final correlated at 0.950 to 0.988 on
  five clips; a direct 1080p control scored 0.257 against the same draft
  (https://blog.segmind.com/seedance-2-5-draft-final-5-clips-tested-and-the-real-cost-math/, a reseller's test). The
  same seed at two resolutions: "These are not the same shot at two sizes."
  (https://blog.segmind.com/advanced-seedance-2-5-prompts-5-expert-patterns-tested-2026/). **varg has no Draft option
  yet**, so step 6 below gives today's path.
- **Long or short depends on the job.** Shimura's 30 s clips reached the screen at 32.2%, his 5 s clips at 3.3%, for
  finished cuts averaging 2.5 s (https://x.com/ucmulleryu/status/2092572054872784904, self-reported). Chris Capel:
  "short generations hold a performance better than long ones" (https://x.com/PJaccetturo/status/2116160709180723486,
  Dreamina partner). Both are right: harvest long, obey short.
- **Three takes earn their cost.** Cuts given 3 takes reached the screen at 22.3%, cuts given 1 at 8.8%
  (https://x.com/ucmulleryu/status/2091821264302412030, self-reported).
- **Sound on every cut is not what pros do.** In 7 launch films a salient hit sits near a visual event 29% of the time,
  against 27% by chance (https://raw.githubusercontent.com/Leonxlnx/earshot/main/docs/launch-video-sound.md). About
  85% of hard cuts carry no sound of their own
  (https://raw.githubusercontent.com/Leonxlnx/cinetic/main/skills/cinetic/references/sound.md). Launch films only;
  music videos differ.
- **Treat all of this as months-old practice.** The method spread from June 2026. No named expert publishes a full
  routing rule, most data is one person's report, and no test runs one previz through all the main models. The rules
  below marked [inference] are our synthesis. `references/evidence.md` has what is proven, what is not and seven cheap
  tests that would settle the biggest calls.

## Advice you will hear, tested

| You will hear | Verdict | Use this instead |
|---|---|---|
| Make a cheap version first, at 480p | Holds, with a change | Cheap pass first, always. Judge staging, camera, timing and shot order at 480p, never faces, hands or small text. Only Draft mode binds the take to its final |
| One long generation for a long shot, short clips for different shots | Holds, with a change | One run per location and light state. New run when the place or light changes, when a shot will need many retakes, or when the edit may move the cut |
| Something changes every 2 or 3 seconds | Holds, with a change | Something new happens every few seconds at the format's rate. New information, an action, a camera move or a sound event count. A transition effect does not. Vary the intervals |
| Every motion has a cause | Holds | Name the cause in the same sentence, with a time. Every sound has a cause in the story. A camera move needs one too |
| Sound hits land on cuts | Does not hold | Hits land on the moments that matter. Most cuts ride on the music. With no music, every cut needs sound |
| Sync within 5 ms | Does not hold as a target | Place sound by script to the sample, accept to the frame. One frame at 24 fps is 41.7 ms. Past 40 ms early or 60 ms late is a defect (EBU R37) |
| 3 takes that differ only in timing and camera | Does not hold on a generative model | Try timing and camera variants in the previz, where they are free and exact, and pick one. Then roll 3 takes with those locked, varying only the performance |

## The work, in order

Each step writes one file. At every **STOP**, show it and wait. Steps 1 to 3 are free.

### 1. Route every element

Go through the shot list and ask of each element, stopping at the first yes
([routing.md](references/routing.md)): must it be exact? is its motion defined by a rule? will it be versioned or
looped? is it a rigid hero object filling the frame? must a hit land within a frame or two of the track? must an AI
plate register with a code layer while the camera moves? must its physics be correct rather than plausible? Otherwise
it is a face, hair, cloth, weather, crowd or photoreal world: hybrid, with the previz as video reference plus images.

Writes `shots.md`: per shot, what code makes and what the model makes. Same failure twice later: split the shot or
build it in 3D. More batches rarely fix a structural failure.

### 2. Direct it in the previz

Timing and camera are decided here, because here they cost nothing. Render 2 or 3 variants of a hard shot if useful,
and pick one. Then add the craft.

- **A cause for every motion.** Each motion gets a chain: cause, anticipation, action, effect on others, settle
  (Disney via Stanchfield, Blair, Lasseter; [animation.md](references/animation.md)). Key anticipation and overshoot
  in the previz, because prompts carry them poorly. No held pose under 6 frames (Goldberg).
- **Ask less of the camera.** Most signature moves of the masters lower AI risk: ration close-ups, hold the first
  camera move for the reversal, crop in on the same axis instead of generating a new shot, let shots shorten into the
  peak ([cinema.md](references/cinema.md)). Models fail most on zoom, arc and roll, and on camera moves during action.
- **To the track.** Write cuts and events against `beats.json`. Vary shot lengths: "three-second clip after three-second
  clip" is Dave Clark's name for the failure (https://every.to/podcast/transcript-how-a-hollywood-director-uses-ai-to-make-movies,
  paywalled, not re-checked).
  For a song, pick a mode per section and declare any off-grid cut ([music-video.md](references/music-video.md)).
- **Leave room for what comes next.** Block the subject off-centre where a title will go, keep a plain wall free, and
  put graphics in simple or static shots ([post-ready.md](references/post-ready.md)).

**STOP:** show the previz with the track.

### 3. Build the reference clip and group the runs

Model only what must be copied [inference]: position, scale, camera and timing always, limb poses only when contact or
silhouette is the point, surface never unless the final look stays CG. Flat unlit solids, grey by default, flat ID
colours when subjects of similar value share a frame, and always a written mapping of shape to subject. Export at
1280x720 or higher and at least 24 fps. Finished looks go in as images, one job per reference.

Group shots into runs ([drafts-and-takes.md](references/drafts-and-takes.md)):

| Job | Generate |
|---|---|
| Harvest: coverage or dialogue you will cut up | 15 to 30 s, 2 to 4 beats. Only the best seconds must work |
| Obey: previz-locked or audio-locked timing | 4 to 11 s (varg's working range, no published threshold), about 3 strong beats |
| Same place and light, no cut will move | One multi-shot run: light and identity hold. Interior cuts have no handles |
| New place or light, many retakes likely, a cut that may move | Its own run |
| Prepared oner or in-camera transition in one world | One generation, "No cuts", timed segments, about 10 to 15 s |
| Transition between two worlds | Two generations with a designed join on a whip, wipe or foreground pass |

Add a 0.5 to 1 s tail to each run [inference]. Add one clean wide and 1 or 2 safety inserts per location, so they get
priced with everything else. A cut between whole seconds stays in `@video1`, because prompt times are whole seconds.
Writes `runs.md`.

### 4. Pick a model per run and price it

Seedance 2.5 is the default for a performance on a clay reference. Pick something else in five cases
([models.md](references/models.md)): a reference it will refuse; no faces and a tight budget
(`minimax_h3_max_3d_to_video`, built for Blender video up to 15 s); finished stills that must not change (`kling_v4`
keyframes); editing an existing clip or cheap B-roll (`wan_3`); or code does it better.

Typical credits for 5 s out with 5 s of clay in, our arithmetic from the catalog:

| Route | 480p | 720p or 768p | 1080p |
|---|---|---|---|
| Seedance 2.5, `byteplus:dreamina-seedance-2-5-260628` | 64 | 139 | 342 |
| Seedance 2.5, `piapi:seedance-2.5` (not labelled video-to-video on the live spec, so test one first) | 124 | 289 | 660 |
| MiniMax H3 Max 3D to Video | 90 | 105 | 145 |
| Kling 4 reference (no input fee assumed) | n/a | 79 | 118 |
| Wan 3 reference (no input fee assumed) | 25 | 50 | 100 |

Plain `seedance_2_5` picks a route by itself, so pin the route on clay shots. Listing a route does not prove it runs: the
first paid take after the yes proves it. If BytePlus fails, the fallback for clay is
`fal:bytedance/seedance-2.5/reference-to-video`, which has blocked realistic faces, so price it again.

Decide per run how it will finish, because that sets the takes in step 5: keep the approved take and upscale it, or
re-roll at higher resolution. Price with `estimate_cost` (`POST /v2/estimate` over REST); it can read low on a PiAPI clay
shot. **STOP:** show the run table with the ceiling, and agree a cap. Local files need uploading first (`POST /v2/files`
or `create_upload`), which comes after the yes.

### 5. Cheap pass

The riskiest shot goes first, one pilot per kind of shot, then the batch at 480p. A take you will keep and upscale gets
3 takes per run, 5 to 7 for acting or physical contact. A run you will re-roll needs 1 take at 480p, because the acting
does not carry; roll the 3 at the final. Between takes vary only the performance, with camera and timing locked by
`@video1`. Kling 4 has no 480p, so one 720p take per beat is its cheap pass. Prompts:
[prompts.md](references/prompts.md). Check each take the moment it lands:

```bash
python3 <skill>/scripts/take_check.py take.mp4 --plan 0,2.5,5 --reference previz.mp4 --json
```

It reports real cuts, frames, codec, bitrate and audio, and warns on a pass-through. Write the measured in-points into
the edit, never the requested ones. Then strip the audio, lay the takes on the locked track, and watch the cut every 3
to 5 shots to feel the pacing before spending more. Same failure twice: stop and change the shot.

**STOP:** show the cheap cut on the real track. Judge staging, camera, timing and order only.

### 6. Final pass

| Situation | Do |
|---|---|
| Draft mode available (BytePlus, some resellers; **not on varg as of 2026-11-03**) | Run the cheap pass as drafts, finalize from the task ID (ids last 14 days). A draft costs the same as plain 480p. Segmind computes break-even at about 1.2 takes on text prompts; BytePlus bills the clay on the final too, so clay shots save less |
| On varg today, stylised or medium shots | Upscale the approved take after the edit, selected ranges plus handles: `topaz_video`, `seedvr_video`, `sima_video_upscaler`. Only 720p to 1080p has a test; 480p to 1080p is unproven, so make a test shot first |
| On varg today, mid-size text, tight faces, dense texture | A new native take at 720p or 1080p with the same references. It is a new performance, so budget 2 to 3 takes. Upscaling left 15 to 25 px text ragged in Segmind's test, and generative upscalers can change how a face reads |
| Anything that must lip-sync | Generate with sound on so mouths move, discard that sound, lay the locked take, then `sync_v3` with only that shot's slice. Retime first, lip-sync second |

Budget by difficulty rather than runtime, and keep a line for shots the edit will ask for after first assembly.

### 7. Hand off

Sound and sync ([sound-sync.md](references/sound-sync.md)): move the picture, not the sound. Slipping a clip to its
contact frame is free; a re-roll is not. Align the body of a hit 0 to +40 ms after the picture event, let a short
transient start up to 60 ms early, keep music or room tone running through every cut.

Hand the next agent a clean package ([post-ready.md](references/post-ready.md)): one sidecar per take
([assets/take.example.json](assets/take.example.json)) with rank, reason, handles and free space; the takes with no
baked grain, vignette, bars, subtitles or logos; 1 or 2 safety inserts and one clean wide per location. Motion design
goes to `hyperframes` and the craft skills (`title-design`, `caption-styles`, `kinetic-type-art`, `social-overlays`,
`footage-effects`, `transition-craft`), the edit to `varg-video-editing`.

## Rules

1. **The previz owns camera and time.** Do not spend takes on them. If a push matters, do it in post on a static plate:
   in one film's measurements three of six pushes matched, one came back at half strength and two vanished.
2. **Model what must be copied, write the rest.** "if you skip that line, seedance copies the cheap 3d render"
   (https://x.com/rewind02/status/2110774943294070795). Say what each reference is for and what to ignore.
3. **Motion in the reference, acting in the prompt.** "Motion carries over from a video reference much better than it
   does from text." (Chris Capel, https://x.com/PJaccetturo/status/2116160709180723486).
4. **Strip every generated soundtrack.** No model plays your audio back: `@audio1` is re-performed. Generated sound is at
   most a guide or a layer.
5. **Cadence in the edit.** Prompted on-twos is a lottery; `ffmpeg -vf "fps=12,fps=24"` is exact, free and keeps sync.
   Details and the recipe that loses a frame: [animation.md](references/animation.md).
6. **Text, logos and numbers in code.** ByteDance on stray subtitles: "This issue cannot currently be eliminated
   completely." (https://docs.byteplus.com/en/docs/modelark/seedance-2-5-prompt-guide). Scan frames after generation.
7. **Spend in the order of risk.** Hardest shot first, pilot before batch, and price before you promise. Quote credits.
8. **Check every take, then show a person.** Agents cannot watch video, and the checks below catch only what can be
   measured. Taste needs a person, and no raw take is shown as the result.
9. **Respect rights.** Real people only with their consent, and no way around a moderation filter. Stylise the
   character, use a sanctioned route, frame around the face, or move the shot to Kling from finished stills. No living
   artist's or director's name in a prompt. Most shot databases are links for people, not model inputs
   ([links.md](references/links.md)).

## Checks

| Check | How | Pass |
|---|---|---|
| Cuts against the plan | `take_check.py --plan` (keyframes on cuts, then scene detection) | Within 1 frame with `@video1`. Text timestamps alone: expect about a second |
| Pass-through or grey copy | `take_check.py --reference` | No warning, and frames do not look like the previz |
| Previz look | Compare action takes with the previz | Does not still move like a clean animatic, one of two styles Joseph Kahn says AI flip-flops between (https://x.com/JosephKahn/status/2070788059680194970) |
| Stray text, logos, bars | Read frames at full size | None |
| People, hands, identity | QA list in `varg-video-prompting`, checked on full-size frames | Exactly as the shot names them |
| Hit against picture | Measure onsets; offset table in `sound-sync.md` | Not past 40 ms early or 60 ms late, except short transients |
| Beat grid | Two trackers, ratios near 2:1, 3:2 or 4:3 are metrical errors, then a click for a person to hear | A person confirms the click |
| Dead stretches | Compare the format's rate in `sound-sync.md` | Fail only on a long dead stretch, never a missed interval |
| Holds | Frame stepping on the key poses | No pose under 6 frames |
| Tracking before pinning a graphic | Plain tracker. House defaults from one film | Homography error under 0.7 px, F inliers over 0.75, point survival over 0.5 |

## Files

| File | Holds |
|---|---|
| [references/goal-prompt.md](references/goal-prompt.md) | The whole skill as one prompt to paste into any agent |
| [references/routing.md](references/routing.md) | Code, AI or hybrid per element, how much detail the previz holds, what goes in each channel |
| [references/models.md](references/models.md) | Which model per shot, prices per route, reference limits, moderation |
| [references/drafts-and-takes.md](references/drafts-and-takes.md) | Cheap passes, upscale or regenerate, long or short, oners, stitching, takes, a worked budget |
| [references/prompts.md](references/prompts.md) | Copy-paste shot prompts and the request fields for each |
| [references/sound-sync.md](references/sound-sync.md) | Generating from an existing track, sync numbers, offsets, beats, change rate, cause |
| [references/cinema.md](references/cinema.md) | Cinematic tricks with checks and AI risk |
| [references/animation.md](references/animation.md) | Animation and cartoon tricks with frame counts, ffmpeg cadence recipes |
| [references/music-video.md](references/music-video.md) | Music video modes, section plans, short clips |
| [references/post-ready.md](references/post-ready.md) | Generating for motion design and edit, tracking, mattes, delivery, the sidecar |
| [references/experts.md](references/experts.md) | Who has shipped this, what to cite them for, their biases |
| [references/links.md](references/links.md) | Databases and startups per step, with rights |
| [references/evidence.md](references/evidence.md) | Verdicts, conflicts and calls, gaps, seven open tests, where this overrides older varg skills |
| [scripts/take_check.py](scripts/take_check.py) | Measure one take: cuts, frames, codec, audio, pass-through, held frames |

## Related skills

Before this one: `find-references`, `video-moodboard`, `video-script`, `character-passport`, `video-sound`,
`threejs-animatic`, `varg-previz`. Alongside: `varg-video-prompting` (prompt anatomy and QA), `kling-4-keyframe-film`
(the stills-and-harvest route), `varg-music-video` (the full music video recipe), `varg-ai` (calls and rendering). After:
`varg-video-editing`, `hyperframes`.
