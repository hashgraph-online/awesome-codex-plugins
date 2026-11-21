# Post-ready generation: plates the next agent can finish

Decides what to do while generating so the next agent can add motion design and edit: what stays out of the plate,
how graphics get pinned, what to deliver, what to record. Motion design belongs to title-design, caption-styles,
kinetic-type-art, social-overlays, footage-effects, transition-craft and hyperframes; editing to varg-video-editing.

`[vendor]` = company selling or reselling it, or a paid partner; `[self]` = one person's own report; `[measured]` = varg's own measurement, usually one film; `[inference]` = our reasoning, nobody tested it; no tag = opened primary source (docs, standard, paper, book).

## Rules at generation time

Post cannot add what the model never drew. Mapping set rules to generation is ours [inference]; the set rules come
from a VFX tips video as summarised by filmmaker [Tihomir Lazarov](https://fstoppers.com/vfx/ten-tips-shooting-video-footage-visual-effects-173143) [self].

| Do this | Support |
|---|---|
| Design free space in the previz: block the subject off-centre and leave a plain wall. In the prompt describe it positively as a blank surface. "plain dark wall on the left third" is our wording, untested, and only backs up the previz | [inference]. Composition held to about 1 to 2% of width on simple shots [measured, one film]. Eian leaves room above and below in first frames ([post](https://x.com/EianLu/status/2117469941364637983) [self, translated]) |
| Use blank space for screen-locked text only. A pinned graphic needs texture near it, or a locked camera and a push in post. A graphic that must feel 3D needs foreground and background objects. Draw no tracking markers into the previz | [inference] from Lazarov [self]: nothing trackable means lock the camera and add the motion in post; parallax lets a track solve in 3D. "Generally, you don't want to place markers for Planar Tracking, because you'll just have to paint them out." ([Hollywood Camera Work](https://www.hollywoodcamerawork.com/tracking-plates.html) [self]). Both sources accept markers when nothing else tracks ("if there's zero to track, you simply have to"); the locked camera is our substitute |
| No in-camera cuts in clips that take tracked graphics. Pass one shot per run and ask for one continuous shot | [inference]: a track restarts at every cut, and interior cuts have no handles |
| No morph or environment change in clips that take tracked graphics | [measured, one film]: 0% of points survived on an orbit with a background morph |
| Leave the look out of plates: no film grain, vignette, painted bars or lens dirt. Add them last. Get 21:9 from `aspect_ratio`, never letterbox. Check borrowed prompts: a BytePlus example says "fine realistic film grain" ([guide](https://docs.byteplus.com/en/docs/modelark/seedance-2-5-prompt-guide)) | [inference]. **No test found** of baked grain, vignette or bars against tracking or matting |
| Keep rain, steam, reflections, fine patterns and thin structures away from areas that get tracked or matted | [measured, one film]: the one rain and steam shot kept 0.47 of its points, no controlled pair. Generators make rigid surfaces "stretch, bend, or "melt" under camera motion" ([GeCo](https://arxiv.org/abs/2512.22274), older models, intro and appendix read) |
| Static or slow camera in graphic shots, no whip or crash zoom. One light state, no rack focus | Camera: Lazarov [self]; [Beeble docs](https://docs.beeble.ai/beeble/video-to-vfx) say avoid shaky camera [vendor]. Light and focus are our additions [inference] |
| Whole silhouette in frame early, subject separated in tone from the background, no flying hair over busy detail | [inference] from the first-frame mask [MatAnyone 2](https://github.com/pq-yang/MatAnyone2) needs and Beeble's input advice [vendor]; untested |

## Text suppression is imperfect, so scan frames

| Do this | Support |
|---|---|
| Scan every take: sample frames and OCR or vision-check, at least the bottom third (ours, untested). Write `qc.text_scan`. Retake rather than paint out where a retake is cheap [inference] | BytePlus on stray subtitles: "This issue cannot currently be eliminated completely." ([guide](https://docs.byteplus.com/en/docs/modelark/seedance-2-5-prompt-guide)). Eian checks a contact sheet every 0.4 s ([post](https://x.com/EianLu/status/2117469941364637983) [self, translated]) |
| Keep the `@video1` previz free of labels and subtitles. Do not repeat dialogue words or attach tone directions to words | "Subtitles in a reference video may override the no-subtitle instruction."; "These descriptions can trigger subtitle generation." ([same guide](https://docs.byteplus.com/en/docs/modelark/seedance-2-5-prompt-guide)) |
| Pick negative wording per model. Prompt lines live in prompts.md | BytePlus's sample: "No subtitles, no text overlays, no dissolve transitions, no duplicated people, only hard cuts." ([tutorial](https://docs.byteplus.com/en/docs/ModelArk/2607688)). Google advises against "no" or "don't" and suggests listing the unwanted terms ([guide](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/video/video-gen-prompt-guide)). The Gemini API's Veo 3.1 Preview shut down on 2026-10-22 ([docs](https://aistudio.google.com/docs/veo)), so recheck for your route |

## Safe areas

| Box | Action or platform margin | Graphics | Source |
|---|---|---|---|
| 16:9 broadcast | 93% (1786x1004 at 1080p) | 90% (1728x972) | [SMPTE ST 2046-1](https://pub.smpte.org/doc/st2046-1/20091123-pub/st2046-1-2009.pdf); [EBU R 95](https://tech.ebu.ch/docs/r/r095.pdf) agrees, 3.5% and 5% per side |
| HyperFrames Studio | 90% | 80% | `hyperframes-studio` skill, "Premiere's defaults". Stricter, and inside 80% is also inside 90% |
| 9:16 at 1080x1920, px top/bottom/left/right | TikTok 240/660/120/120, Reels 269/672/65/65, Shorts 288/672/48/192 | 288/672/120/192, the strictest of each, as in `caption-styles` | [upload-post checker](https://www.upload-post.com/tools/safe-zone-checker/) [vendor], checked 2026-09-23. **Derived from ad guidance; it found no official numbers for organic posts** |

In the previz keep essential action inside 93% and free space inside 90% (80% if HyperFrames' boxes are the check).
Then check output frames: scale can be off from frame one, and one test came back looser [measured].

## Previz camera is intent; track the output

Seedance 2.5 video-to-video [measured, one film, one director, one model]:
- Position drift 0.3 to 2% of width on simple shots. Scale off by 5 to 10% from frame one on 2 of 3 measurable shots.
- Pushes: of six measurable, three matched, one came out at half strength, two vanished. The one orbit did not happen.
- A previz showing the back of a head came back face-on: check orientation before pinning to a subject.
- OpenCV Shi-Tomasi corners, Lucas-Kanade, RANSAC similarity per frame pair. Close-ups measure the subject, not camera.
- Not measured: Kling 4, Veo, Wan, MiniMax `3d_to_video`, lens against previz FOV. No published test of commercial modes
  found. [PartiCam](https://arxiv.org/abs/2609.39504) (abstract only, research methods) calls exact paths "challenging".

**The fix for a push that matters:** generate a static plate slightly wider than needed and push in post, with plate
and graphics in one wrapper, so the graphic is tracked by construction [inference]. Set rule: lock off, add the move in
post, shoot wider (Lazarov [self]). Exaggerating the push in the previz can overshoot, since three of six already matched.

| Overlay (table is ours [inference]) | Do | Why |
|---|---|---|
| Screen-locked title, caption, lower third | No tracking. Read free space from the output | Needs only the output's composition |
| Pinned to a wall, screen or floor in a static or slow shot | 2D or planar track on the output, transforms as JSON, driven by timeline time. Previz data only picks the surface and the tracker's start region. House limit, ours from one film: static, or about 13% scale change over 4 s | Sub-pixel fits [measured, one film]; previz scale and push rate differ. "All these plates are A LOT easier to track with Planar Tracking." ([Hollywood Camera Work](https://www.hollywoodcamerawork.com/tracking-plates.html) [self]) |
| Must feel 3D across parallax | Fake it: static plate plus wrapper push, or short shots. Otherwise a VGGT or MegaSaM solve, checked by reprojection | No 3D solve has been tried on these clips |
| Orbit, morph, whip | Do not pin. Move the graphic to the cut before or after, or generate a graphic-free take | 0% survival [measured, one film] |

## Track acceptance gate

Run per take before compositing. Accept for pinning when homography error is under 0.7 px, F inliers over 0.75 and
survival over 0.5; otherwise retake or move the graphic. **House defaults from one film, ours, not published values.**

How: frames 1280 wide, 12-frame gap, RANSAC. Homography error is median reprojection; F inliers the share fitting one
epipolar geometry at 1 px; survival the share of 600 points still tracked at shot end with a forward-backward check;
jitter the residual from a 9-frame moving average. `scripts/take_check.py` does not compute these; OpenCV does [measured].

- Seen [measured, one film]: 0.12 to 0.64 px on simple shots; the orbit 0.72 px with 0% survival, so survival catches it.
- Record jitter too. It has no threshold: a moving face passed all three at 0.86 px jitter, so look before pinning to a
  subject [measured; the check is ours]. No real-camera baseline was measured.

## Matte, depth and tracking tools

varg's catalog has no video matte, segmentation or depth model today, only image background removal and upscalers
([llms.txt](https://varg.ai/models/llms.txt), checked 2026-11-03). Run these locally or on their host. **No side-by-side
of these mattes on AI footage has been run.** Licences as read on 2026-11-03; recheck before paid work.

| Tool | Gives | Needs or watch | Licence |
|---|---|---|---|
| `npx hyperframes remove-background` (`media-use` skill) | Alpha as VP9 or ProRes 4444, local | People only. `--quality best` for a cutout over its own source | Apache-2.0 (`u2net_human_seg`) |
| [SAM 2.1](https://github.com/facebookresearch/sam2), [SAM 3](https://github.com/facebookresearch/sam3) | Object masks from clicks or boxes; SAM 3 also takes text prompts | Masks, not soft alpha (our note) | 2.1 Apache 2.0; 3 "SAM License", commercial terms not read |
| [MatAnyone 2](https://github.com/pq-yang/MatAnyone2) | Alpha and foreground | Video plus a first-frame mask, for example from SAM. README describes human video matting | NTU S-Lab 1.0: **legal check before paid use** |
| [BiRefNet](https://github.com/ZhengPeng7/BiRefNet), [on fal](https://fal.ai/models/fal-ai/birefnet/v2/video/llms.txt) | Per-frame segmentation; fal outputs ProRes 4444, VP9, mask video | No temporal claim in the README: check flicker | MIT |
| [RVM](https://github.com/PeterL1n/RobustVideoMatting) | Alpha and foreground with no extra input | Built for humans | GPL-3.0 |
| [Video Depth Anything](https://github.com/DepthAnything/Video-Depth-Anything), [on fal](https://fal.ai/models/fal-ai/depth-anything-video/llms.txt) | Temporally consistent depth, long clips | fal defaults to Large: **confirm the hosted licence** | Small Apache-2.0; Base and Large CC BY-NC |
| [TAPIR, BootsTAPIR, TAPNext](https://github.com/google-deepmind/tapnet) | Point tracks, online and offline | BootsTAPIR best at 512x512 | Apache 2.0 |
| [CoTracker3](https://github.com/facebookresearch/co-tracker) | Any-point tracks | "The majority of CoTracker is licensed under CC-BY-NC." | **Out for paid work** |
| [VGGT](https://github.com/facebookresearch/vggt) | Camera, depth, 3D tracks, COLMAP export | README does not describe moving objects | Only VGGT-1B-Commercial, by application form |
| [MegaSaM](https://github.com/mega-sam/mega-sam) | Structure and motion from dynamic video | CUDA, multi-stage setup | Apache 2.0 (software) |

Default, ours and untested: people go to `remove-background`; better edges on people get a SAM mask, then
MatAnyone 2 if the licence clears; other subjects get a SAM mask or BiRefNet. Test `ffmpeg -filters` first: one build had no `vidstabdetect` [measured].

## Delivery specs: the default MP4 is a viewing file

| Item | Do or check | Evidence |
|---|---|---|
| `mov` | Where keying or matting is planned, set `provider_options.byteplus.output_format: mov` (Seedance 2.5). `yuv444p` names no 10-bit, so read `pix_fmt` on the first clip [inference] | "H.264 video encoding + yuv444p chroma sampling + PCM audio encoding", for "color grading, keying, and compositing" ([BytePlus](https://docs.byteplus.com/en/docs/ModelArk/2607688); [varg spec](https://varg.ai/models/seedance_2_5.md)). **Not tested through varg**, nor whether it survives varg's output mirror |
| 10-bit HEVC | Use 1080p for hero shots that get graded, 720p for tests [inference]. Make review copies in H.264 | "1080p output uses 10-bit color depth and H.265/HEVC encoding"; 480p and 720p are 8-bit (BytePlus). It "will not play in Chrome or Firefox on Windows" ([Segmind](https://blog.segmind.com/seedance-2-5-draft-final-5-clips-tested-and-the-real-cost-math/) [vendor]). In HyperFrames, HEVC 8/10-bit assets "render correctly everywhere" and preview is proxied (`hyperframes-core`) |
| Bitrate per route | Probe one clip per route before a batch; fps, codec and bitrate for Kling 4, Veo through varg, Wan 3 and MiniMax H3 are unknown. On fal set `provider_options.fal.bitrate_mode: high`, untested through varg | [measured, one film]: BytePlus 7.3 to 14.7 Mbps, one fal clip 1.03 Mbps. YouTube recommends [5 Mbps at 720p](https://support.google.com/youtube/answer/1722171). A PixVerse ad's claim that Kling 4 gives 4K 10-bit HDR ([post](https://x.com/MonetizationDon/status/2117669858728972636) [vendor]) is unverified; [Kling's guide](https://kling.ai/quickstart/kling-4-model-user-guide) marks 10-bit HDR output "coming soon" |
| Keyframes only on cuts | `ffprobe -skip_frame nokey` is a free shot-boundary detector on Seedance. Run it on the original: conforming replaces the keyframes [inference]. Elsewhere use [practices.md](../../varg-video-editing/references/practices.md) #20 | [measured, one film; other routes and models unchecked]. Cuts landed exact or one frame early, so write real in-points |
| N x 24 + 1 frames | 97 for 4 s, 121 for 5 s, 289 for 12 s. Trim the extra frame deliberately and record it | [measured, Seedance only] |
| Mezzanine for HyperFrames | Keep the original. Conform at the same fps, `-g <fps>` or all-intra, near lossless, tagged bt709 if untagged, and never re-encode twice [inference]. Compare one rendered frame to the source before the batch | "Footage with keyframes more than about 1 s apart freezes on seek: re-encode with `-g <fps>`." (`hyperframes/references/overlays.md`). Every clip measured breaks it. It may affect preview only, and untagged colour in HyperFrames is untested |
| Stay at 24 fps | Run the project and `--fps` at the generated 24. Do not mix 16 or 30 fps sources without an explicit conversion. Probe other models: varg's catalog does not state fps for most | Seedance 2 and 2.5 came back at 24 [measured]; Veo 3.1 24, WAN 2.2 16 ([GeCo](https://arxiv.org/abs/2512.22274) appendix). Seedance reference videos must be 24 to 60 fps (BytePlus) |
| Interpolation | Never to change frame rate. If a 30 fps master is forced, repeat frames with `fps=30` [inference]. Our one exception: a shot deliberately being slowed [inference] | Eian bans interpolated slow motion ([post](https://x.com/EianLu/status/2117469941364637983) [self, translated]). Dave Clark retimed through Topaz, then slowed in post ([Every](https://every.to/podcast/transcript-how-a-hollywood-director-uses-ai-to-make-movies) (not re-checked) [self], Gen-2 era) |

## Finishing order

1. Generate, with the settings above.
2. QC raw: `take_check.py` on the original, text scan.
3. Conform a mezzanine.
4. Select takes pairwise (practices.md #14) and lock the edit with handles.
5. Upscale only selected ranges plus handles; skip for 1080p social [inference]. Or regenerate: drafts-and-takes.md.
6. Matte and track on the upscaled plate, since the upscaler redraws edges [inference]. Proxy tracks are untested.
7. Neutral correction, then grade.
8. Graphics integrated into the scene, at final resolution; never upscale graphics [inference].
9. Unifying pass and grain over plate plus integrated graphics, seeded by frame number.
10. Untreated top layer for captions and logos (`footage-effects`, practices.md #6).
11. Encode at CRF 16 or below if grain is present (`footage-effects`).

"upscale first on the raw ungraded footage", with grain last, is vendor advice with no tests
([invideo](https://invideo.io/faq/what-is-the-correct-post-production-order-for-ai/) [vendor]). The rest of the order is
ours [inference]. **No published test covers upscale before or after matting.**

## Coverage

Script, previz and audio are locked, so this needs less than a live shoot. How many to generate per run is in
drafts-and-takes.md; this is what should reach the edit. **No editor source gave a number for "enough".**

| Item | Do | Evidence |
|---|---|---|
| Takes | 2 on normal shots, 3 to 4 on heroes and the first 3 seconds, about 3 times generated seconds against final seconds. Log rejected takes with a reason too | [inference], thin: a vendor FAQ and one recipe |
| Safety inserts | 1 or 2 per scene: hands, prop, environment, reaction | "You need cutaways for every single scene you shoot." ([shooting guide](https://sites.google.com/vice.com/digitalvideo/shooting-guide/production), VICE, publisher inferred from the URL). The count is ours |
| Clean wide | One per location, doubling as clean plate and title background. Generate it with no subject in the action. Plan a graphics-free take for shots with an end card or data panel | Lazarov shoots a blank plate [self]. **`remove-background --background-output` is not a clean plate**: its plate "has a transparent hole" (`media-use` skill) |
| Handles | At least 12 frames head and tail on single-shot runs, by extending the previz shot past its in and out. Motion is already under way at frame 1; keep the key moment away from both clip ends | "some extra frames, called handles, should be present at the head and tail of each shot" ([OTIO](https://opentimelineio.readthedocs.io/en/latest/use-cases/animation-shot-frame-ranges.html)). **No opened source gives a count; 12 is ours, untested.** Eian generates 4 to 5 s, keeps 2 to 3 s, main action in the first 3 s ([post](https://x.com/EianLu/status/2117469941364637983) [self, translated]). How first and last frames settle is unmeasured |
| Multi-shot runs | Use only where the cut is pinned to locked audio (sound-sync.md). Extending later (`minimax_h3_max_extend`, fal Seedance `task: extension`) is a new generation that may not match | No spare frames at interior cuts [measured, one film]. Extension untested |

## The sidecar

**No standard manifest exists. This sidecar is ours [inference]; nothing in it is an existing standard.** Keep one
`<shot>.<take>.json` next to each clip, shaped like `../assets/take.example.json` (values are illustrative). Record what
a later agent cannot cheaply recompute.

`python3 scripts/take_check.py <take.mp4> [--plan 0,2.5,5] [--reference previz.mp4] [--json]` fills `tech` and lists
cuts from keyframes.

| Block | Holds | Notes |
|---|---|---|
| top level, `source` | `shot`, `scene`, `run`, `take`, `rank`, `rank_reason`; `url`, `job`, `route`, `prompt_sha`, `seed` | `rank_reason` copies the `reason` idea in [video-use's EDL](https://raw.githubusercontent.com/browser-use/video-use/main/SKILL.md) |
| `tech` | Helper output | `keyframes` in seconds, as the helper reports them |
| `timeline` | `edit_in`, `edit_out`, `head_handle`, `tail_handle`, `interior_cut_head` | Frames from 0, `edit_out` exclusive. `interior_cut_head` is true when the head sits on a cut inside a multi-shot run. In HyperFrames handles map to `data-media-start` (`hyperframes-keyframes` skill) |
| `camera` | `planned`, `measured`, `matches_previz` | Planned from the previz, measured from the output |
| `post` | `free_rects`, `no_pin_ranges`, `track` | `rect_pct` is x, y, w, h in percent of frame, field order ours. `track` holds the gate numbers |
| `qc` | `text_scan`, `passthrough`, `faces_ok` | One run returned the previz re-encoded ([seedance-v2v.md](https://github.com/vargHQ/skills/blob/main/varg-previz/references/seedance-v2v.md)): check with `--reference` |

`free_rects` with luma is the most useful field: `hyperframes/references/captions.md` picks text blending by brightness
behind it. A prototype took 0.09 s CPU for 4 s of frames [measured, prototype not validated against faces or text].

OTIO mapping, ours: `source.url` to `ExternalReference.target_url`; `tech.frames` at `tech.fps` to `available_range`, the
whole file; `edit_in` and `edit_out` to `Clip.source_range`, so handles are the gap between the two; beats, if you add
them, to `Marker`; everything else to `metadata.varg`, since the docs define no per-frame rectangles or take ranks.
Alternate takes as `media_references` with `active_media_reference_key` are our reading of a field list: **verify first**.
Docs: [structure](https://opentimelineio.readthedocs.io/en/latest/tutorials/otio-timeline-structure.html),
[schema](https://opentimelineio.readthedocs.io/en/latest/tutorials/otio-serialized-schema-only-fields.html).
