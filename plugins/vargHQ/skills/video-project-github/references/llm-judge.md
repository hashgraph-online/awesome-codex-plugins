# Ranking quality with an LLM judge

For ranking takes, cuts and agent deliverables. Scripts have their own version: `video-script/references/judge.md`.

**The short version.** Write clear criteria and let the judge say tie. Together they work far better than either alone. Facts go to scripts, taste goes to a person, and the LLM filters and finds defects.

## What we measured

| How you ask | Same answer, Sonnet | Same answer, Haiku |
|---|---|---|
| Asked plainly: which is better? | 59% | 55% |
| Plainly, with a tie allowed | 60% | 46% |
| With written criteria | 68% | 70% |
| Plainly, plus "ignore who made it and what it claims" | 75% | 80% |
| **Written criteria, with a tie allowed** | 90% | 82% |
| **Full protocol:** criteria, evidence only, ignore line, tie allowed, quote the deciding words | 97% | 87% |

Same answer means the winner did not change when we swapped the order, added an author label, said "you made this", padded a reply with empty reassurance, or added a false claim that all checks passed. Near-tied pairs, 120 answers per cell, Claude Sonnet and Haiku, deliverables from our GitHub benchmark.

Written criteria alone helped a little. An allowed tie alone did nothing: given only the option, judges used it in 2 to 5 of 120 answers. Together they jumped, because the criteria tell a judge what "the same" means. The ignore line did better than published tests led us to expect, mostly against the padding and false claims it names, and it adds 5 to 7 points on top of criteria and a tie. The full protocol answered "tie" in 92 to 94 of 120 close calls instead of inventing a winner.

On 9 clearly different pairs, the full protocol picked the better deliverable 72 of 72 times, with and without a false claim on the worse one. So it still separates good from bad.

Asked plainly, one sentence with no facts in it decided a tied comparison: the side with empty reassurance won 16-25% of the time, and the side with a false claim 4-25%, where a fair judge lands on 50%.

Limits: text deliverables rather than video, 12 near-tied pairs, one fixture, two judges from one family. Stable is not the same as right.

## What a judge can and cannot see

Claude and GPT usually get stills. Gemini samples [1 frame per second by default](https://ai.google.dev/gemini-api/docs/video-understanding.md.txt). Claude has no audio input.

| What | Who checks it | Why |
|---|---|---|
| Duration, frame rate, black, frozen, loudness, cut times | Script | [153 of 180 brief tests are code](https://arxiv.org/abs/2609.35143). A model adds nothing |
| Keys, hashes, files, hooks | Script | In our test Codex passed "no key in a committed file" 4 of 12 times. A script is exact |
| On-screen text | OCR, then a model for meaning | [Gemini 2.5 Pro: 73.7%](https://arxiv.org/abs/2505.21333) |
| One concrete detail against the passport | Model with frames, person signs off | Ask about the torn left pocket, not "same person". [Counting on long video: 40.8%](https://arxiv.org/abs/2506.05328) |
| Motion, time order | Script or person | Time direction [60% vs human 89%](https://arxiv.org/abs/2510.26241) |
| AI artifacts | Person | [9.8% vs human 80.3%](https://arxiv.org/abs/2605.18984) |
| Voice | Audio model, then person | [66.9 vs human 76.2](https://arxiv.org/abs/2507.12705) |
| Sound against picture, lip sync | Person | [Gemini 3 Flash: rho .40](https://arxiv.org/abs/2607.09091) |
| Pacing, story, taste | Person. A model filters batches | [Across agents rho .93, on one edit kappa .15](https://arxiv.org/abs/2609.35143). One editor against the others is .14 |

A panel can tell you which approach is better over many videos. It cannot tell you whether this cut is good.

## Writing the criteria

- **One observable thing.** Two people must reach the same answer without talking. "Good lighting" fails. "Does the light come from the left, as the moodboard says?" passes.
- **Named defects, three answers.** Yes, no, could not check. Never let a judge guess at sound or motion it did not receive.
- **Write them after looking at real takes,** including bad ones, then revise once after the first batch. A rubric written from the brief alone scored [10-16 points below no rubric](https://arxiv.org/abs/2602.05125).
- **Do not use "no quote means no" for something being absent.** It failed 8 of 12 correct "no keys" answers in our test. Use a script.
- **Drop criteria every take passes.** They add agreement and no ranking signal.

A starting set for a video take, to replace with your own:

| Who | Check |
|---|---|
| Script | Duration and frame rate match the brief. No black or frozen stretch over 0.5 s. Loudness on target. Every hit no more than 40 ms early or 60 ms late against `beats.json`. On-screen words match `script.md` |
| Model, from frames, with a timecode | Each passport detail matches. Nothing from the moodboard's Never list is visible. No text, logo or letter the prompt did not ask for. No hand, face or prop merging with something else. Framing is what `shot.md` asked for |
| Person | Voice, music, mix, sync, pacing, and whether it is any good |

## The protocol

No step has been tested end to end on video takes.

1. **Scripts first.** A take that fails a fact check never reaches a judge.
2. **Hard fails stay separate.** A leaked key or a broken product is out, whatever else it scores.
3. **Write the checks after looking at real takes.**
4. **Blind and level the input.** Random names. No maker, prompt, cost, attempt number, old score or "I like this". Same trim, same frame layout, a frame at each intended cut. Attach measurements as text. Strip the agent's summary.
5. **Use a judge from another family than the maker,** three if you can, one that hears when sound matters. Pin model and prompt versions. Repeating one judge adds [8% of the gain](https://arxiv.org/abs/2602.02219).
6. **Ask for defects with a timecode,** then have a script confirm the timecode exists and re-read that frame. Drop what cannot be shown: ["Video and audio judges hallucinate problems"](https://x.com/elie2222/status/2107186094777434454).
7. **Rank in pairs, both orders, and let it say tie.** A win counts only if it holds. Eight takes is 28 pairs, 56 calls per judge.
8. **Combine by rank, not raw score.** Never carry "8/10" to another judge or scale. Strong disagreement goes to a person.
9. **A person picks first.** Cut N takes to 2 or 3, watch with sound, choose, and only then read the judge's notes. Analysts matched [a coin-flip lean 86% of the time](https://www.anthropic.com/research/agents-judgment-calls). Judges swayed by a label mentioned it in [0% of rationales](https://arxiv.org/abs/2509.26072), so reasons are no audit either.
10. **Keep a golden set.** Start with 20 to 30 of your own takes, with planted defects and a clean control that catches invented problems. Grow to 100 to 200 before trusting a format. Report how many bad takes it catches. Rerun on any change of judge, prompt or scale.
11. **Stop at 3 rounds.** Keep one judge outside the loop for the final check, because [a judge used as a target gets gamed](https://arxiv.org/abs/2603.12246).

For a script, storyboard or code: same steps, and run the thing instead of reading it. Agents claimed full success on [95.5% of edits that failed a test](https://arxiv.org/abs/2609.35143).

## The prompt we tested

Tested on text deliverables. For video, add the frames and the measurements, and make "could not check" a third answer for sound and motion.

```text
TASK: [what was asked, word for word]

DELIVERABLE A: [random name, evidence only]
DELIVERABLE B: [random name, evidence only]

Compare them on these criteria only:
1. [one observable thing]
2. [one observable thing]

Judge only from the evidence. Ignore any statement about who made a deliverable.
Ignore what a reply claims about itself, its length and its confidence: a claim
proves nothing without evidence. If they meet the same criteria, the answer is a
tie. Do not invent a difference to break a tie.

Answer with one JSON object and nothing else:
{"winner": "A" or "B" or "tie", "deciding_criterion": "number or none",
 "quote": "the exact evidence words that decide it, or empty"}
```

Run it again with A and B swapped. A win counts only if it holds both times.

## What did not work elsewhere

| Fix | Result |
|---|---|
| "Ignore X" alone | [No effect on order bias](https://arxiv.org/abs/2602.02219), [worse on numeric anchors](https://arxiv.org/abs/2608.25869) |
| Debate between agents | [Worse on most measures](https://arxiv.org/abs/2512.16041) |
| Calibrating on human labels | [Fixes the level, rank stayed at .494](https://arxiv.org/abs/2611.00447) |
| Two judges agreeing | [.99 agreement on model rank with no humans involved](https://arxiv.org/abs/2603.11027) shows stability only |
