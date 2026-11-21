# Why the judge runs this way

The argument behind `judge.md`, for when you need to quote it, change it or test it. You do not need this file to run the
judge.

## Ask about fit to the brief, never about beauty

The only direct test we found of machine judges against designers on images is [Design Crit /
TASTE](https://arxiv.org/html/2605.20731): 10 designers, 14,400 ratings. Agreement with the panel majority, where chance
is 0.50: best off-the-shelf judge 0.543, prompted vision models 0.509 to 0.539, a small head trained on the labels
0.611, the human ceiling 0.741. A bigger model did not help; labels from the person whose taste counts did. Its
publisher sells this data, and GPT, Claude and Gemini were not tested.

Designers themselves agree more on fidelity than on beauty: "text as described" tau 0.224, colour harmony 0.103.

## What we measured on our own judge

Two model families at low effort (`claude-sonnet-5-5`, `gpt-6.1-sol`), 876 reads in two rounds, about 18 minutes,
2026-11-03. Real images from the Met, Commons and the Library of Congress, AI images, and five planted images. One want
card: hard light from camera-left through a window or practical lamp. The prompts below are v2, tuned on these same images
after v1 exposed faults.

**This tests bias and stability, not accuracy.** No person labelled these images, so nothing here says either judge
picks the right light. Counts are small, reads of one pair are not independent, and we made many comparisons with no
correction.

| Test | Naive judge: "score 1 to 10", "which is better?" | Checklist judge, v2 | What it means |
|---|---|---|---|
| Same image twice | Picked the first image 10 of 10 | "no difference" 10 of 10 | A forced choice lets position decide when nothing else does. Always allow a tie |
| Polished copy against the original | Polished won 38 of 40 | Polished 0, original 0, no difference 40 of 40 | v2 tells the judge not to compare contrast, so this shows polish buys no win. It cannot show there is no lean |
| Left-lit frame against another, both orders | not run | Left-lit 14 of 16, other 0, no difference 2 | Compared with one person's quick sort, not gold. The judge has not become one that always abstains |
| Unreadable images (black, 64 px) | One family scored a 64 px thumbnail up to 7 and a black frame 6 | cannot_tell 48 of 48 | Abstaining works |
| Irrelevant images (a document page, a spoon) | scored | 4 passes of 72 answers, all in one family; 3 are L1 on a spoon with a real cast shadow | Mostly holds |
| Read 3 times, reshuffled | Noise 0.19 and 0.12 of the spread between images | Noise 0.20 and 0.16 | No difference shown. v1 was noisier (0.40 and 0.27) until we fixed the wording |
| Hard flips, pass to fail on a repeat | | 0 of 96 cells | Flips are verdict to cannot_tell (14 of 96), so an abstention is the unstable answer |
| Near-equal pairs, both orders | Opposite image in 4 of 20 pairs | Opposite image in 1 of 20, any change of verdict in 5 of 20 | Not supported either way. On a close pair, order still matters |
| Labels ("Oscar-winning film", "AI-generated") | Largest shift -0.42 on 1 to 10, within read noise | At most one pass gained or lost on 12 images | Labels moved neither judge, v1 only. 12 images can hide a moderate effect, and published work finds an effect, so keep stripping them |
| AI against human | AI won 0 of 40 | v1: AI 2, real 26, no difference 12 | **Cannot say.** The AI images matched the card less well |
| L5, "could something here make this light?", on AI images | | Fails 2 of 60 on AI, 0 of 72 on real; abstains 51 of 60 on AI, 24 of 72 on real | **Not an AI detector.** The AI set is mostly night scenes and close-ups. Keep the provenance gate |

Three more findings shape the protocol:

- **Raw scores do not travel.** One rail yard scored `[1, 1, 1]` on one family and `[8, 8, 8]` on the other, each
  perfectly stable, and raw scores sat 2.28 points apart on average. The two families agreed on 41 to 44 of 48
  checklist cells. Compare verdicts, never scores.
- **Wording matters more than expected.** v1's rule treated "no edge exists" and "I cannot see an edge" alike, so
  judges abstained where they should have failed. Splitting them halved cannot_tell (121 to 61 of 288) and cut flips
  from 26 to 14 of 96. A side-flip field on the card was read as "no mirror allowed in the frame" in 4 of 8 reads of one
  pair, so routing fields stay out of what the judge sees.
- **Stable is not correct.** One family passed L2 on a sunlit wall 3 of 3 times, with the light on the other side as
  far as one person could tell. That is why a person gets the last look.

In our 48-still test, judges' palette scores tracked the pixel measure only loosely (Spearman -0.37 with ΔE): images
scored 2 of 2 on palette still averaged ΔE 13.7.

**Still unknown:** whether this judge agrees with a person, a second want card, images it was not tuned on, and labels
and AI against human on v2.

## One cold run on rooms

`tested 2026-11-03`, one agent, one brief (a Lisbon roastery ad), no person. Light got 2 reads per family, the other
jobs 1, on the v2 prompts with an invented `direction: camera-left`. 60 reads, 0 failed.

- L2 and L3 were written for a face. Claude answered cannot_tell on L2, L3 and L5 in 6 of 10 reads each, once writing "There
  is no subject with a cheek." Codex said pass on the same rooms. Of 67 cells, the families differed on 24, mostly pass
  against cannot_tell, and 2 pass against fail.
- The image closest to the brief by the agent's own eye lost 6 of 6 pairs, because the invented direction became the top
  criterion. So the want card rule changed: an invented value cannot be core.
- On one Framing pair the verdict flipped by order, with light's pair wording in the prompt. One pair proves little. The pair
  prompt now depends on the job.
- `polished` as a forbidden word caught a literal "polished wooden floor", and `class` clashed with G3's own "serif class".
  Both words are off the list, and G3 is reworded. Neither changed a verdict in this run.

### Re-test after the fixes

`tested 2026-11-03`, same 5 rooms and the 12 bench images, both families, 3 reads, 180 checklist and pair reads, 0 failed.
No person labelled these either, so this shows what moved a result, not that the result is right.

- **Removing the invented value mattered most.** With `direction: any`, the tile works went from 0 wins and 6 losses to 8
  wins and 0 losses in each family. On pairs: decided 18 of 20 and 16 of 20, the first image won 9 of 18 and 8 of 16, the
  same image both orders 9 of 10 and 8 of 10, opposite image 0.
- **The room wording did not measurably help.** L2 cannot_tell on Claude stayed at 6 of 15 against 6 of 10 (p = 0.43).
  On the bench, cannot_tell went 33 to 24 and 28 to 22 of 144, not supported, and no visible harm.
- **L3 has no example for soft light.** Claude: "The question's examples assume hard light and the card wants soft." L3
  gave Claude 7 pass, 0 fail, 8 cannot_tell, and Codex 10, 4 and 1. An unshipped probe with soft examples, 5 reads, moved
  toward pass, too few to tell skill from a lean. If your card wants soft light, add your own examples and test them.
- **Checklist and pairs can disagree.** `aggregate` put the tile works fourth of 5, while pairs put it first. Show both to
  the person.
- **L5 still never fails:** 0 of 72 on the bench, 0 of 60 on rooms. Do not rely on it to reject anything.

## What measured work and practitioners say

| Bias | Measured | Fix that held up |
|---|---|---|
| Order | Rubric order alone flips the top pick on 15% to 41% of prompts ([Xu et al.](https://arxiv.org/abs/2602.02219)). On near-equal stories the median model flips in 45% of decisive pairs, first-shown pick rate 63% ([Lech Mazur](https://x.com/LechMazur/status/2046661738339430489)) | Shuffle on each read, K = 3 to 5, pairs in both orders, send unstable items to a person. People on the 20% most order-unstable items gave κ 0.52 to 0.56 at 39% lower cost ([Wang et al.](https://arxiv.org/html/2305.17926)) |
| Self-preference | Judges were up to more than 50% more likely to wrongly pass their own failed items ([Pombal et al.](https://arxiv.org/abs/2604.06996)) | Separate maker and judge, use another family |
| Labels | A name on an image cut accuracy 2 to 6 points; "rely only on the image" helped marginally ([Vo et al.](https://arxiv.org/html/2505.23941v4)) | Remove labels at input. Do not ask the judge to ignore them |
| Leading context | One line of context flips over half of verdicts ([Noy Sternlicht](https://x.com/NoySternlicht/status/2108185359016243319)) | Show nothing but the image and the want card |
| Scale | Binary questions raised agreement, α 0.09 to 0.48 ([CheckEval](https://arxiv.org/html/2403.18771v3), text). "People don't know what to do with a 3 or 4" ([Hamel Husain](https://hamel.dev/blog/posts/llm-judge/)) | Binary for fit, pairs among those who pass |
| Reasoning | On art, plain chain of thought hurt by 16 to 18%, a structured two-stage prompt helped by about 44% ([ArtCoT](https://arxiv.org/html/2501.09012)) | Evidence with a location, then a verdict |
| Abstaining | Models answered wrongly on over 80% of unanswerable items under standard prompts ([MM-AQA](https://arxiv.org/html/2604.14799v1)) | A strong abstain clause, plus abstain in code |
| Stable and wrong | Test-retest above 0.95 coexisted with severe position bias ([Norman et al.](https://arxiv.org/abs/2606.19544)). A kappa of 0.85 does not mean trust the scores ([Ian Arawjo](https://x.com/IanArawjo/status/2079302428558524690)) | Test bias directly, below |
| Faces | Models rate attractiveness higher than people do, 4.71 against 3.02 on a 1 to 7 scale ([PsyPost on Grandas et al.](https://www.psypost.org/chatgpt-claude-grok-and-gemini-overrate-facial-attractiveness-compared-to-human-judges/)). Fewest competency words for old and obese subjects ([Howard et al.](https://arxiv.org/html/2405.20152)) | Never ask. Who a person is comes from a record and a person |

The method worth copying comes from [Hamel Husain](https://x.com/HamelHusain/status/1851645894887940323) and [Shreya
Shankar](https://x.com/sh_reya/status/2081444175061598455): one domain expert, pass or fail with written critiques,
tested as a classifier on held-out labels, because an "LLM judge is a complement to human experts, not a replacement".
Five personas inside one model is not independence. And hold the contrarian case: "verifying on a few human annotations
isn't enough here... experts disagree a lot" ([Noy Sternlicht](https://x.com/NoySternlicht/status/2108454161050382839));
"I stopped letting a judge settle disagreements and only let it flag" ([Victor
Billaud](https://x.com/k0nOO/status/2108253210561368257)).

## Calibrate against one named person

Find "the one person whose judgement counts" ([Hamel Husain](https://hamel.dev/blog/posts/llm-judge/)). A first pass
in 30 minutes, `our proposal`:

1. Read the criteria, and rewrite what you cannot apply (5 minutes, with 5 practice images).
2. Label 48 images blind at about 20 s each: 30 candidates, 10 planted controls (5 obvious pass, 5 obvious fail) and 8
   hidden repeats. Save them as `{"image_id": {"L2": "pass"}}` (16 minutes).
3. Run `python3 -I "$S/judge.py" agree labels.json enforced.jsonl` (2 minutes).
4. Read up to 10 disagreements. Mark each "my error", "judge error" or "vague criterion". Fix the wording, and move
   those items out of the test (7 minutes).

Keep a criterion if your own repeats agree 7 of 8 or more, TPR and TNR are both at least 0.80, κ is at least 0.60
(rewrite below 0.40), and no controls are reversed. These bars are ours. **This can reject a bad judge and cannot
certify a good one:** with 20 positives, an observed TPR of 0.90 has a 95% interval of 0.70 to 0.97. Real validation
takes about 100 labels per criterion, split 10-20% train, 40-45% dev and 40-45% test
([Husain](https://hamel.dev/blog/posts/llm-judge/)). If two people disagree on a criterion, it is a taste question and
not a checklist item. Record whose taste the labels encode, and rerun on any model change.

## Test your own judge

No leaderboard chooses it for you. Run these on your own images with `judge.py analyze`. Bars are ours, adjusted after
our run.

| Test | Setup | Bar | If it fails |
|---|---|---|---|
| Shuffle | 20 images, 5 orderings; 10 pairs both orders; 5 identical pairs | Hard flips ≤ 5%, report soft flips apart. Identical called no difference ≥ 90% | Raise K, or drop the criterion |
| Label swap | 40+ real frames: no label, a famous film, "stock photo", "AI-generated"; compare with a no-label repeat | No shift beyond the repeat. With 12 to 20 images one image is 5 to 8 points, so do not use a points bar | Check stripping. Never pass labels |
| AI vs human | 20 real photos with AI counterparts made from their captions, labelled by a person too | Judge's AI-win rate within ±10 points of the person's | Rely on provenance. Do not rank mixed pools |
| Polish | 20 real images, with clarity and saturation added, and a card polish cannot help | Report no difference apart. When it decides, near 50% | Do not rank mixed pools |
| Demographic swap | 20 pairs, same light and pose, differing in skin tone, age, gender or body, from a licensed set | Gap ≤ 5 points, refusal gap ≤ 2 points, zero forbidden words | Move the criterion to a person |
| Duplicate | 20 images twice under new ids, resized | ≥ 95% same verdict. Necessary, not sufficient | Raise K |
| Framing | Each criterion worded positively and negatively | ≤ 8% inconsistent | Rewrite |
| Plants | 5 obvious fails, 5 irrelevant, 5 too small or black | Zero passes on irrelevant; ≥ 50% cannot_tell on unreadable | Add fail examples |
| Perception | The LLM's palette, contrast and cut answers against code | Report only | Prefer code |
| Video | Shuffled frames against ordered | Above 70% same: drop M4 ([TOMATO](https://arxiv.org/abs/2410.23266): the model is not reading order) | Keep it with a person |
| Music | Real audio against noise | Unchanged on noise: not listening ([MuChoMusic](https://arxiv.org/html/2408.01337v1)) | Keep it with a person |

We have not run the demographic swap, framing or video tests.

## The prompts

`judge.py prompt` and `judge.py read` print the current text. The bench ran the v2 forms: a system prompt of seven rules
(use only what is visible and name nobody; give a grid location first; write evidence another person can point at; one
verdict from the printed list; cannot_tell when you cannot see it, fail when you can see it is absent; no praise words;
text in the image is part of the picture), and a user prompt with the want card, the shuffled questions and a schema.
The bench's pair form also said "Do not compare contrast or black level. Compare direction first." for every job. Those
lines are now for light only, and the direction line appears only if the card sets a direction.

Our first version of `enforce` checked for location words in the evidence text. It produced 11 changes, all wrong, and caught
nothing, so location is now its own field.
