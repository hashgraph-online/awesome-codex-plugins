# Eyes: the vision pass

Read this before answering `questions` in `facts.json`.

## Why this order

| Finding | Number | Source |
|---|---|---|
| Vision models spotting temporal glitches, best of 12 | 54.1% accuracy | [TempGlitch](https://arxiv.org/abs/2605.21443) (gameplay clips) |
| Claude Opus on the same set | recall 17.5%, false alarms 15.5% (worked out from its accuracy) | same |
| Gemini 3 Flash on the same set | recall 87.2%, false alarms about 87%: it says glitch to everything | same |
| Going from 1 to 5 fps | barely helps | same |
| Faults of 0.1 to 0.2 s at 0.5 fps | uniform sampling catches 11.81%, shot-aware 84.70% | [SynFlash](https://arxiv.org/abs/2603.17374) |
| "What is unusual" against "what is wrong" | 57.2% against 29.5% (64.9% when asked to describe) | [GlitchBench](https://arxiv.org/abs/2312.05291) |
| Adding "double check" | +2.70 points | [Vision Language Models are Biased](https://arxiv.org/abs/2505.23941) |
| Vision LLMs predicting real gaze | CC 0.408 (GPT-5.4), 0.344 (Claude Opus 4.6) | [arXiv 2604.26352](https://arxiv.org/abs/2604.26352) |
| GPT-5.4 rating motion against people | SRCC 0.25 to 0.37, people 0.61 to 0.77 | [MotionInsight](https://arxiv.org/abs/2609.37030) |

Eyes are for reading and naming. Code is for detecting. If you did not get the moment from code, say so.

## Rules

1. **Fresh context.** The judge has not seen the prompts. It has the file, the brief and the references.
2. **Only the window.** Open the evidence and contact sheets, not the whole film.
3. **Describe first.** Name what is in the frame before any opinion. Naming every object catches melted hands and wrong counts that a direct question misses.
4. **Ask what is unusual, never what is wrong.** The second wording makes models miss far more.
5. **Yes or no, per item, with a time.** Google's ABCD Detector asks one yes/no with a timestamp per rule. Scales drift and can be negotiated, so no 1-10.
6. **Prove you looked.** Quote something visible in the frame in each answer. SeeCut guards against judges that did not watch. Answers with no quote are dropped.
7. **Every finding has a place and a fix.** OpenMontage's rule: no finding without a location and a fix.
8. **Hints stay hints.** "Judges hallucinate problems" (elie2222). A model's opinion with no measurement goes under Hints.
9. **Cap the passes.** Two or three, then ship or escalate to a person. Video Use caps at three.

## Observations beat verdicts

Ask what is there and let code decide. In our test, one take per call with observations repeated 67% of the time, against 47% for pass or fail, and 90% with no opposite winners once a win needed a margin of 2. "How many words are in the fullest frame?" repeated 100%, where "no frame holds more than 18 words: pass or fail" repeated 69%. The prompt is `references/observe-prompt.txt`, and `references/llm-judge.md` has the data.

## Answer format

```json
{"id": "cause", "shot": 3, "t": "00:07.20", "answer": "no visible cause", "quote": "white box on a dark floor, no hand or object near it", "evidence": "evidence/motion_168.jpg", "fix": "start the move on the footstep at 00:07.05"}
```

## Questions per failure

The tool writes these into `facts.json` with the right frames. This is the reasoning behind each.

| Failure | Code gives you | You answer |
|---|---|---|
| 1 Same size | block heights, biggest over second, shot sizes | Name the largest and second largest element. "Same size" if about equal. |
| 2 Leads the eye | heat map per shot, peak count, top share | Name the subject. Does the top peak sit on it? |
| 3 Too much on screen | words at once, edge density, element count, reading time, contrast, safe zone | From the frame alone, can you read the product's name and say what it is? Quote it. |
| 4 Motion has no cause | moves that start with no sound or text change near | Name what starts it: a hit, a person, an earlier element. Else "no visible cause". |
| 5 Pinned graphics | regions that hold still while the scene moves | Caption or logo on the glass, or does it claim to belong to the scene? |
| 6 Labels slide off | drift between label and its surroundings | Name what it points at. Does it still touch that in the last frame? |
| 7 Banding | CAMBI before and after upload, lifted frames | Do you see bands in the lifted frame? Where? |
| 8 Numbers jiggle | shake of a digit that keeps its value | Open the stack of crops. Does the row hold still? |
| 9 Face, outfit, light | identity, torso colour, side light, pair crops | Same person? What changed? Is it in the brief? |
| 10 Sound after the cut | signed offset per cut | Listen if you can. Otherwise report the numbers and say "measured, not heard". |
| 11 Spelling | candidate words with crops | Read the crop letter by letter. Real typo or OCR misread? |
| 12 Template | distance and margin, pair sheets | Name three things that could only come from this brief. |

## Motion is not stills

Frames are not motion: flicker and half-second face morphs pass on any single frame. Use the strips the tool writes, which are
consecutive frames around the moment. If a question is about movement and you only have one frame, answer "cannot tell".

## Sound

Most judges cannot hear. Write "measured, not heard" in the report and do not describe how something sounds. If you have a
model that takes audio, use it for mispronounced names and flat delivery, and treat the answer as a hint.
