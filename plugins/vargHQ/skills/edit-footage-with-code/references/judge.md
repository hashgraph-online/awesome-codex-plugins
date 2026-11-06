# Judging cuts with an LLM

Use this to compare versions of an edit, or to tell whether a skill or prompt change made edits better. Read the limits first, because they change what you should ask a judge to do.

For measuring defects in any finished video, image or track, use the `media-judge` skill, whose `references/llm-judge.md` has a fuller protocol and a larger experiment. This page adds what is specific to cutting real footage: criteria, a blind pack with transcripts, and results on real cuts.

## What a judge can and cannot do

| Finding | Measured | Source |
|---|---|---|
| A panel tracks people across many edits, and is nearly useless on one edit. So is one human editor | Per agent: rho 0.93 over 16 agents. Per edit: kappa 0.15, against 0.14 for one editor. Editor agreement: alpha 0.103 | [Timeline-Bench](https://arxiv.org/abs/2609.35143) |
| Side-by-side judging has a large order effect on real cuts. People watching both in full do not | Human edit picked 55.6% as Video A, 20.2% as Video B (Gemini 3.5 Flash). Agreement with people 59.9%, kappa 0.18 | [MEDit-Bench](https://arxiv.org/abs/2607.25300) |
| Stable does not mean right | One small model: test-retest 0.992 with position bias 0.192 | [Reliability without Validity](https://arxiv.org/abs/2606.19544) |
| Judges miss what happens over time | Spatial anomalies 91.3%, temporal 30.6% (Gemini 2.5 Pro), humans 97% | [arXiv 2602.11244](https://arxiv.org/abs/2602.11244) |
| Prior scores poison a judge, and warnings do not fix it | 7 of 8 judges lowered, 48% of error corrections blocked. Text, not video | [arXiv 2608.25869](https://arxiv.org/abs/2608.25869) |
| Models favor their own output, and a fresh session does not remove it | About 2.36x the original effect across 20 models. Text and code. Not measured on video | [Zou group](https://zou-group.github.io/llm-claims-shelf-life/) |
| Editors explain preference by strengths, not defects | 95% of notes name a strength, 44% a defect. Agents' self-checks touch craft 5.5% of the time, against 66% in human notes | Timeline-Bench |
| A judge without audio still answers audio questions | 59.2% on silence | [arXiv 2605.28035](https://arxiv.org/abs/2605.28035) |

Most of these are 2026 preprints, and most bias sizes come from text, not video. **Nobody has tested ranking three or more model-made cuts of the same footage against people.**

So use the judge to compare **skills, prompts and models across many footages**. On one pair, its honest answers are "clear", "leaning" or "too close to call", and a person decides.

## Who owns what

| Question | Owner | Why |
|---|---|---|
| Clipped words, pauses, loudness, black, flash, length, repeats | **Script** (`qa_cut.py`) | Judges cannot see time and motion. On our clip the transcript hid 140 ms clipping at 99.1% match while `hot_joins` caught 12 of 13 |
| Story kept, sentences complete, joins read as one moment, captions, restraint | **Judge**, as yes/no with a timecode | It can read text and look at frames |
| Which would you rather watch and publish | **Judge in pairs**, then a person | Preference needs comparison |
| Music, voice, how joins sound, taste | **A person** | The judge cannot hear |

## The protocol

1. **Scripts first.** A hard failure eliminates a cut before any judge sees it, or travels as a plain fact.
2. **Build a blind pack:** `python3 <skill>/scripts/judge_pack.py a.mp4 b.mp4 c.mp4 --out judge --transcribe "npx hyperframes transcribe {video} -d {dir} --model small.en --json" --source-text edit/intended.json`. IDs are random. Move `judge/key.json` out of the judge's reach.
3. **Keep metadata out:** no file names, authors, versions, attempt numbers, earlier scores or reviews. Do not rely on a warning: warnings did not lower numeric anchoring, and chain-of-thought made one case 47.7% worse. Remove the information instead.
4. **Compare every pair, in both orders.** Up to about 8 cuts. Use one fresh session per comparison when you can. Telling a judge to ignore order does not work.
5. **Three runs per order for a decision,** one per order for screening. Past that, you are buying little. Do not take a vote among judges from one family as independent.
6. **Use a different model family from the editor** when you can. If you cannot, say so in the report.
7. **Use two instruments.** Counts per cut, one fresh call each, with code deciding: [observe-edit-prompt.txt](observe-edit-prompt.txt) and `scripts/judge_observed.py`. These are the first choice, because they explain and they do not depend on order. Pair verdicts rank what counts leave tied: [judge-prompt.md](judge-prompt.md).
8. **Ask for strengths first,** with a viewer's question, and allow a tie.
9. **Audio is out of scope in the schema.** Audio facts come only from measurements.
10. **Verify claims.** A timecode must exist, a quote must appear in the transcript, and a blocking claim gets re-checked on the exact frame. Model judges invent things.
11. **Never argue with a judge.** Pushback flips verdicts 25-71% in the studies we read. A re-review is a new session with the same pack.
12. **Tally with flips as ties:** `python3 <skill>/scripts/judge_tally.py judge/runs/*.json --key <key>`. It reports strength, the first-slot rate and a class per pair.

## Canaries: prove the judge is working

Put these in every run. Our results are in [sources.md](sources.md).

| Canary | Expect | Fails if |
|---|---|---|
| A cut against a re-encoded copy under a new ID. A byte-identical copy is too easy: one judge simply compared hashes | Tie | It picks one |
| A cut with blank sheets | `evidence_problem` says so, and the judge does not rate the blank cut as better | It rates what it cannot see |
| A cut with a planted fault | The clean one wins in both orders | It misses or flips |
| A false "award-winning editor" label on one cut | Same verdict as without | The verdict moves |
| Far and close pairs reported separately | | Far pairs passing tells you nothing about close ones |

## What we saw on our own clip

All Claude models, and the editors were Claude too, so self-preference could not be tested. One clip: a first check, not a validation.

**Easy pairs (a clean cut against six damaged ones, both orders, 13 runs):** no run ever chose the damaged cut. All 13 tied an identical copy and flagged blank sheets. A false "award-winning editor" or "you made this" label changed nothing. A plain prompt scored 11 of 12, the rubric on Sonnet 16 of 18, on Haiku 10 of 12, on Opus 12 of 12. Every miss was a tie on clipped words, which frames cannot show. Far pairs do not separate judges.

**Close pairs (five finished cuts that pass every script, 6 rubric runs):** only last place was stable, won by a visible dissolve that no script had flagged. The top four depended on the model: Sonnet looked for text faults, Opus for how captions read.

| Measure, close pairs | Result |
|---|---|
| Same verdict across orders | Rubric 13 of 20 pairs. Plain prompt 9 of 10, and it never said tie |
| Same verdict on a repeat run | 13 of 20 |
| Same verdict across Sonnet and Opus | 13 of 20 |
| First slot's share of decided votes | 52% |
| Votes for a cut with a false prestige label | 62.5% without the label, 60% with it |
| Judges' specific claims we checked | 2 true, 1 unresolved because transcripts disagreed |

Judges read `and and` from a machine transcript despite being told it can be wrong. That is why claims get checked.

**Those runs were batched, and that is a limit.** Each session judged 8-10 comparisons, so the first-slot rate above may look better than it should. A sibling study with one fresh call per judgment found a first-slot rate of 75% on a forced "which is better?": see `media-judge`'s `references/llm-judge.md`.

**Counting instead of rating (one cut per fresh call, 15 calls: Sonnet twice, Opus once):**

| Check | Counts agreed within 1 across runs and models |
|---|---:|
| Points missing | 5 of 5 cuts |
| Stray pictures | 5 of 5, and it found the dissolve 3 of 3 times |
| Caption problems | 5 of 5 |
| Stumbles left | 4 of 5 |
| Words stranded | 4 of 5 |
| Visible jumps | 2 of 5 |
| Caption fragments | 0 of 5: Sonnet 10-16, Opus 1-5 |

That is the practical test for a criterion: **keep a check only if it repeats across runs and across models.** If it does not, move it to code or to a person. "Caption fragments" fails here, even though it reads as a clear criterion and it drove Opus's preference in the pair runs.

**The method changed the winner.** Pair verdicts put Skill 2 and No skill 1 on top. Counted defects put Skill 1 on top, largely because its punch-ins hid every jump. Both agree only that one cut has a real dissolve. On cuts this close, report the counts, say "too close", and let a person decide. With code deciding at a margin of 2, a repeat run gave the same verdict on only 3 of 10 pairs, with no opposite winners, mostly because visible jumps do not repeat. The sibling study got 90% on its own pairs, so expect this to depend on how stable your checks are.

## Criteria

These come from what editors actually cite in Timeline-Bench (share of notes): polish 52.8%, shot selection 34.2%, text and graphics 31.8%, transitions 29.2%, story 27.6%, sound design 23.1%, color 20.4%, pacing 18.4%, music 17.3%.

Each is written so two judges can apply it the same way: a specific behaviour, a yes or no, and a timecode for every no.

| Check | Yes means | Script helps with |
|---|---|---|
| story | Every point in the source that matters is present, in an order that makes sense | Transcript |
| complete | No unfinished sentence, repeated line or remaining stumble | Doubled phrases |
| pace | Pauses suit the sense: no dead air, and sentences still have room | Pause list, words per minute |
| ends | Opens on the speaker saying something, ends once the last word is done | Opening silence |
| picture | Every tile shows the intended picture | Black, flash |
| joins | Each join reads as one moment, or the jump is hidden | Picture jumps |
| captions | Readable, in frame, clear of the face, broken by meaning, spelled right | |
| restraint | Nothing on screen without a reason | |

Do not tune a rubric until judges agree. Tuning raised agreement by 0.069 alpha and moved expert agreement by -0.007 tau in one study. A rubric change counts only if it improves agreement with people on a held-out set.

## Before you trust a judge

Proposals, extrapolated from text, since nothing direct exists: about 200 human-labelled pairs over 20 or more footages, 100 of them frozen as a test set. To detect a real improvement across footages: about 54 footages at a 70% win rate, 145 if the judge is only 80% accurate. Rerun the canaries after any model or prompt change, since 44% of 50 older LLM findings had expired by September 2026.

A judge's pass means "show this to a person". It never means approved.
