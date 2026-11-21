# Judging frames against the board (LLM-as-a-judge without bias)

Tested on the 48 stills behind this skill (2026-11-04) plus 1,710 X posts and 73 papers and guides.
Data: https://github.com/vargHQ/aeo/tree/main/research/2026-11-03-moodboards/llm-judge (varg team access).

## What we measured

| Test | Result | Rule |
|---|---|---|
| No criteria ("rate quality 1-10") | Judges agree with each other (r 0.85) but score against the board (r -0.44); no-board frames 8.1 vs 6.4 | Never ask for "quality" |
| Retest, same rubric | Line scores r 0.87 (84% identical); holistic 1-10 score r 0.61 (33% identical) | Rank on line scores |
| Opus vs Sonnet, same rubric | Line totals r 0.91; leniency gap 1.2 points that reverses with the prompt | Use ranks or z-scores per judge |
| Pairwise, both orders | 1 of 24 pairs flipped; full board won 92% in both orders | Rank by pairs shown both ways |
| Label leak ("shot on film" vs "AI-generated") | -1.25 points (p 0.001); Spearman 0.41 between the two labels | Never reveal where a frame came from |

## Protocol

1. Label a gold set: 50-100 frames, about half failures, line by line, by the art director.
2. One question per board line with anchored 0/1/2 levels (or yes/no atoms) naming what must be visible.
3. Measure in code first: palette ΔE (scripts/palette.py), OCR for text, optical flow for camera moves, face embeddings for identity. Vision models pick the right hex 40.6% of the time (ColorBench) and camera motion at 36.4 AP vs 50.1 for structure-from-motion (CameraBench).
4. One line per call; short evidence before the score.
5. Give the reference frame with each line (a reference cut judge failures from 70% to 15%, Zheng et al. 2023).
6. Blind: random ids, no model names, prompts, versions, costs, earlier scores or source labels; same resolution; no overlays (boxes raise GPT-4o scores by up to 80.2%).
7. Two judges from families other than the generator; combine ranks, not raw numbers (a 3-family panel: κ 0.763 vs 0.627 for one judge).
8. Rank survivors in pairs, both orders; inconsistent = tie for a human.
9. Gate with the minimum: a failed must-have line or defect rejects; non-applicable lines are N/A.
10. Low temperature, 3 samples; unstable verdicts go to a human.
11. Use the judge at Cohen's κ ≥ 0.6 vs the gold set, automate at ≥ 0.8; freeze the wording; re-check monthly.
12. The maker never grades itself: a fresh-context critic sees only the board, references and frames.

## Judge prompt

```text
You are a blind judge of AI-generated frames for one moodboard. You did not make these frames and you do not know which prompt, model or version made each one. Never guess.

Inputs: moodboard.md (the board), 1-3 reference frames, and the frames to judge, named only by random ids.

For EACH frame, line by line:
1. Look first, then write what you SEE for the line in one short phrase (evidence), then the score. No score without evidence.
2. Score each line 0 / 1 / 2 against the board's exact words:
   - Palette: 2 = the named hex colours dominate and nothing else saturated appears; 1 = right family, one extra saturated colour or wrong accent; 0 = different palette.
   - Light: 2 = key from the named side and height, named hardness, named colour temperature, one source family; 1 = right source but wrong side or hardness; 0 = flat, evenly lit or a different source.
   - Framing: 2 = named shot size, camera height and angle, subject at the named place and size (±10% of frame); 1 = one of those off by one step; 0 = different shot.
   - Texture: 2 = the named medium and flaws visible at 100% (grain, halation, softness); 1 = generic "film look"; 0 = clean digital or plastic.
   - Subject: 2 = identity, outfit and colours match the sheet; 1 = one detail off; 0 = different person or product.
   - Motion cue (stills) / camera move (video): 2 = the named cue or move happens; 1 = partly; 0 = absent or a different move.
   - Type: score only if the board says the model draws it; otherwise "n/a, set in code".
3. Defects, pass/fail: anatomy (hands, faces, limbs), text or logo artefacts, AI tells (plastic skin, perfect symmetry, gradient glow). Any fail caps the frame at "reject".

Then rank:
4. Compare frames in pairs only. Show each pair twice, A/B and then B/A. Keep a verdict only if it is the same both times; otherwise call it a tie.
5. Rank by: defects first (fails go last), then total line score, then pairwise wins on "closer to the reference frames".

Rules: temperature 0; ignore image order, file names and resolution; never reward a frame for looking "AI-impressive" or for detail the board did not ask for; a frame's beauty does not raise a line it fails. Output JSON: {id, evidence{line:phrase}, scores{line:0-2}, defects{name:pass|fail}, total, verdict: keep|fix:<line>|reject}, then the ranking with ties marked.
```
