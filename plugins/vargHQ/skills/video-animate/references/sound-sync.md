# Sound sync: animating to a soundtrack that already exists

Decides how to generate each shot against a locked track, how to prompt from it, how close a sound must sit to its
picture event, and what to check. Making voices, effects, music and the mix belongs to [`video-sound`](../../video-sound/SKILL.md).

`[vendor]` = company selling or reselling it, or a paid partner; `[self]` = one person's own report; `[measured]` = varg's own measurement, usually one film; `[inference]` = our reasoning, nobody tested it; no tag = opened primary source (docs, standard, paper, book).

Names: earshot [playbook](https://raw.githubusercontent.com/Leonxlnx/earshot/main/docs/launch-video-sound.md), [study](https://raw.githubusercontent.com/Leonxlnx/earshot/main/docs/motion-sfx-study.md), [README](https://github.com/Leonxlnx/earshot), [LIMITS](https://raw.githubusercontent.com/Leonxlnx/earshot/main/docs/LIMITS.md); cinetic [sound.md](https://raw.githubusercontent.com/Leonxlnx/cinetic/main/skills/cinetic/references/sound.md), [timing-grid.md](https://raw.githubusercontent.com/Leonxlnx/cinetic/main/skills/cinetic/references/timing-grid.md). One author's tools
(Leonxlnx) on films that author chose, so both are [self]: "Seven films are a small sample: treat the numbers as "what
pros did here", not as laws." (playbook). This file beats varg's older [`varg-video-prompting`](../../varg-video-prompting/SKILL.md) and [`audio-lock.md`](../../varg-previz/references/audio-lock.md).

## 1. Move the picture, not the sound

The beat cannot move, so the edit delivers sync; the prompt only shapes performance: "Move the picture, not the
sound." (cinetic sound.md §4). No vendor documents frame-accurate obedience to an audio reference; no model is
measured for it. Slipping a clip to its contact frame is free; a re-roll is not [inference]. After each take, ours:
1. Strip sound with `-an` and the provider's flag; `audio: false` failed once (`varg-video-prompting` §10 [measured]).
2. Measure events from frames. "Write the measured in-points into the edit, not the requested ones." (same file, §9).
3. Slip the clip or retime it piecewise onto the grid. Re-roll only if the event is missing or the retime would show.
4. Check the muxed file: unhandled AAC priming puts audio 2112 samples late, 44 ms at 48 kHz ([Apple](https://developer.apple.com/library/archive/technotes/tn2258/_index.html)).
5. A person signs off on feel, which a checker cannot judge (earshot LIMITS). Never claim you heard it.

## 2. How to generate each shot, and what to do after

Call: sound on for mouths, then discard: silent generations "come back with barely moving mouths"
(`varg-video-prompting` §7 [measured]). Silent for the rest, native audio only for ambience. Table: ours [inference].

| Shot | Generate | Then |
|---|---|---|
| On-camera speech or singing | Sound on (not `audio: false` as in `audio-lock.md` §5), line in prompt, `@audio1` or black-screen reference, close-up, low action | Strip. Lay the locked take. Retime piecewise or run `sync_v3`; if both, retime first, since the model redraws the mouth at playback speed (untested [inference]) |
| Body in time with music | Audio or black-screen reference, role-bound, run under 10 s | Strip. Measure motion peaks. Retime to the grid or re-roll |
| B-roll, product, action cut to music | Silent where the model charges for audio (Veo 3.1 about 105 credits silent against 210 with audio per 5 s, [varg models](../../varg-ai/references/models.md); confirm with `estimate_cost`), otherwise strip. One beat of slack each side (`varg-video-prompting` §3) | Cut on the grid. Sound comes from the edit |
| Shot needing believable ambience or foley | Native audio on | Keep as a guide or layer. Replace hits with placed effects |
| Locked-off moment with a hit | Silent, event at a whole second, one beat of slack | Find the contact frame, slide it onto the beat |

## 3. Prompting from audio

Call: assume `@audio1` is re-performed and lay the locked track. Closer forms help performance, not final sound.

| Form or rule | What is reported, or what to do | Source |
|---|---|---|
| Direct `@audio1` | Re-performed with the model's own timing; a shout ran about 20% slower. Neither Seedance nor Kling played a voiceover verbatim | `varg-video-prompting` §6 [measured]; [Ozan Sihay](https://x.com/ozansihay/status/2117667049304396155) [self, translated]; [CellCog](https://cellcog.ai/blog/seedance-2-5-vs-kling-4-0/) [vendor] |
| Close-up, low action: closer, unmeasured | Near-verbatim in 3 of 3 runs, a wide action staging was not: "Audio reference reproduction in Seedance 2.5 is positional, not length-based." One creator reports good cartoon lip sync with "Preserve the audio and music exactly" plus the lyrics | [Wireflow](https://www.wireflow.ai/blog/real-voice-seedance-2-5) [vendor], 3 runs per condition; [thefinnmckenty](https://x.com/thefinnmckenty/status/2117314370397196671) [self] |
| Black-screen: closer, unmeasured | A black or blank video holding the audio, sent as the video reference: "much more consistent" than a direct file, "not 100% identical" | [SeeGen](https://seegen.ai/seedance-2-0-audio-guide) [vendor], no metrics; [MrDavids1](https://x.com/MrDavids1/status/2115485216361869757) [self], also on MiniMax H3 |
| Role binding | Give the audio one job: "@Audio1 provides tempo only", or "@Audio1 controls tempo and energy" with a video reference for camera. Hold native sound down: "No BGM; generate only environmental sounds and action sounds." | [Emily2040](https://github.com/Emily2040/seedance-2.0/blob/main/skills/seedance-audio/SKILL.md) [self], unmeasured; [Fuser](https://fuser.studio/articles/seedance-2-5-prompt-guide) [vendor] |
| Timestamps | Whole seconds, `[0-3s]`: "supports integer-second timestamps", "not frame-accurate edit points". One test put a line at 4.3 to 4.9 s inside a requested 2 to 5 s. H3 Max "can run up to about 0.7 s longer than requested". Finer forms exist, such as speech windows to 0.01 s, but nobody has measured whether a model obeys them | [BytePlus](https://docs.byteplus.com/en/docs/modelark/seedance-2-5-prompt-guide), [fal copy](https://fal.ai/learn/devs/how-to-use-seedance-2-5); Fuser [vendor], one run; [spec](https://varg.ai/models/minimax_h3_max.md); [Scenario](https://x.com/Scenario_gg/status/2102365314562294250) [vendor] |
| Instrument-hit cut maps | One route names each event as an instrument hit, with the rule "every cut on a hit of @Audio1". Its round-second times miss a 95 BPM grid: a beat is 632 ms, so 3 s falls 158 ms from the nearest beat (our arithmetic). Take times from your own song map [inference]; they stay requests and the edit lands the hit | Higgsfield route, [relayed by @Diplomeme](https://x.com/Diplomeme/status/2077986179895755110) [vendor] |
| Inputs and rights | Not every model takes an audio reference: on varg's specs [Kling 4](https://varg.ai/models/kling_v4.md) and [Veo 3.1](https://varg.ai/models/veo_3_1.md) do not, so read the live schema. Send only your own locked track, and voices you have the right to use | `models.md`; `video-sound` rule 8 |
| Prompt shape | `@Audio1 provides tempo only. No BGM; generate only environmental sounds and action sounds. [0-3s] The drummer raises both sticks. [3-5s] Both sticks strike the snare and the cymbal shakes from the hit.` | Ours, untested |

## 4. Three numbers that get merged into one

The split is ours [inference]. ITU writes + for sound early, section 5 writes −, so the second table uses words.

| Number | What it is | Figure | What to do |
|---|---|---|---|
| Placement precision | How exactly a script can put a sound | Under 5 ms, free | Place to the sample so nothing downstream eats the margin. Never report it as sync |
| Picture grid | The smallest step a cut can move | 41.7 ms at 24 fps, 40 at 25, 33.3 at 30, 16.7 at 60 | Snapping a beat to the nearest frame leaves up to ±20.8, ±20, ±16.7, ±8.3 ms. On a locked song, accept it or raise fps |
| Perception | What a viewer notices | Tens of ms, by content: a hammer stroke about 75 ms early to 188 late, speech 131 to 258 (Dixon & Spitz via [Eg & Behne](https://www.frontiersin.org/articles/10.3389/fpsyg.2015.00736/full), drifting offsets may inflate these [inference]) | Accept to the frame. Report offsets by sound type (section 5) |

| Source | Sound early | Sound late | What it is |
|---|---|---|---|
| [ITU-R BT.1359](https://itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1359-0-199802-S!!PDF-E.pdf): detectability (acceptability) | 45 ms (90) | 125 ms (185) | Averages of subjective tests on TV material |
| [EBU R37](https://tech.ebu.ch/docs/r/r037.pdf), end to end | 40 ms | 60 ms | Any output feeding emission. **Our defect line** for sounds not listed in section 5 |
| EBU R37, per production stage | 5 ms | 15 ms | Of these, the only one saying 5 ms: a budget that stops error building up along a chain |

| Claim to stop repeating | Why | Say instead |
|---|---|---|
| "Within 5 ms" as a perceptual or QA target | One synthesis parameter for whooshes: "`apex` puts a whoosh's loudest moment within 5 ms of the target" (earshot README). It is 12% of a 24 fps frame, so no cut moves in 5 ms steps, and mishandled AAC priming is about nine times larger (our arithmetic) | Placed to the sample, accepted to the frame |
| "a hit 80 ms after the cut already reads wrong" | No data: a rhetorical example in the earshot README and an [X post](https://x.com/Asteri_eth/status/2117629600901534024) [self]. 80 ms is inside ITU's 125 ms and outside EBU's 60 ms. `audio-lock.md` §4 and `varg-video-prompting` §9 still repeat it | Past 60 ms late is a defect (EBU R37) |

## 5. Offsets by sound type

Our synthesis [inference] from the earshot study and cinetic sound.md §13. Never blind-tested; no perceptual study of
a hit on a cut was found. Minus = sound before the picture event, plus = after. Measure sync points, not file starts.

| Sound | Sync point | Target against the picture event | Fix if outside |
|---|---|---|---|
| Click, tap | Onset | −10 to −30 ms (visible press) | Earlier than −60, later than +40 |
| Knock, thud | Onset | About −40 to 0 ms | −60 to +60 |
| Hit, slam, drop on a reveal | Onset, body on the frame | 0 to +40 ms, median about +20 | −40 to +75 |
| Pop-in | Onset | +25 to +40 ms | 0 to +75 |
| Word or text sound | Onset, on the full-opacity frame | +40 to +90 ms after first appearance | Audit by frame |
| Whoosh | Peak on the move's velocity peak, onset 100 to 450 ms ahead | ±45 ms | ±150 ms |
| Riser | End on the cut | 0 to +20 ms | Audible overlap with the hit |
| Dialogue to lips | Word onset | ±1 frame | Past 45 ms early or 125 ms late (ITU detectability) |
| Three or more similar layers | None | Loose | "none of them has to be in sync" ([Murch](https://sound.krotosaudio.com/walter-murch-interview/)) |

| The call on hit offset | Basis |
|---|---|
| Picture level with the hit or one frame ahead. Align the perceived body of the sound 0 to +40 ms after the picture event. Let short transients start up to 60 ms early | Sources look opposed because they measure attack against body [inference]: visual 2 frames ahead, never late (*The Animator's Survival Kit*, Richard Williams, p.272); attacks 30 to 200 ms before the cut (earshot study); "Each hit lands 1 frame after its visual event." ([Nervegna](https://nervegna.substack.com/p/how-to-build-a-motion-design-studio) [self]) |
| Two-frame lead (83 ms at 24 fps) only for deliberate animation accents, checked by a person's ear | Inside ITU's 125 ms, outside EBU's 60 ms. No opened source has a named film editor or sound designer stating an "N frames early" rule |
| Miss late rather than early. Have a person listen to anything past 60 ms late | Viewers forgive late sound more ([Hoffner, column](https://www.tvtechnology.com/opinions/av-synchronization-how-bad-is-bad) [self]). Table limits past 60 ms come from launch films, not a standard [inference] |

## 6. Most cuts get no hit

"Sound hits land on cuts" does not hold; exact-phrase searches found no public origin, so attribute it to nobody. In 7
launch films a salient hit sits within ±100 ms of a visual event 29% of the time, against 27% by chance (earshot
playbook). "About 85% of hard cuts carry no dedicated sound and under 5% a whoosh" (cinetic sound.md §13).

| Case | Rule | Basis |
|---|---|---|
| Limits of those figures | Launch style, one author, nothing equivalent for narrative film, UGC ads or TikTok edits. Final mix only, so quiet effects under loud music can go unseen. Some films lock part of the edit, up to 52% against 31% on the beat | earshot playbook |
| Dense music | Hits land on the moments that matter. Most cuts ride on the music. About 2 hits and 2 whooshes a film | cinetic sound.md §13 |
| Sparse or no music | "For a sparse soundtrack (no dense music) every cut needs sound" | earshot playbook, labelled practice, not measured |
| Music-driven | Grid as the default: structure on downbeats, ordinary cuts on any beat or eighth. In Lin's study, cuts on the accented first beat rated more pleasurable (d = 0.33) on sparse cuts; anticipation by a few frames was not tested. Map drops, stops and re-entries first: they land within 0 to 150 ms of a picture change in about 3/4 of scored films | cinetic timing-grid.md, sound.md §13; [Lin 2022](https://escholarship.org/uc/item/1rq255xj); depth in `music-video.md` |
| Off-grid cut | Declare it in the shot list: `off_grid: anticipation` or `off_grid: subvert`. `video-sound/scripts/sound.py check` flags any listed cut over a frame from the grid: tell the person those are deliberate. "Always" in [`varg-music-video`](../../varg-music-video/SKILL.md) is too strong | Our wording, untested; [`cue-sheet.md`](../../video-sound/references/cue-sheet.md) |

## 7. Measuring beats

Trackers are scored at ±70 ms ([mir_eval](https://raw.githubusercontent.com/craffel/mir_eval/main/mir_eval/beat.py)): Beat This! gets .986 on Ballroom, .627 on hard SMC ([arXiv 2605.12287](https://arxiv.org/html/2605.12287)). A
varg 97 BPM track first read as 129 (`varg-video-prompting` §8 [measured]). Procedure, ours [inference]:
1. Run two trackers from different families, for example Beat This! and librosa.
2. Metrical error test: tempos near 2:1, 3:2 or 4:3 mean one is wrong (97 to 129 is 4:3). Check a drum stem.
3. Render a click over the song for a person to hear. An agent cannot. Report beats as "±1 frame, confirmed by ear".
   If a tracker finds no beats in a section (one found none in the first 20 s of a 47 s track of ours), do not invent them:
   extend the grid from the confirmed tempo and a downbeat a person marks, or cut that section on picture logic [inference].
4. Use per-beat times: music drifts. `sound.py beats` extrapolates past `beats_tracked`, so use tracked beats only.
5. Snap each beat to the nearest onset at least 6 dB over the bed, within about ±35 ms (weaker ones match by chance).

| Tracker | Licence | Note |
|---|---|---|
| [Beat This!](https://raw.githubusercontent.com/CPJKU/beat_this/main/README.md) | MIT code and weights; training data rights left to you | Gives beats and downbeats |
| [librosa `beat_track`](https://raw.githubusercontent.com/librosa/librosa/main/librosa/beat.py) | Not checked in our research | Used by `sound.py beats`. Assumes a fairly steady tempo |
| [madmom](https://raw.githubusercontent.com/CPJKU/madmom/main/README.rst) | Model files CC BY-NC-SA 4.0 | Avoid in commercial work unless licensed |
| [Essentia](https://github.com/MTG/essentia) | AGPL-3.0 | [`RhythmExtractor2013`](https://essentia.upf.edu/reference/std_RhythmExtractor2013.html) needs 44.1 kHz, states no accuracy |

## 8. "Something changes every few seconds"

Retention advice on X with no data. MethodByVid wrote "SOMETHING CHANGES EVERY 2 TO 3 SECONDS" ([Aug 2026](https://x.com/MethodByVid/status/2089018850503451102)), then
"SOMETHING CHANGES EVERY 4 TO 6 SECONDS", adding "a transition effect doesnt count" ([Sep 2026](https://x.com/MethodByVid/status/2099815995502436365)) [self]. No controlled
study or A/B test ties an interval to retention. Use: something new every few seconds, at the format's rate.

| Format | Interval between changes, our synthesis [inference] | Basis |
|---|---|---|
| Crisp launch, hype | 0.5 to 1.5 s | cinetic timing-grid.md, house defaults |
| Calm launch, explainer | 1 to 3 s per shot, slow life between | cinetic; earshot median 0.63 events/s, one per 1.6 s |
| Short-form, ads | 2 to 4 s, denser in the first 3 s | Soft: [movez](https://movez.substack.com/p/how-to-build-motion-design-studio) [self]; [bytecap](https://www.bytecap.io/blog/optimal-short-form-video-length-retention-analysis) [vendor], search summary only; no retention study |
| Big Hollywood feature | About 3.6 s average (GoldenEye, Revenge of the Sith), action outlier 1.7 s | [Cutting](https://cinemetrics.uchicago.edu/article/590235ff-85aa-4714-9553-71d4c44fd61c) |
| Drama, long take, AI hero shot | 5 to 9 s or more if something inside changes | cinetic timing-grid.md |
| Music-driven | Set by the song's sections | [Caston](https://repository.uwl.ac.uk/4706/1/EditingDossiermsmi.2017.6.pdf) |

- A change is new information, an action, a camera move or a sound event, never a transition effect or a cut with
  nothing new. Vary the intervals, as film does ([Cutting via ScienceDaily](https://www.sciencedaily.com/releases/2010/02/100223121435.htm)).
- A checker fails only on a long dead stretch, never on a missed interval. Ours, untested: no listed change for over
  twice the format's upper figure. Cut detection counts a blinking cursor and misses slow crossfades (earshot LIMITS).

## 9. "Every motion has a cause"

The wording is from a 2026 skill for fake product UI demos, not film ([Stageshow](https://raw.githubusercontent.com/benjitaylor/skills/main/stageshow/SKILL.md)). The idea is old. Walt Disney: "the
driving force behind the action is the mood, the personality, the attitude of the character" (*Gesture Drawing for
Animation*, Walt Stanchfield, ed. Leo Brodie, p.5). Lasseter: "some part must initiate the move, like the engine of a
train." ([Lasseter 1987](https://www.ics.uci.edu/~fowlkes/class/ics162/exercises/lasseter.pdf)). No test shows it improves generated output. Do not cite Fincher for it: his reported camera
rule could not be verified. In a shot, ours and untested [inference]:
- Put cause and motion in one sentence with a time: `at 3 s the door slams and the curtain lifts from the draught`.
- Write out what must not move: locked-off camera, no drift. A camera move needs a cause too: subject, reveal or beat.
- QA on frame sheets: for each visible move, what started it? Unexplained moves are the fault list.
- The cue list names each cause. Product films: "Every sound has a visible cause; not every picture event gets a
  sound." (cinetic sound.md §4). Story: off-screen sound may be the point ([Randy Thom](http://filmsound.org/articles/designing_for_sound.htm)). Both: a cause in the story.

## 10. Mix facts that change the picture cut (picture and check columns ours [inference])

| Fact | Basis | In the picture | Check |
|---|---|---|---|
| Room tone runs under everything; without it the track risks "going dead" | [Wikipedia](https://en.wikipedia.org/wiki/Room_tone) | Stripped clips carry no room. Lay the bed across every cut before slipping picture | `sound.py check`: no unplanned gap under −60 dBFS; list deliberate stops in `silences` |
| Silence before a big hit: 30 to 250 ms, median 150, in every scored film but one | cinetic sound.md §13 | Keep those frames (about 4 at 24 fps) free of other accents; hold the hit frame fixed | Gap present at each hit's cue |
| Stop-downs: sound drops at least 10 dB for 0.15 to 1.5 s and returns on a hit, 4 of 7 films | earshot playbook | Put the reveal on the return | Return matches the reveal frame |
| "Two hits a few frames apart flam": 3 to 8 frames at 60 fps, about 50 to 130 ms | cinetic sound.md §12-13, earshot study | When two events sit that close, sound one or move one | Scan the cue list for gaps in that range |
| "Coverage is all or nothing": same action, same sound; discrete changes sound, continuous motion does not | cinetic sound.md §12-13, earshot study | Count repeats of an action before giving it a sound | 14 of 14 or 0 of 14 |
| End tail below −60 dBFS; a third of films end mid-note | cinetic sound.md §12-13, earshot study | Hold the last shot until the tail ends | Tail present in the final file |
| Sound needs room in the picture: let characters listen, leave dialogue pauses; slow motion and extreme wide shots open space | [Randy Thom](http://filmsound.org/articles/designing_for_sound.htm) | Write these into the previz, not the mix | Named in the shot list |
