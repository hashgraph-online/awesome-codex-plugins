# Drafts, run lengths and takes: where the credits go
`[vendor]` = company selling or reselling it, or a paid partner; `[self]` = one person's own report; `[measured]` = varg's own measurement, usually one film; `[inference]` = our reasoning, nobody tested it; no tag = opened primary source (docs, standard, paper, book).

Decides what to generate cheaply first, what that pass can approve on varg today, upscale or regenerate, run length,
how runs join, how many takes to roll, when to stop, and what a 60 s film costs. Prices are in credits, checked
2026-11-03. Confirm every price with `estimate_cost` before spending.

## Cheap first: what Draft mode binds and a plain 480p run does not

Draft mode is a Seedance 2.5 feature. A 480p draft validates "the scene structure, shot scheduling, subject motion,
and prompt intent"; a final is then generated from its task ID, reusing model, prompt, inputs, seed, audio, ratio and
duration "to generate a consistent final video" (BytePlus, https://docs.byteplus.com/en/docs/modelark/seedance-2-5).
The word is consistent, not identical, and BytePlus gives no match guarantee.

| Check | Draft, then final from the task ID | Plain 480p, then a new run at higher resolution |
|---|---|---|
| 480p cost | "The token consumption and token rate for a 480p Draft video are the same as those for a normal 480p video." (BytePlus) | The same |
| Does the shot carry? | Blocking does: frame correlation 0.950 to 0.988 on 5 clips, one cut on the same frame in both (Segmind, https://blog.segmind.com/seedance-2-5-draft-final-5-clips-tested-and-the-real-cost-math/ [vendor]). SSIM 0.79, "close, but not a copy" (AiuniVid, https://aiunivid.com/en/blog/seedance-2-5-draft-mode [vendor, one run]) | No: a direct 1080p control scored 0.257 against the same draft (Segmind); a fresh 1080p scored 0.62 (AiuniVid). "These are not the same shot at two sizes." (Segmind, https://blog.segmind.com/advanced-seedance-2-5-prompts-5-expert-patterns-tested-2026/ [vendor]) |
| Seed | Reused by the final | It "did not carry the composition across a resolution change." (Segmind). Softer, one run: "The same seed did not give an identical shot at each resolution." (Krea, https://www.krea.ai/blog/seedance-2-5-draft-mode-extend-reframe-guide [vendor]) |
| Final | 1080p only per BytePlus and fal; one provider adds 4K (https://docs.oxen.ai/inference-api/reference/models/walkthroughs/seedance_2_5_draft_mode [vendor]). IDs created from 2026-10-28 last 14 days, older ones 7 (BytePlus); guides saying 7 are stale | Any resolution, as a new take |

| Question | Answer |
|---|---|
| Judge at 480p | Staging, camera, cut timing, shot order [inference, from BytePlus's list] |
| Do not judge at 480p | Faces, hands, small text, logos. Fine print "is a smear in the draft" (AiuniVid); a small preview may hide "hand, face, text, or audio defects" (https://anikuku.com/blog/seedance-2-5-draft-mode-cost-guide [vendor]); a logo changed in an otherwise 90 to 95% match (https://x.com/AI__TSUBAKI/status/2116843344399937692 [self]) |
| Warning on the numbers | Segmind's metric is 64x64 greyscale, so it shows blocking matched, not that a face stayed the same person [inference]. AiuniVid's is SSIM on luma; the two do not contradict. Vendor claims of an exact match (Picsart [vendor]) go further than either test |
| Not tested by anyone found | Identity between draft and final. Draft to final on video-to-video from a previz (Segmind's five clips were text prompts). No Draft-style binding was found for Kling 4, Veo 3.1 or Wan 3 |

## What varg can do today

**varg has no Draft mode today, so nothing on varg binds a 480p take to a final.** The public schema has no `draft`
field (checked 2026-11-03, https://varg.ai/models/seedance_2_5.md). `provider_options.byteplus` and
`provider_options.piapi` reject unknown fields, so passing `draft` by hand fails. `provider_options.fal` has a seed,
but no source shows one surviving a resolution change.

A plain 480p run is a motion and blocking test. Its approved take has two futures. Pick one per shot [inference]:

| Future | Do | You keep | You accept |
|---|---|---|---|
| Upscale | Roll the full take count at 480p, because this take is the final take. Lock the edit, then upscale the chosen range plus handles | The approved pixels and performance | Soft detail, and 480p to 1080p has no independent test |
| Re-roll | 1 take per run at 480p is enough, because the acting does not carry. Then the same `@video1`, references and prompt at 720p or 1080p. Log it as a new take and judge it from zero | Blocking and cuts, carried by `@video1`. Measure cuts again: they came back exact or one frame early in our 4 to 12 s runs at 480p and 720p [measured, one film], and no test compares a 480p and a 1080p `@video1` take | New performance, faces and texture, at full take prices |

- Never promise that an approved 480p take comes back at 1080p. Quote and schedule a re-roll as new takes [inference].
- Warning: "the motion is basically identical" (https://x.com/0x_fokki/status/2115445231923421451 [self]) is
  unmeasured; Segmind's controls say otherwise.
- Kling 4 has no seed on varg: treat a 1080p rerun of a 720p take as a new take [inference]; no test exists.

**If Draft ships** (re-read the schema first; steps are ours [inference]):
1. Send every Seedance 2.5 attempt in Draft mode at the full take count: it costs the same as plain 480p and the
   chosen take now carries. Finalize from the task ID and log the ID with the take. ID expired: upscale.
2. Before committing a film, run one video-to-video draft-to-final check. Nobody has published one.
3. Check faces, hands and small text at 1080p and budget a re-draft for failures. Finalizing one ID twice billed twice
   and correlated 0.9999 (Segmind), so a second finalize is unlikely to fix a face.

## Upscale or regenerate

| Shot | Call | Evidence |
|---|---|---|
| Mid-size text, tight faces, dense texture | Native generation at final resolution | 15 to 25 px text came out readable but ragged; crowd faces got "a slightly waxy finish" at 600% zoom, not at normal size (Segmind, https://blog.segmind.com/seedance-2-5-upscaled-vs-native-1080p-side-by-side/ [vendor], 13 renders). It names tight faces as a place native earns its price, yet upscales people in medium or close framing |
| Stylised or medium shots | Upscale | Medium shots and large text tied, at under half the price per 5 s on Segmind's platform |
| 1080p to 4K; a Draft ID that expired, once Draft ships | Upscale | No native 4K route apart from one provider's final; expiry is our call [inference] |
| Text around 10 px in the plate | Neither. Move it to a code layer, see routing.md | Failed on both. "A 4K upscale cannot fix a letter the generator never drew." (Segmind) |
| A 480p source | Upscale one real shot and check it full size before committing the film [inference] | Segmind's test covers a 720p render plus AI upscaler, on a model not on varg's price list. No independent test covers 480p to 1080p |
| Practitioners split | Test your own shot | Heydin upscales 480p with Topaz Astra (https://x.com/heydin_ai/status/2116615425010381222 [vendor, #Ad]); @MANISH1027512 ships 480p, plain upscale and grain, on a look that suits it (https://x.com/MANISH1027512/status/2117153429894361174 [self]); Nezko2026 found ByteDance's 480p upscale unnatural (https://x.com/Nezko2026/status/2117595141649404326 [self]); Pryce: "No, there wasn't any upscaling involved." at 720p (https://x.com/second_bassoon/status/2117703324321694077 [self]) |
| Faces you must keep | No generative upscaler | "Generative models rewrite facial features enough to alter who a person appears to be." (https://theairankings.com/best-ai-video-upscalers/ [self], no published test protocol) |
| Every upscale | After the edit, so handles are not billed [inference]; order in post-ready.md. Ask `estimate_cost` for the price | No head-to-head of upscalers on AI footage was found. varg lists Sima from 15, ByteDance 25, SeedVR 30 and Topaz 50 credits per run, no duration basis stated |

## Long or short: harvest or obey

Nobody has published a decay curve for Seedance 2.5, Kling 4, Veo 3.1 or Wan 3. The evidence points to beats, not
seconds: Seedance 2.5 "reliably delivers about three strongly distinct beats per generation" and past that "tends to
do the first few well and then drift through the rest." (Krea, https://www.krea.ai/blog/seedance-2-5-prompt-guide
[vendor]). Length disputes are two jobs; no controlled test on video-to-video exists. Table is ours [inference]:

| Job | Generate | Why |
|---|---|---|
| Harvest: coverage, dialogue, a take you will cut up | 15 to 30 s, 2 to 4 beats | Only the best seconds must work, and retakes need no match. Shimura's 30 s clips reached the screen at 32.2%, 5 s clips at 3.3%: his cuts average 2.5 s and a clip's first 4.5 s is usually near-static and thrown away (https://x.com/ucmulleryu/status/2092572054872784904 [self]). His count is unpublished, so tenfold is an upper bound |
| Obey: previz-locked or audio-locked timing | 4 to 11 s (varg's working range, no published threshold), about 3 strong beats | Motion stays obedient and a retake is cheap. "short generations hold a performance better than long ones" (Chris Capel via PJ Ace, https://x.com/PJaccetturo/status/2116160709180723486 [vendor, Dreamina partnership]), who also runs 20 to 30 s coverage passes |
| Same location and light, shots that read together, no cut will move | One multi-shot run | Light and identity hold with no matching work |
| New location or light, likely many retakes, a cut the edit may move | Separate run | Hidden cost of multi-shot: interior cuts have zero handles, because a run gives no spare frames past a planned cut [measured, one film] |
| Prepared oner, in-camera transition in one world | One generation, "No cuts", timed segments, about 10 to 15 s | Beyond that, odds fall quickly |
| Transition between two worlds | Two generations with a designed join | A morph inside a clip fails, see below |

| Check each run | Evidence |
|---|---|
| Split by location and light state, not by shot. Name the place exactly | Production prompts hold 5 shots in 10 s (https://x.com/PJaccetturo/status/2116160701400289449 [vendor]). "A vague location is the most common reason a multi-shot sequence starts drifting between cuts." (https://higgsfield.ai/blog/seedance-2-5-prompting-guide [vendor]) |
| More than about 3 strong beats: split. Give each shot a time budget | The model front-loads: unbudgeted cuts landed at 6.08 s and 11.54 s of 15 s; with budgets, shots ran 4.88, 5.16 and 5.03 s (Segmind [vendor]) |
| Stage what each beat shows; do not rely on the words "hard cut" | "Beats left unstaged with only "HARD CUT" between them usually come out as soft morphs rather than real cuts." (Krea [vendor]) |
| With a previz, skip the coverage pass: one generation per shot from a locked frame or `@video1` [inference] | Chris: "Shots from different runs still match, because they all come from frames of the same coverage pass." [vendor]. The previz already fixes the angles |
| Cut every 3 to 5 shots together to feel pacing before spending more | https://x.com/binghe/status/2116785718093873270 [self]; the same pipeline finds 480p shows weaker logic than 720p |
| Do not ask one obedient run to do three runs' work | Retake arithmetic [inference, assumes independent failures; the 1 in 3 is illustrative]: if a 10 s segment succeeds one time in three, three separate segments need about 90 s, about 1,170 credits at 13 credits/s. A 30 s take needing all three right has odds of 1 in 27, about 810 s or 10,530 credits, nine times more. Harvesting removes the penalty |

## Oners and in-camera transitions

A true oner cannot be harvested, so its expected retake cost is highest. Three routes work; none has been compared.

| Route | Do | Evidence |
|---|---|---|
| One generation | Open with duration, one continuous shot, first frame and where the last frame lands; distances and lens as numbers; timestamped blocks | https://x.com/ZentrixHQ/status/2105339471763767447 [self]. "No cuts" held at 8 s and 20 s, with two timed instructions softer than written (Segmind, Krea [vendor]) |
| Previz camera path through video-to-video | Keep moves simple; split long oners by plan | A 15 s free-fall oner with "camera start and framing come from Video 1", split as 15 s plus 5 s (https://x.com/EEJ_OOXO/status/2108791208042766549 [self]). "Motion carries over from a video reference much better than it does from text." (Chris [vendor]) |
| Extension with a stated handoff | Use a keyword such as "extend" or "continue" (BytePlus); say whether the handoff is continuous or a hard cut | https://x.com/gensoFX/status/2117263127503048964 [self] |
| Transition inside one world | "clearly specify both the trigger point and the transition method", such as a left wipe at the 5-second mark | https://docs.byteplus.com/en/docs/modelark/seedance-2-5-prompt-guide |

| Rule | Why |
|---|---|
| Up to about 10 to 15 s, one generation. Beyond that, two generations with the join on a whip, wipe or foreground pass | Ours, untested [inference]. Our camera and cut measurements cover 4 to 12 s runs only |
| No morph inside a clip that takes tracked graphics, and no in-camera cut there either | In our tracking test an orbit with a morph kept 0% of tracked points [measured, one test]. A morph inside a clip "read as slop" on one of our own films (our judgement). A track restarts at every cut [inference]. See post-ready.md |
| Check every oner for hidden cuts: scene detection at threshold 0.2 to 0.3 | As Segmind and Krea did. On Kling 4, 30 s "does not guarantee an uninterrupted take" (https://dev.to/dong_chenguang_2cbe5a1770/kling-40-review-long-takes-faster-motion-and-a-better-way-to-use-references-2h1f, reviewer close to a vendor [vendor]) |
| Do not budget from 30 s oners on X | https://x.com/xIrissy/status/2100511965840109644, https://x.com/Viniai_/status/2100432565517824407 [self] state no retake counts and are best-of selections. No hit rate is published |

## Joining runs, ranked

Only the bottom row is firmly ranked by the sources. The order above it is ours [inference]; no seam test exists.

| Rank | Join | Do | Evidence |
|---|---|---|---|
| 1 | No join: one run for one world | Merge shots of one location and light state | Two 5 s runs merged into 10 s cost the same on per-second billing and lose a seam [inference] |
| 2 | Hard cut between separate runs sharing references | One generation per shot from a locked frame or `@video1` | Chris (above [vendor]) |
| 3 | Designed join on a whip, wipe or foreground pass | Design it into the previz; do the whip in post, see cinema.md | "a moving camera or a strong foreground action" hides a join (invideo, https://invideo.io/faq/why-do-the-first-frames-of-an-ai-extended-video-clip/ [vendor]) |
| 4 | Extension with a stated handoff | Trim the head (below). Backward extension can bridge into an existing clip | https://x.com/DesignSorceress/status/2095433062855135316 [self, says seamless]; forward and backward per BytePlus |
| 5 | Last-frame chain, seed frame taken early | Take the seed frame before the final 10 to 15% of runtime. `return_last_frame` on the BytePlus route returns the frame this avoids [inference] | Re-chain attempts fell "from four down to one" on one sequence (Houbre, https://hackernoon.com/how-to-chain-ai-video-clips-into-one-shot-without-the-hidden-stutter-at-every-cut [self]) |
| 6 | Bare last-frame chain, left unattended | Avoid | "The quality kept getting worse" (https://x.com/alex404/status/2102011956802576832 [self]). By the fourth or fifth clip "character appearance has shifted subtly, lighting has changed tone" (https://www.ngram.com/blog/seedance-2-5-native-30-second-ai-video [vendor]) |

| Seam or handle | Rule | Source |
|---|---|---|
| End-of-clip stutter | Check every chained tail: models "ease the camera and the subject toward stillness" at the end, usually the final 10 to 15% of runtime | Houbre [self] |
| Tail, per run | 0.5 to 1 s; 10 to 15% of runtime when chaining. 1 s per run on 6 runs at 3 takes is 18 s, about 234 credits [our arithmetic] | Ours, untested [inference]. "If the shot calls for four seconds of usable motion, generate five or six." (Houbre [self]) |
| First two frames of an extension | Trim them: they can be errors, and usable motion starts at frame three | invideo [vendor], written about Seedance 2.0 |
| Normal run, both ends | Start the first beat at 0 s rather than paying for a ramp: "ALREADY SPEAKING his line in the very first frame". If the cut may move, keep that motion running through the head handle (post-ready.md). Give the last beat an end time, or it "tends to get cut off when the shot ends" | Chris, https://x.com/PJaccetturo/status/2116160706387362235, https://x.com/PJaccetturo/status/2116160709180723486 [vendor] |
| Frame counts | None sourced. Handles are standard post practice, but no opened source gives a number | https://opentimelineio.readthedocs.io/en/latest/use-cases/animation-shot-frame-ranges.html |

## Takes: vary the performance, nothing else

"3 takes that differ only in timing and camera" is documented nowhere we searched, and cannot be done literally on a
generative model: "Everything it left to the model was re-rolled." (Segmind [vendor]). It is true for deterministic
renders, so it moves to the previz:
1. Make timing and camera variants in the previz, where they are free and exact. Pick one with the person.
2. Lock it as `@video1`. Roll 3 generative takes with the same `@video1` and references, and change at most the one acting clause (prompts.md, case 6), so that "the only
   thing changing between attempts is the performance" (Chris [vendor]).
3. To steer the acting, change one clause: "Change one thing per iteration." (Chris). Log which take won and why.

| Shot, by how much is locked | Takes per run | Source |
|---|---|---|
| Fully rendered image inputs match a frame of the previz | 1 to 3 | https://x.com/fatboypink/status/2070580437429149863 [self] |
| Previz-locked, ordinary: **the opening budget** | 3 | Our call; Shimura compares 3 takes with 1 (https://x.com/ucmulleryu/status/2091821264302412030) and batches 5 per command (https://x.com/ucmulleryu/status/2092229428646719949) [self, translated] |
| Acting or physical contact | 5 to 7 | "It took 5-7 tries each to get the clips that were ultimately selected" (Pryce, above [self], no previz) |
| Blockout shots, performance unlocked | 5 to 25 | https://x.com/reidhannaford/status/2071939853755756819 [self] |

Budget by difficulty, not runtime. The range tracks how much is locked, up to 20 to 27 with little locked (PJ Ace,
2025, https://x.com/PJaccetturo/status/1932893273376579745 [self]). "Usable" differs across sources, so no count
compares directly. varg's Kling skill plans 2 to 4 per beat and does not say what varies.

**Stop rule.** Same failure twice: stop rolling and change the shot. "if a shot fails the same way twice, I split it
or build it in Blender" (https://x.com/Trevsthinktank/status/2117260089799434616 [self]). Four failed batches traced
to a source clip that lacked the moment (https://higgsfield.ai/blog/ai-vs-vfx [vendor]).

Shimura's numbers (10-minute two-person pilot, self-reported, counting method unpublished): 991 cuts made, 152 on
screen; 2,288 takes, 160 used (https://x.com/ucmulleryu/status/2091358648392200328), so 7.0% of takes and 15.3% of
generated cuts reached the screen [inference, arithmetic]. Cuts given 3 takes got there at 22.3%, given 1 take at
8.8%. His correction: volume alone does not hit; locking camera and timing beforehand changes adoption substantially
(https://x.com/ucmulleryu/status/2091706394307408073, our translation).

## Budget ladder for a 60 s film

All numbers are our arithmetic [inference]; nobody has run this. 6 runs of 10 s plus a 1 s tail, 66 s per pass, previz
as `@video1`, Seedance 2.5 on BytePlus. Credits per output second with the same seconds of clay in: about 13 at 480p
(our estimate, not verified on a live clay job; confirm with `estimate_cost`), 27.8 at 720p, 68.4 at 1080p.

Rungs: previz variants generate nothing. One 6 s test run at 480p: 78. At 480p, 66 s x 13 = 858 for 1 take per run,
2,574 for 3, 4,290 for 5. One more take of one run: 143 at 480p, 306 at 720p, 752 at 1080p.

| Path to a finished 60 s | Credits | Per kept second |
|---|---|---|
| **Today:** test run, 3 takes at 480p, upscale the chosen 66 s at about 12 credits/s | 3,444 | 57 |
| **Today:** test run, 1 take at 480p for blocking, then 3 new takes at 720p / 1080p | 6,440 / 14,479 | 107 / 241 |
| **Today:** direct 720p / 1080p, 3 takes, no 480p pass | 5,504 / 13,543 | 92 / 226 |
| **Today:** direct 1080p, 5 takes, no 480p pass | 22,572 | 376 |
| **If Draft ships:** test run, 3 / 5 takes at 480p, final at about 35 credits/s, no clay billed (see Draft final rate) | 4,975 / 6,691 | 83 / 112 |
| Kling 4 stills and harvest, 4 beats of 30 s, 3 takes, about 300 credits of stills: direct 1080p (705 per 30 s) / 720p (471 per 30 s) with one 1080p rerun per beat, which saves nothing and is not locked to the take | About 8,760 / 8,770 | 146 |

| Limit | Read it as |
|---|---|
| Upscale rate | Starlight on fal, 13 Sept 2026, assuming a 30 fps source, from a third-party listing (theairankings, above), not a varg price. Astra 2 at about 30 credits/s makes that path 4,632. It rests on the unproven 480p to 1080p step. Against the Draft path it saves about 1,500 credits, more if finals bill clay, and gives up regenerated detail, so once Draft ships the case for it is budget or expiry, not routine quality [inference] |
| Draft final rate | Read from Segmind's table, not measured, and that table has finals billing no reference seconds. BytePlus says otherwise for its own API: for a final, "the input video duration is calculated based on the input video in Step 1" (https://docs.byteplus.com/en/docs/modelark/seedance-2-5). On clay shots budget about 68.4 credits/s, or 7,166 / 8,882 on the Draft rows [inference]. varg's rate is unknown. Segmind's own arithmetic on text and image input: 18% more at 1 take, break-even at 1.22, then 32%, 49% and 62% less at 2, 3 and 5 takes ("Not cheaper video: cheaper mistakes." [vendor]). Its table reads direct 1080p at 70.38 credits/s, or 13,935 against the 13,543 above |
| Blocking pass | Adds 936 credits: 7% on 1080p, 17% on 720p. One run lost at 1080p with 3 takes costs 2,257, more than the whole pass |
| Route | PiAPI routes cost about double every Seedance row (124, 289, 660 per 5 s against 64, 139, 342), and no route may carry a real person's likeness without consent. Confirm the BytePlus route is live before planning on it |
| Billing | BytePlus has minimums for video input (anikuku [vendor]) and clay seconds bill on Seedance. Older varg files say 16 credits/s, which predates pass-through pricing [inference]. varg's own reference treats `estimate_cost` as a ceiling: it quoted 361 credits for a 9 s job billed 145. Quote and approve each batch before running it (https://x.com/EianLu/status/2117469941364637983 [self]) |
| Contingency, not counted | Add 10 to 20% for shots that fail the face and hand check at final resolution: a judgement, not a measurement. Not counted: character stills, lip sync (`sync_v3`, from 100 credits), sound, code layers |
| Cheaper storyboard | `minimax_h3_max_turbo` 480p at about 13 credits per 5 s, about 172 for 66 s (https://x.com/tapehead_Lab/status/2109576509690462555 [self]). It predicts blocking, not Seedance's performance |
| Per-shot routing | The largest saving on record: a 95 s film for 1,188 credits against about 8,700 if all Seedance 2.5 at 1080p (@MANISH1027512 [self]; his credit unit is not stated in what we read, so do not take them as varg's). See routing.md and models.md |
