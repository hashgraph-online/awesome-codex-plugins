# Sheet prompt templates

Each template fits varg's 2000-character image prompt. Replace `<…>`. For model input keep the background flat light grey, the light even, and the sheet free of text. A white background tends to overexpose as a reference, and a scene background bleeds into later shots.

## Which sheet for which job

| Sheet | For | Feed it to |
|---|---|---|
| Model sheet (6 views) | Identity for every later call | Image edits, Seedance, Wan, MiniMax; crop it for Kling elements |
| Split sheet (face left, body right) | Maximum face size for video swaps | Seedance, Wan, MiniMax H3 |
| Expression sheet | Close-ups and dialogue that stay on-model | Seedance alongside the model sheet |
| Outfit sheet | One sheet per look; a second outfit on one sheet makes hybrids | Image edits |
| Prop sheet | The signature item, product or weapon | Kling elements, image edits |
| Labelled bible | People: casting, client approval, the brand book | Humans only; keep a text-free twin for models |
| Identity board | Stylised characters whose medium must hold | GPT Image, Seedream, Seedance |

## 1. Model sheet from text (the default)

```
Character reference sheet for AI video, flat light-grey studio background, even soft studio light,
no text, no labels, no logos. Top row: three full-body views at the same scale on one ground line:
front, side profile, back, arms relaxed, empty hands. Bottom row: three large head-and-shoulders
close-ups: front, three-quarter, side profile. The same <woman/man/creature> in every panel:
identical face, hair, body, outfit and proportions.
CHARACTER: <name>, <age as a number>, <height and build with visible cues>, <face: shape, eyes,
brows, nose, lips, skin texture, marks>, <hair>, <signature detail>, <default expression>.
WARDROBE: <garment by garment: cut, colour, material, fit>.
<STYLE: "Photoreal, visible skin pores and natural skin texture, no retouching." | a style block>
```

Models: `seedream_5_pro` for photoreal (2K), `nano_banana_2_1` for stylised. Swap the bottom row for expressions ("neutral, laughing, suspicious squint, shouting") when the character has to act.

## 2. Model sheet from photos of a real, consenting person

Attach 2–3 photos in `files` (`nano_banana_2_1`, `gpt_image_2_5` or `seedream_5_pro`). From @simonecanciello's widely shared prompt (Oct 2026):

```
Character turnaround sheet of the person from the reference photos, six views: full body front,
side and back + close-up front, side and back. Strictly keep 100% of face, hair, body, clothing
and all details from the reference. Clean light grey background, consistent and natural lighting.
No text, no labels.
```

Crop the source photos to the person first, so their background does not bleed into the panels. Use only people who agreed to it.

## 3. Split sheet (face first, for video swaps)

From @VisuraCode (used with Wan 3.0):

```
Professional photo character sheet on a flat grey background (#7B7B7C). Left side: an extreme
close-up of the subject's face. Right side: front and back views from head to toe.
Subject: <description>. No text.
```

Add a side close-up if the shot turns the head.

## 4. Labelled bible (for people, not for models)

The layout that rendered on all six models we tried (Nonna Rosa, 2026-10-27):

```
Character reference sheet of one original character on a clean light-grey studio background,
landscape, flat even lighting, <style>. Character: <full card>. Layout: left two thirds: four
full-body views at the same scale standing on one ground line: front, three-quarter, side profile,
back. Right third: a 2x2 grid of head-and-shoulders close-ups: <four expressions>. Bottom strip:
five colour swatches of the palette, and <2–3 signature props> as separate props. Small clean
sans-serif labels under each panel. The same face, hair, outfit and proportions in every panel.
```

Best text: `gpt_image_2_5` (ask for `provider_options.fal.quality: "high"`; default output is ~1088 px wide) and `nano_banana_2_1`. Add a profile block ("Name, Age, Personality, Signature look") or hex codes under the swatches if the bible goes to a client.

## 5. Expression sheet

```
Expression sheet of the character from the reference image, flat light-grey background, even light,
no text. A 3x2 grid of large head-and-shoulders close-ups from the same camera angle: neutral,
laughing, angry, surprised, sad, smug. Identical face, hair, glasses and outfit in every panel;
only the expression changes.
```

Extreme expressions drift first; regenerate only those panels' sheet if they break.

## 6. Outfit sheet (one per look)

```
Outfit sheet of the character from the reference image wearing <new outfit, garment by garment>,
flat light-grey background, even light, no text. Three full-body views at the same scale: front,
side, back. Same face, hair and body as the reference; only the clothes change.
```

## 7. Prop or product sheet

```
Object reference sheet of <the signature item>, flat light-grey background, even light, no text.
Four views: front, side, back, three-quarter top; one close-up of <the detail that must survive>.
```

Keep props off the character sheet (hands empty) and pass this sheet as a separate reference.

## 8. Identity board for stylised characters

Condensed from @aimikoda (GPT Image 2; works with Seedream 5):

```
2:1 character identity board using Image A as the only character and style reference. Match
Image A exactly: identity, proportions, hair, outfit, colours, medium, linework, shading. Clean
minimal background. No grid, no blueprint, no text, arrows or labels; never overlap or crop the
studies. Right 25%: an edge-to-edge close-up hero portrait. Left 10%: four expression portraits,
each a different emotion and head direction. Centre: hero full body facing the viewer, back view,
side view, one low-angle view.
```

## 9. Cartoon or creature turnaround

```
Character turnaround sheet of <name>, an original <creature/cartoon> character, flat light-grey
background, flat lighting, orthographic framing, no text. Top row: front, side profile, back.
Bottom row: three head close-ups: <expressions>. <Style block from styles.md>. One unambiguous
noun per feature ("two antennae", not "ears or antennae"). Original design, no recognizable
existing characters.
```

## 10. Fill a missing view

Rotate an approved front view with `qwen_angles` (one input image):

```json
{
  "model": "qwen_angles",
  "prompt": "same person, same outfit, back view, full body, light grey studio",
  "files": [{ "url": "<approved front full-body crop>" }],
  "provider_options": { "fal": { "horizontal_angle": 180, "vertical_angle": 0, "zoom": 3 } }
}
```

0 = front, 90 = right side, 180 = back, 270 = left. Colour can drift between angles; compare with the sheet.

For an exact panel layout (each panel from a given reference), `flux_3_image_klein` takes `provider_options.fal.bounding_boxes` with `box`, `label`, `description` and `source_image_index`.

## Words that keep panels consistent

- "The same <person> in every panel: identical face, hair, body, outfit and proportions."
- "Do not redesign, beautify, age or modernize the character."
- "When generating unseen angles, keep the exact identity; do not average the face with generic beauty features."
- "Empty hands", "arms relaxed", "same scale on one ground line".
- For people: "normal body proportions" unless the body itself is the point.
