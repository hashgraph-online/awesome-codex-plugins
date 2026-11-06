# Motion references

A motion reference is data, not a picture. A good one proves how long a move takes, where speed peaks, what holds, what
lands and what trails. It does not prove the look, and a still frame proves nothing about motion.

**A search query and a motion spec are different things.** A search box finds "kinetic type". It cannot find "2-frame
holds, overshoot 1.2". `tested 2026-11-03`: `kinetic type, hard cut on the beat, 2-frame holds, overshoot 1.2` on Refs
matched no film on every word and returned 4,472. It is a good spec and a bad query. So:

1. Search with one or two format nouns, plus filters.
2. Pick by eye. Totals are not quality, so read the top 3 or 4.
3. Get a clip you may process, then measure it with [`motion_read.py`](../scripts/motion_read.py).
4. Write the spec from the numbers.

**Step 3 is often where it stops.** Refs and whatships show which films to watch and give no clip you may process, so
nothing is measurable from them: a person watches. Clips you may process come from Commons `filetype:video`, your own work
or a licence, and they rarely match the brief. In the ad cold run no open clip was close and no 9:16 open clip turned up,
so for an ad the person watches and supplies the clip, and you measure that. In the cold run on a coded film no code-made
launch film could be measured: the numbers came from a station clock and a 10 s kinetic type clip, and neither gave a
whole-film structure.

## Read it

A useful reference answers up to eight measurable questions. Fill in the rows it is for: a station clock has no stagger. If
you cannot, you need the frames or another clip.
UI rules come from interface design, and film holds run on other budgets, so label every number by domain. Anchors are
`reported` unless marked. motionmaxxing's numbers are its own, from AI agents reviewed by a human, not independently
checked.

| Feature | Read it with | Anchor and its domain |
|---|---|---|
| Timing | Frames from motion start to settle: `elements`, `camera`, `scale` | 3-7 s pro moments: median move 10 frames, 0.33 s ([motionmaxxing](https://github.com/Tejashmakwana/motionmaxxing)) |
| Spacing | Position curve: `elements`, `camera` | "where an object is in each of the 24 frames" ([Pluralsight](https://www.pluralsight.com/resources/blog/software-development/character-animation-fundamentals-timing-spacing)) |
| Easing | t50, t90, overshoot: `camera`, `elements`, `scale` | Overshoot on 8.8% of moves (motionmaxxing). `tested`: 13 of 40 featured Lottie files use overshoot or anticipation handles |
| Stagger | Onset per region: `elements --grid` | UI: standard 50-100 ms, "Total stagger MUST stay <500ms" ([LottieFiles tables](https://raw.githubusercontent.com/LottieFiles/motion-design-skill/main/skills/motion-design/reference/timing-easing-tables.md)) |
| Holds | Repeat pattern: `holds` | Hand animation: a six-frame stride on twos reads heavy ([Miyazaki via Animation Obsessive](https://animationobsessive.substack.com/p/hayao-miyazaki-on-running)) |
| Transitions | Frames around each cut: `cuts`, motion sheet | 3-7 s moments, not whole films: "96% of moments use hard cuts" (motionmaxxing) |
| Secondary motion | Element offset after the main stop: `elements --crop` per part | UI: "child elements trail 50-150ms" ([LottieFiles](https://raw.githubusercontent.com/LottieFiles/motion-design-skill/main/skills/motion-design/reference/troubleshooting.md)) |
| Camera | Pan, tilt, zoom, roll, jitter: `camera` | Generated shots: "one clear camera move and one clear subject action" ([Sora 2 guide](https://developers.openai.com/cookbook/examples/sora/sora2_prompting_guide)) |

Work in this order: cuts, motion sheet, holds, camera on the 2 or 3 shots that matter, beat check. Do not measure every
shot.

## Measure it

`tested 2026-11-03` with ffmpeg 9.0.2, PySceneDetect 0.7.2, OpenCV 5.0.0 and Python 3.12 on
["Spring"](https://commons.wikimedia.org/wiki/File:Spring_-_Blender_Open_Movie.webm) (Blender Studio, CC BY 4.0, 464.141
s, 2048x858, 24 fps), on ["Trick or
Treat"](https://commons.wikimedia.org/wiki/File:%27Trick_or_Treat%27_-_Kinetic_Typography.webm) (Conanda Sixteinliesena,
CC BY 3.0, 10.1 s, 540x360, flat black and white) and on clips we rendered with known motion. Only the rendered clips have
ground truth, and a moving subject contaminates every global read. Blocks show real output, with some fields left out, and
shorten the command to `motion_read.py`. Run from the project folder with `S=<skill folder>/scripts`, and pin Python 3.12:
an install on 3.15 did not finish in over 5 minutes. For `cuts`, use `--with scenedetect --with opencv-python` instead. `holds` needs
only ffmpeg.

```bash
uv run --no-project --python 3.12 --with opencv-python --with numpy python -I "$S/motion_read.py" camera clip.mp4
```

**Frame rate.** Every read takes it from the packet timestamps and checks both header values. `avg_frame_rate` is 1000/1
on 2 of 4 Commons WebMs from the cold run on a coded film (`r_frame_rate` 25/1 and 24/1), because hidden VP8 frames share
a timestamp. Trusting it gave Trick or Treat 237.2 cuts a minute and a shot of -7.547 s. Now it reads 5.9, shortest 2.32
s, the same as on a re-encode. If the values disagree or the rate varies, it warns and prints the re-encode command:
`ffmpeg -i clip.webm -vf fps=25.0 -an -c:v libx264 -crf 18 -pix_fmt yuv420p constant.mp4`. An impossible result (a
negative shot, a rate outside 1 to 240) exits with an error.

**Cuts.** On Spring, a dark film, ffmpeg `scene>0.3` found 37 and `scdet` found 50. 12 of 12 sampled extra cuts were real,
and the other 44 are unchecked. A rendered clip with cuts at 2, 4 and 6 s read `[2.0, 4.0, 6.0]`. Look at the frames it
saves.

```text
$ motion_read.py cuts spring.webm --out spring_cuts
 "cuts": 93,
 "cuts_per_minute": 12.0,
 "shot_length_s": {"mean": 4.94, "median": 4.0, "p10": 1.44, "p90": 8.22, "shortest": 0.583, "longest": 46.194},
 "cut_times_s": [7.014, 12.014, 15.639, 16.931, 22.972, ...],
```

On a flat graphic clip, compare `--detector adaptive` (the default) and `--detector content`, and look at the frames. On
Trick or Treat, adaptive found `[7.8]` and content `[3.24, 7.8]`, the same as ffmpeg `scene>0.3`. On a rendered flat clip
with cuts at 2, 4, 4.48, 4.96 and 8 s, adaptive missed one and content two, because PySceneDetect holds a shot to 0.6 s:
`--min-shot 0.04` gave both all five. It can over-read too: content with `--min-shot 0.04` read 21 cuts in 10 s on
Cautiva, a busy clip. On the rendered clip above, content found none of 3. Neither reports a ground that only changes
tone.

**Motion sheet.** Every 6th frame, 0.25 s apart at 24 fps. It shows pace and the moves inside a shot. `drawtext` was
missing from our ffmpeg build, so do not count on burned-in timecode.

```bash
ffmpeg -y -ss 60 -t 8 -i ref.webm -an -vf "select='not(mod(n\,6))',scale=240:-2,tile=8x4" -frames:v 1 -fps_mode vfr sheet.png
```

**Holds.** The clip below is drawn on twos, with temporal grain added.

```text
$ motion_read.py holds twos_grain.mp4
 "plain": {"frames": 48, "keep": 48, "drop": 0, "reads_as": "on ones", "longest_hold_frames": 1, "pattern": "KKKKKKKK..."},
 "denoised": {"frames": 48, "keep": 23, "drop": 25, "reads_as": "on twos", "longest_hold_frames": 5, "pattern": "KdKdKdKd..."}
```

Believe a regular pattern, not a count. On Spring 60-68 s the drop count moved with read size alone: 15 at full size, 41
at 640 wide, 74 at 160 wide. A slow move reads as holds. Reading holds on real cel animation is untested. `--stills` adds
freezes over 0.5 s: 11 on Spring, and it also counts black at fades.

**Camera.** One shot at a time. t50 and t90 are the share of the time at which the move has covered 50% and 90% of its
travel. `speed_cv` is the spread of frame speed over its mean. Jitter is what is left after a 9-frame moving average.

```text
$ motion_read.py camera spring.webm --start 296.147 --end 298.547
 "frames": 58,
 "move": ["tilt", "zoom", "roll"],
 "travel_px_480w": 398.4,
 "zoom_pct_s": 8.82,
 "roll_deg_s": 1.367,
 "speed_cv": 0.74,
 "jitter_px_320w": 1.44,
 "ease_phase": {"t50": 0.351, "t90": 0.649, "overshoot_pct": 0.27, "nearest_named": [["power1.out", 0.0418], ...], "cubic_bezier": [0.729, 1.035, 0.311, 0.82], "bezier_rmse": 0.0199},
 "ease_flow": {"t50": 0.316, "t90": 0.579, "overshoot_pct": 0.42, "nearest_named": [["power1.out", 0.0571], ...], "cubic_bezier": [0.232, 0.127, 0.359, 1.145], "bezier_rmse": 0.014},
 "warnings": ["The two reads give different curves. Report t50 and t90 as a range, not one number."]
```

On four rendered clips of 48 frames, true travel 360, the nearest named ease was right every time (`power2.out`, `expo.out`,
`back.out(1.7)`, `power2.out` on threes). Phase read 358.0 to 359.5. Flow read 360.2 and 360.3 on two, and lost track with a
warning on the others (317.8, 189.1). `back.out(1.7)`, true 9.98%, read 10.63%.

A rendered zoom of +50% with a 12° roll in 1.958 s (true 25.53 %/s, 6.128°/s) read 25.67 %/s and -6.132°/s. Signs follow
the picture: a negative pan slides it left, so the camera turns right, and a negative roll turns it counter-clockwise.
When the zoom and roll warning fires, `zoom_pct_s` and `roll_deg_s` print null: a plain pan once read `"zoom_pct_s":
14462.52`.

- Phase correlation holds on big frame jumps, where flow loses track, but has no model of zoom. When `move` lists zoom
  or roll, prefer `ease_flow` (`our proposal`). Otherwise prefer `ease_phase`.
- Set `--start` and `--end` one or two frames inside the cuts, or the cut reads as motion. Moving the window above one
  frame earlier took flow overshoot from 0.42% to 1.74%, so write an overshoot under 2% on real footage as "tiny", not
  as a number.
- Never trust a fitted bezier without t50 and t90. A linear truth came back as `.401, .4, .4, .4`: the same curve, odd
  numbers. `bezier_rmse` over 0.05 means the shot moves, then rests, so split at the rest.

**Elements on flat ground**, for type or UI that slides. Position only. Use `--crop X:Y:W:H` to isolate one element.
Kinetic type mostly moves by scale, so it warns when the size changes more than the position. `--grid` prints null and a
warning if the ground is not flat (under 0.8 of the picture in its two commonest levels) or every cell has one onset.

```text
$ motion_read.py elements el_back.mp4         # truth: starts frame 6, 17 frames, back.out(1.7), 10% overshoot
 "move_starts_at_frame": 6, "move_frames": 17, "overshoot_pct": 9.7, "nearest_named": [["back.out(1.7)", 0.0016], ...]
$ motion_read.py elements el_stagger.mp4 --grid 5x1   # truth: onsets 4, 7, 10, 13, 16
 "onset_frames": {"col0_row0": 4, "col1_row0": 7, "col2_row0": 10, "col3_row0": 13, "col4_row0": 16}, "stagger_frames": [3, 3, 3, 3]
$ motion_read.py elements trick_or_treat.webm --start 1.28 --end 2.0     # truth: a disc grows
 "travel_px": 15.4, "size_change_px": 234, "warnings": ["This reads position only. The element's size changes by 234 px ... Run scale."]
$ motion_read.py elements split_flap.webm --grid 6x6      # a photographed board
 "flat_share": 0.25, "onset_frames": null, "stagger_frames": null, "warnings": ["Could not read: the ground is not flat ...", ...]
```

**Scale on flat ground.** Width and height of what differs from the ground, per frame, then the fast part, the settle and
the hold. One move at a time: start the window on the ground or a held frame, and `--crop` to one element.

```text
$ motion_read.py scale block.mp4     # truth: height 47 held, then 100, 154, 207, 260 on frames 5 to 8, then held
 "move_starts_at_frame": 5, "fast_frames": 4, "settle_frames": 0, "hold_after_frames": 10, "height_px": {"start": 47, "end": 260, ...}, "nearest_named": [["none", 0.0014], ...]
$ motion_read.py scale trick_or_treat.webm --start 1.24 --end 2.04      # real clip: a word, then a disc grows
 "fast_frames": 4, "fast_steps_px": [23, 84, 85, 44], "settle_frames": 15, "settle_pct_per_frame": 0.56, "height_px": {"start": 25, "end": 284, ...}
```

A rendered `back.out(1.7)` of 17 frames read 16, overshoot 9.39% against a true 9.98%, nearest `back.out(1.7)`. A rendered
13-frame creep of 0.5% read 13 frames, 0.51%. It reads a box, so it cannot measure rotation (a turning bar warns that the
box changes and the area does not), part two elements, see past the frame edge, or tell a growing word from one gaining
letters. Width and height changing by different factors warns about those last two. Its only real-clip test so far is
Trick or Treat.

**Beat check.** Get beats with `scripts/sound.py beats` in the `video-sound` skill, count cuts near a beat and compare
with chance (2 x window / beat period). Spring, within ±1, ±2, ±3 frames: 16.1%, 29.0%, 43.0%, against chance 14.4%,
28.7%, 43.1%. It is not cut to the beat, and the test says so. We had no legal clip known to be cut on the beat to test
it.

**Card.** Write one per picked shot (`our proposal`), then run the same commands on your own render and compare.

```json
{"ref":"Spring, Blender Studio, CC BY 4.0","in":296.147,"out":298.547,"frames":58,"fps":24,"move":"tilt, slight zoom",
 "t50":[0.316,0.351],"t90":[0.579,0.649],"overshoot":"tiny","jitter_px_320w":1.44,"ease":".232,.127,.359,1.145","cuts_on_beat":false}
```

## Search it

Results are `tested 2026-11-03`. The rights tag says what the reference may do: `feed`, `words` or `look`.

| Source | First call | What came back | Access | Rights | Verdict |
|---|---|---|---|---|---|
| [Refs](https://refs.video/mcp) | `search.py refs '{"query":"kinetic type","category":"motion","ai_made":false,"limit":8}'` | 64; `ai_made:true` 15. `{"query":"launch","made_with":"hyperframes"}` 3; `"made_with":"remotion","max_seconds":60` 4. Short cards with a summary and a thumbnail, no clip, 30 searches an hour, 48 unique at most. Cards can say `locked: library` ($6 a month per Refs' note): 89 of 89 in the ad cold run. Blueprints need Pro. [Terms](https://refs.video/terms) bar bulk export | `agent`; Pro `token` | `words`; thumbnails `look` | Best for picking a format, and the only source tested with a working AI filter. `ai_made:false` removes code-made films, and `ai_made:true` mixes code with generated (Moonvalley, Veo, Vidu, Leonardo and Stability in the 41 cards read). For a coded piece use `made_with`. Facts in `sources.md` |
| [Commons API](https://commons.wikimedia.org/w/api.php) `filetype:video` | `search.py commons "filetype:video kinetic typography"`. It appends `filetype:bitmap` unless you pass `filetype:` | `kinetic typography` 2, both CC BY 3.0; `split-flap` 13, CC0 to CC BY-SA; `Bahnhofsuhr` 1, CC BY-SA 4.0; `motion graphics` 95 | `agent` | CC0 or public domain with no person `feed`. CC BY, BY-SA `words`, and you may measure them | The open source of clips you may process. Check `bytes` first: the clock is 72 MB |
| [whatships](https://whatships.com) | [`/search-index.json`](https://whatships.com/search-index.json), then `/videos/{slug}/` | 2,908 entries: 2,786 videos, 109 tools, 13 studios. `swiss` 0, `invoicing` 1, `kinetic` 1 | `agent` for the catalogue; a person watches | `look` | The one open catalogue of launch films. Its [`llms.txt`](https://whatships.com/llms.txt) lists "downloading videos as a CDN" as not a fit, so link it, a person watches, and do not process its clips |
| Your own read | `motion_read.py` above | Known eases, holds and stagger recovered | `agent` | Owned, licensed, CC0 or public domain with no identifiable person: `feed`. CC BY, BY-SA and the rest: `words` | Only free route to frame numbers |
| LottieFiles | `featuredPublicAnimations(first:40)` at `https://graphql.lottiefiles.com/2022-08` | 3,418 featured. Undocumented API. In 40 files the top curves were `.33,0,.67,1` (31 files) and linear `.17,.17,.83,.83` (29), so read a file before copying it | `agent` | `words`: the [licence](https://lottiefiles.com/page/license) does not address machine learning | Best for real keyframes and bezier handles |
| [motionmaxxing](https://github.com/Tejashmakwana/motionmaxxing) | README, then `library/moments.jsonl` (not opened) | About 4,288 moves, 53 moments, its own measurement | `agent` | `words` | Useful anchors |
| [Sakugabooru](https://www.sakugabooru.com/help/api) | `/post.json?tags=smears+order:score&limit=3`, metadata only | `smears` 62,126; top score 5934 | `agent`, metadata only | `words`, study only | Best for hand-timing. Robots allow reference use for `*` and name ClaudeBot under training crawlers, so keep to targeted reads |
| [Motionographer](https://motionographer.com/tag/project_breakdown/) | `/tag/project_breakdown/`, `/wp-json/wp/v2/posts?search=breakdown` | 200 | `agent` | `words` | Good, makers explain the work |
| [Codrops on GitHub](https://github.com/codrops), [three.js examples](https://threejs.org/examples/) | `gh search repos --owner codrops "GSAP" --limit 5`; `/examples/files.json` | LiquidDistortion 475 stars; JSON returned | `agent` | `words`; code per repo licence | Source you can read. The Codrops site itself is 403 |
| [Are.na](https://www.are.na/developers/all.md) | `https://api.are.na/v2/search/channels?q=kinetic%20type&per=5` | 28 pages; channels of 326, 274, 223 blocks. In one, 100 of 100 sampled blocks are GIFs | `agent`, targeted only: its terms bar harvesting | `words` | Good for seeing. Never time from a GIF |
| [Promo News](https://www.promonews.tv/videos), [Antville](https://videos.antville.org/), [D&AD](https://www.dandad.org/work/d-ad-awards-archive), [Clio](https://clios.com/winners-gallery/explore?vertical=Clio+Awards&season=2026) | Director name, award category, year | Feeds and filters read. No craft-level search. Promo News ignores `?s=` | `agent` | `words` | Good for music videos and ads |
| Person only | Instagram Reels, [Vimeo Staff Picks](https://vimeo.com/channels/staffpicks), Dribbble, CodePen, Landing Love, Video Static, Ads of the World, Meta Ad Library, LBB, [TikTok Creative Center](https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en), Shadertoy | 403, JS shell, login, or robots forbid | `person`: links in `links.md`, never fetch | `look` | Taste, for the person. For ads, the real picture of a category is here |
| `appmotion.design` | n/a | 404, though X lists still recommend it | `dead` | n/a | Skip |

## Queries

Single runs, `tested 2026-11-03`, and rankings can move. Refs treats long queries as loose matches, so totals grow with
words: `hard cut on the beat` gave 4,335 and `overshoot` gave 30. A wrong tag fails silently, so check `/tag.json?name=`
on Sakugabooru.

| Source | Bad | Came back | Good | Came back |
|---|---|---|---|---|
| Refs | `cool animation` | 1,827: a CPU water cooler, a Hyundai car | `{"query":"kinetic type","category":"motion","ai_made":false}` | 64: Crazy Raccoon, Apple Business Essentials |
| Refs | `stop motion` | 2,913, on target but wide | `{"query":"stop motion","max_seconds":45,"ai_made":false}` | 1,032: Kevin Parry, Thatchers Cider |
| Sakugabooru | `tags=smear` | 0 | `tags=smears+order:score` | 62,126; top score 5934 |
| LottieFiles | `searchPublicAnimations("kinetic typography")` | 73,697, top items 3-17 downloads | `featuredPublicAnimations` | 3,418 curated |
| Are.na | `anticipation follow through`; `spacing chart` | 0 pages; bicycle channels | `motion reference` | 37 pages; channels of 615, 261 |

Once you have measured, write the spec (`our proposal`):

| Bad note | Good note |
|---|---|
| "cool animation" | "kinetic type, hard cut on the beat, on twos, `back.out(1.2)`, 10-frame entries, 3-frame stagger" |
| "make it smoother" | "t90 at 0.3 of the move, 12-frame settle, no linear" |
| "cinematic camera" | "one tilt down over 2.4 s, gathers speed, lands with a tiny overshoot, then locked" |

## Code vs generated

Code needs frame counts and curves. A model needs one move, one action, a duration and visible beats. No source shows
that models obey "overshoot 1.2", which in code means `back.out(1.2)`, 5.29% past the mark. Keep the prompt physical and
the code numeric. The code entries ran on GSAP 3.15.1 and Remotion 4.0.540, except quantising `frame`, which is a
suggestion. The prompts are `our proposal` and went through no video model.

| Fact from reference | Generation prompt | GSAP | Remotion |
|---|---|---|---|
| 17 frames, 10% overshoot | "The card snaps in, slides a little past its mark, and settles back." | `{duration:17/24, ease:"back.out(1.7)"}` | `spring({frame,fps,config:{stiffness:300,damping:20},durationInFrames:17})` |
| 3-frame stagger | "The five words land one after another, in quick succession." | `stagger:3/24` | `delay: i*3` |
| Drawn on twos | "Stepped, low-frame-rate motion, like hand-drawn animation on twos." | `ease:"steps(n)"` | Quantise `frame` to even numbers |
| Tilt, t50 0.30, 2.4 s, tiny overshoot | "Over 2.4 s the camera slowly gathers speed tilting down, then stops firmly with a slight settle." | `CustomEase.create("t",".199,.005,.389,1.205")` | `Easing.bezier(.199,.005,.389,1.205)` |
| End hold 1 s | "Then hold perfectly still for one second." | Timeline gap, `"+=1"` | Add 30 frames |

Treat any one bezier as a sample and check it against the range. `tested`: `back.out(1.2)` overshoots 5.29%,
`back.out(1.7)` 9.98%, `back.out(2.5)` 18.9%. Remotion `spring` at 30 fps: stiffness 100, damping 10 overshoots 16.3%;
100, 15 gives 2.8%; 200, 20 gives 4.2%; 300, 20 gives 10.7%; 170, 26 gives 0.

For a generated shot, carry one camera move from one shot. Guide-clip rules are third-party and conflict: "Seedance
interprets the clip; it does not copy motion exactly"
([Kapwing](https://www.kapwing.com/resources/how-to-use-seedance-2-0-a-guide-for-ai-video-creators/)). With a depth map
"there's nothing left to interpret but the motion" ([@NexlowX](https://x.com/NexlowX/status/2094494202587398616)).

## AI-motion protections

"Floaty" is measurable, though no peer-reviewed source names it and no threshold is calibrated. `tested 2026-11-03`, small
and biased: `camera` on 12 of our AI clips against 10 Spring shots read median `speed_cv` 0.66 against 1.51, and jitter
0.07 against 1.02 px. That suggests what to compare and proves nothing. The sources below are `reported`, mostly vendor
blogs and practitioner posts. Treat them as hypotheses.

| Artefact | What protects you in the reference | Read with | Fix in prompt | Fix in code |
|---|---|---|---|---|
| Floaty camera: "too stable and too smooth" ([Higgsfield](https://higgsfield.ai/blog/ai-video-look-real-2026)) | A real camera with a reason to move, a landing, slight drift | Jitter, t90, overshoot | One named move that "lands" | `CustomEase` from the read; small noise on position |
| Constant speed: "no instant starts/stops; no hovering" ([Imaginary](https://www.imaginary.app/blog/why-your-ai-video-looks-too-smooth-2026-a-troubleshooting-guide-to-fix-plastic-s)) | A visible ramp up and settle | `speed_cv`, `peak_speed_at` | "gathers speed", "brakes", beats with a stop | Never `none` on spatial moves |
| No weight: "gliding with no weight transfer" (Higgsfield) | Contact, foot plants, stride rhythm; Sakugabooru `running`, `walk_cycle` | Motion sheet, `holds` | "weight shifts from foot to foot" | Fewer, stronger poses; holds on twos |
| Everything fades in: "centered text, gradient background, everything fading in" ([@rexan_wong](https://x.com/rexan_wong/status/2103707054108299437)) | A film with cuts, transforms and scale | Motion sheet, `elements` | n/a | Transforms, not fades: 3,392 transform entries to 584 fades (motionmaxxing) |
| Too smooth | A reference on twos or threes | `holds` | "low frame rate feel" ([@Aducate](https://x.com/Aducate/status/2032543653726445605)) | `steps()` |
| Dead frames: "No run of more than 3 consecutive flat frames" (motionmaxxing, 3-7 s moments) | Continuous motion | `holds --stills` | Beats that fill the shot | Secondary and ambient motion |

## Reject if

- You cannot fill the rows this reference is for, or you saw the clip only as a GIF, since re-encoding changes timing.
- You judged it from stills: "Never judge a reference or your own render from one frame every few seconds"
  ([@finnardley](https://x.com/finnardley/status/2115786060231770351)).
- It is a multi-shot clip offered as the guide for one generated shot.
- A complex camera move and a complex action share the clip ([third-party
  tip](https://dev.to/preecha/how-to-use-reference-video-in-seedance-20-copy-motion-and-camera-moves-4g36)).
- It is tagged AI-made and the goal is a human feel. Filter with `ai_made:false`. For a coded piece use `made_with`: `false`
  removes code-made films, and `true` mixes them with generated ones.
- A number has no domain, such as a UI stagger limit applied to a film.
- `warnings` flags the read and you have not split the window or checked a motion sheet.

Universal rejects: [`never.md`](never.md).

## Judge it

Motion M1 to M6 in [`judge.md`](judge.md), a draft and off by default. `cuts` feeds M1 and M2, and M1 is core only if
cutting is this reference's job. `camera` feeds M3 and M5, M4 goes to the LLM, M6 to the person.
