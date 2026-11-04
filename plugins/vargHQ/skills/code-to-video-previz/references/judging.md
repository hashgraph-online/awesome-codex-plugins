# Rank takes with an LLM judge

Clear criteria are necessary and not enough. "Simply asking an LLM to score the outputs was not reliable enough, even with a very
descriptive evaluation rubric" (Notion). Bias comes in through what the judge is shown, how it's asked, who it is and what it's
allowed to answer, so fix all four, then measure it against people. A judge cuts weak work and short-lists. A person picks the winner.

## The recipe

1. **Compute what you can.** No LLM: `check_staging.py` for framing, blocking, the camera and figures walking through the set; `measure_shot.py` and
   `shots.py` for moves and cuts. Judges can't see between frames, and motion read from frames runs from weak to near chance on most models.
2. **Clean the inputs.** Same layout, size and timestamps for every take. Random file names. No take numbers, labels, captions, scores, overlays, or letterboxing.
   Hide the author, the attempt count and earlier verdicts. Give it the brief, the reference and the frames, nothing else.
3. **State the purpose.** "Better" means nothing alone: a guide clip and a finished film want opposite things.
4. **Gate each take alone** with yes/no questions, evidence first, `cannot_tell` allowed. Any failure stops the take. Never add passes into a score.
5. **Rank what survives in pairs** on specific points, evidence first, both orders, ties allowed. If the two orders disagree, it's a tie. `scripts/judge_pack.py` packs and scores this.
6. **Use a second model family.** Where the two disagree, a person decides. Don't expect a big panel to fix it.
7. **Include controls in every round.** An exact copy must tie. A pretty-but-wrong take must lose. If not, throw out the round. For native video, check that it looked: SeeCut voids a verdict unless the judge can copy on-screen text and state the duration.
8. **Report tiers, not a list.** Close calls are noise. A person picks within the top tier.
9. **Calibrate before you trust it** on your own labels: below.

## What we measured

One brief, a correct prototype and 11 copies with one seeded defect each, so the right answer was known. Sonnet 5.5, 360 fresh-context blind calls, plus 42 through Codex.
It isn't a human comparison and it doesn't test taste. The defects are ones we seeded, on one scene.

| test | result | what fixed it |
|---|---|---|
| Two identical images, forced choice | first image 12 of 12 (Codex 4 of 6), "picking A by default" | allow a tie: 12 of 12 ties |
| "Made by a senior previs supervisor" on one of two identical images | labelled one 12 of 12 (Codex 6 of 6). "Your own earlier work": 8 of 12 | hide it. Telling the judge to ignore it still gave 4 of 6. With a tie allowed: 0 of 12 |
| Lit render with a person missing, vs a correct grey one, "which is better?" | lit 6 of 6 (Codex 4 of 6) | evidence lock: 0 of 6. Stating the purpose: 1 of 6. Greyscale inputs: still 6 of 6 |
| A 1 to 10 score, alone | averages from 3.7 to 6.3, and 4 of 10 defects scored no lower than the correct one. A missing person got 6.3 vs 6.0 | don't use it |
| The rubric as a gate: any failure stops the take | 57 of 58 defect runs failed something, 7 of 8 correct runs failed nothing | keep, and read the evidence on a failure |
| She walks through the desk between sampled frames | the sheet is the same, so no judge can see it | `check_staging.py` catches it |
| Four real prototypes, "better as a guide clip?" with no criteria | the pretty lit film beat all three | evidence lock with specific points: it came last (0.25 of 3 wins), and the two clean blockouts led (2.5 of 3). With vague points it still won everything |
| A question written against our own test set | "head visibly higher" failed all three grey real runs | reworded after seeing real outputs: this is criteria drift |

On four real prototypes, as a guide clip, same model and purpose, wins out of 3 for the pretty lit film / the two clean blockouts: no criteria 3.0 / 1.25 and 1.75; evidence lock with vague points like "fit for the purpose" 3.0 / 1.5 and 1.5; evidence lock with specific points 0.25 / 2.5 and 2.5. **Comparing point by point isn't enough. The points have to be specific and name what the purpose rules out.**

## What a judge can't see

| defect | judge reading frames | use instead |
|---|---|---|
| parts passing through each other | a mug inside a body on 373 of 420 frames passed every sheet ([m4lkxx](https://x.com/m4lkxx/status/2116504147465757161)) | geometry on every frame: `check_staging.py` for figures against boxes |
| motion, speed, direction | below | solved camera, tracked path, your eyes |
| things popping, morphing or lagging | Spearman with people: GPT-4o 0.176, Gemini 1.5 Pro -0.172, trained model 0.803 ([2406.15252](https://arxiv.org/abs/2406.15252)) | a scorer trained on video, or a person |
| cuts, pacing | counting cuts, % right on a 4-option question (chance 25): GPT-4o 34.5, Gemini 1.5 Pro 58.6, people 87.5 ([2411.10979](https://arxiv.org/abs/2411.10979)) | a shot detector (`shots.py`). Pacing is yours |
| text | vision models can rewrite wrong text into plausible text, tested on documents, up to 10% of short words ([2607.21617](https://arxiv.org/abs/2607.21617)) | OCR and a diff |
| counting | fine on our stand-ins; 17.05% on altered familiar subjects, adversarial set ([2505.23941](https://arxiv.org/abs/2505.23941)) | scene data or a detector |
| which of two close takes is better | "more real?": Gemini 3.1 Pro 48.6%, human experts 86.4% ([2605.18984](https://arxiv.org/abs/2605.18984)) | a person |

Some of these are older models; we found no run of these defect tests on Opus 5.5, GPT-6 or Gemini 4. Native video isn't a clear escape: counting synthetic bounces, one model scored 19.6% with native video, 29.3% at 4 fps and 68.6% with oracle keyframes around each true bounce, but on state changes those keyframes dropped it from 36.8% to 6.3% ([2608.06361](https://arxiv.org/abs/2608.06361)). So have code find the moment, and test whether showing those frames helps. Check any defect a judge names at the frame it names: judges invent them.

**We found no test of an LLM's pick against a director's pick on generated takes.** Takes of one shot, which differ only in performance, are the hard case: judges agree with people 5 to 13 points less on same-model pairs ([2512.16899](https://arxiv.org/abs/2512.16899)). Before you trust it there, run 20 shots with 4 takes each against a director's picks and the director's own re-pick a week later.

## Writing criteria

- **Label real outputs first, then write the criteria.** "It's often better to wait until you've reviewed some examples before developing a detailed rubric" (Hamel Husain). Our own question failed this.
- **One observable thing per question.** Say what to look at and what fails it. "Is it good?" fails, and so does "fit for the purpose". A frame number and a cause is a task; a mood isn't.
- **Name what the purpose rules out.** This is what moved our ranking. A judge won't mark down a beautiful render unless a point tells it to: "flat light with no drama, because the video model must not copy it".
- **Say what to ignore:** polish, colour, lighting, detail, unless the question asks.
- **Allow `cannot_tell` and allow passing.** A judge told to find defects invents them when the real ones run out.
- **Questions that should answer "no".** Generated yes/no question sets answer yes 96.6 to 100% of the time, so a judge that says yes to everything looks good. Add some where no is right. (We haven't tested this.)
- **Check wording for steering.** "the best designs are museum quality" pushed Anthropic's designs into one look.
- **Vary the order of criteria:** later ones drift towards earlier scores.
- **Keep a human reading outside the rubric.** "Reviewers can become so focused on checking each item that they overlook problems outside the rubric."

## Gate prompt

Run one take per fresh context. Adapt the questions to your brief after looking at real outputs.

```text
BRIEF: <the brief>
PURPOSE: <a guide clip: an AI video model copies only its camera, positions and timing, then redraws everything>
The contact sheet's rows are shots in film order, its columns are the first, middle and last frame. Cells are written R2C3 for row 2, column 3.

Answer each question using only what you can see. Write the evidence first: which cells you looked at and what's in them. Then give a verdict: pass, fail or cannot_tell. Use cannot_tell whenever the frames don't settle it. Never guess.
Don't reward or punish polish, colour, lighting or detail unless a question asks about it.

people: <who must be in which cells>. Fail if anyone is missing, or anyone extra appears.
order: <what each row must show>. Fail if the rows are out of this order.
in_frame: In every cell where a person should be seen, their whole head is inside the frame.
not_blocked: Nothing covers a person's head in any cell.
action: <a rule from the brief you can see in frames, like "the man's nose mark points at the camera in every cell">
coverage: The rows use clearly different shot sizes.
separation: Each person stands out in brightness from whatever is directly behind them.
clean: No readable text, numbers, labels or captions anywhere.
change: <what must differ between the first and last column in a shot, written loosely enough to allow different ways of showing it>
neutral: Flat-lit: no dramatic light pools, hard cast shadows or saturated colour. (Guide clips only.)

Reply with only JSON: {"people":{"evidence":"...","verdict":"pass"}, ...}
```

Any `fail` stops the take: read the evidence first, since a failure can follow from another one. `cannot_tell` means a person or a measurement looks.

## Pair prompt

`judge_pack.py` writes these, with a random criteria order per call. Run every job in a fresh context.

```text
BRIEF: <the brief>
PURPOSE: <the purpose>
Two pictures, A and B. Look at both before you decide.

Compare them on these points, one at a time: <criteria>.
For each point, write what you see in A and what you see in B, and cite where. Don't reward polish, colour, lighting or detail unless a point asks about it.
Only then decide which serves the purpose better. If neither does, say tie: ties are a normal answer.
Reply with only JSON: {"notes":{"point":"..."},"winner":"A"} where winner is A, B or tie.
```

```bash
python3 scripts/judge_pack.py pack take1.jpg take2.jpg take3.jpg --brief brief.txt --purpose "A guide clip for a video model" --out round1/ \
  --criteria "the woman is at the window in the last shot; nothing covers a head; the man never turns around; flat light with no drama, because the video model must not copy it"
# run each job in round1/jobs.json in a fresh context, save {"id":..., "winner":"A", "judge":"sonnet"} per line
python3 scripts/judge_pack.py score round1/ replies.jsonl
```

## Questions by purpose

We tested only the guide clip set.

| judging | ask about | don't ask about |
|---|---|---|
| guide clip | who's in frame, order, framing, facing, coverage, brightness, no text, flat light | look, texture |
| reference match | overlay on several frames: do masses, horizon and light direction line up? Numbers from a camera solve | polish, whether it's "like" the reference overall |
| generated take vs its previz | same people and count, same screen positions, stand-in shapes gone, no text. Cuts and camera by code | motion quality from frames: play it |
| finished film, code-rendered | beats, contact points, reference match, the look against named references | "cinematic" |

## Calibrate

- **Labels:** about 100 per failure mode, with enough passes and fails to measure both. "Below 60 examples, the confidence intervals are often" too wide (Hamel Husain). About 100 to 150 pairs for ranking, by at least 2 people. One named person owns the taste.
- **Measure** true positive and true negative rates on held-out labels, kappa rather than raw agreement (raw overstates it by 33 to 41 points), and signed error: kappa under-reports a constant bias.
- **Re-audit after any model change.** One upgrade collapsed 93% of scores onto a single value. An anchor set of about 200 calls finds it.
- **Expect little on taste:** 0.55 to 0.66 against a designer majority where a judge is order-consistent, with one designer agreeing at about 0.74. It's triage.

## What the research measured

| finding | number | source |
|---|---|---|
| Verdict flips when two answers swap | 46.3% in the paper, 62.5% in a reproduction on similar models | [Zou group](https://zou-group.github.io/llm-claims-shelf-life/) |
| Counting only order-agreeing wins, aesthetic judging | 64.48% to 86.70%, experts 85.00%. Fewer pairs get decided, and on all pairs open models stayed at 0.51 to 0.54 ([2605.20731](https://arxiv.org/abs/2605.20731)) | [2406.09397](https://arxiv.org/abs/2406.09397) |
| Comparison vs rubric, recovering the intended quality order | attorneys rho 0.908 vs 0.150, GPT-5.4 0.421 vs -0.250 (vendor co-authors, text) | [2605.25240](https://arxiv.org/abs/2605.25240) |
| Atomic questions vs an embedding | 0.60 vs 0.33 against human ratings | [2310.18235](https://arxiv.org/abs/2310.18235) |
| Numbers written on an image | shift ratings about 2.5 times more than blur and JPEG damage on average (2.09 vs 0.85). Extreme blur alone moved them about as much | [2605.11218](https://arxiv.org/abs/2605.11218) |
| Irrelevant edits | black padding +10.4%, brightness +5.9% (GPT-4.1-mini, worst setting of each). Defining the bias cut them to +5.6% and +0.8%, but didn't remove them | [2505.15249](https://arxiv.org/abs/2505.15249) |
| Prior scores in the prompt | d up to 0.71 over 192,000 attempted evaluations. A separate test with human labels: blocked 48% of corrections (GPT-4.1). A warning didn't reduce the score shift on the one task tested, though it removed the accuracy loss on labelled data | [2608.25869](https://arxiv.org/abs/2608.25869) |
| Self-recognition with no labels | GPT-4 73.5% accurate at telling its own summaries from others'. On text a fresh copy may not be independent | [2404.13076](https://arxiv.org/abs/2404.13076) |
| Self-preference, blind writing judgments | Sol +7.7, Opus 5.5 +3.4, GLM +1.8 of 100 (vendor). We found no test of a model judging images it made | [ToneBench](https://benchmark.towardsai.com/judges.html) |
| Panels, on text inference tasks | 9 judges behave like 2.0 to 2.5 votes; the best single judge matches or beats them | [2605.29800](https://arxiv.org/abs/2605.29800) |
| Motion from frames | Gemini 3.1 Pro 60.0%, GPT-5.6 Luna 15.0%, open models at most 11.7%, chance 6.25%, humans 91.3%. More frames didn't close the gap | [2609.09528](https://arxiv.org/abs/2609.09528) |
| Blender renders, "closest to the goal" | Claude 3.5 Sonnet 0.66, between people 0.79 | [2504.01786](https://arxiv.org/abs/2504.01786) |

Most 2026 papers here are unreplicated preprints. Much of it was measured on text. We found no study of judging a previz or a guide clip apart from our small test.
