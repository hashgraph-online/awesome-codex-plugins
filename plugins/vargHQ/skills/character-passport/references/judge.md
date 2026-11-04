# Judging and ranking takes with AI judges, without bias

An AI judge is only as reliable as its questions. Ask concrete yes/no questions, one criterion per call, with
the reference in view. Move what a vision model can't see reliably (faces, left/right, tiny details, speech
pace) into code. Check the judge against people before you trust its numbers. Sources, numbers and quotes for
everything below: `judge-evidence.md`.

## What our own test showed (2026-11-03, two blind AI judges, 16 stills)

| Question format | Result | Verdict |
| --- | --- | --- |
| Yes/no passport checklist, 224 calls | 92% agreement, Cohen's kappa 0.88 | reliable |
| Side-specific / tiny items | "hair behind the right ear only" kappa 0.00, "nose bump" 0.50 | rewrite or move to code |
| 1-10 film-likeness | every score 6-8; judges correlate r = 0.47 | too vague to rank |
| 1-10 same person per method | same order as ArcFace face similarity (Spearman 1.0) | big gaps only |

Face check (`scripts/face_check.py`, ArcFace cosine to the sheet's front close-up, same person >= 0.28):
one-line subject 0.02 (0/4 match), passport 0.44 (3/4), + grey sheet 0.66 (4/4), + moodboard sheet 0.58 (4/4).
Averaged over both sheets the two sheet methods tie (0.62 vs 0.64): the judges' 1-point lead for the grey sheet
came from anchoring on the reference they saw first. An action-unit detector (py-feat) gave both "laugh" panels
the same AU6 0.90: it cannot tell genuine from posed acting.

## Biases and their fixes

| Bias | Size | Fix |
| --- | --- | --- |
| Position in a pair | verdict kept after a swap: GPT-4 65%, Claude-v1 23.8% | both orders; disagreement = tie |
| Provenance labels | "Expert" label +18%; model names up to 50 points; never mentioned by the judge | random IDs, no names, no prompts |
| Length | padded answer fooled Claude-v1 91.3% | short critiques; normalised takes |
| Self-preference | GPT-4 +10%, Claude-v1 +25% | judges from other families than the generator |
| Score bunching | one value dominates; video judges score everything average | binary or anchored 0-2; pairs to rank |
| Yes-bias | LLaVA says yes to 80% of no-questions | absence questions; "cannot_determine" |
| Visual tricks | brightness/overlays up to +109.6%; "ignore it" prompts fail | normalise inputs |
| Small details, sides | small objects -7 to -24 pts; crop 39% -> 70%; left/right 56% vs 99% for people | crop and enlarge; side decided in code |
| Format | pairs 79.3% agreement vs scoring r = 0.49 (GPT-4V) | pairs and binary items only |

## Protocol

1. **Blind.** Random IDs; strip filenames and metadata; never pass model, method, prompt or seed; same size,
   format and aspect; no captions or borders; keep the ID map outside the judging code. Reference always first.
2. **Code first** (cheap, deterministic, gates the judge):
   - identity: `scripts/face_check.py` (InsightFace models are non-commercial; use AuraFace, Apache 2.0, for
     commercial work); faces under ~64 px of source detail -> `cannot_determine`;
   - passport details: crops cut from face landmarks on the named side and the mirror side, upscaled to >= 512 px;
   - props: crop similarity to the prop sheet (DINO / DreamSim) as a drift alarm;
   - pace: `scripts/voice_check.py`; prompts: `scripts/prompt.py check`.
3. **One criterion per call**, binary or 0-2 with written anchors, always with `cannot_determine`. The judge
   describes, compares with the reference, then answers in JSON. Shuffle item order if several are grouped.
4. **Rank in pairs, both orders**, then Bradley-Terry over the pairs. Never rank many takes in one prompt.
5. **Three judges, three model families**, none from the generator's family (flag Gemini on Nano Banana/Veo
   takes, GPT on GPT Image takes). Majority vote; a 1-1-1 split goes to a person. k = 3 samples on borderline
   items.
6. **Calibrate.** Two people label 20-30 takes and sharpen the definitions, then freeze the rubric (criteria
   drift is real). Then 60-200 labelled items per criterion, with failures planted on purpose (mirror the scar,
   remove the button, add a finger). Keep a criterion for the judge only if TPR >= 0.85, TNR >= 0.85 and
   kappa >= 0.6 against the people: `scripts/judge_agreement.py a.json b.json --human h.json`. Re-calibrate after
   any change of model, prompt or rubric. Expect acting (C2, C3) and film-likeness (B7) to need people at first.
7. **Report uncertainty.** 3-4 seeds per cell; pass rates with a cluster-bootstrap interval over scenes; a
   50% vs 65% difference needs about 170 cells per method.

## Never ask a vision judge

Same person or not (embedding) · left or right (code) · a tiny detail on a full frame (crop) · counts of fingers,
teeth, buttons · one 1-10 quality score or a ranking of many takes in one prompt · genuine acting from one still or
from video at 1 fps (send 4-8 fps strips) · voice pace by ear (measure).

## Rubric

| ID | Criterion | Pass / fail | Decided by |
| --- | --- | --- | --- |
| G-ID | Same person as the sheet | face similarity >= calibrated threshold | code |
| ID-1 | No contradicting features | fail on different eye colour, brow shape, nose, hairline, jaw, ~10-year age gap; list each | judge |
| PD-k | Passport item k | present in the named-side crop, absent in the mirror crop (crops unlabelled, random order) | judge + code |
| PR-k | Prop item k | colour, shape, wear, markings match the prop-sheet crop | judge |
| B1 | Anatomy | wrong finger count, fused fingers, extra teeth, malformed ears | judge (crop) |
| B2 | Skin | waxy, no pores where they should show, airbrushed sheen | judge |
| B3 | Light logic | shadows/catchlights from different sources; light with no source in the scene | judge |
| B4 | Text | any garbled or invented lettering (n/a if none) | judge |
| B5 | Background | melting objects, bending straight lines, clone patterns | judge |
| B6 | AI gloss | over-sharpening halos, saturation beyond the reference grade | judge |
| B7 | Film-likeness | 0 AI ad/stock/CG · 1 plausible photo, not cinema · 2 could pass as a film frame (anchored by 3 real film frames); rank by pairs | judge |
| B8 | Temporal (video) | face, costume or prop morphs; pop-in; flicker | judge |
| C1 | Emotion reads | a viewer would name the beat's emotion from face and body | judge |
| C2 | Genuine, not posed | 0 posed, eyes and mouth disagree · 1 stiff · 2 eyes and mouth agree, visible cause, natural onset | judge, calibrated |
| C3 | Intensity | under / right / over for the beat and the shot size | judge |
| C4 | Timing (video) | no reaction snapping on/off or starting before its trigger | judge, 4-8 fps |
| VO-1 | Pace | words per minute within ±15% of the target | code |

## Judge prompt (one criterion per call)

````text
SYSTEM
You are a strict visual inspector for film production. You check ONE criterion.
You do not know how these images were made, and it does not matter.
Judge only what is visible. If the evidence is not visible or too small, answer "cannot_determine". Do not guess.

USER (fixed order: reference first, candidate second)
[REFERENCE: character C1] <ref_front.png> <ref_34.png> <ref_detail_P3.png>
Passport item P3: pale vertical scar, about 1.5 cm, on the chin.
[CANDIDATE take_7f3a] <CROP 1> <CROP 2>

CRITERION PD-P3
A: Is the scar described in P3 visible in CROP 1?
B: Is it visible in CROP 2?
"Visible" = a line of lighter or raised skin of roughly the reference shape and orientation.
Shadows, stubble or compression noise do not count.
Examples: <pass_example> PASS because ... <fail_example> FAIL because ...

Steps: 1) describe each crop in 1-2 sentences, 2) compare with the reference, 3) answer.
Return ONLY JSON:
{"criterion":"PD-P3","observation_crop1":"...","observation_crop2":"...","comparison":"...",
 "answer_crop1":"yes|no|cannot_determine","answer_crop2":"yes|no|cannot_determine","confidence":"low|medium|high"}
````

Pairwise variant (B7, C2, ranking takes): describe take A, describe take B, then
`{"preference":"A|B|tie|both_fail","reason":"..."}`; always run twice with A and B swapped.
