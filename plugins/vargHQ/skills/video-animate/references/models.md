# Models: Seedance 2.5 by default, five cases elsewhere

Decides the model, the route and the credit budget for each shot once the previz is approved. Seedance 2.5 goes first
where a performance has to read, and the route moves the price as much as the model does.
`[vendor]` = company selling or reselling it, or a paid partner; `[self]` = one person's own report; `[measured]` = varg's own measurement, usually one film; `[inference]` = our reasoning, nobody tested it; no tag = opened primary source (docs, standard, paper, book).

Ids, limits and routes were read from the [live specs](https://varg.ai/models/llms.txt) on 2026-11-03; where one
disagrees with our research, the spec wins and the line says so. Credits were checked the same day, none on a paid
request: confirm each shot with `estimate_cost`. "Clay" means the previz exported as a plain, untextured video.

## Shot to model

Why Seedance: its vendor documents a full clay workflow ([BytePlus guide](https://docs.byteplus.com/en/docs/ModelArk/2607689)), as fal does for H3 3D to Video (case 2), and it leads Film, Ads, Animation and
Motion Design on [OpenArt](https://openart.ai/arena) [vendor, blind votes, also resells] and [AA image-to-video](https://artificialanalysis.ai/video/leaderboard/image-to-video) at 1157. Kling 4 is on neither.

| Shot | First pick | Fallback | 5 s credits | Strength and evidence |
|---|---|---|---|---|
| Complex camera or exact blocking, characters on screen | `seedance_2_5` reference with clay | `minimax_h3_max_3d_to_video` | 139 (BytePlus 720p, clay in) | Strong: BytePlus guide; same blocks, two prompts, 480p, "Pillars, the train, her path, the camera. Same in both." ([girafframe](https://x.com/girafframe/status/2115464164823171151) [vendor], sells a previs tool); [PJ Ace](https://x.com/PJaccetturo/status/2116160709180723486) [vendor], [Adam James Hill](https://x.com/adam_james_hill/status/2115158642617983124) [self] |
| Environment, vehicle, prop from previz, no faces, up to 15 s | `minimax_h3_max_3d_to_video` | `seedance_2_5` 480p | 105 (768p) | Medium, no head-to-head: [fal](https://x.com/fal/status/2102879559104237764) [vendor], [taziku on Justine Moore's test](https://x.com/taziku_co/status/2103627081167077462) [self] |
| Approved stills that must not change | `kling_v4` keyframes, up to 10 | `flux_3_max` keyframes; `seedance_2_5` first + last | 79 (720p) | Medium: [Workman](https://x.com/mattworkman/status/2116204462263910473) [vendor], [NOBU](https://x.com/nbykos/status/2117136627709673886) [self, translated] |
| Hero photoreal human | `seedance_2_5` through a sanctioned face route (see Moderation) | `kling_v4` from finished stills | 342 (BytePlus 1080p, clay in) | Medium: [Alpha Mom](https://x.com/YourAlphaMom/status/2116635769729323171) [self], AA image-to-video #1 |
| Dialogue coverage, several angles | `seedance_2_5` coverage pass, then one generation per shot | `kling_v4` multi-shot | 323 per 30 s at 480p, no clay | Medium: PJ Ace [vendor], [Monique Pryce](https://x.com/second_bassoon/status/2117307653320007954) [self] |
| Lip sync to the locked track | Generate, then `sync_v3` with the locked slice | `minimax_h3_max` image route with `target_audio_url` (at least 2 s); `minimax_h3_max_lipsync` | Generation + from 100 | Medium: [Ozan Sihay](https://x.com/ozansihay/status/2117667049304396155) [self, translated], [CellCog test 8](https://cellcog.ai/blog/seedance-2-5-vs-kling-4-0/) [vendor] |
| Fights, physical contact | `seedance_2_5` | `kling_v4` for energy over control | 116 (BytePlus 720p, no clay) | Medium, reseller bias: [Farhad Nassiri Afshar](https://x.com/DrNassiriAfshar/status/2116976466558914644) [self], [JSFILMZ](https://x.com/JSFILMZ0412/status/2115828158335222058) [self], [Ima Studio](https://x.com/ImaStudio_ai/status/2115330094319202809) [vendor] |
| Anime, cartoon, stylised | `seedance_2_5` with the style named | `minimax_h3_max_style_*`; `kling_v4` on a copyright refusal | 116 | Medium: OpenArt [vendor], [Akira Tanaka](https://x.com/MartianWarStory/status/2117120879620678062) [self], [CellCog faces](https://cellcog.ai/blog/seedance-2-5-face-likeness-character-consistency/) [vendor] |
| Product hero, hands on product | `seedance_2_5` | `kling_v4`, `minimax_h3_max` for volume; titles in the edit | 116 | Medium: CellCog test 1 [vendor], [Everypixel](https://journal.everypixel.com/kling-4-vs-kling-3) [vendor] |
| Long take, 15 to 30 s | `seedance_2_5`; split where you can | `kling_v4` | 835 per 30 s + 30 s in; Kling 471 per 30 s | Medium: CellCog test 9 [vendor], 33 to 32; [BudgetPixel](https://x.com/budgetpixel/status/2117087946440429863) [vendor] |
| Seamless move between two designed frames | `kling_v4` start + end, chained | `seedance_2_5` first + last | 79 | Medium: [varg notes](https://github.com/vargHQ/skills/blob/main/varg-video-prompting/references/models.md) [measured], not independently checked; CellCog test 6 went to Seedance [vendor] |
| Blocking and motion tests | `seedance_2_5` 480p with clay, or `minimax_h3_max_turbo` 480p as a moving storyboard | `wan_3` 480p | 64 or 13 | Medium: [FoldingEnd](https://x.com/EndFolding79421/status/2107800213708517546) [self], [Leohuan](https://x.com/leohuanfang/status/2116161074391031919) [self] |
| Edit an existing clip | `wan_3` | `omni_flash_1_1` (3-10 s); `seedance_2_5` edit | 50 | Medium: [AA editing](https://artificialanalysis.ai/video/leaderboard/video-editing), OpenArt [vendor] |
| B-roll without previz | `wan_3` | `heygen_video_1`, `flux_3_max` | 50 | Medium: [AA text-to-video](https://artificialanalysis.ai/video/leaderboard/text-to-video) |
| Locked-camera product loop | `pixelcut_looping_video` | `minimax_h3_max` 480p | from 40 | Weak: catalog, [fal H3 Max guide](https://fal.ai/learn/tools/how-to-use-minimax-h3-max) [vendor] |
| Performance from a real actor's video, with their consent | Runway Act-Two or Luma Ray3 Modify, neither on varg | `minimax_h3_max_recast`; `kling_v3_pro_motion_control` (from 504) | 150 (recast 768p) | Weak: [Runway pricing](https://academy.runwayml.com/models-pricing), [Runware on Ray 3.2](https://runware.ai/docs/models/luma-ray3-2/guides/editing-video) [vendor] |
| Thrown object; close-up hands; crowds | Object: `kling_v4`. Hands: no settled pick; short shot, frame around the hardest contact, fix locally [inference]. Crowds: `seedance_2_5` with crowd paths in the previz [inference] | Object: `seedance_2_5`. Crowds: `kling_v4` | 79 for the object | Weak: pancake arc 40 to 36, one take, CellCog test 3 [vendor]; no hands benchmark found; crowds are anecdotes ([rewind](https://x.com/rewind02/status/2110774943294070795) [self], PJ Ace [vendor]) |

The picks are our synthesis [inference]: no named expert publishes a routing table. Strong = official guide plus two
named tests; Medium = official guide or several named posts; Weak = one or two anecdotes. Seedance credits are BytePlus:
if it is not live, budget about double with clay, 1.7 to 1.8 times without. Live spec over our research: Turbo takes
only `image_url` and `end_image_url`, so it cannot read the clay; a different model also says little about Seedance's performance [inference].

## The five cases that point away from Seedance [inference]

| # | Case | Go to | Evidence and what to check |
|---|---|---|---|
| 1 | References it will refuse | Moderation below | "Seedance 2.5 does not support directly uploading reference images or videos containing real human faces." ([BytePlus tutorial](https://docs.byteplus.com/en/docs/ModelArk/2607688)) |
| 2 | No faces and the budget matters | `minimax_h3_max_3d_to_video` | Built for Blender video up to 15 s and 32 shots ([spec](https://varg.ai/models/minimax_h3_max_3d_to_video.md)). Composition is said to hold (taziku [self]); exact geometry, camera paths and motion are "not guaranteed" ([fal](https://fal.ai/models/minimax/h3-max/3d-to-video) [vendor]). Beats BytePlus Seedance on price from 720p up, not at 480p (90 against 64) |
| 3 | Approved finished stills | `kling_v4` keyframes | "Kling 4 Ref2Video REALLY wants fully finished still frames and you can have LOTS of them" (Workman [vendor]). Keyframes beat omni reference, which feels stiff (NOBU [self, translated]). Keyframes mode takes no other assets ([Kling guide](https://kling.ai/quickstart/kling-4-model-user-guide)). Sheets split opinion: "Seedance style Ref2Video (character sheets, location reference, prompt) doesn't work very well" (Workman); a reply says a turnaround sheet fixed drift at 20 s ([MegaSaturn](https://x.com/MegaSaturn/status/2117287193345720468) [self]) |
| 4 | Editing an existing clip | `wan_3` | First on AA editing at 1196, Seedance 2.5 tied second at 1152. On OpenArt the gap is one point, 1080 to 1079 [vendor]. Also cheaper: 50 against 116 at 720p, no clay |
| 5 | Cheap B-roll with no previz | `wan_3` | First on AA text-to-video, at a fraction of Seedance's price |
| | Wan 3 on clay shots | Avoid for now [inference] | Unstable on a three.js previz over two days ([Akakumaya](https://x.com/akakuma0219/status/2115731605998190994) [self, translated]). Prompt rewriting, on by default, changed the scene for the same seed ([Segmind](https://blog.segmind.com/wan-3-prompt-guide-alibabas-official-formulas-tested/) [vendor]); the live spec says turning `provider_options.fal.enable_prompt_expansion` off is "likely to degrade generation quality", so test it on your shot [inference] |
| | Veo 3.1, Runway, Luma; locked audio | Not picks; not a sixth case | Veo 3.1 takes no external video, runs 4, 6 or 8 s and sits at #21 on AA image-to-video ([Google](https://aistudio.google.com/docs/veo)). Runway and Luma are not in the live catalog. Seedance re-performs an audio reference, so plan a sync step on any route (sound-sync.md) |

## Route prices: 5 s out plus 5 s of clay in

| Route | 480p | 720p or 768p | 1080p |
|---|---|---|---|
| `byteplus:dreamina-seedance-2-5-260628` | 64 | 139 | 342 |
| `piapi:seedance-2.5` | 124 | 289 | 660 |
| `piapi:seedance-2.5-less-restriction`, listed first | 136 | 318 | 726 |
| `minimax_h3_max_3d_to_video` | 90 | 105 | 145 |
| `kling_v4` reference, no input fee assumed | n/a | 79 | 118 |
| `wan_3` reference, no input fee assumed | 25 | 50 | 100 |
| `flux_3` video-to-video, `bfl:flux-3-video/v2v` | n/a | 215 | 270 |

| Point | Rule | Check |
|---|---|---|
| **Verify BytePlus before pinning it** | The live spec lists the route, but a listing does not prove it runs: an internal note from 2026-10-28 said the BytePlus key was inactive and fal blocked face references. The spec also says an expired BytePlus task "fails over to the next provider" | After the budget is approved, make the first paid take a 480p take you need anyway, on the pinned route. If it fails, budget from the PiAPI rows. Compare billed credits with this table [inference] |
| The numbers above | Our arithmetic [inference], from per-second rates in varg's api seeds [vendor], cross-checked against live "from" prices. No clay job was billed to test them | Live spec over our research: we had printed 124 / 289 / 660 for less-restriction, but those match standard PiAPI. Live "from" prices (73 against 66) put it 10% higher; its 720p rate is inferred from that gap |
| The input clip is billed on Seedance | BytePlus tokens = (input video s + output s) x W x H x 24 / 1024, at a lower token rate with video in, with a minimum ([pricing](https://docs.byteplus.com/en/docs/ModelArk/1099320)). 5 s at 720p goes from 116 to 139 once clay is added | A longer clay costs more at the same output length |
| PiAPI and the default route | PiAPI adds half the per-second price for each input video second, and varg's estimate does not model it ([api seed](https://github.com/vargHQ/api) [vendor]). The live spec labels video-to-video only on BytePlus and fal's reference route; PiAPI's labels omit it, though its options take `input.video_urls` | `estimate_cost` can read low on a PiAPI clay shot. Pin the route on clay shots |
| H3 3D to Video | fal adds a per-request fee and input tokens beyond 4,096 per shot, with a 5 s billed minimum per shot ([fal](https://fal.ai/models/minimax/h3-max/3d-to-video) [vendor]). varg folds extras into its rate; the seed marks it "CALIBRATE" | Least settled row: a clip of many short shots can bill well above it [inference]. Kling and Wan input fees are unverified, so their rows may be low too |
| 480p clay on BytePlus | About 13 credits per output second, an estimate. An older varg figure of about 16 predates pass-through pricing; the old markup explains the gap [inference]. [Segmind's table](https://blog.segmind.com/seedance-2-5-draft-final-5-clips-tested-and-the-real-cost-math/) implies 12.7 [vendor] | Not verified on a live clay job |
| Comparing | BytePlus costs about half PiAPI at every resolution here. A 480p Seedance clay test (64) undercuts H3 3D to Video at any resolution, so H3's price case starts at 720p. Per generated second at 720p, Seedance runs 1.5 to 2.7 times Kling 4 and 2.3 to 4.2 times Wan 3, by route | Before input fees |

## References and limits

| Route | Images | Video | Audio | Total | Source |
|---|---|---|---|---|---|
| PiAPI | 9 | 3, 15.4 s total | 3, 15 s total | | [Live spec](https://varg.ai/models/seedance_2_5.md) summary line for counts, api seed [vendor] for totals |
| BytePlus | 30 | 10, each 2-30 s, 30 s total | 10, 30 s total | 50 assets | [BytePlus tutorial](https://docs.byteplus.com/en/docs/ModelArk/2607688), [ComfyUI](https://docs.comfy.org/tutorials/partner-nodes/bytedance/seedance-2-5/workflow.md) |

- Design each shot for 9/3/3, then read the [live schema](https://api.varg.ai/v2/tools/video?model=seedance_2_5): `files` allows 50 for the whole model, not per route.
  Our sources give no fal limit. Dreamina, not a varg route, takes 12 files ([Chris via PJ Ace](https://x.com/PJaccetturo/status/2116160709180723486) [vendor]).
- Fewer behaves better: [mix-ups](https://x.com/kan_mi_no9/status/2071964948314607704) [self]; "So maybe sometimes consider deleting a reference." ([Dreamina](https://x.com/dreamina_ai/status/2100927228356026407) [vendor]).
- Clay files on BytePlus: mp4 or mov, 24-60 fps, up to 200 MB, 407,696 to 8,295,044 total pixels (tutorial). By
  arithmetic 854x480 clears that and fails Kling's edit route; 640x360 fails both. Ours, untested: export 1280x720 or
  higher at 24 fps or more, and set `omni_reference_task_type` to `reference` on clay shots.

| Live spec | Inputs | Output | Resolution | Check |
|---|---|---|---|---|
| [`seedance_2_5`](https://varg.ai/models/seedance_2_5.md) | See above | 4-30 s | 480p, 720p, 1080p | The summary says "480p/720p"; its field and BytePlus include 1080p. That is 10-bit H.265, which some players cannot open; BytePlus recommends `output_format: mov` for editing |
| [`minimax_h3_max_3d_to_video`](https://varg.ai/models/minimax_h3_max_3d_to_video.md) | One `video_url` up to 15 s and 32 shots; `reference_image_urls`, or up to 8 generated | Follows the source; `duration` is ignored | 480P, 768P, 1080P | No audio: `audio` is ignored. The top-level field says 720p, the fal option 768P |
| [`kling_v4`](https://varg.ai/models/kling_v4.md) | `video_urls`, `voice_ids`; "up to 7 reference elements, 10 keyframes" | 3-30 s | 720p, 1080p | Edit route: at least 700 px per side, 23.9-60 fps. Kling's guide lists 4K; it is not on varg |
| [`wan_3`](https://varg.ai/models/wan_3.md) | 10 images, 5 videos, 5 audio | 2-30 s | 480p, 720p, 1080p | [Alibaba](https://www.alibabacloud.com/help/en/model-studio/wan3-video-generation-guide): 15 s of reference video, input + output at most 30 s. Top-level `audio` is ignored; use `provider_options.fal.audio` |

## From Seedance 2.0 to 2.5, and do not intercut them

| BytePlus [2.5](https://docs.byteplus.com/en/docs/ModelArk/2607689) and [2.0](https://docs.byteplus.com/en/docs/modelark/2222480) guides | Seedance 2.0 | Seedance 2.5 | What it changes here |
|---|---|---|---|
| Clay reference | Not in its guide | Among "reference capabilities added in Seedance 2.5" | The core of this workflow |
| Timing | Shot numbers only | "Seedance 2.5 supports integer-second timestamps" | Beats pace, but are "not frame-accurate edit points" ([fal's copy](https://fal.ai/learn/devs/how-to-use-seedance-2-5) [vendor]) |
| Length, reference video | 4-15 s; 3 clips, 15 s total | 4-30 s; BytePlus 10 clips, 30 s total | Fits a 30 s previz |
| Multi-view sheets | Not recommended, can read as several people | Supported | Character sheets work directly |
| Top resolution | 4K | 1080p | 4K delivery from 2.5 needs an upscale |
| Draft mode | Not supported ([tutorial](https://docs.byteplus.com/en/docs/ModelArk/2607688) table) | 480p draft, 1080p from the task ID, valid 14 days | No `draft` option on varg's live spec; see drafts-and-takes.md |
| BytePlus credits per second | 7.04 / 15.22 / 37.67 | 10.75 / 23.26 / 57.23 | About 50% more (varg seeds [vendor]) |
| Size of the change | | "Compared with Seedance 2.0, Seedance 2.5 is not a cross-generational leap in the same way that 2.0 was compared with 1.5." | Boards show a modest gap: 1132 to 1080 on OpenArt Film [vendor], 1157 to 1135 on AA image-to-video |
| Look | | "Seedance 2.5 and Seedance 2.0 have significantly different aesthetic style preferences." | Do not intercut them in one sequence [inference] |
| When to stay on 2.0 | Never refused in Everypixel's 15 clips, against 3 refusals for 2.5 | | Use `seedance_2` only for a whole sequence that needs 4K, a cheaper tier or fewer refusals [inference] |

Upscale or regenerate [inference]: regenerate natively for mid-size text, tight faces and dense texture; upscale for
stylised or medium shots, 4K and expired drafts. Only 720p to 1080p has a test: tied at normal size on medium and close
framing, which Segmind upscales, with "a slightly waxy finish" on crowd faces at 600% zoom ([Segmind](https://blog.segmind.com/seedance-2-5-upscaled-vs-native-1080p-side-by-side/) [vendor]). 480p to 1080p is unproven: [Pryce](https://x.com/second_bassoon/status/2117703324321694077) [self] stays native,
[@MANISH1027512](https://x.com/MANISH1027512/status/2117153429894361174) [self] ships 480p. See post-ready.md.

## Moderation and faces

Only Seedance has a documented hard block on realistic faces in references. CellCog reports refusals for photographs,
painted portraits, realistic 3D renders and frames the model itself returned, while stylised cartoon characters
passed, plus false positives that retries did not clear ([CellCog](https://cellcog.ai/blog/seedance-2-5-face-likeness-character-consistency/) [vendor]). Field error:
`InputImageSensitiveContentDetected.PrivacyInformation` ([Griptape](https://github.com/griptape-ai/griptape-nodes-library-standard/issues/782)).

| BytePlus's sanctioned route ([guide](https://docs.byteplus.com/en/docs/modelark/seedance-portrait-asset-guide)) | What it is | Check |
|---|---|---|
| 1. Preset digital characters | A free library addressed by asset ID | Only when no specific person is required |
| 2. Trusted model outputs | Original outputs from the same ModelArk account for 30 days. The list we could read: Seedance 2.5 and 2.0 videos and last frames, Seedream 5.0 lite, pro and flash text-to-image | "Only original model outputs are trusted; they cannot be used after secondary editing or after the validity period has expired." "Trust applies only to input assets. Output may still fail due to ModelArk security moderation policies." Reach through varg, where the account is varg's, is untested. Other image models' sheets are not on the list [inference] |
| 3. Authorized real-person assets | After verification and the person's authorization | The person's consent, every time |

On a refusal, work down this order [inference]: stylise the character; use trusted outputs or preset characters; keep
real people to authorized assets with consent; plan the shot to need no face reference (side profile, medium-wide,
over-the-shoulder, hands only, per CellCog [vendor]); or move a generated character's shot to `kling_v4` from stills.

- Real people's likeness only with their consent, on every model and route. Do not alter a reference to get it past a
  filter. We found no stated real-face block for Kling 4, Wan 3 or H3: missing documentation, not proof of no limit.
- The `-less-restriction` routes are not a way to pass real faces. PiAPI's tier keeps "real-person identity or faces"
  blocked (catalog, Seedance 2 Mini entry). The BytePlus one rests on "the account owner attests the likeness is not a
  real person" (api seed [vendor]). Do not make that attestation for a real person.
- Refusals go beyond faces: "Seedance 2.5 refused 3 of our 15 briefs. Kling 4 shipped all 15." ([Everypixel](https://x.com/Everypixelcom/status/2117279375741550841) [vendor]),
  among them a car chase flagged "potentially sensitive" and an anime brief blocked twice on copyright ([article](https://journal.everypixel.com/kling-4-vs-kling-3) [vendor]).

## Biases in the rankings

| Source or claim | Problem | Do this |
|---|---|---|
| Seedance posts on X | Dreamina pays for views through 2026-12-31: "Rewards start at $100 for 50,000 views and go up to $20,000" ([Dreamina](https://x.com/dreamina_ai/status/2117243037835509798) [vendor]). PJ Ace's series is a [Dreamina partnership](https://x.com/PJaccetturo/status/2116160709839188288) [vendor] | Read them as promotion unless the method is shown |
| CellCog, fal, OpenArt, "vs" posts | [CellCog](https://cellcog.ai/blog/seedance-2-5-vs-kling-4-0/) runs on Seedance, one take per test, picks not blind: Seedance took all ten picks, yet strict scores ran only 408 to 401 and Kling led three. fal sells the H3 Max and FLUX 3 Max it promotes. OpenArt resells. Most "vs" posts come from platforms reselling both models | Check who sells what |
| AA and OpenArt boards | Kling 4 is on neither; AA's anchor is Kling 3.0 at 1000, and its pages show no snapshot date. RigidBench found "no model leads on all ten" measures and higher SSIM going with larger 3D trajectory error ([abstract](https://arxiv.org/abs/2608.15555), tests neither Seedance 2.5 nor Kling 4) | Judge takes against the previz, not on looks [inference] |
| Seedance against Kling verdicts | Seedance favours sheets plus clay and Kling favours finished frames, so tests giving both sheets may underrate Kling [inference, from Workman and NOBU] | Feed each model its own input before comparing |
| Claims that do not hold today | FLUX 3 Max "tied #1" ([BFL](https://x.com/bfl_ai/status/2112255353677328415), 2026-10-19): AA image-to-video has it #12, whether the board moved or the claim never held; the catalog still says "Top-tier image-to-video". H3 Max "ranked #1 for video editing" ([fal](https://x.com/fal/status/2102879559104237764)): AA has Wan 3 #1, H3 768p #5, H3 Max unlisted. Seedance 2.5 "native 4K" on Higgsfield ([relayed by Moroney](https://x.com/lmoroney/status/2114050785176916083) [self]) conflicts with BytePlus's 1080p limit; it may be upscaling, not verified | Do not repeat them |
| This whole file | No named head-to-head runs one clay through these models, and no benchmark scores previz fidelity. Nobody in our research watched the clips, so verdicts belong to their authors. Web quotes came through an extraction tool; posts marked translated are our translations | For a shot that matters, run it: 139 + 105 + 79 + 50 + 30 (`heygen_video_1` reference) is about 403 credits [inference]. "Generate the same shot on all three and note exactly where each one fails." ([David J.](https://x.com/lordofblocks/status/2110053007979413646) [self]) |
