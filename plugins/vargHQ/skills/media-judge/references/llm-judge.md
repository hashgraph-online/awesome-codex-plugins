# LLM as a judge: ranking without the bias

**Clear criteria are necessary, not sufficient.** They fix vagueness and disagreement between judges. They do not fix order, labels or what a model can't see. Bias falls through structure: measure with code, blind, one take per call, let code decide, calibrate on people, audit.

The form of the criterion matters more than its clarity. Ask a model for **what it sees**, not for a verdict, and let code turn that into pass or fail.

## What we measured

Sonnet 5.5, one fresh call per judgment, on 12-frame sheets. 476 judgments on 2026-11-03. Small samples and one model, so read these as a direction. Raw data is in vargHQ/aeo `research/2026-11-03-media-judge/judge_exp`.

**Close pairs of real work.** 10 pairs from launch films and ads, with no right answer, which is where bias shows.

| How the judge is asked | Picked the take shown second | Order flipped the verdict | Same verdict on repeat | Winner followed a planted prestige label |
|---|---|---|---|---|
| "Which is better?", must choose | **75%** (30 of 40) | 10 of 20 | 18 of 20 | 3 of 10 |
| "Which is better?", tie allowed | 67% (26 of 39 decided) | 8 of 20 | 16 of 20 | not run |
| 11 pass/fail criteria, both takes in one call, count the fails | 42% (10 of 24 decided) | 10 of 20 | **7 of 20** | **0 of 10** |

The vague judge is stable and biased, which is the worst combination because it looks reliable. Criteria removed the position bias and the prestige effect, and then the verdict turned noisy.

**One take per call,** so order can't matter at all:

| How the take is judged | Same pair verdict on repeat | Opposite winners on repeat | Ties |
|---|---|---|---|
| Pass or fail on each criterion, count | 47% (28 of 60) | 5 | 53% |
| The model reports what it sees, code decides | 67% (40 of 60) | 3 | 23% |
| The same, and a win needs a margin of 2 | **90%** (54 of 60) | **0** | 70% |

**Seeded pairs,** where one take has a planted defect, so the right answer is known:

| Method | Visible defects: right, tie, wrong | Hidden defects: right, tie, wrong |
|---|---|---|
| "Which is better?" | 20, 0, 4 | 0, 16, 0 |
| Pass or fail, both in one call, count | 11, 11, 2 | 0, 16, 0 |
| Observations, code decides | 10, 2, 0 | 3, 4, 1 |
| Observations, margin of 2 | 6, 6, 0 | 0, 8, 0 |
| Measured facts from `judge.py`, no model | 6, 0, 0 (one run per pair) | 4, 0, 0 (one run per pair) |

The checks were tuned on these planted defects, so the last row is an optimistic bound. Its point is that hidden faults need code at all: the model answered tie on all 16 hidden runs, which is honest, and it can't do better from stills.

What surprised us:

- **The vague judge picked the swapped face 4 of 4 times,** and praised its "full narrative arc". It rewarded novelty. Eyes missed the swap under every wording, while SFace caught it. Identity belongs to code.
- **The same fact, asked differently, repeats differently.** "No frame holds more than 18 words: pass or fail" repeated 69% of the time. "How many words are in the fullest frame?" with code applying the limit repeated 100%.
- **Prestige labels did nothing on easy pairs** (1 wrong of 6, the same as with no label). Bias lives in close calls, which are the ones you most want a judge for.

**Probes,** to check the judge really looks. An all-black sheet got all 12 frames marked broken, 2 of 2 runs. Black against a real take: the real take won 4 of 4, in both orders. Two identical takes, forced to choose: it picked one and said so, "A is an arbitrary pick", 2 of 2. With a tie allowed: tie, 2 of 2.

**A second test agrees.** A separate varg test on seeded 3D previews, with Sonnet 5.5 and Codex, found the same thing from another angle: on two identical images, "made by a senior previs supervisor" won 12 of 12, and forced choice picked the first image 12 of 12, with 12 of 12 ties once a tie was allowed. See `code-to-video-previz/references/judging.md`.

## The protocol

Marked **[M]** where a measurement backs it, **[D]** where it is our design. Almost nothing here has been tested as a whole on video.

1. **Sort every question by who can answer it.** Code measures what it can. Eyes answer yes or no on measured moments. Taste goes to pairs. Nothing gets 1-10. [D, with M on the weakness: Omni-Judge video quality tau 0.020, TempGlitch 49 to 54.1%]
2. **Gates by code first.** A take that fails a gate is listed with the failing fact, and is not ranked. `rejected` means a defect was measured, `review` means nobody could check. [D]
3. **Compare like with like.** Same brief, length window, size, frame rate, encode and loudness. Visual tweaks shift scores: padding +10.4%, brightness +5.9% on images. [M on images]
4. **Blind.** Neutral names. No file name, generator, date, author or votes. Labels shift AI evaluators +34.3 points on text, and judges admit the cue 0% of the time, so telling them to ignore it can't work. [M on text]
5. **Never let the maker judge.** GPT-4 preferred its own output 0.705 and 0.912 of the time, and models rate AI images above sketches. [M]
6. **One take per call, observations only.** Use `references/observe-prompt.txt`. Run it 3 times and keep what most runs report. Then let code decide: `judge.py observed --a a1.json a2.json a3.json --b b1.json b2.json b3.json`. Instructions barely help order bias ("ignore order" 0.99x, chain of thought 0.92x), so remove the order instead of asking. [M here; order numbers on text]
7. **A win needs a margin of 2. Otherwise it is a tie.** A tie is an honest answer, not a failure. Don't force one. Forced choice manufactures winners. [M here, small sample]
8. **Check the evidence with code.** A frame number must exist, and a quote must appear in the OCR. An invalid reply is no verdict. [D, from ABCD and SeeCut]
9. **Ties go to pairs.** Notes on each take alone first (notes before comparing gave +24.48% on adversarial text), then both orders in fresh calls. If the answer flips, it stays a tie. Never show 3 or more at once. `code-to-video-previz/scripts/judge_pack.py` packs and scores a blind round, with random names and a copy that must tie. Three different orders capture about 70% of the gain, and repeating one order only 8%. [M on text and images]
10. **For many takes,** fit Bradley-Terry to the pairs. Use a round robin up to 12 takes, then Swiss or Sort-MST. Report groups, not a list. [M on text; count unknown on video]
11. **A second model family on the top group.** Report where they disagree. No debate: it amplified bias on text, 0.82 to 0.71. [M on text]
12. **Calibrate on people.** Fine-tuned or human-calibrated judges beat stock models on video: VideoScore 77.1 against GPT-4o 23.0, and RoboJudge 0.719 against 0.401. Your own labelled exemplars cut the order gap on images from over 30 points to about 9 or 10, where self-written rubrics only took off 3 to 5. Keep them out of the test set. [M, partly one preprint]
13. **Audit it.** Run identical pairs, fake labels, swaps and brightness changes, and compare the shift against the same pair re-run. Feed it black frames, one frame repeated, and text with no picture: any question it still answers the same way should be dropped (@yoshispeninsula). "Removing the images barely changes the score" is the trap (@HamelHusain). Re-run on any model or prompt change, because one team saw the same summaries pass 34%, 48% and 38% across three versions of one model. Report true positive and true negative rates and kappa, because plain agreement overstated it by 33.8 to 41.2 points. A practitioner figure is 100 to 200 labels per failure mode. [M; thresholds need re-deriving on video]
14. **Keep some checks hidden** from any automatic loop. Best-of-K on one number gets gamed. [M]

## How to write a criterion

Each criterion has: an id, the failure it tests, who decides it, the question, the pass line, its input, the evidence required, when to answer unknown, what it is not, and how it was validated.

Rules:

- **One fact.** If the question has "and" in it, make two.
- **Visible to this judge.** A still can't show jiggle or sync. Send those to code.
- **A stranger could apply it.** No "premium", "cinematic" or "feels".
- **Ask for the observation, not the verdict.** "Quote the misspelled words", not "is the spelling good".
- **Unknown is allowed.** A judge with no way out invents an answer.
- **It returns a place,** a frame number or a quote.
- **No scale.** Changing score labels alone flipped 15.6 to 51.9% of verdicts on text.

| Bad | Why | Good |
|---|---|---|
| Rate the visual hierarchy and how well it leads the eye, 1 to 10 | Two ideas, taste, a scale, no place | Which frames hold 3+ elements where none is clearly larger? List the frames |
| Do the numbers jiggle and do sounds land on cuts? | Two facts a still can't show | Code: shake of a held digit in % of its height, offset per cut in ms |
| Does this look cheap and AI-template instead of premium? | Loaded words, no pass line | Code: margin to template. Eyes: name three things only this brief could produce |
| Is the label correct? | No target, no place | Name the object this label points at, or unknown. Code measures the drift |
| Is the text spelled right? | Invites a yes | Copy this crop exactly. Do not correct. If unreadable, write unknown |

Criteria have their own traps. Their order changes the result: reordering a rubric flipped the top candidate on 15 to 41% of prompts on text, which is one more reason to use one take per call and randomize the order. Criteria also drift once you see real outputs, so expect to rewrite them, and reviewers overlook problems outside the rubric, so keep one open question: "Describe anything unusual."

## What X says

From 3,523 posts, 362 of them on topic (read 2026-11-03; paper figures here are as the posts report them, not checked):

- **The usual failure is the wrong criterion, not a vague one.** In RIFT, on 147 tasks, 50% had missing criteria and 48% misaligned ones, and only 10% had vague wording ([Snorkel](https://x.com/SnorkelAI/status/2117363300090396713), a vendor). Do error analysis on real outputs first ([Hamel Husain](https://x.com/HamelHusain/status/2112588257104216294)).
- **Rubrics don't stop self-preference.** On machine-checked rubrics, a judge passed 38% of its own failed tests against 1.9% for other models, and rubrics were roughly level with direct scoring ([Sword](https://x.com/SwordHQ/status/2102792080808354251)). A five-family vote cut that ratio from 20.15 to 4.18. This post has 2 saves and may be the most useful one we read.
- **Rewording moves judges.** The same meaning in a new prompt: kappa 0.24 for an LLM judge, against 0.80 for people, and taking the plurality over paraphrases raised human correlation from 0.47 to 0.63 ([paper via a small account](https://x.com/randhir302/status/2116076367418941584)).
- **Pairwise is contested.** List posts call it "more reliable than 1-10 scores" with no data. Sword measured pairs as more biased on self-preference. Video ranking still uses pairs, because taste has no pass or fail.
- **Following the brief is a floor, not a ranker.** "Following the brief is nearly solved... The real separator is visual taste: Composition, Temporal rhythm, and Craft" ([Kaggle on Code2Video](https://x.com/kaggle/status/2102109200427942058)).
- **Public LLM judges for video exist, unvalidated.** [Code2Video-AA](https://x.com/ArtificialAnlys/status/2114845067026571365) runs Gemini at 8 fps with 35,000+ verdicts, five axes and Bradley-Terry per axis. We saw no check against people, and the judge also ranks 6th on its own board.
- **Rubrics get hacked.** Checklist coverage goes up while broader quality falls ([Scale](https://x.com/ScaleAILabs/status/2057934166621299180)). If agreement stays low, simplify, split or remove the criterion ([Cameron Wolfe](https://x.com/cwolferesearch/status/2112936086389309449)).
- **People want a way out for the judge.** "If there are no blocking defects, return PASS. Do not invent issues" ([@DanielChibuihe](https://x.com/DanielChibuihe/status/2117186879493668887)). And describe first, assess second ([@abhishekunique7](https://x.com/abhishekunique7/status/2117678423527014440)).

Best real wording found: "all text inside a 120px safe margin; text contrast at least 4.5:1; no dead time over 0.3s; colors match palette within a delta E of 3; brand name visible on the last frame" ([@Mahaximus_](https://x.com/Mahaximus_/status/2108604553046130750)). And: "'Is the subject in frame?' has a defensible answer. 'Does this look good?' doesn't" ([@MarcusSpillane](https://x.com/MarcusSpillane/status/2057435693882683487)).

## Taste

Models are weak here and it is fine to say so. On aesthetics, the best model scored 26.5% against experts at 68.9% on images, and no system passed 0.55 agreement with designers. GPT-5.4 rated motion at SRCC 0.37 where people reached 0.73. Designers themselves agree less on colour harmony than on typography. So taste goes to a person, or to pairs against your own references, and an LLM's opinion on it stays under Hints.

## Not known

Nobody on X reports a flip rate, agreement with people or planted-defect recall for an LLM judge on AI video. No study we found measures order, label or self-preference bias for pairs of videos, or how many comparisons video judges need. No study of LLMs ranking songs turned up. Most numbers above come from text and images, so treat their use on video as an extension.
