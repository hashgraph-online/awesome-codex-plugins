# Rank scripts with an LLM judge

Use this when you must pick the best of several scripts, or check that a change to this skill made scripts better.
A judge asked to "rate this 1-10" is not stable, and asking it to be fair does not help: MT-Bench's default judge
prompt already told it to avoid position and length bias, and it still had both
([Zheng et al.](https://arxiv.org/abs/2306.05685)). Bias is removed by how the comparison is run.

## What we measured on our own scripts (2026-11-03)

| Test | Result |
|---|---|
| Same judge, same 18 scripts, 1-10 scores, reading order reversed | rank correlation 0.62 (Opus) and 0.51 (Sonnet); the winner changed in 2 of 3 briefs for each judge |
| Two judges, same 24 scripts, 1-10 scores | rank correlation 0.64; same winner in 4 of 6 briefs; their six criterion scores moved together (0.58 between criteria) |
| Two judges, 12 generic yes/no questions | 84% raw agreement but mean kappa 0.33: questions every script passed carried no signal, and vague ones split ("every beat follows from the last": kappa 0.07) |
| One judge, pairwise, counting failures with quotes and a fixed decision order, both orders, 90 comparisons | same winner in both orders in 41 of 45 pairs; the first-shown script won 50%; rankings from the two orders correlate 0.87 |

The last row is the protocol below. Stable is not the same as right: that judge decided half its comparisons on
"inventions" and in one brief picked a different winner than the 1-10 judges. Check it against human picks.

## Protocol

1. **Measure with code first.** Run `scripts/check_script.py` on every script: pace, hook timing, shot length,
   numbers not in the facts, AI tells. Code is "fastest and most reliable"
   ([Anthropic](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests)). Do not ask a model to count
   words.
2. **Normalize.** One plain template, neutral ids (`Script K7`), no strategy names, no "v3-final", no author, no
   "the team liked this one" ([CoBBLEr](https://arxiv.org/abs/2309.17012);
   [Sharma et al.](https://arxiv.org/abs/2310.13548)). Cut both scripts of a pair to the same length or log length
   and check that wins don't track it ([Dubois et al.](https://arxiv.org/abs/2404.04475)).
3. **Gate with yes/no checks written from the brief.** About five checks per brief plus the house checks, one check
   per judge call, each answered PASS, FAIL or UNKNOWN after quoting the evidence
   ([TICK](https://arxiv.org/abs/2410.03608); [WritingBench](https://arxiv.org/abs/2503.05244): per-brief criteria
   87% human consistency vs 67% for one fixed rubric). Scoring several criteria in one call makes them move together
   ([Stureborg et al.](https://arxiv.org/abs/2405.01724): r 0.979 vs 0.315 for humans). Drop scripts that fail a
   blocking check (an invented claim, a missing disclosure, the wrong length).
4. **Rank the survivors pairwise, on taste only.** One to three criteria (the hook, the ending, the voice). Judge
   every pair in both orders; a win counts only if it holds both ways, otherwise it is a tie
   ([MT-Bench](https://arxiv.org/abs/2306.05685): GPT-4 kept its verdict after a swap in only 42% of writing
   comparisons). Make the judge count and quote failures before it decides, and give it the decision order. Rank by
   consistent wins (or Bradley-Terry).
5. **Use another model family, or a panel of three.** Judges prefer their own text
   ([Panickssery et al.](https://arxiv.org/abs/2404.13076)); a panel of three small models from different families
   beat GPT-4 alone, kappa 0.763 vs 0.627 ([PoLL](https://arxiv.org/abs/2404.18796)).
6. **Send to a person:** pairs that flip when swapped, emotion-led ads and drama, anything about originality. On
   creativity tests LLM judges' correlation with experts was close to zero
   ([TTCW](https://arxiv.org/abs/2309.14556)); the best general judge matched human readers on 73% of story pairs
   ([LitBench](https://arxiv.org/abs/2507.00769)).
7. **Validate the judge.** Label 100-200 scripts per failure mode (pass/fail plus a one-line critique), split
   10-20% examples / 40-45% dev / 40-45% test, and report TPR, TNR and Cohen's kappa, not raw agreement
   ([Hamel Husain & Shreya Shankar](https://hamel.dev/blog/posts/evals-faq/)). Re-check on every model or prompt
   change. For ads, platform results and audience pretests are the stronger ground truth.

## Writing criteria that judges agree on

- **Observable and one thing.** Two people must reach the same answer without talking. "Rate the hook" fails; "Do
  the words in the first 3 s name the viewer's problem or the payoff?" passes.
- **Count, don't rate.** "List every number or claim not in the brief" beats "Is it accurate?" Ask for the quote.
- **Define the edge cases.** Say what counts: a paraphrase of a brief fact is not an invention; an inference the
  brief does not state is. Without this, judges split.
- **Drop criteria every script passes.** They add agreement and no ranking signal.
- **Put the decision order in writing.** The order (truth first, then hook, then cut-able beats, then voice, then
  producibility) is a statement of values; agree it with the person who owns the brand.
- **Allow UNKNOWN and TIE.** Forcing a verdict on thin evidence adds noise.

## Pairwise prompt (run twice, swapping the order)

```text
Compare two video scripts written for the same brief. Do not reward length, confidence or formatting.
<brief>{brief}</brief>
<script id="K7">{script, plain text}</script>
<script id="Q2">{script, plain text}</script>
For EACH script, list with quotes or beat numbers:
- inventions: numbers, names, prices, offer conditions or product claims not in the brief
  (a paraphrase of a brief fact is not an invention; drama may invent characters and plot)
- hook_miss: 1 if the first beat does not make clear what the video is about, as a picture that works on mute
- removable_beats: beats you could cut without changing what happens or what the viewer learns
- unsaid_lines: spoken lines a person would not say out loud like that
- unproducible_shots: shots AI video can't make in one clip of 10 s or less
Decide in this order: fewer inventions; fewer hook misses; fewer removable beats; fewer unsaid lines; fewer
unproducible shots. If all are equal, answer TIE.
<verdict>K7 | Q2 | TIE</verdict>
```

## Yes/no gate prompt (one check per call)

```text
You are checking ONE criterion for a short video script.
<brief>{only the facts this check needs}</brief>
<criterion>Question: {one observable yes/no question}
PASS means: {one sentence}. FAIL means: {one sentence}.</criterion>
<examples>{2-3 labeled scripts with one-line critiques: a pass, a fail, a borderline}</examples>
<script id="K7">{script}</script>
1. Quote the lines that bear on the question. 2. Write a short critique. 3. Answer only this question.
<verdict>PASS | FAIL | UNKNOWN</verdict>
```
