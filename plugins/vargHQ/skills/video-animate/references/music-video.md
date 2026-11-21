# Music videos and short clips: a section plan, with the downbeat as a default

`[vendor]` = company selling or reselling it, or a paid partner; `[self]` = one person's own report; `[measured]` = varg's own measurement, usually one film; `[inference]` = our reasoning, nobody tested it; no tag = opened primary source (docs, standard, paper, book).

Decides which director mode a shot list follows, when a cut may leave the grid, how pacing changes by section, and what
a short clip must pass. Every check, field name and threshold here is ours and heuristic until run against real
reference videos (shot detection plus `songmap.py` on about 20 of them). Spot-check quotes before reusing them in public.

## Where this file overrides `varg-music-video`

`varg-music-video` is the full end-to-end recipe: use it for `songmap.json`, lyric surfaces, stills, the lip-sync pass,
the lyric gate, review rounds and mastering. When `video-animate` is in charge, apply the middle column on these points.

| `varg-music-video` says | Apply instead | Why |
|---|---|---|
| "Cuts land on downbeats. Always." and the edit script "must refuse off-grid cuts" | Grid is the default. Reject only undeclared off-grid cuts; allow `off_grid: anticipation` and `off_grid: subvert` | Prétet, Pozzi, Lin, below |
| "One shot per lyric line" | `lyric_led` is one mode among `stem_led`, `long_take`, `master_plus_inserts`, `performance_as_concept` | The common shot length is a beat or a bar, not a line. Oners and sound-mapped videos do not follow lines |
| "pair one dance move with one cut, not a continuous take" | Reverse the default: master plus inserts. Use one move, one cut only as a fallback when the model cannot hold the routine | Gondry, Chandelier. Holding a 30 s full-body dance on Seedance 2.5 is untested, so pilot it |
| "Few singing shots." | Keep as a cost rule. Dance, walking and playing count as performance, so `lip_sync: true` stays low without a performance-free video | Pohl; "More lip sync does not automatically mean a better music video." ([Film Threat](https://filmthreat.com/features/i-tested-6-ai-music-video-generators-on-the-same-3-minute-song/), staff byline promoting one tool) |
| "Do not RIFE-interpolate to 60" | Deliver at 30. Interpolate only shots being slowed, then return to delivery fps | Dave Clark, below |
| "the star is on screen in frame 1" | Keep for vertical. On horizontal, allow a held opening with a declared reason | TikTok; the Higgsfield route opens on a 2 s static wide |
| "roughly 2–3× the credits" | Treat as a floor for camera-heavy shots and budget by `shot_difficulty` | Trillo, Hell Grind; eras and models differ |

## The downbeat is a default, not a law

Call: the grid is the default and off-grid cuts are allowed when declared. Put section starts, drops and the payoff on
downbeats; ordinary cuts may sit on any grid point (our wording, untested).

| Source | Finding | Limit |
|---|---|---|
| [Lin, Yeh, Shams 2022](https://escholarship.org/uc/item/1rq255xj) | Cuts on the accented first beat: "a higher perceptual pleasure was found for temporal congruency compared with incongruency". 143 subjects, d = 0.33, 1 of 145 noticed; second experiment t(29) = 2.16, p = .019 | Modest effect. Experiment 1: sparse cuts, about 6 per clip, displaced a little under half a bar. Experiment 2: about 13 per 30 s clip, moved 2 to 2.5 beats. Anticipation by a few frames was not tested, so it does not argue against Pozzi [inference] |
| [Prétet, Richard, Peeters, ISMIR 2021](https://arxiv.org/abs/2108.00970) | 548 official videos. Downbeat co-occurrence within about 0.5 s, by video genre: Dance 0.24, Concept 0.23, Narrative 0.23, Performance 0.16. By music: R&B 0.31, Reggaeton 0.28, Pop 0.21, Rock 0.19 | Dance/Electro shot length often matches the bar, yet alignment is low: same period, different phase. Compare each `start` with `songmap.downbeats`, not only its length |
| Editors and directors, in Prétet | Maxime Pozzi: "Off-beat cuts are used to create dynamics: to surprise the viewer, and illustrate the music's emotional climax." In Rolling in the Deep from 2:20, cuts sit just before the downbeat. Alexandre Courtès: "Cuts have to follow the music's rhythm, even though they might not always co-occur with beats." | Interviews. No frame value given |
| [Pohl 2025](https://reposit.haw-hamburg.de/bitstream/20.500.12738/19403/1/BA_Editing_shaped_the_video_star.pdf) | Cuts following the musical pulse are near 100% across decades; exact beat cuts nearly vanish from the mid-1990s | Bachelor thesis, small sample, human coding |

| Do | Check (ours) |
|---|---|
| Tag every cut | `anchor` is downbeat, beat, offbeat, lyric, action or transient. Untagged cuts fail. Tagged beat cuts land within 100 ms, the default of an [ads pacing checker](https://www.skills.sh/gooseworks-ai/gooseworks-ads-skills/review-video-pacing-rhythm), not research |
| Anticipate only at a climax | `off_grid: anticipation` with negative `offset_frames`, in a declared climax section only. No source gives a value: test 1 to 3 frames |
| Set up, then subvert | `off_grid: subvert` follows at least one bar of on-grid cuts ([Graham Patterson](https://lbbonline.com/news/finely-sliced-why-graham-patterson-is-addicted-to-creative-challenges), second-hand: search summary, page blocked). Start at no more than 25% of a section's cuts |
| Loosen performance shots | Performance has the weakest alignment (0.16), so a hard rule fits it worst [inference]. Anchor to action or lyric when that reads better |

## Director modes

Declare one `mode` per video, or per section with a stated reason. Names are for teaching: never put a living artist's or
director's name in a generation prompt; describe the technique. Mode translation and checks are ours [inference].

| Mode | Copy this | Check on the shot list (ours) |
|---|---|---|
| Stem-led (`stem_led`) | Gondry: "Every sound from the track will be illustrated by an element of the landscape that appears each time that sound is heard." ([forum archive](https://archive.thechembase.com/Adjusted/index5471.html): weak provenance, a 2003 post quoting an unnamed publication). The only full map found is Around the World: robots vocals, tall athletes bass, disco girls high keyboard, skeletons guitar, mummies drum machine ([Wikipedia, citing the DVD book](https://en.wikipedia.org/wiki/Around_the_World_(Daft_Punk_song))) | `element_map` lists each stem and its element; every bar with that stem shows it. Elements rise and fall with active stems. Each hit type (kick, snare, hat roll, bass slide) has a named visual response. A bar-by-element grid is reviewed on the previz before spend: the previz plays the role of Gondry's [graph paper](https://en.wikipedia.org/wiki/Star_Guitar). The Higgsfield "Music-video route" names one instrument hit per event ([third-party copy on X](https://x.com/Diplomeme/status/2077986179895755110)) [vendor], but its round seconds miss its own 95 BPM grid, where one beat is 0.632 s [inference]: take every prompt timestamp from `songmap` |
| Same path, more each pass | Come Into My World: one motion-control orbit looped four times, each lap adds figures ([befores & afters](https://beforesandafters.com/2026/03/24/olivier-gondry-on-the-making-of-kylie-minogues-come-into-my-world/)) | Repeats reuse one camera path and add at least one named element. Gondry had the track changed into loops; audio is locked here, so use the song's real repeats |
| Few shots, many events (`long_take`) | This Is America: six shots, whip pans on musical shifts. "He would add piece by piece, and we would build it big, and then we would then strip it back down." (DP Larkin Seiple on Hiro Murai, [ASC](https://theasc.com/article/dp-larkin-seiple-on-this-is-america-quot/)) | Each musical shift has a logged in-shot event. The layer list rises then falls. Sung long takes split into gated pieces, each aligned to its vocal slice, after OK Go's gates ([Wikipedia, citing MAKE](https://en.wikipedia.org/wiki/This_Too_Shall_Pass_(OK_Go_song))) |
| Master plus inserts (`master_plus_inserts`) | Chandelier: "there are just some things you miss in the one-take, like the close-ups" ([Askill](http://onepointfour.co/2014/05/20/dance-hit/)). Gondry: "I was sick to see choreography being mistreated in videos like filler with fast cutting" ([Wikipedia](https://en.wikipedia.org/wiki/Around_the_World_(Daft_Punk_song)), original not opened) | Dance held full body for 4+ bars; no cut per move without a logged reason. Inserts generated separately. Past the model's generation limit, hide joins at occlusions, as OK Go did |
| Performance as the set (`performance_as_concept`) | Hotline Bling: "I'm a set-driven director." "We're not mixing it with street footage" ([FADER](https://www.thefader.com/2015/10/21/drake-hotline-bling-video-director-x-interview-toronto)) | One set and one light state per section. No cutaways outside declared sets |
| Travelling motif | Cole Bennett's yellow curtain: "We don't just want to set the artist in front of it and shoot them every time." ([Hypebeast](https://hypebeast.com/2024/1/cole-bennett-all-is-yellow-lyrical-lemonade-album-release-interview)) | `motif` appears at least once per section. No two appearances share angle and light |
| One gag, escalated | Turn Down For What: "We just structured it based on how to get the maximum number of fun things in there." ([No Film School](https://nofilmschool.com/2014/05/award-winning-directors-daniels-share-original-treatment-50-million-view-video)) | One premise. Larger scale each chorus. The turn sits "right when the song gets moody and stops building" |
| Tone collision | Never Catch Me: "something extremely joyful that felt like a catharsis compared to the setting" ([FADER](https://thefader.com/2014/10/09/flying-lotus-never-catch-me-behind-the-scenes-hiro-murai)) | `tone_map` holds at least one clash between music and picture, logged as intended |
| Reserve for the edit (any mode) | Hurt began as "a very straightforward performance music video" and "completely changed in the edit" ([ProVideo Coalition](https://www.provideocoalition.com/hurt_editor/), the author's summary of a making-of clip) | Budget line for shots chosen after first assembly |
| Hardest first (any mode) | OK Go: put the fiddly sections at the front; 60+ takes, many failed about 30 s in ([Wired piece, author's copy](https://dylan.tweney.com/ok-go-rube-goldberg-machine/)) | The riskiest generation is the pilot, ahead of shots that depend on it. `shot_difficulty` is set on every shot |

## Section pacing: weak numbers, starting values only

Cuts per minute from [Pohl 2025](https://reposit.haw-hamburg.de/bitstream/20.500.12738/19403/1/BA_Editing_shaped_the_video_star.pdf):
a bachelor thesis, 21 videos from the MTV VMA Best New Artist category, human coding. Seconds per shot is computed.

| Section | Cuts/min | s/shot | Default (ours unless cited) |
|---|---|---|---|
| Intro | 37.7 | 1.59 | Narrative function in 100% of coded intros |
| Verse | 41.0 | 1.46 | Lower energy unless the genre runs fast |
| Pre-chorus | 35.1 | 1.71 | Accelerate or hold back: choose one and log it |
| Chorus | 42.55 | 1.41 | Speeds up in 42.2%, holds in 31.3%: faster or steady, with payoff imagery |
| Bridge | 43.7 | 1.37 | Default to slow [inference]. The mean is skewed by the 2010s; 44.4% slow, and Pozzi says slower and poetic |
| Instrumental | 31.6 | 1.90 | Older videos skew this |
| Outro | 29.5 | 2.03 | Must be slower than the section before: 84.6% slow, none hold steady |

- Do not derive a rate from BPM: Pohl finds no correlation between song tempo and cut rate. No rates by genre exist.
- Do not adopt a mean as a target: 4.76 s in Prétet (automatic detection), about 1.46 s in Pohl (human counting).
- Declare `section_target_cpm` per section; actual stays within 20% (ours). The peak section gets its own rate.
- Keep an energy map per section: stem energy 1 to 5, cuts per minute, scale, camera intensity, layers. Intensity
  follows energy except rows flagged `inversion: true` (format and check ours; the idea is from Pozzi, Kearns, Murai).
- Pohl (multi-label): narrative in 100% of intros and 92% of outros, performance strongest elsewhere. No treatment
  found states a numeric split of performance, narrative and concept, so any ratio you write is yours.

## Editors' procedure and uneven lengths

| Step | Source | Check (ours) |
|---|---|---|
| First assembly | The usual Avid order assembles the best performance takes, then drops in concept or narrative ([Caston, MSMI 2017](https://repository.uwl.ac.uk/4706/1/EditingDossiermsmi.2017.6.pdf)) | The previz cut is the first full-length assembly; generated shots replace it |
| Narrative muted first | Tony Kearns: "just cut the pictures and not listen to the music. Then I did a performance cut and married the two." (Caston) | Narrative shots were watched muted before the marriage |
| Over-cut, then subtract | Art Jones: "The way I like to cut music videos was to over cut it." Then: "Slow it down as opposed to spending more time trying to make it faster." (Caston) | First cut holds about 120% of target shots. Do this on the previz or drafts, where a shot costs little [inference]; see drafts-and-takes.md |
| Lyric cuts, then beat cuts | Ian McLaughlin folds cuts following the lyrics, then punctuates with beat cuts as a final pass ([LBB](https://lbbonline.com/news/more-than-just-cutting-to-the-beat-the-nuance-of-editing-music-videos), second-hand: search summary, page blocked) | `anchor: lyric` cuts are placed before `anchor: beat` cuts |
| Hold the payoff | Kearns criticizes giving "everything away in the first thirty seconds" (Caston) | The biggest new visual sits on the top-energy section, not earlier |
| Draw ramps first | Street Spirit's ramps were tables on graph paper. Dawn Shadforth names the failure: "everything is being shot at 60fps. And cut really slowly." (Caston) | `speed_map` is keyed to beats, ramps end on a named hit, slow motion stays under 30% of a section unless it is the concept. Retime, then lip sync (untested; see sound-sync.md) |
| Uneven lengths | Dave Clark: "I'm able to tell a story and not have to use just three-second clip after three-second clip." "Sometimes you'll get an eight-second clip because I slowed it down, then you'll get a one-second clip." He upconverts in Topaz from 24 to 60 fps, "sometimes 120", then retimes ([Every](https://every.to/podcast/transcript-how-a-hollywood-director-uses-ai-to-make-movies)) (not re-checked: transcript is paywalled) [self, Runway Gen-2 era]. In Prétet the most common shot is about one beat in 329 clips, about one bar in 95, four bars in only 2, yet the mean is 4.76 s: many very short shots and a few long holds [inference; the detector may count flashes as cuts] | Durations come from the section map and bars, never the model's default length. At most 3 equal-length shots in a row unless logged as `metric_pattern`. The duration histogram is not a single spike. At least one 2+ bar hold per minute |
| Lose the previz look | Joseph Kahn: "It's very telling AI flip flops between these two styles because they are the standard pulls." One is action "replicating a potpourri of stuntman action reels or previz animatics." ([X](https://x.com/JosephKahn/status/2070788059680194970)) [self]. This skill starts from a previz, so it applies directly [inference] | Does each action shot still move like a clean animatic? Add operator imperfection, weight and an event in the shot. See animation.md and cinema.md |

## Real AI production numbers

Scarce. No public shot counts or costs were found for Clark's, Kavan's, MetaPuppet's or Chroma winners' videos.

| Project | Numbers | Read it as |
|---|---|---|
| The Hardest Part, Paul Trillo, 2024 ([fxguide](https://www.fxguide.com/?p=419437), [No Film School](https://nofilmschool.com/ai-music-video)) | About 700 clips of about 20 s, 55 to 56 used; "about 230 minutes of video was generated in total" for under 4 min; about six weeks | About 58:1 by minutes, 13:1 by clips, 4.3 s per used shot (computed). Sora pre-release without references: not comparable to reference-mode takes. No official cost, so quote none. He kept artifacts as a choice, to "lean into the strange" (fxguide): declare keep or remove in the brief. He says character consistency struggles are a sign to shoot on camera |
| Hell Grind, Higgsfield, 95 minutes, not a music video ([36Kr](https://eu.36kr.com/en/p/3933070123089287), secondary) [vendor] | 115,446 generation records, 14,593 rework entries; reported budget about $500,000. One action scene took 4,000 to 5,000 generations, a later one 10 to 20. "every rule in this briefing comes from a failed shot" | Budget by shot difficulty, not runtime [inference]. Takes per run: drafts-and-takes.md |
| Dead-Air Crown, Dave Clark ([X](https://x.com/Diesol/status/2067286980195680444)) [self]; a hyperpop video from The Commanding Heights, zeal ([X](https://x.com/zealcaiden/status/2117359490257629331)) [self] | "within a week"; "86.2 agent hours". No shot counts | One data point each, on schedule and agent time |

Kavan Cardoza: "It replaces the physical shoot. Everything else – writing, editing, story, performance – that's still
human-led." ([Creative Bloq](https://www.creativebloq.com/ai/ai-filmmaking-is-a-gimmick-if-you-dont-know-the-rules-of-cinema))

## Beliefs that are wrong: do not repeat them

| Belief | What the source says | Copy instead |
|---|---|---|
| Let Forever Be maps instruments to dancers | No instrument map found. A drummer starts the beat and seven dancers follow; DVCAM world, 35mm stage, morphs between ([forum archive](https://archive.thechembase.com/Adjusted/index5471.html), weak) | Around the World for a sourced map; two named looks switching at section boundaries |
| This Is America is one take | Six total shots ([ASC](https://theasc.com/article/dp-larkin-seiple-on-this-is-america-quot/)) | Few shots, many events |
| The released Chandelier is one take | "The final video isn't one-take but we shot Maddie doing it in one-take" ([Askill](http://onepointfour.co/2014/05/20/dance-hit/)). An alternative one-take release in 2014 is unconfirmed | Master plus inserts |
| OK Go's oners are unbroken | This Too Shall Pass has at least two cuts, at curtains and a warping piano ([Wikipedia, citing MAKE and Detroit Free Press](https://en.wikipedia.org/wiki/This_Too_Shall_Pass_(OK_Go_song))). Upside Down & Inside Out is eight sequences from about 45 minutes ([RedShark](https://www.redsharknews.com/production/item/3304-how-to-make-a-music-video-in-zero-g)) | Hide joins at occlusions and morphs |
| Helicopter (A$AP Rocky) is AI | Gaussian splatting from 56-camera capture: "Every stunt, every swing, every fall was physically performed and captured in real space." ([Radiance Fields](https://radiancefields.com/a-ap-rocky-releases-helicopter-music-video-featuring-gaussian-splatting), quoting Evercoast, the capture company) | Never cite it as an AI example. Its previz-first layout is the closest human analog [inference] |
| Runway's AI film awards have a music video winner | AIF 2026 categories are Film, New Media, Gaming, Design, Advertising, Fashion ([AIF](https://aif.runway.com/)). Earlier years not checked | Chroma Awards Season 1 had music video winners, with no methods in the [list found](https://aifilmcontests.com/topics/chroma-awards-season-2-2026) |
| Unverified lines | Kahn as "structuralist, all about tempo" ([only in a Claude-generated summary he posted](https://x.com/JosephKahn/status/2040133740479828401)); "Most AI edits hold every shot for the same length" (page never found, no author); an exact Star Guitar instrument map (fan observations only); "65% who watch 3 seconds watch 10" ([no method](https://www.kapwing.com/resources/short-form-video-statistics-tiktok-reels-and-shorts-by-the-numbers-in-2026/)); 63% click-through for a key message in 3 s (third parties only); an Atlantic study of drop-off at 52 seconds (anecdote in Caston, untraceable) | Do not reuse any of them |

## Short clips and vertical

| Topic | Data | Limit |
|---|---|---|
| First seconds | "2 seconds of exposure is needed to capture 50% of recall lift, and 2.5 seconds is needed for awareness." 95% of top brand-lift creative do not open with a large logo card. "59% of ads with high numbers (4-5) of event triggers perform above ad memorability benchmarks." ([TikTok deck](https://ads.tiktok.com/business/library/TikTok_Works_Recut_Remix_Reimagine.pdf)). 90% of ad recall impact falls in the first six seconds ([TikTok blog](https://ads.tiktok.com/business/en/blog/creative-best-practices-top-performing-ads/)) [vendor] | First-party, 2021-2022, ads, not music. Applying it to music clips is an assumption |
| Shorts views | Since March 31, 2025: "Shorts views will now count the number of times a creator's Short starts to play or replay." Monetization uses engaged views ([TechCrunch](https://techcrunch.com/?p=2986224)) | A loop raises views, so it cannot stand in for retention [inference] |
| Reels length | 9.77 million organic brand Reels, January to June 2026, median views: under 30 s 4,700; 30-45 s 8,564; 45-60 s 10,374; 60-90 s 9,790; past 180 s 4,428. Engagement peaks at 45-60 s ([Socialinsider](https://socialinsider.io/blog/instagram-reels-length/)) [vendor] | Correlation, brand accounts, no watch time. TikTok on length: "There is no magic number!" |
| Safe zones | No platform publishes binding organic values. Meta Stories and Reels ad margins reported as 14% top, 20 to 35% bottom, 6% sides; scaled from its 1440×2560 to 1080×1920, about 269, 384 to 672 and 65 px ([Billo](https://billo.app/blog/meta-ads-safe-zones)). TikTok estimates: top 108 px, bottom 320 px, 370 px on paid posts ([AdaptlyPost](https://adaptlypost.com/blog/social-media-safe-zones-2026-complete-guide)) | Second-hand third-party guides that conflict. Meta's and Google's own pages not opened |

| Check (ours, [inference]) | Pass when |
|---|---|
| First 2 s | A viewer who stops at 2 s has seen the star or the core image. No logo card. The biggest new visual can still wait for the peak |
| First 6 s | At least 4 of cut, move, sound hit, text, scale change |
| Loop | Last frame matches the first in pose or composition, or holds a final pose (Higgsfield's "FINAL BUTTON") |
| Text | Inside top 14%, bottom 35%, sides 6%, verified in each app's preview. Re-lay out verticals, never crop (`varg-music-video` section 10) |
| Length | Pick the section by song peak, not a benchmark. Test 15 to 30 s against 45 to 60 s; do not assume under 30 s wins |
| Pace | Start at one bar or half a bar, then apply the section map. No peer-reviewed shot length, retention by cut rate or music-specific curve was found. Creator specs only: 1.5 to 3 s or 2 to 4 s for explainer shorts ([X](https://x.com/finnardley/status/2115786060231770351)) [self]; one bar, about 1.8 s at 133.8 BPM, in the `varg-music-video` case study [measured] |

## Failure checks

Same-length cuts and the previz look: see above. Most "flat energy" critique is from vendors: a checklist, not evidence.

| Failure | Named by | Check (ours) |
|---|---|---|
| Flat energy across sections | "does the picture change when the song changes" ([High on Films](https://www.highonfilms.com/judge-an-ai-music-video-generator-by-section-cuts/)) [vendor] | Adjacent sections differ in at least 2 of cut rate, scale, camera, layer count |
| Same-scale runs | [SunoMV](https://suno.bi/en/blog/shot-scale-camera-motion-rhythm-method-sunomv-2026) [vendor] | At most 3 consecutive shots of the same size and motion |
| Random cutaways | No named critique; nearest is Director X's rule against street footage | Each cutaway names `reason`: lyric, motif, narrative beat or instrument. No reason, no shot |
| Same shot every chorus | Nobody; ours [inference] | Chorus 2 and 3 differ from chorus 1 by a declared change |
| AI sheen | "that signature soulless AI sheen" ([Natalie Fear](https://www.creativebloq.com/entertainment/snoop-dogg-ai-music-video), whose main gripe was a claymation moment) | Texture and imperfection rules live in the look bible, checked per clip |
| Consistency decay | Character consistency "gets hard after shot 20" ([Film Threat](https://filmthreat.com/features/i-tested-6-ai-music-video-generators-on-the-same-3-minute-song/)) | Consistency check on full-size frames every 15 to 20 shots |

## Shot list fields

Add to each `storyboard.json` row from `varg-music-video`. Field names, values and validator rules are ours and untested.

```json
{ "mode": "master_plus_inserts", "section_target_cpm": 42, "anchor": "downbeat", "offset_frames": 0, "off_grid": null,
  "stem": "keys", "element": "smokestack", "motif": "curtain", "function": "performance", "lip_sync": false,
  "energy": 4, "inversion": false, "speed_map": [[0.0, 1.0], [1.8, 0.5]], "shot_difficulty": 3,
  "metric_pattern": null, "transition": "hard_cut", "reason": "lyric: 'waiting'" }
```

The validator rejects: an untagged cut; an off-grid cut with no `off_grid` and `reason`; a negative offset outside a
declared climax; a 4th equal-length shot in a row without `metric_pattern`; an outro not slower than the section before;
a bar with a stem from `element_map` but no element in frame; a section with no `motif`, or a repeated motif angle and
light; a cutaway with no `reason`; a section change with no `transition` (hard cut, object wipe, graphic match, jump cut,
per Courtès and Vernallis via Caston); a ramp ending on no named hit; a retime after lip sync; intensity against `energy`
with no `inversion`.
