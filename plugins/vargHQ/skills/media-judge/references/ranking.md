# Ranking takes

## Gates first, then counts

`judge.py rank` sorts on: blockers, then major flags, then minor flags, then the reference margin, then reference distance. It
writes why each take beats the next one, and "tied on every fact" when nothing separates them.

Severity lives in `SEVERITY` in `scripts/mj_rank.py`:

- **Blocker:** a viewer sees it and it can't be defended. Decode errors, black, frozen or glitch frames, a failed flash test, spelling, wrong face under `--one-character`, audio drop-outs, a voice that is off script, wrong size.
- **Major:** repairable, costs reach. Stutter, flicker, upload banding, jiggling numbers, too much text, reading time, contrast, safe zone, sound late across the edit, loudness, clipping, template margin.
- **Minor:** a report for eyes. Same size, attention, frame load, motion cause, drift, shake, pinned graphics, label drift, light.

## Why not one number

- People on X say 1-10 scores drift and can be negotiated, and prefer pass or fail. One creator's ten-dimension score was great while the video "looked like a slide deck".
- A still video scores perfectly on temporal consistency. VBench shows consistency trading against motion.
- Picking the best of K on SyncNet alone brought back lip smacking (`sipratt-p/ugc-factory-core`).
- 16 of 16 skills passed basic technical checks in one test, so technical QC does not separate quality on its own. Facts rule takes out; they do not pick the winner.

## When facts tie

`references/llm-judge.md` has the full protocol and our test. In short:

1. **One take per call, observations only.** Use `references/observe-prompt.txt`, 3 runs per take, in a fresh agent, with file names hidden. Then:
   `uv run scripts/judge.py observed --a a1.json a2.json a3.json --b b1.json b2.json b3.json`. A win needs a margin of 2. In our test this gave 90% same verdict on repeat and no opposite winners, with 70% ties.
2. **Still tied? Pairs.** Notes on each take first, then both orders in fresh calls, and a flip stays a tie. Copy the protocol from `m4bwav/artwright`, SeeCut and portia, which each run pairs in both orders. Never ask "which is better?" once and believe it: our judge picked the take shown second 75% of the time, and repeated itself 90% of the time while doing it.
3. **Still tied? It is a tie.** Send it to a person, or ship either.

Why both orders: two judges with test-retest above 0.95 still had position bias above 0.10 ([21 judges, about 541,000 judgments](https://arxiv.org/abs/2606.19544)), and pairs of similar quality are the most biased ([Judging the Judges](https://arxiv.org/abs/2406.07791)). Those studies are on text. Swapping image order reversed up to [60.9% of decisions](https://arxiv.org/abs/2610.01670).

For many takes:

1. Gate on facts first, so only passers go to pairs.
2. Compare by Swiss or Sort-MST pairs rather than every pair ([arXiv 2508.17840](https://arxiv.org/abs/2508.17840)).
3. Fit Bradley-Terry to the wins. Call two takes tied if their ranges overlap. No one has published how many comparisons video judges need, so check stability by refitting on half the pairs.

## Learning weights from people

If you want a weighted model, fit it to people's choices, and refuse it unless it predicts held-out votes. `siewong007/vantage-pipeline` refuses below 0.70 accuracy on held-out votes. Report kappa rather than plain agreement: exact match overstated agreement by 33.8 to 41.2 points in [the 21-judge study](https://arxiv.org/abs/2606.19544).

## Do not get gamed

Keep some checks out of the agent's loop. Look at a sample by hand each round. Add every miss a person finds as a new fixture.
