# Character references with GPT Image 2.6 (ChatGPT's image model)

Tested 2026-11-05, one day after release: the Vesna test from `evidence.md` rerun on `gpt_image_2_6` through varg,
same passport, look block and four shots. 43 images, $2.86. Face scores: `scripts/face_check.py` (ArcFace cosine to
the sheet's front close-up, same person >= 0.28). Checklist: two blind AI judges. One take per prompt and method.

## Settings

| Setting | Value | Why |
| --- | --- | --- |
| Model | `gpt_image_2_6` (Flare, the default) | Sunburst cost the same, took longer, and its sheet panels were about as consistent (0.54 vs 0.51, one sheet each) |
| Size | `provider_options.fal.image_size` `{"width": 2560, "height": 1440}` for sheets, 1920x1080 for shots | `aspect_ratio: "16:9"` alone returned 1088x608; the bigger size cost the same |
| Quality | `high` | $0.06 a generation, $0.07 an edit with references |
| References | the sheet URL in `files` (up to 16 per call) | no face-fidelity setting exists on 2.x; omit `input_fidelity` |
| `reasoning_effort` (OpenAI "complexity") | leave at the default for shots | low on Sunburst did not stop drift in chained edits (below) |
| Prompt | at most 2,000 characters on varg's image tool | `scripts/prompt.py check` |
| Cut-outs | `background: "transparent"`, `output_format: "png"` | returned a real alpha channel |

## What we measured

| Test | GPT Image 2.6 | Nano Banana 2.1 |
| --- | --- | --- |
| Face similarity, passport only (4 shots) | 0.48, 4 of 4 same person (3 of 4 at 1088x608) | 0.44, 3 of 4 |
| + grey sheet as Image 1 | 0.72 | 0.66 |
| + moodboard-lit sheet as Image 1 (vs the grey sheet) | 0.66 (0.75 vs its own sheet) | 0.58 |
| Passport details right, passport only | 64% | 46% |
| Passport details right, + moodboard-lit sheet | 68% | 63% |
| Scar on HER left side of the chin | 0 of 14 | 0 of 14 |
| Hair behind her right ear only | 10 of 21 | 0 of 23 |
| Sheet grid or backdrop leaking into shots | 0 of 14 | 0 of 8 |

- **Chained edits drift.** Five edits in a row on the last picture: 0.74, 0.55, 0.50, 0.46, 0.48 (Flare);
  0.73, 0.49, 0.42, 0.31, 0.29 (Sunburst, `reasoning_effort: low`). The same five instructions as fresh calls from
  the sheet: 0.89, 0.70, 0.75, 0.66, 0.85 (mean 0.77). The fresh calls also carried the passport and look block; the
  edits only the change. Chained frames still matched each other (0.71 vs 0.73): the chain settles into a different
  face. One of two judges called all 5 chained Flare faces waxy, the other none (a lead, not a finding).
- **Expressions.** Cause + physical tells looked more genuine than adjectives in 8 of 12 judgments (one AI judge, six
  emotions shown in both orders; the cause prompt was 4x longer and repeated the face description).
  Misfires: "white above the irises" made startle cartoonish; "eyes wet" turned worry into sadness; the one-sided
  contempt tell did not show.
- **Age.** InsightFace's age estimate: median 51 for the 12 shots (Nano Banana: 30) from a passport that says 30.
  An explicit age line moved the sheet's front close-up from 40 to 32 in one take.
- **Invented text.** Readable signs and posters in 7 of 8 judge checks of text-only shots, 2 of 16 with a sheet;
  the no-text line gave blank panels in one retest image.
- **Props named in the look block appear.** "Only the umbrella saturated red" added a red umbrella to all 5
  close-ups that had none in the action (2 in a stranger's hand).
- **Prop sheets.** Wear landed on the sheet (the worn J-handle); a geometry defect (a bent rib) did not. In shots
  without the prop sheet attached, the worn handle was right 6 of 24 times: attach it as Image 2.
- **Fix passes.** A whole-sheet edit with six fixes kept the face, fixed almost nothing, kept the scar on the wrong
  side and added a ring. One fix on the front panel, cropped and enlarged 2x, with the side named as the viewer
  sees it, moved the scar to the correct side; hiding one ear under hair failed in the same call.

## Rules for this model

1. Set `image_size`; never rely on the aspect-ratio default for a sheet.
2. Every shot is a fresh call: the sheet as Image 1 + the shot + the passport. Never edit the last output again.
   In the ChatGPT app: save the sheet as a reference and call it with `@name` in each new request.
3. Add "No readable words anywhere: posters, signs and screens are blank or out of focus" to every shot prompt.
4. Name a prop only in shots it is in, including inside the look block.
5. Add an age line: "her age reads as exactly <n>: <what stays young>, <where the tiredness shows>". Check the age.
6. Expect every left/right detail mirrored. Fix it on a cropped panel, one change per call, the side named as the
   viewer sees it ("the right side of the picture, her left"), then check. Or drop it from "never change".
   Untested here: `gpt-image-markup-edit` draws the target spot on a transparent layer, which may place it better.
7. Expressions: cause + tells; startle "for a split second" without "white above the irises"; worry without
   "eyes wet"; one-sided tells as the main instruction with the still side named.
8. Before approving a sheet: age, every side detail, small items (plasters, missing buttons, stains), prop defects,
   no invented text, no extra jewellery, then ten test shots in different light.

## Prompts

Sheet: the turnaround prompt in `sheets.md`, plus the age line. Shot:

```text
Image 1 is the character sheet of <name>: use it for her identity only (face, hair, body, clothes); do not copy
its layout, panels or background. <shot: size, lens, action, light>. No readable words anywhere: posters, signs and
screens are blank or out of focus. SUBJECT: <passport>. <prop passport if the prop is in the shot>. <look block>.
```

Panel fix (crop with `scripts/crop_sheet.py`, enlarge 2x, upload, then):

```text
Edit Image 1, a close-up of a woman facing the camera. Keep everything else exactly as it is: the same face, skin,
expression, hair, clothes, background and light. Make only this change: <one change>, on the RIGHT side of the
picture (her left side).
```

## Sources

OpenAI: Introducing Images 2.6 (https://openai.com/index/introducing-images-2-6/), image generation guide
(https://developers.openai.com/api/docs/guides/image-generation), GPT Image 2.6 prompting guide
(https://developers.openai.com/api/docs/guides/image-prompting), saved references in ChatGPT
(https://help.openai.com/en/articles/11084440-images-in-chatgpt). Drift: Artificial Analysis, 30 chained edits on
GPT Image 2.5 Sunburst, "only about a fifth of the image unchanged"
(https://x.com/ArtificialAnlys/status/2108600224478572767); Keigo Matsumaru, face changed by the 2nd edit on 2.6
(https://x.com/k_matsumaru/status/2118186638228816322). Full guide: Claude Doc DvZVWEccvt1TFoZR7oHEaY. Model guide,
sizes and recipes: the `gpt-image-2-6` skill.
