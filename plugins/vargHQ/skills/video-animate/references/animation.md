# Animation: frame numbers, the cause chain, where cadence lives

`[vendor]` = company selling or reselling it, or a paid partner; `[self]` = one person's own report; `[measured]` = varg's own measurement, usually one film; `[inference]` = our reasoning, nobody tested it; no tag = opened primary source (docs, standard, paper, book).

Decides what every motion must contain, how many frames each beat gets, and whether a technique lives in the previz,
the prompt or the edit. Frame numbers are sourced, at 24 fps. Previz lines, prompt lines and thresholds marked "ours"
are our wording, untested on models unless stated. Looks are in `varg-character-cartoon`; this file adds motion only.

Books: Williams, *The Animator's Survival Kit*. T&J = Thomas and Johnston, *The Illusion of Life*. Goldberg, *Character
Animation Crash Course*. W&H = Whitaker and Halas, *Timing for Animation*. Blair, *Advanced Animation*. Stanchfield,
*Gesture Drawing for Animation*, Brodie ed. (*Drawn to Life* has a same-named lecture; not read). Lasseter, "Principles
of Traditional Animation Applied to 3D Computer Animation", SIGGRAPH 1987. "Snippet only" = search result, page not read.

## Every motion carries a chain: cause, anticipation, action, effect on others, settle

Write one chain per motion on the shot sheet; reject a motion with an empty field. The five-field chain is ours
[inference]. No master says "every motion has a cause" in those words, but each field has a root.

| Field | Write | Check (ours) | Root |
|---|---|---|---|
| Cause | who or what starts it: a mood, a plan, an outside force | the prompt's action sentence names it | Walt Disney, via Eric Larson and Stanchfield p.5: "the driving force behind the action is the mood, the personality, the attitude of the character". Stanchfield on drapery: "Reasons! Reasons! Reasons!" |
| Anticipation | the move the other way, and the weight shift | driver joint goes opposite the main move for 4+ frames | Stanchfield p.164: "Every move we make has two elements: anticipation and opposing force." Williams p.274: we think first, then do, so it shows thought |
| Action | which part starts it, then the order | peak speed runs hip, spine, shoulder, elbow, hand | Lasseter pp.38-39: "some part must initiate the move, like the engine of a train." Babbitt's successive breaking of joints (Williams p.231) |
| Effect on others | what it displaces or sets off: bodies, props, cloth, flesh | the result is on screen, not only the contact | Blair: a cop anticipates on 8, hits on 10, and that "main action between 8 and 10 has caused an overlapping lesser action" that runs to 24 |
| Settle | which parts stop last; heavy parts drag further and settle longer | nothing stops all at once | Walt Disney in T&J, Follow Through: "Things don't come to a stop all at once, guys; first there's one part and then another." Lasseter p.39 |

A heavy lift gets a prepared crouch, a feather none (Williams pp.264-265). Eian names cause and hands in the action
sentence, then checks a contact sheet every 0.4 s ([translated](https://x.com/EianLu/status/2117469941364637983) [self]).

## Frame numbers at 24 fps

| Item | Sourced numbers | Use (ours) | Source |
|---|---|---|---|
| Shortest hold | under 4 does not read; Avery's minimum 5; 6 registers, below it looks like a camera error; "You need at least 6 frames to read any accent" | Enforce automatically: no pose under 6 frames [inference] | Williams pp.271, 293; Goldberg, Timing |
| Longer holds | Disney pose hold 8 to 16; expression 12, stronger 16, 24 often too long. Worked: stands up fast, body held 8; look off-screen 12 before the cut; freeze after a fast throw 12; gag hold 24; title card about 16 per word | Pick per beat | T&J, Follow Through item 5; Goldberg, Timing; W&H |
| Ma | Miyazaki's emptiness placed on purpose: "The time in between my clapping is ma." No frame count exists; do not invent one | Mark it on an audio silence with a moving hold; "nothing happens; she breathes and the grass moves for 3 seconds" | [Ebert, via Medium](https://medium.com/@nayeonpark/ma-the-best-moments-in-a-studio-ghibli-film-are-silent-27210e215b21), snippet only |
| Step tempo | 4 very fast run, 6 run or very fast walk, 8 slow run or cartoon walk, 12 brisk natural walk, 16 stroll, 20 elderly or tired, 24 slow step, 32 drunk song tempo. Milt Kahl stopwatched real walkers on 12. Road Runner sheets ruled at 16 and 12; Babbitt on Tom and Jerry: "All on 8s" | Frames per beat = 1440 / BPM (our arithmetic): 12-frame steps read as 120 BPM, so match the walk to the song | Williams p.110 |
| Accent tempo | 2 stagger, shiver; 4 fast run, head shake, foot tap; 6 slower run; 8 normal run, hammering; 10 jog; 12 normal walk; 16 attitude walk; 18 to 24 tired slog, sneak. 6 vs 8 is perceived, 7 vs 8 is not | Change tempo by 2+ frames | Goldberg, Timing |
| Anticipation | minimum "even if it's just four frames or so"; eyes reach a sudden move about 5 frames later, so a small first move draws the eye; go the other way first, usually slower than the action; too much is corny. Magician: arm back 8, thrust into hat 4, hold 12, pull rabbit 6, hold and react 72. Wally B.'s zip-off is 3 or 4 frames: the more the audience expects, the faster the action can be | Opposite move of 4+ frames, no ratio; "he leans back for 0.3 s, then lunges in 0.15 s" | Goldberg; W&H; Williams pp.274-275, 280; Lasseter p.38 |
| Gravity | 0.08 m after 3 frames, 0.3 m after 6, 1.2 m after 12, 4.9 m after 24 | `y = y0 - 4.9*(f/24)^2`; fail if a dropped prop lands early | W&H |
| Disney take | 16: down on twos 1 to 5 (4), up on ones 5 to 8 (3, accent shown only 2), down on twos 8 to 16 (8); frame 16 is the pose the audience reads | `{antic: 4, up: 3, settle: 8}` | Williams pp.286-287 |
| Warner take | 14: down on twos 1 to 7 (6), pop 7 to 8 (1), down on ones 8 to 14 (6); the accent is only felt. All on twos, 16: 1 to 7, pop 7 to 9, 9 to 17 | `{antic: 6, pop: 1, settle: 6}`; "she sinks down for a quarter second, shoots up tall in a single frame, then settles for a quarter second into wide-eyed shock" | Williams pp.286-287 |
| Realistic take | Basil Rathbone: no anticipation, no stretch; head up in 3, cushions back 7 into a virtual hold, head fixed at screen centre | `{antic: 0, up: 3, settle: 7}`, head only, default for photoreal; "he stays still, then his head lifts sharply by a few centimetres and eases back, nothing else moves" | Williams p.293 |
| Overlap, drag | 2 frames of cause, 14 of effect: stomach recoils 13 to 16, bounces on 18, settles on 24. Avery's compound takes delay bits "often just 2 frames apart". A man in a light coat stops; the coat passes him, flops back, settles | 2-frame per-link lag, hip to hand; "he stops dead; the coat and hair keep moving forward, swing back, and settle by 0.6 s" | Blair; Williams p.290 |
| Accent against sound | visual 2 frames ahead; many live-action editors go 1/3 of a beat, 4 frames on a 12-frame beat; never late; he prefers animating level and advancing the picture in the edit. Others: attacks 30 to 200 ms before the cut ([earshot](https://raw.githubusercontent.com/Leonxlnx/earshot/main/docs/motion-sfx-study.md)); hits 0 to +75 ms after ([cinetic](https://raw.githubusercontent.com/Leonxlnx/cinetic/main/skills/cinetic/references/sound.md)); "Each hit lands 1 frame after its visual event." ([Nervegna](https://nervegna.substack.com/p/how-to-build-a-motion-design-studio)) | Use the call below, not the 1/3-beat lead, on a hit [inference] | Williams p.272 |
| Snap timing | very fast transitions, readable poses each side: "12f hold, 1f, 1f" into the next action | `hold 12, 1, 1, hold 12`; under 3 frames between poses, each pose at least 6 | Goldberg, "A word about quick timing", Gimmicks |
| Fall gag | Jones is quoted on "disappear for 14 frames before he hit". A frame review found no blank frames in Fast and Furrious (1949) or Beep Beep (1952), 42 in Gee Whiz-z-z-z (1956), 42 and 43 in Whoa Be Gone (1958), 31 and 32 in To Beep or Not to Beep (1963) | Hold above the drop, fall on the gravity curve, puff after 30 to 45 frames; "he hangs in the air, looks at camera, then drops out of frame; a puff of dust far below 1.5 s later" | [Brian Lemay](https://www.brianlemay.com/Pages/animationschool/animation/lipsyncbook/timingiseverything.html) |
| Head lean | same two extremes, the inbetween count sets the meaning: 0 hit by a tremendous force, 1 a brick, 2 nervous tic, 3 dodging, 4 crisp order, 5 friendly "come on", 6 sees something desirable, 7 a better look, 8 searching a shelf, 9 appraising, 10 stretching a sore muscle. Exposure is unstated | Pick ones or twos first; log the count per head move | T&J, Timing; Lasseter pp.37-38 |

**Our call on accents: picture level or one frame ahead. Align the perceived body of the sound 0 to +40 ms after the
picture event. Let short transients start up to 60 ms early. Lead by two frames (83 ms) only for deliberate animation
accents, checked by ear.** Sources measure different points of the sound, attack against body. See `sound-sync.md`.

## Where each technique lives

Our reading of the evidence [inference]; only the prompted cadence cell is measured. We found no frame-level test of
whether keyed anticipation or overshoot survives a model, and no named test that prompted them and measured the result.

| Technique | Previz | Prompt | Edit |
|---|---|---|---|
| Anticipation, overshoot | Best, keys carry it | Weak, unmeasured | Partial: slow the wind-up, cut the middle |
| Overlap, drag, settle | Only with cloak or hair bones | Likely fine, models simulate cloth | No |
| On twos, threes, modulated | Unknown if a stepped reference survives | Seedance 2.0 sometimes, Kling 2.5 no | Best; per-part or per-character rates need masks or layers |
| Holds, ma | Yes | Weak | Yes |
| Hit frame removal, impact flash, accent ahead of sound | Yes | No | Best |
| Smear, multiples | Stretched mesh, untested | Unreliable; model smear is usually a defect | Splice one image-model frame, untested |

## The hit: two classic moves as trims

Sourced as drawn animation. Using them as trims on generated footage is ours [inference], untested.

| Move | Source | Trim on a generated take |
|---|---|---|
| Ken Harris leap | remove the drawing before impact and stretch the contact drawing, so the action leaps a one-frame gap: "we won't see it, but we'll feel it" (Williams p.93) | find the frame before contact, remove it with the recipe below, pay it back with a slow frame earlier. A trim cannot stretch the drawing; that comes from the pose keys |
| Art Babbitt | "Don't ever show the hand hitting the chin", via Grim Natwick: show the result, the displaced chin. His punch has no contact frame; the sound goes where the fist is already past the face (Williams p.280) | cut the contact frames so the sound lands on the first frame past the face. Old Westerns did this, with a bang on it (Williams p.280). Try it against a slight pause in the middle, which lets contact be felt (Goldberg) |

## Cadence is a story choice, and it belongs in the edit

| Who | What they did | Source |
|---|---|---|
| Spider-Verse films | mostly 2s, some sections on 1s and 3s: "What we didn't like visually was the smoothness of being on 1s." No motion blur, motion lines and streaked backgrounds instead. Hobie: "his body's on 3s, sometimes other parts of his body are on 2s", "his jacket is on 4s" | Danny Dimian, [Cartoon Brew](https://www.cartoonbrew.com/feature-film/if-its-not-broke-break-it-sony-imageworks-renegade-approach-to-spider-man-into-the-spider-verse-167321.html); Alan Hawkins, [befores & afters](https://beforesandafters.com/2023/06/17/the-across-the-spider-verse-spider-punk-character-hobie-was-animated-with-different-frame-rates-for-different-parts-of-his-own-body-and-accessories/) |
| Puss in Boots: The Last Wish | hero on twos, the wolf on ones: "the wolf brings him back to reality with the animation on ones" | Joel Crawford, [TheWrap](https://www.thewrap.com/puss-in-boots-the-last-wish-director-joel-crawford/) |
| Anime | "As a rule of thumb, motion in anime is often animated every three frames", so 8 drawings per second; "Animation on the 4s can end up looking stilted" | Keisuke Shinohara, translated by [Sakuga Blog](https://blog.sakugabooru.com/2023/05/05/my-dress-up-darling-crosstalk-translation-series-director-keisuke-shinohara-x-character-designer-kazumasa-ishida-x-chief-animation-director-jun-yamazaki/) |
| Kanada style | irregular switching among 1s to 4s. One cut: 6-frame hold, jump to the next pose with no inbetween, aiming on 3s and 4s, the shot on 2s, fire on 1s for two frames | [Animétudes](https://animetudes.com/2021/03/06/the-kanada-style-in-context/) |

- Pick cadence per shot: ones for the threat's shot, twos for the hero's, copying Puss at shot level [inference].
- Run Williams' test (pp.78-79): render on ones, drop every other frame, compare; ones won in all but one case. A
  scramble, a sharp accent or the payoff after a big anticipation needs ones (T&J, Timing).
- Step only graphic surfaces: flat colour, line, no motion blur [inference]. Sakuga Blog argues the same drawing count
  [looks choppy in 3D](https://blog.sakugabooru.com/2016/08/01/embracing-the-3dcg-menace-ambitious-action-girls-und-panzer-the-movie/).
- Why the edit [inference]: it is free, exact, reversible and keeps audio sync. A prompt is a lottery and steps the
  camera too. Whether a stepped previz survives a model is unmeasured, so do not step the previz. The edit cannot add
  anticipation or a smear: "frame hold fixes pacing, not content" ([AIMZ](https://comfy.icu/node/AIMZ_CelAnimationRate)).

## Prompted cadence is a lottery [measured]

Ten public clips, 2026-11-03. A frame is held if its luma difference is under 25% of the local maximum in a +/-4 window
and that maximum exceeds 0.8. Control: a real clip through `fps=12,fps=24` and CRF 30 read 100% runs of 2.

| Clip | Model and instruction | Moving frames in runs of 1 / 2 / 3+ (%) | Reading |
|---|---|---|---|
| [BrettFromDJ](https://x.com/BrettFromDJ/status/2078676148960256144) | Seedance 2.0 on Higgsfield; "animated on twos at 12 frames per second" | 7 / 86 / 7 | Clean twos for 15 s, whole image including camera |
| [MaAyyoub](https://x.com/MaAyyoub/status/2077833166555889772) | Seedance 2.0 on Higgsfield; "True 12 frames per second, ANIMATED ON TWOS", "NO smooth interpolation, NO motion blur, NO morphing" | 49 / 36 / 15 | Partial: clean at 8 to 10 s only |
| [MayorKingAI](https://x.com/MayorKingAI/status/2082516459608219978) | Seedance 2.0 on Leonardo; mid-list style phrase | 88 / 12 / 0 | No twos |
| [Korgami 1](https://x.com/Korgamiai/status/2094340935018516706), [2](https://x.com/Korgamiai/status/2106719553392607306) | Kling 2.5; "CADENCE IS THE MOST IMPORTANT RULE"; softer "two-frame exposure cadence" | 83 / 17 / 0; 97 / 1 / 2 | No real holds in either |
| [HeyAbhishek](https://x.com/HeyAbhishek/status/2117591914073764151) | Seedance 2.5; no cadence words | 85 / 3 / 12 | Baseline, on ones |

- One clean and one partial out of five cadence prompts. Each row is one uncontrolled clip, X re-encodes, and the metric
  cannot separate generation from the poster's edits. Clean results may be selected takes
  ([tebasaki3D](https://x.com/tebasaki3D/status/2078074904533147923) [self]).
- No data for Seedance 2.5, Kling 3 or 4, Veo 3.1, Wan 3 or MiniMax H3 under a cadence prompt. Do not promise it, and
  measure any take prompted for it. Whether Higgsfield post-processed its clips is unknown.
- Do not prompt smears: the MayorKingAI clip asks for "action smears"; one frame sheet at a peak shows none [measured].

## ffmpeg recipes [measured]

Tested on ffmpeg 9.0.2 with a 96-frame source. `-vsync` no longer exists there, use `-fps_mode`. Count frames afterwards.

| Goal | Filter, exact | Result | Locked audio |
|---|---|---|---|
| On twos, on threes | `-vf "fps=12,fps=24"`; threes `fps=8,fps=24` | twos: 96 frames, 48 unique, every run 2. Threes: runs of 3 on a real clip, 87% in the CRF 30 control | Keeps length |
| Kanada-style modulation | `-vf "select='if(lt(t,1),1,if(lt(t,2),not(mod(n,2)),if(lt(t,3),not(mod(n,3)),not(mod(n,4)))))',fps=24"` | 96 frames with runs 1x24, 2x12, 3x8, 4x6 | Keeps length |
| Impact flash | `-vf "negate=enable='between(n,48,49)'"` | inverts only frames 48 to 49 | Keeps length |
| Ken Harris leap | `select='not(eq(n,47))',setpts=N/24/TB` | removes the frame before impact, 95 frames | **Loses one frame.** Duplicate a slow frame earlier, as [Kitamura et al.](https://www.cgg.cs.tsukuba.ac.jp/projects/2013/motion_frame_omission/data/IWAIT.pdf) do: delete the fastest frames, duplicate the slowest, cap duplicates at three |
| Do not use | `select='not(mod(n,2))' -fps_mode cfr -r 24` | loses a frame (95, first run 1) | **Avoid on locked audio** |

`select` followed by `fps=24` does not leap; it holds the previous frame. Set the modulation windows per shot [inference].

## Camera strobing

A character on twos under a camera panning on ones strobes (Williams p.79; Goldberg). Feet in contact with a panning
background must be on ones or they slip (T&J). Spider-Verse breaks this on purpose: "Almost every shot in the movie the
cameras are on ones", characters every other frame (WIRED, "How Animators Created the Spider-Verse", transcript,
attributed to Joshua Beveridge, speaker not labelled in the passage). The edit recipes step the camera too. Fix, untested
in our pipeline [inference]: generate locked-off or slow-camera plates, step the plate, then add the move on ones.

## What to key in Blender or three.js

Recommended order [inference]: 1. mocap, Mixamo or Cartwheel as a base for human weight, or hand keys for a cartoon.
2. Push with phase offsets and a filter. 3. Add explicit take data. 4. Render the reference. 5. Leave cadence to the edit.

| Key | Number | Check (ours, computable from the joint curves before any render) |
|---|---|---|
| Base | agent-keyed motion feels mechanical, pose extraction kept natural dynamics ([ShiZhen AI](https://www.besthub.dev/articles/how-to-use-blender-for-ai-video-previsualization-before-seedance-generation-adc9fec7c95c) [self]); human mocap put on a chicken "will look like a human in a chicken suit", though it looks realistic on a human (Lasseter, in Kitamura et al.) | the clip must really move: with a still mannequin "Seedance came up with the dance" ([Atg_Tsukimao](https://x.com/Atg_Tsukimao/status/2116406711737344126) [self]); otherwise it can be "sometimes too precise" (u/leepuznowski, r/comfyui, May 2026 [self]) |
| Push | `x*(t) = x(t) - G * x''(t)` at amplitude 3; handle planted feet ([Wang et al., SIGGRAPH 2006](https://grail.cs.washington.edu/wp-content/uploads/2015/08/wang-2006-tca.pdf)) | a 12-frame move at A=3, sigma=4 frames gives 30% anticipation from 6 frames early and 30% overshoot [measured, numeric check]. It is symmetric, unlike Williams' slow anticipation and fast action: hand-key the big moves [inference] |
| Wind-up, per-link lag | 4+ frames opposite (Goldberg); 2 frames per link (Avery's bits, Williams p.290) | opposite-sign peak before each fast move; `T - link * 2 / 24`, hip 0, spine 1, shoulder 2, elbow 3, hand 4; add it to `walk()` in `threejs-animatic/references/mannequin-rig.md` |
| Take, pop | takes above | phase lengths, joint list, pop flag. Pop = no blend across one frame; the rig note "a pose change is a blend over a few frames, never a pop" stays right for realistic only |
| Arcs, holds, drops, contact | most living motion is an arc (T&J, Arcs); holds 6+; gravity row; one contact frame before compression (Ken Harris, Williams pp.93-95) | a straight wrist or head path between keys fails; no pose change between accents under 6; a realistic root drifts; every drop on the curve; foot at floor height, no knee bend yet |
| Stretch | constant volume; fast objects stretch until positions overlap frame to frame, which removes strobing (Lasseter p.37) | `sx = sy = 1/Math.sqrt(s)`; a stretched mesh may read as an artefact to the model, test first |
| Cloak, hair | extra bones: "the cloak swings and settles after every stop and turn" ([rewind02](https://x.com/rewind02/status/2115779810932728259) [self]) | no bones, then the prompt carries the drag |

| Motion source | Use | Terms to check |
|---|---|---|
| [CMU mocap](http://mocap.cs.cmu.edu/), [Rain rig](https://studio.blender.org/characters/rain), [Rokoko Motion Library](https://rokoko.com/pricing/) [vendor] | asset | CMU: "This dataset of motions is free for all uses."; no resale; toes and hands are noisy; check each derivative. Rain: CC-BY, credit "Rain Rig (CC) Blender Foundation". Rokoko: commercial use allowed for the library, other output unstated |
| [Mixamo](https://helpx.adobe.com/bg/creative-cloud/faq/mixamo-faq.html), [Cartwheel](https://www.getcartwheel.com/pricing) [vendor] | base | Mixamo: royalty free, commercial allowed (Adobe FAQ, snippet only); not for training models per a [2022 community post](https://community.adobe.com/questions-696/mixamo-faq-licensing-royalties-ownership-eula-and-tos-589400) [self]; use as a video-model reference is not addressed, get a legal read. Cartwheel: commercial terms not on the page |
| [Sakugabooru](https://www.sakugabooru.com/wiki/show?title=help:about), [Line of Action](https://line-of-action.com/terms-conditions), Endless Reference, classic shorts | **study by people only; never feed them to a model or a bot** | Sakugabooru: no licence or reuse terms found, assume studio copyright. Line of Action: "for personal, non-commercial transitory viewing only". Endless Reference: licence not verified. Goldberg tells readers to frame-step shorts |

## Cartoon comedy catalogue

| Trick | Method and numbers (sourced; unmeasured on models, so build in previz or edit) | Source |
|---|---|---|
| Wild take | eye registers an action in "five frames of film"; anvil comes in "four or five frames before the hit"; pair it with "equally wild sound effects". No standard length: one measured take is 149 frames, whole body on ones, eyes keep moving | [Cartoon Brew](https://www.cartoonbrew.com/classic/a-thrilling-tour-through-the-history-of-wild-takes-in-animation-243744.html); [Tralfaz](https://tralfaz.blogspot.com/2024/08/big-city-red-riding-hood.html) |
| Smear, multiples | smear wipes across the farthest points of both keys, one frame, "almost never on twos"; mini-smear helps an arc, ignores volume, one frame; multiples: 12f hold, 1f, 1f, usually one more inbetween, 12f hold. Study Wackiki Wabbit, Long-Haired Hare, A Corny Concerto | Goldberg, Gimmicks; Williams p.96 |
| Zip-off | draw back, one or two drawings forward, then speed lines or a dust puff that disperses in not less than 12 frames; drybrush 16 or more. Or anticipate the exit with no drawings going out, and he is gone | W&H; Williams p.276 |
| Impact star, impact frame | star: solid, usually white shape grows from the impact and breaks up, on ones, long enough to flash, not to overtake the action. Frame: "Usually monochromatic or otherwise chromatically stylized drawings hidden within sequences"; Kanada used black and/or white. Use the flash recipe | Goldberg; [Sakuga Blog](https://blog.sakugabooru.com/glossary/impact-frames/); [Animétudes](https://animetudes.com/2021/03/06/the-kanada-style-in-context/) |
| Stagger | interleave drawings: forward 3, back 2, erratic exposure is fine. Vibrating take: inbetween 1 to 13 on odds and 2 to 13 on evens, shoot consecutively | Williams pp.297-298; W&H |
| Gravity as the joke | "Whenever possible, make gravity the coyote's greatest enemy", as quoted. State the cause: the character's own plan and gravity [inference] | [Gurney Journey](https://gurneyjourney.blogspot.com/2017/03/chuck-jones-on-creative-discipline.html) |
| Squash and stretch | constant volume: scale up along the path, down across it. Ken Harris used it sparingly; too much looks like rubber | Lasseter p.37; Williams pp.39, 93 |

## Claims that do not survive checking

| Do not repeat as fact | What checking found |
|---|---|
| "Anticipation is 2 to 3 times the action" | No master states it. Sourced cases: 4:3 (Disney take), 2:1 (magician), 6:1 (Warner take). A [skills page](https://playbooks.com/skills/dylantarre/animation-principles/anticipation-mastery) says 30 to 50% of the action (snippet only). Use frames, not a ratio |
| A fixed squash and stretch ratio, such as "stretch is 1.5x" | Not in Williams, T&J, Goldberg, Blair or Lasseter. The rule is constant volume |
| "The Dover Boys invented the smear" | False by these sources: Battling Bosko (1932) is listed earlier ([Bloop](https://www.bloopanimation.com/the-art-of-smear-frames/)), and stretched inbetweens came earlier in films crediting Ken Harris, before Jones was credited for Dover Boys ([Cartoon Research](https://cartoonresearch.com/index.php/the-partial-and-mostly-lost-history-of-animation-smear-terminology/)) |
| The Mitchells vs the Machines is stepped | Its animation supervisor: "It didn't seem appropriate for this film to do anything other than fully fleshed out." ([Alan Hawkins](https://beforesandafters.com/2021/04/29/the-way-we-animated-those-was-completely-new/)) |
| The Road Runner rules were a production document | Traced to Chuck Amuck p.225, read only through quotes. [Tralfaz](https://tralfaz.blogspot.com/2018/08/rule-1-is-broken.html) argues Jones wrote them long after the films, and shorts break them. Use them as a cause idea, not as history |
| "Arcane's characters are on twos", "ones in fights, twos for the punch" | No primary source. A [2024 article](https://redsharknews.com/why-netflixs-arcane-looks-so-good-how-fortiche-ramped-up-the-animation-pipeline) says hand-drawn effects at 12 fps and characters at 24, quoting no Fortiche staff |
| Impact frames last a set number of frames | No sourced count; the [glossary](https://blog.sakugabooru.com/glossary/impact-frames/) says a fraction of a second. 1 to 2 frames is a working assumption only |

## Realistic versus stylized

| Choice | Realistic (default ours [inference]) | Stylized (default ours [inference]) | Source of the numbers |
|---|---|---|---|
| Cadence | ones | twos or threes, per shot, or modulated in the edit | Williams p.79; Sakuga Blog 2016 |
| Holds, blinks | moving hold, blinks every 3 to 5 s, once mid-turn unless frightened (Williams p.87); on CG, cushion slowly into the pose over the hold | a graphic character holds longer; 6+ frames | W&H; Goldberg |
| Take, anticipation | Rathbone, head only; small anticipation | Warner, or Disney when the pose must read; opposite move of 4+ frames | Williams pp.286-287, 293; Goldberg |
| Pose change | blend over a few frames | pop or snap, the pop is the joke | `mannequin-rig.md`; Goldberg, snap timing |
| Blur, smear | natural blur; subtle mini-smear at most | no blur, motion lines instead; one-frame smear spliced in post, untested | Spider-Verse above; Goldberg |
