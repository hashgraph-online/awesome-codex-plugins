# Prompts for mockup stills

Templates for the stills that go on a board: anchors, key frames, look tests and fix passes. Every template
has a filled example with an invented subject. For prompting the video step that follows, see
`varg-video-prompting`.

## Which model, what it costs

| Use | Model | Credits per image | Notes |
|---|---|---|---|
| Default stills, edits, consistency from refs | `nano_banana_2_1` | ~6 (1K), ~8 (2K), ~16 (4K) | Takes several reference files; good first pass for a whole board |
| Hero stills, hard edits, geometry-locked frames | `gpt_image_2_5` | ~11 medium, ~23 high | The model reviewers asked for when quality mattered; best at "keep everything, change only X" |

Prices from the `varg-ai` skill (`references/models.md`); other image models are listed there. Run a casting test
on the two models with the hardest shot, pick one, and use it for the whole set so the look does not jump.

## Calling varg (MCP)

- Quick look, up to 4 variations of one prompt: `generate_image({ prompt, count: 2, aspect_ratio: "16:9" })`.
  Add `reference_image: <url>` to edit one image.
- Several references (sheet, master, product): `call_tool({ tool: "image", input: { model: "nano_banana_2_1",
  prompt, aspect_ratio: "16:9", files: [{ url: sheet }, { url: master }] }, wait: true })`. In the prompt,
  `@image1`, `@image2` … follow the order of `files`.
- A whole board: `plan_batch({ title, items: [{ tool: "image", model, params: { prompt, aspect_ratio, files },
  label: "03 She pushes off" }, …] })` prices everything and charges nothing; `run_batch` after the person says
  go.
- One price: `estimate_cost({ input: { model, prompt, … } })`. Quote credits, never money.
- Local files (sheets, blockout renders) need a URL first. With the hosted MCP, call `create_upload` and PUT
  the bytes with curl to the returned `proxy_url` (that also registers the file). `upload_file` with `url`
  fetches a public file; with `path` it only works when the MCP server runs on the same machine.

## Prompt anatomy

Write the parts in this order; skip what does not apply.

1. **References and their roles.** "@image1 is the courier's character sheet: same face, hair and jacket.
   Create a new image, not a sheet. @image2 is the location master: keep the layout exactly."
2. **The camera and its flaws.** A named device and lens, and what its operator gets wrong.
3. **Who, verbatim.** The identity block, pasted, never paraphrased.
4. **What they are doing, mid-task.** An action with a small, specific detail. No poses, no looking at the lens.
5. **Where.** The place block: one specific, ordinary place with its clutter, and where the camera stands in it.
6. **One light.** What the light physically is and does.
7. **Wear.** Scuffs, dirt, damp, creases on the things in frame.
8. **Composition.** Shot size, where the subject sits in the frame, where the title room is, aspect ratio.
9. **Look line.** The same sentence on every prompt of the job: palette, grain, film or medium.
10. **Exclusions.** No text, no logos, no borders, nobody else in frame, no golden hour.

Words that do nothing or backfire:
- "realistic", "8k", "ultra detailed", "cinematic": no information. Name a camera instead.
- "keep the top fifth calm / empty": the model draws a band. Say "full-bleed, no borders" and place the subject.
- "rugged, stubble, handsome": famous-actor faces. Describe a specific person.
- "screaming", "about to be hit", "teeth bared": rejected by safety filters. Write tension or slapstick.
- Five different characters in one prompt: one design, cloned. One character per generation.
- "teal and orange", "golden hour", "glow": the most recognisable AI look.

## Cinematic palette in one paragraph

Decide where it is light and where it is dark before choosing hues. Use two or three hue families plus
neutrals, with one saturated spot where the eye should land. Keep skin natural. Warm subject against a cool
ground separates without effects. Lift the blacks a little, soften the highlights, add light grain. Plan the
colour per act (a colour script) and write each act's palette into those shots' prompts. Baked into the stills,
the palette survives the video step; we did not need a grade.

## Templates with filled examples

### 1. Character sheet

```
Character reference sheet on a flat mid-grey background, no text, no labels. Five views of the same person in a
row: front, three-quarter, profile, back, full body, plus one large face close-up on the right. Even soft studio
light. {IDENTITY BLOCK}. Neutral standing pose, arms relaxed. {LOOK LINE}.
```
Example identity block (paste it into every later prompt unchanged):
```
A bicycle courier, woman in her early thirties, wiry build, sunburnt nose, a small scar through the left
eyebrow, dark hair cut short and uneven, wet at the ends. Faded olive rain jacket with the left cuff frayed,
black cycling tights with a torn knee patched in grey, scuffed white sneakers, one fingerless glove on the right
hand only. Signal-orange roll-top backpack, dirty at the base. Moves fast and economically; never smiles at
the camera.
Do not change between shots: the scar, the frayed left cuff, the single right glove, the orange backpack.
```

### 2. Location master (environment first)

```
Wide establishing plate of {PLACE}, empty, no people. Layout, keep exactly in later shots: 1 {element and where},
2 {element and where}, 3 {element and where}. {LIGHT}. {CLUTTER LIST}. Camera at {height}, looking {direction}.
{LOOK LINE}. No text, no signs with letters, no logos, full-bleed.
```
Example:
```
Wide establishing plate of a city bike lane at dusk after rain, empty, no people. Layout: 1 the lane runs
straight away from camera on the right, 2 a delivery van parked half on the kerb on the left, 3 a bent steel
bollard at the near edge of the lane, 4 traffic lights far down the lane. Overcast dusk, flat soft light, wet
asphalt reflecting the lights. Puddles, a soggy flyer stuck to the kerb, cigarette ends in the drain, a
chained bike with no front wheel. Camera at kerb height, looking down the lane. Handheld documentary camera,
35 mm, muted slate palette, light grain. No text, no signs with letters, no logos, full-bleed.
```

### 3. Product sheet

Use the real packshot when one exists; ask the model only to fill missing angles, never to redraw the label.
```
@image1 is the product: same shape, colours and seams. Product sheet on flat light grey: front, three-quarter,
side, back, top, plus one view of a hand holding it for scale. Even soft light. The label area stays blank. No
text, no logos.
```

### 4. Key frame from anchors

```
@image1 is {character}'s sheet: same face, hair and outfit. Create a new image, not a sheet. @image2 is the
location master: same place, same layout. {CAMERA AND FLAWS}. {ACTION, MID-TASK}. Camera stands {where in the
layout}, looking {toward what}. {LIGHT}. {WEAR}. {COMPOSITION}. {LOOK LINE}. Only {N} people in frame. No text,
no logos, full-bleed.
```
Example:
```
@image1 is the courier's character sheet: same face, scar, jacket and single right glove. Create a new image,
not a sheet. @image2 is the location master: same lane, same van and bollard. Handheld documentary camera,
35 mm, the operator running alongside, framing a little late. She stands on the pedals pushing off from the
kerb, front wheel throwing spray, backpack high on her back. Camera beside the bollard, looking down the lane
toward the traffic lights. Overcast dusk, wet asphalt reflections. Mud on her shins, rain beading on the pack.
Medium shot, her head in the upper third, empty asphalt bottom left for a title. Muted slate palette, one
signal-orange accent, light grain. Only one person in frame. No text, no logos, full-bleed.
```

### 5. Close-up from the master (same moment, closer)

```
@image1 is the approved wide frame of this moment. Same place, same light, same people, same clothes, closer
angle: {close framing}. Keep every detail that is visible in both frames identical. {LOOK LINE}. No text.
```

### 6. Look test (one frame, several looks)

Same subject, same composition, change only the look line, one generation per look. Put them side by side as
variants A, B, C on one frame of the board.
```
A: Handheld documentary camera, 35 mm, overcast, muted slate palette, light grain.
B: 1990s camcorder, slightly soft, clipped highlights, cool fluorescent spill, timecode-free.
C: 1980s Japanese anime cel animation, hand-drawn ink line art, flat cel shading, painted background.
```

### 7. Geometry-locked frame from a blockout render

When masters still drift between cameras, render the camera in a three.js blockout (`threejs-animatic`) and edit
on top of it, ideally with `gpt_image_2_5`.
```
@image1 is a grey-box render of the set from this exact camera. Keep the camera, horizon, perspective and the
position of every block exactly. Turn it into a photograph. Mapping: tall grey block on the left = the
delivery van from @image3; thin cylinder = the bent steel bollard; grey mannequin = the courier from @image2,
in the same pose. {LIGHT}. {LOOK LINE}. Nothing added that is not in the render. No text.
```
Give blockout people a head, arms and legs; a featureless block comes back as a log or a sack.

### 8. Fix passes (edit the still, do not regenerate)

```
Remove only the logos and lettering on the jacket. Change nothing else: same face, pose, light and framing.
```
```
Make her about five years younger. Keep the face shape, scar, hair, clothes, pose, framing and light exactly.
```
```
Remove the extra hand on the backpack strap. Her left hand stays on the handlebar. Change nothing else.
```
Edits keep the composition and the light; a regeneration starts the dice again.

### 9. Moodboard tiles (one look, many subjects)

A moodboard shows the look on different subjects so the reviewer judges the look, not one picture. Keep the
look line fixed and vary only the subject:
```
{LOOK LINE}. {SUBJECT}. No text, no logos.
Subjects: a hand on wet handlebar tape · a shop awning dripping at night · a delivery van's side mirror with
rain · a laptop sleeve inside a backpack, dry · traffic lights through a fogged visor.
```

### 10. Pictures for device mockups

For screens and cards inside the device templates (`iphone-duo-fold`, `stamp-carousel`): generate the picture,
never the UI.
```
A wide panoramic picture for a phone screen: {SUBJECT}, centred interest in the middle third so it reads when
folded, dark edges, no text, no interface, no device frame, no logos. {LOOK LINE}.
```
```
Poster art for one card in a swipe carousel: {SUBJECT}, bold simple shape on a flat colour field, readable at
thumbnail size, no text, no letters, no logos.
```
Interface text, buttons, chat bubbles and numbers come from the template's HTML, where they stay exact and
editable.
