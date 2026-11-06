# Shot prompts for animating from an approved previz

`[vendor]` = company selling or reselling it, or a paid partner; `[self]` = one person's own report; `[measured]` = varg's own measurement; `[inference]` = our reasoning, nobody tested it; no tag = opened primary source.

For an agent whose user holds an approved previz, characters, a moodboard, a script and locked audio. Adds to
`varg-video-prompting/references/prompt-templates.md` ("PT"), which keeps stills, sheets and plain previz v2v (PT 10).
The templates are merged from published forms and have not been run as written unless a line says so; none does.

## Rules that hold across sources
| Rule | How to write it | Source |
|---|---|---|
| Each reference gets one job | One opening line per file. A graybox is "explicitly for camera and staging, never for appearance" | Chris Capel via PJ Ace [vendor: Dreamina partnership] https://x.com/PJaccetturo/status/2116160709180723486. Kling: give each asset a role, or the model infers one less predictably [vendor] https://kling.ai/quickstart/kling-4-model-user-guide |
| Say what to ignore in the blockout | "ignore its grey materials and flat lighting." Give the real form of every symbol, since a sphere can stay a sphere | Ichel Park [self] https://x.com/ichelpark/status/2112990600236851333. "if you skip that line, seedance copies the cheap 3d render" (rewind [self] https://x.com/rewind02/status/2110774943294070795). Kashima [self] https://github.com/atsu-mada/previz-maker-public |
| Describe only what the blockout cannot show | Surfaces, light, weather, faces, anything unbuilt. Name the move to copy, do not re-describe it. Keep the text consistent with the clay | Same blocks, two prompts: built things held, words added unbuilt things, and dropping "island platform" turned one side into a wall (GIRAFFRAME [vendor: sells a previs tool] https://x.com/girafframe/status/2115464164823171151). Runware [vendor] https://runware.ai/docs/models/klingai-video-4-0/guides/reference-videos. BytePlus [vendor] https://docs.byteplus.com/en/docs/ModelArk/2607689 wants text "consistent with the 3D clay-model video", but also says to "describe the desired generated video content in detail", so keeping it short is our reading [inference] |
| Motion in the reference, acting in the prompt | Camera and body path come from `@video1`. Eyes, breath and intention go in words | "Motion carries over from a video reference much better than it does from text." (Capel via PJ Ace [vendor] https://x.com/PJaccetturo/status/2116160709180723486). Depth "can't really capture subtle facial motion" (Curious Refuge [self] https://x.com/CuriousRefuge/status/2087276113672475117) |
| Whole-second timestamps, absolute times, a time budget per shot | `0-2 s`, `2-5 s`, counted from the start of the clip. Not `0.0-1.8 s` as in PT 9-11. A cut between whole seconds stays in `@video1`; round the text to the nearest second. Frame-exact work goes to the edit | BytePlus "supports integer-second timestamps" [vendor] https://docs.byteplus.com/en/docs/modelark/seedance-2-5-prompt-guide; "not frame-accurate edit points" (fal's copy [vendor] https://fal.ai/learn/devs/how-to-use-seedance-2-5). Unbudgeted cuts fell at 6.08 and 11.54 s of 15 s; budgets gave 4.88, 5.16, 5.03 s shots (Segmind [vendor] https://blog.segmind.com/advanced-seedance-2-5-prompts-5-expert-patterns-tested-2026/) |
| One action per beat, with its cause and end state | The next beat continues from that end state. About 3 beats a run | Kashima [self]. "who or what caused it" (Eian [self], translated, https://x.com/EianLu/status/2117469941364637983). "reliably delivers about three strongly distinct beats per generation" (Krea [vendor] https://www.krea.ai/blog/seedance-2-5-prompt-guide) |
| Short when a reference video carries direction, long when only stills do | Clay run: a few lines. Stills only: the prompt carries camera, action, weight and pace | Our reading of a dispute, neither side tested the other's setup [inference]. Long essays, no previz (Pryce [self] https://x.com/second_bassoon/status/2117703324321694077); long on Kling (Workman [vendor] https://x.com/mattworkman/status/2116204462263910473) |
| Logical sections, no JSON | Plain labelled lines: roles, Aim, Events, Locks | JSON syntax wastes characters, separation helps (kaigani [self] https://x.com/kaigani/status/2073005386668577098). Kashima's four headings [self] |
| Negative wording is per model | Seedance forms write "Do not copy". On Kling, use "only" to exclude. Check the first take for what leaked | "Do not copy colours, boxes, spheres or the ground." (Kashima [self], translated, https://github.com/atsu-mada/previz-maker-public). Runware [vendor]. BytePlus: "Use positive descriptions whenever possible", with negatives supported for subtitles and audio [vendor] https://docs.byteplus.com/en/docs/modelark/seedance-2-5-prompt-guide. Nobody compared wordings across models [inference] |
| No text from the model | The last line of every template. Titles, captions and lyrics go in the edit | "never ask the model to type your slogan" (KRUX [self] https://x.com/kruxael/status/2117381314370224424) |
| No living artist's name | Say medium, line, palette and light | House rule, no test behind it [inference]. Seedance 2.5 blocked an anime brief twice with a copyright-related flag (Everypixel [vendor] https://journal.everypixel.com/kling-4-vs-kling-3): rewrite the brief, do not work around a block |

Keep these in proportion: across 300+ motion-first cuts Shimura found no measurable difference by prompt style and no
link between length and adoption (https://x.com/ucmulleryu/status/2092925867978834314 [self]).

Any shot that will take graphics also ends with the plate line from case 9: `Clean digital image, no film grain, no
vignette.`

## 1. Seedance 2.5 reference from clay, single shot
From: BytePlus's "Map the man in gray clothing from [Image 1] to the red model in [Video 1]" [vendor]
https://docs.byteplus.com/en/docs/ModelArk/2607689; Kashima's headings; Ichel Park's clause. For: the default
character shot. Tested as written: no, the merge is ours [inference].
```text
@video1 is only camera, blocking, positions and timing. Do not copy its colours, materials, boxes or lighting.
Map {character} from @image1 to the {colour} model in @video1. The sphere is the head. {Proxy} is {real form}.
@image2 is {location}. Aim: {one sentence on what this shot is about}.
Events: 0-2 s {one action, its cause, its end state}. 2-4 s {next action, continuing from that end state}.
Locks: {what must not move}. Not in the blockout: {eyes, breath, cloth, light, weather}. No BGM.
Full-bleed {aspect} frame, no borders, no letterbox. No text, letters, numbers, logos or UI anywhere in the frame.
```

## 2. Seedance multi-shot run in one location
From: "Beats left unstaged with only "HARD CUT" between them usually come out as soft morphs rather than real cuts."
(Krea [vendor] https://www.krea.ai/blog/seedance-2-5-prompt-guide); Segmind's budgets [vendor]; layout of PT 9. For:
same location and light. Tested as written: no; the staging lines are our reading of Krea [inference].
```text
@video1 is only camera, blocking, cut timing and positions. Do not copy its colours, materials, boxes or lighting.
Map {character} from @image1 to the {colour} model in @video1. @image2 is {location}: all shots here, same light.
Three shots, 9 s, one camera move each. Shot 1, 0-3 s, budget 3 s. {Size and angle}: {one action, cause, end state}.
Hard cut at 3 s to {new size and angle}. Shot 2, 3-6 s, budget 3 s. {Action continuing, its end state}.
Hard cut at 6 s to {new size and angle}. Shot 3, 6-9 s, budget 3 s. {Action continuing, its end state}.
Full-bleed {aspect} frame, no borders, no letterbox. No text, letters, numbers, logos or UI anywhere in the frame.
```
Interior cuts have no handles [measured, one film], so a cut the edit may move needs its own run.

## 3. Dialogue: coverage pass, then one generation per shot
From: Chris Capel via PJ Ace [vendor] https://x.com/PJaccetturo/status/2116160709180723486 and his "ALREADY SPEAKING
his line in the very first frame" https://x.com/PJaccetturo/status/2116160706387362235. For: several angles of one
talking scene. Tested as written: no; these are our forms of his method [inference].
```text
@image1 is {character A}. @image2 is {character B}. @image3 is {location}.
{If a previz exists: @video1 is only camera and staging. Do not copy its colours, materials or lighting.}
Coverage of one scene, {3} angles, 24 s in total. 0-8 s, wide two-shot: {A} says "{line}".
8-16 s, over {A}'s shoulder on {B}: {B} says "{line}". 16-24 s, close-up on {A}: {reaction}, then "{line}".
Full-bleed {aspect} frame, no borders, no letterbox. No text, letters, numbers, logos or UI anywhere in the frame.
```
Keep one clean frame per shot: "Shots from different runs still match, because they all come from frames of the same
coverage pass." With a previz and finished frames (PT 5), start at the second prompt [inference].
```text
@image1 is the first frame of this shot. Keep its framing, faces, set and light.
{Character} is already speaking in the very first frame: "{line}".
0-{n} s: {one action, its cause, its end state}. Between phrases: {a small body action}. Camera: {locked or one move}.
No BGM; generate only environmental sounds and action sounds.
Full-bleed {aspect} frame, no borders, no letterbox. No text, letters, numbers, logos or UI anywhere in the frame.
```

## 4. One-take long shot with an in-camera transition
From: "No cuts", timed segments (ZentrixHQ [self] https://x.com/ZentrixHQ/status/2105339471763767447); "one continuous
physical shot" (nemopi [self], translated, https://x.com/nemopi/status/2076268948673474596); "clearly specify both the
trigger point and the transition method" (BytePlus [vendor] https://docs.byteplus.com/en/docs/modelark/seedance-2-5-prompt-guide).
For: a prepared oner in one world. Tested as written: no.
```text
@video1 is only the camera path and timing. Do not copy its colours, materials, boxes or lighting.
@image1 is {character}: the {colour} model in @video1. @image2 is {location}. One continuous physical shot. No cuts.
0-4 s: {one action, its cause, its end state}. 4-8 s: {next action, continuing from that end state}.
Transition at 8 s. Trigger: {the camera passes behind the pillar}. Method: {the pillar fills the frame and clears}.
8-12 s: {next action}, same {face, outfit, light}, ending on {final framing}.
Full-bleed {aspect} frame, no borders, no letterbox. No text, letters, numbers, logos or UI anywhere in the frame.
```
Find hidden cuts with scene detection at threshold 0.2 to 0.3 (Segmind, Krea [vendor]). Past 10 to 15 s or between two
worlds, make two runs joined on a whip, wipe or foreground pass [inference]; an orbit with a morph kept 0% of tracked
points [measured]. Long moves need an end frame, or mannequins reappear (Sharipov [self] https://x.com/aigenboss/status/2115587840704708984).

## 5. Audio-driven: tempo or performance, sound on then discarded, No BGM
From: "@Audio1 provides tempo only" (Emily2040 [self] https://github.com/Emily2040/seedance-2.0/blob/main/skills/seedance-audio/SKILL.md);
"No BGM; generate only environmental sounds and action sounds." (Fuser [vendor] https://fuser.studio/articles/seedance-2-5-prompt-guide).
For: a body in time with music, or on-camera speech. Tested as written: no; the speech line is ours [inference].
```text
{Music: @audio1 provides tempo only. Do not sing it, speak it or play it back.}
{Speech: @audio1 is a performance reference for {character}: delivery, pace and breath only. Close-up, low action.}
{Music: @video1 is only camera, blocking, positions; do not copy its look. Its {colour} model is @image1.}
@image1 is {character}. @image2 is {location}. 0-3 s: {one action, cause, end state}. {Speech: "{the locked line}".}
No BGM; generate only environmental sounds and action sounds.
Full-bleed {aspect} frame, no borders, no letterbox. No text, letters, numbers, logos or UI anywhere in the frame.
```
Sound on for mouths, then discard it (PT 12). Assume `@audio1` is re-performed (Ozan Sihay [self], translated, https://x.com/ozansihay/status/2117667049304396155),
so the edit delivers sync [inference]: strip the track, lay the locked take, retime, then `sync_v3` (PT 15), or for
music retime to the grid. A black video carrying the audio (PT 16) is reported as more consistent than `@audio1`,
unmeasured (SeeGen [vendor] https://seegen.ai/seedance-2-0-audio-guide; MrDavids1 [self] https://x.com/MrDavids1/status/2115485216361869757).

## 6. Performance take: camera and blocking locked, only the acting varies
From: "The only variable is camera position and lens." turned around (Scenario [vendor] https://x.com/Scenario_gg/status/2102365314562294250);
Shimura's correction. For: an approved camera with unapproved acting. Tested as written: no. The three variants are
ours [inference]; no source compares them with three rolls of one prompt.
```text
@video1 locks camera, blocking, positions and timing: do not restage or re-time. Do not copy its colours or materials.
@image1 is {character}: the {colour} model in @video1. @image2 is {location}.
The only variable is the performance. Aim: {what this moment means to the character}. Performance: {variant}.
0-{n} s: {the one action from the previz, its cause, its end state}, played through that performance.
Full-bleed {aspect} frame, no borders, no letterbox. No text, letters, numbers, logos or UI anywhere in the frame.
```
Run three times, one `{variant}` a run: `{holds it in: a small tell}`, `{lets it reach the body: a larger tell}`,
`{plays against the line: the opposite tell}`. This corrects "3 takes": 22.3% adopted, 8.8% for 1 take
(https://x.com/ucmulleryu/status/2091821264302412030 [self]), but volume alone does not hit; locking camera and timing
first changes it (https://x.com/ucmulleryu/status/2091706394307408073 [self], translated). Budget 5-7 (Pryce [self]).

## 7. Kling 4 from finished stills and keyframes
From: "Kling 4 Ref2Video REALLY wants fully finished still frames and you can have LOTS of them" (Workman [vendor]
https://x.com/mattworkman/status/2116204462263910473); keyframes over omni reference (NOBU [self], translated, https://x.com/nbykos/status/2117136627709673886).
For: approved stills (whole film: `kling-4-keyframe-film`). Tested as written: no. Short is our call [inference],
against Workman's long prompts; expand it with one or two stills.
```text
One continuous shot. {Character} {one action, its cause, its end state}; the keyframes are poses on the way, not cuts.
Camera: {one named move}. Keep every face, outfit and set as in the keyframes. {If speech: she says "{line}".}
Full-bleed {aspect} frame, no borders, no letterbox. No text, letters, numbers, logos or UI anywhere in the frame.
```
"Multi-shot is enabled by default"; keyframes mode takes no other assets (Kling [vendor] https://kling.ai/quickstart/kling-4-model-user-guide).

## 8. `minimax_h3_max_3d_to_video` from a Blender render with no faces
From: the varg spec ("Uncovered shots stay in the video.", so cover every view) and fal: the prompt says what the
blocks are; exact geometry, camera paths and motion are "not guaranteed" [vendor] https://fal.ai/models/minimax/h3-max/3d-to-video.
For: environment, vehicle or prop shots; no faces is our pick [inference]. Tested as written: no.
```text
The video is a 3D blockout. It sets layout, camera, object motion and timing. Its grey surfaces are placeholders.
{Tall grey slab} is {real structure}. {Red box} is {real object}. {Floor plane} is {real ground}.
The reference images set the look of every surface: {materials, light, weather}. No people in any shot.
Full-bleed {aspect} frame, no borders, no letterbox. No text, letters, numbers, logos or UI anywhere in the frame.
```

## 9. Clean plate for motion design
From: no published plate prompt in our sources; all ours [inference]: name what fills the free space, lock the camera
so code layers register, grain and vignette on the final comp. For: a shot taking graphics. Tested as written: no.
```text
@image1 is {the moodboard frame}: take palette and materials only. One continuous shot. No cuts.
Locked camera on a tripod: {position, lens}. {Subject} stays in the {left third}: {one small action, its end state}.
The {right two thirds} is {a plain dark wall}: one even surface in soft low contrast, clear for the whole shot.
Light: {direction and quality}, constant from first frame to last. Clean digital image, no film grain, no vignette.
Full-bleed {aspect} frame, no borders, no letterbox. No text, letters, numbers, logos or UI anywhere in the frame.
```

## 10. Cartoon or stylised with named timing (weak)
From: Kashima's clause [self]; naming the style against realistic pull (BytePlus 2.0 guide [vendor] https://docs.byteplus.com/en/docs/modelark/2222480).
For: 2D or stylised looks. Tested as written: no. Weak: timing names are frame-level and prompt time is whole seconds,
so expect them to be ignored [inference]. No source here measures prompted cadence.
```text
@video1 is only camera, blocking, positions and timing. Do not copy its colours, materials, shapes or lighting.
@image1 is {character}: the {colour} model in @video1, the sphere is the head. @image2 is {stylised location}.
Style: {medium in craft terms: ink line, flat colour}. Every frame stays in it. Timing: {on twos, held poses}.
Events: 0-2 s {one action, its cause, its end state}. 2-4 s {next action, continuing from that end state}.
Full-bleed {aspect} frame, no borders, no letterbox. No text, letters, numbers, logos or UI anywhere in the frame.
```
Do the cadence in the edit: hold frames after the run, e.g. `-vf "fps=12,fps=24"` for twos at 24 fps [inference].

## 11. Image-to-video fallback with the previz deleted
From: PT 7; 4 failed v2v batches moved to image-to-video (Higgsfield [vendor] https://higgsfield.ai/blog/ai-vs-vfx);
"the posed people gave it stiff motion to copy" (David Israel [self, ImagineArt-tagged] https://x.com/RealDavidIsrael/status/2097028838249079149).
For: a take that moves like an animatic, the same failure twice, a previz adding nothing. Tested as written: no.
```text
Animate this exact frame. Camera: {named move, speed, start framing, end framing}.
{Character} {one action, its cause}. Weight: {how the body carries it}. Speed: {fast, no slowing}. Ends: {end state}.
No reference carries this, so write it all: {cloth, hair, breath, background life, each with what moves it}.
Keep {face, outfit, set} exactly as in the image. No cuts, no new objects.
Full-bleed {aspect} frame, no borders, no letterbox. No text, letters, numbers, logos or UI anywhere in the frame.
```
The cost: without clay, Seedance 2.5 kept crossing the axis in one dialogue test (ToAPIs [self] https://x.com/MaddieSmitxfs1/status/2117531141095948371).

## Request fields per template
Checked 2026-11-03 against `https://varg.ai/models/{model}.md` and `https://api.varg.ai/v2/tools/video?model={model}`.
BP = `byteplus:dreamina-seedance-2-5-260628`. REF = `provider_options.byteplus.omni_reference_task_type: "reference"`.
MOV = `provider_options.byteplus.output_format: "mov"`. `fal.x` = `provider_options.fal.x`. Durations are ours
[inference]; 4-11 s is varg's range for locked timing, no published threshold. Also set `aspect_ratio`.
`resolution` is the final. The cheap pass sends the same request at 480p; Kling has no 480p, so it stays at 720p. `files`
are URLs: upload local files first, after the budget is approved. If BP fails on clay: `fal:bytedance/seedance-2.5/reference-to-video`
with `fal.task: "reference"` and `fal.video_urls`, which has blocked realistic faces. PiAPI is not labelled video-to-video
on the live spec, though it takes `input.video_urls` and `input.omni_reference_task_type`, so test one before planning on it.

| # | `model` | `files`, in order | `resolution` | `duration` | `audio` | `provider_options` |
|---|---|---|---|---|---|---|
| 1, 2, 6, 10 | BP | character, location, clay | 720p | 4-11, match the clay | false; true if a mouth moves | REF, MOV |
| 4 | BP | character, location, clay | 720p | 10-15 | false | REF, MOV |
| 3 coverage | BP | characters, location, clay if any | 480p | 20-30 | true | REF |
| 3 per shot | `seedance_2_5` | one frame (one file is the first frame, PT 7) | 720p | 4 or more | true | none |
| 5 music | BP | character, location, clay, audio | 720p | under 10 | not tested either way; strip it | REF, MOV |
| 5 speech | BP | character, location, audio | 720p | 4-10 | true | REF, MOV |
| 7 | `fal:fal-ai/kling-video/v4/keyframes-to-video` | none | 720p or 1080p | 3-30 | true only for speech | `fal.keyframes: [{ time, image_url }]`, up to 10. REF and `output_format` do not exist here |
| 8 | `minimax_h3_max_3d_to_video` | none | `fal.resolution`: 480P, 768P or 1080P | ignored if sent; source up to 15 s and 32 shots | ignored if sent | `fal.video_url`, `fal.reference_image_urls`, `fal.prompt`; `fal.max_generated_reference_images` 1-8 only when no references go in |
| 9 | BP | moodboard frame | 1080p | 4-11 | false | REF, MOV, `provider_options.byteplus.watermark: false` |
| 11 | `seedance_2_5` or `kling_v4` | one still, no video | 720p | 4-11 | false | none |

- `@image1`, `@video1`, `@audio1` are "1-based position within each media type" (Seedance spec, PiAPI field). Its
  summary caps references at 9 images, 3 videos, 3 audio; BytePlus's tutorial allows more, so design to the spec.
- REF: pin BP, because "Only the options of the provider that runs the job apply" and `seedance_2_5` picks a route
  itself; on `fal:bytedance/seedance-2.5/reference-to-video` use `fal.task: "reference"`. Edit mode locks ratio and
  duration, which may explain a varg run that returned the clay re-encoded (untested) [inference]. A mismatch with the
  prompt fails with `InvalidParameter.TaskTypeMismatch`.
- MOV: only BytePlus Seedance has `output_format`. Recommended for editing and extension; its 1080p is 10-bit H.265,
  which some players cannot open (https://docs.byteplus.com/en/docs/ModelArk/2607688 [vendor]).
- Spec gaps: Kling's `keyframes` is in the JSON Schema only and `time` has no stated unit, so check it on the first
  run. H3's page does not say how top-level `files` map, so use the `fal` fields.

## Published prompts worth reading
- Kashima's previz-maker template [self]: https://github.com/atsu-mada/previz-maker-public
- Ichel Park's ignore clause [self]: https://x.com/ichelpark/status/2112990600236851333
- Chris Capel's prompts via PJ Ace [vendor]: https://x.com/PJaccetturo/status/2116160706387362235
- BytePlus's clay-model prompt guide [vendor]: https://docs.byteplus.com/en/docs/ModelArk/2607689
- BytePlus's Seedance 2.5 prompt guide [vendor]: https://docs.byteplus.com/en/docs/modelark/seedance-2-5-prompt-guide
