# Sources and method

Built on 2026-11-03 from X, GitHub and our own tests. Tweets and READMEs are self-reported unless we say otherwise.

## What we read

- **2,318 unique X posts** from 2021 to 2026 on editing with HyperFrames, Remotion and other tools (1,635 about editing, 538 concrete). 390 authors, the top 90 checked by hand.
- **49 primary sources** read in full for the 227 rules behind this skill, each with a matched quote.
- **199 skill repos** read, 8 rated install-first. See [other-skills.md](other-skills.md).
- **Our own test**: an 85 s take with planted defects, and cold agents editing it with and without this skill. See below.

## What nobody has measured

- No rule here was tested against viewer outcomes by anyone we read.
- We found no blind test of an agent's cut against an editor's. The closest is Ali Abdaal's self-scored comparison, read through a summary: round 1 scored HyperFrames 7/10, Resolve MCP 3/10 and Remotion 2/10; after splitting the work into stages both reached about 85%.
- We did not watch the videos in these posts. "Shown with output" means a result was attached, not that it is good.
- Self-reported savings are unaudited, and vendor numbers are marked as vendor.

## People worth reading first

Ranked in the guide. Ranked here by what they contribute to this skill:

| Who | For | Note |
|---|---|---|
| [@condzxyz](https://x.com/condzxyz/status/2109656043441561893) | The most complete numeric cut and check spec | |
| [@ladprofit](https://x.com/ladprofit/status/2115450836398882941) | Numeric ad rules; note-to-rule loop | Still trims jump cuts by hand |
| [@Emarky](https://x.com/Emarky/status/2034995870035268034) | Silence settings, one-camera framing, voice chain, "what doesn't work" | |
| [@trq212's deck](https://thariqs.github.io/cc-video-editing-deck/) | Multi-take selection, edit file, overlay timing | Prompts are verbatim; a colorist found a real log-grading flaw, which he accepted |
| [@ForwardEditor](https://x.com/ForwardEditor/status/2098258583028633924) | Working editor's review loop | Matthew Berman confirms the role |
| [@gregpr07 / video-use](https://github.com/browser-use/video-use/blob/main/SKILL.md) | Reading video as text | Builder |
| [@bozhou_ai](https://x.com/bozhou_ai/status/2074790399789732348) | Word timing as the only clock | |
| [@finnardley](https://x.com/finnardley/status/2116191842492453094) | Word-indexed short-form spec | |
| [@darrrragh](https://x.com/darrrragh/status/2117207422586572964) | A small measured test: 1:23 raw to an editor-level v4 in 40 min | Self-reported, under 200 views |
| [@DZhao63405](https://x.com/DZhao63405/status/2095358879907594572) | Note formats | |
| [@sara_nambiar](https://x.com/sara_nambiar/status/2066181233571463519) | Timing as spoken-word triggers; freezing scenes | |
| [@JNYBGR](https://x.com/JNYBGR/status/2116256733857550396) | What Remotion does and does not decide | Builder, sells licenses |
| [@jake11moran](https://x.com/jake11moran/status/2102878602316652828) | Launch-film order and camera notes | HeyGen |
| [@MarioJoos](https://x.com/MarioJoos/status/1893019071303827764) | Retention: intros, J and L cuts, the cost of B-roll | Warns against golden numbers |

## Rules, by source

How many of the 227 rules each source supports, and for which jobs. Full rulebook: vargHQ/aeo `research/2026-11-03-edit-video-experts/`.

| Source | Rules | Jobs |
|---|---:|---|
| [gregpr07 / video-use](https://github.com/browser-use/video-use/blob/main/SKILL.md) | 29 | captions, feedback-loop, grade, motion-overlay, music, plan, prompting |
| [condzxyz](https://x.com/condzxyz/status/2109656043441561893) | 26 | captions, motion-overlay, music, pacing, punch-ins, qa, reframe, rende |
| [ladprofit](https://x.com/ladprofit/status/2115450836398882941) | 21 | broll, captions, feedback-loop, pacing, prompting, punch-ins, qa, rend |
| [Emarky](https://x.com/Emarky/status/2034995870035268034) | 15 | broll, grade, music, pacing, plan, punch-ins, reframe, render, silence |
| [bozhou_ai](https://x.com/bozhou_ai/status/2074790399789732348) | 14 | broll, feedback-loop, motion-overlay, music, plan, qa, sound, transcri |
| [elie2222](https://x.com/elie2222/status/2107186094777434454) | 11 | broll, captions, music, pacing, qa, render, sound, transitions |
| [eliana_jordan](https://x.com/eliana_jordan/status/2065367900328747424) | 9 | captions, motion-overlay, plan, qa, render, silence |
| [darrrragh](https://x.com/darrrragh/status/2117208133563285597) | 9 | captions, feedback-loop, grade, music, plan, prompting, qa, retakes, s |
| [trq212](https://thariqs.github.io/cc-video-editing-deck/) | 9 | grade, motion-overlay, prompting, retakes |
| [ForwardEditor](https://x.com/ForwardEditor/status/2098258583028633924) | 7 | feedback-loop, punch-ins, qa |
| [sara_nambiar](https://x.com/sara_nambiar/status/2066181233571463519) | 6 | feedback-loop, plan, prompting, transitions |
| [DZhao63405](https://x.com/DZhao63405/status/2095358879907594572) | 6 | broll, feedback-loop, plan |
| [finnardley](https://x.com/finnardley/status/2116191842492453094) | 5 | captions, pacing, silence, sound, transcript |
| [MarioJoos](https://x.com/MarioJoos/status/1893019071303827764) | 5 | broll, pacing, transitions |
| [jake11moran](https://x.com/jake11moran/status/2102878602316652828) | 4 | broll, motion-overlay, plan, prompting |
| [MarioJoos](https://x.com/MarioJoos/status/2028484785673220382) | 4 | pacing, punch-ins, transitions |
| [Ali Abdaal via @Jaden_riku](https://x.com/Jaden_riku/status/2115439253173989673) | 3 | broll, plan |
| [rameerez](https://x.com/rameerez/status/2016208478843318488) | 3 | plan, qa, transitions |
| [alexgoughcooper](https://x.com/alexgoughcooper/status/2115076988327076296) | 3 | feedback-loop |
| [gregpr07](https://x.com/gregpr07/status/2044554562208731373) | 2 | transcript |
| [levelsio](https://x.com/levelsio/status/2116959423117857026) | 2 | prompting, transcript |
| [HyperFrames talking-head-recut skill](https://github.com/heygen-com/hyperframes/tree/main/skills/talking-head-recut) | 2 | motion-overlay, reframe |
| [shintaro032](https://x.com/shintaro032/status/2082729683079283021) | 2 | motion-overlay |
| [itsohqay](https://x.com/itsohqay/status/2064838306211537113) | 2 | grade |
| [MaxRohowsky](https://x.com/MaxRohowsky/status/2117527347679154667) | 2 | grade, prompting |
| [HeyGen](https://x.com/HeyGen/status/2077438104982667282) | 2 | prompting |
| [kodera_ai](https://x.com/kodera_ai/status/2115368170559013189) | 2 | render, sound |
| [nateherk](https://x.com/nateherk/status/2108209557516304862) | 1 | silence |
| [cathrynlavery](https://x.com/cathrynlavery/status/2115278024769970312) | 1 | silence |
| [levelsio](https://x.com/levelsio/status/2116962016883540248) | 1 | pacing |
| [HeyGen](https://x.com/HeyGen/status/2075998619325604238) | 1 | captions |
| [rameerez](https://x.com/rameerez/status/2015859121661059569) | 1 | motion-overlay |
| [EnriTarta](https://x.com/EnriTarta/status/2115433929742151891) | 1 | motion-overlay |
| [jake11moran](https://x.com/jake11moran/status/2103239225902874874) | 1 | motion-overlay |
| [HyperFrames cut-the-curve skill](https://github.com/heygen-com/hyperframes/tree/main/.claude/skills/cut-the-curve) | 1 | transitions |
| [nateherk](https://x.com/nateherk/status/2108196674321666525) | 1 | sound |
| [heygalatea](https://x.com/heygalatea/status/2117681954908770541) | 1 | qa |
| [cathrynlavery](https://github.com/cathrynlavery/yap-studio) | 1 | feedback-loop |
| [EnriTarta](https://x.com/EnriTarta/status/2115418480010817846) | 1 | feedback-loop |
| [alexgoughcooper](https://x.com/alexgoughcooper/status/2115188896468173309) | 1 | feedback-loop |
| [alexgoughcooper](https://x.com/alexgoughcooper/status/2115106838371049851) | 1 | render |
| [JNYBGR](https://x.com/JNYBGR/status/2116256733857550396) | 1 | prompting |
| [JNYBGR](https://x.com/JNYBGR/status/2013334152867717479) | 1 | prompting |
| [HyperFrames_](https://x.com/HyperFrames_/status/2113670541274144802) | 1 | silence |
| [HyperFrames_](https://x.com/HyperFrames_/status/2113697923112575048) | 1 | transcript |

## What we tested ourselves

An 85 s public-domain interview with planted defects: a false start, a repeated sentence, a slate that flashes mid-take, black gaps. One clip, so this shows what can break and is not a rate.

| Cut | Planted defects fixed | Tokens | Minutes |
|---|---:|---:|---:|
| No skill 1 (official HyperFrames skills only) | 7 of 7 | 338K | 99 |
| No skill 2 | 7 of 7 | 376K | 86 |
| This skill, first version 1 | 7 of 7 | 344K | 67 |
| This skill, first version 2 | 7 of 7 | 354K | 73 |
| This skill, after fixes | 7 of 7 | 275K | 35 |

**A strong agent clears these defects with or without this skill.** The fixed version used 23% fewer tokens than the no-skill average, in one run, on a shared machine, so it is a hint and nothing more. The testers' 36 problem notes, many of them the same, drove the fixes here. One further round of fixes came after the last run and was checked by script, not by a new cold agent. Long multi-take footage is untested. Nobody has listened to these cuts.

Blind judges did not separate skill from no skill either. Details are in [judge.md](judge.md).

The generated cut rendered at the edit list's exact length in HyperFrames 0.9.9 and Remotion 4.0.540 (64.800 s). `cut.fcpxml` was checked as valid XML with the right clip count, and **was not opened in Resolve or Final Cut**.

## Disagreements we settled

Where sources conflict, [numbers.md](numbers.md) names a default and the condition that changes it. Three settled here against a source's claim:

- **Which way to assemble.** video-use teaches per-segment extract plus `-c copy`. @hassancs91 measured drift from that, and our own test confirmed it (+300 ms over 14 cuts). We use one filter graph.
- **Whether to re-transcribe.** Sources split. We do it as a check, and as the clock when word times are not trustworthy, because our single-pass times lost 23 of 222 words through the edit list.
- **"Use OffthreadVideo, never Video."** True of the old `<Video>` from `remotion`. The docs now recommend `<Video>` from `@remotion/media`.
