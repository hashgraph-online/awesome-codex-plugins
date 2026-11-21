# Sheets: turnaround, expressions, props

Every sheet is made from the passport, approved as a still, and then attached to every later image or video call.
More layouts (from photos of a real, consenting person; split sheet; labelled bible; identity board; filling a
missing view with `qwen_angles`): varg-character-design `references/sheet-prompts.md`.

## Moodboard look or flat grey

Tested 2026-11-03: the same passport on flat 18% grey and in the LAST BUS look (sodium key from high left, cold
blue fill from the right, 500T grain, #1A1A1A backdrop). As Image 1 in four shots each, both kept the face in 8 of
8 shots and neither leaked its grid or backdrop. The look sheet did not drag night light into a fluorescent
break-room shot, because the shot stated its own light.

| Sheet | Use it when | Watch out for |
| --- | --- | --- |
| Moodboard look | One film, one light family. The sheet doubles as a look test; people approve the face as viewers will see it | The fill must open the shadows; a hard single key hides half the face and the model will invent it. Never put the location in the sheet |
| Flat 18% grey, even light | The character crosses very different lights, several films, or the model copies backgrounds | Approval happens in a light nobody will see |

## Turnaround (moodboard version)

```text
Character turnaround sheet in the look of the film <she/he> is in: <film stock and texture>. Every panel lit the
same way: <key: source, Kelvin, direction>, <fill: source, Kelvin, direction>, face fully readable. Plain <darkest
palette hex> backdrop, no location, no text, no labels, no logos. Top row: three full-body views at the same scale
on one ground line: front, side profile, back; arms relaxed, empty hands. Bottom row: three large head-and-shoulders
close-ups: front, three-quarter, side profile. The same <woman/man> in every panel: identical face, hair, body,
outfit and proportions. Do not beautify, de-age or redesign <her/him>. CHARACTER: <passport>. Photoreal, visible
pores, no retouching.
```

Grey version: replace the first three sentences with "Character turnaround sheet, flat 18% grey studio background,
even soft shadowless light, no text, no labels, no logos."

16:9 on `nano_banana_2_1` gives 1376×768: each close-up is ~450 px wide. For bigger faces make a second
"face sheet" (three close-ups only) and use it as the face reference for video.

## Expression sheet (cause + tells)

```text
Expression sheet of the <woman/man> in Image 1, in the same film look as Image 1 (<texture, key, fill, backdrop>),
no text, no labels. A 3x2 grid of large head-and-shoulders close-ups from the same camera angle. Identical face,
hair and outfit in every panel; only the expression changes. Each panel is a moment with a cause.
1: <cause>: <tells>. 2: <cause>: <tells>. ... 6: <cause>: <tells>.
```

Tells per emotion: `acting.md`. Tested: the adjective version ("neutral, laughing, angry, surprised, sad, smug")
gave stock faces; the cause + tells version gave restrained, specific ones with the same identity.

## Prop sheet

```text
Prop reference sheet of one object, in the look of the film it is in: <texture, key, fill>, plain <hex> backdrop,
every panel lit the same way, no hands, no text, no labels, no logos. Five views of the same <object> at the same
scale: <three-quarter from above>; <side>; <closed / folded / at rest>; a close-up of <the wear detail>; a
close-up of <the second detail>. THE OBJECT: <prop passport>. Photoreal, real material texture: <materials>.
```

Tested: the umbrella sheet kept every wear detail (lacquer worn to pale wood, bent rib, faded top panels, rain
beads). "Faded paler" turned salmon-orange on the top panels: give a hex for the faded colour if it matters.

## Check before approving

Go down the passport and tick each detail on the sheet. Misses we saw: hair longer in the close-ups than in the
full-body row; the "left" scar drawn on her right on both sheets (sides get mirrored); a "missing button" never
visible because the passport's own scarf covers it (check that no detail hides another); posture (stoop) lost in a
straight front pose.
Fix with an edit pass on the approved sheet ("move only the scar to the left side of the chin; change nothing
else"), not a re-roll, which brings new misses.

## Cut it for video

```bash
python3 scripts/crop_sheet.py cast/vesna-sheet.png --out cast/vesna-panels
# r2c1.png = face front (identity), r1c1.png = full-body front (costume), r1c3.png = back (hair, garment cut)
```

## From people with finished work (verbatim in x-evidence.md)

- One visible face per reference image; remove the head from full-body views if the model locks onto the wrong face
  ([@AI__TSUBAKI](https://x.com/AI__TSUBAKI/status/2071600101500518510)).
- Small faces on dense sheets drift in video: make a face sheet, feed 2-3 cropped panels
  ([@meAsifAi](https://x.com/meAsifAi/status/2092329368722801150)).
- Four big frames keep more detail than a 3x3 grid ("split stack") ([@henrydaubrez](https://x.com/henrydaubrez/status/2001337146905690519)).
- Build the sheet after character, set and style are comped together, so it is already in the film's look
  ([@CuriousRefuge](https://x.com/CuriousRefuge/status/2065162768014299228)).
- Write each character's height on the sheet; with three or more characters say in the prompt who is taller.
- If a video model's face filter rejects a clean sheet of a fictional person, a grid drawn over the faces is reported
  to pass ([@mitte_ai](https://x.com/mitte_ai/status/2092734957546287431)); never use it for real people.

## Animation conventions (sources in craft-evidence.md)

- Orthographic, no perspective; head top, eyes, chin, shoulders, waist and feet on the same horizontal lines in every
  view ([Brian Lemay, production art](https://brianlemay.com/Pages/animationschool/layout/Production%20Art%204/Production%20Art%20part%201.pdf)).
- With more than one character: a line-up sheet of the whole cast on one ground line with heights marked.
- A hand sheet when hands hold the hero prop (open, fist, grip on the prop, pointing, relaxed).
- Work out the design in the three-quarter view first (Valve, TF2).
