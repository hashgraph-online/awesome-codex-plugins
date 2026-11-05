# What is measured, and what is only our proposal

Read this before you quote this skill. All our own tests ran on 2026-11-03.

## Measured elsewhere

| Claim | Source | Strength and limit |
|---|---|---|
| Vision models read lighting condition at a mean of 41.6%, lighting type 57.5%, shot size 53.3%, lens 37.7%, camera movement 37.4% | [ShotBench](https://arxiv.org/html/2506.21356), 24 models, June 2025 | Older models. No 2026 frontier rerun found |
| No off-the-shelf judge passed 0.55 agreement with a 5-designer majority, against a human ceiling of 0.741 and chance 0.50 | [Design Crit / TASTE](https://arxiv.org/html/2605.20731) | The only direct test found. GPT, Claude and Gemini were not tested. Its publisher sells this data |
| Designers agree more on fidelity than on beauty: text as described tau 0.224, colour harmony 0.103 | same | People, not models |
| Scores fell as the reference count rose: 7.817 with one, 4.891 with two, 4.453 over 3 to 8 | [MultiBanana](https://arxiv.org/html/2511.22989) | Older models. No count benchmark for Kling 4, Seedance 2.5 or Nano Banana 2.1 |
| Vision-language models score about chance on negation | [NegBench](https://arxiv.org/abs/2501.09425) | Retrieval and tasks, not creative search |
| 41.5% of failed negated statements rendered what the prompt forbade | [NegT2IBench](https://arxiv.org/abs/2610.03084), 11 text-to-image models | Images. No comparison for Seedance 2.5, Kling 4 or Veo 3.1 |
| People score 76% on AI images, 52.6% on 2026 5-second fakes | [Kamali et al.](https://arxiv.org/html/2502.11989), [DF26](https://arxiv.org/abs/2609.07369) | Different media and years |
| Rubric order alone flips the top pick on 15% to 41% of prompts | [Xu et al.](https://arxiv.org/abs/2602.02219) | Text judges |
| Binary questions raised judge agreement, α 0.09 to 0.48 | [CheckEval](https://arxiv.org/html/2403.18771v3) | Text. Gains against people are smaller |

## Measured by us, small

**The 48-still test** (Nano Banana 2.1 and Seedream 5 Pro, 3 scenes, 2 models, data in a private repo). Removing the
light line lost the most film-likeness, +0.50 (p = 0.04), but only 6 pairs and 7 tests stand behind it, and no p-value
survives Holm correction, so it is only suggestive. Agreement between the two judges: κ = 0.66 over six lines, **κ =
0.46 on light, the lowest**, and r = 0.71 on film-likeness with 16.7% exact agreement. An earlier figure of r = 0.96
pooled different scales and should not be quoted. Both judges came from one vendor, and no person scored the stills.

**The judge bench**: see `judge-evidence.md`. It tests bias and stability, not whether a judge picks the right light.

**Search tests.** Every "tested 2026-11-03" line in these files was run that day, and results change. Counts are what
came back, not a measure of quality.

**Tools.** `frame_light.py` and `hdri_light.py` reproduced earlier numbers on the same files. `motion_read.py` was
checked on rendered clips with known motion and one CC BY film. Real footage has no ground truth. `ai_marker.py` found
markers on 15 of 15 of our generated stills, and five re-encode methods erased them.

## Two cold runs

### On an ad

`tested 2026-11-03, one cold run`. One agent ran the skill end to end on one brief: a 20 s Instagram Reels ad for a
small Lisbon roastery, generated plates, a coded end card, a voiceover. No person answered questions, picked from the
board or judged the result. So it shows whether the method can be followed and what it finds. It does not show that the
references are good.

What it found:

- **Routes.** The best route was a Commons category walk, with author, date, EXIF and licence in one call. The best single
  find was LoC HABS/HAER `interior tile`: a real tile works in dark rooms, public and with no people. Met worked by named
  artist only. Light words matched captions, not light.
- **Queries.** Light took 26 queries against a floor of 6, 5 of them silent zeros, and Location 24 plus 7 walks against 3.
  One word pair changed the result.
- **Fusion.** Of 119 kept items, 6 were found by more than one query, and a per-maker cut dropped the candidate that then
  passed every check.
- **The obvious search.** 17 of 48 Refs cards were about coffee, and 9 of those were Nespresso. None of 15 thumbnails
  showed a pour. 89 of 89 cards said `locked: library`.
- **The judge.** 60 reads, 0 failed, 46 of them in 1 min 47 s. On rooms with no face one family answered
  cannot_tell on L2, L3 and L5 in 6 of 10 reads each and the other said pass. Families differed on 24 of 67 cells. The image
  closest to the brief by the agent's eye lost 6 of 6 pairs. Details: `judge-evidence.md`.

**The method's weakest spots, on this one run:**

- **The judge on rooms.** It was built for faces, and an invented direction decided its ranking. We changed the wording
  and the want card rule afterwards.
- **The Refs route for ads.** No clip, locked cards, and big brands in 16:9 (16 of the 17 coffee cards). The real picture
  of a small roastery's ads is in Meta Ad Library, which is person-only.
- **Finding what a person loves.** The inside of an old Portuguese tile shop, the brief's stated love, did not turn up.
  A person must find it.

### On a coded film

`tested 2026-11-03`, 35 minutes, no person. A 45 s 16:9 launch film for an invoicing app, in HyperFrames, with one
generated still. Type, motion and palette were run first. It found 48 poster sheets in one Commons category, exact fonts
with a licence, hex with shares on flat sheets, and a few timing primitives from Commons clips. It did not find a
code-made launch film it may measure, or any whole-film structure, so `DESIGN.md` is part measured and part assumed and
nothing was rendered to test it. 24 judge reads cut nobody. No person has picked from this board either.

## Our proposals, not validated

These are how we chose to assemble the evidence. None was tested as a whole against a person:

- the query floors per job, the stop rule, the five slots and the 11-field brief
- the feeling table and the feeling-to-light table (some cells are measured, marked M)
- the identity card and its five tests, including the three-person rule
- the provenance labels and the date cutoffs (2022-01-01 strict, 2022-11-30 loose)
- 7 to 12 never entries and 3 to 6 negative images
- the feed, words and look tags (legal notes are research, not advice)
- the judge's criteria, bars and funnel
- the visual-to-music mappings

## What nobody has tested

- No published end-to-end test of any brief-to-reference method exists. This one has had two cold runs, and no person has
  judged the result.
- Nothing shows that a reference, role line or light sentence changes a final video in this method, or that
  non-obvious references beat top-of-search ones. No generation or render was run for this skill.
- Whether frontier vision judges can read light. Whether they prefer polished or AI images in a quality judgement.
- Whether a public-domain painting gives its light to a generator without its paint texture.
- Motion prompts were not run through a video model. No shortlisted track was heard.
- FrameThrower, Unsplash, Pexels, YouTube, Are.na v3, Flickr's API, Mapillary and Epidemic Sound were not queried with
  an account, so their result quality is unknown. FrameThrower's is the largest gap for light.
- Chinese short-drama vocabulary needs a native reviewer.
- A look's half-life has no measured figure. We found no critic or study calling Blade Runner a default AI look,
  though the skill's advice to look past the first famous name stands as craft.

## The test to run next

Have one person pick from the cold run's board, and label 48 light candidates in 30 minutes (`judge-evidence.md`). Then
repeat the 48-still study with this method against one-query search, with real film frames as controls and a person as the
anchor. That turns most of the proposals above into numbers.
