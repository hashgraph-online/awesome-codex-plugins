# Prompts for AI UGC ads

`{CAPS}` = fill in. Every spoken line is a product fact or a demo, never a first-person result. Quote with `estimate_cost` first.

## P1. Realistic end-of-day UGC, 15 s (creator still → `seedance_2_5`)

Structure of @abxxai's thread (134.5K views, 1,867 bookmarks), condensed. Step 1: creator still with `gpt_image_2_5` ("iPhone selfie photo, slightly below eye level, of @image1: the same young woman as the reference… Face and hair 100% match the reference. Fully clothed."). Step 2: a clean, straight-on product photo with a readable label. Step 3:

```text
A 15-second vertical (9:16) ultra-photorealistic close-up vlog clip, filmed on a phone held at arm's length. Not an ad. A person talking to their own camera at the end of the day.
TALENT — {AGE}, {HAIR}, {SKIN incl. freckles}, {BROWS, EYES, JEWELRY}. Face, freckles, hair and eye color 100% match the reference. {WARDROBE, "collar slightly crooked, sleeves pushed up"}.
PRODUCT — {BRAND} {PRODUCT} {SIZE}. {CONTAINER, LID}. Front label reads, in this exact order: "{L1}" "{L2}" "{L3}". Shape, color, texture and all label text 100% match the reference, correctly spelled, legible whenever in focus.
LOCATION — {ROOM}. Only fragments read in frame; background soft the entire time.
LIGHTING — One condition, unchanged across all beats: {LIGHT}. No ring light, no fill, no glam lighting.
FRAMING — Close-up throughout. The product enters frame close to the face, never held out toward the lens.
0:00–0:04 Mid-motion already; the product comes up beside the cheek, held low and casual. Selfie camera, handheld drift, one quick autofocus hunt between face and product. Dialogue: "{THROWAWAY_LINE}"
0:04–0:07 Macro: {TEXTURE_ACTION}; label lines cross the frame in focus for a beat. Rack from label to texture. Dialogue: "{FACT_1}"
0:07–0:11 Uses it, a small genuine reaction; talking while working. Pores and natural shadows stay visible. Dialogue: "{FACT_2}"
0:11–0:15 Closest framing, eyes on her own reflection, reaches to stop recording, frame tilts. Dialogue: "{SOFT_LINE}"
PERFORMANCE — Low energy, unperformed: a slow blink, a half-smile that arrives late, one natural swallow, visible breath. No presenter voice, no pointing at the product.
VOICE — Soft, close to the phone mic, natural room tone.
CAMERA CHARACTER — Natural handheld tremor, small framing corrections, autofocus hunts, mild wide-angle distortion, rolling shutter, slight sensor noise. Never stabilized.
STYLE — Real personal vlog, no retouching, no skin smoothing, no product-hero framing, no before/after.
POSITIVE LOCKS — Same face and wardrobe every beat; same product, label legible, sharpest at 0:04–0:07; exactly two arms and two hands, one hand always holding the phone; dialogue exactly as written with natural lip-sync; ambient audio only. No music, no on-screen text, no captions.
```

## P2. Phone-real creator still, JSON (`nano_banana_2_1`, or a 4 s `seedance_2_5` take)

Adapted from @DavidRunsAds (varg how-to template).

```json
{
 "output": {"aspect_ratio": "9:16", "style": "photorealistic candid front-camera selfie, casual social-media look; not studio, not illustration, not 3D render", "summary": "{WHO, WHERE, TIME OF DAY, WHAT THEY ARE DOING}"},
 "subject": {"count": "exactly one person", "apparent_age": "{AGE}", "build": "{BUILD}", "identity": "{FACE_SHAPE}, {EYES}, {BROWS}, {NOSE}, {LIPS}", "expression": "{EXPRESSION}, looking into the lens"},
 "skin": "real skin: visible pores, mild redness, uneven tone, {FRECKLES_OR_MARKS}; not airbrushed",
 "hair": "{HAIR}, individual strands, flyaways at the crown",
 "clothing": "{GARMENT}, {FABRIC}, natural folds, no logos or lettering",
 "environment": "{LIVED_IN_ROOM} with 3-4 named objects, 1-3 m behind, slightly soft",
 "lighting": "{WINDOW_DAYLIGHT_OR_LAMP}, soft, low contrast, no rim light",
 "camera": "handheld phone front camera at arm's length, ~24-26 mm, small-sensor noise, mild edge stretch, no bokeh",
 "composition": "chest-up, face upper-middle, camera rolled a few degrees",
 "color_grading": "muted, natural white balance, no teal-orange grade, no heavy HDR",
 "negative_constraints": ["no text, UI, captions or watermarks", "no extra people", "no visible phone", "no plastic or waxy skin, no perfect symmetry", "no extra or fused fingers", "no studio light"]
}
```

## P3. Reference-led UGC take, 15 s (`seedance_2_5`)

Adapted from the BytePlus Seedance 2.5 prompt guide (varg how-to template).

```text
Raw vertical 9:16 phone video, one UGC take for {PRODUCT}. Image 1 is the creator: keep face, hair and outfit exactly. Image 2 is the product: keep shape, colour and label exactly. Strictly refer to Video 1 for the handheld camera movement, framing and pacing; do not copy its person, words or on-screen text.
Setting: {ROOM}, {LIGHT}. Phone front-camera quality, slight handheld sway, autofocus breathing.
0-2s: Opens mid-sentence, the product from Image 2 already in hand near the lens: "{HOOK_LINE}"
2-6s: {DEMO_ACTION_1} close to the lens, label readable: "{PROBLEM_LINE}"
6-11s: Close-up of {DEMO_ACTION_2} showing {VISIBLE_PROOF}: "{FACT_LINE}"
11-15s: Back to the lens, product beside the face, small laugh: "{SOFT_CTA}"
Audio: only the creator's voice, room tone and handling sounds. No BGM.
Constraints: one creator, same face and outfit; five fingers per hand; the product never changes shape or duplicates. No subtitles, captions, extra logos or watermarks.
```

## P4. One-take street interview, 15 s (`seedance_2_5`)

Adapted from @Zyvex_0x (varg how-to template). For 30–60 s, feed each finished clip back as the reference for the next (reference chain).

```text
Native 15-second vertical 9:16 street-interview clip: one continuous handheld take, no cuts, on {STREET} at {TIME}. Looks like a real viral man-on-the-street clip, not an ad. Image 1 is the passer-by: keep face, hair and outfit exactly.
RULES: one adult in focus. The interviewer is never seen except a right hand holding a fuzzy grey mic from the lower-left; voice off-screen. Five fingers per hand. No readable text or logos except on {PRODUCT}.
CAMERA: older consumer camera, operator 1.2 m away at eye level, natural shake, brief autofocus hunt; never gimbal-smooth.
LOOK: slightly muted colour, imperfect white balance, real skin; no beauty filter.
00.0-02.5 INTERVIEWER: "{QUESTION}" She smirks, eyes up.
02.5-07.0 PASSER-BY (honest, unhurried): "{ANSWER_WITH_PAIN}"
07.0-10.0 INTERVIEWER: "{FOLLOW_UP}" She reaches into her bag.
10.0-13.0 She holds {PRODUCT} beside her face, label to the lens: "{ONE_LINE_REASON}"
13.0-15.0 She shrugs and laughs; the camera holds.
SOUND: city ambience, distant traffic, no music. No subtitles, no watermark.
```

## P5. Camcorder vlog, 15 s in 6 shots (`kling_v4` or `seedance_2_5`)

Structure from @YourAlphaMom's Seedance 2.5 vs Kling 4 test (Kling was right first try and ~16× cheaper; Seedance more real after 3 tries).

```text
CAMERA: DV camcorder handheld feel. POV of {NAME} holding the camera, sometimes propping it on the floor. Hand shake, misaligned framing, delayed focus pulls, clumsy zooms, occasional face cut-off. The camera never appears.
LOOK: soft, slightly blurry tape quality, faint noise, bloomed highlights, flickering auto-exposure, muted contrast.
STYLE: playful, self-deprecating vlog. Quick handheld cuts.
CHARACTER: {NAME, AGE, HAIR, OUTFIT, ACCENT}. SETTING: {PLACE, TIME, 3 PROPS}.
STORYBOARD (15 s, 6 shots): 1 (~2.5 s, propped, medium) {ACTION} LINE: "{L1}" 2 (~2.5 s) "{L2}" 3 (~2.5 s) "{L3}" 4 (~2 s, macro insert, the product, no dialogue, ambient only) 5 (~2.5 s) "{L4}" 6 (~3 s, arm's-length selfie) "{L5}"
```

## P6. Lock the voice across takes (`seedance_2_5` with `@audio1`)

Render the hook first, approve face and voice, then reuse that take's audio:

```text
Use @Image1 as the character's appearance. Use @Audio1 as the dialogue track. The character speaks directly to camera with lips synced to @Audio1. Medium close-up, soft indoor light. Natural conversational tone, subtle head movement. No subtitles.
```

## P7. One-call presenter (`creatify_boreal`)

Sections in the prompt: `[VISUAL]` the presenter, room and the product in hand · `[SPEECH]` the exact lines · `[SOUNDS]` room tone · `[TEXT]` none. English is the validated language. Set `manifest_disclosure` to add an AI label.

## Script helpers (agent prompts)

- Customer language (from @lifemaximised, 286K views, 4,657 bookmarks): "Search Reddit, YouTube comments, Amazon reviews, TikTok comments, and niche forums for people discussing problems related to {CATEGORY}. Extract the exact words they use when describing the problem, what they have tried, why those solutions failed, what outcome they want, and what would make them buy. Format: Quote / Pain Point / Desired Outcome / Funnel Stage / Possible Ad Angle."
- Ad breakdown (from @maxxmalist): "Role: Expert direct-response creative director. Break down this video ad: 1) pain points and psychology (surface problems, deep emotional pains, the villain); 2) the angle (secret discovery, transformation or comparison; the new mechanism; UGC trust vs brand authority); 3) the first 3 seconds and three alternative hooks (curiosity, result, fear); 4) the bridge and the CTA, with any risk reversal."

Sources: [@abxxai](https://x.com/abxxai/status/2095179656802844727), [@YourAlphaMom](https://x.com/YourAlphaMom/status/2115191029641175400), [@lifemaximised](https://x.com/lifemaximised/status/2094966852887687492), [@maxxmalist](https://x.com/maxxmalist/status/2015892584493728087), [varg how-to: make a UGC ad video](https://varg.ai/how-to/make-a-ugc-ad-video), [Luma Seedance guide](https://lumalabs.ai/learning-center/articles/seedance-2.0-complete-guide), [BytePlus Seedance 2.5 guide](https://docs.byteplus.com/en/docs/ModelArk/seedance-2-5-prompt-guide).
