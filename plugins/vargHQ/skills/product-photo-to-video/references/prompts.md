# Prompts for product videos

`{CAPS}` = fill in. Model ids are varg ids. Quote with `estimate_cost` before running.

## P1. 12-panel storyboard sheet (`gpt_image_2_5`)

Adapted from @Ciri_ai's ASMR unboxing sheet (varg how-to template).

```text
Create a clean, premium storyboard infographic for a {DURATION}-second {FORMAT} video of {PRODUCT}. Use the attached product photo as the exact product: same shape, colors, logo and label text in every panel.

Layout: white background, minimal agency style, {ACCENT_COLOR} accents, rounded panel borders.
Header: "STORYBOARD", the product name in bold {ACCENT_COLOR}, subtitle "{FORMAT}". Four info boxes: Duration: {DURATION} s | Style: {STYLE} | Audience: {AUDIENCE} | Audio: {SOUND_LIST}.

{N} panels (8-12) in a 3-column grid. Each panel: a numbered badge, a timestamp (about 2.5 s each), one realistic cinematic photo of the shot, a hand-drawn white doodle sound-word (POP!, TEAR!, POUR~, WOW!), and three lines: VISUAL / ACTION / CAMERA (add DIALOGUE only if someone speaks).

Sequence: 1 the product on {SURFACE}, hands enter. 2-3 open and reveal. 4-6 the most tactile moments ({SENSORY_ACTIONS}). 7-9 the product in use. 10-11 the result in macro. Last panel: hero packshot of the product beside the result, {END_GESTURE}.

Photography: {SURFACE}, soft natural light, shallow depth of field, POV hands only, no face, premium commercial style. Footer: total duration, format {ASPECT}, style.
```

## P2. Multi-shot film with PRODUCT LOCK (`seedance_2_5`; `kling_v4` multi-shot works too)

Adapted from @HeyRu0by (varg how-to template).

```text
{DURATION}-second vertical 9:16 commercial for {PRODUCT}, {N} shots (5-8), ultra-realistic, {TONE}.
@image1 is the exact product. @image2 is the approved storyboard sheet: follow its shot order, but never show its panels, numbers or text.

PRODUCT LOCK: keep the exact pack shape and proportions, logo, typography, colors, label text and material reflections in every shot. Front label reads, in this exact order: "{LINE_1}" "{LINE_2}" "{LINE_3}", correctly spelled, legible whenever in focus. No redesign, no misspelled text, no duplicate packs, no new logos.

01 | 0-2s HOOK: extreme macro of {MOST_SENSORY_MOMENT}, 100mm macro, slow motion.
02 | 2-4s: {ACTION_2}, camera {MOVE_2}.
03 | 4-6s: {TEXTURE_CLOSE_UP}, camera glides along the surface.
04 | 6-9s: {BURST_OR_POUR}, realistic particle and liquid physics.
05 | 9-12s PACK REVEAL: the product from @image1 turns to face camera, front label sharp and readable.
06 | 12-15s HERO: centered packshot on {BACKGROUND}, slow push-in; hold the last second clean, empty space above for the end card.

One camera move per shot, at least 1.5 s per shot. Light: {KEY_LIGHT}, rim light, controlled reflections.
Audio: {FOLEY_LIST}, {MUSIC_STYLE} at {BPM} BPM (or: no background music).
Negative: no warped pack, no changing design, no captions or extra text, no watermark, no flicker, no plastic-looking food.
```

## P3. Exact-SKU locked loop (`kling_v4`, `wan_3`, or `pixelcut_looping_video`)

From Masonry's controlled product-ad test: the safest shot for label fidelity.

```text
Animate the supplied {PRODUCT} source as a restrained ecommerce product-ad loop. The {PACK} remains upright, centered, stationary, and completely visible while the camera makes one very slow subtle push-in with a small clockwise parallax move. Preserve exactly one {PACK}; {SHAPE_AND_PARTS}; {COLORS}; exact {LABEL_TEXT} text; proportions, edges, reflections, shadow, and {BACKGROUND}. Keep the front label readable throughout. Add no hand, person, prop, ingredient, droplet, splash, mist, bubble, extra text, logo, claim, product part, cap movement, liquid movement, cut, transition, or scene change. No audio.
```

## P4. Background swap that keeps the product (`gpt_image_2_5` / `nano_banana_2_1`)

From fal's commercial skill.

```text
keep the uploaded product exactly unchanged, replace only the background with {ENVIRONMENT}, match reflections and contact shadows, {LIGHTING_DIRECTION}, commercial product photography, no product deformation, no added labels
```

Material cues: glass — backlight, rim light, caustics, controlled reflections; metal — strip highlights, hard rim, precise specular lines; jewelry — macro lens feel, dark cards, crisp sparkle.

## P5. Cut-out with alpha (`gpt_image_2_5`, transparent background) — or `bria_guided_remove_background`

From the OpenAI image prompting cookbook.

```text
Extract the product from the input image and isolate it on a fully transparent background.
Output: centered product, crisp silhouette, no halos/fringing.
Preserve product geometry and label legibility exactly.
Do not add a solid backdrop, checkerboard, scenery, or shadow. Do not restyle the product.
```

## P6. Food process film ending on the product (`seedance_2_5`)

Adapted from @Goodmanprotocol (10.5M views, 9,371 bookmarks).

```text
Create a {DURATION}-second cinematic {STYLE} cooking video showing {DISH} being made, ending on {PRODUCT} beside the finished dish.
STYLE: ultra-detailed food textures, realistic cooking physics, visible steam, macro close-ups, shallow depth of field, smooth camera moves, {KITCHEN}. Fast rhythmic editing with match cuts on movement, shape and texture. Hands only, no faces.
TIMELINE (one action per beat, 2-3 s each): 0-2.5s {STEP_1}, close-up, {SOUND_1}. 2.5-5s {STEP_2}. ... {T-4}-{T}s HERO: the finished {DISH} with {PRODUCT} on {SURFACE}; steam rises as the camera slowly arcs around it.
AUDIO: {MUSIC_STYLE} instrumental, 110-120 BPM. Sync ASMR sounds to each action. One soft final tone on the reveal.
NEGATIVE: no storyboard, panels, numbers, captions, UI, logos or text overlays. Keep food, hands, utensils, lighting and set consistent.
```

## P7. Apparel lock (`seedance_2_5`, one `@image` per garment)

```text
@image1 is the model: keep face, hair and body exactly. @image2 is the EXCLUSIVE reference for the {GARMENT}: reproduce the EXACT garment — do not redesign, modify, recolor, simplify, or reinterpret its cut, print, stitching or logo. {SCENE}. Locked camera, the model turns 360° slowly, fabric moves naturally. No text, no extra accessories.
```

## P8. Product in hand (`omni_flash_1_1` role tags)

```text
[0-3s] A {SETTING} sequence. A woman <IMAGE_REF_0> is holding <IMAGE_REF_1> near her face, label toward the lens. Single continuous shot.
```

Sources: [varg how-to](https://varg.ai/how-to/turn-a-product-photo-into-a-video), [fal commercial skill](https://github.com/fal-ai-community/skills/blob/main/skills/commercial/references/prompt-patterns.md), [Masonry](https://masonry.so/blog/best-ai-video-model-for-product-ads), [OpenAI cookbook](https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide), [Gemini Omni docs](https://ai.google.dev/gemini-api/docs/omni.md.txt).
